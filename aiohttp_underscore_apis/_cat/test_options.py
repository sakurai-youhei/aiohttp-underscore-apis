from enum import StrEnum
from unittest import IsolatedAsyncioTestCase, TestCase

from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from webargs import ValidationError

from aiohttp_underscore_apis._cat.options import (
    ColumnOrder,
    FnmatchAnyNames,
    Header,
    Ids,
    Order,
    Sort,
    use_common_options,
)
from aiohttp_underscore_apis.context import Context


class IdsTest(TestCase):
    def test_deserialize(self):
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


class Column(StrEnum):
    APPLE = "apple"
    BANANA = "banana"
    CHERRY = "cherry"


class ColumnOrderTest(TestCase):
    def test_deserialize(self):
        for value, expected in (
            ("apple", (Column.APPLE, "asc")),
            ("banana:asc", (Column.BANANA, "asc")),
            ("cherry:desc", (Column.CHERRY, "desc")),
        ):
            self.assertSequenceEqual(
                ColumnOrder(Column).deserialize(value),
                expected,
            )

        for invalid_value in ("", "APPLE", "apple:up", "cherry:apple"):
            with self.assertRaises(ValidationError):
                ColumnOrder(Column).deserialize(invalid_value)


class SortTest(TestCase):
    def test_deserialize(self):
        for value, expected in (
            ("", tuple()),
            ("apple,banana", ((Column.APPLE, "asc"), (Column.BANANA, "asc"))),
            ("apple,apple", ((Column.APPLE, "asc"), (Column.APPLE, "asc"))),
            (
                "banana:asc,cherry:desc",
                ((Column.BANANA, "asc"), (Column.CHERRY, "desc")),
            ),
        ):
            self.assertSequenceEqual(
                Sort(Column).deserialize(value),
                expected,
            )

        for invalid_value in (",", ",apple", "apple,", "apple,,banana"):
            with self.assertRaises(ValidationError):
                Sort(Column).deserialize(invalid_value)


class FnmatchAnyNamesTest(TestCase):
    def test_deserialize(self):
        validator = FnmatchAnyNames("foo", "bar", "barista", "bazXqux")

        for matching_pattern in ("foo", "bar*", "b*ta", "baz?qux"):
            self.assertEqual(validator(matching_pattern), matching_pattern)

        for non_matching_pattern in ("", "fool", "ba", "b?ta", "bazqux", "qu"):
            with self.assertRaises(ValidationError):
                validator(non_matching_pattern)


class HeaderTest(TestCase):
    def test_deserialize(self):
        for value, expected in (
            ("a*,b*", ["a*", "b*"]),
            ("banana", ["banana"]),
            ("", []),
            ("*", ["*"]),
            ("*e*", ["*e*"]),
        ):
            self.assertListEqual(Header(Column).deserialize(value), expected)

        for invalid_value in ("APPLE", "apple,foo", "ba*,", ",*rry", "a*,,c*"):
            with self.assertRaises(ValidationError):
                Header(Column).deserialize(invalid_value)


class UseCommonOptionsTest(IsolatedAsyncioTestCase):
    async def test_handler(self):

        req = make_mocked_request(
            method="GET",
            path="/test/12,34?v&s=cherry:desc&h=app*,*na",
            match_info={"ids": "12,34"},
        )
        Context(req.app).set_to(req.app)

        @use_common_options(Column)
        async def handler(
            request: web.Request,
            context: Context,
            *,
            ids: set[int] = set(),
            v: bool = False,
            s: list[tuple[StrEnum, Order]] = [],
            h: list[str] = ["apple", "banana"],
            **_,
        ) -> web.Response:

            self.assertIs(request, req)
            self.assertIs(context, Context.get_from(req.app))
            self.assertEqual(ids, {12, 34})
            self.assertTrue(v)
            self.assertEqual(s, [(Column.CHERRY, Order.DESC)])
            self.assertEqual(h, ["app*", "*na"])
            return web.Response(text="OK")

        resp = await handler(req)
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.text, "OK")
