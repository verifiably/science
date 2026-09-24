---
name: "decide"
description: "Record a decision in the current project, with its reasoning."
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

Run `decide` to record a decision in the current project: what was
decided and, in `body`, why. The reasoning is required — a decision
without it is the part a later reader cannot reconstruct. It needs a
selected project. Report the minted record.
