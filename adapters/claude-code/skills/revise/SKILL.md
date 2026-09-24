---
name: "revise"
description: "Revise a project, question, hypothesis, task or decision."
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

Run `revise` to change a project, question, hypothesis, task or decision
by address. Fields not given carry over from the current revision; a
field the record's kind lacks refuses. Closing a task is `status` `done`
or `dropped`; `depends` replaces a task's dependencies and `clear_depends`
empties them. An address whose record has diverged into several standing
revisions refuses and names them; `repair` reconciles them into one, and
then every field must be given, since there is no single revision to
carry over from. Report the minted revision.
