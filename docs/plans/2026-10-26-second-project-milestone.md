# Second-Project Milestone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the second-project milestone (projects design §9.2) against the live world root and leave its record, with one code change first: the launcher loads contract chains.

**Architecture:** Task 1 is the only change to `science` (a `contracts`/`read_contracts` entry may be a table naming a document and its predecessor chain). Tasks 2–3 are kernel-level driver scripts under the task directory that build the working corpus and declare the two unheld datasets, before any server opens. Task 4 commits the record's preflight and predictions. Task 5 drives the frozen schedule through one `science mcp serve` session; Task 6 runs the launcher arms; Task 7 completes the record, attaches the evidence and files the findings.

**Tech Stack:** Python 3.13 under `uv` in `python/`; `beliefs` as an editable path dependency; pytest through `just test-one` / `just test-fast`; `science` run by explicit path `python/.venv/bin/science`.

**Spec:** `docs/specs/2026-10-26-second-project-milestone-design.md` (accepted at review round 2, revision 3 at `2c7a85c`). Section numbers below (§) are that document's unless prefixed "projects design".

## Global Constraints

- Paths: `<data root>` is the directory `SCIENCE_CONFIG` names a file in (`/mnt/ssd/science` on this host); `<world>` is `<data root>/worlds/aec951bc6becacced13df8f7ae6f8abf`; `<task dir>` is `$WORK_ROOT/science/sci-0d00d2`; `<wt>` is this worktree, `.worktrees/second-project-milestone`. Committed text uses the placeholders, never the host paths (the docs hook refuses them).
- Run the worktree's `science` by explicit path, `<wt>/python/.venv/bin/science`, never a launcher on `PATH`; run driver scripts with `<wt>/python/.venv/bin/python`.
- No query address, digest or identity is authored by hand: each is read from a record, a held list, or computed from bytes, and the record prints where it came from.
- Tests run through the recipes only: `just test-one <args>` for one test, `just test-fast` before each commit (run from `<wt>`).
- Conventional commits, no AI attribution. Task records: `tasks start <id>` before a task's first change, `tasks done <id> "<what landed>"` when its commit lands, both from `<wt>`.
- Nothing is held into the store, nothing is published, no corpus manifest is edited, the mm30 corpus is never re-admitted.
- Drivers and transcripts live under `<task dir>`; the directory is noted on the task when created (host, path, purpose, owner) and its kept files attached at the end (§4.3).

## Review Focus

Inputs the spec implies and no criterion exercises; each line's test is in the task that owns the code.

1. A chain whose `predecessors` are listed newest first: refuses by name (`no predecessor was supplied`), never `internal-error` (Task 1).
2. A successor document given as a bare path under `contracts`: refuses by name (Task 1).
3. A chain table whose `document` or `predecessors` key is missing or empty: refuses naming the key (Task 1).
4. A chain under `read_contracts`: the successor is available to mounts and not activated for the writer (Task 1).
5. A chain under `contracts` and the same document bare under `read_contracts`: the existing both-lists refusal fires on identity, not on path (Task 1).

---

### Task 1: Contract chain entries in the launcher config (`sci-7079e3`)

**Files:**
- Modify: `python/src/science/contracts.py` (`load_contract_document`, lines 98–125)
- Modify: `python/src/science/config.py` (the `local`/`readable` comprehensions, lines 178–179)
- Test: `python/tests/test_config.py`
- Modify: `docs/specs/2026-08-31-command-framework-design.md` §9.1 (dated amendment after the `read_contracts` amendment of 2026-09-30)
- Modify: `README.md` (the configuration paragraph, lines 53–57)

**Interfaces:**
- Produces: `science.contracts.load_contract_document(path: Path, base, *, predecessor: DomainContract | None = None) -> tuple[DomainContract, OperatorPlan | None]` (existing name, gains the keyword and catches `SuccessionViolation`).
- Produces: `science.contracts.load_contract_chain(document: Path, predecessors: Sequence[Path], base) -> tuple[DomainContract, OperatorPlan | None]`: parses `predecessors` oldest first, each the next one's predecessor, then `document`; refuses `invalid-input` naming the failing path and the kernel's message.
- Produces: `science.config.ScienceConfig` unchanged in shape; `available_contracts` and `plans` carry a chain's last contract. Task 2 consumes this through `load_config`.

