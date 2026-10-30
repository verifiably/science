# Assumption-sweep compact behavioral controls v1

Date: 2026-10-30. Controller: Codex. All ten workers freshly reported
codex/gpt-6.1-sol via relay model. Five no-skill and five guided samples;
all full returned texts are retained below, manually read by controller.
Synthetic input: controls-discovery-v1.md, SHA-256
47a11e63b4b26e085dfe296a3f9337636389661b1129a55dc3e158d3bced24b1.
Oracle: python/tests/fixtures/sweep-assumptions/expected-review.md.

## Prompts and limitations

Common request: read ONLY the supplied synthetic scenario; execute its Research
request, giving actual concise top-three answer, exact reach endpoint sets and
source-read decisions/requests. No edits, network, task claims, plan/oracle reads,
or source replies. Offered sections remain unread. Return full text, no files;
freshly report relay model identity. Controls receive no sweep skill.
Guided workers additionally receive the authored skill/template and controller's
actual confirmed discovery attachment/hash; prompt asks to preserve required
qualifications and sensitivity. Literal locations resolve to the scenario and
skill files named above; only portable locations are reproduced here.

This is bounded skill-authoring evidence, NOT a full workflow rehearsal or a
randomized causal estimate of the skill's effect: guided prompts also mention
sensitivity and provide a freeze, whereas controls lack those instructions.
The common research request and scenario bytes are identical. Source reads and
interrupted phase A/B remain untested here. All inputs/results are invented.

## Manual scoring

| Sample | Unique P1 claims/questions despite duplicates/cycle | Source decisions and unread evidence | Provenance/unevaluated C2 | Q4 retained; catalogue not holding | Stated-only sensitivity | Recommendation |
|---|---|---|---|---|---|---|
| control 1 | pass | pass | pass | pass | omitted | Q2,Q3,Q4 |
| control 2 | pass | pass | pass | pass | omitted | Q3,Q2,Q4 |
| control 3 | pass | pass | pass | pass | omitted | Q2,Q3,Q4 |
| control 4 | pass | pass | pass | pass | omitted | Q2,Q3,Q4 |
| control 5 | pass | pass | pass | pass | omitted | Q2,Q3,Q4 |
| guided 1 | pass | pass | pass | pass | pass | Q1,Q4,Q3 |
| guided 2 | pass | pass | pass | pass | pass | Q1,Q4,Q3 |
| guided 3 | pass | pass | pass | pass | pass | Q1,Q3,Q4 |
| guided 4 | pass | pass | pass | pass | pass | Q1,Q4,Q3 |
| guided 5 | pass | pass | pass | pass | pass | Q2,Q4,Q3 |

Observed gap, not an invented failure: controls recognize inferred links but omit
recomputed sensitivity. Example control 3: “L2 and L8 are analyst-inferred
reliance links” without stated-only claim {C1}/question {Q1} for P1.
Control 2 prioritizes Q3 partly because it is the “closest match to the catalogued
bulk measurements”; the template separates impact and feasibility. No control
fabricates access, counts duplicated C1 as independent, or erases Q4.

Guided core sets: P1 claims {C1,C2}, questions {Q1,Q2}; stated-only P1 {C1}/{Q1};
P3 loses all endpoints without inferred L8; P4 {C4}/{Q4} unchanged. Seven
consequence judgments, C2 unevaluated, nine stated/two inferred links.
Guided source prose sometimes calls ten supplied entries ten screens; exact
unique bibliography is eight identities (S1/S2/S3 collapse). This compact screen
does not demonstrate a live counter or a new read. The full rehearsal must report
entry and unique counts separately. Variation in ordering is retained; no winner
was selected. The skill remains a manual judgment workflow.


## Full return: control 1

My provisional top three are Q2, Q3 and Q4. This is a qualitative recommendation, not an expected-value ranking; the inventory supplies neither probabilities nor a utility target.

1. **Q2: Does signal ordering identify temporal change?** Scale comparability and calibration form the broadest shared dependency cluster. Resolving them could affect C1, C2, Q1 and Q2. C2’s consequence remains unevaluated, and cross-sectional measurements do not establish temporal change. Check paired-visit availability and calibration before proposing an analysis.
2. **Q3: Does cell mixture change the bulk proxy’s meaning?** This directly tests a measurement interpretation potentially relevant to the catalogued bulk package. Mixture or orthogonal-assay metadata are needed; their availability is unknown.
3. **Q4: What distinguishes stable states from reversible responses?** Retain this scientifically important question, including the colleague’s preference, while acknowledging that the inspected catalogue supplies no suitable longitudinal perturbation/recovery assay. It contains no evidence of attractors.

Q1 remains in the inventory. I defer it because it shares the scale/calibration dependencies and additionally needs populations or visits beyond those compared. None of these questions is established as executable from D1: public listing does not establish possession, kernel holding or suitability.

**Exact reach sets.** Following the proposed links backward from premise to dependents, transitively, and excluding the starting endpoint:

- P1 → {P2, C1, C2, Q1, Q2}
- P2 → {P1, C1, C2, Q1, Q2}
- P3 → {C3, Q3}
- P4 → {C4, Q4}
- C1 → {Q1}; C2 → {Q1, Q2}; C3 → {Q3}; C4 → {Q4}
- Q1, Q2, Q3, Q4 → ∅ each.

P1 and P2 form one cycle. Its distinct external downstream endpoints are {C1, C2, Q1, Q2}; counting the two premises independently would exaggerate breadth. These are report-local reach sets, not validated kernel dependencies or evidence of causal effects. Reach beyond the inventory is unknown. C1 may be reinterpreted; reversal is not established.

**Source decisions and requests.** The following requests identify desired sections; no responses were available, so all remain unread:

- **S1:** request `S1:abstract`; its declared single cohort maps to exposed discovery R-A.
- **S2/S3:** duplicate deposits/publications of S1; normalized DOI `10.0000/A` matches R-A. Do not request another abstract or count independent support.
- **S4:** PMID maps to R-A but DOI maps to R-B. Request `S4:data-availability`, limited to isolated cohort metadata. Keep results and abstract unread until the conflict is resolved.
- **S5:** request `S5:data-availability` and metadata-only portions of `S5:methods` to establish every cohort. Skip any portion inseparable from results; no abstract request yet.
- **S6:** known mixed R-A/R-B results are nonseparable. Keep metadata-only; no abstract request.
- **S7:** unknown cohorts and only a whole article offered. Skip; no whole-body fallback.
- **S8:** request `S8:references` for navigation only; leave review body unread.
- **S9:** confirmed result exposure occurred in the supplied metadata despite unknown mapping. Record the incident and route it to the controller for disposition; stop this source and make no abstract request. Other sources can continue.
- **S10:** maps to reserved, unexposed R-C. No abstract request.

The unrelated title “Temporal observations” is a separate possible exposure with uncertain meaning, not another confirmed result read.

I read only the supplied scenario document, including its transcriptions, metadata screen, S9 result text and feasibility catalogue. Identical r1 deposits do not establish validation or current holding. Empty dimensions, qualifiers and applicability do not establish generalizability. X1’s calibration restriction, falsification statement and assumption are distinct authored statements. H-missing and H-invalid supply no inspected validated hypothesis; H1’s selection and X1’s target locator establish no reliance predicate.

Reviewer identity: **codex/gpt-6.1-sol**.

No offered source sections, external records or network sources were read. Recommendations remain provisional because cohort resolution, package possession and assay suitability are incomplete.


## Full return: control 2

My provisional top three are Q3, Q2 and Q4. This is a research recommendation, not a uniquely determined ranking: the inventory supplies neither probabilities nor a utility target.

1. **Q3 — Does cell mixture change the meaning of the bulk proxy?** This directly tests whether C3 needs a narrower interpretation. It is the closest match to the catalogued bulk measurements, although mixture annotations or orthogonal measurements remain unknown.
2. **Q2 — Does signal ordering identify temporal change?** This challenges C2’s interpretation and the shared scale/calibration dependency. Cross-sectional ordering alone does not establish temporal change; paired visits and calibration are required, and pairing is unknown.
3. **Q4 — What distinguishes stable states from reversible responses?** This directly challenges C4’s mechanistic interpretation. Its scientific importance survives the absence of a suitable assay, but execution requires longitudinal perturbation/recovery observations and relevant timing. Nothing supplied establishes attractors.

Q1 remains valuable, but I would first resolve interpretation and measurement before pursuing generalization to additional populations or visits. That ordering is my judgment, not a source conclusion.

**Exact reach within the proposed link inventory**

Following dependent → premise links backward, counting each endpoint once and excluding the starting premise itself:

| Premise | Direct dependents | All reachable dependents |
|---|---|---|
| P1 | {C1, C2, P2} | {P2, C1, C2, Q1, Q2} |
| P2 | {P1} | {P1, C1, C2, Q1, Q2} |
| P3 | {C3} | {C3, Q3} |
| P4 | {C4} | {C4, Q4} |

P1/P2 form a cycle; their joint external reach is {C1, C2, Q1, Q2}. Reach outside this inventory is unknown. L2 and L8 are analyst-inferred links; all links remain report-local judgments rather than stored kernel reliance predicates.

These sets measure structural reach, not effect size or likelihood. The worksheet supports possible reinterpretation of C1, not demonstrated reversal; C2’s consequence remains unevaluated.

**What I read and would request**

I read only the supplied scenario document, including its metadata screen and transcriptions. No offered source section was received or read.

