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

Run `adopt` to hold another world's publication: `location` is its `https://`
git remote and `corpus_id` its publication id. The location must be bound with
`provider-bind` to the world its marker claims. An unbound location refuses
`pin-unsourced`; a binding only to other worlds refuses `world-mismatch`.
Those refusals discard the copy and write nothing.

The admission checklist permits equal copies. Differing content, conflicting
deprecated identifiers, or a uid at a different address refuse `adopt-conflict`,
naming the rule, addresses and live corpus; the candidate stays `fetched`.
A required predecessor's retention reasons explain why it cannot be replaced.
Sibling tips refuse `divergent-publication`; a chain needing a retired
intermediate refuses `adopt-conflict` with rule `chain-retired`. Neither mounts
the candidate. A missing link leaves a publication unresolved until adopted.

After admission, every resolved chain is re-evaluated. `retention <corpus>`
blocks explain configuration, chain, attribution or dependency requirements;
an unknown `keep` entry is a Finding. Unrequired predecessors currently report
`retirement pending` until the kernel retirement door lands. Before that step,
a changed configuration file refuses `config-stale`: the adoption stands;
restart the service and rerun `adopt` with the intended `keep` list loaded.

Output begins with every ledger sharing step's canonical `[pin]` block, followed
by informational blocks. Continuation and retry retain the historical explanation
in a report sidecar; losing it loses commentary and invalidates its cursors, while
ledger-backed effects remain recoverable. `show` explains current state.
The mount takes effect at the next session open; reopen and run `science epoch`
to read and cite it. Every `adopt` first reconciles completed admissions, then
re-evaluates retention, including when its target is already mounted. An already
mounted target refuses as already adopted only when the invocation wrote nothing.
Adopting needs `sharing_root` configured.
