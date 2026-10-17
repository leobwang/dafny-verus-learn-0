"""Frozen acceptance for R05's two Python items; measurements are fixtures.

No solver is invoked. The actual ten-run experiment is learner work, separate
from this parser/statistical-composition contract.
"""
import json
import math
import statistics
import pytest
from fvh import stats
from fvh_r.variance import TimingRun, Summary, runs_from_log, variance_summary

def write_log(tmp_path, lines):
    path = tmp_path / "runs.jsonl"
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path

def row(**changes):
    doc = {"wall_s": 1.25, "resource_count": 29, "verdict": "verified", "lang": "dafny"}
    doc.update(changes)
    return json.dumps(doc)

def test_rows_preserve_order_verdict_null_and_extra_fields(tmp_path):
    path = write_log(tmp_path, [row(), row(wall_s=0, resource_count=None, verdict="failed"), row(wall_s=2.5, resource_count=4.5, verdict="inconclusive")])
    assert runs_from_log(path) == [TimingRun(1.25,29.0,"verified"),TimingRun(0.0,None,"failed"),TimingRun(2.5,4.5,"inconclusive")]

def test_empty_and_missing_file(tmp_path):
    assert runs_from_log(write_log(tmp_path, [])) == []
    with pytest.raises(OSError):
        runs_from_log(tmp_path / "absent")

@pytest.mark.parametrize("bad", ["", "not-json", "[]", "null", "{}", row(wall_s=True), row(wall_s=-1), row(wall_s=None), row(wall_s="2"), row(wall_s=float("nan")), row(wall_s=float("inf")), row(resource_count=False), row(resource_count=-1), row(resource_count="9"), row(resource_count=float("nan")), row(verdict="ok"), row(verdict=[]), json.dumps({"wall_s":1,"verdict":"verified"})])
def test_malformed_line_fails_with_line_number_not_partial_results(tmp_path,bad):
    with pytest.raises(ValueError, match=r"line 2\b"):
        runs_from_log(write_log(tmp_path,[row(),bad,row()]))

@pytest.mark.parametrize("verdict", ["verified","failed","inconclusive","refused","killed(memory)","error"])
def test_every_wrapper_verdict_is_retained(tmp_path,verdict):
    assert runs_from_log(write_log(tmp_path,[row(verdict=verdict)]))[0].verdict == verdict

def test_summary_composes_frozen_bootstrap_and_sample_statistics(monkeypatch):
    calls=[]
    def capture(values, statistic=statistics.fmean, *, seed):
        calls.append((list(values),statistic,seed))
        return (1.25,3.75)
    monkeypatch.setattr(stats,"bootstrap_ci",capture)
    runs=[TimingRun(1,10,"verified"),TimingRun(3,20,"failed"),TimingRun(5,30,"verified")]
    summary=variance_summary(runs,"wall_s",seed=271)
    assert summary == Summary(3,3.0,2/3,(1.25,3.75))
    assert calls == [([1.0,3.0,5.0],statistics.fmean,271)]
    other=variance_summary(runs,"resource_count",seed=13)
    assert other.n==3 and other.mean==20 and other.cv==0.5
    assert calls[-1] == ([10.0,20.0,30.0],statistics.fmean,13)

def test_real_bootstrap_matches_core_and_is_seeded():
    runs=[TimingRun(x,100,"verified") for x in (1.,2.,4.,5.,9.)]
    values=[r.wall_s for r in runs]
    summary=variance_summary(runs,"wall_s",seed=71)
    assert summary.interval == stats.bootstrap_ci(values,statistics.fmean,seed=71)
    assert summary == variance_summary(runs,"wall_s",seed=71)
    assert summary.mean == statistics.fmean(values)
    assert summary.cv == statistics.stdev(values)/summary.mean

def test_zero_and_constant_samples():
    assert variance_summary([TimingRun(0,8,"verified")]*2,"wall_s",seed=1)==Summary(2,0.,0.,(0.,0.))
    assert variance_summary([TimingRun(4,8,"verified")]*3,"resource_count",seed=1)==Summary(3,8.,0.,(8.,8.))

@pytest.mark.parametrize("runs,field", [([],"wall_s"),([TimingRun(1,2,"verified")],"wall_s"),([TimingRun(1,2,"verified")]*2,"verdict"),([TimingRun(1,None,"verified")]*2,"resource_count"),([TimingRun(-1,2,"verified")]*2,"wall_s"),([TimingRun(float("inf"),2,"verified")]*2,"wall_s"),([TimingRun(float("nan"),2,"verified")]*2,"wall_s"),([TimingRun(True,2,"verified")]*2,"wall_s"),([TimingRun("1",2,"verified")]*2,"wall_s")])
def test_summary_rejects_insufficient_unknown_or_invalid_measurements(runs,field):
    with pytest.raises(ValueError):
        variance_summary(runs,field,seed=1)
