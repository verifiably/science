"""Read full stored records, with project-local notes about world identities."""
from __future__ import annotations

from itertools import combinations

import yaml
from beliefs import stored
from beliefs.coordination import CoordinationAddress
from beliefs.errors import ScienceError
from nodes.core.errors import NodesError

from science.coordination import content_of, selected_project, tip_nodes
from science.lookup import (CoreferencePair, decode_source_assertion, identifiers, source_assertions,
                            source_coreference, sources_carrying, validate_coreference_attestation,
                            world_record, write_root_only)
from science.refusal import Refusal, Refused, kernel_refusal
from science.report import Finding, Heading, KeyVals, Report, Text

__all__ = ["handle"]


def _yaml(value):
    return yaml.safe_dump(value, sort_keys=True).rstrip()


def _relation_dicts(relations):
    return [{"source": r.source, "predicate": r.predicate, "target": r.target} for r in relations]


def _coord_address(node):
    facet = node.facets[stored.COORDINATION_FACET]
    return CoordinationAddress(facet["project"], facet.get("local"))


def _coord_blocks(node):
    address = _coord_address(node)
    pairs = [("address", str(address)), ("pinned", str(address.pinned(node.uid))),
             ("uid", node.uid), ("name", node.title)]
    pairs += [(key, _yaml(value)) for key, value in sorted(content_of(node).items())
              if key not in ("name", "body")]
    return [KeyVals(node.kind, tuple(pairs)), Text(node.body)]


def _notes(ctx, node):
    if ctx.config.coordination is None or ctx.selection is None:
        return []
    try:
        selected_project(ctx)
    except Refused as caught:
        refusal = caught.refusal
        if refusal.code == "unknown-project" or (refusal.code == "kernel-refused" and
                                                refusal.data.get("reason") == "divergent-view"):
            return [Finding(refusal.message)]
        raise
    resolver = ctx.coordination()
    entries = []
    for address, resolved in resolver.standing("note", project=ctx.selection).items():
        for note in tip_nodes(resolver, resolved):
            about = content_of(note).get("about", [])
            if any((found := world_record(ctx, ref)) is not None and found.node.uid == node.uid
                   for ref in about):
                entries.append((str(address), note.title))
    return [KeyVals("notes about this record", tuple(sorted(set(entries))))]


def _source_assertions(ctx, node):
    if node.kind == "source":
        matches = [
            (located, val)
            for located, val in source_assertions(ctx)
            if (target := world_record(ctx, val.source)) is not None and target.node.uid == node.uid
        ]
        if not matches:
            return []
        return [
            KeyVals(
                "source assertions",
                tuple(
                    (
                        located.address,
                        f"{val.bears_on.sign} {val.bears_on.proposition} (extracted by {val.read.extracted_by}) — {located.node.title}",
                    )
                    for located, val in matches
                ),
            )
        ]
    if node.kind == "proposition":
        matches = [
            (located, val)
            for located, val in source_assertions(ctx)
            if (target := world_record(ctx, val.bears_on.proposition)) is not None and target.node.uid == node.uid
        ]
        if not matches:
            return []
        return [
            KeyVals(
                "source assertions",
                tuple(
                    (
                        located.address,
                        f"{val.bears_on.sign} in {val.source} (extracted by {val.read.extracted_by}) — {located.node.title}",
                    )
                    for located, val in matches
                ),
            )
        ]
    return []


def _world_blocks(ctx, found, incident=()):
    node = found.node
    pairs = [("address", node.id), ("uid", node.uid), ("title", node.title)]
    if node.kind == "source":
        pairs += sorted(node.facets[stored.SOURCE_FACET]["identifiers"].items())
        if node.deprecated_ids:
            pairs.append(("formerly", ", ".join(sorted(node.deprecated_ids))))
        pairs += [("held by", ", ".join(found.corpora)),
                  ("correctable here", "yes" if write_root_only(ctx, found) else "no")]
    else:
        if node.kind == "source-assertion":
            decode_source_assertion(node)
        elif node.kind == "coreference-attestation":
            validate_coreference_attestation(ctx, node)
        pairs += [("relations", _yaml(_relation_dicts(node.relations))), ("facets", _yaml(node.facets))]
    blocks = [KeyVals(node.kind, tuple(pairs)), Text(node.body), *_source_assertions(ctx, node), *_notes(ctx, node)]
    if incident:
        blocks.append(Heading("source coreference (live evidence)"))
        blocks.extend(_pair_block(pair) for pair in incident)
    return blocks


