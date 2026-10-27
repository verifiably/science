What this change does: sci-9a7ce2 passes the existing Own classification to preview and new publication attempts. Resume keeps the frozen attempt without recomputing ownership. The frozen branch is ready to merge; the controller owns integration.

Reviewer: **codex/gpt-6.1-sol**, verified by `timeout 2 relay model --harness codex --pretty`.

Reviewed science `210a783..53c0764f8f244160993bb04c269c624a88fd003c` against beliefs spec `deb8d99`, especially section 6.

**Findings: Critical 0; Important 0; Minor 0.**

- `.worktrees/9a7ce2-own-publication/python/src/science/commands/publish.py` forwards `acceptance_inputs(ctx).own_roots` only for new attempts. The resume branch returns before classification.
- `.worktrees/9a7ce2-own-publication/python/src/science/commands/publish_preview.py` uses the same classifier and preserves its errors without fallback.
- The connected classifier and kernel paths retain duplicate-carrier checks, captured-marker protection, admission checks, and frozen retry data. No new configuration, registry behavior, or production write path was introduced.
- `.worktrees/9a7ce2-own-publication/python/tests/test_publish_ownership.py` covers real restored replicas under v2/v3, preview/publication parity, hand-listed registry exclusion, retained publication origins, duplicate carriers, missing/duplicate write mounts, and unreadable unselected mounts. The modified resume test fails immediately if classification reads mounts.
- README, current-facing design amendment, command prompts, and generated adapters describe the new behavior consistently. Scope fits the existing single-installation CLI/service model; no material scaling regression emerged.

Verification evidence supplied: hydrated baseline **886 passed**; focused publication tests **21 passed**; initial fast check **897 passed**, with only stale generated adapters failing. After regeneration, the adapter test and subsequent fast selection each passed **1 test**. `just check`, `git diff --check`, and the commit hook passed. These results collectively cover the reported failure, although the final fast run selected only that prior failure.

Declined to judge: replacing the classifier’s existing `ValueError` with a friendlier refusal; preserving that behavior is an explicit requirement.

Declined to judge: authenticated authorship and the live milestone outcome. Ownership remains an explicit publisher claim under the accepted design; sci-775e90 owns the live rerun.

**Verdict: Accept. Ready to merge.** No corrective round or follow-up finding is needed. This review made no changes, pushed nothing, and left no processes running; the reviewed branch remains for the controller to integrate.

Not checked: suites were not rerun, as instructed; run results above rely on supplied evidence. Live-world success remains unverified until sci-775e90 runs.
