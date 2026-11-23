"""Validate a static plan before publishing a set or making a retrieval."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from beliefs.errors import IdentityError, MalformedRecord
from beliefs.holdings.acquire import LOCATOR_SCHEMES, ResourceRequest
from beliefs.holdings.records import require_store_relative_path, url_locator
from beliefs.identity import v1
from science.refusal import Refusal, Refused

__all__ = ["StaticPlan", "parse_plan"]


@dataclass(frozen=True)
class StaticPlan:
    source: dict
    seeds: tuple[ResourceRequest, ...]
    intervals: dict[str, int | Decimal]


def _object(pairs: list[tuple[str, object]]) -> dict:
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate plan field {key!r}")
        obj[key] = value
    return obj


def _fields(obj: object, required: set[str], optional: set[str]) -> dict:
    if not isinstance(obj, dict):
        raise ValueError("expected a plan object")
    missing = required.difference(obj)
    extra = obj.keys() - required - optional
    if missing or extra:
        raise ValueError(f"missing fields {sorted(missing)}, unexpected fields {sorted(extra)}")
    return obj


def _seed(row: object, path_field: str) -> ResourceRequest:
    item = _fields(row, {path_field, "url"}, {"expected"})
    name = item[path_field]
    try:
        require_store_relative_path(name)
        if not unicodedata.is_normalized("NFC", name):
            raise ValueError("member path must be NFC")
        location = url_locator(item["url"])
        if not location.url.startswith("https://"):
            raise ValueError("retrieval requires HTTPS")
        return ResourceRequest(name, location, expected=item.get("expected"))
    except (ValueError, MalformedRecord) as exc:
        raise ValueError(f"member {name!r}: {exc}") from exc


def _parse(raw: bytes, max_requests: int) -> StaticPlan:
    source = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_float=Decimal)
    if not isinstance(source, dict):
        raise ValueError("the plan must be an object")
    # The original input object, including producer metadata, must fit the log header.
    v1.encode(source)
    rich = "seeds" in source
    rows_key, path_field = ("seeds", "member") if rich else ("resources", "name")
    required = {"title", "locator", rows_key}
    if rich:
        required.update(("resource", "native", "parameters"))
    _fields(source, required, {"politeness"} if rich else set())
    if not isinstance(source["title"], str) or not source["title"]:
        raise ValueError("a plan needs a nonempty title")
    locator = source["locator"]
    scheme, _, rest = locator.partition(":") if isinstance(locator, str) else ("", "", "")
    if scheme not in LOCATOR_SCHEMES or not rest:
        raise ValueError("invalid empirical locator")
    if rich and (not isinstance(source["resource"], str) or not source["resource"]
                 or not isinstance(source["parameters"], dict)):
        raise ValueError("seed plans name a resource and supply a parameters object")
    rows = source[rows_key]
    if not isinstance(rows, list) or not rows:
        raise ValueError("a static plan needs at least one request")
    if len(rows) > max_requests:
        raise ValueError(f"plan exceeds max_requests ({max_requests})")
    seeds = tuple(_seed(row, path_field) for row in rows)
    names = {seed.name for seed in seeds}
    if len(names) != len(seeds):
        raise ValueError("duplicate member path")
    for name in names:
        parent = name
        while "/" in parent:
            parent = parent.rsplit("/", 1)[0]
            if parent in names:
                raise ValueError(f"member {parent!r} is also a directory")
    intervals = source.get("politeness", {})
    if not isinstance(intervals, dict):
        raise ValueError("politeness must map hosts to intervals in seconds")
    normalized = {}
    for host, seconds in intervals.items():
        if (not host or any(c in host for c in "/@?#") or host.lower() in normalized
                or type(seconds) not in (int, Decimal) or seconds < 0):
            raise ValueError(f"invalid service interval for {host!r}")
        normalized[host.lower()] = seconds
    return StaticPlan(source, seeds, normalized)


def parse_plan(raw: bytes, *, max_requests: int) -> StaticPlan:
    try:
        return _parse(raw, max_requests)
    except (ValueError, InvalidOperation, IdentityError, MalformedRecord, RecursionError) as exc:
        raise Refused(Refusal("invalid-input", f"Invalid acquisition plan: {exc}")) from exc
