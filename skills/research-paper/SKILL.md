---
name: research-paper
description: Use when asked to read one paper, or a list of papers one at a time, and record its source, a reading note, and any proposition-paired source assertions in a science project, or to promote statements from an earlier reading note into source-assertion records without re-reading.
---

# Read a research paper

Read [literature-evaluation.md](literature-evaluation.md) and
[statement-extraction.md](statement-extraction.md) before reading, extracting or
promoting statements.

## Boundaries and preconditions

Write records only through science commands, named here by declaration name
(`record`, `source`, `source-correct`, `source-assertion`, `note`, `question`,
`project-select`). Write no repository file and make no commit. This workflow
mints world `source-assertion` records (attributed readings inert in `belief`)
for statements paired with an existing `proposition:<id>`, and when adding a
reading may edit a write-root source's identifiers through `source-correct`;
edit no other existing record. Never call `claim`, never search the world for
propositions unprompted, and never revise reading notes.

First check that science commands are reachable. When invoked directly on an
existing reading note's `coord:` address (`coord:<project>/<local>` or
`coord:<project>/<local>@<revision>`) or stored `note:` id
(`note:<project>.<local>.<uid>`), skip steps 0–4 and go straight to **Promote an
earlier reading**: no selected project is required (promotion writes only world
`source-assertion` records), and no `quarry`, external metadata fetch, `source`
or `source-correct` call runs. Every other invocation (discovering an earlier
reading note through a project's notes on `record`, or writing a new reading
note) requires a selected project: check that one is selected, tell the person
to run `project-select` when needed, and never select one yourself. Check that
`quarry` runs when a step below needs it (never needed for direct promotion or
when step 0 promotes from local records). If a precondition fails, stop with a
plain explanation. Do not locate or install quarry; the session environment
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

Sources and source assertions belong to the world; reading notes belong to the
selected project. Deduplication works by shared identifier, not proof of one
record per article: disjoint identifiers can still produce two records. Look up
every confirmed identifier and mint with all of them. Complete identifiers before
first publication: a source held by another corpus cannot be corrected here.
Existing duplicates stay separate; no command merges them. If two distinct
`source` records share byte-identical representation material and an identical
extraction, `source-assertion` refuses the second anchor with
`data.anchor_conflict` rather than reusing the first. Keep separately citable
versions distinct. Separate DOIs for a preprint and its final article identify
different versions. If a positive pair contradicts verified version evidence,
disclose the disagreement and cite the version actually read. A corrected source's old address
keeps redirecting, including after a wrong identifier is replaced, and
`source-assertion` resolves cited source redirects when checking same-source
reuse. A note's citation may stop resolving if its source's last holder is
retired; these workflows add no retention guarantee. Titles are fixed at minting
and are not identity.

Use the `source coreference (live evidence)` rows in `record`. A `positive`
row on two exact current addresses attests that specific pair. Confirm the
version independently from the material, title and identifiers. A historical or
unavailable row is context. The sole independently identified live source
remains eligible when a peer is unavailable. Linked neighbors are navigation
targets and do not become direct hits. Report `contested` or `negative` evidence
and keep those sources separate. An `unassessed` pair remains a possible
duplicate. Leave overlapping groups unresolved unless each pair in the specific
group is directly positive and independently version-confirmed. Leave signing
any attestation to the person.

If confirmed distinct revisions resolve to one source UID under their available
identifiers (such as two arXiv revisions sharing only the base DOI), explain
that the address cannot distinguish those revisions. Seek a separately
identifiable source for the version read before writing a citation, reading note
or assertion for it. If the material leaves the citable version unresolved, ask
which version was read before writing or promoting.

## Workflow

One paper, read and recorded — or an existing reading note's statements promoted
into `source-assertion` records without re-reading the paper. A list is handled
one paper at a time, each finished before the next. When invoked directly on an
existing reading note's `coord:` address (unpinned or `@<revision>`) or stored
`note:` id (`note:<project>.<local>.<uid>`), skip steps 0–4 and go straight to
**Promote an earlier reading**.

For every promotion offer, show each note's name and address beside the
`source:` address it cites. When several notes match, get the person's explicit
choice before promoting.

