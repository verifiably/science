"""Launcher configuration loaded directly into beliefs' WorldConfig."""
from __future__ import annotations

import os
import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from beliefs.corpus import ReadView
from beliefs.errors import ProfileError
from beliefs.profile import ProfileSpec, compile_profile, shipped_base_contract, shipped_domain_contract
from beliefs.root import open_world_read
from beliefs.world import WorldConfig
from beliefs.world.registry import load_manifest

from science.refusal import Refusal, Refused
from science.contracts import OperatorPlan, load_contract_document

_WORLD_ID_RE = re.compile(r"[0-9a-f]{32}")
_KEYS = (
    "world_root", "world_id", "corpus_roots", "operations_root", "domains", "contracts",
    "store_root",
)
_OPTIONAL_KEYS = ("service_socket",)


@dataclass(frozen=True)
class ScienceConfig:
    world: WorldConfig
    operations_root: Path
    profile: ProfileSpec
    service_socket: Path
    store_root: Path
    plans: tuple[OperatorPlan, ...] = ()


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
    if set(raw) - set(_OPTIONAL_KEYS) != set(_KEYS):
        _refuse("config must contain exactly the required keys")
    if any(type(raw[key]) is not str for key in ("world_root", "world_id", "operations_root")):
        _refuse("config paths and world_id must be strings")
    if "service_socket" in raw and type(raw["service_socket"]) is not str:
        _refuse("config service_socket must be a string")
    if type(raw["corpus_roots"]) is not list or any(
        type(value) is not str for value in raw["corpus_roots"]
    ):
        _refuse("config corpus_roots must be a list of strings")
    if type(raw["domains"]) is not list or any(
        type(value) is not str for value in raw["domains"]
    ):
        _refuse("config domains must be a list of strings")
    if type(raw["contracts"]) is not list or any(type(value) is not str for value in raw["contracts"]):
        _refuse("config contracts must be a list of strings")
    if type(raw["store_root"]) is not str:
        _refuse("config store_root must be a string")
    if not _WORLD_ID_RE.fullmatch(raw["world_id"]):
        _refuse("config world_id must be 32 lowercase hex characters")
    try:
        domains = [shipped_domain_contract(namespace) for namespace in raw["domains"]]
    except ProfileError as caught:
        _refuse(f"config domains do not compile: {caught}")
    base = shipped_base_contract()
    local = [load_contract_document(Path(value).resolve(), base) for value in raw["contracts"]]
    try:
        profile = compile_profile(base, domains + [contract for contract, _ in local])
    except ProfileError as caught:
        _refuse(f"config contracts do not compile: {caught}")
    plans = tuple(plan for _, plan in local if plan is not None)
    operations_root = Path(raw["operations_root"]).resolve()
    # The socket defaults beside the operations root. AF_UNIX caps the path at
    # 107 bytes and a worktree checkout's operations root already exceeds it,
    # so the key exists to name a short path; both `science serve` and the
    # CLI's write routing read it here, which is what keeps them agreeing.
    service_socket = (
        Path(raw["service_socket"]).resolve()
        if "service_socket" in raw
        else operations_root / "service.sock"
    )
    return ScienceConfig(
        world=WorldConfig(
            world_root=Path(raw["world_root"]),
            world_id=raw["world_id"],
            corpus_roots=tuple(Path(value) for value in raw["corpus_roots"]),
        ),
        operations_root=operations_root,
        profile=profile,
        service_socket=service_socket,
        store_root=Path(raw["store_root"]).resolve(),
        plans=plans,
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
        return cls(world=open_world_read(config.world), config=config)

    def read_views(self) -> tuple[tuple[str, ReadView], ...]:
        """One view per configured root, ordered by corpus id then root. Two
        roots carrying the same corpus id both appear: that state is the
        registry's `duplicate-carrier` finding, which `status` reports, and a
        read context that refused or deduplicated would hide it."""
        keyed = []
        for root in self.config.world.corpus_roots:
            keyed.append((load_manifest(root).corpus_id, str(root), ReadView.opened_at(root)))
        keyed.sort(key=lambda entry: entry[:2])
        return tuple((corpus_id, view) for corpus_id, _, view in keyed)

    def load_record(self, uid: str, record_id: str):
        for _, read_view in self.read_views():
            if read_view.holds(record_id):
                node = read_view.get(record_id)
                if node.uid == uid:
                    return node
        raise Refused(Refusal("unknown-cursor", f"record {record_id!r} not found"))

    def single_view(self) -> tuple[str, ReadView]:
        views = self.read_views()
        if len(views) != 1:
            raise Refused(Refusal("invalid-input",
                                  f"the belief path reads exactly one corpus; the config names {len(views)}"))
        return views[0]

    def snapshot(self):
        from science.vocabulary import snapshot
        _, view = self.single_view()
        return snapshot(self.config.profile, view, self.config.store_root, self.store_id(), self.observations())

    def observations(self):
        from science.holdings import found_observations
        corpus_id, view = self.single_view()
        return found_observations(view, self.world, corpus_id)

    def store_id(self) -> str:
        """The configured store's verified identity, read from its genesis by
        detached inspection. `store_identity` is the public reader the store
        identity seam (`beliefs-2d9a55`) adds, a prerequisite for this task."""
        from beliefs.root import store_identity
        identity = store_identity(self.config.store_root)
        if identity is None:
            raise Refused(Refusal("invalid-input", f"{self.config.store_root} is not an initialized store"))
        return identity

    def held_path(self, address: str) -> Path:
        from science.holdings import held_path
        corpus_id, view = self.single_view()
        return held_path(view, self.world, corpus_id, self.config.store_root, self.store_id(), address)

    def is_held(self, node) -> bool:
        from science.holdings import is_held
        corpus_id, view = self.single_view()
        return is_held(view, self.world, corpus_id, node)

    def pins(self):
        (root,) = self.config.world.corpus_roots
        return load_manifest(root).profile

    def epoch_identity(self, *, absent: str | None = None) -> str:
        """The current epoch's packaging identity, or `absent` when none is
        published — the evaluator's snapshot literal unless a caller names the
        field it fills (a verification's epoch is spelled differently)."""
        from beliefs.errors import EpochUnknown
        from beliefs.world.read import current_epoch

        from science.closure import NO_EPOCH_SNAPSHOT
        try:
            return current_epoch(self.world).packaging_identity
        except EpochUnknown:
            return NO_EPOCH_SNAPSHOT if absent is None else absent

    def _context(self, view, corpus_id, observations):
        from science.closure import supplied_context
        from beliefs import stored
        # Keyed as `gather` reads it: the stored assessment's identity, attributed
        # to the one corpus that holds it.
        node_corpus = {
            stored.assessment_value(node, profile=self.config.profile).identity(): (corpus_id,)
            for node in view.iter_stored() if node.kind == "assessment"
        }
        return supplied_context(view, corpus_id=corpus_id, pins=self.pins(), epoch_identity=self.epoch_identity(),
                                observations=observations, node_corpus=node_corpus)

    def gather_inputs(self, proposition: str):
        from science.closure import gather_inputs
        corpus_id, view = self.single_view()
        observations = self.observations()
        return gather_inputs(view, proposition, context=self._context(view, corpus_id, observations),
                             profile=self.config.profile, resolution=self.snapshot())

    def evaluate(self, proposition: str):
        from science.closure import evaluate
        corpus_id, view = self.single_view()
        observations = self.observations()
        return evaluate(view, proposition, observations=observations,
                        context=self._context(view, corpus_id, observations),
                        profile=self.config.profile, resolution=self.snapshot())
