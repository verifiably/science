"""Authoring reads real session records with accepted custody and one retraction fold."""
from dataclasses import replace
from hashlib import sha256

import pytest
from nodes.core.corpus import Corpus
from beliefs import stored
from beliefs.belief import AcceptancePolicy
from beliefs.corpus import ReadView
from beliefs.errors import DependencyNotHeld, ScienceError
from helpers.analysis import analysis_nodes, bootstrap_analysis
from helpers.world import (FIXTURE_AUTHORITY, archive_config, build_two_corpus_world,
                           hold_fixture_dataset, build_belief_world)
from science.config import ReadContext, corpus_id_at
from science.refusal import Refused


def put(root, node):
    Corpus(root).add(node)


def retract(node, token):
    return stored.retraction_node(title=token,
        target=stored.NodeTarget(node.id, node.id, stored.stored_semantic_hash(node)),
        reason="authored-error", rationale="Synthetic correction.", grounds=(node.id,),
        actor="fixture", event_token=token)


def test_session_record_acceptance_and_copy_conflicts(certified_work, monkeypatch):
    from science.authoring_records import session_records
    cfg = build_two_corpus_world(certified_work)
    bootstrap_analysis(cfg)
    node = ReadView.opened_at(cfg.write_root).get(analysis_nodes(cfg.profile)[0].id)
    archive = certified_work / "archive"
    put(archive, node)
    own, other = corpus_id_at(cfg.write_root), corpus_id_at(archive)
    # Explicit acceptance seam over real views; policy branch semantics have their own tests.
    monkeypatch.setattr("science.acceptance.policy", lambda ctx: AcceptancePolicy(
        counts=lambda cid, address: cid == other, statement="archive only"))
    with session_records(ReadContext.open(cfg)) as records:
        assert records.holds(node.id)
        assert records.read(node.id) == node
        assert records.holder(node.id).corpus_id == other
    monkeypatch.setattr("science.acceptance.policy", lambda ctx: AcceptancePolicy(
        counts=lambda cid, address: False, statement="none"))
    with session_records(ReadContext.open(cfg)) as records:
        assert not records.holds(node.id)
        with pytest.raises(DependencyNotHeld):
            records.read(node.id)
    # Differing rejected copies still refuse before acceptance filtering.
    put(archive, node.model_copy(update={"title": "Different copy"}))
    with pytest.raises(Refused, match="copies differ"):
        with session_records(ReadContext.open(cfg)) as records:
            records.holds(node.id)


@pytest.mark.parametrize("reject_counter", [False, True])
def test_cross_mount_counter_retractions_are_folded_once(certified_work, monkeypatch, reject_counter):
    from science.authoring_records import session_records
    cfg = build_two_corpus_world(certified_work)
    bootstrap_analysis(cfg)
    node = analysis_nodes(cfg.profile)[0]
    first = retract(node, "first")
    counter = retract(first, "counter")
    put(cfg.write_root, first)
    put(certified_work / "archive", counter)
    monkeypatch.setattr("science.acceptance.policy", lambda ctx: AcceptancePolicy(
        counts=lambda cid, address: not (reject_counter and address == counter.id), statement="counter selection"))
    with session_records(ReadContext.open(cfg)) as records:
        assert records.retraction_in_force(node.id) is reject_counter
        assert records.holds(node.id) is not reject_counter
        assert (node.id in {n.id for n in records.iter_stored()}) is not reject_counter
        assert records.retraction_in_force(first.id) is not reject_counter


@pytest.mark.parametrize("corruption", ["target", "content", "cycle", "facet", "arm"])
def test_malformed_or_cyclic_accepted_retractions_refuse(certified_work, corruption):
    from science.authoring_records import session_records
    cfg = build_belief_world(certified_work)
    node = analysis_nodes(cfg.profile)[0]
    correction = retract(node, "bad")
    if corruption == "target":
        correction.facets["retraction"]["target"]["ref"] = "procedure:missing"
    elif corruption == "content":
        correction.facets["retraction"]["target"]["content_identity"] = "a" * 64
    elif corruption == "cycle":
        correction.facets["retraction"]["target"]["ref"] = correction.id
        correction.facets["retraction"]["target"]["resolved"] = correction.id
    elif corruption == "arm":
        correction.facets["retraction"]["target"]["arm"] = []
    else:
        correction.facets["retraction"]["extra"] = True
    put(cfg.write_root, stored.stamp_semantic_identity(correction))
    with pytest.raises(ScienceError):
        with session_records(ReadContext.open(cfg)):
            pass


