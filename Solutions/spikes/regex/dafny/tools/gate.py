#!/usr/bin/env python3
"""Empty-body gate, lever matrix and seed-stability runner for the DVR0 Dafny
regex spike (author-only tooling; spec 2.8, DELTAS Δ45/Δ46).

Markers in the reference files (Solutions/spikes/regex/dafny/RG_*.dfy, RX_*.dfy):
    // @hole-begin <id>  ...  // @hole-end <id>
        proof regions of item <id> (a lemma's whole body, or the annotation
        statements inside a function or method body; an id may own several);
    // @impl-begin <id> trivial=<expr>  ...  // @impl-end <id>
        the whole body of an implementation item; the vacuity check replaces
        it by <expr>, a type-correct trivial body that must FAIL the contract.

Every solver job goes through the course wrapper library (scripts/dvl: the
pinned flags, the bundled Z3, --cores 2, an 8 GB systemd cgroup cap, one job
at a time) with DVL_SCRATCH under /tmp/dvl0-dv5a-dvr0f/dafny/ (DVR0_WORK). Variants are
written to a scratch project, verified for the item's symbol only and
deleted; the archive keeps cmd, stdout, stderr, exit, tasks.csv and an
INPUT-NOTE with source and variant sha256s (reference text is not copied):
    ~/.cache/dafny-verus-learn-0/author-probes/dvr0-dafny/recon/<probe-id>/ (DVR0_ARCH)

Subcommands:
  inventory                 the items (id, kind, symbol, proof and code lines)
  ref                       the reference: default seed and seeds 1-3, under
                            manual-lemma-induction and under auto-induction
  gate [ids...]             per item: empty (or annotation-stripped) variant under
                            maxauto (default + seeds 1-3), manualind (seeds 1-3),
                            indfalse (seeds 1-3, lemmas only); impl items also
                            get the trivial-body vacuity check (manualind, 3 seeds)
  lever <lever> ids...      one extra lever (opaqueMatches: Matches opaque, unit on
                            manual induction): the empty body and the reference
                            plus `reveal Matches();`, seeds 1-3
  summary                   aggregate into summary.json (also the items each
                            item's proof calls, for the invented-lemma count)
"""
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPIKE = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(SPIKE, "..", "..", "..", ".."))
WORK = os.environ.get("DVR0_WORK", "/tmp/dvl0-dv5a-dvr0f/dafny")
os.environ.setdefault("DVL_SCRATCH", WORK + "/dvl")
sys.path.insert(0, os.path.join(REPO, "scripts"))
from dvl import dafny as D  # noqa: E402

ARCH = os.path.expanduser(os.environ.get(
    "DVR0_ARCH", "~/.cache/dafny-verus-learn-0/author-probes/dvr0-dafny/recon"))
FILES = ["RG_A1_Re.dfy", "RG_A1b_Facts.dfy", "RG_A2_Deriv.dfy", "RG_A3_Syntax.dfy",
         "RG_A4_Norm.dfy", "RG_A5_VM.dfy", "RX_R02.dfy", "RX_R06_Decomp.dfy",
         "RX_R09_Syntax.dfy", "RX_Items.dfy"]
SEEDS = [1, 2, 3]

BEGIN = re.compile(r"^(\s*)// @hole-begin (\S+)\s*$")
END = re.compile(r"^\s*// @hole-end (\S+)\s*$")
IBEGIN = re.compile(r"^(\s*)// @impl-begin (\S+) trivial=(.*)$")
IEND = re.compile(r"^\s*// @impl-end (\S+)\s*$")
DECL = re.compile(r"^\s*(lemma|method|function|predicate)\s+((?:\{[^}]*\}\s*)*)(\w+)")
MODDECL = re.compile(r"^\s*(?:abstract\s+)?module\s+(\w+)")


def read_sources():
    return {f: open(os.path.join(SPIKE, f)).read().split("\n") for f in FILES}


def sha_text(t):
    return hashlib.sha256(t.encode()).hexdigest()


