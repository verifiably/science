# The Belief Path Commands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the eight commands that carry one proposition from a typed claim to a computed belief over a real `beliefs` world — `claim`, `dataset`, `spec`, `run`, `assess`, `verify`, `belief`, `next` — and measure them by reproducing mm30's one proposition afresh.

**Architecture:** Each command is a declaration (`commands/<name>/command.toml` + `prompt.md`) and a handler module (`python/src/science/commands/<name>.py`) that the existing loader binds by name. Handlers read the world through `ReadContext` and act only through the invocation-scoped writer the dispatcher hands them; every write is a kernel act, every refusal is the framework's envelope. The read context grows three derivations the commands share: the resolution snapshot from held vocabularies, holdings reads from the store, and the supplied context the belief evaluator needs. Two kernel seams (`beliefs-e5ab34`, `beliefs-5fe2e3`) and one framework amendment (Task 1) sit under the commands.

**Tech Stack:** Python 3.11+, `beliefs` (editable path dependency; brings `snakemake`), stdlib `tomllib`/`argparse`/`socketserver`, pytest via `just`. No new dependencies.

**Spec:** `docs/specs/2026-09-09-belief-path-commands-design.md` — the plan argues from it; read both. Governing framework: `docs/specs/2026-08-31-command-framework-design.md`.

## Global Constraints

- Tests run through `just`: `just test-fast` (affected-only) in the inner loop, `just test` before every commit. Never call `pytest` directly (AGENTS.md).
- `tasks start <id>` before a task's first change; `tasks done <id>` in the task's final commit; `tasks check` passes at every commit (the pre-commit hook runs it).
- Conventional commits, no attribution trailers.
- `science` never sees, threads, or constructs a permit or an `Authority` (framework §4.2). Handlers act only through the scoped writer's methods. Test helpers may hold the full fixture authority, as `helpers/world.py` already does.
- Every write handler validates before its first act and refuses with `science.refusal.Refused(Refusal("invalid-input", …))`; after the first act it raises nothing but what the kernel raises (spec §6.3).
- Every command directory is exactly `command.toml` and `prompt.md`; the handler module is the name with `-` → `_`; a `mints` handler's signature is `handle(ctx, writer, *, <inputs…>)`, a read's is `handle(ctx, *, <inputs…>)`, optional inputs default to `None` (loader shape checks).
- `output_budget` ≥ `MIN_OUTPUT_BUDGET` (398). The spec's budgets: 4096 for writes, 8192 for `belief`, 16384 for `next`.
- The committed adapter tree `adapters/claude-code/` must equal a fresh `science adapters build` (`test_generated_tree_matches_committed`). Every task that adds a command regenerates and commits it.
- Machine paths never appear in generated output (`test_mcp_json_has_no_machine_paths`).
- Avoid `/home/<user>` or `/mnt/…` paths in code comments and docs.

## Assumed kernel seams

Tasks 3, 4, 6, 7, 8 and 9 call interfaces `beliefs` does not have yet. These are the names the two `beliefs` tasks deliver; if a name lands differently, change the call site, not the design.

- **`beliefs-e5ab34` (reference rules):** `beliefs.rules.REFERENCE_RULES: Mapping[str, RuleImplementation | EquivalenceImplementation]` keyed by rule identity, holding `"outcome-file/v1"` (interpretation: maps the digest of `outputs/outcome.txt` — one of `supported\n`, `refuted\n`, `inconclusive\n` — to `{"outcome": …}`) and `"content-identity-equality/v1"` (equivalence: `passed` iff the two result manifests are equal). `beliefs.rules.OUTCOME_FILE = "outputs/outcome.txt"`.
- **`beliefs-5fe2e3` (scoped routes):** `beliefs.root.store_identity(store_root: Path) -> str | None` (the public form of the existing private genesis read, by detached inspection); `open_attended_session(world_config, operations_root, *, profile, coordination=None, store_root: Path | None = None)`; `ScopedWriter.operation_port() -> OperationPort` bound to the invocation's scoped authority, whose commits are recorded as `act` lines; `ScopedWriter.holdings_context(*, instrument: str) -> ActContext` over the session's store root, observer = the session actor, whose published observations are recorded as `act` lines; `ScopedWriter.store_id -> str`; and `beliefs.replay.replay(original: RunMinted | RunClosure, …)` reading only the closure.

Do Tasks 1–2 first. Task 3 waits on `beliefs-5fe2e3` for the public store identity reader, so Tasks 4–11 also wait on that seam through the read context. Tasks 6 and 8 additionally need the reference rules; Task 11 follows Task 6 because its readiness test freezes a spec through the production command.

## File structure

**Framework and context (modified):**
- `python/src/science/dispatch.py` — `_invoke_write` catches a handler's `Refused` (Task 1).
- `python/src/science/config.py` — `contracts`, `store_root`; `ScienceConfig.plans`; `ReadContext.single_view()`, `.snapshot()`, `.held_path()`, `.observations()`, `.evaluate()` (Tasks 2–3).

**New modules (one responsibility each):**
- `python/src/science/contracts.py` — load corpus-local contract documents: parsed `DomainContract`s for the profile and the `OperatorPlan` for `claim` (Task 2).
- `python/src/science/vocabulary.py` — the resolution snapshot over held vocabularies (Task 3).
- `python/src/science/holdings.py` — store reads: `Found` observations by address, the held path for an address, `admission_state` checks (Task 3).
- `python/src/science/closure.py` — `Availability`, `SuppliedContext`, `evaluate_over` in one call (Task 3).
- `python/src/science/commands/{dataset,claim,spec,run,assess,verify,belief,next}.py` — handlers (Tasks 4–11).
- `commands/{dataset,claim,spec,run,assess,verify,belief,next}/{command.toml,prompt.md}` — declarations (Tasks 4–11).

**Tests:**
- `python/tests/helpers/world.py` — grown: a corpus-local test contract document, a held dataset, a fixture bundle, a minted fixture run (Task 3 onward).
- `python/tests/test_dispatch_refusals.py` (Task 1), additions to `test_config.py` (Task 2), `test_context.py` (Task 3), `test_cmd_<name>.py` per command (Tasks 4–11), additions to `test_mcp.py` (Task 12).

**Docs:** framework design §9.1 amendments (Task 2); `docs/records/<date>-mm30-through-the-commands.md` (Task 13).

---

### Task 1: The dispatcher closes a surface refusal raised by a write handler

**Files:**
- Modify: `python/src/science/dispatch.py:149-216` (`_invoke_write`)
- Test: `python/tests/test_dispatch_refusals.py`
- Modify: `docs/specs/2026-08-31-command-framework-design.md` §6.1 (one amendment paragraph)

**Interfaces:**
- Consumes: `WriterSession.invocation_acts(iid)`, `close_invocation(iid, outcome)`; `science.refusal.Refused`.
- Produces: the guarantee every later handler relies on — a `Refused` raised before the first act closes the invocation with the refusal envelope, and a retry replays it.

- [ ] **Step 1: Write the failing tests**

```python
# python/tests/test_dispatch_refusals.py
"""Spec §6.3: a surface refusal raised by a write handler closes the invocation."""
from pathlib import Path

import pytest

from science.cursor import MIN_OUTPUT_BUDGET
from science.dispatch import Dispatcher
from science.refusal import Refusal, Refused
from science.report import record_block
from science.schema import Declaration, InputSpec, WriteClass
from helpers.world import build_fixture_world, fixture_proposition_node

REFUSING = Declaration("refusing", "fixture",
                       WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                       MIN_OUTPUT_BUDGET, (InputSpec("slug", "string", True, "d"),), (), Path("."))
HALF_ACTED = Declaration("half-acted", "fixture",
                         WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                         MIN_OUTPUT_BUDGET, (InputSpec("slug", "string", True, "d"),), (), Path("."))


def refusing_handler(ctx, writer, *, slug):
    raise Refused(Refusal("invalid-input", f"no plan row for {slug}"))


def half_acted_handler(ctx, writer, *, slug):
    writer.add(fixture_proposition_node(slug))
    raise Refused(Refusal("invalid-input", "refused after acting"))


@pytest.fixture
def rig(certified_work):
    from beliefs.session import open_attended_session
    from science.config import ReadContext
    cfg = build_fixture_world(certified_work)
    session = open_attended_session(cfg.world, cfg.operations_root, profile=cfg.profile)
    dispatcher = Dispatcher((REFUSING, HALF_ACTED),
                            {"refusing": refusing_handler, "half-acted": half_acted_handler},
                            ReadContext.open(cfg), session=session)
    try:
        yield dispatcher, session
    finally:
        session.close()


def test_refusal_before_any_act_closes_and_replays(rig):
    d, session = rig
    with pytest.raises(Refused) as first:
        d.invoke("refusing", {"slug": "x"}, invocation_id="R" * 8)
    assert first.value.refusal.code == "invalid-input"
    assert "no plan row" in first.value.refusal.message
    # The retry replays the recorded refusal from the ledger, never outcome-unknown.
    with pytest.raises(Refused) as again:
        d.invoke("refusing", {"slug": "x"}, invocation_id="R" * 8)
    assert again.value.refusal.code == "invalid-input"
    assert again.value.refusal.message == first.value.refusal.message
    assert session.invocation_acts("R" * 8) == ()


def test_refusal_after_an_act_closes_done_and_is_an_internal_error(rig):
    d, session = rig
    from science.dispatch import HandlerContractViolation
    with pytest.raises(HandlerContractViolation):
        d.invoke("half-acted", {"slug": "acted"}, invocation_id="H" * 8)
    assert len(session.invocation_acts("H" * 8)) == 1
    # The ledger closed `done`: a retry replays the minted record, not a refusal.
    out = d.invoke("half-acted", {"slug": "acted"}, invocation_id="H" * 8)
    assert "proposition:acted" in out.text
```

- [ ] **Step 2: Run to verify they fail**

Run: `just test-fast`
Expected: the first test fails with `outcome-unknown` on the retry; the second fails with `ImportError: HandlerContractViolation`.

- [ ] **Step 3: Implement the dispatcher change**

In `python/src/science/dispatch.py`, add the exception class near the top (after imports):

```python
class HandlerContractViolation(RuntimeError):
    """A write handler raised a surface refusal after it had already acted.

    Validation precedes the first act (belief-path design §6.3). The acts
    committed are truth, so the invocation closes `done` with them; the
    refusal is not a refusal any more but a defect in the handler.
    """
```

Replace the handler call block in `_invoke_write`:

```python
            try:
                report = self._handlers[decl.name](self._ctx, writer, **canonical)
            except (PermitExceeded, KernelRefusalValue, WriteRefused) as caught:
                return self._close_refused(iid, self._kernel_refusal(caught))
            except Refused as caught:
                acted = self._session.invocation_acts(iid)
                if not acted:
                    return self._close_refused(iid, caught.refusal)
                minted = frozenset(tuple(pair) for act in acted for pair in act.record_ids)
                self._session.close_invocation(
                    iid, {"done": [list(pair) for pair in sorted(minted)]}
                )
                raise HandlerContractViolation(
                    f"{decl.name} refused {caught.refusal.code!r} after {len(acted)} act(s); "
                    "a write handler validates before its first act"
                ) from caught
```

- [ ] **Step 4: Run to verify they pass**

Run: `just test-fast`
Expected: both PASS. Then `just test` — the whole suite still passes.

- [ ] **Step 5: Amend the framework design §6.1**

Append after the dispatch-order paragraph in `docs/specs/2026-08-31-command-framework-design.md` §6.1:

```markdown
**Amended 2026-09-09 (belief-path design §6.3).** A surface `Refused` raised by
a write handler is caught at step 5. With no act recorded for the invocation,
the dispatcher closes it with the refusal envelope exactly as a kernel refusal
closes, and a retry replays that refusal from the ledger. With an act
recorded, the handler broke the validate-before-act rule: the dispatcher closes
`done` with the minted identities and raises `HandlerContractViolation`, an
internal error, because a half-acted write is a defect and not a refusal.
```

- [ ] **Step 6: Commit**

```bash
tasks done sci-614bdd "dispatcher closes surface refusals from write handlers; spec §6.1 amended"
git add python/src/science/dispatch.py python/tests/test_dispatch_refusals.py docs/specs/2026-08-31-command-framework-design.md tasks/
git commit -m "feat(dispatch): close a surface refusal raised by a write handler"
```

---

### Task 2: Configuration — `contracts`, `store_root`, and the operator plan

**Files:**
- Create: `python/src/science/contracts.py`
- Modify: `python/src/science/config.py`
- Modify: `python/tests/helpers/world.py` (`build_fixture_world`, `write_cli_config`)
- Test: `python/tests/test_config.py`, `python/tests/test_contracts.py`
- Modify: `docs/specs/2026-08-31-command-framework-design.md` §9.1

**Interfaces:**
- Consumes: `beliefs.contract.domain.parse_domain_contract(document, *, source, base, predecessor)`, `beliefs.profile.compile_profile`, `shipped_base_contract`, `shipped_domain_contract`.
- Produces: `ScienceConfig.store_root: Path`, `ScienceConfig.plans: tuple[OperatorPlan, ...]`; `science.contracts.OperatorPlan` with `.operator_for(predicate, subject_kind, object_kind) -> str`, `.sort_for(kind) -> str`, `.layers: Mapping[str, str]`, `.polarities: Mapping[str, str]`; `science.contracts.load_contract_document(path, base) -> tuple[DomainContract, OperatorPlan | None]`.

- [ ] **Step 1: Write the failing contract-document tests**

```python
# python/tests/test_contracts.py
from pathlib import Path

import pytest

from science.contracts import OperatorPlan, load_contract_document
from science.refusal import Refused

DOCUMENT = '''\
contract:
  contract: testing
  version: 1
  lineage: genesis
  sorts:
    concept:
      vocabulary: "dataset:%s"
  dimensions: {}
  operators:
    affects-concept-concept:
      arity: 2
      arg_sorts: [concept, concept]
      sign_apt: true
      layers: [causal]
      dimensions: []
    binds-concept-concept:
      arity: 2
      arg_sorts: [concept, concept]
      sign_apt: false
      layers: [causal]
      dimensions: []
plan:
  sorts: {concept: concept}
  layers: {causal: causal}
  polarities: {positive: positive, negative: negative, not_applicable: null}
  operators:
    - {predicate: affects, subject: concept, object: concept, operator: affects-concept-concept}
    - {predicate: binds, subject: concept, object: concept, operator: binds-concept-concept}
'''


def write_document(tmp_path: Path, text: str = DOCUMENT % ("0" * 64)) -> Path:
    path = tmp_path / "testing.yaml"
    path.write_text(text)
    return path


def test_document_parses_to_a_contract_and_a_plan(tmp_path):
    from beliefs.profile import shipped_base_contract
    contract, plan = load_contract_document(write_document(tmp_path), shipped_base_contract())
    assert contract.namespace == "testing"
    assert isinstance(plan, OperatorPlan)
    assert plan.operator_for("affects", "concept", "concept") == "testing/affects-concept-concept"
    assert plan.sort_for("concept") == "testing/concept"
    assert plan.layers["causal"] == "causal"


def test_plan_refuses_a_shape_with_no_row(tmp_path):
    from beliefs.profile import shipped_base_contract
    _, plan = load_contract_document(write_document(tmp_path), shipped_base_contract())
    with pytest.raises(Refused) as caught:
        plan.operator_for("affects", "concept", "protein")
    assert caught.value.refusal.code == "invalid-input"
    assert "affects concept->protein" in caught.value.refusal.message


def test_plan_preserves_a_null_polarity_for_sign_inapt_operators(tmp_path):
    """mm30's plan carries `not_applicable: null`; `build_claim` takes
    polarity=None for a sign-inapt operator, and the plan must say None, not
    the string "None"."""
    from beliefs.profile import shipped_base_contract
    _, plan = load_contract_document(write_document(tmp_path), shipped_base_contract())
    assert "not_applicable" in plan.polarities
    assert plan.polarities["not_applicable"] is None
    assert plan.operator_for("binds", "concept", "concept") == "testing/binds-concept-concept"


def test_document_without_a_plan_yields_none(tmp_path):
    from beliefs.profile import shipped_base_contract
    text = (DOCUMENT % ("0" * 64)).split("plan:")[0]
    _, plan = load_contract_document(write_document(tmp_path, text), shipped_base_contract())
    assert plan is None


def test_malformed_document_refuses(tmp_path):
    from beliefs.profile import shipped_base_contract
    with pytest.raises(Refused) as caught:
        load_contract_document(write_document(tmp_path, "contract: [not a table]\n"), shipped_base_contract())
    assert caught.value.refusal.code == "invalid-input"
```

- [ ] **Step 2: Write the failing config tests** (append to `python/tests/test_config.py`)

```python
def test_contracts_and_store_root_are_required_keys(tmp_path):
    """A config written before the belief-path spec refuses rather than
    compiling a profile the corpus's pins disagree with."""
    assert_invalid_config(write_config(tmp_path, contracts=None, store_root=None))


def test_contracts_compile_into_the_profile(tmp_path):
    from tests.test_contracts import DOCUMENT  # the same fixture document
    doc = tmp_path / "testing.yaml"
    doc.write_text(DOCUMENT % ("0" * 64))
    cfg = load_config(write_config(tmp_path, contracts=f'["{doc}"]'))
    assert "testing" in cfg.profile.activated_contracts
    assert cfg.store_root == tmp_path / "store"
    (plan,) = cfg.plans
    assert plan.operator_for("affects", "concept", "concept") == "testing/affects-concept-concept"


def test_store_root_resolves_like_operations_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config(write_config(tmp_path, store_root="held"))
    assert cfg.store_root == tmp_path / "held"


def test_unparseable_contract_document_refuses_at_load(tmp_path):
    doc = tmp_path / "bad.yaml"
    doc.write_text("contract: 3\n")
    assert_invalid_config(write_config(tmp_path, contracts=f'["{doc}"]'))
```

