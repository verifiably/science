# Science Test Execution Policy and Hosted Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `science`'s local hygiene and broad test recipes under `tools/tt` policy control, add an opt-in `VERIFIABLY_UNCERTIFIED_HOST=1` pytest gate and GitHub Actions `CI` workflow with durable JUnit + module-inventory artifacts, and activate `.tt.toml` (`automatic_broad = false`) and `ci_suite_refs := "refs/heads/*"` after hosted verification.

**Architecture:** `justfile` separates mandatory seconds-long checks (`check-hygiene`, `hook-pre-commit`, `hook-pre-commit-docs`, and the hygiene step of `hook-pre-push` / `hook-pre-push-fast`) from broad pytest targets (`test`, `test-fast`, `ci-python`) and provides untimed composition/force aliases (`check`, `gate`, `test-full`). `python/tests/uncertified_host.py` and `python/tests/conftest.py` convert `atoms.core.errors.CapabilityUnavailable` (both direct and direct `__cause__`) into `pytest.skip` only when `VERIFIABLY_UNCERTIFIED_HOST=1`, allowing `.github/workflows/ci.yml` to run the non-certified tests on `ubuntu-latest` across Python 3.11 and 3.13 while preserving fail-closed certified-host testing locally.

**Tech Stack:** `just`, POSIX `sh` git hooks (`.githooks/pre-commit`, `.githooks/pre-push`), `tools/tt` (the version `main` carries, currently v10), Python 3.11 / 3.13, `uv`, `pytest`, `pytest-xdist`, `pytest-testmon`, GitHub Actions.

**Spec:** `docs/specs/2026-11-02-test-execution-policy-design.md` (frozen at `8cd98e827a9de0df9836a353349f2cfed23915a7`)

## Global Constraints

- Keep the versions of `tools/tt` (currently v10 at `dc39b31`), `tools/ops-check` (v17), and `tools/ops-docs` (v6) that `main` carries; before integrating to `main`, check whether `main` has advanced and merge `main` into `feat/sci-6af05a-test-policy` (never rebase) if it has.
- Every `just` recipe that records a timing row runs through `python3 tools/tt`; do not call `pytest` directly from the shell.
- `check`, `gate`, and `test-full` are untimed aliases so only their child targets (`check-hygiene`, `test`) record timing rows.
- `VERIFIABLY_UNCERTIFIED_HOST` is opt-in and matches only the exact string `"1"`; anywhere else `CapabilityUnavailable` remains a test failure.
- Subprocess tests in `python/tests/test_front_door.py` build `env` key by key, inherit no `TT_FORCE`, `GITHUB_ACTIONS`, `CI`, or host `GIT_*` variables, and set `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1`.
- Do not commit `.tt.toml` or widen `ci_suite_refs := "refs/heads/*"` until an approved hosted CI run finishes with a nonzero executed test count and user activation approval is granted.
- Avoid machine-specific absolute paths and hostnames in committed code, comments, and docs (`python3 tools/ops-check` enforces this).
- On hook-split integration to `main` and on any rollback, record on `sci-6af05a`: `policy: enabled at <RFC3339-UTC> revision <full-sha>`. On activation of `.tt.toml`, record on `sci-6af05a`: `policy: disabled at <RFC3339-UTC> revision <full-sha>`.

## Review Focus

1. **Wrapped `CapabilityUnavailable` (`ExecutionError` or `Refused` with `__cause__ = CapabilityUnavailable`) on an uncertified host**: If a test reaches `beliefs/root.py:871,1043,1359` (`nodes.core.errors.ExecutionError`) or `science/config.py:104,114` (`science.refusal.Refused`) without an earlier `register_root` / `read_chain` call, the unhandled wrapper exception must still skip under `VERIFIABLY_UNCERTIFIED_HOST=1` and re-raise when unset (pinned in Task 2, `test_uncertified_host.py`).
2. **Non-`"1"` `VERIFIABLY_UNCERTIFIED_HOST` values (`""`, `"0"`, `"true"`, `"yes"`)**: Must never disarm the certified-host failure gate (pinned in Task 2, `test_uncertified_host.py`).
3. **Hosted CI running a broad target (`ci-python` or nested `hook-pre-push-fast`) under `automatic_broad = false` when `TT_FORCE=1` is omitted**: `tt` must exit `2` with `"TT_FORCE=1"` on stderr and record no skipped broad row (pinned in Task 3, `test_front_door.py`).
4. **`ci-python` invoked with `SCIENCE_CI_EVIDENCE_DIR` unset or relative**: Must exit `2` with an error on stderr before running pytest (pinned in Task 3, `test_front_door.py`).
5. **Malformed `.tt.toml` (`automatic_broad = "no"`) or leaked git hook env vars (`GIT_DIR`, `GIT_WORK_TREE`) during `.githooks/pre-push`**: `.githooks/pre-push` must exit `2` on malformed `.tt.toml` before invoking `just`, and must clear `git rev-parse --local-env-vars` before invoking child commands (pinned in Task 3, `test_front_door.py`).

---

### Task 1: Execution Setup and Full-Suite Baseline

**Files:**
- Modify: `tasks/sci-6af05a.md` (via `tasks note`)

**Interfaces:**
- Consumes: hydrated `.worktrees/sci-6af05a` (`git config core.hooksPath .githooks`, `python/.venv` synced from `python/uv.lock`).
- Produces: recorded baseline test count (`1195 passed`) and duration on `sci-6af05a` before any code changes.

- [ ] **Step 1: Verify worktree hydration and clean status**

