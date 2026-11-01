"""recheck: re-check one store location through the kernel's session route,
settling an unmatched holdings intent (sci-409235)."""
from __future__ import annotations

from beliefs import stored
from beliefs.errors import MalformedRecord
from beliefs.holdings.records import HoldingsObservation, StoreLocator
from beliefs.report import PublishedObservation

from science.config import configured_stores
from science.refusal import Refusal, Refused
from science.report import Report, record_block

INSTRUMENT = "science/recheck.v1"


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def parse_store_location(text: str) -> StoreLocator:
    """The canonical spelling `store:<id>:<path>`, exactly as given: a padded
    or otherwise altered locator would name a different path, so nothing is
    stripped."""
    if text != text.strip() or not text.isprintable():
        _refuse(f"location {text!r} carries surrounding whitespace or control characters; "
                "give it exactly as the blocked row names it")
    if text.startswith(("url:", "https://", "http://")):
        _refuse(f"location {text!r} is a URL; recheck re-checks store locations only")
    scheme, sep, rest = text.partition(":")
    store_id, sep2, relative = rest.partition(":")
    if scheme != "store" or not sep or not sep2:
        _refuse(f"location {text!r} is not a store locator, store:<store id>:<relative path>")
    try:
        return StoreLocator(store_id, relative)
    except MalformedRecord as caught:
        _refuse(f"location {text!r}: {caught}")


def standing_at(views, locator: StoreLocator) -> tuple[HoldingsObservation, ...]:
    """Every holdings observation at the location in any view, so the new one
    supersedes an inherited head as well as the write corpus's own."""
    canonical = locator.canonical()
    found = {}
    for _, view in views:
        for node in view.iter_stored():
            if node.kind != "holdings-observation":
                continue
            value = stored.holdings_observation_value(node)
            if value.location.canonical() == canonical:
                found[value.identity()] = value
    return tuple(found[identity] for identity in sorted(found))


def _bind(ctx, writer, locator: StoreLocator) -> None:
    if locator.store_id == writer.store_id:
        return
    stores = configured_stores(ctx.config)
    root = stores.get(locator.store_id)
    if root is not None:
        _refuse(f"{locator.canonical()} is in the read store {root}; re-check it under a recovery "
                f"configuration whose store_root is {root}, with the same write_root and the current "
                "store_root moved to read_store_roots")
    _refuse(f"{locator.canonical()} names store {locator.store_id}, which this configuration does not "
            f"hold; configured stores: {', '.join(sorted(stores))}")


def _load(view, ref: str):
    if not view.holds(ref):
        raise RuntimeError(f"{ref}: the re-check minted a record the write corpus does not hold")
    return view.get(ref)


def handle(ctx, writer, *, location) -> Report:
    locator = parse_store_location(location)
    _bind(ctx, writer, locator)
    standing = standing_at(ctx.read_views(), locator)
    # --- the one operation: the kernel's re-check ----------------------------
    outcome = writer.recheck((locator,), instrument=INSTRUMENT,
                             standing={locator.canonical(): standing} if standing else None)
    view = ctx.write_view()
    blocks = [record_block(_load(view, entry.outcome.ref)) for entry in outcome.entries
              if isinstance(entry.outcome, PublishedObservation)]
    return (*blocks, record_block(_load(view, outcome.report_ref)))
