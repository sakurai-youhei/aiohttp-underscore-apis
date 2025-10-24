from enum import StrEnum
from typing import Any, Awaitable, Callable, Concatenate, Protocol, Type, cast

from aiohttp import web
from webargs.aiohttpparser import use_kwargs

from aiohttp_underscore_apis.apis._cat.options import (
    Header,
    Help,
    Order,
    Sort,
    Verbose,
)
from aiohttp_underscore_apis.apis.common import (
    Format,
    compose,
)
from aiohttp_underscore_apis.apis.common import (
    dissect_request as _dissect_request,
)
from aiohttp_underscore_apis.context import Context


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


def dissect_request(header: Type[StrEnum]):
    return cast(
        Callable[
            [Signature],
            Callable[Concatenate[web.Request, ...], Awaitable[web.Response]],
        ],
        compose(
            _dissect_request,
            use_kwargs(
                {
                    "help": Help(),
                    "v": Verbose(),
                    "s": Sort(header),
                    "h": Header(header),
                },
                location="querystring",
            ),
        ),
    )


class SortKeyWithNanSupport:
    def __init__(self, column: StrEnum):
        self.column = column

    def __call__(self, row: dict[str, Any]) -> Any:
        value = row[self.column]
        if value != value:  # NaN check
            return float("-inf")
        return value