Run in `.worktrees/sci-6af05a`:
```bash
git status --short
git config --get core.hooksPath
(cd python && uv sync --frozen)
```
Expected: clean status, `core.hooksPath` is `.githooks`, `uv sync --frozen` reports `Audited 65 packages`.

- [ ] **Step 2: Run the baseline hygiene check and full test suite**

Run in `.worktrees/sci-6af05a`:
```bash
just check
just test
```
Expected: `just check` exits 0; `just test` exits 0 with `1195 passed`.

- [ ] **Step 3: Record the baseline note on `sci-6af05a`**

Run in `.worktrees/sci-6af05a`:
```bash
tasks note sci-6af05a "baseline: just check and just test passed in .worktrees/sci-6af05a before code changes (1195 passed)."
```
Expected: `{"id":"sci-6af05a","warnings":[]}`.

---

### Task 2: Opt-In Uncertified-Host Gate (`uncertified_host.py` and `conftest.py`)

**Files:**
- Create: `python/tests/uncertified_host.py`
- Modify: `python/tests/conftest.py:1-30`
- Test: `python/tests/test_uncertified_host.py`

**Interfaces:**
- Consumes: `atoms.core.errors.CapabilityUnavailable`, `nodes.core.errors.ExecutionError`, `science.refusal.{Refusal, Refused}`
- Produces:
  - `uncertified_host.UNCERTIFIED_HOST_VAR: str = "VERIFIABLY_UNCERTIFIED_HOST"`
  - `uncertified_host.uncertified_host(environ: Mapping[str, str]) -> bool`
  - `uncertified_host.capability_unavailable_from(error: BaseException) -> CapabilityUnavailable | None`
  - `conftest._report_missing_capability(error: BaseException) -> None`
  - `conftest.pytest_runtest_setup(item)`, `conftest.pytest_runtest_call(item)`, `conftest.pytest_runtest_teardown(item, nextitem)`

- [ ] **Step 1: Write the failing unit tests in `python/tests/test_uncertified_host.py`**

Create `python/tests/test_uncertified_host.py`:
```python
"""Unit tests for the opt-in uncertified-host capability gate."""

import pytest
from _pytest.outcomes import Skipped
from atoms.core.errors import CapabilityUnavailable
from nodes.core.errors import ExecutionError
from science.refusal import Refusal, Refused

import conftest
from uncertified_host import (
    UNCERTIFIED_HOST_VAR,
    capability_unavailable_from,
    uncertified_host,
)


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({UNCERTIFIED_HOST_VAR: "1"}, True),
        ({}, False),
        ({UNCERTIFIED_HOST_VAR: ""}, False),
        ({UNCERTIFIED_HOST_VAR: "0"}, False),
        ({UNCERTIFIED_HOST_VAR: "true"}, False),
        ({UNCERTIFIED_HOST_VAR: "yes"}, False),
    ],
)
def test_uncertified_host_requires_exact_one(env: dict[str, str], expected: bool) -> None:
    assert uncertified_host(env) is expected


def test_capability_unavailable_from_unwraps_direct_and_chained_cause() -> None:
    raw = CapabilityUnavailable("ext4 durability probe failed")
    assert capability_unavailable_from(raw) is raw

    wrapped_exec = ExecutionError(str(raw), index=None, applied=0)
    wrapped_exec.__cause__ = raw
    assert capability_unavailable_from(wrapped_exec) is raw

    wrapped_refused = Refused(Refusal("kernel-refused", str(raw), {"kind": "CapabilityUnavailable"}))
    wrapped_refused.__cause__ = raw
    assert capability_unavailable_from(wrapped_refused) is raw

    unrelated = RuntimeError("boom")
    unrelated.__cause__ = ValueError("other")
    assert capability_unavailable_from(unrelated) is None


def test_report_missing_capability_skips_only_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = CapabilityUnavailable("ext4 tuple unavailable")
    wrapped = ExecutionError(str(raw), index=None, applied=0)
    wrapped.__cause__ = raw

    monkeypatch.delenv(UNCERTIFIED_HOST_VAR, raising=False)
    conftest._report_missing_capability(raw)
    conftest._report_missing_capability(wrapped)

    monkeypatch.setenv(UNCERTIFIED_HOST_VAR, "0")
    conftest._report_missing_capability(raw)

    monkeypatch.setenv(UNCERTIFIED_HOST_VAR, "1")
    with pytest.raises(Skipped, match="certified tuple unavailable on this host: ext4 tuple unavailable"):
        conftest._report_missing_capability(raw)
    with pytest.raises(Skipped, match="certified tuple unavailable on this host: ext4 tuple unavailable"):
        conftest._report_missing_capability(wrapped)
```

- [ ] **Step 2: Run `just test-one tests/test_uncertified_host.py` to verify it fails**

Run: `just test-one tests/test_uncertified_host.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'uncertified_host'`.

- [ ] **Step 3: Implement `python/tests/uncertified_host.py` and wire `python/tests/conftest.py`**

Create `python/tests/uncertified_host.py` with `UNCERTIFIED_HOST_VAR = "VERIFIABLY_UNCERTIFIED_HOST"`, `uncertified_host(environ: Mapping[str, str]) -> bool` returning `environ.get(UNCERTIFIED_HOST_VAR, "") == "1"`, and `capability_unavailable_from(error: BaseException) -> CapabilityUnavailable | None` returning `error` when `isinstance(error, CapabilityUnavailable)` else `error.__cause__` when `isinstance(error.__cause__, CapabilityUnavailable)` else `None`.

