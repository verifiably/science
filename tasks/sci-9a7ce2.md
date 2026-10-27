---
id: sci-9a7ce2
title: Pass own-corpus declarations to publication and preview
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-27T15:49:59Z
updated: 2026-10-27T15:49:59Z
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
