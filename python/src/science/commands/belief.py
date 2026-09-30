"""belief: evaluate science.belief.v1 over one proposition (§4.7)."""
from __future__ import annotations

from beliefs.belief import Belief, NoBelief

from science.report import Heading, KeyVals, Report


def handle(ctx, *, proposition) -> Report:
    ctx.mount_holding(proposition)  # refuses a proposition no mount holds, or two do
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
