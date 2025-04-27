# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal

from trytond.i18n import gettext
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.wizard import Button, StateTransition, StateView, Wizard

from .exceptions import DepositError


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    @classmethod
    def __setup__(cls):
        super(Invoice, cls).__setup__()
        cls._buttons.update({
                'recall_deposit': {
                    'invisible': Eval('state') != 'draft',
                    'depends': ['state'],
                    },
                })

    @classmethod
    def _post(cls, invoices):
        super()._post(invoices)
        cls.check_deposit(invoices)

    @classmethod
    @ModelView.button_action('account_deposit.wizard_recall_deposit')
    def recall_deposit(cls, invoices):
        pass

    def call_deposit(self, account, description, maximum=None):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')

        balance = self.party.get_deposit_balance(
            account, currency=self.currency)
        if maximum is None:
            maximum = self.total_amount
        total_amount = min(maximum, self.total_amount, key=abs)

        amount = Decimal(0)
        if self.type.startswith('in'):
            if balance > 0 and total_amount > 0:
                amount = -min(balance, total_amount)
        else:
            if balance < 0 and total_amount > 0:
                amount = -min(-balance, total_amount)
        to_delete = []
        for line in self.lines:
            if line.account == account:
                to_delete.append(line)
        if amount < 0:
            line = self._get_deposit_recall_invoice_line(
                amount, account, description)
            try:
                line.sequence = max(l.sequence for l in self.lines
                    if l.sequence is not None)
            except ValueError:
                pass
            line.save()
        else:
            amount = Decimal(0)
        if to_delete:
            InvoiceLine.delete(to_delete)
        return amount

    def _get_deposit_recall_invoice_line(self, amount, account, description):
        pool = Pool()
        Line = pool.get('account.invoice.line')

        line = Line(
            invoice=self,
            company=self.company,
            type='line',
            quantity=1,
            account=account,
            unit_price=amount,
            description=description,
            )
        # Set taxes
        line.on_change_account()
        return line

    @classmethod
    def check_deposit(cls, invoices):
        to_check = set()
        for invoice in invoices:
            for line in invoice.lines:
                if line.type != 'line':
                    continue
                if line.account.type.deposit:
                    if line.amount < 0:
                        sign = 1 if invoice.type.startswith('in') else -1
                        to_check.add((invoice.party, line.account, sign))

        for party, account, sign in to_check:
            if not party.check_deposit(account, sign):
                raise DepositError(
                    gettext('account_deposit.msg_deposit_not_enough',
                        account=account.rec_name,
                        party=party.rec_name))


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    @classmethod
    def _account_domain(cls, type_):
        domain = super(InvoiceLine, cls)._account_domain(type_)
        return domain + [('type.deposit', '=', True)]


class DepositRecall(Wizard):
    __name__ = 'account.invoice.recall_deposit'
    start = StateView('account.invoice.recall_deposit.start',
        'account_deposit.recall_deposit_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Recall', 'recall', 'tryton-ok', default=True),
            ])
    recall = StateTransition()

    def default_start(self, fields):
        return {
            'company': self.record.company.id,
            'currency': self.record.currency.id,
            }

    def transition_recall(self):
        self.record.call_deposit(self.start.account, self.start.description)
        return 'end'


class DepositRecallStart(ModelView):
    __name__ = 'account.invoice.recall_deposit.start'
    company = fields.Many2One('company.company', 'Company', readonly=True)
    currency = fields.Many2One('currency.currency', "Currency", readonly=True)
    account = fields.Many2One('account.account', 'Account', required=True,
        domain=[
            ('type.deposit', '=', True),
            ('company', '=', Eval('company', -1)),
            ['OR',
                ('currency', '=', Eval('currency', -1)),
                ('second_currency', '=', Eval('currency', -1)),
                ],
            ])
    description = fields.Text('Description', required=True)
