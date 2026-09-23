---
name: "belief"
description: "Evaluate the shipped belief policy over one proposition and render the answer."
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

Run `belief` to see what the shipped policy believes about one proposition
and why: `Belief` with its value, input digest and policy binding; `NoBelief`
with the reason (no eligible assessment, no directional outcome); or
`Refused` with the kernel's reason. Nothing is written.
