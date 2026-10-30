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

## Round 4 and planning transition

- Frozen reviewed spec: `c2f3a885d622fe97f21ec34ddd3eb1a9a2506dd6`.
- Reviewer: claude-code/claude-fable-5-1; user supplied the full review.
- Verdict: accept; Minor 1 (review-article navigation).
- Full report: `spec-round-4-report.md` attached to the task.
- Review note recorded before action. The user's acceptance and permitted
  one-line edit were taken as authorization to draft the implementation plan.

Ruling: resolve the navigation minor by retaining titles and addressable
reference lists fetched through section-only retrieval; never read a
results-bearing review body for navigation. Why: the original navigation wording
was ambiguous against the accepted exposure boundary. Cost: unavailable isolated
reference lists reduce survey coverage. Revisions: finding against `c2f3a88`;
clarification in `1ecfa34f33448dd86a148c8ba23e7523664847a1`, spec section 5.
The reviewer explicitly permitted this edit in the plan-drafting commit without
another spec-review round. Minor (deferred): none.

The accepted coverage cost is retained: discovery may lean on structural/design
metadata and already-exposed publications. No mm policy was changed or relaxed.

## Plan round 1 (self-review)

- Plan: `docs/plans/2026-10-30-assumption-sweep.md`.
- Frozen revision: `1ecfa34f33448dd86a148c8ba23e7523664847a1` (same revision as
  clarified spec).
- Reviewer: controller codex/gpt-6-astra, freshly verified with relay.
- Verdict: accept; no residual findings after the pre-commit self-review.
- Full report: `plan-round-1-report.md` attached to the task.
- This is self-review under writing-plans, not an independent review or human
  approval. No additional delegation was required for plan drafting.

The plan names three dependent deliverables: authored skill/package, complete
synthetic rehearsal, bounded mm pilot and final review. The first step is blocked
until user plan approval; its dependents cannot start early. Inline execution is
the default, with fresh workers only for required behavioral tests and reviews.

Current gate supersedes the previous design-review wait: user reviews frozen
plan `1ecfa34`; after approval the agent unblocks the first step and executes in
the retained worktree. No implementation, runtime tests or live retrieval ran
during planning. `just check`, whitespace validation and the documentation
pre-commit hook passed for the plan-drafting commit.

## Plan round 2 and human approval (round 3)

- Reviewed plan/spec revision: `1ecfa34f33448dd86a148c8ba23e7523664847a1`.
- Reviewer: claude-code/claude-fable-5-1; verdict accept, Minor 2.
- Full report and appended human approval: `plan-round-2-report.md`.
- Both round-2 review and round-3 human acceptance notes were recorded before
  acting on the approval. Keith approved after noting or fixing the minors and
  explicitly requested parking for a fresh inline execution session.

Ruling: fix Minor 1 by invoking `uv run quarry` from quarry's registered checkout
and recording that checkout's revision; do not select a PATH installation.
Why: no quarry was on PATH at approval, while the checkout environment exists
and its README declares this route. Cost: the pilot depends on that checkout
and environment remaining available; absence must be reported, not silently
replaced. Revisions: finding against `1ecfa34`; fixed in
`0f52b49f5b98fe6f10b8cc082de9142b46442cc9`. Observed quarry revision:
`7008433c8d3007b38a8fb08598e7e3ed49e965eb`; no quarry command or retrieval ran.

Ruling: fix Minor 2 by counting every deliberate primary-article full-text
retrieval attempt against 18, including failed access and retries; count
completed reads separately. Bibliographic and isolated-section reads are logged
under the screening bounds, not counted as full-text attempts. Why: this keeps
the execution budget finite and makes spec and plan agree. Cost: failures can
reduce the number of articles actually read and may prevent a three-candidate
result. Revisions: finding against `1ecfa34`; both documents aligned in
`0f52b49f5b98fe6f10b8cc082de9142b46442cc9`.

Minor (deferred): none. No further review round is required for these permitted
clarifications. The approved integration/cleanup step retains all existing
retained-item, review, test, host-pointer and worktree-removal obligations;
approval does not bypass them or authorize a push.

Current state supersedes every previous approval wait: plan and spec are marked
approved at `0f52b49`, Task 1 is unblocked, and the controller is parked at Keith's
request for a fresh session. The next agent starts sci-7b3829 in the retained
worktree and performs Task 1 Setup, including the deferred policy-appropriate
baseline. No implementation, runtime tests, build, live retrieval or pilot ran
in this approval/parking turn. `just check`, whitespace validation and the
documentation pre-commit hook passed for the clarification commit.
