"""R15's acceptance tests for harness/r/fvh_r/spectest.py (frozen; PLAN §4.3, Lab β).

They fail while H1py and H2py are holes and pass on a correct file. No solver
runs here: the cards are synthetic toys (plain integers and booleans, no
course definition), and every `vcheck --gate` run goes to a stand-in runner
that reads the generated file and answers from a table keyed on its
content, so the tests see exactly which files the oracles write and how they
judge each result. Every expected value (rendered files, mutants, outcomes,
counts) is written out by hand, never re-derived from the code under test.

What they hold the oracles to:
  - the given renderer: the binding requires (`x == <literal>`, parameters
    then results), then the spec's requires, and the postcondition or its
    negation as one ensures; the pair's witness hints as `assert` lines in
    the body (D99);
  - the given mutator: the operators per result type, ids, drops;
  - `spec_sound_r15`: one gate run per pair of the non-negated check,
    proved -> holds, failed -> rejects, anything else (a killed run, a
    front-end stage, a refusal, a pass with holes) -> unknown; sound only
    when every pair holds; a failed check of a specification with an
    existential and a pair without witness hints -> unknown, never rejects
    (D99);
  - `spec_complete_r15`: one gate run per output mutant of the negated
    check, proved -> killed, failed -> survived, else unknown; survivors as
    "<pair index>:<mutant id>"; rate over the decided mutants only; the
    same existential exception (a failed check without witness -> unknown);
  - both look `fvh.tools.run` up at call time when `run` is not given.
A body that always answers "sound", or a kill rate of 1.0, fails them.

Run: scripts/vcheck harness/r/fvh_r/spectest.py
     (or, from harness/: uv run pytest tests/r/r15_cases/test_spectest.py)
"""

import re
from pathlib import Path

import pytest

from fvh import tools
from fvh.tools import ToolResult
from fvh_r import spectest as st

SHA0 = "0" * 64

CARD_D = st.CardR15("toy-d-twice", "dafny", "Twice", (("x", "int"),), (("r", "int"),),
                    "module ToyR15 {\n  function Dbl(n: int): int { n + n }\n\n", "}\n")
CARD_V = st.CardR15("toy-v-sign", "verus", "is_pos", (("n", "i64"),), (("b", "bool"),),
                    "use vstd::prelude::*;\n\nverus! {\n\n", "\n} // verus!\n")
SPEC_D = st.SpecR15(CARD_D, ("0 <= x",), ("r == 2 * x",))
SPEC_V = st.SpecR15(CARD_V, (), ("b == (n > 0)",))
SPEC_EVEN = st.SpecR15(CARD_D, (), ("r % 2 == 0",))


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


def bound(text, name):
    """The literal a generated check binds `name` to (Dafny or Verus form)."""
    m = re.search(rf"^\s*(?:requires )?{name} == (-?\w+),?$", text, flags=re.M)
    assert m, text
    return m.group(1)


def files_written(tmp_path):
    return sorted(str(p) for p in Path(tmp_path).iterdir())


# --- the given renderer and mutator ------------------------------------------------------

SOUND_D_3 = """module ToyR15 {
  function Dbl(n: int): int { n + n }

  lemma Twice_PairHolds(x: int, r: int)
    requires x == 3
    requires r == 6
    requires 0 <= x
    ensures r == 2 * x
  {
  }
}
"""

REJECT_V_5 = """use vstd::prelude::*;

verus! {

pub proof fn is_pos_mutant_rejected(n: i64, b: bool)
    requires
        n == 5,
        b == false,
    ensures
        !(b == (n > 0)),
{
}

} // verus!
"""


def test_render_pair_check_binds_then_requires_then_post():
    assert st.render_pair_check_r15(CARD_D, SPEC_D, "Twice_PairHolds", ("3",), ("6",),
                                    False) == SOUND_D_3
    assert st.render_pair_check_r15(CARD_V, SPEC_V, "is_pos_mutant_rejected", ("5",),
                                    ("false",), True) == REJECT_V_5