- [ ] **Step 1: Write the failing tests** in `python/tests/test_config.py`, beside `test_contracts_compile_into_the_profile`. Build the successor document from `test_contracts.DOCUMENT`: same text with `lineage: genesis` replaced by `lineage: {successor: "<identity>"}` where `<identity>` is `parse_domain_contract(yaml.safe_load(DOCUMENT % ("0"*64))["contract"], source="v1", base=shipped_base_contract(), predecessor=None).content_identity`, and one operator appended under `operators:` (`affects-protein-protein: {arity: 2, arg_sorts: [protein, protein], sign_apt: true, layers: [causal], dimensions: []}`). Compute `expected` by parsing v2 with v1 as predecessor the same way (never a literal).

```python
def test_a_contract_chain_compiles_to_the_successor_identity(tmp_path):
    v1, v2, expected = _write_chain(tmp_path)
    cfg = load_config(write_config(tmp_path, contracts=f'[{{ document = "{v2}", predecessors = ["{v1}"] }}]'))
    assert cfg.profile.activated_contracts["testing"] == expected
    (plan,) = cfg.plans
    assert plan.operator_for("affects", "concept", "concept") == "testing/affects-concept-concept"

def test_a_chain_listed_newest_first_refuses_by_name(tmp_path):
    v1, v2, _ = _write_chain(tmp_path)
    refusal = assert_invalid_config(write_config(tmp_path, contracts=f'[{{ document = "{v1}", predecessors = ["{v2}"] }}]'))
    assert "no predecessor was supplied" in refusal.message and str(v2) in refusal.message

def test_a_successor_document_given_bare_refuses_by_name(tmp_path):
    _, v2, _ = _write_chain(tmp_path)
    refusal = assert_invalid_config(write_config(tmp_path, contracts=f'["{v2}"]'))
    assert "no predecessor was supplied" in refusal.message

def test_a_chain_whose_predecessor_does_not_match_refuses_by_name(tmp_path):
    v1, v2, _ = _write_chain(tmp_path)
    other = tmp_path / "other.yaml"
    other.write_text((DOCUMENT % ("1" * 64)))          # a different genesis of the same namespace
    refusal = assert_invalid_config(write_config(tmp_path, contracts=f'[{{ document = "{v2}", predecessors = ["{other}"] }}]'))
    assert "declares successor" in refusal.message

def test_a_chain_table_missing_a_key_refuses_naming_it(tmp_path):
    _, v2, _ = _write_chain(tmp_path)
    refusal = assert_invalid_config(write_config(tmp_path, contracts=f'[{{ document = "{v2}" }}]'))
    assert "predecessors" in refusal.message

def test_a_read_contracts_chain_is_available_to_mounts_only(tmp_path):
    v1, v2, expected = _write_chain(tmp_path)
    cfg = load_config(write_config(tmp_path, extra=f'read_contracts = [{{ document = "{v2}", predecessors = ["{v1}"] }}]\n'))
    assert "testing" not in cfg.profile.activated_contracts
    assert expected in {c.content_identity for c in cfg.available_contracts}

def test_a_chain_and_its_genesis_in_the_other_list_are_two_identities(tmp_path):
    v1, v2, expected = _write_chain(tmp_path)
    cfg = load_config(write_config(tmp_path, contracts=f'[{{ document = "{v2}", predecessors = ["{v1}"] }}]',
                                   extra=f'read_contracts = ["{v1}"]\n'))
    assert cfg.profile.activated_contracts["testing"] == expected

def test_a_chain_and_the_same_successor_bare_in_the_other_list_refuses(tmp_path):
    v1, v2, _ = _write_chain(tmp_path)
    refusal = assert_invalid_config(write_config(tmp_path, contracts=f'[{{ document = "{v2}", predecessors = ["{v1}"] }}]',
                                                 extra=f'read_contracts = [{{ document = "{v2}", predecessors = ["{v1}"] }}]\n'))
    assert "both contracts and read_contracts" in refusal.message
```

The last two pin today's both-lists rule on identity: the genesis `v1` beside the activated successor is two identities and loads; the same chain in both lists is one identity and refuses.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_config.py -k "chain or successor"`
Expected: FAIL; the chain tests with "contracts must be a list of strings" or an uncaught `SuccessionViolation`.

