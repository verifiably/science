"""Domain contracts and succession.

M6's arms selected into cut 1 are here. Its deferred arm — *"consulted belief
digests move"* on an additive successor — needs belief, which the slice does not
compute, and is not asserted anywhere below.
"""

import copy

import pytest

from science.contract import domain
from science.errors import MalformedContract, SuccessionViolation


@pytest.fixture()
def parse(base_contract):
    def _parse(document: object, source: str = "<test>") -> domain.DomainContract:
        return domain.parse_domain_contract(document, source=source, base=base_contract)

    return _parse


class TestTheTestingContract:
    def test_it_loads(self, parse, testing_document):
        contract = parse(testing_document)
        assert contract.namespace == "testing"
        assert contract.predecessor is None  # genesis
        assert set(contract.operators) == {"affects", "subtype-of"}

    def test_term_identifiers_are_namespaced(self, parse, testing_document):
        # §7.3: authored, stable, namespaced — and it is what enters π_claim.
        assert parse(testing_document).term("affects") == "testing/affects"

    def test_both_polarity_regimes_are_reachable(self, parse, testing_document):
        operators = parse(testing_document).operators
        assert operators["affects"].sign_apt is True
        assert operators["subtype-of"].sign_apt is False

    def test_restriction_sorts_resolve_through_dimensions_not_operators(self, parse, testing_document):
        # §7.1: so two operators sharing `population` cannot disagree about what
        # a population restriction is bound to.
        contract = parse(testing_document)
        assert contract.dimensions["population"].restriction_sort == "cohort"
        assert not hasattr(contract.operators["affects"], "restriction_sorts")


class TestVocabularyBindings:
    def test_a_namespace_with_a_release_binds(self, parse, testing_document):
        binding = parse(testing_document).sorts["entity"].vocabulary
        assert (binding.namespace, binding.release) == ("EX", "2026-01-01")

    def test_a_held_dataset_binds_by_content_identity(self, parse, testing_document):
        binding = parse(testing_document).sorts["cohort"].vocabulary
        assert binding.dataset_identity == "0" * 64

    def test_a_bare_namespace_is_refused(self, parse, testing_document):
        # D §5, and the case §7.1's own biology example would fail on.
        broken = copy.deepcopy(testing_document)
        broken["sorts"]["entity"]["vocabulary"] = {"namespace": "EX", "release": None}
        with pytest.raises(MalformedContract, match="bare namespace"):
            parse(broken)

    def test_an_empty_dataset_binding_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["sorts"]["entity"]["vocabulary"] = "dataset:"
        with pytest.raises(MalformedContract):
            parse(broken)


