# quarry: domain layers over scientific resources, with one CLI and skills

Status: draft 2026-10-10, for review. Task `sci-ba7150`.

Sources: the evidence on `sci-ba7150` (the myeloma dataset survey, `mm-159cb7`); the
survey's clients in the multiple-myeloma roster (`roster/http.py`, `roster/sources/`);
the shared CLI conventions (ops `docs/specs/2026-09-20-cli-conventions-design.md` and
its `cli.toml`); this repository's `domains` setting and the projects spec's §6.1
("biology is a contract, not a project"); FAIRsharing's record types; Bioregistry.

## 1. What this is

Agents reach scientific resources by writing their own clients, one per task. The
myeloma survey shows what that costs:

- ENA wildcard queries containing a hyphen, period or space silently return 0, so 22
  of 38 cell-line terms never ran.
- BioStudies expands phrase queries through an ontology with no off switch.
- figshare reports no total, and returns publisher supplements as separate items.
- Zenodo refuses page sizes above 25 when unauthenticated.
- GEO needed a restructured client to bring a 1.5–6 h harvest down to about 10 min.
- ENA's count endpoint returned HTTP 500 during a re-harvest.

Each fix lives in one survey's code and is relearned by the next.

quarry is a new project: one CLI, a Python library under it, and agent skills. Through
them, people and agents reach these resources with fixes that are kept, and the
interface is the same in every science domain. Biology comes first. Chemistry, physics
and astronomy are meant to follow without changing the interface.

## 2. Terms

- **Resource**: one external thing quarry knows: GEO, HGNC, GO, Zenodo, SIMBAD.
- **Role**: what a resource is (§4.1). A resource has one or more roles.
- **Access route**: how a resource is reached: a REST API, a query endpoint, bulk
  download, or a local CLI tool (§4.2). A resource has one or more routes.
- **Adapter**: the code for one access route of one resource. Its pitfall fixes live here.
- **Domain**: a lens over the catalog, named as science names its domains: `core`,
  `biology`, later `chemistry`, `physics`, `astronomy`. A domain selects resources;
  it owns none.
- **Catalog**: the versioned description of every resource and domain, held as data in
  the repository.

## 3. Decisions

| Decision | Chosen | Rejected, and why |
|---|---|---|
| What a domain holds | sources, identifier schemes, skills, and a link to the beliefs domain contract | data access only (two different things called "biology"); skills only (clients stay hand-rolled) |
| Shared resources | a `core` domain of the same shape, used alongside any other | a hidden base every domain inherits (nothing to list, nothing to select) |
| Types | two axes, roles and access routes; a resource may hold several roles | one flat type list (it mixes what a resource is with how it is reached: GEO is one repository with three routes) |
| Domain as lens or namespace | lens: one CLI and global ids; the domain selects catalog, search scope and skills | namespace (`quarry biology show …`, or one CLI per domain): shared resources appear twice, and the grammar is the same only by discipline |
| Repositories | one project holding the runtime, `core` and every domain | one repository per domain: separate CLI tables, tests and adoption, which drift |
| Domain names | science's domain names (`biology`) | short names (`bio`): two names for one thing |
| The beliefs contract | the domain file names it; its code stays in beliefs | moving the code here: beliefs is the only thing that interprets it |
| Relation to the kernel | a plain automation-tier CLI that makes no kernel acts. It describes records and their files; the kernel's `acquisition` operation (beliefs cut 35) retrieves the bytes and mints the dataset with its report (§9) | a `fetch` of quarry's own feeding `science dataset`: a second download path whose provenance the kernel never sees, and `science dataset` holds one file per record; a science command or protocol CLI: data access is upstream of belief |
| Identifiers | Bioregistry's canonical prefixes, from a pinned snapshot | a prefix table of our own |
| Caching | none; recorded responses serve the tests | a response cache now: no evidence yet that harvests need one |

## 4. The model

### 4.1 Roles

Roles fall into two families. The set is closed: a new role is an edit to this spec
and to `quarry check`. Each role carries a FAIRsharing crosswalk where one exists.

*Roles that name or define:*

