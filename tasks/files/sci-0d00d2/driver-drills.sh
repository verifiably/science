#!/usr/bin/env bash
# The three recovery drills of milestone plan Task 5 Step 3, each run's combined
# output captured beside its state, on fresh replicas (ra, rb) and on r3 for (c).
#   drills.sh <wt> <beliefs> <task dir> <reference state> <reference run>
set -u
WT=$1 BELIEFS=$2 T=$3 REF_STATE=$4 REF_RUN=$5
PY=$WT/python/.venv/bin/python
D=$T/driver
run() {  # run <capture file> <args...>: prints and records the exit status
  local out=$1; shift
  "$PY" "$@" >"$out" 2>&1
  local rc=$?
  echo "exit $rc" >>"$out"
  echo "$(basename "$out"): exit $rc"
  return 0
}
latest() { ls -d "$1"/runs/*/ | sort | tail -1; }

# (a) interruption between a selection and its mint
run "$T/ra-build-stdout.txt" "$D/rehearsal.py" "$WT" "$BELIEFS" "$T" ra --build-only
run "$T/ra-run1-stdout.txt" "$D/walk.py" "$T/state/ra" --stop-after W3.select.health
run "$T/ra-run2-stdout.txt" "$D/walk.py" "$T/state/ra"
run "$T/ra-invariants-stdout.txt" "$D/invariants.py" "$REF_STATE" "$REF_RUN" "$T/state/ra" "$(latest "$T/state/ra")"

# (b) a mint whose completion was not journaled
KEY=W3.question.evidence-bound-terms
run "$T/rb-build-stdout.txt" "$D/rehearsal.py" "$WT" "$BELIEFS" "$T" rb --build-only
run "$T/rb-run1-stdout.txt" "$D/walk.py" "$T/state/rb" --crash-before-record "$KEY"
run "$T/rb-run2-stdout.txt" "$D/walk.py" "$T/state/rb"
run "$T/rb-check-stdout.txt" "$D/walk.py" "$T/state/rb" --check "$KEY"
ADDRESS=$(grep -o "coord:[0-9a-f]*/[0-9a-f]*" "$T/rb-check-stdout.txt" | head -1)
run "$T/rb-reconcile-stdout.txt" "$D/walk.py" "$T/state/rb" --reconcile "$KEY=$ADDRESS"
run "$T/rb-run3-stdout.txt" "$D/walk.py" "$T/state/rb"
run "$T/rb-invariants-stdout.txt" "$D/invariants.py" "$REF_STATE" "$REF_RUN" "$T/state/rb" "$(latest "$T/state/rb")"

# (c) a fresh journal against a completed world, twice
run "$T/rc-run1-stdout.txt" "$D/walk.py" "$REF_STATE" --new-run
run "$T/rc-run2-stdout.txt" "$D/walk.py" "$REF_STATE"
