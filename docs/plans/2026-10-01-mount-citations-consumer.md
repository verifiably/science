# Mount Citations Consumer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Science's write commands cite records in the session's read mounts. Belief and
`next` read a mounted session at an epoch that `science epoch` publishes. The
`publishes` declaration-time refusal is gone.

**Architecture:** `ReadContext` gains the session's corpora (`session_mounts`) and two
resolvers: `cited` for citations and `own` for mutation targets. Every write command
resolves through them. A new `science/world_belief.py` holds the epoch currency check, the
world-read supplied context, and the operator epoch build. `ReadContext.evaluate` and
`gather_inputs` choose the corpus-local or the world read by the session's shape. `next`
scans every session corpus and reports `assessed-unevaluated` when the epoch is not
current.

**Tech Stack:** Python 3.11+, the `beliefs` kernel (editable path dependency; this plan
changes no kernel code), pytest through `just`.

**Spec:** `docs/specs/2026-10-01-mount-citations-consumer-design.md`. Kernel source:
beliefs `docs/superpowers/specs/2026-10-01-mount-citations-design.md` (cut 44).

## Global Constraints

- Work in `.worktrees/dc0381-mount-citations`, and from its canonical path
  (`cd "$(pwd -P)"`).
- Tests run only through the justfile.
  - The focused run is `just test-one tests/<file>.py::<test>`, with paths relative to
    `python/`.
  - `just test-fast` runs before every commit.
  - Never call `pytest` directly. A count claim quotes pytest's summary line.
- Run every command in the foreground. Nothing is detached, and no turn ends with a check
  still running.
- Commits use conventional-commit subjects. No AI attribution: no trailer, no co-author
  line, no session URL.
- Task records change only through the `tasks` CLI.
  - `tasks start <step-id>` comes before the task's first edit.
  - `tasks done <step-id> "<one line>"` goes in the task's own commit.
  - `tasks check` must be clean before each commit.
- Write commands decode a cited record under the **writer's** profile
  (`ctx.config.profile`), never the holder's (spec decision 2, kernel decision 3).
- Reads (`belief`, `next`) decode under the holder's profile (`Mount.profile`), as they
  do today.
- Mutation targets (`spec --supersedes`) resolve in the write root alone (spec
  decision 3).
- No fallbacks: a ref no session corpus holds, or two hold, refuses by name. Nothing is
  answered from whichever corpus sorts first.
- A kernel behaviour that contradicts this plan stops the task. Report it with the
  failing output. Do not work around it in science.

## Review Focus

1. A session with coordination off and two configured roots should keep today's
   corpus-local belief, with no epoch required. Task 4 pins it.
2. After `science epoch`, a write to a **read mount** (not the write root) should make
   belief refuse `epoch-stale` naming the mount. Task 4 pins it.
3. `science epoch` run from the CLI should exit 0 and print `built`, then `current` on a
   rerun. Task 3 pins it through `main`.
4. A write-root spec targeting a mounted proposition that uses a namespace only the mount
   pins should refuse `invalid-input`, not raise an internal error. Task 2 pins it on the
   archive fixture.
5. `next` under a mounted session with no epoch should still list every row. Assessed
   rows read `assessed-unevaluated (no-epoch)`, and unassessed rows keep `ready` or
   `not-ready`. Task 5 pins it.

---

### Task 1: The session's corpora and the citation resolvers

**Files:**
- Modify: `python/src/science/config.py`. Add `ReadContext.session_mounts`,
  `has_read_mounts`, `session_ids`, `cited` and `own`, beside `mount_holding`.
- Modify: `python/tests/helpers/world.py`. Add `build_shared_contract_world`,
  `mount_config` and `add_mounted_evidence` after `add_archived_assessment`.
- Create: `python/tests/test_mount_citations.py`

**Interfaces:**
- Produces:
  - `ReadContext.session_mounts() -> tuple[Mount, ...]`
  - `ReadContext.has_read_mounts() -> bool`
  - `ReadContext.session_ids() -> frozenset[str]`
  - `ReadContext.cited(ref: str) -> Mount`
  - `ReadContext.own(ref: str) -> ReadView`
  - In helpers: `build_shared_contract_world(work: Path) -> ScienceConfig`, whose mount
    holds `proposition:shared` and an evidence-free `proposition:fresh`;
    `mount_config(cfg) -> ScienceConfig`; `write_shared_config(cfg) -> Path`; and
    `add_mounted_evidence(cfg, work) -> dict[str, str]`, with keys `data`, `spec`, `run`
    and `assessment`.

- [ ] **Step 1: Add the shared-contract fixture to `tests/helpers/world.py`**

It mirrors `build_two_corpus_world`, but both corpora pin `testing` at one identity: the
second-project shape, where a working corpus cites a mount it agrees with. Append after
`add_archived_assessment`:

```python
def build_shared_contract_world(work: Path) -> ScienceConfig:
    """Two corpora pinning `testing` at one identity: the write root `corpus`
    (with coordination) and the read mount `shared`, which holds the vocabulary
    lists and proposition:shared. The shape a working corpus citing mm30 takes
    (mount citations consumer spec, decision 2)."""
    from beliefs.claim import Referent, build_claim
    from beliefs.projection import project_claim
    from science.contracts import load_contract_document
    base = shipped_base_contract()
    testing, plan = load_contract_document(fixture_contract_document(work), base)
    biology = [shipped_domain_contract(ns) for ns in DOMAINS]
    writer_profile = compile_profile(base, biology + [testing], coordination=shipped_coordination(COORDINATION))
    mount_profile = compile_profile(base, biology + [testing])
    mount_root, corpus_root = work / "shared", work / "corpus"
    config = WorldConfig(work / "world", secrets.token_hex(16), (mount_root, corpus_root))
    init_world_root(config, authority=FIXTURE_AUTHORITY)
    world = open_world(config, authority=FIXTURE_AUTHORITY)
    for root, profile in ((mount_root, mount_profile), (corpus_root, writer_profile)):
        init_corpus_root(root, authority=FIXTURE_AUTHORITY)
        open_corpus(root, authority=FIXTURE_AUTHORITY, profile=profile).adopt_manifest(profile=CorpusPins(
            science_contract="science:" + profile.base_contract_identity,
            domains={ns: f"{ns}:{identity}" for ns, identity in profile.activated_contracts.items()},
        ))
        world.admit(root, provenance=Fresh())
    STORE_IDS[work] = init_store_root(work / "store", authority=FIXTURE_AUTHORITY)
    _install_holdings_reducer(world)
    cfg = ScienceConfig(world=config, operations_root=work / "ops", profile=writer_profile,
                        service_socket=work / "ops" / "service.sock", store_root=work / "store",
                        coordination=COORDINATION, write_root=corpus_root, plans=(plan,),
                        available_contracts=(testing,))
    mounted = mount_config(cfg)
    hold_fixture_dataset(mounted, "concepts.txt", CONCEPTS, "concept vocabulary")
    hold_fixture_dataset(mounted, "levels.txt", LEVELS, "level vocabulary")
    claim = build_claim(mount_profile, operator=plan.operator_for("affects", "concept", "protein"),
                        args=(Referent(sort=plan.sort_for("concept"), term="concept:disease-stage"),
                              Referent(sort=plan.sort_for("protein"), term="protein:PHF19")),
                        layer="causal", polarity="positive")
    mount = open_corpus(mount_root, authority=FIXTURE_AUTHORITY, profile=mount_profile)
    mount.add(stored.proposition_node(
        "shared", title="shared", claim=project_claim(claim),
        display_statement="concept:disease-stage affects protein:PHF19 (shared)"))
    # A second mounted proposition with no evidence anywhere: `next`'s readiness case.
    fresh = build_claim(mount_profile, operator=plan.operator_for("affects", "concept", "protein"),
                        args=(Referent(sort=plan.sort_for("concept"), term="concept:disease-stage"),
                              Referent(sort=plan.sort_for("protein"), term="protein:EZH2")),
                        layer="causal", polarity="positive")
    mount.add(stored.proposition_node(
        "fresh", title="fresh", claim=project_claim(fresh),
        display_statement="concept:disease-stage affects protein:EZH2 (fresh)"))
    return cfg


def write_shared_config(cfg: ScienceConfig) -> Path:
    """The launcher TOML for `build_shared_contract_world`: both roots pin
    `testing`, so no read contract is needed."""
    work = cfg.world.world_root.parent
    path = work / "science.toml"
    path.write_text(f'''\
world_root = "world"
world_id = "{cfg.world.world_id}"
corpus_roots = ["shared", "corpus"]
write_root = "corpus"
operations_root = "ops"
domains = {list(DOMAINS)!r}
contracts = ["testing.yaml"]
store_root = "store"
coordination = {COORDINATION}
''')
    return path


def mount_config(cfg: ScienceConfig) -> ScienceConfig:
    """`cfg`'s world with the `shared` mount as the write root, under the
    profile its manifest pins: the fixture's way to write the mount's records
    through the commands."""
    import dataclasses
    from beliefs.mount import compile_mount_profile
    root = cfg.world.world_root.parent / "shared"
    return dataclasses.replace(cfg, write_root=root, coordination=None,
                               profile=compile_mount_profile(root, available=cfg.available_contracts))


def add_mounted_evidence(cfg: ScienceConfig, work: Path) -> dict[str, str]:
    """In the mount: an observed dataset, a spec on proposition:shared over it,
    one run and its assessment (unverified), written through the commands with
    the mount as write root."""
    mounted = mount_config(cfg)
    data = hold_fixture_dataset(mounted, "data.txt", b"z\n", "expression", **OBSERVED)
    with open_rig(mounted, ("spec",)) as (d, _):
        spec = _minted_ref(d.invoke("spec", dict(SPEC_FIELDS, target="proposition:shared", dataset=data)).text,
                           "analysis-spec")
    run = mint_fixture_run(mounted, spec, data, fixture_bundle(work))
    with open_rig(mounted, ("assess",)) as (d, _):
        assessment = _minted_ref(d.invoke("assess", {"run": run}).text, "assessment")
    return {"data": data, "spec": spec, "run": run, "assessment": assessment}
```

