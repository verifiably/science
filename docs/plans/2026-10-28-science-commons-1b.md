# Science commons milestone 1b Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Milestone 1b of the science commons: *A* adopts *B*'s publication, which carries
*A*'s own records, and both installations read each shared record once; *A* publishes an
update that drops one record, *B* adopts it, and the predecessor *B* still depends on stays
mounted with `show` saying why; retirement of an unrequired predecessor reaches the kernel's
`World.retire` through the `sharing` write class once the kernel's door exists.

**Architecture:** Science adopts cut 48's one equality contract (`content_identity`)
everywhere it compares two copies of a record: `adopt`'s admission checklist, the session's
holder resolution, and the accept policy's Carried branch. Two new modules carry what the
commons design left to the surface: `supersession.py` (address groups, named ancestry, the
ledger fold that names the current publication, missing links) and `retention.py` (why a
superseded publication stays mounted: `keep`, chain retention, attribution, the dependency
walk). `adopt` runs reconcile → candidate → re-evaluation, and `show` reports supersession
and retention. The milestone lands in two merges: Tasks 1–12 (the overlap half) need no
kernel change; Tasks 13–15 (the retirement tail) wait on `beliefs-a989fb`.

**Tech Stack:** Python 3 stdlib, the `beliefs` kernel at or after `316c202` (editable path
dependency), pytest with the certified-world fixtures and `helpers.snapshot`.

**Spec:** `docs/specs/2026-10-28-science-commons-1b-design.md` (accepted at revision 8,
`99eabaa`), over `docs/specs/2026-09-30-science-commons-design.md` §3, §4.7, §4.8, §9, §10,
§12 and the kernel's `beliefs/docs/superpowers/specs/2026-10-28-overlapping-publications-design.md`
§4.1, §4.2, §5.4, §6, §7, §8. Section numbers below (§5.1 …) are the 1b design's unless
prefixed `commons` or `kernel`.

