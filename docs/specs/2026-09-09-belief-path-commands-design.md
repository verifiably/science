# The belief path — design

**Date:** 2026-09-09
**Status:** planned; implementation in progress (Tasks 1–6 and 10 complete). Amended 2026-09-23 for the kernel's typed estimand (§3, §4.3, §4.5, §5.2, §7, §8); the amendment was reviewed 2026-09-23. Goal task `sci-66b26d`.
**Scope:** the first half of sub-project 4 of the user/autonomy layer design
(`beliefs` `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`,
§5.1 and §8 item 4): the commands that carry one proposition from a typed
claim to a computed belief — `claim`, `dataset`, `spec`, `run`, `assess`,
`verify`, `next`, and the read `belief` — over a real world root, measured by
reproducing mm30's one proposition afresh through them. The coordination set
(`project`, `question`, `hypothesis`, `task`, `decide`) is the second half and
its own spec. `publish` is sub-project 5's. Nothing here mints a coordination
kind, acquires a dataset from a URL, scores a candidate under a priority
identity, or sandboxes an actor.

**Inherits:** the command framework design
(`docs/specs/2026-08-31-command-framework-design.md`) in full — the
declaration schema (§3), write classes and routes (§3.3), requirements and
enforcement (§4), the writer session (§5), the invocation protocol (§6), the
renderer and the write-audit rule (§7), the surfaces (§9) and the testing
shape (§11). The layer design's §4.4 (the derived queue), §5.2 (every write is
a kernel act; the surface owns no files) and §7.3 (the priority function is
sub-project 7's). The mm30 reproduction design and record
(`beliefs` `docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md`,
`docs/designs/2026-09-05-mm30-reproduction.md`): the path, the oracle and the
findings discipline. The biology pack design's §3.3 for the corpus-local
`mm30` contract. Terms used without definition — write class, requirement,
scoped writer, session ledger, `Refused(reason)`, act family, corpus-local
contract — are those documents'.

## 1. Problem

The stack has one success criterion (layer design §8; roadmap design §4.0 as
amended 2026-09-05): a coding-agent session over a `beliefs` world holding a
reproduced mm30 corpus, where `next` ranks a proposition, `run` executes a
real analysis under confinement, `verify` reaches `clean-environment`, and
`assess` admits the result to a computed belief, every step a governed
record. Everything under it now exists. Sub-projects 1, 2 and 3 are
complete. The `run-confinement` and `workflow-surface` lanes discharged. The
mm30 reproduction of 2026-09-05 walked the path as a library and reached the
evaluator's answer; the five findings it filed against the kernel are closed,
including the assessment-identity spelling that left its belief at
`NoBelief(no-eligible-assessment)`.

What does not exist is the surface. The framework ships `status` and
nothing else; no command mints a proposition, holds a dataset, freezes a
spec, runs, assesses or verifies. The reproduction driver under `beliefs`
`python/tools/reproduction/` did each of those with the kernel as a library,
under a full permit it constructed itself, from a `target.yaml` four of
whose parameters had to be supplied by hand (`beliefs-efc32d`). The record
is explicit that the driver is the instrument, not the surface: "sub-project
4's commands are written from what they show, not by promoting them."

## 2. Decisions

Rulings from the 2026-09-09 brainstorm, recorded so they are not re-derived.

1. **Two specs, the belief path first.** The six commands on the criterion's
   path each have a measured precursor in the driver. The coordination set
   has none, and putting five unmeasured commands in front of the criterion
   is the ordering the roadmap's 2026-09-05 amendment exists to prevent.
2. **Reproduce afresh; the record's corpus is the oracle.** The measurement
   starts from an empty adopted corpus and walks the path through the
   commands as an agent session would. The 2026-09-05 record's corpus is
   compared against, not continued: it was typed under the unsorted
   vocabulary with an unanchored log, and continuing it would exercise
   `claim` and `dataset` only in fixtures. §8 states what is compared.
3. **A separate `spec` command.** Freezing the analysis spec is the step the
   record measured as the one with real authoring cost, and its identity is
   what `run` executes against and `verify` compares under. Folding it into
   `run` would hide the most person-shaped inputs on the path inside the
   command that also needs a sandbox and a host. The layer design's list is
   "on the order of a dozen", not closed.
4. **Rule implementations live in the kernel.** The interpretation rule
   (`outcome-file`) and the equivalence rule (`content-identity-equality`)
   the driver defined become reference implementations `beliefs` ships,
   keyed by rule identity, beside the belief policy's existing
   `science.belief.v1/reference`. The surface looks a rule up by identity
   and defines none; an unknown identity is a kernel refusal; the audit's
   recomputation resolves the same implementations the freeze bound. §6.
5. **Corpus-local contracts are named by the launcher config, for now.** A
   `contracts` key beside `domains` lists domain-contract documents by path;
   the loader parses each against the shipped base exactly as the driver
   does and compiles them into the profile; the manifest pin check at
   session open is what keeps a document honest. **This is superseded
   whenever the kernel gives contracts a home** — the first full contract cut
   (`beliefs-eacbe2`) or a corpus-root layout rule — and the spec says so
   here rather than designing that home. §5.
6. **Command order on the path is `run`, `assess`, `verify`; belief is a
   read.** Verification publication requires the assessment's corpus ref
   (`publication_node` refuses without one), so the assessment is minted
   before the replay. The belief is computed at read time by the evaluator,
   never stored, and the write-audit rule (§7.4) forbids a write from
   returning it — so it has its own read command, `belief`.
7. **`next` orders by a fixed rule and names no priority identity.** The
   derived queue of layer §4.4 is computed at read time; its scoring function
   `science.priority.v1` is sub-project 7's and is not begun here.
8. **World, corpus and store initialization and adoption are outside the
   commands.** Framework §4.4 rules lifecycle and registry acts operator-time
   library operations, and `science` may not construct the full permit they
   need. The measurement record documents the operator recipe (§8.2), which
   is the driver's first step.
9. **Two kernel seams this spec depends on**, filed in `beliefs` before the
   plan is written: the reference rules of ruling 4, and the scoped writer's
   `run` and `holdings` routes (§6). Neither is designed here beyond the
   requirement stated; each is its own `beliefs` task. One framework seam,
   §6.3, is this repository's and is the plan's first task.

## 3. The path, and the record it leaves

One proposition, in the order the commands run. Every step is a governed
record or a refusal; nothing writes around a refusal (layer §5.2).

| # | command | write class | act | leaves |
|---|---|---|---|---|
| 1 | `dataset` (the concept vocabulary) | `mints:dataset,holdings-observation` | store write and observation under the holdings boundary; `add` of the dataset record under its content address | the bytes in the store, one `holdings-observation` (`Found`), one `dataset` record — the list the contract's `concept` sort binds, so §5.3's snapshot resolves from here |
| 2 | `claim` | `mints:proposition` | `build_claim` under the profile, then `decode_claim` against the snapshot; `add` | one `proposition` record carrying the claim projection and a display statement |
| 3 | `dataset` (the expression matrix) | `mints:dataset,holdings-observation` | as step 1 | as step 1 |
| 3a–3c | `dataset` (the stage-level, measure and identification lists) | `mints:dataset,holdings-observation` | as step 1, once per list | as step 1, once per list — the vocabularies the contract's estimand sorts bind by dataset identity, so §4.3's typed estimand resolves from here |
| 4 | `spec` | `mints:analysis-spec` | `freeze` against the kernel's reference rules; `add` | one `analysis-spec` record; the spec identity is fixed from here |
| 5 | `run` | `mints:run,act-report` routed `run` | `execute_assessment_run` under `CONFINED_POLICY` through the scoped writer's run route | one `run` record, its two launch attestations, the settled intent on the registration chain |
| 6 | `assess` | `mints:assessment` | `build_assessment` through the spec's interpretation rule; `add` | one `assessment` record |
| 7 | `verify` | `mints:run,act-report,verification` routed `run`, `run`, `corpus-write` | `replay` through the run route; `derive_scope`; `build_verification` against the reference equivalence rule; `add` of `publication_node(…, assessment_ref)` | the replayed `run` record, one `verification` record naming the assessment and both runs |
| 8 | `belief` | `read-only` | `evaluate_over` under `science.belief.v1` | nothing; the answer is rendered |
| — | `next` | `read-only` | the derived queue | nothing; the ranking is rendered |

The concept vocabulary is held **before** the claim is typed: `claim`
resolves its referents against the snapshot §5.3 builds from the held list,
and refuses when the list is not held (§4.1). The contract document names
the list's content address before adoption, so the operator computes that
address from the file before the corpus exists. The record's step 1b did the
same, and its 2026-09-08 re-run is where slot 0 first resolved `member`. The estimand vocabularies follow
the same rule (amended 2026-09-23): each list the contract binds by dataset
identity is held by its own `dataset` invocation before `spec`, because a
file prepared on disk is not held until `dataset` writes it to the store
and records the observation, and `spec` refuses an unheld dataset-bound
vocabulary (§4.3).

## 4. The commands

Declarations follow framework §3.2. Every input is one of the closed types;
where the driver read a mapping from `target.yaml`, the command takes the
fields one at a time. Budgets are stated per command and are the contract
(§3.2); the numbers below are the initial declarations, chosen so a
single-record write report fits with room and a read report pages.

### 4.1 `claim`

```toml
schema_version = 1
name = "claim"
purpose = "Type a proposition under the profile and mint its record."
write_class = "mints:proposition"
output_budget = 4096

[inputs.subject]
type = "string"
required = true
doc = "Kind-prefixed term, e.g. concept:disease-stage."
[inputs.predicate]
type = "string"
required = true
doc = "The predicate as the operator plan names it, e.g. affects."
[inputs.object]
type = "string"
required = true
doc = "Kind-prefixed term, e.g. protein:PHF19."
[inputs.layer]
type = "string"
required = true
doc = "A claim layer the plan names, e.g. causal."
[inputs.polarity]
type = "string"
required = true
doc = "A polarity the plan names, e.g. positive."
[inputs.slug]
type = "string"
required = false
doc = "Record id; absent, derived from the three terms as the driver derives it."

[reads]
families = ["corpus-stored", "holdings"]   # holdings: the resolution snapshot (§5.3)
```

The handler resolves each term's kind prefix to a sort, and the predicate
with the two kinds to an operator, through the **operator plan** of the
corpus-local contract document (§5.2). A shape with no plan row refuses
`invalid-input` naming the shape; a plan row is never nearest-typed, exactly
as the driver's `operator_for` refuses. `build_claim` refusals (`ClaimError`,
`ArgumentSortMismatch`) surface as `invalid-input` carrying the kernel's
message.

