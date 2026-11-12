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
  .venv/bin/python tests/fixtures/analysis/demo.py "$SCIENCE_DEMO_ROOT"
```

The script refuses an existing directory. Its transcript prints the configuration,
held prerequisite addresses, command inputs, invocation ids and minted records.
It runs claim → dataset → spec → run → assess → verify → belief, including the
selected target key, then prints the queue. Expected: a passed clean-environment
verification, `Belief` and an admitted queue row. Inspect a refusal or `NoBelief`
before treating the demonstration as successful.

This source-checkout example writes a canned supported outcome after reading
synthetic bytes. It tests plumbing and reproducibility; it is not a biological
finding about PHF19. The outcome-file rule produces no numerical estimate, and
none is invented from the estimand reference. The bootstrap helpers are not an
initialization API for a scientific deployment.

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
building one — a record kind, a cohort or overlap model, a prior-exposure or
validation-reservation ledger, an independence rule, a reader for a shared
resource — ask whether the problem is general to the domain or to every program.
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
took four separate upstream tasks.

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
