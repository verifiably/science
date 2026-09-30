---
name: "next"
description: "Rank the propositions this world can act on, from the current view."
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

Run `next` when the user asks what to work on. It lists propositions in a
fixed order — ready (a spec targets it and every input is held), not ready,
assessed but not admitted, admitted — with each one's statement. With a
project selected, or named with `project` for this call only, it lists the
propositions that project's query selects, evaluated over the world as it
stands now, and opens with a `selection` block: the project, whether every
corpus was present (`complete`, `absent`), and the states it read. With no
project it lists the whole world. Nothing is stored; the ranking is
recomputed every time. It names no priority function; that is a later
sub-project's.
