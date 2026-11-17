---
name: "topic"
description: "Record a topic in the current project: a background synthesis and the world records it draws on."
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

Run `topic` to record a complete background synthesis in the current project.
Supply a non-empty body and a YAML/JSON view query with an addresses predicate
naming the records it draws on. Every address and closure anchor must resolve
before any act. With no selected project, ask the person to use `project-select`.
Never mint an empty topic or one merely to give a term a referent. Report the minted record.