**Review history:** revision 1 (`cad8b3b`) reviewed by a fresh `claude-code` reviewer
(round 1, revise: 2 Critical, 8 Important, 10 Minor): `keep` must load for an unpinned id
(§5.7 rule 1), a sibling publication needs a fork of the publisher, the clock seam is the
writer's, the guard tests need `reopened`, the dependency walk needs every holder's view
and profile, `config-stale` needs the file's path, reconcile looks at `mounted` pins only,
the checklist candidates need construction routes, the group key comes from the marker's
`destination`, and the late-chain state precedes the late-link one. Revision 2 (`e54ca13`)
answered all; a scoped re-review of its delta (round 2, revise: 1 Critical, 3 Important, 6
Minor) found that the `sharing` report contract admits pin blocks only, so `adopt`'s
retention rows and findings need the contract extended (Task 8, Task 12); that the
two-sessions test needs an unadopted late chain and the late-link fixture a reopen and an
epoch (Task 11); and that the `uid-corruption` builder needed its value shape, the
kernel-minted source, the `LOC_C` binding and basis-changing identifiers (Task 8).
Revision 3 (`2de2c94`) answered them, with the minors (the `apply_line` site, the sibling's
re-applied query, the epoch before each late-chain publish, `dataset_at`'s predicate, the
stale check's path, two snapshot callables per base-parametrised builder). Round 3
(`codex/gpt-6-astra`, revise: P1 1, P2 3, P3 1): divergence is any intersecting pair of
tips, not every pair (Task 6); the report contract must survive pagination and omit no
committed pin, so the dispatcher composes the pin prefix and stores the handler's tail in
the invocation outcome (Task 8); an already-mounted retry counts the whole invocation's
writes (Task 8); two commit commands named their files (Tasks 6, 11). Revision 4
(`92c9062`) answered them. Round 4 (`codex/gpt-6-astra`, revise: P1 1, P2 2): the
kernel's close outcome admits exactly one key, so the tail cannot ride in it; the handler
conversion missed `provider-bind` and the synthetic test handlers; existing invocations
have no tail. Revision 5 answers them: the tail is persisted by science under
`operations_root/tails/`, absent meaning empty, every sharing handler converts, and the
audit-failure and 1a-shaped-ledger paths are stated and tested (Task 8). Round 5
(`codex/gpt-6-astra`, revise: P2 1, P3 1; ruling: report sidecars accepted as a narrow
presentation-state exception rather than a kernel outcome change): revision 6 makes the
sidecar durable (directory fsync), closes the invocation in `finally` on any
presentation failure with fault-injection and fresh-dispatcher continuation tests, and
documents the sidecar as historical commentary in the guide and the framework (Tasks 8,
12). Round 6 (`codex/gpt-6-astra`, revise: P2 2): revision 7 syncs the three fixed
directories including `operations_root/` on every write, and splits the failure contract
at the rename, a complete sidecar possibly surviving a post-rename fsync failure and a
retry reading it when present (Task 8). Round 7 (`codex/gpt-6-astra`): accept, no
findings; approved by Keith 2026-10-28.

**Status:** **approved by Keith 2026-10-28 at revision 7, `8937235`**, after review round 7
(`codex/gpt-6-astra`, accept, no findings). Execution ruling (round 3, the user):
subagent-driven, implementers sequential, a whole-branch review before each phase merges;
execution starts in a fresh session with the Setup baseline (`just test`, count noted on
sci-9104fb). Tasks 13–15 stay blocked on `beliefs-a989fb` and are revised against its
merged design before they start.

## Global Constraints

- Every registry write follows the ledger line that is its evidence (commons §7.4); 1b
  adds no sharing transition and no new command, so `tools/cli.toml` and the adapters are
  untouched. `keep` is a configuration key (§3.2).
- `just test-one <args>` while working, `just test-fast` before each commit; paths relative
  to `python/`. Never `pytest` directly.
- Refusal codes are the closed set `science/refusal.py:CODES`; this plan adds exactly
  `divergent-publication`, `corpus-retired` and `config-stale` (Task 3, Task 8, Task 10).
  `chain-retired` is a `rule` value of `adopt-conflict`, not a code.
- `adopt-conflict` data is `{"rule": <rule>, "addresses": [...], "corpus": <corpus id>}`
  with `rule` one of `content`, `deprecated-key`, `uid-corruption` (Task 2) or
  `chain-retired` (Task 8, where `addresses` is `[]` and `corpus` the retired
  intermediate).
- Every comparison of two copies of a record is `beliefs.world.registry.content_identity`
  on the parsed node; no science digest, no byte comparison (§5.1, §5.2, §5.4).
- `supersession.py` and `retention.py` are pure over parsed inputs (`MarkerFields`,
  pins, `SharingLine`s, `ReadView`s); the kernel is read through `publication_tip`,
  `closure_missing` and `World.status` only, so unit tests feed values and the fixture
  tests prove the wiring.
- A write handler refuses only before its first act; `adopt`'s refusals after sharing
  lines are permitted as in 1a (sharing lines are not act lines).
- Reads by root: everything `adopt` compares, classifies or walks is read from the
  sharing registry's roots and the configured roots by `ReadView.opened_at`, never from
  `ctx.mounts()`, which is fixed at session open (§5.1, §5.7 step 3).
- The kernel door `ScopedWriter.retire` does not exist. Tasks 13–15 state the names this
  plan assumes; when `beliefs-a989fb` lands, their Interfaces blocks and code are revised
  together against the merged kernel design before Task 13 starts, never the 1b design. A
  task that reaches the door before it exists parks `--reason dependency` naming
  `beliefs-a989fb`.
- Test subprocess environments are built key by key (`helpers.commons.GIT_ENV`).
- Dates: the plan is written 2026-10-28; documents amended by Task 12 and Task 15 carry
  the date of their commit.

## Review Focus

Inputs the design implies but no task's tests exercise directly, most likely to bite first;
each line's test is in the owning task.

1. **`keep` naming a corpus id the sharing registry does not pin** (a typo would silently
   keep nothing): `load_config` accepts it, since §5.7 rule 1 requires the entry *before*
   the `adopt` that first pins a late predecessor; `adopt`'s re-evaluation and `show`
   report a Finding `keep names corpus <id>, which the sharing registry does not pin`.
   Tasks 8, 9.
2. **A candidate whose `(world, view, destination)` matches no mounted group** (the first
   adoption of a publisher's view): the preflight is trivially *resolved*, nothing is
   classified against, the candidate mounts. Task 8.
3. **A `mounted` ledger line for a corpus whose registry root is gone from disk** (deleted
   by hand): the fold and `show` refuse `invalid-input` naming the corpus and the root,
   never skip it. Task 6.
4. **A carried copy whose other holder is outside the session** (coordination off, so the
   session mounts the write root alone): `explain` says the copy is excluded and names no
   counting holder. Task 4.
5. **A successor whose marker names, in `supersedes_markers`, a marker uid held under a
   different corpus id than the pair says** (a forged link): the pair does not match any
   held pin's `(corpus_id, marker)`, so it is an unheld named pair and the chain is
   *unresolved*, never resolved through the wrong corpus. Task 6.

---

## File structure

- Modify `python/src/science/sharing.py` — `Pin` without `keep` (Task 1).
- Modify `python/src/science/config.py` — `keep` key; `mount_holding`/`cited` over equal
  copies; `cited`'s `corpus-retired` guard; `dataset_at` over live holders (Tasks 1, 3).
- Modify `python/src/science/refusal.py` — three codes (Tasks 3, 8, 10).
- Create `python/src/science/overlap.py` — the admission checklist (Task 2).
- Modify `python/src/science/acceptance.py` — `Carrier.content`, the Carried content check,
  `explain` wording and keys (Task 4); modify `commands/belief.py`, `commands/next.py` for
  `explain`'s new argument.
- Modify `python/src/science/world_belief.py` — the v2 rebinding (Task 5).
- Create `python/src/science/supersession.py` — groups, ancestry, classification, the
  current-publication fold, missing links (Task 6).
- Create `python/src/science/retention.py` — the required set and the dependency walk
  (Task 7).
- Modify `python/src/science/commands/adopt.py` — checklist, preflight, order,
  re-evaluation up to the retirement call (Task 8); the door call and reconcile (Task 13).
- Modify `python/src/science/commands/show.py` — supersession and retention blocks (Task 9).
- Modify `python/src/science/commands/publish.py`, `publish_preview.py` — the
  `corpus-retired` guard and the `attribution-ambiguous` detail (Task 10).
- Modify `python/tests/helpers/commons.py` — the 1b fixture chain (Task 11); create
  `python/tests/test_commons_1b.py` (Task 11, extended by Task 14).
- Modify documents (Tasks 12, 15).

---

### Task 1: `keep` moves to the configuration

**Files:**
- Modify: `python/src/science/sharing.py:65-80,124-150` (`Pin`, `_pin_from`, `_pin_to`),
  `python/src/science/config.py:50-73,142-278` (`ScienceConfig`, `load_config`)
- Modify: `python/tests/helpers/commons.py:219-247` (`write_commons_config` writes `keep`),
  `python/src/science/commands/show.py:85-89` (the `keep` row reads the configuration)
- Test: `python/tests/test_sharing_registry.py`, `python/tests/test_config_sharing.py`

**Interfaces:**
- Produces: `Pin(corpus_id, marker, artifact, world, view, source, fetch, state)` with no
  `keep` field; `ScienceConfig.keep: tuple[str, ...] = ()` and `ScienceConfig.source:
  tuple[Path, str] | None = None` (the configuration file's path and the SHA-256 of its
  bytes, set by `load_config`, `None` for a configuration built in code); `load_config`
  reads a top-level `keep = ["<32 hex>", ...]`, default `()`, refusing `invalid-input` for
  a non-list or a non-hex entry, naming the entry; an id no pin records is accepted
  (Review Focus 1). The `Pin(...)` sites in `tests/test_acceptance.py`,
  `tests/test_config_sharing.py`, `tests/test_publish_ownership.py` and
  `tests/test_sharing_registry.py` already pass no `keep`; they need no edit.

- [ ] **Step 1: Write the failing tests**

```python
# test_sharing_registry.py
def test_a_pin_file_with_a_keep_key_still_parses_and_is_rewritten_without_it(tmp_path):
    registry = SharingRegistry(tmp_path); registry.write_pin(PIN)
    path = tmp_path / "pins" / f"{PIN.corpus_id}.json"
    data = json.loads(path.read_text()); data["keep"] = False; path.write_text(json.dumps(data))
    assert registry.pin(PIN.corpus_id) == PIN
    registry.write_pin(PIN)
    assert "keep" not in json.loads(path.read_text()) and json.loads(path.read_text())["version"] == 1
# test_config_sharing.py
def test_keep_loads_as_corpus_ids(tmp_path): ...            # keep = ["0"*32] -> cfg.keep == ("0"*32,), pinned or not
def test_keep_defaults_to_empty(tmp_path): ...
def test_keep_refuses_a_non_hex_entry(tmp_path): ...        # invalid-input naming the entry
def test_load_config_records_the_files_path_and_digest(tmp_path): ...   # cfg.source == (path, sha256(bytes))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_sharing_registry.py tests/test_config_sharing.py -v`
Expected: FAIL (`_pin_to` still writes `keep`; `ScienceConfig` has no `keep` or `source`).

- [ ] **Step 3: Implement**

Remove `keep` from `Pin`, `_pin_from` (stop reading it; other keys are already ignored),
`_pin_to`, and `apply_line`'s positional `pin.keep` argument (`sharing.py:~267`). Add
`keep` and `source` to `ScienceConfig` and to `load_config` (`_OPTIONAL_KEYS` gains
`keep`; read the file's bytes once for the digest and parse them with `tomllib.loads`),
`keep` validated like `accept` (`config.py:175-179`); `show`'s `keep` row becomes
`_yes(corpus_id in config.keep)` (`test_cmd_show.py:32`'s `keep: no` stays true);
`write_commons_config` emits `keep`.

- [ ] **Step 4: Run the tests and the fast suite**

Run: `just test-one tests/test_sharing_registry.py tests/test_config_sharing.py tests/test_acceptance.py tests/test_cmd_show.py -v`, then `just test-fast`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(sharing): keep is a configuration list, not a pin flag"
```

---

### Task 2: The admission checklist

**Files:**
- Create: `python/src/science/overlap.py`
- Test: `python/tests/test_overlap.py` (new; build two corpora the way
  `tests/test_two_corpora.py` does, with `stored` node builders)

**Interfaces:**
- Consumes: `beliefs.world.registry.content_identity(node) -> str`;
  `ReadView.iter_stored()`, `node.id`, `node.uid`, `node.deprecated_ids`.
- Produces:

```python
@dataclass(frozen=True)
class Conflict:
    rule: Literal["content", "deprecated-key", "uid-corruption"]
    addresses: tuple[str, ...]   # sorted
    corpus: str                  # the live corpus the candidate conflicts with

def conflicts(candidate: ReadView, live: Sequence[tuple[str, ReadView]]) -> Conflict | None
```

  Rule order (§5.1, kernel §4.2): `uid-corruption` first — a candidate uid held in a live
  corpus under a different canonical `id`; then every key of a candidate record (its `id`
  and each `deprecated_ids` entry) that a live corpus holds as a key must belong to a
  record of equal `content_identity`; a differing live-address-to-live-address pair is
  `content`, any other differing shared key is `deprecated-key`. The first live corpus in
  `live` order that conflicts is reported, with every conflicting address of that corpus.
  Equal content under a shared key is no conflict.

- [ ] **Step 1: Write the failing tests**

```python
def test_equal_copies_share_an_address_without_conflict(two_corpora): assert conflicts(copy, [("live", original)]) is None
def test_differing_content_at_a_shared_live_address_is_content(...): assert conflicts(...) == Conflict("content", ("proposition:p",), "live")
def test_a_live_address_meeting_another_records_deprecated_id_is_deprecated_key(...)
def test_two_differing_records_sharing_a_deprecated_id_is_deprecated_key(...)
def test_a_uid_held_live_under_another_address_is_uid_corruption_before_any_key_rule(...)
def test_the_first_conflicting_live_corpus_is_named_with_all_its_addresses(...)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_overlap.py -v`
Expected: FAIL with `ModuleNotFoundError: science.overlap`.

- [ ] **Step 3: Implement `overlap.py`**

Index each live view once: `keys: dict[str, tuple[str, str]]` (key → (canonical id,
content)) and `uids: dict[str, str]` (uid → canonical id). One pass over the candidate.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_overlap.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/overlap.py python/tests/test_overlap.py
git commit -m "feat(sharing): the admission checklist over content identity"
```

---

### Task 3: Session-holder resolution over equal copies, and the retired-corpus guard

**Files:**
- Modify: `python/src/science/config.py:435-437,505-517,563-581` (`dataset_at`,
  `mount_holding`, `cited`), `python/src/science/refusal.py:9-15`
- Test: `python/tests/test_context.py`, `python/tests/test_mount_citations.py`

**Interfaces:**
- Consumes: `content_identity`; `self.world.status(corpus_id).live`.
- Produces: `ReadContext.mount_holding(ref)` and `cited(ref)` return, for several holders
  with equal content identity, the write root's mount when it holds `ref`, else the least
  `corpus_id`'s; unequal holders refuse `invalid-input` naming every holder and that the
  copies differ. `cited` additionally refuses `Refused(Refusal("corpus-retired", <message
  naming the corpus, the record and "reopen the session">, {"corpus": …, "record": …}))`
  when the chosen holder's kernel status is `known and not live` (a configured root the
  world never admitted is a different, existing refusal). `dataset_at` considers only read
  views whose corpus is not `known and not live`. `CODES` gains `corpus-retired`. The
  retired-corpus tests use the `reopened` fixture (P1 mounted at *B*; under `adopted` the
  session's ids are *B*'s write root alone and no guard can fire) and retire P1 with
  `open_world(cfg.world, authority=FIXTURE_AUTHORITY).retire(cid)`, the kernel act the door
  will wrap in Task 13; `ReadContext.open(cfg).world.status(cid)` rescans the registry and
  reads `live is False` while the pin stays `mounted`.

- [ ] **Step 1: Write the failing tests**

```python
def test_cited_answers_the_write_root_for_equal_copies_in_two_mounts(two_corpora_equal_copy): ...
def test_cited_answers_the_least_corpus_for_equal_copies_outside_the_write_root(...): ...
def test_cited_refuses_differing_copies_naming_both_holders(...): assert r.code == "invalid-input" and "differ" in r.message
def test_mount_holding_follows_the_same_rule(...): ...
def test_cited_refuses_a_record_held_only_by_a_retired_corpus(reopened):
    cid = a_identity(reopened.a)["corpus_id"]; ref = a_identity(reopened.a)["assessment"]
    open_world(reopened.b.world, authority=FIXTURE_AUTHORITY).retire(cid)
    r = refused(lambda: ReadContext.open(reopened.b).cited(ref)); assert r.code == "corpus-retired" and r.data == {"corpus": cid, "record": ref}
def test_dataset_at_ignores_a_retired_holder(reopened): assert ReadContext.open(reopened.b).dataset_at(a_identity(reopened.a)["dataset"]) is None   # after the same retire
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_context.py tests/test_mount_citations.py -v`
Expected: FAIL (two holders refuse as duplicate location; no `corpus-retired` code).

- [ ] **Step 3: Implement**

A private `_holder_among(holders: list[Mount], ref) -> Mount` shared by both methods;
`cited` calls `_require_live(mount, ref)` after choosing. `dataset_at` passes
`[(cid, view) for cid, view in self.read_views() if not _retired(self.world.status(cid))]`
with `_retired(status) = status.known and not status.live`, the same predicate
`_require_live` uses.

- [ ] **Step 4: Run the tests and the fast suite**

Run: `just test-one tests/test_context.py tests/test_mount_citations.py -v`, then `just test-fast`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(context): equal copies resolve to one holder; a retired holder refuses citation"
```

---

### Task 4: The Carried branch compares content; `explain` names copies

**Files:**
- Modify: `python/src/science/acceptance.py:27-35,47-61,111-139,165-192`,
  `python/src/science/commands/belief.py`, `python/src/science/commands/next.py` (the
  `explain` call sites)
- Test: `python/tests/test_acceptance.py`, `python/tests/test_cmd_belief.py`,
  `python/tests/test_commons_1a.py:101-128` (the `excluded` key changes)

**Interfaces:**
- Produces: `Carrier` gains `content: Mapping[str, str]` (address → content identity of
  the carrier's copy), filled by `_carrier`. `counts(inputs, corpus_id, address)` keeps its
  signature; the Carried branch additionally requires
  `inputs.carriers[origin].content.get(address) == carrier.content[address]`.
  `explain(context, inputs, holders_of: Callable[[str], tuple[str, ...]]) ->
  tuple[tuple[str, str], ...]`, where `holders_of(address)` returns the session corpus ids
  holding `address`; each excluded pair renders as key `excluded <address> (<corpus>)`
  and value `corpus <c>; copy of a record that counts through corpus <h>` when some other
  holder `h` counts under `inputs`, else `corpus <c>; world <w>` as today. `belief.py` and
  `next.py` pass `lambda a: tuple(m.corpus_id for m in ctx.session_mounts() if m.view.holds(a))`.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_carried_copy_equal_to_the_origins_counts(): ...      # CARRIER_B.content[A_ASSESSMENT] == CARRIER_A.content[A_ASSESSMENT] -> True under accept A
def test_a_carried_copy_differing_from_the_origins_never_counts(): ...   # same inputs, differing content -> False
def test_explain_words_a_copy_whose_record_counted_elsewhere_as_a_copy(): ...
def test_explain_keys_are_qualified_by_corpus(): ...            # two corpora excluding one address -> two keys
def test_explain_names_no_counting_holder_when_the_other_holder_is_outside_the_session(): ...  # Review Focus 4
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_acceptance.py -v`
Expected: FAIL (`Carrier` has no `content`).

- [ ] **Step 3: Implement**

`_carrier` computes `{node.id: content_identity(node) for node in records}` from the
records it already reads. The fixture-level assertion in `test_commons_1a.py` becomes
`acceptance[f"excluded {ids['assessment']} ({ids['corpus_id']})"] == f"corpus {ids['corpus_id']}; world {ids['world']}"`.

- [ ] **Step 4: Run the tests and the fast suite**

Run: `just test-one tests/test_acceptance.py tests/test_cmd_belief.py tests/test_commons_1a.py -v`, then `just test-fast`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(acceptance): the Carried branch compares content identities; explain names copies"
```

---

### Task 5: Rebind the retraction enumeration to v2

**Files:**
- Modify: `python/src/science/world_belief.py:26-31` (`SYMBOL_FIELDS`)
- Test: `python/tests/test_epoch_verb.py`

**Interfaces:**
- Produces: `SYMBOL_FIELDS == {"derive_producer_snapshot": "producer",
  "enumerate_retractions_v2": "retraction", "enumerate_certifications": "certification",
  "reduce_coreference": "coreference"}`; `build_over` is unchanged (it selects by symbol).

- [ ] **Step 1: Write the failing test**

```python
def test_symbol_fields_binds_the_v2_retraction_enumeration_and_not_v1():
    assert SYMBOL_FIELDS["enumerate_retractions_v2"] == "retraction" and "enumerate_retractions" not in SYMBOL_FIELDS
def test_an_epoch_science_builds_names_the_v2_rule(shared): ...   # test_epoch_verb's own `shared` world; build_over, then the epoch's retraction binding is enumerate_retractions_v2's identity
```

- [ ] **Step 2: Run to verify it fails** — `just test-one tests/test_epoch_verb.py -v`; Expected: FAIL.
- [ ] **Step 3: Replace the dict entry.**
- [ ] **Step 4: Run** `just test-one tests/test_epoch_verb.py -v`, then `just test-fast`; Expected: PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(epoch): bind the retraction enumeration to v2"`

---

### Task 6: `supersession.py`

**Files:**
- Create: `python/src/science/supersession.py`
- Test: `python/tests/test_supersession.py` (new; pure inputs built from
  `MarkerFields(...)`, `Pin(...)`, `SharingLine(...)`)

**Interfaces:**
- Consumes: `science.publication.MarkerFields`, which this task extends with
  `destination: Destination` read from the marker facet's `destination` member through
  `Destination.from_projection` (`marker_fields` fills it); `science.publication.marker_of(root)`;
  `beliefs.publication_arrival.publication_tip(roots: tuple[Path, ...], view:
  CoordinationAddress, destination: Destination)` (`CoordinationAddress.parse` for the
  view); `beliefs.session.ledger.read_ledger_evidence`, `LedgerReader.sharing()`;
  `science.sharing.replay`'s ordering key `(at, session id, position)`.
- Produces:

```python
@dataclass(frozen=True)
class Held:                      # one established authorized root, parsed once
    corpus_id: str
    root: Path
    marker: MarkerFields
    state: Literal["mounted", "retired"]

GroupKey = tuple[str, str, str]  # (world, unpinned view, destination locator), from the marker alone

def group_of(marker: MarkerFields) -> GroupKey
def sharing_lines(operations_root: Path) -> tuple[SharingLine, ...]
    # every ledger's sharing lines in replay order; refuses SharingLedgerUnreadable as replay does
def established(registry: SharingRegistry, lines: Sequence[SharingLine]) -> tuple[Pin, ...]
    # the pins folded in memory from `lines` under apply_line's state rule, keeping `mounted`
    # and `retired` only; never reads pin files; refuses invalid-input naming the corpus and
    # root when a mounted pin's root is unreadable (Review Focus 3)
def authorized(pins: Iterable[Pin], bindings: Mapping[str, ProviderBinding], registry, key: GroupKey) -> tuple[Held, ...]
    # established pins in the group whose source is origin-confirmed to key[0]
def ancestry(tip: tuple[str, str], held: Iterable[Held]) -> frozenset[tuple[str, str]]
    # (corpus_id, marker uid) pairs reachable from `tip` through supersedes_markers, following
    # held markers where the named pair is held, keeping unheld named pairs as members

@dataclass(frozen=True)
class Outcome:
    kind: Literal["resolved", "divergent", "unresolved"]
    tip: tuple[str, str] | None          # resolved: the one tip
    tips: tuple[tuple[str, str], ...]    # divergent or unresolved
    missing: tuple[tuple[str, str], ...] # unresolved: the unheld named pairs

def classify(held: Sequence[Held], candidate: Held | None = None) -> Outcome
    # publication_tip over the roots (candidate's included); one tip -> resolved; several:
    # divergent iff ANY two tips' ancestries intersect (a sibling pair is a fork whatever other
    # tips a gap leaves standing), else unresolved with the unheld pairs
def current(lines: Sequence[SharingLine], held: Sequence[Held]) -> tuple[str, str] | None
    # §5.6's fold over the group's `mounted` lines in replay order, links through held markers seen so far
def chain(from_pair, to_pair, held) -> tuple[tuple[str, str], ...] | None
    # the held pairs from `from_pair` to `to_pair` by supersession, None when no held path
```

- [ ] **Step 1: Write the failing tests**

```python
def test_group_key_is_world_view_destination(): ...
def test_two_tips_under_one_held_predecessor_are_divergent(): ...
def test_two_tips_naming_one_unheld_predecessor_are_divergent(): ...          # named ancestry
def test_a_tip_naming_an_unheld_intermediate_is_unresolved_naming_the_pair(): ...
def test_a_sibling_pair_is_divergent_even_beside_a_disconnected_tip(): ...   # P2 and P2' under P1, plus P4 with its link missing: divergent, not unresolved
def test_a_forged_link_naming_a_held_marker_under_the_wrong_corpus_is_unheld(): ...   # Review Focus 5
def test_current_follows_a_gap_filler_and_ignores_a_disconnected_adoption():   # P1, P4, P2 (P3 absent) -> P2
def test_current_is_unmoved_whichever_end_of_a_gap_arrives_second(): ...        # both orders
def test_current_orders_a_same_second_pair_by_ledger_position(): ...
def test_a_retired_line_is_not_consumed_and_a_retired_root_still_links(): ...
def test_established_keeps_mounted_and_retired_only_and_folds_without_reading_pin_files(tmp_path): ...
def test_established_refuses_a_mounted_pin_whose_root_is_missing(tmp_path): ...  # Review Focus 3
```

- [ ] **Step 2: Run to verify they fail** — `just test-one tests/test_supersession.py -v`; Expected: FAIL (module missing).
- [ ] **Step 3: Implement `supersession.py`** as the Interfaces block says; `classify` builds
  the roots tuple for `publication_tip` from `Held.root` values and maps the kernel's
  `CurrentPublication`/`DivergentPublication`/`None` onto `Outcome`.
- [ ] **Step 4: Run** `just test-one tests/test_supersession.py -v`, then `just test-fast`; Expected: PASS.
- [ ] **Step 5: Commit** — `git add python/src/science/supersession.py python/src/science/publication.py python/tests/test_supersession.py && git commit -m "feat(sharing): supersession groups, named ancestry and the current-publication fold"`

---

### Task 7: `retention.py`

**Files:**
- Create: `python/src/science/retention.py`
- Test: `python/tests/test_retention.py` (new; write-root records built with
  `stored.assessment_node`, `run_node`, `verification_node`, `analysis_spec_node` into a
  corpus, a "predecessor" corpus holding the records the successor dropped)

**Interfaces:**
- Consumes: `beliefs.publish_request.closure_missing(view, selected)`; `stored` decoders
  `assessment_value(node, profile=…)` (`.spec`, `.run`, `.proposition`), `run_spec(node)`,
  `verification_derivation(node)`, `analysis_spec_value(node, profile=…)` (`.target`,
  `.input_roles[*].dataset`); `content_identity`; Task 6's `Held`, `chain`.
- Produces:

```python
@dataclass(frozen=True)
class Reason:
    kind: Literal["configuration", "chain", "attribution", "dependency"]
    detail: tuple[str, ...]   # chain: (the kept corpus,); attribution: (the naming corpus,); dependency: sorted addresses

Holder = tuple[str, ReadView, ProfileSpec]   # (corpus_id, view opened by root, that root's manifest profile)

def dependency_closure(write_root: Holder, holders: Sequence[Holder]) -> frozenset[str]
    # the fixed point of: seed = every write-root record's address; for each seed address, the holder
    # among `write_root` + `holders` that holds it (any, bytes equal under the checklist) supplies the
    # node; add closure_missing(holder.view, (address,)) and the facet references of §5.7 rule 4, decoded
    # under that holder's profile (assessment spec/run/proposition; run spec; verification's two runs;
    # spec's dataset roles and target; correction target); `supersedes` fields are not followed; stop
    # when no address is added. A seed held by no holder is kept as an address and not expanded.
def required(predecessor: Held, *, keep: Sequence[str], group_chain: Sequence[Held], tip: tuple[str, str],
             mounted: Sequence[Held], write_root: Holder, live: Sequence[Holder]) -> tuple[Reason, ...]
    # every applicable reason, in the kind order above; `dependency` lists the closure addresses that only
    # `predecessor` holds with equal content among `live`
```

- [ ] **Step 1: Write the failing tests**

```python
def test_dependency_closure_reaches_a_verifications_target_and_its_runs_spec_through_facets(...)
def test_dependency_closure_reaches_a_specs_target_proposition(...)            # the spec-only case, unit level
def test_dependency_closure_does_not_follow_supersedes_fields(...)
def test_required_by_dependency_lists_only_addresses_no_other_live_corpus_holds_equal(...)   # the spec-drop case, unit level
def test_required_by_configuration(...)
def test_required_by_attribution_names_the_naming_corpus(...)
def test_chain_retention_keeps_every_publication_between_a_kept_one_and_the_tip(...)
def test_nothing_required_is_empty(...)
```

- [ ] **Step 2: Run to verify they fail** — `just test-one tests/test_retention.py -v`; Expected: FAIL.
- [ ] **Step 3: Implement `retention.py`** as the Interfaces block's fixed point says.
- [ ] **Step 4: Run** `just test-one tests/test_retention.py -v`, then `just test-fast`; Expected: PASS.
- [ ] **Step 5: Commit** — `git add python/src/science/retention.py python/tests/test_retention.py && git commit -m "feat(sharing): why a superseded publication stays mounted"`

---

### Task 8: `adopt` — checklist, preflight, order and re-evaluation

**Files:**
- Modify: `python/src/science/commands/adopt.py` (whole handler), `commands/adopt/prompt.md`,
  `python/src/science/refusal.py` (`divergent-publication`, `config-stale`),
  `python/src/science/render.py:53-64` (`audit_sharing_report`),
  `python/src/science/dispatch.py:346-353,481-536` (the first response and the continuation
  of a `sharing` invocation), `python/src/science/report.py` (`tail_to_json`,
  `tail_from_json`), `python/src/science/commands/provider_bind.py` (returns `()`)
- Test: `python/tests/test_cmd_adopt.py`, `python/tests/test_dispatch_sharing.py`,
  `python/tests/test_cmd_provider.py`, `python/tests/helpers/commons.py` (the candidate
  builders below)

**The sharing report contract, extended.** Today `audit_sharing_report` refuses any block
that is not a `PinBlock`, the dispatcher renders `_pin_report(lines)` whatever the handler
returned, the write cursor hashes the rendered report (`_render_write`), and
`_continue_write` rebuilds `_pin_report(record.sharing)` and refuses `stale-cursor` on a
digest mismatch. So `adopt` could not say why a predecessor is kept, and any report that
differed from the pin blocks would refuse its own continuation. This task changes the
contract and Task 12 records it as a dated amendment of the framework's §4.4 `sharing`
class:

- A `sharing` **handler returns informational blocks only** (`KeyVals`, `Finding`), its
  reading of registry and kernel state; it never authors a `PinBlock`. Every sharing
  handler converts: `adopt` (today `pin_block(line)` per line), `provider-bind` (today
  `(pin_block(line),)`, now `()`), and the synthetic sharing handlers in
  `test_dispatch_sharing.py`. A regression test shows a successful binding still renders
  its canonical `bound` pin block.
- The **canonical report** is composed by the dispatcher: `_pin_report(lines)` (every
  sharing line of the invocation, in ledger order: the complete pin prefix, so a committed
  effect cannot be omitted) followed by the handler's tail. `audit_sharing_report(tail)`
  refuses any `PinBlock` in the tail.
- The tail is **persisted by science, not by the kernel**, as a **report sidecar**, the
  one presentation-state exception review round 5 ruled (the ledger's close outcome is
  exactly `{"done": …}` or `{"refusal": …}`, `beliefs.session.ledger.validated_outcome`
  refuses a second key, and extending the kernel's effect protocol for commentary was
  rejected). The dispatcher writes the tail, before `close_invocation`, to
  `operations_root / "tails" / <session id> / <invocation id>.json` (science already owns
  `transport/` and `scratch/` under the operations root), through a new
  `report.write_tail(operations_root, session_id, invocation_id, blocks)`: `tails/` and
  `tails/<session id>/` created as needed, a temp file in the target directory, write,
  `fsync` the file, `os.replace`, then **`fsync` the three fixed directories in order,
  `tails/<session id>/`, `tails/`, `operations_root/`**, on every write and not only when
  this attempt created them (a directory entry is durable only when its containing
  directory is synced, and a directory left by an earlier failed attempt is as unsynced as
  a new one), so the entry survives a crash that the ledger's close survives; each block
  serialised as `{"kind": "keyvals", "title": …, "pairs": [[k, v], …]}` or `{"kind":
  "finding", "text": …}` (`report.tail_to_json` / `report.tail_from_json`).
  `_continue_write` and the replay of a closed invocation rebuild
  `_pin_report(record.sharing)` plus the tail read from that file, so the cursor digest
  matches; **an absent file is an empty tail**, which is what every 1a invocation has, so
  their cursors and replays keep working.
- The tail is **historical commentary, not a cache**: it is the invocation's explanation
  at the time it ran, and `show` explains the *current* state, which configuration or
  retention changes move. Losing a sidecar loses that commentary and makes any cursor
  issued over it stale (`stale-cursor`, re-run); the ledger-backed effects stay
  recoverable and complete. Exact historical replay therefore needs the sidecar retained
  beside the ledger.
- **Failure contract.** The audit, the tail serialisation and `write_tail` run inside the
  `try` whose `finally` closes the invocation `done` (today's shape for the audit alone):
  a presentation failure of any kind, `AuditViolation` or an `OSError` from the sidecar
  write, never leaves committed effects in an open invocation; the error propagates in
  both cases below. **Before the rename** (serialisation, temp-file write, file fsync,
  `os.replace` itself) no final sidecar exists, only an unrenamed temp file at most, and a
  retry renders pins only. **After the rename** (a directory fsync fails) a complete
  sidecar exists without a durability guarantee; a retry reads it when it is present and
  renders pins only when a crash took it. Neither case claims the sidecar durable.

Fault-injection tests in `test_dispatch_sharing.py`: `os.replace` raising inside
`write_tail` → the invocation is closed `done`, the error propagates, no final tail file
exists, the retry renders pins only; `tail_to_json` raising → the same; `os.fsync` raising
on the first directory fsync after a successful rename → closed `done`, the error
propagates, the complete sidecar exists and the retry renders it; the three directory
fsyncs happen in the stated order on a first write (`tails/` and `<session id>/` created
by this write) and again on a later write to the same session; a tail written and then
deleted by hand → continuation refuses `stale-cursor` and replay renders pins only; a
continuation through a **fresh `Dispatcher`** over the same operations root renders the
same page as the first one.
- Pagination is therefore one contract for every page: a page may end inside a pin block
  or inside the tail, and the cursor continues from the ledger-rebuilt report plus the
  persisted tail.

Unit tests in `test_dispatch_sharing.py`: a handler returning a `PinBlock` is refused by
the audit and the retry renders the pin report; `provider-bind`'s binding renders its
`bound` pin block; a tail renders after the complete pin prefix on the first response; an
invocation with two sharing lines and a tail renders both pins before the tail; with a
small `output_budget` a cursor issued inside a pin block and one issued inside the tail
both continue to the same text; a retry of a closed invocation renders the persisted tail;
an invocation whose tail file is absent (a 1a-shaped ledger) continues and replays as pins
only.

**Interfaces:**
- Consumes: Task 2 `conflicts`; Task 6 `established`, `authorized`, `classify`, `current`,
  `chain`, `group_of`; Task 7 `required`; `ctx.world.registry().admissions`,
  `ctx.world.status`.
- Produces: `handle(ctx, writer, *, location, corpus_id)` in this order (§5.7):
  1. inputs; `replay`; **reconcile completed effects**: `fetched`/`admitted` pins the
     kernel lists admitted → `mounted` line and pin (as today); `mounted` pins whose kernel
     status is `known and not live` and whose status record is `retired` → see Task 13
     (until then: a Finding `retirement pending: the kernel's retire door (beliefs-a989fb)
     has not landed` per such pin, nothing written); a `departed` status record → its own
     Finding. A `fetched` pin is never looked at here.
  2. target state (as today, with one change: an already-mounted target proceeds to step 4
     and refuses `invalid-input` "already adopted" only when **the whole invocation wrote
     nothing**, step 1's reconcile included; a crash between admission and the `mounted`
     mark is recovered by step 1 and reported as the recovery it is, which the existing
     `test_a_crash_after_admission_before_the_pin_write_recovers_with_its_source` keeps
     asserting).
  3. candidate: fetch or reuse (as today); **checklist**: `conflicts(candidate_view,
     live)` with `live` = every corpus the kernel lists admitted and live, read by root
     (configured roots + registry roots), plus candidates admitted this invocation →
     `adopt-conflict` with the `Conflict`'s rule, addresses and corpus, the candidate
     `fetched`; when `corpus` is a required predecessor (Task 7 over the candidate's
     group), the message appends why (commons §10.5); **preflight**: `classify(authorized
     held, candidate)` → `divergent` refuses `Refusal("divergent-publication", <message
     naming the sibling tips>, {"tips": [...]})`, candidate `fetched`; a chain from the
     candidate to the group's current or any mounted member that passes only through a
     `retired` `Held` → `adopt-conflict` rule `chain-retired`, `corpus` = the retired
     intermediate; otherwise admit and mark `mounted` (as today).
  4. **re-evaluation** over every group of the established state: for each `resolved`
     group, each mounted non-tip member in chain order; `required(...)` empty → first the
     stale check, then Task 13's retirement (until then: the pending-door Finding, nothing
     written); non-empty → a `KeyVals("retention <corpus>", (("kept", "configuration" |
     "chain (for <c>)" | "attribution (named by <c>)" | "dependency (<addresses>)"), …))`
     block. The **stale check**: when `config.source` is not `None` and the file's current
     SHA-256 differs from the recorded one, raise `Refused(Refusal("config-stale",
     <message naming the file, the `keep` list evaluated under and the remedy "restart the
     service and rerun adopt">, {"path": …, "keep": [...]}))`; the invocation closes
     refused and its report is not rendered (`dispatch.py`'s `_close_refused`), but the
     adoption stands because its lines are written, and the message says so. The compared
     path is `config.source[0]` as `load_config` received it; the test rewrites that file
     after the fixture is restored (the restore puts back the loaded bytes, so the digest
     matches at the test's start). With `config.source` `None` the check is skipped. A
     `keep` entry naming a corpus no pin records is a Finding (Review Focus 1). Each
     retirement (Task 13) adds to the tail a `KeyVals("retirement <corpus>", (("keep",
     <the list>), ("remedy", "reopen the session and run science epoch")))` block; the pin
     blocks of two retirements in one invocation both precede the tail, by the contract
     above.
  The prompt describes the new refusals and blocks.

  Candidate builders for the checklist, in `helpers/commons.py`, each from
  `build_reopened`'s installations (each builder is its own snapshot, so neither needs the
  fork of Task 11): `build_content_conflict` (`CorpusWriter.revise` of *A*'s proposition
  with new prose under `FIXTURE_AUTHORITY`, which keeps its id and uid; epoch; publish
  project `a` to `LOC_A3 = "https://remote.test/a3"`; *B* binds `LOC_A3` to *A*'s world and
  adopts → `content` at the proposition's address, `corpus` = P1) and
  `build_uid_corruption` (value `{"installations": value, "c": <ScienceConfig>,
  "corpus_id": <the successor's>}`, as `build_conflicting` shapes its own: a third
  installation `c` built with `build_installation(work, "c", hold_vocabulary=False)`, one
  `source` record minted through the kernel under `FIXTURE_AUTHORITY` with
  `stored.source_node` since no science command mints a source, a project whose query is
  `kinds: [source]`, published to `LOC_C = "https://remote.test/c"`; *B* binds `LOC_C` to
  *C*'s world and adopts; then `correct_identifier` on that source under
  `FIXTURE_AUTHORITY` with identifiers whose basis changes (one DOI replaced by a different
  DOI), which moves the address, keeps the old one in `deprecated_ids` and preserves the
  uid; epoch; republish to `LOC_C`; *B* adopts the successor → `uid-corruption`, `corpus`
  = *C*'s first publication). The `deprecated-key` rule has no publication route in the
  fixture (a differing record sharing a deprecated id needs a second world minting at the
  old address) and is proved by Task 2's unit test alone; the command path is the same
  `conflicts` call.

- [ ] **Step 1: Write the failing tests**

```python
def test_an_equal_content_republication_passes_the_checklist_and_mounts(conflicting_publication): ...  # B adopts P1 then P1' from LOC_A2; both mounted
def test_a_differing_copy_refuses_adopt_conflict_content_and_stays_fetched(content_conflict): ...
def test_a_redirect_published_as_a_successor_refuses_uid_corruption(uid_corruption): ...
def test_a_keep_entry_no_pin_records_is_a_finding(bound): ...   # Review Focus 1
def test_a_sibling_republication_refuses_divergent_publication_and_stays_fetched(sibling_publications): ...
def test_siblings_under_a_never_held_predecessor_refuse_the_same_way(...): ...
def test_a_refused_sibling_left_fetched_changes_nothing_later(...): ...
def test_the_first_adoption_of_a_view_is_trivially_resolved(bound): ...   # Review Focus 2
def test_a_successor_keeps_a_predecessor_b_depends_on_and_reports_why(updated): ...   # kept: dependency (<A's assessment>)
def test_an_unrequired_predecessor_reports_retirement_pending_before_the_door(updated_unkept): ...
def test_adopting_a_mounted_corpus_again_refuses_only_when_the_invocation_wrote_nothing(...): ...
def test_two_retirements_in_one_invocation_render_both_pins_before_the_tail(...): ...   # xfail until Task 13; the three-link late-link case
def test_a_changed_configuration_file_refuses_config_stale_before_the_pending_finding(updated_unkept): ...
    # the file is rewritten after load; the empty-required branch raises config-stale (nothing is pending-reported)
```

(`sibling_publications`, `updated`, `updated_unkept` are Task 11's fixtures; this task adds
`content_conflict` and `uid_corruption` and runs against `conflicting_publication`; the
Task 11-dependent tests are written here and marked `xfail(strict=True, reason="Task 11
fixture")` until Task 11 lands, which removes the marks.)

- [ ] **Step 2: Run to verify they fail** — `just test-one tests/test_cmd_adopt.py -v`; Expected: FAIL.
- [ ] **Step 3: Implement** the handler order; `_require_no_overlap` and `CONFLICT_REASON` are removed.
- [ ] **Step 4: Run** `just test-one tests/test_cmd_adopt.py tests/test_dispatch_sharing.py -v`, then `just test-fast`; Expected: PASS (xfails as expected).
- [ ] **Step 5: Commit** — `git commit -am "feat(adopt): the admission checklist, supersession preflight and retention re-evaluation"`

---

### Task 9: `show` — supersession and retention

**Files:**
- Modify: `python/src/science/commands/show.py`, `commands/show/prompt.md`;
  `commands/show/command.toml` is unchanged (`reads.families` stays `registry,
  corpus-stored`: `adopt` declares no read for the ledger it replays either, and
  `test_cmd_show.py:19-24` keeps asserting the exact set)
- Test: `python/tests/test_cmd_show.py`

**Interfaces:**
- Consumes: Task 6 (`established`, `authorized`, `classify`, `current`, `chain`), Task 7
  (`required`), `ScienceConfig.keep`.
- Produces: `show --corpus-id` adds `KeyVals("supersession", (("group", "<world> <view>
  <destination>"), ("current", "<corpus> <marker>" | "divergent: <tips>" | "unresolved:
  adopt <corpus> <marker>"), ("this pin", "tip" | "superseded by <corpus>" | "sibling" |
  "unlinked chain beside <corpus>")))` and, for a superseded or retired pin,
  `KeyVals("retention", (("kept", …) per reason | ("retired", "yes") | ("pending", "no
  door")))`. The established set is folded in memory (Task 6), not read from pin files.

- [ ] **Step 1: Write the failing tests** (`test_show_a_tip_reports_current_and_tip`,
  `test_show_a_superseded_kept_pin_reports_every_reason`, `test_show_an_unresolved_group_names_the_link_to_adopt`,
  `test_show_an_unlinked_second_destination_reports_it`, `test_show_reports_pending_no_door_on_the_unkept_branch`,
  `test_show_keep_row_reads_the_configuration`; fixture-dependent ones xfail until Task 11).
- [ ] **Step 2: Run to verify they fail** — `just test-one tests/test_cmd_show.py -v`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `just test-one tests/test_cmd_show.py -v`, then `just test-fast`; Expected: PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(show): supersession and retention of a pin"`

---

### Task 10: `publish` and `publish-preview` — the retired-corpus guard and the ambiguous-attribution detail

**Files:**
- Modify: `python/src/science/commands/publish.py`, `publish_preview.py`
- Test: `python/tests/test_cmd_publish.py`, `python/tests/test_publish_ownership.py`

**Interfaces:**
- Produces: both handlers, before the kernel call, refuse `Refusal("corpus-retired", <message
  naming the corpus and "reopen the session">, {"corpus": …})` when any `ctx.session_ids()`
  corpus has `ctx.world.status(cid).live is False`. `publish`'s `PublicationRefused` with
  reason `attribution-ambiguous` is rendered with `field`'s claims as `<corpus>:<marker>`
  pairs and either `adopt <corpus> <marker> from a location bound to world <w> to connect
  them` (the pair a held tip's `supersedes_markers` names) or `no held marker orders these
  claims; the record cannot be published while both carriers are mounted` when every
  claimed marker's `supersedes_markers` is empty.

- [ ] **Step 1: Write the failing tests**

```python
def test_publish_refuses_corpus_retired_when_a_session_corpus_is_not_live(reopened): ...   # World.retire directly, as Task 3; P1 is a session corpus only under reopened
def test_publish_preview_refuses_the_same_way(reopened): ...
def test_attribution_ambiguous_names_the_link_to_adopt(...): ...                  # xfail until Task 11's late-link fixture
def test_attribution_ambiguous_with_unlinked_chains_says_no_marker_orders_them(...): ... # xfail until Task 11
```

- [ ] **Step 2: Run to verify they fail** — `just test-one tests/test_cmd_publish.py -v`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `just test-one tests/test_cmd_publish.py tests/test_publish_ownership.py -v`, then `just test-fast`; Expected: PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(publish): refuse over a retired corpus; name the link an ambiguous attribution needs"`

---

### Task 11: The 1b fixture and the decisive cases through step 5

**Files:**
- Modify: `python/tests/helpers/commons.py` (new builders), `python/tests/conftest.py`
  (fixtures), `python/tests/test_cmd_adopt.py`, `test_cmd_show.py`, `test_cmd_publish.py`
  (remove the xfail marks)
- Create: `python/tests/test_commons_1b.py`

**Interfaces:**
- Produces builders, each snapshot-cached (`commons-1b-<name>`), parametrised by their
  base so the kept chain (from `build_derived`) and the unkept chain (from
  `build_reopened`, no verification at *B*) share them:
  - `fork(installation_home) -> Path` / `restore(copy, installation_home)` — a copy of one
    installation's directory taken aside and put back at the same path the way
    `helpers.snapshot.WorldSnapshot.restore` does (its live-socket guard,
    `_forget_roots_under`, `_forget_worlds_under`, `rmtree`, `copytree(symlinks=True)`);
    the one way to publish a *sibling*, since a publisher's next publish to a destination
    always supersedes its standing binding tip.
  - Base-parametrised builders are exposed as **two module-level callables each**, since
    `snapshot()` refuses a name whose stored builder is not the identical callable: the
    kept chain `build_published_b`, `build_a_bound_b`, `build_overlapping`,
    `build_updated`, `build_b_updated` (snapshots `commons-1b-<name>`) and the unkept chain
    `build_published_b_unkept`, …, `build_b_updated_unkept` (snapshots
    `commons-1b-<name>-unkept`), the latter defined as `def build_x_unkept(work): return
    _build_x(work, base=build_y_unkept)` over private `_build_x(work, *, base)` functions.
  - `build_published_b` — `publish_session_epoch(b)` (*B*'s write root drifted), then *B*
    publishes project `b` to `LOC_B` (P2).
  - `build_a_bound_b` — *A* binds `LOC_B` to *B*'s world.
  - `build_overlapping` — *A* adopts P2; `reopen(a)`; `publish_session_epoch(a)`.
  - `build_updated` — *A* revises project `a`'s query to
    `{"version": "science.view-query.v1", "clauses": [{"all": [{"addresses": [<proposition>, <data.txt dataset>, <concepts.txt dataset>, <levels.txt dataset>, <spec>, <run>]}]}]}`
    (P1's selection minus the assessment, by `a_identity` and `_list_address`), publishes
    an epoch, and publishes project `a` to `LOC_A` again (P3, superseding P1 through *A*'s
    standing binding tip).
  - `build_b_updated` — *B* adopts P3 (P1 kept by rule 4 on the kept chain); `reopen(b)`;
    epoch.
  - `build_b_updated_unkept` — `build_b_updated` over the unkept base: P1 unrequired, the
    pending-door Finding.
  - `build_sibling_publications` — from `build_overlapping`: `fork` *A*, publish P3 as
    `build_updated` does, `restore` *A*, **re-apply the same query revision** (the restore
    brought the `kinds` query back, and with P2 mounted a kinds publish would carry *B*'s
    records), epoch, publish project `a` to `LOC_A` again (P3′: its binding tip is still
    P1's, so both P3 and P3′ supersede P1, equal in content, and the remote holds both).
  - `build_late_chain` — on the unkept base, branched before `build_updated`: *A*
    publishes project `a` to `LOC_A` twice more, an epoch before each as `publish_again`
    does (P2′ superseding P1, P3″ superseding P2′; the dropped-record revision is not
    needed here); *B* holds P1 only.
  - `build_late_link` — `build_late_chain`, then *B* adopts P3″; `reopen(b)`;
    `publish_session_epoch(b)` (P1 and P3″ mounted, P2′ absent). The call that refuses
    `attribution-ambiguous` on it is the `publish` command (the epoch builds, since P1 and
    P3″ hold equal content).
  - `build_late_chain_unadopted` — from `build_bound` (*B* bound to *A*'s world, nothing
    adopted): *A* publishes project `a` to `LOC_A` twice more with an epoch before each; the
    remote holds P1 → P2′ → P3″ and *B* holds nothing. The two-sessions test adopts P1 in
    one session and P3″ in another over it.
  - Fixtures of the same names without `build_`, in `conftest.py`.
- Test cases in `test_commons_1b.py`:

```python
def test_overlap_reads_each_shared_record_once(overlapping): ...    # address map: holders == (A write root, P2) for A's records; and _world_inputs' pins name both holders (§5.4)
def test_belief_under_empty_accept_lists_two_excluded_lines(overlapping): ...   # §5.9 step 3, accept = []
def test_belief_under_accept_b_counts_as_own_assessment_through_the_write_root(overlapping): ...
def test_the_update_supersedes_p1_and_drops_only_the_assessment(updated): ...
def test_b_adopting_the_update_keeps_p1_by_dependency_and_show_says_why(b_updated): ...
def test_shared_records_of_the_two_revisions_read_once_at_b(b_updated): ...
def test_both_sides_gather_equal_identities_for_the_shared_records(b_updated): ...   # §5.9's comparison
def test_the_unkept_branch_reports_retirement_pending_and_retention_pending(b_updated_unkept): ...
def test_two_sessions_mounting_a_gaps_ends_in_one_second_order_by_session_id(late_chain_unadopted, monkeypatch): ...
    # two sessions over B, one adopting P1 and the other P3″, both under
    # monkeypatch.setattr("beliefs.session.writer.utc_now", lambda: "2026-10-28T00:00:00Z") (the writer imports
    # utc_now by name, so the ledger module's binding is not the seam); asserts the outcome is unresolved, current
    # is the end mounted by the lower session id, and nothing is retired
def test_publish_in_the_late_link_state_refuses_attribution_ambiguous_naming_the_link(late_link): ...
```

- [ ] **Step 1: Write the builders, fixtures and tests; remove the xfail marks.**
- [ ] **Step 2: Run** `just test-one tests/test_commons_1b.py tests/test_cmd_adopt.py tests/test_cmd_show.py tests/test_cmd_publish.py -v`; Expected: FAIL on the new cases first, then PASS after fixing builders.
- [ ] **Step 3: Run** `just test-fast`; Expected: PASS.
- [ ] **Step 4: Commit** — `git add python/tests/test_commons_1b.py python/tests/helpers/commons.py python/tests/conftest.py python/tests/test_cmd_adopt.py python/tests/test_cmd_show.py python/tests/test_cmd_publish.py && git commit -m "test(commons): the 1b fixture chain and the decisive cases through the update"`

---

### Task 12: Documents for the overlap half

**Files:**
- Modify: `docs/specs/2026-09-30-science-commons-design.md` (§3 pin row, §7.4, §9, §10
  except its retirement paragraphs, §11 row), `docs/specs/2026-10-28-science-commons-1b-design.md`
  (status: overlap half landed, commit), this plan's Status.

- [ ] **Step 1: Make the §6 amendments that do not describe retirement**, dated, in place,
  each marked *Amended <date> (milestone 1b plan, §<n>)* as 1a's were; and amend the
  framework design (`docs/specs/2026-08-31-command-framework-design.md` §4.4, the
  `sharing` class, and its dispatch and continuation guarantees for write reports) with
  Task 8's report contract: the dispatcher composes the complete ledger-backed pin prefix,
  the handler supplies an informational tail that science persists as a report sidecar
  under the operations root (absent meaning empty; historical commentary, whose loss
  loses the commentary and stales its cursor while every effect stays recoverable), and
  every page continues from the ledger-rebuilt report plus that tail. Amend `AGENTS.md`'s
  rule that the sharing registry is "the one science-owned state" to name the report
  sidecars as the second, presentation-only, science-owned state, with round 5's ruling
  and its cost (exact historical replay needs the sidecar retained beside the ledger).
- [ ] **Step 2: Run** `just gate`; Expected: `check` silent, suite passes. Note the test count on the task.
- [ ] **Step 3: Commit** — `git commit -am "docs(specs): commons amendments for milestone 1b's overlap half"`

---

### Task 13: The retirement door and reconcile (blocked on `beliefs-a989fb`)

**Files:**
- Modify: `python/src/science/commands/adopt.py` (steps 1 and 4), `python/src/science/sharing.py`
  (`apply_line` already folds `retired`; verify)
- Test: `python/tests/test_cmd_adopt.py`

**Interfaces:**
- Consumes (assumed; revise with the merged kernel design): `ScopedWriter.retire(corpus_id:
  str, *, evidence: SharingEvidence) -> SharingLine`, ledgering `retired`, idempotent when
  the corpus already carries a `retired` status under the session's actor; `World.status`.
- Produces: step 4's empty-`required` branch calls the door, records the line, writes the
  pin `retired`, emits the `retired` pin block with the `keep` list and the reopen remedy;
  step 1 calls the door for every `mounted` pin whose status is known and not live and not
  `departed`; the pending-door Finding is removed.

- [ ] Steps: failing tests (`test_an_unrequired_predecessor_is_retired_through_the_door_and_its_line_folds`,
  `test_reconcile_ledgers_a_retirement_the_kernel_committed_without_a_line`,
  `test_the_next_open_mounts_the_tip_only`), replacing Task 8's
  `test_an_unrequired_predecessor_reports_retirement_pending_before_the_door` and Task 9's
  `test_show_reports_pending_no_door_on_the_unkept_branch`; run to fail, implement, run,
  `just test-fast`, commit `feat(adopt): retire an unrequired predecessor through the kernel door`.

---

### Task 14: The retirement gates (blocked on Task 13)

**Files:**
- Modify: `python/tests/helpers/commons.py`, `python/tests/test_commons_1b.py`,
  `python/tests/test_cmd_adopt.py`

- [ ] **Step 1: Write the gates of §5.9**, one test each, against the fixtures Task 11 built
  plus branches this task adds: spec-drop; spec-only; late-link (both arrival orders, then
  P2′ adopted: P1 and P2′ retired); retry after a crash between mount and retirement;
  post-retirement sibling; late-kept predecessor (`chain-retired`); requirement-before-sweep
  (Q naming P1); chain retention; configured keep; stale configuration; the write guards
  (`verify` of *A*'s assessment and `publish`/`publish-preview` refused `corpus-retired`
  after an in-session retirement); `build_b_updated_unkept`'s retirement assertions.
- [ ] **Step 2: Run** `just test-one tests/test_commons_1b.py tests/test_cmd_adopt.py -v`, then `just test-fast`; Expected: PASS.
- [ ] **Step 3: Commit** — `git commit -am "test(commons): the retirement gates"`

---

### Task 15: Documents for the retirement tail

- [ ] **Step 1: Amend** commons §10's retirement paragraphs and §12's 1b paragraph, the 1b
  design's status, this plan's Status; remove the pending-door wording from `adopt`'s and
  `show`'s prompts.
- [ ] **Step 2: Run** `just gate`; note the test count on the task.
- [ ] **Step 3: Commit** — `git commit -am "docs(specs): commons amendments for milestone 1b's retirement tail"`

---

## Self-review

- **Spec coverage.** §5.1 → Task 2, 8; §5.2 → Task 3; §5.3 → no code (the design records
  it as a constraint; Task 12 amends commons §10); §5.4 → Task 4; §5.5 → Task 5; §5.6 →
  Task 6, 8, 9; §5.7 preflight, order, re-evaluation, `keep`, `config-stale` → Task 8;
  §5.7 rule 4 → Task 7; §5.7 write guards → Tasks 3, 10; §5.7 retirement call and reconcile
  → Task 13; §5.8 → Tasks 9, 10; §5.9 → Tasks 11, 14; §6 → Tasks 12, 15; §7 → the split
  at Task 12/13.
- **Step scan.** Tasks 13–15 are deliberately terser: their Interfaces are assumed and the
  Global Constraints say they are rewritten against the merged kernel design before Task
  13 starts.
- **Type consistency.** `Held`, `GroupKey`, `Outcome`, `Reason`, `Conflict` are defined
  once (Tasks 2, 6, 7) and consumed by name in Tasks 8 and 9; `explain`'s third argument
  is named in Task 4 and used by `belief.py`/`next.py` there.
- **Review Focus.** Five lines, each pinned to a task's test (1, 8, 6, 4, 6).
- **Proportion.** The plan is shorter than the design it implements.
