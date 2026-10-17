"""Q12's acceptance tests for harness/q/fvh_q/retry.py (frozen; QPLAN §22.3).

They fail while H1py or H2py is a hole and pass on a correct file. No solver
runs here: the battery's `vcheck --gate` results are replayed from the
recordings under harness/tests/q/fixtures/q12/rec/ (fvh.tools.ReplayRunner;
results only), and the other cases feed `solve_goal` hand-made results. The
battery's expected outcome is written out below (BATTERY_PIN), never
re-derived from the functions under test; `test_pin_matches_expected` checks
it against expected/Q12.battery wherever that file is present (the tools'
scratch overlay holds harness/ only, so there it skips).

What they hold the client to:
  - every try is `run("vcheck --gate", <candidate>)`, through `fvh.tools.run`
    looked up at the time of the call unless `run` is given;
  - a try passes only on a complete pass of the document, judged from the
    result alone, and a killed result is never a pass;
  - each failed try gets the first reason of the docstring's list;
  - at most `k` tries, in the battery's order, stopping at the first pass;
  - `run_battery` goes through `solve_goal` and reports the pinned count.

Run: scripts/vcheck harness/q/fvh_q/retry.py
     (or, from harness/: uv run pytest tests/q/test_retry.py)
"""

import hashlib
import tomllib
from pathlib import Path

import pytest

from fvh import tools
from fvh.tools import ReplayRunner, ToolResult
from fvh_q import retry as rt

HARNESS = Path(__file__).resolve().parents[2]
ROOT = HARNESS.parent
REC = HARNESS / "tests" / "q" / "fixtures" / "q12" / "rec"
REPLAY = ReplayRunner(REC, root=ROOT)
EXPECTED = ROOT / "expected" / "Q12.battery"

# The battery at k = 3 (the recordings' outcome, written out).
BATTERY_PIN = {
    "solved": 8,
    "total": 12,
    "tries": {"D1": 1, "D2": 2, "D3": 3, "D4": 3, "D5": 1, "D6": 2,
              "V1": 1, "V2": 2, "V3": 3, "V4": 3, "V5": 3, "V6": 3},
    "first_failure": {"D4": "verdict:failed", "V4": "holes:1", "V5": "verdict:failed",
                      "V6": "stage:resolve"},
}
SHA0 = "0" * 64


def replay_run(instrument, target):
    return tools.run(instrument, target, root=ROOT, runner=REPLAY)


def result(doc=None, *, exit_code=0, killed=None, target="t.dfy"):
    if killed is not None:
        doc = {"exit_code": exit_code, "lines": ["killed"]}
    return ToolResult("vcheck --gate", target, doc, exit_code, killed, "replay", "course", SHA0)


def passing(target="t.dfy"):
    return result({"lang": "dafny", "stage": "verify", "verdict": "verified", "holes": [],
                   "findings": [], "verified_count": 3, "exit_code": 0}, target=target)


def failing_doc(**over):
    doc = {"lang": "dafny", "stage": "verify", "verdict": "verified", "holes": [],
           "findings": [], "verified_count": 3, "exit_code": 0}
    doc.update(over)
    return doc


class Scripted:
    """A `run` that answers each candidate from a table and records the calls."""

    def __init__(self, table):
        self.table = table
        self.calls = []

    def __call__(self, instrument, target):
        self.calls.append((instrument, target))
        return self.table[target]


# --- the battery, replayed ------------------------------------------------------------


def test_battery_file_loads():
    goals = rt.load_battery(root=ROOT)
    assert [g.id for g in goals] == list(BATTERY_PIN["tries"])
    assert all(len(g.candidates) == 3 for g in goals)
    assert {g.lang for g in goals} == {"dafny", "verus"}


def test_battery_solve_count():
    rep = rt.run_battery(rt.load_battery(root=ROOT), k=3, run=replay_run)
    assert rep.solved == BATTERY_PIN["solved"]
    assert rep.total == BATTERY_PIN["total"]


def test_battery_tries_and_first_failures():
    rep = rt.run_battery(rt.load_battery(root=ROOT), k=3, run=replay_run)
    assert dict(rep.tries) == BATTERY_PIN["tries"]
    assert dict(rep.first_failure) == BATTERY_PIN["first_failure"]


