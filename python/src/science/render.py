"""The one budgeted renderer (spec §7): budget, progress, audit."""
from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass

from science.cursor import MARKER_TEMPLATE
from science.report import RecordBlock, Report, serialize_block


class AuditViolation(Exception):
    pass


@dataclass(frozen=True)
class RenderedPage:
    text: str
    next_position: tuple[int, int] | None
    report_digest: str


def report_digest(report: Report) -> str:
    digest = hashlib.sha256()
    for block in report:
        piece = serialize_block(block).encode()
        digest.update(len(piece).to_bytes(8, "big"))
        digest.update(piece)
    return digest.hexdigest()


def audit_write_report(report: Report, minted: frozenset[tuple[str, str]]) -> None:
    for block in report:
        if not isinstance(block, RecordBlock):
            raise AuditViolation(f"write reports carry record blocks only, got {type(block).__name__}")
        if (block.uid, block.record_id) not in minted:
            raise AuditViolation(
                f"record ({block.uid!r}, {block.record_id!r}) was not minted by this invocation"
            )


def render_full(report: Report) -> str:
    return "".join(serialize_block(block) for block in report)


def _marker(
    budget: int,
    position: tuple[int, int],
    digest: str,
    cursor_for: Callable[[tuple[int, int], str], str],
) -> bytes:
    cursor = cursor_for(position, digest)
    if type(cursor) is not str:
        raise TypeError("cursor_for must return str")
    return MARKER_TEMPLATE.format(budget=budget, cursor=cursor).encode()


def _validate_position(pieces: list[bytes], position: tuple[int, int]) -> None:
    if (type(position) is not tuple or len(position) != 2
            or any(type(value) is not int for value in position)):
        raise ValueError("position must be a pair of integers")
    block, offset = position
    if block == len(pieces) and offset == 0:
        return
    if not 0 <= block < len(pieces) or not 0 <= offset < len(pieces[block]):
        raise ValueError("position is outside the report")
    if offset and pieces[block][offset] & 0xC0 == 0x80:
        raise ValueError("position splits a UTF-8 code point")


def _split(
    piece: bytes,
    *,
    block: int,
    offset: int,
    used: int,
    budget: int,
    digest: str,
    cursor_for: Callable[[tuple[int, int], str], str],
) -> tuple[bytes, tuple[int, int], bytes]:
    for take in range(min(len(piece) - 1, budget - used), 0, -1):
        if piece[take] & 0xC0 == 0x80:
            continue
        position = (block, offset + take)
        marker = _marker(budget, position, digest, cursor_for)
        if used + take + len(marker) <= budget:
            return piece[:take], position, marker
    raise ValueError("cursor marker leaves no room for report content")


def render_page(
    report: Report,
    *,
    budget: int,
    position: tuple[int, int] = (0, 0),
    cursor_for: Callable[[tuple[int, int], str], str],
) -> RenderedPage:
    if type(budget) is not int or budget < 0:
        raise ValueError("budget must be a non-negative integer")

    digest = report_digest(report)
    pieces = [serialize_block(block).encode() for block in report]
    _validate_position(pieces, position)
    block, offset = position
    remaining = b"" if block == len(pieces) else b"".join(
        [pieces[block][offset:]] + pieces[block + 1:]
    )
    if len(remaining) <= budget:
        return RenderedPage(remaining.decode(), None, digest)

    out: list[bytes] = []
    used = 0
    while block < len(pieces):
        piece = pieces[block][offset:]
        next_position = (block + 1, 0)
        marker = _marker(budget, next_position, digest, cursor_for)
        if used + len(piece) + len(marker) <= budget:
            out.append(piece)
            used += len(piece)
            block += 1
            offset = 0
            continue
        if out:
            marker = _marker(budget, (block, offset), digest, cursor_for)
            if used + len(marker) > budget:
                raise ValueError("cursor marker leaves no room for report content")
            return RenderedPage(b"".join(out).decode() + marker.decode(), (block, offset), digest)
        prefix, next_position, marker = _split(
            piece,
            block=block,
            offset=offset,
            used=used,
            budget=budget,
            digest=digest,
            cursor_for=cursor_for,
        )
        return RenderedPage(prefix.decode() + marker.decode(), next_position, digest)

    raise AssertionError("truncated report exhausted")
