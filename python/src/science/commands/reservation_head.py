"""Show one chain's head, its derived changes and the visible events it did not consider."""
from __future__ import annotations

from beliefs.reservation import assignment_changes_of, assignment_head, exposure_events

from science.report import KeyVals, Report
from science.reservation import (
    LiveRecords,
    changes_block,
    event_block,
    group_text,
    kernel_reads,
    one_line,
    require_chain,
    require_reference,
)

__all__ = ["handle"]


def handle(ctx, *, chain: str, scope: str | None = None) -> Report:
    require_chain(chain)
    require_reference("scope", scope, ("proposition:",))
    asked = (("chain", chain), ("scope", scope or "none"))
    with kernel_reads():
        assignments = LiveRecords.capture(ctx, "reservation-assignment")
        head = assignment_head(assignments, chain, scope=scope)
        if head is None:
            return (KeyVals("reservation head", (*asked, ("head", "none"))),)
        title = assignments.get(head.id).title
        changes = assignment_changes_of(assignments, head.id)
        visible = exposure_events(assignments.of("exposure-event"))
    unconsidered = [event for event in visible if event.id not in head.events]
    facts = [*asked, ("head", head.id), ("title", one_line(title)), ("predecessor", head.predecessor or "none"),
             ("rule", f"{one_line(head.rule_name)}, version {one_line(head.rule_version)}")]
    if head.applies is not None:
        facts.append(("applies", head.applies))
    facts += [("assigned at", head.assigned_at), ("assigned by", one_line(head.assigned_by))]
    return (
        KeyVals("reservation head", tuple(facts)),
        KeyVals("frozen inputs", tuple((one_line(name), digest) for name, digest in head.inputs)),
        KeyVals("considered events", (("count", str(len(head.events))), *(("event", ref) for ref in head.events))),
        KeyVals("group roles", (("count", str(len(head.groups))),
                                *((group.role, group_text(group)) for group in head.groups))),
        changes_block(changes),
        KeyVals("visible events not considered by this assignment", (("count", str(len(unconsidered))),)),
        *(event_block(event) for event in unconsidered),
    )
