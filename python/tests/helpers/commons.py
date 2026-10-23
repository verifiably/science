"""Helpers for the commons (sharing) tests."""
from __future__ import annotations

import os
import secrets
import subprocess
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pytest

from beliefs.consulted import CorpusPins
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination, shipped_domain_contract
from beliefs.root import init_corpus_root, init_store_root, init_world_root, open_corpus, open_world
from beliefs.world import Fresh, WorldConfig

from helpers.world import (
    CONCEPTS,
    COORDINATION_V3,
    DOMAINS,
    FIXTURE_AUTHORITY,
    LEVELS,
    OBSERVED,
    SPEC_FIELDS,
    STORE_IDS,
    _install_holdings_reducer,
    _list_address,
    _minted_ref,
    fixture_bundle,
    fixture_contract_document,
    hold_fixture_dataset,
    mint_fixture_run,
    open_rig,
)
from science.config import FetchPolicy, ReadContext, ScienceConfig, load_config
from science.contracts import load_contract_document
from science.dispatch import Dispatcher
from science.publication import binding_fields
from science.refusal import Refusal, Refused
from science.sharing import SharingRegistry
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


# The two-installation fixture (commons 1a plan, Task 5): A publishes a reproducible view, B binds A's location and
# adopts it. Every builder returns a snapshot-storable dict; a pytest fixture wraps it with `Installations.of`.
QUERY_1A = "version: science.view-query.v1\nclauses:\n  - all:\n      - kinds: [proposition, dataset, analysis-spec, run, assessment]\n"
DATA_A = b"gene\tvalue\nPHF19\t1\n"
LOC_A, LOC_B = "https://remote.test/a", "https://remote.test/b"


@dataclass(frozen=True)
class Installations:
    a: ScienceConfig
    b: ScienceConfig
    remotes: Path

    def data_dir(self) -> Path:
        """The bytes B fetches: `a.txt` (A's dataset), `concepts.txt` and `levels.txt` (A's vocabulary lists)."""
        return self.remotes.parent / "data"

    def data_a_path(self) -> Path:
        """The source of A's dataset bytes. The dataset is declared under the name `data.txt` (the shared
        FIXTURE_SNAKEFILE reads `inputs/data.txt`); `a.txt` only carries its bytes."""
        return self.data_dir() / "a.txt"

    @classmethod
    def of(cls, value: dict) -> Installations:
        return cls(**value)


def build_installation(work: Path, name: str, *, hold_vocabulary: bool) -> ScienceConfig:
    """One installation under `work/<name>`: the shipped base and biology packs plus the test contract document
    (`work/testing.yaml`, shared by every installation so their pins agree), compiled with coordination v3; the
    holdings reducer installed; a project `<name>` carrying QUERY_1A. The vocabulary lists are held only when
    `hold_vocabulary`. The sharing root is configured and left uncreated: its first write creates it."""
    base = shipped_base_contract()
    contract, plan = load_contract_document(fixture_contract_document(work), base)
    profile = compile_profile(base, [shipped_domain_contract(ns) for ns in DOMAINS] + [contract],
                              coordination=shipped_coordination(COORDINATION_V3))
    pins = CorpusPins(
        science_contract="science:" + profile.base_contract_identity,
        domains={ns: f"{ns}:{identity}" for ns, identity in profile.activated_contracts.items()},
    )
    home = work / name
    corpus_root = home / "corpus"
    config = WorldConfig(home / "world", secrets.token_hex(16), (corpus_root,))
    init_world_root(config, authority=FIXTURE_AUTHORITY)
    init_corpus_root(corpus_root, authority=FIXTURE_AUTHORITY)
    STORE_IDS[home] = init_store_root(home / "store", authority=FIXTURE_AUTHORITY)
    open_corpus(corpus_root, authority=FIXTURE_AUTHORITY, profile=profile).adopt_manifest(profile=pins)
    world = open_world(config, authority=FIXTURE_AUTHORITY)
    world.admit(corpus_root, provenance=Fresh())
    _install_holdings_reducer(world)
    cfg = ScienceConfig(world=config, operations_root=home / "ops", profile=profile,
                        service_socket=home / "ops" / "service.sock", store_root=home / "store",
                        coordination=COORDINATION_V3, write_root=corpus_root, plans=(plan,),
                        available_contracts=(contract,), sharing_root=home / "sharing", accept=(),
                        fetch=FetchPolicy("fetch", 0))
    if hold_vocabulary:
        hold_fixture_dataset(cfg, "concepts.txt", CONCEPTS, "concept vocabulary")
        hold_fixture_dataset(cfg, "levels.txt", LEVELS, "level vocabulary")
    with open_rig(cfg, ("project",)) as (d, _):
        d.invoke("project", {"name": name, "query": QUERY_1A})
    return cfg


