from unittest import IsolatedAsyncioTestCase, TestCase

from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from webargs import ValidationError

from aiohttp_underscore_apis.apis.common import Format, Ids, dissect_request
from aiohttp_underscore_apis.context import Context


class FieldsTest(TestCase):
    def test_Ids(self):
        for value, expected in (
            ("", set()),
            ("1", {1}),
            ("01", {1}),
            ("1,2,3", {1, 2, 3}),
            ("42,7,13", {42, 7, 13}),
        ):
            self.assertEqual(Ids().deserialize(value), expected)

        for invalid_value in ("F", ",", "foo", "1,2,foo", "1,", ",2", "1,,2"):
            with self.assertRaises(ValidationError):
                Ids().deserialize(invalid_value)


class HandlerDecoratingTest(IsolatedAsyncioTestCase):
    async def test_dissect_request(self):

        mocked_request = make_mocked_request(
            method="GET",
            path="/_routes/12,34?foo=true&format=yaml",
            match_info={"ids": "12,34"},
        )
        Context(mocked_request.app).set_to(mocked_request.app)

        @dissect_request
        async def handler(
            request: web.Request,
            context: Context,
            *,
            ids: set[int] = set(),
            format: Format = Format.JSON,
            **_,
        ) -> web.Response:

            self.assertIs(request, mocked_request)
            self.assertIs(context, Context.get_from(mocked_request.app))
            self.assertEqual(ids, {12, 34})
            self.assertEqual(format, Format.YAML)
            return web.Response(text="OK")

        resp = await handler(mocked_request)
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.text, "OK")
