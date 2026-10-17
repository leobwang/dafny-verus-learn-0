"""Q15's acceptance tests for harness/q/fvh_q/oracles.py (frozen; QPLAN §25.1, §25.6).

They fail while H9py-H12py are holes and pass on a correct file. No solver
runs here: the tasks are synthetic toys (plain integers, no course
definition), and every `vcheck --gate` run goes to a stand-in runner that
reads the generated file and answers from a table, so the tests see exactly
which files the oracles write and how they judge each result. The expected
mutants are written out by hand (MUTANTS_D, MUTANTS_V), never re-derived
from the function under test.

What they hold the oracles to:
  - `mutants`: the sites and operators of the docstring, in order, with ids;
  - `kill_rate`: one gate run per mutant, through `fvh.tools.run` looked up at
    call time unless `run` is given, killed / survived / unknown by
    `outcome`, and the rate;
  - `implication`: the two lemmas, named and built as the docstring says, and
    their outcomes;
  - `classify`: the decision table, VACUOUS first and UNDECIDED for
    everything the verifier did not settle.

Run: scripts/vcheck harness/q/fvh_q/oracles.py
     (or, from harness/: uv run pytest tests/q/test_oracles.py)
"""

import re
from pathlib import Path

import pytest

from fvh import tools
from fvh.tools import ToolResult
from fvh_q import oracles as orc

SHA0 = "0" * 64

D_BODY = '''    // clamp: 0 < x is checked first
    if x < lo {
      r := lo - 1 + 1;
    } else if hi <= x {
      r := hi;
    } else {
      r := x;
    }
    assert r == r ==> true;
    var s := "a < b";
    var t := -1;
'''
TASK_D = orc.Task("toy-d", "dafny", "Clamp", (("x", "int"), ("lo", "int"), ("hi", "int")),
                  (("r", "int"),), D_BODY, "module Toy {\n", "}\n")

V_BODY = '''    let mut v: Vec<u64> = Vec::new();
    let w = Seq::<u64>::empty();
    let k = 0x10 + 1u64;
    if i + 1 < n && v@ =~= w {
        n - 1
    } else {
        -2
    }
'''
TASK_V = orc.Task("toy-v", "verus", "pick", (("i", "u64"), ("n", "u64")), (("r", "u64"),),
                  V_BODY, "use vstd::prelude::*;\n\nverus! {\n\n", "\n} // verus!\n")

# (id, operator, offset, the body's text at the offset)
MUTANTS_D = [("M01", "ror", 46, "<"), ("M02", "aor", 67, "-"), ("M03", "lit+", 69, "1"),
             ("M04", "lit-", 69, "1"), ("M05", "aor", 71, "+"), ("M06", "lit+", 73, "1"),
             ("M07", "lit-", 73, "1"), ("M08", "ror", 93, "<="), ("M09", "ror", 161, "=="),
             ("M10", "lit+", 212, "1"), ("M11", "lit-", 212, "1")]
MUTANTS_V = [("M01", "aor", 88, "+"), ("M02", "lit+", 90, "1"), ("M03", "lit-", 90, "1"),
             ("M04", "aor", 105, "+"), ("M05", "lit+", 107, "1"), ("M06", "lit-", 107, "1"),
             ("M07", "ror", 109, "<"), ("M08", "aor", 137, "-"), ("M09", "lit+", 139, "1"),
             ("M10", "lit-", 139, "1"), ("M11", "lit+", 163, "2"), ("M12", "lit-", 163, "2")]
SWAP = {"ror": {"<": "<=", "<=": "<", "==": "!="}, "aor": {"+": "-", "-": "+"}}


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


def expected_body(body, op, off, tok):
    if op in ("lit+", "lit-"):
        v = int(tok)
        return body[:off] + str(v + 1 if op == "lit+" else v - 1) + body[off + len(tok):]
    return body[:off] + SWAP[op][tok] + body[off + len(tok):]


# --- H9: mutants -------------------------------------------------------------------------

@pytest.mark.parametrize("task,table", [(TASK_D, MUTANTS_D), (TASK_V, MUTANTS_V)])
def test_mutants_sites_and_order(task, table):
    ms = orc.mutants(task)
    assert [(m.id, m.operator, m.offset) for m in ms] == [(i, o, f) for i, o, f, _ in table]
    for m, (_, op, off, tok) in zip(ms, table):
        assert task.body[off:off + len(tok)] == tok
        assert m.body == expected_body(task.body, op, off, tok)
        assert isinstance(m, orc.Mutant)


def test_mutants_none_without_sites():
    t = orc.Task("toy-n", "dafny", "Id", (("x", "int"),), (("r", "int"),),
                 "    r := x; // x < 1\n    var s := \"2 + 3\";\n", "module T {\n", "}\n")
    assert orc.mutants(t) == ()


def test_mutants_each_differs_and_is_distinct():
    for task in (TASK_D, TASK_V):
        bodies = [m.body for m in orc.mutants(task)]
        assert len(bodies) == len(set(bodies))
        assert task.body not in bodies


