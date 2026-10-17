"""Q06's acceptance tests for harness/q/fvh_q/q06_stats.py (frozen; QPLAN §11.2, §11.8).

They fail while any of H5py, H6py and H7py is a hole and pass on a correct
file. Expected values are constants worked by hand or values of fvh.stats
itself on counts written out here; nothing below re-derives the functions under
test. The H6 and H7 tests also check composition: statistics code lives only in
the core (design §9.2 rule 4), so they replace fvh.stats.wilson_interval and
fvh.stats.pass_at_k (and any name the learner module bound to them) with
recording wrappers and require the call.

Run: scripts/vcheck harness/q/fvh_q/q06_stats.py
     (or uv run --directory harness pytest tests/q/test_q06_stats.py)
"""

import inspect
from pathlib import Path

import pytest

import fvh.stats as fstats
from fvh import holes
from fvh.records import RunRecord
from fvh_q import q06_stats as q


def run(task, arm, attempt, ok, holes_=0, lang="dafny"):
    """A run record; ok=True is a verified run, ok=False a failed one."""
    return RunRecord(task, arm, attempt, lang, "verified" if ok else "failed", holes_,
                     0 if ok else 2, 5 if ok else 3)


def record_calls(monkeypatch, name):
    """Replace fvh.stats.<name>, and every name q06_stats bound to it, with a
    wrapper that records its bound arguments and calls the original."""
    original = getattr(fstats, name)
    sig = inspect.signature(original)
    calls = []

    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        calls.append(dict(bound.arguments))
        return original(*args, **kwargs)

    monkeypatch.setattr(fstats, name, wrapper)
    for attr, value in list(vars(q).items()):
        if value is original:
            monkeypatch.setattr(q, attr, wrapper)
    return calls


# --- the file --------------------------------------------------------------------------

def test_no_hole_is_left():
    source = Path(q.__file__).read_text(encoding="utf-8")
    assert holes.count_holes(source) == []


# --- H5: record_from_vcheck ------------------------------------------------------------

def doc(**over):
    base = {"lang": "dafny", "target": "dafny/Q/Q98_Demo/core", "exit_code": 0,
            "verdict": "verified", "stage": "verify", "verified_count": 31,
            "count_unit": "tasks", "holes": [], "findings": [],
            "diagnostics": [{"file": "dafny/Q/Q98_Demo/core/Demo.dfy", "line": 4, "col": 3,
                             "severity": "warning", "message": "a warning", "code": ""}],
            "per_symbol": {}, "raw_dir": "/tmp/dvl-0/runs/x", "cmd": ["dafny", "verify"]}
    base.update(over)
    return base


HOLE = {"file": "f.rs", "line": 9, "col": 5, "kind": "proof-note", "label": "Q98.H1v"}


def diag(severity):
    return {"file": "f.rs", "line": 2, "col": 1, "severity": severity, "message": "m", "code": ""}


def test_h5_a_verified_document():
    r = q.record_from_vcheck(doc(), "Q98.H1d", "learner", 1)
    assert isinstance(r, RunRecord)
    assert r == RunRecord("Q98.H1d", "learner", 1, "dafny", "verified", 0, 0, 31)
    assert r.success


def test_h5_a_failed_document_counts_its_error_diagnostics_and_holes():
    d = doc(lang="verus", verdict="failed", exit_code=1, verified_count=7, holes=[HOLE, HOLE],
            diagnostics=[diag("error"), diag("related"), diag("error"), diag("warning"),
                         diag("error"), diag("info")])
    r = q.record_from_vcheck(d, "lemma_x", "agent", 3)
    assert r == RunRecord("lemma_x", "agent", 3, "verus", "failed", 2, 3, 7)
    assert not r.success


def test_h5_a_verified_run_with_holes_is_not_a_success():
    r = q.record_from_vcheck(doc(holes=[HOLE]), "t", "learner", 2)
    assert (r.verdict, r.holes, r.success) == ("verified", 1, False)


def test_h5_a_document_without_a_count():
    d = doc(verdict="refused", stage="cli", exit_code=None, verified_count=None, diagnostics=[])
    r = q.record_from_vcheck(d, "t", "learner", 1)
    assert (r.verdict, r.verified_count, r.errors) == ("refused", 0, 0)


# --- H6: pass_rate_ci ------------------------------------------------------------------

