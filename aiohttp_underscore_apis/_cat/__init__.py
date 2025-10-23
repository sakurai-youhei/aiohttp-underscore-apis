from enum import StrEnum
from fnmatch import fnmatch
from itertools import chain
from operator import itemgetter
from time import perf_counter

from aiohttp import web
from tabulate import tabulate

from aiohttp_underscore_apis._cat.options import Order, use_common_options
from aiohttp_underscore_apis.context import Context


@web.middleware
async def request_inspector(request: web.Request, handler):
    ctx = Context.get_from(request.app)
    route = request.match_info.route
    route_stats = ctx.route_stats[id(route)]

    route_stats.counter.active += 1
    route_stats.counter.total += 1

    start = perf_counter()
    try:
        return await handler(request)
    finally:
        duration = perf_counter() - start
        route_stats.time_avg.record(duration)
        route_stats.counter.active -= 1


__middlewares__ = [request_inspector]
__route_table__ = web.RouteTableDef()


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
            cls.METHOD.value,
            cls.PATH.value,
            cls.REQ_ACTIVE_COUNT.value,
            cls.REQ_TOTAL_COUNT.value,
        ]


@__route_table__.get("/routes", allow_head=False)
@__route_table__.get("/routes/", allow_head=False)
@__route_table__.get("/routes/{ids:[0-9]+(,[0-9]+)*}", allow_head=False)
@use_common_options(RoutesColumn)
async def routes(
    request: web.Request,
    context: Context,
    *,
    ids: set[int] = set(),
    v: bool = False,
    s: list[tuple[StrEnum, Order]] = [],
    h: list[str] = RoutesColumn.defaults(),
    **_,
) -> web.Response:

    resources = context.core_app.router.resources()
    route_stats = context.route_stats

    table: list[dict[str, str | int | float]] = []

    for resource in resources:
        for route in resource:
            route_id = id(route)

            if ids and route_id not in ids:
                continue

            stats = route_stats[route_id]
            avg_1m, avg_5m, avg_15m = stats.time_avg.calculate()

            table.append(
                {
                    "id": route_id,
                    "name": route.name or "",
                    "method": route.method,
                    "path": resource.canonical,
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

    text = tabulate(
        map(itemgetter(*headers), table),
        headers=headers if v else [],
        tablefmt="plain",
        floatfmt=".6f",
    )
    return web.Response(text=text + "\n")
