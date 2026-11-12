"""A real native event target exercises the command's named curve persistence."""
import json
from pathlib import Path
from decimal import Decimal as D


def test_assess_preserves_native_event_curves(certified_work, monkeypatch):
    import yaml
    import helpers.world as world
    import science.commands.spec as spec_module
    import science.commands.assess as assess_module
    from beliefs import stored
    from beliefs.assess import build_assessment
    from beliefs.assessment_payload import CurvePoint, Interval
    from beliefs.runrecord import decode_run_closure
    from beliefs.spec import RuleImplementation, RuleFixture
    from helpers.analysis import spec_inputs
    from science.config import ReadContext

    contract = yaml.safe_load(world.TEST_CONTRACT)
    body = contract["contract"]
    body["estimands"]["instantiation:affects-concept-protein"]["forms"].append("event-locked")
    body["quantity_kinds"] = {"duration": {"dimension": {"T": 1}, "definition": "Elapsed fixture time."}}
    body["units"] = {"second": {"symbol": "s", "quantity_kind": "duration", "definition": "A second."}}
    body["functionals"] = {"event-response": {
        "definition": "Synthetic normalized response after a classified event.",
        "form": "event-locked", "arity": "two", "response_transformation": "invariant-strictly-increasing",
        "reversal": "complement", "response_reversal": "complement", "exchange": "not-applicable",
        "ties": "midrank", "output": "dimensionless", "domain": "unit-interval", "null": "half",
        "increment": "not-applicable", "uncertainty": "exact", "parameters": "not-applicable"}}
    monkeypatch.setattr(world, "TEST_CONTRACT", yaml.safe_dump(contract))
    payload = {"outcome": "supported", "curves": {"estimate": [
        {"lag": D(0), "estimate": D("0.4"), "uncertainty": {"kind": "interval", "low": D("0.1"), "high": D("0.7"), "level": D("0.95")}},
        {"lag": D(1), "estimate": D("0.6")}]}}
    rule = RuleImplementation("fixture/event-payload/v1", lambda manifest: payload, (RuleFixture((None,), payload),))
    implementations = dict(spec_module.REFERENCE_RULES) | {"beliefs/outcome-file/v1": rule}
    monkeypatch.setattr(spec_module, "REFERENCE_RULES", implementations)
    monkeypatch.setattr(assess_module, "REFERENCE_RULES", implementations)
    cfg = world.build_belief_world(certified_work)
    data = world.hold_fixture_dataset(cfg, "data.txt", b"event\n", "event observations", **world.OBSERVED)
    inputs = spec_inputs(cfg, target="proposition:p1", dataset=data)
    path = Path(inputs["estimand"])
    document = json.loads(path.read_text())
    grouping = document["bindings"].pop("grouping")
    grouping.pop("source")
    document.update(form="event-locked", functional="testing/event-response")
    document["bindings"].update(anchor=grouping, lag={"unit": "testing/second", "windows": []})
    path.write_text(json.dumps(document))
    with world.open_rig(cfg, ("spec",)) as (d, _):
        spec_ref = next(t for t in d.invoke("spec", inputs).text.split() if t.startswith("analysis-spec:"))
    run = world.mint_fixture_run(cfg, spec_ref, data, world.fixture_bundle(certified_work))
    with world.open_rig(cfg, ("assess",)) as (d, _):
        ref = next(t for t in d.invoke("assess", {"run": run}).text.split() if t.startswith("assessment:"))
    view = ReadContext.open(cfg).write_view()
    value = stored.assessment_value(view.get(ref), profile=cfg.profile)
    spec = stored.analysis_spec_value(view.get(spec_ref), profile=cfg.profile)
    derived = build_assessment(decode_run_closure(view.get(run)), specs={spec.identity: spec}, implementations={rule.identity: rule})
    assert value.identity() == derived.identity() and value.target == spec.assessed_target
    assert value.estimates == {} and value.uncertainty is None
    assert value.curves == {"estimate": (CurvePoint(D(0), D("0.4"), Interval(D("0.1"), D("0.7"), D("0.95"))), CurvePoint(D(1), D("0.6"), None))}