def test_battery_attempts_name_the_passing_candidate():
    goals = {g.id: g for g in rt.load_battery(root=ROOT)}
    att = rt.solve_goal(goals["D3"], k=3, run=replay_run)
    assert att.solved and att.tries == 3 and att.passed == goals["D3"].candidates[2]
    assert len(att.reasons) == 2
    att = rt.solve_goal(goals["V6"], k=3, run=replay_run)
    assert not att.solved and att.passed is None and att.tries == 3 and len(att.reasons) == 3


def test_battery_with_k_one():
    rep = rt.run_battery(rt.load_battery(root=ROOT), k=1, run=replay_run)
    assert rep.solved == 3          # D1, D5 and V1 pass on their first candidate
    assert set(rep.tries.values()) == {1}


def test_pin_matches_expected():
    if not EXPECTED.is_file():
        pytest.skip("expected/Q12.battery is not in this tree (the tools' overlay)")
    with open(EXPECTED, "rb") as f:
        pin = tomllib.load(f)
    assert pin["k"] == 3
    assert pin["solved"] == BATTERY_PIN["solved"] and pin["total"] == BATTERY_PIN["total"]
    h = hashlib.sha256()
    for p in sorted(REC.glob("*/*/*.json")):
        h.update(p.relative_to(REC).as_posix().encode() + b"\0" + p.read_bytes())
    assert pin["recordings_sha256"] == h.hexdigest()


# --- solve_goal on hand-made results ----------------------------------------------------


def goal(n=3):
    return rt.Goal("G", "dafny", tuple(f"c{i}.dfy" for i in range(1, n + 1)))


@pytest.mark.parametrize("res, why", [
    (result(killed="memory", exit_code=None), "killed:memory"),
    (result(killed="wall-clock", exit_code=None), "killed:wall-clock"),
    (result({"exit_code": 3, "lines": ["vcheck: refused"]}, exit_code=3), "exit:3"),
    (result({"exit_code": 2, "lines": ["usage"]}, exit_code=2), "exit:2"),
    (result({"exit_code": 1, "lines": ["no json"]}, exit_code=1), "no-document"),
    (result({"stage": "verify", "verdict": "verified", "holes": []}), "no-document"),
    (result(failing_doc(stage="parse", verdict="failed"), exit_code=1), "stage:parse"),
    (result(failing_doc(stage="resolve", verdict="failed", holes=["h"]), exit_code=1),
     "stage:resolve"),
    (result(failing_doc(verdict="failed", holes=["h1", "h2"]), exit_code=1), "holes:2"),
    (result(failing_doc(holes=None)), "holes:0"),
    (result(failing_doc(verdict="failed"), exit_code=1), "verdict:failed"),
    (result(failing_doc(verdict="inconclusive"), exit_code=1), "verdict:inconclusive"),
    (result(failing_doc(verified_count=0)), "count"),
    (result(failing_doc(verified_count=None)), "count"),
    (result(failing_doc(verified_count=True)), "count"),
    (result(failing_doc(verified_count=2.0)), "count"),
    (result(failing_doc(), exit_code=1), "exit:1"),
])
def test_failure_reasons(res, why):
    att = rt.solve_goal(rt.Goal("G", "dafny", ("c1.dfy",)), k=3, run=lambda i, t: res)
    assert att == rt.Attempt("G", False, 1, None, (why,))


def test_killed_is_never_a_pass_even_with_a_passing_text():
    res = ToolResult("vcheck --gate", "t.dfy", {"exit_code": 137, "lines": ["verified"]},
                     137, "memory", "replay", "course", SHA0)
    att = rt.solve_goal(rt.Goal("G", "dafny", ("c1.dfy",)), run=lambda i, t: res)
    assert not att.solved and att.reasons == ("killed:memory",)


def test_first_pass_stops():
    run = Scripted({"c1.dfy": result(failing_doc(verdict="failed"), exit_code=1),
                    "c2.dfy": passing("c2.dfy"), "c3.dfy": passing("c3.dfy")})
    att = rt.solve_goal(goal(), k=3, run=run)
    assert att == rt.Attempt("G", True, 2, "c2.dfy", ("verdict:failed",))
    assert run.calls == [("vcheck --gate", "c1.dfy"), ("vcheck --gate", "c2.dfy")]


