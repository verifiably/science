# Second-project milestone: health over mm30 — design

**Date:** 2026-10-26
**Status:** draft, for review
**Task:** `sci-0d00d2`
**Authority:** `docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md` §9.2
(the seven criteria), §6.2 (the three queries), §7 (the single-home fence), §9.1 (the
reading pass), §10 P7. Its measurements answer `beliefs`' 2026-10-14 request (task note),
`docs/specs/2026-10-01-mount-citations-consumer-design.md` §6 limitations 1 and 3, and
the two shelved kernel ideas `beliefs-7c98bc` and `beliefs-655c10`.
**Discipline:** `docs/records/2026-09-23-mm30-through-the-commands.md`: preflight and
predictions committed before the run, findings classified after, every refusal filed to
its owning lane.

## 1. What this is

A measurement, not a feature. One world root on this host holds the reproduced mm30
corpus and, after this milestone, one fresh working corpus; a session writes the working
corpus and reads both. Three `project` views are minted over that world, one health
question is asked, and the seven observable criteria of §9.2 are run with their outcomes
predicted first. The output is a record, the findings it files, and notes on the two
`beliefs` ideas its counts scope.

The milestone also carries one small code change this reading pass found necessary (§4.2,
§5.3): science's launcher cannot compile the contract the mm30 corpus pins, because that
contract is a successor in a document chain and the loader parses every document as a
genesis. Without it criterion 1 cannot be met: the mm30 corpus cannot be mounted.

## 2. Goals, non-goals, anti-goals

Goals:

- Criteria 1–7 of §9.2 run against the live world root, each with a prediction written
  before the run and marked after it.
- The §9.1 reading pass's three outputs: the three coarse queries with their addresses
  read from the records, the first health question, and the datasets it needs held.
- The measurements of §6: epoch builds by trigger class, explicit address entries per
  view, same-query reuse and repair burden, and citing-write costs.
- Every refusal and gap filed to its lane; `beliefs-7c98bc` and `beliefs-655c10` noted
  with the counts that scope them.

Non-goals:

- Holding the health question's dataset, running or assessing anything new. The
  question's spec is frozen over a declared, unheld dataset, which is what criterion 3
  asks; the next action on it belongs to the health program, not this milestone.
- Recreating any other health or cancer question (§9.3).
- Binding a disease vocabulary (§6.3), or designing a health contract with its own
  estimands (§4.1, option 3).
- A real `publish`: criterion 5 is the dry run, `publish-preview`.
- New `science` commands for corpus genesis or dataset declaration. Both gaps are filed;
  the milestone runs them as kernel-level driver steps and says so.

Anti-goals (what would make this a failure even if every command exits 0):

- A prediction written after its command ran, or a query address authored by hand.
- A scientific example dressed up: a proposition that does not say what the question
  asks, a dataset whose digest is not the digest of real bytes, or a selection
  expectation tuned to pass.
- A refusal worked around in the driver and not filed.

## 3. Constraints the reading pass found

Read before any command ran; each shapes a decision below.

- **C1. The world root is half-built.** `/mnt/ssd/science/worlds/aec951bc6becacced13df8f7ae6f8abf/`
  holds `world/`, `corpora/mm30/` (corpus `8b5d0c80…`, admitted `replica-of`), `store/`
  (`05b6c122…`) and `anchors/`. There is no working corpus, no `ops/`, and
  `SCIENCE_CONFIG` names `/mnt/ssd/science/science.toml`, which does not exist. The
  world has no epoch and no rule bindings; `science epoch` installs the shipped rule
  bundles when it first builds.
- **C2. No command creates a corpus or declares an unheld dataset.** Genesis is
  `init_corpus_root` + `adopt_manifest` + `world.admit(Fresh())` in the kernel, which the
  test helpers and `beliefs`' relocation tool call directly. `science dataset` always
  holds bytes; the kernel's `Declared` state (pinned digests, no observation) is
  reachable only by adding a dataset node through the writer.
