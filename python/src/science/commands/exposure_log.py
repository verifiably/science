"""List exposure events over every configured live mount."""
from __future__ import annotations

from beliefs.reservation import exposure_events

from science.report import KeyVals, Report
from science.reservation import LiveRecords, event_block, kernel_reads, require_reference

__all__ = ["handle"]


def handle(ctx, *, subject: str | None = None, proposition: str | None = None) -> Report:
    require_reference("subject", subject, ("dataset:", "source:"))
    require_reference("proposition", proposition, ("proposition:",))
    with kernel_reads():
        events = exposure_events(LiveRecords.capture(ctx, "exposure-event"), subject=subject, proposition=proposition)
    summary = KeyVals("exposure log", (("subject", subject or "any"), ("proposition", proposition or "any"),
                                       ("events", str(len(events)))))
    return (summary, *(event_block(event) for event in events))
