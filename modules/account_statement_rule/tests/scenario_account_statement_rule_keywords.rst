=======================================
Account Statement Rule Keyword Scenario
=======================================

Imports::

    >>> import datetime as dt
    >>> from decimal import Decimal

    >>> from proteus import Model
    >>> from trytond.modules.account.tests.tools import (
    ...     create_chart, create_fiscalyear, get_accounts)
    >>> from trytond.modules.account_invoice.tests.tools import (
    ...     set_fiscalyear_invoice_sequences)
    >>> from trytond.modules.company.tests.tools import create_company, get_company
    >>> from trytond.tests.tools import activate_modules, assertEqual

    >>> today = dt.date.today()

Activate modules::

    >>> config = activate_modules(
    ...     'account_statement_rule', create_company, create_chart)

Get company::

    >>> company = get_company()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(today=today))
    >>> fiscalyear.click('create_period')

Get accounts::

    >>> accounts = get_accounts()
    >>> receivable = accounts['receivable']
    >>> cash = accounts['cash']

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name="Customer")
    >>> customer.save()

Create statement rules::

    >>> Rule = Model.get('account.statement.rule')

    >>> rule = Rule(name="Party Rule")
    >>> rule.company = company
    >>> rule.description = r"Party: *(?P<party>.*)"
    >>> line = rule.lines.new()
    >>> line.amount = "pending"
    >>> line.account = receivable
    >>> rule.save()

Create a statement with non matching rule::

    >>> AccountJournal = Model.get('account.journal')
    >>> StatementJournal = Model.get('account.statement.journal')
    >>> Statement = Model.get('account.statement')
    >>> account_journal, = AccountJournal.find([('code', '=', 'STA')], limit=1)
    >>> journal_number = StatementJournal(name="Number",
    ...     journal=account_journal,
    ...     account=cash,
    ...     validation='number_of_lines',
    ...     )
    >>> journal_number.save()

    >>> statement = Statement(name="number origins")
    >>> statement.journal = journal_number
    >>> statement.number_of_lines = 1
    >>> origin = statement.origins.new()
    >>> origin.date = today
    >>> origin.amount = Decimal('50.00')
    >>> origin.description = "Party: %s-%s" % (customer.code, customer.name)
    >>> statement.save()
    >>> len(statement.lines)
    0

Apply rules on statement::

    >>> statement.click('apply_rules')
    >>> len(statement.lines)
    0

Manually create a line for the origin::

    >>> origin, = statement.origins
    >>> line = origin.lines.new()
    >>> line.party = customer
    >>> origin.save()
    >>> statement.click('validate_statement')
    >>> statement.click('post')


Create a new statement with same keyword::

    >>> statement = Statement(name="number origins")
    >>> statement.journal = journal_number
    >>> statement.number_of_lines = 1
    >>> origin = statement.origins.new()
    >>> origin.date = today
    >>> origin.amount = Decimal('50.00')
    >>> origin.description = "Party: %s-%s" % (customer.code, customer.name)
    >>> statement.save()
    >>> len(statement.lines)
    0

Now a party is found::

    >>> statement.click('apply_rules')
    >>> line, = statement.lines
    >>> line.amount
    Decimal('50.00')
    >>> assertEqual(line.party, customer)
    >>> assertEqual(line.account, receivable)
