---
id: sci-a2c91b
title: Add the MIT LICENSE file
status: done
priority: 2
size: xs
complexity: low
process: direct
owner: chore/mit-license
created: 2026-10-09T18:46:54Z
updated: 2026-10-10T11:35:52Z
started: 2026-10-10T11:31:16Z
completed: 2026-10-10T11:35:51Z
depends: []
tags: [docs]
model: claude-opus-5-5
agent: claude-code/claude-opus-5-5
---

The repository is public with no LICENSE and no licence in python/pyproject.toml. Add the MIT text at the root and at python/LICENSE, and license = "MIT" plus license-files = ["LICENSE"] in python/pyproject.toml, matching atoms and nodes (same copyright line). Decided by the user 2026-10-09: MIT across the verifiably repositories (verifiably/docs vdocs-910898).

## Notes

- 2026-10-10T11:31:16Z (main): started
  provenance: {"harness_session":"claude-code:ac414f83-8043-4a78-85f6-3816577b190d","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T11:31:16Z (main): halt override: started past sci-5937be by ac414f83-8043-4a78-85f6-3816577b190d: LICENSE file and pyproject licence metadata only; touches no tests or code, cannot affect test-fast latency
- 2026-10-10T11:31:25Z (chore/mit-license): resumed
  provenance: {"harness_session":"claude-code:ac414f83-8043-4a78-85f6-3816577b190d","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T11:35:51Z (chore/mit-license): test-fast: 693 passed, 1 failed (test_a_trickling_listener_cannot_extend_the_selection_deadline) under load average 42; passes alone via test-one; change touches no code
- 2026-10-10T11:35:51Z (chore/mit-license): done
  provenance: {"harness_session":"claude-code:ac414f83-8043-4a78-85f6-3816577b190d","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T11:35:51Z (chore/mit-license): MIT LICENSE at the root and python/LICENSE (atoms/nodes text); python/pyproject.toml declares license = "MIT" and license-files; built wheel carries License-Expression: MIT
  provenance: {"harness_session":"claude-code:ac414f83-8043-4a78-85f6-3816577b190d","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
