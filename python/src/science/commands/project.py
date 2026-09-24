"""project: mint a project, the root of its own address space (spec §3.1)."""
from __future__ import annotations

from science.coordination import now, parse_query_text
from science.report import Report, record_block


def handle(ctx, writer, *, name, query, body=None) -> Report:
    content = {"name": name, "body": body or "", "author": writer.actor, "at": now(),
               "query": parse_query_text(query)}
    node = writer.mint_coordination("project", project=None, content=content)
    return (record_block(node),)
