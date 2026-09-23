from decimal import Decimal

import pytest

from science.refusal import Refused
from helpers.world import (SPEC_FIELDS as FIELDS, build_belief_world, build_fixture_world_with_contract,
                           hold_fixture_dataset, level_list_address, open_rig)


@pytest.fixture
def rig(certified_work):
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec",)) as (d, ctx):
        yield d, ctx, ref


def _specs(ctx):
    _, view = ctx.single_view()
    return [n for n in view.iter_stored() if n.kind == "analysis-spec"]


def test_spec_freezes_a_typed_estimand_and_the_record_id_is_the_identity(rig):
    d, ctx, ref = rig
    out = d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset=ref, parameters=["alpha=0.05"]))
    assert "[analysis-spec] analysis-spec:" in out.text
    from beliefs import stored
    (node,) = _specs(ctx)
    spec = stored.analysis_spec_value(node, profile=ctx.config.profile)
    assert node.id == f"analysis-spec:{spec.identity}"
    assert spec.parameters["alpha"] == Decimal("0.05")
    assert spec.nondeterminism.projection() == {"variant": "deterministic"}
    assert spec.estimand.measure.scale == "additive"
    assert spec.estimand.contrast.baseline.term == "level:early"
    assert dict(spec.applicability) == {}


def test_namespace_bound_estimand_sorts_resolve_not_consulted_and_stand(rig):
    """measure and identification are namespace-bound and not held: the
    kernel's permissive reading stands, as for claim's protein slot."""
    d, ctx, ref = rig
    d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset=ref, measure="measure:anything"))
    assert len(_specs(ctx)) == 1


def test_unheld_level_vocabulary_refuses_naming_its_address_and_mints_nothing(certified_work):
    cfg = build_fixture_world_with_contract(certified_work, hold_levels=False)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("claim", "spec")) as (d, ctx):
        prop = next(t for t in d.invoke("claim", {"subject": "concept:disease-stage", "predicate": "affects",
                                                  "object": "protein:PHF19", "layer": "causal",
                                                  "polarity": "positive"}).text.split()
                    if t.startswith("proposition:"))
        with pytest.raises(Refused) as caught:
            d.invoke("spec", dict(FIELDS, target=prop, dataset=ref))
        assert caught.value.refusal.code == "invalid-input"
        assert level_list_address() in caught.value.refusal.message
        assert "hold it with `dataset`" in caught.value.refusal.message
        assert _specs(ctx) == []


def test_non_member_level_refuses(rig):
    d, ctx, ref = rig
    with pytest.raises(Refused) as caught:
        d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset=ref, comparison="level:never"))
    assert caught.value.refusal.code == "invalid-input"
    assert _specs(ctx) == []


@pytest.mark.parametrize("change", [
    {"quantity": "measure:tpm"},                      # a continuous input on a levels contrast
    {"comparison": None},                             # a levels input missing
    {"contrast": "continuous"},                       # continuous with levels inputs and no quantity
])
def test_contrast_inputs_must_match_the_contrast_kind(rig, change):
    d, ctx, ref = rig
    inputs = {k: v for k, v in dict(FIELDS, target="proposition:p1", dataset=ref, **change).items() if v is not None}
    with pytest.raises(Refused) as caught:
        d.invoke("spec", inputs)
    assert caught.value.refusal.code == "invalid-input"
    assert _specs(ctx) == []


def test_reference_must_be_a_finite_decimal(rig):
    d, _, ref = rig
    for bad in ("zero", "NaN", "Infinity"):
        with pytest.raises(Refused) as caught:
            d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset=ref, reference=bad))
        assert caught.value.refusal.code == "invalid-input"


def test_applicability_qualifier_is_typed_and_accepted(rig):
    d, ctx, ref = rig
    d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset=ref,
                          applicability=["testing/scope=generic:cohort:adults"]))
    from beliefs import stored
    (node,) = _specs(ctx)
    spec = stored.analysis_spec_value(node, profile=ctx.config.profile)
    assert spec.applicability["testing/scope"].quantifier == "generic"


@pytest.mark.parametrize("entry", [
    "testing/scope=most:cohort:adults",               # UnknownQuantifier (a ClaimError)
    "testing/setting=generic:cohort:adults",          # UndeclaredDimension: declared, not on this operator
    "testing/nope=generic:cohort:adults",             # no such dimension in the profile (surface refusal)
])
def test_applicability_authoring_errors_refuse_and_replay_exactly(rig, entry):
    """Not ESTIMAND_ERRORS: build_applicability raises the claim grammar's
    ClaimError subclasses. Escaping the handler would leave the invocation
    open and a retry would read outcome-unknown (design §4.3)."""
    d, ctx, ref = rig
    inputs = dict(FIELDS, target="proposition:p1", dataset=ref, applicability=[entry])
    with pytest.raises(Refused) as first:
        d.invoke("spec", inputs, invocation_id="Q" * 8)
    with pytest.raises(Refused) as again:
        d.invoke("spec", inputs, invocation_id="Q" * 8)
    assert first.value.refusal.code == "invalid-input"
    assert again.value.refusal == first.value.refusal
    assert _specs(ctx) == []


def test_malformed_applicability_entry_refuses(rig):
    d, _, ref = rig
    with pytest.raises(Refused) as caught:
        d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset=ref, applicability=["scope"]))
    assert "dimension=quantifier:term" in caught.value.refusal.message


def test_scale_choices_are_the_kernel_scales():
    from beliefs.estimand import SUPPORTED_SCALES
    from science.loader import production_tree
    decl = next(d for d in production_tree() if d.name == "spec")
    (scale,) = [i for i in decl.inputs if i.name == "scale"]
    assert tuple(scale.choices) == tuple(SUPPORTED_SCALES)


def test_unknown_rule_identity_refuses(rig):
    d, _, ref = rig
    with pytest.raises(Refused) as caught:
        d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset=ref, interpretation_rule="nope/v9"))
    assert caught.value.refusal.code == "invalid-input"
    assert "nope/v9" in caught.value.refusal.message


def test_unknown_dataset_ref_refuses(rig):
    d, _, _ = rig
    with pytest.raises(Refused) as caught:
        d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset="dataset:sha256:" + "0" * 64))
    assert caught.value.refusal.code == "invalid-input"


def test_malformed_parameter_refuses(rig):
    d, _, ref = rig
    with pytest.raises(Refused) as caught:
        d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset=ref, parameters=["alpha"]))
    assert "name=value" in caught.value.refusal.message
