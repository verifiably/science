# Builder check: holdings recheck design (first draft, pre-f00a6ec)
Reviewer: claude-code general-purpose subagent (fresh context), read-only.

Questions, ranked:
1. Detail line for every act-report or only re-check? run/verify/publish also mint act-reports (dispatch.py:436-443 renders all). -> Resolved (author's call): re-check act-reports only; other operations unchanged.
2. Has the reviewer accepted approach 1? -> The user's spec review.
3. Who lands the cli.toml row on ops main? bin/vendored adopt copies only landed commits (adopt() ~420-445); adopt also pulls ~190 lines of other tools' rows. -> Resolved (author's call): plan step 1 adds the row in an ops worktree and merges locally into ops main, no push.
4. Inconclusive reason: stored entry keeps only reason code, not detail (recheck.py builds ByteLocatorUntested/RetrievalFailed from result.reason). -> Resolved (author's call): reason code suffices.

Contradictions found:
- dataset/fetch-only claim incomplete (run/verify/publish) -> fixed by scoping to re-check reports.
- "kernel refusals raised before any intent" not strict: RecheckRefused at close; StoreIdMismatch after intent (boundary.py:217-219, not in KERNEL_REFUSALS); dispatcher KERNEL_REFUSALS path closes refused without checking acts (dispatch.py:243-244). -> Recorded in spec as existing behaviour, unchanged.
- Act-time permit refusal unreachable via dispatcher (dispatch.py:229) -> test scoped to declaration time.
- unsettled blocks a dataset only with a digest-matching observation (adapter.py:71-75) -> assertions on the reduction's blocked list.

Confirmed true: ScopedWriter.recheck description; intents in write corpus; cross-corpus supersession admitted; record titles; KIND_ACTS act-report routes; read-only-serviceable stores readable; act-report reaches invocation_acts via LedgeredPort.execute_fulfilling.
