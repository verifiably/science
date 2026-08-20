# World Registry Slice 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the authoritative world-index core: the public `nodes` §11.1 canonical-text prerequisite, world-root initialization, corpus manifests and state identity, append-only registry admission/status, cut-6 N2 declarations, certified acceptance, and implementation close-out.

**Architecture:** `nodes` owns a versioned RFC 8785 serialization of its complete §11.1 projection in Python and TypeScript; Science parses that text directly into `Decimal` values and uniformly tags every JSON type before `science.identity.v1` hashing. Science keeps `atoms` confined to `science.root`, parameterizes the existing durable executor for corpus and world roots, and implements manifests, state identity, registry values/reduction, and the engine-free `World` API in `science.world`. Every mutation remains one `nodes` `WritePlan`, and every plan path enters the engine transaction's committed registered surface.

**Tech Stack:** Python 3.11+, TypeScript/Node 20+, Pydantic, Zod, PyYAML, RFC 8785/JCS, `nodes-core`, `atoms-core`, pytest, Vitest, Ruff, Pyright, Biome, and the existing N2 sabotage harness.

**Spec:** `docs/designs/2026-08-20-world-registry-design.md`; frozen acceptance authority: `docs/designs/2026-08-20-conformance-cut-6.md`. Read both completely before execution.

## Global Constraints

- Implement the `nodes` prerequisite and pass both-language gates before any Science code consumes it.
- `nodes` §11.1 projection text is RFC 8785 canonical JSON under version `projection.v1`; array order is preserved and object keys are recursively canonicalized.
- `nodes` exports projection value and text, but no Science digest. Science alone owns `science.node-content.v1`.
- Science parses canonical projection text with `parse_int=Decimal` and `parse_float=Decimal`; no binary float reaches `science.identity.v1`.
- The JSON lift tags every type uniformly: `null`, `boolean`, `number`, `string`, `array`, and `object`.
- An NFC key collision from `v1.encode` becomes `CorpusStateMalformed` with `KeyCollision` as `__cause__`.
- No `atoms` import outside `python/src/science/root.py`; `python/tests/test_capability_boundary.py` checks this.
- No mutable `nodes.Corpus` outside `python/src/science/corpus.py`; state identity reads through `ReadView.opened_at`.
- `science.world` never imports `atoms` and receives only a root-taking `WritePlanExecutor` factory.
- Every write-plan path becomes a `registered_path`; no second executor, interim writer, replay reader, or compatibility layer is added.
- The only corpus-manifest mutation is create-only fresh adoption. No fork constructor is built.
- Registry APIs append only. Exact content-named retries succeed; differing acts obey the frozen refusal order.
- Every registry read and mutation rescans the complete registry under the world-root lock.
- Missing configured manifests are non-carriers; malformed configured manifests refuse presence resolution.
- Cut 6 remains 14 selected + 8 labeled = 22 declaration units. The clarification commit `c309db9` changes no cut accounting.
- Portable tests make no durability claim. Certified durable arms run through `python/tools/cut6_acceptance.py` and error rather than skip off the certified tuple.
- Do not edit `python/tools/cut5_acceptance.py` or alter cut 5's meaning.
- Use conventional commits without attribution trailers. Stage only the named paths; never use `git add -A` or `git commit -a`.
- Nodes gates, from its `python/` and `ts/` directories respectively: `uv run --frozen pytest -q`, `uv run --frozen ruff check .`, `uv run --frozen pyright src`; `npm test`, `npm run typecheck`, `npm run check`.
- Science gates, from `python/`: `uv run --frozen pytest -q`, `uv run --frozen ruff check .`, `uv run --frozen pyright src`.

---

### Task 1: Ship `nodes` projection.v1 as canonical JSON text

**Repository:** `nodes` (execute in its own feature worktree and commit there before returning to Science).

**Files:**
- Modify: `docs/STANDARD.md`
- Modify: `docs/designs/2026-08-03-nodes-under-the-system-redesign-design.md`
- Modify: `python/pyproject.toml`, `python/uv.lock`
- Create: `python/src/nodes/core/projection.py`
- Modify: `python/tests/test_parity.py`, `python/tests/test_corpus_parity.py`, `python/tests/test_write_plan_parity.py`
- Delete: `python/tests/_canonical.py`
- Modify: `ts/package.json`, `ts/package-lock.json`, `ts/src/index.ts`
- Create: `ts/src/projection.ts`
- Modify: `ts/tests/parity.test.ts`, `ts/tests/corpus_parity.test.ts`, `ts/tests/write_plan_parity.test.ts`, `ts/tests/cross_parity.test.ts`
- Delete: `ts/tests/_canonical.ts`
- Create: `fixtures/projection.v1.canonical.json`

**Interfaces:**
- Produces Python: `PROJECTION_VERSION: Final[str] = "projection.v1"`; `to_canonical(node: Node) -> dict[str, object]`; `to_canonical_json(node: Node) -> str`.
- Produces TypeScript: `PROJECTION_VERSION = "projection.v1"`; `toCanonical(node: Node): JsonValue`; `toCanonicalJson(node: Node): string`.
- Produces contract: RFC 8785 text is the normative serialized form. The parsed accessor is convenience only.

- [ ] **Step 1: Amend the Tier-1 contract before code.** In `STANDARD.md` §11.1, retain the exact projection fields and add: version `projection.v1`; `to_canonical_json`/`toCanonicalJson` return RFC 8785 UTF-8 JSON text; non-finite numbers and values outside JSON refuse; object keys follow RFC 8785 UTF-16 ordering; arrays, including relations, preserve source order; any change to value or text is a major projection-version bump. Update §11.2 to name `fixtures/projection.v1.canonical.json` as the byte/text oracle and §12 to make projection-version stability explicit. Amend the dated redesign §2.1 from value-only to value-plus-canonical-text, recording Science's Decimal consumer and retaining Science's digest ownership. Mark only §2.1 landed in that design's status/verdict; keep reserved paths and recoverable construction outstanding. Grep nodes README/docs for the old test-helper-only claim and correct every live propagated status in this commit.

- [ ] **Step 2: Add dependency locks.** From `nodes/python`, run:

```bash
uv add 'rfc8785>=0.1.4,<0.2'
```

From `nodes/ts`, run:

```bash
npm install canonicalize@3.0.0
```

The selected packages are dependency-free implementations of RFC 8785; do not add another canonicalizer or a hashing package.

- [ ] **Step 3: Write the failing Python projection tests.** Move every test import from `tests._canonical` to `nodes.core.projection`. Add these checks to `python/tests/test_parity.py`:

```python
from nodes.core.projection import PROJECTION_VERSION, to_canonical, to_canonical_json

CANONICAL_TEXT = FIXTURES / "projection.v1.canonical.json"


def test_projection_version_and_text_are_public():
    assert PROJECTION_VERSION == "projection.v1"
    assert to_canonical_json(_node()) + "\n" == CANONICAL_TEXT.read_text(encoding="utf-8")


def test_projection_text_pins_number_spelling():
    node = _node().model_copy(deep=True)
    node.relations[0].weight = 1e16
    node.facets["numeric"] = {"small": 1e-7}
    text = to_canonical_json(node)
    assert '"weight":10000000000000000' in text
    assert '"small":1e-7' in text


def test_projection_text_rejects_non_finite_numbers():
    node = _node().model_copy(deep=True)
    node.relations[0].weight = float("inf")
    with pytest.raises(ValidationError, match="canonical JSON"):
        to_canonical_json(node)
```

