"""Exposure logs and reservation heads over every configured live mount."""
from __future__ import annotations

import re
from dataclasses import replace

import pytest
from beliefs import stored
from helpers.reservation import (
    COMMANDS, add_foreign_mount, assignment_facet, assignment_node, digest, event_facet, event_node, group, hold_record,
    stored_of, write_payload,
)
from helpers.research import raw_write_node, research_rig
from helpers.snapshot import snapshot
from helpers.world import FIXTURE_AUTHORITY, build_fixture_world, build_shared_contract_world, mount_config
from science.config import corpus_id_at
from science.refusal import Refused

CHAIN = "mm-roster"


@pytest.fixture
def shared(certified_worker_work):
    snap = snapshot(certified_worker_work, "shared-contract", build_shared_contract_world)
    snap.restore()
    return snap.value


def _hold(target, node):
    return hold_record(target.write_root, target.profile, node)


def _event(target, **changes) -> str:
    return _hold(target, event_node(event_facet(**changes), actor="fixture")).id


def _assignment(target, **changes) -> str:
    return _hold(target, assignment_node(assignment_facet(**changes), actor="fixture")).id


def _source(target, accession: str) -> str:
    return _hold(target, stored.source_node(title=accession, identifiers={"accession": accession})).id


def _read(cfg, command, **inputs) -> str:
    with research_rig(cfg, COMMANDS) as (d, _):
        return _all_pages(d, command, inputs)


def _all_pages(d, command, inputs) -> str:
    page, text = d.invoke(command, inputs).text, ""
    while match := re.search(r"\n… truncated at \d+ bytes; continue with cursor (\S+)\n$", page):
        text += page[:match.start()]
        page = d.invoke(command, inputs, cursor=match[1]).text
    return text + page


def _refused(cfg, command, **inputs):
    with research_rig(cfg, COMMANDS) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke(command, inputs)
    return caught.value.refusal


def _listed(text: str) -> list[str]:
    return re.findall(r"^(exposure-event:[0-9a-f]{64}):$", text, re.MULTILINE)


def _section(text: str, title: str) -> list[str]:
    """The `  key: value` lines under one block title."""
    lines = text.splitlines()
    start = lines.index(f"{title}:") + 1
    end = next((i for i in range(start, len(lines)) if not lines[i].startswith("  ")), len(lines))
    return [line.strip() for line in lines[start:end]]


def _three_events(cfg):
    """An mm unmask read, a Sun interval read in the mount, and a knowledge event, with two sharing an instant."""
    mounted = mount_config(cfg)
    gse, tsi = _source(cfg, "GSE24080"), _source(mounted, "TSIS1")
    unmask = _event(cfg, channel="read", subjects=[gse], **{"class": "unmask"}, observer="codex",
                    observed_at="2026-11-06T09:15:00Z")
    interval = _event(mounted, channel="read", subjects=[tsi], propositions=["proposition:shared"], effect="non-exposing",
                      units=[{"start": "2007-11-01T00:00:00Z", "end": "2008-12-01T00:00:00Z"}],
                      observed_at="2026-10-01T00:00:00Z")
    knowledge = _event(cfg, units=[], observed_at="2026-11-06T09:15:00Z")
    return gse, tsi, unmask, interval, knowledge


def test_the_log_lists_every_visible_event_by_time_then_id(shared):
    cfg = shared
    gse, tsi, unmask, interval, knowledge = _three_events(cfg)
    text = _read(cfg, "exposure-log")
    assert _listed(text) == [interval, *sorted([unmask, knowledge])]
    assert _section(text, "exposure log") == ["subject: any", "proposition: any", "events: 3"]
    assert _section(text, unmask) == [
        "observed at: 2026-11-06T09:15:00Z", "channel: read", f"subjects: {gse}",
        'units: testing/cohort "uams-tt2-tt3"', "effect: exposing", "class: unmask", "observer: codex"]
    assert _section(text, interval) == [
        "observed at: 2026-10-01T00:00:00Z", "channel: read", f"subjects: {tsi}",
        "units: 2007-11-01T00:00:00Z .. 2008-12-01T00:00:00Z", "effect: non-exposing", "class: training-knowledge",
        "observer: agy/gemini-4-argon"]
    assert _section(text, knowledge)[2:4] == ["subjects: none", "units: none"]


def test_the_read_surface_does_not_depend_on_coordination(shared):
    cfg = shared
    _three_events(cfg)
    assert _read(cfg, "exposure-log") == _read(replace(cfg, coordination=None), "exposure-log")


