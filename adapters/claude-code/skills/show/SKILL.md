---
name: "show"
description: "Show one pin: its state, source, kernel status, acceptance and verification picture."
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

Run `show` to see why you hold an adopted publication and what it is worth
to you: `corpus_id` names its pin in the sharing registry. The `pin` block
gives its state (`fetched`, `admitted`, `mounted`, `retired`), the world
its marker claims, the marker, the artifact, the view it was published
from, and whether it is kept. The `source` block says where the pin came
from and its `confirmation`: `origin-confirmed` when its source is a
provider location bound to that world, `recommended` when a followed
catalog names it, `unsourced` when no source stands. `fetch` is the fetch
record; `kernel` is this world's registry status (`known`, `live`,
`present`). `acceptance` says whether your accept policy accepts the world
and whether the corpus's records count as evidence; `evidence` lists each
assessment the corpus holds, whether it counts, and the verifications of
it across the session's corpora with their worlds and how many count under
the policy. Independence is not shown. When the kernel admitted the corpus
and the pin is not yet `mounted`, a finding says so: run `adopt` again to
reconcile. An unknown pin refuses `invalid-input`. Nothing is written.

For an authorized established publication group, `supersession` names its
world, unpinned view and destination, then its current corpus and marker.
It reports divergent tips or an unresolved chain with each missing corpus
and marker to adopt. `this pin` says `tip`, `superseded by <corpus>`, or
`sibling`; a mounted chain at another destination of the same world and
view is reported as `unlinked chain beside <corpus>`. Records the two chains
attribute differently cannot be published while both chains are mounted.
The established group and unresolved current are folded from sharing
ledger history, so a lagging pin file does not change that answer. Pins
with no authorized established group have no supersession block.

For a superseded live pin in a resolved group, `retention` lists every
reason it is kept: `configuration`, `chain (for <corpus>)`,
`attribution (named by <corpus>)`, and `dependency (<addresses>)`.
With no reason it says `pending: no door`: the kernel retirement door has
not landed. An unresolved group reports the missing links without claiming
retirement is pending. A kernel-retired pin says `retired: yes`.
The `keep` row reads the current configuration; this read-only command
neither reconciles the registry nor retires a corpus.
