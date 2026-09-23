---
name: "run"
description: "Execute the analysis for a spec once, under confinement, and mint the run record."
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

Run `run` to execute a frozen spec's analysis once under confinement: name
the spec, the dataset it observes, the code directory holding the workflow,
the entrypoint and the targets. It needs bubblewrap on this host and refuses
otherwise before touching anything. The minted run record is the output; a
refusal names the kernel's reason and nothing was written.
