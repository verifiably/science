# Contributor Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a concise, topic-first `docs/guide/` that introduces new contributors to the redesigned Science system while preserving precise routes to its authoritative designs.

**Architecture:** Eight hand-authored Markdown pages synthesize the fifteen pre-guide sources by topic. YAML front matter records freshness and source coverage; a small Python checker validates metadata, source paths, and relative link targets without generating documentation.

**Tech Stack:** Markdown, Python 3.11 standard library, existing PyYAML dependency, pytest

## Global Constraints

- The guide is explanatory; design documents, amendments, and frozen guarantee identifiers remain authoritative.
- The adoption ledger is the sole authority for implementation state.
- Every guide page uses `status: living`, `created: 2026-08-08`, `updated: 2026-08-08`, and a `sources` list.
- Prefer frozen identifiers such as G3, W8a, R12, M10, and P1 over section numbers.
- A banking, amendment, or implementation-state commit must update affected guide pages and `updated` dates in the same commit.
- Add no dependency and no generated synchronization mechanism.
- Add no ledger entry: the guide is explanatory documentation with no system artifact, adoption dependency, or implementation state of its own.
- Use inline Markdown links only; reference-style links are unsupported so every target remains visible to the checker.
- Keep repository-relative paths in docs and code.

## File Structure

| File | Responsibility |
|---|---|
| `python/tools/check_guide.py` | Validate guide front matter, source paths, and relative Markdown link targets. |
| `python/tests/test_check_guide.py` | Guard metadata and path failures, then keep the real guide under pytest. |
| `docs/guide/README.md` | Newcomer entry point, conceptual map, and reading paths; links to the ledger for status. |
| `docs/guide/foundations.md` | Epistemic invariant, kernel, boundaries, profiles, and record categories. |
| `docs/guide/claims-and-belief.md` | Claims, assessments, eligibility, belief, vocabulary, and corpus measurements. |
| `docs/guide/identity-world-and-change.md` | Identity, addressing, corpora, index, correction, and mutation integrity. |
| `docs/guide/computation-and-reproducibility.md` | Analysis specs, closures, runs, replay, equivalence, and verification. |
| `docs/guide/contracts-and-adoption.md` | Contracts, guarantees, conformance, review, cuts, and adoption order. |
| `docs/guide/open-questions.md` | Consolidated unresolved design questions, grouped by topic and linked to sources. |
| `docs/guide/glossary.md` | Canonical alphabetized term definitions. |
| `README.md` | Correct the cosmetic classification of the review-disposition document and link the guide. |

---

### Task 1: Guide checker

**Files:**

- Create: `python/tools/check_guide.py`
- Create: `python/tests/test_check_guide.py`

**Interfaces:**

- Produces: `check(root: Path) -> list[str]`, returning one readable error per violation.
- Produces: CLI `uv run python tools/check_guide.py [guide-dir]`, exiting `0` when valid and `1` when errors exist.

- [ ] **Step 1: Write the focused regression test**

