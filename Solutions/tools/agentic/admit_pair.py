#!/usr/bin/env python3
"""Author-only: the admission of a Q33 statement pair (QPLAN §35.4; DELTAS Δ414). Reference
class (Solutions/): never learner-visible. No model is called.

    python3 Solutions/tools/agentic/admit_pair.py <pair.json> [--out JSON]

A pair is a Lab-2-form task (prose, definitions, an implementation with no specification,
an empty witness), its reference statement and witness call, two faithful alternatives and
one near-miss. It is admitted only when every result below holds, each from the course's
own wrappers, one solver job at a time:

  1 form-verifies    the task form as shipped passes `vcheck --gate` (it states nothing)
  2 ref-gate         the reference program (form + reference statement + witness call)
                     passes `vcheck --gate`: verified, 0 holes
  3 ref-audit        `vaudit` on the reference program: 0 findings
  4 ref-stable       `vcheck --brittleness` [--solvers] on it: stable
  5 not-vacuous      the frozen oracles' vacuity check on the reference: "failed"
  6 self-faithful    the reference judged against itself: FAITHFUL
  7 alternatives     each faithful alternative judged FAITHFUL
  8 near-miss        the near-miss judged as intended (WEAK or STRONG)

Steps 5-8 are the frozen Q15 reference oracles (Solutions/harness/q/fvh_q/oracles.py:
vacuity, implication, classify; the judge's own oracles, Δ220), run host-side with a
runner that calls `scripts/vcheck --gate --json` on scratch copies. This host run is the
admission check (the coordinator's D3); the in-container `truthcheck judge` pass is a
recorded re-check at W1b. A memory kill (137/143) or the clock (124) is recorded as such
and the pair is not admitted; it is never re-run for a better row.
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


def admit(pair):
    O = oracles()
    lang = pair["lang"]
    ext = ".dfy" if lang == "dafny" else ".rs"
    t = pair["task"]
    task = O.Task(id=pair["id"], lang=lang, name=t["name"],
                  params=tuple(tuple(p) for p in t["params"]),
                  results=tuple(tuple(r) for r in t["results"]),
                  body=t["body"], header=t["header"], footer=t["footer"])
    spec = lambda s: O.Spec(task, tuple(s.get("requires", ())), tuple(s.get("ensures", ())))
    ref = spec(pair["reference"])
    WORK.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="pair-", dir=WORK))
    vc, va = str(ROOT / "scripts/vcheck"), str(ROOT / "scripts/vaudit")
    ev, ok = {"id": pair["id"], "lang": lang}, True

    def write(name, text):
        p = tmp / f"{name}{ext}"
        p.write_text(text, encoding="utf-8")
        return str(p)

    def step(name, argv, test):
        nonlocal ok
        code, doc = vrun(argv)
        rec = {"exit": code, "doc": fields(doc)}
        if code in KILLS:
            rec["killed"] = KILLS[code]
        rec["ok"] = code not in KILLS and isinstance(doc, dict) and bool(test(code, doc))
        ok = ok and rec["ok"]
        ev[name] = rec

    form = write("form", O.render_program(task, O.Spec(task), task.body))
    refp = O.render_program(task, ref, task.body).replace(t["footer"], pair["witness_footer"])
    assert refp.endswith(pair["witness_footer"]), "the witness footer must replace the task's footer"
    refprog = write("reference", refp)
    step("form-verifies", [vc, "--gate", "--json", form],
         lambda c, d: d.get("verdict") == "verified" and not d.get("holes"))
    step("ref-gate", [vc, "--gate", "--json", refprog],
         lambda c, d: d.get("verdict") == "verified" and not d.get("holes"))
    step("ref-audit", [va, "--json", refprog], lambda c, d: d.get("findings") == [])
    step("ref-stable", [vc, "--brittleness", "--json"] + (["--solvers"] if lang == "dafny" else [])
         + [refprog], lambda c, d: d.get("stable") is True)

    killed = []

    def run(instrument, path):
        code, doc = vrun([vc, "--gate", "--json", str(path)])
        if code in KILLS:
            killed.append(KILLS[code])
        return SimpleNamespace(document=doc, exit_code=code,
                               killed=KILLS.get(code))

    wd = tmp / "oracle"

    def judge(s):
        vac = O.vacuity(s, run=run, workdir=wd)
        imp = O.implication(s, ref, run=run, workdir=wd)
        return vac, imp, O.classify(imp, vac).value

    vac = O.vacuity(ref, run=run, workdir=wd)
    ev["not-vacuous"] = {"vacuity": vac, "ok": vac == "failed"}
    ok = ok and vac == "failed"
    _, imp, verdict = judge(ref)
    ev["self-faithful"] = {"implication": [imp.spec_implies_ref, imp.ref_implies_spec],
                           "verdict": verdict, "ok": verdict == "faithful"}
    ok = ok and verdict == "faithful"
    for i, alt in enumerate(pair["alternatives"], 1):
        v, imp, verdict = judge(spec(alt))
        good = verdict == alt["intended"] == "faithful"
        ev[f"alternative-{i}"] = {"vacuity": v, "implication": [imp.spec_implies_ref, imp.ref_implies_spec],
                                  "verdict": verdict, "intended": alt["intended"], "ok": good}
        ok = ok and good
    nm = pair["near_miss"]
    v, imp, verdict = judge(spec(nm))
    good = verdict == nm["intended"] and nm["intended"] in ("weak", "strong")
    ev["near-miss"] = {"vacuity": v, "implication": [imp.spec_implies_ref, imp.ref_implies_spec],
                       "verdict": verdict, "intended": nm["intended"], "ok": good}
    ok = ok and good
    if killed:
        ev["killed"] = killed
        ok = False
    ev["admitted"] = ok
    return ev


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pair")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    pair = json.loads(Path(a.pair).read_text(encoding="utf-8"))
    ev = admit(pair)
    text = json.dumps(ev, indent=1, sort_keys=True)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(f"{pair['id']}: {'admitted' if ev['admitted'] else 'NOT admitted'} "
          + " ".join(f"{k}={'ok' if v.get('ok') else 'FAIL'}" for k, v in sorted(ev.items())
                     if isinstance(v, dict) and "ok" in v))
    return 0 if ev["admitted"] else 1


if __name__ == "__main__":
    sys.exit(main())
