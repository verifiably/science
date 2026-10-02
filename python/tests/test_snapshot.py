"""Spec §4.3: a restore discards a test's writes, evicts beliefs' registries,
keeps sandbox links as links, and a snapshot holds data only."""
import os
import socket

import pytest

from beliefs.confinement import host_prerequisites
from helpers.snapshot import check_value, snapshot
from helpers.world import (
    build_belief_world, build_shared_world_with_evidence, hold_fixture_dataset, open_rig, walk_belief_path,
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
    still indexes the first test's dataset (spec §2.2)."""
    snap = snapshot(certified_worker_work, "snapshot-check", _belief_world)
    for _ in range(2):
        snap.restore()
        hold_fixture_dataset(snap.value, "data.txt", b"twice\n", "expression")


def _links(root):
    return {p.relative_to(root): os.readlink(p) for p in root.rglob("*") if p.is_symlink()}


@pytest.mark.skipif(host_prerequisites() is not None, reason="confinement unavailable")
def test_a_confined_world_restores_its_sandbox_links_as_links(certified_worker_work):
    snap = snapshot(certified_worker_work, "walked-confined",
                    lambda work: walk_belief_path(work, confined=True))
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
