"""Input canonicalization: the one form digests and schemas are computed over."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from science.refusal import Refusal, Refused
from science.schema import Declaration

_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "bool": lambda v: isinstance(v, bool),
    "enum": lambda v: isinstance(v, str),
    "list-of-string": lambda v: isinstance(v, list) and all(isinstance(x, str) for x in v),
}


def _refuse(message: str, **data: object) -> None:
    raise Refused(Refusal("invalid-input", message, data))


def canonicalize(decl: Declaration, provided: Mapping[str, object]) -> dict[str, object]:
    known = {i.name: i for i in decl.inputs}
    unknown = set(provided) - set(known)
    if unknown:
        _refuse(f"unknown inputs {sorted(unknown)}", command=decl.name)
    out: dict[str, object] = {}
    for spec in decl.inputs:
        if spec.name in provided:
            value = provided[spec.name]
            if value is None:
                _refuse(f"input {spec.name!r} is null; omit it instead", field=spec.name)
        else:
            value = spec.default
        if value is None:
            if spec.required:
                _refuse(f"missing required input {spec.name!r}", field=spec.name)
            continue
        if not _CHECKS[spec.type](value):
            _refuse(f"input {spec.name!r} is not a {spec.type}", field=spec.name)
        if spec.type == "enum" and value not in spec.choices:
            _refuse(f"input {spec.name!r} must be one of {list(spec.choices)}", field=spec.name)
        out[spec.name] = value
    return dict(sorted(out.items()))


def input_digest(canonical: Mapping[str, object]) -> str:
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()
