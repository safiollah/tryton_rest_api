# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from collections import defaultdict

from sql import Null
from sql.functions import CharLength

from trytond.i18n import gettext
from trytond.model import (
    Check, Index, Model, ModelSQL, ModelView, Workflow, fields)
from trytond.model.exceptions import AccessError
from trytond.pool import Pool
from trytond.pyson import Bool, Eval, If
from trytond.tools import grouped_slice, is_full_text, lstrip_wildcard
from trytond.transaction import Transaction
from trytond.wizard import Button, StateTransition, StateView, Wizard

from .exceptions import (
    InventoryCountWarning, InventoryFutureWarning, InventoryValidationError)


class Inventory(Workflow, ModelSQL, ModelView):
    __name__ = 'stock.inventory'
    _rec_name = 'number'

    _states = {
        'readonly': Eval('state') != 'draft',
        }

    number = fields.Char('Number', readonly=True,
        help="The main identifier for the inventory.")
    location = fields.Many2One(
        'stock.location', 'Location', required=True,
        domain=[('type', '=', 'storage')], states={
            'readonly': (Eval('state') != 'draft') | Eval('lines', [0]),
            },
        help="The location inventoried.")
    date = fields.Date('Date', required=True, states={
            'readonly': (Eval('state') != 'draft') | Eval('lines', [0]),
            },
        help="The date of the stock count.")
    lines = fields.One2Many(
        'stock.inventory.line', 'inventory', 'Lines',
        states={
            'readonly': (_states['readonly'] | ~Eval('location')
                | ~Eval('date')),
            })
    empty_quantity = fields.Selection([
            (None, ""),
            ('keep', "Keep"),
            ('empty', "Empty"),
            ], "Empty Quantity", states=_states,
        help="How lines without a quantity are handled.")
    company = fields.Many2One('company.company', 'Company', required=True,
        states={
            'readonly': (Eval('state') != 'draft') | Eval('lines', [0]),
            },
        help="The company the inventory is associated with.")
    state = fields.Selection([
            ('draft', "Draft"),
            ('done', "Done"),
            ('cancelled', "Cancelled"),
            ], "State", readonly=True, sort=False,
        help="The current state of the inventory.")

    del _states

    @classmethod
    def __setup__(cls):
        cls.number.search_unaccented = False
        super(Inventory, cls).__setup__()
        t = cls.__table__()
        cls._sql_indexes.add(
            Index(
                t,
                (t.state, Index.Equality(cardinality='low')),
                where=t.state == 'draft'))
        cls._order.insert(0, ('date', 'DESC'))
        cls._transitions |= set((
                ('draft', 'done'),
                ('draft', 'cancelled'),
                ))
        cls._buttons.update({
                'confirm': {
                    'invisible': Eval('state').in_(['done', 'cancelled']),
                    'depends': ['state'],
                    },
                'cancel': {
                    'invisible': Eval('state').in_(['cancelled', 'done']),
                    'depends': ['state'],
                    },
                'complete_lines': {
                    'readonly': Eval('state') != 'draft',
                    'depends': ['state'],
                    },
                'do_count': {
                    'readonly': Eval('state') != 'draft',
                    'depends': ['state'],
                    },
                })

    @classmethod
    def __register__(cls, module_name):
        super(Inventory, cls).__register__(module_name)

        cursor = Transaction().connection.cursor()
        table = cls.__table_handler__(module_name)
        sql_table = cls.__table__()

        # Migration from 5.4: remove lost_found
        table.not_null_action('lost_found', 'remove')

        # Migration from 5.6: rename state cancel to cancelled
        cursor.execute(*sql_table.update(
                [sql_table.state], ['cancelled'],
                where=sql_table.state == 'cancel'))

    @classmethod
    def order_number(cls, tables):
        table, _ = tables[None]
        return [
            ~((table.state == 'cancelled') & (table.number == Null)),
            CharLength(table.number), table.number]

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    def get_rec_name(self, name):
        pool = Pool()
        Lang = pool.get('ir.lang')
        lang = Lang.get()
        date = lang.strftime(self.date)
        return f"[{self.number}] {self.location.rec_name} @ {date}"

    @classmethod
    def search_rec_name(cls, name, clause):
        _, operator, operand, *extra = clause
        if operator.startswith('!') or operator.startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        number_value = operand
        if operator.endswith('like') and is_full_text(operand):
            number_value = lstrip_wildcard(operand)
        return [bool_op,
            ('number', operator, number_value, *extra),
            ('location.rec_name', operator, operand, *extra),
            ]

    @classmethod
    def view_attributes(cls):
        return super().view_attributes() + [
            ('/tree', 'visual', If(Eval('state') == 'cancelled', 'muted', '')),
            ]

    @classmethod
    def delete(cls, inventories):
        # Cancel before delete
        cls.cancel(inventories)
        for inventory in inventories:
            if inventory.state != 'cancelled':
                raise AccessError(
                    gettext('stock.msg_inventory_delete_cancel',
                        inventory=inventory.rec_name))
        super(Inventory, cls).delete(inventories)

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def confirm(cls, inventories):
        pool = Pool()
        Move = pool.get('stock.move')
        Date = pool.get('ir.date')
        Warning = pool.get('res.user.warning')
        transaction = Transaction()
        today_cache = {}

        def in_future(inventory):
            if inventory.company not in today_cache:
                with Transaction().set_context(company=inventory.company.id):
                    today_cache[inventory.company] = Date.today()
            today = today_cache[inventory.company]
            if inventory.date > today:
                return inventory
        future_inventories = sorted(filter(in_future, inventories))
        if future_inventories:
            names = ', '.join(i.rec_name for i in future_inventories[:5])
            if len(future_inventories) > 5:
                names + '...'
            warning_name = Warning.format('date_future', future_inventories)
            if Warning.check(warning_name):
                raise InventoryFutureWarning(warning_name,
                    gettext('stock.msg_inventory_date_in_the_future',
                        inventories=names))

        moves = []
        for inventory in inventories:
            keys = set()
            for line in inventory.lines:
                key = line.unique_key
                if key in keys:
                    raise InventoryValidationError(
                        gettext('stock.msg_inventory_line_unique',
                            line=line.rec_name,
                            inventory=inventory.rec_name))
                keys.add(key)
                move = line.get_move()
                if move:
                    moves.append(move)
        if moves:
            with transaction.set_context(_product_replacement=False):
                Move.save(moves)
            with transaction.set_context(_skip_warnings=True):
                Move.do(moves)

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelled')
    def cancel(cls, inventories):
        Line = Pool().get("stock.inventory.line")
        Line.cancel_move([l for i in inventories for l in i.lines])

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Configuration = pool.get('stock.configuration')
        config = Configuration(1)
        vlist = [x.copy() for x in vlist]
        default_company = cls.default_company()
        for values in vlist:
            if values.get('number') is None:
                values['number'] = config.get_multivalue(
                    'inventory_sequence',
                    company=values.get('company', default_company)).get()
        inventories = super(Inventory, cls).create(vlist)
        cls.complete_lines(inventories, fill=False)
        return inventories

    @classmethod
    def write(cls, *args):
        super().write(*args)
        inventories = cls.browse(set(sum(args[::2], [])))
        cls.complete_lines(inventories, fill=False)

    @classmethod
    def copy(cls, inventories, default=None):
        pool = Pool()
        Date = pool.get('ir.date')

        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('date', Date.today())
        default.setdefault('lines.moves', None)
        default.setdefault('number', None)

        new_inventories = super().copy(inventories, default=default)
        cls.complete_lines(new_inventories, fill=False)
        return new_inventories

    @staticmethod
    def grouping():
        return ('product',)

    @classmethod
    @ModelView.button
    def complete_lines(cls, inventories, fill=True):
        '''
        Complete or update the inventories
        '''
        pool = Pool()
        Line = pool.get('stock.inventory.line')
        Product = pool.get('product.product')

        grouping = cls.grouping()
        to_create, to_write = [], []
        for inventory in inventories:
            # Once done computation is wrong because include created moves
            if inventory.state == 'done':
                continue
            # Compute product quantities
            with Transaction().set_context(
                    company=inventory.company.id,
                    stock_date_end=inventory.date):
                if fill:
                    pbl = Product.products_by_location(
                        [inventory.location.id],
                        grouping=grouping)
                else:
                    product_ids = [l.product.id for l in inventory.lines]
                    pbl = defaultdict(int)
                    for product_ids in grouped_slice(product_ids):
                        pbl.update(Product.products_by_location(
                                [inventory.location.id],
                                grouping=grouping,
                                grouping_filter=(list(product_ids),)))

            # Index some data
            product2type = {}
            product2consumable = {}
            for product in Product.browse({line[1] for line in pbl}):
                product2type[product.id] = product.type
                product2consumable[product.id] = product.consumable

            # Update existing lines
            for line in inventory.lines:
                if line.product.type != 'goods':
                    Line.delete([line])
                    continue

                key = (inventory.location.id,) + line.unique_key
                if key in pbl:
                    quantity = pbl.pop(key)
                else:
                    quantity = 0.0
                values = line.update_values4complete(quantity)
                if values:
                    to_write.extend(([line], values))

            if not fill:
                continue
            # Create lines if needed
            for key, quantity in pbl.items():
                product_id = key[grouping.index('product') + 1]
                if (product2type[product_id] != 'goods'
                        or product2consumable[product_id]):
                    continue
                if not quantity:
                    continue

                values = Line.create_values4complete(inventory, quantity)
                for i, fname in enumerate(grouping, 1):
                    values[fname] = key[i]
                to_create.append(values)
        if to_create:
            Line.create(to_create)
        if to_write:
            Line.write(*to_write)

    @classmethod
    @ModelView.button_action('stock.wizard_inventory_count')
    def do_count(cls, inventories):
        cls.complete_lines(inventories)