Run `uv run --frozen pytest tests/test_parity.py -q`; expect collection failure because `nodes.core.projection` does not exist.

- [ ] **Step 4: Implement the Python API.** Create `python/src/nodes/core/projection.py` with the complete §11.1 value and the one JCS call:

```python
from __future__ import annotations

from typing import Final

import rfc8785

from nodes.core.errors import ValidationError
from nodes.core.node import Node

PROJECTION_VERSION: Final[str] = "projection.v1"


def to_canonical(node: Node) -> dict[str, object]:
    return {
        "id": node.id,
        "uid": node.uid,
        "kind": node.kind,
        "title": node.title,
        "body": node.body,
        "metadata": {
            "created": node.metadata.created.isoformat() if node.metadata.created else None,
            "updated": node.metadata.updated.isoformat() if node.metadata.updated else None,
            "version": node.metadata.version,
        },
        "relations": [
            {
                "source": relation.source,
                "predicate": relation.predicate,
                "target": relation.target,
                "directed": relation.directed,
                "weight": relation.weight,
                "attrs": relation.attrs,
            }
            for relation in node.relations
        ],
        "facets": node.facets,
        "deprecated_ids": node.deprecated_ids,
    }


def to_canonical_json(node: Node) -> str:
    try:
        return rfc8785.dumps(to_canonical(node)).decode("utf-8")
    except (rfc8785.CanonicalizationError, UnicodeError, TypeError, ValueError) as caught:
        raise ValidationError(f"node cannot be represented as projection.v1 canonical JSON: {caught}") from caught
```

Generate `fixtures/projection.v1.canonical.json` once from `to_canonical_json(node_from_markdown((FIXTURES / "gene_phf19.md").read_text(encoding="utf-8"))) + "\n"`; inspect and commit the literal oracle. Thereafter tests compare to the committed text and never regenerate it in the assertion.

- [ ] **Step 5: Write the failing TypeScript tests.** Replace private-helper imports with `../src/projection.js`. Add:

```typescript
import { PROJECTION_VERSION, toCanonical, toCanonicalJson } from "../src/projection.js";

it("exports projection.v1 canonical text", () => {
  expect(PROJECTION_VERSION).toBe("projection.v1");
  expect(`${toCanonicalJson(sourceNode())}\n`).toBe(readFileSync(join(FIXTURES, "projection.v1.canonical.json"), "utf-8"));
});

it("pins RFC 8785 number spelling", () => {
  const node = structuredClone(sourceNode());
  node.relations[0].weight = 1e16;
  node.facets.numeric = { small: 1e-7 };
  const text = toCanonicalJson(node);
  expect(text).toContain('"weight":10000000000000000');
  expect(text).toContain('"small":1e-7');
});

it("rejects non-finite numbers", () => {
  const node = structuredClone(sourceNode());
  node.relations[0].weight = Number.POSITIVE_INFINITY;
  expect(() => toCanonicalJson(node)).toThrow(ValidationError);
});
```

Run `npm test -- --run tests/parity.test.ts`; expect failure because the public module does not exist.

- [ ] **Step 6: Implement and export the TypeScript API.** Create `ts/src/projection.ts`:

```typescript
import canonicalize from "canonicalize";
import { ValidationError } from "./errors.js";
import type { Node } from "./node.js";

export const PROJECTION_VERSION = "projection.v1" as const;
export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };

export function toCanonical(node: Node): JsonValue {
  return {
    id: node.id,
    uid: node.uid,
    kind: node.kind,
    title: node.title,
    body: node.body,
    metadata: {
      created: node.metadata.created,
      updated: node.metadata.updated,
      version: node.metadata.version,
    },
    relations: node.relations.map((relation) => ({
      source: relation.source,
      predicate: relation.predicate,
      target: relation.target,
      directed: relation.directed,
      weight: relation.weight,
      attrs: relation.attrs as { [key: string]: JsonValue },
    })),
    facets: node.facets as { [key: string]: JsonValue },
    deprecated_ids: node.deprecatedIds,
  };
}

function assertJsonValue(value: unknown): asserts value is JsonValue {
  if (value === null || typeof value === "boolean" || typeof value === "string") return;
  if (typeof value === "number") {
    if (Number.isFinite(value)) return;
    throw new ValidationError("node cannot be represented as projection.v1 canonical JSON: non-finite number");
  }
  if (Array.isArray(value)) {
    for (const member of value) assertJsonValue(member);
    return;
  }
  if (typeof value === "object" && Object.getPrototypeOf(value) === Object.prototype) {
    for (const member of Object.values(value)) assertJsonValue(member);
    return;
  }
  throw new ValidationError(`node cannot be represented as projection.v1 canonical JSON: ${typeof value}`);
}

export function toCanonicalJson(node: Node): string {
  const value = toCanonical(node);
  assertJsonValue(value);
  try {
    const text = canonicalize(value);
    if (text === undefined) throw new Error("canonicalizer returned undefined");
    return text;
  } catch (caught) {
    throw new ValidationError(`node cannot be represented as projection.v1 canonical JSON: ${String(caught)}`);
  }
}
```

Export `PROJECTION_VERSION`, `JsonValue`, `toCanonical`, and `toCanonicalJson` from `ts/src/index.ts`. Delete both private helpers and update all callers to public imports; do not leave forwarding compatibility modules.

- [ ] **Step 7: Verify both languages and the exact shared text.** Run all six nodes gates. Confirm `git diff --check` and `git status --short` show only the named nodes files.

- [ ] **Step 8: Commit in nodes.** Stage the explicit paths and commit:

```bash
git commit -m "feat(projection): publish projection.v1 canonical JSON text"
```

Record the nodes commit id in the Science implementation results later; do not vendor or copy this API into Science.

---

### Task 2: Register every durable write-plan path and parameterize the executor

**Files:**
- Modify: `python/src/science/root.py`
- Modify: `python/tests/test_durable_executor.py`
- Modify: `python/tests/test_root.py`

**Interfaces:**
- Produces: `DurableExecutor(root: Path, *, backend: Backend, storage: StorageProfile, metadata_root: Path, consumer_tag: str, intent_domain: str, fulfills: str | None = None)`.
- Produces: `durable_executor_factory() -> Callable[[Path], DurableExecutor]` for corpus roots and private `_world_executor_factory()` for world roots.
- Guarantees: `registered_paths == tuple(dict.fromkeys(op.path for op in plan))` for every non-empty plan.

- [ ] **Step 1: Write the failing executor tests.** Replace the old assertion that `registered_paths == ()` and add:

```python
def test_every_plan_path_is_registered(tmp_path, submitted):
    executor(tmp_path).execute([
        CreateOp("corpus.yaml", b"manifest"),
        CreateOp("registry/a.yaml", b"record"),
    ])
    assert submitted[0][2].registered_paths == ("corpus.yaml", "registry/a.yaml")


def test_duplicate_plan_paths_register_once_in_first_occurrence_order(tmp_path, submitted):
    executor(tmp_path).execute([
        CreateOp(path="x", content=b"one"),
        ReplaceOp(path="x", content=b"two", expected_digest=sha256(b"one").hexdigest()),
    ])
    assert submitted[0][2].registered_paths == ("x",)


def test_world_executor_uses_world_consumer_and_intent_domains(tmp_path, submitted):
    root = tmp_path / "world"
    root.mkdir()
    _world_executor_factory()(root).execute([CreateOp("world.yaml", b"world")])
    spec = submitted[0][2]
    assert spec.consumer_tag == "science-world-write-v1"
    assert spec.intent_digest == "sha256:" + v1.digest(
        "science.world-write-intent.v1",
        [{"op": "create", "path": "world.yaml", "content_sha256": sha256(b"world").hexdigest()}],
    )
```

