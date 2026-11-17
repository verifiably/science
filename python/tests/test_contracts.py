from pathlib import Path

import pytest

from science.contracts import OperatorPlan, load_contract_document
from science.refusal import Refused


DOCUMENT = '''\
contract:
  contract: testing
  version: 1
  lineage: genesis
  sorts:
    concept:
      binding: {kind: dataset, dataset: "dataset:sha256:%s"}
      identifier_class: {prefix: concept, pattern: 'concept:.+'}
  dimensions: {}
  templates:
    affects-concept-concept:
      roles: {intervention: {arity: one}, response: {arity: one}}
      sign_apt: true
      layers: [causal]
      forms: [polar]
    binds-concept-concept:
      roles: {intervention: {arity: one}, response: {arity: one}}
      sign_apt: false
      layers: [causal]
      forms: [polar]
  instantiations:
    affects-pair:
      template: affects-concept-concept
      roles: {intervention: [concept], response: [concept]}
    binds-pair:
      template: binds-concept-concept
      roles: {intervention: [concept], response: [concept]}
plan:
  sorts: {concept: concept}
  layers: {causal: causal}
  polarities: {positive: positive, negative: negative, not_applicable: null}
  operators:
    - {predicate: affects, subject: concept, object: concept, operator: affects-concept-concept, roles: {subject: intervention, object: response}}
    - {predicate: binds, subject: concept, object: concept, operator: binds-concept-concept, roles: {subject: intervention, object: response}}
'''


def write_document(tmp_path: Path, text: str = DOCUMENT % ("0" * 64)) -> Path:
    path = tmp_path / "testing.yaml"
    path.write_text(text)
    return path


def test_document_parses_to_a_contract_and_a_plan(tmp_path):
    from beliefs.profile import shipped_base_contract

    contract, plan = load_contract_document(write_document(tmp_path), shipped_base_contract())
    assert contract.namespace == "testing"
    assert isinstance(plan, OperatorPlan)
    assert plan.row_for("affects", "concept", "concept").operator == "testing/affects-concept-concept"
    assert plan.sort_for("concept") == "testing/concept"
    assert plan.layers["causal"] == "causal"


def test_plan_refuses_a_shape_with_no_row(tmp_path):
    from beliefs.profile import shipped_base_contract

    _, plan = load_contract_document(write_document(tmp_path), shipped_base_contract())
    with pytest.raises(Refused) as caught:
        plan.row_for("affects", "concept", "protein")
    assert caught.value.refusal.code == "invalid-input"
    assert "affects concept->protein" in caught.value.refusal.message


def test_plan_preserves_a_null_polarity_for_sign_inapt_operators(tmp_path):
    """A null plan value reaches build_claim as None for sign-inapt operators."""
    from beliefs.profile import shipped_base_contract

    _, plan = load_contract_document(write_document(tmp_path), shipped_base_contract())
    assert "not_applicable" in plan.polarities
    assert plan.polarities["not_applicable"] is None
    assert plan.row_for("binds", "concept", "concept").operator == "testing/binds-concept-concept"


def test_document_without_a_plan_yields_none(tmp_path):
    from beliefs.profile import shipped_base_contract

    text = (DOCUMENT % ("0" * 64)).split("plan:")[0]
    _, plan = load_contract_document(write_document(tmp_path, text), shipped_base_contract())
    assert plan is None


def test_malformed_document_refuses(tmp_path):
    from beliefs.profile import shipped_base_contract

    with pytest.raises(Refused) as caught:
        load_contract_document(
            write_document(tmp_path, "contract: [not a table]\n"), shipped_base_contract()
        )
    assert caught.value.refusal.code == "invalid-input"


@pytest.mark.parametrize("key", ["also", "plans"])
def test_unknown_top_level_key_refuses(tmp_path, key):
    """A document outside {contract, plan} refuses, naming the key: a misspelled
    `plan` would otherwise load with no plan and surface only at claim."""
    from beliefs.profile import shipped_base_contract

    text = DOCUMENT % ("0" * 64) + f"{key}: [biology]\n"
    with pytest.raises(Refused) as caught:
        load_contract_document(write_document(tmp_path, text), shipped_base_contract())
    assert caught.value.refusal.code == "invalid-input"
    assert repr(key) in caught.value.refusal.message


