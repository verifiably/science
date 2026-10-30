# Read restored stores beside one writable store

Status: proposed; requires human review before implementation planning.
Task: sci-300dab.

## Intent and evidence

A relocated world must retain access to inherited holdings while accepting new
dataset bytes. Restoring a store preserves its identity and makes the replica
read-only-serviceable; it does not make it writable. Replacing that store with a
fresh store in the current configuration makes inherited observations unresolvable.

The human's originating request was to diagnose the store lifecycle and reconcile
the failed invocation blocking mm-62e2da. In session
`claude-code:a2943a1d-dd3d-4577-a43b-8347da7f11bf`, the human then authorized filing
three science tasks. The agent proposed the writable-side-store architecture;
this design's choices are the controller's recommendations, not prior human
approval. sci-eccb43 covers refusal closure; sci-409235 covers dangling-intent
settlement. Neither is folded into this work.

Tree inspection on 2026-10-30 established:

- Science at `fa86e50d4f16f4e2d21df8bc69ece57f35e0c9ca` passes `config.store_root`
  to the kernel session. `ReadContext.held_path` and `snapshot` resolve only that
  store's identity. Both `dataset` and `fetch` write using `writer.store_id` and
  `writer.holdings_context`; neither chooses a store independently.
- Beliefs at `405f24995bf0934fe4fc3cdd9fdb98be4dd2516a`, `root.py`, provides
  `init_store_root`, `store_identity` and `fork_store`. A fresh initialization or
  fork mints a new identity. `store_identity` inspects the genesis detached and
  grants nothing. The attended-session constructor binds one write store.
- Atoms at `1e83a241124f743574912e23a4be9946eb484d0c`, root lifecycle design
  sections 5 and 12, states that nothing leaves read-only-serviceable and that
  read admission grants no writability. This is the intended lifecycle boundary,
  not a kernel defect this task should bypass.

The originating investigation reported five inherited mm30 holdings and a failed
holding leaving an unsettled location. Those are historical observations, not
live-world checks repeated by this design session.

## Approaches and recommendation

1. **Keep `store_root`; add `read_store_roots` (recommended).** The existing key
   remains the sole destination for writes and a readable store. Additional
   roots participate only in reads. This is one additive configuration field,
   uses the kernel's existing writer unchanged, and preserves single-store
   configurations without a compatibility layer.
2. **Replace it with `store_roots` and `write_store_root`.** This closely mirrors
   corpus configuration, but forces every configuration and fixture to migrate
   without adding capability needed by this task.
3. **Fork and resolve through ancestry.** This copies payload and requires rules
   for interpreting parent observations under a child's new identity. The
   current public identity reader does not expose that relation. It is larger
   than mounting the original identity alongside a fresh write store.

Choose option 1. A read store does not need to be physically read-only: the
configuration role means science never supplies it to the write endpoint.
Restored stores remain physically read-only under the kernel's lifecycle rules.

## Configuration contract

`store_root` remains required with its existing meaning and path resolution.
Add optional `read_store_roots`, a list of nonempty path strings, defaulting to
`[]`. Paths resolve against the configuration file's real directory, like
`store_root`. `ScienceConfig` carries `read_store_roots: tuple[Path, ...] = ()`.

Example after an operator initializes a fresh sibling store:

```toml
store_root = "stores/working"
read_store_roots = ["store"]
```

`store` is the original restored root. Neither its bytes nor its identity
changes. The corpus configuration still includes the corpora carrying inherited
declarations and observations, with the existing writable `write_root`.

Reject malformed lists, non-string or empty entries, repeated resolved paths,
and an entry resolving to `store_root`, with `invalid-input` naming the field
and offending roots. Do not silently deduplicate. There is no renamed old key,
alternate schema, implicit directory search or auto-initialization.

Validate store identities through a shared configuration helper using
`beliefs.root.store_identity` over `store_root` and every `read_store_roots`
entry. It returns an in-memory identity-to-root mapping, not a new persistent
registry. A missing/uninitialized or malformed store refuses with `invalid-input`
naming its root; translate the kernel's `CorpusRootRefused` at this boundary.
Two roots claiming the same store identity refuse, naming both roots and the
identity. Configured replica selection is explicit: list only one carrier per
identity. Genesis inspection establishes identity, not a new claim of lifecycle
serviceability, current byte integrity or writability.

Keep TOML parsing separate from identity inspection so configuration parsing
needs no initialized stores. The shared helper also checks path uniqueness for
direct `ScienceConfig` callers. Run identity validation before
`open_attended_session`, so invalid read-store bindings cannot create a session
ledger. `ReadContext` uses the same helper lazily, cached for that context, when
it first needs a store binding. Reads that do not consume held bytes need not
open every store. No read invokes a recovering or writable kernel operation.

## Reads and writes

Change the internal `held_path_for` and `held_path` interfaces to accept the
identity-to-root mapping instead of one root and identity. Update all callers,
including `vocabulary.snapshot`, its `ReadContext` call, and focused tests.
Keep `ReadContext.store_id()` meaning the write store's identity; there is no
write selection among read stores.

`held_path_for` walks the reducer's observation tuple in its existing order.
For each `store:<id>:<relative path>` observation, it resolves through the
configured mapping for exactly that id. It returns the first resolvable
observation. URL observations and unconfigured store identities do not resolve.
With none resolvable it raises `invalid-input`, naming the configured identities
and observed locations. Configuration ordering grants no extra authority and
does not override the reducer's order. A fork is a different identity; identical
relative paths or bytes never substitute for the recorded identity.

