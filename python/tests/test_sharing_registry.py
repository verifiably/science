"""The sharing registry: pins, provider bindings, adopted roots, ledger replay."""
from __future__ import annotations

import dataclasses
import os
from pathlib import Path

import pytest

from science.sharing import (
    FetchRecord,
    Pin,
    PinSource,
    ProviderBinding,
    SharingRegistry,
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


@dataclasses.dataclass(frozen=True)
class Line:
    """Structurally a kernel SharingLine."""

    invocation: str
    corpus: str
    marker: str
    artifact: str
    world: str
    view: str
    source: str
    location: str
    verdict: str
    transition: str
    at: str


def line(transition: str, *, source: str = "", at: str = AT, corpus: str = CID,
         location: str = L1) -> Line:
    return Line("i" * 32, corpus, "m1", "art1", W, "view1", source, location, "ok", transition, at)


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


@pytest.fixture
def operations_root(tmp_path: Path) -> Path:
    # Minimal stand-in until Task 4 rebuilds it through the kernel door: two session
    # directories whose ids make directory order the inverse of time order.
    root = tmp_path / "operations"
    (root / "sessions" / ("1" * 32)).mkdir(parents=True)
    (root / "sessions" / ("2" * 32)).mkdir(parents=True)
    return root


@pytest.mark.xfail(
    strict=True, raises=NotImplementedError,
    reason="needs LedgerReader sharing lines from beliefs-f24fe9; Task 4 rebuilds the fixture",
)
def test_replay_applies_lines_in_time_order_across_sessions(tmp_path, operations_root):
    registry = SharingRegistry(tmp_path / "sharing")
    written = replay(registry, operations_root)
    assert [l.transition for l in written] == ["bound", "fetched", "admitted", "mounted"]
    assert registry.bindings()[W].locations == (L1,) and registry.pin(CID).state == "mounted"
