# -*- encoding: utf-8 -*-

from app.home_receipt import blueprint
from flask import render_template, request, redirect, url_for, json
from app.home_receipt.models import *
from app.home_receipt.ocr_receipt import add_new_receipt, add_product
from sqlalchemy import update
from sqlalchemy import func
from wtforms import Form, BooleanField, StringField, PasswordField, validators, FloatField, IntegerField


class AddProductForm(Form):
    product_name = StringField('Product Name', [validators.DataRequired(), validators.Length(min=4, max=25)])
    quantity = IntegerField('Quantity', [validators.DataRequired(), validators.number_range(min=1)])
    unit_price = FloatField('Quantity', [validators.DataRequired(), validators.number_range(min=0)])
    price = FloatField('Quantity', [validators.DataRequired(), validators.number_range(min=0)])

@blueprint.route('/add_product/<id_receipt>', methods=['POST'])
def user_add_product(id_receipt):
    form = AddProductForm(request.form)
    add_product(form.product_name.data, form.quantity.data, form.unit_price.data, form.price.data, id_receipt)
    return redirect(url_for('receipt_blueprint.receipt_detail', id_receipt=id_receipt))

@blueprint.route('/del_product/<id_receipt>/<id_paid_product>', methods=['GET'])
def user_del_product(id_receipt, id_paid_product):
    PaidProduct.query.filter_by(id=id_paid_product).delete()
    db.session.commit()
    return redirect(url_for('receipt_blueprint.receipt_detail', id_receipt=id_receipt))

@blueprint.app_template_filter('strftime')
def _jinja2_filter_datetime(date):
    return date.strftime("%d %B, %Y")

@blueprint.route('/')
def route_default():
    return redirect(url_for('receipt_blueprint.index'))

@blueprint.route('/test')
def test():
    return render_template('home-receipt/test.html')

@blueprint.route('/index')
def index():
    #add_new_receipt('/Users/arnaudrover/PycharmProjects/ocr-receipt/receipts/IMG_9768.jpg')
    query = db.session.query(Receipt, Shop).join(Receipt, Receipt.shop_id == Shop.id).\
        order_by(Receipt.date.desc()).all()
    return render_template('home-receipt/receipts_table.html', title='Bootstrap Table', query=query)

@blueprint.route('/receipt/<id_receipt>')
def receipt_detail(id_receipt):
    form = AddProductForm(request.form)
    query_products = db.session.query(PaidProduct, ProductGroup).\
        join(ProductGroup, PaidProduct.product_group_id == ProductGroup.id).\
        filter(PaidProduct.receipt_id == id_receipt).order_by(PaidProduct.id.asc()).all()
    query_receipt, query_shop = db.session.query(Receipt, Shop).\
        join(Shop, Receipt.shop_id == Shop.id).filter(Receipt.id == id_receipt).first()
    product_sum = db.session.query(func.sum(PaidProduct.price)).filter_by(receipt_id=id_receipt).\
        group_by(PaidProduct.receipt_id).first()
    delta_sum = 0
    if product_sum is not None:
        delta_sum = round(query_receipt.total_price - product_sum[0],2)
    else:
        delta_sum = query_receipt.total_price
    return render_template('home-receipt/receipt_details_table.html', title='Bootstrap Table',
                           query_product=query_products, receipt=query_receipt, shop=query_shop, delta=delta_sum,
                           form=form)

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
            old_group_id = paid_product.product_group_id
            if product_group is None:
                #no product group with this name exits --> update current product group name
                product_group = ProductGroup.query.filter_by(id=paid_product.product_group_id).first()
            else:
                if product_group.id == old_group_id:
                    #Nothing to change
                    return
                #Link all existing product(s) attached to the existing product Group to the new one
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

@blueprint.route('/update_shop', methods=['POST'])
def update_shop():
    pk = request.form['pk']
    name = request.form['name']
    value = request.form['value']
    shop = Shop.query.filter_by(id=pk).first()
    if shop is None:
        # TODO Error return
        return json.dumps({'status': 'OK'})
    shop.name = value
    db.session.commit()

@blueprint.route('/update_receipt', methods=['POST'])
def update_receipt():
    pk = request.form['pk']
    name = request.form['name']
    value = request.form['value']
    receipt = Receipt.query.filter_by(id=pk).first()
    if receipt is None:
        # TODO Error return
        return json.dumps({'status': 'OK'})
    receipt.total_price = value
    db.session.commit()


