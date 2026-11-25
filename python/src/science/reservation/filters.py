"""The grammar of read filters, checked before any record is enumerated."""
from __future__ import annotations

import re

from science.refusal import Refusal, Refused

__all__ = ["require_chain", "require_reference"]

_CHAIN = re.compile(r"[a-z][a-z0-9-]*")


def require_reference(field: str, value: str | None, prefixes: tuple[str, ...]) -> None:
    if value is not None and not any(value.startswith(prefix) and len(value) > len(prefix) for prefix in prefixes):
        raise Refused(Refusal("invalid-input", f"{field} {value!r} is not a {' or '.join(prefixes)} address",
                              {"field": field}))


def require_chain(value: str) -> None:
    if _CHAIN.fullmatch(value) is None:
        raise Refused(Refusal("invalid-input", f"chain {value!r} does not match [a-z][a-z0-9-]*", {"field": "chain"}))
