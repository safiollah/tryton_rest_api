# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.pool import Pool

__all__ = ['register']

from . import product, sale, web


def register():
    Pool.register(
        web.Shop,
        web.Shop_Warehouse,
        web.Shop_Country,
        web.Shop_Product,
        web.Shop_ProductCategory,
        web.User,
        product.Template,
        product.Product,
        product.Category,
        sale.Sale,
        module='web_shop', type_='model')
    Pool.register(
        web.ShopAttribute,
        web.Shop_Attribute,
        product.Attribute,
        module='web_shop', type_='model', depends=['product_attribute'])
    Pool.register(
        product.Image,
        module='web_shop', type_='model', depends=['product_image'])
    Pool.register(
        web.Shop_PriceList,
        module='web_shop', type_='model', depends=['sale_price_list'])
    Pool.register(
        web.Shop_TaxRuleCountry,
        module='web_shop', type_='model', depends=['account_tax_rule_country'])
