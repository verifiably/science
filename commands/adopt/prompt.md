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
