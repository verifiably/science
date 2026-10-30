# Readable Stores Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Read inherited holdings from admitted stores while directing every new holding to the existing single write-store binding.

**Architecture:** Keep required `store_root`; add optional `read_store_roots`. One configuration helper validates unique root identities and existing lifecycle read admission. Read contexts use its mapping; the kernel session still receives only the write store.

**Tech Stack:** Existing Python, pathlib, TOML, beliefs kernel APIs, pytest through the project's just recipes. No new dependency.

**Spec:** [Readable stores design](../specs/2026-10-30-readable-stores-design.md), frozen at science `6d83468c5aa242ffd2ab8a10a3476dcfefa8c4ff`; SHA-256 `f0e64120d6bb9bfaa35d6cd705cb9d2ebfef5d3c43af61ed151680ac47fac31c`.

**State:** Proposed plan; implementation waits for plan review. Controller approved the design under the user's delegated decision after accepted spec rounds 3 and 4. Round 4 adds the pre-integration store inventory below. Tests described here are not yet implemented or run.

**Execution recommendation:** Native inline, in dependency order, with a fresh final reviewer. The three tasks share the configuration and resolver interfaces; separate implementer contexts would repeat that context without useful parallel work.

## Global Constraints

- `store_root` remains required; `read_store_roots` defaults to `[]`. No compatibility layer, schema replacement or new CLI command.
- Read admission accepts only `WRITABLE` and `READ_ONLY_SERVICEABLE`, including for `store_root`; reads never repair, recover, initialize or migrate.
- Store identities match exactly. Duplicate resolved paths and duplicate identities refuse. A fork never substitutes for its parent.
- The reducer's lexicographic `(digest, location)` order chooses the first configured observation. No write-store preference or fallback after an I/O error or digest mismatch.
- Snapshot retains explicit refusal for unresolved found observations; absent declarations/observations and a selected vocabulary's digest mismatch remain unreadable.
- Blocked/unsettled reduction remains authoritative for the entire dataset. No intent repair or receipt/guard disposal here.
- Live initialization, migration, reconfiguration and holding writes require separate authorization. Read-only inventory does not authorize any of them.
- Lifecycle admission is not a per-use byte-integrity proof. Run/verify digest comparison is outside this plan.
- Every subprocess test uses a key-by-key environment with a test-owned HOME, explicit PATH and only needed values; isolate inherited Git configuration if a test uses Git.

## Review Focus

Each risk below is covered in its owning task, rather than left to final review:

1. Old single-store configurations: new admission validation must not silently strand an active world; Task 3 inventories every discovered configured root and blocks integration on unresolved active failures.
2. A valid copied genesis without read admission: Task 1 refuses it without creating metadata, locks, sidecars or a session ledger.
3. Aliases, foreign identities and escaping paths: Tasks 1–2 reject ambiguous bindings and paths outside the matched root.
4. Missing local vocabulary mounts: Task 2 checks snapshot and both consuming paths, preserving refusal rather than quietly changing belief inputs.
5. A healthy second copy beside a corrupt or blocked first location: Tasks 2–3 preserve deterministic selection, no fallback and whole-dataset blockage.

## Workspace, setup and gates

All relative file and recipe paths below are from the execution worktree. When reporting to the user, prefix them with `.worktrees/sci-300dab-stores/` from the main checkout.

- [ ] Resume the existing locked worktree and its task claim, verify the frozen spec, read current AGENTS.md and run trial-arm for each started task. Do not create another worktree.
- [ ] Re-enter using-git-worktrees Setup before code changes. The declared root setup is `git config core.hooksPath .githooks`; README install is `cd python && uv sync`. Verify the editable beliefs sibling resolves first; the main checkout's worktree-storage sibling link currently supplies it. Install only the worktree's environment; do not repoint any host launcher or shared environment. Record any setup failure before tests.
- [ ] Validate test policy in this code root through its tt wrapper. Planning found no `.tt.toml`; with policy unchanged run the deferred full baseline `just test`, recording its command and nonzero test count on the task. With a newly validated policy-off checkout, use the corresponding focused baseline and mandatory hygiene instead; a skip is never a pass.
- [ ] For each code task prove RED then GREEN using `just test-one` below; with current policy run `just test-fast` and `just check` before its commit. Do not call pytest directly. The installed pre-push hook owns later broad verification unless the project's documented exception applies.
- [ ] Follow task lifecycle and record reviews. After all tasks, obtain a fresh whole-branch review and correct material findings under the governing corrective-round rules. Complete Task 3's inventory gate before local integration; no push is authorized.