0. **Check local records first when given a `source:` address or identifier.**
   Whenever the caller supplies a `source:` address or one or more accepted
   identifiers (`doi`, `pmid`, `isbn`, `accession`), call `record` locally
   first — before any `quarry` lookup, `doi.org` metadata fetch, `source`, or
   `source-correct` call (`record` resolves redirects, matches on *any* shared
   identifier, and lists the selected project's notes about each matching source
   and any `source assertions` already anchored in it). Compare every supplied
   identifier (in canonical form) and any supplied title (normalised as above)
   against what `record` returns before offering promotion, since `record`
   matches on *any* shared identifier and a valid DOI paired with a conflicting
   PMID still returns the DOI's source:
   - **Direct conflict with a single local source:** if `record` returns one
     local `source` and any supplied identifier scheme already present on that
     `source` has a different canonical value
     (`scheme in held and held[scheme] != value`), or any supplied title
     disagrees with that `source`'s normalised title, stop immediately for that
     paper and report the conflict — neither promote nor read.
   - **Verified single local match:** if `record` returns one local `source`
     where *every* supplied identifier matches `held`
     (`all(held.get(scheme) == value for scheme, value in given.items())`), any
     supplied title agrees, and `record` lists at least one earlier reading note
     in the selected project, offer **promote statements from an earlier reading
     (without external metadata fetches, `source-correct`, or re-reading), add a
     further reading, or stop** right here (unless the person already asked to
     promote or to add a further reading). When several reading notes exist on
     that `source`, list each note's address and name beside its cited source
     address and require an explicit note choice from the person before entering **Promote an earlier reading**.
   - **Incomplete or multi-source local match:** if `record` returns several
     local sources, or returns one local `source` lacking one of the supplied
     schemes (`scheme not in held`, such as a PMID-only source when given both
     DOI and PMID), local state alone has not verified that all supplied
     identifiers identify one version. Proceed to step 1 for an external
     cross-check before offering promotion, even when a direct pair is positive.
   Only choosing **add a further reading** — or finding no verified local
   reading note, or starting from a bare title, URL or supplied file whose
   identifiers are not yet known — enters step 1.
1. **Identify the paper before reading it.** From a DOI, PMID, title, URL or file,
   confirm its identity by the identity order above. Check that DOI and PMID agree with
   each other and that the title matches; a conflict stops the skill for that
   paper. The reading note records which route confirmed the identity.
   - **Pre-step-2 promotion check:** once step 1 confirms that all supplied
     identifiers and title agree, call `record` across all confirmed identifiers
     together *before* calling `source` or `source-correct` in step 2. If any
     matched local source carries an earlier reading note in the selected project
     not already offered in step 0, offer **promote statements from an earlier
     reading (leaving the `source` record untouched, without `source-correct` or
     re-reading), add a further reading, or stop** (unless the person already
     specified which to run). Whenever several matching sources or several
     reading notes exist, list each candidate note with its name and cited
     `source:` address and require an explicit note choice from the person before
     entering **Promote an earlier reading**.
2. **Find or record the source (when adding a reading).** `record` by every
   confirmed identifier together.
   - Absent: `source`. When the lookup ran on a single identifier, the skill
     says so to the person and in the reading note: a record of the same work
     under a different identifier could not be ruled out.
   - Found, carrying every identifier now known: use it.
   - Found under fewer identifiers, held only by the write root:
     `source-correct`, with the index record as grounds.
   - Found under fewer identifiers, held by any other corpus (a read mount, or
     the write root and a publication of it): use it as it stands and state the
     further identifier in the reading note. `source-correct` would refuse.
   - Several matches: identify which source describes the citable version
     represented by the material. When the version is independently confirmed
     and all pairs in that set are directly positive, disclose the link and
     name the other addresses in the reading note. If several addresses fit
     the material equally well, rank confirmed identifiers (DOI, PMID, ISBN,
     accession), then use lexical address for equivalent ties. For an
     unassessed pair, disclose the possible duplicate and use the confirmed
     identifier rank once independent identity checks succeed. For contrary
     evidence or different versions, keep them separate and use the source
     for the material read.
