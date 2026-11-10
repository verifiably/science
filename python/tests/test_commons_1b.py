"""Real publication/update walks: overlap, acceptance, retention and missing ancestry."""
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from beliefs.intents.publish import Destination
from beliefs.world.registry import content_identity
from helpers.commons import (
    LOC_A, LOC_B, _b_publication, a_identity, b_derivation, build_installation, publish_again, read_rig, refused,
    reopen, transport_with, with_remotes,
)
from helpers.world import concept_list_address, fixture_bundle, level_list_address, open_rig
from science.acceptance import acceptance_inputs, statement
from science.config import ReadContext, corpus_id_at
from science.publication import marker_fields, marker_of
from science.sharing import SharingRegistry, sharing_lines
from science.supersession import classify, current, groups
from science.world_belief import publish_session_epoch
from test_commons_1a import _belief, _identity
from test_cmd_adopt import _adopt, _bind, _states
from test_mount_citations import _confine


def _shared(ids):
    return {ids[key] for key in ("proposition", "dataset", "spec", "run")} | {
        concept_list_address(), level_list_address()}


def _a_pins(installations):
    return tuple(pin for pin in SharingRegistry(installations.b.sharing_root).pins()
                 if pin.world == installations.a.world.world_id and pin.state == "mounted")


def _show(cfg, corpus_id):
    return read_rig(cfg, "show").invoke("show", {"corpus_id": corpus_id}).text


def _retired_lines(cfg):
    return [line for line in sharing_lines(cfg.operations_root) if line.transition == "retired"]


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


def test_the_unkept_branch_retires_the_predecessor_and_reports_it(b_updated_unkept):
    ids = a_identity(b_updated_unkept.a)
    registry = SharingRegistry(b_updated_unkept.b.sharing_root)
    (first,) = [pin for pin in registry.pins() if pin.world == ids["world"] and pin.corpus_id != ids["corpus_id"]]
    text = read_rig(b_updated_unkept.b, "show").invoke("show", {"corpus_id": first.corpus_id}).text
    assert "retention:\n  retired: yes\n" in text
    assert first.state == "retired"
    assert [pin.corpus_id for pin in _a_pins(b_updated_unkept)] == [ids["corpus_id"]]
    (line,) = [line for line in sharing_lines(b_updated_unkept.b.operations_root) if line.transition == "retired"]
    assert line.corpus == first.corpus_id and line.verdict == "retired"
    # `b_updated_unkept.b` is B's next open after the adoption.
    assert registry.root_for(ids["corpus_id"]) in b_updated_unkept.b.world.corpus_roots
    assert registry.root_for(first.corpus_id) not in b_updated_unkept.b.world.corpus_roots


@pytest.mark.parametrize("arrival", ["oldest-first", "newest-first"])
def test_two_sessions_mounting_a_gaps_ends_in_one_second_order_by_session_id(late_chain_unadopted, monkeypatch, arrival):
    installations, first, missing, last = late_chain_unadopted
    early, late = (first, last) if arrival == "oldest-first" else (last, first)
    monkeypatch.setattr("beliefs.session.writer.utc_now", lambda: "2026-10-28T00:00:00Z")
    ids = iter(("b" * 32, "a" * 32))
    monkeypatch.setattr("beliefs.session.secrets", SimpleNamespace(token_hex=lambda _n: next(ids)))
    # Adopt in reverse session-id order across two sequential sessions in the same second.
    with with_remotes(installations):
        for corpus in (early, late):
            with open_rig(installations.b, ("adopt",)) as (d, _):
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


def test_a_successor_dropping_the_spec_keeps_p1_for_bs_verification(spec_drop):
    ids = a_identity(spec_drop.a)
    (first,) = _a_pins(spec_drop)
    text = _adopt(spec_drop, LOC_A, ids["corpus_id"]).text
    registry = SharingRegistry(spec_drop.b.sharing_root)
    selection = marker_fields(marker_of(registry.root_for(ids["corpus_id"]))).selection
    assert {ids["assessment"], ids["run"]} <= selection and ids["spec"] not in selection
    assert f"retention {first.corpus_id}:\n  kept: dependency ({ids['spec']})\n" in text
    assert registry.pin(first.corpus_id).state == registry.pin(ids["corpus_id"]).state == "mounted"
    assert _retired_lines(spec_drop.b) == []
    shown = _show(spec_drop.b, first.corpus_id)
    assert f"this pin: superseded by {ids['corpus_id']}" in shown
    assert f"retention:\n  kept: dependency ({ids['spec']})\n" in shown


