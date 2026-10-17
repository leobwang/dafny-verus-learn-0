"""fvh.executor — the executor: the only thing that validates and performs a
policy's actions (DV4-PLAN §3.2, §3.5, §4.3; design N2).

  Executor(ctx, files, *, runner, meter=None, readable_files=None, run_dir=None,
           verify_target=None, instrument="vcheck --gate", root=None)
      files           the editable inputs as staged: path -> text (the work copy
                      starts as these and lives in memory; the learner's tree
                      is never touched)
      readable_files  the read-only files a Read may see: path -> text
      runner          an isolated fvh.tools runner (ContainerRunner live,
                      ReplayRunner or a recorded log in CI); a runner that is
                      not isolated is refused: every verification of a work
                      copy is a run on agent output (provenance `agent`)
      meter           the run's budget.Meter (caps; the model policies charge it)
      run_dir         when given, actions.jsonl, observations.jsonl and
                      verify.json are written there as the run goes
      replay_end, final_verify   for fvh report's re-derivation only: the end
                      cause a recording's end stands for, and whether the
                      final verification is replayed
      support_files   read-only companions of a crate task (its Cargo.toml and
                      frozen statements: path -> text), written into the work
                      copy at every verification under the editable files and
                      never editable (DV5c gaps lane: crate tasks)
      acceptance      the gated-acceptance tool of a lab arm (Lab 3's arm G,
                      QPLAN §28.5): a callable (work dir, the work copy's paths)
                      -> dict with "passed" (bool), "verdict" (its printed
                      word), "reasons" (list) and "results" (the ToolResults it
                      ran, each on agent provenance in a verification
                      container). With it, every Verify runs the acceptance
                      tool; a Stop is refused until the tool has passed the
                      current work copy, and the run ends ("gate-pass") as soon
                      as it does. The outcome is still the plain instrument's
                      verdict (the acceptance tool's own run of it on the last
                      work copy, or a final verification), as in every other
                      run.
  Executor.run(policy) -> RunResult(outcome, ended_by, verify, steps, usage,
                                    files, findings, detail)

The loop: before each proposal the turn cap and the wall clock are checked (a
reached cap ends the run with its cause; the model units, calls, tokens and
GPU-seconds, are enforced at each model call by budget.Meter.before_call,
whose CapReached ends the run the same way); the policy proposes; each action is validated
and performed in order (Read and Edit on the work copy under the protocol's
rules; Verify materializes the work copy in a fresh directory and runs the
pinned gate instrument on it through fvh.tools.run with provenance `agent`;
Stop ends the run, and actions after it are not performed). A refused action
gets an observation of kind "refused" and the run goes on. At the end, if the
work copy changed since its last verification (or was never verified), one
final verification decides the outcome.

Outcomes (fvh.runlog): the final verification's verdict; `malformed` for a
proposal that does not validate (it counts as a call and ends the run; the
work copy's own verdict is kept); `truncated:<cause>` for a transport,
container or memory failure after model output; `infra-failed` for one
before any; `apparatus-mismatch`; `replay-diverged`; `deferred`. A killed
verification is never a pass: memory reads killed(memory), a time-out
inconclusive (Δ57, Δ58).

Frozen (guard rule 2f), standard library only. This file is on
scripts/check_single_route.py's allowlist (verification goes through the
sandbox runner).
"""

import dataclasses
import json
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from fvh import apparatus, backends, budget, policies, protocol, tools
from fvh.records import VERDICTS
from fvh.tools import runners as _runners

__all__ = ["Executor", "LogRunner", "ReplayAcceptance", "RunResult", "verdict_doc"]


@dataclass(frozen=True)
class RunResult:
    outcome: str
    ended_by: str
    verify: dict | None
    steps: int
    usage: dict
    files: Mapping
    findings: tuple = ()
    detail: str = ""

    def __hash__(self):
        return hash((self.outcome, self.ended_by, self.steps))


def verdict_doc(result: tools.ToolResult) -> dict:
    """The verification document of one gate run: the tool's own document, or,
    for a kill or a text-only result, a document whose verdict is never a pass."""
    if result.killed is not None:
        return {"verdict": "killed(memory)" if result.killed == "memory" else "inconclusive",
                "killed": result.killed, "exit_code": result.exit_code,
                "lines": list(result.document.get("lines", [])), "holes": [],
                "diagnostics": [], "verified_count": 0}
    doc = dict(result.document)
    if doc.get("verdict") not in VERDICTS:
        return {"verdict": "error", "exit_code": result.exit_code,
                "lines": list(doc.get("lines", [])), "holes": [], "diagnostics": [],
                "verified_count": 0}
    return doc


