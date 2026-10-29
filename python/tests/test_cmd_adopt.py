"""`adopt` (commons 1a, Task 8): B fetches A's publication from a bound location, verifies it, sources it, checks
its layout and conflicts, then admits and mounts it. Every registry write follows the sharing line that is its
evidence, and nothing survives a refusal before `fetched`."""
import pytest
from beliefs.corpus import ReadView
from beliefs.session.ledger import LedgerReader, read_ledger_evidence
from beliefs.session.writer import ScopedWriter
from helpers.commons import (
    LOC_A,
    LOC_A2,
    LOC_B,
    Installations,
    a_identity,
    binding_ref,
    build_bound,
    publish_again,
    refused,
    reopen,
    transport_with,
    with_remotes,
)
from helpers.snapshot import snapshot
from helpers.world import hold_fixture_dataset, open_rig

from science.config import ReadContext
from science.publication import binding_fields, marker_fields, marker_of
from science.sharing import PinSource, ProviderBinding, SharingRegistry, replay
from science.world_belief import publish_session_epoch

LOC_OTHER = "https://remote.test/other"
NOT_A_CORPUS = "0" * 32
WORLD_FIRST = "0" * 32  # a world id that sorts before any world a fixture installation generates


def _adopt(installations, location: str, corpus_id: str):
    with with_remotes(installations), open_rig(installations.b, ("adopt",)) as (d, _):
        return d.invoke("adopt", {"location": location, "corpus_id": corpus_id})


def _bind(installations, location: str, corpus_id: str, world: str) -> None:
    with with_remotes(installations), open_rig(installations.b, ("provider-bind",)) as (d, _):
        d.invoke("provider-bind", {"location": location, "corpus_id": corpus_id, "world": world})


def _states(text: str) -> list[str]:
    return [line.split()[2] for line in text.splitlines() if line.startswith("[pin]")]


def _sharing_lines(cfg) -> list:
    """Every sharing line in `cfg`'s session ledgers, in time order."""
    lines = []
    for directory in sorted((cfg.operations_root / "sessions").iterdir()):
        evidence = read_ledger_evidence(cfg.operations_root, directory.name)
        if isinstance(evidence, LedgerReader):
            lines.extend(evidence.sharing())
    return sorted(lines, key=lambda line: line.at)


def _known(cfg, corpus_id: str) -> bool:
    return ReadContext.open(cfg).world.status(corpus_id).known


def _no_copy(registry: SharingRegistry, corpus_id: str) -> bool:
    root = registry.root_for(corpus_id)
    return not root.exists() and not registry.head_artifact_for(corpus_id).exists() and \
        not root.with_name(root.name + ".metadata").exists()


def build_bound_fetched_only(work):
    """`build_bound`, then an adopt that crashes as it reaches admission: B holds a `fetched` pin of A's corpus
    at LOC_A, with its copy, and the kernel has not admitted it."""
    value = build_bound(work)
    installations = Installations.of(value)

    def crash(*args, **kwargs):
        raise RuntimeError("injected crash before admission")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(ScopedWriter, "admit_publication", crash)
        with pytest.raises(RuntimeError, match="injected crash"):
            _adopt(installations, LOC_A, a_identity(installations.a)["corpus_id"])
    return value


@pytest.fixture
def bound_fetched_only(certified_worker_work):
    snap = snapshot(certified_worker_work, "commons-1a-bound-fetched-only", build_bound_fetched_only)
    snap.restore()
    return Installations.of(snap.value)


def test_adopt_unsourced_discards_the_copy_writes_no_pin_and_names_the_remedies(published):
    ids = a_identity(published.a)
    refusal = refused(lambda: _adopt(published, LOC_A, ids["corpus_id"]))
    assert refusal.code == "pin-unsourced" and refusal.data == {"world": ids["world"]}
    assert ids["world"] in refusal.message and "provider-bind" in refusal.message and "follow" in refusal.message
    registry = SharingRegistry(published.b.sharing_root)
    assert registry.pin(ids["corpus_id"]) is None and _no_copy(registry, ids["corpus_id"])
    assert not _known(published.b, ids["corpus_id"])
    assert _sharing_lines(published.b) == []


