---
name: "next"
description: "Rank the propositions this world can act on, from the current view."
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