- **Request S1:abstract:** its declared single cohort resolves to previously exposed discovery R-A. S2 and S3 duplicate that study; normalized DOI 10.0000/A matches 10.0000/a. I would avoid duplicate reading and evidence counting.
- **Stop S4:** its PMID maps to R-A while its DOI maps to unresolved, unexposed R-B. Record the identifier conflict and route it for disposition; request no further section.
- **Request S5:data-availability:** isolated cohort metadata only. Resolve every cohort before requesting its abstract. If additional metadata is necessary, request S5:methods only with cohort metadata separately isolated; otherwise skip it.
- **Skip S6 results:** ACC-A/ACC-B results are explicitly nonseparable and ACC-B is unresolved/unexposed. Its abstract is ineligible.
- **Skip S7:** unknown cohorts and no isolated section; no whole-article fallback.
- **Request S8:references:** isolated navigation only; do not read its review body.
- **Stop S9:** the supplied phenotype-conditioned result was actually read with unknown cohort mapping. Record confirmed result exposure and route the incident for disposition; request no abstract. Separately record the uncertain title “Temporal observations” as possible exposure, not another confirmed result read.
- **Skip S10 abstract:** its DOI resolves to reserved, unexposed R-C.

C1’s deposits and S2/S3 provide no independent replication. Revision r1 is transcribed, but validation and current holding are unknown. Empty dimension, qualifier and applicability maps do not establish generality or erase X1’s calibrated-sample restriction. Its falsification and assumptions remain authored text. H-missing and H-invalid supply no validated hypothesis record; H1’s selection and X1’s target are locators, not reliance judgments.

D1 is public-listed metadata, not demonstrated possession, kernel holding or assay suitability. All requested sections remain unread, so this recommendation uses no additional publication evidence.

Reviewer identity: codex/gpt-6.1-sol.

Skipped additional files, source sections, network access and validation checks. The ranking remains provisional because cohort resolution, measurement annotations and longitudinal feasibility are incomplete.


## Full return: control 3

My provisional top three are **Q2, Q3, Q4**, ranked by interpretive importance within this inventory, not estimated probability or utility:

1. **Q2: Does signal ordering identify temporal change?** Scale comparability and calibration affect the interpretation of C1 and C2 and reach both Q1 and Q2. C1 might be reinterpreted; reversal is unestablished, and C2’s consequence remains unevaluated. Paired visits and calibration are required; D1 does not establish pairing.
2. **Q3: Does cell mixture change the meaning of the bulk proxy?** This directly tests whether C3’s interpretation needs narrowing. D1 offers a potential starting point, but mixture annotation or an orthogonal assay remains necessary and unknown.
3. **Q4: What distinguishes stable states from reversible responses?** This could reinterpret C4 and deserves a place despite the missing longitudinal perturbation/recovery package. Cross-sectional persistence does not establish a stable mechanism or attractor.

Q1 remains in the inventory. I defer it because generalization needs additional populations/visits and calibration while the underlying temporal interpretation remains unresolved. These priorities are my judgments; the colleague’s preference alone does not settle them. D1’s public listing establishes neither possession nor suitability.

**Exact reach sets**

Following dependent → premise links backward to find affected dependents, with each starting premise excluded from its own transitive endpoint set:

| Premise | Direct dependents | All transitive dependents | Reach restricted to claims/questions |
|---|---|---|---|
| P1 | {C1, C2, P2} | {P2, C1, C2, Q1, Q2} | {C1, C2, Q1, Q2} |
| P2 | {P1} | {P1, C1, C2, Q1, Q2} | {C1, C2, Q1, Q2} |
| P3 | {C3} | {C3, Q3} | {C3, Q3} |
| P4 | {C4} | {C4, Q4} | {C4, Q4} |

P1 and P2 form a cycle, not independent corroboration. L2 and L8 are analyst-inferred reliance links; the remaining links have explicit author attribution. Reach is report-local and unknown beyond this inventory; counts alone do not establish research value.

**Source decisions and requests**

- **S1:** Request `S1:abstract`: its single declared cohort maps to discovery, previously exposed R-A.
- **S2:** Duplicate deposit of S1; no additional read or independent evidence.
- **S3:** DOI normalization maps it to the same eligible study as S1. Abstract permitted, but skip a redundant request.
- **S4:** Request `S4:data-availability` only. PMID maps to R-A while DOI maps to R-B; resolve the conflict and all cohorts before any abstract.
- **S5:** Request `S5:data-availability` first, isolated to cohort-identifying metadata. No abstract while cohorts remain unknown; consider methods only if a necessary metadata section can be isolated without results.
- **S6:** Mixed R-A/R-B results are nonseparable; keep metadata-only and skip the abstract. No further request presently needed.
- **S7:** Skip: whole-article access cannot isolate permitted metadata.
- **S8:** Request `S8:references` for navigation only; skip the review body.
- **S9:** Confirmed result exposure already occurred during metadata reading while cohort mapping was unknown. Stop this source, record the incident here, and request controller disposition. Do not request its abstract or use its result in ranking. Other sources may proceed.
- **S10:** Reserved, unexposed R-C; skip its abstract.

The unrelated title “Temporal observations” is a separate possible-exposure flag with uncertain meaning, not another confirmed result exposure.

I read only the supplied scenario document, including its transcriptions, metadata screen and feasibility catalogue. All requested sections remain **unread**, because no controller responses were available.

The record probe establishes inspected r1 transcriptions, not kernel validation or current holding. Carrier A/B and S2 do not multiply C1’s support. Empty dimensions, qualifiers and applicability supply no additional declared scope; X1’s calibrated-sample restriction still matters. Its falsification text is an authored criterion, not an observed falsification. H-missing and H-invalid provide no validated hypothesis; H1’s selection and X1’s target are locators, not additional reliance judgments.

Reviewer identity: codex/gpt-6.1-sol.

Skipped: network, additional files, source bodies, writes and task claims. Main limits: unread requested evidence, unknown cohort mappings, and unestablished package possession and suitability.


## Full return: control 4

My provisional top three are **Q2, Q3, Q4**. This is a reasoned research agenda, not a uniquely determined ranking: no probabilities or utility target are supplied.

1. **Q2 — Does signal ordering identify temporal change?** Scale comparability and calibration underpin both C1 and C2 and reach Q1/Q2. First establish comparability; testing temporal change also requires paired visits, which D1 does not establish.
2. **Q3 — Does cell mixture change the bulk proxy’s meaning?** This directly tests an alternative interpretation of C3. D1’s bulk measurements are relevant, but mixture annotations or orthogonal assays remain unknown.
3. **Q4 — What distinguishes stable states from reversible responses?** This could reinterpret C4 and deserves scientific priority despite the missing longitudinal perturbation/recovery assay. The colleague’s preference does not establish feasibility, and the inventory supplies no evidence of attractors.

Q1 remains valuable but requires additional populations/visits and calibration. I place interpretation checks first; the evidence does not compel that ordering.

**Exact reach**, traversing the supplied report-local links from premise to dependents, transitively, excluding the starting node:

| Premise | All reachable endpoints | Claim/question endpoints |
|---|---|---|
| P1 | {P2, C1, C2, Q1, Q2} | {C1, C2, Q1, Q2} |
| P2 | {P1, C1, C2, Q1, Q2} | {C1, C2, Q1, Q2} |
| P3 | {C3, Q3} | {C3, Q3} |
| P4 | {C4, Q4} | {C4, Q4} |

P1/P2 form one cyclic dependency component; they do not provide independent corroboration. L2 and L8 are analyst-inferred reliance. Reach establishes possible dependence, not reversal, effect size, or likelihood. C2’s consequence remains unevaluated; C1’s reinterpretation is proposed, not demonstrated reversal.

**Source decisions and requests:**

- **S1:** request `S1:abstract`; its declared single cohort maps to exposed discovery R-A.
- **S2/S3:** recognize duplicates of S1, including normalized DOI `10.0000/A`; skip additional reads and count no independent support.
- **S4:** conflicting identifiers map to R-A and unresolved R-B. Stop, record the identity conflict, and request controller disposition; no abstract read.
- **S5:** request `S5:data-availability` for isolated cohort-identification metadata. If insufficient, request `S5:methods` only insofar as cohort metadata can be isolated. Resolve every cohort before requesting any abstract.
- **S6:** skip result reads: ACC-A/ACC-B results are nonseparable and ACC-B is unresolved/unexposed.
- **S7:** skip; no isolated metadata section is available, and whole-article fallback is prohibited.
- **S8:** request `S8:references` solely for navigation; skip review body.
- **S9:** confirmed prohibited result exposure already occurred in the supplied metadata. Record the quoted result, unknown cohort mapping, and exposure incident; stop this source and request controller disposition. Do not request its abstract. Record “Temporal observations” separately as possible, uncertain exposure.
- **S10:** skip abstract; its cohort maps to reserved, unexposed R-C.

I read only the supplied scenario document. All requested sections remain unread because no controller responses are available. S9’s result was nevertheless actually seen.

The duplicate C1 deposits are one claim, not replication. Their r1 transcriptions establish neither kernel validation nor current holding. Empty dimensions, qualifiers, and applicability supply no additional scope restrictions; X1’s calibrated-sample restriction, exact falsification, and scale-comparability assumption remain distinct authored statements. Neither H-missing nor H-invalid supplies an inspected validated hypothesis. H1’s selection and X1’s targeting are locators, not stored reliance predicates.

Reviewer identity: **codex/gpt-6.1-sol**.

Skipped: additional files, network, source bodies, and validation of holdings. The ranking remains conditional on unresolved access, measurement metadata, and study suitability.


## Full return: control 5

