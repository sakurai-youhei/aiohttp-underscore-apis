from functools import partial
from textwrap import dedent

from aiohttp import web

from aiohttp_underscore_apis.apis._cat.handlers import routes as _routes


def setup_routes(app: web.Application) -> None:
    routes = web.RouteTableDef()
    routes_get = partial(routes.get, allow_head=False)

    @routes_get("")
    @routes_get("/")
    async def _(request: web.Request) -> web.Response:
        return web.Response(
            text=dedent(
                """\
                    =^.^=
                    /routes
                    /routes/{route_id}
                """
            )
        )

    routes_get("/routes")(_routes)
    routes_get("/routes/")(_routes)
    routes_get("/routes/{ids:[0-9]+(,[0-9]+)*}")(_routes)

    app.add_routes(routes)
