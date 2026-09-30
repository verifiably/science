---
name: "run"
description: "Execute the analysis for a spec once, under confinement, and mint the run record."
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

Run `run` to execute a frozen spec's analysis once under confinement: name
the spec, the dataset it observes, the code directory holding the workflow,
the entrypoint and the targets. It needs bubblewrap on this host and refuses
otherwise before touching anything. The minted run record is the output; a
refusal names the kernel's reason and nothing was written.
