---
name: research-paper
description: Use when asked to read one paper, or a list of papers one at a time, and record its source and a reading note in a science project.
---

# Read a research paper

Read [literature-evaluation.md](literature-evaluation.md) and
[statement-extraction.md](statement-extraction.md) before reading and extracting.

## Boundaries and preconditions

Write records only through science commands, named here by declaration name.
Write no repository file and make no commit. The only existing record this
workflow edits is a source's identifiers through `source-correct`; edit nothing
else. It adds no source-assertion records and promotes no extraction into belief.

First check that science commands are reachable and a project is selected when
writing notes. Tell the person to run `project-select` when needed; never select
one yourself. Check that `quarry` runs when needed. If a precondition fails, stop
with a plain explanation. Do not locate or install quarry; the session environment
supplies it.

Before reading any text reporting results, follow the exposure policy declared in
the workspace's agent guide or protocol. If it leaves the paper's status unresolved,
stop at bibliographic metadata and say so. An accessible abstract is not permission
to read it.

## Identity and attribution

Confirm identity by the first applicable route: an existing world source found by
`record`; quarry's index record; for a DOI absent from the indexes, the DOI
registry's own metadata record fetched by the harness using content negotiation
at `doi.org`, whose title must match. Failing those routes, proceed only on
identifiers supplied and confirmed by the person, and state in the reading note
that identity was not cross-checked. Model memory cannot confirm identity.

Quarry has no DOI lookup. Search each index for the DOI in its own syntax
(`--native`), then `show` the returned provider id. Read the index record's
cross-references and use every available confirmed identifier together in world
lookups. Compare titles after normalising case, whitespace, markup and closing
punctuation. A new source takes the title from the identity-confirmation route,
without PubMed's closing full stop. Only DOI, PMID, ISBN and accession are accepted;
arXiv, PMCID and URL are not schemes. Use an arXiv paper's `10.48550/arxiv.<id>` DOI.
A paper without an accepted identifier cannot be recorded as a source.

Every statement in the note says which it is: what a named source states (with
source address and reading depth), an existing world result (with address), or the
writer's own reasoning or recollection, labelled as such. Memory is orientation
only and never attributed to a paper. Hedge to match evidence; store no strength
or confidence grade.

Sources belong to the world; reading notes belong to the selected project.
Deduplication works by shared identifier, not proof of one record per article:
disjoint identifiers can still produce two records. Look up every confirmed
identifier and mint with all of them. Complete identifiers before first publication:
a source held by another corpus cannot be corrected here. Existing duplicates
stay separate; no command merges them. A preprint and published version with
different DOIs are different works. A corrected source's old address keeps
redirecting, including after a wrong identifier is replaced. A note's citation
may stop resolving if its source's last holder is retired; these workflows add no
retention guarantee. Titles are fixed at minting and are not identity.

## Workflow

One paper, read and recorded. A list is handled one paper at a time, each finished
before the next.

1. **Identify the paper before reading it.** From a DOI, PMID, title, URL or file,
   confirm its identity by the identity order above. Check that DOI and PMID agree with
   each other and that the title matches; a conflict stops the skill for that
   paper. The reading note records which route confirmed the identity.
2. **Find or record the source.** `record` by every confirmed identifier
   together.
   - Absent: `source`. When the lookup ran on a single identifier, the skill
     says so to the person and in the reading note: a record of the same work
     under a different identifier could not be ruled out.
   - Found, carrying every identifier now known: use it.
   - Found under fewer identifiers, held only by the write root:
     `source-correct`, with the index record as grounds.
   - Found under fewer identifiers, held by any other corpus (a read mount, or
     the write root and a publication of it): use it as it stands and state the
     further identifier in the reading note. `source-correct` would refuse.
   - Several matches: two records already exist for what may be one work. The
     skill tells the person, continues on the match that carries the
     highest-ranked identifier (DOI, then PMID, ISBN, accession), and names the
     other address in the reading note. No command merges them.
3. **Check for an earlier reading.** `record` on the source lists this project's
   notes about it, including notes written against an address the source has
   since left. With one present, the person chooses: add a further reading or
   stop.
4. **Obtain text,** in this order, under the exposure rule:
   1. a file the person supplies;
   2. open-access full text at a location quarry lists for the record;
   3. an abstract: from the index's structured record for the work (PubMed's
      E-utilities record, Europe PMC's core record), or, for a work the indexes
      do not hold, from the DOI registry's metadata record when it carries one.
      Reading depth `abstract`;
   4. nothing reachable: the source stays recorded, no reading note is written,
      and the skill says the paper was not read.

   Text in 2 and 3 is fetched byte for byte into session scratch outside any
   repository, with a tool that saves the response unchanged. A page reader that
   summarises what it fetched is not a fetch: its output cannot be hashed or
   quoted. Where the harness has no byte-exact fetch, the skill reads only a
   supplied file. The skill computes the sha256 of the exact bytes it reads.

   A work outside the indexes has no full-text route here. Its full text is read
   only from a file the person supplies (for an arXiv paper, the PDF they
   download). Add no new retrieval route.

   Never: a publisher landing page fetched to judge access, a pirated copy, or
   model memory standing in for text.
5. **Read** the abstract, introduction, methods, results and discussion, to the
   depth available.
6. **Write the reading note** with `note`, `about` the source. Its parts:
   - *Reading.* Source address and identifiers; what was read (kind of
     representation, where it came from, its sha256, the date); the depth, `full
     text` or `abstract`; whether the work is primary or secondary; and,
     separately, its publication status (peer-reviewed, preprint, other); who read
     it (the person, or the model and version).
   - *Contribution, methods, findings, limitations,* each in the reader's words
     and marked as the reader's summary of the paper.
   - *Statements.* What the paper itself says, in the form stage two will promote:

     ```
     1. stance: asserts | denies | hypothesizes
        span: "<verbatim text from the representation read>"
        where: <section, page or paragraph in that representation>
        paraphrase: <one sentence, the reader's wording>
        proposition: <address>   (optional)
     ```

     A span is copied exactly or it is not a statement. Text that cannot be quoted
     exactly belongs in the summary. From an abstract-only reading, statements are
     limited to what the abstract says, and numbers, cohort definitions and method
     parameters are left out. `proposition` is given only when the reader already
     has a proposition in the world that the statement concerns, such as the one
     under discussion; the skill neither searches for one nor mints one while
     reading.
   - *Reader's commentary,* labelled as the reader's own and never as the paper's.
   - *Relevance to the project* and proposed follow-ups.
7. **Offer follow-up questions for confirmation.** Offer `question` records;
   mint only those the person confirms. End by listing minted addresses and
   anything that could not be done.

The statements are one reader's extraction and the note says so: unadjudicated,
and not to be used as an independent check of the same reader's summary.