**The validation path, stated because `build_claim` consults no vocabulary.**
`build_claim` types; membership is judged at decode. So the handler, before
any act, calls `decode_claim(WireClaim(**project_claim(claim)),
profile=profile, snapshot=<§5.3 snapshot>)` — the projection is a plain
mapping whose five keys are the wire claim's fields, and the decoder
refuses anything but a `WireClaim`. The kernel refuses `not-member` there
and permits the other four outcomes; the receipt records what was
consulted. On top of that the surface applies **one stricter policy, scoped
to dataset-identity bindings**: a `VocabularyBinding` is either a held
dataset by content identity or a namespace with a release, never both. For
a sort bound **by dataset identity** — the corpus-local `concept` sort —
a referent whose outcome is `not-consulted` or `not-available` means the
snapshot lacks a vocabulary this corpus was written to hold, and the
surface refuses `invalid-input` naming the dataset address to hold first.
A person authoring under such a sort gets a membership answer or a
refusal, never a claim that silently skipped the check. For a sort bound
**by namespace and release** — the biology pack's `molecular-entity`, HGNC
at `2026-07-01` — the kernel's permissive reading is retained unchanged:
no ontology release is held here, the referent resolves `not-consulted`,
and the claim is accepted, exactly as the record measured for slot 1 on
2026-09-08. The reproduction's target has one slot of each kind, which is
why the policy is drawn where it is. This is why the vocabulary `dataset`
precedes `claim` in §3.

