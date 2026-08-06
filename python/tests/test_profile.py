"""``ProfileSpec`` — compilation of claim schemas.

M7 is here in full. M8's merge-order arm is here in the half that does not need
``I_claim``; the other half — *"and `I_claim` unchanged"* — lands with the
projection, since asserting it before the projection exists would be asserting
nothing.
"""

import copy

import pytest
import yaml

import science.profile as profile_module
from science.contract import base, domain
from science.errors import DuplicateContribution, ProfileError, SuccessionViolation, WithdrawnFromAuthoring
from science.profile import ProfileSpec, compile_profile


@pytest.fixture()
def parse(base_contract):
    def _parse(document, predecessor=None):
        return domain.parse_domain_contract(document, source="<test>", base=base_contract, predecessor=predecessor)

    return _parse


@pytest.fixture()
def testing(parse, testing_document):
    return parse(testing_document)


@pytest.fixture()
def other(parse, testing_document):
    """A second contract, in another namespace, declaring the same local names."""
    document = copy.deepcopy(testing_document)
    document["contract"] = "elsewhere"
    return parse(document)


class TestNoSecondAuthoredOperatorArtifact:
    """M7's first clause.

    The sabotage it names is *"add a hand-authored operator roster beside the
    contracts"*. The test below is what makes that unreachable rather than merely
    absent: if a roster existed anywhere in the package, a profile compiled from
    **no** domain contracts would still have operators in it.
    """

    def test_a_profile_with_no_domains_has_no_operators(self, base_contract):
        profile = compile_profile(base_contract, [])
        assert profile.operators == {}
        assert profile.dimensions == {}
        assert profile.sorts == {}

    def test_the_base_contract_contributes_no_operator(self, base_contract, testing):
        # §7.1: operators are domain-issued without exception.
        profile = compile_profile(base_contract, [testing])
        assert {decl.contract for decl in profile.operators.values()} == {"testing"}
        assert base_contract.name not in {decl.contract for decl in profile.operators.values()}

    def test_every_operator_traces_to_a_supplied_contract(self, base_contract, testing, other):
        profile = compile_profile(base_contract, [testing, other])
        assert set(profile.operators) == {
            "testing/affects",
            "testing/subtype-of",
            "elsewhere/affects",
            "elsewhere/subtype-of",
        }
        for decl in profile.operators.values():
            assert decl.contract in profile.activated_contracts

    def test_compile_profile_is_the_only_exported_route(self):
        builders = [name for name in profile_module.__all__ if name.islower()]
        assert builders == ["compile_profile"]


class TestSemanticEditsRecompileAndEditorialOnesDoNot:
    """M7's second clause, stated as the pair of asymmetries it actually is."""

    def test_an_editorial_edit_moves_contract_identity_and_not_the_compiled_profile(
        self, base_contract, parse, testing_document, testing
    ):
        edited = copy.deepcopy(testing_document)
        edited["operators"]["affects"]["description"] = "Reworded."
        edited["lineage"] = {"successor": testing.content_identity}
        edited["version"] = 2
        successor = parse(edited, predecessor=testing)

        assert successor.content_identity != testing.content_identity
        assert compile_profile(base_contract, [successor]).compiled_identity == (
            compile_profile(base_contract, [testing]).compiled_identity
        )

    def test_a_semantic_schema_edit_moves_the_compiled_profile(self, base_contract, parse, testing_document, testing):
        # Not reachable within a lineage — succession refuses it — so this is a
        # parallel genesis, which §8.3 records as the open escape hatch. The
        # recompilation property is asserted on the only path that can produce it.
        edited = copy.deepcopy(testing_document)
        edited["operators"]["affects"]["sign_apt"] = False
        assert compile_profile(base_contract, [parse(edited)]).compiled_identity != (
            compile_profile(base_contract, [testing]).compiled_identity
        )

    def test_retiring_an_operator_recompiles(self, base_contract, parse, testing_document, testing):
        # Retirement changes what the authoring constructor may offer, so the
        # compiled runtime profile is genuinely different. It is not editorial.
        retired = copy.deepcopy(testing_document)
        retired["operators"]["affects"]["retired"] = True
        retired["lineage"] = {"successor": testing.content_identity}
        retired["version"] = 2
        successor = parse(retired, predecessor=testing)

        assert compile_profile(base_contract, [successor]).compiled_identity != (
            compile_profile(base_contract, [testing]).compiled_identity
        )

    def test_a_base_contract_edit_recompiles(self, base_contract, base_contract_path, testing):
        edited = copy.deepcopy(yaml.safe_load(base_contract_path.read_text(encoding="utf-8")))
        edited["claim_grammar"]["layers"] = [*edited["claim_grammar"]["layers"], "computational"]
        successor = base.parse_base_contract(edited, source="<test>")

        assert compile_profile(successor, [testing]).compiled_identity != (
            compile_profile(base_contract, [testing]).compiled_identity
        )


