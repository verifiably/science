---
name: "projects"
description: "List every project in the world, marking the selected one."
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

Run `projects` to list every project in the world: its `coord:<project>`
address, its name, the revision that stands, and a mark on the one this
session has selected. Two projects may share a name; the address tells
them apart and is what `project-select` takes when a name is ambiguous. A
project shown as `divergent` has more than one standing revision: report
it as listed, and do not pick one.
