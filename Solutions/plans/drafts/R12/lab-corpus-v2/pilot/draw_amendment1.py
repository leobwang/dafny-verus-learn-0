#!/usr/bin/env python3
"""Author tool: CONFIRMATORY_DRAW.md Amendment 1 (the user's D61), run once after D63's
re-admission. Reads the first draw (CONFIRMATORY.json `first_draw`, or the file itself before
the amendment) and the stratum, writes CONFIRMATORY.json and ROLES.json. Deterministic."""
import hashlib, json, random, sys, tomllib
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
SEED = "R12-labalpha-confirmatory-20261019"
cur = json.loads((HERE / "CONFIRMATORY.json").read_text())
first = cur.get("first_draw", cur)
st = tomllib.loads((ROOT / "bench/local/r/labalpha/STRATUM.toml").read_text())
tasks = st["task"]
clusters = {}
for t in tasks:
    c = clusters.setdefault(t["cluster"], {"sealed": False, "source": t.get("source", "")})
    c["sealed"] |= bool(t.get("sealed"))
pilot = sorted(k for k, v in json.loads((HERE / "ROLES.json").read_text()).items() if v.get("role") == "pilot")
regex_all = sorted(c for c in clusters if not c.startswith("pub-"))
public_all = sorted(c for c in clusters if c.startswith("pub-"))
sealed = sorted(c for c in clusters if clusters[c]["sealed"])
regex = [c for c in regex_all if c not in pilot and c not in sealed]                    # rule 7
public_pool = [c for c in public_all if c not in pilot]                                 # rule 8 (all admitted)
kept = [c for c in first["confirmatory_public"] if c in public_pool]                    # rule 9
rest = [c for c in public_pool if c not in kept]
n = first["K"] - len(regex) - len(kept)
added = sorted(random.Random(SEED + ":public-amendment-1").sample(rest, n))
conf_public = sorted(kept + added)
conf = sorted(regex + conf_public)
assert len(conf) == first["K"] == 80, len(conf)
d_kept = [c for c in first["descriptive"] if c in conf]                                 # rule 10
d_reg_kept = [c for c in d_kept if not c.startswith("pub-")]
d_pub_kept = [c for c in d_kept if c.startswith("pub-")]
d_reg_new = random.Random(SEED + ":descriptive-regex-amendment-1").sample(
    sorted(c for c in regex if c not in d_reg_kept), 12 - len(d_reg_kept))
d_pub_new = random.Random(SEED + ":descriptive-public-amendment-1").sample(
    sorted(c for c in conf_public if c not in d_pub_kept), 8 - len(d_pub_kept))
desc = sorted(d_kept + d_reg_new + d_pub_new)
pool = {"regex": regex, "public": public_pool}
rule = HERE / "CONFIRMATORY_DRAW.md"
out = {"rule": str(rule.relative_to(ROOT)), "rule_sha256": hashlib.sha256(rule.read_bytes()).hexdigest(),
       "amendment": 1, "seed": SEED, "pool": pool,
       "pool_sha256": hashlib.sha256(json.dumps(pool, sort_keys=True).encode()).hexdigest(),
       "stratum_sha256": hashlib.sha256((ROOT / "bench/local/r/labalpha/STRATUM.toml").read_bytes()).hexdigest(),
       "sealed_left": sealed, "public_kept": kept, "public_added": added,
       "descriptive_kept": d_kept, "descriptive_added": sorted(d_reg_new + d_pub_new),
       "confirmatory": conf, "confirmatory_regex": regex, "confirmatory_public": conf_public,
       "descriptive": desc, "K": 80, "first_draw": first}
(HERE / "CONFIRMATORY.json").write_text(json.dumps(out, indent=1) + "\n")
roles = {c: {"role": "pilot"} for c in pilot}
roles.update({c: {"role": "confirmatory", "descriptive": c in desc} for c in conf})
(HERE / "ROLES.json").write_text(json.dumps(roles, indent=1) + "\n")
print(f"confirmatory {len(conf)} = {len(regex)} regex + {len(conf_public)} public "
      f"({len(kept)} kept, {len(added)} added: {added}); descriptive {len(desc)} "
      f"(kept {len(d_kept)}, added {sorted(d_reg_new + d_pub_new)}); sealed left {sealed}")