class TestMergeOrderIsInert:
    """M8's arm, in the half that does not need ``I_claim``.

    **The first two tests below cannot fail, and that is recorded rather than
    hidden.** `science.identity.v1` sorts object keys at encode time, so no
    iteration order inside `compile_profile` can reach the identity — sabotaging
    every sort in the compiler leaves both of them green. They are kept as
    regression guards and are not evidence of anything.

    The third test is the one with force. What *would* make merge order
    significant is a **shape** change — holding the declarations positionally
    instead of keyed by term — so that is what is asserted, and it is the arm
    that goes red when sabotaged.
    """

    def test_the_compiled_profile_is_a_function_of_the_contract_set(self, base_contract, testing, other):
        forward = compile_profile(base_contract, [testing, other])
        reverse = compile_profile(base_contract, [other, testing])
        assert forward.compiled_identity == reverse.compiled_identity
        assert forward.operators == reverse.operators
        assert forward.activated_contracts == reverse.activated_contracts

    def test_the_compiler_contributes_no_input(self, base_contract, testing):
        # No build, version or timestamp is an input to the identity.
        assert compile_profile(base_contract, [testing]).compiled_identity == (
            compile_profile(base_contract, [testing]).compiled_identity
        )

    @pytest.mark.parametrize("section", ["operators", "dimensions", "sorts"])
    def test_declarations_are_keyed_by_term_never_held_positionally(self, base_contract, testing, section):
        # A sequence here would make the merge order an identity input.
        projection = compile_profile(base_contract, [testing]).projection()
        assert isinstance(projection[section], dict)
        assert set(projection[section]) == {f"testing/{local}" for local in _locals(testing, section)}


def _locals(contract, section):
    return getattr(contract, section).keys()


class TestSetsAreSetsAndSlotsAreSlots:
    """§6.2 types `Dims(op)` and `Layers(op)` as **finite sets** and `ArgSort(op)`
    as a function on `Fin(arity(op))`. Holding a set positionally would make
    reordering one line of YAML a redefinition — refused at load, on a change
    that changed nothing.

    Found by a shape test failing for the right reason: `"dimensions":[` turned
    up nested inside every operator.
    """

    @staticmethod
    def _successor(document, predecessor, operators):
        successor = copy.deepcopy(document)
        successor["operators"] = operators
        successor["lineage"] = {"successor": predecessor.content_identity}
        successor["version"] = predecessor.version + 1
        return successor

    @pytest.mark.parametrize("declared_set", ["dimensions", "layers"])
    def test_reordering_a_declared_set_is_not_a_redefinition(
        self, parse, testing_document, base_contract, declared_set
    ):
        genesis = parse(testing_document)
        operators = copy.deepcopy(testing_document["operators"])
        operators["affects"][declared_set] = list(reversed(operators["affects"][declared_set]))
        # Must not raise: succession would otherwise report a redefinition.
        successor = parse(self._successor(testing_document, genesis, operators), predecessor=genesis)
        assert compile_profile(base_contract, [successor]).compiled_identity == (
            compile_profile(base_contract, [genesis]).compiled_identity
        )

    def test_reordering_arg_sorts_is_a_redefinition(self, parse, testing_document):
        # The converse, and the reason the two cannot be canonicalized alike:
        # swapping the slots of `affects` says something different about the world.
        genesis = parse(testing_document)
        operators = copy.deepcopy(testing_document["operators"])
        operators["affects"]["arg_sorts"] = list(reversed(operators["affects"]["arg_sorts"]))
        with pytest.raises(SuccessionViolation, match="different canonical schema projection"):
            parse(self._successor(testing_document, genesis, operators), predecessor=genesis)


