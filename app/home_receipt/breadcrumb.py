from flask import request, url_for
from app.home_receipt.models import *

def view_receipt_id(*args, **kwargs):
    id_receipt = request.view_args['id_receipt']
    return [{'text': '{id}'.format(id=id_receipt), 'url': ''}]

def view_product_id(*args, **kwargs):
    id_product_group = request.view_args['id_product']
    product_group = db.session.query(ProductGroup).filter_by(id=id_product_group).first()
    if product_group is not None:
        return [{'text': product_group.name, 'url': ''}]
    else:
        return [{'text': 'Product Not Found', 'url': ''}]

def view_shop_id(*args, **kwargs):
    id_shop = request.view_args['id_shop']
    shop = db.session.query(Shop).filter_by(id=id_shop).first()
    if shop is not None:
        return [{'text': shop.name, 'url': ''}]
    else:
        return [{'text': 'Shop Not Found', 'url': ''}]