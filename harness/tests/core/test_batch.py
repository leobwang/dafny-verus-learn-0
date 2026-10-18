"""The frozen core's own tests: fvh.batch, the live batch runner of `python -m fvh
run` and `resume`, and `fvh report --reverify` (DV4-PLAN §3.6, §4.2-§4.4). On
throwaway git roots holding an invented module Q98 and invented tasks; the
transports are scripted fakes in the transports' reply shape and the
verification runner an isolated fake, so no model is called and no container
runs."""

import gzip
import hashlib
import json
import os
import re
import subprocess
import uuid
from pathlib import Path

import pytest

from fvh import __main__ as cli
from fvh import apparatus, backends, batch, budget, report, runlog, tools
from fvh.tools import runners as R

TASK = "method SmokeM() ensures false\n{\n}\n"
GOOD = "method SmokeM() ensures true\n{\n}\n"
TASK_PATH = "bench/local/q/lab9/{t}/tasks/{t}.dfy"
REGISTRY = """[[module]]
id = "Q98"
status = "authoring"
agentic = []
budget = { claude_calls = 30, claude_runs = 10, qwen_calls = 100, qwen_runs = 20, gpu_hours = 1 }
"""
APP = """schema = 1
[defaults]
calls = 40
turns = 40
wall_s = 2700
gpu_s = 3600
[window]
allowed_overage = ["rejected"]
five_hour_max = 0.8
seven_day_max = 0.6
[backend.claude]
version = "0.0.0-fake"
binary = "~/no/claude"
sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
model = "fake-model"
effort = "low"
max_turns = 2
[backend.qwen]
version = "0.0.0-fake"
binary = "~/no/qwen-cli"
sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
model = "fake:latest"
num_ctx = 32768
"""
ARMS_SRC = '''
class Sampler:
    def __init__(self, ask, seed):
        self.ask, self.seed = ask, seed

    def propose(self, state, ctx, budget):
        from fvh import protocol as P
        if state.step == 0:
            text = self.ask(f"target={ctx.target} sample " + ctx.material["text"], self.seed)
            return [P.Edit(ctx.target, "", text), P.Verify("gate")]
        return [P.Stop("done" if (state.last_verify or {}).get("verdict") == "verified"
                       else "give-up", "")]


class Repair:
    def __init__(self, ask, seeds):
        self.ask, self.seeds, self.n = ask, list(seeds), 0

    def propose(self, state, ctx, budget):
        from fvh import protocol as P
        if (state.last_verify or {}).get("verdict") == "verified" or self.n >= len(self.seeds):
            return [P.Stop("done", "")]
        text = self.ask(f"target={ctx.target} round {self.n}", self.seeds[self.n])
        self.n += 1
        return [P.Edit(ctx.target, "", text), P.Verify("gate")]
'''
OK_INFO = {"status": "allowed", "overageStatus": "rejected", "isUsingOverage": False,
           "unifiedWindows": {"five_hour": {"utilization": 0.1}, "seven_day": {"utilization": 0.1}}}


class Gate(R.Runner):
    """An isolated fake verification runner: GOOD verifies, anything else fails."""

    name = "replay"
    isolated = True
    seen = []

    def execute(self, instrument, target, *, timeout_s=None):
        text = Path(target).read_text()
        ok = text == GOOD
        Gate.seen.append(text)
        doc = {"verdict": "verified" if ok else "failed", "holes": [],
               "verified_count": 1 if ok else 0, "exit_code": 0 if ok else 1, "stage": "verify",
               "diagnostics": [] if ok else [{"severity": "error", "line": 1}]}
        return tools.ToolResult(instrument, str(target), doc, doc["exit_code"], None, "replay",
                                "agent", hashlib.sha256(text.encode()).hexdigest())


class Fake:
    """A scripted transport in the transports' reply shape: each call returns the
    next reply (a candidate file text, an exception, or a callable)."""

    def __init__(self, family, replies, *, window=("ok", ""), rate_limit=None, log=None):
        self.family = family
        self.replies = list(replies)
        self.window = window
        self.rate_limit = rate_limit
        self.log = log if log is not None else []

    def complete(self, message, *, system="", seed=None):
        self.log.append({"message": message, "seed": seed})
        r = self.replies.pop(0) if self.replies else GOOD
        if isinstance(r, BaseException):
            raise r
        m = re.search(r"target=(\S+)", message)
        target = m.group(1) if m else TASK_PATH.format(t="t1")
        obj = {"actions": [{"type": "edit", "path": target, "old": "", "new": r}]}
        return backends.Completion(text="", structured=obj,
                                   usage={"input_tokens": 3, "output_tokens": 2}, turns=1,
                                   rate_limit=self.rate_limit, window=self.window,
                                   apparatus={"family": self.family}, raw=json.dumps(obj) + "\n")


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@example.invalid", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.run(["git", "-C", str(root), *args], check=True, env=env,
                          capture_output=True, text=True).stdout.strip()


class CourseRoot(type(Path())):
    """A course root that also names the test's invented arms module (`mod`)."""


@pytest.fixture
def root(tmp_path, monkeypatch):
    r = CourseRoot(tmp_path / "course")
    r.mkdir()
    git(r, "init", "-q")
    (r / "MODULES.toml").write_text(REGISTRY)
    for t in ("t1", "t2"):
        p = r / TASK_PATH.format(t=t)
        p.parent.mkdir(parents=True)
        p.write_text(TASK)
    mod = f"fvhtest_arms_{uuid.uuid4().hex[:8]}"
    (r / "harness" / "q").mkdir(parents=True)
    (r / "harness" / "q" / f"{mod}.py").write_text(ARMS_SRC)
    (r / "app.toml").write_text(APP)
    git(r, "add", ".")
    git(r, "commit", "-qm", "course")
    monkeypatch.setenv(apparatus.ENV, str(r / "app.toml"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "run"))
    (tmp_path / "run").mkdir()
    r.mod = mod
    Gate.seen = []
    return r


def write_plan(root, *, arms, tasks=("t1",), lab="", repeats=1, attempts=1, extra=""):
    lines = [f'lab = "{lab}"' if lab else "", "seed = 77", f"tasks = {json.dumps(list(tasks))}",
             f"repeats = {repeats}", f"attempts = {attempts}", 'system = "sys"',
             'instructions = "reply with one edit"', extra]
    for t in tasks:
        lines += [f"[task.{t}]", f'path = "{TASK_PATH.format(t=t)}"']
    for name, fam, rounds, policy, construct in arms:
        lines += ["[[arm]]", f'name = "{name}"', f'family = "{fam}"', f"rounds = {rounds}",
                  f'policy = "{policy}"', f'construct = "{construct}"']
    p = root / "plan.toml"
    p.write_text("\n".join(lines) + "\n")
    return p


def make(root, plan_path, transports, *, lever=None):
    plan = batch.load_plan(plan_path, root)
    seen = []

    def runners(task, lang):
        seen.append((task, lang))
        return Gate()
    b = batch.Batch(root, "Q98", plan, transports=transports, runners=runners, log=lambda m: None,
                    app=apparatus.load(root / "app.toml"))
    b.runner_calls = seen
    return b


def states(root):
    return {k: (v.state, v.outcome) for k, v in
            budget.Ledger(budget.ledger_path(root, "Q98")).attempts().items()}


# --- the plan and the seeds ----------------------------------------------------------

def test_seeds_are_a_pure_function_of_the_base_and_the_attempt():
    a = batch.derive_seed(77, "A1/t1/1/1", 0)
    assert a == batch.derive_seed(77, "A1/t1/1/1", 0) and 0 < a < 2 ** 31
    assert a != batch.derive_seed(77, "A1/t1/2/1", 0)          # repeats: independent samples
    assert a != batch.derive_seed(78, "A1/t1/1/1", 0)
    assert a != batch.derive_seed(77, "A1/t1/1/1", 1)


def test_the_plan_is_checked(root):
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")],
                   tasks=("t1", "t2"), repeats=3)
    plan = batch.load_plan(p, root)
    assert len(plan.items()) == 6 and plan.lever_check is False
    seeds = [s for i in plan.items() for s in plan.seeds(i.id)]
    assert len(set(seeds)) == 6
    for bad, why in (('seed = 77', 'base seed'),
                     ('rounds = 1\npolicy', 'one call per attempt')):
        text = p.read_text()
        if why == 'base seed':
            p.write_text(text.replace(bad, ""))
        else:
            p.write_text(text.replace('rounds = 1', 'rounds = 2'))
        with pytest.raises(batch.BatchError, match=why):
            batch.load_plan(p, root)
        p.write_text(text)
    p.write_text(p.read_text().replace(TASK_PATH.format(t="t2"), "bench/none.dfy"))
    with pytest.raises(batch.BatchError, match="unreadable"):
        batch.load_plan(p, root)
    lab = write_plan(root, lab="lab9", arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")])
    assert batch.load_plan(lab, root).lever_check is True


# --- a batch end to end --------------------------------------------------------------

def test_a_batch_runs_every_attempt_and_closes(root):
    log = []
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler"),
                               ("A2", "qwen", 2, f"{root.mod}:Repair", "seeded")],
                   tasks=("t1",), repeats=2)

    def tr(family, run_dir, seeds, caps):
        return batch.RecordingTransport(Fake(family, ["nope", GOOD], log=log), run_dir,
                                        seeds=seeds)
    b = make(root, p, tr)
    assert b.open() == 4
    assert b.run() == 0
    st = states(root)
    assert set(st) == {"A1/t1/1/1", "A1/t1/2/1", "A2/t1/1/1", "A2/t1/2/1"}
    assert all(v[0] == "scored" for v in st.values())
    assert st["A1/t1/1/1"][1] == "failed" and st["A2/t1/1/1"][1] == "verified"
    heads = budget.read_heads(root)
    assert [h["event"] for _, h in heads] == ["open", "close"]
    plan = batch.load_plan(p, root)
    # each call carried its attempt's pre-registered seed
    want = plan.seeds("A1/t1/1/1")[:1] + plan.seeds("A1/t1/2/1")[:1] + plan.seeds("A2/t1/1/1") \
        + plan.seeds("A2/t1/2/1")
    assert [c["seed"] for c in log] == want
    dirs = runlog.run_dirs(root, "Q98")
    assert len(dirs) == 4
    for d in dirs:
        meta = runlog.load_meta(d)
        assert meta.mode == "harness-executed" and meta.apparatus["seeds"]
        assert meta.apparatus["plan_sha256"] == plan.sha256
        for f in ("calls.jsonl", "actions.jsonl", "observations.jsonl", "verify.json",
                  "inputs.tar.gz", "patch.diff", "transcript.jsonl.gz"):
            assert (d / f).is_file(), (d, f)
        assert (d / "returned" / TASK_PATH.format(t="t1")).is_file()
    rep = report.build(root, "Q98")
    assert rep.reproduced, report.format_report(rep)
    note = batch.batch_note(budget.Ledger(budget.ledger_path(root, "Q98")))
    assert note["plan_sha256"] == plan.sha256
    assert (budget.ledger_path(root, "Q98").parent / note["plan_file"]).read_text() == plan.text