def test_adopt_after_bind_admits_and_marks_mounted(bound):
    ids = a_identity(bound.a)
    cid = ids["corpus_id"]
    text = _adopt(bound, LOC_A, cid).text
    assert _states(text) == ["fetched", "admitted", "mounted"]
    source = f"provider:{LOC_A}"
    lines = [line for line in _sharing_lines(bound.b) if line.transition != "bound"]
    assert [line.transition for line in lines] == ["fetched", "admitted", "mounted"]
    assert all(line.source == source and line.location == LOC_A and line.corpus == cid for line in lines)
    assert all(line.marker == ids["marker"] and line.artifact == ids["artifact"] for line in lines)
    pin = SharingRegistry(bound.b.sharing_root).pin(cid)
    assert pin.state == "mounted" and pin.source == PinSource("provider", LOC_A) and pin.fetch.location == LOC_A
    status = ReadContext.open(bound.b).world.status(cid)
    assert status.known and status.live


def test_a_location_bound_to_two_worlds_sources_the_publication_by_its_own_worlds_binding(bound):
    ids = a_identity(bound.a)
    cid = ids["corpus_id"]
    registry = SharingRegistry(bound.b.sharing_root)
    assert WORLD_FIRST < ids["world"]
    registry.write_binding(ProviderBinding(WORLD_FIRST, (LOC_A,), "2026-10-22T10:00:00Z", True))
    assert _states(_adopt(bound, LOC_A, cid).text) == ["fetched", "admitted", "mounted"]
    pin = registry.pin(cid)
    assert pin.state == "mounted" and pin.source == PinSource("provider", LOC_A) and pin.fetch.location == LOC_A


def test_a_location_bound_only_to_another_world_refuses_world_mismatch_naming_it(published):
    ids = a_identity(published.a)
    cid = ids["corpus_id"]
    registry = SharingRegistry(published.b.sharing_root)
    registry.write_binding(ProviderBinding(WORLD_FIRST, (LOC_A,), "2026-10-22T10:00:00Z", True))
    refusal = refused(lambda: _adopt(published, LOC_A, cid))
    assert refusal.code == "world-mismatch" and refusal.data == {"claimed": ids["world"], "bound": [WORLD_FIRST]}
    assert WORLD_FIRST in refusal.message and ids["world"] in refusal.message
    assert registry.pin(cid) is None and _no_copy(registry, cid) and not _known(published.b, cid)
    assert _sharing_lines(published.b) == []


def test_adopt_at_a_non_canonical_spelling_records_the_canonical_location(bound):
    cid = a_identity(bound.a)["corpus_id"]
    assert _states(_adopt(bound, "https://REMOTE.test:443/a", cid).text) == ["fetched", "admitted", "mounted"]
    pin = SharingRegistry(bound.b.sharing_root).pin(cid)
    assert pin.source == PinSource("provider", LOC_A) and pin.fetch.location == LOC_A


def test_adopt_from_a_local_path_refuses_before_any_line(bound):
    location = str(bound.remotes / "a.git")
    r = refused(lambda: _adopt(bound, location, a_identity(bound.a)["corpus_id"]))
    assert r.code == "invalid-input" and location in r.message and "https://" in r.message
    assert [line.transition for line in _sharing_lines(bound.b)] == ["bound"]


def test_a_retry_at_a_bound_location_that_does_not_hold_the_candidate_refuses_naming_it(published):
    ids = a_identity(published.a)
    cid = ids["corpus_id"]
    # A also publishes at LOC_B, and B binds LOC_B to A's world on that publication: LOC_B never holds `cid`.
    _bind(published, LOC_B, publish_again(published, LOC_B), ids["world"])
    assert refused(lambda: _adopt(published, LOC_A, cid)).code == "pin-unsourced"
    refusal = refused(lambda: _adopt(published, LOC_B, cid))
    assert refusal.code == "invalid-input" and LOC_B in refusal.message
    registry = SharingRegistry(published.b.sharing_root)
    assert registry.pin(cid) is None and _no_copy(registry, cid) and not _known(published.b, cid)


