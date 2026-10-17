"""The frozen core's own tests: fvh.executor (DV4-PLAN §3.2, §3.6, §4.3, §9): the
action rules on the work copy, the verification runner and its provenance, the
caps, the outcomes of §3.6 and §4.3, the run directory's records, and the
re-derivation of a recorded run. The runners here are isolated fakes and
replays: no solver, no container, no model."""

import hashlib
import json
from pathlib import Path

import pytest

from fvh import backends, budget, executor, policies, protocol as P, runlog, tools
from fvh.tools import runners as R

TASK = "method M() ensures false\n{\n}\n"
GOOD = "method M() ensures true\n{\n}\n"


def doc(verdict="failed", errors=1, holes=0):
    return {"lang": "dafny", "stage": "verify", "verdict": verdict,
            "verified_count": 1 if verdict == "verified" else 0,
            "holes": [{"line": 1}] * holes,
            "diagnostics": [{"line": 2, "severity": "error", "message": "e"}] * errors,
            "findings": [], "exit_code": 0 if verdict == "verified" else 1}


class TextRunner(R.Runner):
    """An isolated fake: the gate's document is chosen by the target file's text."""

    name = "replay"
    isolated = True

    def __init__(self, docs=None, *, kill=None, unavailable=False):
        self.docs = docs or {GOOD: doc("verified", 0)}
        self.kill = kill
        self.unavailable = unavailable
        self.targets = []

    def execute(self, instrument, target, *, timeout_s=None):
        if self.unavailable:
            raise tools.RunnerUnavailable("no container yet")
        self.targets.append(target)
        text = Path(target).read_text()
        sha = hashlib.sha256(text.encode()).hexdigest()
        if self.kill and text == self.kill:
            return tools.ToolResult(instrument, str(target), {"exit_code": 137, "lines": ["k"]},
                                    137, "memory", "replay", "agent", sha)
        d = self.docs.get(text, doc())
        return tools.ToolResult(instrument, str(target), d, d["exit_code"], None, "replay",
                                "agent", sha)


def ctx(**kw):
    base = dict(task_id="T1", lang="dafny", statement="s", editable=("w/task.dfy",),
                readable=("w/given.dfy",), target="w/task.dfy", max_actions=4)
    base.update(kw)
    return P.Context(**base)


def ex(runner=None, *, caps=None, run_dir=None, **kw):
    return executor.Executor(ctx(), {"w/task.dfy": TASK}, runner=runner or TextRunner(),
                             meter=budget.Meter(caps or budget.Caps()), run_dir=run_dir,
                             readable_files={"w/given.dfy": "a\nb\nc\n"}, **kw)


def scripted(*proposals):
    return policies.ScriptedPolicy(proposals)


def test_a_host_runner_is_refused():
    with pytest.raises(tools.ProvenanceError):
        executor.Executor(ctx(), {"w/task.dfy": TASK}, runner=tools.HostRunner(preflight=False))


def test_edit_verify_stop_is_scored_by_the_gate(tmp_path):
    runner = TextRunner()
    e = ex(runner, run_dir=tmp_path)
    res = e.run(scripted([P.Edit("w/task.dfy", "", GOOD), P.Verify()], [P.Stop("done")]))
    assert (res.outcome, res.ended_by, res.steps) == ("verified", "stop", 2)
    assert res.files == {"w/task.dfy": GOOD}
    assert all(not str(t).startswith(str(R.ROOT)) for t in runner.targets)  # never the course tree
    assert tools.provenance_of(runner.targets[0]) == "agent"
    lines = [json.loads(x) for x in (tmp_path / "actions.jsonl").read_text().splitlines()]
    assert [x["step"] for x in lines] == [0, 1]
    assert lines[0]["files"] == {"w/task.dfy": P.text_sha256(TASK)}
    assert lines[1]["files"] == {"w/task.dfy": P.text_sha256(GOOD)}
    assert json.loads((tmp_path / "verify.json").read_text())["verdict"] == "verified"


def test_the_policy_sees_the_last_verification_and_the_history():
    seen = []

    def fn(s, c, b):
        seen.append(s)
        return [P.Edit("w/task.dfy", "", GOOD), P.Verify()] if s.step == 0 else [P.Stop("done")]
    ex().run(policies.MockPolicy(fn))
    assert seen[0].last_verify is None and seen[0].history == ()
    assert seen[1].last_verify["verdict"] == "verified"
    assert [o.kind for o in seen[1].history[0].observations] == ["edit", "verify"]


