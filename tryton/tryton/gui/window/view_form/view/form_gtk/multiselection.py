# This file is part of Tryton.  The COPYRIGHT file at the top level of this
# repository contains the full copyright notices and license terms.
from gi.repository import GLib, GObject, Gtk

from tryton.common.selection import SelectionMixin

from .widget import Widget


class MultiSelection(Widget, SelectionMixin):
    expand = True

    def __init__(self, view, attrs):
        super(MultiSelection, self).__init__(view, attrs)

        if int(attrs.get('yexpand', self.expand)):
            self.widget = Gtk.ScrolledWindow()
            self.widget.set_policy(
                Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            self.widget.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        else:
            self.widget = Gtk.VBox()
        self.widget.set_size_request(100, 100)
        self.widget.get_accessible().set_name(attrs.get('string', ''))

        self.model = Gtk.ListStore(GObject.TYPE_PYOBJECT, GObject.TYPE_STRING)
        self.tree = self.mnemonic_widget = Gtk.TreeView()
        self.tree.set_model(self.model)
        self.tree.set_search_column(1)
        self.tree.connect('focus-out-event', lambda *a: self._focus_out())
        self.tree.set_headers_visible(False)
        selection = self.tree.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        selection.connect('changed', self.changed)
        self.widget.add(self.tree)
        column = Gtk.TreeViewColumn()
        select_cell = Gtk.CellRendererToggle()
        select_cell.set_sensitive(False)
        column.pack_start(select_cell, expand=False)
        column.set_cell_data_func(
            select_cell, self._select_data_func, selection)
        name_cell = Gtk.CellRendererText()
        column.pack_start(name_cell, expand=True)
        column.add_attribute(name_cell, 'text', 1)
        self.tree.append_column(column)

        self.nullable_widget = False
        self.init_selection()

    def _select_data_func(self, column, cell, model, iter_, selection):
        cell.set_property('active', selection.iter_is_selected(iter_))

    def _readonly_set(self, readonly):
        super(MultiSelection, self)._readonly_set(readonly)
        selection = self.tree.get_selection()
        selection.set_select_function(lambda *a: not readonly)

    @property
    def modified(self):
        if self.record and self.field:
            group = set(self.field.get_eval(self.record))
            value = set(self.get_value())
            return value != group
        return False

    def changed(self, selection):
        def focus_out():
            if self.widget.props.window:
                self._focus_out()
        # Must be deferred because it triggers a display of the form
        GLib.idle_add(focus_out)

    def get_value(self):
        model, paths = self.tree.get_selection().get_selected_rows()
        return [model[path][0] for path in paths]

    def set_value(self):
        self.field.set_client(self.record, self.get_value())

    def display(self):
        def freeze(iter):
            return list(map(tuple, iter))
        selection = self.tree.get_selection()
        selection.handler_block_by_func(self.changed)
        try:
            # Remove select_function to allow update,
            # it will be set back in the super call
            selection.set_select_function(lambda *a: True)
            self.update_selection(self.record, self.field)
            new_model = freeze(self.selection) != freeze(self.model)
            if new_model:
                self.model.clear()
            if not self.field:
                return
            value2path = {}
            for idx, (value, name) in enumerate(self.selection):
                if new_model:
                    self.model.append((value, name))
                value2path[value] = idx
            selection.unselect_all()
            values = self.field.get_eval(self.record)
            for value in values:
                selection.select_path(value2path[value])
            super(MultiSelection, self).display()
        finally:
            selection.handler_unblock_by_func(self.changed)
