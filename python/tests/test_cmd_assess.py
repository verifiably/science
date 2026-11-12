from helpers.analysis import spec_inputs
import pytest

from science.refusal import Refused
from helpers.world import (OBSERVED, build_belief_world, fixture_bundle, hold_fixture_dataset, mint_fixture_run, open_rig)


@pytest.fixture
def rig(certified_work):
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression", **OBSERVED)
    with open_rig(cfg, ("spec",)) as (d, _):
        spec_ref = next(t for t in d.invoke("spec", spec_inputs(cfg, target="proposition:p1", dataset=ref)).text.split()
                        if t.startswith("analysis-spec:"))
    # The fixture run is minted outside any session, so no attended session
    # may be open across it: a session's writer is the corpus's one writer.
    run_ref = mint_fixture_run(cfg, spec_ref, ref, fixture_bundle(certified_work, "supported"))
    with open_rig(cfg, ("assess",)) as (d, ctx):
        yield d, ctx, run_ref


def test_assess_mints_the_assessment_the_outcome_file_fixes(rig):
    d, ctx, run_ref = rig
    out = d.invoke("assess", {"run": run_ref})
    assert "[assessment] assessment:" in out.text
    view = ctx.write_view()
    from beliefs import stored
    node = next(n for n in view.iter_stored() if n.kind == "assessment")
    value = stored.assessment_value(node, profile=ctx.config.profile)
    assert value.outcome == "supported"
    assert value.proposition == "proposition:p1"
    assert node.id == f"assessment:{value.identity()}"
    spec = stored.analysis_spec_value(view.get("analysis-spec:" + value.spec), profile=ctx.config.profile)
    assert value.target == spec.assessed_target
    assert value.estimates == {} and value.uncertainty is None and value.curves == {}


def test_assess_refuses_an_unknown_run(rig):
    d, _, _ = rig
    with pytest.raises(Refused) as caught:
        d.invoke("assess", {"run": "run:" + "0" * 64})
    assert caught.value.refusal.code == "invalid-input"


def test_named_rule_payload_survives_the_assessment_command(certified_work, monkeypatch):
    from decimal import Decimal as D
    from beliefs import stored
    from beliefs.assess import build_assessment
    from beliefs.assessment_payload import Interval
    from beliefs.runrecord import decode_run_closure
    from beliefs.rules import REFERENCE_RULES
    from beliefs.spec import RuleImplementation, RuleFixture
    from helpers.analysis import assess_target
    from science.config import ReadContext
    payload = {"outcome": "supported", "estimates": {"estimate": D("0.4")},
               "uncertainty": {"estimate": {"kind": "interval", "low": D("0.1"), "high": D("0.7"), "level": D("0.95")}}}
    rule = RuleImplementation("fixture/named-payload/v1", lambda manifest: payload, (RuleFixture((None,), payload),))
    import science.commands.spec as spec_module
    import science.commands.assess as assess_module
    implementations = dict(REFERENCE_RULES) | {"beliefs/outcome-file/v1": rule}
    monkeypatch.setattr(spec_module, "REFERENCE_RULES", implementations)
    monkeypatch.setattr(assess_module, "REFERENCE_RULES", implementations)
    cfg = build_belief_world(certified_work)
    ref, value = assess_target(cfg, certified_work)
    view = ReadContext.open(cfg).write_view()
    spec = stored.analysis_spec_value(view.get("analysis-spec:" + value.spec), profile=cfg.profile)
    derived = build_assessment(decode_run_closure(view.get("run:" + value.run)),
        specs={spec.identity: spec}, implementations={rule.identity: rule})
    assert value.identity() == derived.identity()
    assert value.target == derived.target == spec.assessed_target
    assert value.estimates == {"estimate": D("0.4")}
    assert value.uncertainty == {"estimate": Interval(D("0.1"), D("0.7"), D("0.95"))}
    assert value.curves == {} and ref == "assessment:" + derived.identity()
