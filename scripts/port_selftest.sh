#!/usr/bin/env bash
# port_selftest.sh — the by-hand check of a host against the toolchain contract
# of DELTAS Δ503 (D77-D79): the learner's dafny and verus on PATH, uv >= 0.11.0
# with a Python 3.12+ (a system one or `uv python install 3.12`), no course-side
# memory management. Meant for the MacBook
# (macos-arm64); it runs on Linux x86-64 too, as a control. No model is called.
# It changes nothing outside the checkout and its log directory: no shell
# startup file, no PATH beyond its own process.
#
#   PATH=<dafny dir>:<verus dir>:$PATH scripts/port_selftest.sh [--full-ci]
#       [--containers [--build-images]] [--log-dir DIR]
#
# Steps (each prints one PASS/FAIL line; a summary closes the run):
#   1  preflight      platform id, bash, Python >= 3.12, uv; `uv sync --frozen`
#                     when the checkout has no .venv yet
#   2  versions       scripts/vcheck --versions (dafny, verus and their Z3s
#                     against the pins; a mismatch fails this step)
#   3  fingerprint    scripts/vcheck --fingerprint (the Z3 rlimit fingerprint:
#                     a diagnostic, recorded here)
#   4  contract tests tests/wrappers/test_platform.py (version check, UNTRUSTED
#                     marking, the platform helper)
#   5  hook tests     scripts/test_hooks.sh twice: the guard under /bin/bash
#                     (3.2 on macOS) and under PATH's bash (Homebrew's)
#   6  dafny gate     vcheck --gate on the given layers QG_L1-L3
#   7  verus gate     vcheck --gate on the given crates qg_bignat_l1-l3
#   8  sensitive pins pins.py --chapter on the 13 chapter pins whose output
#                     quotes resource counts or an out-of-resource verdict, in
#                     the author's context (CI=true) so every entry runs
#   9  ci (optional)  --full-ci: scripts/ci.sh (the study run, every job)
#  10  images (opt.)  --containers --build-images: sandbox/build-images.sh for
#                     this host's architecture (Δ504: arm64 on the Mac builds
#                     Verus and Z3 4.12.1 from source, a long build; each
#                     step capped at DVL_BUILD_MEMORY, default 12g, which
#                     Docker's VM must have)
#  11  containers     --containers: the harness environment (`uv sync
#      (optional)     --directory harness --frozen`, once: the host's Python
#                     gate runs `uv run --offline --frozen --directory
#                     harness`, which parity's Python files need; checked and
#                     named, never run for you; Δ506), build-images.sh --check, then
#                     tests/acceptance/sandbox_doors.py (Route C, the controls,
#                     the gate, the caps, the watcher, the return path,
#                     exposure, e2e and parity; never canary, which needs the
#                     author's planted trees). Docker running; your model
#                     server answering GET /v1/models on localhost (127.0.0.1)
#                     port 8000 or 8001 for C5 (no model is called; Δ505); parity
#                     starts 16 GB Verus containers, so Docker's VM needs
#                     more than that
# Logs: DIR (default ~/.cache/dafny-verus-learn-0/port-selftest/<UTC stamp>/).
# Exit 0 when every step passed. Memory: one solver job at a time; the course
# caps nothing (D78), so run it on a host with room (a Verus gate can take a
# few GB).

if [ -z "${BASH_VERSINFO:-}" ] || [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
  for _b in /opt/homebrew/bin/bash /usr/local/bin/bash; do
    if [ -x "$_b" ]; then exec "$_b" "$0" "$@"; fi
  done
  echo "port_selftest: needs bash >= 4 (macOS: brew install bash)" >&2
  exit 3
fi
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SCRIPTS="$ROOT/scripts"
FULLCI=0 CONTAINERS=0 BUILD=0 LOG=""
while [ $# -gt 0 ]; do
  case $1 in
    --full-ci) FULLCI=1 ;;
    --containers) CONTAINERS=1 ;;
    --build-images) BUILD=1 ;;
    --log-dir) [ $# -ge 2 ] || { echo "port_selftest: --log-dir needs a directory" >&2; exit 2; }
               LOG="$2"; shift ;;
    -h|--help) sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "usage: scripts/port_selftest.sh [--full-ci] [--containers [--build-images]] [--log-dir DIR]" >&2; exit 2 ;;
  esac
  shift
done
if [ "$BUILD" = 1 ] && [ "$CONTAINERS" = 0 ]; then
  echo "port_selftest: --build-images goes with --containers" >&2; exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="${LOG:-$HOME/.cache/dafny-verus-learn-0/port-selftest/$STAMP}"
mkdir -p "$LOG" && LOG="$(cd "$LOG" && pwd -P)"
export DVL_SCRATCH="$LOG/scratch" DVL_DAFNY_JOBS=1 DVL_VERUS_JOBS=1 PYTHONDONTWRITEBYTECODE=1
unset DVL_TOOLCHAIN_DIR
cd "$ROOT" || exit 1

# The 13 chapter pins whose fence quotes resource counts or an out-of-resource
# verdict (the port audit). On macOS their Z3 builds count exactly as x86's
# (VERSIONS.md §1.5), so they are expected to pass on both.
SENSITIVE=("Q01 p9dv-d" "Q06 p2dv-d p2dv-v" "Q07 p4d c5d"
           "Q09 w1d w1v p1d-pinned p1d-other p2dv-d p2dv-v" "Q10 p1dv-d" "Q18 k3-sweep")

