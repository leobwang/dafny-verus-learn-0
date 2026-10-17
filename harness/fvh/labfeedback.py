"""Reference-free Lab 2 feedback (D36): only the task form and delivery are read.

The completed learner oracles supply mutation generation and renderers. Policies
receive data through Verify; they never receive a runner or a reference. Every
probe runs with agent provenance in a network-less verification container.
"""
import json
import os
import signal
from pathlib import Path
import shutil
import sys
import tempfile

from fvh import tools


def mutation_score(mutants, *, changes_code, baseline, full):
    """D36: filter annotations, then require baseline verification before scoring.

    A killed, timed-out, or otherwise unknown baseline never enters the
    denominator. Unknown full checks remain visible and never count as kills.
    The per-mutant evidence makes both exclusions auditable.
    """
    rows = []
    for mutant in mutants:
        row = {"id": mutant.id}
        if not changes_code(mutant):
            row["excluded"] = "annotation-only"
        else:
            row["baseline"] = baseline(mutant)
            if row["baseline"] != "proved":
                row["excluded"] = "baseline-" + row["baseline"]
            else:
                row["postconditions"] = full(mutant)
        rows.append(row)
    eligible = [r for r in rows if "postconditions" in r]
    killed = sum(r["postconditions"] == "failed" for r in eligible)
    unknown = sum(r["postconditions"] == "unknown" for r in eligible)
    return {"generated": len(rows), "eligible": len(eligible), "killed": killed,
            "unknown": unknown, "survived": len(eligible) - killed - unknown,
            "rate": killed / len(eligible) if eligible else None, "mutants": rows}


class SpecFeedback:
    """Invoke the trusted course adapter; the frozen core stays stdlib-only.

    The adapter parses candidate text and uses isolated verifier runners.
    No generated program or agent-supplied Python runs on the host.
    """

    def __init__(self, root, task, *, records=None, before_probe=None):
        self.root, self.task = Path(root), task
        self.records = Path(records) if records else None
        self.before_probe = before_probe

    def __call__(self, work, paths, gate_result):
        import subprocess
        from fvh import budget
        remaining = self.before_probe() if self.before_probe else None
        temp = Path(tempfile.mkdtemp(prefix="fvh-feedback-meta-"))
        try:
            gate = temp / "gate.json"
            gate.write_text(json.dumps(gate_result.to_dict()), encoding="utf-8")
            argv = [sys.executable, "-B", str(self.root / "scripts/dvl/spec_feedback.py"),
                    "--root", str(self.root), "--task", self.task,
                    "--delivery", str(Path(work) / self.task), "--gate-result", str(gate)]
            if self.records:
                argv += ["--records", str(self.records)]
            if remaining is not None:
                argv += ["--wall-s", str(remaining)]
            proc = subprocess.Popen(argv, cwd=self.root, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, start_new_session=True)
            def stop():
                # The adapter may be waiting on mksandbox-run. Terminate its
                # process group so that the sandbox's signal cleanup also runs.
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    return
                try:
                    proc.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.communicate()
            try:
                stdout, stderr = proc.communicate(timeout=None if remaining is None else max(1, remaining))
            except subprocess.TimeoutExpired:
                stop()
                raise budget.CapReached("wall-clock", "specification feedback reached the wall cap") from None
            except BaseException:
                stop()
                raise
            ran = subprocess.CompletedProcess(argv, proc.returncode, stdout, stderr)
            if ran.returncode == 124:
                raise budget.CapReached("wall-clock", "specification feedback reached the wall cap")
            if ran.returncode != 0:
                raise tools.RunnerUnavailable("reference-free feedback adapter failed; complete and test Q15's oracles before enabling feedback")
            try:
                result = json.loads(ran.stdout)
            except ValueError:
                raise tools.RunnerUnavailable("reference-free feedback returned invalid JSON") from None
            if not isinstance(result, dict) or not {"mutation", "vacuity", "witness_and_implementation"} <= result.keys():
                raise tools.RunnerUnavailable("reference-free feedback returned an incomplete report")
            return result
        finally:
            shutil.rmtree(temp, ignore_errors=True)
