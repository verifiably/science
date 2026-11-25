"""Pre-act checks of both writes: address occupancy, citations, chain linearity and the kernel's own rules.

The kernel's refusal functions decide; this module resolves what they ask about across the mounts first. A
preflight reads a snapshot, so the write root's final admission still runs at commit.
"""
from __future__ import annotations

from collections.abc import Callable

from beliefs import stored
from beliefs.reservation import (
    UNREAD,
    CheckRefusal,
    ExposureEvent,
    KindOf,
    ReservationAssignment,
    assignment_head,
    assignment_record_refusal,
    assignment_succession_refusal,
    exposure_event_refusal,
)
from nodes.core.node import Node
from nodes.core.relations import Relation

from science.lookup import Located, require_citation_pins, session_record, world_record
from science.refusal import Refusal, Refused
from science.reservation.records import LiveRecords

__all__ = ["admit_assignment", "admit_event", "require_unoccupied"]


def require_unoccupied(ctx, address: str, kind: str) -> None:
    """Refuse when any configured live mount already holds the derived address, under either kind."""
    found = world_record(ctx, address)
    if found is None:
        return
    entry: dict[str, object] = {"address": found.address, "uid": found.node.uid, "corpora": list(found.corpora)}
    if found.address != address:
        entry["redirect"] = True
    if found.node.kind == kind:
        raise Refused(Refusal("invalid-input", f"{found.address} is already recorded", {"existing": [entry]}))
    entry["kind"] = found.node.kind
    raise Refused(Refusal("invalid-input", f"{found.address} is already held as a {found.node.kind}", {"occupied": entry}))


def _refuse(check: CheckRefusal | None) -> None:
    if check is not None:
        raise Refused(Refusal("invalid-input", f"{check.code}: {check.detail}",
                              {"kind": "ReservationRefused", "check": check.code}))


def _asked(check: Callable[[KindOf], CheckRefusal | None]) -> tuple[str, ...]:
    """The kernel references a record check asks about, in the kernel's slot order."""
    refs: list[str] = []

    def note(ref: str):
        refs.append(ref)
        return UNREAD

    check(note)
    return tuple(dict.fromkeys(refs))


def _citations(ctx, refs: tuple[str, ...]) -> dict[str, Located]:
    """Each reference's session record, every holder's pins agreeing, or one refusal naming all that resolve
    nowhere the session mounts."""
    found = {ref: session_record(ctx, ref) for ref in refs}
    unresolved = [ref for ref, located in found.items() if located is None]
    if unresolved:
        data: dict[str, object] = {"unresolved": unresolved}
        message = f"cited record(s) not in the session's corpora: {', '.join(unresolved)}"
        unmounted = {ref: list(held.corpora) for ref in unresolved if (held := world_record(ctx, ref)) is not None}
        if unmounted:
            data["unmounted"] = unmounted
            message += (f"; configured read mount(s) hold {', '.join(unmounted)}, "
                        "but coordination = false mounts only the write root")
        raise Refused(Refusal("invalid-input", message, data))
    for ref in refs:
        require_citation_pins(ctx, ref)
    return {ref: located for ref, located in found.items() if located is not None}


def admit_event(ctx, value: ExposureEvent, node: Node) -> None:
    def check(kind_of: KindOf) -> CheckRefusal | None:
        return exposure_event_refusal(value, node.relations, kind_of=kind_of, sorts=ctx.config.profile.sorts)

    cited = _citations(ctx, _asked(check))
    _refuse(check(lambda ref: cited[ref].node.kind))


def admit_assignment(ctx, value: ReservationAssignment, node: Node) -> None:
    """The record's own rules, then its chain over every live mount, then its succession. A successor's
    predecessor is a record this act supersedes, so it must be the write root's own."""
    predecessor = None
    relations = list(node.relations)
    if value.predecessor is not None:
        predecessor = ctx.own(value.predecessor).get(value.predecessor)
        relations.append(Relation(source=node.id, predicate=stored.SUPERSEDES, target=value.predecessor))
    cited: dict[str, Located] = {}

    def record(ref: str) -> Node:
        return predecessor if predecessor is not None and ref == value.predecessor else cited[ref].node

    def check(kind_of: KindOf) -> CheckRefusal | None:
        return assignment_record_refusal(
            value, relations, kind_of=kind_of, sorts=ctx.config.profile.sorts,
            assignment_of=lambda ref: stored.reservation_assignment_value(record(ref)))

    cited.update(_citations(ctx, tuple(ref for ref in _asked(check) if ref != value.predecessor)))
    if value.predecessor is not None:
        require_citation_pins(ctx, value.predecessor)
    _require_head(ctx, value)
    _refuse(check(lambda ref: record(ref).kind))
    _refuse(assignment_succession_refusal(
        value, None if predecessor is None else stored.reservation_assignment_value(predecessor)))


def _require_head(ctx, value: ReservationAssignment) -> None:
    """The chain's one visible head is the predecessor, and a root's chain has none."""
    found = assignment_head(LiveRecords.capture(ctx, "reservation-assignment"), value.chain, scope=value.scope)
    head = None if found is None else found.id
    if head == value.predecessor:
        return
    where = f"chain {value.chain!r} (scope {value.scope!r})"
    message = (f"{where} already has the head {head}" if value.predecessor is None else
               f"{where} has {'no visible head' if head is None else f'the head {head}'}, "
               f"not the predecessor {value.predecessor}")
    raise Refused(Refusal("invalid-input", message, {"chain": value.chain, "scope": value.scope, "head": head,
                                                     "predecessor": value.predecessor}))
