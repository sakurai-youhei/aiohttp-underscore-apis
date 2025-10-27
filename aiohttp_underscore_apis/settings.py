from dataclasses import dataclass, field
from typing import Any

from marshmallow import Schema, fields
from marshmallow.validate import Range


class PreemptSchema(Schema):
    status = fields.Integer(allow_none=True, validate=Range(min=100, max=599))
    reason = fields.String(allow_none=True)


class SettingsSchema(Schema):
    preempt = fields.Nested(PreemptSchema, required=False)


class RouteSettingsSchema(Schema):
    transient = fields.Nested(SettingsSchema, required=False)


def _defaults() -> dict[str, Any]:
    return {
        "preempt": {
            "status": None,
            "reason": None,
        },
    }


@dataclass(frozen=True)
class RouteSettings:
    transient: dict[str, Any] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=_defaults)