Every name it uses (`secrets`, `WorldConfig`, `init_world_root`, `open_world`,
`init_corpus_root`, `open_corpus`, `Fresh`, `init_store_root`, `STORE_IDS`, `stored`,
`CorpusPins`, `compile_profile`, `shipped_*`) is already imported or defined in
`helpers/world.py` for `build_two_corpus_world`. Check with
`grep -n "^from\|^import" python/tests/helpers/world.py` and add only what is missing.

- [ ] **Step 2: Write the failing tests**

Create `python/tests/test_mount_citations.py`:

```python
"""Mount citations consumer spec, decisions 1–3: a write cites a record any
session corpus holds; a mutation target stays in the write root."""
import dataclasses

import pytest

from beliefs import stored
from beliefs.root import open_corpus
from helpers.world import (
    FIXTURE_AUTHORITY, add_mounted_evidence, build_shared_contract_world, mount_config,
)
from science.config import ReadContext
from science.refusal import Refused


@pytest.fixture
def shared(certified_work, monkeypatch):
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
    cfg = build_shared_contract_world(certified_work)
    return cfg, add_mounted_evidence(cfg, certified_work)


def _ids(cfg) -> dict[str, str]:
    return {mount.root.name: mount.corpus_id for mount in ReadContext.open(cfg).mounts()}


def test_a_mounted_record_is_cited_from_its_holder(shared):
    cfg, mounted = shared
    ctx = ReadContext.open(cfg)
    assert [m.root.name for m in ctx.session_mounts()] == sorted(
        ("corpus", "shared"), key=lambda name: _ids(cfg)[name])
    assert ctx.has_read_mounts() and ctx.session_ids() == frozenset(_ids(cfg).values())
    for ref in (mounted["data"], mounted["assessment"], "proposition:shared"):
        assert ctx.cited(ref).root.name == "shared"


def test_with_coordination_off_a_mounted_ref_refuses_naming_the_mount(shared):
    cfg, mounted = shared
    ctx = ReadContext.open(dataclasses.replace(cfg, coordination=None))
    assert [m.root.name for m in ctx.session_mounts()] == ["corpus"] and not ctx.has_read_mounts()
    with pytest.raises(Refused) as caught:
        ctx.cited(mounted["data"])
    assert caught.value.refusal.code == "invalid-input"
    assert _ids(cfg)["shared"] in caught.value.refusal.message
    assert "coordination" in caught.value.refusal.message


def test_a_ref_two_session_corpora_hold_refuses_naming_both(shared):
    cfg, _ = shared
    node = stored.proposition_node("twice", title="twice", claim={"operator": "affects"})
    for each in (cfg, mount_config(cfg)):
        open_corpus(each.write_root, authority=FIXTURE_AUTHORITY, profile=each.profile).add(node)
    with pytest.raises(Refused) as caught:
        ReadContext.open(cfg).cited("proposition:twice")
    assert caught.value.refusal.code == "invalid-input"
    assert all(corpus_id in caught.value.refusal.message for corpus_id in _ids(cfg).values())


def test_own_refuses_a_mounted_record_naming_the_mount(shared):
    cfg, mounted = shared
    with pytest.raises(Refused) as caught:
        ReadContext.open(cfg).own(mounted["spec"])
    assert caught.value.refusal.code == "invalid-input"
    assert _ids(cfg)["shared"] in caught.value.refusal.message
    assert "write root" in caught.value.refusal.message


def test_an_unheld_ref_refuses_without_a_hint(shared):
    cfg, _ = shared
    with pytest.raises(Refused) as caught:
        ReadContext.open(cfg).cited("proposition:nowhere")
    assert caught.value.refusal.message == "'proposition:nowhere' is not in the session's corpora"
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `just test-one tests/test_mount_citations.py`
Expected: FAIL with `AttributeError: 'ReadContext' object has no attribute 'session_mounts'`
(and `cited`, `own` likewise).

- [ ] **Step 4: Implement the resolvers in `config.py`**

Add these to `ReadContext`, directly after `mount_holding`:

```python
    def session_mounts(self) -> tuple[Mount, ...]:
        """The corpora a write may cite (consumer spec decision 1): the write
        root, plus every read mount when coordination is on, which is exactly
        what `open_session` hands the kernel writer as its read mounts."""
        mounts = self.mounts()
        if self.config.coordination is None:
            return tuple(mount for mount in mounts if mount.root == self.config.write_root)
        return mounts

    def has_read_mounts(self) -> bool:
        return len(self.session_mounts()) > 1

    def session_ids(self) -> frozenset[str]:
        return frozenset(mount.corpus_id for mount in self.session_mounts())

    def cited(self, ref: str) -> Mount:
        """The one session corpus holding `ref` (decision 2). Two holders are a
        duplicate location, refused rather than picked by corpus order; none
        refuses, naming a configured corpus outside the session that holds it."""
        session = self.session_mounts()
        holders = [mount for mount in session if mount.view.holds(ref)]
        if len(holders) > 1:
            raise Refused(Refusal(
                "invalid-input",
                f"{ref!r} is held by corpora {', '.join(m.corpus_id for m in holders)}; one address in two "
                "corpora is a duplicate location, and a citation never picks one"))
        if holders:
            return holders[0]
        inside = {mount.root for mount in session}
        outside = [corpus_id_at(root) for root in self.config.world.corpus_roots
                   if root not in inside and ReadView.opened_at(root).holds(ref)]
        where = (f"; corpus {', '.join(outside)} holds it, but coordination = false, so this session "
                 "mounts only the write root" if outside else "")
        raise Refused(Refusal("invalid-input", f"{ref!r} is not in the session's corpora{where}"))

    def own(self, ref: str) -> ReadView:
        """The write root's view, holding `ref`: a record a command changes is
        the write root's own (decision 3, kernel decision 1)."""
        view = self.write_view()
        if view.holds(ref):
            return view
        elsewhere = [mount.corpus_id for mount in self.mounts()
                     if mount.root != self.config.write_root and mount.view.holds(ref)]
        where = (f"; read mount {', '.join(elsewhere)} holds it, and a record this command changes must "
                 "be in the write root" if elsewhere else "")
        raise Refused(Refusal("invalid-input", f"{ref!r} is not in the write root{where}"))
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `just test-one tests/test_mount_citations.py`
Expected: `5 passed`.

- [ ] **Step 6: Commit**

```bash
just test-fast
tasks check
git add python/src/science/config.py python/tests/helpers/world.py python/tests/test_mount_citations.py tasks/
git commit -m "feat(config): resolve citations over the session's corpora"
```

---

### Task 2: Write commands cite over the session; the dispatcher names citation errors

**Files:**
- Modify: `python/src/science/commands/spec.py:118-140,154`. The target and dataset go
  through `cited`, and `--supersedes` through `own`.
