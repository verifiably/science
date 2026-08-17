# Python Test Pyright Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `uv run --frozen pyright tests` pass without changing tested behavior.

**Architecture:** Keep narrowing at the test sites that know which union arm is expected. Give the shared belief scenario helper one precise `TypedDict` return type so its broad override seam does not erase every field type, and use targeted Pyright ignores only where a test deliberately violates a static contract to exercise runtime validation.

**Tech Stack:** Python 3.11+, Pyright basic mode, pytest, Ruff, uv.

## Global Constraints

- Composition > Inheritance; explicit > defensive; fail early.
- No compatibility layers, new dependencies, or production-code changes.
- Preserve runtime assertions and existing negative-test coverage.
- Verify from `python/` with frozen dependencies.

---

### Task 1: Fix the shared belief scenario typing root cause

**Files:**
- Modify: `python/tests/test_belief.py`
- Test: `python/tests/test_belief.py`

**Interfaces:**
- Consumes: `evaluate` keyword parameters and the existing `scenario(**overrides)` test seam.
- Produces: a `_Scenario` `TypedDict` whose fields match `evaluate`, while retaining `object` overrides for intentional invalid-input tests.

- [x] **Step 1: Confirm the failing check**

Run: `uv run --frozen pyright tests/test_belief.py`
Expected: failures rooted in `dict[str, object]`, plus genuine union and optional-address errors.

- [x] **Step 2: Type the helper and narrow genuine unions**

Add a private `_Scenario(TypedDict)` matching the six evaluator inputs, return it through one explicit `cast`, derive dataset addresses through a helper returning `str`, and add `isinstance` assertions immediately before arm-specific attribute access.

- [x] **Step 3: Verify the file**

Run: `uv run --frozen pyright tests/test_belief.py`
Expected: 0 errors.

### Task 2: Narrow expected union arms at their test sites

**Files:**
- Modify: `python/tests/test_admission.py`
- Modify: `python/tests/test_assess.py`
- Modify: `python/tests/test_boundary.py`
- Modify: `python/tests/test_dataset_state.py`
- Modify: `python/tests/test_inertness.py`
- Modify: `python/tests/test_replay.py`
- Modify: `python/tests/test_verify.py`

**Interfaces:**
- Consumes: existing result unions such as `Admitted | AdmissionRefused`, `RunMinted | RunRefused`, `AssessmentValue | AssessmentFinding`, and verification/dataset-state unions.
- Produces: explicit runtime assertions documenting the arm each test requires.

- [x] **Step 1: Add the smallest assertion before each arm-specific use**

Use existing concrete classes already imported by each file. Where `dataset_address` returns `str | None`, assert non-`None` before constructing keyed observation mappings.

- [x] **Step 2: Run focused checks**

Run: `uv run --frozen pyright tests/test_admission.py tests/test_assess.py tests/test_boundary.py tests/test_dataset_state.py tests/test_inertness.py tests/test_replay.py tests/test_verify.py`
Expected: only deliberate-invalid-input diagnostics remain.

### Task 3: Mark deliberate static-contract violations

**Files:**
- Modify: `python/tests/test_closure.py`
- Modify: `python/tests/test_recipe.py`
- Modify: `python/tests/test_replay.py`
- Modify: `python/tests/test_spec.py`

**Interfaces:**
- Consumes: negative tests that intentionally subclass a final class, mutate frozen values, omit required arguments, or pass malformed field types.
- Produces: line-local `type: ignore[...]` comments using the repository's existing negative-test convention.

- [x] **Step 1: Annotate only the intentional violation lines**

Use `misc`, `arg-type`, or `call-arg` codes matching the diagnostic; do not disable rules at file or project scope.

- [x] **Step 2: Run the complete static check**

Run: `uv run --frozen pyright tests`
Expected: 0 errors, 0 warnings.

### Task 4: Verify behavior and formatting

**Files:**
- Test: all modified Python test files.

**Interfaces:**
- Consumes: Tasks 1-3.
- Produces: a clean branch suitable for review.

- [x] **Step 1: Run focused behavioral tests**

Run: `uv run --frozen pytest tests/test_admission.py tests/test_assess.py tests/test_belief.py tests/test_boundary.py tests/test_closure.py tests/test_dataset_state.py tests/test_inertness.py tests/test_recipe.py tests/test_replay.py tests/test_spec.py tests/test_verify.py -q`
Expected: all pass.

- [x] **Step 2: Run repository gates**

Run: `uv run --frozen ruff check .`
Expected: clean.

Run: `uv run --frozen ruff format --check`
Expected: clean.

Run: `uv run --frozen pyright tests`
Expected: 0 errors, 0 warnings.

Run: `uv run --frozen pytest -q`
Expected: all pass; existing temporary-directory cleanup warnings may remain.

- [x] **Step 3: Review the diff and commit**

Run: `git diff --check && git diff --stat && git status --short`

Commit message: `test: resolve pyright warnings in python tests`
