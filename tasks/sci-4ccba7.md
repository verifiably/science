---
id: sci-4ccba7
title: Test subprocesses get a key-by-key environment and git fixtures stay off host config
status: todo
priority: 3
size: s
complexity: low
process: direct
created: 2026-10-27T00:19:51Z
updated: 2026-10-27T00:19:51Z
depends: []
tags: [testing]
agent: claude-code/claude-opus-5-5
origin: agent
---

Several tests start subprocesses with the inherited environment, which the test rules forbid (a failing case's captured output can then print a credential): python/tests/test_launcher_stop.py (both Popen calls), test_cli_surface.py (science.cli runner), test_selection_query.py (science.cli runner), and test_front_door.py, which passes {**os.environ, ...} to the pre-push hook and the recipe runner and runs git init/add in fixture repos with the host's git config. Build each environment key by key (PATH, HOME at a test-owned temp dir, the variables the child reads, fake values for credentials), set GIT_CONFIG_GLOBAL/GIT_CONFIG_NOSYSTEM for git fixtures, unset inherited GIT_* before building them, and assert the fixture's toplevel and absolute-git-dir before the first write. Found while closing sci-6ffb7f; one shared helper in tests/helpers is likely enough.

## Notes

- 2026-10-27T00:19:51Z (add): created
  provenance: {"harness_session":"claude-code:c826b605-87ec-4aa8-8aea-62a46a0d13b8","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
