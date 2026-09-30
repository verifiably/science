"""The one place a science launcher opens its attended session."""
from __future__ import annotations

from science.config import ScienceConfig, require_coordination_pinned
from science.refusal import Refusal, Refused


def open_session(config: ScienceConfig, project=None):
    """Open the configured single corpus as the writer and optional read mount.

    `project`, an unpinned project address, is the initial selection: the
    kernel resolves and pins it into `session-open` before the session
    directory exists, so one that names no standing project refuses here."""
    from beliefs.errors import ProjectNotResolvable, SessionRefused
    from beliefs.session import open_attended_session

    if len(config.world.corpus_roots) != 1:
        raise SessionRefused(
            f"a session needs exactly one corpus root; the config names {len(config.world.corpus_roots)}"
        )
    (root,) = config.world.corpus_roots
    if config.coordination is not None:
        require_coordination_pinned(config)
    elif project is not None:
        raise Refused(Refusal(
            "invalid-input", "coordination = false in this configuration; no project can be selected"))
    try:
        return open_attended_session(
            config.world, config.operations_root, write_root=root, profile=config.profile,
            mounts={root: config.profile} if config.coordination is not None else None,
            store_root=config.store_root, project=project,
        )
    except ProjectNotResolvable as caught:
        raise Refused(Refusal(
            "unknown-project", f"the initial project does not resolve: {caught}",
            {"tips": list(caught.tips)} if caught.tips else {},
        )) from None
