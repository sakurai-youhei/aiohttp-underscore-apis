from typing import Callable, TypeAlias

from aiohttp import web

SiteFactory: TypeAlias = Callable[[web.BaseRunner], web.BaseSite]
