"""Publication groups and supersession over established, origin-confirmed roots."""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from itertools import combinations
from pathlib import Path
from typing import Literal

from beliefs.coordination import CoordinationAddress
from beliefs.errors import PublicationArrivalRefused
from beliefs.publication_arrival import CAPTURE_DAMAGE, CurrentPublication, DivergentPublication, publication_tip
from beliefs.session.ledger import SharingLine

from science.publication import MarkerFields, marker_fields, marker_of
from science.refusal import Refusal, Refused
from science.sharing import (
    STATE_ORDER, FetchRecord, Pin, PinSource, ProviderBinding, SharingRegistry, sharing_lines,
)

GroupKey = tuple[str, str, str]


@dataclass(frozen=True)
class Held:
    corpus_id: str
    root: Path
    marker: MarkerFields
    state: Literal["mounted", "retired"]


def group_of(marker: MarkerFields) -> GroupKey:
    return marker.world, str(CoordinationAddress.parse(marker.view).unpinned()), marker.destination.locator


def established(registry: SharingRegistry, lines: Sequence[SharingLine]) -> tuple[Pin, ...]:
    """Fold pins under apply_line's monotonic state/first-source rule, ignoring pin files."""
    pins: dict[str, Pin] = {}
    for line in lines:
        if line.transition == "bound":
            continue
        if line.transition not in STATE_ORDER:
            raise ValueError(f"unknown sharing transition {line.transition!r}")
        source = PinSource.parse(line.source)
        pin = pins.get(line.corpus)
        if pin is None:
            pins[line.corpus] = Pin(
                line.corpus, line.marker, line.artifact, line.world, line.view, source,
                FetchRecord(line.location, line.at, line.verdict), line.transition,
            )
        else:
            state = max((pin.state, line.transition), key=STATE_ORDER.index)
            pins[line.corpus] = replace(pin, state=state, source=pin.source if pin.source is not None else source)
    found = tuple(pins[key] for key in sorted(pins) if pins[key].state in ("mounted", "retired"))
    for pin in found:
        if pin.state == "mounted":
            root = registry.root_for(pin.corpus_id)
            try:
                marker_of(root)
            except (*CAPTURE_DAMAGE, PublicationArrivalRefused) as caught:
                raise Refused(Refusal("invalid-input", f"mounted corpus {pin.corpus_id} at {root} is unreadable: {caught}")) from None
    return found


def authorized(pins: Iterable[Pin], bindings: Mapping[str, ProviderBinding], registry: SharingRegistry,
               key: GroupKey) -> tuple[Held, ...]:
    found = []
    for pin in pins:
        if pin.state not in ("mounted", "retired") or pin.world != key[0] or not pin.origin_confirmed(bindings):
            continue
        root = registry.root_for(pin.corpus_id)
        marker = marker_fields(marker_of(root))
        if group_of(marker) == key:
            found.append(Held(pin.corpus_id, root, marker, pin.state))
    return tuple(found)


def ancestry(tip: tuple[str, str], held: Iterable[Held]) -> frozenset[tuple[str, str]]:
    """Keep named pairs, even unheld ones; only the exact held pair supplies further links."""
    markers = {(item.corpus_id, item.marker.uid): item.marker for item in held}
    seen: set[tuple[str, str]] = set()
    pending = [tip]
    while pending:
        pair = pending.pop()
        if pair in seen:
            continue
        seen.add(pair)
        if pair in markers:
            pending.extend(markers[pair].supersedes)
    return frozenset(seen)


@dataclass(frozen=True)
class Outcome:
    kind: Literal["resolved", "divergent", "unresolved"]
    tip: tuple[str, str] | None
    tips: tuple[tuple[str, str], ...]
    missing: tuple[tuple[str, str], ...]


def classify(held: Sequence[Held], candidate: Held | None = None) -> Outcome:
    """Classify one authorized group, including the candidate only for its own preflight."""
    items = tuple(held) + (() if candidate is None else (candidate,))
    if not items:
        return Outcome("unresolved", None, (), ())
    first = items[0].marker
    result = publication_tip(tuple(item.root for item in items), CoordinationAddress.parse(first.view), first.destination)
    if isinstance(result, CurrentPublication):
        return Outcome("resolved", (result.corpus_id, result.marker), (), ())
    if result is None:
        return Outcome("unresolved", None, (), ())
    if not isinstance(result, DivergentPublication):
        raise TypeError(f"unknown publication tip from the kernel: {result!r}")
    ancestries = tuple(ancestry(tip, items) for tip in result.tips)
    if any(left & right for left, right in combinations(ancestries, 2)):
        return Outcome("divergent", None, result.tips, ())
    present = {(item.corpus_id, item.marker.uid) for item in items}
    missing = tuple(sorted(set().union(*ancestries) - present))
    return Outcome("unresolved", None, result.tips, missing)


def current(lines: Sequence[SharingLine], held: Sequence[Held]) -> tuple[str, str] | None:
    """Fold historical mounted lines; only markers seen so far may connect publications."""
    available = {(item.corpus_id, item.marker.uid): item for item in held}
    seen: dict[tuple[str, str], Held] = {}
    tip = None
    for line in lines:
        pair = line.corpus, line.marker
        if line.transition != "mounted" or pair not in available:
            continue
        seen[pair] = available[pair]
        if tip is None:
            tip = pair
        advanced = {tip}
        while successor := next((other for other in seen if other not in advanced
                                and tip in ancestry(other, seen.values())), None):
            tip = successor
            advanced.add(tip)
    return tip


def chain(from_pair: tuple[str, str], to_pair: tuple[str, str], held: Iterable[Held]) -> tuple[tuple[str, str], ...] | None:
    """An endpoint-inclusive held path, from predecessor to descendant (oldest to tip)."""
    markers = {(item.corpus_id, item.marker.uid): item.marker for item in held}
    if from_pair not in markers or to_pair not in markers:
        return None
    pending = [(to_pair,)]
    seen: set[tuple[str, str]] = set()
    while pending:
        path = pending.pop()
        pair = path[-1]
        if pair == from_pair:
            return tuple(reversed(path))
        if pair in seen:
            continue
        seen.add(pair)
        pending.extend((*path, predecessor) for predecessor in markers[pair].supersedes if predecessor in markers)
    return None


def groups(registry: SharingRegistry, lines: Sequence[SharingLine]) -> dict[GroupKey, tuple[Held, ...]]:
    """Authorized established groups, folded from the same evidence as replay."""
    pins = established(registry, lines)
    bindings = registry.bindings()
    keys = {group_of(marker_fields(marker_of(registry.root_for(pin.corpus_id))))
            for pin in pins if pin.origin_confirmed(bindings)}
    return {key: authorized(pins, bindings, registry, key) for key in sorted(keys)}
