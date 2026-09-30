---
id: sci-9b20ea
title: "test_two_corpora: build the full two-corpus fixture once per module"
status: todo
priority: 3
size: s
complexity: low
process: direct
created: 2026-09-30T21:43:20Z
updated: 2026-09-30T22:07:29Z
depends: []
tags: [projects]
agent: claude-code/claude-opus-5-5
---

tests/test_two_corpora.py rebuilds a function-scoped fixture (claim → spec → run → assess → verify in both corpora) for each of its tests, about 185s per module; testmon selects it on any config.py edit, so test-fast pays it often. Build a module-scoped template world once and copytree it per test (check manifests/config embed no absolute paths first), and use the cheaper build_two_corpus_world fixture for the refusal tests that need no run/assess/verify.

## Notes

- 2026-09-30T21:43:20Z (coordination-part3): concerns: sci-923d3a extension — the two-corpus check's fixture costs ~185s per run
- 2026-09-30T22:07:29Z (main): Also: test_belief_answers_for_each_corpus_proposition_whatever_is_selected accepts Belief or NoBelief; pin each proposition's actual kind and reason while reworking the fixture.
