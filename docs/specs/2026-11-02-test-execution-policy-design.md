# Science Test Execution Policy and Hosted Verification Design

- Date: 2026-11-02
- Task: `sci-6af05a`
- Shared authority: `ops-8bfa85` (`docs/specs/2026-10-29-test-execution-policy-design.md` in `ops`)
- Prerequisite: `ops-68729d` (`done`)
- Sibling reference adoptions: `beliefs-067a8d`, `autonomy-23aeff`, `lore-fdbe86`
- Reporting targets: `ops-39bff6`, `ops-8bfa85`
- Shared 30-day evaluation: `ops-56aab7` (deferred to `2026-11-28`; append `sci-6af05a` reference, do not file a duplicate)

## 1. Intent and Scope

Adopt the shared broad-test execution policy (`ops-8bfa85`) in `science` so routine local commit and push hooks run mandatory seconds-long hygiene checks without saturating the host with automatic broad pytest runs, while GitHub Actions runs the non-certified Python suite once per branch push under `TT_FORCE=1` and uploads durable JUnit and module-inventory evidence.

Originating user intent (recovered from `codex:01a1874f-c2d8-7320-ae81-7114e37e343f`, 2026-10-29):

1. Concurrent local pushes and agent completions across repositories contend for CPU and I/O on the shared host and distort timing records.
2. Each repository keeps focused tests (`just test-one <args>`) and fast hygiene checks active during local work, splits local git hooks so mandatory hygiene is timed under the hook target and broad suites are invoked as separate child recipes that `.tt.toml` (`automatic_broad = false`) can skip and record, and offloads automatic broad runs to once-per-branch-push CI with `TT_FORCE=1`.
3. Public GitHub repositories use standard free GitHub-hosted runners without a paid-allowance prerequisite (`ops-2bf257`), and local `automatic_broad = false` is activated only after an approved hosted CI run finishes with a nonzero executed test count and accepted coverage.

## 2. Verified Current State (at `06dd4a7`)

### 2.1 Tooling and Policy

