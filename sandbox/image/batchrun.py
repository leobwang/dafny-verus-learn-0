#!/usr/bin/python3
"""The sealed run's batch runner (/opt/dvl/bin/batchrun; QPLAN §31.3, DELTAS Δ419, the
user's D102).

    batchrun <ID> <part>

Run only by scripts/mksandbox-run, as the one [[command]] of a sealed run: an agent
container (dvl-agent) on the run's model network (Route C) with no agent CLI, which
stages the learner's single-use unsealed part at its stratum's course paths, the
learner's committed agents/ and harness/<t>/fvh_<t>/ work (role graded), the frozen
core harness/fvh/, the trusted tools and pins, and the host's inputs under
/work/grader-in/ (spec.json: the ids, the seed pool, the model, the facts; plan.toml:
the learner's plan, byte for byte the one the host opened; apparatus.toml).

It runs the learner's batch with fvh.sealed.inside(): every attempt of the spec's ids
whose wall clock the run still has, each Qwen call through the image's opencode to the
container's relay (127.0.0.1:8000) and on to the run's gate, every Verify here, in this
container; the run directories are written under /work/grader/runs/, the run's one
returned directory. The learner's records are whole: the run is theirs.

Prints one JSON object (the counts of the ids run and left, the states); the batch's own
log lines precede it. Exit: 0 every id ran, 1 ids are left (the host runs another
chunk), 2 usage, 3 refused (no spec of this module and part, the plan is not the
host's). Standard library only; runs as uid 1000 with no capability.
"""

import json
import os
import re
import sys

WORK = "/work"
LAB = re.compile(r"Q(19|2[0-9]|3[0-3])")
PART = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,31}")


def out(obj, code):
    print(json.dumps(obj, sort_keys=True), flush=True)
    return code


def main(argv):
    if len(argv) != 2 or not LAB.fullmatch(argv[0]) or not PART.fullmatch(argv[1]):
        return out({"error": "usage: batchrun <ID> <part> (a challenge module and its part)"}, 2)
    lab, part = argv
    try:
        with open(os.path.join(WORK, "grader-in", "spec.json"), encoding="utf-8") as fh:
            spec = json.load(fh)
    except (OSError, ValueError):
        return out({"error": "no readable grader-in/spec.json is staged"}, 3)
    if spec.get("kind") != "sealed-run" or spec.get("module") != lab or spec.get("part") != part:
        return out({"error": "the staged spec is not this module's sealed run of this part"}, 3)
    for d in (f"{WORK}/harness/r", f"{WORK}/harness/q", f"{WORK}/harness", f"{WORK}/agents"):
        if d not in sys.path:
            sys.path.insert(0, d)
    os.chdir(WORK)
    from fvh import sealed
    try:
        res = sealed.inside(WORK, log=lambda m: print(f"fvh: {m}", flush=True))
    except sealed.SealedRefused as e:
        return out({"error": str(e)[:300]}, 3)
    states = {}
    for s in res["states"].values():
        states[s] = states.get(s, 0) + 1
    return out({"module": lab, "part": part, "ran": len(res["ran"]), "left": len(res["left"]),
                "states": states, "stop": res.get("stop", "")[:300]}, 0 if not res["left"] else 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
