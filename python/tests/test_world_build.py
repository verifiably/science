"""Coherent preflight and corpus capture: §5.2 and §5.3, exercised end to end.

**What a build is here, and what it deliberately is not.** This module covers
everything up to — and stopping exactly at — the frozen build draft. Preflight
runs under the world lock and answers "may this build run at all, over exactly
these corpora, with exactly these four rules"; capture then enters each covered
corpus's capture hold in sorted order and takes, under that one exclusion, the
corpus's chain head, its corpus-state identity, one enumeration of its stored
nodes, and the state identity again. Publication is Task 9's and appears here
only as an absence to assert: a refused build writes nothing.

**The refusals are ordered, and the order is asserted rather than assumed.**
Several arms below construct a world with two faults at once and pin which one
the build reports. That is not pedantry: a build that reported the second fault
would be a build that inspected a registry, or ran a rule's fixtures, before it
knew the coverage was admissible.

**Concurrency here is event-driven.** Every arm that needs two threads gates
them with `threading.Event` and bounded `join`, and the seams that block are
the injected chain callback and the enumeration helper. No arm sleeps: a sleep
would turn "the capture refused without waiting" into "the capture refused
within a second", which is a different and much weaker claim.
"""

from __future__ import annotations

import subprocess
import sys
import threading
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest
from fixtures_cut6 import PINS
from nodes.core.corpus import Corpus
from nodes.core.node import Node
from nodes.core.write_plan import DefaultExecutor

from science import root as composition_root
from science import stored
from science.corpus import CorpusWriter, _root_state_for
from science.errors import (
    BuildContended,
    BuildHold,
    CaptureDrift,
    CoverageNotLive,
    CoverageUnknown,
    CoverageUnresolvable,
    EnumeratedKindUngoverned,
    RuleNotHeld,
)
from science.world import derive, epoch, registry, rules

JOIN_TIMEOUT = 20.0
"""Every bounded join and event wait in this module. Long enough that a loaded
machine does not fail a passing arm, short enough that a genuine deadlock is a
failure rather than a hung suite."""

ALPHA = "a" * 32
BETA = "b" * 32
GAMMA = "c" * 32

SYMBOL_KINDS = {
    "derive_producer_snapshot": "producer",
    "enumerate_retractions": "retraction-enumeration",
    "enumerate_certifications": "certification-enumeration",
    "reduce_coreference": "coreference-reduction",
}
"""Which receipt kind each shipped rule's symbol derives. The build input is
keyed by receipt kind (§7.5's four); the rules store is keyed by identity and
knows nothing of kinds, so the join is the caller's and is written out here
rather than guessed inside a helper."""


# --- the harness -------------------------------------------------------------


class ChainHeads:
    """The injected `(genesis_digest, tip)` callback, recording every call.

    It is deliberately *not* a stub that ignores its argument: preflight calls
    it on the world root and capture calls it once per carrier, and several
    arms turn on which root it was handed and on what was true at that moment.
    """

    def __init__(self) -> None:
        self.roots: list[Path] = []
        self.observations: list[object] = []
        self.observe = None
        self.gate: threading.Event | None = None
        self.gate_root: Path | None = None
        self.entered = threading.Event()

    def __call__(self, target: Path) -> tuple[str, str]:
        target = Path(target)
        self.roots.append(target)
        if self.observe is not None:
            self.observations.append(self.observe(target))
        if self.gate is not None and target == self.gate_root:
            self.entered.set()
            assert self.gate.wait(JOIN_TIMEOUT), "the gated capture was never released"
        return (f"genesis:{target.name}", f"tip:{target.name}")


def make_world(tmp_path: Path, *corpus_roots: Path, chain_head: ChainHeads | None = None) -> registry.World:
    """A world over `corpus_roots`, writing with the plain executor.

    The corpus executor factory is `DefaultExecutor`, the same object every
    `CorpusWriter` in this module is built with, because `_root_state_for`
    keeps one state — and therefore one operation lock — per root and refuses
    a second factory for a root it already holds.
    """
    return registry.World(
        registry.WorldConfig(tmp_path / "world", "f" * 32, corpus_roots),
        DefaultExecutor,
        chain_head=chain_head or ChainHeads(),
        corpus_executor_factory=DefaultExecutor,
    )


