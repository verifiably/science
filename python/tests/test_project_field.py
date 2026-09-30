"""Spec §4.2: the `selects` key and the `project` protocol field."""
from pathlib import Path

import pytest

from helpers.world import QUERY, build_world_without_coordination, coordination_rig, mint_project
from science.cursor import MIN_OUTPUT_BUDGET
from science.refusal import Refused
from science.report import Text
from science.schema import Declaration, WriteClass

PEEK = Declaration("peek", "fixture", WriteClass("read-only"), MIN_OUTPUT_BUDGET, (), ("coordination",),
                   Path("."), selects=True)
PLAIN = Declaration("plain", "fixture", WriteClass("read-only"), MIN_OUTPUT_BUDGET, (), (), Path("."))
LONG = Declaration("long", "fixture", WriteClass("read-only"), MIN_OUTPUT_BUDGET, (), ("coordination",),
                   Path("."), selects=True)


def peek_handler(ctx):
    return (Text(f"selection={ctx.selection}"),)


def long_handler(ctx):
    return tuple(Text(f"{ctx.selection} row {i} " + "x" * 60) for i in range(200))


EXTRA = ((PEEK, peek_handler), (PLAIN, peek_handler), (LONG, long_handler))
NAMES = ("project", "revise")


def _refused(call, code):
    with pytest.raises(Refused) as caught:
        call()
    assert caught.value.refusal.code == code
    return caught.value.refusal


