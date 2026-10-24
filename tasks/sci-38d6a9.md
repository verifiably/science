---
id: sci-38d6a9
title: "Orient the README to a newcomer: say what the commands replace in an ad-hoc analysis and how a session runs"
status: doing
priority: 2
size: s
complexity: mid
process: direct
owner: main
created: 2026-10-24T18:10:19Z
updated: 2026-10-24T18:10:59Z
started: 2026-10-24T18:10:59Z
depends: []
tags: [docs]
source: vdocs-e4318e
agent: claude-code
---

Follow-on to the second guided tour's finding (vdocs-e4318e; atoms-dd5a5e and the beliefs piece are its siblings). The README abstract ('harness-neutral commands and skills over the beliefs kernel, served as a CLI and over MCP, with generated harness adapters, the derived work queue and publish') and Usage (the command list from tools/cli.toml) tell a newcomer what the layer is made of, not what it is for: a researcher or an agent who today works in a folder of scripts, notebooks and result tables, and would use these commands instead. Rewrite the identity.toml abstract against that status quo, and open Usage with what a session does (the belief path from a stated question to a computed belief, each step a record) before the surface list, pointing to the mm30 walk in docs/records/2026-09-23-mm30-through-the-commands.md as the worked example. Keep the project's history (the predecessor's 253 commands) in the command framework design.

## Notes

- 2026-10-24T18:10:59Z (main): started
  provenance: {"harness_session":"claude-code:0e2eed92-cf40-40a1-aac6-b06ac9f3c1ce","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