class TestResolution:
    """§7.5: ProfileSpec resolves, contracts authorize."""

    def test_local_names_are_resolved_to_term_identifiers(self, base_contract, testing):
        operator = compile_profile(base_contract, [testing]).operator("testing/affects")
        assert operator.arg_sorts == ("testing/entity", "testing/outcome")
        assert operator.dimensions == ("testing/population", "testing/setting")

    def test_a_dimensions_restriction_sort_is_resolved(self, base_contract, testing):
        profile = compile_profile(base_contract, [testing])
        assert profile.dimensions["testing/population"].restriction_sort == "testing/cohort"

    def test_same_local_names_in_different_namespaces_compose(self, base_contract, testing, other):
        # D §8's rule for facets, and the same one here.
        profile = compile_profile(base_contract, [testing, other])
        assert profile.operator("testing/affects").contract == "testing"
        assert profile.operator("elsewhere/affects").contract == "elsewhere"

    def test_two_contracts_in_one_namespace_are_refused(self, base_contract, testing, parse, testing_document):
        twin = parse(copy.deepcopy(testing_document))
        with pytest.raises(DuplicateContribution, match="never last-writer-wins"):
            compile_profile(base_contract, [testing, twin])

    def test_an_absent_operator_refuses_locally(self, base_contract, testing):
        # §7.4 row 4a: local and static, so it refuses here and nothing is minted.
        with pytest.raises(ProfileError, match="no operator"):
            compile_profile(base_contract, [testing]).operator("testing/nowhere")


class TestRetirementIsAnAuthoringProperty:
    """§7.3a: retirement lives in authoring, never in validation."""

    @pytest.fixture()
    def with_retired(self, parse, testing_document, testing):
        retired = copy.deepcopy(testing_document)
        retired["operators"]["affects"]["retired"] = True
        retired["lineage"] = {"successor": testing.content_identity}
        retired["version"] = 2
        return parse(retired, predecessor=testing)

    def test_a_retired_operator_stays_resolvable(self, base_contract, with_retired):
        # decode / import / restore type a historical claim against the frozen
        # retired declaration. Refusing here would corrupt exactly the history
        # retirement exists to preserve.
        profile = compile_profile(base_contract, [with_retired])
        assert profile.operator("testing/affects").retired is True

    def test_a_retired_operator_is_not_offered_for_authoring(self, base_contract, with_retired):
        profile = compile_profile(base_contract, [with_retired])
        assert "testing/affects" not in profile.authorable_operators()
        assert "testing/subtype-of" in profile.authorable_operators()


class TestTheProfileIsCompiledNeverAuthored:
    """M7's first clause has a second half the first pass missed.

    "No second authored operator artifact" is not only about a roster module. A
    `ProfileSpec` a caller can build field-wise, or mutate after the fact, *is* an
    authored profile — and a mutated one carries a `compiled_identity` describing
    a profile that no longer exists, which is `KIND_DESCRIPTORS`' drift with the
    two sources inside one object.
    """

    def test_the_field_wise_constructor_is_refused(self, base_contract, testing):
        compiled = compile_profile(base_contract, [testing])
        with pytest.raises(ProfileError, match="compiled, never authored"):
            ProfileSpec(
                claim_grammar=compiled.claim_grammar,
                operators=dict(compiled.operators),
                dimensions=dict(compiled.dimensions),
                sorts=dict(compiled.sorts),
                base_contract_identity=compiled.base_contract_identity,
                activated_contracts=dict(compiled.activated_contracts),
                compiled_identity=compiled.compiled_identity,
            )

    def test_the_no_argument_constructor_is_refused_too(self):
        # Otherwise the field-wise route is closed and the empty one is not.
        with pytest.raises(ProfileError, match="compiled, never authored"):
            ProfileSpec()

    @pytest.mark.parametrize("section", ["operators", "dimensions", "sorts"])
    def test_the_mappings_are_read_only(self, base_contract, testing, other, section):
        profile = compile_profile(base_contract, [testing])
        mapping = getattr(profile, section)
        with pytest.raises(TypeError):
            mapping["forged"] = next(iter(getattr(compile_profile(base_contract, [other]), section).values()))
        with pytest.raises(TypeError):
            del mapping[next(iter(mapping))]

    def test_activated_contracts_is_read_only(self, base_contract, testing):
        with pytest.raises(TypeError):
            compile_profile(base_contract, [testing]).activated_contracts["forged"] = "f" * 64

    def test_the_fields_are_frozen(self, base_contract, testing):
        profile = compile_profile(base_contract, [testing])
        with pytest.raises(AttributeError):
            profile.compiled_identity = "forged"  # type: ignore[misc]


