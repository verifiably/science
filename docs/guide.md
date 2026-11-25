# Using science

Type: guide; document types 1. For scientists and agents using the CLI, MCP or
Python dispatcher to follow an analysis from held data to a checked belief.
[Configuration](configuration.md), [commands](commands.md), [sessions](sessions.md)
and [sharing](sharing.md) specify the fields and protocols used below.

## Prepare a world

Install from the sibling source checkouts as described in the [README](../README.md#install).
You need Python 3.11 or later, uv, Git, and the locked workflow dependencies.
Writes require a kernel and volume certified by atoms. Runs additionally need
bubblewrap (`bwrap`) and working unprivileged user namespaces; the normal run
command refuses when confinement is unavailable. A temporary filesystem is not
certified storage. See the kernel's
[host requirements](https://github.com/verifiably/beliefs/blob/main/docs/development.md#the-certified-host).

A science configuration names an already initialized world, admitted corpus,
compiled contracts, operations directory and registered store. Science has no
world-initialization command. An operator creates and admits roots and installs
rules through the kernel; see its
[guide](https://github.com/verifiably/beliefs/blob/main/docs/guide.md),
[record contracts](https://github.com/verifiably/beliefs/blob/main/docs/records.md)
and [write protocol](https://github.com/verifiably/beliefs/blob/main/docs/writes.md).
Contract vocabulary datasets and the rules used by an analysis must be held.
Do not copy a manifest or change its pins to bypass admission.

Supply the configuration explicitly on every CLI call, or set `SCIENCE_CONFIG`:

```sh
cd python
uv run science status --config /absolute/path/science.toml
```

Relative configuration paths resolve beside the configuration file, independently
of your working directory. Opening a different directory does not select a world.
The launcher refuses absent configuration and unknown configuration keys.

## A synthetic source-checkout demonstration

The complete [demo script](../python/tests/fixtures/analysis/demo.py) uses explicit
kernel fixture authority to initialize a disposable world and hold its concept
and level lists, two procedures and a classification rule. It copies the full
[estimand authoring document](../python/tests/fixtures/analysis/estimand.json) into
that world, then uses production declarations and an attended session for every
analysis act. The session closes even when an invocation fails.

Choose a new absolute directory on certified storage and a disposable home. From
`science/python`, after the frozen install:

```sh
export SCIENCE_DEMO_ROOT=/absolute/certified/storage/science-demo
mkdir -p "${SCIENCE_DEMO_ROOT}-home"
env -i PATH="$PATH" HOME="${SCIENCE_DEMO_ROOT}-home" PYTHONPATH=tests \
  .venv/bin/python tests/fixtures/analysis/demo.py walk "$SCIENCE_DEMO_ROOT"
```

The script refuses an existing directory. Its transcript prints the configuration,
held prerequisite addresses, command inputs, invocation ids and minted records.
It runs dataset → claim → spec → run → assess → verify → belief, including the
selected target key, then prints the queue. Expected: a passed clean-environment
verification, `Belief` and an admitted queue row. Inspect a refusal or `NoBelief`
before treating the demonstration as successful.

The same invocation with `create` in place of `walk` builds the same world and
stops before the first command: a fresh world for a harness probe whose agent runs
the commands itself. It prints the configuration, held prerequisites, the spec's
rule-procedure binding and the paths of the estimand, data and workflow bundle the
walk uses. With `readback "$SCIENCE_DEMO_ROOT/science.toml"` in place of
`walk "$SCIENCE_DEMO_ROOT"`, it prints the write root's records at any point of the
path. It opens the world without settling an interrupted world transaction, so it
never performs a resuming agent's recovery, and refuses while one is pending. It
prints the count by kind, each proposition's claim identity, each spec's identity,
target and canonical estimand, each run's spec, boundary policy, capabilities and
output digests, each assessment's run and outcome, and each verification's scope and
verdict. After the walk it shows two confined runs, a `supported` assessment and a
passed clean-environment verification.

This source-checkout example writes a canned supported outcome after reading
synthetic bytes. It tests plumbing and reproducibility; it is not a biological
finding about PHF19. The outcome-file rule produces no numerical estimate, and
none is invented from the estimand reference. The bootstrap helpers are not an
initialization API for a scientific deployment.

## A PHF19 world for harness probes

The PHF19 probe uses the pinned GSE179929 gene TPM matrix and predecessor
crosswalk, HGNC 2025-09-05, and the Ensembl 115 GRCh38.p14 annotation. Use the
beliefs sibling checkout pinned for this Science build. The demo checks the kernel's
PHF19 declaration, contract, register, vocabularies and analysis bundle by digest.
The declaration names the matrix, crosswalk, dataset record and proposition record
relative to the predecessor checkout. The release files are explicit arguments.
Keep the original inputs in their existing locations.

From `science/python` after the frozen install, set `PHF19_WORLD` to an absolute,
nonexistent directory on certified storage, `MM30_PREDECESSOR` to the predecessor
multiple-myeloma checkout, and `PHF19_RELEASES` to the directory containing the
verified copies of the two release files.

```sh
PYTHONPATH=tests .venv/bin/python tests/fixtures/analysis/demo.py create-phf19 "$PHF19_WORLD" \
  --predecessor "$MM30_PREDECESSOR" \
  --hgnc "$PHF19_RELEASES/hgnc_complete_set_2025-09-05.tsv" \
  --ensembl "$PHF19_RELEASES/Homo_sapiens.GRCh38.115.gtf.gz"
```

The operator checks the six input digests before creating the world. Bootstrap holds
the vocabularies, mapping and its evidence, classification rule, assay and estimator
procedures, and assumptions registers. It writes `science.toml` and
`authoring.json` with the Science command inputs. The verified matrix copy is ready
for the agent's `dataset` command. Run `dataset`, `claim`, `spec`, `run`, `assess`
and `verify` in order, using the minted addresses for subsequent command arguments.
Use `walk-phf19` in place of `create-phf19` to create and walk a fresh world with
the same inputs, including the final keyed `belief` query.

```sh
PYTHONPATH=tests .venv/bin/python tests/fixtures/analysis/demo.py readback "$PHF19_WORLD/science.toml"
```

Expect `proposition:phf19-rna-pd-vs-ndmm` with the kernel's statistical
gene–stage claim identity. The estimand is probability of superiority for
`hgnc:24566`, with NDMM as baseline, PD as comparison, and GSE179929 as cohort
applicability. Readback shows the original and clean-environment replay runs,
an `inconclusive` assessment, and a `passed` verification. The workflow writes
an effect of approximately `0.600346` to `outputs/stats.tsv` and the keyed
query returns `NoBelief(no-directional-outcome)`. This is an engineering
demonstration with unmodeled subject pairing and unestablished independence and
assay validity.

## Author a native estimand

`spec` takes `--estimand PATH`, required `--standing` and `--evidence-mode`, and
repeatable `--rule-procedures rule-identity=procedure-id`, along with the target,
observed dataset, method, assumptions prose, falsification and two rule identities.
The [complete example JSON](../python/tests/fixtures/analysis/estimand.json)
authors form, functional, named bindings, output specifications, reference,
control, uncertainty and typed assumptions. `schema_version` is integer `1`.
The kernel derives claim/operator identities and frozen dependencies; they are
not authoring fields. The old contrast/slot/measure scalar flags are removed.

Reference values, null-region bounds and increment values use JSON numbers:
`0`, `1` and `0.5` become exact Decimal values. Booleans, non-finite numbers,
strings at those numeric positions, duplicate keys, unknown fields and stored-only
fields refuse before a spec is minted. Native restriction bounds retain their
kernel string encoding. Typed JSON assumptions are distinct from `--assumptions`
prose; an explicit empty list asserts no additional typed assumptions.

Every measurement procedure, classification rule, mapping, proxy, register and
calibration basis must actually be held and pass the native authoring checks.
A model route also requires its explicit held model and the claim's within-model
binding. Foreign prerequisites must be accepted by the author's configuration.
`--registers` may be omitted for an empty register list; it does not manufacture
one. Evidence modes are observation, annotation, simulation, derivation and
literature-extraction; standing is empirical, model or calibrated-model.

The retained `--applicability dimension=quantifier:term` input accepts only
dimensions placed in applicability with term restrictions. For the demo contract,
`--applicability testing/stage=generic:level:early` is well typed. Interval, union,
time-interval, rule and claim-placed dimensions refuse through this command form.
Spec authoring uses live accepted session records and needs no epoch, including
with read mounts. Belief evaluation across mounts still needs a current epoch.

The CLI resolves the estimand file relative to the caller before sending its
absolute path to the service. For MCP or direct dispatcher calls, supply an
absolute path accessible to that process. The file is parsed once per invocation;
validation finishes and input captures close before the single mint.

## Your own analysis

Replace the demonstration with an operator-admitted world and your own contract,
held vocabulary, empirical data and workflow. The contract must declare your
operator, role sorts, applicability dimensions, measurement declarations and estimand; `claim` refuses a combination
with no matching plan row. A locator attests the source of data; it does not prove
its scientific quality. Do not present the fixture's invented accession as yours.

1. `dataset` holds a local file, fingerprints it and optionally records its empirical
   locator. Preserve the returned `dataset:sha256:…` address.
2. `claim` records a typed question. Its title is prose; its typed meaning defines
   identity. Save the `proposition:…` address.
3. `spec` freezes the typed target, standing, dependencies, method, assumptions, input modes and rule procedures.
   Choose rules that actually interpret and compare your workflow's outputs.
4. `run` captures code, environment and held inputs and executes under confinement.
   `entrypoint` is relative to the code root's parent; targets name output paths.
5. `assess` interprets a run under the frozen rule. `verify` repeats it under the
   equivalence rule and records the comparison and its derived scope.
6. `belief` computes the current answer; it does not mint a belief record. `next`
   identifies remaining work. Inspect the input digest and policy binding with
   the answer so its provenance survives later changes.

Use `uv run science <command> --help` for exact CLI flags. The library example
uses input names with underscores; CLI flags use hyphens. To use CLI writes,
keep an attended writer running in another terminal:

```sh
uv run science serve --config /absolute/path/science.toml
uv run science dataset --config /absolute/path/science.toml --path /absolute/path/data.txt --title expression
```

Stop the service when finished. `uv run science mcp serve --config <path>` offers
the same commands over stdio and owns its attended session. Preserve invocation
IDs from transport envelopes: retrying the same write in the same session with
the same ID and inputs replays it; changing inputs under that ID refuses.
Record addresses identify records; invocation IDs identify calls. A continuation
cursor is an opaque page token, not either kind of identity.

## Building for a research program

A research program keeps its workflows, scripts, environments, notebooks and
prose in a workspace repository of its own; its claims, datasets, specs and runs
are minted through `science` into the world. The workspace is the program's, but
the epistemic and methodological components it needs usually are not. Before
building one — a record kind, a cohort or overlap model, an independence rule, a
reader for a shared resource — ask whether the problem is general to the domain or to every program.
If it is, file it upstream first and build it there: `beliefs` owns record kinds
and belief policy, `science` owns the surface and the skills it ships, and
`quarry` owns access to scientific resources. When the program cannot wait for
the upstream release, build a stopgap and have its own record (its guide,
protocol section or module docstring) name the upstream task and the release
that retires it, so the next program finds a plan rather than a second local
copy to extract.

The rule comes from the multiple-myeloma program, which defined cohort nodes,
overlap groups, prior exposure, validation reservation, catchments and assumed
disjointness in its phase-1 protocol and a roster package of about 3,000 lines
because neither `beliefs` nor `science` had them; lifting them out afterwards
took four separate upstream tasks. Prior exposure and validation reservation are
now commands.

### Showing reservation evidence in the program's repository

The program's public repository holds its reservation rule and one generated statement
per chain, and nothing else of the evidence:

- **The rule**, authored as a `standard` (`docs/reservation-rule.md` by convention). It
  states the exact `rule.name` and `rule.version` its assignments carry, and links to
  the statement.
- **The statement**, written by `science reservation-statement --chain <chain> --write
  docs/reservation` after each `reservation-assignment` and committed with what the
  assignment governs. Earlier assignments and events stay in the world; the statement
  names each by address.

After `exposure-event`, add the event's address with `revise` to a clause of the
program's project query that holds one `addresses` predicate and nothing else. That is
what makes the event the program's in a world it shares, and what a publication carries.
Recording an event changes no statement.

A runner, with no world and no `science` installed, reads the JSON file: it compares the
digests of its inputs with `head.facet.inputs`, takes the units it may read from
`head.facet.groups`, and records `head.address` and the file's sha256. A program may also
pin the expected sha256 with the runner's configuration. Where a configuration is present,
the preflight also runs `--check docs/reservation --project <the program's project>` with
the options its rule calls for (`--block-on reserved --block-on withheld --block-on
unscoped`, or `--all-considered --block-on unattributed`). In a world several programs
share it always names its project: otherwise the live session's selection or the
configuration's `default_project` decides, and under another program's project this
program's events never block, while with none selected every program's do. The run records
one of three outcomes:

| Outcome | The run | What it establishes |
|---|---|---|
| passed | proceeds, recording every corpus, marker and project revision the check printed | the statement was the head of the corpora examined, and the gate held for their events at that project revision |
| `chain-absent`, or no configuration | proceeds only if the program's rule allows a run without the world | which statement bytes it read, nothing about currency |
| any other refusal | stops, and the cause is repaired | nothing |

`--check` with `--as-of <head.address>` later confirms that the bytes a run read are that
assignment's statement, not that it was the head at the time.

Publish when the program's own gate passes and `publish-preview` reports `exposure claims`
equal. One addresses-only clause of the project's query names every `history` address,
every address under `events_added`, and every event the program recorded; add the further
references a `closure-incomplete` refusal names. A reader who adopts the publication runs
the same `--check` and gate options against a clone with no project selected (no
`--project`, no session selection and no `default_project`), from a configuration that
mounts only the program's publication beside its own empty write root.

## Recording what was seen and what is held back

Data someone has already looked at stays usable for discovery; whether it can also
confirm an idea formed from it is for the program's reservation rule to decide. Record
each look and each piece of prior knowledge when it happens, with `exposure-event`, and
freeze which data may be explored and which is reserved, with
`reservation-assignment`. Both kinds are world records that any program's
readers can inspect, and neither is an input to `belief`.

A look at data before formulating a question is recorded the same way. Recording it
forces no new assignment: the current one stays the head and `reservation-head` lists
the look as not considered, until the program decides whether its rule changes a role.

With `SCIENCE_CONFIG` set and the service running, this walk records prior knowledge,
roots a chain of epochs that considers it, records a read that exposes the reserved
epoch, and supersedes the assignment. The read cites a `source:` record, which the walk
mints first. Addresses in a payload are sorted.

```sh
address() { grep -o "$1:[0-9a-f]\{64\}"; }

cat > knowledge.json <<'JSON'
{"schema_version": 1, "title": "Model knowledge through its date of use",
 "facet": {"channel": "knowledge", "subjects": [],
           "units": [{"start": "open", "end": "2026-11-07T14:40:51Z"}],
           "effect": "exposing", "class": "training-knowledge",
           "account": "Possible training exposure; no specific learned result asserted.",
           "observer": "agent/K5", "observed_at": "2026-11-07T14:40:51Z", "propositions": []}}
JSON
knowledge=$(science exposure-event --payload knowledge.json | address exposure-event)

assignment() {  # title, events, role of the later epoch, further fields
cat <<JSON
{"schema_version": 1, "title": "$1",
 "facet": {"chain": "epochs", "rule": {"name": "epoch-rule", "version": "1"},
           "inputs": {"boundaries": "sha256:a4b5b8812c9e966f013c55655176cbd22531e7afd0c304cb93cc38e00e50e4a0"},
           "events": [$2],
           "groups": [{"units": [{"start": "open", "end": "2008-12-01T00:00:00Z"}], "role": "open"},
                      {"units": [{"start": "2008-12-01T00:00:00Z", "end": "open"}], "role": "$3"}],
           $4 "assigned_at": "2026-11-08T09:00:00Z"}}
JSON
}
assignment "Epochs, first assignment" "\"$knowledge\"" reserved "" > first.json
first=$(science reservation-assignment --payload first.json | address reservation-assignment)

source=$(science source --title "GSE24080" --accession GSE24080 | address source)
look() {  # title, time
cat <<JSON
{"schema_version": 1, "title": "$1",
 "facet": {"channel": "read", "subjects": ["$source"],
           "units": [{"start": "2008-12-01T00:00:00Z", "end": "open"}],
           "effect": "exposing", "class": "unmask", "account": "$1",
           "observer": "agent/K5", "observed_at": "$2", "propositions": []}}
JSON
}
look "Unmasked the later epoch" "2026-11-09T10:00:00Z" > look.json
look=$(science exposure-event --payload look.json | address exposure-event)

science reservation-head --chain epochs   # still the first assignment; the look is not considered

considered=$(printf '"%s"\n' "$knowledge" "$look" | sort | paste -sd, -)
assignment "Epochs, after the unmask" "$considered" open \
  "\"predecessor\": \"$first\", \"evidence\": [\"$look\"], \"flagged\": []," > second.json
science reservation-assignment --payload second.json

look "Looked at the later epoch again" "2026-11-10T10:00:00Z" > again.json
science exposure-event --payload again.json
science reservation-head --chain epochs

science reservation-statement --chain epochs --write reservation
science reservation-statement --chain epochs --check reservation --block-on reserved
```

`flagged` lists the assessments already made against the group that stops being
reserved, and is empty here because there were none. The last `reservation-head` shows the second
assignment, its one suspended change, and the second look as not considered. The check
passes: that look falls in an epoch the rule no longer reserves.

## Reading and discussing research

With the generated science plugin installed, `/science:research-paper` reads one
paper at a time and records a world source plus a project reading note (including
reading depth, media type, exact-byte digest, reader and quoted statements),
minting a world `source-assertion` directly for any statement paired with an
existing proposition; it can also promote statements from an earlier reading note
into `source-assertion` records offline without re-reading the paper or revising
the note. Source assertions are attributed readings and are inert in `belief`.
`/science:research-topic` records a background synthesis as a topic whose query
names its sources. `/science:discuss` records a critical discussion as a project
note. Select a project with `project-select` before writing notes or topics, or
before discovering earlier reading notes through a project; direct promotion of a
named reading note (`coord:` address or stored `note:` id) writes only world
`source-assertion` records and needs no selected project.

Each article should have one source across projects. Look it up with every
confirmed identifier together: a DOI-only lookup cannot find a record carrying
only a different identifier. Complete a source's identifiers before it is first
published, because a source held by another corpus cannot be corrected here.
Deduplication by shared identifier reduces duplicates; it cannot connect disjoint
identifiers, and existing duplicates are not merged. The skills disclose that
limit when minting after a single-identifier lookup.

Readings obey the workspace's exposure policy. Abstract-only reading is marked
and supports no durable conclusion; unavailable text is not summarized from
memory. The [command reference](commands.md) defines `source`, `source-correct`,
`source-assertion`, `record`, `note` and `topic` and their write boundaries.

## Selection and sharing

A project is a view over records, not a new corpus. `project` creates one from a
query; `project-select --target <name-or-address>` changes the attended session's
selection, and `--clear` clears it. Commands that enumerate through a selection
also support an invocation-only project override. Reads of a named record still
resolve that address; selection does not rewrite its identity.

Sharing is explicit. Publish an epoch, then use `publish-preview --target <project>
--to <destination>` to inspect closure and ownership before `publish`. Publications
carry records and provenance, not all dataset bytes. On another world,
`provider-inspect` examines a provider; `provider-bind` records an explicit binding
to its claimed world; `adopt` verifies and pins the publication. Reopen to mount it,
then `show --corpus-id <id>` explains acceptance. `fetch` holds eligible external
bytes only when configured policy permits it. Publication, provider trust and
redistribution are choices the operator must make explicitly.

## Refusals and honest NoBelief

Read the refusal code, message and detail. Fix configuration/admission before
retrying; do not switch to an uncertified mode to get a green result. A handler
can report already committed work even if a later act could not finish; inspect
its records and ledger before deciding whether to retry.

A passed verification at `same-environment` scope does not admit an assessment.
Failed active verification invalidates it. `NoBelief` can mean unheld policy,
fixtures or inputs, absent corpora, no eligible assessment or no directional
outcome. It is not numeric zero and is not evidence that the scientific claim is
false. Reproducibility establishes that the specified computation repeats; it
cannot rescue a bad method, biased data or the synthetic demonstration's canned
conclusion. See the kernel's [belief rules](https://github.com/verifiably/beliefs/blob/main/docs/records.md#beliefs).
