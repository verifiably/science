"""Resolve the heads from one reduction in the corresponding mounted read views."""

from beliefs import stored
from science.holdings import reduced_heads
from science.refusal import Refusal, Refused

__all__ = ["seal_heads"]


def seal_heads(ctx, locations):
    views = ctx.read_views()
    active, blocked = reduced_heads(ctx.world, frozenset(cid for cid, _ in views))
    heads = {loc: [] for loc in locations}
    unsettled = set()

    def include(row):
        loc = row["location"]
        if loc not in heads:
            return
        ref = "holdings-observation:" + row["head"]
        found = [stored.holdings_observation_value(view.get(ref)) for _, view in views if view.holds(ref)]
        if not found or any(v != found[0] for v in found) or found[0].location.canonical() != loc:
            raise Refused(Refusal("invalid-input", f"cannot resolve standing {ref} at {loc}"))
        heads[loc].append(found[0])

    for row in active:
        include(row)
    for entry in blocked:
        if entry["location"] in heads and "unsettled" in entry["reasons"]:
            unsettled.add(entry["location"])
        for row in entry["heads"]:
            include(row)
    return {loc: tuple(values) for loc, values in heads.items()}, frozenset(unsettled)