- Modify: `python/src/science/commands/run.py:32-42` (`prepare`).
- Modify: `python/src/science/commands/assess.py:18-29`.
- Modify: `python/src/science/commands/verify.py:26-47`.
- Modify: `python/src/science/config.py`: remove `not_held`.
- Modify: `python/src/science/dispatch.py:236-262` (`_invoke_write`'s catch).
- Modify: `python/tests/helpers/world.py` (`mint_fixture_run`).
- Modify: `python/tests/test_write_root.py`. Its three part-3 refusal tests now describe
  lifted refusals.
- Modify: `python/tests/test_mount_citations.py` and
  `python/tests/test_dispatch_refusals.py`.

**Interfaces:**
- Consumes: Task 1's `cited`, `own`, `session_mounts`, `build_shared_contract_world`,
  `mount_config` and `add_mounted_evidence`.
- Produces: `spec`, `run`, `assess` and `verify` accept mounted refs, and
  `ReadContext.not_held` no longer exists.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_mount_citations.py`:

```python
from helpers.world import SPEC_FIELDS, _minted_ref, fixture_bundle, mint_fixture_run, open_rig


def test_spec_run_and_assess_in_the_write_root_cite_the_mount(shared, certified_work):
    """Decision 1: the second-project shape. Every new record lands in the
    write root, and every record it cites stays in the mount."""
    cfg, mounted = shared
    with open_rig(cfg, ("spec",)) as (d, _):
        spec = _minted_ref(d.invoke("spec", dict(SPEC_FIELDS, target="proposition:shared",
                                                 dataset=mounted["data"])).text, "analysis-spec")
    run = mint_fixture_run(cfg, spec, mounted["data"], fixture_bundle(certified_work))
    with open_rig(cfg, ("assess",)) as (d, _):
        assessment = _minted_ref(d.invoke("assess", {"run": run}).text, "assessment")
    own = ReadContext.open(cfg).write_view()
    assert own.holds(spec) and own.holds(run) and own.holds(assessment)
    assert not own.holds("proposition:shared") and not own.holds(mounted["data"])


def test_run_prepares_a_mounted_spec_and_dataset(shared, certified_work):
    from science.commands.run import prepare
    cfg, mounted = shared
    code, entrypoint, targets = fixture_bundle(certified_work)
    prepared = prepare(ReadContext.open(cfg), mounted["spec"], mounted["data"], str(code), entrypoint, targets)
    assert list(prepared["held_inputs"]) == [prepared["spec"].input_roles[0].dataset]


def test_verify_of_a_mounted_assessment_lands_in_the_write_root(shared, certified_work):
    cfg, mounted = shared
    code, entrypoint, _ = fixture_bundle(certified_work)
    with open_rig(cfg, ("verify",)) as (d, _):
        out = d.invoke("verify", {"assessment": mounted["assessment"], "code": str(code),
                                  "entrypoint": entrypoint})
    verification = _minted_ref(out.text, "verification")
    assert ReadContext.open(cfg).write_view().holds(verification)


def test_supersedes_names_a_write_root_spec_only(shared):
    cfg, mounted = shared
    with open_rig(cfg, ("spec",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("spec", dict(SPEC_FIELDS, target="proposition:shared", dataset=mounted["data"],
                                  supersedes=mounted["spec"]))
    assert caught.value.refusal.code == "invalid-input"
    assert _ids(cfg)["shared"] in caught.value.refusal.message
    assert "write root" in caught.value.refusal.message
```

Append to `python/tests/test_dispatch_refusals.py`:

```python
@pytest.mark.parametrize("raised", [
    lambda: __import__("beliefs.errors", fromlist=["x"]).CitationContractMismatch(
        Path("/m"), "testing", "testing:aa", "testing:bb"),
    lambda: __import__("beliefs.errors", fromlist=["x"]).BuildContended("read mount /m: build-contended"),
], ids=["CitationContractMismatch", "BuildContended"])
def test_a_citation_error_from_the_writer_is_a_named_kernel_refusal(certified_work, raised):
    """Consumer spec decision 5: these are not WriteRefused, and would
    otherwise escape as internal errors."""
    from science.session import open_session
    from science.config import ReadContext
    error = raised()
    citing = Declaration("citing", "fixture",
                         WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                         MIN_OUTPUT_BUDGET, (), (), Path("."))

    def handler(ctx, writer):
        raise error

    cfg = build_fixture_world(certified_work)
    session = open_session(cfg)
    try:
        d = Dispatcher((citing,), {"citing": handler}, ReadContext.open(cfg), session=session)
        with pytest.raises(Refused) as caught:
            d.invoke("citing", {})
    finally:
        session.close()
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == type(error).__name__
    assert caught.value.refusal.message == str(error)


def test_a_duplicate_citation_from_the_writer_is_a_named_kernel_refusal(certified_work):
    from beliefs.errors import AddressMapConflict
    from beliefs.corpus import Finding
    from science.session import open_session
    from science.config import ReadContext
    error = AddressMapConflict(Finding("error", "duplicate-location", "proposition:twice", "c1, c2",
                                       "proposition:twice: held by corpora c1, c2"))
    citing = Declaration("citing", "fixture",
                         WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                         MIN_OUTPUT_BUDGET, (), (), Path("."))

    def handler(ctx, writer):
        raise error

    cfg = build_fixture_world(certified_work)
    session = open_session(cfg)
    try:
        d = Dispatcher((citing,), {"citing": handler}, ReadContext.open(cfg), session=session)
        with pytest.raises(Refused) as caught:
            d.invoke("citing", {})
    finally:
        session.close()
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "AddressMapConflict"
```

`beliefs.corpus.Finding` is a dataclass with fields
`(severity, code, ref, detail, message)`, checked at `corpus.py:211`.

Then rewrite the three part-3 tests in `python/tests/test_write_root.py`, because their
refusals are lifted:

```python
def test_a_spec_over_a_read_mount_dataset_is_minted(two):
    """Consumer spec decision 1 lifts part 3's refusal: the kernel now judges
    an assessment's observed dataset over the session's corpora."""
    data = hold_fixture_dataset(archive_config(two), "data.txt", b"y\n", "expression", **OBSERVED)
    with open_rig(two, ("claim", "spec")) as (d, ctx):
        d.invoke("claim", CLAIM)
        out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:claimed", dataset=data))
        assert "analysis-spec:" in out.text
        assert not ctx.write_view().holds(data)


def test_a_spec_on_a_proposition_only_the_mount_can_decode_refuses(two):
    """Consumer spec decision 2: proposition:archived uses the archive's
    corpus-local contract, which the writer does not pin, so the writer's own
    decode refuses, the mm30 case the second-project corpus must pin around."""
    data = hold_fixture_dataset(archive_config(two), "data.txt", b"y\n", "expression", **OBSERVED)
    with open_rig(two, ("spec",)) as (d, ctx):
        with pytest.raises(Refused) as caught:
            d.invoke("spec", dict(SPEC_FIELDS, target="proposition:archived", dataset=data))
        assert not any(n.kind == "analysis-spec" for n in ctx.write_view().iter_stored())
    assert caught.value.refusal.code == "invalid-input"
```

Keep `test_holding_bytes_a_read_mount_declares_refuses_naming_its_record` unchanged
(decision 4). Replace `test_run_given_a_read_mount_dataset_refuses_naming_the_mount_before_any_act`:
its body stays, with these changes:
- the test is renamed `test_run_given_a_mounted_dataset_the_spec_does_not_observe_refuses_before_any_act`;
- the final assertion becomes:

```python
    assert caught.value.refusal.code == "invalid-input"
    assert "is not the dataset the spec observes" in caught.value.refusal.message
```

Drop the now-unused `archive_id` line in that test.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_mount_citations.py tests/test_dispatch_refusals.py tests/test_write_root.py`
Expected: FAIL. The new citation tests refuse `invalid-input … this command reads the
write root`. The dispatcher tests fail with the raw exception propagating (not
`Refused`). `test_a_spec_over_a_read_mount_dataset_is_minted` refuses.

- [ ] **Step 3: Move every citation to `cited`/`own`**

In `commands/spec.py`, replace the block from `view = ctx.write_view()` through the
supersedes check, and the later `view.get(target)`:

```python
    profile = ctx.config.profile
    target_view, dataset_view = ctx.cited(target).view, ctx.cited(dataset).view
    try:
        address = dataset_address(stored.dataset_declaration(dataset_view.get(dataset)))
    except MalformedRecord as caught:
        _refuse(f"{dataset}: {caught}")
    if address is None:
        _refuse(f"{dataset} declares no content identity")
    superseded = None
    if supersedes is not None:
        # A record ref the corpus holds, resolved before any act: a bare identity
        # or an unheld spec refuses here rather than escaping as MalformedRecord.
        try:
            superseded = stored.local_id("analysis-spec", supersedes)
        except MalformedRecord as caught:
            _refuse(f"supersedes {supersedes!r} is not an analysis-spec ref: {caught}")
        ctx.own(supersedes)  # a mutation target is the write root's (decision 3)
```

and further down:

```python
        claim, _ = claim_from_stored(target_view.get(target), profile=profile, snapshot=snapshot)
```

In `commands/run.py`, replace `prepare`'s first lines:

```python
    """Everything the boundary needs, validated; shared with verify. The spec
    and dataset are cited from whichever session corpus holds them, decoded
    under the writer's profile (consumer spec decision 2)."""
    spec_view, dataset_view = ctx.cited(spec_ref).view, ctx.cited(dataset_ref).view
    try:
        spec = stored.analysis_spec_value(spec_view.get(spec_ref), profile=ctx.config.profile)
        address = dataset_address(stored.dataset_declaration(dataset_view.get(dataset_ref)))
    except MalformedRecord as caught:
        _refuse(str(caught))
```

`handle`'s read-back of the minted run keeps `ctx.write_view()`.

In `commands/assess.py`, replace the reads at the top of `handle`:

```python
def handle(ctx, writer, *, run) -> Report:
    view = ctx.cited(run).view
    try:
        closure = decode_run_closure(view.get(run))
    except MalformedRecord as caught:
        _refuse(f"{run}: {caught}")
    if not closure.recipe.spec_identity:
        _refuse(f"{run} names no analysis-spec")
    spec_ref = stored.typed_ref("analysis-spec", closure.recipe.spec_identity)
    spec = stored.analysis_spec_value(ctx.cited(spec_ref).view.get(spec_ref), profile=ctx.config.profile)
```

First run `grep -rn "names no analysis-spec" python/tests`. A test pinning the old
`this corpus holds` wording takes the new message: an unheld spec now refuses with
`cited`'s `is not in the session's corpora`.

In `commands/verify.py`, replace `handle`'s reads up to `dataset_ref = found[1].id`:

```python
def handle(ctx, writer, *, assessment, code, entrypoint, cores=None) -> Report:
    try:
        value = stored.assessment_value(ctx.cited(assessment).view.get(assessment), profile=ctx.config.profile)
    except MalformedRecord as caught:
        _refuse(f"{assessment}: {caught}")
    run_ref = stored.typed_ref("run", value.run)
    spec_ref = stored.typed_ref("analysis-spec", value.spec)
    original = decode_run_closure(ctx.cited(run_ref).view.get(run_ref))
    (role,) = stored.analysis_spec_value(ctx.cited(spec_ref).view.get(spec_ref),
                                         profile=ctx.config.profile).input_roles
    # The session's corpora, as every citation reads (consumer spec decision 1).
    found = dataset_at(tuple((mount.corpus_id, mount.view) for mount in ctx.session_mounts()), role.dataset)
    if found is None:
        _refuse(f"the spec's dataset {role.dataset} is not in the session's corpora")
    dataset_ref = found[1].id
```

Remove the now-unused `corpus_id_at` import from `verify.py`. The read-back
`view = ctx.write_view()` after the replay stays.

In `config.py`, delete `not_held`. Then
`grep -rn "not_held" python/src python/tests` must print nothing.

In `tests/helpers/world.py` `mint_fixture_run`, replace the two `view.get` reads:

```python
    spec = stored.analysis_spec_value(ctx.cited(spec_ref).view.get(spec_ref), profile=cfg.profile)
    address = dataset_address(stored.dataset_declaration(ctx.cited(dataset_ref).view.get(dataset_ref)))
```

and delete its `view = ctx.write_view()` line. A run written through the bare durable
port may name a dataset another corpus holds; the kernel's J16 sets up the same dangling
edge.

- [ ] **Step 4: Catch the three citation errors in the dispatcher**

In `dispatch.py` `_invoke_write`, extend the imports and the catch around the handler
call:

```python
        from beliefs.errors import AddressMapConflict, BuildContended, CitationContractMismatch, WriteRefused
```

```python
            except (PermitExceeded, KernelRefusalValue, WriteRefused,
                    CitationContractMismatch, AddressMapConflict, BuildContended) as caught:
                return self._close_refused(iid, self._kernel_refusal(caught))
```

`_kernel_refusal`'s generic arm already yields
`Refusal("kernel-refused", str(error), {"kind": type(error).__name__})`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `just test-one tests/test_mount_citations.py tests/test_dispatch_refusals.py tests/test_write_root.py`
Expected: all pass. If `test_a_spec_on_a_proposition_only_the_mount_can_decode_refuses`
fails with an exception other than `Refused`, stop and report it. `claim_from_stored`
raising outside `AUTHORING_ERRORS` is a spec decision-2 finding, not something to catch
here.

- [ ] **Step 6: Commit**

```bash
just test-fast
tasks check
git add python/src/science python/tests tasks/
git commit -m "feat(commands): spec, run, assess and verify cite the session's read mounts"
```

---

### Task 3: Epoch currency and `science epoch`

**Files:**
- Create: `python/src/science/world_belief.py`
- Modify: `python/src/science/refusal.py:9-13` (`CODES`).
- Modify: `python/src/science/schema.py:14` (`RESERVED_COMMANDS`).
- Modify: `python/src/science/cli.py:76-94` (the parser) and `:170` and `:255`
  (`_framework_verb`).
- Modify: `python/tests/test_canonical.py:93`, which counts 11 codes.
- Create: `python/tests/test_epoch_verb.py`

**Interfaces:**
- Consumes: Task 1's `ReadContext.session_ids()` and the fixtures.
- Produces (in `science.world_belief`):
  - `Current(epoch, view)`, a frozen dataclass.
  - `epoch_currency(world, session_ids: frozenset[str]) -> Current`. It raises
    `Refused` with code `no-epoch` or `epoch-stale`, and its `data` carries `missing`,
    `extra` and `drifted`, each a sorted list of corpus ids.
  - `build_over(config, coverage: frozenset[str])`, which returns the published
    `Epoch`.
  - `Published(state, packaging_identity, coverage)`.
  - `publish_session_epoch(config) -> Published`, with `state` either `"current"` or
    `"built"`.
  - `EPOCH_CODES = frozenset({"no-epoch", "epoch-stale"})`.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_epoch_verb.py`:

```python
"""Consumer spec decisions 7, 8 and 12: an epoch is current for a session only
at exact coverage with no drift; `science epoch` builds one or reuses it."""
import dataclasses

import pytest

from beliefs.root import chain_head_reader, init_corpus_root, open_corpus, open_world
from beliefs.consulted import CorpusPins
from beliefs.world import Fresh, WorldConfig
from helpers.world import FIXTURE_AUTHORITY, add_mounted_evidence, build_shared_contract_world, fixture_proposition_node
from science.config import ReadContext
from science.refusal import Refused
from science.world_belief import build_over, epoch_currency, publish_session_epoch


@pytest.fixture
def shared(certified_work):
    cfg = build_shared_contract_world(certified_work)
    add_mounted_evidence(cfg, certified_work)
    return cfg


def _refusal(cfg):
    ctx = ReadContext.open(cfg)
    with pytest.raises(Refused) as caught:
        epoch_currency(ctx.world, ctx.session_ids())
    return caught.value.refusal


def test_no_epoch_refuses_naming_the_remedy(shared):
    refusal = _refusal(shared)
    assert refusal.code == "no-epoch" and "science epoch" in refusal.message


def test_the_verb_builds_over_exactly_the_session_corpora(shared):
    published = publish_session_epoch(shared)
    assert published.state == "built"
    assert frozenset(cid for cid, _ in published.coverage) == ReadContext.open(shared).session_ids()
    ctx = ReadContext.open(shared)
    assert epoch_currency(ctx.world, ctx.session_ids()).epoch.packaging_identity == published.packaging_identity


def test_a_rerun_with_nothing_changed_builds_nothing(shared):
    """Review round 1, P2 3: a second build would anchor a moved chain head and
    mint a new identity, so the verb reuses a current epoch. Production-backed:
    no chain head is injected."""
    first = publish_session_epoch(shared)
    world_root = shared.world.world_root
    pointer = (world_root / "epochs" / "current").read_bytes()
    head = chain_head_reader()(world_root)
    again = publish_session_epoch(shared)
    assert again.state == "current" and again.packaging_identity == first.packaging_identity
    assert (world_root / "epochs" / "current").read_bytes() == pointer
    assert chain_head_reader()(world_root) == head


def test_a_write_root_write_makes_it_stale_and_the_verb_rebuilds(shared):
    first = publish_session_epoch(shared)
    open_corpus(shared.write_root, authority=FIXTURE_AUTHORITY, profile=shared.profile).add(
        fixture_proposition_node("later"))
    refusal = _refusal(shared)
    write_id = ReadContext.open(shared).cited("proposition:later").corpus_id
    assert refusal.code == "epoch-stale" and refusal.data["drifted"] == [write_id]
    rebuilt = publish_session_epoch(shared)
    assert rebuilt.state == "built" and rebuilt.packaging_identity != first.packaging_identity


def test_a_coordination_write_after_the_epoch_leaves_it_current(shared):
    """Consumer spec decision 7: belief never reads coordination records, and
    a view at the epoch holds only mapped ones, so the answer is unchanged."""
    from helpers.world import QUERY, open_rig
    first = publish_session_epoch(shared)
    with open_rig(shared, ("project",)) as (d, _):
        d.invoke("project", {"name": "health", "query": QUERY})
    ctx = ReadContext.open(shared)
    assert epoch_currency(ctx.world, ctx.session_ids()).epoch.packaging_identity == first.packaging_identity
    assert publish_session_epoch(shared).state == "current"


def test_coverage_missing_a_session_corpus_is_stale(shared):
    ctx = ReadContext.open(shared)
    write_id = next(m.corpus_id for m in ctx.session_mounts() if m.root == shared.write_root)
    build_over(shared, ctx.session_ids() - {write_id})
    refusal = _refusal(shared)
    assert refusal.code == "epoch-stale" and refusal.data["missing"] == [write_id] and refusal.data["extra"] == []


def test_coverage_with_an_extra_corpus_is_stale_and_the_verb_rebuilds_exactly(shared, certified_work):
    """Review round 1, P2 2: an epoch another configuration published over a
    superset would read the extra corpus as absent and answer
    unavailable-corpus-absent."""
    extra_root = certified_work / "extra"
    init_corpus_root(extra_root, authority=FIXTURE_AUTHORITY)
    profile = ReadContext.open(shared)._profiles[shared.write_root]
    open_corpus(extra_root, authority=FIXTURE_AUTHORITY, profile=profile).adopt_manifest(profile=CorpusPins(
        science_contract="science:" + profile.base_contract_identity,
        domains={ns: f"{ns}:{identity}" for ns, identity in profile.activated_contracts.items()}))
    wide = dataclasses.replace(shared, world=WorldConfig(
        shared.world.world_root, shared.world.world_id, shared.world.corpus_roots + (extra_root,)))
    open_world(wide.world, authority=FIXTURE_AUTHORITY).admit(extra_root, provenance=Fresh())
    extra_id = next(m.corpus_id for m in ReadContext.open(wide).mounts() if m.root == extra_root)
    build_over(wide, ReadContext.open(wide).session_ids())
    refusal = _refusal(shared)
    assert refusal.code == "epoch-stale" and refusal.data["extra"] == [extra_id] and refusal.data["missing"] == []
    rebuilt = publish_session_epoch(shared)
    assert rebuilt.state == "built"
    assert frozenset(cid for cid, _ in rebuilt.coverage) == ReadContext.open(shared).session_ids()


def test_a_contended_corpus_refuses_naming_the_lock(shared, monkeypatch):
    import science.world_belief as world_belief
    from beliefs.errors import BuildContended

    def contended(*_, **__):
        raise BuildContended("an epoch build cannot capture this root: its operation lock is held")

    monkeypatch.setattr(world_belief, "build_epoch", contended)
    with pytest.raises(Refused) as caught:
        publish_session_epoch(shared)
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "BuildContended"


def test_the_cli_verb_prints_built_then_current(shared, capsys):
    from helpers.world import write_shared_config
    from science.cli import main
    path = write_shared_config(shared)
    assert main(["epoch", "--config", str(path)]) == 0
    assert capsys.readouterr().out.startswith("built: ")
    assert main(["epoch", "--config", str(path)]) == 0
    assert capsys.readouterr().out.startswith("current: ")
```

`write_shared_config` is Task 1's helper. The two-corpus config writer hard-codes the
`archive` root and a read contract this world does not have.

Also bump `test_canonical.py`'s count: `assert "kernel-refused" in CODES and len(CODES) == 13`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_epoch_verb.py tests/test_canonical.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'science.world_belief'`, and
`13 != 11` in `test_canonical`.

- [ ] **Step 3: Add the codes and reserve the name**

In `refusal.py`:

```python
CODES = frozenset({
    "unknown-command", "invalid-input", "permit-exceeded", "outcome-unknown",
    "unknown-cursor", "stale-cursor", "input-mismatch", "kernel-refused",
    "no-current-project", "unknown-project", "ambiguous-project",
    "no-epoch", "epoch-stale",
})
```

In `schema.py`:

```python
RESERVED_COMMANDS = frozenset({"continue", "serve", "mcp", "adapters", "build", "epoch"})
```

- [ ] **Step 4: Write `science/world_belief.py`**

```python
"""Belief over a session's corpora at an epoch (consumer spec decisions 7–8).

A mounted session's belief is a world read at the current epoch, and only at
one that is current for the session: coverage equal to the session corpora's
ids, and no drift in any of them. `science epoch` is the operator verb that
makes one current; it reuses an epoch already current rather than rebuilding,
because a rebuild anchors a moved world chain head and mints a new identity."""
from __future__ import annotations

from dataclasses import dataclass

from beliefs.coordination import COORDINATION_KINDS
from beliefs.errors import BuildContended, EpochUnknown
from beliefs.permit import Authority, WritePermit
from beliefs.root import install_shipped_world_rules, open_world
from beliefs.world.epoch import DerivationBindings, build_epoch
from beliefs.world.read import current_epoch
from beliefs.world.rules import shipped_rule_bundles
from beliefs.world.view import WorldReadView, open_world_view

from science.refusal import Refusal, Refused

EPOCH_CODES = frozenset({"no-epoch", "epoch-stale"})
REMEDY = "run `science epoch` to publish one over the session's corpora"

# Which derivation each shipped rule's symbol fills. The rules store is keyed by
# identity and knows nothing of kinds, so the join is the caller's (beliefs
# epoch design §7.5); a symbol missing here is a KeyError, never a guess.
SYMBOL_FIELDS = {
    "derive_producer_snapshot": "producer",
    "enumerate_retractions": "retraction",
    "enumerate_certifications": "certification",
    "reduce_coreference": "coreference",
}
EPOCH_AUTHORITY = Authority(WritePermit(frozenset(), frozenset({"epoch"})), "science-epoch")


@dataclass(frozen=True)
class Current:
    epoch: object  # beliefs.world.epoch.Epoch
    view: WorldReadView


@dataclass(frozen=True)
class Published:
    state: str  # "current" | "built"
    packaging_identity: str
    coverage: tuple[tuple[str, str], ...]


def _stale(message: str, *, missing=(), extra=(), drifted=()) -> Refused:
    return Refused(Refusal("epoch-stale", f"{message}; {REMEDY}",
                           {"missing": sorted(missing), "extra": sorted(extra), "drifted": sorted(drifted)}))


def _inert(view: WorldReadView, report) -> bool:
    """Drift belief cannot see (consumer spec decision 7): the state moved only
    by unmapped records, every one of a coordination kind. A moved state with
    nothing unmapped is not inert; a changed mapped record never gets here,
    because `open_world_view` refuses it."""
    if not report.unmapped:
        return False
    unmapped = frozenset(report.unmapped)
    return all(node.kind in COORDINATION_KINDS
               for node in view.captured_records(report.corpus_id) if node.uid in unmapped)


def epoch_currency(world, session_ids: frozenset[str]) -> Current:
    """The current epoch and its view, when that epoch is current for the
    session; otherwise `no-epoch` or `epoch-stale`, naming the corpora."""
    try:
        published = current_epoch(world)
    except EpochUnknown:
        raise Refused(Refusal("no-epoch", f"this world has published no epoch; {REMEDY}")) from None
    covered = frozenset(corpus_id for corpus_id, _ in published.coverage)
    missing, extra = session_ids - covered, covered - session_ids
    if missing or extra:
        raise _stale(f"epoch {published.packaging_identity} covers {', '.join(sorted(covered))}, not exactly the "
                     f"session's {', '.join(sorted(session_ids))}", missing=missing, extra=extra)
    view = open_world_view(world, published)
    drifted = sorted(report.corpus_id for report in view.drift() if not _inert(view, report))
    if drifted:
        raise _stale(f"corpora {', '.join(drifted)} have moved since epoch {published.packaging_identity}",
                     drifted=drifted)
    return Current(published, view)


def build_over(config, coverage: frozenset[str]):
    """Install the shipped rules (idempotent: identical bytes submit nothing)
    and publish one epoch over exactly `coverage`."""
    world = open_world(config.world, authority=EPOCH_AUTHORITY)
    bindings = dict(zip((bundle.symbol for bundle in shipped_rule_bundles()),
                        install_shipped_world_rules(world), strict=True))
    fields = {field: bindings[symbol] for symbol, field in SYMBOL_FIELDS.items()}
    try:
        return build_epoch(world, coverage=coverage, bindings=DerivationBindings(**fields))
    except BuildContended as caught:
        raise Refused(Refusal("kernel-refused", str(caught), {"kind": "BuildContended"})) from None


def publish_session_epoch(config) -> Published:
    """`science epoch`: reuse the current epoch when it is current for the
    session; otherwise build one over exactly the session's corpora."""
    from science.config import ReadContext

    ctx = ReadContext.open(config)
    session_ids = ctx.session_ids()
    try:
        current = epoch_currency(ctx.world, session_ids)
    except Refused as caught:
        if caught.refusal.code not in EPOCH_CODES:
            raise
    else:
        return Published("current", current.epoch.packaging_identity, current.epoch.coverage)
    built = build_over(config, session_ids)
    return Published("built", built.packaging_identity, built.coverage)
```

All imports above are confirmed at their definitions (beliefs `world/rules.py:315`,
`world/epoch.py:1359,1392`, `world/view.py:70,263`, `root.py:1975,1988`).

- [ ] **Step 5: Wire the operator verb into `cli.py`**

In `build_parser`, after the `build` subparser:

```python
    epoch = subparsers.add_parser("epoch", help="Publish an epoch over the session's corpora, or report the current one")
    epoch.add_argument("--config", type=Path)
```

In `main`, change the framework-verb set to
`{"mcp", "adapters", "build", "serve", "epoch"}`. In `_framework_verb`, before the final
`raise NotImplementedError`:

```python
    if namespace.command == "epoch":
        from science.world_belief import publish_session_epoch

        published = publish_session_epoch(load_config(resolve_config_path(namespace.config)))
        sys.stdout.write(f"{published.state}: {published.packaging_identity}\n")
        sys.stdout.writelines(f"  {corpus_id} {state}\n" for corpus_id, state in published.coverage)
        return EXIT_OK
```

A `Refused` from it reaches `main`'s existing `except Refused` and exits `EXIT_REFUSED`
(3) with the JSON line.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `just test-one tests/test_epoch_verb.py tests/test_canonical.py tests/test_cli.py`
Expected: all pass. `test_cli.py` covers the parser; if it enumerates the framework verbs
by name, add `epoch` to its expectation.

- [ ] **Step 7: Commit**

```bash
just test-fast
tasks check
git add python/src/science python/tests tasks/
git commit -m "feat(cli): science epoch publishes or reuses the session's epoch"
```

---

### Task 4: Belief reads a mounted session at the current epoch

**Files:**
- Modify: `python/src/science/world_belief.py`. Add `world_context`.
- Modify: `python/src/science/config.py`:
  - add `_world_read`, `world_read` and `epoch_refusal`;
  - change `gather_inputs` and `evaluate`;
  - delete `_refuse_foreign_observations` and its call in `_context`.
- Modify: `python/tests/test_two_corpora.py`. Its fixture publishes an epoch, and the
  foreign-observation test is replaced.
- Modify: `python/tests/test_mount_citations.py`.

**Interfaces:**
- Consumes: Task 3's `epoch_currency`, `Current`, `publish_session_epoch` and
  `EPOCH_CODES`.
- Produces:
  - `ReadContext.world_read() -> Current`, which raises `Refused` with an epoch code.
  - `ReadContext.epoch_refusal() -> Refusal | None`.
  - `world_belief.world_context(current, observations, pins) -> SuppliedContext`.
  - `ReadContext.gather_inputs` and `evaluate` choose the mode with `has_read_mounts()`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_mount_citations.py`:

```python
def _walk(cfg, mounted, work) -> str:
    """spec → run → assess in the write root over the mount's proposition and
    data; returns the assessment ref."""
    with open_rig(cfg, ("spec",)) as (d, _):
        spec = _minted_ref(d.invoke("spec", dict(SPEC_FIELDS, target="proposition:shared",
                                                 dataset=mounted["data"])).text, "analysis-spec")
    run = mint_fixture_run(cfg, spec, mounted["data"], fixture_bundle(work))
    with open_rig(cfg, ("assess",)) as (d, _):
        return _minted_ref(d.invoke("assess", {"run": run}).text, "assessment")


def test_mounted_belief_needs_an_epoch(shared, certified_work):
    from science.commands.belief import handle as belief
    cfg, mounted = shared
    _walk(cfg, mounted, certified_work)
    with pytest.raises(Refused) as caught:
        belief(ReadContext.open(cfg), proposition="proposition:shared")
    assert caught.value.refusal.code == "no-epoch"


def test_at_a_current_epoch_belief_counts_the_write_roots_assessment_of_a_mounted_proposition(
        shared, certified_work):
    from science.commands.belief import handle as belief
    from science.world_belief import publish_session_epoch
    cfg, mounted = shared
    assessment = _walk(cfg, mounted, certified_work)
    publish_session_epoch(cfg)
    ctx = ReadContext.open(cfg)
    inputs = ctx.gather_inputs("proposition:shared")
    local = stored.assessment_value(ctx.write_view().get(assessment), profile=cfg.profile).identity()
    held = stored.assessment_value(ctx.cited(mounted["assessment"]).view.get(mounted["assessment"]),
                                   profile=cfg.profile).identity()
    assert {local, held} <= {a.identity() for a in inputs.assessments}
    report = belief(ctx, proposition="proposition:shared")
    assert dict(report[1].pairs)["kind"] in ("Belief", "NoBelief")


def test_a_read_mount_write_after_the_epoch_is_stale_naming_the_mount(shared, certified_work):
    from science.commands.belief import handle as belief
    from science.world_belief import publish_session_epoch
    cfg, mounted = shared
    publish_session_epoch(cfg)
    mounted_cfg = mount_config(cfg)
    open_corpus(mounted_cfg.write_root, authority=FIXTURE_AUTHORITY, profile=mounted_cfg.profile).add(
        stored.proposition_node("late", title="late", claim={"operator": "affects"}))
    with pytest.raises(Refused) as caught:
        belief(ReadContext.open(cfg), proposition="proposition:shared")
    assert caught.value.refusal.code == "epoch-stale"
    assert caught.value.refusal.data["drifted"] == [_ids(cfg)["shared"]]


def test_with_coordination_off_belief_stays_corpus_local_without_an_epoch(shared):
    """Review focus 1: no read mounts, no epoch needed."""
    from science.commands.belief import handle as belief
    cfg, _ = shared
    local = dataclasses.replace(cfg, coordination=None)
    report = belief(ReadContext.open(local), proposition="proposition:shared")
    assert dict(report[1].pairs)["kind"] in ("Belief", "NoBelief", "Refused")
```

The last test reads `proposition:shared` from its holder alone, which is today's path.
With coordination off, `mount_holding` still finds it in the configured `shared` root.

In `python/tests/test_two_corpora.py`:

1. End the `world` fixture with an epoch, so its existing belief and `next` tests read a
   current one:

```python
    from science.world_belief import publish_session_epoch
    publish_session_epoch(cfg)
    return cfg
```

2. Replace `test_an_assessment_resting_on_a_dataset_its_corpus_lacks_refuses_naming_it`
   with the kernel's refusal, now that science's guard is gone (consumer spec
   decision 6):

```python
def test_a_corpus_local_read_of_evidence_resting_outside_the_corpus_is_the_kernels_refusal(world):
    """Consumer spec decision 6: science's guard is gone; the kernel's
    corpus-local gather refuses input-outside-corpus itself. A view hiding the
    observed dataset stands in for an edited corpus."""
    from beliefs import stored
    from beliefs.belief import Refused as BeliefRefused
    from science.closure import evaluate
    ctx = ReadContext.open(world)
    mount = ctx.mount_holding("proposition:claimed")
    (assessment,) = [n for n in mount.view.iter_stored() if n.kind == "assessment"]
    run = stored.typed_ref("run", stored.assessment_value(assessment, profile=mount.profile).run)
    (hidden,) = stored.inputs_of(mount.view.get(run), stored.OBSERVES)

    class Hiding:
        def __init__(self, view):
            self._view = view

        def holds(self, ref):
            return ref != hidden and self._view.holds(ref)

        def __getattr__(self, name):
            return getattr(self._view, name)

    hiding = dataclasses.replace(mount, view=Hiding(mount.view))
    observations = ctx.observations()
    answer = evaluate(hiding.view, "proposition:claimed", observations=observations,
                      context=ctx._context(hiding, observations, "proposition:claimed"),
                      profile=mount.profile, resolution=ctx.snapshot(mount.profile))
    assert isinstance(answer, BeliefRefused) and answer.reason.startswith("input-outside-corpus")
    assert hidden in answer.reason
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_mount_citations.py tests/test_two_corpora.py`
Expected: FAIL.
- `test_mounted_belief_needs_an_epoch` gets an answer, not `no-epoch`.
- The counting test misses the write root's assessment, because `gather` reads only the
  mount.
- The replaced two-corpora test fails on science's own `invalid-input`.

- [ ] **Step 3: Add `world_context` to `world_belief.py`**

```python
def world_context(current: Current, observations, pins):
    """The supplied context of a world read (beliefs J20's recipe): lineage
    rooted at every observed dataset the epoch maps, the epoch's producer
    snapshot, and each covered corpus's pins. `gather` fills node_corpus."""
    from beliefs.belief import SuppliedContext
    from beliefs.corpus import lineage_snapshot

    view = current.view
    return SuppliedContext(
        snapshot=lineage_snapshot(view, sorted(address for address in observations if view.holds(address))),
        producer_snapshot_identity=view.producer_snapshot_identity(),
        node_corpus={},
        pins=pins,
    )
```

- [ ] **Step 4: Switch `ReadContext`'s belief reads by mode**

In `config.py`, add after `has_read_mounts`:

```python
    @cached_property
    def _world_read(self):
        """The session's epoch currency, computed once per context: a `Current`,
        or the `Refused` saying why there is none (consumer spec decision 7)."""
        from science.world_belief import epoch_currency
        try:
            return epoch_currency(self.world, self.session_ids())
        except Refused as caught:
            return caught

    def world_read(self):
        current = self._world_read
        if isinstance(current, Refused):
            raise current
        return current

    def epoch_refusal(self) -> Refusal | None:
        return self._world_read.refusal if isinstance(self._world_read, Refused) else None

    def _world_context(self, current):
        from science.world_belief import world_context
        pins = {mount.corpus_id: self.pins(mount.root) for mount in self.session_mounts()}
        return world_context(current, self.observations(), pins)
```

Replace `gather_inputs` and `evaluate`:

```python
    def gather_inputs(self, proposition: str):
        from science.closure import gather_inputs
        mount = self.mount_holding(proposition)
        if self.has_read_mounts():
            current = self.world_read()
            return gather_inputs(current.view, proposition, context=self._world_context(current),
                                 profile=mount.profile, resolution=self.snapshot(mount.profile))
        observations = self.observations()
        return gather_inputs(mount.view, proposition, context=self._context(mount, observations, proposition),
                             profile=mount.profile, resolution=self.snapshot(mount.profile))

    def evaluate(self, proposition: str):
        from science.closure import evaluate
        mount = self.mount_holding(proposition)
        observations = self.observations()
        if self.has_read_mounts():
            current = self.world_read()
            return evaluate(current.view, proposition, observations=observations,
                            context=self._world_context(current), profile=mount.profile,
                            resolution=self.snapshot(mount.profile))
        return evaluate(mount.view, proposition, observations=observations,
                        context=self._context(mount, observations, proposition),
                        profile=mount.profile, resolution=self.snapshot(mount.profile))
```

In `_context`, delete the `self._refuse_foreign_observations(...)` call and its comment.
Keep the `declared` filter, and reword its comment to:

```python
        # The lineage snapshot walks from each observed dataset through this
        # mount's view, which resolves only its own datasets; evidence resting
        # outside the corpus is the kernel's input-outside-corpus refusal.
```

Delete the `_refuse_foreign_observations` method. Then
`grep -rn "_refuse_foreign_observations" python` must print nothing.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `just test-one tests/test_mount_citations.py tests/test_two_corpora.py tests/test_epoch_verb.py`
Expected: all pass.

Then run `just test-fast`. Any other failure in a world with two configured roots and
coordination on (`test_mounts.py`, `test_cmd_next_selection.py`, `test_mcp.py`) that now
refuses `no-epoch` is the spec's intended behaviour. That fixture publishes an epoch with
`publish_session_epoch(cfg)` after its last write, as `test_two_corpora`'s does. A
failure of any other shape stops the task: report it.

- [ ] **Step 6: Commit**

```bash
tasks check
git add python/src/science python/tests tasks/
git commit -m "feat(belief): a mounted session reads belief at the current epoch"
```

---

### Task 5: `next` scans the session and reports `assessed-unevaluated`

**Files:**
- Modify: `python/src/science/commands/next.py:13-55` (`CLASSES`, `_targeting_specs`,
  `classify`) and `:118-124` (row rendering).
- Modify: `python/tests/test_mount_citations.py`.

**Interfaces:**
- Consumes:
  - Task 1's `session_mounts`;
  - Task 4's `gather_inputs` (which raises an epoch `Refused` in world mode) and
    `epoch_refusal()`;
  - Task 3's `EPOCH_CODES`.
- Produces: `CLASSES = ("ready", "not-ready", "assessed-unevaluated",
  "assessed-not-admitted", "admitted")`. `classify` may return `"assessed-unevaluated"`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_mount_citations.py`:

```python
def test_a_write_root_spec_on_a_mounted_proposition_makes_it_ready(shared, certified_work):
    """Review round 1, P2 1: readiness reads specs in every session corpus.
    proposition:fresh is mounted with no evidence anywhere until the write root
    writes a spec on it."""
    from science.commands.next import classify
    cfg, mounted = shared
    assert classify(ReadContext.open(cfg), "proposition:fresh") == "not-ready"
    with open_rig(cfg, ("spec",)) as (d, _):
        d.invoke("spec", dict(SPEC_FIELDS, target="proposition:fresh", dataset=mounted["data"]))
    assert classify(ReadContext.open(cfg), "proposition:fresh") == "ready"


def test_next_marks_mounted_evidence_unevaluated_without_an_epoch_and_judges_it_with_one(
        shared, certified_work):
    from science.commands.next import classify, handle
    from science.world_belief import publish_session_epoch
    cfg, mounted = shared
    _walk(cfg, mounted, certified_work)
    assert classify(ReadContext.open(cfg), "proposition:shared") == "assessed-unevaluated"
    rows = handle(ReadContext.open(cfg), limit=None)[-1].pairs
    assert dict(rows)["proposition:shared"].startswith("assessed-unevaluated (no-epoch): ")
    publish_session_epoch(cfg)
    assert classify(ReadContext.open(cfg), "proposition:shared") == "assessed-not-admitted"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_mount_citations.py -k "ready or unevaluated"`
Expected: FAIL.
- The readiness test reads `not-ready` after the spec, because `_targeting_specs` reads
  only the mount.
- The `next` test raises `Refused` `no-epoch` out of `classify` instead of classifying.

- [ ] **Step 3: Implement**

In `next.py`:

```python
from science.world_belief import EPOCH_CODES

CLASSES = ("ready", "not-ready", "assessed-unevaluated", "assessed-not-admitted", "admitted")


def _targeting_specs(mounts, proposition):
    """Every session corpus's specs targeting `proposition`, each decoded under
    its holder's profile (consumer spec decision 9)."""
    return [spec for mount in mounts for node in mount.view.iter_stored() if node.kind == "analysis-spec"
            for spec in (stored.analysis_spec_value(node, profile=mount.profile),) if spec.target == proposition]


def _assessed(mounts, proposition) -> bool:
    return any(node.kind == "assessment"
               and stored.assessment_value(node, profile=mount.profile).proposition == proposition
               for mount in mounts for node in mount.view.iter_stored())
```

Replace `classify`:

```python
def classify(ctx, proposition: str) -> str:
    """The class rule over the evidence in every session corpus (consumer spec
    decision 9). Admission of a mounted session's evidence is judged at the
    current epoch; without one it is `assessed-unevaluated`."""
    ctx.mount_holding(proposition)  # refuses a proposition no mount holds, or two do
    mounts = ctx.session_mounts()
    if not _assessed(mounts, proposition):
        everywhere = ctx.mounts()
        return ("ready" if any(_inputs_held(ctx, everywhere, s) for s in _targeting_specs(mounts, proposition))
                else "not-ready")
    try:
        inputs = ctx.gather_inputs(proposition)
    except Refused as caught:
        if caught.refusal.code in EPOCH_CODES:
            return "assessed-unevaluated"
        raise
    observations = ctx.observations()
    for assessment in inputs.assessments:
        run = inputs.runs.get(assessment.run)
        if run is not None and isinstance(admit(assessment, run, observations, inputs.verifications), Admitted):
            return "admitted"
    return "assessed-not-admitted"
```

In `handle`, change the `propositions` rendering so an unevaluated row carries its
reason:

```python
    def label(c: int) -> str:
        refusal = ctx.epoch_refusal()
        return f"{CLASSES[c]} ({refusal.code})" if CLASSES[c] == "assessed-unevaluated" and refusal else CLASSES[c]

    blocks.append(KeyVals("propositions",
                          tuple((pid, f"{label(c)}: {statement}") for c, pid, statement in shown)
                          or (("none", "no propositions"),)))
```

`_inputs_held` keeps reading `ctx.mounts()`: a spec's dataset is one world record, in
whichever configured corpus declares it (part 3).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_mount_citations.py tests/test_cmd_next.py tests/test_cmd_next_selection.py tests/test_two_corpora.py tests/test_belief_path.py`
Expected: all pass. A test that sorts rows by the old class indices takes the new order,
which places `assessed-unevaluated` between `not-ready` and `assessed-not-admitted`.

- [ ] **Step 5: Commit**

```bash
just test-fast
tasks check
git add python/src/science python/tests tasks/
git commit -m "feat(next): scan every session corpus; assessed-unevaluated without a current epoch"
```

---

### Task 6: The `publishes` class reaches the permit

**Files:**
- Modify: `python/src/science/dispatch.py:182-191` (the `publishes` arm).
- Modify: `python/tests/test_dispatch.py:176-194` and
  `python/tests/test_synthetic_tree.py:21-36`.
- Modify: `python/tests/helpers/synthetic.py:53-67`. The `unreachable` docstring and its
  comment are no longer true.
- Modify: `docs/specs/2026-08-31-command-framework-design.md` §4.4 (the 2026-09-09
  amendment).

**Interfaces:**
- Produces: `Dispatcher._required` returns `RequiredCapabilities.publishes()` for a
  `publishes` class.

- [ ] **Step 1: Write the failing tests**

Replace `test_publishes_class_refuses_until_the_publish_family_exists` in
`test_dispatch.py`:

```python
def test_publishes_class_requires_the_publication_permit():
    """sci-498acb: the publish act family has landed, so the permit decides;
    no declaration-time refusal remains."""
    from beliefs.permit import RequiredCapabilities
    publish = make_decl("pub", write_class="publishes")
    dispatcher = Dispatcher((publish,), {"pub": lambda ctx, writer: ()},
                            read_context=StubContext(), session=object())
    assert dispatcher._required(publish) == RequiredCapabilities.publishes()
```

Replace `test_declaration_time_refusal_for_class_above_permit` in
`test_synthetic_tree.py`:

```python
def test_a_publishes_class_command_reaches_its_handler_under_an_attended_session(certified_work):
    """An attended session's ceiling is the full permit, which covers the
    publication requirement, so the handler runs (sci-498acb)."""
    from science.session import open_session
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from helpers.world import build_fixture_world
    decls = _fixture_tree()
    cfg = build_fixture_world(certified_work)
    session = open_session(cfg)
    executed = []
    d = Dispatcher(decls, {"pub-view": lambda ctx, writer: executed.append(True) or ()},
                   ReadContext.open(cfg), session=session)
    try:
        d.invoke("pub-view", {})
    finally:
        session.close()
    assert executed == [True]
```

In `helpers/synthetic.py`, `pub-view` now reaches its handler. Make its handler record
the call rather than raise. Replace the docstring sentence "no publish act family exists
yet, so it can never reach its handler" with "it reaches its handler under an attended
session, whose ceiling covers the publication permit". Replace the
`handlers["pub-view"] = unreachable` line with:

```python
    handlers["pub-view"] = lambda ctx, writer, **inputs: ()  # the permit decides (sci-498acb)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_dispatch.py tests/test_synthetic_tree.py`
Expected: FAIL with `Refused: permit-exceeded … sub-project 5`.

- [ ] **Step 3: Implement**

In `dispatch.py` `_required`:

```python
            case "publishes":
                return RequiredCapabilities.publishes()
```

In the framework design §4.4, append directly after the **Amended 2026-09-09**
paragraph:

```markdown
**Amended 2026-10-01 (`sci-498acb`).** The 2026-09-09 amendment above no longer
holds: `publish` is an act family, `RequiredCapabilities.publishes()` constructs, and a
`publishes`-class command's requirement is decided by the permit like every other
write class. The dispatcher's declaration-time refusal is removed
(`docs/specs/2026-10-01-mount-citations-consumer-design.md` decision 10).
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_dispatch.py tests/test_synthetic_tree.py tests/test_status.py`
Expected: all pass. `test_status.py:117` builds a `WriteClass("publishes")`; if it
asserted the old refusal, it takes the permit's answer.

- [ ] **Step 5: Commit, closing `sci-498acb`**

```bash
just test-fast
tasks done sci-498acb "publishes class calls RequiredCapabilities.publishes(); declaration-time refusal and its §4.4 amendment retired (sci-dc0381 Task 6)"
tasks check
git add python/src/science python/tests docs/specs/2026-08-31-command-framework-design.md tasks/
git commit -m "feat(dispatch): the publishes class reaches the permit"
```

---

### Task 7: Design amendments, closing the absorbed task

**Files:**
- Modify: `docs/specs/2026-09-24-coordination-command-set-design.md`: §5.5, after the
  last part 3 amendment (`grep -n "Amended 2026-09-30 (implementation, part 3)"`), and
  the refusal-code list near line 364.
- Modify: `docs/specs/2026-09-30-science-commons-design.md`, §11's "belief evaluating
  over a world read".

- [ ] **Step 1: Amend coordination §5.5**

Append after the last part 3 amendment paragraph in §5.5:

```markdown
**Amended 2026-10-01 (mount citations, `sci-dc0381`).** Beliefs cut 44 lets a session's
writes cite its read mounts, and both part 3 fences come down
(`docs/specs/2026-10-01-mount-citations-consumer-design.md`):

- `spec`, `run`, `assess` and `verify` resolve what they cite over the session's
  corpora, which are the write root plus every read mount when coordination is on.
  `dataset` still refuses bytes a mount declares, and `spec --supersedes` names a
  write-root spec only.
- Science's foreign-observation guard is removed. The kernel's corpus-local read
  refuses `input-outside-corpus` itself.
- Belief in a session with read mounts is a world read at the current epoch. It answers
  only when the epoch's coverage equals the session's corpora and none has drifted.
  Otherwise it refuses `no-epoch` or `epoch-stale`, and `science epoch` (an operator
  verb) publishes or reuses one.
- `next` scans every session corpus for specs and assessments. With read mounts and no
  current epoch, an assessed proposition is `assessed-unevaluated`, a fifth class
  between `not-ready` and `assessed-not-admitted`, carrying the refusal code.
```

In the refusal-code list (the bullets around `ambiguous-project`), add:

```markdown
- `no-epoch` — a mounted session's belief or admission read with no published epoch;
  the remedy is `science epoch`.
- `epoch-stale` — the current epoch's coverage differs from the session's corpora, or a
  session corpus moved since it; `data.missing`, `data.extra` and `data.drifted` name the
  corpora.
```

- [ ] **Step 2: Point commons §11 here**

After the sentence ending "since after adoption the assessment and the proposition it
assesses live in different corpora;", insert:

```markdown
(built by `docs/specs/2026-10-01-mount-citations-consumer-design.md`: an epoch-bound
world read, with `science epoch` as its operator verb)
```

- [ ] **Step 3: Verify the docs gate and close**

```bash
just check
tasks done sci-b1c777 "landed in sci-dc0381: both part 3 refusals lifted, cross-mount lineage read at the epoch, coordination §5.5 amended"
tasks check
git add docs tasks/
git commit -m "docs(specs): coordination and commons amendments for mount citations"
```

`sci-dc0381` closes after the whole-branch review, in the commit that records that
review's disposition.
