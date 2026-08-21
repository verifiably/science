"""S8's static claim, and the `atoms`-import rule beside it.

**Two boundaries, two checks, neither standing in for the other.** S8 is about
who holds a **mutable corpus handle**: the write API is its only holder, every
other module receives a `ReadView`, and constructing or receiving a `Corpus`
outside `science.corpus` is a static violation. The `atoms`-import confinement
is about engine capability and is architecture, not an S8 arm — it is asserted
here because it belongs beside S8, not inside it.

**Why a static check and not a scan of writers.** "Discover the writers and
check them" is a roster wearing a predicate's clothes: a new writer reaching the
filesystem through an unrecognized primitive is simply not discovered, and the
scan reports clean. What is checkable is who holds the handle. What it does
**not** cover — a module writing bytes to a corpus path with a raw filesystem
call — is stated in §4.2.1 and pinned by the acceptance negative, not by this.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import science

PACKAGE = Path(science.__file__).resolve().parent
"""The package as **imported**, not as checked out.

The sabotage harness runs a check against a copy of the package on
`PYTHONPATH`; a static check that read the working tree instead would inspect
the unmutated source and score every sabotage as survived — which is vacuity
wearing the costume of a static assertion.
"""
WRITE_API = "corpus.py"
COMPOSITION_ROOT = "root.py"
WORLD_PACKAGE = "world"
"""The world layer, which now reaches the engine's chain and must not do so
directly. `World` receives one `(genesis_digest, tip)` callback; `root.py`
implements it with `atoms.read_chain`, and no `ChainView` — nor any other
engine type — crosses the package boundary."""


def modules() -> list[Path]:
    return sorted(path for path in PACKAGE.rglob("*.py"))


def world_modules() -> list[Path]:
    return sorted(path for path in (PACKAGE / WORLD_PACKAGE).rglob("*.py"))


def relative(path: Path) -> str:
    return path.relative_to(PACKAGE).as_posix()


def parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def names_of(tree: ast.Module) -> set[str]:
    """Every bare name and attribute tail the module mentions."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
    return found


def imported_modules(tree: ast.Module) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            found.add(node.module)
    return found


class TestS8TheMutableCorpusHandleHasOneHolder:
    @pytest.mark.parametrize("module", [path for path in modules() if relative(path) != WRITE_API], ids=relative)
    def test_no_module_outside_the_write_api_names_the_mutable_corpus(self, module):
        tree = parsed(module)
        assert not any(
            imported == "nodes.core.corpus" for imported in imported_modules(tree)
        ), f"{relative(module)} imports the mutable corpus"
        assert "Corpus" not in names_of(tree), f"{relative(module)} names Corpus"

    def test_the_write_api_is_the_one_module_that_does(self):
        tree = parsed(PACKAGE / WRITE_API)
        assert "nodes.core.corpus" in imported_modules(tree)
        assert "Corpus" in names_of(tree)

    def test_the_check_would_see_a_second_holder(self, tmp_path):
        # Otherwise the arm asserts that the tree happens to be quiet rather
        # than that the check can speak: a module that constructs one is what it
        # has to catch.
        offender = tmp_path / "writer.py"
        offender.write_text(
            "from nodes.core.corpus import Corpus\n\n\ndef build(root):\n    return Corpus(root)\n",
            encoding="utf-8",
        )
        tree = parsed(offender)
        assert "nodes.core.corpus" in imported_modules(tree)
        assert "Corpus" in names_of(tree)

    def test_a_read_view_is_what_every_other_module_receives(self):
        # The positive half: the facade is exported, and the handle is not.
        from science.corpus import ReadView

        assert not hasattr(ReadView, "add")
        assert not any(name.startswith(("add", "delete")) for name in vars(ReadView))


class TestTheCompositionRootIsTheOneAtomsImporter:
    @pytest.mark.parametrize(
        "module", [path for path in modules() if relative(path) != COMPOSITION_ROOT], ids=relative
    )
    def test_no_module_outside_the_composition_root_imports_atoms(self, module):
        offending = [
            imported
            for imported in imported_modules(parsed(module))
            if imported == "atoms" or imported.startswith("atoms.")
        ]
        assert offending == [], f"{relative(module)} imports {offending}"

    def test_the_composition_root_does_import_atoms(self):
        imported = imported_modules(parsed(PACKAGE / COMPOSITION_ROOT))
        assert any(name == "atoms" or name.startswith("atoms.") for name in imported)


class TestTheWorldPackageHoldsNoEngineCapability:
    """The same rule, stated over the package that most nearly needs to break it.

    The world layer is where recovery-completing chain reads enter Science: a
    build's anchors are chain digests, and preflight completes recovery before
    it inspects a single world file. It gets there through an injected
    `Callable[[Path], tuple[str, str]]` and never through `atoms`, so the two
    digests are the only engine-derived values that exist above the composition
    root. Asserting it here, over `science/world/` by name, means a future
    module in that package cannot pass by being one of many.
    """

    def test_the_world_package_is_not_empty(self):
        # Otherwise a rename to a package this test cannot find would score as
        # a clean sweep of nothing.
        assert len(world_modules()) >= 4

    @pytest.mark.parametrize("module", world_modules(), ids=relative)
    def test_no_world_module_imports_atoms(self, module):
        offending = [
            imported
            for imported in imported_modules(parsed(module))
            if imported == "atoms" or imported.startswith("atoms.")
        ]
        assert offending == [], f"{relative(module)} imports {offending}"

    @pytest.mark.parametrize("module", world_modules(), ids=relative)
    def test_no_world_module_names_an_engine_chain_view(self, module):
        assert "ChainView" not in names_of(parsed(module)), f"{relative(module)} names ChainView"
        assert "read_chain" not in names_of(parsed(module)), f"{relative(module)} names read_chain"

    def test_the_check_would_see_a_world_module_reading_the_chain(self, tmp_path):
        offender = tmp_path / "epoch.py"
        offender.write_text(
            "from atoms.coordinator.commands import read_chain\n\n\n"
            "def head(root, backend, storage) -> ChainView:\n"
            "    return read_chain(backend, str(root), str(root), storage)\n",
            encoding="utf-8",
        )
        tree = parsed(offender)
        assert any(name.startswith("atoms") for name in imported_modules(tree))
        assert {"ChainView", "read_chain"} <= names_of(tree)
