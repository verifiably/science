# `recheck` command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `science recheck --location store:<id>:<path>`, which re-checks one location in the session's bound store through `ScopedWriter.recheck` and reports the kernel's Found, Absent or inconclusive result, settling an unmatched holdings intent.

**Architecture:** A new `mints:holdings-observation,act-report` command whose handler validates the locator and the store binding, gathers standing observations from every mounted view, and calls the kernel's public re-check route. The renderer's `record_block` gains a kernel-derived detail line for holdings observations and re-check act-reports. A location in a read store is reached through a documented recovery configuration.

**Tech Stack:** Python 3, pytest via `just test-one`, the vendored ops `cli.toml`, beliefs (editable path dependency).

**Spec:** `docs/specs/2026-10-31-holdings-recheck-design.md` (accepted at f00a6ec; review round 1, gemini-4-argon).

## Global Constraints

- Command name `recheck`; module `science.commands.recheck`; instrument `"science/recheck.v1"`.
- One input, `location`, type `string`, required, not repeatable; CLI option `--location`.
- `write_class = "mints:holdings-observation,act-report"`; `[write.routes]` `holdings-observation = "holdings"`, `act-report = "corpus-write"`; `[reads] families = ["corpus-stored", "holdings"]`; `output_budget = 2048`.
- Use only `ScopedWriter.recheck` and other public beliefs names; never `ScopedWriter._writer` or session seams in product code.
- Validate before the first act: every handler refusal is raised before `writer.recheck`.
- Never label the command read-only; never assume Absent.
- `tools/cli.toml` changes only by `bin/vendored adopt cli.toml` from a commit already on ops `main`.
- Tests: `just test-one <pytest args>` while working, `just test-fast` before each commit (no `.tt.toml`: policy enabled). Never call pytest directly. Subprocess tests build their environment key by key.
- Committed text carries no machine-specific absolute paths.

## Review Focus

1. A locator pasted with surrounding whitespace or a trailing newline: expected `invalid-input`, never a re-check of a different path (Task 2 test `test_padded_location_refuses`).
2. A store id copied in upper case: expected `invalid-input` naming the identity rule (Task 2, `test_malformed_location_refuses` case `uppercase-id`).
3. Re-checking the same location twice: the second observation supersedes the first and the location has one head (Task 2, `test_second_recheck_supersedes_the_first`).
4. A retry with the same `--invocation-id`: replays the first report and does not re-check (Task 3, `test_replay_renders_the_same_detail`).
5. A path nobody ever wrote: the re-check publishes Absent with no refusal, by design (Task 2, `test_never_written_location_reads_absent`).

---

### Task 1: Declare the `recheck` row in ops

**Files (ops repository, its own worktree):**
- Modify: `cli.toml` (the `# ---- science` section, after the `fetch` row)
- Test: `tests/test_cli.py` only if ops' existing per-row checks require an entry (follow 9d07bfe's pattern)

**Interfaces:**
- Produces: an ops `main` commit whose `cli.toml` carries the row below, for Task 2's adopt.

- [ ] **Step 1: Create an ops worktree** per the global Git rule (`work-link --ensure .worktrees` if it applies, `git worktree add -b feat/science-recheck-row .worktrees/science-recheck-row main`, lock it, `just setup`).
- [ ] **Step 2: Add the row**

```toml
[[cli.science.commands]]
path = ["recheck"]
summary = "Re-check one store location and record what the store holds there, settling an unmatched holdings intent"
options = [
  { shared = "config", value = "path" },
  { names = ["--invocation-id"], value = "string" },
  { names = ["--continue"], value = "string" },
  { names = ["--location"], value = "string", required = true },
]
```

- [ ] **Step 3: Run ops' table checks:** `just test-one tests/test_cli.py tests/test_cli_surface.py tests/test_vendored.py`. Expected: PASS.
- [ ] **Step 4: Commit** in the ops worktree: `feat(cli): declare science recheck (sci-409235)`; then `just test-fast` per ops' guide.
- [ ] **Step 5: Integrate locally:** merge the branch into ops `main` in the ops main checkout (no push), confirm `git log -1 -- cli.toml` on `main` shows it, then unlock and remove the ops worktree after its ignored-file check and `tt-report`. Note the ops merge commit on sci-409235.

### Task 2: The command and its handler

