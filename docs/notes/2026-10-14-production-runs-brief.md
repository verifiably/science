# Production runs and multi-resource datasets — brief

**Date:** 2026-10-14 (revised the same day after review) · **Ideas:** sci-ccd96f ·
**Goal:** sci-d1e874 · **Research:** sci-dfec5b

## 1. Problem

A workspace project builds a processed package (several files plus a manifest)
from raw bytes it holds, with a workflow it can name. It needs that package held
as **one** dataset whose lineage reaches the raw bytes and the workflow by
identity, and then **used**: an analysis reads named members of the package, and
its run can be replayed. The multiple-myeloma program's first milestone is the
GSE24080 pilot held with lineage (mm-a32d58); its phase-1 protocol §5 records the
missing lineage as a known gap on every roster entry until it exists. Its later
phases analyse those packages, so holding alone is not the end of the path.

## 2. Current behaviour and evidence

The GSE24080 spike (multiple-myeloma `docs/reports/2026-10-09-gse24080-spike.md`)
rebuilt the package into a fresh directory: **7 of 7 resource digests matched**,
and `datapackage.json` matched **except its `created` timestamp** (§4.2). It then
measured the science surface (§4.4, findings F1, F2):

- `science dataset` holds one regular file (`python/src/science/commands/dataset.py`
  refuses a directory and declares one resource). A 7-file package became 5
  unrelated dataset records tied only by a locator string.
- `science run` executes an analysis-spec through
  `beliefs.boundary.execute_assessment_run`; no command mints a
  dataset-production run, so `transforms`/`produces` and the lineage basis are
  unreachable.

Consumers assume one file per dataset: `run.prepare` (`commands/run.py`) passes
one `held_path` per input address, `holdings.held_path_for` returns the first
matching location, and assessment `verify` (`commands/verify.py`) replays through
the same `prepare`.

The kernel has the vocabulary (beliefs `python/src/beliefs/`: multi-resource
`DatasetDeclaration`, `execute_production_run`, `production.mint_dataset`,
`stored.dataset_node(basis=…)`), but its path stops short, observed 2026-10-14:

1. `boundary._stage_inputs` refuses a held input that is not one regular file.
2. `runrecord.publication_plan` writes only the run record; its `produces` edge
   names an address with no dataset record behind it.
3. The run's output bytes are hashed in scratch and not kept.
4. No code turns a `StampedBasis` into the stored lineage-basis facet.

And closing 1–4 still leaves the produced package **ineligible as empirical
evidence**: assessment writes refuse an ineligible observed dataset
(`corpus._refuse_ineligible`), eligibility needs a valid `empirical-observation`
facet, and the kernel refuses that facet beside a lineage basis or a producer
(`acquisition.py` facet check and `bearer_refusal`). Inheriting standing through
lineage is beliefs-8ecbb5, shelved until a concrete workflow observes a held
derived dataset.

Acquisition (`holdings/acquire.py`, exposed later by sci-a17882) mints one
multi-resource dataset with the empirical facet from https URLs: it fits the raw
input, not the produced package.

## 3. Constraints

- Every durable thing is a kernel record through the permit-bound writer;
  science keeps no storage of its own. A new command is a `tools/cli.toml` row
  first.
- Command framework §2.2: a command is one deterministic handler.
- Commons §4.8: `derived_from` is a view over `produces ∘ transforms`.
- Kernel computation-reproducibility design §5.2: one output per run.
- beliefs-8ecbb5: the acquisition bearer rule stands until inherited standing is
  designed.
- Dataset identity is the digest over declared resources: a manifest that
  embeds occurrence metadata (a build timestamp) gives identical rebuilds
  different addresses.

## 4. Alternatives

- **A. Extend `dataset` and `run`.** `run` takes a production recipe as a second
  shape. Few rows; `run` carries two contracts.
- **B. New production command beside `run`.** `dataset` holds a manifest-declared
  package; a production command records the run and mints the package with its
  lineage basis; `run` and `verify` resolve and stage named package members.
- **C. Kernel-first.** Land gaps 1–4 as beliefs requirements before either surface.

Lean: **B on top of C**, with package-member resolution in `run` and `verify` in
scope. Acceptance: an analysis consuming two distinct members of a held
multi-resource dataset, then its replay through `verify`; and a production run
whose identical rebuild mints the same package address. On empirical use of the
*produced* package, lean **defer explicitly**: demonstrate member consumption on
an acquired (empirical) multi-resource input, such as GSE24080's series matrix
and clinical table, and name beliefs-8ecbb5 as the gate before any assessment
observes a produced package.

## 5. Unanswered questions

- Are gaps 1–4 unbuilt kernel work or the caller's? — sci-dfec5b.
- Does the first milestone include assessments that observe a produced package
  (unshelving beliefs-8ecbb5), or defer them? Which multiple-myeloma phase first
  needs one? — sci-dfec5b recommends; the user decides.
- Is the produced dataset minted atomically with the run record, or in a defined
  order? — the kernel design, after sci-dfec5b.
- Manifest identity: deterministic manifest bytes, or occurrence metadata
  (build time, host) kept outside the identified package? — the planned spec,
  starting from the spike's `created` measurement.
- How does a package declare a resource the source names but the build did not
  retrieve (the spike's `declared_not_retrieved`)? — the spec, with mm-6c2f3c.

## 6. Proposed decomposition

- sci-d1e874 — goal: hold and use processed packages with production lineage.
- sci-dfec5b — research (gaps 1–4; the eligibility boundary with beliefs-8ecbb5).
  Wakes sci-ccd96f.
- sci-ccd96f — waits on sci-dfec5b; then a `planned` spec covering the
  production surface, member resolution in `run` and `verify`, manifest
  identity, and the beliefs requirements it files.
