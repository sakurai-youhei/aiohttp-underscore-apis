from functools import partial
from textwrap import dedent

from aiohttp import web

from aiohttp_underscore_apis.apis._cat.handlers import routes as _cat_routes
from aiohttp_underscore_apis.apis._cat.handlers import tasks as _cat_tasks


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
                    /tasks
                    /tasks/{task_id}
                """
            )
        )

    routes_get("/routes")(_cat_routes)
    routes_get("/routes/")(_cat_routes)
    routes_get("/routes/{ids:[0-9]+(,[0-9]+)*}")(_cat_routes)

    routes_get("/tasks")(_cat_tasks)
    routes_get("/tasks/")(_cat_tasks)
    routes_get("/tasks/{ids:[0-9]+(,[0-9]+)*}")(_cat_tasks)

    app.add_routes(routes)
