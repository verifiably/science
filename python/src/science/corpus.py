"""The write API and the read side — the one module that holds a mutable corpus.

**S8's capability boundary is what this module's shape is for.** A `Corpus`
structurally satisfies any read-only `Protocol` despite carrying mutation
methods, so a protocol is not a capability boundary. What is one is a concrete
facade: `ReadView` holds its `Corpus` privately and exposes exactly the read
surface — `get`, one-hop `outbound`/`inbound`, and member iteration. Every module
outside this one receives a `ReadView`, and no mutable `Corpus` is constructed or
received anywhere else. That claim is checkable by AST, which is the point: a
roster of trusted writers has a hole by construction, and a new writer reaching
the filesystem through an unrecognized primitive is simply never discovered.

**Stale-hash validation lives on the facade's node-read path.** Every fetch —
`get`, and every node a traversal resolves — recomputes the semantic hash from
the stored fields and refuses a disagreement. Iteration is deliberately *not* a
fetch: the corpus check reads through it and must **report** what it finds
rather than raise, and a check that could not survive reaching a stale node
would report nothing about the corpus beyond it.

**A live `Corpus` indexes at construction, so a raw filesystem write is
invisible to it.** Every fixture that writes bytes behind the API reconstructs a
fresh facade before asserting read behaviour — reconstruction from disk is the
recovery posture the seam names, and it is the read this slice actually runs.

**Traversal is corpus-local throughout.** A walk truncates at the corpus edge;
reaching a target the holding corpus does not carry is the world index's, which
this slice does not build.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import final

from nodes.core.corpus import Corpus
from nodes.core.errors import CollisionError
from nodes.core.errors import ValidationError as NodesValidationError
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.structural_index import ResolvedEdge
from nodes.core.write_plan import WritePlanExecutor
from pydantic import ValidationError as PydanticValidationError

from science import stored
from science.dataset import dataset_address
from science.errors import (
    BasisMissing,
    CollisionRefused,
    EligibilityUnmet,
    FamilyKindUnsupported,
    IdentityError,
    RecordAlreadyMinted,
    ScienceError,
    SemanticHashMissing,
    SemanticHashStale,
    SupersedeIdentityUnchanged,
    SupersedeTargetMissing,
    ValidationRefused,
)
from science.lineage import Basis, LineageSnapshot, Producer, Route
from science.record import RunInput, RunValue
from science.sealed import sealed
from science.traversal import LineageEntry, Reach, RelationEntry, Step, closure

__all__ = [
    "DIRECTIONS",
    "CorpusWriter",
    "Finding",
    "LineageAdjacency",
    "ReadView",
    "RelationAdjacency",
    "corpus_check",
    "derived_from",
    "lineage_snapshot",
    "run_value",
]

DIRECTIONS = ("inbound", "outbound")


@sealed
@final
@dataclass(frozen=True)
class Finding:
    """`nodes`' finding envelope, under a Science-owned code namespace.

    The envelope is reused and the codes are not: `nodes`' seven structural
    codes cannot express a cross-node predicate, and a kind invariant surfaces
    there as `invariant-violated` with an empty detail. `message` is
    human-facing and normative for nothing — never used for ordering, never
    compared for parity.
    """

    severity: str
    code: str
    ref: str
    detail: str
    message: str

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return (self.ref, self.code, self.detail)


class ReadView:
    """The read-only facade. Concrete, not a protocol — see the module docstring."""

    def __init__(self, corpus: Corpus) -> None:
        self._corpus = corpus

    @classmethod
    def opened_at(cls, root: Path) -> ReadView:
        """Open a corpus root for reading alone. The mutable handle this builds
        never leaves the facade, which is what makes a read-only opener safe to
        hand to any module."""
        return cls(Corpus(Path(root)))

    # --- resolution ---------------------------------------------------------

    def resolve(self, ref: str) -> str | None:
        """The live id a ref names — through a deprecated id as `nodes`
        resolves one — or `None` when the corpus holds no such node."""
        uid = self._corpus.index.resolve_uid(ref)
        return None if uid is None else self._corpus.index.by_uid[uid].id

    def holds(self, ref: str) -> bool:
        return self.resolve(ref) is not None

    # --- fetching -----------------------------------------------------------

    def get(self, ref: str) -> Node:
        """Fetch one node, refusing a stale semantic hash (`semantic-hash-stale`)
        and an unstamped governed kind (`semantic-hash-missing`).

        The stale refusal is S3's read-side check; the missing refusal is the
        2026-08-18 review's strengthening — a governed kind is minted stamped
        without exception, so omission is statically detectable. What neither
        can see is an edit that moved the fields **and** the stamp together:
        the store compares a state against itself and has no record of what
        preceded it — substrate §4.3's bound, inherited here rather than
        papered over.
        """
        return self._validated(self._corpus.get(ref))

    def outbound(self, ref: str) -> list[ResolvedEdge]:
        return self._corpus.outbound(ref)

    def inbound(self, ref: str) -> list[ResolvedEdge]:
        return self._corpus.inbound(ref)

    def iter_stored(self) -> Iterator[Node]:
        """Every stored node, **unvalidated**. The corpus check's read: a
        reporting check that raised at the first stale node would report one
        finding and hide every other."""
        yield from self._corpus.all()

    def live_id(self, uid: str) -> str:
        return self._corpus.index.by_uid[uid].id

    @staticmethod
    def _validated(node: Node) -> Node:
        if stored.semantic_hash_missing(node):
            raise SemanticHashMissing(
                f"{node.id}: a {node.kind!r} carries no semantic-identity stamp "
                "(semantic-hash-missing); the boundary mints every governed record stamped, "
                "so an unstamped one is a raw write that skipped even self-stamping"
            )
        if stored.semantic_hash_disagrees(node):
            raise SemanticHashStale(
                f"{node.id}: the stored semantic hash disagrees with the fields it covers "
                "(semantic-hash-stale); the node is an untrusted import, not a guaranteed mutation"
            )
        return node


@dataclass
class _RootState:
    lock: threading.Lock
    corpus: Corpus
    view: ReadView
    executor_factory: Callable[[Path], WritePlanExecutor]


_ROOT_STATES: dict[str, _RootState] = {}
_ROOT_STATES_LOCK = threading.Lock()


def _root_state_for(root: Path, executor_factory: Callable[[Path], WritePlanExecutor]) -> _RootState:
    resolved = Path(root).resolve()
    key = str(resolved)
    with _ROOT_STATES_LOCK:
        state = _ROOT_STATES.get(key)
        if state is None:
            corpus = Corpus(resolved, executor_factory=executor_factory)
            state = _RootState(threading.Lock(), corpus, ReadView(corpus), executor_factory)
            _ROOT_STATES[key] = state
        elif state.executor_factory is not executor_factory:
            raise ScienceError(f"corpus root {key!r} is already open with a different executor factory")
        return state


# --- the two adjacency adapters ---------------------------------------------


class RelationAdjacency:
    """Stored relations under one predicate, in one direction.

    `directed` is **not reinterpreted**: an undirected relation is reached from
    its stored source and not from its stored target, exactly as it is stored.
    Reading it both ways would invent an edge the author did not write, and the
    fixture that pins this is why the flag is read at all.
    """

    def __init__(self, view: ReadView, predicate: str, direction: str) -> None:
        if direction not in DIRECTIONS:
            raise ValueError(f"direction {direction!r} is outside {DIRECTIONS}")
        self._view = view
        self._predicate = predicate
        self._direction = direction

    def steps(self, ref: str) -> tuple[Step, ...]:
        if self._direction == "outbound":
            return self._outbound(ref)
        return self._inbound(ref)

    def _outbound(self, ref: str) -> tuple[Step, ...]:
        node = self._view.get(ref)
        steps: list[Step] = []
        for position, relation in enumerate(node.relations):
            if relation.predicate != self._predicate or relation.source != node.id:
                continue
            steps.append(
                Step(
                    stored=relation.target,
                    resolved=self._view.resolve(relation.target),
                    entry=RelationEntry(
                        source=node.id,
                        position=position,
                        predicate=relation.predicate,
                        target=relation.target,
                    ),
                )
            )
        return tuple(steps)

    def _inbound(self, ref: str) -> tuple[Step, ...]:
        steps: list[Step] = []
        for edge in self._view.inbound(ref):
            if edge.relation.predicate != self._predicate or edge.source_uid is None:
                continue
            source_id = self._view.live_id(edge.source_uid)
            source = self._view.get(source_id)
            position = next(
                (index for index, relation in enumerate(source.relations) if relation == edge.relation),
                0,
            )
            steps.append(
                Step(
                    stored=source_id,
                    resolved=source_id,
                    entry=RelationEntry(
                        source=source_id,
                        position=position,
                        predicate=edge.relation.predicate,
                        target=edge.relation.target,
                    ),
                )
            )
        return tuple(steps)


class LineageAdjacency:
    """The stamped lineage basis, walked as a facet.

    **No predicate and no direction argument**, and that is a claim rather than
    an omission: a lineage step has neither, so a relation adapter's clauses are
    category errors here. What it can express that the relation adapter cannot
    is the difference between an unresolvable **ancestor** and an unresolvable
    **producing run** — the route's two positions, both resolution-checked,
    only one of them an edge of the closure.
    """

    def __init__(self, view: ReadView) -> None:
        self._view = view

    def steps(self, ref: str) -> tuple[Step, ...]:
        node = self._view.get(ref)
        steps: list[Step] = []
        for index, route in enumerate(stored.basis_routes(node)):
            run = route.get("run")
            if isinstance(run, str):
                steps.append(
                    Step(
                        stored=run,
                        resolved=self._view.resolve(run),
                        entry=LineageEntry(dataset=node.id, route=index, position="run", target=run),
                        # Checked, never followed: a producing run is not an
                        # ancestor, and walking into it would put runs in a
                        # dataset closure.
                        follow=False,
                    )
                )
            ancestor = route.get("ancestor")
            if isinstance(ancestor, str):
                steps.append(
                    Step(
                        stored=ancestor,
                        resolved=self._view.resolve(ancestor),
                        entry=LineageEntry(dataset=node.id, route=index, position="ancestor", target=ancestor),
                    )
                )
        return tuple(steps)


# --- the walks the arms run over ---------------------------------------------


def derived_from(view: ReadView, dataset: str) -> Reach:
    """`derived_from` as a **view** over `produces ∘ transforms`, walked out of
    the store — stored nowhere, and no API accepts an authored ancestry list.

    One step: the runs whose `produces` edge names this dataset, and what each
    of those runs `transforms`. Independence does not read this view — it walks
    the stamped basis — and the two are allowed to disagree, which is the
    disagreement R23's fixture constructs.
    """
    return closure(dataset, _DerivedFromAdjacency(view))


class _DerivedFromAdjacency:
    def __init__(self, view: ReadView) -> None:
        self._view = view

    def steps(self, ref: str) -> tuple[Step, ...]:
        steps: list[Step] = []
        for producer in RelationAdjacency(self._view, stored.PRODUCES, "inbound").steps(ref):
            if producer.resolved is None:
                continue
            steps.extend(RelationAdjacency(self._view, stored.TRANSFORMS, "outbound").steps(producer.resolved))
        return tuple(steps)


def run_value(view: ReadView, ref: str) -> RunValue:
    """A stored run as cut 2's value: its spec, and its role-partitioned inputs
    with each input dataset's declaration read from the dataset itself.

    **Corpus-local**: an input naming a dataset this corpus does not hold is not
    in the value, because its declaration lives wherever that dataset does and
    resolving an address to the corpus holding it is the world index's job. A
    walk truncating at the corpus edge is this layer's documented property.
    """
    node = view.get(ref)
    inputs = tuple(
        RunInput(role=role, dataset=stored.dataset_declaration(view.get(target)))
        for role in stored.INPUT_ROLES
        for target in stored.inputs_of(node, role)
        if view.holds(target)
    )
    return RunValue(ref=ref, spec=stored.run_spec(node) or "", inputs=inputs)


def lineage_snapshot(view: ReadView, roots: Sequence[str]) -> LineageSnapshot:
    """Produce substrate §5's snapshot from a store, corpus-locally.

    The inspected set is `{observed root} ∪ closure` — the union written out,
    because the walk is start-excluding and a root whose own immediate parent is
    gone must still be inspected. Nothing here decides anything: `certify` reads
    the tags, the resolutions and the producer sets this assembles.
    """
    adjacency = LineageAdjacency(view)
    inspected: list[str] = []
    for root in roots:
        for dataset in (root, *closure(root, adjacency).reached):
            if dataset not in inspected:
                inspected.append(dataset)

    bases: dict[str, Basis] = {}
    producers: dict[str, tuple[Producer, ...]] = {}
    for dataset in inspected:
        if not view.holds(dataset):
            continue
        node = view.get(dataset)
        routes = tuple(
            Route(
                dataset=dataset,
                stored_run=str(route.get("run", "")),
                resolved_run=view.resolve(str(route.get("run", ""))),
                stored_ancestor=str(route.get("ancestor", "")),
                resolved_ancestor=view.resolve(str(route.get("ancestor", ""))),
                transforms=tuple(str(entry) for entry in route.get("transforms", []) or ()),
            )
            for route in stored.basis_routes(node)
        )
        facet = stored.lineage_basis(node)
        if facet is not None and routes:
            bases[dataset] = Basis(tag=str(facet.get("tag", "single")), routes=routes)
        producers[dataset] = tuple(_producers_of(view, dataset))
    return LineageSnapshot(roots=tuple(roots), bases=bases, producers=producers)


def _producers_of(view: ReadView, dataset: str) -> list[Producer]:
    """The runs holding a `produces` edge to `dataset`, with what each of them
    `transforms`. The producer set is the divergence test's input; the basis
    route is what it is compared against, and the two are separate reads on
    purpose — a build that derived one from the other could not disagree."""
    producers: list[Producer] = []
    for edge in view.inbound(dataset):
        if edge.relation.predicate != stored.PRODUCES:
            continue
        run_ref = edge.relation.source
        resolved = view.resolve(run_ref)
        transforms = () if resolved is None else stored.inputs_of(view.get(resolved), stored.TRANSFORMS)
        producers.append(Producer(stored_run=run_ref, resolved_run=resolved, transforms=transforms))
    return producers


# --- the §6.2 corpus check ---------------------------------------------------


def eligibility_refusal(view: ReadView, node: Node) -> str | None:
    """S7's cross-node predicate, in one implementation for both boundaries.

    assessment → run → `observes` → dataset → facet. `reads` inputs never
    confer eligibility, in any quantity, and no clause of this reaches the
    registry compile: the kinds are the kernel's and the facet is the `science`
    base profile's own.

    Returns the reason the `assesses` edge is inadmissible, or `None`.
    """
    if not any(relation.predicate == stored.ASSESSES for relation in node.relations):
        return None
    facet = node.facets.get(stored.ASSESSMENT_FACET)
    run_ref = facet.get("run") if isinstance(facet, dict) else None
    if not isinstance(run_ref, str) or not run_ref:
        return "the assessment names no run"
    if not view.holds(run_ref):
        return f"the run {run_ref!r} resolves to no node in this corpus"
    run = view.get(run_ref)
    observed = stored.inputs_of(run, stored.OBSERVES)
    if not observed:
        return f"the run {run_ref!r} has no observes input; reads inputs never confer eligibility"
    for dataset_ref in observed:
        if view.holds(dataset_ref) and stored.is_empirical_observation(view.get(dataset_ref)):
            return None
    return f"no observes input of {run_ref!r} carries the empirical-observation facet"


def corpus_check(view: ReadView) -> tuple[Finding, ...]:
    """The profile-level check (substrate §6.2 item 2), reported and never raised.

    Files are canonical and hand-editable, so a node can reach the store without
    passing the write boundary. What this reports is what such a node can be
    caught by: a stale stamp, a governed kind with no stamp at all, and an
    `assesses` edge whose run does not support it. What it is silent on is a
    raw write that is **self-consistent** — the hash agrees because the writer
    computed it, and nothing structural is wrong because nothing is. That
    silence is §4.2.1's stated bound, not a gap here.
    """
    findings: list[Finding] = []
    for node in view.iter_stored():
        if stored.semantic_hash_missing(node):
            findings.append(
                Finding(
                    severity="error",
                    code="semantic-hash-missing",
                    ref=node.id,
                    detail="unstamped",
                    message=f"{node.id}: a {node.kind!r} carries no semantic-identity stamp",
                )
            )
        try:
            if stored.semantic_hash_disagrees(node):
                findings.append(
                    Finding(
                        severity="error",
                        code="semantic-hash-stale",
                        ref=node.id,
                        detail="mismatch",
                        message=f"{node.id}: the stored semantic hash disagrees with the fields it covers",
                    )
                )
        except IdentityError as refused:
            findings.append(
                Finding(
                    severity="error",
                    code="semantic-hash-stale",
                    ref=node.id,
                    detail="unencodable",
                    message=f"{node.id}: the covered fields do not encode, so no hash can be recomputed: {refused}",
                )
            )
        reason = eligibility_refusal(view, node)
        if reason is not None:
            for relation in node.relations:
                if relation.predicate == stored.ASSESSES:
                    findings.append(
                        Finding(
                            severity="error",
                            code="eligibility-unmet",
                            ref=node.id,
                            detail=relation.target,
                            message=f"{node.id}: assesses {relation.target!r} but {reason}",
                        )
                    )
    return tuple(sorted(findings, key=lambda finding: finding.sort_key))


class CorpusWriter:
    """The write API — the sole constructor and holder of a mutable `Corpus`.

    Its public surface in this slice is **add alone**. What this package decides
    — basis, eligibility, collisions, the add-only guard — refuses in Science's
    vocabulary as a `WriteRefused`; what the executor layer decides — plan
    validity, engine refusal, halt — crosses the boundary as the seam's
    `PlanRefusedError` and `ExecutionError`. A third vocabulary wrapping those
    two would add a layer with no added discrimination.

    **Every add is serialized end to end under a per-root operation lock** —
    read, refuse, plan, execute. The refusals read corpus state before the
    engine lease exists, and only some of those reads are safe under concurrency:
    the **monotone** predicates (W3, S7) cannot be invalidated by another
    admitted add, because nothing removes a basis or an `observes` edge, but the
    **collision** predicates can — two planners can each pass `assert_addable`
    for one uid under different ids, plan creates at two different paths, and
    both no-clobber effects succeed. `CreateFileNoClobber` backstops only the
    same-path race. So the ruling is a single-planner restriction: in-process it
    is this lock, and cross-process it is a **stated deployment obligation**
    whose violation is detected loudly rather than prevented — strict
    construction refuses the duplicate uid with `CollisionError`.

    Deletion-capable family adapters must re-own this question; neither argument
    transfers to them.
    """

    def __init__(self, root: Path, executor_factory: Callable[[Path], WritePlanExecutor]) -> None:
        self._state = _root_state_for(root, executor_factory)
        self._operation = self._state.lock

    @property
    def _corpus(self) -> Corpus:
        return self._state.corpus

    @property
    def _view(self) -> ReadView:
        return self._state.view

    @property
    def read_view(self) -> ReadView:
        """The facade every other module receives. The mutable handle stays
        here."""
        return self._view

    def add(self, node: Node) -> Node:
        """Mint one record, returning it as `nodes` mints it.

        A write against an unregistered root surfaces as the executor's
        `ExecutionError(index=None, applied=0)` with the engine's registration
        refusal as cause — init is an explicit act, not a fallback this
        performs.
        """
        with self._operation:
            self._refuse(node)
            return self._corpus.add(node)

    def supersede(self, successor: Node, *, of: str) -> Node:
        """Mint a proposition successor without touching its predecessor."""
        with self._operation:
            predecessor_id = self._view.resolve(of)
            if predecessor_id is None:
                raise SupersedeTargetMissing(f"{of!r}: predecessor does not resolve locally")
            predecessor = self._view.get(predecessor_id)
            if predecessor.kind != "proposition" or successor.kind != "proposition":
                raise FamilyKindUnsupported("supersede operates on propositions only")
            self._refuse_already_minted(successor)
            self._refuse_malformed_supersede_successor(successor)
            if any(relation.predicate == stored.SUPERSEDES for relation in successor.relations):
                raise ValidationRefused(f"{successor.id}: supersedes relations are authored by the adapter")
            try:
                successor_identity = stored.recompute_semantic_hash(successor)
            except IdentityError as caught:
                raise ValidationRefused(f"{successor.id}: refused by document validation: {caught}") from caught
            if successor_identity == stored.recompute_semantic_hash(predecessor):
                raise SupersedeIdentityUnchanged(
                    f"{successor.id}: successor semantic identity is unchanged; use revise instead"
                )
            candidate = successor.model_copy(
                update={
                    "relations": [
                        *successor.relations,
                        Relation(source=successor.id, predicate=stored.SUPERSEDES, target=predecessor_id),
                    ]
                }
            )
            self._refuse(candidate)
            return self._corpus.add(candidate)

    # --- the refusals, in order ---------------------------------------------

    def _refuse_malformed_supersede_successor(self, successor: Node) -> None:
        if not all(isinstance(relation, Relation) for relation in successor.relations):
            raise ValidationRefused(f"{successor.id}: refused by document validation: malformed relation")
        self._refuse_invalid(successor)

    def _refuse(self, node: Node) -> None:
        self._refuse_already_minted(node)
        self._refuse_missing_basis(node)
        self._refuse_ineligible(node)
        if stored.display_facet_malformed(node):
            raise ValidationRefused(f"{node.id}: refused by document validation: malformed display facet")
        self._refuse_invalid(node)
        self._refuse_collision(node)

    def _refuse_already_minted(self, node: Node) -> None:
        """The add-only guard, **before plan construction**: an existing
        `(uid, id)` pair is the pair `nodes`' own `add` would answer with a
        `ReplaceOp`, so refusing here is what keeps every plan this surface
        emits a create. The edit surface is the family adapters'."""
        existing = self._corpus.index.by_uid.get(node.uid)
        if existing is not None and existing.id == node.id:
            raise RecordAlreadyMinted(
                f"{node.id} is already minted under uid {node.uid}; an edit is a new mint, never a rewrite"
            )

    def _refuse_missing_basis(self, node: Node) -> None:
        """W3 as narrowed, over the record being minted and nothing else."""
        if node.kind == "source" and not stored.external_identifiers(node):
            raise BasisMissing(
                f"{node.id}: a source carries an accepted external identifier "
                f"({', '.join(stored.ACCEPTED_EXTERNAL_IDENTIFIERS)}); a curation note is its own explicit add, "
                "and no title-and-year fallback exists"
            )
        if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) is None:
            raise BasisMissing(
                f"{node.id}: a dataset carries a content identity — every declared resource pinned by an "
                "accepted digest. Supplying it later is a second, separate mint"
            )

    def _refuse_ineligible(self, node: Node) -> None:
        """S7's write boundary, reading the cross-node predicate through this
        corpus's own read view."""
        reason = eligibility_refusal(self._view, node)
        if reason is not None:
            raise EligibilityUnmet(f"{node.id}: the assesses edge is inadmissible because {reason}")

    @staticmethod
    def _refuse_invalid(node: Node) -> None:
        """`nodes`' document validation, wrapped so no `nodes` exception escapes
        raw. The registry half is unexercised here: no kind registry is compiled
        in this slice, and G5's kind-existence check waits with it."""
        try:
            Node.model_validate(node.model_dump())
        except (NodesValidationError, PydanticValidationError) as caught:
            raise ValidationRefused(f"{node.id}: refused by document validation: {caught}") from caught

    def _refuse_collision(self, node: Node) -> None:
        try:
            self._corpus.index.assert_addable(node)
        except CollisionError as caught:
            raise CollisionRefused(str(caught)) from caught
