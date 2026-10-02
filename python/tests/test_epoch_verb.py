"""Consumer spec decisions 7, 8 and 12: an epoch is current for a session only
at exact coverage with no drift; `science epoch` builds one or reuses it."""
import dataclasses
import json

import pytest

from beliefs.root import chain_head_reader, init_corpus_root, open_corpus, open_world
from beliefs.consulted import CorpusPins
from beliefs.corpus import Finding
from beliefs.world import Fresh, WorldConfig
from helpers.world import (
    FIXTURE_AUTHORITY, QUERY, add_mounted_evidence, build_shared_contract_world,
    fixture_proposition_node, mount_config, open_rig, write_shared_config,
)
from science.cli import main
from science.config import ReadContext
from science.refusal import Refused
import science.world_belief as world_belief
from science.world_belief import build_over, epoch_currency, publish_session_epoch
from beliefs.errors import AddressMapConflict, BuildContended, ResolutionRefused


@pytest.fixture
def shared(certified_work):
    cfg = build_shared_contract_world(certified_work)
    add_mounted_evidence(cfg, certified_work)
    return cfg


def _refusal(cfg):
    ctx = ReadContext.open(cfg)
    with pytest.raises(Refused) as caught:
        epoch_currency(ctx.world, ctx.session_ids())
    return caught.value.refusal


def test_no_epoch_refuses_naming_the_remedy(shared):
    refusal = _refusal(shared)
    assert refusal.code == "no-epoch" and "science epoch" in refusal.message


def test_the_verb_builds_over_exactly_the_session_corpora(shared):
    published = publish_session_epoch(shared)
    assert published.state == "built"
    assert frozenset(cid for cid, _ in published.coverage) == ReadContext.open(shared).session_ids()
    ctx = ReadContext.open(shared)
    assert epoch_currency(ctx.world, ctx.session_ids()).epoch.packaging_identity == published.packaging_identity


def test_a_rerun_with_nothing_changed_builds_nothing(shared):
    """Review round 1, P2 3: a second build would anchor a moved chain head and
    mint a new identity, so the verb reuses a current epoch. Production-backed:
    no chain head is injected."""
    first = publish_session_epoch(shared)
    world_root = shared.world.world_root
    pointer = (world_root / "epochs" / "current").read_bytes()
    head = chain_head_reader()(world_root)
    again = publish_session_epoch(shared)
    assert again.state == "current" and again.packaging_identity == first.packaging_identity
    assert (world_root / "epochs" / "current").read_bytes() == pointer
    assert chain_head_reader()(world_root) == head


def test_a_write_root_write_makes_it_stale_and_the_verb_rebuilds(shared):
    first = publish_session_epoch(shared)
    open_corpus(shared.write_root, authority=FIXTURE_AUTHORITY, profile=shared.profile).add(
        fixture_proposition_node("later"))
    refusal = _refusal(shared)
    write_id = ReadContext.open(shared).cited("proposition:later").corpus_id
    assert refusal.code == "epoch-stale" and refusal.data["drifted"] == [write_id]
    rebuilt = publish_session_epoch(shared)
    assert rebuilt.state == "built" and rebuilt.packaging_identity != first.packaging_identity


def test_a_coordination_write_after_the_epoch_makes_it_stale(shared):
    """Strict drift (plan review round 1, P1): nothing proves a coordination
    write left mapped content unchanged, so it is drift like any other."""
    publish_session_epoch(shared)
    with open_rig(shared, ("project",)) as (d, _):
        d.invoke("project", {"name": "health", "query": QUERY})
    refusal = _refusal(shared)
    write_id = next(m.corpus_id for m in ReadContext.open(shared).session_mounts() if m.root == shared.write_root)
    assert refusal.code == "epoch-stale" and refusal.data["drifted"] == [write_id]
    assert publish_session_epoch(shared).state == "built"
    ctx = ReadContext.open(shared)
    epoch_currency(ctx.world, ctx.session_ids())