Run `uv run --frozen pytest tests/test_durable_executor.py tests/test_root.py -q`; expect failures on the empty registration tuple and missing world factory.

- [ ] **Step 2: Parameterize without adding another executor.** Add constants:

```python
WORLD_CONSUMER_TAG = "science-world-write-v1"
WORLD_INTENT_DOMAIN = "science.world-write-intent.v1"
```

Store `_consumer_tag` and `_intent_domain` on `DurableExecutor`; replace global uses in `build_spec` and `write_intent_digest` with those values. Update the existing `executor` test helper and `DurableOperationPort.execute_fulfilling` constructor call to pass `CONSUMER_TAG` and `INTENT_DOMAIN`. Keep `write_intent_digest(plan)` as the corpus public helper, and add private `_write_intent_digest(plan, domain)` used by the executor. Set:

```python
registered_paths = tuple(dict.fromkeys(operation.path for operation in plan))
```

Pass that tuple to `build_spec`. Do not register derived parent directories because they are effects, not authored plan paths.

- [ ] **Step 3: Keep the two factories as stable module-level callables.** `_durable_executor` binds corpus constants. `_world_executor` binds world constants. `durable_executor_factory()` and `_world_executor_factory()` return those function objects, not new closures, retaining the existing corpus-root factory pattern.

- [ ] **Step 4: Verify.** Run the two focused modules, then the full portable Science suite, Ruff, and Pyright.

- [ ] **Step 5: Commit.** Stage the three files and commit:

```bash
git commit -m "feat(root): register every durable plan path"
```

---

### Task 3: Add the closed corpus manifest, fresh adoption, and corpus finding

**Files:**
- Create: `python/src/science/world.py`
- Modify: `python/src/science/errors.py`
- Modify: `python/src/science/corpus.py`
- Create: `python/tests/fixtures_cut6.py`
- Create: `python/tests/test_manifest.py`
- Modify: `python/tests/test_corpus_write.py`

**Interfaces:**
- Produces: `CorpusManifest`, `ForkedFrom`, `load_manifest(Path)`, `manifest_projection(CorpusManifest)`, `manifest_bytes(CorpusManifest)`.
- Produces: `CorpusWriter.adopt_manifest(*, profile: CorpusPins) -> CorpusManifest`.
- Adds errors: `ManifestMalformed`, `ManifestAlreadyPresent`, `ManifestMissing`, `CorpusStateMalformed`, `WorldIdMismatch`, `WorldUninitialized`, `ProvenanceMismatch`, `ForkParentUnknown`, `CorpusIdKnown`, `StatusTargetUnknown`, `StatusTerminal`, `RegistryMalformed`.

Add each refusal directly under `ScienceError`; the names are the public distinction, and this slice needs no speculative intermediate error families.

- [ ] **Step 1: Create exact shared fixtures.** `fixtures_cut6.py` defines only constants and constructors used by two or more modules:

```python
from science.consulted import CorpusPins

SCIENCE_ID = "science:" + "a" * 64
BIOLOGY_ID = "biology:" + "b" * 64
PINS = CorpusPins(science_contract=SCIENCE_ID, domains={"biology": BIOLOGY_ID})


def manifest_document(corpus_id: str = "1" * 32) -> str:
    return (
        "manifest_version: 2\n"
        f"corpus_id: {corpus_id}\n"
        "profile:\n"
        f"  science_contract: {SCIENCE_ID}\n"
        "  domains:\n"
        f"    biology: {BIOLOGY_ID}\n"
    )
```

- [ ] **Step 2: Write loader/projection failures first.** In `test_manifest.py`, cover: missing file → `ManifestMissing`; accepted fresh and fork shapes; wrong version; unknown fields at root/profile/fork levels; duplicate `domains` key; uppercase/wrong-length ids; malformed contract identities; a `science` domains key; domain key/prefix disagreement; formatting and mapping-order invariance. Pin this projection:

```python
assert manifest_projection(manifest) == {
    "manifest_version": 2,
    "corpus_id": "1" * 32,
    "profile": {
        "science_contract": SCIENCE_ID,
        "domains": {"biology": BIOLOGY_ID},
    },
}
```

For a fork, assert the optional member is exactly:

```python
{"corpus_id": "2" * 32, "corpus_state": "3" * 64}
```

Run `uv run --frozen pytest tests/test_manifest.py -q`; expect collection failure because `science.world` does not exist.

- [ ] **Step 3: Implement one strict YAML loader in `science.world`.** Use a private `yaml.SafeLoader` subclass whose mapping constructor rejects a repeated key before constructing the dict. Wrap file I/O, YAML, type, duplicate-key, and validation failures as `ManifestMalformed`, except `FileNotFoundError` which becomes `ManifestMissing`. Validate exact dict types and closed key sets. Use `[a-z][a-z0-9-]*` namespaces, `science:<64 lowerhex>` for the base identity, `<domain>:<64 lowerhex>` for domain identities, 32 lowerhex corpus ids, 64 lowerhex state ids, and exact integer version 2 with booleans refused as integers.

Define immutable values:

```python
@dataclass(frozen=True)
class ForkedFrom:
    corpus_id: str
    corpus_state: str


@dataclass(frozen=True)
class CorpusManifest:
    manifest_version: Literal[2]
    corpus_id: str
    profile: CorpusPins
    forked_from: ForkedFrom | None = None
```

`manifest_projection` copies `CorpusPins.domains` from its `MappingProxyType` into an ordinary key-sorted `dict` and omits `forked_from` when absent. `manifest_bytes` uses `yaml.safe_dump(projection, sort_keys=True, allow_unicode=True).encode("utf-8")` so authored bytes are stable but identity remains projection-level.

- [ ] **Step 4: Write fresh-adoption and corpus-check failures.** Add to `test_corpus_write.py` using its recording executor:

```python
def test_adopt_manifest_mints_and_executes_one_create(writer):
    manifest = writer.adopt_manifest(profile=PINS)
    assert re.fullmatch(r"[0-9a-f]{32}", manifest.corpus_id)
    assert manifest.forked_from is None
    assert Recorder.plans[-1] == [CreateOp("corpus.yaml", manifest_bytes(manifest))]
    assert load_manifest(writer.read_view._corpus.store.root) == manifest


def test_adopt_manifest_never_remints(writer):
    first = writer.adopt_manifest(profile=PINS)
    with pytest.raises(ManifestAlreadyPresent):
        writer.adopt_manifest(profile=PINS)
    assert load_manifest(writer.read_view._corpus.store.root) == first
```

Add to `test_manifest.py`: malformed present manifest produces one `Finding(severity="error", code="manifest-malformed", ref="corpus.yaml", detail=<message>)`; absent manifest produces none.

- [ ] **Step 5: Implement adoption under the existing operation lock.** In `CorpusWriter.adopt_manifest`, import manifest helpers locally from `science.world` to avoid a module cycle. While holding `self._operation`: validate the profile by round-tripping it through the manifest validator; refuse any existing path at `corpus.yaml`; construct `CorpusManifest(2, secrets.token_hex(16), profile)`; execute `[CreateOp("corpus.yaml", manifest_bytes(manifest))]` through `self._state.executor_factory(self._corpus.store.root)`; return the manifest. Do not call `nodes.Corpus.add` for a non-node file.

