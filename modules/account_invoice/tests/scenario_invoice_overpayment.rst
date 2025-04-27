============================
Invoice Overpayment Scenario
============================

Imports::

    >>> from decimal import Decimal

    >>> from proteus import Model
    >>> from trytond.modules.account.tests.tools import (
    ...     create_chart, create_fiscalyear, get_accounts)
    >>> from trytond.modules.account_invoice.tests.tools import (
    ...     set_fiscalyear_invoice_sequences)
    >>> from trytond.modules.company.tests.tools import create_company
    >>> from trytond.tests.tools import activate_modules

Activate modules::

    >>> config = activate_modules('account_invoice', create_company, create_chart)

Create fiscal years::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear())
    >>> fiscalyear.click('create_period')

Get accounts::

    >>> accounts = get_accounts()

Create payment method::

    >>> Journal = Model.get('account.journal')
    >>> PaymentMethod = Model.get('account.invoice.payment.method')
    >>> Sequence = Model.get('ir.sequence')
    >>> journal_cash, = Journal.find([('type', '=', 'cash')])
    >>> payment_method = PaymentMethod()
    >>> payment_method.name = 'Cash'
    >>> payment_method.journal = journal_cash
    >>> payment_method.credit_account = accounts['cash']
    >>> payment_method.debit_account = accounts['cash']
    >>> payment_method.save()

Create write-off method::

    >>> WriteOff = Model.get('account.move.reconcile.write_off')
    >>> sequence_journal, = Sequence.find(
    ...     [('sequence_type.name', '=', "Account Journal")], limit=1)
    >>> journal_writeoff = Journal(
    ...     name='Write-Off', type='write-off', sequence=sequence_journal)
    >>> journal_writeoff.save()
    >>> writeoff = WriteOff()
    >>> writeoff.name = 'Write-off'
    >>> writeoff.journal = journal_writeoff
    >>> writeoff.credit_account = accounts['expense']
    >>> writeoff.debit_account = accounts['expense']
    >>> writeoff.save()

Create party::

    >>> Party = Model.get('party.party')
    >>> party = Party(name='Party')
    >>> party.save()

Create an invoice::

    >>> Invoice = Model.get('account.invoice')
    >>> invoice = Invoice(party=party)
    >>> line = invoice.lines.new()
    >>> line.account = accounts['revenue']
    >>> line.quantity = 1
    >>> line.unit_price = Decimal('100')
    >>> invoice.click('post')
    >>> invoice.state
    'posted'
    >>> invoice.total_amount
    Decimal('100.00')

Overpay the invoice with write-off::

    >>> pay = invoice.click('pay')
    >>> pay.form.amount = Decimal('110.00')
    >>> pay.form.payment_method = payment_method
    >>> pay.execute('choice')
    >>> pay.form.type = 'writeoff'
    >>> pay.form.writeoff = writeoff
    >>> pay.form.amount_writeoff
    Decimal('-10.00')
    >>> pay.execute('pay')
    >>> invoice.state
    'paid'

    >>> accounts['receivable'].reload()
    >>> accounts['receivable'].balance
    Decimal('0.00')

Overpay the invoice without write-off::

    >>> invoice, = invoice.duplicate()
    >>> invoice.click('post')
    >>> pay = invoice.click('pay')
    >>> pay.form.amount = Decimal('110.00')
    >>> pay.form.payment_method = payment_method
    >>> pay.execute('choice')
    >>> pay.form.type = 'overpayment'
    >>> pay.execute('pay')
    >>> invoice.state
    'paid'

    >>> accounts['receivable'].reload()
    >>> accounts['receivable'].balance
    Decimal('-10.00')
