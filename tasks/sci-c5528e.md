---
id: sci-c5528e
title: "Coordination command set: design spec (second half of sub-project 4)"
status: todo
priority: 1
size: l
complexity: high
process: planned
created: 2026-09-23T11:40:35Z
updated: 2026-09-23T11:40:35Z
depends: []
tags: [projects]
agent: claude-code/claude-fable-5-1
---

The belief path design (dogfood-commands branch, docs/specs/2026-09-09-belief-path-commands-design.md) defers project, question, hypothesis, task and decide to their own spec, written after the belief path measurement. That spec inherits the projects design (docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md) §5 and §7 and carries guarantees P1, P2, P4, P5 and P8: project genesis needs no selection; subordinate view and coordination kinds refuse no-current-project without one; project select rewrites the session's selection and appends a ledger entry; reads resolve selection from an explicit --project, else the live session over service_socket (science mcp serve binds it for this query), else default_project; the same-query mint. Also folds in sci-17851d (coordination profile wired at session open) and the default_project and write_root config keys. Depends on the belief path measurement landing.
