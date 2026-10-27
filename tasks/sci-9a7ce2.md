---
id: sci-9a7ce2
title: Pass own-corpus declarations to publication and preview
status: done
priority: 2
size: s
complexity: mid
process: direct
owner: fix/9a7ce2-own-publication
created: 2026-10-27T15:49:59Z
updated: 2026-10-27T19:05:48Z
started: 2026-10-27T18:49:38Z
completed: 2026-10-27T19:04:24Z
closed: 2026-10-27T19:04:24Z
depends: [beliefs-7c612b]
tags: []
source: beliefs-7c612b
agent: codex
origin: agent
---

Implement the consumer integration from beliefs spec docs/superpowers/specs/2026-10-27-owned-replica-publication-design.md revision deb8d99 (resolve the beliefs checkout through tasks projects). Reuse acceptance_inputs(ctx).own_roots for both a new writer.publish attempt in commands/publish.py and publication_preview in commands/publish_preview.py; never compute ownership for resume. This intentionally adds the acceptance classifier preconditions to preview: duplicate claimed carriers, exactly one write mount, and errors reading any configured mount must not silently fall back. Test configured markerless Own roots, sharing-registry exclusion even when hand-listed, marker-bearing roots, duplicate-holder refusal, missing/duplicate write mounts using the existing helper failure behavior, preview/publish parity under v2 and v3, and resume without recomputation. Update the preview comment and current documentation. No new user configuration option, registry mutation, or live-world write. Kernel implementation must land first; sci-775e90 owns the live milestone rerun and should also depend on this task.

## Notes

