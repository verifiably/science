# Conformance cut 5 — the family adapters

**Status:** Frozen 2026-08-19; second reader discharged; post-freeze feasibility
corrections recorded 2026-08-19.

**Sources:** `2026-08-17-conformance-cut-4.md`; the family-adapter design
`2026-08-19-family-adapters-design.md` §8; and the
frozen S, G, M, T, R, and C rows quoted below.

## 1. What this cut is

Cut 5 is the frozen acceptance boundary for the supersede/revise, retraction,
and explicit-import families at Science's certified composition root. It
selected obligations before their implementation. At freeze, no adapter or test
was claimed to exist; banking froze the selection after §6's independent
reading.

The selection rule is cut 4's rule, made deliberately conservative: a clause is
selected only when its source mutation and every named check run entirely
inside §2. A row is **full** only when cut 5 runs every arm in its frozen cell;
one unrun arm makes it **part**, even when a prior cut already exercised that
arm or an argument says that it should not count. A row with no cut-5 arm is
**deferred**. Prior-cut evidence remains evidence, but it is not silently
relabelled as cut-5 selection.

## 2. The boundary

In scope:

- the proposition-only `supersede` and `revise` families, including the
  adapter-owned `supersedes` edge and the exact prose revision allowlist;
- the controlled `retract` family, stored immutable retraction records, local
  target and route resolution, counter-retraction chains, and corpus-local
  standing;
- one-bundle explicit import: intent append, whole-bundle validation over the
  bundle union the local corpus, one payload transaction, and a separately
  stored boundary-minted act-report fulfilling the intent;
- one process-global operation-lock registry keyed by resolved corpus root,
  held across read, refusal, planning, and execution for every writer entry
  point;
- the optional uncovered `display.display_statement` proposition facet;
- the stored `retraction` and `act-report` kinds and their controlled
  constructors;
- the read-side `superseded_by` and `standing_in_local_view` evaluators and the
  corpus-local integrity findings for the new raw-write shapes; and
- a cut-5 acceptance runner over the certified engine tuple. Portable tests
  remain portable; a selected durable arm errors rather than skips when that
  tuple is unavailable or fails.

Out of scope:

- the **world index**, including corpus identities, cross-corpus resolution,
  the global retraction map, and authoritative world standing;
- the global **audit** and every clause whose detector is audit-only;
- the managed **holdings root** and mount/unmount semantics;
- **anchor acts**, anchored observer sets, and Science-side tamper-log
  verification;
- **consolidate**, **move/rename**, and **deletion** operations;
- the **rules store and resolver**; and
- the **registry compile**.

The local standing name is load-bearing: no selected clause may substitute
`standing_in_local_view` for a world-standing claim. Raw filesystem writes may
construct negative fixtures, but they are not family operations and do not make
audit, move, or deletion part of the slice.

## 3. The selection, against the frozen rows

The code blocks preserve each source row verbatim. The bullets immediately
after each block are the cut-5 split. **Selected** bullets are the complete arm
inventory that Task 16's N2 declarations must enumerate; **prior** bullets are
not selected again; every **deferred** bullet names its unblocker.

### 3.1 Supersede and revise

#### S2 — full

```markdown
| **S2** | A semantic edit through the write API mints a new proposition | Science | edit scope via API; assert new node, `supersedes` edge, prior refs unmoved |
```

- **Selected:** through `supersede`, change proposition semantic scope and
  assert a fresh proposition, exactly one adapter-authored `supersedes` edge,
  and every prior reference still bound to the predecessor.

#### S4 — full

```markdown
| **S4** | `nodes.rename` is never used for a semantic change | Science | assert no rename path is reachable from the semantic-change branch |
```

- **Selected:** assert that the semantic-change branch reaches no
  `nodes.rename` path. Supersession is create-only; revision is same-address
  replacement and refuses semantic change.

#### G7 — full

```markdown
| **G7** | A semantic edit to a proposition cannot retarget existing evidence | Edit a proposition's scope in place; assert a new semantic identity is minted, that prior assessments still bind the old one, and that belief on the old identity is unchanged. **Also assert the converse, in both prose forms** (second form added 2026-08-05, ρA1/ρA2): overwrite `title` alone, and separately overwrite `display_statement` alone, and assert in each case *no* mint, no new node, and an unchanged digest — pinning that the split of §4.1 is real in both directions and that display edits stay free. The positive arm is unchanged and **strengthens** under the typed projection: it forked identity only when prose moved the hash, and now forks whenever a typed field differs |
```

- **Selected:** edit proposition scope; assert a new semantic identity, prior
  assessments still bound to the predecessor, and unchanged belief on that
  predecessor.
- **Selected:** overwrite `title` alone through `revise`; assert no mint, no new
  node, and an unchanged semantic digest.
- **Selected:** overwrite `display_statement` alone through `revise`; assert the
  same no-mint, no-new-node, unchanged-digest result. The positive typed-field
  strengthening is exercised by the scope edit.

#### M5 — part

```markdown
| **M5** | **Qualification participates in claim identity** | Two claims differing **only** in a restriction identifier → different `I_claim`; differing **only** in quantifier tag → different; one carrying a dimension the other omits → different. Then the founding case end to end: mint kernel §4.1's *"in adults"* claim, assess it, "edit" to *"in all humans"*, and assert a **new** identity, the prior assessment still bound to the old one, and a `supersedes` link. **Sabotage:** drop the qualifier map from `π_claim` and assert the founding case **collapses to one identity** — the row's whole point. **Negative:** re-serialize the qualifier map with keys in a different order and assert the identity is **unchanged** |
```

- **Selected:** the founding case end to end: mint and assess *in adults*,
  supersede it with *in all humans*, and assert the new identity, the prior
  assessment still bound to the predecessor, and the `supersedes` edge.
