---
id: sci-b979ce
title: "Commons 1a: a decisive belief verdict flip needs a clean-environment verification fixture"
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-23T17:10:07Z
updated: 2026-10-24T10:22:10Z
depends: []
parent: sci-6b6014
tags: [commons]
source: sci-13050a
agent: claude-code
---

Why: commons 1a proves that accept selects the right inputs, but its minimal-policy original run cannot yield an admitting verification. Add one confined two-installation test so the same policy distinction also changes the returned belief. [ref:brief] records the checked evidence, fixture boundaries and the separation from the other deferred limits.

Established by source inspection at science 846772e: helpers.commons._add_a_evidence calls mint_fixture_run under MINIMAL_POLICY; the existing derived fixture's A verification is same-environment/passed and both policy settings return NoBelief. test_belief_path already demonstrates the real confined run/replay path reaching clean-environment/passed and Belief. No new two-installation confined case has been executed during this scope pass.

Done: add a confined variant of the existing two-installation path, using the supported fixture output. A's original run executes through science run with the normal confinement policy, then A publishes and B binds/adopts/reopens, fetches the mounted bytes and verifies A's assessment. Assert the stored verification is clean-environment/passed, with no other admitted assessment masking the contrast. For the same proposition and current epoch, accept=[] excludes A's assessment and its dependent verification and returns NoBelief; accept=[A] includes them and returns Belief with the independently expected supported value. Check the acceptance context and gathered identities as well as the answer. Do not fabricate scope, patch admission, or turn the portable fixture into the confined one.

Keep the existing portable input/context test. Follow test_belief_path's explicit host_prerequisites skip for the added confined case; a skipped case is not evidence that the new acceptance check passed. Record at least one actual confined pass before closing. Reuse snapshot and commons helpers and preserve their isolated subprocess/Git environments.

Verification: just test-one tests/test_commons_1a.py tests/test_belief_path.py, then just test-fast before committing. Report test counts and whether the confined case executed. Scope is the fixture and acceptance proof; no production belief-policy or verification-semantics change.

Where: python/tests/test_commons_1a.py, python/tests/helpers/commons.py, python/tests/helpers/world.py (mint_fixture_run, fixture_bundle, walk_belief_path), python/tests/conftest.py and python/tests/test_belief_path.py. Existing spec: docs/specs/2026-09-30-science-commons-design.md section 12; original ledger: tasks/files/sci-13050a/sdd-ledger-commons-1a.md Task 12.

## Original capture

test_commons_1a's belief case asserts inclusion and exclusion of A's assessment in the belief inputs and context under accept=[] and accept=[A], which spec §12 1a asks for, but the answer is NoBelief no-eligible-assessment under both: B's verification of A's assessment is same-environment because A's run is minted under the minimal policy by the portable fixture, and the kernel admits only clean-environment passes. A fixture that mints A's run through run under confinement would let the test show the verdict change too.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-commons-1a-follow-ups-brief.md — evidence, boundaries and wake conditions for the commons follow-ups

## Notes

- 2026-10-24T10:22:10Z (main): scope: scoped; at 846772e the portable commons run uses MINIMAL_POLICY, while test_belief_path establishes a real confined run/replay pattern. Settled a confined two-installation acceptance-verdict check, preserving portable coverage and requiring an actual confined pass; priority 2, size s, complexity mid, process direct; brief: docs/notes/2026-10-24-commons-1a-follow-ups-brief.md
