"""Q12's acceptance tests for harness/q/fvh_q/policies.py (frozen; QPLAN §22.6).

The arms are written on `fvh.protocol` (DV4-PLAN §3.2), and every test runs
on its real actions. Only in a checkout where `fvh.protocol` cannot be
imported do these tests put a stand-in for the three actions the arms build
(Edit, Verify, Stop: DV4-PLAN §3.2's fields) in its place and skip
`test_core_protocol_has_the_actions` (the run's report names it).

No model and no container run here: `ask` is a scripted function, and the
observations are written-out verifier documents. State, Context and Budget
are plain objects with the fields the arms read (DV4-PLAN §3.2): State.step
and State.last_verify; Context.target, lang, statement and material
(`instructions`, `text`); Budget.exhausted.

What they hold the arms to (design §11.1, QPLAN §22.5):
  - matched compute: one `ask` call per `propose` at most, none once the
    budget is exhausted or the seeds are used up, the pre-registered seeds
    in order;
  - A1 never puts an observation into a prompt; A2 repairs its last
    candidate from its last document; A3 expands the frontier candidate
    with the fewest failing obligations, the earlier one on a tie;
  - every candidate is submitted as an Edit of the target over the text the
    work copy holds, followed by a gate run, and a run ends with Stop;
  - `render` is a pure function of its arguments.

Run: scripts/vcheck harness/q/fvh_q/policies.py
     (or, from harness/: uv run pytest tests/q/test_policies.py)
"""

import dataclasses
import importlib
import sys
import types
from types import SimpleNamespace

import pytest

import fvh

try:
    protocol = importlib.import_module("fvh.protocol")
    STAND_IN = False
except ImportError:
    protocol = types.ModuleType("fvh.protocol")

    @dataclasses.dataclass(frozen=True)
    class Edit:
        path: str
        old: str
        new: str

    @dataclasses.dataclass(frozen=True)
    class Verify:
        mode: str

    @dataclasses.dataclass(frozen=True)
    class Stop:
        reason: str
        note: str = ""

    protocol.Edit, protocol.Verify, protocol.Stop = Edit, Verify, Stop
    sys.modules["fvh.protocol"] = protocol
    fvh.protocol = protocol
    STAND_IN = True

from fvh_q import policies as pol  # noqa: E402  (after the stand-in, when there is one)

TASK = "method M() ensures false\n{\n}\n"


def ctx():
    return SimpleNamespace(task_id="T1", lang="dafny", statement="M is never called",
                           target="work/task.dfy", editable=("work/task.dfy",), readable=(),
                           material={"instructions": "Prove the statement.", "text": TASK})


def state(step, last=None):
    return SimpleNamespace(task_id="T1", step=step, files={}, last_verify=last, history=())


def budget(exhausted=False):
    return SimpleNamespace(calls_left=0 if exhausted else 8, tokens_left=10**6,
                           wall_s_left=600.0, gpu_s_left=600.0, exhausted=exhausted)


def doc(errors=0, holes=0, *, stage="verify", verdict=None):
    v = verdict or ("verified" if errors == 0 and holes == 0 else "failed")
    return {"lang": "dafny", "stage": stage, "verdict": v, "verified_count": 0 if errors else 2,
            "holes": [{"line": 1}] * holes,
            "diagnostics": [{"line": 10 + i, "col": 1, "severity": "error",
                             "message": f"error {i}"} for i in range(errors)]
            + [{"line": 99, "col": 1, "severity": "related", "message": "related"}],
            "findings": [], "exit_code": 0 if v == "verified" else 1}


