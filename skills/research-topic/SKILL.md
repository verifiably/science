---
name: research-topic
description: Use when asked to research a topic's background in a science project and record a synthesis grounded in identified sources.
---

# Research a topic

Produce one background synthesis grounded in identified sources. Read
[literature-evaluation.md](literature-evaluation.md) before evaluating literature.

## Boundaries and preconditions

Write scientific records only through science commands, named here by their
declaration names. Write no repository file and make no commit. Edit only the
topic the person asks to supplement with `revise`, and source identifiers through
`source-correct` as below. Leave signing any coreference attestation to the
person. Do not edit other existing records.

First check that science commands are reachable, that a project is selected, and
that `quarry` runs. If any check fails, stop with a plain explanation. Ask the
person to run `project-select` when needed; never select a project for them.
Do not locate or install quarry; the session environment must supply it.

Before reading results, follow any exposure policy in the workspace's guide or
protocol. If it leaves a paper's status unresolved, stop at bibliographic metadata
for that paper and say so. An accessible abstract is not permission to read it.

## Workflow

1. **Check what exists.** Use `project-show` to list topics and `record` to read
   overlaps. If a topic overlaps, ask the person to choose supplementing it,
   recording a narrower topic, or stopping. Never overwrite silently.
2. **Scope.** State the bounds; explicitly narrow a broad request. The chosen
   scope opens the synthesis.
3. **Find literature and confirm identity.** Search PubMed and Europe PMC through
   quarry (`--in`), reading every coverage row before trusting counts. Harness web
   search can suggest candidates and is the main discovery route outside index
   coverage. A candidate becomes a reference only after identity is confirmed.
   Existing world sources are references by address.

   Confirm identity by the first applicable route: an existing source found by
   `record`; quarry's index record; for a DOI absent from both indexes, the DOI
   registry's own metadata record fetched by the harness via content negotiation
   at `doi.org`, whose title must match; finally identifiers supplied and confirmed
   by the person. In that last route, explicitly record that identity was not
   cross-checked. Model memory cannot confirm identity.

   Quarry has no DOI lookup: search each index for the DOI in its own native
   syntax (`--native`), then `show` the returned provider id. Read its
   cross-references, confirm DOI and PMID refer to the same work, and use every
   available confirmed identifier together in subsequent world lookups. Conflicting
   identifiers or titles stop work on that paper. Compare titles after normalising
   case, whitespace, markup and closing punctuation. A new source takes the title
   of the route that confirmed identity, without PubMed's closing full stop.
4. **Find or record each source.** Call `record` with every confirmed identifier
   together; inspect its identifiers, corpora and `correctable here` result.
   - Absent: call `source` with the confirmed title and all confirmed identifiers.
     If lookup used only one identifier, tell the person and state in the synthesis
     that an existing record under a different identifier could not be ruled out.
   - Found carrying every identifier now known: use it.
   - Found under fewer identifiers, `correctable here` true (only the write root
     holds it): call `source-correct` with the index record as grounds.
   - Found under fewer identifiers, `correctable here` false (another corpus holds
     it, including a read mount or the write root plus a publication): use it as it
     stands and state the further identifier in the synthesis. Never correct or
     duplicate it; `source-correct` would refuse.
   - Several matches: identify the version represented by the material using
     title, identifiers and independent version evidence. Read the `source
     coreference (live evidence)` rows. Only a `positive` row on two exact
     current sources attests that specific pair. `historical-redirect` and
     `unavailable` give context. Linked neighbors are navigation targets.
     A missing peer adds no candidate, and the sole independently identified
     live source remains eligible.
   - If an exact pair is `unassessed`, disclose the possible duplicate and
     use the confirmed-identifier rank (DOI, PMID, ISBN, accession) after
     independent identity checks succeed. For `contested` or `negative`,
     disclose the disagreement and keep the records separate.
   - Different verified versions remain separate. If a positive link joins
     verified different versions, such as a preprint and final article with
     different DOIs, disclose the disagreement and cite each version
     independently at its own reading depth.

   If the material leaves the citable version unresolved, ask which version
   was read before citing or counting that item. If two confirmed distinct
   revisions resolve to one source UID (such as two arXiv revisions with only
   their base DOI), explain that the UID cannot identify the version read.
   Seek an independently identifiable source before citing or counting that
   item. Continue on the other sources and record this item in coverage
   limitations.

   Only DOI, PMID, ISBN and accession are accepted. Use an arXiv paper's
   `10.48550/arxiv.<id>` DOI, not an arXiv, PMCID or URL scheme. A candidate with no
   accepted identifier is named in coverage and excluded from the query.
5. **Read to the required depth.** Follow the exposure policy and the evaluation
   rules. Topics usually read abstracts; repeating numbers, cohort definitions,
   method parameters or validation claims requires full text.

   Obtain text in order: a person-supplied file; open-access full text at a location
   quarry lists; an abstract from the index's structured record (PubMed
   E-utilities or Europe PMC core), or, outside those indexes, the DOI registry's
   metadata record if it contains one. Outside the indexes, full text is read only
   from a supplied file. Add no new retrieval route. If nothing is reachable, keep
   the source recorded, say it was not read, and attribute no findings to it.

   Fetch remote text byte for byte into session scratch outside repositories,
   using a tool that saves the unchanged response. Compute sha256 over the exact
   bytes read. A summarising page reader supplies neither quotable nor hashable
   text. Without a byte-exact fetch, read only a supplied file. Never use publisher
   landing pages to judge access, pirated copies, or model memory as text.
6. **Write the synthesis.** Use `topic` with a name, non-empty body and this query
   form, naming every source the synthesis cites:

   ```yaml
   version: science.view-query.v1
   clauses:
     - all:
         - addresses: ["source:<digest>", "source:<digest>"]
   ```

   Count each confirmed citable version once when the source records used
   are directly positive for every pair. Check this across separate identifier
   lookups as well as a single lookup, and disclose the other linked addresses.
   Keep overlapping groups unresolved when any required pair is absent or its
   version is unconfirmed. Cite the source for each passage actually read.
   If passages came from two addresses for one confirmed version, keep both
   actual addresses in the query and prose while counting one version.

   The body contains scope; what is established; what is uncertain or contested
   (the disagreement and what it turns on); gaps; relevance to the project; open
   questions; and coverage (searches, unreachable or unread text, candidates
   lacking an identifier). Synthesize across sources rather than listing summaries.

   Attribute every statement as a named source's statement (address and reading
   depth), an existing world result (address), or the writer's own labelled
   reasoning or recollection. For each reading give the representation and origin,
   sha256, date, depth (`abstract` or `full text`), reader (person or model and
   version), primary/secondary provenance and separate publication status
   (peer-reviewed, preprint, other). Preserve identity-confirmation route and the
   source-lookup disclosures above. Abstract-only readings support no durable
   conclusion. Hedge to match evidence; store no strength or confidence grade.

   When supplementing the topic chosen in step 1, use `revise` with its unpinned
   `coord:<project>/<local>` address and a complete resulting synthesis/query.
   Read pinned identity from `record`, but omit `@<revision>` for `revise`.
   A new query must name at least one resolving address, with all addresses and
   closure anchors resolving. A carried query is not rechecked on renaming.
   Never mint a topic without a source, an empty stub, or a vocabulary referent.
   If nothing citable was found, say so and write nothing.
7. **Recommend next readings.** Name papers that deserve `/science:research-paper`.
   Offer open questions as `question` records and mint only those the person
   confirms. End by listing minted addresses and anything that could not be done.
