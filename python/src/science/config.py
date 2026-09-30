"""Launcher configuration loaded directly into beliefs' WorldConfig."""
from __future__ import annotations

import os
import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import NoReturn

from beliefs.contract.domain import DomainContract
from beliefs.corpus import ReadView
from beliefs.errors import ManifestMalformed, ManifestMissing, MountPinUnresolved, ProfileError
from beliefs.profile import (
    ProfileSpec,
    compile_profile,
    shipped_base_contract,
    shipped_coordination,
    shipped_domain_contract,
)
from beliefs.root import open_world_read
from beliefs.world import WorldConfig
from beliefs.world.registry import load_manifest

from science.refusal import Refusal, Refused
from science.contracts import OperatorPlan, load_contract_document

_WORLD_ID_RE = re.compile(r"[0-9a-f]{32}")
_KEYS = (
    "world_root", "world_id", "corpus_roots", "operations_root", "domains", "contracts",
    "store_root", "coordination",
)
_OPTIONAL_KEYS = ("service_socket", "default_project", "write_root", "read_contracts")


@dataclass(frozen=True)
class ScienceConfig:
    world: WorldConfig
    operations_root: Path
    profile: ProfileSpec
    service_socket: Path
    store_root: Path
    coordination: int | None
    # The one configured root the session writes (spec §6); the others are
    # read mounts.
    write_root: Path
    plans: tuple[OperatorPlan, ...] = ()
    # An unpinned beliefs.coordination.CoordinationAddress or None: the project a
    # launcher opens under and a CLI read falls back to with no live session.
    default_project: object = None
    # What a read mount's pins may resolve against: the `contracts` documents,
    # which the writer activates, then the `read_contracts` documents, which it
    # never does.
    available_contracts: tuple[DomainContract, ...] = ()


def _refuse(message: str) -> NoReturn:
    raise Refused(Refusal("invalid-input", message))


def _project_address(value: object):
    """`default_project` is an address, never a name: names are content and may
    collide or change (coordination design §6)."""
    from beliefs.coordination import CoordinationAddress

    try:
        address = CoordinationAddress.parse(value)
    except ValueError:
        address = None
    if address is None or address.local is not None or address.revision is not None:
        _refuse("config default_project must be a project address, coord:<project>; "
                "a name is content and may change")
    return address


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
    missing, unknown = set(_KEYS) - set(raw), set(raw) - set(_KEYS) - set(_OPTIONAL_KEYS)
    if missing or unknown:
        _refuse(f"config must contain exactly the required keys; missing {sorted(missing)}, "
                f"unknown {sorted(unknown)}")
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
    if "write_root" in raw and type(raw["write_root"]) is not str:
        _refuse("config write_root must be a string")
    read_contracts = raw.get("read_contracts", [])
    if type(read_contracts) is not list or any(type(value) is not str for value in read_contracts):
        _refuse("config read_contracts must be a list of strings")
    if type(raw["store_root"]) is not str:
        _refuse("config store_root must be a string")
    coordination = raw["coordination"]
    if coordination is False:
        coordination = None
    elif type(coordination) is not int or coordination < 1:
        _refuse("config coordination must be a coordination contract version (an integer) or false")
    default_project = None
    if "default_project" in raw:
        if coordination is None:
            _refuse("config default_project needs a resolver, and this configuration sets "
                    "`coordination = false`")
        default_project = _project_address(raw["default_project"])
    if not _WORLD_ID_RE.fullmatch(raw["world_id"]):
        _refuse("config world_id must be 32 lowercase hex characters")
    base_dir = path.resolve().parent

    def located(value: str) -> Path:
        # Relative paths name places beside the configuration file, never the
        # process's working directory (projects design P1); an absolute value
        # is unchanged by the join.
        return (base_dir / value).resolve()

    try:
        domains = [shipped_domain_contract(namespace) for namespace in raw["domains"]]
    except ProfileError as caught:
        _refuse(f"config domains do not compile: {caught}")
    base = shipped_base_contract()
    local = [load_contract_document(located(value), base) for value in raw["contracts"]]
    readable = [load_contract_document(located(value), base) for value in read_contracts]
    activated = {contract.content_identity for contract, _ in local}
    both = sorted(contract.namespace for contract, _ in readable if contract.content_identity in activated)
    if both:
        _refuse(f"config lists {both} in both contracts and read_contracts; a document is "
                "activated for the writer or available to read mounts only")
    try:
        profile = compile_profile(
            base,
            domains + [contract for contract, _ in local],
            coordination=None if coordination is None else shipped_coordination(coordination),
        )
    except ProfileError as caught:
        _refuse(f"config contracts do not compile: {caught}")
    plans = tuple(plan for _, plan in local if plan is not None)
    corpus_roots = tuple(located(value) for value in raw["corpus_roots"])
    if "write_root" in raw:
        write_root = located(raw["write_root"])
        if write_root not in corpus_roots:
            _refuse(f"config write_root {write_root} is not one of corpus_roots")
    elif len(corpus_roots) == 1:
        (write_root,) = corpus_roots
    else:
        _refuse(f"config names {len(corpus_roots)} corpus_roots and no write_root; "
                "name the one the session writes")
    operations_root = located(raw["operations_root"])
    # The socket defaults beside the operations root. AF_UNIX caps the path at
    # 107 bytes and a worktree checkout's operations root already exceeds it,
    # so the key exists to name a short path; both `science serve` and the
    # CLI's write routing read it here, which is what keeps them agreeing.
    service_socket = (
        located(raw["service_socket"])
        if "service_socket" in raw
        else operations_root / "service.sock"
    )
    return ScienceConfig(
        world=WorldConfig(
            world_root=located(raw["world_root"]),
            world_id=raw["world_id"],
            corpus_roots=corpus_roots,
        ),
        operations_root=operations_root,
        profile=profile,
        service_socket=service_socket,
        store_root=located(raw["store_root"]),
        coordination=coordination,
        write_root=write_root,
        plans=plans,
        default_project=default_project,
        available_contracts=tuple(contract for contract, _ in local + readable),
    )


