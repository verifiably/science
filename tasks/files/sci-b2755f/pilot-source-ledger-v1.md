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
