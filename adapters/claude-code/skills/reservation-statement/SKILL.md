---
name: "reservation-statement"
description: "Check a reservation chain's checked-in statement against its current records and the exposure they have not considered."
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

Check that the two files a program's repository holds for one reservation chain are the statement of the chain's current head, byte for byte, and report the visible exposure events the head has not considered.
The files are generated: `<chain>.json` and `<chain>.md` in `check`, or `<chain>/<slug>.json` and `.md` for a scoped chain. Never edit them. They are written only by the attended CLI's `--write <directory>` option, which this command does not offer here.
Under a selected project each unconsidered event is the program's (the project's query claims it in an addresses-only clause), another program's, or unattributed. With no project selected every event is the program's.
In a world several programs share, always pass `project` naming the program's own: an ambient selection can be another program's, under which this program's events never block. A reader checking an adopted publication selects none.
`block_on` and `all_considered` state the program's own rule; with neither, the list is a report only. Pass exactly the options the program's reservation rule names.
A missing or differing file refuses `statement-stale`, a chain with no record `chain-absent`, and a blocked gate `events-unconsidered`, naming each event. Act on the refusal's code and data, never on the report's text.
A passing check speaks only for the corpora, publication markers and project revision it prints; record them with the run.