def test_render_pair_check_conjunction_and_empty():
    two = st.SpecR15(CARD_D, (), ("r >= x", "r % 2 == 0"))
    t = st.render_pair_check_r15(CARD_D, two, "L", ("1",), ("2",), False)
    assert "    ensures (r >= x) && (r % 2 == 0)\n" in t
    t = st.render_pair_check_r15(CARD_D, two, "L", ("1",), ("2",), True)
    assert "    ensures !((r >= x) && (r % 2 == 0))\n" in t
    none = st.SpecR15(CARD_D)
    assert "    ensures true\n" in st.render_pair_check_r15(CARD_D, none, "L", ("1",), ("2",), False)
    assert "    ensures false\n" in st.render_pair_check_r15(CARD_D, none, "L", ("1",), ("2",), True)


def test_render_pair_check_refuses_bad_arity_and_other_card():
    with pytest.raises(ValueError):
        st.render_pair_check_r15(CARD_D, SPEC_D, "L", ("1", "2"), ("2",), False)
    with pytest.raises(ValueError):
        st.render_pair_check_r15(CARD_D, SPEC_V, "L", ("1",), ("2",), False)
    with pytest.raises(TypeError):
        st.render_pair_check_r15(CARD_D, SPEC_D, "L", (1,), ("2",), False)


CARD_2 = st.CardR15("toy-d-two", "dafny", "Two", (("a", "int"), ("c", "int")),
                    (("q", "nat"), ("ok", "bool")), "module T {\n", "}\n")


@pytest.mark.parametrize("card,outputs,want", [
    (CARD_D, ("6",), [("O01", "r", ("7",)), ("O02", "r", ("5",)), ("O03", "r", ("0",))]),
    (CARD_D, ("0",), [("O01", "r", ("1",)), ("O02", "r", ("-1",))]),
    (CARD_D, ("1",), [("O01", "r", ("2",)), ("O02", "r", ("0",))]),
    (CARD_D, ("x + 1",), []),
    (CARD_V, ("true",), [("O01", "b", ("false",))]),
    (CARD_V, ("True",), []),
    (CARD_2, ("1", "true"), [("O01", "q", ("2", "true")), ("O02", "q", ("0", "true")),
                             ("O03", "ok", ("1", "false"))]),
    (CARD_2, ("0", "false"), [("O01", "q", ("1", "false")), ("O02", "ok", ("0", "true"))]),
])
def test_mutate_outputs(card, outputs, want):
    pair = st.IOPairR15(("4",) * len(card.params), outputs)
    got = st.mutate_outputs_r15(card, pair)
    assert all(isinstance(m, st.OutputMutantR15) for m in got)
    assert [(m.id, m.result, m.outputs) for m in got] == want


def test_mutate_outputs_other_types():
    seq = st.CardR15("toy-s", "dafny", "S", (), (("s", "seq<int>"),), "module T {\n", "}\n")
    assert st.mutate_outputs_r15(seq, st.IOPairR15((), ("[1, 2]",))) == ()
    neg = st.CardR15("toy-i", "verus", "f", (), (("r", "i64"),), "", "")
    assert [m.outputs for m in st.mutate_outputs_r15(neg, st.IOPairR15((), ("-3",)))] == \
        [("-2",), ("-4",), ("0",)]
    uns = st.CardR15("toy-u", "verus", "g", (), (("r", "u64"),), "", "")
    assert [m.outputs for m in st.mutate_outputs_r15(uns, st.IOPairR15((), ("0",)))] == [("1",)]


def test_outcome_rule():
    assert st.outcome_r15(res(doc("verified"))) == "proved"
    assert st.outcome_r15(res(doc("verified", count=0), exit_code=0)) == "unknown"
    assert st.outcome_r15(res(doc("verified", holes=["h"]), exit_code=0)) == "unknown"
    assert st.outcome_r15(res(doc("failed"))) == "failed"
    assert st.outcome_r15(res(doc("failed", stage="parse"))) == "unknown"
    assert st.outcome_r15(res(doc("refused", stage="cli"))) == "unknown"
    assert st.outcome_r15(res({}, killed="memory")) == "unknown"


# --- H1: spec_sound_r15 ------------------------------------------------------------------

PAIRS_D = (st.IOPairR15(("3",), ("6",)), st.IOPairR15(("0",), ("0",)),
           st.IOPairR15(("5",), ("10",)), st.IOPairR15(("7",), ("14",)))


def decide_sound_d(text):
    x = bound(text, "x")
    return {"3": res(doc("verified")),                    # holds
            "0": res({}, killed="memory"),                # unknown: killed
            "5": res(doc("failed")),                      # rejects
            "7": res(doc("failed", stage="resolve"))}[x]  # unknown: a front-end stage


