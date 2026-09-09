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
    assert by_name["coord-note"].write_class.kind == "coordination"
    assert by_name["pub-view"].write_class.kind == "publishes"
    assert by_name["mint-claim"].write_class.routes == {"proposition": "corpus-write"}


def test_declaration_time_refusal_for_class_above_permit(certified_work):
    """A publishes-class command against an attended session without the publish
    family refuses before the handler runs (spec §6.1 step 3)."""
    from beliefs.session import open_attended_session
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.refusal import Refused
    from helpers.world import build_fixture_world
    decls = _fixture_tree()
    cfg = build_fixture_world(certified_work)
    session = open_attended_session(cfg.world, cfg.operations_root, profile=cfg.profile)
    d = Dispatcher(decls, {"pub-view": lambda ctx, writer: ()}, ReadContext.open(cfg),
                   session=session)
    try:
        with pytest.raises(Refused) as e:
            d.invoke("pub-view", {})
        assert e.value.refusal.code == "permit-exceeded"
    finally:
        session.close()
