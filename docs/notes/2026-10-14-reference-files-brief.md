# A project's reference files — brief

**Date:** 2026-10-14 · **Ideas:** sci-b9f9d4 · **Goal:** sci-f6c61b · **Research:** sci-76de75

## 1. Problem

A workspace project consults files it must be able to revisit: review
supplements scanned for accessions, articles read for provenance, book
chapters. It needs them kept out of git, findable later, and citable from its
records by content digest and by DOI or PMID, so a record can say exactly which
bytes it read.

## 2. Current behaviour and evidence

- Proto-science kept each project's PDFs in `papers/pdfs/` beside a
  `references.bib`, outside version control.
- multiple-myeloma keeps an interim store in its gitignored `data/references/`
  (`data/` is ignored), with each file's sha256 listed in a note on the task that
  used it (mm-0a147a, 2026-10-11).
- beliefs: a `source` record is addressed `source:<digest>` from DOI, PMID, ISBN
  or accession, and carries only an identifiers facet (`stored.source_node`).
  Holdings observations attest bytes a **dataset** declares
  (`holdings/boundary.write`), and acquisition hashes and stores fetched
  resources only to mint a dataset with an `empirical-observation` facet.
- lit's corpus design (2026-09-21) leaves PDFs to Paperpile, the system of
  record ("No PDF paths").
- quarry downloads no files (sci-a17882's acceptance).

## 3. Constraints

- Every durable thing is a governed kernel record; science keeps no storage of
  its own (AGENTS.md).
- A paper is a source, not an observation: holding it as an empirical dataset
  would let it bear on belief (compare beliefs-91bce7, annotations are not
  observations).
- Workspaces are referenced from the world, never the reverse (projects design
  §3); bytes stay out of git.

## 4. Alternatives

- **A. Kernel-held source bytes.** A source record names held files by digest,
  attested by holdings observations as dataset resources are; science gains a
  way to hold one. Strongest citation, but needs kernel work and a non-empirical
  path.
- **B. Workspace convention.** A gitignored `references/` directory per
  workspace with a manifest mapping sha256 → source address (DOI/PMID) and the
  file name; records cite the source address, and the manifest resolves bytes.
  No kernel change, and close to the interim; the bytes are not attested by the
  world.
- **C. lit and Paperpile.** Paperpile holds the PDFs; lit's nodes carry a
  pointer. Supplements and books outside Paperpile have no home.

Lean: **B now, A if the research finds a cheap kernel path**. B formalizes what
multiple-myeloma already does and can later be held by the kernel without
changing what records cite.

## 5. Unanswered questions

- Can a source record be tied to held bytes today, or does holding require a
  dataset? — sci-76de75, from the beliefs code and docs.
- Where do the bytes live across hosts (Dropbox, WORK_ROOT storage) and is
  sync expected? — the user.
- Should the convention live in science (a workspace layout rule) or lit? —
  the user, after sci-76de75.

## 6. Proposed decomposition

- sci-f6c61b — goal: reference files addressable from records.
- sci-76de75 — research (can a source record cite held bytes). Wakes sci-b9f9d4.
- sci-b9f9d4 — waits on sci-76de75; then scoped against the chosen alternative.
