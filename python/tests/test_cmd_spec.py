"""Native spec authoring with real held prerequisites and pre-write refusals."""
from dataclasses import replace
from decimal import Decimal
import json

import pytest
from beliefs import stored
from beliefs.errors import (MeasurementNotAdmitted, DependencyCycle, DependencyNotHeld, MalformedRecord,
                           MeasurementError, MalformedRestriction, RuleUnbound)
from helpers.snapshot import snapshot
from helpers.analysis import analysis_nodes, bootstrap_analysis, write_estimand_document
from helpers.world import (build_belief_world, build_spec_rig_world, hold_fixture_dataset,
                           level_list_address, concept_list_address, open_rig, FIXTURE_AUTHORITY)
from science.refusal import Refused


def inputs(cfg, *, target="proposition:p1", dataset, **overrides):
    from helpers.analysis import spec_inputs
    return spec_inputs(cfg, target=target, dataset=dataset, **overrides)


@pytest.fixture
def rig(certified_worker_work):
    snap = snapshot(certified_worker_work, "spec-rig", build_spec_rig_world)
    snap.restore()
    cfg, ref = snap.value
    with open_rig(cfg, ("spec",)) as (d, ctx):
        yield d, ctx, ref


def specs(ctx):
    return [n for n in ctx.write_view().iter_stored() if n.kind == "analysis-spec"]


def mutate_document(arguments, mutate):
    from pathlib import Path
    path = Path(arguments["estimand"])
    document = json.loads(path.read_text())
    mutate(document)
    path.write_text(json.dumps(document))


def refuse_and_replay(d, ctx, arguments):
    with pytest.raises(Refused) as first:
        d.invoke("spec", arguments, invocation_id="RefuseSpec")
    with pytest.raises(Refused) as second:
        d.invoke("spec", arguments, invocation_id="RefuseSpec")
    assert first.value.refusal.code == "invalid-input"
    assert second.value.refusal == first.value.refusal
    assert specs(ctx) == []
    return first.value.refusal


def test_spec_freezes_a_typed_estimand_and_the_record_id_is_the_identity(rig):
    d, ctx, ref = rig
    d.invoke("spec", inputs(ctx.config, dataset=ref, parameters=["alpha=0.05"]))
    node, = specs(ctx)
    spec = stored.analysis_spec_value(node, profile=ctx.config.profile)
    assert node.id == f"analysis-spec:{spec.identity}"
    assert spec.parameters["alpha"] == Decimal("0.05")
    assert spec.nondeterminism.projection() == {"variant": "deterministic"}
    assert spec.estimand.functional == "general/probability-of-superiority"
    assert spec.estimand.bindings["grouping"].classes[0].term == "level:early"
    assert spec.estimand.outputs["estimate"].typing == "dimensionless"
    assert spec.estimand.reference.value == Decimal("0.5")
    assert dict(spec.applicability.values) == {}
    assert spec.standing == "empirical" and spec.registers == ()
    assert len(spec.input_roles) == 1 and spec.input_roles[0].mode == "observation"
    assert any(
        b.procedure == analysis_nodes(ctx.config.profile)[2].id for b in spec.rule_bindings)


@pytest.mark.parametrize("value", [0, 1, 0.5])
def test_integer_and_fraction_reference_freeze_exactly(rig, value):
    d, ctx, ref = rig
    args = inputs(ctx.config, dataset=ref)
    mutate_document(args, lambda doc: doc["reference"].update(value=value))
    d.invoke("spec", args)
    spec = stored.analysis_spec_value(specs(ctx)[0], profile=ctx.config.profile)
    assert type(spec.estimand.reference.value) is Decimal
    assert spec.estimand.reference.value == Decimal(str(value))


@pytest.mark.parametrize("value", [True, "0.5", float("nan"), float("inf")])
def test_invalid_numeric_input_refuses_before_mint_and_replays(rig, value):
    d, ctx, ref = rig
    args = inputs(ctx.config, dataset=ref)
    mutate_document(args, lambda doc: doc["reference"].update(value=value))
    refuse_and_replay(d, ctx, args)


@pytest.mark.parametrize("flag", ["contrast", "slot", "baseline", "comparison", "quantity", "increment",
                                  "measure", "scale", "reference", "identification", "conditioning"])
