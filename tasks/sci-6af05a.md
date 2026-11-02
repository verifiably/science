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
updated: 2026-11-02T12:06:02Z
started: 2026-11-02T10:38:24Z
depends: [ops-68729d]
tags: []
source: "tt-policy:sci"
agent: codex
origin: agent
spec: docs/specs/2026-11-02-test-execution-policy-design.md
plan: docs/plans/2026-11-02-test-execution-policy.md
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
- 2026-11-02T11:23:50Z (feat/sci-6af05a-test-policy): spec round 1 rulings & pilot verification: ran uncertified-volume pilot in .worktrees/sci-6af05a (1195 collected across 72 modules: 532 passed across 14 all-pass + 27 mixed modules, 663 skipped across 27 mixed + 31 all-skip modules, 0 failed in 5.45s on 16 workers / 5.22s on 4 workers). Accepted all 6 round-1 items from claude-code/claude-opus-5-5 in 2fb59e88ee75498baeb50b935c4ae647d7fccc44 (recorded with Why/Cost in tasks/files/sci-6af05a/spec-review-ledger.md; no deferred minors). Worktree .worktrees/sci-6af05a remains locked on unmerged branch feat/sci-6af05a-test-policy; no pushes performed; host-load --section session reports nothing left running.
- 2026-11-02T11:23:52Z (feat/sci-6af05a-test-policy): parked (waiting on user, review): Write implementation plan in docs/plans/2026-11-02-test-execution-policy.md after user approves revised docs/specs/2026-11-02-test-execution-policy-design.md (frozen at 2fb59e88ee75498baeb50b935c4ae647d7fccc44)
- 2026-11-02T11:29:51Z (feat/sci-6af05a-test-policy): resumed
- 2026-11-02T11:29:53Z (feat/sci-6af05a-test-policy): review: spec round 2 — verdict: revise; findings: 1 important; reviewer: claude-code/claude-opus-5-5
- 2026-11-02T11:30:58Z (feat/sci-6af05a-test-policy): spec round 2 rulings: accepted Important 1 from claude-code/claude-opus-5-5 in 365799fe519726eafa7e8a70e1f2ef2f796c268b (§5.3 now requires TT_FORCE=1 just test-fast on the certified host before merging any branch touching python/, and just test-full for shared fixtures, lifecycle code, or dependency changes) and restored 'policy: disabled at <RFC3339-UTC> revision <full-sha>' in §7.3.3 to match ops/bin/tt-latency:452 and autonomy-23aeff (recorded with Why/Cost in tasks/files/sci-6af05a/spec-review-ledger.md; no deferred minors). Worktree .worktrees/sci-6af05a remains locked on unmerged branch feat/sci-6af05a-test-policy; no pushes performed; host-load --section session reports nothing left running.
- 2026-11-02T11:31:00Z (feat/sci-6af05a-test-policy): parked (waiting on user, review): Write implementation plan in docs/plans/2026-11-02-test-execution-policy.md after user approves docs/specs/2026-11-02-test-execution-policy-design.md (frozen at 365799fe519726eafa7e8a70e1f2ef2f796c268b)
- 2026-11-02T11:40:36Z (feat/sci-6af05a-test-policy): resumed
- 2026-11-02T11:40:38Z (feat/sci-6af05a-test-policy): review: spec round 3 — verdict: accept; findings: minor 2; reviewer: claude-code/claude-opus-5-5
- 2026-11-02T11:44:22Z (feat/sci-6af05a-test-policy): plan drafted: committed implementation plan at e0ba174bd04bc7f2638529ecbadb9e4ca80560ce in docs/plans/2026-11-02-test-execution-policy.md (sha256 edd0e54d14f24686dde059e605416a0332322b2c32f811358df3f1b3a59d2427) implementing accepted spec 8cd98e857bd75ce0be1858c06b2b2053f9db382a across 6 tasks. Recommended execution approach: Native (executing-plans) in this session because the 6 sequential tasks share .worktrees/sci-6af05a and Tasks 5-6 carry live main integration and the Publication/Activation approval packets (alternative: Subagent-driven via subagent-driven-development). Worktree .worktrees/sci-6af05a remains locked on unmerged branch feat/sci-6af05a-test-policy; no pushes performed; host-load --section session reports nothing left running.
- 2026-11-02T11:44:24Z (feat/sci-6af05a-test-policy): parked (waiting on user, review): Execute docs/plans/2026-11-02-test-execution-policy.md (frozen at e0ba174bd04bc7f2638529ecbadb9e4ca80560ce) after user approves the plan
- 2026-11-02T11:53:38Z (feat/sci-6af05a-test-policy): resumed
- 2026-11-02T11:53:40Z (feat/sci-6af05a-test-policy): review: plan round 1 — verdict: revise; findings: 4 important, 4 minor; reviewer: claude-code/claude-opus-5-5
- 2026-11-02T11:56:40Z (feat/sci-6af05a-test-policy): attached: plan-review-ledger.md (5216 bytes): Plan review ledger for docs/plans/2026-11-02-test-execution-policy.md
- 2026-11-02T11:56:42Z (feat/sci-6af05a-test-policy): plan round 1 rulings: merged main (dc39b31, tt v10) into feat/sci-6af05a-test-policy and accepted all 8 findings (4 important, 4 minor) from claude-code/claude-opus-5-5 in d32cbf1ae6a0613c48d93d6ec900a334d34a78a0 (sha256 23ed6f1ab0c4bdbd4b32d2d212d006a181493a58fcd56e6e13ee930f2dffe86e; rulings with Why/Cost attached in tasks/files/sci-6af05a/plan-review-ledger.md; no deferred minors). Worktree .worktrees/sci-6af05a remains locked on unmerged branch feat/sci-6af05a-test-policy; no pushes performed; host-load --section session reports nothing left running.
- 2026-11-02T11:56:44Z (feat/sci-6af05a-test-policy): parked (waiting on user, review): Execute docs/plans/2026-11-02-test-execution-policy.md (frozen at d32cbf1ae6a0613c48d93d6ec900a334d34a78a0) after user approves the revised plan
- 2026-11-02T12:06:02Z (feat/sci-6af05a-test-policy): resumed