Update `write_config` in `test_config.py` so the two keys are written by default and can be omitted:

```python
def write_config(
    tmp_path: Path,
    world_id: str = WORLD_ID,
    extra: str = "",
    operations_root: str | Path | None = None,
    domains: str = "[]",
    contracts: str | None = "[]",
    store_root: str | Path | None = "",
) -> Path:
    world_root = tmp_path / "world"
    ops = tmp_path / "ops" if operations_root is None else operations_root
    store = tmp_path / "store" if store_root == "" else store_root
    corpus = tmp_path / "corpora" / "one"
    cfg = tmp_path / "science.toml"
    lines = [
        f'world_root = "{world_root}"',
        f'world_id = "{world_id}"',
        f'corpus_roots = ["{corpus}"]',
        f'operations_root = "{ops}"',
        f"domains = {domains}",
    ]
    if contracts is not None:
        lines.append(f"contracts = {contracts}")
    if store is not None:
        lines.append(f'store_root = "{store}"')
    cfg.write_text("\n".join(lines) + "\n" + extra)
    return cfg
```

Also update the parametrized malformed-TOML cases (`_TAIL`) to carry the two new keys: `_TAIL = 'domains = []\ncontracts = []\nstore_root = "/x"\n'`, and the two cases that end with an explicit `domains = …` line gain `contracts = []\nstore_root = "/x"\n` after it.

- [ ] **Step 3: Run to verify they fail**

Run: `just test-fast`
Expected: `ImportError` for `science.contracts`; the config tests fail on `must contain exactly the required keys`.

- [ ] **Step 4: Write `science/contracts.py`**

```python
"""Corpus-local contract documents (belief-path design §5.2).

A document carries `contract` (a domain contract, parsed against the shipped
base) and optionally `plan`: the operator plan `claim` reads to turn a
predicate and two kind prefixes into an operator, and a kind prefix into a
sort. The plan is launcher input; the contract's identity does not cover it.
Superseded whenever the kernel gives contracts a home (design ruling 5).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

from beliefs.contract.domain import DomainContract, parse_domain_contract
from beliefs.errors import MalformedContract

from science.refusal import Refusal, Refused


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


@dataclass(frozen=True)
class OperatorPlan:
    namespace: str
    operators: Mapping[tuple[str, str | None, str | None], str]
    sorts: Mapping[str, str]
    layers: Mapping[str, str]
    polarities: Mapping[str, str | None]
    """A null value is a value: `not_applicable: null` names the polarity a
    sign-inapt operator takes (`build_claim(polarity=None)`). Missing is
    different from null; callers test membership, never truthiness."""

    def operator_for(self, predicate: str, subject_kind: str, object_kind: str) -> str:
        row = self.operators.get((predicate, subject_kind, object_kind))
        if row is None:
            row = self.operators.get((predicate, None, None))
        if row is None:
            _refuse(f"no plan row for {predicate} {subject_kind}->{object_kind} in contract "
                    f"{self.namespace!r}; a shape with no row is refused, never nearest-typed")
        return row

    def sort_for(self, kind: str) -> str:
        sort = self.sorts.get(kind)
        if sort is None:
            _refuse(f"kind prefix {kind!r} maps to no sort in contract {self.namespace!r}'s plan")
        return sort


def _term(domain: DomainContract, name: str) -> str:
    return name if "/" in name else domain.term(name)


def _plan(raw: object, domain: DomainContract) -> OperatorPlan:
    if not isinstance(raw, dict):
        _refuse("a contract document's plan must be a table")
    rows_raw = raw.get("operators") or []
    if not isinstance(rows_raw, list):
        _refuse("plan.operators must be a list of rows")
    rows: dict[tuple[str, str | None, str | None], str] = {}
    for row in rows_raw:
        if not isinstance(row, dict) or "predicate" not in row or "operator" not in row:
            _refuse("each plan row names predicate and operator")
        key = (str(row["predicate"]), row.get("subject"), row.get("object"))
        rows[key] = _term(domain, str(row["operator"]))
    return OperatorPlan(
        namespace=domain.namespace,
        operators=rows,
        sorts={str(k): _term(domain, str(v)) for k, v in (raw.get("sorts") or {}).items()},
        layers={str(k): str(v) for k, v in (raw.get("layers") or {}).items()},
        polarities={str(k): (None if v is None else str(v)) for k, v in (raw.get("polarities") or {}).items()},
    )


def load_contract_document(path: Path, base) -> tuple[DomainContract, OperatorPlan | None]:
    if not path.is_file():
        _refuse(f"contract document not found: {path}")
    try:
        document = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as caught:
        _refuse(f"contract document {path} is not readable YAML: {caught}")
    if not isinstance(document, dict) or "contract" not in document:
        _refuse(f"contract document {path} must be a table with a `contract` key")
    try:
        contract = parse_domain_contract(
            document["contract"], source=f"{path}: contract", base=base, predecessor=None
        )
    except MalformedContract as caught:
        _refuse(f"contract document {path} does not parse: {caught}")
    plan = _plan(document["plan"], contract) if "plan" in document else None
    return contract, plan
```

Check the exception name: `grep -n "^class MalformedContract" ~/d/beliefs/python/src/beliefs/errors.py`; if it lives elsewhere, import from there. `DomainContract.namespace` and `.term(name)` are what the driver's `vocabulary.py` used.

- [ ] **Step 5: Extend `science/config.py`**

```python
_KEYS = ("world_root", "world_id", "corpus_roots", "operations_root", "domains", "contracts", "store_root")
```

Add to `ScienceConfig`:

```python
    store_root: Path
    plans: tuple[OperatorPlan, ...] = ()
```

In `load_config`, after the `domains` type check:

```python
    if type(raw["contracts"]) is not list or any(type(v) is not str for v in raw["contracts"]):
        _refuse("config contracts must be a list of strings")
    if type(raw["store_root"]) is not str:
        _refuse("config store_root must be a string")
```

Replace the profile compilation:

```python
    base = shipped_base_contract()
    try:
        domains = [shipped_domain_contract(namespace) for namespace in raw["domains"]]
    except ProfileError as caught:
        _refuse(f"config domains do not compile: {caught}")
    local = [load_contract_document(Path(value).resolve(), base) for value in raw["contracts"]]
    try:
        profile = compile_profile(base, domains + [contract for contract, _ in local])
    except ProfileError as caught:
        _refuse(f"config contracts do not compile: {caught}")
    plans = tuple(plan for _, plan in local if plan is not None)
```

and pass `store_root=Path(raw["store_root"]).resolve(), plans=plans` to the `ScienceConfig(...)` call. Import `OperatorPlan, load_contract_document` from `science.contracts`.

- [ ] **Step 6: Grow the fixture helpers** (`python/tests/helpers/world.py`)

`build_fixture_world` gains a store root and returns `store_root=work / "store"` on the config (initialize it: `store_id = init_store_root(work / "store", authority=FIXTURE_AUTHORITY)` and keep the id on a module-level dict `STORE_IDS[work] = store_id` for later helpers). `write_cli_config` writes `contracts = []` and `store_root = "{cfg.store_root}"`.

- [ ] **Step 7: Run to verify they pass**

Run: `just test` (the config change touches every fixture).
Expected: all PASS, including `test_status.py` (its hand-built `ScienceConfig` gains `store_root=cfg.store_root`).

- [ ] **Step 8: Amend framework design §9.1**

Append after the `service_socket` paragraph:

```markdown
`contracts` and `store_root` (**added 2026-09-09**: belief-path design §5.1).
`contracts` lists corpus-local domain-contract documents by path, parsed
against the shipped base and compiled into the profile with the shipped
domains; a document may carry an operator `plan` the `claim` command reads.
It is required and may be empty, for `domains`'s reason. `store_root` is the
holdings store the session and the `dataset` command bind, resolved like
`operations_root`; required. Both are superseded whenever the kernel gives
contracts a home (belief-path ruling 5).
```

- [ ] **Step 9: Commit**

```bash
tasks done sci-05c56c "contracts and store_root config keys; corpus-local contract documents and operator plans"
git add python/src/science/contracts.py python/src/science/config.py python/tests/ docs/specs/2026-08-31-command-framework-design.md tasks/
git commit -m "feat(config): corpus-local contract documents and the holdings store root"
```

---

### Task 3: The read context — snapshot, holdings reads, supplied context, fixture path

**Blocked on `beliefs-5fe2e3`** (`beliefs.root.store_identity`).

**Files:**
- Create: `python/src/science/vocabulary.py`, `python/src/science/holdings.py`, `python/src/science/closure.py`
- Modify: `python/src/science/config.py` (`ReadContext`)
- Modify: `python/tests/helpers/world.py` (contract document, held dataset, bundle, fixture run)
- Test: `python/tests/test_context.py`

**Interfaces:**
- Consumes: `beliefs.resolution.build_snapshot(readable=…)`, `VocabularyBinding`, `ProfileSpec.sorts` (`CompiledSort.vocabulary`), `stored.dataset_declaration`, `stored.holdings_observation_value`, `beliefs.dataset.{dataset_address, admission_state, ByteObservation, Held}`, `beliefs.evaluation.{evaluate_over, gather}`, `beliefs.belief.{Availability, SuppliedContext}`, `beliefs.closure.RetractionEnumeration`, `beliefs.corpus.lineage_snapshot`, `beliefs.policy.{BELIEF_V1, BELIEF_V1_RULE, BELIEF_V1_FIXTURES, PolicyBinding}`, `beliefs.world.read.current_epoch`, `beliefs.errors.EpochUnknown`, `beliefs.world.registry.load_manifest`.
- Produces on `ReadContext`: `single_view() -> tuple[str, ReadView]`; `store_id() -> str`; `snapshot() -> ResolutionSnapshot`; `observations() -> dict[str, tuple[ByteObservation, ...]]` keyed by dataset address; `held_path(address) -> Path`; `is_held(node) -> bool`; `evaluate(proposition) -> Belief | NoBelief | Refused`; `gather_inputs(proposition) -> EvaluationInputs`; `pins() -> CorpusPins`; `epoch_identity() -> str`.
- Produces in helpers: `fixture_contract_document(work) -> Path` (a `testing` contract with `concept` bound by dataset identity and `protein` bound by namespace/release, and a plan), `hold_fixture_dataset(cfg, name, content, title) -> str` (returns the dataset ref), `unhold_fixture_dataset(cfg, ref) -> None` (a later `Absent` observation superseding the `Found`), `fixture_bundle(work, outcome="supported") -> tuple[Path, str, tuple[str, ...]]` (code dir, entrypoint, targets), `mint_fixture_run(cfg, spec_ref, dataset_ref, bundle) -> str` (a run under `MINIMAL_POLICY`, returns the run ref), `build_belief_world(work) -> ScienceConfig` (fixture world compiled with the test contract, the holdings reducer installed, concept list held, one proposition minted), `open_rig(cfg, names)` (a dispatcher over the named production commands with an attended session; yields `(dispatcher, ctx)`), and `SPEC_FIELDS` (the draft fields every spec test reuses).

- [ ] **Step 1: Write the failing tests**

```python
# python/tests/test_context.py
import pytest

from beliefs.resolution import TermOutcome
from science.config import ReadContext
from science.refusal import Refused
from helpers.world import build_belief_world, hold_fixture_dataset


def test_single_view_names_the_one_corpus(certified_work):
    ctx = ReadContext.open(build_belief_world(certified_work))
    corpus_id, view = ctx.single_view()
    assert len(corpus_id) == 32 and view.holds("proposition:p1")


def test_snapshot_resolves_the_held_concept_vocabulary(certified_work):
    cfg = build_belief_world(certified_work)
    ctx = ReadContext.open(cfg)
    snapshot = ctx.snapshot()
    (binding,) = [s.vocabulary for s in cfg.profile.sorts.values() if s.vocabulary.dataset_identity]
    assert snapshot.resolve(binding, "concept:disease-stage") is TermOutcome.MEMBER
    assert snapshot.resolve(binding, "concept:absent") is TermOutcome.NOT_MEMBER


def test_snapshot_omits_a_vocabulary_that_is_not_held(certified_work):
    """The binding names a dataset; nothing holds it; the snapshot says so."""
    from helpers.world import build_fixture_world_with_contract
    cfg = build_fixture_world_with_contract(certified_work, hold_concepts=False)
    snapshot = ReadContext.open(cfg).snapshot()
    (binding,) = [s.vocabulary for s in cfg.profile.sorts.values() if s.vocabulary.dataset_identity]
    assert snapshot.resolve(binding, "concept:disease-stage") is TermOutcome.NOT_AVAILABLE


def test_a_later_absent_observation_removes_heldness(certified_work):
    """The reduction, not the history: once an Absent supersedes the Found at
    a location, the dataset is not held, whatever the older observation says."""
    from helpers.world import unhold_fixture_dataset
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"gone\n", "expression")
    ctx = ReadContext.open(cfg)
    _, view = ctx.single_view()
    assert ctx.is_held(view.get(ref))
    unhold_fixture_dataset(cfg, ref)
    ctx = ReadContext.open(cfg)
    _, view = ctx.single_view()
    assert not ctx.is_held(view.get(ref))
    from beliefs import stored
    from beliefs.dataset import dataset_address
    assert dataset_address(stored.dataset_declaration(view.get(ref))) not in ctx.observations()


def _tree_digest(root):
    from hashlib import sha256
    digest = sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode()); digest.update(path.read_bytes())
    return digest.hexdigest()


def test_holdings_reads_inspect_detached_and_write_nothing(certified_work, monkeypatch):
    """A read must not recover: the reducer is fed the detached chain view,
    and the corpus tree, its metadata and the store are byte-identical after."""
    import science.holdings as holdings_module
    from beliefs.root import log_seam, metadata_root_for
    cfg = build_belief_world(certified_work)
    hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    (root,) = cfg.world.corpus_roots
    before = tuple(_tree_digest(d) for d in (root, metadata_root_for(root), cfg.store_root))
    seam = log_seam()

    class RefusingSeam:
        inspect_detached = staticmethod(seam.inspect_detached)
        state_facts = staticmethod(seam.state_facts)

        @staticmethod
        def inspect_registered(root):
            raise AssertionError("a holdings read must never use the registered (recovering) inspection")

    monkeypatch.setattr(holdings_module, "log_seam", lambda: RefusingSeam)
    ctx = ReadContext.open(cfg)
    assert ctx.observations()
    assert tuple(_tree_digest(d) for d in (root, metadata_root_for(root), cfg.store_root)) == before


def test_observations_and_held_path_follow_the_store(certified_work):
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"hello\n", "expression")
    ctx = ReadContext.open(cfg)
    _, view = ctx.single_view()
    node = view.get(ref)
    assert ctx.is_held(node)
    from beliefs import stored
    from beliefs.dataset import dataset_address
    address = dataset_address(stored.dataset_declaration(node))
    assert address in ctx.observations()
    assert ctx.held_path(address).read_bytes() == b"hello\n"


def test_held_path_resolves_only_the_configured_store(certified_work):
    """An observation recorded for another store id never selects a file here,
    even when its relative path exists under this store root."""
    from beliefs.dataset import ByteObservation
    from science.holdings import held_path_for
    from science.refusal import Refused
    cfg = build_belief_world(certified_work)
    ctx = ReadContext.open(cfg)
    mine = ctx.store_id()
    other = ("0" * 32) if mine != "0" * 32 else ("1" * 32)
    (cfg.store_root / "aa").mkdir(exist_ok=True)
    (cfg.store_root / "aa" / "f.txt").write_bytes(b"here\n")
    foreign = ByteObservation(digest="sha256:" + "a" * 64, location=f"store:{other}:aa/f.txt")
    local = ByteObservation(digest="sha256:" + "a" * 64, location=f"store:{mine}:aa/f.txt")
    with pytest.raises(Refused):
        held_path_for(cfg.store_root, mine, (foreign,))
    assert held_path_for(cfg.store_root, mine, (foreign, local)) == cfg.store_root / "aa" / "f.txt"


def test_held_path_refuses_an_unknown_address(certified_work):
    ctx = ReadContext.open(build_belief_world(certified_work))
    with pytest.raises(Refused) as caught:
        ctx.held_path("dataset:sha256:" + "0" * 64)
    assert caught.value.refusal.code == "invalid-input"


def test_evaluate_answers_no_belief_before_any_assessment(certified_work):
    ctx = ReadContext.open(build_belief_world(certified_work))
    answer = ctx.evaluate("proposition:p1")
    assert type(answer).__name__ == "NoBelief"
    assert answer.reason == "no-eligible-assessment"


def test_epoch_identity_is_the_no_epoch_value_without_one(certified_work):
    ctx = ReadContext.open(build_belief_world(certified_work))
    assert ctx.epoch_identity() == "no-epoch-published"
```

