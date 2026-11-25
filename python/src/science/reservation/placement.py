"""Where an exposure event's units fall against an assignment's groups.

Pure arithmetic over kernel units: which of it blocks anything is the program's rule, applied by
`science.reservation.gate`.
"""
from __future__ import annotations

from collections.abc import Iterable
from unicodedata import normalize

from beliefs.reservation import OPEN, ROLES, ExposureEvent, IntervalUnit, ReservationAssignment, TermUnit

__all__ = ["OUTSIDE", "PLACES", "UNSCOPED", "places"]

OUTSIDE, UNSCOPED = "outside", "unscoped"
PLACES = (*ROLES, OUTSIDE, UNSCOPED)

# Whole-second UTC timestamps order as text; these bound them on either side.
_BEFORE, _AFTER = "", "~"
_Span = tuple[str, str]


def places(event: ExposureEvent, assignment: ReservationAssignment) -> tuple[str, ...]:
    """Every place the event falls, in `PLACES` order. A unit of another shape than the groups', or a term of a
    sort they do not use, falls nowhere."""
    if not event.units:
        return (UNSCOPED,)
    found: set[str] = set()
    for unit in event.units:
        if isinstance(unit, TermUnit):
            found |= _term_places(unit, assignment)
        else:
            found |= _interval_places(unit, assignment)
    return tuple(place for place in PLACES if place in found)


def _key(unit: TermUnit) -> tuple[str, str]:
    # The kernel's identity is over NFC text, so two spellings of one term are one unit.
    return unit.sort, normalize("NFC", unit.term)


def _term_places(unit: TermUnit, assignment: ReservationAssignment) -> set[str]:
    held = [(_key(member), group.role) for group in assignment.groups for member in group.units
            if isinstance(member, TermUnit)]
    if unit.sort not in {sort for (sort, _), _ in held}:
        return set()
    return {role for key, role in held if key == _key(unit)} or {OUTSIDE}


def _span(unit: IntervalUnit) -> _Span:
    return _BEFORE if unit.start == OPEN else unit.start, _AFTER if unit.end == OPEN else unit.end


def _overlap(one: _Span, other: _Span) -> bool:
    return one[0] < other[1] and other[0] < one[1]


def _covered(span: _Span, spans: Iterable[_Span]) -> bool:
    """Whether the union of half-open `spans` holds every part of `span`."""
    reached, end = span
    for start, stop in sorted(spans):
        if start > reached:
            break
        reached = max(reached, stop)
    return reached >= end


def _interval_places(unit: IntervalUnit, assignment: ReservationAssignment) -> set[str]:
    held = [(_span(member), group.role) for group in assignment.groups for member in group.units
            if isinstance(member, IntervalUnit)]
    if not held:
        return set()
    span = _span(unit)
    found = {role for other, role in held if _overlap(span, other)}
    if not _covered(span, (other for other, _ in held)):
        found.add(OUTSIDE)
    return found