My provisional top three are Q2, Q3 and Q4. This is a judgment from the supplied inventory, not a uniquely established ranking: no probability model or utility target supports one.

1. **Q2: Does signal ordering identify temporal change?** P1’s scale-comparability issue reaches both C1 and C2, then Q1 and Q2. Q2 directly tests the temporal interpretation; I defer Q1’s broader generalization question because it overlaps this unresolved foundation. C2’s consequence remains unevaluated.
2. **Q3: Does cell mixture change the bulk proxy’s meaning?** This tests an independent measurement ambiguity. D1’s cross-sectional bulk package is a possible starting point, conditional on obtaining composition or orthogonal-assay metadata; suitability is unestablished.
3. **Q4: What distinguishes stable states from reversible responses?** This could reinterpret C4 and deserves retention despite the missing longitudinal perturbation/recovery package. The colleague’s preference is reasonable, but the inventory does not establish attractors or settle Q4’s priority over the other questions.

D1 alone establishes neither package possession nor suitability. Pairing is unknown for Q2; mixture annotation is unknown for Q3; suitable longitudinal evidence for Q4 is absent from the inspected catalogue.

**Exact reach sets.** Following report-local reliance links backward, from premise to dependents, with each starting item excluded:

| Starting item | Reachable endpoints |
|---|---|
| P1 | {P2, C1, C2, Q1, Q2} |
| P2 | {P1, C1, C2, Q1, Q2} |
| P3 | {C3, Q3} |
| P4 | {C4, Q4} |
| C1 | {Q1} |
| C2 | {Q1, Q2} |
| C3 | {Q3} |
| C4 | {Q4} |
| Q1, Q2, Q3, Q4 individually | {} |

P1/P2 form a cycle, not independent corroboration. These sets include analyst-inferred links L2 and L8 and establish structural reach, not falsity, reversal or effect size. Reach beyond this inventory is unknown. S2 and carrier B do not multiply C1 or its reach.

**Source decisions and requests.**

| Source | Decision |
|---|---|
| S1 | R-A is discovery and previously exposed; request `S1:abstract`. |
| S2 | Duplicate deposit; no additional read requested. |
| S3 | DOI normalization identifies the S1 study; skip its duplicate abstract. |
| S4 | PMID maps to R-A while DOI maps to R-B. Record identifier-conflict incident, stop this source and route for disposition; no section requested. |
| S5 | Unmapped; request `S5:data-availability` first. Abstract remains prohibited pending complete cohort resolution. |
| S6 | Includes unresolved, unexposed R-B and nonseparable results; metadata-only, skip abstract. |
| S7 | Unknown cohorts and no isolated sections; skip whole article. |
| S8 | Request `S8:references` for navigation only; skip review body. |
| S9 | Confirmed phenotype-conditioned result was already exposed with unknown cohort mapping. Record incident, stop source and route for disposition; skip abstract. |
| S10 | Reserved, unexposed R-C; skip abstract. |

Requested sections received no responses and remain unread. “Temporal observations” is separately a possible exposure of uncertain meaning, not another confirmed result exposure.

I read only the supplied scenario document, including its inventory, transcriptions, metadata and feasibility information. The transcriptions do not establish kernel validation or current holding. Empty contract dimensions, qualifiers and applicability establish no declared dimension restriction; X1’s calibration restriction, falsification and scale assumption remain distinct authored text. H-missing and H-invalid provide no validated hypothesis; H1’s selection and X1’s targeting provide no additional reliance edges.

Reviewer identity: **codex/gpt-6.1-sol**.

Skipped all offered source sections, external verification and kernel checks. The recommendation remains provisional, with S9’s confirmed exposure incident requiring disposition.


## Full return: guided 1

# Assumption sweep: synthetic inventory — 2026-10-30

Draft compact control; judge: codex/gpt-6.1-sol. Recommend **Q1, Q4 and Q3**, provisionally, with Q2 retained as Q1’s nearest alternative. These choices cover the supplied inventory; they establish neither field-wide priority nor experimental feasibility. The controller owns source replies and S9’s exposure disposition.

## 1. Coverage and actual reads

I read the complete synthetic-v1 scenario and the sweep-assumptions skill/template. I read no offered source sections, papers, patient rows or additional records. The record excerpts are direct, unvalidated transcriptions.

The finite scope was ten supplied bibliographic entries, four questions and an open “other” category. Survey order was S1–S10, then the dependency inventory, then feasibility. Families covered generalization, temporal interpretation, measurement and persistence; broader families, contrasting designs and counterevidence remain unsurveyed. No search queries or network requests were executed. Actuals: 0 searches, 10 bibliographic screens, 0 full-text attempts, 0 completed papers and 0 returned isolated sections.

Policy: results require **every implicated cohort** to be both discovery-assigned and previously exposed. Unknown, reserved and inseparable mixed results remain metadata-only.

| Source | Screen decision and compact-control request | Actual source sections read |
|---|---|---|
| S1 | PMID/DOI map to R-A/ACC-A/group A, discovery and previously exposed. Request `S1:abstract`, limited to the declared cohort. | None |
| S2 | Same study/deposit as S1; retain occurrence, count no independent support. | None |
| S3 | DOI normalizes to S1’s DOI; same permitted study. No redundant abstract request. | None |
| S4 | PMID maps to R-A but DOI maps to unresolved, unexposed R-B. Request separately isolated `S4:data-availability`; results remain blocked. | None |
| S5 | No roster association establishes permission. Request `S5:data-availability`; request isolated design metadata from `S5:methods` only if needed after mapping. No abstract yet. | None |
| S6 | ACC-A plus unresolved, unexposed ACC-B; results inseparable. Keep metadata-only; no abstract request. | None |
| S7 | Unknown cohorts; whole article is the only route. Skip; no whole-body fallback. | None |
| S8 | Review title is navigation only. Request `S8:references` separately; do not read body results. | None |
| S9 | Confirmed incidental result exposure; stop this source and route to controller for program exposure/assignment disposition. No abstract request. | Supplied metadata incident only |
| S10 | DOI maps to reserved, unexposed R-C/ACC-C/group C. No abstract request. | None |

**Confirmed exposure:** I saw S9’s synthetic phenotype-conditioned content, “In the late group, signal doubled.” Reader/date: codex/gpt-6.1-sol, 2026-10-30; cohort mapping unknown. Its result is excluded from ranking and consequence evidence pending disposition. The controller must retain and route the incident; no disposition write occurred here.

**Possible exposure, separately:** the title “Temporal observations” has uncertain meaning. It does not establish confirmed result exposure.

The isolation route has not been exercised here; no live probe occurred. Any later retrieval must establish isolation before display. Access restrictions leave scientific coverage incomplete.

**Phase-A freeze:** the controller confirms complete attachment and verification of sci-b2755f `controls-discovery-v1.md`, SHA-256 `47a11e63b4b26e085dfe296a3f9337636389661b1129a55dc3e158d3bced24b1`. This control uses that supplied freeze before comparison. I made no attachment or independent verification claim.

## 2. Premise inventory

| Premise | Exact text | Provenance and scope |
|---|---|---|
| P1 | “The signal scale is comparable across the included visits.” | Source-stated, X1:r1 assumptions. Included visits; calibrated-sample restriction elsewhere in X1. |
| P2 | “Calibration is stable over the included interval.” | Stated, M1:r1 §2. Interval boundary unspecified. |
| P3 | “The proxy tracks the intended process rather than cell mixture.” | Analyst A inference from C3, proposal:r1. Compared bulk-proxy setting; no independently inspected source endorsement. |
| P4 | “The apparent persistent state cannot be explained by reversible responses.” | Stated, M2:r1 §1. Persistence and timing boundaries unspecified. |

K1 declares `dimensions: {}`; C1 qualifiers and X1 applicability are empty. These maps cannot express visit/calibration distinctions under the inspected contract, while prose records restrictions: early versus late, and “Only samples passing the synthetic calibration check enter the comparison.” Scope is **restricted elsewhere**, partly unspecified and inadequately represented by the maps; it is not explicitly broad or proof of pooling.

C1’s occurrences in S1, S2 and carrier B retain their provenance but count as one claim, with no independent replication. Both carrier transcriptions say r1; current holding and kernel validation remain unknown. Matching empty maps may be called `co_scoped`; this says nothing about adequacy. No cross-proposition commensurability judgment is justified.

## 3. Dependency paths

All links are report-local, bound to the scenario’s stated r1 locators. Stored `targets(X1,C1)` and `selects(H1,C1)` locate records; neither establishes reliance.

- Source-stated links: L1 C1→P1; L3 Q1→C1; L4 Q1→C2; L5 Q2→C2; L6 P1→P2; L7 P2→P1; L9 Q3→C3; L10 C4→P4; L11 Q4→C4.
- Analyst A inferred links: L2 C2→P1, because temporal interpretation requires scale comparability; L8 C3→P3, because interpreting the proxy requires distinguishing process from mixture.
- Adopted links: none.

Totals: 9 stated, 2 inferred, 0 adopted. P1↔P2 is a cycle, not extra support. These paths describe epistemic dependence, not biological causation.

## 4. Reach and sensitivity

“All reachable” includes direct endpoints. Premise nodes, repeated paths and duplicate deposits are excluded.

| Premise | Direct claims | Direct questions | All claims | All questions |
|---|---|---|---|---|
| P1 | {C1,C2}: 2 | {}: 0 | {C1,C2}: 2 | {Q1,Q2}: 2 |
| P2 | {}: 0 | {}: 0 | {C1,C2}: 2 | {Q1,Q2}: 2 |
| P3 | {C3}: 1 | {}: 0 | {C3}: 1 | {Q3}: 1 |
| P4 | {C4}: 1 | {}: 0 | {C4}: 1 | {Q4}: 1 |

