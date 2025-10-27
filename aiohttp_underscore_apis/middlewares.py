from collections import ChainMap
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


@web.middleware
async def request_interceptor(request: web.Request, handler):
    ctx = Context.get_from(request.app)
    route = request.match_info.route
    route_settings = ctx.route_settings[id(route)]

    preempt = ChainMap(
        route_settings.transient.get("preempt", {}),
        route_settings.defaults["preempt"],
    )

    if preempt["status"] is not None:
        return web.Response(status=preempt["status"], reason=preempt["reason"])

    return await handler(request)


@web.middleware
async def task_tracker(request: web.Request, handler):
    ctx = Context.get_from(request.app)
    route = request.match_info.route
    task_refs = ctx.task_refs[id(route)]

    if request.task is not None:
        task_refs.add(request.task)
    try:
        return await handler(request)
    finally:
        if request.task is not None:
            task_refs.discard(request.task)
