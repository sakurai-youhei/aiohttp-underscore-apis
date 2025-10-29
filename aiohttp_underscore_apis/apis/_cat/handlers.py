from asyncio import all_tasks

from aiohttp_underscore_apis.apis._cat.base import CatBase
from aiohttp_underscore_apis.context import Context


class CatRoutes(CatBase):
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
    def helps(cls):
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
    def iter_rows(cls, context: Context):

        for route in context.core_app.router.routes():

            route_id = id(route)
            handler = f"{route.handler.__module__}.{route.handler.__name__}"
            info = route.get_info()
            path = info.get("path") or info.get("formatter", "<unknown>")
            stats = context.route_stats[route_id]

            yield dict(
                zip(
                    cls,
                    (
                        route_id,
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


class CatTasks(CatBase):
    ID = "id"
    NAME = "name"
    CORO = "coro"
    DONE = "done"
    CANCELLED = "cancelled"
    CANCELLING = "cancelling"
    ROUTE_ID = "route_id"

    @classmethod
    def defaults(cls):
        return [*cls]

    @classmethod
    def helps(cls):
        return {
            cls.ID: "Internal identifier",
            cls.NAME: "Task name",
            cls.CORO: "Coroutine object wrapped by task",
            cls.DONE: "Whether or not task is done",
            cls.CANCELLED: "Number of pending cancellation requests",
            cls.CANCELLING: "Whether or not task is cancelling",
            cls.ROUTE_ID: "Route ID associated with the task",
        }

    @classmethod
    def iter_rows(cls, context: Context):

        id_map = {
            id(task): route_id
            for route_id, tasks in context.task_refs.items()
            for task in tasks
        }

        for task in all_tasks(context.core_app.loop):
            coro = task.get_coro()

            yield dict(
                zip(
                    cls,
                    (
                        id(task),
                        task.get_name(),
                        coro and coro.__qualname__,
                        task.done(),
                        task.cancelled(),
                        task.cancelling(),
                        id_map.get(id(task), -1),
                    ),
                )
            )


routes = CatRoutes.handler()
tasks = CatTasks.handler()
__all__ = ["routes", "tasks"]
