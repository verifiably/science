---
id: sci-539f1b
title: Correct belief-path review report assertions and seam dependency
status: done
priority: 1
size: xs
owner: dogfood-commands
created: 2026-09-09T14:15:12Z
updated: 2026-09-09T14:18:20Z
depends: []
parent: sci-66b26d
tags: [dogfood]
---

Correct Task 12 transport expectations to render every identity recorded by the invocation, and block Task 3 on the public store identity reader. Keep the spec and task dependency graph consistent.

## Notes

- 2026-09-09T14:18:20Z (dogfood-commands): Corrected complete invocation report assertions and spec wording; Task 3 now depends on beliefs-5fe2e3 and the plan order reflects it. Verified the extracted report helper; just test: 270 passed.
