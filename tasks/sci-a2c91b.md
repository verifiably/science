---
id: sci-a2c91b
title: Add the MIT LICENSE file
status: doing
priority: 2
size: xs
complexity: low
process: direct
owner: main
created: 2026-10-09T18:46:54Z
updated: 2026-10-10T11:31:16Z
started: 2026-10-10T11:31:16Z
depends: []
tags: [docs]
agent: claude-code/claude-opus-5-5
---

The repository is public with no LICENSE and no licence in python/pyproject.toml. Add the MIT text at the root and at python/LICENSE, and license = "MIT" plus license-files = ["LICENSE"] in python/pyproject.toml, matching atoms and nodes (same copyright line). Decided by the user 2026-10-09: MIT across the verifiably repositories (verifiably/docs vdocs-910898).

## Notes

- 2026-10-10T11:31:16Z (main): started
  provenance: {"harness_session":"claude-code:ac414f83-8043-4a78-85f6-3816577b190d","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T11:31:16Z (main): halt override: started past sci-5937be by ac414f83-8043-4a78-85f6-3816577b190d: LICENSE file and pyproject licence metadata only; touches no tests or code, cannot affect test-fast latency
