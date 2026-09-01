"""Launcher configuration loaded directly into beliefs' WorldConfig."""
from __future__ import annotations

import os
import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from beliefs.corpus import ReadView
from beliefs.root import open_world
from beliefs.world import WorldConfig
from beliefs.world.registry import load_manifest

from science.refusal import Refusal, Refused

_WORLD_ID_RE = re.compile(r"[0-9a-f]{32}")
_KEYS = ("world_root", "world_id", "corpus_roots", "operations_root")


@dataclass(frozen=True)
class ScienceConfig:
    world: WorldConfig
    operations_root: Path


def _refuse(message: str) -> None:
    raise Refused(Refusal("invalid-input", message))


def load_config(path: Path) -> ScienceConfig:
    if not path.is_file():
        _refuse(f"config file not found: {path}")
    try:
        with path.open("rb") as config_file:
            raw = tomllib.load(config_file)
    except (OSError, tomllib.TOMLDecodeError):
        _refuse("config is not valid TOML")
    if type(raw) is not dict:
        _refuse("config must be a table")
    if set(raw) != set(_KEYS):
        _refuse("config must contain exactly the required keys")
    if any(type(raw[key]) is not str for key in ("world_root", "world_id", "operations_root")):
        _refuse("config paths and world_id must be strings")
    if type(raw["corpus_roots"]) is not list or any(
        type(value) is not str for value in raw["corpus_roots"]
    ):
        _refuse("config corpus_roots must be a list of strings")
    if not _WORLD_ID_RE.fullmatch(raw["world_id"]):
        _refuse("config world_id must be 32 lowercase hex characters")
    return ScienceConfig(
        world=WorldConfig(
            world_root=Path(raw["world_root"]),
            world_id=raw["world_id"],
            corpus_roots=tuple(Path(value) for value in raw["corpus_roots"]),
        ),
        operations_root=Path(raw["operations_root"]).resolve(),
    )


def resolve_config_path(cli_value: str | None, env: Mapping[str, str] | None = None) -> Path:
    env = os.environ if env is None else env
    if cli_value:
        return Path(cli_value)
    if "SCIENCE_CONFIG" in env:
        return Path(env["SCIENCE_CONFIG"])
    _refuse("no --config and no SCIENCE_CONFIG")
    raise AssertionError


@dataclass(frozen=True)
class ReadContext:
    world: object
    config: ScienceConfig

    @classmethod
    def open(cls, config: ScienceConfig) -> ReadContext:
        return cls(world=open_world(config.world), config=config)

    def read_views(self) -> tuple[tuple[str, ReadView], ...]:
        pairs = []
        for root in self.config.world.corpus_roots:
            pairs.append((load_manifest(root).corpus_id, ReadView.opened_at(root)))
        return tuple(sorted(pairs))

    def load_record(self, uid: str, record_id: str):
        for _, read_view in self.read_views():
            if read_view.holds(record_id):
                node = read_view.get(record_id)
                if node.uid == uid:
                    return node
        raise Refused(Refusal("unknown-cursor", f"record {record_id!r} not found"))
