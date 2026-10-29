"""`show` (commons 1a, Task 11): one pin's state, source, kernel status, acceptance and verification picture,
reading B's registry, the kernel's registry and the session's records; it writes nothing."""
from dataclasses import replace

import pytest
from beliefs.coordination import CoordinationAddress

from helpers.commons import LOC_A, LOC_A2, a_identity, publish_again, read_rig, refused, write_commons_config
from test_cmd_adopt import _adopt, bound_fetched_only
from helpers.world import (
    LEVELS, WORKING_FIELDS, _minted_ref, concept_list_address, level_list_address, open_rig,
)

from science.config import ReadContext, load_config
from science.sharing import SharingRegistry

LAG = "registry lags the kernel: `adopt` reconciles it"


def _show(cfg, corpus_id: str) -> str:
    return read_rig(cfg, "show").invoke("show", {"corpus_id": corpus_id}).text


def test_show_is_read_only_over_its_declared_reads():
    from science.loader import production_tree
    decl = next(d for d in production_tree() if d.name == "show")
    assert decl.write_class.kind == "read-only"
    assert set(decl.reads) == {"registry", "corpus-stored"}


def test_show_a_mounted_origin_confirmed_pin(adopted):
    ids = a_identity(adopted.a)
    pin = SharingRegistry(adopted.b.sharing_root).pin(ids["corpus_id"])
    text = _show(adopted.b, ids["corpus_id"])
    for line in (f"## Pin: {ids['corpus_id']}", "state: mounted", f"world: {ids['world']}",
                 f"marker: {ids['marker']}", f"artifact: {ids['artifact']}", f"view: {pin.view}", "keep: no",
                 "kind: provider", f"reference: {LOC_A}", "confirmation: origin-confirmed",
                 f"location: {LOC_A}", f"at: {pin.fetch.at}", f"verdict: {pin.fetch.verdict}",
                 # B opened before the adopt: the kernel admitted the corpus, B's configuration carries no root of it.
                 "known: yes", "live: yes", "present: no",
                 "independence: not exposed by the kernel's inputs (Deviation 8)"):
        assert line in text, line
    assert LAG not in text


def test_show_distinguishes_accepted_evidence_from_confirmed_origin(reopened):
    ids = a_identity(reopened.a)
    unaccepted = _show(reopened.b, ids["corpus_id"])
    assert "confirmation: origin-confirmed" in unaccepted and "world accepted: no" in unaccepted
    assert "counts as evidence: no" in unaccepted and "present: yes" in unaccepted
    assert (f"{ids['assessment']}: counts no; verifications 0 from worlds none, 0 count under the policy"
            in unaccepted)
    accepted = _show(replace(reopened.b, accept=(ids["world"],)), ids["corpus_id"])
    assert "world accepted: yes" in accepted and "counts as evidence: yes" in accepted
    assert f"{ids['assessment']}: counts yes; verifications 0" in accepted


def test_show_keep_row_reads_the_configuration(reopened):
    corpus_id = a_identity(reopened.a)["corpus_id"]
    configured = replace(reopened.b, keep=(corpus_id,))
    loaded = load_config(write_commons_config(configured))
    assert "keep: yes" in _show(loaded, corpus_id)


def test_b_resolves_the_vocabulary_from_fetched_bytes_without_redeclaring(verified):
    ids = a_identity(verified.a)
    ctx = ReadContext.open(verified.b)
    assert ctx.cited(concept_list_address()).corpus_id == ids["corpus_id"]
    assert ctx.cited(level_list_address()).corpus_id == ids["corpus_id"]
    assert ctx.held_path(level_list_address()).read_bytes() == LEVELS
    assert not any(node.kind == "dataset" for node in ctx.write_view().iter_stored())
    with open_rig(verified.b, ("spec",)) as (d, _):
        text = d.invoke("spec", dict(WORKING_FIELDS, target=ids["proposition"], dataset=ids["dataset"])).text
    spec_b = _minted_ref(text, "analysis-spec")
    assert ReadContext.open(verified.b).own(spec_b)


def test_show_lists_bs_verification_of_as_assessment_once_minted(verified):
    # accept=(): A's assessment does not count, B's own verification of it does; both facts show
    ids = a_identity(verified.a)
    text = _show(verified.b, ids["corpus_id"])
    assert (f"{ids['assessment']}: counts no; verifications 1 from worlds {verified.b.world.world_id}, "
            "1 count under the policy") in text


def test_show_reports_a_registry_that_lags_the_kernel(adopted):
    ids = a_identity(adopted.a)
    registry = SharingRegistry(adopted.b.sharing_root)
    registry.write_pin(replace(registry.pin(ids["corpus_id"]), state="admitted"))
    text = _show(adopted.b, ids["corpus_id"])
    assert "state: admitted" in text and "known: yes" in text and "live: yes" in text
    assert f"! {LAG}" in text


def test_show_of_an_unknown_pin_refuses(adopted):
    refusal = refused(lambda: _show(adopted.b, "0" * 32))
    assert refusal.code == "invalid-input" and "0" * 32 in refusal.message