def test_sound_outcomes_and_files(tmp_path):
    run = Runner(decide_sound_d)
    rep = st.spec_sound_r15(SPEC_D, PAIRS_D, run=run, workdir=tmp_path)
    assert isinstance(rep, st.SoundReportR15)
    assert rep.outcomes == ("holds", "unknown", "rejects", "unknown")
    assert rep.sound is False
    assert [c[0] for c in run.calls] == ["vcheck --gate"] * 4
    assert [bound(t, "x") for _, _, t in run.calls] == ["3", "0", "5", "7"]
    assert [bound(t, "r") for _, _, t in run.calls] == ["6", "0", "10", "14"]
    assert run.calls[0][2] == SOUND_D_3
    for _, _, t in run.calls:
        assert "    ensures r == 2 * x\n" in t and "!(" not in t
    assert files_written(tmp_path) == sorted(c[1] for c in run.calls)
    assert len(set(c[1] for c in run.calls)) == 4


def test_sound_all_hold_verus(tmp_path):
    run = Runner(lambda text: res(doc("verified")))
    pairs = (st.IOPairR15(("5",), ("true",)), st.IOPairR15(("-2",), ("false",)))
    rep = st.spec_sound_r15(SPEC_V, pairs, run=run, workdir=tmp_path)
    assert rep == st.SoundReportR15(("holds", "holds"), True)
    assert run.calls[1][2] == """use vstd::prelude::*;

verus! {

pub proof fn is_pos_pair_holds(n: i64, b: bool)
    requires
        n == -2,
        b == false,
    ensures
        b == (n > 0),
{
}

} // verus!
"""
    assert files_written(tmp_path) == sorted(c[1] for c in run.calls)


def test_sound_never_counts_unsettled_runs_as_holding(tmp_path):
    answers = iter([res(doc("verified", holes=["h"]), exit_code=0),
                    res(doc("verified"), exit_code=1),
                    res(doc("refused", stage="cli")),
                    res({}, killed="wall-clock")])
    run = Runner(lambda text: next(answers))
    rep = st.spec_sound_r15(SPEC_D, PAIRS_D, run=run, workdir=tmp_path)
    assert rep == st.SoundReportR15(("unknown",) * 4, False)


def test_sound_one_rejecting_pair_is_unsound(tmp_path):
    run = Runner(lambda text: res(doc("failed")) if bound(text, "x") == "5" else res(doc("verified")))
    rep = st.spec_sound_r15(SPEC_D, PAIRS_D, run=run, workdir=tmp_path)
    assert rep == st.SoundReportR15(("holds", "holds", "rejects", "holds"), False)


def test_sound_uses_fvh_tools_run_at_call_time(monkeypatch, tmp_path):
    run = Runner(lambda text: res(doc("verified")))
    monkeypatch.setattr(tools, "run", run)
    rep = st.spec_sound_r15(SPEC_D, PAIRS_D[:2], workdir=tmp_path)
    assert len(run.calls) == 2 and rep == st.SoundReportR15(("holds", "holds"), True)


def test_sound_refuses_no_pair():
    with pytest.raises(ValueError):
        st.spec_sound_r15(SPEC_D, (), run=Runner(lambda t: res(doc("verified"))))


# --- H2: spec_complete_r15 ---------------------------------------------------------------

PAIRS_EVEN = (st.IOPairR15(("3",), ("6",)), st.IOPairR15(("0",), ("0",)))

# The mutants of PAIRS_EVEN, by hand: pair 0 (r = 6) O01 7, O02 5, O03 0;
# pair 1 (r = 0) O01 1, O02 -1. Against `r % 2 == 0`: 7, 1 and -1 are
# rejected (proved), 0 survives (failed), and the run on 5 is killed.
TABLE_EVEN = {("3", "7"): res(doc("verified")),
              ("3", "5"): res({}, killed="memory"),
              ("3", "0"): res(doc("failed")),
              ("0", "1"): res(doc("verified")),
              ("0", "-1"): res(doc("verified"))}

REJECT_D_3_7 = """module ToyR15 {
  function Dbl(n: int): int { n + n }

  lemma Twice_MutantRejected(x: int, r: int)
    requires x == 3
    requires r == 7
    ensures !(r % 2 == 0)
  {
  }
}
"""


