import sys
import types
from pathlib import Path

import pytest

from science.commands.status import handle
from science.config import ReadContext
from science.cursor import MIN_OUTPUT_BUDGET
from science.loader import production_tree, resolve_handlers
from science.report import Heading, KeyVals
from science.refusal import Refused
from science.schema import Declaration, DeclarationError, InputSpec, WriteClass
from helpers.world import add_one_more_record, build_fixture_world


def test_status_renders_registry_epoch_and_counts(certified_work):
    cfg = build_fixture_world(certified_work)
    report = handle(ReadContext.open(cfg))
    text = "".join(str(block) for block in report)

    assert isinstance(report[0], Heading)
    assert "no current epoch" in text.lower()
    assert any(
        "proposition" in str(block)
        for block in report
        if isinstance(block, KeyVals)
    ), "expected per-corpus counts by kind"
    assert "live=True" in text


def test_status_renders_corpus_findings(certified_work, tmp_path):
    """`CorpusStatus.findings` reaches the report. The registry reduction emits
    exactly one finding today, `duplicate-carrier`, when two configured roots
    carry the same corpus id — a copied root is that state."""
    import shutil

    from beliefs.world import WorldConfig

    from science.config import ScienceConfig
    from science.report import Finding

    cfg = build_fixture_world(certified_work)
    (root,) = cfg.world.corpus_roots
    twin = tmp_path / "twin"
    shutil.copytree(root, twin)
    doubled = ScienceConfig(
        world=WorldConfig(cfg.world.world_root, cfg.world.world_id, (root, twin)),
        operations_root=cfg.operations_root,
        profile=cfg.profile,
        service_socket=cfg.service_socket,
        store_root=cfg.store_root,
        coordination=cfg.coordination,
    )

    report = handle(ReadContext.open(doubled))

    findings = [block for block in report if isinstance(block, Finding)]
    assert len(findings) == 1
    assert findings[0].text.startswith("error duplicate-carrier ")
    assert "multiple configured roots carry this corpus id" in findings[0].text
    assert str(twin) in findings[0].text  # the detail names the carriers
    corpora = next(block for block in report if isinstance(block, KeyVals))
    assert "present=False" in corpora.pairs[0][1]
    # The finding follows the corpora block it is about, before the epoch.
    assert report.index(findings[0]) == report.index(corpora) + 1
    # A clean world renders no finding block at all.
    assert not any(isinstance(block, Finding) for block in handle(ReadContext.open(cfg)))


def test_status_mutation_is_caught(certified_work):
    cfg = build_fixture_world(certified_work)
    before = handle(ReadContext.open(cfg))

    add_one_more_record(cfg)

    assert handle(ReadContext.open(cfg)) != before


def test_read_context_opens_views_and_loads_the_named_record(certified_work):
    context = ReadContext.open(build_fixture_world(certified_work))

    ((corpus_id, read_view),) = context.read_views()
    node = next(read_view.iter_stored())

    assert corpus_id
    assert context.load_record(node.uid, node.id) == node
    with pytest.raises(Refused) as caught:
        context.load_record("wrong-uid", node.id)
    assert caught.value.refusal.code == "unknown-cursor"


def test_production_tree_ships_status_with_a_bound_handler():
    decls = production_tree()

    assert "status" in [declaration.name for declaration in decls]
    handlers = resolve_handlers(decls)
    assert all(callable(handlers[declaration.name]) for declaration in decls)


def test_production_kind_acts_is_the_kernel_table_exactly():
    """No fallback and no local copy: the routes come from beliefs or nowhere."""
    from beliefs.permit import KIND_ACTS

    from science.loader import production_kind_acts

    assert production_kind_acts() == dict(KIND_ACTS)
    assert production_kind_acts()["proposition"] == frozenset({"corpus-write"})


@pytest.mark.parametrize(
    "write_class",
    [
        WriteClass("coordination"),
        WriteClass("mints", ("note",), {"note": "corpus-write"}),
        WriteClass("publishes"),
    ],
)
def test_production_tree_admits_write_classes_now_that_capabilities_landed(
    monkeypatch, write_class
):
    import science.loader as loader

    declaration = Declaration(
        "future-write", "p", write_class, MIN_OUTPUT_BUDGET, (), (), Path(".")
    )
    monkeypatch.setattr(loader, "load_command_tree", lambda *args, **kwargs: (declaration,))

    assert loader.production_tree() == (declaration,)


def _star_args(ctx, *args):
    return ()


def _star_kwargs(ctx, **kwargs):
    return ()


def _positional_only(ctx, corpus, /):
    return ()


def _wrong_lead(world):
    return ()


