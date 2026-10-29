"""Retirement preserves live inputs, attribution origins and their held chains."""
from dataclasses import fields, replace
from pathlib import Path

import pytest
from nodes.core.corpus import Corpus
from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.intents.publish import Destination
from beliefs.publish_request import pins_of
from beliefs.root import init_corpus_root, open_corpus
from beliefs.rules import REFERENCE_RULES
from beliefs.spec import SpecDraft, freeze
from helpers.world import FIXTURE_AUTHORITY, PROFILE, SPEC_FIELDS, build_spec_rig_world, open_rig

from science.publication import MarkerFields
from science.retention import Reason, dependency_closure, required
from science.supersession import Held


def holder(root, *nodes, profile=PROFILE):
    init_corpus_root(root, authority=FIXTURE_AUTHORITY)
    writer = open_corpus(root, authority=FIXTURE_AUTHORITY, profile=profile)
    writer.adopt_manifest(profile=pins_of(profile))
    # Publication subsets may omit a spec's target; authoring validation is not the read under test.
    corpus = Corpus(root)
    for node in nodes:
        corpus.add(node)
    view = ReadView.opened_at(root)
    return view.corpus_id, view, profile


def held(n, *predecessors, root=None, attributions=None, state="mounted"):
    return Held(f"p{n}", root or Path(f"/roots/p{n}"), MarkerFields(
        f"m{n}", "a" * 32, f"coord:{'b' * 32}@{'c' * 32}",
        Destination.remote("https://example.org/publications"), frozenset(),
        attributions or {}, tuple((f"p{p}", f"m{p}") for p in predecessors)), state)


@pytest.fixture
def graph(certified_work):
    (certified_work / "origin").mkdir()
    cfg, dataset = build_spec_rig_world(certified_work / "origin")
    with open_rig(cfg, ("spec",)) as (dispatcher, ctx):
        dispatcher.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=dataset))
        spec_node, = [n for n in ctx.write_view().iter_stored() if n.kind == "analysis-spec"]
    spec = stored.analysis_spec_value(spec_node, profile=cfg.profile)
    assessment = stored.assessment_node(
        "a", title="assessment", spec=spec.identity, run="run:original", proposition="proposition:p1",
        outcome="supported", interpretation_rule=spec.interpretation_rule,
        estimand=spec.estimand, applicability=spec.applicability)
    run = stored.run_node("original", title="original", spec=spec.identity)
    replay = stored.run_node("replayed", title="replayed", spec=spec.identity)
    verification = stored.verification_node(
        "v", title="verification", assessment="identity", assessment_ref=assessment.id,
        scope="replay", verdict="passed", derivation=(run.id, replay.id))
    origin = ReadView.opened_at(cfg.write_root)
    return cfg.profile, spec_node, origin.get(dataset), origin.get("proposition:p1"), assessment, run, replay, verification


def test_dependency_closure_reaches_a_verifications_target_and_its_runs_spec_through_facets(certified_work, graph):
    profile, spec, dataset, proposition, assessment, run, replay, verification = graph
    write = holder(certified_work / "write", verification)
    successor = holder(certified_work / "successor", assessment, run, profile=profile)
    predecessor = holder(certified_work / "predecessor", spec, dataset, proposition, replay, profile=profile)
    assert dependency_closure(write, (successor, predecessor)) == frozenset({
        verification.id, assessment.id, run.id, replay.id, spec.id, dataset.id, proposition.id})


def test_dependency_closure_reaches_a_specs_target_proposition(certified_work, graph):
    profile, spec, dataset, proposition, *_ = graph
    write = holder(certified_work / "write", spec, profile=profile)
    predecessor = holder(certified_work / "predecessor", dataset, proposition)
    assert dependency_closure(write, (predecessor,)) == frozenset({spec.id, dataset.id, proposition.id})


def test_dependency_closure_does_not_follow_supersedes_fields(certified_work, graph):
    profile, old_spec, dataset, proposition, assessment, run, replay, verification = graph
    value = stored.analysis_spec_value(old_spec, profile=profile)
    draft = SpecDraft(**{field.name: getattr(value, field.name) for field in fields(SpecDraft)})
    spec = stored.analysis_spec_node(freeze(draft, held_rules=REFERENCE_RULES, supersedes=value.identity))
    verification = stored.verification_node(
        "v", title="verification", assessment="identity", assessment_ref=assessment.id,
        scope="replay", verdict="passed", supersedes="verification:old")
    write = holder(certified_work / "write", spec, verification, profile=profile)
    assert dependency_closure(write, ()) == frozenset({spec.id, verification.id, dataset.id, proposition.id, assessment.id})


def test_dependency_closure_keeps_missing_addresses_and_stops_on_cycles(certified_work):
    first = stored.run_node("first", title="first", spec="missing", reads=("run:second",))
    second = stored.run_node("second", title="second", spec="missing", reads=(first.id,))
    write = holder(certified_work / "write", first)
    other = holder(certified_work / "other", second)
    assert dependency_closure(write, (other,)) == frozenset({first.id, second.id, "analysis-spec:missing"})


