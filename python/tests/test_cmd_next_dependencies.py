"""Native dependency eligibility must reach the queue admission gate."""
import pytest
from beliefs import stored
from beliefs.confinement import host_prerequisites
from beliefs.root import open_corpus
from helpers.analysis import analysis_nodes
from helpers.world import FIXTURE_AUTHORITY, walk_belief_path_confined
from science.commands.next import classify
from science.config import ReadContext


def test_next_single_key_admission_uses_dependency_evidence(certified_work):
    reason = host_prerequisites()
    if reason is not None:
        pytest.skip(f"confinement unavailable: {reason}")
    cfg, proposition = walk_belief_path_confined(certified_work)
    assert classify(ReadContext.open(cfg), proposition) == "admitted"
    procedure = ReadContext.open(cfg).write_view().get(analysis_nodes(cfg.profile)[0].id)
    correction = stored.retraction_node(title="withdraw procedure", target=stored.NodeTarget(
        procedure.id, procedure.id, stored.stored_semantic_hash(procedure)), reason="authored-error",
        rationale="The fixture procedure is withdrawn.", grounds=(procedure.id,), actor="fixture", event_token="withdraw")
    open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).retract(correction)
    ctx = ReadContext.open(cfg)
    (key,) = ctx.claim_view(proposition).beliefs
    inputs = ctx.gather_inputs(proposition, key=key)
    assert type(inputs.dependencies.closure.verdicts[procedure.id]).__name__ == "Ineligible"
    assert classify(ctx, proposition) == "assessed-not-admitted"


def test_next_multikey_stays_unevaluated_when_each_key_is_admitted(certified_work):
    from decimal import Decimal
    from helpers.analysis import spec_inputs, write_estimand_document
    from helpers.world import fixture_bundle, open_rig
    reason = host_prerequisites()
    if reason is not None:
        pytest.skip(f"confinement unavailable: {reason}")
    cfg, proposition = walk_belief_path_confined(certified_work)
    ctx = ReadContext.open(cfg)
    original = next(stored.analysis_spec_value(node, profile=cfg.profile)
                    for node in ctx.write_view().iter_stored() if node.kind == "analysis-spec")
    inputs = spec_inputs(cfg, target=proposition, dataset=original.input_roles[0].dataset)
    inputs["estimand"] = str(write_estimand_document(cfg, reference=Decimal(0)))
    code, entrypoint, targets = fixture_bundle(certified_work)
    with open_rig(cfg, ("spec", "run", "assess", "verify")) as (d, _):
        spec = next(t for t in d.invoke("spec", inputs).text.split() if t.startswith("analysis-spec:"))
        run = next(t for t in d.invoke("run", {"spec": spec, "dataset": inputs["dataset"], "code": str(code),
            "entrypoint": entrypoint, "targets": list(targets)}).text.split() if t.startswith("run:"))
        assessment = next(t for t in d.invoke("assess", {"run": run}).text.split() if t.startswith("assessment:"))
        d.invoke("verify", {"assessment": assessment, "code": str(code), "entrypoint": entrypoint})
    ctx = ReadContext.open(cfg)
    keys = tuple(ctx.claim_view(proposition).beliefs)
    assert len(keys) == 2
    assert [type(ctx.evaluate(proposition, key=key)).__name__ for key in keys] == ["Belief", "Belief"]
    assert classify(ctx, proposition) == "assessed-unevaluated"