def test_a_fetched_pin_is_reused_only_at_its_own_location(bound_fetched_only):
    cid = a_identity(bound_fetched_only.a)["corpus_id"]
    registry = SharingRegistry(bound_fetched_only.b.sharing_root)
    assert registry.pin(cid).state == "fetched" and not _known(bound_fetched_only.b, cid)
    r = refused(lambda: _adopt(bound_fetched_only, LOC_OTHER, cid))
    assert r.code == "invalid-input" and LOC_A in r.message
    assert registry.pin(cid).state == "fetched"
    assert _states(_adopt(bound_fetched_only, LOC_A, cid).text) == ["admitted", "mounted"]
    assert registry.pin(cid).state == "mounted" and _known(bound_fetched_only.b, cid)


def test_a_registry_rebuilt_from_the_ledger_alone_matches_the_live_one(adopted, tmp_path):
    cid = a_identity(adopted.a)["corpus_id"]
    registry = SharingRegistry(adopted.b.sharing_root)
    rebuilt = SharingRegistry(tmp_path / "rebuilt")
    replay(rebuilt, adopted.b.operations_root)
    assert rebuilt.pin(cid) == registry.pin(cid) and rebuilt.bindings() == registry.bindings()


def test_the_adopted_root_is_a_corpus_root_at_the_next_open(adopted):
    ids = a_identity(adopted.a)
    cfg = reopen(adopted.b)
    assert SharingRegistry(adopted.b.sharing_root).root_for(ids["corpus_id"]) in cfg.world.corpus_roots
    assert ReadContext.open(cfg).cited(ids["proposition"]).corpus_id == ids["corpus_id"]


def test_publish_before_reopen_freezes_only_bs_own_view(adopted):
    # Before reopen B's session does not mount the adopted corpus, so B's epoch does not cover it: the kernel's
    # selection is complete over the covered corpora, and B's publication carries B's own records alone.
    cid = a_identity(adopted.a)["corpus_id"]
    own = hold_fixture_dataset(adopted.b, "b.txt", b"gene\tvalue\n", "expression")  # B's selection is not empty
    publish_session_epoch(adopted.b)
    with with_remotes(adopted), open_rig(adopted.b, ("publish",)) as (d, ctx):
        text = d.invoke("publish", {"target": "b", "to": LOC_B}).text
        binding = binding_fields(ctx.write_view().get(binding_ref(text)))
    into = adopted.remotes.parent / "fetched-b"
    root, _ = transport_with(adopted).fetch_corpus(binding.destination, binding.corpus_id, into)
    fields = marker_fields(marker_of(root))
    adopted_root = SharingRegistry(adopted.b.sharing_root).root_for(cid)
    a_addresses = {node.id for node in ReadView.opened_at(adopted_root).iter_stored()}
    assert fields.selection == {own} and not fields.selection & a_addresses
    assert fields.attributions == {}


def test_adopt_a_second_time_refuses_already_adopted(adopted):
    cid = a_identity(adopted.a)["corpus_id"]
    before = _sharing_lines(adopted.b)
    r = refused(lambda: _adopt(adopted, LOC_A, cid))
    assert r.code == "invalid-input" and "already adopted" in r.message
    assert _sharing_lines(adopted.b) == before


def test_an_equal_content_republication_passes_the_checklist_and_mounts(conflicting_publication):
    installations, cid2 = conflicting_publication
    ids = a_identity(installations.a, binding_destination=LOC_A)
    _adopt(installations, LOC_A, ids["corpus_id"])
    assert _states(_adopt(installations, LOC_A2, cid2).text) == ["fetched", "admitted", "mounted"]
    registry = SharingRegistry(installations.b.sharing_root)
    assert registry.pin(cid2).state == registry.pin(ids["corpus_id"]).state == "mounted"
    assert _known(installations.b, cid2)


