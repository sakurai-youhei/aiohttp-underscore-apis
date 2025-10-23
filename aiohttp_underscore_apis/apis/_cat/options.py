from enum import StrEnum
from fnmatch import fnmatch
from typing import Any, Awaitable, Callable, Concatenate, Protocol, Type, cast

from aiohttp import web
from webargs import ValidationError, fields, validate
from webargs.aiohttpparser import use_kwargs

from aiohttp_underscore_apis.context import Context


class Ids(fields.DelimitedList):
    def __init__(self):
        super().__init__(fields.Int)

    def _deserialize(self, *args, **kwargs):
        return set(super()._deserialize(*args, **kwargs))


class Help(fields.Boolean):
    truthy = {"", *fields.Boolean.truthy}


class Verbose(fields.Boolean):
    truthy = {"", *fields.Boolean.truthy}


class Format(StrEnum):
    TEXT = "text"
    JSON = "json"


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


class Signature(Protocol):
    def __call__(
        self,
        request: web.Request,
        context: Context,
        *,
        ids: set[int] = set(),
        help: bool = False,
        format: Format = Format.TEXT,
        v: bool = False,
        s: list[tuple[StrEnum, Order]] = [],
        h: list[str] = [],
        **kwargs: Any,
    ) -> Awaitable[web.Response]: ...


def _compose(*decorators):
    def composed(fn):
        for decorator in reversed(decorators):
            fn = decorator(fn)
        return fn

    return composed


def use_common_options(header: Type[StrEnum]):
    return cast(
        Callable[
            [Signature],
            Callable[Concatenate[web.Request, ...], Awaitable[web.Response]],
        ],
        _compose(
            use_kwargs({"ids": Ids()}, location="match_info"),
            use_kwargs(
                {
                    "help": Help(),
                    "format": fields.Enum(Format, by_value=True),
                    "v": Verbose(),
                    "s": Sort(header),
                    "h": Header(header),
                },
                location="querystring",
            ),
            Context.use,
        ),
    )
