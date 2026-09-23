# mm30 through the belief-path commands — record

**Date:** 2026-09-23
**Status:** run 2026-09-23, complete. The predictions (§2) were committed before the run (`6e96bf6`); every one is confirmed (§4). The path reached a computed belief with the assessment admitted, which is the design's success criterion.
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

### 3.1 The operator recipe

Run once, before any command, as a script beside the work directory (design §8.2;
`.work/mm30-commands/` beside the main checkout, gitignored). The contract document is
the kernel driver's `tools/reproduction/mm30.yaml` with its `lineage` changed to
`genesis`, since the loader takes no predecessor (design §5.2); its sorts, `estimands:`
row, plan and bindings are otherwise the driver's. Verbatim:

```python
"""The operator recipe (belief-path design §8.2): the world, corpus and store an
operator initializes before the commands run. Operator-time library calls under
an authority the operator constructs; recorded verbatim in the record."""
import secrets
from hashlib import sha256
from pathlib import Path

from beliefs.consulted import CorpusPins
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.holdings.reduce import holdings_rule_bundle
from beliefs.permit import Authority, WritePermit
from beliefs.profile import compile_profile, shipped_base_contract, shipped_domain_contract
from beliefs.root import init_corpus_root, init_store_root, init_world_root, open_corpus, open_world
from beliefs.world import Fresh, WorldConfig
from beliefs.world.rules import install_rule_binding

from science.contracts import load_contract_document

WORK = Path(__file__).resolve().parent
AUTH = Authority(WritePermit.full(), "operator")
# The four vocabulary lists the contract binds by dataset identity, built as the
# kernel's reproduction driver builds them (tools/reproduction/lists.py).
LISTS = {"CONCEPTS": "mm30-concepts.txt", "LEVELS": "mm30-stage-levels.txt",
         "MEASURES": "mm30-measures.txt", "IDENTIFICATIONS": "mm30-identifications.txt"}
doc = WORK / "mm30.yaml"   # the kernel driver's mm30.yaml re-authored `lineage: genesis`
text = doc.read_text()
for placeholder, name in LISTS.items():
    digest = "sha256:" + sha256((WORK / name).read_bytes()).hexdigest()
    address = dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name=name, digest=digest),)))
    text = text.replace("{{" + placeholder + "}}", address.removeprefix("dataset:"))
    print(f"{placeholder}: {address}")
doc.write_text(text)
base = shipped_base_contract()
contract, _ = load_contract_document(doc, base)
profile = compile_profile(base, [shipped_domain_contract("biology"), contract])
pins = CorpusPins(science_contract="science:" + profile.base_contract_identity,
                  domains={ns: f"{ns}:{i}" for ns, i in profile.activated_contracts.items()})
config = WorldConfig(WORK / "world", secrets.token_hex(16), (WORK / "corpus",))
init_world_root(config, authority=AUTH)
init_corpus_root(WORK / "corpus", authority=AUTH)
store_id = init_store_root(WORK / "store", authority=AUTH)
open_corpus(WORK / "corpus", authority=AUTH, profile=profile).adopt_manifest(profile=pins)
world = open_world(config, authority=AUTH)
world.admit(WORK / "corpus", provenance=Fresh())
install_rule_binding(world, holdings_rule_bundle())   # the holdings reducer the reads derive through
print(f"world_id: {config.world_id}")
print(f"store_id: {store_id}")
(WORK / "science.toml").write_text(f'''\
world_root = "{WORK / 'world'}"
world_id = "{config.world_id}"
corpus_roots = ["{WORK / 'corpus'}"]
operations_root = "{WORK / 'ops'}"
domains = ["biology"]
contracts = ["{doc}"]
store_root = "{WORK / 'store'}"
''')
```

It printed the four list addresses (concepts `dataset:sha256:be3bf183…`, stage levels
`…85b5e347…`, measures `…08027c2e…`, identifications `…79e30710…`), world
`1f088f8ae3723f3471872a4c94bfa5de` and store `0f0659a3f717a69bee585b5821450f87`, and
wrote `science.toml` with `domains = ["biology"]`, the document under `contracts`, and
`store_root`. `science status` then showed one corpus, known, live and present, with no
records and no epoch.

### 3.2 The commands

One `science mcp serve --config science.toml` process, so one attended session: each
call a JSON-RPC `tools/call` frame on its stdin and its reply read from its stdout, as a
coding-agent session's MCP client sends them. The driver script and the full transcript
(`walk.jsonl`) stay in the work directory. The walk took 36 s wall-clock, 2026-09-23T20:55:00Z
to 20:55:36Z; the server wrote nothing to stderr. No call refused.

