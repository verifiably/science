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
    snapshot = ctx.snapshot(nodes=ctx.write_view().iter_stored(), observations=ctx.observations())
    binding = cfg.profile.sorts["testing/concept"]
    assert snapshot.resolve(binding, "concept:disease-stage") is TermOutcome.MEMBER
    assert snapshot.resolve(binding, "concept:absent") is TermOutcome.NOT_MEMBER


def test_snapshot_omits_a_vocabulary_that_is_not_held(certified_work):
    """The binding names a dataset; nothing holds it; the snapshot says so."""
    from helpers.world import build_fixture_world_with_contract
    cfg = build_fixture_world_with_contract(certified_work, hold_concepts=False)
    ctx = ReadContext.open(cfg)
    snapshot = ctx.snapshot(nodes=ctx.write_view().iter_stored(), observations=ctx.observations())
    binding = cfg.profile.sorts["testing/concept"]
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
        held_path_for({mine: cfg.store_root}, (foreign,))
    assert held_path_for({mine: cfg.store_root}, (foreign, local)) == cfg.store_root / "aa" / "f.txt"


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


def test_context_reads_inherited_store_and_keeps_write_identity(certified_work):
    from beliefs.root import init_store_root, store_identity
    from helpers.world import FIXTURE_AUTHORITY, concept_list_address, write_config_for
    from science.config import load_config
    cfg = build_belief_world(certified_work)
    inherited = cfg.store_root
    write = certified_work / "fresh"
    write_id = init_store_root(write, authority=FIXTURE_AUTHORITY)
    cfg = dataclasses.replace(cfg, store_root=write, read_store_roots=(inherited,))
    cfg = load_config(write_config_for(cfg))
    ctx = ReadContext.open(cfg)
    assert ctx.store_id() == write_id != store_identity(inherited)
    assert ctx.held_path(concept_list_address()).is_relative_to(inherited)
    binding = cfg.profile.sorts["testing/concept"]
    assert ctx.snapshot(nodes=ctx.write_view().iter_stored(), observations=ctx.observations()).resolve(binding, "concept:disease-stage") is TermOutcome.MEMBER


@pytest.mark.parametrize("method", ["snapshot", "evaluate", "gather_inputs"])
def test_snapshot_refuses_unconfigured_observation(certified_work, method):
    from beliefs.root import init_store_root
    from helpers.world import FIXTURE_AUTHORITY
    cfg = build_belief_world(certified_work)
    fresh = certified_work / "fresh"
    init_store_root(fresh, authority=FIXTURE_AUTHORITY)
    ctx = ReadContext.open(dataclasses.replace(cfg, store_root=fresh))
    with pytest.raises(Refused) as caught:
        getattr(ctx, method)(*(() if method == "snapshot" else ("proposition:p1",)))
    assert caught.value.refusal.code == "invalid-input"


@pytest.mark.parametrize("damage", ["digest", "io"])
def test_snapshot_does_not_fall_back_after_bad_copy(certified_work, monkeypatch, damage):
    from pathlib import Path
    from beliefs.dataset import ByteObservation
    from helpers.world import concept_list_address
    from science.vocabulary import snapshot
    cfg = build_belief_world(certified_work)
    ctx = ReadContext.open(cfg)
    bad = certified_work / "bad-copy"
    bad.mkdir()
    observations = {}
    for address, found in ctx.observations().items():
        relative = found[0].location.split(":", 2)[2]
        target = bad / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((cfg.store_root / relative).read_bytes())
        observations[address] = tuple(ByteObservation(found[0].digest, f"store:{identity}:{relative}")
                                      for identity in ("1" * 32, "2" * 32))
    target = bad / observations[concept_list_address()][0].location.split(":", 2)[2]
    if damage == "digest":
        target.write_bytes(b"corrupt")
    else:
        target.unlink()
    read_bytes = Path.read_bytes
    def read_without_fallback(path):
        if path.is_relative_to(cfg.store_root):
            raise AssertionError("read a later good copy after choosing the bad copy")
        return read_bytes(path)
    monkeypatch.setattr(Path, "read_bytes", read_without_fallback)
    stores = {"1" * 32: bad, "2" * 32: cfg.store_root}
    if damage == "io":
        with pytest.raises(Refused):
            snapshot(cfg.profile, ctx.write_view().iter_stored(), stores, observations)
    else:
        result = snapshot(cfg.profile, ctx.write_view().iter_stored(), stores, observations)
        binding = cfg.profile.sorts["testing/concept"]
        assert result.resolve(binding, "concept:disease-stage") is TermOutcome.NOT_AVAILABLE


def test_snapshot_without_found_observations_is_unreadable(certified_work):
    cfg = build_belief_world(certified_work)
    binding = cfg.profile.sorts["testing/concept"]
    ctx = ReadContext.open(cfg)
    assert ctx.snapshot(nodes=ctx.write_view().iter_stored(), observations={}).resolve(
        binding, "concept:disease-stage") is TermOutcome.NOT_AVAILABLE


