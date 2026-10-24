---
id: sci-38d6a9
title: "Orient the README to a newcomer: say what the commands replace in an ad-hoc analysis and how a session runs"
status: done
priority: 2
size: s
complexity: mid
process: direct
owner: docs/38d6a9-newcomer-readme
created: 2026-10-24T18:10:19Z
updated: 2026-10-24T18:44:10Z
started: 2026-10-24T18:10:59Z
completed: 2026-10-24T18:44:10Z
closed: 2026-10-24T18:44:10Z
depends: []
tags: [docs]
source: vdocs-e4318e
agent: claude-code
---

Follow-on to the second guided tour's finding (vdocs-e4318e; atoms-dd5a5e and the beliefs piece are its siblings). The README abstract ('harness-neutral commands and skills over the beliefs kernel, served as a CLI and over MCP, with generated harness adapters, the derived work queue and publish') and Usage (the command list from tools/cli.toml) tell a newcomer what the layer is made of, not what it is for: a researcher or an agent who today works in a folder of scripts, notebooks and result tables, and would use these commands instead. Rewrite the identity.toml abstract against that status quo, and open Usage with what a session does (the belief path from a stated question to a computed belief, each step a record) before the surface list, pointing to the mm30 walk in docs/records/2026-09-23-mm30-through-the-commands.md as the worked example. Keep the project's history (the predecessor's 253 commands) in the command framework design.

## Notes

- 2026-10-24T18:10:59Z (main): started
  provenance: {"harness_session":"claude-code:0e2eed92-cf40-40a1-aac6-b06ac9f3c1ce","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-24T18:11:00Z (docs/38d6a9-newcomer-readme): resumed
  provenance: {"harness_session":"claude-code:0e2eed92-cf40-40a1-aac6-b06ac9f3c1ce","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-24T18:24:13Z (docs/38d6a9-newcomer-readme): baseline 2026-10-24 (just test, worktree .worktrees/38d6a9-newcomer-readme at 10144da): 858 passed, 106.07 s
- 2026-10-24T18:34:41Z (docs/38d6a9-newcomer-readme): review: impl round 1 — verdict: revise; findings: Important 3, Minor 5; reviewer: claude-code/claude-fable-5-1
- 2026-10-24T18:43:22Z (docs/38d6a9-newcomer-readme): review: impl round 2 — verdict: accept; findings: Minor 3; reviewer: claude-code/claude-fable-5-1
- 2026-10-24T18:44:10Z (docs/38d6a9-newcomer-readme): done
  provenance: {"harness_session":"claude-code:0e2eed92-cf40-40a1-aac6-b06ac9f3c1ce","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-24T18:44:10Z (docs/38d6a9-newcomer-readme): identity.toml abstract states what the commands replace in an ad hoc project; README Usage opens with the belief path a session follows, one command at a time in plain words, and Documentation leads with the mm30 record; two review rounds (revise, accept)
  provenance: {"harness_session":"claude-code:0e2eed92-cf40-40a1-aac6-b06ac9f3c1ce","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
