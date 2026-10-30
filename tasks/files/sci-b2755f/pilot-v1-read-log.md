# Pilot read log v1 — 2026-10-30

Reader: controller (Codex). This is an audit record of permitted metadata and
local record-field inspection, not an extra scientific store. No new result
source is authorized by its contents. See the source ledger for title incidents.

## Supported local reads

From the isolated worktree's python directory:

```sh
uv run science status --config "$SCIENCE_CONFIG"
uv run science project-show --config "$SCIENCE_CONFIG" --project coord:4dbcb70467a87cd727cc6303cbd697a2
uv run science project-show --config "$SCIENCE_CONFIG" --project coord:4dbcb70467a87cd727cc6303cbd697a2 --continue <returned-cursor>
```

Status exit 0: corpus coverage/counts, not holdings or verdicts.
Project-show: first heading page, then 16384-byte coordination page, then 1753-byte
final page containing Q09's standing title. Its project revision is
e45271d5810b679f060926e0cb305f74. An initial continuation omitting --project exited
3 with no-current-project; rerun with the same explicit project succeeded and
progressed to completion. No project-select command or session selection write.
No actual primary title/content was read by these coordination pages.

Direct fields: three proposition files, two specs, three question files, one
composite; exact inspected raw transcriptions are retained in local-records-v1.json.
Their source-file SHA-256 values and unvalidated status are in the frozen discovery
attachment. Two corpus manifests and active/domain/reproduction contract dimensions
were read. Old reproduction X1 was compared byte-for-byte with current X1, not
counted as another source. Scientific result/holding record bodies and patient
payloads were not displayed or inspected. Existing repository source definitions
(spec.py, paths.py, estimand/adapter code) are labelled code evidence.

## Bibliographic metadata calls

Registered quarry checkout and own environment, revision
7008433c8d3007b38a8fb08598e7e3ed49e965eb. Exact starting queries and positions are
in pilot-source-ledger-v1.md; commands, actual invocation timestamps, statuses and
raw metadata output names follow. No abstract or generic result snippet requested.

```sh
uv run --frozen quarry search --in pubmed --native <exact-query-below> -n 6 --json
uv run --frozen quarry show pubmed:40906971 --json
```

```jsonl
{"number": 1, "family": "broad", "query": "\"multiple myeloma\"[Title/Abstract] AND (question* OR limitation* OR challenge*) AND (\"1900/01/01\"[Date - Publication] : \"2026/10/30\"[Date - Publication])", "limit": 6, "started": "2026-10-30T10:54:46.406054+00:00", "exit": 0, "stdout": "search-01.json", "stderr": "search-01.stderr"}
{"number": 2, "family": "heterogeneity", "query": "\"multiple myeloma\"[Title/Abstract] AND (heterogeneity OR subtype* OR generaliz*) NOT review[Publication Type] AND (\"1900/01/01\"[Date - Publication] : \"2026/10/30\"[Date - Publication])", "limit": 6, "started": "2026-10-30T10:59:28.491560+00:00", "exit": 0, "stdout": "search-02.json", "stderr": "search-02.stderr"}
{"number": 3, "family": "progression", "query": "\"multiple myeloma\"[Title/Abstract] AND (initiation OR progression OR precursor) NOT review[Publication Type] AND (\"1900/01/01\"[Date - Publication] : \"2026/10/30\"[Date - Publication])", "limit": 6, "started": "2026-10-30T10:59:31.607709+00:00", "exit": 0, "stdout": "search-03.json", "stderr": "search-03.stderr"}
{"number": 4, "family": "measurement", "query": "\"multiple myeloma\"[Title/Abstract] AND (measurement OR proxy OR \"cell mixture\" OR purity) NOT review[Publication Type] AND (\"1900/01/01\"[Date - Publication] : \"2026/10/30\"[Date - Publication])", "limit": 6, "started": "2026-10-30T10:59:34.193344+00:00", "exit": 0, "stdout": "search-04.json", "stderr": "search-04.stderr"}
{"number": 5, "family": "microenvironment", "query": "\"multiple myeloma\"[Title/Abstract] AND (microenvironment OR immune) NOT review[Publication Type] AND (\"1900/01/01\"[Date - Publication] : \"2026/10/30\"[Date - Publication])", "limit": 6, "started": "2026-10-30T10:59:36.910805+00:00", "exit": 0, "stdout": "search-05.json", "stderr": "search-05.stderr"}
{"number": 6, "family": "treatment", "query": "\"multiple myeloma\"[Title/Abstract] AND (response OR resistance) NOT review[Publication Type] AND (\"1900/01/01\"[Date - Publication] : \"2026/10/30\"[Date - Publication])", "limit": 6, "started": "2026-10-30T10:59:39.568138+00:00", "exit": 0, "stdout": "search-06.json", "stderr": "search-06.stderr"}
{"number": 7, "family": "persistence", "query": "\"multiple myeloma\"[Title/Abstract] AND (relapse OR persistence OR \"clonal evolution\") NOT review[Publication Type] AND (\"1900/01/01\"[Date - Publication] : \"2026/10/30\"[Date - Publication])", "limit": 6, "started": "2026-10-30T10:59:42.171913+00:00", "exit": 0, "stdout": "search-07.json", "stderr": "search-07.stderr"}
```

