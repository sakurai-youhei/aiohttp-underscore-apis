from enum import StrEnum
from fnmatch import fnmatch
from itertools import chain
from operator import itemgetter

from aiohttp import web
from tabulate import tabulate

from aiohttp_underscore_apis.apis._cat.options import (
    Format,
    Order,
    use_common_options,
)
from aiohttp_underscore_apis.context import Context


class RoutesColumn(StrEnum):
    ID = "id"
    NAME = "name"
    METHOD = "method"
    PATH = "path"
    REQ_ACTIVE_COUNT = "req.active.count"
    REQ_TOTAL_COUNT = "req.total.count"
    RESP_TIME_AVG_1M = "resp.time_sec.avg_1m"
    RESP_TIME_AVG_5M = "resp.time_sec.avg_5m"
    RESP_TIME_AVG_15M = "resp.time_sec.avg_15m"

    @classmethod
    def defaults(cls):
        return [
            cls.ID.value,
            cls.NAME.value,
            cls.METHOD.value,
            cls.PATH.value,
            cls.REQ_ACTIVE_COUNT.value,
            cls.REQ_TOTAL_COUNT.value,
        ]

    @classmethod
    def helps(cls) -> dict[str, str]:
        return {
            cls.ID: "Internal identifier",
            cls.NAME: "Route name",
            cls.METHOD: "Route HTTP method",
            cls.PATH: "Route path",
            cls.REQ_ACTIVE_COUNT: "Number of active requests",
            cls.REQ_TOTAL_COUNT: "Total number of requests",
            cls.RESP_TIME_AVG_1M: "Average response time over last 1 min",
            cls.RESP_TIME_AVG_5M: "Average response time over last 5 min",
            cls.RESP_TIME_AVG_15M: "Average response time over last 15 min",
        }


@use_common_options(RoutesColumn)
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

    resources = context.core_app.router.resources()
    route_stats = context.route_stats

    table: list[dict[str, str | int | float]] = []

    for route in chain.from_iterable(resources):
        route_id = id(route)

        if ids and route_id not in ids:
            continue

        stats = route_stats[route_id]
        avg_1m, avg_5m, avg_15m = stats.time_avg.calculate()

        info = route.get_info()
        path = info.get("path") or info.get("formatter", "<unknown>")
        table.append(
            {
                "id": route_id,
                "name": route.name or "",
                "method": route.method,
                "path": path,
                "req.active.count": stats.counter.active,
                "req.total.count": stats.counter.total,
                "resp.time_sec.avg_1m": avg_1m,
                "resp.time_sec.avg_5m": avg_5m,
                "resp.time_sec.avg_15m": avg_15m,
            }
        )

    for column, order in reversed(s):
        reverse = order == Order.DESC
        table.sort(key=itemgetter(column), reverse=reverse)

    headers = tuple(
        chain.from_iterable(
            (column for column in RoutesColumn if fnmatch(column, pattern))
            for pattern in h
        )
    )
    rows = map(itemgetter(*headers), table)

    if format == Format.JSON:
        return web.json_response([dict(zip(headers, row)) for row in rows])

    text = tabulate(
        rows, headers=headers if v else [], tablefmt="plain", floatfmt=".6f"
    )
    return web.Response(text=text + "\n")