- **Prior, not selected again:** restriction-only, quantifier-only, and
  present-versus-absent qualification identity; dropping the qualifier map; and
  qualifier-key order. Cut 1 exercised these clauses. Because cut 5 does not
  run them, M5 is part rather than full.

### 3.2 Explicit import

#### S3 — full

```markdown
| **S3** | A stale semantic hash is rejected on import | Science | hand-edit fields only; assert refusal. **Negative:** edit fields *and* hash; assert it passes undetected, pinning §4.3 |
```

- **Selected:** hand-edit semantic fields without changing the stored stamp and
  assert explicit import refuses the stale stamp before any payload write.
- **Selected:** hand-edit both the semantic fields and stamp consistently and
  assert explicit import admits it undetected, preserving §4.3's limit. The
  fixture is a record with no independently forged derivation for another
  selected validator to reject.

#### T1 — part

```markdown
| **T1** | Only the boundary mints an act-report | Attempt to author one through every construction path — direct authoring, and any API taking report fields as input; assert no such path exists. Explicitly import another observer's report and assert it enters **structurally validated, not operation-authenticated, attributed, and inert** — nothing derivable exists to recompute, and no validation state is written. **Negative:** raw-write a self-consistent report; assert it is not detected on read, and that an audit detects it **only with the tamper log implemented and a valid anchored observer set** — otherwise the raw write remains undetectable, and the design text claims no more |
```

- **Selected:** explicitly import another observer's act-report and assert it
  enters structurally validated, not operation-authenticated, attributed, and
  inert; nothing derivable is recomputed and no validation state is stored.
- **Prior, not selected again:** the ordinary-API/direct-authoring prohibition
  selected by cut 3. The family-owned-kind reservation is implementation support
  for that standing claim, not a new cut-5 arm.
- **Deferred:** the raw-write negative's audit detection waits on the **audit**;
  its conditional tamper-log detection waits on **anchor acts and a valid
  anchored observer set**.

#### T2 — part

```markdown
| **T2** | One started operation, one intent, one terminal record — and no act precedes the intent | Run each operation kind to success; assert exactly one qualifying fulfillment: the `run` where one is minted, the act-report otherwise. **Positive:** a post-intent attempt that mints no run closes through **exactly one** qualifying act-report. Attempt a second fulfilling registration on one intent → **malformed**, the log's rule as built. Make root selection fail, then the intent append fail; assert in each case **no act began** — no request issued, no lease taken, **no record minted** (an `event_token` generated in memory and carried by no intent and no record is not a mint). **Negative (a):** a missing-spec run request refuses **pre-intent**; assert a surviving boundary publishes an *unfulfilling* act-report, that it fulfills nothing, and that a crash there leaves no trace. **Negative (b):** a complete non-conforming execution mints a **run**, never an act-report. **Negative (c):** a dataset-production attempt opens the **operation intent** — assert the assessment-run intent cannot be spelled without a `spec_identity` |
```

- **Selected:** for a successful import, assert one started operation, exactly
  one intent, exactly one qualifying terminal act-report fulfillment, and no
  payload act before the intent.
- **Selected:** for a post-intent import refusal that mints no run, assert exactly
  one qualifying refusal report closes the intent and no payload is written.
- **Selected:** make intent append fail; assert no payload or report act began
  and no record was minted.
- **Deferred:** root-selection failure belongs to the **boundary that selects a
  corpus root**, before an already-rooted `CorpusWriter`; success for every
  other operation kind, the missing-spec run request and its unfulfilling
  report/crash clause, and the complete non-conforming execution remain with
  their respective **run, acquisition, audit, and other operation-family
  cuts**. Pre-intent request validation is an implementation promise, not a
  substitute frozen arm. Dataset-production's typed intent shape is prior cut-3
  standing, not selected again.
- **Deferred:** second-fulfillment classification waits on a durable-log
  consumer/classifier. The current port and engine treat `fulfills` as opaque
  and append both registrations; counting them in a test does not classify the
  history.

#### M3 — part

```markdown
| **M3** | **`standing` terminates, because the retraction graph is a DAG** | **Termination itself, on valid states:** evaluate `standing` over retraction chains of increasing depth, including counter-retractions and several standing retractions of one target, and assert termination and a stable value. Without this arm a looping implementation passes while its validator is perfectly correct. **The validator, exercised directly** — the only arm that can certify the check exists: hand it an abstract two-cycle and assert a **cycle-specific** result carrying a **witness** (the offending edge set), not a generic failure. Case-split the cycle across the boundary that matters — both records in the **bundle**, and one record in the bundle closing a cycle through the **resolved world context** — and assert import invokes the validator on the **union**, never on the bundle alone. **That import consumes the result:** force a cycle verdict for an otherwise entirely valid bundle and assert the import **refuses with no write**; an importer that calls the validator and ignores its witness must fail this arm. **Ordinary writes:** attempt a retraction whose target does not already resolve and assert refusal (C10), which is what makes a write incapable of closing a cycle. **Merge's two arms, restated onto its successors 2026-08-08 (`2026-08-08-world-address-ruling.md` §5; ρA10):** the distinct-basis arm becomes **unspellable rather than refused** — assert **no operation exists** that merges two distinct-basis retractions, which is stronger than the refusal this arm banked, and assert instead that a `coreference-attestation` over them leaves both retraction records **byte-unchanged** and closes **no cycle** (**W15**). The equal-basis arm keeps its shape under its new name: `consolidate` two **equal-basis** replicas of one retraction held in two corpora **while a counter-retraction `R` already targets it**, and assert it **succeeds**, that the retraction's content identity is **unchanged**, and that `R` is **not rewritten and not re-minted** — now true by construction, since `consolidate` requires one canonical address and performs no inbound rewrite (**W16**). World §4.3's `duplicate location` state has no other resolution. **Raw writes:** a cyclic configuration is classified **malformed by audit before any standing or belief evaluation** — assert no reading is invoked on it (§3.3, `Ω_valid`). **Explicitly not the test:** refusing a hand-written cyclic *pair* certifies nothing. Each retraction's content-derived address already includes its target identity, so such a pair fails **identity recomputation** on its own, and a generic "import refused" passes whether or not any acyclicity validation exists. That fixture is circular evidence, and an earlier draft of this row used it. **Negative:** no topological rank is stored anywhere; re-evaluate the same state after admitting records in a different order and assert every identity and `belief_input_digest` is unchanged |
```

