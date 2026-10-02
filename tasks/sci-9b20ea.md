---
id: sci-9b20ea
title: "test_two_corpora: build the full two-corpus fixture once per module"
status: done
priority: 3
size: s
complexity: low
process: direct
owner: test-latency
created: 2026-09-30T21:43:20Z
updated: 2026-10-02T12:55:46Z
started: 2026-10-02T10:29:05Z
completed: 2026-10-02T10:34:41Z
depends: []
tags: [projects]
model: claude-opus-5-5
agent: claude-code/claude-opus-5-5
---

tests/test_two_corpora.py rebuilds a function-scoped fixture (claim → spec → run → assess → verify in both corpora) for each of its tests, about 185s per module; testmon selects it on any config.py edit, so test-fast pays it often. Build a module-scoped template world once and copytree it per test (check manifests/config embed no absolute paths first), and use the cheaper build_two_corpus_world fixture for the refusal tests that need no run/assess/verify.

## Notes

- 2026-09-30T21:43:20Z (coordination-part3): concerns: sci-923d3a extension — the two-corpus check's fixture costs ~185s per run
- 2026-09-30T22:07:29Z (main): Also: test_belief_answers_for_each_corpus_proposition_whatever_is_selected accepts Belief or NoBelief; pin each proposition's actual kind and reason while reworking the fixture.
- 2026-10-02T09:06:09Z (test-latency): absorbed by sci-5937be (world fixture snapshots spec); closes with the test_two_corpora conversion
- 2026-10-02T10:29:05Z (test-latency): started
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T10:29:05Z (test-latency): halt override: started past sci-5937be by fdd0a33b-81b7-41f1-82a2-bf45de0a4198: absorbed by the halt's own remedy (spec §7); closed in sci-16a04d's commit
- 2026-10-02T10:34:41Z (test-latency): done
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T10:34:41Z (test-latency): test_two_corpora restores a walked snapshot and a cheaper two-corpus snapshot for refusals; belief test pinned to NoBelief/no-eligible-assessment (sci-5937be)
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T12:55:46Z (test-latency): correction: the pin claimed at close had not landed (the edit sat behind a halted tasks start in an && chain); landed in the final-review fix commit, verified passing and failing on a wrong expected value
