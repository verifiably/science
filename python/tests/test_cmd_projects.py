"""Spec §3.8: projects and project-show."""
import re

import pytest

from helpers.world import QUERY, build_world_without_coordination, coordination_rig, mint_project
from science.refusal import Refused

NAMES = ("project", "project-select", "projects", "project-show",
         "question", "hypothesis", "task", "decide", "revise")
CANONICAL_QUERY = '{"clauses":[{"all":[{"kinds":["proposition"]}]}],"version":"science.view-query.v1"}'


def _refused(call, code):
    with pytest.raises(Refused) as caught:
        call()
    assert caught.value.refusal.code == code
    return caught.value.refusal


def _task(d, name):
    out = d.invoke("task", {"name": name})
    project, local = re.search(r"task:([0-9a-f]{32})\.([0-9a-f]{32})\.", out.text).groups()
    return f"coord:{project}/{local}"


def _twin(node, title):
    """A sibling revision of `node`: pydantic copy differing in revision id and name."""
    return node.model_copy(update={"id": node.id.rsplit(".", 1)[0] + "." + "e" * 32, "uid": "e" * 32,
                                   "title": title})


def _diverge(monkeypatch, kind, address, real, twin):
    """Two tips cannot arise in one root (coordination §4.3), so the resolver's
    enumeration is stubbed to report them for one address."""
    from beliefs.coordination import CoordinationRefused
    from beliefs.corpus import CoordinationResolver

    standing, revision = CoordinationResolver.standing, CoordinationResolver.revision

    def fake_standing(self, asked, *, project=None):
        found = dict(standing(self, asked, project=project))
        if asked == kind:
            found[address] = CoordinationRefused("divergent-view", (real.uid, twin.uid))
        return found

    monkeypatch.setattr(CoordinationResolver, "standing", fake_standing)
    monkeypatch.setattr(CoordinationResolver, "revision",
                        lambda self, uid: twin if uid == twin.uid else revision(self, uid))


