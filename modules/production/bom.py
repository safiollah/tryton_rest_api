# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from sql.functions import CharLength

from trytond.model import DeactivableMixin, ModelSQL, ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond.tools import is_full_text, lstrip_wildcard
from trytond.wizard import Button, StateView, Wizard


class BOM(DeactivableMixin, ModelSQL, ModelView):
    __name__ = 'production.bom'

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char(
        "Code",
        states={
            'readonly': Eval('code_readonly', False),
            })
    code_readonly = fields.Function(
        fields.Boolean("Code Readonly"), 'get_code_readonly')
    inputs = fields.One2Many('production.bom.input', 'bom', "Input Materials")
    outputs = fields.One2Many(
        'production.bom.output', 'bom', "Output Materials")
    output_products = fields.Many2Many('production.bom.output',
        'bom', 'product', 'Output Products')

    @classmethod
    def order_code(cls, tables):
        table, _ = tables[None]
        if cls.default_code_readonly():
            return [CharLength(table.code), table.code]
        else:
            return [table.code]

    @classmethod
    def default_code_readonly(cls):
        pool = Pool()
        Configuration = pool.get('production.configuration')
        config = Configuration(1)
        return bool(config.bom_sequence)

    def get_code_readonly(self, name):
        return self.default_code_readonly()

    @classmethod
    def order_rec_name(cls, tables):
        table, _ = tables[None]
        return cls.order_code(tables) + [table.name]

    def get_rec_name(self, name):
        if self.code:
            return '[' + self.code + '] ' + self.name
        else:
            return self.name

    @classmethod
    def search_rec_name(cls, name, clause):
        _, operator, operand, *extra = clause
        if operator.startswith('!') or operator.startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        code_value = operand
        if operator.endswith('like') and is_full_text(operand):
            code_value = lstrip_wildcard(operand)
        return [bool_op,
            ('name', operator, operand, *extra),
            ('code', operator, code_value, *extra),
            ]

    def compute_factor(self, product, quantity, unit):
        '''
        Compute factor for an output product
        '''
        Uom = Pool().get('product.uom')
        output_quantity = 0
        for output in self.outputs:
            if output.product == product:
                output_quantity += Uom.compute_qty(
                    output.unit, output.quantity, unit, round=False)
        if output_quantity:
            return quantity / output_quantity
        else:
            return 0

    @classmethod
    def _code_sequence(cls):
        pool = Pool()
        Configuration = pool.get('production.configuration')
        config = Configuration(1)
        return config.bom_sequence

    @classmethod
    def create(cls, vlist):
        vlist = [v.copy() for v in vlist]
        missing_code = [v for v in vlist if not v.get('code')]
        if missing_code:
            if sequence := cls._code_sequence():
                for values, code in zip(
                        missing_code, sequence.get_many(len(missing_code))):
                    values['code'] = code
        return super().create(vlist)

    @classmethod
    def copy(cls, records, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('code', None)
        default.setdefault('output_products', None)
        return super(BOM, cls).copy(records, default=default)


class BOMInput(ModelSQL, ModelView):
    __name__ = 'production.bom.input'

    bom = fields.Many2One(
        'production.bom', "BOM", required=True, ondelete='CASCADE')
    product = fields.Many2One('product.product', 'Product', required=True)
    uom_category = fields.Function(fields.Many2One(
        'product.uom.category', 'Uom Category'), 'on_change_with_uom_category')
    unit = fields.Many2One(
        'product.uom', "Unit", required=True,
        domain=[
            ('category', '=', Eval('uom_category', -1)),
            ])
    quantity = fields.Float(
        "Quantity", digits='unit', required=True,
        domain=['OR',
            ('quantity', '>=', 0),
            ('quantity', '=', None),
            ])

    @classmethod
    def __setup__(cls):
        super(BOMInput, cls).__setup__()
        cls.product.domain = [('type', 'in', cls.get_product_types())]
        cls.__access__.add('bom')

    @classmethod
    def __register__(cls, module):
        table_h = cls.__table_handler__(module)

        # Migration from 6.8: rename uom to unit
        if (table_h.column_exist('uom')
                and not table_h.column_exist('unit')):
            table_h.column_rename('uom', 'unit')

        super().__register__(module)
        table_h = cls.__table_handler__(module)

        # Migration from 6.0: remove unique constraint
        table_h.drop_constraint('product_bom_uniq')

    @classmethod
    def get_product_types(cls):
        return ['goods', 'assets']

    @fields.depends('product', 'unit')
    def on_change_product(self):
        if self.product:
            category = self.product.default_uom.category
            if not self.unit or self.unit.category != category:
                self.unit = self.product.default_uom
        else:
            self.unit = None

    @fields.depends('product')
    def on_change_with_uom_category(self, name=None):
        return self.product.default_uom.category if self.product else None

    def get_rec_name(self, name):
        return self.product.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('product.rec_name',) + tuple(clause[1:])]

    @classmethod
    def validate(cls, boms):
        super(BOMInput, cls).validate(boms)
        for bom in boms:
            bom.check_bom_recursion()

    def check_bom_recursion(self):
        '''
        Check BOM recursion
        '''
        self.product.check_bom_recursion()

    def compute_quantity(self, factor):
        return self.unit.ceil(self.quantity * factor)