def inventory(src=None):
    src = src or read_sources()
    items = {}
    for f in FILES:
        lines = src[f]
        open_h = open_i = None
        module = None
        for i, ln in enumerate(lines):
            m = MODDECL.match(ln)
            if m:
                module = m.group(1)
            m = BEGIN.match(ln)
            if m:
                assert open_h is None, (f, i)
                open_h = (m.group(2), i)
                continue
            m = END.match(ln)
            if m:
                assert open_h and open_h[0] == m.group(1), (f, i)
                it = items.setdefault(m.group(1), {"file": f, "regions": [], "impl": None})
                it["regions"].append((open_h[1], i))
                it.setdefault("module", module)
                open_h = None
                continue
            m = IBEGIN.match(ln)
            if m:
                assert open_i is None
                open_i = (m.group(2), i, m.group(3).strip())
                continue
            m = IEND.match(ln)
            if m:
                assert open_i and open_i[0] == m.group(1)
                it = items.setdefault(m.group(1), {"file": f, "regions": [], "impl": None})
                it["impl"] = (open_i[1], i, open_i[2])
                it.setdefault("module", module)
                open_i = None
        assert open_h is None and open_i is None, f
    for hid, it in items.items():
        lines = src[it["file"]]
        first = it["impl"][0] if it["impl"] else it["regions"][0][0]
        for j in range(first, -1, -1):
            m = DECL.match(lines[j])
            if m:
                it["decl_line"], it["declkind"], it["name"] = j, m.group(1), m.group(3)
                break
        assert it["name"] == hid.split(".", 1)[1], (hid, it["name"])
        it["symbol"] = it["module"] + "." + it["name"]
        it["kind"] = ("impl" if it["impl"] else
                      "lemma" if it["declkind"] == "lemma" else "annot")
        n = 0
        for (b, e) in it["regions"]:
            n += sum(1 for ln in lines[b + 1:e]
                     if ln.strip() and not ln.strip().startswith("//"))
        it["proof_lines"] = n
        if it["impl"]:
            b, e, _ = it["impl"]
            inside = set()
            for (rb, re_) in it["regions"]:
                inside.update(range(rb, re_ + 1))
            it["code_lines"] = sum(1 for k in range(b + 1, e) if k not in inside
                                   and lines[k].strip() and not lines[k].strip().startswith("//"))
        else:
            it["code_lines"] = 0
    return items


def make_variant(hid, mode, lever, src=None):
    """{file: text}. mode: ref | empty | trivial. lever: maxauto | manualind | indfalse."""
    src = src or read_sources()
    items = inventory(src)
    out = {f: list(src[f]) for f in FILES}
    drop = {f: set() for f in FILES}
    repl = {f: {} for f in FILES}
    it = items.get(hid)
    if it and mode == "empty":
        for (b, e) in it["regions"]:
            drop[it["file"]].update(range(b + 1, e))
    if it and mode == "trivial":
        b, e, triv = it["impl"]
        drop[it["file"]].update(range(b + 1, e))
        ind = IBEGIN.match(src[it["file"]][b]).group(1)
        repl[it["file"]][b] = [src[it["file"]][b], ind + triv]
    if it and mode == "revealref":
        b = it["regions"][0][0]
        ind = BEGIN.match(src[it["file"]][b]).group(1)
        repl[it["file"]][b] = [src[it["file"]][b], ind + "reveal Matches();"]
    if lever == "opaqueMatches":
        a1 = out["RG_A1_Re.dfy"]
        k = [i for i, ln in enumerate(a1) if ln.startswith("  ghost predicate Matches(")]
        assert len(k) == 1
        a1[k[0]] = a1[k[0]].replace("ghost predicate Matches(", "ghost opaque predicate Matches(", 1)
    if lever == "maxauto":
        for f in FILES:
            for i, ln in enumerate(out[f]):
                out[f][i] = ln.replace("{:induction false} ", "").replace("opaque function ", "function ")
    if it and lever == "indfalse" and it["declkind"] == "lemma":
        j = it["decl_line"]
        if "{:induction false}" not in out[it["file"]][j]:
            out[it["file"]][j] = out[it["file"]][j].replace("lemma ", "lemma {:induction false} ", 1)
    res = {}
    for f in FILES:
        lines = []
        for i, ln in enumerate(out[f]):
            if i in repl[f]:
                lines.extend(repl[f][i])
            elif i not in drop[f]:
                lines.append(ln)
        res[f] = "\n".join(lines)
    return res


def options_for(lever):
    return {"resource-limit": 5000000,
            "manual-lemma-induction": lever in ("manualind", "opaqueMatches")}