class Model:
    """A scripted `ask`: the n-th call returns replies[n]; records every call."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, prompt, seed):
        self.calls.append((prompt, seed))
        return self.replies[len(self.calls) - 1]


def kinds(actions):
    return [type(a).__name__ for a in actions]


@pytest.mark.skipif(STAND_IN, reason="fvh.protocol is not importable here, so the other "
                    "tests ran on a stand-in for its actions (QPLAN §22.8, §30 Q53)")
def test_core_protocol_has_the_actions():
    for name in ("Edit", "Verify", "Stop", "State", "Context", "Budget", "ACTION_SCHEMA"):
        assert hasattr(protocol, name), name
    assert protocol.Edit(path="p", old="a", new="b").new == "b"


# --- the given helpers ------------------------------------------------------------------


def test_given_failing_and_verified():
    assert pol.failing(doc(2, 1)) == 3
    assert pol.failing(doc(0, 0)) == 0
    assert pol.failing(doc(stage="resolve", verdict="failed")) == 10**6
    assert pol.failing(None) == 10**6
    assert pol.verified(doc()) and not pol.verified(doc(1)) and not pol.verified(None)


# --- H11: render --------------------------------------------------------------------------


def test_render_independent_holds_the_task_and_nothing_else():
    c = ctx()
    p = pol.render(state(3, doc(4)), c, mode="independent")
    assert p.startswith("Prove the statement.")
    assert c.statement in p and "dafny" in p and TASK.strip() in p
    assert "error 0" not in p and "line 10" not in p


def test_render_independent_ignores_the_run_so_far():
    c = ctx()
    assert pol.render(state(0), c, mode="independent") == \
        pol.render(state(5, doc(3, 2)), c, mode="independent")


def test_render_repair_carries_the_errors_in_order():
    c = ctx()
    focus = pol.Candidate("CANDIDATE TEXT", doc(3, 2))
    p = pol.render(state(1, focus.verify), c, mode="repair", focus=focus)
    assert p.startswith("Prove the statement.") and "CANDIDATE TEXT" in p
    assert p.index("error 0") < p.index("error 1") < p.index("error 2")
    assert "line 10" in p and "related" not in p
    assert TASK.strip() not in p


def test_render_caps_the_errors_at_twenty():
    c = ctx()
    focus = pol.Candidate("X", doc(25))
    p = pol.render(state(1), c, mode="expand", focus=focus)
    assert "error 19" in p and "error 20" not in p


def test_render_is_deterministic():
    c = ctx()
    focus = pol.Candidate("X", doc(2))
    assert pol.render(state(1), c, mode="expand", focus=focus) == \
        pol.render(state(1), c, mode="expand", focus=focus)


@pytest.mark.parametrize("mode, focus", [
    ("sideways", None),
    ("repair", None),
    ("expand", None),
    ("repair", pol.Candidate("X", None)),
])
def test_render_refuses(mode, focus):
    with pytest.raises(ValueError):
        pol.render(state(1), ctx(), mode=mode, focus=focus)


# --- H8: A1 -------------------------------------------------------------------------------


def test_a1_one_call_then_stop():
    m = Model("method M() ensures false\n{\n  assume false;\n}\n")
    a1 = pol.IndependentSampler(m, seed=41)
    first = a1.propose(state(0), ctx(), budget())
    assert kinds(first) == ["Edit", "Verify"]
    assert first[0] == protocol.Edit(path="work/task.dfy", old=TASK, new=m.replies[0])
    assert first[1] == protocol.Verify(mode="gate")
    assert len(m.calls) == 1 and m.calls[0][1] == 41
    assert m.calls[0][0] == pol.render(state(0), ctx(), mode="independent")
    done = a1.propose(state(1, doc()), ctx(), budget())
    assert done == [protocol.Stop(reason="done", note="")]
    assert len(m.calls) == 1


def test_a1_gives_up_on_a_failed_gate():
    a1 = pol.IndependentSampler(Model("X"), seed=1)
    a1.propose(state(0), ctx(), budget())
    out = a1.propose(state(1, doc(2)), ctx(), budget())
    assert kinds(out) == ["Stop"] and out[0].reason == "give-up"


def test_a1_exhausted_budget_makes_no_call():
    m = Model()
    out = pol.IndependentSampler(m, seed=1).propose(state(0), ctx(), budget(True))
    assert kinds(out) == ["Stop"] and out[0].reason == "give-up" and m.calls == []


def test_a1_same_text_is_only_verified():
    out = pol.IndependentSampler(Model(TASK), seed=1).propose(state(0), ctx(), budget())
    assert kinds(out) == ["Verify"]


# --- H9: A2 -------------------------------------------------------------------------------


def test_a2_repairs_the_last_candidate():
    m = Model("C1", "C2", "C3")
    a2 = pol.SequentialRepair(m, seeds=[7, 8, 9])
    c = ctx()
    out = a2.propose(state(0), c, budget())
    assert out[0] == protocol.Edit(path=c.target, old=TASK, new="C1")
    out = a2.propose(state(1, doc(2)), c, budget())
    assert out[0] == protocol.Edit(path=c.target, old="C1", new="C2")
    focus = pol.Candidate("C1", doc(2))
    assert m.calls[1] == (pol.render(state(1, doc(2)), c, mode="repair", focus=focus), 8)
    out = a2.propose(state(2, doc(1)), c, budget())
    assert out[0] == protocol.Edit(path=c.target, old="C2", new="C3")
    assert [s for _, s in m.calls] == [7, 8, 9]
    assert m.calls[0][0] == pol.render(state(0), c, mode="independent")


def test_a2_stops_when_verified():
    m = Model("C1", "C2")
    a2 = pol.SequentialRepair(m, seeds=[1, 2])
    a2.propose(state(0), ctx(), budget())
    out = a2.propose(state(1, doc()), ctx(), budget())
    assert out == [protocol.Stop(reason="done", note="")] and len(m.calls) == 1


def test_a2_stops_when_the_seeds_run_out():
    m = Model("C1", "C2", "C3")
    a2 = pol.SequentialRepair(m, seeds=[1, 2])
    a2.propose(state(0), ctx(), budget())
    a2.propose(state(1, doc(1)), ctx(), budget())
    out = a2.propose(state(2, doc(1)), ctx(), budget())
    assert kinds(out) == ["Stop"] and out[0].reason == "give-up" and len(m.calls) == 2


def test_a2_stops_on_an_exhausted_budget():
    m = Model("C1", "C2")
    a2 = pol.SequentialRepair(m, seeds=[1, 2])
    a2.propose(state(0), ctx(), budget())
    out = a2.propose(state(1, doc(1)), ctx(), budget(True))
    assert kinds(out) == ["Stop"] and len(m.calls) == 1


# --- H10: A3 ------------------------------------------------------------------------------


def test_a3_expands_the_fewest_failing_first():
    m = Model("C1", "C2", "C3", "C4")
    a3 = pol.BestFirst(m, seeds=[1, 2, 3, 4])
    c = ctx()
    out = a3.propose(state(0), c, budget())                    # C1, from the task form
    assert out[0] == protocol.Edit(path=c.target, old=TASK, new="C1")
    out = a3.propose(state(1, doc(3)), c, budget())            # C1 fails 3: expand C1
    assert out[0] == protocol.Edit(path=c.target, old="C1", new="C2")
    assert m.calls[1][0] == pol.render(state(1, doc(3)), c, mode="expand",
                                       focus=pol.Candidate("C1", doc(3)))
    out = a3.propose(state(2, doc(5)), c, budget())            # C2 fails 5: C1 is still
    assert out[0] == protocol.Edit(path=c.target, old="C2", new="C3")  # the best
    assert m.calls[2][0] == pol.render(state(2, doc(5)), c, mode="expand",
                                       focus=pol.Candidate("C1", doc(3)))
    out = a3.propose(state(3, doc(1)), c, budget())            # C3 fails 1: expand C3
    assert out[0] == protocol.Edit(path=c.target, old="C3", new="C4")
    assert m.calls[3][0] == pol.render(state(3, doc(1)), c, mode="expand",
                                       focus=pol.Candidate("C3", doc(1)))
    assert [s for _, s in m.calls] == [1, 2, 3, 4]


def test_a3_returns_to_the_better_state_after_a_worse_child():
    m = Model("C1", "C2", "C3", "C4")
    a3 = pol.BestFirst(m, seeds=[1, 2, 3, 4])
    c = ctx()
    a3.propose(state(0), c, budget())
    a3.propose(state(1, doc(2)), c, budget())                  # C1: 2; expand C1 -> C2
    a3.propose(state(2, doc(1)), c, budget())                  # C2: 1; expand C2 -> C3
    out = a3.propose(state(3, doc(4)), c, budget())            # C3: 4; expand C2 again
    assert out[0] == protocol.Edit(path=c.target, old="C3", new="C4")
    assert m.calls[3][0] == pol.render(state(3, doc(4)), c, mode="expand",
                                       focus=pol.Candidate("C2", doc(1)))


def test_a3_tie_goes_to_the_earlier_candidate():
    m = Model("C1", "C2", "C3", "C4", "C5")
    a3 = pol.BestFirst(m, seeds=[1, 2, 3, 4, 5])
    c = ctx()
    a3.propose(state(0), c, budget())
    a3.propose(state(1, doc(2)), c, budget())                  # C1: 2 -> expand C1 (C2)
    a3.propose(state(2, doc(2)), c, budget())                  # C2: 2 -> C1 again (C3)
    a3.propose(state(3, doc(2)), c, budget())                  # C3: 2 -> C1 again (C4)
    assert m.calls[3][0] == pol.render(state(3, doc(2)), c, mode="expand",
                                       focus=pol.Candidate("C1", doc(2)))


def test_a3_stops_when_verified_or_out_of_seeds():
    m = Model("C1", "C2")
    a3 = pol.BestFirst(m, seeds=[1, 2])
    a3.propose(state(0), ctx(), budget())
    assert a3.propose(state(1, doc()), ctx(), budget()) == [protocol.Stop(reason="done", note="")]
    m = Model("C1", "C2", "C3")
    a3 = pol.BestFirst(m, seeds=[1, 2])
    a3.propose(state(0), ctx(), budget())
    a3.propose(state(1, doc(1)), ctx(), budget())
    out = a3.propose(state(2, doc(1)), ctx(), budget())
    assert kinds(out) == ["Stop"] and out[0].reason == "give-up" and len(m.calls) == 2


def test_a3_exhausted_budget_makes_no_call():
    m = Model("C1")
    out = pol.BestFirst(m, seeds=[1]).propose(state(0), ctx(), budget(True))
    assert kinds(out) == ["Stop"] and m.calls == []


# --- matched compute across the arms ------------------------------------------------------


@pytest.mark.parametrize("make", [
    lambda m: pol.SequentialRepair(m, seeds=range(8)),
    lambda m: pol.BestFirst(m, seeds=range(8)),
])
def test_at_most_b_calls(make):
    m = Model(*[f"C{i}" for i in range(20)])
    arm = make(m)
    out, step = arm.propose(state(0), ctx(), budget()), 0
    while kinds(out) != ["Stop"]:
        step += 1
        out = arm.propose(state(step, doc(1)), ctx(), budget())
        assert step < 20
    assert len(m.calls) == 8
