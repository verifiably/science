"""Real publication/update walks: overlap, acceptance, retention and missing ancestry."""
import json
from dataclasses import replace

import pytest

from beliefs.intents.publish import Destination
from beliefs.world.registry import content_identity
from helpers.commons import (
    LOC_A, a_identity, b_derivation, read_rig, refused, transport_with, with_remotes,
)
from helpers.world import concept_list_address, fixture_bundle, level_list_address, open_rig
from science.acceptance import acceptance_inputs, statement
from science.config import ReadContext, corpus_id_at
from science.publication import marker_fields, marker_of
from science.sharing import SharingRegistry, sharing_lines
from science.supersession import classify, current, groups
from science.world_belief import publish_session_epoch
from test_commons_1a import _belief, _identity
from test_mount_citations import _confine


def _shared(ids):
    return {ids[key] for key in ("proposition", "dataset", "spec", "run")} | {
        concept_list_address(), level_list_address()}


def _a_pins(installations):
    return tuple(pin for pin in SharingRegistry(installations.b.sharing_root).pins()
                 if pin.world == installations.a.world.world_id and pin.state == "mounted")


def test_overlap_reads_each_shared_record_once(overlapping):
    ids = a_identity(overlapping.a)
    (carrier,) = SharingRegistry(overlapping.a.sharing_root).pins()
    ctx = ReadContext.open(overlapping.a)
    epoch, _, context = ctx._world_inputs
    holders = tuple(sorted((corpus_id_at(overlapping.a.write_root), carrier.corpus_id)))
    records = tuple(epoch.view.iter_stored())
    for address in _shared(ids) | {ids["assessment"]}:
        assert sum(node.id == address for node in records) == 1
        assert epoch.view.holders_of(address) == holders
    assert set(context.pins) == set(holders)


def test_belief_under_empty_accept_lists_two_excluded_lines(overlapping):
    ids = a_identity(overlapping.a)
    own = b_derivation(overlapping.b)
    (carrier,) = SharingRegistry(overlapping.a.sharing_root).pins()
    _, context = _belief(overlapping.a, ids["proposition"])
    assert {key: value for key, value in context.items() if key.startswith("excluded")} == {
        f"excluded {ids['assessment']} ({carrier.corpus_id})":
            f"corpus {carrier.corpus_id}; copy of a record that counts through corpus {corpus_id_at(overlapping.a.write_root)}",
        f"excluded {own['assessment']} ({carrier.corpus_id})":
            f"corpus {carrier.corpus_id}; world {overlapping.b.world.world_id}",
    }
    gathered = ReadContext.open(overlapping.a).gather_inputs(ids["proposition"])
    assert [item.identity() for item in gathered.assessments] == [_identity(overlapping.a, ids["assessment"])]


def test_belief_under_accept_b_counts_as_own_assessment_through_the_write_root(overlapping):
    ids = a_identity(overlapping.a)
    own = b_derivation(overlapping.b)
    accepting = replace(overlapping.a, accept=(overlapping.b.world.world_id,))
    (carrier,) = SharingRegistry(accepting.sharing_root).pins()
    _, context = _belief(accepting, ids["proposition"])
    assert {key: value for key, value in context.items() if key.startswith("excluded")} == {
        f"excluded {ids['assessment']} ({carrier.corpus_id})":
            f"corpus {carrier.corpus_id}; copy of a record that counts through corpus {corpus_id_at(accepting.write_root)}",
    }
    gathered = ReadContext.open(accepting).gather_inputs(ids["proposition"])
    assert sorted(item.identity() for item in gathered.assessments) == sorted([
        _identity(accepting, ids["assessment"]), _identity(accepting, own["assessment"]),
    ])


def test_the_update_supersedes_p1_and_drops_only_the_assessment(updated):
    ids = a_identity(updated.a)
    (first,) = _a_pins(updated)
    registry = SharingRegistry(updated.b.sharing_root)
    original = marker_fields(marker_of(registry.root_for(first.corpus_id)))
    root, _ = transport_with(updated).fetch_corpus(
        Destination.remote(LOC_A), ids["corpus_id"], updated.remotes.parent / "inspect-update")
    successor = marker_fields(marker_of(root))
    assert successor.supersedes == ((first.corpus_id, first.marker),)
    assert successor.selection == _shared(ids)
    assert original.selection - successor.selection == {ids["assessment"]}
    assert successor.attributions == {}


def test_b_adopting_the_update_keeps_p1_by_dependency_and_show_says_why(b_updated, monkeypatch):
    ids = a_identity(b_updated.a)
    (first,) = [pin for pin in _a_pins(b_updated) if pin.corpus_id != ids["corpus_id"]]
    text = read_rig(b_updated.b, "show").invoke("show", {"corpus_id": first.corpus_id}).text
    assert f"this pin: superseded by {ids['corpus_id']}" in text
    assert f"kept: dependency ({ids['assessment']})" in text
    accepting = replace(b_updated.b, accept=(ids["world"],))
    ctx = ReadContext.open(accepting)
    assert ctx.cited(ids["assessment"]).corpus_id == first.corpus_id
    gathered = ctx.gather_inputs(ids["proposition"])
    assessment = _identity(accepting, ids["assessment"])
    assert sum(item.identity() == assessment for item in gathered.assessments) == 1
    assert sum(item.assessment == assessment for item in gathered.verifications) == 1
    _confine(monkeypatch)
    code, entrypoint, _ = fixture_bundle(b_updated.remotes.parent / "a")
    with open_rig(accepting, ("verify",)) as (d, _):
        text = d.invoke("verify", {"assessment": ids["assessment"], "code": str(code),
                                   "entrypoint": entrypoint}).text
    assert "[verification]" in text


