---
name: "exposure-event"
description: "Record one look at data, or one piece of prior knowledge, as an exposure event."
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

Record what someone saw or already knew, as soon as it happens: one look at data (`channel` `read`, naming its `dataset:` or `source:` subjects) or one piece of prior knowledge (`channel` `knowledge`, with no subjects).
No selected project is required. Write the JSON payload first and pass its path: `schema_version` 1, a one-line `title`, and the `facet`; `docs/commands.md` has a complete example.
Omit `recorded_by`, which the session supplies, and omit an optional field instead of giving it null or an empty value. `observer`, `observed_at` and the external `evidence` tokens are yours to state.
Every subject, proposition and `run:`, `act-report:` or `holdings-observation:` evidence token must resolve in the session's live corpora, and every term unit's sort must be one the configuration declares.
An event changes no assignment: the current `reservation-head` stays current and lists the new event as not considered.
When a refusal carries `data.existing`, the identical event is already recorded and is safe to cite when the session mounts its holder; `data.occupied` means another kind of record holds that address.
