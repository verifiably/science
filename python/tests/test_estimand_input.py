"""Exact authoring encodings and closed native estimand member shapes."""
import copy
import json
from decimal import Decimal
from fractions import Fraction

import pytest

from beliefs.claim import Referent
from beliefs.errors import ScienceError
from beliefs.estimand import (
    AxisLevels, DatasetBinding, IncrementBinding, LagBinding, MeasuredBinding,
    NullReference, RoleAnchor, RoleBinding, RoleLevels, RoleTermLevels,
    RuleAnchor, RuleClassLevels, ValueReference,
)
from beliefs.measurement import measure_from_projection
from beliefs.restriction import IntervalRestriction
from science.refusal import Refused


@pytest.fixture
def source(tmp_path):
    from helpers.analysis import write_estimand_document
    from helpers.world import fixture_contract_document
    from science.config import load_config
    from test_config import write_config
    path = fixture_contract_document(tmp_path)
    cfg = load_config(write_config(tmp_path, domains='["general"]', contracts=f'["{path}"]'))
    path = write_estimand_document(cfg)
    return cfg.profile, path, json.loads(path.read_text())


def read(source, document=None, *, raw=None):
    from science.estimand_input import read_estimand_input
    profile, path, original = source
    path.write_text(raw if raw is not None else json.dumps(original if document is None else document))
    return read_estimand_input(path, profile=profile)


@pytest.mark.parametrize("token", ["0", "1", "0.5", "0.12345678901234567890123456789"])
def test_estimand_numeric_positions_preserve_exact_decimal(source, token):
    raw = json.dumps(source[2]).replace('"value": 0.5', f'"value": {token}')
    doc = read(source, raw=raw)
    assert type(doc.reference.value) is Decimal
    assert doc.reference.value == Decimal(token)


@pytest.mark.parametrize("value", [True, "0.5", None, [], {}])
def test_reference_requires_numeric_tokens(source, value):
    source[2]["reference"]["value"] = value
    with pytest.raises(Refused):
        read(source)


@pytest.mark.parametrize("value", [True, False, 0, 2, 1.0, "1"])
def test_version_is_exact_integer_one(source, value):
    source[2]["schema_version"] = value
    with pytest.raises(Refused):
        read(source)


@pytest.mark.parametrize("field", ["claim", "operator", "dependencies", "identity", "extra"])
def test_frozen_only_and_unknown_fields_refuse(source, field):
    source[2][field] = "forbidden"
    with pytest.raises(Refused):
        read(source)


@pytest.mark.parametrize("raw", ['{"schema_version": 1, "schema_version": 1}',
                                  '{"reference":{"kind":"value","value":0,"value":1}}',
                                  '{"value":NaN}', '{"value":Infinity}', '{"value":-Infinity}', '{'])
def test_duplicate_nonfinite_and_malformed_json_refuses(source, raw):
    with pytest.raises(Refused):
        read(source, raw=raw)


def test_unreadable_input_refuses(source):
    from science.estimand_input import read_estimand_input
    profile, path, _ = source
    path.write_bytes(b'\xff')
    with pytest.raises(Refused):
        read_estimand_input(path, profile=profile)
    path.unlink()
    with pytest.raises(Refused):
        read_estimand_input(path, profile=profile)


def test_null_and_named_output_references_are_exact(source):
    source[2]["reference"] = {"kind": "null", "region": {"low": 0, "high": 1}}
    assert read(source).reference == NullReference(Decimal(0), Decimal(1))
    source[2]["reference"] = {"beta": {"kind": "value", "value": 0}}
    assert read(source).reference == {"beta": ValueReference(Decimal(0))}


@pytest.mark.parametrize("case", ["role", "measured", "role-terms", "rule-classes", "roles",
                                  "axis", "increment", "rule-anchor", "role-anchor", "lag", "universe", "variables", "independent"])
def test_native_binding_arms(source, case):
    response = source[2]["bindings"]["response"]
    measure = measure_from_projection(response["measure"])
    ref = {"sort": "testing/level", "term": "level:early"}
    typed_ref = Referent("testing/level", "level:early")
    rule = "classification-rule:" + "a" * 64
    interval = {"unit": "testing/hour", "low": "0", "high": "1.25", "low_closed": True, "high_closed": False}
    typed_interval = IntervalRestriction("testing/hour", Fraction(0), Fraction(5, 4), True, False)
    bindings = {
        "role": ("membership", {"role": "response"}, RoleBinding("response", None)),
        "measured": ("response", response, MeasuredBinding("response", None, measure, None, None)),
        "role-terms": ("grouping", {"role": "intervention", "levels": {"source": "role-terms", "levels": [ref]}}, RoleTermLevels("intervention", None, (typed_ref,))),
        "rule-classes": ("grouping", {"rule": rule, "source": "rule-classes", "classes": [ref]}, RuleClassLevels(rule, (typed_ref,))),
        "roles": ("grouping", {"source": "roles", "roles": [response, response]}, RoleLevels((MeasuredBinding("response", None, measure, None, None),) * 2)),
        "axis": ("grouping", {"source": "axis", "levels": [interval]}, AxisLevels((typed_interval,))),
        "increment": ("grouping", {"role": "response", "measure": response["measure"], "increment": {"value": 1, "unit": "testing/hour"}}, IncrementBinding("response", None, measure, Decimal(1), "testing/hour")),
        "rule-anchor": ("anchor", {"rule": rule, "classes": [ref]}, RuleAnchor(rule, (typed_ref,))),
        "role-anchor": ("anchor", {"role": "response", "category": ref}, RoleAnchor("response", None, typed_ref)),
        "lag": ("lag", {"unit": "testing/hour", "windows": [interval]}, LagBinding("testing/hour", (typed_interval,))),
        "universe": ("universe", {"digest": "sha256:" + "b" * 64}, DatasetBinding("sha256:" + "b" * 64)),
        "variables": ("variables", [{"name": "x", "binding": response}], (("x", MeasuredBinding("response", None, measure, None, None)),)),
        "independent": ("independent", [{"name": "x", "binding": response}], (("x", MeasuredBinding("response", None, measure, None, None)),)),
    }
    variable, raw, expected = bindings[case]
    source[2]["bindings"] = {variable: raw}
    assert read(source).bindings[variable] == expected


def test_nested_unknown_fields_and_nonstring_referents_refuse(source):
    document = copy.deepcopy(source[2])
    document["bindings"]["response"]["surprise"] = True
    with pytest.raises(Refused):
        read(source, document)
    source[2]["control"]["conditioning"] = [{"sort": "testing/concept", "term": 2}]
    with pytest.raises(Refused):
        read(source)


def test_restriction_reader_keeps_native_string_bounds(source):
    source[2]["bindings"] = {"grouping": {"source": "axis", "levels": [
        {"unit": "testing/hour", "low": 1.25, "low_closed": True, "high_closed": False}]}}
    with pytest.raises(ScienceError):
        read(source)


def test_named_output_reference_can_be_named_kind(source):
    source[2]["reference"] = {"kind": {"kind": "value", "value": 0}}
    assert read(source).reference == {"kind": ValueReference(Decimal(0))}
