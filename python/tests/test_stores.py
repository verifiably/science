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
    # shortcut: internal lifecycle error import pending public exports in beliefs-1dfd8c.
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