class TestActivationIsNotConsultation:
    """D6's conditional arm, guarded at the shape rather than in prose.

    The first pass carried one `contract_identities` mapping with the base
    contract folded in. Anything computing a digest from its values would have
    moved a belief because an unrelated domain was switched on — D6's negative
    arm, committed by the accessor rather than by the walk.
    """

    def test_the_unconditional_and_the_conditional_are_separate_fields(self, base_contract, testing, other):
        profile = compile_profile(base_contract, [testing, other])
        assert profile.base_contract_identity == base_contract.content_identity
        assert profile.activated_contracts == {
            "testing": testing.content_identity,
            "elsewhere": other.content_identity,
        }

    def test_the_base_contract_is_not_among_the_activated(self, base_contract, testing):
        # Folding it in is what makes "take every value" look reasonable.
        profile = compile_profile(base_contract, [testing])
        assert base_contract.name not in profile.activated_contracts
        assert profile.base_contract_identity not in set(profile.activated_contracts.values())

    def test_the_base_contract_identity_survives_an_empty_profile(self, base_contract):
        # D §8: membership is unconditional, so no walk may be able to omit it.
        profile = compile_profile(base_contract, [])
        assert profile.base_contract_identity == base_contract.content_identity
        assert profile.activated_contracts == {}

    def test_no_member_offers_a_consulted_set(self, base_contract, testing):
        # Belief is outside cut 1. A member named for the consulted set would be
        # a placeholder that computes the activated one, which is the collapse.
        profile = compile_profile(base_contract, [testing])
        assert not [name for name in dir(profile) if "consult" in name.lower()]

    def test_the_compiled_identity_is_not_a_contract_identity(self, base_contract, testing):
        profile = compile_profile(base_contract, [testing])
        assert profile.compiled_identity != profile.base_contract_identity
        assert profile.compiled_identity not in set(profile.activated_contracts.values())


class TestRetirementReachesThroughSorts:
    """§7.3a's authoring boundary, applied to every route into it.

    Checking only the operator's own `retired` flag leaves an operator offered
    whose slots cannot be filled — the refusal then lands when the author tries
    to bind a referent, one step past the boundary §7.3a draws.
    """

    @pytest.fixture()
    def retire(self, parse, testing_document, base_contract):
        def _retire(section, name):
            genesis = parse(testing_document)
            document = copy.deepcopy(testing_document)
            document[section][name]["retired"] = True
            document["lineage"] = {"successor": genesis.content_identity}
            document["version"] = 2
            return compile_profile(base_contract, [parse(document, predecessor=genesis)])

        return _retire

    def test_retiring_an_argument_sort_withdraws_the_operator(self, retire):
        profile = retire("sorts", "outcome")  # affects : entity x outcome
        assert "testing/affects" not in profile.authorable_operators()
        assert "testing/subtype-of" in profile.authorable_operators()  # entity x entity

    def test_the_withdrawn_operator_stays_resolvable_for_decode(self, retire):
        # Historical claims are typed against the frozen declaration; refusing
        # here would corrupt the history retirement exists to preserve.
        profile = retire("sorts", "outcome")
        assert profile.operator("testing/affects").retired is False

    def test_retiring_the_operator_itself_still_withdraws_it(self, retire):
        assert "testing/affects" not in retire("operators", "affects").authorable_operators()

    def test_a_withdrawn_operator_offers_no_dimensions_at_all(self, retire):
        # Not an empty tuple: `subtype-of` legitimately returns one, so an empty
        # answer here would make "withdrawn" and "permits none" the same fact.
        for section, name, reason in [
            ("operators", "affects", "the operator is retired"),
            ("sorts", "outcome", "argument sorts"),
        ]:
            profile = retire(section, name)
            with pytest.raises(WithdrawnFromAuthoring, match=reason):
                profile.authorable_dimensions("testing/affects")

    def test_an_unresolvable_operator_is_not_a_withdrawn_one(self, base_contract, testing):
        # Two different facts, and the profile must not answer one with the other.
        profile = compile_profile(base_contract, [testing])
        with pytest.raises(ProfileError, match="no operator"):
            profile.authorable_dimensions("testing/absent")

    def test_retiring_a_permitted_dimension_withdraws_only_that_dimension(self, retire):
        # §6.2: Dims(op) is the set of dimensions *permitted*, not required, so
        # the operator remains authorable without it.
        profile = retire("dimensions", "setting")
        assert "testing/affects" in profile.authorable_operators()
        assert profile.authorable_dimensions("testing/affects") == ("testing/population",)

    def test_retiring_a_restriction_sort_withdraws_its_dimension(self, retire):
        # A restriction is sorted exactly as an argument is, so a retired
        # restriction sort leaves nothing selectable on that dimension.
        profile = retire("sorts", "cohort")  # population : restriction_sort cohort
        assert profile.authorable_dimensions("testing/affects") == ("testing/setting",)

    def test_nothing_is_withdrawn_when_nothing_is_retired(self, base_contract, testing):
        profile = compile_profile(base_contract, [testing])
        assert set(profile.authorable_operators()) == {"testing/affects", "testing/subtype-of"}
        assert profile.authorable_dimensions("testing/affects") == ("testing/population", "testing/setting")
        assert profile.authorable_dimensions("testing/subtype-of") == ()
