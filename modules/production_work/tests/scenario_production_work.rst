========================
Production Work Scenario
========================

Imports::

    >>> import datetime as dt
    >>> from decimal import Decimal

    >>> from proteus import Model
    >>> from trytond.modules.company.tests.tools import create_company
    >>> from trytond.tests.tools import activate_modules, assertEqual, set_user

    >>> today = dt.date.today()

Activate modules::

    >>> config = activate_modules('production_work', create_company)

    >>> Employee = Model.get('company.employee')
    >>> Group = Model.get('res.group')
    >>> Party = Model.get('party.party')
    >>> User = Model.get('res.user')

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

    >>> template2 = ProductTemplate()
    >>> template2.name = 'component 2'
    >>> template2.default_uom = unit
    >>> template2.type = 'goods'
    >>> template2.list_price = Decimal(5)
    >>> component2, = template2.products
    >>> component2.cost_price = Decimal(1)
    >>> template2.save()
    >>> component2, = template2.products

Create work centers::

    >>> WorkCenter = Model.get('production.work.center')
    >>> WorkCenterCategory = Model.get('production.work.center.category')
    >>> category1 = WorkCenterCategory(name='Category 1')
    >>> category1.save()
    >>> category2 = WorkCenterCategory(name='Category 2')
    >>> category2.save()
    >>> center_root = WorkCenter(name='Root')
    >>> center_root.save()
    >>> center1 = WorkCenter(name='Center 1')
    >>> center1.parent = center_root
    >>> center1.category = category1
    >>> center1.cost_price = Decimal('10')
    >>> center1.cost_method = 'cycle'
    >>> center1.save()
    >>> center2 = WorkCenter(name='Center 2')
    >>> center2.parent = center_root
    >>> center2.category = category2
    >>> center2.cost_price = Decimal('5')
    >>> center2.cost_method = 'hour'
    >>> center2.save()

Create Bill of Material and Routing::

    >>> BOM = Model.get('production.bom')
    >>> BOMInput = Model.get('production.bom.input')
    >>> BOMOutput = Model.get('production.bom.output')
    >>> bom = BOM(name='product')
    >>> input1 = BOMInput()
    >>> bom.inputs.append(input1)
    >>> input1.product = component1
    >>> input1.quantity = 1
    >>> input2 = BOMInput()
    >>> bom.inputs.append(input2)
    >>> input2.product = component2
    >>> input2.quantity = 1
    >>> output = BOMOutput()
    >>> bom.outputs.append(output)
    >>> output.product = product
    >>> output.quantity = 1
    >>> bom.save()

    >>> Routing = Model.get('production.routing')
    >>> Operation = Model.get('production.routing.operation')
    >>> operation1 = Operation(name='Operation 1')
    >>> operation1.work_center_category = category1
    >>> operation1.save()
    >>> operation2 = Operation(name='Operation 2')
    >>> operation2.work_center_category = category2
    >>> operation2.save()
    >>> routing = Routing(name='product')
    >>> routing.boms.append(bom)
    >>> step1 = routing.steps.new(operation=operation1)
    >>> step2 = routing.steps.new(operation=operation2)
    >>> routing.save()

    >>> ProductBom = Model.get('product.product-production.bom')
    >>> product.boms.append(ProductBom(bom=bom, routing=routing))
    >>> product.save()

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
    >>> inventory_line1.quantity = 10
    >>> inventory_line2 = InventoryLine()
    >>> inventory.lines.append(inventory_line2)
    >>> inventory_line2.product = component2
    >>> inventory_line2.quantity = 10
    >>> inventory.click('confirm')
    >>> inventory.state
    'done'

Create production user::

    >>> production_user = User()
    >>> production_user.name = "Production"
    >>> production_user.login = 'production'
    >>> production_user.groups.extend(Group.find([
    ...             ('name', '=', 'Production'),
    ...             ]))
    >>> employee_party = Party(name="Employee")
    >>> employee_party.save()
    >>> employee = Employee(party=employee_party)
    >>> employee.save()
    >>> production_user.employees.append(employee)
    >>> production_user.employee = employee
    >>> production_user.save()

    >>> set_user(production_user)

Make a production::

    >>> Production = Model.get('production')
    >>> production = Production()
    >>> production.product = product
    >>> production.bom = bom
    >>> production.routing = routing
    >>> production.work_center = center_root
    >>> production.quantity = 1
    >>> production.click('wait')
    >>> production.state
    'waiting'
    >>> production.cost
    Decimal('2.0000')

Test works::

    >>> work1, work2 = production.works
    >>> assertEqual(work1.operation, operation1)
    >>> assertEqual(work1.work_center, center1)
    >>> work1.state
    'request'
    >>> assertEqual(work2.operation, operation2)
    >>> assertEqual(work2.work_center, center2)
    >>> work2.state
    'request'

Run the production::

    >>> production.click('assign_try')
    >>> production.click('run')
    >>> production.state
    'running'

Test works::

    >>> work1, work2 = production.works
    >>> work1.state
    'draft'
    >>> work2.state
    'draft'

Run works::

    >>> cycle1 = work1.cycles.new()
    >>> cycle1.click('run')
    >>> cycle1.state
    'running'
    >>> assertEqual(cycle1.run_by, employee)
    >>> work1.reload()
    >>> work1.state
    'running'
    >>> cycle1.click('do')
    >>> cycle1.state
    'done'
    >>> assertEqual(cycle1.done_by, employee)
    >>> work1.reload()
    >>> work1.state
    'finished'
    >>> cycle2 = work2.cycles.new()
    >>> cycle2.click('cancel')
    >>> assertEqual(cycle2.cancelled_by, employee)
    >>> cycle2.state
    'cancelled'
    >>> work2.reload()
    >>> work2.state
    'draft'
    >>> work2.click('start')
    >>> cycle2, = [c for c in work2.active_cycles]
    >>> cycle2.duration = dt.timedelta(hours=1)
    >>> cycle2.save()
    >>> work2.click('stop')
    >>> work2.state
    'finished'
    >>> cycle2.reload()
    >>> cycle2.state
    'done'

Add an extra work::

    >>> work2b = production.works.new()
    >>> work2b.operation = operation2
    >>> work2b.work_center = center2
    >>> production.save()
    >>> work2b = production.works[-1]

    >>> work2b.state
    'draft'

And delete the extra work::

    >>> work2b.delete()

Check production cost::

    >>> production.reload()
    >>> production.cost
    Decimal('17.0000')
    >>> work1.cost
    Decimal('10.0000')
    >>> work2.cost
    Decimal('5.0000')

Do the production::

    >>> production.click('do')
    >>> production.state
    'done'

Work is now done::

    >>> work2.reload()
    >>> work2.state
    'done'
