# SDD ledger — plan: docs/plans/2026-10-22-science-commons-1a.md

Session 2026-10-22 (controller claude-code/claude-opus-5-5). Task sci-13050a, trial arm: not enrolled.
Spec: docs/specs/2026-09-30-science-commons-design.md (reachable).
Kernel dependency beliefs-f24fe9: status todo at session start, so Tasks 4-13 are blocked; this session runs Tasks 1-3.

## Pre-flight scan (Tasks 1-3 in full; their interfaces to Tasks 4, 5, 10)

Shared files and interfaces:

| Pair | Produces / consumes | Found |
|---|---|---|
| 1 -> 4 | 1 produces `sharing.py` with `replay` (may defer as NotImplementedError + strict xfail); 4 removes the xfail and makes replay live over the door's lines | consistent; 1's replay test cannot build real fake_ledgers before the kernel writes sharing lines (see ruling R1) |
| 1 -> 2 | `SharingRegistry.mounted_roots()`, `SharingRegistryMalformed(entry, reason)` consumed by the loader | consistent |
| 1 -> 7, 8 | `write_binding`, `write_pin`, `root_for`, `scratch`, `apply_line`, `replay` | consistent by name; checked again when 7/8 unblock |
| 2 -> 3 | 2 creates `helpers/commons.py` (`write_minimal_config`, `refused`); 3 appends `GIT_ENV`, `commit_count`, `Remotes` | consistent, sequential |
| 2 -> 5 | `ScienceConfig.sharing_root/accept/fetch`, `FetchPolicy("fetch", 0)` used by `build_installation` | consistent |
| 2 -> 10 | 2 adds config keys; 10 modifies `ReadContext.evaluate/gather_inputs` in the same file | distinct regions, no conflict |
| 3 -> 6 | `GitTransport(cache, author=, remote_for=, env=)`, `GitTransportFault`, `production_git_env`; 6 builds the transport in `publication.py` | consistent |
| 3 -> 5 | `Remotes.remote_for` used by `with_remotes` | consistent |

Per-task self-consistency:

| Task | Found |
|---|---|
| 1 | Interfaces, tests and step 3's deferral agree. `Pin.keep` is not on `SharingLine`: lines create pins with keep False (consistent with spec §4.5 keep as local state). Kernel names verified: `beliefs.session.ledger.LedgerReader`, `InvocationRecord`, `open_ledger_reader` exist; `.sharing` does not yet. |
| 2 | Tests match keys; `config.py` line refs (31-56, 78-190) match current code; `write_config` exists in `tests/test_config.py`; `Refused.refusal` exists for `refused()`. Plan's test sketch for the single-root case names no mounted pin fixture: implementer builds one (a mounted pin whose root holds a corpus). |
| 3 | Kernel `Transport`, `TransportAbandoned`, `transport_files`, `local_listing`, `Destination` exist as named; "the sibling" is `<corpus_id>.head-artifact.v1` (transport_files). Test sketches omit `monkeypatch` params and fixture definitions (`remote`, `dest`, `files`, `bare`): sketches, not contradictions. |

Rulings:

- Ruling R1: Task 1's `test_replay_applies_lines_in_time_order_across_sessions` is written now as a strict xfail whose body states the intended assertions; its `fake_ledgers` fixture cannot write sharing lines until `beliefs-f24fe9` lands, so the xfail fails on `replay`'s NotImplementedError (or on the missing kernel line type) and Task 4 rebuilds the fixture through the real door — the plan's step 3 deferral covers this — cost if wrong: Task 4 rewrites one test fixture.
- Ruling R2: this session stops after Task 3 and parks sci-13050a `--reason dependency` on beliefs-f24fe9 rather than implementing the kernel task here — the plan's Global Constraints say a task that reaches a missing door parks naming it, and beliefs-f24fe9 is a planned kernel task in another repository — cost if wrong: the milestone waits on the kernel task being scheduled.

## Progress