This change does not introduce search-on-read, network retrieval, trying another
file after an I/O error, or recovery. Preserve the existing reducer's blocked
and unsettled results. Preserve locator validation; a malformed or escaping
store-relative locator must never expose a path outside its matched root.
Vocabulary reads continue checking their declared digest, and run/verify keep
their existing input validation. Byte integrity is not inferred merely from a
configured path. Semantic holdings/admission reduction remains independent of
whether a local store is configured; `is_held` and `found_observations` retain
their current meanings.

The session continues passing only `config.store_root` to beliefs. `dataset`
and `fetch` continue deriving locators from `writer.store_id`; the new mapping
never enters their write destination selection. A newly created holding's
observation names the fresh store, and subsequent reads can resolve both old
and new observations. Existing per-location supersession must continue leaving
other stores' observations standing.

## Creating the writable side store

Deliver a reference runbook at `docs/stores.md`, linked from the README, with
an executable operator recipe using `beliefs.root.init_store_root`. The recipe
is an explicit operator-time kernel call, like existing world setup in the
mm30 record, not a science command or a new permission family. Framework
section 4.4 keeps generic lifecycle creation outside command reachability.
No new CLI declaration or adapter is needed.

The runbook must cover this sequence:

1. Stop the world's writer through its owner and retain the old configuration.
   Record the restored store's identity and the inherited holdings to verify.
   Choose a fresh sibling path on a kernel-supported certified volume, outside
   the old store and its metadata tree. Retain the restored store and metadata.
2. Initialize only that explicit path. The recipe takes an absolute destination
   argument, prints the resulting store id, and does not edit configuration:

   ```python
   import sys
   from pathlib import Path
   from beliefs.permit import Authority, WritePermit
   from beliefs.root import init_store_root

   destination = Path(sys.argv[1])
   if not destination.is_absolute():
       raise SystemExit("destination must be an absolute path")
   authority = Authority(WritePermit(frozenset(), frozenset({"lifecycle"})), "operator")
   print(init_store_root(destination, authority=authority))
   ```

   Run it with the project's documented Python environment. The published
   runbook supplies the complete shell invocation with the argument. The
   initializer owns retry semantics: rerunning its successful initialization
   returns its identity; trying to initialize a restored copy refuses. Do not
   edit lifecycle metadata or mint substitute observations manually.
3. Set `store_root` to the new destination and append the original root to
   `read_store_roots`, preserving any existing read stores. Check that the new
   identity differs from all configured read-store identities. Keep all other
   configuration fields, especially corpus mounts and `write_root`, intact.
4. Restart the writer with that exact config. Verify the inherited vocabulary
   and input lookups. An authorized new holding should resolve under the fresh
   store and leave the inherited root's payload, chain and metadata unchanged.
5. Retain both stores and both sets of metadata for future relocation/backup.
   After new writes, reverting the config to the old single store hides new
   holdings; rollback must preserve access to every identity still referenced.

This task delivers and tests the recipe on disposable certified fixtures.
Executing it in the live mm30 world, changing that world's config, settling the
old intent, disposing the retry guard and retrying the key holding remain
separate explicitly authorized actions owned by mm-62e2da and sci-409235.
Landing this task provides the route; it does not prove the live pilot ready.

## Scope and verification

Production changes reach `config.py`, `holdings.py`, `vocabulary.py` and
`session.py`; `dataset` and `fetch` should need no new destination logic.
Review `run.prepare` and its `verify` consumer to ensure their inherited-data
reads use the shared resolver. Update helpers that serialize `ScienceConfig`
so a nonempty `read_store_roots` survives round-tripping. No dependencies or
new persistent science state are needed.

Update framework configuration section 9.1 and its current key summary, README
configuration guidance, and the new runbook. Historical records and old plans
remain historical; their existing single-store examples are still valid for
single-store worlds. Mention the runbook from the belief-path configuration
section if needed to prevent its single-store description implying a limit.

Acceptance evidence must include:

- Existing one-store behavior and config round trips; multi-store round trips,
  relative paths independent of cwd, malformed lists, duplicate paths/aliases,
  malformed or missing genesis and duplicate identities. Session validation
  failures leave no new session ledger.
- An observation under a configured read-store id resolves there; an unknown
  id never resolves by path coincidence, including a fork's fresh identity.
  Multiple eligible observations preserve reducer order; path confinement
  stays intact. Store identity inspection remains detached and non-mutating.
- A real restored replica fixture, created through kernel replicate/restore
  routes with its observations retained in configured corpora. Initialize the
  fresh store through the documented recipe. Inherited dataset and vocabulary
  reads work; a dataset command writes and reads new bytes only in the fresh
  store. Compare the restored root, its metadata and chain before/after.
- A fetch against the fresh store preserves a matching inherited observation
  under the old store id. Run preparation and verify's shared preparation can
  consume inherited held inputs; no live scientific experiment is needed.
- A blocked/unsettled holding stays blocked; adding a store grants no repair.
  Keep the existing missing-observation and digest-mismatch coverage.

Use `just test-one <pytest args>` for regression work with RED then GREEN;
use the project's mandatory checks and baseline policy during implementation.
There is no `.tt.toml` at the inspected code root, so normal suite requirements
apply. The full baseline is deferred until execution Setup, as the planned-work
rule requires. The design phase runs documentation/task hygiene only and makes
no claim that the regression has been fixed or runtime-tested.

## Builder discretion and review gate

The builder chooses helper names, fixture placement, and whether removing a
now-redundant internal method reduces code. They may not change identity
matching, destination selection, lifecycle permissions, refusal semantics,
operator authorization or the live-world boundary without revising this design.

The next deliverable after human design approval is a separately reviewed
implementation plan. The design does not authorize implementation or live-world
mutation by itself.
