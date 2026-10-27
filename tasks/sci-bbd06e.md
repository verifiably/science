---
id: sci-bbd06e
title: "Launchers treat SIGINT as a stop signal: Ctrl-C on science serve gets the held startup and drained shutdown"
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-27T00:19:50Z
updated: 2026-10-27T00:19:50Z
depends: []
tags: [command-framework]
source: sci-6ffb7f
agent: claude-code/claude-opus-5-5
origin: agent
---

science.stop holds SIGTERM and SIGHUP across launcher startup and cleanup (sci-6ffb7f), but SIGINT still raises KeyboardInterrupt wherever the main thread is. Ctrl-C is the ordinary way to stop an interactive `science serve`, so it can still hit the windows that task closed: between bind and the try that owns cleanup (leaked socket), during session open (unclosed session), and inside the close-time drain (an in-flight socket write then meets SessionClosed and socketserver prints a traceback). Raised as declined-to-judge by the sci-6ffb7f implementation review. Decide whether SIGINT joins _STOP_SIGNALS (exit status 130, and the existing SIG_IGN rule) or gets its own handling; add it to the startup-window and EOF-drain tests in python/tests/test_launcher_stop.py; amend coordination spec §5.3's 2026-10-26 amendment.

## Notes

- 2026-10-27T00:19:50Z (add): created
  provenance: {"harness_session":"claude-code:c826b605-87ec-4aa8-8aea-62a46a0d13b8","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
