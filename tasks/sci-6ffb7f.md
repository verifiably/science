---
id: sci-6ffb7f
title: Launcher lifecycle edges at stop and shutdown
status: doing
priority: 3
size: s
complexity: mid
process: direct
owner: coordination-closeout
created: 2026-09-24T14:26:54Z
updated: 2026-10-27T00:14:46Z
started: 2026-10-26T23:37:02Z
depends: []
parent: sci-c5528e
tags: [command-framework]
agent: claude-code/claude-opus-5-5
---

Edges left by coordination part 1's socket and stop-signal work (cli.py _stop_signals_exit, serve.py service_server, mcp.py serve): (1) a socket write still in flight when mcp serve shuts down hits SessionClosed at close_invocation and socketserver prints a traceback to stderr, the MCP harness's log — drain or join handler threads before session.close, or map it; (2) a stop signal in the microsecond window after bind but before the try that owns cleanup (cli.py serve arm; mcp.py between service_server's bind and server assignment) leaks the socket; (3) a stop signal while mcp serve/serve is still opening its session leaves that session unclosed (pre-existing). Also the test suite binds MCP sockets under MAIN_ROOT/.framework-test/<32 hex>/ops/service.sock, 90 bytes here against the 107-byte AF_UNIX limit: a longer checkout path breaks every MCP-driven test; give the test helpers a short default socket.

## Notes

- 2026-10-26T23:37:02Z (coordination-closeout): started
  provenance: {"harness_session":"claude-code:c826b605-87ec-4aa8-8aea-62a46a0d13b8","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-26T23:51:58Z (coordination-closeout): implemented in fbeb32a on coordination-closeout (just test 870 passed, just check rc 0); impl review dispatched to a fresh reviewer over 42604b7..fbeb32a
- 2026-10-27T00:01:44Z (coordination-closeout): review: impl round 1 — verdict: revise; findings: Important 1, Minor 4; reviewer: claude-code/claude-opus-5-5
- 2026-10-27T00:11:29Z (coordination-closeout): review: impl round 2 — verdict: accept; findings: Minor 3; reviewer: claude-code/claude-opus-5-5
- 2026-10-27T00:14:46Z (coordination-closeout): Ruling: round 2 Minor B (a few-bytecode unheld window between mcp serve's EOF return and its cleanup hold) is minor (deferred). Why: the MCP stdio order is close stdin, wait, then SIGTERM, so a first signal inside that window is not reachable in practice, and closing it needs a re-hold API. Cost if wrong: a stale socket and unclosed session on that exact timing, which the next launcher reports as an existing socket. Round 2 Minors A and C fixed in the following commit.
