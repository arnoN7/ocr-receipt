import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from app import db


Base = db.Model


class Shop(Base):

    __tablename__ = 'shop'

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)
    name = sa.Column(sa.String())
    address = sa.Column(sa.String())
    postcode = sa.Column(sa.Integer())
    city = sa.Column(sa.String())
    siret = sa.Column(sa.String())
    phone = sa.Column(sa.String())
    created_at = sa.Column(sa.TIMESTAMP(), server_default=func.now())


class Receipt(Base):

    __tablename__ = 'receipt'

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)
    shop_id = sa.Column(sa.Integer(), sa.ForeignKey('shop.id'))
    total_price = sa.Column(sa.Float())
    file = sa.Column(sa.String())
    date = sa.Column(sa.TIMESTAMP(), server_default=func.now())
    prices_pos_top = sa.Column(sa.Float())
    prices_pos_left = sa.Column(sa.Float())
    prices_pos_width = sa.Column(sa.Float())
    prices_pos_height = sa.Column(sa.Float())


class PaidProduct(Base):

    __tablename__ = 'paid_product'

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)
    receipt_id = sa.Column(sa.Integer(), sa.ForeignKey('receipt.id'))
    product_group_id = sa.Column(sa.Integer(), sa.ForeignKey('product_group.id'))
    quantity = sa.Column(sa.Integer())
    price = sa.Column(sa.Float())
    unit_price = sa.Column(sa.Float())
    pos_top = sa.Column(sa.Float())
    pos_left = sa.Column(sa.Float())
    pos_width = sa.Column(sa.Float())
    pos_height = sa.Column(sa.Float())


class ProductGroup(Base):

    __tablename__ = 'product_group'

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)
    name = sa.Column(sa.String())
    created_at = sa.Column(sa.TIMESTAMP(), server_default=func.now())


class Product(Base):

    __tablename__ = 'product'

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)
    name = sa.Column(sa.String())
    created_at = sa.Column(sa.TIMESTAMP(), server_default=func.now())
    product_group_id = sa.Column(sa.Integer(), sa.ForeignKey('product_group.id'))
