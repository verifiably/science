"""Spec §3.7: project-select."""
import io
import json
import re

import pytest

from helpers.world import QUERY, build_world_without_coordination, coordination_rig, mint_project
from science.refusal import Refused

NAMES = ("project", "project-select", "question", "revise")


def _refused(call, code):
    with pytest.raises(Refused) as caught:
        call()
    assert caught.value.refusal.code == code
    return caught.value.refusal


def test_selecting_by_name_and_by_address(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        health, cancer = mint_project(d, "health"), mint_project(d, "cancer")
        by_name = d.invoke("project-select", {"target": "health"})
        assert d.selection == health
        revision = ctx.coordination().resolve(health).uid
        assert by_name.text == f"selected: {health}@{revision}\nname: health\n"
        assert "name: cancer\n" in d.invoke("project-select", {"target": str(cancer)}).text
        assert d.selection == cancer


def test_a_question_lands_under_the_selected_project_and_clear_unselects(certified_work):
    """P2 through the real command: selected, a question mints; cleared, it refuses."""
    question = {"name": "Does PHF19 track stage?", "query": QUERY}
    with coordination_rig(certified_work, NAMES) as (d, _):
        health = mint_project(d, "health")
        d.invoke("project-select", {"target": "health"})
        assert f"[question] question:{health.project}." in d.invoke("question", question).text
        assert d.invoke("project-select", {"clear": True}).text == "selected: none\n"
        assert d.selection is None
        _refused(lambda: d.invoke("question", question), "no-current-project")


def test_a_shared_name_is_ambiguous_and_the_address_still_selects(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        first, second = mint_project(d, "health"), mint_project(d, "health")
        refusal = _refused(lambda: d.invoke("project-select", {"target": "health"}), "ambiguous-project")
        assert sorted(c["address"] for c in refusal.data["candidates"]) == sorted([str(first), str(second)])
        assert d.selection is None
        d.invoke("project-select", {"target": str(second)})
        assert d.selection == second


def test_an_unknown_project_refuses_and_replays(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        for target in ("nope", "coord:" + "f" * 32):
            for _ in range(2):
                _refused(lambda: d.invoke("project-select", {"target": target}, invocation_id="U" * 8 + target[-1]),
                         "unknown-project")
        assert d.selection is None


def test_a_rename_leaves_the_selection_standing(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        health = mint_project(d, "health")
        d.invoke("project-select", {"target": "health"})
        d.invoke("revise", {"address": str(health), "name": "human health"})
        assert d.selection == health
        assert f"question:{health.project}." in d.invoke("question", {"name": "q", "query": QUERY}).text


@pytest.mark.parametrize("inputs", [{}, {"clear": False}, {"target": "health", "clear": True},
                                    {"target": ""}, {"target": "coord:zzz"},
                                    {"target": "coord:" + "a" * 32 + "/" + "b" * 32}])
def test_malformed_requests_refuse_before_any_selection(certified_work, inputs):
    with coordination_rig(certified_work, NAMES) as (d, _):
        health = mint_project(d, "health")
        d.invoke("project-select", {"target": "health"})
        _refused(lambda: d.invoke("project-select", inputs), "invalid-input")
        assert d.selection == health


def test_a_divergent_project_refuses_with_every_tip_and_selects_nothing(certified_work, monkeypatch):
    """Two tips cannot arise in one root, so the resolver is stubbed to report them."""
    from beliefs.coordination import CoordinationRefused
    from beliefs.corpus import CoordinationResolver

    with coordination_rig(certified_work, NAMES) as (d, ctx):
        health, cancer = mint_project(d, "health"), mint_project(d, "cancer")
        d.invoke("project-select", {"target": "cancer"})
        tips = (ctx.coordination().resolve(health).uid, "e" * 32)
        resolve = CoordinationResolver.resolve
        monkeypatch.setattr(
            CoordinationResolver, "resolve",
            lambda self, address: CoordinationRefused("divergent-view", tips)
            if address == health else resolve(self, address))
        refusal = _refused(lambda: d.invoke("project-select", {"target": str(health)}), "kernel-refused")
        assert refusal.data == {"kind": "divergent-view", "tips": sorted(tips)}
        assert d.selection == cancer


def test_without_coordination_every_form_refuses_naming_the_setting(certified_work):
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers
    from science.session import open_session

    cfg = build_world_without_coordination(certified_work)
    decls = tuple(decl for decl in production_tree() if decl.name == "project-select")
    session = open_session(cfg)
    try:
        d = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(cfg), session=session)
        for inputs in ({"clear": True}, {"target": "health"}):
            refusal = _refused(lambda: d.invoke("project-select", inputs), "invalid-input")
            assert "coordination = false" in refusal.message
    finally:
        session.close()


def test_a_session_handler_must_lead_with_ctx_and_port(monkeypatch):
    import science.commands.project_select as module
    from science.loader import production_tree, resolve_handlers
    from science.schema import DeclarationError

    decls = tuple(decl for decl in production_tree() if decl.name == "project-select")
    monkeypatch.setattr(module, "handle", lambda ctx, writer, *, target=None, clear=None: ())
    with pytest.raises(DeclarationError) as caught:
        resolve_handlers(decls)
    assert "['ctx', 'port']" in str(caught.value)


def test_over_mcp_stdio_a_selection_replays_and_a_refusal_carries_its_envelope(certified_work, short_tmp):
    """Framework §9.4: the new write through one transport, with replay and
    the refusal envelope."""
    from helpers.world import write_cli_config
    from science.mcp import serve
    from test_mcp import rpc

    def call(index, name, arguments):
        return json.dumps(rpc("tools/call", {"name": name, "arguments": arguments}, id=index))

    select = {"target": "health", "invocation_id": "S" * 8}
    unknown = {"target": "nope", "invocation_id": "U" * 8}
    frames = [call(1, "project", {"name": "health", "query": QUERY}),
              call(2, "project-select", select), call(3, "project-select", select),
              call(4, "project-select", unknown), call(5, "project-select", unknown)]
    stdout = io.StringIO()
    serve(write_cli_config(certified_work, service_socket=short_tmp / "service.sock"),
          stdin=io.BytesIO(("\n".join(frames) + "\n").encode()), stdout=stdout, stderr=io.StringIO())
    minted, first, again, refused, replayed = [json.loads(line)["result"] for line in stdout.getvalue().splitlines()]
    project = re.search(r"project:([0-9a-f]{32})\.", minted["content"][0]["text"]).group(1)
    assert first["content"][0]["text"].startswith(f"selected: coord:{project}@")
    assert first == again and first["structuredContent"] == {"invocation_id": "S" * 8}
    assert refused["isError"] is True and refused == replayed
    assert refused["structuredContent"]["refusal"]["code"] == "unknown-project"
    assert refused["structuredContent"]["invocation_id"] == "U" * 8
