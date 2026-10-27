"""publish-preview: what `publish` would freeze, computed by the kernel's own step 0 and written nowhere."""
from __future__ import annotations

from collections import Counter

from beliefs.errors import EpochUnknown, PublicationRefused, SelectionRefused
from beliefs.publish import publication_preview
from nodes.core.ids import NodeId

from science.acceptance import acceptance_inputs
from science.coordination import resolve_project_ref
from science.publication import parse_destination, selection_detail
from science.refusal import Refusal, Refused
from science.report import Heading, KeyVals, Report, Text
from science.world_belief import REMEDY


def handle(ctx, *, target, to) -> Report:
    view = resolve_project_ref(ctx, target)
    destination = parse_destination(to)
    try:
        preview = publication_preview(ctx.world, ctx.coordination(), view, own_pins=ctx.pins(),
                                      own_corpora=acceptance_inputs(ctx).own_roots)
    except EpochUnknown:
        raise Refused(Refusal("no-epoch", f"this world has published no epoch; {REMEDY}")) from None
    except SelectionRefused as refused:
        raise Refused(Refusal("kernel-refused", selection_detail(refused),
                              {"kind": type(refused).__name__, "reason": refused.reason})) from None
    except PublicationRefused as refused:
        raise Refused(Refusal("kernel-refused", str(refused),
                              {"kind": type(refused).__name__, "reason": refused.reason})) from None
    kinds = Counter(NodeId.parse(address).kind for address in preview.selected)
    selection = (*((kind, str(count)) for kind, count in sorted(kinds.items())),
                 *(("record", address) for address in preview.selected))
    report: list = [
        Heading(f"publish {preview.view} to {destination.locator} at epoch {preview.epoch}"),
        KeyVals("selection", selection),
        KeyVals("closure", (("status", "complete"),)),
    ]
    # Own-only selections, including declared replicas, have no entries: None under v2, () under v3.
    if preview.attributions:
        report.append(KeyVals("attribution", tuple((address, f"{corpus} {marker}")
                                                   for address, corpus, marker in preview.attributions)))
    else:
        report.append(Text("attribution: every selected record is this world's own"))
    datasets = tuple(address for address in preview.selected if NodeId.parse(address).kind == "dataset")
    if datasets:
        report.append(KeyVals("inputs the destination will not carry", tuple(
            (address, f"bytes {'held' if ctx.is_held(ctx.mount_holding(address).view.get(address)) else 'not held'}; "
                      "redistribution unknown")
            for address in datasets)))
    else:
        report.append(Text("inputs the destination will not carry: none"))
    return tuple(report)
