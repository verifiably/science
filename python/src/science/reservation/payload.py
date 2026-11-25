"""The strict JSON envelope both write commands read: a title and one kernel facet, less its writer.

This boundary checks representation. References, sorts and chains are checked against the world by
`science.reservation.admission`.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from beliefs.errors import IdentityError, MalformedRecord
from beliefs.identity import v1
from beliefs.reservation import (
    ExposureEvent,
    ReservationAssignment,
    exposure_event_from_facet,
    reservation_assignment_from_facet,
)

from science.refusal import Refusal, Refused

__all__ = ["EXPOSURE_EVENT", "RESERVATION_ASSIGNMENT", "Payload", "RecordForm", "read_payload"]

_ENVELOPE = frozenset({"schema_version", "title", "facet"})


@dataclass(frozen=True)
class RecordForm:
    """What an envelope's facet decodes as, and the field the session's writer fills in."""
    kind: str
    writer_field: str
    decode: Callable[[Mapping[str, object]], ExposureEvent | ReservationAssignment]


EXPOSURE_EVENT = RecordForm("exposure-event", "recorded_by", exposure_event_from_facet)
RESERVATION_ASSIGNMENT = RecordForm("reservation-assignment", "assigned_by", reservation_assignment_from_facet)


@dataclass(frozen=True)
class Payload:
    title: str
    value: ExposureEvent | ReservationAssignment


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"non-finite JSON constant {value}")


def _document(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_constant, object_pairs_hook=_unique)


def _encodable_line(value: object) -> bool:
    if type(value) is not str or not value.strip() or "\n" in value or "\r" in value:
        return False
    try:
        v1.encode(value)
    except IdentityError:
        return False
    return True


def read_payload(path: Path, form: RecordForm, *, actor: str) -> Payload:
    """Read the envelope once and decode its facet under `actor` as the writer. Messages name the file
    alone: under a run handle its directory is the endpoint's private capture."""
    def refuse(message: str, **data: object):
        return Refused(Refusal("invalid-input", f"{form.kind} payload {path.name}: {message}", data))

    try:
        document = _document(path)
    except OSError as caught:
        raise refuse(caught.strerror or type(caught).__name__, kind=type(caught).__name__) from caught
    except (ValueError, RecursionError) as caught:
        raise refuse(str(caught), kind=type(caught).__name__) from caught
    if type(document) is not dict or set(document) != _ENVELOPE:
        raise refuse(f"expected one object with exactly {sorted(_ENVELOPE)}", field="envelope")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise refuse("schema_version must be the integer 1", field="schema_version")
    title, facet = document["title"], document["facet"]
    if not _encodable_line(title):
        raise refuse("title must be a single non-empty line of v1-encodable text", field="title")
    if type(facet) is not dict:
        raise refuse("facet must be an object", field="facet")
    if form.writer_field in facet:
        raise refuse(f"the session supplies {form.writer_field}; omit it", field=f"facet.{form.writer_field}")
    complete = {**facet, form.writer_field: actor}
    try:
        value = form.decode(complete)
        canonical = value.facet()
        value.identity()
    except (MalformedRecord, IdentityError) as caught:
        raise refuse(str(caught), kind=type(caught).__name__) from caught
    if canonical != complete:
        differing = sorted(key for key in complete.keys() | canonical.keys()
                           if complete.get(key, _ENVELOPE) != canonical.get(key, _ENVELOPE))
        raise refuse(f"the facet is not canonical at {', '.join(differing)}; omit an optional field instead of "
                     "giving it null or an empty value", field="facet", noncanonical=differing)
    return Payload(title, value)
