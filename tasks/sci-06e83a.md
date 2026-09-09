---
id: sci-06e83a
title: "Service process, CLI write routing, synthetic exemplars"
status: done
priority: 1
size: l
owner: service-process
created: 2026-08-31T21:29:15Z
updated: 2026-09-09T10:08:17Z
depends: [sci-c3f0bb]
tags: [command-framework]
spec: docs/specs/2026-08-31-command-framework-design.md
plan: docs/plans/2026-08-31-command-framework.md
step: "Task 13: Service process, CLI write routing, synthetic exemplars end-to-end (beliefs-gated)"
---

## Notes

- 2026-09-09T10:08:17Z (service-process): Unix-socket writer service (science serve), CLI write routing preserving the read path's wire, and four synthetic exemplars end to end. Fixed a Task 12 defect the pub-view exemplar exposed: RequiredCapabilities.publishes() refuses to construct a requirement, so _required states the permit-exceeded refusal itself and computes the requirement before touching the session. Added an AF_UNIX path-length refusal and daemon threads (server_close otherwise joins handlers blocked on live clients). Spec and README now say sub-project 2 is implemented. 257 passed; science build ok
