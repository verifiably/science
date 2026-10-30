# Pilot continuation v2 outcome

Date: 2026-10-30. Reader: Codex. Task sci-d3044e remains incomplete.

The one live data-availability probe frozen in pilot-setup-v2.md returned HTTP 500 in 4.458 seconds at 13:00:47 UTC. No response error body, article, abstract or section was displayed or inspected. No raw paper was saved. The section extractor did not receive live article bytes, so live section isolation remains unverified. This observes a failed endpoint request; it does not establish a provider bug or its root cause.

The historical pilot-v1-report.md and discovery-inventory-v1.md remain the scientific assessment and frozen discovery inventory. No new scientific evidence or comparison arose in v2; no replacement inventory or three-candidate report is claimed. Tasks 1–2 remain accepted. No final completion review or branch integration is justified by this outcome.

## Verification

- Verified recorded manifest hashes and all entries: scratch 38, pilot-v1-evidence 35, plan workspace 36.
- Roster, catchments, reservation and exposure-policy hashes still match v1 exactly; reused their recorded cohort/group mapping. Both known probe cohorts are discovery/exposed; additional cohorts remain unchecked.
- The unchanged run-local extractor passed its synthetic section/sentinel/refusal self-check. This proves mechanics, not live provider shape.
- mm-eca42c remains todo; its incident sources remain excluded from ranking/consequences.
- New work is evidence/task documentation only. No product code changed and no runtime suite was required or run in this continuation. Hygiene is recorded separately on the task after execution.

## Budget and next action

Cumulative pilot usage remains 7/24 searches, 33/80 unique bibliography identities, 0/18 deliberate full-text-reading attempts, zero completed full texts, zero abstracts and zero sections read. Two isolated route probes have failed, one each in frozen v1 and v2; neither was a full-text-reading attempt. No invisible retry, reset of cumulative caps, fallback endpoint or broad search was used.

Agent next action: after route availability changes, resume the retained worktree, verify manifests, freeze a newly versioned one-probe setup within the remaining cumulative caps, and establish permitted live section isolation. Then refresh advanced source/world/quarry contracts, inspect primary sources across the original families under cohort permissions, freeze the expanded inventory before comparison, and complete the report and fresh whole-branch review. Preserve/reconcile main changes before eventual local integration. If a different retrieval route is selected, demonstrate the same extraction boundary before use; this outcome authorizes no additional request by itself.

No process will retry in the background. No protected results, patient data, world records, policies or assignments were accessed or changed. No push or host-pointer change.

## Exact probe metadata

```json
{
  "at": "2026-10-30T13:00:47.517520+00:00",
  "source": "pubmed:40906971",
  "pmcid": "PMC12514755",
  "url": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12514755/fullTextXML",
  "section": "data-availability",
  "attempt": 1,
  "fulltext_read_attempt": false,
  "setup_sha256": "50c1c9e2a77be18b9a5cd5c237aa9557ccf0d741f4a1f9ccb995da615cd02f76",
  "verdict": "route unavailable; no error body or article read",
  "error_type": "HTTPError",
  "http_status": 500,
  "seconds": 4.458
}
```