def test_retired_scalar_flags_refuse_canonicalization(rig, flag):
    d, ctx, ref = rig
    refuse_and_replay(d, ctx, inputs(ctx.config, dataset=ref, **{flag: "retired"}))


@pytest.mark.parametrize("change", [{"standing": "empirical", "model": "procedure:" + "a" * 64},
                                    {"standing": "model"}, {"standing": "calibrated-model"},
                                    {"rule_procedures": ["unknown=procedure:" + "a" * 64]},
                                    {"rule_procedures": []},
                                    {"registers": ["assumptions-register:" + "a" * 64]}])
def test_standing_and_rule_dependencies_refuse_and_replay(rig, change):
    d, ctx, ref = rig
    refuse_and_replay(d, ctx, inputs(ctx.config, **({"dataset": ref} | change)))


def test_duplicate_rule_procedures_refuse(rig):
    d, ctx, ref = rig
    args = inputs(ctx.config, dataset=ref)
    args["rule_procedures"] *= 2
    refuse_and_replay(d, ctx, args)


def test_applicability_qualifier_is_typed_and_accepted(rig):
    d, ctx, ref = rig
    d.invoke("spec", inputs(ctx.config, dataset=ref, applicability=["testing/scope=generic:cohort:adults"]))
    spec = stored.analysis_spec_value(specs(ctx)[0], profile=ctx.config.profile)
    assert spec.applicability.values["testing/scope"].quantifier == "generic"


@pytest.mark.parametrize("entry", ["scope", "testing/nope=generic:cohort:adults", "testing/scope=most:cohort:adults"])
def test_applicability_authoring_errors_refuse_and_replay_exactly(rig, entry):
    d, ctx, ref = rig
    refuse_and_replay(d, ctx, inputs(ctx.config, dataset=ref, applicability=[entry]))


@pytest.mark.parametrize("form", ["claim", "union", "interval", "time-interval", "rule"])
def test_non_term_or_claim_side_dimensions_refuse(certified_work, monkeypatch, form):
    import yaml
    import helpers.world as world
    document = yaml.safe_load(world.TEST_CONTRACT)
    dim = document["contract"]["dimensions"]["scope"]
    if form == "claim":
        dim["placement"] = "claim"
        dim.pop("restriction")
    else:
        dim["restriction"] = {"form": form}
        if form == "union": dim["restriction"]["of"] = {"form": "term", "sort": "cohort"}
        if form == "interval": dim["restriction"]["quantity_kind"] = "general/relative-abundance"
        if form == "rule": dim["restriction"]["classes"] = "level"
    monkeypatch.setattr(world, "TEST_CONTRACT", yaml.safe_dump(document))
    cfg = build_belief_world(certified_work)
    data = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec",)) as (d, ctx):
        refusal = refuse_and_replay(d, ctx, inputs(cfg, dataset=data, applicability=["testing/scope=generic:cohort:adults"]))
        assert form in refusal.message


@pytest.mark.parametrize("error", [DependencyCycle, DependencyNotHeld, MalformedRecord, MalformedRestriction,
                                    MeasurementError, MeasurementNotAdmitted, RuleUnbound])
def test_complete_kernel_error_boundary_refuses_before_write(rig, monkeypatch, error):
    d, ctx, ref = rig
    import science.commands.spec as spec_module
    def refuse(*args, **kwargs): raise error("boundary test")
    monkeypatch.setattr(spec_module, "freeze", refuse)
    refusal = refuse_and_replay(d, ctx, inputs(ctx.config, dataset=ref))
    assert refusal.data["kind"] == error.__name__


