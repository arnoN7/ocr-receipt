# from imutils.perspective import four_point_transform
import copy

import imutils
import numpy
import pytesseract
import random
from pytesseract import Output
from datetime import datetime, date
from functools import cmp_to_key
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_, and_
from app.home_receipt.models import Shop, Receipt, PaidProduct, Product, ProductGroup
from app import db
import cv2
import numpy as np
import re
import io
import os

TOTAL_PRICE = "total_price"
MAX_START_COLUMN_PRICE = 0.75
MIN_OVERLAP = 0.2

REGEX_PRODUCT = r"(?P<qte>^\d+) (?P<product>.{3,}) (?P<price>\d+[\.,]\d{2})"
REGEX_PRODUCT_QTY = r"(?P<qte>^\d+)(?P<product>.+)"
REGEX_BEGIN_SPACES = r"^[ ]+"
REGEX_END_SPACES = r"[ ]+$"
REGEX_PRICE = r" (?P<price>\d+\.\d{2})"
REGEX_PRICES = r"(?P<price>\d+\.\d{2}.+)"
REGEX_RECEIPT = [["siret", r"siret (?P<siret>[\d ]+)"],
                 ["address", r"(?P<address>\d+.+(rue|avenue|av|impasse|imp).+)"],
                 ["postcode", r"(?P<postcode>\d{5}) [^\n ]+"],
                 ["city", r"(\d{5}) (?P<city>[^\n \d]+)"],
                 ["phone", r"(?P<phone>(\d{2}|\+\d{3})\.(\d{2}\.){3}\d{2})"],
                 ["date", r"(?P<date>(\d{2}/){2}\d{4})"]]

RECOGNIZED_TXT = "recognized.txt"
# engine = create_engine('sqlite:///ocr-receipt.sqlite3', echo=True)

# Base.metadata.create_all(engine)
# Session = sessionmaker(bind=engine)
session = db.session

image_path_expl = '/Users/arnaudrover/PycharmProjects/ocr-receipt/app/static/receipts/NAT_IMG_0220.jpg'


class Rect():
    def __init__(self, x=0, y=0, height=0, width=0):
        self.x = x
        self.y = y
        self.height = height
        self.width = width

    def is_vertical_overlap(self, rect, min_overlap=0):
        if self.x <= rect.x < (self.x + self.width) <= (rect.x + rect.width):
            if (((self.x + self.width) - rect.x) / ((rect.x + rect.width) - self.x)) > min_overlap:
                return True
        if rect.x <= self.x < (rect.x + rect.width) <= (self.x + self.width):
            if (((rect.x + rect.width) - self.x) / ((self.x + self.width) - rect.x)) > min_overlap:
                return True
        return False

    def get_outer_rect(self, rect):
        if self.x <= rect.x < (rect.x + rect.width) <= (self.x + self.width):
            return copy.deepcopy(self)
        if rect.x <= self.x < (self.x + self.width) <= (rect.x + rect.width):
            return copy.deepcopy(rect)
        return None

    # Return True if self is inside rect
    def is_inside(self, rect):
        if rect.x <= self.x < (self.x + self.width) <= (rect.x + rect.width):
            return True
        return False

    def get_side_right(self, rect):
        if self.x < rect.x:
            return copy.deepcopy(rect)
        return copy.deepcopy(self)

    def get_side_left(self, rect):
        if self.x < rect.x:
            return copy.deepcopy(self)
        return copy.deepcopy(rect)

    def get_upper(self, rect):
        if self.y < rect.y:
            return copy.deepcopy(self)
        else:
            return copy.deepcopy(rect)


def contour_sort(a, b):
    xa, ya, wa, ha = cv2.boundingRect(a)
    xb, yb, wb, hb = cv2.boundingRect(b)
    result = ya - yb
    if result != 0:
        return result
    else:
        return xa - xb


def prepare_img(image, debug=False):
    # load image
    orig = cv2.imread(image)
    img = orig.copy()
    ratio = orig.shape[1] / float(img.shape[1])
    # convert the image to grayscale, blur it slightly, and apply edge detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5,), 0)
    edged = cv2.Canny(blurred, 75, 200)
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (120, 120))
    dilation = cv2.dilate(edged, rect_kernel, iterations=1)
    # Find Receipt contour
    contours, hierarchy = cv2.findContours(dilation.copy(), cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)
    receipt_cnt = sorted(contours, key=cv2.contourArea, reverse=True)
    x, y, w, h = cv2.boundingRect(receipt_cnt[0])
    cropped_receipt = gray[y:y + h, x:x + w]
    cropped_receipt = cv2.adaptiveThreshold(cropped_receipt, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, \
                                            cv2.THRESH_BINARY, 39, 25)
    if debug:
        cv2.drawContours(img, contours, -1, (0, 255, 0), 3)
        cv2.imshow('Original ', gray)
        cv2.imshow('Contour ', img)
        cv2.imshow('Cropped', cropped_receipt)
        cv2.waitKey()
        cv2.destroyAllWindows()
    return cropped_receipt


