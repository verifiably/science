"""show: one pin's state, source, kernel status, acceptance and verification picture (commons spec §4.5, §11
step 2). The evidence picture is read from the records, not from the kernel's belief inputs: those drop a
verification whose assessment the policy excluded, and `show` must list it. Writes nothing."""
from __future__ import annotations

from beliefs import stored
from beliefs.corpus import ReadView

from science import publication, supersession
from science.acceptance import AcceptanceInputs, acceptance_inputs, counts
from science.config import live_mounts
from science.retention import required
from science.refusal import Refusal, Refused
from science.report import Finding, Heading, KeyVals, Report, Text
from science.sharing import STATE_ORDER, Pin, SharingRegistry, sharing_lines

LAG = "registry lags the kernel: `adopt` reconciles it"


def _yes(value: bool) -> str:
    return "yes" if value else "no"


def _confirmation(pin: Pin, inputs: AcceptanceInputs) -> str:
    """Origin-confirmed when the source is a location bound to the marker's world, recommended when a catalog
    names it; any other pin has no source that stands."""
    if pin.origin_confirmed(inputs.bindings):
        return "origin-confirmed"
    if pin.source is not None and pin.source.kind == "catalog":
        return "recommended"
    return "unsourced"


def _world_of(ctx, inputs: AcceptanceInputs, corpus_id: str) -> str:
    """The world a session corpus speaks for: the reader's own, or the one its publication marker claims."""
    if corpus_id in inputs.own_roots:
        return ctx.config.world.world_id
    if corpus_id in inputs.carriers:
        return inputs.carriers[corpus_id].world
    raise Refused(Refusal("invalid-input", f"corpus {corpus_id} holds a verification but is neither this world's "
                                           "own nor a publication, so its world is unknown"))


def _verifications(ctx) -> dict[str, list[tuple[str, str]]]:
    """Every verification record across the session's corpora, as (holding corpus, address), by the assessment
    its `verifies` relation targets."""
    found: dict[str, list[tuple[str, str]]] = {}
    for mount in ctx.session_mounts():
        for node in mount.view.iter_stored():
            if node.kind != "verification":
                continue
            for relation in node.relations:
                if relation.predicate == stored.VERIFIES:
                    found.setdefault(relation.target, []).append((mount.corpus_id, node.id))
    return found


def _evidence(ctx, inputs: AcceptanceInputs, corpus_id: str, assessments: list[str]) -> tuple[tuple[str, str], ...]:
    verifying = _verifications(ctx)
    rows = []
    for address in assessments:
        held = verifying.get(address, [])
        worlds = sorted({_world_of(ctx, inputs, holder) for holder, _ in held})
        counted = sum(1 for holder, verification in held if counts(inputs, holder, verification))
        rows.append((address, f"counts {_yes(counts(inputs, corpus_id, address))}; verifications {len(held)} "
                              f"from worlds {', '.join(worlds) or 'none'}, {counted} count under the policy"))
    return tuple(rows) or (("assessments", "none: the corpus holds no assessment"),)


