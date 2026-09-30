---
name: "projects"
description: "List every project in the world, marking the selected one."
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

Run `projects` to list every project in the world: its `coord:<project>`
address, its name, the revision that stands, and a mark on the one this
session has selected. Two projects may share a name; the address tells
them apart and is what `project-select` takes when a name is ambiguous. A
project shown as `divergent` has more than one standing revision: report
it as listed, and do not pick one.