## File map

| File | Responsibility |
| --- | --- |
| `python/src/science/config.py` | TOML field, resolved path validation, admitted identity mapping, cached read-context access |
| `python/src/science/session.py` | Validate bindings before the kernel creates a session; continue binding only `store_root` |
| `python/src/science/holdings.py` | Resolve observations through the mapping while preserving reduction semantics |
| `python/src/science/vocabulary.py` | Pass the mapping and document snapshot refusal/unreadable cases |
| `python/tests/test_stores.py` (new) | Mapping, lifecycle, restored-store integration fixtures and tests |
| Existing config/context/session/run/verify/fetch tests and test config writers | Regression and consumer coverage |
| `docs/stores.md` (new), README and current configuration descriptions | Operator recipe and config/read behavior |

### Task 1: Validate configured store bindings before use

**Files:** Modify `python/src/science/config.py`, `python/src/science/session.py`, `python/tests/test_config.py`, `python/tests/test_session_open.py`, `python/tests/helpers/world.py`, `python/tests/helpers/commons.py`; create `python/tests/test_stores.py`.

**Interfaces:**
- Consumes `beliefs.root.store_identity(root: Path) -> str | None`, `read_lifecycle_state(root: Path) -> LifecycleState`, and `metadata_root_for(root: Path) -> Path`.
- Produces `ScienceConfig.read_store_roots: tuple[Path, ...] = ()` and `science.config.configured_stores(config: ScienceConfig) -> dict[str, Path]`. The mapping contains the write store and every read store, with resolved roots and one root per identity.

- [ ] **Step 1: Add failing configuration and admission tests.** Extend the existing test config writers to emit the optional list when supplied. Keep existing configs valid without it. Add tests named `test_read_store_roots_round_trip`, `test_read_store_paths_are_config_relative`, `test_read_store_roots_reject_bad_entries`, `test_configured_stores_reject_duplicate_paths_and_ids`, `test_configured_stores_require_read_admission`, and `test_bad_store_binding_precedes_session_ledger`. Pin these assertions (the case table is test data, not a new production API):

  ```python
  assert load_config(single_config).read_store_roots == ()
  assert load_config(multi_config).read_store_roots == (read_root.resolve(),)
  assert configured_stores(cfg) == {write_id: write_root.resolve(), read_id: read_root.resolve()}
  readable = {LifecycleState.WRITABLE, LifecycleState.READ_ONLY_SERVICEABLE}
  refused = {LifecycleState.METADATA_LESS, LifecycleState.BINDING_MISMATCHED,
             LifecycleState.READ_ONLY_UNSERVICEABLE}
  assert readable | refused == set(LifecycleState)
  assert caught.value.refusal.code == "invalid-input"
  assert str(bad_root) in caught.value.refusal.message
  assert not (cfg.operations_root / "sessions").exists()
  ```

  Cover a non-list, non-string entries, empty strings, duplicate paths through `..` or symlinks, overlap with `store_root`, duplicate genesis ids, absent/malformed genesis, and direct dataclass callers. For each of the five lifecycle states test both write and read roles. Inject only the lifecycle result to test the closed state table; separately use real initialized and copied roots to exercise the actual API. Identity `None` and `CorpusRootRefused` must both name the root.

- [ ] **Step 2: Run RED.** `just test-one tests/test_config.py tests/test_stores.py tests/test_session_open.py`. Expected: new assertions fail because the field/helper/admission gate is absent; existing failures caused by missing dependencies are setup failures, not RED evidence.

- [ ] **Step 3: Implement the field, helper and pre-session gate.** Add the optional key and string-list validation to `load_config`, using its existing `located` rule; reject duplicate resolved paths without silently deduplicating. `configured_stores` repeats the root-uniqueness check for direct constructors, inspects identities, rejects duplicate ids, then validates every root's lifecycle. Call it from `open_session` before `open_attended_session`; continue passing only `config.store_root` into the kernel. Parsing TOML itself does no identity/lifecycle inspection.

  Error contract: invalid bindings/states and `CorpusRootRefused` become `Refused(Refusal("invalid-input", ...))`. Inspection failures from the existing `beliefs.root.AtomsError` base (including `MetadataStoreInvalid`, `CapabilityUnavailable` and `PreconditionRefused`) or `OSError` become `kernel-refused`, with `data={"kind": type(caught).__name__, "root": str(root)}` and a message naming the root and original cause; preserve `__cause__`. Import through `beliefs.root`, never directly from atoms, and do not classify engine subtypes or catch `Exception`. Unexpected programming errors still propagate, never produce a mapping. This uses the existing surface refusal envelope; it does not add a kernel API or change kernel exception behavior.

