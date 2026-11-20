"""Publication retirement keeps local citations at their stored spelling."""
from dataclasses import replace
from itertools import permutations

import pytest
from beliefs import stored
from beliefs.coordination import CoordinationAddress, VIEW_KINDS
from beliefs.corpus import CoordinationResolver, CorpusWriter, ReadView
from beliefs.intents.publish import Destination, PublishIntent
from beliefs.publication import binding_record, marker_record
from helpers.analysis import analysis_nodes
from helpers.world import BARE_PROFILE, PROFILE_V3, fixture_proposition_node, fixture_source_node
from nodes.core.errors import NodesError

from science import retention
from science.retention import Reason
from test_retention import graph, held, holder, reasons


def revision(kind, number, *, local="b" * 32, predecessors=(), **content):
    address = CoordinationAddress("a" * 32, None if kind == "project" else local)
    return CorpusWriter._coordination_node(
        kind, address, f"{number:032x}",
        {"name": kind, "body": "text", "author": "fixture", "at": "2026-11-20T00:00:00Z", **content},
        predecessors=predecessors,
    )


def note(*addresses):
    return revision("note", 30, local="e" * 32, about=list(addresses))


def query(*clauses):
    return {"version": "science.view-query.v1", "clauses": [{"all": list(clause)} for clause in clauses]}


def pin(carrier, number=1):
    return replace(held(number), corpus_id=carrier[0])


def test_note_keeps_only_the_cited_leaf(certified_work, graph):
    config, spec, dataset, proposition, assessment, run, replay, verification = graph
    citing = note(assessment.id, "assessment:departed")
    write = holder(certified_work / "write", citing, profile=BARE_PROFILE)
    leaf = holder(certified_work / "leaf", assessment, profile=config.profile)
    input_run = holder(certified_work / "run", run, profile=config.profile)
    assert reasons(pin(leaf), write, live=(leaf, input_run)) == (Reason("dependency", (assessment.id,)),)
    assert reasons(pin(input_run), write, live=(leaf, input_run)) == ()
    equal = holder(certified_work / "equal", assessment, profile=config.profile)
    assert reasons(pin(leaf), write, live=(leaf, input_run, equal)) == ()

    strong = holder(certified_work / "strong", citing, verification, spec, dataset, proposition, replay,
                    *analysis_nodes(config.profile), profile=config.profile)
    assert reasons(pin(input_run), strong, live=(leaf, input_run)) == (Reason("dependency", (run.id,)),)


@pytest.mark.parametrize("kind", VIEW_KINDS)
def test_view_tips_protect_explicit_addresses_and_anchors(certified_work, kind):
    explicit = fixture_proposition_node("explicit")
    neighbor = fixture_proposition_node("neighbor")
    anchor = stored.run_node("anchor", title="anchor", spec="", reads=(neighbor.id,))
    view = revision(kind, 1, query=query(
        ({"addresses": [explicit.id]}, {"kinds": ["proposition"]}),
        ({"closure": {"anchor": anchor.id, "predicates": ["reads"], "direction": "out"}},),
    ))
    write = holder(certified_work / "write", view)
    cited = holder(certified_work / "cited", explicit, anchor)
    traversed = holder(certified_work / "traversed", neighbor)
    assert reasons(pin(cited), write, live=(cited, traversed)) == (Reason("dependency", (explicit.id, anchor.id)),)
    assert reasons(pin(traversed), write, live=(cited, traversed)) == ()


def test_divergent_tips_and_repair_keep_only_standing_citations(certified_work):
    x, y = (fixture_proposition_node(name) for name in ("x", "y"))
    r1 = revision("topic", 1, query=query(({"addresses": [x.id]},)))
    r2 = revision("topic", 2, query=query(({"addresses": [y.id]},)), predecessors=(r1,))
    r3 = revision("topic", 3, query=query(({"addresses": [x.id]},)), predecessors=(r1,))
    r4 = revision("topic", 4, query=query(), predecessors=(r2, r3))
    carrier = holder(certified_work / "cited", x, y)
    for name, records, expected in (
        ("superseded", (r1, r2), (Reason("dependency", (y.id,)),)),
        ("divergent", (r1, r2, r3), (Reason("dependency", (x.id, y.id)),)),
        ("repaired", (r1, r2, r3, r4), ()),
        ("immutable", (r1, r2, r3, r4, note(x.id)), (Reason("dependency", (x.id,)),)),
    ):
        write = holder(certified_work / name, *records)
        assert reasons(pin(carrier), write, live=(carrier,)) == expected


