---
id: sci-a1d45f
title: "Run endpoint for the autonomy envelope: serve --run, handle checks, control socket and seal, path confinement, CLI handle mode, heads and log.v1"
status: todo
priority: 2
size: l
complexity: high
process: planned
created: 2026-10-12T12:10:24Z
updated: 2026-10-12T12:10:25Z
depends: [beliefs-7a56ef]
tags: []
source: autonomy-250f4d
agent: claude-code/claude-opus-5-5
---

The surface slice the autonomy envelope (sub-project 6) needs; design it here. Source: autonomy docs/specs/2026-10-12-envelope-design.md (branch envelope-design until merged), §4 and §12. Depends on the beliefs run-session slice.

- serve --run <launch file>: a run session with the tier's permit, written chains, run dir, scratch dir, socket, control socket, token file, lease.
- The handle: token from a ro-bound file; accept only SO_PEERCRED peers inside the actor's PID namespace (bad-peer otherwise) (row E13).
- The control socket: renew / seal / reports (session id, ledger path, basis at open and seal, sealed tips); EOF seals; seal.json written by the endpoint; seal-timeout path; the endpoint's own execution subtree (child cgroup, or direct children) killed at the seal; run-sealed refusal mapping.
- Decision 11 path confinement: scratch O_PATH handle, openat2 RESOLVE_BENEATH|NO_SYMLINKS|NO_MAGICLINKS|NO_XDEV, component-wise scratch prefix, fd-walk capture of code into <ops>/capture/<invocation>/<basename>, entrypoint opened beneath the capture before any intent, path-confinement-unavailable without openat2, dispatch refusal for commands that cannot comply (row E14).
- CLI handle mode: VERIFIABLY_ENDPOINT + VERIFIABLY_TOKEN_FILE route every declared command through the handle with no host config; handle-incomplete and handle-mode refusals; mcp bridge (row E19).
- heads [--resolve] and log --chain --after [--through] with the versioned log.v1 contract (chain identity, holdings act kind and location, fulfills, consumer tag, txid, registered paths, settlement registration and committed) (row E18).
- The basis computation: file digests of the installed beliefs, science and verifiably-* closure, plus policy, packs and contracts.
