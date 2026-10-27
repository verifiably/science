# Second project over mm30: health, cancer and multiple-myeloma — record

**Date:** 2026-10-27
**Status:** run 2026-10-27; predictions committed before the live run (`e51e706`); criteria 1, 2, 6 and 7 met, 3 and 4 partly met, 5 unmet (§4.4). The live run, its
marks, findings and measurements are §3–§7.
**Scope:** the milestone of `docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md`
§9.2, as `docs/specs/2026-10-26-second-project-milestone-design.md` (the design) frames it
and `docs/plans/2026-10-26-second-project-milestone.md` (the plan) runs it: one world root
at the user's data location holding the relocated mm30 corpus and a fresh working corpus,
opened as one session; `health`, `cancer`, `multiple-myeloma` and a findings-level
`multiple-myeloma-findings` project; one health question, its same-query copy under
`cancer`, and one measurement-only question. A measurement: its one code change is the
contract-chain loader (`sci-7079e3`, the plan's Task 1); everything else runs through the
commands, with two kernel-level driver steps the design names (genesis, declaration).

Paths: `<data root>` is the directory `SCIENCE_CONFIG` names a file in; `<world>` is
`<data root>/worlds/aec951bc6becacced13df8f7ae6f8abf`; `<task dir>` is the task's
persistent scratch directory, `$WORK_ROOT/science/sci-0d00d2/`; drivers are under
`<task dir>/driver/` and are attached to `sci-0d00d2` at the end.

## 1. Preflight

Written before the live run, after the rehearsal on replicas.

### 1.1 The world as found (design C1–C8)

- **C1.** `<data root>` holds `worlds/` only: no `science.toml`, no `contracts/`. `<world>`
  holds `world/`, `store/`, `anchors/` (the corpus and store head artifacts),
  `relocation.json` and `corpora/mm30/` (corpus `8b5d0c802677ee445e2b9d91ebf5d6a7`,
  admitted `replica-of`, restore and arrival `validated`); no working corpus, no `ops/`.
  The world has published no epoch and holds no rule binding.
- **C1a (found by the rehearsal, not by the reading pass).** The world holds no
  holdings-reducer rule either. `science epoch` installs the four shipped enumeration
  rules and not the reducer; relocation reconstructs a world without it; no science
  command installs it. Without it every holdings read fails `RuleNotHeld`, so every
  citing write (`claim`, `spec`) fails, and the failure reaches the person as
  `internal-error` (rehearsal r2, §1.3). Genesis therefore installs it, by the recipe the
  mm30 record's §3.1 and science's fixture worlds use
  (`install_rule_binding(world, holdings_rule_bundle())`). Filed in §5.
- **C2.** No `science` command creates a corpus or declares an unheld dataset
  (`tools/cli.toml`); genesis and the declarations are kernel-level driver steps, run
  before the server opens.
- **C3.** The mm30 manifest pins `mm30:4af7c4212d482ae60f429526ff5a8a6d4c335f70351a2687cd2062ffdedf437c`.
  The chain cut 22 → cut 31 → current, with the four vocabulary tokens replaced by the
  held lists' addresses (read from the four `mm30 … vocabulary` dataset records) and the
  `also:` line dropped, compiles under the Task 1 loader to that identity (rehearsal
  r1–r3, ra, rb; genesis checks it again on the live world before writing anything).
- **C6.** The mm30 corpus holds 18 records: analysis-spec 1, assessment 1, composite 1,
  dataset 5, holdings-observation 5, proposition 2, run 2, verification 1.
- **C4, C5, C7** were read in the kernel and the queries by the design, and the rehearsal
  agreed with each: the EZH2 spec froze under mm30's one estimand-bearing operator; every
  myeloma view selected the EZH2 proposition through its `concept:disease-stage` term
  clause; and the dry run refused `attribution-contract-unpinned` naming the replica.
- **C8.** The predecessor trees: `cancer/cancer-types/multiple-myeloma` has 260 dataset
  entities, `health/meta` 62; their names overlap in exactly `depmap` and `tcga`; `gtex`
  is `health/meta`'s only.
- **Commits.** science: this branch, `second-project-milestone`, at the commit of this
  record (Task 1 landed at `19738ca`, review fixes `316338a`). beliefs: `741fea1`, its
  working tree carrying an uncommitted `python/uv.lock` edit that is not this task's;
  science's environment uses beliefs as an editable path dependency.
- **The config** genesis writes is §5.2's, with one erratum: §5.2 spreads the
  `contracts` inline table over two lines, which TOML 1.0 (Python's `tomllib`) refuses;
  genesis writes the same table on one line.

### 1.2 The inputs (design §4.1)

Downloaded per attempt into an empty directory, checked against the published md5,
digested, and discarded; the rehearsal's downloads gave:

| resource | bytes | md5 (published) | sha256 |
|---|---|---|---|
| `mm_counts.csv.gz` (Zenodo 22399365) | 3,172,813 | `e18dc9b72619d6473e2274cf3823b395` | `f0f5a328068ad3bf9687e06e71f29c22aa87b72da40089c4ae2d2782f861024d` |
| `mm_metadata.csv` (Zenodo 22399365) | 7,637 | `9201e47ffb0e3900b01fd96a913b56f6` | `12e7bd37ae94fe229323078144c0c9efe84140cac3143b0bad234ed2c3895094` |
| `gencode.v36.annotation.gtf.gz` (GENCODE FTP) | 44,507,458 | `c03931958d4572148650d62eb6dec41a` | `81359865bab048361cbeaf91c9441aac4c700b63978e6691d579d78bf2322d30` |

The metadata's `condition` column holds exactly `diagnostico` (30 rows) and `recidiva`
(30 rows): `level:ndmm` is `diagnostico`, `level:pd` is `recidiva`. The cohort dataset
(both Zenodo resources) is `dataset:sha256:e565a18845914ff4fd1656f1a45f303f723a78f32c758d1fadb1854f899a7dd3`;
the annotation is `dataset:sha256:22bc74180538f1c53fd1e336f3c056c96eae712c5d752ab016cc2baab8967b81`.

**Locators, a deviation found by the rehearsal.** The design gives the cohort's locator
as `doi:10.5281/zenodo.22399365`. The kernel's empirical-observation facet declares the
locator schemes `accession`, `url` and `instrument`, and refused `doi` at the first
`add`, writing nothing (rehearsal r1). The declarations use
`url:https://doi.org/10.5281/zenodo.22399365` and `url:` + the GENCODE FTP URL; the
dataset addresses fold over the digests only and are unaffected. Filed in §5.

### 1.3 The rehearsal and the drills (plan Task 5)

Every driver ran first on disposable replicas of the live world, built by the kernel's
own route (`replicate_root` and `restore_root` against the live world's exported head
artifacts, a fresh world, `admit_arrival` with `ReplicaOf`); the live world's file tree
was hashed before and after each replication and did not change. The replicas live in
the main checkout's gitignored `.work/sci-0d00d2/`, because the kernel's durability
allowlist refuses the task directory's volume (the first r1 attempt, refused in
`replicate_root` before any replica existed).

- **r1** (`364c4921…`): genesis complete (chain and pins as §5.2); declaration refused
  the `doi:` locator (above).
- **r2** (`80666ede…`): genesis, declaration, frozen queries, S0 and E1 (`built`) passed;
  W1's `claim` answered JSON-RPC `-32603 Internal error`, nothing minted; an in-process
  reproduction gave `RuleNotHeld` (C1a).
- **r3** (`6f10ffd5…`, run `20261027T122639Z`): the whole schedule and the arms. Every
  call `ok` except R4, refused as C7 predicts; epochs E1–E4 `built` in 7.35, 7.69, 8.03
  and 10.66 s, E5 `current` in 5.15 s; every view `equivalent` and `complete`; the arms
  all equal. Two of the design's predictions were refuted here and are carried into §2
  beside the originals: R0's `next` before E3 does not refuse `epoch-stale`, it renders
  and marks the stale row `assessed-unevaluated (epoch-stale)`; and a `closure` clause
  never selects its own anchor (the kernel's traversal is start-excluding), so the
  GSE179929 dataset is in no myeloma view and the assessment is not in the findings view.
- **Drill (a)** (`ra`, `1a882eec…`): `walk.py --stop-after W3.select.health`, then a plain
  rerun: W1 and W2 verified by content, the selection re-issued on the new server, the
  question minted, the run completed; its invariants (per view the selected world
  records, `equivalent`, `complete`; per `next-*.txt` the ids, classes and order) equal
  r3's.
- **Drill (b)** (`rb`, `a4a9ce20…`; its first declaration hit Zenodo HTTP 504 and was
  retried): `--crash-before-record W3.question.evidence-bound-terms` (exit 1); the rerun
  exits 3 naming the key and `walk.py <state> --check <key>`; `--check` found the minted
  question; `--reconcile` journaled it after verifying it by content; the rerun completed
  with R3 `equivalent: true`; invariants equal r3's.
- **Drill (c)** (r3's world, a new run, twice): both invocations stop at W1.claim's
  fail-before-write check naming `proposition:concept-disease-stage-affects-protein-ezh2`,
  with stop rows only: no attempt, no server, no epoch.

The drivers as drilled are recorded by sha256 in `<task dir>/drivers-as-drilled.sha256`
and on the task; the live run compares against them before it starts. r3's full walk ran
the walk driver before its second review round's fixes (the fresh-run guard, the
resolved-query manifest check, `--run`); drills (a)–(c) ran the drivers as drilled, and
(a) and (b) each completed the whole schedule.

### 1.4 The reading pass (design §5.1)

The three coarse queries (§2.2), the first health question (design §4.1: *Does disease
stage drive the PRC2 catalytic core (EZH2) where it drives PHF19?*, a narrower sub-claim:
its stage levels are myeloma's), and the datasets it needs held: the cohort and the
annotation of §1.2, declared and not held. The overlap inventory is C8's.

## 2. Schedule and predictions

Each prediction is marked in §4 `confirmed`, `confirmed for another reason`, or
`refuted`; each criterion `met`, `partly met` or `unmet`. Where the rehearsal refuted a
design prediction, both are stated: the design's (**D**) is marked against the live run
as written, and the rehearsal's (**R**) is what this record expects.

### 2.1 The schedule

Nothing runs between steps but what this table lists; every write between two epochs is
listed, so each epoch's trigger class is a fact of the schedule.

| key | what runs | prediction |
|---|---|---|
| G | `genesis.py`: checks (world, chain, pins in a temporary root) before any write; contracts, `science.toml`, the working corpus (`init_corpus_root`, `adopt_manifest`, `admit(Fresh())`), the holdings reducer | chain `mm30:4af7c421…`; pins science `52a43993…`, biology `24bcec43…`, mm30 `4af7c421…`, coordination `b2386628…`; a fresh corpus id |
| D | `declare.py`: both nodes validated, then added | the two addresses of §1.2, equal to the rehearsal's |
| T | `terms.py`: the six templates | the `MANIFEST` equal to r3's (§2.2) |
| S0 | `science mcp serve` opens; `status` | two corpora `known=True live=True present=True`; `No current epoch.`; working corpus `dataset: 2`; mm30 as C6 |
| E1 | `science epoch` (**initial**: the declarations) | `built` |
| W1.claim | `claim concept:disease-stage affects protein:EZH2`, `causal_effect`, `positive` (**evidence**) | `proposition:concept-disease-stage-affects-protein-ezh2` under `mm30/affects-concept-molecular-entity` |
| W1.spec | `spec` over the cohort, levels `ndmm`→`pd` on slot 0, `measure:rna-seq-tpm` additive reference 0, observational, the two shipped rules, `alpha=0.05` (**evidence**) | `analysis-spec:5132014c5feecd52d09c801c220074bae2fd7677ec009b1a0228186602763036` (content-derived; equal in r3, ra, rb) |
| Q1 | the placeholder in `health.yaml` and `health-question.yaml` replaced by the spec's address, into `queries-resolved/` | projection hashes as §2.2 |
| E2 | `science epoch` (**evidence**: W1) | `built` |
| W2.project.* | `project` ×4 under no selection, in the order `multiple-myeloma`, `cancer`, `health`, `multiple-myeloma-findings` (**coordination-only**) | four `project` records |
| R0 | `next`, before E3 | **D:** `epoch-stale`. **R:** renders; the EZH2 and PHF19 → overall-survival rows `not-ready`, the stage → PHF19 row `assessed-unevaluated (epoch-stale)` |
| E3 | `science epoch` (**coordination-only**: W2) | `built`; the rebuild `beliefs-655c10` asks about |
| R1.* | each project's selection at E3, its stored query read back and evaluated | §2.3 |
| W3 | `project-select health`; `question` (health-question); `project-select cancer`; `reuse --source` the question; `project-select multiple-myeloma`; `question` (`evidence-bound terms`) (**coordination-only**) | three mints; the reuse's stored query projection equal to its source's, its body naming the source's pinned address |
| E4 | `science epoch` (**coordination-only**: W3) | `built` |
| E5 | `science epoch` (**none**) | `current`, the same packaging identity as E4 |
| R2.* | `project-select <p>` then `next`, for `multiple-myeloma`, `cancer`, `health`; then `project-select --clear` and `next` | §2.4 |
| R3.* | the selections of the health question, its copy, and `evidence-bound terms` at E4 | §2.3 |
| R4 | `publish-preview --target multiple-myeloma-findings --to <run dir>/publish` | `refused [kernel-refused] attribution-contract-unpinned: 8b5d0c802677ee445e2b9d91ebf5d6a7`; no closure report |
| R5 | `belief --proposition proposition:concept-disease-stage-affects-protein-phf19` | `NoBelief`, reason `no-directional-outcome` |
| S1 | `status` | working corpus: analysis-spec 1, dataset 2, project 4, proposition 1, question 3; an epoch equal to E4's |
| C6 | arms: a fresh server per arm over the same `science.toml`, cwd the mm program's checkout, then a temporary directory holding a decoy `science.toml`, `science.yaml` and `corpus.yaml`; in each `project-select health` over MCP, then CLI `status`, `projects`, `next` | the two arms byte-identical, and both `next` equal to R2's `health` |
| C7 | one server, cwd the worktree's `python/`: `project-select health` over MCP, then CLI `next`, `next --project multiple-myeloma`, `projects` in fresh processes | `next` equal to R2's `health`; the `--project` read equal to R2's `multiple-myeloma`; `projects` marks `health` `(selected)` |

The journal keys and the live-run contract are the plan's (Global Constraints, Task 4).
The rows C6 and C7 are the design's names for the arms of criteria 6 and 7, unrelated to
the constraints C1–C8 of §1.1.

### 2.2 The frozen queries

Six templates, written once per state by `terms.py`, every address read from a record.
`multiple-myeloma.yaml` and `cancer.yaml` are byte-identical. Raw file sha256 (after the
placeholder substitution, as `queries-resolved/MANIFEST` records it) and the projection
sha256 (the serialization `science.coordination.query_digest` uses), both predicted equal
to r3's:

| query | raw sha256 | projection sha256 | clauses |
|---|---|---|---|
| `multiple-myeloma` | `f846932b…` | `a7f42011…` | the closure (anchor `dataset:sha256:a6bf229e…`, `observes`, `produced_by`, `assesses`, `verifies`, both directions); the mm30 spec `analysis-spec:10e8bfce…` by address; 285 `references-term` clauses, one per line of the held concept list (`sha256:c7e45f81…`, the mm30 record's P4), in its order |
| `cancer` | `f846932b…` | `a7f42011…` | `multiple-myeloma`'s verbatim |
| `health` | `bbe86645…` | `e7824d0d…` | `multiple-myeloma`'s, plus one `addresses` clause: the EZH2 proposition, the EZH2 spec, the cohort, the annotation |
| `multiple-myeloma-findings` | `1d009c2f…` | `02a9932e…` | the closure from `assessment:27bd9753ffa77bf6` outward over `assesses`, `produced_by`, `observes`, `reads`, `transforms`, `produces`; the mm30 spec by address |
| `evidence-bound-terms` | `7f9301c0…` | `31c8ff33…` | the closure and the mm30 spec, as `multiple-myeloma`; one `references-term`, `concept:disease-stage`, read from the stage → PHF19 claim's first argument |
| `health-question` | `66d003d6…` | `10f605d3…` | the closure, and `health`'s `addresses` clause |

`multiple-myeloma.yaml` in full:

```yaml
version: science.view-query.v1
clauses:
- all:
  - closure:
      anchor: dataset:sha256:a6bf229ef0abd8e11f0b7f017cbdb6977395e23d83fb122fcf141f723ba1e448
      predicates:
      - observes
      - produced_by
      - assesses
      - verifies
      direction: both
- all:
  - addresses:
    - analysis-spec:10e8bfce1aaad8a937a79bfba7cf523ac42b4240ec8b15e20e5b5f450d234714
- all:
  - references-term: concept:1q-associated-architecture
- all:
  - references-term: concept:1q-gain
- all:
  - references-term: concept:1q21
- all:
  - references-term: concept:3d-genome
- all:
  - references-term: concept:8q-gain
- all:
  - references-term: concept:acquired-secondary-events
- all:
  - references-term: concept:age
- all:
  - references-term: concept:aged-niche-fitness-landscape
- all:
  - references-term: concept:aneuploidy
- all:
  - references-term: concept:anti-cd38-backbone
- all:
  - references-term: concept:ap1-chromatin-memory
- all:
  - references-term: concept:ap1-niche-arm
- all:
  - references-term: concept:ap1-null-candidate-arms
- all:
  - references-term: concept:ap1-stress-arm
- all:
  - references-term: concept:ap1-stress-niche-balance
- all:
  - references-term: concept:apparent-basin-depth
- all:
  - references-term: concept:attractor-landscape
- all:
  - references-term: concept:autophagy-compensation
- all:
  - references-term: concept:baseline-bcma-expression
- all:
  - references-term: concept:baseline-gprc5d-expression
- all:
  - references-term: concept:baseline-secondary-events
- all:
  - references-term: concept:baseline-subtype-architecture
- all:
  - references-term: concept:baseline-treatment
- all:
  - references-term: concept:basin-position
- all:
  - references-term: concept:bcl2-apobec-architecture
- all:
  - references-term: concept:bcl2-dependency-state
- all:
  - references-term: concept:bcl2-mcl1-ratio
- all:
  - references-term: concept:bcma-antigen-loss
- all:
  - references-term: concept:bcma-bispecific
- all:
  - references-term: concept:bcma-car-t
- all:
  - references-term: concept:belantamab-bvd-regimen
- all:
  - references-term: concept:benchmarking
- all:
  - references-term: concept:bh3-profiling
- all:
  - references-term: concept:biomarker
- all:
  - references-term: concept:biophysics
- all:
  - references-term: concept:biosynthetic-infrastructure
- all:
  - references-term: concept:bmsc-adhesion
- all:
  - references-term: concept:bone-marrow-niche
- all:
  - references-term: concept:bortezomib-regimen
- all:
  - references-term: concept:bridging-therapy
- all:
  - references-term: concept:bulk-deconvolution-proxy
- all:
  - references-term: concept:bulk-expression
- all:
  - references-term: concept:cal3-generic-prognostic-control
- all:
  - references-term: concept:cam-dr-resistance
- all:
  - references-term: concept:cancer-testis-antigens
- all:
  - references-term: concept:car-t-persistence-surrogates
- all:
  - references-term: concept:carfilzomib-regimen
- all:
  - references-term: concept:causal-dag
- all:
  - references-term: concept:cd138-selection
- all:
  - references-term: concept:cell-cycle
- all:
  - references-term: concept:cell-cycle-inhibitor-silencing
- all:
  - references-term: concept:cell-line-models
- all:
  - references-term: concept:cell-of-origin
- all:
  - references-term: concept:cell-state
- all:
  - references-term: concept:cell-state-composition
- all:
  - references-term: concept:cell-state-fitness
- all:
  - references-term: concept:cell-type-composition
- all:
  - references-term: concept:centrosome
- all:
  - references-term: concept:chr8p
- all:
  - references-term: concept:chromatin
- all:
  - references-term: concept:chromosomal-enrichment
- all:
  - references-term: concept:chromosomal-instability
- all:
  - references-term: concept:chromosome-territories
- all:
  - references-term: concept:clinical-immunology-covariates
- all:
  - references-term: concept:clinical-phenotype
- all:
  - references-term: concept:clinical-trials
- all:
  - references-term: concept:clonal-evolution
- all:
  - references-term: concept:clonal-hematopoiesis
- all:
  - references-term: concept:co-occurring-events
- all:
  - references-term: concept:comorbidities
- all:
  - references-term: concept:confounding
- all:
  - references-term: concept:copy-number-alteration
- all:
  - references-term: concept:corepressor
- all:
  - references-term: concept:covariance
- all:
  - references-term: concept:crab-criteria
- all:
  - references-term: concept:crbn-e3-ligase-function
- all:
  - references-term: concept:crbn-enhancer-methylation
- all:
  - references-term: concept:crbn-imid-predictive-estimand
- all:
  - references-term: concept:crbn-loss-of-function
- all:
  - references-term: concept:crbn-promoter
- all:
  - references-term: concept:cross-arm-predictive-estimand
- all:
  - references-term: concept:cross-platform-replication
- all:
  - references-term: concept:cta-chrxp-program
- all:
  - references-term: concept:cytogenetic-risk
- all:
  - references-term: concept:cytogenetics
- all:
  - references-term: concept:dataset-inclusion
- all:
  - references-term: concept:del-17p
- all:
  - references-term: concept:dis3-mutation
- all:
  - references-term: concept:disease-progression
- all:
  - references-term: concept:disease-severity-index
- all:
  - references-term: concept:disease-stage
- all:
  - references-term: concept:dnds-stability
- all:
  - references-term: concept:dnmt-inhibitor
- all:
  - references-term: concept:driver-mutation
- all:
  - references-term: concept:drug-sensitivity
- all:
  - references-term: concept:drug-toxicity
- all:
  - references-term: concept:duration-of-response
- all:
  - references-term: concept:dynamical-systems
- all:
  - references-term: concept:e2f-family
- all:
  - references-term: concept:eif4f-dependency
- all:
  - references-term: concept:eif4f-initiation-arm
- all:
  - references-term: concept:endeavor-cross-pi-predictive-estimand
- all:
  - references-term: concept:enhancer
- all:
  - references-term: concept:epigenome
- all:
  - references-term: concept:event-ordering
- all:
  - references-term: concept:evolutionary-state
- all:
  - references-term: concept:extramedullary-disease
- all:
  - references-term: concept:fda-cdx-immune-fitness-biomarker-absence
- all:
  - references-term: concept:fda-cdx-pi-biomarker-absence
- all:
  - references-term: concept:fda-clinical-hold
- all:
  - references-term: concept:first-relapse
- all:
  - references-term: concept:fitness-selection
- all:
  - references-term: concept:founding-event
- all:
  - references-term: concept:g2m-phase
- all:
  - references-term: concept:gain-1q-negative
- all:
  - references-term: concept:gdsc2-bortezomib-enrichment
- all:
  - references-term: concept:gene-dosage-effect
- all:
  - references-term: concept:gene-expression
- all:
  - references-term: concept:gene-ranking
- all:
  - references-term: concept:gene-signature
- all:
  - references-term: concept:germinal-center
- all:
  - references-term: concept:global-transcriptional-upregulation
- all:
  - references-term: concept:glycolysis
- all:
  - references-term: concept:gprc5d-antigen-loss
- all:
  - references-term: concept:gprc5d-bispecific
- all:
  - references-term: concept:h3k27me3
- all:
  - references-term: concept:hexosamine-pathway
- all:
  - references-term: concept:high-risk-relapse-identity
- all:
  - references-term: concept:hopfield-basin-energy
- all:
  - references-term: concept:hyperdiploidy
- all:
  - references-term: concept:hypoxia
- all:
  - references-term: concept:identifiability
- all:
  - references-term: concept:igh-translocation-lineage
- all:
  - references-term: concept:ikzf-bypass-mutation
- all:
  - references-term: concept:ikzf-degradation
- all:
  - references-term: concept:imid-comparator-evidence
- all:
  - references-term: concept:imid-refractoriness
- all:
  - references-term: concept:imid-regimen
- all:
  - references-term: concept:immune-escape
- all:
  - references-term: concept:immune-evasion
- all:
  - references-term: concept:immune-microenvironment-state
- all:
  - references-term: concept:immunotherapy
- all:
  - references-term: concept:infection
- all:
  - references-term: concept:interferon-signaling
- all:
  - references-term: concept:iss-stage
- all:
  - references-term: concept:ixazomib-regimen
- all:
  - references-term: concept:jnk-apoptosis-arm
- all:
  - references-term: concept:latent-evolutionary-state
- all:
  - references-term: concept:latent-variable
- all:
  - references-term: concept:line-of-therapy
- all:
  - references-term: concept:longitudinal-sampling
- all:
  - references-term: concept:maf-lineage-arm
- all:
  - references-term: concept:mapk-erk-readout
- all:
  - references-term: concept:mapk-signaling
- all:
  - references-term: concept:measured-expression
- all:
  - references-term: concept:mechanism
- all:
  - references-term: concept:meta-analysis-method
- all:
  - references-term: concept:midas-iberdomide-arm
- all:
  - references-term: concept:minimal-residual-disease
- all:
  - references-term: concept:mitochondrial-redox-program
- all:
  - references-term: concept:mitosis
- all:
  - references-term: concept:mitra-innate-pi-sensitivity-signature
- all:
  - references-term: concept:molecular-subtypes
- all:
  - references-term: concept:mrd-negativity
- all:
  - references-term: concept:mtor-signaling
- all:
  - references-term: concept:mulligan-innate-pi-sensitivity-signature
- all:
  - references-term: concept:mutation-landscape
- all:
  - references-term: concept:mutational-burden
- all:
  - references-term: concept:mxd-family
- all:
  - references-term: concept:myc-high-state
- all:
  - references-term: concept:myc-rearrangement
- all:
  - references-term: concept:natural-experiment
- all:
  - references-term: concept:neutral-drift
- all:
  - references-term: concept:nfkb-pathway-state
- all:
  - references-term: concept:niche-fit-clone
- all:
  - references-term: concept:nk-cell-fitness
- all:
  - references-term: concept:non-1q-architecture
- all:
  - references-term: concept:non-1q-driver
- all:
  - references-term: concept:non-pi-comparator
- all:
  - references-term: concept:nras-mutation
- all:
  - references-term: concept:nucleolar-stress
- all:
  - references-term: concept:null-hypothesis
- all:
  - references-term: concept:other-1q-drivers
- all:
  - references-term: concept:other-high-risk-lesions
- all:
  - references-term: concept:other-phf19-regulators
- all:
  - references-term: concept:overall-response-rate
- all:
  - references-term: concept:overall-survival
- all:
  - references-term: concept:p53-pathway
- all:
  - references-term: concept:patient-age
- all:
  - references-term: concept:patient-survival
- all:
  - references-term: concept:penta-refractory
- all:
  - references-term: concept:pentose-phosphate-pathway
- all:
  - references-term: concept:phase-3-trial
- all:
  - references-term: concept:pi-refractoriness
- all:
  - references-term: concept:placebo-vd-regimen
- all:
  - references-term: concept:plasma-cell
- all:
  - references-term: concept:plasma-cell-lineage-extension
- all:
  - references-term: concept:plasmablast-program-retention
- all:
  - references-term: concept:platform-heterogeneity
- all:
  - references-term: concept:platform-technology
- all:
  - references-term: concept:polycomb-epigenetic-architecture
- all:
  - references-term: concept:pomalidomide-dex-regimen
- all:
  - references-term: concept:population-genetics
- all:
  - references-term: concept:post-treatment-neutrality
- all:
  - references-term: concept:prc2-complex
- all:
  - references-term: concept:prc2-inhibition
- all:
  - references-term: concept:predictive-biomarker
- all:
  - references-term: concept:pretreatment-positive-selection
- all:
  - references-term: concept:primary-molecular-lineage
- all:
  - references-term: concept:prior-bcma-class-exposure
- all:
  - references-term: concept:prognosis
- all:
  - references-term: concept:progression-free-survival
- all:
  - references-term: concept:proliferation-rate
- all:
  - references-term: concept:proteasome-subunit-expression
- all:
  - references-term: concept:proteasome-subunit-upregulation
- all:
  - references-term: concept:proteostasis-survival-state
- all:
  - references-term: concept:quasi-potential
- all:
  - references-term: concept:randomized-controlled-trial
- all:
  - references-term: concept:ratchet-strength
- all:
  - references-term: concept:redox-gsta4-bin
- all:
  - references-term: concept:relapse
- all:
  - references-term: concept:relapse-subtype
- all:
  - references-term: concept:ribosomal-proteins
- all:
  - references-term: concept:ribosome
- all:
  - references-term: concept:ribosome-biogenesis
- all:
  - references-term: concept:ribosomopathy
- all:
  - references-term: concept:risk-stratification
- all:
  - references-term: concept:rna-polymerase-i
- all:
  - references-term: concept:rpl-family
- all:
  - references-term: concept:rps-family
- all:
  - references-term: concept:s-phase
- all:
  - references-term: concept:secondary-genomic-drivers
- all:
  - references-term: concept:shared-late-state-program
- all:
  - references-term: concept:signaling
- all:
  - references-term: concept:single-cell-immune-profiling
- all:
  - references-term: concept:snorna
- all:
  - references-term: concept:stage-treatment-selection
- all:
  - references-term: concept:state-commitment-entropy
- all:
  - references-term: concept:stdmetafor-ranking
- all:
  - references-term: concept:subclonal-architecture
- all:
  - references-term: concept:subclonal-resistance-timing
- all:
  - references-term: concept:subclone-bme-interaction-state
- all:
  - references-term: concept:subclones
- all:
  - references-term: concept:sumz-ranking
- all:
  - references-term: concept:super-enhancer
- all:
  - references-term: concept:suppressive-myeloid-skewing
- all:
  - references-term: concept:swog-s0777-predictive-estimand
- all:
  - references-term: concept:symptom-clusters
- all:
  - references-term: concept:symptoms
- all:
  - references-term: concept:t-11-14
- all:
  - references-term: concept:t-14-16
- all:
  - references-term: concept:t-4-14
- all:
  - references-term: concept:t-cell-engager-bispecific
- all:
  - references-term: concept:t-cell-exhaustion
- all:
  - references-term: concept:t-cell-fitness-state
- all:
  - references-term: concept:target-antigen-expression
- all:
  - references-term: concept:terminal-attractor
- all:
  - references-term: concept:therapy-resistance
- all:
  - references-term: concept:therapy-selection-pressure
- all:
  - references-term: concept:tp53-len-pressure-candidate
- all:
  - references-term: concept:transcription
- all:
  - references-term: concept:transcription-factor-regulation
- all:
  - references-term: concept:transcription-factors
- all:
  - references-term: concept:transcriptional-reprogramming
- all:
  - references-term: concept:transition-event
- all:
  - references-term: concept:translation-program
- all:
  - references-term: concept:treatment-benefit
- all:
  - references-term: concept:treatment-era
- all:
  - references-term: concept:treatment-perturbation
- all:
  - references-term: concept:treatment-regime-filter
- all:
  - references-term: concept:treatment-resistance
- all:
  - references-term: concept:treatment-response
- all:
  - references-term: concept:treg-infiltration
- all:
  - references-term: concept:triple-class-refractory
- all:
  - references-term: concept:tumor-burden
- all:
  - references-term: concept:tumor-heterogeneity
- all:
  - references-term: concept:tumor-microenvironment
- all:
  - references-term: concept:tumor-purity
- all:
  - references-term: concept:ubels-stlsig-pi-benefit-signature
- all:
  - references-term: concept:unfolded-protein-response
- all:
  - references-term: concept:unfolded-protein-response-capacity
- all:
  - references-term: concept:upregulation-mechanism
- all:
  - references-term: concept:venetoclax-dex-regimen
- all:
  - references-term: concept:venetoclax-vd-regimen
- all:
  - references-term: concept:within-hd-subcluster
```

### 2.3 The selections

Read back from each minted record and evaluated at the current epoch (R1 at E3, R3 at
E4). Every row is predicted `equivalent: true` (the stored projection equals the input
file's) and `complete: true` with nothing absent or unresolved. Short forms: *EZH2* is
the EZH2 proposition, *PHF19* the stage → PHF19 proposition, *OS* the PHF19 →
overall-survival proposition, *runs* the two mm30 runs, *A* the assessment, *V* the
verification, *S30* the mm30 spec, *S-EZH2* the EZH2 spec, *G* `dataset:sha256:a6bf229e…`
(GSE179929), *cohort* and *annotation* the declared datasets.

| view | D (design §5.6) | R (rehearsal r3, ra, rb) |
|---|---|---|
| `multiple-myeloma` (R1) | PHF19, OS, EZH2, runs, A, V, G, S30 (9) | PHF19, OS, EZH2, runs, A, V, S30 (8): not G, the closure's anchor |
| `cancer` (R1) | as `multiple-myeloma` | as `multiple-myeloma` |
| `health` (R1) | `multiple-myeloma`'s plus S-EZH2, cohort, annotation (12) | `multiple-myeloma`'s plus S-EZH2, cohort, annotation (11) |
| `multiple-myeloma-findings` (R1) | A, run `8b1a2401…`, PHF19, G, S30 (5) | run `8b1a2401…`, PHF19, G, S30 (4): not A, the closure's anchor |
| health question (R3) | (not stated) | EZH2, PHF19, runs, A, V, S-EZH2, cohort, annotation (9) |
| its copy under `cancer` (R3) | equal to the question's | equal to the question's |
| `evidence-bound terms` (R3) | PHF19, EZH2, runs, A, V, G, S30 (8) | PHF19, EZH2, runs, A, V, S30 (7): not G |

Never selected by any view: the composite (C6), the four vocabulary datasets, and
GSE179929's holdings observations.

### 2.4 The `next` renderings

Under each project the rendering opens with a `selection:` block naming that project's
address pinned to its revision, its name, `complete: true`, `absent: none`, the world id
and each corpus's state digest, which are this run's own; the unselected rendering has no
such block. The `propositions:` block is predicted byte-identical under all four:

```
propositions:
  proposition:concept-disease-stage-affects-protein-ezh2: not-ready: concept:disease-stage affects protein:EZH2
  proposition:protein-phf19-affects-concept-overall-survival: not-ready: Higher PHF19 expression predicts shorter overall survival — inquiry 0001-prognosis's spine, minted here with no evidence.
  proposition:concept-disease-stage-affects-protein-phf19: admitted: concept:disease-stage affects protein:PHF19
```

Equal rankings everywhere: §9.2's expected difference between `health` and
`multiple-myeloma` does not appear, because under the prescribed term clauses the EZH2
proposition is a `multiple-myeloma` proposition (design C5).

### 2.5 The criteria

| criterion (projects design §9.2) | predicted |
|---|---|
| 1. one world root, the relocated mm30 corpus and a fresh working corpus, one session writing one and reading both | **met** (G, S0) |
| 2. three projects with §6.2's queries, at least one mm30 proposition selected by all three at one epoch | **met** (R1: PHF19 and OS in all three) |
| 3. a `health` question reaching mm30 facts, its same-query copy under `cancer`, a new proposition and a spec over an unheld dataset, so that `health` selects a fact `multiple-myeloma` does not | **partly met**: everything exists as required; the fact `health` alone selects is the spec and the two datasets, not the proposition (C5) |
| 4. `next` under each project and none renders exactly its selection's propositions in class order, the expected sets stated before | **partly met**: each rendering is its selection's propositions in class order and equals §2.4; the sets are this record's, not the ones §9.2 expected (`multiple-myeloma` holds the EZH2 proposition too) |
| 5. a dry run of `multiple-myeloma` at the findings level reporting its selection and closure, or refusing `closure-incomplete` | **unmet**: the dry run refuses on attribution (C7), neither permitted outcome |
| 6. sessions opened inside the mm workspace and in an unrelated directory read identically | **met** (C6 arms) |
| 7. an MCP `project-select`, then a CLI `next` in a new process, observing the selection | **met** (C7 arm) |

Should a live declared address differ from §1.2's, the downloaded bytes differed from the
rehearsal's; that would itself be a finding, and the queries' `MANIFEST` would then
differ in `health.yaml` and `health-question.yaml` only.

## 3. The path

Run 2026-10-27, 12:40–12:44Z, on the live world: genesis, the declarations and the frozen
queries from the drivers as drilled (their sha256s compared before the first write), then
one `science mcp serve` process for the walk (run `<task dir>/state/live/runs/20261027T124235Z`),
then the arms. No step stopped: there was no resume and no reconcile. One earlier
invocation of the walk failed at exit 127 on a mistyped interpreter path before any
process or run directory existed.

### 3.1 The recipes

**Genesis** (`genesis.py`), every check before the first write: the world opens read-only
under the given id (`open_world_read`) and holds no working corpus, `science.toml` or
contracts; the four vocabulary addresses are read from the mm30 dataset records titled
`mm30 … vocabulary`; the three contract documents are copied from `beliefs`
`python/tools/reproduction/` without their `also:` line and with the four tokens replaced,
into a temporary data root, where `load_contract_chain` and `load_config` must give the
mm30 manifest's pins. Then, for real: the documents under `<data root>/contracts/mm30/`,
`science.toml` (§1.1's erratum), and

```python
init_corpus_root(cfg.write_root, authority=AUTHORITY)
open_corpus(cfg.write_root, authority=AUTHORITY, profile=cfg.profile).adopt_manifest(profile=CorpusPins(
    science_contract="science:" + cfg.profile.base_contract_identity,
    domains={ns: f"{ns}:{identity}" for ns, identity in cfg.profile.activated_contracts.items()},
))
open_world(cfg.world, authority=AUTHORITY).admit(cfg.write_root, provenance=Fresh())
install_rule_binding(open_world(cfg.world, authority=AUTHORITY), holdings_rule_bundle())
```

with `AUTHORITY = Authority(WritePermit.full(), "sci-0d00d2-driver")`. Output: the working
corpus `4b1c238d06cf7fa18def5ea2554d4f16`, pins science `52a43993…`, biology `24bcec43…`,
mm30 `4af7c421…`, coordination `b2386628…`, and the holdings-reducer binding (rule
`0a0ea45c…`, implementation `f03e496b…`).

**Declaration** (`declare.py`): each input downloaded into an empty directory, its md5
checked, digested and discarded; both nodes built, then both validated (the profile's
document checks, the writer's facet-payload checks, and no record at either address)
before either is added:

```python
stored.dataset_node(title=title,
                    resources=[{"name": r["name"], "digest": "sha256:" + r["sha256"]} for r in resources],
                    empirical_observation={"locator": locator, "attested_by": "sci-0d00d2-driver"},
                    domain_facets=domain_facets)          # the cohort: {"biology/gene-axis": {"axis": "rows", "namespace": "Ensembl"}}
open_corpus(cfg.write_root, authority=AUTHORITY, profile=cfg.profile).add(node)
```

**The selection read** (`selections.py`): the minted record resolved by its returned
address (`resolve_one`), its stored query read back (`stored_query`), its projection
hashed as `query_digest` does and compared with the input file's, and evaluated over the
current epoch's world view through the kernel's read-only door:

```python
world = open_world_read(cfg.world)
published = current_epoch(world)
selection = evaluate_query(open_world_view(world, published), stored_query(tip))
```

**Rehearsal replication** (`rehearsal.py`), the `beliefs` relocation recipe with the live
world as the source: `replicate_root` and `restore_root` of `corpora/mm30` and `store`
against the live world's `anchors/*.head`, a fresh `init_world_root`, `admit_arrival` with
`ReplicaOf(8b5d0c80…)`; the live world's file tree hashed before and after.

**The placeholder** (journal key `Q1`): `health.yaml` and `health-question.yaml` carry
`analysis-spec:<minted>` until W1.spec returns; the walk copies the templates to
`queries-resolved/` and substitutes the spec's address. Journaled hashes: `health.yaml`
raw `bbe86645…`, projection `e7824d0d…`; `health-question.yaml` raw `66d003d6…`,
projection `10f605d3…`; both equal to the rehearsal's.

### 3.2 The commands

Every call one JSON-RPC `tools/call` frame (`walk.jsonl`); every epoch `science epoch` in
a fresh process; seconds are end to end at the driver. The server wrote nothing to stderr.

| key | command | invocation | minted or result | seconds |
|---|---|---|---|---|
| S0 | `status` | `880c27c5…` | read | 0.04 |
| E1 | `science epoch` | — | `built` `53776e885678bbc9…` | 1.66 |
| W1.claim | `claim` | `bf748262…` | `proposition:concept-disease-stage-affects-protein-ezh2` | 0.31 |
| W1.spec | `spec` | `92d259d4…` | `analysis-spec:5132014c5feecd52d09c801c220074bae2fd7677ec00…` | 0.36 |
| E2 | `science epoch` | — | `built` `bda2592890ea1e6c…` | 1.44 |
| W2.project.multiple-myeloma | `project` | `10693608…` | `coord:66ab99117a2bd1b491175d0d2c612ac2` | 0.22 |
| W2.project.cancer | `project` | `5d3ce216…` | `coord:ef2b7fe9b5a8b6b35c8657b645ed0db2` | 0.23 |
| W2.project.health | `project` | `c3d2eacf…` | `coord:4dbcb70467a87cd727cc6303cbd697a2` | 0.23 |
| W2.project.multiple-myeloma-findings | `project` | `02d6524a…` | `coord:04d558cc1eb479ea7fcf00c53430b00b` | 0.15 |
| R0.next-stale | `next` | `f809b67e…` | read | 1.14 |
| E3 | `science epoch` | — | `built` `cd1f59f2bf868bd7…` | 1.91 |
| W3.select.health | `project-select` | `8064dd27…` | selected `health` | 0.29 |
| W3.question.health | `question` | `8f2ebf30…` | `coord:4dbcb70467a87cd727cc6303cbd697a2/3cffd9be7ceb0e8655d…` | 0.19 |
| W3.select.cancer | `project-select` | `fb819ac6…` | selected `cancer` | 0.28 |
| W3.reuse | `reuse` | `7e634058…` | `coord:ef2b7fe9b5a8b6b35c8657b645ed0db2/f1cc8f85f03d6e7caf9…` | 0.25 |
| W3.select.multiple-myeloma | `project-select` | `4f0754a3…` | selected `multiple-myeloma` | 0.28 |
| W3.question.evidence-bound-terms | `question` | `2de91a87…` | `coord:66ab99117a2bd1b491175d0d2c612ac2/83ba85bda606da218a2…` | 0.20 |
| E4 | `science epoch` | — | `built` `a854308b9d585ca7…` | 1.94 |
| E5 | `science epoch` | — | `current` `a854308b9d585ca7…` | 1.11 |
| R2.multiple-myeloma.select | `project-select` | `07db7eea…` | selected `multiple-myeloma` | 0.30 |
| R2.multiple-myeloma | `next` | `a11d1fef…` | read | 1.80 |
| R2.cancer.select | `project-select` | `684aaee4…` | selected `cancer` | 0.27 |
| R2.cancer | `next` | `b219d209…` | read | 1.78 |
| R2.health.select | `project-select` | `674284b2…` | selected `health` | 0.30 |
| R2.health | `next` | `44ff2c3d…` | read | 1.80 |
| R2.unselected.select | `project-select` | `4e7313da…` | selected `none` | 0.01 |
| R2.unselected | `next` | `d7e65a85…` | read | 1.34 |
| R4 | `publish-preview` | `5ef3ec68…` | refused `kernel-refused` | 0.55 |
| R5 | `belief` | `ba114201…` | read | 1.09 |
| S1 | `status` | `23467dd5…` | read | 0.15 |

R1 and R3 are kernel reads (§3.1), not commands. The arms (`arms/`): three fresh servers,
each with `project-select health` over MCP, then CLI reads in fresh processes.

## 4. Predictions, marked

### 4.1 The schedule

| key | observed | mark |
|---|---|---|
| G | chain `4af7c421…`, the four pins of §2.1, working corpus `4b1c238d…`, the reducer installed (`genesis-progress.json`) | confirmed |
| D | cohort `dataset:sha256:e565a188…`, annotation `dataset:sha256:22bc7418…`, equal to the rehearsal's (`declared.json`) | confirmed |
| T | `queries/MANIFEST` equal to r3's | confirmed |
| S0 | two corpora `known=True live=True present=True`; `No current epoch.`; working corpus `dataset: 2`; mm30 as C6 (`status-initial.txt`) | confirmed |
| E1 | `built` `53776e88…` (`epochs.json`) | confirmed |
| W1.claim | `proposition:concept-disease-stage-affects-protein-ezh2`; its record carries operator `mm30/affects-concept-molecular-entity`, args `concept:disease-stage`, `protein:EZH2`, polarity `positive` | confirmed |
| W1.spec | `analysis-spec:5132014c…`, the rehearsal's identity | confirmed |
| E2 | `built` `bda25928…` | confirmed |
| W2 | four `project` records (§3.2) | confirmed |
| R0 | **D** `epoch-stale`: **refuted**; it rendered. **R**: the EZH2 and PHF19 → overall-survival rows `not-ready`, the stage → PHF19 row `assessed-unevaluated (epoch-stale)` (`next-stale.txt`): confirmed | D refuted, R confirmed |
| E3 | `built` `cd1f59f2…` | confirmed |
| W3 | three mints; the copy's stored projection `10f605d3…` equals its source's; its body opens `Same query as coord:4dbcb704…/3cffd9be…@f9f210e5….`; the source's tip is still `f9f210e5…` (`selections.json`) | confirmed |
| E4 | `built` `a854308b…` | confirmed |
| E5 | `current` `a854308b…`, E4's identity | confirmed |
| R4 | `refused [kernel-refused] attribution-contract-unpinned: 8b5d0c802677ee445e2b9d91ebf5d6a7` (`publish-preview.txt`) | confirmed |
| R5 | `NoBelief`, `no-directional-outcome` (`belief.txt`) | confirmed |
| S1 | working corpus analysis-spec 1, dataset 2, project 4, proposition 1, question 3; epoch `a854308b…` (`status-final.txt`) | confirmed |
| C6 | `arms/compare.json`: workspace and unrelated byte-identical for `status`, `projects`, `next`; both `next` equal to R2's `health` | confirmed |
| C7 | `arms/compare.json`: CLI `next` equal to R2's `health`; `next --project multiple-myeloma` equal to R2's `multiple-myeloma`; `projects` marks `health` `(selected)` | confirmed |

### 4.2 The selections

Every R1 and R3 row is `equivalent: true` and `complete: true`, with nothing absent and
nothing unresolved (`selections.json`). Against §2.3:

| view | observed | D | R |
|---|---|---|---|
| `multiple-myeloma` | PHF19, OS, EZH2, runs, A, V, S30 (8) | refuted: G is not selected | confirmed |
| `cancer` | as `multiple-myeloma` | refuted, as above | confirmed |
| `health` | `multiple-myeloma`'s plus S-EZH2, cohort, annotation (11) | refuted: no G | confirmed |
| `multiple-myeloma-findings` | run `8b1a2401…`, PHF19, G, S30 (4) | refuted: no A | confirmed |
| health question | EZH2, PHF19, runs, A, V, S-EZH2, cohort, annotation (9) | — | confirmed |
| its copy under `cancer` | equal to the question's | confirmed | confirmed |
| `evidence-bound terms` | PHF19, EZH2, runs, A, V, S30 (7) | refuted: no G | confirmed |

Every D refutation has one cause: a `closure` clause selects what its anchor reaches and
never the anchor (finding F8). The live sets also equal the rehearsal's by
`invariants.py` (`invariants-vs-r3.json`), which compares the selected world records per view
and the `next` ids, classes and order.

### 4.3 The renderings

The four R2 `propositions:` blocks are byte-identical to §2.4 (`next-*.txt`); each project's
`selection:` block names that project, `complete: true`, `absent: none`, the world and
both corpora's state digests; the unselected rendering has none. Confirmed.

### 4.4 The criteria

| criterion | verdict | evidence |
|---|---|---|
| 1 | **met** | G and S0: one world, mm30 relocated and the working corpus fresh, one session writing the working corpus and reading both (`status-initial.txt`, `status-final.txt`) |
| 2 | **met** | R1: PHF19 and OS selected by `health`, `cancer` and `multiple-myeloma` at E3 |
| 3 | **partly met** | the question under `health` reaches mm30 facts (its selection holds PHF19, the runs, A and V), its copy under `cancer` is one same-query act, the new proposition and its spec over a declared, unheld cohort exist; the fact `health` selects and `multiple-myeloma` does not is S-EZH2 and the two datasets, not the proposition (C5) |
| 4 | **partly met** | each `next` renders exactly its selection's propositions in the fixed class order and equals the set this record stated before the run; the sets are not §9.2's expected ones, since `multiple-myeloma` and the whole world hold the EZH2 proposition alike |
| 5 | **unmet** | the dry run refuses `attribution-contract-unpinned` (F12): neither a report nor `closure-incomplete`. §6 M5 computes the two closures the dry run could not report |
| 6 | **met** | C6 arm |
| 7 | **met** | C7 arm |

## 5. Findings

Classified `defect`, `design-gap`, `surface-gap` or `corpus-work`, each filed to its
lane, origin `agent`, source `sci-0d00d2`.

| # | finding | class | filed |
|---|---|---|---|
| F1 | science's launcher parsed every contract document as a genesis, so the successor contract mm30 pins could not be loaded and a successor document reached the person as `internal-error` | defect | `sci-7079e3`, fixed on this branch (`19738ca`, `316338a`) |
| F2 | no command creates a corpus; genesis is a kernel-level step (§3.1) | surface-gap | `sci-326015` |
| F3 | no command declares a dataset without holding it (§3.1) | surface-gap | `sci-20aee0` |
| F4 | `spec` declares one input, `observes`; the annotation the analysis reads is named only in the method text | surface-gap | `sci-06c689` |
| F5 | only a project can be previewed or published; the findings level had to be minted as a project | surface-gap | `sci-2a3f0a` |
| F6 | no command renders a view's selection; every selection here was read by a driver through the kernel | surface-gap | `sci-8e2cd7` |
| F7 | the coarse form leaves the composite outside every clause, and its term-clause rule makes the typing contract's vocabulary the project boundary (§7) | design-gap | `sci-538142` |
| F8 | a `closure` clause never selects its anchor: the myeloma views omit GSE179929 and the findings level omits its own assessment | design-gap | `sci-c5872f` |
| F9 | a health contract (estimands beyond myeloma's stages, a disease vocabulary) is what the health program's first real question needs | idea | `sci-036920` |
| F10 | a kernel `RuleNotHeld` raised while reading holdings reaches the person as `internal-error` (rehearsal r2) | defect | `sci-0f110f` |
| F11 | no command installs the holdings reducer; a relocated world serves no citing write until a kernel-level step installs it (C1a) | surface-gap | `sci-5ae0e6` |
| F12 | a relocated replica of the world's own corpus is refused as a foreign publication | design-gap | `beliefs-7c612b` |
| F13 | the stored-edge publication closure is narrower than the projection-derived closure of a findings view (M5) | design-gap | `beliefs-37d7ca` |
| F14 | the reproduction driver's contract documents carry an `also:` key no consumer reads | idea | `beliefs-1ad2c9` |
| F15 | the empirical-observation locator declares no `doi` scheme (§1.2) | design-gap | `beliefs-46b937` |

Not filed, with reasons: the first rehearsal attempt's `CapabilityUnavailable` (atoms'
durability allowlist does not admit the task directory's volume, a host fact the
replicas were moved for, §1.3); Zenodo's HTTP 504 during one rehearsal download
(transient); the spec's two-line TOML table (§1.1, this task's own design text); R0's
rendering (a refuted prediction, not a refusal: `next` marks the stale row rather than
refusing, which the consumer design's per-row classification allows).

## 6. Measurements

### M1 Epochs

| epoch | trigger (from the schedule) | writes since the previous | outcome | live s | rehearsal r3 s |
|---|---|---|---|---|---|
| E1 | initial | the two declarations (kernel-level) | built | 1.66 | 7.35 |
| E2 | evidence | `claim`, `spec` | built | 1.44 | 7.69 |
| E3 | coordination-only | `project` ×4 | built | 1.91 | 8.03 |
| E4 | coordination-only | `question`, `reuse`, `question` | built | 1.94 | 10.66 |
| E5 | none | — | current | 1.11 | 5.15 |

Two coordination-only rebuilds out of four builds, 1.91 s and 1.94 s live (8.03 s and
10.66 s on the rehearsal replica, whose data root sits in a synced tree); each costs about
what an evidence build costs. The rebuild is forced because any drift is `epoch-stale`
(consumer limitation 2); R0 shows the stale row is still rendered. This is the count
`beliefs-655c10` asked for.

### M2 Explicit entries

| view | `addresses` entries | term clauses | closure anchors | selected |
|---|---|---|---|---|
| `multiple-myeloma`, `cancer` | 1 (S30) | 285 | 1 (G) | 8 |
| `health` | 5 (S30; EZH2, S-EZH2, cohort, annotation) | 285 | 1 | 11 |
| `multiple-myeloma-findings` | 1 (S30) | 0 | 1 (A) | 4 |
| health question and its copy | 4 | 0 | 1 | 9 |
| `evidence-bound terms` | 1 | 1 (`concept:disease-stage`) | 1 | 7 |

By clause, in `multiple-myeloma`: the closure from G reaches the two runs, A, V and PHF19
(5); the address adds S30; the term clauses add OS (`concept:overall-survival`) and EZH2
(`concept:disease-stage`). The evidence-bound form selects the same records less OS: the
285-clause rule's whole extra reach in this world is one unevidenced proposition plus
every proposition any future claim types under mm30 (the EZH2 case). The coarse form
omits the composite (no `composes` predicate) and its own anchor (F8).

Every `addresses` entry for S30 exists because a run reaches its spec only through a
facet and a spec emits no relations; the four entries of the health clause exist because
nothing connects a spec to its target and declared inputs before a run. Storing
`executes`, `targets` and spec-input edges (`beliefs-7c98bc`) would retire the S30 entry
from all five views that carry it and, with an EZH2 anchor, the health clause's three
spec-side entries; anchors themselves would still need naming (F8).

### M3 The fence

Three separate counts: research questions **1** (the health question); same-query reuses
**1** (its copy under `cancer`); measurement-only questions **1** (`evidence-bound
terms`). Repairs needed **0**; the source did not change (its tip after the reuse is the
revision it was minted at, `f9f210e5…`). The reuse ratio is 1 reuse to 1 research
question.

### M4 Command latency

End to end at the driver, live: citing writes `claim` 0.31 s and `spec` 0.36 s;
coordination writes `project` 0.15–0.23 s, `question` 0.19–0.20 s, `reuse` 0.25 s;
`project-select` 0.01–0.30 s; reads `next` 1.14–1.80 s, `belief` 1.09 s,
`publish-preview` 0.55 s. A latency, not a mount cost (design M4).

### M5 The two closures of the findings selection

The findings selection is run `8b1a2401…`, PHF19, G and S30 (4 records; the design
expected 5 with A, F8). Its stored relations, read from the record files under
`<world>/corpora/mm30/`: the run `observes` G; PHF19, G and S30 carry none. The
assessment, not selected, `assesses` PHF19 and is `produced_by` the run; the verification
`verifies` the assessment.

- **Stored-edge closure** (what `closure_missing` walks): from the selection, the run
  reaches G, which is selected. Complete, and it reaches nothing outside the selection.
- **Projection-derived closure** (projects design §8.1: each run's spec facet, each
  spec's projection target and declared inputs, each assessment's run): the run's spec
  facet reaches S30; S30's target reaches PHF19 and its `observes` input reaches G; no
  assessment is selected. Complete.
- **What one reaches and the other does not:** S30 and PHF19 are reached by projection and
  by no stored edge (they are in the selection by address and through A's closure). The
  vocabulary datasets are reached by neither: the contract binds them, not the spec.

Both closures are complete over this selection, so had the dry run reached its closure
step it would have had nothing missing to report; it refused on attribution first (F12).
The difference between the two rules is F13.

### M6 The working corpus after the walk

analysis-spec 1, dataset 2, project 4, proposition 1, question 3 (11 records). Session
ledger `select` lines: 7 in the walk's session (three in W3, four in R2), one in each of
the three arm sessions: 10. The walk's session ledger records 9 acts, one per mint.

## 7. What this decides

- **The fence (projects design §7).** One reuse against one research question is not a
  pattern, and it needed no repair. No `beliefs` request is made.
- **`beliefs-7c98bc`** is noted with M2's counts: the S30 `addresses` entry in five views
  and the health clause's spec-side entries are what the edges would retire.
- **`beliefs-655c10`** is noted with M1's: two coordination-only rebuilds in the schedule's
  four builds, 1.91 s and 1.94 s live, each about an evidence build's cost.
- **Proposed amendment to §6.2's term-clause rule** (design §8, not applied; the user's
  call): a project's term clauses name the concepts its own evidence binds. M2's evidence
  is that the prescribed rule's extra reach here is one unevidenced proposition plus any
  future mm30-typed claim. F7 carries it.
- **Proposed amendment to §9.2 criterion 5** (design §8, not applied): while `beliefs`
  refuses a relocated replica (F12), the criterion names the attribution refusal as a
  third outcome, or the dry run moves to a corpus admitted `fresh`.
- **A third amendment this run argues for** (not applied): §6.2's coarse queries and
  §8.1's findings level name their anchors, since a closure never selects its anchor
  (F8).
- **The health program's first real question** needs a contract with estimands beyond
  myeloma's and a disease vocabulary (F9). The declared cohort is the mm program's to
  hold or supersede under its own protocol (`mm-a32d58`).