def test_mounted_supersession_edges_do_not_release_local_tips(certified_work):
    x = fixture_proposition_node("x")
    r1 = revision("topic", 1, query=query(({"addresses": [x.id]},)))
    r2 = revision("topic", 2, query=query(), predecessors=(r1,))
    r3 = revision("topic", 3, query=query(), predecessors=(r2,))
    write = holder(certified_work / "write", r1, r3, profile=PROFILE_V3)
    mounted = holder(certified_work / "mounted", r2, profile=PROFILE_V3)
    carrier = holder(certified_work / "cited", x)
    resolver = CoordinationResolver({certified_work / "write": write[2], certified_work / "mounted": mounted[2]})
    assert resolver.resolve(CoordinationAddress("a" * 32, "b" * 32)).id == r3.id
    assert reasons(pin(carrier), write, live=(mounted, carrier)) == (Reason("dependency", (x.id,)),)


def test_publication_coordination_records_add_no_citations(certified_work):
    intent = PublishIntent("publish", "c" * 32, "fixture", "2026-11-20T00:00:00Z",
                           CoordinationAddress("a" * 32, revision="b" * 32),
                           Destination.remote("https://example.org/publications"), (), (), ())
    x = fixture_proposition_node("x")
    marker = marker_record(intent, world_id="d" * 32, epoch="f" * 64, selection=(x.id,))
    binding = binding_record(intent, corpus_id="e" * 32, marker=marker.uid, artifact="0" * 64)
    write = holder(certified_work / "write", marker, binding,
                   revision("project", 1, query=query()), revision("note", 2))
    carrier = holder(certified_work / "carrier", x)
    assert reasons(pin(carrier), write, live=(carrier,)) == ()


def attestation(left, right, stance=1):
    return stored.coreference_attestation_node(
        title="An identity judgment", endpoints=(left, right), stance=stance, actor="fixture",
        grounds="Comparison", event_token=f"event:{stance}",
    )


@pytest.mark.parametrize("make_node", [fixture_source_node, fixture_proposition_node])
def test_coreference_citations_use_both_stored_spellings(certified_work, make_node):
    left, right = (make_node(name) for name in ("left", "right"))
    old = left.id if left.kind == "source" else "proposition:retired-identifier"
    redirected = (left if old == left.id else
                  stored.stamp_semantic_identity(left.model_copy(update={"deprecated_ids": [old]})))
    write = holder(certified_work / "write", attestation(old, right.id), attestation(old, right.id, -1))
    a = holder(certified_work / "a", redirected)
    b = holder(certified_work / "b", right)
    wrong_spelling = holder(certified_work / "wrong-spelling", left)
    equal = holder(certified_work / "equal", redirected)
    assert reasons(pin(a), write, live=(a, b)) == (Reason("dependency", (old,)),)
    assert reasons(pin(b), write, live=(a, b)) == (Reason("dependency", (right.id,)),)
    assert reasons(pin(a), write, live=(a, wrong_spelling)) == (
        () if old == left.id else (Reason("dependency", (old,)),)
    )
    assert reasons(pin(a), write, live=(a, equal)) == ()


def test_publication_closure_cannot_follow_attestation_endpoints(certified_work, monkeypatch):
    neighbor = fixture_proposition_node("neighbor")
    cited = stored.run_node("cited", title="cited", spec="", reads=(neighbor.id,))
    statement = attestation(cited.id, "run:departed", -1)
    strong = stored.run_node("strong", title="strong", spec="", reads=(cited.id,))
    write = holder(certified_work / "write", statement)
    write_with_strong = holder(certified_work / "strong", statement, strong)
    leaf = holder(certified_work / "leaf", cited)
    input_record = holder(certified_work / "input", neighbor)
    original = retention.closure_missing

    def export_closure(view, selection):
        if selection == (statement.id,):
            return (cited.id, "run:departed")
        return original(view, selection)

    monkeypatch.setattr(retention, "closure_missing", export_closure)
    assert reasons(pin(leaf), write, live=(leaf, input_record)) == (Reason("dependency", (cited.id,)),)
    assert reasons(pin(input_record), write, live=(leaf, input_record)) == ()
    assert reasons(pin(input_record), write_with_strong, live=(leaf, input_record)) == (
        Reason("dependency", (neighbor.id,)),
    )


