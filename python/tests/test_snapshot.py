"""a restore discards a test's writes, evicts beliefs' registries,
keeps sandbox links as links, and a snapshot holds data only."""
import collections
import os
import socket
import uuid

import pytest

from beliefs.confinement import host_prerequisites
import helpers.snapshot as snapshot_module
from helpers.commons import fork, restore
from helpers.snapshot import Derived, Root, check_value, clear_live, copy_value, materialize, snapshot
from helpers.world import (
    build_belief_world, build_shared_world_with_evidence, hold_fixture_dataset, open_rig, walk_belief_path_confined,
)
from science.config import ReadContext


def _belief_world(work):
    return build_belief_world(work)


def _files(root):
    return {(p.relative_to(root), p.read_bytes()) for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


def _datasets(cfg):
    return [n.id for n in ReadContext.open(cfg).write_view().iter_stored() if n.kind == "dataset"]


def test_a_restore_discards_the_previous_tests_writes(certified_worker_work):
    snap = snapshot(certified_worker_work, "snapshot-check", _belief_world)
    snap.restore()
    before = _datasets(snap.value)
    ref = hold_fixture_dataset(snap.value, "data.txt", b"restore\n", "expression")
    assert ref in _datasets(snap.value)
    snap.restore()
    assert _datasets(snap.value) == before
    assert _files(snap.work) == _files(snap.image)


def test_the_same_write_succeeds_after_every_restore(certified_worker_work):
    """Without eviction the second write is CollisionRefused: the open corpus
    still indexes the first test's dataset."""
    snap = snapshot(certified_worker_work, "snapshot-check", _belief_world)
    for _ in range(2):
        snap.restore()
        hold_fixture_dataset(snap.value, "data.txt", b"twice\n", "expression")


def _links(root):
    return {p.relative_to(root): os.readlink(p) for p in root.rglob("*") if p.is_symlink()}


@pytest.mark.skipif(host_prerequisites() is not None, reason="confinement unavailable")
def test_a_confined_world_restores_its_sandbox_links_as_links(certified_worker_work):
    snap = snapshot(certified_worker_work, "walked-confined", walk_belief_path_confined)
    links = _links(snap.image)
    assert links, "a confined walk left no links; this check exercises nothing"
    for _ in range(2):
        snap.restore()
        assert _links(snap.work) == links


def test_a_live_dispatcher_is_refused_by_type_name(certified_worker_work):
    snap = snapshot(certified_worker_work, "snapshot-check", _belief_world)
    snap.restore()
    with open_rig(snap.value, ("spec",)) as (d, _):
        with pytest.raises(TypeError, match=type(d).__name__):
            check_value((snap.value, {"rig": d}))


def test_a_real_builders_config_and_refs_are_accepted(certified_worker_work):
    snap = snapshot(certified_worker_work, "shared-with-evidence", build_shared_world_with_evidence)
    check_value(snap.value)


def test_a_socket_under_the_world_refuses_the_restore(certified_worker_work):
    snap = snapshot(certified_worker_work, "snapshot-check", _belief_world)
    snap.restore()
    path = snap.work / "ops" / "s.sock"
    path.parent.mkdir(parents=True, exist_ok=True)
    server = socket.socket(socket.AF_UNIX)
    try:
        server.bind(str(path))  # under the certified root, well inside AF_UNIX's 107 bytes
        with pytest.raises(RuntimeError, match="s.sock"):
            snap.restore()
    finally:
        server.close()
        path.unlink()


def test_a_name_reused_with_another_builder_is_refused(certified_worker_work):
    """A name is one world: a second builder under it would get whichever world
    its worker built first, depending on worksteal order."""
    snapshot(certified_worker_work, "snapshot-check", _belief_world)
    with pytest.raises(ValueError, match="snapshot-check"):
        snapshot(certified_worker_work, "snapshot-check", build_belief_world)


# toy declarations over plain files,
# each named afresh so another test's built snapshots cannot satisfy it.


def _manifest(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


def _chain(calls):
    """A three-link lineage whose builders record their order, write `<link>.txt` and append to `links`."""
    names = [uuid.uuid4().hex for _ in range(3)]

    def build(work):
        calls.append(names[0])
        (work / f"{names[0]}.txt").write_text(names[0])
        return {"links": [names[0]]}

    def step_for(name):
        def step(work, value):
            calls.append(name)
            (work / f"{name}.txt").write_text(name)
            value["links"].append(name)
            return value
        return step

    root = Root(names[0], build)
    mid = Derived(names[1], root, step_for(names[1]))
    return root, mid, Derived(names[2], mid, step_for(names[2]))


def test_a_cold_deep_descendant_builds_each_ancestor_once_in_order(tmp_path):
    calls = []
    root, mid, leaf = _chain(calls)
    snap = materialize(tmp_path, leaf)
    assert calls == [root.name, mid.name, leaf.name]
    assert snap.work == tmp_path / root.name and snap.image == tmp_path / f"{leaf.name}.image"
    assert materialize(tmp_path, mid).declaration is mid and calls == [root.name, mid.name, leaf.name]


def test_construction_starts_from_the_base_image_not_a_dirtied_directory(tmp_path):
    calls = []
    root, mid, leaf = _chain(calls)
    base = materialize(tmp_path, mid); base.restore()
    (base.work / "stray.txt").write_text("dirty"); (base.work / f"{root.name}.txt").unlink()
    clear_live()  # a fresh test
    seen = {}
    def probe_step(work, value):
        seen["files"] = _manifest(work)
        return value
    materialize(tmp_path, Derived(uuid.uuid4().hex, mid, probe_step))
    assert seen["files"] == _manifest(base.image)


def test_construction_restores_record_nothing_so_the_live_restore_succeeds(tmp_path):
    _, _, leaf = _chain([])
    snap = materialize(tmp_path, leaf)
    assert snapshot_module._LIVE == {}
    snap.restore()
    assert snapshot_module._LIVE == {snap.work: leaf}


def test_a_step_internal_restore_records_nothing(tmp_path):
    root = Root(uuid.uuid4().hex, lambda work: ((work / "sub").mkdir(), (work / "sub" / "f").write_text("1"), {})[2])
    def step(work, value):
        copy = fork(work / "sub"); (work / "sub" / "f").write_text("2"); restore(copy, work / "sub")
        return value
    snap = materialize(tmp_path, Derived(uuid.uuid4().hex, root, step))
    assert snapshot_module._LIVE == {} and (snap.image / "sub" / "f").read_text() == "1"


def test_copy_value_rebuilds_containers_and_keeps_leaves(fresh_value):
    copied = copy_value(fresh_value)
    assert copied == fresh_value and copied is not fresh_value
    assert copied["a"] is fresh_value["a"]  # a ScienceConfig leaf, shared
    nested = {"k": [1], "t": (1, {"x": 2})}
    out = copy_value(nested)
    assert out == nested and out["k"] is not nested["k"] and out["t"][1] is not nested["t"][1]
    with pytest.raises(TypeError, match="Point"):
        copy_value(collections.namedtuple("Point", "x")(1))


def test_a_step_mutating_its_copy_leaves_the_base_value_unchanged(tmp_path):
    root = Root(uuid.uuid4().hex, lambda work: {"k": [1], "t": (1, {"x": 2})})
    def step(work, value):
        value["k"].append(2); value["t"][1]["x"] = 3; value["new"] = True
        return value
    materialize(tmp_path, Derived(uuid.uuid4().hex, root, step))
    assert snapshot_module._SNAPSHOTS[root.name].value == {"k": [1], "t": (1, {"x": 2})}


def test_a_different_declaration_under_a_built_name_is_refused(tmp_path):
    root = Root(uuid.uuid4().hex, lambda work: {})
    materialize(tmp_path, root)
    with pytest.raises(ValueError, match=root.name):
        materialize(tmp_path, Root(root.name, root.build))


def test_snapshot_calls_share_one_root_per_name_and_builder(tmp_path):
    name = uuid.uuid4().hex
    build = lambda work: {}
    assert snapshot(tmp_path, name, build).declaration is snapshot(tmp_path, name, build).declaration
    with pytest.raises(ValueError, match=name):
        snapshot(tmp_path, name, lambda work: {})


def test_a_descendant_of_an_impostor_ancestor_is_refused(tmp_path):
    name = uuid.uuid4().hex
    materialize(tmp_path, Root(name, lambda work: {"which": "a"}))
    impostor = Root(name, lambda work: {"which": "b"})
    leaf = Derived(uuid.uuid4().hex, impostor, lambda work, value: value)
    with pytest.raises(ValueError, match=name):
        materialize(tmp_path, leaf)
    assert leaf.name not in snapshot_module._SNAPSHOTS


def test_a_declaration_reusing_a_root_name_is_refused(tmp_path):
    name = uuid.uuid4().hex
    snapshot(tmp_path, name, lambda work: {})
    with pytest.raises(ValueError, match=name):
        materialize(tmp_path, Root(name, lambda work: {}))


def test_a_request_from_a_lineage_with_a_live_world_is_refused_untouched(tmp_path):
    _, mid, leaf = _chain([])
    live = materialize(tmp_path, mid); live.restore()
    files, images = _manifest(tmp_path), sorted(p.name for p in tmp_path.glob("*.image"))
    with pytest.raises(RuntimeError, match=f"{mid.name}.*{leaf.name}|{leaf.name}.*{mid.name}"):
        materialize(tmp_path, leaf)
    assert _manifest(tmp_path) == files and sorted(p.name for p in tmp_path.glob("*.image")) == images
    assert leaf.name not in snapshot_module._SNAPSHOTS


def test_a_restore_from_a_lineage_with_a_live_world_is_refused_untouched(tmp_path):
    _, mid, leaf = _chain([])
    other = materialize(tmp_path, leaf)
    live = materialize(tmp_path, mid); live.restore()
    files = _manifest(live.work)
    with pytest.raises(RuntimeError, match=leaf.name):
        other.restore()
    assert _manifest(live.work) == files


def test_a_failed_step_is_rebuilt_from_its_base(tmp_path):
    root = Root(uuid.uuid4().hex, lambda work: ((work / "base.txt").write_text("b"), {})[1])
    attempts = []
    def step(work, value):
        assert not (work / "half.txt").exists()  # each attempt starts from the base's image
        attempts.append(1); (work / "half.txt").write_text("x")
        if len(attempts) == 1:
            raise RuntimeError("step failed")
        return value
    leaf = Derived(uuid.uuid4().hex, root, step)
    with pytest.raises(RuntimeError, match="step failed"):
        materialize(tmp_path, leaf)
    assert leaf.name not in snapshot_module._SNAPSHOTS and not (tmp_path / f"{leaf.name}.image").exists()
    snap = materialize(tmp_path, leaf)
    assert set(_manifest(snap.image)) == {"base.txt", "half.txt"}


def test_a_socket_in_the_lineage_refuses_construction(short_tmp):
    root = Root(uuid.uuid4().hex, lambda work: {})
    live = materialize(short_tmp, root); live.restore()
    path = live.work / "s.sock"
    server = socket.socket(socket.AF_UNIX)
    try:
        server.bind(str(path))
        clear_live()
        with pytest.raises(RuntimeError, match="s.sock"):
            materialize(short_tmp, Derived(uuid.uuid4().hex, root, lambda work, value: value))
    finally:
        server.close(); path.unlink()


def test_the_commons_chain_is_one_lineage_rooted_at_fresh():
    from helpers import commons
    leaves = [commons.SIBLING_PUBLICATIONS, commons.SIBLING_PUBLICATIONS_UNKEPT, commons.LATE_LINK,
              commons.B_UPDATED, commons.B_UPDATED_UNKEPT, commons.EQUAL_HOLDERS, commons.SPEC_DROP,
              commons.SPEC_ONLY, commons.CONFLICTING, commons.CONTENT_CONFLICT, commons.UID_CORRUPTION,
              commons.LATE_CHAIN_UNADOPTED]
    for leaf in leaves:
        node = leaf
        while isinstance(node, Derived):
            node = node.base
        assert node is commons.FRESH, leaf.name
    assert isinstance(commons.FRESH_NO_EPOCH, Root)


def test_a_failed_root_build_is_retried_from_an_empty_directory(tmp_path):
    attempts = []

    def build(work):
        assert list(work.iterdir()) == []  # each attempt starts empty
        attempts.append(1)
        (work / "half.txt").write_text("x")
        if len(attempts) == 1:
            raise RuntimeError("root build failed")
        return {}
    root = Root(uuid.uuid4().hex, build)
    with pytest.raises(RuntimeError, match="root build failed"):
        materialize(tmp_path, root)
    assert root.name not in snapshot_module._SNAPSHOTS
    snap = materialize(tmp_path, root)
    assert set(_manifest(snap.image)) == {"half.txt"} and len(attempts) == 2


def test_a_leftover_unrecorded_image_is_replaced(tmp_path):
    root, mid, _ = _chain([])
    materialize(tmp_path, root)
    stale = tmp_path / f"{mid.name}.image"  # what a failed image copy leaves
    stale.mkdir()
    (stale / "partial.txt").write_text("partial")
    snap = materialize(tmp_path, mid)
    assert set(_manifest(snap.image)) == {f"{root.name}.txt", f"{mid.name}.txt"}
