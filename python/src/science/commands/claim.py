"""claim: type a proposition under the profile and mint it (belief-path §4.1)."""
from __future__ import annotations

import re

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.decode import WireClaim, decode_claim
from beliefs.errors import ClaimError, DecodeError, UnboundReferent
from beliefs.projection import project_claim
from beliefs.resolution import TermOutcome

from science.refusal import Refusal, Refused
from science.report import Report, record_block
from science.vocabulary import dataset_bound_sorts


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def _kind(term: str) -> str:
    kind, colon, tail = term.partition(":")
    if not colon or not kind or not tail:
        _refuse(f"term {term!r} carries no `<kind>:` prefix")
    return kind


def _slug(subject: str, predicate: str, object_: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", f"{subject} {predicate} {object_}".lower()).strip("-")


def handle(ctx, writer, *, subject, predicate, object, layer, polarity, slug=None) -> Report:
    plans = ctx.config.plans
    if not plans:
        _refuse("the config names no contract document with a plan; claim needs one")
    (plan,) = plans[:1]
    subject_kind, object_kind = _kind(subject), _kind(object)
    operator = plan.operator_for(predicate, subject_kind, object_kind)
    if layer not in plan.layers:
        _refuse(f"layer {layer!r} is not in the plan")
    if polarity not in plan.polarities:
        _refuse(f"polarity {polarity!r} is not in the plan")
    layer_term = plan.layers[layer]
    polarity_term = plan.polarities[polarity]  # None for a sign-inapt operator's not_applicable
    try:
        claim = build_claim(ctx.config.profile, operator=operator,
                            args=(Referent(sort=plan.sort_for(subject_kind), term=subject),
                                  Referent(sort=plan.sort_for(object_kind), term=object)),
                            layer=layer_term, polarity=polarity_term)
    except ClaimError as caught:
        _refuse(f"build_claim refused: {caught}")
    projection = project_claim(claim)
    snapshot = ctx.snapshot()
    try:
        _, receipt = decode_claim(WireClaim(**projection), profile=ctx.config.profile, snapshot=snapshot)
    except UnboundReferent as caught:  # the one resolution outcome that refuses
        _refuse(f"membership refused (not-member): {caught}")
    except (ClaimError, DecodeError) as caught:
        _refuse(f"claim refused at decode: {caught}")
    bound = dataset_bound_sorts(ctx.config.profile)
    for label, outcome in receipt.outcomes.items():
        # Labels are `argument:<slot>` or `restriction:<dimension>`; only
        # argument slots carry a sort from the plan.
        role, _, where = label.partition(":")
        sort = claim.args[int(where)].sort if role == "argument" else None
        if sort in bound and outcome in (TermOutcome.NOT_CONSULTED, TermOutcome.NOT_AVAILABLE):
            _refuse(f"sort {sort} binds vocabulary dataset:{bound[sort].dataset_identity}, which is not "
                    "held here; hold it with `dataset` before typing a claim under it")
    node = writer.add(stored.proposition_node(
        slug or _slug(subject, predicate, object), title=f"{subject} {predicate} {object}",
        claim=projection, display_statement=f"{subject} {predicate} {object}"))
    return (record_block(node),)
