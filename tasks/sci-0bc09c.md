---
id: sci-0bc09c
title: Fix selected next duplicate-corpus refusal regression blocking push
status: done
priority: 2
size: xs
complexity: low
process: direct
owner: fix/duplicate-refusal
created: 2026-10-28T20:03:42Z
updated: 2026-10-28T20:18:23Z
started: 2026-10-28T20:03:53Z
completed: 2026-10-28T20:17:53Z
closed: 2026-10-28T20:17:53Z
depends: []
tags: []
agent: codex
origin: user
---

Reproduce the reported test_two_corpora selected-next failure, trace the kernel refusal contract, and make the smallest correction that preserves duplicate rejection. Verify through the documented test front door.

## Notes

- 2026-10-28T20:03:42Z (add): created
  provenance: {"harness_session":"codex:01a1841b-698b-79f0-b115-6c26f9b6acb0","harness_session_source":"CODEX_THREAD_ID","origin":"user"}
- 2026-10-28T20:03:53Z (main): started
  provenance: {"harness_session":"codex:01a1841b-698b-79f0-b115-6c26f9b6acb0","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-28T20:04:08Z (fix/duplicate-refusal): resumed
  provenance: {"harness_session":"codex:01a1841b-698b-79f0-b115-6c26f9b6acb0","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-28T20:05:23Z (fix/duplicate-refusal): Root cause: beliefs 759976f admits identical multi-holder records. The selected-next test duplicates identical bytes and queries proposition:claimed, absent from build_two_corpus_world, so it now reaches SelectionRefused/address-unknown. Scope is test fixtures and assertions only: preserve differing-content conflict coverage and add identical-copy coverage for an existing selected record. Production passthrough is correct. Focused reproduction: 1 failed in 2.80s.
- 2026-10-28T20:08:57Z (fix/duplicate-refusal): Baseline just test (hydrated isolated worktree): 898 tests, 897 passed and the reported selected-next test failed in 240.47s. Corrected only test setup and assertions to the kernel content-identity contract; no production changes or broader holder-policy adoption.
- 2026-10-28T20:11:13Z (fix/duplicate-refusal): review: impl round 1 — verdict: accept; findings: none; reviewer: codex/gpt-6.1-sol
- 2026-10-28T20:11:16Z (fix/duplicate-refusal): Ruling: Accept the reviewer scope exclusion for selecting/citing the duplicated address and broader holder-set acceptance; keep that work in sci-73c80e. Why: this change repairs a stale refusal fixture and claims only unrelated selected reads, while the broader adoption already has its own recorded intent. Cost: Science still refuses direct duplicate-holder reads until that task lands. Revision: working diff against 303feaa5d81f02c554f597bdf8a4873f35e92cdd, python/tests/test_two_corpora.py.
- 2026-10-28T20:11:18Z (fix/duplicate-refusal): attached: implementation-review.md (1282 bytes): Read-only implementation review by codex/gpt-6.1-sol; no findings
- 2026-10-28T20:13:15Z (fix/duplicate-refusal): Focused just test-one tests/test_two_corpora.py: 13 passed in 37.86s; just check passed. First just test-fast granted 1 worker under transient load; interrupted after 103 passed in 234.50s, no failures, once host-budget show recovered to 12. Rebuild generated testmon data and rerun the whole fast check at the current host budget.
- 2026-10-28T20:17:00Z (fix/duplicate-refusal): Identify the current integration owner
  provenance: {"harness_session":"codex:01a1841b-698b-79f0-b115-6c26f9b6acb0","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-28T20:17:50Z (fix/duplicate-refusal): Verified: just test-fast selected every test and passed all 899 in 242.23s; focused test file passed all 13; just check and commit hook passed; independent codex/gpt-6.1-sol review accepted with no findings. Fix commit 065ae81. Interrupted first fast run had 103 passed, no failures; rerun was green in full.
- 2026-10-28T20:17:52Z (fix/duplicate-refusal): retained: {"host":"titan","kind":"worktree","path":".worktrees/fix-duplicate-refusal","state":"kept","verification":"verified","purpose":"Immediate local integration of reviewed test-only fix 065ae81 and checked removal in this turn; no scratch or off-tree evidence copies","next_owner":"session:codex:01a1841b-698b-79f0-b115-6c26f9b6acb0","cleanup_trigger":"After local merge to main, verify ignored-file disposition, test timing harvest and no host pointers, then remove task worktree"}
- 2026-10-28T20:17:53Z (fix/duplicate-refusal): done
  provenance: {"harness_session":"codex:01a1841b-698b-79f0-b115-6c26f9b6acb0","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-28T20:17:53Z (fix/duplicate-refusal): Corrected stale duplicate fixture for content-identity holders; conflicting copies still refuse and identical copies permit unrelated selected reads. 13 focused and 899 full-selection fast tests passed; guide checks and independent review passed. Local merge and checked worktree cleanup follow in this turn.
  provenance: {"harness_session":"codex:01a1841b-698b-79f0-b115-6c26f9b6acb0","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-28T20:18:23Z (main): Local integration complete: main fast-forwarded to 0232f09, including fix 065ae81 and the full review attachment. Removal dispositions: python/.pytest_cache and python/.testmondata are regenerable test caches; python/.venv is the regenerable isolated installed environment. No other ignored or untracked files, no scratch or off-tree evidence copies; review is committed on main. tt-report ran successfully. Host-pointer scan of user bin directories and systemd units found none into this worktree; this session changed no launchers or config includes.
