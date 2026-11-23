"""Static acquisition inputs must be sealable before the set is published."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from science.acquisition.plan import parse_plan
from science.refusal import Refused


FIXTURE = Path(__file__).parents[1] / "fixtures" / "acquisition" / "quarry-geo.json"


def test_quarry_plan_preserves_input_and_seed_order():
    raw = FIXTURE.read_bytes()
    plan = parse_plan(raw, max_requests=2)
    assert plan.source == json.loads(raw)
    assert [seed.name for seed in plan.seeds] == [r["name"] for r in plan.source["resources"]]


def test_static_seeds_keep_native_parameters_and_exact_service_interval():
    raw = b'''{"title":"t","locator":"instrument:i","resource":"example","native":"q",
    "parameters":{"cut":0.123456789123456789},"politeness":{"example.org":0.25},
    "seeds":[{"member":"dir/a","url":"HTTPS://EXAMPLE.ORG/path","expected":"sha256:DIGEST"}]}'''
    plan = parse_plan(raw.replace(b"DIGEST", b"f" * 64), max_requests=1)
    assert plan.source["parameters"]["cut"] == Decimal("0.123456789123456789")
    assert plan.source["native"] == "q"
    assert plan.intervals == {"example.org": Decimal("0.25")}
    assert plan.seeds[0].url.url == "https://example.org/path"
    assert plan.seeds[0].expected == "sha256:" + "f" * 64


@pytest.mark.parametrize("changes", [
    {"seeds": []}, {"traversal": "next"}, {"max_response_bytes": 10},
    {"title": ""}, {"locator": "bad:id"}, {"resources": []},
])
def test_refuses_invalid_top_level(changes):
    source = json.loads(FIXTURE.read_bytes()) | changes
    with pytest.raises(Refused):
        parse_plan(json.dumps(source).encode(), max_requests=2)


@pytest.mark.parametrize(("names", "url", "expected"), [
    (["a", "a"], "https://host/x", None), (["a/b", "a"], "https://host/x", None),
    (["../a"], "https://host/x", None), (["e\u0301"], "https://host/x", None),
    (["a"], "http://host/x", None), (["a"], "https://u@host/x", None),
    (["a"], "https://host/x", "sha256:bad"),
])
def test_refuses_unsealable_seeds(names, url, expected):
    rows = [{"name": name, "url": url} for name in names]
    if expected is not None:
        rows[0]["expected"] = expected
    raw = json.dumps({"resources": rows, "locator": "accession:x", "title": "t"}).encode()
    with pytest.raises(Refused):
        parse_plan(raw, max_requests=2)


def test_refused_member_is_named_without_contact():
    source = json.loads(FIXTURE.read_bytes())
    second = source["resources"][1]
    second["url"] = second["url"].replace("https:", "http:")
    with pytest.raises(Refused, match=second["name"]):
        parse_plan(json.dumps(source).encode(), max_requests=2)


def test_rejects_duplicate_keys_and_oversize_plan():
    with pytest.raises(Refused, match="duplicate"):
        parse_plan(b'{"title":1,"title":2}', max_requests=1)
    with pytest.raises(Refused, match="max_requests"):
        parse_plan(FIXTURE.read_bytes(), max_requests=1)