class BOMOutput(BOMInput):
    __name__ = 'production.bom.output'
    __string__ = None
    _table = None  # Needed to override BOMInput._table

    def compute_quantity(self, factor):
        return self.unit.floor(self.quantity * factor)

    @classmethod
    def delete(cls, outputs):
        pool = Pool()
        ProductBOM = pool.get('product.product-production.bom')
        bom_products = [b for o in outputs for b in o.product.boms]
        super(BOMOutput, cls).delete(outputs)
        # Validate that output_products domain on bom is still valid
        ProductBOM._validate(bom_products, ['bom'])

    @classmethod
    def write(cls, *args):
        pool = Pool()
        ProductBOM = pool.get('product.product-production.bom')
        actions = iter(args)
        bom_products = []
        for outputs, values in zip(actions, actions):
            if 'product' in values:
                bom_products.extend(
                    [b for o in outputs for b in o.product.boms])
        super().write(*args)
        # Validate that output_products domain on bom is still valid
        ProductBOM._validate(bom_products, ['bom'])


class BOMTree(ModelView):
    __name__ = 'production.bom.tree'

    product = fields.Many2One('product.product', 'Product')
    quantity = fields.Float('Quantity', digits='unit')
    unit = fields.Many2One('product.uom', "Unit")
    childs = fields.One2Many('production.bom.tree', None, 'Childs')

    @classmethod
    def tree(cls, product, quantity, unit, bom=None):
        Input = Pool().get('production.bom.input')

        result = []
        if bom is None:
            pbom = product.get_bom()
            if pbom is None:
                return result
            bom = pbom.bom

        factor = bom.compute_factor(product, quantity, unit)
        for input_ in bom.inputs:
            quantity = Input.compute_quantity(input_, factor)
            childs = cls.tree(input_.product, quantity, input_.unit)
            values = {
                'product': input_.product.id,
                'product.': {
                    'rec_name': input_.product.rec_name,
                    },
                'quantity': quantity,
                'unit': input_.unit.id,
                'unit.': {
                    'rec_name': input_.unit.rec_name,
                    },
                'childs': childs,
            }
            result.append(values)
        return result


class OpenBOMTreeStart(ModelView):
    __name__ = 'production.bom.tree.open.start'

    quantity = fields.Float('Quantity', digits='unit', required=True)
    unit = fields.Many2One(
        'product.uom', "Unit", required=True,
        domain=[
            ('category', '=', Eval('category', -1)),
            ])
    category = fields.Many2One('product.uom.category', 'Category',
        readonly=True)
    bom = fields.Many2One('product.product-production.bom',
        'BOM', required=True, domain=[
            ('product', '=', Eval('product', -1)),
            ])
    product = fields.Many2One('product.product', 'Product', readonly=True)


class OpenBOMTreeTree(ModelView):
    __name__ = 'production.bom.tree.open.tree'

    bom_tree = fields.One2Many('production.bom.tree', None, 'BOM Tree',
        readonly=True)

    @classmethod
    def tree(cls, bom, product, quantity, unit):
        pool = Pool()
        Tree = pool.get('production.bom.tree')

        childs = Tree.tree(product, quantity, unit, bom=bom)
        bom_tree = [{
                'product': product.id,
                'product.': {
                    'rec_name': product.rec_name,
                    },
                'quantity': quantity,
                'unit': unit.id,
                'unit.': {
                    'rec_name': unit.rec_name,
                    },
                'childs': childs,
                }]
        return {
            'bom_tree': bom_tree,
            }


class OpenBOMTree(Wizard):
    __name__ = 'production.bom.tree.open'

    start = StateView('production.bom.tree.open.start',
        'production.bom_tree_open_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('OK', 'tree', 'tryton-ok', True),
            ])
    tree = StateView('production.bom.tree.open.tree',
        'production.bom_tree_open_tree_view_form', [
            Button('Change', 'start', 'tryton-back'),
            Button('Close', 'end', 'tryton-close'),
            ])

    def default_start(self, fields):
        defaults = {}
        product = self.record
        defaults['category'] = product.default_uom.category.id
        if getattr(self.start, 'unit', None):
            defaults['unit'] = self.start.unit.id
        else:
            defaults['unit'] = product.default_uom.id
        defaults['product'] = product.id
        if getattr(self.start, 'bom', None):
            defaults['bom'] = self.start.bom.id
        else:
            bom = product.get_bom()
            if bom:
                defaults['bom'] = bom.id
        defaults['quantity'] = getattr(self.start, 'quantity', None)
        return defaults

    def default_tree(self, fields):
        pool = Pool()
        BomTree = pool.get('production.bom.tree.open.tree')
        return BomTree.tree(self.start.bom.bom, self.start.product,
            self.start.quantity, self.start.unit)
