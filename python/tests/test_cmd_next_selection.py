"""Spec §5.5 and P5: next through the selected project's query, evaluated live."""
import json
import re

import pytest

from helpers.world import add_one_more_record, build_belief_world, build_fixture_world, open_rig
from science.refusal import Refused

NAMES = ("project", "project-select", "revise", "next", "belief")
VERSION = "science.view-query.v1"


def _addresses(*refs):
    return json.dumps({"version": VERSION, "clauses": [{"all": [{"addresses": list(refs)}]}]})


def _kinds(kinds):
    return json.dumps({"version": VERSION, "clauses": [{"all": [{"kinds": list(kinds)}]}]})


def _project(d, name, query):
    from beliefs.coordination import CoordinationAddress

    out = d.invoke("project", {"name": name, "query": query})
    return CoordinationAddress(re.search(r"project:([0-9a-f]{32})\.", out.text).group(1))


def _rows(text):
    return text.split("propositions:\n", 1)[1]


def _refused(call, code):
    with pytest.raises(Refused) as caught:
        call()
    assert caught.value.refusal.code == code
    return caught.value.refusal


@pytest.fixture
def world(certified_work):
    """The fixture world with two propositions, p1 and p2."""
    cfg = build_fixture_world(certified_work)
    add_one_more_record(cfg)
    return cfg


def test_next_under_a_selection_classifies_exactly_the_selected_propositions(world):
    """The mutation that falls back to the whole world shows p2."""
    with open_rig(world, NAMES) as (d, ctx):
        one = _project(d, "one", _addresses("proposition:p1"))
        d.invoke("project-select", {"target": "one"})
        text = d.invoke("next", {}).text
        revision = ctx.coordination().resolve(one).uid
    assert _rows(text) == "  proposition:p1: not-ready: p1\n"
    assert text.startswith(
        "## Next\nselection:\n"
        f"  project: {one}@{revision}\n  name: one\n  complete: true\n  absent: none\n"
        f"  world: {world.world.world_id}\n  corpus ")
    assert re.search(r"\n  corpus [0-9a-f]{32}: [0-9a-f]{64}\npropositions:\n", text)


def test_unselected_next_equals_next_under_a_whole_world_project(world):
    """P5: the unselected session reads the whole world."""
    with open_rig(world, NAMES) as (d, _):
        unselected = d.invoke("next", {}).text
        _project(d, "everything", _kinds(sorted(world.profile.coordination_query_kinds)))
        d.invoke("project-select", {"target": "everything"})
        selected = d.invoke("next", {}).text
    assert unselected == "## Next\npropositions:\n" + _rows(unselected)  # no selection block
    assert _rows(selected) == _rows(unselected)
    assert "proposition:p1" in _rows(selected) and "proposition:p2" in _rows(selected)


def test_belief_answers_for_its_proposition_whatever_is_selected(certified_work):
    """P5 and decision 4: selection scopes enumeration, never lookup by identity."""
    ask = {"proposition": "proposition:p1"}
    with open_rig(build_belief_world(certified_work), NAMES) as (d, _):
        _project(d, "empty", json.dumps({"version": VERSION, "clauses": []}))
        d.invoke("project-select", {"target": "empty"})
        selected = d.invoke("belief", ask).text
        assert _rows(d.invoke("next", {}).text) == "  none: no propositions\n"
        d.invoke("project-select", {"clear": True})
        assert d.invoke("belief", ask).text == selected
        assert "proposition:p1" in d.invoke("next", {}).text


def test_a_proposition_minted_after_selecting_appears_without_republishing(certified_work):
    """Decision 3: the queue is attention, evaluated live; no epoch mediates it."""
    cfg = build_fixture_world(certified_work)
    with open_rig(cfg, NAMES) as (d, _):
        _project(d, "claims", _kinds(["proposition"]))
        d.invoke("project-select", {"target": "claims"})
        assert "proposition:p2" not in d.invoke("next", {}).text
        add_one_more_record(cfg)
        assert "proposition:p2" in _rows(d.invoke("next", {}).text)


def test_a_proposition_minted_while_next_runs_is_not_dropped(certified_work, monkeypatch):
    """The lookup view opens after the live capture. One opened before it does
    not hold a record minted in between, which the capture then selects: the
    mutation that opens the view first drops p2's row under `complete: true`."""
    import science.commands.next as next_module

    cfg = build_fixture_world(certified_work)
    evaluate = next_module.live_selection

    def minting_first(ctx, project):
        add_one_more_record(cfg)  # lands after the handler began, before the capture
        return evaluate(ctx, project)

    with open_rig(cfg, NAMES) as (d, _):
        _project(d, "claims", _kinds(["proposition"]))
        d.invoke("project-select", {"target": "claims"})
        monkeypatch.setattr(next_module, "live_selection", minting_first)
        text = d.invoke("next", {}).text
    assert "complete: true" in text
    assert "proposition:p1" in _rows(text) and "proposition:p2" in _rows(text)


