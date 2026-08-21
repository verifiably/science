"""Retraction enumeration — every found retraction with its resolution.

The subject projection is specification §7.6's retraction enumeration: each
found ref stays attached to its resolution, the pairs are sorted, and the
declared coverage travels with them. A ref found twice with the same resolution
is one finding; the same ref with two resolutions is two, because dropping
either would be an enumeration deciding which resolution it preferred.
"""


def enumerate_retractions(capture):
    found = set()
    for pair in capture["found"]:
        ref, resolution = pair
        found.add((ref, resolution))
    return {
        "found": [[ref, resolution] for ref, resolution in sorted(found)],
        "coverage": sorted(capture["coverage"]),
    }