def corpus_at(root: Path, corpus_id: str, nodes: tuple[Node, ...] = ()) -> Path:
    """A corpus root carrying a closed manifest and the given stored nodes."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "corpus.yaml").write_bytes(registry.manifest_bytes(registry.CorpusManifest(2, corpus_id, PINS)))
    handle = Corpus(root)
    for node in nodes:
        handle.add(node)
    return root


def sample_nodes() -> tuple[Node, ...]:
    """One dataset, one run producing it, and one retraction naming the run.

    Enough that all four derivations have something to say: the producer
    snapshot sees the `produces` edge, the retraction enumeration and the
    discovery map see the retraction, and the certification and coreference
    reductions see the empty enumerations §13 defers them to.
    """
    dataset = stored.dataset_node("one", title="dataset one")
    run = stored.run_node("one", title="run one", spec="analysis-spec:one", produces=[dataset.id])
    retraction = stored.retraction_node(
        title="retraction one",
        target=stored.NodeTarget(ref=run.id, resolved=run.id, content_identity="d" * 64),
        reason="authored-error",
        rationale="the run was misconfigured",
        grounds=[dataset.id],
        actor="alice",
        event_token="event-one",
    )
    return (dataset, run, retraction)


def install_bindings(world: registry.World) -> dict[str, rules.RuleBinding]:
    """Hold the four shipped rules and return them keyed by receipt kind."""
    return {
        SYMBOL_KINDS[bundle.symbol]: rules.install_rule_binding(world, bundle)
        for bundle in rules.shipped_rule_bundles()
    }


def admitted_world(
    tmp_path: Path,
    coverage: tuple[str, ...] = (ALPHA,),
    *,
    chain_head: ChainHeads | None = None,
) -> tuple[registry.World, dict[str, rules.RuleBinding], dict[str, Path]]:
    """A world holding the four rules with every id in `coverage` admitted."""
    roots = {corpus_id: corpus_at(tmp_path / corpus_id[:6], corpus_id, sample_nodes()) for corpus_id in coverage}
    world = make_world(tmp_path, *roots.values(), chain_head=chain_head)
    for corpus_root in roots.values():
        world.admit(corpus_root, provenance=registry.Fresh(), actor="alice")
    return world, install_bindings(world), roots


def build(world: registry.World, coverage: tuple[str, ...], bindings: dict[str, rules.RuleBinding]):
    return epoch._capture_build_inputs(world, coverage=frozenset(coverage), bindings=bindings)


def lock_for(corpus_root: Path):
    return _root_state_for(corpus_root, DefaultExecutor).lock


def stray_file(corpus_root: Path, before: frozenset[Path]) -> Path:
    """The one stored document a corpus gained since `before`."""
    now = frozenset(path for path in corpus_root.rglob("*.md"))
    gained = now - before
    assert len(gained) == 1, f"expected exactly one new stored document, found {sorted(gained)}"
    return next(iter(gained))


# --- Step 1: the root boundary ------------------------------------------------


class TestTheCompositionRootReadsTheChain:
    def test_the_callback_passes_the_backend_root_metadata_root_and_storage(self, monkeypatch, tmp_path):
        calls: list[tuple[object, ...]] = []

        class View:
            genesis_digest = "genesis-digest"
            tip = "tip-digest"
            entries = (("genesis-digest", object()),)

        def record(backend, project_root, metadata_root, storage):
            calls.append((backend, project_root, metadata_root, storage))
            return View()

        monkeypatch.setattr(composition_root, "read_chain", record)
        target = tmp_path / "some-root"

        answer = composition_root.chain_head_reader()(target)

        assert calls == [
            (
                composition_root._PRODUCTION_BACKEND,
                str(target),
                str(composition_root.metadata_root_for(target)),
                composition_root.PRODUCTION_STORAGE,
            )
        ]
        assert answer == ("genesis-digest", "tip-digest")

    def test_only_the_two_digests_leave_the_composition_root(self, monkeypatch, tmp_path):
        class View:
            genesis_digest = "genesis-digest"
            tip = "tip-digest"
            entries = ("an entry nothing above the boundary may see",)

        monkeypatch.setattr(composition_root, "read_chain", lambda *_args: View())

        answer = composition_root.chain_head_reader()(tmp_path)

        assert type(answer) is tuple
        assert all(type(member) is str for member in answer)
        assert len(answer) == 2

    def test_an_opened_world_carries_the_composition_roots_reader(self, monkeypatch, tmp_path):
        from test_root import patch_world_engine

        patch_world_engine(monkeypatch, [])
        config = registry.WorldConfig(tmp_path / "world", "1" * 32, ())
        composition_root.init_world_root(config)

        world = composition_root.open_world(config)

        assert world._chain_head is composition_root.chain_head_reader()
        assert world._corpus_executor_factory is composition_root.durable_executor_factory()


@pytest.mark.parametrize("module", ["derive", "epoch", "registry", "rules"])
def test_each_world_module_imports_first_without_a_cycle(module):
    """Every world module is importable *first* in a fresh interpreter.

    `rules` imports `epoch`, `epoch` imports `rules` and `derive`, and `derive`
    imports `epoch`. All three edges are module-form and every use is at call
    time, which is what makes the cycle resolvable in every order — a name-form
    import of any of them would raise on exactly one of these four entries.
    """
    completed = subprocess.run(
        [sys.executable, "-c", f"import science.world.{module}"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


# --- Step 2: preflight --------------------------------------------------------


def test_build_refuses_unadmitted_manifest_carrier(tmp_path):
    """X7. A carrier is present and readable and the id is still unknown.

    Presence is not admission: the manifest is the corpus's own claim about
    itself, and a world that let one into a build would be admitting corpora by
    filesystem configuration.
    """
    corpus_root = corpus_at(tmp_path / "alpha", ALPHA, sample_nodes())
    world = make_world(tmp_path, corpus_root)
    bindings = install_bindings(world)

    with pytest.raises(CoverageUnknown) as refusal:
        build(world, (ALPHA,), bindings)

    assert ALPHA in str(refusal.value)
    assert not (world.config.world_root / "epochs").exists()


def test_admission_allows_same_build_preflight(tmp_path):
    """X7's positive half: the *same* declared build runs once the id is admitted."""
    corpus_root = corpus_at(tmp_path / "alpha", ALPHA, sample_nodes())
    world = make_world(tmp_path, corpus_root)
    bindings = install_bindings(world)
    with pytest.raises(CoverageUnknown):
        build(world, (ALPHA,), bindings)

    world.admit(corpus_root, provenance=registry.Fresh(), actor="alice")
    draft = build(world, (ALPHA,), bindings)

    assert draft.coverage == (ALPHA,)
    assert draft.capture.coverage == (ALPHA,)


