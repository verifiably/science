"""Shared cut-3 fixtures: value builders now; Snakefile texts (Task 5) and the
boundary invocation helper (Task 6) are appended by their tasks."""

from decimal import Decimal
from typing import cast

from science.recipe import (
    BoundaryPolicy,
    BoundaryReceipt,
    EnvironmentManifest,
    Invocation,
    Occurrence,
    Recipe,
    RecipeInput,
    ResultManifest,
    RunClosure,
    TraceJob,
)

# Tests build fixture values through the private constructor deliberately —
# the public surface must not offer one, and Task 11 pins that (T1).
from science.report import Entry, LocatorEntry, PublishedObservation, RunAttemptEntry, RunRefusal, _mint_report
from science.spec import (
    RealizedSeeds,
    RuleFixture,
    RuleImplementation,
    Seeded,
    SeedPlan,
    SpecDraft,
    SpecInput,
)

D_IN = "sha256:" + "aa" * 32
D_OUT = "sha256:" + "bb" * 32
DATA_ADDRESS = "dataset:sha256:" + "aa" * 32
READS_ADDRESS = "dataset:sha256:" + "ee" * 32
POLICY = BoundaryPolicy(identity="boundary-policy/minimal-v1", scope_rule="scope-derivation/v1")


def seed_plan(
    streams=("model-initialization",), roots=None, stream_roots=None
) -> SeedPlan:
    roots = roots if roots is not None else {"root-a": 11}
    stream_roots = stream_roots if stream_roots is not None else {s: "root-a" for s in streams}
    return SeedPlan(
        derivation_rule="seed-derivation/v1", streams=streams, roots=roots, stream_roots=stream_roots
    )


def spec_rules() -> dict[str, RuleImplementation]:
    return {
        "median-difference/v1": RuleImplementation(
            identity="impl-interp-1",
            evaluate=lambda manifest: {"outcome": "supported"},
            fixtures=(RuleFixture(arguments=(None,), expected={"outcome": "supported"}),),
        ),
        "content-identity-equality/v1": RuleImplementation(
            identity="impl-eq-1",
            evaluate=lambda a, b: "passed" if a == b else "failed",
            fixtures=(RuleFixture(arguments=(1, 1), expected="passed"),),
        ),
    }


def spec_draft(**overrides) -> SpecDraft:
    fields = {
        "target": "prop-1",
        "estimand": "the effect of x on y",
        "method": "fit the model",
        "assumptions": "iid draws",
        "falsification": "a null effect",
        "input_roles": (SpecInput(role="observes", dataset=DATA_ADDRESS),),
        "applicability": "the sampled population",
        "interpretation_rule": "median-difference/v1",
        "equivalence_rule": "content-identity-equality/v1",
        "parameters": {"alpha": Decimal("0.05")},
        "nondeterminism": Seeded(plan=seed_plan()),
    }
    fields.update(overrides)
    return SpecDraft(**fields)


def seeded() -> Seeded:
    return Seeded(
        plan=SeedPlan(
            derivation_rule="seed-derivation/v1",
            streams=("model-initialization",),
            roots={"root-a": 11},
            stream_roots={"model-initialization": "root-a"},
        )
    )


def invocation(**overrides) -> Invocation:
    fields = {
        "entrypoint": "code/workflow/Snakefile",
        "targets": ("outputs/result.txt",),
        "bindings": ("inputs", "parameters", "nondeterminism"),
        "declared_outputs": ("outputs/result.txt",),
    }
    fields.update(overrides)
    return Invocation(**fields)


def recipe(**overrides) -> Recipe:
    fields = {
        "shape": "assessment",
        "spec_identity": "spec-" + "11" * 8,
        "code_identity": "sha256:" + "cc" * 32,
        "environment": EnvironmentManifest(artifacts=(("python", "sha256:" + "dd" * 32),)),
        "workflow_definition_identity": "sha256:" + "ee" * 32,
        "invocation": invocation(),
        "inputs": (
            RecipeInput(
                role="observes", dataset="dataset:sha256:" + "ff" * 32, content=D_IN
            ),
        ),
        "parameters": {"alpha": Decimal("0.05")},
        "nondeterminism": seeded(),
        "boundary_policy": POLICY,
        "rule_bindings": (
            ("content-identity-equality/v1", "impl-eq-1"),
            ("median-difference/v1", "impl-interp-1"),
        ),
    }
    fields.update(overrides)
    return Recipe(**fields)


def occurrence(**overrides) -> Occurrence:
    fields = {
        "event_token": "tok-1",
        "started_at": "2026-08-12T00:00:00Z",
        "actor": "tester",
        "host_realization": "host-a",
        "trace": (
            TraceJob(
                job_id="0",
                rule="transform",
                wildcards=(),
                inputs=("inputs/data.txt",),
                outputs=("outputs/result.txt",),
            ),
        ),
        "realized_seeds": RealizedSeeds(seeds={"transform": {"model-initialization": 7}}),
        "receipt": BoundaryReceipt(
            scratch_mapping="scratch-mount-a", argv=("snakemake",), rendered_config=()
        ),
    }
    fields.update(overrides)
    return Occurrence(**fields)


def closure(**overrides) -> RunClosure:
    fields = {
        "recipe": recipe(),
        "result": ResultManifest(outputs=(("outputs/result.txt", D_OUT),)),
        "occurrence": occurrence(),
    }
    fields.update(overrides)
    return RunClosure(**fields)


def report(**overrides):
    fields: dict[str, object] = {
        "operation": "acquisition",
        "event_token": "tok-1",
        "actor": "tester",
        "observer": "observer-1",
        "instrument": "instrument-1",
        "opened_at": "2026-08-12T00:00:00Z",
        "closed_at": "2026-08-12T00:05:00Z",
        "entries": (
            LocatorEntry(subject="url://example/data", outcome=PublishedObservation(ref="obs-1")),
            RunAttemptEntry(subject="absent", outcome=RunRefusal(missing_member="spec_identity")),
        ),
    }
    fields.update(overrides)
    return _mint_report(
        operation=cast(str, fields["operation"]),
        event_token=cast(str, fields["event_token"]),
        actor=cast(str, fields["actor"]),
        observer=cast(str, fields["observer"]),
        instrument=cast(str, fields["instrument"]),
        opened_at=cast(str, fields["opened_at"]),
        closed_at=cast(str, fields["closed_at"]),
        entries=cast(tuple[Entry, ...], fields["entries"]),
    )
