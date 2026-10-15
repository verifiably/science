---
id: sci-89f5fe
title: "test_serve: a serve_forever thread left running spins its xdist worker"
status: todo
priority: 0
size: xs
complexity: low
process: direct
created: 2026-10-15T11:37:31Z
updated: 2026-10-15T11:37:31Z
depends: []
parent: sci-5937be
tags: [testing]
agent: claude-code/claude-opus-5-5
---

test_cli_write_routes_to_the_configured_socket calls server_close() without shutdown(), so its serve_forever daemon thread keeps polling a closed socket for the rest of the worker's life. Measured: the walked two-corpus world builds in 14 s alone or after a clean serve test, 77 s after this one; in a 16-worker config.py selection the worker that ran it ends at ~110 s while the rest end by 39-70 s. Fix: shut the server down; guard: test_serve fails any test that leaves a serve_forever thread alive. Leak since 3427042 (2026-09-09), before the breach window.
