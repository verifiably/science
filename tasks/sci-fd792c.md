---
id: sci-fd792c
title: Let the operator name the service socket path
status: done
priority: 2
size: xs
owner: quick-wins
created: 2026-09-09T10:22:23Z
updated: 2026-09-09T12:10:28Z
depends: []
tags: [command-framework]
spec: docs/specs/2026-08-31-command-framework-design.md
---

science.cli._service_socket hardcodes <operations_root>/service.sock, and both 'science serve' and _via_service derive the path from it. There is no override.

serve() refuses before binding when the path exceeds the AF_UNIX limit of 107 bytes (science.serve.MAX_SOCKET_PATH_BYTES), which names the problem — the raw OSError named neither the path nor the limit — but leaves no remedy short of relocating operations_root. The path is 117 bytes from a worktree checkout of this repo and 90 from the main checkout, so the limit is reachable in ordinary use, not a contrived case.

A '--socket PATH' option on the serve verb and on write-routed commands, or a config key beside operations_root, closes it. Both ends must agree on the resolved path, so whichever form is chosen has to be readable by _via_service too.

## Notes

- 2026-09-09T12:10:28Z (quick-wins): optional service_socket config key, resolved like operations_root and defaulting to service.sock beside it; both the serve verb and _via_service read config.service_socket; spec §9.1 amended
