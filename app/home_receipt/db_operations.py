from app.home_receipt.models import *

def delete_orphan_shops():
    ophan_shops = db.session.query(Shop).join(Receipt, Receipt.shop_id == Shop.id, isouter=True).\
        filter(Receipt.shop_id == None).all()
    for orphan in ophan_shops:
        db.session.query(Shop).filter_by(id=orphan.id).delete()
    db.session.commit()

def delete_receipt_and_paid_products(id_receipt):
    PaidProduct.query.filter_by(receipt_id=id_receipt).delete()
    db.session.commit()
    Receipt.query.filter_by(id=id_receipt).delete()
    db.session.commit()

def get_shops():
    shops = db.session.query(Shop).all()
    choices = []
    for shop in shops:
        choices.append((int(shop.id), shop.name))
    return choices