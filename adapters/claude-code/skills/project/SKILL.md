---
name: "project"
description: "Start a project: a name and a query over the world."
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

Run `project` to start a project: a name and a query over the world
(`science.view-query.v1`, as YAML or JSON text). A project is a label over
a query, never a container — the world facts its query selects are its
content, and they belong to every other project whose query selects them
too. Minting a project needs no selected project. Report the minted
record; its address is `coord:<project>`, the identity every later
reference uses, since names may be shared.
