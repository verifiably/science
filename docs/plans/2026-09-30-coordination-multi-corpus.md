# Coordination command set, part 3: multi-corpus — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One configuration names a write root and several mounted corpora; the session writes only the write root, every mount is read under the profile its own manifest pins, and `next` and `belief` read across the mounts while the write commands read their own evidence in the write root.

**Architecture:** The configuration gains `write_root` and `read_contracts`. One function, `science.config.mount_profiles(config)`, maps every configured root to its profile: the write root to the writer's stated profile, every other root to `beliefs.mount.compile_mount_profile(root, available=contracts ∪ read_contracts)`. The launcher's session and the sessionless read context's resolver both take that mapping. `ReadContext.single_view()` is replaced by `write_view()` (write-root-only commands), `mounts()` and `mount_holding(ref)` (read-set-wide commands). Holdings observations and vocabulary lookups read every mount, since there is one store.

**Tech Stack:** Python 3.13, `beliefs` (editable path dependency), pytest with pytest-xdist and pytest-testmon, `just` recipes over `tools/tt`.

**Spec:** `docs/specs/2026-09-24-coordination-command-set-design.md` §5.5 (classification across mounted corpora and its two 2026-09-30 amendments), §6 (`write_root`, `read_contracts`, every mount under its own manifest's profile, and the part 3 planning amendment), §9 (the two-corpus check, the profile-selection row, and the part 3 amendment to the two-corpus row). Read it with this plan: the three "planning, part 3" amendments dated 2026-09-30 are reviewed with it.

**Kernel seams this plan calls** (on `beliefs` main since 2026-09-27, cut 43, `beliefs-fe7149`):

- `beliefs.mount.compile_mount_profile(root: Path, *, available: Iterable[DomainContract] = ()) -> ProfileSpec`. Activates exactly the manifest's pins, each resolved by content identity against the shipped packs and `available`. Raises `beliefs.errors.MountPinUnresolved` (a `ProfileError`, with `.root`, `.namespace`, `.pin`), and lets `ManifestMissing` / `ManifestMalformed` propagate.
- `beliefs.session.open_attended_session(world_config, operations_root, *, write_root: Path, profile: ProfileSpec, mounts: Mapping[Path, ProfileSpec] | None = None, store_root=None, project=None)`. `mounts`, when given, must key exactly `corpus_roots`, and `mounts[write_root]` must be compatible with `profile`; `mounts=None` opens without a resolver. The session writes only `write_root`.
- `beliefs.corpus.CoordinationResolver({root: profile, ...})` checks each mount's manifest pins against its profile (`ContractMismatch`), and resolves tips over the union of mounts.
- `beliefs.world.live.evaluate_live_query(world, query)` covers every **admitted** corpus; `LiveSelection.selected` holds world addresses (record ids), each at one corpus: the kernel refuses a duplicate location with `AddressMapConflict`.
- `DomainContract.namespace`, `DomainContract.content_identity`.

**Where to work.** `.worktrees/coordination-part3` (branch `coordination-part3`), created and locked. `tasks start <step id>` before each task. The steps, in order, each depending on the one before; their parent is `sci-923d3a`: `sci-e7e630` (Task 1), `sci-b7558d` (Task 2), `sci-e8b32e` (Task 3), `sci-5967fe` (Task 4), `sci-ca4d61` (Task 5).

## Global Constraints

- Tests run through the front door only, never bare `pytest`: `just test-one <path relative to python/>` for the test at hand, `just test-fast` before each commit, `just gate` before the branch merges.
- `tasks check` before every commit; each task's `tasks done <id> "<what landed>"` goes in that task's final commit. Conventional commits; no AI attribution lines.
- The writer's profile is stated, never inferred (spec §6): the write root is always mounted under `config.profile`, and nothing from `read_contracts` enters it. Availability never becomes activation.
- Write-root-only commands — `claim`, `dataset`, `spec`, `run`, `assess`, `verify` — read the refs they are given in the write root. Read-set-wide commands — `belief`, `next`, `status` — find a record in whichever mount holds it and decode it under that mount's profile.
- A ref no longer "is not in the corpus" without saying where it is: when a read mount holds it, the refusal names that mount's corpus id.
- No compatibility layer: `single_view()` is deleted in Task 4, not kept beside its replacements.
- No docs or comments name absolute host paths.

## Review Focus

- **A world that admits a corpus the configuration does not mount**, with a project selecting one of its records — a person expects `next` to refuse naming the address and `corpus_roots`, not a traceback and not a queue missing the row. Task 4 pins it.
- **The same record id held in two mounted corpora** (two corpora minting the same claim slug) — a person expects `belief` and `next` to refuse naming both corpora, never to answer from whichever mount sorted first. Task 4 pins it.
- **A write command given a record only a read mount holds** (`spec --target` an mm30 proposition) — a person expects a refusal saying the record lives in the read mount and this command reads the write root, not "is not in the corpus". Task 3 pins it for `spec`, and the shared `not_held` covers every write command.
- **A read mount whose manifest is missing or pins an unavailable contract** — a person expects a refusal naming the root and the pin at session open and at a sessionless read, never a bare `MountPinUnresolved` rendered as an internal error. Task 2 pins both.
- **Holding in the write root bytes a read mount already holds** (the milestone re-holds an mm30 input) — a person expects the `dataset` command to mint the record in the write root. Task 3 pins it; if the kernel's holdings write refuses the other corpus's standing observation, stop and record it as a kernel question rather than working around it.

---

### Task 1: The configuration's `write_root` and `read_contracts`

**Files:**
- Modify: `python/src/science/config.py` (`_OPTIONAL_KEYS`, `ScienceConfig`, `load_config`)
- Modify: `python/tests/helpers/world.py` (every `ScienceConfig(...)`; new `ARCHIVE` document helper)
- Modify: `python/tests/test_session_open.py:96`, `python/tests/test_status.py:47` (their `ScienceConfig(...)`)
- Test: `python/tests/test_config_mounts.py` (create)

**Interfaces:**
- Consumes: `science.contracts.load_contract_document(path, base) -> (DomainContract, OperatorPlan | None)`.
- Produces:
  - `ScienceConfig.write_root: Path` — a required field, placed after `coordination`; always one of `world.corpus_roots`.
  - `ScienceConfig.available_contracts: tuple[DomainContract, ...] = ()` — the parsed `contracts` documents followed by the parsed `read_contracts` documents.
  - `helpers.world.archive_contract_document(work: Path) -> Path` — writes `work/"archive.yaml"`.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_config_mounts.py`:

```python
"""Spec §6: `write_root` and `read_contracts` (coordination part 3)."""
import shutil
from pathlib import Path

import pytest

from helpers.world import DOMAINS, archive_contract_document, build_fixture_world_with_contract
from science.config import load_config
from science.refusal import Refused


def _config(work: Path, *, corpus_roots=("corpus",), extra: str = "") -> Path:
    """The contract world's launcher TOML, every path relative to the file."""
    cfg = build_fixture_world_with_contract(work)
    path = work / "science.toml"
    path.write_text(
        'world_root = "world"\n'
        f'world_id = "{cfg.world.world_id}"\n'
        f"corpus_roots = {list(corpus_roots)!r}\n"
        'operations_root = "ops"\n'
        f"domains = {list(DOMAINS)!r}\n"
        'contracts = ["testing.yaml"]\n'
        'store_root = "store"\n'
        "coordination = 2\n" + extra
    )
    return path


def _refused(path: Path) -> str:
    with pytest.raises(Refused) as caught:
        load_config(path)
    assert caught.value.refusal.code == "invalid-input"
    return caught.value.refusal.message


def test_one_root_is_the_write_root_without_the_key(certified_work):
    assert load_config(_config(certified_work)).write_root == (certified_work / "corpus").resolve()


def test_two_roots_need_a_write_root(certified_work):
    message = _refused(_config(certified_work, corpus_roots=("corpus", "archive")))
    assert "write_root" in message and "2 corpus_roots" in message


def test_a_write_root_outside_corpus_roots_refuses(certified_work):
    assert "not one of corpus_roots" in _refused(_config(certified_work, extra='write_root = "elsewhere"\n'))


def test_write_root_must_be_a_string(certified_work):
    assert "write_root must be a string" in _refused(_config(certified_work, extra="write_root = 3\n"))


def test_a_relative_write_root_resolves_against_the_file(certified_work, tmp_path, monkeypatch):
    path = _config(certified_work, corpus_roots=("corpus", "archive"), extra='write_root = "corpus"\n')
    monkeypatch.chdir(tmp_path)
    assert load_config(path).write_root == (certified_work / "corpus").resolve()


def test_read_contracts_are_available_and_never_activated(certified_work):
    path = _config(certified_work, extra='read_contracts = ["archive.yaml"]\n')
    archive_contract_document(certified_work)
    cfg = load_config(path)
    assert "archive" not in cfg.profile.activated_contracts
    assert [contract.namespace for contract in cfg.available_contracts] == ["testing", "archive"]
    assert [plan.namespace for plan in cfg.plans] == ["testing"]


def test_read_contracts_must_be_a_list_of_strings(certified_work):
    message = _refused(_config(certified_work, extra='read_contracts = "archive.yaml"\n'))
    assert "read_contracts must be a list of strings" in message


def test_a_document_in_both_lists_refuses(certified_work):
    message = _refused(_config(certified_work, extra='read_contracts = ["testing.yaml"]\n'))
    assert "both contracts and read_contracts" in message and "testing" in message


def test_one_document_under_two_paths_is_still_in_both_lists(certified_work):
    path = _config(certified_work, extra='read_contracts = ["copy.yaml"]\n')
    shutil.copy(certified_work / "testing.yaml", certified_work / "copy.yaml")
    assert "both contracts and read_contracts" in _refused(path)
```

Add to `python/tests/helpers/world.py`, directly after `fixture_contract_document`:

```python
def archive_contract_document(work: Path) -> Path:
    """A second corpus-local contract, `archive`: the test contract under
    another namespace, for a read mount the writer never activates (spec §9)."""
    path = work / "archive.yaml"
    path.write_text((TEST_CONTRACT % {"concepts": concept_list_address().removeprefix("dataset:"),
                                      "levels": level_list_address().removeprefix("dataset:")})
                    .replace("contract: testing", "contract: archive", 1))
    return path
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_config_mounts.py`
Expected: FAIL — `write_root` is an unknown key, and `ScienceConfig` has no `write_root` or `available_contracts`.

- [ ] **Step 3: Implement**

In `python/src/science/config.py`:

```python
from beliefs.contract.domain import DomainContract

_OPTIONAL_KEYS = ("service_socket", "default_project", "write_root", "read_contracts")


@dataclass(frozen=True)
class ScienceConfig:
    world: WorldConfig
    operations_root: Path
    profile: ProfileSpec
    service_socket: Path
    store_root: Path
    coordination: int | None
    # The one configured root the session writes (spec §6); the others are
    # read mounts.
    write_root: Path
    plans: tuple[OperatorPlan, ...] = ()
    # An unpinned beliefs.coordination.CoordinationAddress or None: the project a
    # launcher opens under and a CLI read falls back to with no live session.
    default_project: object = None
    # What a read mount's pins may resolve against: the `contracts` documents,
    # which the writer activates, then the `read_contracts` documents, which it
    # never does.
    available_contracts: tuple[DomainContract, ...] = ()
```

In `load_config`, beside the other type checks:

```python
    if "write_root" in raw and type(raw["write_root"]) is not str:
        _refuse("config write_root must be a string")
    read_contracts = raw.get("read_contracts", [])
    if type(read_contracts) is not list or any(type(value) is not str for value in read_contracts):
        _refuse("config read_contracts must be a list of strings")
```

After `local = [...]`:

```python
    readable = [load_contract_document(located(value), base) for value in read_contracts]
    activated = {contract.content_identity for contract, _ in local}
    both = sorted(contract.namespace for contract, _ in readable if contract.content_identity in activated)
    if both:
        _refuse(f"config lists {both} in both contracts and read_contracts; a document is "
                "activated for the writer or available to read mounts only")
```

`plans` stays built from `local` only. Before `return`, replace the inline `corpus_roots` tuple with:

```python
    corpus_roots = tuple(located(value) for value in raw["corpus_roots"])
    if "write_root" in raw:
        write_root = located(raw["write_root"])
        if write_root not in corpus_roots:
            _refuse(f"config write_root {write_root} is not one of corpus_roots")
    elif len(corpus_roots) == 1:
        (write_root,) = corpus_roots
    else:
        _refuse(f"config names {len(corpus_roots)} corpus_roots and no write_root; "
                "name the one the session writes")
```

and pass `corpus_roots=corpus_roots`, `write_root=write_root`, `available_contracts=tuple(contract for contract, _ in local + readable)` to the constructors.

Then give every direct `ScienceConfig(...)` construction its write root — `grep -rn "ScienceConfig(" python/tests` lists them: in `helpers/world.py`, `build_fixture_world` and `build_world_without_coordination` pass `write_root=corpus_root`, and `build_fixture_world_with_contract` passes `write_root=corpus_root, available_contracts=(contract,)`; `test_session_open.py:96` and `test_status.py:47` pass their first corpus root.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_config_mounts.py tests/test_config.py tests/test_cwd_independence.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
just test-fast && tasks check
git add python/src/science/config.py python/tests/helpers/world.py python/tests/test_config_mounts.py \
  python/tests/test_session_open.py python/tests/test_status.py tasks/
git commit -m "feat(config): write_root and read_contracts"
```

---

### Task 2: Every mount under its own manifest's profile

**Files:**
- Modify: `python/src/science/config.py` (`Mount`, `mount_profiles`, `require_coordination_pinned`, `ReadContext.mounts`, `ReadContext.coordination`)
- Modify: `python/src/science/session.py` (`open_session`)
- Modify: `python/tests/helpers/world.py` (`build_two_corpus_world`, `archive_config`)
- Test: `python/tests/test_mounts.py` (create)

**Interfaces:**
- Consumes: `ScienceConfig.write_root`, `.available_contracts` (Task 1); `compile_mount_profile`; `open_attended_session(write_root=, mounts=)`.
- Produces:
  - `science.config.Mount` — frozen dataclass `(corpus_id: str, root: Path, view: ReadView, profile: ProfileSpec)`.
  - `science.config.mount_profiles(config: ScienceConfig) -> dict[Path, ProfileSpec]` — refuses `invalid-input` naming the root (and the pin).
  - `ReadContext.mounts() -> tuple[Mount, ...]` — one per configured root, ordered by corpus id then root, each view opened at the call.
  - `helpers.world.build_two_corpus_world(work: Path) -> ScienceConfig` — the write root `work/"corpus"` (base, biology, `testing`, coordination 2; empty) and the read mount `work/"archive"` (base, biology, `archive`; no coordination), in one world and one store. The archive holds the concept and level vocabulary lists and `proposition:archived`, typed under `archive`'s `affects-concept-protein`. `read_contracts` supplies `archive`.
  - `helpers.world.archive_config(cfg: ScienceConfig) -> ScienceConfig` — the same world with the archive as write root under its own profile and plan, `coordination=None`: how a fixture writes the archive's evidence through the commands.

- [ ] **Step 1: Write the fixture and the failing tests**

Add to `python/tests/helpers/world.py`:

```python
def build_two_corpus_world(work: Path) -> ScienceConfig:
    """Spec §9's two corpora: the write root `corpus` (base, biology, the
    `testing` contract and coordination) and the read mount `archive` (base,
    biology and the corpus-local `archive` contract, no coordination — the mm30
    shape), in one world and one store. The archive holds the vocabulary lists
    and proposition:archived; `archive` reaches the mount through
    read_contracts alone."""
    from beliefs.claim import Referent, build_claim
    from beliefs.projection import project_claim
    from science.contracts import load_contract_document
    base = shipped_base_contract()
    testing, testing_plan = load_contract_document(fixture_contract_document(work), base)
    archive, archive_plan = load_contract_document(archive_contract_document(work), base)
    biology = [shipped_domain_contract(ns) for ns in DOMAINS]
    writer_profile = compile_profile(base, biology + [testing], coordination=shipped_coordination(COORDINATION))
    archive_profile = compile_profile(base, biology + [archive])
    archive_root, corpus_root = work / "archive", work / "corpus"
    config = WorldConfig(work / "world", secrets.token_hex(16), (archive_root, corpus_root))
    init_world_root(config, authority=FIXTURE_AUTHORITY)
    world = open_world(config, authority=FIXTURE_AUTHORITY)
    for root, profile in ((archive_root, archive_profile), (corpus_root, writer_profile)):
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
                        coordination=COORDINATION, write_root=corpus_root, plans=(testing_plan,),
                        available_contracts=(testing, archive))
    archived = archive_config(cfg)
    hold_fixture_dataset(archived, "concepts.txt", CONCEPTS, "concept vocabulary")
    hold_fixture_dataset(archived, "levels.txt", LEVELS, "level vocabulary")
    claim = build_claim(archive_profile, operator=archive_plan.operator_for("affects", "concept", "protein"),
                        args=(Referent(sort=archive_plan.sort_for("concept"), term="concept:disease-stage"),
                              Referent(sort=archive_plan.sort_for("protein"), term="protein:PHF19")),
                        layer="causal", polarity="positive")
    open_corpus(archive_root, authority=FIXTURE_AUTHORITY, profile=archive_profile).add(stored.proposition_node(
        "archived", title="archived", claim=project_claim(claim),
        display_statement="concept:disease-stage affects protein:PHF19 (archived)"))
    return cfg


def archive_config(cfg: ScienceConfig) -> ScienceConfig:
    """`cfg`'s world with the archive as the write root, under the profile its
    manifest pins and its own plan: the fixture's way to write the archive's
    evidence through the commands."""
    import dataclasses
    from beliefs.mount import compile_mount_profile
    from science.contracts import load_contract_document
    archive_root = cfg.world.world_root.parent / "archive"
    _, plan = load_contract_document(archive_root.parent / "archive.yaml", shipped_base_contract())
    return dataclasses.replace(cfg, write_root=archive_root, coordination=None, plans=(plan,),
                               profile=compile_mount_profile(archive_root, available=cfg.available_contracts))
```

and in `hold_fixture_dataset`, replace `(root,) = cfg.world.corpus_roots` with `root = cfg.write_root`.

Create `python/tests/test_mounts.py`:

```python
"""Spec §6: every mount under its own manifest's profile, in the session and
in the sessionless read context alike."""
import dataclasses

import pytest

from beliefs.corpus import ReadView
from beliefs.world import WorldConfig
from helpers.world import build_two_corpus_world, mint_project, open_rig
from science.config import ReadContext, mount_profiles
from science.coordination import resolve_project_ref
from science.refusal import Refused


@pytest.fixture
def two(certified_work):
    return build_two_corpus_world(certified_work)


def _refused(call) -> str:
    with pytest.raises(Refused) as caught:
        call()
    assert caught.value.refusal.code == "invalid-input"
    return caught.value.refusal.message


def test_the_write_root_is_mounted_under_the_writer_profile_and_the_archive_under_its_pins(two):
    mounts = {mount.root.name: mount for mount in ReadContext.open(two).mounts()}
    assert mounts["corpus"].profile is two.profile
    archive = mounts["archive"].profile.activated_contracts
    assert "archive" in archive and "testing" not in archive and "coordination" not in archive


def test_mounts_are_ordered_by_corpus_id(two):
    ids = [mount.corpus_id for mount in ReadContext.open(two).mounts()]
    assert ids == sorted(ids) and len(ids) == 2


def test_a_read_mount_pin_no_document_carries_refuses_naming_root_and_pin(two):
    bare = dataclasses.replace(two, available_contracts=two.available_contracts[:1])
    message = _refused(lambda: mount_profiles(bare))
    assert "archive" in message and "archive:" in message
    assert "archive" in _refused(lambda: ReadContext.open(bare).coordination())


def test_a_read_mount_without_a_manifest_refuses_naming_the_root(two):
    empty = two.world.world_root.parent / "empty"
    empty.mkdir()
    widened = dataclasses.replace(two, world=WorldConfig(
        two.world.world_root, two.world.world_id, two.world.corpus_roots + (empty,)))
    assert str(empty) in _refused(lambda: mount_profiles(widened))


def test_the_session_opens_over_both_roots_though_the_archive_pins_no_coordination(two):
    with open_rig(two, ("project",)) as (dispatcher, _):
        mint_project(dispatcher, "health")
    projects = lambda root: [n for n in ReadView.opened_at(root).iter_stored() if n.kind == "project"]
    assert len(projects(two.write_root)) == 1
    assert projects(two.world.world_root.parent / "archive") == []


def test_a_sessionless_read_resolves_over_both_mounts(two):
    with open_rig(two, ("project",)) as (dispatcher, _):
        address = mint_project(dispatcher, "health")
    assert resolve_project_ref(ReadContext.open(two), "health") == address
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_mounts.py`
Expected: FAIL — `mount_profiles` and `ReadContext.mounts` do not exist; `open_session` refuses two roots.

- [ ] **Step 3: Implement**

In `python/src/science/config.py`:

```python
from functools import cached_property


@dataclass(frozen=True)
class Mount:
    """One configured root as a read sees it: its corpus id, a view opened at
    the call, and the profile its records decode under."""
    corpus_id: str
    root: Path
    view: ReadView
    profile: ProfileSpec


def mount_profiles(config: ScienceConfig) -> dict[Path, ProfileSpec]:
    """Every configured root under the profile its own manifest pins (spec §6):
    the write root under the writer's stated profile, every other root compiled
    from its pins against the shipped packs and the available documents.
    Availability never becomes activation."""
    from beliefs.mount import compile_mount_profile

    profiles = {}
    for root in config.world.corpus_roots:
        if root == config.write_root:
            profiles[root] = config.profile
            continue
        try:
            profiles[root] = compile_mount_profile(root, available=config.available_contracts)
        except MountPinUnresolved as caught:
            _refuse(f"the read mount {root} pins {caught.pin}, which no shipped pack and no "
                    "document in contracts or read_contracts carries")
        except (ManifestMissing, ManifestMalformed) as caught:
            _refuse(f"the read mount {root} has no readable manifest: {caught}")
    return profiles
```

(`MountPinUnresolved` joins the `beliefs.errors` import.)

`require_coordination_pinned` checks the write root only — a read mount is mounted under whatever it pins:

```python
    namespace = shipped_coordination(config.coordination).namespace
    wanted = f"{namespace}:{config.profile.activated_contracts[namespace]}"
    root = config.write_root
    try:
        pinned = load_manifest(root).profile.domains.get(namespace)
    except (ManifestMissing, ManifestMalformed):
        return
    # the two refusals below are unchanged, naming `root`
```

In `ReadContext`:

```python
    @cached_property
    def _profiles(self) -> dict[Path, ProfileSpec]:
        # Compiled once per context; a dispatcher's per-invocation `replace`
        # builds a fresh context, so a command compiles once (kernel decision 9).
        return mount_profiles(self.config)

    def mounts(self) -> tuple[Mount, ...]:
        """One mount per configured root, ordered by corpus id then root, each
        view opened now: a view indexes its corpus as of its opening."""
        keyed = sorted((load_manifest(root).corpus_id, str(root), root) for root in self.config.world.corpus_roots)
        return tuple(Mount(corpus_id, root, ReadView.opened_at(root), self._profiles[root])
                     for corpus_id, _, root in keyed)

    def coordination(self):
        """A live resolver over every configured root, each under its own
        manifest's profile (coordination §6.2; spec §6)."""
        from beliefs.corpus import CoordinationResolver

        if self.config.coordination is None:
            raise Refused(Refusal("invalid-input",
                                  "coordination = false in this configuration; there is no resolver to ask"))
        require_coordination_pinned(self.config)
        return CoordinationResolver(self._profiles)
```

In `python/src/science/session.py`, drop the one-root refusal and open over the write root and every mount:

```python
def open_session(config: ScienceConfig, project=None):
    """Open the configured write root as the writer, with every configured root
    mounted under its own manifest's profile when coordination is on.
    ... (keep the `project` paragraph)"""
    from beliefs.errors import ProjectNotResolvable
    from beliefs.session import open_attended_session

    if config.coordination is not None:
        require_coordination_pinned(config)
    elif project is not None:
        raise Refused(Refusal(
            "invalid-input", "coordination = false in this configuration; no project can be selected"))
    try:
        return open_attended_session(
            config.world, config.operations_root, write_root=config.write_root, profile=config.profile,
            mounts=mount_profiles(config) if config.coordination is not None else None,
            store_root=config.store_root, project=project,
        )
    except ProjectNotResolvable as caught:
        ...  # unchanged
```

(`mount_profiles` joins the `science.config` import.) Update `ReadContext.coordination`'s old docstring and the `test_session_open.py` test that asserted the one-root `SessionRefused`, if any, to the kernel's refusal of a write root outside `corpus_roots`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_mounts.py tests/test_session_open.py tests/test_context.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
just test-fast && tasks check
git add python/src/science/config.py python/src/science/session.py python/tests/ tasks/
git commit -m "feat(config): mount every corpus under its own manifest's profile"
```

---

### Task 3: The write-root-only commands

**Files:**
- Modify: `python/src/science/config.py` (`ReadContext.write_view`, `not_held`, `observations`, `snapshot`, `held_path`, `is_held`, `pins`)
- Modify: `python/src/science/holdings.py` (every function takes the read views, not one view and corpus id)
- Modify: `python/src/science/vocabulary.py` (`snapshot`, `_dataset_at`)
- Modify: `python/src/science/commands/dataset.py`, `spec.py`, `run.py`, `assess.py`, `verify.py`
- Modify: `python/tests/helpers/world.py` (`unhold_fixture_dataset`, `mint_fixture_run`), and every test calling `single_view()` except `test_cmd_belief.py`/`test_cmd_next*.py`
- Test: `python/tests/test_write_root.py` (create)

**Interfaces:**
- Consumes: `ReadContext.mounts()`, `Mount` (Task 2); `build_two_corpus_world`, `archive_config` (Task 2).
- Produces:
  - `ReadContext.write_view() -> ReadView` — the write root's view, opened at the call.
  - `ReadContext.not_held(ref: str) -> NoReturn` — refuses `invalid-input`: `"{ref!r} is not in the corpus"`, plus `"; read mount <corpus id> holds it, and this command reads the write root"` when a read mount does.
  - `ReadContext.snapshot(profile: ProfileSpec | None = None)` — the writer's profile by default.
  - `ReadContext.pins(root: Path | None = None)` — the write root's pins by default.
  - `science.holdings`: `reduced_heads(world, corpus_ids: frozenset[str])`, `reduced_observations(views, world)`, `found_observations(views, world)`, `held_path(views, world, store_root, store_id, address)`, `is_held(views, world, node)`, where `views` is `ReadContext.read_views()`'s `((corpus_id, ReadView), ...)`.
  - `science.vocabulary.snapshot(profile, views, store_root, store_id, observations)`.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_write_root.py`:

```python
"""Spec §5.5 (part 3 amendment): the write commands read the write root, and
share the one store's holdings and vocabularies with every mount."""
import pytest

from beliefs.corpus import ReadView
from helpers.world import OBSERVED, SPEC_FIELDS, archive_config, build_two_corpus_world, hold_fixture_dataset, open_rig
from science.config import ReadContext
from science.refusal import Refused

CLAIM = {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
         "layer": "causal", "polarity": "positive", "slug": "claimed"}


@pytest.fixture
def two(certified_work):
    return build_two_corpus_world(certified_work)


def test_claim_types_through_a_vocabulary_held_in_the_read_mount(two):
    with open_rig(two, ("claim",)) as (d, ctx):
        d.invoke("claim", CLAIM)
        assert ctx.write_view().holds("proposition:claimed")
    assert not ReadView.opened_at(two.world.world_root.parent / "archive").holds("proposition:claimed")


def test_a_spec_in_the_write_root_reads_its_dataset_there(two):
    data = hold_fixture_dataset(two, "data.txt", b"y\n", "expression", **OBSERVED)
    with open_rig(two, ("claim", "spec")) as (d, ctx):
        d.invoke("claim", CLAIM)
        out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:claimed", dataset=data))
        assert "analysis-spec:" in out.text


def test_a_write_command_given_a_read_mount_record_names_the_mount(two):
    data = hold_fixture_dataset(two, "data.txt", b"y\n", "expression", **OBSERVED)
    archive_id = next(m.corpus_id for m in ReadContext.open(two).mounts() if m.root.name == "archive")
    with open_rig(two, ("spec",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("spec", dict(SPEC_FIELDS, target="proposition:archived", dataset=data))
    assert caught.value.refusal.code == "invalid-input"
    assert archive_id in caught.value.refusal.message and "write root" in caught.value.refusal.message


def test_bytes_a_read_mount_holds_can_be_held_again_in_the_write_root(two, certified_work):
    hold_fixture_dataset(archive_config(two), "data.txt", b"z\n", "expression", **OBSERVED)
    source = certified_work / "data.txt"
    source.write_bytes(b"z\n")
    with open_rig(two, ("dataset",)) as (d, ctx):
        out = d.invoke("dataset", {"path": str(source), "title": "expression again"})
        ref = out.text.split("\n", 1)[0].split()[-1]  # adjust to the record block's id line
        assert ctx.write_view().holds(ref)
```

(Read the `dataset` record block's rendering in an existing `test_cmd_dataset.py` test and extract the ref the same way.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_write_root.py`
Expected: FAIL — `write_view` does not exist; `single_view()` refuses two roots.

- [ ] **Step 3: Implement the read context and the store reads**

`python/src/science/holdings.py` — one store, every mount:

```python
def reduced_heads(world, corpus_ids: frozenset[str]):
    """(active, blocked) from the world's held reducer over these corpora.
    ... (keep the detached-inspection paragraph)"""
    seam = log_seam()
    active, blocked, _ = derive_holdings(
        world, corpus_ids, binding_for(holdings_rule_bundle()),
        chain_view=seam.inspect_detached, state_facts=seam.state_facts,
    )
    return active, blocked


def reduced_observations(views, world) -> dict[str, DatasetAnswer | DatasetBlocked]:
    """The reduction's answer for every dataset record any mount holds: one
    store, whichever corpus declared the dataset."""
    active, blocked = reduced_heads(world, frozenset(corpus_id for corpus_id, _ in views))
    answers: dict[str, DatasetAnswer | DatasetBlocked] = {}
    for _, view in views:
        for node in view.iter_stored():
            if node.kind != "dataset":
                continue
            declaration = stored.dataset_declaration(node)
            address = dataset_address(declaration)
            if address is not None:
                answers[address] = dataset_observations(declaration, active, blocked)
    return answers
```

`found_observations(views, world)`, `held_path(views, world, store_root, store_id, address)` and `is_held(views, world, node)` take `views` in place of `view, world, corpus_id` and pass it through; their bodies are otherwise unchanged.

`python/src/science/vocabulary.py`: `snapshot(profile, views, store_root, store_id, observations)` and `_dataset_at(views, address)` scan every view:

```python
def _dataset_at(views, address: str):
    for _, view in views:
        for node in view.iter_stored():
            if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) == address:
                return node
    return None
```

`ReadContext` in `python/src/science/config.py`:

```python
    def write_view(self) -> ReadView:
        """The write root's view, opened now: what a write command reads the
        records it is given in (spec §5.5, part 3)."""
        return ReadView.opened_at(self.config.write_root)

    def not_held(self, ref: str) -> NoReturn:
        """Refuse a ref the write root does not hold, naming the read mount that
        does: a person who passed an mm30 record learns where it is."""
        elsewhere = [load_manifest(root).corpus_id for root in self.config.world.corpus_roots
                     if root != self.config.write_root and ReadView.opened_at(root).holds(ref)]
        where = (f"; read mount {', '.join(elsewhere)} holds it, and this command reads the write root"
                 if elsewhere else "")
        raise Refused(Refusal("invalid-input", f"{ref!r} is not in the corpus{where}"))

    def snapshot(self, profile: ProfileSpec | None = None):
        from science.vocabulary import snapshot
        return snapshot(self.config.profile if profile is None else profile, self.read_views(),
                        self.config.store_root, self.store_id(), self.observations())

    def observations(self):
        from science.holdings import found_observations
        return found_observations(self.read_views(), self.world)

    def held_path(self, address: str) -> Path:
        from science.holdings import held_path
        return held_path(self.read_views(), self.world, self.config.store_root, self.store_id(), address)

    def is_held(self, node) -> bool:
        from science.holdings import is_held
        return is_held(self.read_views(), self.world, node)

    def pins(self, root: Path | None = None):
        return load_manifest(self.config.write_root if root is None else root).profile
```

(`NoReturn` from `typing`.) `single_view()` stays until Task 4; `_context`, `gather_inputs` and `evaluate` keep calling it.

- [ ] **Step 4: Convert the write commands**

Each of these replaces `_, view = ctx.single_view()` with `view = ctx.write_view()`, and each "is not in the corpus" refusal of a given ref with `ctx.not_held(ref)`:

- `commands/dataset.py` — the view only (it is given a path, not a ref). Its `standing` observations stay the write root's: the holdings write is the write root's act.
- `commands/spec.py` — `for ref in (target, dataset): if not view.holds(ref): ctx.not_held(ref)`; `supersedes` likewise.
- `commands/run.py` — `prepare`'s `spec_ref` and `dataset_ref`; `handle`'s view after the run.
- `commands/assess.py` — `run`. The "names no analysis-spec this corpus holds" refusal stays as it is: the run is in the write root, so its spec must be too.
- `commands/verify.py` — `assessment`; the view after the replay. `ctx.pins()` is already the write root's.

`commands/claim.py` needs no change: `ctx.snapshot()` now finds the vocabulary in any mount.

In `python/tests/helpers/world.py`: `unhold_fixture_dataset` uses `root = cfg.write_root` and `view = ReadContext.open(cfg).write_view()`; `mint_fixture_run` uses `view = ctx.write_view()` and `root = cfg.write_root`. In the tests, `grep -rln "single_view()" python/tests` lists the callers; outside `test_cmd_belief.py` and `test_cmd_next*.py`, replace `_, view = ctx.single_view()` with `view = ctx.write_view()` (the same mechanical rewrite in each). Any test asserting the old `holdings`/`vocabulary` signatures moves to the new ones.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `just test-one tests/test_write_root.py tests/test_cmd_dataset.py tests/test_cmd_spec.py tests/test_cmd_run.py tests/test_cmd_assess.py tests/test_cmd_verify.py tests/test_cmd_claim.py tests/test_belief_path.py`
Expected: PASS. If `test_bytes_a_read_mount_holds_can_be_held_again_in_the_write_root` fails inside the kernel's holdings write (a refusal about the location's standing observation), stop: note the error on the task and park it `--reason decision`; it is a kernel question for the milestone, not something to route around here.

- [ ] **Step 6: Commit**

```bash
just test-fast && tasks check
git add python/src/science/ python/tests/ tasks/
git commit -m "feat(commands): write commands read the write root; one store across mounts"
```

---

### Task 4: `belief` and `next` across the mounts, and the two-corpus check

**Files:**
- Modify: `python/src/science/config.py` (`ReadContext.mount_holding`, `_context`, `gather_inputs`, `evaluate`; delete `single_view`)
- Modify: `python/src/science/commands/belief.py`, `python/src/science/commands/next.py`
- Modify: `python/tests/helpers/world.py` (`add_archived_assessment`, `write_two_corpus_config`)
- Modify: `python/tests/test_cmd_belief.py`, `python/tests/test_cmd_next.py`, `python/tests/test_cmd_next_selection.py` (any `single_view()` call becomes `write_view()`; the unheld-record `RuntimeError` test becomes the Task 4 refusal)
- Test: `python/tests/test_two_corpora.py` (create)

**Interfaces:**
- Consumes: everything above; `science.coordination.live_selection`, `selected_project`.
- Produces:
  - `ReadContext.mount_holding(ref: str) -> Mount` — the one mount holding `ref`; refuses `invalid-input` `"{ref!r} is not in the configured corpora"` when none does, and naming both corpus ids when two do.
  - `ReadContext.gather_inputs(proposition)`, `ReadContext.evaluate(proposition)` — under the holding mount's view, corpus id, pins and profile.
  - `science.commands.next.classify(ctx, proposition) -> str` — signature unchanged; reads the holding mount.
  - `helpers.world.add_archived_assessment(cfg, work) -> str` — the archive's spec, run and assessment of `proposition:archived`, returning the assessment ref.
  - `helpers.world.write_two_corpus_config(cfg) -> Path` — the launcher TOML with `write_root` and `read_contracts`.

- [ ] **Step 1: Write the fixtures and the failing tests**

Add to `python/tests/helpers/world.py`:

```python
def add_archived_assessment(cfg: ScienceConfig, work: Path) -> str:
    """The archive's evidence for proposition:archived — a spec over held data,
    one run and its assessment, no verification — written through the commands
    with the archive as write root. `next` then reads it assessed-not-admitted."""
    archived = archive_config(cfg)
    data = hold_fixture_dataset(archived, "data.txt", b"x\n", "expression", **OBSERVED)
    with open_rig(archived, ("spec",)) as (d, _):
        out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:archived", dataset=data))
    spec = _minted_ref(out.text, "analysis-spec")
    run = mint_fixture_run(archived, spec, data, fixture_bundle(work))
    with open_rig(archived, ("assess",)) as (d, _):
        return _minted_ref(d.invoke("assess", {"run": run}).text, "assessment")


def write_two_corpus_config(cfg: ScienceConfig) -> Path:
    """The launcher TOML for `build_two_corpus_world`: both roots, the write
    root, `testing` activated and `archive` available to the read mount only."""
    work = cfg.world.world_root.parent
    path = work / "science.toml"
    path.write_text(f'''\
world_root = "world"
world_id = "{cfg.world.world_id}"
corpus_roots = ["archive", "corpus"]
write_root = "corpus"
operations_root = "ops"
domains = {list(DOMAINS)!r}
contracts = ["testing.yaml"]
read_contracts = ["archive.yaml"]
store_root = "store"
coordination = {COORDINATION}
''')
    return path
```

`_minted_ref(text, kind)` extracts the minted record's id from a record block; if the existing tests already have such a helper (`grep -rn "analysis-spec:" python/tests/test_cmd_assess.py`), reuse it and move it into `helpers/world.py` instead of writing a second one.

Create `python/tests/test_two_corpora.py`:

```python
"""Spec §9, the two-corpus check: each proposition's evidence in its own
corpus, each corpus decoded under its own manifest's profile."""
import dataclasses
import json
import re

import pytest

from beliefs.errors import ContractMismatch
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination, shipped_domain_contract
from beliefs.world import WorldConfig
from helpers.world import (
    COORDINATION, DOMAINS, OBSERVED, SPEC_FIELDS, FIXTURE_AUTHORITY, add_archived_assessment,
    build_two_corpus_world, hold_fixture_dataset, open_rig, write_two_corpus_config,
)
from science.commands.next import handle
from science.config import ReadContext
from science.refusal import Refused
from science.session import open_session

NAMES = ("claim", "spec", "project", "project-select", "next", "belief")
VERSION = "science.view-query.v1"
CLAIM = {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
         "layer": "causal", "polarity": "positive", "slug": "claimed"}


def _query(clause):
    return json.dumps({"version": VERSION, "clauses": [{"all": [clause]}]})


def _rows(text):
    return text.split("propositions:\n", 1)[1]


@pytest.fixture
def world(certified_work):
    """The archive's proposition assessed; the write root's claimed and ready."""
    cfg = build_two_corpus_world(certified_work)
    add_archived_assessment(cfg, certified_work)
    data = hold_fixture_dataset(cfg, "data.txt", b"y\n", "expression", **OBSERVED)
    with open_rig(cfg, ("claim", "spec")) as (d, _):
        d.invoke("claim", CLAIM)
        d.invoke("spec", dict(SPEC_FIELDS, target="proposition:claimed", dataset=data))
    return cfg


def test_next_under_a_project_selecting_both_classifies_each_from_its_own_corpus(world):
    """The mutation that enumerates the write root only drops the archived row;
    the mutation that decodes the read mount under the writer's profile fails
    on the corpus-local `archive` operator."""
    with open_rig(world, NAMES) as (d, _):
        d.invoke("project", {"name": "both",
                             "query": _query({"addresses": ["proposition:archived", "proposition:claimed"]})})
        d.invoke("project-select", {"target": "both"})
        text = d.invoke("next", {}).text
    assert _rows(text) == (
        "  proposition:claimed: ready: concept:disease-stage affects protein:PHF19\n"
        "  proposition:archived: assessed-not-admitted: concept:disease-stage affects protein:PHF19 (archived)\n"
    )


def test_the_unselected_session_reads_both_corpora_as_a_project_of_every_kind_does(world):
    """P5 across two corpora."""
    with open_rig(world, NAMES) as (d, _):
        unselected = _rows(d.invoke("next", {}).text)
        d.invoke("project", {"name": "all", "query": _query({"kinds": ["proposition"]})})
        d.invoke("project-select", {"target": "all"})
        selected = _rows(d.invoke("next", {}).text)
    assert unselected == selected and "proposition:archived" in unselected


def test_belief_answers_for_a_read_mount_proposition_whatever_is_selected(world):
    ctx = ReadContext.open(world)
    from science.commands.belief import handle as belief
    report = belief(ctx, proposition="proposition:archived")
    assert report[0].text == "Belief: proposition:archived"


def test_a_sessionless_cli_read_mounts_both_corpora_each_under_its_own_profile(world, capsys):
    from science.cli import main
    assert main(["next", "--config", str(write_two_corpus_config(world))]) == 0
    out = capsys.readouterr().out
    assert "proposition:archived: assessed-not-admitted" in out and "proposition:claimed: ready" in out


def test_activating_read_contracts_in_the_writer_is_refused_by_the_write_root_pins(world):
    from science.contracts import load_contract_document
    base = shipped_base_contract()
    loaded = [load_contract_document(world.world.world_root.parent / name, base)[0]
              for name in ("testing.yaml", "archive.yaml")]
    widened = compile_profile(base, [shipped_domain_contract(ns) for ns in DOMAINS] + loaded,
                              coordination=shipped_coordination(COORDINATION))
    with pytest.raises(ContractMismatch):
        open_session(dataclasses.replace(world, profile=widened))


def test_a_selected_record_no_configured_corpus_holds_refuses_naming_it(world):
    """The world admits the archive; a configuration mounting only the write
    root cannot read the row, and says so."""
    with open_rig(world, ("project",)) as (d, _):
        d.invoke("project", {"name": "archived", "query": _query({"addresses": ["proposition:archived"]})})
    narrowed = dataclasses.replace(world, world=WorldConfig(
        world.world.world_root, world.world.world_id, (world.write_root,)))
    with open_rig(narrowed, NAMES) as (d, _):
        d.invoke("project-select", {"target": "archived"})
        with pytest.raises(Refused) as caught:
            d.invoke("next", {})
    assert caught.value.refusal.code == "invalid-input"
    assert "proposition:archived" in caught.value.refusal.message
    assert "corpus_roots" in caught.value.refusal.message


def test_one_id_in_two_corpora_refuses_naming_both(world):
    from beliefs import stored
    from beliefs.root import open_corpus
    from helpers.world import archive_config
    node = stored.proposition_node("twice", title="twice", claim={"operator": "affects"})
    for cfg in (world, archive_config(world)):
        open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(node)
    ctx = ReadContext.open(world)
    ids = [mount.corpus_id for mount in ctx.mounts()]
    for call in (lambda: ctx.mount_holding("proposition:twice"), lambda: handle(ctx, limit=None)):
        with pytest.raises(Refused) as caught:
            call()
        assert caught.value.refusal.code == "invalid-input"
        assert all(corpus_id in caught.value.refusal.message for corpus_id in ids)
```

(`Heading.text` is the heading's text. The row order in the first test is class order then id — `ready` before `assessed-not-admitted` — as `CLASSES` sorts it.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_two_corpora.py`
Expected: FAIL — `single_view()` refuses two roots in `next`, `belief` and `classify`; `mount_holding` does not exist.

- [ ] **Step 3: Implement the read context**

In `ReadContext`, delete `single_view` and add:

```python
    def mount_holding(self, ref: str) -> Mount:
        """The one mounted corpus holding `ref`. A record id in two corpora is
        the world's duplicate-location conflict, refused rather than answered
        from whichever mount sorts first."""
        holders = [mount for mount in self.mounts() if mount.view.holds(ref)]
        if not holders:
            raise Refused(Refusal("invalid-input", f"{ref!r} is not in the configured corpora"))
        if len(holders) > 1:
            raise Refused(Refusal("invalid-input",
                                  f"{ref!r} is held by corpora {', '.join(m.corpus_id for m in holders)}; "
                                  "one address in two corpora is a duplicate location, which `status` reports"))
        return holders[0]

    def _context(self, mount: Mount, observations):
        from science.closure import supplied_context
        from beliefs import stored
        # Keyed as `gather` reads it: the stored assessment's identity, attributed
        # to the one corpus that holds it.
        node_corpus = {
            stored.assessment_value(node, profile=mount.profile).identity(): (mount.corpus_id,)
            for node in mount.view.iter_stored() if node.kind == "assessment"
        }
        return supplied_context(mount.view, corpus_id=mount.corpus_id, pins=self.pins(mount.root),
                                epoch_identity=self.epoch_identity(), observations=observations,
                                node_corpus=node_corpus)

    def gather_inputs(self, proposition: str):
        from science.closure import gather_inputs
        mount = self.mount_holding(proposition)
        observations = self.observations()
        return gather_inputs(mount.view, proposition, context=self._context(mount, observations),
                             profile=mount.profile, resolution=self.snapshot(mount.profile))

    def evaluate(self, proposition: str):
        from science.closure import evaluate
        mount = self.mount_holding(proposition)
        observations = self.observations()
        return evaluate(mount.view, proposition, observations=observations,
                        context=self._context(mount, observations),
                        profile=mount.profile, resolution=self.snapshot(mount.profile))
```

- [ ] **Step 4: Convert `belief` and `next`**

`commands/belief.py`:

```python
def handle(ctx, *, proposition) -> Report:
    ctx.mount_holding(proposition)  # refuses a proposition no mount holds, or two do
    answer = ctx.evaluate(proposition)
    ...  # unchanged
```

`commands/next.py` — `classify` reads the proposition's own corpus under its own profile, and finds a spec input's dataset in whichever mount holds it:

```python
def _dataset_node(mounts, address):
    return next((node for mount in mounts for node in mount.view.iter_stored() if node.kind == "dataset"
                 and dataset_address(stored.dataset_declaration(node)) == address), None)


def _inputs_held(ctx, mounts, spec) -> bool:
    observations = ctx.observations()
    for role in spec.input_roles:
        node = _dataset_node(mounts, role.dataset)
        if node is None:
            return False
        if not isinstance(admission_state(stored.dataset_declaration(node), observations.get(role.dataset, ())), Held):
            return False
    return True


def classify(ctx, proposition: str) -> str:
    """The four-class rule over the evidence in the proposition's own corpus,
    decoded under that corpus's profile (spec §5.5)."""
    mount = ctx.mount_holding(proposition)
    view, profile = mount.view, mount.profile
    assessed = any(n.kind == "assessment" and stored.assessment_value(n, profile=profile).proposition == proposition
                   for n in view.iter_stored())
    if not assessed:
        mounts = ctx.mounts()
        return ("ready" if any(_inputs_held(ctx, mounts, s) for s in _targeting_specs(view, proposition, profile))
                else "not-ready")
    ...  # the admitted / assessed-not-admitted arm, unchanged
```

and `handle`:

```python
    if project is None:
        nodes = [node for mount in ctx.mounts() for node in mount.view.iter_stored() if node.kind == "proposition"]
    else:
        live = live_selection(ctx, project)
        # Opened after the capture, never before it: a read view indexes the
        # corpus as it stood when it was opened, so an earlier one would not hold
        # a proposition minted in between, and its row would vanish under
        # `complete: true`.
        mounts = ctx.mounts()
        unmounted = [ref for ref in live.selected if not any(m.view.holds(ref) for m in mounts)]
        if unmounted:
            # The capture reads every admitted corpus; the configuration mounts
            # only corpus_roots. A row it cannot read is refused, never dropped.
            raise Refused(Refusal("invalid-input",
                                  f"the selection names {', '.join(unmounted)}, which no corpus in "
                                  "corpus_roots holds; the world admits a corpus this configuration does not mount"))
        blocks.append(KeyVals("selection", _selection_pairs(ctx.selection, project, live)))
        # A selected record that is not a proposition is not a row.
        nodes = [node for node in (next(m.view.get(ref) for m in mounts if m.view.holds(ref))
                                   for ref in live.selected) if node.kind == "proposition"]
```

(`Refused`, `Refusal` from `science.refusal`.) A duplicate id in the unselected arm reaches `classify`'s `mount_holding`, which refuses it.

Replace any remaining `single_view()` in `test_cmd_belief.py`, `test_cmd_next.py` and `test_cmd_next_selection.py` with `write_view()`. The old test pinning the unheld-record `RuntimeError` (grep `RuntimeError` in `test_cmd_next_selection.py`) now expects the `invalid-input` refusal above; if it built its state by admitting a corpus the configuration does not mount, only its expectation changes. `grep -rn "single_view" python/` must print nothing.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `just test-one tests/test_two_corpora.py tests/test_cmd_next.py tests/test_cmd_next_selection.py tests/test_cmd_belief.py tests/test_belief_path.py`
Expected: PASS.

- [ ] **Step 6: Check the mutations bite**

Make each mutation in turn, run `just test-one tests/test_two_corpora.py`, confirm the named test fails, and revert:

1. In `next.handle`'s unselected arm, enumerate `(m for m in ctx.mounts() if m.root == ctx.config.write_root)` → `test_the_unselected_session_reads_both_corpora…` fails; in the selected arm the unmounted refusal fires on `proposition:archived`.
2. In `mount_profiles`, return `config.profile` for every root → the session refuses at open with `ContractMismatch` on the archive mount (every test in the module fails at the fixture's first `open_rig`), and `ReadContext.mounts` decodes the archive's assessment under the wrong profile.
3. In `load_config`, compile `readable` documents into `profile` → covered by `test_activating_read_contracts_in_the_writer_is_refused_by_the_write_root_pins`, which builds that profile directly.

Record the three outcomes in one task note.

- [ ] **Step 7: Commit**

```bash
just test-fast && tasks check
git add python/src/science/ python/tests/ tasks/
git commit -m "feat(commands): belief and next read across mounted corpora"
```

---

### Task 5: The dated amendments and the close-out

**Files:**
- Modify: `docs/specs/2026-08-31-command-framework-design.md` (§9.1)
- Modify: `docs/specs/2026-09-24-coordination-command-set-design.md` (status line)
- Modify: `docs/specs/2026-09-09-belief-path-commands-design.md` (§4.8, if it still says `next` reads one corpus)

- [ ] **Step 1: Amend the framework design**

Append to framework §9.1 a dated paragraph:

```markdown
**Amended 2026-09-30 (coordination part 3):** two optional keys. `write_root` names the
one entry of `corpus_roots` the session writes — required when there is more than one,
defaulting to the sole root otherwise, resolved against the file. `read_contracts` lists
corpus-local contract documents a read mount's pins may resolve against and the writer
never activates; a document in both lists refuses. Every other root is mounted under the
profile its own manifest pins (coordination command set §6).
```

- [ ] **Step 2: Mark the spec implemented**

In the coordination spec's status line, replace "Part 3 (multi-corpus, `sci-923d3a`) planned 2026-09-30, plan …" with "part 3 (multi-corpus) implemented 2026-09-30, plan `docs/plans/2026-09-30-coordination-multi-corpus.md`." Check belief-path §4.8: if it says `next` reads one corpus, add a dated line pointing at coordination §5.5's part 3 amendment.

- [ ] **Step 3: Verify and close**

```bash
just gate
tasks note sci-0d00d2 "criterion 4's dependency sci-923d3a landed: write_root, read_contracts, per-mount profiles, next and belief across mounts"
tasks done <step id> "framework §9.1 and spec status amended"
tasks done sci-923d3a "write_root and read_contracts; every mount under its own manifest's profile in session and sessionless reads; write commands read the write root; belief and next across mounts; the two-corpus check"
tasks check
git add docs/ tasks/
git commit -m "docs: coordination part 3 amendments and close-out"
```

Expected: `just gate` passes. The branch then goes to the final whole-branch review before merging.