RESULTS=()
FAILED=0
step() {   # NAME LOGFILE CMD... — run CMD, log it, record PASS/FAIL
  local name=$1 log="$LOG/$2.log" rc; shift 2
  printf '== %s\n' "$name"
  { printf '$'; printf ' %q' "$@"; printf '\n'; } >"$log"
  "$@" >>"$log" 2>&1
  rc=$?
  if [ "$rc" = 0 ]; then RESULTS+=("PASS  $name"); else
    RESULTS+=("FAIL  $name   (exit $rc; $log)"); FAILED=$((FAILED + 1)); fi
  tail -n 3 "$log" | sed 's/^/   /'
}

preflight() {
  echo "platform: $(PYTHONPATH="$SCRIPTS" python3 -B -m dvl.host id)"
  echo "bash: $BASH_VERSION; /bin/bash: $(/bin/bash -c 'echo $BASH_VERSION')"
  command -v uv >/dev/null || { echo "uv is not on PATH"; return 1; }
  echo "uv: $(uv --version)"
  if [ ! -x "$ROOT/.venv/bin/python3" ]; then uv sync --frozen || return 1; fi
  echo "python (course env): $("$ROOT/.venv/bin/python3" --version)"
  "$ROOT/.venv/bin/python3" -c 'import sys; sys.exit(sys.version_info < (3, 12))' || return 1
  echo "dafny on PATH: $(command -v dafny || echo MISSING)"
  echo "verus on PATH: $(command -v verus || echo MISSING)"
  command -v dafny >/dev/null && command -v verus >/dev/null
}
step "preflight (platform, bash, uv, Python >= 3.12, tools on PATH)" preflight preflight
export PATH="$ROOT/.venv/bin:$PATH"       # this process only: the course env's python3

step "vcheck --versions (dafny, verus and their Z3s against the pins)" versions \
  "$SCRIPTS/vcheck" --versions
step "vcheck --fingerprint (diagnostic: Z3 rlimit counts as the reference builds)" fingerprint \
  "$SCRIPTS/vcheck" --fingerprint
step "tests/wrappers/test_platform.py (version check, UNTRUSTED marking)" contract-tests \
  python3 -B -m unittest discover -s "$ROOT/tests/wrappers" -p test_platform.py
step "hook tests, guard under /bin/bash ($(/bin/bash -c 'echo $BASH_VERSION'))" hooks-binbash \
  env PATH="/bin:/usr/bin:$PATH" "$SCRIPTS/test_hooks.sh"
step "hook tests, guard under PATH's bash ($(bash -c 'echo $BASH_VERSION'))" hooks-pathbash \
  "$SCRIPTS/test_hooks.sh"
step "dafny gate: given layers QG_L1-L3" dafny-gate "$SCRIPTS/vcheck" --gate \
  dafny/given/Q/QG_L1_BigNat.dfy dafny/given/Q/QG_L2_BigNat.dfy dafny/given/Q/QG_L3_BigNat.dfy
step "verus gate: given crates qg_bignat_l1-l3" verus-gate "$SCRIPTS/vcheck" --gate \
  verus/given/qg_bignat_l1 verus/given/qg_bignat_l2 verus/given/qg_bignat_l3

sensitive() {
  local spec mod e rc=0
  for spec in "${SENSITIVE[@]}"; do
    set -- $spec; mod=$1; shift
    local args=()
    for e in "$@"; do args+=(--entry "$e"); done
    echo "-- $mod $*"
    CI=true "$SCRIPTS/pins.py" --chapter "$mod" "${args[@]}" || rc=1
  done
  return $rc
}
step "the 13 resource-sensitive chapter pins (pins.py --chapter, author context)" sensitive sensitive

if [ "$FULLCI" = 1 ]; then
  step "scripts/ci.sh (study run, every job)" ci "$SCRIPTS/ci.sh" --log-dir "$LOG/ci"
fi

DOORS=(access images controls gate memory pids wall watcher reap return secret exposure e2e parity)
harness_env() {   # the host side of parity's Python files runs uv offline in harness/
  if uv run --offline --frozen --directory "$ROOT/harness" python3 -c 'import fvh, pytest' >/dev/null 2>&1; then
    echo "harness environment: ready (uv run --offline --frozen --directory harness)"
    return 0
  fi
  echo "harness environment: not synced. Run once, online, from the repository root:"
  echo "  uv sync --directory harness --frozen"
  echo "(the host's Python gate runs uv offline in harness/; without it parity's Python files read 'error' at stage cli)"
  return 1
}
if [ "$CONTAINERS" = 1 ]; then
  if [ "$BUILD" = 1 ]; then
    step "sandbox/build-images.sh (this host's architecture: $(PYTHONPATH="$SCRIPTS" python3 -B -c 'from dvl import host; print(host.docker_arch())'))" \
      build-images "$ROOT/sandbox/build-images.sh"
  fi
  step "the harness environment (uv sync --directory harness --frozen, once)" harness-env harness_env
  step "sandbox/build-images.sh --check (the lock names the local images)" images-check \
    "$ROOT/sandbox/build-images.sh" --check
  step "sandbox_doors.py ${DOORS[*]}" doors \
    python3 -B "$ROOT/tests/acceptance/sandbox_doors.py" "${DOORS[@]}" --archive "$LOG/doors"
fi

echo
echo "port_selftest summary ($(PYTHONPATH="$SCRIPTS" python3 -B -m dvl.host id), $STAMP; logs: $LOG)"
for r in "${RESULTS[@]}"; do echo "  $r"; done
if [ "$FAILED" = 0 ]; then
  echo "port_selftest: ALL ${#RESULTS[@]} STEPS PASSED"
  exit 0
fi
echo "port_selftest: $FAILED of ${#RESULTS[@]} steps FAILED"
exit 1
