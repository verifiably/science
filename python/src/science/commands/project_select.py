"""project-select: the session's current project (spec §3.7)."""
from __future__ import annotations

from science.coordination import resolve_one, resolve_project_ref
from science.refusal import Refusal, Refused
from science.report import Report, SelectionBlock


def handle(ctx, port, *, target=None, clear=None) -> Report:
    # Canonicalization supplies `clear`'s declared false; the handler default
    # is None because the loader requires it of every optional input.
    ctx.coordination()  # `coordination = false` refuses by name, a clear included
    if (target is None) == (not clear):
        raise Refused(Refusal("invalid-input", "give exactly one of `target` and `clear`"))
    if clear:
        port.select(None)
        return (SelectionBlock(None, None),)
    address = resolve_project_ref(ctx, target)
    resolve_one(ctx, address)  # a divergent project refuses here, naming every tip
    pinned = port.select(address)
    return (SelectionBlock(str(pinned), ctx.coordination().resolve(pinned).title),)
