"""Freeze a typed estimand against accepted session-held prerequisites."""
from __future__ import annotations

from dataclasses import fields
from decimal import Decimal, InvalidOperation
from pathlib import Path

from beliefs import stored
from beliefs.applicability import ScopedRestriction, build_applicability
from beliefs.claim import Referent
from beliefs.dataset import dataset_address
from beliefs.decode import claim_from_stored
from beliefs.errors import ScienceError
from beliefs.estimand import build_estimand, estimand_referents
from beliefs.restriction import TermRestriction
from beliefs.rules import REFERENCE_RULES
from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze
from science.authoring_records import session_records
from science.estimand_input import read_estimand_input
from science.refusal import AUTHORING_INPUT_ERRORS, Refusal, Refused, kernel_refusal
from science.report import Report, record_block
from science.vocabulary import require_performed


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def _decimal(name: str, value: str) -> Decimal:
    try:
        number = Decimal(value)
    except InvalidOperation:
        _refuse(f"{name} {value!r} is not a decimal")
    if not number.is_finite():
        _refuse(f"{name} {value!r} is not finite")
    return number


def parse_parameters(entries) -> dict[str, Decimal]:
    parameters = {}
    for entry in entries or ():
        name, sep, value = entry.partition("=")
        if not sep or not name:
            _refuse(f"parameter {entry!r} is not name=value")
        parameters[name] = _decimal(f"parameter {name}", value)
    return parameters


def _rule(identity: str):
    implementation = REFERENCE_RULES.get(identity)
    if implementation is None:
        _refuse(f"no reference rule {identity!r}; the kernel ships {sorted(REFERENCE_RULES)}")
    return implementation


def _rule_procedures(entries):
    bindings = {}
    for entry in entries:
        name, sep, procedure = entry.partition("=")
        if not sep or not name or not procedure:
            _refuse(f"rule procedure {entry!r} must be rule-identity=procedure-id")
        if name in bindings:
            _refuse(f"duplicate rule procedure binding {name!r}")
        bindings[name] = procedure
    return bindings


def _applicability(profile, entries):
    scoped, referents = {}, {}
    for entry in entries or ():
        dimension, sep, rest = entry.partition("=")
        quantifier, colon, term = rest.partition(":")
        if not sep or not dimension or not colon or not quantifier or not term:
            _refuse(f"applicability {entry!r} is not dimension=quantifier:term")
        declared = profile.dimensions.get(dimension)
        if declared is None:
            _refuse(f"applicability has no dimension {dimension!r}")
        restriction = declared.restriction
        form = None if restriction is None else restriction.form
        if declared.placement != "applicability" or form != "term":
            _refuse(f"applicability dimension {dimension!r} has incompatible placement {declared.placement!r} / form {form!r}; this input requires applicability term restrictions")
        scoped[dimension] = ScopedRestriction(quantifier, TermRestriction(restriction.sort, term))
        referents[f"restriction:{dimension}"] = Referent(restriction.sort, term)
    return scoped, referents


def handle(ctx, writer, *, target, dataset, estimand, standing, evidence_mode, rule_procedures,
           method, assumptions, falsification, interpretation_rule, equivalence_rule,
           model=None, registers=None, applicability=None, parameters=None, supersedes=None) -> Report:
    profile = ctx.config.profile
    try:
        document = read_estimand_input(Path(estimand), profile=profile)
        superseded = None
        if supersedes is not None:
            superseded = stored.local_id("analysis-spec", supersedes)
            ctx.own(supersedes)
        held_rules = {interpretation_rule: _rule(interpretation_rule), equivalence_rule: _rule(equivalence_rule)}
        bindings = _rule_procedures(rule_procedures)
        with session_records(ctx) as records:
            # Keep the established missing/outside-session citation diagnostic;
            # accepted equal copies are chosen by the captured session reader.
            for ref in (target, dataset):
                if not records.holds(ref):
                    ctx.cited(ref)
            target_node, dataset_node = records.read(target), records.read(dataset)
            address = dataset_address(stored.dataset_declaration(dataset_node))
            if address is None:
                _refuse(f"{dataset} declares no content identity")
            snapshot = ctx.authoring_snapshot(records=records)
            claim, _ = claim_from_stored(target_node, profile=profile, snapshot=snapshot)
            scoped, scope_refs = _applicability(profile, applicability)
            scoped, scope_receipt = build_applicability(profile, claim, scoped, snapshot=snapshot)
            value, receipt = build_estimand(profile, claim,
                **{f.name: getattr(document, f.name) for f in fields(document)},
                applicability=scoped, snapshot=snapshot, records=records,
                assessment_dependency=records.assessment_dependency)
            require_performed(profile, receipt, {f"estimand:{label}": ref for label, ref in estimand_referents(value).items()})
            require_performed(profile, scope_receipt, scope_refs)
            draft = SpecDraft(target=target_node.id, estimand=value, method=method, assumptions=assumptions,
                falsification=falsification, input_roles=(SpecInput(role="observes", dataset=address, mode=evidence_mode),),
                applicability=scoped, interpretation_rule=interpretation_rule, equivalence_rule=equivalence_rule,
                parameters=parse_parameters(parameters), nondeterminism=Deterministic(),
                standing=standing, model=model, registers=tuple(registers or ()))
            spec = freeze(draft, held_rules=held_rules, rule_procedures=bindings, profile=profile,
                          claim=claim, records=records, assessment_dependency=records.assessment_dependency,
                          supersedes=superseded)
    except AUTHORING_INPUT_ERRORS as caught:
        raise Refused(Refusal("invalid-input", f"spec authoring refused: {caught}",
                              {"kind": type(caught).__name__})) from caught
    except ScienceError as caught:
        raise Refused(kernel_refusal(caught)) from caught
    # Input captures are released before the writer obtains its mint authority.
    node = writer.add(stored.analysis_spec_node(spec))
    return (record_block(node),)