- 2026-10-27T15:49:59Z (add): created
  provenance: {"harness_session":"codex:01a17dcb-2a5d-7101-9aa7-305b6690786c","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
- 2026-10-27T18:49:38Z (main): started
  provenance: {"harness_session":"codex:01a17eb1-eac2-7e50-9dca-09bb9c9cb87b","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-27T18:50:17Z (fix/9a7ce2-own-publication): resumed
  provenance: {"harness_session":"codex:01a17eb1-eac2-7e50-9dca-09bb9c9cb87b","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-27T18:52:48Z (fix/9a7ce2-own-publication): Direct implementation in .worktrees/9a7ce2-own-publication (fix/9a7ce2-own-publication). Hydrated with documented uv sync route using --frozen; full baseline just test: 886 passed in 118.52s. Kernel prerequisite integrated in beliefs main at 918c5c1; frozen spec deb8d99 section 6 is the integration contract. sci-775e90 already depends on this task. Affected scope: publish/new-attempt call, publish-preview call/comment, command tests and current publication docs; no API/config/export/registry change.
- 2026-10-27T18:58:08Z (fix/9a7ce2-own-publication): RED proof: markerless restored replica failed preview under v2 (attribution-contract-unpinned) and v3 (attribution-source-invalid/marker-absent); after preview wiring, the same tests advanced to publish and failed with those reasons there. Classifier-precondition tests also failed before wiring. Existing remote fault/resume test passes with ReadContext.mounts forced to fail before resume, proving no reclassification. Fixture setup initially needed the documented replication destination parent; fixed the fixture, with no upstream change.
- 2026-10-27T19:01:45Z (fix/9a7ce2-own-publication): Implementation 53c0764: both commands pass the existing Own classification, resume bypasses it, docs/prompts and generated adapters updated. GREEN: focused publication tests 21 passed in 45.84s; just check and commit hook passed. First fast run selected all 898: 897 passed, only test_generated_tree_matches_committed failed (stale generated prompts). Regenerated with uv run science adapters build; focused adapter test 1 passed, then just test-fast selected the prior failing case and passed 1/1. No runtime code changed after the 897 passing cases. Independent read-only whole-branch review dispatched against 210a783..53c0764; no live-world test or push.
- 2026-10-27T19:03:45Z (fix/9a7ce2-own-publication): review: impl round 1 — verdict: accept; findings: none; reviewer: codex/gpt-6.1-sol
- 2026-10-27T19:03:47Z (fix/9a7ce2-own-publication): attached: impl-round-1-report.md (2863 bytes): Full read-only whole-branch review of 210a783..53c0764; verified codex/gpt-6.1-sol; accept, no findings
- 2026-10-27T19:04:08Z (fix/9a7ce2-own-publication): Ruling: preserve the existing ValueError on missing/duplicate write mounts (review declined-to-judge item 1). Why: sci-9a7ce2 and beliefs spec deb8d99 section 6 explicitly require the helper’s actual failure behavior, not a new refusal translation. Cost: malformed mount configurations still expose the unpacking error rather than a friendlier diagnostic. Revision: 53c0764. No corrective change.
- 2026-10-27T19:04:10Z (fix/9a7ce2-own-publication): Ruling: authenticated authorship and live milestone success remain outside this integration (review declined-to-judge item 2). Why: the accepted design supplies an explicit publisher claim and sci-775e90 owns the live rerun. Cost: this integration does not prove authorship or criterion-5 success in the live world. Revision: 53c0764; kernel spec deb8d99. No deferred minor findings.
- 2026-10-27T19:04:23Z (fix/9a7ce2-own-publication): retained: {"host":"titan","kind":"worktree","path":".worktrees/9a7ce2-own-publication","state":"kept","verification":"verified","purpose":"Reviewed implementation and full review attachment, pending immediate local integration and checked removal in this turn; ignored items are only regenerable pytest cache, testmon database and installed environment","next_owner":"session:codex:01a17eb1-eac2-7e50-9dca-09bb9c9cb87b","cleanup_trigger":"Successful local merge, merged-tree checks, tt-report and final ignored-file/host-pointer checks"}
- 2026-10-27T19:04:24Z (fix/9a7ce2-own-publication): done
  provenance: {"harness_session":"codex:01a17eb1-eac2-7e50-9dca-09bb9c9cb87b","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-27T19:04:24Z (fix/9a7ce2-own-publication): Implemented 53c0764: existing Own roots passed to preview and new publication attempts; frozen resume preserved. V2/v3 restored-replica integration, registry/marker exclusions, duplicate/mount/read-error preconditions and remote resume covered. Baseline 886 passed; focused 21 passed; fast 897 passed plus stale-adapter case repaired and rerun 1/1; checks clean. Independent codex/gpt-6.1-sol review accepts with no findings; full report attached and both scope rulings recorded. This session owns immediate local integration and checked worktree removal. No live milestone claim or push; sci-775e90 owns live rerun.
  provenance: {"harness_session":"codex:01a17eb1-eac2-7e50-9dca-09bb9c9cb87b","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-27T19:05:40Z (main): Integrated locally into main by fast-forward at b6e3dbd. Merged-tree just check passed; restored-own-replica v2/v3 tests passed 2/2 and generated-adapter consistency passed 1/1. Full reviewer report is listed by tasks show and hash-identical in main and the task worktree (SHA256 18d38eac2ad296de50044b55f4db5a6e25ef6c0907effbebc6aff6e04bbd17de). No host launcher, user systemd unit or inspected config pointer resolves into the worktree. Ignored-file dispositions: python/.pytest_cache and python/.testmondata are regenerable test cache/dependency-selection data; python/.venv is installed dependencies regenerated by the documented setup route; discard these on checked removal. No tracked/untracked changes, submodules, plan workspaces or off-tree evidence copies remain. tt-report completed before removal.
- 2026-10-27T19:05:48Z (main): retained: {"host":"titan","kind":"worktree","path":".worktrees/9a7ce2-own-publication","state":"released","verification":"verified","purpose":"Reviewed branch integrated locally at b6e3dbd, merged-tree checks passed, full review hash-verified in main attachment, checked worktree removal completed and task branch deleted","next_owner":"none","cleanup_trigger":"none"}
