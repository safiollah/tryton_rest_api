==============================
Stock Supply Forecast Scenario
==============================

Imports::

    >>> import datetime as dt
    >>> from decimal import Decimal

    >>> from proteus import Model, Wizard
    >>> from trytond.modules.account.tests.tools import create_chart, get_accounts
    >>> from trytond.modules.company.tests.tools import create_company
    >>> from trytond.tests.tools import activate_modules, assertEqual

    >>> today = dt.date.today()
    >>> yesterday = today - dt.timedelta(days=1)
    >>> tomorrow = today + dt.timedelta(days=1)

Activate modules::

    >>> config = activate_modules(
    ...     'stock_supply_forecast', create_company, create_chart)

Get accounts::

    >>> accounts = get_accounts()
    >>> expense = accounts['expense']

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()

Create account category::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_expense = expense
    >>> account_category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> ProductTemplate = Model.get('product.template')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])

    >>> template = ProductTemplate()
    >>> template.name = 'Product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('20')
    >>> template.purchasable = True
    >>> template.account_category = account_category
    >>> template.save()
    >>> product, = template.products

Get warehouse location::

    >>> Location = Model.get('stock.location')
    >>> warehouse_loc, = Location.find([('code', '=', 'WH')])

Create a forecast::

    >>> Forecast = Model.get('stock.forecast')
    >>> forecast = Forecast()
    >>> forecast.warehouse = warehouse_loc
    >>> forecast.from_date = yesterday
    >>> forecast.to_date = tomorrow
    >>> forecast_line = forecast.lines.new()
    >>> forecast_line.product = product
    >>> forecast_line.quantity = 10
    >>> forecast.save()

There is no purchase request::

    >>> create_pr = Wizard('stock.supply')
    >>> create_pr.execute('create_')
    >>> PurchaseRequest = Model.get('purchase.request')
    >>> PurchaseRequest.find([])
    []

There is a draft purchase request after confirming the forecast::

    >>> forecast.click('confirm')
    >>> create_pr = Wizard('stock.supply')
    >>> create_pr.execute('create_')
    >>> pr, = PurchaseRequest.find([('state', '=', 'draft')])
    >>> assertEqual(pr.product, product)
    >>> pr.quantity
    10.0
