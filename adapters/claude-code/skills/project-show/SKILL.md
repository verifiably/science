---
name: "project-show"
description: "Show one project: its query and its questions, hypotheses, tasks and decisions."
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

Run `project-show` to see one project: the selected one, or the one named
with `project` for this call only, which leaves the session's selection
where it was. It shows the project's address, standing revision, name and
canonical query, then its records — open tasks first, then questions,
hypotheses, decisions, and closed tasks — each with its address. With
nothing selected and no project named it refuses; select one with
`project-select` or name one.
