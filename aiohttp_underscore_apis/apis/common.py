from enum import StrEnum
from functools import partial, reduce
from typing import (
    Any,
    Awaitable,
    Callable,
    Concatenate,
    Protocol,
    cast,
)

from aiohttp import web
from webargs import fields
from webargs.aiohttpparser import use_kwargs

from aiohttp_underscore_apis.context import Context


class Ids(fields.DelimitedList):
    def __init__(self):
        super().__init__(fields.Int)

    def _deserialize(self, *args, **kwargs):
        return set(super()._deserialize(*args, **kwargs))


class Pretty(fields.Boolean):
    truthy = {"", *fields.Boolean.truthy}


class FilterPath(fields.DelimitedList):
    def __init__(self):
        super().__init__(fields.Str)


class Format(StrEnum):
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"


class Signature(Protocol):
    def __call__(
        self,
        request: web.Request,
        context: Context,
        *,
        ids: set[int] = set(),
        format: Format = Format.JSON,
        pretty: bool = False,
        filter_path: list[str] = [],
        **_: Any,
    ) -> Awaitable[web.Response]: ...


dissect_request = cast(
    Callable[
        [Signature],
        Callable[Concatenate[web.Request, ...], Awaitable[web.Response]],
    ],
    partial(
        reduce,
        lambda handler, deco: cast(Callable, deco)(handler),
        (
            Context.use,
            use_kwargs({"ids": Ids()}, location="match_info"),
            use_kwargs(
                {
                    "format": fields.Enum(Format, by_value=True),
                    "pretty": Pretty(),
                    "filter_path": FilterPath(),
                },
                location="querystring",
            ),
        ),
    ),
)
