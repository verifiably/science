---
name: "provider-inspect"
description: "Show the world a publication at a provider's location claims, verifying it and recording nothing."
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

Run `provider-inspect` before binding a provider: `location` is the
`https://` git remote a publication was published to and `corpus_id` the
publication's corpus id. It fetches that corpus into a scratch copy,
verifies its chain against its head artifact, reads its publication
marker, and deletes the copy. The output is the `publication` block: the
`world` id the marker claims, the `marker` uid, the `artifact` identity
(the SHA-256 of the head artifact), the revision-pinned `view` it was
published from, and the `verdict`, always `validated`. The world id is the
publisher's claim, not proof of who controls that world; confirm it with
the publisher, then run `provider-bind` with it as `world`. Nothing is
recorded. A location that does not hold the corpus, cannot be reached, or
holds a copy that does not validate refuses `invalid-input` naming the
location.
