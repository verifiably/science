---
id: sci-6af05a
title: Adopt shared broad-test policy and remote verification
status: doing
priority: 1
size: m
complexity: mid
process: planned
owner: feat/sci-6af05a-test-policy
created: 2026-10-29T13:46:08Z
updated: 2026-11-02T11:23:48Z
started: 2026-11-02T10:38:24Z
depends: [ops-68729d]
tags: []
source: "tt-policy:sci"
agent: codex
origin: agent
spec: docs/specs/2026-11-02-test-execution-policy-design.md
---

Adopt the approved shared test execution policy for this personal project after the ops pilot. Owner: the next sci implementer; Keith approves external activation. State: pending preparation, not offloaded. Shared authority: ops-8bfa85 (read its approved spec and plan with tasks doc); pilot prerequisite ops-68729d.

Observed 2026-10-29: code checkout is its own Git top level; records kind in-tree; profile personal. Current policy file: absent (enabled). Wrapper: {"tools/tt": "# tt version 7"}. Commands: test-one, test-fast, test, check, hook-pre-commit, hook-pre-push. Read [ref:front-door] for actual commands and setup. Workflows: None found..

Current command/ref declarations:
```
fast_cmd := "cd python && uv run pytest --testmon " + xdist
test_cmd := "cd python && uv run pytest " + xdist
one_cmd := "cd python && uv run pytest"
ci_suite_refs := ""
ci_remote := "origin"
```

Prepare a reviewed project-specific design/plan and isolated worktree. Adopt the published wrapper only after ops and obs readers are live. Keep test-one/focused implementation checks and mandatory hygiene on; split broad lint/type/test work into explicit targets. Preserve current selectors and argument forwarding. Add the forced test-full route. Verify branch/ref coverage against workflow triggers and use explicit TT_FORCE=1 for the full remote suite, including nested recipes. One suite per push, latest-ref cancellation, no duplicate internal-PR run. Keep local policy enabled until an approved hosted invocation finishes with a nonzero test count and accepted coverage.

Inventory capability omissions and private sibling checkouts from actual workflow/setup; none are presumed equivalent to local verification.

Prepare the activation packet with current private-repository allowance and enforced no-paid-overage setting, setup, exact refs, executed tests, excluded modules and skipped-test/module counts. Publishing workflows, live global instruction/hook delivery and account changes require explicit approval. Existing work/external/shared Git roots are not independent opt-ins. Reuse host/profile proof only for identical setup paths. Detached records remain separate from code policy lookup.

After approved activation, commit .tt.toml with real broad target names, verify focused execution/recorded skip/forced failure/covered remote push, and retire each disabled timing obligation explicitly without claiming performance verification. Record the actual activation revision/time here. On hook-split integration and rollback write exactly: policy: enabled at <RFC3339-UTC> revision <full-sha>. This record's source tt-policy:sci is the latency floor lookup key. Keep remaining diagnosis and unrelated obligations. Report status to ops-39bff6; never label pending work as offloaded. The first actual activation files the 30-day regret review under ops; no scheduler and no invented date.

## References

- front-door (input, required, kind=configuration): justfile

## Notes

- 2026-10-29T13:46:08Z (add): created
  provenance: {"harness_session":"codex:01a1874f-c2d8-7320-ae81-7114e37e343f","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
- 2026-11-02T10:38:24Z (main): started
- 2026-11-02T10:40:30Z (feat/sci-6af05a-test-policy): resumed
- 2026-11-02T10:51:25Z (feat/sci-6af05a-test-policy): origin: filed by codex:01a1874f-c2d8-7320-ae81-7114e37e343f (2026-10-29T13:46:08Z, L1682/L1695) as the science adoption child of ops-8bfa85 (authority docs/specs/2026-10-29-test-execution-policy-design.md in ops, dependency ops-68729d resolved). User intent in L15/L108/L294/L538/L2555/L2583/L2697 of that session established shared tt broad-test policy, local hook split, once-per-branch-push CI offload with TT_FORCE=1, dropping the exact-balance billing prerequisite for public GitHub repositories, and the 30-day shared evaluation ops-56aab7. No open intent questions remain for user clarification before drafting the spec.
- 2026-11-02T10:51:27Z (feat/sci-6af05a-test-policy): worktree: created and locked .worktrees/sci-6af05a on branch feat/sci-6af05a-test-policy from 06dd4a7; hydrated via root guide setup (git config core.hooksPath .githooks) and python/uv.lock (uv sync --frozen into .worktrees/sci-6af05a/python/.venv). Baseline suite deferred to plan execution Setup under the planned-work worktree rule.
- 2026-11-02T11:00:29Z (feat/sci-6af05a-test-policy): attached: spec-round-1-builder-report.md (274 bytes): Read-only builder check report on frozen spec 7608d2c9af3cdcaa61b1f696fc4e6ceb540035bd
- 2026-11-02T11:00:31Z (feat/sci-6af05a-test-policy): attached: spec-review-ledger.md (275 bytes): Spec review ledger for docs/specs/2026-11-02-test-execution-policy-design.md
- 2026-11-02T11:00:33Z (feat/sci-6af05a-test-policy): review: spec round 1 — verdict: approved; findings: none; reviewer: antigravity/inherit
- 2026-11-02T11:00:35Z (feat/sci-6af05a-test-policy): retained-items & disclosures: worktree .worktrees/sci-6af05a locked on branch feat/sci-6af05a-test-policy (unmerged; integrates to main after plan execution and verification); gitignored python/.venv is regenerable via uv sync --frozen; no pushes performed; no host pointers repointed; host-load --section session reports nothing left running. Spec design calls and rejected alternatives (synthetic check-code target, monolithic hook-pre-push-fast wrapper, host-budget in hosted CI) are recorded in docs/specs/2026-11-02-test-execution-policy-design.md §3.
- 2026-11-02T11:00:37Z (feat/sci-6af05a-test-policy): parked (waiting on user, review): Write implementation plan in docs/plans/2026-11-02-test-execution-policy.md after user approves docs/specs/2026-11-02-test-execution-policy-design.md (frozen at 7608d2c9af3cdcaa61b1f696fc4e6ceb540035bd)
- 2026-11-02T11:14:30Z (feat/sci-6af05a-test-policy): resumed
- 2026-11-02T11:14:32Z (feat/sci-6af05a-test-policy): review: spec round 1 — verdict: revise; findings: 2 important, 3 minor; reviewer: claude-code/claude-opus-5-5
- 2026-11-02T11:23:44Z (feat/sci-6af05a-test-policy): attached: spec-round-2-builder-report.md (274 bytes): Read-only builder check report on revised frozen spec 2fb59e88ee75498baeb50b935c4ae647d7fccc44
- 2026-11-02T11:23:48Z (feat/sci-6af05a-test-policy): review: spec round 2 — verdict: approved; findings: none; reviewer: antigravity/inherit
