"""The frozen core's own tests: fvh.report, the frozen half of `fvh report`, and
the `python -m fvh` command line (DV4-PLAN §3.1, §3.6, §4.2, §9). On throwaway
roots holding an invented module Q98: runs recorded by the executor with
isolated fake runners, a ledger and its anchors. (Named test_core_report.py:
harness/tests/q/ has Q12's test_report.py.) No model, no container."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from fvh import __main__ as cli
from fvh import apparatus, budget, executor, policies, protocol as P, report, runlog, tools
from fvh.tools import runners as R

TASK = "method M() ensures false\n{\n}\n"
GOOD = "method M() ensures true\n{\n}\n"
REGISTRY = """[[module]]
id = "Q98"
status = "authoring"
agentic = ["dafny/Q/Q98/a.dfy"]
budget = { claude_calls = 20, claude_runs = 4, qwen_calls = 100, qwen_runs = 10, gpu_hours = 1 }
"""


class Gate(R.Runner):
    name = "replay"
    isolated = True

    def execute(self, instrument, target, *, timeout_s=None):
        text = Path(target).read_text()
        ok = text == GOOD
        doc = {"verdict": "verified" if ok else "failed", "holes": [],
               "verified_count": 1 if ok else 0, "exit_code": 0 if ok else 1,
               "diagnostics": [] if ok else [{"severity": "error", "line": 1}]}
        return tools.ToolResult(instrument, str(target), doc, doc["exit_code"], None, "replay",
                                "agent", hashlib.sha256(text.encode()).hexdigest())


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@example.invalid", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.run(["git", "-C", str(root), *args], check=True, env=env,
                          capture_output=True, text=True).stdout.strip()


def course(tmp_path):
    root = tmp_path / "course"
    root.mkdir()
    git(root, "init", "-q")
    (root / "MODULES.toml").write_text(REGISTRY)
    return root


def record(root, run_id, arm, proposals, *, outcome=None, repeat=1, findings=()):
    d = root / "research" / "runs" / "Q98" / run_id
    ctx = P.Context(task_id="t1", lang="dafny", statement="s", editable=("w/a.dfy",),
                    readable=(), target="w/a.dfy")
    res = executor.Executor(ctx, {"w/a.dfy": TASK}, runner=Gate(), run_dir=d).run(
        policies.ScriptedPolicy(proposals))
    tree = runlog.write_inputs(d, {"w/a.dfy": TASK.encode()})
    meta = runlog.RunMeta(run_id=run_id, module="Q98", arm=arm, task_id="t1", lang="dafny",
                          attempt=1, repeat=repeat, mode="harness-executed", backend="mock",
                          outcome=outcome or res.outcome, ended_by=res.ended_by,
                          verify=res.verify, inputs_sha256=tree, findings=findings,
                          apparatus={"backend": {"qwen": {"version": "v", "model": "m",
                                                          "pinned_sha256": "a" * 64}}})
    runlog.write_meta(d, meta)
    return d


SOLVE = [[P.Edit("w/a.dfy", "", GOOD), P.Verify()], [P.Stop("done")]]
FAIL = [[P.Edit("w/a.dfy", "", "nope"), P.Verify()], [P.Stop("give-up")]]


def test_a_reproducible_module(tmp_path):
    root = course(tmp_path)
    lg = budget.open_batch(root, "Q98", budget.enumerate_plan(
        [budget.Arm("A1", budget.QWEN, 2)], ["t1"], repeats=2), course_commit="c")
    record(root, "r1", "A1", SOLVE)
    record(root, "r2", "A1", FAIL, repeat=2)
    record(root, "r3", "A1", FAIL[:1], outcome="truncated:rate-limit", repeat=2)
    rd = root / "research" / "runs" / "Q98" / "r4"
    rd.mkdir()
    runlog.write_inputs(rd, {"w/a.dfy": TASK.encode()})
    runlog.write_meta(rd, runlog.RunMeta(run_id="r4", module="Q98", arm="A2", task_id="t1",
                                         lang="dafny", attempt=1, repeat=1, mode="policy",
                                         backend="mock", outcome="infra-failed"))
    budget.close_batch(root, "Q98", course_commit="c")
    rep = report.build(root, "Q98")
    text = report.format_report(rep)
    assert rep.reproduced, text
    assert [c.derived for c in rep.checks] == ["verified", "failed", "truncated:rate-limit",
                                               "infra-failed"]
    assert "A1: 1/3 | 1/2 (truncated 1)" in text
    assert "arm A2: excluded infra-failed 1" in text
    assert "has uncommitted changes" in text                 # the heads file is not committed
    assert "qwen: version v, model m" in text
    assert lg.path.is_file()


def test_tampering_is_found(tmp_path):
    root = course(tmp_path)
    d = record(root, "r1", "A1", SOLVE, outcome="failed")
    rep = report.build(root, "Q98")
    assert not rep.reproduced and "outcome differs" in report.format_report(rep)
    (d / "inputs.sha256").write_text("0" * 64 + "  w/a.dfy\n")
    rep = report.build(root, "Q98")
    assert rep.checks[0].derived == "unreadable"


def test_a_broken_ledger_refuses_the_report(tmp_path):
    root = course(tmp_path)
    budget.open_batch(root, "Q98", budget.enumerate_plan([budget.Arm("A1", budget.QWEN, 2)],
                                                         ["t1"]), course_commit="c")
    budget.ledger_path(root, "Q98").unlink()
    rep = report.build(root, "Q98")
    assert not rep.ledger_ok and "REFUSED" in report.format_report(rep)
    assert cli.main(["--root", str(root), "report", "Q98"]) == 3


def test_over_cap_runs_are_disclosed(tmp_path):
    root = course(tmp_path)
    d = record(root, "r1", "A1", SOLVE)
    (d / "transcript.jsonl.gz").write_bytes(b"\0" * (runlog.CAP_BYTES + 1))
    assert any("over the" in x for x in report.build(root, "Q98").disclosure)


# --- the command line -------------------------------------------------------------------

@pytest.fixture
def app_env(tmp_path, monkeypatch):
    p = tmp_path / "apparatus.toml"
    p.write_text("schema = 1\n[defaults]\ncalls = 4\n")
    monkeypatch.setenv(apparatus.ENV, str(p))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    return p


def plan(tmp_path, lab=False, rounds=2, tasks=("t1", "t2")):
    """A batch plan (fvh.batch's form) over invented task files in the course root."""
    root = tmp_path / "course"
    lines = (["lab = \"lab9\""] if lab else []) + [
        "seed = 5", f"tasks = {json.dumps(list(tasks))}", "repeats = 2"]
    for t in tasks:
        f = root / "bench" / "local" / "q" / "lab9" / t / "tasks" / f"{t}.dfy"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(TASK)
        lines += [f"[task.{t}]", f"path = \"bench/local/q/lab9/{t}/tasks/{t}.dfy\""]
    lines += ["[[arm]]", "name = \"A1\"", f"family = \"{budget.QWEN}\"", f"rounds = {rounds}",
              "policy = \"fvh:smoke\"", "construct = \"model\""]
    p = tmp_path / "plan.toml"
    p.write_text("\n".join(lines) + "\n")
    return p


def test_cli_run_checks_then_refuses_a_live_batch_in_ci(tmp_path, app_env, capsys, monkeypatch):
    root = course(tmp_path)
    assert cli.main(["--root", str(root), "run", "Q98", "--plan", str(plan(tmp_path)),
                     "--dry-run"]) == 0
    assert "plan of 4 attempt(s)" in capsys.readouterr().out
    monkeypatch.setenv("FVH_NO_MODEL", "1")
    assert cli.main(["--root", str(root), "run", "Q98", "--plan", str(plan(tmp_path))]) == 3
    assert "FVH_NO_MODEL" in capsys.readouterr().err
    assert cli.main(["--root", str(root), "run", "Q98", "--plan",
                     str(plan(tmp_path, rounds=50)), "--dry-run"]) == 3
    assert "qwen_calls = 100" in capsys.readouterr().err
    assert cli.main(["--root", str(root), "run", "Q98", "--plan",
                     str(plan(tmp_path, lab=True)), "--dry-run"]) == 3
    assert "no pre-registration" in capsys.readouterr().err
    assert not budget.ledger_path(root, "Q98").exists()


def test_cli_refuses_without_an_apparatus_file(tmp_path, monkeypatch):
    root = course(tmp_path)
    monkeypatch.setenv(apparatus.ENV, str(tmp_path / "missing.toml"))
    assert cli.main(["--root", str(root), "run", "Q98", "--plan", str(plan(tmp_path)),
                     "--dry-run"]) == 3
    assert cli.main(["--root", str(root), "apparatus"]) == 3


def test_cli_apparatus_check_and_ledger_and_resume(tmp_path, monkeypatch, capsys):
    root = course(tmp_path)
    fake = Path(__file__).resolve().parent / "fakes" / "apparatus.toml"
    monkeypatch.setenv(apparatus.ENV, str(fake))
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    assert cli.main(["--root", str(root), "apparatus", "--check"]) == 3
    assert "drift: backend." in capsys.readouterr().err
    assert cli.main(["--root", str(root), "apparatus"]) == 0
    assert json.loads(capsys.readouterr().out)["apparatus_file"] == str(fake)
    assert cli.main(["--root", str(root), "ledger", "Q98"]) == 0
    assert cli.main(["--root", str(root), "resume", "Q98", "--dry-run"]) == 3
    budget.open_batch(root, "Q98", budget.enumerate_plan([budget.Arm("A1", budget.QWEN, 2)],
                                                         ["t1"]), course_commit="c")
    capsys.readouterr()
    assert cli.main(["--root", str(root), "resume", "Q98", "--dry-run"]) == 0
    assert "A1/t1/1/1" in capsys.readouterr().out
    assert cli.main(["--root", str(root), "ledger", "Q98"]) == 0
    assert cli.main(["--root", str(root), "report", "Q98", "--reverify", "r1"]) == 3
    assert cli.main(["--root", str(root), "ledger", "Q97"]) == 3


def test_cli_contract_local_dry_run(tmp_path, capsys):
    root = course(tmp_path)
    (root / "dafny/Q/Q98").mkdir(parents=True)
    (root / "research").mkdir()
    (root / "research/q98_snapshot.dfy").write_text("snap\n")
    (root / "dafny/Q/Q98/a.dfy").write_text(
        "/* CONTRACT\ngoal: g\nallowed-files:\n  - dafny/Q/Q98/a.dfy\nacceptance:\n"
        "  - `scripts/specfreeze --against research/q98_snapshot.dfy dafny/Q/Q98/a.dfy` "
        "reports no change\n*/\n")
    git(root, "add", ".")
    git(root, "commit", "-qm", "s")
    assert cli.main(["--root", str(root), "contract-local", "Q98", "--dry-run"]) == 0
    assert "[specfreeze-against]" in capsys.readouterr().out
    assert cli.main(["--root", str(root), "contract-local", "Q98"]) == 3


def test_cli_usage_errors_exit_2():
    with pytest.raises(SystemExit) as e:
        cli.main(["frobnicate"])
    assert e.value.code == 2
