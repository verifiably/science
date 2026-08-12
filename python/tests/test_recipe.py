"""R1, R2's member-mutation arms and value-level negative, R14 at run and
closure positions, R17's value halves, M2, and R21's value-level manifest
refusals. R2's trace and job-ID components are deferred to the full workflow
surface (cut 3 §7.3 item 1)."""

import dataclasses
import inspect
from decimal import Decimal

import pytest
from fixtures_cut3 import (
    D_IN,
    D_OUT,
    DATA_ADDRESS,
    POLICY,
    READS_ADDRESS,
    closure,
    invocation,
    occurrence,
    recipe,
    spec_draft,
    spec_rules,
)

from science.errors import (
    BinaryFloatRefused,
    KeyCollision,
    MalformedClosure,
    NonFiniteDecimal,
    NullRefused,
    UnsafeInvocation,
)
from science.identity import v1
from science.recipe import (
    BoundaryPolicy,
    EnvironmentManifest,
    Invocation,
    RecipeInput,
    ResultManifest,
    project_recipe,
)
from science.record import AssessmentValue, SourceAssertion
from science.spec import Deterministic, ExclusionCertification, RealizedSeeds, SpecInput, freeze


# --- R1 ----------------------------------------------------------------------
def test_r1_an_incomplete_closure_is_refused_and_no_run_value_exists():
    # A declared output the result lacks: refusal, not a weaker run (§2).
    with pytest.raises(MalformedClosure):
        closure(result=ResultManifest(outputs=()))


def test_r1_the_note_is_a_separate_act_and_the_member_is_then_supplied():
    # Mirroring W3: the source-assertion is its own explicit authored act (cut
    # 2's typed constructor); only the supplied member mints the run value.
    note = SourceAssertion(
        ref="s1",
        relation="asserts",
        proposition="prop-1",
        payload={"quote": "environment reconstructed by hand"},
    )
    assert note.relation == "asserts"
    run = closure()  # every member present — the run value exists
    assert len(run.address()) == 64  # a bare v1 digest


def test_r1_no_unknown_or_attested_component_is_representable():
    for field in ("code_identity", "workflow_definition_identity"):
        for value in ("unknown", "attested", ""):
            with pytest.raises(MalformedClosure):
                recipe(**{field: value})
    with pytest.raises(MalformedClosure):
        recipe(inputs=(RecipeInput(role="observes", dataset="dataset:x", content="unknown"),))


def test_r1_a_bare_lockfile_digest_is_refused_as_environment_identity():
    with pytest.raises(MalformedClosure):
        recipe(environment="sha256:" + "99" * 32)


# --- R2 ----------------------------------------------------------------------
RECIPE_MUTATIONS = [
    (
        "shape",
        lambda: recipe(
            shape="dataset-production",
            spec_identity=None,
            inputs=(RecipeInput(role="transforms", dataset="dataset:x", content=D_IN),),
        ),
    ),
    ("spec_identity", lambda: recipe(spec_identity="spec-" + "22" * 8)),
    ("code_identity", lambda: recipe(code_identity="sha256:" + "ab" * 32)),
    (
        "environment",
        lambda: recipe(
            environment=EnvironmentManifest(
                artifacts=(("python", "sha256:" + "ba" * 32),)
            )
        ),
    ),
    (
        "workflow_definition_identity",
        lambda: recipe(workflow_definition_identity="sha256:" + "cd" * 32),
    ),
    (
        "invocation",
        lambda: recipe(
            invocation=invocation(targets=("outputs/other.txt",))
        ),
    ),
    (
        "inputs_content",
        lambda: recipe(
            inputs=(
                RecipeInput(
                    role="observes", dataset="dataset:x", content="sha256:" + "12" * 32
                ),
            )
        ),
    ),
    (
        "inputs_exclusion",
        lambda: recipe(
            inputs=(
                RecipeInput(role="observes", dataset="dataset:x", content=D_IN),
                RecipeInput(
                    role="reads",
                    dataset="dataset:y",
                    content="sha256:" + "34" * 32,
                    exclusion=ExclusionCertification(
                        rationale="reference table", attribution="tester"
                    ),
                ),
            )
        ),
    ),
    ("parameters", lambda: recipe(parameters={"alpha": Decimal("0.5")})),
    ("nondeterminism", lambda: recipe(nondeterminism=Deterministic())),
    (
        "boundary_policy",
        lambda: recipe(
            boundary_policy=BoundaryPolicy(
                identity="boundary-policy/other-v1", scope_rule="scope-derivation/v1"
            )
        ),
    ),
    (
        "rule_bindings",
        lambda: recipe(rule_bindings=(("content-identity-equality/v1", "impl-eq-2"),)),
    ),
]


