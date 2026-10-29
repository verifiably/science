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
    WORKING_FIELDS,
    _install_holdings_reducer,
    _list_address,
    _minted_ref,
    concept_list_address,
    fixture_bundle,
    fixture_contract_document,
    hold_fixture_dataset,
    level_list_address,
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
    write root, the sharing root, accept, fetch and keep."""
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
        "keep": list(cfg.keep),
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


def a_identity(a: ScienceConfig, *, binding_destination: str | None = None) -> dict[str, str]:
    """A's evidence refs (proposition, dataset, spec, run, assessment) and its world id; once A has published,
    also the publication's `corpus_id`, `marker` and `artifact`, read from the binding in A's write root (the one
    to `binding_destination` when A has published to more than one)."""
    view = ReadContext.open(a).write_view()

    def only(kind: str) -> str:
        (ref,) = [node.id for node in view.iter_stored() if node.kind == kind]
        return ref
    dataset = _list_address(DATA_A, "data.txt")
    assert view.holds(dataset), f"A holds no dataset {dataset}"
    ids = {"proposition": only("proposition"), "dataset": dataset, "spec": only("analysis-spec"),
           "run": only("run"), "assessment": only("assessment"), "world": a.world.world_id}
    from science.coordination import tip_nodes
    resolver = ReadContext.open(a).coordination()
    bindings = [node for resolved in resolver.standing("publication-binding").values()
                for node in tip_nodes(resolver, resolved) if view.holds(node.id)]
    if binding_destination is not None:
        bindings = [node for node in bindings if binding_fields(node).destination.locator == binding_destination]
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


def publish_again(installations: Installations, location: str) -> str:
    """A publishes its project `a` a second time, to `location`: a new corpus id holding the same addresses.
    The first publication's binding drifted A's write root, so A publishes an epoch first. Returns that corpus
    id."""
    from science.world_belief import publish_session_epoch
    publish_session_epoch(installations.a)
    with with_remotes(installations), open_rig(installations.a, ("publish",)) as (d, ctx):
        text = d.invoke("publish", {"target": "a", "to": location}).text
        return binding_fields(ctx.write_view().get(binding_ref(text))).corpus_id


def build_adopted(work: Path) -> dict:
    """`build_bound`, then B adopts A's publication from LOC_A: B's pin is `mounted`; B's configuration is the
    one it opened with, so the adopted root mounts at B's next open (`reopen`)."""
    value = build_bound(work)
    installations = Installations.of(value)
    with with_remotes(installations), open_rig(installations.b, ("adopt",)) as (d, _):
        d.invoke("adopt", {"location": LOC_A, "corpus_id": a_identity(installations.a)["corpus_id"]})
    return value


def build_reopened(work: Path) -> dict:
    """`build_adopted`, then B reopened (its adopted root mounted) with an epoch published over it."""
    from science.world_belief import publish_session_epoch
    value = build_adopted(work)
    b = reopen(value["b"])
    publish_session_epoch(b)
    return {**value, "b": b}


def build_verified(work: Path) -> dict:
    """`build_reopened`, then B fetches the bytes of three datasets A's mount declares (A's dataset from
    `data_dir()/a.txt`, the concept and level lists from `concepts.txt` and `levels.txt`), citing each from the
    mount and declaring none, and verifies A's assessment. The run policy is the minimal one for the build when
    the host cannot confine, as `test_mount_citations._confine` sets it."""
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    value = build_reopened(work)
    installations = Installations.of(value)
    ids = a_identity(installations.a)
    data = installations.data_dir()
    code, entrypoint, _ = fixture_bundle(work / "a")  # the bundle A's run was minted from
    with pytest.MonkeyPatch.context() as monkeypatch:
        if host_prerequisites() is not None:
            monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        with open_rig(installations.b, ("fetch", "verify")) as (d, _):
            for dataset, source in ((ids["dataset"], installations.data_a_path()),
                                    (concept_list_address(), data / "concepts.txt"),
                                    (level_list_address(), data / "levels.txt")):
                d.invoke("fetch", {"dataset": dataset, "source": str(source)})
            d.invoke("verify", {"assessment": ids["assessment"], "code": str(code), "entrypoint": entrypoint})
    return value


def closure_input_addresses(closure) -> frozenset[str]:
    """The dataset addresses a decoded run closure's recipe names as its inputs."""
    return frozenset(item.dataset for item in closure.recipe.inputs)


