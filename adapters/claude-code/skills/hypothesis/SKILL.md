---
name: "hypothesis"
description: "Ask a hypothesis in the current project: a name and a query over the world."
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

Run `hypothesis` to state a hypothesis in the current project. It needs a
selected project: with none it refuses `no-current-project`, and the
answer to "which project does this belong to" is the one you are in —
another project that wants it copies it with `reuse`. The query names
the world facts that bear on the hypothesis. Report the minted record.
