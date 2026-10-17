"""Q18-record-gate.py — record the gate v2 fixtures' instrument results (author-only; QPLAN §28.4).

Runs, on every delivery of harness/tests/q/fixtures/q18/set.toml, the instruments a correct gate v2
runs on it ("vcheck --gate", "vaudit", "seed-rerun", and "specfreeze --check" where the delivery
brings its frozen companion) through the frozen core's HostRunner (one solver job at a time, under
the course tools' caps; the runner's own memory preflight before each job), and writes each result
with fvh.tools.runners.write_recording to

    harness/tests/q/fixtures/q18/rec/<lang>/<ID>/<slug(instrument)>.json

the layout ReplayRunner(fixtures_dir=.../q18/rec) indexes. Results only, never a label (the labels
are the set file's, read by the evaluator alone). A killed run, or one whose exit is not 0 or 1, is
reported and never recorded (as fvh.tools.record does).

With --k2-record it also writes K2's own delivered record, harness/tests/q/fixtures/q18/K2/
verification.json: the document of `scripts/vcheck --json --symbol add_one` on K2 (a learner-loop
run of one function, the kind of record a delivery might bring as its evidence), redacted as the
runner redacts a document (<root>, <scratch>, ~).

It does not change the frozen core: it composes the core's public runner and writer, as
Solutions/plans/Q12-record-battery.py does.

Run from the course root of the authoring worktree:
    PYTHONPATH=harness python3 -B Solutions/plans/Q18-record-gate.py [--only K3 ...] [--k2-record]
Exit 0 when every planned result was recorded, 1 otherwise.
"""

import argparse
import json
import sys
import tempfile
import tomllib
from pathlib import Path

from fvh.tools import runners as R

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "harness/tests/q/fixtures/q18"
OUT = FIX / "rec"


def frozen_companion(d):
    """The frozen statement companion a delivery brings, or None."""
    for p in R.command("specfreeze --check", d["target"], lang=d["lang"])[1:]:
        if p.startswith("--") or p == d["target"] or p.endswith("/src/lib.rs"):
            continue
        return p if p in d["files"] else None
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--k2-record", action="store_true")
    a = ap.parse_args(argv)
    with open(FIX / "set.toml", "rb") as f:
        deliveries = tomllib.load(f)["delivery"]
    runner = R.HostRunner(ROOT)
    bad = 0
    for d in deliveries:
        if a.only is not None and d["id"] not in a.only:
            continue
        names = ["vcheck --gate", "vaudit", "seed-rerun"]
        if frozen_companion(d):
            names.insert(2, "specfreeze --check")
        for name in names:
            res = runner.execute(name, d["target"])
            if res.killed is not None or res.exit_code not in (0, 1):
                print(f"{d['lang']}/{d['id']} {name}: NOT recorded (exit {res.exit_code}, "
                      f"killed {res.killed})", flush=True)
                bad += 1
                continue
            path = R.recording_path(OUT, d["lang"], d["id"], name)
            R.write_recording(path, res, runner.argv(name, d["target"]))
            doc = res.document if isinstance(res.document, dict) else {}
            print(f"{d['lang']}/{d['id']} {name}: exit {res.exit_code}, verdict "
                  f"{doc.get('verdict', doc.get('verdicts'))}, stable {doc.get('stable')}",
                  flush=True)
    if a.k2_record:
        scratch = Path(tempfile.mkdtemp(prefix="fvh-tool-", dir=R._scratch_base(ROOT)))
        argv = [sys.executable, "-B", str(ROOT / "scripts/vcheck"), "--json", "--symbol",
                "add_one", "harness/tests/q/fixtures/q18/K2"]
        rc, out, err, timed_out = R._spawn(argv, ROOT, R._tool_env(scratch), 600)
        if timed_out or rc not in (0, 1):
            print(f"K2 record: NOT written (exit {rc}, timed out {timed_out})")
            bad += 1
        else:
            doc = R._redact_json(json.loads(out), R._redactor(ROOT, scratch))
            (FIX / "K2/verification.json").write_text(
                json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"K2 record: exit {rc}, verdict {doc.get('verdict')}, cmd partial: "
                  f"{[x for x in doc.get('cmd', []) if x.startswith('--verify')]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
