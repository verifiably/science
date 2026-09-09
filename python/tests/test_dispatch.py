from pathlib import Path

import pytest

from science.cursor import MIN_OUTPUT_BUDGET, ReadCursor, decode, encode
from science.dispatch import Dispatcher
from science.refusal import Refusal, Refused
from science.report import Text
from science.schema import Declaration, InputSpec, WriteClass


def make_decl(name="lots", budget=MIN_OUTPUT_BUDGET, inputs=(), write_class="read-only"):
    return Declaration(name, "p", WriteClass(write_class), budget, tuple(inputs), (), Path("."))


def lots_handler(ctx, **inputs):
    return tuple(Text(f"row {i} " + "x" * 60) for i in range(200))


def small_handler(ctx, *, corpus=None):
    return (Text(f"corpus={corpus}"),)


def build():
    decls = (
        make_decl("lots", inputs=(InputSpec("corpus", "string", False, "d", "d"),)),
        make_decl("small", inputs=(InputSpec("corpus", "string", False, "d"),)),
    )
    return Dispatcher(decls, {"lots": lots_handler, "small": small_handler}, read_context=object())


def cursor_from(text):
    return text.rsplit("cursor ", 1)[1].strip()


def test_unknown_command_refused_with_supplied_invocation_id():
    with pytest.raises(Refused) as caught:
        build().invoke("nope", {}, invocation_id="caller_id")
    assert caught.value.refusal.code == "unknown-command"
    assert caught.value.invocation_id == "caller_id"


def test_unknown_command_is_resolved_before_inputs_are_validated():
    with pytest.raises(Refused) as caught:
        build().invoke("nope", [], invocation_id="caller_id")
    assert caught.value.refusal.code == "unknown-command"
    assert caught.value.invocation_id == "caller_id"


def test_handler_refusal_id_is_bound_to_the_calling_invocation():
    dispatcher = build()

    def refusing_handler(ctx, **inputs):
        raise Refused(Refusal("kernel-refused", "handler refused"), "foreign_id")

    dispatcher._handlers["small"] = refusing_handler
    with pytest.raises(Refused) as caught:
        dispatcher.invoke("small", {}, invocation_id="caller_id")
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.invocation_id == "caller_id"


def test_read_invocation_renders_and_mints_id():
    out = build().invoke("small", {"corpus": "c1"})
    assert "corpus=c1" in out.text
    assert len(out.invocation_id) == 32


def test_pagination_round_trip_through_cursor():
    dispatcher = build()
    first = dispatcher.invoke("lots", {})
    assert "continue with cursor scur1." in first.text
    second = dispatcher.invoke("lots", {}, cursor=cursor_from(first.text))
    assert second.text and second.text != first.text


def test_continuation_reexecutes_the_read_handler():
    calls = []

    def handler(ctx, **inputs):
        calls.append(inputs)
        return lots_handler(ctx, **inputs)

    dispatcher = build()
    dispatcher._handlers["lots"] = handler
    first = dispatcher.invoke("lots", {})
    dispatcher.invoke("lots", {}, cursor=cursor_from(first.text))
    assert calls == [{"corpus": "d"}, {"corpus": "d"}]


def test_continuation_recanonicalizes_before_handler_execution():
    dispatcher = build()
    first = dispatcher.invoke("lots", {})
    dispatcher._handlers["lots"] = lambda *args, **kwargs: pytest.fail("handler must not run")
    with pytest.raises(Refused) as caught:
        dispatcher.invoke("lots", {"stray": "value"}, cursor=cursor_from(first.text),
                          invocation_id="caller_id")
    assert caught.value.refusal.code == "invalid-input"
    assert caught.value.invocation_id == "caller_id"


def test_stale_cursor_refused_when_world_moves():
    dispatcher = build()
    first = dispatcher.invoke("lots", {})
    dispatcher._handlers["lots"] = lambda ctx, **inputs: (Text("changed"),)
    with pytest.raises(Refused) as caught:
        dispatcher.invoke("lots", {}, cursor=cursor_from(first.text), invocation_id="caller_id")
    assert caught.value.refusal.code == "stale-cursor"
    assert caught.value.invocation_id == "caller_id"


def test_input_mismatch_on_altered_inputs():
    dispatcher = build()
    first = dispatcher.invoke("lots", {})
    with pytest.raises(Refused) as caught:
        dispatcher.invoke("lots", {"corpus": "other"}, cursor=cursor_from(first.text),
                          invocation_id="caller_id")
    assert caught.value.refusal.code == "input-mismatch"
    assert caught.value.invocation_id == "caller_id"


@pytest.mark.parametrize("invocation_id", ["has space", 7])
def test_bad_invocation_id_refused(invocation_id):
    with pytest.raises(Refused) as caught:
        build().invoke("small", {}, invocation_id=invocation_id)
    assert caught.value.refusal.code == "invalid-input"
    assert len(caught.value.invocation_id) == 32


def test_forged_mid_character_offset_refused():
    dispatcher = build()
    dispatcher._handlers["lots"] = lambda ctx, **inputs: (Text("é" * 4000),)
    first = dispatcher.invoke("lots", {})
    cursor = decode(cursor_from(first.text))
    forged = encode(ReadCursor(cursor.command, cursor.input_digest, cursor.report_digest,
                               cursor.block, cursor.offset + 1))
    with pytest.raises(Refused) as caught:
        dispatcher.invoke("lots", {}, cursor=forged, invocation_id="caller_id")
    assert caught.value.refusal.code == "stale-cursor"
    assert caught.value.invocation_id == "caller_id"


def test_malformed_cursor_refusal_carries_invocation_id():
    with pytest.raises(Refused) as caught:
        build().invoke("lots", {}, cursor="not-a-cursor", invocation_id="caller_id")
    assert caught.value.refusal.code == "unknown-cursor"
    assert caught.value.invocation_id == "caller_id"


def test_write_on_a_sessionless_surface_refuses_before_the_handler():
    """A CLI read invocation opens no session (spec §9.2); a write there is
    refused, not executed against a missing one."""
    executed = []
    write = make_decl("write", write_class="coordination")
    dispatcher = Dispatcher(
        (write,),
        {"write": lambda ctx, writer: executed.append(True) or ()},
        read_context=object(),
    )

    with pytest.raises(Refused) as caught:
        dispatcher.invoke("write", {}, invocation_id="caller_id")

    assert caught.value.refusal.code == "permit-exceeded"
    assert caught.value.invocation_id == "caller_id"
    assert not executed