- [ ] **Step 4: Add and run focused error/no-mutation checks.** In `test_stores.py`, inject `PermissionError` and a kernel metadata inspection error and assert named refusal, retained cause, no mapping and no ledger. For a real metadata-less copy, a real writable store and a real admitted replica, compare file names/types, symlink targets and file bytes under the root and `metadata_root_for(root)` before/after; include absence of the metadata tree, lock and SQLite sidecars in the comparison. Do not interpret access-time changes as mutation. Reuse the existing tree-digest pattern, extending it to absent trees and links locally in this test file. A real unserviceable replica after `replicate_root` and before the restore grant covers incomplete admission; inject a restore-grant failure before it acts and assert retry remains refused until an explicit fixture restore succeeds.

- [ ] **Step 5: Run GREEN and commit.** Repeat Step 2 and the newly added test cases, then policy-appropriate pre-commit gates. Commit explicit paths with `feat(stores): validate configured read store admission`. Record actual test counts and finish this task's record.

### Task 2: Resolve inherited holdings and vocabularies through every admitted store

**Files:** Modify `python/src/science/config.py`, `python/src/science/holdings.py`, `python/src/science/vocabulary.py`, `python/tests/test_context.py`, `python/tests/test_stores.py`, and the relevant consumer assertions in `python/tests/test_cmd_run.py` and `python/tests/test_cmd_verify.py`.

**Interfaces:**
- Consumes Task 1's `configured_stores(config) -> dict[str, Path]`.
- Produces cached `ReadContext._stores: dict[str, Path]`; retains `store_id() -> str` for the write-store identity and `held_path(address: str) -> Path`.
- Replaces internal signatures with `held_path_for(stores: Mapping[str, Path], observations: tuple[ByteObservation, ...]) -> Path`, `held_path(views, world, stores: Mapping[str, Path], address: str) -> Path`, and `vocabulary.snapshot(profile: ProfileSpec, views, stores: Mapping[str, Path], observations) -> ResolutionSnapshot`.

- [ ] **Step 1: Add failing resolution tests.** Update the old single-store helper calls and add tests named `test_held_path_reads_each_configured_identity`, `test_foreign_identity_never_resolves_by_path`, `test_read_copy_can_sort_before_write_copy`, `test_held_path_rejects_escape`, `test_snapshot_refuses_unconfigured_observation`, and `test_snapshot_does_not_fall_back_after_bad_copy`. Pin these assertions with ordinary fixture paths and `ByteObservation` values:

  ```python
  assert held_path_for(stores, (foreign, inherited)) == read_root / relative
  assert held_path_for(stores, ordered_equal_digest_observations) == first_root / relative
  assert caught.value.refusal.code == "invalid-input"
  assert ReadContext.open(cfg).store_id() == write_id
  assert ctx.snapshot().resolve(binding, "concept:disease-stage") is TermOutcome.MEMBER
  ```

  Use fixed distinct ids in pure resolver tests to make lexicographic selection deterministic. Include an unknown identity with the same relative file present in a configured store, URLs, empty observations, absolute paths, `..`, and a symlink escaping the selected root. Snapshot tests must distinguish missing declaration/no observations (unreadable) from found observations with no configured carrier (refusal). A chosen file's digest mismatch is unreadable and its I/O failure propagates; neither reads a later good copy. Spy on the second file's read if necessary.

- [ ] **Step 2: Run RED.** `just test-one tests/test_context.py tests/test_stores.py`. Expected: inherited paths and snapshot tests fail against the one-store resolver.

- [ ] **Step 3: Implement the mapping interfaces and update every caller.** `_stores` calls Task 1's helper on first use. `store_id()` obtains the identity whose mapped root equals `config.store_root.resolve()`; no second unvalidated identity lookup. `snapshot` and `held_path` pass the same cached mapping. Keep the reducer and its observation order unchanged. For a matching store locator use the existing `StoreLocator` validation, translate `MalformedRecord` into `invalid-input`, and refuse if the resolved candidate leaves its matched root (including symlinks). Return the selected root joined with the validated relative path; do not test other observations after selection. No special write-store priority, path search, network lookup or fallback.

  Update snapshot's docstring to state all three outcomes: unresolved found observation refuses; absent evidence is unreadable; selected bytes with wrong digest are unreadable. Leave `is_held`, `found_observations`, `dataset` and `fetch` destination logic unchanged. Search every `held_path_for`, `held_path`, `snapshot` and `store_id` call before completing the signature change.

