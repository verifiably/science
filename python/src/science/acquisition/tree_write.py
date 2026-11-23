"""Write a validated local tree using the current heads at its store location."""

from beliefs.holdings.boundary import InconclusiveAttempt, recheck_tree, tree_write
from beliefs.holdings.records import StoreTreeLocator
from beliefs.tree import tree_digest
from science.acquisition.standing import seal_heads
from science.refusal import Refusal, Refused

__all__ = ["hold_tree"]


def hold_tree(ctx, writer, instrument, tree, members):
    location = StoreTreeLocator(writer.store_id, tree_digest(tree).split(":")[1])
    key = location.canonical()
    heads, unsettled = seal_heads(ctx, [key])
    act = writer.holdings_context(instrument=instrument)
    standing = heads[key]
    if key in unsettled:
        observed = recheck_tree(act, location, standing=standing)
        if isinstance(observed, InconclusiveAttempt):
            raise Refused(Refusal("invalid-input", f"{key}: tree re-check was inconclusive"))
        standing = (observed.record,)
    return tree_write(act, location, tree, members, standing=standing)
