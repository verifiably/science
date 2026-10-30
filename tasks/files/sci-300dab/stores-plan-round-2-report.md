# Plan review round 2

Reviewer: claude-code/claude-opus-5-5 (identity supplied in the relayed review).
Frozen revision: science 3ccc4a86015a3f118e0fba7125aaef98b3910b27, docs/plans/2026-10-30-readable-stores.md.
Verdict: revise; Important 1, Minor 4. Full relayed review follows.

I'd revise the plan before implementation, though only lightly. Its references hold up, but the step that turns store-inspection errors into refusals doesn't use the project's existing route, which the spec required. Fixing that plus four smaller points means freezing a new plan revision and sending it back for review. Implementation stays blocked until then. Separately, the plan's State line says the design was approved under delegation from you. I didn't approve it: last round I said the design gate was yours. If you approved it, the line should say so.

**What I reviewed:** commit 3ccc4a8, `docs/plans/2026-10-30-readable-stores.md` in `.worktrees/sci-300dab-stores`. The spec hash in the plan matches the frozen spec at 6d83468, and the spec hasn't changed since.

**Checked and holding up**
- **Kernel calls:** every function the plan relies on exists in beliefs with the shape it assumes. That covers `read_lifecycle_state`, `metadata_root_for`, `export_head_artifact` (which takes a store root), `restore_root` with a store subject, `ArtifactCarrier` and `ObserverSet`, and `migrate_root_to_lifecycle_v3`. The plan describes the migration correctly: calling it is the operator's statement that this host originally created the store, and it applies only to the exact pre-lifecycle store.
- **Path checks:** `StoreLocator` already validates both the store id and the relative path, so Task 2 can reuse it instead of re-parsing.
- **Test helpers:** `open_rig`, `build_belief_world`, `hold_fixture_dataset` and `STORE_IDS` all exist. The plan is right that `STORE_IDS` is keyed to the original store, so it can't be used after the write store is swapped. Beliefs' `tests/test_store_subjects.py` has store export and restore patterns Task 3 can borrow.
- **Session paths:** both `serve.py` and `mcp.py` open sessions through `session.open_session`, so the check before the session opens covers both.
- **Test policy:** there is still no `.tt.toml`, so the full baseline and the usual suite rules apply, as the plan says.
- **Execution mode:** I agree with inline execution plus a fresh final reviewer. The three tasks are sequential and share the same interfaces.

**Important**

1. **Task 1's error handling neither uses the existing route nor public names.**
   - **Non-public imports:** the plan imports `AtomsError`, `MetadataStoreInvalid`, `CapabilityUnavailable` and `PreconditionRefused` "through `beliefs.root`". None of them is in `beliefs.root.__all__`; they are just imports inside that module. Nothing in science imports them today.
   - **A second refusal path:** the plan builds the `kernel-refused` refusal inside `config.py`. The dispatcher already has one function for that, `Dispatcher._kernel_refusal`, whose comment calls it "the one normalization path for every kernel refusal shape". It catches only the closed `KERNEL_REFUSALS` tuple.
   - **Why it matters:** the spec asked the plan to name "the existing surface normalization route". This plan adds a second one, with a different data shape (it adds `root`), built on names beliefs doesn't publish.
   - **Fix:** move the refusal-building code from `_kernel_refusal` into a shared helper in `refusal.py` that both the dispatcher and the store helper call, so there is one shape and the root is an addition to it. Then either file a beliefs task to export these four error types and import them once it lands, or keep the import from `beliefs.root` with a comment that cites that task. Doing nothing still fails loudly on import if beliefs reorganizes, so this isn't a silent risk, but the plan shouldn't call these names public.

**Minor**

2. **The halt is still open.** sci-0bea23 is still `todo` and tagged `halt`. Each of sci-14a324, sci-bb8611 and sci-e5d803 needs `tasks start <id> --force --reason "…"`, and the plan's resume step should say so. Also, `just test-fast` is the slow recipe behind that halt (142 s against a 90 s limit), so expect slow pre-commit runs.
3. **Task 1 Step 4 tests kernel behaviour, not science's.** It injects a failure during the restore step and checks that retries stay refused until a restore succeeds. That exercises beliefs' and atoms' restore semantics. Science only needs a replica that reads as read-only-unserviceable to be refused without changes on disk. I'd drop the injected-failure part.
4. **Task 3's blocked-holding test is vague about its setup.** "Feed the actual holdings reducer a matching blocked row" doesn't say how a blocked row reaches `held_path`. It could be a real unsettled intent in the fixture or a patched `reduced_heads`. Name one so the implementer doesn't have to guess. The patched version is enough, because the spec's claim here is about science passing on `DatasetBlocked`.
5. **Plan sizing.** Task 3's inventory step is the most open-ended part of the plan, for example "follow discovered config references until no unexplained live reference remains". Consider a time limit or a fixed list of places to search, with anything not covered recorded as a known gap for you to rule on. The plan already allows that gap, so this is about keeping the step bounded, not about correctness.

**Review note for the controller to record (I wrote no note):** `review: plan round <n> — verdict: revise; findings: Important 1, Minor 4; reviewer: claude-code/claude-opus-5-5`. Here `<n>` is 1, unless the self-review was recorded as a round, in which case it is 2. The provenance point in my opening paragraph is about the record, not the plan's content, so I didn't count it as a finding.
