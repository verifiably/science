---
id: sci-eb808f
title: "Git transport: commit through plumbing on a bare cache instead of a checked-out working tree"
status: todo
priority: 2
size: m
complexity: mid
process: direct
created: 2026-10-23T18:45:05Z
updated: 2026-10-24T11:33:33Z
depends: []
tags: [commons]
source: sci-13050a
agent: claude-code
---

Deferred from the commons 1a final review (ledger attached to sci-13050a: Final M3, M6, and the two fix-round minors). science/transport_git.py checks the remote's tree out into a cache working tree, so (1) the user's global git config and the remote's .gitattributes apply at add/commit (commit.gpgsign can block in the dispatcher lock; core.autocrlf, filter=lfs, text/eol can alter blobs), (2) a remote that plants <cid>.head-artifact.v1 as a symlink entry makes our push keep mode 120000 for the head artifact (our cat-file readers and the kernel listing are unaffected, but a third-party checkout dangles, and an idempotent re-push never repairs it), (3) a plain file left at <cid> after a deleted branch makes every later push refuse 'not a directory', and (4) the cache has no lock, so read-only provider-inspect can reset it under a concurrent publish. Committing with hash-object -w --no-filters / mktree / commit-tree on a bare cache, with pinned -c settings, removes all four; refuse existing non-regular entries rather than normalising them.

Established at science 99111f7 (commons 1a merged at c8a2cd7): _sync still initializes a non-bare clone, resets origin/main into its working tree and mutates shared tracking refs; _stage writes files and git-adds them; push uses git commit. The symlink escape was already fixed at 9160284 by core.symlinks=false and _target containment/lstat checks. This task replaces the remaining checkout/configuration and cache-race exposure; it must retain that protection. See [ref:commons] §8 and [ref:review-ledger] Final M3/M6 and the two fix-round minors.

Done: use bare-cache object plumbing with hash-object --no-filters, explicit regular-file tree entries and commit-tree, preserving unrelated remote entries and rejecting existing non-regular publication entries rather than repairing their mode. Preserve git's authentication configuration while pinning the settings that affect generated content/commits; leave the host's config untouched. Serialize shared-cache mutation across transport instances/processes, including first initialization, and resolve each read to one immutable fetched commit so listing/fetch cannot mix versions during a concurrent publish. Keep idempotence, the bounded rejected-push retry, recovery after a deleted remote branch, and the before-commit/after-push fault seams. Test hostile modes, inherited signing/hooks/filter/eol settings, stale cache debris after branch deletion, and concurrent inspection/publishing with deterministic coordination.

Where: python/src/science/transport_git.py; its public callers in publication.py (transport_for, download, inspect) and publish.py; python/tests/test_transport_git.py and helpers/commons.py. Adapt private _stage/_run test seams if needed; retain the existing public transport interface. Git fixtures must use an explicit isolated environment and verify their repository before writes. Run just test-one tests/test_transport_git.py tests/test_cmd_publish.py tests/test_cmd_adopt.py tests/test_cmd_provider.py, then just test-fast. No new transport backend or general authentication layer.

## References

- commons (input, required, kind=spec): docs/specs/2026-09-30-science-commons-design.md — governing identity, transport, acceptance and recovery contract
- review-ledger (context, kind=ledger): tasks/files/sci-13050a/sdd-ledger-commons-1a.md — original findings and retained rulings

## Notes

- 2026-10-24T11:33:33Z (main): scope: rescoped; checked at 99111f7 against transport_git.py, commons spec §8 and the sci-13050a ledger; recorded the existing 9160284 symlink protection, bounded bare-cache conversion and immutable-read/cache-serialization checks; priority 2 unchanged; medium, mid, direct.
