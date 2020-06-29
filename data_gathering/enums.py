
from enum import Enum


class AccountType(Enum):
    Organization = 0
    User = 1


class EndCondition(Enum):
    Unmaintained = 'unmaintained_ids'
    Maintained = 'maintained_ids'
    NotSuitable = 'not_suitable_ids'
