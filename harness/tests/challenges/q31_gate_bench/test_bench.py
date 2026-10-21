"""Q31's acceptance tests for agents/q31_gate_bench/bench.py (frozen; QPLAN §33.1, Δ406).

They fail while any of Q31.H9py-H13py is a hole and pass on a correct file. The run
records are invented here with fvh.runlog's own writers (no model, no solver): two arms
on four tasks, two repeats each, one infra-failed run that must not count. Expected
numbers are written out by hand; the intervals come from fvh.stats, the core every
estimator composes.

Run: scripts/vcheck agents/q31_gate_bench/bench.py
"""

import pytest

import fvh.stats as fstats
from fvh import runlog
from q31_gate_bench import bench as b

# (arm, task, repeat, outcome, calls)
RUNS = [
    ("one", "t1", 1, "verified", 1), ("one", "t1", 2, "verified", 1),
    ("one", "t2", 1, "failed", 1), ("one", "t2", 2, "verified", 1),
    ("one", "t3", 1, "failed", 1), ("one", "t3", 2, "failed", 1),
    ("one", "t4", 1, "failed", 1), ("one", "t4", 2, "failed", 1),
    ("par", "t1", 1, "verified", 3), ("par", "t1", 2, "verified", 2),
    ("par", "t2", 1, "failed", 4), ("par", "t2", 2, "failed", 4),
    ("par", "t3", 1, "verified", 2), ("par", "t3", 2, "failed", 4),
    ("par", "t4", 1, "failed", 4), ("par", "t4", 2, "failed", 4),
    ("par", "t4", 3, "infra-failed", 0),
]
STRATA = {"t1": "course-local", "t2": "course-local", "t3": "public", "t4": "public"}


@pytest.fixture
def root(tmp_path):
    for k, (arm, task, rep, outcome, calls) in enumerate(RUNS):
        d = tmp_path / "research" / "runs" / "Q31" / f"r{k:02d}"
        d.mkdir(parents=True)
        runlog.write_meta(d, runlog.RunMeta(
            run_id=f"r{k:02d}", module="Q31", arm=arm, task_id=task, lang="dafny", attempt=1,
            repeat=rep, mode="policy", backend="qwen", outcome=outcome,
            usage={"calls": calls, "tokens": 100 * calls, "turns": calls, "wall_s": 10.0 * calls,
                   "gpu_s": 9.0 * calls}))
    return tmp_path


def test_load_runs_keeps_scored_runs_in_order(root):
    rows = b.load_runs(root, "Q31", strata=STRATA)
    assert len(rows) == 16                                      # the infra-failed run is out
    assert [(r.arm, r.task, r.repeat) for r in rows][:3] == [("one", "t1", 1), ("one", "t1", 2),
                                                            ("one", "t2", 1)]
    assert rows[0].solved and not rows[2].solved and rows[0].stratum == "course-local"
    assert rows[0].cost == {"calls": 1.0, "tokens": 100.0, "wall_s": 10.0, "gpu_s": 9.0}
    assert {r.arm for r in b.load_runs(root, "Q31", arms=("par",))} == {"par"}
    assert {r.stratum for r in b.load_runs(root, "Q31")} == {"unknown"}


def test_pass_at_k(root):
    rows = b.load_runs(root, "Q31", strata=STRATA)
    t = b.pass_at_k_table(rows, (1,))
    est, ci = t.rows[("one", "course-local", "dafny", 1)]
    assert est == pytest.approx(0.75)                           # t1 2/2, t2 1/2
    assert ci == fstats.bootstrap_ci([1.0, 0.5], seed=0)
    assert t.rows[("par", "public", "dafny", 1)][0] == pytest.approx(0.25)
    assert t.n_tasks[("one", "course-local", "dafny", 1)] == 2
    with pytest.raises(ValueError):
        b.pass_at_k_table(rows, (2,))                            # 2 samples < 2k = 4
    single = [r for r in rows if r.repeat == 1]
    est, ci = b.pass_at_k_table(single, (1,)).rows[("par", "course-local", "dafny", 1)]
    assert est == pytest.approx(0.5) and ci == fstats.wilson_interval(1, 2)


def test_cost_curve(root):
    rows = b.load_runs(root, "Q31", strata=STRATA)
    c = b.cost_curve(rows, "calls", (1, 3))
    assert c.axis == "calls"
    (b1, s1, ci1), (b3, s3, _) = c.points["par"]
    assert (b1, s1, s3) == (1, 0.0, pytest.approx(3 / 8))
    one = c.points["one"][0]
    assert one[1] == pytest.approx(3 / 8)
    assert one[2] == fstats.bootstrap_ci([1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0], seed=0)
    with pytest.raises(ValueError):
        b.cost_curve(rows, "dollars", (1,))


def test_paired_report(root):
    rows = b.load_runs(root, "Q31", strata=STRATA)
    p = b.paired_report(rows, "one", "par", family=(0.001,))
    assert (p.n, p.discordant) == (4, (0, 1))                   # repeat 1: one t1; par t1, t3
    assert p.p_value == fstats.mcnemar(0, 1)
    assert p.rejected == fstats.holm([fstats.mcnemar(0, 1), 0.001])[0]
    assert p.mde == fstats.mde_two_proportions(4, 0.5, paired=True)
    with pytest.raises(ValueError):
        b.paired_report(rows, "one", "nobody")


def test_render_is_deterministic(root):
    rows = b.load_runs(root, "Q31", strata=STRATA)
    tabs = [b.pass_at_k_table(rows, (1,)), b.cost_curve(rows, "calls", (1, 3)),
            b.paired_report(rows, "one", "par")]
    text = b.render(tabs)
    assert text == b.render(list(reversed(tabs)))
    lines = text.splitlines()
    assert lines == sorted(lines)
    assert "pass\tone\tcourse-local\tdafny\t1\t0.7500\t" in text
    assert sum(1 for x in lines if x.startswith("curve\t")) == 4
    assert sum(1 for x in lines if x.startswith("paired\t")) == 1
    with pytest.raises(TypeError):
        b.render([object()])
