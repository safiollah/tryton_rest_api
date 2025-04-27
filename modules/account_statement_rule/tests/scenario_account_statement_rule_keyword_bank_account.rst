====================================================
Account Statement Rule Keyword Bank Account Scenario
====================================================

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
    ...     ['account_statement_rule', 'bank'],
    ...     create_company, create_chart)

    >>> AccountJournal = Model.get('account.journal')
    >>> Bank = Model.get('bank')
    >>> BankAccount = Model.get('bank.account')
    >>> Party = Model.get('party.party')
    >>> Rule = Model.get('account.statement.rule')
    >>> Statement = Model.get('account.statement')
    >>> StatementJournal = Model.get('account.statement.journal')

Get company::

    >>> company = get_company()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(today=today))
    >>> fiscalyear.click('create_period')

Get accounts::

    >>> accounts = get_accounts()

Create a party::

    >>> customer = Party(name="Customer")
    >>> customer.save()

Create a bank::

    >>> party_bank = Party(name="Bank")
    >>> party_bank.save()
    >>> bank = Bank(party=party_bank)
    >>> bank.save()

Create statement rules::

    >>> rule = Rule(name="Party Rule")
    >>> rule.company = company
    >>> rule.description = r"Account: *(?P<bank_account>.*)"
    >>> line = rule.lines.new()
    >>> line.amount = "pending"
    >>> line.account = accounts['receivable']
    >>> rule.save()

Create a statement with non matching rule::

    >>> account_journal, = AccountJournal.find([('code', '=', 'STA')], limit=1)
    >>> journal_number = StatementJournal(
    ...     name="Number",
    ...     journal=account_journal,
    ...     account=accounts['cash'],
    ...     validation='number_of_lines')
    >>> journal_number.save()

    >>> statement = Statement(name="Test")
    >>> statement.journal = journal_number
    >>> statement.number_of_lines = 1
    >>> origin = statement.origins.new()
    >>> origin.date = today
    >>> origin.amount = Decimal('50.00')
    >>> origin.description = "Account: 123456"
    >>> statement.save()
    >>> len(statement.lines)
    0

Apply rules on statement::

    >>> statement.click('apply_rules')
    >>> len(statement.lines)
    0

Create the bank account::

    >>> bank_account = BankAccount(bank=bank)
    >>> bank_account.owners.append(Party(customer.id))
    >>> number = bank_account.numbers.new()
    >>> number.type = 'other'
    >>> number.number = "123456"
    >>> bank_account.save()

Apply rules on statement match::

    >>> statement.click('apply_rules')
    >>> line, = statement.lines
    >>> assertEqual(line.party, customer)

    >>> statement.click('validate_statement')
    >>> statement.click('post')

Remove the bank account::

    >>> bank_account.delete()

Create a new statement with same keyword::

    >>> statement = Statement(name="Test")
    >>> statement.journal = journal_number
    >>> statement.number_of_lines = 1
    >>> origin = statement.origins.new()
    >>> origin.date = today
    >>> origin.amount = Decimal('50.00')
    >>> origin.description = "Account: 123456"
    >>> statement.save()
    >>> len(statement.lines)
    0

Now a party is found::

    >>> statement.click('apply_rules')
    >>> line, = statement.lines
    >>> line.amount
    Decimal('50.00')
    >>> assertEqual(line.party, customer)
    >>> assertEqual(line.account, accounts['receivable'])
