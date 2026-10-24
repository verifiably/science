---
id: sci-cf4d58
title: "Acceptance and show: compute the policy inputs once per read and share adopt's reconcile predicate"
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-23T18:45:08Z
updated: 2026-10-24T11:33:54Z
depends: []
tags: [commons]
source: sci-13050a
agent: claude-code
---

Deferred from the commons 1a reviews (ledger attached to sci-13050a). (1) acceptance_inputs is rebuilt for the kernel's predicate and again for explain/next, re-reading the registry between, so belief's explanation is not guaranteed to describe the predicate used (Task 10 M1); cache it on ReadContext. (2) closure.gather_inputs/evaluate default acceptance=None, so a future caller skips the policy silently (Final M8); make it required. (3) show's 'counts as evidence' row is judged from the first assessment only (Final M1); report k of n. (4) show's registry-lags-kernel finding uses a different predicate from adopt._reconcile (Task 11 minor); share one helper. (5) explain's 'excluded <address>' keys omit the corpus and can collide (Task 10 M3).

Established at science 99111f7: ReadContext already uses cached_property for views, observations and world inputs, and Dispatcher creates a fresh context with dataclasses.replace for each invocation. acceptance_inputs is uncached and reads registry.pins twice; policy(), belief.handle's explanation, and next._assessed independently rebuild it. Both closure wrappers accept omission, although current production callers in config.py already pass a policy. show uses assessments[0] for the summary; its lag test uses status.known/live while adopt uses membership in registry().admissions. explain keys omit corpus identity. See [ref:commons] §9/10 and [ref:review-ledger] Task 10 M1/M3, Task 11 and Final M1/M8.

Done: reuse the existing ReadContext cache pattern for one acceptance-input snapshot per invocation, reading the registry pin collection once for that snapshot, and make the kernel predicate, next classification, show and belief explanation consume it. A new context must see later registry changes. Require an explicit acceptance argument at the closure wrappers; update all callers/tests without weakening the current policy. Show k of n assessments that count rather than infer the corpus-wide result from the first, preserving the no-assessment n/a case and existing per-assessment verification rows. Share adopt's fetched/admitted plus kernel-admission predicate with show's read-only lag finding, so both name the same recoverable condition. Qualify exclusion keys by corpus and address. Test within-context consistency across a registry mutation, refresh on a new context, mixed/no assessments, matching lag decisions, distinct corpora sharing an excluded address, and required wrapper arguments.

Where: python/src/science/config.py (ReadContext), acceptance.py, closure.py, commands/belief.py, next.py, show.py and adopt.py; tests/test_context.py, test_acceptance.py, test_cmd_belief.py, test_cmd_next.py, test_cmd_show.py and test_cmd_adopt.py. Find every closure caller before changing the required argument. Run the affected files through just test-one, then just test-fast. Keep carried-content authentication and the actual verdict-flip fixture with sci-4a3543 and sci-b979ce; broader next re-derivation cleanup remains sci-e42351.

## References

- commons (input, required, kind=spec): docs/specs/2026-09-30-science-commons-design.md — governing identity, transport, acceptance and recovery contract
- review-ledger (context, kind=ledger): tasks/files/sci-13050a/sdd-ledger-commons-1a.md — original findings and retained rulings