def ocr_image(cropped_receipt):
    data = pytesseract.image_to_data(cropped_receipt, output_type=Output.DICT)
    img_h = cropped_receipt.shape[0]
    img_w = cropped_receipt.shape[1]
    current_gl_line = 0
    current_block = -1
    current_line = -1
    current_par = -1
    result = {}
    result_text = ""
    # Organise Data per line and record position metadata
    for i in range(len(data['line_num'])):
        txt = data['text'][i].lower().replace(',', '.')
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
            # Add text in line
            if current_gl_line not in result:
                result[current_gl_line] = {}
                result[current_gl_line]['text'] = txt
                result[current_gl_line]['words'] = {}
                j = 0
            else:
                result[current_gl_line]['text'] = result[current_gl_line]['text'] + " " + txt
            # Record words metadata
            result[current_gl_line]['words'][j] = {}
            result[current_gl_line]['words'][j]['text'] = txt
            result[current_gl_line]['words'][j]['rect'] = Rect(left, top, height, width)
            j = j + 1
            # Record left of the line and be sure we get the top left point
            if 'left' not in result[current_gl_line]:
                result[current_gl_line]['left'] = left
            if 'top' not in result[current_gl_line]:
                result[current_gl_line]['top'] = top
            if 'height' not in result[current_gl_line]:
                result[current_gl_line]['height'] = height
            if 'width' not in result[current_gl_line]:
                result[current_gl_line]['width'] = width
            # ensure we include all words in line in width
            else:
                new_width = left + width - result[current_gl_line]['left']
                if new_width > result[current_gl_line]['width']:
                    result[current_gl_line]['width'] = new_width
    for i in result:
        result[i]['left'] = result[i]['left'] / img_w
        result[i]['width'] = result[i]['width'] / img_w
        result[i]['top'] = result[i]['top'] / img_h
        result[i]['height'] = result[i]['height'] / img_h
        if result_text == "":
            result_text = str(result[i]['text']) + '\n'
        else:
            result_text = result_text + str(result[i]['text']) + '\n'
    return result, result_text


def record_receipt(text, text_data, path, shape):
    img_h = shape[0]
    img_w = shape[1]
    buf = io.StringIO(text)
    name = buf.readline().replace('\n', '')
    params = {}
    # Extract all common parameters of the shop and receipt (name, address, etc.)
    for param in REGEX_RECEIPT:
        matches = re.finditer(param[1], text, re.MULTILINE)
        for match in matches:
            if param[0] == "date":
                # get the smallest date to avoid future date coupon validity
                if 'date' in params.keys():
                    if datetime.strptime(params['date'], '%d/%m/%Y') > \
                            datetime.strptime(match.group('date'), '%d/%m/%Y'):
                        params['date'] = match.group(param[0])
                else:
                    params[param[0]] = match.group(param[0])
            else:
                params[param[0]] = match.group(param[0])
            break
    if params.get('date', None) is not None:
        params['date'] = datetime.strptime(params['date'], '%d/%m/%Y')
    else:
        params['date'] = date.today()
    total_price, pos_y_total_price = find_total_price(text_data)

    shop = Shop(name=name, address=params.get('address', "NO_ADDRESS"), postcode=params.get('postcode', "00000"),
                city=params.get('city', "NO_CITY"), siret=params.get('siret', "NO_SIRET"),
                phone=params.get('phone', "NO_PHONE"))
    query_shop = session.query(Shop.id).filter(
        or_(Shop.name == shop.name, Shop.siret == params.get('siret', ""),
            Shop.phone == params.get('phone', ""))).first()
    if query_shop is None:
        session.add(shop)
        session.commit()
    else:
        shop = query_shop
    price_column = locate_price_column(pos_y_total_price, text_data)
    receipt = Receipt(shop_id=shop.id, date=params.get('date', ""),
                      total_price=total_price, file=os.path.basename(path), prices_pos_top=price_column.y,
                      prices_pos_left=price_column.x, prices_pos_width=price_column.width,
                      prices_pos_height=price_column.height, img_width=img_w, img_height=img_h,
                      pos_y_total_price=pos_y_total_price)
    exists = session.query(Receipt.id).filter(Receipt.file == receipt.file).first() is not None
    if not exists:
        session.add(receipt)
        session.commit()
    return receipt


