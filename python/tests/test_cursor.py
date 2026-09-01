import base64
import json

import pytest

from science.cursor import (
    MAX_CURSOR_BYTES, MIN_OUTPUT_BUDGET, ReadCursor, WriteCursor, decode, encode,
)
from science.refusal import Refused

U64_MAX = 2**64 - 1


def test_round_trip_both_forms():
    r = ReadCursor("status", "a" * 64, "b" * 64, 3, 17)
    w = WriteCursor("c" * 32, "x" * 64, "d" * 64, 0, 0)
    assert decode(encode(r)) == r
    assert decode(encode(w)) == w


def test_maximal_cursor_fits_published_bound():
    r = ReadCursor("x" * 32, "f" * 64, "f" * 64, U64_MAX, U64_MAX)
    w = WriteCursor("f" * 32, "z" * 64, "f" * 64, U64_MAX, U64_MAX)
    assert len(encode(r).encode()) <= MAX_CURSOR_BYTES
    assert len(encode(w).encode()) <= MAX_CURSOR_BYTES
    assert MIN_OUTPUT_BUDGET > MAX_CURSOR_BYTES


@pytest.mark.parametrize("junk", ["", "scur1.", "nope", "scur1.!!!!", "scur2.AAAA",
                                  "scur1." + "A" * 4096, None])
def test_garbage_refuses_unknown_cursor(junk):
    with pytest.raises(Refused) as e:
        decode(junk)
    assert e.value.refusal.code == "unknown-cursor"


def _hand_encode(raw: dict) -> str:
    return "scur1." + base64.urlsafe_b64encode(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()).decode().rstrip("=")


def test_field_bounds_enforced_on_decode():
    over_long = {"f": "r", "c": "s" * 33, "i": "a" * 64, "r": "b" * 64, "b": 1, "o": 1}
    with pytest.raises(Refused):
        decode(_hand_encode(over_long))


def test_boolean_position_refused():
    forged = {"f": "r", "c": "status", "i": "a" * 64, "r": "b" * 64, "b": True, "o": 0}
    with pytest.raises(Refused) as e:
        decode(_hand_encode(forged))
    assert e.value.refusal.code == "unknown-cursor"


@pytest.mark.parametrize("raw", [
    {"f": "r", "c": "status", "i": "a" * 64, "r": "b" * 64, "b": 0, "o": 0, "x": 1},
    {"f": "r", "c": "status", "i": "a" * 64, "r": "b" * 64, "b": 0},
    {"f": "w", "s": "a" * 32, "n": "run", "r": "b" * 64, "b": 0, "o": 0, "c": "status"},
])
def test_variant_keys_must_be_exact(raw):
    with pytest.raises(Refused) as e:
        decode(_hand_encode(raw))
    assert e.value.refusal.code == "unknown-cursor"


def test_budget_floor_refused_in_schema(tmp_path):
    from science.schema import DeclarationError, load_declaration
    toml = f'''\
schema_version = 1
name = "tiny"
purpose = "p"
write_class = "read-only"
output_budget = {MIN_OUTPUT_BUDGET - 1}
'''
    d = tmp_path / "tiny"
    d.mkdir()
    (d / "command.toml").write_text(toml)
    (d / "prompt.md").write_text("x")
    with pytest.raises(DeclarationError) as e:
        load_declaration(d, kind_acts={}, contract_kinds=frozenset())
    assert "MIN_OUTPUT_BUDGET" in str(e.value)