In `python/tests/conftest.py`, import `from uncertified_host import capability_unavailable_from, uncertified_host` and add:
```python
def _report_missing_capability(error: BaseException) -> None:
    cause = capability_unavailable_from(error)
    if cause is not None and uncertified_host(os.environ):
        pytest.skip(f"certified tuple unavailable on this host: {cause}")


@pytest.hookimpl(wrapper=True)
def pytest_runtest_setup(item):
    try:
        return (yield)
    except Exception as error:
        _report_missing_capability(error)
        raise


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    try:
        return (yield)
    except Exception as error:
        _report_missing_capability(error)
        raise


@pytest.hookimpl(wrapper=True)
def pytest_runtest_teardown(item, nextitem):
    try:
        return (yield)
    except Exception as error:
        _report_missing_capability(error)
        raise
```

- [ ] **Step 4: Run `just test-one` on `test_uncertified_host.py` and verify uncertified-volume skipping on `test_stores.py`**

Run:
```bash
just test-one tests/test_uncertified_host.py
SCIENCE_TEST_ROOT=/tmp/sci-uncertified-gate-check VERIFIABLY_UNCERTIFIED_HOST=1 just test-one tests/test_stores.py tests/test_uncertified_host.py
rm -rf /tmp/sci-uncertified-gate-check
```
Expected: first run passes 8/8 tests in `test_uncertified_host.py`; second run passes 20 tests (12 non-certified in `test_stores.py` + 8 in `test_uncertified_host.py`) and skips 30 certified tests in `test_stores.py` with 0 failures.

- [ ] **Step 5: Commit**

```bash
git add python/tests/uncertified_host.py python/tests/conftest.py python/tests/test_uncertified_host.py
git commit -m "test(conftest): add opt-in VERIFIABLY_UNCERTIFIED_HOST skip gate (sci-6af05a)"
```

---

### Task 3: Front-Door Recipe Split, `ci-python`, Pre-Push Policy Warning, and Isolated Route Tests

**Files:**
- Modify: `justfile`
- Modify: `.githooks/pre-push`
- Modify: `python/tests/test_front_door.py`

**Interfaces:**
- Consumes: `tools/tt` (`read_policy`, `execution_decision`), `.githooks/pre-commit`, `.githooks/pre-push`, `justfile`
- Produces:
  - `justfile` variables: `xdist`, `fast_cmd`, `test_cmd`, `one_cmd`, `check_hygiene_cmd`, `docs_paths`, `docs_check_cmd`, `ci_suite_refs := ""`, `ci_remote := "origin"`, `ci_evidence_cmd`, `ci_py_test_cmd`
  - `justfile` recipes: `test-one +args`, `test-fast`, `test`, `test-full`, `ci-python`, `check-hygiene`, `check`, `gate`, `docs`, `hook-pre-commit`, `hook-pre-commit-docs`, `hook-pre-push`, `hook-pre-push-fast`
  - `.githooks/pre-push` policy warning and error handling (`exit 2` on unreadable/malformed `.tt.toml`)
  - `FrontDoor` isolated fixture in `python/tests/test_front_door.py`

- [ ] **Step 1: Replace `python/tests/test_front_door.py` with isolated `FrontDoor` route and policy tests (RED)**