At the start of `corpus_check`, inspect `<root>/corpus.yaml`: absence adds nothing; `load_manifest` success adds nothing; `ManifestMalformed` adds the exact finding and continues checking stored nodes. Do not catch `ManifestMissing` after an existence check.

- [ ] **Step 6: Verify and commit.** Run `test_manifest.py`, `test_corpus_write.py`, the full portable suite, Ruff, and Pyright. Commit:

```bash
git commit -m "feat(corpus): add closed manifests and fresh adoption"
```

---

### Task 4: Compute corpus-state identity through the uniform JSON lift

**Files:**
- Modify: `python/src/science/world.py`
- Create: `python/tests/test_corpus_state.py`

**Interfaces:**
- Consumes nodes: `to_canonical_json(node: Node) -> str` from Task 1.
- Produces Science: `corpus_state_identity(corpus_root: Path) -> str`.
- Private helper: `_lift_json(value: object) -> object`, accepting only values returned by `json.loads` configured with `parse_int=Decimal` and `parse_float=Decimal`.

- [ ] **Step 1: Write the JSON-lift tests before the implementation.** Use `v1.encode(_lift_json(value))` as the observable bytes and cover every tag, including the marker-collision case:

```python
def test_json_lift_tags_every_type_uniformly():
    value = json.loads(
        '{"n":null,"b":true,"i":1,"d":1.25,"s":"x","a":[null],"o":{"null":null}}',
        parse_int=Decimal,
        parse_float=Decimal,
    )
    assert _lift_json(value) == [
        "object",
        {
            "n": ["null"],
            "b": ["boolean", True],
            "i": ["number", Decimal("1")],
            "d": ["number", Decimal("1.25")],
            "s": ["string", "x"],
            "a": ["array", [["null"]]],
            "o": ["object", {"null": ["null"]}],
        },
    ]


def test_authored_null_marker_object_does_not_collide_with_null():
    assert v1.encode(_lift_json({"tag": "null"})) != v1.encode(_lift_json(None))


def test_lift_preserves_array_order():
    assert v1.encode(_lift_json([1, 2])) != v1.encode(_lift_json([2, 1]))
```

Add a parser test that patches `to_canonical_json` to return `'{"n":1e+16,"m":1e-7}'`, spies on `_lift_json`, and asserts it receives `Decimal("1E+16")` and `Decimal("1E-7")`, never `float`.

- [ ] **Step 2: Write state-identity failures.** Build roots with the real nodes default executor; every recomputation reopens through the production read facade. Use these helpers and names, extending the same concrete pattern for the manifest and git cases:

```python
def _state_root(tmp_path, node):
    root = tmp_path / "corpus"
    root.mkdir()
    manifest = CorpusManifest(2, "1" * 32, PINS)
    (root / "corpus.yaml").write_bytes(manifest_bytes(manifest))
    Corpus(root).add(node)
    return root


def _replace(root, node):
    Corpus(root).add(node)
    return corpus_state_identity(root)


def test_node_content_and_produces_relations_move_state_while_semantic_identity_stands(tmp_path):
    run = stored.run_node("state", title="state", spec="analysis-spec:s1", produces=("dataset:a",))
    root = _state_root(tmp_path, run)
    semantic = stored.stored_semantic_hash(run)
    states = [corpus_state_identity(root)]
    body_edit = run.model_copy(update={"body": "changed"})
    states.append(_replace(root, body_edit))
    removed = body_edit.model_copy(update={"relations": []})
    states.append(_replace(root, removed))
    added = removed.model_copy(update={"relations": [
        Relation(source=run.id, predicate=stored.PRODUCES, target="dataset:b")
    ]})
    states.append(_replace(root, added))
    retargeted = added.model_copy(update={"relations": [
        Relation(source=run.id, predicate=stored.PRODUCES, target="dataset:c")
    ]})
    states.append(_replace(root, retargeted))
    assert len(set(states)) == len(states)
    assert {stored.stored_semantic_hash(node) for node in (run, body_edit, removed, added, retargeted)} == {semantic}


def test_relation_reordering_moves_state(tmp_path):
    run = stored.run_node(
        "ordered", title="ordered", spec="analysis-spec:s1", produces=("dataset:a", "dataset:b")
    )
    root = _state_root(tmp_path, run)
    before = corpus_state_identity(root)
    reversed_run = run.model_copy(update={"relations": list(reversed(run.relations))})
    assert _replace(root, reversed_run) != before


def test_filesystem_and_formatting_changes_are_inert(tmp_path):
    run = stored.run_node("inert", title="inert", spec="analysis-spec:s1")
    root = _state_root(tmp_path, run)
    expected = corpus_state_identity(root)
    original = Corpus(root).store.path_for(run.id)
    renamed = root / "renamed" / original.name
    renamed.parent.mkdir()
    original.rename(renamed)
    (root / "editor.txt").write_text("one\n", encoding="utf-8")
    (root / "editor.txt").write_text("two\n\n", encoding="utf-8")
    parsed = yaml.safe_load((root / "corpus.yaml").read_text(encoding="utf-8"))
    (root / "corpus.yaml").write_text(yaml.safe_dump(parsed, default_flow_style=True), encoding="utf-8")
    for path in root.rglob("*"):
        os.utime(path, None)
    assert corpus_state_identity(root) == expected
```

`test_every_semantic_manifest_member_moves_state` rewrites one valid member at a time from the original bytes—base identity, one domain identity, corpus id, then `forked_from`—and asserts four digests distinct from baseline. `test_manifest_damage_refuses_before_digesting` writes the exact unknown-field, duplicate-domain-key, and malformed-identity YAML inputs from `test_manifest.py` and asserts `ManifestMalformed` for each. `test_git_is_not_an_identity_member` first computes outside git; then initializes a repository with an empty commit, changes the still-untracked node through `Corpus.add`, asserts state moves while `git rev-parse HEAD` does not, commits the resulting files without changing them again, and asserts the new HEAD leaves state fixed.

Also test `ManifestMissing` directly and verify a malformed node, duplicate uid, projection failure, JSON failure, and lift failure each raise `CorpusStateMalformed` with the original exception as `__cause__`.

For the NFC collision, patch `to_canonical_json` to return `'{"e\\u0301":1,"\\u00e9":2}'`; assert `CorpusStateMalformed.__cause__` is `KeyCollision`.

Run `uv run --frozen pytest tests/test_corpus_state.py -q`; expect import failures for `_lift_json` and `corpus_state_identity`.

- [ ] **Step 3: Implement the exact uniform lift.** Put the `bool` branch before `Decimal` and refuse anything else:

```python
def _lift_json(value: object) -> object:
    if value is None:
        return ["null"]
    if type(value) is bool:
        return ["boolean", value]
    if isinstance(value, Decimal):
        return ["number", value]
    if type(value) is str:
        return ["string", value]
    if type(value) is list:
        return ["array", [_lift_json(member) for member in value]]
    if type(value) is dict:
        lifted: dict[str, object] = {}
        for key, member in value.items():
            if type(key) is not str:
                raise TypeError(f"JSON object key {key!r} is not a string")
            lifted[key] = _lift_json(member)
        return ["object", lifted]
    raise TypeError(f"{type(value).__name__} is not a JSON value")
```

Parse projection text with:

```python
def _reject_json_constant(value: str) -> NoReturn:
    raise ValueError(f"non-standard JSON constant {value!r}")


json.loads(
    projection_text,
    parse_int=Decimal,
    parse_float=Decimal,
    parse_constant=_reject_json_constant,
)
```

Do not implement `Decimal(str(float))`; the selected nodes API is text-shaped.

- [ ] **Step 4: Implement the state formula through the read facade.** `corpus_state_identity` first loads the manifest. It then opens `ReadView.opened_at(root)`, iterates `iter_stored()`, calls `to_canonical_json`, parses and lifts, and computes:

```python
node_identity = v1.digest("science.node-content.v1", lifted)
members.append({"uid": node.uid, "content_identity": node_identity})
projection = {
    "manifest": manifest_projection(manifest),
    "nodes": sorted(members, key=lambda member: member["uid"]),
}
return v1.digest("science.corpus-state.v1", projection)
```

Wrap nodes parse/collision errors, projection errors, JSON errors, lift errors, and `IdentityError` from the node-content digest in `CorpusStateMalformed` with the original exception as `__cause__`. `ReadView.opened_at` already refuses duplicate uids while constructing the nodes index, so do not add a second duplicate scan. Leave `ManifestMissing` and `ManifestMalformed` unwrapped. Outer corpus digest errors are programming errors because its projection is Science-authored and admissible.

- [ ] **Step 5: Verify and commit.** Run the focused module, full portable suite, Ruff, and Pyright. Commit:

```bash
git commit -m "feat(world): derive corpus-state identity from complete node projections"
```

---

### Task 5: Initialize and open the second engine-root kind

**Files:**
- Modify: `python/src/science/world.py`
- Modify: `python/src/science/root.py`
- Modify: `python/tests/test_root.py`
- Create: `python/tests/test_world.py`

**Interfaces:**
- Produces: immutable `WorldConfig(world_root: Path, world_id: str, corpus_roots: tuple[Path, ...])`.
- Produces root API: `WORLD_GENESIS_DOMAIN`, `WORLD_CONSUMER_TAG`, `init_world_root(config) -> None`, `open_world(config) -> World`.
- Produces mirror helpers in `science.world`: `_world_mirror_bytes(world_id: str) -> bytes`; `_load_world_mirror(root: Path) -> str`.
- `World` constructor remains engine-free: `World(config: WorldConfig, executor_factory: Callable[[Path], WritePlanExecutor])`.

- [ ] **Step 1: Write config and mirror tests.** In `test_world.py`:

```python
def test_world_config_resolves_paths_and_deduplicates_no_roots(tmp_path):
    root = tmp_path / "a" / ".." / "world"
    corpus = tmp_path / "corpus"
    config = WorldConfig(root, "1" * 32, (corpus, corpus / "."))
    assert config.world_root == root.resolve()
    assert config.corpus_roots == (corpus.resolve(), corpus.resolve())


@pytest.mark.parametrize("world_id", ["", "A" * 32, "a" * 31, "g" * 32])
def test_world_config_refuses_malformed_id(tmp_path, world_id):
    with pytest.raises(ValueError, match="world_id"):
        WorldConfig(tmp_path, world_id, ())


def test_world_mirror_loader_requires_a_valid_file(tmp_path):
    with pytest.raises(WorldUninitialized):
        _load_world_mirror(tmp_path)
    (tmp_path / "world.yaml").write_text("world_id: " + "2" * 32 + "\n")
    assert _load_world_mirror(tmp_path) == "2" * 32
```

The public `open_world` engine tests belong in `test_root.py`; use monkeypatching there to avoid a certified-volume claim in portable tests.

- [ ] **Step 2: Add the immutable config and mirror parser.** `WorldConfig.__post_init__` requires exact `Path`-coercible inputs, validates 32 lowerhex, resolves the world and each corpus root without deduplicating the caller's tuple, and writes the normalized values with `object.__setattr__`. `_load_world_mirror` uses the same duplicate-key-aware closed YAML discipline as manifests; absence or malformed shape raises `WorldUninitialized`, while a valid mirror with a different id is compared by `World`/`open_world` and raises `WorldIdMismatch`.

- [ ] **Step 3: Write root-init failures.** In `test_root.py`, patch `register_root` and `_world_executor_factory` with one local helper that records registration and applies only the create plans needed by these tests:

```python
def patch_world_engine(monkeypatch, calls):
    def record_registration(_backend, _project_root, _metadata_root, _storage, payload, _surface):
        calls.append(("register", payload))

    class Recorder:
        def __init__(self, world_root):
            self.root = world_root

        def execute(self, plan):
            calls.append(("execute", plan))
            for operation in plan:
                assert isinstance(operation, CreateOp)
                target = self.root / operation.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(operation.content)

    monkeypatch.setattr(root, "register_root", record_registration)
    monkeypatch.setattr(root, "_world_executor_factory", lambda: lambda world_root: Recorder(world_root))


def test_init_world_registers_genesis_then_creates_mirror(monkeypatch, tmp_path):
    calls = []
    patch_world_engine(monkeypatch, calls)
    config = WorldConfig(tmp_path / "world", "1" * 32, ())
    init_world_root(config)
    assert calls[0] == (
        "register",
        v1.encode({"domain": "science.world-root.v1", "world_id": "1" * 32}),
    )
    assert calls[1] == ("execute", [CreateOp("world.yaml", _world_mirror_bytes("1" * 32))])


def test_init_world_exact_mirror_retry_executes_no_transaction(monkeypatch, tmp_path):
    calls = []
    patch_world_engine(monkeypatch, calls)
    config = WorldConfig(tmp_path / "world", "1" * 32, ())
    init_world_root(config)
    calls.clear()
    init_world_root(config)
    assert [kind for kind, _value in calls] == ["register"]
```

Also cover non-directory root refusal, malformed mirror, mirror mismatch, `open_world` success, and the constant consumer tag.

Add a portable layout test through the recorder: after init, `world.yaml` exists while `registry/`, `epochs/`, and `rules/` do not. It makes no claim about `.#~chain/`, which only the real engine creates. The certified fixture in Task 7 asserts that chain path; after its first admission, only `registry/` joins the authored layout while `epochs/` and `rules/` remain absent.

- [ ] **Step 4: Implement root wiring.** Add the constant and private payload function:

```python
WORLD_GENESIS_DOMAIN = "science.world-root.v1"


def _world_genesis_payload(world_id: str) -> bytes:
    return v1.encode({"domain": WORLD_GENESIS_DOMAIN, "world_id": world_id})
```

`init_world_root` validates before `mkdir`, registers with empty genesis baseline, then: absent mirror → one create-only plan through `_world_executor_factory`; present mirror → load and compare, exact success returns, mismatch raises. `open_world` loads and compares the mirror and returns `World(config, _world_executor_factory())`; it never calls `register_root`.

- [ ] **Step 5: Add separate world-root state.** In `science.world`:

```python
@dataclass
class _WorldState:
    lock: threading.Lock
    registry: RegistryView
```

Use `_WORLD_STATES` and `_WORLD_STATES_LOCK`, keyed by resolved world-root string. `World` holds its supplied executor factory directly; the shared state contains only the lock and cached registry view named by the design. The initial `RegistryView` is empty; Task 6 replaces it on every rescan. Do not store a `nodes.Corpus` here.

- [ ] **Step 6: Verify and commit.** Run focused tests, full portable suite, capability-boundary test, Ruff, and Pyright. Commit:

```bash
git commit -m "feat(root): initialize and open durable world roots"
```