- **C3. The mm30 corpus pins a successor contract.** Its manifest pins
  `mm30:4af7c4212d482ae60f429526ff5a8a6d4c335f70351a2687cd2062ffdedf437c`
  (`beliefs` reproduction design §11.1). That identity is produced only by parsing the
  chain cut 22 → cut 31 → current (`beliefs` `python/tools/reproduction/mm30-cut22.yaml`,
  `mm30-cut31.yaml`, `mm30.yaml`), each document as the next one's predecessor, with the
  four `{{…}}` vocabulary tokens replaced by the held lists' addresses. Verified in this
  pass: the driver's `vocabulary.contract()` yields `4af7c42…`; science's
  `load_contract_document` (predecessor `None`) refuses the current document's
  `successor` lineage and refuses the `also:` key the driver's copies carry. So neither
  `contracts` nor `read_contracts` can name the pinned contract today, and
  `compile_mount_profile` would refuse the mount as `MountPinUnresolved`.
- **C4. Only one operator carries estimands.** `spec` freezes an estimand from the
  operator's `estimands:` declaration. The shipped biology pack declares none; mm30
  declares one, for `affects-concept-molecular-entity` (slot 0 levels from
  `stage-level`, measure `measure`, identification, conditioning `concept`). The stage
  levels are `level:ndmm` and `level:pd`; the one measure is `measure:rna-seq-tpm`. A new
  proposition that can carry a spec in this world is therefore `concept:<c> affects
  protein:<g>`, typed under mm30, contrasted NDMM → PD in RNA-seq TPM. For the working
  corpus to type it, the writer must activate mm30 at the pinned identity, which the
  consumer spec's decision 2 already requires of citations.
- **C5. Term clauses and criterion 3 interact.** `references-term` selects every
  proposition whose claim binds the term. If `multiple-myeloma`'s coarse query names
  `concept:disease-stage`, a new proposition over that concept is selected by
  `multiple-myeloma` too, and §9.2's "a fact `health` selects and `multiple-myeloma` does
  not" fails by construction, not by evidence.
- **C6. The live mm30 edges are fewer than §6.2 lists.** Both runs carry `observes` only
  (no `reads` to the vocabulary lists); the assessment `assesses` the stage → PHF19
  proposition and is `produced_by` run `8b1a2401…`; the verification `verifies` it. The
  second proposition (PHF19 → overall survival) and the composite are reached by no
  closure over §6.2's four predicates.
- **C7. The dry run will refuse on attribution, not closure.** `publish-preview
  --target <project> --to <absolute path>` is the kernel's step 0, written nowhere; it
  reports selection, closure status and the inputs the destination will not carry, and a
  kernel `PublicationRefused` reaches the person as `kernel-refused` with its reason.
  Two facts fix its outcome here. The closure check (`beliefs` `publish_request.closure_missing`)
  walks stored world relations only, so a spec's projection-held inputs can never be
  "missing": closure over the coarse selection is complete. And the attribution check
  (`beliefs` `publish._selected_attributions`) treats every `replica-of` holder of a
  selected record as a foreign publication: under the working corpus's coordination v2
  pin it refuses `attribution-contract-unpinned` naming the replica; under v3 it demands
  a publication marker the relocated corpus does not carry (`attribution-source-invalid`).
  Every record `multiple-myeloma` selects is mm30's, and mm30 was admitted `replica-of`
  by its relocation. So criterion 5 cannot report a clean dry run in this world, and the
  design predicts the refusal (§5.6) rather than re-admitting the corpus to dodge it.
- **C7a. Writes route through one live session.** Write-class commands reach the corpus
  over the service socket, and `science serve` or `science mcp serve` opens one attended
  kernel session for its lifetime. A kernel-level driver step cannot run beside that
  session; it runs before the server opens or after it exits. And a query address must
  exist when the view is evaluated: `evaluate_query` refuses `address-unknown` for an
  address the world does not hold, so a project whose query names the health records
  cannot be evaluated before those records exist.
