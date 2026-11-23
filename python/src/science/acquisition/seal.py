"""Bind acceptance to its destination and recover the governed acquisition report."""

from __future__ import annotations

from beliefs import stored
from beliefs.durable import write_create_only
from beliefs.holdings.acquisition_log import render_acquisition_log
from beliefs.holdings.records import StoreLocator, StoreTreeLocator
from beliefs.holdings.seal import LOG_NAME, SealRequest
from beliefs.session.ledger import open_ledger_reader

from science.acquisition.binding import seal_identity
from science.acquisition.journal import Journal, locked_directory, set_directory, validate_root
from science.acquisition.retrieve import clean_work_files, verified_members
from science.acquisition.standing import seal_heads
from science.config import corpus_id_at
from science.refusal import Refusal, Refused
from science.report import record_block

__all__ = ["accept", "seal_set"]


def _refuse(message, code="invalid-input"):
    raise Refused(Refusal(code, message))


def _already(receipt):
    _refuse(f"already sealed as {receipt['dataset']} with {receipt['report']}; see acquire status")


def _recover(ctx, bound):
    view = ctx.write_view()
    matches = []
    for node in view.iter_stored():
        if node.kind != "act-report":
            continue
        report = stored.act_report_facet(node)
        for entry in report["entries"]:
            if entry["kind"] != "acquisition-set" or entry["outcome"]["log"] != bound["log"]:
                continue
            value = entry["outcome"]
            subject = StoreTreeLocator(bound["store"], bound["tree"].split(":")[1]).canonical()
            if (entry["subject"] != subject or value["tree"] != bound["tree"] or value["origin"] != bound["origin"]
                    or report["actor"] != "session:" + bound["session"]):
                _refuse("conflicting governed evidence for this acquisition log", "outcome-unknown")
            matches.append(node.id)
    if len(matches) == 1 and view.holds(bound["dataset"]):
        return matches[0]
    if matches:
        _refuse("ambiguous acquisition report or missing declaration", "outcome-unknown")
    reader = open_ledger_reader(ctx.config.operations_root, bound["session"])
    invocation = reader.invocation(bound["invocation"])
    if invocation is None or reader.torn_tail or invocation.command not in ("acquire-import", "acquire-seal"):
        _refuse("prior invocation evidence is incomplete", "outcome-unknown")
    if any(ref.startswith("act-report:") for act in invocation.acts for _, ref in act.record_ids):
        _refuse("prior invocation recorded a report which could not be recovered", "outcome-unknown")
    # The caller checks whether this prior invocation can still act.
    return None


def accept(ctx, writer, log, title, locator, bound, bind, finish, request_files):
    """Both origins reach this one kernel seal. request_files is needed only before a fresh write."""
    identity = seal_identity(log, title, locator)
    identity.update(store=writer.store_id, corpus=corpus_id_at(ctx.config.write_root))
    address = identity["dataset"]
    tree = StoreTreeLocator(writer.store_id, identity["tree"].split(":")[1])
    session = writer.actor.removeprefix("session:")
    if bound is not None:
        if any(bound[k] != v for k, v in identity.items()):
            _refuse("the same set is bound to another log, title, locator, corpus or store")
        report = _recover(ctx, bound)
        if report:
            receipt = dict(dataset=address, report=report)
            finish(receipt)
            _already(receipt)
        if session != bound["session"]:
            prior = open_ledger_reader(ctx.config.operations_root, bound["session"])
            if not prior.closed and prior.invocation(bound["invocation"]).outcome is None:
                _refuse("prior writer has an open invocation without an acquisition report", "outcome-unknown")
    found = ctx.dataset_at(address)
    if found and found[0] != identity["corpus"] and not ctx.write_view().holds(address):
        _refuse(f"dataset {address} is already declared on read mount {found[0]}")
    location_names = [tree.canonical(), StoreLocator(writer.store_id, identity["log"].split(":")[1] + "/" + LOG_NAME).canonical()]
    for name, digest in log.header.source_journals:
        location_names.append(StoreLocator(writer.store_id, digest.split(":")[1] + "/" + name).canonical())
    standing, unsettled = seal_heads(ctx, location_names)
    file, members, originals = request_files()
    request = SealRequest(title, locator, "data", members, file, log.header.origin, log.header.fetched_by, originals)
    bind(dict(**identity, invocation=writer.invocation_id, session=session))
    result = writer.seal_acquisition(request, instrument="science/acquire-seal.v1", standing=standing, unsettled=unsettled)
    finish(dict(dataset=result.address, report=result.report_ref))
    view = ctx.write_view()
    blocks = [record_block(view.get(result.report_ref))]
    if result.dataset is not None:
        blocks.append(record_block(result.dataset))
    return tuple(blocks)


def seal_set(ctx, writer, token, partial):
    operations, protected = ctx.config.acquisition_roots()
    validate_root(operations, protected)
    path = set_directory(operations, token)
    with locked_directory(path, "set-busy"):
        journal = Journal.open(operations, token, repair=True)
        if journal.receipt:
            if (journal.binding["corpus"] != corpus_id_at(ctx.config.write_root)
                    or journal.binding["store"] != writer.store_id):
                _refuse("this set was sealed in another destination")
            clean_work_files(journal)
            _already(journal.receipt)
        if not journal.binding:
            members = verified_members(journal)
            if not members:
                _refuse("an acquisition needs at least one verified fetched member")
            if any(r.state != "fetched" for r in journal.requests):
                if not partial and not journal.partial:
                    _refuse("incomplete acquisition requires explicit partial acceptance")
                if not journal.partial:
                    journal.append("partial")
                for seq, state in enumerate(journal.requests, 1):
                    if state.state == "pending":
                        journal.append("abandoned", seq=seq)
        log = journal.acquisition_log()

        def request_files():
            file = path / LOG_NAME
            write_create_only(file, render_acquisition_log(log))
            return file, verified_members(journal), ()

        def finish(receipt):
            journal.append("sealed", **receipt)
            clean_work_files(journal)

        return accept(ctx, writer, log, journal.plan.source["title"], journal.plan.source["locator"], journal.binding,
                      lambda binding: journal.append("sealing", **binding), finish, request_files)