def _positional_input(ctx, corpus=None):
    return ()


def _missing_writer(ctx, *, corpus=None):
    return ()


def _stray_writer(ctx, writer, *, corpus=None):
    return ()


def _required_with_default(ctx, *, corpus=None):
    return ()


def _optional_without_default(ctx, *, corpus):
    return ()


def _good(ctx, *, corpus=None):
    return ()


def _good_required(ctx, *, corpus):
    return ()


def _declaration(name, handle, write_class, inputs):
    module = types.ModuleType(f"science.commands.{name}")
    module.handle = handle
    return module, Declaration(
        name,
        "p",
        write_class,
        MIN_OUTPUT_BUDGET,
        inputs,
        (),
        Path("."),
    )


def _bind_and_resolve(monkeypatch, name, handle, write_class, inputs):
    module, declaration = _declaration(name, handle, write_class, inputs)
    monkeypatch.setitem(sys.modules, module.__name__, module)
    return resolve_handlers((declaration,))


@pytest.mark.parametrize(
    "bad_handle",
    [
        _star_args,
        _star_kwargs,
        _positional_only,
        _wrong_lead,
        _positional_input,
        _stray_writer,
    ],
)
def test_each_bad_read_handler_shape_refused_in_isolation(monkeypatch, bad_handle):
    inputs = (
        ()
        if bad_handle is _wrong_lead
        else (InputSpec("corpus", "string", False, "d"),)
    )

    with pytest.raises(DeclarationError):
        _bind_and_resolve(
            monkeypatch,
            "shapecase",
            bad_handle,
            WriteClass("read-only"),
            inputs,
        )


@pytest.mark.parametrize(
    ("bad_handle", "required"),
    [(_required_with_default, True), (_optional_without_default, False)],
)
def test_handler_defaults_must_match_declaration(monkeypatch, bad_handle, required):
    inputs = (InputSpec("corpus", "string", required, "d"),)

    with pytest.raises(DeclarationError):
        _bind_and_resolve(
            monkeypatch,
            "defaultcase",
            bad_handle,
            WriteClass("read-only"),
            inputs,
        )


def test_write_handler_must_take_writer(monkeypatch):
    write_class = WriteClass(
        "mints", ("proposition",), {"proposition": "corpus-write"}
    )
    inputs = (InputSpec("corpus", "string", False, "d"),)

    with pytest.raises(DeclarationError):
        _bind_and_resolve(
            monkeypatch, "shapecase", _missing_writer, write_class, inputs
        )


@pytest.mark.parametrize(("good_handle", "required"), [(_good, False), (_good_required, True)])
def test_good_handler_shape_resolves(monkeypatch, good_handle, required):
    handlers = _bind_and_resolve(
        monkeypatch,
        "shapecase",
        good_handle,
        WriteClass("read-only"),
        (InputSpec("corpus", "string", required, "d"),),
    )

    assert callable(handlers["shapecase"])


def test_missing_handler_module_is_refused():
    declaration = Declaration(
        "missing-handler-module",
        "p",
        WriteClass("read-only"),
        MIN_OUTPUT_BUDGET,
        (),
        (),
        Path("."),
    )

    with pytest.raises(DeclarationError):
        resolve_handlers((declaration,))


def test_module_without_handle_is_refused(monkeypatch):
    module = types.ModuleType("science.commands.no_handle")
    monkeypatch.setitem(sys.modules, module.__name__, module)
    declaration = Declaration(
        "no-handle",
        "p",
        WriteClass("read-only"),
        MIN_OUTPUT_BUDGET,
        (),
        (),
        Path("."),
    )

    with pytest.raises(DeclarationError):
        resolve_handlers((declaration,))


def test_status_performs_exactly_its_declared_read_families(monkeypatch):
    from types import SimpleNamespace

    import science.commands.status as status_module

    used = set()

    class SpyWorld:
        def registry(self):
            used.add("registry")
            return SimpleNamespace(admissions=(), statuses=(), log_heads=())

        def status(self, corpus_id):
            raise AssertionError("no corpora in the spy world")

    def spy_current_epoch(world):
        used.add("epoch")
        from beliefs.errors import EpochUnknown

        raise EpochUnknown("spy world has none")

    monkeypatch.setattr(status_module, "current_epoch", spy_current_epoch)
    spy_context = types.SimpleNamespace(
        world=SpyWorld(), read_views=lambda: used.add("corpus-stored") or ()
    )

    status_module.handle(spy_context)

    declared = set(
        next(
            declaration
            for declaration in production_tree()
            if declaration.name == "status"
        ).reads
    )
    assert used == declared