def test_build_refuses_duplicate_carrier_coverage(tmp_path):
    """X5. Two configured roots carry one admitted id: no build, not a choice."""
    first = corpus_at(tmp_path / "first", ALPHA, sample_nodes())
    second = corpus_at(tmp_path / "second", ALPHA, sample_nodes())
    world = make_world(tmp_path, first, second)
    world.admit(first, provenance=registry.Fresh(), actor="alice")
    bindings = install_bindings(world)

    with pytest.raises(CoverageUnresolvable) as refusal:
        build(world, (ALPHA,), bindings)

    assert str(first) in str(refusal.value) and str(second) in str(refusal.value)


class TestPreflightOrder:
    def test_the_chain_head_is_read_under_the_world_lock_before_any_world_file(self, monkeypatch, tmp_path):
        order: list[str] = []
        heads = ChainHeads()
        world, bindings, _roots = admitted_world(tmp_path, (ALPHA,), chain_head=heads)

        scan = registry._scan_registry
        resolve = rules._locked_resolve_rule_bindings
        heads.observe = lambda _target: order.append("chain-head") or world._state.lock.locked()
        monkeypatch.setattr(
            registry, "_scan_registry", lambda world_root: (order.append("registry"), scan(world_root))[1]
        )
        monkeypatch.setattr(
            rules,
            "_locked_resolve_rule_bindings",
            lambda world_root, held: (order.append("rules"), resolve(world_root, held))[1],
        )

        build(world, (ALPHA,), bindings)

        assert order[:3] == ["chain-head", "registry", "rules"]
        assert heads.observations[0] is True
        assert heads.roots[0] == world.config.world_root

    def test_the_world_lock_is_released_before_any_corpus_is_captured(self, tmp_path):
        heads = ChainHeads()
        world, bindings, roots = admitted_world(tmp_path, (ALPHA,), chain_head=heads)
        heads.observe = lambda target: (target, world._state.lock.locked())

        build(world, (ALPHA,), bindings)

        assert heads.observations == [(world.config.world_root, True), (roots[ALPHA], False)]

    def test_coverage_is_checked_before_the_rule_bindings(self, tmp_path):
        corpus_root = corpus_at(tmp_path / "alpha", ALPHA, sample_nodes())
        world = make_world(tmp_path, corpus_root)
        unheld = {kind: rules.RuleBinding("1" * 64, "2" * 64) for kind in SYMBOL_KINDS.values()}

        with pytest.raises(CoverageUnknown):
            build(world, (ALPHA,), unheld)

    def test_admission_is_checked_before_liveness_and_liveness_before_the_carrier(self, tmp_path):
        # Two ids, both faulty, and the sorted-first one's fault is the one
        # reported: ALPHA is retired, BETA has no carrier at all.
        alpha_root = corpus_at(tmp_path / "alpha", ALPHA, sample_nodes())
        world = make_world(tmp_path, alpha_root)
        world.admit(alpha_root, provenance=registry.Fresh(), actor="alice")
        world.retire(ALPHA, actor="alice")
        bindings = install_bindings(world)

        with pytest.raises(CoverageNotLive) as refusal:
            build(world, (ALPHA, BETA), bindings)

        assert ALPHA in str(refusal.value)

    def test_a_retired_id_refuses_even_with_a_single_present_carrier(self, tmp_path):
        corpus_root = corpus_at(tmp_path / "alpha", ALPHA, sample_nodes())
        world = make_world(tmp_path, corpus_root)
        world.admit(corpus_root, provenance=registry.Fresh(), actor="alice")
        world.depart(ALPHA, actor="alice")
        bindings = install_bindings(world)

        with pytest.raises(CoverageNotLive):
            build(world, (ALPHA,), bindings)

    def test_an_admitted_live_id_with_no_carrier_is_unresolvable(self, tmp_path):
        alpha_root = corpus_at(tmp_path / "alpha", ALPHA, sample_nodes())
        world = make_world(tmp_path, alpha_root)
        world.admit(alpha_root, provenance=registry.Fresh(), actor="alice")
        registry._scan_registry(world.config.world_root)
        # BETA is admitted through a carrier the world then stops configuring.
        beta_root = corpus_at(tmp_path / "beta", BETA, sample_nodes())
        world.admit(beta_root, provenance=registry.Fresh(), actor="alice")
        bindings = install_bindings(world)

        with pytest.raises(CoverageUnresolvable) as refusal:
            build(world, (ALPHA, BETA), bindings)

        assert BETA in str(refusal.value)

    def test_an_unheld_binding_refuses_after_the_coverage_resolves(self, tmp_path):
        world, bindings, _roots = admitted_world(tmp_path, (ALPHA,))
        removed = dict(bindings)
        rules.remove_rule_binding(world, removed["producer"])

        with pytest.raises(RuleNotHeld):
            build(world, (ALPHA,), removed)

    def test_every_receipt_kind_must_be_named_exactly_once(self, tmp_path):
        world, bindings, _roots = admitted_world(tmp_path, (ALPHA,))
        short = {kind: binding for kind, binding in bindings.items() if kind != "producer"}

        with pytest.raises(ValueError, match="receipt kind"):
            build(world, (ALPHA,), short)

    def test_preflight_pins_a_sorted_carrier_mapping_and_never_substitutes_live_ids(self, tmp_path):
        # Three admitted live corpora; the build declares two of them, out of
        # order. Nothing about the third reaches the capture, and its operation
        # lock is never taken.
        world, bindings, roots = admitted_world(tmp_path, (GAMMA, ALPHA, BETA))
        untouched = lock_for(roots[GAMMA])
        generation = untouched._capture_generation

        preflight = epoch._preflight(world, coverage=frozenset({BETA, ALPHA}), bindings=bindings)

        assert preflight.coverage == (ALPHA, BETA)
        assert list(preflight.carriers) == [ALPHA, BETA]
        assert preflight.carriers[ALPHA] == roots[ALPHA]
        assert preflight.carriers[BETA] == roots[BETA]
        assert untouched._capture_generation == generation

    def test_the_build_start_world_head_is_the_preflight_tip(self, tmp_path):
        heads = ChainHeads()
        world, bindings, _roots = admitted_world(tmp_path, (ALPHA,), chain_head=heads)

        draft = build(world, (ALPHA,), bindings)

        assert draft.world_anchor.subject == world.config.world_id
        assert draft.world_anchor.head_digest == f"tip:{world.config.world_root.name}"
        assert draft.world_anchor.genesis_digest == f"genesis:{world.config.world_root.name}"


