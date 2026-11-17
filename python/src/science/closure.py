"""Belief evaluation in one call: the availability and
supplied context the evaluator does not compute itself, built from the
world, then the keyed claim view under the shipped policy and the reader's accept
policy."""
from __future__ import annotations

from beliefs.belief import AcceptancePolicy, Availability, Belief, NoBelief, SuppliedContext
from beliefs.belief import Refused as KernelRefused
from beliefs.corpus import ReadView, lineage_snapshot
from beliefs.evaluation import ClaimView, EvaluationInputs, claim_view as kernel_claim_view, gather
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.profile import ProfileSpec
from beliefs.resolution import ResolutionSnapshot

from science.refusal import Refusal, Refused

# What stands for an epoch when none is published. Two fields, two literals,
# as the kernel's reproduction driver spells them: the evaluator's producer
# snapshot identity, and a verification record's epoch. Admission compares
# neither with the other.
NO_EPOCH_SNAPSHOT = "no-epoch-published"
NO_EPOCH_VERIFICATION = "none-published"

BINDING = PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity)


def availability(observations) -> Availability:
    return Availability(observations=observations, implementations={BELIEF_V1.identity: BELIEF_V1},
                        fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES})


def supplied_context(view: ReadView, *, corpus_id: str, pins, epoch_identity: str,
                     observations, node_corpus) -> SuppliedContext:
    return SuppliedContext(
        snapshot=lineage_snapshot(view, sorted(observations)),
        producer_snapshot_identity=epoch_identity,
        node_corpus=node_corpus,
        pins={corpus_id: pins},
    )


def gather_inputs(view, proposition, *, key: str, observations, context, profile: ProfileSpec,
                  resolution: ResolutionSnapshot, acceptance: AcceptancePolicy | None = None) -> EvaluationInputs:
    return gather(view, proposition, key=key, observations=observations, context=context, profile=profile,
                  resolution=resolution, binding=BINDING, acceptance=acceptance)


def claim_view(view, proposition, *, observations, context, profile, resolution,
               acceptance: AcceptancePolicy | None = None) -> ClaimView:
    return kernel_claim_view(view, proposition, availability=availability(observations), context=context,
                             profile=profile, resolution=resolution, binding=BINDING, acceptance=acceptance)


def select_answer(view: ClaimView, key: str | None = None) -> tuple[str | None, Belief | NoBelief | KernelRefused]:
    keys = sorted(view.beliefs)
    if key is not None:
        if key not in view.beliefs:
            raise Refused(Refusal("invalid-input", f"{key!r} is not an assessed target key for {view.proposition}",
                                  {"key": key, "available_keys": keys}))
        return key, view.beliefs[key]
    if len(keys) > 1:
        raise Refused(Refusal("multiple-assessed-propositions", f"{view.proposition} has multiple assessed targets",
            {"available_keys": keys, "remedy": f"science belief --proposition {view.proposition} --key <key>"}))
    if keys:
        return keys[0], view.beliefs[keys[0]]
    if view.claim_answer is None:
        raise RuntimeError("an empty kernel claim view has no claim-level answer")
    return None, view.claim_answer


def evaluate(view, proposition, *, key=None, **kwargs):
    return select_answer(claim_view(view, proposition, **kwargs), key)[1]