| Role | What it does | Examples | FAIRsharing |
|---|---|---|---|
| `identifier-scheme` | assigns identifiers, little else | HGNC, ORCID, DOI, NCBI Taxonomy | identifier schema |
| `vocabulary` | a fixed term list with little structure | MeSH qualifiers, ENA checklist values | terminology artefact |
| `ontology` | terms with formal relations | GO, UBERON, ChEBI | terminology artefact |
| `data-model` | classes and slots for structuring data, not a term list | BioLink, schema.org, IVOA ObsCore | model/format |

*Roles that hold data:*

| Role | What it does | Examples | FAIRsharing |
|---|---|---|---|
| `repository` | takes submissions; holds deposited datasets under accessions | GEO, ENA, BioStudies, Zenodo, MAST | repository |
| `knowledgebase` | curated records about entities | UniProt, Ensembl, PubChem, SIMBAD | knowledgebase |
| `literature-index` | records about publications | PubMed, OpenAlex, arXiv, ADS | knowledgebase |

A resource lists every role it plays: HGNC is `identifier-scheme` and `knowledgebase`;
ChEBI is `ontology` and `knowledgebase`. File formats (FASTQ, FITS, mmCIF) are not a
role in this version. `files` reports a file's media type when the resource gives
one, and a `format` role is added when a command needs one.

### 4.2 Access routes

| Route | Examples |
|---|---|
| `rest` | E-utilities, ENA portal API, Zenodo API |
| `query-endpoint` | SPARQL, TAP/ADQL, BioMart |
| `bulk` | FTP, HTTPS file trees, S3 |
| `local-tool` | sra-tools, edirect |

A route declares what the adapter needs to use it well: its base URL, its rate (minimum
interval between requests), the service whose allowance the rate draws on, its
authentication (none, optional key, required key) and the variable that holds the key,
its page-size cap, and whether it reports a total.

### 4.3 Roles decide the verbs

| Verb family | Roles it serves |
|---|---|
| `id check`, `id normalize`, `id resolve` | `identifier-scheme`, and any resource whose records have ids |
| `term search`, `term show` | `vocabulary`, `ontology` |
| `term ancestors` | `ontology` |
| `search`, `show`, `files` | `repository`, `knowledgebase`, `literature-index` (`files` only where records have files) |
| `resources list`, `resources show`, `domains list` | the catalog itself |

`data-model` has no verbs in this version; it is catalogued so agents can find it.
A verb used on a resource that lacks its role is refused with the error kind
`unsupported_role`.

## 5. Repository layout

```
quarry/
  src/quarry/
    catalog/                    # inside the package, so an installed quarry carries it
      resources/<resource>.toml # one file per resource, whatever domains list it
      domains/<domain>.toml     # membership, beliefs contract, default search set
      bioregistry.json          # pinned snapshot; its version is in catalog/SOURCES.toml
    cli.py                      # the click surface; thin over the library
    catalog.py                  # loading and checking the catalog
    ids.py                      # CURIE parsing, normalization, resolution
    http.py                     # the shared client (§9)
    query.py                    # shared and domain filters, compilation contract (§8)
    acquisition.py              # the acquisition request `files --acquisition` emits (§9)
    adapters/<name>.py          # one module per resource, or per service several resources share (OLS)
  skills/
    quarry/SKILL.md             # using the CLI, in any domain
    quarry-<domain>/SKILL.md    # which resource answers which question, and its pitfalls
  tests/
    fixtures/<resource>/        # recorded responses
  tools/cli.toml                # vendored from ops
```

A resource file is the same whether one domain lists it or three, so PDB is described
once even though both biology and chemistry list it.

## 6. Catalog format

A resource:

```toml
id = "ena"
name = "European Nucleotide Archive"
roles = ["repository"]
prefixes = ["bioproject", "insdc.sra"]  # Bioregistry prefixes this resource owns (§7)
fairsharing = "FAIRsharing.…"        # its FAIRsharing record, when one exists
adapter = "quarry.adapters.ena"     # several resources may name one service adapter

[[routes]]
kind = "rest"
url = "https://www.ebi.ac.uk/ena/portal/api"
min_interval = 0.5
service = "ebi-ena"                    # routes naming one service share one throttle (§9)
auth = "none"
reports_total = true

[[pitfalls]]
summary = "a wildcard cannot contain '-', '.' or a space and matches substrings"
handling = "terms compile to exact-equality clauses; wildcards are never generated"
evidence = "mm-159cb7: 22 of 38 cell-line terms returned 0"
```

A domain:

```toml
id = "biology"
summary = "life-science repositories, knowledgebases, identifiers and ontologies"
beliefs_contract = "biology"           # the contract science activates by this name
beliefs_contract_version = 1           # the version this domain was written against
includes = ["core"]
resources = ["geo", "ena", "biostudies", "go", "uberon", "ncbitaxon"]
search_default = ["geo", "ena", "biostudies"]
filters = ["organism"]                 # domain filters this domain defines (§8)

[facet_namespaces]                     # the contract's facet namespaces, as Bioregistry prefixes
HGNC = "hgnc"
```

A domain's effective resources and search set are its own plus those of every domain
it `includes`, in that order. `core` has `search_default = ["zenodo", "figshare"]`, so a
biology search covers GEO, ENA, BioStudies, Zenodo and figshare. Literature indexes are
searched by naming them with `--in`.

`quarry check` validates the catalog under the shared `check` meaning: it prints nothing
and exits 0 when the catalog is clean, and prints its findings on stdout and exits 1
otherwise. It finds:

- an unknown role or route kind;
- a resource with no adapter module, or an adapter with no resource file;
- a prefix that is missing from the Bioregistry snapshot (the resource may declare
  `local_prefixes` for schemes Bioregistry lacks, and says why);
- a domain naming a missing resource;
- a prefix owned by two resources, or a facet namespace that maps to no known prefix;
- a pitfall without `handling` or `evidence`.

## 7. Identifiers

- **Output.** Every id quarry prints is a CURIE in Bioregistry's canonical form:
  `geo:GSE24080`, `pubmed:…`, `doi:10.…`.
- **Input.** quarry accepts Bioregistry synonyms (`PMID:` and `pmid:` both become
  `pubmed:`) and canonical prefixes in any case.
- **Ownership.** Each prefix has at most one owning resource in the catalog; `show`
  and `files` on a CURIE go to its owner. Other resources may still emit ids under
  that prefix as results or cross-references (BioStudies emits `geo:` cross-references,
  and Zenodo and figshare emit `doi:`). A CURIE whose prefix has no owner is refused
  (`no_owner`). In the first version `doi:` has none: it is a cross-reference only,
  until a resource that owns it (DataCite, Crossref) is added.
- **Bare accessions.** `id normalize GSE24080` matches the patterns of owned prefixes
  only, not the whole snapshot: several Bioregistry patterns (`ena.embl`'s
  `^[A-Z]+[0-9]+(\.\d+)?$`) match nearly every accession. When exactly one owned prefix
  matches, it prints that CURIE. When several match, it fails with the error kind
  `ambiguous_id`, whose detail names the candidates. Other commands refuse a bare
  accession with the same error rather than guess.
- **Resolution.** `id resolve <curie>` prints the URLs the snapshot and the owning
  resource give for the id. `id check <id>…` takes the shared `check` meaning: nothing
  and exit 0 when every id is well formed for its prefix; otherwise one finding per id
  on stdout (`unknown_prefix` or `malformed`) and exit 1.
- **Outside Bioregistry.** Schemes Bioregistry lacks (many in astronomy) are
  `local_prefixes` on their resource and follow the same rules.
