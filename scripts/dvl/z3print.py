"""dvl.z3print — the Z3 rlimit fingerprint (DELTAS Δ503; the port audit).

A Z3 binary's fingerprint is its answer (sat/unsat/unknown) and its rlimit
count, `(get-info :rlimit)`, on each query of tests/fingerprint/z3/queries/:
29 SMT-LIB files that Dafny 4.11.0 wrote for the course's given layers L1-L2
and for three out-of-resource specimens at seeds 1-3, at the course resource
limit (several end exactly at it). The port audit found every build of one Z3
version measured, vendor or Dafny's own, on x86-64 and on aarch64, to give the identical
fingerprint, while 4.12.1 and 4.14.1 differ on most queries. So a solver
whose fingerprint equals tests/fingerprint/z3/expected/<version>.tsv counts
exactly what the reference build counts, and every pinned resource figure and
out-of-resource verdict reproduces with it.

`get_toolchain.sh <tool> --fingerprint` checks an install's bundled solvers
against it, and scripts/port_selftest.sh runs that on macOS. All queries run as ONE capped job (dvl.common.run_capped, 4 GB).

  python3 -m dvl.z3print check   <z3> <version>   exit 0 match, 1 differ, 2 usage
  python3 -m dvl.z3print measure <z3>             print the fingerprint (author)
"""

from __future__ import annotations

import sys
from pathlib import Path

from dvl import common

FP_DIR = common.REPO_ROOT / "tests" / "fingerprint" / "z3"
QUERIES = FP_DIR / "queries"
EXPECTED = FP_DIR / "expected"
MEM_GB = 4
PER_QUERY_S = 600
TOTAL_S = 7200

# One query per line: "<name> <results,> <rlimits,>" (the probe's format).
RUNNER = r"""
z="$1"; d="$2"; t="$3"
for f in "$d"/*.smt2; do
  out=$("$z" -T:"$t" "$f" 2>&1)
  res=$(printf '%s\n' "$out" | grep -E '^(sat|unsat|unknown|timeout)$' | tr '\n' ',')
  rl=$(printf '%s\n' "$out" | grep -oE '^\(:rlimit [0-9]+\)' | grep -oE '[0-9]+' | tr '\n' ',')
  printf '%s %s %s\n' "$(basename "$f")" "${res:--}" "${rl:--}"
done
"""


def measure(z3):
    """{query: (results, rlimits)} of binary `z3`, run as one capped job."""
    z3 = Path(z3).resolve()
    if not z3.is_file():
        raise common.DvlError(f"no solver at {z3}")
    rc, so, se = common.run_capped(["sh", "-c", RUNNER, "z3print", str(z3), str(QUERIES),
                                    str(PER_QUERY_S)], MEM_GB, TOTAL_S, pool="z3print")
    if common.is_killed(rc):
        raise common.DvlError(f"the fingerprint job was killed(memory) (exit {rc})")
    if rc != 0:
        raise common.DvlError(f"the fingerprint job failed (exit {rc}; {se})")
    return parse(Path(so).read_text(encoding="utf-8"))


def parse(text):
    out = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 3:
            out[parts[0]] = (parts[1], parts[2])
    return out


def expected(version):
    path = EXPECTED / f"{version}.tsv"
    if not path.is_file():
        raise common.DvlError(f"no reference fingerprint for Z3 {version} ({path})")
    return parse(path.read_text(encoding="utf-8"))


def compare(got, want):
    """[(query, got, want)] of the queries that differ (a missing one included)."""
    bad = []
    for q in sorted(set(got) | set(want)):
        if got.get(q) != want.get(q):
            bad.append((q, got.get(q), want.get(q)))
    return bad


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if len(args) == 3 and args[0] == "check":
            want = expected(args[2])
            got = measure(args[1])
            bad = compare(got, want)
            if bad:
                for q, g, w in bad:
                    print(f"z3print: {q}: got {g}, reference {w}", file=sys.stderr)
                print(f"z3print: {args[1]}: fingerprint DIFFERS from Z3 {args[2]}'s on "
                      f"{len(bad)} of {len(want)} queries", file=sys.stderr)
                return 1
            print(f"z3print: {args[1]}: fingerprint matches Z3 {args[2]} on all {len(want)} "
                  "queries", file=sys.stderr)
            return 0
        if len(args) == 2 and args[0] == "measure":
            for q, (r, l) in sorted(measure(args[1]).items()):
                print(f"{q} {r} {l}")
            return 0
    except common.DvlError as e:
        print(f"z3print: {e}", file=sys.stderr)
        return 1
    print(__doc__.split("\n\n")[-1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