def test_complete_counts_survivors_and_rate(tmp_path):
    run = Runner(lambda text: TABLE_EVEN[(bound(text, "x"), bound(text, "r"))])
    rep = st.spec_complete_r15(SPEC_EVEN, PAIRS_EVEN, run=run, workdir=tmp_path)
    assert isinstance(rep, st.CompleteReportR15)
    assert rep == st.CompleteReportR15(5, 3, 1, 1, ("0:O03",), 0.75)
    assert [(bound(t, "x"), bound(t, "r")) for _, _, t in run.calls] == \
        [("3", "7"), ("3", "5"), ("3", "0"), ("0", "1"), ("0", "-1")]
    assert [c[0] for c in run.calls] == ["vcheck --gate"] * 5
    assert run.calls[0][2] == REJECT_D_3_7
    assert files_written(tmp_path) == sorted(c[1] for c in run.calls)
    assert len(set(c[1] for c in run.calls)) == 5


def test_complete_all_survive_is_rate_zero(tmp_path):
    run = Runner(lambda text: res(doc("failed")))
    rep = st.spec_complete_r15(SPEC_EVEN, PAIRS_EVEN, run=run, workdir=tmp_path)
    assert rep == st.CompleteReportR15(5, 0, 5, 0, ("0:O01", "0:O02", "0:O03", "1:O01", "1:O02"),
                                       0.0)


def test_complete_nothing_decided_is_rate_zero(tmp_path):
    answers = iter([res({}, killed="memory"), res(doc("failed", stage="parse")),
                    res(doc("refused", stage="cli")), res(doc("verified", count=0), exit_code=0),
                    res(doc("error", stage="verify"))])
    run = Runner(lambda text: next(answers))
    rep = st.spec_complete_r15(SPEC_EVEN, PAIRS_EVEN, run=run, workdir=tmp_path)
    assert rep == st.CompleteReportR15(5, 0, 0, 5, (), 0.0)


def test_complete_verus_front_end_is_unknown(tmp_path):
    table = {("5", "false"): res(doc("verified")), ("0", "true"): res(doc("failed", stage="resolve"))}
    run = Runner(lambda text: table[(bound(text, "n"), bound(text, "b"))])
    pairs = (st.IOPairR15(("5",), ("true",)), st.IOPairR15(("0",), ("false",)))
    rep = st.spec_complete_r15(SPEC_V, pairs, run=run, workdir=tmp_path)
    assert rep == st.CompleteReportR15(2, 1, 0, 1, (), 1.0)
    assert run.calls[0][2] == REJECT_V_5


def test_complete_no_mutant_runs_nothing(tmp_path):
    seq = st.CardR15("toy-s", "dafny", "S", (("k", "int"),), (("s", "seq<int>"),),
                     "module T {\n", "}\n")
    run = Runner(lambda text: res(doc("verified")))
    rep = st.spec_complete_r15(st.SpecR15(seq, (), ("|s| == k",)),
                               (st.IOPairR15(("2",), ("[1, 2]",)),), run=run, workdir=tmp_path)
    assert rep == st.CompleteReportR15(0, 0, 0, 0, (), 0.0)
    assert run.calls == [] and files_written(tmp_path) == []


def test_complete_uses_fvh_tools_run_at_call_time(monkeypatch, tmp_path):
    run = Runner(lambda text: res(doc("verified")))
    monkeypatch.setattr(tools, "run", run)
    rep = st.spec_complete_r15(SPEC_EVEN, PAIRS_EVEN[1:], workdir=tmp_path)
    assert len(run.calls) == 2 and rep == st.CompleteReportR15(2, 2, 0, 0, (), 1.0)


def test_complete_refuses_no_pair():
    with pytest.raises(ValueError):
        st.spec_complete_r15(SPEC_EVEN, (), run=Runner(lambda t: res(doc("verified"))))


# --- witness hints (D99): an existential without a witness is unknown, never a verdict ---

CARD_W = st.CardR15("toy-d-has", "dafny", "Has", (("s", "seq<int>"),), (("b", "bool"),),
                    "module ToyWR15 {\n\n", "}\n")
SPEC_W = st.SpecR15(CARD_W, (), ("b == exists i :: 0 <= i < |s| && s[i] == 7",))
CARD_WV = st.CardR15("toy-v-has", "verus", "has", (("s", "Seq<int>"),), (("b", "bool"),),
                     "use vstd::prelude::*;\n\nverus! {\n\n", "\n} // verus!\n")
