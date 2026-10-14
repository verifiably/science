# A project's reference files — brief

**Date:** 2026-10-14 (revised the same day after review) · **Ideas:** sci-b9f9d4 ·
**Goal:** sci-f6c61b · **Research:** sci-76de75

## 1. Problem

A workspace project consults files it must be able to revisit: review
supplements scanned for accessions, articles read for provenance, book
chapters. It needs them kept out of git and findable later, and its records must
say **exactly which bytes** they read: an article, its supplement and a corrected
version share one DOI, so the work cited is not enough.

## 2. Current behaviour and evidence

- Proto-science kept each project's PDFs in `papers/pdfs/` beside a
  `references.bib`, outside version control.
- multiple-myeloma keeps an interim store in its gitignored `data/references/`,
  with each file's sha256 in a note on the task that used it (mm-0a147a).
- beliefs: a `source` record is addressed `source:<digest>` from DOI, PMID, ISBN
  or accession and carries only an identifiers facet (`stored.source_node`); it
  names no bytes.
- Holding bytes is not empirical standing. `science dataset` mints a dataset
  record with the `empirical-observation` facet only when a locator is given
  (`commands/dataset.py`); without one the dataset is held but cannot be observed
  as evidence. The holdings writer (`holdings/boundary.write`) acts on a store
  location and bytes and does not itself require a dataset record.
- Acquisition stores fetched https resources and always stamps the empirical
  facet, so it is the wrong door for a paper.
- lit's corpus design (2026-09-21) leaves PDFs to Paperpile ("No PDF paths");
  quarry downloads no files.

## 3. Constraints

- Every durable thing is a governed kernel record; science keeps no storage of
  its own (AGENTS.md).
- A reference file must not bear on belief: whatever holds it carries no
  empirical facet (compare beliefs-91bce7).
- A citation's meaning is fixed when written: it names the source **and** the
  content digest, or a governed record binding both. A location index may be
  lost, moved or rebuilt without changing what any citation means.
- Workspaces are referenced from the world, never the reverse (projects design
  §3); bytes stay out of git.

## 4. Alternatives

- **A. Governed binding over existing non-empirical holding.** Each file is held
  as a dataset with no empirical facet (today's `science dataset` without a
  locator); a governed relation binds it to its source record. A citation names
  the source address and the dataset (whose address is derived from the
  digest). Missing: that relation and a retrieval interface from the citation
  to the held bytes.
- **B. Workspace store with a self-sufficient citation.** Records cite
  `source:<…>` plus `sha256:<…>` directly; a gitignored `references/` manifest
  maps digest to file path and is only a location lookup. No kernel change; the
  bytes are not attested by the world.
- **C. lit and Paperpile.** Paperpile holds the PDFs; lit's nodes point at them.
  Supplements and books outside Paperpile have no home.

Lean: **source address plus digest as the citation in every alternative**; then
**A** if sci-76de75 finds the relation and retrieval cheap, otherwise **B**, which
A can later attest without changing any citation's meaning.

## 5. Unanswered questions

- What is missing between a source record and held bytes: a relation kind, a
  retrieval interface, or both? Does existing non-empirical holding serve as is?
  — sci-76de75, from the beliefs and science code.
- Where do the bytes live across hosts (Dropbox, WORK_ROOT storage) and is sync
  expected? — the user.
- Does the convention belong to science (a workspace rule) or lit? — the user,
  after sci-76de75.

## 6. Proposed decomposition

- sci-f6c61b — goal: reference files cited by exact bytes.
- sci-76de75 — research (the source-to-bytes relationship and retrieval
  interface). Wakes sci-b9f9d4.
- sci-b9f9d4 — waits on sci-76de75; then scoped against the chosen alternative.
