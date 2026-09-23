---
id: sci-3a01b3
title: Contract documents silently ignore unknown top-level keys
status: todo
priority: 3
size: xs
complexity: low
process: direct
created: 2026-09-23T20:57:16Z
updated: 2026-09-23T20:57:24Z
depends: []
tags: [command-framework]
agent: claude-code/claude-opus-5-5
---

science.contracts.load_contract_document reads `contract` and `plan` and ignores every other top-level key. The kernel driver's mm30.yaml carries `also: [biology]`, which the loader drops without a word (found 2026-09-23 in the mm30 measurement, docs/records/2026-09-23-mm30-through-the-commands.md §5); the config's `domains` supplied biology, so nothing broke, but a misspelled `plan` key would load a document with no plan and surface only later as claim's 'no plan' refusal. Refuse invalid-input on any top-level key outside {contract, plan}, or name the ignored ones explicitly.
