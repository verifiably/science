---
name: "belief"
description: "Evaluate the shipped belief policy over one proposition and render the answer."
---

You are working over one world of governed records through the `science`
commands. The current project is chosen with `project-select`. A command
that enumerates the world reads through the selected project's query, and
sees the whole world when none is selected; a command given an identity
answers for that identity whatever is selected. A question or any
coordination record needs a selected project, except a project itself; a
fact does not. Corpus writes are kernel acts that return their own records;
session writes return the selection they recorded. Report refusals verbatim,
and never retry with altered inputs, repair, or write around one. Results are
budgeted: a truncated result ends with a cursor, and continuing with that
cursor is the only way to see the rest. A command's declared inputs are its
whole interface; there is nothing to reach around.

Run `belief` to see what the shipped policy believes about one proposition
and why: `Belief` with its value, input digest and policy binding; `NoBelief`
with the reason (no eligible assessment, no directional outcome); or
`Refused` with the kernel's reason. Nothing is written.
