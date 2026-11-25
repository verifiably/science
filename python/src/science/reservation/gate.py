"""The exposure an assignment has not considered, and which of it a program's rule lets block.

Science applies no default: the program's rule chooses the places and whether every event must be considered.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from beliefs.reservation import ExposureEvent, ReservationAssignment

from science.refusal import Refusal, Refused
from science.report import KeyVals
from science.reservation.attribution import PROGRAM, UNATTRIBUTED, Claims
from science.reservation.placement import PLACES, places
from science.reservation.presentation import event_block

__all__ = ["Gate", "Unconsidered", "gate_of", "unconsidered_blocks", "unconsidered_events"]

_BLOCKABLE = (*PLACES, UNATTRIBUTED)


@dataclass(frozen=True)
class Unconsidered:
    """A visible event the head did not consider: whose it is and where it falls."""
    event: ExposureEvent
    whose: str
    places: tuple[str, ...]


@dataclass(frozen=True)
class Gate:
    block_on: frozenset[str]
    all_considered: bool

    def blocks(self, item: Unconsidered) -> bool:
        if item.whose == PROGRAM:
            return self.all_considered or (item.event.effect == "exposing"
                                           and not self.block_on.isdisjoint(item.places))
        return item.whose == UNATTRIBUTED and UNATTRIBUTED in self.block_on

    def require(self, head: ReservationAssignment, items: Iterable[Unconsidered]) -> None:
        blocked = [item for item in items if self.blocks(item)]
        if blocked:
            raise Refused(Refusal(
                "events-unconsidered", f"{head.id} has not considered {len(blocked)} event(s) this gate blocks on",
                {"head": head.id, "events": [
                    {"address": item.event.id, "whose": item.whose, "places": list(item.places),
                     "effect": item.event.effect} for item in blocked]}))


def gate_of(block_on: Sequence[str], all_considered: bool) -> Gate:
    unknown = sorted(set(block_on) - set(_BLOCKABLE))
    if unknown:
        raise Refused(Refusal("invalid-input", f"block_on {', '.join(unknown)} is not one of {', '.join(_BLOCKABLE)}",
                              {"field": "block_on"}))
    return Gate(frozenset(block_on), all_considered)


def unconsidered_events(head: ReservationAssignment, visible: Iterable[ExposureEvent],
                        claims: Claims) -> tuple[Unconsidered, ...]:
    return tuple(Unconsidered(event, claims.whose(event), places(event, head))
                 for event in visible if event.id not in head.events)


def unconsidered_blocks(items: Sequence[Unconsidered]) -> tuple[KeyVals, ...]:
    blocks = [KeyVals("visible events not considered by this assignment", (("count", str(len(items))),))]
    for item in items:
        block = event_block(item.event)
        blocks.append(KeyVals(block.title, (("whose", item.whose), ("falls", ", ".join(item.places) or "nowhere"),
                                            *block.pairs)))
    return tuple(blocks)
