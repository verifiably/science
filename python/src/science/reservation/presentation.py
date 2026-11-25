"""Report blocks for exposure events and assignment changes."""
from __future__ import annotations

import json
from collections.abc import Iterable

from beliefs.reservation import ExposureEvent, Group, GroupChange, TermUnit, Unit

from science.report import KeyVals

__all__ = ["changes_block", "event_block", "group_text", "one_line", "unit_text"]


def one_line(text: str) -> str:
    """Text a record supplies, quoted when a control character in it could start another report line."""
    return text if text.isprintable() else json.dumps(text, ensure_ascii=False)


def unit_text(unit: Unit) -> str:
    if isinstance(unit, TermUnit):
        return f"{unit.sort} {json.dumps(unit.term, ensure_ascii=False)}"
    return f"{unit.start} .. {unit.end}"


def _listed(items: Iterable[str]) -> str:
    return ", ".join(items) or "none"


def group_text(group: Group) -> str:
    text = _listed(unit_text(unit) for unit in group.units)
    if group.label is not None:
        text += f"; label {one_line(group.label)}"
    if group.basis is not None:
        text += f"; basis {group.basis}"
    return text


def event_block(event: ExposureEvent) -> KeyVals:
    return KeyVals(event.id, (
        ("observed at", event.observed_at),
        ("channel", event.channel),
        ("subjects", _listed(one_line(ref) for ref in event.subjects)),
        ("units", _listed(unit_text(unit) for unit in event.units)),
        ("effect", event.effect),
        ("class", one_line(event.read_class)),
        ("observer", one_line(event.observer)),
    ))


def changes_block(changes: tuple[GroupChange, ...]) -> KeyVals:
    pairs = [("count", str(len(changes)))]
    for change in changes:
        text = unit_text(change.unit)
        if change.previous_role is not None:
            text += f"; was {change.previous_role}"
        if change.suspended:
            text += "; suspended"
        pairs.append((change.kind, text))
    return KeyVals("changes from the predecessor", tuple(pairs))
