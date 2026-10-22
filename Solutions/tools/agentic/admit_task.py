#!/usr/bin/env python3
"""Author-only: the admission of a topic (e) course-local task (QPLAN §32.3, §33.4, §34.4;
DELTAS Δ408). Reference class (Solutions/): never learner-visible.

    python3 Solutions/tools/agentic/admit_task.py <form> <answer> [--out JSON]

A task is admitted only when every result below holds, each from the course's own
wrappers, one solver job at a time (they run under the wrappers' caps):

  1 answer-gate      scripts/vcheck --gate --json <answer>: verified, 0 holes
  2 answer-audit     scripts/vaudit --json <answer>: 0 findings
  3 lab-gate         scripts/vcheck --gate --lab-task <form> --json <answer>: verified
                     (the delivery keeps the form's statement and levers)
  4 form-fails       scripts/vcheck --gate --json <form>: failed at the verify stage
                     (an unresolved or unparsed form is no task)
  5 stable           scripts/vcheck --brittleness --json [--solvers] <answer>: stable
                     (Dafny over every bundled Z3: solver diversity, not independent
                     checking)
  6 maxauto (Dafny): the form with its `{:induction false}` removed still fails at
                     verify. Recorded for every task; REQUIRED for a Q32 tranche task
                     (QPLAN §34.4, Δ412): when --tranche is given or the form's path
                     names a q32-t<k> stratum, a Dafny task maxauto closes is not
                     admitted, so the check cannot be skipped

A memory kill (137/143) or the wrappers' wall-clock kill (124) is recorded as such and
the task is not admitted; it is never re-run for a better row. The evidence JSON (the
documents' verdict-level fields, never file text) goes to --out.
Exit 0 admitted, 1 not admitted, 2 usage.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
KILLS = {137: "killed(memory)", 143: "killed(memory)", 124: "killed(wall-clock)"}


def run(argv):
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    try:
        doc = json.loads(p.stdout)
    except json.JSONDecodeError:
        doc = None
    return p.returncode, doc


def fields(doc, keys=("verdict", "stage", "verified_count", "stable")):
    if not isinstance(doc, dict):
        return None
    out = {k: doc.get(k) for k in keys if k in doc}
    if "holes" in doc:
        out["holes"] = len(doc.get("holes") or [])
    if "findings" in doc:
        out["findings"] = len(doc.get("findings") or [])
    return out


WORK = Path.home() / ".cache/dafny-verus-learn-0/author-probes/dv7-build/admit-work"


TRANCHE = re.compile(r"(^|/)q32-t\d+(/|$)")


def admit(form, answer, tranche=False):
    """vcheck refuses a reference path, so the answer is verified as a copy outside the
    tree (the reference class's author scratch), named as the task form is."""
    lang = "dafny" if form.endswith(".dfy") else "verus"
    WORK.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="admit-", dir=WORK))
    copy = tmp / Path(form).name
    copy.write_text((ROOT / answer).read_text(encoding="utf-8"), encoding="utf-8")
    answer_ref, answer = answer, str(copy)
    vc, va = str(ROOT / "scripts/vcheck"), str(ROOT / "scripts/vaudit")
    ev, ok = {"form": form, "answer": answer_ref, "lang": lang}, True

    def step(name, argv, test):
        nonlocal ok
        code, doc = run(argv)
        rec = {"exit": code, "doc": fields(doc)}
        if code in KILLS:
            rec["killed"] = KILLS[code]
        rec["ok"] = code not in KILLS and test(code, doc or {})
        ev[name] = rec
        ok = ok and rec["ok"]

    step("answer-gate", [vc, "--gate", "--json", answer],
         lambda c, d: d.get("verdict") == "verified" and not d.get("holes"))
    step("answer-audit", [va, "--json", answer], lambda c, d: d.get("findings") == [])
    step("lab-gate", [vc, "--gate", "--lab-task", form, "--json", answer],
         lambda c, d: d.get("verdict") == "verified")
    step("form-fails", [vc, "--gate", "--json", form],
         lambda c, d: d.get("verdict") == "failed" and d.get("stage") == "verify")
    step("stable", [vc, "--brittleness", "--json"] + (["--solvers"] if lang == "dafny" else [])
         + [answer], lambda c, d: d.get("stable") is True)
    if lang == "dafny":
        text = (ROOT / form).read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix="dvl-admit-") as d:
            f = Path(d) / Path(form).name
            f.write_text(re.sub(r"\{:induction false\}\s*", "", text), encoding="utf-8")
            code, doc = run([vc, "--gate", "--json", str(f)])
            ev["maxauto"] = {"exit": code, "doc": fields(doc),
                             "fails": isinstance(doc, dict) and doc.get("verdict") == "failed"}
            if code in KILLS:
                ev["maxauto"]["killed"] = KILLS[code]
        if tranche or TRANCHE.search(str(form)):
            ev["maxauto"]["required"] = True
            ev["maxauto"]["ok"] = ev["maxauto"]["fails"]
            ok = ok and ev["maxauto"]["fails"]
    ev["admitted"] = ok
    return ev


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("form")
    ap.add_argument("answer")
    ap.add_argument("--out")
    ap.add_argument("--tranche", action="store_true",
                    help="a Q32 tranche task: maxauto must fail (also inferred from the path)")
    a = ap.parse_args(argv)
    ev = admit(a.form, a.answer, tranche=a.tranche)
    text = json.dumps(ev, indent=1, sort_keys=True)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(f"{a.form}: {'admitted' if ev['admitted'] else 'NOT admitted'} "
          + " ".join(f"{k}={'ok' if v.get('ok') else 'FAIL'}" for k, v in ev.items()
                     if isinstance(v, dict) and "ok" in v)
          + (f" maxauto_fails={ev['maxauto']['fails']}" if "maxauto" in ev else ""))
    return 0 if ev["admitted"] else 1


if __name__ == "__main__":
    sys.exit(main())
