"""R15's acceptance tests for harness/r/fvh_r/roundtrip.py (frozen; PLAN §4.3, Lab β).

They fail while H3py is a hole and pass on a correct file. No model and no
solver runs here (CI never calls a model): the policy is a script of fixed
replies that records every prompt it is sent, the cards are synthetic toys
(plain integers and booleans), and every `vcheck --gate` run goes to a
stand-in runner that reads the generated lemma and answers from a table
keyed on its name. Every expected value is written out by hand, never
re-derived from the code under test.

What they hold the round trip to:
  - two policy calls, the described specification first, then the
    signature and the description only;
  - redaction: a second prompt that quotes a clause of the original raises
    ValueError before it is sent, and nothing runs;
  - an unparsed second reply: verdict "unparsed", no gate run, no file;
  - the two implication lemmas, named and built as the docstring says,
    forward first, and the verdict table (an unsettled run is "unknown").
A body that always answers "equivalent" fails them.

Run: scripts/vcheck harness/r/fvh_r/roundtrip.py
     (or, from harness/: uv run pytest tests/r/r15_cases/test_roundtrip.py)
"""

import re
from pathlib import Path

import pytest

from fvh import tools
from fvh.tools import ToolResult
from fvh_r import roundtrip as rt
from fvh_r import spectest as st

SHA0 = "0" * 64

CARD_D = st.CardR15("toy-d-twice", "dafny", "Twice", (("x", "int"),), (("r", "int"),),
                    "module ToyR15 {\n  function Dbl(n: int): int { n + n }\n\n", "}\n")
CARD_V = st.CardR15("toy-v-sign", "verus", "is_pos", (("n", "i64"),), (("b", "bool"),),
                    "use vstd::prelude::*;\n\nverus! {\n\n", "\n} // verus!\n")
SPEC_D = st.SpecR15(CARD_D, ("0 <= x",), ("r == 2 * x",))
SPEC_V = st.SpecR15(CARD_V, (), ("b == (n > 0)",))

DESC_D = "Given a whole number x that is not negative, it returns r, exactly twice x."
DESC_V = "It answers true exactly when the number n is positive, and false otherwise."


def doc(verdict, stage="verify", holes=(), count=3):
    return {"verdict": verdict, "stage": stage, "holes": list(holes), "verified_count": count,
            "diagnostics": []}


def res(document, *, exit_code=None, killed=None, target="t"):
    if exit_code is None:
        exit_code = 0 if document.get("verdict") == "verified" else 1
    if killed is not None:
        document, exit_code = {"exit_code": None, "lines": ["killed"]}, None
    return ToolResult("vcheck --gate", target, document, exit_code, killed, "replay", "agent", SHA0)


class Runner:
    """A stand-in for fvh.tools.run: records (instrument, path, text) and
    answers with decide(text)."""

    def __init__(self, decide):
        self.decide, self.calls = decide, []

    def __call__(self, instrument, target, **kw):
        text = Path(target).read_text(encoding="utf-8")
        self.calls.append((instrument, target, text))
        return self.decide(text)


class Script:
    """A scripted policy: the n-th reply to the n-th prompt; records prompts."""

    def __init__(self, *replies):
        self.replies, self.prompts = list(replies), []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        assert len(self.prompts) <= len(self.replies), "the script has no reply for this call"
        return self.replies[len(self.prompts) - 1]


def lemma_name(text):
    m = re.search(r"(?:lemma|pub proof fn) (\w+)\(", text)
    assert m, text
    return m.group(1)


def by_name(table):
    return lambda text: table[lemma_name(text)]


def fence(*lines, tag="dafny"):
    return "Here it is.\n```" + tag + "\n" + "\n".join(lines) + "\n```\nDone.\n"


def files_written(tmp_path):
    return sorted(str(p) for p in Path(tmp_path).iterdir())


# --- the given prompts, parser and lemma ---------------------------------------------------

