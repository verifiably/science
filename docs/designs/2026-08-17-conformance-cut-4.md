# Conformance cut 4 — the first persistence slice

**Status:** Draft — selection pending; freezes when the composition-root adapter design banks.

**Sources:** the cut-4 scope spec
(`docs/superpowers/specs/2026-08-17-conformance-cut-4-scope-design.md`);
`2026-08-11-conformance-cut-3.md`; `2026-08-03-redesign-adoption-ledger.md`;
and, by description, the `atoms` authority design §14 and Plan B §12.2.

## 1. What this cut is drawn against

Cut 4 is drawn against the certified `atoms` engine adopted at Science's
composition root: the corpus-write adapter compiles a generic corpus write
into a `TransactionSpec` and submits it against the certified Linux volume
tuple, per the `atoms` authority design §14. Every other volume tuple fails
closed — there is no fallback path that writes durably outside the certified
binding.

The slice is **add-only**. Edits, moves, and deletions are not built here;
they are the family adapters' surface — supersede, archive, import/cohort —
which Plan B item 2 assigns to their own adapters in later cuts. What this
cut selects is bounded by the corpus-write adapter alone, Plan B item 1.

The draft freezes when the composition-root adapter design banks, and that
design itself waits on the `nodes` write-plan/executor seam freeze. Until it
banks, this document's status header reads draft, and its freeze block, once
written, is present but not in force.

## 2. The boundary

In scope:

- durable minting of new corpus records through the write API's add path;
- refusal of every volume tuple outside the certified binding;
- compilation-correctness obligations at the Science boundary — `atoms`'
  physical certification is relied on, never re-run;
- stored-corpus traversal over the durable store.

Out of scope, each named with where it waits:

- **the family dialects** (supersede, archive, import/cohort) — wait for
  their own adapters, Plan B item 2;
- **the managed holdings root** — the verified-holdings store's own
  management surface is not the corpus-write adapter's target, and waits on
  an adapter this slice does not build;
- **the world index** — waits on composition-root adoption together with the
  `nodes` contract deltas, as cut 3 restated;
- **retraction records** — subtracting standing without deleting a record is
  an edit-shaped write, outside this slice's add-only surface;
- **the rules store and resolver** — remain unbuilt, exactly as cut 2's P1
  deferral recorded;
- **the registry compile** — remains unbuilt, so the kind-existence check it
  would ground stays unbuilt with it;
- **the L rows and anchor carriage** — wait on the next persistence cut, as
  the closing paragraph below states.

Registration is an engine facility. The `atoms` executor appends a
registration entry inside every transaction this slice commits, and
`TransactionSpec` already carries `consumer_tag`, `intent_digest`, and
`fulfills` — the corpus-write adapter reserves nothing and adds no effect of
its own. No L row is selected here: anchor carriage and Science-side
verification — cut 3's intent/reduction semantics meeting the durable chain
— are the next persistence cut's work, and it selects the L rows then. Until
anchor acts exist, every transaction this cut commits is **chained but
unanchored**, and the unbounded unanchored tail is this cut's stated
limitation.

## 3. Step 1 — what the slice crosses

**The substrate.** The slice crosses the write API's add path made durable
and the stored-corpus traversal that reads back what that path minted: a
corpus record is minted through the add path, compiled into a
`TransactionSpec`, and committed against the certified volume tuple; the
world layer's closure then walks the committed store through `nodes`'
one-hop `outbound()` / `inbound()` operations — one algorithm over the
relation and lineage adjacency adapters, as the substrate consolidation
design §3 relocated it. Three consequences bound every S-row reading below,
and each is a boundary fact rather than a preference.

1. **A corpus root is durable; the crossing between two of them is not
   built.** Corpora exist and a record knows its own, but nothing resolves
   an address to the corpus holding it — that step is the world resolver,
   and the world addressing design's own capability table assigns it to the
   world layer, where a corpus-local walk "truncates at the corpus edge".
   The **world index** is out of scope, so every closure this cut runs is
   corpus-local, and every cross-corpus fixture defers with it.
2. **A raw filesystem write to a corpus path is available, and it is a
   fixture act rather than a slice operation.** The substrate consolidation
   design §4.2.1 defines such a write as an **untrusted import** by
   definition — a module bypassing `nodes` entirely — and with a durable
   store beneath it, a fixture constructs one without the write API,
   without an edit, and without touching any excluded subsystem. That is
   what makes S3's stale-hash pair, S7's eligibility violation, and S8's
   negative runnable here, and it is the one construction this cut's S rows
   use that the add path does not perform. It is invisible to the
   engine-supplied chain in both directions: the chain records the
   transactions this slice commits, not the filesystem beneath them.
3. **The slice is add-only, so a store state a deletion would produce is
   reached only by minting it.** A basis entry naming an address no record
   carries is mintable, and an arm asserting the resulting *state* is
   selectable. An arm asserting the *transition* — a digest that moved
   because something was removed — is not, and it stays with the deletion
   surface.

## 4. Step 2 — the selection, arm by arm

### 4.1 Selected in full

