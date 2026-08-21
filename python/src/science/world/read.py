"""The read surface over a published epoch: opening one, and selecting one.

Specification §8.1 gives a world two ways to name a publication and only two.
`open_epoch` names one **explicitly**, by the packaging identity of the bytes
it means. `current_epoch` follows the operational pointer and then performs the
same open — no weaker validation, no different result type, no separate path
into the carrier.

**`current` is operational convenience and nothing else.** It exists so a human
or a script can say "the one this world last published" without carrying a
digest around. It is not a belief input and it is not an identity: an API that
accepts belief inputs accepts an explicit producer-snapshot identity, never the
word or the function `current` (§8.1). Nothing in this module is reachable from
belief, and the reason is structural rather than a convention — a snapshot is
retrieved by its own identity from whichever retained epoch carries it.

**One lock, taken before the recovery barrier.** Both acts acquire
`_WorldState.lock` first, cross the recovery barrier second, and hold the lock
through every carrier read and every validation. Publication holds the same
lock across its whole transaction, so a reader arriving mid-publication waits
and then sees the finished epoch: it cannot mistake an applied prefix for a
malformed carrier. The lock is not reentrant, which is why `current_epoch`
reaches `epoch._locked_open_epoch` directly rather than calling `open_epoch` —
re-entry would not be a style question here, it would deadlock.

**Why this is a module and not more of `epoch.py`.** Specification §3 pins the
world package's layout, and the two halves it separates are the carrier — what
an epoch *is*, how it is derived and how it is published — and the reads a
world performs *through* one. Task 10's receipt validation, address resolution
and coreference queries land here, beside the opening they all begin with.
"""

from __future__ import annotations

from science.errors import EpochUnknown

# Module form for the same reason `epoch` imports `rules` that way: every use
# below is at call time, so no import order can bind a partially initialised
# name. Nothing here may touch `epoch.<name>` at module level.
from science.world import epoch, registry

__all__ = ["current_epoch", "open_epoch"]


def open_epoch(world: registry.World, packaging_identity: str) -> epoch.Epoch:
    """Open the one epoch these publication bytes name.

    The complete §8.1 check: the exact member set, every closed document, and
    the recomputed packaging identity. `EpochMalformed` for a carrier that
    fails any of it, `EpochUnknown` for a name this world retains nothing
    under. A receipt that parses and then violates §7.5's contract is *not* a
    carrier failure and opens (§8.2).
    """
    with world._state.lock:
        world._chain_head(world.config.world_root)
        return epoch._locked_open_epoch(world.config.world_root, packaging_identity)


def current_epoch(world: registry.World) -> epoch.Epoch:
    """Open whichever epoch `epochs/current` presently names.

    One acquisition of the world lock covers the barrier, the pointer read and
    the open, so the epoch returned is the one the pointer named at a single
    moment rather than at two. A world that has published nothing has no
    current epoch, and says so: `EpochUnknown`, never an invented answer.
    """
    with world._state.lock:
        world._chain_head(world.config.world_root)
        named = epoch._locked_current_identity(world.config.world_root)
        if named is None:
            raise EpochUnknown(
                f"{world.config.world_root / 'epochs' / epoch.CURRENT_POINTER}: "
                "this world has published no epoch, so it selects none"
            )
        return epoch._locked_open_epoch(world.config.world_root, named)