def prereg_for(root, body):
    """paper/Q98_answers.tex with `body` in its PREREG block, and a gradebook row
    that unlocks exactly that block; returns the block's full hash."""
    block = f"% PREREG-BEGIN\n{body}% PREREG-END\n"
    (root / "paper").mkdir(exist_ok=True)
    (root / "paper" / "Q98_answers.tex").write_text(block)
    full = hashlib.sha256(block.encode()).hexdigest()
    (root / "instructor").mkdir(exist_ok=True)
    (root / "instructor" / "gradebook.md").write_text(
        f"| 2026-10-12 | Q98 | prereg | 3 sha256 {full[:16]} | none |\n")
    return full


def test_a_lab_batch_needs_its_pre_registration_and_runs_the_lever_check(root):
    p = write_plan(root, lab="lab9", arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")])
    b = make(root, p, lambda *a: batch.RecordingTransport(Fake("qwen", [GOOD]), a[1]))
    with pytest.raises(batch.BatchError, match="pre-registration|answers"):
        b.open()
    assert not budget.ledger_path(root, "Q98").exists()
    sha = batch.load_plan(p, root).sha256
    # graded, but naming no plan, two plans, or another plan: refused (DV5d)
    for body, msg in (("plan\n", "names no batch plan"),
                      (f"plan-sha256: {sha}\n\\texttt{{plan-sha256: {'0' * 64}}}\n",
                       "names 2 different plans"),
                      (f"\\texttt{{plan-sha256: {'ab' * 32}}}\n", "the plan changed after")):
        prereg_for(root, body)
        b = make(root, p, lambda *a: batch.RecordingTransport(Fake("qwen", [GOOD]), a[1]))
        with pytest.raises(batch.BatchError, match=msg):
            b.open()
        assert not budget.ledger_path(root, "Q98").exists()
    full = prereg_for(root, f"\\textbf{{Batch plan}} \\texttt{{plan-sha256: {sha.upper()}}}\n")
    b = make(root, p, lambda *a: batch.RecordingTransport(Fake("qwen", [GOOD]), a[1]))
    b.open()
    seen = []
    b.runners = lambda task, lang: (seen.append(task), Gate())[1]
    assert b.run() == 0
    meta = runlog.load_meta(runlog.run_dirs(root, "Q98")[0])
    assert meta.prereg_sha256 == full and meta.lab == "lab9"
    assert meta.apparatus["lab_task"] == TASK_PATH.format(t="t1") and seen


def test_the_live_runner_passes_the_lab_task_to_the_container_runner(root):
    p = write_plan(root, lab="lab9", arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")])
    plan = batch.load_plan(p, root)
    b = batch.Batch(root, "Q98", plan, transports=lambda *a: None, mem_gb=16,
                    app=apparatus.load(root / "app.toml"))
    r = b._runner(TASK_PATH.format(t="t1"), "dafny")
    assert isinstance(r, tools.ContainerRunner) and r.lab_task == TASK_PATH.format(t="t1")
    assert r.mem_gb == 16
    assert r.argv("vcheck --gate", "x.dfy") == ["scripts/vcheck", "--json", "--gate",
                                                 "--lab-task", "lab-task/" + TASK_PATH.format(t="t1"),
                                                 "x.dfy"]
    assert r.argv("vaudit", "x.dfy") == ["scripts/vaudit", "--json", "x.dfy"]


@pytest.mark.parametrize("value", ["own", "preserve"])
def test_lab_code_permission_survives_recording_and_reverification(root, monkeypatch, value):
    p = write_plan(root, lab="", extra="lever_check = true",
                   arms=[("V", "qwen", 1, f"{root.mod}:Sampler", "sampler")])
    p.write_text(p.read_text() + f'lab_code = "{value}"\n')
    b = make(root, p, lambda f, d, s, c: batch.RecordingTransport(Fake(f, [GOOD]), d, seeds=s))
    arm = b.plan.arm("V")
    live = batch.Batch(root, "Q98", b.plan, app=b.app)._runner(
        TASK_PATH.format(t="t1"), "dafny", arm)
    cmd = live.argv("vcheck --gate", "x.dfy")
    assert ("--lab-code" in cmd) == (value == "own")
    if value == "own":
        assert cmd[cmd.index("--lab-code") + 1] == "own"
    b.open()
    assert b.run() == 0
    rd = runlog.run_dirs(root, "Q98")[0]
    assert runlog.load_meta(rd).apparatus["lab_code"] == value
    seen = []

    class Spy(tools.ContainerRunner):
        def execute(self, instrument, target, *, timeout_s=None):
            seen.append(self.lab_code)
            return Gate().execute(instrument, target)

    monkeypatch.setattr(tools, "ContainerRunner", Spy)
    assert report.reverify(root, "Q98", rd.name).ok
    assert seen == [value]


@pytest.mark.parametrize("value", ["off", "", True, 1])
def test_invalid_lab_code_permission_is_refused(root, value):
    p = write_plan(root, arms=[("V", "qwen", 1, f"{root.mod}:Sampler", "sampler")])
    p.write_text(p.read_text() + f'lab_code = {json.dumps(value)}\n')
    with pytest.raises(batch.BatchError, match="lab_code"):
        batch.load_plan(p, root)


@pytest.mark.parametrize("mode", ["policy", "agent"])
def test_invalid_recorded_lab_code_is_refused_before_replay(root, mode):
    rd = root / "research/runs/Q98/bad-permission"
    runlog.write_inputs(rd, {TASK_PATH.format(t="t1"): TASK.encode()})
    meta = runlog.RunMeta(run_id=rd.name, module="Q98", arm="V", task_id="t1",
                          lang="dafny", attempt=1, repeat=1, mode=mode,
                          backend="qwen", outcome="failed", apparatus={"lab_code": "off"})
    with pytest.raises(ValueError, match="bad-permission: invalid recorded lab_code"):
        report.rederive(rd, meta)


# --- the window, the sentinel, the stops between attempts ----------------------------

def test_a_claude_batch_starts_with_a_sentinel_and_the_window_defers_it(root):
    log = []
    p = write_plan(root, arms=[("C", budget.CLAUDE, 1, f"{root.mod}:Sampler", "sampler")],
                   tasks=("t1", "t2"))
    calls = {"n": 0}

    def tr(family, run_dir, seeds, caps):
        calls["n"] += 1
        win = ("defer", "the five_hour window's utilization 0.85") if calls["n"] == 2 \
            else ("ok", "")
        return batch.RecordingTransport(Fake(family, [GOOD], window=win, rate_limit=OK_INFO,
                                             log=log), run_dir, seeds=seeds)
    b = make(root, p, tr)
    b.open()
    assert b.run() == 3                                   # deferred between attempts
    lines = budget.Ledger(budget.ledger_path(root, "Q98")).read()
    assert [x["kind"] for x in lines].count("sentinel") == 1
    assert "sentinel" in log[0]["message"]
    st = states(root)
    assert st["C/t1/1/1"] == ("scored", "verified") and st["C/t2/1/1"][0] == "deferred"
    assert budget.last_anchor(root, "Q98")["event"] == "open"
    assert budget.read_window(root / budget.WINDOW_FILE) is not None
    # a fresh recorded event lets the resumed batch start without a sentinel
    rc = batch.resume(root, "Q98", transports=lambda f, d, s, c: batch.RecordingTransport(
        Fake(f, [GOOD], rate_limit=OK_INFO, log=log), d, seeds=s), runners=lambda t, l: Gate(),
        log=lambda m: None, app=apparatus.load(root / "app.toml"))
    assert rc == 0
    lines = budget.Ledger(budget.ledger_path(root, "Q98")).read()
    assert [x["kind"] for x in lines].count("sentinel") == 1
    assert states(root)["C/t2/1/1"] == ("scored", "verified")
    assert budget.last_anchor(root, "Q98")["event"] == "close"
    assert report.build(root, "Q98").reproduced


def test_an_apparatus_mismatch_stops_the_batch_and_stays_re_issuable(root):
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")],
                   tasks=("t1", "t2"))
    b = make(root, p, lambda f, d, s, c: batch.RecordingTransport(
        Fake(f, [apparatus.ApparatusMismatch("the init assertions failed")]), d, seeds=s))
    b.open()
    assert b.run() == 3
    st = states(root)
    assert st["A1/t1/1/1"][0] == "infra-failed" and st["A1/t2/1/1"][0] == "deferred"
    assert budget.resume_order(budget.Ledger(budget.ledger_path(root, "Q98"))) == \
        ["A1/t1/1/1", "A1/t2/1/1"]


# --- interruption and resume ---------------------------------------------------------

def test_an_interruption_after_model_output_is_scored_and_never_re_issued(root):
    p = write_plan(root, arms=[("A2", "qwen", 2, f"{root.mod}:Repair", "seeded")],
                   tasks=("t1", "t2"))
    b = make(root, p, lambda f, d, s, c: batch.RecordingTransport(
        Fake(f, ["nope", batch.Interrupted()]), d, seeds=s))
    b.open()
    assert b.run() == 1
    st = states(root)
    assert st["A2/t1/1/1"] == ("scored", "truncated:interrupted")
    assert st["A2/t2/1/1"] == ("planned", None)
    meta = runlog.load_meta(runlog.run_dirs(root, "Q98")[0])
    assert meta.outcome == "truncated:interrupted"
    assert runlog.to_run_record(meta).verdict == "inconclusive"
    assert budget.resume_order(budget.Ledger(budget.ledger_path(root, "Q98"))) == ["A2/t2/1/1"]
    rep = report.build(root, "Q98")
    assert rep.reproduced, report.format_report(rep)


def test_an_interruption_before_model_output_is_re_issued_with_the_same_seeds(root):
    log = []
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")])
    b = make(root, p, lambda f, d, s, c: batch.RecordingTransport(
        Fake(f, [batch.Interrupted()], log=log), d, seeds=s))
    b.open()
    assert b.run() == 1
    assert states(root)["A1/t1/1/1"][0] == "infra-failed"
    rc = batch.resume(root, "Q98", transports=lambda f, d, s, c: batch.RecordingTransport(
        Fake(f, [GOOD], log=log), d, seeds=s), runners=lambda t, l: Gate(), log=lambda m: None,
        app=apparatus.load(root / "app.toml"))
    assert rc == 0 and states(root)["A1/t1/1/1"] == ("scored", "verified")
    assert log[0]["seed"] == log[1]["seed"]


def test_resume_settles_what_a_killed_runner_left_running(root):
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")],
                   tasks=("t1", "t2"))
    b = make(root, p, lambda *a: None)
    b.open()
    lg = budget.Ledger(budget.ledger_path(root, "Q98"))
    # the runner was killed: one attempt had a model answer recorded, one had none
    for aid, rid, answered in (("A1/t1/1/1", "r-out", True), ("A1/t2/1/1", "r-none", False)):
        lg.move(aid, "running", run_id=rid)
        d = lg.path.parent / rid
        d.mkdir()
        runlog.write_inputs(d, {TASK_PATH.format(t=aid.split("/")[1]): TASK.encode()})
        if answered:
            (d / "calls.jsonl").write_text(json.dumps({"n": 0, "had_output": True}) + "\n")
    rc = batch.resume(root, "Q98", transports=lambda f, d, s, c: batch.RecordingTransport(
        Fake(f, [GOOD]), d, seeds=s), runners=lambda t, l: Gate(), log=lambda m: None,
        app=apparatus.load(root / "app.toml"))
    assert rc == 0
    st = states(root)
    assert st["A1/t1/1/1"] == ("scored", "truncated:interrupted")
    assert st["A1/t2/1/1"] == ("scored", "verified")          # re-issued under its id
    assert budget.last_anchor(root, "Q98")["event"] == "close"
    killed = runlog.load_meta(lg.path.parent / "r-out")
    assert "runner-killed" in killed.findings
    rep = report.build(root, "Q98")
    text = report.format_report(rep)
    assert rep.reproduced, text
    assert "excluded infra-failed 1" in text


