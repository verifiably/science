# Front door for tests. Focused loop: `just test-one <pytest args>`.
# Inner loop: `just test-fast` (affected-only via pytest-testmon).
# Full suite: `just test` (forced override: `just test-full`).
# Gates: `just check` at pre-commit, `just gate` at pre-push.
# The git hooks in .githooks/ call `hook-pre-commit` and `hook-pre-push`, which run
# hygiene under their own target names and delegate broad suites so the report and
# `.tt.toml` policy can price and govern them separately.
# Design: ops docs/specs/2026-10-29-test-execution-policy-design.md.

set quiet
set positional-arguments

tt := "python3 tools/tt"

# The commands, each written once. Recipes and hooks all run these, so a hook can
# never drift from the gate it is supposed to be. Avoid single quotes inside them.
# The package lives under python/; `uv run` syncs the dev group (pytest, pytest-testmon,
# pytest-xdist). Each test builds its own certified world, and atoms certifies the volume
# on every open by spawning children, so tests wait on I/O and subprocesses rather than
# CPU: 8 workers with work-stealing took the suite from 626 s to 79 s on 2026-09-23,
# and 16 workers bought nothing more. The worker count is the host's budget: test runs go
# through `host-budget run` (ops), which sets PYTEST_XDIST_AUTO_NUM_WORKERS for `-n auto`
# (design: ops docs/specs/2026-09-24-host-budget-design.md). Worktree runs need no
# SCIENCE_TEST_ROOT: conftest resolves the certified test root through the main checkout.
xdist := "-n auto --dist worksteal"
fast_cmd := "cd python && uv run pytest --testmon " + xdist
test_cmd := "cd python && uv run pytest " + xdist
one_cmd := "cd python && uv run pytest"
# No formatter, linter, or typechecker is configured for this repository yet, so the
# seconds-long hygiene gate is the guide checks (ops-check, ops-docs) and the task-record check.
check_hygiene_cmd := "python3 tools/ops-check && python3 tools/ops-docs check && tasks check"

# Only passive docs and task records: python/tests/fixtures/*.md are command inputs.
docs_paths := "README.md AGENTS.md docs/*.md tasks/*.md"
docs_check_cmd := check_hygiene_cmd

# Activated to "refs/heads/*" in Phase 3 after hosted CI verification.
ci_suite_refs := ""
ci_remote := "origin"
ci_evidence_cmd := "case \"${SCIENCE_CI_EVIDENCE_DIR:?set SCIENCE_CI_EVIDENCE_DIR}\" in /*) ;; *) echo \"CI evidence path must be absolute\" >&2; exit 2;; esac"
ci_py_test_cmd := "cd python && uv run --frozen pytest --junitxml=\"$SCIENCE_CI_EVIDENCE_DIR/pytest.xml\" " + xdist

# One path, path::test, or -k expression, with each argument forwarded unchanged.
test-one +args:
    {{tt}} test-one -- host-budget run -- sh -c '{{one_cmd}} "$@" 2>&1' test-one "$@"

# Affected-only: the inner loop. An empty selection is a result, not a failure.
test-fast:
    {{tt}} test-fast -- host-budget run -- sh -c '{{fast_cmd}}'

# The full suite.
test:
    {{tt}} test -- host-budget run -- sh -c '{{test_cmd}}'

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

# Regenerate the identity and family regions in README.md and AGENTS.md from
# identity.toml and tools/family.toml. The only thing that edits those regions; `check`
# refuses a commit while they are out of date.
docs:
    {{tt}} docs -- python3 tools/ops-docs write

# What the pre-commit hook runs: `check-hygiene`'s command under its own hook target.
hook-pre-commit:
    {{tt}} hook-pre-commit -- sh -c '{{check_hygiene_cmd}}'

# Every staged path is a passive document or task record.
hook-pre-commit-docs:
    {{tt}} hook-pre-commit-docs -- sh -c '{{docs_check_cmd}}'

# What the pre-push hook runs: mandatory hygiene under the hook target, then the broad suite.
hook-pre-push:
    {{tt}} hook-pre-push -- sh -c '{{check_hygiene_cmd}}'
    just test

# Available for CI-covered pushes when ci_suite_refs is configured.
hook-pre-push-fast:
    {{tt}} hook-pre-push-fast -- sh -c '{{check_hygiene_cmd}}'
    just test-fast
