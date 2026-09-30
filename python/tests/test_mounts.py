"""Spec §6: every mount under its own manifest's profile, in the session and
in the sessionless read context alike."""
import dataclasses

import pytest

from beliefs.corpus import ReadView
from beliefs.world import WorldConfig
from helpers.world import build_two_corpus_world, mint_project, open_rig
from science.config import ReadContext, mount_profiles
from science.coordination import resolve_project_ref
from science.refusal import Refused


@pytest.fixture
def two(certified_work):
    return build_two_corpus_world(certified_work)


def _refused(call) -> str:
    with pytest.raises(Refused) as caught:
        call()
    assert caught.value.refusal.code == "invalid-input"
    return caught.value.refusal.message


def test_the_write_root_is_mounted_under_the_writer_profile_and_the_archive_under_its_pins(two):
    mounts = {mount.root.name: mount for mount in ReadContext.open(two).mounts()}
    assert mounts["corpus"].profile is two.profile
    archive = mounts["archive"].profile.activated_contracts
    assert "archive" in archive and "testing" not in archive and "coordination" not in archive


def test_mounts_are_ordered_by_corpus_id(two):
    ids = [mount.corpus_id for mount in ReadContext.open(two).mounts()]
    assert ids == sorted(ids) and len(ids) == 2


def test_a_read_mount_pin_no_document_carries_refuses_naming_root_and_pin(two):
    bare = dataclasses.replace(two, available_contracts=two.available_contracts[:1])
    message = _refused(lambda: mount_profiles(bare))
    assert "archive" in message and "archive:" in message
    assert "archive" in _refused(lambda: ReadContext.open(bare).coordination())


def test_a_read_mount_without_a_manifest_refuses_naming_the_root(two):
    """Review round 1, P2: through the read context's own methods, not only
    `mount_profiles` — `mounts()` must not reach a raw ManifestMissing."""
    empty = two.world.world_root.parent / "empty"
    empty.mkdir()
    widened = dataclasses.replace(two, world=WorldConfig(
        two.world.world_root, two.world.world_id, two.world.corpus_roots + (empty,)))
    ctx = ReadContext.open(widened)
    for call in (lambda: mount_profiles(widened), ctx.mounts, ctx.read_views, ctx.coordination):
        assert str(empty) in _refused(call)


def test_the_session_opens_over_both_roots_though_the_archive_pins_no_coordination(two):
    with open_rig(two, ("project",)) as (dispatcher, _):
        mint_project(dispatcher, "health")
    projects = lambda root: [n for n in ReadView.opened_at(root).iter_stored() if n.kind == "project"]
    assert len(projects(two.write_root)) == 1
    assert projects(two.world.world_root.parent / "archive") == []


def test_a_sessionless_read_resolves_over_both_mounts(two):
    with open_rig(two, ("project",)) as (dispatcher, _):
        address = mint_project(dispatcher, "health")
    assert resolve_project_ref(ReadContext.open(two), "health") == address