def test_reference_free_feedback_reaches_policy_and_replays_without_running_probes(tmp_path):
    calls, seen = [], []

    def feedback(work, paths, result):
        calls.append(Path(work, "w/task.dfy").read_text())
        return {"mutation": {"eligible": 3, "killed": 1, "rate": 1 / 3}}

    def policy(state, context, remaining):
        if state.step == 0:
            return [P.Edit("w/task.dfy", "", GOOD), P.Verify()]
        seen.append(state.last_verify["spec_feedback"])
        return [P.Stop("done")]

    result = ex(run_dir=tmp_path, feedback=feedback).run(policies.MockPolicy(policy))
    assert result.outcome == "verified" and calls == [GOOD]
    assert seen[0]["mutation"]["eligible"] == 3
    replay = ex(runner=executor.LogRunner(tmp_path), final_verify=False)
    replayed = replay.run(policies.ReplayPolicy(tmp_path))
    assert replayed.verify["spec_feedback"] == result.verify["spec_feedback"]
    assert calls == [GOOD]


def test_refused_actions_are_observed_and_the_run_goes_on():
    seen = []

    def fn(s, c, b):
        seen.append(s)
        if s.step == 0:
            return [P.Read("w/other.dfy"), P.Edit("w/given.dfy", "a", "b"),
                    P.Edit("w/task.dfy", "nothing", "x"), P.Read("w/given.dfy", 2, 3)]
        return [P.Stop("give-up")]
    res = ex().run(policies.MockPolicy(fn))
    obs = seen[1].history[0].observations
    assert [o.kind for o in obs] == ["refused", "refused", "refused", "read"]
    assert obs[3].text == "b\nc\n"
    assert res.files == {"w/task.dfy": TASK}
    assert res.outcome == "failed" and res.ended_by == "stop"   # the final verification decides


def test_the_read_limit_cuts_and_says_so():
    seen = []
    big = "x" * 100

    def fn(s, c, b):
        seen.append(s)
        return [P.Read("w/given.dfy")] if s.step == 0 else [P.Stop("give-up")]
    e = executor.Executor(ctx(read_limit=10), {"w/task.dfy": TASK}, runner=TextRunner(),
                          readable_files={"w/given.dfy": big})
    e.run(policies.MockPolicy(fn))
    o = seen[1].history[0].observations[0]
    assert o.cut == 90 and "90 bytes cut" in o.text


def test_actions_after_stop_are_not_performed():
    res = ex().run(scripted([P.Stop("give-up"), P.Edit("w/task.dfy", "", GOOD)]))
    assert res.files == {"w/task.dfy": TASK} and res.ended_by == "stop"


@pytest.mark.parametrize("proposal", [
    [],
    [P.Verify()] * 5,                                   # above ctx.max_actions (4)
])
def test_a_proposal_that_does_not_validate_is_malformed(proposal, tmp_path):
    res = ex(run_dir=tmp_path).run(scripted(proposal))
    assert (res.outcome, res.ended_by) == ("malformed", "malformed")
    assert res.verify["verdict"] == "failed"            # the work copy's own verdict is kept
    rec = json.loads((tmp_path / "actions.jsonl").read_text().splitlines()[0])
    assert "malformed" in rec


def test_a_model_reply_that_raises_malformed_ends_the_run():
    def fn(s, c, b):
        raise P.Malformed("the reply is not JSON")
    res = ex().run(policies.MockPolicy(fn))
    assert res.outcome == "malformed" and "not JSON" in res.detail


@pytest.mark.parametrize("caps, cause", [
    (budget.Caps(turns=2), "turn-cap"),
    (budget.Caps(wall_s=0), "wall-clock"),
])
def test_a_cap_ends_the_run_with_its_cause(caps, cause):
    res = ex(caps=caps).run(policies.MockPolicy(lambda s, c, b: [P.Verify()]))
    assert res.ended_by == cause and res.outcome == "failed"


def test_a_call_cap_reached_inside_a_policy():
    meter = budget.Meter(budget.Caps(calls=1))

    def fn(s, c, b):
        meter.before_call()
        meter.charge(calls=1)
        return [P.Edit("w/task.dfy", "", GOOD), P.Verify()]
    e = executor.Executor(ctx(), {"w/task.dfy": TASK}, runner=TextRunner(), meter=meter)
    res = e.run(policies.MockPolicy(fn))
    assert res.ended_by == "call-cap" and res.outcome == "verified" and res.steps == 1


def test_a_killed_verification_is_never_a_pass():
    runner = TextRunner(kill=GOOD)
    res = ex(runner).run(scripted([P.Edit("w/task.dfy", "", GOOD), P.Verify()],
                                  [P.Stop("done")]))
    assert res.outcome == "killed(memory)" and res.verify["killed"] == "memory"


def raising(exc):
    def fn(s, c, b):
        if s.step == 0:
            return [P.Edit("w/task.dfy", "", GOOD)]
        raise exc
    return policies.MockPolicy(fn)


