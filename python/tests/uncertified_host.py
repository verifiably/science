"""Opt-in uncertified-host capability gate for hosted verification."""

from collections.abc import Mapping

from atoms.core.errors import CapabilityUnavailable

UNCERTIFIED_HOST_VAR = "VERIFIABLY_UNCERTIFIED_HOST"


def uncertified_host(environ: Mapping[str, str]) -> bool:
    return environ.get(UNCERTIFIED_HOST_VAR, "") == "1"


def capability_unavailable_from(error: BaseException) -> CapabilityUnavailable | None:
    if isinstance(error, CapabilityUnavailable):
        return error
    cause = error.__cause__
    if isinstance(cause, CapabilityUnavailable):
        return cause
    return None