def derive_changed_analysis(installations: Installations) -> dict[str, str]:
    """B's changed analysis over A's mounted records, declaring none of them: a `spec` on A's proposition over
    A's dataset with one changed input (WORKING_FIELDS' method), a run of it from B's own copy of the fixture
    bundle (minted under MINIMAL_POLICY, as `mint_fixture_run` does), and its assessment. B must hold the
    dataset's bytes (`build_verified` fetched them). Returns the spec, run and assessment refs."""
    b = installations.b
    ids = a_identity(installations.a)
    with open_rig(b, ("spec",)) as (d, _):
        spec = _minted_ref(d.invoke("spec", dict(WORKING_FIELDS, target=ids["proposition"],
                                                 dataset=ids["dataset"])).text, "analysis-spec")
    run = mint_fixture_run(b, spec, ids["dataset"], fixture_bundle(installations.remotes.parent / "b"))
    with open_rig(b, ("assess",)) as (d, _):
        assessment = _minted_ref(d.invoke("assess", {"run": run}).text, "assessment")
    return {"spec": spec, "run": run, "assessment": assessment}


def b_derivation(b: ScienceConfig) -> dict[str, str]:
    """The spec, run and assessment `derive_changed_analysis` minted, read from B's write root: its one spec and
    one assessment, and the run that assessment names (B's write root also holds the replay its `verify` ran)."""
    from beliefs import stored
    from beliefs.runrecord import run_ref
    view = ReadContext.open(b).write_view()

    def only(kind: str):
        (node,) = [node for node in view.iter_stored() if node.kind == kind]
        return node
    assessment = only("assessment")
    return {"spec": only("analysis-spec").id, "assessment": assessment.id,
            "run": run_ref(stored.assessment_value(assessment, profile=b.profile).run)}


def build_derived(work: Path) -> dict:
    """`build_verified`, then B derives its changed analysis over A's mounted records
    (`derive_changed_analysis`)."""
    value = build_verified(work)
    derive_changed_analysis(Installations.of(value))
    return value


LOC_A2 = "https://remote.test/a2"


def build_conflicting(work: Path) -> dict:
    """`build_bound`, then A publishes its project `a` a second time, to LOC_A2 (a new corpus id holding the same
    addresses), and B binds LOC_A2 to A's world. `installations` is the `Installations` value; `corpus_id` the
    second publication's."""
    value = build_bound(work)
    installations = Installations.of(value)
    corpus_id = publish_again(installations, LOC_A2)
    with with_remotes(installations), open_rig(installations.b, ("provider-bind",)) as (d, _):
        d.invoke("provider-bind",
                 {"location": LOC_A2, "corpus_id": corpus_id, "world": installations.a.world.world_id})
    return {"installations": value, "corpus_id": corpus_id}


LOC_A3, LOC_C = "https://remote.test/a3", "https://remote.test/c"


def build_content_conflict(work: Path) -> dict:
    """A revises its published proposition in place; B still holds the earlier content."""
    value = build_reopened(work)
    installations = Installations.of(value)
    a = installations.a
    writer = open_corpus(a.write_root, authority=FIXTURE_AUTHORITY, profile=a.profile)
    proposition = writer.read_view.get(a_identity(a)["proposition"])
    writer.revise(proposition.model_copy(update={"title": "Revised proposition prose"}))
    cid = publish_again(installations, LOC_A3)
    with with_remotes(installations), open_rig(installations.b, ("provider-bind",)) as (d, _):
        d.invoke("provider-bind", {"location": LOC_A3, "corpus_id": cid, "world": a.world.world_id})
    return {"installations": value, "corpus_id": cid}


def build_uid_corruption(work: Path) -> dict:
    """C redirects a source's identifier after B adopted its first publication."""
    from beliefs import stored
    from science.world_belief import publish_session_epoch

    value = build_reopened(work)
    installations = Installations.of(value)
    c = build_installation(work, "c", hold_vocabulary=False)
    writer = open_corpus(c.write_root, authority=FIXTURE_AUTHORITY, profile=c.profile)
    source = writer.add(stored.source_node(title="A source", identifiers={"doi": "10.1234/original"}))
    with open_rig(c, ("project",)) as (d, _):
        d.invoke("project", {"name": "sources", "query": "version: science.view-query.v1\nclauses:\n  - all:\n      - kinds: [source]\n"})

    def publish():
        publish_session_epoch(c)
        with with_remotes(installations), open_rig(c, ("publish",)) as (d, ctx):
            text = d.invoke("publish", {"target": "sources", "to": LOC_C}).text
            return binding_fields(ctx.write_view().get(binding_ref(text))).corpus_id

    first = publish()
    with with_remotes(installations), open_rig(installations.b, ("provider-bind", "adopt")) as (d, _):
        d.invoke("provider-bind", {"location": LOC_C, "corpus_id": first, "world": c.world.world_id})
        d.invoke("adopt", {"location": LOC_C, "corpus_id": first})
    writer.correct_identifier(source.id, {"doi": "10.1234/corrected"}, grounds="corrected DOI")
    return {"installations": value, "c": c, "corpus_id": publish(), "predecessor": first}


def fork(installation_home: Path) -> Path:
    """Save one publisher outside its home, keeping its absolute-path identities intact."""
    import shutil
    copy = Path(tempfile.mkdtemp(prefix=f"{installation_home.name}-fork-", dir=installation_home.parent))
    copy.rmdir()
    shutil.copytree(installation_home, copy, symlinks=True)
    return copy


