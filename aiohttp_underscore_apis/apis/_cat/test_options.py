from enum import StrEnum
from unittest import TestCase

from webargs import ValidationError

from aiohttp_underscore_apis.apis._cat.options import (
    ColumnOrder,
    FnmatchAnyNames,
    Header,
    Sort,
)


class Column(StrEnum):
    APPLE = "apple"
    BANANA = "banana"
    CHERRY = "cherry"


class FieldsTest(TestCase):
    def test_ColumnOrder(self):
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

    def test_Sort(self):
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

    def test_FnmatchAnyNames(self):
        validator = FnmatchAnyNames("foo", "bar", "barista", "bazXqux")

        for matching_pattern in ("foo", "bar*", "b*ta", "baz?qux"):
            self.assertEqual(validator(matching_pattern), matching_pattern)

        for non_matching_pattern in ("", "fool", "ba", "b?ta", "bazqux", "qu"):
            with self.assertRaises(ValidationError):
                validator(non_matching_pattern)

    def test_Header(self):
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
