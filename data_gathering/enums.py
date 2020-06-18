
import enum


class AccountType(enum.Enum):
    Organization = 0
    User = 1


class EndCondition(enum.Enum):
    Unmaintained = 'unmaintained_ids'
    Maintained = 'maintained_ids'
    Visited = 'not_suitable_ids'
