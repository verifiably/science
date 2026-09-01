"""Bounded, versioned cursor encoding (spec §7.3, §3.2 constants)."""
from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from typing import NoReturn

from science.refusal import INVOCATION_ID_RE, Refusal, Refused
from science.schema import MAX_NAME_BYTES, NAME_RE

_PREFIX = "scur1."
_BASE64URL_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_HEX32 = re.compile(r"^[0-9a-f]{32}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_U64_MAX = 2**64 - 1


@dataclass(frozen=True)
class ReadCursor:
    command: str
    input_digest: str
    report_digest: str
    block: int
    offset: int


@dataclass(frozen=True)
class WriteCursor:
    session_id: str
    invocation_id: str
    report_digest: str
    block: int
    offset: int


def _refuse() -> NoReturn:
    raise Refused(Refusal("unknown-cursor", "cursor does not parse"))


def _check_u64(value: object) -> int:
    if type(value) is not int or not 0 <= value <= _U64_MAX:
        _refuse()
    return value


def _unique_object(pairs: list[tuple[object, object]]) -> dict[object, object]:
    raw = dict(pairs)
    if len(raw) != len(pairs):
        raise ValueError("duplicate cursor key")
    return raw


def encode(cursor: ReadCursor | WriteCursor) -> str:
    if isinstance(cursor, ReadCursor):
        raw = {"f": "r", "c": cursor.command, "i": cursor.input_digest,
               "r": cursor.report_digest, "b": cursor.block, "o": cursor.offset}
    elif isinstance(cursor, WriteCursor):
        raw = {"f": "w", "s": cursor.session_id, "n": cursor.invocation_id,
               "r": cursor.report_digest, "b": cursor.block, "o": cursor.offset}
    else:
        raise TypeError("cursor must be a ReadCursor or WriteCursor")
    payload = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    return _PREFIX + base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode(token: str) -> ReadCursor | WriteCursor:
    if type(token) is not str:
        _refuse()
    try:
        token_bytes = token.encode("ascii")
    except UnicodeEncodeError:
        _refuse()
    if len(token_bytes) > MAX_CURSOR_BYTES:
        _refuse()
    if not token.startswith(_PREFIX):
        _refuse()
    body = token[len(_PREFIX):]
    if not _BASE64URL_RE.fullmatch(body):
        _refuse()
    try:
        payload = base64.b64decode(body + "=" * (-len(body) % 4), altchars=b"-_", validate=True)
        raw = json.loads(payload, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
        _refuse()
    if type(raw) is not dict:
        _refuse()
    form = raw.get("f")
    if form == "r":
        if set(raw) != {"f", "c", "i", "r", "b", "o"}:
            _refuse()
        command = raw["c"]
        if not (type(command) is str and NAME_RE.fullmatch(command)
                and len(command.encode()) <= MAX_NAME_BYTES):
            _refuse()
        if not (type(raw["i"]) is str and _HEX64.fullmatch(raw["i"])
                and type(raw["r"]) is str and _HEX64.fullmatch(raw["r"])):
            _refuse()
        return ReadCursor(command, raw["i"], raw["r"], _check_u64(raw["b"]), _check_u64(raw["o"]))
    if form == "w":
        if set(raw) != {"f", "s", "n", "r", "b", "o"}:
            _refuse()
        if not (type(raw["s"]) is str and _HEX32.fullmatch(raw["s"])
                and type(raw["n"]) is str and INVOCATION_ID_RE.fullmatch(raw["n"])
                and type(raw["r"]) is str and _HEX64.fullmatch(raw["r"])):
            _refuse()
        return WriteCursor(raw["s"], raw["n"], raw["r"], _check_u64(raw["b"]), _check_u64(raw["o"]))
    _refuse()


def _max_cursor_bytes() -> int:
    read_max = ReadCursor("x" * MAX_NAME_BYTES, "f" * 64, "f" * 64, _U64_MAX, _U64_MAX)
    write_max = WriteCursor("f" * 32, "z" * 64, "f" * 64, _U64_MAX, _U64_MAX)
    return max(len(encode(read_max).encode()), len(encode(write_max).encode()))


MAX_CURSOR_BYTES = _max_cursor_bytes()
MARKER_TEMPLATE = "\n… truncated at {budget} bytes; continue with cursor {cursor}\n"
_MARKER_FIXED = len(MARKER_TEMPLATE.format(budget=9 * 10**19, cursor="").encode())
MIN_OUTPUT_BUDGET = _MARKER_FIXED + MAX_CURSOR_BYTES + 4
