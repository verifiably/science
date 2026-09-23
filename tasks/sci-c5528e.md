---
id: sci-c5528e
title: "Coordination command set: design spec (second half of sub-project 4)"
status: todo
priority: 1
size: l
complexity: high
process: planned
defer: 2026-10-23
created: 2026-09-23T11:40:35Z
updated: 2026-09-23T12:03:55Z
depends: []
tags: [projects]
agent: claude-code/claude-fable-5-1
---

The belief path design (dogfood-commands branch, docs/specs/2026-09-09-belief-path-commands-design.md) defers project, question, hypothesis, task and decide to their own spec, written after the belief path measurement. That spec inherits the projects design (docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md) §5 and §7 and carries guarantees P1, P2, P4, P5 and P8: project genesis needs no selection; subordinate view and coordination kinds refuse no-current-project without one; project select rewrites the session's selection and appends a ledger entry; reads resolve selection from an explicit --project, else the live session over service_socket (science mcp serve binds it for this query), else default_project; the same-query mint. Also folds in sci-17851d (coordination profile wired at session open) and the default_project and write_root config keys. Depends on the belief path measurement landing.

## Notes

- 2026-09-23T12:03:55Z (projects-spec): From the branch review 2026-09-23, four items this spec carries: (1) P1 gap: relative paths inside SCIENCE_CONFIG resolve against the process cwd (load_config; pinned by test_load_config_resolves_relative_operations_root and test_service_socket_is_configurable_and_resolved), so one config can name different worlds from different directories; resolve them against the config file's directory or refuse them, and update those two tests. (2) The preamble says 'no project can be selected yet' and test_preamble_states_the_selected_project_rule asserts that sentence: when selection lands, amend both, and widen 'a question or task' to 'a question or any coordination record'. (3) Extend the P1 test from resolve_config_path/load_config to session open in cli.py, serve.py and mcp.py. (4) Amend the belief path design's next ('from the current view') to take the projects design §5 by reference. Blocked on the belief path measurement (sci-030658, dogfood-commands branch); the dep is wired when that record reaches main.
- 2026-09-23T12:03:55Z (projects-spec): Deferred 30d so the picker does not offer it before sci-030658 lands; start spends the deferral.
