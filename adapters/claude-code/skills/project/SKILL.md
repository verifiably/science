---
name: "project"
description: "Start a project: a name and a query over the world."
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

Run `project` to start a project: a name and a query over the world
(`science.view-query.v1`, as YAML or JSON text). A project is a label over
a query, never a container — the world facts its query selects are its
content, and they belong to every other project whose query selects them
too. Minting a project needs no selected project. Report the minted
record; its address is `coord:<project>`, the identity every later
reference uses, since names may be shared.
