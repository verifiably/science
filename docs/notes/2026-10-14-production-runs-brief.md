# Production runs and multi-resource datasets — brief

**Date:** 2026-10-14 · **Ideas:** sci-ccd96f · **Goal:** sci-d1e874 · **Research:** sci-dfec5b

## 1. Problem

A workspace project builds a processed package (several files plus a manifest)
from raw bytes it holds, with a workflow it can name. It needs that package held
as **one** dataset whose lineage reaches the raw bytes and the workflow by
identity, so a later analysis that reads the package inherits its provenance.
The multiple-myeloma program's first milestone is exactly this for the GSE24080
pilot (mm-a32d58), and its phase-1 protocol §5 records the missing lineage as a
known gap on every roster entry until it exists.

## 2. Current behaviour and evidence

The GSE24080 spike (multiple-myeloma `docs/reports/2026-10-09-gse24080-spike.md`,
§4.4 and findings F1, F2) rebuilt the package with identical digests and then
measured the science surface:

- `science dataset` holds one regular file (`python/src/science/commands/dataset.py`
  refuses a directory and declares exactly one resource; `holdings.held_path_for`
  returns one location). A 7-file package became 5 unrelated dataset records tied
  only by a locator string.
- `science run` executes an analysis-spec bound to a proposition through
  `beliefs.boundary.execute_assessment_run` (`commands/run.py`); no command mints a
  dataset-production run, so the kernel's `transforms`/`produces` roles and the
  `lineage-basis` facet are unreachable.

The kernel has most of the vocabulary (beliefs `python/src/beliefs/`):
multi-resource `DatasetDeclaration` and `dataset_address` (`dataset.py`),
`execute_production_run` (`boundary.py`), `production.mint_dataset` (one address
over a run's declared outputs, a `produces` edge, a `StampedBasis`), and
`stored.dataset_node(basis=…)`. But its path stops short, observed 2026-10-14:

1. `boundary._stage_inputs` refuses any held input that is not one regular file,
   so a multi-resource dataset cannot be a `transforms` input.
2. `runrecord.publication_plan` writes only the run record; its `produces` edge
   names an address with no dataset record behind it.
3. The run's output bytes are hashed in scratch and not kept.
4. No code turns a `StampedBasis` into the stored lineage-basis facet; the only
   other `dataset_node` caller is acquisition, and tests set the facet by hand.

Acquisition (`holdings/acquire.py`, exposed later by sci-a17882) already mints one
multi-resource dataset, but only from https URLs, and always stamps the
`empirical-observation` facet, which the kernel refuses beside a lineage basis. It
fits the raw input, not the produced package.

## 3. Constraints

- Every durable thing is a kernel record written through the permit-bound
  writer; science keeps no storage of its own (AGENTS.md).
- A new command is a row in `tools/cli.toml` first (conformance test).
- Command framework §2.2: a command is one deterministic handler; an
  orchestration-only unit is a skill.
- Commons §4.8: `derived_from` is a view over `produces ∘ transforms`, never an
  authored list, so lineage must be real edges.
- Kernel computation-reproducibility design §5.2: one output per run, a single
  dataset or package.

## 4. Alternatives

- **A. Extend `dataset` and `run`.** `dataset` holds a manifest-declared package;
  `run` accepts a production recipe with no proposition. Few surface rows, but
  `run`'s contract (spec → assessment) becomes two shapes.
- **B. New production command beside `run`.** `dataset` gains package holding; a
  separate command (name open) records a production run whose inputs are held
  datasets and whose output is the package, minted with its lineage basis. Keeps
  `run` spec-bound.
- **C. Kernel-first.** Land the four kernel gaps as beliefs requirements, then
  either surface; the surface choice waits on what the kernel returns.

Lean: **B on top of C**: the kernel gaps have to close whichever surface is
chosen, and a separate command keeps each handler to one contract.

## 5. Unanswered questions

- Are gaps 1–4 unbuilt kernel work, or does the design leave them to the
  caller? — sci-dfec5b, from the beliefs design, code and history.
- Is the produced dataset minted and stored atomically with the run record, or
  in a defined order? — the kernel design, after sci-dfec5b.
- What manifest form does a package declare (e.g. `datapackage.json`), and how
  is the workflow identified when there is no analysis-spec? — the planned spec
  for sci-ccd96f.
- How does a recipe express a resource the source declares but the package did
  not retrieve (the spike's `declared_not_retrieved`)? — the same spec, with
  mm-6c2f3c's second-modality probe as input.

## 6. Proposed decomposition

- sci-d1e874 — goal: hold processed packages with production lineage.
- sci-dfec5b — research (gaps 1–4: kernel or caller). Wakes sci-ccd96f.
- sci-ccd96f — waits on sci-dfec5b; then scoped as a `planned` spec covering the
  science surface and the beliefs requirements it files.
