"""Emit beliefs.corpus.Finding values, not science.report.Finding text blocks.

This is an open-time audit only: running endpoints do not poll for peer crashes.
Reconciliation classifies ledger evidence, not liveness: session-unclosed means
the referenced session has no close line, which a healthy live peer also yields.
"""
import json
from dataclasses import asdict

from beliefs.corpus import Finding


def report_findings(findings: tuple[Finding, ...], *, reported_by: str, stream) -> None:
    if not findings:
        return
    for finding in findings:
        payload = {**asdict(finding), "reported_by": reported_by}
        stream.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    if hasattr(stream, "flush"):
        stream.flush()
