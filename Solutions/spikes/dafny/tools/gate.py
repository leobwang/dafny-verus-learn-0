#!/usr/bin/env python3
"""Empty-body gate, lever matrix and seed-stability runner for the Dafny
BigNat spike (author-only tooling; spec 2.8, 6.5, 11.5 items 2 and 9).

Holes are delimited in the reference files by
    // @hole-begin <id>      ...      // @hole-end <id>
(an id may own several regions, e.g. a loop's invariants plus its body
asserts). The gate never copies reference proof text out of Solutions/:
variants are generated into a scratch dir, verified, and deleted; each probe
dir records the source sha256s, the transformation, and the generated
variant sha256s in INPUT-NOTE.txt, so `gate.py emit ...` regenerates them
byte for byte.

Subcommands:
  inventory               print the hole inventory (ids, kind, proof lines)
  ref                     verify the reference (pinned limit, default seed)
  units                   resource-limit units check (limit below known cost)
  determinism             3 plain runs and 3 seed-1 runs: rc reproducible?
  seeds                   verify the reference under the 3 pinned seeds
  gate [--levers=a,b] [ids...]  empty-body gate + lever matrix for each hole
                          (levers: indfalse manualind fuel0 fuel01 nonl opaque
                          opaqueValid maxauto; maxauto strips every baked lever;
                          "maxauto+X" stacks lever X on maxauto)
  gateseeds [ids...]      shipped configuration, empty and ref, 3 seeds
  maxseeds [ids...]       empty body under maxauto, 3 seeds
  escalate                re-run out-of-resource empty-body passes at 10x
  test                    dafny test --target py on the compiled code
  summary                 aggregate everything into summary.json
  emit <id> <mode> <levers,...|-> <outdir>   regenerate one variant
"""
import concurrent.futures
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe  # noqa: E402

SPIKE = probe.SPIKE
FILES = ["QG_L1_BigNat.dfy", "QG_L2_BigNat.dfy", "QG_L3_BigNat.dfy", "QG_L4_BigNat.dfy"]
TESTS = "QG_BigNat_Tests.dfy"
LAYER_INDEX = {"L1": 0, "L2": 1, "L3": 2, "L4": 3, "Arith": 3, "Spec": 3}
# highest layer whose functions a hole's module can name (Arith sees only L1;
# BigNatLimbs reaches the layers only through qualified imports, so no lever
# inserts reveals there)
VISIBLE = {"L1": 0, "L2": 1, "L3": 2, "L4": 3, "Arith": 0, "Spec": -1}
MODULE = {"L1": "QG_L1_BigNat", "L2": "QG_L2_BigNat", "L3": "QG_L3_BigNat",
          "L4": "QG_L4_BigNat", "Arith": "QG_L4_Arith", "Spec": "BigNatLimbs"}

# Pinned deterministic settings (spec 6.5).
RLIMIT = int(os.environ.get("GATE_RLIMIT", "5000000"))
ESCALATE_RLIMIT = 50_000_000
CORES = os.environ.get("DAFNY_CORES", "2")  # concurrent z3 per dafny run; workers x cores bounds total z3 (OOM incident 2026-10-03)
# No --boogie pass-through anywhere: at 4.11.0 any --boogie value makes
# --standard-libraries fail to load its .doo (exit 1; probe toy-stdlib-options).
# Seeded runs therefore use `dafny measure-complexity --random-seed S
# --mutations 1`, which accepts --standard-libraries and still reports
# verification errors with exit 4 (probe toy-measure-complexity-fail).
SEEDS = [1, 2, 3]
# L3 and L4 import Std.Arithmetic (the std tier), so every run passes this.
STDLIB = "--standard-libraries"
# Default lever matrix: maximal automation alone, then each lever stacked on it.
LEVERS = ["maxauto", "maxauto+indfalse", "maxauto+manualind", "maxauto+fuel0", "maxauto+fuel01",
          "maxauto+nonl", "maxauto+opaque", "maxauto+opaqueValid", "revealbaked"]
SCRATCH = os.environ.get(
    "SPIKE_SCRATCH",
    "/tmp/claude-1000/-home-leobwang-code-learn-dafny-verus-dafny-verus-learn-0/"
    "775f5d3b-1af2-4c64-8092-e46bc97356ce/scratchpad/sd2/gate")