The record is `stored.proposition_node(slug, title, claim=
project_claim(claim), display_statement="<subject> <predicate> <object>")`.
The report is the record block.

### 4.2 `dataset`

```toml
name = "dataset"
purpose = "Hold a local file in the store and mint the dataset record under its content address."
write_class = "mints:dataset,holdings-observation"
output_budget = 4096

[write.routes]
holdings-observation = "holdings"   # dataset's one route is derived

[inputs.path]
type = "string"
required = true
doc = "A regular file on this host; its bytes are held, never a directory."
[inputs.title]
type = "string"
required = true
doc = "The dataset's title."
[inputs.locator]
type = "string"
required = false
doc = "An empirical-observation locator, e.g. accession:GSE179929; absent, the record carries no such facet."
[inputs.facets]
type = "list-of-string"
required = false
doc = "Domain facets as name=key:value pairs, e.g. biology/gene-axis=axis:rows,namespace:HGNC."

[reads]
families = ["corpus-stored"]
```

The handler reads the file, digests it, computes the dataset address from
the declaration (`dataset_address(DatasetDeclaration(resources=(…,)))`),
writes the bytes to the store under a **content-derived location**,
`<sha256 hex>/<basename>`, and publishes the observation through the scoped
writer's holdings route (§6.2), then mints `stored.dataset_node(address,
title, resources, empirical_observation, domain_facets)` and checks
`admission_state` over the stored declaration and the observation reads
`Held`; anything else is an internal error, since held bytes with a matching
digest that do not read `Held` is a kernel defect, not input. A non-regular
path refuses `invalid-input` before any act.

**Collisions.** Two different files can share a title and a basename; a
title-derived directory would put them at one location, and the holdings
boundary writes a location without looking, so differing digests would
become contested heads. The content-derived directory makes a location
name one byte sequence, so a collision is always the same bytes. Two cases
remain, both checked before any act: a `dataset` record already exists
under the computed address — refuse `invalid-input` naming it, since the
dataset is held and the record is the person's answer; or observations
exist at the location with no record (a prior invocation held the bytes and
died before the mint) — the handler passes every existing observation at
that location as `standing`, so the new `Found` supersedes them and the
holdings reduction sees one head. A location is never reused for other
bytes, so no other supersession arises here. A
`locator` carries `attested_by` as the session actor — the endpoint sets it,
never the caller (framework §5.1). The report is the dataset record block;
the observation is not a record block the audit knows, and the write-audit
rule is satisfied because the report carries the minted dataset only.

URL acquisition is the `url-retrieval` lane's (`beliefs-d13fe8`); until it
lands the person fetches, and the surface holds what it is given.

### 4.3 `spec`

```toml
name = "spec"
purpose = "Freeze an analysis spec against the kernel's reference rules and mint its record."
write_class = "mints:analysis-spec"
output_budget = 4096

[inputs.target]
type = "string"
required = true
doc = "The proposition ref this spec assesses."
[inputs.dataset]
type = "string"
required = true
doc = "The dataset ref the analysis observes (role observes)."
[inputs.contrast]
type = "enum"
choices = ["levels", "continuous"]
required = true
doc = "What the estimand contrasts: two levels of an argument, or an increment along a quantity."
[inputs.slot]
type = "int"
required = true
doc = "The claim argument position the contrast varies (0-based)."
[inputs.baseline]
type = "string"
required = false
doc = "levels only: the baseline level, a kind-prefixed term, e.g. level:ndmm."
[inputs.comparison]
type = "string"
required = false
doc = "levels only: the comparison level, a kind-prefixed term."
[inputs.quantity]
type = "string"
required = false
doc = "continuous only: the quantity the increment is taken along, a kind-prefixed term."
[inputs.increment]
type = "string"
required = false
doc = "continuous only: the increment, a decimal."
[inputs.measure]
type = "string"
required = true
doc = "The measured quantity, a kind-prefixed term, e.g. measure:rna-seq-tpm."
[inputs.scale]
type = "enum"
choices = ["additive", "multiplicative"]
required = true
doc = "The scale the effect is expressed on."
[inputs.reference]
type = "string"
required = true
doc = "The null value on that scale, a decimal (0 additive, 1 multiplicative is typical, never assumed)."
[inputs.identification]
type = "string"
required = true
doc = "The identification strategy, a kind-prefixed term, e.g. identification:observational."
[inputs.conditioning]
type = "list-of-string"
required = false
doc = "Kind-prefixed terms the estimate conditions on; absent, none."
[inputs.method]
type = "string"
required = true
[inputs.assumptions]
type = "string"
required = true
[inputs.falsification]
type = "string"
required = true
[inputs.applicability]
type = "list-of-string"
required = false
doc = "Scope qualifiers as dimension=quantifier:term; absent, the spec applies wherever the claim does."
[inputs.interpretation_rule]
type = "string"
required = true
doc = "A rule identity the kernel ships a reference implementation for."
[inputs.equivalence_rule]
type = "string"
required = true
[inputs.parameters]
type = "list-of-string"
required = false
doc = "name=value pairs; values parse as decimals."
[inputs.supersedes]
type = "string"
required = false
doc = "The analysis-spec ref this one supersedes."