- [ ] **Step 4: Cover the shared consumers.** Parameterize the existing evaluation/gathering setup to invoke both `ReadContext.evaluate` and `ReadContext.gather_inputs` with a found vocabulary observation whose store is unconfigured; assert `invalid-input` survives both paths. Preserve their current no-epoch fixture requirements; do not fake a passing evaluation. For run preparation, build the existing spec fixture and assert `prepared["held_inputs"][address]` points to the inherited root. In verify's existing assessment fixture wrap its imported `prepare` to call the real function and capture that mapping; stop before replay with a test sentinel, proving the actual handler consumed the inherited path without running another scientific workflow.

- [ ] **Step 5: Run GREEN and commit.** `just test-one tests/test_context.py tests/test_stores.py tests/test_cmd_run.py tests/test_cmd_verify.py`, then policy-appropriate gates. Commit explicit paths with `feat(stores): resolve holdings across admitted stores`. Record counts and finish this task's record.

### Task 3: Prove relocated-store writes and gate rollout with a live inventory

**Files:** Modify `python/tests/test_stores.py`, `python/tests/test_cmd_fetch.py`, `README.md`, `docs/specs/2026-08-31-command-framework-design.md`, `docs/specs/2026-09-09-belief-path-commands-design.md`; create `docs/stores.md`. Record host-specific inventory on this task, not in portable reference docs.

**Interfaces:**
- Consumes Tasks 1–2, the existing `open_rig`/`build_belief_world` fixture helpers and public `replicate_root`, `restore_root`, `export_head_artifact`, `StoreSubject`, `ObserverSet` and `ArtifactCarrier` kernel APIs.
- Produces a tested operator runbook and evidence that new writes use only the fresh store while inherited reads and the source tree remain intact. No new production interface.

- [ ] **Step 1: Build a real relocated-store fixture and missing-evidence tests.** In `test_stores.py`, start with `build_belief_world` and hold an additional ordinary dataset before replication. Export the source store head with `StoreSubject(store_id)`, replicate it into a separate existing parent, and restore it using the exported artifact. Assert the restore report is `validated` and lifecycle is `READ_ONLY_SERVICEABLE`. Keep the corpus carrying the source observations mounted; configure only the restored carrier for that identity. Create a fresh write store using the exact runbook recipe below. Do not use `hold_fixture_dataset` after swapping the write store because its `STORE_IDS` fixture mapping names the original store; use the real dataset command for new bytes.

  Test names: `test_relocated_store_reads_and_new_dataset_write`, `test_fetch_keeps_inherited_observation`, `test_blocked_digest_is_not_rescued_by_fresh_store`, and `test_operator_store_recipe_is_repeatable`. Required assertions:

  ```python
  assert read_lifecycle_state(restored) is LifecycleState.READ_ONLY_SERVICEABLE
  assert new_store_id != inherited_store_id
  assert ReadContext.open(cfg).held_path(old_address).read_bytes() == old_bytes
  assert ReadContext.open(cfg).held_path(new_address).is_relative_to(cfg.store_root)
  assert before_restored_tree == after_restored_tree
  assert before_restored_metadata == after_restored_metadata
  assert {old_location, new_location} <= reduced_locations
  assert isinstance(blocked_answer, DatasetBlocked)
  ```

  Include inherited vocabulary resolution before and after the new dataset write. Fetch the declared inherited bytes into the new store with the fixture's enabled fetch policy; verify observation locations retain both identities. Feed the actual holdings reducer a matching blocked row alongside a healthy location and verify `held_path` refuses the whole address; adding the mapping cannot mask that result.

- [ ] **Step 2: Run the focused evidence checks.** `just test-one tests/test_stores.py tests/test_cmd_fetch.py`. New end-to-end tests may already pass after Tasks 1–2; record that honestly as integration evidence, not fabricated RED. Any newly required production correction needs a focused failing check before its fix. The runbook-recipe test initially fails because the documented recipe is not yet present; prove that RED before adding it.

