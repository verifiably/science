"""The error hierarchy.

Every refusal in this package raises one of these. They are deliberately
fine-grained: several banked oracles turn on refusals staying *distinct* rather
than collapsing into one another (D3's five-way non-collapsing test is the
sharpest case), and a test that can only assert "something was raised" cannot
tell a good refusal from a bad one.
"""


class ScienceError(Exception):
    """Base for every error this package raises."""


class IdentityError(ScienceError):
    """A value or domain was refused by the identity contract."""


class UnsupportedValueType(IdentityError):
    """A value of a type the contract does not admit."""


class NullRefused(IdentityError):
    """A null. Refused, never pruned: an absent member must differ from a
    present-and-empty one, and pruning is what makes ``{"x": null}`` and ``{}``
    the same bytes."""


class BinaryFloatRefused(IdentityError):
    """A binary float. The caller supplies a decimal and owns the rounding, so a
    scientific value never inherits an accidental IEEE spelling."""


class NonFiniteDecimal(IdentityError):
    """``NaN``, ``Infinity``, ``-Infinity`` or a signalling form. JSON has no
    encoding for these and every substitute collides with something else."""


class NonStringKey(IdentityError):
    """An object key that is not a string."""


class KeyCollision(IdentityError):
    """Two object keys that are distinct before NFC normalization and identical
    after it. Rejected, never silently merged."""


class LoneSurrogate(IdentityError):
    """A string carrying an unpaired UTF-16 surrogate. It has no UTF-8 encoding,
    and the two implementations disagree about what it even is."""


class MalformedDomain(IdentityError):
    """A digest domain that is not a well-formed, versioned domain name."""


class ContractError(ScienceError):
    """A contract was refused at load."""


class MalformedContract(ContractError):
    """A contract that is structurally wrong — an unknown field, a missing one, a
    value of the wrong shape. Unknown fields are refused rather than ignored: D5
    is explicit that an unrecognized field is *"refused at load, never ignored and
    never digested"*, and a contract quietly accepting one would make the reader
    and the loader disagree about what the document says."""


class UnparsedContract(ContractError):
    """A contract object that no parser produced.

    The root of the trust chain, and the reason ``ProfileSpec``'s own refusal to
    be authored is not sufficient on its own. That refusal says a profile came
    from ``compile_profile``; this one says what ``compile_profile`` was handed
    came from the authored documents. Without it a claim can be typed against a
    hand-built contract — which is to say typed against nothing, every operator,
    sort, layer and dimension in it invented by whoever built the object, with
    the normative SSOT (D §6) never opened."""


class ContractMismatch(ContractError):
    """Two contracts, each genuine, that were not typed against one another.

    Distinct from ``UnparsedContract`` and worth its own name: nothing here was
    forged, no brand was bypassed, and every parser did its job. A domain
    contract's layer selections are checked **once**, at parse time, against the
    base contract it was handed, and the compiled operator then carries them as
    facts — so compiling it against a *different* base yields a claim standing on
    a layer the compiled base does not declare.

    The general shape, worth remembering because provenance checks do not catch
    it: authenticating each input separately says nothing about whether they
    **belong together**. The rule is narrower than *"every stage records its
    inputs"*, and both halves of it matter. It applies to an artifact whose
    **validity is conditional** on a particular upstream artifact — some check it
    passed was taken against that one and is never retaken — and which **may
    later be recombined independently**, so it can arrive somewhere holding a
    different partner. Such a boundary must **either verify a recorded dependency
    or revalidate the relation**; a stage that rechecks what it depends on, or
    whose output never travels apart from its input, owes neither."""


class SuccessionViolation(ContractError):
    """A successor contract that redefines, drops, or misdeclares its lineage.
    Refused at contract **load** — never at claim decode, which sees wire bytes
    and cannot tell a claim being authored now from one being restored from a
    backup (§7.3a)."""


class ProfileError(ScienceError):
    """A profile refused — at compilation, at construction, or at resolution."""


class DuplicateContribution(ProfileError):
    """Two contracts contributing to one namespace. D §8's rule for facets, and
    the same one here: contributions in *different* namespaces compose, and two
    contributions to one namespaced identifier are refused at compile, never
    resolved last-writer-wins."""


