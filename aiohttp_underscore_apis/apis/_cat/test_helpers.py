from enum import StrEnum
from unittest import IsolatedAsyncioTestCase

from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from aiohttp_underscore_apis.apis._cat.helpers import dissect_request
from aiohttp_underscore_apis.apis._cat.options import Order
from aiohttp_underscore_apis.apis.common import Format
from aiohttp_underscore_apis.context import Context


class Column(StrEnum):
    APPLE = "apple"
    BANANA = "banana"
    CHERRY = "cherry"


class HandlerDecoratingTest(IsolatedAsyncioTestCase):
    async def test_dissect_request(self):

        mocked_request = make_mocked_request(
            method="GET",
            path="/test/12,34?v&s=cherry:desc&h=app*,*na&format=json",
            match_info={"ids": "12,34"},
        )
        Context(mocked_request.app).set_to(mocked_request.app)

        @dissect_request(Column)
        async def handler(
            request: web.Request,
            context: Context,
            *,
            ids: set[int] = set(),
            help: bool = False,
            format: Format = Format.TEXT,
            v: bool = False,
            s: list[tuple[StrEnum, Order]] = [],
            h: list[str] = ["apple", "banana"],
            **_,
        ) -> web.Response:

            self.assertIs(request, mocked_request)
            self.assertIs(context, Context.get_from(mocked_request.app))
            self.assertEqual(ids, {12, 34})
            self.assertFalse(help)
            self.assertEqual(format, Format.JSON)
            self.assertTrue(v)
            self.assertEqual(s, [(Column.CHERRY, Order.DESC)])
            self.assertEqual(h, ["app*", "*na"])
            return web.Response(text="OK")

        resp = await handler(mocked_request)
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.text, "OK")
