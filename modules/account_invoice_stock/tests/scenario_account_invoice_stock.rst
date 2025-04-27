========================
Invoice - Stock Scenario
========================

Imports::

    >>> from decimal import Decimal

    >>> from proteus import Model
    >>> from trytond.modules.account.tests.tools import (
    ...     create_chart, create_fiscalyear, get_accounts)
    >>> from trytond.modules.account_invoice.tests.tools import (
    ...     set_fiscalyear_invoice_sequences)
    >>> from trytond.modules.company.tests.tools import create_company
    >>> from trytond.modules.currency.tests.tools import get_currency
    >>> from trytond.tests.tools import activate_modules

Activate modules::

    >>> config = activate_modules(
    ...     'account_invoice_stock', create_company, create_chart)

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear())
    >>> fiscalyear.click('create_period')

Get accounts::

    >>> accounts = get_accounts()

Create a party::

    >>> Party = Model.get('party.party')
    >>> party = Party(name="Party")
    >>> party.save()

Create an account category::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_expense = accounts['expense']
    >>> account_category.account_revenue = accounts['revenue']
    >>> account_category.save()

Create a product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('40')
    >>> template.account_category = account_category
    >>> template.save()
    >>> product, = template.products

Get stock locations::

    >>> Location = Model.get('stock.location')
    >>> output_loc, = Location.find([('code', '=', 'OUT')])
    >>> customer_loc, = Location.find([('code', '=', 'CUS')])

Create a shipment::

    >>> Shipment = Model.get('stock.shipment.out')
    >>> Move = Model.get('stock.move')
    >>> shipment = Shipment()
    >>> shipment.customer = party
    >>> move = shipment.outgoing_moves.new()
    >>> move.product = product
    >>> move.quantity = 10
    >>> move.from_location = output_loc
    >>> move.to_location = customer_loc
    >>> move.unit_price = Decimal('40.0000')
    >>> move.currency = get_currency()
    >>> shipment.click('wait')
    >>> shipment.state
    'waiting'
    >>> move, = shipment.outgoing_moves

Create an invoice for half the quantity with higher price::

    >>> Invoice = Model.get('account.invoice')
    >>> invoice = Invoice(type='out')
    >>> invoice.party = party
    >>> line = invoice.lines.new()
    >>> line.product = product
    >>> line.quantity = 5
    >>> line.unit_price = Decimal('50.0000')
    >>> line.stock_moves.append(Move(move.id))
    >>> invoice.click('post')
    >>> invoice.state
    'posted'

Check move unit price is not changed::

    >>> move.reload()
    >>> move.unit_price
    Decimal('40.0000')

Ship the products::

    >>> shipment.click('assign_force')
    >>> shipment.click('pick')
    >>> shipment.click('pack')
    >>> shipment.click('do')
    >>> shipment.state
    'done'

Check move unit price has been updated::

    >>> move.reload()
    >>> move.unit_price
    Decimal('50.0000')

Create a second invoice for the remaining quantity cheaper::

    >>> invoice = Invoice(type='out')
    >>> invoice.party = party
    >>> line = invoice.lines.new()
    >>> line.product = product
    >>> line.quantity = 5
    >>> line.unit_price = Decimal('40.0000')
    >>> line.stock_moves.append(Move(move.id))
    >>> invoice.click('post')
    >>> invoice.state
    'posted'

Check move unit price has been updated again::

    >>> move.reload()
    >>> move.unit_price
    Decimal('45.0000')
