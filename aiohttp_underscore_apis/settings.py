from dataclasses import dataclass, field
from typing import Any


def _defaults() -> dict[str, Any]:
    return {
        "overrides": {
            "response": {
                "status": None,
                "reason": None,
            }
        },
    }


@dataclass(frozen=True)
class RouteSettings:
    transient: dict[str, Any] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=_defaults)
