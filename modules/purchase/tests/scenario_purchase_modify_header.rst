===============================
Purchase Modify Header Scenario
===============================

Imports::

    >>> from decimal import Decimal

    >>> from proteus import Model
    >>> from trytond.modules.account.tests.tools import (
    ...     create_chart, create_tax, get_accounts)
    >>> from trytond.modules.company.tests.tools import create_company
    >>> from trytond.tests.tools import activate_modules, assertEqual

Activate modules::

    >>> config = activate_modules('purchase', create_company, create_chart)

Get accounts::

    >>> accounts = get_accounts()
    >>> expense = accounts['expense']

Create tax and tax rule::

    >>> tax = create_tax(Decimal('.10'))
    >>> tax.save()

    >>> TaxRule = Model.get('account.tax.rule')
    >>> foreign = TaxRule(name='Foreign Suppliers')
    >>> no_tax = foreign.lines.new()
    >>> no_tax.origin_tax = tax
    >>> foreign.save()

Create account categories::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_expense = expense
    >>> account_category.supplier_taxes.append(tax)
    >>> account_category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')

    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.list_price = Decimal('10')
    >>> template.account_category = account_category
    >>> template.save()
    >>> product, = template.products

Create parties::

    >>> Party = Model.get('party.party')
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()
    >>> another = Party(name='Another Supplier', supplier_tax_rule=foreign)
    >>> another.save()

Create a sale with a line::

    >>> Purchase = Model.get('purchase.purchase')
    >>> purchase = Purchase()
    >>> purchase.party = supplier
    >>> purchase_line = purchase.lines.new()
    >>> purchase_line.product = product
    >>> purchase_line.quantity = 3
    >>> purchase_line.unit_price = Decimal('5.0000')
    >>> purchase_line_comment = purchase.lines.new(type='comment')
    >>> purchase.save()
    >>> purchase.untaxed_amount, purchase.tax_amount, purchase.total_amount
    (Decimal('15.00'), Decimal('1.50'), Decimal('16.50'))

Change the party::

    >>> modify_header = purchase.click('modify_header')
    >>> assertEqual(modify_header.form.party, supplier)
    >>> modify_header.form.party = another
    >>> modify_header.execute('modify')

    >>> purchase.party.name
    'Another Supplier'
    >>> purchase.untaxed_amount, purchase.tax_amount, purchase.total_amount
    (Decimal('15.00'), Decimal('0'), Decimal('15.00'))