def test_resume_refuses_a_changed_plan_copy(root):
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")])
    b = make(root, p, lambda *a: None)
    b.open()
    note = batch.batch_note(budget.Ledger(budget.ledger_path(root, "Q98")))
    copy = budget.ledger_path(root, "Q98").parent / note["plan_file"]
    copy.write_text(copy.read_text().replace("seed = 77", "seed = 78"))
    with pytest.raises(batch.BatchError, match="differs"):
        batch.resume(root, "Q98", transports=lambda *a: None, runners=lambda t, l: Gate(),
                     app=apparatus.load(root / "app.toml"))


# --- reverify and the agent-mode re-derivation ---------------------------------------

def test_reverify_repeats_each_verification_and_finds_a_difference(root):
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")],
                   tasks=("t1", "t2"))
    replies = [GOOD, "nope"]
    b = make(root, p, lambda f, d, s, c: batch.RecordingTransport(
        Fake(f, [replies.pop(0)]), d, seeds=s))
    b.open()
    b.run()
    git(root, "add", ".")
    git(root, "commit", "-qm", "the batch")
    got = report.reverify_all(root, "Q98", runner=Gate())
    assert len(got) == 2 and all(r.ok for r in got)
    assert {r.derived[0] for r in got} == {"verified", "failed"}
    d = [x for x in runlog.run_dirs(root, "Q98") if runlog.load_meta(x).outcome == "verified"][0]
    (d / "returned" / TASK_PATH.format(t="t1")).write_text("tampered\n")
    r = report.reverify(root, "Q98", d.name, runner=Gate())
    assert not r.ok and r.recorded[0] == "verified" and r.derived[0] == "failed"