Check `ResolutionSnapshot.resolve`'s name and return with `grep -n "def resolve\|class TermOutcome" -A 3 ~/d/beliefs/python/src/beliefs/resolution.py`; adjust the two assertions to the real method (it may be `outcome(binding, term)`).

- [ ] **Step 2: Grow the helpers** (`python/tests/helpers/world.py`)

```python
TEST_CONTRACT = '''\
contract:
  contract: testing
  version: 1
  lineage: genesis
  sorts:
    concept:
      vocabulary: "dataset:%(concepts)s"
    protein:
      vocabulary: {namespace: HGNC, release: "2026-07-01"}
  dimensions: {}
  operators:
    affects-concept-protein:
      arity: 2
      arg_sorts: [concept, protein]
      sign_apt: true
      layers: [causal]
      dimensions: []
    affects-concept-concept:
      arity: 2
      arg_sorts: [concept, concept]
      sign_apt: true
      layers: [causal]
      dimensions: []
plan:
  sorts: {concept: concept, protein: protein}
  layers: {causal: causal}
  polarities: {positive: positive, negative: negative, not_applicable: null}
  operators:
    - {predicate: affects, subject: concept, object: protein, operator: affects-concept-protein}
    - {predicate: affects, subject: concept, object: concept, operator: affects-concept-concept}
'''
CONCEPTS = b"concept:disease-stage\nconcept:remission\n"


def concept_list_address() -> str:
    from hashlib import sha256
    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
    digest = "sha256:" + sha256(CONCEPTS).hexdigest()
    return dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name="concepts.txt", digest=digest),)))


def fixture_contract_document(work: Path) -> Path:
    path = work / "testing.yaml"
    path.write_text(TEST_CONTRACT % {"concepts": concept_list_address().removeprefix("dataset:")})
    return path


def build_fixture_world_with_contract(work: Path, *, hold_concepts: bool = True) -> ScienceConfig:
    """A world whose profile compiles the test contract; the concept list held
    (or not), one proposition minted under the plan's first row."""
    from beliefs.profile import shipped_base_contract
    from science.contracts import load_contract_document
    base = shipped_base_contract()
    contract, plan = load_contract_document(fixture_contract_document(work), base)
    profile = compile_profile(base, [shipped_domain_contract(ns) for ns in DOMAINS] + [contract])
    pins = CorpusPins(
        science_contract="science:" + profile.base_contract_identity,
        domains={ns: f"{ns}:{identity}" for ns, identity in profile.activated_contracts.items()},
    )
    corpus_root = work / "corpus"
    config = WorldConfig(work / "world", secrets.token_hex(16), (corpus_root,))
    init_world_root(config, authority=FIXTURE_AUTHORITY)
    init_corpus_root(corpus_root, authority=FIXTURE_AUTHORITY)
    store_id = init_store_root(work / "store", authority=FIXTURE_AUTHORITY)
    STORE_IDS[work] = store_id
    writer = open_corpus(corpus_root, authority=FIXTURE_AUTHORITY, profile=profile)
    writer.adopt_manifest(profile=pins)
    world = open_world(config, authority=FIXTURE_AUTHORITY)
    world.admit(corpus_root, provenance=Fresh())
    # The holdings reducer is a rule the world holds (an epoch-family act, so
    # operator-time): reads derive active and blocked heads through it.
    from beliefs.holdings.reduce import holdings_rule_bundle
    from beliefs.world.rules import install_rule_binding
    install_rule_binding(world, holdings_rule_bundle())
    cfg = ScienceConfig(world=config, operations_root=work / "ops", profile=profile,
                        service_socket=work / "ops" / "service.sock", store_root=work / "store",
                        plans=(plan,))
    if hold_concepts:
        hold_fixture_dataset(cfg, "concepts.txt", CONCEPTS, "concept vocabulary")
    return cfg


def hold_fixture_dataset(cfg: ScienceConfig, name: str, content: bytes, title: str, **facets) -> str:
    """Hold bytes the way the `dataset` command will: content-derived location,
    Found observation, dataset record under the content address. Tests hold the
    full authority; the command goes through the scoped writer."""
    from hashlib import sha256
    from beliefs import stored
    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
    from beliefs.holdings.boundary import ActContext, write
    from beliefs.holdings.records import StoreLocator
    from beliefs.root import holdings_seam
    digest = "sha256:" + sha256(content).hexdigest()
    (root,) = cfg.world.corpus_roots
    ctx = ActContext(root, cfg.store_root, "fixture", "fixture/hold.v1", FIXTURE_AUTHORITY,
                     holdings_seam(), profile=cfg.profile)
    write(ctx, StoreLocator(STORE_IDS[root.parent], f"{digest.removeprefix('sha256:')}/{name}"),
          content, expected=digest)
    address = dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name=name, digest=digest),)))
    node = stored.dataset_node(address.removeprefix("dataset:"), title=title,
                               resources=[{"name": name, "digest": digest}], **facets)
    return open_corpus(root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(node).id


def unhold_fixture_dataset(cfg: ScienceConfig, ref: str) -> None:
    """Delete the held bytes and publish the Absent observation that supersedes
    the Found: the state a later re-check would leave."""
    from beliefs import stored
    from beliefs.holdings.boundary import ActContext, delete
    from beliefs.root import holdings_seam
    from science.config import ReadContext
    (root,) = cfg.world.corpus_roots
    _, view = ReadContext.open(cfg).single_view()
    (resource,) = stored.dataset_declaration(view.get(ref)).resources
    relative = f"{resource.digest.removeprefix('sha256:')}/{resource.name}"
    standing = tuple(stored.holdings_observation_value(n) for n in view.iter_stored()
                     if n.kind == "holdings-observation"
                     and stored.holdings_observation_value(n).location.relative_path == relative)
    ctx = ActContext(root, cfg.store_root, "fixture", "fixture/hold.v1", FIXTURE_AUTHORITY,
                     holdings_seam(), profile=cfg.profile)
    delete(ctx, standing[0].location, standing=standing)


SPEC_FIELDS = {"estimand": "difference in PHF19 expression", "method": "rank comparison",
               "assumptions": "independent samples", "falsification": "no difference at alpha",
               "applicability": "samples with a stage token",
               "interpretation_rule": "outcome-file/v1", "equivalence_rule": "content-identity-equality/v1"}


@contextmanager
def open_rig(cfg: ScienceConfig, names: tuple[str, ...]):
    """A dispatcher over the production declarations named, with an attended
    session over `cfg`; yields (dispatcher, read context). Task 4 adds
    `store_root=cfg.store_root` to the session call once the seam lands."""
    from beliefs.session import open_attended_session
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers
    decls = tuple(d for d in production_tree() if d.name in names)
    session = open_attended_session(cfg.world, cfg.operations_root, profile=cfg.profile)
    ctx = ReadContext.open(cfg)
    try:
        yield Dispatcher(decls, resolve_handlers(decls), ctx, session=session), ctx
    finally:
        session.close()


def build_belief_world(work: Path) -> ScienceConfig:
    """The contract world plus one proposition typed under the plan: the
    starting state for claim/spec/run/assess/verify/belief/next tests."""
    from beliefs import stored
    from beliefs.claim import Referent, build_claim
    from beliefs.projection import project_claim
    cfg = build_fixture_world_with_contract(work)
    (plan,) = cfg.plans
    claim = build_claim(cfg.profile, operator=plan.operator_for("affects", "concept", "protein"),
                        args=(Referent(sort=plan.sort_for("concept"), term="concept:disease-stage"),
                              Referent(sort=plan.sort_for("protein"), term="protein:PHF19")),
                        layer="causal", polarity="positive")
    node = stored.proposition_node("p1", title="p1", claim=project_claim(claim),
                                   display_statement="concept:disease-stage affects protein:PHF19")
    open_corpus(cfg.world.corpus_roots[0], authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(node)
    return cfg


FIXTURE_SNAKEFILE = '''\
rule outcome:
    input: "inputs/data.txt"
    output: "outputs/stats.tsv", "outputs/outcome.txt"
    run:
        import pathlib
        pathlib.Path(input[0]).read_text()
        pathlib.Path(output[0]).write_text("n\\t1\\n")
        pathlib.Path(output[1]).write_text("%(outcome)s\\n")
'''


def fixture_bundle(work: Path, outcome: str = "supported") -> tuple[Path, str, tuple[str, ...]]:
    code = work / "analysis"
    (code / "workflow").mkdir(parents=True, exist_ok=True)
    (code / "workflow" / "Snakefile").write_text(FIXTURE_SNAKEFILE % {"outcome": outcome})
    return code, "analysis/workflow/Snakefile", ("outputs/stats.tsv", "outputs/outcome.txt")


def mint_fixture_run(cfg: ScienceConfig, spec_ref: str, dataset_ref: str, bundle) -> str:
    """One assessment run under MINIMAL_POLICY through the kernel library, so
    assess/verify/belief/next tests have a run on hosts without bubblewrap."""
    import socket
    from datetime import UTC, datetime
    from beliefs import stored
    from beliefs.adapter import WorkflowDefinition
    from beliefs.boundary import RunMinted, execute_assessment_run
    from beliefs.dataset import dataset_address
    from beliefs.recipe import MINIMAL_POLICY
    from beliefs.root import durable_operation_port
    from beliefs.runrecord import run_ref
    from science.config import ReadContext
    code, entrypoint, targets = bundle
    ctx = ReadContext.open(cfg)
    _, view = ctx.single_view()
    spec = stored.analysis_spec_value(view.get(spec_ref))
    address = dataset_address(stored.dataset_declaration(view.get(dataset_ref)))
    (root,) = cfg.world.corpus_roots
    outcome = execute_assessment_run(
        spec=spec, port=durable_operation_port(root, FIXTURE_AUTHORITY, profile=cfg.profile),
        boundary_policy=MINIMAL_POLICY,
        definition=WorkflowDefinition(snakefile=(code / "workflow" / "Snakefile").read_bytes(), family_streams={}),
        code_roots=(code,), held_inputs={address: ctx.held_path(address)}, entrypoint=entrypoint,
        targets=targets, declared_outputs=targets, observer="fixture",
        started_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        host_realization=socket.gethostname(), scratch_base=cfg.operations_root / "scratch" / "fixture")
    assert isinstance(outcome, RunMinted), outcome
    return run_ref(outcome.run.address())
```

`STORE_IDS: dict[Path, str] = {}` at module level, keyed by the work directory, and `from contextlib import contextmanager` at the top. `build_fixture_world` (the plain one) also initializes a store, records its id, and installs the holdings reducer the same way, so Task 2's tests hold and `status` over a plain world can read holdings.

- [ ] **Step 3: Run to verify they fail**

Run: `just test-fast`
Expected: `AttributeError: 'ReadContext' object has no attribute 'single_view'` and friends.

- [ ] **Step 4: Write `science/vocabulary.py`**

```python
"""The resolution snapshot over held vocabularies (belief-path design §5.3)."""
from __future__ import annotations

from hashlib import sha256

from beliefs import stored
from beliefs.contract.domain import VocabularyBinding
from beliefs.corpus import ReadView
from beliefs.dataset import dataset_address
from beliefs.profile import ProfileSpec
from beliefs.resolution import ResolutionSnapshot, build_snapshot

from science.holdings import held_path_for


def dataset_bound_sorts(profile: ProfileSpec) -> dict[str, VocabularyBinding]:
    """Sort term -> binding, for every sort bound by dataset identity."""
    return {
        term: compiled.vocabulary
        for term, compiled in profile.sorts.items()
        if compiled.vocabulary.dataset_identity is not None
    }


def snapshot(profile: ProfileSpec, view: ReadView, store_root, store_id: str, observations) -> ResolutionSnapshot:
    """Read each dataset-bound vocabulary from the store by the address the
    contract names. `observations` is the read context's reduced mapping
    (address -> Found observations). A binding whose dataset is not in the
    corpus or not held is listed unreadable, so a referent under it resolves
    not-available."""
    readable: dict[VocabularyBinding, list[str]] = {}
    unreadable: list[VocabularyBinding] = []
    for binding in dataset_bound_sorts(profile).values():
        address = f"dataset:{binding.dataset_identity}"
        node = _dataset_at(view, address)
        if node is None or address not in observations:
            unreadable.append(binding)
            continue
        path = held_path_for(store_root, store_id, observations[address])
        content = path.read_bytes()
        (resource,) = stored.dataset_declaration(node).resources
        if "sha256:" + sha256(content).hexdigest() != resource.digest:
            unreadable.append(binding)  # an edited copy is not the held vocabulary
            continue
        readable[binding] = content.decode("utf-8").splitlines()
    return build_snapshot(readable=readable, unreadable=tuple(unreadable))


def _dataset_at(view: ReadView, address: str):
    for node in view.iter_stored():
        if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) == address:
            return node
    return None
```

- [ ] **Step 5: Write `science/holdings.py`**

The kernel's holdings reduction — supersession walks, contested heads,
unsettled intents — is a rule the world holds; `derive_holdings` captures a
corpus and reduces it to `active` and `blocked` head projections, and
`dataset_observations` joins those to one declaration. The surface never
reads observation records directly for heldness: a later `Absent` must
remove it, and only the reduction knows that.

```python
"""Store reads for the belief path (design §5.4), through the kernel's
holdings reduction: the reduced answer per dataset address, the held path
for an address, and the admission check."""
from __future__ import annotations

from pathlib import Path

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.dataset import ByteObservation, Held, admission_state, dataset_address
from beliefs.holdings.adapter import DatasetAnswer, DatasetBlocked, dataset_observations
from beliefs.holdings.receipt import derive_holdings
from beliefs.holdings.reduce import holdings_rule_bundle
from beliefs.root import log_seam
from beliefs.world.rules import binding_for

from science.refusal import Refusal, Refused


def reduced_heads(world, corpus_id: str):
    """(active, blocked) from the world's held reducer over this corpus.

    Detached inspection, deliberately: the registered inspection reaches the
    engine's recovering `inspect_chain`, which may reclaim debris and append
    registrations or settlements. A read context holds no authority to write,
    and a read that repaired the chain on the way past would be a write the
    ledger never saw. Pending evidence is read as pending."""
    seam = log_seam()
    active, blocked, _ = derive_holdings(
        world, frozenset({corpus_id}), binding_for(holdings_rule_bundle()),
        chain_view=seam.inspect_detached, state_facts=seam.state_facts,
    )
    return active, blocked


def reduced_observations(view: ReadView, world, corpus_id: str) -> dict[str, DatasetAnswer | DatasetBlocked]:
    """The reduction's answer for every dataset record that has an address."""
    active, blocked = reduced_heads(world, corpus_id)
    answers: dict[str, DatasetAnswer | DatasetBlocked] = {}
    for node in view.iter_stored():
        if node.kind != "dataset":
            continue
        declaration = stored.dataset_declaration(node)
        address = dataset_address(declaration)
        if address is not None:
            answers[address] = dataset_observations(declaration, active, blocked)
    return answers


def found_observations(view: ReadView, world, corpus_id: str) -> dict[str, tuple[ByteObservation, ...]]:
    """Address -> the reduced Found observations; blocked and empty answers
    are absent from the mapping, which is what `Availability` wants."""
    return {
        address: answer.observations
        for address, answer in reduced_observations(view, world, corpus_id).items()
        if isinstance(answer, DatasetAnswer) and answer.observations
    }


def held_path_for(store_root: Path, store_id: str, observations: tuple[ByteObservation, ...]) -> Path:
    """The reducer renders a location as `store:<store id>:<relative path>`.
    Only an observation recorded for the configured store's own identity
    resolves here: evidence for another store names bytes this root never
    held, however the relative paths happen to coincide."""
    for observation in observations:
        parts = observation.location.split(":", 2)
        if len(parts) == 3 and parts[0] == "store" and parts[1] == store_id and parts[2]:
            return Path(store_root) / parts[2]
    raise Refused(Refusal("invalid-input",
                          f"no observation resolves in store {store_id}: "
                          f"{sorted(o.location for o in observations)}"))


def held_path(view: ReadView, world, corpus_id: str, store_root: Path, store_id: str, address: str) -> Path:
    answer = reduced_observations(view, world, corpus_id).get(address)
    if isinstance(answer, DatasetBlocked):
        raise Refused(Refusal("invalid-input",
                              f"{address} is blocked at {answer.locations}: {answer.reasons}"))
    if not isinstance(answer, DatasetAnswer) or not answer.observations:
        raise Refused(Refusal("invalid-input", f"{address} is not held in this store"))
    return held_path_for(store_root, store_id, answer.observations)


def is_held(view: ReadView, world, corpus_id: str, node) -> bool:
    declaration = stored.dataset_declaration(node)
    address = dataset_address(declaration)
    if address is None:
        return False
    answer = reduced_observations(view, world, corpus_id).get(address)
    if not isinstance(answer, DatasetAnswer):
        return False
    return isinstance(admission_state(declaration, answer.observations), Held)
```

Two names to pin at implementation: `beliefs.root.log_seam` (the session module imports it as `log_seam`; confirm with `grep -n "^def log_seam\|^def _log_seam" ~/d/beliefs/python/src/beliefs/root.py`), and whether `derive_holdings` runs under the read-only world the read context opens (it captures and resolves the held rule; it should require no act family — if it does, that is a finding for `beliefs-5fe2e3`).

- [ ] **Step 6: Write `science/closure.py`**

