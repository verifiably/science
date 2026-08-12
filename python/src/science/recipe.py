"""Recipe, occurrence, result, and run-closure values."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import final

from science.errors import MalformedClosure, UnsafeInvocation
from science.identity import v1
from science.sealed import sealed
from science.spec import (
    Deterministic,
    ExclusionCertification,
    FrozenSpec,
    RealizedSeeds,
    Seeded,
    StochasticUnseeded,
)

__all__ = [
    "ASSESSMENT_ROLES",
    "ENVIRONMENT_DOMAIN",
    "PRODUCTION_ROLES",
    "RECIPE_DOMAIN",
    "RUN_DOMAIN",
    "SHAPES",
    "BoundaryPolicy",
    "BoundaryReceipt",
    "EnvironmentManifest",
    "ExclusionCertification",
    "Invocation",
    "Occurrence",
    "Recipe",
    "RecipeInput",
    "ResultManifest",
    "RunClosure",
    "TraceJob",
    "project_recipe",
]

RECIPE_DOMAIN = "science.recipe.v1"
RUN_DOMAIN = "science.run.v1"
ENVIRONMENT_DOMAIN = "science.environment.v1"

SHAPES = ("assessment", "dataset-production")
ASSESSMENT_ROLES = ("observes", "reads")
PRODUCTION_ROLES = ("transforms", "reads")


def _require_component(value: str, where: str) -> None:
    if value in ("", "unknown", "attested"):
        raise MalformedClosure(f"{where} must carry a held component identity, not {value!r}")


def _freeze_parameter_value(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_parameter_value(member) for key, member in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_parameter_value(member) for member in value)
    return value


def _project_parameter_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _project_parameter_value(member) for key, member in value.items()}
    if isinstance(value, tuple):
        return [_project_parameter_value(member) for member in value]
    return value


def _require_tuple(value: object, where: str) -> None:
    if not isinstance(value, tuple):
        raise MalformedClosure(f"{where} must be a tuple")


def _pairs(rows: tuple[tuple[str, str], ...]) -> list[list[str]]:
    return [list(row) for row in sorted(rows)]


@sealed
@final
@dataclass(frozen=True)
class RecipeInput:
    role: str
    dataset: str
    content: str
    exclusion: ExclusionCertification | None = None

    def __post_init__(self) -> None:
        _require_component(self.content, "input content")
        if self.exclusion is not None and self.role != "reads":
            raise MalformedClosure("an exclusion certification is carried by a `reads` input only")


@sealed
@final
@dataclass(frozen=True)
class Invocation:
    entrypoint: str
    targets: tuple[str, ...]
    bindings: tuple[str, ...]
    declared_outputs: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, values in (
            ("targets", self.targets),
            ("bindings", self.bindings),
            ("declared_outputs", self.declared_outputs),
        ):
            _require_tuple(values, f"invocation {name}")
        if any(target.startswith("-") for target in self.targets):
            raise UnsafeInvocation("an option-like target is not a workflow target")
        for output in self.declared_outputs:
            depth = 0
            if PurePosixPath(output).is_absolute():
                raise UnsafeInvocation(f"declared output {output!r} is absolute")
            for segment in output.split("/"):
                if segment == "..":
                    depth -= 1
                elif segment not in ("", "."):
                    depth += 1
                if depth < 0:
                    raise UnsafeInvocation(f"declared output {output!r} escapes the run root")
        if len(set(self.declared_outputs)) != len(self.declared_outputs):
            raise MalformedClosure("duplicate logical names in declared outputs")


@sealed
@final
@dataclass(frozen=True)
class EnvironmentManifest:
    artifacts: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _require_tuple(self.artifacts, "environment artifacts")
        if not all(
            isinstance(row, tuple)
            and len(row) == 2
            and all(isinstance(member, str) for member in row)
            for row in self.artifacts
        ):
            raise MalformedClosure("environment artifacts are (name, content identity) pairs")

    def identity(self) -> str:
        return v1.digest(ENVIRONMENT_DOMAIN, {"artifacts": _pairs(self.artifacts)})


@sealed
@final
@dataclass(frozen=True)
class BoundaryPolicy:
    identity: str
    scope_rule: str
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_tuple(self.capabilities, "boundary policy capabilities")


@sealed
@final
@dataclass(frozen=True)
class Recipe:
    shape: str
    spec_identity: str | None
    code_identity: str
    environment: EnvironmentManifest
    workflow_definition_identity: str
    invocation: Invocation
    inputs: tuple[RecipeInput, ...]
    parameters: Mapping[str, object]
    nondeterminism: Deterministic | Seeded | StochasticUnseeded
    boundary_policy: BoundaryPolicy
    rule_bindings: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if self.shape not in SHAPES:
            raise MalformedClosure(f"recipe shape {self.shape!r} is outside {SHAPES}")
        if self.shape == "assessment" and self.spec_identity is None:
            raise MalformedClosure("an assessment recipe carries its frozen spec identity")
        if self.shape == "dataset-production" and self.spec_identity is not None:
            raise MalformedClosure("a dataset-production recipe has no assessment spec identity")
        if not isinstance(self.environment, EnvironmentManifest):
            raise MalformedClosure("environment must be an EnvironmentManifest, not a lockfile digest")
        if not isinstance(self.invocation, Invocation):
            raise MalformedClosure("invocation must be an Invocation")
        if not isinstance(self.boundary_policy, BoundaryPolicy):
            raise MalformedClosure("boundary_policy must be a BoundaryPolicy")
        _require_tuple(self.inputs, "recipe inputs")
        _require_tuple(self.rule_bindings, "recipe rule bindings")
        if not all(isinstance(entry, RecipeInput) for entry in self.inputs):
            raise MalformedClosure("recipe inputs hold RecipeInput values only")
        roles = ASSESSMENT_ROLES if self.shape == "assessment" else PRODUCTION_ROLES
        if any(entry.role not in roles for entry in self.inputs):
            raise MalformedClosure(f"an input role is outside the {self.shape} partition {roles}")
        if not isinstance(self.parameters, Mapping):
            raise MalformedClosure("recipe parameters must be a mapping")
        if not isinstance(self.nondeterminism, (Deterministic, Seeded, StochasticUnseeded)):
            raise MalformedClosure("recipe nondeterminism must be a frozen spec variant")
        if not all(
            isinstance(row, tuple)
            and len(row) == 2
            and all(isinstance(member, str) for member in row)
            for row in self.rule_bindings
        ):
            raise MalformedClosure("rule bindings are (rule, implementation) pairs")
        _require_component(self.code_identity, "code identity")
        _require_component(self.workflow_definition_identity, "workflow definition identity")
        object.__setattr__(
            self,
            "parameters",
            MappingProxyType(
                {key: _freeze_parameter_value(value) for key, value in self.parameters.items()}
            ),
        )

    def _projection(self) -> dict[str, object]:
        inputs = []
        for entry in sorted(
            self.inputs,
            key=lambda value: (
                value.role,
                value.dataset,
                value.content,
                value.exclusion.rationale if value.exclusion else "",
                value.exclusion.attribution if value.exclusion else "",
            ),
        ):
            row: dict[str, object] = {
                "role": entry.role,
                "dataset": entry.dataset,
                "content": entry.content,
            }
            if entry.exclusion is not None:
                row["exclusion"] = {
                    "rationale": entry.exclusion.rationale,
                    "attribution": entry.exclusion.attribution,
                }
            inputs.append(row)
        projection: dict[str, object] = {
            "shape": self.shape,
            "code_identity": self.code_identity,
            "environment": self.environment.identity(),
            "workflow_definition_identity": self.workflow_definition_identity,
            "invocation": {
                "entrypoint": self.invocation.entrypoint,
                "targets": list(self.invocation.targets),
                "bindings": list(self.invocation.bindings),
                "declared_outputs": list(self.invocation.declared_outputs),
            },
            "inputs": inputs,
            "parameters": _project_parameter_value(self.parameters),
            "nondeterminism": self.nondeterminism.projection(),
            "boundary_policy": {
                "identity": self.boundary_policy.identity,
                "scope_rule": self.boundary_policy.scope_rule,
                "capabilities": sorted(self.boundary_policy.capabilities),
            },
            "rule_bindings": _pairs(self.rule_bindings),
        }
        if self.spec_identity is not None:
            projection["spec_identity"] = self.spec_identity
        # Scheduling options have no recipe member: they cannot become a second
        # parameter channel or alter the recorded closure.
        return projection

    def identity(self) -> str:
        return v1.digest(RECIPE_DOMAIN, self._projection())


def project_recipe(
    spec: FrozenSpec,
    *,
    held: Mapping[str, str],
    code_identity: str,
    environment: EnvironmentManifest,
    workflow_definition_identity: str,
    invocation: Invocation,
    boundary_policy: BoundaryPolicy,
) -> Recipe:
    if not isinstance(spec, FrozenSpec):
        raise MalformedClosure("project_recipe requires a FrozenSpec")
    try:
        inputs = tuple(
            RecipeInput(
                role=entry.role,
                dataset=entry.dataset,
                content=held[entry.dataset],
                exclusion=entry.exclusion,
            )
            for entry in spec.input_roles
        )
    except KeyError as error:
        raise MalformedClosure(f"declared input {error.args[0]!r} is not held") from error
    return Recipe(
        shape="assessment",
        spec_identity=spec.identity,
        code_identity=code_identity,
        environment=environment,
        workflow_definition_identity=workflow_definition_identity,
        invocation=invocation,
        inputs=inputs,
        parameters=spec.parameters,
        nondeterminism=spec.nondeterminism,
        boundary_policy=boundary_policy,
        rule_bindings=spec.rule_bindings,
    )


@sealed
@final
@dataclass(frozen=True)
class ResultManifest:
    outputs: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _require_tuple(self.outputs, "result outputs")
        if not all(
            isinstance(row, tuple)
            and len(row) == 2
            and all(isinstance(member, str) for member in row)
            for row in self.outputs
        ):
            raise MalformedClosure("result outputs are (logical name, content identity) pairs")
        names = [name for name, _ in self.outputs]
        if len(set(names)) != len(names):
            raise MalformedClosure("duplicate logical names in result manifest")


@sealed
@final
@dataclass(frozen=True)
class TraceJob:
    job_id: str
    rule: str
    wildcards: tuple[tuple[str, str], ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, values in (
            ("wildcards", self.wildcards),
            ("inputs", self.inputs),
            ("outputs", self.outputs),
        ):
            _require_tuple(values, f"trace job {name}")


@sealed
@final
@dataclass(frozen=True)
class BoundaryReceipt:
    scratch_mapping: str
    argv: tuple[str, ...]
    rendered_config: tuple[tuple[str, str], ...]
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, values in (
            ("argv", self.argv),
            ("rendered_config", self.rendered_config),
            ("capabilities", self.capabilities),
        ):
            _require_tuple(values, f"boundary receipt {name}")


@sealed
@final
@dataclass(frozen=True)
class Occurrence:
    event_token: str
    started_at: str
    actor: str
    host_realization: str
    trace: tuple[TraceJob, ...]
    realized_seeds: RealizedSeeds
    receipt: BoundaryReceipt

    def __post_init__(self) -> None:
        _require_tuple(self.trace, "occurrence trace")
        if not all(isinstance(job, TraceJob) for job in self.trace):
            raise MalformedClosure("occurrence trace holds TraceJob values only")


def _trace_projection(job: TraceJob) -> dict[str, object]:
    return {
        "job_id": job.job_id,
        "rule": job.rule,
        "wildcards": _pairs(job.wildcards),
        "inputs": list(job.inputs),
        "outputs": list(job.outputs),
    }


def _occurrence_projection(occurrence: Occurrence) -> dict[str, object]:
    return {
        "event_token": occurrence.event_token,
        "started_at": occurrence.started_at,
        "actor": occurrence.actor,
        "host_realization": occurrence.host_realization,
        "trace": [_trace_projection(job) for job in occurrence.trace],
        "realized_seeds": occurrence.realized_seeds.projection(),
        "receipt": {
            "scratch_mapping": occurrence.receipt.scratch_mapping,
            "argv": list(occurrence.receipt.argv),
            "rendered_config": _pairs(occurrence.receipt.rendered_config),
            "capabilities": sorted(occurrence.receipt.capabilities),
        },
    }


@sealed
@final
@dataclass(frozen=True)
class RunClosure:
    recipe: Recipe
    result: ResultManifest
    occurrence: Occurrence

    def __post_init__(self) -> None:
        declared = set(self.recipe.invocation.declared_outputs)
        supplied = {name for name, _ in self.result.outputs}
        if declared - supplied:
            raise MalformedClosure(f"missing declared output: {sorted(declared - supplied)}")
        if supplied - declared:
            raise MalformedClosure(f"undeclared entry: {sorted(supplied - declared)}")

    def address(self) -> str:
        return v1.digest(
            RUN_DOMAIN,
            {
                "recipe": self.recipe._projection(),
                "result": _pairs(self.result.outputs),
                "occurrence": _occurrence_projection(self.occurrence),
            },
        )