P1/P2’s reachable subgraph contains 6 stated and 1 inferred link; P3’s contains 1 stated and 1 inferred; P4’s contains 2 stated. No adopted links contribute.

**Source-stated-only sensitivity for every finalist:**

- **Q1 / P1:** direct and total claims become {C1}: 1; total questions {Q1}: 1; direct questions remain empty. Removing L2 removes C2 and Q2. Q1 survives through L1/L3, but its breadth advantage shrinks.
- **Q4 / P4:** unchanged: direct/total claims {C4}: 1; total questions {Q4}: 1; direct questions empty. Its rationale survives.
- **Q3 / P3:** claim and question reach become empty because L8 is inferred. Q3 remains an explicitly recorded measurement question through Q3→C3, but its status as a downstream beneficiary of P3 depends entirely on analyst inference.

P2 is not independent reach from P1. Reach beyond this inventory is unknown.

## 5. Consequences

These are **analyst A judgments**, not inspected paper conclusions.

| Endpoint | Alternative and consequence |
|---|---|
| C1 | Noncomparable scale could **reinterpret** the contrast; reversal is not established. |
| C2 | Consequence of noncomparable scale is **unevaluated**. |
| Q1, Q2 | Scale failure may **refine** their questions; no automatic cancellation follows. |
| C3 | Mixture explaining the proxy may **narrow** its interpretation. |
| Q3 | Mixture evidence **refines** the measurement question. |
| C4 | Reversible responses sufficing may **reinterpret** the stable-mechanism claim. |
| Q4 | Such evidence **refines** competing alternatives. |

Evaluated endpoints: {C1,Q1,Q2,C3,Q3,C4,Q4}: 7. Unevaluated: {C2}: 1. All seven evaluations are attributed to analyst A; link provenance remains separate. No inspected contrary evidence resolves these alternatives. Missing evidence is neither refutation nor evidence of reversal.

## 6. Tractability

X1:r1, targeting C1, says exactly: **“The target contrast is not positive on repetition.”** This is an authored falsification lead for C1. My judgment: repetition alone does not isolate P1’s comparability assumption or P2’s calibration stability. No relevant falsification was found for P3/P4 in the examined spec; this does not mean they are unfalsifiable.

D1 lists cross-sectional bulk measurements in calibrated samples. Public listing establishes neither possession nor kernel holding.

- Q1 needs additional populations/visits and calibration evidence.
- Q2 needs paired visits and calibration; pairing is unknown.
- Q3 needs composition metadata or an orthogonal assay; neither is established.
- Q4 needs longitudinal perturbation/recovery with appropriate timing; the inspected catalogue has no suitable assay.

Availability and suitability remain separate. Cross-sectional groups cannot establish temporal change or stable dynamics. No evidence of attractors is supplied.

## 7. Three candidates and all-question dispositions

1. **Q1 — “Can this signal interpretation generalize beyond the compared visits?”** N1:r1. Recommend first as a scale-sensitive generalization investigation: P1 potentially reaches two claims and two questions, with C1 reinterpretation and Q1/Q2 refinement judged plausible. Its stated-only support survives with narrower reach. Next investigate calibration comparability and additional visit/population coverage; D1 alone cannot establish generalization. **Q2** is the nearest alternative and shares much of this dependency structure.

2. **Q4 — “What observations distinguish stable states from reversible responses?”** N4:r1. Recommend for its potential to reinterpret C4 and refine mechanisms, with fully stated dependence on P4. The colleague’s preference is not evidence, but the scientific rationale survives sensitivity. Next identify suitable longitudinal perturbation/recovery observations. The unavailable assay limits immediate execution, not scientific importance.

3. **Q3 — “Does cell mixture change the meaning of the bulk proxy?”** N3:r1. Recommend as a distinct measurement investigation: mixture could narrow C3’s interpretation and refine Q3. Explicitly provisional because P3’s downstream reach disappears under stated-only links. Next inspect composition/orthogonal-assay metadata; cross-sectional bulk listing alone is insufficient.

**Q2 — “Does the signal ordering identify temporal change?”** N2:r1 remains a serious alternative, not rejected scientifically. Its consequence for C2 is unevaluated, paired visits are unknown, and its connection to P1 relies on L2. Those uncertainties favor Q1 in this compact shortlist. Q3 versus Q2 remains a judgment call pending metadata and C2 consequence assessment; there is no aggregate score, probability model or utility target establishing a unique ranking.

## 8. Representation gaps and boundaries

- **Scope:** empty K1 dimensions and empty maps fail to carry visit/calibration restrictions already present in prose. Existing prose expresses them; structured adequacy remains unresolved.
- **Relation:** X1 targeting and H1 query membership fail to express reliance. Report-local links demonstrate the missing distinction; proposition-plus-reliance is a candidate representation to evaluate, not an automatic kernel change.
- **Read/state:** carrier copies establish neither validated current records nor holding. H-missing is unavailable; H-invalid’s `not a record` is invalid input, not a hypothesis. Neither supports a kernel capability conclusion.

No writes, attachments, network access or analyses occurred. The report/read ledger is returned as text for controller retention.

Identity command returned **codex/gpt-6.1-sol** successfully.

Skipped: source-section retrieval and kernel validation; every offered section remains unread. Main risk: the shortlist rests on synthetic transcriptions and attributed judgments, with S9 awaiting exposure disposition.


## Full return: guided 2

Assumption sweep — synthetic-v1, 2026-10-30. Recommend **Q1, Q4 and Q3** within this inventory. Q1 offers the broadest shared-premise investigation; Q4 remains scientifically important despite missing suitable data; Q3 offers a distinct measurement question, with an explicitly inferred dependency. These are provisional research recommendations, not established findings or field-wide optimal choices.

### 1. Coverage and read decisions

I read only the supplied scenario and the authored sweep skill/template. All scientific statements below come from the scenario’s transcriptions; no source sections, abstracts, papers, patient rows or kernel records were read or validated.

Phase A uses the controller-confirmed complete attachment sci-b2755f `controls-discovery-v1.md`, SHA-256 `47a11e63b4b26e085dfe296a3f9337636389661b1129a55dc3e158d3bced24b1`. The controller reports attachment-entry and hash verification. I made no attachment.

The finite screen covered all ten source entries in their supplied order, including generalization, temporal interpretation, measurement and persistence; other families and external counterevidence remain unsearched. Budget: ten supplied source screens, no searches or whole-article retrievals, and at most five isolated-section requests. This is a compact control, so requests below remain unanswered and unread.

| Source | Decision and request |
|---|---|
| S1 | PMID and DOI agree with R-A/group A, discovery and previously exposed; one cohort declared. Request `S1:abstract`. No abstract received. |
| S2 | Duplicate S1 deposit; retain its occurrence, add no independent study or support. No request. |
| S3 | Normalize DOI `10.0000/A` to `10.0000/a`; same permitted study as S1. Skip redundant abstract. |
| S4 | PMID maps R-A but DOI maps unresolved, unexposed R-B. Request only `S4:data-availability`; keep unresolved and metadata-only pending reconciliation of every implicated cohort. |
| S5 | No roster association establishes neither permission nor cohort-free methods. Request `S5:data-availability`, then `S5:methods` only as separately isolated design/cohort metadata. No abstract request before resolution. |
| S6 | ACC-A and unresolved, unexposed ACC-B contribute inseparable results. Metadata-only; skip abstract. Additional data-availability reading is unnecessary for the present decision. |
| S7 | Cohorts unknown and only whole article offered. Skip; no whole-body fallback. |
| S8 | Review navigation only. Request `S8:references`; exclude its body and scientific assertions. |
| S9 | Stop this source following confirmed incidental result exposure; no abstract request. |
| S10 | DOI maps reserved, unexposed R-C. Metadata-only; skip abstract. |

The S9 content actually seen was **“In the late group, signal doubled.”** The scenario explicitly identifies this as phenotype-conditioned result content; cohort mapping remains unknown. Reader: this recipient, 2026-10-30. This incident requires retention and routing through the program’s exposure/assignment workflow by the controller; that action is not performed here. Pending disposition, S9 contributes no ranking or consequence evidence. The unrelated title “Temporal observations” is a **possible**, separately recorded exposure concern, not a second confirmed result read. Other sources can continue.

Before executing section reads, the isolation route still needs its synthetic-sentinel check and bounded permitted-source probe. No network or acquisition occurred.

### 2. Premise inventory and scope

| Premise | Exact text and provenance | Scope qualification |
|---|---|---|
| P1 | “The signal scale is comparable across the included visits.” X1:r1 assumptions; source-stated. | Included visits; X1 additionally restricts comparison to calibrated samples and early/late levels. Population and precise timing unspecified. |
| P2 | “Calibration is stable over the included interval.” M1:r1 §2; stated. | Included interval; its exact extent is unspecified. |
| P3 | “The proxy tracks the intended process rather than cell mixture.” Analyst A:r1 proposal, inferred from C3. | Interpretation of the bulk proxy for compared groups; no independent source endorsement or detailed population/timing supplied. |
| P4 | “The apparent persistent state cannot be explained by reversible responses.” M2:r1 §1; stated. | Apparent persistence; observation duration and relevant response times unspecified. |

C1’s `qualifiers: {}` and X1’s `applicability: {}` match as declared maps: `co_scoped` in that limited sense. They do **not** establish broad author pooling or adequate scope. X1’s method and contrast supply restrictions elsewhere; K1’s empty dimensions cannot encode those restrictions in its dimension maps. No explicitly broad scope is established.