def test_filters_intersect_and_a_well_formed_miss_is_an_empty_list(shared):
    cfg = shared
    gse, tsi, unmask, interval, _ = _three_events(cfg)
    assert _listed(_read(cfg, "exposure-log", subject=gse)) == [unmask]
    assert _listed(_read(cfg, "exposure-log", subject=tsi, proposition="proposition:shared")) == [interval]
    for miss in ({"subject": gse, "proposition": "proposition:shared"}, {"subject": "dataset:absent"},
                 {"proposition": "proposition:absent"}):
        text = _read(cfg, "exposure-log", **miss)
        assert _listed(text) == [] and "events: 0" in _section(text, "exposure log")


@pytest.mark.parametrize("command,inputs", [
    *(("exposure-log", {"subject": value}) for value in (
        "", "GSE24080", "dataset:", "source:", "proposition:shared", "cohort:uams-tt2-tt3", "testing/cohort", "Dataset:x")),
    *(("exposure-log", {"proposition": value}) for value in ("", "shared", "proposition:", "source:x")),
    *(("reservation-head", {"chain": value}) for value in ("", "MM", "1a", "mm roster", "mm-roster\n", "mm_roster", "-mm")),
    *(("reservation-head", {"chain": CHAIN, "scope": value}) for value in ("", "shared", "proposition:", "dataset:x")),
])
def test_a_malformed_filter_refuses_before_any_record_is_read(shared, monkeypatch, command, inputs):
    import science.reservation.records as records
    monkeypatch.setattr(records, "captured_mounts", lambda ctx: pytest.fail("a malformed filter reached the corpora"))
    refusal = _refused(shared, command, **inputs)
    assert refusal.code == "invalid-input"
    assert refusal.data == {"field": next(reversed(inputs))}


def test_agreeing_copies_are_one_event_and_differing_copies_refuse(shared):
    cfg = shared
    mounted = mount_config(cfg)
    node = event_node(event_facet(), actor="fixture")
    for target in (cfg, mounted):
        _hold(target, node)
    assert _listed(_read(cfg, "exposure-log")) == [node.id]
    other = event_node(event_facet(observer="codex"), actor="fixture")
    for index, target in enumerate((cfg, mounted)):
        _hold(target, other.model_copy(update={"title": f"copy {index}"}))
    for command, inputs in (("exposure-log", {}), ("exposure-log", {"subject": "dataset:unrelated"})):
        refusal = _refused(cfg, command, **inputs)
        assert refusal.code == "invalid-input" and "copies differ" in refusal.message
        assert all(corpus_id_at(target.write_root) in refusal.message for target in (cfg, mounted))


def test_a_retired_mounts_records_are_not_visible(shared):
    from beliefs.root import open_world
    cfg = shared
    mounted = mount_config(cfg)
    kept, gone = _event(cfg), _event(mounted, observer="codex")
    _assignment(mounted)
    assert set(_listed(_read(cfg, "exposure-log"))) == {kept, gone}
    open_world(cfg.world, authority=FIXTURE_AUTHORITY).retire(corpus_id_at(mounted.write_root))
    assert _listed(_read(cfg, "exposure-log")) == [kept]
    assert "head: none" in _section(_read(cfg, "reservation-head", chain=CHAIN), "reservation head")


@pytest.mark.parametrize("damage", ["stale-stamp", "malformed-facet"])
@pytest.mark.parametrize("kind", ["exposure-event", "reservation-assignment"])
def test_a_malformed_record_the_answer_needs_refuses_structurally(shared, damage, kind):
    cfg = shared
    _assignment(cfg)
    node, facet = ((event_node(event_facet(), actor="fixture"), stored.EXPOSURE_EVENT_FACET) if kind == "exposure-event"
                   else (assignment_node(assignment_facet(chain="other"), actor="fixture"), stored.RESERVATION_ASSIGNMENT_FACET))
    del node.facets[facet]["account" if kind == "exposure-event" else "rule"]
    if damage == "malformed-facet":
        stored.stamp_semantic_identity(node)
    raw_write_node(mount_config(cfg).write_root, node)
    expected = {"stale-stamp": "SemanticHashStale", "malformed-facet": "MalformedRecord"}[damage]
    refusal = _refused(cfg, "reservation-head", chain=CHAIN)
    assert refusal.code == "kernel-refused" and refusal.data == {"kind": expected}
    if kind == "exposure-event":
        refusal = _refused(cfg, "exposure-log")
        assert refusal.code == "kernel-refused" and refusal.data == {"kind": expected}
    else:  # no assignment is needed to answer an event query
        assert _listed(_read(cfg, "exposure-log")) == []