@pytest.mark.parametrize("arm", ["node", "route"])
def test_dependency_closure_follows_correction_record_targets(certified_work, arm):
    address = "proposition:target" if arm == "node" else "dataset:target"
    target = (stored.NodeTarget(address, address, "identity") if arm == "node"
              else stored.RouteTarget(address, address, "identity", "route"))
    correction = stored.retraction_node(title="correction", target=target, reason="authored-error",
        rationale="incorrect", grounds=("source:grounds",), actor="fixture", event_token="event")
    write = holder(certified_work / "write", correction)
    assert dependency_closure(write, ()) == frozenset({correction.id, address, "source:grounds"})


def test_required_by_dependency_lists_only_addresses_no_other_live_corpus_holds_equal(certified_work, graph):
    profile, spec, dataset, proposition, assessment, run, replay, verification = graph
    write = holder(certified_work / "write", verification)
    predecessor = holder(certified_work / "predecessor", spec, dataset, proposition, assessment, run, replay, profile=profile)
    successor = holder(certified_work / "successor", dataset, proposition, assessment, run, replay, profile=profile)
    p1 = replace(held(1, root=certified_work / "predecessor"), corpus_id=predecessor[0])
    args = dict(keep=(), group_chain=(p1,), tip=("p2", "m2"), mounted=(p1,), write_root=write)
    assert required(p1, live=(predecessor, successor), **args) == (Reason("dependency", (spec.id,)),)
    equal = holder(certified_work / "equal", spec, profile=profile)
    assert required(p1, live=(predecessor, successor, equal), **args) == ()
    differing = holder(certified_work / "differing", spec.model_copy(update={"title": "different"}), profile=profile)
    assert required(p1, live=(predecessor, successor, differing), **args) == (Reason("dependency", (spec.id,)),)


@pytest.fixture
def empty_write(certified_work):
    return holder(certified_work / "write")


def reasons(predecessor, write, *, keep=(), chain_items=None, mounted=(), live=()):
    return required(predecessor, keep=keep, group_chain=chain_items or (predecessor,),
                    tip=("p4", "m4"), mounted=mounted, write_root=write, live=live)


def test_required_by_configuration(empty_write):
    assert reasons(held(1), empty_write, keep=("p1",)) == (Reason("configuration", ()),)


def test_required_by_attribution_names_the_naming_corpus(empty_write):
    naming = held(8, attributions={"proposition:p": ("p1", "m1")})
    retired = replace(held(9, attributions={"proposition:p": ("p1", "m1")}), state="retired")
    assert reasons(held(1), empty_write, mounted=(retired, naming)) == (Reason("attribution", ("p8",)),)


@pytest.mark.parametrize("older_reason", ["configuration", "attribution", "dependency"])
def test_chain_retention_keeps_every_publication_between_a_kept_one_and_the_tip(certified_work, empty_write, older_reason):
    node = stored.proposition_node("target", title="target", claim={"operator": "affects"})
    source = holder(certified_work / "source", node)
    p1 = replace(held(1), corpus_id=source[0])
    p2 = replace(held(2), marker=replace(held(2).marker, supersedes=((p1.corpus_id, "m1"),)))
    p3, p4 = held(3, 2), held(4, 3)
    items = (p1, p2, p3, p4)
    keep = (p1.corpus_id,) if older_reason == "configuration" else ()
    mounted = (held(8, attributions={node.id: (p1.corpus_id, "m1")}),) if older_reason == "attribution" else ()
    write = empty_write
    if older_reason == "dependency":
        run = stored.run_node("local", title="local", spec="missing", reads=(node.id,))
        write = holder(certified_work / "dependent", run)
    for predecessor in (p2, p3):
        assert reasons(predecessor, write, keep=keep, chain_items=items, mounted=mounted, live=(source,)) == (
            Reason("chain", (p1.corpus_id,)),)


def test_required_returns_all_reasons_in_kind_order_with_sorted_dependencies(certified_work):
    a = stored.proposition_node("a", title="a", claim={"operator": "affects"})
    z = stored.proposition_node("z", title="z", claim={"operator": "affects"})
    source = holder(certified_work / "source", z, a)
    run = stored.run_node("local", title="local", spec="missing", reads=(z.id, a.id))
    write = holder(certified_work / "write", run)
    p0 = held(0)
    p1 = replace(held(1, 0), corpus_id=source[0])
    p4 = replace(held(4), marker=replace(held(4).marker, supersedes=((p1.corpus_id, "m1"),)))
    naming = held(8, attributions={a.id: (p1.corpus_id, "m1")})
    assert reasons(p1, write, keep=("p0", p1.corpus_id), chain_items=(p0, p1, p4), mounted=(naming,),
                   live=(source,)) == (
        Reason("configuration", ()), Reason("chain", ("p0",)), Reason("attribution", ("p8",)),
        Reason("dependency", ("proposition:a", "proposition:z")))


def test_nothing_required_is_empty(empty_write):
    assert reasons(held(1), empty_write) == ()
    assert reasons(held(2), empty_write, keep=("p1",), chain_items=(held(1), held(2), held(4, 2))) == ()
