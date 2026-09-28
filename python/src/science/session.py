"""The one place a science launcher opens its attended session."""
from __future__ import annotations

from science.config import ScienceConfig
from science.refusal import Refusal, Refused


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
        _require_coordination_pinned(config)
    return open_attended_session(
        config.world, config.operations_root, write_root=root, profile=config.profile,
        mounts={root: config.profile} if config.coordination is not None else None,
        store_root=config.store_root,
    )


def _require_coordination_pinned(config: ScienceConfig) -> None:
    """Spec §6: a configuration that asks for coordination of a corpus whose
    manifest does not pin it is refused by name. The kernel would refuse the
    same state as a bare pin mismatch, which the CLI can only render as an
    internal error; every pre-coordination configuration upgraded with
    `coordination = N` reaches this. A root whose manifest is missing or
    malformed is left to the kernel's own named `SessionRefused`."""
    from beliefs.errors import ManifestMalformed, ManifestMissing
    from beliefs.profile import shipped_coordination
    from beliefs.world import load_manifest

    namespace = shipped_coordination(config.coordination).namespace
    wanted = f"{namespace}:{config.profile.activated_contracts[namespace]}"
    for root in config.world.corpus_roots:
        try:
            pinned = load_manifest(root).profile.domains.get(namespace)
        except (ManifestMissing, ManifestMalformed):
            continue
        if pinned is None:
            raise Refused(Refusal(
                "invalid-input",
                f"the configuration asks for coordination the corpus at {root} does not pin; "
                "set `coordination = false` for a corpus adopted before coordination",
            ))
        if pinned != wanted:
            raise Refused(Refusal(
                "invalid-input",
                f"the corpus at {root} pins coordination contract {pinned}, not the one "
                f"`coordination = {config.coordination}` compiles; set `coordination` to the version it pins",
            ))