@pytest.mark.parametrize("problem", [
    "about-duplicate", "about-scalar", "about-nonstring", "about-untyped", "extra-note-field",
    "bad-title", "note-predecessor", "bad-address", "mixed-history", "missing-query", "old-query",
    "wrong-coordination-kind", "no-coordination-facet", "wrong-event-kind", "bad-rebuild",
    "mixed-endpoint-kinds", "missing-stamp", "id", "uid", "kind",
])
def test_invalid_local_citations_are_global(certified_work, monkeypatch, problem):
    x = fixture_proposition_node("x")
    listing = note(x.id)
    facet = listing.facets[stored.COORDINATION_FACET]
    more = ()
    if problem.startswith("about-"):
        facet["about"] = {
            "about-duplicate": [x.id, x.id], "about-scalar": x.id,
            "about-nonstring": [9], "about-untyped": ["proposition:"],
        }[problem]
    elif problem == "extra-note-field":
        facet["query"] = query()
    elif problem == "bad-title":
        listing = listing.model_copy(update={"title": ""})
    elif problem == "note-predecessor":
        older = revision("note", 4, local="e" * 32)
        listing = revision("note", 5, local="e" * 32, predecessors=(older,))
    elif problem == "bad-address":
        listing = revision("topic", 1, local=None, query=query())
    elif problem == "mixed-history":
        listing = revision("topic", 1, query=query())
        more = (revision("question", 2, query=query()),)
    elif problem in {"missing-query", "old-query"}:
        listing = revision("topic", 1, query=query())
        if problem == "old-query":
            more = (revision("topic", 2, query=query(), predecessors=(listing,)),)
            listing.facets[stored.COORDINATION_FACET]["query"] = {}
        else:
            del listing.facets[stored.COORDINATION_FACET]["query"]
    elif problem == "wrong-coordination-kind":
        listing = listing.model_copy(update={"id": "proposition:with-note-facet", "kind": "proposition"})
    elif problem == "no-coordination-facet":
        listing = listing.model_copy(update={"facets": {}})
    elif problem in {"wrong-event-kind", "bad-rebuild", "mixed-endpoint-kinds", "missing-stamp"}:
        listing = attestation(x.id, "proposition:y")
        if problem == "bad-rebuild":
            listing.facets[stored.COREFERENCE_ATTESTATION_FACET]["grounds"] = "Different grounds"
            listing = stored.stamp_semantic_identity(listing)
        elif problem == "mixed-endpoint-kinds":
            listing = attestation(x.id, "source:other")
        elif problem == "missing-stamp":
            del listing.facets[stored.SEMANTIC_IDENTITY_FACET]
    write = holder(certified_work / "write", listing, *more)
    carrier = holder(certified_work / "carrier", x)
    if problem == "wrong-event-kind":
        wrong = listing.model_copy(update={"kind": "proposition"})
        iterate, get = ReadView.iter_stored, ReadView.get

        def iter_changed(view):
            for node in iterate(view):
                yield wrong if view is write[1] and node.id == listing.id else node

        def get_wrong_kind(view, ref):
            return wrong if view is write[1] and ref == listing.id else get(view, ref)

        monkeypatch.setattr(ReadView, "iter_stored", iter_changed)
        monkeypatch.setattr(ReadView, "get", get_wrong_kind)
    if problem in {"id", "uid", "kind"}:
        get = ReadView.get

        def get_changed(view, ref):
            node = get(view, ref)
            if view is write[1] and ref == listing.id:
                return node.model_copy(update={problem: getattr(x, problem)})
            return node

        monkeypatch.setattr(ReadView, "get", get_changed)
    reason, = reasons(pin(carrier), write, live=(carrier,))
    assert reason.kind == "dependency"
    assert any(write[0] in detail and detail.startswith("write corpus ") and listing.kind in detail
               for detail in reason.detail)