def test_a_keep_entry_no_pin_records_is_a_finding(bound):
    from dataclasses import replace
    value = replace(bound, b=replace(bound.b, keep=(NOT_A_CORPUS,)))
    text = _adopt(value, LOC_A, a_identity(value.a)["corpus_id"]).text
    assert f"! keep entry {NOT_A_CORPUS}" in text and "no pin" in text


def test_adopt_of_an_absent_corpus_writes_nothing(bound):
    before = _sharing_lines(bound.b)
    r = refused(lambda: _adopt(bound, LOC_A, NOT_A_CORPUS))
    assert r.code == "invalid-input" and LOC_A in r.message and "absent" in r.message
    registry = SharingRegistry(bound.b.sharing_root)
    assert registry.pins() == () and _no_copy(registry, NOT_A_CORPUS)
    assert _sharing_lines(bound.b) == before


def _crash_on_write_pin(monkeypatch, state: str) -> None:
    write_pin = SharingRegistry.write_pin

    def crash(self, pin):
        if pin.state == state:
            raise RuntimeError(f"injected crash before the {state} pin write")
        write_pin(self, pin)

    monkeypatch.setattr(SharingRegistry, "write_pin", crash)


def test_a_crash_after_admission_before_the_pin_write_recovers_with_its_source(bound, monkeypatch):
    cid = a_identity(bound.a)["corpus_id"]
    registry = SharingRegistry(bound.b.sharing_root)
    _crash_on_write_pin(monkeypatch, "admitted")
    with pytest.raises(RuntimeError, match="injected crash"):
        _adopt(bound, LOC_A, cid)
    monkeypatch.undo()
    assert _known(bound.b, cid)
    assert registry.pin(cid).state == "fetched" and registry.pin(cid).source == PinSource("provider", LOC_A)
    text = _adopt(bound, LOC_A, cid).text
    assert _states(text) == ["mounted"]
    assert registry.pin(cid).state == "mounted" and registry.pin(cid).source == PinSource("provider", LOC_A)
    assert refused(lambda: _adopt(bound, LOC_A, cid)).code == "invalid-input"


def test_a_crash_between_the_mounted_line_and_the_pin_write_is_repaired_by_replay(bound, monkeypatch):
    cid = a_identity(bound.a)["corpus_id"]
    registry = SharingRegistry(bound.b.sharing_root)
    _crash_on_write_pin(monkeypatch, "mounted")
    with pytest.raises(RuntimeError, match="injected crash"):
        _adopt(bound, LOC_A, cid)
    monkeypatch.undo()
    assert registry.pin(cid).state == "admitted"
    (line,) = replay(registry, bound.b.operations_root)
    assert line.transition == "mounted" and line.source == f"provider:{LOC_A}"
    assert registry.pin(cid).state == "mounted" and registry.pin(cid).source == PinSource("provider", LOC_A)


def test_the_reopened_fixture_mounts_the_adopted_corpus_under_an_epoch_covering_it(reopened):
    from beliefs.world.read import current_epoch
    cid = a_identity(reopened.a)["corpus_id"]
    assert SharingRegistry(reopened.b.sharing_root).root_for(cid) in reopened.b.world.corpus_roots
    assert cid in dict(current_epoch(ReadContext.open(reopened.b).world).coverage)


def test_an_unrequired_equal_successor_reports_retirement_pending(adopted):
    cid1 = a_identity(adopted.a)["corpus_id"]
    cid2 = publish_again(adopted, LOC_A)
    text = _adopt(adopted, LOC_A, cid2).text
    assert "retirement pending" in text and "beliefs-a989fb" in text and cid1 in text
    assert _states(text) == ["fetched", "admitted", "mounted"]
    assert SharingRegistry(adopted.b.sharing_root).pin(cid1).state == "mounted"


