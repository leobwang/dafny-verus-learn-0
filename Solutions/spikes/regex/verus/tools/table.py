#!/usr/bin/env python3
"""DVR0 regex reference (Verus): aggregate one archive pass into a per-item table (no solver job).

  table.py ARCHIVE_DIR OUT_JSON

Reads ARCHIVE_DIR/{lines.json, stability-rl2/summary.json, gate-rl2/summary.json,
gate-rl2-named-return/*/*.json, triv-rl2/*/*.triv.json} and writes, per fn: crate, mode, proof
lines, the empty-body gate verdict (failed = every variant failed: the item passes the gate;
verified = some variant verified: the item falls to automation; error = the plain variant did
not reach verification), the named-return re-run, the trivial-body check and the crate's
stability under seeds 1-3.
"""
import json
import sys
from pathlib import Path


def load(p):
    return json.loads(p.read_text()) if p.is_file() else None


def main():
    a, out = Path(sys.argv[1]), Path(sys.argv[2])
    lines = load(a / "lines.json") or []
    stab = load(a / "stability-rl2" / "summary.json") or {}
    gate = {(r["crate"], r["item"]): r for r in (load(a / "gate-rl2" / "summary.json") or [])}
    ret = {}
    for p in sorted((a / "gate-rl2-named-return").glob("*/*.json")):
        r = load(p)
        ret[(r["crate"], r["item"])] = r
    triv = {}
    for p in sorted((a / "triv-rl2").glob("*/*.triv.json")):
        r = load(p)
        triv[(r["crate"], r["item"])] = r
    items = []
    for r in lines:
        k = (r["crate"], r["item"])
        g, n, t = gate.get(k), ret.get(k), triv.get(k)
        items.append({
            "crate": r["crate"], "item": r["item"], "mode": r["mode"],
            "proof_lines": r["proof_lines"], "body_lines": r["body_lines"],
            "gate": g["verdict"] if g else None,
            "gate_modes": g["modes"] if g else None,
            "gate_verifying_variants": sorted(v for v, s in (g or {}).get("per_variant", {}).items()
                                              if s in ("verifies", "fn-not-checked")),
            "gate_named_return": n["verdict"] if n else None,
            "trivial_body": t["verdict"] if t else None,
        })
    crates = {c: {s: {"verdict": v["verdict"], "verified": v["verified"], "holes": v["holes"],
                      "wall_s": v["wall_s"]} for s, v in row.items()} for c, row in stab.items()}
    out.write_text(json.dumps({"stability": crates, "items": items}, indent=1, sort_keys=True))
    for it in items:
        if it["mode"] == "spec":
            continue
        print(f"{it['crate']:11} {it['item']:44} {it['mode']:5} pl={it['proof_lines']:3} "
              f"gate={it['gate']} ret={it['gate_named_return']} triv={it['trivial_body']}")


if __name__ == "__main__":
    main()
