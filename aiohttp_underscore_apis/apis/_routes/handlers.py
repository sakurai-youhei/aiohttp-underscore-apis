import json
from functools import partial
from typing import Any

import yaml
from aiohttp import web

from aiohttp_underscore_apis.apis.common import Format, dissect_request
from aiohttp_underscore_apis.apis.filter_path import (
    filter_path as _filter_path,
)
from aiohttp_underscore_apis.context import Context


@dissect_request
async def _routes(
    request: web.Request,
    context: Context,
    *,
    ids: set[int] = set(),
    format: Format = Format.JSON,
    pretty: bool = False,
    filter_path: list[str] = [],
    **_: Any,
) -> web.Response:

    routes: dict[int, dict[str, Any]] = {}
    for route in context.core_app.router.routes():
        route_id = id(route)
        if ids and route_id not in ids:
            continue

        handler = f"{route.handler.__module__}.{route.handler.__name__}"
        info = route.get_info()
        path = info.get("path") or info.get("formatter", "<unknown>")

        routes[route_id] = {
            "handler": handler,
            "name": route.name,
            "method": route.method,
            "path": path,
        }

    routes = _filter_path(routes, *filter_path)

    if format == Format.YAML:
        return web.Response(
            text=yaml.dump(routes, sort_keys=False),
            content_type="application/x-yaml",
        )

    return web.json_response(
        routes, dumps=partial(json.dumps, indent=4 if pretty else None)
    )