def test_write_scan_failure_preserves_unresolved_provenance(certified_work, monkeypatch):
    cited = fixture_proposition_node("cited")
    missing = stored.run_node("missing", title="missing", spec="departed")
    write = holder(certified_work / "write", missing, note(cited.id))
    carrier = holder(certified_work / "carrier", cited)
    original = ReadView.iter_stored
    resolve = ReadView.resolve
    closure = retention.dependency_closure
    direct_reads = []
    walk_finished = False

    def damaged(view):
        yield from original(view)
        if view is write[1]:
            raise OSError("iterator broke after records")

    def finish_walk(*args, **kwargs):
        nonlocal walk_finished
        result = closure(*args, **kwargs)
        walk_finished = True
        return result

    def track(view, ref):
        if walk_finished:
            direct_reads.append(ref)
        return resolve(view, ref)

    monkeypatch.setattr(ReadView, "iter_stored", damaged)
    monkeypatch.setattr(ReadView, "resolve", track)
    monkeypatch.setattr(retention, "dependency_closure", finish_walk)
    reason, = reasons(pin(carrier), write, live=(carrier,))
    assert reason.kind == "dependency"
    assert "unresolved-reference analysis-spec:departed" in reason.detail
    assert any(detail.startswith(f"write corpus {write[0]} ") and "OSError" in detail for detail in reason.detail)
    assert reason.detail == tuple(sorted(set(reason.detail)))
    assert direct_reads == []


@pytest.mark.parametrize("fault", ["conflict-id", "conflict-content", "resolve", "get", "wrong-id", "identity"])
def test_citation_uncertainty_is_scoped_to_possible_holders(certified_work, monkeypatch, fault):
    x, y = (fixture_proposition_node(name) for name in ("x", "y"))
    write = holder(certified_work / "write", note(x.id, y.id))
    a = holder(certified_work / "a", x)
    b = holder(certified_work / "b", x)
    rival = x
    if fault == "conflict-content":
        rival = stored.stamp_semantic_identity(x.model_copy(update={"title": "different held record"}))
    if fault == "conflict-id":
        rival = stored.stamp_semantic_identity(
            fixture_proposition_node("new-x").model_copy(update={"deprecated_ids": [x.id]}),
        )
    c = holder(certified_work / "c", rival)
    absent = holder(certified_work / "absent", y)
    resolve, get = ReadView.resolve, ReadView.get
    identity = retention.content_identity
    inspected = []

    def inspect(view, ref):
        if ref == x.id:
            inspected.append(view.corpus_id)
            if view is c[1] and fault == "resolve":
                raise NodesError("failed resolution")
        return resolve(view, ref)

    def fetch(view, ref):
        if view is c[1] and ref == x.id:
            if fault == "get":
                raise OSError("failed read")
            if fault == "wrong-id":
                return y
            if fault == "identity":
                return get(view, ref).model_copy(update={"title": "identity failure"})
        return get(view, ref)

    def measure(node):
        if node.title == "identity failure":
            raise TypeError("identity failure")
        return identity(node)

    monkeypatch.setattr(ReadView, "resolve", inspect)
    monkeypatch.setattr(ReadView, "get", fetch)
    monkeypatch.setattr(retention, "content_identity", measure)
    expected = None
    for related in permutations((a, b, c)):
        # An alias for the write corpus must not replace the actual write view.
        shadow = (write[0], absent[1], write[2])
        live = (*related, absent, b, shadow)
        for possible in (a, b, c):
            inspected.clear()
            actual, = reasons(pin(possible), write, live=live)
            assert actual.kind == "dependency"
            assert len(inspected) == 5 and set(inspected) == {write[0], a[0], b[0], c[0], absent[0]}
            assert all(x.id in detail and c[0] in detail for detail in actual.detail)
            if fault.startswith("conflict"):
                assert ", ".join(sorted((a[0], b[0], c[0]))) in actual.detail[0]
            if expected is None:
                expected = actual
            assert actual == expected
        assert reasons(pin(absent), write, live=live) == (Reason("dependency", (y.id,)),)


