#!/usr/bin/env python3
"""Author-only D36 measurement of pinned Lab 2 reference programs.

Use one solver at a time inside a 16 GiB systemd scope (CLAUDE.md).
This repeats the original author measurement, not an agent verification route.
Only checksum-verified sealed reference code enters the host verifier. Runtime
policy feedback continues to use isolated containers and never reads this file.
All programs, diagnostics and per-mutant records stay in protected author scratch.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "harness")]
from dvl import judge, labcode, sandbox
from fvh.labfeedback import mutation_score
from fvh.tools import ToolResult


def measure(work, only=()):
    why = sandbox.author_gate(ROOT)
    if why:
        raise SystemExit("author context required: " + why)
    work = work.resolve()
    if not str(work).startswith("/tmp/dvl0-dv"):
        raise SystemExit("work must be protected author scratch under /tmp/dvl0-dv…")
    work.mkdir(parents=True, exist_ok=True)
    pin = sandbox.truth_pins(ROOT)["Q15"]
    files = sandbox._sealed_tree(ROOT, pin["archive"], want_sha=pin["sha256"],
                                 want_manifest=pin["manifest_sha256"], want_files=pin["files"],
                                 recipient=pin["recipient"], lab="Q15")
    oracle_path = work / "oracles.py"
    oracle_path.write_bytes(files["judge/oracles.py"])
    source = importlib.util.spec_from_file_location("sealed_measurement_oracles", oracle_path)
    O = importlib.util.module_from_spec(source)
    sys.modules[source.name] = O
    source.loader.exec_module(O)
    stamp = {"archive_sha256": pin["sha256"],
             "score_sha256": hashlib.sha256((ROOT / "harness/fvh/labfeedback.py").read_bytes()).hexdigest(),
             "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    stamp_path = work / "inputs.json"
    if stamp_path.exists() and json.loads(stamp_path.read_text()) != stamp:
        raise SystemExit("measurement inputs changed; use a fresh work directory")
    stamp_path.write_text(json.dumps(stamp, indent=2))
    output = work / "scores.json"
    results = json.loads(output.read_text()) if output.exists() else {}
    cards = tomllib.loads((ROOT / "bench/local/q/lab2pub/STRATUM.toml").read_text())["card"]
    if set(only) - {c["id"] for c in cards}:
        raise SystemExit("unknown public card")
    for card in cards:
        cid, lang = card["id"], card["lang"]
        if cid in results or (only and cid not in only):
            continue
        ext = ".dfy" if lang == "dafny" else ".rs"
        rel = f"bench/local/q/lab2pub/{cid}/tasks/{cid}{ext}"
        form = ROOT / rel
        text = files[f"tasks/{cid}/{cid}{ext}"].decode()
        target, witness = labcode._targets(form.read_text(), lang)
        candidate = judge.candidate(text, lang, target)
        delivery = labcode.without_declaration(text, lang, witness)
        src = labcode.mutant_source(form, delivery)
        task = O.Task(cid, lang, target, tuple(map(tuple, candidate["params"])),
                      tuple(map(tuple, candidate["results"])), src["body"], src["header"], src["footer"])
        spec = O.Spec(task, tuple(candidate["requires"]), tuple(candidate["ensures"]))
        base = O.Spec(task, spec.requires, ())
        probes = work / cid
        probes.mkdir(exist_ok=True)
        evidence = []

        def probe(sp, body):
            path = Path(O.write_target(O.render_program(task, sp, body), lang, probes))
            argv = ["timeout", "--signal=TERM", "--kill-after=10s", "600",
                    str(ROOT / "scripts/vcheck"), "--gate", "--json", str(path)]
            p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                               env={**os.environ, "DVL_SCRATCH": str(probes / "scratch")})
            try:
                doc = json.loads(p.stdout)
                if isinstance(doc, list) and len(doc) == 1:
                    doc = doc[0]
            except ValueError:
                doc = {}
            if not isinstance(doc, dict):
                doc = {}
            killed = "wall-clock" if p.returncode == 124 else (
                "memory" if p.returncode in (137, 143, -9, -15) else None)
            result = ToolResult("vcheck --gate", str(path), doc, p.returncode, killed,
                                "host", "course", hashlib.sha256(p.stdout.encode()).hexdigest())
            evidence.append(result.to_dict())
            path.unlink()
            return O.outcome(result)

        unmutated = {"full": probe(spec, task.body), "baseline": probe(base, task.body)}
        if set(unmutated.values()) != {"proved"}:
            (probes / "evidence.json").write_text(json.dumps(evidence, indent=1))
            raise SystemExit(f"{cid}: unmutated reference failed measurement preflight")
        score = mutation_score(O.mutants(task), changes_code=lambda m: labcode.code_mutant(
            form, delivery, m.body), baseline=lambda m: probe(base, m.body),
            full=lambda m: probe(spec, m.body))
        results[cid] = {"unmutated": unmutated, "mutation": score, "probe_runs": len(evidence)}
        (probes / "evidence.json").write_text(json.dumps(evidence, indent=1))
        output.write_text(json.dumps(results, indent=1))
        print(f"{cid}: generated={score['generated']} eligible={score['eligible']} "
              f"killed={score['killed']} unknown={score['unknown']}", flush=True)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--only", nargs="*", default=[])
    args = parser.parse_args()
    measure(args.work, args.only)
