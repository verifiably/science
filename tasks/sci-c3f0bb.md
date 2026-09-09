---
id: sci-c3f0bb
title: "Write dispatch with scoped permits, claims, and dedup"
status: done
priority: 1
size: l
owner: write-dispatch
created: 2026-08-31T21:29:15Z
updated: 2026-09-09T09:22:00Z
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
- 2026-09-05T09:16:28Z (main): Not startable on 2026-09-05: beliefs.session is absent (beliefs main e01d6d1). beliefs-afbbff is claimed by a finished session in beliefs/.worktrees/writer-session with an uncommitted design (docs/designs/2026-09-05-writer-session-design.md, status: designed, cut 19 freezes after review) and no code; science-side helpers (fixture_proposition_node, fixture_source_node, build_fixture_world) are ready
- 2026-09-09T09:11:18Z (write-dispatch): Contract amended 2026-09-09: open_attended_session and open_corpus require profile: ProfileSpec (beliefs writer-session design integration amendment 2026-09-07). Spec gains a domains config key compiled into ScienceConfig.profile; plan gains Step 0 repairing the fixture world (15 tests red on main)
- 2026-09-09T09:22:00Z (write-dispatch): Write branch of Dispatcher.invoke over a real attended session: scoped permits (declaration-time and act-time), atomic claims under one lock, dedup replaying canonically from the ledger, and ledger-rebuilt rendering on first response and replay alike. Config gained the domains key compiling ScienceConfig.profile; the fixture world was repaired for beliefs cut 22 (15 tests red on main). loader imports KIND_ACTS exactly and mcp.serve holds one session. Contract amendment landed in 3bfa28d, code in d5bb981. 245 passed