Exactly four arms are selected:

- **Selected:** evaluate `standing_in_local_view` over an admissible local DAG
  with increasing-depth chains, counter-retractions, and sibling retractions;
  assert termination and a stable value.
- **Selected:** invoke the validator directly on an abstract cycle and require a
  cycle-specific result carrying the offending edge set as witness.
- **Selected:** force the cycle verdict for an otherwise valid bundle and assert
  import consumes it, refuses, and performs no payload write.
- **Selected:** attempt an ordinary retraction write whose target does not
  already resolve and assert C10 refusal; this is C10's termination role.

- **Deferred:** the distinct-basis coreference-attestation arm waits on the
  **world index/coreference surface**; the equal-basis replica arm waits on
  **consolidate and the world index**; raw-written-cycle classification waits on
  the global **audit**; and the admission-order/no-stored-rank negative waits on
  a later **M3 completion cut**. Those unrun clauses keep M3 part.
- **Deferred:** the bundle-only and bundle-plus-local concrete cycle arms wait
  on a spellable controlled identity construction. A controlled retraction's
  content identity hashes its target identity, so a cyclic pair requires a
  circular fixed point. Raw forged pairs instead fail controlled-shape
  validation and are the frozen row's explicitly forbidden non-test.

#### R19 — deferred

```markdown
| **R19** | Verification derivation is validated at explicit import and under audit, and neither mounting nor a raw write is an epistemic event (§7.3c) | Assert the constructor's arguments are **ordered run refs, an optional certification, and the explicitly selected contract identity and epoch (5b §7.6), and nothing else**: attempt to pass a comparison report, a conformance result, a boundary receipt, an **equivalence-rule evaluator**, or an **implementation selection** and assert no such parameter exists. Assert the evaluator's **identity** is resolved from the **original run's frozen spec** and its **implementation** from the run's frozen `rule_bindings` (5b §6), and that a **mixed-shape** pair is refused. **Explicit import, inputs resolvable:** hand a `verification` with a fabricated report, a chosen `scope` and `verdict`, and an address computed to agree with them to the **import operation** — the untrusted-import case substrate §4.2 says passes stale-hash and corpus checks — and assert the import is **refused before any write**, and that no file exists afterwards. Assert an import whose inputs do **not** resolve **proceeds** and emits an **import finding**, and that **no validation state is written onto the verification** in either case — the record is immutable and gains no `validated` field. Assert the recomputation resolves **across corpora** through the world resolver, and that a verification whose runs live in a different corpus is **not** refused for that reason alone. Do the same for an `analysis-spec` whose `stochastic-unseeded` contract accompanies a bitwise `equivalence_rule`. **Both transitions, which is the point of this row:** **(a) genuine, available → unavailable** — record a `passed` verification under a declared **tolerance**, make its artifacts unreachable here while they remain **held elsewhere**, and assert it is **not refused**, admission is **unchanged**, and no `inconclusive` is recorded; **(b) forged, unavailable → available** — import a self-consistent forged verification whose artifacts do **not** resolve (so it enters unvalidated and admits), then **mount them**, and assert admission is **still unchanged** until an **audit** runs, that the audit emits the contradiction finding and **mints nothing** (amended 2026-08-03, 5b §7.6), that a separate explicit constructor act naming its own cut and epoch mints the **superseding verification** carrying the correct derivation, and that admission changes **because of that node**, never as a side effect of the mount or of the audit alone. Assert reading the record at any point in either transition validates nothing. **Negative (c) — availability is not an epistemic result:** assert an unvalidated verification is neither certified sound nor treated as non-admitting; where its inputs cannot be resolved anywhere in the world, assert belief is **not computable**, never a silently unchanged or lowered value. **Negative (d) — the import boundary is an operation, not a directory:** write the same forged verification straight into a corpus path with a raw filesystem call, bypassing the import operation entirely; assert it is **not** refused, that **reloading the corpus does not validate it** at any point, and that it is caught **only** when an audit runs — pinning that "validate on import" is a claim about Science's operations and never about files appearing on disk. **Negative (e):** assert a raw-written *run* whose internal hashes agree is **still** not detected, and that an unaudited self-consistent verification is **not** distinguishable from a genuine one — both are substrate §4.3's limitation and need §9's log; this test must not be read as closing either *(Amended 2026-08-11, the act-report design §4: the constructor's closed list gains one member — the optional report-position citation. Every other extra argument is still refused, deleting the cited report invalidates nothing, and the audit arm is unchanged: the evaluator mints nothing, its finding recorded as an entry in the boundary wrapper's inert act-report.)* |
```

- **Prior, not selected again:** the constructor/evaluator-shape clauses and cut
  4's local durable-read availability and raw-write clauses.
- **Deferred:** explicit-import derivation validation requires the original and
  replayed `RunClosure` values, their results, comparison evidence, frozen
  specifications, and callable equivalence-rule implementations. Persisted
  runs and verifications and `import_bundle(Sequence[Node])` carry none of that
  complete evidence. Cross-corpus recomputation and the different-corpus
  negative also wait on the **world index**; availability transitions and
  world-wide computability wait on the **world index and holdings root**;
  contradiction discovery and the superseding constructor act wait on the
  **audit**; log-backed raw-write detection waits on **anchor acts**.