def test_show_a_tip_reports_current_and_tip(adopted):
    ids = a_identity(adopted.a)
    text = _show(adopted.b, ids["corpus_id"])
    pin = SharingRegistry(adopted.b.sharing_root).pin(ids["corpus_id"])
    view = str(CoordinationAddress.parse(pin.view).unpinned())
    assert (f"supersession:\n  group: {ids['world']} {view} {LOC_A}\n"
            f"  current: {ids['corpus_id']} {ids['marker']}\n  this pin: tip\n") in text
    assert "retention:" not in text


@pytest.mark.parametrize("kept", [False, True])
def test_show_a_superseded_pin_reports_configuration_or_pending(adopted, kept):
    first = a_identity(adopted.a)["corpus_id"]
    successor = publish_again(adopted, LOC_A)
    _adopt(adopted, LOC_A, successor)
    cfg = replace(adopted.b, keep=(first,) if kept else ())
    text = _show(cfg, first)
    assert f"this pin: superseded by {successor}" in text
    assert ("retention:\n  kept: configuration\n" if kept else "retention:\n  pending: no door\n") in text
    assert "retention:" not in _show(cfg, successor)


def test_show_an_unlinked_second_destination_reports_it(conflicting_publication):
    installations, second = conflicting_publication
    first = a_identity(installations.a, binding_destination=LOC_A)["corpus_id"]
    _adopt(installations, LOC_A, first)
    _adopt(installations, LOC_A2, second)
    for corpus, other in ((first, second), (second, first)):
        text = _show(installations.b, corpus)
        assert f"this pin: unlinked chain beside {other}" in text
        assert "records attributed differently cannot be published while both chains are mounted" in text
        assert "retention:" not in text


@pytest.mark.xfail(strict=True, reason="Task 11 fixture: late_link returns (Installations, missing_link)")
def test_show_an_unresolved_group_names_the_link_to_adopt(request):
    installations, missing = request.getfixturevalue("late_link")
    registry = SharingRegistry(installations.b.sharing_root)
    from science.publication import marker_fields, marker_of
    mounted = [pin for pin in registry.pins() if pin.state == "mounted" and pin.world == installations.a.world.world_id]
    assert len(mounted) == 2
    links = {marker for pin in mounted
             for corpus, marker in marker_fields(marker_of(registry.root_for(pin.corpus_id))).supersedes
             if corpus == missing}
    (missing_marker,) = links
    for pin in mounted:
        assert f"current: unresolved: adopt {missing} {missing_marker}" in _show(installations.b, pin.corpus_id)


@pytest.mark.xfail(strict=True, reason="Task 11 fixture: updated returns Installations with P3 in A's binding")
def test_show_a_superseded_kept_pin_reports_every_reason(request):
    updated = request.getfixturevalue("updated")
    registry = SharingRegistry(updated.b.sharing_root)
    (first,) = [pin.corpus_id for pin in registry.pins() if pin.state == "mounted"]
    ids = a_identity(updated.a, binding_destination=LOC_A)
    _adopt(updated, LOC_A, ids["corpus_id"])
    text = _show(replace(updated.b, keep=(first,)), first)
    assert f"this pin: superseded by {ids['corpus_id']}" in text
    assert (f"retention:\n  kept: configuration\n  kept: dependency ({ids['assessment']})\n") in text


@pytest.mark.xfail(strict=True, reason="Task 11 fixture: updated_unkept returns Installations with P3 in A's binding")
def test_show_reports_pending_no_door_on_the_unkept_branch(request):
    updated = request.getfixturevalue("updated_unkept")
    registry = SharingRegistry(updated.b.sharing_root)
    (first,) = [pin.corpus_id for pin in registry.pins() if pin.state == "mounted"]
    _adopt(updated, LOC_A, a_identity(updated.a, binding_destination=LOC_A)["corpus_id"])
    assert "retention:\n  pending: no door\n" in _show(updated.b, first)


def test_show_uses_mounted_ledger_history_when_the_pin_file_lags(adopted):
    ids = a_identity(adopted.a)
    registry = SharingRegistry(adopted.b.sharing_root)
    registry.write_pin(replace(registry.pin(ids["corpus_id"]), state="fetched", source=None))
    text = _show(adopted.b, ids["corpus_id"])
    assert f"current: {ids['corpus_id']} {ids['marker']}" in text
    assert "this pin: tip" in text


@pytest.mark.parametrize("terminal", ["retired", "departed"])
def test_show_reports_only_an_explicit_retired_kernel_status_as_retired(adopted, monkeypatch, terminal):
    from beliefs.world import World
    from beliefs.world.registry import StatusRecord
    corpus = a_identity(adopted.a)["corpus_id"]
    status, registry = World.status, World.registry
    # The retirement door is not available yet; inject its complete parsed status reads.
    monkeypatch.setattr(World, "status", lambda world, target: replace(status(world, target), live=False)
                        if target == corpus else status(world, target))
    monkeypatch.setattr(World, "registry", lambda world: replace(registry(world), statuses=(
        StatusRecord(corpus, terminal, f"session:{'a' * 32}"),)))
    text = _show(adopted.b, corpus)
    assert "live: no" in text
    assert ("retention:\n  retired: yes\n" in text) is (terminal == "retired")


