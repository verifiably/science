"""Correct a source without splitting shared identity or colliding with another."""
from beliefs.source import source_address
from beliefs.stored import SOURCE_FACET

from science.lookup import identifiers, require_identifiers, shared_with, sources_carrying, world_record
from science.refusal import Refusal, Refused
from science.report import Report, record_block


def handle(ctx, writer, *, address, grounds, doi=None, pmid=None, isbn=None, accession=None) -> Report:
    view = ctx.write_view()
    if not view.holds(address):
        holder = world_record(ctx, address)
        raise Refused(Refusal("invalid-input", "only a source in the write root can be corrected",
                              {"corpus": list(holder.corpora) if holder else []}))
    node = view.get(address)
    if node.kind != "source":
        raise Refused(Refusal("invalid-input", "the record is not a source", {"address": address}))
    given = identifiers(doi=doi, pmid=pmid, isbn=isbn, accession=accession)
    require_identifiers(given)
    held = node.facets[SOURCE_FACET]["identifiers"]
    result = {**held, **given}
    if result == held:
        raise Refused(Refusal("invalid-input", "the identifiers are unchanged", {"address": node.id}))
    shared = shared_with(ctx, node)
    if shared:
        raise Refused(Refusal("invalid-input", "a shared source cannot be changed here; use it as it stands",
                              {"corpora": list(shared)}))
    introduced = {scheme: value for scheme, value in given.items() if held.get(scheme) != value}
    found = [located.entry() for located in sources_carrying(ctx, introduced)
             if located.node.uid != node.uid]
    new_address = source_address(result)
    holder = world_record(ctx, new_address)
    if holder is not None and holder.node.uid != node.uid:
        entry = holder.entry(asked=new_address)
        if entry not in found:
            found.append(entry)
    if found:
        raise Refused(Refusal("invalid-input", "the correction collides with an existing record", {"existing": found}))
    corrected = writer.correct_identifier(address, result, grounds=grounds)
    return (record_block(corrected),)
