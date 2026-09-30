---
name: "revise"
description: "Revise a project, question, hypothesis, task or decision."
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

Run `revise` to change a project, question, hypothesis, task or decision
by address. Fields not given carry over from the current revision; a
field the record's kind lacks refuses. Closing a task is `status` `done`
or `dropped`; `depends` replaces a task's dependencies and `clear_depends`
empties them. An address whose record has diverged into several standing
revisions refuses and names them; `repair` reconciles them into one, and
then every field must be given, since there is no single revision to
carry over from. Report the minted revision.