#### R20 — part

```markdown
| **R20** | The nondeterminism contract cannot contradict itself, and stream totality reaches both records (§3.1a, §6.2) | Attempt to freeze a spec that is `deterministic` **with** a seed plan, `stochastic-unseeded` **with** a seed plan, and `seeded` **without** one; assert each is **unspellable** — refused by the union, not by a validator. Attempt a `seeded` plan with multiple roots and **no total stream-to-root mapping**; assert refusal, since the derivation has no determined root argument. Assert `stochastic-unseeded` **is** freezable when it carries a rationale — an honest declaration is not an error. **Negative (a):** assert `stochastic-unseeded` alongside a **bitwise** `equivalence_rule` is caught at **freeze time** *and* on **import** (§7.3c), and assert this one is a **check** rather than a type refusal, since it spans two fields. **Negative (b) — totality reaches the occurrence:** declare two streams over two roots, then attempt to record realized seeds keyed by **job alone**; assert the occurrence **cannot represent it** and the run is refused, pinning that a plan naming two roots is not satisfiable by a record with one slot. **Negative (c) — the *obligation* is per family, though the *declaration* is global:** assert the spec **does** hold one global set of logical streams — that is correct and required for the equality check — while **no global per-job obligation is spellable**, so an honest record in which different families realize different streams **conforms**. Pin that no conformance rule here is satisfiable only by a job claiming streams it did not use. **Negative (d) — no topology in the spec:** assert the frozen spec names **logical streams only**, that **no workflow rule or process name can be spelled in it**, and that stream identities name **analytical roles** (`model-initialization`, `resample-draws`) rather than **libraries** — assert a spec built around `numpy-rng` and `torch-rng` fails review for the same reason a rule name would, since a reimplementation in another framework draws the same analytical randomness elsewhere. Then build two implementations of one spec with **different rule decompositions**, and assert both carry the **same `spec_identity`** and can be compared under `independent-implementation` — pinning that a family-named field in the spec would have made that scope row unreachable for every seeded spec |
```

- **Selected:** the import half of negative (a): a locally checkable
  `stochastic-unseeded` spec paired with a bitwise equivalence rule is refused
  before payload write, as a cross-field check rather than a union type refusal.
- **Prior, not selected again:** the union spellability, freeze-time, occurrence
  totality, and frozen logical-stream clauses selected by cut 3.
- **Deferred:** per-family workflow obligations and the two-decomposition
  comparison wait on the **full workflow surface**.

#### R22 — deferred

```markdown
| **R22** | The assessment facet is derived from the run through the ordinary API (§3.1b, §5.1, kernel §4.2.1) | Assert the assessment constructor takes **only a run ref** — attempt to pass `outcome`, `estimate`, `uncertainty`, `estimand`, `applicability` or `interpretation_rule` and assert **no such parameter exists**. Run an analysis whose result the frozen `interpretation_rule` maps to **`refuted`**, and assert no API path produces an assessment carrying `supported`; assert the derived `outcome` changes only when the **result** or the **rule** changes. Assert `estimand` and `applicability` are **copied by the constructor** from the frozen spec, and that `proposition` comes from the spec's `target`. **Evaluator failure (§3.1b):** make the rule's evaluator fail — unreadable output, unparseable payload, missing rule implementation — and assert **no assessment is produced** and a finding is recorded; assert `inconclusive` is **not** produced, since it is a scientific outcome and machinery failure is not one. **Negative (a):** assert narrowing `applicability` after seeing the result requires a **successor spec and a new run**. **Negative (b) — no revisions, but the values are still hashed:** assert there is **no edit** that changes a facet and leaves the same assessment, and that the world basis `(spec, run, proposition)` is the constructor's own argument set. Then assert **G3 digests keyed facets** — sorted `(assessment identity, facet digest)` pairs — with **both** halves tested, since two consecutive revisions each dropped one: raw-write an assessment at the correct address carrying `supported` where the derivation yields `refuted` and assert the **belief digest differs** from the correct state's (which hashing identities alone would have missed); then **exchange the facets of two assessments** on one proposition, over different runs and different lineages, and assert the belief digest **differs** (which hashing a bag of facet digests alone would have missed, the multiset being unchanged). Assert the second state can aggregate to a different belief, so the digest is not merely being pedantic. Assert this is **change detection, not truth detection**. **Reach:** execute one recipe, then execute a second differing **only** by an inline exclusion certification (§5.2), so the two assessments carry **byte-identical facet values**; assert the belief digest differs. Assert that editing the certification alone changes **no** belief digest, because it mints a recipe and no run. **Rule binding (§3.1b):** assert a spec naming an `interpretation_rule` that resolves to neither a held implementation nor a registry entry with fixtures is **refused**, and that an implementation failing its fixtures **is not that rule**. **Negative (c) — the API is not the world:** hand-write an assessment file with a fabricated facet straight into a corpus path; assert it is **not** refused and **not** detected on read, that **explicit import** recomputes the facet from the run and **refuses** a mismatch, and that a raw-written one is caught **only under audit** — the §7.3c limitation, unchanged, and read-time validation would violate R5 |
```

- **Prior, not selected again:** the constructor, derivation, supplied-rule,
  keyed-facet, at-the-address raw-write, and read-side nondetection clauses
  selected by cuts 3 and 4.
- **Deferred:** explicit-import outcome recomputation requires a complete
  `RunClosure` result, its frozen specification, and a callable interpretation
  implementation. Persisted runs and assessments and
  `import_bundle(Sequence[Node])` omit those inputs. Resolving an interpretation
  rule waits on the **rules store and resolver**; catching a raw-written
  assessment waits on the global **audit**.

