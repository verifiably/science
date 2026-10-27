# Second-Project Milestone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the second-project milestone (projects design §9.2) against the live world root and leave its record, with one code change first: the launcher loads contract chains.

**Architecture:** Task 1 is the only change to `science`. Tasks 2–4 write the drivers under the task directory: genesis and declaration (kernel-level, before any server), the frozen queries, and the walk, selection reader and launcher arms, all sharing one journal-and-cleanup module. Task 5 rehearses every driver end to end on a disposable replica world built by the kernel's own replication route, so the first live mutation (Task 7) runs code that has already completed once. Task 6 commits the record's preflight and predictions between the rehearsal and the live run. Task 8 completes the record, attaches the evidence and files the findings.

**Tech Stack:** Python 3.13 under `uv` in `python/`; `beliefs` as an editable path dependency; pytest through `just test-one` / `just test-fast`; `science` run by explicit path `python/.venv/bin/science`.

**Spec:** `docs/specs/2026-10-26-second-project-milestone-design.md` (accepted at review round 2, revision 3 at `2c7a85c`). Section numbers below (§) are that document's unless prefixed "projects design". Revision 2 of this plan folds in plan review round 1 (P1 1, P2 4, Minor 1).

## Global Constraints

- Paths: `<data root>` is the directory `SCIENCE_CONFIG` names a file in (`/mnt/ssd/science` on this host); `<world>` is `<data root>/worlds/aec951bc6becacced13df8f7ae6f8abf`; `<task dir>` is `$WORK_ROOT/science/sci-0d00d2`; `<wt>` is this worktree, `.worktrees/second-project-milestone`; `<beliefs>` is the beliefs checkout beside this one. Committed text uses the placeholders, never the host paths (the docs hook refuses them).
- Run the worktree's `science` by explicit path, `<wt>/python/.venv/bin/science`, never a launcher on `PATH`; run driver scripts with `<wt>/python/.venv/bin/python`. Every driver takes the config path and the task directory as arguments and reads nothing from its cwd.
- No query address, digest or identity is authored by hand: each is read from a record, a held list, a reply, or computed from bytes, and the record prints where it came from.
- **Live-run contract (every driver that writes):** a fail-before-write check precedes each mint (the thing to be minted must not already exist); each returned identity is appended to `<run dir>/progress.json` before the next call; a restart reads the journal, verifies each recorded identity still resolves, skips those steps and continues; a server is always closed in `finally` (stdin closed, `wait(timeout=30)`, then `terminate()`, then `kill()`), and every read of its stdout is bounded (120 s, then the run aborts with the step named). No driver mutates the live world before Task 5's rehearsal has completed on the replica.
- Tests run through the recipes only: `just test-one <args>` for one test, `just test-fast` before each commit (run from `<wt>`). The worktree baseline (`just test`) runs once at execution's Setup, before Task 1.
- Conventional commits, no AI attribution. Task records: `tasks start <id>` before a task's first change, `tasks done <id> "<what landed>"` when its commit lands, both from `<wt>`.
- Nothing is held into the store, nothing is published, no corpus manifest is edited, the mm30 corpus is never re-admitted into the live world.
- Drivers, queries, rehearsal and run artifacts live under `<task dir>`; the directory is noted on the task when created (host, path, purpose, owner) and its kept files attached at the end (§4.3).

## Review Focus

Inputs the spec implies and no criterion exercises; each line's test is in the task that owns the code.

1. A chain whose `predecessors` are listed newest first: refuses by name (`no predecessor was supplied`), never `internal-error` (Task 1).
2. A successor document given as a bare path under `contracts`: refuses by name (Task 1).
3. A chain table whose `document` or `predecessors` key is missing or empty: refuses naming the key (Task 1).
4. A chain under `read_contracts`: the successor is available to mounts and not activated for the writer (Task 1).
5. A chain under `contracts` and the same chain under `read_contracts`: the existing both-lists refusal fires on identity (Task 1).

---

### Task 1: Contract chain entries in the launcher config (`sci-7079e3`)