SPEC_WV = st.SpecR15(CARD_WV, (), ("b == exists|i: int| 0 <= i < s.len() && s[i] == 7",))


def lit(text, name):
    """The whole literal a generated check binds `name` to (any literal form)."""
    m = re.search(rf"^\s*(?:requires )?{name} == (.+?),?$", text, flags=re.M)
    assert m, text
    return m.group(1)

HOLDS_W = """module ToyWR15 {

  lemma Has_PairHolds(s: seq<int>, b: bool)
    requires s == [1, 7]
    requires b == true
    ensures b == exists i :: 0 <= i < |s| && s[i] == 7
  {
    assert s[1] == 7;
  }
}
"""

REJECT_WV = """use vstd::prelude::*;

verus! {

pub proof fn has_mutant_rejected(s: Seq<int>, b: bool)
    requires
        s == seq![1, 7],
        b == false,
    ensures
        !(b == exists|i: int| 0 <= i < s.len() && s[i] == 7),
{
    assert(s[1] == 7);
}

} // verus!
"""


def test_has_existential():
    assert st.has_existential_r15(SPEC_W) and st.has_existential_r15(SPEC_WV)
    assert not st.has_existential_r15(SPEC_D) and not st.has_existential_r15(SPEC_V)
    assert not st.has_existential_r15(st.SpecR15(CARD_D, (), ("r == existsCount(x)",)))
    assert not st.has_existential_r15(st.SpecR15(CARD_D, ("exists k :: k == x",), ("true",)))


def test_render_pair_check_asserts_the_witnesses():
    assert st.render_pair_check_r15(CARD_W, SPEC_W, "Has_PairHolds", ("[1, 7]",), ("true",),
                                    False, witnesses=("s[1] == 7",)) == HOLDS_W
    assert st.render_pair_check_r15(CARD_WV, SPEC_WV, "has_mutant_rejected", ("seq![1, 7]",),
                                    ("false",), True, witnesses=("s[1] == 7",)) == REJECT_WV
    assert st.IOPairR15(("1",), ("2",)).witnesses == ()


def test_sound_existential_without_witness_is_unknown(tmp_path):
    pairs = (st.IOPairR15(("[1, 7]",), ("true",), ("s[1] == 7",)),   # witness: verdicts stand
             st.IOPairR15(("[7]",), ("true",), ("s[0] == 7",)),
             st.IOPairR15(("[1]",), ("false",)),                     # no witness
             st.IOPairR15(("[2, 3]",), ("false",)))
    table = {"[1, 7]": res(doc("verified")), "[7]": res(doc("failed")),
             "[1]": res(doc("failed")), "[2, 3]": res(doc("verified"))}
    run = Runner(lambda text: table[lit(text, "s")])
    rep = st.spec_sound_r15(SPEC_W, pairs, run=run, workdir=tmp_path)
    assert rep == st.SoundReportR15(("holds", "rejects", "unknown", "holds"), False)
    assert run.calls[0][2] == HOLDS_W
    assert "    assert s[0] == 7;\n" in run.calls[1][2]
    assert "assert" not in run.calls[2][2] and "assert" not in run.calls[3][2]
    # no existential: a failed check rejects with or without a hint
    run = Runner(lambda text: res(doc("failed")))
    rep = st.spec_sound_r15(SPEC_D, (st.IOPairR15(("3",), ("7",)),), run=run, workdir=tmp_path)
    assert rep.outcomes == ("rejects",)


def test_complete_existential_without_witness_is_unknown(tmp_path):
    pairs = (st.IOPairR15(("seq![1, 7]",), ("true",), ("s[1] == 7",)),
             st.IOPairR15(("seq![1]",), ("false",)),
             st.IOPairR15(("seq![7]",), ("true",), ("s[0] == 7",)))
    table = {"seq![1, 7]": res(doc("verified")), "seq![1]": res(doc("failed")),
             "seq![7]": res(doc("failed"))}
    run = Runner(lambda text: table[lit(text, "s")])
    rep = st.spec_complete_r15(SPEC_WV, pairs, run=run, workdir=tmp_path)
    assert rep == st.CompleteReportR15(3, 1, 1, 1, ("2:O01",), 0.5)
    assert run.calls[0][2] == REJECT_WV
    assert "assert" not in run.calls[1][2]