def test_pass_on_first_try_has_no_reasons():
    run = Scripted({"c1.dfy": passing("c1.dfy")})
    assert rt.solve_goal(goal(1), run=run) == rt.Attempt("G", True, 1, "c1.dfy", ())


def test_at_most_k_tries():
    bad = result(failing_doc(verdict="failed"), exit_code=1)
    run = Scripted({f"c{i}.dfy": bad for i in range(1, 6)} | {"c5.dfy": passing("c5.dfy")})
    att = rt.solve_goal(goal(5), k=2, run=run)
    assert att == rt.Attempt("G", False, 2, None, ("verdict:failed", "verdict:failed"))
    assert len(run.calls) == 2
    att = rt.solve_goal(goal(5), k=5, run=Scripted(run.table))
    assert att.solved and att.tries == 5 and att.passed == "c5.dfy"


def test_default_k_is_three():
    bad = result(failing_doc(verdict="failed"), exit_code=1)
    run = Scripted({f"c{i}.dfy": bad for i in range(1, 5)} | {"c4.dfy": passing("c4.dfy")})
    att = rt.solve_goal(goal(4), run=run)
    assert not att.solved and att.tries == 3


def test_k_below_one_raises():
    with pytest.raises(ValueError):
        rt.solve_goal(goal(), k=0, run=Scripted({}))


def test_no_candidates():
    assert rt.solve_goal(rt.Goal("G", "verus", ()), run=Scripted({})) == \
        rt.Attempt("G", False, 0, None, ())


def test_run_is_looked_up_at_call_time(monkeypatch):
    calls = []

    def fake(instrument, target, **kw):
        calls.append((instrument, target))
        return passing(target)

    monkeypatch.setattr(tools, "run", fake)
    att = rt.solve_goal(goal(), k=3)
    assert att.solved and calls == [("vcheck --gate", "c1.dfy")]


def test_run_argument_replaces_tools_run(monkeypatch):
    def boom(*a, **kw):
        raise AssertionError("fvh.tools.run was called although run was given")

    monkeypatch.setattr(tools, "run", boom)
    run = Scripted({"c1.dfy": passing("c1.dfy")})
    assert rt.solve_goal(goal(), run=run).solved


# --- run_battery ----------------------------------------------------------------------------


def test_run_battery_goes_through_solve_goal(monkeypatch):
    seen = []

    def stub(g, *, k=3, run=None):
        seen.append((g.id, k, run))
        if g.id == "A":
            return rt.Attempt("A", True, 2, "a2", ("verdict:failed",))
        return rt.Attempt(g.id, False, 3, None, ("stage:parse", "holes:1", "count"))

    marker = object()
    monkeypatch.setattr(rt, "solve_goal", stub)
    goals = [rt.Goal("A", "dafny", ("a1", "a2")), rt.Goal("B", "verus", ("b1", "b2", "b3"))]
    rep = rt.run_battery(goals, k=4, run=marker)
    assert seen == [("A", 4, marker), ("B", 4, marker)]
    assert rep == rt.BatteryReport(1, 2, {"A": 2, "B": 3}, {"B": "stage:parse"})


def test_run_battery_counts_from_real_attempts():
    table = {"a1": result(failing_doc(verdict="failed"), exit_code=1, target="a1"),
             "a2": passing("a2"),
             "b1": result(failing_doc(stage="resolve", verdict="failed"), exit_code=1,
                          target="b1")}
    goals = [rt.Goal("A", "dafny", ("a1", "a2")), rt.Goal("B", "dafny", ("b1",)),
             rt.Goal("C", "verus", ())]
    rep = rt.run_battery(goals, run=Scripted(table))
    assert rep.solved == 1 and rep.total == 3
    assert dict(rep.tries) == {"A": 2, "B": 1, "C": 0}
    assert dict(rep.first_failure) == {"B": "stage:resolve"}


def test_run_battery_rejects_a_repeated_id():
    goals = [rt.Goal("A", "dafny", ()), rt.Goal("A", "verus", ())]
    with pytest.raises(ValueError):
        rt.run_battery(goals, run=Scripted({}))


def test_run_battery_of_nothing():
    assert rt.run_battery([], run=Scripted({})) == rt.BatteryReport(0, 0, {}, {})
