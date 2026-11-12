"""Custody is independent of scientific eligibility and preserves frozen references."""
from dataclasses import replace

import pytest
from beliefs import stored
from beliefs.dependencies import DependencyEntry
from beliefs.measurement import Observable
from beliefs.procedure import SameAs, procedure_from_stored
from beliefs.proxy_model import Calibration, ProxyModel, ProxySource, ProxyTarget
from beliefs.referent_mapping import ReferentMapping
from beliefs.register import AssumptionsRegister
from helpers.analysis import analysis_nodes
from science.config import ReadContext
from science.retention import dependency_closure, required
from test_retention import graph, held, holder


def normative_nodes(config, basis):
    profile = config.profile
    assay, classes, _ = analysis_nodes(profile)
    value = stored.assessment_value(basis, profile=profile)
    calibration = stored.assessment_node(value.identity(), title="calibration", spec=value.spec,
        run=stored.typed_ref("run", value.run), proposition=value.proposition, outcome=value.outcome,
        interpretation_rule=value.interpretation_rule, target=value.target)
    mapping = stored.referent_mapping_node(ReferentMapping("testing/protein", "testing/protein", {}, "one-to-one", None, None))
    proxy = stored.proxy_model_node(ProxyModel(ProxySource(Observable("general/relative-abundance", "testing/protein"), assay.id),
        ProxyTarget(Observable("general/relative-abundance", "testing/protein"), None), {}, Calibration(Observable("general/relative-abundance", "testing/protein"),
        (calibration.id,), (value.interpretation_rule,), None), None))
    register = stored.assumptions_register_node(AssumptionsRegister("testing:" + profile.activated_contracts["testing"], None, {}))
    return (assay, mapping, proxy, classes, register, calibration)


@pytest.mark.parametrize("kind", ["procedure", "referent-mapping", "proxy-model", "classification-rule", "assumptions-register", "assessment"])
def test_only_carrier_of_a_frozen_dependency_is_kept(certified_work, graph, kind):
    config, spec_node, dataset, proposition, basis, run, _, _ = graph
    value = stored.analysis_spec_value(spec_node, profile=config.profile)
    nodes = normative_nodes(config, basis)
    dependency = next(node for node in nodes if node.kind == kind)
    facet = stored.assessment_value(dependency, profile=config.profile).facet_digest() if kind == "assessment" else None
    entries = {d.id: d for d in value.assessed_target.dependencies}
    entries.setdefault(dependency.id, DependencyEntry(dependency.id, (), facet))
    target = replace(value.assessed_target, dependencies=tuple(entries[k] for k in sorted(entries)))
    dependent = stored.assessment_node("dependent", title="dependent", spec=value.identity,
        run="run:local", proposition=proposition.id, outcome="supported", interpretation_rule=value.interpretation_rule, target=target)
    # Explicit raw custody fixture: retention never claims this is an eligible derivation.
    base = list(ReadContext.open(config).write_view().iter_stored()) + list(nodes) + [run, stored.run_node("local", title="local", spec=value.identity), dependent]
    base = {node.id: node for node in base if node.id != dependency.id}
    write = holder(certified_work / "write", *base.values(), profile=config.profile)
    predecessor = holder(certified_work / "predecessor", dependency, profile=config.profile)
    observations = ReadContext.open(config).observations()
    result = dependency_closure(write, (predecessor,), observations=observations)
    assert dependency.id in result.addresses and result.unresolved == ()
    pin = replace(held(1), corpus_id=predecessor[0])
    args = dict(keep=(), group_chain=(pin,), tip=("p2", "m2"), mounted=(pin,), write_root=write, observations=observations)
    assert any(dependency.id in reason.detail for reason in required(pin, live=(predecessor,), **args))
    equal = holder(certified_work / "equal", dependency, profile=config.profile)
    assert required(pin, live=(predecessor, equal), **args) == ()
    differing = holder(certified_work / "differing", stored.stamp_semantic_identity(dependency.model_copy(update={"title": "different copy"}, deep=True)), profile=config.profile)
    left = dependency_closure(write, (predecessor, differing), observations=observations)
    right = dependency_closure(write, (differing, predecessor), observations=observations)
    assert left == right
    assert any("unresolved-copy" in reason and dependency.id in reason for reason in left.unresolved)
    assert required(pin, live=(predecessor, differing), **args)


def test_same_holder_world_edges_and_same_as_authority_are_transitive(certified_work, graph):
    config, _, _, _, _, _, _, _ = graph
    assay = analysis_nodes(config.profile)[0]
    scaled = stored.procedure_node(replace(procedure_from_stored(assay), name="shared scale", scale=SameAs(assay.id)))
    run = stored.run_node("local", title="local", spec="", reads=(scaled.id,))
    write = holder(certified_work / "write", run, scaled, profile=config.profile)
    carrier = holder(certified_work / "carrier", assay, profile=config.profile)
    result = dependency_closure(write, (carrier,), observations={})
    assert {run.id, scaled.id, assay.id} <= result.addresses
    assert result.unresolved == ()


def test_differing_holder_with_a_later_normative_reference_is_unresolved(certified_work, graph):
    config, _, _, _, _, _, _, _ = graph
    assay = analysis_nodes(config.profile)[0]
    different = stored.procedure_node(replace(procedure_from_stored(assay), name="later", scale=SameAs("procedure:" + "f" * 64)))
    different = different.model_copy(update={"id": assay.id})  # raw conflicting custody evidence
    write = holder(certified_work / "write", stored.run_node("local", title="local", spec="", reads=(assay.id,)))
    first = holder(certified_work / "first", assay, profile=config.profile)
    later = holder(certified_work / "later", different, profile=config.profile)
    a = dependency_closure(write, (first, later), observations={})
    b = dependency_closure(write, (later, first), observations={})
    assert a == b and a.unresolved
    assert assay.id in " ".join(a.unresolved) and first[0] in " ".join(a.unresolved) and later[0] in " ".join(a.unresolved)