def test_session_observation_lookup_uses_content_digest(certified_work):
    from science.authoring_records import session_records
    cfg = build_two_corpus_world(certified_work)
    data = b"content digest\n"
    address = hold_fixture_dataset(archive_config(cfg), "code.py", data, "code")
    with session_records(ReadContext.open(cfg)) as records:
        assert records.observation_held("sha256:" + sha256(data).hexdigest())
        assert not records.observation_held(address)
        assert not records.observation_held("sha256:" + "a" * 64)
        assert address in records.observations
    with session_records(ReadContext.open(replace(cfg, coordination=None))) as records:
        assert not records.observation_held("sha256:" + sha256(data).hexdigest())
        assert not records.holds(address)


def test_calibration_authoring_reader_has_no_epoch_dependency(certified_work):
    from science.authoring_records import session_records
    from beliefs.eligibility import Ineligible
    cfg = build_belief_world(certified_work)
    ctx = ReadContext.open(cfg)
    with session_records(ctx) as records:
        assert records.holds(analysis_nodes(cfg.profile)[0].id)
        assert isinstance(records.assessment_eligibility("assessment:" + "a" * 64), Ineligible)
        with pytest.raises(DependencyNotHeld):
            records.assessment_dependency("assessment:" + "a" * 64)
    # Stale/missing epoch reads are deliberately unavailable; authoring never asks.
    class AuthoringContext:
        config, world = cfg, ctx.world
        def mounts(self): return ctx.mounts()
        def session_mounts(self): return ctx.session_mounts()
        def world_read(self): raise AssertionError("authoring accessed epoch")
    with session_records(AuthoringContext()) as records:
        assert records.read(analysis_nodes(cfg.profile)[0].id).kind == "procedure"


def basis_records(cfg):
    """Actual kernel-authored target with stored run and verification evidence."""
    from dataclasses import fields
    from beliefs.applicability import build_applicability
    from beliefs.claim import Referent, build_claim
    from beliefs.estimand import build_estimand
    from beliefs.projection import project_claim
    from beliefs.record import AssessmentValue
    from beliefs.resolution import build_snapshot
    from beliefs.target import AssessedTarget
    from helpers.analysis import write_estimand_document
    from science.estimand_input import read_estimand_input
    from science.authoring_records import session_records
    claim = build_claim(cfg.profile, operator="general/changes-under-intervention",
        roles={"intervention": Referent("testing/concept", "concept:disease-stage"),
               "response": Referent("testing/protein", "protein:PHF19")},
        layer="causal", polarity="positive")
    snapshot = build_snapshot(readable={})
    applicability, _ = build_applicability(cfg.profile, claim, {}, snapshot=snapshot)
    doc = read_estimand_input(write_estimand_document(cfg), profile=cfg.profile)
    with session_records(ReadContext.open(cfg)) as records:
        estimand, _ = build_estimand(cfg.profile, claim,
            **{f.name: getattr(doc, f.name) for f in fields(doc)},
            applicability=applicability, snapshot=snapshot, records=records,
            assessment_dependency=records.assessment_dependency)
    target = AssessedTarget(estimand, applicability, estimand.dependencies, None, "empirical")
    data = hold_fixture_dataset(cfg, "calibration.txt", b"empirical calibration\n", "calibration")
    run = stored.run_node("calibration", title="calibration", spec="a" * 64, observes=(data,))
    value = AssessmentValue(spec="a" * 64, run="calibration", proposition="proposition:calibration",
        outcome="supported", interpretation_rule="fixture/calibration/v1", target=target)
    assessment = stored.assessment_node(value.identity(), title="basis", spec=value.spec,
        run=run.id, proposition=value.proposition, outcome=value.outcome,
        interpretation_rule=value.interpretation_rule, target=target)
    proposition = stored.proposition_node("calibration", title="calibration", claim=project_claim(claim))
    verification = stored.verification_node("basis", title="basis", assessment=value.identity(),
        assessment_ref=assessment.id, scope="clean-environment", verdict="passed")
    for node in (proposition, run, assessment, verification):
        put(cfg.write_root, node)
    return assessment, verification, data


@pytest.mark.parametrize("epoch", ["missing", "stale"])
def test_valid_calibration_basis_uses_same_live_session_without_epoch(certified_work, epoch):
    from science.authoring_records import session_records
    from science.world_belief import publish_session_epoch
    from beliefs.eligibility import Eligible
    cfg = build_two_corpus_world(certified_work)
    if epoch == "stale":
        publish_session_epoch(cfg)
    bootstrap_analysis(cfg)
    assessment, _, _ = basis_records(cfg)
    ctx = ReadContext.open(cfg)
    with pytest.raises(Refused) as caught:
        ctx.world_read()
    assert caught.value.refusal.code == ("no-epoch" if epoch == "missing" else "epoch-stale")
    with session_records(ctx) as records:
        assert isinstance(records.assessment_eligibility(assessment.id), Eligible)
        frozen = records.assessment_dependency(assessment.id)
        assert frozen.facet_digest == stored.assessment_value(assessment, profile=cfg.profile).facet_digest()
        assert frozen.dependencies