def _add_a_evidence(a: ScienceConfig, work: Path) -> None:
    """proposition:p1, the observed dataset DATA_A, a spec on p1 over it, one run and its assessment."""
    with open_rig(a, ("claim", "spec")) as (d, _):
        d.invoke("claim", {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
                           "layer": "causal", "polarity": "positive", "slug": "p1"})
        # Held as `data.txt`, the input FIXTURE_SNAKEFILE reads; `data_dir()/a.txt` is only a source of its bytes.
        data = hold_fixture_dataset(a, "data.txt", DATA_A, "expression", **OBSERVED)
        spec = _minted_ref(d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=data)).text,
                           "analysis-spec")
    run = mint_fixture_run(a, spec, data, fixture_bundle(work))
    with open_rig(a, ("assess",)) as (d, _):
        d.invoke("assess", {"run": run})


def build_fresh(work: Path, *, epoch: bool = True) -> dict:
    """A with reproducible evidence (and its epoch published when `epoch`), B empty, the remotes' directory and
    the data directory B fetches from. Every session it opens is closed."""
    from science.world_belief import publish_session_epoch
    a = build_installation(work, "a", hold_vocabulary=True)
    b = build_installation(work, "b", hold_vocabulary=False)
    _add_a_evidence(a, work / "a")
    if epoch:
        publish_session_epoch(a)
    remotes, data = work / "remotes", work / "data"
    remotes.mkdir()
    data.mkdir()
    for name, content in (("a.txt", DATA_A), ("concepts.txt", CONCEPTS), ("levels.txt", LEVELS)):
        (data / name).write_bytes(content)
    return {"a": a, "b": b, "remotes": remotes}


def build_fresh_no_epoch(work: Path) -> dict:
    """`build_fresh` without A's epoch, as a snapshot builder."""
    return build_fresh(work, epoch=False)


def write_commons_config(cfg: ScienceConfig) -> Path:
    """The launcher TOML for an installation `build_installation` built, beside its world root: every key,
    including the configured corpus roots (the sharing registry's mounted roots are the loader's to add), the
    write root, the sharing root, accept and fetch."""
    home = cfg.world.world_root.parent
    contract = home.parent / "testing.yaml"
    assert contract.is_file(), "write_commons_config needs the installations' contract document"
    mounted = set(SharingRegistry(cfg.sharing_root).mounted_roots())
    keys = {
        "world_root": str(cfg.world.world_root),
        "world_id": cfg.world.world_id,
        "corpus_roots": [str(root) for root in cfg.world.corpus_roots if root not in mounted],
        "write_root": str(cfg.write_root),
        "operations_root": str(cfg.operations_root),
        "service_socket": str(cfg.service_socket),
        "domains": list(DOMAINS),
        "contracts": [str(contract)],
        "store_root": str(cfg.store_root),
        "coordination": cfg.coordination,
        "sharing_root": str(cfg.sharing_root),
        "accept": list(cfg.accept),
        "fetch": {"policy": cfg.fetch.policy, "max_bytes": cfg.fetch.max_bytes},
    }
    if cfg.default_project is not None:
        keys["default_project"] = str(cfg.default_project)
    path = home / "science.toml"
    path.write_text("".join(f"{key} = {_toml(value)}\n" for key, value in keys.items()))
    return path