| row | what the slice must demonstrate |
|---|---|
| **S3** | a stale semantic hash refused on import, where *import* is the substrate consolidation design §4.2.1 sense — an untrusted write — and not the import/cohort **plan family** this cut excludes: a record whose stored hash disagrees with its fields is raw-written into the durable store and the read refuses it. The refusal half needs no edit at all — a refusable record is *minted* stale rather than edited stale — so the row's own word "hand-edit" names a construction, not a dependency on the excluded edit surface. **Negative**, pinning §4.3's bound: raw-write a record whose fields and stored hash agree with each other and with nothing that preceded them, and assert it passes undetected. The negative is neither strengthened nor weakened by durability here — the chain records committed transactions, and a raw write is not one — so what it pins is exactly §4.3's recorded-history limitation, the G4/G8 pattern the banked cell names |
| **S7** | eligibility enforced at **both** boundaries, both of which this slice builds. The write boundary (substrate consolidation design §6.2 item 1): the add path refuses to mint an inadmissible `assesses` edge. The profile-level corpus check (item 2): a file raw-written into the durable store carrying an `assesses` edge whose run has no `observes` input is reported `eligibility-unmet` by the check reading that store, under the Science-owned code namespace §6.2 fixes. The cross-node predicate spans assessment → run → `observes` → dataset → facet — kernel kinds and the `science` base profile's own `empirical-observation` facet, corrected there by the domain-extension boundary — so no clause of it reaches the excluded **registry compile**. The row's stated bound, that a raw write producing a *valid* node is intentionally unreported, is asserted rather than assumed: it is S8's negative, selected below |
| **S8** | the static claim over the code this cut wires: no module outside the write API constructs or receives a mutable `Corpus`, checked by AST — the capability boundary §4.2.1 chose precisely so that a new writer cannot escape by being undiscovered. The claim gains its first durable subject here, the composition root where the corpus-write adapter is the handle's one holder. **Negative:** write a corpus file with a raw filesystem call and assert S8 does **not** fire — the limit pinned, then validated by §4.3's stale-hash check and §6.2's corpus check, which are S3 and S7 and are selected in this same cut, subject to the recorded-history limitation the row carries |

### 4.2 Selected in part

| row | arms **in** cut 4 | arms **deferred**, and on what |
|---|---|---|
| **S1** | the relation fixture minted through the add path into one durable corpus root and walked back out of it: chain, diamond, cycle, unrelated predicate, deprecated ref, dangling target, and the **undirected relation** reached from its stored source but not its stored target — the whole of it corpus-local traversal over `nodes`' one-hop operations, which is the traversal this cut's boundary names; membership-traversal agreement and the non-reinterpretation of `directed` are asserted over that store. **Negative:** `nodes` exposes **no** transitive operation — a static reading of that package's surface, depending on nothing this cut builds | the **chain crossing corpora**, with its assertion of the full closure rather than truncation at the corpus edge. Reaching a target the holding corpus does not carry requires resolving an address to the corpus holding it, and that is the **world index**; run corpus-locally the fixture cannot be built at all, and a truncation indistinguishable from the dangling-target case already selected would assert nothing |
| **S1a** | the lineage fixture over the same durable root, walked as a **facet** rather than as relations: chain, diamond, cycle, a `single` basis, a `conflict` basis yielding **every** route and certifying nothing, and the unresolvable **ancestor** told apart from the unresolvable **producing run** — the distinction the relation adapter cannot express. Both unresolvable cases are constructed by *minting* a basis entry naming an address no record carries, never by deleting one, so §3's add-only reading reaches them; the `conflict` tag is likewise written into the store rather than produced, the boundary minting only `single`. **Negatives:** the lineage adapter accepts **no** predicate and **no** direction argument; and one algorithm serves both adapters, so cycle-safety and start-exclusion are certified once — assertable because S1's adapter arms are selected in this same cut | the **cross-corpus chain**, deferred with S1's and for the same reason — a basis whose ancestor lives in another corpus is resolvable only through the **world index** |
| **S5** | the walk that *produces* the lineage snapshot from a store, in its corpus-local form: the basis walked transitively out of a durable corpus root under the substrate consolidation design §5's procedure — the inspected set is `{observed root} ∪ closure`, the root included because the traversal is start-excluding (step 1); a `conflict` tag short-circuits to `lineage-divergent` on the tag alone, before resolution or comparison (step 2); a basis entry that does not resolve — absent ancestor or absent producing run alike — yields `lineage-incomplete` and no certificate (step 2b); and deleting the observed root's immediate parent is reached in its minted form, a root carrying an unresolvable entry with an empty closure, still `lineage-incomplete`. Cut 2 deferred exactly this piece on "**S1a's and the write API's** territory"; this cut supplies both — the add path mints the basis durably, and S1a's walk runs over the store — so what cut 2 could not run is what this cut adds | the walk's **cross-corpus** reach, with S1's and S1a's, on the **world index**; the banked construction — *delete* an ancestor named by a basis and assert the `belief_input_digest` **changed** and belief did not rise — which is a transition across the **deletion surface** Plan B item 2 assigns to the family adapters, leaving both halves where cut 2 left them, over supplied snapshots; and the negative's *"indistinguishable from one where that run never existed"* clause, which needs the same **deletion surface** and is in any case a claim about what a store retains after a removal, not about the walk this cut adds |

### 4.3 Standing from prior cuts

Two substrate rows the reading reached and left exactly where they stand.
**S2** — *a semantic edit through the write API mints a new proposition* —
is pure edit in its banked cell
(`2026-08-02-substrate-consolidation-design.md:550`: edit scope via API,
assert a new node, a `supersedes` edge, and prior refs unmoved): every
clause of it is the supersede dialect's surface, so it gains no arm and
defers whole to the **supersede family's** cut. **S4** — *`nodes.rename` is
never used for a semantic change* — asserts that no rename path is
reachable **from the semantic-change branch** (`:552`), and this slice
builds no such branch; asserting unreachability from a branch that does not
exist is not a weaker form of the row but a vacuous one, which N2's
sabotage doctrine refuses. It defers whole with S2, to the same cut.

## 5. Step 3 — fully deferred rows, grouped by unblocking subsystem

## 6. Accounting, freeze, and amendment discipline

## 7. The second reader — reserved
