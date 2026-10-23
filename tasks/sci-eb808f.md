---
id: sci-eb808f
title: "Git transport: commit through plumbing on a bare cache instead of a checked-out working tree"
status: todo
priority: 2
size: m
complexity: mid
created: 2026-10-23T18:45:05Z
updated: 2026-10-23T18:45:05Z
depends: []
tags: [commons]
source: sci-13050a
agent: claude-code
---

Deferred from the commons 1a final review (ledger attached to sci-13050a: Final M3, M6, and the two fix-round minors). science/transport_git.py checks the remote's tree out into a cache working tree, so (1) the user's global git config and the remote's .gitattributes apply at add/commit (commit.gpgsign can block in the dispatcher lock; core.autocrlf, filter=lfs, text/eol can alter blobs), (2) a remote that plants <cid>.head-artifact.v1 as a symlink entry makes our push keep mode 120000 for the head artifact (our cat-file readers and the kernel listing are unaffected, but a third-party checkout dangles, and an idempotent re-push never repairs it), (3) a plain file left at <cid> after a deleted branch makes every later push refuse 'not a directory', and (4) the cache has no lock, so read-only provider-inspect can reset it under a concurrent publish. Committing with hash-object -w --no-filters / mktree / commit-tree on a bare cache, with pinned -c settings, removes all four; refuse existing non-regular entries rather than normalising them.
