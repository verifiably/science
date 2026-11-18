"""Mint a governed source assertion after checking text encoding, cross-corpus occupancy, anchor identity, and targets."""
from __future__ import annotations

from beliefs import stored
from beliefs.errors import IdentityError, MalformedRecord, SignatureRefused
from beliefs.identity import v1
from beliefs.source_assertion import Bearing, Reading, Representation, SourceAssertion, Span

from science.lookup import Located, decode_source_assertion, session_record, world_record
from science.refusal import Refusal, Refused
from science.report import Report, record_block

__all__ = ["handle"]


def _occupied_entry(found: Located, *, asked: str) -> dict[str, object]:
    entry: dict[str, object] = {
        "address": found.address,
        "uid": found.node.uid,
        "kind": found.node.kind,
        "corpora": list(found.corpora),
    }
    if found.address != asked:
        entry["redirect"] = True
    return entry


def _existing_entry(found: Located, existing_val: SourceAssertion, *, asked: str) -> dict[str, object]:
    entry: dict[str, object] = {
        "address": found.address,
        "uid": found.node.uid,
        "source": existing_val.source,
        "corpora": list(found.corpora),
    }
    if found.address != asked:
        entry["redirect"] = True
    return entry


def handle(
    ctx,
    writer,
    *,
    source: str,
    proposition: str,
    sign: str,
    quote: str,
    locator: str,
    sha256: str,
    media_type: str,
    extent: str,
    extracted_by: str,
    attributed_to: str | None = None,
    title: str,
    body: str | None = None,
) -> Report:
    if type(title) is not str or not title.strip() or "\n" in title or "\r" in title:
        raise Refused(Refusal("invalid-input", "title must be a single non-empty line", {"field": "title"}))
    try:
        v1.encode(title)
    except IdentityError as caught:
        raise Refused(Refusal("invalid-input", f"title is not v1-encodable: {caught}", {"field": "title"})) from caught

    if body is not None:
        if type(body) is not str:
            raise Refused(Refusal("invalid-input", "body must be a string", {"field": "body"}))
        try:
            v1.encode(body)
        except IdentityError as caught:
            raise Refused(
                Refusal("invalid-input", f"body is not v1-encodable: {caught}", {"field": "body"})
            ) from caught

    try:
        value = SourceAssertion(
            source=source,
            read=Reading(
                representation=Representation(sha256=sha256, media_type=media_type, extent=extent),
                span=Span(quote=quote, locator=locator),
                extracted_by=extracted_by,
                attributed_to=attributed_to,
            ),
            bears_on=Bearing(sign=sign, proposition=proposition),
            recorded_by=writer.actor,
        )
    except (MalformedRecord, SignatureRefused) as caught:
        raise Refused(Refusal("invalid-input", str(caught), {"kind": type(caught).__name__})) from caught

    found = world_record(ctx, value.id)
    if found is not None:
        if found.node.kind != "source-assertion":
            raise Refused(
                Refusal(
                    "invalid-input",
                    f"{found.address} is already held as a {found.node.kind}",
                    {"occupied": _occupied_entry(found, asked=value.id)},
                )
            )
        existing_val = decode_source_assertion(found.node)
        existing_src = world_record(ctx, existing_val.source)
        requested_src = world_record(ctx, source)
        if requested_src is not None and requested_src.node.kind == "source":
            if (
                existing_src is not None
                and existing_src.node.kind == "source"
                and existing_src.node.uid == requested_src.node.uid
            ):
                raise Refused(
                    Refusal(
                        "invalid-input",
                        f"{found.address} is already recorded",
                        {"existing": [_existing_entry(found, existing_val, asked=value.id)]},
                    )
                )
            raise Refused(
                Refusal(
                    "invalid-input",
                    f"{found.address} is already anchored in {existing_val.source}, which resolves to "
                    f"{existing_src.address if existing_src is not None else None}, not {requested_src.address}",
                    {
                        "anchor_conflict": {
                            "address": found.address,
                            "uid": found.node.uid,
                            "existing_source": existing_val.source,
                            "resolved_existing_source": existing_src.address if existing_src is not None else None,
                            "requested_source": source,
                            "resolved_requested_source": requested_src.address,
                            "corpora": list(found.corpora),
                        }
                    },
                )
            )

    unresolved: list[str] = []
    wrong_kind: list[dict[str, str]] = []
    for slot, ref, expected_kind in (
        ("source", source, "source"),
        ("proposition", proposition, "proposition"),
    ):
        located = session_record(ctx, ref)
        if located is None:
            if ref not in unresolved:
                unresolved.append(ref)
        elif located.node.kind != expected_kind:
            wrong_kind.append({"slot": slot, "address": located.address, "kind": located.node.kind})

    if unresolved:
        unmounted: dict[str, list[str]] = {}
        if ctx.config.coordination is None:
            for ref in unresolved:
                found_cfg = world_record(ctx, ref)
                if found_cfg is not None:
                    unmounted[ref] = list(found_cfg.corpora)
        data: dict[str, object] = {"unresolved": unresolved}
        message = f"target record(s) not in the session's corpora: {', '.join(unresolved)}"
        if unmounted:
            data["unmounted"] = unmounted
            message += (
                f"; configured read mount(s) hold {', '.join(unmounted)}, "
                "but coordination = false mounts only the write root"
            )
        raise Refused(Refusal("invalid-input", message, data))

    if wrong_kind:
        details = ", ".join(f"{item['slot']} resolves to {item['address']} ({item['kind']})" for item in wrong_kind)
        raise Refused(
            Refusal("invalid-input", f"target record(s) have the wrong kind: {details}", {"wrong_kind": wrong_kind})
        )

    node = writer.add(stored.source_assertion_node(value, title=title, body=body or ""))
    return (record_block(node),)