def _pair_block(pair: CoreferencePair) -> KeyVals:
    endpoints = []
    for address, item in zip(pair.addresses, pair.resolved, strict=True):
        if item is None:
            status = "unavailable"
        elif item.address == address:
            status = "exact"
        else:
            status = f"redirected to {item.address}"
        endpoints.append(f"{address} ({status})")
    return KeyVals("coreference pair", (
        ("left", endpoints[0]), ("right", endpoints[1]), ("state", pair.state),
        ("balance", str(pair.balance)), ("distinct_key_count", str(pair.distinct_key_count)),
        ("attestations", ", ".join(pair.attestations)),
    ))


def _source_blocks(ctx, hits):
    evidence = source_coreference(ctx)
    current_pairs = {pair.addresses for pair in evidence if pair.state in {"positive", "contested", "negative"}}
    unassessed = [
        CoreferencePair((first.address, second.address), (first, second), 0, 0, ())
        for first, second in combinations(hits, 2)
        if (first.address, second.address) not in current_pairs
    ]
    blocks = []
    for hit in hits:
        uid = hit.node.uid
        incident = [(peer, pair) for pair in (*evidence, *unassessed) if (peer := pair.other_address(uid)) is not None]
        incident.sort(key=lambda item: (item[0], item[1].addresses))
        blocks.extend(_world_blocks(ctx, hit, [pair for _, pair in incident]))
    blocks.extend(Finding(f"These records may be one work: {pair.addresses[0]} and {pair.addresses[1]}.")
                  for pair in unassessed)
    return tuple(blocks)


def _read(ctx, *, address, doi, pmid, isbn, accession) -> Report:
    by_identifier = any(value is not None for value in (doi, pmid, isbn, accession))
    if address is None and not by_identifier:
        raise Refused(Refusal("invalid-input", "give an address or one or more identifiers",
                              {"kind": "BasisMissing"}))
    if address is not None and by_identifier:
        raise Refused(Refusal("invalid-input", "give an address or one or more identifiers, exclusively"))
    if address is None:
        found = sources_carrying(ctx, identifiers(doi=doi, pmid=pmid, isbn=isbn, accession=accession))
        if not found:
            return (Finding("No source carries these identifiers."),)
        return _source_blocks(ctx, found)
    if address.startswith("coord:"):
        resolver = ctx.coordination()
        try:
            coord = CoordinationAddress.parse(address)
        except ValueError as caught:
            raise Refused(Refusal("invalid-input", str(caught))) from caught
        nodes = tip_nodes(resolver, resolver.resolve(coord))
        if nodes:
            return tuple(block for node in nodes for block in _coord_blocks(node))
    else:
        found = world_record(ctx, address)
        if found is not None:
            if (found.node.kind != "coreference-attestation" and
                    stored.COORDINATION_FACET in found.node.facets):
                ctx.coordination()
                return tuple(_coord_blocks(found.node))
            if found.node.kind == "source":
                return _source_blocks(ctx, (found,))
            return tuple(_world_blocks(ctx, found))
        # Stored coordination ids name an exact revision, including superseded ones.
        parts = address.split(":", 1)
        if len(parts) == 2 and parts[0] in ("project", "question", "hypothesis", "task", "decision", "topic", "note"):
            resolver = ctx.coordination()
            node = resolver.revision(parts[1].rsplit(".", 1)[-1])
            if node is not None and node.id == address:
                return tuple(_coord_blocks(node))
    raise Refused(Refusal("invalid-input", f"{address} names no record in the configured corpora"))


def handle(ctx, *, address=None, doi=None, pmid=None, isbn=None, accession=None) -> Report:
    try:
        return _read(ctx, address=address, doi=doi, pmid=pmid, isbn=isbn, accession=accession)
    except (ScienceError, NodesError, OSError) as caught:
        if address is None or address.startswith(("source:", "coreference-attestation:")):
            raise Refused(kernel_refusal(caught)) from caught
        raise
