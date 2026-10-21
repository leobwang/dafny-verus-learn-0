"""Q32's acceptance tests for agents/q32_proof_search/agent.py (frozen; QPLAN §34.1, Δ406).

They fail while any of Q32.H1py-H7py is a hole and pass on a correct file. No model
and no solver: `ask` is a scripted function, the verification documents are invented in
the shape `scripts/vcheck --gate --json` prints, and the index is built over a small
invented tree under tmp_path. Expected values are written out.

Run: scripts/vcheck agents/q32_proof_search/agent.py
"""

import hashlib
import json

import pytest

from fvh import protocol as P
from q32_proof_search import agent as A

LOOP = "method M(n: nat)\n{\n  var i := 0;\n  while i < n\n  {\n    i := i + 1;\n  }\n}\n"
WITH_INV = LOOP.replace("  while i < n\n", "  while i < n\n    invariant i <= n\n")
FAILED = {"verdict": "failed", "stage": "verify", "holes": [], "verified_count": 0,
          "diagnostics": [{"severity": "error", "line": 4, "message": "loop invariant 7 may not hold, see LemmaBound"}]}
VERIFIED = {"verdict": "verified", "stage": "verify", "holes": [], "verified_count": 1,
            "diagnostics": []}


def ctx():
    return P.Context(task_id="t", lang="dafny", statement="s", editable=("t.dfy",), readable=(),
                     target="t.dfy", material={"instructions": "Prove it.", "text": LOOP})


def state(step, files=None, last=None, history=()):
    return P.State("t", step, files or {"t.dfy": P.text_sha256(LOOP)}, last, tuple(history))


def test_compile_edit():
    e = A.compile_edit(A.TypedEdit("invariant", "t.dfy", "  while i < n", "    invariant i <= n"), LOOP)
    assert (e.path, e.old, e.new) == ("t.dfy", "  while i < n\n", "  while i < n\n    invariant i <= n\n")
    assert LOOP.replace(e.old, e.new) == WITH_INV
    for bad in (A.TypedEdit("rewrite", "t.dfy", "  while i < n", "x"),
                A.TypedEdit("assert", "t.dfy", "  while i < n", "    invariant i <= n"),
                A.TypedEdit("invariant", "t.dfy", "nowhere", "    invariant i <= n")):
        with pytest.raises(ValueError):
            A.compile_edit(bad, LOOP)
    with pytest.raises(ValueError):                                     # the anchor twice
        A.compile_edit(A.TypedEdit("invariant", "t.dfy", "  while i < n", "    invariant i <= n"),
                       LOOP + LOOP)


def test_typed_diff():
    got = A.typed_diff(LOOP, WITH_INV)
    assert got == A.TypedEdit("invariant", "", "  while i < n", "    invariant i <= n")
    assert A.typed_diff(LOOP, LOOP) is None
    assert A.typed_diff(LOOP, LOOP.replace("i + 1", "i + 2")) is None             # a change
    assert A.typed_diff(LOOP, LOOP.replace("  while", "    x := 1;\n  while")) is None  # no kind
    two = WITH_INV.replace("    i := i + 1;\n", "    i := i + 1;\n    assert i <= n;\n")
    assert A.typed_diff(LOOP, two) is None                                         # two places
    call = LOOP.replace("    i := i + 1;\n", "    i := i + 1;\n    LemmaBound(i, n);\n")
    assert A.typed_diff(LOOP, call).kind == "lemma-call"


def test_dedup_key_ignores_moved_lines():
    moved = json.loads(json.dumps(FAILED))
    moved["diagnostics"][0]["message"] = "loop invariant 9 may not hold, see LemmaBound"
    moved["diagnostics"][0]["line"] = 12
    a, b = state(1, last=FAILED), state(1, last=moved)
    assert A.dedup_key(a) == A.dedup_key(b)
    assert A.dedup_key(a) != A.dedup_key(state(1, last=VERIFIED))
    assert A.dedup_key(a) != A.dedup_key(state(1, files={"t.dfy": "0" * 64}, last=FAILED))
    assert len(A.dedup_key(a)) == 64