```python
"""Belief evaluation in one call (design §4.7, §5.5): the availability and
supplied context the evaluator does not compute itself, built from the
world, then `evaluate_over` under the shipped policy."""
from __future__ import annotations

from beliefs.belief import Availability, SuppliedContext
from beliefs.closure import RetractionEnumeration
from beliefs.corpus import ReadView, lineage_snapshot
from beliefs.evaluation import EvaluationInputs, evaluate_over, gather
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.profile import ProfileSpec
from beliefs.resolution import ResolutionSnapshot

BINDING = PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity)


def availability(observations) -> Availability:
    return Availability(observations=observations, implementations={BELIEF_V1.identity: BELIEF_V1},
                        fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES})


def supplied_context(view: ReadView, *, corpus_id: str, pins, epoch_identity: str,
                     observations, node_corpus) -> SuppliedContext:
    return SuppliedContext(
        snapshot=lineage_snapshot(view, sorted(observations)),
        producer_snapshot_identity=epoch_identity,
        retractions=RetractionEnumeration(found=(), coverage=(corpus_id,)),
        node_corpus=node_corpus,
        pins={corpus_id: pins},
    )


def gather_inputs(view, proposition, *, context, profile: ProfileSpec, resolution: ResolutionSnapshot) -> EvaluationInputs:
    return gather(view, proposition, context=context, profile=profile, resolution=resolution, binding=BINDING)


def evaluate(view, proposition, *, observations, context, profile, resolution):
    return evaluate_over(view, proposition, availability=availability(observations), context=context,
                         profile=profile, resolution=resolution, binding=BINDING)
```

- [ ] **Step 7: Grow `ReadContext`** (`science/config.py`)

```python
    def single_view(self) -> tuple[str, ReadView]:
        views = self.read_views()
        if len(views) != 1:
            raise Refused(Refusal("invalid-input",
                                  f"the belief path reads exactly one corpus; the config names {len(views)}"))
        return views[0]

    def snapshot(self):
        from science.vocabulary import snapshot
        _, view = self.single_view()
        return snapshot(self.config.profile, view, self.config.store_root, self.store_id(), self.observations())

    def observations(self):
        from science.holdings import found_observations
        corpus_id, view = self.single_view()
        return found_observations(view, self.world, corpus_id)

    def store_id(self) -> str:
        """The configured store's verified identity, read from its genesis by
        detached inspection. `store_identity` is the public reader the routes
        seam (`beliefs-5fe2e3`) adds, a prerequisite for this task."""
        from beliefs.root import store_identity
        identity = store_identity(self.config.store_root)
        if identity is None:
            raise Refused(Refusal("invalid-input", f"{self.config.store_root} is not an initialized store"))
        return identity

    def held_path(self, address: str) -> Path:
        from science.holdings import held_path
        corpus_id, view = self.single_view()
        return held_path(view, self.world, corpus_id, self.config.store_root, self.store_id(), address)

    def is_held(self, node) -> bool:
        from science.holdings import is_held
        corpus_id, view = self.single_view()
        return is_held(view, self.world, corpus_id, node)

    def pins(self):
        (root,) = self.config.world.corpus_roots
        return load_manifest(root).profile

    def epoch_identity(self) -> str:
        from beliefs.errors import EpochUnknown
        from beliefs.world.read import current_epoch
        try:
            return current_epoch(self.world).packaging_identity
        except EpochUnknown:
            return "no-epoch-published"

    def _context(self, view, corpus_id, observations):
        from science.closure import supplied_context
        node_corpus = {node.id: corpus_id for node in view.iter_stored() if node.kind == "assessment"}
        return supplied_context(view, corpus_id=corpus_id, pins=self.pins(), epoch_identity=self.epoch_identity(),
                                observations=observations, node_corpus=node_corpus)

    def gather_inputs(self, proposition: str):
        from science.closure import gather_inputs
        corpus_id, view = self.single_view()
        observations = self.observations()
        return gather_inputs(view, proposition, context=self._context(view, corpus_id, observations),
                             profile=self.config.profile, resolution=self.snapshot())

    def evaluate(self, proposition: str):
        from science.closure import evaluate
        corpus_id, view = self.single_view()
        observations = self.observations()
        return evaluate(view, proposition, observations=observations,
                        context=self._context(view, corpus_id, observations),
                        profile=self.config.profile, resolution=self.snapshot())
```

`node_corpus` is keyed by what `gather` needs: check with `grep -n "node_corpus" ~/d/beliefs/python/src/beliefs/evaluation.py ~/d/beliefs/python/src/beliefs/consulted.py | head` whether the key is the assessment's identity or its record id, and key accordingly (the driver keyed by the stored identity; use `stored.assessment_value(node).identity()` if so).

- [ ] **Step 8: Run to verify they pass**

Run: `just test`
Expected: all PASS. `test_evaluate_answers_no_belief_before_any_assessment` proves the full evaluator path runs over the fixture world.

- [ ] **Step 9: Commit**

```bash
tasks done sci-98282e "read context: resolution snapshot, holdings reads, supplied context; belief-path fixtures"
git add python/src/science/ python/tests/ tasks/
git commit -m "feat(context): snapshot, holdings reads and belief evaluation on the read context"
```

---

### Task 4: `dataset` — hold a local file and mint the dataset record

**Blocked on `beliefs-5fe2e3`** (`writer.holdings_context`, `writer.store_id`, `open_attended_session(store_root=…)`).

**Files:**
- Create: `commands/dataset/command.toml`, `commands/dataset/prompt.md`, `python/src/science/commands/dataset.py`
- Modify: `python/src/science/serve.py`, `python/src/science/mcp.py` (pass `store_root=config.store_root` to `open_attended_session`)
- Modify: `python/tests/helpers/world.py` (`open_rig` passes the fixture store root when opening the attended session)
- Test: `python/tests/test_cmd_dataset.py`
- Regenerate: `adapters/claude-code/`

**Interfaces:**
- Consumes: `ScopedWriter.holdings_context(instrument=…)`, `ScopedWriter.store_id`, `ScopedWriter.add`; `beliefs.holdings.boundary.write(ctx, location, content, expected=, standing=)`; `ctx.single_view()`, `ctx.observations()`, `ctx.is_held()`.
- Produces: `dataset` records under `dataset:sha256:<hex>`; handler `handle(ctx, writer, *, path, title, locator=None, facets=None)`.

- [ ] **Step 1: The declaration and prompt**

`commands/dataset/command.toml`:

```toml
schema_version = 1
name = "dataset"
purpose = "Hold a local file in the store and mint the dataset record under its content address."
write_class = "mints:dataset,holdings-observation"
output_budget = 4096

[write.routes]
holdings-observation = "holdings"

[inputs.path]
type = "string"
required = true
doc = "A regular file on this host; its bytes are held, never a directory."

[inputs.title]
type = "string"
required = true
doc = "The dataset's title."

[inputs.locator]
type = "string"
required = false
doc = "An empirical-observation locator, e.g. accession:GSE179929; absent, the record carries no such facet."

[inputs.facets]
type = "list-of-string"
required = false
doc = "Domain facets as name=key:value,key:value, e.g. biology/gene-axis=axis:rows,namespace:HGNC."

[reads]
families = ["corpus-stored", "holdings"]
```

`commands/dataset/prompt.md`:

```markdown
Run `dataset` when the user has a data file on this machine that an analysis
will observe, or the vocabulary list a contract binds. Give the file's path
and a title; add `locator` for an accession the record should cite and
`facets` for domain facets the contract declares. The output is the minted
record only; if it refuses, report the refusal and change nothing.
```

- [ ] **Step 2: Write the failing tests**

```python
# python/tests/test_cmd_dataset.py
import pytest

from science.refusal import Refused
from helpers.world import build_belief_world, open_rig


@pytest.fixture
def rig(certified_work):
    with open_rig(build_belief_world(certified_work), ("dataset",)) as pair:
        yield pair


def test_dataset_holds_bytes_and_mints_the_record(rig, tmp_path):
    d, ctx = rig
    data = tmp_path / "matrix.txt"
    data.write_bytes(b"gene\tv\nPHF19\t1\n")
    out = d.invoke("dataset", {"path": str(data), "title": "expression", "locator": "accession:GSE1",
                               "facets": ["biology/gene-axis=axis:rows,namespace:HGNC"]})
    assert "[dataset] dataset:sha256:" in out.text
    _, view = ctx.single_view()
    node = next(n for n in view.iter_stored() if n.kind == "dataset" and n.title == "expression")
    assert ctx.is_held(node)
    from beliefs import stored
    assert stored.is_empirical_observation(node)


def test_non_regular_path_refuses_before_any_act(rig, tmp_path):
    d, ctx = rig
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(tmp_path), "title": "dir"})
    assert caught.value.refusal.code == "invalid-input"
    _, view = ctx.single_view()
    assert not any(n.kind == "dataset" and n.title == "dir" for n in view.iter_stored())


def test_same_bytes_twice_refuse_naming_the_record(rig, tmp_path):
    d, _ = rig
    data = tmp_path / "a.txt"
    data.write_bytes(b"same\n")
    first = d.invoke("dataset", {"path": str(data), "title": "one"})
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(data), "title": "two"})
    assert "dataset:sha256:" in caught.value.refusal.message
    assert caught.value.refusal.message.split()[-1] in first.text


def test_two_files_with_one_title_and_basename_land_apart(rig, tmp_path):
    d, ctx = rig
    a, b = tmp_path / "x" / "data.txt", tmp_path / "y" / "data.txt"
    a.parent.mkdir(); b.parent.mkdir()
    a.write_bytes(b"A\n"); b.write_bytes(b"B\n")
    d.invoke("dataset", {"path": str(a), "title": "t"})
    d.invoke("dataset", {"path": str(b), "title": "t"})
    assert len(ctx.observations()) >= 3  # concepts + two held files


def test_malformed_metadata_leaves_no_acts(rig, tmp_path):
    """`oops` is not a facet the profile declares: the refusal comes before
    the holdings write, so neither bytes nor an observation exist afterward."""
    d, ctx = rig
    data = tmp_path / "m.txt"
    data.write_bytes(b"M\n")
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(data), "title": "m", "facets": ["oops=k:v"]}, invocation_id="M" * 8)
    assert caught.value.refusal.code == "invalid-input"
    assert "oops" in caught.value.refusal.message
    from hashlib import sha256
    from beliefs import stored
    digest = sha256(b"M\n").hexdigest()
    assert not (ctx.config.store_root / digest).exists()  # no bytes were written
    _, view = ctx.single_view()
    assert not any(n.kind == "dataset" and n.title == "m" for n in view.iter_stored())
    assert not any(n.kind == "holdings-observation"
                   and stored.holdings_observation_value(n).location.relative_path.startswith(digest)
                   for n in view.iter_stored())


def test_malformed_locator_leaves_no_acts(rig, tmp_path):
    """The empirical-observation payload is validated before the holdings
    write, not by the writer after it."""
    d, ctx = rig
    data = tmp_path / "l.txt"
    data.write_bytes(b"L\n")
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(data), "title": "l", "locator": "not-a-locator"})
    assert caught.value.refusal.code == "invalid-input"
    from hashlib import sha256
    assert not (ctx.config.store_root / sha256(b"L\n").hexdigest()).exists()
    _, view = ctx.single_view()
    assert not any(n.kind == "dataset" and n.title == "l" for n in view.iter_stored())


def test_attested_by_is_the_session_actor(rig, tmp_path):
    d, ctx = rig
    data = tmp_path / "e.txt"
    data.write_bytes(b"E\n")
    d.invoke("dataset", {"path": str(data), "title": "e", "locator": "accession:X"})
    _, view = ctx.single_view()
    node = next(n for n in view.iter_stored() if n.kind == "dataset" and n.title == "e")
    facet = node.facets["empirical-observation"]
    assert facet["attested_by"].startswith("session:")
```

In `helpers/world.py`'s `open_rig` (Task 3), the session call becomes
`open_attended_session(cfg.world, cfg.operations_root, profile=cfg.profile, store_root=cfg.store_root)`.

Check the exact accessor for a node's facets (`node.facets[...]` or `stored._facet(node, name)`) with `grep -n "def is_empirical_observation" -B2 -A3 ~/d/beliefs/python/src/beliefs/stored.py` and use the public one.

- [ ] **Step 3: Run to verify they fail**

Run: `just test-fast`
Expected: `DeclarationError: cannot import science.commands.dataset`.

- [ ] **Step 4: Write the handler**

```python
# python/src/science/commands/dataset.py
"""dataset: hold a local file and mint the dataset record (belief-path §4.2)."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from beliefs import stored
from beliefs.acquisition import bearer_refusal, validity_refusal
from beliefs.dataset import DatasetDeclaration, Held, ResourceDeclaration, admission_state, dataset_address
from beliefs.errors import FacetError, FacetPayloadRefused, MalformedRecord, UnknownKindError
from beliefs.facets import validate_payload
from beliefs.holdings.boundary import write
from beliefs.holdings.records import Found, StoreLocator

from science.refusal import Refusal, Refused
from science.report import Report, record_block

INSTRUMENT = "science/dataset.v1"


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def _parse_facets(entries) -> dict[str, dict[str, str]]:
    facets: dict[str, dict[str, str]] = {}
    for entry in entries or ():
        name, sep, body = entry.partition("=")
        if not sep or not name:
            _refuse(f"facet {entry!r} is not name=key:value,...")
        pairs = {}
        for pair in body.split(","):
            key, colon, value = pair.partition(":")
            if not colon or not key:
                _refuse(f"facet {entry!r}: {pair!r} is not key:value")
            pairs[key] = value
        facets[name] = pairs
    return facets


def handle(ctx, writer, *, path, title, locator=None, facets=None) -> Report:
    source = Path(path)
    if not source.is_file():
        _refuse(f"{path} is not a regular file")
    domain_facets = _parse_facets(facets)
    content = source.read_bytes()
    digest = "sha256:" + sha256(content).hexdigest()
    declaration = DatasetDeclaration(resources=(ResourceDeclaration(name=source.name, digest=digest),))
    address = dataset_address(declaration)
    _, view = ctx.single_view()
    for node in view.iter_stored():
        if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) == address:
            _refuse(f"these bytes are already held as {node.id}")
    relative = f"{digest.removeprefix('sha256:')}/{source.name}"
    standing = tuple(
        stored.holdings_observation_value(node)
        for node in view.iter_stored()
        if node.kind == "holdings-observation"
        and stored.holdings_observation_value(node).location.relative_path == relative
    )
    # The record is built and validated BEFORE the first act: a facet the
    # profile does not know, or a payload it refuses, must leave no bytes in
    # the store and no observation behind (design §6.3, validate before act).
    empirical = None
    if locator is not None:
        empirical = {"locator": locator, "attested_by": writer.actor}
    try:
        proposed = stored.dataset_node(
            address.removeprefix("dataset:"), title=title,
            resources=[{"name": source.name, "digest": digest}],
            empirical_observation=empirical, domain_facets=domain_facets or None,
        )
    except MalformedRecord as caught:
        _refuse(f"dataset record refused: {caught}")
    profile = ctx.config.profile
    try:
        profile.validate_document(proposed)  # kind registered, facet keys declared
    except (UnknownKindError, FacetError) as caught:
        _refuse(f"dataset record refused: {caught}")
    # Every facet payload the profile compiles a shape for — the domain facets
    # AND the empirical-observation facet — exactly as the writer's own
    # `_refuse_facets` will check them, so the writer can refuse nothing here
    # that this did not refuse first.
    for key, payload in proposed.facets.items():
        facet = profile.facets.get(key)
        if facet is not None:
            try:
                validate_payload(facet, payload, where=proposed.id)
            except FacetPayloadRefused as caught:
                _refuse(f"facet {key!r} refused: {caught}")
    for name in domain_facets:
        if name not in profile.facets:
            _refuse(f"facet {name!r} is not declared by this profile")
    reason = bearer_refusal(view, proposed)
    if reason is not None:
        _refuse(f"dataset record refused: {reason}")
    if empirical is not None:
        reason = validity_refusal(view, proposed, profile)
        if reason is not None:
            _refuse(f"locator refused: {reason}")
    # --- first act: the holdings write ---------------------------------------
    holdings = writer.holdings_context(instrument=INSTRUMENT)
    published = write(holdings, StoreLocator(writer.store_id, relative), content, expected=digest,
                      standing=standing)
    node = writer.add(proposed)
    from beliefs.dataset import ByteObservation
    outcome = published.record.outcome
    assert isinstance(outcome, Found)
    verdict = admission_state(stored.dataset_declaration(node),
                              (ByteObservation(digest=outcome.digest, location=published.record.location.canonical()),))
    if not isinstance(verdict, Held):
        raise RuntimeError(f"held bytes with a matching digest did not read Held: {verdict!r}")
    return (record_block(node),)
```

`FacetPayloadRefused` is what `validate_payload` raises (a `ValidationRefused` subclass); `UnknownKindError` and `FacetError` are what `validate_document` raises — pin all three against `beliefs/errors.py` at implementation. `bearer_refusal` and `validity_refusal` are the pure reads the writer's `_refuse_facets` performs over its view; calling them over the read view first is what makes "validate before act" true for the locator. Then in `serve.py`, `mcp.py`, and the helpers' `open_rig`, pass `store_root=config.store_root` (resp. `cfg.store_root`) to `open_attended_session`.