```python
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "check_guide", Path(__file__).parents[1] / "tools" / "check_guide.py"
)
assert _SPEC is not None and _SPEC.loader is not None
checker = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = checker
_SPEC.loader.exec_module(checker)


def _page(body: str, sources: str = "  - ../source.md") -> str:
    return f"""---
title: Test
status: living
created: 2026-08-08
updated: 2026-08-08
sources:
{sources}
---
{body}
"""


def test_valid_metadata_and_relative_link_pass(tmp_path: Path) -> None:
    guide = tmp_path / "guide"
    guide.mkdir()
    (tmp_path / "source.md").write_text("# Source\n")
    (guide / "README.md").write_text(_page("[source](../source.md)"))
    assert checker.check(guide) == []


def test_missing_metadata_and_broken_link_are_reported(tmp_path: Path) -> None:
    guide = tmp_path / "guide"
    guide.mkdir()
    (guide / "README.md").write_text("# No metadata\n[missing](missing.md)\n")
    errors = checker.check(guide)
    assert any("YAML front matter" in error for error in errors)
    assert any("missing.md" in error for error in errors)


@pytest.mark.parametrize(
    ("frontmatter", "message"),
    [
        ("title: Test\nstatus: living\ncreated: 2026-08-08\nupdated: 2026-08-08\nsources: [", "malformed"),
        ("title: Test\nstatus: living\ncreated: 2026-08-08\nupdated: 2026-08-08", "missing metadata: sources"),
        (
            "title: Test\nstatus: living\ncreated: 2026-08-08\nupdated: 2026-08-08\nsources: no",
            "sources must be a non-empty list",
        ),
        (
            "title: Test\nstatus: living\ncreated: 2026-08-08\nupdated: 2026-08-08\nsources: []",
            "sources must be a non-empty list",
        ),
    ],
)
def test_metadata_failures_are_specific(tmp_path: Path, frontmatter: str, message: str) -> None:
    guide = tmp_path / "guide"
    guide.mkdir()
    (guide / "README.md").write_text(f"---\n{frontmatter}\n---\n")
    assert any(message in error for error in checker.check(guide))


def test_sources_resolve_and_local_links_are_relative_and_inline(tmp_path: Path) -> None:
    guide = tmp_path / "guide"
    guide.mkdir()
    (guide / "README.md").write_text(
        _page("[absolute](/tmp/source.md)\n[reference][source]", "  - ../missing.md")
    )
    errors = checker.check(guide)
    assert any("missing source" in error for error in errors)
    assert any("absolute link" in error for error in errors)
    assert any("reference-style links are unsupported" in error for error in errors)
```

- [ ] **Step 2: Run the test and verify the tool is absent**

Run: `cd python && uv run pytest tests/test_check_guide.py -q`

Expected: collection fails with `FileNotFoundError` because `tools/check_guide.py` does not exist.

- [ ] **Step 3: Implement the minimal checker**

```python
"""Validate contributor-guide metadata and local Markdown links."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

REQUIRED = frozenset({"title", "status", "created", "updated", "sources"})
LINK = re.compile(r"(?<!!)\[[^]]+]\(([^)]+)\)")
REFERENCE_LINK = re.compile(r"(?<!!)\[[^]]+]\[[^]]*]")
DEFAULT_GUIDE = Path(__file__).resolve().parents[2] / "docs" / "guide"


def check(root: Path) -> list[str]:
    if not root.is_dir():
        return [f"{root}: not a directory"]
    errors: list[str] = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        body = text
        metadata = None
        if not text.startswith("---\n"):
            errors.append(f"{path}: missing YAML front matter")
        else:
            parts = text.split("---", 2)
            if len(parts) != 3:
                errors.append(f"{path}: unterminated YAML front matter")
            else:
                body = parts[2]
                try:
                    metadata = yaml.safe_load(parts[1])
                except yaml.YAMLError as exc:
                    errors.append(f"{path}: malformed YAML front matter: {exc}")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{path}: YAML front matter is not a mapping")
        elif isinstance(metadata, dict):
            missing = sorted(REQUIRED - metadata.keys())
            if missing:
                errors.append(f"{path}: missing metadata: {', '.join(missing)}")
            if "sources" in metadata:
                sources = metadata["sources"]
                if not isinstance(sources, list) or not sources:
                    errors.append(f"{path}: sources must be a non-empty list")
                else:
                    for source in sources:
                        if not isinstance(source, str) or not source or source.startswith("/"):
                            errors.append(f"{path}: source must be a relative path: {source!r}")
                        elif not (path.parent / source).exists():
                            errors.append(f"{path}: missing source: {source}")
        for raw in LINK.findall(body):
            target = raw.split()[0].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            if parsed.path.startswith("/"):
                errors.append(f"{path}: absolute link is not allowed: {target}")
            elif not (path.parent / unquote(parsed.path)).exists():
                errors.append(f"{path}: missing link target: {target}")
        if REFERENCE_LINK.search(body):
            errors.append(f"{path}: reference-style links are unsupported")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    errors = check(Path(args[0]) if args else DEFAULT_GUIDE)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the focused test**

Run: `cd python && uv run pytest tests/test_check_guide.py -q`

Expected: all focused checker tests pass.

- [ ] **Step 5: Run style checks**

Run: `cd python && uv run ruff check tools/check_guide.py tests/test_check_guide.py`

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add python/tools/check_guide.py python/tests/test_check_guide.py
git commit -m "feat: add contributor guide checks"
```