- **C8. The predecessor is on this host** in the predecessor tree (`proto/projects/`, a sibling checkout):
  `health/meta` (193 questions), `cancer/cancer-types/multiple-myeloma` (260 dataset
  entities). Their dataset entity names overlap in exactly two: `depmap` and `tcga`.
  `health/meta`'s myeloma-related material is the translational-capacity propositions
  and question 0167 (p53/RP–MDM2 surveillance), whose cited mm30 evidence (a TP53
  stratification) is not a governed record in the reproduced corpus.

## 4. Approaches

### 4.1 The scientific example

1. **A proposition typed under mm30's estimand-bearing operator, chosen so no mm30 term
   clause selects it** (chosen). `concept:disease-progression affects protein:EZH2`,
   layer `causal_effect`, polarity positive, asked under `health` as: *does disease
   progression drive the PRC2 catalytic core (EZH2) where it drives PHF19?* It stands
   on the live record `concept:disease-stage affects protein:PHF19` and on the
   predecessor's PHF19/PRC2 mechanism line (`protein-phf19-regulates-concept-prc2-complex`,
   `protein-ezh2-associates-with-protein-phf19`, interpretation t199's finding that the
   PHF19 signature is myeloma-context-specific). Its spec contrasts NDMM → PD in RNA-seq
   TPM over a second, unheld cohort. The record labels it a **narrower sub-claim**: the
   half that makes it a health question (does the PRC2 coupling generalise beyond
   myeloma, `health/meta` plan 0006's "weak-generalization" flag) is not representable
   until a disease vocabulary is bound (§6.3), and the stage levels are myeloma's.
   `concept:disease-progression` is in mm30's concept vocabulary and names the NDMM → PD
   contrast as a process; it is chosen over `concept:disease-stage` so that
   `multiple-myeloma`'s term clauses (C5) do not select it, and the record says so.
2. `concept:disease-stage affects protein:EZH2`. The literal sub-claim; rejected because
   of C5: the only way to keep it out of `multiple-myeloma` would be to drop the term
   clause the spec prescribes, which is tuning the query to the test.
3. A `health` corpus-local contract with its own estimands (tissue levels, a TPM
   measure) and a GTEx-anchored co-expression claim (`protein:PHF19 associates-with
   protein:EZH2`). The only genuinely cross-disease option, and the right shape for a
   health program; rejected here because it is contract design and vocabulary holding,
   outside a measurement of the project surface. Named in §8 as the follow-up.

The dataset: Zenodo record 22399365, "Frozen MMRF-CoMMpass count matrix for RNA-seq
differential expression teaching (diagnosis vs. relapse, n=30+30)", CC-BY-4.0, published
2026-09-05, listed `eligible` in the mm program's roster (`commpass-open-60-counts`;
exposure noted there). Two resources are declared: `mm_counts.csv.gz` (3,172,813 bytes,
Zenodo md5 `e18dc9b7…`) and `mm_metadata.csv` (7,637 bytes, md5 `9201e47f…`). Each
sha256 is computed from bytes downloaded to the driver's scratch directory and checked
against Zenodo's md5 before the declaration; the bytes are then discarded, never held.
The honest limit is stated in the spec's `method` and in the record: the files carry
STAR unstranded counts, and `measure:rna-seq-tpm` is reached by a stated transformation
(GENCODE v36 lengths), which is the analysis's first step when the dataset is held. The
alternative, declaring a desired future dataset with a made-up digest, is rejected: a
fixture digest exercises the machinery and declares nothing.

### 4.2 The pinned contract

1. **Teach the launcher loader contract chains** (chosen). A `contracts` or
   `read_contracts` entry is a path (a genesis document, as today) or a table
   `{ document = "<path>", predecessors = ["<oldest>", …] }`; the loader parses the
   predecessors oldest first, each as the next document's predecessor, and the entry
   activates the last. A chain whose link fails `check_succession` refuses by name. The
   world's copies of the three documents carry the concrete vocabulary addresses and no
   `also:` key; the preflight asserts the chain compiles to `4af7c42…`.