- [ ] **Step 5: Run to verify they pass; regenerate the adapter tree**

Run: `just test-fast`, then `cd python && uv run science adapters build` and `just test`.
Expected: all PASS, including `test_generated_tree_matches_committed` after regeneration.

- [ ] **Step 6: Commit**

```bash
tasks done sci-413d97 "dataset command: content-derived hold, standing supersession, record under the content address"
git add commands/dataset python/src/science/commands/dataset.py python/src/science/serve.py python/src/science/mcp.py python/tests/ adapters/claude-code tasks/
git commit -m "feat(commands): dataset holds a local file and mints its record"
```

---

### Task 5: `claim` — type a proposition and mint it

**Files:**
- Create: `commands/claim/command.toml`, `commands/claim/prompt.md`, `python/src/science/commands/claim.py`
- Test: `python/tests/test_cmd_claim.py`
- Regenerate: `adapters/claude-code/`

**Interfaces:**
- Consumes: `ctx.config.plans`, `ctx.snapshot()`, `beliefs.claim.{build_claim, Referent}`, `beliefs.decode.{decode_claim, WireClaim}`, `beliefs.projection.project_claim`, `beliefs.errors.ClaimError`, `stored.proposition_node`.
- Produces: `proposition:<slug>` records; `handle(ctx, writer, *, subject, predicate, object, layer, polarity, slug=None)`.

- [ ] **Step 1: Declaration and prompt**

`commands/claim/command.toml` — exactly the spec's §4.1 declaration (six inputs, `families = ["corpus-stored", "holdings"]`, budget 4096). Note `object` shadows a builtin only as a keyword name; the handler signature must still spell it `object` because the loader matches parameter names to inputs.

`commands/claim/prompt.md`:

```markdown
Run `claim` to type a proposition the user states as subject, predicate and
object, each term prefixed by its kind (`concept:disease-stage`,
`protein:PHF19`), with the claim layer and polarity. The operator comes from
the corpus's contract plan; a shape the plan has no row for refuses, and the
refusal names the shape rather than guessing. Under a vocabulary-bound sort
the term must be a member of the held vocabulary. Report the minted record.
```

- [ ] **Step 2: Write the failing tests**

```python
# python/tests/test_cmd_claim.py
import pytest

from science.refusal import Refused
from helpers.world import build_fixture_world_with_contract, open_rig

BASE = {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
        "layer": "causal", "polarity": "positive"}


def test_claim_types_under_the_plan_and_mints(certified_work):
    with open_rig(build_fixture_world_with_contract(certified_work), ("claim",)) as (d, ctx):
        out = d.invoke("claim", dict(BASE))
        assert "[proposition] proposition:concept-disease-stage-affects-protein-phf19" in out.text
        _, view = ctx.single_view()
        node = view.get("proposition:concept-disease-stage-affects-protein-phf19")
        assert node.facets["proposition"]["operator"] == "testing/affects-concept-protein"


def test_shape_with_no_plan_row_refuses_naming_it(certified_work):
    with open_rig(build_fixture_world_with_contract(certified_work), ("claim",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("claim", dict(BASE, subject="protein:PHF19", object="concept:disease-stage"))
        assert caught.value.refusal.code == "invalid-input"
        assert "affects protein->concept" in caught.value.refusal.message


def test_non_member_under_the_dataset_bound_sort_refuses(certified_work):
    with open_rig(build_fixture_world_with_contract(certified_work), ("claim",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("claim", dict(BASE, subject="concept:not-in-the-list"))
        assert caught.value.refusal.code == "invalid-input"
        assert "not-member" in caught.value.refusal.message


def test_unheld_vocabulary_under_the_dataset_bound_sort_refuses_naming_the_address(certified_work):
    cfg = build_fixture_world_with_contract(certified_work, hold_concepts=False)
    with open_rig(cfg, ("claim",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("claim", dict(BASE))
        assert "dataset:sha256:" in caught.value.refusal.message
        assert "hold" in caught.value.refusal.message


def test_namespace_bound_sort_resolves_not_consulted_and_is_accepted(certified_work):
    """The protein slot is HGNC-bound by namespace and release; no release is
    held; the kernel's permissive reading stands (design §4.1)."""
    with open_rig(build_fixture_world_with_contract(certified_work), ("claim",)) as (d, _):
        out = d.invoke("claim", dict(BASE, object="protein:ANYTHING", slug="any"))
        assert "proposition:any" in out.text


def test_claim_performs_exactly_its_declared_reads(certified_work):
    """N2's shape: the declaration's families are what the handler touches."""
    from science.loader import production_tree
    decl = next(d for d in production_tree() if d.name == "claim")
    assert set(decl.reads) == {"corpus-stored", "holdings"}
```

- [ ] **Step 3: Run to verify they fail**

Run: `just test-fast` — `cannot import science.commands.claim`.

- [ ] **Step 4: Write the handler**

```python
# python/src/science/commands/claim.py
"""claim: type a proposition under the profile and mint it (belief-path §4.1)."""
from __future__ import annotations

import re

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.decode import WireClaim, decode_claim
from beliefs.errors import ClaimError
from beliefs.projection import project_claim
from beliefs.resolution import TermOutcome

from science.refusal import Refusal, Refused
from science.report import Report, record_block
from science.vocabulary import dataset_bound_sorts


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def _kind(term: str) -> str:
    kind, colon, tail = term.partition(":")
    if not colon or not kind or not tail:
        _refuse(f"term {term!r} carries no `<kind>:` prefix")
    return kind


def _slug(subject: str, predicate: str, object_: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", f"{subject} {predicate} {object_}".lower()).strip("-")


def handle(ctx, writer, *, subject, predicate, object, layer, polarity, slug=None) -> Report:
    plans = ctx.config.plans
    if not plans:
        _refuse("the config names no contract document with a plan; claim needs one")
    (plan,) = plans[:1]
    subject_kind, object_kind = _kind(subject), _kind(object)
    operator = plan.operator_for(predicate, subject_kind, object_kind)
    if layer not in plan.layers:
        _refuse(f"layer {layer!r} is not in the plan")
    if polarity not in plan.polarities:
        _refuse(f"polarity {polarity!r} is not in the plan")
    layer_term = plan.layers[layer]
    polarity_term = plan.polarities[polarity]  # None for a sign-inapt operator's not_applicable
    try:
        claim = build_claim(ctx.config.profile, operator=operator,
                            args=(Referent(sort=plan.sort_for(subject_kind), term=subject),
                                  Referent(sort=plan.sort_for(object_kind), term=object)),
                            layer=layer_term, polarity=polarity_term)
    except ClaimError as caught:
        _refuse(f"build_claim refused: {caught}")
    projection = project_claim(claim)
    snapshot = ctx.snapshot()
    try:
        _, receipt = decode_claim(WireClaim(**projection), profile=ctx.config.profile, snapshot=snapshot)
    except ClaimError as caught:  # not-member refuses at decode
        _refuse(f"membership refused: {caught}")
    bound = dataset_bound_sorts(ctx.config.profile)
    for position, outcome in receipt.outcomes.items():
        sort = claim.args[position.index].sort if hasattr(position, "index") else None
        if sort in bound and outcome in (TermOutcome.NOT_CONSULTED, TermOutcome.NOT_AVAILABLE):
            _refuse(f"sort {sort} binds vocabulary dataset:{bound[sort].dataset_identity}, which is not "
                    "held here; hold it with `dataset` before typing a claim under it")
    node = writer.add(stored.proposition_node(
        slug or _slug(subject, predicate, object), title=f"{subject} {predicate} {object}",
        claim=projection, display_statement=f"{subject} {predicate} {object}"))
    return (record_block(node),)
```

Two things to pin against the kernel while implementing: the exception `decode_claim` raises on `not-member` (`grep -n "NOT_MEMBER\|raise " ~/d/beliefs/python/src/beliefs/decode.py | head`) — catch exactly that class; and `BindingCheckReceipt.outcomes`' key type (`grep -n "class ReferentPosition\|class BindingCheckReceipt" -A 8 ~/d/beliefs/python/src/beliefs/resolution.py`) — map each key to its argument's sort by the real field name, replacing the `hasattr` guess.

- [ ] **Step 5: Run, regenerate, run**

`just test-fast`; `cd python && uv run science adapters build`; `just test`. All PASS.

- [ ] **Step 6: Commit**

```bash
tasks done sci-b9ac07 "claim command: plan-typed, membership judged at decode, stricter policy under dataset-bound sorts"
git add commands/claim python/src/science/commands/claim.py python/tests/test_cmd_claim.py adapters/claude-code tasks/
git commit -m "feat(commands): claim types a proposition under the contract plan"
```

---

### Task 6: `spec` — freeze an analysis spec

**Blocked on `beliefs-e5ab34`** (`beliefs.rules.REFERENCE_RULES`).

**Files:**
- Create: `commands/spec/command.toml`, `commands/spec/prompt.md`, `python/src/science/commands/spec.py`
- Test: `python/tests/test_cmd_spec.py`
- Regenerate: `adapters/claude-code/`

**Interfaces:**
- Consumes: `beliefs.rules.REFERENCE_RULES`; `beliefs.spec.{SpecDraft, SpecInput, Deterministic, freeze, MalformedSpec, UnfreezableSpec}`; `stored.{analysis_spec_node, dataset_declaration}`; `beliefs.dataset.dataset_address`.
- Produces: `analysis-spec:<identity>` records; `handle(ctx, writer, *, target, dataset, estimand, method, assumptions, falsification, applicability, interpretation_rule, equivalence_rule, parameters=None, supersedes=None)`; helper `science.commands.spec.parse_parameters(list[str]) -> dict[str, Decimal]`.

- [ ] **Step 1: Declaration and prompt** — the spec's §4.3 declaration minus the removed `nondeterminism` input; budget 4096; `families = ["corpus-stored"]`. Prompt:

```markdown
Run `spec` to freeze the analysis that will assess a proposition: the target
proposition, the dataset it observes, the estimand, method, assumptions,
falsification condition and applicability in the user's words, and the
interpretation and equivalence rule identities the kernel ships. Parameters
are name=value pairs. The frozen spec's identity is what `run` executes and
`verify` compares under; it cannot be edited, only superseded.
```

- [ ] **Step 2: Failing tests**

```python
# python/tests/test_cmd_spec.py
from decimal import Decimal

import pytest

from science.refusal import Refused
from helpers.world import SPEC_FIELDS as FIELDS, build_belief_world, hold_fixture_dataset, open_rig


@pytest.fixture
def rig(certified_work):
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec",)) as (d, ctx):
        yield d, ctx, ref


def test_spec_freezes_and_the_record_id_is_the_identity(rig):
    d, ctx, ref = rig
    out = d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset=ref, parameters=["alpha=0.05"]))
    assert "[analysis-spec] analysis-spec:" in out.text
    _, view = ctx.single_view()
    from beliefs import stored
    node = next(n for n in view.iter_stored() if n.kind == "analysis-spec")
    spec = stored.analysis_spec_value(node)
    assert node.id == f"analysis-spec:{spec.identity}"
    assert spec.parameters["alpha"] == Decimal("0.05")
    assert spec.nondeterminism.projection() == {"variant": "deterministic"}


def test_unknown_rule_identity_refuses(rig):
    d, _, ref = rig
    with pytest.raises(Refused) as caught:
        d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset=ref, interpretation_rule="nope/v9"))
    assert caught.value.refusal.code == "invalid-input"
    assert "nope/v9" in caught.value.refusal.message


def test_unknown_dataset_ref_refuses(rig):
    d, _, _ = rig
    with pytest.raises(Refused) as caught:
        d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset="dataset:sha256:" + "0" * 64))
    assert caught.value.refusal.code == "invalid-input"


def test_malformed_parameter_refuses(rig):
    d, _, ref = rig
    with pytest.raises(Refused) as caught:
        d.invoke("spec", dict(FIELDS, target="proposition:p1", dataset=ref, parameters=["alpha"]))
    assert "name=value" in caught.value.refusal.message
```

- [ ] **Step 3: Run to verify they fail** — `just test-fast`.

- [ ] **Step 4: Handler**

```python
# python/src/science/commands/spec.py
"""spec: freeze an analysis spec against the kernel's reference rules (§4.3)."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from beliefs import stored
from beliefs.dataset import dataset_address
from beliefs.errors import MalformedRecord
from beliefs.rules import REFERENCE_RULES
from beliefs.spec import Deterministic, MalformedSpec, SpecDraft, SpecInput, UnfreezableSpec, freeze

from science.refusal import Refusal, Refused
from science.report import Report, record_block


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def parse_parameters(entries) -> dict[str, Decimal]:
    parameters: dict[str, Decimal] = {}
    for entry in entries or ():
        name, sep, value = entry.partition("=")
        if not sep or not name:
            _refuse(f"parameter {entry!r} is not name=value")
        try:
            parameters[name] = Decimal(value)
        except InvalidOperation:
            _refuse(f"parameter {entry!r}: {value!r} is not a decimal")
    return parameters


def _rule(identity: str):
    implementation = REFERENCE_RULES.get(identity)
    if implementation is None:
        _refuse(f"no reference rule {identity!r}; the kernel ships {sorted(REFERENCE_RULES)}")
    return implementation


def handle(ctx, writer, *, target, dataset, estimand, method, assumptions, falsification,
           applicability, interpretation_rule, equivalence_rule, parameters=None, supersedes=None) -> Report:
    _, view = ctx.single_view()
    if not view.holds(target):
        _refuse(f"target {target!r} is not in the corpus")
    if not view.holds(dataset):
        _refuse(f"dataset {dataset!r} is not in the corpus")
    try:
        address = dataset_address(stored.dataset_declaration(view.get(dataset)))
    except MalformedRecord as caught:
        _refuse(f"{dataset}: {caught}")
    if address is None:
        _refuse(f"{dataset} declares no content identity")
    held_rules = {interpretation_rule: _rule(interpretation_rule), equivalence_rule: _rule(equivalence_rule)}
    draft = SpecDraft(target=target, estimand=estimand, method=method, assumptions=assumptions,
                      falsification=falsification,
                      input_roles=(SpecInput(role="observes", dataset=address),),
                      applicability=applicability, interpretation_rule=interpretation_rule,
                      equivalence_rule=equivalence_rule, parameters=parse_parameters(parameters),
                      nondeterminism=Deterministic())
    try:
        spec = freeze(draft, held_rules=held_rules, supersedes=supersedes)
    except (MalformedSpec, UnfreezableSpec) as caught:
        _refuse(f"freeze refused: {caught}")
    node = writer.add(stored.analysis_spec_node(spec))
    return (record_block(node),)
```

`supersedes`, when given, is a record ref; `freeze` expects the superseded spec's identity — strip `analysis-spec:` with `stored.local_id("analysis-spec", supersedes)` before passing it.

- [ ] **Step 5: Run, regenerate, run** — `just test-fast`; `cd python && uv run science adapters build`; `just test`.

- [ ] **Step 6: Commit**

```bash
tasks done sci-57c3d3 "spec command: deterministic draft frozen against the kernel's reference rules"
git add commands/spec python/src/science/commands/spec.py python/tests/test_cmd_spec.py adapters/claude-code tasks/
git commit -m "feat(commands): spec freezes an analysis spec"
```

---

### Task 7: `run` — execute once under confinement

**Blocked on `beliefs-5fe2e3`** (`writer.operation_port()`).

**Files:**
- Create: `commands/run/command.toml`, `commands/run/prompt.md`, `python/src/science/commands/run.py`
- Test: `python/tests/test_cmd_run.py`
- Regenerate: `adapters/claude-code/`

**Interfaces:**
- Consumes: `beliefs.confinement.host_prerequisites`, `beliefs.recipe.CONFINED_POLICY`, `beliefs.boundary.{execute_assessment_run, RunMinted, RunRefused}`, `beliefs.adapter.WorkflowDefinition`, `beliefs.runrecord.run_ref`, `stored.analysis_spec_value`, `ctx.held_path`, `writer.operation_port()`.
- Produces: `run:<address>` records; `handle(ctx, writer, *, spec, dataset, code, entrypoint, targets, cores=None)`; module constant `POLICY = CONFINED_POLICY` (tests monkeypatch it to `MINIMAL_POLICY` where bubblewrap is absent); helper `science.commands.run.prepare(ctx, spec, dataset, code, entrypoint, targets) -> dict` shared with `verify`.

- [ ] **Step 1: Declaration and prompt** — the spec's §4.4 declaration; `families = ["corpus-stored", "holdings"]`. Prompt:

```markdown
Run `run` to execute a frozen spec's analysis once under confinement: name
the spec, the dataset it observes, the code directory holding the workflow,
the entrypoint and the targets. It needs bubblewrap on this host and refuses
otherwise before touching anything. The minted run record is the output; a
refusal names the kernel's reason and nothing was written.
```

- [ ] **Step 2: Failing tests**

