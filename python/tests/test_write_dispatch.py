import threading

import pytest

from science.dispatch import Dispatcher
from science.cursor import MIN_OUTPUT_BUDGET
from science.refusal import Refused
from science.schema import Declaration
from pathlib import Path
from helpers.synthetic import (
    HANDLERS, MINT_CLAIM, OVERREACH, echoing_handler, forging_handler,
)
from helpers.world import build_fixture_world


@pytest.fixture
def rig(certified_work):
    from beliefs.session import open_attended_session
    from science.config import ReadContext
    cfg = build_fixture_world(certified_work)
    session = open_attended_session(cfg.world, cfg.operations_root, profile=cfg.profile)
    dispatcher = Dispatcher((MINT_CLAIM, OVERREACH), dict(HANDLERS),
                            ReadContext.open(cfg), session=session)
    try:
        yield dispatcher, session
    finally:
        session.close()  # the session-close ledger line, exercised every test


def test_write_returns_only_its_record(rig):
    d, _ = rig
    out = d.invoke("mint-claim", {"slug": "hello"})
    assert "proposition:hello" in out.text and "audit echo" not in out.text


def test_act_time_refusal_when_body_exceeds_declaration(rig):
    d, _ = rig
    with pytest.raises(Refused) as e:
        d.invoke("overreach", {})
    # The contract is exact: exceeding the invocation-scoped permit is
    # permit-exceeded, never a generic kernel refusal.
    assert e.value.refusal.code == "permit-exceeded"


def test_dedup_replays_without_reexecution(rig):
    d, session = rig
    first = d.invoke("mint-claim", {"slug": "once"}, invocation_id="A" * 8)
    again = d.invoke("mint-claim", {"slug": "once"}, invocation_id="A" * 8)
    assert first.text == again.text
    assert len(session.invocation_acts("A" * 8)) == 1  # one act, not two


def test_id_reuse_with_different_payload_refused(rig):
    d, _ = rig
    d.invoke("mint-claim", {"slug": "x"}, invocation_id="B" * 8)
    with pytest.raises(Refused) as e:
        d.invoke("mint-claim", {"slug": "y"}, invocation_id="B" * 8)
    assert e.value.refusal.code == "input-mismatch"