class TestOperatorDeclarations:
    def test_arity_must_match_arg_sorts(self, parse, testing_document):
        # ArgSort(op) is a function on Fin(arity(op)); a mismatch leaves a slot
        # with no sort or a sort with no slot.
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["arity"] = 3
        with pytest.raises(MalformedContract, match="arity is 3"):
            parse(broken)

    def test_an_operator_admitting_no_layer_is_refused(self, parse, testing_document):
        # §6.2: it would make Claim uninhabited at that operator.
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["layers"] = []
        with pytest.raises(MalformedContract, match="non-empty"):
            parse(broken)

    def test_a_domain_may_not_mint_a_layer(self, parse, testing_document):
        # §7.1: the layer set is base-owned but per-operator restricted. A domain
        # that could mint one would be redefining what kind of thing a claim is.
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["layers"] = ["teleological"]
        with pytest.raises(MalformedContract, match="may not extend it"):
            parse(broken)

    def test_an_undeclared_arg_sort_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["arg_sorts"] = ["entity", "nowhere"]
        with pytest.raises(MalformedContract, match="not a sort"):
            parse(broken)

    def test_an_undeclared_dimension_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["dimensions"] = ["nowhere"]
        with pytest.raises(MalformedContract, match="not a dimension"):
            parse(broken)

    def test_an_undeclared_restriction_sort_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["dimensions"]["population"]["restriction_sort"] = "nowhere"
        with pytest.raises(MalformedContract, match="not a sort"):
            parse(broken)

    def test_sign_apt_must_be_a_boolean(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["sign_apt"] = "yes"
        with pytest.raises(MalformedContract, match="true or false"):
            parse(broken)

    def test_an_unknown_operator_field_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["polarity"] = "positive"
        with pytest.raises(MalformedContract, match="unknown field"):
            parse(broken)


class TestTheBaseContractIssuesNoOperator:
    def test_a_domain_contract_named_science_is_refused(self, parse, testing_document):
        # §7.1: operators are domain-issued without exception. A base-issued one
        # would sit outside the closure walk every other operator goes through.
        broken = copy.deepcopy(testing_document)
        broken["contract"] = "science"
        with pytest.raises(MalformedContract, match="domain-issued without exception"):
            parse(broken)


class TestSuccession:
    """§8.3's adopted rules, refused at contract load."""

    @pytest.fixture()
    def genesis(self, parse, testing_document):
        return parse(testing_document)

    def successor_of(self, parse, document, predecessor, **edits):
        successor = copy.deepcopy(document)
        successor["lineage"] = {"successor": predecessor.content_identity}
        successor["version"] = predecessor.version + 1
        for path, value in edits.items():
            cursor = successor
            *parents, leaf = path.split(".")
            for step in parents:
                cursor = cursor[step]
            cursor[leaf] = value
        return parse(successor)

    def test_genesis_is_compared_against_nothing(self, genesis):
        domain.check_succession(genesis, None)

    def test_genesis_with_a_predecessor_supplied_is_refused(self, genesis):
        with pytest.raises(SuccessionViolation, match="declares genesis"):
            domain.check_succession(genesis, genesis)

    def test_a_successor_with_no_predecessor_supplied_is_refused(self, parse, testing_document, genesis):
        # Skipping the check would let a redefinition through on the evidence
        # that nobody looked — the corpus's own recurring error, inverted.
        successor = self.successor_of(parse, testing_document, genesis)
        with pytest.raises(SuccessionViolation, match="two-contract check"):
            domain.check_succession(successor, None)

    def test_an_additive_successor_is_accepted(self, parse, testing_document, genesis):
        added = copy.deepcopy(testing_document["operators"])
        added["precedes"] = {
            "arity": 2,
            "arg_sorts": ["entity", "entity"],
            "sign_apt": False,
            "layers": ["structural"],
            "dimensions": [],
        }
        successor = self.successor_of(parse, testing_document, genesis, operators=added)
        domain.check_succession(successor, genesis)

    def test_an_editorial_change_is_accepted_and_moves_contract_identity(self, parse, testing_document, genesis):
        edited = copy.deepcopy(testing_document["operators"])
        edited["affects"]["description"] = "Reworded. Meaning-bearing fields untouched."
        successor = self.successor_of(parse, testing_document, genesis, operators=edited)
        domain.check_succession(successor, genesis)
        assert successor.content_identity != genesis.content_identity

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("arity", 1),
            ("arg_sorts", ["outcome", "entity"]),
            ("sign_apt", False),
            ("layers", ["structural"]),
            ("dimensions", ["population"]),
        ],
    )
    def test_redefining_a_declared_schema_is_refused(self, parse, testing_document, genesis, field, value):
        edited = copy.deepcopy(testing_document["operators"])
        edited["affects"][field] = value
        if field == "arity":
            edited["affects"]["arg_sorts"] = ["entity"]
        successor = self.successor_of(parse, testing_document, genesis, operators=edited)
        with pytest.raises(SuccessionViolation, match="different canonical schema projection"):
            domain.check_succession(successor, genesis)

    def test_retiring_an_identifier_is_permitted(self, parse, testing_document, genesis):
        # `retired` is deliberately outside the canonical schema projection. Were
        # it inside, retiring an identifier would itself be a redefinition —
        # refusing the one operation §7.3a requires to be permitted.
        retired = copy.deepcopy(testing_document["operators"])
        retired["affects"]["retired"] = True
        successor = self.successor_of(parse, testing_document, genesis, operators=retired)
        domain.check_succession(successor, genesis)
        assert successor.operators["affects"].retired is True

    def test_dropping_a_declaration_is_refused(self, parse, testing_document, genesis):
        dropped = copy.deepcopy(testing_document["operators"])
        del dropped["subtype-of"]
        successor = self.successor_of(parse, testing_document, genesis, operators=dropped)
        with pytest.raises(SuccessionViolation, match="drops claim-vocabulary"):
            domain.check_succession(successor, genesis)

    def test_dropping_a_retired_declaration_is_refused(self, parse, testing_document, genesis):
        # A tombstone is what makes a historical claim still typeable.
        retired = copy.deepcopy(testing_document["operators"])
        retired["affects"]["retired"] = True
        tombstoned = self.successor_of(parse, testing_document, genesis, operators=retired)
        dropped = copy.deepcopy(retired)
        del dropped["affects"]
        third = copy.deepcopy(testing_document)
        third["operators"] = dropped
        third["lineage"] = {"successor": tombstoned.content_identity}
        third["version"] = 3
        with pytest.raises(SuccessionViolation, match="drops claim-vocabulary"):
            domain.check_succession(parse(third), tombstoned)

    def test_a_mismatched_predecessor_identity_is_refused(self, parse, testing_document, genesis):
        successor = copy.deepcopy(testing_document)
        successor["lineage"] = {"successor": "f" * 64}
        successor["version"] = 2
        with pytest.raises(SuccessionViolation, match="content identity is"):
            domain.check_succession(parse(successor), genesis)

    def test_succession_covers_sorts_and_dimensions_too(self, parse, testing_document, genesis):
        edited = copy.deepcopy(testing_document["dimensions"])
        edited["population"]["restriction_sort"] = "entity"
        successor = self.successor_of(parse, testing_document, genesis, dimensions=edited)
        with pytest.raises(SuccessionViolation, match="dimension:population"):
            domain.check_succession(successor, genesis)

    def test_the_scope_is_claim_vocabulary_and_nothing_else(self, genesis):
        # §8.3's scope restriction: an unscoped "every identifier" would have
        # this design quietly deciding facet versioning, which D §12 leaves open.
        assert all(key.split(":")[0] in {"sort", "dimension", "operator"} for key in genesis.claim_vocabulary())


class TestParallelGenesis:
    def test_a_second_genesis_in_one_namespace_is_not_prevented(self, parse, testing_document):
        # §8.3 rules this an escape hatch and says so: the rules enforce
        # immutability *within a declared lineage*, not across a namespace.
        # Closing it needs pin-transition validation or a namespace authority —
        # governance, not typing — and ρC1 leaves it open. Asserted here so the
        # hole is visible in the suite rather than only in prose.
        first = parse(testing_document)
        forked = copy.deepcopy(testing_document)
        forked["operators"]["affects"]["arity"] = 1
        forked["operators"]["affects"]["arg_sorts"] = ["entity"]
        second = parse(forked)  # also genesis, same namespace, incompatible schema

        domain.check_succession(first, None)
        domain.check_succession(second, None)
        assert first.namespace == second.namespace
        assert first.claim_vocabulary() != second.claim_vocabulary()
