===================
Production Scenario
===================

Imports::

    >>> import datetime as dt
    >>> from decimal import Decimal

    >>> from proteus import Model
    >>> from trytond.modules.company.tests.tools import create_company
    >>> from trytond.tests.tools import activate_modules, assertEqual, assertNotEqual

    >>> today = dt.date.today()
    >>> yesterday = today - dt.timedelta(days=1)
    >>> before_yesterday = yesterday - dt.timedelta(days=1)

Activate modules::

    >>> config = activate_modules('production', create_company)

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')

    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.producible = True
    >>> template.list_price = Decimal(30)
    >>> product, = template.products
    >>> product.cost_price = Decimal(20)
    >>> template.save()
    >>> product, = template.products

Create Components::

    >>> template1 = ProductTemplate()
    >>> template1.name = 'component 1'
    >>> template1.default_uom = unit
    >>> template1.type = 'goods'
    >>> template1.list_price = Decimal(5)
    >>> component1, = template1.products
    >>> component1.cost_price = Decimal(1)
    >>> template1.save()
    >>> component1, = template1.products

    >>> meter, = ProductUom.find([('name', '=', 'Meter')])
    >>> centimeter, = ProductUom.find([('name', '=', 'Centimeter')])

    >>> template2 = ProductTemplate()
    >>> template2.name = 'component 2'
    >>> template2.default_uom = meter
    >>> template2.type = 'goods'
    >>> template2.list_price = Decimal(7)
    >>> component2, = template2.products
    >>> component2.cost_price = Decimal(5)
    >>> template2.save()
    >>> component2, = template2.products

Create Bill of Material::

    >>> BOM = Model.get('production.bom')
    >>> BOMInput = Model.get('production.bom.input')
    >>> BOMOutput = Model.get('production.bom.output')
    >>> bom = BOM(name='product')
    >>> input1 = BOMInput()
    >>> bom.inputs.append(input1)
    >>> input1.product = component1
    >>> input1.quantity = 5
    >>> input2 = BOMInput()
    >>> bom.inputs.append(input2)
    >>> input2.product = component2
    >>> input2.quantity = 150
    >>> input2.unit = centimeter
    >>> output = BOMOutput()
    >>> bom.outputs.append(output)
    >>> output.product = product
    >>> output.quantity = 1
    >>> bom.save()

    >>> ProductBom = Model.get('product.product-production.bom')
    >>> product.boms.append(ProductBom(bom=bom))
    >>> product.save()

    >>> ProductionLeadTime = Model.get('production.lead_time')
    >>> production_lead_time = ProductionLeadTime()
    >>> production_lead_time.product = product
    >>> production_lead_time.bom = bom
    >>> production_lead_time.lead_time = dt.timedelta(1)
    >>> production_lead_time.save()

Create an Inventory::

    >>> Inventory = Model.get('stock.inventory')
    >>> InventoryLine = Model.get('stock.inventory.line')
    >>> Location = Model.get('stock.location')
    >>> storage, = Location.find([
    ...         ('code', '=', 'STO'),
    ...         ])
    >>> inventory = Inventory()
    >>> inventory.location = storage
    >>> inventory_line1 = InventoryLine()
    >>> inventory.lines.append(inventory_line1)
    >>> inventory_line1.product = component1
    >>> inventory_line1.quantity = 20
    >>> inventory_line2 = InventoryLine()
    >>> inventory.lines.append(inventory_line2)
    >>> inventory_line2.product = component2
    >>> inventory_line2.quantity = 6
    >>> inventory.click('confirm')
    >>> inventory.state
    'done'

Make a production::

    >>> Production = Model.get('production')
    >>> production = Production()
    >>> production.planned_date = today
    >>> production.product = product
    >>> production.bom = bom
    >>> production.quantity = 2
    >>> assertEqual(production.planned_start_date, yesterday)
    >>> sorted([i.quantity for i in production.inputs])
    [10.0, 300.0]
    >>> output, = production.outputs
    >>> output.quantity
    2.0
    >>> production.save()
    >>> production.cost
    Decimal('25.0000')
    >>> production.number
    >>> production.click('wait')
    >>> production.state
    'waiting'
    >>> assertNotEqual(production.number, None)

Test reset bom button::

    >>> for input in production.inputs:
    ...     input.quantity += 1
    >>> production.click(
    ...     'reset_bom',
    ...     change=[
    ...         'bom', 'product', 'unit', 'quantity',
    ...         'inputs', 'outputs', 'company', 'warehouse', 'location'])
    >>> sorted([i.quantity for i in production.inputs])
    [10.0, 300.0]
    >>> output, = production.outputs
    >>> output.quantity
    2.0

Do the production::

    >>> production.click('assign_try')
    >>> production.state
    'assigned'
    >>> {i.state for i in production.inputs}
    {'assigned'}
    >>> production.click('run')
    >>> {i.state for i in production.inputs}
    {'done'}
    >>> for input_ in production.inputs:
    ...     assertEqual(input_.effective_date, today)
    >>> production.click('do')
    >>> output, = production.outputs
    >>> output.state
    'done'
    >>> assertEqual(output.effective_date, production.effective_date)
    >>> output.unit_price
    Decimal('12.5000')
    >>> with config.set_context(locations=[storage.id]):
    ...     Product(product.id).quantity
    2.0

Make a production with effective date yesterday and running the day before::

    >>> Production = Model.get('production')
    >>> production = Production()
    >>> production.effective_date = yesterday
    >>> production.effective_start_date = before_yesterday
    >>> production.product = product
    >>> production.bom = bom
    >>> production.quantity = 2
    >>> production.click('wait')
    >>> production.click('assign_try')
    >>> production.click('run')
    >>> production.reload()
    >>> for input_ in production.inputs:
    ...     assertEqual(input_.effective_date, before_yesterday)
    >>> production.click('do')
    >>> production.reload()
    >>> output, = production.outputs
    >>> assertEqual(output.effective_date, yesterday)

Make a production with a bom of zero quantity::

    >>> zero_bom, = BOM.duplicate([bom])
    >>> for input_ in bom.inputs:
    ...     input_.quantity = 0.0
    >>> bom_output, = bom.outputs
    >>> bom_output.quantity = 0.0
    >>> bom.save()
    >>> production = Production()
    >>> production.product = product
    >>> production.bom = bom
    >>> production.planned_start_date = yesterday
    >>> production.quantity = 2
    >>> [i.quantity for i in production.inputs]
    [0.0, 0.0]
    >>> output, = production.outputs
    >>> output.quantity
    0.0

Reschedule productions::

    >>> production.click('wait')
    >>> Cron = Model.get('ir.cron')
    >>> cron = Cron(method='production|reschedule')
    >>> cron.interval_number = 1
    >>> cron.interval_type = 'months'
    >>> cron.click('run_once')
    >>> production.reload()
    >>> assertEqual(production.planned_start_date, today)