class LogRunner(_runners.Runner):
    """Replays the tool results of a recorded run's observations.jsonl, in order
    (fvh report's re-derivation; no solver, no container)."""

    name = "replay"
    isolated = True

    def __init__(self, run_dir, *, skip_acceptance=False):
        self.results = []
        p = Path(run_dir) / "observations.jsonl"
        for line in (p.read_text(encoding="utf-8").splitlines() if p.is_file() else []):
            if line.strip():
                rec = json.loads(line)
                if skip_acceptance and any(
                        isinstance((o.get("verdict") or {}).get("acceptance"), dict)
                        for o in rec.get("observations", []) if isinstance(o, dict)):
                    continue              # a gated arm's step: ReplayAcceptance replays it
                for t in rec.get("tools", []):
                    self.results.append(tools.ToolResult(**{**t, "runner": "replay"}))
        self.used = 0

    def execute(self, instrument, target, *, timeout_s=None):
        if self.used >= len(self.results):
            raise tools.NoRecording("the recorded run holds no further verification")
        r = self.results[self.used]
        self.used += 1
        if r.instrument != instrument:
            raise tools.NoRecording(f"the recording ran {r.instrument}, not {instrument}")
        return dataclasses.replace(r, target=str(target))


class ReplayAcceptance:
    """Replays a gated run's acceptance verdicts from its observations.jsonl, in
    order (fvh report's re-derivation): each call returns the recorded verdict
    and the tool results that verdict was computed from."""

    def __init__(self, run_dir):
        self.calls = []
        p = Path(run_dir) / "observations.jsonl"
        for line in (p.read_text(encoding="utf-8").splitlines() if p.is_file() else []):
            if not line.strip():
                continue
            rec = json.loads(line)
            tools_ = [tools.ToolResult(**{**x, "runner": "replay"}) for x in rec.get("tools", [])]
            for o in rec.get("observations", []):
                acc = ((o.get("verdict") or {}) if isinstance(o, dict) else {}).get("acceptance")
                if o.get("kind") == "verify" and isinstance(acc, dict):
                    n = int(acc.get("tools") or 0)
                    self.calls.append({"passed": bool(acc.get("passed")),
                                       "verdict": acc.get("verdict", ""),
                                       "reasons": list(acc.get("reasons") or []),
                                       "results": tools_[:n]})
                    tools_ = tools_[n:]
        self.used = 0

    def __call__(self, work, paths):
        if self.used >= len(self.calls):
            raise tools.NoRecording("the recorded run holds no further acceptance verdict")
        got = self.calls[self.used]
        self.used += 1
        return got