Update `python/tests/test_front_door.py` to define `FrontDoor(base: Path)` (isolated git repo in `tmp_path` with key-by-key `self.env` containing only `PATH`, `HOME`, `USER`, `GIT_CONFIG_GLOBAL="/dev/null"`, `GIT_CONFIG_NOSYSTEM="1"`, `GIT_AUTHOR_*`, `GIT_COMMITTER_*`, `TT_LOG`, plus a stub `host-budget` and `ssh` in `base / "bin"` and `marker.py` replacing `check_hygiene_cmd`, `fast_cmd`, `test_cmd`, `one_cmd`, and `ci_py_test_cmd`) and tests:
- `test_fixture_environment_is_isolated(front_door)`: asserts no `TT_FORCE`, `GITHUB_ACTIONS`, `CI`, or extra `GIT_*` vars in `front_door.env`.
- `test_recipes_match_shared_contract(front_door)`: asserts `just --summary` equals `{"test-fast", "test-one", "test", "test-full", "ci-python", "check-hygiene", "check", "gate", "docs", "hook-pre-commit", "hook-pre-commit-docs", "hook-pre-push", "hook-pre-push-fast"}`.
- `test_pre_commit_routes_docs_paths_only_when_every_staged_file_matches(front_door, path, expected_target)`: parametrized over `("README.md", "hook-pre-commit-docs")`, `("AGENTS.md", "hook-pre-commit-docs")`, `("docs/stores.md", "hook-pre-commit-docs")`, `("tasks/sci-6af05a.md", "hook-pre-commit-docs")`, `("python/tests/fixtures/doc.md", "hook-pre-commit")`, `("justfile", "hook-pre-commit")`.
- `test_policy_off_keeps_hygiene_and_skips_broad_children(front_door, recipe, expected_skipped)`: parametrized over `("check", [])`, `("gate", ["test"])`, `("hook-pre-commit", [])`, `("hook-pre-commit-docs", [])`, `("hook-pre-push", ["test"])`, `("hook-pre-push-fast", ["test-fast"])`. Verifies `markers() == [["hygiene"]]` and skipped rows have `execution == "skipped"`, `execution_reason == "policy-disabled"`, and `exit`, `tests`, `selection`, `slowest` all `None`.
- `test_enabled_hooks_run_hygiene_then_suite_and_stop_on_hygiene_failure(front_door)`: verifies `hook-pre-push` (`[["hygiene"], ["suite"]]`), `hook-pre-push-fast` (`[["hygiene"], ["fast"]]`), hygiene failure (`FAIL_TARGET="hygiene"` -> exit 7, suite not started), and suite failure (`FAIL_TARGET="fast"` -> exit 7).
- `test_test_full_and_forced_gate_override_policy_off(front_door)`: verifies `test-full` runs `test` with `execution_reason == "forced"` and propagates `FAIL_TARGET="suite"` exit 7; verifies `TT_FORCE=1 just gate` runs both `check-hygiene` and `test` with `execution_reason == "forced"`.
- `test_test_one_runs_under_policy_off_and_preserves_arguments(front_door)`: verifies `just test-one -k "a and b" "tests/p q.py" "it's" '$HOME' 'renders *'` passes arguments intact, records `("test-one", "ran")`, and `just test-one` without arguments exits nonzero.
- `test_ci_python_requires_absolute_evidence_dir_and_runs_when_forced(front_door, tmp_path)`: under `automatic_broad = false`, verifies `TT_FORCE=1 just ci-python` without `SCIENCE_CI_EVIDENCE_DIR` or with relative `SCIENCE_CI_EVIDENCE_DIR="rel/path"` fails with exit 2 (`CI evidence path must be absolute` / `set SCIENCE_CI_EVIDENCE_DIR`), and with `SCIENCE_CI_EVIDENCE_DIR=str(tmp_path / "ev")` runs `ops-check` and `ci_py_test_cmd`.
- `test_hosted_broad_targets_without_force_fail_loudly(front_door, target)`: parametrized over `("test", "test-fast", "ci-python", "hook-pre-push-fast")` with `GITHUB_ACTIONS="true"` and `automatic_broad = false`: exits 2 with `"TT_FORCE=1"` in stderr and records no skipped row; with `TT_FORCE="1"`, succeeds.
- `test_pre_push_routes_refs_and_warns_only_on_uncovered_skipped_push(front_door)`: tests `.githooks/pre-push` ref routing (`refs/heads/main`, `refs/heads/feat/x`, `refs/tags/v1`, deletion ref, malformed ref, empty `ci_suite_refs`, `backup` remote), verifies stdin ref bytes reach the recipe intact, and verifies the stderr warning `remote full-suite coverage is not declared for this push` appears only when `recipe=hook-pre-push` and `test` is skipped by policy.
- `test_unreadable_policy_refuses_push(front_door)`: writes invalid `.tt.toml` (`automatic_broad = "no"\nbroad_targets = ["test"]\n`), runs `.githooks/pre-push`, asserts exit 2 and `cannot inspect test execution policy` in stderr.
- `test_missing_keepalive_refuses_before_gate(front_door)`: sets `SSH_INTERVAL="0"`, runs `.githooks/pre-push` with `git@example.invalid:repo`, asserts exit 1 and `ServerAliveInterval 60` in stderr.
- `test_pre_push_clears_git_local_environment(front_door)`: passes `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` into `.githooks/pre-push` and verifies the child `marker.py` environment has none of them.

- [ ] **Step 2: Run `just test-one tests/test_front_door.py` to verify it fails**

Run: `just test-one tests/test_front_door.py`
Expected: FAIL because `justfile` still has `check_cmd` instead of `check_hygiene_cmd`, lacks `check-hygiene`, `test-full`, and `ci-python`, and `.githooks/pre-push` lacks the policy warning block.

- [ ] **Step 3: Update `justfile` and `.githooks/pre-push`**

In `justfile`:
- Rename `check_cmd` to `check_hygiene_cmd := "python3 tools/ops-check && python3 tools/ops-docs check && tasks check"` and set `docs_check_cmd := check_hygiene_cmd`.
- Remove unused `push_fast_cmd`.
- Add:
  ```just
  ci_evidence_cmd := "case \"${SCIENCE_CI_EVIDENCE_DIR:?set SCIENCE_CI_EVIDENCE_DIR}\" in /*) ;; *) echo \"CI evidence path must be absolute\" >&2; exit 2;; esac"
  ci_py_test_cmd := "cd python && uv run --frozen pytest --junitxml=\"$SCIENCE_CI_EVIDENCE_DIR/pytest.xml\" " + xdist
  ```
- Define:
  ```just
  # Deliberate full-suite verification; the inner `test` is the only timing record.
  test-full:
      TT_FORCE=1 just test

  # Hosted CI target: no host-budget or tasks binary on the runner; writes JUnit into
  # SCIENCE_CI_EVIDENCE_DIR and runs the vendored ops-check hygiene gate.
  ci-python:
      {{tt}} ci-python -- sh -c '{{ci_evidence_cmd}} && python3 tools/ops-check && {{ci_py_test_cmd}}'

  # Mandatory hygiene checks: ops-check, ops-docs check, and tasks check.
  check-hygiene:
      {{tt}} check-hygiene -- sh -c '{{check_hygiene_cmd}}'

  # Untimed composition; this repository has no separate lint/typecheck workload.
  check:
      just check-hygiene

  gate:
      just check
      just test

  hook-pre-commit:
      {{tt}} hook-pre-commit -- sh -c '{{check_hygiene_cmd}}'

  hook-pre-commit-docs:
      {{tt}} hook-pre-commit-docs -- sh -c '{{docs_check_cmd}}'

  hook-pre-push:
      {{tt}} hook-pre-push -- sh -c '{{check_hygiene_cmd}}'
      just test

  hook-pre-push-fast:
      {{tt}} hook-pre-push-fast -- sh -c '{{check_hygiene_cmd}}'
      just test-fast
  ```

