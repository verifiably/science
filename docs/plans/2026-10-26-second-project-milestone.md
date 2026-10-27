# Second-Project Milestone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the second-project milestone (projects design §9.2) against the live world root and leave its record, with one code change first: the launcher loads contract chains.

**Architecture:** Task 1 is the only change to `science`. Tasks 2–4 write the drivers under the task directory: shared code only, with every mutable thing (journals, declarations, frozen queries, outputs) in a per-attempt state directory bound to one world. Task 5 rehearses every driver end to end on disposable replica worlds built by the kernel's own replication route, and drills the three recovery cases, so the first live mutation (Task 7) runs code that has already completed and recovered once. Task 6 commits the record's preflight and predictions between the rehearsal and the live run. Task 8 completes the record, attaches the evidence and files the findings.

**Tech Stack:** Python 3.13 under `uv` in `python/`; `beliefs` as an editable path dependency; pytest through `just test-one` / `just test-fast`; `science` run by explicit path `python/.venv/bin/science`.

**Spec:** `docs/specs/2026-10-26-second-project-milestone-design.md` (accepted at review round 2, revision 3 at `2c7a85c`). Section numbers below (§) are that document's unless prefixed "projects design". Revision 3 of this plan folds in plan review rounds 1 (P1 1, P2 4, Minor 1) and 2 (P1 2, P2 1).

## Global Constraints

- Paths: `<data root>` is the directory `SCIENCE_CONFIG` names a file in (`/mnt/ssd/science` on this host); `<world>` is `<data root>/worlds/aec951bc6becacced13df8f7ae6f8abf`; `<task dir>` is `$WORK_ROOT/science/sci-0d00d2`; `<wt>` is this worktree, `.worktrees/second-project-milestone`; `<beliefs>` is the beliefs checkout beside this one. Committed text uses the placeholders, never the host paths (the docs hook refuses them).
- **Task directory layout.** `<task dir>/driver/` holds shared code and nothing mutable. Every attempt has its own state directory `<state>` = `<task dir>/state/<name>/` (`rehearsal-1`, `rehearsal-2`, …, `live`), holding `world.json` (`world_id`, `config` path, `data_root`, created at), `genesis-progress.json`, `declared.json`, `queries/` (the frozen templates and `MANIFEST`), and `runs/<timestamp>/` (the journal `progress.json`, `queries-resolved/`, every output). Every driver takes `<state>` as its argument and reads the config path from `world.json`; a driver given a `<state>` whose `world.json` names another world than the config's refuses before doing anything. Replica worlds live under `<task dir>/rehearsal/<name>/`; downloads under `<task dir>/inputs/<state name>/<file>/`, each file in its own empty directory, discarded after digesting.
- Run the worktree's `science` by explicit path, `<wt>/python/.venv/bin/science`, never a launcher on `PATH`; run driver scripts with `<wt>/python/.venv/bin/python`. Drivers read nothing from their cwd.
- No query address, digest or identity is authored by hand: each is read from a record, a held list, a reply, or computed from bytes, and the record prints where it came from.
- **Live-run contract (every driver that writes):**
  - every mutation has a unique journal key (Task 4 lists them) and is journaled in two phases: `attempt(key)` is written and fsynced before the call, `record(key, identity, …)` after the reply;
  - a fail-before-write check precedes each mint: the thing to be minted must not already exist (by exact identity or name, never by a count);
  - a restart reads the journal; a `recorded` key is verified by resolving its identity and comparing content (Task 4 says what is compared per key) and then skipped; an `attempted` key with no record is an uncertain write: the driver stops with exit status 3, prints the key and the exact check to run, and continues only after `--reconcile KEY=IDENTITY` (the identity the person found, or `KEY=none` when the check shows nothing was minted) is journaled;
  - before the first unjournaled step after a restart, the driver re-issues the most recent journaled selection (`project-select <target>` or `--clear`) on the new server, so session state is restored before any mint;
  - a server is always closed in `finally` (stdin closed, `wait(timeout=30)`, then `terminate()`, then `kill()`), and every read of its stdout is bounded (120 s, then the run aborts naming the step);
  - no driver mutates the live world before Task 5's rehearsal and drills have completed on replicas.