def test_a_root_head_reports_its_frozen_derivation(shared):
    cfg = shared
    event = _event(cfg)
    groups = [group("a20-mm-patients", role="unresolved"),
              group("uams-tt2", "uams-tt3", role="reserved", label="reserved (A1)", basis=digest("comparison"))]
    root = _assignment(cfg, events=[event], groups=groups, inputs={"roster.yaml": digest("roster"), "amendment-7": digest("a7")})
    text = _read(cfg, "reservation-head", chain=CHAIN)
    assert _section(text, "reservation head") == [
        f"chain: {CHAIN}", "scope: none", f"head: {root}", "title: Recorded by a test", "predecessor: none",
        "rule: mm-phase-1-protocol, version amendment-7", "assigned at: 2026-11-06T13:00:00Z", "assigned by: fixture"]
    assert _section(text, "frozen inputs") == [f"amendment-7: {digest('a7')}", f"roster.yaml: {digest('roster')}"]
    assert _section(text, "considered events") == ["count: 1", f"event: {event}"]
    assert _section(text, "group roles") == [
        "count: 2", 'unresolved: testing/cohort "a20-mm-patients"',
        f'reserved: testing/cohort "uams-tt2", testing/cohort "uams-tt3"; label reserved (A1); basis {digest("comparison")}']
    assert _section(text, "changes from the predecessor") == ["count: 0"]
    assert _section(text, "visible events not considered by this assignment") == ["count: 0"]
    assert _listed(text) == []


def test_a_successor_head_reports_its_changes_across_mounts(shared):
    cfg = shared
    mounted = mount_config(cfg)
    groups = [group("a", role="reserved"), group("b"), group("c", role="withheld")]
    node = assignment_node(assignment_facet(groups=groups), actor="fixture")
    for target in (cfg, mounted):
        _hold(target, node)
    successor = _assignment(mounted, predecessor=node.id, evidence=["ledger:entry"], flagged=[],
                            groups=[group("a", role="open"), group("b"), group("d", role="reserved")])
    text = _read(cfg, "reservation-head", chain=CHAIN)
    head = _section(text, "reservation head")
    assert f"head: {successor}" in head and f"predecessor: {node.id}" in head
    assert _section(text, "changes from the predecessor") == [
        "count: 3", 'changed: testing/cohort "a"; was reserved; suspended', 'absent: testing/cohort "c"; was withheld',
        'added: testing/cohort "d"']


def test_the_head_of_each_exact_chain_and_scope(shared):
    cfg = shared
    program = _assignment(cfg)
    scoped = _assignment(mount_config(cfg), scope="proposition:shared", chain=CHAIN)
    other = _assignment(cfg, chain="sun-epochs")
    for inputs, head in (({"chain": CHAIN}, program), ({"chain": CHAIN, "scope": "proposition:shared"}, scoped),
                         ({"chain": "sun-epochs"}, other)):
        section = _section(_read(cfg, "reservation-head", **inputs), "reservation head")
        assert f"head: {head}" in section and f"scope: {inputs.get('scope', 'none')}" in section


@pytest.mark.parametrize("inputs", [{"chain": "absent"}, {"chain": CHAIN, "scope": "proposition:shared"}])
def test_a_chain_with_no_record_is_an_explicit_empty_result(shared, inputs):
    cfg = shared
    _assignment(cfg)
    text = _read(cfg, "reservation-head", **inputs)
    assert text == ("reservation head:\n" f"  chain: {inputs['chain']}\n" f"  scope: {inputs.get('scope', 'none')}\n"
                    "  head: none\n")


@pytest.mark.parametrize("fork", ["two-roots", "two-heads"])
def test_independent_heads_surface_as_ambiguity(shared, fork):
    cfg = shared
    mounted = mount_config(cfg)
    if fork == "two-roots":
        for name, target in (("a", cfg), ("b", mounted)):
            _assignment(target, inputs={"roster.yaml": digest(name)})
    else:
        root = assignment_node(assignment_facet(), actor="fixture")
        for name, target in (("a", cfg), ("b", mounted)):
            _hold(target, root)
            _assignment(target, inputs={"roster.yaml": digest(name)}, predecessor=root.id)
    refusal = _refused(cfg, "reservation-head", chain=CHAIN)
    assert refusal.code == "kernel-refused" and refusal.data == {"kind": "ChainAmbiguous"}
    assert "two " in refusal.message