def test_mutants_no_lit_minus_on_zero():
    t = orc.Task("toy-r", "dafny", "Z", (), (("r", "int"),), "    r := 0 + 0;\n", "module T {\n", "}\n")
    ms = orc.mutants(t)
    # lit+ on either 0 gives a different body; aor gives `0 - 0`; no lit- on 0
    assert [(m.operator, m.offset) for m in ms] == [("lit+", 9), ("aor", 11), ("lit+", 13)]
    assert [m.id for m in ms] == ["M01", "M02", "M03"]


# --- H10: kill_rate ----------------------------------------------------------------------

SPEC_D = orc.Spec(TASK_D, ("lo <= hi",), ("lo <= r <= hi", "x < lo ==> r == lo"))


def decide_by_marker(text):
    # the stand-in judges each mutant by a marker of its body
    if "lo - 1 - 1" in text or "hi < x" in text:
        return res(doc("verified"))                     # survives
    if "lo - 2 + 1" in text:
        return res({}, killed="memory")                 # unknown
    if "r != r" in text:
        return res(doc("failed", stage="resolve"))      # unknown: a front-end stage
    return res(doc("failed"))                           # killed


def test_kill_rate_counts_and_rate(tmp_path):
    ms = orc.mutants(TASK_D)
    run = Runner(decide_by_marker)
    rep = orc.kill_rate(SPEC_D, ms, run=run, workdir=tmp_path)
    assert isinstance(rep, orc.KillReport)
    by_body = {m.id: m.body for m in ms}
    survivors = [m.id for m in ms if "lo - 1 - 1" in m.body or "hi < x" in m.body]
    unknown = [m.id for m in ms if "lo - 2 + 1" in m.body or "r != r" in m.body]
    assert survivors and unknown
    assert rep.total == len(ms) and rep.survived == len(survivors) and rep.unknown == len(unknown)
    assert rep.killed == len(ms) - len(survivors) - len(unknown)
    assert rep.survivors == tuple(survivors)
    assert rep.rate == pytest.approx(rep.killed / rep.total)
    assert [c[0] for c in run.calls] == ["vcheck --gate"] * len(ms)
    for (_, target, text), m in zip(run.calls, ms):
        assert Path(target).parent == tmp_path
        assert text == orc.render_program(TASK_D, SPEC_D, by_body[m.id])


def test_kill_rate_uses_fvh_tools_run_at_call_time(monkeypatch, tmp_path):
    run = Runner(lambda text: res(doc("failed")))
    monkeypatch.setattr(tools, "run", run)
    rep = orc.kill_rate(SPEC_D, orc.mutants(TASK_D)[:2], workdir=tmp_path)
    assert len(run.calls) == 2 and rep.killed == 2 and rep.rate == 1.0


def test_kill_rate_never_counts_a_pass_with_holes(tmp_path):
    run = Runner(lambda text: res(doc("verified", holes=["h"]), exit_code=0))
    rep = orc.kill_rate(SPEC_D, orc.mutants(TASK_D)[:3], run=run, workdir=tmp_path)
    assert (rep.killed, rep.survived, rep.unknown) == (0, 0, 3)


def test_kill_rate_refuses_no_mutant():
    with pytest.raises(ValueError):
        orc.kill_rate(SPEC_D, (), run=Runner(lambda t: res(doc("failed"))))


# --- H11: implication --------------------------------------------------------------------

REF_D = orc.Spec(TASK_D, ("lo <= hi",), ("lo <= r <= hi", "x < lo ==> r == lo",
                                         "hi < x ==> r == hi", "lo <= x <= hi ==> r == x"))


def sections(text, lang):
    """(name, params, requires clauses, ensures clauses) of the one lemma in text."""
    if lang == "dafny":
        m = re.search(r"lemma (\w+)\(([^)]*)\)\n((?:    (?:requires|ensures) .*\n)*)  \{", text)
        assert m, text
        req = re.findall(r"^    requires (.*)$", m.group(3), flags=re.M)
        ens = re.findall(r"^    ensures (.*)$", m.group(3), flags=re.M)
    else:
        m = re.search(r"pub proof fn (\w+)\(([^)]*)\)\n(.*?)\n\{", text, flags=re.S)
        assert m, text
        block = m.group(3)
        req_s = re.search(r"    requires\n((?:        .*,\n?)*)", block + "\n")
        ens_s = re.search(r"    ensures\n((?:        .*,\n?)*)", block + "\n")
        req = [c.strip()[:-1] for c in req_s.group(1).splitlines()] if req_s else []
        ens = [c.strip()[:-1] for c in ens_s.group(1).splitlines()] if ens_s else []
    return m.group(1), m.group(2), req, ens


