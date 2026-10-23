"""The two-installation fixture every commons 1a command test starts from: A with
reproducible evidence and a current epoch, B empty, both pinned to coordination v3
under one contract document."""
import pytest

from beliefs.world.registry import load_manifest
from helpers.commons import (
    DATA_A,
    GIT_ENV,
    Installations,
    Remotes,
    a_identity,
    build_fresh,
    build_fresh_no_epoch,
    read_rig,
    refused,
    reopen,
    with_remotes,
)
from helpers.snapshot import check_value, snapshot
from helpers.world import CONCEPTS, LEVELS, PINS_V3, concept_list_address
import science.publication as publication
from science.config import FetchPolicy, ReadContext
from science.sharing import SharingRegistry
from science.world_belief import epoch_currency

V3_PIN = PINS_V3.domains["coordination"]


@pytest.fixture
def fresh_value(certified_worker_work):
    snap = snapshot(certified_worker_work, "commons-1a-fresh", build_fresh)
    snap.restore()
    return snap.value


@pytest.fixture
def fresh(fresh_value):
    return Installations.of(fresh_value)


@pytest.fixture
def fresh_no_epoch(certified_worker_work):
    snap = snapshot(certified_worker_work, "commons-1a-fresh-no-epoch", build_fresh_no_epoch)
    snap.restore()
    return Installations.of(snap.value)


def test_both_installations_pin_coordination_v3_and_the_same_contract(fresh):
    for cfg in (fresh.a, fresh.b):
        assert load_manifest(cfg.write_root).profile.domains["coordination"] == V3_PIN
    assert load_manifest(fresh.a.write_root).profile == load_manifest(fresh.b.write_root).profile


def test_only_a_holds_the_vocabulary_lists(fresh):
    assert ReadContext.open(fresh.a).cited(concept_list_address())
    assert refused(lambda: ReadContext.open(fresh.b).cited(concept_list_address())).code == "invalid-input"


def test_a_holds_the_reproducible_evidence_and_a_current_epoch(fresh):
    ids = a_identity(fresh.a)
    ctx = ReadContext.open(fresh.a)
    assert set(ids) == {"proposition", "dataset", "spec", "run", "assessment", "world"}
    assert ids["world"] == fresh.a.world.world_id
    for key in ("proposition", "dataset", "spec", "run", "assessment"):
        assert ctx.cited(ids[key]).root == fresh.a.write_root
    assert ctx.held_path(ids["dataset"]).read_bytes() == DATA_A
    epoch_currency(ctx.world, ctx.session_ids())


def test_without_an_epoch_a_has_no_current_epoch(fresh_no_epoch):
    ctx = ReadContext.open(fresh_no_epoch.a)
    assert refused(lambda: epoch_currency(ctx.world, ctx.session_ids())).code == "no-epoch"


def test_b_is_empty_with_fetch_policy_and_a_sharing_root(fresh):
    assert fresh.b.fetch == FetchPolicy("fetch", 0) and not fresh.b.sharing_root.exists()   # created on first write
    assert SharingRegistry(fresh.b.sharing_root).pins() == ()
    kinds = {node.kind for node in ReadContext.open(fresh.b).write_view().iter_stored()}
    assert not kinds & {"proposition", "dataset", "analysis-spec", "run", "assessment"}


def test_the_fixture_value_is_snapshot_storable(fresh_value):
    check_value(fresh_value)


def test_reopen_round_trips_the_sharing_keys(fresh):
    cfg = reopen(fresh.b)
    assert cfg.sharing_root == fresh.b.sharing_root and cfg.fetch == fresh.b.fetch
    assert cfg.accept == fresh.b.accept and cfg.world == fresh.b.world and cfg.write_root == fresh.b.write_root
    assert cfg.profile.base_contract_identity == fresh.b.profile.base_contract_identity
    assert cfg.profile.activated_contracts == fresh.b.profile.activated_contracts


def test_each_installation_carries_its_one_project(fresh):
    for name, cfg in (("a", fresh.a), ("b", fresh.b)):
        text = read_rig(cfg, "projects").invoke("projects", {}).text
        (line,) = [line.strip() for line in text.splitlines() if line.strip().startswith("coord:")]
        assert line.split(": ", 1)[1].startswith(f"{name} @")


def test_the_data_dir_holds_a_data_and_the_vocabulary_lists(fresh):
    data = fresh.data_dir()
    assert sorted(p.name for p in data.iterdir()) == ["a.txt", "concepts.txt", "levels.txt"]
    assert fresh.data_a_path() == data / "a.txt" and fresh.data_a_path().read_bytes() == DATA_A
    assert (data / "concepts.txt").read_bytes() == CONCEPTS and (data / "levels.txt").read_bytes() == LEVELS


def test_with_remotes_sets_and_restores_the_publication_seams(fresh):
    before = (publication.REMOTE_FOR, publication.GIT_ENV)
    with with_remotes(fresh):
        assert publication.GIT_ENV == GIT_ENV
        assert publication.REMOTE_FOR.__self__.base == Remotes(fresh.remotes).base
    assert (publication.REMOTE_FOR, publication.GIT_ENV) == before


def test_with_remotes_restores_the_seams_when_its_body_raises(fresh):
    before = (publication.REMOTE_FOR, publication.GIT_ENV)
    with pytest.raises(RuntimeError), with_remotes(fresh):
        raise RuntimeError("body")
    assert (publication.REMOTE_FOR, publication.GIT_ENV) == before