---

### Task 6: Implement append-only registry admission, status, and presence

**Files:**
- Modify: `python/src/science/world.py`
- Create: `python/tests/test_world_registry.py`

**Interfaces:**
- Produces provenance values: `Fresh`, `ReplicaOf(parent_corpus_id: str)`, `ForkOf(parent_corpus_id: str, parent_corpus_state: str)` and union `AdmissionProvenance`.
- Produces record values: `AdmissionRecord`, `StatusRecord`, immutable `RegistryView(admissions, statuses)`, and `CorpusStatus(known, live, present, findings)`.
- Produces `World.registry()`, `World.status(corpus_id)`, `World.admit(corpus_root, *, provenance, actor)`, `World.retire(corpus_id, *, actor)`, `World.depart(corpus_id, *, actor)`.
- Private pure reducer: `_reduce_status(config: WorldConfig, view: RegistryView, corpus_id: str) -> CorpusStatus`, which makes record-order invariance directly testable.

- [ ] **Step 1: Pin the record projections and content names.** Write tests asserting exact values:

```python
assert admission_projection(record) == {
    "record_kind": "admission",
    "corpus_id": manifest.corpus_id,
    "manifest": manifest_projection(manifest),
    "provenance": {"kind": "fresh"},
    "actor": "alice",
}
assert admission_digest(record) == v1.digest("science.world-admission.v1", admission_projection(record))

assert status_projection(record) == {
    "record_kind": "status",
    "corpus_id": manifest.corpus_id,
    "status": "retired",
    "actor": "alice",
}
assert status_digest(record) == v1.digest("science.world-status.v1", status_projection(record))
```

Replica provenance is `{"kind": "replica-of", "parent_corpus_id": id}`. Fork provenance additionally carries `parent_corpus_state`. Test projection-level validity by rewriting one registry YAML file with different whitespace at the same digest path and asserting the registry still loads.

- [ ] **Step 2: Implement immutable record values and one strict registry loader.** All record constructors validate ids and require actors to be exact strings accepted by `v1.encode`; do not invent an actor vocabulary or non-emptiness rule absent from the design. Serialize with sorted safe YAML. `_scan_registry(root)` returns empty if `registry/` is absent; otherwise every direct member must be a regular `*.yaml` file. Parse with duplicate-key rejection, validate the exact closed shape selected by `record_kind`, reconstruct the value, recompute the kind-specific digest, and require `path.name == f"{digest}.yaml"`. Wrap any failure as `RegistryMalformed` with its cause. Return admissions and statuses sorted by their content digest, never directory iteration order.

- [ ] **Step 3: Write admission refusal-order tests.** Cover all three provenances and the exact order:

```python
def test_exact_admission_retry_is_success_without_second_file(world, fresh_corpus):
    first = world.admit(fresh_corpus, provenance=Fresh(), actor="alice")
    second = world.admit(fresh_corpus, provenance=Fresh(), actor="alice")
    assert second == first
    assert len(tuple((world.config.world_root / "registry").iterdir())) == 1


def test_known_id_refuses_fresh_and_replica_provenance(world, fresh_corpus):
    manifest = load_manifest(fresh_corpus)
    world.admit(fresh_corpus, provenance=Fresh(), actor="alice")
    for provenance in (Fresh(), ReplicaOf(manifest.corpus_id)):
        with pytest.raises(CorpusIdKnown):
            world.admit(fresh_corpus, provenance=provenance, actor="bob")


def test_fork_provenance_requires_exact_manifest_and_known_parent(world, fork_fixture):
    with pytest.raises(ForkParentUnknown):
        world.admit(fork_fixture.root, provenance=fork_fixture.provenance, actor="alice")
    world.admit(fork_fixture.parent, provenance=Fresh(), actor="alice")
    assert world.admit(fork_fixture.root, provenance=fork_fixture.provenance, actor="alice")
```

Also assert: Fresh against a fork manifest → `ProvenanceMismatch`; ReplicaOf against a fork manifest → mismatch; replica parent must equal the retained manifest id; ForkOf's two parent facts must exactly match `forked_from`; malformed manifest wins before exact retry; provenance mismatch wins before known-id refusal; no refused call creates a file.

- [ ] **Step 4: Implement admission in the normative order.** While holding `self._state.lock`: rescan and replace the cached view; load manifest; validate provenance; build candidate and path; exact existing path returns the loaded matching record; any admission for id → `CorpusIdKnown`; unknown fork parent → `ForkParentUnknown`; execute one `CreateOp`; rescan and return the committed record. The post-write rescan ensures the returned cache represents disk and does not authorize from planned state.

- [ ] **Step 5: Write and implement terminal status.** Tests cover unknown target, exact retry, other terminal status, same status/different actor, and no file on refusal. Implement one private `_terminal(corpus_id, status, actor)` used by `retire` and `depart`: rescan; require known; build candidate; exact file success; any existing terminal for id → `StatusTerminal`; append; rescan; return. No public reset, purge, replace, delete, or un-retire method exists.

- [ ] **Step 6: Write computed-status and rescan tests.** Cover all combinations of `known`, `live`, and `present`; missing configured root manifest as non-carrier; malformed configured manifest refusal; resolved-root deduplication; duplicate carriers; raw registry arrival between reads; status invariance under raw file creation order; replica restoration with unchanged registry; and raw admission deletion remaining undetected.

Pin the duplicate finding:

```python
assert status.present is False
assert [(f.severity, f.code, f.ref) for f in status.findings] == [
    ("error", "duplicate-carrier", corpus_id)
]
assert status.findings[0].detail == "carriers=" + ",".join(sorted((str(a.resolve()), str(b.resolve()))))
```

- [ ] **Step 7: Implement read reduction.** `registry()` acquires the lock, rescans, stores, and returns the immutable view. `status()` does the same, then calculates `known = any(admission.corpus_id == id)`, `live = known and not any(status.corpus_id == id for status in statuses)`. Resolve and deduplicate configured roots; `ManifestMissing` continues, `ManifestMalformed` propagates, matching manifests become carriers. Exactly one carrier means present; zero means absent; more than one means absent plus the finding. Do not catch registry errors or convert them to findings.

- [ ] **Step 8: Add append-only surface and malformed-store tests.** Assert the public `World` callables are exactly `admit`, `depart`, `registry`, `retire`, `status` plus ordinary object methods; assert no purge/delete/replace/reset spelling. For each malformed registry case—foreign file, directory, duplicate key, unknown field, wrong record kind, invalid id, wrong digest filename—both `registry()` and `status()` raise `RegistryMalformed` and skip nothing.

- [ ] **Step 9: Verify and commit.** Run `test_world_registry.py`, all world/manifest/state tests, the full portable suite, Ruff, and Pyright. Commit:

```bash
git commit -m "feat(world): append admissions and terminal status records"
```

---

### Task 7: Declare and sabotage exactly the 22 frozen cut-6 units

**Files:**
- Create: `python/tests/n2_arms_cut6.py`
- Create: `python/tests/acceptance/test_n2_cut6.py`
- Modify: `python/tests/test_n2.py`

**Interfaces:**
- Produces: `CUT6_ARMS: tuple[Arm, ...]` with exactly 22 entries.
- Consumes: one existing test function per `checks` node id; every node id resolves alone and fails under its exact sabotage.
- Preserves: the existing `audit`, `baseline`, and five malformed-arm verdicts without copying the harness.

