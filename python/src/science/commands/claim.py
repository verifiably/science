"""claim: type a proposition under the profile and mint it."""
from __future__ import annotations

import re

from beliefs import stored
from beliefs.claim import Member, Referent, build_claim
from beliefs.decode import WireClaim, decode_claim
from beliefs.errors import ScienceError, UnboundReferent
from beliefs.projection import project_claim

from science.refusal import Refusal, Refused
from science.report import Report, record_block
from science.vocabulary import require_performed
from science.authoring_records import session_records


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
    row = plan.row_for(predicate, subject_kind, object_kind)
    if layer not in plan.layers:
        _refuse(f"layer {layer!r} is not in the plan")
    if polarity not in plan.polarities:
        _refuse(f"polarity {polarity!r} is not in the plan")
    layer_term = plan.layers[layer]
    polarity_term = plan.polarities[polarity]  # None for a sign-inapt operator's not_applicable
    try:
        subject_ref = Referent(sort=plan.sort_for(subject_kind), term=subject)
        object_ref = Referent(sort=plan.sort_for(object_kind), term=object)
        subject_role, object_role = row.roles["subject"], row.roles["object"]
        roles = ({subject_role: (Member(subject_ref), Member(object_ref))} if subject_role == object_role
                 else {subject_role: subject_ref, object_role: object_ref})
        claim = build_claim(ctx.config.profile, operator=row.operator, roles=roles,
                            layer=layer_term, polarity=polarity_term)
        projection = project_claim(claim)
        with session_records(ctx) as records:
            snapshot = ctx.authoring_snapshot(records=records)
            _, receipt = decode_claim(WireClaim(**projection), profile=ctx.config.profile, snapshot=snapshot)
            referents = {}
            for name, value in claim.roles.items():
                if isinstance(value, Referent):
                    referents[f"role:{name}"] = value
                else:
                    referents.update({f"role:{name}[{i}]": member.referent for i, member in enumerate(value)})
            require_performed(ctx.config.profile, receipt, referents)
    except UnboundReferent as caught:
        _refuse(f"membership refused (not-member): {caught}")
    except ScienceError as caught:
        raise Refused(Refusal("invalid-input", f"claim refused: {caught}",
                              {"kind": type(caught).__name__})) from caught
    node = writer.add(stored.proposition_node(
        slug or _slug(subject, predicate, object), title=f"{subject} {predicate} {object}",
        claim=projection, display_statement=f"{subject} {predicate} {object}"))
    return (record_block(node),)