# Recursive or definitional functions a lever may hide, by defining layer.
FUNCS = {"ToNat": 0, "Pow": 0, "Head": 0, "Tail": 0, "Drop": 0, "Normalize": 1, "FromNat": 1,
         "AddLimb": 1, "Cmp": 2, "AddC": 3, "Add": 3, "MulLimbC": 3,
         "MulLimb": 3, "Mul": 3}

BEGIN = re.compile(r"^(\s*)// @hole-begin (\S+)\s*$")
END = re.compile(r"^\s*// @hole-end (\S+)\s*$")
DECL = re.compile(r"^(\s*)(lemma|method|function)\s+((?:\{[^}]*\}\s*)*)(\w+)")
NLATTR = re.compile(r"^(\s*)((?:abstract\s+)?module) \{:disableNonlinearArithmetic\} ")


def read_sources():
    return {f: open(os.path.join(SPIKE, f)).read().split("\n") for f in FILES}


def inventory(src=None):
    src = src or read_sources()
    holes = {}
    for f in FILES:
        lines = src[f]
        open_id, start = None, None
        for i, ln in enumerate(lines):
            m = BEGIN.match(ln)
            if m:
                assert open_id is None, (f, i, "nested hole")
                open_id, start = m.group(2), i
                continue
            m = END.match(ln)
            if m:
                assert m.group(1) == open_id, (f, i, "mismatched hole-end")
                h = holes.setdefault(open_id, {"file": f, "regions": []})
                assert h["file"] == f
                h["regions"].append((start, i))
                open_id = None
        assert open_id is None, (f, "unclosed hole")
    for hid, h in holes.items():
        lines = src[h["file"]]
        first = h["regions"][0][0]
        decl = None
        for j in range(first, -1, -1):
            m = DECL.match(lines[j])
            if m:
                decl = (j, m.group(2), m.group(4))
                break
        assert decl, hid
        h["decl_line"], h["kind"], h["name"] = decl
        if h["kind"] == "function":
            # a `function ... by method` body: the hole is the method part
            assert hid.split(".", 1)[1] == h["name"] + "ByMethod", (hid, h["name"])
            h["kind"] = "by-method"
        else:
            assert h["name"] == hid.split(".", 1)[1], (hid, h["name"])
        prefix = hid.split(".", 1)[0]
        h["layer"] = prefix
        h["symbol"] = MODULE[prefix] + "." + h["name"]
        n = 0
        for (b, e) in h["regions"]:
            for ln in lines[b + 1:e]:
                s = ln.strip()
                if s and not s.startswith("//"):
                    n += 1
        h["proof_lines"] = n
        h["files_needed"] = FILES[:LAYER_INDEX[prefix] + 1]
        # subject functions: those named in the declaration's contract lines
        contract = []
        for ln in lines[h["decl_line"]:first]:
            if ln.strip() == "{":
                break
            contract.append(ln)
        words = set(re.findall(r"\b(\w+)\s*\(", " ".join(contract)))
        h["subjects"] = sorted(f for f in FUNCS if f in words and f != h["name"])
    return holes


