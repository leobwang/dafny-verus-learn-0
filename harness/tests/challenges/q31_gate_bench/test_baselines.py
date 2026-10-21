"""Q31's acceptance tests for agents/q31_gate_bench/baselines.py (frozen; QPLAN §33.1, Δ406).

They fail while Q31.H14py or H15py is a hole. No model: the one-shot renderer is a
function of its arguments, and the scripted policy replays its two proposals.

Run: scripts/vcheck agents/q31_gate_bench/baselines.py
"""

import pytest

from fvh import policies, protocol as P
from q31_gate_bench import baselines as bl


def ctx(text="method M() {}"):
    return P.Context(task_id="t", lang="dafny", statement="Prove M.", editable=("t.dfy",),
                     readable=(), target="t.dfy", material={"instructions": "Be brief.", "text": text})


def st(step, history=()):
    return P.State("t", step, {"t.dfy": "0" * 64}, None, tuple(history))


def test_scripted():
    e = P.Edit(path="t.dfy", old="", new="method M() {}\n")
    pol = bl.scripted([e])
    assert isinstance(pol, policies.ScriptedPolicy)
    assert pol.propose(st(0), ctx(), P.Budget()) == [e, P.Verify()]
    assert pol.propose(st(1), ctx(), P.Budget()) == [P.Stop(reason="done")]
    with pytest.raises(policies.ScriptExhausted):
        pol.propose(st(2), ctx(), P.Budget())


def test_one_shot_render():
    text = bl.one_shot_render(st(0), ctx(), P.Budget())
    assert text.startswith("Be brief.") and text.endswith(bl.REPLY_RULE)
    assert "Statement:\nProve M." in text and "```\nmethod M() {}\n```" in text
    later = st(3, history=(P.Turn(0, (P.Verify(),), ()),))
    assert bl.one_shot_render(later, ctx(), P.Budget(calls_left=1)) == text
    assert bl.one_shot_render(st(0), ctx("other"), P.Budget()) != text
