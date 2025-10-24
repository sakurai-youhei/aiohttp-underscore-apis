from enum import StrEnum
from fnmatch import fnmatch
from itertools import chain
from operator import itemgetter
from typing import Any

import yaml
from aiohttp import web
from tabulate import tabulate

from aiohttp_underscore_apis.apis._cat.helpers import (
    SortKeyWithNanSupport,
    dissect_request,
)
from aiohttp_underscore_apis.apis._cat.options import Order
from aiohttp_underscore_apis.apis.common import Format
from aiohttp_underscore_apis.context import Context
from aiohttp_underscore_apis.stats import RouteStats


class RoutesColumn(StrEnum):
    ID = "id"
    HANDLER = "handler"
    NAME = "name"
    METHOD = "method"
    PATH = "path"
    REQ_ACTIVE_COUNT = "stats.req.active"
    REQ_TOTAL_COUNT = "stats.req.total"
    RESP_TIME_AVG_1M = "stats.resp.time_avg_1m"
    RESP_TIME_AVG_5M = "stats.resp.time_avg_5m"
    RESP_TIME_AVG_15M = "stats.resp.time_avg_15m"

    @classmethod
    def defaults(cls):
        return [
            cls.ID.value,
            cls.METHOD.value,
            cls.PATH.value,
            cls.REQ_ACTIVE_COUNT.value,
            cls.REQ_TOTAL_COUNT.value,
        ]

    @classmethod
    def helps(cls) -> dict[str, str]:
        return {
            cls.ID: "Internal identifier",
            cls.HANDLER: "Route handler",
            cls.NAME: "Route name",
            cls.METHOD: "Route HTTP method",
            cls.PATH: "Route path",
            cls.REQ_ACTIVE_COUNT: "Number of active requests",
            cls.REQ_TOTAL_COUNT: "Total number of requests",
            cls.RESP_TIME_AVG_1M: "Average response time over last 1 min",
            cls.RESP_TIME_AVG_5M: "Average response time over last 5 min",
            cls.RESP_TIME_AVG_15M: "Average response time over last 15 min",
        }

    @classmethod
    def make_dict(
        cls, route: web.AbstractRoute, stats: RouteStats
    ) -> dict[str, Any]:

        handler = f"{route.handler.__module__}.{route.handler.__name__}"
        info = route.get_info()
        path = info.get("path") or info.get("formatter", "<unknown>")

        return dict(
            zip(
                cls,
                (
                    id(route),
                    handler,
                    route.name or "",
                    route.method,
                    path,
                    stats.counter.active,
                    stats.counter.total,
                    *stats.time_avg.calculate(),
                ),
            )
        )


@dissect_request(RoutesColumn)
async def routes(
    request: web.Request,
    context: Context,
    *,
    ids: set[int] = set(),
    help: bool = False,
    format: Format = Format.TEXT,
    v: bool = False,
    s: list[tuple[StrEnum, Order]] = [],
    h: list[str] = RoutesColumn.defaults(),
    **_,
) -> web.Response:

    if help:
        text = tabulate(RoutesColumn.helps().items())
        return web.Response(text=text + "\n")

    table: list[dict[str, str | int | float]] = []

    for route in context.core_app.router.routes():
        route_id = id(route)

        if ids and route_id not in ids:
            continue

        row = RoutesColumn.make_dict(route, context.route_stats[route_id])
        table.append(row)

    for column, order in reversed(s):
        table.sort(
            key=SortKeyWithNanSupport(column),
            reverse=order == Order.DESC,
        )

    headers = tuple(
        chain.from_iterable(
            (column for column in RoutesColumn if fnmatch(column, pattern))
            for pattern in h
        )
    )
    rows = map(itemgetter(*headers), table)

    if format == Format.JSON:
        return web.json_response([dict(zip(headers, row)) for row in rows])

    elif format == Format.YAML:
        text = yaml.dump(
            [dict(zip(map(str, headers), row)) for row in rows],
            sort_keys=False,
        )
        content_type = "application/x-yaml"

    else:
        text = tabulate(
            rows,
            headers=headers if v else [],
            tablefmt="plain",
            floatfmt=".6f",
        )
        content_type = "text/plain"

    return web.Response(text=text + "\n", content_type=content_type)
