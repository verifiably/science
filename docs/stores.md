# Reading inherited stores beside a writable store

Science writes holdings only to the required `store_root`. Optional
`read_store_roots` adds carriers for inherited observations:

```toml
store_root = "store-working"
read_store_roots = ["store"]
```

Both paths resolve against the configuration file's real directory. With no
`read_store_roots`, the configuration continues to use one store. A read store
may be a restored replica or a previous writable store; its role never makes
it a destination for `dataset` or `fetch`.

Every configured root must have a store identity and existing read admission:
`WRITABLE` or `READ_ONLY_SERVICEABLE`. Duplicate resolved paths or identities
refuse. A copied genesis alone is insufficient. Inspection never initializes,
repairs, recovers or migrates a root, and errors refuse rather than assume
readability. The check also applies to `store_root`, before opening a session
ledger; a read context checks lazily when it needs stores.

Holdings resolve by exact store identity in the reducer's lexicographic
`(digest, location)` order. The write store has no priority. An I/O error or
vocabulary digest mismatch does not cause a retry from another copy. A
vocabulary with found observations but no configured carrier refuses, including
through evaluation and input gathering. Missing declarations or found
observations, and a selected vocabulary's digest mismatch, remain unreadable.
Lifecycle admission does not attest payload bytes on every use. Run/verify
staging records a digest but does not compare it with the dataset declaration.

## Relocating a world

These are explicit operator actions. Landing the read-store support does not
perform or authorize live initialization, migration, configuration changes or
holding writes.

1. Stop the world's writer through its owner and retain the old config. Record
   the inherited store identity and holdings to check afterward. Retain its
   payload and metadata. Confirm its state with
   `beliefs.root.read_lifecycle_state`: only `WRITABLE` and
   `READ_ONLY_SERVICEABLE` supply reads. An incomplete restore must be completed
   through the kernel restore route before mounting it.

   Choose an absolute, fresh sibling path on a kernel-supported certified
   volume. For `store` and `store-working`, `metadata_root_for(root)` names
   `store.metadata` and `store-working.metadata`. Resolve all four paths.
   For each new payload/metadata path `new` and old payload/metadata path `old`,
   require `new != old`, `not new.is_relative_to(old)`, and
   `not old.is_relative_to(new)`. Neither new tree may overlap either old tree.

2. From the checkout's `python/` directory, after the README's `uv sync` setup,
   replace the absolute destination below and run the initializer. It uses
   only the `lifecycle` authority and prints the new identity; it does not edit
   configuration. This is an operator kernel call, not a science command.

<!-- store-init-recipe -->
```sh
uv run python - /absolute/path/to/store-working <<'PY'
import sys
from pathlib import Path
from beliefs.permit import Authority, WritePermit
from beliefs.root import init_store_root

destination = Path(sys.argv[1])
if not destination.is_absolute():
    raise SystemExit("destination must be an absolute path")
authority = Authority(WritePermit(frozenset(), frozenset({"lifecycle"})), "operator")
print(init_store_root(destination, authority=authority))
PY
```

   Repeating a successful initialization returns the same identity. Passing
   a restored copy refuses; initialization is not promotion to writable.
   Never edit lifecycle metadata or mint replacement observations by hand.

3. Set `store_root` to the new root and append the original root to
   `read_store_roots`, preserving existing entries. Require the new identity
   to differ from every read-store identity. Retain the corpora containing
   inherited declarations and observations, and leave `write_root` and the
   other configuration fields intact.

4. Restart the writer using that exact config. Verify inherited vocabulary and
   input lookups. An explicitly authorized new holding must resolve in the new
   store while the inherited payload, chain and metadata remain unchanged.
   A blocked location for a declared digest blocks the entire dataset, even
   beside a healthy copy of the same bytes. This configuration cannot repair
   or route around that block. Before declaring the mm-62e2da pilot ready,
   inspect its actual reduction and settle any unsettled location as
   [Settling an unsettled location](#settling-an-unsettled-location) describes.

5. Back up both stores and both metadata trees. After new writes, reverting
   to the old single-store config hides the new holdings. Rollback must keep
   every still-referenced store identity available; removing a config entry
   does not move or rewrite observations.

## Settling an unsettled location

A holdings write appends its intent to the write corpus before it touches the
store. When the store then refuses (a read-only-serviceable `store_root`) or
the write is interrupted, no observation follows, and the holdings reduction
blocks that location `unsettled` until a later re-check at the same location,
in the same corpus chain, is matched by its observation. `science recheck`
is that re-check. It reads the store and writes governed evidence (an
observation and a re-check act-report) to the configuration's `write_root`, so
it settles only intents in that `write_root`'s chain, and on a live world it
needs the person's authorization first.

1. Find the blocked location. A dataset read that meets the block refuses
   naming it (`<address> is blocked at <locations>: <reasons>`), and the
   holdings reduction lists it among its blocked rows; no science command
   lists blocked rows by itself. Its spelling is
   `store:<store id>:<relative path>`; give it to `recheck` unchanged.
2. When the location's store is the current `store_root`, for instance before
   relocating, run `science recheck --location <location>` with the working
   configuration.
3. When the location's store is in `read_store_roots`, as after relocation,
   the working configuration refuses and names this route. Stop any running
   `science serve`, then run the re-check under a recovery configuration: that
   read store as `store_root`, the same `write_root` and operations root, and
   the writable store moved to `read_store_roots`. A re-check never writes the
   store, so binding a read-only-serviceable one is valid. Then restore the
   working configuration and restart the writer.
4. Read the result. `found <digest>` or `absent` publishes an observation and
   clears the block. An inconclusive read (`retrieval-failed` or
   `byte-locator-untested` with the kernel's reason) publishes none and leaves
   the block: fix the store's serviceability, then re-check again. Absent is
   never assumed; the report carries what the kernel observed.

## Existing stores without admission

Inventory each configured write and read store before rollout. An older
single-store world can now refuse reads if its root lacks admission. Record
its identity, lifecycle state or inspection error, and whether the config is
active or archived; retain evidence for archived or deleted worlds. Unknown
or inaccessible active roots require resolution before rollout.

Beliefs provides `migrate_root_to_lifecycle_v3` for the exact pre-lifecycle v2
store. Calling it is the operator's attestation that this host originally
created the root. A refusal alone does not establish that premise. Inspect the
kernel diagnostics and source records, and obtain explicit authorization for
any needed migration. A restored replica needs restore completion, not this
migration or a writable promotion. Science never migrates on read.
