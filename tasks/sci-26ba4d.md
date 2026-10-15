---
id: sci-26ba4d
title: "test_a_trickling_listener_cannot_extend_the_selection_deadline fails under host load: its 0.4 s wall bound covers all of cli.main"
status: todo
priority: 2
size: xs
complexity: low
process: direct
created: 2026-10-15T08:38:43Z
updated: 2026-10-15T08:38:43Z
depends: []
tags: [testing]
agent: claude-code/claude-opus-5-5
---

Failed in a full test-fast run on titan 2026-10-15 at load 15 (16 workers), passed alone in 2.3 s. The test asserts elapsed < 0.4 s around cli.main(project-show), which includes config load and dispatch, not only the 0.1 s selection deadline. Bound the deadline itself (e.g. time the selection call, or assert against a clock the test controls) so load cannot fail it.
