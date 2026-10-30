# Assumption-sweep discovery inventory v1 — mm — 2026-10-30

Status: frozen phase A, before comparative impact/available-data assessment.
Task sci-b2755f; step sci-d3044e. Author: controller (Codex). This is a dated
research evaluation artifact, not a beliefs corpus, minted graph or scientific store.
No shortlist or feasibility ranking has been selected. Missing primary reads are
preserved rather than filled from model memory.

## Coverage and read status

Setup: pilot-setup-v1.md, SHA-256
9801114ed3a1919a3cd046074c68a70e23d5a192ae4e8a91eb0695561c68ae56.
Science source skill 461f4072b27825635887906892930da6ba7c0388;
beliefs cd4fe60adb35b301619d5a838ab835a4aeaa2a3d;
mm a7250080ffa99369884eec670c42a21380482b6f;
quarry 7008433c8d3007b38a8fb08598e7e3ed49e965eb.

Supported `uv run science status --config "$SCIENCE_CONFIG"` ran from this
worktree's python directory and succeeded. It reported known/live/present corpora
and counts, not scientific verdicts, a field export or actual holdings.

All scientific field values below were read directly from explicitly configured
record files. They remain **unvalidated file inspections**: the successful status
read does not independently validate every quoted field/revision. The configured
world is aec951bc6becacced13df8f7ae6f8abf. Carriers:

- mm30, corpus 8b5d0c802677ee445e2b9d91ebf5d6a7: two propositions, one spec,
  one composite; status also counts five datasets, five holdings-observations,
  two runs, one assessment and one verification. Those result/holding contents
  were not inspected and are not evidence for a present belief/holding claim.
- working, corpus 4b1c238d06cf7fa18def5ea2554d4f16: one proposition, one spec,
  three question files and four projects; status also counts two datasets.
  The scientific/question fields were inspected; project records and dataset
  bytes were not read. The two identically worded clinical questions explicitly
  identify the same query; preserve both project contexts as alias occurrences.
- No hypothesis, source or source-assertion files were found in their kind
  directories in either carrier. This is examined coverage, not a global absence
  claim or permission for a new store.

Both manifests declare biology:24bcec4370cfcff3077414798c02525814d4aeaaf84430ab378838df7345d53b,
mm30:4af7c4212d482ae60f429526ff5a8a6d4c335f70351a2687cd2062ffdedf437c,
and science:52a4399342235225fbf23526050cf64ff0436d9b72bc54e30fc0c2cb7193b220.
Working additionally declares coordination:b23866284ae160f7e7322cbb3c63adcbc84f5f894e6f30f5468c76dc8434993d.
Manifest file hashes: mm30 8e8d45ed082c42b3f812e04afeb71a01f998a3bfda6c60cbbecbc2d8f16cac55;
working 33209bebd569d1f612c691f945b4fbbb2508748ca2a80a16736a23cb6245803b.
Corpus state identities are not exported by the status report and were not
independently reconstructed; inspected file hashes below are the revision binds.

The old reproduction root declared by beliefs' reproduction/paths.py exists
separately. Its X1 spec file is byte-identical to configured mm30 X1; it contributes
no independent spec/claim. Other old record bodies and old/current holding state
were not revalidated. Reproduction spec.py is code evidence, not an inspected run.
The active successor contract, mm30 cut-31 template and biology domain declare
empty dimensions. Stage contrast and method restrictions still exist elsewhere.

## Exact local item and revision index

