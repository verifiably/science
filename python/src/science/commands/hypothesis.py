"""hypothesis: a view minted under the current project (spec §3.2)."""
from __future__ import annotations

from science.coordination import now, parse_query_text
from science.report import Report, record_block


def handle(ctx, writer, *, name, query, body=None) -> Report:
    project = ctx.current_project()
    content = {"name": name, "body": body or "", "author": writer.actor, "at": now(),
               "query": parse_query_text(query)}
    return (record_block(writer.mint_coordination("hypothesis", project=project, content=content)),)
