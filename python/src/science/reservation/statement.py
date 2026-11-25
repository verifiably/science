"""A reservation chain's statement: the JSON file and the page a program's repository holds, rendered from the
chain's records alone, so the head's address determines every byte."""
from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unicodedata import normalize

from beliefs import stored
from beliefs.reservation import (
    ExposureEvent,
    ReservationAssignment,
    Unit,
    assignment_changes,
    assignment_head,
    unit_facet,
    unit_from_facet,
)
from nodes.core.errors import RefError

from science.refusal import Refusal, Refused
from science.reservation.page import render_page
from science.reservation.records import LiveRecords

__all__ = ["Statement", "read_statement", "require_current", "statement_digest", "statement_paths", "write_files"]

SCHEMA_VERSION = 1
_KIND = "reservation-assignment"
_SCOPE = "proposition:"
# History fields carried over from each assignment's facet when the record has them.
_CARRIED = ("account", "applies", "evidence", "flagged", "participants", "prior_runs")


@dataclass(frozen=True)
class Statement:
    head: ReservationAssignment
    json: bytes
    page: bytes


def _nfc(value):
    """The spelling the kernel's identity is computed over: two corpora may hold one address spelled differently."""
    if isinstance(value, str):
        return normalize("NFC", value)
    if isinstance(value, dict):
        return {_nfc(key): _nfc(member) for key, member in value.items()}
    if isinstance(value, list):
        return [_nfc(member) for member in value]
    return value


def _invalid(message: str, **data: object) -> Refused:
    return Refused(Refusal("invalid-input", message, data))


def _named(records: LiveRecords, ref: str, chain: str, scope: str | None) -> ReservationAssignment:
    """The assignment `ref` names, of exactly this chain and scope. The chain's head is not looked for."""
    try:
        node = records.get(ref)
    except RefError:
        raise _invalid(f"{ref}: no configured live corpus holds it", field="as_of") from None
    if node.kind != _KIND:
        raise _invalid(f"{ref} is a {node.kind}, not a {_KIND}", field="as_of")
    value = stored.reservation_assignment_value(node)
    if (value.chain, value.scope) != (chain, scope):
        raise _invalid(f"{ref} is of chain {value.chain!r} (scope {value.scope!r}), not {chain!r} (scope {scope!r})",
                       field="as_of", chain=value.chain, scope=value.scope)
    return value


def _line(records: LiveRecords, head: ReservationAssignment) -> tuple[ReservationAssignment, ...]:
    """The head's chain, root first."""
    line = [head]
    while (ref := line[-1].predecessor) is not None:
        line.append(stored.reservation_assignment_value(records.get(ref)))
    return tuple(reversed(line))


@dataclass(frozen=True)
class _Spelled:
    """A kernel group under NFC spelling, for comparison only: a constructed `Group` would refuse a unit order
    that normalization moved."""
    units: tuple[Unit, ...]
    role: str
    label: str | None
    basis: str | None

    @property
    def first(self) -> Unit:
        return self.units[0]


def _spelled(value: ReservationAssignment) -> SimpleNamespace:
    return SimpleNamespace(groups=tuple(
        _Spelled(tuple(unit_from_facet(_nfc(unit_facet(unit))) for unit in group.units), group.role,
                 _nfc(group.label), group.basis) for group in value.groups))


def _history_entry(value: ReservationAssignment, predecessor: ReservationAssignment | None) -> dict:
    facet = _nfc(value.facet())
    before = {"groups": facet["groups"], "events": [], "inputs": {}} if predecessor is None else _nfc(predecessor.facet())
    changes = () if predecessor is None else assignment_changes(_spelled(predecessor), _spelled(value))
    entry = {
        "address": value.id,
        "assigned_at": facet["assigned_at"],
        "assigned_by": facet["assigned_by"],
        "rule": facet["rule"],
        **{key: facet[key] for key in _CARRIED if key in facet},
        "changes": [{"kind": change.kind, "unit": unit_facet(change.unit), "suspended": change.suspended,
                     **({} if change.previous_role is None else {"previous_role": change.previous_role})}
                    for change in changes],
        "groups_removed": [group for group in before["groups"] if group not in facet["groups"]],
        "groups_added": [group for group in facet["groups"] if group not in before["groups"]],
        "events_added": [ref for ref in facet["events"] if ref not in before["events"]],
        "events_dropped": [ref for ref in before["events"] if ref not in facet["events"]],
        "inputs_changed": sorted(name for name in {*before["inputs"], *facet["inputs"]}
                                 if before["inputs"].get(name) != facet["inputs"].get(name)),
    }
    return entry


