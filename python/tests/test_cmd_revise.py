import re

import pytest

from helpers.world import QUERY, coordination_rig, mint_project
from science.refusal import Refused

NAMES = ("project", "task", "revise")


def _task(d):
    out = d.invoke("task", {"name": "hold", "body": "the matrix"})
    project, local = re.search(r"task:([0-9a-f]{32})\.([0-9a-f]{32})\.", out.text).groups()
    return f"coord:{project}/{local}"


def test_rename_carries_every_other_field(certified_work):
    from beliefs.coordination import CoordinationAddress
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        project = mint_project(d, "health")
        d.invoke("revise", {"address": str(project), "name": "human health"})
        node = ctx.coordination().resolve(CoordinationAddress(project.project))
    assert node.title == "human health"
    assert node.facets["coordination"]["query"]["clauses"][0]["all"][0]["kinds"] == ["proposition"]


def test_closing_a_task_is_a_status_revision(certified_work):
    from beliefs.coordination import CoordinationAddress
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        d._selection = mint_project(d)
        address = _task(d)
        d.invoke("revise", {"address": address, "status": "done"})
        node = ctx.coordination().resolve(CoordinationAddress.parse(address))
    assert node.facets["coordination"]["status"] == "done" and node.body == "the matrix"


def test_a_field_the_kind_lacks_refuses_before_any_act(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        project = mint_project(d)
        with pytest.raises(Refused) as caught:
            d.invoke("revise", {"address": str(project), "status": "done"})
    assert caught.value.refusal.code == "invalid-input"
    assert "status" in caught.value.refusal.message and "project" in caught.value.refusal.message


def test_an_address_never_minted_refuses_naming_it(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("revise", {"address": "coord:" + "f" * 32, "name": "x"})
    assert caught.value.refusal.code == "invalid-input"
    assert "f" * 32 in caught.value.refusal.message


def test_a_revision_with_no_field_refuses(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        project = mint_project(d)
        with pytest.raises(Refused) as caught:
            d.invoke("revise", {"address": str(project)})
    assert caught.value.refusal.code == "invalid-input"


def test_clear_depends_empties_a_tasks_dependencies_through_the_cli_shape(certified_work):
    from beliefs.coordination import CoordinationAddress
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        d._selection = mint_project(d)
        first, second = _task(d), _task(d)
        d.invoke("revise", {"address": second, "depends": [first]})
        d.invoke("revise", {"address": second, "clear_depends": True})
        node = ctx.coordination().resolve(CoordinationAddress.parse(second))
        with pytest.raises(Refused) as both:
            d.invoke("revise", {"address": second, "depends": [first], "clear_depends": True})
    assert node.facets["coordination"]["depends"] == []
    assert both.value.refusal.code == "invalid-input"


def test_clear_depends_parses_from_the_cli():
    from science.cli import build_parser
    from science.loader import production_tree
    parsed = build_parser(production_tree()).parse_args(
        ["revise", "--address", "coord:" + "a" * 32 + "/" + "b" * 32, "--clear-depends"])
    assert parsed.clear_depends is True


class _Tip:
    def __init__(self, node):
        self.node = node


class _RecordingWriter:
    actor = "session:" + "0" * 32

    def __init__(self):
        self.calls = []

    def revise_coordination(self, kind, address, *, predecessors, content):
        self.calls.append((kind, address, sorted(predecessors), content))
        return self.node


def test_divergence_refuses_without_repair(certified_work, monkeypatch):
    """Two tips cannot arise in one root under the lock (coordination §4.3), so
    the resolver is stubbed to report them. Part 3's two-corpus fixture exercises
    a real divergence end to end."""
    import science.commands.revise as revise_module
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        project = mint_project(d)
        real = ctx.coordination().tips(project)[0].node
        # Node is a pydantic model: a sibling revision differs in its revision id alone.
        twin = real.model_copy(update={"id": real.id.rsplit(".", 1)[0] + "." + "e" * 32, "uid": "e" * 32})
        monkeypatch.setattr(revise_module, "standing_tips", lambda ctx, address: (_Tip(real), _Tip(twin)))
        with pytest.raises(Refused) as caught:
            d.invoke("revise", {"address": str(project), "name": "x"})
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "divergent-view"
    assert caught.value.refusal.data["tips"] == sorted([real.uid, twin.uid])


def test_repair_names_every_tip_and_takes_every_field(certified_work, monkeypatch):
    """The handler alone, with a recording writer: the dispatcher's write audit
    admits only records an act minted, and a divergence cannot be built in one
    root, so predecessor construction is checked here and real writes are
    covered by the dispatcher tests above."""
    import science.commands.revise as revise_module
    from science.config import ReadContext
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        project = mint_project(d)
        real = ctx.coordination().tips(project)[0].node
    twin = real.model_copy(update={"id": real.id.rsplit(".", 1)[0] + "." + "e" * 32, "uid": "e" * 32})
    monkeypatch.setattr(revise_module, "standing_tips", lambda ctx, address: (_Tip(real), _Tip(twin)))
    writer = _RecordingWriter()
    writer.node = real
    with pytest.raises(Refused) as partial:
        revise_module.handle(ctx, writer, address=str(project), name="x", repair=True)
    assert partial.value.refusal.code == "invalid-input"  # body and query missing
    assert writer.calls == []
    revise_module.handle(ctx, writer, address=str(project), name="x", body="", query=QUERY, repair=True)
    ((kind, address, predecessors, content),) = writer.calls
    assert kind == "project" and predecessors == sorted([real.uid, twin.uid])
    assert content["name"] == "x" and content["author"] == writer.actor
