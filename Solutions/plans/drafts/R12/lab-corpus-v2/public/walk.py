"""Lab alpha public slice: run the pre-registered walk of WALK.md. Author-side.

  walk.py prepare    C0-C3 (static) and materialization for the first 160 walk members
  walk.py admit N    the admission tool on the prepared members, N at a time (each job takes
                     a solver slot through /tmp/dvl0-dvr4-labalpha/slot.sh)
  walk.py select     the walk in order: the first 45 members passing every check (C3's
                     dynamic part, distinctness from earlier accepted members, applied here);
                     writes C0-C7.jsonl, installs the taken forms under bench/local/r/labalpha
                     and their family records

Admission jobs are independent of each other, so they may run in any order; the selection
reads them in walk order, which is the sequential walk's result.
"""
import concurrent.futures as cf
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
ROOT = HERE.parents[5]
ORDER = json.loads((HERE / "ORDER.json").read_text())
STATE = Path("/tmp/dvl0-dvr4-labalpha/l4state")
LIMIT_WALK, LIMIT_TAKE = 160, 45
SHORT = {"dafnybench": "db", "humaneval-verus": "hev"}
LANG = {"dafnybench": "dafny", "humaneval-verus": "verus"}
EXT = {"dafnybench": ".dfy", "humaneval-verus": ".rs"}
TOOL_TO_C = {"original-model-code-frame": "C7", "reference-gate": "C6", "reference-three-seeds": "C5",
             "baseline-proof-fails": "tool:baseline-proof-fails", "audit-clean": "tool:audit-clean",
             "max-auto-empty-fails": "tool:max-auto-empty-fails", "wrong-hints-fail": "tool:wrong-hints-fail"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def he_id(set_, task):
    if set_ == "humaneval-verus":
        m = re.match(r"human_eval_(\d+)", task)
    else:
        m = re.match(r"llm-verified-eval_.*_dafny_(\d+)\.dfy$", task)
    return int(m.group(1)) if m else None


def static_excluded():
    pools = tomllib.loads((ROOT / "bench/public/POOLS.toml").read_text())
    ids = {int(m.group(1)) for d in pools.get("draw", []) for c in d.get("cards", [])
           if (m := re.fullmatch(r"[dv]p\d+-he(\d+)", c))}
    tasks = {(d["set"], t) for d in pools.get("draw", []) for t in d.get("drawn", [])}
    res = json.loads((ROOT / "bench/local/r/labalpha-smoke/UNUSED_PUBLIC.json").read_text())
    ids |= set(res.get("excluded_humaneval_ids", []))
    for row in res.get("selected", []):
        tasks.add((row["set"], row["task"]))
        h = he_id(row["set"], row["task"])
        if h is not None:
            ids.add(h)
    return ids, tasks


def members():
    out = []
    for k, (set_, task) in enumerate(ORDER["walk"][:LIMIT_WALK]):
        out.append({"k": k, "set": set_, "task": task, "id": f"pub-{SHORT[set_]}-{k:03d}"})
    return out


def prepare():
    STATE.mkdir(exist_ok=True)
    ids, tasks = static_excluded()
    pools = {p["set"]: p for p in tomllib.loads((ROOT / "bench/public/POOLS.toml").read_text())["pool"]}
    rows = []
    for m in members():
        row = dict(m)
        set_, task = m["set"], m["task"]
        ans = ROOT / "bench/public" / set_ / "answers" / task
        row["answer_sha256"] = sha(ans)
        row["pool_sha256"] = pools[set_]["pool_sha256"]
        row["set_sha256"] = pools[set_]["set_sha256"]
        row["checks"] = {}
        row["flags"] = {}
        # C0 licence
        if set_ == "humaneval-verus":
            row["checks"]["C0"] = "pass: MIT (set licence; HumanEval prompts MIT)"
        else:
            row["checks"]["C0"] = "pass: Apache-2.0 (set licence)"
            row["flags"]["c0_flag"] = "per-file upstream licence not recorded"
        # C1 form
        work = STATE / m["id"]
        if work.exists():
            shutil.rmtree(work)
        p = subprocess.run([sys.executable, "-B", str(HERE / "materialize.py"), set_, task, m["id"], str(work)],
                           capture_output=True, text=True)
        try:
            res = json.loads(p.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            res = {"c1": "materializer error: " + (p.stderr.strip().splitlines() or ["?"])[-1][:300]}
        if "c1" in res:
            row["result"], row["failed"], row["reason"] = "skipped", "C1", res["c1"]
            rows.append(row)
            continue
        rec = json.loads((work / "materialize.json").read_text())
        row["checks"]["C1"] = f"pass: target {rec['target']}, {rec['sites']} sites, {len(rec['kept_annotations'])} annotations kept as provided"
        row["flags"].update(rec["flags"])
        row["target"], row["sites"] = rec["target"], rec["sites"]
        # C2 prose
        if set_ == "humaneval-verus":
            if "### PROMPT" not in ans.read_text():
                row["result"], row["failed"], row["reason"] = "skipped", "C2", "no HumanEval PROMPT block"
                rows.append(row)
                continue
            row["checks"]["C2"] = "pass: PROMPT block present"
        else:
            row["checks"]["C2"] = "n/a (dafnybench has no prose prompt)"
        # C3 static part
        h = he_id(set_, task)
        row["humaneval_id"] = h
        if (set_, task) in tasks:
            row["result"], row["failed"], row["reason"] = "skipped", "C3", "an earlier draw or R12's prior reservation holds this task"
        elif h is not None and h in ids:
            row["result"], row["failed"], row["reason"] = "skipped", "C3", f"HumanEval/{h} is an earlier draw's or R12's prior reservation's"
        else:
            row["result"] = "prepared"
        rows.append(row)
    (STATE / "prepared.json").write_text(json.dumps(rows, indent=1) + "\n")
    print(sum(r["result"] == "prepared" for r in rows), "prepared of", len(rows))


def admit_one(row):
    set_, tid = row["set"], row["id"]
    work = STATE / tid
    form = work / (tid + EXT[set_])
    ev = V2 / tid
    ev.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(work / "hints.json", ev / "hints.json")
    shutil.copyfile(work / "materialize.json", ev / "materialize.json")
    cmd = ["/tmp/dvl0-dvr4-labalpha/slot.sh", LANG[set_], sys.executable, "-B", "tools/R12/admit_forms.py",
           str(form), "--admit", str(ev / "hints.json"), "--evidence", str(ev / "evidence"),
           "--admission", str(work / "ADMISSION.json")]
    import time
    attempt, usage = 0, 0
    while True:
        attempt += 1
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if p.returncode == 2 and usage < 10:  # the tool file was being edited: wait and retry
            usage += 1
            time.sleep(60)
            continue
        if p.returncode != 3 or attempt >= 2:
            break
    out = {"id": tid, "exit": p.returncode, "stdout": p.stdout[-500:], "stderr": p.stderr[-800:], "attempts": attempt}
    (work / "admit.json").write_text(json.dumps(out, indent=1) + "\n")
    return tid, p.returncode


def admit(n):
    """n workers per language, so Dafny members are not held behind the shared Verus slots."""
    rows = json.loads((STATE / "prepared.json").read_text())
    todo = [r for r in rows if r["result"] == "prepared" and not (STATE / r["id"] / "admit.json").exists()]
    pools = {lang: cf.ThreadPoolExecutor(n) for lang in ("dafny", "verus")}
    futs = [pools[LANG[r["set"]]].submit(admit_one, r) for r in todo]
    for f in cf.as_completed(futs):
        tid, code = f.result()
        print(tid, code, flush=True)


def select():
    rows = json.loads((STATE / "prepared.json").read_text())
    taken, seen_he, seen_ans, log = [], set(), set(), []
    for row in rows:
        r = dict(row)
        if len(taken) >= LIMIT_TAKE:
            r["result"], r["reason"] = "not walked", "the stop rule was met (45 admitted)"
            r["failed"] = None
            r["checks"] = {}
            log.append(r)
            continue
        if r["result"] == "prepared":
            work = STATE / r["id"]
            adm = json.loads((work / "admit.json").read_text()) if (work / "admit.json").exists() else None
            report = V2 / r["id"] / "evidence" / "report.json"
            rep = json.loads(report.read_text()) if report.exists() else {}
            if adm is None:
                r["result"], r["failed"], r["reason"] = "pending", "-", "admission not run"
            elif adm["exit"] == 3:
                r["result"], r["failed"], r["reason"] = "skipped", "retry", "solver stopped twice (killed or net)"
            elif adm["exit"] != 0:
                key = rep.get("rejected_at") or "tool"
                c = TOOL_TO_C.get(key, key)
                if key == "baseline-proof-fails":
                    doc = rep.get("evidence", {}).get("baseline", {}).get("document", {})
                    if doc.get("stage") != "verify":
                        c = "C4"
                r["result"], r["failed"] = "skipped", c
                r["reason"] = (adm["stderr"].strip().splitlines() or ["?"])[-1][:300]
                if key == "baseline-proof-fails":
                    doc = rep.get("evidence", {}).get("baseline", {}).get("document", {})
                    r["reason"] += f" (baseline verdict {doc.get('verdict')}, stage {doc.get('stage')})"
            else:
                h = r.get("humaneval_id")
                if h is not None and h in seen_he:
                    r["result"], r["failed"], r["reason"] = "skipped", "C3", f"HumanEval/{h} is an earlier accepted member's"
                elif r["answer_sha256"] in seen_ans:
                    r["result"], r["failed"], r["reason"] = "skipped", "C3", "same answer bytes as an earlier accepted member"
                else:
                    r["result"] = "admitted"
                    for k in ("C4", "C5", "C6"):
                        r["checks"][k] = "pass"
                    r["checks"]["C7"] = "pass: static frame control (statement table, models, executable skeleton); no Claude judging (D45)"
                    r["checks"]["C3"] = "pass"
                    if h is not None:
                        seen_he.add(h)
                    seen_ans.add(r["answer_sha256"])
                    taken.append(r)
        elif r["result"] == "skipped" and r.get("failed") == "C3":
            pass
        log.append(r)
    with (HERE / "C0-C7.jsonl").open("w") as fh:
        for r in log:
            fh.write(json.dumps({k: r.get(k) for k in ("k", "set", "task", "id", "result", "failed", "reason", "checks", "flags", "target", "sites", "humaneval_id")}, sort_keys=True) + "\n")
    # install the taken members
    fam = V2 / "families"
    fam.mkdir(exist_ok=True)
    for r in taken:
        tid, set_ = r["id"], r["set"]
        work = STATE / tid
        dest = ROOT / "bench/local/r/labalpha" / tid
        (dest / "tasks").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(work / (tid + EXT[set_]), dest / "tasks" / (tid + EXT[set_]))
        shutil.copyfile(work / "ADMISSION.json", dest / "ADMISSION.json")
        rec = {"cluster": tid, "kind": "public", "set": set_, "upstream_task": f"bench/public/{set_}/answers/{r['task']}",
               "upstream_answer_sha256": r["answer_sha256"], "set_sha256": r["set_sha256"], "pool_sha256": r["pool_sha256"],
               "licence": r["checks"]["C0"], "licence_flag": r["flags"].get("c0_flag"), "lang": LANG[set_],
               "tasks": [tid], "target": r["target"], "sites": r["sites"], "humaneval_id": r.get("humaneval_id"),
               "checks": r["checks"], "flags": r["flags"], "walk_position": r["k"], "status": "admitted",
               "contamination": "possibly seen: a public 2023-2025 repository task; the perturbation probe is deferred (WALK.md)"}
        (fam / f"{tid}.json").write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
    by = {}
    for r in taken:
        by[r["set"]] = by.get(r["set"], 0) + 1
    print(len(taken), "taken", by, "walked", sum(1 for r in log if r["result"] != "not walked"))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "prepare":
        prepare()
    elif cmd == "admit":
        admit(int(sys.argv[2]))
    elif cmd == "select":
        select()