@pytest.mark.parametrize("kind", ["procedure", "register", "calibration"])
@pytest.mark.parametrize("standing", ["missing", "retracted", "unaccepted"])
def test_dependency_standing_prevents_spec_mint(certified_work, monkeypatch, kind, standing):
    from beliefs.belief import AcceptancePolicy
    from beliefs.corpus import ReadView
    from beliefs.measurement import Observable
    from beliefs.proxy_model import Calibration, ProxyModel, ProxySource, ProxyTarget
    from beliefs.register import AssumptionsRegister
    from nodes.core.corpus import Corpus
    from test_authoring_records import retract
    cfg = build_belief_world(certified_work)
    args = inputs(cfg, dataset=hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression"))
    if kind == "procedure":
        existing = ReadView.opened_at(cfg.write_root).get(analysis_nodes(cfg.profile)[0].id)
        from beliefs.procedure import procedure_from_stored
        node = stored.procedure_node(replace(procedure_from_stored(existing), name="Required assay"))
        mutate_document(args, lambda doc: doc["bindings"]["response"]["measure"].update(procedure=node.id, scale=node.id))
    elif kind == "register":
        node = stored.assumptions_register_node(AssumptionsRegister("testing:" + cfg.profile.activated_contracts["testing"], None, {}))
        args["registers"] = [node.id]
    else:
        obs = Observable("general/relative-abundance", "testing/protein")
        node = stored.proxy_model_node(ProxyModel(ProxySource(obs, analysis_nodes(cfg.profile)[0].id),
            ProxyTarget(obs, None), {}, Calibration(obs, (), (), None), None))
        mutate_document(args, lambda doc: doc.update(calibration=node.id))
    if standing != "missing":
        Corpus(cfg.write_root).add(node)
    if standing == "retracted":
        Corpus(cfg.write_root).add(retract(node, "withdraw dependency"))
    if standing == "unaccepted":
        monkeypatch.setattr("science.acceptance.policy", lambda ctx: AcceptancePolicy(
            counts=lambda cid, ref: ref != node.id, statement="exclude dependency"))
    with open_rig(cfg, ("spec",)) as (d, ctx):
        refusal = refuse_and_replay(d, ctx, args)
        assert node.id in refusal.message


def test_unheld_level_vocabulary_refuses_naming_its_address_and_mints_nothing(certified_work):
    cfg = build_belief_world(certified_work, hold_levels=False)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec",)) as (d, ctx):
        refusal = refuse_and_replay(d, ctx, inputs(cfg, dataset=ref))
        assert level_list_address() in refusal.message


def test_an_unheld_vocabulary_under_a_conditioning_term_refuses(certified_work):
    cfg = build_belief_world(certified_work, hold_concepts=False)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    args = inputs(cfg, dataset=ref)
    mutate_document(args, lambda doc: doc["control"].update(conditioning=[{"sort":"testing/concept", "term":"concept:remission"}]))
    with open_rig(cfg, ("spec",)) as (d, ctx):
        assert concept_list_address() in refuse_and_replay(d, ctx, args).message


@pytest.mark.parametrize("change", [{"interpretation_rule": "nope/v9"}, {"dataset": "dataset:sha256:" + "0" * 64},
                                    {"parameters": ["alpha"]}, {"supersedes": "bare-identity"},
                                    {"supersedes": "analysis-spec:" + "0" * 64}])
def test_invalid_references_and_parameters_refuse(rig, change):
    d, ctx, ref = rig
    refuse_and_replay(d, ctx, inputs(ctx.config, **({"dataset": ref} | change)))


def test_supersedes_a_held_spec_mints_the_successor(rig):
    d, ctx, ref = rig
    d.invoke("spec", inputs(ctx.config, dataset=ref))
    first = specs(ctx)[0].id
    d.invoke("spec", inputs(ctx.config, dataset=ref, method="revised method", supersedes=first))
    assert len(specs(ctx)) == 2


@pytest.mark.parametrize("epoch", ["missing", "stale"])
def test_claim_dataset_spec_authoring_with_read_mounts_needs_no_epoch(certified_work, epoch):
    from helpers.world import build_two_corpus_world
    from science.world_belief import publish_session_epoch
    cfg = build_two_corpus_world(certified_work)
    bootstrap_analysis(cfg)
    if epoch == "stale": publish_session_epoch(cfg)
    source = certified_work / "authoring.txt"
    source.write_bytes(b"new empirical input\n")
    with open_rig(cfg, ("claim", "dataset", "spec")) as (d, ctx):
        d.invoke("claim", {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
                           "layer": "causal", "polarity": "positive", "slug": "p1"})
        result = d.invoke("dataset", {"path": str(source), "title": "new input"})
        data = next(t for t in result.text.split() if t.startswith("dataset:"))
        d.invoke("spec", inputs(cfg, dataset=data))
        assert len(specs(ctx)) == 1
        from science.config import ReadContext
        with pytest.raises(Refused) as caught:
            ReadContext.open(cfg).world_read()
        assert caught.value.refusal.code == ("no-epoch" if epoch == "missing" else "epoch-stale")


def test_non_member_level_in_native_document_refuses(rig):
    d, ctx, ref = rig
    args = inputs(ctx.config, dataset=ref)
    mutate_document(args, lambda doc: doc["bindings"]["grouping"]["classes"][1].update(term="level:never"))
    refuse_and_replay(d, ctx, args)


def test_an_unheld_vocabulary_under_an_applicability_restriction_refuses(certified_work):
    from beliefs.classification_rule import ClassificationRule
    from beliefs.measurement import Observable
    from beliefs.root import open_corpus
    cfg = build_belief_world(certified_work, hold_levels=False)
    rule = open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(stored.classification_rule_node(
        ClassificationRule("testing/cohort", (Observable("general/relative-abundance", "testing/protein"),),
                           "Synthetic cohort grouping independent of the stage vocabulary.", None, None, "fixture")))
    args = inputs(cfg, dataset=hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression"),
                  applicability=["testing/stage=generic:level:early"])
    mutate_document(args, lambda doc: doc["bindings"].update(grouping={"source": "rule-classes", "rule": rule.id,
        "classes": [{"sort": "testing/cohort", "term": "cohort:early"}, {"sort": "testing/cohort", "term": "cohort:late"}]}))
    with open_rig(cfg, ("spec",)) as (d, ctx):
        assert level_list_address() in refuse_and_replay(d, ctx, args).message


def test_a_held_register_is_frozen_in_the_target_dependency_set(rig):
    from beliefs.register import AssumptionsRegister
    from beliefs.root import open_corpus
    d, ctx, ref = rig
    cfg = ctx.config
    register = open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(
        stored.assumptions_register_node(AssumptionsRegister("testing:" + cfg.profile.activated_contracts["testing"], None, {})))
    d.invoke("spec", inputs(cfg, dataset=ref, registers=[register.id]))
    spec = stored.analysis_spec_value(specs(ctx)[0], profile=cfg.profile)
    assert spec.registers == (register.id,)
    assert register.id in {entry.id for entry in spec.assessed_target.dependencies}


def test_model_spec_freezes_an_explicit_held_model_for_a_native_model_claim(certified_work, monkeypatch):
    import yaml
    import helpers.world as world
    from beliefs.claim import Referent, build_claim
    from beliefs.procedure import ModelInputs, Procedure
    from beliefs.projection import project_claim
    from beliefs.root import open_corpus
    document = yaml.safe_load(world.TEST_CONTRACT)
    document["contract"]["sorts"]["model-ref"] = {"binding": {"kind": "world-kind", "world_kind": "procedure"}}
    monkeypatch.setattr(world, "TEST_CONTRACT", yaml.safe_dump(document))
    cfg = build_belief_world(certified_work)
    writer = open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile)
    model = writer.add(stored.procedure_node(Procedure("testing/model", "Fixture model", "Explicit empty-input model.",
        (), None, {}, (), (), None, ModelInputs((), ()), {}, None)))
    claim = build_claim(cfg.profile, operator="general/changes-under-intervention", roles={
        "intervention": Referent("testing/concept", "concept:disease-stage"),
        "response": Referent("testing/protein", "protein:PHF19"),
        "within-model": Referent("testing/model-ref", model.id)}, layer="causal", polarity="positive")
    writer.add(stored.proposition_node("modeled", title="modeled", claim=project_claim(claim)))
    data = hold_fixture_dataset(cfg, "simulation.txt", b"model output\n", "simulation")
    with open_rig(cfg, ("spec",)) as (d, ctx):
        d.invoke("spec", inputs(cfg, target="proposition:modeled", dataset=data,
                               standing="model", model=model.id, evidence_mode="simulation"))
        value = stored.analysis_spec_value(specs(ctx)[0], profile=cfg.profile)
        assert value.standing == "model" and value.model == model.id
        assert model.id in {entry.id for entry in value.assessed_target.dependencies}
