---
name: "adopt"
description: "Fetch, verify and admit a publication from a bound provider's location, and mount it at the next open."
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

Run `adopt` to hold another world's publication: `location` is the
`https://` git remote it was published to and `corpus_id` the publication
there. It fetches the corpus, verifies its chain against the head artifact
published beside it, and sources it: the location must be bound, with
`provider-bind`, to the world the publication's marker claims. Unbound, it
refuses `pin-unsourced` naming that world and the remedies, `provider-bind`
or `follow`; bound only to other worlds, `world-mismatch` naming them.
Either way the copy is deleted and nothing is recorded. A copy that
shares an address with a corpus this world already holds refuses
`adopt-conflict` with the shared addresses, and stays `fetched`. A clean
copy is admitted to the world and marked mounted. The output is one
`[pin]` block per sharing step this run took (`fetched`, `admitted`,
`mounted`). The mount takes effect at the next session open; reopen (and
capture an epoch) to read and cite the adopted records. A run
interrupted after admission is completed by the next `adopt` of the same
corpus; adopting a mounted corpus again refuses as already adopted.
Adopting needs `sharing_root` configured.
