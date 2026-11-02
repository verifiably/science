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

### 2.4 Remote Repository, Sibling Dependencies, and Uncertified Runner Boundary

- `origin` is `git@github.com:verifiably/science.git`. On GitHub, `verifiably/science` is public (`visibility: public`, `private: false`, default branch `main`). `origin/main` is currently at `7a4915237c9af766fb7d38abc96413839642c60a` (581 commits behind local `main` at `06dd4a748e76ec24d0701c2f27093a33289b7e52`).
- `science/python/pyproject.toml` and `science/python/uv.lock` require `verifiably-beliefs` as an editable path dependency at `../../beliefs/python`, which in turn requires `verifiably-atoms` at `../../atoms/python` and `verifiably-nodes` at `../../nodes/python`.
- All three sibling repositories (`verifiably/beliefs`, `verifiably/atoms`, `verifiably/nodes`) are public on GitHub, and their published `origin/main` heads (`600afa63396bb7353e8f67adf447f28fc6b6e019`, `935535a7275eeaa9d5ea9189b0b2163c021d4a95`, `ce159f2694c3149416f3d7e24ac0fedad5f4253d`) match the Python runtime code on local `main`.
- `python/tests/` has 72 `test_*.py` modules (886 test definitions, ~1195 collected items).
  - Roughly 542 test definitions across 57 modules use `certified_work`, `certified_worker_work`, or downstream snapshot fixtures (`fresh`, `reopened`, `store_config`, `relocated_store`, `rig`, `two_corpora`, `graph`, `shared`, etc.) that initialize or open `atoms`-backed roots under `SCIENCE_TEST_ROOT`. On an uncertified runner (`ubuntu-latest`), `atoms` raises `atoms.core.errors.CapabilityUnavailable` because the runner's kernel/filesystem tuple is not in `atoms`'s certified allowlist.
  - Two tests (`test_snapshot.py::test_a_confined_world_restores_its_sandbox_links_as_links` and `test_belief_path.py::test_under_confinement_the_path_ends_in_an_admitted_belief`) check `beliefs.confinement.host_prerequisites()` before entering `walk_belief_path_confined` and skip with `"confinement unavailable..."` when `bwrap` or unprivileged user namespaces are unavailable.
  - Roughly 330+ test definitions (400+ parameterized items) across 40 modules run against pure-Python or `tmp_path` fixtures without touching `atoms` certified roots (covering CLI surface, parser/schema, config validation, sharing registry, supersession, retention dependency closure, git transport, canonical encoding, adapters, rendering, reports, cursors, findings, front-door routing, and snapshot lineage mechanics).
- Unlike `beliefs` and `atoms`, `science/python/tests/conftest.py` does not yet convert `CapabilityUnavailable` to `pytest.skip` when `VERIFIABLY_UNCERTIFIED_HOST=1`.

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
   - *Decision*: Add `python/tests/uncertified_host.py` (defining `UNCERTIFIED_HOST_VAR = "VERIFIABLY_UNCERTIFIED_HOST"` and `uncertified_host(environ)`) and wire `pytest_runtest_setup`, `pytest_runtest_call`, and `pytest_runtest_teardown` in `python/tests/conftest.py` so `atoms.core.errors.CapabilityUnavailable` converts to `pytest.skip(f"certified tuple unavailable on this host: {error}")` only when `VERIFIABLY_UNCERTIFIED_HOST == "1"`. Add unit tests in `python/tests/test_uncertified_host.py` verifying that `uncertified_host` requires exact `"1"` and that `_skip_if_uncertified` re-raises `CapabilityUnavailable` when unset or set to any other value.
   - *Why*: Mirrors `beliefs` and `atoms` (`UNCERTIFIED_HOST_VAR`), keeping local developer and certified-host runs strictly fail-closed while allowing the uncertified GitHub Actions runner to execute the ~400+ non-certified tests and report exact skip counts in JUnit XML.

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

- Workflow file: `.github/workflows/ci.yml`, name `ci`.
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

### 5.2 Job Matrix, Sibling Checkouts, and Environment

