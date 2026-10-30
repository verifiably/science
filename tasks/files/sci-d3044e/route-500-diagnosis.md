# Europe PMC fullTextXML HTTP 500: diagnosis

Date: 2026-10-30, Claude Code (claude-opus-5-5), at the user's request. No article, abstract or section text was displayed or inspected.

## Finding

The Europe PMC REST route `/webservices/rest/{PMCID}/fullTextXML` serves only the Europe PMC open-access subset. For a PMC-held article outside that subset it returns a generic Spring error (`{"status":500,"error":"Internal Server Error",...}`, 151 bytes, application/json) instead of 404. The failure is deterministic per article, not a transient outage, so waiting for availability will never clear it.

The probe source pubmed:40906971 / PMC12514755 has metadata flags isOpenAccess=N, inEPMC=Y, inPMC=Y. Both frozen probes (v1, v2) were therefore bound to fail.

## Evidence (status codes and metadata flags only; bodies discarded except the 151-byte error JSON)

| Request | OA flag | Status |
|---|---|---|
| PMC12514755 (probe source) | N | 500, reproduced |
| PMC3257301 (unrelated control) | OA | 200 |
| 3 unrelated non-OA PMC articles (query "soil microbiology") | N | 500, 500, 500 |
| 3 unrelated OA PMC articles (same query) | Y | 200, 200, 200 |

Pilot non-incident sources (13 PMIDs from pilot-sources-v1.json; incident sources excluded, no titles requested or shown):

| Class | Count | fullTextXML |
|---|---|---|
| OA, in PMC | 4 (42926231, 42928255, 42930200, 42935712) | 200 for all 4 (body sent to /dev/null, not read) |
| Not OA, in PMC | 2 (40906971, 42923674) | 500 for both |
| Not in PMC | 7 | no full-text route |

The isOpenAccess flag predicted the status for 6/6 pilot PMC sources and 7/7 controls.

## Not tested

NCBI routes (efetch db=pmc, PMC BioC, the PMC OA service) are expected to carry the same open-access restriction; this was not checked.
