import dataclasses

import pytest

from beliefs.resolution import TermOutcome
from science.config import ReadContext
from science.refusal import Refused
from helpers.world import build_belief_world, hold_fixture_dataset


@pytest.fixture
def equal_copies(certified_work):
    from beliefs import stored
    from beliefs.root import init_corpus_root, open_corpus, open_world
    from beliefs.world import Fresh
    from helpers.world import FIXTURE_AUTHORITY
    cfg = build_belief_world(certified_work)
    pins = ReadContext.open(cfg).pins()
    extra = (certified_work / "copy", certified_work / "empty")
    for root in extra:
        init_corpus_root(root, authority=FIXTURE_AUTHORITY)
        writer = open_corpus(root, authority=FIXTURE_AUTHORITY, profile=cfg.profile)
        writer.adopt_manifest(profile=pins)
        open_world(cfg.world, authority=FIXTURE_AUTHORITY).admit(root, provenance=Fresh())
    cfg = dataclasses.replace(cfg, world=dataclasses.replace(
        cfg.world, corpus_roots=cfg.world.corpus_roots + extra))
    node = stored.proposition_node("twice", title="twice", claim={"operator": "affects"})
    for root in (cfg.write_root, extra[0]):
        open_corpus(root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(node)
    return cfg


@pytest.mark.parametrize("method", ["mount_holding", "cited"])
def test_equal_copies_prefer_the_write_root_over_the_least_corpus(equal_copies, method):
    cfg = equal_copies
    holders = [mount for mount in ReadContext.open(cfg).mounts() if mount.view.holds("proposition:twice")]
    preferred = max(holders, key=lambda mount: mount.corpus_id)
    ctx = ReadContext.open(dataclasses.replace(cfg, write_root=preferred.root))
    assert getattr(ctx, method)("proposition:twice").corpus_id == preferred.corpus_id


@pytest.mark.parametrize("method", ["mount_holding", "cited"])
def test_equal_copies_outside_the_write_root_choose_the_least_corpus(equal_copies, method):
    cfg = equal_copies
    mounts = ReadContext.open(cfg).mounts()
    empty = next(mount for mount in mounts if not mount.view.holds("proposition:twice"))
    expected = min(mount.corpus_id for mount in mounts if mount.view.holds("proposition:twice"))
    ctx = ReadContext.open(dataclasses.replace(cfg, write_root=empty.root))
    assert getattr(ctx, method)("proposition:twice").corpus_id == expected


def test_dataset_at_ignores_a_retired_holder(reopened):
    from beliefs.root import open_world
    from helpers.commons import a_identity
    from helpers.world import FIXTURE_AUTHORITY
    ids = a_identity(reopened.a)
    assert ReadContext.open(reopened.b).dataset_at(ids["dataset"])[0] == ids["corpus_id"]
    open_world(reopened.b.world, authority=FIXTURE_AUTHORITY).retire(ids["corpus_id"])
    assert ReadContext.open(reopened.b).dataset_at(ids["dataset"]) is None


def test_mount_holding_names_the_one_corpus(certified_work):
    cfg = build_belief_world(certified_work)
    mount = ReadContext.open(cfg).mount_holding("proposition:p1")
    assert len(mount.corpus_id) == 32 and mount.root == cfg.write_root and mount.profile == cfg.profile


def test_mount_holding_refuses_a_record_no_mount_holds(certified_work):
    ctx = ReadContext.open(build_belief_world(certified_work))
    with pytest.raises(Refused) as caught:
        ctx.mount_holding("proposition:absent")
    assert caught.value.refusal.code == "invalid-input"
    assert "'proposition:absent' is not in the configured corpora" in caught.value.refusal.message


def test_snapshot_resolves_the_held_concept_vocabulary(certified_work):
    cfg = build_belief_world(certified_work)
    ctx = ReadContext.open(cfg)
    snapshot = ctx.snapshot()
    binding = cfg.profile.sorts["testing/concept"].vocabulary
    assert snapshot.resolve(binding, "concept:disease-stage") is TermOutcome.MEMBER
    assert snapshot.resolve(binding, "concept:absent") is TermOutcome.NOT_MEMBER


def test_snapshot_omits_a_vocabulary_that_is_not_held(certified_work):
    """The binding names a dataset; nothing holds it; the snapshot says so."""
    from helpers.world import build_fixture_world_with_contract
    cfg = build_fixture_world_with_contract(certified_work, hold_concepts=False)
    snapshot = ReadContext.open(cfg).snapshot()
    binding = cfg.profile.sorts["testing/concept"].vocabulary
    assert snapshot.resolve(binding, "concept:disease-stage") is TermOutcome.NOT_AVAILABLE


def test_a_later_absent_observation_removes_heldness(certified_work):
    """The reduction, not the history: once an Absent supersedes the Found at
    a location, the dataset is not held, whatever the older observation says."""
    from helpers.world import unhold_fixture_dataset
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"gone\n", "expression")
    ctx = ReadContext.open(cfg)
    view = ctx.write_view()
    assert ctx.is_held(view.get(ref))
    unhold_fixture_dataset(cfg, ref)
    ctx = ReadContext.open(cfg)
    view = ctx.write_view()
    assert not ctx.is_held(view.get(ref))
    from beliefs import stored
    from beliefs.dataset import dataset_address
    assert dataset_address(stored.dataset_declaration(view.get(ref))) not in ctx.observations()


