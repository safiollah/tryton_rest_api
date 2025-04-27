# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import json

from trytond.model.exceptions import AccessError
from trytond.pool import Pool
from trytond.tests.test_tryton import (
    TestCase, activate_module, with_transaction)
from trytond.transaction import Transaction


class ResourceTestCase(TestCase):
    "Test Resource"

    @classmethod
    def setUpClass(cls):
        activate_module('tests')

    @with_transaction()
    def test_resources_copied(self):
        "Test resources are copied"
        pool = Pool()
        Resource = pool.get('test.resource')
        Other = pool.get('test.resource.other')
        Note = pool.get('ir.note')

        record = Resource()
        record.save()
        note = Note(resource=record, copy_to_resources=[Other.__name__])
        note.save()
        other = Other()
        other.save()
        copies = record.copy_resources_to(other)

        other_notes = Note.search([('resource', '=', str(other))])
        self.assertTrue(other_notes)
        self.assertEqual(len(other_notes), 1)
        self.assertEqual(other_notes, copies)

    @with_transaction()
    def test_resources_not_copied(self):
        "Test resources are not copied"
        pool = Pool()
        Resource = pool.get('test.resource')
        Other = pool.get('test.resource.other')
        Note = pool.get('ir.note')

        record = Resource()
        record.save()
        note = Note(resource=record)
        note.save()
        other = Other()
        other.save()
        copies = record.copy_resources_to(other)

        other_notes = Note.search([('resource', '=', str(other))])
        self.assertFalse(other_notes)
        self.assertFalse(copies)

    @with_transaction()
    def test_note_write(self):
        "Test note write behaviour"
        pool = Pool()
        Note = pool.get('ir.note')
        Resource = pool.get('test.resource')
        User = pool.get('res.user')

        user = User(login='test')
        user.save()
        record = Resource()
        record.save()
        note = Note(resource=record, message="Message")
        note.save()
        write_date = note.write_date

        with Transaction().set_user(user.id):
            user_note = Note(note.id)
            user_note.unread = False
            user_note.save()

        note = Note(note.id)
        self.assertEqual(user_note.write_date, write_date)

    @with_transaction()
    def test_resources_rule(self):
        "Test resources rules are applied on search"
        pool = Pool()
        Note = pool.get('ir.note')
        Warning = pool.get('res.user.warning')

        warning1 = Warning(user=0, name="root")
        warning1.save()
        note1 = Note(resource=warning1)
        note1.save()
        warning2 = Warning(user=1, name="admin")
        warning2.save()
        note2 = Note(resource=warning2)
        note2.save()

        with Transaction().set_context(_check_access=True):
            notes = Note.search([])
            count = Note.search([], count=True)
            query = Note.search([], query=True)

            self.assertEqual(notes, [note2])
            self.assertEqual(count, 1)
            self.assertTrue(query)

    @with_transaction()
    def test_resource_with_access(self):
        "Test create/write/read/delete on resource with access"
        pool = Pool()
        Note = pool.get('ir.note')
        Resource = pool.get('test.resource')
        ModelAccess = pool.get('ir.model.access')

        ModelAccess.create([{
                    'model': Resource.__name__,
                    'group': None,
                    'perm_write': True,
                    'perm_read': True,
                    }])
        record, = Resource.create([{}])

        with Transaction().set_context(_check_access=True):
            note_id, = Note.create([{
                        'resource': record,
                        'message': "Foo",
                        }])
            Note.write([note_id], {'message': "Bar"})
            Note.read([note_id], ['message'])
            Note.delete([note_id])

    @with_transaction()
    def test_resource_without_access(self):
        "Test create/write/read/delete on resource without access"
        pool = Pool()
        Note = pool.get('ir.note')
        Resource = pool.get('test.resource')
        ModelAccess = pool.get('ir.model.access')

        ModelAccess.create([{
                    'model': Resource.__name__,
                    'group': None,
                    'perm_write': False,
                    'perm_read': False,
                    }])
        record, = Resource.create([{}])

        note_id, = Note.create([{
                    'resource': record,
                    'message': "Message",
                    }])

        with Transaction().set_context(_check_access=True):
            with self.assertRaises(AccessError):
                Note.create([{
                            'resource': record,
                            'message': "Message",
                            }])

            with self.assertRaises(AccessError):
                Note.write([note_id], {'message': "Bar"})
            with self.assertRaises(AccessError):
                Note.read([note_id], ['message'])
            with self.assertRaises(AccessError):
                Note.delete([note_id])

    @with_transaction()
    def test_resource_with_rule(self):
        "Test create/write/read/delete on resource with rule"
        pool = Pool()
        Note = pool.get('ir.note')
        Resource = pool.get('test.resource')
        RuleGroup = pool.get('ir.rule.group')

        RuleGroup.create([{
                    'name': "Test",
                    'model': Resource.__name__,
                    'global_p': True,
                    'perm_write': True,
                    'rules': [('create', [{
                                    'domain': json.dumps(
                                        [('id', '>=', 0)]),
                                    }])],
                    }])
        record, = Resource.create([{}])

        with Transaction().set_context(_check_access=True):
            note_id, = Note.create([{
                        'resource': record,
                        'message': "Foo",
                        }])
            Note.write([note_id], {'message': "Bar"})
            Note.read([note_id], ['message'])
            Note.delete([note_id])

    @with_transaction()
    def test_resource_without_rule(self):
        "Test create/write/read/delete on resource without rule"
        pool = Pool()
        Note = pool.get('ir.note')
        Resource = pool.get('test.resource')
        RuleGroup = pool.get('ir.rule.group')

        RuleGroup.create([{
                    'name': "Test",
                    'model': Resource.__name__,
                    'global_p': True,
                    'perm_write': True,
                    'rules': [('create', [{
                                    'domain': json.dumps(
                                        [('id', '<', 0)]),
                                    }])],
                    }])
        record, = Resource.create([{}])

        note_id, = Note.create([{
                    'resource': record,
                    'message': "Message",
                    }])

        with Transaction().set_context(_check_access=True):
            with self.assertRaises(AccessError):
                Note.create([{
                            'resource': record,
                            'message': "Message",
                            }])

            with self.assertRaises(AccessError):
                Note.write([note_id], {'message': "Bar"})
            with self.assertRaises(AccessError):
                Note.read([note_id], ['message'])
            with self.assertRaises(AccessError):
                Note.delete([note_id])