def test_show_an_intermediate_reports_configuration_and_chain(adopted):
    first = a_identity(adopted.a)["corpus_id"]
    second = publish_again(adopted, LOC_A)
    _adopt(adopted, LOC_A, second)
    third = publish_again(adopted, LOC_A)
    _adopt(adopted, LOC_A, third)
    text = _show(replace(adopted.b, keep=(first, second)), second)
    assert f"this pin: superseded by {third}" in text
    assert f"retention:\n  kept: configuration\n  kept: chain (for {first})\n" in text


def test_show_omits_supersession_without_an_authorized_established_group(adopted):
    registry = SharingRegistry(adopted.b.sharing_root)
    ids = a_identity(adopted.a)
    (adopted.b.sharing_root / "providers" / f"{ids['world']}.json").unlink()
    text = _show(adopted.b, ids["corpus_id"])
    assert "confirmation: unsourced" in text
    assert "supersession:" not in text and "retention:" not in text


def test_show_a_first_fetched_pin_has_no_current(bound_fetched_only):
    corpus = a_identity(bound_fetched_only.a)["corpus_id"]
    text = _show(bound_fetched_only.b, corpus)
    assert "state: fetched" in text
    assert "supersession:" not in text and "retention:" not in text


@pytest.mark.parametrize("divergent", [False, True])
def test_show_renders_parsed_unresolved_and_divergent_groups(adopted, monkeypatch, divergent):
    from beliefs.publication_arrival import DivergentPublication
    from science import supersession
    from science.publication import marker_fields, marker_of
    from science.sharing import sharing_lines
    registry = SharingRegistry(adopted.b.sharing_root)
    corpus = a_identity(adopted.a)["corpus_id"]
    root = registry.root_for(corpus)
    marker = marker_fields(marker_of(root))
    first = supersession.Held(corpus, root, marker, "mounted")
    second = replace(first, corpus_id="2" * 32, root=root / "second",
                     marker=replace(marker, uid="3" * 32, supersedes=((corpus, marker.uid),)))
    fourth = replace(first, corpus_id="4" * 32, root=root / "fourth",
                     marker=replace(marker, uid="5" * 32,
                                    supersedes=((corpus, marker.uid),) if divergent else (("6" * 32, "7" * 32),)))
    if divergent:
        first = replace(first, marker=replace(marker, supersedes=(("6" * 32, "7" * 32),)))
        fourth = replace(fourth, marker=replace(fourth.marker, supersedes=(("6" * 32, "7" * 32),)))
    held = (first, fourth) if divergent else (first, second, fourth)
    tips = ((first.corpus_id, first.marker.uid), (fourth.corpus_id, fourth.marker.uid)) if divergent else (
        (second.corpus_id, second.marker.uid), (fourth.corpus_id, fourth.marker.uid))
    history = sharing_lines(adopted.b.operations_root)
    mounted = next(line for line in history if line.transition == "mounted")
    history += (replace(mounted, corpus=fourth.corpus_id, marker=fourth.marker.uid),
                replace(mounted, corpus=second.corpus_id, marker=second.marker.uid))
    # Supply parsed filesystem/kernel inputs; the graph, current fold and rendering stay real.
    monkeypatch.setattr("science.commands.show.sharing_lines", lambda operations: history)
    monkeypatch.setattr(supersession, "groups", lambda registry, lines: {supersession.group_of(marker): held})
    monkeypatch.setattr(supersession, "publication_tip", lambda roots, view, destination:
                        DivergentPublication(tips))
    text = _show(adopted.b, corpus)
    if divergent:
        assert f"current: divergent: {first.corpus_id} {first.marker.uid}, {fourth.corpus_id} {fourth.marker.uid}" in text
        assert "this pin: sibling" in text
    else:
        assert f"current: unresolved: adopt {'6' * 32} {'7' * 32}" in text
        assert f"this pin: superseded by {second.corpus_id}" in text
    assert "retention:" not in text


@pytest.mark.parametrize("admitted", [False, True])
def test_live_retention_inputs_follow_kernel_admission_when_pin_state_lags(request, admitted):
    from science.config import live_mounts
    installations = request.getfixturevalue("adopted" if admitted else "bound_fetched_only")
    corpus = a_identity(installations.a)["corpus_id"]
    registry = SharingRegistry(installations.b.sharing_root)
    registry.write_pin(replace(registry.pin(corpus), state="fetched"))
    ctx = ReadContext.open(installations.b)
    assert ctx.world.status(corpus).known is admitted
    assert (corpus in {mount.corpus_id for mount in live_mounts(installations.b, ctx.world, registry)}) is admitted
