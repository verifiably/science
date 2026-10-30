---
id: sci-eb1559
title: Retain and dispose assumption-sweep pilot evidence after incident and control follow-ups
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-30T14:07:58Z
updated: 2026-10-30T14:12:04Z
depends: [mm-eca42c, sci-30eb71]
tags: []
source: sci-b2755f
agent: codex
origin: agent
---

Own the persistent exact pilot inputs, selected-section evidence and execution workspace after the accepted sweep branch integrates. Wait for mm-eca42c exposure disposition and sci-30eb71 compact-control correction; then verify hashes and preserve any still-needed audit evidence before per-item cleanup. This is evidence lifecycle work, not a new scientific analysis or authorization to use stopped-source results. Retained paths and manifests will be recorded on this task before transfer. No branch or worktree is required for read-only lifecycle maintenance.

## Notes

- 2026-10-30T14:07:58Z (add): created
  provenance: {"harness_session":"codex:01a18ce3-2793-7ad1-b204-ef9b88b33aba","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
- 2026-10-30T14:11:57Z (feat/sci-b2755f-assumption-sweep): Created $WORK_ROOT/science/sci-b2755f/plan-workspace on titan as an exact copy of the completed plan workspace before worktree cleanup; owner sci-eb1559, mutable until checkpoint below.
- 2026-10-30T14:11:59Z (feat/sci-b2755f-assumption-sweep): retained: {"host": "titan", "kind": "scratch", "path": "$WORK_ROOT/science/sci-b2755f", "state": "kept", "verification": "verified", "purpose": "Complete persistent pilot input/helper/evidence container; includes copyrighted selected sections off-tree, not permission for reuse", "next_owner": "task:sci-eb1559", "cleanup_trigger": "After mm-eca42c incident disposition and sci-30eb71 control correction, verify preservation and assess each item before cleanup", "manifest": "$WORK_ROOT/science/sci-b2755f/manifest.sha256", "sha256": "df97fc91d331f43a13250e9cdfbf6f90294810f27c7785a0cc80885ad4007eb4"}
- 2026-10-30T14:12:01Z (feat/sci-b2755f-assumption-sweep): retained: {"host": "titan", "kind": "evidence", "path": "$WORK_ROOT/science/sci-b2755f/pilot-v1-evidence", "state": "kept", "verification": "verified", "purpose": "Exact original inputs and logs", "next_owner": "task:sci-eb1559", "cleanup_trigger": "After mm-eca42c incident disposition and sci-30eb71 control correction, verify preservation and assess each item before cleanup", "manifest": "$WORK_ROOT/science/sci-b2755f/pilot-v1-evidence/manifest.sha256", "sha256": "c72642b8ff891608e3e49eb69a4093e0e0e7513a3f3bd8a9f192005c6f066693"}
- 2026-10-30T14:12:02Z (feat/sci-b2755f-assumption-sweep): retained: {"host": "titan", "kind": "evidence", "path": "$WORK_ROOT/science/sci-b2755f/pilot-v2-evidence", "state": "kept", "verification": "verified", "purpose": "Exact second failed non-OA probe evidence", "next_owner": "task:sci-eb1559", "cleanup_trigger": "After mm-eca42c incident disposition and sci-30eb71 control correction, verify preservation and assess each item before cleanup", "manifest": "$WORK_ROOT/science/sci-b2755f/pilot-v2-evidence/manifest.sha256", "sha256": "cff817d9495f81b81f650950b8bc263b84595b81138ba3051cd21f3e2f03f5d8"}
- 2026-10-30T14:12:04Z (feat/sci-b2755f-assumption-sweep): retained: {"host": "titan", "kind": "evidence", "path": "$WORK_ROOT/science/sci-b2755f/pilot-v3-evidence", "state": "kept", "verification": "verified", "purpose": "Exact OA-corrected source selections, incident evidence, metadata, frozen report copies and reader checks", "next_owner": "task:sci-eb1559", "cleanup_trigger": "After mm-eca42c incident disposition and sci-30eb71 control correction, verify preservation and assess each item before cleanup", "manifest": "$WORK_ROOT/science/sci-b2755f/pilot-v3-evidence/manifest.sha256", "sha256": "6c6ab3155c34a72c413397a9c0a0b0d891475e33a2686ac5d9148dd956c90e25"}
