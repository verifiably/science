"""Operational authoring failures retain their protocol category and replay."""
import pytest

from beliefs.errors import (CaptureDrift, CoverageUnresolvable, PermitExceeded,
                           PermitFact, PermitSummary, RuleNotHeld)
from helpers.analysis import spec_inputs
from helpers.snapshot import snapshot
from helpers.world import build_spec_rig_world, open_rig
from science.refusal import Refused


@pytest.fixture
def rig(certified_worker_work):
    saved = snapshot(certified_worker_work, "operational-authoring", build_spec_rig_world)
    saved.restore()
    cfg, dataset = saved.value
    with open_rig(cfg, ("claim", "spec")) as (dispatcher, ctx):
        yield dispatcher, ctx, dataset


@pytest.mark.parametrize("command", ["claim", "spec"])
@pytest.mark.parametrize("failure,code,data", [
    (RuleNotHeld("holdings reducer missing"), "kernel-refused", {"kind": "RuleNotHeld"}),
    (CoverageUnresolvable("carrier unavailable"), "kernel-refused", {"kind": "CoverageUnresolvable"}),
    (CaptureDrift("capture changed"), "kernel-refused", {"kind": "CaptureDrift"}),
    (PermitExceeded(PermitFact("family", "holdings"), PermitSummary((), (), False)),
     "permit-exceeded", {"requirement": "PermitFact(dimension='family', name='holdings')",
                         "capability": "PermitSummary(kinds=(), act_families=(), ungoverned=False)"}),
])
def test_operational_capture_refusal_replays_without_mint(rig, monkeypatch, command, failure, code, data):
    dispatcher, ctx, dataset = rig
    arguments = (spec_inputs(ctx.config, target="proposition:p1", dataset=dataset) if command == "spec" else
                 {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
                  "layer": "causal", "polarity": "positive", "slug": "unminted"})
    before = {node.id for node in ctx.write_view().iter_stored()}

    # Keep capture, selection, dispatcher and ledger real; fail only holdings' read.
    def fail_reduction(*args, **kwargs):
        raise failure

    with monkeypatch.context() as patch:
        patch.setattr("science.authoring_records.found_observations", fail_reduction)
        with pytest.raises(Refused) as first:
            dispatcher.invoke(command, arguments, invocation_id="OperationalAuthoring")
    assert first.value.refusal.code == code
    assert first.value.refusal.message == str(failure)
    assert first.value.refusal.data == data
    # The cause is gone: an exact retry still replays the closed refusal.
    with pytest.raises(Refused) as replay:
        dispatcher.invoke(command, arguments, invocation_id="OperationalAuthoring")
    assert replay.value.refusal == first.value.refusal
    assert dispatcher._session.invocation_acts("OperationalAuthoring") == ()
    assert {node.id for node in ctx.write_view().iter_stored()} == before


def test_operational_freeze_refusal_is_not_scientific_invalid_input(rig, monkeypatch):
    dispatcher, ctx, dataset = rig
    arguments = spec_inputs(ctx.config, target="proposition:p1", dataset=dataset)

    def unavailable(*args, **kwargs):
        raise RuleNotHeld("rule capture lost")

    with monkeypatch.context() as patch:
        patch.setattr("science.commands.spec.freeze", unavailable)
        with pytest.raises(Refused) as first:
            dispatcher.invoke("spec", arguments, invocation_id="OperationalFreeze")
    assert first.value.refusal.code == "kernel-refused"
    assert first.value.refusal.data == {"kind": "RuleNotHeld"}
    with pytest.raises(Refused) as replay:
        dispatcher.invoke("spec", arguments, invocation_id="OperationalFreeze")
    assert replay.value.refusal == first.value.refusal
    assert dispatcher._session.invocation_acts("OperationalFreeze") == ()
    assert not [node for node in ctx.write_view().iter_stored() if node.kind == "analysis-spec"]
