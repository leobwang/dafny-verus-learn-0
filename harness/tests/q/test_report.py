"""Q12's acceptance tests for harness/q/fvh_q/report.py (frozen; QPLAN §22.6).

They fail while H12py or H13py is a hole and pass on a correct file. The rows
are synthetic (no run of Lab 1 exists before its batch runner): small hand-written
tables whose cells, rates and discordant counts are written out below; the
statistics are checked against direct calls of the frozen core (fvh.stats)
with the same inputs, so a re-derived estimator that differs fails.

What they hold the tables to (design §11.1; QPLAN §22.6):
  - a cell is (task, repeat); an arm solves it when any of its attempts
    there succeeded; only the cells every arm has are paired;
  - truncations are counted per arm and stay failures in the table;
  - the comparison is paired, its interval is the bootstrap of the paired
    differences, Holm runs over the whole pre-registered family, and the
    McNemar line is per repeat.

Run: scripts/vcheck harness/q/fvh_q/report.py
     (or, from harness/: uv run pytest tests/q/test_report.py)
"""

import pytest

from fvh import stats
from fvh.records import RunRecord
from fvh_q import report as rp


def row(task, arm, repeat, ok, *, attempt=1, outcome=None, holes=0):
    verdict = "verified" if ok else "failed"
    rec = RunRecord(task, arm, attempt, "dafny", verdict, holes, 0 if ok else 1, 2 if ok else 0)
    return rp.LabRun(rec, repeat, outcome or verdict)


# Two repeats of four tasks; A1 has eight attempts per cell (some shown), A2 one.
ROWS = [
    # repeat 1
    row("t1", "A1", 1, False, attempt=1), row("t1", "A1", 1, True, attempt=2),
    row("t2", "A1", 1, False), row("t3", "A1", 1, True), row("t4", "A1", 1, False),
    row("t1", "A2", 1, True), row("t2", "A2", 1, True), row("t3", "A2", 1, False),
    row("t4", "A2", 1, False, outcome="truncated:rate-limit"),
    # repeat 2
    row("t1", "A1", 2, True), row("t2", "A1", 2, False), row("t3", "A1", 2, False),
    row("t4", "A1", 2, False, outcome="truncated:gate"),
    row("t1", "A2", 2, True), row("t2", "A2", 2, True), row("t3", "A2", 2, True),
    row("t4", "A2", 2, False),
    # an arm left out, and a cell only A1 has
    row("t1", "C", 1, True), row("t5", "A1", 1, True),
]
KEYS = (("t1", 1), ("t1", 2), ("t2", 1), ("t2", 2), ("t3", 1), ("t3", 2), ("t4", 1), ("t4", 2))
A1 = (True, True, False, False, True, False, False, False)
A2 = (True, True, True, True, False, True, False, False)


def table():
    return rp.paired_table(ROWS, ["A1", "A2"], excluded={"A1": 2, "Z": 5})


# --- H12 ----------------------------------------------------------------------------------


def test_cells_and_pairs():
    t = table()
    assert t.arms == ("A1", "A2")
    assert t.keys == KEYS
    assert t.solved == {"A1": A1, "A2": A2}
    assert t.unpaired == (("t5", 1),)


def test_truncations_and_exclusions():
    t = table()
    assert t.truncated == {"A1": 1, "A2": 1}
    assert t.excluded == {"A1": 2, "A2": 0}


def test_a_hole_is_not_a_success():
    rows = [row("t1", "A1", 1, True, holes=1), row("t1", "A2", 1, True)]
    rows[0] = rp.LabRun(RunRecord("t1", "A1", 1, "dafny", "verified", 1, 0, 2), 1, "verified")
    t = rp.paired_table(rows, ["A1", "A2"])
    assert t.solved == {"A1": (False,), "A2": (True,)}
    assert t.excluded == {"A1": 0, "A2": 0}


def test_other_arms_are_left_out():
    t = rp.paired_table(ROWS, ["A2", "C"])
    assert t.keys == (("t1", 1),) and t.solved == {"A2": (True,), "C": (True,)}
    assert len(t.unpaired) == 7


@pytest.mark.parametrize("arms", [[], ["A1", "A1"]])
def test_bad_arms(arms):
    with pytest.raises(ValueError):
        rp.paired_table(ROWS, arms)


# --- H13 ----------------------------------------------------------------------------------


FAMILY = [("A2", "A1"), ("A3", "A1")]


def table3():
    rows = list(ROWS)
    for (task, rep), ok in zip(KEYS, (True, False, False, False, True, True, False, True)):
        rows.append(row(task, "A3", rep, ok))
    return rp.paired_table(rows, ["A1", "A2", "A3"])


def test_rates_and_difference():
    c = rp.compare(table3(), "A2", "A1", family=FAMILY, seed=11)
    assert (c.a, c.b, c.n) == ("A2", "A1", 8)
    assert c.rate_a == pytest.approx(5 / 8) and c.rate_b == pytest.approx(3 / 8)
    assert c.diff == pytest.approx(2 / 8)


def test_interval_is_the_paired_bootstrap():
    c = rp.compare(table3(), "A2", "A1", family=FAMILY, seed=11)
    diffs = [float(x) - float(y) for x, y in zip(A2, A1)]
    assert c.interval == stats.bootstrap_ci(diffs, seed=11)


def test_p_and_holm_over_the_family():
    t = table3()
    c = rp.compare(t, "A2", "A1", family=FAMILY, seed=5)
    a3 = (True, False, False, False, True, True, False, True)
    f = [float(v) for v in A1]
    p21 = stats.permutation_test([float(v) for v in A2], f, paired=True, seed=5)
    p31 = stats.permutation_test([float(v) for v in a3], f, paired=True, seed=5)
    assert c.p == p21
    assert c.holm_reject == stats.holm([p21, p31])[0]
    c3 = rp.compare(t, "A3", "A1", family=FAMILY, seed=5)
    assert c3.p == p31 and c3.holm_reject == stats.holm([p21, p31])[1]


def test_mcnemar_per_repeat():
    c = rp.compare(table3(), "A2", "A1", family=FAMILY, seed=1)
    # repeat 1: A2 only t2 (b=1), A1 only t3 (c=1); repeat 2: A2 only t2, t3 (b=2), none (c=0)
    assert c.mcnemar_by_repeat == {1: stats.mcnemar(1, 1), 2: stats.mcnemar(2, 0)}


def test_order_of_the_arms_matters():
    c = rp.compare(table3(), "A1", "A2", family=[("A1", "A2")], seed=1)
    assert c.diff == pytest.approx(-2 / 8)
    assert c.mcnemar_by_repeat == {1: stats.mcnemar(1, 1), 2: stats.mcnemar(0, 2)}


def test_same_seed_same_result():
    t = table3()
    assert rp.compare(t, "A2", "A1", family=FAMILY, seed=3) == \
        rp.compare(t, "A2", "A1", family=FAMILY, seed=3)


@pytest.mark.parametrize("a, b, family", [
    ("A2", "A9", [("A2", "A9")]),
    ("A2", "A1", [("A3", "A1")]),
])
def test_compare_refuses(a, b, family):
    with pytest.raises(ValueError):
        rp.compare(table3(), a, b, family=family, seed=1)


def test_compare_refuses_an_empty_table():
    t = rp.paired_table([row("t1", "A1", 1, True), row("t2", "A2", 1, True)], ["A1", "A2"])
    with pytest.raises(ValueError):
        rp.compare(t, "A1", "A2", family=[("A1", "A2")], seed=1)
