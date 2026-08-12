"""Replay eligibility, execution, conformance, equivalence, and scope."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import final

from science.adapter import WorkflowDefinition
from science.boundary import RunMinted, RunRefused, execute_assessment_run, execute_production_run
from science.errors import MalformedClosure, MalformedRecord
from science.recipe import ResultManifest, RunClosure
from science.sealed import sealed
from science.spec import (
    SEED_DERIVATION_V1,
    Deterministic,
    FrozenSpec,
    RuleFixture,
    Seeded,
    StochasticUnseeded,
    derive_seed,
)

AVAILABLE = "available"
NOT_AVAILABLE = "not-available"
CONFORMING = "conforming"


@sealed
@final
@dataclass(frozen=True)
class EquivalenceImplementation:
    identity: str
    evaluate: Callable[[ResultManifest, ResultManifest], str]
    fixtures: tuple[RuleFixture, ...]

    def __post_init__(self) -> None:
        try:
            parameters = tuple(inspect.signature(self.evaluate).parameters.values())
        except (TypeError, ValueError) as error:
            raise MalformedRecord("an equivalence evaluator must expose its two-result signature") from error
        positional = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        if len(parameters) != 2 or any(
            parameter.kind not in positional or parameter.default is not inspect.Parameter.empty
            for parameter in parameters
        ):
            raise MalformedRecord("an equivalence evaluator takes exactly the original and replay results")


def _manifest_equality(original: ResultManifest, replayed: ResultManifest) -> str:
    return "passed" if original == replayed else "failed"


CONTENT_EQUALITY = EquivalenceImplementation("impl-eq-1", _manifest_equality, ())
DATASET_CONTENT_EQUALITY = EquivalenceImplementation("impl-dataset-eq-1", _manifest_equality, ())


@sealed
@final
@dataclass(frozen=True)
class CodeLineageCertification:
    rationale: str
    attribution: str

    def __post_init__(self) -> None:
        if any(type(value) is not str or not value for value in (self.rationale, self.attribution)):
            raise MalformedRecord("a code-lineage certification carries a rationale and attribution")


def replay_eligibility(
    run: RunClosure,
    *,
    resolvable_here: frozenset[str],
    attributions: Mapping[str, str],
) -> str:
    recipe = run.recipe
    required = {
        recipe.code_identity,
        recipe.environment.identity(),
        recipe.workflow_definition_identity,
        *(entry.content for entry in recipe.inputs),
    }
    return AVAILABLE if required <= resolvable_here and run.address() in attributions else NOT_AVAILABLE


def replay(
    original: RunMinted,
    *,
    spec: FrozenSpec | None,
    definition: WorkflowDefinition,
    code_roots: tuple[Path, ...],
    held_inputs: Mapping[str, Path],
    entrypoint: str,
    targets: tuple[str, ...],
    declared_outputs: tuple[str, ...],
    actor: str,
    observer: str,
    started_at: str,
    host_realization: str,
    scratch_base: Path,
    cores: int = 1,
) -> RunMinted | RunRefused:
    common = {
        "definition": definition,
        "code_roots": code_roots,
        "held_inputs": held_inputs,
        "entrypoint": entrypoint,
        "targets": targets,
        "declared_outputs": declared_outputs,
        "actor": actor,
        "observer": observer,
        "started_at": started_at,
        "host_realization": host_realization,
        "scratch_base": scratch_base,
        "cores": cores,
    }
    recipe = original.run.recipe
    if recipe.shape == "assessment":
        outcome = execute_assessment_run(spec=spec, **common)
    else:
        outcome = execute_production_run(
            inputs=recipe.inputs,
            parameters=recipe.parameters,
            nondeterminism=recipe.nondeterminism,
            **common,
        )
    if isinstance(outcome, RunRefused):
        return outcome
    if outcome.run.recipe.identity() != recipe.identity():
        error = MalformedClosure("reconstructed recipe differs from the original recipe")
        return RunRefused(str(error), None, outcome.intent, None)
    return outcome


def byte_tolerance_rule(store: Mapping[str, bytes]) -> EquivalenceImplementation:
    tolerance = Decimal("0.000001")

    def evaluate(original: ResultManifest, replayed: ResultManifest) -> str:
        left = dict(original.outputs)
        right = dict(replayed.outputs)
        if left.keys() != right.keys():
            return "failed"
        try:
            for name in left:
                a = Decimal(store[left[name]].decode("utf-8"))
                b = Decimal(store[right[name]].decode("utf-8"))
                if not a.is_finite() or not b.is_finite():
                    return "inconclusive"
                if abs(a - b) > tolerance:
                    return "failed"
        except Exception:  # noqa: BLE001 — any artifact-reader or payload failure is inconclusive
            return "inconclusive"
        return "passed"

    return EquivalenceImplementation(
        identity="impl-tolerance-1e-6",
        evaluate=evaluate,
        fixtures=(),
    )


def conformance(run: RunClosure) -> str:
    contract = run.recipe.nondeterminism
    realized = run.occurrence.realized_seeds.seeds
    if type(contract) is StochasticUnseeded:
        return CONFORMING
    if type(contract) is Deterministic:
        if realized:
            return f"non-conforming: deterministic recipe reported seeds for {min(realized)!r}"
        return CONFORMING

    if type(contract) is not Seeded:
        return "non-conforming: unknown nondeterminism contract"
    plan = contract.plan
    if plan.derivation_rule != SEED_DERIVATION_V1:
        return f"non-conforming: unsupported seed derivation rule {plan.derivation_rule!r}"

    expected = {
        job.rule: {
            stream: derive_seed(plan.roots[plan.stream_roots[stream]], job.rule, stream) for stream in plan.streams
        }
        for job in run.occurrence.trace
    }
    for job in sorted(set(expected) | set(realized)):
        if job not in expected:
            return f"non-conforming: realized seeds name unexecuted job {job!r}"
        if job not in realized:
            return f"non-conforming: missing realized seeds for job {job!r}"
        for stream in sorted(set(expected[job]) | set(realized[job])):
            if stream not in expected[job]:
                return f"non-conforming: job {job!r} names undeclared stream {stream!r}"
            if stream not in realized[job]:
                return f"non-conforming: job {job!r} is missing stream {stream!r}"
            if realized[job][stream] != expected[job][stream]:
                return (
                    f"non-conforming: job {job!r} stream {stream!r} realized "
                    f"{realized[job][stream]}, expected {expected[job][stream]}"
                )
    return CONFORMING


def derive_scope(
    original: RunClosure,
    replayed: RunClosure,
    *,
    certification: CodeLineageCertification | None,
) -> str:
    """Walk only the scope rows this boundary can attest."""
    if conformance(original) != CONFORMING or conformance(replayed) != CONFORMING:
        return "not-certified"
    if original.recipe.identity() == replayed.recipe.identity():
        return "same-environment"
    left = original.recipe
    right = replayed.recipe
    left_observes = {entry.content for entry in left.inputs if entry.role == "observes"}
    right_observes = {entry.content for entry in right.inputs if entry.role == "observes"}
    if (
        left.spec_identity is not None
        and left.spec_identity == right.spec_identity
        and left_observes == right_observes
        and left.code_identity != right.code_identity
        and type(certification) is CodeLineageCertification
    ):
        return "independent-implementation"
    return "not-certified"


derive_scope.__doc__ = """Derive verification scope from two conforming closures.

The `clean-environment` row of §7.3's table needs a receipt attesting
reconstruction and confinement capabilities; no receipt this boundary emits
can attest one, so the row is not spelled here — deferred with the
confinement-capable boundary policy (cut 3 §4.2, R4 row).
"""