- `tools/tt` is already version 9 (the task body's observation of version 7 is stale; no `tt` re-vendor is required).
- `tools/ops-check` is version 17 and `tools/ops-docs` is version 6.
- No `.tt.toml` exists at the repository root, so `tt` currently defaults to `automatic_broad = true`.
- No open `test-latency` or `halt` tasks exist in `sci`.

### 2.2 Front Door and Git Hooks

Current `justfile` definitions:

- `xdist := "-n auto --dist worksteal"`
- `fast_cmd := "cd python && uv run pytest --testmon " + xdist`
- `test_cmd := "cd python && uv run pytest " + xdist`
- `one_cmd := "cd python && uv run pytest"`
- `check_cmd := "python3 tools/ops-check && python3 tools/ops-docs check && tasks check"`
- `docs_paths := "README.md AGENTS.md docs/*.md tasks/*.md"`
- `docs_check_cmd := check_cmd`
- `ci_suite_refs := ""`
- `ci_remote := "origin"`
- `push_fast_cmd := fast_cmd`

Current recipes and hooks:

- `test-one +args`, `test-fast`, and `test` run under `{{tt}} <target> -- host-budget run -- sh -c ...`.
- `check` runs `{{tt}} check -- sh -c '{{check_cmd}}'`. No formatter, linter, or typechecker is configured in `python/pyproject.toml` (`[dependency-groups].dev` contains only `pytest`, `pytest-testmon`, and `pytest-xdist`).
- `gate: check test`.
- `hook-pre-commit` and `hook-pre-commit-docs` both run `check_cmd` under their own `tt` targets.
- `hook-pre-push` runs `{{tt}} hook-pre-push -- sh -c '{{check_cmd}} && host-budget run -- sh -c "{{test_cmd}}"'` as a single monolithic protected `tt` target, and `hook-pre-push-fast` runs `{{tt}} hook-pre-push-fast -- sh -c '{{check_cmd}} && host-budget run -- sh -c "{{push_fast_cmd}}"'` as a single monolithic protected `tt` target. Because `hook-pre-push` and `hook-pre-push-fast` are in `tt`'s `PROTECTED_TARGETS`, keeping `test_cmd` / `push_fast_cmd` inside those `tt` invocations would bypass `.tt.toml`.
- `.githooks/pre-push` checks SSH keepalive and selects `hook-pre-push-fast` when the remote is `ci_remote` and all pushed refs match `ci_suite_refs`, or `hook-pre-push` otherwise. It does not yet include the `ops` template's policy-off stderr warning when an uncovered push skips `test`.

### 2.3 Local Timing Baseline (`2026-10-01` to `2026-11-02`)

From `tt-report --project sci --since 2026-10-01 --all`:

| Target | Runs | Median | p90 | Slowest | Pass |
| --- | ---: | ---: | ---: | ---: | ---: |
| `check` | 124 | 1.0s | 1.4s | 16.5s | 100% |
| `docs` | 5 | 0.9s | 1.0s | 1.0s | 100% |
| `hook-pre-commit` | 270 | 0.8s | 1.3s | 3.1s | 97% |
| `hook-pre-commit-docs` | 1479 | 0.9s | 1.4s | 3.1s | 100% |
| `hook-pre-push` | 17 | 109.4s | 208.8s | 237.4s | 94% |
| `test` | 43 | 124.5s | 255.7s | 538.9s | 93% |
| `test-fast` | 113 | 135.2s | 406.8s | 599.2s | 77% |
| `test-one` | 517 | 35.2s | 116.8s | 328.9s | 69% |

### 2.4 Remote Repository, Sibling Dependencies, and Measured Uncertified-Volume Pilot

- `origin` is `git@github.com:verifiably/science.git`. On GitHub, `verifiably/science` is public (`visibility: public`, `private: false`, default branch `main`). `origin/main` is currently at `7a4915237c9af766fb7d38abc96413839642c60a` (581 commits behind local `main` at `06dd4a748e76ec24d0701c2f27093a33289b7e52`).
- `science/python/pyproject.toml` and `science/python/uv.lock` require `verifiably-beliefs` as an editable path dependency at `../../beliefs/python`, which in turn requires `verifiably-atoms` at `../../atoms/python` and `verifiably-nodes` at `../../nodes/python`.
- All three sibling repositories (`verifiably/beliefs`, `verifiably/atoms`, `verifiably/nodes`) are public on GitHub. Currently their local `main` branches are ahead of `origin/main`:
  - `verifiably/beliefs`: local `main` (`8f32a44a1781197cab9c2288ab34560c6b959ab5`) is 35 commits ahead of `origin/main` (`600afa63396bb7353e8f67adf447f28fc6b6e019`), with zero diff under `python/` (all 35 commits are task-record, tool-vendor, and doc-migration commits).
  - `verifiably/atoms`: local `main` (`14918133bbc8872edbaa031ba5d2fd1ada0dd41b`) is 37 commits ahead of `origin/main` (`935535a7275eeaa9d5ea9189b0b2163c021d4a95`), with a 3-file diff under `python/` (`python/README.md`, `python/pyproject.toml` adding `atoms.chain` to `import-names`, and a docstring edit in `python/src/atoms/coordinator/__init__.py`).
  - `verifiably/nodes`: local `main` (`09d6b1e700088b5a85a50b41d6a93a223dbce29a`) is 5 commits ahead of `origin/main` (`ce159f2694c3149416f3d7e24ac0fedad5f4253d`), with zero diff under `python/`.
  Because `.github/workflows/ci.yml` checks out each sibling's default branch (`main`), the Publication Packet (§7.2) re-verifies `HEAD...origin/main` across `science`, `beliefs`, `atoms`, and `nodes` before any push and includes any sibling `main` pushes needed so hosted CI tests the same sibling trees as local development.
- **Measured uncertified-volume pilot**: Running the full `science` pytest suite against an uncertified volume (`SCIENCE_TEST_ROOT` pointed at the worktree's uncertified storage volume with `VERIFIABLY_UNCERTIFIED_HOST=1`) collected **1,195 items across 72 `test_*.py` modules** and completed in **5.45s on 16 workers** (**5.22s on 4 workers**):
  - **532 items passed (44.5%)** across **41 modules**:
    - **14 all-pass modules (286 passed, 0 skipped)**: `test_adapters` (12), `test_canonical` (8), `test_config` (61), `test_config_sharing` (18), `test_contracts` (21), `test_cursor` (17), `test_dispatch` (15), `test_findings` (1), `test_front_door` (12), `test_render` (10), `test_report` (12), `test_schema` (47), `test_sharing_registry` (22), `test_transport_git` (20).
    - **27 mixed modules (246 passed, 317 skipped)**: `test_acceptance` (17/4), `test_cli` (6/3), `test_cli_surface` (39/1), `test_cmd_adopt` (4/39), `test_cmd_belief` (1/5), `test_cmd_claim` (1/5), `test_cmd_next_selection` (1/11), `test_cmd_project_select` (1/14), `test_cmd_revise` (1/9), `test_cmd_show` (5/26), `test_cmd_spec` (1/21), `test_coordination_helpers` (7/1), `test_cwd_independence` (1/7), `test_dispatch_refusals` (8/11), `test_dispatch_sharing` (7/20), `test_epoch_verb` (1/18), `test_initial_selection` (1/9), `test_launcher_stop` (3/11), `test_mcp` (75/13), `test_project_field` (3/12), `test_publish_ownership` (2/16), `test_serve` (1/17), `test_snapshot` (16/8), `test_status` (19/4), `test_stores` (12/30), `test_supersession` (22/1), `test_synthetic_tree` (1/1).
  - **663 items skipped (55.5%)**: 317 in the 27 mixed modules above plus **346 across 31 all-skip modules** (`test_belief_path` [3], `test_belief_path_transports` [7], `test_cmd_assess` [2], `test_cmd_dataset` [11], `test_cmd_fetch` [10], `test_cmd_next` [4], `test_cmd_project` [6], `test_cmd_projects` [11], `test_cmd_provider` [12], `test_cmd_publish` [15], `test_cmd_recheck` [26], `test_cmd_reuse` [10], `test_cmd_run` [6], `test_cmd_subordinate` [11], `test_cmd_verify` [6], `test_commons_1a` [5], `test_commons_1b` [21], `test_commons_fixture` [11], `test_config_mounts` [9], `test_context` [23], `test_mcp_socket` [2], `test_mount_citations` [23], `test_mounts` [8], `test_overlap` [10], `test_retention` [14], `test_selection_query` [19], `test_session_class` [17], `test_session_open` [6], `test_two_corpora` [16], `test_write_dispatch` [16], `test_write_root` [6]).
  - **0 items failed or errored**: Every certified test in `science` initializes its durable world, corpus, or store first through `init_world_root`, `init_corpus_root`, or `init_store_root` in `beliefs.root`, which call `atoms.coordinator.register_root` or `read_chain` directly and raise bare `CapabilityUnavailable` before any transaction write wrapper (`beliefs/root.py:871,1043,1359` raising `ExecutionError(...) from caught`), store inspection wrapper (`science/config.py:104,114` raising `Refused(...) from caught`), or CLI `subprocess` invocation (`test_cli.py`, `test_launcher_stop.py`, `test_selection_query.py`, `test_stores.py::run_store_recipe`, all of which call `write_cli_config` or `build_belief_world` in the parent pytest process first) is reached.
  - On `ubuntu-latest` (where `bwrap` and unprivileged user namespaces are unavailable), 2 of the 663 skipped items (`test_snapshot.py::test_a_confined_world_restores_its_sandbox_links_as_links` and `test_belief_path.py::test_under_confinement_the_path_ends_in_an_admitted_belief`) skip at `host_prerequisites() is not None` with `"confinement unavailable..."` before entering `walk_belief_path_confined`, while the remaining 661 skip with `"certified tuple unavailable on this host: ..."`.

## 3. Approaches Considered and Design Calls

Every project-specific choice below is the author's call and is marked for review.

1. **Author's call — Hygiene-only `check` (no `check-code` target)**:
   - *Decision*: Define `check_hygiene_cmd := "python3 tools/ops-check && python3 tools/ops-docs check && tasks check"`, timed target `check-hygiene`, and untimed alias `check` that invokes `just check-hygiene`. Do not invent a no-op `check-code` target.
   - *Why*: `science` configures no linter, formatter, or typechecker, matching `autonomy-23aeff`. Adding a synthetic `check-code` target would record empty timing rows.
2. **Author's call — Split hook recipes and delegate covered pushes to `just test-fast`**:
   - *Decision*:
     - `hook-pre-commit` runs `{{tt}} hook-pre-commit -- sh -c '{{check_hygiene_cmd}}'`.
     - `hook-pre-commit-docs` runs `{{tt}} hook-pre-commit-docs -- sh -c '{{docs_check_cmd}}'`.
     - `hook-pre-push` runs `{{tt}} hook-pre-push -- sh -c '{{check_hygiene_cmd}}'` followed by `just test`.
     - `hook-pre-push-fast` runs `{{tt}} hook-pre-push-fast -- sh -c '{{check_hygiene_cmd}}'` followed by `just test-fast` (removing the duplicate `push_fast_cmd` variable since `push_fast_cmd` was identical to `fast_cmd`).
   - *Why*: Mandatory hygiene is timed once under the protected hook target, and the broad suite runs as a separate child recipe (`test` or `test-fast`) that `tt` evaluates against `.tt.toml`. If hygiene fails, the recipe exits nonzero before reaching the suite.
3. **Author's call — Dedicated `ci-python` target for hosted CI with JUnit evidence**:
   - *Decision*: Add `ci-python` to `justfile`:
     ```just
     ci_evidence_cmd := "case \"${SCIENCE_CI_EVIDENCE_DIR:?set SCIENCE_CI_EVIDENCE_DIR}\" in /*) ;; *) echo \"CI evidence path must be absolute\" >&2; exit 2;; esac"
     ci_py_test_cmd := "cd python && uv run --frozen pytest --junitxml=\"$SCIENCE_CI_EVIDENCE_DIR/pytest.xml\" " + xdist

     ci-python:
         {{tt}} ci-python -- sh -c '{{ci_evidence_cmd}} && python3 tools/ops-check && {{ci_py_test_cmd}}'
     ```
     Include `"ci-python"` in `.tt.toml` `broad_targets = ["test", "test-fast", "ci-python"]`.
   - *Why*: GitHub-hosted runners do not have `host-budget` or `tasks` installed, and `tt` deletes its internal `TT_JUNIT_DIR` on exit. Having a dedicated `ci-python` broad target (mirroring `beliefs-067a8d`) lets CI size workers via `PYTEST_XDIST_AUTO_NUM_WORKERS: "4"`, run the portable `python3 tools/ops-check` check plus the full pytest suite with `--junitxml="$SCIENCE_CI_EVIDENCE_DIR/pytest.xml"`, and still fail closed with exit code 2 if `GITHUB_ACTIONS=true` and `TT_FORCE=1` is ever missing.
4. **Author's call — Opt-in `VERIFIABLY_UNCERTIFIED_HOST=1` gate in `python/tests/`**:
   - *Decision*: Add `python/tests/uncertified_host.py` (defining `UNCERTIFIED_HOST_VAR = "VERIFIABLY_UNCERTIFIED_HOST"` and `uncertified_host(environ)`) and wire `pytest_runtest_setup`, `pytest_runtest_call`, and `pytest_runtest_teardown` (`@pytest.hookimpl(wrapper=True)`) in `python/tests/conftest.py`. Check both direct `CapabilityUnavailable` and direct `__cause__` (`error if isinstance(error, CapabilityUnavailable) else error.__cause__ if isinstance(error.__cause__, CapabilityUnavailable) else None`) so that if a future test reaches `beliefs/root.py:871,1043,1359` (`ExecutionError(...) from caught`) or `science/config.py:104,114` (`Refused(...) from caught`) without an earlier `register_root` / `read_chain` call, an unhandled exception caused by `CapabilityUnavailable` still converts to `pytest.skip(f"certified tuple unavailable on this host: {cause}")` when `VERIFIABLY_UNCERTIFIED_HOST == "1"`. Add unit tests in `python/tests/test_uncertified_host.py` verifying exact `"1"` matching, direct and `__cause__` conversion under `"1"`, and fail-closed re-raising when unset or set to any other value.
   - *Why*: Mirrors `beliefs` and `atoms` while closing the `from caught` wrapper seam if a future test bypasses `init_*_root`, without maintaining a static module exclusion list that would skip the 246 passing tests inside the 27 mixed modules.

## 4. Target Classification and Command Contract

| Target | Classification | Invocation | Policy-off behavior (`automatic_broad = false`) |
| --- | --- | --- | --- |
| `test-one +args` | Protected (`PROTECTED_TARGETS`) | `{{tt}} test-one -- host-budget run -- sh -c '{{one_cmd}} "$@" 2>&1' test-one "$@"` | Always runs |
| `test-fast` | Broad (`broad_targets`) | `{{tt}} test-fast -- host-budget run -- sh -c '{{fast_cmd}}'` | Skips locally (`execution: "skipped"`, `reason: "policy-disabled"`), runs with `TT_FORCE=1`, refuses with exit 2 if `GITHUB_ACTIONS=true` without `TT_FORCE=1` |
| `test` | Broad (`broad_targets`) | `{{tt}} test -- host-budget run -- sh -c '{{test_cmd}}'` | Skips locally (`execution: "skipped"`, `reason: "policy-disabled"`), runs with `TT_FORCE=1`, refuses with exit 2 if `GITHUB_ACTIONS=true` without `TT_FORCE=1` |
| `test-full` | Untimed alias | `TT_FORCE=1 just test` | Always runs `test` with `execution: "ran"`, `reason: "forced"` |
| `ci-python` | Broad (`broad_targets`) | `{{tt}} ci-python -- sh -c '{{ci_evidence_cmd}} && python3 tools/ops-check && {{ci_py_test_cmd}}'` | Skips locally unless `TT_FORCE=1`; on `GITHUB_ACTIONS=true`, refuses with exit 2 without `TT_FORCE=1` and runs with `TT_FORCE=1` |
| `check-hygiene` | Protected (`PROTECTED_TARGETS`) | `{{tt}} check-hygiene -- sh -c '{{check_hygiene_cmd}}'` | Always runs |
| `check` | Untimed alias | `just check-hygiene` | Always runs `check-hygiene` |
| `gate` | Untimed alias | `just check` then `just test` | Runs `check-hygiene`, then evaluates `test` under policy (`TT_FORCE=1 just gate` forces both) |
| `docs` | Protected (`PROTECTED_TARGETS`) | `{{tt}} docs -- python3 tools/ops-docs write` | Always runs |
| `hook-pre-commit` | Protected (`PROTECTED_TARGETS`) | `{{tt}} hook-pre-commit -- sh -c '{{check_hygiene_cmd}}'` | Always runs |
| `hook-pre-commit-docs` | Protected (`PROTECTED_TARGETS`) | `{{tt}} hook-pre-commit-docs -- sh -c '{{docs_check_cmd}}'` | Always runs |
| `hook-pre-push` | Protected parent + broad child | `{{tt}} hook-pre-push -- sh -c '{{check_hygiene_cmd}}'` then `just test` | Runs hygiene under `hook-pre-push`, then skips `test` (with pre-push warning on stderr) |
| `hook-pre-push-fast` | Protected parent + broad child | `{{tt}} hook-pre-push-fast -- sh -c '{{check_hygiene_cmd}}'` then `just test-fast` | Runs hygiene under `hook-pre-push-fast`, then skips `test-fast` |

### 4.1 Pre-Push Policy Warning and Coverage Routing

`.githooks/pre-push` adopts the shared `ops` template (`templates/githooks/pre-push`) policy inspection block:

- When `recipe=hook-pre-push`, `.githooks/pre-push` loads the path from `just --evaluate tt` using `importlib.machinery.SourceFileLoader` and checks `tt.execution_decision('test', tt.read_policy(pathlib.Path.cwd()), os.environ)`.
- If `execution == 'skipped'`, it writes to stderr:
  `pre-push: local test skipped by policy; remote full-suite coverage is not declared for this push. Use TT_FORCE=1 for deliberate local verification.`
- If `.tt.toml` is malformed or unreadable, `tt.read_policy` raises `ValueError` / `OSError` and the hook prints `pre-push: cannot inspect test execution policy: ...` and exits `2`.
- `ci_suite_refs` stays `""` while the local hook split and workflow are implemented and tested locally, and is widened to `"refs/heads/*"` once `.github/workflows/ci.yml` is active on `origin`.

## 5. Hosted Verification Workflow (`.github/workflows/ci.yml`)

### 5.1 Triggers, Concurrency, and Fork Guard

- Workflow file: `.github/workflows/ci.yml`, name `CI`.
- Triggers:
  - `push`: `branches: ["**"]` (matches `ci_suite_refs := "refs/heads/*"`; every branch push runs CI once).
  - `pull_request`: enabled for external/fork PRs only; the job carries:
    `if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name != github.repository`
    so same-repo pull requests do not double-run alongside `push`.
  - `workflow_dispatch`: enabled for manual runs.
- Concurrency:
  ```yaml
  concurrency:
    group: ${{ github.workflow }}-${{ github.ref }}
    cancel-in-progress: true
  ```
- Permissions: `contents: read`.

### 5.2 Job Matrix, Pinned Actions, Sibling Checkouts, and Evidence Steps

Mirroring `beliefs/.github/workflows/ci.yml`, every GitHub Action is pinned by full commit SHA, `setup-uv` is pinned to `0.11.29` and receives `python-version: ${{ matrix.python-version }}` directly (with no separate `setup-python` action so `uv` cannot pick the runner's system Python instead of the matrix version), and `module-inventory.txt` is written in a dedicated step before `uv sync --frozen` and `just ci-python`:

- Job `python`:
  - `runs-on: ubuntu-latest`
  - `if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name != github.repository`
  - `timeout-minutes: 30` (matching `beliefs`; the 4-worker uncertified pilot ran in 5.22s locally, leaving generous headroom for cold runner dependency installation)
  - `strategy`: `fail-fast: false`, `matrix.python-version: ["3.11", "3.13"]`
  - `env`:
    - `TT_FORCE: "1"`
    - `PYTEST_XDIST_AUTO_NUM_WORKERS: "4"`
  - `defaults.run.working-directory: science/python`
  - Steps:
    1. `actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0` with `path: science`.
    2. `actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0` with `repository: verifiably/beliefs`, `path: beliefs`.
    3. `actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0` with `repository: verifiably/atoms`, `path: atoms`.
    4. `actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0` with `repository: verifiably/nodes`, `path: nodes`.
    5. `astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2` with `version: "0.11.29"` and `python-version: ${{ matrix.python-version }}`.
    6. `extractions/setup-just@53165ef7e734c5c07cb06b3c8e7b647c5aa16db3 # v4.0.0`.
    7. `Prepare coverage evidence` (before tests run):
       ```sh
       evidence_dir="$RUNNER_TEMP/science-python-coverage"
       mkdir -p "$evidence_dir"
       echo "SCIENCE_CI_EVIDENCE_DIR=$evidence_dir" >> "$GITHUB_ENV"
       science=$(git rev-parse HEAD)
       beliefs=$(git -C ../../beliefs rev-parse HEAD)
       atoms=$(git -C ../../atoms rev-parse HEAD)
       nodes=$(git -C ../../nodes rev-parse HEAD)
       {
         echo "science $science"
         echo "beliefs $beliefs"
         echo "atoms $atoms"
         echo "nodes $nodes"
         git ls-files -- tests | grep -E '(^|/)(test_[^/]*|[^/]*_test)[.]py$'
         cat pyproject.toml
       } > "$evidence_dir/module-inventory.txt"
       ```
    8. `uv sync --frozen` (in `science/python`).
    9. `just ci-python` with `env: VERIFIABLY_UNCERTIFIED_HOST: "1"`.
    10. `Require coverage evidence` (`if: always()`): verifies `test -s "${SCIENCE_CI_EVIDENCE_DIR:?}/pytest.xml"` and `test -s "$SCIENCE_CI_EVIDENCE_DIR/module-inventory.txt"`, parses `pytest.xml` to verify `executed > 0`, `failures == 0`, `errors == 0`, and that every `<skipped>` message contains `"certified tuple unavailable on this host:"` or `"confinement unavailable"`, and prints `executed=<N> skipped=<M>`.
    11. `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1` (`if: always()`): `name: python-${{ matrix.python-version }}-coverage`, `path: ${{ env.SCIENCE_CI_EVIDENCE_DIR }}`, `retention-days: 30`, `if-no-files-found: error`.

### 5.3 Certified-Host Omission, Trade-Off, and Mandatory Local Verification Rule

- **Coverage split and trade-off**: Hosted CI (`ubuntu-latest`) executes **532 of 1,195 items (44.5%)** across 41 modules and skips **663 items (55.5%)** across 58 modules (31 all-skip modules and 27 mixed modules) because the runner cannot supply the certified Linux kernel + ext4 volume tuple required by `atoms` (`docs/certification/2026-09-03-ext4-linux-7.2.2-arch1-1.json`) or unprivileged bubblewrap sandboxes. Once `.tt.toml` (`automatic_broad = false`) is active, git hooks (`pre-commit`, `pre-push`) will no longer run those 663 certified items automatically on commit or push.
- **When certified-host verification is required (`AGENTS.md` rule)**:
  1. **Focused inner loop (every change)**: `just test-one <pytest args>` is protected by `tt` and always runs against the certified volume (`MAIN_ROOT / ".framework-test"`) even when `automatic_broad = false`. Any change to a command or module must run `just test-one` on its corresponding test module(s), including certified-fixture tests.
  2. **Before merging any `python/` changes to `main`**: Because 58 of the 72 test modules (31 all-skip and 27 mixed, including modules such as `retention.py`, `overlap.py`, `sharing.py`, `coordination.py`, `supersession.py`, `closure.py`, `cli.py`, `loader.py`, `stop.py`, `mcp.py`, and `serve.py`) have certified-fixture tests that skip on an uncertified runner and any hand-kept module allowlist would go stale, **any branch that touches `python/`** must run `TT_FORCE=1 just test-fast` on the certified host before merging to `main` (`pytest-testmon` selects the affected tests so the cost scales with the change). Any branch that changes shared test fixtures (`python/tests/conftest.py`, `python/tests/helpers/*`), session/dispatch/store lifecycle code, or sibling/locked dependencies (`python/pyproject.toml`, `python/uv.lock`) must run `just test-full` on the certified host before merging to `main`.
  3. **Deliberate full-suite and full-gate routes**:
     - `TT_FORCE=1 just test-fast`: forced testmon-selected suite on the certified host.
     - `just test-full`: forced full 1,195-item suite on the certified host (`execution: "ran"`, `reason: "forced"`).
     - `TT_FORCE=1 just gate`: forced hygiene + full suite on the certified host.
- `README.md` and `AGENTS.md` will state both the 532/663 hosted-vs-certified split and the mandatory rule above for running `just test-one`, `TT_FORCE=1 just test-fast`, and `just test-full` on the certified host.

## 6. Isolated Front-Door and Workflow Conformance Tests

Replace the old fake-`just` and live-`ROOT` tests in `python/tests/test_front_door.py` with an isolated fixture checkout (`FrontDoor`) that builds its environment key by key (inheriting no `TT_FORCE`, `GITHUB_ACTIONS`, `CI`, or host `GIT_*` variables; setting `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1`), copies `justfile`, `tools/tt`, `.githooks/pre-commit`, and `.githooks/pre-push` into a temporary Git repository, replaces `check_hygiene_cmd`, `fast_cmd`, `test_cmd`, `one_cmd`, and `ci_py_test_cmd` with lightweight marker invocations, and verifies:

1. Staged paths route docs-only commits (`README.md`, `AGENTS.md`, `docs/*.md`, `tasks/*.md`) to `hook-pre-commit-docs` and code/fixture commits (including `python/tests/fixtures/foo.md` and `justfile`) to `hook-pre-commit`.
2. Under `automatic_broad = false`, `hook-pre-commit` and `hook-pre-commit-docs` run hygiene (`execution: "ran"`), while `hook-pre-push`, `hook-pre-push-fast`, `check`, and `gate` run `check-hygiene` once (`execution: "ran"`) and skip their broad child (`test` or `test-fast` with `execution: "skipped"`, `execution_reason: "policy-disabled"`).
3. Under `automatic_broad = true` (or absent `.tt.toml`), `hook-pre-push` and `hook-pre-push-fast` run hygiene first and then run `test` or `test-fast`; a failing hygiene step stops before the broad child starts; a failing broad child propagates its nonzero exit status.
4. `test-full` forces `test` (`execution: "ran"`, `execution_reason: "forced"`) and propagates failures; `test-one` runs under policy-off and forwards arguments with spaces, `$`, and globs intact.
5. On `GITHUB_ACTIONS=true` with `automatic_broad = false` and without `TT_FORCE=1`, `test`, `test-fast`, `ci-python`, and `hook-pre-push-fast` fail with exit code 2 and `TT_FORCE=1` on stderr without recording a skipped row; with `TT_FORCE=1`, they run.
6. `.githooks/pre-push` routes branch pushes to `origin` (`refs/heads/main`, `refs/heads/feat/x`) to `hook-pre-push-fast` when `ci_suite_refs = "refs/heads/*"`, routes tag pushes (`refs/tags/v1`), other remotes (`backup`), or empty `ci_suite_refs` to `hook-pre-push`, emits the policy warning on stderr only when `hook-pre-push` will skip `test`, refuses malformed `.tt.toml` with exit code 2, refuses missing SSH keepalive with exit code 1, and clears `git rev-parse --local-env-vars`.
7. `.github/workflows/ci.yml` conformance checks verify triggers (`push` on `branches: ["**"]`, `pull_request` with the same-repo skip condition, `workflow_dispatch`), concurrency group and `cancel-in-progress: true`, `TT_FORCE: "1"`, `VERIFIABLY_UNCERTIFIED_HOST: "1"`, full-SHA action pins (`actions/checkout`, `astral-sh/setup-uv` with `version: "0.11.29"` and `python-version: ${{ matrix.python-version }}`, `extractions/setup-just`, `actions/upload-artifact`) with no `setup-python`, sibling checkouts (`science`, `beliefs`, `atoms`, `nodes`), `Prepare coverage evidence` before `just ci-python`, and `Require coverage evidence`.

## 7. Rollout Sequence, Approval Packets, and Rollback

### 7.1 Phase 1 — Local Implementation (Policy Enabled)

1. Implement `python/tests/uncertified_host.py`, `python/tests/test_uncertified_host.py`, and the `conftest.py` hooks.
2. Update `justfile` (`check-hygiene`, untimed `check`, `test-full`, `ci-python`, split `hook-pre-commit`, `hook-pre-commit-docs`, `hook-pre-push`, `hook-pre-push-fast`), `.githooks/pre-push` (policy warning), `.github/workflows/ci.yml`, `python/tests/test_front_door.py`, `README.md`, and `AGENTS.md`.
3. Keep `.tt.toml` absent and `ci_suite_refs := ""` (testing `ci_suite_refs` in fixture checkouts) until the workflow is published and verified on GitHub.
4. When the hook-split and workflow commit integrates to `main`, record on `sci-6af05a` the exact lifecycle note required by `ops/bin/tt-latency:450-457` (any note starting with `policy:` on a `tt-policy:<prefix>` task must match `r"policy: (enabled|disabled) at (\S+) revision [0-9a-f]{40}"`):
   `policy: enabled at <RFC3339-UTC> revision <full-sha>`

### 7.2 Phase 2 — Publication Packet and Hosted CI Verification

Before pushing to `origin` (`git@github.com:verifiably/science.git`), present the **Publication Packet** for user approval:

- Target remote and visibility: `origin` (`verifiably/science`, public repository; standard GitHub-hosted runners are free under `ops-2bf257`).
- Exact ref(s) and commit SHA to push in `science` (noting that `origin/main` is at `7a4915237c9af766fb7d38abc96413839642c60a`, so pushing `main` or `feat/sci-6af05a-test-policy` publishes the 581 local `main` commits plus the `sci-6af05a` commits).
- Sibling sync check across `verifiably/beliefs`, `verifiably/atoms`, and `verifiably/nodes`: report `HEAD...origin/main` and `git diff origin/main..HEAD -- python/` for each sibling and request approval to push any sibling `main` branch (`beliefs`, `atoms`, `nodes`) that is ahead of `origin/main` so CI checks out the current default-branch heads.
- Confirmation that `.tt.toml` is still absent (local policy remains enabled until CI passes).

After user push approval:

- Push the approved refs and watch the GitHub Actions `CI` workflow run via `gh run list` / `gh run watch`.
- Download the uploaded `python-3.11-coverage` and `python-3.13-coverage` artifacts (`pytest.xml` and `module-inventory.txt`) and verify nonzero executed test counts (expected ~532 passed, ~663 skipped), zero failures/errors, expected uncertified-host / confinement skips, and recorded sibling revisions.

### 7.3 Phase 3 — Activation Packet and Policy Flip

Present the **Activation Packet** for user approval before committing `.tt.toml`:

- Hosted workflow run URL, run ID, commit SHA, and per-matrix (`3.11`, `3.13`) executed vs skipped test counts from `pytest.xml` compared against the local uncertified pilot (532 passed, 663 skipped).
- Sibling revisions (`science`, `beliefs`, `atoms`, `nodes`) and module list from `module-inventory.txt`.
- Explicit statement of the certified-host omission (663 items across 31 all-skip and 27 mixed modules skipped on `ubuntu-latest`) and the local deliberate verification rule (§5.3: `just test-one`, `TT_FORCE=1 just test-fast`, `just test-full`, `TT_FORCE=1 just gate`).
- Proposed activation diff:
  - `.tt.toml`:
    ```toml
    automatic_broad = false
    broad_targets = ["test", "test-fast", "ci-python"]
    ```
  - `justfile`: `ci_suite_refs := "refs/heads/*"`.
- Exact rollback sequence.

After user activation approval:

1. Commit `.tt.toml` and `ci_suite_refs := "refs/heads/*"`, merge to `main`, and push `main` to `origin`.
2. Verify post-activation behavior and record on `sci-6af05a`:
   - Focused run (`just test-one tests/test_front_door.py`) executes (`execution: "ran"`).
   - Automatic broad run (`just test` or `just hook-pre-push-fast`) records a skip (`execution: "skipped"`, `execution_reason: "policy-disabled"`).
   - Forced failure (`TT_FORCE=1` against a failing test or fixture) records a nonzero exit and propagates failure.
   - Covered branch push to `origin` runs `hook-pre-push-fast` locally (running hygiene and skipping `test-fast`) and triggers a passing hosted CI run.
3. Record the activation timestamp and revision on `sci-6af05a` using the exact lifecycle form parsed by `ops/bin/tt-latency:452`:
   `policy: disabled at <RFC3339-UTC> revision <full-sha>`
4. Record completion summary and activation timestamp/revision on `ops-39bff6`, `ops-8bfa85`, and `ops-56aab7`.

### 7.4 Rollback Route

If hosted CI breaks or local policy-off causes unexpected regressions:

1. Remove `.tt.toml` (or set `automatic_broad = true`) and, if remote coverage is no longer trusted, set `ci_suite_refs := ""` in `justfile`.
2. Commit and integrate to `main`.
3. Record on `sci-6af05a`:
   `policy: enabled at <RFC3339-UTC> revision <full-sha>`
