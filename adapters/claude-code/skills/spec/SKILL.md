---
name: "spec"
description: "Freeze an analysis spec against the kernel's reference rules and mint its record."
---

You are working over one world of governed records through the `science`
commands. The world is read through the selected project's query when one is
selected and whole when none is; no project can be selected yet, so every
command reads the whole world. A question or task needs a selected project;
a fact does not. Every write is a kernel act that returns its own record or a
refusal — report refusals verbatim, and never retry with altered inputs,
repair, or write around one. Results are budgeted: a truncated result ends
with a cursor, and continuing with that cursor is the only way to see the
rest. A command's declared inputs are its whole interface; there is nothing
to reach around.

Run `spec` to freeze the analysis that will assess a proposition. Give the
target proposition and the dataset it observes; the estimand as its parts —
a `levels` contrast (slot, baseline and comparison levels) or a
`continuous` one (slot, quantity and increment), the measure and its scale,
the reference value on that scale, the identification strategy, and any
conditioning terms, each term kind-prefixed as the contract's vocabularies
spell it; applicability as dimension=quantifier:term entries, if the
analysis is narrower than the claim; the method, assumptions and
falsification condition in the user's words; and the interpretation and
equivalence rule identities the kernel ships. Parameters are name=value
pairs. Nothing is defaulted: ask the user rather than guess a reference or
a scale. The frozen spec's identity is what `run` executes and `verify`
compares under; it cannot be edited, only superseded.
