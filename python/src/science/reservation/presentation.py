"""Report blocks for exposure events and assignment changes."""
from __future__ import annotations

import json
from collections.abc import Iterable

from beliefs.reservation import ExposureEvent, Group, GroupChange, TermUnit, Unit

from science.report import KeyVals

__all__ = ["changes_block", "event_block", "group_text", "one_line", "quoted", "unit_text"]

_JSON_ESCAPES = {'"': r'\"', "\\": r"\\", "\b": r"\b", "\f": r"\f", "\n": r"\n", "\r": r"\r", "\t": r"\t"}


def _escape(ch: str) -> str:
    if ch in _JSON_ESCAPES:
        return _JSON_ESCAPES[ch]
    if ch.isprintable():
        return ch
    return r"\u007f" if ord(ch) == 0x7F else json.dumps(ch, ensure_ascii=True)[1:-1]


def quoted(text: str) -> str:
    """Text quoted as a single-line JSON string, with every non-printable character escaped."""
    return '"' + "".join(_escape(ch) for ch in text) + '"'


def one_line(text: str) -> str:
    """Text a record supplies, quoted when a non-printable character in it could start another report line."""
    return text if text.isprintable() else quoted(text)


def unit_text(unit: Unit) -> str:
    if isinstance(unit, TermUnit):
        return f"{unit.sort} {quoted(unit.term)}"
    return f"{unit.start} .. {unit.end}"


def _listed(items: Iterable[str]) -> str:
    return ", ".join(items) or "none"


def group_text(group: Group) -> str:
    text = _listed(unit_text(unit) for unit in group.units)
    if group.label is not None:
        text += f"; label {quoted(group.label)}"
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
