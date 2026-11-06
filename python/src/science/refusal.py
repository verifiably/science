"""The structured refusal envelope  and protocol identifier bounds."""
from __future__ import annotations

import re
import secrets
from collections.abc import Mapping
from dataclasses import dataclass, field

from beliefs.errors import ProjectNotResolvable
from beliefs.permit import PermitExceeded
from beliefs.session import KernelRefusalValue

CODES = frozenset({
    "unknown-command", "invalid-input", "permit-exceeded", "outcome-unknown",
    "unknown-cursor", "stale-cursor", "input-mismatch", "kernel-refused",
    "no-current-project", "unknown-project", "ambiguous-project",
    "no-epoch", "epoch-stale",
    "pin-unsourced", "world-mismatch", "adopt-conflict", "corpus-retired", "divergent-publication", "config-stale",
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
    """The one wire form of a refusal: exactly the  triple."""
    return {"code": refusal.code, "message": refusal.message, "data": dict(refusal.data)}


def mint_token() -> str:
    return secrets.token_hex(16)


def kernel_refusal(error: Exception, *, root: str | None = None) -> Refusal:
    """The one normalization path for every kernel refusal shape."""
    code = "kernel-refused"
    message = str(error)
    if isinstance(error, PermitExceeded):
        code = "permit-exceeded"
        data = {"requirement": str(error.requirement), "capability": str(error.capability)}
    elif isinstance(error, KernelRefusalValue):
        value = error.value
        data = {"kind": type(value).__name__, "reason": str(value.reason)}
        message = str(value.reason)
        # RunRefused carries the refusing error's message separately from its reason.
        detail = str(getattr(value, "detail", ""))
        if detail:
            data["detail"] = detail
            message = f"{message}: {detail}"
    else:
        data = {"kind": type(error).__name__}
        if isinstance(error, ProjectNotResolvable) and error.tips:
            data["tips"] = list(error.tips)
    if root is not None:
        data["root"] = root
        message = f"{root}: {message}"
    return Refusal(code, message, data)
