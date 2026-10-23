"""Helpers for the commons (sharing) tests."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from science.refusal import Refusal, Refused
from test_config import write_config


def _toml(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{key} = {_toml(item)}" for key, item in value.items()) + " }"
    return '"' + str(value) + '"'


def write_minimal_config(work: Path, **overrides: object) -> Path:
    """A loadable configuration under `work`; each override (`accept`, `fetch`,
    `sharing_root`) becomes a top-level key."""
    extra = "".join(f"{key} = {_toml(value)}\n" for key, value in overrides.items())
    return write_config(work, extra=extra)


def refused(call: Callable[[], object]) -> Refusal:
    with pytest.raises(Refused) as caught:
        call()
    return caught.value.refusal