2. Block the milestone on a separate task. Cleaner records, slower; the need is measured
   here and the change is small. Rejected as the path, kept as the record: the change is
   filed as its own `sci` task the milestone depends on, implemented as the plan's first
   task in this worktree.
3. Re-pin the corpus. Never: the corpus's manifest is the kernel's and the corpus is a
   replica.

### 4.3 Kernel-only steps

A driver under `.work/second-project/` (gitignored, as `.work/mm30-commands/` is):
`genesis.py` (world config, the working corpus, its manifest, admission, the contract
copies, `science.toml`), `declare.py` (the unheld dataset), `walk.py` (the MCP frames,
adapted from the mm30 walk), and the transcripts. Both kernel-level steps run **before
the server opens** (C7a): genesis, then the declaration, then one `science mcp serve`
process carries every command of the walk as one attended session. Each kernel-only
step is quoted in the record and filed as a surface gap. The alternative, adding
`science corpus-init` and `science declare` first, is rejected: the milestone measures
the surface as it is.

### 4.4 Criterion 7's MCP arm

The driver sends the JSON-RPC frames to `science mcp serve`, as the mm30 walk did, and
the CLI read runs in a fresh process while the server lives. A live coding-agent arm
(the pi probe's shape) is not required by §9.2 and is optional.

### 4.5 Where the record lands

`docs/records/2026-10-26-second-project-milestone.md`. §9.2 says `docs/plans/`; the
`docs/records/` directory, where both measurement records now live, postdates that
sentence. This is the author's call.

## 5. The design

### 5.1 The reading pass (§9.1)

One bounded pass over `health/meta`, `multiple-myeloma` and the overlap produced:

- **The three coarse queries** (§5.4), with every address read from the records.
- **The first health question** (§4.1, §5.5).
- **The datasets the question needs held:** the declared Zenodo set (§4.1), and nothing
  else; the vocabulary lists it types under are held by the mm30 corpus.
- **The overlap inventory**, for the record: the predecessor dataset entities shared by
  name between the two trees are `depmap` and `tcga`; GTEx is `health/meta`'s only.
  None is held or declared here.

### 5.2 The world

```
/mnt/ssd/science/
  science.toml                       # SCIENCE_CONFIG, written by genesis.py
  contracts/mm30/                    # the chain, addresses concrete, no `also:`
    mm30-cut22.yaml  mm30-cut31.yaml  mm30.yaml
  worlds/aec951bc6becacced13df8f7ae6f8abf/
    world/  store/  anchors/  relocation.json
    corpora/mm30/                    # as relocated
    corpora/working/                 # the working corpus (§3.1: one writer per host; a
                                     # second host gets a second corpus)
    ops/                             # operations_root; the service socket beside it
```

`science.toml`:

```toml
world_root = "worlds/aec951bc6becacced13df8f7ae6f8abf/world"
world_id = "aec951bc6becacced13df8f7ae6f8abf"
corpus_roots = ["worlds/aec951bc6becacced13df8f7ae6f8abf/corpora/mm30",
                "worlds/aec951bc6becacced13df8f7ae6f8abf/corpora/working"]
write_root = "worlds/aec951bc6becacced13df8f7ae6f8abf/corpora/working"
operations_root = "worlds/aec951bc6becacced13df8f7ae6f8abf/ops"
store_root = "worlds/aec951bc6becacced13df8f7ae6f8abf/store"
domains = ["biology"]
contracts = [{ document = "contracts/mm30/mm30.yaml",
               predecessors = ["contracts/mm30/mm30-cut22.yaml", "contracts/mm30/mm30-cut31.yaml"] }]
coordination = 2
```

The working corpus pins exactly what the writer activates: base `52a43993…`, biology
`24bcec43…`, mm30 `4af7c421…`, coordination v2. mm30 goes under `contracts`, not
`read_contracts`, because the writer types the health proposition under it (C4) and the
consumer spec's decision 2 asks the second-project record to say which namespaces the
working corpus pins: both of mm30's, at mm30's identity.

### 5.3 The loader change

In `science.config.load_config` and `science.contracts`: a `contracts`/`read_contracts`
entry is a string or a table with `document` and a non-empty `predecessors` list; any
other shape refuses naming the entry. Loading walks the predecessors oldest first through
`parse_domain_contract(…, predecessor=<previous>)`, then the document; the entry's
contract is the last. A `SuccessionViolation` or `MalformedContract` anywhere in the
chain refuses with the entry and the kernel's message. Today the loader catches only
`MalformedContract`, so a successor document reaches the person as `internal-error`;
the chain loader catches both, for a bare path as well as a table. Relative paths resolve as every
config path does. Duplicate detection across `contracts` and `read_contracts` compares the
activated contract's identity, as today.

Tests: a chain compiles to the successor's identity and a bare path still parses a
genesis; a chain whose predecessor does not match refuses by name; a table missing a key
refuses by name. The framework design §9.1 takes a dated amendment and the README's
configuration paragraph names the shape.

### 5.4 The three queries

Addresses are read from the records at minting time; the record pins the full values.
Clause semantics: top-level `clauses` union, `all` intersects.

`multiple-myeloma`:

```yaml
version: science.view-query.v1
clauses:
  - all: [{closure: {anchor: "dataset:sha256:a6bf229ef0abd8e11f0b7f017cbdb6977395e23d83fb122fcf141f723ba1e448",
                     predicates: [observes, produced_by, assesses, verifies], direction: both}}]
  - all: [{addresses: ["analysis-spec:10e8bfce1aaad8a937a79bfba7cf523ac42b4240ec8b15e20e5b5f450d234714"]}]
  - all: [{references-term: "concept:disease-stage"}]
  - all: [{references-term: "concept:overall-survival"}]
```

§6.2 prescribes one term clause per concept the contract binds; the vocabulary binds
285. The coarse form here names the two concepts the live propositions bind, and the
record reports 285 as the full form's clause count (M2). The composite
`composite:h1-prognosis-fragment` is reached by no clause (C6: `composes` is not among
the four predicates); the record reports it as the coarse form's known omission rather
than widening the predicate list past the spec.

`cancer`: the four clauses verbatim.

`health`: the four clauses verbatim, plus

```yaml
  - all: [{addresses: ["proposition:concept-disease-progression-affects-protein-ezh2",
                       "analysis-spec:<minted>",
                       "dataset:sha256:<declared>"]}]
```

so that containment holds as a fact about the queries (§6.2): `multiple-myeloma` ⊆
`cancer` = `multiple-myeloma`, and both ⊂ `health`.

The health `question`'s own query is the closure clause over the mm30 dataset plus the
same `addresses` clause: its evidence path reaches mm30 facts, and it names what it
introduces.

### 5.5 The health question's records

Minted in the working corpus in this order. The world facts come first, before any
project exists (world kinds need no selection, P2), because `health`'s query names
them and a view cannot be evaluated over an address the world does not hold (C7a):

1. The dataset declaration (driver, kernel-level, before the server opens): two
   resources with their sha256 digests, title "MMRF-CoMMpass teaching counts, 30
   diagnosis and 30 relapse (Zenodo 22399365)", empirical observation
   `locator: doi:10.5281/zenodo.22399365` attested by the driver's actor, and a
   `biology/gene-axis` facet as the mm30 dataset record carries. Its address is the
   content fold over the two digests.
2. `claim --subject concept:disease-progression --predicate affects --object protein:EZH2
   --layer causal_effect --polarity positive` → `proposition:concept-disease-progression-affects-protein-ezh2`
   under `mm30/affects-concept-molecular-entity`; `protein:EZH2` resolves `not-consulted`
   under the HGNC binding as PHF19 did. A citing write: the concept vocabulary is read
   from the mm30 mount.
3. `spec --target <the proposition> --dataset <the declaration> --contrast levels --slot 0
   --baseline level:ndmm --comparison level:pd --measure measure:rna-seq-tpm --scale
   additive --reference 0 --identification identification:observational` with the method,
   assumptions, falsification and the two shipped rules (`beliefs/outcome-file/v1`,
   `beliefs/content-identity-equality/v1`), `--parameters alpha=0.05` as mm30's walk
   gave it. The method states the counts → TPM step.
4. The three `project` records (§5.4), under no selection: `health`'s `addresses`
   clause now names records the world holds.
5. `project-select health`, `question` (§5.4's query); then `project-select cancer`,
   `reuse --source <its address>`.

### 5.6 The walk, by criterion, with predictions

Written here as the record's §2 will carry them; the record is the authority once
committed before the run. Each is marked `confirmed`, `confirmed for another reason`, or
`refuted`.

| # | step | prediction |
|---|---|---|
| 1 | `genesis.py`, then `science status` | the world lists two corpora, each `known`, `live` and `present` with no finding; records in mm30: 18 (5 datasets, 5 holdings observations, 1 analysis-spec, 2 runs, 1 assessment, 1 verification, 2 propositions, 1 composite), in working: none; no current epoch |
| 1 | `science epoch` (initial) | `built` over both corpora; the shipped rules install; wall time recorded (M1) |
| 1 | `declare.py` ran before the server; the server opens once | the declaration is in working as a `Declared` dataset; `next` (no selection) shows `assessed-unevaluated (epoch-stale)` for the PHF19 proposition until `science epoch` (M1, `evidence`) |
| 3 | `claim`, `spec` under no selection | both mint (world kinds need no project); `spec` resolves its vocabulary referents in the mm30 mount and accepts a `Declared` dataset; each is a citing write (M4) |
| 2 | `project` ×3 under no selection | three `project` records minted (P2's genesis path); each a coordination write; `next` afterwards is `epoch-stale` until `science epoch` (M1, `coordination-only`) |
| 2 | at one epoch, the three selections | each selects `proposition:concept-disease-stage-affects-protein-phf19` (closure and term), `…protein-phf19-affects-concept-overall-survival` (term), both runs, the assessment, the verification, `dataset:sha256:a6bf229e…`, `analysis-spec:10e8bfce…`; not the composite, not the vocabulary datasets. `health` additionally selects the EZH2 proposition, its spec and the declared dataset; `cancer` and `multiple-myeloma` do not |
| 3 | `project-select health`; `question` | the question mints under `health`, its query evaluable; a coordination write (M1) |
| 3 | `project-select cancer`; `reuse` | one act; the copy carries the source's query byte-equal and a body naming the source address; the source's tip is unchanged (M3) |
| 4 | `next` under each project and none, at one epoch | `multiple-myeloma` = `cancer`: `not-ready: protein:PHF19 affects concept:overall-survival`, then `admitted: concept:disease-stage affects protein:PHF19`; `health` = unselected: `not-ready: concept:disease-progression affects protein:EZH2`, `not-ready: … overall-survival`, `admitted: …PHF19`; rows in class order then id |
| 5 | `publish-preview --target multiple-myeloma --to <scratch>` | refuses `kernel-refused`, reason `attribution-contract-unpinned` naming corpus `8b5d0c80…` (C7): every selected record is held by a `replica-of` corpus and the working corpus pins coordination v2. No closure report is rendered. The refuted branch is a clean report, which would mean the kernel exempts a replica of the world's own relocated corpus. The closure the selection would carry is computed by the record from the stored relations (M5): eight records, complete |
| 6 | `status` and `next` from the mm program's workspace checkout (`multiple-myeloma`), from `.work/mm30-commands` (a decoy `science.toml` and corpus) and from a fresh `mktemp -d` | byte-identical output |
| 7 | over `science mcp serve`: `project-select health`; then CLI `next` in a new process, `next --project multiple-myeloma`, then `projects` | the CLI read observes `health`; the `--project` read observes `multiple-myeloma`; `projects` still marks `health` |

Expected `NoBelief(no-directional-outcome)` for the PHF19 proposition's belief is not a
criterion and is read once for the record's completeness.

### 5.7 Measurements

- **M1 epochs.** Every `science epoch` run: trigger class (`initial`,
  `coordination-only`, `evidence`, `none` when nothing changed), outcome (`built` or
  `current`), wall time, and the read that forced it. Coordination-only count and cost go
  to `beliefs-655c10`; the per-change cost to consumer limitation 1.
- **M2 explicit entries.** Per view: `addresses` entries, term clauses, closure anchors;
  plus the full coarse form's term count (285) and the records the coarse form omits
  (the composite). To `beliefs-7c98bc`.
- **M3 the fence.** Same-query mints (1), fresh questions (1), repairs needed (0
  expected), and whether the source changed. To §7's decision; a request to `beliefs`
  only if the count argues for one.
- **M4 citing writes.** Wall time of `claim`, `spec` and the declaration (cross-corpus
  citations, one mount open per citing write) against `project`, `question`, `reuse`.
  To consumer limitation 3 and `sci-d92797`.
- **M5 the closure on refusal.** Criterion 5 refuses on attribution (C7), so the
  record carries the refusal verbatim and computes the selection's closure itself from
  the stored relations, listing any identity outside the selection; the publish
  design's closure rule is then measured even though the act never reports it.
- **M6 the working corpus after the walk:** records by kind, and the ledger lines
  (`project-select`) count.

### 5.8 Findings

Classified `defect`, `design-gap`, `surface-gap`, `corpus-work`, each filed to its lane
(`sci` or `beliefs`) with the record as evidence. Known before the run: the contract
chain (§5.3, `sci`, fixed in this plan); no corpus genesis command (`sci`); no dataset
declaration command (`sci`); the `also:` key in the kernel driver's documents
(`beliefs`, informational); the composite outside the coarse form (`sci`, query design);
a relocated replica of the world's own corpus refused as a foreign publication (C7,
`beliefs`, design-gap: the publish act has no notion of a replica the same person
relocated, so no project over the mm30 corpus can be published until it does).

### 5.9 The record

`docs/records/2026-10-26-second-project-milestone.md`, in the mm30 record's shape:
§1 preflight (C1–C8 as observed, the chain identity check, kernel and science commits),
§2 predictions (§5.6), §3 the path (recipes and the command table with invocation ids),
§4 predictions marked, §5 findings, §6 measurements (M1–M6), §7 what this decides (the
fence, the two `beliefs` notes). §1–§2 are committed before the run and the commit named
in the record's status line.

## 6. Guarantees

P7 (projects design §10): the milestone record. The loader change carries its own tests
(§5.3). Nothing else in science changes.

## 7. What is left to the builder

- The genesis driver's exact kernel calls (mirror `tests/helpers/world.py`'s
  `build_fixture_world` and `beliefs` `relocate.py`), the actor name, and the
  `gene-axis` facet's field values for the declaration.
- Whether `science epoch` is run after each coordination write or once after the three
  `project` mints; M1 records whichever the driver does, and both counts are legitimate.
- The scratch directory for the Zenodo download and the `publish-preview` destination,
  both under `.work/second-project/`.
- Test names and fixture shape for the chain loader.

## 8. What this decides and what follows

- §7's fence: one reuse against one fresh question is not a pattern; no `beliefs`
  request unless M3 says otherwise.
- Criterion 5 is met in its refusing sense, with a reason §9.2 did not foresee: the
  dry run refuses on attribution before it can report closure. The finding goes to
  `beliefs` as a design gap in the publish act, and the record's own closure
  computation (M5) stands in for the report until the act can give one.
- `beliefs-7c98bc` and `beliefs-655c10` receive their notes from M2 and M1.
- The health program's first real question needs what option 3 of §4.1 names: a
  contract with estimands beyond myeloma's and a disease vocabulary. Filed as an idea in
  `sci`, not scoped here.
- The mm program (`mm-a32d58`) holds datasets into this world after this milestone; the
  declared Zenodo set is one it may hold or supersede under its own protocol.