def test_a_successor_reports_configuration_retention(adopted):
    from dataclasses import replace
    cid1 = a_identity(adopted.a)["corpus_id"]
    cid2 = publish_again(adopted, LOC_A)
    value = replace(adopted, b=replace(adopted.b, keep=(cid1,)))
    text = _adopt(value, LOC_A, cid2).text
    assert f"retention {cid1}:\n  kept: configuration" in text
    assert "retirement pending" not in text


def test_changed_configuration_refuses_before_pending_and_keeps_the_adoption(adopted):
    from dataclasses import replace
    cid2 = publish_again(adopted, LOC_A)
    cfg = reopen(adopted.b)
    path, _ = cfg.source
    path.write_text(path.read_text() + "\n# changed after load\n")
    value = replace(adopted, b=cfg)
    refusal = refused(lambda: _adopt(value, LOC_A, cid2))
    assert refusal.code == "config-stale" and refusal.data == {"path": str(path), "keep": []}
    assert "restart the service and rerun adopt" in refusal.message and "adoption" in refusal.message
    assert SharingRegistry(cfg.sharing_root).pin(cid2).state == "mounted"


@pytest.fixture
def content_conflict(certified_worker_work):
    from helpers.commons import build_content_conflict
    snap = snapshot(certified_worker_work, "commons-1b-content-conflict", build_content_conflict)
    snap.restore()
    return Installations.of(snap.value["installations"]), snap.value["corpus_id"]


@pytest.fixture
def uid_corruption(certified_worker_work):
    from helpers.commons import build_uid_corruption
    snap = snapshot(certified_worker_work, "commons-1b-uid-corruption", build_uid_corruption)
    snap.restore()
    return Installations.of(snap.value["installations"]), snap.value


def test_a_differing_copy_refuses_adopt_conflict_content_and_stays_fetched(content_conflict):
    from helpers.commons import LOC_A3
    installations, cid = content_conflict
    ids = a_identity(installations.a, binding_destination=LOC_A)
    refusal = refused(lambda: _adopt(installations, LOC_A3, cid))
    assert refusal.code == "adopt-conflict"
    assert refusal.data == {"rule": "content", "addresses": [ids["proposition"]], "corpus": ids["corpus_id"]}
    assert SharingRegistry(installations.b.sharing_root).pin(cid).state == "fetched"
    assert not _known(installations.b, cid)


def test_a_redirect_published_as_a_successor_refuses_uid_corruption(uid_corruption):
    from helpers.commons import LOC_C
    installations, value = uid_corruption
    cid = value["corpus_id"]
    refusal = refused(lambda: _adopt(installations, LOC_C, cid))
    assert refusal.code == "adopt-conflict" and refusal.data["rule"] == "uid-corruption"
    assert refusal.data["corpus"] == value["predecessor"] and len(refusal.data["addresses"]) == 2
    assert SharingRegistry(installations.b.sharing_root).pin(cid).state == "fetched"
    assert not _known(installations.b, cid)


def test_first_adoption_is_trivially_resolved(bound):
    from science.supersession import classify, groups, sharing_lines
    cid = a_identity(bound.a)["corpus_id"]
    _adopt(bound, LOC_A, cid)
    (held,) = groups(SharingRegistry(bound.b.sharing_root), sharing_lines(bound.b.operations_root)).values()
    outcome = classify(held)
    assert outcome.kind == "resolved" and outcome.tip[0] == cid


@pytest.mark.parametrize("held_predecessor", [True, False])
def test_preflight_refuses_siblings_even_under_an_unheld_predecessor(monkeypatch, held_predecessor):
    from beliefs.publication_arrival import DivergentPublication
    from science.commands.adopt import _preflight
    from test_supersession import held, kernel_result, line
    p1, p2, p3 = held(1), held(2, 1), held(3, 1)
    previous = (p1, p2) if held_predecessor else (p2,)
    kernel_result(monkeypatch, (*previous, p3), DivergentPublication((("p2", "m2"), ("p3", "m3"))))
    r = refused(lambda: _preflight(previous, p3, tuple(map(line, previous))))
    assert r.code == "divergent-publication" and r.data == {"tips": [["p2", "m2"], ["p3", "m3"]]}
    assert "p2" in r.message and "p3" in r.message


