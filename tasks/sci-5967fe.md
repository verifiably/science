---
id: sci-5967fe
title: "belief and next across the mounts, and the two-corpus check"
status: done
priority: 2
size: m
complexity: mid
process: direct
owner: coordination-part3
created: 2026-09-30T15:01:04Z
updated: 2026-09-30T21:21:11Z
started: 2026-09-30T20:29:05Z
completed: 2026-09-30T21:01:13Z
depends: [sci-e8b32e]
parent: sci-923d3a
tags: [projects]
model: claude-opus-5-5
agent: claude-code/claude-opus-5-5
plan: docs/plans/2026-09-30-coordination-multi-corpus.md
step: "Task 4: `belief` and `next` across the mounts, and the two-corpus check"
---

## Notes

- 2026-09-30T20:29:05Z (coordination-part3): started
  provenance: {"harness_session":"claude-code:3b3b2eb8-e8ff-4d3a-ab47-ad4337a07185","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T20:56:12Z (coordination-part3): mutation checks: (1) next.handle enumerating the write root only — unselected arm: test_the_unselected_session_reads_both_corpora… and test_a_sessionless_cli_read… fail (archived row dropped); selected arm (mounts filtered to write root): test_next_under_a_project_selecting_both… fails with the unmounted refusal naming proposition:archived. (2) mount_profiles returning config.profile for every root: all 10 tests in test_two_corpora error at the fixture with ContractMismatch on the archive mount. (3) load_config compiling read_contracts into profile: test_two_corpora passes all 10 (test_activating_read_contracts… builds the widened profile directly, so it shows the consequence, not the load_config mutation); the mutation is caught by test_config_mounts.py::test_read_contracts_are_available_and_never_activated. All reverted.
- 2026-09-30T21:01:13Z (coordination-part3): done
  provenance: {"harness_session":"claude-code:3b3b2eb8-e8ff-4d3a-ab47-ad4337a07185","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T21:01:13Z (coordination-part3): belief and next read across mounted corpora via ReadContext.mount_holding; single_view deleted; two-corpus check in test_two_corpora.py
  provenance: {"harness_session":"claude-code:3b3b2eb8-e8ff-4d3a-ab47-ad4337a07185","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T21:21:10Z (coordination-part3): review: impl round 1 — verdict: revise; findings: Important 2; reviewer: controller
- 2026-09-30T21:21:10Z (coordination-part3): fix round 1: next translates the kernel's address-unknown into invalid-input naming the refs, corpus_roots and the unmounted corpus ids when the world's registry has live admitted corpora with no configured carrier; _context refuses an assessment whose run reads a dataset its mount does not declare instead of silently dropping it. Mutations: bypassing the translation fails the narrowed test; dropping the refusal call fails the hiding-view test; emptying the lineage roots fails test_each_corpus_lineage_reaches_the_evaluator. All reverted.
