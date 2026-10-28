---
id: sci-0bc09c
title: Fix selected next duplicate-corpus refusal regression blocking push
status: doing
priority: 2
size: xs
complexity: low
process: direct
owner: fix/duplicate-refusal
created: 2026-10-28T20:03:42Z
updated: 2026-10-28T20:11:18Z
started: 2026-10-28T20:03:53Z
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