@pytest.mark.parametrize("late_predecessor", [True, False])
def test_preflight_refuses_a_chain_through_a_retired_intermediate(monkeypatch, late_predecessor):
    from beliefs.publication_arrival import CurrentPublication
    from science.commands.adopt import _preflight
    from test_supersession import held, kernel_result, line
    p1, p2, p3 = held(1), held(2, 1, state="retired"), held(3, 2)
    candidate, previous = (p1, (p2, p3)) if late_predecessor else (p3, (p1, p2))
    kernel_result(monkeypatch, (*previous, candidate), CurrentPublication("p3", "m3"))
    r = refused(lambda: _preflight(previous, candidate, tuple(map(line, previous))))
    assert r.code == "adopt-conflict" and r.data == {"rule": "chain-retired", "addresses": [], "corpus": "p2"}


@pytest.mark.xfail(strict=True, reason="Task 11 fixture: updated returns Installations with P3 in A's binding")
def test_a_successor_keeps_a_predecessor_b_depends_on_and_reports_why(request):
    updated = request.getfixturevalue("updated")
    registry = SharingRegistry(updated.b.sharing_root)
    (predecessor,) = [pin for pin in registry.pins() if pin.world == updated.a.world.world_id and pin.state == "mounted"]
    ids = a_identity(updated.a, binding_destination=LOC_A)
    text = _adopt(updated, LOC_A, ids["corpus_id"]).text
    assert f"retention {predecessor.corpus_id}:" in text
    assert f"dependency ({ids['assessment']})" in text
    assert registry.pin(predecessor.corpus_id).state == "mounted"


@pytest.mark.xfail(strict=True, reason="Task 11 fixture: updated_unkept returns Installations with P3 in A's binding")
def test_unkept_dropped_assessment_reports_retirement_pending(request):
    updated = request.getfixturevalue("updated_unkept")
    registry = SharingRegistry(updated.b.sharing_root)
    (predecessor,) = [pin for pin in registry.pins() if pin.world == updated.a.world.world_id and pin.state == "mounted"]
    text = _adopt(updated, LOC_A, a_identity(updated.a, binding_destination=LOC_A)["corpus_id"]).text
    assert predecessor.corpus_id in text and "retirement pending" in text and "beliefs-a989fb" in text
    assert registry.pin(predecessor.corpus_id).state == "mounted"


@pytest.mark.xfail(strict=True, reason="Task 11 fixture: sibling_publications returns (Installations, P3, P3prime)")
def test_a_refused_sibling_stays_fetched_and_does_not_change_later_evaluation(request):
    installations, first, sibling = request.getfixturevalue("sibling_publications")
    _adopt(installations, LOC_A, first)
    r = refused(lambda: _adopt(installations, LOC_A, sibling))
    assert r.code == "divergent-publication" and {pair[0] for pair in r.data["tips"]} == {first, sibling}
    registry = SharingRegistry(installations.b.sharing_root)
    assert registry.pin(first).state == "mounted" and registry.pin(sibling).state == "fetched"
    assert not _known(installations.b, sibling)
    from science.supersession import classify, groups, sharing_lines
    state = groups(registry, sharing_lines(installations.b.operations_root))
    group = next(group for group in state.values() if any(item.corpus_id == first for item in group))
    assert classify(group).kind == "resolved" and classify(group).tip[0] == first
    again = refused(lambda: _adopt(installations, LOC_A, first))
    assert again.code == "invalid-input" and "already adopted" in again.message