@pytest.mark.parametrize("exc, outcome", [
    (backends.TransportError("rate-limit", "window reached"), "truncated:rate-limit"),
    (backends.TransportError("cli-crash", "crash"), "truncated:cli-crash"),
    (backends.ApparatusMismatch("init"), "apparatus-mismatch"),
    (backends.Deferred("token"), "deferred"),
])
def test_outside_causes_after_output(exc, outcome):
    res = ex().run(raising(exc))
    assert res.outcome == outcome and res.ended_by == outcome


def test_an_outside_cause_before_any_output_is_infra_failed():
    def fn(s, c, b):
        raise backends.TransportError("auth", "rejected")
    res = ex().run(policies.MockPolicy(fn))
    assert (res.outcome, res.ended_by) == ("infra-failed", "infra-failed")


def test_no_container_after_output_truncates_and_before_it_is_infra():
    res = ex(TextRunner(unavailable=True)).run(scripted([P.Verify()]))
    assert res.outcome == "truncated:container"
    def fn(s, c, b):
        raise budget.CapReached("call-cap")
    res = ex(TextRunner(unavailable=True)).run(policies.MockPolicy(fn))
    assert res.outcome == "infra-failed"


def test_a_scripted_policy_that_runs_out():
    res = ex().run(scripted([P.Verify()]))
    assert res.ended_by == "script-end" and res.outcome == "failed"


def record_run(tmp_path, proposals, *, meta_outcome=None, runner=None):
    """A recorded run directory (inputs, logs, run.json), as the executor writes it."""
    runner = runner or TextRunner()
    e = ex(runner, run_dir=tmp_path)
    res = e.run(scripted(*proposals))
    tree = runlog.write_inputs(tmp_path, {"w/task.dfy": TASK.encode()})
    meta = runlog.RunMeta(run_id="r1", module="Q98", arm="A1", task_id="T1", lang="dafny",
                          attempt=1, repeat=1, mode="harness-executed", backend="mock",
                          outcome=meta_outcome or res.outcome, ended_by=res.ended_by,
                          verify=res.verify, inputs_sha256=tree)
    runlog.write_meta(tmp_path, meta)
    return res, meta


def test_a_recorded_run_re_derives_through_its_logs(tmp_path):
    from fvh import report
    res, meta = record_run(tmp_path, [[P.Edit("w/task.dfy", "", "z"), P.Verify()],
                                      [P.Edit("w/task.dfy", "", GOOD)]])
    assert res.outcome == "verified" and res.ended_by == "script-end"
    check = report.rederive(tmp_path, meta)
    assert check.ok and check.derived == "verified"


def test_a_tampered_log_does_not_reproduce(tmp_path):
    from fvh import report
    _, meta = record_run(tmp_path, [[P.Edit("w/task.dfy", "", GOOD), P.Verify()],
                                    [P.Stop("done")]], meta_outcome="failed")
    check = report.rederive(tmp_path, meta)
    assert not check.ok and check.derived == "verified"
    lines = (tmp_path / "actions.jsonl").read_text().splitlines()
    rec = json.loads(lines[1])
    rec["files"]["w/task.dfy"] = "0" * 64
    lines[1] = json.dumps(rec)
    (tmp_path / "actions.jsonl").write_text("\n".join(lines) + "\n")
    check = report.rederive(tmp_path, runlog.RunMeta(**{**meta.to_dict(), "outcome": "verified"}))
    assert not check.ok and check.derived == "replay-diverged"


def test_a_malformed_run_re_derives(tmp_path):
    from fvh import report
    res, meta = record_run(tmp_path, [[P.Edit("w/task.dfy", "", "z")], []])
    assert res.outcome == "malformed"
    check = report.rederive(tmp_path, meta)
    assert check.ok and check.derived == "malformed"


def test_a_capped_run_re_derives_with_its_recorded_end(tmp_path):
    from fvh import report
    e = ex(TextRunner(), caps=budget.Caps(turns=2), run_dir=tmp_path)
    res = e.run(policies.MockPolicy(lambda s, c, b: [P.Edit("w/task.dfy", "", GOOD if s.step
                                                            else "z"), P.Verify()]))
    assert (res.outcome, res.ended_by) == ("verified", "turn-cap")
    tree = runlog.write_inputs(tmp_path, {"w/task.dfy": TASK.encode()})
    meta = runlog.RunMeta(run_id="r2", module="Q98", arm="A1", task_id="T1", lang="dafny",
                          attempt=1, repeat=1, mode="policy", backend="mock",
                          outcome=res.outcome, ended_by=res.ended_by, verify=res.verify,
                          inputs_sha256=tree)
    check = report.rederive(tmp_path, meta)
    assert check.ok and check.derived == "verified"
