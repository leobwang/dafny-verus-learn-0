#!/usr/bin/env python3
"""DVR0 regex spike (Verus): the measurement sweep through the pinned wrapper (dvl.verus).

  sweep.py stability OUT_DIR          every crate, --rlimit 2 (pin), seeds 1 2 3 (no-cheating run)
  sweep.py triv OUT_DIR crate:item[=body] ...   the trivial-body vacuity check (TRIV)
  sweep.py gate OUT_DIR [crate ...] [--only crate:item,...]
                                      the empty-body gate per item: proof fns E0 E0H E1 NL BV,
                                      exec fns with proof text E0 E0H E1 INV; seeds 1 2 3;
                                      BV under the pinned 120 s clock (pins.toml eb_mode_timeout_s)

One Verus job at a time (DVL_VERUS_JOBS unset = 1), each under the wrapper's 16G MemoryMax
scope. Writes one JSON per crate or item into OUT_DIR and a summary.json; skips items whose
JSON already exists (resumable).
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(HERE))
os.environ.setdefault("DVL_SCRATCH", "/tmp/dvl0-dv5a-dvr0f/verus-dvl")
from dvl import verus as V  # noqa: E402
import lines  # noqa: E402

CRATES = ["rg_re_a1", "rg_re_a1b", "rg_re_a2", "rg_re_a3", "rg_re_a4", "rg_re_a5", "rg_rexc",
          "rg_arena", "rg_ref_r02", "rg_ref_r06", "rg_ref_r09"]
SEEDS = [1, 2, 3]


def stability(out, crates=None):
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for c in crates or CRATES:
        row = {}
        for s in SEEDS:
            t0 = time.time()
            res = V.verify(str(ROOT / c), seed=s, lint_mode="reference")
            row[f"seed{s}"] = {"verdict": res.verdict, "verified": res.verified_count,
                               "holes": len(res.holes), "errors": [d.message.splitlines()[0]
                               for d in res.diagnostics if d.severity == "error"],
                               "per_symbol": res.per_symbol, "wall_s": round(time.time() - t0, 1),
                               "cmd": [str(x) for x in res.cmd]}
            print(c, s, res.verdict, res.verified_count, flush=True)
        summary[c] = row
        (out / f"{c}.json").write_text(json.dumps(row, indent=1, sort_keys=True))
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True))


def gate(out, crates, only=None):
    out.mkdir(parents=True, exist_ok=True)
    for c in crates:
        for r in lines.count(ROOT / c):
            if r["mode"] == "spec" or (r["mode"] == "exec" and r["proof_lines"] == 0):
                continue
            item = r["item"]
            if only is not None and f"{c}:{item}" not in only:
                continue
            f = out / c / (item.replace("::", "__") + ".json")
            if f.exists():
                continue
            f.parent.mkdir(parents=True, exist_ok=True)
            modes = ["E0", "E0H", "E1", "NL", "BV"] if r["mode"] == "proof" else ["E0", "E0H", "E1", "INV"]
            t0 = time.time()
            res = V.empty_body(str(ROOT / c), item, modes=modes, seeds=SEEDS)
            rec = {"crate": c, "item": item, "mode": r["mode"], "proof_lines": r["proof_lines"],
                   "modes": modes, "verdict": res.verdict, "per_variant": res.per_symbol,
                   "diagnostics": [d.message.splitlines()[0] for d in res.diagnostics],
                   "wall_s": round(time.time() - t0, 1)}
            f.write_text(json.dumps(rec, indent=1, sort_keys=True))
            print(c, item, res.verdict, rec["wall_s"], flush=True)
    rows = [json.loads(p.read_text()) for p in sorted(out.glob("*/*.json"))]
    (out / "summary.json").write_text(json.dumps(rows, indent=1, sort_keys=True))


def triv(out, specs):
    """The trivial-body vacuity check (TRIV) for exec fns: `crate:item[=body]`; the body
    defaults to the wrapper's (unit, integer or bool return)."""
    out.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        ci, _, body = spec.partition("=")
        c, item = ci.split(":", 1)
        f = out / c / (item.replace("::", "__") + ".triv.json")
        if f.exists():
            continue
        f.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        res = V.empty_body(str(ROOT / c), item, modes=["TRIV"], seeds=SEEDS,
                           triv_body=body or None)
        rec = {"crate": c, "item": item, "mode": "exec (trivial body)", "body": body or "(wrapper)",
               "verdict": res.verdict, "per_variant": res.per_symbol,
               "diagnostics": [d.message.splitlines()[0] for d in res.diagnostics],
               "wall_s": round(time.time() - t0, 1)}
        f.write_text(json.dumps(rec, indent=1, sort_keys=True))
        print(c, item, "TRIV", res.verdict, rec["wall_s"], flush=True)


if __name__ == "__main__":
    cmd, out = sys.argv[1], Path(sys.argv[2])
    args = sys.argv[3:]
    only = None
    if "--only" in args:
        k = args.index("--only")
        only = set(args[k + 1].split(","))
        args = args[:k] + args[k + 2:]
    if cmd == "stability":
        stability(out, args or None)
    elif cmd == "gate":
        gate(out, args or CRATES, only)
    elif cmd == "triv":
        triv(out, args)
    else:
        sys.exit("usage: sweep.py stability|gate OUT_DIR [crate ...] [--only crate:item,...] | "
                 "triv OUT_DIR crate:item[=body] ...")