def resolve_config_path(cli_value: str | None, env: Mapping[str, str] | None = None) -> Path:
    env = os.environ if env is None else env
    if cli_value:
        return Path(cli_value)
    if "SCIENCE_CONFIG" in env:
        return Path(env["SCIENCE_CONFIG"])
    _refuse("no --config and no SCIENCE_CONFIG")
    raise AssertionError


def require_write_root_pins(config: ScienceConfig) -> None:
    """Spec §6: the writer's stated profile must be exactly what the write
    root's manifest pins, and a configuration that disagrees is refused by name.
    Only the write root is checked: a read mount is mounted under whatever it
    pins. The kernel would refuse the same state as a bare pin mismatch, which
    the CLI can only render as an internal error. Two mistakes reach this: a
    pre-coordination configuration upgraded with `coordination = N`, and a read
    mount's contract listed under `contracts`, which activates it for the
    writer, instead of `read_contracts`. A root whose manifest is missing or
    malformed is left to the kernel's own named `SessionRefused` for a session,
    and to `corpus_id_at` for a sessionless read."""
    root = config.write_root
    try:
        pinned = dict(load_manifest(root).profile.domains)
    except (ManifestMissing, ManifestMalformed):
        return
    wanted = {namespace: f"{namespace}:{identity}"
              for namespace, identity in config.profile.activated_contracts.items()}
    if config.coordination is not None:
        namespace = shipped_coordination(config.coordination).namespace
        if namespace not in pinned:
            _refuse(f"the configuration asks for coordination the corpus at {root} does not pin; "
                    "set `coordination = false` for a corpus adopted before coordination")
        if pinned[namespace] != wanted[namespace]:
            _refuse(f"the corpus at {root} pins coordination contract {pinned[namespace]}, not the one "
                    f"`coordination = {config.coordination}` compiles; set `coordination` to the version it pins")
    unpinned = sorted(set(wanted) - set(pinned))
    if unpinned:
        _refuse(f"the writer activates {unpinned}, which the write root {root} does not pin; a contract "
                "only a read mount pins belongs in read_contracts, not contracts")
    disagreeing = sorted(namespace for namespace in pinned if pinned[namespace] != wanted.get(namespace))
    if disagreeing:
        _refuse(f"the write root {root} pins {[pinned[namespace] for namespace in disagreeing]}, which the "
                "writer's profile does not activate; the writer's profile is exactly the write root's pins")


@dataclass(frozen=True)
class Mount:
    """One configured root as a read sees it: its corpus id, a view opened at
    the call, and the profile its records decode under."""
    corpus_id: str
    root: Path
    view: ReadView
    profile: ProfileSpec