- [ ] **Step 3: Implement the loader.** In `contracts.py`: add `predecessor` to `load_contract_document`, pass it to `parse_domain_contract`, and catch `SuccessionViolation` (from `beliefs.errors`) beside `MalformedContract`, refusing `f"contract document {path} does not parse: {caught}"`. Add `load_contract_chain` as the Interfaces block states, parsing each predecessor through `load_contract_document(path, base, predecessor=previous)` and discarding their plans. In `config.py`: replace the two comprehensions by a helper `_contract_entries(raw: object, key: str) -> list[tuple[DomainContract, OperatorPlan | None]]` that accepts a string (as today) or a dict with exactly `document` (str) and `predecessors` (non-empty list of str), refusing `f"config {key} entry must be a path or a table with document and predecessors"` naming the missing key, and resolves every path with `located`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_config.py`
Expected: PASS, including the pre-existing contract tests.

- [ ] **Step 5: Amend the docs.** Framework design §9.1: after the 2026-09-30 `read_contracts` amendment add `**Amended 2026-10-26** (second-project milestone design §5.3): an entry of \`contracts\` or \`read_contracts\` is a path, or a table \`{ document, predecessors }\` naming a successor document and its predecessor documents oldest first; the loader parses the chain document by document and activates the last.` README configuration paragraph: one sentence naming the table shape.

- [ ] **Step 6: Fast check and commit**

Run: `just test-fast` then `just check`
Expected: both exit 0.

```bash
git add python/src/science/contracts.py python/src/science/config.py python/tests/test_config.py docs/specs/2026-08-31-command-framework-design.md README.md
git commit -m "feat(config): contract entries may name a predecessor chain"
```

Then `tasks done sci-7079e3 "contract chain entries in contracts/read_contracts; successor documents refuse by name"`.

---

### Task 2: Genesis of the working corpus and `science.toml`

**Files:**
- Create: `<task dir>/driver/genesis.py` (not committed; attached in Task 7)
- Create: `<data root>/contracts/mm30/{mm30-cut22.yaml,mm30-cut31.yaml,mm30.yaml}`, `<world>/corpora/working/`, `<world>/ops/`, `<data root>/science.toml`

**Interfaces:**
- Consumes: Task 1's chain entry through `science.config.load_config`.
- Produces: `<data root>/science.toml` exactly as §5.2 (relative paths against `<data root>`), and the working corpus pinned to base `52a43993…`, biology `24bcec43…`, mm30 `4af7c421…`, coordination v2. Tasks 3, 5, 6 consume the config path.

- [ ] **Step 1: Create the task directory and note it.** `mkdir -p <task dir>/driver <task dir>/inputs <task dir>/runs`, then `tasks note sci-0d00d2 "scratch: <host> <task dir> — drivers, downloaded inputs (discarded after digesting), run transcripts; owner this task"`.

- [ ] **Step 2: Write `genesis.py`** with these functions, run as `python genesis.py <data root> <beliefs checkout>`:
  - `concrete_documents(beliefs: Path, out: Path) -> list[Path]`: for each of `python/tools/reproduction/mm30-cut22.yaml`, `mm30-cut31.yaml`, `mm30.yaml`, read the text, drop the top-level `also:` line, replace `{{CONCEPTS}}`, `{{LEVELS}}`, `{{MEASURES}}`, `{{IDENTIFICATIONS}}` with the four addresses read from the mm30 corpus's dataset records (`<world>/corpora/mm30/dataset/*.md`): the record titled `mm30 concept vocabulary` → CONCEPTS, `mm30 stage-level vocabulary` → LEVELS, `mm30 measure vocabulary` → MEASURES, `mm30 identification vocabulary` → IDENTIFICATIONS, each address its `id` without the `dataset:` prefix; write to `out/<name>`; return the three paths oldest first.
  - `assert_chain(out: Path, pinned: str) -> None`: `load_contract_chain(out/"mm30.yaml", [out/"mm30-cut22.yaml", out/"mm30-cut31.yaml"], shipped_base_contract())[0].content_identity == pinned`, where `pinned` is read from `<world>/corpora/mm30/corpus.yaml` (`profile.domains.mm30` without its prefix); raise otherwise.
  - `write_config(data_root: Path) -> Path`: the §5.2 TOML verbatim.
  - `make_working_corpus(cfg: ScienceConfig, authority) -> None`: `init_corpus_root(cfg.write_root, authority=authority)`; `open_corpus(cfg.write_root, authority=authority, profile=cfg.profile).adopt_manifest(profile=CorpusPins(science_contract="science:"+cfg.profile.base_contract_identity, domains={ns: f"{ns}:{i}" for ns, i in cfg.profile.activated_contracts.items()}))`; `open_world(cfg.world, authority=authority).admit(cfg.write_root, provenance=Fresh())`.
  - `authority = Authority(WritePermit.full(), "sci-0d00d2-driver")`.
  - `main`: documents → config → `cfg = load_config(config_path)` → `assert_chain` → `make_working_corpus` → print the pins and the chain identity.

