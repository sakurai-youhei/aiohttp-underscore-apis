import json
from unittest import IsolatedAsyncioTestCase

from aiohttp.test_utils import make_mocked_request

from aiohttp_underscore_apis.apis._cat.base import CatBase
from aiohttp_underscore_apis.context import Context


class CatNone(CatBase):
    ID = "id"
    APPLE = "apple"
    BANANA = "banana"
    CHERRY = "cherry"

    @classmethod
    def defaults(cls):
        return [
            cls.ID.value,
        ]

    @classmethod
    def helps(cls):
        return {
            cls.ID: "Internal identifier",
            cls.APPLE: "Number of apples",
            cls.BANANA: "Number of bananas",
            cls.CHERRY: "Number of cherries",
        }

    @classmethod
    def iter_rows(cls, context: Context):
        assert context is not None
        assert isinstance(context, Context)
        yield {
            CatNone.ID: 1,
            CatNone.APPLE: 10,
            CatNone.BANANA: 20,
            CatNone.CHERRY: 30,
        }


class CatBaseTest(IsolatedAsyncioTestCase):
    async def test_dissect_request(self):

        mocked_request = make_mocked_request(
            method="GET",
            path="_cat/none/1,2?v&s=cherry:desc&h=app*,*na&format=json",
            match_info={"ids": "1,2"},
        )
        Context(mocked_request.app).set_to(mocked_request.app)

        resp = await CatNone.handler()(mocked_request)
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.content_type, "application/json")
        assert resp.text
        self.assertSequenceEqual(
            json.loads(resp.text), [{"apple": 10, "banana": 20}]
        )
