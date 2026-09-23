"""Belief evaluation in one call (design §4.7, §5.5): the availability and
supplied context the evaluator does not compute itself, built from the
world, then `evaluate_over` under the shipped policy."""
from __future__ import annotations

from beliefs.belief import Availability, SuppliedContext
from beliefs.corpus import ReadView, lineage_snapshot
from beliefs.evaluation import EvaluationInputs, evaluate_over, gather
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.profile import ProfileSpec
from beliefs.resolution import ResolutionSnapshot

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


def gather_inputs(view, proposition, *, context, profile: ProfileSpec, resolution: ResolutionSnapshot) -> EvaluationInputs:
    return gather(view, proposition, context=context, profile=profile, resolution=resolution, binding=BINDING)


def evaluate(view, proposition, *, observations, context, profile, resolution):
    return evaluate_over(view, proposition, availability=availability(observations), context=context,
                         profile=profile, resolution=resolution, binding=BINDING)
