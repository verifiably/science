"""Mint one exposure event from a strict payload, after every check that needs no act."""
from __future__ import annotations

from pathlib import Path

from beliefs import stored

from science.report import Report, record_block
from science.reservation import EXPOSURE_EVENT, admit_event, kernel_reads, read_payload, require_unoccupied

__all__ = ["handle"]


def handle(ctx, writer, *, payload: str) -> Report:
    with kernel_reads():
        document = read_payload(Path(payload), EXPOSURE_EVENT, actor=writer.actor)
        require_unoccupied(ctx, document.value.id, EXPOSURE_EVENT.kind)
        node = stored.exposure_event_node(document.value, title=document.title)
        admit_event(ctx, document.value, node)
    return (record_block(writer.add(node)),)