# --- Step 3: serial coherent capture ------------------------------------------


def test_chain_head_and_state_are_captured_in_one_hold(monkeypatch, tmp_path):
    """X9. One hold, one generation, four observations inside it.

    The chain head, the pre-enumeration state, the enumeration and the
    recomputed state each record the operation lock's holder and capture
    generation at the moment they run. All four must read `capture` and the
    same generation: a head read one generation later is a head from a
    different exclusion, and the epoch's anchor would then name a chain the
    captured state never coexisted with.
    """
    heads = ChainHeads()
    world, bindings, roots = admitted_world(tmp_path, (ALPHA,), chain_head=heads)
    lock = lock_for(roots[ALPHA])
    seen: list[tuple[str, object, int]] = []

    def observe(stage: str) -> None:
        seen.append((stage, lock._holder, lock._capture_generation))

    heads.observe = lambda target: observe("chain-head") if target == roots[ALPHA] else None
    state_identity = registry.corpus_state_identity
    enumerate_records = epoch._captured_records

    def watched_state(corpus_root):
        observe("state")
        return state_identity(corpus_root)

    def watched_records(corpus_root):
        observe("enumerate")
        return enumerate_records(corpus_root)

    monkeypatch.setattr(registry, "corpus_state_identity", watched_state)
    monkeypatch.setattr(epoch, "_captured_records", watched_records)

    draft = build(world, (ALPHA,), bindings)

    assert [stage for stage, _holder, _generation in seen] == ["chain-head", "state", "enumerate", "state"]
    assert {holder for _stage, holder, _generation in seen} == {"capture"}
    assert len({generation for _stage, _holder, generation in seen}) == 1
    assert lock._holder is None
    assert draft.anchors == (epoch._Anchor(ALPHA, f"genesis:{roots[ALPHA].name}", f"tip:{roots[ALPHA].name}"),)


