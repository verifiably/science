"""Strict JSON authoring input into public kernel estimand members.

This boundary checks representation. Scientific admission and frozen dependencies
remain the responsibility of build_estimand and freeze.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from types import MappingProxyType

from beliefs.assumptions import AssumptionInstance, instance_from_projection
from beliefs.claim import Referent
from beliefs.estimand import (
    AxisLevels, Binding, Control, DatasetBinding, IncrementBinding, LagBinding,
    MeasuredBinding, NullReference, OutputSpec, Reference, RoleAnchor, RoleBinding,
    RoleLevels, RoleTermLevels, RuleAnchor, RuleClassLevels, ValueReference,
)
from beliefs.measurement import measure_from_projection
from beliefs.profile import ProfileSpec
from beliefs.restriction import restriction_from_projection
from science.refusal import Refusal, Refused

__all__ = ["EstimandInput", "read_estimand_input"]


@dataclass(frozen=True)
class EstimandInput:
    form: str
    functional: str
    bindings: Mapping[str, Binding]
    outputs: Mapping[str, OutputSpec]
    reference: Reference | Mapping[str, Reference]
    control: Control
    uncertainty: str
    assumptions: tuple[AssumptionInstance, ...]
    calibration: str | None


def _shape(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or set(value) - set(required) - set(optional):
        raise ValueError(f"expected object fields {sorted(required)}, optional {sorted(optional)}")
    return value


def _text(value):
    if type(value) is not str or not value:
        raise ValueError("expected a nonempty string")
    return value


def _array(value):
    if type(value) is not list:
        raise ValueError("expected an array")
    return value


def _mapping(value):
    if type(value) is not dict:
        raise ValueError("expected an object")
    return value


def _decimal(value):
    if type(value) is int:
        value = Decimal(value)
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("expected a finite numeric literal")
    return value


def _referent(value):
    body = _shape(value, {"sort", "term"})
    return Referent(_text(body["sort"]), _text(body["term"]))


def _interval(value):
    return restriction_from_projection(value, form="interval")


def _measured(value):
    body = _shape(value, {"role", "measure"}, {"member", "mapping", "proxy"})
    return MeasuredBinding(_text(body["role"]), _referent(body["member"]) if "member" in body else None,
                           measure_from_projection(body["measure"]),
                           _text(body["mapping"]) if "mapping" in body else None,
                           _text(body["proxy"]) if "proxy" in body else None)


def _binding(value, variable):
    if variable in {"variables", "independent"}:
        result = []
        for raw in _array(value):
            row = _shape(raw, {"name", "binding"})
            result.append((_text(row["name"]), _measured(row["binding"])))
        return tuple(result)
    if variable == "universe":
        return DatasetBinding(_text(_shape(value, {"digest"})["digest"]))
    if variable == "lag":
        body = _shape(value, {"unit", "windows"})
        return LagBinding(_text(body["unit"]), tuple(_interval(v) for v in _array(body["windows"])))
    body = _mapping(value)
    if "rule" in body:
        body = _shape(body, {"rule", "classes"}, {"source"} if variable == "grouping" else ())
        classes = tuple(_referent(v) for v in _array(body["classes"]))
        if variable == "grouping":
            if body.get("source") != "rule-classes":
                raise ValueError("grouping rule source must be rule-classes")
            return RuleClassLevels(_text(body["rule"]), classes)
        return RuleAnchor(_text(body["rule"]), classes)
    if body.get("source") == "roles":
        body = _shape(body, {"source", "roles"})
        roles = tuple(_measured(v) for v in _array(body["roles"]))
        if len(roles) != 2:
            raise ValueError("roles grouping requires exactly two measured roles")
        return RoleLevels(roles)
    if body.get("source") == "axis":
        body = _shape(body, {"source", "levels"})
        return AxisLevels(tuple(_interval(v) for v in _array(body["levels"])))
    if variable == "response":
        return _measured(body)
    required = {"role"}
    if variable == "grouping":
        required.update({"measure", "increment"} if "increment" in body else {"levels"})
    elif variable == "anchor":
        required.add("category")
    body = _shape(body, required, {"member"})
    role = _text(body["role"])
    member = _referent(body["member"]) if "member" in body else None
    if variable == "grouping":
        if "increment" in body:
            inc = _shape(body["increment"], {"value", "unit"})
            return IncrementBinding(role, member, measure_from_projection(body["measure"]),
                                    _decimal(inc["value"]), _text(inc["unit"]))
        levels = _shape(body["levels"], {"source", "levels"})
        if levels["source"] != "role-terms":
            raise ValueError("role grouping levels require source role-terms")
        return RoleTermLevels(role, member, tuple(_referent(v) for v in _array(levels["levels"])))
    if variable == "anchor":
        return RoleAnchor(role, member, _referent(body["category"]))
    return RoleBinding(role, member)


def _reference(value):
    body = _mapping(value)
    if body.get("kind") == "value":
        return ValueReference(_decimal(_shape(body, {"kind", "value"})["value"]))
    body = _shape(body, {"kind", "region"})
    if body["kind"] != "null":
        raise ValueError("reference kind must be value or null")
    region = _shape(body["region"], {"low", "high"})
    return NullReference(_decimal(region["low"]), _decimal(region["high"]))


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"non-finite JSON constant {value}")


def read_estimand_input(path: Path, *, profile: ProfileSpec) -> EstimandInput:
    """Read once; preserve kernel exceptions for the command's refusal boundary."""
    try:
        body = _shape(json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal,
                                 parse_constant=_constant, object_pairs_hook=_pairs),
                      {"schema_version", "form", "functional", "bindings", "outputs", "reference",
                       "control", "uncertainty", "assumptions"}, {"calibration"})
        if type(body["schema_version"]) is not int or body["schema_version"] != 1:
            raise ValueError("schema_version must be exact integer 1")
        outputs = {}
        for name, value in _mapping(body["outputs"]).items():
            row = _shape(value, {"typing", "domain"}, {"quantity_kind", "unit", "scale"})
            outputs[_text(name)] = OutputSpec(**{key: _text(v) for key, v in row.items()})
        control = _shape(body["control"], {"identification", "conditioning", "design", "selection"})
        reference = _mapping(body["reference"])
        reference = (_reference(reference) if type(reference.get("kind")) is str else
                     MappingProxyType({_text(k): _reference(v) for k, v in reference.items()}))
        return EstimandInput(
            _text(body["form"]), _text(body["functional"]),
            MappingProxyType({_text(k): _binding(v, k) for k, v in _mapping(body["bindings"]).items()}),
            MappingProxyType(outputs), reference,
            Control(_text(control["identification"]), tuple(_referent(v) for v in _array(control["conditioning"])),
                    _text(control["design"]), _text(control["selection"])),
            _text(body["uncertainty"]), tuple(instance_from_projection(v) for v in _array(body["assumptions"])),
            _text(body["calibration"]) if "calibration" in body else None,
        )
    except (OSError, UnicodeError, ValueError, InvalidOperation) as caught:
        raise Refused(Refusal("invalid-input", f"estimand input {path}: {caught}",
                              {"kind": type(caught).__name__})) from caught