def _content(line: tuple[ReservationAssignment, ...], events: list[ExposureEvent]) -> dict:
    head = line[-1]
    content = {
        "schema_version": SCHEMA_VERSION,
        "chain": head.chain,
        "head": {"address": head.id, "facet": _nfc(head.facet())},
        "history": [_history_entry(value, predecessor)
                    for predecessor, value in zip((None, *line), line, strict=False)],
        "events": [{"address": event.id, "facet": _nfc(event.facet())} for event in events],
    }
    if head.scope is not None:
        content["scope"] = head.scope
    return content


def read_statement(records: LiveRecords, chain: str, scope: str | None, as_of: str | None) -> Statement:
    """The statement of the chain's one head, or of `as_of` as it stood when it was the head."""
    records = records.of(_KIND)
    head = assignment_head(records, chain, scope=scope) if as_of is None else _named(records, as_of, chain, scope)
    if head is None:
        raise Refused(Refusal("chain-absent", f"chain {chain!r} (scope {scope!r}) has no record in the configured "
                                              "live corpora", {"chain": chain, "scope": scope}))
    events = [stored.exposure_event_value(records.get(ref)) for ref in head.events]
    content = _content(_line(records, head), sorted(events, key=lambda event: (event.observed_at, event.id)))
    text = json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return Statement(head, text.encode(), render_page(content).encode())


def statement_paths(directory: Path, chain: str, scope: str | None) -> tuple[Path, Path]:
    """The JSON file and the page."""
    name = chain if scope is None else f"{chain}/{_slug(scope)}"
    return directory / f"{name}.json", directory / f"{name}.md"


def _slug(scope: str) -> str:
    slug = scope.removeprefix(_SCOPE)
    if slug in (".", "..") or "/" in slug or "\x00" in slug:
        raise _invalid(f"scope {scope!r} does not name one path segment", field="scope")
    return slug


def require_current(statement: Statement, directory: Path, paths: tuple[Path, Path]) -> None:
    """Refuse unless both files hold exactly the rendered bytes."""
    stale, states = [], []
    for path, content in zip(paths, (statement.json, statement.page), strict=True):
        try:
            found = path.read_bytes()
        except FileNotFoundError:
            found = None
        except OSError as caught:
            raise _invalid(f"{path}: {caught.strerror or type(caught).__name__}", kind=type(caught).__name__) from caught
        if found != content:
            name = path.relative_to(directory).as_posix()
            stale.append(name)
            states.append(f"{name} {'is missing' if found is None else 'differs'}")
    if stale:
        raise Refused(Refusal("statement-stale", f"{'; '.join(states)} from the statement of {statement.head.id}",
                              {"head": statement.head.id, "files": stale}))


def statement_digest(content: bytes) -> str:
    return f"sha256:{sha256(content).hexdigest()}"


def write_files(statement: Statement, paths: tuple[Path, Path]) -> None:
    """Replace each file atomically, the page before the JSON: an interruption between them leaves a pair that
    `require_current` reports, naming the file still to be written."""
    json_path, page_path = paths
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        _replace(page_path, statement.page)
        _replace(json_path, statement.json)
    except OSError as caught:
        raise _invalid(f"{caught.filename}: {caught.strerror or type(caught).__name__}",
                       kind=type(caught).__name__) from caught


def _replace(path: Path, content: bytes) -> None:
    partial = path.with_name(f".{secrets.token_hex(8)}.partial")
    try:
        with partial.open("xb") as out:
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.replace(partial, path)
    finally:
        partial.unlink(missing_ok=True)