def test_api_write_refuses_during_capture(tmp_path):
    """X9. A corpus write arriving while a capture holds the root is `BuildHold`."""
    heads = ChainHeads()
    world, bindings, roots = admitted_world(tmp_path, (ALPHA,), chain_head=heads)
    release = threading.Event()
    heads.gate = release
    heads.gate_root = roots[ALPHA]
    outcome: list[object] = []

    def run() -> None:
        try:
            outcome.append(build(world, (ALPHA,), bindings))
        except BaseException as caught:  # noqa: BLE001 — the arm reports whatever the build did
            outcome.append(caught)

    builder = threading.Thread(target=run, name="capture")
    builder.start()
    try:
        assert heads.entered.wait(JOIN_TIMEOUT), "the capture never entered its hold"
        writer = CorpusWriter(roots[ALPHA], DefaultExecutor)
        with pytest.raises(BuildHold):
            writer.add(stored.dataset_node("blocked", title="blocked"))
    finally:
        release.set()
        builder.join(JOIN_TIMEOUT)

    assert not builder.is_alive()
    assert isinstance(outcome[0], epoch._BuildDraft)


def test_capture_refuses_active_writer_without_waiting(tmp_path):
    """X9. A build behind a writer refuses at once rather than queueing.

    "Without waiting" is proved by the writer never releasing: the build's
    refusal is observed while the writer's hold is still in force, so no
    reading of the outcome is available in which the build waited for it.
    """
    world, bindings, roots = admitted_world(tmp_path, (ALPHA,))
    lock = lock_for(roots[ALPHA])
    outcome: list[object] = []

    def run() -> None:
        try:
            outcome.append(build(world, (ALPHA,), bindings))
        except BaseException as caught:  # noqa: BLE001 — the arm reports whatever the build did
            outcome.append(caught)

    with lock:
        builder = threading.Thread(target=run, name="contended-capture")
        builder.start()
        builder.join(JOIN_TIMEOUT)
        held_throughout = lock._holder

    assert not builder.is_alive(), "the build queued behind a corpus writer"
    assert held_throughout == "writer"
    assert isinstance(outcome[0], BuildContended)


def test_capture_drift_discards_without_publication(monkeypatch, tmp_path):
    """X9. Raw content moves inside the hold; the whole capture is discarded.

    The mutation is a raw filesystem edit, which is the only writer the hold
    cannot exclude. The second state computation sees it, and the build refuses
    with `CaptureDrift`: no draft, no second attempt, and nothing written
    beneath the world root.
    """
    world, bindings, roots = admitted_world(tmp_path, (ALPHA,))
    corpus_root = roots[ALPHA]
    before = frozenset(corpus_root.rglob("*.md"))
    Corpus(corpus_root).add(stored.dataset_node("drift", title="drift"))
    stash = tmp_path / "stashed.md"
    home = stray_file(corpus_root, before)
    home.rename(stash)

    enumerate_records = epoch._captured_records
    state_identity = registry.corpus_state_identity
    attempts: list[Path] = []
    states: list[Path] = []

    def drifting_records(root: Path):
        attempts.append(root)
        stash.rename(home)
        return enumerate_records(root)

    monkeypatch.setattr(epoch, "_captured_records", drifting_records)
    monkeypatch.setattr(registry, "corpus_state_identity", lambda root: (states.append(root), state_identity(root))[1])

    with pytest.raises(CaptureDrift) as refusal:
        build(world, (ALPHA,), bindings)

    assert ALPHA in str(refusal.value)
    assert attempts == [corpus_root], "the build retried a drifted capture"
    assert states == [corpus_root, corpus_root], "the build recomputed the state more than twice"
    assert not (world.config.world_root / "epochs").exists()
    assert lock_for(corpus_root)._holder is None


