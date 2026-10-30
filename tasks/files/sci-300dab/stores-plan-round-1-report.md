Reviewer: codex/gpt-6-astra (fresh relay model command verified identity)
Review mode: controller self-review required by writing-plans; not an independent review
Artifact: docs/plans/2026-10-30-readable-stores.md
Revision: 3ccc4a86015a3f118e0fba7125aaef98b3910b27
Spec: 6d83468c5aa242ffd2ab8a10a3476dcfefa8c4ff

Verdict: accept for human plan review; findings: none.

Spec coverage: Task 1 covers the additive configuration field, aliases, duplicate identities, lifecycle admission, direct constructors, error normalization, no-mutation checks and pre-session validation. Task 2 covers the resolver and snapshot interfaces, all named callers, deterministic ordering, confinement, foreign identities, missing-vocabulary refusal and run/verify consumption. Task 3 covers the actual replicate/restore route, fresh-store initialization, dataset/fetch observations, unchanged inherited roots, blocked reduction, operator docs and the round-4 compatibility inventory.

Step scan: each task names files, consumed and produced interfaces, test names and assertions, test recipes, implementation decisions and commit boundaries. Task 3 explicitly permits integration tests to pass after earlier tasks and does not mislabel that as RED; production corrections must still have failing evidence. The operator-recipe test starts with the missing documented artifact. Setup preserves the deferred baseline and revalidates current test policy.

Type consistency: configured_stores returns the identity-to-Path mapping consumed by the cached ReadContext mapping, holdings helpers and vocabulary snapshot. Public context held_path and store_id retain their return types. Kernel imports and method signatures were checked against the local tree; the new Python interfaces are defined in the task that produces them.

Review Focus: all five listed risks have owning tasks and checks. The initial compatibility search is explicitly bounded, and the execution gate refreshes and expands it; it does not treat the absent spike store as an active failure because its retained report documents deletion. A migration or restore requires separate authorization and fresh evidence; inspection cannot invoke either.

Proportion: the plan is 182 lines against the 311-line design. It specifies decisions and checks without duplicating production implementations or introducing new dependencies, commands or persistent state. Inline execution is recommended for the shared interfaces, with the required fresh final implementation review.

Verification: just check and the staged documentation hook passed after removing a hostname caught by the hook; git diff --check passed. The frozen spec is unchanged. Three direct child tasks are linked to the exact plan headings in dependency order.

Limits: no implementation, regression suite or full baseline ran. The planning inventory used only detached identity and nonmutating lifecycle queries; it is not an exhaustive host inventory or proof of live pilot readiness. Admitted payload integrity and run/verify declaration-digest comparison remain outside this plan. Human plan review is still pending.