**Files:**
- Modify: `python/src/science/contracts.py` (`load_contract_document`, lines 98–125)
- Modify: `python/src/science/config.py` (the string-only gates at lines 135–141 **and** the `local`/`readable` comprehensions at lines 178–179)
- Test: `python/tests/test_config.py`
- Modify: `docs/specs/2026-08-31-command-framework-design.md` §9.1 (dated amendment after the `read_contracts` amendment of 2026-09-30)
- Modify: `README.md` (the configuration paragraph, lines 53–57)

**Interfaces:**
- Produces: `science.contracts.load_contract_document(path: Path, base, *, predecessor: DomainContract | None = None) -> tuple[DomainContract, OperatorPlan | None]` (existing name, gains the keyword and catches `SuccessionViolation`).
- Produces: `science.contracts.load_contract_chain(document: Path, predecessors: Sequence[Path], base) -> tuple[DomainContract, OperatorPlan | None]`: parses `predecessors` oldest first, each the next one's predecessor, then `document`; refuses `invalid-input` naming the failing path and the kernel's message.
- Produces: `science.config.ScienceConfig` unchanged in shape; `available_contracts` and `plans` carry a chain's last contract. Task 2 consumes this through `load_config`.

- [ ] **Step 1: Write the failing tests** in `python/tests/test_config.py`, beside `test_contracts_compile_into_the_profile`, with one helper `_write_chain(tmp_path) -> tuple[Path, Path, str]`. The genesis `v1` is `test_contracts.DOCUMENT % ("0" * 64)`. The successor `v2` is the same text with `lineage: genesis` replaced by `lineage: {successor: "<v1 identity>"}` and one operator appended under `operators:` using only the declared `concept` sort: `regulates-concept-concept: {arity: 2, arg_sorts: [concept, concept], sign_apt: true, layers: [causal], dimensions: []}`, plus its plan row `{predicate: regulates, subject: concept, object: concept, operator: regulates-concept-concept}`. `<v1 identity>` is `parse_domain_contract(yaml.safe_load(v1_text)["contract"], source="v1", base=shipped_base_contract(), predecessor=None).content_identity`; the helper returns `expected` by parsing `v2` the same way with that contract as predecessor (never a literal).

```python
def test_a_contract_chain_compiles_to_the_successor_identity(tmp_path):
    v1, v2, expected = _write_chain(tmp_path)
    cfg = load_config(write_config(tmp_path, contracts=f'[{{ document = "{v2}", predecessors = ["{v1}"] }}]'))
    assert cfg.profile.activated_contracts["testing"] == expected
    (plan,) = cfg.plans
    assert plan.operator_for("regulates", "concept", "concept") == "testing/regulates-concept-concept"

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
    other.write_text(DOCUMENT % ("1" * 64))            # a different genesis of the same namespace
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

def test_the_same_chain_in_both_lists_refuses_on_identity(tmp_path):
    v1, v2, _ = _write_chain(tmp_path)
    refusal = assert_invalid_config(write_config(tmp_path, contracts=f'[{{ document = "{v2}", predecessors = ["{v1}"] }}]',
                                                 extra=f'read_contracts = [{{ document = "{v2}", predecessors = ["{v1}"] }}]\n'))
    assert "both contracts and read_contracts" in refusal.message
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_config.py -k "chain or successor"`
Expected: FAIL; the table cases with `config contracts must be a list of strings`, the bare-successor case with an uncaught `SuccessionViolation`.

- [ ] **Step 3: Implement the loader.** In `contracts.py`: add `predecessor` to `load_contract_document`, pass it to `parse_domain_contract`, and catch `SuccessionViolation` (from `beliefs.errors`) beside `MalformedContract`, refusing `f"contract document {path} does not parse: {caught}"`. Add `load_contract_chain` as the Interfaces block states, parsing each predecessor through `load_contract_document(path, base, predecessor=previous)` and discarding their plans. In `config.py`: replace the two `must be a list of strings` gates by one `_contract_entry_shape(raw: object, key: str) -> None` that accepts a list whose members are strings or dicts with exactly `document` (str) and `predecessors` (non-empty list of str), refusing `f"config {key} entry must be a path or a table with document and predecessors"` and naming a missing or empty key; replace the two comprehensions by `_contract_entries(raw, key, located, base) -> list[tuple[DomainContract, OperatorPlan | None]]` calling `load_contract_document` for a string and `load_contract_chain` for a table, every path through `located`.

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

