"""The one place a science launcher opens its attended session."""
from __future__ import annotations

from science.config import ScienceConfig


def open_session(config: ScienceConfig):
    """The kernel requires the coordination profile to equal the writer's in
    compiled identity (`require_profile_compatible`), so with coordination on
    the one compiled profile is passed as both."""
    from beliefs.session import open_attended_session

    return open_attended_session(
        config.world, config.operations_root, profile=config.profile,
        coordination=config.profile if config.coordination is not None else None,
        store_root=config.store_root,
    )
