"""The one place a science launcher opens its attended session."""
from __future__ import annotations

from science.config import ScienceConfig, require_coordination_pinned


def open_session(config: ScienceConfig):
    """Open the configured single corpus as the writer and optional read mount."""
    from beliefs.errors import SessionRefused
    from beliefs.session import open_attended_session

    if len(config.world.corpus_roots) != 1:
        raise SessionRefused(
            f"a session needs exactly one corpus root; the config names {len(config.world.corpus_roots)}"
        )
    (root,) = config.world.corpus_roots
    if config.coordination is not None:
        require_coordination_pinned(config)
    return open_attended_session(
        config.world, config.operations_root, write_root=root, profile=config.profile,
        mounts={root: config.profile} if config.coordination is not None else None,
        store_root=config.store_root,
    )
