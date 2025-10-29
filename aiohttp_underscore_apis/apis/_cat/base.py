from abc import abstractmethod
from collections.abc import Awaitable, Iterable, Sequence, Set
from enum import StrEnum
from fnmatch import fnmatch
from itertools import chain
from operator import itemgetter
from typing import Any, Callable, Mapping

import yaml
from aiohttp import web
from tabulate import tabulate
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
    dissect_request,
)
from aiohttp_underscore_apis.context import Context


class CatBase(StrEnum):
    @classmethod
    @abstractmethod
    def defaults(cls) -> Iterable[str]:
        pass

    @classmethod
    @abstractmethod
    def helps(cls) -> Mapping[str, str]:
        pass

    @classmethod
    @abstractmethod
    def iter_rows(cls, context: Context) -> Iterable[Mapping["CatBase", Any]]:
        pass

    @classmethod
    def _help_response(cls) -> web.Response:
        text = tabulate(cls.helps().items())
        return web.Response(text=text + "\n")

    @classmethod
    def _include_headers(cls, h: Iterable[str]) -> Sequence["CatBase"]:
        return tuple(
            chain.from_iterable(
                (header for header in cls if fnmatch(header, pattern))
                for pattern in h
            )
        )

    @classmethod
    def _json_response(cls, rows, headers) -> web.Response:
        return web.json_response([dict(zip(headers, row)) for row in rows])

    @classmethod
    def _yaml_response(cls, rows, headers) -> web.Response:
        return web.Response(
            text=yaml.dump(
                [dict(zip(map(str, headers), row)) for row in rows],
                sort_keys=False,
            )
            + "\n",
            content_type="application/x-yaml",
        )

    @classmethod
    def _text_response(cls, rows, headers) -> web.Response:
        return web.Response(
            text=tabulate(
                rows,
                headers=headers,
                tablefmt="plain",
                floatfmt=".6f",
            )
            + "\n",
            content_type="text/plain",
        )

    @classmethod
    def handler(cls) -> Callable[[web.Request], Awaitable[web.Response]]:

        @dissect_request
        @use_kwargs(
            {
                "help": Help(),
                "v": Verbose(),
                "s": Sort(cls),
                "h": Header(cls),
            },
            location="querystring",
        )
        async def _handler(
            request: web.Request,
            context: Context,
            *,
            ids: Set[int] = set(),
            help: bool = False,
            format: Format = Format.TEXT,
            v: bool = False,
            s: Sequence[tuple["CatBase", Order]] = [],
            h: Iterable[str] = cls.defaults(),
            **_,
        ) -> web.Response:

            if help:
                return cls._help_response()

            table: list[Mapping["CatBase", Any]] = []
            for row in cls.iter_rows(context):
                if ids and row[cls.__members__["ID"]] not in ids:
                    continue
                table.append(row)

            for header, order in reversed(s):
                table.sort(
                    key=SortKeyWithNanSupport(header),
                    reverse=order == Order.DESC,
                )

            headers = cls._include_headers(h)
            rows = map(itemgetter(*headers), table)

            if format == Format.JSON:
                return cls._json_response(rows, headers)

            elif format == Format.YAML:
                return cls._yaml_response(rows, headers)

            return cls._text_response(rows, headers if v else [])

        return _handler


class SortKeyWithNanSupport:
    def __init__(self, header: CatBase):
        self.header = header

    def __call__(self, row: Mapping[CatBase, Any]) -> Any:
        value = row[self.header]
        if value != value:  # NaN check
            return float("-inf")
        return value
