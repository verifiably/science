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


def parse_address(text: str, *, subordinate: bool):
    """An unpinned `coord:` address: `coord:<project>/<local>` when
    `subordinate`, else `coord:<project>`."""
    from beliefs.coordination import CoordinationAddress

    try:
        address = CoordinationAddress.parse(text)
    except ValueError as caught:
        _refuse(str(caught))
    if address.revision is not None:
        _refuse(f"{text!r} pins a revision; name the address unpinned")
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
