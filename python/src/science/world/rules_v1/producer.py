"""Producer derivation — the producers map and its coverage.

The subject projection is specification §7.6's producer snapshot: sorted
`{"dataset": …, "runs": […]}` members and the sorted declared coverage. Every
`produces` edge contributes its run under its dataset, and the same edge
contributed twice contributes once — an enumeration counts what exists, not how
many times it was seen.
"""


def derive_producer_snapshot(capture):
    producers = {}
    for edge in capture["produces"]:
        dataset, run = edge
        producers.setdefault(dataset, set()).add(run)
    return {
        "producers": [
            {"dataset": dataset, "runs": sorted(runs)} for dataset, runs in sorted(producers.items())
        ],
        "coverage": sorted(capture["coverage"]),
    }
