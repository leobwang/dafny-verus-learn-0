"""The frozen core's own tests: fvh.labalpha, Lab alpha's policy instrument (DVR4 plan
sections 3.3 and 3.8): the equal feedback cap, the call record's accounting and the
failed-node rule, on an invented engine policy (no model, no verifier)."""

import json
from types import SimpleNamespace

import pytest

from fvh import labalpha as L
from fvh import protocol as P


def test_feedback_under_the_cap_is_unchanged_and_counted():
    fb = [{"kind": "diagnostic", "message": "assertion failed", "line": 3}]
    out, acc = L.cap_feedback(fb, 256)
    assert out is fb and acc["feedback_truncated"] is False
    text = json.dumps(fb, ensure_ascii=False, sort_keys=True)
    assert acc["feedback_bytes"] == len(text.encode()) == acc["feedback_bytes_sent"]
    assert acc["feedback_tokens_est"] == -(-len(text.encode()) // L.BYTES_PER_TOKEN)


def test_both_formats_meet_the_same_cap_head_and_tail_kept():
    raw = {"verdict": "failed", "diagnostics": [{"message": "x" * 5000, "line": i} for i in range(4)]}
    obl = [{"kind": "diagnostic", "message": "y" * 5000}] * 4
    for fb in (raw, obl):
        out, acc = L.cap_feedback(fb, 512)
        text = json.dumps(fb, ensure_ascii=False, sort_keys=True)
        assert acc["feedback_truncated"] is True and isinstance(out, str)
        assert len(out.encode()) <= 512 * L.BYTES_PER_TOKEN == acc["feedback_cap_tokens"] * 4
        assert acc["feedback_bytes_sent"] == len(out.encode())
        assert out.startswith(text[:200]) and out.endswith(text[-200:])
        assert "[R12 feedback cap:" in out


def test_the_cap_never_splits_a_character():
    out, _ = L.cap_feedback(["é" * 3000], 64)
    out.encode("utf-8")                                   # decodes cleanly: no half character
    with pytest.raises(ValueError):
        L.cap_feedback([], 10)


def test_message_accounting():
    capped, _ = L.cap_feedback(["z" * 9000], 64)
    for fb, trunc in (([{"a": 1}], False), (capped, True)):
        msg = json.dumps({"task": "t", "feedback": fb})
        acc = L.message_accounting(msg)
        assert acc["message_bytes"] == len(msg.encode()) and acc["feedback_truncated"] is trunc
        assert acc["feedback_bytes"] == len(json.dumps(fb, ensure_ascii=False, sort_keys=True).encode())
    assert L.message_accounting("not json") == {"message_bytes": 8}


# --- the failed-node rule, on an invented engine policy -----------------------------------

class Engine:
    def __init__(self):
        self.attempts, self.pending, self.observed = [], None, 0

    def observe(self, outcome):
        if self.pending is None:
            raise RuntimeError("no staged node to observe")
        self.observed += 1
        self.attempts[-1] = "observed"
        self.pending = None


class Row(str):
    @property
    def status(self):
        return str(self)


class EnginePolicy:
    """The engine policy's shape: observe the last verification, then stage one node whose
    hint data comes from ask; a rejected reply raises Malformed with no node pending."""

    def __init__(self, ask, seeds):
        self.ask, self.seeds, self.engine, self.prompts = ask, list(seeds), None, []

    def step_r12(self, state, ctx, budget):
        if self.engine is None:
            self.engine = Engine()
        else:                       # as fvh_r.engine.R12Policy: every later step observes first
            self.engine.observe(None)
        if len(self.engine.attempts) >= len(self.seeds):
            return [P.Stop("give-up", "generation budget exhausted")]
        prompt = json.dumps({"feedback": {"raw": "r" * 20000}, "n": len(self.engine.attempts)})
        reply = self.ask(prompt, self.seeds[len(self.engine.attempts)])
        if reply == "bad":
            self.engine.attempts.append(Row("malformed"))
            raise P.Malformed("model supplied invalid hint data")
        self.engine.attempts.append(Row("pending"))
        self.engine.pending = True
        return [P.Edit("t.dfy", "", reply), P.Verify(mode="gate")]


def test_a_rejected_reply_is_a_failed_node_and_the_run_goes_on():
    replies = iter(["bad", "bad", "good-1", "bad", "good-2"])
    seen = []

    def ask(prompt, seed):
        seen.append((json.loads(prompt), seed))
        return next(replies)
    pol = L.wrap(EnginePolicy, cap_tokens=256)(ask, [11, 12, 13, 14, 15])
    out = pol.step_r12(None, None, SimpleNamespace(exhausted=False))
    assert isinstance(out[0], P.Edit) and out[0].new == "good-1" and pol.failed_nodes == 2
    assert [s for _, s in seen] == [11, 12, 13]           # the next seed each time
    assert all(isinstance(p["feedback"], str) and "[R12 feedback cap:" in p["feedback"] for p, _ in seen)
    assert pol.engine.observed == 0 and "observe" not in vars(pol.engine)
    out = pol.step_r12(None, None, SimpleNamespace(exhausted=False))   # observe, then a bad one
    assert out[0].new == "good-2" and pol.engine.observed == 1 and pol.failed_nodes == 3
    out = pol.step_r12(None, None, SimpleNamespace(exhausted=False))
    assert isinstance(out[0], P.Stop) and out[0].reason == "give-up"


def test_other_malformed_steps_still_end_the_run():
    class Broken(EnginePolicy):
        def step_r12(self, state, ctx, budget):
            raise P.Malformed("task context changed")
    pol = L.wrap(Broken)(lambda p, s: "good", [1])
    with pytest.raises(P.Malformed, match="context changed"):
        pol.step_r12(None, None, SimpleNamespace(exhausted=False))


def test_the_regimes_wrap_the_engine_by_name(monkeypatch):
    import sys
    import types
    mod = types.ModuleType("fvhtest_engine")
    mod.R12BestFirst = EnginePolicy
    monkeypatch.setitem(sys.modules, "fvhtest_engine", mod)
    monkeypatch.setattr(L, "ENGINE", "fvhtest_engine")
    pol = L.BestFirst(lambda p, s: "good", [1])
    assert isinstance(pol, EnginePolicy) and type(pol).__name__ == "LabAlphaEnginePolicy"


def test_the_learner_header_stays_out_of_the_prompt():
    src = "// [R12 header] DO NOT OPEN BEFORE R11 IS DONE.\n// [R12 header] more\n// R12_HINT_SITES: []\nlemma L() {}\n"
    out = L.strip_header(src)
    assert out == "//\n//\n// R12_HINT_SITES: []\nlemma L() {}\n" and out.count("\n") == src.count("\n")
    assert L.strip_header("// a comment\nx\n") == "// a comment\nx\n"
    seen = []
    ask = L._capped_ask(lambda p, s: seen.append(json.loads(p)) or "x", 256)
    ask(json.dumps({"source": src, "feedback": []}), 1)
    assert "DO NOT OPEN" not in seen[0]["source"] and seen[0]["source"] == out
