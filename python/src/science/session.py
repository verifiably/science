"""The one place a science launcher opens its attended session."""
from __future__ import annotations

from science.config import ScienceConfig, mount_profiles, require_write_root_pins
from science.refusal import Refusal, Refused


def open_session(config: ScienceConfig, project=None):
    """Open the configured write root as the writer, with every configured root
    mounted under its own manifest's profile when coordination is on.

    `project`, an unpinned project address, is the initial selection: the
    kernel resolves and pins it into `session-open` before the session
    directory exists, so one that names no standing project refuses here."""
    from beliefs.errors import ProjectNotResolvable
    from beliefs.session import open_attended_session

    require_write_root_pins(config)
    if config.coordination is None and project is not None:
        raise Refused(Refusal(
            "invalid-input", "coordination = false in this configuration; no project can be selected"))
    try:
        return open_attended_session(
            config.world, config.operations_root, write_root=config.write_root, profile=config.profile,
            mounts=mount_profiles(config) if config.coordination is not None else None,
            store_root=config.store_root, project=project,
        )
    except ProjectNotResolvable as caught:
        raise Refused(Refusal(
            "unknown-project", f"the initial project does not resolve: {caught}",
            {"tips": list(caught.tips)} if caught.tips else {},
        )) from None
