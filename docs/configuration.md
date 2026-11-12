# Configuration

Type: data model; document types 1. The science TOML configuration is currently
unversioned. It names existing kernel roots and the reader/writer profile; it does
not initialize or repair them. See [the guide](guide.md) for bootstrap and use,
[stores](stores.md) for read admission, and [sessions](sessions.md) for launch order.

## Location and required fields

Pass `--config <file>` or `SCIENCE_CONFIG`; an explicit CLI value wins. No file is
discovered from the working directory. All path values below resolve against the
configuration file's real parent directory, including contract predecessor paths.
Unknown top-level keys, missing required keys, malformed TOML and invalid types
refuse as `invalid-input`. Boolean values do not stand in for integers.

| Required key | Type and meaning |
| --- | --- |
| `world_root` | String path of the initialized world registry |
| `world_id` | Exactly 32 lowercase hexadecimal characters identifying that world |
| `corpus_roots` | List of string paths mounted by this configuration |
| `operations_root` | String path for session ledgers, operation scratch and presentation sidecars |
| `domains` | List of shipped domain namespace strings compiled for the writer |
| `contracts` | List of local contract entries activated for the writer |
| `store_root` | String path of the sole destination store for new holdings |
| `coordination` | Positive integer naming a shipped coordination contract, or `false` to disable coordination |

For example, after operator bootstrap has created these roots and adopted the
corresponding manifests:

```toml
world_root = "world"
world_id = "0123456789abcdef0123456789abcdef"
corpus_roots = ["corpus"]
operations_root = "operations"
domains = ["general"]
contracts = []
store_root = "store"
coordination = 2
```

The shipped `general` contract declares no sorts, dimensions or dataset facets.
Add an explicit local contract for a program's vocabulary, measurement and
`--facets` inputs; `local/gene-axis` must be declared there before use.
That illustrative id is not a usable world identity. Read the actual bootstrap
configuration rather than assigning a new id to an existing world.

## Optional fields and defaults

| Key | Type, default and restrictions |
| --- | --- |
| `write_root` | String path; defaults to the single configured corpus root. With zero or multiple roots it must be explicit and belong to `corpus_roots`. |
| `read_contracts` | Contract-entry list, default `[]`; available for resolving read mounts, never activated for the writer. |
| `service_socket` | String path, default `operations_root/service.sock`; Unix socket path must fit the host limit (107 UTF-8 bytes on Linux). |
| `default_project` | Unpinned project address `coord:<project>`; no default. Names, subordinate addresses and revision pins refuse. Requires coordination. |
| `read_store_roots` | List of nonempty string paths, default `[]`; inherited holdings carriers, never write destinations. |
| `sharing_root` | String path, absent by default; registry and adopted roots for sharing. Mounted pins add read roots at config load. |
| `accept` | List of 32 lowercase hex world ids, default `[]`; whose published evidence the reader accepts. |
| `keep` | List of 32 lowercase hex corpus ids, default `[]`; protects pins against retirement. |
| `fetch` | Table, default `{ policy = "records-only", max_bytes = 0 }`. |

`fetch` takes exactly required `policy` (`records-only` or `fetch`) and optional
nonnegative integer `max_bytes`. Zero means no byte limit; it is not a spending or
network quota. `fetch` still checks declared digests. See [sharing](sharing.md).

## Contract entries and mount profiles

A contract entry is a path string for a genesis document, or a table for a
successor with its predecessors, oldest first:

```toml
contracts = [
  { document = "contracts/current.yaml", predecessors = ["contracts/genesis.yaml"] }
]
read_contracts = ["contracts/another-domain.yaml"]
```

The table permits only `document` and `predecessors`: a nonempty document string
and a nonempty list of predecessor path strings. Loading compiles the lineage,
including the document's authoring plan if present. A contract identity listed
in both `contracts` and `read_contracts` refuses. The writer's base, domain and
coordination profile must agree exactly with its manifest pins before session
creation. Read mounts compile the profile their own manifest pins name, using
shipped and available local contracts. A mount's contract is not silently replaced
by the writer's. Unresolvable or conflicting pins refuse.

`write_root` is chosen before sharing mounts are appended; sharing cannot change
which corpus is writable. Duplicate claimed corpus carriers refuse. Equal record
copies can resolve across session holders; disagreeing content refuses. Scientific
writes use the one writer profile and may cite admitted read mounts. Mutating an
existing record remains restricted to the write root.

## Storage and state boundaries

Resolved duplicate store paths and duplicate store identities refuse. Every store
must already be initialized and `WRITABLE` or `READ_ONLY_SERVICEABLE`. Store
inspection never recovers or promotes it; an incomplete restore requires the
kernel route. Session opening validates stores before creating a ledger; read
contexts validate lazily when store access is needed.

All scientific records live in beliefs corpora. Session selection and sharing
acts instead leave ledger lines. Science's sharing registry is a projection of
those lines; its historical report-tail files are presentation evidence whose
commentary cannot be reconstructed if lost. Retain them beside the ledgers when
exact replay matters. Configuration loading records a content digest, and sharing
operations can refuse `config-stale` when the file no longer matches that capture.
Root lifecycle, manifest and contract admission remain kernel checks, distinct
from TOML shape validation.

## Local contract document and operator plan

The YAML document is currently unversioned at the launcher layer and has exactly
required `contract` and optional `plan`. The kernel parses the domain contract
and its lineage; see its [contracts](https://github.com/verifiably/beliefs/blob/main/docs/contracts.md).
The plan is launcher input and is not covered by that contract's content identity.

`plan` is a table with string mappings `sorts` (term kind prefix to contract
sort), `layers` and `polarities` (null is allowed for sign-inapt operators), plus
an `operators` list. Every row requires `predicate`, `operator` and exactly
`roles: {subject: <role>, object: <role>}`. Optional `subject` and `object` kind
prefixes must occur together; omitting both declares a wildcard row.

For local concept/protein sorts, a row mapping the binary CLI onto the shipped
named-role operator is:

```yaml
predicate: affects
subject: concept
object: protein
operator: general/changes-under-intervention
roles: {subject: intervention, object: response}
```

Unqualified operator/sort names resolve within the local contract namespace.
Claim authoring tries the exact `(predicate, subject, object)` row, then the
wildcard; no row or sort mapping refuses. Duplicate row keys refuse. After profile
composition, activated `contracts` plans must fill either two distinct one roles
or one many role admitting two unit-coefficient members, without an unfilled
ordinary role. Many-role receipt indexes follow the kernel's canonical member
order, which may differ from CLI subject/object order.

`read_contracts` documents have their plan shapes parsed but do not activate plans
or validate their operators against the writer's profile. `claim` uses the first
activated document carrying a plan; plans are not merged. Positional plans must
be rewritten explicitly with named roles.
