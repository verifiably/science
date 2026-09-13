---
id: sci-71cf32
title: Review the hctsa feature space for redundancy among candidate detectors
status: done
priority: 2
size: m
complexity: mid
owner: main
created: 2026-09-13T03:04:58Z
updated: 2026-09-13T09:14:06Z
started: 2026-09-13T03:05:17Z
completed: 2026-09-13T03:10:31Z
depends: []
parent: sci-3fc3a9
tags: [natural-systems]
---

Framing §2.1 and §6 q2. Read Fulcher, Little and Jones 2013 (arXiv 1304.1209), the hctsa feature taxonomy, and the catch22 reduction. Output: a short note listing which of the candidate detector families (repetition, oscillation, scaling, branching, recursion, relaxation, cross-series dependence) are already covered by hctsa features, which features are known to be redundant, and which candidates have no hctsa analogue. Record each candidate's source and whether its selection used the expression corpus (§2.6). No detector is written in this task.

## Notes

- 2026-09-13T03:10:31Z (main): Review written to docs/notes/2026-09-13-hctsa-review.md; framing §2.1 now points at it. Findings: all univariate candidate families are covered in hctsa; cross-series dependence is covered by no library; branching and recursion are not time-series properties; catch22 is a supervised, label-driven reduction and cannot see location or spread
- 2026-09-13T03:10:31Z (main): hctsa review landed in docs/notes/2026-09-13-hctsa-review.md with the coverage table and six consequences for the experimental design
- 2026-09-13T09:07:07Z (main): Re-homed to natural-systems-v2 as ns-474552; the note now lives there
- 2026-09-13T09:14:06Z (main): The initial review summary above was superseded by the 2026-09-13 corrections in natural-systems-v2: existing multivariate tooling covers cross-series dependence; branching and recursion are deferred by scope; normalization does not establish that relaxation is undetectable.