In `.githooks/pre-push`, insert the `ops` template's policy inspection block after `unset $git_local_vars` and before `printf %s "$refs" | exec just "$recipe"`:
```sh
# Warn when local policy skips a suite for which this push declares no remote cover.
# Load the project's configured wrapper, so this hook has no second policy parser.
if [ "$recipe" = hook-pre-push ]; then
    tt_command=$(just --evaluate tt 2>/dev/null) || tt_command=
    if [ -n "$tt_command" ]; then
        python3 - "$tt_command" <<'PY' || exit $?
import importlib.machinery, importlib.util, os, pathlib, shlex, sys
try:
    command = shlex.split(sys.argv[1])
    loader = importlib.machinery.SourceFileLoader('tt_policy', command[-1])
    spec = importlib.util.spec_from_loader(loader.name, loader)
    tt = importlib.util.module_from_spec(spec)
    loader.exec_module(tt)
    execution, _ = tt.execution_decision('test', tt.read_policy(pathlib.Path.cwd()), os.environ)
    if execution == 'skipped':
        sys.stderr.write('pre-push: local test skipped by policy; remote full-suite coverage is not declared for this push. Use TT_FORCE=1 for deliberate local verification.\n')
except (ValueError, OSError, IndexError, AttributeError) as error:
    sys.stderr.write(f'pre-push: cannot inspect test execution policy: {error}\n')
    sys.exit(2)
PY
    fi
fi
```

- [ ] **Step 4: Run `just test-one tests/test_front_door.py` and `just check`**

Run:
```bash
just test-one tests/test_front_door.py
just check
```
Expected: all tests in `test_front_door.py` pass; `just check` exits 0.

- [ ] **Step 5: Commit**

```bash
git add justfile .githooks/pre-push python/tests/test_front_door.py
git commit -m "build(gates): split hygiene and broad test recipes under tt policy (sci-6af05a)"
```

---

### Task 4: Hosted CI Workflow (`.github/workflows/ci.yml`) and Project Guides (`README.md`, `AGENTS.md`)

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `python/tests/test_front_door.py`

**Interfaces:**
- Consumes: `just ci-python`, `SCIENCE_CI_EVIDENCE_DIR`, `VERIFIABLY_UNCERTIFIED_HOST=1`, `TT_FORCE=1`, `PYTEST_XDIST_AUTO_NUM_WORKERS=4`
- Produces: `.github/workflows/ci.yml` (`name: CI`, job `python` on `ubuntu-latest` for Python `3.11` and `3.13`), updated `README.md` and `AGENTS.md`

- [ ] **Step 1: Add workflow conformance tests in `python/tests/test_front_door.py` (RED)**

Append to `python/tests/test_front_door.py`:
- `test_ci_workflow_conformance()`: reads `REPO / ".github/workflows/ci.yml"` and asserts:
  - Triggers: `push` with `branches: ["**"]`, `pull_request`, `workflow_dispatch`.
  - Job condition: `if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name != github.repository`.
  - Concurrency: `group: ${{ github.workflow }}-${{ github.ref }}` and `cancel-in-progress: true`.
  - Permissions & timeout: `contents: read` and `timeout-minutes: 30`.
  - Matrix & env: `python-version: ["3.11", "3.13"]`, `TT_FORCE: "1"`, `PYTEST_XDIST_AUTO_NUM_WORKERS: "4"`, `working-directory: science/python`.
  - Pinned action SHAs: all `uses:` match `[^@]+@[0-9a-f]{40}`, including `actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0`, `astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990` with `version: "0.11.29"` and `python-version: ${{ matrix.python-version }}`, `extractions/setup-just@53165ef7e734c5c07cb06b3c8e7b647c5aa16db3`, `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`, and `"setup-python"` is absent.
  - Sibling checkouts: `path: science`, `repository: verifiably/beliefs` (`path: beliefs`), `repository: verifiably/atoms` (`path: atoms`), `repository: verifiably/nodes` (`path: nodes`).
  - Step ordering: `"Prepare coverage evidence"` < `"uv sync --frozen"` < `"just ci-python"` < `"Require coverage evidence"` < `"actions/upload-artifact@"`.

- [ ] **Step 2: Run `just test-one tests/test_front_door.py -k test_ci_workflow_conformance` to verify it fails**

Run: `just test-one tests/test_front_door.py -k test_ci_workflow_conformance`
Expected: FAIL with `FileNotFoundError` for `.github/workflows/ci.yml`.

- [ ] **Step 3: Create `.github/workflows/ci.yml` and update `README.md` and `AGENTS.md`**

Create `.github/workflows/ci.yml` matching Spec §5.1–§5.2 (`name: CI`, triggers `push` on `branches: ["**"]`, `pull_request`, `workflow_dispatch`, `permissions: contents: read`, `concurrency` per workflow-ref with `cancel-in-progress: true`, job `python` on `ubuntu-latest` with fork-only PR guard, `timeout-minutes: 30`, matrix `["3.11", "3.13"]`, `TT_FORCE: "1"`, `PYTEST_XDIST_AUTO_NUM_WORKERS: "4"`, `defaults.run.working-directory: science/python`, SHA-pinned checkouts of `science`, `verifiably/beliefs`, `verifiably/atoms`, `verifiably/nodes`, `setup-uv` `0.11.29` with `python-version: ${{ matrix.python-version }}`, `setup-just`, `Prepare coverage evidence` writing `module-inventory.txt`, `uv sync --frozen`, `just ci-python` with `VERIFIABLY_UNCERTIFIED_HOST: "1"`, `Require coverage evidence` parsing `pytest.xml` to require `executed > 0`, `failures == 0`, `errors == 0`, and only `"certified tuple unavailable on this host:"` or `"confinement unavailable"` skip reasons, and `actions/upload-artifact` uploading `python-${{ matrix.python-version }}-coverage` with `retention-days: 30` and `if-no-files-found: error`).

