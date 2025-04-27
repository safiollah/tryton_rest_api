# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import datetime as dt
from decimal import Decimal

from trytond.modules.account.tests import create_chart
from trytond.modules.company.tests import (
    CompanyTestMixin, PartyCompanyCheckEraseMixin, create_company, set_company)
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.transaction import Transaction


class PurchaseTestCase(
        PartyCompanyCheckEraseMixin, CompanyTestMixin, ModuleTestCase):
    'Test Purchase module'
    module = 'purchase'

    @with_transaction()
    def test_purchase_price(self):
        'Test purchase price'
        pool = Pool()
        Account = pool.get('account.account')
        Template = pool.get('product.template')
        Product = pool.get('product.product')
        Uom = pool.get('product.uom')
        ProductSupplier = pool.get('purchase.product_supplier')
        Party = pool.get('party.party')
        Purchase = pool.get('purchase.purchase')

        company = create_company()
        with set_company(company):
            create_chart(company)

            receivable, = Account.search([
                    ('closed', '!=', True),
                    ('type.receivable', '=', True),
                    ('party_required', '=', True),
                    ('company', '=', company.id),
                    ], limit=1)
            payable, = Account.search([
                    ('closed', '!=', True),
                    ('type.payable', '=', True),
                    ('party_required', '=', True),
                    ('company', '=', company.id),
                    ], limit=1)

            kg, = Uom.search([('name', '=', 'Kilogram')])
            g, = Uom.search([('name', '=', 'Gram')])

            template, = Template.create([{
                        'name': 'Product',
                        'default_uom': g.id,
                        'purchase_uom': kg.id,
                        'list_price': Decimal(5),
                        'purchasable': True,
                        'products': [('create', [{
                                        'cost_price': Decimal(3),
                                        }])],
                        }])
            product, = template.products

            supplier, = Party.create([{
                        'name': 'Supplier',
                        'account_receivable': receivable.id,
                        'account_payable': payable.id,
                        'addresses': [('create', [{}])],
                        }])
            product_supplier, = ProductSupplier.create([{
                        'template': template.id,
                        'party': supplier.id,
                        'prices': [('create', [{
                                        'sequence': 1,
                                        'quantity': 1,
                                        'unit_price': Decimal(3000),
                                        }, {
                                        'sequence': 2,
                                        'quantity': 2,
                                        'unit_price': Decimal(2500),
                                        }])],
                        }])

            purchase, = Purchase.create([{
                        'party': supplier.id,
                        'invoice_address': supplier.addresses[0].id,
                        'purchase_date': dt.date.today(),
                        'lines': [('create', [{
                                        'product': product.id,
                                        'quantity': 10,
                                        'unit': kg.id,
                                        'unit_price': Decimal(2000),
                                        }])],
                        }])
            purchase.state = 'confirmed'
            purchase.save()

            prices = Product.get_purchase_price([product], quantity=100)
            self.assertEqual(prices, {product.id: Decimal(2)})
            prices = Product.get_purchase_price([product], quantity=1500)
            self.assertEqual(prices, {product.id: Decimal(2)})

            with Transaction().set_context(uom=kg.id):
                prices = Product.get_purchase_price([product], quantity=0.5)
                self.assertEqual(prices, {product.id: Decimal(2000)})
                prices = Product.get_purchase_price([product], quantity=1.5)
                self.assertEqual(prices, {product.id: Decimal(2000)})

            with Transaction().set_context(supplier=supplier.id):
                prices = Product.get_purchase_price([product], quantity=100)
                self.assertEqual(prices, {product.id: Decimal(2)})
                prices = Product.get_purchase_price([product], quantity=1500)
                self.assertEqual(prices, {product.id: Decimal(3)})
                prices = Product.get_purchase_price([product], quantity=3000)
                self.assertEqual(prices, {product.id: Decimal('2.5')})

            with Transaction().set_context(uom=kg.id, supplier=supplier.id):
                prices = Product.get_purchase_price([product], quantity=0.5)
                self.assertEqual(prices, {product.id: Decimal(2000)})
                prices = Product.get_purchase_price([product], quantity=1.5)
                self.assertEqual(prices, {product.id: Decimal(3000)})
                prices = Product.get_purchase_price([product], quantity=3)
                self.assertEqual(prices, {product.id: Decimal(2500)})
                prices = Product.get_purchase_price([product], quantity=-4)
                self.assertEqual(prices, {product.id: Decimal(2500)})


del ModuleTestCase