def test_a_project_minted_before_the_epoch_leaves_it_current(shared):
    """The epoch maps only world kinds, so a coordination record it leaves
    unmapped at an unchanged state is not drift."""
    with open_rig(shared, ("project",)) as (d, _):
        d.invoke("project", {"name": "health", "query": QUERY})
    publish_session_epoch(shared)
    ctx = ReadContext.open(shared)
    epoch_currency(ctx.world, ctx.session_ids())


def test_a_mapped_facet_change_beside_a_coordination_write_is_stale(shared):
    """The plan-review P1 regression: a mapped dataset's facet revised in the
    mount alongside a new coordination record in the write root. The view
    would serve the changed facet; currency must refuse, naming both."""
    publish_session_epoch(shared)
    mounted = mount_config(shared)
    writer = open_corpus(mounted.write_root, authority=FIXTURE_AUTHORITY, profile=mounted.profile)
    (dataset,) = [n for n in ReadContext.open(mounted).write_view().iter_stored()
                  if n.kind == "dataset" and "empirical-observation" in n.facets]
    candidate = dataset.model_copy(deep=True)
    candidate.facets["empirical-observation"] = {"locator": "accession:GSE-REVISED", "attested_by": "fixture"}
    writer.revise(candidate)
    with open_rig(shared, ("project",)) as (d, _):
        d.invoke("project", {"name": "health", "query": QUERY})
    refusal = _refusal(shared)
    assert refusal.code == "epoch-stale"
    assert refusal.data["drifted"] == sorted(ReadContext.open(shared).session_ids())


def test_contention_while_checking_an_existing_epoch_is_a_named_refusal(shared, monkeypatch):
    """Plan review round 1, P2: opening the view takes every covered corpus's
    capture hold, so a busy corpus refuses here too, never internal-error."""
    publish_session_epoch(shared)

    def contended(*_, **__):
        raise BuildContended("an epoch build cannot capture this root: its operation lock is held")

    monkeypatch.setattr(world_belief, "open_world_view", contended)
    with pytest.raises(Refused) as caught:
        publish_session_epoch(shared)
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "BuildContended"


def test_a_world_the_kernel_refuses_to_resolve_is_a_named_refusal(shared, monkeypatch):
    """A uid held by two corpora is the kernel's W8b refusal at view open; it
    reaches the reader named, never as a raw exception."""
    publish_session_epoch(shared)

    def refused(*_, **__):
        raise ResolutionRefused("uid 'u' is held by both a and b; world uid uniqueness is enforced")

    monkeypatch.setattr(world_belief, "open_world_view", refused)
    ctx = ReadContext.open(shared)
    with pytest.raises(Refused) as caught:
        epoch_currency(ctx.world, ctx.session_ids())
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "ResolutionRefused"


def test_a_mapped_record_deleted_after_the_epoch_is_rebuilt_over(shared):
    """Final review I2: a mapped record the carrier no longer holds makes the
    kernel refuse the old epoch's view (`ResolutionRefused`). The read names
    the remedy, and the remedy runs: `science epoch` rebuilds over the present
    corpora rather than re-raising the old epoch's refusal."""
    publish_session_epoch(shared)
    mount_root = next(root for root in shared.world.corpus_roots if root != shared.write_root)
    profile = ReadContext.open(shared)._profiles[mount_root]
    open_corpus(mount_root, authority=FIXTURE_AUTHORITY, profile=profile).delete("proposition:fresh")
    refusal = _refusal(shared)
    assert refusal.code == "kernel-refused" and refusal.data["kind"] == "ResolutionRefused"
    assert "science epoch" in refusal.message
    assert publish_session_epoch(shared).state == "built"
    ctx = ReadContext.open(shared)
    epoch_currency(ctx.world, ctx.session_ids())


