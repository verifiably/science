"""note: a dated statement under the current project."""
from __future__ import annotations

from science.coordination import now, require_body
from science.lookup import unresolved_citations
from science.refusal import Refusal, Refused
from science.report import Report, record_block


def handle(ctx, writer, *, name, body, about=None) -> Report:
    project = ctx.current_project()
    require_body(body)
    ctx.coordination()
    unresolved = unresolved_citations(ctx, about or ())
    if unresolved:
        raise Refused(Refusal("invalid-input", "about names unresolved world records",
                              {"unresolved": unresolved}))
    content = {"name": name, "body": body, "author": writer.actor, "at": now()}
    if about is not None:
        content["about"] = list(dict.fromkeys(about))
    return (record_block(writer.mint_coordination("note", project=project, content=content)),)