class InventoryLine(ModelSQL, ModelView):
    __name__ = 'stock.inventory.line'
    _states = {
        'readonly': Eval('inventory_state') != 'draft',
        }

    product = fields.Many2One('product.product', 'Product', required=True,
        domain=[
            ('type', '=', 'goods'),
            ], states=_states)
    unit = fields.Function(fields.Many2One(
            'product.uom', "Unit",
            help="The unit in which the quantity is specified."),
        'get_unit')
    expected_quantity = fields.Float(
        "Expected Quantity", digits='unit', required=True, readonly=True,
        states={
            'invisible': Eval('id', -1) < 0,
        },
        help="The quantity the system calculated should be in the location.")
    quantity = fields.Float(
        "Actual Quantity", digits='unit', states=_states,
        domain=[
            If(Eval('quantity', None),
                ('quantity', '>=', 0),
                ()),
            ],
        help="The actual quantity found in the location.")
    moves = fields.One2Many('stock.move', 'origin', 'Moves', readonly=True)
    inventory = fields.Many2One('stock.inventory', 'Inventory', required=True,
        ondelete='CASCADE',
        states={
            'readonly': _states['readonly'] & Bool(Eval('inventory')),
            },
        help="The inventory the line belongs to.")
    inventory_location = fields.Function(
        fields.Many2One('stock.location', "Location"),
        'on_change_with_inventory_location',
        searcher='search_inventory_location')
    inventory_date = fields.Function(
        fields.Date("Date"),
        'on_change_with_inventory_date',
        searcher='search_inventory_date')
    inventory_state = fields.Function(
        fields.Selection('get_inventory_states', "Inventory State",
        depends={'inventory'}),
        'on_change_with_inventory_state')

    @classmethod
    def __setup__(cls):
        super(InventoryLine, cls).__setup__()
        cls.__access__.add('inventory')
        t = cls.__table__()
        cls._sql_constraints += [
            ('check_line_qty_pos', Check(t, t.quantity >= 0),
                'stock.msg_inventory_line_quantity_positive'),
            ]
        cls._order.insert(0, ('product', 'ASC'))

    @staticmethod
    def default_expected_quantity():
        return 0.

    @fields.depends('product')
    def on_change_product(self):
        if self.product:
            self.unit = self.product.default_uom

    @fields.depends('inventory', '_parent_inventory.location')
    def on_change_with_inventory_location(self, name=None):
        return self.inventory.location if self.inventory else None

    @classmethod
    def search_inventory_location(cls, name, clause):
        nested = clause[0][len(name):]
        return [('inventory.location' + nested, *clause[1:])]

    @fields.depends('inventory', '_parent_inventory.date')
    def on_change_with_inventory_date(self, name=None):
        if self.inventory:
            return self.inventory.date

    @classmethod
    def search_inventory_date(cls, name, clause):
        return [('inventory.date',) + tuple(clause[1:])]

    @classmethod
    def get_inventory_states(cls):
        pool = Pool()
        Inventory = pool.get('stock.inventory')
        return Inventory.fields_get(['state'])['state']['selection']

    @fields.depends('inventory', '_parent_inventory.state')
    def on_change_with_inventory_state(self, name=None):
        if self.inventory:
            return self.inventory.state
        return 'draft'

    def get_rec_name(self, name):
        return self.product.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('product.rec_name',) + tuple(clause[1:])]

    def get_unit(self, name):
        return self.product.default_uom

    @property
    def unique_key(self):
        key = []
        for fname in self.inventory.grouping():
            value = getattr(self, fname)
            if isinstance(value, Model):
                value = value.id
            key.append(value)
        return tuple(key)

    @classmethod
    def cancel_move(cls, lines):
        Move = Pool().get('stock.move')
        moves = [m for l in lines for m in l.moves if l.moves]
        Move.cancel(moves)
        Move.delete(moves)

    def get_move(self):
        '''
        Return Move instance for the inventory line
        '''
        pool = Pool()
        Move = pool.get('stock.move')

        qty = self.quantity
        if qty is None:
            if self.inventory.empty_quantity is None:
                raise InventoryValidationError(
                    gettext('stock.msg_inventory_missing_empty_quantity',
                        inventory=self.inventory.rec_name))
            if self.inventory.empty_quantity == 'keep':
                return
            else:
                qty = 0.0

        delta_qty = self.unit.round(self.expected_quantity - qty)
        if delta_qty == 0.0:
            return
        from_location = self.inventory.location
        to_location = self.inventory.location.lost_found_used
        if not to_location:
            raise InventoryValidationError(
                gettext('stock.msg_inventory_location_missing_lost_found',
                    inventory=self.inventory.rec_name,
                    location=self.inventory.location.rec_name))
        if delta_qty < 0:
            (from_location, to_location, delta_qty) = \
                (to_location, from_location, -delta_qty)

        return Move(
            from_location=from_location,
            to_location=to_location,
            quantity=delta_qty,
            product=self.product,
            unit=self.unit,
            company=self.inventory.company,
            effective_date=self.inventory.date,
            origin=self,
            )

    def update_values4complete(self, quantity):
        '''
        Return update values to complete inventory
        '''
        values = {}
        # if nothing changed, no update
        if self.expected_quantity == quantity:
            return values
        values['expected_quantity'] = quantity
        return values

    @classmethod
    def create_values4complete(cls, inventory, quantity):
        '''
        Return create values to complete inventory
        '''
        return {
            'inventory': inventory.id,
            'expected_quantity': quantity,
        }

    @classmethod
    def delete(cls, lines):
        for line in lines:
            if line.inventory_state not in {'cancelled', 'draft'}:
                raise AccessError(
                    gettext('stock.msg_inventory_line_delete_cancel',
                        line=line.rec_name,
                        inventory=line.inventory.rec_name))
        super(InventoryLine, cls).delete(lines)


