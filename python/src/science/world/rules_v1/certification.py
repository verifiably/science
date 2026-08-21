"""Certification enumeration — the by-kind inventory.

The subject projection is specification §7.6's certification inventory: sorted
kinds, each carrying its sorted distinct refs, and the declared coverage. It is
location-free and resolution-free by construction — a ref enters the inventory
without its corpus and without whether it resolves, because both are properties
of the world reading the epoch rather than of the epoch.
"""


def enumerate_certifications(capture):
    by_kind = {}
    for entry in capture["certifications"]:
        kind, ref = entry
        by_kind.setdefault(kind, set()).add(ref)
    return {
        "by_kind": [{"kind": kind, "refs": sorted(refs)} for kind, refs in sorted(by_kind.items())],
        "coverage": sorted(capture["coverage"]),
    }