# Arm A, six tasks. First attempts: t1 ok, t2 fail, t3 verified with a hole (no success),
# t4 ok, t5 fail, t6 ok: 3 successes of 6. Later attempts and arm B must not count;
# t2's and t5's second attempts sit before their first ones.
ARM_RECORDS = [
    run("t2", "A", 2, True), run("t1", "A", 1, True), run("t2", "A", 1, False),
    run("t3", "A", 1, True, holes_=1), run("t1", "B", 1, False), run("t4", "A", 1, True),
    run("t5", "A", 2, True), run("t5", "A", 1, False), run("t6", "A", 1, True),
    run("t6", "B", 1, True), run("t3", "A", 2, True), run("t7", "B", 1, True),
]


def test_h6_counts_each_task_once_through_its_first_attempt():
    s, n, interval = q.pass_rate_ci(ARM_RECORDS, "A")
    assert (s, n) == (3, 6)
    assert interval == fstats.wilson_interval(3, 6, 0.95)


def test_h6_other_arm_and_other_confidence():
    s, n, interval = q.pass_rate_ci(ARM_RECORDS, "B", 0.8)
    assert (s, n) == (2, 3)
    assert interval == fstats.wilson_interval(2, 3, 0.8)


def test_h6_composes_wilson_interval(monkeypatch):
    calls = record_calls(monkeypatch, "wilson_interval")
    s, n, interval = q.pass_rate_ci(ARM_RECORDS, "A", 0.9)
    assert calls, "pass_rate_ci must call fvh.stats.wilson_interval"
    assert {"successes": 3, "n": 6, "confidence": 0.9} in calls
    assert interval == fstats.wilson_interval(3, 6, 0.9)


@pytest.mark.parametrize("records,arm", [([], "A"), (ARM_RECORDS, "C")])
def test_h6_an_arm_with_no_records_raises(records, arm):
    with pytest.raises(ValueError):
        q.pass_rate_ci(records, arm)


# --- H7: pass_at_k_by_task -------------------------------------------------------------

# Arm A: u1 4 samples, 1 success; u2 4 samples, none (one verified with a hole);
# u3 4 samples, all successes; u4 3 samples, 2 successes. Arm B is noise.
SAMPLES = (
    [run("u1", "A", i, i == 2) for i in range(1, 5)]
    + [run("u2", "A", 1, True, holes_=2)] + [run("u2", "A", i, False) for i in range(2, 5)]
    + [run("u3", "A", i, True) for i in range(1, 5)]
    + [run("u4", "A", 1, True), run("u4", "A", 2, False), run("u4", "A", 3, True)]
    + [run("u1", "B", 1, True), run("u9", "B", 1, False)]
)


def test_h7_the_mean_of_the_per_task_estimates():
    # k = 2: u1 1 - C(3,2)/C(4,2) = 0.5; u2 0; u3 1; u4 1 - C(1,2)/C(3,2) = 1: mean 0.625
    assert q.pass_at_k_by_task(SAMPLES, "A", 2) == pytest.approx(0.625, abs=1e-12)


def test_h7_k_one_is_the_mean_per_task_success_rate():
    # k = 1: 1/4, 0, 1, 2/3
    want = (0.25 + 0.0 + 1.0 + 2 / 3) / 4
    assert q.pass_at_k_by_task(SAMPLES, "A", 1) == pytest.approx(want, abs=1e-12)


def test_h7_composes_pass_at_k(monkeypatch):
    calls = record_calls(monkeypatch, "pass_at_k")
    got = q.pass_at_k_by_task(SAMPLES, "A", 3)
    assert calls, "pass_at_k_by_task must call fvh.stats.pass_at_k"
    seen = sorted((c["n"], c["c"], c["k"]) for c in calls)
    assert seen == [(3, 2, 3), (4, 0, 3), (4, 1, 3), (4, 4, 3)]
    want = (fstats.pass_at_k(4, 1, 3) + fstats.pass_at_k(4, 0, 3) + fstats.pass_at_k(4, 4, 3)
            + fstats.pass_at_k(3, 2, 3)) / 4
    assert got == pytest.approx(want, abs=1e-12)


def test_h7_other_arm():
    # B: u1 one success of one, u9 none of one: (1 + 0) / 2
    assert q.pass_at_k_by_task(SAMPLES, "B", 1) == pytest.approx(0.5, abs=1e-12)


@pytest.mark.parametrize("records,arm", [([], "A"), (SAMPLES, "C")])
def test_h7_an_arm_with_no_records_raises(records, arm):
    with pytest.raises(ValueError):
        q.pass_at_k_by_task(records, arm, 1)
