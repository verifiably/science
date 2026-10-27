# Second-project milestone: health over mm30 — design

**Date:** 2026-10-26
**Status:** accepted for planning at review round 2 (revision 2, `1f65730`); revision 3
carries that round's two minor corrections (M3, M4). The proposed authority amendments
of §8 are not approved by that acceptance.
**Task:** `sci-0d00d2`
**Authority:** `docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md` §9.2
(the seven criteria), §6.2 (the three queries), §7 (the single-home fence), §8.1 (the
findings level), §9.1 (the reading pass), §10 P7. Its measurements answer `beliefs`'
2026-10-14 request (task note), `docs/specs/2026-10-01-mount-citations-consumer-design.md`
§6 limitations 1 and 3, and the two shelved kernel ideas `beliefs-7c98bc` and
`beliefs-655c10`.
**Discipline:** `docs/records/2026-09-23-mm30-through-the-commands.md`: preflight and
predictions committed before the run, findings classified after, every refusal filed to
its owning lane. A criterion the run cannot meet is reported unmet; no acceptance
condition is relaxed here, and the two places where the evidence argues for amending
the authority are proposed as amendments (§8), not applied.

Paths: `<data root>` is the directory `SCIENCE_CONFIG` names a file in; `<task dir>` is
the task's persistent scratch directory, `$WORK_ROOT/science/sci-0d00d2/`.

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

Two criteria are predicted not to come out as §9.2 expects, for reasons the reading pass
found in the kernel and in the queries themselves: criterion 3's "a fact `health` selects
and `multiple-myeloma` does not" holds for the question's spec and dataset but not for
its proposition (C5), and criterion 5's dry run refuses on attribution before it can
report closure (C7). Both are predicted as such, run as prescribed, and reported unmet
where they are unmet.

## 2. Goals, non-goals, anti-goals

Goals:

- Criteria 1–7 of §9.2 run against the live world root as prescribed, each with a
  prediction written before the run and marked after it, including the predicted
  shortfalls.
- The §9.1 reading pass's three outputs: the three coarse queries with their addresses
  read from the records, the first health question, and the datasets it needs held.
- The measurements of §5.7: epoch builds by trigger class under a frozen schedule,
  explicit entries per view, same-query reuse and repair burden, command latencies, and
  the two closures (stored-edge and projection-derived) of the findings selection.
- Every refusal and gap filed to its lane; `beliefs-7c98bc` and `beliefs-655c10` noted
  with the counts that scope them; the two amendments of §8 proposed with their
  evidence.

Non-goals:

- Holding the health question's datasets, running or assessing anything new. The
  question's spec is frozen over declared, unheld inputs, which is what criterion 3
  asks; the next action on it belongs to the health program.
- Recreating any other health or cancer question (§9.3).
- Binding a disease vocabulary (§6.3), or designing a health contract with its own
  estimands (§4.1, option 3).
- A real `publish`: criterion 5 is the dry run, `publish-preview`.
- New `science` commands for corpus genesis, dataset declaration, a second spec input,
  or publishing a non-project view. Each gap is filed; the milestone runs the first two
  as kernel-level driver steps and says so.

Anti-goals (what would make this a failure even if every command exits 0):

- A prediction written after its command ran, or a query address authored by hand.
- A query, a concept, or a schedule chosen so that a criterion comes out as expected: the
  prescribed forms are run, and their results are what they are.
- A scientific example dressed up: a proposition that does not say what the question
  asks, a dataset whose digest is not the digest of real bytes, or an analysis whose
  inputs are not all declared.
- A refusal worked around in the driver and not filed.

## 3. Constraints the reading pass found

Read before any command ran; each shapes a decision below.