- [ ] **Step 1: Give every frozen unit one exact test function.** Reuse the focused tests from Tasks 3–6, renaming where necessary to these stable node ids:

| unit | row | check |
|---|---|---|
| append-only public surface | X4 | `test_world_registry.py::test_world_public_surface_has_no_registry_mutator` |
| raw deletion undetected | X4 | `test_world_registry.py::test_raw_admission_deletion_is_undetected` |
| known id refuses, including replica-of | X5 | `test_world_registry.py::test_known_id_refuses_fresh_and_replica_provenance` |
| retired cannot return live | X6 | `test_world_registry.py::test_retired_corpus_has_no_return_to_live_act` |
| replica restoration changes presence only | X6 | `test_world_registry.py::test_replica_restoration_recomputes_presence_without_admission` |
| record-order invariance | X6 | `test_world_registry.py::test_status_reduction_is_record_order_invariant` |
| opaque stable fresh identity | W13 | `test_manifest.py::test_fresh_id_is_opaque_and_survives_root_moves_and_reclones` |
| no ordinary remint | W13 | `test_manifest.py::test_existing_manifest_refuses_remint` |
| node content/produces movement | W13 | `test_corpus_state.py::test_node_content_and_produces_relations_move_state_while_semantic_identity_stands` |
| relation reorder movement | W13 | `test_corpus_state.py::test_relation_reordering_moves_state` |
| filesystem/format invariance | W13 | `test_corpus_state.py::test_filesystem_and_formatting_changes_are_inert` |
| semantic manifest movement | W13 | `test_corpus_state.py::test_every_semantic_manifest_member_moves_state` |
| malformed manifest refusal | W13 | `test_corpus_state.py::test_manifest_damage_refuses_before_digesting` |
| git independence | W13 | `test_corpus_state.py::test_git_is_not_an_identity_member` |
| exact admission retry | labeled:admission-idempotency | `test_world_registry.py::test_exact_admission_retry_is_success_without_second_file` |
| exact/differing status retry | labeled:status-idempotency | `test_world_registry.py::test_status_retry_is_idempotent_and_differing_terminal_acts_refuse` |
| initialization retry | labeled:initialization-idempotency | `acceptance/test_n2_cut6.py::test_world_initialization_recovers_between_genesis_and_mirror` |
| mirror registration evidence | labeled:durable-mirror | `acceptance/test_n2_cut6.py::test_world_mirror_registration_names_world_yaml` |
| manifest registration evidence | labeled:durable-manifest | `acceptance/test_n2_cut6.py::test_manifest_registration_names_corpus_yaml` |
| registry registration evidence | labeled:durable-registry | `acceptance/test_n2_cut6.py::test_registry_registrations_name_each_record_path` |
| duplicate-carrier finding | labeled:duplicate-carrier | `test_world_registry.py::test_duplicate_carriers_are_a_distinct_finding` |
| manifest-malformed finding | labeled:manifest-malformed | `test_manifest.py::test_corpus_check_distinguishes_malformed_from_absent_manifest` |

- [ ] **Step 2: Add certified fixtures and durable checks.** In `acceptance/test_n2_cut6.py`, reuse `work_directory` from `acceptance/conftest.py`. Allocate unique world/corpus roots with pid plus a counter, initialize through the real composition root, and clean both roots plus both metadata siblings in `finally`/fixture teardown. Reuse `chain_entries` from `test_durable_families.py`; committed evidence is the `RegisteredEntry.final` mapping, not a claimed replay.

In that fixture, assert the real initialized root contains `world.yaml` and `.#~chain/` but no empty `registry/`, `epochs/`, or `rules/`; after the first admission, assert `registry/` alone has materialized.

The three evidence assertions are:

```python
assert "world.yaml" in dict(registration.final)
assert "corpus.yaml" in dict(registration.final)
assert set(dict(registration.final)) == {f"registry/{admission_digest}.yaml"}
assert set(dict(status_registration.final)) == {f"registry/{status_digest}.yaml"}
```

For the crash seam, monkeypatch `root.DurableExecutor.execute` to raise once before executing the mirror plan, assert registration left `.#~chain` but no mirror, restore the method, retry the same config, and then retry once more as a no-op. Finally call `init_world_root` with a different `world_id` and assert the engine raises `PreconditionRefused`.

- [ ] **Step 3: Declare the exact sabotages in `n2_arms_cut6.py`.** Use the standing `Arm` and `Sabotage` values. The 22 source mutations are fixed as follows; the implementation tasks must retain these small, unique source strings or update the declaration and immediately rerun its stale check:

| row | source mutation |
|---|---|
| X4 surface | insert a public `purge()` immediately before `World.registry()` |
| X4 deletion | after registry directory enumeration, raise `RegistryMalformed` when the directory is empty |
| X5 known | change the known-id admission guard to `if False:` |
| X6 terminal | use the same known-id guard mutation; the post-retirement re-admission in its dedicated test must then succeed |
| X6 replica | change `present = len(carriers) == 1` to `present = False` |
| X6 order | change `live = known and not any(record.corpus_id == corpus_id for record in view.statuses)` to `live = known and (not view.statuses or view.statuses[-1].corpus_id != corpus_id)` |
| W13 opaque | change `secrets.token_hex(16)` to the constant `"0" * 32` |
| W13 remint | change the `corpus.yaml` existence guard to `if False:` |
| W13 content/relations | remove `relations` from the parsed node projection immediately before `_lift_json` |
| W13 relation order | sort list members by `repr` in `_lift_json` instead of preserving order |
| W13 invariance | add raw `corpus.yaml` text to the outer state projection |
| W13 manifest movement | replace the complete manifest projection with only `{"corpus_id": manifest.corpus_id}` |
| W13 malformed | disable the unknown-field branch in the closed-field validator |
| W13 git | add `git rev-parse HEAD` output to the outer projection using an inline `subprocess.check_output` import |
| labeled admission retry | disable only the exact-existing admission-file success branch |
| labeled status retry | disable only the exact-existing status-file success branch |
| labeled initialization retry | replace the exact mirror-match return with `raise WorldIdMismatch` |
| labeled durable mirror | filter `world.yaml` from the computed registered-path tuple |
| labeled durable manifest | filter `corpus.yaml` from the computed registered-path tuple |
| labeled durable registry | filter paths beginning `registry/` from the computed registered-path tuple |
| labeled duplicate carrier | disable the `len(carriers) > 1` finding branch |
| labeled manifest malformed | replace the `ManifestMalformed` corpus-check append block with `pass` |

The order-invariance check calls `_reduce_status` directly with a `RegistryView` and its reversed tuples. This makes a last-record sabotage observable; filesystem creation order is deliberately erased by content-name scanning and cannot serve as the test input.

- [ ] **Step 4: Assert the declaration inventory, not merely its length.** Add:

```python
assert len(CUT6_ARMS) == 22
assert Counter(arm.row for arm in CUT6_ARMS) == {
    "X4": 2,
    "X5": 1,
    "X6": 3,
    "W13": 8,
    "labeled:admission-idempotency": 1,
    "labeled:status-idempotency": 1,
    "labeled:initialization-idempotency": 1,
    "labeled:durable-mirror": 1,
    "labeled:durable-manifest": 1,
    "labeled:durable-registry": 1,
    "labeled:duplicate-carrier": 1,
    "labeled:manifest-malformed": 1,
}
```

Also assert X7 is absent and no arm row names a slice-2 build.