- [ ] **Step 3: Run it**

Run: `<wt>/python/.venv/bin/python <task dir>/driver/genesis.py <data root> <beliefs checkout>`
Expected: prints `mm30 chain: 4af7c4212d482ae60f429526ff5a8a6d4c335f70351a2687cd2062ffdedf437c` and the four pins; exit 0.

- [ ] **Step 4: Verify with the launcher**

Run: `SCIENCE_CONFIG=<data root>/science.toml <wt>/python/.venv/bin/science status`
Expected: two corpora, each `known=True live=True present=True`, no finding; `records in 8b5d0c80…` with 18 entries by kind as §3 C6; a `records in <working id>` block with no rows; `No current epoch.` Save the output to `<task dir>/runs/preflight-status.txt`.

- [ ] **Step 5: Note the genesis on the task**: `tasks note sci-0d00d2 "genesis: working corpus <id> admitted fresh; pins <four>; config at <data root>/science.toml; driver <task dir>/driver/genesis.py"`.

---

### Task 3: Declare the two unheld datasets

**Files:**
- Create: `<task dir>/driver/declare.py`, `<task dir>/driver/declared.json`

**Interfaces:**
- Consumes: Task 2's config.
- Produces: `declared.json` with keys `cohort` (dataset address), `annotation` (dataset address), `cohort_resources` and `annotation_resources` (name, bytes, md5, sha256 each), `condition_values` (the distinct `condition` strings, with the one equal to `diagnostico` labelled `ndmm` and the other `pd`). Task 5 reads it.

- [ ] **Step 1: Write `declare.py`**, run as `python declare.py <config path> <task dir>`:
  - `fetch(url: str, into: Path, md5: str) -> Path`: download with `urllib.request` into `into/<basename>`; refuse unless the md5 matches. The three sources and their published md5s: `https://zenodo.org/records/22399365/files/mm_counts.csv.gz?download=1` → `e18dc9b72619d6473e2274cf3823b395`; `https://zenodo.org/records/22399365/files/mm_metadata.csv?download=1` → `9201e47ffb0e3900b01fd96a913b56f6`; `https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_36/gencode.v36.annotation.gtf.gz` → `c03931958d4572148650d62eb6dec41a`.
  - `resource(path: Path) -> dict`: `{"name": path.name, "digest": "sha256:" + sha256(bytes)}`.
  - `condition_values(metadata: Path) -> dict[str, str]`: the distinct values of the `condition` column; `diagnostico` → `ndmm`, the other → `pd`; refuse unless exactly two.
  - `declare(cfg, authority, *, title, resources, locator, domain_facets=None) -> str`: `node = stored.dataset_node(title=title, resources=resources, empirical_observation={"locator": locator, "attested_by": authority.actor}, domain_facets=domain_facets)`; `open_corpus(cfg.write_root, authority=authority, profile=cfg.profile).add(node).id`.
  - Cohort: title `MMRF-CoMMpass teaching counts, 30 diagnosis and 30 relapse (Zenodo 22399365)`, resources `[counts, metadata]`, locator `doi:10.5281/zenodo.22399365`, `domain_facets={"gene-axis": <the same field names as the GSE179929 record's gene-axis facet in <world>/corpora/mm30/dataset/sha256__a6bf229e….md, with the axis the counts file's rows and the namespace Ensembl>}`.
  - Annotation: title `GENCODE release 36 primary annotation (gencode.v36.annotation.gtf.gz)`, one resource, locator the FTP URL, no domain facet.
  - After both declarations: write `declared.json`, then delete `<task dir>/inputs/*`.

