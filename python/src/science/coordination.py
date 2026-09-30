"""Shared reads and input parsing for the coordination commands (spec §3)."""
from __future__ import annotations

from datetime import UTC, datetime

import yaml

from science.refusal import Refusal, Refused

# Stored in the coordination facet beside the content fields; never content.
_ADDRESS_FIELDS = frozenset({"project", "local"})


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_query_text(text: str) -> dict:
    """YAML (JSON is a subset) that must be a mapping; the kernel validates the
    query language and the profile's world kinds at the act."""
    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError as caught:
        _refuse(f"query is not YAML or JSON: {caught}")
    if not isinstance(value, dict):
        _refuse("query must be a mapping with `version` and `clauses`")
    return value


def parse_unpinned(text: str):
    """An unpinned `coord:` address of either shape."""
    from beliefs.coordination import CoordinationAddress

    try:
        address = CoordinationAddress.parse(text)
    except ValueError as caught:
        _refuse(str(caught))
    if address.revision is not None:
        _refuse(f"{text!r} pins a revision; name the address unpinned")
    return address


def parse_address(text: str, *, subordinate: bool):
    """An unpinned `coord:` address: `coord:<project>/<local>` when
    `subordinate`, else `coord:<project>`."""
    address = parse_unpinned(text)
    if subordinate and address.local is None:
        _refuse(f"{text!r} is a project address; this input takes coord:<project>/<local>")
    if not subordinate and address.local is not None:
        _refuse(f"{text!r} is a subordinate address; this input takes coord:<project>")
    return address


def content_of(node) -> dict:
    """The full content a revision was minted with: name, body and every facet
    field except the address. `query` is the stored canonical projection, which
    the kernel accepts back as-is."""
    from beliefs import stored

    facet = node.facets[stored.COORDINATION_FACET]
    return {"name": node.title, "body": node.body,
            **{field: value for field, value in facet.items() if field not in _ADDRESS_FIELDS}}


def standing_tips(ctx, address):
    """Every standing tip of `address`; refuses when the address was never minted."""
    tips = ctx.coordination().tips(address)
    if not tips:
        _refuse(f"{address} names no coordination record in the configured corpora")
    return tips


def resolve_one(ctx, address):
    """The address's one standing tip, or refuse — `divergent-view` naming every tip."""
    from beliefs.coordination import CoordinationRefused

    resolved = ctx.coordination().resolve(address)
    if resolved is None:
        _refuse(f"{address} names no coordination record in the configured corpora")
    if isinstance(resolved, CoordinationRefused):
        raise Refused(Refusal(
            "kernel-refused",
            f"{address} has {len(resolved.tips)} standing tips; revise it with `repair` to reconcile them",
            {"kind": resolved.reason, "tips": list(resolved.tips)},
        ))
    return resolved


def tip_nodes(resolver, resolved) -> tuple:
    """The standing tips behind one `standing()` or `resolve()` answer: none,
    the one tip, or every tip of a divergent address."""
    from beliefs.coordination import CoordinationRefused

    if resolved is None:
        return ()
    if isinstance(resolved, CoordinationRefused):
        return tuple(resolver.revision(uid) for uid in resolved.tips)
    return (resolved,)


def query_digest(node) -> str:
    """sha256 over a view revision's canonical query projection: what tells two
    projects that share a name apart."""
    import hashlib
    import json

    from beliefs.view_query import stored_query

    payload = json.dumps(stored_query(node).projection(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def resolve_project_ref(ctx, text: str):
    """A project's name or `coord:<project>` address, as its unpinned address
    (spec §3.7, §5.2). A name matches a standing tip's name exactly; names are
    content, so none refuses `unknown-project` and two refuse `ambiguous-project`.
    A divergent project's address is returned: whoever reads through it refuses."""
    from beliefs.coordination import CoordinationRefused

    resolver = ctx.coordination()
    if text.startswith("coord:"):
        address = parse_address(text, subordinate=False)
        resolved = resolver.resolve(address)
        if resolved is None or (not isinstance(resolved, CoordinationRefused) and resolved.kind != "project"):
            raise Refused(Refusal("unknown-project", f"{text} names no standing project"))
        return address
    if not text:
        _refuse("a project is named by its name or its coord:<project> address")
    candidates = []
    for address, resolved in resolver.standing("project").items():
        named = [node for node in tip_nodes(resolver, resolved) if node.title == text]
        if named:
            candidates.append((address, named[0]))
    if not candidates:
        raise Refused(Refusal("unknown-project", f"no standing project is named {text!r}"))
    if len(candidates) > 1:
        raise Refused(Refusal(
            "ambiguous-project",
            f"{len(candidates)} projects are named {text!r}; name one by its address",
            {"candidates": [{"address": str(address), "query_digest": query_digest(node)}
                            for address, node in candidates]},
        ))
    return candidates[0][0]


def selected_project(ctx):
    """The selection's one standing tip, or None with nothing selected. A
    selection that no longer resolves to a project refuses `unknown-project`;
    one that diverged refuses `divergent-view` naming every tip (spec §7)."""
    from beliefs.coordination import CoordinationRefused

    if ctx.selection is None:
        return None
    resolved = ctx.coordination().resolve(ctx.selection)
    if isinstance(resolved, CoordinationRefused):
        raise Refused(Refusal(
            "kernel-refused",
            f"{ctx.selection} has {len(resolved.tips)} standing tips; reconcile them with `revise --repair`, "
            "or clear the selection with `project-select --clear`",
            {"kind": resolved.reason, "tips": list(resolved.tips)},
        ))
    if resolved is None or resolved.kind != "project":
        raise Refused(Refusal("unknown-project", f"{ctx.selection} names no standing project"))
    return resolved


def live_selection(ctx, project):
    """What the project's query denotes over the world's current state (beliefs
    live-query design): attention, never an epoch's answer. The kernel's
    refusals arrive as `kernel-refused`, its class name in `data.kind`."""
    from beliefs.errors import (
        AddressMapConflict, BuildContended, CaptureDrift, ResolutionRefused, SelectionRefused,
    )
    from beliefs.view_query import stored_query
    from beliefs.world import live

    try:
        return live.evaluate_live_query(ctx.world, stored_query(project))
    except SelectionRefused as caught:
        raise Refused(Refusal(
            "kernel-refused", str(caught),
            {"kind": "SelectionRefused", "reason": caught.reason, "refs": list(caught.refs)},
        )) from None
    except (AddressMapConflict, BuildContended, CaptureDrift, ResolutionRefused) as caught:
        raise Refused(Refusal("kernel-refused", str(caught), {"kind": type(caught).__name__})) from None
