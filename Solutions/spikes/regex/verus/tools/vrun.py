#!/usr/bin/env python3
"""DVR0 regex spike (Verus): a thin CLI over the pinned wrapper library dvl.verus.

Every solver job goes through dvl.verus (systemd-run scope, MemoryMax = pins mem_gb = 16G,
one job at a time: DVL_VERUS_JOBS unset = 1). Scratch is DVL_SCRATCH (default here
/tmp/dvl0-dv5a-dvr0f/verus-dvl).

  vrun.py verify <crate> [--seed N] [--symbol S] [--json OUT]
  vrun.py eb <crate> <fn symbol> [--modes M,M] [--seeds 1,2,3] [--json OUT]
"""
import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "scripts"))
os.environ.setdefault("DVL_SCRATCH", "/tmp/dvl0-dv5a-dvr0f/verus-dvl")
from dvl import verus as V  # noqa: E402
from dvl import common  # noqa: E402


def show(res, out):
    d = res.to_dict()
    print(f"verdict={res.verdict} stage={res.stage} verified={res.verified_count} "
          f"exit={res.exit_code} holes={len(res.holes)}")
    for k, v in sorted(res.per_symbol.items()):
        print(f"  {k}: {v}")
    for g in res.diagnostics:
        print(f"  {g.severity} {Path(g.file).name}:{g.line}:{g.col}: {g.message.splitlines()[0][:300]}")
    for f in res.findings:
        print(f"  finding {f.kind} {Path(f.file).name}:{f.line}: {f.message[:200]}")
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(d, indent=1, sort_keys=True))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("verify")
    a.add_argument("crate")
    a.add_argument("--seed", type=int)
    a.add_argument("--symbol")
    a.add_argument("--json")
    a.add_argument("--extra", default="")
    b = sub.add_parser("eb")
    b.add_argument("crate")
    b.add_argument("fn")
    b.add_argument("--modes")
    b.add_argument("--seeds", default="1,2,3")
    b.add_argument("--json")
    ns = ap.parse_args()
    if ns.cmd == "verify":
        extra = tuple(ns.extra.split()) if ns.extra else ()
        res = V.verify(ns.crate, seed=ns.seed, symbol=ns.symbol, extra_args=extra,
                       lint_mode="reference")
    else:
        modes = ns.modes.split(",") if ns.modes else None
        seeds = [int(x) for x in ns.seeds.split(",")]
        res = V.empty_body(ns.crate, ns.fn, modes=modes, seeds=seeds)
    show(res, ns.json)
    return 0 if res.verdict in ("verified", "failed") else 1


if __name__ == "__main__":
    sys.exit(main())
