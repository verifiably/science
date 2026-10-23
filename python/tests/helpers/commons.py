"""Helpers for the commons (sharing) tests."""
from __future__ import annotations

import os
import subprocess
import tempfile
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


# Built key by key: a git hook's exported GIT_DIR / GIT_INDEX_FILE / GIT_WORK_TREE never reach a fixture's git,
# and the host's real git configuration is never read.
GIT_ENV = {
    "PATH": os.environ["PATH"],
    "HOME": tempfile.mkdtemp(prefix="science-git-home-"),
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@science.invalid",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@science.invalid",
}


def commit_count(bare: Path) -> int:
    """Commits on `main` of a bare repository; 0 while the branch is unborn."""
    probe = subprocess.run(["git", "-C", str(bare), "rev-parse", "--verify", "--quiet", "refs/heads/main"],
                           env=GIT_ENV, capture_output=True)
    if probe.returncode != 0:
        return 0
    count = subprocess.run(["git", "-C", str(bare), "rev-list", "--count", "main"],
                           env=GIT_ENV, capture_output=True, text=True, check=True)
    return int(count.stdout)


class Remotes:
    """Local bare repositories standing in for `https://remote.test/<name>` locators."""

    def __init__(self, base: Path) -> None:
        self.base = Path(base)

    def bare(self, name: str) -> Path:
        path = self.base / f"{name}.git"
        if not path.exists():
            subprocess.run(["git", "init", "--bare", "-b", "main", str(path)], env=GIT_ENV,
                           capture_output=True, check=True)
        return path

    def remote_for(self, destination) -> str:
        prefix = "https://remote.test/"
        assert destination.locator.startswith(prefix), destination.locator
        return str(self.bare(destination.locator[len(prefix):]))