- **The roster.** Its id forms map as follows (Bioregistry, checked 2026-10-10):

  | Roster form | quarry form | Note |
  |---|---|---|
  | `geo:GSEn` | `geo:GSEn` | owned by GEO |
  | `bioproject:PRJ…` | `bioproject:PRJ…` | owned by ENA |
  | `sra:SRP…` | `insdc.sra:SRP…` | `sra` is not a Bioregistry prefix or synonym |
  | `pmid:n` | `pubmed:n` | synonym |
  | BioStudies `E-GEOD-n` | `arrayexpress:E-GEOD-n`, with cross-reference `geo:GSEn` | `biostudies` covers `S-…` accessions only |
  | Zenodo record | `zenodo.record:n` | `zenodo` is a synonym |
  | figshare item | `figshare:n`; a publisher supplement's paper DOI goes in `publication` (§8.3), and the item's own DOI in `xrefs` | a `local_prefix`: Bioregistry has none. The roster used the paper DOI as a group's id; quarry keeps each item under its own id, so `show` and `files` resolve it, and grouping supplements under their paper stays the consumer's step |

## 8. Command surface

| Command | Purpose |
|---|---|
| `domains list` | the domains, their resources, and their beliefs contracts |
| `resources list [--domain D] [--role R] [--route K]` | the catalog |
| `resources show <resource>` | roles, routes, limits, pitfalls, crosswalks |
| `search <terms>… [--in R]… [--domain D] [filters] [--exact] [--native Q] [--allow-partial] [--since] [--until] [-n]` | records across data-holding resources |
| `show <curie>` | one record |
| `files <curie> [--file GLOB] [--acquisition]` | a record's files: URL, size, checksum and media type when known; with `--acquisition`, the request the kernel's acquisition takes (§9) |
| `id check\|normalize\|resolve <id>` | identifiers |
| `term search <text> --in R`, `term show <curie>`, `term ancestors <curie>` | vocabularies and ontologies |
| `check` | validate the catalog |
| `skills build` | regenerate the skills' resource notes from the catalog (§10) |