Then `tasks done sci-7079e3 "contract chain entries in contracts/read_contracts; successor documents refuse by name"`, and dispatch an independent read-only review of this commit before Task 2 (the reviewer returns its findings in its final message; fix Critical and Important ones here).

---

### Task 2: Drivers: common module, genesis and declaration

**Files:**
- Create: `<task dir>/driver/common.py`, `<task dir>/driver/genesis.py`, `<task dir>/driver/declare.py` (not committed; attached in Task 8)

**Interfaces:**
- Consumes: Task 1's chain entry through `science.config.load_config`.
- Produces, in `common.py`: `AUTHORITY = Authority(WritePermit.full(), "sci-0d00d2-driver")`; `Journal(path: Path)` with `done(step: str) -> dict | None` and `record(step: str, **fields) -> None` (append-only JSON, written and fsynced before returning); `science_bin(wt: Path) -> Path`; `run_cli(config: Path, args: list[str], *, cwd: Path, timeout: float = 120) -> str` (stdout, raising with the step on non-zero exit).
- Produces, in `genesis.py`: `<data root>/contracts/mm30/{mm30-cut22,mm30-cut31,mm30}.yaml`, `<data root>/science.toml` exactly as §5.2 (relative paths), the working corpus admitted `fresh` and pinned to base `52a43993…`, biology `24bcec43…`, mm30 `4af7c421…`, coordination v2.
- Produces, in `declare.py`: `<task dir>/driver/declared.json` with keys `cohort`, `annotation` (dataset addresses), `cohort_resources`, `annotation_resources` (each `name, bytes, md5, sha256`), `condition_values` (`{"ndmm": "<diagnosis label>", "pd": "<relapse label>"}`). Tasks 3, 4, 5, 7 consume it.
- Both drivers take `<data root> <beliefs> <task dir>` (genesis) and `<config path> <task dir>` (declare), so Task 5 can point them at the replica.

- [ ] **Step 1: Create the task directory and note it.** `mkdir -p <task dir>/driver <task dir>/inputs <task dir>/queries <task dir>/runs <task dir>/rehearsal`, then `tasks note sci-0d00d2 "scratch: <host> <task dir> — drivers, frozen queries, downloaded inputs (discarded after digesting), rehearsal replica, run transcripts; owner this task"`.

- [ ] **Step 2: Write `common.py`** with the Interfaces above. `run_cli` sets the environment key by key (`PATH`, `HOME`, `SCIENCE_CONFIG`), never the inherited one.

- [ ] **Step 3: Write `genesis.py`** with:
  - `vocabulary_addresses(mm30_corpus: Path) -> dict[str, str]`: from `mm30_corpus/dataset/*.md`, the record titled `mm30 concept vocabulary` → `CONCEPTS`, `mm30 stage-level vocabulary` → `LEVELS`, `mm30 measure vocabulary` → `MEASURES`, `mm30 identification vocabulary` → `IDENTIFICATIONS`, each the record's `id` without `dataset:`; refuse unless all four are found once.
  - `concrete_documents(beliefs: Path, out: Path, addresses) -> list[Path]`: for `python/tools/reproduction/mm30-cut22.yaml`, `mm30-cut31.yaml`, `mm30.yaml`: read, drop the top-level `also:` line, replace the four `{{…}}` tokens, write to `out/<name>`; return oldest first. Fail before writing if `out` exists.
  - `pinned_identity(mm30_corpus: Path) -> str`: `profile.domains.mm30` of `corpus.yaml` without its prefix.
  - `write_config(data_root: Path, world_id: str) -> Path`: §5.2's TOML verbatim; fail before writing if the file exists.
  - `make_working_corpus(cfg, authority) -> str`: fail if `cfg.write_root` exists; `init_corpus_root`; `open_corpus(...).adopt_manifest(profile=CorpusPins(science_contract="science:"+cfg.profile.base_contract_identity, domains={ns: f"{ns}:{i}" for ns, i in cfg.profile.activated_contracts.items()}))`; `open_world(cfg.world, authority).admit(cfg.write_root, provenance=Fresh())`; return the corpus id read back from `cfg.write_root/corpus.yaml`.
  - `main`: addresses → documents → config → `cfg = load_config(config)` → assert `load_contract_chain(...)[0].content_identity == pinned_identity(...)` → `make_working_corpus` → print the chain identity, the pins and the working corpus id; journal each step in `<task dir>/driver/genesis-progress.json` so a rerun after a partial failure reports what exists and stops rather than re-creating.

