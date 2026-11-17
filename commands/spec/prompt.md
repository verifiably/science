Run `spec` to freeze an analysis for a proposition and its one observes dataset.
Supply a UTF-8 native estimand JSON document, explicit standing and evidence mode,
and rule-identity=procedure-id bindings for held procedures. The interpretation
rule must have a binding. Supply a held model or assumptions registers when the
scientific route requires them; absent registers means an empty list.

The document declares form, functional, named bindings, typed outputs, reference,
control, uncertainty and assumptions with schema_version 1. Decimal positions
use JSON numbers; restriction bounds use their native strings. The target claim
and held records determine frozen identities and dependencies. Missing scientific
facts or prerequisites refuse; never infer them or create records automatically.

Give method, assumptions and falsification in the user's words, and the shipped
interpretation/equivalence rule identities. Parameters are name=value decimals.
Applicability accepts dimension=quantifier:term only for declared applicability
term restrictions. A frozen spec can only be superseded.