def _tree_digest(root):
    from hashlib import sha256
    digest = sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode()); digest.update(path.read_bytes())
    return digest.hexdigest()


def test_holdings_reads_inspect_detached_and_write_nothing(certified_work, monkeypatch):
    """A read must not recover: the reducer is fed the detached chain view,
    and the corpus tree, its metadata and the store are byte-identical after."""
    import science.holdings as holdings_module
    from beliefs.root import log_seam, metadata_root_for
    cfg = build_belief_world(certified_work)
    hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    (root,) = cfg.world.corpus_roots
    before = tuple(_tree_digest(d) for d in (root, metadata_root_for(root), cfg.store_root))
    seam = log_seam()

    class RefusingSeam:
        inspect_detached = staticmethod(seam.inspect_detached)
        state_facts = staticmethod(seam.state_facts)

        @staticmethod
        def inspect_registered(root):
            raise AssertionError("a holdings read must never use the registered (recovering) inspection")

    monkeypatch.setattr(holdings_module, "log_seam", lambda: RefusingSeam)
    ctx = ReadContext.open(cfg)
    assert ctx.observations()
    assert tuple(_tree_digest(d) for d in (root, metadata_root_for(root), cfg.store_root)) == before


def test_observations_and_held_path_follow_the_store(certified_work):
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"hello\n", "expression")
    ctx = ReadContext.open(cfg)
    view = ctx.write_view()
    node = view.get(ref)
    assert ctx.is_held(node)
    from beliefs import stored
    from beliefs.dataset import dataset_address
    address = dataset_address(stored.dataset_declaration(node))
    assert address in ctx.observations()
    assert ctx.held_path(address).read_bytes() == b"hello\n"


def test_held_path_resolves_only_the_configured_store(certified_work):
    """An observation recorded for another store id never selects a file here,
    even when its relative path exists under this store root."""
    from beliefs.dataset import ByteObservation
    from science.holdings import held_path_for
    from science.refusal import Refused
    cfg = build_belief_world(certified_work)
    ctx = ReadContext.open(cfg)
    mine = ctx.store_id()
    other = ("0" * 32) if mine != "0" * 32 else ("1" * 32)
    (cfg.store_root / "aa").mkdir(exist_ok=True)
    (cfg.store_root / "aa" / "f.txt").write_bytes(b"here\n")
    foreign = ByteObservation(digest="sha256:" + "a" * 64, location=f"store:{other}:aa/f.txt")
    local = ByteObservation(digest="sha256:" + "a" * 64, location=f"store:{mine}:aa/f.txt")
    with pytest.raises(Refused):
        held_path_for(cfg.store_root, mine, (foreign,))
    assert held_path_for(cfg.store_root, mine, (foreign, local)) == cfg.store_root / "aa" / "f.txt"


def test_held_path_refuses_an_unknown_address(certified_work):
    ctx = ReadContext.open(build_belief_world(certified_work))
    with pytest.raises(Refused) as caught:
        ctx.held_path("dataset:sha256:" + "0" * 64)
    assert caught.value.refusal.code == "invalid-input"


def test_evaluate_answers_no_belief_before_any_assessment(certified_work):
    ctx = ReadContext.open(build_belief_world(certified_work))
    answer = ctx.evaluate("proposition:p1")
    assert type(answer).__name__ == "NoBelief"
    assert answer.reason == "no-eligible-assessment"


def test_epoch_identity_is_the_no_epoch_value_without_one(certified_work):
    ctx = ReadContext.open(build_belief_world(certified_work))
    assert ctx.epoch_identity() == "no-epoch-published"
