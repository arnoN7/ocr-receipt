# -*- encoding: utf-8 -*-
from datetime import datetime

from app.home_receipt import blueprint
from flask import render_template, request, redirect, url_for, json
from app.home_receipt.models import *
from app.home_receipt.ocr_receipt import add_new_receipt, add_product
from sqlalchemy import update
from sqlalchemy import func
from wtforms import Form, StringField, validators, FloatField, IntegerField, SelectField, DateField
from flask_breadcrumbs import Breadcrumbs, register_breadcrumb
import app.home_receipt.breadcrumb as bc
import app.home_receipt.db_operations as op



class AddProductForm(Form):
    product_name = StringField('Product Name', [validators.DataRequired(), validators.Length(min=4, max=25)])
    quantity = IntegerField('Quantity', [validators.DataRequired(), validators.number_range(min=1)])
    unit_price = FloatField('Unit Price', [validators.DataRequired(), validators.number_range(min=0)])
    price = FloatField('Price', [validators.DataRequired(), validators.number_range(min=0)])

class UpdateReceiptOverviewForm(Form):
    shop_select = SelectField("Merge with another shop", validate_choice=False)
    total_price = FloatField('Total Price', [validators.DataRequired(), validators.number_range(min=0)])
    date = DateField('Date', [validators.DataRequired()], "%d-%m-%Y")

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
@register_breadcrumb(blueprint, '.', 'Home')
def index():
    #add_new_receipt('/Users/arnaudrover/PycharmProjects/ocr-receipt/receipts/IMG_9768.jpg')
    query = db.session.query(Receipt, Shop).join(Receipt, Receipt.shop_id == Shop.id). \
        order_by(Receipt.date.desc()).all()
    return render_template('home-receipt/receipts_table.html', title='Bootstrap Table', query=query)

@blueprint.route('/shops')
@register_breadcrumb(blueprint, '.shops', 'Shops')
def shops():
    query = db.session.\
        query(Shop, func.count(Receipt.id), func.sum(Receipt.total_price), func.avg(Receipt.total_price)).\
        join(Receipt, Receipt.shop_id == Shop.id).group_by(Shop.id). \
        order_by(Shop.name.asc()).all()
    return render_template('home-receipt/shops_table.html', title='Bootstrap Table', query=query)

@blueprint.route('/products')
@register_breadcrumb(blueprint, '.products', 'Products')
def products():
    query = db.session.\
        query(ProductGroup, func.count(PaidProduct.id), func.avg(PaidProduct.unit_price),
              func.min(PaidProduct.unit_price), func.max(PaidProduct.unit_price)).\
        join(PaidProduct, PaidProduct.product_group_id == ProductGroup.id).group_by(ProductGroup.name). \
        order_by(ProductGroup.name.asc()).all()
    return render_template('home-receipt/products_table.html', title='Bootstrap Table', query=query)

@blueprint.route('/receipt/<id_receipt>')
@register_breadcrumb(blueprint, '.receipt', '/', dynamic_list_constructor=bc.view_receipt_id)
def receipt_detail(id_receipt):
    form = AddProductForm(request.form)
    form_receipt = UpdateReceiptOverviewForm(request.form)
    form_receipt.shop_select.choices = op.get_shops()
    query_products = db.session.query(PaidProduct, ProductGroup).\
        join(ProductGroup, PaidProduct.product_group_id == ProductGroup.id).\
        filter(PaidProduct.receipt_id == id_receipt).order_by(PaidProduct.id.asc()).all()
    query_receipt, query_shop = db.session.query(Receipt, Shop).\
        join(Shop, Receipt.shop_id == Shop.id).filter(Receipt.id == id_receipt).first()
    product_sum = db.session.query(func.sum(PaidProduct.price)).filter_by(receipt_id=id_receipt).\
        group_by(PaidProduct.receipt_id).first()
    all_product_group = db.session.query(ProductGroup.name).all()
    product_all = []
    for product in all_product_group:
        product_all.append(product[0])
    if product_sum is not None:
        delta_sum = round(query_receipt.total_price - product_sum[0],2)
    else:
        delta_sum = query_receipt.total_price
    return render_template('home-receipt/receipt_details_table.html', title='Bootstrap Table',
                           query_product=query_products, receipt=query_receipt, shop=query_shop, delta=delta_sum,
                           form=form, products_all=product_all, form_receipt=form_receipt)

@blueprint.route('/product/<id_product>')
@register_breadcrumb(blueprint, '.products.id', '', dynamic_list_constructor=bc.view_product_id)
def product_detail(id_product):
    query = db.session. \
        query(Shop, PaidProduct, Receipt, ProductGroup). \
        join(PaidProduct, PaidProduct.product_group_id == ProductGroup.id).\
        join(Receipt, PaidProduct.receipt_id == Receipt.id).\
        join(Shop, Receipt.shop_id == Shop.id).\
        filter(ProductGroup.id == id_product).all()
    return render_template('home-receipt/product_detail.html', title='Bootstrap Table', query=query)

@blueprint.route('/shop/<id_shop>')
@register_breadcrumb(blueprint, '.shops.id', '', dynamic_list_constructor=bc.view_shop_id)
def shop_detail(id_shop):
    form = UpdateReceiptOverviewForm()
    img_path = ""
    shop = db.session.query(Shop).filter_by(id=id_shop).first()
    receipt = db.session.query(Receipt).filter_by(shop_id=id_shop).order_by(Receipt.date.desc()).first()
    if receipt is not None:
        img_path = receipt.file
    return render_template('home-receipt/shop_detail.html', title='Bootstrap Table', shop=shop, file=img_path,
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
    op.delete_receipt_and_paid_products(id_receipt)
    op.delete_orphan_shops()
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
    setattr(shop, name, value)
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
    if name == 'date':
        value = datetime.strptime(value, '%d-%m-%Y')
    setattr(receipt, name, value)
    db.session.commit()


