==============================================
Invoice Scenario Alternate Currency Lower Rate
==============================================

Imports::

    >>> import datetime as dt
    >>> from decimal import Decimal

    >>> from proteus import Model
    >>> from trytond.modules.account.tests.tools import (
    ...     create_chart, create_fiscalyear, get_accounts)
    >>> from trytond.modules.account_invoice.tests.tools import (
    ...     set_fiscalyear_invoice_sequences)
    >>> from trytond.modules.company.tests.tools import create_company
    >>> from trytond.modules.currency.tests.tools import get_currency
    >>> from trytond.tests.tools import activate_modules, assertEqual

    >>> today = dt.date.today()

Activate modules::

    >>> config = activate_modules('account_invoice', create_company, create_chart)

Get currencies::

    >>> currency = get_currency('USD')
    >>> eur = get_currency('EUR')

Set alternate currency rates::

    >>> rate = eur.rates.new()
    >>> rate.date = today
    >>> rate.rate = Decimal('0.5')
    >>> eur.save()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(today=today))
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

Create party::

    >>> Party = Model.get('party.party')
    >>> party = Party(name='Party')
    >>> party.save()

Create invoice with alternate currency::

    >>> Invoice = Model.get('account.invoice')
    >>> invoice = Invoice()
    >>> invoice.party = party
    >>> invoice.currency = eur
    >>> line = invoice.lines.new()
    >>> line.description = "Line"
    >>> line.account = accounts['revenue']
    >>> line.quantity = 5
    >>> line.unit_price = Decimal('80')
    >>> invoice.invoice_date = today
    >>> invoice.click('post')
    >>> invoice.state
    'posted'
    >>> invoice.total_amount
    Decimal('400.00')

Pay the invoice::

    >>> pay = invoice.click('pay')
    >>> pay.form.amount
    Decimal('400.00')
    >>> assertEqual(pay.form.currency, eur)
    >>> pay.form.payment_method = payment_method
    >>> pay.form.date = today
    >>> pay.execute('choice')
    >>> pay.state
    'end'
    >>> invoice.state
    'paid'
