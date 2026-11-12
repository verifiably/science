"""Invocation-local accepted session records for kernel authoring.

No epoch is opened. The same captured inventory supplies held dependencies,
merged retractions, calibration evidence and authoring vocabulary snapshots.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from collections.abc import Iterator
from types import MappingProxyType

from nodes.core.node import Node
from beliefs import stored
from beliefs.corpus import ELIGIBLE_RETRACTION_TARGET_KINDS, retraction_standing, run_value
from beliefs.dependencies import FrozenAssessmentDependency
from beliefs.eligibility import AssessmentEligibilityReader, Ineligible
from beliefs.errors import DependencyNotHeld, MalformedRecord, RetractionTargetUnresolvable
from beliefs.proxy_model import proxy_from_stored
from beliefs.world.registry import content_identity
from science import acceptance
from science.config import Mount, ReadContext, _retired
from science.holdings import found_observations
from science.refusal import Refusal, Refused

__all__ = ["SessionRecords", "session_records"]


class SessionRecords:
    def __init__(self, ctx: ReadContext) -> None:
        self.profile = ctx.config.profile
        self._write_root = ctx.config.write_root
        self._mounts = tuple(replace(m, view=m.view.captured()) for m in ctx.session_mounts()
                             if not _retired(ctx.world.status(m.corpus_id)))
        # Policy is decided over the configured mounts; only live session copies
        # below can confer heldness, irrespective of other accepted roots.
        self._policy = acceptance.policy(ctx)
        self._addresses = sorted({n.id for m in self._mounts for n in m.view.iter_stored()})
        self._selected = {}
        facets = {}
        for address in self._addresses:
            mount = self._select(address)
            if mount is None:
                continue
            node = mount.view.get(address)
            if node.kind == "retraction":
                facets[address] = self._retraction(node, mount.profile)
        self._standing = retraction_standing(self, facets)
        self.observations = MappingProxyType(found_observations(
            [(m.corpus_id, m.view) for m in self._mounts], ctx.world))
        self._digests = frozenset(o.digest for address, values in self.observations.items()
                                 if self.holds(address) for o in values)
        self.assessment_eligibility = AssessmentEligibilityReader(
            self, self.profile, self._run_of, self._verifications_of)

    def _select(self, ref: str) -> Mount | None:
        if ref in self._selected:
            return self._selected[ref]
        holders = [m for m in self._mounts if m.view.holds(ref)]
        if len({(m.view.resolve(ref), content_identity(m.view.get(ref))) for m in holders}) > 1:
            raise Refused(Refusal("invalid-input", f"{ref!r} is held by corpora "
                                  f"{', '.join(m.corpus_id for m in holders)}; the copies differ"))
        accepted = [m for m in holders if self._policy.counts(m.corpus_id, m.view.resolve(ref))]
        chosen = min(accepted, key=lambda m: (m.root != self._write_root, m.corpus_id)) if accepted else None
        self._selected[ref] = chosen
        return chosen

    def resolve(self, ref: str) -> str | None:
        """Accepted canonical resolution, before applying the retraction fold."""
        mount = self._select(ref)
        return None if mount is None else mount.view.resolve(ref)

    def holder(self, ref: str) -> Mount:
        mount = self._select(ref)
        if mount is None:
            raise DependencyNotHeld(f"dependency {ref!r} is not held by an accepted live session corpus")
        return mount

    def holds(self, id: str) -> bool:
        canonical = self.resolve(id)
        return canonical is not None and not self.retraction_in_force(canonical)

    def read(self, id: str) -> Node:
        if not self.holds(id):
            raise DependencyNotHeld(f"dependency {id!r} is not held or is retracted")
        return self.holder(id).view.get(id)

    def get(self, ref: str) -> Node:
        return self.read(ref)

    def iter_stored(self) -> Iterator[Node]:
        for address in self._addresses:
            if self.holds(address):
                yield self.read(address)

    def retraction_in_force(self, id: str) -> bool:
        return not self._standing.get(self.resolve(id) or id, True)

    def observation_held(self, digest: str) -> bool:
        return digest in self._digests

    def crosswalks(self, a: str, b: str) -> tuple[str, ...]:
        found = []
        for node in self.iter_stored():
            if node.kind == "proxy-model":
                value = proxy_from_stored(node)
                if value.crosswalk is not None and {value.source.procedure, value.target.scale_of} == {a, b}:
                    found.append(node.id)
        return tuple(sorted(found))

    def assessment_dependency(self, ref: str) -> FrozenAssessmentDependency:
        verdict = self.assessment_eligibility(ref)
        if isinstance(verdict, Ineligible):
            raise DependencyNotHeld(f"calibration basis {ref!r} is ineligible: {verdict.reason}")
        return stored.frozen_assessment_dependency(ref, records=self, profile=self.profile)

    def _run_of(self, id: str):
        ref = stored.typed_ref("run", id)
        node = self.read(ref)
        for role in stored.INPUT_ROLES:
            for target in stored.inputs_of(node, role):
                self.read(target)
        return run_value(self, ref)

    def _verifications_of(self, identity: str):
        selected = []
        for node in self.iter_stored():
            if node.kind != "verification":
                continue
            # Select by real target before decoding unrelated verification facets.
            for relation in node.relations:
                if relation.predicate != stored.VERIFIES or not self.holds(relation.target):
                    continue
                assessment = stored.assessment_value(self.read(relation.target), profile=self.profile)
                if assessment.identity() == identity:
                    value = stored.verification_value(node)
                    if value.assessment == identity:
                        selected.append(value)
                    break
        return tuple(selected)

    def _retraction(self, node: Node, profile):
        violations = profile.document_violations(node)
        if violations:
            raise MalformedRecord(f"{node.id}: invalid retraction document: {violations}")
        facet = node.facets.get(stored.RETRACTION_FACET)
        required = {"target", "reason", "rationale", "grounds", "actor", "event_token"}
        if not isinstance(facet, dict) or set(facet) not in (required, required | {"successor"}):
            raise MalformedRecord(f"{node.id}: malformed retraction facet")
        target = facet["target"]
        if not isinstance(target, dict):
            raise MalformedRecord(f"{node.id}: malformed retraction target")
        arm = target.get("arm")
        fields = {"node": {"arm", "ref", "resolved", "content_identity"},
                  "route": {"arm", "dataset", "resolved", "content_identity", "route_identity"},
                  "snapshot": {"arm", "subject_kind", "subject_identity"}}
        if type(arm) is not str or arm not in fields or set(target) != fields[arm] or not all(type(v) is str and v for v in target.values()):
            raise MalformedRecord(f"{node.id}: malformed retraction target")
        if arm == "node":
            value = stored.NodeTarget(target["ref"], target["resolved"], target["content_identity"])
        elif arm == "route":
            value = stored.RouteTarget(target["dataset"], target["resolved"], target["content_identity"], target["route_identity"])
        else:
            value = stored.SnapshotTarget(target["subject_kind"], target["subject_identity"])
        expected = stored.retraction_node(title=node.title, target=value, **{k: v for k, v in facet.items() if k != "target"})
        if (node.id, node.facets, node.relations) != (expected.id, expected.facets, expected.relations):
            raise MalformedRecord(f"{node.id}: retraction does not match the controlled stored shape")
        if arm != "snapshot":
            ref = target["ref" if arm == "node" else "dataset"]
            resolved = self.resolve(ref)
            if resolved is None or resolved != target["resolved"]:
                raise RetractionTargetUnresolvable(f"{node.id}: retraction target does not resolve exactly")
            held = self.holder(resolved).view.get(resolved)
            if (held.kind not in ELIGIBLE_RETRACTION_TARGET_KINDS if arm == "node" else held.kind != "dataset"):
                raise MalformedRecord(f"{node.id}: ineligible retraction target kind")
            if stored.stored_semantic_hash(held) != target["content_identity"]:
                raise RetractionTargetUnresolvable(f"{node.id}: retraction target content identity differs")
            if arm == "route" and not any(r.get("identity") == target["route_identity"] for r in stored.basis_routes(held)):
                raise RetractionTargetUnresolvable(f"{node.id}: route identity is absent from the stamped basis")
        return facet


@contextmanager
def session_records(ctx: ReadContext) -> Iterator[SessionRecords]:
    # captured ReadViews are immutable in-memory records, not owned sockets or
    # open filesystem handles. The context gives their capture one invocation.
    yield SessionRecords(ctx)