def test_raw_aba_during_capture_is_undetectable(monkeypatch, tmp_path):
    """X9's stated limit, written as a limit and not as a bug.

    A raw edit that adds a record and removes it again inside one hold leaves
    both corpus-state computations identical, so the drift check — which
    compares two states and nothing else — cannot see it. The enumeration in
    between saw the intermediate corpus, and the captured records prove it.

    Nothing here is a defect to fix at this layer: detecting A→B→A needs a
    witness the corpus does not keep (substrate §4.2.1's recorded-history
    bound). What the arm pins is that the build does not *claim* otherwise —
    the captured state is exactly the state both computations saw, and no
    freshness claim beyond it is published.
    """
    world, bindings, roots = admitted_world(tmp_path, (ALPHA,))
    corpus_root = roots[ALPHA]
    before = frozenset(corpus_root.rglob("*.md"))
    interloper = stored.dataset_node("interloper", title="interloper")
    Corpus(corpus_root).add(interloper)
    stash = tmp_path / "interloper.md"
    home = stray_file(corpus_root, before)
    home.rename(stash)
    quiet_state = registry.corpus_state_identity(corpus_root)

    enumerate_records = epoch._captured_records

    def aba_records(root: Path):
        stash.rename(home)
        try:
            return enumerate_records(root)
        finally:
            home.rename(stash)

    monkeypatch.setattr(epoch, "_captured_records", aba_records)

    draft = build(world, (ALPHA,), bindings)

    captured = draft.capture.corpora[0]
    assert captured.corpus_state == quiet_state
    assert interloper.id in {record.address for record in captured.records}
    assert interloper.id not in {node.id for node in Corpus(corpus_root).all()}


def test_four_receipts_share_identical_corpus_states(tmp_path):
    """X9. One captured state per corpus, and all four receipts carry it.

    The draft holds exactly one `corpus_states` value — there is nowhere in it
    for a per-kind state to live — and the four rules it resolved all run over
    the one captured projection. That is what makes the four receipts of one
    epoch comparable at all.
    """
    world, bindings, _roots = admitted_world(tmp_path, (BETA, ALPHA))

    draft = build(world, (ALPHA, BETA), bindings)

    receipts = derive.derivation_receipts(
        snapshot=derive.producer_snapshot(draft.run("producer")),
        enumeration=derive.retraction_enumeration(draft.run("retraction-enumeration")),
        inventory=derive.certification_inventory(draft.run("certification-enumeration")),
        coreference=derive.coreference_map(draft.run("coreference-reduction")),
        corpus_states=draft.corpus_states,
        bindings=draft.bindings,
    )

    assert len(receipts) == 4
    assert {receipt.corpus_states for receipt in receipts} == {draft.corpus_states}
    assert draft.corpus_states == tuple(
        sorted((captured.corpus_id, captured.corpus_state) for captured in draft.capture.corpora)
    )
    assert [corpus_id for corpus_id, _state in draft.corpus_states] == [ALPHA, BETA]


