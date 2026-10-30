---
id: sci-b7abdf
title: Strengthen assumption-sweep screening with staged external-cohort and embedded-result rehearsals
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-30T15:04:23Z
updated: 2026-10-30T15:05:52Z
depends: []
tags: []
source: "sci-b2755f:screening-rehearsal-extension"
agent: codex
origin: agent
---

Origin: agent-proposed follow-up to the accepted sci-b2755f / sci-d3044e pilot, after the user asked which additional follow-ups would be useful. Acceptance at science commit e674683 covers three bounded questions, not field-wide priority or biological validation. The exact input report is attached to sci-b2755f as pilot-v3-report.md (SHA256 6815cc2f6d9b5c5d86d5aaafd291dfe88aba4cedb097fb8f47f7ec038356f18f); resolve its current path with tasks show sci-b2755f. The full source/inventory/read/review artifacts are on that same task. Persistent exact inputs belong to sci-eb1559; verify its manifests before use.

Why: the reusable skill already requires all implicated cohorts to be cleared, and the existing fixture explicitly declares both cohorts in its mixed-source example. In the real pilot, an abstract was read after clearing its primary cohort but before a separate external-validation section revealed an unresolved cohort. Methods sections also exposed outcome tables, and reference link metadata carried result-bearing titles. Excluding those results made the final report admissible; it did not make preventive screening succeed.

Bound: strengthen the existing authored skill and synthetic rehearsal, not build a downloader or universal semantic filter. Add staged synthetic responses in which the first availability/sample section names only permitted cohort A, a separate validation section introduces unresolved cohort B, a Methods subsection embeds an outcome table, and a reference identifier field includes an encoded result title. Require the smallest explicit pre-abstract record of which result cohorts and validation sources were checked, their mappings and unresolved limits. Retain source-local stop/exclusion/routing behavior and the possibility that safe isolation is unavailable. Structural extraction and OA eligibility never certify semantic permission. No new scientific reads are needed: use invented fixture content informed by the incident categories.

Done when the new staged rehearsal shows the current weakness, the revised workflow demonstrably refuses premature abstract access and handles embedded-result incidents, the existing reach/duplicate/freeze cases still pass, generated adapters match authored files, policy-appropriate focused packaging checks and hygiene pass, and a fresh read-only reviewer accepts the returned behavior. Preserve frozen historical fixtures/reports by versioning new execution evidence. Do not claim a text-only checklist guarantees zero exposure. quarry-404f63 owns Europe PMC metadata/file availability; section/cohort gating stays with the consumer. This is a scoped extension based on a pre-close recorded incident, not a newly discovered defect in the accepted report.
Deliver the findings as [ref:result], attached through tasks attach; verify the task lists the attachment before completion.

## References

- skill (input, required, kind=guide): skills/sweep-assumptions/SKILL.md — current read boundary
- scenario (input, required, kind=dataset): python/tests/fixtures/sweep-assumptions/scenario.md — staged synthetic source inputs
- oracle (input, required, kind=guide): python/tests/fixtures/sweep-assumptions/expected-review.md — existing behavioral acceptance
- pilot (input, required, kind=report): tasks/files/sci-b2755f/pilot-v3-report.md — incidents and accepted use restrictions
- result (output, kind=report): files:screening-rehearsal-v2-report.md — bounded findings and verification

## Notes

- 2026-10-30T15:04:23Z (add): created
  provenance: {"harness_session":"codex:01a18ce3-2793-7ad1-b204-ef9b88b33aba","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
- 2026-10-30T15:04:25Z (main): concerns: sci-b2755f extension — Strengthen the reusable screening rehearsal using recorded pilot failure modes; preserve the accepted report and existing incident disposition.
