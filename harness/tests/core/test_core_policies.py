"""The frozen core's own tests: fvh.policies (DV4-PLAN §3.3, §9): the Policy
protocol, Mock, Scripted and Replay determinism, and replay divergence. No model,
no container. (Named test_core_policies.py: harness/tests/q/ has Q12's
test_policies.py, and test basenames are unique in this project.)"""

import json

import pytest

from fvh import policies, protocol as P


def ctx():
    return P.Context(task_id="T1", lang="dafny", statement="s", editable=("a.dfy",),
                     readable=(), target="a.dfy")


def state(step, files=None):
    return P.State("T1", step, files or {"a.dfy": P.text_sha256("x")})


def test_the_protocol_is_runtime_checkable():
    assert isinstance(policies.MockPolicy(lambda s, c, b: []), policies.Policy)
    assert isinstance(policies.ScriptedPolicy([]), policies.Policy)
    assert not isinstance(object(), policies.Policy)


def test_mock_is_a_function_of_its_arguments():
    seen = []

    def fn(s, c, b):
        seen.append((s.step, c.task_id, b.exhausted))
        return (P.Verify(),) if s.step == 0 else [P.Stop("done")]
    m = policies.MockPolicy(fn)
    assert m.propose(state(0), ctx(), P.Budget()) == [P.Verify()]
    assert m.propose(state(0), ctx(), P.Budget()) == [P.Verify()]
    assert m.propose(state(1), ctx(), P.Budget(calls_left=0)) == [P.Stop("done")]
    assert seen == [(0, "T1", False), (0, "T1", False), (1, "T1", True)]
    with pytest.raises(TypeError):
        policies.MockPolicy(lambda s, c, b: ["not an action"]).propose(state(0), ctx(), P.Budget())
    with pytest.raises(TypeError):
        policies.MockPolicy(3)


def test_scripted_returns_the_nth_proposal_at_step_n():
    script = [[P.Edit("a.dfy", "", "y"), P.Verify()], [P.Stop("give-up")]]
    s = policies.ScriptedPolicy(script)
    assert s.propose(state(1), ctx(), P.Budget()) == [P.Stop("give-up")]
    assert s.propose(state(0), ctx(), P.Budget()) == script[0]
    with pytest.raises(policies.ScriptExhausted):
        s.propose(state(2), ctx(), P.Budget())


def write_actions(tmp_path, recs):
    (tmp_path / "actions.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs))
    return tmp_path


def test_replay_replays_and_checks_the_digests(tmp_path):
    f0 = {"a.dfy": P.text_sha256("x")}
    f1 = {"a.dfy": P.text_sha256("y")}
    d = write_actions(tmp_path, [
        {"step": 0, "files": f0, "actions": [{"type": "edit", "path": "a.dfy", "old": "",
                                              "new": "y"}, {"type": "verify", "mode": "gate"}]},
        {"step": 1, "files": f1, "actions": [{"type": "stop", "reason": "done"}]}])
    r = policies.ReplayPolicy(d)
    assert r.propose(state(0, f0), ctx(), P.Budget()) == [P.Edit("a.dfy", "", "y"), P.Verify()]
    assert r.propose(state(1, f1), ctx(), P.Budget()) == [P.Stop("done")]
    with pytest.raises(policies.ReplayDiverged, match="a.dfy"):
        r.propose(state(1, f0), ctx(), P.Budget())
    with pytest.raises(policies.ReplayEnd):
        r.propose(state(2, f1), ctx(), P.Budget())


def test_replay_reproduces_a_malformed_reply(tmp_path):
    f0 = {"a.dfy": P.text_sha256("x")}
    d = write_actions(tmp_path, [{"step": 0, "files": f0, "malformed": "not JSON"}])
    with pytest.raises(P.Malformed, match="not JSON"):
        policies.ReplayPolicy(d).propose(state(0, f0), ctx(), P.Budget())


@pytest.mark.parametrize("recs", [
    [{"step": 1, "files": {}, "actions": []}],
    [{"step": 0, "files": {}}],
    [{"step": 0, "files": {}, "actions": [], "malformed": "x"}],
    [{"step": 0, "files": []}],
])
def test_replay_refuses_a_bad_recording(tmp_path, recs):
    with pytest.raises(ValueError):
        policies.ReplayPolicy(write_actions(tmp_path, recs))


def test_the_mole_plants_at_its_steps_and_passes_the_rest_through():
    asked = []

    def inner_fn(s, c, b):
        asked.append(s.step)
        return [P.Verify()]
    plant = (P.Edit("a.dfy", "", "lemma {:axiom} L()"), P.Stop("done"))
    labels = []
    m = policies.MolePolicy(policies.MockPolicy(inner_fn), {1: ("X03-a", plant)},
                            label_sink=lambda step, pid: labels.append((step, pid)))
    assert isinstance(m, policies.Policy)
    assert m.propose(state(0), ctx(), P.Budget()) == [P.Verify()]
    assert m.propose(state(1), ctx(), P.Budget()) == list(plant)
    assert m.propose(state(2), ctx(), P.Budget()) == [P.Verify()]
    assert asked == [0, 2]                         # the inner policy is not asked at a plant
    assert m.injected == [(1, "X03-a")] and labels == [(1, "X03-a")]
    # the plant id never enters a proposal
    assert "X03-a" not in json.dumps(P.proposal_to_json(m.propose(state(1), ctx(), P.Budget())))


def test_the_mole_checks_its_plants():
    inner = policies.ScriptedPolicy([[P.Verify()]])
    with pytest.raises(TypeError):
        policies.MolePolicy(object(), {})
    with pytest.raises(TypeError):
        policies.MolePolicy(inner, {-1: ("p", [P.Verify()])})
    with pytest.raises(TypeError):
        policies.MolePolicy(inner, {0: ("", [P.Verify()])})
    with pytest.raises(TypeError):
        policies.MolePolicy(inner, {0: ("p", ["not an action"])})
    with pytest.raises(TypeError):
        policies.MolePolicy(inner, {}, label_sink=3)