def make_variant(hid, mode, levers, src=None):
    """Return {filename: text} for all FILES, transformed."""
    src = src or read_sources()
    holes = inventory(src)
    out = {f: list(src[f]) for f in FILES}
    edits = {f: {} for f in FILES}  # line index -> replacement list of lines
    h = holes[hid] if hid else None
    if h and mode in ("empty", "revealonly"):
        for (b, e) in h["regions"]:
            for k in range(b + 1, e):
                edits[h["file"]][k] = []
    if h and "maxauto" in levers:
        # Maximal automation (applied first, so other levers stack on it): undo every automation-reducing lever the
        # reference bakes in (the hole's {:induction false}, the module-level
        # {:disableNonlinearArithmetic}, and opaque functions; `reveal` of a
        # non-opaque function is accepted silently, probe toy-reveal-nonopaque).
        j = h["decl_line"]
        out[h["file"]][j] = out[h["file"]][j].replace("{:induction false} ", "", 1)
        for f in FILES:
            for i, ln in enumerate(out[f]):
                if NLATTR.match(ln):
                    out[f][i] = ln.replace("{:disableNonlinearArithmetic} ", "", 1)
                elif re.match(r"^\s*opaque function ", ln):
                    out[f][i] = ln.replace("opaque function ", "function ", 1)
    if h and "indfalse" in levers and h["kind"] == "lemma":
        j = h["decl_line"]
        if "{:induction false}" not in out[h["file"]][j]:
            out[h["file"]][j] = out[h["file"]][j].replace("lemma ", "lemma {:induction false} ", 1)
    if h and "fuel0" in levers and h["kind"] == "lemma" and h["subjects"]:
        j = h["decl_line"]
        attrs = " ".join("{:fuel %s, 0, 0}" % f for f in h["subjects"])
        out[h["file"]][j] = out[h["file"]][j].replace("lemma ", "lemma " + attrs + " ", 1)
    if h and "fuel01" in levers and h["kind"] == "lemma" and h["subjects"]:
        # {:fuel F, 1, 1} is rejected at 4.11.0 ("high value == 1 + low value",
        # probe fuel-syntax-1-1); the default is 1, 2, so the lower settings are 0, 1 and 0, 0.
        j = h["decl_line"]
        attrs = " ".join("{:fuel %s, 0, 1}" % f for f in h["subjects"])
        out[h["file"]][j] = out[h["file"]][j].replace("lemma ", "lemma " + attrs + " ", 1)
    if h and "opaque" in levers and h["subjects"]:
        hide = h["subjects"]
        for fn in hide:
            ff = FILES[FUNCS[fn]]
            # first definition in the file is the layer's own (BigNatSpec/BigNatLimbs
            # also declare Add and Cmp, later in the L4 file)
            idx = [i for i, ln in enumerate(out[ff]) if re.match(r"^\s*(opaque\s+)?function %s\(" % fn, ln)][:1]
            assert len(idx) == 1, fn
            if "opaque function" not in out[ff][idx[0]]:
                out[ff][idx[0]] = out[ff][idx[0]].replace("function ", "opaque function ", 1)
        for oid, oh in holes.items():
            if VISIBLE[oh["layer"]] < 0:
                continue
            if oid == hid and mode == "empty":
                continue
            vis = [fn for fn in hide if FUNCS[fn] <= VISIBLE[oh["layer"]]]
            if not vis:
                continue
            b = oh["regions"][0][0]
            indent = BEGIN.match(src[oh["file"]][b]).group(1)
            prev = edits[oh["file"]].get(b)
            edits[oh["file"]][b] = (prev if prev is not None else [src[oh["file"]][b]]) + [
                indent + "reveal " + ", ".join(vis) + ";"]
    if "opaqueValid" in levers:
        l1 = out["QG_L1_BigNat.dfy"]
        idx = [i for i, ln in enumerate(l1) if re.match(r"^\s*predicate Valid\(", ln)]
        assert len(idx) == 1
        l1[idx[0]] = l1[idx[0]].replace("predicate Valid(", "opaque predicate Valid(", 1)
        for oid, oh in holes.items():
            if VISIBLE[oh["layer"]] < 0:
                continue
            if oid == hid and mode == "empty":
                continue
            b = oh["regions"][0][0]
            indent = BEGIN.match(src[oh["file"]][b]).group(1)
            prev = edits[oh["file"]].get(b)
            edits[oh["file"]][b] = (prev if prev is not None else [src[oh["file"]][b]]) + [
                indent + "reveal Valid;"]
    if h and "revealbaked" in levers and mode == "revealonly":
        # the minimal answer under the shipped AddC opacity: just `reveal AddC();`
        b = h["regions"][0][0]
        indent = BEGIN.match(src[h["file"]][b]).group(1)
        prev = edits[h["file"]].get(b)
        edits[h["file"]][b] = (prev if prev is not None else [src[h["file"]][b]]) + [indent + "reveal AddC();"]
    res = {}
    for f in FILES:
        lines = []
        for i, ln in enumerate(out[f]):
            if i in edits[f]:
                rep = edits[f][i]
                # a begin-marker edit keeps the marker line itself
                lines.extend(rep)
            else:
                lines.append(ln)
        res[f] = "\n".join(lines)
    return res


