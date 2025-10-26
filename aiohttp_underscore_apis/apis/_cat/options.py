from enum import StrEnum
from fnmatch import fnmatch
from typing import Type

from webargs import ValidationError, fields, validate


class Help(fields.Boolean):
    truthy = {"", *fields.Boolean.truthy}


class Verbose(fields.Boolean):
    truthy = {"", *fields.Boolean.truthy}


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"


class ColumnOrder(fields.DelimitedTuple):
    def __init__(self, column: Type[StrEnum]):
        super().__init__(
            (
                fields.Enum(column, by_value=True),
                fields.Enum(Order, by_value=True),
            ),
            delimiter=":",
        )
        self.validate_length.min = 1
        self.validate_length.max = 2
        self.validate_length.equal = None

    def _deserialize(self, *args, **kwargs):
        value = super()._deserialize(*args, **kwargs)
        if len(value) == 1:
            return (value[0], Order.ASC)
        return value[0], value[1]


class Sort(fields.DelimitedList):
    def __init__(self, column: Type[StrEnum]):
        super().__init__(ColumnOrder(column))


class FnmatchAnyNames(validate.Validator):
    def __init__(self, *names: str):
        self.names = tuple(names)

    def _repr_args(self) -> str:
        return f"names={self.names!r}"

    def __call__(self, value: str) -> str:
        for name in self.names:
            if fnmatch(name, value):
                break
        else:
            raise ValidationError(
                f"{value!r} does not match {self._repr_args()}"
            )

        return value


class Header(fields.DelimitedList):
    def __init__(self, column: Type[StrEnum]):
        super().__init__(fields.Str(validate=FnmatchAnyNames(*column)))
