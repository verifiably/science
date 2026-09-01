"""status: the shipped read exemplar (spec §11)."""
from __future__ import annotations

from collections import Counter

from beliefs.errors import EpochUnknown
from beliefs.world.read import current_epoch

from science.report import Heading, KeyVals, Report, Text


def handle(ctx) -> Report:
    world = ctx.world
    blocks: list = [Heading("World status")]
    registry = world.registry()
    corpus_ids = sorted(record.corpus_id for record in registry.admissions)
    rows = []
    for corpus_id in corpus_ids:
        status = world.status(corpus_id)
        rows.append(
            (
                corpus_id,
                f"known={status.known} live={status.live} present={status.present}",
            )
        )
    blocks.append(
        KeyVals("corpora", tuple(rows) or (("none", "no corpora admitted"),))
    )
    try:
        epoch = current_epoch(world)
        blocks.append(KeyVals("epoch", (("packaging", epoch.packaging_identity),)))
    except EpochUnknown:
        blocks.append(Text("No current epoch."))
    for corpus_id, read_view in ctx.read_views():
        counts = Counter(node.kind for node in read_view.iter_stored())
        blocks.append(
            KeyVals(
                f"records in {corpus_id}",
                tuple((kind, str(count)) for kind, count in sorted(counts.items())),
            )
        )
    return tuple(blocks)
