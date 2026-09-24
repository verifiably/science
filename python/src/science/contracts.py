"""Corpus-local contract documents (belief-path design §5.2).

A document carries a domain contract and optionally the operator plan that
maps authored claim terms to that contract. The plan is launcher input and is
not covered by the contract identity. This is superseded when the kernel gives
contracts a home (belief-path design ruling 5).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

from beliefs.contract.domain import DomainContract, parse_domain_contract
from beliefs.errors import MalformedContract

from science.refusal import Refusal, Refused


def _refuse(message: str) -> None:
    raise Refused(Refusal("invalid-input", message))


@dataclass(frozen=True)
class OperatorPlan:
    namespace: str
    operators: Mapping[tuple[str, str | None, str | None], str]
    sorts: Mapping[str, str]
    layers: Mapping[str, str]
    polarities: Mapping[str, str | None]

    def operator_for(self, predicate: str, subject_kind: str, object_kind: str) -> str:
        operator = self.operators.get((predicate, subject_kind, object_kind))
        if operator is None:
            operator = self.operators.get((predicate, None, None))
        if operator is None:
            _refuse(
                f"no plan row for {predicate} {subject_kind}->{object_kind} in contract "
                f"{self.namespace!r}; a shape with no row is refused, never nearest-typed"
            )
        return operator

    def sort_for(self, kind: str) -> str:
        sort = self.sorts.get(kind)
        if sort is None:
            _refuse(f"kind prefix {kind!r} maps to no sort in contract {self.namespace!r}'s plan")
        return sort


def _term(domain: DomainContract, name: str) -> str:
    return name if "/" in name else domain.term(name)


def _string_table(raw: dict, name: str, *, nullable: bool = False) -> dict[str, str | None]:
    value = raw.get(name, {})
    if not isinstance(value, dict):
        _refuse(f"plan.{name} must be a table")
    allowed = (str, type(None)) if nullable else (str,)
    if any(type(key) is not str or type(item) not in allowed for key, item in value.items()):
        _refuse(f"plan.{name} keys and values must be strings" + (" or null" if nullable else ""))
    return value


def _plan(raw: object, domain: DomainContract) -> OperatorPlan:
    if not isinstance(raw, dict):
        _refuse("a contract document's plan must be a table")
    rows_raw = raw.get("operators", [])
    if not isinstance(rows_raw, list):
        _refuse("plan.operators must be a list of rows")
    rows: dict[tuple[str, str | None, str | None], str] = {}
    for row in rows_raw:
        if not isinstance(row, dict):
            _refuse("each plan row must be a table")
        predicate = row.get("predicate")
        operator = row.get("operator")
        subject = row.get("subject")
        object_ = row.get("object")
        if type(predicate) is not str or type(operator) is not str:
            _refuse("each plan row names predicate and operator as strings")
        if subject is not None and type(subject) is not str:
            _refuse("a plan row subject must be a string when present")
        if object_ is not None and type(object_) is not str:
            _refuse("a plan row object must be a string when present")
        rows[(predicate, subject, object_)] = _term(domain, operator)
    sorts = _string_table(raw, "sorts")
    layers = _string_table(raw, "layers")
    polarities = _string_table(raw, "polarities", nullable=True)
    return OperatorPlan(
        namespace=domain.namespace,
        operators=rows,
        sorts={key: _term(domain, value) for key, value in sorts.items()},
        layers=layers,
        polarities=polarities,
    )


def load_contract_document(path: Path, base) -> tuple[DomainContract, OperatorPlan | None]:
    if not path.is_file():
        _refuse(f"contract document not found: {path}")
    try:
        document = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as caught:
        _refuse(f"contract document {path} is not readable YAML: {caught}")
    if not isinstance(document, dict) or "contract" not in document:
        _refuse(f"contract document {path} must be a table with a `contract` key")
    unknown = sorted(set(document) - {"contract", "plan"})
    if unknown:
        # The kernel driver's documents carry `also:`; here the config's `domains`
        # names the composed domain contracts, so the key would be dropped unread.
        _refuse(
            f"contract document {path} carries unknown top-level keys {unknown}; "
            "it holds only `contract` and `plan`, and composed domains come from "
            "the config's `domains`"
        )
    try:
        contract = parse_domain_contract(
            document["contract"], source=f"{path}: contract", base=base, predecessor=None
        )
    except MalformedContract as caught:
        _refuse(f"contract document {path} does not parse: {caught}")
    plan = _plan(document["plan"], contract) if "plan" in document else None
    return contract, plan
