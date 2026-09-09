---
id: sci-66b26d
title: "Sub-project 4: the dogfood command set over a reproduced mm30 corpus"
status: blocked
priority: 1
size: xl
created: 2026-09-09T12:12:00Z
updated: 2026-09-09T15:44:53Z
depends: [beliefs-e5ab34, beliefs-5fe2e3, beliefs-2d9a55]
tags: [dogfood, command-framework]
spec: docs/specs/2026-09-09-belief-path-commands-design.md
plan: docs/plans/2026-09-09-belief-path-commands.md
---

Item 4 of the user/autonomy layer design §8 and the stack's one success criterion: a coding-agent session over a beliefs world holding a reproduced mm30 corpus, where next ranks a proposition, run executes a real analysis under confinement, verify reaches clean-environment, and assess admits the result to a computed belief, every step a governed record. §5.1 names the set: status, next, project, question, hypothesis, claim, dataset, run, verify, assess, task, decide (publish is sub-project 5's). Its precursors are met: items 1, 2 and 3 are complete; the run-confinement and workflow-surface lanes discharged; the five findings the mm30 reproduction record filed (beliefs-754995 and children) are done. The reproduction driver under beliefs python/tools/reproduction is the instrument the commands are written from, not promoted. Brainstorm opened 2026-09-09; spec to follow.

## Notes

- 2026-09-09T12:14:04Z (dogfood-commands): Brainstorm ruling 2026-09-09: two specs. The belief path first (next, claim, dataset, run, verify, assess), meeting the success criterion with commands that each have a measured precursor in the reproduction driver; the coordination set (project, question, hypothesis, task, decide) is its own spec afterward.
- 2026-09-09T12:24:24Z (dogfood-commands): Brainstorm ruling: the belief path is measured by reproducing mm30 afresh through the commands from an empty adopted corpus; the 2026-09-05 reproduction record's corpus is the oracle (same proposition, dataset digest, frozen spec identity; belief past no-eligible-assessment). Fixture worlds carry the unit tests.
- 2026-09-09T12:26:01Z (dogfood-commands): Brainstorm ruling: a separate spec command (mints:analysis-spec) freezes the analysis spec from the draft fields and a workflow definition; run takes a spec ref and a dataset ref and only executes under confinement. The list is on the order of a dozen, not closed.
- 2026-09-09T12:31:05Z (dogfood-commands): Brainstorm ruling: rule implementations live in the kernel. beliefs ships reference implementations of the outcome-file interpretation rule and content-identity equality keyed by rule identity, beside science.belief.v1/reference; the surface looks rules up by identity and defines none. Command order on the path is run, assess, verify (verification publication needs the assessment ref); belief is computed at read time.
- 2026-09-09T12:35:07Z (dogfood-commands): Brainstorm ruling: corpus-local contract documents are named by a contracts config key beside domains, parsed against the shipped base and compiled into the profile; the manifest pin check at session open keeps them honest. Stated in the spec as superseded whenever the kernel gives contracts a home.
- 2026-09-09T12:54:17Z (dogfood-commands): Spec review round 1 (six findings, all verified): claim validates membership through decode_claim with a stricter surface policy for bound sorts, so the vocabulary dataset precedes claim; dataset locations are content-derived with standing supersession; a dispatcher amendment (§6.3) closes surface refusals from write handlers; next joins inputs through targeting specs and class 4 is admit; spec is deterministic-only; the claim-identity oracle is the 2026-09-08 value 780ace59.
- 2026-09-09T13:08:43Z (dogfood-commands): Spec review round 2: the mandatory-consultation policy is restricted to dataset-identity bindings; namespace/release bindings (the pack's HGNC molecular-entity) keep the kernel's permissive not-consulted; decode call is decode_claim(WireClaim(**project_claim(claim)), ...).
- 2026-09-09T13:46:33Z (dogfood-commands): Plan review round 1 (eight findings, all verified): holdings reads go through the kernel's held reducer (derive_holdings + dataset_observations; fixtures and the operator recipe install the binding); run/verify raise KernelRefusalValue for RunRefused; dataset validates the record and facets before its first act; the full-path test admits only under confinement and asserts non-admission under the minimal policy; contract fixtures use the authored dataset:<id> syntax; null polarities preserved; helpers moved to Task 3; every command tested through its transport.
- 2026-09-09T14:08:33Z (dogfood-commands): Plan review round 2 (six findings, all verified): holdings reads use detached inspection and a test proves a read writes nothing; dataset validates every facet payload plus bearer/validity before the first act; held paths match the configured store's identity; MCP replay tested within one serve lifetime; Task 11 depends on Task 6; spec, run, assess and verify each driven through a real transport, with the spec's §7 bullet corrected.
- 2026-09-09T15:44:53Z (dogfood-commands): Tasks 1–2 (sci-614bdd, sci-05c56c) landed on branch dogfood-commands (7d738d9, 6ddd6eb, 4cc7ddd). Everything from Task 3 waits on the beliefs kernel: beliefs-2d9a55 (store_identity, xs) unblocks Task 3 and then Tasks 5 and 10; beliefs-5fe2e3 (scoped run/holdings routes) unblocks Tasks 4, 7, 9; beliefs-e5ab34 (reference rules) unblocks Tasks 6, 8. Pick up again with 'tasks ready' once beliefs-2d9a55 closes; the branch is rebased on main after quick-wins merged.