- **C1. The world root is half-built.** `<data root>/worlds/aec951bc6becacced13df8f7ae6f8abf/`
  holds `world/`, `corpora/mm30/` (corpus `8b5d0c80…`, admitted `replica-of`), `store/`
  (`05b6c122…`) and `anchors/`. There is no working corpus, no `ops/`, and
  `SCIENCE_CONFIG` names a `science.toml` under `<data root>` that does not exist. The
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
  `load_contract_document` (predecessor `None`) refuses the `also:` key the driver's
  copies carry, and without that key the current document's `successor` lineage raises
  `SuccessionViolation`, which the loader does not catch (it reaches the person as
  `internal-error`). So neither `contracts` nor `read_contracts` can name the pinned
  contract today, and `compile_mount_profile` would refuse the mount as
  `MountPinUnresolved`.
- **C4. Only one operator carries estimands.** `spec` freezes an estimand from the
  operator's `estimands:` declaration. The shipped biology pack declares none; mm30
  declares one, for `affects-concept-molecular-entity` (slot 0 levels from
  `stage-level`, measure `measure`, identification, conditioning `concept`). The stage
  levels are `level:ndmm` and `level:pd`; the one measure is `measure:rna-seq-tpm`. A new
  proposition that can carry a spec in this world is therefore `concept:<c> affects
  protein:<g>`, typed under mm30, contrasted NDMM → PD in RNA-seq TPM. For the working
  corpus to type it, the writer must activate mm30 at the pinned identity, which the
  consumer spec's decision 2 already requires of citations. `spec` declares exactly one
  input, in the `observes` role; an analysis that reads a second resource cannot name it.
