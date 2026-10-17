"""D36 regression: annotation/baseline failures cannot inflate a mutation score."""
from types import SimpleNamespace
import signal
import subprocess

import pytest

from fvh import budget, tools
from fvh.labfeedback import SpecFeedback, mutation_score


def test_only_baseline_verified_code_mutations_enter_the_score():
    mutants = [SimpleNamespace(id=s) for s in ("annotation", "bad-base", "unknown-base",
                                               "killed", "survived", "unknown")]
    calls = []

    def baseline(m):
        calls.append(("baseline", m.id))
        return {"bad-base": "failed", "unknown-base": "unknown"}.get(m.id, "proved")

    def full(m):
        calls.append(("full", m.id))
        return {"killed": "failed", "survived": "proved", "unknown": "unknown"}[m.id]

    report = mutation_score(mutants, changes_code=lambda m: m.id != "annotation",
                            baseline=baseline, full=full)
    assert report["generated"] == 6
    assert report["eligible"] == 3
    assert report["killed"] == report["survived"] == report["unknown"] == 1
    assert report["rate"] == 1 / 3
    assert ("baseline", "annotation") not in calls
    assert ("full", "bad-base") not in calls
    assert ("full", "unknown-base") not in calls
    assert report["mutants"][0]["excluded"] == "annotation-only"
    assert report["mutants"][2]["excluded"] == "baseline-unknown"


def test_no_eligible_mutation_is_an_undefined_rate():
    report = mutation_score([SimpleNamespace(id="m")], changes_code=lambda m: True,
                            baseline=lambda m: "unknown", full=lambda m: "failed")
    assert report["eligible"] == 0
    assert report["rate"] is None


@pytest.mark.parametrize("cancel", [False, True])
def test_adapter_wall_cap_or_cancellation_terminates_its_process_group(monkeypatch, tmp_path, cancel):
    calls = []

    class Process:
        pid = 424242

        def communicate(self, timeout=None):
            calls.append(("wait", timeout))
            if len(calls) == 1:
                if cancel:
                    raise KeyboardInterrupt
                raise subprocess.TimeoutExpired("adapter", timeout)
            return "", ""

    def popen(argv, **kwargs):
        assert kwargs["start_new_session"]
        assert argv[-2:] == ["--wall-s", "2"]
        return Process()

    monkeypatch.setattr(subprocess, "Popen", popen)
    monkeypatch.setattr("os.killpg", lambda pid, sig: calls.append((pid, sig)))
    feedback = SpecFeedback(tmp_path, "task.dfy", before_probe=lambda: 2)
    with pytest.raises(KeyboardInterrupt if cancel else budget.CapReached):
        feedback(tmp_path, (), SimpleNamespace(to_dict=lambda: {}))
    assert calls == [("wait", 2), (424242, signal.SIGTERM), ("wait", 10)]


@pytest.mark.parametrize("stdout", ["not-json", '{}', '[]'])
def test_adapter_refuses_unusable_reports(monkeypatch, tmp_path, stdout):
    proc = SimpleNamespace(returncode=0, communicate=lambda **kw: (stdout, ""))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: proc)
    with pytest.raises(tools.RunnerUnavailable):
        SpecFeedback(tmp_path, "task.dfy")(
            tmp_path, (), SimpleNamespace(to_dict=lambda: {}))
