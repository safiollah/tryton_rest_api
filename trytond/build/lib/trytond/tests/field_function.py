# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.model import ModelSQL, ModelStorage, fields
from trytond.pool import Pool
from trytond.transaction import Transaction


class FunctionDefinition(ModelStorage):
    __name__ = 'test.function.definition'
    function = fields.Function(
        fields.Integer("Integer"),
        'on_change_with_function', searcher='search_function')

    def on_change_with_function(self, name=None):
        return self.id

    @classmethod
    def search_function(cls, name, clause):
        return [('id',) + tuple(clause[1:])]


class FunctionAccessor(ModelSQL):
    __name__ = 'test.function.accessor'

    target = fields.Many2One('test.function.accessor.target', "Target")
    function = fields.Function(
        fields.Many2One('test.function.accessor.target', "Function"),
        'on_change_with_function')

    @fields.depends('target')
    def on_change_with_function(self, name=None):
        if self.target:
            return self.target.id


class FunctionAccessorTarget(ModelSQL):
    __name__ = 'test.function.accessor.target'


class FunctonGetter(ModelSQL):
    __name__ = 'test.function.getter'

    function_class = fields.Function(
        fields.Char("Function"), 'get_function_class')
    function_class_names = fields.Function(
        fields.Char("Function"), 'get_function_class_names')
    function_instance = fields.Function(
        fields.Char("Function"), 'get_function_instance')
    function_instance_names = fields.Function(
        fields.Char("Function"), 'get_function_instance_names')

    @classmethod
    def get_function_class(cls, records, name):
        assert name == 'function_class', name
        return {r.id: "class" for r in records}

    @classmethod
    def get_function_class_names(cls, records, names):
        assert names == ['function_class_names'], names
        return {n: {r.id: "class names" for r in records} for n in names}

    def get_function_instance(self, name):
        assert name == 'function_instance', name
        return "instance"

    def get_function_instance_names(self, names):
        assert names == ['function_instance_names'], names
        return {n: "instance names" for n in names}


class FunctionGetterContext(ModelSQL):
    __name__ = 'test.function.getter_context'

    function_with_context = fields.Function(
        fields.Char("Function"),
        'getter', getter_with_context=True)
    function_without_context = fields.Function(
        fields.Char("Function"),
        'getter', getter_with_context=False)

    def getter(self, name):
        context = Transaction().context
        return '%s - %s' % (
            context.get('language', 'empty'), context.get('test', 'empty'))


class FunctionGetterLocalCache(ModelSQL):
    __name__ = 'test.function.getter_local_cache'

    function1 = fields.Function(
        fields.Char("Char 1"), 'get_function1')
    function2 = fields.Function(
        fields.Char("Char 2"), 'get_function2')

    def get_function1(self, name):
        return "test"

    def get_function2(self, name):
        return self.function1.upper()

    @classmethod
    def index_get_field(cls, name):
        index = super().index_get_field(name)
        if name == 'function2':
            index = cls.index_get_field('function1') + 1
        return index


def register(module):
    Pool.register(
        FunctionDefinition,
        FunctionAccessor,
        FunctionAccessorTarget,
        FunctonGetter,
        FunctionGetterContext,
        FunctionGetterLocalCache,
        module=module, type_='model')