class Count(Wizard):
    __name__ = 'stock.inventory.count'
    start_state = 'search'

    search = StateView(
        'stock.inventory.count.search',
        'stock.inventory_count_search_view_form', [
            Button("End", 'end', 'tryton-cancel'),
            Button("Select", 'quantity', 'tryton-forward', default=True),
            ])
    quantity = StateView(
        'stock.inventory.count.quantity',
        'stock.inventory_count_quantity_view_form', [
            Button("Cancel", 'search', 'tryton-cancel'),
            Button("Add", 'add', 'tryton-ok', default=True),
            ])
    add = StateTransition()

    def default_quantity(self, fields):
        pool = Pool()
        InventoryLine = pool.get('stock.inventory.line')
        Warning = pool.get('res.user.warning')
        values = {}
        lines = InventoryLine.search(
            self.get_line_domain(self.record), limit=1)
        if not lines:
            warning_name = '%s.%s.count_create' % (
                self.record, self.search.search)
            if Warning.check(warning_name):
                raise InventoryCountWarning(warning_name,
                    gettext('stock.msg_inventory_count_create_line',
                        search=self.search.search.rec_name))
            line, = InventoryLine.create([self.get_line_values(self.record)])
        else:
            line, = lines
        values['line'] = line.id
        values['product'] = line.product.id
        values['unit'] = line.unit.id
        if line.unit.rounding == 1:
            values['quantity'] = 1.
        return values

    def get_line_domain(self, inventory):
        pool = Pool()
        Product = pool.get('product.product')
        domain = [
            ('inventory', '=', inventory.id),
            ]
        if isinstance(self.search.search, Product):
            domain.append(('product', '=', self.search.search.id))
        return domain

    def get_line_values(self, inventory):
        pool = Pool()
        Product = pool.get('product.product')
        InventoryLine = pool.get('stock.inventory.line')
        values = InventoryLine.create_values4complete(inventory, 0)
        if isinstance(self.search.search, Product):
            values['product'] = self.search.search.id
        return values

    def transition_add(self):
        if self.quantity.line and self.quantity.quantity:
            line = self.quantity.line
            if line.quantity:
                line.quantity += self.quantity.quantity
            else:
                line.quantity = self.quantity.quantity
            line.save()
        return 'search'


class CountSearch(ModelView):
    __name__ = 'stock.inventory.count.search'

    search = fields.Reference(
        "Search", [
            ('product.product', "Product"),
            ],
        required=True,
        domain={
            'product.product': [
                ('type', '=', 'goods'),
                ('consumable', '=', False),
                ],
            },
        help="The item that's counted.")

    @classmethod
    def default_search(cls):
        return 'product.product,-1'


class CountQuantity(ModelView):
    __name__ = 'stock.inventory.count.quantity'

    line = fields.Many2One(
        'stock.inventory.line', "Line", readonly=True, required=True)
    product = fields.Many2One('product.product', "Product", readonly=True)
    unit = fields.Many2One(
        'product.uom', "Unit", readonly=True,
        help="The unit in which the quantities are specified.")
    total_quantity = fields.Float(
        "Total Quantity", digits='unit', readonly=True,
        help="The total amount of the line counted so far.")

    quantity = fields.Float(
        "Quantity", digits='unit', required=True,
        help="The quantity to add to the existing count.")

    @fields.depends('quantity', 'line')
    def on_change_quantity(self):
        if self.line:
            self.total_quantity = (
                (self.line.quantity or 0) + (self.quantity or 0))
