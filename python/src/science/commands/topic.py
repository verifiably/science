"""topic: a complete synthesis under the current project."""
from __future__ import annotations

from science.coordination import now, parse_query_text, require_body, require_topic_query
from science.report import Report, record_block


def handle(ctx, writer, *, name, body, query) -> Report:
    project = ctx.current_project()
    require_body(body)
    ctx.coordination()
    parsed = parse_query_text(query)
    require_topic_query(ctx, parsed)
    content = {"name": name, "body": body, "author": writer.actor, "at": now(), "query": parsed}
    return (record_block(writer.mint_coordination("topic", project=project, content=content)),)