def test_describe_prompt_holds_signature_and_clauses_only():
    p = rt.describe_prompt_r15(SPEC_D)
    assert "method Twice(x: int) returns (r: int)" in p
    assert "0 <= x" in p and "r == 2 * x" in p and "English" in p
    assert "n + n" not in p and "Dbl" not in p and "module ToyR15" not in p
    q = rt.describe_prompt_r15(SPEC_V)
    assert "fn is_pos(n: i64) -> (b: bool)" in q and "b == (n > 0)" in q
    assert "verus!" not in q and "vstd" not in q


def test_formalize_prompt_holds_signature_and_description_only():
    p = rt.formalize_prompt_r15(CARD_D, DESC_D)
    assert "method Twice(x: int) returns (r: int)" in p and DESC_D in p
    assert "requires:" in p and "ensures:" in p
    assert "0 <= x" not in p and "r == 2 * x" not in p and "n + n" not in p
    with pytest.raises(TypeError):
        rt.formalize_prompt_r15(CARD_D, None)


@pytest.mark.parametrize("text,want", [
    (fence("  requires: 0 <= x ", "", "ensures: r == x + x"), (("0 <= x",), ("r == x + x",))),
    (fence("ensures: r >= x", tag=""), ((), ("r >= x",))),
    ("```\nensures: a\n```\n```\nensures: b\n```\n", ((), ("a",))),
])
def test_parse_spec_reply(text, want):
    assert rt.parse_spec_reply_r15(CARD_D, text) == st.SpecR15(CARD_D, *want)


@pytest.mark.parametrize("text", [
    "requires: 0 <= x\nensures: r == x + x\n",            # no fenced block
    fence("ensures: r == x + x", "so r is even"),          # a line of neither form
    fence("ensures:"),                                     # an empty clause
    fence(""),                                             # no clause
    None,
])
def test_parse_spec_reply_none(text):
    assert rt.parse_spec_reply_r15(CARD_D, text) is None


FORWARD_D = """module ToyR15 {
  function Dbl(n: int): int { n + n }

  lemma Twice_Forward(x: int, r: int)
    requires 0 <= x
    requires r == 2 * x
    ensures 0 <= x
    ensures r == x + x
  {
  }
}
"""

BACKWARD_D = """module ToyR15 {
  function Dbl(n: int): int { n + n }

  lemma Twice_Backward(x: int, r: int)
    requires 0 <= x
    requires r == x + x
    ensures 0 <= x
    ensures r == 2 * x
  {
  }
}
"""

FORWARD_V = """use vstd::prelude::*;

verus! {

pub proof fn is_pos_forward(n: i64, b: bool)
    requires
        b == (n > 0),
    ensures
        b <==> n > 0,
{
}

} // verus!
"""


def test_render_implication():
    spec2 = st.SpecR15(CARD_D, ("0 <= x",), ("r == x + x",))
    assert rt.render_implication_r15(CARD_D, "Twice_Forward", SPEC_D, spec2) == FORWARD_D
    assert rt.render_implication_r15(CARD_D, "Twice_Backward", spec2, SPEC_D) == BACKWARD_D
    with pytest.raises(ValueError):
        rt.render_implication_r15(CARD_D, "L", SPEC_D, SPEC_V)


# --- H3: roundtrip_r15 -------------------------------------------------------------------

def test_roundtrip_equivalent_dafny(tmp_path):
    ask = Script(DESC_D, fence("requires: 0 <= x", "ensures: r == x + x"))
    run = Runner(by_name({"Twice_Forward": res(doc("verified")),
                          "Twice_Backward": res(doc("verified"))}))
    rep = rt.roundtrip_r15(SPEC_D, ask, run=run, workdir=tmp_path)
    spec2 = st.SpecR15(CARD_D, ("0 <= x",), ("r == x + x",))
    assert rep == rt.RoundtripReportR15(DESC_D, spec2, "proved", "proved", "equivalent", 2)
    assert ask.prompts == [rt.describe_prompt_r15(SPEC_D), rt.formalize_prompt_r15(CARD_D, DESC_D)]
    assert [c[0] for c in run.calls] == ["vcheck --gate"] * 2
    assert [c[2] for c in run.calls] == [FORWARD_D, BACKWARD_D]
    assert files_written(tmp_path) == sorted(c[1] for c in run.calls)
    assert len(set(c[1] for c in run.calls)) == 2