class SubclassRefused(ScienceError):
    """A subclass of a type that must stay closed.

    Opacity is worth exactly what `isinstance` is worth. A subclass can expose a
    raw constructor and mint an unchecked object that still satisfies
    `isinstance(x, Claim)` — at which point every downstream reader that trusts a
    `Claim` unconditionally is wrong, and M13's guarantee is gone without a line
    of it having been edited. `ProfileSpec` makes the same claim and needs the
    same seal, and so does every user-defined value type whose invariant a
    `Claim` trusts — `Referent`'s own check is what makes a claim's contents
    identifiers. The scope is that trust relation, not everything a claim holds.

    Not a `ClaimError` or a `ProfileError`: nothing is wrong with any claim or
    any profile. What is wrong is the code that was written."""


class WithdrawnFromAuthoring(ScienceError):
    """A retired identifier reached the **authoring** boundary — an operator, one
    of its argument sorts, a selected dimension, or that dimension's restriction
    sort.

    Deliberately not a `ContractError`: nothing is wrong with the contract, and
    nothing is wrong with the claim as a historical record. §7.3a puts retirement
    in authoring and *only* in authoring, so this refusal must never be reachable
    from decode, import or restore — which is why it is its own class and not a
    member of the family those boundaries raise.
    """


class ClaimError(ScienceError):
    """A claim, or a part of one, that is not admissible.

    Raised by the validated constructor and by the value types it admits. The
    subclasses stay distinct because M11 decodes each ill-formed input *in turn*
    and asserts a refusal each time; a single `ClaimError` would let one check
    silently cover for another's absence.
    """


class UntypedReferent(ClaimError):
    """A bare string, or any untyped value, in an argument slot or a restriction.

    §6.2 types a slot as `Referent(ArgSort(op, i))`, so the sort must travel with
    the value. A string carries no sort, which means nothing about it can be
    checked against the slot it was put in (M4)."""


class MalformedReferent(ClaimError):
    """A `Referent` whose sort or term is not an identifier.

    `term` is the one position in a claim that **nothing downstream checks**:
    the operator, the layer, the dimensions and the sorts are all matched against
    the profile's own tables, so a non-identifier there refuses on its own, but a
    referent's term is only checked for *membership* — and that is deferred to
    decode, against a snapshot. Without this check a `Claim` could be minted
    holding an integer where an identifier belongs."""


class UntypedQualifier(ClaimError):
    """A qualifier entry that is not a `Qualifier`. Structural typing is not
    enough here: an arbitrary object exposing `quantifier` and `restriction`
    would be stored inside a `Claim` and trusted as one."""


class ArityMismatch(ClaimError):
    """More or fewer arguments than the operator declares. Arity is per operator
    because it is not universally 2 (§6.2)."""


class ArgumentSortMismatch(ClaimError):
    """A referent of one sort in a slot declared for another. Inside the model
    these are different types and neither inhabits the other; here the sorts are
    runtime values, so the same fact is a refusal."""


class UndeclaredDimension(ClaimError):
    """A qualifier on a dimension the operator does not permit. `Dims(op)` is
    declared per operator — a population restriction is meaningless for a
    structural operator (§6.2)."""


class RestrictionSortMismatch(ClaimError):
    """A restriction bound to a referent of the wrong sort. A restriction is
    sorted exactly as an argument is (§6.2)."""


class UnknownQuantifier(ClaimError):
    """A quantifier outside the kernel's closed set. §6.4 rules the set
    kernel-owned and closed: `{ generic, universal, existential }`."""


class PolarityRefused(ClaimError):
    """A polarity the operator cannot carry — a sign asserted on a sign-inapt
    operator, no sign supplied for a sign-apt one, or a tag outside the base
    contract's closed set. For a sign-inapt operator `Polarity(op)` is the unit
    type (§6.3), so there is exactly one inhabitant and nothing for an author to
    choose."""


class InadmissibleLayer(ClaimError):
    """A layer outside the operator's declared set. `Layers(op)` is non-empty by
    construction — an operator admitting no layer would make `Claim` uninhabited
    at that operator (§6.2)."""


class TagCollision(ContractError):
    """Two kernel tags that must stay distinct and do not — a duplicate inside a
    closed set, or a ``sign_inapt_tag`` that is also an assertable polarity.
    ``inapt`` and ``unsigned`` are different facts (§7.5), and a projection that
    cannot tell them apart has lost the distinction it exists to carry."""
