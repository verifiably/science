import pytest

from science.loader import production_tree
from science.refusal import Refused


def test_every_production_name_has_an_explicit_run_decision():
    from science.run_endpoint.policy import ORDINARY, CONFINED, REFUSED
    assert not (ORDINARY & CONFINED or ORDINARY & REFUSED or CONFINED & REFUSED)
    assert ORDINARY | CONFINED | REFUSED == {d.name for d in production_tree()} | {"heads", "log"}


@pytest.mark.parametrize("command,inputs", [
    ("publish", {}), ("publish-preview", {}), ("verify", {}), ("provider-inspect", {}),
    ("adopt", {}), ("unaudited", {}), ("heads", {"resolve": True}),
    ("fetch", {"source": "https://example.invalid/item"}),
    ("derive", {"workflow_environment": "a" * 64}),
    ("run", {"workflow_environment": "a" * 64}),
    ("verify", {"workflow_environment": "a" * 64}),
    ("derive", {"workflow_environment": ""}),
])
def test_restricted_routes_refuse_before_the_body(command, inputs):
    from science.run_endpoint.policy import admit
    with pytest.raises(Refused) as caught:
        admit(command, inputs)
    assert caught.value.refusal.code == "permit-exceeded"


@pytest.mark.parametrize("command,inputs,confined", [
    ("exposure-event", {"payload": "/scratch/payload.json"}, True),
    ("reservation-assignment", {"payload": "/scratch/payload.json"}, True),
    ("exposure-log", {"subject": "dataset:a"}, False),
    ("reservation-head", {"chain": "roster"}, False),
])
def test_exposure_and_reservation_commands_have_their_run_admission(command, inputs, confined):
    from science.run_endpoint.policy import CONFINED, ORDINARY, admit
    assert command in (CONFINED if confined else ORDINARY)
    admit(command, inputs)


@pytest.mark.parametrize("has_act", [False, True])
def test_sealed_run_keeps_the_real_invocation_outcome(certified_work, has_act):
    import json
    import threading
    from pathlib import Path
    from beliefs.permit import WritePermit
    from beliefs.session import open_run_session
    from beliefs.session.ledger import ledger_path
    from helpers.world import build_fixture_world, fixture_proposition_node
    from science.config import ReadContext
    from science.cursor import MIN_OUTPUT_BUDGET
    from science.dispatch import Dispatcher
    from science.run_endpoint.paths import Scratch
    from science.schema import Declaration, WriteClass

    cfg = build_fixture_world(certified_work)
    permit = WritePermit.from_json({"kinds": ["proposition"], "act_families": ["corpus-write"], "ungoverned": False})
    session = open_run_session(cfg.world, cfg.operations_root, write_root=cfg.write_root, profile=cfg.profile, ceiling=permit)
    decl = Declaration("claim", "Fixture mint", WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                       MIN_OUTPUT_BUDGET, (), (), Path("."))

    def handler(ctx, writer):
        if has_act:
            writer.add(fixture_proposition_node("committed"))
        session.seal(1)
        writer.add(fixture_proposition_node("after"))
        pytest.fail("a sealed writer admitted an act")

    path = ledger_path(cfg.operations_root, session.session_id)
    try:
        with Scratch(certified_work, cfg.operations_root, threading.Event()) as inputs:
            d = Dispatcher([decl], {"claim": handler}, ReadContext.open(cfg), session=session, run_inputs=inputs)
            with pytest.raises(Refused) as caught:
                d.invoke("claim", {}, invocation_id="attempt")
            assert caught.value.refusal.code == "run-sealed"
            with pytest.raises(Refused, match="run-sealed"):
                d.invoke("claim", {}, invocation_id="late")
    finally:
        session.close()
    lines = [json.loads(row) for row in path.read_bytes().splitlines()]
    assert [row["line"] for row in lines[-2:]] == ["invocation-close", "session-close"]
    outcome = lines[-2]["outcome"]
    if has_act:
        assert outcome["done"][0][1] == "proposition:committed"
    else:
        assert outcome["refusal"]["code"] == "run-sealed"
    assert not any(row.get("invocation") == "late" for row in lines)
