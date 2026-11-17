"""Topics are complete syntheses with resolving view references."""
from dataclasses import replace
import json

import pytest

from beliefs.coordination import CoordinationAddress
from helpers.research import add_source, research_rig
from helpers.world import build_two_corpus_world, mint_project
from science.refusal import Refused

NAMES = ("topic", "project", "project-select")


def query(*predicates):
    return json.dumps({"version": "science.view-query.v1", "clauses": [{"all": list(predicates)}]})


def selected(d):
    project = mint_project(d)
    d.invoke("project-select", {"target": str(project)})
    return project


def test_without_a_selection_refuses(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("topic", {"name": "Methods", "body": "Synthesis", "query": query({"kinds": ["proposition"]})})
        assert caught.value.refusal.code == "no-current-project"


def test_without_coordination_refuses(certified_work):
    cfg = replace(build_two_corpus_world(certified_work), coordination=None)
    with research_rig(cfg, NAMES) as (d, ctx):
        d._selection = CoordinationAddress.parse("coord:" + "a" * 32)
        with pytest.raises(Refused) as expected:
            ctx.coordination()
        with pytest.raises(Refused) as caught:
            d.invoke("topic", {"name": "Methods", "body": "Synthesis", "query": query({"kinds": ["proposition"]})})
        assert caught.value.refusal.code == expected.value.refusal.code


def test_a_topic_is_minted(certified_work):
    cfg = build_two_corpus_world(certified_work)
    source = add_source(cfg, "archive", "A method", doi="10.1234/method")
    with research_rig(cfg, NAMES) as (d, ctx):
        project = selected(d)
        out = d.invoke("topic", {"name": "Methods", "body": "A grounded synthesis", "query": query({"addresses": [source.id]})})
        assert out.text.startswith(f"[topic] topic:{project.project}.")
        (node,) = ctx.coordination().standing("topic").values()
        assert node.title == "Methods" and node.body == "A grounded synthesis"
        assert node.facets["coordination"]["query"]["clauses"][0]["all"] == [{"addresses": [source.id]}]


@pytest.mark.parametrize("body", ["", " \n "])
def test_a_blank_body_refuses(certified_work, body):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, ctx):
        selected(d)
        with pytest.raises(Refused) as caught:
            d.invoke("topic", {"name": "Methods", "body": body, "query": query({"addresses": ["proposition:archived"]})})
        assert caught.value.refusal.code == "invalid-input"
        assert caught.value.refusal.data == {"field": "body"}
        assert not ctx.coordination().standing("topic")


def test_a_query_without_addresses_refuses(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, ctx):
        selected(d)
        with pytest.raises(Refused) as caught:
            d.invoke("topic", {"name": "Methods", "body": "Synthesis", "query": query({"kinds": ["proposition"]})})
        assert caught.value.refusal.code == "invalid-input"
        assert caught.value.refusal.data == {"reason": "no-addresses"}
        assert not ctx.coordination().standing("topic")


@pytest.mark.parametrize("predicates, missing", [
    (({"addresses": ["source:missing", "proposition:missing"]},), ["proposition:missing", "source:missing"]),
    (({"addresses": ["proposition:archived"]}, {"closure": {"anchor": "proposition:missing", "predicates": ["anchored_in"], "direction": "out"}}), ["proposition:missing"]),
])
def test_an_unresolved_address_refuses(certified_work, predicates, missing):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, ctx):
        selected(d)
        with pytest.raises(Refused) as caught:
            d.invoke("topic", {"name": "Methods", "body": "Synthesis", "query": query(*predicates)})
        assert caught.value.refusal.code == "invalid-input"
        assert caught.value.refusal.data == {"unresolved": missing}
        assert not ctx.coordination().standing("topic")


@pytest.mark.parametrize("value, code", [("[]", "invalid-input"), ('{"version":"wrong"}', "kernel-refused")])
def test_a_malformed_query_refuses(certified_work, value, code):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, ctx):
        selected(d)
        with pytest.raises(Refused) as caught:
            d.invoke("topic", {"name": "Methods", "body": "Synthesis", "query": value})
        assert caught.value.refusal.code == code
        assert not ctx.coordination().standing("topic")