@pytest.mark.parametrize("ensures,fwd,bwd,want", [
    # r >= x follows from r == 2 * x on x >= 0, not conversely: spec2 says less
    ("r >= x", res(doc("verified")), res(doc("failed")), ("proved", "failed", "weaker")),
    # r == x + x && r > x fails at x = 0: spec2 says more
    ("r == x + x && r > x", res(doc("failed")), res(doc("verified")),
     ("failed", "proved", "stronger")),
    ("r == x + 1", res(doc("failed")), res(doc("failed")), ("failed", "failed", "incomparable")),
    ("r == x + x", res({}, killed="wall-clock"), res(doc("failed")),
     ("unknown", "failed", "unknown")),
    ("r == x + x", res(doc("verified")), res(doc("failed", stage="resolve")),
     ("proved", "unknown", "unknown")),
    ("r == x + x", res(doc("verified", holes=["h"]), exit_code=0), res(doc("verified")),
     ("unknown", "proved", "unknown")),
])
def test_roundtrip_verdict_table(tmp_path, ensures, fwd, bwd, want):
    ask = Script(DESC_D, fence("requires: 0 <= x", f"ensures: {ensures}"))
    run = Runner(by_name({"Twice_Forward": fwd, "Twice_Backward": bwd}))
    rep = rt.roundtrip_r15(SPEC_D, ask, run=run, workdir=tmp_path)
    assert (rep.forward, rep.backward, rep.verdict) == want
    assert rep.spec2 == st.SpecR15(CARD_D, ("0 <= x",), (ensures,))
    assert rep.calls == 2 and rep.description == DESC_D
    assert [lemma_name(c[2]) for c in run.calls] == ["Twice_Forward", "Twice_Backward"]


def test_roundtrip_verus(tmp_path):
    ask = Script(DESC_V, fence("ensures: b <==> n > 0", tag="verus"))
    run = Runner(by_name({"is_pos_forward": res(doc("verified")),
                          "is_pos_backward": res(doc("verified"))}))
    rep = rt.roundtrip_r15(SPEC_V, ask, run=run, workdir=tmp_path)
    assert rep == rt.RoundtripReportR15(DESC_V, st.SpecR15(CARD_V, (), ("b <==> n > 0",)),
                                        "proved", "proved", "equivalent", 2)
    assert run.calls[0][2] == FORWARD_V
    assert [lemma_name(c[2]) for c in run.calls] == ["is_pos_forward", "is_pos_backward"]


@pytest.mark.parametrize("reply", [
    "requires: 0 <= x\nensures: r == x + x\n",
    fence("r is twice x"),
    "",
])
def test_roundtrip_unparsed_runs_nothing(tmp_path, reply):
    ask = Script(DESC_D, reply)
    run = Runner(lambda text: pytest.fail("an unparsed reply reached the verifier"))
    rep = rt.roundtrip_r15(SPEC_D, ask, run=run, workdir=tmp_path)
    assert rep == rt.RoundtripReportR15(DESC_D, None, None, None, "unparsed", 2)
    assert len(ask.prompts) == 2 and run.calls == [] and files_written(tmp_path) == []


@pytest.mark.parametrize("description", [
    "It returns r == 2 * x.",                      # quotes the ensures
    "It needs 0 <= x and doubles x.",              # quotes the requires
])
def test_roundtrip_redaction(tmp_path, description):
    ask = Script(description, fence("ensures: r == 2 * x"))
    run = Runner(lambda text: pytest.fail("a redaction failure reached the verifier"))
    with pytest.raises(ValueError):
        rt.roundtrip_r15(SPEC_D, ask, run=run, workdir=tmp_path)
    assert len(ask.prompts) == 1 and run.calls == [] and files_written(tmp_path) == []


def test_roundtrip_uses_fvh_tools_run_at_call_time(monkeypatch, tmp_path):
    run = Runner(lambda text: res(doc("verified")))
    monkeypatch.setattr(tools, "run", run)
    ask = Script(DESC_D, fence("requires: 0 <= x", "ensures: r == x + x"))
    rep = rt.roundtrip_r15(SPEC_D, ask, workdir=tmp_path)
    assert rep.verdict == "equivalent" and len(run.calls) == 2