- [ ] **Step 4: Write `declare.py`** with:
  - `fetch(url: str, into: Path, md5: str) -> Path`: `urllib.request` into `into/<basename>` (a fresh empty directory per file); refuse unless the md5 matches. Sources: `https://zenodo.org/records/22399365/files/mm_counts.csv.gz?download=1` → `e18dc9b72619d6473e2274cf3823b395`; `https://zenodo.org/records/22399365/files/mm_metadata.csv?download=1` → `9201e47ffb0e3900b01fd96a913b56f6`; `https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_36/gencode.v36.annotation.gtf.gz` → `c03931958d4572148650d62eb6dec41a`.
  - `resource(path: Path) -> dict`: `{"name": path.name, "digest": "sha256:" + sha256(bytes)}`.
  - `condition_values(metadata: Path) -> dict[str, str]`: the distinct `condition` strings; refuse unless they are exactly `{"diagnostico", "recidiva"}` (read from the published file on 2026-10-26: 30 rows each); return `{"ndmm": "diagnostico", "pd": "recidiva"}`.
  - `node(title, resources, locator, domain_facets=None)`: `stored.dataset_node(title=title, resources=resources, empirical_observation={"locator": locator, "attested_by": AUTHORITY.actor}, domain_facets=domain_facets)`.
  - Cohort: title `MMRF-CoMMpass teaching counts, 30 diagnosis and 30 relapse (Zenodo 22399365)`, resources `[counts, metadata]`, locator `doi:10.5281/zenodo.22399365`, `domain_facets={"biology/gene-axis": {"axis": "rows", "namespace": "Ensembl"}}` (the key is namespaced, as the mounted GSE179929 record's). Annotation: title `GENCODE release 36 primary annotation (gencode.v36.annotation.gtf.gz)`, one resource, locator the FTP URL, no domain facet.
  - `main`: build **both** nodes, validate both (`cfg.profile.document_violations(node)` empty, and `ctx.dataset_at(address) is None` for each through `ReadContext.open(cfg)`) before either write; then `open_corpus(cfg.write_root, authority=AUTHORITY, profile=cfg.profile).add(node)` each, journaling the address after each; write `declared.json`; delete `<task dir>/inputs/*`.

- [ ] **Step 5: Static check.** `<wt>/python/.venv/bin/python -m py_compile <task dir>/driver/*.py` exits 0. The drivers run for the first time in Task 5.

---

### Task 3: The frozen queries

**Files:**
- Create: `<task dir>/driver/terms.py`, `<task dir>/queries/{multiple-myeloma,cancer,health,multiple-myeloma-findings,evidence-bound-terms,health-question}.yaml`, `<task dir>/queries/MANIFEST` (sha256 per file)

**Interfaces:**
- Consumes: `declared.json` (Task 2 structure; the real values after Task 5's live declaration, see Step 3).
- Produces: `terms.py` with `concept_terms(store_root: Path) -> list[str]` (the held concept list's lines, in order, after asserting its sha256 is `c7e45f81…`, the mm30 record's P4), `write_queries(world: Path, declared: dict, out: Path) -> None`, and `PLACEHOLDER = "analysis-spec:<minted>"`. The six YAML files are what `project`/`question` receive; the walk substitutes exactly `PLACEHOLDER` in `health.yaml` and `health-question.yaml` with W1's spec address and records the substitution.

- [ ] **Step 1: Write `terms.py`.** `multiple-myeloma`: the closure clause, the spec `addresses` clause, then one `{"all": [{"references-term": term}]}` per line of `concept_terms`. `cancer`: identical bytes. `health`: the same plus `{"all": [{"addresses": ["proposition:concept-disease-stage-affects-protein-ezh2", PLACEHOLDER, declared["cohort"], declared["annotation"]]}]}`. `multiple-myeloma-findings` and `evidence-bound-terms`: §5.4 verbatim (`concept:disease-stage` read from the stage → PHF19 proposition record's `args`, not typed). `health-question`: the closure clause plus `health`'s extra `addresses` clause. The closure anchor and the spec address are read from `<world>/corpora/mm30/` records (`dataset:gse179929`'s id; the one `analysis-spec` record's id). Dump YAML with `sort_keys=False`; write `MANIFEST`.

- [ ] **Step 2: Generate against the rehearsal replica first** (Task 5 runs this) and **against the live world in Task 7**; both runs must produce byte-identical files except the two declared addresses, which the record states. Verify: `grep -c references-term <task dir>/queries/multiple-myeloma.yaml` prints 285; `diff multiple-myeloma.yaml cancer.yaml` is empty; `health.yaml` contains the four extra addresses.

---

### Task 4: Drivers: the walk, the selection reader, the launcher arms

**Files:**
- Create: `<task dir>/driver/walk.py`, `<task dir>/driver/selections.py`, `<task dir>/driver/arms.py`

**Interfaces:**
- Consumes: `common.py`, `declared.json`, the six query files, the config.
- Produces per run `<task dir>/runs/<timestamp>/`: `progress.json` (the journal: step → identity, invocation id, seconds), `walk.jsonl` (each MCP call: `step, call, arguments, result, seconds`), `serve.stderr`, `epochs.json` (`step, trigger, outcome, packaging_identity, seconds, writes_since_previous`), `selections.json` (per view: `address, revision, stored_query_sha256, frozen_query_sha256, equal, epoch, selected, contributing, absent, unresolved, complete`), `next-stale.txt`, `next-{multiple-myeloma,cancer,health,unselected}.txt`, `publish-preview.txt`, `belief.txt`, `status-final.txt`, and `arms/{workspace,unrelated,mcp}/…`.

- [ ] **Step 1: Write `selections.py`.** `read_view(cfg, address: str) -> dict`: resolve the minted record by its returned address (`resolve_one(ctx, parse_unpinned(address))`, `content_of(tip)`), take its stored `query`, hash its canonical YAML, compare with the frozen file's hash; `world = open_world(cfg.world, authority=<a read authority with no write permit, as world_belief's EPOCH_AUTHORITY is built>)`; `published = current_epoch(world)`; `selection = evaluate_query(open_world_view(world, published), parse_view_query(stored_query))`; return the `selections.json` row with `selection.selected`, `contributing`, `absent`, `unresolved` (as their projection), `complete`, and `published.packaging_identity`. Never evaluates a query that was not read back from a record.

- [ ] **Step 2: Write `walk.py`** from the mm30 walk's pattern, under the live-run contract: `Server(cfg, cwd, run_dir)` context manager (Popen of `science mcp serve --config`, `finally` cleanup as the contract says); `call(step, name, arguments) -> dict` with a bounded `readline` (a reader thread and `queue.get(timeout=120)`), timing, journaling the returned address (parsed from the reply's record block) under `step`; `epoch(step, trigger, writes)` running `science epoch` through `run_cli`, parsing `built:`/`current:` and the packaging identity from the first line; `before_mint(step)` fail-before-write checks: for W2, `projects` must list none of the four names; for W3's questions, `project-show` under the selected project must list no question of that name; for W1, `claim`'s slug must not resolve (the reply of a duplicate is a refusal, which the journal would then record as the step's failure). Resume: on start, if `progress.json` exists, each journaled step is verified (its address resolves through `selections.read_view` for views, or `project-show`/`status` for the others) and skipped. The schedule, nothing else between steps: `S0 status` → `E1 epoch(initial, [declarations])` → `W1 claim` (§5.5 step 2) and `spec` (§5.5 step 3; `dataset` = `declared["cohort"]`, method text naming `declared["annotation"]`) → substitute `PLACEHOLDER` in `health.yaml` and `health-question.yaml` with the spec address, journaling both hashes → `E2 epoch(evidence, [claim, spec])` → `W2 project ×4` in the order `multiple-myeloma`, `cancer`, `health`, `multiple-myeloma-findings` → `next` saved as `next-stale.txt` → `E3 epoch(coordination-only, [project×4])` → `R1 read_view` for the four projects → `W3 project-select health; question` (`health-question.yaml`, name `Does disease stage drive the PRC2 catalytic core (EZH2) where it drives PHF19?`) `; project-select cancer; reuse --source <the question's address>; project-select multiple-myeloma; question` (`evidence-bound-terms.yaml`, name `evidence-bound terms`) → `E4 epoch(coordination-only, [question, reuse, question])` → `E5 epoch(none, [])` → `R2 next` under each project (`project-select` then `next`) and after `project-select --clear` → `R3 read_view` of the two questions and the reuse → `R4 publish-preview --target multiple-myeloma-findings --to <run dir>/publish` saved verbatim (its refusal is expected and journaled as the step's result, not a failure) → `R5 belief --proposition proposition:concept-disease-stage-affects-protein-phf19` → `status` saved as `status-final.txt`.

- [ ] **Step 3: Write `arms.py`.** `arm(name, cwd, run_dir)`: a `Server` with that `cwd`; over MCP `project-select {"target": "health"}`; then `run_cli` `status`, `projects`, `next` with the same `cwd`, saved; server closed by the context manager. The `workspace` arm's cwd is the mm program's workspace checkout; the `unrelated` arm's is `tempfile.mkdtemp()` holding `science.toml` (`world_root = "/nowhere"`), `science.yaml` (`project: decoy`) and `corpus.yaml` (`corpus: decoy`). The `mcp` arm: cwd `<wt>/python`; over MCP `project-select health`; then fresh-process `next` (→ `next-cli.txt`), `next --project multiple-myeloma` (→ `next-project-mm.txt`), `projects` (→ `projects-after.txt`). `compare(run_dir) -> dict`, written to `arms/compare.json`: (a) `workspace/` against `unrelated/` for `status.txt`, `projects.txt`, `next.txt`, all byte-equal; (b) both arms' `next.txt` equal to the walk's `next-health.txt`; (c) `mcp/next-cli.txt` equal to `next-health.txt`, `mcp/next-project-mm.txt` equal to `next-multiple-myeloma.txt`, and `mcp/projects-after.txt` marking `health` as selected.

- [ ] **Step 4: Static check.** `py_compile` all drivers exits 0; `python -c "import walk, selections, arms"` from `<task dir>/driver` with the worktree's interpreter exits 0.

---

### Task 5: Rehearsal on a disposable replica

**Files:**
- Create: `<task dir>/driver/rehearsal.py`, `<task dir>/rehearsal/<rehearsal world id>/…`, `<task dir>/rehearsal/science.toml`, `<task dir>/rehearsal/contracts/…`, `<task dir>/runs/rehearsal-<timestamp>/`

**Interfaces:**
- Consumes: every driver of Tasks 2–4, `<world>/anchors/*.head`, `<world>/corpora/mm30`, `<world>/store`.
- Produces: a replica world under `<task dir>/rehearsal/`, and one complete run of genesis → declare → terms → walk → arms against it.

- [ ] **Step 1: Write `rehearsal.py`** on `<beliefs>/python/tools/reproduction/relocate.py`'s recipe, with the live world as the source: `home = <task dir>/rehearsal/worlds/<secrets.token_hex(16)>`; copy the two head artifacts from `<world>/anchors/`; `replicate_root(<world>/corpora/mm30, home/corpora/mm30, authority=AUTHORITY)` then `restore_root(..., CorpusSubject(corpus_id), ObserverSet((ArtifactCarrier.from_bytes(corpus_head),)), authority=AUTHORITY)` and the same for the store with `StoreSubject(store_id)`; `init_world_root(WorldConfig(home/"world", world_id, (home/"corpora"/"mm30",)), authority=AUTHORITY)`; `admit_arrival(open_world(...), corpus_root, ReplicaOf(corpus_id), ObserverSet(...))`; refuse unless both restores and the arrival answer `validated`. Then run, in order, `genesis.py <task dir>/rehearsal <beliefs> <task dir>` (its config lands at `<task dir>/rehearsal/science.toml`), `declare.py`, `terms.py`, `walk.py`, `arms.py`, each against that config, run directory `<task dir>/runs/rehearsal-<timestamp>/`.

- [ ] **Step 2: Run the rehearsal**

Run: `<wt>/python/.venv/bin/python <task dir>/driver/rehearsal.py <wt> <beliefs> <task dir>`
Expected: every MCP call `ok` except R4 `REFUSED` with `attribution-contract-unpinned`; `epochs.json` outcomes `built, built, built, built, current`; `next-stale.txt` carries `epoch-stale`; the four `next-*.txt` equal §5.6's R2 text; `selections.json` has `equal: true` and `complete: true` for every view, with the R1 sets of §5.6; `arms/compare.json` all equal. Any other refusal or mismatch is noted on the task with its text, filed (§5.8) where it is a finding, and fixed in the driver where it is the driver's; then the rehearsal reruns from a fresh replica (`rm -rf <task dir>/rehearsal` first) until it completes as expected.

- [ ] **Step 3: Exercise the recovery path once.** Rerun `walk.py` against the completed rehearsal run directory: it must report every step as journaled and resolved, mint nothing, and exit 0; `status-final.txt` is unchanged. Then run `walk.py` with a fresh run directory against the same replica: it must refuse at `before_mint(W2)` naming `multiple-myeloma` as existing, before any write. Record both outcomes on the task.

- [ ] **Step 4: Note the rehearsal** on the task: replica world id, run directory, the five epoch seconds, and that the live drivers are the files just exercised (their sha256s).

---

### Task 6: The record's preflight and predictions, committed before the live run

**Files:**
- Create: `docs/records/2026-10-26-second-project-milestone.md` (§1 and §2 only)

**Interfaces:**
- Consumes: Task 5's rehearsal artifacts (the queries' hashes, the rehearsal's `declared.json` resource digests, the two `condition` labels).
- Produces: the committed schedule and predictions the live run is marked against; Task 7 copies the step ids into its journal.

- [ ] **Step 1: Write §1 Preflight**: the mm30 record's shape (date, status line reading "predictions committed before the live run (`<sha>`)", scope). Contents: C1–C8 as observed on the live world (no working corpus yet; the pinned mm30 identity and the chain identity equal; the 18 records), the beliefs and science commits (`git -C <beliefs> rev-parse --short HEAD`, `git rev-parse --short HEAD`), the rehearsal's outcome in one paragraph (replica world id, every step as expected, recovery path exercised), the three inputs' md5 and sha256 digests and the two `condition` labels from the rehearsal download, and §5.1's reading-pass outputs (the overlap inventory `depmap`, `tcga`; GTEx `health/meta`'s only; the first health question's wording; the two datasets it needs held).

- [ ] **Step 2: Write §2 Schedule and predictions**: §5.6's table verbatim with the step ids of Task 4's schedule; the six frozen queries by hash with `multiple-myeloma.yaml` quoted in full (285 term clauses, the held list's sha256 `c7e45f81…` beside it) and the others by their differing clauses; the predicted `next` renderings as exact text; the predicted refusal text for R4; the predicted `selections.json` sets; the criterion verdicts predicted (`met` for 1, 2, 6, 7; `partly met` for 3, 4; `unmet` for 5). State that the live declared addresses will differ from the rehearsal's only if the downloaded bytes differ, which would itself be a finding.

- [ ] **Step 3: Commit** (`just check` first):

```bash
git add docs/records/2026-10-26-second-project-milestone.md
git commit -m "docs(records): second-project milestone preflight and predictions"
```

---

### Task 7: The live run

**Files:**
- Create: `<data root>/contracts/mm30/…`, `<data root>/science.toml`, `<world>/corpora/working/`, `<world>/ops/`, `<task dir>/runs/live-<timestamp>/`

**Interfaces:**
- Consumes: the drivers exactly as rehearsed (compare their sha256s with Task 5's note before running), the committed record.
- Produces: the live working corpus with its records, and the run directory Task 8 reads.

- [ ] **Step 1: Genesis.** Run `genesis.py <data root> <beliefs> <task dir>`. Expected: the chain identity line, the four pins, the working corpus id. Then `SCIENCE_CONFIG=<data root>/science.toml <wt>/python/.venv/bin/science status` saved as `<run dir>/preflight-status.txt`: two corpora `known=True live=True present=True`, 18 records in mm30, none in the working corpus, `No current epoch.` Note the corpus id and pins on the task.

- [ ] **Step 2: Declare.** Run `declare.py <data root>/science.toml <task dir>`. Expected: two addresses equal to the rehearsal's; `declared.json` rewritten; `<task dir>/inputs/` empty; `status` shows `dataset 2` in the working corpus and no holdings observation.

- [ ] **Step 3: Freeze the live queries.** Run `terms.py` against the live world; `diff -r` against the rehearsal's `queries/` shows differences only in the two declared addresses (none expected); `MANIFEST` rewritten.

- [ ] **Step 4: The walk and the arms.** Run `walk.py <data root>/science.toml <task dir>` then `arms.py <data root>/science.toml <task dir>` with run directory `<task dir>/runs/live-<timestamp>/`. Expected: as Task 5 Step 2. If the walk stops, follow the live-run contract: note the step and the refusal text on the task, file it, and resume from the journal; never rerun genesis or the declarations.

- [ ] **Step 5: Note the run** on the task: run directory, refusals (expected R4 only, or the list), the five epoch outcomes with seconds, `arms/compare.json`.

---

### Task 8: Complete the record, attach the evidence, file the findings

**Files:**
- Modify: `docs/records/2026-10-26-second-project-milestone.md` (§3–§7)
- Attach to `sci-0d00d2`: `common.py`, `genesis.py`, `declare.py`, `terms.py`, `walk.py`, `selections.py`, `arms.py`, `rehearsal.py`, `science.toml` (the live one), `declared.json`, every file under `<task dir>/queries/`, and from the live run directory `progress.json`, `walk.jsonl`, `serve.stderr`, `epochs.json`, `selections.json`, `next-stale.txt`, the four `next-*.txt`, `publish-preview.txt`, `belief.txt`, `status-final.txt`, `preflight-status.txt`, and every file under `arms/`.

**Interfaces:**
- Consumes: every artifact of Task 7, the committed §1–§2.

- [ ] **Step 1: Write §3 The path**: the recipes (genesis, declaration, selection read, rehearsal replication) quoted; the command table with step id, command, invocation id, minted address, seconds; the `PLACEHOLDER` substitution with both hashes.

- [ ] **Step 2: Write §4 Predictions, marked** and each criterion's verdict (`met`, `partly met`, `unmet`) against §2, citing the artifact each mark reads; `selections.json`'s `equal` and `complete` columns reported per view.

- [ ] **Step 3: Write §5 Findings**: the §5.8 list plus anything the rehearsal or the run raised, each with class and the task id it is filed under (Step 6).

- [ ] **Step 4: Write §6 Measurements** M1–M6 from `epochs.json`, `selections.json`, `walk.jsonl` and the stored relations (M5: the stored-edge closure and the projection-derived closure of the five findings records, read from the record files under `<world>/corpora/mm30/`).

- [ ] **Step 5: Write §7 What this decides**: the fence (M3's three counts), the two notes to `beliefs`, the two proposed amendments (§8) with their evidence, and the health follow-up. Set the status line's commit sha to Task 6's commit.

- [ ] **Step 6: File the findings** (each `--origin agent`, body naming the record path and section; one task per finding): in `sci`: no corpus genesis command; no dataset declaration command; `spec` names one input; only a project can be previewed or published; no command renders a view's selection; the composite outside the coarse form and the §6.2 term-clause amendment (one task, tag `projects`); the health contract idea (`--status idea`). In `beliefs` (`tasks add --project beliefs …`): a relocated replica of the world's own corpus refused as a foreign publication; stored-edge closure narrower than the projection-derived rule; the `also:` key (idea). Then `tasks note beliefs-7c98bc "<M2 counts>"` and `tasks note beliefs-655c10 "<M1 coordination-only count and seconds>"`. Record each returned id in §5.

- [ ] **Step 7: Attach the evidence**: one `tasks attach sci-0d00d2 <file> --caption "<what it shows>"` per file listed above, from `<wt>`. Then `rm -rf <task dir>/rehearsal` (its findings, if any, are in §5 with their text) and write the retained-item note for what stays under `<task dir>` (path, purpose: the run directories; next owner: the health program's first task; cleanup trigger: that task's start or 90 days; a manifest of sha256s and its hash).

- [ ] **Step 8: Commit** (`just check` first):

```bash
git add docs/records/2026-10-26-second-project-milestone.md tasks/
git commit -m "docs(records): second-project milestone run, findings and measurements"
```

Then `tasks done sci-0d00d2 "<one line: criteria met/partly/unmet, record path>"` once the branch's final review is in.
