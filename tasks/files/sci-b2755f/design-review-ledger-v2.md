# Assumption-sweep design review ledger

Task: sci-b2755f

## Round 1

- Artifact: `docs/specs/2026-10-30-assumption-sweep-design.md`.
- Repository: science; branch: `feat/sci-b2755f-assumption-sweep`.
- Frozen revision: `af4b359e88f2a51368c6eac711516f550136cc26`.
- Reviewer: codex/gpt-6.1-sol; fresh builder check, read-only.
- Verdict: accept; Important 0, Minor 0.
- Full review: task attachment `builder-check-round-1-report.md`.
- Rulings: none required; no findings to dispose.
- Minor (deferred): none.

## Round 2

- Artifact and frozen revision: same as round 1.
- Reviewer: claude-code/claude-fable-5-1; full review supplied by the user.
- Verdict: revise; Important 1, Minor 3.
- Full review: task attachment `spec-round-2-report.md`.
- Review note recorded before revision work.

Ruling: accept the Important screening-procedure finding; retain mm's existing
exposure definition with no exemption for an unmapped results-bearing abstract.
Use PMID/DOI matching, section-only metadata to resolve mappings, and source-local
skips while screening continues. Why: the mm ledger's section 1 and dated abstract
and search-summary entries already classify these result reads as exposure; no
policy amendment is needed to fix the screening order. Cost: readable coverage
may shrink; a section-isolation failure can cause unintended exposure that must
be recorded and routed through mm's workflow. Revisions: finding against
`af4b359e88f2a51368c6eac711516f550136cc26`; correction in
`c2f3a885d622fe97f21ec34ddd3eb1a9a2506dd6`, sections 4–5 and rehearsal in section 8.

Minor 1 resolved: section 8 explicitly makes the rehearsal a manual dry run,
judged by a fresh reviewer, with plain-document fixtures under
`python/tests/fixtures/sweep-assumptions/`. Automated adapter checks establish
packaging, not scientific judgment. Synthetic reliance cycles are not world records.

Minor 2 resolved: section 5 requires a self-contained, versioned inventory
attachment and SHA-256 before phase B; inspectability no longer depends on a
host-local path.

Minor 3 resolved: section 8 states a minimal authored-skill convention, with a
bounded reconciliation rule if sci-cc4fb9 lands a documented convention first.

All three corrections are in `c2f3a885d622fe97f21ec34ddd3eb1a9a2506dd6`.
Minor (deferred): none.

## Round 3

- Frozen revision: `c2f3a885d622fe97f21ec34ddd3eb1a9a2506dd6`.
- Reviewer: codex/gpt-6.1-sol, runtime identity verified by reviewer.
- Scope: round-2 fixes and consequential gaps, including multiple cohorts and
  retrieval boundaries; read-only.
- Verdict: accept; Critical 0, Important 0, Minor 0.
- Full review: task attachment `spec-round-3-report.md`.
- No residual question requires another design revision; no further rulings.
- Minor (deferred): none.

The round-1 builder check and round-3 scoped check cover design readiness. The
round-3 phrase about a remaining builder check does not identify an additional
finding or unanswered question; no duplicate builder check is required. User
approval of the revised frozen artifact remains the design gate before planning.

## Verification and next step

`just check` and `git diff --check` passed for revision 2; its documentation
pre-commit hook passed. mm's unchanged revision
`a7250080ffa99369884eec670c42a21380482b6f` was checked for the policy language,
abstract-exposure entries and roster counts (1559 entries, 830 publication PMID,
100 DOI; counts overlap). No runtime tests, retrieval rehearsal or pilot ran.

After user approval of the revised design, the agent drafts the implementation
plan in the retained worktree for its separate review. No skill implementation
or pilot starts at this gate.