@pytest.mark.parametrize(
    "plan",
    [
        "[]",
        "{operators: false}",
        "{sorts: false}",
        "{layers: []}",
        "{polarities: false}",
        "{operators: [false]}",
        "{operators: [{predicate: 3, operator: affects-concept-concept, roles: {subject: intervention, object: response}}]}",
        "{operators: [{predicate: affects, subject: [], operator: affects-concept-concept, roles: {subject: intervention, object: response}}]}",
        "{operators: [{predicate: affects, object: 3, operator: affects-concept-concept, roles: {subject: intervention, object: response}}]}",
        "{operators: [{predicate: affects, operator: false}]}",
        "{sorts: {concept: 3}}",
        "{layers: {causal: false}}",
        "{polarities: {positive: 3}}",
    ],
)
def test_malformed_plan_shapes_refuse_at_load(tmp_path, plan):
    from beliefs.profile import shipped_base_contract

    text = (DOCUMENT % ("0" * 64)).split("plan:")[0] + f"plan: {plan}\n"
    with pytest.raises(Refused) as caught:
        load_contract_document(write_document(tmp_path, text), shipped_base_contract())
    assert caught.value.refusal.code == "invalid-input"


def test_plan_supports_a_predicate_wildcard_row(tmp_path):
    from beliefs.profile import shipped_base_contract

    text = (DOCUMENT % ("0" * 64)).replace(
        "    - {predicate: affects, subject: concept, object: concept, operator: affects-concept-concept, roles: {subject: intervention, object: response}}",
        "    - {predicate: affects, operator: affects-concept-concept, roles: {subject: intervention, object: response}}",
    )
    _, plan = load_contract_document(write_document(tmp_path, text), shipped_base_contract())
    assert plan.row_for("affects", "protein", "dataset").operator == "testing/affects-concept-concept"


def test_plan_rows_have_explicit_roles(tmp_path):
    from beliefs.profile import shipped_base_contract
    _, plan = load_contract_document(write_document(tmp_path), shipped_base_contract())
    row = plan.row_for("affects", "concept", "concept")
    assert row.roles == {"subject": "intervention", "object": "response"}


@pytest.mark.parametrize("roles", [None, {}, {"subject": "intervention"},
                                   {"subject": 1, "object": "response"},
                                   {"subject": "intervention", "object": "response", "extra": "x"}])
def test_plan_roles_are_required_and_closed(tmp_path, roles):
    import yaml
    from beliefs.profile import shipped_base_contract
    doc = yaml.safe_load(DOCUMENT % ("0" * 64))
    row = doc["plan"]["operators"][0]
    if roles is None:
        row.pop("roles", None)
    else:
        row["roles"] = roles
    with pytest.raises(Refused):
        load_contract_document(write_document(tmp_path, yaml.safe_dump(doc)), shipped_base_contract())


def test_exact_row_precedes_wildcard(tmp_path):
    import yaml
    from beliefs.profile import shipped_base_contract
    doc = yaml.safe_load(DOCUMENT % ("0" * 64))
    doc["plan"]["operators"].append({"predicate": "affects", "operator": "binds-concept-concept",
                                        "roles": {"subject": "intervention", "object": "response"}})
    _, plan = load_contract_document(write_document(tmp_path, yaml.safe_dump(doc)), shipped_base_contract())
    assert plan.row_for("affects", "concept", "concept").operator == "testing/affects-concept-concept"
    assert plan.row_for("affects", "protein", "concept").operator == "testing/binds-concept-concept"


def test_analysis_prerequisites_are_real_held_records(certified_work):
    import json
    from helpers.analysis import analysis_nodes, bootstrap_analysis, write_estimand_document
    from helpers.world import build_fixture_world_with_contract
    from science.config import ReadContext
    cfg = build_fixture_world_with_contract(certified_work)
    bootstrap_analysis(cfg)
    nodes = analysis_nodes(cfg.profile)
    assert nodes == analysis_nodes(cfg.profile)
    assert [node.kind for node in nodes] == ["procedure", "classification-rule", "procedure"]
    view = ReadContext.open(cfg).write_view()
    assert all(view.holds(node.id) for node in nodes)
    document = json.loads(write_estimand_document(cfg).read_text())
    assert document["bindings"]["grouping"]["source"] == "rule-classes"
    assert document["reference"] == {"kind": "value", "value": 0.5}
