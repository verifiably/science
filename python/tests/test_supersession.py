"""Ledger-derived publication groups, named ancestry and current selection."""
from dataclasses import replace
from pathlib import Path

import pytest
from beliefs.coordination import CoordinationAddress
from beliefs.intents.publish import Destination
from beliefs.publication_arrival import CurrentPublication, DivergentPublication
from beliefs.session.ledger import LedgerWriter, SharingLine, ledger_path
from helpers.commons import LOC_A, a_identity
from science.publication import MarkerFields, marker_fields, marker_of
from science.refusal import Refused
from science.sharing import FetchRecord, Pin, PinSource, ProviderBinding, SharingLedgerUnreadable, SharingRegistry
from science.supersession import Held, Outcome, ancestry, authorized, chain, classify, current, established, group_of, sharing_lines

W = "a" * 32
VIEW = f"coord:{'b' * 32}@{'c' * 32}"
DEST = Destination.remote("https://example.org/publications")
AT = "2026-10-28T12:00:00Z"


def held(n, *predecessors, state="mounted"):
    return Held(f"p{n}", Path(f"/roots/p{n}"), MarkerFields(
        uid=f"m{n}", world=W, view=VIEW, destination=DEST, selection=frozenset(), attributions={},
        supersedes=tuple((f"p{p}", f"m{p}") for p in predecessors)), state)


def line(item, transition="mounted", *, source=f"provider:{DEST.locator}", at=AT):
    return SharingLine("invoke", item.corpus_id, item.marker.uid, "artifact", W, VIEW, source,
                       DEST.locator, "validated", transition, at)


def pin(item, *, source=f"provider:{DEST.locator}", world=W):
    return Pin(item.corpus_id, item.marker.uid, "artifact", world, VIEW, PinSource.parse(source),
               FetchRecord(DEST.locator, AT, "validated"), item.state)


def kernel_result(monkeypatch, items, result):
    # Unit inputs are parsed values; only the kernel's filesystem read is replaced.
    def read(roots, view, destination):
        assert roots == tuple(item.root for item in items)
        assert view == CoordinationAddress.parse(VIEW)
        assert destination == DEST
        return result
    monkeypatch.setattr("science.supersession.publication_tip", read)


def test_group_key_is_world_view_destination():
    item = held(1)
    assert group_of(item.marker) == (W, f"coord:{'b' * 32}", DEST.locator)
    assert group_of(replace(item.marker, world="d" * 32)) != group_of(item.marker)
    assert group_of(replace(item.marker, destination=Destination.local("/other"))) != group_of(item.marker)
    assert group_of(replace(item.marker, view=f"coord:{'b' * 32}@{'d' * 32}")) == group_of(item.marker)


def test_resolved_candidate_is_passed_to_kernel(monkeypatch):
    p1, p2 = held(1), held(2, 1)
    kernel_result(monkeypatch, (p1, p2), CurrentPublication("p2", "m2"))
    assert classify((p1,), p2) == Outcome("resolved", ("p2", "m2"), (), ())


def test_empty_group_has_no_tip():
    assert classify(()) == Outcome("unresolved", None, (), ())


@pytest.mark.parametrize("with_predecessor", [True, False])
def test_sibling_tips_are_divergent_with_held_or_unheld_predecessor(monkeypatch, with_predecessor):
    items = ((held(1),) if with_predecessor else ()) + (held(2, 1), held(3, 1))
    kernel_result(monkeypatch, items, DivergentPublication((("p2", "m2"), ("p3", "m3"))))
    assert classify(items) == Outcome("divergent", None, (("p2", "m2"), ("p3", "m3")), ())


def test_a_tip_naming_an_unheld_intermediate_is_unresolved_naming_the_pair(monkeypatch):
    items = (held(1), held(3, 2))
    kernel_result(monkeypatch, items, DivergentPublication((("p1", "m1"), ("p3", "m3"))))
    assert classify(items) == Outcome("unresolved", None, (("p1", "m1"), ("p3", "m3")), (("p2", "m2"),))


def test_a_sibling_pair_is_divergent_even_beside_a_disconnected_tip(monkeypatch):
    items = (held(1), held(2, 1), held("2b", 1), held(4, 3))
    tips = (("p2", "m2"), ("p2b", "m2b"), ("p4", "m4"))
    kernel_result(monkeypatch, items, DivergentPublication(tips))
    assert classify(items) == Outcome("divergent", None, tips, ())


