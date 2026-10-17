"""Q12-record-battery.py — record the Q12 retry battery (author-only; QPLAN §30 Q53).

Runs `vcheck --gate` on every candidate of harness/tests/q/fixtures/q12/battery.toml
through the frozen core's HostRunner (one solver job at a time, under the course
tools' caps; the runner's own memory preflight before each job) and writes each
result with fvh.tools.runners.write_recording to

    harness/tests/q/fixtures/q12/rec/<lang>/<goal>-c<n>/vcheck-gate.json

the layout ReplayRunner(fixtures_dir=.../q12/rec) indexes. Results only. A killed
run, or one whose exit is not 0 or 1, is reported and never recorded (as
fvh.tools.record does). It does not change the frozen core: QPLAN §30 Q53 asked
for `fvh.tools.record` to be extended to the battery; this script composes the
core's public runner and writer instead, so the core stays as built.

Run from the course root of the authoring worktree:
    PYTHONPATH=harness python3 -B Solutions/plans/Q12-record-battery.py
(add `--only D1-c2 ...` to re-record some). Exit 0 when every planned result was
recorded, 1 otherwise.
"""

import argparse
import sys
import tomllib
from pathlib import Path

from fvh.tools import runners as R

ROOT = Path(__file__).resolve().parents[2]
BATTERY = ROOT / "harness/tests/q/fixtures/q12/battery.toml"
OUT = ROOT / "harness/tests/q/fixtures/q12/rec"
INSTRUMENT = "vcheck --gate"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args(argv)
    with open(BATTERY, "rb") as f:
        goals = tomllib.load(f)["goal"]
    runner = R.HostRunner(ROOT)
    bad = 0
    for g in goals:
        for i, cand in enumerate(g["candidates"], 1):
            fid = f"{g['id']}-c{i}"
            if a.only is not None and fid not in a.only:
                continue
            res = runner.execute(INSTRUMENT, cand)
            if res.killed is not None or res.exit_code not in (0, 1):
                print(f"{g['lang']}/{fid}: NOT recorded (exit {res.exit_code}, "
                      f"killed {res.killed})", flush=True)
                bad += 1
                continue
            path = R.recording_path(OUT, g["lang"], fid, INSTRUMENT)
            R.write_recording(path, res, runner.argv(INSTRUMENT, cand))
            doc = res.document if isinstance(res.document, dict) else {}
            print(f"{g['lang']}/{fid}: exit {res.exit_code}, stage {doc.get('stage')}, "
                  f"verdict {doc.get('verdict')}, holes {len(doc.get('holes') or [])}",
                  flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
