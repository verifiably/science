"""spec: freeze an analysis spec against the kernel's reference rules (§4.3).

The estimand is typed against the claim it answers: the target's operator
fixes every sort through its contract's `estimands:` declaration, so the
surface takes terms and numbers only, never a sort (design §4.3, amended
2026-09-23)."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from beliefs import stored
from beliefs.claim import Qualifier, Referent
from beliefs.dataset import dataset_address
from beliefs.decode import claim_from_stored
from beliefs.errors import ClaimError, DecodeError, MalformedRecord, ProfileError
from beliefs.estimand import (ESTIMAND_ERRORS, ContinuousContrast, Control, LevelsContrast, Measure,
                              build_applicability, build_estimand)
from beliefs.resolution import ReferentPosition, TermOutcome
from beliefs.rules import REFERENCE_RULES
from beliefs.spec import Deterministic, MalformedSpec, SpecDraft, SpecInput, UnfreezableSpec, freeze

from science.refusal import Refusal, Refused
from science.report import Report, record_block
from science.vocabulary import dataset_bound_sorts

# Every authoring error the kernel raises on this path: kept whole so none
# escapes the handler and leaves the invocation open (design §4.3).
AUTHORING_ERRORS = (*ESTIMAND_ERRORS, ClaimError, DecodeError, ProfileError)
UNRESOLVED = (TermOutcome.NOT_CONSULTED, TermOutcome.NOT_AVAILABLE)


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
    parameters: dict[str, Decimal] = {}
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


def _contrast(decl, contrast, slot, baseline, comparison, quantity, increment):
    """(contrast value, {receipt label: referent}) — or refuse. Nothing is
    defaulted: an input of the other kind, or a missing one of this kind,
    refuses."""
    kinds = {"levels": {"baseline": baseline, "comparison": comparison},
             "continuous": {"quantity": quantity, "increment": increment}}
    stray = sorted(k for kind, given in kinds.items() if kind != contrast for k, v in given.items() if v is not None)
    if stray:
        _refuse(f"{', '.join(stray)} belong to the other contrast kind, not {contrast}")
    missing = sorted(k for k, v in kinds[contrast].items() if v is None)
    if missing:
        _refuse(f"a {contrast} contrast needs {', '.join(missing)}")
    if contrast == "levels":
        sort = decl.level_sorts.get(str(slot))
        if sort is None:
            _refuse(f"{decl.operator} declares no level sort for slot {slot}; "
                    f"its levels are declared for slots {sorted(decl.level_sorts, key=int)}")
        low, high = Referent(sort, baseline), Referent(sort, comparison)
        return (LevelsContrast(slot=slot, baseline=low, comparison=high),
                {"contrast.baseline": low, "contrast.comparison": high})
    along = Referent(decl.measure_sort, quantity)
    return (ContinuousContrast(slot=slot, quantity=along, increment=_decimal("increment", increment)),
            {"contrast.quantity": along})


def _qualifiers(profile, entries) -> dict[str, Qualifier]:
    qualifiers: dict[str, Qualifier] = {}
    for entry in entries or ():
        dimension, sep, rest = entry.partition("=")
        quantifier, colon, term = rest.partition(":")
        if not sep or not dimension or not colon or not quantifier or not term:
            _refuse(f"applicability {entry!r} is not dimension=quantifier:term")
        declared = profile.dimensions.get(dimension)
        if declared is None:
            _refuse(f"applicability {entry!r}: no dimension {dimension!r} in this profile; "
                    f"it declares {sorted(profile.dimensions)}")
        qualifiers[dimension] = Qualifier(quantifier, Referent(declared.restriction_sort, term))
    return qualifiers


def _require_held(profile, receipt, referents: dict[str, Referent]) -> None:
    """The kernel refuses only not-member; §5.2 requires a dataset-bound
    vocabulary to be held, so an unresolved outcome under one refuses here."""
    bound = dataset_bound_sorts(profile)
    for label, referent in referents.items():
        outcome = receipt.outcomes[label]
        if referent.sort in bound and outcome in UNRESOLVED:
            _refuse(f"{referent.term} ({label}): sort {referent.sort} binds vocabulary "
                    f"dataset:{bound[referent.sort].dataset_identity}, which is not held here ({outcome.value}); "
                    "hold it with `dataset` before freezing a spec under it")


def handle(ctx, writer, *, target, dataset, contrast, slot, measure, scale, reference, identification,
           method, assumptions, falsification, interpretation_rule, equivalence_rule,
           baseline=None, comparison=None, quantity=None, increment=None, conditioning=None,
           applicability=None, parameters=None, supersedes=None) -> Report:
    profile = ctx.config.profile
    _, view = ctx.single_view()
    for ref in (target, dataset):
        if not view.holds(ref):
            _refuse(f"{ref!r} is not in the corpus")
    try:
        address = dataset_address(stored.dataset_declaration(view.get(dataset)))
    except MalformedRecord as caught:
        _refuse(f"{dataset}: {caught}")
    if address is None:
        _refuse(f"{dataset} declares no content identity")
    superseded = None
    if supersedes is not None:
        # A record ref the corpus holds, resolved before any act: a bare identity
        # or an unheld spec refuses here rather than escaping as MalformedRecord.
        try:
            superseded = stored.local_id("analysis-spec", supersedes)
        except MalformedRecord as caught:
            _refuse(f"supersedes {supersedes!r} is not an analysis-spec ref: {caught}")
        if not view.holds(supersedes):
            _refuse(f"supersedes {supersedes!r} is not in the corpus")
    held_rules = {interpretation_rule: _rule(interpretation_rule), equivalence_rule: _rule(equivalence_rule)}
    snapshot = ctx.snapshot()
    try:
        claim, _ = claim_from_stored(view.get(target), profile=profile, snapshot=snapshot)
        decl = profile.estimand(claim.operator)
        contrast_value, referents = _contrast(decl, contrast, slot, baseline, comparison, quantity, increment)
        referents["measure.quantity"] = Referent(decl.measure_sort, measure)
        referents["control.identification"] = Referent(decl.identification_sort, identification)
        conditioned = tuple(Referent(decl.conditioning_sort, term) for term in conditioning or ())
        for index, member in enumerate(conditioned):
            referents[f"control.conditioning[{index}]"] = member
        estimand, estimand_receipt = build_estimand(
            profile, claim, snapshot=snapshot, contrast=contrast_value,
            measure=Measure(quantity=referents["measure.quantity"], scale=scale),
            reference=_decimal("reference", reference),
            control=Control(identification=referents["control.identification"], conditioning=conditioned))
        qualifiers = _qualifiers(profile, applicability)
        scoped, applicability_receipt = build_applicability(profile, claim, qualifiers, snapshot=snapshot)
    except AUTHORING_ERRORS as caught:
        _refuse(f"estimand refused: {caught}")
    _require_held(profile, estimand_receipt,
                  {ReferentPosition.estimand(part).label(): r for part, r in referents.items()})
    _require_held(profile, applicability_receipt,
                  {ReferentPosition.restriction(d).label(): q.restriction for d, q in qualifiers.items()})
    draft = SpecDraft(target=target, estimand=estimand, method=method, assumptions=assumptions,
                      falsification=falsification,
                      input_roles=(SpecInput(role="observes", dataset=address),),
                      applicability=scoped, interpretation_rule=interpretation_rule,
                      equivalence_rule=equivalence_rule, parameters=parse_parameters(parameters),
                      nondeterminism=Deterministic())
    try:
        spec = freeze(draft, held_rules=held_rules, supersedes=superseded)
    except (MalformedSpec, UnfreezableSpec) as caught:
        _refuse(f"freeze refused: {caught}")
    node = writer.add(stored.analysis_spec_node(spec))
    return (record_block(node),)