class TestSerialCapture:
    def test_corpora_are_captured_serially_in_sorted_id_order(self, tmp_path):
        heads = ChainHeads()
        world, bindings, roots = admitted_world(tmp_path, (GAMMA, ALPHA, BETA), chain_head=heads)
        locks = {corpus_id: lock_for(root) for corpus_id, root in roots.items()}
        heads.observe = lambda target: tuple(
            sorted(corpus_id for corpus_id, lock in locks.items() if lock._holder is not None)
        )

        draft = build(world, (ALPHA, BETA, GAMMA), bindings)

        assert heads.roots == [world.config.world_root, roots[ALPHA], roots[BETA], roots[GAMMA]]
        assert heads.observations == [(), (ALPHA,), (BETA,), (GAMMA,)]
        assert [anchor.subject for anchor in draft.anchors] == [ALPHA, BETA, GAMMA]

    def test_every_stored_node_is_enumerated_once_and_feeds_all_four_rules(self, monkeypatch, tmp_path):
        world, bindings, roots = admitted_world(tmp_path, (ALPHA,))
        passes: list[Path] = []
        enumerate_records = epoch._captured_records
        monkeypatch.setattr(
            epoch, "_captured_records", lambda root: (passes.append(root), enumerate_records(root))[1]
        )

        draft = build(world, (ALPHA,), bindings)

        assert passes == [roots[ALPHA]]
        stored_ids = {node.id for node in Corpus(roots[ALPHA]).all()}
        assert {record.address for record in draft.capture.corpora[0].records} == stored_ids

        supplied: list[object] = []
        for kind in sorted(epoch.DERIVATION_KINDS):
            held = draft.held[kind]
            invoke = held.invoke
            draft.run(kind)
            supplied.append(draft.capture.rule_input())
            assert invoke is held.invoke
        assert len(supplied) == 4
        assert all(value == supplied[0] for value in supplied)

    def test_the_producer_snapshot_sees_the_captured_produces_edge(self, tmp_path):
        world, bindings, _roots = admitted_world(tmp_path, (ALPHA,))

        draft = build(world, (ALPHA,), bindings)
        snapshot = derive.producer_snapshot(draft.run("producer"))

        assert snapshot.coverage == (ALPHA,)
        assert dict(snapshot.producers) == {"dataset:one": ("run:one",)}

    def test_the_retraction_enumeration_carries_the_captured_resolution(self, tmp_path):
        world, bindings, _roots = admitted_world(tmp_path, (ALPHA,))

        draft = build(world, (ALPHA,), bindings)
        enumeration = derive.retraction_enumeration(draft.run("retraction-enumeration"))

        assert [resolution for _ref, resolution in enumeration.found] == ["upheld"]
        assert all(resolution in epoch.RETRACTION_RESOLUTIONS for _ref, resolution in enumeration.found)

    def test_a_retracted_retraction_is_captured_as_overturned(self, tmp_path):
        dataset, run, first = sample_nodes()
        counter = stored.retraction_node(
            title="counter retraction",
            target=stored.NodeTarget(ref=first.id, resolved=first.id, content_identity="e" * 64),
            reason="authored-error",
            rationale="the first retraction was wrong",
            grounds=[dataset.id],
            actor="bob",
            event_token="event-two",
        )
        corpus_root = corpus_at(tmp_path / "alpha", ALPHA, (dataset, run, first, counter))
        world = make_world(tmp_path, corpus_root)
        world.admit(corpus_root, provenance=registry.Fresh(), actor="alice")
        bindings = install_bindings(world)

        draft = build(world, (ALPHA,), bindings)
        resolutions = {
            record.address: record.retraction.resolution
            for record in draft.capture.corpora[0].records
            if record.retraction is not None
        }

        assert resolutions == {first.id: "overturned", counter.id: "upheld"}

    def test_the_discovery_map_groups_the_captured_targets(self, tmp_path):
        world, bindings, _roots = admitted_world(tmp_path, (ALPHA,))

        draft = build(world, (ALPHA,), bindings)
        discovery = derive.retraction_discovery_map(draft.capture)

        assert set(discovery) == {"run:one"}

    def test_only_immutable_captured_values_leave_the_hold(self, tmp_path):
        world, bindings, roots = admitted_world(tmp_path, (ALPHA,))

        draft = build(world, (ALPHA,), bindings)

        with pytest.raises(FrozenInstanceError):
            draft.coverage = ()
        with pytest.raises(FrozenInstanceError):
            draft.capture.corpora[0].records[0].address = "x"
        assert not any(isinstance(getattr(draft, field.name), Path) for field in fields(draft))
        assert str(roots[ALPHA]) not in repr(draft.capture)
        assert type(draft.capture.corpora) is tuple
        with pytest.raises(TypeError):
            draft.held["producer"] = None


# --- Step 4: the ungoverned enumerated kinds ----------------------------------


@pytest.mark.parametrize("kind", ["coreference-attestation", "instrument-certification"])
def test_build_refuses_ungoverned_enumerated_record(tmp_path, kind):
    """§13's deferral, enforced at capture rather than trusted.

    Both kinds are enumerated by one of the four maps and neither has a
    governed stored-kind definition in this slice. A record claiming one is
    therefore content no derivation may read: the build refuses the whole
    capture rather than deriving from it or quietly leaving it out.
    """
    assert kind not in stored.SEMANTIC_DOMAINS
    dataset, run, retraction = sample_nodes()
    claimant = Node(id=f"{kind}:claim", kind=kind, title="an ungoverned claim")
    corpus_root = corpus_at(tmp_path / "alpha", ALPHA, (dataset, run, retraction))
    Corpus(corpus_root).add(claimant)
    world = make_world(tmp_path, corpus_root)
    world.admit(corpus_root, provenance=registry.Fresh(), actor="alice")
    bindings = install_bindings(world)

    with pytest.raises(EnumeratedKindUngoverned) as refusal:
        build(world, (ALPHA,), bindings)

    assert kind in str(refusal.value)
    assert claimant.id in str(refusal.value)
    assert not (world.config.world_root / "epochs").exists()