### Task 2: Entry point and foundations

**Files:**

- Create: `docs/guide/README.md`
- Create: `docs/guide/foundations.md`

**Source mapping:**

- `README.md`: contributor-guide design and adoption ledger.
- `foundations.md`: epistemic kernel, substrate consolidation, domain extension boundary, and formal model.

- [ ] **Step 1: Write `docs/guide/README.md`**

Include YAML metadata, the non-authoritative rule, a six-node conceptual map, the newcomer path through the five topic pages, direct-reference links to the glossary and open questions, and a status link to adoption-ledger §3. Do not copy an implementation tally into the page. Add a maintenance note requiring source banking, amendment, and implementation-state commits to update affected guide pages and `updated` dates in the same commit; require inline Markdown links so the checker can inspect every target.

- [ ] **Step 2: Write `docs/guide/foundations.md`**

Lead with G1's invariant. Summarize held artifacts, records versus computed views, the ten kernel kinds, the `nodes`/`science`/`domains`/`practices`/`atoms` ownership split, profile compilation, and the clean-start rule. Preserve the distinction between mechanism and policy.

- [ ] **Step 3: Check the partial guide diff**

Run: `git diff --check`

Expected: no whitespace errors. The whole-guide checker is deliberately deferred until every linked page exists in Task 5.

- [ ] **Step 4: Commit**

```bash
git add docs/guide/README.md docs/guide/foundations.md
git commit -m "docs: introduce the science guide"
```

### Task 3: Claims and belief

**Files:**

- Create: `docs/guide/claims-and-belief.md`

**Source mapping:** Epistemic kernel, formal model and claim calculus, domain extension boundary, belief policy, corpus survey, multi-corpus typing exercise, and review disposition.

- [ ] **Step 1: Write the topic page**

Explain the typed claim structure (`Operator`, arguments, sorts, layer, polarity, qualifiers), canonical projection, why prose leaves identity, assessment eligibility, independence, and policy-bound belief values. State the three belief-query outcomes and distinguish `NoEligibleAssessment` from `Unavailable`.

- [ ] **Step 2: Report measurements within their bounds**

State that the survey covered eight predecessor corpora and 6,860 records. Separate the typing configurations: the fitted unsorted plan typed 307 of 307 structured mm30 propositions; the modal-sorted plan typed 282 of 307 and refused 25 with `ArgumentSortMismatch`. State that the modal sorting rule was computed rather than independently chosen, a different rule can change the 25, and the 25 survives the fitting objection without becoming independent validation. Also report that the two other typed corpora recorded no claims, no surveyed corpus exercised qualifiers, and `mechanistic_narrative` was not admitted.

- [ ] **Step 3: Check the partial guide diff and commit**

Run: `git diff --check`

Expected: no whitespace errors. The whole-guide checker remains deferred until Task 5.

```bash
git add docs/guide/claims-and-belief.md
git commit -m "docs: summarize claims and belief"
```

### Task 4: Identity, history, and computation

**Files:**

- Create: `docs/guide/identity-world-and-change.md`
- Create: `docs/guide/computation-and-reproducibility.md`

**Source mapping:**

- `identity-world-and-change.md`: substrate consolidation, world addressing, correction lifecycle, world-index packaging, tamper-evident log, and formal model.
- `computation-and-reproducibility.md`: epistemic kernel, world addressing, computation and reproducibility, normative contract, and tamper-evident log.

- [ ] **Step 1: Write identity, world, and change**

Explain content identity versus world address, aliases, corpus identity, the world index and bounded freshness, immutable retractions that subtract standing, supersession versus retraction, append-only epoch chains, anchors, pre-mutation registration, and the precise ceiling of detectable removal. Preserve occurrence-versus-authorization and content-equality-versus-chronology distinctions.

- [ ] **Step 2: Write computation and reproducibility**

Explain the analysis spec as preregistration, complete run closure, assessment and dataset-production run shapes, captured code/environment/input identities, imported workflow DAGs, replay eligibility, equivalence rules, derived verification scope, and verification as an artifact rather than mutable state. Preserve replay-eligibility-versus-epistemic-verdict and definition-versus-invocation distinctions.

- [ ] **Step 3: Check the partial guide diff and commit**

Run: `git diff --check`