def test_shared_records_of_the_two_revisions_read_once_at_b(b_updated):
    ids = a_identity(b_updated.a)
    ctx = ReadContext.open(b_updated.b)
    epoch, _, context = ctx._world_inputs
    holders = tuple(sorted(pin.corpus_id for pin in _a_pins(b_updated)))
    records = tuple(epoch.view.iter_stored())
    for address in _shared(ids):
        assert sum(node.id == address for node in records) == 1
        assert epoch.view.holders_of(address) == holders
    assert set(holders) <= set(context.pins)


def test_both_sides_gather_equal_identities_for_the_shared_records(b_updated):
    ids = a_identity(b_updated.a)
    # A's publication binding moved after its overlap epoch.
    publish_session_epoch(b_updated.a)
    contexts = [ReadContext.open(replace(cfg, accept=(other.world.world_id,)))
                for cfg, other in ((b_updated.a, b_updated.b), (b_updated.b, b_updated.a))]
    contents, assessments, statements = [], [], []
    for ctx in contexts:
        world = ctx.world_read().view
        contents.append({address: content_identity(world.get(address)) for address in _shared(ids)})
        assert all(len(world.holders_of(address)) == 2 for address in _shared(ids))
        gathered = ctx.gather_inputs(ids["proposition"])
        assessments.append(sorted(item.identity() for item in gathered.assessments))
        for key in ("dataset", "run"):
            assert gathered.node_corpus[ids[key]] == world.holders_of(ids[key])
        answer = ctx.evaluate(ids["proposition"])
        assert answer.acceptance.statement == statement(acceptance_inputs(ctx))
        parsed = json.loads(answer.acceptance.statement)
        assert parsed["own_roots"] == [corpus_id_at(ctx.config.write_root)]
        assert parsed["verifiers"] == sorted((b_updated.a.world.world_id, b_updated.b.world.world_id))
        statements.append(answer.acceptance.statement)
    assert contents[0] == contents[1]
    assert assessments[0] == assessments[1]
    assert statements[0] != statements[1]


def test_the_unkept_branch_reports_retirement_pending_and_retention_pending(b_updated_unkept):
    ids = a_identity(b_updated_unkept.a)
    (first,) = [pin for pin in _a_pins(b_updated_unkept) if pin.corpus_id != ids["corpus_id"]]
    text = read_rig(b_updated_unkept.b, "show").invoke("show", {"corpus_id": first.corpus_id}).text
    assert "retention:\n  pending: no door\n" in text
    assert all(pin.state == "mounted" for pin in _a_pins(b_updated_unkept))
    assert not [line for line in sharing_lines(b_updated_unkept.b.operations_root) if line.transition == "retired"]


@pytest.mark.parametrize("arrival", ["oldest-first", "newest-first"])
def test_two_sessions_mounting_a_gaps_ends_in_one_second_order_by_session_id(late_chain_unadopted, monkeypatch, arrival):
    installations, first, missing, last = late_chain_unadopted
    early, late = (first, last) if arrival == "oldest-first" else (last, first)
    monkeypatch.setattr("beliefs.session.writer.utc_now", lambda: "2026-10-28T00:00:00Z")
    # Open both first, then adopt in reverse id order to distinguish sorting from wall-clock arrival.
    with with_remotes(installations), open_rig(installations.b, ("adopt",)) as (one, _), \
            open_rig(installations.b, ("adopt",)) as (two, _):
        ordered = sorted((one, two), key=lambda d: d._session.session_id)
        for d, corpus in ((ordered[1], early), (ordered[0], late)):
            d.invoke("adopt", {"location": LOC_A, "corpus_id": corpus})
    registry = SharingRegistry(installations.b.sharing_root)
    lines = sharing_lines(installations.b.operations_root)
    mounted = [line for line in lines if line.transition == "mounted"]
    assert [line.at for line in mounted] == ["2026-10-28T00:00:00Z"] * 2
    assert [line.corpus for line in mounted] == [late, early]
    (held,) = groups(registry, lines).values()
    outcome = classify(held)
    assert outcome.kind == "unresolved" and {pair[0] for pair in outcome.missing} == {missing}
    assert current(lines, held) == (late, registry.pin(late).marker)
    assert all(pin.state == "mounted" for pin in registry.pins())
    assert not any(line.transition == "retired" for line in lines)


def test_publish_in_the_late_link_state_refuses_attribution_ambiguous_naming_the_link(late_link):
    installations, missing = late_link
    registry = SharingRegistry(installations.b.sharing_root)
    pins = _a_pins(installations)
    (pair,) = {pair for pin in pins for pair in marker_fields(marker_of(registry.root_for(pin.corpus_id))).supersedes
              if pair[0] == missing}
    destination = installations.remotes / "publish-refusal"
    destination.mkdir()
    with open_rig(installations.b, ("publish",)) as (d, _):
        refusal = refused(lambda: d.invoke("publish", {"target": "b", "to": str(destination)}))
    assert refusal.code == "kernel-refused" and refusal.data["reason"] == "attribution-ambiguous"
    assert f"adopt {pair[0]} {pair[1]}" in refusal.message
    assert all(f"{pin.corpus_id}:{pin.marker}" in refusal.message for pin in pins)
    assert list(destination.iterdir()) == []
