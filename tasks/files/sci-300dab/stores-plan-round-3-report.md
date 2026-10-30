# Plan review round 3 — controller self-review

Reviewer: codex/gpt-6-astra, verified in this turn by `timeout 2 relay model --harness codex --pretty`.
Revision: science 0ddb1ad1df3c1d4c1a4ff4b43d08065eeeb0671a, docs/plans/2026-10-30-readable-stores.md.
Plan SHA-256: 5f35ec669504e4772780d8b61791c466b18bacc5cf51f0b6173419e65a30ba1d.
Spec: unchanged 6d83468c5aa242ffd2ab8a10a3476dcfefa8c4ff; SHA-256 f0e64120d6bb9bfaa35d6cd705cb9d2ebfef5d3c43af61ed151680ac47fac31c.

Verdict: accept; findings: none. This is the writing-plans controller checklist, not an independent review or authorization to implement.

- Spec coverage remains in the three sequential tasks: admission/configuration; resolution/snapshot/consumers; restored-store writes/runbook/compatibility inventory. The spec's incomplete restore case is represented by a real replica before its restore grant, asserting science refusal and unchanged files. Kernel failure-injection and retry semantics are excluded as requested.
- Important 1: the plan extracts the existing Dispatcher._kernel_refusal into one shared helper, retains its existing shapes and the dispatcher's closed catch list, and adds root context only when requested. Checked all five production call sites and existing dispatch/write/session regression files. Internal exception imports are explicitly temporary and linked to newly filed beliefs-1dfd8c; no unsupported public-export claim remains.
- Minor 2: child starts record scoped overrides of open sci-0bea23; the 142-second test-fast observation and normal test obligations remain explicit.
- Minor 3: restore-grant failure injection and retry assertions removed; science's refusal/no-mutation boundary remains covered.
- Minor 4: blocked fixture now patches reduced_heads with a named inherited head and explicit location/heads/reasons row, preserving a healthy active row. Checked the actual dataset_observations adapter keys and matching logic; it and reduced_observations run unpatched through held_path.
- Minor 5: discovery is limited to named roots/configs/referenced worktrees and 20 minutes. Unread or out-of-scope references remain recorded gaps requiring controller disposition before integration, not implied coverage.
- Provenance correction: the controller approved the design, not the user. Earlier task-note wording was corrected by an append-only note. Inline execution plus a fresh final reviewer remains the agreed method.
- Step/type/proportion checks: shared helper has one exact signature; downstream mapping interfaces and task order are unchanged. New tests target preserved normalization semantics and root context. The plan remains shorter than the spec; added text settles review decisions without adding product scope.

Verification: just check and git diff --check exited 0; documentation commit hooks passed. No runtime tests, implementation, live mutation, or fresh live-store inventory were performed. The baseline remains deferred to execution Setup. No findings rejected or deferred; the internal-import limitation is explicitly tracked by beliefs-1dfd8c.
