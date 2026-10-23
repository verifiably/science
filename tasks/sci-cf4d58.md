---
id: sci-cf4d58
title: "Acceptance and show: compute the policy inputs once per read and share adopt's reconcile predicate"
status: todo
priority: 2
size: s
complexity: low
created: 2026-10-23T18:45:08Z
updated: 2026-10-23T18:45:08Z
depends: []
tags: [commons]
source: sci-13050a
agent: claude-code
---

Deferred from the commons 1a reviews (ledger attached to sci-13050a). (1) acceptance_inputs is rebuilt for the kernel's predicate and again for explain/next, re-reading the registry between, so belief's explanation is not guaranteed to describe the predicate used (Task 10 M1); cache it on ReadContext. (2) closure.gather_inputs/evaluate default acceptance=None, so a future caller skips the policy silently (Final M8); make it required. (3) show's 'counts as evidence' row is judged from the first assessment only (Final M1); report k of n. (4) show's registry-lags-kernel finding uses a different predicate from adopt._reconcile (Task 11 minor); share one helper. (5) explain's 'excluded <address>' keys omit the corpus and can collide (Task 10 M3).
