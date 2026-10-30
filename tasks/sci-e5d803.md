---
id: sci-e5d803
title: Prove relocated-store writes and gate rollout with a live inventory
status: doing
priority: 1
size: m
complexity: high
process: direct
owner: sci-300dab-stores
created: 2026-10-30T20:24:43Z
updated: 2026-10-30T23:26:25Z
started: 2026-10-30T23:26:25Z
depends: [sci-bb8611]
parent: sci-300dab
tags: [holdings]
source: "sci-300dab:readable-stores-plan-task-3"
agent: codex
origin: agent
spec: docs/specs/2026-10-30-readable-stores-design.md
plan: docs/plans/2026-10-30-readable-stores.md
step: "Task 3: Prove relocated-store writes and gate rollout with a live inventory"
---

Implement plan Task 3 after plan approval and Tasks 1–2: real restored-store integration, tested operator init recipe and current configuration docs. Before integration refresh discovery and nonmutating inspection of every configured store, distinguishing active roots from archived configs with evidence; block on unresolved active failures or coverage gaps. Live migration/restore/reconfiguration and holding writes need separate authorization. Planning found mm30 readable and the spike world deleted per its retained report; recheck rather than treating these as permanent facts.

## Notes

- 2026-10-30T20:24:43Z (add): created
  provenance: {"harness_session":"codex:01a18e58-0cdf-75c2-bf7d-f4ac22417069","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
- 2026-10-30T23:26:25Z (sci-300dab-stores): started
  provenance: {"harness_session":"codex:01a18e58-0cdf-75c2-bf7d-f4ac22417069","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-30T23:26:25Z (sci-300dab-stores): halt override: started past sci-0bea23 by 01a18e58-0cdf-75c2-bf7d-f4ac22417069: Execute approved readable-stores plan despite open timing halt sci-0bea23