def sha_text(t):
    return hashlib.sha256(t.encode()).hexdigest()


def parse_csv(path):
    rows = {}
    if not os.path.exists(path):
        return rows
    with open(path) as fh:
        for r in csv.DictReader(fh):
            name = r["TestResult.DisplayName"]
            rows.setdefault(name, []).append(
                (r["TestResult.Outcome"], int(r["TestResult.ResourceCount"]), r.get("RandomSeed")))
    return rows


def classify(rows, symbol, rlimit):
    key = symbol + " (correctness)"
    outs = [x for k, v in rows.items() if k == key or k.startswith(key + " (assertion batch ")
            for x in v]
    if not outs:
        return {"outcome": "absent", "rc": None}
    rc = max(x[1] for x in outs)
    if all(x[0] == "Passed" for x in outs):
        return {"outcome": "pass", "rc": rc}
    if any(x[0] != "Passed" and x[1] >= rlimit for x in outs):
        return {"outcome": "oor", "rc": rc}
    return {"outcome": "fail", "rc": rc}


def verify_variant(probe_id, hid, mode, levers, files, rlimit=RLIMIT, seed=None, extra_note=""):
    src = read_sources()
    variant = make_variant(hid, mode, levers, src)
    tmp = tempfile.mkdtemp(prefix="v-", dir=SCRATCH)
    try:
        for f in files:
            with open(os.path.join(tmp, f), "w") as fh:
                fh.write(variant[f])
        arch = os.path.join(probe.ARCH, probe_id)
        os.makedirs(arch, exist_ok=True)
        logcsv = os.path.join(arch, "results.csv")
        if seed is None:
            argv = [probe.DAFNY, "verify"]
        else:
            argv = [probe.DAFNY, "measure-complexity", "--random-seed", str(seed), "--mutations", "1"]
        argv += [STDLIB, "--resource-limit", str(rlimit), "--cores", CORES]
        if "nonl" in levers:
            argv.append("--disable-nonlinear-arithmetic")
        if "manualind" in levers:
            argv.append("--manual-lemma-induction")
        argv += ["--log-format", f"csv;LogFileName={logcsv}"] + files
        note = [f"variant: hole={hid or '-'} mode={mode} levers={','.join(levers) or '-'}"
                f" seed={seed if seed is not None else 'default'} rlimit={rlimit}",
                f"regenerate: python3 {SPIKE}/tools/gate.py emit {hid or '-'} {mode} "
                f"{','.join(levers) or '-'} <outdir>",
                "source files (Solutions/spikes/dafny):"]
        for f in files:
            note.append(f"  {f}\tsource_sha256={sha_text(chr(10).join(src[f]))}"
                        f"\tvariant_sha256={sha_text(variant[f])}")
        note.append(f"the variant files were written to a scratch dir ({tmp}) and deleted after the run")
        if extra_note:
            note.append(extra_note)
        # probe.run wipes the dir, so run first into it, then restore csv
        rc, out, err = probe.run(probe_id, argv, tmp, note_extra="\n".join(note))
        return rc, out, err, parse_csv(logcsv)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_inventory():
    holes = inventory()
    for hid, h in holes.items():
        print(f"{hid:28s} {h['kind']:7s} lines={h['proof_lines']:3d} regions={len(h['regions'])} "
              f"symbol={h['symbol']} subjects={','.join(h['subjects'])}")


def run_jobs(jobs, workers=None):
    workers = workers or int(os.environ.get("GATE_WORKERS", "3"))
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(verify_variant, *j[1:]): j[0] for j in jobs}
        for fu in concurrent.futures.as_completed(futs):
            key = futs[fu]
            try:
                results[key] = fu.result()
            except Exception as exc:  # keep the other results
                print("job failed:", key, repr(exc), file=sys.stderr)
    return results


def summary_line(out):
    for ln in out.splitlines():
        if ln.startswith("Dafny program verifier finished"):
            return ln
    return ""