- Tests run through the recipes only: `just test-one <args>` for one test, `just test-fast` before each commit (run from `<wt>`). The worktree baseline (`just test`) runs once at execution's Setup, before Task 1.
- Conventional commits, no AI attribution. Task records: `tasks start <id>` before a task's first change, `tasks done <id> "<what landed>"` when its commit lands, both from `<wt>`.
- Nothing is held into the store, nothing is published, no corpus manifest is edited, the mm30 corpus is never re-admitted into the live world.
- The task directory is noted on the task when created (host, path, purpose, owner) and its kept files attached at the end (§4.3).

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
- Produces, in `common.py`: `AUTHORITY = Authority(WritePermit.full(), "sci-0d00d2-driver")`; `State(path: Path)` with `.world` (the parsed `world.json`), `.config` (its config path), `.declared`, `.queries`, `.runs`, and `State.create(path, *, world_id, data_root, config) -> State` (refuses if `world.json` exists); `Journal(path: Path, *, world_id: str, config: Path)` whose file header binds it to that world and config and whose rows are `{"key", "phase": "attempt"|"record"|"reconcile", "at", "identity", "invocation_id", "seconds"}` written and fsynced per row, with `attempt(key)`, `record(key, **fields)`, `status(key) -> "recorded"|"attempted"|"reconciled"|None`, `identity(key)`, `last_selection() -> str | None`; `science_bin(wt: Path) -> Path`; `run_cli(config: Path, args: list[str], *, cwd: Path, timeout: float = 120) -> str` (stdout, raising with the step on non-zero exit, environment built key by key: `PATH`, `HOME`, `SCIENCE_CONFIG`).
- Produces, in `genesis.py <state> <data root> <world id> <beliefs> <mm30 corpus>`: `<data root>/contracts/mm30/{mm30-cut22,mm30-cut31,mm30}.yaml`, `<data root>/science.toml` as §5.2 with the given world id (relative paths), the working corpus admitted `fresh` and pinned to base `52a43993…`, biology `24bcec43…`, mm30 `4af7c421…`, coordination v2; `<state>/world.json` written first and `<state>/genesis-progress.json` per step.
- Produces, in `declare.py <state>`: `<state>/declared.json` with keys `cohort`, `annotation` (dataset addresses), `cohort_resources`, `annotation_resources` (each `name, bytes, md5, sha256`), `condition_values` (`{"ndmm": "diagnostico", "pd": "recidiva"}`). Tasks 3, 4, 5, 7 consume it.

- [ ] **Step 1: Create the task directory and note it.** `mkdir -p <task dir>/driver <task dir>/state <task dir>/inputs <task dir>/rehearsal`, then `tasks note sci-0d00d2 "scratch: <host> <task dir> — shared drivers, per-attempt state (journals, declarations, frozen queries, run outputs), downloaded inputs (discarded after digesting), rehearsal replicas; owner this task"`.

- [ ] **Step 2: Write `common.py`** with the Interfaces above.

- [ ] **Step 3: Write `genesis.py`** with:
  - `vocabulary_addresses(mm30_corpus: Path) -> dict[str, str]`: from `mm30_corpus/dataset/*.md`, the record titled `mm30 concept vocabulary` → `CONCEPTS`, `mm30 stage-level vocabulary` → `LEVELS`, `mm30 measure vocabulary` → `MEASURES`, `mm30 identification vocabulary` → `IDENTIFICATIONS`, each the record's `id` without `dataset:`; refuse unless all four are found once.
  - `concrete_documents(beliefs: Path, out: Path, addresses) -> list[Path]`: for `python/tools/reproduction/mm30-cut22.yaml`, `mm30-cut31.yaml`, `mm30.yaml`: read, drop the top-level `also:` line, replace the four `{{…}}` tokens, write to `out/<name>`; return oldest first. Fail before writing if `out` exists.
  - `pinned_identity(mm30_corpus: Path) -> str`: `profile.domains.mm30` of `corpus.yaml` without its prefix.
  - `write_config(data_root: Path, world_id: str) -> Path`: §5.2's TOML verbatim with `world_id` substituted; fail before writing if the file exists.
  - `make_working_corpus(cfg, authority) -> str`: fail if `cfg.write_root` exists; `init_corpus_root`; `open_corpus(...).adopt_manifest(profile=CorpusPins(science_contract="science:"+cfg.profile.base_contract_identity, domains={ns: f"{ns}:{i}" for ns, i in cfg.profile.activated_contracts.items()}))`; `open_world(cfg.world, authority).admit(cfg.write_root, provenance=Fresh())`; return the corpus id read back from `cfg.write_root/corpus.yaml`.
  - `main`: `State.create` → addresses → documents → config → `cfg = load_config(config)` → assert `cfg.world.world_id == <world id>` and `load_contract_chain(...)[0].content_identity == pinned_identity(...)` → `make_working_corpus` → print the chain identity, the pins and the working corpus id; each step journaled in `genesis-progress.json` (bound to the world id) so a rerun reports what exists and stops rather than re-creating.