- [ ] **Step 2: Run it**

Run: `<wt>/python/.venv/bin/python <task dir>/driver/declare.py <data root>/science.toml <task dir>`
Expected: two `dataset:sha256:…` addresses printed; `declared.json` written; `<task dir>/inputs/` empty.

- [ ] **Step 3: Verify.** `science status` now shows `dataset 2` in the working corpus; `grep -c '' <world>/corpora/working/holdings-observation/* 2>/dev/null` finds no observation (nothing held). Note on the task: the two addresses, the md5/sha256 pairs and the two `condition` values.

---

### Task 4: The record's preflight and predictions, committed before the run

**Files:**
- Create: `docs/records/2026-10-26-second-project-milestone.md` (§1 and §2 only)

**Interfaces:**
- Consumes: Task 2's status output, Task 3's `declared.json`.
- Produces: the committed schedule the driver follows; Task 5 copies its step ids (`S0`, `E1`, `W1`, …) into the transcript.

- [ ] **Step 1: Write §1 Preflight**: the mm30 record's shape (date, status line reading "predictions committed before the run (`<sha>`)", scope). Contents: C1–C8 as observed (the working corpus id, the four pins, the chain identity, the two declared addresses with their resource digests, the two `condition` values), the beliefs and science commits in use (`git -C <beliefs> rev-parse --short HEAD`, `git rev-parse --short HEAD`), confinement not needed (no run); and §5.1's reading-pass outputs: the overlap inventory (`depmap`, `tcga`; GTEx `health/meta`'s only), the first health question's wording, and the two datasets it needs held.

- [ ] **Step 2: Write §2 Schedule and predictions**: §5.6's table verbatim with placeholders filled (the EZH2 proposition id, the spec address left as `<minted>`, the two declared addresses), the four queries of §5.4 in full (the 285 term clauses generated by the Task 5 generator and pasted, with the held list's sha256 `c7e45f81…` stated beside them), the predicted `next` renderings as exact text, the predicted refusal text for R4, and the criterion verdicts predicted (`met` for 1, 2, 6, 7; `partly met` for 3, 4; `unmet` for 5).

- [ ] **Step 3: Commit** (`just check` first):

```bash
git add docs/records/2026-10-26-second-project-milestone.md
git commit -m "docs(records): second-project milestone preflight and predictions"
```

Put the commit sha into the status line in Task 7, not now.

---

### Task 5: The walk

**Files:**
- Create: `<task dir>/driver/walk.py`, `<task dir>/driver/terms.py`, `<task dir>/driver/selections.py`
- Create at run time: `<task dir>/runs/<timestamp>/{walk.jsonl,serve.stderr,epochs.json,selections.json,next-*.txt,publish-preview.txt,belief.txt}`

**Interfaces:**
- Consumes: `declared.json` (Task 3), the config (Task 2), the schedule ids (Task 4).
- Produces: the run directory above; `epochs.json` rows `{step, trigger, outcome, seconds, writes_since_previous}`; `selections.json` rows `{view, epoch, selected: [addresses]}`; `walk.jsonl` as the mm30 walk's (`call`, `arguments`, `result`, plus `seconds` and `step`).

