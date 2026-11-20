"""Sign a statement about two exact source addresses."""
from __future__ import annotations

from typing import NoReturn

from beliefs import stored
from beliefs.errors import BuildHold, MalformedRecord, ScienceError
from beliefs.world.view import WorldReadView
from nodes.core.errors import NodesError

from science import world_belief
from science.config import corpus_id_at
from science.lookup import Located, _live, _located
from science.refusal import Refusal, Refused, kernel_refusal
from science.report import Report, record_block

__all__ = ["handle"]


def _refuse_endpoint(field: str, address: str, reason: str, found: Located | None = None) -> NoReturn:
    messages = {
        "unresolved": "does not identify a source in a live configured corpus",
        "wrong-kind": "identifies a record of a different kind",
        "redirect": "has been redirected; use its current address",
        "outside-session": "is held outside the session's live citation mounts",
        "self-pair": "identifies the same source as left",
    }
    data = {"field": field, "address": address, "reason": reason}
    if found is not None:
        data["corpora"] = list(found.corpora)
        if found.address != address:
            data["current_address"] = found.address
    raise Refused(Refusal("invalid-input", f"{field} {address!r} {messages[reason]}", data))


def _endpoint(ctx, mounts, session_roots, field: str, address: str) -> Located:
    holders = [mount for mount in mounts if mount.view.holds(address)]
    found = _located(ctx, holders, address)
    if found is None:
        _refuse_endpoint(field, address, "unresolved")
    if found.node.kind != "source":
        _refuse_endpoint(field, address, "wrong-kind", found)
    if found.address != address:
        _refuse_endpoint(field, address, "redirect", found)
    if not any(mount.root in session_roots for mount in holders):
        _refuse_endpoint(field, address, "outside-session", found)
    return found


def _statement(writer, left: str, right: str, stance: str, grounds: str):
    invalid = Refusal("invalid-input", "grounds must be nonblank Unicode NFC text encodable as UTF-8",
                      {"field": "grounds", "reason": "invalid-text"})
    if not grounds.strip():
        raise Refused(invalid)
    value, title = {
        "same": (1, "Sources describe the same citable version"),
        "distinct": (-1, "Sources describe distinct citable versions"),
    }[stance]
    try:
        return stored.coreference_attestation_node(title=title, endpoints=(left, right), stance=value,
                                                   actor=writer.actor, grounds=grounds,
                                                   event_token=writer.invocation_id)
    except MalformedRecord as caught:
        raise Refused(invalid) from caught


def _mounted_view(ctx, mounts, first: Located, second: Located) -> WorldReadView:
    live_ids = frozenset(mount.corpus_id for mount in mounts)
    session_ids = ctx.session_ids()
    try:
        view = world_belief.epoch_currency(ctx.world, live_ids, require_present=True).view
    except Refused as caught:
        refusal = caught.refusal
        needs_publication = refusal.code == "no-epoch" or (
            refusal.code == "epoch-stale" and refusal.data.keys() == {"missing", "extra", "drifted"}
        )
        if not needs_publication:
            raise
        if session_ids != live_ids:
            raise Refused(Refusal(
                "config-stale", "correct the listed roots/read mounts and reopen the session, then publish "
                "over the live set",
                {"session_only": sorted(session_ids - live_ids), "live_only": sorted(live_ids - session_ids)},
            )) from caught
        raise Refused(Refusal(
            refusal.code, f"{refusal.message}; run `science epoch` to publish over the live mounts, "
            "then use a fresh invocation", refusal.data,
        )) from caught

    for field, expected in (("left", first), ("right", second)):
        address = view.resolve(expected.address)
        uid = None
        if address is not None:
            node = view.get(expected.address)
            if node.kind != "source":
                raise MalformedRecord(f"{expected.address} resolves to a {node.kind} in the captured view")
            uid = node.uid
        if address != expected.address or uid != expected.node.uid:
            raise Refused(Refusal(
                "epoch-stale", f"the captured {field} source differs from the live record; reread the source "
                "by address and verify which exact record to name",
                {"field": field, "address": expected.address, "expected_uid": expected.node.uid,
                 "resolved_address": address, "resolved_uid": uid},
            ))
    return view


def handle(ctx, writer, *, left: str, right: str, stance: str, grounds: str) -> Report:
    try:
        mounts = _live(ctx, ctx.mounts())
        write_mount = next((mount for mount in mounts if mount.root == ctx.config.write_root), None)
        if write_mount is None:
            corpus = corpus_id_at(ctx.config.write_root)
            raise Refused(Refusal("corpus-retired", f"write corpus {corpus} is retired; reopen the session",
                                  {"corpus": corpus}))
        session_roots = {mount.root for mount in ctx.session_mounts()}
        first = _endpoint(ctx, mounts, session_roots, "left", left)
        second = _endpoint(ctx, mounts, session_roots, "right", right)
        if first.node.uid == second.node.uid:
            _refuse_endpoint("right", right, "self-pair", second)
        local = all(write_mount.view.resolve(address) == address for address in (left, right))
    except (ScienceError, NodesError, OSError) as caught:
        raise Refused(kernel_refusal(caught)) from caught

    node = _statement(writer, first.address, second.address, stance, grounds)
    try:
        view = None if local else _mounted_view(ctx, mounts, first, second)
    except (ScienceError, NodesError, OSError) as caught:
        raise Refused(kernel_refusal(caught)) from caught
    try:
        minted = writer.attest_coreference(node) if view is None else writer.attest_coreference(node, view=view)
    except BuildHold as caught:
        raise Refused(kernel_refusal(caught)) from caught
    return (record_block(minted),)
