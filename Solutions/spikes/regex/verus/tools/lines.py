#!/usr/bin/env python3
"""DVR0 regex spike (Verus): proof-line counts per fn, the DV0 heuristic (DV0-REPORT §5).

Every file of the crate reachable through `mod` declarations (dvl.verus.crate_files), symbols
with their module path.
proof fn: non-blank, non-comment lines strictly inside the body braces.
exec fn:  non-blank, non-comment lines covered by proof text (proof blocks, assert,
          ghost/tracked lets, reveal) and loop invariant / decreases clauses
          (dvl.verus_spec.proof_spans, plus loop decreases), counted once per line.
spec fns are definitions and are listed with their body lines only.

  lines.py <crate>... [--json OUT]
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "scripts"))
from dvl import verus_spec as vs  # noqa: E402
from dvl import verus as V  # noqa: E402


def code_line(text_lines, n):
    s = text_lines[n - 1].strip()
    return bool(s) and not s.startswith("//")


def count(crate):
    rows = []
    for f, modpath, test_only in V.crate_files(Path(crate) / "src" / "lib.rs"):
        if not test_only:
            rows += count_file(crate, Path(f), modpath)
    return rows


def count_file(crate, f, modpath):
    text = f.read_text()
    tl = text.split("\n")
    src = vs.parse(text)
    rows = []
    for it in src.walk():
        if it.kind != "fn" or not it.in_verus or not it.body:
            continue
        b0, b1 = it.body
        l0, l1 = src.line_of(b0), src.line_of(b1)
        body = [n for n in range(l0 + 1, l1) if code_line(tl, n)]
        if it.mode in ("proof", "spec"):
            proof = body if it.mode == "proof" else []
        else:
            spans = vs.proof_spans(src, b0 + 1, b1, invariants=True, proof=True)
            covered = set()
            for a, b in spans:
                la = text.count("\n", 0, a) + 1
                lb = text.count("\n", 0, b) + 1
                covered.update(range(la, lb + 1))
            # loop decreases clauses (kept by E0, but proof text for the count)
            t = src.toks
            for k in range(b0 + 1, b1):
                if t[k].kind == "id" and t[k].text == "decreases" and t[k].line > l0:
                    covered.add(t[k].line)
                    j = k + 1
                    while j < b1 and t[j].text != "{":
                        covered.add(t[j].line)
                        j += 1
            proof = sorted(n for n in covered if code_line(tl, n))
        sym = "::".join(filter(None, [modpath, vs.item_symbol(it)]))
        rows.append({"crate": Path(crate).name, "item": sym, "mode": it.mode,
                     "first_line": src.line_of(it.head), "body_lines": len(body),
                     "proof_lines": len(proof)})
    return rows


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json")
        out = args[i + 1]
        args = args[:i] + args[i + 2:]
    rows = []
    for c in args:
        rows += count(c)
    for r in rows:
        print(f"{r['crate']:10} {r['item']:28} {r['mode']:5} line {r['first_line']:4} "
              f"body {r['body_lines']:3} proof {r['proof_lines']:3}")
    if out:
        Path(out).write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