@pytest.mark.xfail(strict=True, reason="Task 13 retirement door; Task 11 late_link returns (Installations, missing_link)")
def test_two_retirements_in_one_invocation_render_both_pins_before_tail(request):
    installations, missing = request.getfixturevalue("late_link")
    registry = SharingRegistry(installations.b.sharing_root)
    before = {pin.corpus_id for pin in registry.pins() if pin.state == "mounted"}
    text = _adopt(installations, LOC_A, missing).text
    retired = [line for line in text.splitlines() if line.startswith("[pin]") and line.endswith(" retired")]
    assert len(retired) == 2 and any(missing in line for line in retired)
    assert any(any(corpus in line for corpus in before) for line in retired)
    assert max(text.index(line) for line in retired) < text.index("retirement ")
    assert "reopen the session and run science epoch" in text


def test_a_mounted_target_reports_another_pins_admission_recovery(adopted, monkeypatch):
    cid1 = a_identity(adopted.a)["corpus_id"]
    cid2 = publish_again(adopted, LOC_A)
    _crash_on_write_pin(monkeypatch, "admitted")
    with pytest.raises(RuntimeError, match="injected crash"):
        _adopt(adopted, LOC_A, cid2)
    monkeypatch.undo()
    text = _adopt(adopted, LOC_A, cid1).text
    assert _states(text) == ["mounted"] and f"[pin] {cid2} mounted" in text
    assert "retirement pending" in text


def test_a_conflict_names_why_its_predecessor_is_required(adopted):
    from dataclasses import replace
    from beliefs.root import open_corpus
    from helpers.world import FIXTURE_AUTHORITY
    cid1 = a_identity(adopted.a)["corpus_id"]
    writer = open_corpus(adopted.a.write_root, authority=FIXTURE_AUTHORITY, profile=adopted.a.profile)
    node = writer.read_view.get(a_identity(adopted.a)["proposition"])
    writer.revise(node.model_copy(update={"title": "Revised content"}))
    cid2 = publish_again(adopted, LOC_A)
    installations = replace(adopted, b=replace(adopted.b, keep=(cid1,)))
    refusal = refused(lambda: _adopt(installations, LOC_A, cid2))
    assert refusal.code == "adopt-conflict" and refusal.data["rule"] == "content"
    assert "required predecessor: configuration" in refusal.message


@pytest.mark.parametrize("terminal", ["retired", "departed"])
def test_completed_terminal_effect_is_reported_once_without_new_retirement(adopted, terminal):
    from beliefs.root import open_world
    from helpers.world import FIXTURE_AUTHORITY
    cid1 = a_identity(adopted.a)["corpus_id"]
    cid2 = publish_again(adopted, LOC_A)
    world = open_world(adopted.b.world, authority=FIXTURE_AUTHORITY)
    (world.retire if terminal == "retired" else world.depart)(cid1)
    text = _adopt(adopted, LOC_A, cid2).text
    assert _states(text) == ["fetched", "admitted", "mounted"]
    findings = [line for line in text.splitlines() if line.startswith("!") and cid1 in line]
    assert len(findings) == 1
    assert ("retirement pending" if terminal == "retired" else "departed") in findings[0]
    if terminal == "departed":
        assert "retirement pending" not in text
    else:
        assert "beliefs-a989fb" in text


@pytest.mark.xfail(strict=True, reason="Task 11 fixture: sibling_publications returns (Installations, P3, P3prime)")
def test_siblings_under_a_never_held_predecessor_refuse_the_same_way(request):
    from dataclasses import replace
    from helpers.commons import build_installation
    installations, first, sibling = request.getfixturevalue("sibling_publications")
    reader = build_installation(installations.remotes.parent, "new-reader", hold_vocabulary=False)
    value = replace(installations, b=reader)
    _bind(value, LOC_A, first, installations.a.world.world_id)
    _adopt(value, LOC_A, first)
    refusal = refused(lambda: _adopt(value, LOC_A, sibling))
    assert refusal.code == "divergent-publication"
    assert {pair[0] for pair in refusal.data["tips"]} == {first, sibling}
    pins = SharingRegistry(reader.sharing_root).pins()
    assert {pin.corpus_id for pin in pins} == {first, sibling}
    assert SharingRegistry(reader.sharing_root).pin(sibling).state == "fetched"
