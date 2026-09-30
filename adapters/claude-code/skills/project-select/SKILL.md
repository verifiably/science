---
name: "project-select"
description: "Select the current project for this session, or clear it."
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

Run `project-select` to choose the project this session works in: give
`target` a project's name, or its `coord:<project>` address when two
projects share a name. The selection is the address, so a later rename
leaves it standing. It scopes what `next` and `project-show` enumerate, and
it is the project a new question, hypothesis, task or decision lands under.
`clear` unselects, after which enumerations read the whole world. Report
the selection block as returned; on `ambiguous-project`, show the
candidates and ask which address was meant.