@pytest.mark.parametrize("name,mutate", RECIPE_MUTATIONS, ids=[n for n, _ in RECIPE_MUTATIONS])
def test_r2_every_recipe_member_moves_the_run_address(name, mutate):
    mutated_recipe = mutate()
    assert mutated_recipe.identity() != recipe().identity()
    mutated = closure(recipe=mutated_recipe)
    assert mutated.address() != closure().address()


def test_r2_the_result_and_each_occurrence_member_move_the_address():
    baseline = closure().address()
    assert (
        closure(
            result=ResultManifest(outputs=(("outputs/result.txt", "sha256:" + "56" * 32),))
        ).address()
        != baseline
    )
    for field, value in [
        ("event_token", "tok-2"),
        ("started_at", "2026-08-12T01:00:00Z"),
        ("actor", "other"),
        ("host_realization", "host-b"),
    ]:
        assert closure(occurrence=occurrence(**{field: value})).address() != baseline
    assert (
        closure(
            occurrence=occurrence(
                realized_seeds=RealizedSeeds(
                    seeds={"transform": {"model-initialization": 8}}
                )
            )
        ).address()
        != baseline
    )
    assert closure(occurrence=occurrence(trace=())).address() != baseline


def test_r2_equal_recipes_despite_differing_seeds_and_event_tokens():
    # The retained negative (cut 3 §7.3 item 1): seeds and tokens are
    # occurrence members; the recipe holds nothing post-execution.
    a = closure()
    b = closure(
        occurrence=occurrence(
            event_token="tok-2",
            realized_seeds=RealizedSeeds(
                seeds={"transform": {"model-initialization": 99}}
            ),
        )
    )
    assert a.recipe.identity() == b.recipe.identity()
    assert a.address() != b.address()


def test_recipe_keeps_nested_parameters_immutable_after_construction():
    parameters = {"nested": {"values": ["before"]}}
    value = recipe(parameters=parameters)
    parameters["nested"]["values"].append("after")
    assert value.parameters == {"nested": {"values": ("before",)}}


# --- R14 at run and closure positions ----------------------------------------
def test_r14_binary_floats_are_refused_at_every_run_position():
    with pytest.raises(BinaryFloatRefused):
        recipe(parameters={"alpha": 0.05}).identity()
    with pytest.raises(BinaryFloatRefused):
        recipe(parameters={"nested": {"deep": [0.1 + 0.2]}}).identity()


def test_r14_the_four_collisions_walked_at_the_recipe_position():
    assert recipe(parameters={"x": Decimal("0.5")}).identity() != recipe(
        parameters={"x": "0.5"}
    ).identity()
    with pytest.raises(NullRefused):
        recipe(parameters={"x": None}).identity()
    assert recipe(parameters={"x": 1}).identity() != recipe(
        parameters={"x": Decimal("1.0")}
    ).identity()
    assert recipe(parameters={"x": Decimal("1.00")}).identity() == recipe(
        parameters={"x": Decimal("1.0")}
    ).identity()
    with pytest.raises(KeyCollision):
        recipe(parameters={"é": 1, "é": 2}).identity()


def test_r14_nan_and_infinity_are_refused_in_every_position():
    for bad in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")):
        with pytest.raises(NonFiniteDecimal):
            recipe(parameters={"x": bad}).identity()
        with pytest.raises(NonFiniteDecimal):
            recipe(parameters={"deep": [{"y": bad}]}).identity()


def test_r14_kind_domains_separate_and_v2_never_equals_v1():
    payload = {"same": "bytes"}
    assert v1.digest("science.recipe.v1", payload) != v1.digest("science.run.v1", payload)
    assert v1.digest("science.recipe.v1", payload) != v1.digest("science.recipe.v2", payload)


# --- R17's value halves -------------------------------------------------------
def test_r17_projection_offers_no_caller_path_for_the_projected_members():
    params = inspect.signature(project_recipe).parameters
    assert list(params) == [
        "spec",
        "held",
        "code_identity",
        "environment",
        "workflow_definition_identity",
        "invocation",
        "boundary_policy",
    ]
    assert not {"inputs", "parameters", "nondeterminism"} & set(params)