def write_project(d, variant, opts):
    os.makedirs(d, exist_ok=True)
    for f, t in variant.items():
        with open(os.path.join(d, f), "w") as fh:
            fh.write(t)
    with open(os.path.join(d, "dfyconfig.toml"), "w") as fh:
        fh.write("includes = [" + ", ".join(f'"{f}"' for f in FILES) + "]\n\n[options]\n")
        for k, v in opts.items():
            fh.write(f"{k} = {str(v).lower() if isinstance(v, bool) else v}\n")


def csv_rows(path):
    rows = []
    if os.path.isfile(path):
        with open(path, newline="") as fh:
            for r in csv.DictReader(fh):
                rows.append((r.get("TestResult.DisplayName", ""), r.get("TestResult.Outcome", ""),
                             int(r.get("TestResult.ResourceCount") or 0)))
    return rows


def run(probe_id, hid, mode, lever, seed, symbol=None):
    src = read_sources()
    variant = make_variant(hid, mode, lever, src)
    os.makedirs(WORK + "/variants", exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="v-", dir=WORK + "/variants")
    try:
        write_project(tmp, variant, options_for(lever))
        res = D.verify(tmp, symbol=symbol, seed=seed)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    arch = os.path.join(ARCH, probe_id)
    if os.path.isdir(arch):
        shutil.rmtree(arch)
    os.makedirs(arch)
    raw = res.raw_dir
    rows = []
    if raw and os.path.isdir(raw):
        for name in os.listdir(raw):
            p = os.path.join(raw, name)
            if os.path.isfile(p):
                shutil.copy(p, arch)
        rows = csv_rows(os.path.join(raw, "tasks.csv"))
    with open(os.path.join(arch, "cmd.txt"), "w") as fh:
        fh.write(" ".join(res.cmd) + "\n")
    with open(os.path.join(arch, "exit.txt"), "w") as fh:
        fh.write(f"{res.exit_code}\n")
    note = [f"variant: item={hid or '-'} mode={mode} lever={lever} seed={seed if seed else 'default'}"
            f" symbol={symbol or '(whole project)'} options={json.dumps(options_for(lever))}",
            f"regenerate: python3 {HERE}/gate.py (make_variant('{hid}', '{mode}', '{lever}'))",
            "the variant project was written to a scratch dir under " + WORK + "/variants and deleted",
            "source files (Solutions/spikes/regex/dafny; reference text is not copied):"]
    for f in FILES:
        note.append(f"  {f}\tsource_sha256={sha_text(chr(10).join(src[f]))}"
                    f"\tvariant_sha256={sha_text(variant[f])}")
    note.append(f"verdict={res.verdict} per_symbol={json.dumps(res.per_symbol, sort_keys=True)}")
    with open(os.path.join(arch, "INPUT-NOTE.txt"), "w") as fh:
        fh.write("\n".join(note) + "\n")
    st = res.per_symbol.get(symbol) if symbol else res.verdict
    if res.verdict in ("killed(memory)", "error", "refused"):
        st = res.verdict
    elif st is None:
        st = "absent"
    rc = max([r[2] for r in rows if symbol is None or r[0].split(" (", 1)[0] == symbol] or [0])
    return {"status": st, "verdict": res.verdict, "verified_count": res.verified_count,
            "max_rc": rc, "probe": probe_id}


def load(path):
    return json.load(open(path)) if os.path.exists(path) else {}


def save(path, data):
    with open(path, "w") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)


def cmd_inventory():
    for hid, it in inventory().items():
        print(f"{hid:26s} {it['kind']:6s} proof={it['proof_lines']:3d} code={it['code_lines']:3d}"
              f" regions={len(it['regions'])} {it['symbol']}")


def cmd_ref():
    out = {}
    for lever in ("manualind", "auto"):
        for seed in [None] + SEEDS:
            key = f"{lever}:{seed or 'default'}"
            r = run(f"ref/{lever}-{seed or 'default'}", None, "ref", lever, seed)
            # per-symbol resource maximum over the whole reference
            print(key, r, flush=True)
            out[key] = r
    save(os.path.join(WORK, "ref.json"), out)