@pytest.mark.parametrize("defect", ["verification", "run", "frozen-facet"])
def test_calibration_reader_refuses_ineligible_real_basis(certified_work, defect):
    from science.authoring_records import session_records
    from beliefs.eligibility import Ineligible
    from beliefs.identity import v1
    cfg = build_belief_world(certified_work)
    assessment, verification, _ = basis_records(cfg)
    if defect == "verification":
        put(cfg.write_root, retract(verification, "withdraw verification"))
    elif defect == "run":
        Corpus(cfg.write_root).delete("run:calibration")
    else:
        typed = v1.decode(assessment.facets["assessment"]["typed"].encode())
        typed["dependencies"] = []
        assessment.facets["assessment"]["typed"] = v1.encode(typed).decode()
        put(cfg.write_root, stored.stamp_semantic_identity(assessment))
    with session_records(ReadContext.open(cfg)) as records:
        assert isinstance(records.assessment_eligibility(assessment.id), Ineligible)
        with pytest.raises(DependencyNotHeld):
            records.assessment_dependency(assessment.id)


def test_well_formed_retraction_target_must_resolve_exactly(certified_work):
    from science.authoring_records import session_records
    from beliefs.errors import RetractionTargetUnresolvable
    cfg = build_belief_world(certified_work)
    correction = stored.retraction_node(title="missing", target=stored.NodeTarget(
        "procedure:" + "a" * 64, "procedure:" + "a" * 64, "b" * 64),
        reason="authored-error", rationale="Synthetic correction.",
        grounds=("proposition:p1",), actor="fixture", event_token="missing")
    put(cfg.write_root, correction)
    with pytest.raises(RetractionTargetUnresolvable):
        with session_records(ReadContext.open(cfg)):
            pass


@pytest.mark.parametrize("missing", ["datasets", "code", None])
def test_model_eligibility_checks_actual_input_content_digests(certified_work, missing):
    from beliefs.eligibility import Eligible, Ineligible, closure_eligibility
    from beliefs.procedure import ModelInputs, Procedure
    from science.authoring_records import session_records
    cfg = build_belief_world(certified_work)
    digest = "sha256:" + sha256(b"held model input\n").hexdigest()
    hold_fixture_dataset(cfg, "model-input.txt", b"held model input\n", "model input")
    absent = "sha256:" + "a" * 64
    procedure = Procedure("testing/model", "Synthetic model", "Explicit model input test.", (), None,
        {}, (), (), None, ModelInputs((absent if missing == "datasets" else digest,),
                                      (absent if missing == "code" else digest,)), {}, None)
    from beliefs.root import open_corpus
    node = open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(stored.procedure_node(procedure))
    with session_records(ReadContext.open(cfg)) as records:
        verdict = closure_eligibility((node.id,), records, cfg.profile).verdicts[node.id]
        assert isinstance(verdict, Eligible if missing is None else Ineligible)


def test_crosswalk_lookup_supports_both_scale_directions(certified_work, monkeypatch):
    from fractions import Fraction
    import helpers.world as world
    from beliefs.assumptions import AssumptionInstance
    from beliefs.measurement import Observable
    from beliefs.procedure import procedure_from_stored, Scale
    from beliefs.proxy_model import ProxyModel, ProxySource, ProxyTarget, Crosswalk, Conversion, Error
    from beliefs.root import open_corpus
    from science.authoring_records import session_records
    monkeypatch.setattr(world, "TEST_CONTRACT", world.TEST_CONTRACT.replace(
        "  measurements:\n", "  assumption_kinds:\n    crosswalk-validity:\n      collapses: Synthetic crosswalk validity.\n      particulars: [record]\n  measurements:\n"))
    cfg = build_belief_world(certified_work)
    writer = open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile)
    first = analysis_nodes(cfg.profile)[0]
    second = writer.add(stored.procedure_node(replace(procedure_from_stored(first), name="Other scale",
        scale=Scale(Fraction(0), Fraction(10), "higher-is-more"))))
    obs = Observable("general/relative-abundance", "testing/protein")
    proxy = writer.add(stored.proxy_model_node(ProxyModel(ProxySource(obs, first.id), ProxyTarget(None, second.id), {},
        AssumptionInstance("testing/crosswalk-validity", {"record": "synthetic"}),
        Crosswalk({"population": "synthetic"}, Conversion("multiplicative", Fraction(10), None), Error("absolute", Fraction(0))))))
    with session_records(ReadContext.open(cfg)) as records:
        assert records.crosswalks(first.id, second.id) == (proxy.id,)
        assert records.crosswalks(second.id, first.id) == (proxy.id,)
