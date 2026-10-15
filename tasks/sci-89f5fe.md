---
id: sci-89f5fe
title: "test_serve: a serve_forever thread left running spins its xdist worker"
status: done
priority: 0
size: xs
complexity: low
process: direct
owner: fix/serve-thread-leak
created: 2026-10-15T11:37:31Z
updated: 2026-10-15T12:03:43Z
started: 2026-10-15T11:37:49Z
completed: 2026-10-15T12:03:42Z
depends: []
parent: sci-5937be
tags: [testing]
agent: claude-code/claude-opus-5-5
---

test_cli_write_routes_to_the_configured_socket calls server_close() without shutdown(), so its serve_forever daemon thread keeps polling a closed socket for the rest of the worker's life. Measured: the walked two-corpus world builds in 14 s alone or after a clean serve test, 77 s after this one; in a 16-worker config.py selection the worker that ran it ends at ~110 s while the rest end by 39-70 s. Fix: shut the server down; guard: test_serve fails any test that leaves a serve_forever thread alive. Leak since 3427042 (2026-09-09), before the breach window.

## Notes

- 2026-10-15T11:37:49Z (fix/serve-thread-leak): started
  provenance: {"harness_session":"claude-code:68ab2ddc-9049-44b2-91f0-59dfdd878c6c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-15T12:03:41Z (fix/serve-thread-leak): review: impl round 1 — verdict: accept; findings: critical 0, important 0, minor 4; reviewer: claude-code/claude-opus-5-5
- 2026-10-15T12:03:41Z (fix/serve-thread-leak): minor (deferred): guard flags a thread from a higher-scoped fixture loaded late via request.getfixturevalue; a _DummyThread makes join raise a confusing RuntimeError; no pytester test proves the guard fires; leaks from session/module fixtures are unchecked by design
- 2026-10-15T12:03:42Z (fix/serve-thread-leak): done
  provenance: {"harness_session":"claude-code:68ab2ddc-9049-44b2-91f0-59dfdd878c6c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-15T12:03:42Z (fix/serve-thread-leak): both serve_forever leaks shut down (test_serve, test_belief_path_transports); conftest fails any test leaving a thread running; world build after the leaking test 77 s -> 14 s; full suite 694 passed 56.7 s at 16 workers
  provenance: {"harness_session":"claude-code:68ab2ddc-9049-44b2-91f0-59dfdd878c6c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