| ID | Carrier/local record locator | Exact statement or relevant content | File SHA-256 |
|---|---|---|---|
| C1 | mm30/proposition/concept-disease-stage-affects-protein-phf19.md | `concept:disease-stage affects protein:PHF19`; typed positive, causal, qualifiers empty | 454301b06d310fbf8e9d8585ffdc17f6d4f3f0fd426c6eb4be56f786de306817 |
| C2 | mm30/proposition/protein-phf19-affects-concept-overall-survival.md | Title: `PHF19 expression affects overall survival (negatively)`; display says `Higher PHF19 expression predicts shorter overall survival` and identifies it as a spine minted with no evidence | 58f521b29fb504fc0df5dd74d0eb3437d88cfeb570c27b31f4ed84fb2cd193f7 |
| C3 | working/proposition/concept-disease-stage-affects-protein-ezh2.md | `concept:disease-stage affects protein:EZH2`; typed positive, causal, qualifiers empty | 0393da753dbaefaf7f86acf150d00be8c5ee1f91cba40a4205cc8cc22d4a0f39 |
| X1 | mm30/analysis-spec/10e8bfce1aaad8a937a79bfba7cf523ac42b4240ec8b15e20e5b5f450d234714.md | Frozen projection targets C1; observational, unconditioned NDMM→PD levels contrast; additive RNA-seq TPM, two-group rank comparison; non-finite values cause refusal | dfe98346b77a472a14353bb20c8fa82a929c6ac71620f2e8c5137d5c36d7ee4e |
| X2 | working/analysis-spec/5132014c5feecd52d09c801c220074bae2fd7677ec009b1a0228186602763036.md | Targets C3; same stage levels, RNA-seq TPM and observational identification; method defines GENCODE36 gene lengths, unstranded counts, one sample/patient, diagnostico→NDMM and recidiva→PD | 1ee118cd1787b05b850f934f34bcbeb254448197e62df3d08b42e4b23276f64b |
| M1 | mm30/composite/h1-prognosis-fragment.md | `h1-prognosis fragment: disease stage → PHF19 ⊣ overall survival`; causal DAG with C1/C2 members | 30a4626952101dada39b53aa17ab44e378c22144b0fa26db34319b881df89c94 |
| Q09a | working/question/4dbcb70467a87cd727cc6303cbd697a2.3cffd9be7ceb0e8655d8ef19fb4590a6.f9f210e5a663cec01218c4eca87c5295.md | `Does disease stage drive the PRC2 catalytic core (EZH2) where it drives PHF19?` | e8314172205b7dfcc8becff200bc4014039055cc2d6667c013795cb24ef6a18f |
| Q09b | working/question/ef2b7fe9b5a8b6b35c8657b645ed0db2.f1cc8f85f03d6e7caf9ae55e1e772292.7845f9d0cd4974a66a21c1424b7e81d4.md | Same exact question/query; body explicitly names Q09a as same query | 4687df61246b15a49795288fa3a9a09d63e31077e9d81bbb7e0681f988662f9e |
| Q10 | working/question/66ab99117a2bd1b491175d0d2c612ac2.83ba85bda606da218a27f8d98ac62d1b.6f0c4c3dc79230995de33570306684cc.md | `evidence-bound terms`; body: `Measurement only ... the term clauses its own evidence binds.` | 00397fbdec4cd450978bbd15cac28fae1dfab539e911a79e51e12d8af3cfe4ae |

C2's display describes its minting context, not a freshly evaluated current belief.
No assessment/verdict was read here. Q09's body calls itself a narrower sub-claim
of the health program's PRC2 line and says the cross-disease half is not representable
yet under these myeloma stage levels. That recorded broader intent is preserved;
this pilot neither narrows the health goal nor claims the current contract meets it.

## Premise inventory — exact text apart from analyst proposals

