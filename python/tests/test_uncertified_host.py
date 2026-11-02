"""Unit tests for the opt-in uncertified-host capability gate."""

import pytest
from _pytest.outcomes import Skipped
from atoms.core.errors import CapabilityUnavailable
from nodes.core.errors import ExecutionError
from science.refusal import Refusal, Refused

import conftest
from uncertified_host import (
    UNCERTIFIED_HOST_VAR,
    capability_unavailable_from,
    uncertified_host,
)


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({UNCERTIFIED_HOST_VAR: "1"}, True),
        ({}, False),
        ({UNCERTIFIED_HOST_VAR: ""}, False),
        ({UNCERTIFIED_HOST_VAR: "0"}, False),
        ({UNCERTIFIED_HOST_VAR: "true"}, False),
        ({UNCERTIFIED_HOST_VAR: "yes"}, False),
    ],
)
def test_uncertified_host_requires_exact_one(env: dict[str, str], expected: bool) -> None:
    assert uncertified_host(env) is expected


def test_capability_unavailable_from_unwraps_direct_and_chained_cause() -> None:
    raw = CapabilityUnavailable("ext4 durability probe failed")
    assert capability_unavailable_from(raw) is raw

    wrapped_exec = ExecutionError(str(raw), index=None, applied=0)
    wrapped_exec.__cause__ = raw
    assert capability_unavailable_from(wrapped_exec) is raw

    wrapped_refused = Refused(Refusal("kernel-refused", str(raw), {"kind": "CapabilityUnavailable"}))
    wrapped_refused.__cause__ = raw
    assert capability_unavailable_from(wrapped_refused) is raw

    unrelated = RuntimeError("boom")
    unrelated.__cause__ = ValueError("other")
    assert capability_unavailable_from(unrelated) is None


def test_report_missing_capability_skips_only_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = CapabilityUnavailable("ext4 tuple unavailable")
    wrapped = ExecutionError(str(raw), index=None, applied=0)
    wrapped.__cause__ = raw

    monkeypatch.delenv(UNCERTIFIED_HOST_VAR, raising=False)
    conftest._report_missing_capability(raw)
    conftest._report_missing_capability(wrapped)

    monkeypatch.setenv(UNCERTIFIED_HOST_VAR, "0")
    conftest._report_missing_capability(raw)

    monkeypatch.setenv(UNCERTIFIED_HOST_VAR, "1")
    with pytest.raises(Skipped, match="certified tuple unavailable on this host: ext4 tuple unavailable"):
        conftest._report_missing_capability(raw)
    with pytest.raises(Skipped, match="certified tuple unavailable on this host: ext4 tuple unavailable"):
        conftest._report_missing_capability(wrapped)
