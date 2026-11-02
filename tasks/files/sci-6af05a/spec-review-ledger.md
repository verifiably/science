# Spec Review Ledger

## Round 1 — Builder Check (7608d2c9af3cdcaa61b1f696fc4e6ceb540035bd)

- Reviewer: antigravity/inherit (read-only builder check 7672027b-77d8-4031-a0ad-8d1024c0807d)
- Verdict: approved
- Findings: none (nothing important left)

## Round 1 — User / External Review (7608d2c9af3cdcaa61b1f696fc4e6ceb540035bd -> 2fb59e88ee75498baeb50b935c4ae647d7fccc44)

- Reviewer: claude-code/claude-opus-5-5
- Verdict: revise
- Findings: 2 important, 3 minor, 1 decision/trade-off

### Rulings

1. **Important 1 — Uncertified skip split was estimated from static fixture names rather than measured on an uncertified volume, and `beliefs/root.py:871,1043,1359` wraps `CapabilityUnavailable` in `ExecutionError`.**
   - Ruling: accepted and fixed in `2fb59e88ee75498baeb50b935c4ae647d7fccc44` (§2.4, §3.4, §5.3, §7.2–7.3).
   - Why: Running the suite against the worktree's uncertified `/mnt/ssd3` volume with `VERIFIABLY_UNCERTIFIED_HOST=1` measured the exact split across all 1,195 collected items in 72 modules: 532 passed (44.5%, across 14 all-pass and 27 mixed modules), 663 skipped (55.5%, across 27 mixed and 31 all-skip modules), and 0 failed in 5.45s (16 workers) / 5.22s (4 workers). Every certified test in `science` initializes its durable root first via `init_world_root`, `init_corpus_root`, or `init_store_root` (`atoms.coordinator.register_root` / `read_chain`), which raises bare `CapabilityUnavailable` before any transaction write wrapper or CLI subprocess runs; checking both direct `CapabilityUnavailable` and `error.__cause__` in `conftest.py` also closes the `from caught` wrapper seam (`beliefs/root.py:871,1043,1359` and `science/config.py:104,114`) without a static module exclusion list that would drop the 246 passing items in the 27 mixed modules.
   - Cost: If a future test spawns a CLI subprocess against an uninitialized path on an uncertified volume without calling `init_*_root` in the parent process first, that test will fail in CI until it uses `certified_work` / `write_cli_config` in the parent process.
2. **Important 2 — Workflow action pinning, `setup-uv` Python selection, and pre-test `module-inventory.txt`.**
   - Ruling: accepted and fixed in `2fb59e88ee75498baeb50b935c4ae647d7fccc44` (§5.2, §6.7).
   - Why: Mirroring `beliefs/.github/workflows/ci.yml` (`actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0`, `astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990` with `version: "0.11.29"` and `python-version: ${{ matrix.python-version }}`, `extractions/setup-just@53165ef7e734c5c07cb06b3c8e7b647c5aa16db3`, `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`, no `setup-python`, and writing `module-inventory.txt` in `Prepare coverage evidence` before `uv sync --frozen` and `just ci-python`) ensures `uv` binds the exact matrix Python and preserves the inventory even if the test step aborts early.
   - Cost: Pinned action SHAs and `uv` `0.11.29` require explicit commits when upgrading runner actions or `uv`.
3. **Minor 3 — Sibling `origin/main` vs local `main` commit counts and Publication Packet check.**
   - Ruling: accepted and fixed in `2fb59e88ee75498baeb50b935c4ae647d7fccc44` (§2.4, §7.2).
   - Why: `beliefs` is 35 commits ahead of `origin/main` (0 files under `python/`), `atoms` is 37 commits ahead (3 files under `python/` including `atoms.chain` in `import-names`), and `nodes` is 5 commits ahead (0 files under `python/`). Re-checking `HEAD...origin/main` across all four repositories in the Publication Packet and pushing any ahead sibling `main` branches with user approval ensures hosted CI checks out the exact default-branch heads tested locally.
   - Cost: Publishing `science` CI may also require pushing `main` in `beliefs`, `atoms`, and `nodes`.
4. **Minor 4 — `policy: disabled at ...` note format in §7.3.3.**
   - Ruling: accepted and fixed in `2fb59e88ee75498baeb50b935c4ae647d7fccc44` (§7.1.4, §7.3.3).
   - Why: Although `ops/bin/tt-latency:452` accepts `(enabled|disabled)` in its regex and ignores `disabled`, the task body specifies `policy: enabled at <RFC3339-UTC> revision <full-sha>` only for hook-split integration and rollback. Using `activation: automatic_broad=false at <RFC3339-UTC> revision <full-sha>` for activation avoids overloading the `policy:` prefix while recording the exact activation timestamp and revision.
   - Cost: None.
5. **Minor 5 — Calibrate `timeout-minutes` from the pilot and match `beliefs` (`30`).**
   - Ruling: accepted and fixed in `2fb59e88ee75498baeb50b935c4ae647d7fccc44` (§5.2).
   - Why: The 4-worker uncertified pilot finished in 5.22s locally; setting `timeout-minutes: 30` matches `beliefs` and leaves generous headroom for cold runner dependency installation.
   - Cost: A hung runner job waits up to 30 minutes instead of 20 before timing out.