def restore(copy: Path, installation_home: Path) -> None:
    from helpers.snapshot import WorldSnapshot
    WorldSnapshot(installation_home, copy, None, fork).restore()


def _build_published_b(work: Path, *, base) -> dict:
    from science.world_belief import publish_session_epoch
    value = base(work)
    publish_session_epoch(value["b"])
    with with_remotes(Installations.of(value)), open_rig(value["b"], ("publish",)) as (d, _):
        d.invoke("publish", {"target": "b", "to": LOC_B})
    return value


def build_published_b(work):
    return _build_published_b(work, base=build_derived)


def build_published_b_unkept(work):
    return _build_published_b(work, base=build_reopened)


def _b_publication(b):
    (node,) = [node for node in ReadContext.open(b).write_view().iter_stored()
               if node.kind == "publication-binding"]
    return binding_fields(node)


def _build_a_bound_b(work: Path, *, base) -> dict:
    value = base(work)
    with with_remotes(Installations.of(value)), open_rig(value["a"], ("provider-bind",)) as (d, _):
        d.invoke("provider-bind", {"location": LOC_B, "corpus_id": _b_publication(value["b"]).corpus_id,
                                   "world": value["b"].world.world_id})
    return value


def build_a_bound_b(work):
    return _build_a_bound_b(work, base=build_published_b)


def build_a_bound_b_unkept(work):
    return _build_a_bound_b(work, base=build_published_b_unkept)


def _build_overlapping(work: Path, *, base) -> dict:
    from science.world_belief import publish_session_epoch
    value = base(work)
    with with_remotes(Installations.of(value)), open_rig(value["a"], ("adopt",)) as (d, _):
        d.invoke("adopt", {"location": LOC_B, "corpus_id": _b_publication(value["b"]).corpus_id})
    value["a"] = reopen(value["a"])
    publish_session_epoch(value["a"])
    return value


def build_overlapping(work):
    return _build_overlapping(work, base=build_a_bound_b)


def build_overlapping_unkept(work):
    return _build_overlapping(work, base=build_a_bound_b_unkept)


def _publish_update(installations: Installations) -> str:
    import json
    from science.coordination import resolve_project_ref
    ids = a_identity(installations.a)
    addresses = [ids[key] for key in ("proposition", "dataset", "spec", "run")]
    addresses += [_list_address(CONCEPTS, "concepts.txt"), _list_address(LEVELS, "levels.txt")]
    with open_rig(installations.a, ("revise",)) as (d, ctx):
        d.invoke("revise", {"address": str(resolve_project_ref(ctx, "a")),
                            "query": json.dumps({"version": "science.view-query.v1",
                                                 "clauses": [{"all": [{"addresses": addresses}]}]})})
    return publish_again(installations, LOC_A)


def _build_updated(work: Path, *, base) -> dict:
    value = base(work)
    _publish_update(Installations.of(value))
    return value


def build_updated(work):
    return _build_updated(work, base=build_overlapping)


def build_updated_unkept(work):
    return _build_updated(work, base=build_overlapping_unkept)


def _build_b_updated(work: Path, *, base) -> dict:
    from science.world_belief import publish_session_epoch
    value = base(work)
    with with_remotes(Installations.of(value)), open_rig(value["b"], ("adopt",)) as (d, _):
        d.invoke("adopt", {"location": LOC_A, "corpus_id": a_identity(value["a"])["corpus_id"]})
    value["b"] = reopen(value["b"])
    publish_session_epoch(value["b"])
    return value


def build_b_updated(work):
    return _build_b_updated(work, base=build_updated)


def build_b_updated_unkept(work):
    return _build_b_updated(work, base=build_updated_unkept)


def build_sibling_publications(work):
    import shutil
    value = build_overlapping(work)
    installations = Installations.of(value)
    home = installations.a.world.world_root.parent
    copy = fork(home)
    first = _publish_update(installations)
    restore(copy, home)
    sibling = _publish_update(installations)
    shutil.rmtree(copy)
    return value, first, sibling


def _build_late_chain(work: Path, *, base) -> tuple:
    value = base(work)
    installations = Installations.of(value)
    first = a_identity(installations.a)["corpus_id"]
    missing = publish_again(installations, LOC_A)
    last = publish_again(installations, LOC_A)
    return value, first, missing, last


def build_late_chain(work):
    return _build_late_chain(work, base=build_overlapping_unkept)


def build_late_chain_unadopted(work):
    return _build_late_chain(work, base=build_bound)


def build_late_link(work):
    from science.world_belief import publish_session_epoch
    value, _, missing, last = build_late_chain(work)
    with with_remotes(Installations.of(value)), open_rig(value["b"], ("adopt",)) as (d, _):
        d.invoke("adopt", {"location": LOC_A, "corpus_id": last})
    value["b"] = reopen(value["b"])
    publish_session_epoch(value["b"])
    return value, missing
