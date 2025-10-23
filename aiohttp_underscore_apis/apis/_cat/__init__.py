from textwrap import dedent

from aiohttp import web

from aiohttp_underscore_apis.apis._cat.handlers import routes as _routes


def setup_routes(app: web.Application) -> None:
    routes = web.RouteTableDef()

    @routes.get("", allow_head=False)
    @routes.get("/", allow_head=False)
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

    routes.get("/routes", allow_head=False)(_routes)
    routes.get("/routes/", allow_head=False)(_routes)
    routes.get("/routes/{ids:[0-9]+(,[0-9]+)*}", allow_head=False)(_routes)

    app.add_routes(routes)
