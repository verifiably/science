"""What a minted view selects (milestone design §5.6 R1/R3, M2).

Only a query read back from its record is evaluated: the minted record is resolved by
its returned address, its stored projection is compared with the input file's, and
the stored query is evaluated over the current epoch's world view.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


def _sha256(text: str | bytes) -> str:
    return hashlib.sha256(text.encode() if isinstance(text, str) else text).hexdigest()


def projection_sha256(query: dict) -> str:
    from beliefs.view_query import parse_view_query

    return _sha256(json.dumps(parse_view_query(query).projection(), sort_keys=True, separators=(",", ":")))


def resolved_tip(cfg, address: str):
    from science.config import ReadContext
    from science.coordination import parse_unpinned, resolve_one

    return resolve_one(ReadContext.open(cfg), parse_unpinned(address))


def equivalence(cfg, address: str, input_path: Path) -> dict:
    """The stored record's query projection against the input file's."""
    from science.coordination import query_digest

    tip = resolved_tip(cfg, address)
    stored = query_digest(tip)
    given = projection_sha256(yaml.safe_load(input_path.read_text()))
    return {"address": address, "revision": tip.uid, "name": tip.title,
            "raw_input_sha256": _sha256(input_path.read_bytes()),
            "input_projection_sha256": given, "stored_projection_sha256": stored, "equivalent": given == stored}


def read_view(cfg, key: str, address: str, input_path: Path) -> dict:
    from beliefs.root import open_world_read
    from beliefs.view_query import stored_query
    from beliefs.world.read import current_epoch
    from beliefs.world.selection import evaluate_query
    from beliefs.world.view import open_world_view

    row = {"key": key, **equivalence(cfg, address, input_path)}
    tip = resolved_tip(cfg, address)
    world = open_world_read(cfg.world)
    published = current_epoch(world)
    selection = evaluate_query(open_world_view(world, published), stored_query(tip))
    projection = selection.projection()
    return {**row, "epoch": published.packaging_identity, "selected": projection["selected"],
            "contributing": projection["contributing"], "absent": projection["absent"],
            "unresolved": projection["unresolved"], "complete": selection.complete}
