---
id: sci-551ba2
title: Refuse every writer-profile vs write-root pin mismatch by name
status: todo
priority: 3
size: s
complexity: low
process: direct
created: 2026-09-30T22:07:29Z
updated: 2026-09-30T22:07:30Z
depends: []
tags: [projects]
agent: claude-code/claude-opus-5-5
---

require_write_root_pins (config.py) compares domain pins only: a base (science_contract) pin mismatch still reaches the kernel's bare ContractMismatch, which serve/mcp and sessionless reads print as internal-error. Extend the check to the base pin. Also: with coordination = false over a write root that pins coordination, the refusal should suggest setting coordination = <N>.

## Notes

- 2026-09-30T22:07:29Z (main): concerns: sci-923d3a extension — part 3's named pin refusal covers domain pins only