def test_a_forged_link_naming_a_held_marker_under_the_wrong_corpus_is_unheld(monkeypatch):
    p1, p2 = held(1), held(2)
    p2 = replace(p2, marker=replace(p2.marker, supersedes=(("wrong-corpus", "m1"),)))
    items = (p1, p2)
    kernel_result(monkeypatch, items, DivergentPublication((("p1", "m1"), ("p2", "m2"))))
    assert ancestry(("p2", "m2"), items) == frozenset({("p2", "m2"), ("wrong-corpus", "m1")})
    assert classify(items).missing == (("wrong-corpus", "m1"),)


def test_ancestry_follows_retired_links_and_stops_on_cycles():
    items = (held(1, 3, state="retired"), held(2, 1), held(3, 2))
    assert ancestry(("p3", "m3"), items) == frozenset({("p1", "m1"), ("p2", "m2"), ("p3", "m3")})


def test_current_follows_a_gap_filler_and_ignores_a_disconnected_adoption():
    p1, p2, p4 = held(1), held(2, 1), held(4, 3)
    assert current((line(p1), line(p4), line(p2)), (p1, p2, p4)) == ("p2", "m2")


@pytest.mark.parametrize("order, expected", [((1, 3), ("p1", "m1")), ((3, 1), ("p3", "m3"))])
def test_current_is_unmoved_whichever_end_of_a_gap_arrives_second(order, expected):
    items = {1: held(1), 3: held(3, 2)}
    assert current(tuple(line(items[n]) for n in order), tuple(items.values())) == expected


def test_current_advances_an_already_seen_tip_when_the_gap_arrives():
    items = (held(1), held(2, 1), held(3, 2), held(4, 3))
    assert current(tuple(line(items[n]) for n in (0, 3, 1, 2)), items) == ("p4", "m4")


def test_current_does_not_use_future_marker_links():
    p1, p2, p3 = held(1), held(2, 1), held(3, 2)
    assert current((line(p1), line(p3)), (p1, p2, p3)) == ("p1", "m1")


def test_a_retired_line_is_not_consumed_and_a_retired_root_still_links():
    p1, p2, p3 = held(1), held(2, 1, state="retired"), held(3, 2)
    assert current((line(p1), line(p3), line(p2, "retired")), (p1, p2, p3)) == ("p1", "m1")
    assert current((line(p1), line(p3), line(p2), line(p2, "retired")), (p1, p2, p3)) == ("p3", "m3")


def test_current_consumes_historical_mount_of_a_now_retired_pin():
    p1, p3 = held(1, state="retired"), held(3, 2)
    assert current((line(p1), line(p3)), (p1, p3)) == ("p1", "m1")


def test_chain_is_endpoint_inclusive_from_predecessor_to_tip():
    items = (held(1), held(2, 1, state="retired"), held(3, 2), held(5, 4))
    assert chain(("p1", "m1"), ("p3", "m3"), items) == (("p1", "m1"), ("p2", "m2"), ("p3", "m3"))
    assert chain(("p3", "m3"), ("p1", "m1"), items) is None
    assert chain(("p1", "m1"), ("p5", "m5"), items) is None
    assert chain(("p1", "m1"), ("p1", "m1"), items) == (("p1", "m1"),)
    assert chain(("absent", "m1"), ("absent", "m1"), items) is None


def test_established_keeps_mounted_and_retired_only_and_never_reads_pin_files(tmp_path, monkeypatch):
    registry = SharingRegistry(tmp_path)
    items = tuple(held(n) for n in range(1, 5))
    # Marker reading is checked separately with a real root below.
    monkeypatch.setattr("science.supersession.marker_of", lambda root: object())
    (tmp_path / "pins").mkdir()
    (tmp_path / "pins" / "broken.json").write_text("invalid JSON")
    p1, p2, p3, p4 = items
    lines = (line(p1, "bound"), line(p1, "fetched", source=""), line(p2, "admitted"),
             line(p3), line(p4, "retired"), line(p3, "fetched"), line(p3, "admitted"),
             line(p1), line(p1, "fetched", source="catalog:later"))
    pins = established(registry, lines)
    assert [(p.corpus_id, p.state) for p in pins] == [("p1", "mounted"), ("p3", "mounted"), ("p4", "retired")]
    assert pins[0].source == PinSource("provider", DEST.locator)
    assert pins[0].fetch == FetchRecord(DEST.locator, AT, "validated")
    assert (tmp_path / "pins" / "broken.json").read_text() == "invalid JSON"


def test_established_refuses_a_mounted_pin_whose_root_is_missing(tmp_path):
    registry = SharingRegistry(tmp_path)
    with pytest.raises(Refused) as caught:
        established(registry, (line(held(1)),))
    refusal = caught.value.refusal
    assert refusal.code == "invalid-input"
    assert "p1" in refusal.message and str(registry.root_for("p1")) in refusal.message
    assert not registry.root_for("p1").exists()


