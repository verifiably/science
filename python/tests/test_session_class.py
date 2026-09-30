"""Spec §4.1: the `session` write class, its port, and the selection block."""
import json
from pathlib import Path

import pytest

from helpers.world import QUERY, build_fixture_world, mint_project
from science.cursor import MIN_OUTPUT_BUDGET
from science.dispatch import Dispatcher, HandlerContractViolation, SessionPort
from science.refusal import Refusal, Refused
from science.render import AuditViolation
from science.report import SelectionBlock, Text
from science.schema import Declaration, InputSpec, WriteClass

PICK = Declaration("pick", "fixture", WriteClass("session"), MIN_OUTPUT_BUDGET,
                   (InputSpec("address", "string", False, "d"),), (), Path("."))


def _address(text):
    from beliefs.coordination import CoordinationAddress
    return None if text is None else CoordinationAddress.parse(text)


def pick_handler(ctx, port, *, address=None):
    pinned = port.select(_address(address))
    if pinned is None:
        return (SelectionBlock(None, None),)
    return (SelectionBlock(str(pinned), ctx.coordination().resolve(pinned).title),)


@pytest.fixture
def rig(certified_work):
    from science.config import ReadContext
    from science.loader import production_tree, resolve_handlers
    from science.session import open_session

    cfg = build_fixture_world(certified_work)
    decls = tuple(d for d in production_tree() if d.name in ("project", "revise"))
    handlers = resolve_handlers(decls)
    handlers["pick"] = pick_handler
    session = open_session(cfg)
    dispatcher = Dispatcher(decls + (PICK,), handlers, ReadContext.open(cfg), session=session)
    try:
        yield dispatcher, session, cfg
    finally:
        session.close()


def _lines(cfg, session, kind):
    from beliefs.session import ledger_path
    text = ledger_path(cfg.operations_root, session.session_id).read_text()
    return [line for line in map(json.loads, text.splitlines()) if line["line"] == kind]


def test_selecting_sets_the_endpoint_selection_and_ledgers_one_line(rig):
    d, session, cfg = rig
    health = mint_project(d, "health")
    out = d.invoke("pick", {"address": str(health)}, invocation_id="S" * 8)
    pinned = session.invocation_selection("S" * 8).project
    assert out.text == f"selected: {pinned}\nname: health\n"
    assert pinned.unpinned() == health and d.selection == health
    assert [line["project"] for line in _lines(cfg, session, "select")] == [str(pinned)]
    (close,) = [line for line in _lines(cfg, session, "invocation-close") if line["invocation"] == "S" * 8]
    assert close["outcome"] == {"done": []}


def test_clearing_renders_none(rig):
    d, _, _ = rig
    d.invoke("pick", {"address": str(mint_project(d, "health"))})
    assert d.invoke("pick", {}).text == "selected: none\n"
    assert d.selection is None


def test_without_a_session_refuses_permit_exceeded(certified_work):
    from science.config import ReadContext

    d = Dispatcher((PICK,), {"pick": pick_handler}, ReadContext.open(build_fixture_world(certified_work)))
    with pytest.raises(Refused) as caught:
        d.invoke("pick", {})
    assert caught.value.refusal.code == "permit-exceeded"
    assert caught.value.refusal.message == "no writer session on this surface"


def test_the_handler_is_given_a_port_and_no_kernel_writer(rig):
    d, _, _ = rig
    seen = []

    def spy(ctx, port, *, address=None):
        seen.append(port)
        return pick_handler(ctx, port, address=address)

    d._handlers["pick"] = spy
    d.invoke("pick", {})
    (port,) = seen
    assert type(port) is SessionPort
    assert [name for name in dir(port) if not name.startswith("_")] == ["select"]


def test_a_replay_returns_the_recorded_outcome_and_appends_no_second_line(rig):
    d, session, cfg = rig
    health = mint_project(d, "health")
    first = d.invoke("pick", {"address": str(health)}, invocation_id="R" * 8)
    d._handlers["pick"] = lambda *a, **k: pytest.fail("a replay must not run the handler")
    again = d.invoke("pick", {"address": str(health)}, invocation_id="R" * 8)
    assert again.text == first.text
    assert len(_lines(cfg, session, "select")) == 1


def test_a_replay_after_a_rename_renders_what_the_selection_was(rig):
    d, _, _ = rig
    health = mint_project(d, "health")
    first = d.invoke("pick", {"address": str(health)}, invocation_id="N" * 8)
    d.invoke("revise", {"address": str(health), "name": "human health"})
    again = d.invoke("pick", {"address": str(health)}, invocation_id="N" * 8)
    assert again.text == first.text and "name: health\n" in again.text
    assert d.selection == health  # the selection is the address; the rename left it standing


