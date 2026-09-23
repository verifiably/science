import pytest

from science.refusal import Refused
from helpers.world import build_fixture_world_with_contract, open_rig

BASE = {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
        "layer": "causal", "polarity": "positive"}


def test_claim_types_under_the_plan_and_mints(certified_work):
    with open_rig(build_fixture_world_with_contract(certified_work), ("claim",)) as (d, ctx):
        out = d.invoke("claim", dict(BASE))
        assert "[proposition] proposition:concept-disease-stage-affects-protein-phf19" in out.text
        _, view = ctx.single_view()
        node = view.get("proposition:concept-disease-stage-affects-protein-phf19")
        assert node.facets["proposition"]["operator"] == "testing/affects-concept-protein"


def test_shape_with_no_plan_row_refuses_naming_it(certified_work):
    with open_rig(build_fixture_world_with_contract(certified_work), ("claim",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("claim", dict(BASE, subject="protein:PHF19", object="concept:disease-stage"))
        assert caught.value.refusal.code == "invalid-input"
        assert "affects protein->concept" in caught.value.refusal.message


def test_non_member_under_the_dataset_bound_sort_refuses(certified_work):
    with open_rig(build_fixture_world_with_contract(certified_work), ("claim",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("claim", dict(BASE, subject="concept:not-in-the-list"))
        assert caught.value.refusal.code == "invalid-input"
        assert "not-member" in caught.value.refusal.message


def test_unheld_vocabulary_under_the_dataset_bound_sort_refuses_naming_the_address(certified_work):
    cfg = build_fixture_world_with_contract(certified_work, hold_concepts=False)
    with open_rig(cfg, ("claim",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("claim", dict(BASE))
        assert "dataset:sha256:" in caught.value.refusal.message
        assert "hold" in caught.value.refusal.message


def test_namespace_bound_sort_resolves_not_consulted_and_is_accepted(certified_work):
    """The protein slot is HGNC-bound by namespace and release; no release is
    held; the kernel's permissive reading stands (design §4.1)."""
    with open_rig(build_fixture_world_with_contract(certified_work), ("claim",)) as (d, _):
        out = d.invoke("claim", dict(BASE, object="protein:ANYTHING", slug="any"))
        assert "proposition:any" in out.text


def test_claim_performs_exactly_its_declared_reads(certified_work):
    """N2's shape: the declaration's families are what the handler touches."""
    from science.loader import production_tree
    decl = next(d for d in production_tree() if d.name == "claim")
    assert set(decl.reads) == {"corpus-stored", "holdings"}
