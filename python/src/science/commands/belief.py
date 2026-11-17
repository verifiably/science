"""belief: evaluate science.belief.v1 over one proposition, under the reader's accept policy, which the
report explains."""
from __future__ import annotations

from beliefs.belief import Belief, NoBelief

from science.acceptance import acceptance_inputs, explain
from science.closure import select_answer
from science.report import Heading, KeyVals, Report


def handle(ctx, *, proposition, key=None) -> Report:
    ctx.mount_holding(proposition)  # refuses an absent proposition or differing copies
    selected, answer = select_answer(ctx.claim_view(proposition), key)
    if isinstance(answer, Belief):
        pairs = (("kind", "Belief"), ("value", str(answer.value)),
                 ("belief_input_digest", answer.belief_input_digest),
                 ("policy_binding", f"{answer.policy_binding.rule} {answer.policy_binding.implementation}"))
    elif isinstance(answer, NoBelief):
        pairs = (("kind", "NoBelief"), ("reason", answer.reason), ("detail", answer.detail))
    else:
        pairs = (("kind", "Refused"), ("reason", answer.reason))
    if selected is not None:
        pairs = (("key", selected), *pairs)
    report = (Heading(f"Belief: {proposition}"), KeyVals("answer", pairs))
    if answer.acceptance is None:
        return report
    return (*report, KeyVals("acceptance", explain(
        answer.acceptance, acceptance_inputs(ctx),
        lambda address: tuple(m.corpus_id for m in ctx.session_mounts() if m.view.holds(address)))))