def test_coverage_missing_a_session_corpus_is_stale(shared):
    ctx = ReadContext.open(shared)
    write_id = next(m.corpus_id for m in ctx.session_mounts() if m.root == shared.write_root)
    build_over(shared, ctx.session_ids() - {write_id})
    refusal = _refusal(shared)
    assert refusal.code == "epoch-stale" and refusal.data["missing"] == [write_id] and refusal.data["extra"] == []


def test_coverage_with_an_extra_corpus_is_stale_and_the_verb_rebuilds_exactly(shared, certified_work):
    """Review round 1, P2 2: an epoch another configuration published over a
    superset would read the extra corpus as absent and answer
    unavailable-corpus-absent."""
    extra_root = certified_work / "extra"
    init_corpus_root(extra_root, authority=FIXTURE_AUTHORITY)
    profile = ReadContext.open(shared)._profiles[shared.write_root]
    open_corpus(extra_root, authority=FIXTURE_AUTHORITY, profile=profile).adopt_manifest(profile=CorpusPins(
        science_contract="science:" + profile.base_contract_identity,
        domains={ns: f"{ns}:{identity}" for ns, identity in profile.activated_contracts.items()}))
    wide = dataclasses.replace(shared, world=WorldConfig(
        shared.world.world_root, shared.world.world_id, shared.world.corpus_roots + (extra_root,)))
    open_world(wide.world, authority=FIXTURE_AUTHORITY).admit(extra_root, provenance=Fresh())
    extra_id = next(m.corpus_id for m in ReadContext.open(wide).mounts() if m.root == extra_root)
    build_over(wide, ReadContext.open(wide).session_ids())
    refusal = _refusal(shared)
    assert refusal.code == "epoch-stale" and refusal.data["extra"] == [extra_id] and refusal.data["missing"] == []
    rebuilt = publish_session_epoch(shared)
    assert rebuilt.state == "built"
    assert frozenset(cid for cid, _ in rebuilt.coverage) == ReadContext.open(shared).session_ids()


_DUPLICATE = Finding(severity="error", code="duplicate-location", ref="proposition:twice",
                     detail="corpus claims=('a', 'b')", message="one canonical address, several records")


@pytest.mark.parametrize("raised", [
    BuildContended("an epoch build cannot capture this root: its operation lock is held"),
    ResolutionRefused("uid 'u' is held by both a and b; world uid uniqueness is enforced"),
    AddressMapConflict(_DUPLICATE),
], ids=lambda raised: type(raised).__name__)
def test_a_kernel_refusal_from_the_build_is_named(shared, monkeypatch, raised):
    """A busy corpus (`BuildContended`), and a build the kernel will not resolve
    or map (final review I2), each refuse named, never internal-error."""
    def refused(*_, **__):
        raise raised

    monkeypatch.setattr(world_belief, "build_epoch", refused)
    with pytest.raises(Refused) as caught:
        publish_session_epoch(shared)
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == type(raised).__name__


def test_the_cli_verb_refuses_on_the_wire(shared, monkeypatch, capsys):
    """Final review M9: the verb's refusal path is the CLI's, exit 3 and the
    refusal envelope on stderr."""
    def contended(*_, **__):
        raise BuildContended("an epoch build cannot capture this root: its operation lock is held")

    monkeypatch.setattr(world_belief, "build_epoch", contended)
    path = write_shared_config(shared)
    assert main(["epoch", "--config", str(path)]) == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    refusal = json.loads(captured.err.strip().splitlines()[-1])["refusal"]
    assert refusal["code"] == "kernel-refused" and refusal["data"] == {"kind": "BuildContended"}


def test_the_cli_verb_prints_built_then_current(shared, capsys):
    path = write_shared_config(shared)
    assert main(["epoch", "--config", str(path)]) == 0
    assert capsys.readouterr().out.startswith("built: ")
    assert main(["epoch", "--config", str(path)]) == 0
    assert capsys.readouterr().out.startswith("current: ")
