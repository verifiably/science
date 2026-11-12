import pytest

from science.refusal import Refused
from helpers.world import build_fixture_world_with_contract, open_rig

BASE = {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
        "layer": "causal", "polarity": "positive"}


def test_claim_types_under_the_plan_and_mints(certified_work):
    with open_rig(build_fixture_world_with_contract(certified_work), ("claim",)) as (d, ctx):
        out = d.invoke("claim", dict(BASE))
        assert "[proposition] proposition:concept-disease-stage-affects-protein-phf19" in out.text
        view = ctx.write_view()
        node = view.get("proposition:concept-disease-stage-affects-protein-phf19")
        assert node.facets["proposition"]["operator"] == "general/changes-under-intervention"


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
    held; the kernel's permissive reading stands."""
    with open_rig(build_fixture_world_with_contract(certified_work), ("claim",)) as (d, _):
        out = d.invoke("claim", dict(BASE, object="protein:ANYTHING", slug="any"))
        assert "proposition:any" in out.text


def test_claim_performs_exactly_its_declared_reads(certified_work):
    """N2's shape: the declaration's families are what the handler touches."""
    from science.loader import production_tree
    decl = next(d for d in production_tree() if d.name == "claim")
    assert set(decl.reads) == {"corpus-stored", "holdings"}


def _extended_contract(monkeypatch):
    import yaml
    import helpers.world as world
    from helpers.world import _list_address
    proteins = b"protein:PHF19\n"
    doc = yaml.safe_load(world.TEST_CONTRACT)
    doc["contract"]["sorts"]["protein"]["binding"] = {"kind": "dataset", "dataset": _list_address(proteins, "proteins.txt")}
    doc["contract"]["instantiations"]["covaries-pair"] = {
        "template": "general/covaries-with", "roles": {"parties": ["concept", "protein"]}}
    doc["contract"]["templates"] = {"binds": {
        "roles": {"intervention": {"arity": "one"}, "response": {"arity": "one"}},
        "sign_apt": False, "forms": ["polar"], "layers": ["causal"]}}
    doc["contract"]["instantiations"]["binds-pair"] = {
        "template": "binds", "roles": {"intervention": ["concept"], "response": ["protein"]}}
    doc["plan"]["layers"]["statistical"] = "statistical"
    doc["plan"]["operators"] += [
        {"predicate": "covaries", "operator": "general/covaries-with", "roles": {"subject": "parties", "object": "parties"}},
        {"predicate": "binds", "operator": "binds", "roles": {"subject": "intervention", "object": "response"}}]
    monkeypatch.setattr(world, "TEST_CONTRACT", yaml.safe_dump(doc))
    return proteins


def test_many_role_receipt_checks_canonical_member_sort(certified_work, monkeypatch):
    from helpers.world import hold_fixture_dataset, concept_list_address
    proteins = _extended_contract(monkeypatch)
    cfg = build_fixture_world_with_contract(certified_work, hold_concepts=False)
    hold_fixture_dataset(cfg, "proteins.txt", proteins, "proteins")
    with open_rig(cfg, ("claim",)) as (d, ctx):
        with pytest.raises(Refused) as caught:
            d.invoke("claim", dict(BASE, subject="protein:PHF19", object="concept:disease-stage",
                                   predicate="covaries", layer="statistical"))
        assert concept_list_address() in caught.value.refusal.message
        assert not [n for n in ctx.write_view().iter_stored() if n.kind == "proposition"]


def test_many_role_canonical_identity_and_duplicate_refusal(certified_work, monkeypatch):
    from helpers.world import hold_fixture_dataset
    proteins = _extended_contract(monkeypatch)
    cfg = build_fixture_world_with_contract(certified_work)
    hold_fixture_dataset(cfg, "proteins.txt", proteins, "proteins")
    with open_rig(cfg, ("claim",)) as (d, ctx):
        d.invoke("claim", dict(BASE, predicate="covaries", layer="statistical", slug="forward"))
        d.invoke("claim", dict(BASE, predicate="covaries", layer="statistical", slug="reverse",
                               subject=BASE["object"], object=BASE["subject"]))
        view = ctx.write_view()
        assert view.get("proposition:forward").facets["proposition"] == view.get("proposition:reverse").facets["proposition"]
        with pytest.raises(Refused):
            d.invoke("claim", dict(BASE, predicate="covaries", layer="statistical", object=BASE["subject"]))


def test_sign_inapt_builds_none_and_decodes_native_wire_tag(certified_work, monkeypatch):
    from helpers.world import hold_fixture_dataset
    proteins = _extended_contract(monkeypatch)
    cfg = build_fixture_world_with_contract(certified_work)
    hold_fixture_dataset(cfg, "proteins.txt", proteins, "proteins")
    with open_rig(cfg, ("claim",)) as (d, ctx):
        d.invoke("claim", dict(BASE, predicate="binds", polarity="not_applicable", slug="bound"))
        assert ctx.write_view().get("proposition:bound").facets["proposition"]["polarity"] == "inapt"


@pytest.mark.parametrize("roles", [
    {"source": {"arity": "many", "min": 1}, "response": {"arity": "one"}},
    {"source": {"arity": "many", "min": 3}},
    {"source": {"arity": "one"}},
])
def test_unsupported_binary_role_shapes_refuse(roles):
    from beliefs.profile import compile_profile, shipped_base_contract
    from beliefs.contract.domain import parse_domain_contract
    from science.contracts import OperatorPlan, PlanRow, validate_plan
    base = shipped_base_contract()
    contract = parse_domain_contract({"contract": "shape", "version": 1, "lineage": "genesis",
        "sorts": {}, "dimensions": {}, "templates": {"binary": {"roles": roles,
            "sign_apt": True, "layers": ["causal"], "forms": ["polar"]}}},
        source="<test>", base=base, predecessor=None)
    profile = compile_profile(base, [contract])
    plan = OperatorPlan("shape", {("p", None, None): PlanRow("shape/binary",
        {"subject": "source", "object": "response" if "response" in roles else "source"})}, {}, {}, {})
    with pytest.raises(Refused, match="roles"):
        validate_plan(plan, profile)


def test_world_kind_missing_member_prevents_mint(certified_work, monkeypatch):
    import yaml
    import helpers.world as world
    doc = yaml.safe_load(world.TEST_CONTRACT)
    doc["contract"]["sorts"]["witness"] = {"binding": {"kind": "world-kind", "world_kind": "procedure"}}
    doc["contract"]["instantiations"]["procedure-response"] = {
        "template": "general/changes-under-intervention", "roles": {"intervention": ["witness"], "response": ["protein"]}}
    doc["plan"]["sorts"]["procedure"] = "witness"
    doc["plan"]["operators"].append({"predicate": "affects", "subject": "procedure", "object": "protein",
        "operator": "general/changes-under-intervention", "roles": {"subject": "intervention", "object": "response"}})
    monkeypatch.setattr(world, "TEST_CONTRACT", yaml.safe_dump(doc))
    with open_rig(build_fixture_world_with_contract(certified_work), ("claim",)) as (d, ctx):
        with pytest.raises(Refused, match="not-member"):
            d.invoke("claim", dict(BASE, subject="procedure:" + "a" * 64))
        assert not [n for n in ctx.write_view().iter_stored() if n.kind == "proposition"]