**Files:**
- Modify: `tools/cli.toml` (adopted, not edited)
- Create: `commands/recheck/command.toml` (the spec's declaration verbatim), `commands/recheck/prompt.md`
- Create: `python/src/science/commands/recheck.py`
- Create: `adapters/claude-code/skills/recheck/SKILL.md` and any other generated files (regenerated, not hand-written)
- Modify: `README.md` (add `recheck` to the belief-path command list)
- Test: `python/tests/test_cmd_recheck.py`

**Interfaces:**
- Consumes: Task 1's ops `main` commit.
- Produces:
  - `parse_store_location(text: str) -> StoreLocator`: raises `Refused(Refusal("invalid-input", ...))`.
  - `standing_at(views, locator: StoreLocator) -> tuple[HoldingsObservation, ...]`: every `holdings-observation` at `locator.canonical()` across `views` (`ctx.read_views()` pairs), deduplicated by `identity()`, sorted by identity.
  - `handle(ctx, writer, *, location: str) -> Report`.
  - Test helper in `test_cmd_recheck.py`: `refused_write(cfg, work, tmp_path) -> tuple[ScienceConfig, str]`, which runs `dataset` against a restored read-only-serviceable replica bound as `store_root` (as `test_cmd_dataset.py::test_a_store_refused_write_closes_refused_and_replays` does) and returns that config and the canonical location left unsettled (`store:<id>:<sha256 hex>/<file name>`). Also `blocked_reasons(cfg) -> dict[str, list[str]]`, reading `science.holdings.reduced_heads(ctx.world, all read-view corpus ids)` blocked rows by `location`. Tasks 3 and 4 import both.

- [ ] **Step 1: Adopt the table:** `python3 <ops checkout>/bin/vendored adopt cli.toml` (ops checkout from `tasks root` or `tasks projects --paths`). Expected: `tools/cli.toml` gains the row (and other tools' landed rows); `git diff tools/cli.toml` shows no change to other science rows.
- [ ] **Step 2: Write failing tests** in `python/tests/test_cmd_recheck.py`, each through `open_rig(cfg, ("dataset", "recheck"))`:
  - `test_recheck_settles_a_refused_write`: after `refused_write`, `blocked_reasons(cfg)[location] == ["unsettled"]`; a second location held normally by `dataset` is not blocked. Invoke `recheck` with `{"location": location}` under the same config. The minted records are one `holdings-observation` whose `stored.holdings_observation_value(node).outcome` is `Absent()` at `location`, and one `act-report` with `stored.act_report_facet(node)["operation"] == "re-check"`. Afterwards `location not in blocked_reasons(cfg)`, and the other location is still unblocked with its head unchanged.
  - `test_recheck_finds_held_bytes`: on a location `dataset` held, the observation's outcome is `Found("sha256:<digest of the bytes>")` and its `supersedes` holds the earlier observation's identity.
  - `test_second_recheck_supersedes_the_first`: two re-checks at one location leave exactly one active head, the second observation.
  - `test_inherited_head_is_superseded` (uses `test_stores.py`'s `relocated_store` approach, re-check under the recovery configuration of Task 4's shape: `store_root` the restored store, `read_store_roots` the fresh one): a head at the location in a mounted read corpus appears in the new observation's `supersedes`, and the location is not `contested`. If the fixture world mounts only one corpus, build the second mount the way `coordination_rig`'s fixtures do.
  - `test_never_written_location_reads_absent`: `store:<bound id>:never/written.txt` publishes Absent, no refusal.
  - `test_inconclusive_read_keeps_the_block`: after `refused_write`, inject a `ReadUnestablishedView` by monkeypatching `beliefs.root._store_read_path` before the rig opens (verify the session's seam captures it; if not, patch the inner seam's member the way `beliefs/tests/test_holdings_recheck.py` builds its fake seam). The invocation closes `done` with one `act-report` whose single entry's outcome kind is `retrieval-failed`, no new observation, and `blocked_reasons(cfg)[location] == ["unsettled"]`.
  - `test_malformed_location_refuses`, parametrized: `""`, `"store:"`, `"store:abc:x.txt"`, `uppercase-id` (`"store:" + "A" * 32 + ":x.txt"`), `"store:<bound id>:../escape"`, `"store:<bound id>:/abs"`, `"url:https://example.org/x"`, `"https://example.org/x"`. Each refuses `invalid-input`; `session.invocation_acts(iid)` is empty and the write corpus chain length is unchanged.
  - `test_padded_location_refuses`: `" " + location` and `location + "\n"` refuse `invalid-input` with no act.
  - `test_unconfigured_store_refuses`: a well-formed locator naming a fresh `uuid4().hex` refuses `invalid-input`; the message names the configured identities.
  - `test_read_store_location_refuses_with_the_route`: under a config with a read store, a locator in the read store refuses `invalid-input`; the message names that root and the words `store_root` and `read_store_roots`.
  - `test_insufficient_permit_refuses_before_the_handler`: a session opened with a permit lacking `holdings` (or `corpus-write`) refuses `permit-exceeded` and appends no `invocation-open` (follow the existing permit-refusal tests in `test_dispatch_refusals.py` and `test_dispatch.py`).
- [ ] **Step 3: Run** `just test-one tests/test_cmd_recheck.py`. Expected: FAIL (unknown command `recheck`).
- [ ] **Step 4: Write the declaration and prompt.** `command.toml` is the spec's block verbatim. `prompt.md` (agent-facing, in the style of `commands/fetch/prompt.md`): when to run it (a location blocked `unsettled` after a refused or interrupted holdings write), the `store:<id>:<path>` spelling taken from the blocked row, that it settles only intents in this configuration's `write_root`, that a live world re-check needs the person's authorization, how to read Found, Absent and inconclusive, and that a refusal changes nothing.
- [ ] **Step 5: Implement `recheck.py`.** `parse_store_location`: refuse anything not of the form `store:<id>:<rest>` exactly as given (no stripping), construct `StoreLocator(id, rest)`, and turn `MalformedRecord` into `invalid-input` with the kernel's message; a `url:` or `https://` prefix gets a message saying URL locations are out of scope. `handle`: parse; compare with `writer.store_id`, and on mismatch consult `science.config.configured_stores(ctx.config)` for the two refusal messages; `standing_at(ctx.read_views(), locator)`; `outcome = writer.recheck((locator,), instrument=INSTRUMENT, standing={locator.canonical(): standing} if standing else None)`; then load the minted nodes through `ctx.write_view()` (not the cached read views) by `outcome.report_ref` and by the `PublishedObservation` ref in `outcome.entries`, and return their `record_block`s, observation first. Both loads must find their node; a miss is a `RuntimeError` (a kernel contract break, not a refusal).
- [ ] **Step 6: Run** `just test-one tests/test_cmd_recheck.py`. Expected: PASS.
- [ ] **Step 7: Regenerate adapters and conformance.** Regenerate `adapters/claude-code` with the `science adapters` command (README "The world"); then `just test-one tests/test_adapters.py tests/test_cli_surface.py tests/test_contracts.py`. Expected: PASS. Add `recheck` to README's belief-path list.
- [ ] **Step 8: Commit:** `just test-fast`, then `feat(recheck): re-check a store location through the session route (sci-409235)` with `tools/cli.toml`, `commands/recheck/`, `python/src/science/commands/recheck.py`, the test, adapters and README.

### Task 3: The kernel's result in the report

**Files:**
- Modify: `python/src/science/report.py` (`RecordBlock`, `record_block`, `serialize_block`)
- Modify: `docs/specs/2026-08-31-command-framework-design.md` (§7.4 dated amendment)
- Modify: fixtures and expected outputs under `python/tests/` that render `dataset` or `fetch` reports
- Test: `python/tests/test_report.py`, `python/tests/test_cmd_recheck.py`

**Interfaces:**
- Consumes: Task 2's `refused_write`, `handle`.
- Produces: `RecordBlock(uid: str, record_id: str, kind: str, title: str, detail: tuple[str, ...] = ())`; `record_block(node) -> RecordBlock` fills `detail` for `holdings-observation` and for `act-report` whose facet `operation == "re-check"`, and `()` for everything else. `serialize_block` renders each detail line on its own line after the title, after the existing two lines.

- [ ] **Step 1: Write failing tests:**
  - `test_report.py::test_observation_block_states_the_outcome`: a found observation node gives `detail == ("found sha256:<hex> at store:<id>:<path>",)`; an absent one gives `("absent at store:<id>:<path>",)`.
  - `test_report.py::test_recheck_report_block_lists_each_entry`: a re-check act-report node with one published entry gives `("store:<id>:<path>: observed holdings-observation:<identity>",)`; with a retrieval-failed entry, `("store:<id>:<path>: retrieval-failed <reason code>",)`.
  - `test_report.py::test_other_act_reports_carry_no_detail`: a `run` act-report node gives `detail == ()`, and its serialized block is byte-identical to today's.
  - `test_report.py::test_four_argument_record_block_still_constructs`: `RecordBlock("u", "i", "k", "t").detail == ()`.
  - `test_cmd_recheck.py::test_rendered_report_states_absent`: the text `d.invoke("recheck", ...)` returns contains `absent at <location>`.
  - `test_cmd_recheck.py::test_replay_renders_the_same_detail`: a second invoke with the same `invocation_id` returns identical text and appends no new act; a continuation page (small `output_budget` via a test declaration, or the existing continuation helper) still carries the detail line.
- [ ] **Step 2: Run** `just test-one tests/test_report.py tests/test_cmd_recheck.py`. Expected: the new tests FAIL.
- [ ] **Step 3: Implement** in `report.py`. Read the observation through `stored.holdings_observation_value(node)` (outcome finding and digest, `location.canonical()`); read the act-report through `stored.act_report_facet(node)` (`operation`, `entries[*].subject`, `entries[*].outcome`). Wording is exactly the strings in Step 1.
- [ ] **Step 4: Run** the Step 2 command, then `just test-one tests/test_cmd_dataset.py tests/test_cmd_fetch.py tests/test_render.py tests/test_write_dispatch.py`; update any expected `dataset`/`fetch` output to include the observation's detail line. Expected: PASS.
- [ ] **Step 5: Amend §7.4** of the framework design with a dated paragraph: a record block for a `holdings-observation` or a `re-check` act-report carries detail lines the renderer derives from the stored record, on first response, replay and continuation; handlers author none; other kinds and act-report operations are unchanged (sci-409235).
- [ ] **Step 6: Commit:** `just test-fast`, then `feat(report): state holdings outcomes in record blocks (sci-409235)`.

### Task 4: Read-store recovery and the runbook

**Files:**
- Modify: `docs/stores.md` (step 4, plus a new section "Settling an unsettled location")
- Test: `python/tests/test_cmd_recheck.py`

**Interfaces:**
- Consumes: Task 2's `refused_write`, `blocked_reasons`; `test_stores.py`'s `replicate_store` and store recipe approach.

- [ ] **Step 1: Write the failing test** `test_recovery_configuration_settles_a_read_store_location`: build the incident (`refused_write`, store_root = restored replica); create a fresh writable store and the working config `replace(cfg, store_root=fresh, read_store_roots=(restored,))`. Under the working config, `recheck` at the location refuses `invalid-input` naming the recovery route, with no act. Under the recovery config `replace(cfg, store_root=restored, read_store_roots=(fresh,))`, same `write_root` and `operations_root`, opened after the working session closed, `recheck` publishes Absent. Reopened under the working config, `blocked_reasons` no longer holds the location, and a holding written there earlier in the fresh store still resolves through `ctx.held_path`.
- [ ] **Step 2: Run** `just test-one tests/test_cmd_recheck.py -k recovery`. Expected: PASS if Tasks 2 and 3 already cover the path (then this test is the evidence); otherwise FAIL naming what is missing, and fix the handler, not the test.
- [ ] **Step 3: Update `docs/stores.md`:** replace step 4's "sci-409235 owns any unsettled-intent work under separate live-write authorization" with a pointer to the new section. The section: find the blocked location in the reduction; with the person's authorization, run `science recheck --location <it>` before relocating when the location is in the current `store_root`; after relocation, stop any running `science serve`, run it under a recovery configuration (that read store as `store_root`, the same `write_root`, the writable store in `read_store_roots`), then return to the working configuration; read Found, Absent and inconclusive (inconclusive leaves the block; fix the store's serviceability, then re-check). State that the re-check settles only intents in that `write_root`'s chain.
- [ ] **Step 4: Run** `just check` (docs and ops-check). Expected: PASS.
- [ ] **Step 5: Commit:** `just test-fast`, then `docs(stores): settle an unsettled location with recheck (sci-409235)`.
