---
id: sci-d2ae2f
title: "test_cli_surface: help, usage and enum checks call main() in-process; one subprocess test keeps the python -m entry"
status: done
priority: 0
size: xs
complexity: low
process: direct
owner: test/cli-surface-in-process
created: 2026-10-15T08:32:59Z
updated: 2026-10-15T08:39:12Z
started: 2026-10-15T08:33:11Z
completed: 2026-10-15T08:39:12Z
depends: []
parent: sci-5937be
tags: [testing, test-latency]
agent: claude-code/claude-opus-5-5
---

Measured 2026-10-15: test_cli_surface spawns python -m science.cli 106 times per full run, ~1 s each under xdist load, 80 of 1252 worker-seconds (6%). argparse help and usage errors raise SystemExit in-process, so capsys sees the same stdout/stderr and exit code. Keep test_version as the subprocess check of the module entry point.

## Notes

- 2026-10-15T08:33:11Z (test/cli-surface-in-process): started
  provenance: {"harness_session":"claude-code:16bb464b-a654-47f6-8366-99c2a9b2a602","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-15T08:39:12Z (test/cli-surface-in-process): done
  provenance: {"harness_session":"claude-code:16bb464b-a654-47f6-8366-99c2a9b2a602","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-15T08:39:12Z (test/cli-surface-in-process): test_cli_surface runs help/usage/enum checks through main() in-process (30dac66); module serial 57.8 s -> 4.3 s; test_version keeps the subprocess entry-point check
  provenance: {"harness_session":"claude-code:16bb464b-a654-47f6-8366-99c2a9b2a602","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