- **C5. Under the prescribed queries, every proposition the working corpus can carry a
  spec for is a `multiple-myeloma` proposition.** §6.2 prescribes for `multiple-myeloma`
  "one term clause per concept the mm30 contract binds", and `references-term` selects
  every proposition whose claim binds the term. The contract binds 285 concepts, and C4
  makes every spec-bearing proposition a claim over one of them. So the proposition
  criterion 3 introduces is selected by `multiple-myeloma` whatever concept it names;
  what `health` selects and `multiple-myeloma` does not can only be the question's
  `analysis-spec` and its declared datasets, which no term clause reaches and no edge
  connects. This is a fact about the coarse form, foreseen by §6.3 ("coarse and honest:
  a proposition reached from a myeloma dataset is a myeloma proposition"), and the
  design runs the prescribed form and reports it (§5.6 rows 3 and 4, §8).
- **C6. The live mm30 edges are fewer than §6.2 lists.** Both runs carry `observes` only
  (no `reads` to the vocabulary lists); the assessment `assesses` the stage → PHF19
  proposition and is `produced_by` run `8b1a2401…`; the verification `verifies` it. The
  second proposition (PHF19 → overall survival) and the composite are reached by no
  closure over §6.2's four predicates. The live corpus holds 18 records: 5 datasets, 5
  holdings observations, 1 analysis-spec, 2 runs, 1 assessment, 1 verification, 2
  propositions, 1 composite.
- **C7. The dry run refuses on attribution, not closure.** `publish-preview --target
  <project> --to <absolute path>` is the kernel's step 0, written nowhere; a kernel
  `PublicationRefused` reaches the person as `kernel-refused` with its reason. Its
  target resolves through `resolve_project_ref`, so only a `project` record can be
  previewed: a findings level, which §8.1 calls a view the project keeps, must be
  minted as a project to be dry-run (a surface gap). The closure check (`beliefs`
  `publish_request.closure_missing`) walks stored world relations only, so a spec's
  projection-held inputs cannot be reported missing. The attribution check (`beliefs`
  `publish._selected_attributions`) treats every `replica-of` holder of a selected
  record as a foreign publication: under the working corpus's coordination v2 pin it
  refuses `attribution-contract-unpinned` naming the replica; under v3 it demands a
  publication marker the relocated corpus does not carry (`attribution-source-invalid`).
  Every record a myeloma view selects is mm30's, and mm30 was admitted `replica-of` by
  its relocation. So in this world the dry run gives neither of §9.2's two permitted
  outcomes, and criterion 5 is predicted unmet.
- **C7a. Writes route through one live session, and a query is evaluated over what the
  world holds.** Write-class commands reach the corpus over the service socket, and
  `science serve` or `science mcp serve` opens one attended kernel session for its
  lifetime; a kernel-level driver step runs before the server opens or after it exits.
  `evaluate_query` refuses `address-unknown` for an address the world does not hold, so
  a project whose query names the health records cannot be evaluated before those
  records exist.
- **C8. The predecessor is on this host** in the predecessor tree (`proto/projects/`, a
  sibling checkout): `health/meta` (193 questions), `cancer/cancer-types/multiple-myeloma`
  (260 dataset entities). Their dataset entity names overlap in exactly two: `depmap` and
  `tcga`. `health/meta`'s myeloma-related material is the translational-capacity
  propositions and question 0167 (p53/RP–MDM2 surveillance), whose cited mm30 evidence
  (a TP53 stratification) is not a governed record in the reproduced corpus.

## 4. Approaches

### 4.1 The scientific example

1. **The literal sub-claim, typed under mm30's estimand-bearing operator** (chosen).
   `concept:disease-stage affects protein:EZH2`, layer `causal_effect`, polarity
   positive, asked under `health` as: *does disease stage drive the PRC2 catalytic core
   (EZH2) where it drives PHF19?* It stands on the live record `concept:disease-stage
   affects protein:PHF19` and on the predecessor's PHF19/PRC2 mechanism line
   (`protein-phf19-regulates-concept-prc2-complex`, `protein-ezh2-associates-with-protein-phf19`,
   interpretation t199's finding that the PHF19 signature is myeloma-context-specific).
   Its spec contrasts NDMM → PD in RNA-seq TPM over a second, unheld cohort. The record
   labels it a **narrower sub-claim**: the half that makes it a health question (does the
   PRC2 coupling generalise beyond myeloma, `health/meta` plan 0006's
   "weak-generalization" flag) is not representable until a disease vocabulary is bound
   (§6.3), and the stage levels are myeloma's. By C5 `multiple-myeloma` selects it; the
   design does not avoid that by picking another concept.
2. `concept:disease-progression affects protein:EZH2`, as revision 1 proposed. Rejected:
   it kept the proposition out of `multiple-myeloma` only together with a reduction of
   the prescribed term clauses to two, which is an exclusion engineered into the inputs
   (review round 1, P1); under the prescribed clauses it is selected the same.
3. A `health` corpus-local contract with its own estimands (tissue levels, a TPM
   measure) and a GTEx-anchored co-expression claim (`protein:PHF19 associates-with
   protein:EZH2`). The only genuinely cross-disease option, and the right shape for a
   health program; rejected here because it is contract design and vocabulary holding,
   outside a measurement of the project surface. Named in §8 as the follow-up.

**The datasets.** The cohort is Zenodo record 22399365, "Frozen MMRF-CoMMpass count
matrix for RNA-seq differential expression teaching (diagnosis vs. relapse, n=30+30)",
CC-BY-4.0, published 2026-09-05, listed `eligible` in the mm program's roster
(`commpass-open-60-counts`; exposure noted there). Two resources are declared as one
dataset: `mm_counts.csv.gz` (3,172,813 bytes, Zenodo md5 `e18dc9b7…`; raw STAR
`unstranded` counts, GDC data release 46.0, rows keyed by versioned Ensembl gene ids)
and `mm_metadata.csv` (7,637 bytes, md5 `9201e47f…`; columns `file_id, case_id,
barcode, sample_type, condition`). The analysis's third input is the annotation the
counts were produced against, GENCODE release 36's primary annotation
(`gencode.v36.annotation.gtf.gz` from the GENCODE FTP), declared as a second dataset
record. Each sha256 is computed from bytes downloaded to `<task dir>/inputs/`, checked
against Zenodo's md5 or GENCODE's published checksum before the declaration, and the
bytes are then discarded, never held.

**The analysis as the spec's method states it** (frozen, so that the spec is executable
when the inputs are held): TPM per gene from the `unstranded` count by the GDC's own
rule, count divided by gene length in kilobases where gene length is the sum of the
gene's non-overlapping exon bases from the GTF, normalised to a million per sample;
`protein:EZH2` is the row whose Ensembl id without its version suffix is
`ENSG00000106462`; `level:ndmm` is every sample whose `condition` is the diagnosis value
(`diagnostico`) and `level:pd` every sample with the relapse value, both values read and
pinned at preflight; one sample per patient as the source states; a two-group rank
comparison as the mm30 spec's, alpha 0.05. The honest limits: the surface names one
input (C4), so the GTF is declared as a dataset and named by address in the method text
rather than as a `reads` input (filed, §5.8); and the counts are not TPM, so the
transformation is the analysis's first step and is written down here.

The alternative, declaring a desired future dataset with a made-up digest, is rejected:
a fixture digest exercises the machinery and declares nothing.

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

### 4.3 Kernel-only steps and where the evidence lives

A driver under `<task dir>/driver/`: `genesis.py` (world config, the working corpus,
its manifest, admission, the contract copies, `science.toml`), `declare.py` (the two
unheld datasets), `walk.py` (the MCP frames, adapted from the mm30 walk), and the
transcripts under `<task dir>/runs/<timestamp>/`. Both kernel-level steps run **before
the server opens** (C7a): genesis, then the declarations, then one `science mcp serve`
process carries every command of the walk as one attended session. Each kernel-only
step is quoted in the record and filed as a surface gap. The alternative, adding
`science corpus-init` and `science declare` first, is rejected: the milestone measures
the surface as it is.

Retention: `<task dir>` is created at the plan's first run and noted on the task at that
moment (host, path, purpose, owner); the three driver scripts, `science.toml` as
written, and each run's `walk.jsonl` and `serve.stderr` are attached to the task at the
run's end (`tasks attach`, one caption each); the recipes are quoted in the record. The
downloaded inputs are discarded after their digests are recorded. The directory is
accounted for under the retained-item rule at park and at done.

### 4.4 Criterion 7's MCP arm

The driver sends the JSON-RPC frames to `science mcp serve`, as the mm30 walk did, and
the CLI read runs in a fresh process while the server lives. A live coding-agent arm
(the pi probe's shape) is not required by §9.2 and is optional.

### 4.5 Where the record lands

`docs/records/2026-10-26-second-project-milestone.md`, accepted at review round 1. §9.2
says `docs/plans/`; the `docs/records/` directory, where both measurement records now
live, postdates that sentence, and the authority takes a dated amendment saying so
(§8), committed with this revision.

## 5. The design

### 5.1 The reading pass (§9.1)

One bounded pass over `health/meta`, `multiple-myeloma` and the overlap produced:

- **The three coarse queries** (§5.4), with every address read from the records.
- **The first health question** (§4.1, §5.5).
- **The datasets the question needs held:** the declared cohort and the declared
  annotation (§4.1), and nothing else; the vocabulary lists it types under are held by
  the mm30 corpus.
- **The overlap inventory**, for the record: the predecessor dataset entities shared by
  name between the two trees are `depmap` and `tcga`; GTEx is `health/meta`'s only.
  None is held or declared here.

### 5.2 The world

```
<data root>/
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
chain refuses with the entry and the kernel's message; today only `MalformedContract` is
caught (C3), and the chain loader catches both for a bare path as well as a table.
Relative paths resolve as every config path does. Duplicate detection across `contracts`
and `read_contracts` compares the activated contract's identity, as today.

Tests: a chain compiles to the successor's identity and a bare path still parses a
genesis; a chain whose predecessor does not match refuses by name; a successor document
given as a bare path refuses by name rather than erroring; a table missing a key refuses
by name. The framework design §9.1 takes a dated amendment and the README's
configuration paragraph names the shape.

### 5.4 The views

Addresses are read from the records at minting time; the record pins the full values.
Clause semantics: top-level `clauses` union, `all` intersects.

`multiple-myeloma`, exactly as §6.2 prescribes:

```yaml
version: science.view-query.v1
clauses:
  - all: [{closure: {anchor: "dataset:sha256:a6bf229ef0abd8e11f0b7f017cbdb6977395e23d83fb122fcf141f723ba1e448",
                     predicates: [observes, produced_by, assesses, verifies], direction: both}}]
  - all: [{addresses: ["analysis-spec:10e8bfce1aaad8a937a79bfba7cf523ac42b4240ec8b15e20e5b5f450d234714"]}]
  - all: [{references-term: "concept:1q-associated-architecture"}]
  # … one term clause per concept the mm30 contract binds: 285 clauses, generated from
  # the held concept list `dataset:sha256:be3bf183…`, in the list's order …
```

`cancer`: the clauses verbatim.

`health`: the clauses verbatim, plus

```yaml
  - all: [{addresses: ["proposition:concept-disease-stage-affects-protein-ezh2",
                       "analysis-spec:<minted>",
                       "dataset:sha256:<the cohort>",
                       "dataset:sha256:<the annotation>"]}]
```

so that containment holds as a fact about the queries (§6.2): `multiple-myeloma` ⊆
`cancer` = `multiple-myeloma`, and both ⊂ `health`.

The composite `composite:h1-prognosis-fragment` is reached by no clause (C6: `composes`
is not among the four predicates); the record reports it as the coarse form's known
omission rather than widening the predicate list past the spec.

`multiple-myeloma-findings`, a fourth `project` record carrying §8.1's findings-level
selection for criterion 5, since only a project can be previewed (C7): per admitted
assessment one outward closure, plus the spec by address; no composite, since not every
member of the one composite is selected:

```yaml
version: science.view-query.v1
clauses:
  - all: [{closure: {anchor: "assessment:27bd9753ffa77bf6",
                     predicates: [assesses, produced_by, observes, reads, transforms, produces],
                     direction: out}}]
  - all: [{addresses: ["analysis-spec:10e8bfce1aaad8a937a79bfba7cf523ac42b4240ec8b15e20e5b5f450d234714"]}]
```

The health `question`'s own query is the closure clause over the mm30 dataset plus the
same `addresses` clause as `health`'s: its evidence path reaches mm30 facts, and it
names what it introduces.

**A measured alternative, not a replacement.** The prescribed term-clause rule makes the
mm30 contract's vocabulary the project's boundary (C5). The design proposes an
amendment (§8) and measures what it would select: one `question` under
`multiple-myeloma`, named `evidence-bound terms`, whose query replaces the 285 term
clauses by one per concept bound by a proposition the closure clause reaches
(`concept:disease-stage`, read from the stage → PHF19 claim's arguments). It is minted in
the coordination batch (§5.6) and evaluated at the same epoch as the projects; its
selection against `multiple-myeloma`'s is M2's second column.

### 5.5 The health question's records

Minted in the working corpus in this order. The world facts come first, before any
project exists (world kinds need no selection, P2), because `health`'s query names
them and a view cannot be evaluated over an address the world does not hold (C7a):

1. The two dataset declarations (driver, kernel-level, before the server opens): the
   cohort (two resources) and the annotation (one), each with its sha256 digests, a
   title naming the source, an empirical observation (`locator:
   doi:10.5281/zenodo.22399365`; the GENCODE FTP URL) attested by the driver's actor,
   and, on the cohort, a `biology/gene-axis` facet as the mm30 dataset record carries.
   Each address is the content fold over its digests.
2. `claim --subject concept:disease-stage --predicate affects --object protein:EZH2
   --layer causal_effect --polarity positive` → `proposition:concept-disease-stage-affects-protein-ezh2`
   under `mm30/affects-concept-molecular-entity`; `protein:EZH2` resolves `not-consulted`
   under the HGNC binding as PHF19 did. A citing write: the concept vocabulary is read
   from the mm30 mount.
3. `spec --target <the proposition> --dataset <the cohort> --contrast levels --slot 0
   --baseline level:ndmm --comparison level:pd --measure measure:rna-seq-tpm --scale
   additive --reference 0 --identification identification:observational` with the
   method of §4.1 (naming the annotation's address), assumptions, falsification and the
   two shipped rules (`beliefs/outcome-file/v1`, `beliefs/content-identity-equality/v1`),
   `--parameters alpha=0.05` as mm30's walk gave it.
4. The four `project` records (§5.4), under no selection.
5. `project-select health`, `question` (§5.4's query); `project-select cancer`,
   `reuse --source <its address>`; `project-select multiple-myeloma`, `question`
   (`evidence-bound terms`, §5.4).

### 5.6 The walk and its predictions

The schedule is frozen here and copied into the record's §2 before the run; every write
between two epochs is listed, so each epoch's trigger class is a fact of the schedule,
not a reading of the log. Each prediction is marked `confirmed`, `confirmed for another
reason`, or `refuted`; a criterion is marked `met`, `partly met` or `unmet`.

| step | what runs | prediction |
|---|---|---|
| G | `genesis.py`; `declare.py` | the working corpus exists with the pins of §5.2; the chain compiles to `4af7c42…`; two `Declared` datasets in the working corpus |
| S0 | `science mcp serve` opens; `status` | two corpora, each `known`, `live`, `present`, no finding; records in mm30: 18 by kind as C6; in the working corpus: 2 datasets; no current epoch |
| E1 | `science epoch` (**initial**) | `built` over both corpora; the shipped rules install; wall time (M1) |
| W1 | `claim`; `spec` (**evidence**, two citing writes) | both mint; `spec` resolves its vocabulary referents in the mm30 mount and accepts a `Declared` dataset |
| E2 | `science epoch` (**evidence**: W1) | `built`; wall time |
| W2 | `project` ×4, under no selection (**coordination-only**) | four `project` records (P2's genesis path); `next` before E3 is `epoch-stale` |
| E3 | `science epoch` (**coordination-only**: W2) | `built`; wall time. This is the rebuild `beliefs-655c10` asks about |
| R1 | selections at E3 (M2) | `multiple-myeloma` = `cancer`: the stage → PHF19 proposition (closure and term), PHF19 → overall-survival (term), **the EZH2 proposition (term `concept:disease-stage`, C5)**, both runs, the assessment, the verification, `dataset:sha256:a6bf229e…`, `analysis-spec:10e8bfce…`; not the composite, not the vocabulary datasets, not the EZH2 spec, not the declared datasets. `health`: the same plus the EZH2 spec and the two declared datasets. `multiple-myeloma-findings`: the assessment, run `8b1a2401…`, the stage → PHF19 proposition, `dataset:sha256:a6bf229e…`, the spec (5 records) |
| W3 | `project-select health`; `question`; `project-select cancer`; `reuse`; `project-select multiple-myeloma`; `question` (**coordination-only**; the selections are ledger lines) | three mints; `reuse` is one act, the copy's query byte-equal to the source's, its body naming the source address, the source's tip unchanged (M3) |
| E4 | `science epoch` (**coordination-only**: W3) | `built`; wall time |
| E5 | `science epoch` (**none**) | `current`, no build; wall time |
| R2 | `next` under each of the three projects and under none (criterion 4) | `multiple-myeloma` = `cancer` = `health` = unselected: `not-ready: concept:disease-stage affects protein:EZH2`, `not-ready: protein:PHF19 affects concept:overall-survival`, `admitted: concept:disease-stage affects protein:PHF19`; rows in class order then id. Equal rankings everywhere: §9.2's expected difference between `health` and `multiple-myeloma` does not appear (C5), and the criterion is **partly met**: each view renders exactly its selection's propositions, and the sets are the ones predicted here, not the ones §9.2 expected |
| R3 | `evidence-bound terms`'s selection at E4 (M2) | the stage → PHF19 and EZH2 propositions, both runs, assessment, verification, dataset, spec; not PHF19 → overall-survival |
| R4 | `publish-preview --target multiple-myeloma-findings --to <task dir>/runs/<ts>/publish` (criterion 5) | refuses `kernel-refused`, reason `attribution-contract-unpinned` naming corpus `8b5d0c80…` (C7); no closure report. Criterion 5 **unmet**: the refusal is neither of §9.2's permitted outcomes. The record computes both closures of the 5-record selection (M5) |
| R5 | belief, for completeness | `NoBelief(no-directional-outcome)` for the PHF19 proposition |
| C6 | the server exits; two launcher arms, each a fresh `science mcp serve` over the same `science.toml`: one started with cwd the mm program's workspace checkout (`multiple-myeloma`), one with cwd a fresh `mktemp -d` holding a decoy `science.toml`, `science.yaml` and `corpus.yaml`; in each, `project-select health` then `status`, `projects`, `next`; shutdown between them | the two arms' `status`, `projects` and `next` renderings are byte-identical, and identical to the R2 `health` rendering |
| C7 | one server again: over MCP `project-select health`; then CLI `next` in a new process, `next --project multiple-myeloma`, then `projects` | the CLI read observes `health`; the `--project` read observes `multiple-myeloma`; `projects` still marks `health` |

Criterion 3 is **partly met**: the question, its proposition, its spec and the copied
view all exist as predicted; the fact `health` selects and `multiple-myeloma` does not is
the spec and the two datasets, not the proposition.

### 5.7 Measurements

- **M1 epochs.** Every `science epoch` run of the schedule: its trigger class from the
  schedule (`initial`, `evidence`, `coordination-only`, `none`), outcome (`built` or
  `current`), wall time, and the writes between it and the previous one. Coordination-only
  builds (E3, E4) and their cost go to `beliefs-655c10`; the per-change cost to consumer
  limitation 1.
- **M2 explicit entries.** Per view: `addresses` entries, term clauses, closure anchors
  and the records each selects; the prescribed form (285 term clauses) beside the
  evidence-bound form (R3); the records the coarse form omits (the composite). To
  `beliefs-7c98bc` and to the §8 amendment.
- **M3 the fence.** Reported as three separate counts, never summed: research
  questions (1, the health question), same-query reuses (1), and measurement-only
  questions (1, `evidence-bound terms`, which exists for M2 and is not usage); plus
  repairs needed (0 expected) and whether the source changed. The reuse ratio is the
  first two counts alone. To §7's decision; a request to `beliefs` only if the count
  argues for one.
- **M4 command latency.** End-to-end wall time of every write command in the walk, so
  citing writes (`claim`, `spec`) sit beside coordination writes (`project`, `question`,
  `reuse`). It is a latency, not a mount cost: the record does not infer a count of mount
  openings from the code (the read context caches openings per context, and `claim`
  reaches the vocabulary through the resolution snapshot rather than `cited()`), and
  isolating the mount cost would need direct timing this milestone does not add.
- **M5 the two closures.** Of the findings selection (R4's 5 records): the stored-edge
  closure (what `closure_missing` walks, expected complete) and the projection-derived
  closure (§8.1's rule: the run's spec facet, the spec's projection target and declared
  inputs, each assessment's run), listing every identity one reaches and the other does
  not. Expected: the spec is reached by projection and by address only; the vocabulary
  datasets are reached by neither, since the contract binds them, not the spec.
- **M6 the working corpus after the walk:** records by kind, and the ledger lines
  (`project-select`) count.

### 5.8 Findings

Classified `defect`, `design-gap`, `surface-gap`, `corpus-work`, each filed to its lane
(`sci` or `beliefs`) with the record as evidence. Known before the run: the contract
chain (§5.3, `sci`, fixed in this plan); no corpus genesis command (`sci`); no dataset
declaration command (`sci`); `spec` names one input only, so an annotation an analysis
reads cannot be a `reads` input (`sci`, C4); only a project can be previewed or
published, so a level must be a project (`sci`, C7); the `also:` key in the kernel
driver's documents (`beliefs`, informational); the composite outside the coarse form
(`sci`, query design); a relocated replica of the world's own corpus refused as a foreign
publication (`beliefs`, design-gap: the publish act has no notion of a replica the same
person relocated, so no view over the mm30 corpus can be published until it does); the
stored-edge closure narrower than §8.1's projection-derived rule (`beliefs`, with M5);
and the term-clause rule of §6.2 making the typing contract the project boundary (`sci`,
the §8 amendment, with M2).

### 5.9 The record

`docs/records/2026-10-26-second-project-milestone.md`, in the mm30 record's shape:
§1 preflight (C1–C8 as observed, the chain identity check, the pinned `condition`
values, kernel and science commits), §2 the schedule and predictions (§5.6), §3 the
path (recipes and the command table with invocation ids), §4 predictions marked and
each criterion's verdict, §5 findings, §6 measurements (M1–M6), §7 what this decides
(the fence, the two `beliefs` notes, the two proposed amendments). §1–§2 are committed
before the run and the commit named in the record's status line.

## 6. Guarantees

P7 (projects design §10): the milestone record. The loader change carries its own tests
(§5.3). Nothing else in science changes.

## 7. What is left to the builder

- The genesis driver's exact kernel calls (mirror `tests/helpers/world.py`'s
  `build_fixture_world` and `beliefs` `relocate.py`), the actor name, and the
  `gene-axis` facet's field values for the cohort declaration.
- The generator for the 285 term clauses from the held concept list, and the YAML the
  `project` command receives.
- Test names and fixture shape for the chain loader.
- The exact launcher invocation for the two C6 arms.

## 8. What this decides, and the amendments it proposes

- §7's fence: one reuse against one research question is not a pattern; no `beliefs`
  request unless M3 says otherwise.
- `beliefs-7c98bc` and `beliefs-655c10` receive their notes from M2 and M1.
- **Proposed amendment to §6.2's term-clause rule** (not applied; the user's call after
  the run, with M2 as evidence). The rule "one term clause per concept the contract
  binds" selects every proposition typed under the contract, which makes the mm30
  contract's vocabulary the project's boundary: the "contract boundary" §3.1 calls a
  typing fact becomes an organisational one, the thing §6.1 refuses for biology ("there
  is nothing a biology project view would select that the domain does not already
  define"). The replacement would have a project's term clauses name the concepts its
  own evidence binds (those bound by propositions its closure clauses reach), so that a
  view selects by what it has found out, and a new claim joins a project by being asked
  or reached there. The justification stands whether or not the EZH2 proposition is
  selected; the design runs the prescribed rule.
- **Proposed amendment to §9.2 criterion 5**, if `beliefs` keeps refusing a relocated
  replica: the criterion names the attribution refusal as a third outcome, or the
  milestone's dry run moves to a corpus admitted `fresh`. Not applied; filed with the
  finding.
- **Applied amendment**, committed with this revision: §9.2's "leaves a record in
  `docs/plans/`" reads `docs/records/`, dated, accepted at review round 1.
- Criterion 3 is partly met and criterion 5 unmet in this world for the reasons C5 and
  C7 give; both are reported as such, and neither acceptance condition is changed by
  this document.
- The health program's first real question needs what option 3 of §4.1 names: a
  contract with estimands beyond myeloma's and a disease vocabulary. Filed as an idea in
  `sci`, not scoped here.
- The mm program (`mm-a32d58`) holds datasets into this world after this milestone; the
  declared cohort is one it may hold or supersede under its own protocol.
