====================
Move Cancel Scenario
====================

Imports::

    >>> from decimal import Decimal

    >>> from proteus import Model, Wizard
    >>> from trytond.modules.account.tests.tools import (
    ...     create_chart, create_fiscalyear, get_accounts)
    >>> from trytond.modules.company.tests.tools import create_company
    >>> from trytond.modules.currency.tests.tools import get_currency
    >>> from trytond.tests.tools import activate_modules, assertEqual

Activate modules::

    >>> config = activate_modules('account', create_company, create_chart)

    >>> Reconciliation = Model.get('account.move.reconciliation')

Create fiscal year::

    >>> fiscalyear = create_fiscalyear()
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]

Get accounts::

    >>> accounts = get_accounts()
    >>> receivable = accounts['receivable']
    >>> revenue = accounts['revenue']

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()
    >>> party = Party(name='Party')
    >>> party.save()

Create Move to cancel::

    >>> Journal = Model.get('account.journal')
    >>> Move = Model.get('account.move')
    >>> journal_revenue, = Journal.find([
    ...         ('code', '=', 'REV'),
    ...         ])
    >>> journal_cash, = Journal.find([
    ...         ('code', '=', 'CASH'),
    ...         ])
    >>> move = Move()
    >>> move.period = period
    >>> move.journal = journal_revenue
    >>> move.date = period.start_date
    >>> line = move.lines.new()
    >>> line.account = revenue
    >>> line.credit = Decimal(42)
    >>> line = move.lines.new()
    >>> line.account = receivable
    >>> line.debit = Decimal(32)
    >>> line.party = customer
    >>> line.second_currency = get_currency('EUR')
    >>> line.amount_second_currency = Decimal(30)
    >>> line = move.lines.new()
    >>> line.account = receivable
    >>> line.debit = Decimal(10)
    >>> line.party = party
    >>> move.save()
    >>> revenue.reload()
    >>> revenue.credit
    Decimal('42.00')
    >>> receivable.reload()
    >>> receivable.debit
    Decimal('42.00')

Cancel reversal Move::

    >>> cancel_move = Wizard('account.move.cancel', [move])
    >>> cancel_move.form.description = "Reversal"
    >>> cancel_move.form.reversal = True
    >>> cancel_move.execute('cancel')
    >>> cancel_move.state
    'end'
    >>> move.reload()
    >>> [bool(l.reconciliation) for l in move.lines if l.account == receivable]
    [True, True]
    >>> line, _ = [l for l in move.lines if l.account == receivable]
    >>> cancel_move, = [l.move for l in line.reconciliation.lines
    ...     if l.move != move]
    >>> assertEqual(cancel_move.origin, move)
    >>> cancel_move.description
    'Reversal'
    >>> assertEqual({l.origin for l in cancel_move.lines}, set(move.lines))
    >>> revenue.reload()
    >>> revenue.credit
    Decimal('42.00')
    >>> revenue.debit
    Decimal('42.00')
    >>> receivable.reload()
    >>> receivable.credit
    Decimal('42.00')
    >>> receivable.debit
    Decimal('42.00')

    >>> reconciliations = {
    ...     l.reconciliation for l in cancel_move.lines if l.reconciliation}
    >>> Reconciliation.delete(list(reconciliations))
    >>> cancel_move.reload()
    >>> cancel_move.delete()

Cancel Move::

    >>> cancel_move = Wizard('account.move.cancel', [move])
    >>> cancel_move.form.description = 'Cancel'
    >>> cancel_move.form.reversal = False
    >>> cancel_move.execute('cancel')
    >>> cancel_move.state
    'end'
    >>> move.reload()
    >>> [bool(l.reconciliation) for l in move.lines if l.account == receivable]
    [True, True]
    >>> line, _ = [l for l in move.lines if l.account == receivable]
    >>> cancel_move, = [l.move for l in line.reconciliation.lines
    ...     if l.move != move]
    >>> assertEqual(cancel_move.origin, move)
    >>> cancel_move.description
    'Cancel'
    >>> assertEqual({l.origin for l in cancel_move.lines}, set(move.lines))
    >>> revenue.reload()
    >>> revenue.credit
    Decimal('0.00')
    >>> receivable.reload()
    >>> receivable.debit
    Decimal('0.00')
