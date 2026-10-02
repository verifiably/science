import pytest

from science.schema import load_command_tree

KIND_ACTS = {"proposition": frozenset({"corpus-write"})}


def _fixture_tree():
    from pathlib import Path
    root = Path(__file__).parent / "fixtures" / "commands"
    return load_command_tree(root, kind_acts=KIND_ACTS,
                             contract_kinds=frozenset(KIND_ACTS))


def test_synthetic_tree_loads():
    by_name = {d.name: d for d in _fixture_tree()}
    assert by_name["pub-view"].write_class.kind == "publishes"
    assert by_name["mint-claim"].write_class.routes == {"proposition": "corpus-write"}


def test_a_publishes_class_command_reaches_its_handler_under_an_attended_session(certified_work):
    """An attended session's ceiling is the full permit, which covers the
    publication requirement, so the handler runs (sci-498acb)."""
    from science.session import open_session
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from helpers.world import build_fixture_world
    decls = _fixture_tree()
    cfg = build_fixture_world(certified_work)
    session = open_session(cfg)
    executed = []
    d = Dispatcher(decls, {"pub-view": lambda ctx, writer: executed.append(True) or ()},
                   ReadContext.open(cfg), session=session)
    try:
        d.invoke("pub-view", {})
    finally:
        session.close()
    assert executed == [True]