def test_reverify_with_the_container_runner_stages_the_runs_commit(root, monkeypatch):
    p = write_plan(root, lab="", arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")])
    b = make(root, p, lambda f, d, s, c: batch.RecordingTransport(Fake(f, [GOOD]), d, seeds=s))
    b.open()
    b.run()
    seen = {}

    class Spy(tools.ContainerRunner):
        def execute(self, instrument, target, *, timeout_s=None):
            seen.update(rev=self.rev, mem=self.mem_gb, lab=self.lab_task,
                        text=Path(target).read_text())
            return Gate().execute(instrument, target)
    monkeypatch.setattr(tools, "ContainerRunner", Spy)
    rid = runlog.run_dirs(root, "Q98")[0].name
    r = report.reverify(root, "Q98", rid, mem_gb=16)
    assert r.ok and seen["rev"] == git(root, "rev-parse", "HEAD") and seen["mem"] == 16
    assert seen["text"] == GOOD


def test_an_agent_mode_run_is_re_derived_from_its_records(root):
    d = root / "research" / "runs" / "Q98" / "agent-1"
    rel = "dafny/Q/Q98/a.dfy"
    runlog.write_inputs(d, {rel: TASK.encode()})
    (d / "returned" / "dafny/Q/Q98").mkdir(parents=True)
    (d / "returned" / rel).write_text(GOOD)
    gate = {"verdict": "verified", "holes": [], "verified_count": 1}
    (d / "verify.json").write_text(json.dumps({"schema": 1, "gate": gate, "lines": []}))
    runlog.write_meta(d, runlog.RunMeta(run_id="agent-1", module="Q98", arm="replay",
                                        task_id="a", lang="dafny", attempt=1, repeat=1,
                                        mode="agent", backend="qwen-agent", outcome="verified",
                                        verify=gate))
    c = report.rederive(d, runlog.load_meta(d))
    assert c.ok and c.derived == "verified" and "agent run" in c.detail
    (d / "returned" / "dafny/Q/Q98/extra.dfy").write_text("x")
    assert not report.rederive(d, runlog.load_meta(d)).ok
    (d / "returned" / "dafny/Q/Q98/extra.dfy").unlink()
    r = report.reverify(root, "Q98", "agent-1", runner=Gate())
    assert r.ok and r.target == rel


# --- the command line ----------------------------------------------------------------

def test_cli_run_dry_run_and_the_ci_refusal(root, capsys, monkeypatch):
    (root / "app-min.toml").write_text("schema = 1\n[defaults]\ncalls = 4\n")
    monkeypatch.setenv(apparatus.ENV, str(root / "app-min.toml"))
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")],
                   tasks=("t1", "t2"), repeats=2)
    assert cli.main(["--root", str(root), "run", "Q98", "--plan", str(p), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "plan of 4 attempt(s)" in out and "base seed 77" in out
    monkeypatch.setenv("FVH_NO_MODEL", "1")
    assert cli.main(["--root", str(root), "run", "Q98", "--plan", str(p)]) == 3
    assert "FVH_NO_MODEL" in capsys.readouterr().err
    monkeypatch.delenv("FVH_NO_MODEL")
    monkeypatch.setenv("DVL_NO_DOCKER", "1")
    assert cli.main(["--root", str(root), "run", "Q98", "--plan", str(p)]) == 3
    assert not budget.ledger_path(root, "Q98").exists()
    big = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")],
                     tasks=("t1", "t2"), repeats=30)
    assert cli.main(["--root", str(root), "run", "Q98", "--plan", str(big), "--dry-run"]) == 3
    assert "qwen_runs = 20" in capsys.readouterr().err


def test_cli_resume_dry_run_lists_what_it_would_settle(root, capsys):
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")],
                   tasks=("t1", "t2"))
    b = make(root, p, lambda *a: None)
    b.open()
    budget.Ledger(budget.ledger_path(root, "Q98")).move("A1/t1/1/1", "running", run_id="x")
    capsys.readouterr()
    assert cli.main(["--root", str(root), "resume", "Q98", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "settle A1/t1/1/1" in out and "A1/t2/1/1" in out


def test_secret_patterns_match_the_sandbox_scan():
    blob = b'x "accessToken": "abcdefghij" y'
    assert batch.secret_hits(blob) == ["oauth-json-key"]
    assert batch.secret_hits(b"plain text") == []


def test_a_transcript_with_a_credential_shape_is_withheld(root):
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")])

    class Leaky(Fake):
        def complete(self, message, *, system="", seed=None):
            c = super().complete(message, system=system, seed=seed)
            import dataclasses
            return dataclasses.replace(c, raw='{"accessToken": "abcdefghijk"}\n')
    b = make(root, p, lambda f, d, s, c: batch.RecordingTransport(Leaky(f, [GOOD]), d, seeds=s))
    b.open()
    b.run()
    d = runlog.run_dirs(root, "Q98")[0]
    meta = runlog.load_meta(d)
    assert not (d / "transcript.jsonl.gz").exists()
    assert "secret-scan:withheld" in meta.findings and meta.secret_scan["hits"]


def test_the_gate_config_carries_the_runs_seeds(root):
    from fvh.backends import gate as G
    app_text = APP + ('[model_server]\nmodels = { "fake:latest" = "' + "a" * 64 + '" }\n'
                      'options = { temperature = 0.6, seed = 1 }\nmargin = 512\n')
    (root / "app2.toml").write_text(app_text)
    cfg = G.gate_config(apparatus.load(root / "app2.toml"), seeds=[5, 6], calls=2, gpu_s=30)
    assert cfg["seeds"] == [5, 6] and cfg["caps"] == {"calls": 2, "gpu_s": 30.0}
    assert cfg["digest"] == "a" * 64 and cfg["unload_on_stop"] is False
    with pytest.raises(G.GateError):
        G.gate_config(apparatus.load(root / "app2.toml"), seeds=[], calls=1)


def test_the_gpu_calendar_lock_defers_a_second_batch(tmp_path):
    from fvh.backends import gate as G
    with G.GpuCalendar(base=tmp_path):
        with pytest.raises(backends.Deferred):
            G.GpuCalendar(base=tmp_path).__enter__()
    with G.GpuCalendar(base=tmp_path):
        pass


def test_no_gate_starts_under_the_ci_switch(root, monkeypatch, tmp_path):
    from fvh.backends import gate as G
    monkeypatch.setenv("FVH_NO_MODEL", "1")
    with pytest.raises(backends.ModelDisabled):
        G.HostGate(tmp_path / "rd", {"model": "m"})


def test_gzip_of_the_gate_log(tmp_path):
    (tmp_path / "gate.log").write_text("x\n")
    batch._compress_gate_log(tmp_path)
    assert gzip.decompress((tmp_path / "gate.log.gz").read_bytes()) == b"x\n"
    assert not (tmp_path / "gate.log").exists()


def test_an_arm_that_cannot_be_built_refuses_the_batch_before_any_write(root):
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:NoSuchArm", "sampler")])
    b = make(root, p, lambda *a: None)
    with pytest.raises(batch.BatchError, match="NoSuchArm"):
        b.open()
    assert not budget.ledger_path(root, "Q98").exists()
    assert budget.read_heads(root) == []


def test_spent_gpu_hours_stop_a_qwen_batch_between_attempts(root):
    (root / "MODULES.toml").write_text(REGISTRY.replace("gpu_hours = 1", "gpu_hours = 0.001"))
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")],
                   tasks=("t1", "t2"))

    class Hot(Fake):
        def complete(self, message, *, system="", seed=None):
            import dataclasses
            return dataclasses.replace(super().complete(message, system=system, seed=seed),
                                       gpu_s=10.0)
    b = make(root, p, lambda f, d, s, c: batch.RecordingTransport(Hot(f, [GOOD]), d, seeds=s))
    b.open()
    assert b.run() == 3
    st = states(root)
    assert st["A1/t1/1/1"][0] == "scored" and st["A1/t2/1/1"][0] == "deferred"
    lines = budget.Ledger(budget.ledger_path(root, "Q98")).read()
    assert [x.get("gpu_s") for x in lines if x.get("state") == "scored"] == [10.0]


# --- the DV5c fix round: overage, drift, the server, the scan, the lever, the ledger ---

FAKE_CLI = r'''#!/bin/sh
echo x >> "@LOG@"
cat <<JSON
{"type":"system","subtype":"init","tools":["StructuredOutput"],"mcp_servers":[],"model":"fake-model","apiKeySource":"none","claude_code_version":"0.0.0-fake","cwd":"$PWD","plugins":[],"skills":[]}
{"type":"rate_limit_event","rate_limit_info":{"status":"allowed","overageStatus":"allowed","isUsingOverage":true}}
{"type":"assistant","message":{"model":"fake-model"}}
{"type":"result","is_error":false,"num_turns":1,"structured_output":{"actions":[{"type":"stop","reason":"done","note":""}]},"usage":{}}
JSON
'''


def _fake_claude(root, tmp_path):
    """A pinned fake CLI whose every call reports overage (an invented stream)."""
    import time as _t
    home = Path(os.environ["HOME"])
    (home / "bin").mkdir(parents=True)
    (home / ".claude").mkdir()
    fb = home / "bin" / "claude-fake"
    fb.write_text(FAKE_CLI.replace("@LOG@", str(tmp_path / "calls.log")))
    fb.chmod(0o755)
    (home / ".claude" / ".credentials.json").write_text(json.dumps(
        {"claudeAiOauth": {"accessToken": "tok", "expiresAt": (_t.time() + 86400) * 1000}}))
    app = (root / "app.toml").read_text().replace('binary = "~/no/claude"',
                                                 'binary = "~/bin/claude-fake"', 1)
    app = app.replace('sha256 = "' + "0" * 64 + '"',
                      f'sha256 = "{hashlib.sha256(fb.read_bytes()).hexdigest()}"', 1)
    (root / "app.toml").write_text(app)
    budget.write_window(root / budget.WINDOW_FILE, OK_INFO)
    return lambda: len((tmp_path / "calls.log").read_text().splitlines()) \
        if (tmp_path / "calls.log").exists() else 0


def test_an_overage_stop_is_sticky_across_resume(root, tmp_path, monkeypatch):
    monkeypatch.delenv("FVH_NO_MODEL", raising=False)   # the CLI is an invented fake
    calls = _fake_claude(root, tmp_path)
    p = write_plan(root, arms=[("c", budget.CLAUDE, 1, f"{root.mod}:Sampler", "sampler")],
                   tasks=("t1", "t2"))
    b = batch.Batch(root, "Q98", batch.load_plan(p, root), runners=lambda t, l: Gate(),
                    log=lambda m: None, app=apparatus.load(root / "app.toml"))
    b.open()
    assert b.run() == 3 and calls() == 1
    led = budget.Ledger(budget.ledger_path(root, "Q98"))
    assert led.overage_stop() is not None
    assert budget.read_window(root / budget.WINDOW_FILE)["rate_limit_info"]["isUsingOverage"]
    moved = [x for x in led.read() if x.get("state") == "infra-failed"]
    assert moved and moved[0]["calls"] == 1                  # the call that ran is counted
    assert led.used()[budget.CLAUDE]["calls"] == 3
    for _ in range(2):                                     # every resume refuses, no call
        assert batch.resume(root, "Q98", runners=lambda t, l: Gate(), log=lambda m: None,
                            app=apparatus.load(root / "app.toml"), check_apparatus=False) == 3
    assert calls() == 1
    with pytest.raises(batch.BatchError, match="overage stop"):   # nor does a new batch open
        batch.Batch(root, "Q98", batch.load_plan(p, root), runners=lambda t, l: Gate(),
                    app=apparatus.load(root / "app.toml")).open()
    # the human clears it: the next call runs (and stops again on this fake)
    assert batch.resume(root, "Q98", runners=lambda t, l: Gate(), log=lambda m: None,
                        app=apparatus.load(root / "app.toml"), after_overage_check=True,
                        check_apparatus=False) == 3
    assert calls() == 2 and led.overage_stop() is not None


def test_resume_refuses_on_drift_and_a_changed_apparatus_file(root, monkeypatch, capsys):
    p = write_plan(root, arms=[("a", "qwen", 1, f"{root.mod}:Sampler", "sampler")])
    b = make(root, p, lambda *a: None)
    b.open()
    (root / "app.toml").write_text((root / "app.toml").read_text()
                                   + '[pins]\nimages_lock_sha256 = "' + "1" * 64 + '"\n')
    with pytest.raises(batch.BatchError, match="changed since the batch opened"):
        batch.resume(root, "Q98", transports=lambda *a: None, runners=lambda t, l: Gate(),
                     app=apparatus.load(root / "app.toml"))
    with pytest.raises(batch.BatchError, match="apparatus drift: .*images_lock"):
        batch.resume(root, "Q98", transports=lambda *a: None, runners=lambda t, l: Gate(),
                     app=apparatus.load(root / "app.toml"), new_apparatus=True,
                     check_apparatus=True)
    notes = budget.Ledger(budget.ledger_path(root, "Q98")).notes("apparatus-changed")
    assert len(notes) == 1
    reached = {}
    monkeypatch.setattr(batch, "resume", lambda *a, **k: reached.setdefault("r", 0))
    monkeypatch.delenv("FVH_NO_MODEL", raising=False)
    monkeypatch.delenv("DVL_NO_DOCKER", raising=False)
    assert cli.main(["--root", str(root), "resume", "Q98"]) == 3
    assert "apparatus drift" in capsys.readouterr().err and "r" not in reached


def test_the_model_server_is_checked_against_its_pins(root, monkeypatch):
    from fvh.backends import gate as G
    app_text = APP + ('[model_server]\nversion = "0.33.2"\nmodels = { "fake:latest" = "'
                      + "a" * 64 + '" }\nunit = { OLLAMA_KV_CACHE_TYPE = "q8_0" }\n'
                      'options = { seed = 1 }\n')
    (root / "app.toml").write_text(app_text)
    app = apparatus.load(root / "app.toml")
    good = {"reachable": True, "version": "0.33.2", "models": {"fake:latest": "a" * 64},
            "unit": {"OLLAMA_KV_CACHE_TYPE": "q8_0"}}
    assert G.server_drift(app, good) == []
    bad = {**good, "version": "0.34.0", "unit": {"OLLAMA_KV_CACHE_TYPE": "f16"},
           "models": {"fake:latest": "b" * 64}}
    assert {d.field for d in G.server_drift(app, bad)} == {
        "model_server.version", "model_server.unit.OLLAMA_KV_CACHE_TYPE",
        "model_server.models.fake:latest"}
    assert [d.field for d in G.server_drift(app, {"reachable": False})] == [
        "model_server.reachable"]
    # a live Qwen batch refuses before its first attempt, nothing moved
    p = write_plan(root, arms=[("a", "qwen", 1, f"{root.mod}:Sampler", "sampler")])
    b = batch.Batch(root, "Q98", batch.load_plan(p, root), runners=lambda t, l: Gate(),
                    log=lambda m: None, app=app)
    monkeypatch.setattr(G, "server_facts", lambda app, **k: bad)
    b.open()
    assert b.run() == 3 and "model_server.version" in b.stop
    assert states(root) == {"a/t1/1/1": ("planned", None)}


def test_a_gate_that_does_not_start_stops_the_batch(root, monkeypatch):
    from fvh.backends import gate as G
    p = write_plan(root, arms=[("a", "qwen", 1, f"{root.mod}:Sampler", "sampler")],
                   tasks=("t1", "t2"))

    def boom(family, rd, seeds, caps):
        raise G.GateError("the model gate did not start: fake:latest has digest None")
    b = make(root, p, boom)
    b.open()
    assert b.run() == 3 and "apparatus mismatch" in b.stop
    st = states(root)
    assert st["a/t1/1/1"][0] == "infra-failed" and st["a/t2/1/1"][0] == "deferred"


def test_every_file_of_a_run_goes_through_the_secret_scan(root):
    token = "sk-ant-oat01-" + "Q" * 40
    p = write_plan(root, arms=[("a", "qwen", 1, f"{root.mod}:Sampler", "sampler")])

    class FakeGate:
        def __init__(self, rd):
            self.rd = rd

        def counts(self):
            return {"calls": 1, "gpu_s": 1.0}

        def stop(self):
            (self.rd / "gate.log").write_text(json.dumps({"response": f"reply {token}"}) + "\n")

    def transports(family, rd, seeds, caps):
        t = batch.RecordingTransport(Fake(family, [GOOD + f"// {token}\n"]), rd, seeds=seeds)
        t.gate_handle = FakeGate(rd)
        return t
    b = make(root, p, transports)
    b.open()
    b.run()
    d = runlog.run_dirs(root, "Q98")[0]
    meta = runlog.load_meta(d)
    assert "secret-scan:withheld" in meta.findings
    names = set(meta.secret_scan["withheld"])
    assert {"gate.log.gz", "patch.diff", "actions.jsonl"} <= names
    assert any(n.startswith("returned/") for n in names)
    for f in d.rglob("*"):
        if f.is_file():
            data = f.read_bytes()
            data = gzip.decompress(data) if f.suffix == ".gz" else data
            assert token.encode() not in data, f
    rec = meta.secret_scan["withheld_files"][0]
    assert set(rec) == {"name", "size", "sha256", "findings"}


def test_a_lab_plan_cannot_turn_off_the_lever_check(root):
    p = write_plan(root, lab="lab9", arms=[("a", "qwen", 1, f"{root.mod}:Sampler", "sampler")],
                   extra="lever_check = false")
    with pytest.raises(batch.BatchError, match="always runs the lab gate's lever check"):
        batch.load_plan(p, root)


def test_stale_state_directories_are_reaped(root, tmp_path):
    base = Path(os.environ["XDG_RUNTIME_DIR"]) / "fvh-claude-state"
    base.mkdir()
    old, new = base / "old", base / "new"
    for d in (old, new):
        (d / "config").mkdir(parents=True)
        (d / "config" / ".credentials.json").write_text("{}")
    os.utime(old, (0, 0))
    assert batch._reap_state(apparatus.load(root / "app.toml")) == 1
    assert not old.exists() and new.exists()


def test_reverify_does_not_report_an_unverified_last_edit(root):
    (root / "harness" / "q" / f"{root.mod}.py").write_text(
        (root / "harness" / "q" / f"{root.mod}.py").read_text() + '''
class EditThenCut:
    def __init__(self, ask, seeds):
        self.ask, self.seeds, self.n = ask, list(seeds), 0

    def propose(self, state, ctx, budget):
        from fvh import protocol as P
        text = self.ask(f"target={ctx.target} round {self.n}", self.seeds[self.n])
        self.n += 1
        if state.step == 0:
            return [P.Edit(ctx.target, "", text), P.Verify("gate")]
        return [P.Edit(ctx.target, "", text)]
''')
    p = write_plan(root, arms=[("r", "qwen", 3, f"{root.mod}:EditThenCut", "seeded")])
    cut = backends.TransportError("cli-crash", "cut", had_output=True)
    b = make(root, p, lambda f, d, s, c: batch.RecordingTransport(Fake(f, [GOOD, TASK, cut]), d,
                                                                   seeds=s))
    b.open()
    b.run()
    git(root, "add", "-A")
    git(root, "commit", "-qm", "the batch")
    [r] = report.reverify_all(root, "Q98", runner=Gate())
    assert r.ok and "never verified" in r.detail


def test_resume_dry_run_uses_the_plans_max_reissue(root, capsys):
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")],
                   extra="max_reissue = 1")
    b = make(root, p, lambda *a: None)
    b.open()
    led = budget.Ledger(budget.ledger_path(root, "Q98"))
    led.move("A1/t1/1/1", "running")
    led.move("A1/t1/1/1", "infra-failed")
    led.move("A1/t1/1/1", "running")
    led.move("A1/t1/1/1", "infra-failed", max_reissue=1)
    capsys.readouterr()
    assert cli.main(["--root", str(root), "resume", "Q98", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "A1/t1/1/1" not in out and "max_reissue 1" in out


def test_resume_refuses_re_issues_past_the_registry_budget(root):
    (root / "MODULES.toml").write_text(REGISTRY.replace("qwen_calls = 100", "qwen_calls = 2"))
    git(root, "commit", "-qam", "budget")
    p = write_plan(root, arms=[("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")],
                   tasks=("t1", "t2"))
    b = make(root, p, lambda *a: None)
    b.open()
    led = budget.Ledger(budget.ledger_path(root, "Q98"))
    led.move("A1/t1/1/1", "running")
    led.move("A1/t1/1/1", "infra-failed", calls=1)
    with pytest.raises(batch.BatchError, match="re-issuing would need"):
        batch.resume(root, "Q98", transports=lambda *a: None, runners=lambda t, l: Gate(),
                     app=apparatus.load(root / "app.toml"))


# =====================================================================================
# Agent mode (construct "agent": the user's decision D8; DV5d). A scripted agent in the
# live route's interface stands in for the agent's container: each session returns
# scripted files and writes the gate's counts into its session directory as the live
# gate does, so no model is called and no container starts.
# =====================================================================================

from fvh.backends import agent as AG  # noqa: E402

CRATE = "bench/local/q/lab9/{t}/tasks"
GOOD_RS = "// good\nfn agent_smoke_ok() {}\n"
STUB_RS = "// stub\nfn agent_smoke_ok() { unimplemented!() }\n"
CARGO = '[package]\nname = "agent_smoke_c1"\nversion = "0.1.0"\n'
FROZEN = "// frozen statements\n"
GATE_SRC = '''
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Pins:
    min_verified: int
    symbols: tuple


@dataclass(frozen=True)
class CrateTarget:
    id: str
    lang: str
    target: str
    files: tuple
    pins: Pins


@dataclass(frozen=True)
class Verdict:
    word: str
    reasons: tuple


@dataclass(frozen=True)
class Result:
    id: str
    verdict: Verdict


def render(v):
    return v.word


def gate_crate(target, *, run=None):
    g = run("vcheck --gate", target.target)
    a = run("vaudit", target.target)
    ok = g.document.get("verdict") == "verified" and a.exit_code == 0 \\
        and all(Path(f).is_file() for f in target.files)
    return Result(target.id, Verdict("PASS" if ok else "FAIL",
                                     () if ok else ("vcheck --gate: not a complete pass",)))
'''


class CrateGate(R.Runner):
    """An isolated fake verification runner over a crate directory: a crate whose
    src/lib.rs is GOOD_RS, with its read-only companions beside it, verifies."""

    name = "replay"
    isolated = True

    def execute(self, instrument, target, *, timeout_s=None):
        t = Path(target)
        lib = (t / "src" / "lib.rs").read_text() if (t / "src" / "lib.rs").is_file() else ""
        ok = lib == GOOD_RS and (t / "Cargo.toml").read_text() == CARGO \
            and (t / "frozen.rs").read_text() == FROZEN
        doc = {"verdict": "verified" if ok else "failed", "holes": [],
               "verified_count": 1 if ok else 0, "exit_code": 0 if ok else 1, "stage": "verify",
               "diagnostics": [] if ok else [{"severity": "error", "line": 1}]}
        return tools.ToolResult(instrument, str(target), doc, 0 if ok else 1, None, "replay",
                                "agent", hashlib.sha256(lib.encode()).hexdigest())


class ScriptedAgent:
    """The agent-mode route (fvh.backends.agent.LiveAgent's interface), scripted. Each
    session takes the next step: {"returned": {path: text} or callable(spec), "calls":
    n, "code": 0|1|124, "agent_end": "exit"|"error"|"wall-clock", "ended_by": ...,
    "raise": an exception raised after the gate's counts are written, "transcript":
    bytes, "seg_calls": the calls the returned Segment carries (default "calls")}. A
    session writes TASK.md and gate-counts.json into its directory, as the live
    session does."""

    def __init__(self, steps=(), problems=()):
        self.steps = list(steps)
        self.problems = list(problems)
        self.specs = []
        self.preflights = []

    def preflight(self, spec):
        self.preflights.append(spec)
        return list(self.problems)

    def run_segment(self, spec):
        self.specs.append(spec)
        st = self.steps.pop(0) if self.steps else {}
        seg = Path(spec.seg_dir)
        seg.mkdir(parents=True, exist_ok=True)
        (seg / "TASK.md").write_text(spec.brief)
        calls = min(int(st.get("calls", 1)), spec.turns)
        (seg / "gate-counts.json").write_text(json.dumps(
            {"calls": calls, "gpu_s": 2.0 * calls, "prompt_tokens": 10 * calls,
             "output_tokens": 3 * calls, "capped": st.get("capped", 0), "ctx_saturated": 0}))
        if "transcript" in st:
            (seg / "transcript.jsonl.gz").write_bytes(gzip.compress(st["transcript"]))
        if "raise" in st:
            raise st["raise"]
        ret = st.get("returned", {})
        if callable(ret):
            ret = ret(spec)
        code = st.get("code", 0)
        sc = int(st.get("seg_calls", calls))   # a Segment without the sandbox's record
        return AG.Segment(code=code, ended_by=st.get("ended_by", "done" if code == 0 else
                                                     "start-failed"),
                          agent_end=st.get("agent_end", "exit" if code == 0 else ""),
                          returned=dict(ret), calls=sc, gpu_s=2.0 * sc,
                          prompt_tokens=10 * sc, output_tokens=3 * sc,
                          capped=st.get("capped", 0), selftest_ok=st.get("selftest_ok", True),
                          manifest_sha256="ab" * 32, image="dvl-agent@sha256:" + "cd" * 32,
                          detail=st.get("detail", ""))


def agent_plan(root, *, arms, tasks=("t1",), repeats=1, lab="", extra="", crate=False):
    lines = [f'lab = "{lab}"' if lab else "", "seed = 77", f"tasks = {json.dumps(list(tasks))}",
             f"repeats = {repeats}", 'instructions = "Make the file verify."', extra]
    for t in tasks:
        lines += [f"[task.{t}]", f'path = "{(CRATE if crate else TASK_PATH).format(t=t)}"',
                  f'statement = "the statement of {t}"']
    for name, rounds, acceptance in arms:
        lines += ["[[arm]]", f'name = "{name}"', 'family = "qwen"', f"rounds = {rounds}",
                  'construct = "agent"', f'acceptance = "{acceptance}"']
    p = root / "plan.toml"
    p.write_text("\n".join(lines) + "\n")
    return p


def make_agent(root, plan_path, agent, *, runner=None):
    plan = batch.load_plan(plan_path, root)
    return batch.Batch(root, "Q98", plan, runners=lambda task, lang: (runner or Gate)(),
                       agent=agent, log=lambda m: None, app=apparatus.load(root / "app.toml"))


def put_crate(root, t="c1"):
    d = root / CRATE.format(t=t)
    (d / "src").mkdir(parents=True)
    (d / "Cargo.toml").write_text(CARGO)
    (d / "frozen.rs").write_text(FROZEN)
    (d / "src" / "lib.rs").write_text(STUB_RS)
    gmod = f"fvhtest_gate_{uuid.uuid4().hex[:8]}"
    (root / "harness" / "q" / f"{gmod}.py").write_text(GATE_SRC)
    git(root, "add", ".")
    git(root, "commit", "-qm", "crate")
    gate = f"harness/q/{gmod}.py"
    return f'gate = "{gate}"\ngate_sha256 = "{hashlib.sha256((root / gate).read_bytes()).hexdigest()}"'


def agent_runs(root):
    """{"<task>/<repeat>": (RunMeta, run directory)} of the module's runs."""
    out = {}
    for d in runlog.run_dirs(root, "Q98"):
        m = runlog.load_meta(d)
        out[f"{m.task_id}/{m.repeat}"] = (m, d)
    return out


def test_an_agent_arm_is_checked(root):
    p = agent_plan(root, arms=[("Q", 40, "verify")])
    plan = batch.load_plan(p, root)
    assert plan.arms[0].agent and plan.arms[0].policy == "" and len(plan.seeds("Q/t1/1/1")) == 40
    text = p.read_text()
    for bad, match in (('family = "qwen"', 'family = "claude"'), ("rounds = 40", "rounds = 201"),
                       ('construct = "agent"', 'construct = "agent"\nturns = 9'),
                       ('construct = "agent"', 'construct = "agent"\nwall_s = 20000'),
                       ('construct = "agent"', 'construct = "agent"\nwall_s = 60'),
                       ('construct = "agent"', f'construct = "agent"\npolicy = "{root.mod}:Sampler"')):
        p.write_text(text.replace(bad, match))
        with pytest.raises(batch.BatchError, match="agent-mode arm|agent session"):
            batch.load_plan(p, root)
    p.write_text(text)
    # a harness-executed arm still names its policy
    p.write_text(text + '[[arm]]\nname = "H"\nfamily = "qwen"\nrounds = 1\nconstruct = "sampler"\n')
    with pytest.raises(batch.BatchError, match="has no policy"):
        batch.load_plan(p, root)


def test_an_agent_batch_runs_scores_rederives_and_reverifies(root):
    agent = ScriptedAgent([{"returned": {TASK_PATH.format(t="t1"): GOOD}, "calls": 3},
                           {"returned": {TASK_PATH.format(t="t1"): "nope\n"}, "calls": 2,
                            "transcript": b'{"type":"text","part":{"text":"sk-ant-oat01-'
                                          + b"Q" * 40 + b'"}}\n'}])
    p = agent_plan(root, arms=[("Q", 8, "verify")], repeats=2)
    b = make_agent(root, p, agent)
    assert b.open() == 2 and len(agent.preflights) == 1
    assert b.run() == 0
    assert states(root) == {"Q/t1/1/1": ("scored", "verified"), "Q/t1/2/1": ("scored", "failed")}
    plan = batch.load_plan(p, root)
    # each session: the attempt's seeds, its turns (the arm's rounds), the task by src
    assert [s.seeds for s in agent.specs] == [tuple(plan.seeds("Q/t1/1/1")),
                                              tuple(plan.seeds("Q/t1/2/1"))]
    assert [s.turns for s in agent.specs] == [8, 8] and agent.specs[0].texts is None
    assert agent.specs[0].task == TASK_PATH.format(t="t1") and agent.specs[0].module == "Q98"
    brief = agent.specs[0].brief
    for want in ("Make the file verify.", "the statement of t1", TASK_PATH.format(t="t1"),
                 "scripts/vcheck --gate", "verified once more"):
        assert want in brief, want
    runs = agent_runs(root)
    m1, d1 = runs["t1/1"]
    assert m1.mode == "agent" and m1.backend == "qwen" and m1.ended_by == "stop"
    assert m1.usage["calls"] == 3 and m1.usage["gpu_s"] == 6.0 and m1.usage["sessions"] == 1
    assert m1.apparatus["seeds"] == plan.seeds("Q/t1/1/1") and m1.apparatus["arm_construct"] == "agent"
    for f in ("inputs.tar.gz", "inputs.sha256", "patch.diff", "verify.json", "seg-1/TASK.md",
              "seg-1/gate-counts.json"):
        assert (d1 / f).is_file(), f
    assert (d1 / "returned" / TASK_PATH.format(t="t1")).read_text() == GOOD
    led = budget.Ledger(budget.ledger_path(root, "Q98"))
    assert [r.get("calls") for r in led.read() if r.get("state") == "scored"] == [3, 2]
    # the second run's transcript held a credential-shaped string: withheld, recorded
    m2, d2 = runs["t1/2"]
    assert not (d2 / "seg-1" / "transcript.jsonl.gz").exists()
    assert "secret-scan:withheld" in m2.findings and m2.secret_scan["withheld"]
    rep = report.build(root, "Q98")
    assert rep.reproduced, report.format_report(rep)
    assert all("an agent run" in c.detail for c in rep.checks)
    git(root, "add", "-A")
    git(root, "commit", "-qm", "the batch")
    got = report.reverify_all(root, "Q98", runner=Gate())
    assert [r.ok for r in got] == [True, True]
    assert sorted(r.derived[0] for r in got) == ["failed", "verified"]


def test_live_run_exits_map_onto_the_ledger_and_resume(root):
    agent = ScriptedAgent([
        {"code": 1, "calls": 0, "ended_by": "start-failed"},           # before output
        {"code": 1, "calls": 2, "ended_by": "killed(memory)"},          # after output
        {"code": 124, "calls": 1},                                      # its wall clock
        {"raise": backends.Deferred("memory short"), "calls": 0}])      # deferred
    p = agent_plan(root, arms=[("Q", 4, "verify")], tasks=("t1", "t2"), repeats=2)
    b = make_agent(root, p, agent)
    b.open()
    assert b.run() == batch.EXIT_REFUSED                                 # stopped: deferred
    st = states(root)
    assert st["Q/t1/1/1"] == ("infra-failed", None)
    assert st["Q/t1/2/1"] == ("scored", "truncated:container")
    assert st["Q/t2/1/1"] == ("scored", "failed")         # judged on the copy as last returned
    assert st["Q/t2/2/1"][0] == "deferred"
    runs = agent_runs(root)
    assert runs["t2/1"][0].ended_by == "wall-clock"
    # resume re-issues the infra-failed id under its seeds and runs the deferred one
    again = ScriptedAgent([{"returned": {TASK_PATH.format(t="t1"): GOOD}},
                           {"returned": {TASK_PATH.format(t="t2"): GOOD}}])
    assert batch.resume(root, "Q98", runners=lambda task, lang: Gate(), agent=again,
                        app=apparatus.load(root / "app.toml"), log=lambda m: None) == 0
    plan = batch.load_plan(p, root)
    assert [s.seeds for s in again.specs] == [tuple(plan.seeds("Q/t1/1/1")),
                                              tuple(plan.seeds("Q/t2/2/1"))]
    st = states(root)
    assert st["Q/t1/1/1"] == ("scored", "verified") and st["Q/t2/2/1"] == ("scored", "verified")
    assert [h["event"] for _, h in budget.read_heads(root)] == ["open", "close"]


def test_a_refused_sandbox_stops_the_batch_and_open_preflights_it(root):
    p = agent_plan(root, arms=[("Q", 4, "verify")], tasks=("t1", "t2"))
    b = make_agent(root, p, ScriptedAgent(problems=["attestation: t1 is not attested"]))
    with pytest.raises(batch.BatchError, match="attested"):
        b.open()
    assert not budget.ledger_path(root, "Q98").exists()
    agent = ScriptedAgent([{"code": 1, "calls": 0, "ended_by": "selftest-failed",
                            "selftest_ok": False, "detail": "the self-test failed"}])
    b = make_agent(root, p, agent)
    b.open()
    assert b.run() == batch.EXIT_REFUSED and len(agent.specs) == 1
    st = states(root)
    assert st["Q/t1/1/1"][0] == "infra-failed" and st["Q/t2/1/1"][0] == "deferred"


def test_an_interrupted_agent_attempt_is_truncated_after_output_and_resumed(root):
    agent = ScriptedAgent([{"raise": batch.Interrupted(), "calls": 2}])
    p = agent_plan(root, arms=[("Q", 4, "verify")], tasks=("t1", "t2"))
    b = make_agent(root, p, agent)
    b.open()
    assert b.run() == batch.EXIT_FAIL
    assert states(root)["Q/t1/1/1"] == ("scored", batch.INTERRUPTED)
    # the same before any output: infra-failed, re-issued by resume
    agent2 = ScriptedAgent([{"raise": batch.Interrupted(), "calls": 0}])
    assert batch.resume(root, "Q98", runners=lambda task, lang: Gate(), agent=agent2,
                        app=apparatus.load(root / "app.toml"), log=lambda m: None) == batch.EXIT_FAIL
    assert states(root)["Q/t2/1/1"] == ("infra-failed", None)
    agent3 = ScriptedAgent([{"returned": {TASK_PATH.format(t="t2"): GOOD}}])
    assert batch.resume(root, "Q98", runners=lambda task, lang: Gate(), agent=agent3,
                        app=apparatus.load(root / "app.toml"), log=lambda m: None) == 0
    assert states(root)["Q/t2/1/1"] == ("scored", "verified")
    assert report.build(root, "Q98").reproduced


def test_a_killed_runner_is_settled_from_the_sessions_gate_counts(root):
    p = agent_plan(root, arms=[("Q", 4, "verify")], tasks=("t1", "t2"))
    b = make_agent(root, p, ScriptedAgent())
    b.open()
    led = budget.Ledger(budget.ledger_path(root, "Q98"))
    for aid, calls in (("Q/t1/1/1", 3), ("Q/t2/1/1", 0)):    # as a SIGKILL leaves them
        rid = runlog.new_run_id(aid)
        rd = led.path.parent / rid
        (rd / "seg-1").mkdir(parents=True)
        (rd / "seg-1" / "gate-counts.json").write_text(json.dumps({"calls": calls, "gpu_s": 1.5}))
        (rd / "seg-1" / "gate.log").write_text('{"event": "start"}\n')
        (rd / "seg-1" / ".seeds.json").write_text("[1, 2, 3, 4]")
        led.move(aid, "running", run_id=rid)
    again = ScriptedAgent([{"returned": {TASK_PATH.format(t="t2"): GOOD}}])
    assert batch.resume(root, "Q98", runners=lambda task, lang: Gate(), agent=again,
                        app=apparatus.load(root / "app.toml"), log=lambda m: None) == 0
    st = states(root)
    assert st["Q/t1/1/1"] == ("scored", batch.INTERRUPTED)            # output: never re-issued
    assert st["Q/t2/1/1"] == ("scored", "verified") and len(again.specs) == 1
    killed = [m for m, d in agent_runs(root).values() if m.outcome == batch.INTERRUPTED][0]
    assert killed.mode == "agent" and "runner-killed" in killed.findings
    assert killed.apparatus["lab_task"] == ""                 # not a lab plan: no lever check
    assert killed.usage["calls"] == 3 and killed.usage["gpu_s"] == 1.5
    d = [d for m, d in agent_runs(root).values() if m.outcome == batch.INTERRUPTED][0]
    assert (d / "seg-1" / "gate.log.gz").is_file() and not (d / "seg-1" / "gate.log").exists()
    assert not (d / "seg-1" / ".seeds.json").exists()          # the hand-over files go
    rows = [r for r in budget.Ledger(budget.ledger_path(root, "Q98")).read()
            if r.get("id") == "Q/t1/1/1" and r.get("state") == "scored"]
    assert rows[0]["calls"] == 3 and rows[0]["gpu_s"] == 1.5


def test_a_gated_agent_arm_refuses_a_stop_until_the_gate_passes(root):
    extra = put_crate(root)
    lib = CRATE.format(t="c1") + "/src/lib.rs"
    agent = ScriptedAgent([{"returned": {lib: STUB_RS.replace("stub", "still a stub")},
                            "calls": 3},
                           {"returned": {lib: GOOD_RS}, "calls": 2}])
    p = agent_plan(root, arms=[("G", 10, "gate")], tasks=("c1",), crate=True, extra=extra)
    b = make_agent(root, p, agent, runner=CrateGate)
    b.open()
    assert b.run() == 0
    assert states(root) == {"G/c1/1/1": ("scored", "verified")}
    s1, s2 = agent.specs
    plan = batch.load_plan(p, root)
    seeds = plan.seeds("G/c1/1/1")
    # the second session continues the attempt: its work copy inline, the rest of the
    # turns and seeds, the gate's refusal in its brief
    assert (s1.turns, s2.turns) == (10, 7) and s2.seeds == tuple(seeds[3:10])
    assert s1.texts is None and s2.texts == {lib: STUB_RS.replace("stub", "still a stub")}
    assert "your stop is refused" in s1.brief and "Your last stop was refused" not in s1.brief
    assert "Your last stop was refused" in s2.brief and "not a complete pass" in s2.brief
    assert "The plain gate (`vcheck --gate`) on your files: " in s2.brief
    assert "It is not the judgement" in s1.brief and "each stop by the acceptance gate" in s1.brief
    [(m, d)] = agent_runs(root).values()
    assert m.ended_by == "gate-pass" and m.usage["calls"] == 5 and m.usage["sessions"] == 2
    assert m.apparatus["acceptance"] == "gate" and m.apparatus["crate"] == CRATE.format(t="c1")
    acc = [json.loads(x) for x in (d / "acceptance.jsonl").read_text().splitlines()]
    assert [(a["segment"], a["passed"]) for a in acc] == [(1, False), (2, True)]
    assert m.verify["acceptance"]["passed"] is True and m.verify["verdict"] == "verified"
    assert sorted(x.name for x in d.iterdir() if x.name.startswith("seg-")) == ["seg-1", "seg-2"]
    # only the companions' own text is staged: the inputs are the crate as shipped
    assert sorted(runlog.read_inputs(d)) == sorted(
        f"{CRATE.format(t='c1')}/{x}" for x in ("Cargo.toml", "frozen.rs", "src/lib.rs"))
    assert report.build(root, "Q98").reproduced
    git(root, "add", "-A")
    git(root, "commit", "-qm", "the batch")
    [r] = report.reverify_all(root, "Q98", runner=CrateGate())
    assert r.ok and r.derived[0] == "verified"


def test_a_gated_agent_arm_ends_at_its_cap_with_the_gates_verdict(root):
    extra = put_crate(root)
    lib = CRATE.format(t="c1") + "/src/lib.rs"
    agent = ScriptedAgent([{"returned": {lib: "// nothing yet\n"}, "calls": 6}])
    p = agent_plan(root, arms=[("G", 6, "gate"), ("P", 6, "verify")], tasks=("c1",), crate=True,
                   extra=extra)
    b = make_agent(root, p, agent, runner=CrateGate)
    b.open()
    agent.steps.append({"returned": {lib: GOOD_RS}, "calls": 6, "capped": 1})
    assert b.run() == 0
    st = states(root)
    assert st == {"G/c1/1/1": ("scored", "failed"), "P/c1/1/1": ("scored", "verified")}
    runs = {runlog.load_meta(d).arm: runlog.load_meta(d) for d in runlog.run_dirs(root, "Q98")}
    assert runs["G"].ended_by == "call-cap" and runs["G"].usage["sessions"] == 1
    assert runs["G"].verify["acceptance"]["passed"] is False
    assert runs["P"].ended_by == "call-cap" and "acceptance" not in runs["P"].verify
    assert "verified once more" in agent.specs[1].brief


def test_a_session_without_a_model_request_is_infra_failed(root):
    extra = put_crate(root)
    agent = ScriptedAgent([{"returned": {}, "calls": 0}])
    p = agent_plan(root, arms=[("G", 6, "gate")], tasks=("c1",), crate=True, extra=extra)
    b = make_agent(root, p, agent, runner=CrateGate)
    b.open()
    b.run()
    assert len(agent.specs) == 1
    [(m, d)] = agent_runs(root).values()
    assert m.outcome == "infra-failed"           # no model output at all: re-issuable


def test_the_live_agent_route_refuses_in_the_ci_environment(root, monkeypatch):
    monkeypatch.setenv("FVH_NO_MODEL", "1")
    with pytest.raises(backends.ModelDisabled):
        AG.LiveAgent(root, apparatus.load(root / "app.toml"))
    monkeypatch.delenv("FVH_NO_MODEL")
    monkeypatch.setenv("DVL_NO_DOCKER", "1")
    with pytest.raises(backends.ModelDisabled):
        AG.LiveAgent(root, apparatus.load(root / "app.toml"))
    p = agent_plan(root, arms=[("Q", 4, "verify")])
    b = batch.Batch(root, "Q98", batch.load_plan(p, root), log=lambda m: None,
                    app=apparatus.load(root / "app.toml"))
    with pytest.raises(batch.BatchError, match="DVL_NO_DOCKER"):
        b.open()
    assert not budget.ledger_path(root, "Q98").exists()


def test_a_gated_continuation_without_a_request_ends_the_run(root):
    extra = put_crate(root)
    lib = CRATE.format(t="c1") + "/src/lib.rs"
    agent = ScriptedAgent([{"returned": {lib: "// try 1\n"}, "calls": 2},
                           {"returned": {}, "calls": 0}])
    p = agent_plan(root, arms=[("G", 9, "gate")], tasks=("c1",), crate=True, extra=extra)
    b = make_agent(root, p, agent, runner=CrateGate)
    b.open()
    assert b.run() == 0
    [(m, d)] = agent_runs(root).values()
    assert (m.outcome, m.ended_by, m.usage["sessions"]) == ("failed", "stop", 2)
    acc = (d / "acceptance.jsonl").read_text().splitlines()
    assert len(acc) == 2 and not any(json.loads(x)["passed"] for x in acc)


def test_a_settled_lab_run_keeps_the_plans_lever_check(root):
    p = agent_plan(root, arms=[("Q", 4, "verify")], lab="lab9")
    prereg_for(root, f"plan-sha256: {batch.load_plan(p, root).sha256}\n")
    b = make_agent(root, p, ScriptedAgent())
    b.open()
    led = budget.Ledger(budget.ledger_path(root, "Q98"))
    rid = runlog.new_run_id("Q/t1/1/1")
    (led.path.parent / rid / "seg-1").mkdir(parents=True)
    (led.path.parent / rid / "seg-1" / "gate-counts.json").write_text('{"calls": 1}')
    led.move("Q/t1/1/1", "running", run_id=rid)
    assert batch.resume(root, "Q98", runners=lambda task, lang: Gate(), agent=ScriptedAgent(),
                        app=apparatus.load(root / "app.toml"), log=lambda m: None) == 0
    [(m, d)] = agent_runs(root).values()
    assert m.apparatus["lab_task"] == TASK_PATH.format(t="t1")
    assert not any("lever check" in x for x in report.build(root, "Q98").disclosure)


# --- DV5d review fixes: the live flag, a killed session's counts, the refusal's brief --

def test_a_live_agent_batch_holds_the_calendar_lock_and_unloads(root, monkeypatch):
    """`fvh run` builds the live agent route in open()'s preflight: the batch stays live
    (the calendar lock for the whole batch, its fd in every session, the server check,
    the state reap and the unload)."""
    from fvh.backends import gate as G
    seen = {"lock": 0, "unlock": 0, "server": 0, "reap": 0, "unload": 0}
    agent = ScriptedAgent([{"returned": {TASK_PATH.format(t="t1"): GOOD}, "calls": 2}])
    monkeypatch.setattr(AG, "LiveAgent", lambda *a, **k: agent)

    class Lock:
        def __init__(self):
            self.fh = open(os.devnull)

        def __enter__(self):
            seen["lock"] += 1
            return self

        def __exit__(self, *a):
            seen["unlock"] += 1
            self.fh.close()

    class Unload:
        def __init__(self, *a, **k):
            pass

        def start(self):
            seen["unload"] += 1

        def stop(self):
            pass

    def server(self):
        seen["server"] += 1
        self.server = {"version": "fake"}

    monkeypatch.setattr(G, "GpuCalendar", Lock)
    monkeypatch.setattr(G, "HostGate", Unload)
    monkeypatch.setattr(G, "gate_config", lambda *a, **k: {})
    monkeypatch.setattr(batch.Batch, "server_check", server)
    monkeypatch.setattr(batch, "_reap_state", lambda app: seen.__setitem__("reap", 1))
    p = agent_plan(root, arms=[("Q", 4, "verify")])
    b = batch.Batch(root, "Q98", batch.load_plan(p, root), runners=lambda task, lang: Gate(),
                    log=lambda m: None, app=apparatus.load(root / "app.toml"))
    assert b.live
    b.open()
    assert b.agent is agent and b.live          # the preflight built the route: still live
    assert b.run() == 0
    assert seen == {"lock": 1, "unlock": 1, "server": 1, "reap": 1, "unload": 1}
    assert agent.specs[0].calendar_fd is not None
    [(m, d)] = agent_runs(root).values()
    assert m.apparatus["model_server_found"] == {"version": "fake"}
    # an injected route stays a test route
    assert not make_agent(root, p, ScriptedAgent()).live


@pytest.mark.parametrize("ended_by,outcome", [("killed-memory", "truncated:host-memory"),
                                               ("sandbox-failed", "truncated:container"),
                                               ("session-timeout", "truncated:container")])
def test_a_session_ended_without_its_record_after_a_request_is_scored(root, ended_by, outcome):
    """A session whose Segment carries no calls (no sandbox.json) but whose gate counted
    requests had model output: truncated and scored, never re-issued (Δ208)."""
    agent = ScriptedAgent([{"code": 1, "calls": 3, "seg_calls": 0, "ended_by": ended_by,
                            "detail": "no record"}])
    p = agent_plan(root, arms=[("Q", 8, "verify")])
    b = make_agent(root, p, agent)
    b.open()
    b.run()
    assert states(root) == {"Q/t1/1/1": ("scored", outcome)}
    [(m, d)] = agent_runs(root).values()
    assert m.usage["calls"] == 3
    rec = [r for r in budget.Ledger(budget.ledger_path(root, "Q98")).read()
           if r.get("kind") == "attempt" and r.get("state") == "scored"]
    assert rec and rec[-1]["calls"] == 3
    assert not budget.resume_order(budget.Ledger(budget.ledger_path(root, "Q98")),
                                   max_reissue=3)


def test_an_attempt_with_no_room_for_a_session_is_deferred(root, monkeypatch):
    agent = ScriptedAgent()
    p = agent_plan(root, arms=[("Q", 8, "verify")], tasks=("t1", "t2"))
    b = make_agent(root, p, agent)
    b.open()
    monkeypatch.setattr(b, "_agent_caps", lambda arm: {"turns": 8, "wall_s": 60.0,
                                                       "gpu_s": None})
    assert b.run() == batch.EXIT_REFUSED
    assert agent.specs == []
    st = states(root)
    assert st["Q/t1/1/1"][0] == "deferred" and st["Q/t2/1/1"][0] == "deferred"


def test_a_refused_stops_brief_carries_five_reasons_and_the_plain_verdict(root):
    extra = put_crate(root)
    p = agent_plan(root, arms=[("G", 8, "gate")], tasks=("c1",), crate=True, extra=extra)
    b = make_agent(root, p, ScriptedAgent())
    arm = b.plan.arm("G")
    text = b.agent_brief(arm, "c1", refusal={"verdict": "FAIL", "vcheck": "failed",
                                             "reasons": [f"reason {i}" for i in range(9)]})
    assert [x for x in text.splitlines() if x.startswith("- reason")] == [
        f"- reason {i}" for i in range(5)]
    assert "The plain gate (`vcheck --gate`) on your files: failed" in text


def test_the_live_routes_early_returns_carry_the_gates_counts(root, monkeypatch, tmp_path):
    """LiveAgent.run_segment without the sandbox's record (a timeout, a memory kill, a
    failed sandbox): the Segment carries what the session's gate counted. mksandbox-run
    is a fake here: nothing starts."""
    monkeypatch.delenv("FVH_NO_MODEL", raising=False)
    monkeypatch.delenv("DVL_NO_DOCKER", raising=False)
    la = AG.LiveAgent(root, apparatus.load(root / "app.toml"))
    monkeypatch.setattr(la, "_build", lambda spec, where: (Path(where) / ".m.json", None))
    counts = {"calls": 5, "gpu_s": 40.0, "prompt_tokens": 50, "output_tokens": 9}

    def spec(k):
        return AG.SegmentSpec(attempt_id="Q/t1/1/1", run_id=f"r{k}", module="Q98",
                              task=TASK_PATH.format(t="t1"), brief="b", turns=8, seeds=(1,) * 8,
                              wall_s=300.0, gpu_s=None, seg_dir=tmp_path / f"seg-{k}")

    def mk(result):
        def run(args, timeout, fds=()):
            seg = Path(args[args.index("--records") + 1])
            (seg / "gate-counts.json").write_text(json.dumps(counts))
            if result == "timeout":
                raise subprocess.TimeoutExpired(args, timeout)
            return subprocess.CompletedProcess(args, result, "", "a line\n")
        return run

    for k, (result, ended) in enumerate((("timeout", "session-timeout"), (-9, "killed-memory"),
                                         (137, "killed-memory"), (1, "sandbox-failed"))):
        monkeypatch.setattr(la, "_mk", mk(result))
        seg = la.run_segment(spec(k))
        assert (seg.code, seg.ended_by, seg.calls, seg.gpu_s, seg.output_tokens) == \
            (1, ended, 5, 40.0, 9)


# --- Lab alpha: plan roles, the freeze, the call record's accounting (DVR4 plan 3.8) -----

def _schema2(root, roles):
    lines = ["schema = 2", 'lab = "Q98"']
    for t, role in roles.items():
        lines += ["[[cluster]]", f'id = "{t}"', f'role = "{role}"', f'tasks = ["{t}"]']
    (root / "bench/local/q/lab9/STRATUM.toml").write_text("\n".join(lines) + "\n")


def test_a_plan_over_a_schema2_stratum_keeps_to_its_role(root):
    _schema2(root, {"t1": "pilot", "t2": "confirmatory"})
    git(root, "add", "."); git(root, "commit", "-qm", "stratum")
    arms = [("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")]
    for extra, tasks, msg in (("", ("t1",), "names its role"),
                              ('role = "pilot"', ("t1", "t2"), "outside the pilot clusters"),
                              ('role = "confirmatory"', ("t2",), "only under the committed freeze")):
        p = write_plan(root, arms=arms, tasks=tasks, extra=extra)
        b = make(root, p, lambda *a: batch.RecordingTransport(Fake("qwen", [GOOD]), a[1]))
        with pytest.raises(batch.BatchError, match=msg):
            b.open()
        assert not budget.ledger_path(root, "Q98").exists()
    p = write_plan(root, arms=arms, tasks=("t1",), extra='role = "pilot"')
    assert batch.load_plan(p, root).role == "pilot"
    b = make(root, p, lambda *a: batch.RecordingTransport(Fake("qwen", [GOOD]), a[1]))
    b.open()
    assert b.run() == 0
    note = batch.batch_note(budget.Ledger(budget.ledger_path(root, "Q98")))
    assert note["role"] == "pilot" and "freeze_sha256" not in note


def test_an_unknown_role_or_a_missing_freeze_file_is_a_plan_error(root):
    arms = [("A1", "qwen", 1, f"{root.mod}:Sampler", "sampler")]
    with pytest.raises(batch.BatchError, match="role is one of"):
        batch.load_plan(write_plan(root, arms=arms, extra='role = "final"'), root)
    with pytest.raises(batch.BatchError, match="freeze"):
        batch.load_plan(write_plan(root, arms=arms, extra='freeze = "nope/FREEZE.toml"'), root)


def test_the_call_record_logs_the_message_and_feedback_sizes(tmp_path):
    from fvh import labalpha
    capped, _ = labalpha.cap_feedback(["q" * 10000], 64)
    msg = json.dumps({"task": "t", "feedback": capped})
    t = batch.RecordingTransport(Fake("qwen", [GOOD]), tmp_path)
    t.complete(msg, seed=3)
    t.complete("plain text", seed=4)
    rows = [json.loads(x) for x in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert rows[0]["message_bytes"] == len(msg.encode()) and rows[0]["feedback_truncated"] is True
    assert rows[0]["feedback_bytes"] == len(json.dumps(capped, sort_keys=True, ensure_ascii=False).encode())
    assert "feedback_bytes" not in rows[1] and rows[1]["message_bytes"] == 10
