from aiohttp import web

from aiohttp_underscore_apis.apis._routes.handlers import (
    _routes,
    _routes_cancel_tasks,
)


def setup_routes(app: web.Application) -> None:
    routes = web.RouteTableDef()

    routes.get("", allow_head=False)(_routes)
    routes.get("/", allow_head=False)(_routes)
    routes.get("/{ids:[0-9]+(,[0-9]+)*}", allow_head=False)(_routes)

    routes.post("/{ids:[0-9]+(,[0-9]+)*}/_cancel_tasks")(_routes_cancel_tasks)

    app.add_routes(routes)
