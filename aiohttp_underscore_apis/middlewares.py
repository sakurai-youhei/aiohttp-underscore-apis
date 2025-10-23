from time import perf_counter

from aiohttp import web

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
