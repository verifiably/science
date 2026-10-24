---
id: sci-d798cf
title: "python/uv.lock is stale against pyproject: every uv run rewrites it (revision 3 to 5, adds the pytest-xdist specifier)"
status: todo
priority: 3
size: xs
complexity: low
process: direct
created: 2026-10-24T18:28:19Z
updated: 2026-10-24T18:28:19Z
depends: []
tags: [tooling]
agent: claude-code
---

Seen 2026-10-24 in a fresh worktree at 10144da: 'just test' and 'just test-fast' (both 'uv run' without --frozen) left python/uv.lock modified: 'revision = 3' became 5 and 'requires-dist' gained '{ name = "pytest-xdist", specifier = ">=3.6" }'. The committed lock predates the pytest-xdist dependency in pyproject, so every run dirties the tree and a docs-only commit has to revert the lock by hand. Done when 'uv lock' is committed once and the recipes run '--frozen' (as atoms' and beliefs' do) so a stale lock fails rather than rewrites.
