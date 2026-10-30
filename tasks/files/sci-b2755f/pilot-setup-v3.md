# Pilot setup v3: access eligibility before retrieval

Frozen 2026-10-30 before new metadata/source requests. Task sci-d3044e; parent sci-b2755f. Analyst Codex. Approved plan/spec and source/exposure boundaries unchanged. User correction recorded on sci-d3044e 13:10:33 UTC supersedes the v1/v2 wait-for-availability assumption. Europe PMC fullTextXML serves the OA subset; PMC12514755 has isOpenAccess=N and is not an eligible probe. Official supporting documentation: https://dev.europepmc.org/doc/EBI_Europe_PMC_Web_Service_Reference.pdf and https://europepmc.org/docs/Europe_PMC_Export_Formats_Feature_List.pdf. Generic HTTP500 behavior is evidenced by the diagnostic attachment, not guaranteed for every failure.

## Bounds and selection

Carry forward 7/24 literature searches, 33/80 screened identities, 0/18 deliberate full-text-reading attempts; two failed isolated probes, zero article sections/abstracts read. Diagnostic status/flag calls by the separate user-requested investigation are outside this scientific search sequence, retained in route-500-diagnosis.md, and yielded no scientific assertions. Metadata identity/eligibility batches here are conservatively charged as searches and each newly screened PMID against the identity cap. No budget reset.

One new live isolation probe, selected from a roster-derived pool after metadata confirms OA and all known implicated cohorts are exposed discovery. The four OA non-incident sources already screened have no roster match, so none yet qualifies for that probe. Select the first eligible item in the first twelve known-exposed publication identities in roster-entry order (list below); this deterministic choice tests the reader, not scientific priority. Reconcile DOI as well as PMID against all entries before probing. If selection fails, record source/shape failure without declaring the provider down; never display the body to find a section. Any corrected mechanism must retain the tested boundary.

Preflight further sources using projected Europe PMC lite metadata: identity, PMID/DOI/PMCID, isOpenAccess/inEPMC flags, date and publication type when available; suppress abstracts and unrequested fields before display. Non-OA, non-PMC and stopped incident sources remain metadata-only. OA grants no cohort/result permission. After a successful permitted probe, request only isolated availability and necessary design sections for unknown mappings, and map every implicated cohort before results. Reviews: titles/isolated references only. Further searches cover the six original families plus open other, with counterevidence capacity. Do not select scientific priorities by convenient datasets; retain coverage gaps.

## Reader and preservation

Reuse the existing select-section.py after its fresh synthetic sentinel/refusal self-check. HTTP bytes remain in memory and are projected before analyst display; raw article bytes are never persisted. Log every request/failure; no silent retries. Retain permitted selected sections off-tree for audit, attach attributed summaries and short excerpts only. Freeze new discovery before comparative feasibility. No world, policy or assignment writes, patient/matrix reads, biological analysis, publication or service.

All retained manifests verified (42 scratch, 35 v1, 3 v2, 36 workspace files). Current mm roster/catchments/reservation/exposure-policy hashes match v1. Quarry current revision 23ac8d6821ffc7f5748c5b2b141b56e87f4e173e has inspected PubMed ESummary metadata-only _row; use its registered checkout and own uv environment. Refresh configured-world and contract evidence before new comparative claims. Main changes await integration reconciliation. mm-eca42c remains undisposed and its sources excluded.

## Probe pool (metadata only)

- PMID 29296884; roster entries gse105216; known exposed discovery cohorts gse105216.
- PMID 30254104; roster entries gse107843, gse99634, gse99635; known exposed discovery cohorts gse99636.
- PMID 29895968; roster entries gse108159; known exposed discovery cohorts gse108159.
- PMID 29712909; roster entries gse111310; known exposed discovery cohorts gse111310.
- PMID 31142679; roster entries gse113295, gse113642; known exposed discovery cohorts gse113295, gse113642.
- PMID 30275468; roster entries gse114961; known exposed discovery cohorts gse114961.
- PMID 30157427; roster entries gse117131; known exposed discovery cohorts gse117131.
- PMID 29563136; roster entries gse118985; known exposed discovery cohorts gse118985.
- PMID 30518681; roster entries gse120444; known exposed discovery cohorts oetjen-2018.
- PMID 24144643; roster entries gse122231; known exposed discovery cohorts swog-s0120.
- PMID 31221779; roster entries gse124188; known exposed discovery cohorts gse124188.
- PMID 30635013; roster entries gse124858, gse124859, gse124860; known exposed discovery cohorts gse124860.

Extractor SHA-256: 9a80f5f5fbc1bf53cd33ba08c62198d741f7a247fd75d10dad3e469d6e20a443
