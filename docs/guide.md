# Using science

Type: guide; document types 1. For scientists and agents using the CLI, MCP or
Python dispatcher to follow an analysis from held data to a checked belief.

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

This example uses public test helpers for operator-time bootstrap only: they
initialize a disposable world, adopt the testing contract, hold its concept and
level lists, and install the holdings reducer. This is a source-checkout example,
not an initialization API for a scientific deployment. The testing workflow reads
`x\n` and writes canned `supported` output. An admitted result here demonstrates
plumbing and reproducibility; it is not a biological finding about PHF19.

Choose a **new, empty path on certified storage**, outside any real corpus or
store, and an empty disposable home. Run from `science/python` after the frozen
install. The environment below deliberately supplies no credentials or private
study paths. Set `SCIENCE_DEMO_ROOT` to that new path; the script refuses an
existing one. Keep the transcript and the directory if you need its evidence.

```sh
export SCIENCE_DEMO_ROOT=/absolute/certified/storage/science-demo
mkdir -p "$SCIENCE_DEMO_ROOT-home"
env -i PATH="$PATH" HOME="$SCIENCE_DEMO_ROOT-home" \
  SCIENCE_DEMO_ROOT="$SCIENCE_DEMO_ROOT" PYTHONPATH=tests \
  .venv/bin/python - <<'PY'
import json
import os
from pathlib import Path

from helpers.world import build_fixture_world_with_contract, fixture_bundle, write_config_for
from science.config import ReadContext, load_config
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.session import open_session

work = Path(os.environ["SCIENCE_DEMO_ROOT"])
assert work.is_absolute(), "choose an absolute path on certified storage"
work.mkdir()  # exclusive: never reuse another world's directory
cfg = build_fixture_world_with_contract(work)
config_path = write_config_for(cfg)
cfg = load_config(config_path)
print("configuration:", config_path)
code, entrypoint, targets = fixture_bundle(work, "supported")
data = work / "data.txt"
data.write_bytes(b"x\n")
declarations = production_tree()
session = open_session(cfg)
d = Dispatcher(declarations, resolve_handlers(declarations), ReadContext.open(cfg), session=session)

def invoke(name, inputs):
    print("COMMAND", name, json.dumps(inputs, sort_keys=True))
    result = d.invoke(name, inputs)
    print("INVOCATION", result.invocation_id)
    print(result.text)
    return result.text

def record(text, kind):
    return next(word for word in text.split() if word.startswith(kind + ":"))

try:
    dataset = record(invoke("dataset", {
        "path": str(data), "title": "expression", "locator": "accession:GSE-FIXTURE",
    }), "dataset")
    proposition = record(invoke("claim", {
        "subject": "concept:disease-stage", "predicate": "affects",
        "object": "protein:PHF19", "layer": "causal", "polarity": "positive",
    }), "proposition")
    spec = record(invoke("spec", {
        "target": proposition, "dataset": dataset,
        "contrast": "levels", "slot": 0, "baseline": "level:early", "comparison": "level:late",
        "measure": "measure:tpm", "scale": "additive", "reference": "0",
        "identification": "identification:observational", "method": "rank comparison",
        "assumptions": "independent samples", "falsification": "no difference at alpha",
        "interpretation_rule": "beliefs/outcome-file/v1",
        "equivalence_rule": "beliefs/content-identity-equality/v1",
    }), "analysis-spec")
    run = record(invoke("run", {
        "spec": spec, "dataset": dataset, "code": str(code),
        "entrypoint": entrypoint, "targets": list(targets),
    }), "run")
    assessment = record(invoke("assess", {"run": run}), "assessment")
    invoke("verify", {"assessment": assessment, "code": str(code), "entrypoint": entrypoint})
    invoke("belief", {"proposition": proposition})
    invoke("next", {})
finally:
    session.close()
PY
```

Every `invoke` goes through production declarations, validation, permits and the
attended session. The example creates no service and closes its session even on
failure. Its `science.toml` exposes the exact bootstrap paths and contract; inspect
it before using the same world through another transport.

Expected: `dataset`, `claim`, `spec`, `run`, `assess` and `verify` each report their
minted records. Save the returned addresses, rather than guessing a title or digest.
Verification should be `passed` with `clean-environment` scope; the final answer
should be `Belief` and the proposition classified as `admitted`. A refusal or
`NoBelief` must be explained before treating the demonstration as successful.
Generated IDs depend on the new world and execution and are not portable constants.

## Your own analysis

Replace the demonstration with an operator-admitted world and your own contract,
held vocabulary, empirical data and workflow. The contract must declare your
operator, argument sorts, qualifiers and estimand; `claim` refuses a combination
with no matching plan row. A locator attests the source of data; it does not prove
its scientific quality. Do not present the fixture's invented accession as yours.

1. `dataset` holds a local file, fingerprints it and optionally records its empirical
   locator. Preserve the returned `dataset:sha256:…` address.
2. `claim` records a typed question. Its title is prose; its typed meaning defines
   identity. Save the `proposition:…` address.
3. `spec` freezes the target, estimand, method, assumptions, input roles and rules.
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
