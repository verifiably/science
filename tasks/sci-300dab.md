---
id: sci-300dab
title: "A relocated world has no writable store: science binds one store_root, the restored replica, so every dataset holding write refuses"
status: doing
priority: 1
size: m
complexity: high
process: planned
owner: sci-300dab-stores
created: 2026-10-30T19:15:26Z
updated: 2026-10-30T19:51:56Z
started: 2026-10-30T19:45:58Z
depends: []
tags: [holdings]
source: mm-62e2da
agent: claude-code/claude-opus-5-5
origin: mixed
spec: docs/specs/2026-10-30-readable-stores-design.md
---

A relocated world's store root arrives through restore_root as read-only-serviceable. In atoms (lifecycle design §5, §12) nothing leaves that state and grant_read_serviceability never grants writability; beliefs makes a writable store only through init_store_root or fork_store, each with a fresh store id. Science binds exactly one `store_root` for both reads and writes, and `holdings.held_path_for` resolves only observations naming that store's id. So in the relocated mm30 world every `science dataset` holding write refuses: atoms raises PreconditionRefused("root lifecycle state read-only-serviceable does not grant writability"), and beliefs raises StoreWriteRefused. Repointing `store_root` at a fork or a fresh store would orphan the inherited holdings (5 active in the mm30 world).

Corpora already have the needed shape: restored `corpus_roots` plus a writable `write_root`. The store has no counterpart.

Wanted: a writable store beside the restored one, for example read stores plus one write store, with held-path resolution over every configured store's id, or a fork whose lineage science honours. The route that creates it for a relocated world is also wanted, plus docs for the config change.

Observed 2026-10-30 in the mm30 world (store 05b6c1225e710bb1559f36e8333f3f29), invocation 6cf80d367660d05be56a00f686e7f23c. It blocks mm-62e2da, the multiple-myeloma phase-2 key holding.

## Notes

- 2026-10-30T19:15:26Z (add): created
  provenance: {"harness_session":"claude-code:a2943a1d-dd3d-4577-a43b-8347da7f11bf","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"mixed"}
- 2026-10-30T19:45:58Z (main): started
  provenance: {"harness_session":"codex:01a18e58-0cdf-75c2-bf7d-f4ac22417069","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-30T19:45:58Z (main): halt override: started past sci-0bea23 by 01a18e58-0cdf-75c2-bf7d-f4ac22417069: User explicitly requested sci-300dab; investigate and prepare its design despite the existing test-latency halt sci-0bea23.
- 2026-10-30T19:46:36Z (sci-300dab-stores): resumed
  provenance: {"harness_session":"codex:01a18e58-0cdf-75c2-bf7d-f4ac22417069","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-30T19:47:24Z (sci-300dab-stores): Origin recovered from claude-code:a2943a1d-dd3d-4577-a43b-8347da7f11bf: human asked to diagnose the store lifecycle and reconcile mm-62e2da, then authorized filing three science tasks. Writable-side-store architecture was the agent proposal; refusal closure and dangling-intent settlement were separately filed as sci-eccb43 and sci-409235. Current code confirms single-store binding in session.py and config.ReadContext; held_path_for and vocabulary.snapshot only resolve that identity. Planned design in .worktrees/sci-300dab-stores; setup used the AGENTS.md hook command. Full-suite baseline deliberately deferred to implementation Setup per planned-work rule; no code or live-world changes.
- 2026-10-30T19:50:37Z (sci-300dab-stores): Design recommendation frozen for builder review at science commit 915409e42b540287e3fce9f062a097cca1bda100, docs/specs/2026-10-30-readable-stores-design.md: retain store_root for writes and add read_store_roots for identity-bound reads. The creation route is a documented operator-time init_store_root recipe, not a command-reachable lifecycle act. just check and git diff --check passed; no runtime tests were run in this design-only phase.
- 2026-10-30T19:51:15Z (sci-300dab-stores): review: spec round 1 — verdict: accept; findings: none; reviewer: codex/gpt-6.1-sol
- 2026-10-30T19:51:18Z (sci-300dab-stores): attached: stores-builder-check-report.md (432 bytes): Full builder review of frozen design 915409e; accepted with no important questions, reviewer codex/gpt-6.1-sol.
- 2026-10-30T19:51:53Z (sci-300dab-stores): retained: {"host": "titan", "kind": "scratch", "path": "$WORK_ROOT/science/.worktrees/sci-300dab-stores/.superpowers/sdd/sci-300dab-stores", "state": "kept", "verification": "verified", "purpose": "Frozen-design builder review workspace; full review also attached to sci-300dab as stores-builder-check-report.md", "next_owner": "task:sci-300dab", "cleanup_trigger": "After design approval and completed implementation integration, verify attached review then inspect for removal", "manifest": "$WORK_ROOT/science/.worktrees/sci-300dab-stores/.superpowers/sdd/sci-300dab-stores/manifest.sha256", "sha256": "fe4be9d742a5ef85596bc733016e5289c3e7dc9eaafd84444a1d9d69f043aea1"}
- 2026-10-30T19:51:56Z (sci-300dab-stores): retained: {"host":"titan","kind":"worktree","path":".worktrees/sci-300dab-stores","state":"kept","verification":"verified","purpose":"Locked branch sci-300dab-stores holds frozen spec 915409e and attached builder review for human design review, then implementation planning","next_owner":"task:sci-300dab","cleanup_trigger":"After human spec and plan approval, implementation, final review and local integration, inspect retained contents and host pointers before removal"}