def save_json(name, obj):
    with open(os.path.join(probe.ARCH, name), "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)


def load_json(name):
    p = os.path.join(probe.ARCH, name)
    return json.load(open(p)) if os.path.exists(p) else {}


def cmd_ref():
    holes = inventory()
    rc, out, err, rows = verify_variant("ref-verify", None, "ref", [], FILES)
    res = {"exit": rc, "summary": summary_line(out),
           "items": {hid: classify(rows, h["symbol"], RLIMIT) for hid, h in holes.items()},
           "max_rc": max(r[1] for v in rows.values() for r in v)}
    save_json("ref.json", res)
    print(json.dumps(res, indent=1))


def cmd_units():
    # A limit below the known cost of the costliest symbols must report them
    # out of resource, at that limit, in the same units as the CSV counts.
    lim = 150_000
    rc, out, err, rows = verify_variant("rlimit-units", None, "ref", [], FILES, rlimit=lim,
                                        extra_note=f"deliberately low limit {lim}")
    print(rc)
    print(out[-3000:])


def cmd_seeds():
    holes = inventory()
    res = {}
    jobs = [(s, f"seed-{s}", None, "ref", [], FILES, RLIMIT, s) for s in SEEDS]
    out = run_jobs(jobs)
    for s in SEEDS:
        rc, o, e, rows = out[s]
        res[str(s)] = {"exit": rc, "summary": summary_line(o),
                       "items": {hid: classify(rows, h["symbol"], RLIMIT) for hid, h in holes.items()},
                       "max_rc": max(r[1] for v in rows.values() for r in v)}
    save_json("seeds.json", res)
    for s in SEEDS:
        print(s, res[str(s)]["exit"], res[str(s)]["summary"], res[str(s)]["max_rc"])


def cmd_gate(args):
    src = read_sources()
    holes = inventory(src)
    levers, ids = LEVERS, []
    for a in args:
        if a.startswith("--levers="):
            levers = a.split("=", 1)[1].split(",")
        else:
            ids.append(a)
    ids = ids or list(holes)
    jobs = []
    for hid in ids:
        h = holes[hid]
        files = h["files_needed"]
        # the shipped configuration: empty body, levers as baked into the reference
        jobs.append(((hid, "empty", ""), f"gate/{hid}/empty-default", hid, "empty", [], files))
        for lv in levers:
            if lv.startswith("maxauto+"):
                base = lv.split("+")[1]
            else:
                base = lv
            if base in ("indfalse", "manualind", "fuel0", "fuel01") and h["kind"] != "lemma":
                continue
            if base in ("fuel0", "fuel01", "opaque") and not h["subjects"]:
                continue
            if base == "revealbaked" and "opaque-AddC" not in baked_levers(h, src):
                continue
            lvs = lv.split("+")
            if base == "revealbaked":
                jobs.append(((hid, "revealonly", lv), f"gate/{hid}/revealonly-{lv}", hid, "revealonly",
                             lvs, files))
                continue
            jobs.append(((hid, "ref", lv), f"gate/{hid}/ref-{lv}", hid, "ref", lvs, files))
            jobs.append(((hid, "empty", lv), f"gate/{hid}/empty-{lv}", hid, "empty", lvs, files))
            if base in ("opaque", "opaqueValid"):
                # the minimal answer under an opacity lever: just the reveal
                jobs.append(((hid, "revealonly", lv), f"gate/{hid}/revealonly-{lv}", hid, "revealonly",
                             lvs, files))
    out = run_jobs(jobs)
    res = load_json("gate.json")
    for (hid, mode, lv), (rc, o, e, rows) in out.items():
        h = holes[hid]
        c = classify(rows, h["symbol"], RLIMIT)
        others = sorted(k for k, v in rows.items()
                        if not k.startswith(h["symbol"] + " (") and any(x[0] != "Passed" for x in v))
        res.setdefault(hid, {})[f"{mode}-{lv or 'default'}"] = {
            "exit": rc, **c, "other_failures": others}
    save_json("gate.json", res)
    for hid in ids:
        print(hid, json.dumps(res[hid], sort_keys=True))


# Shipping configuration per hole, decided from the lever matrix in gate.json:
#   "none-needed": the empty body fails even under maximal automation;
#   "baked":       it fails as shipped (the reference's own levers suffice);
#   "lever":       the first lever (in PREF order, item-local levers first) whose
#                  empty body fails while the reference still passes;
#   "reveal-drill": only an opacity lever makes it fail, and `reveal F;` alone
#                  then closes it (a one-line drill, not a proof hole);
#   "not-a-hole":  SMT closes the empty body under every lever tried.
PREF = ["indfalse", "fuel01", "fuel0", "opaque", "opaqueValid", "nonl", "manualind"]


def _bad(g, k):
    return g.get(k, {}).get("outcome") in ("fail", "oor")


def _ok(g, k):
    return g.get(k, {}).get("outcome") == "pass"


def decide(g):
    # an out-of-resource empty body that passes at 10x the limit counts as closed by SMT
    if _bad(g, "empty-maxauto") and not _ok(g, "empty-maxauto-x10"):
        return "none-needed", []
    if _bad(g, "empty-default"):
        if _ok(g, "revealonly-revealbaked"):
            return "reveal-drill", []
        return "baked", []
    works = [lv for lv in PREF if _bad(g, f"empty-maxauto+{lv}") and _ok(g, f"ref-maxauto+{lv}")]
    for lv in works:
        # under an opacity lever, a hole whose whole answer is `reveal F;` is a
        # reveal drill, not a proof hole
        if not _ok(g, f"revealonly-maxauto+{lv}"):
            return "lever", [lv]
    if works:
        return "reveal-drill", [works[0]]
    return "not-a-hole", None


def shipping(hid, gate=None):
    gate = gate if gate is not None else load_json("gate.json")
    return decide(gate.get(hid, {}))[1]


def cmd_gateseeds(ids):
    holes = inventory()
    ids = ids or list(holes)
    gate = load_json("gate.json")
    jobs = []
    for hid in ids:
        h = holes[hid]
        lv = shipping(hid, gate)
        if lv is None:
            continue
        tag = lv[0] if lv else "default"
        for s in SEEDS:
            jobs.append(((hid, "empty", tag, s), f"gateseeds/{hid}/empty-{tag}-seed{s}", hid, "empty", lv,
                         h["files_needed"], RLIMIT, s))
            if lv:  # baked references are covered by the whole-file seed runs
                jobs.append(((hid, "ref", tag, s), f"gateseeds/{hid}/ref-{tag}-seed{s}", hid, "ref", lv,
                             h["files_needed"], RLIMIT, s))
    out = run_jobs(jobs)
    res = load_json("gateseeds.json")
    for (hid, mode, tag, s), (rc, o, e, rows) in out.items():
        c = classify(rows, holes[hid]["symbol"], RLIMIT)
        res.setdefault(hid, {})[f"{mode}-{tag}-seed{s}"] = {"exit": rc, **c}
    save_json("gateseeds.json", res)
    for hid in ids:
        if hid in res:
            print(hid, json.dumps(res[hid], sort_keys=True))


def cmd_maxseeds(ids):
    """Empty body under maximal automation, 3 pinned seeds: is the verdict stable?"""
    holes = inventory()
    ids = ids or list(holes)
    jobs = []
    for hid in ids:
        for s in SEEDS:
            jobs.append(((hid, s), f"gateseeds/{hid}/empty-maxauto-seed{s}", hid, "empty", ["maxauto"],
                         holes[hid]["files_needed"], RLIMIT, s))
    out = run_jobs(jobs)
    res = load_json("gateseeds.json")
    for (hid, s), (rc, o, e, rows) in out.items():
        c = classify(rows, holes[hid]["symbol"], RLIMIT)
        res.setdefault(hid, {})[f"empty-maxauto-seed{s}"] = {"exit": rc, **c}
    save_json("gateseeds.json", res)
    for hid in ids:
        print(hid, " ".join(f"s{s}:{res[hid][f'empty-maxauto-seed{s}']['outcome']}" for s in SEEDS))


def baked_levers(h, src):
    """Automation-reducing settings the shipped reference already carries for this hole."""
    b = []
    if "{:induction false}" in src[h["file"]][h["decl_line"]]:
        b.append("induction-false")
    if h["layer"] in ("L4", "Arith", "Spec"):
        b.append("module-disableNonlinearArithmetic")
    body = " ".join(" ".join(src[h["file"]][x:y]) for (x, y) in h["regions"])
    if "reveal AddC" in body or set(h["subjects"]) & {"AddC", "Add", "Mul"}:
        b.append("opaque-AddC")
    return b


def cmd_determinism():
    """Same input, 3 fresh processes each: plain verify, and measure-complexity
    with seed 1. Are the per-symbol resource counts identical run to run?"""
    jobs = []
    for rep_ in ("a", "b", "c"):
        jobs.append((("verify", rep_), f"determinism/verify-{rep_}", None, "ref", [], FILES, RLIMIT, None))
        jobs.append((("seed1", rep_), f"determinism/seed1-{rep_}", None, "ref", [], FILES, RLIMIT, 1))
    out = run_jobs(jobs)
    res = {}
    for kind in ("verify", "seed1"):
        per = {}
        for rep_ in ("a", "b", "c"):
            rc, o, e, rows = out[(kind, rep_)]
            per[rep_] = {k: sorted(x[1] for x in v) for k, v in rows.items()}
            res.setdefault("exit", {})[f"{kind}-{rep_}"] = rc
        names = sorted(set().union(*[set(v) for v in per.values()]))
        differing = [n for n in names if len({json.dumps(per[r].get(n)) for r in per}) > 1]
        res[kind] = {"symbols": len(names), "symbols_with_rc_differing": len(differing),
                     "total_rc": {r: sum(sum(v) for v in per[r].values()) for r in per},
                     "examples": {n: {r: per[r].get(n) for r in per} for n in differing[:5]}}
    save_json("determinism.json", res)
    print(json.dumps(res, indent=1))


def cmd_summary():
    src = read_sources()
    holes = inventory(src)
    gate = load_json("gate.json")
    gs = load_json("gateseeds.json")
    seeds = load_json("seeds.json")
    ref = load_json("ref.json")
    out = {}
    for hid, h in holes.items():
        g = gate.get(hid, {})
        decision, lv = decide(g)
        tag = (lv[0] if lv else "default") if lv is not None else None
        closing = sorted(k.split("-", 1)[1] for k, v in g.items()
                         if k.startswith("empty-") and not k.endswith("-x10") and v["outcome"] != "pass"
                         and g.get("ref-" + k.split("-", 1)[1], {"outcome": "pass" if k == "empty-default" else "?"})
                         ["outcome"] == "pass")
        r = {
            "symbol": h["symbol"], "kind": h["kind"], "file": h["file"],
            "decl_line": h["decl_line"] + 1, "proof_lines": h["proof_lines"],
            "baked_levers": baked_levers(h, src),
            "maxauto_empty": g.get("empty-maxauto", {}).get("outcome"),
            "maxauto_ref": g.get("ref-maxauto", {}).get("outcome"),
            "maxauto_empty_seeds_fail": sum(1 for s in SEEDS
                                            if gs.get(hid, {}).get(f"empty-maxauto-seed{s}", {}).get("outcome")
                                            in ("fail", "oor")),
            "decision": decision,
            "shipped_lever": tag,
            "shipped_empty": (g.get("empty-default" if tag == "default" else f"empty-maxauto+{tag}", {})
                              .get("outcome") if tag else None),
            "revealonly_passes": bool(_ok(g, "revealonly-revealbaked") or
                                      (tag not in (None, "default") and _ok(g, f"revealonly-maxauto+{tag}"))),
            "maxauto_empty_x10": g.get("empty-maxauto-x10", {}).get("outcome"),
            "shipped_empty_seeds_fail": (sum(1 for s in SEEDS
                                             if gs.get(hid, {}).get(f"empty-{tag}-seed{s}", {}).get("outcome")
                                             in ("fail", "oor")) if tag else None),
            "levers_failing_empty_with_ref_passing": closing,
            "ref_default_seed": ref.get("items", {}).get(hid, {}).get("outcome"),
            "ref_rc_default_seed": ref.get("items", {}).get(hid, {}).get("rc"),
            "ref_seeds_pass": sum(1 for s in SEEDS
                                  if seeds.get(str(s), {}).get("items", {}).get(hid, {}).get("outcome") == "pass"),
        }
        if tag and tag != "default":
            r["ref_shipped_lever_seeds_pass"] = sum(
                1 for s in SEEDS if gs.get(hid, {}).get(f"ref-{tag}-seed{s}", {}).get("outcome") == "pass")
        out[hid] = r
    save_json("summary.json", out)
    for hid, r in out.items():
        print(f"{hid:26s} {r['kind']:9s} L={r['proof_lines']:3d} {r['decision']:11s} maxauto-empty={r['maxauto_empty']}"
              f"({r['maxauto_empty_seeds_fail']}/3 fail) maxauto-ref={r['maxauto_ref']} "
              f"ship={r['shipped_lever']} ship-empty={r['shipped_empty']}({r['shipped_empty_seeds_fail']}/3 fail) "
              f"ref-seeds={r['ref_seeds_pass']}/3 baked={','.join(r['baked_levers']) or '-'} "
              f"fail-levers={','.join(r['levers_failing_empty_with_ref_passing'])}")


def cmd_escalate():
    holes = inventory()
    res = load_json("gate.json")
    jobs = []
    for hid, r in res.items():
        for key, v in r.items():
            if key.startswith("empty-") and v["outcome"] == "oor":
                lv = key.split("-", 1)[1]
                levers = [] if lv == "default" else lv.split("+")
                jobs.append(((hid, key), f"gate/{hid}/{key}-x10", hid, "empty", levers,
                             holes[hid]["files_needed"], ESCALATE_RLIMIT))
    out = run_jobs(jobs)
    for (hid, key), (rc, o, e, rows) in out.items():
        c = classify(rows, holes[hid]["symbol"], ESCALATE_RLIMIT)
        res[hid][key + "-x10"] = {"exit": rc, **c, "rlimit": ESCALATE_RLIMIT}
        print(hid, key, c)
    save_json("gate.json", res)


def cmd_test():
    files = FILES + [TESTS]
    out_dir = os.path.join(SCRATCH, "testout")
    shutil.rmtree(out_dir, ignore_errors=True)
    argv = [probe.DAFNY, "test", "--target", "py", STDLIB, "--resource-limit", str(RLIMIT), "--cores", CORES,
            "--output", os.path.join(out_dir, "QG_BigNat_Tests")] + files
    src_note = "\n".join(f"{f}\tsha256={probe.sha256(os.path.join(SPIKE, f))}" for f in files)
    rc, out, err = probe.run("test-py", argv, SPIKE,
                             note_extra="Input files (Solutions/spikes/dafny), recorded by path and sha256:\n"
                                        + src_note + f"\nThe generated Python went to {out_dir} and was "
                                        "deleted after the run.")
    shutil.rmtree(out_dir, ignore_errors=True)
    print(rc)
    print(out)
    print(err)


def cmd_emit(hid, mode, levers, outdir):
    levers = [] if levers == "-" else levers.split(",")
    hid = None if hid == "-" else hid
    v = make_variant(hid, mode, levers)
    os.makedirs(outdir, exist_ok=True)
    for f, t in v.items():
        with open(os.path.join(outdir, f), "w") as fh:
            fh.write(t)
        print(f, sha_text(t))


if __name__ == "__main__":
    os.makedirs(SCRATCH, exist_ok=True)
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(2)
    c = a[0]
    if c == "inventory":
        cmd_inventory()
    elif c == "ref":
        cmd_ref()
    elif c == "units":
        cmd_units()
    elif c == "determinism":
        cmd_determinism()
    elif c == "seeds":
        cmd_seeds()
    elif c == "gate":
        cmd_gate(a[1:])
    elif c == "gateseeds":
        cmd_gateseeds(a[1:])
    elif c == "maxseeds":
        cmd_maxseeds(a[1:])
    elif c == "summary":
        cmd_summary()
    elif c == "escalate":
        cmd_escalate()
    elif c == "test":
        cmd_test()
    elif c == "emit":
        cmd_emit(*a[1:5])
    else:
        print(__doc__)
        sys.exit(2)