def _world_kind_contract(monkeypatch):
    import helpers.world as world
    monkeypatch.setattr(world, "TEST_CONTRACT", world.TEST_CONTRACT.replace(
        "  sorts:\n", "  sorts:\n    witness:\n      binding: {kind: world-kind, world_kind: procedure}\n", 1))


@pytest.mark.parametrize("excluded", ["retired", "rejected", "unmounted"])
def test_authoring_snapshot_scope_excludes_non_session_holders(certified_work, monkeypatch, excluded):
    from beliefs.root import open_corpus, open_world
    from helpers.analysis import analysis_nodes
    from helpers.world import FIXTURE_AUTHORITY, build_two_corpus_world, archive_config
    from science.authoring_records import session_records
    _world_kind_contract(monkeypatch)
    cfg = build_two_corpus_world(certified_work)
    archive = archive_config(cfg)
    node = open_corpus(archive.write_root, authority=FIXTURE_AUTHORITY, profile=archive.profile).add(analysis_nodes(archive.profile)[0])
    other = ReadContext.open(cfg).mount_holding(node.id).corpus_id
    if excluded == "retired":
        open_world(cfg.world, authority=FIXTURE_AUTHORITY).retire(other)
    elif excluded == "rejected":
        from beliefs.coordination import CoordinationAddress
        from beliefs.intents.publish import Destination, PublishIntent
        from beliefs.publication import marker_record
        from beliefs.publication_arrival import require_publication_layout
        from beliefs.root import init_corpus_root
        from beliefs.world import Fresh
        from nodes.core.corpus import Corpus
        root = certified_work / "publication"
        init_corpus_root(root, authority=FIXTURE_AUTHORITY)
        writer = open_corpus(root, authority=FIXTURE_AUTHORITY, profile=cfg.profile)
        writer.adopt_manifest(profile=ReadContext.open(cfg).pins())
        open_world(cfg.world, authority=FIXTURE_AUTHORITY).admit(root, provenance=Fresh())
        node = writer.add(analysis_nodes(cfg.profile)[0])
        intent = PublishIntent("publish", "a" * 32, "fixture", "2026-11-12T00:00:00Z",
            CoordinationAddress("b" * 32, revision="c" * 32), Destination.local(str(root)), (), (), ())
        marker = marker_record(intent, world_id="d" * 32, epoch="e" * 64, selection=(node.id,))
        Corpus(root).add(marker)
        require_publication_layout(tuple(ReadContext.open(dataclasses.replace(cfg, write_root=root,
            world=dataclasses.replace(cfg.world, corpus_roots=(root,)))).write_view().iter_stored()))
        cfg = dataclasses.replace(cfg, world=dataclasses.replace(cfg.world,
            corpus_roots=cfg.world.corpus_roots + (root,)))
    else:
        cfg = dataclasses.replace(cfg, coordination=None)
    ctx = ReadContext.open(cfg)
    with session_records(ctx) as records:
        result = ctx.authoring_snapshot(records=records)
        assert result.resolve(cfg.profile.sorts["testing/witness"], node.id) is TermOutcome.NOT_MEMBER
    if excluded == "rejected":
        # An accepted equal copy can supply membership despite the rejected carrier.
        Corpus(cfg.write_root).add(node)
        ctx = ReadContext.open(cfg)
        with session_records(ctx) as records:
            assert ctx.authoring_snapshot(records=records).resolve(
                cfg.profile.sorts["testing/witness"], node.id) is TermOutcome.MEMBER


def test_read_snapshot_scope_uses_only_selected_capture(certified_work, monkeypatch):
    from beliefs.root import open_corpus
    from helpers.analysis import bootstrap_analysis, analysis_nodes
    from helpers.world import FIXTURE_AUTHORITY, build_two_corpus_world
    from science.world_belief import publish_session_epoch
    _world_kind_contract(monkeypatch)
    cfg = build_two_corpus_world(certified_work)
    bootstrap_analysis(cfg)
    candidate = analysis_nodes(cfg.profile)[0].id
    # Stop after actual context/snapshot construction until Task 6's keyed seam.
    monkeypatch.setattr("science.closure.evaluate", lambda view, prop, **kw: kw["resolution"])
    local = dataclasses.replace(cfg, coordination=None)
    result = ReadContext.open(local).evaluate("proposition:archived")
    assert result.resolve(cfg.profile.sorts["testing/witness"], candidate) is TermOutcome.NOT_MEMBER
    publish_session_epoch(cfg)
    result = ReadContext.open(cfg).evaluate("proposition:archived")
    assert result.resolve(cfg.profile.sorts["testing/witness"], candidate) is TermOutcome.MEMBER
    from dataclasses import replace
    from beliefs import stored
    from beliefs.procedure import procedure_from_stored
    later = stored.procedure_node(replace(procedure_from_stored(analysis_nodes(cfg.profile)[0]), name="Later"))
    open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(later)
    assert result.resolve(cfg.profile.sorts["testing/witness"], later.id) is TermOutcome.NOT_MEMBER
    with pytest.raises(Refused) as caught:
        ReadContext.open(cfg).evaluate("proposition:archived")
    assert caught.value.refusal.code == "epoch-stale"