@pytest.mark.parametrize("arm", ["code", "datasets"])
def test_procedure_input_digest_keeps_every_matching_dataset(certified_work, graph, arm):
    from beliefs.procedure import ModelInputs
    config, _, dataset, _, _, _, _, _ = graph
    digest = stored.dataset_declaration(dataset).resources[0].digest
    inputs = ModelInputs((digest,), ()) if arm == "datasets" else ModelInputs((), (digest,))
    model = stored.procedure_node(replace(procedure_from_stored(analysis_nodes(config.profile)[0]),
        name="input-dependent procedure", inputs=inputs))
    write = holder(certified_work / "write", model, profile=config.profile)
    other_digest = "sha256:" + "e" * 64
    combined = stored.dataset_node(title="combined", resources=[{"name": "data", "digest": digest}, {"name": "extra", "digest": other_digest}])
    carrier = holder(certified_work / "carrier", dataset, combined, profile=config.profile)
    observations = ReadContext.open(config).observations()
    # A partially observed declaration also carries the requested resource digest.
    observations[combined.id] = observations[dataset.id]
    result = dependency_closure(write, (carrier,), observations=observations)
    assert {dataset.id, combined.id} <= result.addresses and result.unresolved == ()
    missing = dependency_closure(write, (carrier,), observations={})
    assert any(digest in reason for reason in missing.unresolved)
    pin = replace(held(1), corpus_id=carrier[0])
    reasons = required(pin, keep=(), group_chain=(pin,), tip=("p2", "m2"), mounted=(pin,), write_root=write, live=(carrier,), observations={})
    assert any(digest in detail for reason in reasons for detail in reason.detail)
    args = dict(keep=(), group_chain=(pin,), tip=("p2", "m2"), mounted=(pin,), write_root=write, observations=observations)
    assert required(pin, live=(carrier,), **args)
    equal = holder(certified_work / "equal", dataset, combined, profile=config.profile)
    assert required(pin, live=(carrier, equal), **args) == ()
    different = stored.stamp_semantic_identity(dataset.model_copy(update={"title": "different dataset copy"}, deep=True))
    conflicting = holder(certified_work / "conflicting", different, combined, profile=config.profile)
    assert required(pin, live=(carrier, conflicting), **args)
    assert "unresolved-copy" in " ".join(dependency_closure(write, (carrier, conflicting), observations=observations).unresolved)


@pytest.mark.parametrize("damage", ["missing", "malformed", "stale"])
def test_unknown_or_malformed_required_reference_blocks_retirement(certified_work, graph, damage):
    config, _, _, _, _, _, _, _ = graph
    assay = analysis_nodes(config.profile)[0]
    run = stored.run_node("local", title="local", spec="", reads=(assay.id,))
    write = holder(certified_work / "write", run, profile=config.profile)
    broken = assay.model_copy(deep=True)
    broken.facets["procedure"]["unexpected"] = "malformed"
    if damage == "malformed":
        broken = stored.stamp_semantic_identity(broken)
    carrier = holder(certified_work / "carrier", *((broken,) if damage != "missing" else ()), profile=config.profile)
    result = dependency_closure(write, (carrier,), observations={})
    assert assay.id in result.addresses and assay.id in " ".join(result.unresolved)
    pin = replace(held(1), corpus_id=carrier[0])
    assert required(pin, keep=(), group_chain=(pin,), tip=("p2", "m2"), mounted=(pin,), write_root=write, live=(carrier,), observations={})


@pytest.mark.parametrize("target_arm", ["observable", "scale-of"])
def test_proxy_in_another_holder_reaches_calibration_and_normative_references(certified_work, graph, target_arm):
    from fractions import Fraction
    from beliefs.proxy_model import Conversion, Crosswalk, Error, proxy_from_stored
    config, spec, _, _, basis, run, _, _ = graph
    nodes = normative_nodes(config, basis)
    proxy_node = next(n for n in nodes if n.kind == "proxy-model")
    target = stored.procedure_node(replace(procedure_from_stored(nodes[0]), name="other scale"))
    if target_arm == "scale-of":
        proxy_node = stored.proxy_model_node(replace(proxy_from_stored(proxy_node), target=ProxyTarget(None, target.id),
            crosswalk=Crosswalk({}, Conversion("multiplicative", Fraction(1), None), Error("exact", Fraction(0)))))
    write = holder(certified_work / "write", stored.run_node("local", title="local", spec="", reads=(proxy_node.id,)))
    middle = holder(certified_work / "middle", proxy_node, profile=config.profile)
    base = {n.id: n for n in ReadContext.open(config).write_view().iter_stored()}
    base.update({n.id: n for n in (*nodes, run, target) if n.kind != "proxy-model"})
    carrier = holder(certified_work / "carrier", *base.values(), profile=config.profile)
    result = dependency_closure(write, (middle, carrier), observations={})
    assert {nodes[0].id, nodes[-1].id, spec.id, run.id} <= result.addresses
    if target_arm == "scale-of":
        assert target.id in result.addresses
    assert result.unresolved == ()
