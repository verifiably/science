"""The one place a science launcher opens its attended session."""
from __future__ import annotations

from science.config import ScienceConfig
from science.refusal import Refusal, Refused


def open_session(config: ScienceConfig):
    """The kernel requires the coordination profile to equal the writer's in
    compiled identity (`require_profile_compatible`), so with coordination on
    the one compiled profile is passed as both."""
    from beliefs.session import open_attended_session

    if config.coordination is not None:
        _require_coordination_pinned(config)
    return open_attended_session(
        config.world, config.operations_root, profile=config.profile,
        coordination=config.profile if config.coordination is not None else None,
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
