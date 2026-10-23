---
name: "provider-bind"
description: "Bind a provider's location to the world its publication claims, when the given world id matches."
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

Run `provider-bind` to record that a location speaks for a world:
`location` is the `https://` git remote, `corpus_id` a publication there,
and `world` the world id you confirm, as `provider-inspect` reported it.
The confirmation is the argument: it fetches and verifies the publication
into scratch, and binds the location only when `world` is the world its
marker claims, refusing `world-mismatch` (with the `claimed` and `given`
ids) otherwise. `world` must be another world's id, not this one's. The
output is one `[pin]` block for the `bound` sharing line: the corpus, its
marker, the artifact identity, the world, the view and the verdict. Pins
learned from a bound location are origin-confirmed, which an `accept`
policy requires. Binding needs `sharing_root` configured. A location that
does not hold the corpus or a copy that does not validate refuses
`invalid-input` naming the location, and nothing is recorded.