#### R23 — deferred

```markdown
| **R23** | A produced dataset, its ancestry and its durable basis are minted by the boundary (§5.2) | Assert the output dataset's address is the **dataset basis projection over the output manifest's content identities** — deduplicated, sorted, digested (admission ramp §6.2; *amended 2026-08-09, this read "the single output entry's content identity", which a uniform projection cannot return for a one-entry manifest without a cardinality special case inside an identity function*) — and that the run's **`produces`** edge is emitted with the run; attempt to attach `produces` naming a dataset the manifest did **not** emit, and assert the ordinary API offers no such path. Assert **no `produced_by` edge exists in either direction of the API** — the retired representation must not be reachable. **Negative (a) — no nominal handle in identity:** emit byte-identical output under two different **logical names** and assert **one** dataset address results — pinning that the address is not the manifest digest, which carries the name. Assert `derived_from` **resolves as a view** over `produces ∘ transforms`, is **not stored**, and is **not read by independence** — which walks the stamped basis — and that no authored ancestry list is accepted. **Negative (b) — the independence multiplier:** construct two runs sharing an upstream dataset and omit it from one's ancestry in a build that permits authoring; assert the omission **would** make the two assessments read as independent under kernel §4.2.1's disjoint-closure rule, then assert the derived form makes it unspellable. **Negative (c) — omission survives derivation:** classify a shared **empirical** input as auxiliary `reads` **without certification**; assert the closure is **incomplete** and independence is **`not-certified`**, never assumed — pinning that deriving the edge did not make the classification honest. Assert a **certified** exclusion does remove the input from the closure, that the certification is **inline on the `reads` entry** with a rationale and attribution, and that adding or withdrawing it **mints a different recipe** — then assert it mints **no run**, and that the original run is unchanged, until that recipe is **executed**. **Then assert both limits:** a *false* certification still omits the edge and still inflates belief — the guarantee is attribution, not truth; and after a corrected re-execution, assert the **original run and its false certification are still active belief inputs**, with no API path that retires either, pinning §11.13 rather than letting attribution be read as correction. **Replay cardinality:** replay a `dataset-production` run successfully and assert **one dataset address with two `produces` edges from two runs**; assert the lineage view composes over both, and that **no existing dataset node was mutated** to record either — including that the pre-existing dataset's **lineage basis is unchanged** and still names the first run. **Deletion, which the view alone cannot see:** stamp the basis, then **delete the producing run**; assert the dataset does **not** read as a root, that the unresolved basis entry emits **`lineage-incomplete`**, that independence over it is **`not-certified`**, and that kernel §5.1's belief digest **moves** — asserting the stored ref and its `null` resolution are recorded **separately**, since recording either alone loses the deletion. Assert the same for a deleted **ancestor**. Assert a *second* surviving run producing the same address by another route does **not** repair the first basis. **Negative (e) — divergence, not union and not silence:** have `R1` mint `D` from `A`, stamping the basis, then have `R2` produce byte-identical `D` from `B`. Assert independence over `D` becomes **`not-certified`** with a **`lineage-divergent`** finding — not silently unioned into ancestry, which the single basis cannot make durable, and not silently ignored, which would certify `D` independent of `B`-derived evidence while a derivation from `B` demonstrably exists. Assert kernel §5.1's belief digest **moves** when `R2` is added, pinning that the snapshot covers the **producer set** and not only the basis. **Coverage (§11.15):** enumerate producers from a **producer snapshot** whose coverage omits `R2`'s corpus and assert the digest **differs** from the full-coverage one even though every *present* corpus is identical; then make `R2`'s corpus absent **within** coverage and assert `not-present` rather than a silent undiverged reading. **Negative — location is not evidence:** move a dataset between corpora and edit an alias, and assert the belief digest is **unchanged** (world W5) — pinning that the member is the snapshot and not the whole index. **Derivation, not just hashing:** delete `R2`'s entry from a valid snapshot, leave its coverage and receipt intact, and hand it to **explicit import**; assert it is **refused** because rebuilding from the receipt's corpus states does not reproduce the map, that a snapshot carrying **no receipt** is refused as unrecomputable and that a receipt naming corpora rather than **exact states**, or naming a bare version string rather than a fixture-bound rule identity, evaluates to **`malformed`** — refused at import, and returned as `malformed` rather than `unresolvable` by an **audit** that meets one raw-written, since no arriving corpus or rule could ever make it checkable (world §5, W8a). Assert a snapshot whose receipts are **all malformed** is **`unchecked`**, never `contradicted`, with a malformed finding per pair. Assert a fabricated snapshot written straight into place is caught **only under audit** — never on read, which would violate R5. Assert the third case is **not** a refusal: a receipt naming exact states whose **corpora are absent here** imports with a **finding**, writes no validation state, and is checked by a later audit (world §5) — "cannot be checked here" is `not-present`, not `unknown`. Assert a receipt whose covered corpus has **moved to a new state** is likewise **unresolvable** rather than refuted, so a snapshot's completeness evidence is checkable only while the receipt is **`resolvable`** — **each** covered corpus at its own recorded state (world §5, limitation 10). **Two corpora:** make one of two covered corpora move while the other stands still, and assert the receipt is **unresolvable** — one corpus cannot satisfy the other's entry. **The rule is a receipt member too:** mutate the receipt's `producer_snapshot_rule_identity` and assert the **receipt identity moves** while the snapshot's semantic identity and the belief digest do **not**; then install a newer enumeration rule beside the old and assert the receipt **still validates**, stop holding the old rule and assert **`unresolvable`** rather than refuted, and assert a rule whose implementation fails its fixtures **is not that rule** (world W8a). **Negative — the receipt is not a belief input:** move a dataset between two covered corpora, so **both** corpus-state identities in the receipt change while the producers map does not; assert the belief digest is **unchanged**, pinning that exact states sit outside the semantic identity and that the completeness mechanism did not smuggle location back in. **Then assert the residue (§11.14):** delete `R2` and assert certification is **restored** and the resulting state is **indistinguishable** from one where `R2` never existed — no retained prior digest, since belief is a computed view; assert specifically that **no** test can distinguish them, rather than asserting a difference the design cannot deliver. **Merge and the tagged basis (world §4.3):** assert a boundary-minted basis is always **`single`**, and that the **only** transition to `conflict` is a merge of records whose routes differ. Merge two records at one content address with different routes; assert the survivor carries `conflict([both], sorted)`, that no field-selection path chooses between them and **no ordinary API removes a route**, that the dataset is `lineage-divergent` with independence `not-certified`, and — unlike the deletion case — that the conflict **survives** deleting either producing run. Assert merging two `conflict`s **unions** their routes. Assert the traversal over a `conflict` resolves **every** route's refs and certifies nothing, and that divergence is decided on the **tag** before any comparison — no `transforms`-versus-basis comparison is attempted against a set. **Valid state:** assert `conflict` with **fewer than two distinct routes is unconstructible**, so a conflict that never occurred cannot be spelled and there is one representation per fact. **Lifecycle:** assert **no** API resolves a conflict — none retires a route, chooses between two, or records one as wrong — so the state is permanent under this design (§11.13's missing correction lifecycle, reached from another direction). **Then assert two limits, which are not one limit:** a raw filesystem edit *can* drop a route or forge a `single`, and the API guarantee does not reach the filesystem (§11.11) — with `B`'s producing run still present, assert an **audit detects** the forged `single(A)`, since recomputation still has `B` to contradict it. **Then delete `B`'s producing run as well** and assert the audit reports **nothing**: every surviving route resolves and no record of `B` remains. Assert specifically that **no test distinguishes** that corpus from one in which the conflict never arose, rather than asserting a detection the design cannot deliver — the composite of §11.11 and §11.14, where R23 previously claimed a route's removal was always caught while the row above it said no path removes one. **Negative (f) — the replay case is not divergent:** replay `R1`'s recipe; assert the second producer's `transforms` set **equals** the basis, that **no** divergence is reported, and that independence stays certified — pinning that the divergence rule does not fire on the case §5.3 is built to reach. **Negative (g) — self-edges:** run an identity transform that transforms and produces one content identity; assert the run is **valid**, that **no** `D derived_from D` edge appears in the view, that the closure is **not** reported as cyclic, and that the run is **not** divergent — then assert a genuine two-node cycle **is** reported. **Negative (h):** assert an input's role is fixed in the recipe before execution, so reclassifying it mints a **different recipe**, and a different run only on execution; and assert a raw-written lineage basis is caught only under audit, as in R22 |
```