| # | command | invocation | minted |
|---|---|---|---|
| 1 | `dataset` (concept list) | `100462b9…` | `dataset:sha256:be3bf183…` and its `Found` observation |
| 2 | `claim` (`concept:disease-stage` affects `protein:PHF19`, `causal_effect`, `positive`) | `5d0610bb…` | `proposition:concept-disease-stage-affects-protein-phf19` |
| 3 | `dataset` (the GSE179929 matrix, `locator = accession:GSE179929`) | `52989f62…` | `dataset:sha256:a6bf229e…` and its observation |
| 3a–3c | `dataset` (stage levels, measures, identifications) | `c8261d79…`, `1fd57fd3…`, `f8c38c8e…` | `…85b5e347…`, `…08027c2e…`, `…79e30710…`, each with its observation |
| 4 | `spec` (typed estimand; the driver's prose; `alpha=0.05`) | `6948f0d9…` | `analysis-spec:b617f5d80aa063d5…` |
| 5 | `run` (the driver's rendered bundle, `analysis/workflow/Snakefile`) | `4d589205…` | `run:d9ed67b3…`, `boundary-policy/confined-v1`, capabilities `closure-confined-filesystem`, `from-bundle`, `network-denied` |
| 6 | `assess` | `82727c14…` | `assessment:51e63dbff46a4198`, outcome `inconclusive` |
| 7 | `verify` | `19835517…` | the replayed `run:ca9141f5…` (same policy and capabilities) and `verification:b96439f8…`: `clean-environment`, `passed` |
| 8 | `belief` | `6c165fde…` | nothing; `NoBelief(no-directional-outcome)` |
| — | `next` | `3edcfde2…` | nothing; the proposition classified `admitted` |

Then the CLI, against the same config after the MCP server exited: `science belief
--proposition proposition:concept-disease-stage-affects-protein-phf19` and `science
next`, both exit 0; each rendering is byte-identical to the MCP reply for the same
read (framework §9.4). The corpus holds 16 records: one proposition, five datasets,
five holdings observations, one analysis spec, two runs, one assessment and one
verification.

## 4. Predictions, marked

| # | observed | mark |
|---|---|---|
| P1 | `proposition:concept-disease-stage-affects-protein-phf19` | confirmed |
| P2 | `780ace5964c8ab8315607ee9ed084b4acf6bf0f3f20f82bbbd41c11408cddb1c`, operator `mm30/affects-concept-molecular-entity` | confirmed |
| P3 | `dataset:sha256:a6bf229ef0abd8e11f0b7f017cbdb6977395e23d83fb122fcf141f723ba1e448` | confirmed |
| P4 | concepts `sha256:c7e45f81…`, address `dataset:sha256:be3bf183…` (the rebuild run's `concepts_address`) | confirmed |
| P5 | the three lists held by steps 3a–3c before `spec` | confirmed |
| P6 | method, assumptions, falsification, the observes input, `alpha = 0.05` and deterministic nondeterminism as the driver's; the estimand projection **equal** to the driver's current frozen spec's (levels `ndmm`→`pd` on slot 0, `rna-seq-tpm` additive, reference 0, observational, no conditioning), applicability empty | confirmed |
| P7 | `b617f5d8…` against the record's `86aaa1a8…` | confirmed, and narrowed: against the kernel driver's **current** spec (`10e8bfce…`, which carries the same typed estimand), every field is equal except the two rule identities — the driver binds the same implementations (`impl-outcome-file-1`, `impl-eq-1`) under its legacy names `mm30-reproduction/outcome-file/v1` and `content-identity-equality/v1`, the surface under the kernel's `beliefs/…/v1` (design §6.1). The identity difference is the rule names and nothing else |
| P8 | `stats.tsv` z = 1.1589, p = 0.2465, n = 51, confined, both runs | confirmed |
| P9 | `inconclusive` | confirmed |
| P10 | `clean-environment`, `passed`; both result manifests equal | confirmed |
| P11 | `NoBelief(no-directional-outcome)` through MCP and the CLI | confirmed: the assessment is admitted (P12), and the frozen rule's `inconclusive` is the data's answer |
| P12 | `admitted` through MCP and the CLI | confirmed |

The design's criterion — a coding-agent session over a beliefs world where `run`
executes a real analysis under confinement, `verify` reaches clean-environment, and
`assess` admits the result to a computed belief, every step a governed record — is
met. That the belief is `NoBelief` is the data's answer under this rule, as the kernel
record's rebuild run also found.

## 5. Findings

Classified as design §8.1 asks. The path itself raised no refusal; everything below
was found while building the commands the path runs, or on reading its results.

| # | finding | class | where filed |
|---|---|---|---|
| F1 | The confinement closure refused a `.pth` import of a builtin (`sys`, from coverage's `a1_coverage.pth`, which pytest-testmon installs), so no run could be minted from the dev environment | defect | `beliefs-76fe0e`, fixed in beliefs `ff45ecb` |
| F2 | A run committed through the operation port was invisible to the root's shared writer index, so `assess` after `run` in one session was refused | defect | `beliefs-40e593`, fixed in beliefs `70ff54e` |
| F3 | `ResultManifest` keeps the workflow's target order in memory and sorts when stored, so the content-equality rule reads `failed` for identical outputs when a stored original meets a fresh replay | defect | `beliefs-97075f`, open; `verify` builds its verification from both stored forms, the computation the audit repeats |
| F4 | The refusal envelope drops a kernel refusal's `detail`, so F1 surfaced as a bare `closure-unsupported` | defect | `sci-23e773` |
| F5 | The contract-document loader ignores unknown top-level keys; the driver's `also: [biology]` was dropped silently | defect | `sci-3a01b3` |
| F6 | The predecessor mm30 checkout is gone from this host; the matrix came from the kernel store's held copy, whose address is the oracle's | corpus-work | this record (§1); nothing to file |
| F7 | The kernel driver still spells its rules by their legacy identities, so its spec and the surface's differ in identity while binding the same implementations | design-gap | noted for the kernel reproduction lane; not filed here, since it is the driver's (throwaway by declaration) spelling |
