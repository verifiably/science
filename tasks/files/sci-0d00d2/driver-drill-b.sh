#!/usr/bin/env bash
# Drill (b) on an rb state whose genesis completed: declare and freeze if needed,
# then crash-before-record, exit 3, --check, --reconcile, resume, invariants.
#   drill-b.sh <wt> <task dir> <reference state> <reference run>
set -u
WT=$1 T=$2 REF_STATE=$3 REF_RUN=$4
PY=$WT/python/.venv/bin/python
D=$T/driver
KEY=W3.question.evidence-bound-terms
run() {
  local out=$1; shift
  "$PY" "$@" >"$out" 2>&1
  local rc=$?
  echo "exit $rc" >>"$out"
  echo "$(basename "$out"): exit $rc"
}
[ -f "$T/state/rb/declared.json" ] || run "$T/rb-declare-retry-stdout.txt" "$D/declare.py" "$T/state/rb"
[ -d "$T/state/rb/queries" ] || run "$T/rb-terms-stdout.txt" "$D/terms.py" "$T/state/rb"
run "$T/rb-run1-stdout.txt" "$D/walk.py" "$T/state/rb" --crash-before-record "$KEY"
run "$T/rb-run2-stdout.txt" "$D/walk.py" "$T/state/rb"
run "$T/rb-check-stdout.txt" "$D/walk.py" "$T/state/rb" --check "$KEY"
ADDRESS=$(grep -o "coord:[0-9a-f]*/[0-9a-f]*" "$T/rb-check-stdout.txt" | head -1)
echo "address $ADDRESS"
run "$T/rb-reconcile-stdout.txt" "$D/walk.py" "$T/state/rb" --reconcile "$KEY=$ADDRESS"
run "$T/rb-run3-stdout.txt" "$D/walk.py" "$T/state/rb"
LATEST=$(ls -d "$T"/state/rb/runs/*/ | sort | tail -1)
run "$T/rb-invariants-stdout.txt" "$D/invariants.py" "$REF_STATE" "$REF_RUN" "$T/state/rb" "$LATEST"
