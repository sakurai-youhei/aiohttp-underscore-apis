import json
from functools import partial
from typing import Any, NotRequired, TypedDict

import yaml
from aiohttp import web
from webargs import fields
from webargs.aiohttpparser import use_kwargs

from aiohttp_underscore_apis.apis.common import Format, dissect_request
from aiohttp_underscore_apis.apis.filter_path import (
    filter_path as _filter_path,
)
from aiohttp_underscore_apis.context import Context


def _response(
    data: Any, filter_path: list[str], format: Format, pretty: bool
) -> web.Response:
    print(data)
    data = _filter_path(data, *filter_path)
    print(data)

    if format == Format.YAML:
        return web.Response(
            text=yaml.dump(data, sort_keys=False),
            content_type="application/x-yaml",
        )

    return web.json_response(
        data, dumps=partial(json.dumps, indent=4 if pretty else None)
    )


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

    return _response(routes, filter_path, format, pretty)


@dissect_request
async def _routes_cancel_tasks(
    request: web.Request,
    context: Context,
    *,
    ids: set[int] = set(),
    **_: Any,
) -> web.Response:

    for route_id in ids:
        for task in context.task_refs[route_id]:
            task.cancel()

    return web.Response(status=204)


class _Settings(TypedDict):
    transient: dict[str, Any]
    defaults: NotRequired[dict[str, Any]]


class IncludeDefaults(fields.Boolean):
    truthy = {"", *fields.Boolean.truthy}


@dissect_request
@use_kwargs({"include_defaults": IncludeDefaults()}, location="querystring")
async def _routes_settings(
    request: web.Request,
    context: Context,
    *,
    ids: set[int] = set(),
    format: Format = Format.JSON,
    pretty: bool = False,
    filter_path: list[str] = [],
    include_defaults: bool = False,
    **_: Any,
) -> web.Response:

    settings: dict[int, _Settings] = {}
    for route in context.core_app.router.routes():
        route_id = id(route)
        if ids and route_id not in ids:
            continue

        route_settings = context.route_settings[route_id]

        settings[route_id] = {"transient": route_settings.transient}

        if include_defaults:
            settings[route_id]["defaults"] = route_settings.defaults

    print(settings, filter_path, format, pretty)
    return _response(settings, filter_path, format, pretty)
