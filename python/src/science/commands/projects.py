"""projects: every standing project, and which one is selected (spec §3.8)."""
from __future__ import annotations

from science.coordination import tip_nodes
from science.report import Heading, KeyVals, Report


def _revisions(tips) -> str:
    return "; ".join(f"{tip.title} @{tip.uid}" for tip in tips)


def handle(ctx) -> Report:
    resolver = ctx.coordination()
    rows = []
    for address, resolved in resolver.standing("project").items():
        tips = tip_nodes(resolver, resolved)
        if not tips:
            text = "no standing revision"
        elif len(tips) == 1:
            text = _revisions(tips)
        else:
            text = "divergent: " + _revisions(tips)  # listed once, never dropped
        if address == ctx.selection:
            text += " (selected)"
        rows.append((min((tip.title for tip in tips), default=""), str(address), text))
    rows.sort()
    return (Heading("Projects"),
            KeyVals("projects", tuple((address, text) for _, address, text in rows)
                    or (("none", "no projects"),)))
