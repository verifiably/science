"""reuse: the same-query mint, one act (spec §3.5, decision 7)."""
from __future__ import annotations

from science.coordination import content_of, now, parse_unpinned, resolve_one
from science.refusal import Refusal, Refused
from science.report import Report, record_block

_REUSABLE = frozenset({"question", "hypothesis"})


def handle(ctx, writer, *, source, name=None) -> Report:
    project = ctx.current_project()
    address = parse_unpinned(source)
    if address.local is None:
        raise Refused(Refusal("invalid-input",
                              f"{source!r} is a project; copy its query into `project --query` instead"))
    tip = resolve_one(ctx, address)
    if tip.kind not in _REUSABLE:
        raise Refused(Refusal("invalid-input", f"{source} is a {tip.kind}; `reuse` copies a question or hypothesis"))
    original = content_of(tip)
    body = f"Same query as {address.pinned(tip.uid)}.\n\n{original['body']}"
    content = {"name": name or original["name"], "body": body, "author": writer.actor, "at": now(),
               "query": original["query"]}
    return (record_block(writer.mint_coordination(tip.kind, project=project, content=content)),)
