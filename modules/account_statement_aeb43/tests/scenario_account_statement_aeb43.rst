================================
Account Statement AEB43 Scenario
================================

Imports::

    >>> from functools import partial

    >>> from proteus import Model, Wizard
    >>> from trytond.modules.account.tests.tools import create_chart, get_accounts
    >>> from trytond.modules.company.tests.tools import create_company, get_company
    >>> from trytond.modules.currency.tests.tools import get_currency
    >>> from trytond.tests.tools import activate_modules, assertEqual
    >>> from trytond.tools import file_open

Activate modules::

    >>> config = activate_modules(
    ...     'account_statement_aeb43',
    ...     partial(create_company, currency='EUR'), create_chart)

Get company::

    >>> company = get_company()

Setup currency::

    >>> eur = get_currency('EUR')
    >>> eur.numeric_code = '978'
    >>> eur.save()

Get accounts::

    >>> accounts = get_accounts()
    >>> cash = accounts['cash']

Create parties::

    >>> Party = Model.get('party.party')
    >>> bank_party = Party(name='Bank')
    >>> bank_party.save()

Create Bank Account::

    >>> Bank = Model.get('bank')
    >>> BankAccount = Model.get('bank.account')
    >>> bank = Bank()
    >>> bank.party = bank_party
    >>> bank.save()
    >>> bank_account = BankAccount()
    >>> bank_account.bank = bank
    >>> bank_account.owners.append(Party(company.party.id))
    >>> bank_account.currency = company.currency
    >>> bank_account_number = bank_account.numbers.new()
    >>> bank_account_number.type = 'iban'
    >>> bank_account_number.number = 'ES0600815398730001414452'
    >>> bank_account.save()

Create a statement::

    >>> AccountJournal = Model.get('account.journal')
    >>> StatementJournal = Model.get('account.statement.journal')
    >>> account_journal, = AccountJournal.find([('code', '=', 'STA')], limit=1)
    >>> journal = StatementJournal(name='Number',
    ...     journal=account_journal,
    ...     validation='number_of_lines',
    ...     account=cash,
    ...     bank_account=bank_account,
    ...     )
    >>> journal.save()

Import AEB43 file::

    >>> Statement = Model.get('account.statement')
    >>> with file_open(
    ...         'account_statement_aeb43/tests/n43.txt',
    ...         mode='rb') as fp:
    ...     aeb43 = fp.read()
    >>> waeb43 = Wizard('account.statement.import')
    >>> waeb43.form.file_format = 'aeb43'
    >>> waeb43.form.file_ = aeb43
    >>> waeb43.execute('import_')

Check Statement::

    >>> Statement = Model.get('account.statement')
    >>> statement, = Statement.find([])
    >>> assertEqual(statement.journal, journal)
    >>> statement.number_of_lines
    1
    >>> statement.total_amount
    Decimal('-10.98')
    >>> statement.start_balance
    Decimal('3005')
    >>> statement.end_balance
    Decimal('2994.02')
    >>> statement.number_of_lines
    1
    >>> origin, = statement.origins
    >>> origin.date
    datetime.date(2018, 3, 19)
    >>> origin.amount
    Decimal('-10.98')
    >>> origin.description
    'COMPRA TARG 5540XXXXXXXX3014 DNH*MICHAEL SCOTT'
    >>> origin.information['aeb43_record_type']
    '12'
    >>> origin.information['aeb43_first_reference']
    '000000000000'
    >>> origin.information['aeb43_second_reference']
    '5540014387733014'
