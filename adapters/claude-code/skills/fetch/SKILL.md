---
name: "fetch"
description: "Hold a mounted dataset's bytes from a local path or an https URL, after checking the declared digest."
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

Run `fetch` when a dataset record is mounted from another installation and this
machine does not yet hold its bytes. Give the dataset's address and a `source`:
an absolute path or an https:// URL. The bytes are held only if they match the
digest the dataset declares, and the configuration's `[fetch]` policy allows it
(`records-only` refuses). The output is the holdings observation; if it refuses,
report the refusal and change nothing.
