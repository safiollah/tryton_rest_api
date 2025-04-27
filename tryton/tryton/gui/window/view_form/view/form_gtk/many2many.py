# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import gettext

from gi.repository import Gdk, Gtk

import tryton.common as common
from tryton.common.completion import get_completion, update_completion
from tryton.common.domain_parser import quote
from tryton.common.underline import set_underline
from tryton.gui.window.view_form.screen import Screen
from tryton.gui.window.win_form import WinForm
from tryton.gui.window.win_search import WinSearch

from .widget import Widget

_ = gettext.gettext


class Many2Many(Widget):
    expand = True

    def __init__(self, view, attrs):
        super(Many2Many, self).__init__(view, attrs)

        self.widget = Gtk.Frame()
        self.widget.set_shadow_type(Gtk.ShadowType.NONE)
        self.widget.get_accessible().set_name(attrs.get('string', ''))
        vbox = Gtk.VBox(homogeneous=False, spacing=5)
        self.widget.add(vbox)
        self._readonly = True
        self._required = False
        self._position = 0

        hbox = Gtk.HBox(homogeneous=False, spacing=0)
        hbox.set_border_width(2)

        self.title = Gtk.Label(
            label=set_underline(attrs.get('string', '')),
            use_underline=True, halign=Gtk.Align.START)
        hbox.pack_start(self.title, expand=True, fill=True, padding=0)

        hbox.pack_start(Gtk.VSeparator(), expand=False, fill=True, padding=0)

        tooltips = common.Tooltips()

        self.wid_text = Gtk.Entry()
        self.wid_text.set_placeholder_text(_('Search'))
        self.wid_text.set_property('width_chars', 13)
        self.wid_text.connect('focus-out-event', self._focus_out)
        hbox.pack_start(self.wid_text, expand=True, fill=True, padding=0)

        if int(self.attrs.get('completion', 1)):
            self.wid_completion = get_completion(
                search=self.read_access,
                create=self.create_access)
            self.wid_completion.connect('match-selected',
                self._completion_match_selected)
            self.wid_completion.connect('action-activated',
                self._completion_action_activated)
            self.wid_text.set_completion(self.wid_completion)
            self.wid_text.connect('changed', self._update_completion)
        else:
            self.wid_completion = None

        self.but_add = Gtk.Button(can_focus=False)
        tooltips.set_tip(self.but_add, _('Add existing record'))
        self.but_add.connect('clicked', self._sig_add)
        self.but_add.add(common.IconFactory.get_image(
                'tryton-add', Gtk.IconSize.SMALL_TOOLBAR))
        self.but_add.set_relief(Gtk.ReliefStyle.NONE)
        hbox.pack_start(self.but_add, expand=False, fill=False, padding=0)

        self.label = Gtk.Label(label='(_/0)')
        hbox.pack_start(self.label, expand=False, fill=False, padding=0)

        self.but_remove = Gtk.Button(can_focus=False)
        tooltips.set_tip(self.but_remove, _('Remove selected record'))
        self.but_remove.connect('clicked', self._sig_remove)
        self.but_remove.add(common.IconFactory.get_image(
                'tryton-remove', Gtk.IconSize.SMALL_TOOLBAR))
        self.but_remove.set_relief(Gtk.ReliefStyle.NONE)
        hbox.pack_start(self.but_remove, expand=False, fill=False, padding=0)

        self.but_unremove = Gtk.Button(can_focus=False)
        tooltips.set_tip(self.but_unremove, _("Restore selected record"))
        self.but_unremove.connect('clicked', self._sig_unremove)
        self.but_unremove.add(common.IconFactory.get_image(
                'tryton-undo', Gtk.IconSize.SMALL_TOOLBAR))
        self.but_unremove.set_relief(Gtk.ReliefStyle.NONE)
        hbox.pack_start(self.but_unremove, expand=False, fill=False, padding=0)

        tooltips.enable()

        frame = Gtk.Frame()
        frame.add(hbox)
        frame.set_shadow_type(Gtk.ShadowType.OUT)
        vbox.pack_start(frame, expand=False, fill=True, padding=0)

        model = attrs['relation']
        breadcrumb = list(self.view.screen.breadcrumb)
        breadcrumb.append(
            attrs.get('string') or common.MODELNAME.get(model))
        self.screen = Screen(model,
            view_ids=attrs.get('view_ids', '').split(','),
            mode=['tree'], views_preload=attrs.get('views', {}),
            order=attrs.get('order'),
            row_activate=self._on_activate,
            readonly=True,
            limit=None,
            context=self.view.screen.context,
            breadcrumb=breadcrumb)
        self.screen.windows.append(self)

        vbox.pack_start(self.screen.widget, expand=True, fill=True, padding=0)

        self.title.set_mnemonic_widget(
            self.screen.current_view.mnemonic_widget)

        self.screen.widget.connect('key_press_event', self.on_keypress)
        self.wid_text.connect('key_press_event', self.on_keypress)

        self._popup = False

    def on_keypress(self, widget, event):
        editable = self.wid_text.get_editable()
        activate_keys = [Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab]
        remove_keys = [Gdk.KEY_Delete, Gdk.KEY_KP_Delete]
        if not self.wid_completion:
            activate_keys.append(Gdk.KEY_Return)
        if widget == self.screen.widget:
            if event.keyval == Gdk.KEY_F3 and editable:
                self._sig_add()
                return True
            elif event.keyval == Gdk.KEY_F2:
                self._sig_edit()
                return True
            elif event.keyval in remove_keys and editable:
                self._sig_remove()
                return True
            elif event.keyval == Gdk.KEY_Insert:
                self._sig_unremove()
                return True
        elif widget == self.wid_text:
            if event.keyval == Gdk.KEY_F3:
                self._sig_new()
                return True
            elif event.keyval == Gdk.KEY_F2:
                self._sig_add()
                return True
            elif event.keyval in activate_keys and self.wid_text.get_text():
                self._sig_add()
                self.wid_text.grab_focus()
        return False

    def destroy(self):
        self.wid_text.disconnect_by_func(self._focus_out)
        self.screen.destroy()

    def get_access(self, type_):
        model = self.attrs['relation']
        if model:
            return common.MODELACCESS[model][type_]
        else:
            return True

    @property
    def read_access(self):
        return self.get_access('read')

    @property
    def create_access(self):
        return int(self.attrs.get('create', 1)) and self.get_access('create')

    def _sig_add(self, *args):
        domain = self.field.domain_get(self.record)
        add_remove = self.record.expr_eval(self.attrs.get('add_remove'))
        if add_remove:
            domain = [domain, add_remove]
        existing_ids = self.field.get_eval(self.record)
        if existing_ids:
            domain = [domain, ('id', 'not in', existing_ids)]
        context = self.field.get_search_context(self.record)
        order = self.field.get_search_order(self.record)
        value = self.wid_text.get_text()

        if self._popup:
            return
        else:
            self._popup = True

        def callback(result):
            if result:
                ids = [x[0] for x in result]
                self.screen.load(ids, modified=True)
            self.screen.set_cursor()
            self.wid_text.set_text('')
            self._popup = False
        win = WinSearch(self.attrs['relation'], callback, sel_multi=True,
            context=context, domain=domain, order=order,
            view_ids=self.attrs.get('view_ids', '').split(','),
            views_preload=self.attrs.get('views', {}),
            new=self.create_access,
            title=self.attrs.get('string'))
        win.screen.search_filter(quote(value))
        win.show()

    def _sig_remove(self, *args):
        self.screen.remove(remove=True)

    def _sig_unremove(self, *args):
        self.screen.unremove()

    def _on_activate(self):
        self._sig_edit()

    def _get_screen_form(self):
        domain = self.field.domain_get(self.record)
        add_remove = self.record.expr_eval(self.attrs.get('add_remove'))
        if add_remove:
            domain = [domain, add_remove]
        context = self.field.get_context(self.record)
        # Remove the first tree view as mode is form only
        view_ids = self.attrs.get('view_ids', '').split(',')[1:]
        model = self.attrs['relation']
        breadcrumb = list(self.view.screen.breadcrumb)
        breadcrumb.append(
            self.attrs.get('string') or common.MODELNAME.get(model))
        return Screen(model, domain=domain,
            view_ids=view_ids,
            mode=['form'], views_preload=self.attrs.get('views', {}),
            context=context, breadcrumb=breadcrumb)

    def _sig_edit(self):
        if not self.screen.current_record:
            return
        if self._popup:
            return
        else:
            self._popup = True
        # Create a new screen that is not linked to the parent otherwise on the
        # save of the record will trigger the save of the parent
        screen = self._get_screen_form()
        screen.load([self.screen.current_record.id])
        screen.current_record = screen.group.get(self.screen.current_record.id)

        def callback(result):
            if result:
                screen.current_record.save()
                added = 'id' in self.screen.current_record.modified_fields
                # Force a reload on next display
                self.screen.current_record.cancel()
                if added:
                    self.screen.current_record.modified_fields.setdefault('id')
                # Force a display to clear the CellCache
                self.screen.display()
            self._popup = False
        WinForm(screen, callback)

    def _sig_new(self, defaults=None):
        if self._popup:
            return
        else:
            self._popup = True
        screen = self._get_screen_form()
        defaults = defaults.copy() if defaults is not None else {}
        defaults['rec_name'] = self.wid_text.get_text()

        def callback(result):
            if result:
                record = screen.current_record
                self.screen.load([record.id], modified=True)
            self.wid_text.set_text('')
            self.wid_text.grab_focus()
            self._popup = False

        WinForm(
            screen, callback, new=True, save_current=True, defaults=defaults)

    def _readonly_set(self, value):
        self._readonly = value
        self._set_button_sensitive()
        self.wid_text.set_sensitive(not value)
        self.wid_text.set_editable(not value)
        self._set_label_state()

    def _required_set(self, value):
        self._required = value
        self._set_label_state()

    def _set_label_state(self):
        common.apply_label_attributes(
            self.title, self._readonly, self._required)

    def _set_button_sensitive(self):
        if self.record and self.field:
            field_size = self.record.expr_eval(self.attrs.get('size'))
            m2m_size = len(self.field.get_eval(self.record))
            size_limit = (field_size is not None
                and m2m_size >= field_size >= 0)
        else:
            size_limit = False

        removable = any(
            not r.deleted and not r.removed
            for r in self.screen.selected_records)
        unremovable = any(
            r.deleted or r.removed for r in self.screen.selected_records)

        self.but_add.set_sensitive(bool(
                not self._readonly
                and not size_limit))
        self.but_remove.set_sensitive(bool(
                not self._readonly
                and removable
                and self._position))
        self.but_unremove.set_sensitive(bool(
                not self._readonly
                and not size_limit
                and unremovable
                and self._position))

    def record_message(self, position, size, *args):
        self._position = position
        name = str(position) if position else '_'
        selected = len(self.screen.selected_records)
        if selected > 1:
            name += '#%i' % selected
        name = '(%s/%s)' % (name, common.humanize(size))
        self.label.set_text(name)
        self._set_button_sensitive()

    def display(self):
        super(Many2Many, self).display()
        if not self.field:
            self.screen.new_group()
            self.screen.current_record = None
            self.screen.parent = None
            self.screen.display()
            return False
        new_group = self.field.get_client(self.record)
        if id(self.screen.group) != id(new_group):
            self.screen.group = new_group
        self.screen.display()
        return True

    def set_value(self):
        self.screen.current_view.set_value()
        return True

    def _completion_match_selected(self, completion, model, iter_):
        record_id, defaults = model.get(iter_, 1, 2)
        if record_id is not None:
            self.screen.load([record_id], modified=True)
            self.wid_text.set_text('')
            self.wid_text.grab_focus()

            completion_model = self.wid_completion.get_model()
            completion_model.clear()
            completion_model.search_text = self.wid_text.get_text()
        else:
            self._sig_new(defaults)
        return True

    def _update_completion(self, widget):
        if self._readonly:
            return
        if not self.record:
            return
        model = self.attrs['relation']
        domain = self.field.domain_get(self.record)
        add_remove = self.record.expr_eval(self.attrs.get('add_remove'))
        if add_remove:
            domain = [domain, add_remove]
        existing_ids = self.field.get_eval(self.record)
        if existing_ids:
            domain = [domain, ('id', 'not in', existing_ids)]
        update_completion(
            self.wid_text, self.record, self.field, model, domain)

    def _completion_action_activated(self, completion, index):
        if index == 0:
            self._sig_add()
            self.wid_text.grab_focus()
        elif index == 1:
            self._sig_new()