class TestUngovernedKindsAreRefusedNotAssumed:
    def test_the_refusal_precedes_every_derivation(self, monkeypatch, tmp_path):
        # No captured view is ever assembled, so no reducer can have read one:
        # the refusal is raised while the pass is still walking stored records.
        dataset, run, retraction = sample_nodes()
        corpus_root = corpus_at(tmp_path / "alpha", ALPHA, (dataset, run, retraction))
        Corpus(corpus_root).add(Node(id="coreference-attestation:c", kind="coreference-attestation", title="c"))
        world = make_world(tmp_path, corpus_root)
        world.admit(corpus_root, provenance=registry.Fresh(), actor="alice")
        bindings = install_bindings(world)
        monkeypatch.setattr(derive, "Capture", lambda *_a, **_k: pytest.fail("a capture reached derivation"))

        with pytest.raises(EnumeratedKindUngoverned):
            build(world, (ALPHA,), bindings)

        assert lock_for(corpus_root)._holder is None

    def test_absence_of_either_kind_is_an_ordinary_empty_enumeration(self, tmp_path):
        world, bindings, _roots = admitted_world(tmp_path, (ALPHA,))

        draft = build(world, (ALPHA,), bindings)
        inventory = derive.certification_inventory(draft.run("certification-enumeration"))
        coreference = derive.coreference_map(draft.run("coreference-reduction"))

        assert dict(inventory.by_kind) == {}
        assert inventory.coverage == (ALPHA,)
        assert dict(coreference.pairs) == {}
        assert all(record.certification is None for record in draft.capture.corpora[0].records)
        assert all(record.coreference is None for record in draft.capture.corpora[0].records)

    def test_a_governed_enumerated_kind_is_admitted(self, tmp_path):
        assert set(epoch.ENUMERATED_SOURCE_KINDS) & set(stored.SEMANTIC_DOMAINS) == {"retraction", "run"}


# --- Step 6: the pre-publication binding recheck ------------------------------


class TestThePrePublicationRecheck:
    def test_it_reacquires_the_world_lock_and_reads_no_corpus(self, monkeypatch, tmp_path):
        world, bindings, roots = admitted_world(tmp_path, (ALPHA,))
        draft = build(world, (ALPHA,), bindings)
        locked: list[bool] = []
        resolve = rules._locked_resolve_rule_bindings
        monkeypatch.setattr(
            rules,
            "_locked_resolve_rule_bindings",
            lambda world_root, held: (locked.append(world._state.lock.locked()), resolve(world_root, held))[1],
        )
        monkeypatch.setattr(
            registry, "corpus_state_identity", lambda root: pytest.fail("the recheck read a corpus")
        )
        monkeypatch.setattr(epoch, "_captured_records", lambda root: pytest.fail("the recheck read a corpus"))
        generation = lock_for(roots[ALPHA])._capture_generation

        held = epoch._recheck_rule_bindings(world, draft)

        assert locked == [True]
        assert set(held) == set(epoch.DERIVATION_KINDS)
        assert lock_for(roots[ALPHA])._capture_generation == generation

    def test_a_binding_removed_after_capture_refuses(self, tmp_path):
        world, bindings, _roots = admitted_world(tmp_path, (ALPHA,))
        draft = build(world, (ALPHA,), bindings)

        rules.remove_rule_binding(world, bindings["coreference-reduction"])

        with pytest.raises(RuleNotHeld):
            epoch._recheck_rule_bindings(world, draft)

    def test_an_untouched_store_rechecks_the_same_four_pairs(self, tmp_path):
        world, bindings, _roots = admitted_world(tmp_path, (ALPHA,))
        draft = build(world, (ALPHA,), bindings)

        held = epoch._recheck_rule_bindings(world, draft)

        assert {kind: value.binding for kind, value in held.items()} == bindings
        assert draft.bindings == {
            kind: (binding.rule_identity, binding.implementation_identity) for kind, binding in bindings.items()
        }