def mount_profiles(config: ScienceConfig) -> dict[Path, ProfileSpec]:
    """Every configured root under the profile its own manifest pins (spec §6):
    the write root under the writer's stated profile, every other root compiled
    from its pins against the shipped packs and the available documents.
    Availability never becomes activation."""
    from beliefs.mount import compile_mount_profile

    profiles = {}
    for root in config.world.corpus_roots:
        if root == config.write_root:
            profiles[root] = config.profile
            continue
        try:
            profiles[root] = compile_mount_profile(root, available=config.available_contracts)
        except MountPinUnresolved as caught:
            _refuse(f"the read mount {root} pins {caught.pin}, which no shipped pack and no "
                    "document in contracts or read_contracts carries")
        except (ManifestMissing, ManifestMalformed) as caught:
            _refuse(f"the read mount {root} has no readable manifest: {caught}")
    return profiles


def corpus_id_at(root: Path) -> str:
    """The root's corpus id, or a refusal naming the root: a missing or
    malformed manifest is a configuration state, never an internal error."""
    try:
        return load_manifest(root).corpus_id
    except (ManifestMissing, ManifestMalformed) as caught:
        _refuse(f"the corpus root {root} has no readable manifest: {caught}")


@dataclass(frozen=True)
class ReadContext:
    world: object
    config: ScienceConfig
    selection: object = None  # a beliefs.coordination.CoordinationAddress or None; typed
    # `object` because `beliefs.coordination` is imported lazily like the rest
    # of this module's kernel reads.

    @classmethod
    def open(cls, config: ScienceConfig) -> ReadContext:
        return cls(world=open_world_read(config.world), config=config)

    def current_project(self):
        """The selected project's unpinned address, or refuse: a subordinate
        record's address is (project identity, local id), and with nothing
        selected there is no project identity to bind (projects design §5.3)."""
        if self.selection is None:
            raise Refused(Refusal(
                "no-current-project",
                "no project is selected; select one with `project-select`, or copy a view "
                "into the current project with `reuse`",
            ))
        return self.selection

    @cached_property
    def _profiles(self) -> dict[Path, ProfileSpec]:
        # Compiled once per context; a dispatcher's per-invocation `replace`
        # builds a fresh context, so a command compiles once (kernel decision 9).
        return mount_profiles(self.config)

    def mounts(self) -> tuple[Mount, ...]:
        """One mount per configured root, ordered by corpus id then root, each
        view opened now: a view indexes its corpus as of its opening. Profiles
        first and manifests through `corpus_id_at`, so a root that cannot be
        mounted refuses by name before any view opens."""
        profiles = self._profiles
        keyed = sorted((corpus_id_at(root), str(root), root) for root in self.config.world.corpus_roots)
        return tuple(Mount(corpus_id, root, ReadView.opened_at(root), profiles[root])
                     for corpus_id, _, root in keyed)

    def read_views(self) -> tuple[tuple[str, ReadView], ...]:
        """One view per configured root, ordered by corpus id then root. Two
        roots carrying the same corpus id both appear: that state is the
        registry's `duplicate-carrier` finding, which `status` reports, and a
        read context that refused or deduplicated would hide it."""
        keyed = []
        for root in self.config.world.corpus_roots:
            keyed.append((corpus_id_at(root), str(root), ReadView.opened_at(root)))
        keyed.sort(key=lambda entry: entry[:2])
        return tuple((corpus_id, view) for corpus_id, _, view in keyed)

    def load_record(self, uid: str, record_id: str):
        for _, read_view in self.read_views():
            if read_view.holds(record_id):
                node = read_view.get(record_id)
                if node.uid == uid:
                    return node
        raise Refused(Refusal("unknown-cursor", f"record {record_id!r} not found"))

    def write_view(self) -> ReadView:
        """The write root's view, opened now: what a write command reads the
        records it is given in (spec §5.5, part 3)."""
        return ReadView.opened_at(self.config.write_root)

    def not_held(self, ref: str) -> NoReturn:
        """Refuse a ref the write root does not hold, naming the read mount that
        does: a person who passed an mm30 record learns where it is."""
        elsewhere = [corpus_id_at(root) for root in self.config.world.corpus_roots
                     if root != self.config.write_root and ReadView.opened_at(root).holds(ref)]
        where = (f"; read mount {', '.join(elsewhere)} holds it, and this command reads the write root"
                 if elsewhere else "")
        raise Refused(Refusal("invalid-input", f"{ref!r} is not in the corpus{where}"))

    def dataset_at(self, address: str):
        from science.holdings import dataset_at
        return dataset_at(self.read_views(), address)

    def snapshot(self, profile: ProfileSpec | None = None):
        from science.vocabulary import snapshot
        return snapshot(self.config.profile if profile is None else profile, self.read_views(),
                        self.config.store_root, self.store_id(), self.observations())

    def observations(self):
        from science.holdings import found_observations
        return found_observations(self.read_views(), self.world)

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
        return held_path(self.read_views(), self.world, self.config.store_root, self.store_id(), address)

    def is_held(self, node) -> bool:
        from science.holdings import is_held
        return is_held(self.read_views(), self.world, node)

    def coordination(self):
        """A live resolver over every configured root, each under its own
        manifest's profile (coordination §6.2; spec §6)."""
        from beliefs.corpus import CoordinationResolver

        if self.config.coordination is None:
            raise Refused(Refusal("invalid-input",
                                  "coordination = false in this configuration; there is no resolver to ask"))
        # Every root's manifest read by name first: a resolver over a root
        # without one would stop at a bare ManifestMissing (spec §5.5).
        for root in self.config.world.corpus_roots:
            corpus_id_at(root)
        require_write_root_pins(self.config)
        return CoordinationResolver(self._profiles)

    def pins(self, root: Path | None = None):
        return load_manifest(self.config.write_root if root is None else root).profile

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

    def mount_holding(self, ref: str) -> Mount:
        """The one mounted corpus holding `ref`. A record id in two corpora is
        the world's duplicate-location conflict, refused rather than answered
        from whichever mount sorts first."""
        holders = [mount for mount in self.mounts() if mount.view.holds(ref)]
        if not holders:
            raise Refused(Refusal("invalid-input", f"{ref!r} is not in the configured corpora"))
        if len(holders) > 1:
            raise Refused(Refusal("invalid-input",
                                  f"{ref!r} is held by corpora {', '.join(m.corpus_id for m in holders)}; "
                                  "one address in two corpora is a duplicate location, which `status` reports"))
        return holders[0]

    def _context(self, mount: Mount, observations, proposition: str):
        from science.closure import supplied_context
        from beliefs import stored
        assessments = [(node, stored.assessment_value(node, profile=mount.profile))
                       for node in mount.view.iter_stored() if node.kind == "assessment"]
        # Keyed as `gather` reads it: the stored assessment's identity, attributed
        # to the one corpus that holds it.
        node_corpus = {value.identity(): (mount.corpus_id,) for _, value in assessments}
        # Only the evidence `gather` reads for this proposition: one edited
        # assessment elsewhere in the corpus does not block every proposition.
        self._refuse_foreign_observations(
            mount, [(node, value) for node, value in assessments if value.proposition == proposition])
        # The lineage snapshot walks from each observed dataset through this
        # mount's view, which cannot resolve another mount's dataset. The check
        # above refuses this proposition's evidence that observes one, so the
        # datasets left out are ones no gathered assessment observes (spec §5.5,
        # part 3).
        declared = {address: found for address, found in observations.items() if mount.view.holds(address)}
        return supplied_context(mount.view, corpus_id=mount.corpus_id, pins=self.pins(mount.root),
                                epoch_identity=self.epoch_identity(), observations=declared,
                                node_corpus=node_corpus)

    def _refuse_foreign_observations(self, mount: Mount, assessments) -> None:
        """Refuse an assessment, of the (node, value) pairs given, whose run
        reads a dataset the mount does not declare: its lineage cannot be read through the mount's view,
        and leaving it out would degrade admission without saying so. Write
        commands never mint one (`CorpusWriter._refuse_ineligible` reads the
        writer's own view); only an edited corpus can hold one."""
        from beliefs import stored
        for node, value in assessments:
            run = stored.typed_ref("run", value.run)
            if not mount.view.holds(run):
                continue  # a missing run is `gather`'s to report
            foreign = sorted(target for role in stored.INPUT_ROLES
                             for target in stored.inputs_of(mount.view.get(run), role)
                             if not mount.view.holds(target))
            if foreign:
                raise Refused(Refusal(
                    "invalid-input",
                    f"{node.id} in corpus {mount.corpus_id} rests on {run}, which reads {', '.join(foreign)}; "
                    "that corpus does not declare them, and a corpus's evidence reads only its own datasets"))

    def gather_inputs(self, proposition: str):
        from science.closure import gather_inputs
        mount = self.mount_holding(proposition)
        observations = self.observations()
        return gather_inputs(mount.view, proposition, context=self._context(mount, observations, proposition),
                             profile=mount.profile, resolution=self.snapshot(mount.profile))

    def evaluate(self, proposition: str):
        from science.closure import evaluate
        mount = self.mount_holding(proposition)
        observations = self.observations()
        return evaluate(mount.view, proposition, observations=observations,
                        context=self._context(mount, observations, proposition),
                        profile=mount.profile, resolution=self.snapshot(mount.profile))
