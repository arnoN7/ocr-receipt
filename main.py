# from imutils.perspective import four_point_transform
import pytesseract
from datetime import datetime
from functools import cmp_to_key
from sqlalchemy import create_engine, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import or_, and_
from sqlalchemy import Column, Integer, String
from models import *
import argparse
import imutils
import cv2
import re
import io

REGEX_PRODUCT = r"(?P<qte>^\d+) (?P<product>.{3,}) (?P<price>\d+[\.,]\d{2})"
REGEX_DATE = r"\d{2}/\d{2}/\d{4}"
REGEX_RECEIPT = [["siret", r"Siret (?P<siret>[\d ]+)"],
                 ["address", r"(?P<address>\d+.+(Rue|Avenue|Av|Impasse|Imp).+)"],
                 ["postcode", r"(?P<postcode>\d{5}) [^\n ]+"],
                 ["city", r"(\d{5}) (?P<city>[^\n ]+)"],
                 ["phone", r"(?P<phone>(\d{2}|\+\d{3}).(\d{2}.){3}\d{2})"],
                 ["date", r"(?P<date>(\d{2}/){2}\d{4})"],
                 ["total_price", r"TOTAL.+ (?P<total_price>\d+\.\d{2})"]]
REGEX_ADDRESS = r"\d+.+(Rue|Avenue|Av|Impasse|Imp).+"

RECOGNIZED_TXT = "recognized.txt"
engine = create_engine('sqlite:///ocr-receipt.sqlite3', echo=True)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

image_path = 'receipts/IMG_9768.jpg'


def contour_sort(a, b):
    xa, ya, wa, ha = cv2.boundingRect(a)
    xb, yb, wb, hb = cv2.boundingRect(b)
    result = ya - yb
    if result != 0:
        return result
    else:
        return xa - xb


def extract_text(image):
    result = ""
    img = cv2.imread(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 75, 250)
    # Specify structure shape and kernel size.
    # Kernel size increases or decreases the area
    # of the rectangle to be detected.
    # A smaller value like (10, 10) will detect
    # each word instead of a sentence.
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    # Applying dilation on the threshold image
    dilation = cv2.dilate(edged, rect_kernel, iterations=1)
    # Finding contours
    contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)

    im3 = img.copy()
    gray2 = cv2.cvtColor(im3, cv2.COLOR_BGR2GRAY)
    file = open(RECOGNIZED_TXT, "w+")
    file.write("")
    file.close()
    contours = sorted(contours, key=cmp_to_key(contour_sort))
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cropped = gray2[y:y + h, x:x + w]
        text = pytesseract.image_to_string(cropped, lang='fra')
        if text != "":
            if result == "":
                result = text
            else:
                result = result + '\n' + text
    return result


def record_receipt(text, path):
    buf = io.StringIO(text)
    name = buf.readline().replace('\n', '')
    params = {}
    # Extract all common parameters of the shop and receipt (name, address, etc.)
    for param in REGEX_RECEIPT:
        matches = re.finditer(param[1], text, re.MULTILINE)
        for match in matches:
            params[param[0]] = match.group(param[0])
            break
    if params.get('date', None) is not None:
        params['date'] = datetime.strptime(params['date'], '%d/%m/%Y')

    shop = Shop(name=name, address=params.get('address', "NO_ADDRESS"), postcode=params.get('postcode', "00000"),
                city=params.get('city', "NO_CITY"), siret=params.get('siret', "NO_SIRET"),
                phone=params.get('phone', "NO_PHONE"))
    exists = session.query(Shop.id).filter(
        or_(Shop.name == shop.name, Shop.siret == params.get('siret', ""),
            Shop.phone == params.get('phone', ""))).first() is not None
    if not exists:
        session.add(shop)
        session.commit()
    receipt = Receipt(shop_id=shop.id, date=params.get('date', ""),
                      total_price=params.get('total_price', 0), file=path)
    exists = session.query(Receipt.id).filter(Receipt.file == receipt.file).first() is not None
    if not exists:
        session.add(receipt)
        session.commit()
    return receipt.id


def record_products(text, receipt_id):
    matches = re.finditer(REGEX_PRODUCT, text, re.MULTILINE)
    for match in matches:
        product_name = match.group('product')
        quantity = int(match.group('qte'))
        price = float(match.group('price').replace(',', '.'))
        unit_price = price / quantity
        product = Product(name=match.group('product'))
        product_id = session.query(Product.id).filter(Product.name == product.name).first()
        # Add product if not exist in product list
        if product_id is None:
            session.add(product)
            session.commit()
        paid_product = PaidProduct(receipt_id=receipt_id, product_id=product.id,
                                   quantity=quantity, price=price, unit_price=unit_price)
        exists = session.query(PaidProduct.id).filter(
            and_(PaidProduct.product_id == paid_product.product_id,
                 PaidProduct.receipt_id == paid_product.receipt_id)).first() is not None
        if not exists:
            session.add(paid_product)
            session.commit()


receipt_text = extract_text(image_path)
file = open(RECOGNIZED_TXT, 'w+')
file.write(receipt_text)
r_id = record_receipt(receipt_text, image_path)
if r_id is not None:
    record_products(receipt_text, r_id)