Update `README.md` (`## Development`) and `AGENTS.md` (`## Gates`) to document:
- `just test-one <pytest args>` (protected focused loop), `just test-fast` (broad inner loop), `just test` (broad full suite), `just test-full` (untimed `TT_FORCE=1 just test`), `just ci-python` (hosted CI target), `just check-hygiene` (mandatory hygiene), `just check` (untimed alias), `just gate` (untimed `check` + `test`; `TT_FORCE=1 just gate` forces the full gate).
- `.tt.toml` policy behavior (`automatic_broad = false` skips `test`, `test-fast`, and `ci-python` locally unless `TT_FORCE=1`), `.githooks/pre-push` routing (`ci_suite_refs` to `hook-pre-push-fast`, uncovered refs to `hook-pre-push` with stderr warning when skipped).
- Hosted CI vs certified-host split (532 baseline items run on `ubuntu-latest`, 663 items requiring the certified `atoms` kernel + ext4 tuple or `bwrap` confinement skip via `VERIFIABLY_UNCERTIFIED_HOST=1`) and the mandatory certified-host verification rule:
  - Every change runs `just test-one` on its affected test module(s).
  - Any branch touching `python/` must run `TT_FORCE=1 just test-fast` on the certified host before merging to `main`.
  - Any branch changing shared test fixtures (`python/tests/conftest.py`, `python/tests/helpers/*`), session/dispatch/store lifecycle modules (`python/src/science/{config,session,dispatch,holdings,publication,world_belief}.py`), or sibling/locked dependencies (`python/pyproject.toml`, `python/uv.lock`) must run `just test-full` on the certified host before merging to `main`.

- [ ] **Step 4: Run `just test-one` and `just check`**

Run:
```bash
just test-one tests/test_front_door.py tests/test_uncertified_host.py
just check
```
Expected: all tests in `test_front_door.py` and `test_uncertified_host.py` pass; `just check` (`ops-check`, `ops-docs check`, `tasks check`) exits 0.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml README.md AGENTS.md python/tests/test_front_door.py
git commit -m "ci: add hosted Python workflow and document certified-host verification rule (sci-6af05a)"
```

---

### Task 5: Whole-Branch Final Review and Phase 1 Integration to `main`

**Files:**
- Modify: `tasks/sci-6af05a.md` (via `tasks note`)

**Interfaces:**
- Consumes: completed Tasks 1–4 on `feat/sci-6af05a-test-policy` (with `.tt.toml` absent and `ci_suite_refs := ""`)
- Produces: reviewed Phase 1 branch integrated to `main` with `policy: enabled at <RFC3339-UTC> revision <full-sha>` recorded on `sci-6af05a`.

- [ ] **Step 1: Sync with `main` if `main` has moved, then run full certified verification**

Run in `.worktrees/sci-6af05a`:
```bash
git rev-list --left-right --count main...HEAD
# If main has commits ahead of the merge base, merge main (never rebase):
git merge --no-edit main
just check
just test-full
```
Expected: `just check` exits 0; `just test-full` exits 0 with `0 failed, 0 errors`, and `passed == baseline (1195) + new tests added in test_uncertified_host.py and test_front_door.py`.

- [ ] **Step 2: Run whole-branch final code review (`requesting-code-review`)**

Dispatch a fresh read-only review subagent over the whole Phase 1 branch (`git diff main..HEAD` at the frozen branch commit) against `docs/specs/2026-11-02-test-execution-policy-design.md` and `docs/plans/2026-11-02-test-execution-policy.md`. Record `review: final round 1 — verdict: ...; findings: ...; reviewer: ...` on `sci-6af05a` and rulings in the plan ledger (`plan-review-ledger.md`), running up to 5 review-and-fix rounds until approved and rerunning `just check` and `just test-full` after any fix.

- [ ] **Step 3: Integrate Phase 1 to `main` and record the `policy: enabled` note**

From the main checkout, fast-forward `main` to `feat/sci-6af05a-test-policy` (if `git merge --ff-only` fails because another session committed to `main` between the review and integration, merge `main` into `feat/sci-6af05a-test-policy` via `git -C .worktrees/sci-6af05a merge --no-edit main`, rerun `just check` and `just test-full` in `.worktrees/sci-6af05a`, record the merge commit in the ledger, and then retry `git merge --ff-only`), record the exact `policy: enabled` lifecycle note on `sci-6af05a`, and fast-forward `feat/sci-6af05a-test-policy` in `.worktrees/sci-6af05a` to match `main`:
```bash
git merge --ff-only feat/sci-6af05a-test-policy
SHA=$(git rev-parse HEAD)
STAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
tasks note sci-6af05a "policy: enabled at $STAMP revision $SHA"
git -C .worktrees/sci-6af05a merge --ff-only main
```
Expected: `main` and `feat/sci-6af05a-test-policy` match, `just check` passes, and `sci-6af05a` carries `policy: enabled at <RFC3339-UTC> revision <full-sha>`.

---

### Task 6: Publication Packet and Hosted CI Verification

**Files:**
- Modify: `tasks/sci-6af05a.md` (via `tasks note`, `tasks attach`, `tasks park`)

**Interfaces:**
- Consumes: Phase 1 integrated on `main` from Task 5
- Produces: user-approved push of `main` (and any ahead sibling `main` branches) to `origin`, verified GitHub Actions `CI` run, and attached `ci-module-inventory.txt` and `ci-junit-summary.md` on `sci-6af05a`.

- [ ] **Step 1: Prepare the Publication Packet and park for user push approval**

Check `gh auth status`, repository visibility, and `HEAD...origin/main` across `science`, `beliefs`, `atoms`, and `nodes`:
```bash
gh auth status
for repo in . ../beliefs ../atoms ../nodes; do
  git -C "$repo" rev-parse HEAD origin/main
  git -C "$repo" rev-list --left-right --count HEAD...origin/main
  git -C "$repo" diff --stat origin/main..HEAD -- python/