def test_concurrent_same_id_executes_once(rig):
    d, session = rig
    results, errors = [], []

    def call():
        try:
            results.append(d.invoke("mint-claim", {"slug": "race"}, invocation_id="C" * 8))
        except Refused as e:
            errors.append(e)

    threads = [threading.Thread(target=call) for _ in range(8)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(session.invocation_acts("C" * 8)) == 1
    # All eight succeed identically: one executes, seven replay canonically.
    assert not errors and len(results) == 8
    assert len({r.text for r in results}) == 1
    assert {r.invocation_id for r in results} == {"C" * 8}


def test_audit_echo_is_unrepresentable_and_ledger_stays_true(rig):
    from science.render import AuditViolation
    d, session = rig
    d._handlers["mint-claim"] = echoing_handler
    with pytest.raises(AuditViolation):  # internal error; the echo is never rendered
        d.invoke("mint-claim", {"slug": "z"}, invocation_id="E" * 8)
    # The acts committed, so the ledger closed `done` — and a dedup retry
    # replays canonically from the ledger, bypassing the echoing handler.
    replay = d.invoke("mint-claim", {"slug": "z"}, invocation_id="E" * 8)
    assert "audit echo" not in replay.text and "proposition:z" in replay.text


def test_refusal_replay_is_exact(rig):
    d, session = rig
    with pytest.raises(Refused) as first:
        d.invoke("overreach", {}, invocation_id="F" * 8)
    acts_after_first = len(session.invocation_acts("F" * 8))
    with pytest.raises(Refused) as again:
        d.invoke("overreach", {}, invocation_id="F" * 8)
    # Code, message, data, AND the invocation id all survive replay.
    assert again.value.refusal.code == first.value.refusal.code
    assert again.value.refusal.message == first.value.refusal.message
    assert dict(again.value.refusal.data) == dict(first.value.refusal.data)
    assert first.value.invocation_id == again.value.invocation_id == "F" * 8
    assert len(session.invocation_acts("F" * 8)) == acts_after_first  # not re-executed


def test_value_style_kernel_refusal_normalizes(rig):
    from beliefs.session import KernelRefusalValue
    d, _ = rig

    class FakeRunRefused:
        reason = "recipe-mismatch: fixture"

    def value_refusing_handler(ctx, writer, *, slug):
        raise KernelRefusalValue(FakeRunRefused())

    d._handlers["mint-claim"] = value_refusing_handler
    with pytest.raises(Refused) as e:
        d.invoke("mint-claim", {"slug": "v"}, invocation_id="H" * 8)
    assert e.value.refusal.code == "kernel-refused"
    assert e.value.refusal.data["kind"] == "FakeRunRefused"
    assert "recipe-mismatch" in e.value.refusal.data["reason"]
    assert e.value.invocation_id == "H" * 8


def test_value_style_kernel_refusal_carries_detail(rig):
    from beliefs.session import KernelRefusalValue
    d, _ = rig

    class FakeRunRefused:
        reason = "closure-unsupported"
        detail = "a1_coverage.pth imports 'sys', which is not a closure member"

    def value_refusing_handler(ctx, writer, *, slug):
        raise KernelRefusalValue(FakeRunRefused())

    d._handlers["mint-claim"] = value_refusing_handler
    with pytest.raises(Refused) as e:
        d.invoke("mint-claim", {"slug": "w"}, invocation_id="J" * 8)
    refusal = e.value.refusal
    assert refusal.data["reason"] == "closure-unsupported"
    assert refusal.data["detail"] == FakeRunRefused.detail
    assert FakeRunRefused.detail in refusal.message


def test_forged_kind_and_title_never_render(rig):
    d, _ = rig
    d._handlers["mint-claim"] = forging_handler
    out = d.invoke("mint-claim", {"slug": "forge"})
    # The identity pair is real, so the audit passes — but the canonical
    # ledger-rebuilt render shows the record's true kind and title.
    assert "FORGED TITLE" not in out.text and "verification" not in out.text
    assert "[proposition] proposition:forge" in out.text


def test_unknown_claim_type_fails_closed(rig, monkeypatch):
    """A claim outside the closed union must never execute as fresh."""
    d, session = rig
    monkeypatch.setattr(session, "claim_invocation", lambda *a, **k: object())
    with pytest.raises(TypeError):
        d.invoke("mint-claim", {"slug": "never"}, invocation_id="M" * 8)
    assert len(session.invocation_acts("M" * 8)) == 0  # nothing was written


def test_write_cursor_bound_to_its_command(rig):
    d, _ = rig
    small = Declaration("mint-claim", "fixture", MINT_CLAIM.write_class,
                        MIN_OUTPUT_BUDGET, MINT_CLAIM.inputs, (), Path("."))
    d._decls["mint-claim"] = small
    first = d.invoke("mint-claim", {"slug": "long-" + "n" * 200}, invocation_id="J" * 8)
    cursor = first.text.rsplit("cursor ", 1)[1].strip()
    with pytest.raises(Refused) as e:
        d.invoke("overreach", {}, cursor=cursor)  # a different command
    assert e.value.refusal.code == "input-mismatch"


def test_open_invocation_refuses_outcome_unknown(rig):
    d, session = rig
    # Simulate a crashed prior attempt: claimed and opened, never closed.
    from science.canonical import canonicalize, input_digest
    digest = input_digest(canonicalize(MINT_CLAIM, {"slug": "crashed"}))
    session.claim_invocation("G" * 8, "mint-claim", digest)
    with pytest.raises(Refused) as e:
        d.invoke("mint-claim", {"slug": "crashed"}, invocation_id="G" * 8)
    assert e.value.refusal.code == "outcome-unknown"


def test_write_cursor_rerenders_without_handler(rig):
    d, session = rig
    # A tiny declared budget forces truncation of even one record block.
    small = Declaration("mint-claim", "fixture", MINT_CLAIM.write_class,
                        MIN_OUTPUT_BUDGET, MINT_CLAIM.inputs, (), Path("."))
    d._decls["mint-claim"] = small
    first = d.invoke("mint-claim", {"slug": "long-" + "n" * 200}, invocation_id="D" * 8)
    assert "cursor" in first.text
    cursor = first.text.rsplit("cursor ", 1)[1].strip()
    d._handlers["mint-claim"] = lambda *a, **k: pytest.fail("write handler must not run on continuation")
    second = d.invoke("mint-claim", {}, cursor=cursor)
    assert second.text