| P ID | Exact source text or explicitly labelled analyst proposal | Scope and provenance; existing correspondence |
|---|---|---|
| P1 | `independent samples` | Source-stated clause, X1 projection assumptions; scoped to X1's input/contrast, not all mm cohorts |
| P2 | `the stage is a two-level factor carried by each sample id` | Source-stated clause, X1 assumptions; stage encoded in IDs; actual sample labels not opened |
| P3 | `independent samples, one per patient` | Source-stated clause, X2 assumptions; related to P1 but retains its additional patient-unit restriction; not merged into one globally scoped premise |
| P4 | `the stage is the two-level factor the metadata's `condition` column carries` | Source-stated clause, X2 assumptions; method explicitly maps diagnostico/recidiva, not inferred to be different diseases |
| P5 | `the counts were produced against GENCODE release 36` | Source-stated clause, X2 assumptions; one annotation/input restriction; raw counts not checked |
| P6 | Analyst proposal: an observational, unconditioned stage rank contrast is adequate evidence for the causal proposition being considered | Inferred from C1/C3 causal typing versus X1/X2 observational estimands/methods; not an assumption attributed to the authors, and not asserted true |
| P7 | Analyst proposal: within X1, the gene's TPM contrast compares the relevant biological/sample units adequately | Inferred measurement/composition requirement; X1-specific scope, not protein-abundance equivalence or a claim that composition confounding occurred |
| P8 | Analyst proposal: within X2, the TPM/annotation/sample-unit choices adequately measure the target comparison | Inferred from X2 method; kept separate from P7 because input/population/method restrictions differ |
| P9 | Reuse existing C1 as a possible presupposition of Q09's `where it drives PHF19` wording | Existing causal proposition, not a newly stored premise. Its role as reliance is agent-inferred/ambiguous; no adopted confidence or scope fit is established |

Five source-stated assumption clauses, three analyst-proposed adequacy statements,
and one reused source claim with an inferred premise role. No explicit adoption.
No inspected source asserts that mm is one disease, that discrete disease-system
states exist, or that clusters establish attractor dynamics. Missing dimensions
are not evidence for those propositions. All qualifiers/applicability maps are
empty; X1/X2 contrasts and X2 method provide restrictions elsewhere. Scope can be
both restricted elsewhere and not expressible in the active dimension vocabulary.
P6–P8 adequacy/scope remain unassessed, not known failures.

## Stored locators and proposed dependency links

Stored locators: M1 `composes` C1/C2; X1/X2 projection `target` C1/C3;
Q09 query addresses select X2/C3/datasets and a closure around X1's input;
Q10 queries X1/input and a references-term clause. Original predicates/query
membership remain locators only. A causal DAG is not an epistemic reliance graph.

Each of the following is a **proposed**, revision-bound reliance judgment by the
controller, not a stored relationship or causal edge. All endpoint IDs bind to
the exact file hashes above and to scoped premise clauses in those files.

| Link | Dependent → premise | Reason and link provenance |
|---|---|---|
| L1 | C1 → P1 | Inferred: interpreting X1's comparison requires its stated independence clause |
| L2 | C1 → P2 | Inferred: interpreting its stage contrast requires the stated ID-label semantics |
| L3 | C3 → P3 | Inferred: interpreting X2's comparison requires its patient-unit assumption |
| L4 | C3 → P4 | Inferred: interpreting its stage contrast requires the recorded condition mapping |
| L5 | C3 → P5 | Inferred: interpreting the method requires compatible counts/annotation semantics |
| L6 | C1 → P6 | Inferred: causal interpretation requires examining identification adequacy |
| L7 | C3 → P6 | Inferred: same identification question; does not assert confounding occurred |
| L8 | C1 → P7 | Inferred: relevant measurement comparison depends on X1-specific adequacy |
| L9 | C3 → P8 | Inferred: X2-specific adequacy, not a claim of cross-cohort equivalence |
| L10 | Q09 → C1 (P9 correspondence) | Inferred/ambiguous presupposition in wording; may instead be a tentative comparator; no premise endorsement inferred from query membership |

Link provenance: ten inferred; zero explicitly source-stated reliance statements;
zero adopted. Premise-statement provenance is different. No C2 reliance is inferred
from M1's DAG, and no Q09→C3 reliance is minted merely because C3 is the question's
target. New question leads below have no judged reliance links yet; their reach is
unassessed, not evidence of zero importance. No reach/impact calculations are made
in this discovery freeze.

## Complete discovered question/lead inventory, before feasibility comparison

