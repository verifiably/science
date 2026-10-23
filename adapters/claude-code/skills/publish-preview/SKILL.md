---
name: "publish-preview"
description: "Show what publishing a project's view would freeze, without writing anything."
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

Run `publish-preview` before `publish`, with the same `target` and `to`, to
see what the kernel would freeze: the selection by kind and every selected
record, whether its closure is complete, which records carry another
world's attribution, and which datasets' bytes the destination will not
carry. It refuses exactly where `publish` would refuse before writing,
naming the kernel's reason (for `closure-incomplete`, the missing records).
Nothing is written.
