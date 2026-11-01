---
name: "recheck"
description: "Re-check one store location and record what the store holds there, settling an unmatched holdings intent."
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

Run `recheck` when a store location is blocked `unsettled`: a holdings write
appended its intent and then the store refused or the write was interrupted,
so no observation followed. Give the location exactly as the blocked row names
it, `store:<store id>:<relative path>`, with nothing added or trimmed. The
location must be in this configuration's `store_root`; a location in a read
store refuses and names the recovery configuration. The re-check reads the
store and writes evidence to the governed corpus: it settles only intents in
this configuration's `write_root`, and on a live world it needs the person's
authorization first. The output is what the kernel observed. `found` with a
digest or `absent` publishes an observation and clears the block; an
inconclusive read (`retrieval-failed` or `byte-locator-untested` with the
kernel's reason) publishes none and leaves the block. Report the result as
given; never assume absent. A refusal changes nothing.
