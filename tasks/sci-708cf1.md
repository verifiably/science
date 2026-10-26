---
id: sci-708cf1
title: Documentation review
status: todo
priority: 3
size: s
complexity: low
process: direct
created: 2026-10-24T12:49:50Z
updated: 2026-10-26T15:11:54Z
depends: []
tags: [docs]
source: curate-docs
agent: codex
---

The reusable record of curate-docs passes over this project: one note per pass naming the rubric version, commit, documents covered, exclusions and findings by verdict; resolution of findings is recorded apart from the review. Never closed by a pass; ops owns its lifecycle.

## Notes

- 2026-10-24T12:49:53Z (main): doc-review: eligible since 2026-10-24: baseline
- 2026-10-24T18:56:25Z (main): Raised to P1 and undeferred on 2026-10-24 at the owner's request: first-pass documentation reviews of active projects run now rather than three a week under the doc-review cap. Run /curate-docs in this project's checkout; the next doc-review run acknowledges the pass as volunteered.
- 2026-10-25T16:09:52Z (main): curate-docs: rubric v2; commit df22dd1; mechanical: ops-docs 0, ops-check 0 (also 0 after refined commit 44252d1); covered: identity.toml (whole), README.md (whole), AGENTS.md (whole), docs/specs/2026-08-31-command-framework-design.md (authority) sections: head and status lines 1-26 (criterion 2 only); excluded: docs/specs/: dated decision records except authority head/status, docs/plans/: implementation plans, docs/notes/: dated briefs, docs/records/2026-09-23-mm30-through-the-commands.md and docs/records/2026-10-12-pi-attended-probe.md: dated records (including README-linked walkthrough), tools/: vendored tree including tools/README.md; keep: 1 (purpose and abstract distinct), 2 (authority names implementation 2026-09-09 and amendment 2026-10-01; newest done task naming it is sci-fd792c 2026-09-09, no newest-done fallback), 5 (baseline: corpus-write boundary cites named authority and scoped-permit history sci-c3f0bb; CLI drift prevented by conformance introduced for sci-1ef4b8 at 628b1d6; the overbroad write claim is finding F3 under 9), 7 (setup, gates and layout projections agree), 11 (no subsystems declared; only nested README is excluded tools/README.md); not judged: 6: retired in v2; budget checked mechanically, 10: no eligible current-behaviour reference documents; no unread eligible ranges or self-dates (0 of 800 reference lines); refined: README.md (3): removed unpublished-state aside while preserving checkout installation guidance, AGENTS.md (3): removed historical 80-second/8-worker measurement, AGENTS.md (4): deleted duplicated global tt-report reminder (2 lines saved); stale: README.md (8,9) F1: purported command surface omits publish, publish-preview, provider-inspect, provider-bind, adopt, fetch and show although all seven appear in tools/cli.toml, commands/ and the parser (commons landed c8a2cd7); README.md (8,9) F2: status example supplies neither --config nor SCIENCE_CONFIG, while config.py:248-254 refuses without one and main loads it for status; identity.toml, README.md and AGENTS.md (9) F3: every-write-is-a-corpus-record/no-storage claims contradict session-class selection and sharing-class ledger lines plus science-owned provider/pin JSON (dispatch.py:_invoke_sharing, commands/provider_bind.py:handle, sharing.py:SharingRegistry); unresolved: 3
- 2026-10-25T16:11:30Z (main): curate-docs: resolution; README.md F1: omitted seven shipped commons commands -> sci-221a57 (filed); README.md F2: missing configuration precondition in status example -> sci-6b94d0 (filed); identity.toml, README.md and AGENTS.md F3: overbroad corpus-write/no-storage guarantee -> sci-966868 (filed; first note records concerns: sci-38d6a9 defect); decision: 0 awaiting the human; refinements: 44252d1 merged locally into main (publication-state aside and historical test timing removed; duplicated global tt-report reminder deleted, 2 lines saved); verification: ops-docs 0 and ops-check 0 before/after edits, tasks check 0 and normal pre-commit hook 0; no examples or tests run under curate-docs bounds, including no worktree baseline or test-fast (the README filename in test_front_door.py is a synthetic staged-path case, not README content read as input); cleanup: no ignored entries, no new plan ledger, inherited tracked reports remain identical in main, no checked launcher/service/config pointer into the temporary tree, tt-report completed, .worktrees/curate-docs-708cf1 and its merged branch removed; no scratch or off-tree evidence retained, no push, host-load reported nothing left running; reusable review task status/priority/body unchanged and all three finding tasks remain open for a future implementing agent.
