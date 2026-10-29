#!/usr/bin/python3
"""The Z3 rlimit fingerprint at image build time (DELTAS Δ504; the course's
diagnostic is scripts/vcheck --fingerprint, dvl.z3print).

    z3fp.py Z3 VERSION FPDIR

Runs every query of FPDIR/queries/ (tests/fingerprint/z3/ as staged) through
the binary Z3 and compares each query's answers and `(get-info :rlimit)`
counts with FPDIR/expected/VERSION.tsv, the reference build's. Exit 0 when all
match, 1 otherwise (the image build fails). Standard library only.
"""

import re
import subprocess
import sys
from pathlib import Path

RESULT = re.compile(r"^(sat|unsat|unknown|timeout)$", re.M)
RLIMIT = re.compile(r"^\(:rlimit (\d+)\)", re.M)


def measure(z3, queries):
    out = {}
    for f in sorted(Path(queries).glob("*.smt2")):
        p = subprocess.run([z3, "-T:600", str(f)], capture_output=True, text=True)
        text = p.stdout + p.stderr
        res = "".join(m + "," for m in RESULT.findall(text)) or "-"
        rl = "".join(m + "," for m in RLIMIT.findall(text)) or "-"
        out[f.name] = (res, rl)
    return out


def expected(path):
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 3:
            out[parts[0]] = (parts[1], parts[2])
    return out


def main(argv):
    if len(argv) != 4:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    z3, version, fp = argv[1], argv[2], Path(argv[3])
    want = expected(fp / "expected" / f"{version}.tsv")
    got = measure(z3, fp / "queries")
    bad = [q for q in sorted(set(want) | set(got)) if want.get(q) != got.get(q)]
    for q in bad:
        print(f"z3fp: {q}: got {got.get(q)}, reference {want.get(q)}", file=sys.stderr)
    print(f"z3fp: {z3} (Z3 {version}): {len(want) - len(bad)} of {len(want)} queries match"
          + (" — the fingerprint DIFFERS" if bad else ""), file=sys.stderr)
    return 1 if bad or not want else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
