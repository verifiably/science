"""The sharing registry: pins, provider bindings, adopted roots, ledger replay."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from beliefs.session.ledger import LedgerWriter, SharingLine, ledger_path

from science.sharing import (
    FetchRecord,
    Pin,
    PinSource,
    ProviderBinding,
    SharingRegistry,
    SharingLedgerUnreadable,
    SharingRegistryMalformed,
    apply_line,
    replay,
)

CID = "a" * 32
CID_B = "b" * 32
W = "c" * 32
W_OTHER = "d" * 32
L1 = "https://example.org/one"
L2 = "https://example.org/two"
AT = "2026-10-22T10:00:00Z"
LATER = "2026-10-22T11:00:00Z"
BINDING = ProviderBinding(W, (L1,), AT, True)


def line(transition: str, *, source: str = "", at: str = AT, corpus: str = CID,
         location: str = L1) -> SharingLine:
    return SharingLine("i" * 32, corpus, "m1", "art1", W, "view1", source, location, "ok", transition, at)


def make_pin(corpus_id: str = CID, *, state: str = "fetched", source=None, world: str = W) -> Pin:
    return Pin(corpus_id, "m1", "art1", world, "view1", source, FetchRecord(L1, AT, "ok"), state)


def test_pin_round_trips_and_sorts(tmp_path):
    registry = SharingRegistry(tmp_path)
    registry.write_pin(make_pin(CID_B))
    registry.write_pin(make_pin(CID, source=PinSource("catalog", "art1"), state="mounted"))
    pins = registry.pins()
    assert [p.corpus_id for p in pins] == [CID, CID_B]
    assert registry.pin(CID) == pins[0] and pins[0].source == PinSource("catalog", "art1")
    assert registry.pin("e" * 32) is None


def test_mounted_roots_are_exactly_the_mounted_pins(tmp_path):
    registry = SharingRegistry(tmp_path)
    registry.write_pin(make_pin(CID, state="mounted"))
    registry.write_pin(make_pin(CID_B, state="admitted"))
    assert registry.mounted_roots() == (tmp_path / "roots" / CID,)
    assert registry.root_for(CID_B) == tmp_path / "roots" / CID_B
    assert registry.scratch("tok") == tmp_path / "scratch" / "tok"


def test_binding_for_location_matches_a_bound_location_only(tmp_path):
    registry = SharingRegistry(tmp_path)
    registry.write_binding(BINDING)
    assert registry.binding_for_location(L1) == BINDING
    assert registry.binding_for_location(L2) is None
    assert registry.binding_for_location(L1 + "/x") is None


def test_write_binding_merges_locations_for_one_world(tmp_path):
    registry = SharingRegistry(tmp_path)
    registry.write_binding(ProviderBinding(W, (L1,), AT, True))
    registry.write_binding(ProviderBinding(W, (L2,), AT, True))
    assert registry.bindings()[W].locations == (L1, L2)


def test_origin_confirmed_needs_a_confirmed_binding_to_the_markers_world():
    sourced = make_pin(source=PinSource("provider", L1))
    assert sourced.origin_confirmed({W: BINDING})
    assert not sourced.origin_confirmed({})
    assert not sourced.origin_confirmed({W: ProviderBinding(W, (L1,), AT, False)})
    assert not sourced.origin_confirmed({W: ProviderBinding(W, (L2,), AT, True)})
    assert not sourced.origin_confirmed({W_OTHER: ProviderBinding(W_OTHER, (L1,), AT, True)})
    assert not make_pin(source=PinSource("catalog", L1)).origin_confirmed({W: BINDING})
    assert not make_pin(source=None).origin_confirmed({W: BINDING})


def test_pin_source_parse_and_render():
    assert PinSource.parse("") is None
    assert PinSource.parse(f"provider:{L1}") == PinSource("provider", L1)
    assert PinSource.parse("catalog:art1").render() == "catalog:art1"
    with pytest.raises(ValueError):
        PinSource.parse("nowhere:x")


@pytest.mark.parametrize("damage", ["{", '{"version": 1, "corpus_id": "short"}', '{"version": 2}'])
def test_malformed_pin_names_its_file(tmp_path, damage):
    (tmp_path / "pins").mkdir()
    (tmp_path / "pins" / f"{CID}.json").write_text(damage)
    with pytest.raises(SharingRegistryMalformed) as caught:
        SharingRegistry(tmp_path).pins()
    assert caught.value.entry == f"pins/{CID}.json"
    assert caught.value.reason


def test_malformed_binding_names_its_file(tmp_path):
    (tmp_path / "providers").mkdir()
    (tmp_path / "providers" / f"{W}.json").write_text('{"version": 2}')
    with pytest.raises(SharingRegistryMalformed) as caught:
        SharingRegistry(tmp_path).bindings()
    assert caught.value.entry == f"providers/{W}.json"


def test_write_is_atomic_and_leaves_no_temp_file(tmp_path, monkeypatch):
    registry = SharingRegistry(tmp_path)
    registry.write_pin(make_pin())
    registry.write_binding(BINDING)
    assert sorted(p.name for p in (tmp_path / "pins").iterdir()) == [f"{CID}.json"]
    assert sorted(p.name for p in (tmp_path / "providers").iterdir()) == [f"{W}.json"]
    before = (tmp_path / "pins" / f"{CID}.json").read_text()

    def boom(src, dst):
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        registry.write_pin(make_pin(state="mounted"))
    assert (tmp_path / "pins" / f"{CID}.json").read_text() == before
    assert sorted(p.name for p in (tmp_path / "pins").iterdir()) == [f"{CID}.json"]


def test_an_absent_root_reads_as_empty(tmp_path):
    assert SharingRegistry(tmp_path / "none").pins() == ()
    assert SharingRegistry(tmp_path / "none").bindings() == {}
    assert SharingRegistry(tmp_path / "none").mounted_roots() == ()


def test_apply_line_is_idempotent_and_never_lowers_a_state(tmp_path):
    registry = SharingRegistry(tmp_path)
    assert apply_line(registry, line("fetched")) and not apply_line(registry, line("fetched"))
    assert apply_line(registry, line("mounted")) and registry.pin(CID).state == "mounted"
    assert not apply_line(registry, line("admitted")) and registry.pin(CID).state == "mounted"
    assert apply_line(registry, line("retired")) and registry.pin(CID).state == "retired"


def test_apply_line_binds_idempotently(tmp_path):
    registry = SharingRegistry(tmp_path)
    assert apply_line(registry, line("bound"))
    assert registry.bindings()[W] == ProviderBinding(W, (L1,), AT, True)
    assert not apply_line(registry, line("bound", at=LATER))
    assert registry.bindings()[W].bound_since == AT


def test_a_state_line_without_a_pin_creates_it(tmp_path):
    registry = SharingRegistry(tmp_path)
    assert apply_line(registry, line("admitted", source=f"provider:{L1}"))
    assert registry.pin(CID) == Pin(
        CID, "m1", "art1", W, "view1", PinSource("provider", L1),
        FetchRecord(L1, AT, "ok"), "admitted",
    )


def test_a_rebuilt_registry_keeps_the_source(tmp_path):
    registry = SharingRegistry(tmp_path)
    for each in (line("fetched", source=f"provider:{L1}"), line("admitted"), line("mounted")):
        apply_line(registry, each)
    assert registry.pin(CID).source == PinSource("provider", L1)
    assert registry.pin(CID).origin_confirmed({W: BINDING})


def test_a_source_is_set_late_but_never_cleared(tmp_path):
    registry = SharingRegistry(tmp_path)
    apply_line(registry, line("fetched"))
    assert registry.pin(CID).source is None
    assert apply_line(registry, line("admitted", source="catalog:art1"))
    assert registry.pin(CID).source == PinSource("catalog", "art1")
    apply_line(registry, line("mounted"))
    assert registry.pin(CID).source == PinSource("catalog", "art1")


VIEW = f"coord:{'1' * 32}@{'2' * 32}"


def _sharing(invocation: str, transition: str, at: str) -> dict:
    return {
        "line": "sharing", "invocation": invocation, "corpus": CID, "marker": "5" * 32,
        "artifact": "6" * 64, "world": W, "view": VIEW, "source": f"provider:{L1}",
        "location": L1, "verdict": "validated", "transition": transition, "at": at,
    }


def _write_session(operations_root: Path, session_id: str, *invocations) -> None:
    """One closed session ledger written through the kernel's own ledger writer, which
    validates every line; each invocation is (id, [(transition, at), ...])."""
    path = ledger_path(operations_root, session_id)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    try:
        writer.append({
            "line": "session-open", "session": session_id, "actor": f"session:{session_id}", "world": "e" * 32,
            "permit": {"kinds": [], "act_families": ["lifecycle", "registry"], "ungoverned": False},
            "at": "2026-10-22T09:00:00Z",
        })
        for invocation, steps in invocations:
            writer.append({"line": "invocation-open", "invocation": invocation, "command": "adopt",
                           "input_digest": "f" * 64, "at": "2026-10-22T09:00:00Z"})
            for transition, at in steps:
                writer.append(_sharing(invocation, transition, at))
            writer.append({"line": "invocation-close", "invocation": invocation, "outcome": {"done": []}})
        writer.append({"line": "session-close", "at": "2026-10-22T13:00:00Z"})
    finally:
        writer.close()


@pytest.fixture
def operations_root(tmp_path: Path) -> Path:
    # Two sessions whose ids make directory order the inverse of time order, and a
    # tie on `at` inside the later one that only ledger position breaks.
    root = tmp_path / "operations"
    _write_session(root, "1" * 32, ("late", [("admitted", "2026-10-22T12:00:00Z"),
                                             ("mounted", "2026-10-22T12:00:00Z")]))
    _write_session(root, "2" * 32, ("early", [("bound", "2026-10-22T10:00:00Z"),
                                              ("fetched", "2026-10-22T11:00:00Z")]))
    return root


def test_replay_applies_lines_in_time_order_across_sessions(tmp_path, operations_root):
    registry = SharingRegistry(tmp_path / "sharing")
    written = replay(registry, operations_root)
    assert [l.transition for l in written] == ["bound", "fetched", "admitted", "mounted"]
    assert registry.bindings()[W].locations == (L1,) and registry.pin(CID).state == "mounted"
    assert registry.pin(CID).source == PinSource("provider", L1)
    assert replay(registry, operations_root) == ()


def test_replay_of_no_sessions_writes_nothing(tmp_path):
    registry = SharingRegistry(tmp_path / "sharing")
    assert replay(registry, tmp_path / "operations") == ()
    assert registry.pins() == () and registry.bindings() == {}


@pytest.mark.parametrize("ledger", [None, b""], ids=["missing", "empty"])
def test_replay_skips_a_session_whose_creation_was_interrupted(tmp_path, operations_root, ledger):
    # No ledger file, or one the session-open line never reached: the kernel reads
    # both as interrupted creation, and neither can hold a sharing line.
    interrupted = ledger_path(operations_root, "0" * 32)
    interrupted.parent.mkdir(parents=True)
    if ledger is not None:
        interrupted.write_bytes(ledger)
    registry = SharingRegistry(tmp_path / "sharing")
    assert [l.transition for l in replay(registry, operations_root)] == ["bound", "fetched", "admitted", "mounted"]


def test_replay_refuses_an_unreadable_ledger_naming_its_session(tmp_path, operations_root):
    damaged = ledger_path(operations_root, "0" * 32)
    damaged.parent.mkdir(parents=True)
    damaged.write_bytes(b'{"line": "act"}\n')
    registry = SharingRegistry(tmp_path / "sharing")
    with pytest.raises(SharingLedgerUnreadable) as caught:
        replay(registry, operations_root)
    assert caught.value.session_id == "0" * 32 and "0" * 32 in str(caught.value)
    assert registry.pins() == () and registry.bindings() == {}