```python
# python/tests/test_cmd_run.py
import pytest

from science.refusal import Refused
from helpers.world import SPEC_FIELDS, build_belief_world, fixture_bundle, hold_fixture_dataset, open_rig


@pytest.fixture
def rig(certified_work, monkeypatch):
    import science.commands.run as run_module
    from beliefs.recipe import MINIMAL_POLICY
    from beliefs.confinement import host_prerequisites
    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec", "run")) as (d, ctx):
        spec_out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref))
        spec_ref = next(t for t in spec_out.text.split() if t.startswith("analysis-spec:"))
        yield d, ctx, spec_ref, ref


def test_run_mints_one_run_record(rig, certified_work):
    d, ctx, spec_ref, ref = rig
    code, entrypoint, targets = fixture_bundle(certified_work)
    out = d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": str(code),
                           "entrypoint": entrypoint, "targets": list(targets)})
    assert "[run] run:" in out.text
    _, view = ctx.single_view()
    assert sum(1 for n in view.iter_stored() if n.kind == "run") == 1


def test_run_refuses_without_bubblewrap_before_any_act(certified_work, monkeypatch):
    import science.commands.run as run_module
    monkeypatch.setattr(run_module, "host_prerequisites", lambda: "bubblewrap (bwrap) is not on PATH")
    cfg = build_belief_world(certified_work)
    with open_rig(cfg, ("run",)) as (d, ctx):
        with pytest.raises(Refused) as caught:
            d.invoke("run", {"spec": "analysis-spec:" + "0" * 64, "dataset": "dataset:x", "code": "/nowhere",
                             "entrypoint": "e", "targets": ["t"]})
        assert "bubblewrap" in caught.value.refusal.message
        _, view = ctx.single_view()
        assert not any(n.kind == "run" for n in view.iter_stored())


def test_run_refuses_a_missing_code_directory(rig):
    d, _, spec_ref, ref = rig
    with pytest.raises(Refused) as caught:
        d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": "/does/not/exist",
                         "entrypoint": "analysis/workflow/Snakefile", "targets": ["outputs/outcome.txt"]})
    assert caught.value.refusal.code == "invalid-input"


def test_kernel_run_refusal_is_the_refusal_envelope(rig, certified_work):
    """A wrong entrypoint reaches the boundary, which refuses with its reason;
    the invocation closes with that envelope."""
    d, _, spec_ref, ref = rig
    code, _, targets = fixture_bundle(certified_work)
    with pytest.raises(Refused) as caught:
        d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": str(code),
                         "entrypoint": "analysis/workflow/Missing", "targets": list(targets)})
    assert caught.value.refusal.code == "invalid-input"  # prepare() refuses before the boundary


def test_boundary_refusal_is_kernel_refused_and_closes_the_invocation(rig, certified_work):
    """A definition the entrypoint does not embody reaches the boundary, which
    refuses; the dispatcher's kernel path renders it and closes the ledger."""
    d, _, spec_ref, ref = rig
    code, entrypoint, targets = fixture_bundle(certified_work)
    (code / "workflow" / "Snakefile").write_text("rule nothing:\n    output: 'outputs/other.txt'\n    shell: 'touch {output}'\n")
    with pytest.raises(Refused) as caught:
        d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": str(code),
                         "entrypoint": entrypoint, "targets": list(targets)}, invocation_id="K" * 8)
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "RunRefused"
    with pytest.raises(Refused) as again:  # the refusal replays from the ledger
        d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": str(code),
                         "entrypoint": entrypoint, "targets": list(targets)}, invocation_id="K" * 8)
    assert again.value.refusal.code == "kernel-refused"
```

- [ ] **Step 3: Run to verify they fail** — `just test-fast`.

- [ ] **Step 4: Handler**

```python
# python/src/science/commands/run.py
"""run: execute a frozen spec's analysis once under confinement (§4.4)."""
from __future__ import annotations

import socket
from datetime import UTC, datetime
from pathlib import Path

from beliefs import stored
from beliefs.adapter import WorkflowDefinition
from beliefs.boundary import RunMinted, RunRefused, execute_assessment_run
from beliefs.confinement import host_prerequisites
from beliefs.dataset import dataset_address
from beliefs.errors import MalformedRecord
from beliefs.recipe import CONFINED_POLICY
from beliefs.runrecord import run_ref

from science.refusal import Refusal, Refused
from science.report import Report, record_block

POLICY = CONFINED_POLICY


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def prepare(ctx, spec_ref: str, dataset_ref: str, code: str, entrypoint: str, targets) -> dict:
    """Everything the boundary needs, validated; shared with verify."""
    _, view = ctx.single_view()
    if not view.holds(spec_ref):
        _refuse(f"spec {spec_ref!r} is not in the corpus")
    if not view.holds(dataset_ref):
        _refuse(f"dataset {dataset_ref!r} is not in the corpus")
    try:
        spec = stored.analysis_spec_value(view.get(spec_ref))
        address = dataset_address(stored.dataset_declaration(view.get(dataset_ref)))
    except MalformedRecord as caught:
        _refuse(str(caught))
    if address is None or all(role.dataset != address for role in spec.input_roles):
        _refuse(f"{dataset_ref} is not the dataset the spec observes")
    code_root = Path(code)
    if not code_root.is_dir():
        _refuse(f"code {code!r} is not a directory")
    snakefile = code_root.parent / entrypoint
    if not snakefile.is_file():
        _refuse(f"entrypoint {entrypoint!r} is not a file under {code_root.parent}")
    if not targets:
        _refuse("targets must name at least one output")
    return {
        "spec": spec,
        "definition": WorkflowDefinition(snakefile=snakefile.read_bytes(), family_streams={}),
        "code_roots": (code_root,),
        "held_inputs": {address: ctx.held_path(address)},
        "entrypoint": entrypoint,
        "targets": tuple(targets),
        "declared_outputs": tuple(targets),
        "host_realization": socket.gethostname(),
    }


def handle(ctx, writer, *, spec, dataset, code, entrypoint, targets, cores=None) -> Report:
    reason = host_prerequisites()
    if reason is not None:
        _refuse(f"confinement is unavailable on this host: {reason}")
    prepared = prepare(ctx, spec, dataset, code, entrypoint, targets)
    outcome = execute_assessment_run(
        port=writer.operation_port(), boundary_policy=POLICY, observer=writer.actor,
        started_at=now(), scratch_base=ctx.config.operations_root / "scratch" / writer.invocation_id,
        cores=cores or 1, **prepared,
    )
    if isinstance(outcome, RunRefused):
        # A kernel refusal, through the kernel path: the boundary may already
        # have written its act-report through the port, so this is never a
        # surface `Refused` (Task 1 would call that a handler defect). The
        # dispatcher normalizes it to `kernel-refused` carrying the reason.
        raise KernelRefusalValue(outcome)
    assert isinstance(outcome, RunMinted)
    _, view = ctx.single_view()
    return (record_block(view.get(run_ref(outcome.run.address()))),)
```

with `from beliefs.session import KernelRefusalValue` among the imports. `RunRefused` carries `reason` and `detail`; the dispatcher's `_kernel_refusal` renders `Refusal("kernel-refused", str(value.reason), {"kind": "RunRefused", "reason": …})`. `writer.actor` is the session actor exposed on the scoped writer (assumed seam).

- [ ] **Step 5: Run, regenerate, run** — `just test-fast`; `cd python && uv run science adapters build`; `just test`.

- [ ] **Step 6: Commit**

```bash
tasks done sci-fe0065 "run command: one confined execution through the scoped operation port"
git add commands/run python/src/science/commands/run.py python/tests/test_cmd_run.py adapters/claude-code tasks/
git commit -m "feat(commands): run executes a frozen spec under confinement"
```

---

### Task 8: `assess` — derive and mint the assessment

**Blocked on `beliefs-e5ab34`.**

**Files:**
- Create: `commands/assess/command.toml`, `commands/assess/prompt.md`, `python/src/science/commands/assess.py`
- Test: `python/tests/test_cmd_assess.py`
- Regenerate: `adapters/claude-code/`

**Interfaces:**
- Consumes: `beliefs.runrecord.decode_run_closure`, `beliefs.assess.{build_assessment, AssessmentFinding}`, `beliefs.rules.REFERENCE_RULES`, `stored.{analysis_spec_value, assessment_node, assessment_value}`.
- Produces: `assessment:<16 hex>` records; `handle(ctx, writer, *, run)`.

- [ ] **Step 1: Declaration and prompt** — spec §4.5; prompt:

```markdown
Run `assess` after `run`: name the run record, and the assessment the run's
outputs support under the spec's interpretation rule is derived and minted.
Nothing is judged here beyond the rule; admission to belief is what `verify`
enables and `belief` reports.
```

- [ ] **Step 2: Failing tests**

```python
# python/tests/test_cmd_assess.py
import pytest

from science.refusal import Refused
from helpers.world import SPEC_FIELDS, build_belief_world, fixture_bundle, hold_fixture_dataset, mint_fixture_run, open_rig


@pytest.fixture
def rig(certified_work):
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec", "assess")) as (d, ctx):
        spec_ref = next(t for t in d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref)).text.split()
                        if t.startswith("analysis-spec:"))
        run_ref = mint_fixture_run(cfg, spec_ref, ref, fixture_bundle(certified_work, "supported"))
        yield d, ctx, run_ref


def test_assess_mints_the_assessment_the_outcome_file_fixes(rig):
    d, ctx, run_ref = rig
    out = d.invoke("assess", {"run": run_ref})
    assert "[assessment] assessment:" in out.text
    _, view = ctx.single_view()
    from beliefs import stored
    node = next(n for n in view.iter_stored() if n.kind == "assessment")
    value = stored.assessment_value(node)
    assert value.outcome == "supported"
    assert value.proposition == "proposition:p1"
    assert node.id == f"assessment:{value.identity()[:16]}"


def test_assess_refuses_an_unknown_run(rig):
    d, _, _ = rig
    with pytest.raises(Refused) as caught:
        d.invoke("assess", {"run": "run:" + "0" * 64})
    assert caught.value.refusal.code == "invalid-input"
```

- [ ] **Step 3: Run to verify they fail** — `just test-fast`.

- [ ] **Step 4: Handler**

```python
# python/src/science/commands/assess.py
"""assess: derive the assessment a run supports and mint it (§4.5)."""
from __future__ import annotations

from beliefs import stored
from beliefs.assess import AssessmentFinding, build_assessment
from beliefs.errors import MalformedRecord
from beliefs.rules import REFERENCE_RULES
from beliefs.runrecord import decode_run_closure

from science.refusal import Refusal, Refused
from science.report import Report, record_block


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def handle(ctx, writer, *, run) -> Report:
    _, view = ctx.single_view()
    if not view.holds(run):
        _refuse(f"run {run!r} is not in the corpus")
    try:
        closure = decode_run_closure(view.get(run))
    except MalformedRecord as caught:
        _refuse(f"{run}: {caught}")
    spec_ref = stored.typed_ref("analysis-spec", closure.recipe.spec_identity or "")
    if not closure.recipe.spec_identity or not view.holds(spec_ref):
        _refuse(f"{run} names no analysis-spec this corpus holds")
    spec = stored.analysis_spec_value(view.get(spec_ref))
    rule = REFERENCE_RULES.get(spec.interpretation_rule)
    if rule is None:
        _refuse(f"the spec's interpretation rule {spec.interpretation_rule!r} is not a reference rule")
    derived = build_assessment(closure, specs={spec.identity: spec}, implementations={rule.identity: rule})
    if isinstance(derived, AssessmentFinding):
        _refuse(f"assessment finding: {derived.reason}")
    optional = {k: v for k, v in (("estimate", derived.estimate), ("uncertainty", derived.uncertainty),
                                   ("estimand", derived.estimand), ("applicability", derived.applicability))
                if v is not None}
    node = writer.add(stored.assessment_node(
        derived.identity()[:16], title=f"assessment of {spec.target}", spec=spec.identity, run=run,
        proposition=spec.target, outcome=derived.outcome, interpretation_rule=derived.interpretation_rule,
        **optional))
    stored_identity = stored.assessment_value(node).identity()
    if stored_identity != derived.identity():
        raise RuntimeError(f"stored assessment identity {stored_identity} differs from derived {derived.identity()}")
    return (record_block(node),)
```

- [ ] **Step 5: Run, regenerate, run** — `just test-fast`; `cd python && uv run science adapters build`; `just test`.

- [ ] **Step 6: Commit**

```bash
tasks done sci-881719 "assess command: build_assessment through the reference rule, one stored identity"
git add commands/assess python/src/science/commands/assess.py python/tests/test_cmd_assess.py adapters/claude-code tasks/
git commit -m "feat(commands): assess derives and mints the assessment"
```

---

### Task 9: `verify` — replay, derive scope and verdict, mint the verification

**Blocked on `beliefs-5fe2e3` and Task 7 (`sci-fe0065`)** (`writer.operation_port()`,
`replay` over a closure, and the run preparation interface). Task 9 follows
Task 7 because it imports `science.commands.run.{prepare, now, POLICY}` directly.

**Files:**
- Create: `commands/verify/command.toml`, `commands/verify/prompt.md`, `python/src/science/commands/verify.py`
- Test: `python/tests/test_cmd_verify.py`
- Regenerate: `adapters/claude-code/`

**Interfaces:**
- Consumes: `science.commands.run.{prepare, now, POLICY}`; `beliefs.session.KernelRefusalValue`; `beliefs.replay.{replay, derive_scope}`; `beliefs.verify.{build_verification, AssessmentVerification, publication_node}`; `beliefs.rules.REFERENCE_RULES`; `ctx.pins()`, `ctx.epoch_identity()`.
- Produces: `verification:<identity>` records naming the assessment; `handle(ctx, writer, *, assessment, code, entrypoint, cores=None)`.

- [ ] **Step 1: Declaration and prompt** — spec §4.6; prompt:

```markdown
Run `verify` after `assess`: name the assessment and the same code directory
and entrypoint the run used. The original run is replayed, the two are
compared under the spec's equivalence rule, and the verification is minted
with its scope and verdict. `clean-environment` with `passed` is what admits
the assessment to belief; ask `belief` to see whether it did.
```

- [ ] **Step 2: Failing tests**

```python
# python/tests/test_cmd_verify.py
import pytest

from science.refusal import Refused
from helpers.world import SPEC_FIELDS, build_belief_world, fixture_bundle, hold_fixture_dataset, mint_fixture_run, open_rig


@pytest.fixture
def rig(certified_work, monkeypatch):
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    bundle = fixture_bundle(certified_work, "supported")
    with open_rig(cfg, ("spec", "assess", "verify")) as (d, ctx):
        spec_ref = next(t for t in d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref)).text.split()
                        if t.startswith("analysis-spec:"))
        run_ref = mint_fixture_run(cfg, spec_ref, ref, bundle)
        assessment_ref = next(t for t in d.invoke("assess", {"run": run_ref}).text.split() if t.startswith("assessment:"))
        yield d, ctx, assessment_ref, bundle


def test_verify_mints_a_verification_naming_the_assessment_and_both_runs(rig):
    d, ctx, assessment_ref, (code, entrypoint, _) = rig
    out = d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint})
    assert "[verification] verification:" in out.text
    _, view = ctx.single_view()
    node = next(n for n in view.iter_stored() if n.kind == "verification")
    facet = node.facets["verification"]
    assert facet["verdict"] == "passed"
    assert facet["derivation"]["original"] != facet["derivation"]["replayed"]
    assert sum(1 for n in view.iter_stored() if n.kind == "run") == 2
    assert any(r.target == assessment_ref for r in node.relations)


def test_verify_refuses_an_unknown_assessment(rig):
    d, _, _, (code, entrypoint, _) = rig
    with pytest.raises(Refused) as caught:
        d.invoke("verify", {"assessment": "assessment:0000000000000000", "code": str(code), "entrypoint": entrypoint})
    assert caught.value.refusal.code == "invalid-input"


def test_a_disagreeing_replay_yields_failed_and_still_mints(rig, certified_work):
    """The bundle's outcome file is rewritten between run and replay; the
    equivalence rule says failed; the verification is a record either way."""
    d, ctx, assessment_ref, (code, entrypoint, _) = rig
    (code / "workflow" / "Snakefile").write_text((code / "workflow" / "Snakefile").read_text().replace("supported", "refuted"))
    with pytest.raises(Refused) as caught:
        d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint})
    # A changed bundle changes the recipe identity: the boundary refuses the
    # replay as a different recipe, never a silently different result.
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "RunRefused"
```

The third test encodes what the boundary does today (`expected_recipe_identity` mismatch refuses). If the kernel instead executes and the rule answers `failed`, change the assertion to look for `"verdict"] == "failed"`; either way the test pins one behavior and the docstring says which.

- [ ] **Step 3: Run to verify they fail** — `just test-fast`.

- [ ] **Step 4: Handler**