def test_strong_direct_holder_failure_is_global_and_precedes_leaf_reads(certified_work, monkeypatch):
    x, cited = (fixture_proposition_node(name) for name in ("x", "cited"))
    provenance = stored.run_node("local", title="local", spec="", reads=(x.id,))
    write = holder(certified_work / "write", provenance, note(cited.id))
    a, b, failing = (holder(certified_work / name, x) for name in ("a", "b", "failing"))
    absent = holder(certified_work / "absent", cited)
    older = pin(a)
    intermediate = replace(pin(absent, 2), marker=replace(pin(absent, 2).marker,
                           supersedes=((older.corpus_id, older.marker.uid),)))
    group = (older, intermediate, held(4))
    group = (*group[:2], replace(group[2], marker=replace(group[2].marker,
                                 supersedes=((intermediate.corpus_id, intermediate.marker.uid),))))
    closure = retention.dependency_closure
    resolve = ReadView.resolve
    direct_leaves = []
    direct = False

    def finish_walk(*args, **kwargs):
        nonlocal direct
        direct = False
        result = closure(*args, **kwargs)
        assert result.unresolved == ()
        direct = True
        return result

    def inspect(view, ref):
        if direct and ref == cited.id:
            direct_leaves.append(ref)
        if direct and view is failing[1] and ref == x.id:
            raise OSError("direct strong holder failed")
        return resolve(view, ref)

    monkeypatch.setattr(retention, "dependency_closure", finish_walk)
    monkeypatch.setattr(ReadView, "resolve", inspect)
    expected = None
    for related in permutations((a, b, failing)):
        for item in (older, intermediate, held(3)):
            report = reasons(item, write, live=(*related, absent), chain_items=group)
            reason, = (reason for reason in report if reason.kind == "dependency")
            assert x.id in reason.detail[0] and failing[0] in reason.detail[0] and "OSError" in reason.detail[0]
            if expected is None:
                expected = reason
            assert reason == expected
    assert direct_leaves == []


@pytest.mark.parametrize("operation", ["get", "digest-enumeration"])
def test_provenance_walk_read_and_digest_failures_are_global(certified_work, graph, monkeypatch, operation):
    from beliefs.procedure import ModelInputs, procedure_from_stored

    config, _, dataset, proposition, *_ = graph
    procedure = procedure_from_stored(analysis_nodes(config.profile)[2])
    missing = stored.run_node("missing", title="missing", spec="departed")
    trigger = stored.run_node("trigger", title="trigger", spec="", reads=(proposition.id,))
    if operation == "digest-enumeration":
        trigger = stored.procedure_node(replace(procedure, inputs=ModelInputs(("sha256:" + "a" * 64,), ())))
    write = holder(certified_work / "write", trigger, missing, profile=config.profile)
    origin = holder(certified_work / "provenance-holder", proposition, dataset, profile=config.profile)
    original_iter, original_get = ReadView.iter_stored, ReadView.get

    def iterate(view):
        yield from original_iter(view)
        if operation == "digest-enumeration" and view is origin[1]:
            raise OSError("digest inventory unreadable")

    def get(view, ref):
        if operation == "get" and view is origin[1] and ref == proposition.id:
            raise NodesError("provenance read failed")
        return original_get(view, ref)

    monkeypatch.setattr(ReadView, "iter_stored", iterate)
    monkeypatch.setattr(ReadView, "get", get)
    reason, = reasons(held(1), write, live=(origin,))
    assert reason.kind == "dependency"
    assert "unresolved-reference analysis-spec:departed" in reason.detail
    expected_class = "NodesError" if operation == "get" else "OSError"
    assert any(origin[0] in detail and expected_class in detail for detail in reason.detail)


@pytest.mark.parametrize("other_tip", [False, True])
def test_cyclic_local_view_history_blocks_every_predecessor(certified_work, other_tip):
    target = fixture_proposition_node("cited")
    view = revision("topic", 1, query=query(({"addresses": [target.id]},)))
    cyclic = revision("topic", 1, predecessors=(view,), query=query(({"addresses": [target.id]},)))
    records = (cyclic, revision("topic", 2, query=query())) if other_tip else (cyclic,)
    write = holder(certified_work / "write", *records)
    carrier = holder(certified_work / "carrier", target)
    diagnostic = f"write corpus {write[0]} validate coordination history {cyclic.id} (coordination-supersession-cycle)"
    for predecessor in (pin(carrier), held(2)):
        assert reasons(predecessor, write, live=(carrier,)) == (Reason("dependency", (diagnostic,)),)
