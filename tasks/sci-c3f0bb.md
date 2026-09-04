---
id: sci-c3f0bb
title: "Write dispatch with scoped permits, claims, and dedup"
status: todo
priority: 1
size: l
created: 2026-08-31T21:29:15Z
updated: 2026-09-04T21:40:12Z
depends: [sci-5abf0b, beliefs-96a24a, beliefs-afbbff]
tags: [command-framework]
spec: docs/specs/2026-08-31-command-framework-design.md
plan: docs/plans/2026-08-31-command-framework.md
step: "Task 12: Write dispatch — requirements, claims, dedup (beliefs-gated)"
---

## Notes

- 2026-09-04T09:27:57Z (main): beliefs-96a24a design banked 2026-09-04 (beliefs docs/designs/2026-09-04-write-permits-design.md, cut 16 frozen at 895f822): exports beliefs.permit.RequiredCapabilities, KIND_ACTS, permit_covers and errors.PermitExceeded exactly as Task 12's Consumes block names them
- 2026-09-04T13:15:14Z (main): Companion contract amended: WritePermit gains the ungoverned dimension (beliefs design §13.7); Consumes names unchanged
- 2026-09-04T21:40:12Z (main): write-permit exports live at beliefs merge commit da37650: RequiredCapabilities, KIND_ACTS, and PermitExceeded
