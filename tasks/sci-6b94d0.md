---
id: sci-6b94d0
title: README status example must name its required configuration
status: done
priority: 3
size: xs
complexity: low
process: direct
owner: docs/guide-accuracy
created: 2026-10-25T16:10:40Z
updated: 2026-10-25T16:44:01Z
started: 2026-10-25T16:38:23Z
completed: 2026-10-25T16:44:01Z
closed: 2026-10-25T16:44:01Z
depends: []
tags: [docs]
source: sci-708cf1
agent: codex
origin: agent
---

curate-docs finding F2 at df22dd1 (review sci-708cf1). README.md presents uv run science status as printing the world after checkout installation, but neither supplies --config nor establishes SCIENCE_CONFIG. python/src/science/config.py:248-254 refuses when both are absent, and cli.py:main loads that configuration before dispatching status. Make the example name a configuration file and state how the reader supplies it, with a pointer to the applicable setup/configuration reference. Do not invent an implicit config search or change the CLI. Check the guidance against resolve_config_path/load_config and run the documented documentation gates. The curation pass did not execute the example or the dated linked walkthrough; this is a source-proven missing precondition under rubric criteria 8 and 9.

## Notes

- 2026-10-25T16:10:40Z (add): created
  provenance: {"harness_session":"codex:01a173cd-4c79-7471-99bd-ef2e7f4689d4","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
- 2026-10-25T16:38:23Z (main): started
  provenance: {"harness_session":"claude-code:3a1909a3-739d-4c3b-94a7-6da33a326219","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-25T16:38:31Z (docs/guide-accuracy): resumed
  provenance: {"harness_session":"claude-code:3a1909a3-739d-4c3b-94a7-6da33a326219","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-25T16:44:01Z (docs/guide-accuracy): done
  provenance: {"harness_session":"claude-code:3a1909a3-739d-4c3b-94a7-6da33a326219","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-25T16:44:01Z (docs/guide-accuracy): README status example passes --config and states the --config/SCIENCE_CONFIG requirement (no cwd discovery; build and adapters exempt), pointing to framework design §9.1 and the mm30 record §3.1; checked against resolve_config_path and cli.py (16ca62d)
  provenance: {"harness_session":"claude-code:3a1909a3-739d-4c3b-94a7-6da33a326219","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
