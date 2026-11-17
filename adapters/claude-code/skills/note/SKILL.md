---
name: "note"
description: "Record a note in the current project: a name, a body, and the world records it is about."
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

Run `note` to record a dated statement in the current project. Supply a
non-empty body and any world addresses it is about. With no selected project,
it refuses `no-current-project`; ask the person to use `project-select`.
Every about address must resolve before any act. Notes cannot be revised;
a correction is a new note naming the old note in its body. Report the minted record.
