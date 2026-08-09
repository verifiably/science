from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from conftest import REPO_ROOT

_SPEC = importlib.util.spec_from_file_location("check_guide", Path(__file__).parents[1] / "tools" / "check_guide.py")
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
    (tmp_path / "source.md").write_text("# Source\n", encoding="utf-8")
    (guide / "README.md").write_text(_page("[source](../source.md)"), encoding="utf-8")
    assert checker.check(guide) == []


def test_missing_metadata_and_broken_link_are_reported(tmp_path: Path) -> None:
    guide = tmp_path / "guide"
    guide.mkdir()
    (guide / "README.md").write_text("# No metadata\n[missing](missing.md)\n", encoding="utf-8")
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
    (guide / "README.md").write_text(f"---\n{frontmatter}\n---\n", encoding="utf-8")
    assert any(message in error for error in checker.check(guide))


def test_sources_resolve_and_local_links_are_relative_and_inline(tmp_path: Path) -> None:
    guide = tmp_path / "guide"
    guide.mkdir()
    (guide / "README.md").write_text(
        _page("[absolute](/tmp/source.md)\n[reference][source]", "  - ../missing.md"),
        encoding="utf-8",
    )
    errors = checker.check(guide)
    assert any("missing source" in error for error in errors)
    assert any("absolute link" in error for error in errors)
    assert any("reference-style links are unsupported" in error for error in errors)


def test_repository_guide_is_valid() -> None:
    assert checker.check(REPO_ROOT / "docs" / "guide") == []