def reopen(cfg: ScienceConfig) -> ScienceConfig:
    """What the loader builds from `cfg`'s launcher TOML."""
    return load_config(write_commons_config(cfg))


def read_rig(cfg: ScienceConfig, *names: str) -> Dispatcher:
    """A dispatcher over the production declarations named, reading `cfg`, with no session."""
    from science.loader import production_tree, resolve_handlers
    decls = tuple(d for d in production_tree() if d.name in names)
    missing = sorted(set(names) - {d.name for d in decls})
    if missing:
        raise ValueError(f"no production declarations named {missing}")
    return Dispatcher(decls, resolve_handlers(decls), ReadContext.open(cfg))


def a_identity(a: ScienceConfig) -> dict[str, str]:
    """A's evidence refs (proposition, dataset, spec, run, assessment) and its world id; once A has published,
    also the publication's `corpus_id`, `marker` and `artifact`, read from the binding in A's write root."""
    view = ReadContext.open(a).write_view()

    def only(kind: str) -> str:
        (ref,) = [node.id for node in view.iter_stored() if node.kind == kind]
        return ref
    dataset = _list_address(DATA_A, "data.txt")
    assert view.holds(dataset), f"A holds no dataset {dataset}"
    ids = {"proposition": only("proposition"), "dataset": dataset, "spec": only("analysis-spec"),
           "run": only("run"), "assessment": only("assessment"), "world": a.world.world_id}
    bindings = [node for node in view.iter_stored() if node.kind == "publication-binding"]
    assert len(bindings) <= 1, f"A holds {len(bindings)} publication bindings; a_identity reads one"
    if bindings:
        binding = binding_fields(bindings[0])
        ids.update(corpus_id=binding.corpus_id, marker=binding.marker, artifact=binding.artifact)
    return ids


@contextmanager
def with_remotes(installations: Installations) -> Iterator[None]:
    """Point the publication seams at the installations' bare repositories and the isolated git environment,
    restoring both on exit."""
    import science.publication as publication
    saved = publication.REMOTE_FOR, publication.GIT_ENV
    publication.REMOTE_FOR = Remotes(installations.remotes).remote_for
    publication.GIT_ENV = GIT_ENV
    try:
        yield
    finally:
        publication.REMOTE_FOR, publication.GIT_ENV = saved


def build_published(work: Path) -> dict:
    """`build_fresh`, then A publishes its project `a` to LOC_A over the remotes' bare repositories."""
    value = build_fresh(work)
    with with_remotes(Installations.of(value)), open_rig(value["a"], ("publish",)) as (d, _):
        d.invoke("publish", {"target": "a", "to": LOC_A})
    return value


def build_bound(work: Path) -> dict:
    """`build_published`, then B binds LOC_A to A's world with `provider-bind`, passing the world id A's marker
    claims."""
    value = build_published(work)
    installations = Installations.of(value)
    ids = a_identity(installations.a)
    with with_remotes(installations), open_rig(installations.b, ("provider-bind",)) as (d, _):
        d.invoke("provider-bind", {"location": LOC_A, "corpus_id": ids["corpus_id"], "world": ids["world"]})
    return value


def transport_with(installations: Installations, **seams: object):
    """A git transport over the installations' bare repositories, under the isolated git environment, with its
    cache in a fresh directory under the work tree (removed with it) and each named test seam set."""
    from science.transport_git import GitTransport
    cache = installations.remotes.parent / "transport-cache" / secrets.token_hex(8)
    transport = GitTransport(cache, author="test", remote_for=Remotes(installations.remotes).remote_for,
                             env=GIT_ENV)
    for name, value in seams.items():
        if not hasattr(GitTransport, name):
            raise AttributeError(f"GitTransport has no test seam {name!r}")
        setattr(transport, name, value)
    return transport


def binding_ref(text: str) -> str:
    """The record id of the `[publication-binding]` block in a command's report."""
    (line,) = [line for line in text.splitlines() if line.startswith("[publication-binding] ")]
    return line.split()[1]