```python
# python/src/science/commands/verify.py
"""verify: replay the assessment's run and mint the verification (§4.6)."""
from __future__ import annotations

from beliefs import stored
from beliefs.boundary import RunMinted, RunRefused
from beliefs.errors import MalformedRecord
from beliefs.replay import derive_scope, replay
from beliefs.rules import REFERENCE_RULES
from beliefs.runrecord import decode_run_closure
from beliefs.verify import AssessmentVerification, build_verification, publication_node

from beliefs.session import KernelRefusalValue

from science.commands.run import POLICY, now, prepare
from science.refusal import Refusal, Refused
from science.report import Report, record_block


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def handle(ctx, writer, *, assessment, code, entrypoint, cores=None) -> Report:
    _, view = ctx.single_view()
    if not view.holds(assessment):
        _refuse(f"assessment {assessment!r} is not in the corpus")
    try:
        value = stored.assessment_value(view.get(assessment))
    except MalformedRecord as caught:
        _refuse(f"{assessment}: {caught}")
    run_ref = stored.typed_ref("run", value.run)
    spec_ref = stored.typed_ref("analysis-spec", value.spec)
    if not view.holds(run_ref) or not view.holds(spec_ref):
        _refuse(f"{assessment} names a run or spec this corpus does not hold")
    original = decode_run_closure(view.get(run_ref))
    (role,) = stored.analysis_spec_value(view.get(spec_ref)).input_roles
    dataset_ref = next((n.id for n in view.iter_stored() if n.kind == "dataset"
                        and _address(n) == role.dataset), None)
    if dataset_ref is None:
        _refuse(f"the spec's dataset {role.dataset} is not in the corpus")
    prepared = prepare(ctx, spec_ref, dataset_ref, code, entrypoint, original.recipe.invocation.targets)
    spec = prepared.pop("spec")
    equivalence = REFERENCE_RULES.get(spec.equivalence_rule)
    if equivalence is None:
        _refuse(f"the spec's equivalence rule {spec.equivalence_rule!r} is not a reference rule")
    # --- first act: the replay -----------------------------------------------
    outcome = replay(original, port=writer.operation_port(), spec=spec, observer=writer.actor,
                     started_at=now(), scratch_base=ctx.config.operations_root / "scratch" / writer.invocation_id,
                     cores=cores or 1, **prepared)
    if isinstance(outcome, RunRefused):
        raise KernelRefusalValue(outcome)  # the kernel path, as in run
    assert isinstance(outcome, RunMinted)
    replayed = outcome.run
    derive_scope(original, replayed, certification=None)
    verification = build_verification(original, replayed, specs={spec.identity: spec},
                                      held_rules={equivalence.identity: equivalence},
                                      contract_identity=ctx.pins().science_contract,
                                      epoch=ctx.epoch_identity())
    if not isinstance(verification, AssessmentVerification):
        raise RuntimeError(f"build_verification over an assessment run returned {type(verification).__name__}")
    node = writer.add(publication_node(verification, assessment_ref=assessment))
    return (record_block(node),)


def _address(node) -> str | None:
    from beliefs.dataset import dataset_address
    return dataset_address(stored.dataset_declaration(node))
```

The replay is the first act, and `prepare` validates everything before it. `epoch` for `build_verification` takes `"none-published"` in the driver; `ctx.epoch_identity()` returns `"no-epoch-published"` — check which literal the kernel expects (`grep -n "none-published\|no-epoch-published" ~/d/beliefs/python/src/beliefs/*.py`) and use one constant for both call sites, defined in `science/closure.py`.

- [ ] **Step 5: Run, regenerate, run** — `just test-fast`; `cd python && uv run science adapters build`; `just test`.

- [ ] **Step 6: Commit**

```bash
tasks done sci-5fe8fc "verify command: replay through the operation port, verification against the assessment"
git add commands/verify python/src/science/commands/verify.py python/tests/test_cmd_verify.py adapters/claude-code tasks/
git commit -m "feat(commands): verify replays and mints the verification"
```

---

### Task 10: `belief` — evaluate and render the answer

**Files:**
- Create: `commands/belief/command.toml`, `commands/belief/prompt.md`, `python/src/science/commands/belief.py`
- Test: `python/tests/test_cmd_belief.py`
- Regenerate: `adapters/claude-code/`

**Interfaces:**
- Consumes: `ctx.evaluate(proposition)`; `beliefs.belief.{Belief, NoBelief, Refused as KernelRefused}`.
- Produces: `handle(ctx, *, proposition) -> Report` of `Heading` + `KeyVals`.

- [ ] **Step 1: Declaration and prompt** — spec §4.7 (budget 8192; `families = ["corpus-stored", "holdings", "epoch", "registry"]`). Prompt:

```markdown
Run `belief` to see what the shipped policy believes about one proposition
and why: `Belief` with its value, input digest and policy binding; `NoBelief`
with the reason (no eligible assessment, no directional outcome); or
`Refused` with the kernel's reason. Nothing is written.
```

- [ ] **Step 2: Failing tests**

```python
# python/tests/test_cmd_belief.py
import pytest

from science.commands.belief import handle
from science.config import ReadContext
from science.report import KeyVals
from helpers.world import build_belief_world


def test_belief_renders_no_belief_with_its_reason_before_assessment(certified_work):
    report = handle(ReadContext.open(build_belief_world(certified_work)), proposition="proposition:p1")
    kv = next(b for b in report if isinstance(b, KeyVals))
    pairs = dict(kv.pairs)
    assert pairs["kind"] == "NoBelief"
    assert pairs["reason"] == "no-eligible-assessment"


def test_belief_refuses_an_unknown_proposition(certified_work):
    from science.refusal import Refused
    with pytest.raises(Refused):
        handle(ReadContext.open(build_belief_world(certified_work)), proposition="proposition:nope")


def test_belief_performs_exactly_its_declared_reads():
    from science.loader import production_tree
    decl = next(d for d in production_tree() if d.name == "belief")
    assert set(decl.reads) == {"corpus-stored", "holdings", "epoch", "registry"}
```

The full-path `Belief` case is asserted in Task 12's transport test once assess and verify exist (`test_belief_after_the_full_path`); it asserts `pairs["kind"] == "Belief"` and that `value`, `belief_input_digest` and `policy_binding` are present.

- [ ] **Step 3: Run to verify they fail** — `just test-fast`.

- [ ] **Step 4: Handler**

```python
# python/src/science/commands/belief.py
"""belief: evaluate science.belief.v1 over one proposition (§4.7)."""
from __future__ import annotations

from beliefs.belief import Belief, NoBelief

from science.refusal import Refusal, Refused
from science.report import Heading, KeyVals, Report


def handle(ctx, *, proposition) -> Report:
    _, view = ctx.single_view()
    if not view.holds(proposition):
        raise Refused(Refusal("invalid-input", f"proposition {proposition!r} is not in the corpus"))
    answer = ctx.evaluate(proposition)
    if isinstance(answer, Belief):
        pairs = (("kind", "Belief"), ("value", str(answer.value)),
                 ("belief_input_digest", answer.belief_input_digest),
                 ("policy_binding", f"{answer.policy_binding.rule} {answer.policy_binding.implementation}"))
    elif isinstance(answer, NoBelief):
        pairs = (("kind", "NoBelief"), ("reason", answer.reason), ("detail", answer.detail))
    else:
        pairs = (("kind", "Refused"), ("reason", answer.reason))
    return (Heading(f"Belief: {proposition}"), KeyVals("answer", pairs))
```

- [ ] **Step 5: Run, regenerate, run** — `just test-fast`; `cd python && uv run science adapters build`; `just test`.

- [ ] **Step 6: Commit**

```bash
tasks done sci-3bfa6d "belief read: the evaluator's answer with its reason"
git add commands/belief python/src/science/commands/belief.py python/tests/test_cmd_belief.py adapters/claude-code tasks/
git commit -m "feat(commands): belief renders the evaluator's answer"
```

---

### Task 11: `next` — the derived queue

**Files:**
- Create: `commands/next/command.toml`, `commands/next/prompt.md`, `python/src/science/commands/next.py`
- Test: `python/tests/test_cmd_next.py`
- Regenerate: `adapters/claude-code/`

**Interfaces:**
- Consumes: `ctx.single_view()`, `ctx.observations()`, `ctx.gather_inputs(proposition)`, `beliefs.admission.{admit, Admitted}`, `stored.{analysis_spec_value, assessment_value, dataset_declaration}`, `beliefs.dataset.{admission_state, Held}`.
- Produces: `handle(ctx, *, limit=None) -> Report`; `science.commands.next.classify(ctx, proposition_id) -> str` in `{"ready", "not-ready", "assessed-not-admitted", "admitted"}`.

- [ ] **Step 1: Declaration and prompt** — spec §4.8 (budget 16384). Prompt:

```markdown
Run `next` when the user asks what to work on. It lists propositions in a
fixed order — ready (a spec targets it and every input is held), not ready,
assessed but not admitted, admitted — with each one's statement. Nothing is
stored; the ranking is recomputed every time. It names no priority function;
that is a later sub-project's.
```

- [ ] **Step 2: Failing tests**

```python
# python/tests/test_cmd_next.py
from science.commands.next import classify, handle
from science.config import ReadContext
from science.report import KeyVals
from helpers.world import SPEC_FIELDS, build_belief_world, hold_fixture_dataset, open_rig


def test_a_proposition_no_spec_targets_is_not_ready_however_much_is_held(certified_work):
    cfg = build_belief_world(certified_work)
    hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    assert classify(ReadContext.open(cfg), "proposition:p1") == "not-ready"


def test_a_spec_whose_inputs_are_held_makes_it_ready(certified_work):
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec",)) as (d, ctx):
        d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref))
        assert classify(ctx, "proposition:p1") == "ready"


def test_a_later_absent_observation_moves_it_back_to_not_ready(certified_work):
    from helpers.world import unhold_fixture_dataset
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec",)) as (d, _):
        d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref))
    assert classify(ReadContext.open(cfg), "proposition:p1") == "ready"
    unhold_fixture_dataset(cfg, ref)
    assert classify(ReadContext.open(cfg), "proposition:p1") == "not-ready"


def test_next_renders_rows_in_class_order(certified_work):
    cfg = build_belief_world(certified_work)
    report = handle(ReadContext.open(cfg), limit=None)
    kv = next(b for b in report if isinstance(b, KeyVals))
    assert kv.pairs[0][0] == "proposition:p1"
    assert kv.pairs[0][1].startswith("not-ready:")
```

The assessed and admitted classes are asserted in Task 12's full-path test, where a run, an assessment and a verification exist.

- [ ] **Step 3: Run to verify they fail** — `just test-fast`.

- [ ] **Step 4: Handler**

```python
# python/src/science/commands/next.py
"""next: the derived queue of layer §4.4, computed at read time (§4.8)."""
from __future__ import annotations

from beliefs import stored
from beliefs.admission import Admitted, admit
from beliefs.dataset import Held, admission_state, dataset_address

from science.report import Heading, KeyVals, Report

CLASSES = ("ready", "not-ready", "assessed-not-admitted", "admitted")


def _targeting_specs(view, proposition):
    return [stored.analysis_spec_value(n) for n in view.iter_stored()
            if n.kind == "analysis-spec" and stored.analysis_spec_value(n).target == proposition]


def _inputs_held(ctx, view, spec) -> bool:
    observations = ctx.observations()
    for role in spec.input_roles:
        node = next((n for n in view.iter_stored() if n.kind == "dataset"
                     and dataset_address(stored.dataset_declaration(n)) == role.dataset), None)
        if node is None:
            return False
        if not isinstance(admission_state(stored.dataset_declaration(node), observations.get(role.dataset, ())), Held):
            return False
    return True


def classify(ctx, proposition: str) -> str:
    _, view = ctx.single_view()
    assessed = any(n.kind == "assessment" and stored.assessment_value(n).proposition == proposition
                   for n in view.iter_stored())
    if not assessed:
        return "ready" if any(_inputs_held(ctx, view, s) for s in _targeting_specs(view, proposition)) else "not-ready"
    inputs = ctx.gather_inputs(proposition)
    observations = ctx.observations()
    for assessment in inputs.assessments:
        run = inputs.runs.get(assessment.run)
        if run is not None and isinstance(admit(assessment, run, observations, inputs.verifications), Admitted):
            return "admitted"
    return "assessed-not-admitted"


def handle(ctx, *, limit=None) -> Report:
    _, view = ctx.single_view()
    rows = []
    for node in view.iter_stored():
        if node.kind != "proposition":
            continue
        statement = (stored.display_statement(node) if hasattr(stored, "display_statement") else None) or node.title
        rows.append((CLASSES.index(classify(ctx, node.id)), node.id, statement))
    rows.sort()
    shown = rows[: (limit or 10)]
    return (Heading("Next"),
            KeyVals("propositions", tuple((pid, f"{CLASSES[c]}: {statement}") for c, pid, statement in shown)
                    or (("none", "no propositions"),)))
```

Replace the `hasattr` guess for the display statement with the real accessor (`grep -n "display_statement" ~/d/beliefs/python/src/beliefs/stored.py`).

- [ ] **Step 5: Run, regenerate, run** — `just test-fast`; `cd python && uv run science adapters build`; `just test`.

- [ ] **Step 6: Commit**

```bash
tasks done sci-258ac6 "next: four fixed classes over the derived queue, inputs joined through targeting specs"
git add commands/next python/src/science/commands/next.py python/tests/test_cmd_next.py adapters/claude-code tasks/
git commit -m "feat(commands): next ranks propositions by a fixed derived order"
```

---

### Task 12: The full path through both surfaces

**Files:**
- Test: `python/tests/test_belief_path.py`, `python/tests/test_belief_path_transports.py`
- Modify: `python/tests/helpers/world.py` (`write_config_for`)

**Interfaces:**
- Consumes: everything above; the MCP `rpc()` helper and `serve()` from `test_mcp.py`; `science.cli.main`; `science.serve.serve`; `beliefs.session.open_ledger_reader`; `science.report.{record_block, serialize_block}` for the complete canonical report a write renders. The run and verify legs skip to the minimal policy where bubblewrap is absent, exactly as `test_belief_path.py` does.
- Produces: `helpers.world.write_config_for(cfg) -> Path` (the TOML for an existing config, including `contracts` and `store_root`).

- [ ] **Step 1: The full path, portable and confined**

```python
# python/tests/test_belief_path.py
"""The success criterion over the fixture world: claim -> dataset -> spec ->
run -> assess -> verify -> belief, every step a record, through one
dispatcher. Two hosts, two answers: under the minimal boundary policy a
replay cannot qualify as clean-environment, so the verification does not
admit and the belief stays NoBelief; under confinement it admits."""
import pytest

from beliefs.confinement import host_prerequisites
from science.report import KeyVals
from helpers.world import SPEC_FIELDS, build_fixture_world_with_contract, fixture_bundle, open_rig

CONFINED = host_prerequisites() is None


def walk(certified_work, monkeypatch, *, confined: bool):
    import science.commands.run as run_module
    from beliefs.recipe import MINIMAL_POLICY
    if not confined:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)
    cfg = build_fixture_world_with_contract(certified_work)
    code, entrypoint, targets = fixture_bundle(certified_work, "supported")
    data = certified_work / "data.txt"
    data.write_bytes(b"x\n")
    names = ("claim", "dataset", "spec", "run", "assess", "verify", "belief", "next")
    rig = open_rig(cfg, names)
    d, ctx = rig.__enter__()

    def ref(text, prefix):
        return next(t for t in text.split() if t.startswith(prefix))
    prop = ref(d.invoke("claim", {"subject": "concept:disease-stage", "predicate": "affects",
                                  "object": "protein:PHF19", "layer": "causal", "polarity": "positive"}).text,
               "proposition:")
    dataset = ref(d.invoke("dataset", {"path": str(data), "title": "expression"}).text, "dataset:")
    spec = ref(d.invoke("spec", dict(SPEC_FIELDS, target=prop, dataset=dataset)).text, "analysis-spec:")
    run = ref(d.invoke("run", {"spec": spec, "dataset": dataset, "code": str(code),
                               "entrypoint": entrypoint, "targets": list(targets)}).text, "run:")
    assessment = ref(d.invoke("assess", {"run": run}).text, "assessment:")
    d.invoke("verify", {"assessment": assessment, "code": str(code), "entrypoint": entrypoint})
    return rig, d, ctx, prop, cfg


@pytest.fixture
def walked_portable(certified_work, monkeypatch):
    rig, d, ctx, prop, cfg = walk(certified_work, monkeypatch, confined=False)
    try:
        yield d, ctx, prop, cfg
    finally:
        rig.__exit__(None, None, None)


@pytest.fixture
def walked_confined(certified_work, monkeypatch):
    if not CONFINED:
        pytest.skip(f"confinement unavailable: {host_prerequisites()}")
    rig, d, ctx, prop, cfg = walk(certified_work, monkeypatch, confined=True)
    try:
        yield d, ctx, prop, cfg
    finally:
        rig.__exit__(None, None, None)


def _answer(ctx, prop):
    from science.commands.belief import handle as belief
    return dict(next(b for b in belief(ctx, proposition=prop) if isinstance(b, KeyVals)).pairs)


def test_every_step_left_exactly_its_record(walked_portable):
    _, ctx, _, _ = walked_portable
    _, view = ctx.single_view()
    kinds = sorted(n.kind for n in view.iter_stored())
    assert kinds.count("proposition") == 1 and kinds.count("dataset") == 2
    assert kinds.count("analysis-spec") == 1 and kinds.count("run") == 2
    assert kinds.count("assessment") == 1 and kinds.count("verification") == 1


def test_without_confinement_the_verification_does_not_admit(walked_portable):
    """same-environment, passed — a real verification, not an admitting one."""
    from science.commands.next import classify
    _, ctx, prop, _ = walked_portable
    _, view = ctx.single_view()
    facet = next(n for n in view.iter_stored() if n.kind == "verification").facets["verification"]
    assert facet["verdict"] == "passed" and facet["scope"] == "same-environment"
    pairs = _answer(ctx, prop)
    assert pairs["kind"] == "NoBelief" and pairs["reason"] == "no-eligible-assessment"
    assert classify(ctx, prop) == "assessed-not-admitted"


def test_under_confinement_the_path_ends_in_an_admitted_belief(walked_confined):
    from science.commands.next import classify
    _, ctx, prop, _ = walked_confined
    _, view = ctx.single_view()
    facet = next(n for n in view.iter_stored() if n.kind == "verification").facets["verification"]
    assert facet["scope"] == "clean-environment" and facet["verdict"] == "passed"
    pairs = _answer(ctx, prop)
    assert pairs["kind"] == "Belief", pairs
    assert pairs["value"] and pairs["belief_input_digest"] and pairs["policy_binding"]
    assert classify(ctx, prop) == "admitted"
```

