"""The structured refusal envelope (spec §6.3) and protocol identifier bounds."""
from __future__ import annotations

import re
import secrets
from collections.abc import Mapping
from dataclasses import dataclass, field

CODES = frozenset({
    "unknown-command", "invalid-input", "permit-exceeded", "outcome-unknown",
    "unknown-cursor", "stale-cursor", "input-mismatch", "kernel-refused",
    "no-current-project", "unknown-project", "ambiguous-project",
})
INVOCATION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


@dataclass(frozen=True)
class Refusal:
    code: str
    message: str
    data: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.code not in CODES:
            raise ValueError(f"unknown refusal code {self.code!r}")


class Refused(Exception):
    """Carries the structured envelope and an optional invocation id."""

    def __init__(self, refusal: Refusal, invocation_id: str | None = None) -> None:
        self.refusal = refusal
        self.invocation_id = invocation_id
        super().__init__(f"{refusal.code}: {refusal.message}")


def envelope(refusal: Refusal) -> dict:
    """The one wire form of a refusal: exactly the spec §6.3 triple."""
    return {"code": refusal.code, "message": refusal.message, "data": dict(refusal.data)}


def mint_token() -> str:
    return secrets.token_hex(16)