- [ ] **Step 1: Write `terms.py`**: `term_clauses(store_root: Path) -> list[dict]`: read the held concept list at the store path the holdings reducer names for `dataset:sha256:be3bf183…` (find it under `<world>/store/mm30-concepts/`), refuse unless its sha256 is `c7e45f81…` (the mm30 record's P4), and return `[{"all": [{"references-term": line}]} for line in lines]` in file order; `query(clauses: list[dict]) -> str` dumps `{"version": "science.view-query.v1", "clauses": clauses}` as YAML. `mm_query(store_root) -> str` is the closure clause, the spec `addresses` clause and the 285 term clauses; `health_query(store_root, extra: list[str]) -> str` appends `{"all": [{"addresses": extra}]}`; `findings_query() -> str` is §5.4's `multiple-myeloma-findings`; `evidence_bound_query() -> str` replaces the term clauses by `concept:disease-stage` only, read from the stage → PHF19 proposition record's `args`.

- [ ] **Step 2: Write `selections.py`**: `selection(cfg, query_text: str) -> list[str]`: `world = open_world(cfg.world, authority=<read authority as world_belief.EPOCH_AUTHORITY's shape>)`; `view = open_world_view(world, current_epoch(world))`; `sorted(evaluate_query(view, parse_view_query(yaml.safe_load(query_text))).selected)` (read the `Selection` type's field name in `beliefs/world/selection.py` and use it). This is a kernel-level read the surface lacks; Task 7 files it.

- [ ] **Step 3: Write `walk.py`** from the mm30 walk's pattern (`subprocess.Popen` of `<wt>/python/.venv/bin/science mcp serve --config <cfg>`, one JSON-RPC `tools/call` per command, replies appended to `walk.jsonl`), with: `call(step, name, arguments) -> dict` timing each call; `epoch(step, trigger, writes) -> None` running `science epoch --config <cfg>` as a subprocess, timing it, parsing `built:`/`current:` from its first line into `epochs.json`; `cli(args) -> str` running the CLI by explicit path with `SCIENCE_CONFIG` set, saving stdout under the run directory. The schedule, in this order and nothing else between steps: `S0 status` → `E1 epoch(initial, [declarations])` → `W1 claim` (§5.5 step 2) and `spec` (§5.5 step 3; `dataset` = `declared.json`'s cohort, method text naming the annotation address) → `E2 epoch(evidence, [claim, spec])` → `W2 project ×4` (`multiple-myeloma`, `cancer`, `health`, `multiple-myeloma-findings`, queries from `terms.py`; `health`'s extra addresses = the EZH2 proposition, the spec address from W1's reply, the two declared addresses) → `next` once, saved as `next-stale.txt` (expected `epoch-stale`) → `E3 epoch(coordination-only, [project×4])` → `R1 selections` for the four projects → `W3 project-select health; question` (query = closure clause + `health`'s extra addresses, name `Does disease stage drive the PRC2 catalytic core (EZH2) where it drives PHF19?`) `; project-select cancer; reuse; project-select multiple-myeloma; question` (`evidence-bound terms`) → `E4 epoch(coordination-only, [question, reuse, question])` → `E5 epoch(none, [])` → `R2`: `next` under `multiple-myeloma`, `cancer`, `health` (each via `project-select` then `next`) and after `project-select --clear`, saved as `next-<name>.txt` → `R3 selection` of `evidence-bound terms`'s query → `R4 publish-preview --target multiple-myeloma-findings --to <run dir>/publish` saved verbatim → `R5 belief --proposition proposition:concept-disease-stage-affects-protein-phf19` → `status` saved as `status-final.txt` (M6) → the server exits.

- [ ] **Step 4: Run the walk**

Run: `<wt>/python/.venv/bin/python <task dir>/driver/walk.py <data root>/science.toml <task dir>`
Expected: every call `ok` except R4 `REFUSED` with `attribution-contract-unpinned`; `epochs.json` has five rows with outcomes `built, built, built, built, current`; `next-stale.txt` carries `epoch-stale`; the four `next-*.txt` are the §5.6 R2 text. A refusal anywhere else stops the run: note it on the task with its text and file it before retrying (§5.8).

- [ ] **Step 5: Note the run**: `tasks note sci-0d00d2 "walk: <run dir>; refusals: <list or none>; epochs: <five outcomes with seconds>"`.

---

### Task 6: The launcher arms (criteria 6 and 7)

**Files:**
- Create: `<task dir>/driver/arms.py`
- Create at run time: `<task dir>/runs/<timestamp>/arms/{workspace,unrelated,mcp}/…`

**Interfaces:**
- Consumes: the config; the walk's `next-health.txt` (Task 5).
- Produces: per arm `status.txt`, `projects.txt`, `next.txt`, `serve.stderr`; for the `mcp` arm also `next-cli.txt`, `next-project-mm.txt`, `projects-after.txt`.

- [ ] **Step 1: Write `arms.py`**: `arm(name, cwd: Path, run_dir) -> None` starts `science mcp serve --config <cfg>` with `cwd=cwd`, sends `project-select {"target": "health"}` over MCP, then runs the CLI `status`, `projects`, `next` by explicit path with the same `cwd` and `SCIENCE_CONFIG`, saves each, and terminates the server (stdin close, wait). The `workspace` arm's cwd is the mm program's workspace checkout; the `unrelated` arm's is `tempfile.mkdtemp()` holding `science.toml` (`world_root = "/nowhere"`), `science.yaml` (`project: decoy`) and `corpus.yaml` (`corpus: decoy`). The `mcp` arm (criterion 7): cwd `<wt>/python`; over MCP `project-select health`; then in fresh processes `next` (→ `next-cli.txt`), `next --project multiple-myeloma` (→ `next-project-mm.txt`), `projects` (→ `projects-after.txt`); then terminate.

- [ ] **Step 2: Run the arms**

Run: `<wt>/python/.venv/bin/python <task dir>/driver/arms.py <data root>/science.toml <task dir>`
Expected: `diff` of `workspace/` against `unrelated/` is empty for `status.txt`, `projects.txt`, `next.txt`; `next.txt` equals Task 5's `next-health.txt`; `mcp/next-cli.txt` equals `next-health.txt`; `mcp/next-project-mm.txt` equals `next-multiple-myeloma.txt`; `mcp/projects-after.txt` marks `health`.

- [ ] **Step 3: Note the arms** on the task with the three diffs' outcomes.

---

### Task 7: Complete the record, attach the evidence, file the findings

**Files:**
- Modify: `docs/records/2026-10-26-second-project-milestone.md` (§3–§7)
- Attach: `genesis.py`, `declare.py`, `walk.py`, `terms.py`, `selections.py`, `arms.py`, `science.toml`, `walk.jsonl`, `serve.stderr`, `epochs.json`, `selections.json`, `publish-preview.txt`

**Interfaces:**
- Consumes: every run artifact of Tasks 5–6, `declared.json`.

- [ ] **Step 1: Write §3 The path**: the recipes (genesis, declaration, selection read) quoted; the command table with step id, command, invocation id, minted address, seconds.

- [ ] **Step 2: Write §4 Predictions, marked** and each criterion's verdict (`met`, `partly met`, `unmet`) against §2, citing the artifact each mark reads.

- [ ] **Step 3: Write §5 Findings**: the §5.8 list plus anything the run raised, each with class and the task id it is filed under (Step 6).

- [ ] **Step 4: Write §6 Measurements** M1–M6 from `epochs.json`, `selections.json`, `walk.jsonl` and the stored relations (M5: list the stored-edge closure and the projection-derived closure of the five findings records, read from the record files under `<world>/corpora/mm30/`).

- [ ] **Step 5: Write §7 What this decides**: the fence (M3's three counts), the two notes to `beliefs`, the two proposed amendments (§8) with their evidence, and the health follow-up. Set the status line's commit sha to Task 4's commit.

- [ ] **Step 6: File the findings** (each `--origin agent`, body naming the record path and section; one task per finding): in `sci`: no corpus genesis command; no dataset declaration command; `spec` names one input; only a project can be previewed or published; no command renders a view's selection; the composite outside the coarse form and the §6.2 term-clause amendment (one task, `projects`); the health contract idea (`--status idea`). In `beliefs` (`tasks add --project beliefs …`): a relocated replica of the world's own corpus refused as a foreign publication; stored-edge closure narrower than the projection-derived rule; the `also:` key (idea). Then `tasks note beliefs-7c98bc "<M2 counts>"` and `tasks note beliefs-655c10 "<M1 coordination-only count and seconds>"`. Record each returned id in §5.

- [ ] **Step 7: Attach the evidence**: one `tasks attach sci-0d00d2 <file> --caption "<what it shows>"` per file listed above, from `<wt>`.

- [ ] **Step 8: Commit** (`just check` first):

```bash
git add docs/records/2026-10-26-second-project-milestone.md tasks/
git commit -m "docs(records): second-project milestone run, findings and measurements"
```

Then account for `<task dir>` under the retained-item rule in a task note (path, purpose, next owner, cleanup trigger, manifest hash), and `tasks done sci-0d00d2 "<one line: criteria met/partly/unmet, record path>"` once the branch is reviewed.
