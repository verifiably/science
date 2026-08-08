# Contributor Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a concise, topic-first `docs/guide/` that introduces new contributors to the redesigned Science system while preserving precise routes to its authoritative designs.

**Architecture:** Eight hand-authored Markdown pages synthesize the fifteen pre-guide sources by topic. YAML front matter records freshness and source coverage; a small Python checker validates metadata and relative link targets without generating documentation.

**Tech Stack:** Markdown, Python 3.11 standard library, existing PyYAML dependency, pytest

## Global Constraints

- The guide is explanatory; design documents, amendments, and frozen guarantee identifiers remain authoritative.
- The adoption ledger is the sole authority for implementation state.
- Every guide page uses `status: living`, `created: 2026-08-08`, `updated: 2026-08-08`, and a `sources` list.
- Prefer frozen identifiers such as G3, W8a, R12, M10, and P1 over section numbers.
- A banking, amendment, or implementation-state commit must update affected guide pages and `updated` dates in the same commit.
- Add no dependency and no generated synchronization mechanism.
- Add no ledger entry: the guide is explanatory documentation with no system artifact, adoption dependency, or implementation state of its own.
- Keep repository-relative paths in docs and code.

## File Structure

| File | Responsibility |
|---|---|
| `python/tools/check_guide.py` | Validate guide front matter and relative Markdown link targets. |
| `python/tests/test_check_guide.py` | Guard valid pages plus malformed metadata and broken-link failures. |
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

_SPEC = importlib.util.spec_from_file_location(
    "check_guide", Path(__file__).parents[1] / "tools" / "check_guide.py"
)
assert _SPEC is not None and _SPEC.loader is not None
checker = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = checker
_SPEC.loader.exec_module(checker)


def _page(body: str) -> str:
    return f"""---
title: Test
status: living
created: 2026-08-08
updated: 2026-08-08
sources: []
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
```

- [ ] **Step 2: Run the test and verify the tool is absent**

Run: `cd python && uv run pytest tests/test_check_guide.py -q`

Expected: collection fails because `tools/check_guide.py` does not exist.

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
DEFAULT_GUIDE = Path(__file__).resolve().parents[2] / "docs" / "guide"


def check(root: Path) -> list[str]:
    if not root.is_dir():
        return [f"{root}: not a directory"]
    errors: list[str] = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        body = text
        if not text.startswith("---\n"):
            errors.append(f"{path}: missing YAML front matter")
        else:
            parts = text.split("---", 2)
            body = parts[2] if len(parts) == 3 else ""
            try:
                metadata = yaml.safe_load(parts[1]) if len(parts) == 3 else None
            except yaml.YAMLError as exc:
                errors.append(f"{path}: malformed YAML front matter: {exc}")
                metadata = None
            if not isinstance(metadata, dict):
                errors.append(f"{path}: YAML front matter is not a mapping")
            else:
                missing = sorted(REQUIRED - metadata.keys())
                if missing:
                    errors.append(f"{path}: missing metadata: {', '.join(missing)}")
                if not isinstance(metadata.get("sources"), list):
                    errors.append(f"{path}: sources must be a list")
        for raw in LINK.findall(body):
            target = raw.split()[0].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
                continue
            resolved = path.parent / unquote(parsed.path)
            if not resolved.exists():
                errors.append(f"{path}: missing link target: {target}")
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

Expected: `2 passed`.

- [ ] **Step 5: Run style checks**

Run: `cd python && uv run ruff check tools/check_guide.py tests/test_check_guide.py`

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add python/tools/check_guide.py python/tests/test_check_guide.py
git commit -m "test: add contributor guide checks"
```

### Task 2: Entry point and foundations

**Files:**

- Create: `docs/guide/README.md`
- Create: `docs/guide/foundations.md`

**Source mapping:**

- `README.md`: contributor-guide design and adoption ledger.
- `foundations.md`: epistemic kernel, substrate consolidation, domain extension boundary, and formal model.

- [ ] **Step 1: Write `docs/guide/README.md`**

Include YAML metadata, the non-authoritative rule, a six-node conceptual map, the newcomer path through the five topic pages, direct-reference links to the glossary and open questions, and a status link to adoption-ledger §3. Do not copy an implementation tally into the page.

- [ ] **Step 2: Write `docs/guide/foundations.md`**

Lead with G1's invariant. Summarize held artifacts, records versus computed views, the ten kernel kinds, the `nodes`/`science`/`domains`/`practices`/`atoms` ownership split, profile compilation, and the clean-start rule. Preserve the distinction between mechanism and policy.

- [ ] **Step 3: Check the two pages**

Run: `cd python && uv run python tools/check_guide.py`

Expected: no output and exit `0`.

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

State that the survey covered eight predecessor corpora and 6,860 records; the typing exercise typed 307 structured mm30 propositions, found 25 sort refusals under modal sorts, reached no claims in the two other typed corpora, and observed no qualifiers. Explain that fitted results are not independent validation and that `mechanistic_narrative` was not admitted.

- [ ] **Step 3: Check and commit**

Run: `cd python && uv run python tools/check_guide.py`

Expected: no output and exit `0`.

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

- [ ] **Step 3: Check and commit**

Run: `cd python && uv run python tools/check_guide.py`

Expected: no output and exit `0`.

```bash
git add docs/guide/identity-world-and-change.md docs/guide/computation-and-reproducibility.md
git commit -m "docs: summarize identity and reproducibility"
```

### Task 5: Contracts, questions, glossary, and navigation

**Files:**

- Create: `docs/guide/contracts-and-adoption.md`
- Create: `docs/guide/open-questions.md`
- Create: `docs/guide/glossary.md`
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

- [ ] **Step 5: Check and commit**

Run: `cd python && uv run python tools/check_guide.py`

Expected: no output and exit `0`.

```bash
git add README.md docs/guide
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

Expected: `2 passed`.

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