Setup: baseline just test 694 passed (bdcef24). Task 1: BASE 8640883
Task 1: implementer DONE_WITH_CONCERNS at 5edd991 (17 passed, 1 strict xfail; test-fast 711 passed). Concern checked: 32-lowercase-hex ids match kernel _require_lower_hex(…, 32). Note: python/uv.lock drift (revision 3->5, uv re-render) from uv sync, pre-existing tool drift, left uncommitted.
Task 1: review (claude-code/claude-sonnet-5-5): spec compliant, approved; 0 Critical, 0 Important, 5 Minor.
Task 1: minor (deferred): _read_all loses the entry name on OSError from read_text (sharing.py:214)
Task 1: minor (deferred): pin/binding files are not checked to match their corpus_id/world filename (orphan risk)
Task 1: minor (deferred): pin()/binding_for_location() re-read the whole directory per call
Task 1: minor (deferred): malformed-pin case '{"version":1,"corpus_id":"short"}' fails on missing world before the hex check; add a case isolating the id-format branch
Task 1: minor (deferred): write_binding's merge (keeps bound_since, ORs confirmed) is untested
Task 1: ⚠️ SharingLine Protocol is a stand-in; Task 4 checks field names/types against the kernel class.
Task 1: complete (commits 8640883..5edd991, review clean)
Task 2: BASE 550f4e1
Task 2: implementer DONE_WITH_CONCERNS at 780ba7e (48 passed; test-fast 404 passed). Concerns: implementation written before tests (RED shown by stashing); mount tests use a minimal corpus.yaml file; write_root-in-union check unreachable.
Task 2: review (claude-code/claude-sonnet-5-5): spec compliant, approved; 0 Critical, 0 Important, 7 Minor (one labelled plan-mandated).
Task 2: Ruling: keep the unreachable `write_root not in corpus_roots` check after the union (config.py:189-190), which the reviewer flagged as plan-mandated dead code — the plan's Interfaces text requires the check, it guards the invariant if the union ever changes to replace roots, and it costs nothing at runtime — cost if wrong: one dead line, removed when the plan is next revised.
Task 2: ⚠️ resolved: no test loads a real corpus through a mount yet; Task 5's two-installation fixture and Task 8/12's adopt->mount path exercise it (owned there).
Task 2: ⚠️ resolved: max_bytes 0 means "no bound" under policy "fetch" (spec line 541; Task 9 maps 0 to sys.maxsize).
Task 2: minor (deferred): missing-root test assertion is satisfied by the path alone; assert the corpus id separately (test_config_sharing.py:344)
Task 2: minor (deferred): a nonexistent sharing_root directory loads as an empty registry (intended for first run; typo risk)
Task 2: minor (deferred): fetch-table error message "missing policy: False, unknown []" is awkward (config.py:118-119)
Task 2: minor (deferred): only the absent-directory case of a missing mounted root is tested, not a directory without corpus.yaml
Task 2: minor (deferred): implementation preceded tests (RED shown by stash) — process note
Task 2: complete (commits 550f4e1..780ba7e, review clean)
Task 3: BASE a147d18
Task 3: implementer DONE at dced046 (16 passed). Notes: fixed rejected-first-push leaving a local commit on an unborn remote; fetch_corpus overwrites an existing into/<cid>.
Task 3: review (claude-code/claude-opus-5-5): spec compliant; needs fixes — 0 Critical, 2 Important (I1 stale origin ref without --prune -> false verified-complete listing and silent non-push; I2 fetch_corpus path traversal from remote tree names), 6 Minor.
Task 3: minor (deferred): many GitTransportFault messages from _run lack the locator (transport_git.py:125, :165)
Task 3: minor (deferred): push(dest, {}) raises bare StopIteration; corpus_id taken from first name unchecked (:87)
Task 3: minor (deferred): unborn-remote path clears the index only when a local HEAD exists (:148-151)
Task 3: minor (deferred): GIT_ENV HOME mkdtemp never removed (commons.py:217)
Task 3: minor (deferred): make() unused `bare` param; test_test_env_isolates_git_from_the_host near-tautological (plan-mandated; real isolation shown by the injected-object-dir test)
Task 3: minor (deferred): allowlist lacks proxy vars and DBUS_SESSION_BUS_ADDRESS/XDG_RUNTIME_DIR for keyring credential helpers (plan-mandated list; portability)
Task 3: Ruling: the GIT_PASSTHROUGH allowlist stays exactly as the plan lists it this round (proxy and keyring variables not added) — the plan's list was reviewed over six rounds, git's http.proxy config still applies, and this host's helpers need neither — cost if wrong: a push through a keyring-backed helper or env-only proxy fails until the list grows; logged as a deferred minor for the final review.
Task 3: fix round 1/5 (2 addressed, 0 open — I1 fetch --prune + deleted-branch test; I2 _sync converts git's reset refusal of hostile entries to GitTransportFault naming the locator, _names/resolve checks as defence in depth; commits dced046..2b5fec9; re-review claude-code/claude-sonnet-5-5)
Task 3: minor (deferred): _names component check and fetch_corpus resolve check are not reached by any test (git's reset refuses first)
Task 3: minor (deferred): every reset --hard failure in _sync reports "remote tree refused", including local I/O failures
Task 3: complete (commits a147d18..2b5fec9, review clean)
Stop: Tasks 4-13 blocked on beliefs-f24fe9 (todo); per Ruling R2, sci-13050a parked --reason dependency. Resume at Task 4 (sci-f31dfa) once beliefs-f24fe9 lands.

## Session 2026-10-23: resumed (beliefs-f24fe9 merged at beliefs b923277, relayed by the beliefs session, verified)

- Ruling R3: amended the plan's Interfaces blocks for Tasks 4, 6, 7, 8 to the built kernel names (bc068a7): record_sharing(evidence, *, transition, verdict) with a 7-field SharingEvidence; restore door is restore_root(root, …) and checks layout/evidence/capture before its act, so adopt's layout refusal now deletes the copy with no pin (was: pin stays fetched); preview takes own_pins and raises PublicationRefused (closure-incomplete etc.) instead of returning closure_missing, so publish-preview's closure section reads "complete"; Task 1's SharingLine stand-in is replaced by the kernel class in Task 4 — the plan's Kernel dependency constraint authorises Interfaces+code changes without design change, and each change follows the kernel's recorded amendment — cost if wrong: one task's handler order or report section reworked.

Pre-flight scan, Tasks 4-13 (against the amended Interfaces):

| Pair | Produces / consumes | Found |
|---|---|---|
| 4 -> 7, 8 | PinBlock/pin_block, _invoke_sharing (refusal after sharing lines allowed), audit_sharing_report | consistent |
| 4 -> 1 | replay goes live over LedgerReader.sharing(); xfail removed; stand-in Protocol replaced | consistent after R3 |
| 5 -> 6..12 | Installations, build_* builders returning snapshot-storable dicts, with_remotes, read_rig, reopen | consistent; 6/7/8/11/12 each extend helpers/commons.py in sequence |
| 6 -> 7, 8, 10, 12 | publication.py marker_of/marker_fields/artifact_identity/binding_fields/transport_for, build_published | consistent |
| 7 -> 8 | publication.inspect, build_bound, bindings written after the bound line | consistent |
| 8 -> 9, 10, 11 | build_adopted/build_reopened, mounted pin with source | consistent |
| 9 -> 11, 12 | fetch command used by build_verified and the reproduce test | consistent |
| 10 -> 11, 12 | acceptance_inputs/counts/explain; belief's acceptance section | consistent |
| 6 -> 13 / 1-12 -> 13 | Task 13 amends spec/framework docs for Deviations 1-9 | consistent |

| Task | Self-consistency |
|---|---|
| 4 | tests and Interfaces agree after R3; probe evidence must satisfy the kernel's field validation (noted in the plan) |
| 5 | consistent; v3 coordination profile for both installations |
| 6 | after R3 the closure KeyVals carries only "complete"; test_preview names "closure" still holds |
| 7 | consistent |
| 8 | after R3 step 7 is the door's; test_adopt_unsourced etc unchanged; no test exercises a layout refusal — consistent with plan's list |
| 9 | consistent; max_bytes 0 = no bound |
| 10 | belief_input_digest changes once a policy is always supplied: existing digest assertions are updated, not weakened (plan says) |
| 11, 12, 13 | consistent |
Task 4: BASE 44d9ed8
Task 4: implementer DONE_WITH_CONCERNS at 7b9767a (108+110 passed; test-fast 599 selected, 1 fixed). Concerns: audit accepts an in-order subset of lines; replay of finished invocation reads live session list; touched test_canonical.py (code count 13->16) and helpers/synthetic.py; replay test uses kernel LedgerWriter directly.
Task 4: review (claude-code/claude-opus-5-5): spec compliant; needs fixes — 0 Critical, 2 Important (I1 replay raises on LedgerMissing/LedgerEmpty sessions the kernel treats as harmless; I2 kernel-exception tuple duplicated between _invoke_write and _invoke_sharing), 5 Minor. Audit subset reading accepted by reviewer; replay-from-live-index sound.
Task 4: minor (deferred): refuse-path HandlerContractViolation message interpolates the raw exception, not the code (dispatch.py ~340)
Task 4: minor (deferred): empty source renders "source: " with trailing space (report.py ~96)
Task 4: minor (deferred): pin_block/audit_sharing_report params untyped
Task 4: minor (deferred): redundant sorted() over session directories in replay
Task 4: minor (deferred): replay test's _write_session hardcodes kernel ledger line dicts (LedgerWriter validates; noted)
Task 4: fix round 1/5 (2 addressed, 0 open — replay via read_ledger_evidence skipping Missing/Empty, SharingLedgerUnreadable on Unreadable; one KERNEL_REFUSALS tuple, _close_acted shared; commits 7b9767a..57dac26; re-review claude-code/claude-sonnet-5-5)
Task 4: complete (commits 44d9ed8..57dac26, review clean)
Task 5: BASE d429dbc
Task 5: Ruling: create a minimal science/publication.py in Task 5 holding only the REMOTE_FOR and GIT_ENV seams, so with_remotes has real seams to set and restore; Task 6 fills in the rest — the plan's Task 5 helper with_remotes sets seams that Task 6's Interfaces define, an ordering gap in the plan — cost if wrong: Task 6 moves two lines.
Task 5: implementer DONE_WITH_CONCERNS at 5c81fa7 (11 passed; test-fast 384; build ~6.2s). Concerns: A's dataset held as data.txt (shared Snakefile reads inputs/data.txt); PROFILE_V3=PROFILE+contract compiled per installation; project minted via project command with QUERY_1A; pytest fixtures live in the test file.
Task 5: review (claude-code/claude-sonnet-5-5): spec compliant; needs fixes — 0 Critical, 1 Important (I1 fresh/fresh_value/fresh_no_epoch fixtures live in the test module, invisible to Tasks 6-12's test files; move to conftest), 5 Minor. Deviations 1-3 accepted.
Task 5: Ruling: accept the implementer's deviations — A's dataset declared as data.txt (the shared Snakefile reads inputs/data.txt; data_dir()/a.txt supplies the bytes, fetch checks declared digest/name), project minted through the project command (mint_project hardcodes its query), PROFILE_V3/PINS_V3 without the contract (a module constant cannot load the contract file) — each keeps the brief's behaviour and the reviewer accepted them — cost if wrong: Tasks 9/11 adjust a file name.
Task 5: minor (deferred): pin derivation written twice (PINS_V3 vs build_installation); PINS_V3 name implies installation pins
Task 5: minor (deferred): data_a_path docstring should say the dataset is declared as data.txt
Task 5: minor (deferred): Task 6 must read publication.REMOTE_FOR/GIT_ENV at call time (carry into Task 6 dispatch)
Task 5: minor (deferred): commons helpers import private _install_holdings_reducer/_list_address/_minted_ref from helpers.world
Task 5: fix round 1/5 (2 addressed, 0 open — fixtures moved to conftest; data_a_path docstring; commits 5c81fa7..6e37326; re-review claude-code/claude-haiku-5-5)
Task 5: complete (commits d429dbc..6e37326, review clean)
Task 6: note: ops checkout main holds another session's uncommitted work (tasks/ops-df9e86.md, r2/); CLI-row commits in ops are pathspec-limited to cli.toml per the plan's Global Constraints, so that work is untouched.
Task 6: BASE a85faa3

## Session 2026-10-23 (b): resumed after the controller session 3f86999b was stopped by the user at 14:59:19Z

- Controller claude-code/claude-opus-5-5 (session 7f485a). Took over sci-13050a and sci-2e30eb (stale claim: pid 1994241 gone). Trial arm: not enrolled.
- Task 6 state at takeover: implementer a47ca45 killed with the session; no report file, no science commit. ops deac725 "feat(cli): science publish and publish-preview rows" is committed; the adopt ran (tools/cli.toml, tools/cli_surface.py modified). Uncommitted in the tree: publication.py, commands/publish{,-preview}/, commands/publish{,_preview}.py, test_cmd_publish.py, helpers/commons.py, conftest.py (published fixture), adapters/claude-code/skills/publish{,-preview}/. python/uv.lock drift stays uncommitted (sci-124072 owns the re-lock).
- Task 6: BASE a85faa3 (unchanged); a fresh implementer completes the in-tree work.
Task 6: implementer (fresh, claude-code/opus) af18c5d dispatched over the inherited draft
Task 6: implementer DONE_WITH_CONCERNS at 3a112e7 (step 4: 54 passed; test-fast 120; just check 0). Concerns: report reads the binding by the returned id, not binding_address (resume has no view); extra no-epoch/stale-corpus handling+tests beyond the brief; ops deac725 unpushed.
Task 6: review (claude-code/claude-opus-5-5): spec compliant, approved; 0 Critical, 0 Important, 6 Minor. Both deviations judged sound against the kernel.
Task 6: Ruling: accept the implementer's two departures from the brief — the publish report reads the binding by Published.binding instead of binding_address(view, destination) (the resume path resolves no view), and both commands map EpochUnknown/SelectionRefused (corpus-drifted names `science epoch`) to no-epoch/kernel-refused (neither is in KERNEL_REFUSALS, so they would otherwise escape dispatch) — the reviewer verified both against the kernel — cost if wrong: the report lookup changes in one line; two extra refusal branches removed.
Task 6: minor (deferred): no-epoch message text repeated verbatim in publish.py:45, publish_preview.py:23 and world_belief.py:70; export one constant beside REMEDY
Task 6: minor (deferred): publish.py:52 control-flow `assert type(outcome) is Published`; use an explicit raise
Task 6: minor (deferred): resume ignores target and uses to only for the transport; a mismatch fails safe as a generic kernel-refused (ValidationRefused)
Task 6: minor (deferred): untested branches: local absolute-path publish (transport_for None), preview attribution KeyVals, preview closure-incomplete naming refs, http:// destination as invalid-input
Task 6: minor (deferred): marker_fields reads attributions with .get(..., []), so a v2 marker without the field reads as v3 with none (explicit > defensive)
Task 6: minor (deferred): preview SelectionRefused refusal data carries kind/reason only, refs only in the message
Task 6: minor (deferred): ops deac725 (publish rows) is committed on ops main, not pushed
Task 6: complete (commits a85faa3..3a112e7, review clean)
Task 7: BASE 1235396
Task 7: implementer (claude-code/opus) adc9b28 dispatched
Task 7: implementer DONE_WITH_CONCERNS at 4a5f95e, ops b58206c (12 passed; step 4 59; test-fast 795). Concerns: local-path location refuses invalid-input; ObserverCarrierInvalid/PublicationArrivalRefused -> invalid-input naming the location (untested); line/binding record canonical destination.locator; inspect refuses an existing scratch dir.
Task 7: review (claude-code/claude-opus-5-5): spec compliant, approved; 0 Critical, 0 Important, Minor 3 + cross-task notes. All four implementer rulings judged sound.
Task 7: Ruling: a local-path provider location refuses invalid-input — milestone 1a is "over git" (spec §12) and adopt fetches only through fetch_corpus, so a local provider has nothing to adopt from; spec §3 allows a local path, so Task 13 records the narrowing among the Deviations — cost if wrong: local providers need a fetch path in 1b.
Task 7: Ruling: ObserverCarrierInvalid and PublicationArrivalRefused from inspect refuse invalid-input naming the location — both mean the location holds no valid publication, which the prompt already promises; unmapped they would crash dispatch — cost if wrong: a different code for two rare refusals.
Task 7: Ruling: the bound line and the binding record the canonical destination.locator, not the raw input — binding_for_location matches strings exactly, so a raw spelling would make a binding a canonical lookup misses — cost if wrong: none found; Task 8 must canonicalize (carried into its dispatch).
Task 7: Ruling: inspect refuses an existing scratch directory (mkdir without exist_ok) — dispatch makes registry.scratch(iid) fresh by construction and inspect uses a random token, so the error is a loud assertion — cost if wrong: scratch left by a SIGKILL is never reclaimed.
Task 7: minor (deferred): local-path refusal lacks {"location"} data and quotes with !r unlike the other location refusals; fires after replay rather than beside parse_destination (publication.py:159-162)
Task 7: minor (deferred): inspect's non-validated-verdict, ObserverCarrierInvalid and PublicationArrivalRefused branches untested; absent-corpus test does not assert r.data
Task 7: minor (deferred): absent-corpus message names the location twice (GitTransportFault already starts with it) (publication.py:171)
Task 7: minor (deferred): publication.py:133 repeats sharing.py:23's _ID_RE; expose one require_id
Task 7: minor (deferred): provider-bind adds a location already bound to another world to a second binding; binding_for_location returns whichever comes first (sharing.py:219-229) — undecided by the brief; Task 8's world-mismatch reads that lookup
Task 7: minor (deferred): Deviation 9 says provider scratch is under operations_root; provider-bind's is under sharing_root (registry.scratch) — Task 13 aligns the text
Task 7: complete (commits 1235396..4a5f95e, review clean)
Task 8: BASE 9b0a056
Task 8: Ruling: adopt canonicalizes its `location` input through publication.parse_destination before any use, and uses destination.locator for binding_for_location, the fetched-pin location comparison, PinSource and SharingEvidence.location; a non-remote location refuses invalid-input as provider-bind does — Task 7 records bindings under the canonical locator and the registry matches strings exactly, so the brief's raw-location lookups would refuse pin-unsourced on a non-canonical spelling — cost if wrong: none found; one call moves.
Task 8: implementer (claude-code/opus) dispatched
Task 8: implementer NEEDS_CONTEXT at 628b38e, ops 3584515 (step 4: 62 passed, 1 xfailed; test-fast 810 passed, 1 xfailed). test_publish_before_reopen_refuses_selection_incomplete cannot pass: the kernel raises selection-incomplete only for corpora the epoch covers without a carrier (beliefs publish.py:345-347, world/view.py:341); an epoch built before reopen covers only the session's mounts, so the adopted corpus is live-but-uncovered and B's publish succeeds.
Task 8: Ruling: (a) accept the kernel's selection semantics — before reopen B's publish freezes B's own view over B's current epoch, which cannot contain records derived from the unmounted adopted corpus, so the publication is honest; the xfail becomes a test of the actual behaviour (publish before reopen succeeds and its marker selects none of A's addresses), the adopt prompt drops the selection-incomplete claim and keeps "takes effect at the next open", and Task 13 records Deviation 10 amending spec §4.3 step 3 and the §10 point 3 rationale sentence; (b) a science-side guard was rejected as inventing a refusal the kernel does not define, (c) a kernel change is outside this plan — cost if wrong: a later science guard or kernel change restores the refusal; a beliefs question task is filed at the end ("an admitted corpus absent from session mounts is silently uncovered by every epoch: intended?").
Task 8: implementer DONE at f06c6aa after the ruling (step 4: 63 passed; test-fast 15 selected passed). Open choices for review: head artifact kept at roots/<cid>.head-artifact.v1; download-time layout refusal is invalid-input via a download helper shared with inspect; SharingEvidenceDisagrees data key 'field'; conflicting_publication standalone fixture; publication.py/sharing.py touched beyond the file list.
Task 8: review (claude-code/claude-opus-5-5): spec compliant against the brief as amended by both rulings; approved; 0 Critical, 0 Important, 7 Minor. Step order checked step by step.
Task 8: Ruling: accept the implementer's open choices — head artifact kept at roots/<cid>.head-artifact.v1 (a pin stores only the hash; removed with the copy; nothing enumerates roots/), a layout failure found while downloading refuses invalid-input through the download helper shared with inspect (the door's own PublicationArrivalRefused stays kernel-refused), SharingEvidenceDisagrees data keyed by `field`, conflicting_publication a standalone fixture, small publication.py/sharing.py changes beyond the file list — the reviewer verified each against the kernel and the registry — cost if wrong: one refusal code or one path helper changes.
Task 8: minor (deferred): sharing.py:237 hardcodes ".head-artifact.v1" duplicating transport_git._HEAD_SUFFIX
Task 8: minor (deferred): test_publish_before_reopen_freezes_only_bs_own_view does not assert its mechanism (B's epoch coverage excludes the adopted corpus); add the coverage assertion before Task 13 writes the behaviour into the spec
Task 8: minor (deferred): adopt maps only WriteRefused from admit_publication; ArrivalRefused passes through and is not in KERNEL_REFUSALS (likely unreachable after a validated evaluate_copy; line.verdict not checked)
Task 8: minor (deferred): untested branches: world-mismatch, non-validated copy, door refusal + discard, admit refusal leaving fetched, reconcile of a fetched pin the kernel already admitted; the report's self-review overstates this coverage
Task 8: minor (deferred): adopt prompt says "reopen (and capture an epoch)" without naming the `epoch` command
Task 8: minor (deferred): SharingEvidenceDisagrees refusal data drops claimed/found
Task 8: minor (deferred): a retired pin refuses "already adopted"; the brief is silent on retired (Task 13 spec pass)
Task 8: minor (deferred): ops 3584515 (adopt row) committed, not pushed
Task 8: complete (commits 9b0a056..f06c6aa, review clean)
Task 9: BASE b02b764
Task 9: implementer (claude-code/sonnet) dispatched
Task 9: implementer DONE_WITH_CONCERNS at 89eac88, ops 956c8ef (57 passed; test-fast selected 0). Concerns: tests written after the handler (RED shown by removing the module); purpose aligned to the cli.toml summary.
Task 9: review (claude-code/claude-sonnet-5-5): spec compliant, approved; 0 Critical, 0 Important, 9 Minor. All checks precede the one act; scratch file unlinked on every exit.
Task 9: minor (deferred): digest-mismatch tests may pass on the kernel's expected= check alone; spy on write to pin the handler's own check
Task 9: minor (deferred): "writes nothing" judged only via held_path; assert holdings-observation count unchanged
Task 9: minor (deferred): untested refusals: multi-resource, missing digest, relative path, non-regular file, NotAttempted, nonzero max_bytes passed to URL bounds
Task 9: minor (deferred): unlink not tested on read error or URL max_bytes refusal (code covers both)
Task 9: minor (deferred): scratch/fetch/<iid> directory left behind (fetch.py:25-26)
Task 9: minor (deferred): path source read fully before the max_bytes check; stat pre-check optional (brief orders it)
Task 9: minor (deferred): holdings_observation_value evaluated twice per node (fetch.py:63-67); test import order; unused tmp_path
Task 9: minor (deferred): tests written after the handler (RED shown retroactively); test-fast selected 0 tests
Task 9: minor (deferred): ops 956c8ef (fetch row) committed, not pushed
Task 9: complete (commits b02b764..89eac88, review clean)
Task 10: BASE 23b8a39
Task 10: implementer (claude-code/opus) dispatched
Task 10: implementer DONE_WITH_CONCERNS at a42e917 (step 4: 44 passed; test-fast 71; just test 834 passed). Concerns: accept-A test cannot show a Belief (A's assessment unverified; Task 12 territory); inputs read ctx.mounts() not session_mounts(); next.py _assessed counts only accepted assessments (+test); belief's read families unchanged though it reads the registry; inputs not cached.
Task 10: review (claude-code/claude-opus-5-5): spec compliant; needs fixes — 0 Critical, 2 Important (I1 a hand-listed root claiming a pinned corpus id takes that pin's standing: carriers dict keyed by corpus id, branches 4/5 check neither address-in-selection nor marker==pin.marker; I2 plan-mandated branch 3: (a) an attribution naming an intermediary that itself carries the address counts, (b) address-only selection check does not tie B's copy to A's content), 4 Minor. Implementer's 5 concerns judged acceptable.
Task 10: Ruling: I1 is fixed — branches 4 and 5 additionally require `address in carrier.selection` and `carrier.marker == pins[corpus_id].marker`, and acceptance_inputs refuses invalid-input naming both roots when two mounts share a corpus id and either is a carrier or pinned (the kernel's (corpus_id, address) cannot say which root a record came from); markerless unpinned duplicates keep config.py's existing behaviour — amends the brief's branch conditions, which only tightens them: honest roots satisfy the conjuncts because require_publication_layout makes a root's content equal its selection — cost if wrong: a legitimate duplicate-id configuration with a marker refuses belief reads until the rule is relaxed.
Task 10: Ruling: I2a is fixed — branch 3 additionally requires `address not in carriers[origin].attributions` (the named origin must hold the record as its own) — spec §4.8 copies the first origin forward, so an honest marker never names an intermediary — cost if wrong: a carried-forward attribution written by an older marker format would stop counting.
Task 10: Ruling: I2b is deferred to 1b — branch 3 keeps the plan's address-only selection check; a per-address content identity on Carrier changes the plan's interface, and in 1a world reads refuse one address in two corpora (Deviation 3), so substitution reaches only corpus-local reads with origin and carrier both configured; beliefs-81367e (1b) lifts that limit and must bring content identity with it; Task 13 files the follow-up — cost if wrong: a corpus-local read can count substituted content under an accepted origin's address.
Task 10: minor (deferred): acceptance inputs computed twice per belief and per proposition in next; explain may not describe the exact predicate the kernel used; cache on ReadContext (M1)
Task 10: minor (deferred): acceptance.py:44 comment says session mounts; code reads every configured mount (M2)
Task 10: minor (deferred): explain's "excluded {address}" keys omit the corpus and can collide (M3)
Task 10: minor (deferred): no test of a hand-listed marker-carrying root becoming a carrier, nor of the malformed-marker invalid-input refusal (M4)
Task 10: fix round 1/5 (2 addressed, 0 open — I1 branches 4/5 require address in carrier selection and marker==pin.marker, duplicate carrier/pinned corpus ids refuse invalid-input naming the roots; I2a branch 3 requires the origin to hold the address as its own; commits a42e917..5954a8c; re-review claude-code/claude-sonnet-5-5)
Task 10: minor (deferred): a path listed twice in corpus_roots would form a duplicate group and refuse belief reads if it carries a marker (WorldConfig dedupe unchecked)
Task 10: complete (commits 23b8a39..5954a8c, review clean)
Task 11: BASE 3aae480
Task 11: implementer (claude-code/opus) dispatched
Task 11: implementer DONE at d0a13ce, ops 56fc3e6 (step 4: 57 passed; test-fast 847). verify ran (host_prerequisites None). Confirmation mapping: origin-confirmed = pin.origin_confirmed; recommended = catalog source; unsourced = none or unbound provider.
Task 11: review (claude-code/claude-opus-5-5): spec compliant, approved; 0 Critical, 0 Important, 4 Minor (one plan-mandated). Confirmation mapping agrees with spec §4.4 item 4 (not §4.5) for provider and catalog sources.
Task 11: Ruling: the plan-mandated POLICY=MINIMAL_POLICY monkeypatch in build_verified stays for now and goes to the final review as a deferred minor — it is inert (verify never reads run.POLICY) but harmless, and removing it means amending the plan's fixture text in Task 13 — cost if wrong: one misleading docstring sentence until removed.
Task 11: minor (deferred): a list-recommended provider source (binding confirmed=False) would read `unsourced`, against spec §4.4's "followed catalog or list" (unreachable in 1a: both binding writers set confirmed=True); recommended/unsourced untested
Task 11: minor (deferred): show's lag predicate (known and live, state below mounted) differs from adopt._reconcile's (kernel admissions, fetched/admitted); share one helper
Task 11: minor (deferred, plan-mandated): build_verified's POLICY monkeypatch is inert (verify imports only now, prepare from run); docstring describes nothing
Task 11: minor (deferred): untested branches: unset sharing_root, n/a acceptance row, "assessments: none", non-publication holder refusal
Task 11: minor (deferred): ops 56fc3e6 (show row) committed, not pushed
Task 11: complete (commits 3aae480..d0a13ce, review clean)
Task 12: BASE 0182e63
Task 12: implementer (claude-code/opus) dispatched
Task 12: implementer DONE_WITH_CONCERNS at 5ea3dc2 (5 passed, 110.7s cold / 60.3s warm; test-fast 852). Concern: belief cannot flip NoBelief->Belief: B's verification of A's assessment is same-environment (A's run minted under the minimal policy by the portable fixture), the kernel admits only clean-environment passes; the test asserts exclusion line, gathered assessments and verification presence per policy instead.
Task 12: Ruling: the belief decisive case is met by asserting inputs, not a NoBelief->Belief flip — spec §12 1a says B's belief with accept=[] 'excludes A's assessments and says so in its context, and with accept=[A] includes them', i.e. inclusion in the belief's inputs; a verdict flip needs a clean-environment verification, which the portable fixture's minimal-policy run cannot give without changing the fixture chain — cost if wrong: a fixture minting A's run through run under confinement, plus one test assertion.
Task 12: review (claude-code/claude-sonnet-5-5): spec compliant (lineage, attribution, transport non-vacuous; belief case meets the ruling), approved; 0 Critical, 0 Important, 4 Minor.
Task 12: minor (deferred): reproduction test asserts only "[verification]" in text, not the verdict passed (test_commons_1a.py:60)
Task 12: minor (deferred): transport_for swapped by hand with try/finally instead of monkeypatch (test_commons_1a.py:134-147)
Task 12: minor (deferred): the "partial push" lands fully then faults; no partial file set; docstring should state the limit
Task 12: minor (deferred): tests import private _pending/_confine from other test modules
Task 12: complete (commits 0182e63..5ea3dc2, review clean)
Follow-ups filed by the controller: sci-9afbc8 (fetch URL observation, Deviation 4), sci-4a3543 (Carried content identity, 1b), sci-b979ce (clean-environment fixture for a belief flip), beliefs-79d2ce (kernel question: admitted corpus outside every epoch).
Task 13: BASE 93f95a3; controller additions in task-13-controller-additions.md (Deviations 10-12, §12 sentence, Deviation 9 wording)
Task 13: implementer DONE at a92bed0, ops dd3d8f9 (just gate: check silent, 852 passed; commit amended afterwards for text wrapping, pre-commit check passed). Departures: cli.toml header's just vendor-cli was already replaced in ops a3c0a10, so the fix names <ops checkout>/bin/vendored; Deviation 10 amended at §5 step 3 (the controller's '§4.3' citation was wrong).
Task 13: review (claude-code/claude-sonnet-5-5): spec compliant, approved; 0 Critical, 0 Important, 2 Minor. Behavioural claims spot-checked against the code.
Task 13: minor (deferred): §5 step 3 amendment says adopt's pin block names the epoch; the epoch wording is in the adopt prompt, not the report
Task 13: minor (deferred): §12 amendment states "the kernel admits only clean-environment passes" as a kernel fact; verify in the kernel or soften to "in the 1a fixture"
Task 13: minor (deferred): ops dd3d8f9 (cli.toml header) committed, not pushed
Task 13: complete (commits 93f95a3..a92bed0, review clean)
Final review: package review-632b9ea..bf74521.diff + code-only final-632b9ea..a92bed0-code.diff; dispatched (claude-code/opus) over 632b9ea..bf74521 with the deferred-minor triage
Final review (claude-code/claude-opus-5-5): with fixes — 0 Critical, 2 Important (I1 publish writes through symlinks planted in a hostile remote's tree: _sync checks out with reset --hard and _stage follows symlinks — confirmed by probe; I2 a location bound to two worlds makes adopt refuse world-mismatch by world-id sort order with a false message — confirmed by probe), 9 Minor (M1-M9). Deferred-minor triage: must fix with I1/I2 — Task 7 second-world binding, Task 8 world-mismatch untested, Task 3 hostile-tree path checks untested; cheap alongside — Task 8 ArrivalRefused, Task 6 assert, Task 2 nonexistent sharing_root; remaining 68 may stay deferred.
Final: Ruling: I1 is fixed by checking the cache out with core.symlinks=false and an lstat check refusing any symlink component of each path _stage writes (GitTransportFault naming the locator and path), with a hostile-remote test planting both symlinks — the reviewer's plumbing rewrite (bare cache, hash-object/mktree/commit-tree) was rejected for this round because it rewrites a reviewed transport; the minimal fix closes the hole — cost if wrong: M3 (global git config and remote .gitattributes) stays deferred and the transport keeps a working tree.
Final: Ruling: I2 is fixed in adopt._source by looking up the binding of the marker's world (registry.bindings().get(fields.world)) and accepting when the canonical locator is in its locations; world-mismatch only when no binding of that world holds the location, naming every world the location is bound to; provider-bind keeps allowing one location for several worlds (spec §8 containers) — cost if wrong: if one-world-per-location is wanted, provider-bind gains a refusal later.
Final: Ruling: the three triage "must fix" minors ride with I1/I2 as their tests (Task 7 binding lookup is I2's root cause; Task 8 world-mismatch test; Task 3 hostile-tree test); the "cheap alongside" minors and M1-M9 stay deferred as minors, per the corrective-round rule that minors never enter a round — cost if wrong: a nonexistent sharing_root still loads as an empty registry until fixed.
Final: minor (deferred): M1 show's "counts as evidence" judged from assessments[0] alone
Final: minor (deferred): M2 publish refuses kernel-refused(no-epoch) while publish-preview refuses no-epoch; EPOCH_CODES callers miss publish
Final: minor (deferred): M3 transport git behaviour depends on global git config (gpgsign, hooksPath, autocrlf, lfs) and remote .gitattributes
Final: minor (deferred): M4 a re-fetch of a fetched pin's vanished copy ignores the pinned artifact/marker; apply_line silently keeps the first line's fields
Final: minor (deferred): M5 ArrivalRefused, SharingLedgerUnreadable, OSError in _run/_stage escape as tracebacks
Final: minor (deferred): M6 transport cache has no lock; read-only provider-inspect shares it with publish
Final: minor (deferred): M7 adopting your own publication back is unreachable (provider-bind refuses own world)
Final: minor (deferred): M8 gather_inputs/evaluate default acceptance=None lets a future caller skip the policy
Final: minor (deferred): M9 spec §9 Dev 12 omits next among refusing reads; §10 Dev 9 list omits the restore door's kernel-refused
Final: minor (deferred): Task 13's clean-environment claim verified true (beliefs admission.py:74) — resolved
Final: fix round 1/5 dispatched (claude-code/opus); FIX_BASE bf74521
Final: fix round 1 FIX_BASE corrected to 7183b58 (HEAD after the review note commit)
Final: fix round 1 implementer DONE_WITH_CONCERNS at 9160284 (I1), fb78c9c (I2); covering 70, test-fast, just test 855 passed. Concerns: mode 120000 survives re-add with core.symlinks=false (head-artifact stored as a symlink entry; nothing written outside the cache; listing hashes unaffected); no reader-side hostile test (git refuses first); binding_for_location removed; world-mismatch data 'bound' is a sorted list.
Final: fix round 1/5 (2 addressed, 0 open — I1 core.symlinks=false on every transport git call plus _target lstat/containment refusal before staging; I2 adopt sources by the marker's world binding, world-mismatch names every bound world, binding_for_location removed; commits 7183b58..b259940; re-review claude-code/claude-opus-5-5)
Final: minor (deferred): a remote planting <cid>.head-artifact.v1 as a symlink entry makes our push store the head artifact with mode 120000 (our cat-file readers and the kernel listing unaffected; a third-party symlink checkout dangles; an idempotent re-push never repairs it); suggested fix: refuse existing index entries whose mode is not 100644/100755 before add
Final: minor (deferred): after a remote once served a plain file at <cid> and its branch is deleted, the unborn-remote rm --cached leaves the file and every later push refuses "not a directory" until the cache is cleared (fails safe)
Final: complete — final review clean after corrective round 1