def test_implication_lemmas_dafny(tmp_path):
    spec = orc.Spec(TASK_D, ("lo <= hi",), ("lo <= r <= hi",))
    outcomes = {"Clamp_SpecImpliesRef": res(doc("failed")),
                "Clamp_RefImpliesSpec": res(doc("verified"))}
    run = Runner(lambda text: outcomes[sections(text, "dafny")[0]])
    imp = orc.implication(spec, REF_D, run=run, workdir=tmp_path)
    assert imp == orc.Implication("failed", "proved")
    got = {sections(t, "dafny")[0]: sections(t, "dafny") for _, _, t in run.calls}
    assert set(got) == {"Clamp_SpecImpliesRef", "Clamp_RefImpliesSpec"}
    _, params, req, ens = got["Clamp_SpecImpliesRef"]
    assert params == "x: int, lo: int, hi: int, r: int"
    assert req == list(REF_D.requires) + list(spec.requires) + list(spec.ensures)
    assert ens == list(REF_D.ensures)
    _, params, req, ens = got["Clamp_RefImpliesSpec"]
    assert req == list(REF_D.requires) + list(REF_D.ensures)
    assert ens == list(spec.requires) + list(spec.ensures)
    for _, target, text in run.calls:
        assert text.startswith(TASK_D.header) and text.endswith(TASK_D.footer)
        assert Path(target).parent == tmp_path


def test_implication_lemmas_verus(tmp_path):
    spec = orc.Spec(TASK_V, ("i < n",), ("r <= n",))
    ref = orc.Spec(TASK_V, ("i < n",), ("r < n",))
    outcomes = {"pick_spec_implies_ref": res(doc("verified")),
                "pick_ref_implies_spec": res({}, killed="wall-clock")}
    run = Runner(lambda text: outcomes[sections(text, "verus")[0]])
    imp = orc.implication(spec, ref, run=run, workdir=tmp_path)
    assert imp == orc.Implication("proved", "unknown")
    got = {sections(t, "verus")[0]: sections(t, "verus") for _, _, t in run.calls}
    _, params, req, ens = got["pick_spec_implies_ref"]
    assert params == "i: u64, n: u64, r: u64"
    assert req == ["i < n", "i < n", "r <= n"] and ens == ["r < n"]
    _, _, req, ens = got["pick_ref_implies_spec"]
    assert req == ["i < n", "r < n"] and ens == ["i < n", "r <= n"]


def test_implication_uses_fvh_tools_run_at_call_time(monkeypatch, tmp_path):
    run = Runner(lambda text: res(doc("verified")))
    monkeypatch.setattr(tools, "run", run)
    assert orc.implication(SPEC_D, REF_D, workdir=tmp_path) == orc.Implication("proved", "proved")
    assert [c[0] for c in run.calls] == ["vcheck --gate", "vcheck --gate"]


def test_implication_refuses_different_tasks():
    with pytest.raises(ValueError):
        orc.implication(SPEC_D, orc.Spec(TASK_V), run=Runner(lambda t: res(doc("verified"))))


# --- H12: classify -----------------------------------------------------------------------

@pytest.mark.parametrize("a,b,vac,want", [
    ("proved", "proved", "failed", "FAITHFUL"),
    ("proved", "failed", "failed", "STRONG"),
    ("failed", "proved", "failed", "WEAK"),
    ("failed", "failed", "failed", "UNDECIDED"),
    ("unknown", "proved", "failed", "UNDECIDED"),
    ("proved", "unknown", "failed", "UNDECIDED"),
    ("proved", "proved", "proved", "VACUOUS"),
    ("failed", "failed", "proved", "VACUOUS"),
    ("proved", "proved", "unknown", "UNDECIDED"),
])
def test_classify_table(a, b, vac, want):
    assert orc.classify(orc.Implication(a, b), vac) is orc.Verdict[want]


@pytest.mark.parametrize("a,b,vac", [("yes", "proved", "failed"), ("proved", "proved", None),
                                     ("proved", "", "failed")])
def test_classify_refuses_non_outcomes(a, b, vac):
    with pytest.raises(ValueError):
        orc.classify(orc.Implication(a, b), vac)


# --- the given pieces the holes rest on --------------------------------------------------

def test_outcome_and_vacuity(tmp_path):
    assert orc.outcome(res(doc("verified"))) == "proved"
    assert orc.outcome(res(doc("verified", count=0), exit_code=0)) == "unknown"
    assert orc.outcome(res(doc("failed"))) == "failed"
    assert orc.outcome(res(doc("failed", stage="parse"))) == "unknown"
    assert orc.outcome(res({}, killed="memory")) == "unknown"
    run = Runner(lambda text: res(doc("verified")))
    assert orc.vacuity(orc.Spec(TASK_D, ("lo > hi", "lo < hi")), run=run, workdir=tmp_path) == "proved"
    assert sections(run.calls[0][2], "dafny")[3] == ["false"]
    assert orc.vacuity(orc.Spec(TASK_D, (), ("r == x",)), run=run) == "failed"
    assert len(run.calls) == 1
