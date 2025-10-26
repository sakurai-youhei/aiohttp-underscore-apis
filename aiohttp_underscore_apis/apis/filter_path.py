from collections import deque
from contextlib import suppress
from functools import singledispatch
from re import compile as re_compile
from typing import Any, Callable, Type, TypeVar


class _UnnecessaryPath(Exception):
    pass


@singledispatch
def _filter_path(value: Any, *matchers: Callable, path: str = "") -> Any:
    if not matchers:
        return value

    elif any(matcher(path) for matcher in matchers):
        return value

    raise _UnnecessaryPath()


@_filter_path.register
def _(lst: list, *matchers: Callable, path: str = "") -> list:
    filtered: deque[Any] = deque()

    for item in lst:
        with suppress(_UnnecessaryPath):
            filtered.append(_filter_path(item, *matchers, path=path))

    if not filtered:
        raise _UnnecessaryPath()

    return list(filtered)


@_filter_path.register
def _(dct: dict, *matchers: Callable, path: str = "") -> dict:
    filtered: dict[Any, Any] = {}

    for key in dct:
        with suppress(_UnnecessaryPath):
            filtered[key] = _filter_path(
                dct[key], *matchers, path=f"{path}.{key}" if path else key
            )

    if not filtered:
        raise _UnnecessaryPath()

    return filtered


def _make_matcher(filter_expression: str) -> Callable:
    """Translate an Elasticsearch filter expression into a regex matcher"""

    include = True if not filter_expression.startswith("-") else False

    keys = filter_expression.lstrip("+-").split(".")
    for i, key in enumerate(keys):
        if key:
            chars = key.split("**")
            keys[i] = ".*".join(c.replace("*", "[^.]*") for c in chars)
        else:
            keys[i] = ".*"

    pattern = re_compile("^" + r"\.".join(keys) + r"(?:\..+)?$")

    if include:
        return pattern.match
    else:
        return lambda s: not pattern.match(s)


T = TypeVar("T", dict, list)


def _make_instance(cls: Type[T]) -> T:
    """Create and return a new instance of T while satisfying type checkers"""

    return cls()


def filter_path(dict_or_list: T, *filter_expressions: str) -> T:
    """Filter a dict or a list according to the given filter expressions

    >>> filter_path(
    ...     {"foo": {"bar": 1, "baz": 2}, "qux": [10, 20, 30]},
    ...     "*.ba*",
    ... )
    {'foo': {'bar': 1, 'baz': 2}}

    The behavior of this filter_path is best-effort emulation of the behavior
    of Elasticsearch's filter_path, which can be referenced at the following
    URL.

    https://www.elastic.co/docs/reference/elasticsearch/rest-apis/common-options#common-options-response-filtering

    If you observe behavior that differs from the original, please report an
    issue with some examples.

    It always returns a new instance even if no filtering was applied. Raises
    TypeError if the given value is neither a dict nor a list.
    """

    if not isinstance(dict_or_list, (dict, list)):
        raise TypeError("Only dict and list are supported")

    inclusive_matchers = [
        _make_matcher(f) for f in filter_expressions if not f.startswith("-")
    ]
    exclusive_matchers = [
        _make_matcher(f) for f in filter_expressions if f.startswith("-")
    ]

    try:
        # The exclusive matchers shall be applied first and the result shall be
        # filtered again using the inclusive matchers.
        if exclusive_matchers:
            dict_or_list = _filter_path(dict_or_list, *exclusive_matchers)

        return _filter_path(dict_or_list, *inclusive_matchers)
    except _UnnecessaryPath:
        return _make_instance(type(dict_or_list))