done
```
Record the Publication Packet note on `sci-6af05a`, park `sci-6af05a` (`--waiting-on user --reason approval`), and ask the user for approval to push `main` in `science` (and any ahead sibling `main` branches in `beliefs`, `atoms`, `nodes`) to `origin`.

- [ ] **Step 2: Push approved refs, watch the hosted `CI` run, verify coverage, and attach evidence to `sci-6af05a`**

After user push approval:
```bash
# Push approved sibling main branches if any, then push science main:
git push origin main
GH_TOKEN=$(gh auth token --user khughitt) gh run list --repo verifiably/science --branch main --limit 1
GH_TOKEN=$(gh auth token --user khughitt) gh run watch <run-id> --repo verifiably/science --exit-status
GH_TOKEN=$(gh auth token --user khughitt) gh run download <run-id> --repo verifiably/science --dir /tmp/sci-6af05a-ci-artifacts
```
Verify `/tmp/sci-6af05a-ci-artifacts/python-3.11-coverage/{pytest.xml,module-inventory.txt}` and `python-3.13-coverage/{pytest.xml,module-inventory.txt}`:
- Confirm `failures == 0`, `errors == 0`, `executed >= pilot (532) + new tests added in test_uncertified_host.py and test_front_door.py`, and compare `skipped` against the local uncertified pilot (`663`), verifying every skip message matches `"certified tuple unavailable on this host:"` or `"confinement unavailable"`.
- Attach `module-inventory.txt` and a JUnit count summary to `sci-6af05a` before deleting `/tmp/sci-6af05a-ci-artifacts`:
  ```bash
  tasks attach sci-6af05a /tmp/sci-6af05a-ci-artifacts/python-3.13-coverage/module-inventory.txt --name ci-module-inventory.txt --caption "Hosted CI module-inventory.txt from initial verification run"
  # Format and attach ci-junit-summary.md with run ID, URL, and 3.11/3.13 executed/skipped/failed/error counts:
  tasks attach sci-6af05a /tmp/sci-6af05a-ci-artifacts/ci-junit-summary.md --name ci-junit-summary.md --caption "Hosted CI JUnit counts and skip comparison for Python 3.11 and 3.13"
  rm -rf /tmp/sci-6af05a-ci-artifacts
  ```

---

### Task 7: Activation Packet, `.tt.toml` + `ci_suite_refs` Activation, Post-Activation Verification, and Reporting

**Files:**
- Create: `.tt.toml`
- Modify: `justfile` (`ci_suite_refs := "refs/heads/*"`)
- Modify: `python/tests/test_front_door.py`
- Modify: `tasks/sci-6af05a.md`

**Interfaces:**
- Consumes: verified hosted `CI` run and attached `ci-module-inventory.txt` / `ci-junit-summary.md` from Task 6
- Produces: committed `.tt.toml` (`automatic_broad = false`, `broad_targets = ["test", "test-fast", "ci-python"]`), `ci_suite_refs := "refs/heads/*"` in `justfile`, live repository policy conformance tests in `python/tests/test_front_door.py`, post-activation verification evidence, `policy: disabled at <RFC3339-UTC> revision <full-sha>` note on `sci-6af05a`, removed `.worktrees/sci-6af05a`, and updates on `ops-39bff6`, `ops-8bfa85`, and `ops-56aab7`.

- [ ] **Step 1: Present the Activation Packet and park for user activation approval**

Record the Activation Packet note on `sci-6af05a`:
- Hosted run URL/ID/SHA, Python 3.11 and 3.13 executed and skipped counts vs the local pilot (referencing attached `ci-junit-summary.md`).
- Sibling SHAs and module inventory count (referencing attached `ci-module-inventory.txt`).
- Certified-host omission and `AGENTS.md` pre-merge verification rule.
- Proposed `.tt.toml` and `ci_suite_refs := "refs/heads/*"` diff and rollback route.
- Explicit push scope covered by the activation approval: (1) pushing `main` to `origin` (`verifiably/science`) with the activation commit (`.tt.toml`, `justfile`, `python/tests/test_front_door.py`) to verify covered push routing and trigger hosted `CI`, and (2) pushing `main` to `origin` (`verifiably/science`) with the final `sci-6af05a` lifecycle-note and task-closure commit.
Park `sci-6af05a` (`--waiting-on user --reason approval`) and request user approval.

- [ ] **Step 2: Add live repository policy assertions in `python/tests/test_front_door.py` (RED)**

After user activation approval, add to `python/tests/test_front_door.py`:
- `test_live_repository_policy_and_ci_suite_refs(front_door)`: uses `tt.read_policy(REPO)` in a clean subprocess to assert `{"automatic_broad": False, "broad_targets": ["test", "test-fast", "ci-python"]}`, and runs `just --justfile <REPO/justfile> --evaluate ci_suite_refs` and `ci_remote` to assert `"refs/heads/*"` and `"origin"`.

Run: `just test-one tests/test_front_door.py -k test_live_repository_policy_and_ci_suite_refs`
Expected: FAIL because `.tt.toml` does not exist yet and `ci_suite_refs` is `""`.

- [ ] **Step 3: Create `.tt.toml` and widen `ci_suite_refs` in `justfile` (GREEN)**

Create `.tt.toml`:
```toml
automatic_broad = false
broad_targets = ["test", "test-fast", "ci-python"]
```
In `justfile`, update:
```just
ci_suite_refs := "refs/heads/*"
```

Run:
```bash
just test-one tests/test_front_door.py
just check
```
Expected: all tests in `test_front_door.py` pass; `just check` exits 0.

- [ ] **Step 4: Commit activation, run scoped review, and integrate to `main`**

In `.worktrees/sci-6af05a`:
```bash
git rev-list --left-right --count main...HEAD
# Merge main if it moved:
git merge --no-edit main
git add .tt.toml justfile python/tests/test_front_door.py
git commit -m "build(policy): disable automatic local broad suites after CI verification (sci-6af05a)"
```
Dispatch a scoped read-only review subagent over the activation commit diff (`git show HEAD`) against the Activation Packet and Spec §4 / §7.3, record `review: activation round 1 — verdict: ...` on `sci-6af05a`, then fast-forward `main` to `feat/sci-6af05a-test-policy`.

- [ ] **Step 5: Verify the four post-activation behaviors, record `policy: disabled`, and push to `origin`**

Verify and record on `sci-6af05a`:
1. **Focused execution runs under policy-off**: run `just test-one tests/test_front_door.py` and confirm the recorded timing row has `target == "test-one"`, `execution == "ran"`, `execution_reason == "default"`, `exit == 0`.
2. **Automatic broad target records a skip**: run `just test` and confirm the recorded timing row has `target == "test"`, `execution == "skipped"`, `execution_reason == "policy-disabled"`, `exit is None`.
3. **Forced failure on a broad target propagates nonzero exit and records failure**:
   - Create an untracked failing test file `.worktrees/sci-6af05a/python/tests/test_forced_failure_probe.py` containing `def test_forced_failure_probe(): assert False`.
   - Run `TT_FORCE=1 just test-fast` in `.worktrees/sci-6af05a` and verify a nonzero exit code and that the recorded `test-fast` row has `execution == "ran"`, `execution_reason == "forced"`, and `exit != 0`.
   - Remove `.worktrees/sci-6af05a/python/tests/test_forced_failure_probe.py` and verify `git -C .worktrees/sci-6af05a status --short` is empty.
4. **Record `policy: disabled` and verify covered remote push**:
   - Record `policy: disabled at <RFC3339-UTC> revision <full-sha>` on `sci-6af05a` using the activation commit SHA on `main`.
   - Push `main` to `origin` (`git push origin main`), confirm `.githooks/pre-push` selects `hook-pre-push-fast` (running `hook-pre-push-fast` hygiene and skipping `test-fast`), and watch the triggered hosted `CI` run on GitHub Actions to completion (`gh run watch --exit-status`).

- [ ] **Step 6: Run `tt-report`, attach plan ledger, remove `.worktrees/sci-6af05a`, update `ops` tasks, and close `sci-6af05a`**

1. Run `tt-report --project sci --since 2026-11-02 --all` and record the timing summary in the done note on `sci-6af05a`.
2. Update `tasks/files/sci-6af05a/plan-review-ledger.md` in place with all plan, final, and activation review rulings and any deferred minors, attach `.superpowers/sdd/2026-11-02-test-execution-policy/progress.md` via `tasks attach sci-6af05a .superpowers/sdd/2026-11-02-test-execution-policy/progress.md --name sdd-progress-ledger.md --caption "SDD execution ledger for sci-6af05a"`, and verify `tasks show sci-6af05a` lists all attachments (`spec-round-1-builder-report.md`, `spec-round-2-builder-report.md`, `spec-review-ledger.md`, `ci-module-inventory.txt`, `ci-junit-summary.md`, `plan-review-ledger.md`, `sdd-progress-ledger.md`).
3. Inspect `git -C .worktrees/sci-6af05a status --ignored --porcelain` and give each entry an explicit disposition in the task note (discard regenerable `python/.venv`, `python/.pytest_cache`, `python/.testmondata`).
4. Check `readlink -f ~/bin/* ~/.local/bin/*` to confirm no host pointer resolves into `.worktrees/sci-6af05a`, confirm `git -C .worktrees/sci-6af05a status --porcelain` prints nothing, then remove the worktree and branch:
   ```bash
   git worktree unlock .worktrees/sci-6af05a
   git worktree remove .worktrees/sci-6af05a
   git branch -d feat/sci-6af05a-test-policy
   ```
5. Record completion notes (with activation revision/timestamp, hosted CI run ID/counts, and certified-host rule) on `ops-39bff6`, `ops-8bfa85`, and `ops-56aab7` (`tasks -C ../ops note ...` and `tasks -C ../ops edit ops-56aab7 --ref ...`).
6. Close `sci-6af05a` (`tasks done sci-6af05a ...`), run `just check`, and push `main` to `origin`.