def test_r17_the_projected_recipe_carries_the_spec_whole():
    spec = freeze(spec_draft(), held_rules=spec_rules())
    projected = project_recipe(
        spec,
        held={DATA_ADDRESS: D_IN},
        code_identity="sha256:" + "cc" * 32,
        environment=EnvironmentManifest(artifacts=(("python", "sha256:" + "dd" * 32),)),
        workflow_definition_identity="sha256:" + "ee" * 32,
        invocation=invocation(),
        boundary_policy=POLICY,
    )
    assert projected.spec_identity == spec.identity
    assert projected.nondeterminism == spec.nondeterminism
    assert dict(projected.parameters) == dict(spec.parameters)
    assert projected.rule_bindings == spec.rule_bindings
    certified = freeze(
        spec_draft(
            input_roles=(
                SpecInput(role="observes", dataset=DATA_ADDRESS),
                SpecInput(
                    role="reads",
                    dataset=READS_ADDRESS,
                    exclusion=ExclusionCertification(
                        rationale="palette", attribution="tester"
                    ),
                ),
            )
        ),
        held_rules=spec_rules(),
    )
    reprojected = project_recipe(
        certified,
        held={DATA_ADDRESS: D_IN, READS_ADDRESS: "sha256:" + "34" * 32},
        code_identity="sha256:" + "cc" * 32,
        environment=EnvironmentManifest(artifacts=(("python", "sha256:" + "dd" * 32),)),
        workflow_definition_identity="sha256:" + "ee" * 32,
        invocation=invocation(),
        boundary_policy=POLICY,
    )
    assert reprojected.inputs[1].exclusion == certified.input_roles[1].exclusion


def test_r17_invocation_holds_bindings_not_values():
    assert {f.name for f in dataclasses.fields(Invocation)} == {
        "entrypoint",
        "targets",
        "bindings",
        "declared_outputs",
    }
    with pytest.raises(UnsafeInvocation):
        invocation(targets=("--config",))


# --- M2 ----------------------------------------------------------------------
def test_m2_substituting_any_input_moves_the_assessment_identity_every_time():
    inputs = (
        RecipeInput(role="observes", dataset="dataset:x", content=D_IN),
        RecipeInput(role="reads", dataset="dataset:y", content="sha256:" + "34" * 32),
    )
    base = closure(recipe=recipe(inputs=inputs))
    for position in range(len(inputs)):
        substituted = list(inputs)
        substituted[position] = RecipeInput(
            role=inputs[position].role,
            dataset="dataset:z",
            content="sha256:" + "78" * 32,
        )
        other = closure(recipe=recipe(inputs=tuple(substituted)))
        original = AssessmentValue(
            spec="s",
            run=base.address(),
            proposition="p",
            outcome="supported",
            interpretation_rule="r",
        )
        moved = AssessmentValue(
            spec="s",
            run=other.address(),
            proposition="p",
            outcome="supported",
            interpretation_rule="r",
        )
        assert original.identity() != moved.identity()


def test_m2_an_input_no_declared_role_partition_covers_is_refused_not_ignored():
    with pytest.raises(MalformedClosure):
        recipe(inputs=(RecipeInput(role="transforms", dataset="dataset:x", content=D_IN),))
    with pytest.raises(MalformedClosure):
        recipe(
            shape="dataset-production",
            spec_identity=None,
            inputs=(RecipeInput(role="observes", dataset="dataset:x", content=D_IN),),
        )


# --- R21's value-level manifest refusals (the boundary arms are Task 6's) -----
def test_r21_an_undeclared_manifest_entry_mints_no_run():
    with pytest.raises(MalformedClosure):
        closure(
            result=ResultManifest(
                outputs=(("outputs/result.txt", D_OUT), ("outputs/extra.txt", D_IN))
            )
        )


def test_r21_absolute_and_root_escaping_output_declarations_are_refused():
    with pytest.raises(UnsafeInvocation):
        invocation(declared_outputs=("/etc/passwd",))
    with pytest.raises(UnsafeInvocation):
        invocation(declared_outputs=("../outside.txt",))
    with pytest.raises(UnsafeInvocation):
        invocation(declared_outputs=("outputs/../../outside.txt",))


def test_r21_a_duplicate_logical_name_is_refused():
    with pytest.raises(MalformedClosure):
        ResultManifest(outputs=(("a", D_OUT), ("a", D_IN)))
    with pytest.raises(MalformedClosure):
        invocation(declared_outputs=("outputs/a.txt", "outputs/a.txt"))
