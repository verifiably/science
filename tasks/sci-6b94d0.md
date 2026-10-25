---
id: sci-6b94d0
title: README status example must name its required configuration
status: todo
priority: 3
size: xs
complexity: low
process: direct
created: 2026-10-25T16:10:40Z
updated: 2026-10-25T16:10:40Z
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
