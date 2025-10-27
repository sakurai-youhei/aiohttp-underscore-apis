from functools import partial

from aiohttp import web

from aiohttp_underscore_apis.apis._routes.handlers import (
    _routes,
    _routes_interrupt,
    _routes_settings,
    _set_route_settings,
)


def setup_routes(app: web.Application) -> None:
    routes = web.RouteTableDef()
    routes_get = partial(routes.get, allow_head=False)

    routes_get("")(_routes)
    routes_get("/")(_routes)
    routes_get("/{ids:[0-9]+(,[0-9]+)*}")(_routes)

    routes.post("/{ids:[0-9]+(,[0-9]+)*}/interrupt")(_routes_interrupt)

    routes_get("/settings")(_routes_settings)
    routes_get("/{ids:[0-9]+(,[0-9]+)*}/settings")(_routes_settings)

    routes.put("/{ids:[0-9]+(,[0-9]+)*}/settings")(_set_route_settings)

    app.add_routes(routes)