[reads]
families = ["corpus-stored"]
```

**The typed estimand (amended 2026-09-23).** The kernel types a spec's
estimand against the claim it answers (`beliefs.estimand.build_estimand`):
the target's operator fixes every sort through its contract's `estimands:`
declaration, and the claim's identity enters the estimand, so the write
boundary refuses a spec whose estimand names another claim. The spec's
`applicability` is likewise a typed qualifier mapping
(`build_applicability`), not prose. The surface therefore takes the
estimand as its parts, and takes terms and numbers only — never a sort,
exactly as `claim` takes sorts from the plan. The handler restores the
target's `Claim` with `decode.claim_from_stored(node, profile=,
snapshot=<§5.3>)`; reads `profile.estimand(claim.operator)`, whose absence
refuses `invalid-input` naming the operator (a contract that declares no
estimand for an operator admits no spec against claims under it); builds
each `Referent` with the declaration's sort for its role —
`level_sorts[slot]` for `baseline` and `comparison`, `measure_sort`,
`identification_sort`, `conditioning_sort`; and calls `build_estimand(…,
contrast=LevelsContrast(slot, baseline, comparison) |
ContinuousContrast(slot, quantity, increment), measure=Measure(measure,
scale), reference=Decimal(reference), control=Control(identification,
conditioning), snapshot=)` and `build_applicability(profile, claim,
qualifiers, snapshot=)`, where each `applicability` entry
`dimension=quantifier:term` becomes `Qualifier(quantifier, Referent(<the
dimension's restriction_sort>, term))` and the kernel checks the quantifier
against the claim grammar. A contrast input given for the other contrast
kind, or one missing for its own, refuses: nothing is defaulted. A
decimal that does not parse refuses.

Every authoring error the kernel raises on this path is `invalid-input`
with its message, and is caught before the first act: `ESTIMAND_ERRORS`
(`EstimandError`, `UnboundReferent`) from `build_estimand`; `ClaimError`
from `build_applicability`, which runs the claim grammar's qualifier checks
and raises its subclasses (`UnknownQuantifier`, `UndeclaredDimension` and
the rest); `DecodeError` and `ClaimError` from `claim_from_stored`; and
`ProfileError` from `profile.estimand`. The dispatcher closes a `Refused`
raised before any act (§6.3) but not a kernel authoring exception, which
would escape it and leave the invocation open, so a retry under the same
`invocation_id` would read `outcome-unknown`; mapping the full set is what
keeps a malformed spec a replayable refusal.

The kernel refuses only `not-member`; it accepts `not-consulted` and
`not-available`, so the surface enforces §5.2's rule itself, as `claim`
does (§4.1). Before the first act the handler reads both receipts — the
estimand's and the applicability's — and, for every referent whose sort is
bound by dataset identity, refuses `invalid-input` when its outcome is
`not-consulted` or `not-available`, naming the sort and the unheld
vocabulary's `dataset:<address>` and saying to hold it with `dataset`. A
referent under a namespace binding resolving `not-consulted` stands
(§4.1's policy). `method`, `assumptions` and `falsification` stay prose;
the kernel does not type them.

The handler resolves the dataset ref to its address, builds the `SpecDraft`
with one `SpecInput(role="observes", dataset=<address>)` and
`nondeterminism=Deterministic()`, looks the two rule identities up in the
kernel's reference rules (§6.1) — an unknown identity refuses
`invalid-input` with the kernel's message — and calls `freeze(draft,
held_rules=…, supersedes=…)`. `MalformedSpec` and `UnfreezableSpec` are
`invalid-input`.

**Deterministic only.** The kernel's other two contracts need authoring
this surface does not yet take: `Seeded` carries a `SeedPlan` (a derivation
rule and logical stream identities) and `StochasticUnseeded` a non-empty
rationale, and a seeded workflow's family streams enter the definition
snapshot `run` builds (§4.4). The reproduction is deterministic, so the
declaration exposes no nondeterminism input and `run` fixes family streams
empty; the first non-deterministic analysis authored through the surface
is a spec amendment adding those inputs together, not a default. The record is
`stored.analysis_spec_node(spec)`, whose id is the spec identity. The
report is the record block.

What the spec does **not** carry is the workflow. `execute_assessment_run`
takes the `WorkflowDefinition` and the code roots as run-time arguments
beside the frozen spec, and the run record's recipe captures the
definition snapshot and the bundle identity. So the code is `run`'s input
(§4.4), and a spec is reusable across runs of the same analysis, which is
what verification compares.

### 4.4 `run`

```toml
name = "run"
purpose = "Execute the analysis for a spec once, under confinement, and mint the run record."
write_class = "mints:run,act-report"
output_budget = 4096

[write.routes]
run = "run"
act-report = "run"

[inputs.spec]
type = "string"
required = true
doc = "The analysis-spec ref."
[inputs.dataset]
type = "string"
required = true
doc = "The dataset ref the spec's observes role names; its held bytes are the run's input."
[inputs.code]
type = "string"
required = true
doc = "A directory on this host: the bundle root, e.g. analysis/ holding workflow/Snakefile."
[inputs.entrypoint]
type = "string"
required = true
doc = "The workflow entrypoint relative to the bundle's parent, e.g. analysis/workflow/Snakefile."
[inputs.targets]
type = "list-of-string"
required = true
doc = "The workflow targets; also the declared outputs."
[inputs.cores]
type = "int"
required = false
default = 1

[reads]
families = ["corpus-stored", "holdings"]
```

Before touching the session: `host_prerequisites()`; a reason refuses
`invalid-input` carrying it (the framework has no host-refusal code, and
adding one is a spec amendment this document does not make). The handler
restores the `FrozenSpec` from the record (`stored.analysis_spec_value`),
resolves the dataset ref to the held file in the store (§5.4), reads the
Snakefile at the entrypoint into a `WorkflowDefinition` with no family
streams (deterministic only, §4.3), and calls `execute_assessment_run(spec, port=<run route>,
boundary_policy=CONFINED_POLICY, definition, code_roots=(code,),
held_inputs={address: path}, entrypoint, targets, declared_outputs=targets,
observer=<session actor>, started_at=now, host_realization=hostname,
scratch_base=<operations root>/scratch/<invocation>, cores)`. A
`RunRefused` renders as the refusal envelope with the kernel's reason
(`no-frozen-spec`, the preflight reasons, `execution-failed`,
`permit-exceeded`); for a `RunMinted`, the handler reports the run record
block. The dispatcher rebuilds the wire report from every identity minted
by the invocation, including the run route's act reports, in `(uid, record_id)`
order. The scratch directory is the operations root's, never a corpus's,
and is left for the operator as the driver left its.

The code directory is read from the host and its identity enters the
record; the surface stores no copy of it. Layer §5.2's "owns no files" is
about corpus writes, and a code root a person names is input like a
dataset path.

### 4.5 `assess`

```toml
name = "assess"
purpose = "Derive the assessment a run's outputs support under its spec's rule, and mint it."
write_class = "mints:assessment"
output_budget = 4096

[inputs.run]
type = "string"
required = true
doc = "The run ref."

[reads]
families = ["corpus-stored"]
```

The handler decodes the run closure, restores the spec the closure names,
resolves the interpretation rule from the kernel's reference rules, and
calls `build_assessment(run, specs={identity: spec},
implementations={impl.identity: impl})`. An `AssessmentFinding` refuses
`invalid-input` with its reason. The record is `stored.assessment_node(
derived.identity()[:16], title, spec, run=run_ref(address), proposition,
outcome, interpretation_rule, estimand, applicability, **optional)` — the
driver's call, now with the run member in one spelling (`beliefs-ae9b18`).
The estimand and applicability are the derived assessment's own, carried
from the frozen spec; the kernel requires both (amended 2026-09-23), and
only `estimate` and `uncertainty` stay optional. The report is the
record block.

### 4.6 `verify`

```toml
name = "verify"
purpose = "Replay an assessment's run, derive scope and verdict, and mint the verification."
write_class = "mints:run,act-report,verification"
output_budget = 4096

[write.routes]
run = "run"
act-report = "run"
# verification's one route is derived

[inputs.assessment]
type = "string"
required = true
doc = "The assessment ref."
[inputs.code]
type = "string"
required = true
doc = "The bundle root, as given to run; its identity must match the original's."
[inputs.entrypoint]
type = "string"
required = true
[inputs.cores]
type = "int"
required = false
default = 1

[reads]
families = ["corpus-stored", "holdings"]
```

The handler loads the assessment, its run, its spec and the dataset the
run observed, then `replay(original, spec, …)` through the run route with
the same arguments `run` used. `derive_scope(original, replayed,
certification=None)` and `build_verification(original, replayed, specs,
held_rules={equivalence}, contract_identity=<manifest pins' science
contract>, epoch=<current epoch's packaging identity or "none-published">)`
follow; the record is `publication_node(verification,
assessment_ref=<assessment ref>)`. A replay `RunRefused` is the refusal
envelope. The handler reports the verification record block, whose title
carries scope and verdict. The dispatcher rebuilds the wire report from
every identity minted by the invocation, including the replayed run and
the run route's act reports, in `(uid, record_id)` order; the audit admits
the replayed run because the declaration names `run`.

`verify` does not say whether the belief is admitted. That is `belief`'s.

### 4.7 `belief`

```toml
name = "belief"
purpose = "Evaluate the shipped belief policy over one proposition and render the answer."
write_class = "read-only"
output_budget = 8192

[inputs.proposition]
type = "string"
required = true

[reads]
families = ["corpus-stored", "holdings", "epoch", "registry"]
```

The handler builds `Availability(observations=<every stored Found
holdings observation keyed by dataset address>, implementations={BELIEF_V1},
fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES})` and the `SuppliedContext`
of §5.5, then `evaluate_over(view, proposition, availability, context,
profile, resolution=<§5.3 snapshot>, binding=PolicyBinding(BELIEF_V1_RULE,
BELIEF_V1.identity))`. It renders one `KeyVals` block: the answer's kind
(`Belief`, `NoBelief`, `Refused`), its reason and detail, and for a
`Belief` its value, input digest and policy binding — the three the record
says must travel together. The holdings reduction rule (supersession,
coverage) is applied through the kernel's `dataset_observations` adapter,
not bypassed as the driver bypassed it.

### 4.8 `next`

```toml
name = "next"
purpose = "Rank the propositions this world can act on, from the current view."
write_class = "read-only"
output_budget = 16384

[inputs.limit]
type = "int"
required = false
default = 10

[reads]
families = ["corpus-stored", "holdings", "epoch", "registry"]
```

The derived queue of layer §4.4, computed at read time and stored nowhere.
For every stored proposition the handler classifies, in this order, and
renders the first `limit` in class order then record id. Inputs are joined
through the specs that target the proposition: a proposition's inputs are
the `observes`-role dataset addresses of every `analysis-spec` whose
`target` is its ref, and an input is held when `admission_state` over the
stored declaration and the corpus's observations reads `Held`.

1. **ready** — no assessment names it, and at least one spec targets it
   whose inputs are all held;
2. **not ready** — no assessment names it, and no such spec: either no
   spec targets it or every targeting spec has an input not held;
3. **assessed, not admitted** — an assessment names it and class 4 does
   not apply: no verification in `ADMITTED` state names the assessment, or
   one does and `admit` still refuses (an input no longer held, a run
   mismatch);
4. **admitted** — for some assessment naming it, `admit(assessment, run,
   observations, verifications)` returns `Admitted`.

Class 4 is the criterion's "admitted", computed by the same gate `belief`
runs; class 3 is its complement over assessed propositions, so the four
classes partition every stored proposition. Each row renders the
proposition's display statement and its class. This
is a fixed rule so that `next` ranks a proposition today; the scoring
function of layer §7.3 replaces the ordering, not the classification, and
until then `next` names no priority identity. "Stale verifications" and
"open tasks" from §4.4 are not classes here: nothing supersedes a
verification yet, and tasks are the coordination set's.

## 5. Configuration and the read context

### 5.1 Two keys

`contracts` (ruling 5) and `store_root` join framework §9.1's file:

```toml
world_root = "…"
world_id = "…"
corpus_roots = ["…"]
operations_root = "…"
domains = ["biology"]
contracts = ["…/mm30.yaml"]     # corpus-local domain-contract documents; may be empty
store_root = "…"                # the holdings store; required
```

`contracts` is required and may be empty, for the reason `domains` is: a
config written before this spec refuses rather than silently compiling a
profile the corpus's pins disagree with. `store_root` is required because
`dataset` binds a store and the session carries none; the loader resolves
it like `operations_root`. Both are added to the framework design's §9.1
as amendments in the implementing commit.

### 5.2 Compiling the profile, and the operator plan

The loader parses each document with `parse_domain_contract(doc["contract"],
source, base=shipped_base_contract(), predecessor=None)` and compiles
`compile_profile(base, [shipped_domain_contract(ns) …] + [parsed …])`. A
document that fails to parse or compile refuses `invalid-input` at load,
like an unshipped namespace. Beside `contract`, a document may carry `plan`
— the driver's operator plan: `operators` rows of `(predicate, subject kind,
object kind) → operator`, `sorts` of kind prefix → sort, `layers` and
`polarities` — which `claim` reads (§4.1). The plan is launcher input, not
contract content; the contract's identity does not cover it, and the
manifest pins check only the contract.

A contract whose operators a spec will target declares an `estimands:` row
for each such operator — `level_sorts` by argument slot, `measure_sort`,
`identification_sort`, `conditioning_sort` — and declares those sorts
(amended 2026-09-23; §4.3). A sort bound by namespace and release resolves
`not-consulted` and stands, so an estimand vocabulary need not be held for
the surface to type against it; one bound by dataset identity must be held,
as for `claim`. The loader parses every document as `lineage: genesis`
(`predecessor=None`): a successor lineage refuses at load, and a
successor-aware home for contracts is the kernel's to give (ruling 5).

### 5.3 The resolution snapshot

A corpus-local contract may bind a sort to a vocabulary dataset (`concept:
{vocabulary: dataset:sha256:…}`). The read context resolves each such
binding by looking the dataset record up in the corpus, reading its held
bytes from the store by the address the record declares, checking the
digest, and building `build_snapshot(readable={binding: lines})`. A binding
whose dataset is not in the corpus, or not held, yields a snapshot without
it; `claim` then refuses a referent under that sort (§4.1's surface policy),
naming the address to hold. This is the driver's `snapshot_over`, with its two
`RuntimeError`s as `invalid-input`.

Bootstrapping order, stated because it is circular at first sight: the
document names the concept list by content address; the operator computes
that address from the file (`dataset_address` over one resource) and
writes it into the document; the corpus is adopted under the profile that
compiles from it; then `dataset` holds the list, and from that point the
snapshot resolves. The record's step 1b is the precedent.

### 5.4 Holdings reads

`run`, `verify`, `belief` and `next` read the store: the held path for a
dataset address (`run`, `verify`), and every `Found` observation keyed by
address (`belief`, `next`). A `holdings` read family is added to the
schema's documented families for the reader tests (framework §3.2 makes
`reads` a test contract, not runtime enforcement).

### 5.5 The supplied context

`belief` supplies the closure members the evaluator does not compute
(`SuppliedContext`): `snapshot = lineage_snapshot(view, [addresses])`;
`producer_snapshot_identity` = the current epoch's packaging identity, or
`"no-epoch-published"` when `current_epoch` raises `EpochUnknown`;
`retractions = RetractionEnumeration(found=(), coverage=(corpus_id,))` — no
retraction search exists to run, and the enumeration states its scope;
`node_corpus` mapping the gathered assessment identities to this corpus;
`pins` from the manifest. Each is a read the declaration lists.

## 6. Seams this spec depends on

Three are `beliefs` tasks, filed 2026-09-09 and depended on by `sci-66b26d`:
`beliefs-e5ab34` (§6.1), `beliefs-5fe2e3` (§6.2), and `beliefs-2d9a55`, the
public store identity reader §6.2 names, split out of the routes seam so the
read-only commands can land before it. This document states the
requirement; their designs are theirs. The fourth (§6.3) is a framework
amendment in this repository and the plan's first task.

### 6.1 Reference rule implementations

`beliefs` ships, keyed by rule identity and importable by the surface
without constructing anything: an interpretation rule that maps a
`ResultManifest`'s digest for a canonical outcome file to one of
`supported`, `refuted`, `inconclusive` (the driver's
`mm30-reproduction/outcome-file/v1`, under a kernel identity), and the
equivalence rule `content-identity-equality/v1` (identity of result
manifests). Each carries its fixtures, so `freeze` binds it and
`check_verification` recomputes against it. The surface's `spec` takes rule
identities as strings and resolves them through this table; an identity not
in it refuses.

The rule identity is part of what the spec identity digests
(`rule_bindings`), so a spec frozen under the kernel's identity for the
outcome rule differs in identity from the record's `86aaa1a8…`. §8.3
states what is compared instead.

### 6.2 The scoped writer's `run` and `holdings` routes

`ScopedWriter` exposes seven corpus-write methods. The run boundary takes an
`OperationPort` and the holdings boundary an `ActContext`, and both bind an
`Authority`, which framework §4.2 forbids the surface to see or thread. So
today a command whose declared route is `run` or `holdings` obtains a
requirement, a scoped writer, and no way to act. The seam: the scoped
writer exposes the two routes under the invocation's scoped authority — an
operation port for `execute_assessment_run` and `replay`, and a holdings act
context over a store root the session is opened with — and records their
commits as `act` lines the same way `add` does, so the ledger-versus-chain
comparison meets them. `open_attended_session` therefore takes the store
root, which is why §5.1 makes it configuration. The read context also needs
the store root's identity without a session (§5): `beliefs.root.store_identity`,
the public form of the kernel's private genesis read by detached inspection,
is its own task, `beliefs-2d9a55`.

### 6.3 Surface refusals from a write handler

Every write command above validates before its first act and refuses
`invalid-input` from inside the handler — a shape with no plan row, a
non-regular path, an unknown rule identity, a host without bubblewrap. The
dispatcher today claims the invocation, then closes it only for the kernel
refusals it catches (`PermitExceeded`, `KernelRefusalValue`,
`WriteRefused`); a surface `Refused` raised by the handler propagates with
the invocation still open, and a retry under the same id refuses
`outcome-unknown` for a write that never acted. Framework §6.1 is amended:
a `Refused` raised by a write handler is caught by the dispatcher, which
reads the invocation's acts from the session; **with no act recorded** it
closes the invocation with the refusal envelope, exactly as a kernel
refusal closes, and a retry replays that refusal from the ledger through
the existing `ClaimDone` path; **with an act recorded** the handler broke
the validate-before-act rule, and the dispatcher closes `done` with the
minted identities — the ledger records act truth — and raises an internal
error, since a half-acted write is a defect and not a refusal. The
amendment lands in §7's first task with two tests: a handler that refuses
before acting leaves a closed invocation whose retry replays
`invalid-input`; a handler that acts and then refuses closes `done` and
surfaces `internal-error`.

## 7. Testing

Framework §11's harness shape, per command: the assertion, the source
mutation that falsifies it, the test that catches the mutation. Fixture
worlds are the existing helpers grown as needed: a corpus-local test
contract with one dataset-bound sort, one namespace-and-release-bound
sort and a two-row plan, and an `estimands:` row for the plan's first
operator whose level sort is bound by dataset identity and whose measure,
identification and conditioning sorts are bound by namespace (amended
2026-09-23), a held one-line dataset, a fixture bundle whose Snakefile
writes a fixed outcome.

- **The dispatcher amendment of §6.3**, first: the two tests it names,
  against the synthetic exemplars, before any command handler exists to
  need it.
- **Each write command mints exactly its declared kinds.** A run of the
  handler over the fixture world leaves the declared records and no others;
  the audit rejects a report carrying anything else. One refusal per
  command proving the class is enforced at the act: a handler mutated to
  mint a kind it does not declare is refused `permit-exceeded` under the
  full attended permit (framework §4.2).
- **`claim`** types the fixture's one plan row and refuses a shape with no
  row; the refusal names the shape. The fixture contract binds one sort by
  dataset identity and one by namespace and release. Under the
  dataset-bound sort a member resolves, a non-member refuses with the
  kernel's message, and an unheld vocabulary refuses naming the dataset
  address; under the namespace-bound sort the referent resolves
  `not-consulted` and the claim is accepted.
- **`dataset`** holds bytes whose digest the record declares and reads
  `Held`; a non-regular path refuses before any act; the locator's
  `attested_by` is the session actor and no input can set it. Two files
  with one title and basename land at two locations; the same bytes twice
  refuse naming the record; bytes held with no record are re-held with the
  earlier observation superseded.
- **`spec`** freezes against the reference rules and the record's id is
  the spec identity; an unknown rule identity refuses; a stochastic-unseeded
  draft under a bitwise equivalence rule refuses at freeze. The typed
  estimand (amended 2026-09-23): with the level vocabulary not held, `spec`
  refuses `invalid-input` naming the level sort's `dataset:<address>` and
  mints nothing (the mutation that drops the receipt check makes the spec
  mint); the namespace-bound measure resolves `not-consulted` and the spec
  mints. A contrast input given for the other kind, or missing for its
  own, refuses. An applicability entry with an unknown quantifier and one
  naming an undeclared dimension each refuse `invalid-input`, and the
  same `invocation_id` replayed returns the identical refusal, not
  `outcome-unknown` (the mutation that narrows the catch to
  `ESTIMAND_ERRORS` fails the replay).
- **`run`** refuses on a host without bubblewrap before any act (mocked
  `host_prerequisites`); on a capable host it mints one run under
  `CONFINED_POLICY`. The confined case is marked to run only where the
  prerequisites hold and is otherwise skipped with the reason, as the
  kernel's own confinement tests are.
- **`assess`** mints the assessment whose outcome the fixture bundle's
  outcome file fixes; the stored and derived identities agree.
- **`verify`** mints a verification naming the assessment and both runs;
  a fixture whose replay disagrees yields `failed` and still mints.
- **`belief`** over the fixture path answers `Belief` once the verification
  is admitted and `NoBelief` with the reason before; the three-part answer
  renders.
- **`next`** classifies the fixture's propositions into the four classes and
  the mutation that drops a held dataset moves a row from class 1 to 2, and
  an admitted row to class 3; a proposition no spec targets is class 2
  however many datasets are held.
- **Every command through its transport** (framework §9.4). The reads
  render byte-identical through the CLI and the MCP server. A write's
  report contains every identity minted by the invocation, rebuilt from the
  corpus in `(uid, record_id)` order. Uids are minted per world, so writes
  are compared to the corpus each transport wrote to, not
  byte-for-byte across transports; each write is driven through at least
  one real transport, with invocation replay and the refusal envelope
  exercised on both.
- **The reproduction** (§8) is the integration measurement and is run by
  hand on a bubblewrap host; it is not a test in the suite.

## 8. The measurement

### 8.1 What is done

On a host where `host_prerequisites()` is `None`, over a fresh world root,
corpus root and store on a certified volume beside the main checkout
(gitignored, as the record's `.mm30-reproduction/` is): the operator recipe
(§8.2), then the path of §3 through `science mcp serve` driven by a coding
agent, with the CLI used for at least one step to exercise both surfaces.
Predictions are written before the run, in the record's §5 discipline, and
every refusal is classified `design-gap`, `corpus-work`, `defect` or
`closed`, filed through the owning lane.

### 8.2 The operator recipe

The driver's step 1, as a library: `init_world_root`, `init_corpus_root`,
`init_store_root`; the concept list's content address computed and written
into `mm30.yaml`, with the stage-level, measure and identification lists
beside it (amended 2026-09-23: the kernel's own successor document binds
four lists and declares the `estimands:` row for
`affects-concept-molecular-entity`; the surface's document is authored
`lineage: genesis` with the same sorts, row and bindings, since the loader
takes no predecessor, §5.2); `adopt_manifest(profile=pins)` and `World.admit(root,
provenance=Fresh())` under an authority the operator constructs. The recipe
is recorded verbatim in the record, and the layer design's ruling that these
are operator-time library operations is restated there.

### 8.3 What is compared to the oracle

| record value | oracle | expected |
|---|---|---|
| proposition id | `proposition:concept-disease-stage-affects-protein-phf19` | equal |
| claim identity | `780ace5964c8ab83…` (the record's 2026-09-08 measurement, which replaced `5e702bc43fdf51d3…`) | equal — the claim names the sorted operator `mm30/affects-concept-molecular-entity` under the biology pack, as the re-run did; the 2026-09-05 identity named `mm30-reproduction/affects` under the unsorted vocabulary and is not the target |
| expression dataset address | `dataset:sha256:a6bf229e…` | equal — same bytes |
| concept list digest | `sha256:c7e45f81…` | equal |
| spec draft fields | the record's step 4 draft | equal for `method`, `assumptions`, `falsification`, inputs, rules and parameters; the prose estimand and applicability are replaced by the typed estimand the kernel's current driver builds (levels `ndmm`→positive level on slot 0, `rna-seq-tpm` additive, reference 0, observational, unconditioned; empty applicability) |
| spec identity | `86aaa1a8…` | **differs**, by the interpretation rule's kernel identity (§6.1) and by the typed estimand; stated, not papered over |
| assessment outcome | `inconclusive` | equal on the same host and data |
| verification scope and verdict | `clean-environment`, `passed` | equal on a bubblewrap host |
| belief | `NoBelief(no-eligible-assessment)` | **`NoBelief(no-directional-outcome)`**: the identity gap closed (`beliefs-ae9b18`), so admission succeeds and the frozen rule's `inconclusive` gives the scientific answer the record said it never reached |

The last row is the criterion: admitted to a computed belief. That the
belief is `NoBelief` is the data's answer under this rule, and the record
predicted it.

### 8.4 What the record leaves

`docs/records/2026-<date>-mm30-through-the-commands.md` in this repository,
in the reproduction record's shape: preflight, the path table with what each
command minted, predictions, findings, authoring cost, driver corrections
(here: surface corrections), what the run does not claim. Findings become
tasks through their owning lanes. The record closes `sci-66b26d`'s first
half and re-ranks nothing itself; a re-rank is the roadmap's.

## 9. Alternatives rejected

- **One spec for the dozen.** Rejected by ruling 1.
- **Continuing the record's corpus.** Rejected by ruling 2: it would carry
  the driver's compromises into the surface's first measurement and leave
  `claim` and `dataset` unmeasured.
- **Freezing inside `run`.** Rejected by ruling 3.
- **A rule library in the surface.** Rejected by ruling 4: the audit
  recomputes in the kernel and cannot resolve a rule the surface owns —
  the record's step 10b gap, made permanent.
- **Contracts as a stored record kind, now.** Rejected by ruling 5 as
  ordering: it is where the kernel is headed, and the criterion does not
  wait for it.
- **A `science init` framework verb** for world, corpus and store setup.
  Rejected by ruling 8: it would construct the full permit `science` may not
  hold. If the operator recipe proves to be the path's real cost, the fix
  is a framework amendment defining lifecycle ledger evidence, not a verb.
- **A `run` that also assesses.** Rejected: the assessment is its own
  governed record with its own rule, and a run that failed to assess would
  have to be either rolled back (the kernel has no such act) or left
  half-reported.
- **`belief` folded into `next`.** Rejected: `next` ranks; the criterion
  asks for one proposition's answer with its reason, and a ranking row is
  not that.
- **Threading the session authority into the run and holdings boundaries
  from the surface.** Rejected by framework §4.2: the surface never sees a
  permit. Hence §6.2.

## 10. Task mapping

`sci-66b26d` is the goal; it depends on `beliefs-e5ab34` (§6.1),
`beliefs-2d9a55` and `beliefs-5fe2e3` (§6.2), so it leaves `ready` until all
three close. The plan
attaches to it and adds one child per task, in dependency order: the
dispatcher amendment (§6.3); configuration and the read context (§5);
`claim`; `dataset`; `spec`;
`run`; `assess`; `verify`; `belief`; `next`; transport equivalence; the
measurement and its record (§8), which closes the first half. The
coordination set's spec follows the record, informed by it.
