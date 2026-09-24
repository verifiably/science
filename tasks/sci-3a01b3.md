---
id: sci-3a01b3
title: Contract documents silently ignore unknown top-level keys
status: done
priority: 3
size: xs
complexity: low
process: direct
owner: main
created: 2026-09-23T20:57:16Z
updated: 2026-09-24T09:38:01Z
started: 2026-09-24T09:33:27Z
completed: 2026-09-24T09:38:01Z
depends: []
tags: [command-framework]
agent: claude-code/claude-opus-5-5
---

science.contracts.load_contract_document reads `contract` and `plan` and ignores every other top-level key. The kernel driver's mm30.yaml carries `also: [biology]`, which the loader drops without a word (found 2026-09-23 in the mm30 measurement, docs/records/2026-09-23-mm30-through-the-commands.md §5); the config's `domains` supplied biology, so nothing broke, but a misspelled `plan` key would load a document with no plan and surface only later as claim's 'no plan' refusal. Refuse invalid-input on any top-level key outside {contract, plan}, or name the ignored ones explicitly.

## Notes

- 2026-09-24T09:33:27Z (main): started
  provenance: {"harness_session":"claude-code:dde7b5c4-c65b-4f4c-9ec0-bc965ee48ee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-24T09:38:01Z (contract-keys): done
  provenance: {"harness_session":"claude-code:dde7b5c4-c65b-4f4c-9ec0-bc965ee48ee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-24T09:38:01Z (contract-keys): load_contract_document refuses invalid-input on any top-level key outside {contract, plan}, naming the keys and pointing at the config's domains; test_unknown_top_level_key_refuses
  provenance: {"harness_session":"claude-code:dde7b5c4-c65b-4f4c-9ec0-bc965ee48ee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