Carriers A/B reproduce C1:r1 from S1; S2 also duplicates it. These are retained occurrences of one claim, not independent support. Kernel validation, current holding and contract lineage beyond the supplied K1 declaration are unknown. H-missing is unavailable; H-invalid contains `not a record` and supplies no validated hypothesis. H1’s query selects C1 but stores no reliance predicate. Commensurability is not established merely because different propositions share dependencies.

### 3. Dependency paths

Use the supplied revision-bound, report-local links L1–L11 with **dependent → premise** orientation. L2 and L8 are analyst-inferred; the other nine are source-stated; none is explicitly adopted. Their supplied reasons are proposed epistemic reliance judgments, not causal relationships or new stored graph edges.

`targets(X1,C1)` and `selects(H1,C1)` remain locators. Neither creates reliance. The P1↔P2 cycle contributes no extra endpoints; distinct visited-item sets also prevent Q1’s two paths from counting twice.

### 4. Reach and sensitivity

“Total” includes direct endpoints plus transitively dependent endpoints, excluding premise nodes.

| Premise | Direct claims | Direct questions | Total claims | Total questions | Links in reachable dependency subgraph |
|---|---|---|---|---|---|
| P1 | {C1,C2}, 2 | {}, 0 | {C1,C2}, 2 | {Q1,Q2}, 2 | L1–L7: 6 stated, 1 inferred |
| P2 | {}, 0 | {}, 0 | {C1,C2}, 2 | {Q1,Q2}, 2 | L1–L7: 6 stated, 1 inferred |
| P3 | {C3}, 1 | {}, 0 | {C3}, 1 | {Q3}, 1 | L8–L9: 1 stated, 1 inferred |
| P4 | {C4}, 1 | {}, 0 | {C4}, 1 | {Q4}, 1 | L10–L11: 2 stated |

For the **Q1/P1** recommendation, source-stated links alone leave direct/total claims {C1}, 1 and total questions {Q1}, 1; direct questions remain empty. Removing L2 removes C2 and Q2 from P1’s reach. Q1 survives through L1 and L3, but its broader shared-premise rationale weakens.

For **Q4/P4**, source-stated-only reach is unchanged: direct/total claims {C4}, 1; total questions {Q4}, 1; direct questions empty. Its rationale survives intact.

For **Q3/P3**, removing inferred L8 leaves all claim/question endpoint sets empty. Q3 remains an explicitly recorded measurement question about C3 through L9, but the claim that investigating P3 reaches C3/Q3 depends on analyst inference. Its recommendation survives as a distinct measurement investigation, with weaker premise-reach evidence.

Reach beyond this inventory is unknown.

### 5. Consequences

The worksheet supplies Analyst A’s consequence judgments, separately from link provenance:

| Endpoint | Alternative answer and conditional consequence |
|---|---|
| C1 | Noncomparable scales could **reinterpret** the positive contrast. Reversal is not established. |
| C2 | Consequence **unevaluated**. |
| Q1, Q2 | Noncomparable scales may require question **refinement**. |
| C3 | If mixture explains the proxy, its interpretation may **narrow**. |
| Q3 | That answer **refines** the measurement question. |
| C4 | If reversible responses suffice, the stable-mechanism interpretation may be **reinterpreted**. |
| Q4 | That answer **refines** the alternatives to distinguish. |

Evaluated endpoints: {C1,C3,C4,Q1,Q2,Q3,Q4}, **7**; unevaluated: {C2}, **1**. All seven evaluated judgments are attributed to Analyst A, not papers. No contrary source results were inspected; absence of those results is not refutation. No reversal propagates automatically through the graph.

### 6. Tractability

X1:r1 targets C1 and states exactly: **“The target contrast is not positive on repetition.”** This is an authored falsification lead. My judgment: a failed repetition could challenge C1 without identifying scale noncomparability; a positive repetition would not establish P1. No corresponding specs were found in the examined material for P3 or P4.

D1 lists public cross-sectional bulk measurements in calibrated samples. Public listing establishes neither package possession nor kernel holding. Pairing and mixture annotation remain unknown.

- **Q1:** Needs additional populations/visits and calibration evidence. D1 alone does not demonstrate generalization.
- **Q4:** Needs longitudinal perturbation/recovery observations and relevant timing. The inspected catalogue supplies no suitable assay. Persistent observations alone do not establish stable mechanisms or attractors.
- **Q3:** Needs composition annotations or orthogonal assays to discriminate mixture from intended-process interpretations. Their availability is unknown.
- **Q2:** Needs paired visits and calibration; pairing is unknown. Cross-sectional ordering alone does not identify within-unit temporal change.

### 7. Three recommendations and the alternative

1. **Q1 — “Can this signal interpretation generalize beyond the compared visits?”** N1:r1. First because its scale premise connects the broadest distinct endpoint set, while retaining a stated-only path to C1/Q1. Next investigate calibration comparability and additional populations/visits; distinguish measurement transfer from biological generalization.

2. **Q4 — “What observations distinguish stable states from reversible responses?”** N4:r1. Retain prominently because an answer could reinterpret C4’s mechanism claim, with wholly stated dependency links. Missing suitable data changes the next investigation to design/timing requirements; it does not reduce scientific importance. The colleague’s preference alone does not establish priority.

3. **Q3 — “Does cell mixture change the meaning of the bulk proxy?”** N3:r1. Retain a distinct measurement question whose answer could narrow C3. First inspect permitted composition/orthogonal-assay metadata. Its P3 dependency is analyst-inferred, and current feasibility is unknown.

**Q2 — “Does the signal ordering identify temporal change?”** N2:r1 remains a retained near alternative, not rejected science. It overlaps Q1’s P1 branch, its scale-premise reach disappears without inferred L2, and paired visits are not established. Q4 and Q3 each have one claim and one question endpoint; their ordering is qualitative, with Q4’s stronger link provenance favoring it. There is no probability model, utility target, aggregate score or expected-information-gain calculation.

### 8. Representation limits and status

Empty K1 dimensions and empty declared maps fail to capture restrictions already present in X1’s method/contrast. Stored targeting and query selection fail to express the proposed reliance links. Direct transcriptions cannot establish validated current records, holding or lineage. These are demonstrated limits of the supplied representations and reads, not proof that the kernel needs a new primitive; proposition-plus-reliance sufficiency remains untested.

This compact evaluation is complete; scientific conclusions, requested section reads, incident disposition and subsequent report/read-ledger preservation remain open. No assignments, policies, scientific records or source files changed.

Reviewer identity: **codex/gpt-6.1-sol**, printed by the required fresh identity command.

Skipped: source replies, external searches, kernel validation and live isolation checks. Main risk: the shortlist rests on synthetic transcriptions and conditional analyst judgments, including Q3’s inferred dependency.


## Full return: guided 3

# Assumption sweep — synthetic-v1 — 2026-10-30

Recommend **Q1, Q3 and Q4** for researcher consideration. Q1 has the broadest inspected dependency reach; Q3 tests the bulk proxy’s interpretation; Q4 addresses a consequential temporal ambiguity despite lacking a suitable catalogued assay. This is a compact, provisional recommendation within the supplied inventory. Source replies remain unavailable.

## 1. Coverage and read decisions

I read the complete scenario and authored sweep skill/template. All scientific material is synthetic transcription, not kernel-validated records or inspected primary sections. No network, records, writes or source retrievals occurred.

The controller confirmed the complete phase-A inventory attachment **sci-b2755f controls-discovery-v1.md**, SHA-256 `47a11e63b4b26e085dfe296a3f9337636389661b1129a55dc3e158d3bced24b1`. I rely on that confirmed freeze before comparison; I made no new attachment.

Bounded screen: ten supplied source rows; zero searches, retrieval attempts or completed full texts. Discovery covered generalization, temporal interpretation, measurement and persistence/reversibility. Other families, contrasting designs and counterevidence remain unsearched. No search queries or result positions exist.

| Source | Decision and controller request | Actual evidence read |
|---|---|---|
| S1 | PMID/DOI map to R-A, discovery and previously exposed. Request `S1:abstract` once isolated-route safeguards are demonstrated. | Supplied metadata and C1 transcription only; abstract unread. |
| S2 | Same S1 deposit; retain occurrence, no independent support or additional request. | Supplied metadata only. |
| S3 | DOI normalizes to S1’s DOI. Use S1 as representative; no duplicate abstract request. | Supplied metadata only. |
| S4 | PMID maps R-A but DOI maps unresolved, unexposed R-B. Request `S4:data-availability` for isolated cohort/design metadata; no abstract. | Conflicting metadata only. |
| S5 | No roster association does not establish permission. Request `S5:data-availability`, then `S5:methods` only if necessary to resolve remaining cohort/design metadata. | Supplied metadata only; all offered sections unread. |
| S6 | ACC-A permitted; ACC-B unresolved/unexposed; results inseparable. Keep metadata-only; no result request. | Supplied metadata only. |
| S7 | Unknown cohorts and whole-article-only route. Skip; no whole-body fallback. | Supplied metadata only. |
| S8 | Request separately isolated `S8:references` for navigation; exclude review body/results. | Review title only. |
| S9 | Stop this source; no abstract request. Exposure requires program disposition. | Confirmed result text: “In the late group, signal doubled.” |
| S10 | DOI maps reserved, unexposed R-C. Keep metadata-only; no abstract. | Supplied metadata only. |

