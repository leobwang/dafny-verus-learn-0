#!/usr/bin/env python3
"""DVR0 regex spike (Verus): the empty-body gate for witness-returning proof fns.

dvl.verus.eb_variant replaces a proof body by `{}`, which does not type-check when the
proof fn has a named return (`-> (res: T)`): every variant ends `no-verify(mismatched
types)` and the gate verdict is `error`. Here, for such fns only, the E0/E0H/E1 body is
`{ arbitrary() }` (vstd's uninterpreted value: the empty proof plus an unconstrained
witness), everything else as in the wrapper (same jobs, caps, seeds, rlimits, groups).

  gate_ret.py OUT_DIR crate:item ...
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
os.environ.setdefault("DVL_SCRATCH", "/tmp/dvl0-dv5a-dvr0f/verus-dvl")
from dvl import verus as V  # noqa: E402

_orig = V.eb_variant


def eb_variant(text, src, it, mode, groups=(), triv_body=None, item_id=None):
    if it.mode == "proof" and it.ret is not None and mode in ("E0", "E0H", "E1") and it.body:
        t = src.toks
        b0, b1 = t[it.body[0]].start, t[it.body[1]].end
        new = text[:b0] + "{\n    arbitrary()\n}" + text[b1:]
        if groups:
            ins = V.vs.module_insert_point(src, it)
            new = new[:ins] + "broadcast use " + ", ".join(groups) + ";\n\n" + new[ins:]
        return new
    return _orig(text, src, it, mode, groups, triv_body, item_id)


V.eb_variant = eb_variant


def main():
    out = Path(sys.argv[1])
    for spec in sys.argv[2:]:
        crate, item = spec.split(":")
        f = out / crate / (item.replace("::", "__") + ".json")
        f.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        res = V.empty_body(str(ROOT / crate), item, modes=["E0", "E0H", "E1"], seeds=[1, 2, 3])
        rec = {"crate": crate, "item": item, "mode": "proof (named return)",
               "body": "{ arbitrary() }", "verdict": res.verdict, "per_variant": res.per_symbol,
               "diagnostics": [d.message.splitlines()[0] for d in res.diagnostics],
               "wall_s": round(time.time() - t0, 1)}
        f.write_text(json.dumps(rec, indent=1, sort_keys=True))
        print(crate, item, res.verdict, rec["wall_s"], flush=True)


if __name__ == "__main__":
    main()
