---
id: sci-bd518f
title: Rewrite t@t commit authorship in this repository
status: done
priority: 2
size: s
complexity: low
process: direct
owner: main
created: 2026-10-16T16:33:09Z
updated: 2026-10-17T00:53:11Z
started: 2026-10-17T00:46:07Z
completed: 2026-10-17T00:53:11Z
depends: [ops-e5b39c]
tags: []
source: git-identity-leak-2026-10-07
agent: claude-code/claude-opus-5-5
---

Rewrite this repository's t <t@t> commits (from the 2026-10-07 global-config leak; see ops-5749d9) to Keith Hughitt <keith.hughitt@gmail.com>, following the runbook ops-e5b39c. Inventory on titan 2026-10-16: 124 t@t commits on all refs, 41 unpushed on main, 2 worktree(s); remote: verifiably/science.

## Notes

- 2026-10-17T00:46:07Z (main): started
  provenance: {"harness_session":"claude-code:c6863573-34c2-470d-b394-259f7cc75503","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-17T00:46:07Z (main): halt override: started past sci-5937be by c6863573-34c2-470d-b394-259f7cc75503: its test-fast run is the halt's third verify run
- 2026-10-17T00:46:08Z (main): Direct history maintenance under ops-e5b39c's pilot procedure (as relay-653378). No agent session in sci on Titan or Europa; Europa has only the main checkout. Inventory: 441 commits, 124 t@t, all on main (origin/main reaches 83, pushed); coordination-part2 (worktree on Titan WORK_ROOT, locked, clean) is merged and predates the window (unchanged). No tags, stash, signatures, extra headers, repo-local user.*, or .git-blame-ignore-revs. Remote verifiably/science (unprotected) main c28cdbdf808587c5afbfb2ff357fa6d610a0e753 (lease). Started past the sci-5937be halt as its park invites; this task's test-fast is offered as that halt's verify run. Steps: bundle --all; mirror; filter-repo --mailmap; byte-verify; citation check; guarded update-ref transaction; attach map; test-fast; push main --force-with-lease.
- 2026-10-17T00:46:30Z (main): attached: 2026-10-16-identity-commit-map.txt (10496 bytes): Authorship rewrite map: 128 changed commit IDs (old new); resolves historical SHA references in task notes and docs without editing them
- 2026-10-17T00:53:11Z (main): done
  provenance: {"harness_session":"claude-code:c6863573-34c2-470d-b394-259f7cc75503","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-17T00:53:11Z (main): Rewrote 124 t@t commits to Keith Hughitt (248 identity lines, 128 hashes changed) in one filter-repo pass in a mirror outside Dropbox; verified all 443 commits byte-for-byte (only mapped parents and identities differ; no message SHAs; every tree preserved). Swapped main in one guarded update-ref transaction; coordination-part2 (merged, pre-window) unchanged. Rewritten SHAs cited in tracked files are prose in task notes and one record; map attached (tasks/files/sci-bd518f/2026-10-16-identity-commit-map.txt). just test-fast selected nothing (testmon, unchanged tree); just test green (694 passed). tt-latency verify then met the sci-5937be halt, closed with its output. Pushed main with lease c28cdbd -> 656ff27 (verifiably/science, unprotected). A fresh remote mirror, Titan and Europa show 0 t@t; Europa fsck clean once synced. Forced only past ops-e5b39c, whose pilot procedure was followed. Artifacts on Titan at WORK_ROOT/science/identity-rewrite-20261017T004609Z.
  provenance: {"harness_session":"claude-code:c6863573-34c2-470d-b394-259f7cc75503","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