def test_a_successor_dropping_the_proposition_keeps_p1_for_bs_spec(spec_only):
    ids = a_identity(spec_only.a)
    (first,) = _a_pins(spec_only)
    text = _adopt(spec_only, LOC_A, ids["corpus_id"]).text
    registry = SharingRegistry(spec_only.b.sharing_root)
    assert marker_fields(marker_of(registry.root_for(ids["corpus_id"]))).selection == {
        ids["dataset"], concept_list_address(), level_list_address()}
    kinds = {node.kind for node in ReadContext.open(spec_only.b).write_view().iter_stored()}
    assert "analysis-spec" in kinds and not {"run", "assessment", "verification"} & kinds
    assert f"retention {first.corpus_id}:\n  kept: dependency ({ids['proposition']})\n" in text
    assert registry.pin(first.corpus_id).state == registry.pin(ids["corpus_id"]).state == "mounted"
    assert _retired_lines(spec_only.b) == []
    assert f"retention:\n  kept: dependency ({ids['proposition']})\n" in _show(spec_only.b, first.corpus_id)


@pytest.mark.parametrize("arrival", ["oldest-first", "newest-first"])
def test_the_late_link_resolves_the_chain_and_retires_both_non_tips(late_chain_unadopted, arrival):
    installations, first, missing, last = late_chain_unadopted
    early, late = (first, last) if arrival == "oldest-first" else (last, first)
    # One session: the two ends' `mounted` lines are ordered by ledger position, whatever their stamps.
    with with_remotes(installations), open_rig(installations.b, ("adopt",)) as (d, _):
        for corpus in (early, late):
            d.invoke("adopt", {"location": LOC_A, "corpus_id": corpus})
    registry = SharingRegistry(installations.b.sharing_root)
    lines = sharing_lines(installations.b.operations_root)
    (held,) = groups(registry, lines).values()
    outcome = classify(held)
    assert outcome.kind == "unresolved" and {pair[0] for pair in outcome.missing} == {missing}
    assert current(lines, held) == (early, registry.pin(early).marker)
    assert {pin.corpus_id: pin.state for pin in registry.pins()} == {first: "mounted", last: "mounted"}
    assert _retired_lines(installations.b) == []
    _adopt(installations, LOC_A, missing)
    retired = _retired_lines(installations.b)
    assert sorted(line.corpus for line in retired) == sorted((first, missing))
    assert all(line.verdict == "retired" for line in retired)
    assert {pin.corpus_id: pin.state for pin in registry.pins()} == {
        first: "retired", missing: "retired", last: "mounted"}
    (held,) = groups(registry, sharing_lines(installations.b.operations_root)).values()
    assert classify(held).kind == "resolved" and classify(held).tip[0] == last


def test_the_sweep_judges_each_predecessor_against_the_holders_the_last_retirement_left(equal_holders, monkeypatch):
    installations, first, equal, last = equal_holders
    ids = a_identity(installations.a)
    _adopt(installations, LOC_A, last)
    assert _retired_lines(installations.b) == []
    # The late link resolves P1 -> P2 -> P3: P1 is judged first, while P2 still holds the assessment.
    text = _adopt(installations, LOC_A, equal).text
    registry = SharingRegistry(installations.b.sharing_root)
    assert {pin.corpus_id: pin.state for pin in registry.pins()} == {
        first: "retired", equal: "mounted", last: "mounted"}
    assert [line.corpus for line in _retired_lines(installations.b)] == [first]
    assert f"retirement {first}:\n" in text
    assert f"retention {equal}:\n  kept: dependency ({ids['assessment']})\n" in text
    assert f"retention:\n  kept: dependency ({ids['assessment']})\n" in _show(installations.b, equal)
    b = reopen(installations.b)
    publish_session_epoch(b)
    assert ReadContext.open(b).cited(ids["assessment"]).corpus_id == equal
    _confine(monkeypatch)
    code, entrypoint, _ = fixture_bundle(installations.remotes.parent / "a")
    with open_rig(b, ("verify",)) as (d, _):
        text = d.invoke("verify", {"assessment": ids["assessment"], "code": str(code), "entrypoint": entrypoint}).text
    assert "[verification]" in text


def test_a_sibling_arriving_after_retirement_is_divergent_against_the_retired_copy(sibling_publications_unkept):
    installations, first, sibling = sibling_publications_unkept
    (predecessor,) = _a_pins(installations)
    _adopt(installations, LOC_A, first)
    registry = SharingRegistry(installations.b.sharing_root)
    assert registry.pin(predecessor.corpus_id).state == "retired"
    (held,) = [group for group in groups(registry, sharing_lines(installations.b.operations_root)).values()
               if any(item.corpus_id == first for item in group)]
    assert {item.corpus_id: item.state for item in held} == {predecessor.corpus_id: "retired", first: "mounted"}
    refusal = refused(lambda: _adopt(installations, LOC_A, sibling))
    assert refusal.code == "divergent-publication" and {pair[0] for pair in refusal.data["tips"]} == {first, sibling}
    assert registry.pin(sibling).state == "fetched"
    assert not ReadContext.open(installations.b).world.status(sibling).known
    assert registry.pin(first).state == "mounted" and registry.pin(predecessor.corpus_id).state == "retired"


