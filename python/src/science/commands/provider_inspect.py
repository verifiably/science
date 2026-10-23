"""provider-inspect: the world a publication at a provider's location claims, read from a scratch copy that is
evaluated, granting nothing, and deleted (commons spec §4.4 layer 3; plan Deviation 2). Records nothing."""
from __future__ import annotations

import secrets
import shutil

from science import publication
from science.report import KeyVals, Report


def handle(ctx, *, location, corpus_id) -> Report:
    publication.require_id(corpus_id, "corpus_id")
    destination = publication.parse_destination(location)
    scratch = ctx.config.operations_root / "scratch" / "inspect" / secrets.token_hex(16)
    try:
        found = publication.inspect(ctx.config, destination, corpus_id, scratch)
    finally:
        if scratch.exists():
            shutil.rmtree(scratch)
    fields = found.fields
    return (KeyVals("publication", (("world", fields.world), ("marker", fields.uid), ("artifact", found.artifact),
                                    ("view", fields.view), ("verdict", found.verdict))),)