class Executor:
    """Performs one run of a policy on a work copy (module docstring)."""

    def __init__(self, ctx: protocol.Context, files: Mapping[str, str], *, runner,
                 meter: budget.Meter | None = None, readable_files: Mapping[str, str] | None = None,
                 run_dir=None, verify_target: str | None = None,
                 instrument: str = "vcheck --gate", root=None, replay_end: str = "script-end",
                 final_verify: bool = True, support_files: Mapping[str, str] | None = None,
                 acceptance=None, feedback=None):
        if not getattr(runner, "isolated", False):
            raise tools.ProvenanceError(f"{type(runner).__name__} is not isolated: a work copy "
                                        "is agent output and is verified only in the "
                                        "verification container")
        if instrument not in tools.INSTRUMENTS:
            raise ValueError(f"{instrument!r} is not an instrument")
        missing = [p for p in ctx.editable if p not in files]
        if missing:
            raise ValueError("the staged files lack editable path(s): " + ", ".join(missing))
        self.ctx = ctx
        self.files = {p: str(files[p]) for p in ctx.editable}
        self.staged = dict(self.files)
        self.readable = dict(readable_files or {})
        self.support = {p: str(x) for p, x in (support_files or {}).items()
                        if p not in self.files}
        for p, x in self.support.items():
            self.readable.setdefault(p, x)
        self.acceptance = acceptance
        self.feedback = feedback
        self.gate_passed = None       # the work-copy digests the acceptance tool last passed
        self.runner = runner
        self.meter = meter or budget.Meter()
        self.run_dir = Path(run_dir) if run_dir is not None else None
        self.verify_target = verify_target or ctx.target
        self.instrument = instrument
        self.root = root
        self.replay_end = replay_end
        self.final_verify = final_verify
        self.last_verify = None
        self.dirty = True
        self.history = []
        self.proposals = 0
        self.findings = []

    # --- records -------------------------------------------------------------------

    def _append(self, name, rec):
        if self.run_dir is None:
            return
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with (self.run_dir / name).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")

    def _digests(self):
        return {p: protocol.text_sha256(t) for p, t in sorted(self.files.items())}

    # --- actions -------------------------------------------------------------------

    def _read(self, a):
        if not self.ctx.may_read(a.path):
            return protocol.Observation("refused", False, f"{a.path} is not readable in this task")
        text = self.files.get(a.path, self.readable.get(a.path))
        if text is None:
            return protocol.Observation("refused", False, f"{a.path} is not staged")
        lines = text.splitlines(keepends=True)
        lo = (a.start or 1) - 1
        hi = a.end if a.end is not None else len(lines)
        body, cut = protocol.clip("".join(lines[lo:hi]), self.ctx.read_limit)
        return protocol.Observation("read", True, body, cut=cut)

    def _edit(self, a):
        if a.path not in self.ctx.editable:
            return protocol.Observation("refused", False, f"{a.path} is not editable in this task")
        cur = self.files[a.path]
        if a.old == "":
            self.files[a.path] = a.new
        else:
            n = cur.count(a.old)
            if n != 1:
                return protocol.Observation("refused", False, f"the edit's old text occurs {n} "
                                            f"times in {a.path}, not exactly once")
            self.files[a.path] = cur.replace(a.old, a.new, 1)
        if self.files[a.path] != cur:
            self.dirty = True
        return protocol.Observation("edit", True, f"edited {a.path}")

    def _materialize(self, work):
        for p, t in list(self.support.items()) + list(self.files.items()):
            f = work / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(t, encoding="utf-8")

    def _gate(self, mode):
        """A Verify of a gated arm: the acceptance tool on the work copy."""
        work = Path(tempfile.mkdtemp(prefix="work-"))
        try:
            self._materialize(work)
            got = self.acceptance(work, tuple(sorted(set(self.support) | set(self.files))))
        finally:
            shutil.rmtree(work, ignore_errors=True)
        results = list(got.get("results") or [])
        gate_res = next((r for r in results if r.instrument == self.instrument), None)
        doc = verdict_doc(gate_res) if gate_res is not None else {
            "verdict": "error", "lines": [], "holes": [], "diagnostics": [], "verified_count": 0}
        passed = bool(got.get("passed"))
        reasons = [str(x)[:300] for x in (got.get("reasons") or [])][:20]
        doc["acceptance"] = {"passed": passed, "verdict": str(got.get("verdict", ""))[:200],
                             "reasons": reasons, "tools": len(results)}
        doc["files_sha256"] = self._digests()
        self.last_verify, self.dirty = doc, False
        self.gate_passed = self._digests() if passed else None
        text = (f"{mode}: acceptance {doc['acceptance']['verdict'] or ('PASS' if passed else 'FAIL')}"
                + ("" if passed else "; " + "; ".join(reasons[:5]))
                + f"; vcheck --gate: {doc.get('verdict')}")
        return protocol.Observation("verify", passed, text, verdict=doc), results

    def _verify(self, mode):
        work = Path(tempfile.mkdtemp(prefix="work-"))
        try:
            self._materialize(work)
            res = tools.run(self.instrument, work / self.verify_target, root=self.root,
                            runner=self.runner, provenance="agent")
            if self.feedback is not None:
                extra = self.feedback(work, tuple(sorted(self.files)), res)
                res = dataclasses.replace(res, document={**res.document, "spec_feedback": extra})
        finally:
            shutil.rmtree(work, ignore_errors=True)
        doc = verdict_doc(res)
        doc["files_sha256"] = self._digests()     # the work copy this verdict is of (DV5c)
        self.last_verify, self.dirty = doc, False
        holes = doc.get("holes")
        text = (f"{mode}: {doc.get('verdict')}, holes "
                f"{len(holes) if isinstance(holes, list) else holes or 0}")
        obs = protocol.Observation("verify", doc.get("verdict") == "verified", text, verdict=doc)
        return obs, res

    # --- the run -------------------------------------------------------------------

    def _had_output(self):
        return self.meter.outputs > 0 or self.proposals > 0

    def _cut(self, cause, detail):
        if self._had_output():
            return f"truncated:{cause}", f"truncated:{cause}", detail
        return "infra-failed", "infra-failed", detail

    def run(self, policy) -> RunResult:
        outcome = ended_by = detail = None
        step = 0
        while True:
            cause = self.meter.cause(budget.TURN_UNITS)
            if cause is not None:
                ended_by = cause
                break
            state = protocol.State(self.ctx.task_id, step, self._digests(), self.last_verify,
                                   tuple(self.history))
            files = self._digests()
            try:
                actions = list(policy.propose(state, self.ctx, self.meter.snapshot()))
                if not actions:
                    raise protocol.Malformed("a proposal holds at least one action")
                if len(actions) > self.ctx.max_actions:
                    raise protocol.Malformed(f"a proposal holds at most {self.ctx.max_actions} "
                                             f"actions, not {len(actions)}")
                for a in actions:
                    if type(a) not in protocol.ACTION_TYPES.values():
                        raise protocol.Malformed(f"{type(a).__name__} is not an action")
            except protocol.Malformed as e:
                self.meter.turns += 1
                self._append("actions.jsonl", {"step": step, "files": files, "malformed": str(e)})
                outcome, ended_by, detail = "malformed", "malformed", str(e)
                break
            except budget.CapReached as e:
                ended_by, detail = e.cause, str(e)
                break
            except backends.TransportError as e:
                if e.had_output:
                    self.proposals += 1
                outcome, ended_by, detail = self._cut(e.cause, str(e))
                break
            except apparatus.ApparatusMismatch as e:
                outcome, ended_by, detail = "apparatus-mismatch", "apparatus-mismatch", str(e)
                break
            except backends.Deferred as e:
                outcome, ended_by, detail = "deferred", "deferred", str(e)
                break
            except policies.ReplayDiverged as e:
                outcome, ended_by, detail = "replay-diverged", "replay-diverged", str(e)
                break
            except (policies.ReplayEnd, policies.ScriptExhausted) as e:
                ended_by, detail = (self.replay_end if isinstance(e, policies.ReplayEnd)
                                    else "script-end"), str(e)
                break
            self.proposals += 1
            self.meter.turns += 1
            self._append("actions.jsonl", {"step": step, "files": files,
                                           "actions": [protocol.action_to_json(a)
                                                       for a in actions]})
            observations, results, stopped, gated = [], [], False, False
            try:
                for a in actions:
                    if isinstance(a, protocol.Read):
                        observations.append(self._read(a))
                    elif isinstance(a, protocol.Edit):
                        observations.append(self._edit(a))
                    elif isinstance(a, protocol.Verify) and self.acceptance is not None:
                        obs, res_list = self._gate(a.mode)
                        observations.append(obs)
                        results += [r.to_dict() for r in res_list]
                        if self.gate_passed == self._digests():
                            gated = True
                            break
                    elif isinstance(a, protocol.Verify):
                        obs, res = self._verify(a.mode)
                        observations.append(obs)
                        results.append(res.to_dict())
                    elif self.acceptance is not None and self.gate_passed != self._digests():
                        observations.append(protocol.Observation(
                            "refused", False, "stop refused: in this arm a run ends only when "
                            "the acceptance tool passes the current work copy (Verify runs it) "
                            "or the budget ends"))
                    else:
                        observations.append(protocol.Observation("stop", True,
                                                                 f"{a.reason}: {a.note}"[:200]))
                        stopped = True
                        break
            except budget.CapReached as e:
                outcome, ended_by, detail = self._cut(e.cause, str(e))
            except tools.RunnerUnavailable as e:
                outcome, ended_by, detail = self._cut("container", str(e))
            except tools.PreflightError as e:
                outcome, ended_by, detail = self._cut("host-memory", str(e))
            self._append("observations.jsonl", {
                "step": step, "observations": [protocol.observation_to_json(o)
                                               for o in observations], "tools": results})
            self.history.append(protocol.Turn(step, tuple(actions), tuple(observations)))
            if outcome is not None:
                break
            if stopped:
                ended_by = "stop"
                break
            if gated:
                ended_by = "gate-pass"    # the gate's own run of the instrument decides
                break
            step += 1
        final = self.final_verify and (outcome is None or outcome == "malformed")
        if final and (self.dirty or self.last_verify is None):
            try:
                obs, res = self._verify("final")
                self._append("observations.jsonl", {"step": "final", "observations":
                                                    [protocol.observation_to_json(obs)],
                                                    "tools": [res.to_dict()]})
            except budget.CapReached as e:
                outcome, ended_by, detail = self._cut(e.cause, str(e))
            except tools.RunnerUnavailable as e:
                outcome, ended_by, detail = self._cut("container", str(e))
            except tools.PreflightError as e:
                outcome, ended_by, detail = self._cut("host-memory", str(e))
        if outcome is None:
            outcome = (self.last_verify or {}).get("verdict", "error")
            if outcome not in VERDICTS:
                outcome = "error"
        if self.run_dir is not None and self.last_verify is not None:
            (self.run_dir / "verify.json").write_text(
                json.dumps(self.last_verify, sort_keys=True, indent=1) + "\n", encoding="utf-8")
        return RunResult(outcome, ended_by or "", self.last_verify, len(self.history),
                         self.meter.usage(), dict(self.files), tuple(self.findings),
                         detail or "")
