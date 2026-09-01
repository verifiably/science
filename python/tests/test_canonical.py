import re

import pytest

from science.canonical import canonicalize, input_digest
from science.refusal import CODES, INVOCATION_ID_RE, Refusal, Refused, mint_token
from science.schema import Declaration, InputSpec, WriteClass
from pathlib import Path


def decl(*inputs: InputSpec) -> Declaration:
    return Declaration("t", "p", WriteClass("read-only"), 4096, tuple(inputs), (), Path("."))


def test_defaults_applied_and_absent_dropped():
    d = decl(InputSpec("a", "string", False, "d", default="x"),
             InputSpec("b", "int", False, "d"))
    assert canonicalize(d, {}) == {"a": "x"}


def test_unknown_and_wrong_type_refused():
    d = decl(InputSpec("a", "int", True, "d"))
    with pytest.raises(Refused) as e:
        canonicalize(d, {"a": 1, "zz": 2})
    assert e.value.refusal.code == "invalid-input"
    with pytest.raises(Refused):
        canonicalize(d, {"a": "not-int"})
    with pytest.raises(Refused):  # missing required
        canonicalize(d, {})
    with pytest.raises(Refused):  # bool is not an int
        canonicalize(d, {"a": True})


def test_subclasses_are_refused_at_closed_input_boundary():
    class StringSubclass(str):
        pass

    class IntSubclass(int):
        pass

    class ListSubclass(list):
        pass

    for spec, value in (
        (InputSpec("a", "string", True, "d"), StringSubclass("x")),
        (InputSpec("a", "int", True, "d"), IntSubclass(1)),
        (InputSpec("a", "list-of-string", True, "d"), ListSubclass(["x"])),
        (InputSpec("a", "list-of-string", True, "d"), [StringSubclass("x")]),
    ):
        with pytest.raises(Refused):
            canonicalize(decl(spec), {"a": value})


def test_explicit_null_is_refused_not_absent():
    d = decl(InputSpec("a", "string", False, "d", default="x"))
    with pytest.raises(Refused) as e:
        canonicalize(d, {"a": None})  # must NOT silently become the default
    assert e.value.refusal.code == "invalid-input"


def test_enum_and_list_validation():
    d = decl(InputSpec("m", "enum", True, "d", choices=("x", "y")),
             InputSpec("l", "list-of-string", False, "d"))
    assert canonicalize(d, {"m": "x", "l": ["a", "b"]}) == {"l": ["a", "b"], "m": "x"}
    with pytest.raises(Refused):
        canonicalize(d, {"m": "z"})
    with pytest.raises(Refused):
        canonicalize(d, {"m": "x", "l": [1]})


def test_digest_stable_and_order_free():
    d = decl(InputSpec("a", "string", True, "d"), InputSpec("b", "int", False, "d"))
    one = input_digest(canonicalize(d, {"a": "v", "b": 2}))
    two = input_digest(canonicalize(d, {"b": 2, "a": "v"}))
    assert one == two and re.fullmatch(r"[0-9a-f]{64}", one)


def test_refusal_shapes():
    assert "kernel-refused" in CODES and len(CODES) == 8
    r = Refusal("invalid-input", "bad", {"field": "a"})
    assert Refused(r).refusal is r
    assert INVOCATION_ID_RE.fullmatch("A-z_09")
    assert not INVOCATION_ID_RE.fullmatch("x" * 65) and not INVOCATION_ID_RE.fullmatch("a b")
    assert re.fullmatch(r"[0-9a-f]{32}", mint_token())