- [ ] **Step 3: Write and exercise `docs/stores.md`.** Include the complete shell invocation for the spec's Python initializer, taking an absolute destination and using an operator authority limited to `lifecycle`. Use one fenced shell block marked by a stable `store-init-recipe` HTML comment; the test extracts that block, substitutes only the interpreter command and explicit destination argument for its fixture, and executes the exact Python body. Run twice, require the same id, and prove passing a restored copy refuses without changing it. The subprocess environment is built key by key, using the current test interpreter, explicit PATH, test-owned HOME, a fake USER if needed, and `PYTHONDONTWRITEBYTECODE=1`; no inherited credentials or shared environment.

  Include `store-working`/`store` config, resolved payload/metadata non-overlap checks, retained corpora, writer restart under the exact config, inherited-read verification, whole-dataset blockage, both stores' backup needs and rollback limitations. Explain old single-store read admission and the public `migrate_root_to_lifecycle_v3` route: it is an explicit operator attestation of the original minting host, applies only to the exact pre-lifecycle v2 store, and must never be called merely because the read check refuses. A restored replica needs restore completion, not promotion to writable. Do not provide an automated migrate-on-read path.

  Link the runbook from README; update framework section 9.1 and the belief-path current configuration description. Leave historical run records and old plans unchanged. No command manifest or generated adapter changes are needed.

- [ ] **Step 4: Refresh the complete discovered-config inventory before integration.** Do this on the registered host using an existing declared environment with bytecode writes disabled. Inspect TOML directly with `tomllib`, resolve relative paths against the real config file, and call only `store_identity`, `read_lifecycle_state` and `metadata_root_for` for each write/read store. Do not open a science session or a writable world. Search named configs from `SCIENCE_CONFIG`, launcher/service configuration and task/source records; search TOML files in registered science/research-program roots, their relevant worktrees and the referenced data trees. Follow discovered config references until no unexplained live reference remains. Record the exact search locations and exclusions; do not claim an exhaustive host-wide inventory if locations remain unknown.

  Each row on the task records config path and SHA-256, resolved root/metadata path, identity, lifecycle state or typed error, and active/archived/unknown status with its evidence. Include every root even if several configs share it, marking aliases. A copied config attachment with relative paths is historical evidence, not a launcher rooted at its attachment directory.

  Planning-time seed, to recheck rather than trust indefinitely:

  | Config | Observation on the inspected host, 2026-10-30 | Disposition |
  | --- | --- | --- |
  | Active config selected by `SCIENCE_CONFIG` (mm30) | Store `05b6c1225e710bb1559f36e8333f3f29`, `read-only-serviceable` | Read admission passes; writes still require the separate fresh-store route |
  | mm `docs/reports/2026-10-09-gse24080-spike-science.toml` | Root absent, no identity, `metadata-less` | The adjacent spike report's retention section records deletion of its disposable world; config is archived evidence |
  | sci-0d00d2 `live-science.toml` attachment | Copy of the live config | Historical attachment, not another active world |

  Exact host paths and the original command observations are in sci-300dab's planning note. The initial search covered main science, mm, beliefs, ns, sun and autonomy trees and the active data tree; it did not cover arbitrary external locations or all worktrees. Step 4 must refresh and expand that scope as described above.

- [ ] **Step 5: Apply the compatibility gate.** Every discovered active store must have a valid unique identity and readable state; every archived/removed row needs recorded evidence; every unknown or inaccessible row stays unresolved. For an active `READ_ONLY_UNSERVICEABLE` root, identify whether it is an exact pre-lifecycle store or incomplete restore using the kernel's diagnostics and source records; never infer that solely from its state. Record the authorized migration/restore owner and block integration pending completion and a fresh read check, or an explicit user disposition. No auto-migration, silent exclusion or retroactive “inactive” classification. If coverage has a known gap, obtain its disposition before integration. This gate checks read compatibility, not live writability or mm-62e2da pilot readiness.

- [ ] **Step 6: Verify, review and commit.** Run `just test-one tests/test_stores.py tests/test_cmd_fetch.py tests/test_context.py tests/test_cmd_run.py tests/test_cmd_verify.py` and policy-appropriate hygiene/fast checks; record counts, inventory scope and any blocked rows separately. Commit explicit paths with `docs(stores): document and verify writable side stores`. Finish this task only when its compatibility gate has a disposition. Then perform the final whole-branch review, make required corrections, and finish the parent only when all obligations are met. Local integration is `git merge sci-300dab-stores` from the clean main checkout after review and the compatibility gate; any live migration, deployment, reconfiguration or push remains separately authorized.

## Coverage and handoff

Task 1 covers configuration, identities, lifecycle states/errors and pre-session refusal. Task 2 covers resolver/snapshot semantics and run/verify consumers. Task 3 covers real restore plus writes, operator creation, docs, blocked holdings, retained bytes and compatibility inventory. No spec requirement is deferred; the separate run-input digest comparison question remains explicitly outside scope.

The controller self-reviews the final plan for spec coverage, exact interfaces, checkable steps and proportion before freezing it. User plan review precedes implementation. If another review revises the plan, freeze a new commit rather than editing the revision under review.