6. **Decision / Trade-off 6 — State the mandatory rule for when certified-host tests must run locally once `automatic_broad = false` is active.**
   - Ruling: accepted and added in `2fb59e88ee75498baeb50b935c4ae647d7fccc44` (§5.3).
   - Why: Because hosted CI skips 663 of 1,195 items (55.5%, including 31 all-skip modules and 27 mixed modules), §5.3 now specifies that (1) every change runs `just test-one` on its affected test module(s) (which runs on the certified volume even under `automatic_broad = false`), and (2) any branch touching certified-root or confinement paths (`config.py`, `session.py`, `dispatch.py`, `holdings.py`, `publication.py`, `world_belief.py`, `commands/*`, `conftest.py`, `helpers/{world,commons,snapshot}.py`, or `pyproject.toml`/`uv.lock`) must run `TT_FORCE=1 just test-fast` (or `just test-full` for shared fixture, lifecycle, or sibling dependency changes) on the certified host before merging to `main`.
   - Cost: Git hooks do not enforce this rule automatically when `automatic_broad = false`; enforcement relies on `AGENTS.md` and task verification gates.

### Minor (deferred)

- None.

## Round 2 — Builder Check (2fb59e88ee75498baeb50b935c4ae647d7fccc44)

- Reviewer: antigravity/inherit (read-only builder check ba3749e7-9108-4b88-9787-7685eb3d702d)
- Verdict: approved
- Findings: none (nothing important left)

## Round 2 — User / External Review (2fb59e88ee75498baeb50b935c4ae647d7fccc44 -> 365799fe519726eafa7e8a70e1f2ef2f796c268b)

- Reviewer: claude-code/claude-opus-5-5
- Verdict: revise
- Findings: 1 important

### Rulings

1. **Important 1 — Broaden §5.3 pre-merge certified-host rule from a hand-kept file subset to any branch touching `python/`.**
   - Ruling: accepted and fixed in `365799fe519726eafa7e8a70e1f2ef2f796c268b` (§5.3).
   - Why: 58 of the 72 test modules (31 all-skip and 27 mixed, including `retention.py`, `overlap.py`, `sharing.py`, `coordination.py`, `supersession.py`, `closure.py`, `cli.py`, `loader.py`, `stop.py`, `mcp.py`, and `serve.py`) have certified-fixture tests skipped on an uncertified runner, and a hand-kept file list would both omit existing modules and go stale as modules are added. Requiring `TT_FORCE=1 just test-fast` on the certified host before merging any branch that touches `python/` covers all Python modules while letting `pytest-testmon` scale the run to affected tests, and keeping `just test-full` for shared fixtures (`python/tests/conftest.py`, `python/tests/helpers/*`), lifecycle code, and sibling/locked dependencies (`python/pyproject.toml`, `python/uv.lock`) covers cross-cutting changes.
   - Cost: Every branch touching `python/` pays one `TT_FORCE=1 just test-fast` run on the certified host before merge.
2. **Correction to Round 1 Finding 4 — Restore `policy: disabled at <RFC3339-UTC> revision <full-sha>` in §7.3.3.**
   - Ruling: accepted and restored in `365799fe519726eafa7e8a70e1f2ef2f796c268b` (§7.3.3).
   - Why: `ops/bin/tt-latency:452` explicitly parses `policy: (enabled|disabled) at (\S+) revision [0-9a-f]{40}` (using `enabled` for the latency floor), and sibling adoptions (`autonomy-23aeff`) record `policy: disabled at <RFC3339-UTC> revision <full-sha>` at activation.
   - Cost: None.

### Minor (deferred)

- None.

## Round 3 — User / External Review (365799fe519726eafa7e8a70e1f2ef2f796c268b -> 8cd98e857bd75ce0be1858c06b2b2053f9db382a)

- Reviewer: claude-code/claude-opus-5-5 (accepted for planning by Keith)
- Verdict: accept
- Findings: 2 minor

### Rulings

1. **Minor 1 — §5.3 item 2 listed source modules (`retention.py`, `overlap.py`, etc.) directly after "58 of the 72 test modules".**
   - Ruling: accepted and fixed in `8cd98e857bd75ce0be1858c06b2b2053f9db382a` (§5.3).
   - Why: Clarifying that those are source modules under `python/src/science/` whose corresponding test modules skip keeps the sentence accurate.
   - Cost: None.
2. **Minor 2 — §5.3 named "session/dispatch/store lifecycle code" for the `just test-full` trigger without naming the files.**
   - Ruling: accepted and fixed in `8cd98e857bd75ce0be1858c06b2b2053f9db382a` (§5.3).
   - Why: Naming `python/src/science/{config,session,dispatch,holdings,publication,world_belief}.py` explicitly prevents two readings of the `AGENTS.md` rule.
   - Cost: None.

### Minor (deferred)

- None.
