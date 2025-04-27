=================================================
Sale Supply Drop Shipment with Amendment Scenario
=================================================

Imports::

    >>> from decimal import Decimal

    >>> from proteus import Model, Wizard
    >>> from trytond.modules.account.tests.tools import create_chart, get_accounts
    >>> from trytond.modules.company.tests.tools import create_company
    >>> from trytond.tests.tools import activate_modules

Activate modules::

    >>> config = activate_modules([
    ...         'sale_supply_drop_shipment',
    ...         'sale_amendment',
    ...         ],
    ...     create_company, create_chart)

    >>> Party = Model.get('party.party')
    >>> ProductCategory = Model.get('product.category')
    >>> ProductSupplier = Model.get('purchase.product_supplier')
    >>> ProductTemplate = Model.get('product.template')
    >>> ProductUom = Model.get('product.uom')
    >>> Purchase = Model.get('purchase.purchase')
    >>> PurchaseRequest = Model.get('purchase.request')
    >>> Sale = Model.get('sale.sale')
    >>> Shipment = Model.get('stock.shipment.drop')

Get accounts::

    >>> accounts = get_accounts()

Create parties::

    >>> supplier = Party(name="Supplier")
    >>> supplier.save()
    >>> customer = Party(name="Customer")
    >>> customer.save()

Create account category::

    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_expense = accounts['expense']
    >>> account_category.account_revenue = accounts['revenue']
    >>> account_category.save()

Create product::

    >>> unit, = ProductUom.find([('name', '=', "Unit")])

    >>> template = ProductTemplate()
    >>> template.name = "Product"
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10.000')
    >>> template.supply_on_sale = 'always'
    >>> template.account_category = account_category
    >>> product_supplier = template.product_suppliers.new()
    >>> product_supplier.party = supplier
    >>> product_supplier.drop_shipment = True
    >>> template.save()
    >>> product, = template.products
    >>> product_supplier.save()

Sale 5 products::

    >>> sale = Sale(party=customer)
    >>> line = sale.lines.new()
    >>> line.product = product
    >>> line.quantity = 5
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.state
    'processing'

Create purchase::

    >>> purchase_request, = PurchaseRequest.find()
    >>> create_purchase = Wizard(
    ...     'purchase.request.create_purchase', [purchase_request])
    >>> purchase, = Purchase.find()
    >>> purchase.click('quote')
    >>> purchase.click('confirm')
    >>> purchase.state
    'processing'

    >>> shipment, = Shipment.find()
    >>> shipment.state
    'waiting'

Add an amendment::

    >>> amendment = sale.amendments.new()
    >>> line = amendment.lines.new()
    >>> line.action = 'line'
    >>> line.line, = sale.lines
    >>> line.quantity = 4
    >>> amendment.click('validate_amendment')
    >>> amendment.state
    'validated'

Check drop shipment::

    >>> supplier_move, = shipment.supplier_moves
    >>> supplier_move.quantity
    5.0
    >>> customer_move, = shipment.customer_moves
    >>> customer_move.quantity
    5.0
