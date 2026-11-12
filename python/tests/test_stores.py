"""Admission and identity boundaries for the stores that supply held bytes."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import shutil

import pytest

from beliefs.root import (
    LifecycleState, export_head_artifact, init_store_root, metadata_root_for,
    open_world, read_lifecycle_state, replicate_root, restore_root, store_identity,
)
from beliefs.world.anchors import StoreSubject
from beliefs.world.verify import ArtifactCarrier, ObserverSet
from helpers.world import FIXTURE_AUTHORITY, build_fixture_world
from science import config as config_module
from science.refusal import Refused
from science.session import open_session


def tree_snapshot(root):
    """Include absent trees, empty directories, modes, links and exact file content."""
    if not root.exists():
        return None
    return {
        str(path.relative_to(root)): (
            path.lstat().st_mode,
            str(path.readlink()) if path.is_symlink() else
            sha256(path.read_bytes()).hexdigest() if path.is_file() else None,
        ) for path in [root, *sorted(root.rglob("*"))]
    }


def store_snapshot(root):
    return tree_snapshot(root), tree_snapshot(metadata_root_for(root))


def replicate_store(cfg, destination, *, admit):
    subject = StoreSubject(store_identity(cfg.store_root))
    artifact = export_head_artifact(
        open_world(cfg.world, authority=FIXTURE_AUTHORITY), subject, store_root=cfg.store_root,
    )
    replicate_root(cfg.store_root, destination, authority=FIXTURE_AUTHORITY)
    if admit:
        report = restore_root(destination, subject, ObserverSet((ArtifactCarrier.from_bytes(artifact),)),
                              authority=FIXTURE_AUTHORITY)
        assert report.outcome == "validated"
    return destination


@pytest.fixture
def store_config(certified_work):
    cfg = build_fixture_world(certified_work)
    extra = certified_work / "read-store"
    init_store_root(extra, authority=FIXTURE_AUTHORITY)
    return replace(cfg, read_store_roots=(extra,))


def test_configured_stores_map_both_roles(store_config):
    cfg = store_config
    assert config_module.configured_stores(cfg) == {
        store_identity(root): root.resolve() for root in (cfg.store_root, *cfg.read_store_roots)
    }


@pytest.mark.parametrize("duplicate", ["write", "alias", "identity"])
def test_configured_stores_reject_duplicate_paths_and_ids(store_config, duplicate):
    cfg = store_config
    if duplicate == "write":
        cfg = replace(cfg, read_store_roots=(cfg.store_root,))
    elif duplicate == "alias":
        alias = cfg.store_root.parent / "alias"
        alias.symlink_to(cfg.read_store_roots[0])
        cfg = replace(cfg, read_store_roots=(*cfg.read_store_roots, alias))
    else:
        copy = cfg.store_root.parent / "copy"
        shutil.copytree(cfg.store_root, copy)
        cfg = replace(cfg, read_store_roots=(copy,))
    with pytest.raises(Refused) as caught:
        config_module.configured_stores(cfg)
    assert caught.value.refusal.code == "invalid-input"
    assert str(cfg.read_store_roots[0].resolve()) in caught.value.refusal.message
    if duplicate == "identity":
        assert str(cfg.store_root) in caught.value.refusal.message
        assert store_identity(cfg.store_root) in caught.value.refusal.message


@pytest.mark.parametrize("role", ["write", "read"])
@pytest.mark.parametrize("state", list(LifecycleState))
def test_configured_stores_require_read_admission(store_config, monkeypatch, role, state):
    cfg = store_config
    target = cfg.store_root if role == "write" else cfg.read_store_roots[0]
    monkeypatch.setattr(config_module, "read_lifecycle_state",
                        lambda root: state if root == target else LifecycleState.WRITABLE)
    if state in {LifecycleState.WRITABLE, LifecycleState.READ_ONLY_SERVICEABLE}:
        assert config_module.configured_stores(cfg)[store_identity(target)] == target
    else:
        with pytest.raises(Refused) as caught:
            config_module.configured_stores(cfg)
        assert caught.value.refusal.code == "invalid-input"
        assert str(target) in caught.value.refusal.message
        assert state.value in caught.value.refusal.message


@pytest.mark.parametrize("kind", ["missing", "malformed", "corpus"])
def test_bad_store_identity_names_root(store_config, kind):
    cfg = store_config
    root = cfg.write_root if kind == "corpus" else cfg.store_root.parent / kind
    if kind == "malformed":
        (root / ".#~chain").mkdir(parents=True)
        (root / ".#~chain" / ("a" * 64)).write_bytes(b"broken")
    with pytest.raises(Refused) as caught:
        config_module.configured_stores(replace(cfg, read_store_roots=(root,)))
    assert caught.value.refusal.code == "invalid-input"
    assert str(root) in caught.value.refusal.message


@pytest.mark.parametrize("kind", ["writable", "copy", "unserviceable", "restored"])
def test_admission_inspection_never_changes_disk(certified_work, kind):
    cfg = build_fixture_world(certified_work)
    root = certified_work / "carrier"
    if kind == "writable":
        init_store_root(root, authority=FIXTURE_AUTHORITY)
    elif kind == "copy":
        shutil.copytree(cfg.store_root, root)
    else:
        replicate_store(cfg, root, admit=kind == "restored")
    expected = {"writable": LifecycleState.WRITABLE, "copy": LifecycleState.METADATA_LESS,
                "unserviceable": LifecycleState.READ_ONLY_UNSERVICEABLE,
                "restored": LifecycleState.READ_ONLY_SERVICEABLE}[kind]
    assert read_lifecycle_state(root) is expected
    # Configure only one carrier for the copied identity.
    fresh = certified_work / "fresh"
    init_store_root(fresh, authority=FIXTURE_AUTHORITY)
    cfg = replace(cfg, store_root=fresh, read_store_roots=(root,))
    before = store_snapshot(root), store_snapshot(fresh)
    if kind in {"copy", "unserviceable"}:
        with pytest.raises(Refused) as caught:
            open_session(cfg)
        assert caught.value.refusal.code == "invalid-input"
        assert str(root) in caught.value.refusal.message
        assert not (cfg.operations_root / "sessions").exists()
    else:
        assert config_module.configured_stores(cfg)[store_identity(root)] == root
    assert (store_snapshot(root), store_snapshot(fresh)) == before


@pytest.mark.parametrize("stage", ["store_identity", "read_lifecycle_state"])
@pytest.mark.parametrize("kind", ["os", "metadata"])
def test_store_inspection_error_retains_cause_and_creates_no_ledger(store_config, monkeypatch, stage, kind):
    # shortcut: internal lifecycle error import pending public exports.
    from beliefs.root import MetadataStoreInvalid
    error = PermissionError("unreadable") if kind == "os" else MetadataStoreInvalid("broken metadata")
    def fail(root):
        raise error
    monkeypatch.setattr(config_module, stage, fail)
    before = store_snapshot(store_config.store_root)
    with pytest.raises(Refused) as caught:
        open_session(store_config)
    assert caught.value.__cause__ is error
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data == {"kind": type(error).__name__, "root": str(store_config.store_root)}
    assert str(error) in caught.value.refusal.message
    assert str(store_config.store_root) in caught.value.refusal.message
    assert not (store_config.operations_root / "sessions").exists()
    assert store_snapshot(store_config.store_root) == before


def test_bad_store_binding_precedes_session_ledger(store_config):
    missing = store_config.store_root.parent / "missing"
    with pytest.raises(Refused):
        open_session(replace(store_config, read_store_roots=(missing,)))
    assert not (store_config.operations_root / "sessions").exists()


@pytest.mark.parametrize("selected", ["1" * 32, "2" * 32])
def test_held_path_reads_each_configured_identity(tmp_path, selected):
    from beliefs.dataset import ByteObservation
    from science.holdings import held_path_for
    stores = {"1" * 32: tmp_path / "write", "2" * 32: tmp_path / "read"}
    observation = ByteObservation("sha256:" + "a" * 64, f"store:{selected}:file.txt")
    assert held_path_for(stores, (observation,)) == stores[selected] / "file.txt"


@pytest.mark.parametrize("locations", [[], ["https://data.test/file.txt"], [f"store:{'3' * 32}:file.txt"]])
def test_foreign_identity_never_resolves_by_path(tmp_path, locations):
    from beliefs.dataset import ByteObservation
    from science.holdings import held_path_for
    (tmp_path / "file.txt").write_bytes(b"same path")
    observations = tuple(ByteObservation("sha256:" + "a" * 64, location) for location in locations)
    with pytest.raises(Refused) as caught:
        held_path_for({"1" * 32: tmp_path}, observations)
    assert caught.value.refusal.code == "invalid-input"
    assert "1" * 32 in caught.value.refusal.message
    for location in locations:
        assert location in caught.value.refusal.message


def test_read_copy_can_sort_before_write_copy(tmp_path):
    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration
    from beliefs.holdings.adapter import dataset_observations
    from science.holdings import held_path_for
    digest = "sha256:" + "a" * 64
    declaration = DatasetDeclaration(resources=(ResourceDeclaration(name="f", digest=digest),))
    active = [{"location": f"store:{identity}:f", "outcome": {"finding": "found", "digest": digest},
               "history": []} for identity in ["2" * 32, "1" * 32]]
    observations = dataset_observations(declaration, active, []).observations
    stores = {"2" * 32: tmp_path / "write", "1" * 32: tmp_path / "read"}
    assert held_path_for(stores, observations) == tmp_path / "read" / "f"


@pytest.mark.parametrize("relative", ["/outside", "../outside", "", "a/../../outside", "link/outside"])
def test_held_path_rejects_escape(tmp_path, relative):
    from beliefs.dataset import ByteObservation
    from science.holdings import held_path_for
    root = tmp_path / "store"
    root.mkdir()
    (root / "link").symlink_to(tmp_path, target_is_directory=True)
    observation = ByteObservation("sha256:" + "a" * 64, f"store:{'1' * 32}:{relative}")
    with pytest.raises(Refused) as caught:
        held_path_for({"1" * 32: root}, (observation,))
    assert caught.value.refusal.code == "invalid-input"


def test_held_path_validates_a_matched_store_identity(tmp_path):
    from beliefs.dataset import ByteObservation
    from science.holdings import held_path_for
    with pytest.raises(Refused):
        held_path_for({"invalid": tmp_path}, (ByteObservation("sha256:" + "a" * 64, "store:invalid:f"),))


def run_store_recipe(destination, home):
    """Execute the runbook's shell block, changing only interpreter and destination."""
    import os
    import shlex
    import subprocess
    import sys
    doc = Path(__file__).resolve().parents[2] / "docs" / "stores.md"
    recipe = doc.read_text().split("<!-- store-init-recipe -->", 1)[1].split("```sh", 1)[1].split("```", 1)[0]
    recipe = recipe.replace("uv run python", shlex.quote(sys.executable))
    recipe = recipe.replace("/absolute/path/to/store-working", shlex.quote(str(destination)))
    home.mkdir(exist_ok=True)
    env = {"PATH": str(Path(sys.executable).parent) + os.pathsep + os.defpath,
           "HOME": str(home), "USER": "store-test", "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(["/bin/sh", "-c", recipe], env=env, capture_output=True, text=True, timeout=30)


@pytest.fixture
def relocated_store(certified_work):
    from helpers.world import build_belief_world, hold_fixture_dataset
    from science.config import FetchPolicy
    cfg = build_belief_world(certified_work)
    content = b"inherited expression\n"
    address = hold_fixture_dataset(cfg, "old.txt", content, "inherited")
    restored = replicate_store(cfg, certified_work / "restored", admit=True)
    assert read_lifecycle_state(restored) is LifecycleState.READ_ONLY_SERVICEABLE
    fresh = certified_work / "store-working"
    created = run_store_recipe(fresh, certified_work / "recipe-home")
    assert created.returncode == 0, created.stderr
    cfg = replace(cfg, store_root=fresh, read_store_roots=(restored,), fetch=FetchPolicy("fetch", 0))
    return cfg, address, content


def test_relocated_store_reads_and_new_dataset_write(relocated_store, certified_work):
    from beliefs.resolution import TermOutcome
    from helpers.world import open_rig
    from science.config import ReadContext
    cfg, old_address, old_bytes = relocated_store
    restored, = cfg.read_store_roots
    inherited_id, write_id = store_identity(restored), store_identity(cfg.store_root)
    assert write_id != inherited_id
    before = store_snapshot(restored)
    ctx = ReadContext.open(cfg)
    binding = cfg.profile.sorts["testing/concept"]
    assert ctx.snapshot(nodes=ctx.write_view().iter_stored(), observations=ctx.observations()).resolve(binding, "concept:disease-stage") is TermOutcome.MEMBER
    assert ctx.held_path(old_address).read_bytes() == old_bytes
    source = certified_work / "new.txt"
    source.write_bytes(b"new expression\n")
    with open_rig(cfg, ("dataset",)) as (dispatcher, _):
        outcome = dispatcher.invoke("dataset", {"path": str(source), "title": "new"})
    new_address = next(word for word in outcome.text.split() if word.startswith("dataset:"))
    ctx = ReadContext.open(cfg)
    assert ctx.held_path(new_address).is_relative_to(cfg.store_root)
    assert ctx.held_path(new_address).read_bytes() == source.read_bytes()
    assert all(o.location.startswith(f"store:{write_id}:") for o in ctx.observations()[new_address])
    assert ctx.snapshot(nodes=ctx.write_view().iter_stored(), observations=ctx.observations()).resolve(binding, "concept:disease-stage") is TermOutcome.MEMBER
    assert ctx.held_path(old_address).read_bytes() == old_bytes
    assert store_snapshot(restored) == before


def fetch_inherited(cfg, address):
    from helpers.world import open_rig
    from science.config import ReadContext
    source = ReadContext.open(cfg).held_path(address)
    with open_rig(cfg, ("fetch",)) as (dispatcher, _):
        dispatcher.invoke("fetch", {"dataset": address, "source": str(source)})


def test_fetch_keeps_inherited_observation(relocated_store):
    from science.config import ReadContext
    cfg, address, content = relocated_store
    restored, = cfg.read_store_roots
    before = store_snapshot(restored)
    old_location = ReadContext.open(cfg).observations()[address][0].location
    fetch_inherited(cfg, address)
    found = ReadContext.open(cfg).observations()[address]
    locations = {observation.location for observation in found}
    assert old_location in locations
    assert any(location.startswith(f"store:{store_identity(cfg.store_root)}:") for location in locations)
    assert len(locations) == 2
    assert ReadContext.open(cfg).held_path(address).read_bytes() == content
    assert store_snapshot(restored) == before


def test_blocked_digest_is_not_rescued_by_fresh_store(relocated_store, monkeypatch):
    from beliefs.holdings.adapter import DatasetBlocked
    from science.config import ReadContext
    import science.holdings as holdings
    cfg, address, _ = relocated_store
    fetch_inherited(cfg, address)
    ctx = ReadContext.open(cfg)
    active, blocked = holdings.reduced_heads(ctx.world, frozenset(cid for cid, _ in ctx.read_views()))
    assert not blocked
    inherited_location = next(o.location for o in ctx.observations()[address]
                              if o.location.startswith(f"store:{store_identity(cfg.read_store_roots[0])}:"))
    inherited_head = next(row for row in active if row["location"] == inherited_location)
    active = [row for row in active if row["location"] != inherited_location]
    blocked = [{"location": inherited_location, "heads": [inherited_head], "reasons": ["unsettled"]}]
    monkeypatch.setattr(holdings, "reduced_heads", lambda world, corpus_ids: (active, blocked))
    assert isinstance(holdings.reduced_observations(ctx.read_views(), ctx.world)[address], DatasetBlocked)
    with pytest.raises(Refused) as caught:
        ReadContext.open(cfg).held_path(address)
    assert caught.value.refusal.code == "invalid-input"
    assert "blocked" in caught.value.refusal.message
    # Each location on its own line, spelled as `recheck` takes it.
    assert caught.value.refusal.message.splitlines()[1:] == [inherited_location]


def test_operator_store_recipe_is_repeatable(relocated_store, certified_work):
    cfg, _, _ = relocated_store
    repeated = run_store_recipe(cfg.store_root, certified_work / "recipe-home")
    assert repeated.returncode == 0, repeated.stderr
    assert repeated.stdout.strip() == store_identity(cfg.store_root)
    restored, = cfg.read_store_roots
    before = store_snapshot(restored)
    refused = run_store_recipe(restored, certified_work / "recipe-home")
    assert refused.returncode != 0
    assert store_snapshot(restored) == before


def test_inherited_and_write_stores_refuse_corrupted_bytes_in_run_and_verify_without_fallback(
    certified_work, monkeypatch
):
    import science.commands.run as run_module
    from beliefs import boundary as boundary_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    from helpers.world import (
        OBSERVED,
        SPEC_FIELDS,
        STORE_IDS,
        build_belief_world,
        fixture_bundle,
        hold_fixture_dataset,
        open_rig,
    )
    from science.config import FetchPolicy, ReadContext

    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)

    cfg = build_belief_world(certified_work)
    orig_store = cfg.store_root
    cand_a = certified_work / "cand-a"
    cand_b = certified_work / "cand-b"
    init_store_root(cand_a, authority=FIXTURE_AUTHORITY)
    init_store_root(cand_b, authority=FIXTURE_AUTHORITY)
    low_store, high_store = sorted((cand_a, cand_b), key=store_identity)

    cfg_low = replace(cfg, store_root=low_store, read_store_roots=(orig_store,))
    STORE_IDS[cfg_low.write_root.parent] = store_identity(low_store)
    inherited_bytes = b"inherited-expression\n"
    inherited_ref = hold_fixture_dataset(cfg_low, "data.txt", inherited_bytes, "inherited", **OBSERVED)
    restored = replicate_store(cfg_low, certified_work / "restored-low", admit=True)

    cfg = replace(
        cfg,
        store_root=high_store,
        read_store_roots=(restored, orig_store),
        fetch=FetchPolicy("fetch", 0),
    )
    STORE_IDS[cfg.write_root.parent] = store_identity(high_store)
    code, entrypoint, targets = fixture_bundle(certified_work, "supported")

    # (a) Unchanged inherited holding succeeds through run, assess, and verify.
    with open_rig(cfg, ("spec", "run", "assess", "verify")) as (d, ctx):
        spec_out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=inherited_ref))
        spec_ref = next(t for t in spec_out.text.split() if t.startswith("analysis-spec:"))
        run_out = d.invoke("run", {"spec": spec_ref, "dataset": inherited_ref, "code": str(code),
                                   "entrypoint": entrypoint, "targets": list(targets)})
        run_ref = next(t for t in run_out.text.split() if t.startswith("run:"))
        assess_out = d.invoke("assess", {"run": run_ref})
        assessment_ref = next(t for t in assess_out.text.split() if t.startswith("assessment:"))
        verify_out = d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint})
        assert "[verification] verification:" in verify_out.text

    # (b) Add a valid second copy in store_root (high_store), then corrupt the first-selected
    # inherited carrier in restored (low_store). Both run and verify must refuse without
    # falling back to high_store or launching an engine.
    fetch_inherited(cfg, inherited_ref)
    ctx = ReadContext.open(cfg)
    assert len(ctx.observations()[inherited_ref]) == 2
    selected_inherited = ctx.held_path(inherited_ref)
    assert selected_inherited.is_relative_to(restored)
    selected_inherited.write_bytes(b"corrupted-inherited\n")

    def _never_engine(*args, **kwargs):
        raise AssertionError("engine must not launch on corrupted store bytes")

    with monkeypatch.context() as patch:
        patch.setattr(boundary_module, "run_engine", _never_engine)
        patch.setattr(boundary_module, "launch_confined", _never_engine)
        with open_rig(cfg, ("run", "verify")) as (d, _):
            with pytest.raises(Refused) as run_caught:
                d.invoke("run", {"spec": spec_ref, "dataset": inherited_ref, "code": str(code),
                                 "entrypoint": entrypoint, "targets": list(targets)})
            assert run_caught.value.refusal.code == "kernel-refused"
            assert "does not match expected" in run_caught.value.refusal.data["reason"]

            with pytest.raises(Refused) as verify_caught:
                d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint})
            assert verify_caught.value.refusal.code == "kernel-refused"
            assert "does not match expected" in verify_caught.value.refusal.data["reason"]

    # (c) Holding in store_root (high_store) whose bytes are altered after admission refuses
    # in both run and verify before workflow execution.
    write_bytes = b"write-store-expression\n"
    write_ref = hold_fixture_dataset(cfg, "data.txt", write_bytes, "writable", **OBSERVED)
    with open_rig(cfg, ("spec", "run", "assess")) as (d, _):
        w_spec_out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=write_ref))
        w_spec_ref = next(t for t in w_spec_out.text.split() if t.startswith("analysis-spec:"))
        w_run_out = d.invoke("run", {"spec": w_spec_ref, "dataset": write_ref, "code": str(code),
                                     "entrypoint": entrypoint, "targets": list(targets)})
        w_run_ref = next(t for t in w_run_out.text.split() if t.startswith("run:"))
        w_assess_out = d.invoke("assess", {"run": w_run_ref})
        w_assessment_ref = next(t for t in w_assess_out.text.split() if t.startswith("assessment:"))

    write_carrier = ReadContext.open(cfg).held_path(write_ref)
    assert write_carrier.is_relative_to(high_store)
    write_carrier.write_bytes(b"corrupted-writable\n")

    with monkeypatch.context() as patch:
        patch.setattr(boundary_module, "run_engine", _never_engine)
        patch.setattr(boundary_module, "launch_confined", _never_engine)
        with open_rig(cfg, ("run", "verify")) as (d, _):
            with pytest.raises(Refused) as w_run_caught:
                d.invoke("run", {"spec": w_spec_ref, "dataset": write_ref, "code": str(code),
                                 "entrypoint": entrypoint, "targets": list(targets)})
            assert w_run_caught.value.refusal.code == "kernel-refused"
            assert "does not match expected" in w_run_caught.value.refusal.data["reason"]

            with pytest.raises(Refused) as w_verify_caught:
                d.invoke("verify", {"assessment": w_assessment_ref, "code": str(code), "entrypoint": entrypoint})
            assert w_verify_caught.value.refusal.code == "kernel-refused"
            assert "does not match expected" in w_verify_caught.value.refusal.data["reason"]

