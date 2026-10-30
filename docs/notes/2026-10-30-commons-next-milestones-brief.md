# Commons after milestone 1 — scope brief

## Problem

Carry the approved commons direction into milestones 2–4: discover and adopt a
collection, preserve its promised material, then harden identity and sharing.
The shared source is sci-fe8522 and the approved commons design §12. All three
ideas woke when milestone 1 completed; this brief does not approve implementation.

## Current behaviour and evidence

At science `023d911`, sci-13050a and sci-9104fb are done. The latter records
integration at `775ec0f`, including retirement (`bb1fad5`, `320f9e3`, `1339976`),
and a historical gate of 1070 passing tests. This pass did not rerun that gate.
The commons design §12 records both halves as implemented; its introductory
pending-retirement sentence is stale (document polish already has sci-7a964f).

`python/src/science/transport_git.py` provides push, listing and corpus fetch.
`sharing.py` reserves follows and recognizes catalog pin sources, but
`commands/adopt.py:_source` still requires a bound provider. The CLI has no
catalog, follow or provider-list commands. Those data types are preparation,
not proof of a working commons. `config.py` and `commands/fetch.py` already
implement records-only/fetch and byte bounds; fetch currently holds one resource.
Milestone 3 therefore extends existing fetch behavior, not a blank implementation.

The three ideas have no creation occurrence/session stamp. Their filing events
are unavailable under the origin reading rule; sci-fe8522's filing summary
corroborates the batch but does not establish whose asks they were. Origin stays
unknown. There is no recorded origin_session for an older-request lookup.

## Constraints

The commons design §§4, 7, 12 and 14 remain authority: follow, hold and accept
are separate; catalog recommendations and imported bindings confer no authority;
aggregation preserves each author's statements and promises and refuses conflicting
pins; publication identity is content, independent of location. Registry effects
need ledger evidence and replay. New CLI rows originate in ops' vocabulary.
No new need is declared by this project's task configuration.

Reuse beliefs-42d201 for marker-locator adequacy, beliefs-36d11c for signed head
artifacts and beliefs-51fa7d for coordination/view publication. The latter two
remain shelved pending a scoped milestone 4; a brief alone does not meet that wake.
Existing repair work, especially sci-347a36 (pinned refetch integrity), and
sci-eb808f (Git plumbing), must be reconciled by the design, not duplicated.
The clean-environment verdict evidence gap remains sci-b979ce.

## Alternatives

1. Promote all three directly to implementation: rejected because catalog policy,
   transport reconciliation and signing interfaces still need decisions.
2. Re-shelve everything: rejected because milestone 1's completion met the old wake.
3. Recommended: keep the ideas briefed with explicit waits; design milestone 2,
   run one bounded preservation experiment, and design the hardening boundary.
   Designs require human review before implementation planning and execution.

## Unanswered questions

- Milestone 2 designer: settle §14's inclusion audit trail, relation vocabulary
  using a first real catalog, and reproducibility summary; define side-artifact
  commands, ledger/replay and mirror adoption. Exercise execution-locator handoff
  and report its evidence to beliefs-42d201 instead of adding another locator task.
- Milestone 3 researcher: can the current transport contract reconcile an interrupted
  draft-to-publication operation, or does it need a commit boundary? Determine layout,
  visibility and retry evidence from current official documentation and a bounded
  experiment. A local model is not proof of live service behavior; remote writes
  need separate authorization. Preserve records/data/execution promise distinctions.
- Milestone 4 designer: specify signing and re-confirmation on location ownership
  change, subscription traversal bounds, coordination publication, and curated find
  relations. Reuse the kernel tasks, identify which milestone 2 contracts it needs,
  and arrange their re-scoping when the milestone's scope actually settles.

## Proposed decomposition

Goal sci-009431 groups the existing roadmap and these next actions:

- sci-03ddea: design catalogs and mirror adoption; wakes sci-8363b5 (milestone 2).
- sci-3a2f02: determine whether preservation transport needs a commit boundary;
  wakes sci-65d6c9 (milestone 3).
- sci-03179a: design hardening boundaries; wakes sci-66d347 (milestone 4).

Each milestone waits on its corresponding follow-up. Each completion records
findings here and re-admits its waiting idea before merging its result branch.
Original milestone bodies and sources are preserved. All three verdicts are
briefed: the follow-ups settle decisions before implementation is scoped.
