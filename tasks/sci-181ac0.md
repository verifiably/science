---
id: sci-181ac0
title: "test_config: '3' is a shipped coordination version now; pick an unshipped one"
status: done
priority: 1
size: xs
complexity: low
process: direct
owner: transports-floor
created: 2026-10-02T20:34:26Z
updated: 2026-10-02T20:34:33Z
started: 2026-10-02T20:34:26Z
completed: 2026-10-02T20:34:33Z
depends: []
tags: [testing]
model: claude-opus-5-5
agent: claude-code/claude-opus-5-5
---

beliefs 454fc55 ships coordination contract v3, so test_coordination_value_outside_its_forms_is_refused[3] no longer refuses. Use 4, the first unshipped version.

## Notes

- 2026-10-02T20:34:26Z (transports-floor): started
  provenance: {"harness_session":"claude-code:54e3b78d-e88d-4e32-8d7d-a54e5a20e916","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T20:34:26Z (transports-floor): halt override: started past sci-5937be by 54e3b78d-e88d-4e32-8d7d-a54e5a20e916: fails the suite on main since beliefs shipped coordination v3; blocks a green merge of the halt's follow-up
- 2026-10-02T20:34:33Z (transports-floor): done
  provenance: {"harness_session":"claude-code:54e3b78d-e88d-4e32-8d7d-a54e5a20e916","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T20:34:33Z (transports-floor): parametrize on 4, the first coordination version beliefs does not ship
  provenance: {"harness_session":"claude-code:54e3b78d-e88d-4e32-8d7d-a54e5a20e916","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