- Job `python`:
  - `runs-on: ubuntu-latest`
  - `timeout-minutes: 20`
  - `strategy`: `fail-fast: false`, `matrix.python-version: ["3.11", "3.13"]` (covering `requires-python = ">=3.11"` in `python/pyproject.toml` and matching `beliefs`).
  - Steps:
    1. Checkout `verifiably/science` into `path: science`.
    2. Checkout `verifiably/beliefs` into `path: beliefs`.
    3. Checkout `verifiably/atoms` into `path: atoms`.
    4. Checkout `verifiably/nodes` into `path: nodes`.
    5. `astral-sh/setup-uv@v5` and `actions/setup-python@v5` with `python-version: ${{ matrix.python-version }}`.
    6. Install `just` (`extractions/setup-just@v2`).
    7. Sync locked dependencies in `working-directory: science/python`: `uv sync --frozen`.
    8. Prepare evidence directory: `mkdir -p "$RUNNER_TEMP/ci-evidence/python-${{ matrix.python-version }}"`.
    9. Run `just ci-python` in `working-directory: science` with environment:
       - `TT_FORCE: "1"`
       - `PYTEST_XDIST_AUTO_NUM_WORKERS: "4"`
       - `VERIFIABLY_UNCERTIFIED_HOST: "1"`
       - `SCIENCE_CI_EVIDENCE_DIR: ${{ runner.temp }}/ci-evidence/python-${{ matrix.python-version }}`
    10. `Require coverage evidence` (`if: always()`): Python step that parses `$SCIENCE_CI_EVIDENCE_DIR/pytest.xml`, verifies every `<skipped>` message contains either `"certified tuple unavailable on this host:"` or `"confinement unavailable"`, verifies `executed > 0`, `failures == 0`, `errors == 0`, writes `$SCIENCE_CI_EVIDENCE_DIR/module-inventory.txt` recording the exact `HEAD` SHAs of `science`, `beliefs`, `atoms`, and `nodes`, the list of `tests/test_*.py` modules without `certified_work` / `certified_worker_work`, and `python/pyproject.toml`, and prints `executed=<N> skipped=<M>`.
    11. Upload artifact (`if: always()`): `actions/upload-artifact@v4` with `name: python-${{ matrix.python-version }}-coverage-evidence`, `path: ${{ runner.temp }}/ci-evidence/python-${{ matrix.python-version }}`, `if-no-files-found: error`, `retention-days: 30`.

### 5.3 Certified-Host Omission and Local Deliberate Routes

- Hosted CI (`ubuntu-latest`) cannot supply the certified Linux kernel + ext4 volume tuple required by `atoms` (`docs/certification/2026-09-03-ext4-linux-7.2.2-arch1-1.json`) or unprivileged bubblewrap sandboxes. Tests that touch `atoms` roots skip via `VERIFIABLY_UNCERTIFIED_HOST=1` and are recorded in `pytest.xml`.
- Full certified-volume and confinement verification remains available on the certified developer host through explicit commands that bypass or force policy:
  - Focused during implementation: `just test-one <pytest args>`
  - Forced fast selection: `TT_FORCE=1 just test-fast`
  - Forced full suite: `just test-full` (or `TT_FORCE=1 just test`)
  - Forced full gate: `TT_FORCE=1 just gate`
- `README.md` and `AGENTS.md` will document both the local policy-off behavior (`.tt.toml`, `just test-one`, `just test-full`, `TT_FORCE=1 just gate`) and the hosted vs certified-host split.

## 6. Isolated Front-Door and Workflow Conformance Tests

Replace the old fake-`just` tests in `python/tests/test_front_door.py` with an isolated fixture checkout (`FrontDoor`) that builds its environment key by key (inheriting no `TT_FORCE`, `GITHUB_ACTIONS`, `CI`, or host `GIT_*` variables; setting `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1`), copies `justfile`, `tools/tt`, `.githooks/pre-commit`, and `.githooks/pre-push` into a temporary Git repository, replaces `check_hygiene_cmd`, `fast_cmd`, `test_cmd`, `one_cmd`, and `ci_py_test_cmd` with lightweight marker invocations, and verifies:

1. Staged paths route docs-only commits (`README.md`, `AGENTS.md`, `docs/*.md`, `tasks/*.md`) to `hook-pre-commit-docs` and code/fixture commits (including `python/tests/fixtures/foo.md` and `justfile`) to `hook-pre-commit`.
2. Under `automatic_broad = false`, `hook-pre-commit` and `hook-pre-commit-docs` run hygiene (`execution: "ran"`), while `hook-pre-push`, `hook-pre-push-fast`, `check`, and `gate` run `check-hygiene` once (`execution: "ran"`) and skip their broad child (`test` or `test-fast` with `execution: "skipped"`, `execution_reason: "policy-disabled"`).
3. Under `automatic_broad = true` (or absent `.tt.toml`), `hook-pre-push` and `hook-pre-push-fast` run hygiene first and then run `test` or `test-fast`; a failing hygiene step stops before the broad child starts; a failing broad child propagates its nonzero exit status.
4. `test-full` forces `test` (`execution: "ran"`, `execution_reason: "forced"`) and propagates failures; `test-one` runs under policy-off and forwards arguments with spaces, `$`, and globs intact.
5. On `GITHUB_ACTIONS=true` with `automatic_broad = false` and without `TT_FORCE=1`, `test`, `test-fast`, `ci-python`, and `hook-pre-push-fast` fail with exit code 2 and `TT_FORCE=1` on stderr without recording a skipped row; with `TT_FORCE=1`, they run.
6. `.githooks/pre-push` routes branch pushes to `origin` (`refs/heads/main`, `refs/heads/feat/x`) to `hook-pre-push-fast` when `ci_suite_refs = "refs/heads/*"`, routes tag pushes (`refs/tags/v1`), other remotes (`backup`), or empty `ci_suite_refs` to `hook-pre-push`, emits the policy warning on stderr only when `hook-pre-push` will skip `test`, refuses malformed `.tt.toml` with exit code 2, refuses missing SSH keepalive with exit code 1, and clears `git rev-parse --local-env-vars`.
7. `.github/workflows/ci.yml` conformance checks verify triggers (`push` on `branches: ["**"]`, `pull_request` with the same-repo skip condition, `workflow_dispatch`), concurrency group and `cancel-in-progress: true`, `TT_FORCE: "1"`, `VERIFIABLY_UNCERTIFIED_HOST: "1"`, sibling checkouts (`science`, `beliefs`, `atoms`, `nodes`), `just ci-python`, JUnit + `module-inventory.txt` verification, and `actions/upload-artifact@v4`.

## 7. Rollout Sequence, Approval Packets, and Rollback

### 7.1 Phase 1 — Local Implementation (Policy Enabled)

1. Implement `python/tests/uncertified_host.py`, `python/tests/test_uncertified_host.py`, and the `conftest.py` hooks.
2. Update `justfile` (`check-hygiene`, untimed `check`, `test-full`, `ci-python`, split `hook-pre-commit`, `hook-pre-commit-docs`, `hook-pre-push`, `hook-pre-push-fast`), `.githooks/pre-push` (policy warning), `.github/workflows/ci.yml`, `python/tests/test_front_door.py`, `README.md`, and `AGENTS.md`.
3. Keep `.tt.toml` absent and `ci_suite_refs := ""` (or test `ci_suite_refs` in fixture checkouts) until the workflow is published and verified on GitHub.
4. When the hook-split and workflow commit integrates to `main`, record on `sci-6af05a`:
   `policy: enabled at <RFC3339-UTC> revision <full-sha>`

### 7.2 Phase 2 — Publication Packet and Hosted CI Verification

Before pushing to `origin` (`git@github.com:verifiably/science.git`), present the **Publication Packet** for user approval:

- Target remote and visibility: `origin` (`verifiably/science`, public repository; standard GitHub-hosted runners are free under `ops-2bf257`).
- Exact ref(s) and commit SHA to push (noting that `origin/main` is currently at `7a4915237c9af766fb7d38abc96413839642c60a`, so pushing `main` or `feat/sci-6af05a-test-policy` will publish the 581 local `main` commits plus the `sci-6af05a` commits).
- Confirmation that `.tt.toml` is still absent (local policy remains enabled until CI passes).

After user push approval:

- Push and watch the GitHub Actions `ci` workflow run via `gh run list` / `gh run watch`.
- Download the uploaded `python-3.11-coverage-evidence` and `python-3.13-coverage-evidence` artifacts (`pytest.xml` and `module-inventory.txt`) and verify nonzero executed test counts, zero failures/errors, expected certified-host skips, and recorded sibling revisions.

### 7.3 Phase 3 — Activation Packet and Policy Flip

Present the **Activation Packet** for user approval before committing `.tt.toml`:

- Hosted workflow run URL, run ID, commit SHA, and per-matrix (`3.11`, `3.13`) executed vs skipped test counts from `pytest.xml`.
- Sibling revisions (`science`, `beliefs`, `atoms`, `nodes`) and eligible module count from `module-inventory.txt`.
- Explicit statement of the certified-host omission (`CapabilityUnavailable` and `bwrap` confinement tests skipped on `ubuntu-latest`) and the local deliberate routes (`just test-one`, `just test-full`, `TT_FORCE=1 just gate`) that retain certified coverage on the certified host.
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
3. Record on `sci-6af05a`:
   `policy: disabled at <RFC3339-UTC> revision <full-sha>`
4. Record completion summary and activation timestamp/revision on `ops-39bff6`, `ops-8bfa85`, and `ops-56aab7`.

### 7.4 Rollback Route

If hosted CI breaks or local policy-off causes unexpected regressions:

1. Remove `.tt.toml` (or set `automatic_broad = true`) and, if remote coverage is no longer trusted, set `ci_suite_refs := ""` in `justfile`.
2. Commit and integrate to `main`.
3. Record on `sci-6af05a`:
   `policy: enabled at <RFC3339-UTC> revision <full-sha>`