## Identity/probe reads

The identity lookup selected only a deterministic exposed roster publication for
a section-route probe, not a scientific finalist. All roster PMID/DOI matches for
40906971 resolve to bcd-25-0005-antigen-loss-cohort. Its referenced cohort groups
are bcd-25-0005-antigen-loss-cohort and commpass, both discovery/exposed; additional
cohorts were not assumed absent. Current source/mapping hashes are in setup.
The request was intended to isolate availability metadata before analyst display.

```jsonl
{"at": "2026-10-30T10:56:19.150039+00:00", "kind": "bibliographic-identity", "source": "pubmed:40906971", "route": "uv run --frozen quarry show", "exit": 0, "file": "probe-bibliography-v1.json"}
{"at": "2026-10-30T10:57:11.128683+00:00", "kind": "live-section-probe", "source": "pubmed:40906971", "pmcid": "PMC12514755", "url": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12514755/fullTextXML", "requested_section": "data-availability", "raw_file": "probe-article-raw-v1.xml", "fulltext_read_attempt": false, "known_cohorts": "bcd-25-0005-antigen-loss-cohort and commpass; discovery/exposed in current roster; additional cohorts not yet cleared", "verdict": "route unavailable, fail closed", "error": "HTTPError: HTTP Error 500: "}
```

The request raised HTTPError 500 before any article or selected-section read.
The rehearsed standard-library extractor was not given a live article; live
response shape remains unverified. One probe only; no body fallback or hidden
retry. The exact extractor source/self-check is preserved in rehearsal-v1-read-log.md
and accepted by rehearsal-v1-review-report.md. No later abstract/section request.

## Freeze and subsequent assessment

The self-contained discovery-inventory-v1.md was attached and its tasks show entry
and exact SHA-256 equality verified before any available-data comparison:
f221d359e15b13a0ba61e5019d0878c46ce6b0470a77375f103f9d76cc62f6f3.
It preserves the full source ledger, all proposed premises/leads and dispositions.

Phase B read roster projections for gse179929, commpass-open-60-counts and the
probe entry; counted modality/longitudinal flags; inspected only metadata in the
two working dataset record manifests. No patient rows, count values, private
outputs or masks were opened. Paired/longitudinal metadata raises a sample-unit
check, not proof that X1 violated independence. All actual holdings unknown.

Exposure routing: three confirmed title statements and seventeen possible titles,
source/date/reader/mapping uncertainty preserved in the source ledger and
mm-eca42c; stopped sources used for no ranking/consequence claim. Routing is not
disposition. No scientific record, roster, policy or assignment write.

## Retained input fingerprints

Under the task's persistent $WORK_ROOT/science/sci-b2755f directory, these exact
inspection inputs/logs remain frozen for the branch/report review. Raw API
responses are bibliographic metadata only; no raw primary paper was retained.
Read the task retained-item checkpoint for the complete directory manifest.

| File | SHA-256 |
|---|---|
| local-records-v1.json | 17a78f669c9e42637a06311d749d67c5f3a5f0975c51a985743e36f2d674c5da |
| roster-mapping-v1.json | 89ca9f4025df8c84420098f3eb4c4f373d14f1940ab99c02f3032175f6ec4d5e |
| phase-b-metadata-v1.json | 4f377c856baa0437509c869e7ed28e5a81725c9dcfd4dde7e8786ff2219740cd |
| pilot-query-log.jsonl | b7a10eaff28fbe21ff07e6ac2a01ef353576424ff87d9b6e43a56ccfb9eb09af |
| pilot-read-log.jsonl | 21ba0601217a47ca35f2d8c39cc878497896e97da7384da502f9286583f492e9 |
| world-status-v1.txt | 729b18f756d6cafe8b8f4321e38df18d95a0743e6f3fa1f4c4fdcea0bb95a679 |
| project-show-health-v1.txt | 1f2a6065df8597bd91985c23faa19884b19061453c87bfcce09e0beeb61a3f0c |
| project-show-health-cursor-v2.txt | 5f7a8fcc8657bbf9d56a09d6a040b2ab06cbfb4a927282c80e1ae2f2dbd05c15 |
| project-show-health-cursor-v3.txt | eb24ff53da4d2dbb13ff09a4ba8d38dd391ee1ab63cf59a1d896e5bbe8d17d1b |