def _supersession(ctx, registry, pin, status) -> Report:
    history = sharing_lines(ctx.config.operations_root)
    groups = supersession.groups(registry, history)
    marker = publication.marker_fields(publication.marker_of(registry.root_for(pin.corpus_id)))
    key = supersession.group_of(marker)
    held = groups.get(key, ())
    retired = (KeyVals("retention", (("retired", "yes"),)),) if any(
        item.corpus_id == pin.corpus_id and item.status == "retired" for item in ctx.world.registry().statuses) else ()
    if not held:
        return retired
    outcome = supersession.classify(held)
    tip = outcome.tip if outcome.kind == "resolved" else supersession.current(history, held)
    pair = pin.corpus_id, marker.uid
    path = None if tip is None else supersession.chain(pair, tip, held)
    relation = "sibling"
    if outcome.kind != "divergent":
        if pair == tip:
            relation = "tip"
        elif path:
            relation = f"superseded by {tip[0]}"
    if outcome.kind == "resolved":
        current = " ".join(tip)
    elif outcome.kind == "divergent":
        current = "divergent: " + ", ".join(" ".join(pair) for pair in outcome.tips)
    else:
        current = "unresolved: " + ", ".join(f"adopt {corpus} {marker}" for corpus, marker in outcome.missing)
    beside = sorted(item.corpus_id for other, items in groups.items() if other != key and other[:2] == key[:2]
                    for item in items if item.state == "mounted" and ctx.world.status(item.corpus_id).live)
    if beside:
        relation = "unlinked chain beside " + ", ".join(beside)
    blocks = [KeyVals("supersession", (("group", " ".join(key)), ("current", current), ("this pin", relation)))]
    if beside:
        blocks.append(Finding("records attributed differently cannot be published while both chains are mounted"))
    if retired:
        return (*blocks, *retired)
    if outcome.kind != "resolved" or not path or pair == tip or not status.live:
        return tuple(blocks)
    predecessor = next(item for item in held if item.corpus_id == pin.corpus_id)
    mounts = live_mounts(ctx.config, ctx.world, registry)
    write = next(mount for mount in mounts if mount.root == ctx.config.write_root)
    live_ids = {mount.corpus_id for mount in mounts}
    reasons = required(predecessor, keep=ctx.config.keep, group_chain=held, tip=tip,
                       mounted=tuple(item for items in groups.values() for item in items
                                     if item.state == "mounted" and item.corpus_id in live_ids),
                       write_root=(write.corpus_id, write.view, write.profile),
                       live=tuple((mount.corpus_id, mount.view, mount.profile) for mount in mounts if mount != write))
    rows = []
    for reason in reasons:
        if reason.kind == "configuration":
            value = "configuration"
        elif reason.kind == "chain":
            value = f"chain (for {reason.detail[0]})"
        elif reason.kind == "attribution":
            value = f"attribution (named by {reason.detail[0]})"
        else:
            value = f"dependency ({', '.join(reason.detail)})"
        rows.append(("kept", value))
    blocks.append(KeyVals("retention", tuple(rows) or (("pending", "no door"),)))
    return tuple(blocks)


def handle(ctx, *, corpus_id) -> Report:
    publication.require_id(corpus_id, "corpus_id")
    config = ctx.config
    if config.sharing_root is None:
        raise Refused(Refusal("invalid-input", "show reads a pin from the sharing registry; configure `sharing_root`",
                              {"key": "sharing_root"}))
    registry = SharingRegistry(config.sharing_root)
    pin = registry.pin(corpus_id)
    if pin is None:
        raise Refused(Refusal("invalid-input", f"no pin for corpus {corpus_id} in the sharing registry",
                              {"corpus_id": corpus_id}))
    inputs = acceptance_inputs(ctx)
    status = ctx.world.status(corpus_id)
    # The corpus's own records, read from the copy the registry holds, whether or not this context mounts it.
    assessments = sorted(node.id for node in ReadView.opened_at(registry.root_for(corpus_id)).iter_stored()
                         if node.kind == "assessment")
    source = pin.source
    blocks: list = [
        Heading(f"Pin: {corpus_id}"),
        KeyVals("pin", (("state", pin.state), ("world", pin.world), ("marker", pin.marker),
                        ("artifact", pin.artifact), ("view", pin.view), ("keep", _yes(corpus_id in config.keep)))),
        KeyVals("source", (("kind", "none" if source is None else source.kind),
                           ("reference", "none" if source is None else source.reference),
                           ("confirmation", _confirmation(pin, inputs)))),
        KeyVals("fetch", (("location", pin.fetch.location), ("at", pin.fetch.at), ("verdict", pin.fetch.verdict))),
        KeyVals("kernel", (("known", _yes(status.known)), ("live", _yes(status.live)),
                           ("present", _yes(status.present)))),
        KeyVals("acceptance", (("world accepted", _yes(pin.world in inputs.verifiers)),
                               ("counts as evidence",
                                _yes(counts(inputs, corpus_id, assessments[0])) if assessments else "n/a"))),
        KeyVals("evidence", _evidence(ctx, inputs, corpus_id, assessments)),
        Text("independence: not exposed by the kernel's inputs (Deviation 8)"),
    ]
    blocks.extend(_supersession(ctx, registry, pin, status))
    if status.known and status.live and STATE_ORDER.index(pin.state) < STATE_ORDER.index("mounted"):
        blocks.append(Finding(LAG))
    return tuple(blocks)