3. **Check for an earlier reading.** `record` on the source lists this project's
   notes about it (including notes written against an address the source has
   since left) and any `source assertions` already anchored in it. With any
   earlier reading note not already handled in step 0 or step 1 (such as inputs
   whose identifiers were unknown before step 1), the person chooses: **promote
   statements from the earlier reading (without re-reading)**, **add a further
   reading**, or **stop**. Show the cited source address beside each offered
   note and require an explicit note choice when several match.
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
   depth available. Check the material actually read against the source chosen
   in step 2 before recording it. Cite that source in the note and each
   assertion, including when another linked address carries a higher-ranked
   identifier.
6. **Mint any direct source assertions and write the reading note.** For
   statements paired with an existing proposition, call `source-assertion`
   *before* calling `note` (`about` the source), since notes are never revised.
   Its parts:
   - *Reading.* Source address and identifiers; what was read — both
     representation kind and explicit MIME `media_type` (`application/xml` for
     PMC JATS XML or PubMed abstract XML, `application/json` for BioC JSON or
     DOI registry JSON, `application/pdf` for PDF, `text/markdown` for Markdown,
     `text/html` for HTML, `text/plain` for plain text), where it came from, its
     exact 64-lowercase-hex `sha256`, and the date; the depth, `full text` or
     `abstract`; whether the work is primary or secondary; and, separately, its
     publication status (peer-reviewed, preprint, other); and a clean
     `Reader: <actor>` identifier naming the person or model-and-version who read
     it (keep any transport or relay commentary separate rather than appending
     clauses onto `Reader:`).
   - *Contribution, methods, findings, limitations,* each in the reader's words
     and marked as the reader's summary of the paper.
   - *Statements.* What the paper itself says:

     ```
     1. stance: asserts | denies | hypothesizes
        span: "<verbatim text from the representation read, in Unicode NFC>"
        where: <section, page or paragraph in that representation>
        paraphrase: <one sentence, the reader's wording>
        attributed_to: <annotator within the source>   (optional)
        proposition: <address>                         (optional)
        source_assertion: <address>                    (present when minted or reused)
     ```

     Normalise `span`, `where`, `media_type` and optional `attributed_to` to
     Unicode NFC (if the source representation yielded decomposed characters)
     while preserving exact wording, whitespace, case and punctuation, so the
     note text and `source-assertion` inputs are byte-identical NFC strings. A
     span is copied verbatim or it is not a statement; text that cannot be quoted
     exactly belongs in the summary. From an abstract-only reading, statements
     are limited to what the abstract says, and numbers, cohort definitions and
     method parameters are left out. `proposition` is given only when the reader
     already has an existing `proposition:<id>` in the world that the statement
     concerns (such as one supplied by the person or under discussion), verified
     first with `record` to have `kind == "proposition"`; never call `claim` and
     never search the world for propositions unprompted while reading.

     For each statement carrying a verified `proposition: proposition:<id>`,
     call `source-assertion` before `note` (`source` = the source address,
     `proposition`, `sign` = `stance`, `quote` = `span`, `locator` = `where`,
     `sha256`, `media_type`, `extent` = `full` for `full text` or `abstract` for
     `abstract`, `extracted_by` = the clean `Reader:` actor, optional
     `attributed_to`, and `title` = single-line `paraphrase`). Decide reuse from
     the refusal `data` payload alone:
     - If `source-assertion` succeeds, record its minted address on
       `source_assertion: <address>`.
     - If `source-assertion` refuses with `"existing"` in `data`
       (`data.existing`, same resolved `source`, including across
       `source-correct` redirects), reuse `data.existing[0].address` and record
       `source_assertion: <address>` on that statement in the note.
     - If `source-assertion` refuses with `data.anchor_conflict` (identical
       extraction from byte-identical material already anchored in a distinct
       `source` record) or `data.occupied` (wrong-kind occupancy at that
       address), never reuse that address: omit `source_assertion:`, keep the
       statement in the reading note, and disclose the conflict to the person.
     Keep every proposition-less statement in the reading note without
     `proposition:` or `source_assertion:`.
   - *Reader's commentary,* labelled as the reader's own and never as the paper's.
   - *Relevance to the project* and proposed follow-ups.