| Q ID/family | Exact recorded question or analyst-proposed lead | Origin, inspected basis and discovery status |
|---|---|---|
| Q01 / identification | Which recorded stage comparisons support a causal interpretation, and what additional identification would be needed? | Analyst proposal from C1/C3 causal typing and X1/X2 observational, unconditioned rank comparisons; no claim that effects are absent |
| Q02 / heterogeneity and generalization | Which distinctions within mm change what conclusions can be shared across patients, and which conclusions remain common? | User's candidate family plus analyst framing, not selected as the field's best question; latent disease-system states are a hypothesis, not stage relabelling |
| Q03 / initiation and progression | Which observations distinguish processes of initiation and progression from differences among sampled patient groups? | Analyst search-family prompt; no inspected primary assertion establishes a field-wide gap |
| Q04 / measurement | Under what sample, composition and annotation conditions do these RNA-seq TPM comparisons measure the intended biological contrast? | Analyst proposal grounded in X1/X2 methods and scoped P1–P5/P7–P8; actual metadata/data validity not evaluated |
| Q05 / microenvironment and immunity | Which tumor–host or immune distinctions must be observed to discriminate competing explanations of progression or response? | Analyst family prompt retained; no claims extracted from unread sources or result-title incidents |
| Q06 / response and resistance | What observations distinguish pre-existing resistant states, treatment adaptation and differences in exposure or sampling? | Analyst family prompt; not attributed to the withheld result-title papers |
| Q07 / persistence and time | What longitudinal or perturbational observations distinguish persistent mechanisms from reversible responses or selection? | Analyst family prompt, retaining the user's system-state intuition without asserting attractor dynamics |
| Q08 / other: endpoints and transport | Which clinical endpoint and population distinctions change whether an apparent disease signal can be transported to another setting? | Analyst broader prompt; metadata-only search coverage is insufficient to call this an established open problem |
| Q09 / PRC2, stored | Does disease stage drive the PRC2 catalytic core (EZH2) where it drives PHF19? | Exact stored title; Q09a/Q09b aliases preserve both project contexts; no new author adoption assumed |
| Q10 / technical, stored | evidence-bound terms | Exact stored technical measurement query. Retained in coverage, not silently promoted to a biological research priority |

These are **leads**, not a fabricated literature-derived shortlist. Q01–Q08 are
explicit analyst/user-originated proposals. The source survey supplied metadata
coverage and permission limits, but no inspected primary-text assumption or
question extraction. No source-assertion candidate from an unread abstract is
represented as read evidence. The unknown yield is a discovery result.

## Source identities, queries, read limits and incidents

The complete source ledger follows, so this attachment alone retains its citations,
coverage and dispositions. Separate attachment pilot-source-ledger-v1.md preserves
the same ledger. No raw papers, patient data or protected result bundles are included.

# Pilot source ledger v1 — 2026-10-30

Task sci-b2755f; step sci-d3044e. Reader: controller (Codex). Frozen setup:
pilot-setup-v1.md, SHA-256 9801114ed3a1919a3cd046074c68a70e23d5a192ae4e8a91eb0695561c68ae56.
Quarry revision 7008433c8d3007b38a8fb08598e7e3ed49e965eb, registered checkout's
own environment. Every command used uv run --frozen quarry with --in pubmed,
--native <query>, -n 6 and --json. Metadata output contract checked in source:
ESummary title, PMID, DOI/PMC xrefs, date and journal only; no abstract requested.
Raw metadata responses/logs remain in retained task scratch, not a raw-paper corpus.

## Budget and access verdict

7/24 search attempts, all exit 0; 42 returned query occurrences collapse to 32
unique PubMed records. One separate probe identity lookup adds PMID 40906971:
33 unique bibliographic records screened against roster publication IDs/DOIs.
These are record identities, not 33 independent studies. No cross-record DOI alias
was identified; overlapping cohorts are not independent study support.
Full-text-for-reading attempts 0/18; completed full-text reads 0; abstract reads 0;
article-section reads 0. One section-only live probe, separate from full-text
reading attempts, returned HTTP 500. No invisible retry or cap expansion occurred.
Caps remain unexhausted; evidence retrieval failed before scientific extraction.

Service ordering: ESearch default with no explicit sort, positions preserved below;
coverage is limited for every query. Recent-title and relevance bias is substantial.
The six intended families were queried; this is not six evidence-covered families.
No review bodies, reference lists, abstracts or primary results sections were read.