def cmd_lever(lever, ids):
    """empty and reference-plus-reveal variants under one extra lever, 3 seeds."""
    items = inventory()
    path = os.path.join(WORK, "gate.json")
    data = load(path)
    for hid in ids:
        it = items[hid]
        res = data.get(hid, {})
        for mode in ("empty", "revealref"):
            for seed in SEEDS:
                key = f"{mode}:{lever}:{seed}"
                if key in res:
                    continue
                r = run(f"gate/{hid}/{mode}-{lever}-{seed}", hid, mode, lever, seed, it["symbol"])
                res[key] = r
                print(hid, key, r["status"], r["max_rc"], flush=True)
                data[hid] = res
                save(path, data)


def cmd_gate(ids):
    items = inventory()
    path = os.path.join(WORK, "gate.json")
    data = load(path)
    for hid in ids or list(items):
        it = items[hid]
        sym = it["symbol"]
        res = data.get(hid, {})
        plan = [("empty", "maxauto", None)] + [("empty", "maxauto", s) for s in SEEDS] \
            + [("empty", "manualind", s) for s in SEEDS]
        if it["declkind"] == "lemma":
            plan += [("empty", "indfalse", s) for s in SEEDS]
        if it["kind"] == "impl":
            plan += [("trivial", "manualind", s) for s in SEEDS]
            if not it["regions"]:
                plan = [p for p in plan if p[0] == "trivial"]
        for mode, lever, seed in plan:
            key = f"{mode}:{lever}:{seed or 'default'}"
            if key in res:
                continue
            r = run(f"gate/{hid}/{mode}-{lever}-{seed or 'default'}", hid, mode, lever, seed, sym)
            res[key] = r
            print(hid, key, r["status"], r["max_rc"], flush=True)
            data[hid] = res
            save(path, data)


def cmd_summary():
    items = inventory()
    gate = load(os.path.join(WORK, "gate.json"))
    ref = load(os.path.join(WORK, "ref.json"))
    summ = {"ref": ref, "items": {}}
    src = read_sources()
    names = {it["name"]: hid for hid, it in items.items() if it["declkind"] == "lemma"}
    for hid, it in items.items():
        body = []
        for (b, e) in it["regions"]:
            body += src[it["file"]][b + 1:e]
        called = sorted({names[n] for n in re.findall(r"\b([A-Z]\w*)\s*\(", "\n".join(body))
                         if n in names and names[n] != hid})
        it["calls"] = called
    for hid, it in items.items():
        g = gate.get(hid, {})

        def verdict(prefix):
            sts = [v["status"] for k, v in g.items() if k.startswith(prefix)]
            if not sts:
                return None
            if any(s == "verified" for s in sts):
                return "VERIFIES(" + ",".join(k.split(":")[-1] for k, v in g.items()
                                              if k.startswith(prefix) and v["status"] == "verified") + ")"
            if all(s in ("failed", "inconclusive") for s in sts):
                return "fails" if all(s == "failed" for s in sts) else "fails(incl. inconclusive)"
            return "/".join(sorted(set(sts)))
        summ["items"][hid] = {
            "kind": it["kind"], "symbol": it["symbol"], "proof_lines": it["proof_lines"],
            "code_lines": it["code_lines"], "calls_items": it["calls"],
            "empty_maxauto": verdict("empty:maxauto:"),
            "empty_manualind": verdict("empty:manualind:"),
            "empty_indfalse": verdict("empty:indfalse:"),
            "trivial_manualind": verdict("trivial:manualind:"),
            "empty_opaqueMatches": verdict("empty:opaqueMatches:"),
            "ref_reveal_opaqueMatches": verdict("revealref:opaqueMatches:"),
        }
    save(os.path.join(SPIKE, "summary.json"), summ)
    for hid, s in summ["items"].items():
        print(f"{hid:26s} {s['kind']:6s} pl={s['proof_lines']:3d} cl={s['code_lines']:3d} "
              f"maxauto={s['empty_maxauto']} manualind={s['empty_manualind']} "
              f"indfalse={s['empty_indfalse']} trivial={s['trivial_manualind']}"
              + (f" opaqueM={s['empty_opaqueMatches']} opaqueM-ref={s['ref_reveal_opaqueMatches']}"
                 if s['empty_opaqueMatches'] else ""))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "inventory"
    if cmd == "inventory":
        cmd_inventory()
    elif cmd == "ref":
        cmd_ref()
    elif cmd == "gate":
        cmd_gate(sys.argv[2:])
    elif cmd == "lever":
        cmd_lever(sys.argv[2], sys.argv[3:])
    elif cmd == "summary":
        cmd_summary()
    else:
        sys.exit(__doc__)
