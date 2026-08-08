# Contributor guide — design

**Date:** 2026-08-08
**Status:** Approved for implementation
**Scope:** A concise, topic-first companion to the redesign documents for new
contributors. The guide summarizes decisions; it does not replace or amend
them.

## 1. Purpose

The redesign corpus is thorough but organized by the order in which problems
were resolved. A new contributor instead needs a stable mental model: what
Science believes, which objects carry that model, how identity and history
work, how computation becomes eligible evidence, and which parts exist today.

The guide will provide that path while keeping exact links back to the design
documents for readers who need definitions, rationale, limitations, or
acceptance criteria.

## 2. Authority and freshness

The guide is explanatory, not normative. Design documents, their amendments,
and their guarantee tables remain the source of truth. When a summary and a
design disagree, the design wins and the guide should be corrected.

Every page carries YAML metadata with:

- `title`
- `status`, initially `evolving`
- `created`, initially `2026-08-08`
- `updated`, initially `2026-08-08`
- `sources`, listing the design documents summarized by that page

Guide pages distinguish **design status** from **implementation status**. A
banked or approved design is not described as implemented unless the repository
or adoption ledger says it is.

## 3. Organization

`docs/guide/` will contain:

| Page | Responsibility |
|---|---|
| `README.md` | Introduce Science, show the conceptual map, report overall implementation status, and provide newcomer and reference reading paths. |
| `foundations.md` | Explain the epistemic invariant, kernel, ownership boundaries, profiles, and main record categories. |
| `claims-and-belief.md` | Explain typed claims, assessments, evidence eligibility, belief policy, and domain vocabulary. |
| `identity-world-and-change.md` | Explain semantic identity, addresses, corpora, the world index, epochs, retraction, and supersession. |
| `computation-and-reproducibility.md` | Explain analysis specs, run closures, replay eligibility, equivalence, and verification. |
| `contracts-and-adoption.md` | Explain normative contracts, guarantees, conformance, review evidence, implementation cuts, and adoption order. |
| `open-questions.md` | Consolidate unresolved questions without silently promoting limitations or deferred implementation into design uncertainty. |
| `glossary.md` | Provide one canonical, alphabetized set of short definitions linked to the relevant topic pages and sources. |

This organization follows concepts rather than source-file boundaries. A
design may inform several pages, and a page may synthesize several designs.

## 4. Page shape

Topic pages use this structure, omitting a section only when it has no useful
content:

1. **TL;DR** — one sentence.
2. **Why it matters** — the user-visible or epistemic problem in one short
   paragraph.
3. **Key ideas** — the smallest set of concepts needed to understand the topic.
4. **How it connects** — relationships to other guide topics.
5. **Current state** — what is designed, banked, measured, or implemented.
6. **Open edges** — a short link to the consolidated question list.
7. **References** — precise design-document sections and other authoritative
   project sources.

The index and glossary use structures suited to navigation rather than forcing
this template.

## 5. Editorial rules

- Lead with the system idea, not the history of how it was discovered.
- Prefer short paragraphs, bullets, and small tables over exhaustive prose.
- Define a term once in the glossary; topic pages may give only the local
  context needed to read them.
- Preserve important distinctions such as record versus view, occurrence
  versus authorization, replay eligibility versus epistemic verdict, and
  design status versus implementation status.
- Link directly to the relevant design section whenever a concise summary
  necessarily drops qualifications.
- Carry forward settled amendments rather than repeating superseded wording.
- Report measurements with their stated scope and limitations.
- Use repository-relative links and the existing `docs/` conventions.

## 6. Source coverage

Each of the fifteen redesign documents that predate this guide design will
appear in at least one guide page's `sources` metadata or reference list. The
adoption ledger and repository README govern implementation-state claims. Later
design documents can be incorporated by updating the affected pages and their
`updated` dates; no generated synchronization mechanism is needed.

## 7. Verification

The finished guide is checked for:

- valid relative Markdown links;
- required metadata on every page;
- coverage of every existing design document;
- consistent glossary definitions and internal links;
- no unresolved placeholders;
- explicit separation of designed, banked, measured, and implemented states.

The guide is successful when a new contributor can read the index plus the five
topic pages in order, explain the system's invariant and major boundaries, and
reach the exact source sections for details without reading the full design
corpus first.