def test_value():
    assert A.value(state(1, last=VERIFIED)) == 1.0
    assert A.value(state(1, last=FAILED)) == pytest.approx(1 / 3)
    assert A.value(state(0)) == 0.0
    holes = dict(VERIFIED, holes=[{"line": 1}])
    assert A.value(state(1, last=holes)) == pytest.approx(1 / 3)


def test_build_index(tmp_path):
    d = tmp_path / "dafny" / "given" / "Q"
    d.mkdir(parents=True)
    (d / "L.dfy").write_text("module L {\n  lemma LemmaBound(i: nat, n: nat)\n  function F(x: int): int\n}\n")
    v = tmp_path / "verus" / "given" / "c" / "src"
    v.mkdir(parents=True)
    (v / "lib.rs").write_text("verus! {\npub proof fn lemma_add(a: nat)\n  {}\n}\n")
    idx = A.build_index(tmp_path)
    names = [e[0] for e in idx.entries]
    assert names == sorted(names) and set(names) == {"LemmaBound", "F", "lemma_add"}
    assert ("LemmaBound", "lemma LemmaBound(i: nat, n: nat)", "dafny/given/Q/L.dfy") in idx.entries
    assert idx.sha256 == A.build_index(tmp_path).sha256 and len(idx.sha256) == 64
    with pytest.raises(ValueError):
        A.build_index(tmp_path, ("Solutions/",))


class Ask:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def __call__(self, prompt, seed):
        self.calls.append((prompt, seed))
        return self.replies.pop(0)


def test_the_search_submits_typed_children_and_stops(tmp_path):
    d = tmp_path / "dafny" / "given" / "Q"
    d.mkdir(parents=True)
    (d / "L.dfy").write_text("module L {\n  lemma LemmaBound(i: nat, n: nat)\n}\n")
    ask = Ask([LOOP.replace("i + 1", "i + 2"),          # not a typed edit: rejected
               WITH_INV])                               # accepted
    agent = A.Agent(ask, [11, 12, 13], index=A.build_index(tmp_path))
    acts = agent.propose(state(0), ctx(), P.Budget(calls_left=8))
    assert acts == [P.Edit(path="t.dfy", old=LOOP, new=WITH_INV), P.Verify()]
    assert [s for _, s in ask.calls] == [11, 12]
    assert "Prove it." in ask.calls[0][0] and LOOP in ask.calls[0][0]
    turn = P.Turn(0, tuple(acts), ())
    done = agent.propose(state(1, {"t.dfy": P.text_sha256(WITH_INV)}, VERIFIED, [turn]), ctx(),
                         P.Budget(calls_left=6))
    assert done == [P.Stop(reason="done")]


def test_the_prompt_carries_retrieval_hints(tmp_path):
    d = tmp_path / "dafny" / "given" / "Q"
    d.mkdir(parents=True)
    (d / "L.dfy").write_text("module L {\n  lemma LemmaBound(i: nat, n: nat)\n  lemma Other()\n}\n")
    ask = Ask([WITH_INV, WITH_INV.replace("    invariant i <= n\n",
                                          "    invariant i <= n\n    invariant 0 <= i\n")])
    agent = A.Agent(ask, [1, 2, 3], index=A.build_index(tmp_path))
    first = agent.propose(state(0), ctx(), P.Budget(calls_left=8))
    turn = P.Turn(0, tuple(first), ())
    agent.propose(state(1, {"t.dfy": P.text_sha256(WITH_INV)}, FAILED, [turn]), ctx(),
                  P.Budget(calls_left=7))
    prompt = ask.calls[1][0]
    assert "lemma LemmaBound(i: nat, n: nat)" in prompt and "lemma Other()" not in prompt
    assert "loop invariant 7 may not hold" in prompt


def test_the_search_gives_up_within_its_budget():
    ask = Ask([LOOP, LOOP, LOOP])
    agent = A.Agent(ask, [1, 2, 3])
    assert agent.propose(state(0), ctx(), P.Budget(calls_left=2)) == [P.Stop(reason="give-up")]
    assert len(ask.calls) == 2
    spent = A.Agent(Ask([]), [1])
    assert spent.propose(state(0), ctx(), P.Budget(calls_left=0)) == [P.Stop(reason="give-up")]
