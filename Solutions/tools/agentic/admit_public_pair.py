#!/usr/bin/env python3
"""Author-only: the admission of a Q33 public dev pair (QPLAN §35.4; DELTAS Δ416). Reference
class (Solutions/): never learner-visible. No model is called.

    python3 Solutions/tools/agentic/admit_public_pair.py --form F --refprog P --name N --lang L [--out JSON]

The form is a public task in Lab 2's form (scripts/dvl/lab2pub.py's transforms: the
specification and proofs removed, the prose and the code kept, an empty witness); the
reference program is the source's answer with the author's witness call. Admitted only when,
each from the course's wrappers, one solver job at a time:

  1 form-resolves  `vcheck --json` on the form reaches the verify stage (C4)
  2 ref-gate       the reference program passes `vcheck --gate`: verified, 0 holes
  3 ref-lab-gate   and `vcheck --gate --lab-task <form>`: it is a delivery of the form (C6)
  4 ref-audit      `vaudit` on it: 0 findings
  5 ref-stable     `vcheck --brittleness` [--solvers]: stable (C5)
  6 base           the frozen oracles' context lemma over the reference's definitions verifies
  7 not-vacuous    the frozen oracles' vacuity check on the reference statement: "failed"
  8 self-faithful  the reference statement judged against itself: FAITHFUL

Steps 6-8 build the oracles' Task from the reference program as the grader's `truthcheck
judge` does (dvl.judge.candidate: the target's declaration removed, its parameters and
results, its requires and ensures) and run Solutions/harness/q/fvh_q/oracles.py host-side
with a runner that calls `scripts/vcheck --gate --json` on scratch copies (the coordinator's
D3). A kill (137/143, 124) is recorded and the pair is not admitted; nothing is re-run.
Exit 0 admitted, 1 not admitted, 2 usage.
"""

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
KILLS = {137: "killed(memory)", 143: "killed(memory)", 124: "killed(wall-clock)"}
WORK = Path.home() / ".cache/dafny-verus-learn-0/author-probes/dv7-build/admit-work"


def oracles():
    sys.path.insert(0, str(ROOT / "harness"))
    spec = importlib.util.spec_from_file_location(
        "q15_reference_oracles", ROOT / "Solutions/harness/q/fvh_q/oracles.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def vrun(argv):
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


def admit(form, refprog, name, lang):
    sys.path.insert(0, str(ROOT / "scripts"))
    from dvl import judge as J
    O = oracles()
    ext = ".dfy" if lang == "dafny" else ".rs"
    WORK.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="pubpair-", dir=WORK))
    fcopy, rcopy = tmp / f"form{ext}", tmp / f"reference{ext}"
    fcopy.write_text(Path(form).read_text(encoding="utf-8"), encoding="utf-8")
    rtext = Path(refprog).read_text(encoding="utf-8")
    rcopy.write_text(rtext, encoding="utf-8")
    vc, va = str(ROOT / "scripts/vcheck"), str(ROOT / "scripts/vaudit")
    ev, ok = {"name": name, "lang": lang, "form": str(form), "reference": str(refprog)}, True

    def step(key, argv, test):
        nonlocal ok
        code, doc = vrun(argv)
        rec = {"exit": code, "doc": fields(doc)}
        if code in KILLS:
            rec["killed"] = KILLS[code]
        rec["ok"] = code not in KILLS and isinstance(doc, dict) and bool(test(code, doc))
        ok = ok and rec["ok"]
        ev[key] = rec

    step("form-resolves", [vc, "--json", str(fcopy)], lambda c, d: d.get("stage") == "verify")
    step("ref-gate", [vc, "--gate", "--json", str(rcopy)],
         lambda c, d: d.get("verdict") == "verified" and not d.get("holes"))
    step("ref-lab-gate", [vc, "--gate", "--lab-task", str(form), "--json", str(rcopy)],
         lambda c, d: d.get("verdict") == "verified")
    step("ref-audit", [va, "--json", str(rcopy)], lambda c, d: d.get("findings") == [])
    step("ref-stable", [vc, "--brittleness", "--json"] + (["--solvers"] if lang == "dafny" else [])
         + [str(rcopy)], lambda c, d: d.get("stable") is True)

    killed = []

    def run(instrument, path):
        code, doc = vrun([vc, "--gate", "--json", str(path)])
        if code in KILLS:
            killed.append(KILLS[code])
        return SimpleNamespace(document=doc, exit_code=code, killed=KILLS.get(code))

    try:
        cand = J.candidate(rtext, lang, name)
    except J.JudgeInputError as e:
        ev["candidate"] = {"ok": False, "why": str(e)}
        ev["admitted"] = False
        return ev
    task = O.Task(name, lang, name, tuple(tuple(p) for p in cand["params"]),
                  tuple(tuple(r) for r in cand["results"]), "", cand["header"], cand["footer"])
    ref = O.Spec(task, tuple(cand["requires"]), tuple(cand["ensures"]))
    wd = tmp / "oracle"
    base_name = "DvlJudgeBase" if lang == "dafny" else "dvl_judge_base"
    base = O.outcome(run("vcheck --gate", O.write_target(O.render_lemma(task, base_name, (), (), ()),
                                                         lang, wd)))
    ev["base"] = {"outcome": base, "ok": base == "proved"}
    ok = ok and base == "proved"
    vac = O.vacuity(ref, run=run, workdir=wd)
    ev["not-vacuous"] = {"vacuity": vac, "ok": vac == "failed"}
    ok = ok and vac == "failed"
    imp = O.implication(ref, ref, run=run, workdir=wd)
    verdict = O.classify(imp, vac).value
    ev["self-faithful"] = {"implication": [imp.spec_implies_ref, imp.ref_implies_spec],
                           "verdict": verdict, "ok": verdict == "faithful"}
    ok = ok and verdict == "faithful"
    ev["reference_statement"] = {"requires": list(cand["requires"]), "ensures": list(cand["ensures"])}
    if killed:
        ev["killed"] = killed
        ok = False
    ev["admitted"] = ok
    return ev


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True)
    ap.add_argument("--refprog", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--lang", required=True, choices=("dafny", "verus"))
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    ev = admit(a.form, a.refprog, a.name, a.lang)
    text = json.dumps(ev, indent=1, sort_keys=True)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(f"{a.name}: {'admitted' if ev['admitted'] else 'NOT admitted'} "
          + " ".join(f"{k}={'ok' if v.get('ok') else 'FAIL'}" for k, v in sorted(ev.items())
                     if isinstance(v, dict) and "ok" in v))
    return 0 if ev["admitted"] else 1


if __name__ == "__main__":
    sys.exit(main())
