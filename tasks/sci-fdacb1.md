---
id: sci-fdacb1
title: Adopt the verifiably README template (rollout 2)
status: done
priority: 2
size: m
complexity: low
process: direct
owner: docs/readme-template
created: 2026-10-09T23:22:18Z
updated: 2026-10-10T11:55:11Z
started: 2026-10-10T11:46:37Z
completed: 2026-10-10T11:55:09Z
depends: [sci-a2c91b]
tags: [docs]
agent: claude-code/claude-fable-5-1
---

Adopt the verifiably family README template as verifiably/docs docs/plans/2026-10-09-readme-template.md, section 'Rollout 2: science', specifies: tools, identity.toml, both guides, the family copy, Usage from tools/cli.toml, the defect fixes. Absorbs sci-edc546. Spec: verifiably/docs docs/specs/2026-10-09-readme-template-design.md.

## Notes

- 2026-10-10T11:46:37Z (main): started
  provenance: {"harness_session":"claude-code:f9d782b7-b57a-4662-be5f-eb7f97c62796","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T11:46:37Z (main): halt override: started past sci-5937be by f9d782b7-b57a-4662-be5f-eb7f97c62796: README/AGENTS docs, identity.toml and ops-docs in check_cmd; touches no tests or package code, cannot affect test-fast latency
- 2026-10-10T11:46:46Z (docs/readme-template): resumed
  provenance: {"harness_session":"claude-code:f9d782b7-b57a-4662-be5f-eb7f97c62796","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T11:55:09Z (docs/readme-template): test-fast: 694 passed in 404 s (fresh worktree, testmon ran the whole suite); review focus 1 pinned: name = sci gives 'tools/family.toml: does not list this project (sci)' exit 1, restored exit 0
- 2026-10-10T11:55:09Z (docs/readme-template): beyond the plan: justfile gains a docs recipe (ops-docs check's refusal says 'run just docs'), the check_cmd comment and the AGENTS pre-commit bullet name ops-docs, README Layout drops skills/ (untracked, empty)
- 2026-10-10T11:55:09Z (docs/readme-template): done
  provenance: {"harness_session":"claude-code:f9d782b7-b57a-4662-be5f-eb7f97c62796","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T11:55:09Z (docs/readme-template): verifiably README template adopted: vendored ops-docs v3, tools/family.toml, identity.toml, README in template order with identity and family regions, AGENTS.md Setup/Gates/Layout/Rules, check_cmd runs ops-docs check, just docs recipe
  provenance: {"harness_session":"claude-code:f9d782b7-b57a-4662-be5f-eb7f97c62796","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
