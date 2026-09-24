import re

import pytest

from helpers.world import QUERY, coordination_rig
from science.refusal import Refused

ADDRESS = re.compile(r"\[project\] project:([0-9a-f]{32})\.([0-9a-f]{32})")


def test_project_genesis_needs_no_selection(certified_work):
    """P2's genesis arm: a fresh world's first act."""
    with coordination_rig(certified_work, ("project",)) as (d, ctx):
        out = d.invoke("project", {"name": "health", "query": QUERY})
        project, revision = ADDRESS.search(out.text).groups()
        from beliefs.coordination import CoordinationAddress
        node = ctx.coordination().resolve(CoordinationAddress(project))
    assert node.title == "health" and node.uid == revision
    assert node.facets["coordination"]["query"]["clauses"][0]["all"][0]["kinds"] == ["proposition"]


def test_project_accepts_a_json_query(certified_work):
    with coordination_rig(certified_work, ("project",)) as (d, _):
        out = d.invoke("project", {"name": "j", "query": '{"version": "science.view-query.v1", "clauses": []}'})
    assert ADDRESS.search(out.text)


@pytest.mark.parametrize("query", ["- a\n", "3", ""])
def test_a_query_that_is_not_a_mapping_refuses_before_any_act_and_replays(certified_work, query):
    with coordination_rig(certified_work, ("project",)) as (d, _):
        for _ in range(2):
            with pytest.raises(Refused) as caught:
                d.invoke("project", {"name": "bad", "query": query}, invocation_id="Q" * 8)
            assert caught.value.refusal.code == "invalid-input"


def test_a_query_the_kernel_rejects_is_kernel_refused(certified_work):
    bad = "version: science.view-query.v1\nclauses:\n  - all:\n      - kinds: [task]\n"
    with coordination_rig(certified_work, ("project",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("project", {"name": "bad", "query": bad})
    assert caught.value.refusal.code == "kernel-refused"
