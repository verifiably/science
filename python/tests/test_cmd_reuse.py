import re

import pytest

from helpers.world import QUERY, coordination_rig, mint_project
from science.refusal import Refused

NAMES = ("project", "question", "task", "decide", "reuse")
LOCAL = re.compile(r"\[(\w+)\] \w+:([0-9a-f]{32})\.([0-9a-f]{32})\.([0-9a-f]{32})")


def test_reuse_copies_the_query_into_the_current_project_and_leaves_the_source(certified_work):
    """P4."""
    from beliefs.coordination import CoordinationAddress
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        myeloma, health = mint_project(d, "multiple-myeloma"), mint_project(d, "health")
        d._selection = myeloma
        kind, project, local, revision = LOCAL.search(
            d.invoke("question", {"name": "PHF19 and stage", "query": QUERY, "body": "why"}).text).groups()
        source = CoordinationAddress(project, local)
        before = ctx.coordination().resolve(source)
        d._selection = health
        copied = LOCAL.search(d.invoke("reuse", {"source": str(source)}).text).groups()
        after = ctx.coordination().resolve(source)
        copy = ctx.coordination().resolve(CoordinationAddress(copied[1], copied[2]))
    assert copied[0] == "question" and copied[1] == health.project
    assert copy.facets["coordination"]["query"] == before.facets["coordination"]["query"]
    assert copy.title == "PHF19 and stage"
    assert copy.body.startswith(f"Same query as {source}@{revision}.\n\nwhy")
    assert after.uid == before.uid  # the source is untouched


def test_reuse_takes_a_new_name(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        d._selection = mint_project(d)
        _, project, local, _ = LOCAL.search(d.invoke("question", {"name": "q", "query": QUERY}).text).groups()
        out = d.invoke("reuse", {"source": f"coord:{project}/{local}", "name": "renamed"})
    assert "renamed" in out.text


def test_reuse_needs_a_selection(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        d._selection = mint_project(d)
        _, project, local, _ = LOCAL.search(d.invoke("question", {"name": "q", "query": QUERY}).text).groups()
        d._selection = None
        with pytest.raises(Refused) as caught:
            d.invoke("reuse", {"source": f"coord:{project}/{local}"})
    assert caught.value.refusal.code == "no-current-project"


@pytest.mark.parametrize("make", ["task", "decision", "project"])
def test_reuse_of_a_non_view_or_a_project_refuses(certified_work, make):
    with coordination_rig(certified_work, NAMES) as (d, _):
        project = mint_project(d)
        d._selection = project
        if make == "task":
            _, p, local, _ = LOCAL.search(d.invoke("task", {"name": "t"}).text).groups()
            source = f"coord:{p}/{local}"
        elif make == "decision":
            _, p, local, _ = LOCAL.search(d.invoke("decide", {"name": "d", "body": "why"}).text).groups()
            source = f"coord:{p}/{local}"
        else:
            source = str(project)
        with pytest.raises(Refused) as caught:
            d.invoke("reuse", {"source": source})
    assert caught.value.refusal.code == "invalid-input"
    if make in ("task", "decision"):
        assert make in caught.value.refusal.message


def test_reuse_of_a_source_never_minted_refuses_naming_it(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        d._selection = mint_project(d)
        source = f"coord:{'f' * 32}/{'e' * 32}"
        with pytest.raises(Refused) as caught:
            d.invoke("reuse", {"source": source})
    assert caught.value.refusal.code == "invalid-input"
    assert "f" * 32 in caught.value.refusal.message and "e" * 32 in caught.value.refusal.message


class _DivergedResolver:
    def __init__(self, refusal):
        self._refusal = refusal

    def resolve(self, address):
        return self._refusal


def test_reuse_of_a_source_with_several_standing_tips_refuses_naming_them(certified_work, monkeypatch):
    """A source cannot diverge in one root under the lock (coordination §4.3), so
    the resolver is stubbed to report a divergence, the way test_cmd_revise.py
    stubs one for `revise`: `resolve_one`'s divergent-tips branch has no other way
    to be exercised here."""
    from beliefs.coordination import CoordinationRefused
    from science.config import ReadContext
    with coordination_rig(certified_work, NAMES) as (d, _):
        d._selection = mint_project(d)
        _, project, local, _ = LOCAL.search(d.invoke("question", {"name": "q", "query": QUERY}).text).groups()
        tips = ("a" * 32, "b" * 32)
        refusal = CoordinationRefused("divergent-view", tips)
        monkeypatch.setattr(ReadContext, "coordination", lambda self: _DivergedResolver(refusal))
        with pytest.raises(Refused) as caught:
            d.invoke("reuse", {"source": f"coord:{project}/{local}"})
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "divergent-view"
    assert caught.value.refusal.data["tips"] == sorted(tips)