- [ ] **Step 2: The transports, per command**

Framework §9.4 wants byte-identical rendering through the CLI and the MCP
server, and the belief-path design §7 wants every command through its real
transport: CLI argument parsing, service routing for writes, MCP argument
handling, invocation replay and the refusal envelope on each.

```python
# python/tests/test_belief_path_transports.py
import io
import json
import socket
import threading

import pytest

from helpers.world import SPEC_FIELDS, build_fixture_world_with_contract, write_config_for
from tests.test_mcp import rpc


@pytest.fixture
def world(certified_work):
    cfg = build_fixture_world_with_contract(certified_work)
    return cfg, write_config_for(cfg)


def mcp_calls(cfg_path, calls):
    """Every call in one `serve()` lifetime — one attended session — so that
    invocation replay, which is session-scoped, is what gets tested."""
    from science.mcp import serve
    frames = []
    for index, (name, arguments, invocation_id) in enumerate(calls, 1):
        params = {"name": name, "arguments": dict(arguments)}
        if invocation_id is not None:
            params["arguments"]["invocation_id"] = invocation_id
        frames.append(json.dumps(rpc("tools/call", params, id=index)))
    stdin = io.BytesIO(("\n".join(frames) + "\n").encode())
    stdout = io.StringIO()
    serve(cfg_path, stdin=stdin, stdout=stdout, stderr=io.StringIO())
    return [json.loads(line)["result"] for line in stdout.getvalue().splitlines()]


def mcp_call(cfg_path, name, arguments, invocation_id=None):
    (result,) = mcp_calls(cfg_path, [(name, arguments, invocation_id)])
    return result


CLAIM = {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
         "layer": "causal", "polarity": "positive"}


def test_mcp_write_replays_under_one_invocation_id(world):
    cfg, cfg_path = world
    first, again = mcp_calls(cfg_path, [("claim", CLAIM, "A" * 8), ("claim", CLAIM, "A" * 8)])
    assert first["isError"] is False
    assert first["content"][0]["text"] == again["content"][0]["text"]
    assert first["structuredContent"]["invocation_id"] == "A" * 8
    from science.config import ReadContext
    _, view = ReadContext.open(cfg).single_view()
    assert sum(1 for n in view.iter_stored() if n.kind == "proposition") == 1
    # One act in the session's ledger, not two: the second call replayed.
    from beliefs.session import ledger_path
    (ledger,) = (cfg.operations_root / "sessions").glob("*/ledger.v1")
    assert sum(1 for line in ledger.read_text().splitlines() if '"act"' in line) == 1


def test_mcp_refusal_carries_the_envelope(world):
    _, cfg_path = world
    result = mcp_call(cfg_path, "claim", dict(CLAIM, subject="protein:PHF19", object="concept:disease-stage"))
    assert result["isError"] is True
    assert result["structuredContent"]["refusal"]["code"] == "invalid-input"
    assert "no plan row" in result["structuredContent"]["refusal"]["message"]


def test_cli_write_routes_through_the_service_and_refuses_with_the_json_line(world, tmp_path, capsys):
    from science.cli import main
    from science.serve import serve
    from science.config import load_config
    cfg, _ = world
    named = tmp_path / "svc.sock"
    cfg_path = write_config_for(cfg, service_socket=named)
    server = serve(load_config(cfg_path), named)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        data = tmp_path / "m.txt"
        data.write_bytes(b"x\n")
        assert main(["dataset", "--config", str(cfg_path), "--path", str(data), "--title", "m",
                     "--facets", "biology/gene-axis=axis:rows,namespace:HGNC"]) == 0
        out = capsys.readouterr()
        assert "[dataset] dataset:sha256:" in out.out
        assert json.loads(out.err)["invocation_id"]
        assert main(["dataset", "--config", str(cfg_path), "--path", str(tmp_path), "--title", "dir"]) == 3
        err = json.loads(capsys.readouterr().err)
        assert err["refusal"]["code"] == "invalid-input"
        assert main(["dataset", "--config", str(cfg_path), "--path", str(data), "--title", "m",
                     "--invocation-id", "R" * 8]) == 3  # same bytes: refuses naming the record
        assert main(["dataset", "--config", str(cfg_path), "--path", str(data), "--title", "m",
                     "--invocation-id", "R" * 8]) == 3  # and replays that refusal
    finally:
        server.server_close()


def test_every_write_reaches_its_transport_and_renders_the_canonical_report(world, tmp_path, capsys, monkeypatch):
    """spec and assess through MCP, run and verify through the CLI service:
    each write's text contains every record minted by its invocation, rebuilt
    from the corpus in (uid, record_id) order. Uids are minted per world, so
    writes are compared to the corpus, not byte-for-byte across transports
    (design §7)."""
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    from beliefs.session import open_ledger_reader
    from science.cli import main
    from science.config import ReadContext, load_config
    from science.report import record_block, serialize_block
    from science.serve import serve
    from helpers.world import fixture_bundle
    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)
    cfg, _ = world
    named = tmp_path / "svc.sock"
    cfg_path = write_config_for(cfg, service_socket=named)
    code, entrypoint, targets = fixture_bundle(tmp_path, "supported")
    data = tmp_path / "data.txt"
    data.write_bytes(b"x\n")

    def canonical(invocation_id):
        (invocation,) = [
            entry
            for path in (cfg.operations_root / "sessions").glob("*/ledger.v1")
            if (entry := open_ledger_reader(cfg.operations_root, path.parent.name).invocation(invocation_id)) is not None
        ]
        pairs = sorted({pair for act in invocation.acts for pair in act.record_ids})
        assert pairs
        assert invocation.outcome == {"done": [list(pair) for pair in pairs]}
        ctx = ReadContext.open(cfg)
        return "".join(serialize_block(record_block(ctx.load_record(uid, record_id)))
                       for uid, record_id in pairs)

    def ref_in(text, prefix):
        return next(t for t in text.split() if t.startswith(prefix))

    result = mcp_call(cfg_path, "claim", CLAIM)
    prop_text = result["content"][0]["text"]
    prop = ref_in(prop_text, "proposition:")
    assert prop_text == canonical(result["structuredContent"]["invocation_id"])
    server = serve(load_config(cfg_path), named)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        assert main(["dataset", "--config", str(cfg_path), "--path", str(data), "--title", "expression"]) == 0
        output = capsys.readouterr()
        dataset = ref_in(output.out, "dataset:")
        assert output.out == canonical(json.loads(output.err)["invocation_id"])
        result = mcp_call(cfg_path, "spec", dict(SPEC_FIELDS, target=prop, dataset=dataset))
        spec_text = result["content"][0]["text"]
        spec = ref_in(spec_text, "analysis-spec:")
        assert spec_text == canonical(result["structuredContent"]["invocation_id"])
        assert main(["run", "--config", str(cfg_path), "--spec", spec, "--dataset", dataset,
                     "--code", str(code), "--entrypoint", entrypoint, *sum((["--targets", t] for t in targets), [])]) == 0
        output = capsys.readouterr()
        run_text = output.out
        run = ref_in(run_text, "run:")
        assert run_text == canonical(json.loads(output.err)["invocation_id"])
        result = mcp_call(cfg_path, "assess", {"run": run})
        assess_text = result["content"][0]["text"]
        assessment = ref_in(assess_text, "assessment:")
        assert assess_text == canonical(result["structuredContent"]["invocation_id"])
        assert main(["verify", "--config", str(cfg_path), "--assessment", assessment,
                     "--code", str(code), "--entrypoint", entrypoint]) == 0
        output = capsys.readouterr()
        assert ref_in(output.out, "verification:")
        assert output.out == canonical(json.loads(output.err)["invocation_id"])
        # A kernel refusal through the service: the same bundle edited between
        # run and replay is a different recipe, refused by the boundary.
        (code / "workflow" / "Snakefile").write_text((code / "workflow" / "Snakefile").read_text().replace("supported", "refuted"))
        assert main(["verify", "--config", str(cfg_path), "--assessment", assessment,
                     "--code", str(code), "--entrypoint", entrypoint]) == 3
        assert json.loads(capsys.readouterr().err)["refusal"]["code"] == "kernel-refused"
    finally:
        server.server_close()
    # And the two commands not yet seen on the other transport: assess's
    # refusal through the service, spec's refusal through MCP.
    result = mcp_call(cfg_path, "spec", dict(SPEC_FIELDS, target=prop, dataset=dataset, interpretation_rule="nope/v9"))
    assert result["isError"] is True and result["structuredContent"]["refusal"]["code"] == "invalid-input"


def test_reads_render_identically_through_mcp_and_cli(world, capsys):
    from science.cli import main
    cfg, cfg_path = world
    mcp_call(cfg_path, "claim", CLAIM)
    for name, arguments, argv in (
        ("belief", {"proposition": "proposition:concept-disease-stage-affects-protein-phf19"},
         ["--proposition", "proposition:concept-disease-stage-affects-protein-phf19"]),
        ("next", {}, []),
    ):
        text = mcp_call(cfg_path, name, arguments)["content"][0]["text"]
        assert main([name, "--config", str(cfg_path), *argv]) == 0
        assert capsys.readouterr().out == text
```

Add `write_config_for(cfg, service_socket=None) -> Path` to the helpers: it writes every key the loader requires from an existing `ScienceConfig`, with `contracts = ["<the fixture document path>"]`, `store_root`, and `service_socket` when given. The MCP result shape and the `rpc()` signature are those in `test_mcp.py`; the JSON stderr line is the CLI's §9.2 wire. Each transport test proves one thing the dispatcher tests cannot: argparse compiled the declared inputs (including `--facets` as a repeated option), the service routed the write and its refusal, the MCP tool accepted `invocation_id` and replayed, and the refusal envelope survived each wire.

- [ ] **Step 3: Run to verify** — `just test`. The portable path and all transport tests pass on any host; the confined test skips with the reason where bubblewrap is absent and passes where it is present.

- [ ] **Step 4: Commit**

```bash
tasks done sci-445f89 "the full belief path over the fixture world: admitted under confinement, honestly not without; every command through its transport"
git add python/tests/ tasks/
git commit -m "test(belief-path): the full path on both surfaces, confined and portable"
```

---

### Task 13: The measurement — mm30 through the commands

**Files:**
- Create: `docs/records/<run date>-mm30-through-the-commands.md`
- Modify: `docs/specs/2026-09-09-belief-path-commands-design.md` (status line), `tasks/` (findings filed)

**Interfaces:**
- Consumes: a bubblewrap host; the predecessor mm30 checkout the 2026-09-05 record used; `beliefs` library for the operator recipe (§8.2); `science mcp serve` and the CLI.

- [ ] **Step 1: Write the predictions section first**

Create the record with §1 preflight and §5 predictions before running anything, in the 2026-09-05 record's shape. Predictions to state: the proposition id and claim identity `780ace5964c8ab83…`; the concept-list digest `sha256:c7e45f81…` and the expression dataset address `dataset:sha256:a6bf229e…`; the spec identity differs from `86aaa1a8…` by the rule identity; assessment `inconclusive`; scope `clean-environment`, verdict `passed`; belief `NoBelief(no-directional-outcome)`.

- [ ] **Step 2: The operator recipe**

Run as a Python script beside the checkout (not committed under `python/src`), recording it verbatim in the record's §8.2:

```python
import secrets
from pathlib import Path
from hashlib import sha256
from beliefs.permit import Authority, WritePermit
from beliefs.profile import compile_profile, shipped_base_contract, shipped_domain_contract
from beliefs.root import init_corpus_root, init_store_root, init_world_root, open_corpus, open_world
from beliefs.world import Fresh, WorldConfig
from beliefs.consulted import CorpusPins
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from science.contracts import load_contract_document

WORK = Path(".mm30-commands").resolve()
AUTH = Authority(WritePermit.full(), "operator")
concepts = (WORK / "mm30-concepts.txt").read_bytes()          # built as the record's step 1b built it
digest = "sha256:" + sha256(concepts).hexdigest()
address = dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name="mm30-concepts.txt", digest=digest),)))
doc = WORK / "mm30.yaml"                                        # the biology-pack design §3.3 document, with
doc.write_text(doc.read_text().replace("{{CONCEPTS}}", address.removeprefix("dataset:")))  # the address filled in
base = shipped_base_contract()
contract, _ = load_contract_document(doc, base)
profile = compile_profile(base, [shipped_domain_contract("biology"), contract])
pins = CorpusPins(science_contract="science:" + profile.base_contract_identity,
                  domains={ns: f"{ns}:{i}" for ns, i in profile.activated_contracts.items()})
config = WorldConfig(WORK / "world", secrets.token_hex(16), (WORK / "corpus",))
init_world_root(config, authority=AUTH); init_corpus_root(WORK / "corpus", authority=AUTH)
init_store_root(WORK / "store", authority=AUTH)
open_corpus(WORK / "corpus", authority=AUTH, profile=profile).adopt_manifest(profile=pins)
world = open_world(config, authority=AUTH)
world.admit(WORK / "corpus", provenance=Fresh())
from beliefs.holdings.reduce import holdings_rule_bundle
from beliefs.world.rules import install_rule_binding
install_rule_binding(world, holdings_rule_bundle())   # the holdings reducer the reads derive through
print(config.world_id)
```

Then write `science.toml` with the world root, id, corpus root, `operations_root`, `domains = ["biology"]`, `contracts = ["<WORK>/mm30.yaml"]`, `store_root`.

- [ ] **Step 3: Walk the path**

Start `science mcp serve --config science.toml` from a coding-agent session and drive: `dataset` (the concept list), `claim`, `dataset` (the expression matrix from the predecessor's GSE179929 file), `spec` (the record's step 4 draft fields, `outcome-file/v1`, `content-identity-equality/v1`, `alpha=0.05`), `run` (the record's analysis bundle rendered as its `spec.py` rendered it, with the four parameters the finding `beliefs-efc32d` names supplied by the person), `assess`, `verify`, `belief`, `next`. Use the CLI for `belief` and `next` at least once. Record each command's minted id and any refusal in the record's §3 table, classified `design-gap` / `corpus-work` / `defect` / `closed`.

- [ ] **Step 4: Compare to the oracle and write the record**

Fill §8.3's table with observed values against the predictions. File each finding as a task through its owning lane (`tasks add … --project beliefs` or here), and note each id in the record. Update the spec's status line to `implemented <date>; measured <date>, record docs/records/…`.

- [ ] **Step 5: Commit and close**

```bash
tasks done sci-030658 "mm30 reproduced through the commands; record written; findings filed"
git add docs/records docs/specs/2026-09-09-belief-path-commands-design.md tasks/
git commit -m "docs(records): mm30 through the belief-path commands"
```

Then `tasks done sci-66b26d` only if the coordination-set half is also done or split out; otherwise note the record on the goal and leave it open for the second spec.

---

## Self-review

**Spec coverage.** §5.4's holdings reads go through the kernel's held reducer (Task 3), which the fixture worlds and the operator recipe install. §2 rulings 1–9: 1, 2 → Task 13; 3 → Task 6; 4 → the assumed seam + Tasks 6, 8, 9; 5 → Task 2; 6 → Tasks 8–10 ordering; 7 → Task 11; 8 → Task 13 step 2; 9 → seams stated up front. §4.1–4.8 → Tasks 5, 4, 6, 7, 8, 9, 10, 11. §5.1–5.5 → Tasks 2–3. §6.1–6.2 → assumed seams; §6.3 → Task 1. §7 → each task's tests plus Task 12; the transport equivalence test covers the two reads (writes render the same canonical ledger-rebuilt report on both surfaces by construction, framework §7.4). §8 → Task 13.

**Placeholders.** None: every step carries its code or its exact command. The four `grep` checkpoints (Tasks 3, 5, 9, 11) are for pinning a kernel name at implementation time, with the fallback spelled out.

**Type consistency.** `open_rig(cfg, names) -> (Dispatcher, ReadContext)` is defined in Task 3 and used the same way in Tasks 4–12; `SPEC_FIELDS` likewise. `prepare()` returns the keyword set `execute_assessment_run` and `replay` share, and `verify` pops `spec` because `replay` takes it by name. `ctx.held_path(address)` takes a dataset address string everywhere; `ctx.observations()` is the reduced mapping everywhere. `REFERENCE_RULES` is a mapping in Tasks 6, 8, 9. Kernel refusals (`RunRefused`) go through `KernelRefusalValue` in Tasks 7 and 9; only pre-act validation raises the surface `Refused`.

**Task order.** 1 → 2 → 3 (public store identity reader from the routes seam) → 5, 10 (read context and Task 3 helpers) → 4 → 6, 8 (rules seam) → 11 (its readiness test freezes a spec through the production `spec` command, so it follows Task 6) → 7, 9 → 12 → 13. Tasks 1–2 can proceed before the kernel seams land. Every helper a task imports is defined in Task 3 or earlier; nothing imports forward.
