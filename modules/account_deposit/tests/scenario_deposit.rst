================
Deposit Scenario
================

Imports::

    >>> from decimal import Decimal

    >>> from proteus import Model
    >>> from trytond.modules.account.tests.tools import (
    ...     create_chart, create_fiscalyear, get_accounts)
    >>> from trytond.modules.account_deposit.tests.tools import add_deposit_accounts
    >>> from trytond.modules.account_invoice.tests.tools import (
    ...     create_payment_term, set_fiscalyear_invoice_sequences)
    >>> from trytond.modules.company.tests.tools import create_company
    >>> from trytond.tests.tools import activate_modules

Activate modules::

    >>> config = activate_modules('account_deposit', create_company, create_chart)

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear())
    >>> fiscalyear.click('create_period')

Get accounts::

    >>> accounts = add_deposit_accounts(get_accounts())

Create party::

    >>> Party = Model.get('party.party')
    >>> party = Party(name='Party')
    >>> party.save()

Create payment_term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Create deposit invoice::

    >>> Invoice = Model.get('account.invoice')
    >>> invoice = Invoice(party=party, payment_term=payment_term)
    >>> line = invoice.lines.new()
    >>> line.account = accounts['deposit']
    >>> line.description = 'Deposit'
    >>> line.quantity = 1
    >>> line.unit_price = Decimal(100)
    >>> invoice.click('post')
    >>> invoice.untaxed_amount
    Decimal('100.00')

Check party deposit::

    >>> party.reload()
    >>> party.deposit
    Decimal('100.00')

Create final invoice::

    >>> invoice = Invoice(party=party, payment_term=payment_term)
    >>> line = invoice.lines.new()
    >>> line.account = accounts['revenue']
    >>> line.description = 'Revenue'
    >>> line.quantity = 1
    >>> line.unit_price = Decimal(500)
    >>> invoice.save()
    >>> invoice.untaxed_amount
    Decimal('500.00')

Recall deposit::

    >>> recall_deposit = invoice.click('recall_deposit')
    >>> recall_deposit.form.account = accounts['deposit']
    >>> recall_deposit.form.description = 'Recall Deposit'
    >>> recall_deposit.execute('recall')
    >>> invoice.reload()
    >>> deposit_line, = [l for l in invoice.lines
    ...     if l.account == accounts['deposit']]
    >>> deposit_line.amount
    Decimal('-100.00')
    >>> invoice.untaxed_amount
    Decimal('400.00')

Recall too much::

    >>> deposit_line.unit_price = Decimal('-200.00')
    >>> deposit_line.save()
    >>> invoice.click('post')
    Traceback (most recent call last):
        ...
    DepositError: ...

Recall available::

    >>> deposit_line.unit_price = Decimal('-100.00')
    >>> deposit_line.save()
    >>> invoice.click('post')