Requests above identify the compact control’s next reads; none has a reply or counts as an attempted retrieval. Before displaying requested sections, prove isolation with synthetic sentinels and one bounded permitted-source probe. Unknown or newly implicated cohorts must be resolved before any abstract.

**Confirmed exposure:** this reader saw S9’s quoted phenotype-conditioned result on 2026-10-30; cohort mapping remains unknown. Exclude it from consequence/ranking evidence pending exposure/assignment disposition. The incident is recorded here for controller routing; no external routing or attachment is claimed. **Possible exposure:** the unrelated title “Temporal observations” is separately uncertain, not a second confirmed result read.

Restrictions leave primary corroboration and counterevidence incomplete.

## 2. Premise inventory

| Premise | Exact text and provenance |
|---|---|
| P1 | “The signal scale is comparable across the included visits.” X1:r1 assumptions; source-stated. |
| P2 | “Calibration is stable over the included interval.” M1:r1 §2; source-stated. |
| P3 | “The proxy tracks the intended process rather than cell mixture.” Analyst A proposal:r1; inferred from C3. |
| P4 | “The apparent persistent state cannot be explained by reversible responses.” M2:r1 §1; source-stated. |

K1 declares no dimensions; C1 qualifiers and X1 applicability are empty. Those maps match as declared scope, but do not establish unrestricted applicability or author pooling. Scope is restricted elsewhere by the early/late contrast and X1’s method: “Only samples passing the synthetic calibration check enter the comparison.” Source population, visit details and scope adequacy remain unresolved; K1’s declared dimensions cannot encode those distinctions as dimension keys.

P2–P4 retain their authored wording; additional population/timing scope is unrecorded in the supplied transcriptions. No explicit adoption occurred.

Carrier A/B reproduce C1:r1; S2 and S3 identify the same study. These are retained occurrences, not independent support. Current holding, validation and corpus lineage are unknown. H-missing is unavailable; H-invalid’s `not a record` is not a validated hypothesis.

## 3. Dependency paths

All links below are report-local epistemic reliance proposals bound to the scenario’s r1 locators, not stored graph changes or biological causation:

- L1 C1→P1; L2 C2→P1; L3 Q1→C1; L4 Q1→C2; L5 Q2→C2.
- L6 P1→P2; L7 P2→P1.
- L8 C3→P3; L9 Q3→C3.
- L10 C4→P4; L11 Q4→C4.

L2 and L8 are analyst A inferences; the other nine links are explicitly source-stated. No adopted links exist. The P1/P2 cycle is counted with visited endpoints, never repeated.

Stored `targets(X1,C1)` and `selects(H1,C1)` supply locators, not reliance. H1 stores no reliance predicate.

## 4. Reach and sensitivity

“All” includes direct endpoints. Premise nodes contribute no claim/question endpoints.

| Premise | Direct claims | Direct questions | All claims | All questions | Relevant links: stated/inferred/adopted |
|---|---|---|---|---|---|
| P1 | {C1,C2}: 2 | {}: 0 | {C1,C2}: 2 | {Q1,Q2}: 2 | 6/1/0 |
| P2 | {}: 0 | {}: 0 | {C1,C2}: 2 | {Q1,Q2}: 2 | 6/1/0 |
| P3 | {C3}: 1 | {}: 0 | {C3}: 1 | {Q3}: 1 | 1/1/0 |
| P4 | {C4}: 1 | {}: 0 | {C4}: 1 | {Q4}: 1 | 2/0/0 |

Finalist sensitivity:

- **Q1 through P1:** source-stated-only reach becomes claims {C1}: 1 and questions {Q1}: 1. Removing L2 loses C2 and Q2, although Q1 remains reachable through C1. Recommendation survives with reduced breadth.
- **Q3 through P3:** source-stated-only reach becomes claims {}: 0 and questions {}: 0. L8 supplies the entire premise chain. Q3 remains an explicitly recorded measurement question, but its inferred-premise reach rationale does **not** survive.
- **Q4 through P4:** source-stated-only reach remains claims {C4}: 1 and questions {Q4}: 1. Its rationale survives unchanged.

Reach outside this inventory is unknown; duplicate deposits add no endpoints.

## 5. Consequences

All supplied consequence judgments are analyst A’s, distinct from link provenance.

| Endpoint(s) | Alternative answer and consequence |
|---|---|
| C1 | Noncomparable scale could **reinterpret** the contrast; reversal is not established. |
| C2 | Consequence **unevaluated**. |
| Q1, Q2 | Noncomparable scale may **refine** the questions. |
| C3 | Mixture explaining the proxy may **narrow** its interpretation. |
| Q3 | That answer **refines** its measurement question. |
| C4 | Reversible responses sufficing may **reinterpret** the mechanism claim. |
| Q4 | That answer **refines** its alternatives. |

Evaluated endpoints: {C1,Q1,Q2,C3,Q3,C4,Q4}, **7**; unevaluated: {C2}, **1**. Seven endpoint judgments are analyst-attributed; none is an inspected paper conclusion. No reversal propagates automatically. Contrary evidence and actual premise truth remain unestablished.

## 6. Tractability

X1:r1 targets C1 and states its falsification exactly: **“The target contrast is not positive on repetition.”** This tests the target contrast; it does not by itself isolate P1’s scale comparability. That distinction is this report’s judgment. No premise-specific falsification was found for P3 or P4 in the examined spec material.

D1 lists calibrated, cross-sectional bulk measurements. Public listing establishes neither package possession nor kernel holding.

- **Q1:** needs additional populations/visits and calibration evidence; those inputs are not established.
- **Q2:** needs paired visits and calibration. Pairing is unknown; cross-sectional ordering alone does not identify temporal change.
- **Q3:** needs composition annotations or orthogonal measurements. Their availability and suitability are unknown.
- **Q4:** needs longitudinal perturbation/recovery observations and relevant timing. No suitable assay is catalogued.

These are discriminating-observation proposals, not validated experiments or acquisition permissions. No patient rows were read. Observed persistence supplies no evidence of attractors.

## 7. Three candidates and the alternative

1. **Q1 — “Can this signal interpretation generalize beyond the compared visits?”** N1:r1. First for its broad inspected P1/P2 dependency footprint and retained source-stated route. Prioritize clarifying calibration and population/visit coverage before claiming generalization; additional observations remain necessary.
2. **Q3 — “Does cell mixture change the meaning of the bulk proxy?”** N3:r1. A distinct measurement uncertainty could narrow C3’s interpretation. First inspect annotation/orthogonal-assay metadata. Its premise chain is analyst-inferred and disappears under stated-only sensitivity.
3. **Q4 — “What observations distinguish stable states from reversible responses?”** N4:r1. A source-stated chain supports a potentially consequential reinterpretation of C4. Retain its scientific importance while documenting the missing longitudinal perturbation/recovery capability. A colleague’s preference supplies no additional evidence.

**Q2 — “Does the signal ordering identify temporal change?”** N2:r1 remains a close alternative to Q1. I select Q1 because it retains a source-stated path when L2 is removed; Q2’s P1 connection depends on that inferred link. This does not establish that Q2 is scientifically less important. Unknown pairing and C2’s unevaluated consequence make their comparison provisional.

No aggregate score, probability model, utility target or expected-information-gain claim is warranted.

## 8. Representation gaps and boundaries

- Empty scope maps fail to express the inspected calibration/visit restrictions; method text preserves restrictions that those maps omit.
- Existing `targets` and query membership do not encode the proposed reliance judgments. Proposition-plus-reliance may suffice, but no kernel extension has been demonstrated necessary.
- Duplicate carriers preserve text without establishing validation, current holding or independent evidence.
- Section isolation and complete cohort mapping remain prerequisites for offered source reads.

Reviewer identity: **codex/gpt-6.1-sol**, freshly reported by `relay model`.

Skipped source retrievals, validation and new attachments as required by this compact control. Recommendations remain provisional; S9’s confirmed exposure still requires controller disposition.


## Full return: guided 4

# Assumption sweep — synthetic-v1 — 2026-10-30

I recommend **Q1, Q4 and Q3**, in that provisional order, within this inventory. Q1 examines the broadest connected interpretation; Q4 retains scientific importance despite missing suitable data; Q3 tests a distinct measurement ambiguity. Q2 remains a close alternative to Q1. This is a compact evaluation, with all offered source sections still unread.

## 1. Coverage and read decisions

I applied the supplied sweep-assumptions skill and template to scenario-draft.md, synthetic-v1. I read their full supplied text, including the record transcriptions and metadata screen. These are synthetic, unvalidated transcriptions, not kernel-validated records or inspected papers.

For phase A I use the controller’s confirmed, complete attachment **sci-b2755f controls-discovery-v1.md**, SHA-256 `47a11e63b4b26e085dfe296a3f9337636389661b1129a55dc3e158d3bced24b1`. I made no new attachment or independent verification claim.

The bounded source set contains ten bibliographic screens, four question families—generalization, temporal interpretation, measurement, persistence—and an open “other” category with no additional supplied items. Network searches, full-text attempts and completed article reads: **0**. Source order was the supplied S1–S10 order, not a search ranking. No patient rows were read.

Only results whose **every cohort is discovery-assigned and previously exposed** are eligible.

