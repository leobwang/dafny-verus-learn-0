"""Course adapter for D36's reference-free feedback; no hidden reference is read."""
import argparse
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "harness"), str(ROOT / "harness/q")]
from fvh import budget, tools
from fvh.labfeedback import mutation_score

class SpecFeedback:
    """An executor callback; its oracle and isolated runner are injectable in tests."""

    def __init__(self, root, task, *, module="Q15", runner=None, oracle=None, records=None,
                 before_probe=None):
        self.root, self.task = Path(root), task
        self.module, self.oracle = module, oracle
        self.runner = runner or tools.ContainerRunner(self.root, module=module)
        if not self.runner.isolated:
            raise tools.ProvenanceError("specification feedback requires an isolated runner")
        self.records = Path(records) if records else None
        self.before_probe = before_probe

    def __call__(self, work, paths, gate_result):
        # Imports run only for an explicitly opted-in S1 arm. No hidden truth
        # or reference oracle module is reachable through this route.
        sys.path.insert(0, str(self.root / "scripts"))
        try:
            from dvl import judge, labcode
        finally:
            sys.path.pop(0)
        if self.oracle is None:
            import importlib
            self.oracle = importlib.import_module("fvh_q.oracles")
        O = self.oracle
        task_path = self.root / self.task
        delivery = (Path(work) / self.task).read_text(encoding="utf-8")
        lang = "dafny" if task_path.suffix == ".dfy" else "verus"
        target, witness = labcode._targets(task_path.read_text(encoding="utf-8"), lang)
        try:
            candidate = judge.candidate(delivery, lang, target)
            # Witness calls refer to the target. A vacuity lemma replaces that
            # target, so drop the witness declaration from the probe's surroundings.
            probe_delivery = labcode.without_declaration(delivery, lang, witness)
            source = labcode.mutant_source(task_path, probe_delivery)
        except (judge.JudgeInputError, labcode.CodeError):
            # An incomplete candidate is an ordinary policy observation. Keep
            # the failed gate available so the next turn can repair it.
            result = {"mutation": None, "vacuity": "unknown",
                      "witness_and_implementation": O.outcome(gate_result),
                      "probe_runs": 0, "unavailable": "candidate-unparseable"}
            self._record(result, [])
            return result
        task = O.Task(Path(self.task).stem, lang, target,
                      tuple(map(tuple, candidate["params"])), tuple(map(tuple, candidate["results"])),
                      source["body"], source["header"], source["footer"])
        spec = O.Spec(task, tuple(candidate["requires"]), tuple(candidate["ensures"]))
        baseline_spec = O.Spec(task, spec.requires, ())
        temp = Path(tempfile.mkdtemp(prefix="fvh-spec-feedback-"))
        probe_dir = temp / "bench/local/q/lab2/oracle/tasks"
        evidence = []
        try:
            def run(instrument, path):
                if self.before_probe is not None:
                    self.before_probe()
                # Keep the probe at its original card's course path. The
                # sandbox may then exclude that attested shipped form from
                # public-answer matching; added candidate material stays scanned.
                named = temp / "probes" / self.task
                named.parent.mkdir(parents=True, exist_ok=True)
                named.write_bytes(Path(path).read_bytes())
                result = tools.run(instrument, named, root=self.root, runner=self.runner,
                                   provenance="agent")
                evidence.append(result.to_dict())
                return result

            def probe(sp, mutant):
                path = O.write_target(O.render_program(task, sp, mutant.body), lang, probe_dir)
                return O.outcome(run("vcheck --gate", path))

            score = mutation_score(O.mutants(task), changes_code=lambda m: labcode.code_mutant(
                task_path, probe_delivery, m.body), baseline=lambda m: probe(baseline_spec, m),
                full=lambda m: probe(spec, m))
            result = {"mutation": score, "vacuity": O.vacuity(spec, run=run, workdir=probe_dir),
                      "witness_and_implementation": O.outcome(gate_result),
                      "probe_runs": len(evidence)}
            self._record(result, evidence)
            return result
        finally:
            shutil.rmtree(temp, ignore_errors=True)

    def _record(self, result, evidence):
        if self.records:
            self.records.parent.mkdir(parents=True, exist_ok=True)
            with self.records.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"feedback": result, "tools": evidence}, sort_keys=True) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--delivery", type=Path, required=True)
    ap.add_argument("--gate-result", type=Path, required=True)
    ap.add_argument("--records", type=Path)
    ap.add_argument("--wall-s", type=float)
    args = ap.parse_args()
    started = time.monotonic()
    def before_probe():
        if args.wall_s is not None and time.monotonic() - started >= args.wall_s:
            raise budget.CapReached("wall-clock", "specification feedback reached the wall cap")
    work = Path(tempfile.mkdtemp(prefix="fvh-feedback-input-"))
    try:
        path = work / args.task
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(args.delivery.read_bytes())
        result = tools.ToolResult(**json.loads(args.gate_result.read_text()))
        feedback = SpecFeedback(args.root, args.task, records=args.records, before_probe=before_probe)
        print(json.dumps(feedback(work, (args.task,), result), sort_keys=True))
    except budget.CapReached:
        return 124
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