def test_projects_lists_by_name_then_address_and_marks_the_selected(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        zeta, first, second = mint_project(d, "zeta"), mint_project(d, "alpha"), mint_project(d, "alpha")
        d.invoke("project-select", {"target": "zeta"})
        text = d.invoke("projects", {}).text
        revision = {address: ctx.coordination().resolve(address).uid for address in (zeta, first, second)}
    low, high = sorted((first, second), key=str)
    assert text == ("## Projects\nprojects:\n"
                    f"  {low}: alpha @{revision[low]}\n"
                    f"  {high}: alpha @{revision[high]}\n"
                    f"  {zeta}: zeta @{revision[zeta]} (selected)\n")


def test_projects_with_none_says_so(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        assert d.invoke("projects", {}).text == "## Projects\nprojects:\n  none: no projects\n"


def test_a_divergent_project_renders_once_with_every_tip(certified_work, monkeypatch):
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        health = mint_project(d, "health")
        real = ctx.coordination().resolve(health)
        twin = _twin(real, "human health")
        _diverge(monkeypatch, "project", health, real, twin)
        text = d.invoke("projects", {}).text
    assert text.count(str(health)) == 1
    assert f"  {health}: divergent: " in text
    assert f"health @{real.uid}" in text and f"human health @{twin.uid}" in text


def test_project_show_renders_the_selection_in_section_order(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        health = mint_project(d, "health")
        d.invoke("project-select", {"target": "health"})
        hold, run = _task(d, "hold"), _task(d, "run")
        d.invoke("revise", {"address": run, "status": "done"})
        d.invoke("question", {"name": "Does PHF19 track stage?", "query": QUERY})
        d.invoke("hypothesis", {"name": "PHF19 rises with stage", "query": QUERY})
        d.invoke("decide", {"name": "Use the coarse query", "body": "No disease vocabulary is bound yet."})
        text = d.invoke("project-show", {}).text
        revision = ctx.coordination().resolve(health).uid
    assert text.startswith(
        "## Project: health\nproject:\n"
        f"  address: {health}\n  revision: {revision}\n  name: health\n  query: {CANONICAL_QUERY}\n"
        "open tasks:\n"
        f"  {hold}: open: hold\n")
    titles = ["open tasks:", "questions:", "hypotheses:", "decisions:", "closed tasks:"]
    positions = [text.index("\n" + title) for title in titles]
    assert positions == sorted(positions)
    assert text.endswith(f"closed tasks:\n  {run}: done: run\n")  # a `done` revision moved it (spec §9)
    assert ": Does PHF19 track stage?\n" in text and ": Use the coarse query\n" in text


def test_a_project_with_no_records_says_so(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        d.invoke("project-select", {"target": str(mint_project(d, "health"))})
        assert d.invoke("project-show", {}).text.endswith("No questions, hypotheses, tasks or decisions yet.\n")


def test_project_binds_this_show_only(certified_work):
    """P8 at the dispatcher: the field shows another project and the
    endpoint's selection is unchanged afterwards."""
    with coordination_rig(certified_work, NAMES) as (d, _):
        health, cancer = mint_project(d, "health"), mint_project(d, "cancer")
        d.invoke("project-select", {"target": "health"})
        assert d.invoke("project-show", {}, project="cancer").text.startswith("## Project: cancer\n")
        assert d.invoke("project-show", {}, project=str(cancer)).text.startswith("## Project: cancer\n")
        assert d.selection == health
        assert d.invoke("project-show", {}).text.startswith("## Project: health\n")


def test_nothing_selected_and_nothing_named_refuses(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        mint_project(d, "health")
        refusal = _refused(lambda: d.invoke("project-show", {}), "no-current-project")
        _refused(lambda: d.invoke("project-show", {}, project="nope"), "unknown-project")
    assert "project-select" in refusal.message and "--project" in refusal.message


def test_a_revised_project_shows_its_new_tip_without_reselecting(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        health = mint_project(d, "health")
        d.invoke("project-select", {"target": "health"})
        d.invoke("revise", {"address": str(health), "name": "human health"})
        assert d.invoke("project-show", {}).text.startswith("## Project: human health\n")


def test_a_divergent_task_renders_once_under_open_tasks_with_every_tip(certified_work, monkeypatch):
    from beliefs.coordination import CoordinationAddress

    with coordination_rig(certified_work, NAMES) as (d, ctx):
        d.invoke("project-select", {"target": str(mint_project(d, "health"))})
        hold = CoordinationAddress.parse(_task(d, "hold"))
        real = ctx.coordination().resolve(hold)
        twin = _twin(real, "hold it")
        _diverge(monkeypatch, "task", hold, real, twin)
        text = d.invoke("project-show", {}).text
    assert "closed tasks:" not in text and text.count(str(hold)) == 1
    assert f"open tasks:\n  {hold}: divergent: " in text
    assert f"hold @{real.uid}" in text and f"hold it @{twin.uid}" in text


def test_without_coordination_both_reads_refuse_naming_the_setting(certified_work):
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers

    decls = tuple(decl for decl in production_tree() if decl.name in ("projects", "project-show"))
    d = Dispatcher(decls, resolve_handlers(decls),
                   ReadContext.open(build_world_without_coordination(certified_work)))
    for command in ("projects", "project-show"):
        assert "coordination = false" in _refused(lambda: d.invoke(command, {}), "invalid-input").message


def test_the_project_reads_render_identically_through_the_cli_and_mcp(certified_work, capsys):
    """Framework §9.4: each new read, byte for byte, through both transports."""
    from helpers.world import mint_projects, write_cli_config
    from science.cli import main
    from science.config import ReadContext, load_config
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers
    from science.mcp import handle_request
    from test_mcp import rpc

    config_path = write_cli_config(certified_work)
    config = load_config(config_path)
    (health,) = mint_projects(config, "health")
    declarations = production_tree()
    dispatcher = Dispatcher(declarations, resolve_handlers(declarations), ReadContext.open(config))
    for argv, name, arguments in (
        (["projects"], "projects", {}),
        (["project-show", "--project", str(health)], "project-show", {"project": str(health)}),
    ):
        assert main([*argv, "--config", str(config_path)]) == 0
        cli_text = capsys.readouterr().out
        mcp_text = handle_request(rpc("tools/call", {"name": name, "arguments": arguments}),
                                  dispatcher, declarations)["result"]["content"][0]["text"]
        assert cli_text == mcp_text and "health" in cli_text