def test_a_selected_record_no_mounted_corpus_holds_refuses_rather_than_vanishing(world, monkeypatch):
    """A capture naming a record no mounted corpus holds leaves a row `next`
    cannot read: refused by name, never a silently shorter queue."""
    from types import SimpleNamespace

    import science.commands.next as next_module

    stamp = SimpleNamespace(world_id=world.world.world_id, coverage=())
    ghost = SimpleNamespace(selected=("proposition:ghost", "proposition:p1"), complete=True, absent=(), stamp=stamp)
    with open_rig(world, NAMES) as (d, _):
        _project(d, "one", _addresses("proposition:p1"))
        d.invoke("project-select", {"target": "one"})
        monkeypatch.setattr(next_module, "live_selection", lambda ctx, project: ghost)
        refusal = _refused(lambda: d.invoke("next", {}), "invalid-input")
    assert "proposition:ghost" in refusal.message and "corpus_roots" in refusal.message


def test_a_revised_query_is_followed_without_reselecting(world):
    with open_rig(world, NAMES) as (d, _):
        one = _project(d, "one", _addresses("proposition:p1"))
        d.invoke("project-select", {"target": "one"})
        d.invoke("revise", {"address": str(one), "query": _addresses("proposition:p2")})
        assert _rows(d.invoke("next", {}).text) == "  proposition:p2: not-ready: p2\n"


def test_project_binds_one_next_and_leaves_the_session_unselected(world):
    with open_rig(world, NAMES) as (d, _):
        _project(d, "one", _addresses("proposition:p1"))
        assert _rows(d.invoke("next", {}, project="one").text) == "  proposition:p1: not-ready: p1\n"
        assert d.selection is None
        assert "proposition:p2" in d.invoke("next", {}).text


def test_a_query_naming_an_address_the_world_does_not_hold_is_kernel_refused(world):
    with open_rig(world, NAMES) as (d, _):
        _project(d, "ghost", _addresses("proposition:absent"))
        d.invoke("project-select", {"target": "ghost"})
        refusal = _refused(lambda: d.invoke("next", {}), "kernel-refused")
    assert refusal.data == {"kind": "SelectionRefused", "reason": "address-unknown",
                            "refs": ["proposition:absent"]}


def test_a_contended_capture_is_kernel_refused_not_a_traceback(world, monkeypatch):
    """A live capture never waits behind a corpus operation: the kernel raises
    BuildContended, and the person is told so."""
    import beliefs.world.live as live
    from beliefs.errors import BuildContended

    def contended(world_, query):
        raise BuildContended("the corpus operation lock is held")

    with open_rig(world, NAMES) as (d, _):
        _project(d, "one", _addresses("proposition:p1"))
        d.invoke("project-select", {"target": "one"})
        monkeypatch.setattr(live, "evaluate_live_query", contended)
        refusal = _refused(lambda: d.invoke("next", {}), "kernel-refused")
    assert refusal.data == {"kind": "BuildContended"}
    assert "operation lock" in refusal.message


def test_next_declares_the_selection_and_its_reads():
    from science.loader import production_tree

    decl = next(decl for decl in production_tree() if decl.name == "next")
    assert decl.selects is True
    assert set(decl.reads) == {"corpus-stored", "holdings", "epoch", "registry", "coordination"}


def test_next_renders_identically_through_the_cli_and_mcp(certified_work, capsys):
    from helpers.world import write_cli_config
    from science.cli import main
    from science.config import ReadContext, load_config
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers
    from science.mcp import handle_request
    from test_mcp import rpc

    config_path = write_cli_config(certified_work)
    config = load_config(config_path)
    with open_rig(config, NAMES) as (d, _):
        one = _project(d, "one", _addresses("proposition:p1"))
    declarations = production_tree()
    dispatcher = Dispatcher(declarations, resolve_handlers(declarations), ReadContext.open(config))
    assert main(["next", "--config", str(config_path), "--project", str(one)]) == 0
    cli_text = capsys.readouterr().out
    mcp_text = handle_request(rpc("tools/call", {"name": "next", "arguments": {"project": str(one)}}),
                              dispatcher, declarations)["result"]["content"][0]["text"]
    assert cli_text == mcp_text and "selection:\n" in cli_text
