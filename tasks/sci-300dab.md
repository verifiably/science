---
id: sci-300dab
title: "A relocated world has no writable store: science binds one store_root, the restored replica, so every dataset holding write refuses"
status: todo
priority: 1
size: m
complexity: high
process: planned
created: 2026-10-30T19:15:26Z
updated: 2026-10-30T19:15:26Z
depends: []
tags: [holdings]
source: mm-62e2da
agent: claude-code/claude-opus-5-5
origin: mixed
---

A relocated world's store root arrives through restore_root as read-only-serviceable. In atoms (lifecycle design §5, §12) nothing leaves that state and grant_read_serviceability never grants writability; beliefs makes a writable store only through init_store_root or fork_store, each with a fresh store id. Science binds exactly one `store_root` for both reads and writes, and `holdings.held_path_for` resolves only observations naming that store's id. So in the relocated mm30 world every `science dataset` holding write refuses: atoms raises PreconditionRefused("root lifecycle state read-only-serviceable does not grant writability"), and beliefs raises StoreWriteRefused. Repointing `store_root` at a fork or a fresh store would orphan the inherited holdings (5 active in the mm30 world).

Corpora already have the needed shape: restored `corpus_roots` plus a writable `write_root`. The store has no counterpart.

Wanted: a writable store beside the restored one, for example read stores plus one write store, with held-path resolution over every configured store's id, or a fork whose lineage science honours. The route that creates it for a relocated world is also wanted, plus docs for the config change.

Observed 2026-10-30 in the mm30 world (store 05b6c1225e710bb1559f36e8333f3f29), invocation 6cf80d367660d05be56a00f686e7f23c. It blocks mm-62e2da, the multiple-myeloma phase-2 key holding.

## Notes

- 2026-10-30T19:15:26Z (add): created
  provenance: {"harness_session":"claude-code:a2943a1d-dd3d-4577-a43b-8347da7f11bf","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"mixed"}
