"""``ProfileSpec`` — the sole compiled runtime profile.

D §6 closed substrate §12 by **retiring** the second per-kind source of truth
rather than picking a winner between two. One normative source — the `science`
base contract together with the activated domain contracts — and every runtime
artifact compiled from it:

    base contract  ─┐   (normative SSOT)
                    ├─▶  ProfileSpec  ─┬─▶  KindSpec set  (D4, deferred)
    domain contracts┘   (compiled)     └─▶  claim schemas (M7, here)

Only the claim-schema half is built. `KindSpec` compilation is **D4**, fully
deferred from cut 1, and an operator roster is not a per-kind artifact — an
operator belongs to no kind, which is why D §6 had to be widened rather than
merely read (M7).

**`ProfileSpec` resolves; contracts authorize** (§7.5). The two roles must not
blur, and the sharp consequence is that **`ProfileSpec`'s own identity never
appears in `π_claim` or in the consulted set**. If a compiled artifact were an
identity authority, recompiling — a different merge order, a different compiler —
could move claim identity with no contract edit anywhere, which is
`KIND_DESCRIPTORS`' defect one level up. What enters `belief_input_digest` is the
set of **contract** identities (D6), never the compiled artifact's.

``compiled_identity`` exists for a narrower job: it is what M7 means by
*"semantic-schema edits recompile, description edits do not."* It is derived from
the merged **schema projections** alone, so an editorial edit moves the contract
identity and leaves this one still. It is not an input to any claim.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from science.contract.base import BaseContract, ClaimGrammar
from science.contract.domain import DomainContract, OperatorDecl, VocabularyBinding
from science.errors import DuplicateContribution, ProfileError
from science.identity import v1

__all__ = ["CompiledDimension", "CompiledOperator", "CompiledSort", "ProfileSpec", "compile_profile"]

PROFILE_DOMAIN = "science.profile.v1"


@dataclass(frozen=True)
class CompiledSort:
    term: str
    vocabulary: VocabularyBinding
    retired: bool
    contract: str

    def schema_projection(self) -> dict[str, object]:
        return {"vocabulary": self.vocabulary.projection(), "retired": self.retired}


@dataclass(frozen=True)
class CompiledDimension:
    term: str
    restriction_sort: str
    retired: bool
    contract: str

    def schema_projection(self) -> dict[str, object]:
        return {"restriction_sort": self.restriction_sort, "retired": self.retired}


@dataclass(frozen=True)
class CompiledOperator:
    """A declaration with every local name resolved to a term identifier.

    Resolution is the compiled artifact's whole job. `arg_sorts` and `dimensions`
    are written locally in a contract and are namespaced here, because a claim's
    projection carries **term identifiers** (§6.5) and a local name is not one.
    """

    term: str
    arity: int
    arg_sorts: tuple[str, ...]
    sign_apt: bool
    layers: tuple[str, ...]
    dimensions: tuple[str, ...]
    retired: bool
    contract: str

    def schema_projection(self) -> dict[str, object]:
        # Sets are sorted, slots are not — see `OperatorDecl.schema_projection`.
        return {
            "arity": self.arity,
            "arg_sorts": list(self.arg_sorts),
            "sign_apt": self.sign_apt,
            "layers": sorted(self.layers),
            "dimensions": sorted(self.dimensions),
            "retired": self.retired,
        }


@dataclass(frozen=True)
class ProfileSpec:
    claim_grammar: ClaimGrammar
    operators: Mapping[str, CompiledOperator]
    dimensions: Mapping[str, CompiledDimension]
    sorts: Mapping[str, CompiledSort]
    contract_identities: Mapping[str, str]
    """Namespace → content identity, base contract included.

    D §8 makes the base contract's membership **unconditional**: a derivation
    reading no base-profile facet at all still consults it, because a base
    contract can reinterpret a kernel kind or a relation signature. Belief is
    outside cut 1, so nothing here computes a digest — this is the set such a
    computation would read, carried so that it is not reconstructed later from a
    walk that could under-collect (D limitation 2 warns such a walk fails *open*).
    """
    compiled_identity: str

    def projection(self) -> dict[str, object]:
        """The canonical projection ``compiled_identity`` is taken over.

        Exposed because the property that merge order is inert is **not**
        enforced here: `science.identity.v1` sorts object keys at encode time, so
        any insertion order already yields the same bytes. What would break it is
        a shape change — carrying the operators as a **sequence** rather than a
        map keyed by term — and that is what a test can check.
        """
        return _projection(self.claim_grammar, self.operators, self.dimensions, self.sorts)

    def operator(self, term: str) -> CompiledOperator:
        """Resolve an operator term identifier, or refuse.

        §7.4 row 4a: a claim naming an operator whose declaring contract is not
        in the profile is a **local, static** failure, so it refuses here and
        nothing is minted. That is a different failure from 4b's cross-corpus
        conflict, which is only visible when a derivation assembles a closure.
        """
        try:
            return self.operators[term]
        except KeyError:
            raise ProfileError(
                f"no operator {term!r} in this profile. Operators are domain-issued (§7.1); "
                f"activated namespaces are {sorted(self.contract_identities)}."
            ) from None

    def authorable_operators(self) -> tuple[str, ...]:
        """The operators the typed **authoring** constructor may offer.

        §7.3a: retirement lives in authoring, not in validation. A retired
        identifier is still resolvable — decode, import and restore type a
        historical claim against the frozen retired declaration — and refusing it
        at decode would corrupt exactly the history retirement exists to
        preserve.
        """
        return tuple(sorted(term for term, decl in self.operators.items() if not decl.retired))


def compile_profile(base: BaseContract, domains: Iterable[DomainContract]) -> ProfileSpec:
    """Merge the base contract and the activated domain contracts.

    Merging happens **upstream** of any registration, which is why D §6 could
    report a zero `nodes` delta: `Registry` never sees two contributors for one
    kind because the compiled product is already one fully-composed spec.
    """
    activated = list(domains)

    seen: dict[str, DomainContract] = {}
    for contract in activated:
        if contract.namespace in seen:
            raise DuplicateContribution(
                f"two contracts contribute to namespace {contract.namespace!r}. Contributions in different "
                "namespaces compose; two to one namespace are refused at compile, never last-writer-wins."
            )
        seen[contract.namespace] = contract

    sorts: dict[str, CompiledSort] = {}
    dimensions: dict[str, CompiledDimension] = {}
    operators: dict[str, CompiledOperator] = {}

    # Sorted for a reproducible construction order, which helps a reader diffing
    # two profiles. It is **not** what makes merge order inert: identity.v1 sorts
    # object keys at encode time, so this loop's order cannot reach the identity
    # either way. Recorded because the opposite is easy to assume — and was
    # assumed here first, until sabotaging the sort left the suite green.
    for namespace in sorted(seen):
        contract = seen[namespace]
        for name, decl in contract.sorts.items():
            sorts[contract.term(name)] = CompiledSort(
                term=contract.term(name), vocabulary=decl.vocabulary, retired=decl.retired, contract=namespace
            )
        for name, dimension in contract.dimensions.items():
            dimensions[contract.term(name)] = CompiledDimension(
                term=contract.term(name),
                restriction_sort=contract.term(dimension.restriction_sort),
                retired=dimension.retired,
                contract=namespace,
            )
        for name, operator in contract.operators.items():
            operators[contract.term(name)] = _compile_operator(contract, operator)

    contract_identities = {base.name: base.content_identity, **{ns: c.content_identity for ns, c in seen.items()}}

    return ProfileSpec(
        claim_grammar=base.claim_grammar,
        operators=operators,
        dimensions=dimensions,
        sorts=sorts,
        contract_identities=contract_identities,
        compiled_identity=v1.digest(PROFILE_DOMAIN, _projection(base.claim_grammar, operators, dimensions, sorts)),
    )


def _projection(
    claim_grammar: ClaimGrammar,
    operators: Mapping[str, CompiledOperator],
    dimensions: Mapping[str, CompiledDimension],
    sorts: Mapping[str, CompiledSort],
) -> dict[str, object]:
    """Every declaration is keyed **by term identifier**, never held positionally.

    That is the load-bearing choice. A sequence would make the merge order an
    identity input, so recompiling after activating the same domains in a
    different order would move the compiled identity — and D §6 retired the
    second per-kind source of truth precisely so that a compiled artifact could
    not drift from what it was compiled from.
    """
    return {
        # Closed *sets*, so sorted here too. The base contract keeps its authored
        # order in memory because that order is what a reader sees; it is not an
        # input to anything, since a kernel tag's bytes are its symbol.
        "claim_grammar": {
            "version": claim_grammar.version,
            "quantifiers": sorted(claim_grammar.quantifiers),
            "polarities": sorted(claim_grammar.polarities),
            "sign_inapt_tag": claim_grammar.sign_inapt_tag,
            "layers": sorted(claim_grammar.layers),
        },
        "operators": {term: decl.schema_projection() for term, decl in operators.items()},
        "dimensions": {term: decl.schema_projection() for term, decl in dimensions.items()},
        "sorts": {term: decl.schema_projection() for term, decl in sorts.items()},
    }


def _compile_operator(contract: DomainContract, operator: OperatorDecl) -> CompiledOperator:
    return CompiledOperator(
        term=contract.term(operator.name),
        arity=operator.arity,
        arg_sorts=tuple(contract.term(sort) for sort in operator.arg_sorts),
        sign_apt=operator.sign_apt,
        layers=operator.layers,
        dimensions=tuple(contract.term(dimension) for dimension in operator.dimensions),
        retired=operator.retired,
        contract=contract.namespace,
    )
