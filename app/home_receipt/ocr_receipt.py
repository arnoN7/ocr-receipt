# from imutils.perspective import four_point_transform
import pytesseract
import random
from pytesseract import Output
from datetime import datetime
from functools import cmp_to_key
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_, and_
from app.home_receipt.models import Shop, Receipt, PaidProduct, Product, ProductGroup
from app import db
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
#engine = create_engine('sqlite:///ocr-receipt.sqlite3', echo=True)

#Base.metadata.create_all(engine)
#Session = sessionmaker(bind=engine)
session = db.session

image_path_expl = '/Users/arnaudrover/PycharmProjects/ocr-receipt/receipts/IMG_9768.jpg'



def contour_sort(a, b):
    xa, ya, wa, ha = cv2.boundingRect(a)
    xb, yb, wb, hb = cv2.boundingRect(b)
    result = ya - yb
    if result != 0:
        return result
    else:
        return xa - xb


def extract_text(image):
    result = {}
    result_text = ""
    img = cv2.imread(image)
    img_h = img.shape[0]
    img_w = img.shape[1]
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
    current_gl_line = 0
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cropped = gray2[y:y + h, x:x + w]
        data = pytesseract.image_to_data(cropped, lang='fra', output_type=Output.DICT)
        current_block = -1
        current_line = -1
        current_par = -1
        for i in range(len(data['line_num'])):
            txt = data['text'][i]
            line_num = data['line_num'][i]
            block_num = data['block_num'][i]
            par_num = data['par_num'][i]
            top, left = data['top'][i], data['left'][i]
            width, height = data['width'][i], data['height'][i]
            if not (txt == ''):
                if current_line != line_num or current_block != block_num or current_par != par_num:
                    current_gl_line = current_gl_line + 1
                    current_line = line_num
                    current_block = block_num
                    current_par = par_num
                #Add text in line
                if current_gl_line not in result:
                    result[current_gl_line] = {}
                    result[current_gl_line]['text'] = txt
                else:
                    result[current_gl_line]['text'] = result[current_gl_line]['text'] + " " + txt
                #Record left of the line and be sure we get the top left point
                if 'left' not in result[current_gl_line]:
                    result[current_gl_line]['left'] = left + x
                if 'top' not in result[current_gl_line]:
                    result[current_gl_line]['top'] = top + y
                if 'height' not in result[current_gl_line]:
                    result[current_gl_line]['height'] = height
                if 'width' not in result[current_gl_line]:
                    result[current_gl_line]['width'] = width
                #ensure we include all words in line in width
                else:
                    new_width = x + left + width - result[current_gl_line]['left']
                    if new_width > result[current_gl_line]['width']:
                        result[current_gl_line]['width'] = new_width
    for i in result:
        result[i]['left'] = result[i]['left'] / img_w
        result[i]['width'] = result[i]['width'] / img_w
        result[i]['top'] = result[i]['top'] / img_h
        result[i]['height'] = result[i]['height'] / img_h
        if result_text =="":
            result_text = str(result[i]['text'])+'\n'
        else:
            result_text = result_text + str(result[i]['text'])+'\n'
    return result, result_text


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
        product = Product.query.filter_by(name=product_name).first()
        # Add product if not exist in product list
        if product is None:
            product_group = ProductGroup(name=product_name)
            session.add(product_group)
            session.commit()
            product = Product(name=product_name, product_group_id=product_group.id)
            session.add(product)
            session.commit()
        paid_product = PaidProduct(receipt_id=receipt_id, product_group_id=product.product_group_id,
                                   quantity=quantity, price=price, unit_price=unit_price,
                                   pos_top=random.randint(0, 100)/100, pos_left=0, pos_width=0.7, pos_height=0.2)
        session.add(paid_product)
        session.commit()
    return None

def record_products_pos(text_data, receipt_id):
    for i in text_data:
        matches = re.finditer(REGEX_PRODUCT, text_data[i]['text'], re.MULTILINE)
        for match in matches:
            product_name = match.group('product')
            quantity = int(match.group('qte'))
            price = float(match.group('price').replace(',', '.'))
            unit_price = price / quantity
            product = Product.query.filter_by(name=product_name).first()
            # Add product if not exist in product list
            if product is None:
                product_group = ProductGroup(name=product_name)
                session.add(product_group)
                session.commit()
                product = Product(name=product_name, product_group_id=product_group.id)
                session.add(product)
                session.commit()
            paid_product = PaidProduct(receipt_id=receipt_id, product_group_id=product.product_group_id,
                                       quantity=quantity, price=price, unit_price=unit_price,
                                       pos_top=text_data[i]['top'], pos_left=text_data[i]['left'],
                                       pos_width=text_data[i]['width'], pos_height=text_data[i]['height'])
            session.add(paid_product)
            session.commit()
    return None


def add_new_receipt(image_path):
    receipt_data, receipt_text = extract_text(image_path)
    file = open(RECOGNIZED_TXT, 'w+')
    file.write(receipt_text)
    r_id = record_receipt(receipt_text, image_path)
    if r_id is not None:
        #record_products(receipt_data, r_id)
        record_products_pos(receipt_data, r_id)

#add_new_receipt(image_path_expl)
