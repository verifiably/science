"""belief: evaluate science.belief.v1 over one proposition (§4.7)."""
from __future__ import annotations

from beliefs.belief import Belief, NoBelief

from science.refusal import Refusal, Refused
from science.report import Heading, KeyVals, Report


def handle(ctx, *, proposition) -> Report:
    _, view = ctx.single_view()
    if not view.holds(proposition):
        raise Refused(Refusal("invalid-input", f"proposition {proposition!r} is not in the corpus"))
    answer = ctx.evaluate(proposition)
    if isinstance(answer, Belief):
        pairs = (("kind", "Belief"), ("value", str(answer.value)),
                 ("belief_input_digest", answer.belief_input_digest),
                 ("policy_binding", f"{answer.policy_binding.rule} {answer.policy_binding.implementation}"))
    elif isinstance(answer, NoBelief):
        pairs = (("kind", "NoBelief"), ("reason", answer.reason), ("detail", answer.detail))
    else:
        pairs = (("kind", "Refused"), ("reason", answer.reason))
    return (Heading(f"Belief: {proposition}"), KeyVals("answer", pairs))
