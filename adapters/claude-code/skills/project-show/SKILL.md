---
name: "project-show"
description: "Show one project: its query and its questions, hypotheses, tasks and decisions."
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

Run `project-show` to see one project: the selected one, or the one named
with `project` for this call only, which leaves the session's selection
where it was. It shows the project's address, standing revision, name and
canonical query, then its records — open tasks first, then questions,
hypotheses, decisions, and closed tasks — each with its address. With
nothing selected and no project named it refuses; select one with
`project-select` or name one.
