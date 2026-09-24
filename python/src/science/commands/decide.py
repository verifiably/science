"""decide: a decision and its reasoning under the current project (spec §3.4)."""
from __future__ import annotations

from science.coordination import now
from science.report import Report, record_block


def handle(ctx, writer, *, name, body) -> Report:
    project = ctx.current_project()
    content = {"name": name, "body": body, "author": writer.actor, "at": now()}
    return (record_block(writer.mint_coordination("decision", project=project, content=content)),)