- **Prior, not selected again:** boundary-minted dataset/`produces` shape,
  replay cardinality, inline exclusion mechanics, and cut 4's corpus-local
  `derived_from` view and basis/composition reading.
- **Deferred:** the local basis/composition disagreement clause's frozen source
  mutation is a second dataset-production run, not explicit import; it waits on
  that **operation-family boundary** rather than being respelled as import
  behavior. The row's actual explicit-import clauses concern producer snapshots
  and receipts and therefore wait on the **world index and rules store**. Global
  producer completeness, coverage, cross-corpus divergence, and independence
  also wait on the **world index**; correction of active false routes waits on
  **retraction coverage/world standing**; every move, consolidate, and deletion
  clause waits on those named **family surfaces**; and raw-written-basis
  detection waits on the **audit**.

### 3.3 Retraction

#### C1 — full

```markdown
| C1 | Retraction is additive: the target is byte-identical and still resolvable after | retract; assert target bytes, address, and resolution unchanged; assert no API edits or deletes a target |
```

- **Selected:** retract through the controlled create-only family; assert the
  target's bytes, address, and local resolution are unchanged, and assert no
  family API edits or deletes the target.

#### C2 — full

```markdown
| C2 | Attribution, reason, and ground are required at the boundary | submit a retraction missing each in turn; assert refusal with no file written |
```

- **Selected:** omit actor/event attribution, typed reason/rationale, and grounds
  in turn; each construction or boundary attempt refuses with no file written.

#### C3 — part

```markdown
| C3 | The digest covers the retraction enumeration — refs, resolutions, and coverage declaration; never exact corpus states | retract an in-closure, in-coverage input → digest moves; input outside the closure → unchanged; **standing retraction in an uncovered corpus → digest unchanged, and the coverage declaration is itself a digest member — the bound is visible, not silent**; **in-coverage corpus move (content identities unchanged) → digest unchanged, receipt records the new states** |
```

- **Selected:** in a supplied corpus-local closure, a local standing retraction
  of an in-closure input changes the digest; a retraction of an input outside the
  closure leaves it unchanged. The local enumeration's found refs and standing
  resolutions are the mutated digest members.
- **Deferred:** uncovered-corpus behavior and the coverage declaration wait on
  the **world index and global retraction map**; exact-state receipts and the
  move-invariance clause wait on the **world index and move surface**.

#### C4 — full

```markdown
| C4 | Subtraction is direction-free | retract a supporting assessment → support falls; retract a refuting one → support rises; assert both apply identically |
```

- **Selected:** using corpus-local standing, retract a supporting assessment and
  assert support falls; retract a refuting assessment and assert support rises.

#### C5 — full

```markdown
| C5 | Chain, not toggle — and standing is sibling-aware | retract, then counter-retract → admission equals the initial state while all three digests are pairwise distinct; **two sibling retractions of one target, counter-retract one → standing stays subtracted until the second is also counter-retracted** |
```

