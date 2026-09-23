# mm30 through the belief-path commands — record

**Date:** 2026-09-23
**Status:** predictions written before the run; the run and its comparison follow.
**Scope:** the measurement of the belief-path design
(`docs/specs/2026-09-09-belief-path-commands-design.md` §8; plan Task 13): mm30's one
proposition reproduced afresh through the eight commands, from an empty adopted
corpus, over `science mcp serve` driven by a coding-agent session, with the CLI used
for `belief` and `next`. The oracle is the kernel's mm30 reproduction record
(`beliefs` `docs/designs/2026-09-05-mm30-reproduction.md`, its 2026-09-08 re-run and
its §10 estimand-typing addendum). A measurement: it produces this record and the
findings it files. It changes no code.

## 1. Preflight

Written before the run.

- **Confinement:** `beliefs.confinement.host_prerequisites()` is `None` on this host
  (bubblewrap present), so `run` and `verify` execute under `CONFINED_POLICY`.
- **The predecessor checkout is absent from this host.** The oracle record read the
  expression matrix from the predecessor mm30 checkout
  (`<predecessor>/data/supp/orig/misund2022/GSE179929_gene_tpm.txt.gz`); that path
  does not exist here. The same bytes are held in the kernel reproduction's store
  (`beliefs` `.work/reproduction/mm30/store/gse179929/GSE179929_gene_tpm.txt.gz`):
  6,154,181 bytes, whose dataset address under the file's basename is
  `dataset:sha256:a6bf229ef0abd8e11f0b7f017cbdb6977395e23d83fb122fcf141f723ba1e448`,
  the oracle's. The run copies those bytes into its own work directory and holds
  them through `dataset`; identity, not provenance of the copy, is what the
  comparison reads.
- **The vocabulary lists** are the four the kernel driver built
  (`tools/reproduction/lists.py`), taken from the same directory: concepts
  (`sha256:c7e45f81…`, the oracle's digest), stage levels, measures and
  identifications.
- **The four analysis parameters** the finding `beliefs-efc32d` names are supplied,
  as that finding says the driver's run supplied them, verbatim from the rebuild
  run's `target.yaml` (`beliefs` `docs/plans/2026-09-10-mm30-reproduction-rebuild-run/`):
  `value_row` `ENSG00000119403`, `value_row_symbol` `PHF19`, `group_separator` `_`,
  `positive_level` `PD`. They are authored input here, not derived.
- **Kernel state:** beliefs `main` carries `beliefs-76fe0e` (`ff45ecb`) and
  `beliefs-40e593` (`70ff54e`), both fixed during the command implementation;
  `beliefs-97075f` is open, and `verify` builds its verification from both runs'
  stored forms, which is the case that defect does not reach.

## 2. Predictions

Written before any command ran (design §8.3). Each is marked in §4 `confirmed`,
`confirmed for another reason: …`, or `refuted`.

| # | record value | oracle | predicted |
|---|---|---|---|
| P1 | proposition id | `proposition:concept-disease-stage-affects-protein-phf19` | equal |
| P2 | claim identity | `780ace5964c8ab83…` (2026-09-08) | equal: the sorted operator `mm30/affects-concept-molecular-entity` under the biology pack |
| P3 | expression dataset address | `dataset:sha256:a6bf229e…` | equal: same bytes |
| P4 | concept list digest | `sha256:c7e45f81…` | equal |
| P5 | the three estimand lists | held by the driver as datasets | each held through `dataset` before `spec`, as design §3 steps 3a–3c require |
| P6 | spec draft fields | the record's step 4 draft; the §10.2 typed estimand | equal for `method`, `assumptions`, `falsification`, inputs, rules (by their kernel identities) and `alpha = 0.05`; the estimand as §10.2 spells it (levels `ndmm`→`pd` on slot 0, `rna-seq-tpm` additive, reference 0, observational, unconditioned; empty applicability) |
| P7 | spec identity | `86aaa1a8…` | **differs**, by the rule identities (`beliefs/outcome-file/v1`) and the typed estimand; stated, not papered over |
| P8 | run | confined, `stats.tsv` z = 1.159, p = 0.246, n = 51 | the same statistics, confined |
| P9 | assessment outcome | `inconclusive` | equal |
| P10 | verification scope and verdict | `clean-environment`, `passed` | equal |
| P11 | belief | `NoBelief(no-eligible-assessment)` (2026-09-05); `NoBelief(no-directional-outcome)` (the rebuild run) | `NoBelief(no-directional-outcome)`: the assessment is admitted and the frozen rule's `inconclusive` is the data's answer |
| P12 | `next` | — | the proposition classified `admitted` |

## 3. The path

To be filled from the run.

## 4. Predictions, marked

To be filled from the run.

## 5. Findings

To be filled from the run.