@pytest.mark.parametrize("predecessor", ["missing", "divergent"])
def test_a_head_whose_predecessor_cannot_be_read_refuses(shared, predecessor):
    cfg = shared
    mounted = mount_config(cfg)
    root = assignment_node(assignment_facet(), actor="fixture")
    if predecessor == "divergent":
        for index, target in enumerate((cfg, mounted)):
            _hold(target, root.model_copy(update={"title": f"copy {index}"}))
    raw_write_node(cfg.write_root, assignment_node(
        assignment_facet(inputs={"roster.yaml": digest("b")}, predecessor=root.id), actor="fixture"))
    refusal = _refused(cfg, "reservation-head", chain=CHAIN)
    if predecessor == "missing":
        assert refusal.code == "kernel-refused" and refusal.data == {"kind": "RefError"} and root.id in refusal.message
    else:
        assert refusal.code == "invalid-input" and "copies differ" in refusal.message


def test_an_event_recorded_after_the_head_is_visible_and_not_considered(shared, tmp_path):
    """The observation-first case: a prior look is recorded without a successor, and the head stays current."""
    cfg = shared
    older = _event(mount_config(cfg), observer="codex", observed_at="2020-01-01T00:00:00Z")
    considered = _event(cfg)
    with research_rig(cfg, COMMANDS) as (d, ctx):
        root = re.search(r"reservation-assignment:[0-9a-f]{64}", d.invoke("reservation-assignment", {
            "payload": write_payload(tmp_path, assignment_facet(events=[considered]))}).text)[0]
        before = _all_pages(d, "reservation-head", {"chain": CHAIN})
        assert _listed(before) == [older]
        later = re.search(r"exposure-event:[0-9a-f]{64}", d.invoke("exposure-event", {"payload": write_payload(
            tmp_path, event_facet(units=[], account="Characterized the dataset before formulating.",
                                  observed_at="2026-11-08T00:00:00Z"))}).text)[0]
        after = _all_pages(d, "reservation-head", {"chain": CHAIN})
        assert f"head: {root}" in _section(after, "reservation head")
        assert _section(after, "visible events not considered by this assignment") == ["count: 2"]
        assert _listed(after) == [older, later]
        assert _section(after, "considered events") == ["count: 1", f"event: {considered}"]
        assert stored_of(ctx, "reservation-assignment") == [root]
        log = _listed(_all_pages(d, "exposure-log", {}))
        assert [ref for ref in log if ref != considered] == [older, later]


def test_a_foreign_pinned_mount_is_read_like_any_other(shared):
    """Reads need no contract agreement: neither kind is decoded under a domain contract."""
    cfg, root, profile = add_foreign_mount(shared)
    node = hold_record(root, profile, event_node(event_facet(), actor="fixture"))
    assert _listed(_read(cfg, "exposure-log")) == [node.id]


def test_text_a_record_supplies_cannot_start_a_report_line(shared):
    cfg = shared
    event = _event(cfg, observer="codex\n  effect: non-exposing", **{"class": "a\nb"},
                   units=[{"sort": "testing/cohort", "term": "x\n  observer: someone"}])
    section = _section(_read(cfg, "exposure-log"), event)
    assert section[3:] == ['units: testing/cohort "x\\n  observer: someone"', "effect: exposing", 'class: "a\\nb"',
                           'observer: "codex\\n  effect: non-exposing"']


def test_a_long_report_pages_to_the_same_text_and_a_changed_world_stales_its_cursor(certified_work):
    cfg = build_fixture_world(certified_work)
    for index in range(60):
        _event(cfg, units=[], observer=f"observer-{index:02}")
    with research_rig(cfg, COMMANDS) as (d, _):
        first = d.invoke("exposure-log", {}).text
        cursor = re.search(r"continue with cursor (\S+)\n$", first)[1]
        assert len(_listed(_all_pages(d, "exposure-log", {}))) == 60
        _event(cfg, units=[], observer="one-more")
        with pytest.raises(Refused) as caught:
            d.invoke("exposure-log", {}, cursor=cursor)
        assert caught.value.refusal.code == "stale-cursor"


def test_the_minted_report_is_rebuilt_from_the_records(shared, tmp_path):
    cfg = shared
    with research_rig(cfg, COMMANDS) as (d, ctx):
        payload = write_payload(tmp_path, event_facet(units=[]), title="First look")
        text = d.invoke("exposure-event", {"payload": payload}, invocation_id="MINT").text
        address = re.search(r"exposure-event:[0-9a-f]{64}", text)[0]
        node = ctx.write_view().get(address)
        assert text == f"[exposure-event] {address} uid={node.uid}\nFirst look\n"
        (tmp_path / "payload.json").write_text("{}")
        assert d.invoke("exposure-event", {"payload": payload}, invocation_id="MINT").text == text