Expected: no whitespace errors. The whole-guide checker remains deferred until Task 5.

```bash
git add docs/guide/identity-world-and-change.md docs/guide/computation-and-reproducibility.md
git commit -m "docs: summarize identity and reproducibility"
```

### Task 5: Contracts, questions, glossary, and navigation

**Files:**

- Create: `docs/guide/contracts-and-adoption.md`
- Create: `docs/guide/open-questions.md`
- Create: `docs/guide/glossary.md`
- Modify: `python/tests/test_check_guide.py`
- Modify: `README.md`

**Source mapping:**

- `contracts-and-adoption.md`: normative contract, adoption ledger, review disposition, corpus survey, and multi-corpus typing exercise.
- `open-questions.md`: every source carrying an unresolved question, with exact source links and no duplication of closed rulings.
- `glossary.md`: all fifteen pre-guide sources, with one definition per term.

- [ ] **Step 1: Write contracts and adoption**

Explain versioned normative contracts, frozen guarantee identifiers, conformance oracles, mutation testing under N2, instrument certification, the purpose and stop edge of conformance cut 1, and the adoption dependency order. Link to the living ledger and disposition record for current detail instead of copying changing counts.

- [ ] **Step 2: Consolidate open questions**

Group unresolved questions under foundations, claims and belief, identity and history, reproducibility, and contracts/adoption. For each question give one sentence, its source link, and what decision or artifact it depends on. Exclude limitations, deferred work with a settled design, and questions explicitly closed by later amendments.

- [ ] **Step 3: Build the glossary**

Alphabetize short definitions for at least: address, alias, analysis spec, anchor, assessment, belief, belief policy, claim, closure, contract, corpus, epoch, guarantee, held, independence, kernel, operator, profile, qualifier, replay eligibility, retraction, run, standing, supersession, verification, view, vocabulary, and world index. Link each term to its primary topic page and authoritative source.

- [ ] **Step 4: Finish navigation and correct README framing**

Add cross-links among every guide page. Add a root README link to `docs/guide/README.md`. Replace the sentence classifying all non-ledger documents as redesigns/measurements with wording that explicitly includes the review-disposition record.

- [ ] **Step 5: Put the real guide under pytest**

Add the import alongside the file's existing imports and the test at the end of
`python/tests/test_check_guide.py`:

```python
from conftest import REPO_ROOT


def test_repository_guide_is_valid() -> None:
    assert checker.check(REPO_ROOT / "docs" / "guide") == []
```

Run: `cd python && uv run pytest tests/test_check_guide.py -q`

Expected: all checker tests, including the real repository guide, pass.

- [ ] **Step 6: Check and commit**

Run: `cd python && uv run python tools/check_guide.py`

Expected: no output and exit `0`.

```bash
git add README.md docs/guide python/tests/test_check_guide.py
git commit -m "docs: complete the contributor guide"
```

### Task 6: Coverage and final verification

**Files:**

- Modify only guide pages with discovered coverage or consistency gaps.

- [ ] **Step 1: Verify all fifteen pre-guide sources are cited**

Compare `docs/designs/*.md` excluding the contributor-guide design against guide `sources` metadata and reference lists. Confirm each source appears at least once and that the mutation-log and typing-exercise ownership called out in review is explicit.

- [ ] **Step 2: Verify editorial consistency**

Search for unresolved placeholders, duplicate glossary headings, implementation claims not sourced to the ledger, stale superseded wording, and section-number references where a frozen guarantee identifier exists.

- [ ] **Step 3: Run the guide checker and focused regression**

Run: `cd python && uv run pytest tests/test_check_guide.py -q`

Expected: all checker tests pass.

Run: `cd python && uv run python tools/check_guide.py`

Expected: no output and exit `0`.

- [ ] **Step 4: Run repository verification**

Run: `cd python && uv run ruff check .`

Expected: no errors.

Run: `cd python && uv run pytest -q`

Expected: all Python tests pass.

Run: `npm test`

Working directory: `ts/`

Expected: all TypeScript tests pass.

- [ ] **Step 5: Commit any final corrections**

If Step 1 or Step 2 required edits:

```bash
git add docs/guide README.md
git commit -m "docs: verify contributor guide coverage"
```
