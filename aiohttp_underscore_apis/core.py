import asyncio
from dataclasses import dataclass, field
from typing import ClassVar

from aiohttp import web
from aiohttp.typedefs import Middleware

from aiohttp_underscore_apis.apis import _cat, _routes
from aiohttp_underscore_apis.context import Context
from aiohttp_underscore_apis.middlewares import request_inspector
from aiohttp_underscore_apis.types import SiteFactory


@dataclass(frozen=True)
class AiohttpUnderscoreApis:
    _apis: ClassVar[list] = [_cat, _routes]

    site_factories: list[SiteFactory] = field(default_factory=list)

    def init_subapps(
        self, core_app: web.Application
    ) -> dict[str, web.Application]:

        ctx = Context(core_app=core_app)
        ctx.set_to(core_app)

        subapps: dict[str, web.Application] = {}
        for mod in type(self)._apis:
            *_, name = mod.__name__.rsplit(".", 1)

            app = subapps[name] = web.Application()
            ctx.set_to(app)

            mod.setup_routes(app)

        return subapps

    async def listener(self, main_app: web.Application):
        app = web.Application()
        for name, subapp in self.init_subapps(main_app).items():
            app.add_subapp(f"/{name}", subapp)

        runner = web.AppRunner(app, handle_signals=True)
        await runner.setup()

        sites = [site(runner) for site in self.site_factories]
        await asyncio.gather(*[site.start() for site in sites])
        yield
        await asyncio.gather(*[site.stop() for site in sites])

    @property
    def middlewares(self) -> tuple[Middleware, ...]:
        return (request_inspector,)