def locate_price_column(pos_y_total_price, text_data):
    # locate product price column in the receipt (should be above the total price)
    price_column = Rect(y=pos_y_total_price)
    for i in text_data:
        # Don't find prices after total price position
        if text_data[i]['words'][0]['rect'].y > pos_y_total_price:
            continue
        line_txt = text_data[i]['text']
        matches = re.finditer(REGEX_PRICE, line_txt, re.MULTILINE)
        for match in matches:
            price = match.group('price')
            # get price coordinates
            price_rect = None
            for j in text_data[i]['words']:
                if price in text_data[i]['words'][j]['text']:
                    price_rect = text_data[i]['words'][j]['rect']
            if price_rect is None:
                break
            if price_column.is_vertical_overlap(price_rect, MIN_OVERLAP):
                # Adjust price column (i.e photo was taken in diagonal)
                right_rect = price_column.get_side_right(price_rect)
                left_rect = price_column.get_side_left(price_rect)
                price_column.x = left_rect.x
                price_column.width = right_rect.x + right_rect.width - left_rect.x
            elif (outer_rect := price_column.get_outer_rect(price_rect)) is not None:
                price_column.x = outer_rect.x
                price_column.width = outer_rect.width
            else:
                # Reset price column only if it is at the beginning of the receipt
                if text_data[i]['words'][0]['rect'].y < pos_y_total_price * MAX_START_COLUMN_PRICE:
                    right_rect = price_column.get_side_right(price_rect)
                    price_column.x = right_rect.x
                    price_column.width = right_rect.width
            price_column.y = price_column.get_upper(price_rect).y
            price_column.height = pos_y_total_price - price_column.y
    return price_column


def find_total_price(text_data):
    total_price = 0
    pos_y_total_price = 0
    for i in text_data:
        line_txt = text_data[i]['text']
        if 'total' in line_txt:
            matches = re.finditer(REGEX_PRICE, line_txt, re.MULTILINE)
            for match in matches:
                # Find the highest total price in the receipt
                if float(match.group('price')) > total_price:
                    total_price = float(match.group('price'))
                    pos_y_total_price = text_data[i]['words'][0]['rect'].y
    return total_price, pos_y_total_price


def record_products(text, receipt_id):
    matches = re.finditer(REGEX_PRODUCT, text, re.MULTILINE)
    for match in matches:
        product_name = match.group('product')
        quantity = int(match.group('qte'))
        price = float(match.group('price').replace(',', '.'))
        unit_price = price / quantity
        add_product(price, product_name, quantity, receipt_id, unit_price)
    return None


def add_product(product_name, quantity, unit_price, price, receipt_id):
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
                               pos_top=0, pos_left=0, pos_width=0, pos_height=0)
    session.add(paid_product)
    session.commit()


def is_product_line(text_data_i, column_price):
    matches = re.finditer(REGEX_PRICE, text_data_i['text'], re.MULTILINE)
    for match in matches:
        price = match.group('price')
        # Check if price is in price column
        for j in text_data_i['words']:
            if price in text_data_i['words'][j]['text']:
                price_rect = text_data_i['words'][j]['rect']
                if price_rect.is_inside(column_price):
                    return float(price)
    return False


def record_products_pos(text_data, receipt):
    if receipt is None:
        return
    column_price = Rect(receipt.prices_pos_left, receipt.prices_pos_top, receipt.prices_pos_height,
                        receipt.prices_pos_width)
    for i in text_data:
        if text_data[i]['words'][0]['rect'].y >= receipt.pos_y_total_price:
            continue
        # Get product from line
        if price := is_product_line(text_data[i], column_price):
            # Remove prices
            quantity = 0
            product_text = re.sub(REGEX_PRICES, '', text_data[i]['text'])
            product_text = re.sub(REGEX_BEGIN_SPACES, '', product_text)
            product_text = re.sub(REGEX_END_SPACES, '', product_text)
            matches = re.finditer(REGEX_PRODUCT_QTY, product_text, re.MULTILINE)
            for match in matches:
                quantity = int(match.group('qte'))
                product_name = match.group('product')
            if quantity == 0:
                # Quantity not found in product line set 0
                quantity = 1
                product_name = product_text
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
            paid_product = PaidProduct(receipt_id=receipt.id, product_group_id=product.product_group_id,
                                       quantity=quantity, price=price, unit_price=unit_price,
                                       pos_top=text_data[i]['top'], pos_left=text_data[i]['left'],
                                       pos_width=text_data[i]['width'], pos_height=text_data[i]['height'])
            session.add(paid_product)
            session.commit()
    return None


def add_new_receipt(image_path, debug=False):
    cropped_receipt = prepare_img(image_path, debug)
    cv2.imwrite(image_path, cropped_receipt)
    receipt_data, receipt_text = ocr_image(cropped_receipt)
    f = open(RECOGNIZED_TXT, 'w+')
    f.write(receipt_text)
    f.close()
    receipt = record_receipt(receipt_text, receipt_data, image_path, cropped_receipt.shape)

    if receipt is not None:
        # record_products(receipt_data, r_id)
        record_products_pos(receipt_data, receipt)

#add_new_receipt(image_path_expl, debug=True)
#prepare_img(image_path_expl, debug=True)
