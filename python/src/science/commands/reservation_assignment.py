"""Mint a reservation assignment: a chain root, or the visible head's successor."""
from __future__ import annotations

from pathlib import Path

from beliefs import stored

from science.report import Report, record_block
from science.reservation import (
    RESERVATION_ASSIGNMENT,
    admit_assignment,
    kernel_reads,
    read_payload,
    require_unoccupied,
)

__all__ = ["handle"]


def handle(ctx, writer, *, payload: str) -> Report:
    with kernel_reads():
        document = read_payload(Path(payload), RESERVATION_ASSIGNMENT, actor=writer.actor)
        value = document.value
        require_unoccupied(ctx, value.id, RESERVATION_ASSIGNMENT.kind)
        node = stored.reservation_assignment_node(value, title=document.title)
        admit_assignment(ctx, value, node)
    if value.predecessor is None:
        return (record_block(writer.add(node)),)
    return (record_block(writer.supersede(node, of=value.predecessor)),)