- **Selected:** retract then counter-retract; assert admission returns to the
  initial value while the three digest states remain pairwise distinct.
- **Selected:** create two sibling retractions, counter-retract one, and assert
  standing stays subtracted until the second is also counter-retracted.

#### C6 — part

```markdown
| C6 | Verification retraction recomputes admission fail-closed under amended G8 (§7a) | retract a false failing verification → admitted iff a standing passing one remains; retract the passing one → unadmitted; a passing *sibling* still clears nothing. **Negative (unchanged):** raw deletion of a verification still restores admission undetectably — kernel §8.7's bound stands, §8 |
```

- **Selected:** retract a false failing verification and assert admission returns
  iff a standing passing verification remains; retract that passing verification
  and assert de-admission; a passing sibling still clears no standing failure.
- **Deferred:** the raw-deletion negative remains the **deletion/history-limit
  cut's** fixture and is not selected as a sanctioned family operation.

#### C7 — deferred

```markdown
| C7 | Route retirement never selects silently | conflict of two routes: retire one → certifiable over the survivor; retire both → `not-certified`; assert stored basis facet unchanged throughout (route preservation) |
```

- **Deferred:** every clause requires effective-route standing over a conflict
  basis and certification after retirement. The node-only local standing
  evaluator cannot stand in for it. It waits on the **route-standing evaluator,
  conflict/merge semantics, and consolidate surface**.

#### C8 — deferred

```markdown
| C8 | A retracted snapshot is refused where recomputation already happens | import naming it refuses before any write; audit and diagnostic query report `retracted`; **negative:** mounting the corpus writes nothing and validates nothing |
```

- **Deferred:** the named target is a stored semantic snapshot, which this cut
  does not add; import and diagnostic enforcement wait on the **stored snapshot
  and snapshot evaluator**, audit reporting on the **audit**, and the mount
  negative on the **managed holdings root**.

#### C9 — deferred

```markdown
| C9 | Narrowing is snapshot succession plus retraction, never mutation behind an identity | derive the narrowed successor snapshot, retract the old naming it as `successor`; assert the old snapshot's identity and its receipts are byte-unchanged, a computation naming the old hits C8's refusal, one naming the new proceeds, and the digest moves. **Negative:** nothing resolves through the retraction to the successor implicitly |
```

- **Deferred:** the whole row waits on the **stored semantic-snapshot kind,
  snapshot succession/evaluator, and world-index-backed digest enumeration**.
  The informational `successor` field alone would make every behavioral clause
  vacuous.

#### C10 — part

```markdown
| C10 | Ineligible or ill-formed targets are unspellable through the boundary — and, since 2026-08-05, this is also what makes an ordinary write incapable of closing a cycle in the retraction graph (§4; formal model ρA9, M3). **The test below is unchanged**; the row gains a role it always played, not an arm | retraction naming a note, a proposition, a run → refused; **a `route` arm naming a route absent from the named dataset's stamped basis → malformed**; a retraction naming an `instrument-certification` → **eligible** (added 2026-08-03, normative-contract §7.2 — its standing is read by scope derivation); raw-write each refused case and assert the audit reports it |
```

- **Selected:** refuse node-arm targets of kind note, proposition, and run.
- **Selected:** refuse a route arm naming a route absent from the locally
  resolved dataset's stamped basis.
- **Deferred:** positive eligibility of an `instrument-certification` waits on
  its **stored kind and registry compile**; reporting raw-written refused cases
  waits on the global **audit**. Ordinary-write target resolution remains the
  single M3 declaration above; C10's frozen text says that termination role is
  not a new arm.

#### G2c — part

```markdown
| **G2c** | An assessment is admitted only in the **admitted** verification state | Walk every row of the §3.3 lifecycle table; assert admission only for `clean-environment, passed` with no active `failed`. Assert a passing sibling does **not** clear an active failure |
```

- **Selected:** the positive C6 retraction states: retract a false failing
  verification and admit only when a standing passing verification remains;
  retract the passing verification and de-admit. A passing sibling does not
  substitute for the standing retraction.
- **Prior, not selected again:** the rest of the lifecycle-table walk and the
  ordinary passing-sibling negative. Because cut 5 runs only the positive
  retraction addition, G2c is part.

#### G8 — part

```markdown
| **G8** | A later failing verification forces recomputation and, **while recorded**, clears only by explicit resolution **or a standing retraction** (bounded — §3.3, amended by correction-lifecycle §7a) | Attach a failing verification to an admitted assessment; assert invalidation and recomputation of every touched proposition. Assert it is **not** cleared by recency or by a passing sibling, **and is cleared by a standing retraction** (correction-lifecycle C6). **Also assert the negative:** delete the failing verification and confirm the assessment returns to admitted — pinning that deletion is §3.2's undetectable-history limit, not a tamper-evidence claim |
```

- **Selected:** a standing retraction of the active failing verification clears
  that failure and forces the affected admission/belief recomputation.
- **Prior, not selected again:** attaching the failure and refusing recency or a
  passing sibling as clearing paths.
- **Deferred:** the raw-deletion negative remains with the **deletion/history
  limit**, not the sanctioned retraction family.

## 4. Accounting

Cut 5 reads 24 frozen rows: **8 full + 10 part + 6 deferred = 24**.

| state | rows | n |
|---|---|---:|
| full | S2, S3, S4, G7, C1, C2, C4, C5 | 8 |
| part | M5, T1, T2, M3, R20, C3, C6, C10, G2c, G8 | 10 |
| deferred | R19, R22, R23, C7, C8, C9 | 6 |

