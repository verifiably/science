---
name: "reuse"
description: "Copy a question or hypothesis into the current project with the same query."
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

Run `reuse` when a question or hypothesis from another project belongs
in the current one too. A question belongs to the project it was asked
in and never moves; `reuse` mints the current project's own record with
the same query, naming the source in its body. The source is untouched.
Report the minted record.
