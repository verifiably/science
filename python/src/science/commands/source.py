"""Mint a source only when no supplied identifier already names a held record."""
from beliefs import stored
from beliefs.source import source_address

from science.lookup import (identifiers, require_identifiers, sources_carrying,
                            world_record, write_root_only)
from science.refusal import Refusal, Refused
from science.report import Report, record_block


def handle(ctx, writer, *, title, doi=None, pmid=None, isbn=None, accession=None) -> Report:
    given = identifiers(doi=doi, pmid=pmid, isbn=isbn, accession=accession)
    require_identifiers(given)
    if not title.strip():
        raise Refused(Refusal("invalid-input", "the title must not be empty", {"field": "title"}))
    found = sources_carrying(ctx, given)
    if found:
        messages = []
        for located in found:
            held = located.node.facets[stored.SOURCE_FACET]["identifiers"]
            if all(held.get(scheme) == value for scheme, value in given.items()):
                messages.append(f"{located.address} is already recorded")
            elif write_root_only(ctx, located):
                messages.append(f"{located.address}: add the identifier with `source-correct`")
            else:
                messages.append(f"{located.address} is held by {', '.join(located.corpora)}; "
                                "it cannot be changed here and is used as it stands")
        raise Refused(Refusal("invalid-input", "; ".join(messages),
                              {"existing": [located.entry() for located in found]}))
    address = source_address(given)
    holder = world_record(ctx, address)
    if holder is not None:
        raise Refused(Refusal("invalid-input", f"{address} redirects to {holder.address}; "
                              "the retired address cannot be used for a new source",
                              {"existing": [holder.entry(asked=address)]}))
    node = writer.add(stored.source_node(title=title, identifiers=given))
    return (record_block(node),)