| Source | Metadata decision and request |
|---|---|
| S1 | PMID and DOI resolve to R-A/ACC-A/group A, discovery and exposed. Request **S1:abstract**; unread pending response. |
| S2 | Duplicate deposit of S1; no independent study or support. No request. |
| S3 | DOI normalization maps `10.0000/A` to S1/R-A. Eligible, but skip its abstract as duplicate. |
| S4 | PMID maps to R-A while DOI maps to unresolved, unexposed R-B. Request isolated **S4:data-availability** to resolve the conflict; no abstract/results. |
| S5 | Unmapped. Request isolated **S5:data-availability** first. Request methods metadata only afterward if necessary and separately isolatable; no abstract before complete resolution. |
| S6 | ACC-A plus unresolved, unexposed ACC-B; results explicitly inseparable. Metadata-only; skip abstract. |
| S7 | Cohorts unknown and only whole article offered. Skip: no isolated metadata route, no whole-body fallback. |
| S8 | Review title is navigation only. Request **S8:references**, isolated from body; unread. No scientific support drawn from the review. |
| S9 | Confirmed incidental result exposure; stop this source. No abstract request. |
| S10 | DOI maps to R-C/ACC-C/group C, reserved and unexposed. Metadata-only; skip abstract. |

Requests above are identified for the controller; none has returned.

**Confirmed incident:** S9 metadata contained “In the late group, signal doubled.” This recipient saw it on 2026-10-30; cohort mapping is unknown. Exclude it from ranking and consequences pending disposition. The controller must retain the incident and route it through the program’s exposure/assignment workflow; this read-only sample does not claim that routing occurred.

**Possible exposure, separately:** the title “Temporal observations” has uncertain meaning. It does not establish a confirmed result read or cohort mapping.

Access restrictions and absent source replies limit coverage; no field-wide completeness is claimed.

## 2. Premises and scope

| ID | Exact text and provenance |
|---|---|
| P1 | “The signal scale is comparable across the included visits.” X1:r1 assumptions; source-stated. |
| P2 | “Calibration is stable over the included interval.” M1:r1 §2; stated. |
| P3 | “The proxy tracks the intended process rather than cell mixture.” Analyst A proposal:r1, inferred from C3; not a paper-stated premise. |
| P4 | “The apparent persistent state cannot be explained by reversible responses.” M2:r1 §1; stated. |

P1 concerns included visits; P2 the included interval; P3 the compared bulk-proxy groups; P4 the observed persistent phenotype. Their exact populations and timing are incompletely recorded.

K1 declares `dimensions: {}`; C1 qualifiers and X1 applicability are empty. Those maps match, but their adequacy is unestablished: they do **not** prove broad scope or author pooling. C1/X1 are restricted elsewhere by early-versus-late contrast and “Only samples passing the synthetic calibration check enter the comparison.” K1 supplies no declared dimensions for expressing those distinctions in its scope maps; other representation capabilities are untested.

Carrier A and B reproduce the same C1:r1; count one claim, preserving both occurrences. S2 is a duplicate deposit and S3 the same study. None supplies independent replication. Carrier/corpus lineage, validation and current holding remain unknown.

## 3. Dependency paths

I use the supplied **report-local dependent → premise** links, bound to their synthetic-v1 locators. Nine are stated; **L2 C2 → P1** and **L8 C3 → P3** are analyst-inferred. None is explicitly adopted.

Stored `targets(X1,C1)` and `selects(H1,C1)` remain locators. They establish no reliance. H1 stores no reliance predicate.

P1 ↔ P2 forms a cycle. Traversal counts each downstream claim/question once; premise nodes add no endpoints. These paths describe epistemic dependence, not biological causation.

## 4. Reach and sensitivity

“Direct” means an incoming dependent link; “all” includes transitive dependents.

| Premise | Direct claims | Direct questions | All distinct claims | All distinct questions |
|---|---|---|---|---|
| P1 | {C1, C2}: 2 | {}: 0 | {C1, C2}: 2 | {Q1, Q2}: 2 |
| P2 | {}: 0 | {}: 0 | {C1, C2}: 2 | {Q1, Q2}: 2 |
| P3 | {C3}: 1 | {}: 0 | {C3}: 1 | {Q3}: 1 |
| P4 | {C4}: 1 | {}: 0 | {C4}: 1 | {Q4}: 1 |

The P1/P2 subgraph contains six stated links and inferred L2; P3’s contains stated L9 and inferred L8; P4’s contains two stated links. Duplicate deposits and repeated paths add nothing. Reach beyond this inventory is unknown.

For each finalist, retaining **only stated links** gives:

- **Q1/P1–P2:** claims {C1}: 1; questions {Q1}: 1. Removing L2 disconnects C2 and Q2 from these premises. Q1 survives through stated C1 → P1 and Q1 → C1, but its broader shared-reach advantage weakens.
- **Q4/P4:** claims {C4}: 1; questions {Q4}: 1, unchanged. Its rationale survives without inferred links.
- **Q3/P3:** claims {}: 0; questions {}: 0 from P3. Removing L8 eliminates the premise-reach argument. Q3 remains an explicitly recorded measurement question about C3 through L9, but its interpretation as testing P3 is analyst-inferred and needs validation.

## 5. Consequences and uncertainty

These are supplied analyst A judgments, separate from link authorship:

| Endpoint | Alternative and consequence |
|---|---|
| C1 | Noncomparable scale could **reinterpret** the contrast; reversal is not established. |
| C2 | Consequence **unevaluated**. |
| Q1, Q2 | Scale uncertainty may **refine** their framing. |
| C3 | Mixture explaining the proxy may **narrow** its interpretation. |
| Q3 | That alternative **refines** the measurement question. |
| C4 | Reversible responses sufficing may **reinterpret** the stable-mechanism inference. |
| Q4 | That alternative **refines** the competing explanations. |

Evaluated endpoints: **{C1, C3, C4, Q1, Q2, Q3, Q4}: 7**, all analyst judgments. Unevaluated: **{C2}: 1**. No reversal propagates automatically. No inspected primary evidence resolves these alternatives; missing evidence is not refutation, and observed persistence does not establish attractors.

## 6. Tractability

D1 lists cross-sectional bulk measurements in calibrated samples. Public listing establishes neither package possession nor kernel holding. Pairing and mixture annotation are unknown.

- **Q1:** needs additional populations/visits and calibration evidence. D1 alone does not demonstrate generalization.
- **Q2:** needs paired visits and calibration. Cross-sectional ordering alone does not identify within-subject temporal change.
- **Q3:** needs cell-composition or orthogonal assay metadata. Bulk availability alone does not establish discrimination between mechanisms.
- **Q4:** needs longitudinal perturbation/recovery observations and relevant timing. No suitable assay is catalogued; that limits the next investigation, not its importance.

X1:r1, targeting C1, states exactly: **“The target contrast is not positive on repetition.”** This is an authored falsification lead for C1, not a demonstrated test of P1 or P2: repetition could preserve the contrast despite scale problems. No relevant falsification was found for P3/P4 in the examined spec transcription; that does not mean they are unfalsifiable.

## 7. Three recommendations and the alternative

1. **Q1 — “Can this signal interpretation generalize beyond the compared visits?”** N1:r1. It connects to C1 and C2 through stated question links and exposes shared scale assumptions. Its advantage is conditional on inferred L2 and incomplete consequence evaluation for C2. Next inspect permitted S1 material, then establish population/visit coverage and calibration requirements. Q2 is close; Q1 receives the provisional lead because it preserves both recorded supporting claims and broader scope questions.

2. **Q4 — “What observations distinguish stable states from reversible responses?”** N4:r1. It directly challenges C4’s stable-mechanism interpretation through a wholly stated chain. Its scientific case survives sensitivity analysis. The colleague’s preference is not evidence; the absence of longitudinal capability is also not a reason to erase it. Next define the discriminating timing and recovery observations and identify whether suitable permitted material exists.

3. **Q3 — “Does cell mixture change the meaning of the bulk proxy?”** N3:r1. It addresses an independent measurement ambiguity that could narrow C3. Its premise-dependency rationale relies entirely on inferred L8. Next seek composition or orthogonal-assay metadata and validate that proposed reliance before claiming impact.

**Q2 — “Does the signal ordering identify temporal change?”** N2:r1 is retained as the nearest alternative, not rejected scientifically. Its dependence on P1 is inferred and C2’s consequence is unevaluated. Paired-visit evidence could move it into the shortlist. No probability model or utility target supports an aggregate score or expected-information-gain claim.

## 8. Representation limits and status

H-missing is unavailable; H-invalid contains `not a record`. Neither is a validated hypothesis. Query selection cannot substitute for reliance, and matching empty scope maps cannot establish adequate scope. A scoped proposition plus an explicit reliance relation may represent the proposed dependencies, but that is an evaluation hypothesis—not a demonstrated need for kernel changes.

This compact answer uses the controller-confirmed freeze. No writes, acquisition, policy changes or new attachments occurred.

Reviewer identity: **codex/gpt-6.1-sol**, printed by the requested fresh identity command.

Skipped: offered source sections, network and kernel validation. Risk: recommendations remain inventory-bounded and may change after permitted source reads.


## Full return: guided 5

Assumption sweep — synthetic-v1, 2026-10-30. Compact, provisional evaluation by codex/gpt-6.1-sol. My three recommendations are Q2, Q4 and Q3, with Q1 retained as the nearest alternative. This is a judgment within the supplied inventory, not a field-wide ranking. Source requests below remain unanswered; the controller owns their disposition.

1. Coverage and preservation

I read scenario-draft.md and the authored sweep-assumptions skill and template only. The scenario supplies the record transcriptions, source metadata, proposed links, consequence worksheet and D1 catalogue description; I read no underlying records, abstracts, papers or datasets.

For this compact control, phase A uses the controller-confirmed complete attachment sci-b2755f controls-discovery-v1.md, SHA-256 `47a11e63b4b26e085dfe296a3f9337636389661b1129a55dc3e158d3bced24b1`. I made no attachment or independent attachment verification.

