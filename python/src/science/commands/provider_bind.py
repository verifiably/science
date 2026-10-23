"""provider-bind: bind a provider's location to the world its publication claims, when the reader passes that
same world id (commons spec §4.4 layer 3). The `bound` sharing line is the evidence; the registry's binding
follows it, and `sharing.replay` restores a binding the line outlived."""
from __future__ import annotations

import shutil

from beliefs.session.ledger import SharingEvidence

from science import publication
from science.refusal import Refusal, Refused
from science.report import Report, pin_block
from science.sharing import ProviderBinding, SharingRegistry, replay


def handle(ctx, writer, *, location, corpus_id, world) -> Report:
    config = ctx.config
    publication.require_id(corpus_id, "corpus_id")
    publication.require_id(world, "world")
    if world == config.world.world_id:
        raise Refused(Refusal("invalid-input", f"world {world} is this world's own id: a provider is another world"))
    destination = publication.parse_destination(location)
    if config.sharing_root is None:
        raise Refused(Refusal("invalid-input", "provider-bind records a binding in the sharing registry; "
                                               "configure `sharing_root`", {"key": "sharing_root"}))
    registry = SharingRegistry(config.sharing_root)
    replay(registry, config.operations_root)
    scratch = registry.scratch(writer.invocation_id)
    try:
        found = publication.inspect(config, destination, corpus_id, scratch)
        if found.fields.world != world:
            raise Refused(Refusal(
                "world-mismatch",
                f"the publication at {destination.locator} claims world {found.fields.world}, not {world}",
                {"claimed": found.fields.world, "given": world}))
        line = writer.record_sharing(
            SharingEvidence(corpus_id, found.fields.uid, found.artifact, world, found.fields.view,
                            source=f"provider:{destination.locator}", location=destination.locator),
            transition="bound", verdict=found.verdict)
        registry.write_binding(ProviderBinding(world, (destination.locator,), line.at, True))
    finally:
        if scratch.exists():
            shutil.rmtree(scratch)
    return (pin_block(line),)