- [ ] **Step 4: Write `declare.py`** with:
  - `fetch(url: str, into: Path, md5: str) -> Path`: `urllib.request` into `into/<basename>` (a fresh empty directory per file); refuse unless the md5 matches. Sources: `https://zenodo.org/records/22399365/files/mm_counts.csv.gz?download=1` → `e18dc9b72619d6473e2274cf3823b395`; `https://zenodo.org/records/22399365/files/mm_metadata.csv?download=1` → `9201e47ffb0e3900b01fd96a913b56f6`; `https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_36/gencode.v36.annotation.gtf.gz` → `c03931958d4572148650d62eb6dec41a`.
  - `resource(path: Path) -> dict`: `{"name": path.name, "digest": "sha256:" + sha256(bytes)}`.
  - `condition_values(metadata: Path) -> dict[str, str]`: the distinct `condition` strings; refuse unless they are exactly `{"diagnostico", "recidiva"}` (read from the published file on 2026-10-26: 30 rows each); return `{"ndmm": "diagnostico", "pd": "recidiva"}`.
  - `node(title, resources, locator, domain_facets=None)`: `stored.dataset_node(title=title, resources=resources, empirical_observation={"locator": locator, "attested_by": AUTHORITY.actor}, domain_facets=domain_facets)`.
  - Cohort: title `MMRF-CoMMpass teaching counts, 30 diagnosis and 30 relapse (Zenodo 22399365)`, resources `[counts, metadata]`, locator `doi:10.5281/zenodo.22399365`, `domain_facets={"biology/gene-axis": {"axis": "rows", "namespace": "Ensembl"}}` (the key is namespaced, as the mounted GSE179929 record's). Annotation: title `GENCODE release 36 primary annotation (gencode.v36.annotation.gtf.gz)`, one resource, locator the FTP URL, no domain facet.
  - `main`: refuse if `<state>/declared.json` exists; build **both** nodes, validate both (`cfg.profile.document_violations(node)` empty, and `ctx.dataset_at(address) is None` for each through `ReadContext.open(cfg)`) before either write; then `open_corpus(cfg.write_root, authority=AUTHORITY, profile=cfg.profile).add(node)` each, journaling the address in `<state>/declare-progress.json` after each; write `declared.json`; delete `<task dir>/inputs/<state name>/`.

- [ ] **Step 5: Static check.** `<wt>/python/.venv/bin/python -m py_compile <task dir>/driver/*.py` exits 0. The drivers run for the first time in Task 5.

---

### Task 3: The frozen queries

**Files:**
- Create: `<task dir>/driver/terms.py`; per state `<state>/queries/{multiple-myeloma,cancer,health,multiple-myeloma-findings,evidence-bound-terms,health-question}.yaml` and `<state>/queries/MANIFEST` (sha256 per file)

**Interfaces:**
- Consumes: `<state>/declared.json`, `<state>/world.json`.
- Produces: `terms.py <state>` with `concept_terms(store_root: Path) -> list[str]` (the held concept list's lines, in order, after asserting its sha256 is `c7e45f81…`, the mm30 record's P4), `write_queries(state: State) -> None` (refuses if `<state>/queries/` exists: the templates are written once per state and never rewritten), and `PLACEHOLDER = "analysis-spec:<minted>"`. The six YAML files are immutable templates; the walk writes substituted copies under `<run dir>/queries-resolved/` and never edits them.

- [ ] **Step 1: Write `terms.py`.** `multiple-myeloma`: the closure clause, the spec `addresses` clause, then one `{"all": [{"references-term": term}]}` per line of `concept_terms`. `cancer`: identical bytes. `health`: the same plus `{"all": [{"addresses": ["proposition:concept-disease-stage-affects-protein-ezh2", PLACEHOLDER, declared["cohort"], declared["annotation"]]}]}`. `multiple-myeloma-findings` and `evidence-bound-terms`: §5.4 verbatim (`concept:disease-stage` read from the stage → PHF19 proposition record's `args`, not typed). `health-question`: the closure clause plus `health`'s extra `addresses` clause. The closure anchor and the spec address are read from the mm30 corpus records (`dataset:gse179929`'s id; the one `analysis-spec` record's id). Dump YAML with `sort_keys=False`; write `MANIFEST`.

- [ ] **Step 2: Verify on first use** (Task 5 runs it per rehearsal state; Task 7 for `live`): `grep -c references-term <state>/queries/multiple-myeloma.yaml` prints 285; `diff multiple-myeloma.yaml cancer.yaml` is empty; `health.yaml` contains the four extra addresses; the `MANIFEST`s of two states differ only in `health.yaml` and `health-question.yaml` when their declared addresses differ, else not at all.

---

### Task 4: Drivers: the walk, the selection reader, the launcher arms

**Files:**
- Create: `<task dir>/driver/walk.py`, `<task dir>/driver/selections.py`, `<task dir>/driver/arms.py`

**Interfaces:**
- Consumes: `common.py`, `<state>/declared.json`, `<state>/queries/`, the config from `world.json`.
- Produces per run `<run dir>` = `<state>/runs/<timestamp>/`: `progress.json` (the two-phase journal), `queries-resolved/` (the substituted copies, with `MANIFEST`), `walk.jsonl` (each MCP call: `key, call, arguments, result, seconds`), `serve.stderr`, `epochs.json` (`key, trigger, outcome, packaging_identity, seconds, writes_since_previous`), `selections.json` (per view: `key, address, revision, raw_input_sha256, input_projection_sha256, stored_projection_sha256, equivalent, epoch, selected, contributing, absent, unresolved, complete`), `next-stale.txt`, `next-{multiple-myeloma,cancer,health,unselected}.txt`, `publish-preview.txt`, `belief.txt`, `status-final.txt`, and `arms/{workspace,unrelated,mcp}/…` plus `arms/compare.json`.
- Journal keys, in schedule order: `S0`, `E1`, `W1.claim`, `W1.spec`, `E2`, `W2.project.multiple-myeloma`, `W2.project.cancer`, `W2.project.health`, `W2.project.multiple-myeloma-findings`, `R0.next-stale`, `E3`, `R1.<view>` ×4, `W3.select.health`, `W3.question.health`, `W3.select.cancer`, `W3.reuse`, `W3.select.multiple-myeloma`, `W3.question.evidence-bound-terms`, `E4`, `E5`, `R2.<view|unselected>` ×4 (each a `select` then a `next`, journaled as one read), `R3.<question|reuse>` ×3, `R4`, `R5`, `S1`. Only `W*` keys mutate the corpus; `select` keys write a ledger line and are re-issued on resume, never skipped.

- [ ] **Step 1: Write `selections.py`.** `projection_sha256(query: dict) -> str`: `sha256(json.dumps(parse_view_query(query).projection(), sort_keys=True, separators=(",", ":")))`, the serialization `science.coordination.query_digest` uses. `read_view(cfg, key, address: str, input_path: Path) -> dict`: resolve the minted record by its returned address (`resolve_one(ctx, parse_unpinned(address))`, `content_of(tip)`), compute `stored_projection_sha256 = query_digest(tip)` and `input_projection_sha256 = projection_sha256(yaml.safe_load(input_path.read_text()))`, `equivalent = (they are equal)`, and `raw_input_sha256` of the file bytes for artifact integrity; `world = open_world(cfg.world, authority=<a read authority with no write permit, as world_belief's EPOCH_AUTHORITY is built>)`; `published = current_epoch(world)`; `selection = evaluate_query(open_world_view(world, published), stored_query(tip))`; return the `selections.json` row with `selection.selected`, `contributing`, `absent`, `unresolved` (as their projection), `complete`, and `published.packaging_identity`. Never evaluates a query that was not read back from a record.

- [ ] **Step 2: Write `walk.py`** from the mm30 walk's pattern, under the live-run contract: `Server(cfg, cwd, run_dir)` context manager (Popen of `science mcp serve --config`, `finally` cleanup as the contract says); `call(key, name, arguments) -> dict` with a bounded `readline` (a reader thread and `queue.get(timeout=120)`), timing, and for a `W*` key `journal.attempt(key)` before the frame is written and `journal.record(key, identity=<the address parsed from the reply's record block>, invocation_id=…)` after; `epoch(key, trigger, writes)` running `science epoch` through `run_cli`, parsing `built:`/`current:` and the packaging identity from the first line; `select(key, target | None)` journaled as a `select` row. Fail-before-write checks, each before its `attempt`: `W1.claim`: `claim`'s slug `concept-disease-stage-affects-protein-ezh2` must not resolve in the write view; `W1.spec`: no `analysis-spec` in the write view targets that proposition; `W2.project.<name>`: `projects` lists no project of that name; `W3.question.<name>` and `W3.reuse`: `project-show` under the selected project lists no question of that name (the reuse's name is the source's). **Resume** (`progress.json` exists): verify every `recorded` `W*` key by exact content: `W1.claim` → the proposition resolves with operator `mm30/affects-concept-molecular-entity` and args `[concept:disease-stage, protein:EZH2]`; `W1.spec` → the address resolves, its target is the proposition and its `observes` input is `declared["cohort"]`; `W2.*`, `W3.question.*`, `W3.reuse` → `selections.read_view` reports `equivalent: true` against the resolved input in `queries-resolved/`; an `attempted` key without a record → exit 3 printing `uncertain write <key>: run <check> and rerun with --reconcile <key>=<identity|none>` where `<check>` is the fail-before-write check's command for that key; then re-issue `journal.last_selection()` (a `select` row's target, or `--clear`) on the new server, and continue from the first unjournaled key. `--reconcile KEY=VALUE` journals a `reconcile` row and exits 0. Test hooks, honoured only when given: `--stop-after KEY` (exit 0 right after that key is journaled, server closed), `--crash-before-record KEY` (send the frame, read the reply, write nothing, exit 1, server closed). **The schedule**, nothing else between steps: `S0 status` → `E1 epoch(initial, [declarations])` → `W1.claim` (§5.5 step 2) and `W1.spec` (§5.5 step 3; `dataset` = `declared["cohort"]`, method text naming `declared["annotation"]`) → write `queries-resolved/` by copying `<state>/queries/` and replacing `PLACEHOLDER` in `health.yaml` and `health-question.yaml` with the spec address (journaled with both files' raw and projection hashes) → `E2 epoch(evidence, [claim, spec])` → `W2.project.*` ×4 in the order `multiple-myeloma`, `cancer`, `health`, `multiple-myeloma-findings` → `R0 next` saved as `next-stale.txt` → `E3 epoch(coordination-only, [project×4])` → `R1 read_view` ×4 → `W3.select.health`, `W3.question.health` (`health-question.yaml`, name `Does disease stage drive the PRC2 catalytic core (EZH2) where it drives PHF19?`), `W3.select.cancer`, `W3.reuse` (`--source` the question's address), `W3.select.multiple-myeloma`, `W3.question.evidence-bound-terms` (`evidence-bound-terms.yaml`, name `evidence-bound terms`) → `E4 epoch(coordination-only, [question, reuse, question])` → `E5 epoch(none, [])` → `R2`: for each of `multiple-myeloma`, `cancer`, `health` a `select` then `next`, then `select --clear` and `next`, saved as `next-<name>.txt` → `R3 read_view` of the two questions and the reuse → `R4 publish-preview --target multiple-myeloma-findings --to <run dir>/publish` saved verbatim (its refusal is expected and journaled as the step's result, not a failure) → `R5 belief --proposition proposition:concept-disease-stage-affects-protein-phf19` → `S1 status` saved as `status-final.txt`.

- [ ] **Step 3: Write `arms.py <state> <run dir>`.** `arm(name, cwd, run_dir)`: a `Server` with that `cwd`; over MCP `project-select {"target": "health"}`; then `run_cli` `status`, `projects`, `next` with the same `cwd`, saved; server closed by the context manager. The `workspace` arm's cwd is the mm program's workspace checkout; the `unrelated` arm's is `tempfile.mkdtemp()` holding `science.toml` (`world_root = "/nowhere"`), `science.yaml` (`project: decoy`) and `corpus.yaml` (`corpus: decoy`). The `mcp` arm: cwd `<wt>/python`; over MCP `project-select health`; then fresh-process `next` (→ `next-cli.txt`), `next --project multiple-myeloma` (→ `next-project-mm.txt`), `projects` (→ `projects-after.txt`). `compare(run_dir) -> dict`, written to `arms/compare.json`: (a) `workspace/` against `unrelated/` for `status.txt`, `projects.txt`, `next.txt`, all byte-equal; (b) both arms' `next.txt` equal to the walk's `next-health.txt`; (c) `mcp/next-cli.txt` equal to `next-health.txt`, `mcp/next-project-mm.txt` equal to `next-multiple-myeloma.txt`, and `mcp/projects-after.txt` marking `health` as selected.

- [ ] **Step 4: Static check.** `py_compile` all drivers exits 0; `python -c "import walk, selections, arms"` from `<task dir>/driver` with the worktree's interpreter exits 0.

---

### Task 5: Rehearsal and recovery drills on disposable replicas

**Files:**
- Create: `<task dir>/driver/rehearsal.py`; per attempt `<task dir>/rehearsal/<name>/worlds/<id>/…`, `<task dir>/rehearsal/<name>/science.toml`, `<task dir>/rehearsal/<name>/contracts/…`, `<task dir>/state/<name>/…`

**Interfaces:**
- Consumes: every driver of Tasks 2–4, `<world>/anchors/*.head`, `<world>/corpora/mm30`, `<world>/store`.
- Produces: `rehearsal.py <wt> <beliefs> <task dir> <name>` builds a replica world under `<task dir>/rehearsal/<name>/` (its data root), with `genesis.py` pointed at it and the replica's generated world id, then runs `declare.py`, `terms.py`, `walk.py` and `arms.py` against `<task dir>/state/<name>/`; `rehearsal.py --build-only` stops after `terms.py` for the drills.

- [ ] **Step 1: Write `rehearsal.py`** on `<beliefs>/python/tools/reproduction/relocate.py`'s recipe, with the live world as the source: `home = <task dir>/rehearsal/<name>/worlds/<secrets.token_hex(16)>`; copy the two head artifacts from `<world>/anchors/`; `replicate_root(<world>/corpora/mm30, home/corpora/mm30, authority=AUTHORITY)` then `restore_root(..., CorpusSubject(corpus_id), ObserverSet((ArtifactCarrier.from_bytes(corpus_head),)), authority=AUTHORITY)` and the same for the store with `StoreSubject(store_id)`; `init_world_root(WorldConfig(home/"world", world_id, (home/"corpora"/"mm30",)), authority=AUTHORITY)`; `admit_arrival(open_world(...), corpus_root, ReplicaOf(corpus_id), ObserverSet(...))`; refuse unless both restores and the arrival answer `validated`. Then run, in order, `genesis.py <state> <task dir>/rehearsal/<name> <world id> <beliefs> <home>/corpora/mm30`, `declare.py <state>`, `terms.py <state>`, and unless `--build-only`, `walk.py <state>` and `arms.py <state> <run dir>`.

- [ ] **Step 2: Run the full rehearsal** as `rehearsal-1`

Run: `<wt>/python/.venv/bin/python <task dir>/driver/rehearsal.py <wt> <beliefs> <task dir> rehearsal-1`
Expected: every MCP call `ok` except R4 `REFUSED` with `attribution-contract-unpinned`; `epochs.json` outcomes `built, built, built, built, current`; `next-stale.txt` carries `epoch-stale`; the four `next-*.txt` equal §5.6's R2 text; `selections.json` has `equivalent: true` and `complete: true` for every view, with the R1 sets of §5.6; `arms/compare.json` all equal. Any other refusal or mismatch is noted on the task with its text, filed (§5.8) where it is a finding, and fixed in the driver where it is the driver's; then the rehearsal reruns under a new name from a fresh replica until it completes as expected.

- [ ] **Step 3: Drill the recovery cases**, each on its own fresh replica (`rehearsal.py --build-only … <name>` first):
  - **(a) interruption between a selection and its mint** (`rehearsal-a`): `walk.py <state> --stop-after W3.select.health`; then `walk.py <state>` again with the same run directory. Expected: the second run verifies `W1.*` and `W2.*` by content, re-issues `project-select health` on its new server, mints `W3.question.health`, and completes; `selections.json` and the four `next-*.txt` equal rehearsal-1's.
  - **(b) a mint whose completion was not journaled** (`rehearsal-b`): `walk.py <state> --crash-before-record W3.question.evidence-bound-terms`; then `walk.py <state>` again. Expected: exit 3 naming `W3.question.evidence-bound-terms` and the check `project-show` under `multiple-myeloma`; the operator runs that check by explicit path, finds the question, runs `walk.py <state> --reconcile W3.question.evidence-bound-terms=<its address>`; `walk.py <state>` then completes with `R3` reporting that question `equivalent: true`.
  - **(c) a fresh journal against a completed world** (`rehearsal-1`'s replica, new run directory): `walk.py <state>` must stop at `W1.claim`'s fail-before-write check, naming the existing proposition, before any `attempt` row is written.
  Record each drill's outcome on the task; a drill that does not behave as expected is a driver defect, fixed and re-drilled on a fresh replica.

- [ ] **Step 4: Note the rehearsal** on the task: the replica world ids, run directories, the five epoch seconds of rehearsal-1, and the sha256 of every driver file as drilled.

---

### Task 6: The record's preflight and predictions, committed before the live run

**Files:**
- Create: `docs/records/2026-10-26-second-project-milestone.md` (§1 and §2 only)

**Interfaces:**
- Consumes: Task 5's artifacts (rehearsal-1's `queries/MANIFEST`, `declared.json` resource digests, the two `condition` labels, the drills' outcomes).
- Produces: the committed schedule and predictions the live run is marked against.

- [ ] **Step 1: Write §1 Preflight**: the mm30 record's shape (date, status line reading "predictions committed before the live run (`<sha>`)", scope). Contents: C1–C8 as observed on the live world (no working corpus yet; the pinned mm30 identity and the chain identity equal; the 18 records), the beliefs and science commits (`git -C <beliefs> rev-parse --short HEAD`, `git rev-parse --short HEAD`), the rehearsal and the three drills in one paragraph each (replica ids, outcomes, driver sha256s), the three inputs' md5 and sha256 digests and the two `condition` labels from the rehearsal download, and §5.1's reading-pass outputs (the overlap inventory `depmap`, `tcga`; GTEx `health/meta`'s only; the first health question's wording; the two datasets it needs held).

- [ ] **Step 2: Write §2 Schedule and predictions**: §5.6's table with the journal keys of Task 4; the six frozen queries by projection hash with `multiple-myeloma.yaml` quoted in full (285 term clauses, the held list's sha256 `c7e45f81…` beside it) and the others by their differing clauses; the predicted `next` renderings as exact text; the predicted refusal text for R4; the predicted `selections.json` sets; the criterion verdicts predicted (`met` for 1, 2, 6, 7; `partly met` for 3, 4; `unmet` for 5). State that the live declared addresses will differ from the rehearsal's only if the downloaded bytes differ, which would itself be a finding.

- [ ] **Step 3: Commit** (`just check` first):

```bash
git add docs/records/2026-10-26-second-project-milestone.md
git commit -m "docs(records): second-project milestone preflight and predictions"
```

---

### Task 7: The live run

**Files:**
- Create: `<data root>/contracts/mm30/…`, `<data root>/science.toml`, `<world>/corpora/working/`, `<world>/ops/`, `<task dir>/state/live/…`

**Interfaces:**
- Consumes: the drivers exactly as drilled (compare their sha256s with Task 5's note before running), the committed record.
- Produces: the live working corpus with its records, and `<task dir>/state/live/runs/<timestamp>/` for Task 8.

- [ ] **Step 1: Genesis.** Run `genesis.py <task dir>/state/live <data root> aec951bc6becacced13df8f7ae6f8abf <beliefs> <world>/corpora/mm30`. Expected: the chain identity line, the four pins, the working corpus id. Then `SCIENCE_CONFIG=<data root>/science.toml <wt>/python/.venv/bin/science status` saved as `<state>/preflight-status.txt`: two corpora `known=True live=True present=True`, 18 records in mm30, none in the working corpus, `No current epoch.` Note the corpus id and pins on the task.

- [ ] **Step 2: Declare.** Run `declare.py <task dir>/state/live`. Expected: two addresses equal to rehearsal-1's; `declared.json` written; `<task dir>/inputs/live/` gone; `status` shows `dataset 2` in the working corpus and no holdings observation.

- [ ] **Step 3: Freeze the live queries.** Run `terms.py <task dir>/state/live`; `diff` its `MANIFEST` against rehearsal-1's shows no difference (the addresses are equal), else the differing files are named on the task.

- [ ] **Step 4: The walk and the arms.** Run `walk.py <task dir>/state/live` then `arms.py <task dir>/state/live <run dir>`. Expected: as Task 5 Step 2. If the walk stops, follow the live-run contract: note the key and the refusal text on the task, file it, reconcile if the stop was an uncertain write, and resume from the journal; never rerun genesis or the declarations.

- [ ] **Step 5: Note the run** on the task: run directory, refusals (expected R4 only, or the list), the five epoch outcomes with seconds, `arms/compare.json`, and any resume or reconcile that happened.

---

### Task 8: Complete the record, attach the evidence, file the findings

**Files:**
- Modify: `docs/records/2026-10-26-second-project-milestone.md` (§3–§7)
- Attach to `sci-0d00d2`: `common.py`, `genesis.py`, `declare.py`, `terms.py`, `walk.py`, `selections.py`, `arms.py`, `rehearsal.py`, the live `science.toml`, `<state>/world.json`, `<state>/declared.json`, every file under `<state>/queries/`, and from the live run directory `progress.json`, every file under `queries-resolved/`, `walk.jsonl`, `serve.stderr`, `epochs.json`, `selections.json`, `next-stale.txt`, the four `next-*.txt`, `publish-preview.txt`, `belief.txt`, `status-final.txt`, `<state>/preflight-status.txt`, and every file under `arms/`.

**Interfaces:**
- Consumes: every artifact of Task 7, the committed §1–§2.

- [ ] **Step 1: Write §3 The path**: the recipes (genesis, declaration, selection read, rehearsal replication) quoted; the command table with journal key, command, invocation id, minted address, seconds; the `PLACEHOLDER` substitution with both hashes; any resume or reconcile, with its journal rows.

- [ ] **Step 2: Write §4 Predictions, marked** and each criterion's verdict (`met`, `partly met`, `unmet`) against §2, citing the artifact each mark reads; `selections.json`'s `equivalent` and `complete` columns reported per view.

- [ ] **Step 3: Write §5 Findings**: the §5.8 list plus anything the rehearsal, the drills or the run raised, each with class and the task id it is filed under (Step 6).

- [ ] **Step 4: Write §6 Measurements** M1–M6 from `epochs.json`, `selections.json`, `walk.jsonl` and the stored relations (M5: the stored-edge closure and the projection-derived closure of the five findings records, read from the record files under `<world>/corpora/mm30/`).

- [ ] **Step 5: Write §7 What this decides**: the fence (M3's three counts), the two notes to `beliefs`, the two proposed amendments (§8) with their evidence, and the health follow-up. Set the status line's commit sha to Task 6's commit.

- [ ] **Step 6: File the findings** (each `--origin agent`, body naming the record path and section; one task per finding): in `sci`: no corpus genesis command; no dataset declaration command; `spec` names one input; only a project can be previewed or published; no command renders a view's selection; the composite outside the coarse form and the §6.2 term-clause amendment (one task, tag `projects`); the health contract idea (`--status idea`). In `beliefs` (`tasks add --project beliefs …`): a relocated replica of the world's own corpus refused as a foreign publication; stored-edge closure narrower than the projection-derived rule; the `also:` key (idea). Then `tasks note beliefs-7c98bc "<M2 counts>"` and `tasks note beliefs-655c10 "<M1 coordination-only count and seconds>"`. Record each returned id in §5.

- [ ] **Step 7: Attach the evidence**: one `tasks attach sci-0d00d2 <file> --caption "<what it shows>"` per file listed above, from `<wt>`. Then `rm -rf <task dir>/rehearsal <task dir>/state/rehearsal-*` (their findings, if any, are in §5 with their text) and write the retained-item note for what stays under `<task dir>` (path, purpose: the live state and run directory; next owner: the health program's first task; cleanup trigger: that task's start or 90 days; a manifest of sha256s and its hash).

- [ ] **Step 8: Commit** (`just check` first):

```bash
git add docs/records/2026-10-26-second-project-milestone.md tasks/
git commit -m "docs(records): second-project milestone run, findings and measurements"
```

Then `tasks done sci-0d00d2 "<one line: criteria met/partly/unmet, record path>"` once the branch's final review is in.
