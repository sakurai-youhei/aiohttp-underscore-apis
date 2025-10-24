from enum import StrEnum
from typing import Any, Awaitable, Callable, Concatenate, Protocol, cast

from aiohttp import web
from webargs import fields
from webargs.aiohttpparser import use_kwargs

from aiohttp_underscore_apis.context import Context


class Ids(fields.DelimitedList):
    def __init__(self):
        super().__init__(fields.Int)

    def _deserialize(self, *args, **kwargs):
        return set(super()._deserialize(*args, **kwargs))


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
        **kwargs: Any,
    ) -> Awaitable[web.Response]: ...


def compose(*decorators):
    def composed(fn):
        for decorator in reversed(decorators):
            fn = decorator(fn)
        return fn

    return composed


_format_field = fields.Enum(Format, by_value=True)

dissect_request = cast(
    Callable[
        [Signature],
        Callable[Concatenate[web.Request, ...], Awaitable[web.Response]],
    ],
    compose(
        use_kwargs({"ids": Ids()}, location="match_info"),
        use_kwargs({"format": _format_field}, location="querystring"),
        Context.use,
    ),
)