def test_authorized_requires_confirmed_origin_and_the_markers_whole_group(tmp_path, monkeypatch):
    registry = SharingRegistry(tmp_path)
    p1 = held(1)
    binding = ProviderBinding(W, (DEST.locator,), AT, True)
    fields = {registry.root_for(f"p{n}"): p1.marker for n in range(1, 8)}
    fields[registry.root_for("p5")] = replace(p1.marker, destination=Destination.local("/elsewhere"))
    fields[registry.root_for("p6")] = replace(p1.marker, view=f"coord:{'d' * 32}@{'c' * 32}")
    fields[registry.root_for("p7")] = replace(p1.marker, world="d" * 32)
    monkeypatch.setattr("science.supersession.marker_of", lambda root: fields[root])
    monkeypatch.setattr("science.supersession.marker_fields", lambda value: value)
    pins = (pin(p1), pin(held(2), source=""), pin(held(3), source="catalog:art"),
            pin(held(4), world="d" * 32), pin(held(5)), pin(held(6)), pin(held(7)))
    expected = (replace(p1, root=registry.root_for("p1")),)
    assert authorized(pins, {W: binding}, registry, group_of(p1.marker)) == expected
    assert authorized(pins, {W: replace(binding, confirmed=False)}, registry, group_of(p1.marker)) == ()
    assert authorized(pins, {W: replace(binding, locations=())}, registry, group_of(p1.marker)) == ()


def write_ledger(root, session, items):
    path = ledger_path(root, session)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    try:
        writer.append({"line": "session-open", "session": session, "actor": f"session:{session}", "world": W,
                       "permit": {"kinds": [], "act_families": ["lifecycle", "registry"], "ungoverned": False}, "at": AT})
        writer.append({"line": "invocation-open", "invocation": "invoke", "command": "adopt", "input_digest": "f" * 64, "at": AT})
        for item in items:
            writer.append({"line": "sharing", **item.__dict__})
        writer.append({"line": "invocation-close", "invocation": "invoke", "outcome": {"done": []}})
        writer.append({"line": "session-close", "at": AT})
    finally:
        writer.close()


def test_sharing_lines_orders_by_time_session_then_position_and_current_uses_that_order(tmp_path):
    p1, p3 = held(1), held(3, 2)
    # Ledger fields need canonical identities; the pure graph does not.
    p1 = replace(p1, corpus_id="1" * 32, marker=replace(p1.marker, uid="2" * 32))
    p3 = replace(p3, corpus_id="3" * 32, marker=replace(p3.marker, uid="4" * 32))
    def valid(item, transition="mounted", at=AT):
        return replace(line(item, transition, at=at), artifact="5" * 64)
    write_ledger(tmp_path, "a" * 32, (valid(p3), valid(p1)))
    write_ledger(tmp_path, "b" * 32, (valid(p1, "fetched", at="2026-10-28T11:00:00Z"), valid(p1)))
    missing = ledger_path(tmp_path, "0" * 32)
    missing.parent.mkdir(parents=True)
    empty = ledger_path(tmp_path, "f" * 32)
    empty.parent.mkdir(parents=True)
    empty.write_bytes(b"")
    lines = sharing_lines(tmp_path)
    assert [(l.corpus, l.transition) for l in lines] == [(p1.corpus_id, "fetched"), (p3.corpus_id, "mounted"),
                                                        (p1.corpus_id, "mounted"), (p1.corpus_id, "mounted")]
    assert current(lines, (p1, p3)) == (p3.corpus_id, p3.marker.uid)
    assert sharing_lines(tmp_path / "absent") == ()


def test_sharing_lines_refuses_unreadable_ledger(tmp_path):
    path = ledger_path(tmp_path, "a" * 32)
    path.parent.mkdir(parents=True)
    path.write_text('{"line":"act"}\n')
    with pytest.raises(SharingLedgerUnreadable) as caught:
        sharing_lines(tmp_path)
    assert caught.value.session_id == "a" * 32


def test_real_marker_destination_and_kernel_tip_are_wired(published):
    ids = a_identity(published.a)
    # The provider transport holds the fetched corpus at B only after adoption;
    # the publisher's local transport cache already holds its publication root.
    roots = list((published.a.operations_root / "transport").rglob("corpus.yaml"))
    root = next(path.parent for path in roots if path.parent.name == ids["corpus_id"])
    fields = marker_fields(marker_of(root))
    assert fields.destination == Destination.remote(LOC_A)
    assert group_of(fields) == (ids["world"], str(CoordinationAddress.parse(fields.view).unpinned()), LOC_A)
    item = Held(ids["corpus_id"], root, fields, "mounted")
    assert classify((item,)) == Outcome("resolved", (ids["corpus_id"], ids["marker"]), (), ())
