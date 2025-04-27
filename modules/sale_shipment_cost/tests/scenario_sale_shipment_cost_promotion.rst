=====================================
Sale Shipment Cost Promotion Scenario
=====================================

Imports::

    >>> from decimal import Decimal

    >>> from proteus import Model
    >>> from trytond.modules.account.tests.tools import create_chart, get_accounts
    >>> from trytond.modules.company.tests.tools import create_company
    >>> from trytond.modules.currency.tests.tools import get_currency
    >>> from trytond.tests.tools import activate_modules

Activate modules::

    >>> config = activate_modules([
    ...         'sale_shipment_cost',
    ...         'sale',
    ...         'sale_promotion',
    ...         ],
    ...     create_company, create_chart)

Get accounts::

    >>> accounts = get_accounts()

Create customer::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create account category::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_revenue = accounts['revenue']
    >>> account_category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])

    >>> template = ProductTemplate()
    >>> template.name = 'Product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.salable = True
    >>> template.list_price = Decimal('20')
    >>> template.account_category = account_category
    >>> template.save()
    >>> product, = template.products

    >>> carrier_template = ProductTemplate()
    >>> carrier_template.name = 'Carrier Product'
    >>> carrier_template.default_uom = unit
    >>> carrier_template.type = 'service'
    >>> carrier_template.salable = True
    >>> carrier_template.list_price = Decimal('3')
    >>> carrier_template.account_category = account_category
    >>> carrier_template.save()
    >>> carrier_product, = carrier_template.products

Create Promotion::

    >>> Promotion = Model.get('sale.promotion')
    >>> promotion = Promotion(name='product 2 free')
    >>> promotion.amount = Decimal('101')
    >>> promotion.amount_shipment_cost_included = False
    >>> promotion.currency = get_currency()
    >>> promotion.products.extend([Product(carrier_product.id)])
    >>> promotion.formula = '0.0'
    >>> promotion.save()

Create carrier::

    >>> Carrier = Model.get('carrier')
    >>> carrier = Carrier()
    >>> party = Party(name='Carrier')
    >>> party.save()
    >>> carrier.party = party
    >>> carrier.carrier_product = carrier_product
    >>> carrier.save()

Sale products without the promotion::

    >>> Sale = Model.get('sale.sale')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.carrier = carrier
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 5.0
    >>> sale.click('quote')
    >>> cost_line = sale.lines[-1]
    >>> cost_line.amount
    Decimal('3.00')

Increase sale to get the promotion::

    >>> sale.click('draft')
    >>> line = sale.lines[0]
    >>> line.quantity = 6.0
    >>> sale.click('quote')
    >>> cost_line = sale.lines[-1]
    >>> cost_line.amount
    Decimal('0.00')