def test_a_kernel_refusal_closes_the_invocation_and_replays(rig):
    d, session, cfg = rig
    health = mint_project(d, "health")
    d.invoke("pick", {"address": str(health)})
    for _ in range(2):
        with pytest.raises(Refused) as caught:
            d.invoke("pick", {"address": "coord:" + "f" * 32}, invocation_id="K" * 8)
        assert caught.value.refusal.code == "kernel-refused"
        assert caught.value.refusal.data["kind"] == "ProjectNotResolvable"
    assert d.selection == health
    assert len(_lines(cfg, session, "select")) == 1


def test_a_surface_refusal_before_selecting_closes_and_replays(rig):
    d, session, cfg = rig

    def refusing(ctx, port, *, address=None):
        raise Refused(Refusal("invalid-input", "nothing to select"))

    d._handlers["pick"] = refusing
    for _ in range(2):
        with pytest.raises(Refused) as caught:
            d.invoke("pick", {}, invocation_id="V" * 8)
        assert caught.value.refusal.message == "nothing to select"
    assert _lines(cfg, session, "select") == []


def test_a_report_with_anything_but_the_recorded_block_fails_the_audit(rig):
    d, _, _ = rig
    health = mint_project(d, "health")

    def echoing(ctx, port, *, address=None):
        return pick_handler(ctx, port, address=address) + (Text("audit echo!"),)

    d._handlers["pick"] = echoing
    with pytest.raises(AuditViolation):
        d.invoke("pick", {"address": str(health)}, invocation_id="E" * 8)
    # The selection was ledgered, so the invocation closed `done` and a replay
    # renders the canonical block, bypassing the echoing handler.
    replay = d.invoke("pick", {"address": str(health)}, invocation_id="E" * 8)
    assert "audit echo" not in replay.text and replay.text.startswith(f"selected: {health}@")


def test_a_forged_name_never_renders(rig):
    d, _, _ = rig
    health = mint_project(d, "health")

    def forging(ctx, port, *, address=None):
        return (SelectionBlock(str(port.select(_address(address))), "FORGED NAME"),)

    d._handlers["pick"] = forging
    out = d.invoke("pick", {"address": str(health)})
    assert "FORGED NAME" not in out.text and "name: health\n" in out.text


def test_a_handler_that_returns_without_selecting_is_a_defect(rig):
    d, _, _ = rig
    d._handlers["pick"] = lambda ctx, port, *, address=None: (SelectionBlock(None, None),)
    for _ in range(2):  # the first response and the replay alike
        with pytest.raises(HandlerContractViolation):
            d.invoke("pick", {}, invocation_id="Z" * 8)


def test_a_refusal_after_selecting_is_a_defect_and_the_selection_stands(rig):
    d, _, _ = rig
    health = mint_project(d, "health")

    def late(ctx, port, *, address=None):
        port.select(_address(address))
        raise Refused(Refusal("invalid-input", "refused after selecting"))

    d._handlers["pick"] = late
    with pytest.raises(HandlerContractViolation):
        d.invoke("pick", {"address": str(health)}, invocation_id="L" * 8)
    assert d.selection == health  # the ledger line is truth
    assert "name: health\n" in d.invoke("pick", {"address": str(health)}, invocation_id="L" * 8).text


def test_a_long_name_continues_from_the_ledger_without_the_handler(rig):
    d, _, _ = rig
    out = d.invoke("project", {"name": "n" * 600, "query": QUERY})
    import re
    address = "coord:" + re.search(r"project:([0-9a-f]{32})\.", out.text).group(1)
    first = d.invoke("pick", {"address": address}, invocation_id="C" * 8)
    cursor = first.text.rsplit("cursor ", 1)[1].strip()
    d._handlers["pick"] = lambda *a, **k: pytest.fail("a continuation must not run the handler")
    second = d.invoke("pick", {}, cursor=cursor)
    assert second.text and "n" * 50 in second.text


def test_a_second_selection_is_a_defect_and_replays_the_first(rig):
    d, session, cfg = rig
    health = mint_project(d, "health")

    def twice(ctx, port, *, address=None):
        port.select(_address(address))
        port.select(None)

    d._handlers["pick"] = twice
    with pytest.raises(HandlerContractViolation):
        d.invoke("pick", {"address": str(health)}, invocation_id="D" * 8)
    assert d.selection == health
    assert len(_lines(cfg, session, "select")) == 1
    assert "name: health\n" in d.invoke("pick", {"address": str(health)}, invocation_id="D" * 8).text


def test_a_kernel_refusal_after_selecting_is_a_defect_and_replays(rig):
    from beliefs.errors import ProjectNotResolvable

    d, session, cfg = rig
    health = mint_project(d, "health")

    def late(ctx, port, *, address=None):
        port.select(_address(address))
        raise ProjectNotResolvable("refused after selecting")

    d._handlers["pick"] = late
    with pytest.raises(HandlerContractViolation):
        d.invoke("pick", {"address": str(health)}, invocation_id="W" * 8)
    assert d.selection == health
    assert len(_lines(cfg, session, "select")) == 1
    assert "name: health\n" in d.invoke("pick", {"address": str(health)}, invocation_id="W" * 8).text