## Queries and complete returned identity dispositions

1. **broad**: `"multiple myeloma"[Title/Abstract] AND (question* OR limitation* OR challenge*) AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`; service total 4009, returned 6, coverage limited.
2. **heterogeneity**: `"multiple myeloma"[Title/Abstract] AND (heterogeneity OR subtype* OR generaliz*) NOT review[Publication Type] AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`; service total 2420, returned 6, coverage limited.
3. **progression**: `"multiple myeloma"[Title/Abstract] AND (initiation OR progression OR precursor) NOT review[Publication Type] AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`; service total 13381, returned 6, coverage limited.
4. **measurement**: `"multiple myeloma"[Title/Abstract] AND (measurement OR proxy OR "cell mixture" OR purity) NOT review[Publication Type] AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`; service total 3920, returned 6, coverage limited.
5. **microenvironment**: `"multiple myeloma"[Title/Abstract] AND (microenvironment OR immune) NOT review[Publication Type] AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`; service total 5274, returned 6, coverage limited.
6. **treatment**: `"multiple myeloma"[Title/Abstract] AND (response OR resistance) NOT review[Publication Type] AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`; service total 12597, returned 6, coverage limited.
7. **persistence**: `"multiple myeloma"[Title/Abstract] AND (relapse OR persistence OR "clonal evolution") NOT review[Publication Type] AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`; service total 8495, returned 6, coverage limited.

