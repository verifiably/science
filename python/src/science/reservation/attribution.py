"""Whose an exposure event is: the program's whose project query claims it.

The kernel names no program on an event. A project claims an address when a clause of its query holds one
`addresses` predicate naming it and nothing else: the kernel intersects a clause's predicates, so an address
beside another predicate may be selected by neither the query nor a publication.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from beliefs.coordination import CoordinationAddress
from beliefs.reservation import ExposureEvent
from beliefs.view_query import Addresses, ViewQuery, stored_query

from science.coordination import selected_project, tip_nodes

__all__ = ["ANOTHER_PROGRAM", "PROGRAM", "UNATTRIBUTED", "Claims", "claimed_events", "differing_events", "read_claims"]

PROGRAM, ANOTHER_PROGRAM, UNATTRIBUTED = "program", "another-program", "unattributed"
_EVENT = "exposure-event:"


def claimed_events(query: ViewQuery) -> frozenset[str]:
    """The exposure events the query claims."""
    return frozenset(address for clause in query.clauses if len(clause.predicates) == 1
                     for predicate in clause.predicates if isinstance(predicate, Addresses)
                     for address in predicate.values if address.startswith(_EVENT))


def differing_events(query: ViewQuery, selection: Iterable[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(selected and not claimed, claimed and not selected): the exposure events a reader of `selection` and the
    author under `query` would judge differently. Both are empty when a publication may be relied on."""
    claimed = claimed_events(query)
    selected = {address for address in selection if address.startswith(_EVENT)}
    return tuple(sorted(selected - claimed)), tuple(sorted(claimed - selected))


@dataclass(frozen=True)
class Claims:
    """What the selected project claims and what every other standing project does, or no project. `project` is
    pinned to the revision read."""
    project: CoordinationAddress | None
    own: frozenset[str] = frozenset()
    others: frozenset[str] = frozenset()

    def whose(self, event: ExposureEvent) -> str:
        if self.project is None or event.id in self.own:
            return PROGRAM
        return ANOTHER_PROGRAM if event.id in self.others else UNATTRIBUTED


def read_claims(ctx) -> Claims:
    """The selection's one standing tip, or a refusal. Another project with divergent tips claims what any of
    them claims, as retention keeps what any tip needs."""
    project = selected_project(ctx)
    if project is None:
        return Claims(None)
    resolver = ctx.coordination()
    others: frozenset[str] = frozenset()
    for address, resolved in resolver.standing("project").items():
        if address != ctx.selection:
            others = others.union(*(claimed_events(stored_query(node)) for node in tip_nodes(resolver, resolved)))
    return Claims(ctx.selection.pinned(project.uid), claimed_events(stored_query(project)), others)
