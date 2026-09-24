"""task: an open task under the current project (spec §3.3)."""
from __future__ import annotations

from science.coordination import now
from science.report import Report, record_block


def handle(ctx, writer, *, name, body=None, depends=None) -> Report:
    project = ctx.current_project()
    content = {"name": name, "body": body or "", "author": writer.actor, "at": now(),
               "status": "open", "depends": list(depends or ())}
    return (record_block(writer.mint_coordination("task", project=project, content=content)),)
