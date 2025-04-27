# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.exceptions import UserError, UserWarning
from trytond.model.exceptions import ValidationError


class PeriodNotFoundError(UserError):
    pass


class PeriodValidationError(ValidationError):
    pass


class ClosePeriodError(PeriodValidationError):
    pass


class PeriodDatesError(PeriodValidationError):
    pass


class FiscalYearNotFoundError(UserError):
    pass


class FiscalYearCloseError(UserError):
    pass


class FiscalYearReOpenError(UserError):
    pass


class JournalMissing(UserError):
    pass


class AccountMissing(UserError):
    pass


class AccountValidationError(ValidationError):
    pass


class SecondCurrencyError(AccountValidationError):
    pass


class ChartWarning(UserWarning):
    pass


class PostError(UserError):
    pass


class MoveTemplateExpressionError(UserError):
    pass


class MoveTemplateKeywordValidationError(ValidationError):
    pass


class CopyWarning(UserWarning):
    pass


class CancelWarning(UserWarning):
    pass


class ReconciliationError(ValidationError):
    pass


class ReconciliationDeleteWarning(UserWarning):
    pass


class CancelDelegatedWarning(UserWarning):
    pass


class GroupLineError(UserError):
    pass


class GroupLineWarning(UserWarning):
    pass


class RescheduleLineError(UserError):
    pass


class RescheduleLineWarning(UserWarning):
    pass


class DelegateLineError(UserError):
    pass


class DelegateLineWarning(UserWarning):
    pass
