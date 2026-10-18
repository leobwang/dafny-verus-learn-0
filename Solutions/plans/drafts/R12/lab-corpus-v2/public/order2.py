"""WALK.md Amendment 2: the lemma-shaped-first order for walk positions >= 60. Author-side.
Positions 0-59 stay ORDER.json's. The members not yet walked keep their per-set seeded
order (ORDER.json's orders) and are stably partitioned: lemma-shaped first (materialize.py's
static `lemma_shaped` flag; a member that does not materialize counts as not lemma-shaped),
then the rest; the two partitioned orders are interleaved dafnybench first, as before."""
import json, hashlib, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
O = json.loads((HERE / "ORDER.json").read_text())
head = O["walk"][:60]
done = {tuple(x) for x in head}
rest = {s: [t for t in O["orders"][s] if (s, t) not in done] for s in ("dafnybench", "humaneval-verus")}
flags = {}
with tempfile.TemporaryDirectory(prefix="dvl0-r12-order2-") as tmp:
    for s, ts in rest.items():
        for t in ts:
            d = Path(tmp) / t
            p = subprocess.run([sys.executable, "-B", str(HERE / "materialize.py"), s, t, "x", str(d)], capture_output=True, text=True)
            ok = (d / "materialize.json").exists()
            flags[s + "/" + t] = bool(ok and json.loads((d / "materialize.json").read_text())["flags"].get("lemma_shaped"))
part = {s: [t for t in ts if flags[s + "/" + t]] + [t for t in ts if not flags[s + "/" + t]] for s, ts in rest.items()}
tail, db, hv = [], part["dafnybench"], part["humaneval-verus"]
for i in range(max(len(db), len(hv))):
    if i < len(db): tail.append(["dafnybench", db[i]])
    if i < len(hv): tail.append(["humaneval-verus", hv[i]])
doc = {"amendment": 2, "seed": O["seed"], "base_order_sha256": hashlib.sha256((HERE / "ORDER.json").read_bytes()).hexdigest(),
       "lemma_shaped": flags, "walk": head + tail}
t = json.dumps(doc, indent=1, sort_keys=True) + "\n"
(HERE / "ORDER2.json").write_text(t)
print(hashlib.sha256(t.encode()).hexdigest(), {s: sum(flags[s + "/" + x] for x in ts) for s, ts in rest.items()}, {s: len(ts) for s, ts in rest.items()})