7. **Offer follow-up questions for confirmation.** Offer `question` records;
   mint only those the person confirms. End by listing minted addresses, any
   reused same-source `source-assertion` addresses, any conflicts, and anything
   that could not be done.

The statements and any source assertions minted from them are one reader's
attributed extraction and the note says so: unadjudicated, inert in `belief`,
and not to be used as an independent check of the same reader's summary.

## Promote an earlier reading

Given an existing reading note (by `coord:` address, unpinned or `@<revision>`;
by stored `note:<project>.<local>.<uid>` id; or explicitly chosen in step 0,
step 1 or step 3), promote statements into world `source-assertion` records
without re-reading the paper:

1. **Read local records only.** Read the note in full with `record`, and read its
   cited `source:` address with `record` (which resolves through `source-correct`
   redirects to the live `source` and lists `source assertions` already anchored
   in it). Keep the note's own resolved source UID as the anchor, including
   when it has a positive link. Make zero `quarry` calls, `doi.org` or external metadata fetches,
   `source` or `source-correct` calls, or paper-file reads.
2. **Extract reading provenance strictly from the note's *Reading* section.**
   - `source`: the `source:` address cited in the note (pass as cited;
     `source-assertion` resolves `source-correct` redirects to the live `source`).
   - `sha256`: the 64 lowercase hex digits recorded in the note.
   - `extent`: `full` for `full text`, or `abstract` for `abstract`.
   - `extracted_by`: the actor identifier from the note's `Reader:` field,
     stripping any trailing provenance clauses such as `, observed through ...`,
     and never substituting the promoting session's own model (`recorded_by` is
     stamped automatically from the session writer).
   - `media_type`: the explicit MIME type when the note names one, or mapped from
     unambiguous representation descriptions: `PMC JATS XML` or
     `PubMed abstract XML` → `application/xml`, `BioC JSON` or
     `DOI registry JSON` → `application/json`, `PDF` → `application/pdf`,
     `Markdown` → `text/markdown`, `HTML` → `text/html`, plain text →
     `text/plain`. If the note's description leaves `media_type` ambiguous,
     confirm it with the person rather than guessing.
   If any required provenance field (`source`, `sha256`, depth, `Reader`) or a
   promoted statement's `span`, `where` or `paraphrase` is missing from the
   note, stop and name what is missing rather than guessing or re-reading
   silently.
3. **Verify propositions and signs.**
   - A statement that already carries `proposition: proposition:<id>` uses that
     `proposition` and its recorded `stance` as `sign`, after verifying with
     `record` that `proposition:<id>` resolves to a record of
     `kind == "proposition"`.
   - A statement lacking a `proposition:` line is promoted only when the person
     supplies or confirms both an existing `proposition:<id>` (verified with
     `record` to have `kind == "proposition"`) and the statement's `sign`
     (`asserts`, `denies`, `hypothesizes`) on *that* proposition, since a
     sentence asserted in prose may `deny` an oppositely polarised proposition.
     Never call `claim` or search world propositions unprompted.
   - Statements with no proposition remain in the reading note and are reported
     as unpromoted for lack of a proposition.
4. **Normalise and mint without revising the note.** For each statement to
   promote, normalise `span`, `where`, `media_type` and optional `attributed_to`
   to Unicode NFC if decomposed, and call `source-assertion` with `title` set to
   the single-line `paraphrase`. Decide reuse from `record` on the note's
   resolved `source` (verifying full `read` and `bears_on` equality if reusing
   before calling `source-assertion`) or `"existing"` in `source-assertion`'s
   refusal `data` payload alone: if that exact assertion is already recorded on
   the same resolved `source` (including when `source-assertion` refuses with
   `data.existing`), treat it as idempotently present and report
   `data.existing[0].address` (or the verified existing address). Never reuse
   `data.anchor_conflict` (distinct `source` anchor) or `data.occupied`
   (wrong-kind occupancy): leave the statement in the reading note and disclose
   the conflict. Never revise the reading note. End by reporting newly minted
   `source-assertion` addresses, reused same-source addresses, any
   `data.anchor_conflict` or `data.occupied` conflicts, and unpromoted statements
   left in the note.