- [ ] **Step 5: Reuse the cut-5 N2 test shape.** `test_n2_cut6.py` defines one session `findings` fixture over `CUT6_ARMS`; checks `vacuous`, `mixed`, `uncollected`, `stale`; rejects class nodes; verifies every unsabotaged node resolves; and runs the four synthetic malformed-arm verdicts. Import these from the existing harness rather than copying their implementation.

- [ ] **Step 6: Propagate only the new acceptance-root environment.** In `test_n2.py`, add `SCIENCE_CUT6_ROOT` to `_run_check`'s allowlist and to the explicit uncertified-root regression. Do not add CUT6 arms to cuts 1–3's `all_arms`; cut 6 owns its certified acceptance module, as cuts 4 and 5 do.

- [ ] **Step 7: Run red/green at declaration granularity.** First run the 22 unsabotaged checks individually via the new baseline test. Then run each `audit` and require `sound`; a stale, mixed, vacuous, or uncollected verdict is a task failure, not a reason to weaken the sabotage. Run the full portable suite after the cut-6 module's portable dependencies pass.

- [ ] **Step 8: Commit.** Stage the three paths and commit:

```bash
git commit -m "test(cut6): declare and sabotage the 22 frozen units"
```

---

### Task 8: Add the cut-6 acceptance runner and its portable guards

**Files:**
- Create: `python/tools/cut6_acceptance.py`
- Create: `python/tests/test_cut6_acceptance.py`

**Interfaces:**
- Produces CLI: `uv run --frozen python -m tools.cut6_acceptance [pytest args]`.
- Uses `SCIENCE_CUT6_ROOT`; default work directory is `<repo>/.cut6-acceptance`.
- Returns `2` when the engine refuses the volume tuple, never a skip or success.

- [ ] **Step 1: Write runner guards first.** Mirror `test_cut5_acceptance.py` without importing or editing cut 5. Cover: missing `acceptance/test_n2_cut6.py` refuses before probe; probe refusal returns `PROBE_REFUSED`; pytest return code is propagated; temporary run directory is removed on success and failure; child environment contains `SCIENCE_CUT6_ROOT`, `SCIENCE_CUT5_ROOT`, and `SCIENCE_CUT4_ROOT` all bound to the certified run directory because reused older acceptance fixtures consult their own names.

- [ ] **Step 2: Implement the runner.** The probe creates one `WorldConfig(run / "probe-world", "0" * 32, ())`, calls `init_world_root`, and always removes the world root and `metadata_root_for(root)`. After a successful probe, run only `acceptance/test_n2_cut6.py`; its declared checks invoke any needed portable and durable nodes individually. Use `subprocess.run([sys.executable, "-m", "pytest", str(n2), *argv], cwd=PYTHON_ROOT, check=False, env=...)`. Remove the run directory in `finally`.

- [ ] **Step 3: Verify portable guards.** Run:

```bash
uv run --frozen pytest tests/test_cut6_acceptance.py -q
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen pyright src
```

- [ ] **Step 4: Run certified acceptance.** From `python/`:

```bash
uv run --frozen python -m tools.cut6_acceptance -q
```

Require exit 0 and retain the exact test count and elapsed output for Task 9. Then explicitly point `SCIENCE_CUT6_ROOT` at `/dev/shm/science-cut6-refusal` and require exit 2 with the engine's allowlist/barrier refusal and no payload file.

- [ ] **Step 5: Commit.** Stage the runner and guard and commit:

```bash
git commit -m "test(cut6): add the certified acceptance runner"
```

---

### Task 9: Record discharge and close implementation-state claims

**Files:**
- Create: `docs/plans/2026-08-20-conformance-cut-6-results.md`
- Modify: `docs/designs/2026-08-20-world-registry-design.md`
- Modify: `docs/designs/2026-08-20-conformance-cut-6.md`
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md`
- Modify: `python/README.md`
- Modify as grep requires: `docs/guide/identity-world-and-change.md`, `docs/guide/foundations.md`, `docs/guide/open-questions.md`

**Interfaces:**
- Produces the historical record of what actually ran; no frozen row text or cut accounting changes.

- [ ] **Step 1: Run the complete final gate from fresh state.** Run both nodes language gate sets at the committed Task-1 revision. From Science `python/`, run the portable suite, Ruff, Pyright, `tools/check_guide.py`, the 12-test design-corpus guard, and certified cut-6 acceptance. Run `git diff --check` in both repositories. Record exact commands, pass counts, and certified volume result from their fresh outputs.

- [ ] **Step 2: Write the results record from observed output.** Follow `docs/plans/2026-08-19-conformance-cut-5-results.md`: date/subject; a command-result-claim table; exact certified output; the 2 full + 2 part + 1 deferred row accounting; all 14 selected and 8 labeled units grouped by X4/X5/X6/W13/labeled behavior; the `c309db9` feasibility clarification; the nodes prerequisite commit; and explicit non-claims—epochs/build, X7, X5 build arm, fork constructor, chain replay/refutation, genesis/mirror open-path verification, anchor carriage, registry deletion detection, and cross-process locking.

- [ ] **Step 3: Correct design and cut status without rewriting history.** World design status becomes “Implemented 2026-08-20; conformance cut 6 discharged” and retains dated deferrals. Cut status remains frozen and adds “discharged 2026-08-20; results at …”; do not edit quoted rows, selected bullets, or 22-unit accounting.

- [ ] **Step 4: Close the ledger precisely.** Row 1 says the authoritative core landed while epochs and four maps remain outstanding. Row 2 becomes **partially landed**: fresh adoption/minting and state identity complete; fork construction and build-time uniqueness outstanding. Row 3 names the shipped versioned §11.1 RFC 8785 text API and its nodes commit, while leaving reserved paths, recoverable construction, and digest-id hazards at their actual states. The Plan B gate note says slice 1 landed and slice 2 remains.

- [ ] **Step 5: Run the required propagated-claim grep and correct only live user-facing claims.** Run:

```bash
rg -n "implementation prospective|remains prospective|world index.*unbuilt|world indexing.*unbuilt|corpus manifest.*unbuilt|corpus_id.*unbuilt|Everything else in the design corpus is unbuilt" README.md python/README.md docs/guide docs/designs
```

At minimum, replace `python/README.md`'s blanket “Everything else … unbuilt” with a pointer to the ledger plus a short statement that cuts 1–6 have landed their selected slices. In `identity-world-and-change.md` and `foundations.md`, state that the authoritative world root/manifest/registry core is implemented while epoch publication, maps, global resolution, anchor verification, and slice-2 build behavior remain designed or deferred. Add the world-registry design, cut, and results to those pages' `sources`, and set affected guide `updated` dates to `2026-08-20`. Do not change conceptual prose that was already future-tense by design rather than an implementation-status claim.

- [ ] **Step 6: Verify documentation and repository cleanliness.** Run `tools/check_guide.py`, `test_designs_corpus.py`, `git diff --check`, and the grep again. Any remaining hit must be either a dated historical statement or an explicit slice-2 deferral; explain that classification in the results record if it could be mistaken for drift.

- [ ] **Step 7: Commit the discharge landing.** Stage only the results/status/ledger/guide files and commit:

```bash
git commit -m "docs(cut6): record world-registry discharge"
```

- [ ] **Step 8: Final verification after the commit.** Re-run `git status --short --branch`, the portable Science gate, and cut-6 acceptance. Confirm the nodes prerequisite commit is reachable in the nodes repository and the Science worktree is clean. Report both commit ids and the exact final pass counts.
