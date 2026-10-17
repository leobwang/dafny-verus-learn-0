#!/usr/bin/env bash
# Full DV0 measurement pipeline for the Dafny BigNat spike (author-only tooling).
# Safe when run bare: GATE_WORKERS defaults to 3 and DAFNY_CORES to 2 (6 z3 at most).
# Intended invocation (CLAUDE.md "Resources"; this lane's share is 16 GB):
#   systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 \
#     env GATE_WORKERS=3 DAFNY_CORES=2 Solutions/spikes/dafny/tools/run_all.sh
set -u
export GATE_WORKERS="${GATE_WORKERS:-3}" DAFNY_CORES="${DAFNY_CORES:-2}"
cd "$(dirname "$0")"
for step in ref units determinism seeds gate escalate gateseeds maxseeds test summary; do
  echo "== $(date -Is) step $step (workers=$GATE_WORKERS cores=$DAFNY_CORES)"
  python3 gate.py "$step"
  rc=$?
  echo "== $(date -Is) step $step exit=$rc"
  if [ "$rc" -eq 137 ] || [ "$rc" -eq 143 ]; then
    echo "killed(memory) at step $step"; exit "$rc"
  fi
done
echo "== ALL DONE $(date -Is)"