def test_a_late_kept_predecessor_refuses_chain_retired_naming_the_retired_intermediate(late_chain_unadopted):
    installations, first, missing, last = late_chain_unadopted
    _adopt(installations, LOC_A, missing)
    _adopt(installations, LOC_A, last)
    registry = SharingRegistry(installations.b.sharing_root)
    assert registry.pin(missing).state == "retired"
    keeping = replace(installations, b=replace(installations.b, keep=(first,)))
    refusal = refused(lambda: _adopt(keeping, LOC_A, first))
    assert refusal.code == "adopt-conflict"
    assert refusal.data == {"rule": "chain-retired", "addresses": [], "corpus": missing}
    assert missing in refusal.message
    assert registry.pin(first).state == "fetched"
    assert not ReadContext.open(installations.b).world.status(first).known
    assert registry.pin(last).state == "mounted"


def test_a_publication_naming_a_pending_predecessor_keeps_it_by_attribution(updated_unkept, monkeypatch):
    ids = a_identity(updated_unkept.a, binding_destination=LOC_A)
    (first,) = [pin.corpus_id for pin in _a_pins(updated_unkept)]
    q = _b_publication(updated_unkept.b).corpus_id
    reader = build_installation(updated_unkept.remotes.parent, "c", hold_vocabulary=False)
    value = replace(updated_unkept, b=reader)
    _bind(value, LOC_A, first, ids["world"])
    _adopt(value, LOC_A, first)

    def crash(*args):
        raise RuntimeError("injected crash before sweep")

    with monkeypatch.context() as patch:
        patch.setattr("science.commands.adopt._reevaluate", crash)
        with pytest.raises(RuntimeError, match="injected crash before sweep"):
            _adopt(value, LOC_A, ids["corpus_id"])
    registry = SharingRegistry(reader.sharing_root)
    assert registry.pin(first).state == registry.pin(ids["corpus_id"]).state == "mounted"
    assert "retention:\n  pending: rerun adopt\n" in _show(reader, first)
    _bind(value, LOC_B, q, updated_unkept.b.world.world_id)
    text = _adopt(value, LOC_B, q).text
    assert _states(text) == ["fetched", "admitted", "mounted"]
    attributions = marker_fields(marker_of(registry.root_for(q))).attributions
    assert ids["assessment"] in attributions and {origin for origin, _ in attributions.values()} == {first}
    assert f"retention {first}:\n  kept: attribution (named by {q})\n" in text
    assert registry.pin(first).state == registry.pin(q).state == "mounted"
    assert ReadContext.open(reader).world.status(first).live
    assert _retired_lines(reader) == []
    assert f"retention:\n  kept: attribution (named by {q})\n" in _show(reader, first)


def test_a_chain_kept_for_bs_verification_keeps_the_intermediate_and_retires_nothing(b_updated):
    middle = a_identity(b_updated.a)["corpus_id"]
    (first,) = [pin.corpus_id for pin in _a_pins(b_updated) if pin.corpus_id != middle]
    tip = publish_again(b_updated, LOC_A)
    ids = a_identity(b_updated.a)
    text = _adopt(b_updated, LOC_A, tip).text
    assert f"retention {first}:\n  kept: dependency ({ids['assessment']})\n" in text
    assert f"retention {middle}:\n  kept: chain (for {first})\n" in text
    assert {pin.corpus_id for pin in _a_pins(b_updated)} == {first, middle, tip}
    assert _retired_lines(b_updated.b) == []
    assert f"retention:\n  kept: chain (for {first})\n" in _show(b_updated.b, middle)


def test_writes_after_an_in_session_retirement_refuse_corpus_retired(updated_unkept):
    ids = a_identity(updated_unkept.a, binding_destination=LOC_A)
    (first,) = [pin.corpus_id for pin in _a_pins(updated_unkept)]
    cfg = updated_unkept.b
    code, entrypoint, _ = fixture_bundle(updated_unkept.remotes.parent / "a")
    destination = cfg.world.world_root.parent / "guarded-publication"
    commands = ("adopt", "verify", "publish-preview", "publish")
    with with_remotes(updated_unkept), open_rig(cfg, commands) as (d, ctx):
        d.invoke("adopt", {"location": LOC_A, "corpus_id": ids["corpus_id"]})
        assert SharingRegistry(cfg.sharing_root).pin(first).state == "retired"
        assert first in ctx.session_ids()
        before = tuple(ctx.write_view().iter_stored())
        verify = refused(lambda: d.invoke("verify", {"assessment": ids["assessment"], "code": str(code),
                                                     "entrypoint": entrypoint}))
        publications = [refused(lambda: d.invoke(command, {"target": "b", "to": str(destination)}))
                        for command in ("publish-preview", "publish")]
        assert tuple(ctx.write_view().iter_stored()) == before
    assert verify.code == "corpus-retired" and verify.data == {"corpus": first, "record": ids["assessment"]}
    assert "reopen the session" in verify.message
    for refusal in publications:
        assert refusal.code == "corpus-retired" and refusal.data == {"corpus": first}
        assert first in refusal.message and "reopen the session" in refusal.message
    assert not destination.exists()