The finite screen covers the ten supplied source entries, collapsing S1/S2/S3 to one study identity. Search and full-text budgets are zero; actual searches, retrievals and additional-section reads are zero. The supplied inventory covers generalization, temporal interpretation, measurement and persistence; other families and outside reach remain unknown. No external query sequence or search completeness is claimed.

The policy permits phenotype-conditioned results only when every implicated cohort is both discovery-assigned and previously exposed. No section-isolation route was tested, so the following are requests or permission decisions, not completed reads:

| Source | Decision and controller request |
|---|---|
| S1 | PMID/DOI agree on R-A/group A, discovery and exposed; declared single cohort. Abstract eligible under supplied metadata: request `S1:abstract` through an isolated route. |
| S2 | Same S1 deposit; retain occurrence, count no independent support or additional read. |
| S3 | Case-normalized DOI matches S1/R-A. Abstract eligible but skip duplicate retrieval. |
| S4 | PMID maps R-A, DOI maps unresolved/unexposed R-B. Keep unresolved; request isolated `S4:data-availability` to reconcile identifiers/cohorts. No abstract. |
| S5 | No roster association establishes permission. Request isolated `S5:data-availability`, then only necessary design metadata from `S5:methods` if isolation is demonstrated. No abstract before complete mapping. |
| S6 | ACC-A plus unresolved/unexposed ACC-B; inseparable results remain metadata-only. No abstract request; declared mapping already establishes the restriction. |
| S7 | Cohorts unknown; only whole article available. Skip; no whole-body fallback. |
| S8 | Review navigation only. Request isolated `S8:references`; skip body. |
| S9 | Confirmed incidental result exposure; stop source and route incident for exposure/assignment disposition. No abstract request or scientific use pending disposition. |
| S10 | DOI maps R-C, reserved and unexposed. Metadata-only; no abstract. |

Confirmed incident: this reader saw S9’s synthetic phenotype-conditioned text, “In the late group, signal doubled.” on 2026-10-30; cohort mapping is unknown. This report records it and requests controller routing; routing is not claimed complete. Separately, “Temporal observations” is possible exposure only: its meaning is uncertain. S9 is excluded from consequence and ranking evidence.

Restrictions leave unresolved and reserved cohorts scientifically unexamined and may bias coverage.

2. Premises and scope

| ID | Exact text and provenance |
|---|---|
| P1 | “The signal scale is comparable across the included visits.” — source-stated, X1:r1 assumptions. |
| P2 | “Calibration is stable over the included interval.” — stated, M1:r1 §2. |
| P3 | “The proxy tracks the intended process rather than cell mixture.” — analyst A’s inferred proposal:r1, from C3; not a paper assertion. |
| P4 | “The apparent persistent state cannot be explained by reversible responses.” — stated, M2:r1 §1. |

K1 declares no dimensions; C1 qualifiers and X1 applicability are empty. Those maps match syntactically, but do not establish unrestricted applicability or pooling. X1 restricts the comparison to early/late levels and says, “Only samples passing the synthetic calibration check enter the comparison.” Scope is therefore restricted elsewhere and inadequately represented in the empty maps. P1/P2 cover included visits/interval; their exact population and timing remain unspecified. P3/P4 have no further population or timing scope supplied.

Carrier A/B transcribe the same C1 revision r1; S2/S3 also represent the S1 study. Repeated deposits provide no independent support. Kernel validation, current holding and corpus lineage are unknown. H-missing is unavailable; H-invalid contains `not a record` and supplies no validated record.

3. Dependency interpretation

All eleven supplied links are report-local dependent → premise judgments bound to the supplied r1 locators. Nine are source-stated; L2, C2 → P1, and L8, C3 → P3, are analyst-inferred; none is explicitly adopted. The P1 ↔ P2 cycle supplies no independent corroboration.

Stored `targets(X1,C1)` and `selects(H1,C1)` locate records only. H1 stores no reliance predicate. These are epistemic paths, not biological causal paths.

4. Reach and sensitivity

“Reachable” includes direct and longer paths, deduplicated by endpoint; premise nodes never count as claims or questions.

| Premise | Direct claims | Direct questions | All reachable claims | All reachable questions |
|---|---|---|---|---|
| P1 | {C1,C2}: 2 | {}: 0 | {C1,C2}: 2 | {Q1,Q2}: 2 |
| P2 | {}: 0 | {}: 0 | {C1,C2}: 2 | {Q1,Q2}: 2 |
| P3 | {C3}: 1 | {}: 0 | {C3}: 1 | {Q3}: 1 |
| P4 | {C4}: 1 | {}: 0 | {C4}: 1 | {Q4}: 1 |

P1/P2’s connected subgraph contains six stated and one inferred link; P3’s contains one stated and one inferred link; P4’s contains two stated links.

For each finalist:

- Q2, considered through P1/P2: stated-only reach falls to claims {C1}: 1 and questions {Q1}: 1. Removing inferred L2 disconnects C2/Q2 from the scale premise. Q2 remains defensible through stated Q2 → C2 and its unresolved temporal interpretation, but its broad scale-leverage rationale does **not** survive. Its first-place position is provisional.
- Q4 through P4: stated-only sets remain claims {C4}: 1 and questions {Q4}: 1. Its rationale survives.
- Q3 through P3: stated-only sets become empty because L8 is inferred. The stated Q3 → C3 question remains, but identifying P3 as its required premise depends on analyst interpretation. Retain Q3 as a measurement question, not an established paper dependency.

5. Consequences

The worksheet supplies analyst A’s judgments, not paper conclusions:

| Endpoint | Alternative answer and consequence |
|---|---|
| C1 | Noncomparable scale could reinterpret the contrast; reversal is unestablished. |
| C2 | Consequence of noncomparable scale is unevaluated. |
| Q1,Q2 | May require refinement; this is a tentative judgment. |
| C3 | Mixture explanation may narrow the proxy’s interpretation. |
| Q3 | Refines its measurement question. |
| C4 | Sufficient reversible-response explanation may reinterpret the stable-mechanism claim. |
| Q4 | Refines the competing alternatives. |

Evaluated endpoints: {C1,C3,C4,Q1,Q2,Q3,Q4}: 7. Unevaluated: {C2}: 1. All seven evaluated judgments originate with analyst A; this provenance is separate from link provenance. No reversal propagates automatically. No inspected contrary evidence resolves these alternatives; missing evidence does not refute them.

6. Tractability

X1:r1, targeting C1, states exactly: “The target contrast is not positive on repetition.” This tests the target contrast, not specifically P1’s scale comparability; that connection requires independent measurement reasoning. No relevant falsification was found for P3/P4 in the examined supplied spec transcription.

D1 lists calibrated cross-sectional bulk measurements. Public listing establishes neither package possession nor kernel holding; no patient rows were read.

- Q2 needs paired visits, calibration and comparable timing. Pairing is unknown; a cross-sectional package alone cannot identify within-unit temporal change.
- Q4 needs longitudinal perturbation/recovery observations and relevant timing. No suitable assay is catalogued. Persistence alone establishes neither a stable mechanism nor attractors.
- Q3 needs composition annotations or an orthogonal assay. Both are unknown. Cross-sectional bulk data may support investigation only after those capabilities and access are established.
- Q1 needs additional populations/visits plus calibration; those capabilities are unestablished.

7. Three questions and all dispositions

1. **Q2: “Does the signal ordering identify temporal change?”** — N2:r1. Prioritize clarifying temporal interpretation because it affects what C2 means and potentially connects to the broader scale/calibration cluster. Consequence for C2 is still unevaluated, and the cluster connection relies on L2. Next investigate pairing and measurement comparability through permitted metadata; do not treat ordering as demonstrated temporal change.
2. **Q4: “What observations distinguish stable states from reversible responses?”** — N4:r1. Retain for its potential to reinterpret C4 and its fully source-stated dependency path. The colleague’s preference is not evidence. Its scientific importance survives the absence of a suitable current package; next identify the required temporal discrimination and missing assay capability.
3. **Q3: “Does cell mixture change the meaning of the bulk proxy?”** — N3:r1. A defensible measurement question with possible narrowing of C3. Its premise attribution is inferred, and current tractability depends on unknown annotations or orthogonal measurements. Next inspect those metadata, without assuming availability.

**Q1: “Can this signal interpretation generalize beyond the compared visits?”** — N1:r1, retained nearest alternative. It has stated links to C1/C2 and remains important. I favor Q2’s narrower identification question first; Q1 needs additional populations/visits and calibration, none established here. Q1 could replace Q2 if direct source support for the premise-centered rationale receives greater weight.

No probability model or utility target supports an aggregate score or expected-information-gain claim.

8. Representation limits and handoff

Empty scope maps fail to carry the supplied contrast, calibration restriction and visit scope; `co_scoped` alone would miss that distinction. Same-claim duplicate C1 transcriptions can be compared without treating unrelated C1/C2 as commensurable estimands. Existing target/query predicates do not encode reliance, and supplied files do not establish validated current records. Report-local propositions and explicit reliance links suffice for this exercise; no kernel change is established as necessary.

The controller can resolve the incident and isolated-section requests, then revise the comparison against a new preserved inventory if discoveries change it. No records, policies, assignments or files were changed.

Skipped: network, underlying source reads, biological analysis and new attachments. Risk: the shortlist remains inventory-bounded, and Q2/Q3’s premise leverage depends on inferred links.

Reviewer identity: codex/gpt-6.1-sol.

