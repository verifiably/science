Run `spec` to freeze the analysis that will assess a proposition. Give the
target proposition and the dataset it observes; the estimand as its parts —
a `levels` contrast (slot, baseline and comparison levels) or a
`continuous` one (slot, quantity and increment), the measure and its scale,
the reference value on that scale, the identification strategy, and any
conditioning terms, each term kind-prefixed as the contract's vocabularies
spell it; applicability as dimension=quantifier:term entries, if the
analysis is narrower than the claim; the method, assumptions and
falsification condition in the user's words; and the interpretation and
equivalence rule identities the kernel ships. Parameters are name=value
pairs. Nothing is defaulted: ask the user rather than guess a reference or
a scale. The frozen spec's identity is what `run` executes and `verify`
compares under; it cannot be edited, only superseded.
