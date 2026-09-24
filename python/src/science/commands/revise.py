"""revise: a whole new revision naming its predecessors (spec §3.6)."""
from __future__ import annotations

from science.coordination import content_of, now, parse_address, parse_query_text, standing_tips
from science.refusal import Refusal, Refused
from science.report import Report, record_block

# The content fields each kind carries beyond name and body (coordination v2 contract).
_FIELDS = {
    "project": {"query"}, "question": {"query"}, "hypothesis": {"query"},
    "task": {"status", "depends"}, "decision": set(),
}


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def handle(ctx, writer, *, address, name=None, body=None, query=None, status=None, depends=None,
           clear_depends=None, repair=None) -> Report:
    # Canonicalization supplies each bool's declared `false`; the handler
    # default is None because the loader requires it of every optional input.
    parsed = parse_address(address, subordinate=address.count("/") == 1)
    if clear_depends and depends is not None:
        _refuse("give `depends` or `clear_depends`, not both")
    if clear_depends:
        depends = []
    given = {field: value for field, value in
             (("name", name), ("body", body), ("query", query), ("status", status), ("depends", depends))
             if value is not None}
    if not given:
        _refuse("revise names no field to change")
    tips = standing_tips(ctx, parsed)
    kind = tips[0].node.kind
    if kind not in _FIELDS:
        _refuse(f"{address} is a {kind}, which `revise` does not edit")
    lacking = sorted(set(given) - {"name", "body"} - _FIELDS[kind])
    if lacking:
        _refuse(f"a {kind} has no {', '.join(lacking)} field")
    if "query" in given:
        given["query"] = parse_query_text(given["query"])
    if "depends" in given:
        given["depends"] = list(given["depends"])
    if len(tips) > 1 and not repair:
        raise Refused(Refusal(
            "kernel-refused",
            f"{address} has {len(tips)} standing tips; revise it with `repair` to reconcile them",
            {"kind": "divergent-view", "tips": sorted(tip.node.uid for tip in tips)},
        ))
    if repair:
        missing = sorted(({"name", "body"} | _FIELDS[kind]) - set(given))
        if missing:
            _refuse(f"repair takes every field, since no one tip carries over; missing {', '.join(missing)}")
        content = dict(given)
    else:
        content = {**content_of(tips[0].node), **given}
    content.update(author=writer.actor, at=now())
    node = writer.revise_coordination(kind, parsed, predecessors=[tip.node.uid for tip in tips],
                                      content=content)
    return (record_block(node),)