The commands follow the shared conventions: `--json` and `--pretty`, `-n/--limit`,
`--since` and `--until` (bounds on the record's release date), the error object on
stderr, and exits 0, 1 and 2. `check` and `id check` take the shared `check` meaning.
Local options (`--domain`, `--in`, `--role`, `--route`, `--exact`, `--native`,
`--allow-partial`, `--file`, `--acquisition`, `--trace`, and the domain filters) become
rows in ops `cli.toml` before they are built, under a `[cli.quarry]` header (§11). The
shared `--config` and `-C` are bound too (§8.1).

### 8.1 The lens

`--domain` selects the catalog that `resources list` shows and the resources a
`search` without `--in` covers. `--in` names resources explicitly and overrides the
domain's `search_default`. Commands that take a CURIE need no domain, since the prefix
names the resource.

The domain comes from, in order of precedence (highest first):

1. `--domain`;
2. `QUARRY_DOMAIN`;
3. `domain` in the configuration file: the one `--config` names, else the nearest
   `quarry.toml` at or above the working directory (or the `-C` directory). A workspace
   such as multiple-myeloma sets `domain = "biology"` there once;
4. `core`.

Every result names the domain it used. quarry does not read science's world
configuration; that file describes a world, not a workspace.

### 8.2 Filters and queries

- **Shared filters** apply to every data-holding resource: the terms, `--since`,
  `--until` and `-n`. Each term is a phrase, and the phrases combine with OR, as the
  roster's queries do: `search myeloma plasmacytoma` finds records matching either.
  Filters combine with AND, with each other and with the terms. `-n` caps each
  resource's listing, not the merged results; results are merged in the order of the
  search set.
- **Domain filters** are declared by a domain (biology: `--organism`, which takes a
  taxon name or `ncbitaxon:` CURIE).
- **Compilation.** Each adapter compiles the filters into its resource's native query,
  with the resource's escaping rules: ENA terms become exact-equality clauses, and
  GEO's become `[All Fields]` phrases with `[ORGN]`.
- **Matching.** Each coverage entry says how the resource matched the terms:
  `"match": "exact"` (ENA's equality clauses) or `"expanded"` (BioStudies expands
  phrases through an ontology and has no off switch). `--exact` requires exact
  matching everywhere.
- **Refusal.** An adapter that cannot express a filter refuses (`unsupported_filter`,
  naming the resource and filter) rather than drop it. Under `--exact`, BioStudies
  refuses, so a biology search with `--exact` needs `--in` without it.
- **`--native Q`** passes one resource's own query unchanged, in place of compiled
  terms and filters. It requires exactly one `--in`, and it refuses terms, domain
  filters and `--exact` beside it (a usage error, exit 2). `--since` and `--until`
  are refused too, since dates belong in the native query. `-n` stays allowed: result
  limits are request parameters separate from the query (E-utilities' `retmax`, ENA's
  `limit`), so quarry applies it through paging and reports `"complete": "limited"`.

### 8.3 Output and completeness

`search` returns one object:

```json
{"domain": "biology",
 "coverage": [{"resource": "ena", "native": "(study_title=\"myeloma\" …) AND tax_eq(9606)",
               "match": "exact", "total": 412, "returned": 412, "complete": "total"}],
 "results": [{"id": "bioproject:PRJNA…", "resource": "ena", "kind": "dataset",
              "title": "…", "date": "2021-03-04", "summary": "…",
              "xrefs": ["geo:GSE…"], "publication": "pubmed:…",
              "domain_fields": {"biology": {"organism": "Homo sapiens", "taxon": "ncbitaxon:9606"}}}],
 "warnings": []}
```

- **`complete`** is `total` when the listing equals the resource's reported total, and
  `short-page` when the resource reports no total and paging ended on a short page
  (figshare). A listing shorter than the reported total is a failure, not a result.
- **`-n`.** A search with `-n` stops early by request; its coverage says
  `"complete": "limited"`.
- **Failures.** When one resource fails, the command fails with that resource's error
  object, and no results are printed. `--allow-partial` instead completes with exit 0,
  marks the resource `"complete": "failed"` in coverage with its error, and adds a
  warning naming it. The failure stays in the result rather than in the exit code,
  since the conventions allow no result beside an error.
- **Reproducibility.** `native` is the query actually sent, so a harvest can be
  rerun.
- **Publication.** `publication` is the one paper a record belongs to (a figshare
  supplement's parent paper, a GEO series' citation), as a CURIE, or absent. It is
  kept apart from `xrefs` because one record can carry several DOIs: the figshare item
  `figshare:34254439` has its own DOI (ending `.t007`) and its paper's, and consumers
  group by the second. Every other cross-reference stays in `xrefs`. When a resource
  names several papers, the first is `publication` and the rest go to `xrefs`, with a
  warning.
- **Kinds.** `kind` is `dataset`, `record` or `publication`. The fields every domain
  shares are fixed. Domain-specific fields sit under `domain_fields.<domain>`, so a
  consumer of `core` fields never meets a biology field it does not expect.

## 9. Runtime

- **One HTTP client**, new and on httpx (as lit uses). It keeps what the roster's
  urllib `Http` learned (per-source intervals, a User-Agent, retries on 429 and 5xx)
  and adds what it lacked:
  - one throttle per service and key, shared across a process: routes naming the
    same `service` draw on one allowance, so GEO and PubMed, both on NCBI
    E-utilities (`service = "ncbi-eutils"`), never exceed it together. Two quarry
    processes on one host do not coordinate; a harvest that needs more than one runs
    them in sequence;
  - a User-Agent naming quarry and its version;
  - retries with backoff on 408, 429, 5xx and transport errors, honouring
    `Retry-After`;
  - a log of every request, printed to stderr under `--trace` (`QUARRY_TRACE`
    mirrors it).
- **Redaction.** A route declares where its credential travels (`key_param`, such as
  E-utilities' `api_key` query parameter, or `key_header`). The client replaces that
  value with `REDACTED` in every trace line, error detail and recorded fixture, and
  fixture matching ignores it. A credential therefore never reaches a log, a committed
  file or an error object.
- **Keys.** A route names its key variable (`key_env`, for example `NCBI_API_KEY`)
  and its keyed interval (`keyed_min_interval`). When the variable is set, the key is
  sent and the keyed interval applies. Key variables keep each service's own names, so
  they are an exception to the `QUARRY_<OPTION>` rule. The conventions give a CLI header
  no `exception` field, so the exception is a comment beside the `[cli.quarry]` header
  until ops provides one.
- **Paging.** Adapters page by the route's cap and never request more (Zenodo: 25
  without a key).
- **Acquisition, not download.** quarry does not download a record's files. The
  kernel's `acquisition` operation (beliefs cut 35) does: per resource it looks at a
  URL under recorded bounds, hashes the bytes, optionally stores them, and mints one
  dataset with its act report in one transaction. `files <curie> --acquisition`
  prints the request that operation takes, as one JSON value:
  - `title`: the record's title;
  - `locator`: `accession:<canonical CURIE>` (`accession:geo:GSE24080`). The
    kernel's locator check splits at the first colon only, so the whole CURIE is the
    remainder, and `figshare:123` and `zenodo.record:123` stay distinct;
  - `resources`: one per file (after `--file`), each a unique name, its URL, and
    `expected` as a sha256 digest when the resource publishes one. Resources that
    publish only MD5 (GEO) leave `expected` unset, since the kernel's instrument
    checks sha256.

  The kernel retrieves over http and https only. An adapter gives each file's
  documented HTTPS location (GEO and ENA serve their FTP trees over HTTPS as well).
  When a file has none, `--acquisition` fails with `unsupported_transport`, naming
  the file, rather than emit a request the kernel would refuse. Plain `files` still
  lists every location the resource gives.

  Retrieval bounds (timeout, byte ceiling) are the consuming command's to set, not
  quarry's. Several files make one dataset, not one record per file. science exposes no command
  for acquisition yet. A `science acquire` command that takes this request is a
  science task, filed when this plan lands, and it is a dependency of the end-to-end
  path but not of quarry's first version.

## 10. Skills

- **`quarry`** teaches the CLI in any domain:
  - the verb families and the lens;
  - reading `coverage` before trusting a count;
  - `--native` as the exit for queries the shared filters cannot express;
  - recording a harvest's `native` queries.
- **`quarry-<domain>`** teaches the domain: which resource answers which question
  (deposited data, curated entity facts, literature), and each resource's pitfalls.
  Its resource notes are generated from the catalog's `pitfalls` (`quarry skills
  build`, checked in), so a fix and its warning cannot drift. Hand-written guidance
  sits around the generated part.

The skills ship from this repository through hq's declared links, as the tasks skill
does.

## 11. Relations to other projects

- **science and beliefs.** quarry makes no kernel acts. A domain file names the beliefs
  contract (`biology`, version 1) it corresponds to, and `domains list` shows the pair;
  quarry does not read beliefs, so the version is a declaration a reviewer checks when
  the contract changes. A workspace finds records and their files with quarry, then
  hands `files --acquisition` to the kernel's acquisition (§9).
- **lit.** lit owns literature as a world model: OpenAlex snapshots, corpora and walks.
  quarry's `literature-index` resources serve live per-record lookup and search. They
  do not replace lit's snapshot. lit has PubMed pipelines and `world place --pmid` of
  its own, so the two overlap on PubMed: quarry searches it live, lit places records in
  its world. Whether lit's PubMed and OpenAlex API calls move onto quarry's adapters is
  a later question for lit, and quarry's first version changes nothing there.
- **multiple-myeloma.** The roster becomes quarry's first consumer once the biology
  domain covers its resources. Its migration is a task in that project, filed when
  this plan lands. The roster's fixtures are re-recorded rather than reused, since its
  replay matches by substring and ignores request bodies (§12).
- **ops.** quarry joins the shared CLI vocabulary as an automation-tier CLI. The
  project is registered with tasks under the prefix `quarry` first, since a
  `[cli.<name>]` header must name a registered project. Its header is `[cli.quarry]`
  with `project = "quarry"`, env `QUARRY`, default output `pretty`, and the
  key-variable exception noted beside it (§9). Its rows are edited into ops `cli.toml` first, then
  vendored, and one conformance test checks them.
- **The verifiably family.** quarry is not a member; like lit, it is a tool that
  workspaces use. Joining later is an adoption under the family's README contract.

## 12. Testing

- **Fixtures.** Tests never reach the network. Each adapter's tests replay recorded
  responses from `tests/fixtures/<resource>/`. Matching is on method, path, sorted
  query parameters and the request body (GEO's esummary and figshare's search are
  POSTs), not on substrings, so a changed request fails loudly.
- **Recording.** `just record <resource>` refreshes one resource's fixtures against
  the live service; recording is a person's or agent's deliberate act, never part of a
  test run.
- **Redaction.** A test sets a sentinel key, runs authenticated requests under
  `--trace` and through recording, and asserts the sentinel appears in no trace line,
  fixture or error object.
- **Shared throttle.** A test interleaves GEO and PubMed calls on a fake clock and
  asserts the combined rate stays within the E-utilities allowance.
- **Pitfalls.** Each catalog pitfall has a test that reproduces its trigger from a
  fixture and asserts the handling: the ENA hyphenated term, the Zenodo page cap, the
  figshare short page, an incomplete ENA listing, and the two-DOI figshare item
  (`figshare:34254439`), whose parent DOI must land in `publication` and its own in
  `xrefs`.
- **Conformance.** The conformance test from ops checks the parser surface against
  `cli.toml`.
- **Live checks.** `just live` runs one small query per route against the real
  services. It is opt-in and reports which routes answered.
- **Front door.** The justfile provides `setup`, `test-one`, `test-fast`, `test` and
  `check`, recorded through `tt`.

## 13. First version

**Domains.** `core` and `biology`.

**Resources.**

| Resource | Roles | Domain | Why first |
|---|---|---|---|
| GEO | repository | biology | the roster's restructured client and SuperSeries handling |
| ENA | repository | biology | exact-equality compilation; the truncation guard |
| BioStudies | repository | biology | organism from facets; the `E-GEOD-` to `geo:` mapping |
| Zenodo | repository | core | the page cap |
| figshare | repository | core | short-page completeness; publisher supplements carry their paper's DOI |
| PubMed | literature-index | core | the roster's review search |
| GO, UBERON, NCBITaxon | ontology | biology | the `term` verbs; one shared adapter over EBI's Ontology Lookup Service (OLS) serves all three, and more ontologies are a resource file each |

The `id` verbs work from the pinned Bioregistry snapshot (§7), which is catalog input
rather than a resource. The first six rows come from the roster, with its known
pitfalls; their fixtures are recorded anew (§11). The ontologies and the snapshot make
the `id` and `term` families real in the first version, so the role model is proven on
more than repositories. dbGaP, EGA, GDC, cBioPortal and OpenAlex follow as
ordinary additions: a resource file, an adapter, fixtures.

## 14. Other domains: a check on the contract

The model generalizes when the other sciences need no new verbs or layout.

| Domain | Repository | Knowledgebase | Literature | Identifiers | Vocabulary or ontology | Data model | Domain filters |
|---|---|---|---|---|---|---|---|
| chemistry | PubChem deposits, Zenodo | PubChem, ChEMBL, PDB | core | InChIKey, CAS (proprietary) | ChEBI | — | `--formula`, `--inchikey` |
| physics | HEPData, CERN Open Data | NIST constants | INSPIRE | INSPIRE ids, DOI | — | — | `--collaboration` |
| astronomy | MAST, ESO archive | SIMBAD (TAP) | ADS, arXiv | `local_prefixes` for survey ids | IVOA UCDs | IVOA ObsCore | `--object`, `--position`, `--radius` |

Astronomy brings the `query-endpoint` route (TAP/ADQL) and identifiers Bioregistry
lacks. Chemistry brings identifiers that are computed rather than assigned (InChIKey),
which `id check` validates by pattern. Both fit the model as written. Each domain
arrives with its own spec, which may extend this one but not change its verbs.

## 15. Out of scope

- Writes to any external resource (submission, deposition); science's commons spec
  owns publishing.
- Downloading bytes: the kernel's acquisition does it (§9).
- A response cache.
- A query language of quarry's own beyond the shared and domain filters and
  `--native`.
- Moving the beliefs domain contracts out of beliefs.
- An MCP server; the CLI and skills come first, and an MCP surface is a later choice.
