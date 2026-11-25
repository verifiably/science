# Synthetic analysis example

`demo.py walk ROOT` initializes a new disposable world using the source checkout's
explicit kernel fixture authority, holds its vocabulary and measurement prerequisites,
and runs the production dataset → claim → spec → run → assess → verify → keyed
belief workflow. It requires a certified volume and production confinement.
`demo.py create ROOT` builds the same world and stops before the first command, for
a harness probe whose agent runs the commands; `demo.py readback CONFIG` prints the
world's records at any point of the path.

Run from `python/` after `uv sync --frozen`, with `PYTHONPATH=tests`. `create` and
`walk` take an absolute, nonexistent directory; `readback` takes that world's
`science.toml` and opens it without settling an interrupted world transaction. The [guide](../../../../docs/guide.md#a-synthetic-source-checkout-demonstration)
shows the complete invocation. The script closes its attended session before exit.

`estimand.json` is the complete authoring input for this fixture contract. Its
procedure and classification-rule addresses name the exact records bootstrap
holds; they are examples, not substitutes for a program's own scientific facts.
The workflow writes a canned supported verdict. The shipped outcome-file rule
produces no numeric estimates, uncertainty or curves; the estimand reference
`0.5` does not become an observed estimate.


`prepare-phf19` accepts the same pinned inputs as `walk-phf19`. It closes the
preparation writer, checks the ready row and prints the operator's action target.
The prepared fixture leaves the original run, assessment and verification for the
actor. Offline tests use disposable synthetic inputs.