This is row accounting, not a denominator of prose arms. Each **Selected**
bullet in §3 is one declaration unit for N2; a declaration may name a
parameterized mutation where the frozen cell itself does so. No row outside
these 24 is selected by cut 5, and no prior-cut arm is counted as new selection.

## 5. N2 and acceptance obligations

Task 16 owns cut 5's N2 declarations. It must declare every §3 **Selected**
bullet, and only those 28 bullets, as data with:

- its frozen row id and assertion;
- the exact source mutation, against real module text;
- every exact test or acceptance node that must fail under that mutation; and
- a verdict from the standing harness for `vacuous`, `stale`, `mixed`,
  `uncollected`, and class-node collapse.

The unsabotaged baseline must pass. A selected durable arm runs through the
cut-5 acceptance runner on the certified tuple; errors on that tuple are errors,
never skips. Portable arms remain in the portable suite. The cut-5 runner may
invoke cut 4 as a prefix, but neither `python/tools/cut4_acceptance.py` nor cut
4's meaning is edited.

N2 was prospective when this cut froze: the cut fixed the declaration inventory
but claimed no declaration, sabotage, or test existed yet.

## 6. The second reader

The independent reader received only the frozen rows quoted in §3, the
family-adapter specification, and §2's boundary; they were not asked to
preserve the draft's rationale. Their review attacked in the historically
common direction, toward overstated coverage.

The reader must:

1. check every selected clause and its exact source mutation against §2;
2. demote any clause that reaches the world index, global audit, holdings,
   anchor carriage, rules store, registry compile, or a deferred family;
3. reject any substitution of `standing_in_local_view` for world standing;
4. check the R19/R20/R22/R23 selection against §8's narrowing rule — a missing
   local validator narrows the selection rather than expanding the validator's
   promise; and
5. rederive §4 and the §5 declaration inventory independently.

### 6.1 Run and dispositions

The independent reading ran on 2026-08-19 with only §3's quoted frozen rows,
the family-adapter specification, and §2's boundary declaration. It found and
closed three overstatements:

1. **T2 pre-intent refusal:** the draft replaced the frozen root-selection
   failure with request validation failure. The replacement is not a banked arm.
   **Disposition:** retain only intent-append failure in the selected bullet;
   keep root selection deferred and identify request validation as unselected.
2. **R23 import behavior:** the frozen local basis/composition disagreement is
   triggered by a second dataset-production run. The row's explicit-import
   clauses instead require producer snapshots, receipts, world corpus states,
   and rule resolution. **Disposition:** remove the invented import mutation and
   defer R23; the specification's validation promise narrows rather than
   expanding the selection.
3. **C10 declaration count:** ordinary-write target resolution is selected by
   M3, while C10 says its termination role is not a new arm. **Disposition:**
   keep the one M3 declaration and remove the duplicate C10 declaration unit.

The reader originally rederived all 24 row states as **8 full + 12 part + 4
deferred** and counted **34** §3 Selected declaration units for Task 16. That
was the bank-time result: the reader correctly demoted R23 but missed that R19
and R22 cannot run from the frozen import boundary.

A later implementation-feasibility audit found that the persisted
run/verification/assessment projections and `import_bundle(Sequence[Node])`
omit the complete `RunClosure`, result, comparison, frozen-specification, and
callable rule-implementation evidence needed for R19 and R22 semantic
recomputation. Exact link and stamp hygiene cannot substitute for those checks.
The post-freeze correction therefore defers R19 and R22, leaves R20 selected
and R23 deferred, and rederives the inventory as **8 full + 10 part + 6
deferred = 24**, with **31** §3 Selected declaration units for Task 16.

The reading completed before banking froze the cut. At banking, implementation
was prospective: no implementation task could cite the cut as a discharge
authority until its selected obligations were implemented and verified.

A second implementation-feasibility review on 2026-08-19 found two more
unexecutable declarations without changing either affected row's `part`
classification:

1. **T2 second fulfillment:** the operation port and engine treat `fulfills`
   as opaque and append both registrations. No durable-log consumer or
   classifier exists, and a test-local count is not classification.
   **Disposition:** defer this arm until that consumer exists; retain T2's
   success, refusal, and intent-append-failure arms.
2. **M3 concrete import cycles:** controlled retraction identities hash their
   targets, so a cyclic pair cannot be constructed without circular fixed-point
   identities. Raw forged pairs fail controlled-shape validation and are the
   row's explicitly forbidden non-test. **Disposition:** defer the bundle-only
   and bundle-plus-local arms until a controlled cycle is spellable; retain the
   direct abstract witness, forced-verdict consumption, local-DAG termination,
   and ordinary unresolved-target arms.

The current inventory is therefore **28** §3 Selected declaration units. Row
accounting remains **8 full + 10 part + 6 deferred = 24** because T2 and M3
retain selected arms and remain part.

## 7. Limitations

1. **Local is not world.** Retraction discovery, standing, cycle validation,
   derivation recomputation, and producer comparison stop at one corpus root
   plus the arriving bundle. An absent foreign record produces only the outcome
   the frozen import rule permits; it is never silently treated as verified.
2. **The operation log is still unanchored.** Intent, payload, and report grains
   are durable and chained, but no selected arm refutes truncation or chain
   removal without anchor acts and a valid observer set.
3. **No recovery resumption.** A crash can leave intent only or intent plus
   payload. Retrying opens a new operation; it does not adopt the old intent.
4. **No world-changing family.** Consolidate, move/rename, and deletion remain
   deferred and must reopen target-resolution and locking assumptions.
5. **Prospective, not discharged.** The cells state what implementation and N2
   must demonstrate. They do not say the current tree does it.
6. **Arm boundaries remain a reading.** The frozen cells are prose. That is why
   the independent reading is a precondition of freeze and why any uncertainty
   is classified toward part or deferral.
