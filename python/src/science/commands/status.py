"""status: the shipped read exemplar (spec §11)."""
from __future__ import annotations

from collections import Counter

from beliefs.errors import EpochUnknown
from beliefs.world.read import current_epoch

from science.report import Finding, Heading, KeyVals, Report, Text


def _finding_text(finding) -> str:
    """The kernel finding's fields in one line: severity, code and ref lead,
    the human message follows, and a non-empty detail closes in parentheses."""
    text = f"{finding.severity} {finding.code} {finding.ref}: {finding.message}"
    return f"{text} ({finding.detail})" if finding.detail else text


def handle(ctx) -> Report:
    world = ctx.world
    blocks: list = [Heading("World status")]
    registry = world.registry()
    corpus_ids = sorted(record.corpus_id for record in registry.admissions)
    rows = []
    findings: list = []
    for corpus_id in corpus_ids:
        status = world.status(corpus_id)
        rows.append(
            (
                corpus_id,
                f"known={status.known} live={status.live} present={status.present}",
            )
        )
        findings.extend(Finding(_finding_text(finding)) for finding in status.findings)
    blocks.append(
        KeyVals("corpora", tuple(rows) or (("none", "no corpora admitted"),))
    )
    # One block per finding, in corpus order, right after the rows they qualify.
    blocks.extend(findings)
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
