"""fvh.judging and `fvh report --judge` (QPLAN §25.6, §30 Q49): on a throwaway root with an
invented module Q98, a pinned (invented) sealed archive and run directories written
here; the grader is a stand-in runner, so no container, key or solver runs."""

import json
from pathlib import Path

import pytest

from fvh import __main__ as cli
from fvh import judging, runlog

ARC = "Hidden/labs/Q98/verdicts.tar.age"
FORM_D = "bench/local/q/lab9/d01-x/tasks/d01-x.dfy"
FORM_V = "bench/local/q/lab9/v01-y/tasks/v01-y.rs"
REGISTRY = """[[module]]
id = "Q98"
status = "authoring"
agentic = ["dafny/Q/Q98/a.dfy"]
budget = { claude_calls = 20, claude_runs = 4, qwen_calls = 100, qwen_runs = 10, gpu_hours = 1 }
"""


def course(tmp_path):
    root = tmp_path / "course"
    (root / "sandbox").mkdir(parents=True)
    (root / "MODULES.toml").write_text(REGISTRY)
    (root / "sandbox" / "truth.toml").write_text(
        'schema = 1\n[[lab]]\nid = "Q98"\narchive = "Hidden/labs/Q98/verdicts.tar.age"\n')
    return root


def lab_run(root, run_id, task, *, returned=None, lang="dafny", outcome="verified"):
    d = root / "research" / "runs" / "Q98" / run_id
    tree = runlog.write_inputs(d, {task: b"shipped\n"} if task else {"w/a.dfy": b"x\n"})
    if returned is not None:
        f = d / "returned" / task
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(returned)
    runlog.write_meta(d, runlog.RunMeta(
        run_id=run_id, module="Q98", arm="S1", task_id="t1", lang=lang, attempt=1, repeat=1,
        mode="harness-executed", backend="mock", outcome=outcome, lab="Q98",
        inputs_sha256=tree, apparatus={"lab_task": task} if task else {}))
    return d


class Grader:
    """A stand-in for mksandbox-run's judging run: records each spec, answers rows."""

    def __init__(self, verdicts, code=0, error=None):
        self.verdicts, self.code, self.error, self.calls = verdicts, code, error, []

    def __call__(self, argv):
        spec = Path(argv[argv.index("--judge") + 1])
        cands = json.loads(spec.read_text())["candidates"]
        texts = {c["id"]: Path(c["file"]).read_bytes() for c in cands}
        self.calls.append((argv, cands, texts))
        if self.error:
            return 3, json.dumps({"error": self.error}) + "\n"
        rows = [{"id": c["id"], "card": c["card"], "verdict": self.verdicts[c["id"]],
                 "base": "proved", "spec_implies_ref": "proved"} for c in cands]
        return self.code, "run note\n" + json.dumps({"judged": rows}) + "\n"


def test_every_lab_run_is_judged_by_language(tmp_path):
    root = course(tmp_path)
    lab_run(root, "r1", FORM_D, returned=b"delivered\n")
    lab_run(root, "r2", FORM_D)                                   # no returned copy
    lab_run(root, "r3", FORM_V, returned=b"fn x() {}\n", lang="verus")
    lab_run(root, "r4", "")                                       # not a lab card's run
    g = Grader({"r1": "faithful", "r2": "weak", "r3": "vacuous"})
    got = judging.judge(root, "Q98", "all", archive=ARC, mem_gb=16, runner=g)
    by = {j.run_id: j for j in got}
    assert by["r1"].verdict == "faithful" and by["r1"].card == "d01-x"
    assert by["r2"].verdict == "weak"
    assert by["r3"].verdict == "vacuous"
    assert by["r4"].verdict == "" and "lab_task" in by["r4"].detail
    assert len(g.calls) == 2                                      # one container per language
    for argv, cands, texts in g.calls:
        assert argv[:4] == ["--truth", "Hidden/labs/Q98/verdicts.tar.age", "--truth-check",
                            "judge"]
        assert argv[-2:] == ["--mem-gb", "16"]
        assert {c["card"] for c in cands} <= {"d01-x", "v01-y"}
        if "r1" in texts:
            assert texts["r1"] == b"delivered\n" and texts["r2"] == b"shipped\n"
    assert not any(Path(c["file"]).exists() for _, cands, _ in g.calls for c in cands)


def test_one_run_and_a_failed_judging_run(tmp_path):
    root = course(tmp_path)
    lab_run(root, "r1", FORM_D, returned=b"d\n")
    lab_run(root, "r2", FORM_D, returned=b"e\n")
    got = judging.judge(root, "Q98", "r2", archive=ARC, runner=Grader({"r2": "strong"}))
    assert [(j.run_id, j.verdict) for j in got] == [("r2", "strong")]
    got = judging.judge(root, "Q98", "all", archive=ARC, runner=Grader({}, error="refused: no key"))
    assert all(j.verdict == "" and "refused: no key" in j.detail for j in got)
    with pytest.raises(ValueError):
        judging.judge(root, "Q98", "r9", archive=ARC, runner=Grader({}))
    with pytest.raises(ValueError):
        judging.judge(root, "Q98", "all", archive="Hidden/labs/Q97/verdicts.tar.age",
                      runner=Grader({}))


def test_runs_of_an_excluded_outcome_are_not_judged_or_counted(tmp_path, monkeypatch, capsys):
    root = course(tmp_path)
    lab_run(root, "r1", FORM_D, returned=b"d\n")
    for k, oc in enumerate(("infra-failed", "apparatus-mismatch", "replay-diverged", "deferred")):
        lab_run(root, f"x{k}", FORM_D, outcome=oc)
    g = Grader({"r1": "faithful"})
    got = judging.judge(root, "Q98", "all", archive=ARC, runner=g)
    by = {j.run_id: j for j in got}
    assert by["r1"].verdict == "faithful" and not by["r1"].excluded
    for k in range(4):
        assert by[f"x{k}"].excluded and by[f"x{k}"].verdict == ""
        assert "excluded outcome" in by[f"x{k}"].detail
    assert [c["id"] for _, cands, _ in g.calls for c in cands] == ["r1"]
    monkeypatch.setattr(judging, "_default_runner", lambda r: Grader({"r1": "faithful"}))
    code = cli.main(["--root", str(root), "report", "Q98", "--judge", "all", "--truth", ARC])
    out = capsys.readouterr()
    assert code == 0
    assert "1/1 run(s) judged" in out.out + out.err
    assert "4 run(s) of an excluded outcome not judged" in out.out + out.err


def test_no_pinned_archive_is_refused(tmp_path):
    root = course(tmp_path)
    (root / "sandbox" / "truth.toml").write_text("schema = 1\n")
    with pytest.raises(ValueError):
        judging.judge(root, "Q98", "all", archive=ARC, runner=Grader({}))


def test_the_command_line(tmp_path, monkeypatch, capsys):
    root = course(tmp_path)
    lab_run(root, "r1", FORM_D, returned=b"d\n")
    monkeypatch.setattr(judging, "_default_runner", lambda r: Grader({"r1": "faithful"}))
    code = cli.main(["--root", str(root), "report", "Q98", "--judge", "all", "--truth", ARC])
    out = capsys.readouterr()
    assert code == 0
    assert "r1 d01-x: faithful" in out.out
    assert "1/1 run(s) judged" in out.out + out.err
    code = cli.main(["--root", str(root), "report", "Q98", "--judge", "all", "--reverify",
                     "all", "--truth", ARC])
    assert code == 3
    code = cli.main(["--root", str(root), "report", "Q98", "--judge", "all"])
    assert code == 3
