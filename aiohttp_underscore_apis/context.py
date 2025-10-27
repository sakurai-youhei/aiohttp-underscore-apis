from asyncio import Task
from collections import defaultdict
from collections.abc import Awaitable
from dataclasses import dataclass, field
from functools import partial, wraps
from typing import Callable, Concatenate, DefaultDict, ParamSpec
from weakref import WeakSet

from aiohttp import web

from aiohttp_underscore_apis.settings import RouteSettings
from aiohttp_underscore_apis.stats import RouteStats

APP_CONTEXT_KEY = "_aiohttp_underscore_apis_context_"
P = ParamSpec("P")


@dataclass(frozen=True)
class Context:
    core_app: web.Application
    route_stats: DefaultDict[int, RouteStats] = field(
        default_factory=partial(defaultdict, RouteStats)
    )
    route_settings: DefaultDict[int, RouteSettings] = field(
        default_factory=partial(defaultdict, RouteSettings)
    )
    task_refs: DefaultDict[int, WeakSet[Task]] = field(
        default_factory=partial(defaultdict, WeakSet)
    )

    def set_to(self, app: web.Application) -> None:
        app[APP_CONTEXT_KEY] = self

    @staticmethod
    def get_from(app: web.Application) -> "Context":
        return app[APP_CONTEXT_KEY]

    @classmethod
    def use(
        cls,
        handler: Callable[
            Concatenate[web.Request, "Context", P], Awaitable[web.Response]
        ],
    ) -> Callable[Concatenate[web.Request, P], Awaitable[web.Response]]:

        @wraps(handler)
        async def wrapper(req: web.Request, *args: P.args, **kwargs: P.kwargs):

            return await handler(req, cls.get_from(req.app), *args, **kwargs)

        return wrapper
