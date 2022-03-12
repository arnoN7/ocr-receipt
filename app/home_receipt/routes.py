# -*- encoding: utf-8 -*-

from app.home_receipt import blueprint
from flask import render_template, request, redirect, url_for, json
from app.home_receipt.models import *
from app.home_receipt.ocr_receipt import add_new_receipt
from sqlalchemy import update
from flask_login import login_required
from jinja2 import TemplateNotFound


@blueprint.route('/')
def route_default():
    return redirect(url_for('receipt_blueprint.index'))

@blueprint.route('/test')
def test():
    return render_template('home-receipt/test.html')

@blueprint.route('/index')
def index():
    #add_new_receipt('/Users/arnaudrover/PycharmProjects/ocr-receipt/receipts/IMG_9768.jpg')
    query = db.session.query(Receipt, Shop).all()
    return render_template('home-receipt/receipts_table.html', title='Bootstrap Table', query=query)

@blueprint.route('/receipt/<id_receipt>')
def receipt_detail(id_receipt):
    query = db.session.query(PaidProduct, ProductGroup).\
        join(ProductGroup, PaidProduct.product_group_id == ProductGroup.id).\
        filter(PaidProduct.receipt_id == id_receipt).all()
    return render_template('home-receipt/receipt_details_table.html', title='Bootstrap Table', query=query)

@blueprint.route('/receipt/add', methods=['POST'])
def receipt_add():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.filename = 'app/static/receipts/'+uploaded_file.filename
        uploaded_file.save(uploaded_file.filename)
        add_new_receipt(uploaded_file.filename)
    return redirect(url_for('receipt_blueprint.index'))

@blueprint.route('/receipt/del/<id_receipt>')
def receipt_delete(id_receipt):
    PaidProduct.query.filter_by(receipt_id=id_receipt).delete()
    Receipt.query.filter_by(id=id_receipt).delete()
    db.session.commit()
    return redirect(url_for('receipt_blueprint.index'))

@blueprint.route('/update_product', methods=['POST'])
def update_product_group():
        pk = request.form['pk']
        name = request.form['name']
        value = request.form['value']
        paid_product = PaidProduct.query.filter_by(id=pk).first()
        if paid_product is None :
            #TODO Error return
            return json.dumps({'status':'OK'})
        if name == 'unit_price' or name == 'price' or name == 'quantity':
            setattr(paid_product, name, value)
        elif name == 'name':
            #Try to find an existing product group with this name
            product_group = ProductGroup.query.filter_by(name=value).first()
            if product_group is None:
                #no product group with this name exits --> update current product group name
                product_group = ProductGroup.query.filter_by(id=paid_product.product_group_id).first()
            else:
                #Link all existing product(s) attached to the existing product Group to the new one
                old_group_id = paid_product.product_group_id
                update_products = update(Product).where(Product.product_group_id == old_group_id).\
                    values(product_group_id=product_group.id)
                update_paid_products = update(PaidProduct).where(PaidProduct.product_group_id == old_group_id). \
                    values(product_group_id=product_group.id)
                db.session.execute(update_products)
                db.session.execute(update_paid_products)
                paid_product.product_group_id = product_group.id
                #Delete Orphan Product Group
                ProductGroup.query.filter_by(id=old_group_id).delete()
            setattr(product_group, name, value)
        db.session.commit()
        print('pk={p} name = {name} value = {value}'.format(p=pk, name=name, value=value))
        return json.dumps({'status':'OK'})