| Row | Identity/primary locator | Title metadata (up to 25 words) | Publication date and xrefs | Query occurrences | Actual read/disposition |
|---|---|---|---|---|---|
| S01 | [pubmed:42956534](https://pubmed.ncbi.nlm.nih.gov/42956534/) | Immunotherapy in multiple myeloma: Molecular mechanisms, current clinical strategies, resistance, and future perspectives. | 2026-10-15; doi:10.1016/j.seminoncol.2026.152568 | query 1/broad position 1 | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |
| S02 | [pubmed:42953531](https://pubmed.ncbi.nlm.nih.gov/42953531/) | Multiple Myeloma Presenting as a Pancoast-Like Tumor: A Diagnostic Challenge. | 2026-09-28; doi:10.7759/cureus.117093, pmc:PMC13716347 | query 1/broad position 2; query 3/progression position 1 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S03 | [pubmed:42938792](https://pubmed.ncbi.nlm.nih.gov/42938792/) | CAR T-Cell Therapy in Hematological Malignancies: Mechanisms, Innovations, and Challenges. | 2026-10-09; doi:10.3390/cancers18203254, pmc:PMC13702778 | query 1/broad position 3 | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |
| S04 | [pubmed:42935712](https://pubmed.ncbi.nlm.nih.gov/42935712/) | Multiple myeloma: an overview of drug therapies and supportive care. | 2026-10-01; doi:10.18773/austprescr.2026.044, pmc:PMC13696861 | query 1/broad position 4 | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |
| S05 | [pubmed:42935493](https://pubmed.ncbi.nlm.nih.gov/42935493/) | Cardiac Amyloidosis in Monoclonal Gammopathy of Undetermined Significance. | 2026-10-25; doi:10.7759/cureus.118586, pmc:PMC13696110 | query 1/broad position 5 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S06 | [pubmed:42930200](https://pubmed.ncbi.nlm.nih.gov/42930200/) | Challenges of Conducting a Feasibility Pilot Randomized Controlled Trial During COVID-19 Restrictions: Rivaroxaban Versus Acetyl Salicylic Acid in Patients with Multiple Myeloma on Lenalidomide-Based Therapy … [abbreviated] | 2026-10-20; doi:10.3390/curroncol33100633, pmc:PMC13702975 | query 1/broad position 6 | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |
| S07 | [pubmed:42952746](https://pubmed.ncbi.nlm.nih.gov/42952746/) | Crystalline versus non-crystalline light-chain proximal tubulopathy: a case series. | 2026-10-14; doi:10.3389/fmed.2026.1963349, pmc:PMC13713427 | query 2/heterogeneity position 1; query 3/progression position 3 | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |
| S08 | [pubmed:42952551](https://pubmed.ncbi.nlm.nih.gov/42952551/) | Practice patterns in myeloma bone disease: a multi-center survey. | 2026-10-14; doi:10.3389/fonc.2026.1948667, pmc:PMC13713382 | query 2/heterogeneity position 2; query 6/treatment position 2; query 7/persistence position 2 | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |
| S09 | [pubmed:42923449](https://pubmed.ncbi.nlm.nih.gov/42923449/) | Monoclonal Interstitial Nephritis with IgA-Kappa Plasma Cells Deposition in Sjögren Syndrome: A Case Report. | 2026-09-08; doi:10.1159/cnd/abxag004, pmc:PMC13688647 | query 2/heterogeneity position 3 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S10 | [pubmed:42913707](https://pubmed.ncbi.nlm.nih.gov/42913707/) | Factors Associated With Clinical Trial Participation in Adult Hematopoietic Stem Cell Transplantation Recipients: A Center for International Blood and Marrow Transplant Research (CIBMTR) Analysis. | 2026-10-22; doi:10.6004/jnccn.2026.7054 | query 2/heterogeneity position 4 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S11 | [pubmed:42897348](https://pubmed.ncbi.nlm.nih.gov/42897348/) | Molecular predictors of minimal residual disease in newly diagnosed multiple myeloma treated with quadruplet therapy. | 2026-10-19; doi:10.1038/s41591-026-04692-0 | query 2/heterogeneity position 5 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S12 | [pubmed:42891620](https://pubmed.ncbi.nlm.nih.gov/42891620/) | Identification of Macrophage Polarization-Related Biomarkers in Multiple Myeloma Using Integrated Bioinformatics. | 2026-10-16; doi:10.3791/72728 | query 2/heterogeneity position 6 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S13 | [pubmed:42952767](https://pubmed.ncbi.nlm.nih.gov/42952767/) | Glomerular diseases associated with multiple myeloma: renal pathology and survival outcomes in a retrospective study at Charles Nicolle Hospital, Tunis, Tunisia. | 2026-06-08; doi:10.11604/pamj.2026.54.35.38464, pmc:PMC13713757 | query 3/progression position 2 | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |
| S14 | [pubmed:42952296](https://pubmed.ncbi.nlm.nih.gov/42952296/) | Proliferating Cell Nuclear Antigen as New Therapeutic Target in Multiple Myeloma. | 2026-10-29; doi:10.1158/1535-7163.MCT-25-1543 | query 3/progression position 4 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S15 | [pubmed:42948798](https://pubmed.ncbi.nlm.nih.gov/42948798/) | Vitality as a Prognostic Biomarker in Hematologic Malignancies: Association With Overall Survival and Progression-Free Survival. | 2026-09-26; doi:10.7759/cureus.116984, pmc:PMC13712484 | query 3/progression position 5 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S16 | [pubmed:42946606](https://pubmed.ncbi.nlm.nih.gov/42946606/) | Teclistamab Response- and Relapse-Related Immune Correlates in the MajesTEC-1 China Cohort. | 2026-09-22; doi:10.1016/j.clml.2026.09.014 | query 3/progression position 6; query 5/microenvironment position 2; query 6/treatment position 4; query 7/persistence position 3 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S17 | [pubmed:42959044](https://pubmed.ncbi.nlm.nih.gov/42959044/) | Consistency and correlation of a domestic Kehua serum free light chain assay with two imported analytical systems. | 2026-10-15; doi:10.3389/fonc.2026.1900671, pmc:PMC13716613 | query 4/measurement position 1 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S18 | [pubmed:42935042](https://pubmed.ncbi.nlm.nih.gov/42935042/) | Ubiquitin Protease Levels and Mitochondrial DNA Synthesis in Multiple Myeloma. | 2026-10-01; doi:10.31557/APJCP.2026.27.10.3517 | query 4/measurement position 2 | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |
| S19 | [pubmed:42930578](https://pubmed.ncbi.nlm.nih.gov/42930578/) | Prognostic Impact of EASIX According to the Timing of Assessment in Newly Diagnosed Multiple Myeloma Undergoing Autologous Stem Cell Transplantation. | 2026-10-10; doi:10.3390/medsci14060659, pmc:PMC13706759 | query 4/measurement position 3 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S20 | [pubmed:42928255](https://pubmed.ncbi.nlm.nih.gov/42928255/) | AI-based automated body composition analysis from whole-body MRI and (PET-) CT: an intermodal comparison from same-day examinations. | 2026-10-24; doi:10.1186/s40644-026-01134-5, pmc:PMC13700498 | query 4/measurement position 4 | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |
| S21 | [pubmed:42926231](https://pubmed.ncbi.nlm.nih.gov/42926231/) | Patient-reported outcomes and skeletal symptoms in multiple myeloma stratified by proteasome inhibitor-based therapy: a prospective interdisciplinary cohort study. | 2026-10-15; doi:10.1186/s12885-026-17177-7, pmc:PMC13695283 | query 4/measurement position 5 | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |
| S22 | [pubmed:42923061](https://pubmed.ncbi.nlm.nih.gov/42923061/) | Integrated hs-cTnI, global longitudinal strain, and coronary artery calcium for risk stratification of anthracycline-related cardiac dysfunction in multiple myeloma. | 2026-10-08; doi:10.3389/fcvm.2026.1830462, pmc:PMC13686920 | query 4/measurement position 6 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S23 | [pubmed:42957756](https://pubmed.ncbi.nlm.nih.gov/42957756/) | Single-cell analysis reveals favorable responses of tumor-associated monocytes to bortezomib-based treatment in multiple myeloma. | 2026-10-28; doi:10.1038/s41698-026-01666-w | query 5/microenvironment position 1; query 6/treatment position 1 | confirmed result title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S24 | [pubmed:42938920](https://pubmed.ncbi.nlm.nih.gov/42938920/) | Infectious Complications and Toxicities of the Teclistamab Plus Daratumumab Combination in Relapsed or Refractory Multiple Myeloma: A Disproportionality and Drug-Interaction Analysis of the FDA Adverse … [abbreviated] | 2026-10-20; doi:10.3390/cancers18203388, pmc:PMC13702562 | query 5/microenvironment position 3; query 7/persistence position 4 | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |
| S25 | [pubmed:42923674](https://pubmed.ncbi.nlm.nih.gov/42923674/) | Machine learning-based prognostic model and immune landscape analysis in multiple myeloma. | 2026-09-15; doi:10.62347/EOZA1443, pmc:PMC13687873 | query 5/microenvironment position 4 | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |
| S26 | [pubmed:42904597](https://pubmed.ncbi.nlm.nih.gov/42904597/) | A role for eIF5A in translational control of stress-inducible proteins in multiple myeloma cell lines. | 2026-10-21; doi:10.1002/1878-0261.70328, pmc:PMC13685402 | query 5/microenvironment position 5 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S27 | [pubmed:42902067](https://pubmed.ncbi.nlm.nih.gov/42902067/) | Integrated transcriptomics reveals a TNFRSF-metabolism axis and a context-dependent BCMA signaling state in myeloma progression. | 2026-07-24; doi:10.1007/s00277-026-07192-w, pmc:PMC13683256 | query 5/microenvironment position 6 | confirmed result title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S28 | [pubmed:42949631](https://pubmed.ncbi.nlm.nih.gov/42949631/) | ALDH2 Suppresses Ferroptosis and Promotes Bortezomib Resistance in Multiple Myeloma Through the KEAP1-NRF2 Feedback Loop. | 2026-10-28; doi:10.1002/advs.78403, pmc:PMC13715670 | query 6/treatment position 3 | confirmed result title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S29 | [pubmed:42938801](https://pubmed.ncbi.nlm.nih.gov/42938801/) | Associations of Baseline Cognitive and Psychosocial Function with Clinical Outcomes After Autologous Stem Cell Transplantation in a Multiple Myeloma Sample. | 2026-10-10; doi:10.3390/cancers18203264, pmc:PMC13702346 | query 6/treatment position 5 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S30 | [pubmed:42936704](https://pubmed.ncbi.nlm.nih.gov/42936704/) | Prognostic value of simultaneous [(18)F]FDG-PET/MRI in refractory multiple myeloma treated with anti-BCMA CAR T. | 2026-10-26; doi:10.1002/hem3.70515, pmc:PMC13702043 | query 6/treatment position 6; query 7/persistence position 5 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S31 | [pubmed:42957637](https://pubmed.ncbi.nlm.nih.gov/42957637/) | Beyond binary: graded frailty assessment and outcomes after CAR-T cell therapy in relapsed/refractory multiple myeloma. | 2026-10-28; doi:10.1038/s41408-026-01653-1 | query 7/persistence position 1 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S32 | [pubmed:42933856](https://pubmed.ncbi.nlm.nih.gov/42933856/) | Concurrent myelomatous pleural and pericardial effusions with cardiac tamponade in relapsed extramedullary IgA kappa multiple myeloma. | 2026-10-26; doi:10.1136/bcr-2026-277613 | query 7/persistence position 6 | possible result-bearing title; source stopped; incident awaiting mm disposition; excluded from ranking/consequences |
| S33 | [pubmed:40906971](https://pubmed.ncbi.nlm.nih.gov/40906971/) | Timing Genomic Antigen Loss in Multiple Myeloma Treated with T Cell-Redirecting Immunotherapies. | 2025-11-03; doi:10.1158/2643-3230.BCD-25-0005, pmc:PMC12514755 | probe-only identity lookup; first lexicographic exposed roster publication, not a ranked scientific source | no unambiguous result claim identified in title; metadata-only; no usable isolated mapping route; no scientific assertion extracted |

## Mapping and probe

All 32 search-result identifiers had no exact PMID/normalized-DOI match among
all 1559 roster entries at mm a7250080ffa99369884eec670c42a21380482b6f. No title
similarity was promoted to identity. Accessions/aliases could not be resolved
without unavailable isolated availability/design sections; unknown is not safe.

Probe publication PMID 40906971 / DOI 10.1158/2643-3230.BCD-25-0005 /
PMC12514755 maps to roster entry bcd-25-0005-antigen-loss-cohort, referencing
cohorts bcd-25-0005-antigen-loss-cohort and commpass. The entry is exposed from
ledger §4.2, and fresh amendment-7 grouping assigns both to exposed discovery
groups. Known relevant cohorts were permitted; additional cohorts were not
assumed absent. Selection was only a deterministic permitted-source route probe,
not a discovery or feasibility preference for that paper's topic.

Exact probe: GET https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12514755/fullTextXML,
intended to feed the rehearsed select-section.py data-availability projection
before display. Observed HTTP 500; no article bytes, availability section,
abstract or result was displayed. Route unavailable for this run under its
one-probe rule. Sources requiring it stay metadata-only; no whole-page fallback.
The synthetic route proof remains valid, while live provider shape is unverified.

## Exposure incidents and disposition

Three confirmed result-bearing titles: PMID 42957756, 42949631 and 42902067.
Actual content is the title field recorded above, read on 2026-10-30 by controller
(Codex). These explicitly assert treatment-conditioned response or molecular/
resistance findings. Cohort mapping is unknown; no roster cohort is declared
exposed by guess. They were stopped after the metadata batch review and excluded
from consequence/ranking evidence. No further material from them was requested.

Seventeen possible result-bearing/association/case/outcome titles are separately
marked above. Their content may describe an objective or proposal rather than an
actual result; uncertainty is not silently converted to confirmed exposure.
They remain omitted from comparison evidence pending disposition.

Existing mm workflow follow-up **mm-eca42c** contains the exact title content,
source identities, reader/date, mapping uncertainty and required disposition.
This filing records routing only, not resolved exposure or changed assignments.
No mm policy/roster/reservation or scientific record was edited by this sweep.
Other sources continued under metadata-only limits. No empirical assertion was
extracted or attributed to an unread abstract or primary article.