def test_project_binds_one_invocation_and_leaves_the_endpoint_selection(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        health, cancer = mint_project(d, "health"), mint_project(d, "cancer")
        d._selection = health  # project-select sets this through the session port (Task 2)
        assert d.invoke("peek", {}, project=str(cancer)).text == f"selection={cancer}\n"
        assert d.invoke("peek", {}, project="cancer").text == f"selection={cancer}\n"
        assert d.invoke("peek", {}).text == f"selection={health}\n"
        assert d.selection == health


def test_a_name_follows_the_projects_current_name(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        health = mint_project(d, "health")
        d.invoke("revise", {"address": str(health), "name": "human health"})
        assert d.invoke("peek", {}, project="human health").text == f"selection={health}\n"
        _refused(lambda: d.invoke("peek", {}, project="health"), "unknown-project")


def test_a_project_that_does_not_stand_refuses_unknown_project(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        _refused(lambda: d.invoke("peek", {}, project="nope"), "unknown-project")
        _refused(lambda: d.invoke("peek", {}, project="coord:" + "f" * 32), "unknown-project")


def test_a_malformed_or_subordinate_address_is_invalid_input_not_a_name(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        _refused(lambda: d.invoke("peek", {}, project="coord:zzz"), "invalid-input")
        _refused(lambda: d.invoke("peek", {}, project="coord:" + "a" * 32 + "/" + "b" * 32), "invalid-input")
        _refused(lambda: d.invoke("peek", {}, project=""), "invalid-input")


def test_a_shared_name_refuses_ambiguous_project_listing_each_candidate(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        first, second = mint_project(d, "health"), mint_project(d, "health")
        refusal = _refused(lambda: d.invoke("peek", {}, project="health"), "ambiguous-project")
        assert d.invoke("peek", {}, project=str(first)).text == f"selection={first}\n"
    candidates = refusal.data["candidates"]
    assert sorted(c["address"] for c in candidates) == sorted([str(first), str(second)])
    assert all(len(c["query_digest"]) == 64 for c in candidates)


def test_project_on_a_command_that_does_not_select_refuses(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        mint_project(d, "health")
        refusal = _refused(lambda: d.invoke("plain", {}, project="health"), "invalid-input")
    assert "plain" in refusal.message


def test_project_on_a_write_refuses_and_claims_nothing(certified_work):
    inputs = {"name": "health", "query": QUERY}
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        _refused(lambda: d.invoke("project", inputs, invocation_id="W" * 8, project="health"), "invalid-input")
        assert "[project]" in d.invoke("project", inputs, invocation_id="W" * 8).text  # the id was never claimed


def test_a_continuation_carries_the_field_again(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        health = mint_project(d, "health")
        first = d.invoke("long", {}, project=str(health))
        cursor = first.text.rsplit("cursor ", 1)[1].strip()
        assert d.invoke("long", {}, cursor=cursor, project=str(health)).text
        # Without the field the endpoint's selection (none) renders another report.
        _refused(lambda: d.invoke("long", {}, cursor=cursor), "stale-cursor")


def test_without_coordination_the_field_refuses_naming_the_setting(certified_work):
    from science.config import ReadContext
    from science.dispatch import Dispatcher

    ctx = ReadContext.open(build_world_without_coordination(certified_work))
    d = Dispatcher((PEEK,), {"peek": peek_handler}, ctx)
    refusal = _refused(lambda: d.invoke("peek", {}, project="health"), "invalid-input")
    assert "coordination = false" in refusal.message


def test_selected_project_reads_the_selections_one_tip(certified_work):
    from dataclasses import replace

    from beliefs.coordination import CoordinationAddress
    from science.coordination import selected_project

    with coordination_rig(certified_work, NAMES) as (d, ctx):
        health = mint_project(d, "health")
        assert selected_project(ctx) is None
        assert selected_project(replace(ctx, selection=health)).title == "health"
        gone = replace(ctx, selection=CoordinationAddress("f" * 32))
        _refused(lambda: selected_project(gone), "unknown-project")


def test_a_divergent_selection_refuses_with_every_tip(certified_work, monkeypatch):
    """Two tips cannot arise in one root (coordination §4.3), so the resolver
    is stubbed to report them, as `test_cmd_revise.py` does."""
    from dataclasses import replace

    from beliefs.coordination import CoordinationRefused
    from beliefs.corpus import CoordinationResolver
    from science.coordination import selected_project

    with coordination_rig(certified_work, NAMES) as (d, ctx):
        health = mint_project(d, "health")
        tips = (ctx.coordination().resolve(health).uid, "e" * 32)
        monkeypatch.setattr(CoordinationResolver, "resolve",
                            lambda self, address: CoordinationRefused("divergent-view", tips))
        refusal = _refused(lambda: selected_project(replace(ctx, selection=health)), "kernel-refused")
    assert refusal.data == {"kind": "divergent-view", "tips": sorted(tips)}


def test_the_cli_offers_project_on_selects_commands_only():
    from science.cli import build_parser

    parser = build_parser((PEEK, PLAIN))
    assert parser.parse_args(["peek", "--project", "health"]).project == "health"
    assert parser.parse_args(["peek"]).project is None
    with pytest.raises(SystemExit) as caught:
        parser.parse_args(["plain", "--project", "health"])
    assert caught.value.code == 2


def test_the_mcp_schema_offers_project_on_selects_commands_only():
    from science.mcp import tool_schema

    assert tool_schema(PEEK)["inputSchema"]["properties"]["project"]["type"] == "string"
    assert "project" not in tool_schema(PLAIN)["inputSchema"]["properties"]


def test_an_mcp_call_carries_project_to_the_dispatcher(certified_work):
    from science.mcp import handle_request
    from test_mcp import rpc

    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        health = mint_project(d, "health")
        decls = (PEEK, PLAIN)
        shown = handle_request(rpc("tools/call", {"name": "peek", "arguments": {"project": "health"}}), d, decls)
        refused = handle_request(rpc("tools/call", {"name": "plain", "arguments": {"project": "health"}}), d, decls)
        wrong = handle_request(rpc("tools/call", {"name": "peek", "arguments": {"project": 3}}), d, decls)
    assert shown["result"]["content"][0]["text"] == f"selection={health}\n"
    assert refused["result"]["structuredContent"]["refusal"]["code"] == "invalid-input"
    assert wrong["error"]["message"] == "project must be a string"


def test_a_socket_request_carries_project():
    from science.serve import _validated

    assert _validated({"command": "peek", "project": "health"}) == ("peek", {}, None, None, "health")
    _refused(lambda: _validated({"command": "peek", "project": 3}), "invalid-input")
