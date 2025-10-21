from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial

from aiohttp import web

from aiohttp_underscore_apis.stats import RouteStats

APP_CONTEXT_KEY = "_aiohttp_underscore_apis_context_"


@dataclass(frozen=True)
class Context:
    core_app: web.Application
    route_stats: dict[int, RouteStats] = field(
        default_factory=partial(defaultdict, RouteStats)
    )

    def set_to(self, app: web.Application) -> None:
        app[APP_CONTEXT_KEY] = self

    @staticmethod
    def get_from(app: web.Application) -> "Context":
        return app[APP_CONTEXT_KEY]
