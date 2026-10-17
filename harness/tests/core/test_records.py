"""The frozen core's own tests: fvh.records (QPLAN §11.8).

The calibration rows below are written in scripts/firsttry.py's format (five
tab-separated columns, `#` comment lines, the first row of an item wins);
tests/harness_adapter/ checks the same format against the writer itself.
"""

import dataclasses
import json

import pytest

from fvh import records
from fvh.records import CalibRow, RunRecord


def rec(task, arm="A", attempt=1, verdict="verified", holes=0, errors=0, count=4, lang="dafny"):
    return RunRecord(task, arm, attempt, lang, verdict, holes, errors, count)


# --- RunRecord -------------------------------------------------------------------------

def test_success_is_verified_with_no_hole():
    assert rec("t").success
    assert not rec("t", holes=1).success
    assert not rec("t", verdict="failed", errors=2).success
    assert not rec("t", verdict="inconclusive").success


def test_run_record_is_frozen():
    r = rec("t")
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.holes = 3


@pytest.mark.parametrize("change,exc", [
    (dict(task_id=""), ValueError), (dict(arm=""), ValueError), (dict(attempt=0), ValueError),
    (dict(holes=-1), ValueError), (dict(errors=-2), ValueError),
    (dict(verified_count=-1), ValueError), (dict(verdict="pass"), ValueError),
    (dict(attempt=1.0), TypeError), (dict(holes=True), TypeError), (dict(lang=None), TypeError),
])
def test_run_record_rejects_bad_fields(change, exc):
    base = dict(task_id="t", arm="A", attempt=1, lang="verus", verdict="verified", holes=0,
                errors=0, verified_count=2)
    with pytest.raises(exc):
        RunRecord(**{**base, **change})


def test_every_tool_verdict_is_accepted():
    for v in records.VERDICTS:
        assert rec("t", verdict=v).verdict == v


# --- JSON Lines ------------------------------------------------------------------------

def test_dump_and_load_round_trip(tmp_path):
    rs = [rec("t1"), rec("t2", arm="B", attempt=2, verdict="failed", errors=3, count=0),
          rec("t3", verdict="killed(memory)", lang="verus")]
    path = tmp_path / "runs.jsonl"
    records.dump_jsonl(rs, path)
    assert records.load_jsonl(path) == rs
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3 and json.loads(lines[0])["task_id"] == "t1"


def test_load_jsonl_skips_blank_lines(tmp_path):
    path = tmp_path / "runs.jsonl"
    obj = dataclasses.asdict(rec("t1"))
    path.write_text("\n" + json.dumps(obj) + "\n\n", encoding="utf-8")
    assert records.load_jsonl(path) == [rec("t1")]


@pytest.mark.parametrize("line", [
    "not json",
    "[1, 2]",
    json.dumps({"task_id": "t"}),
    json.dumps({**dataclasses.asdict(rec("t")), "extra": 1}),
    json.dumps({**dataclasses.asdict(rec("t")), "attempt": 0}),
])
def test_load_jsonl_names_the_bad_line(tmp_path, line):
    path = tmp_path / "runs.jsonl"
    path.write_text(json.dumps(dataclasses.asdict(rec("ok"))) + "\n" + line + "\n",
                    encoding="utf-8")
    with pytest.raises(ValueError, match=r":2: "):
        records.load_jsonl(path)


def test_dump_jsonl_writes_only_run_records(tmp_path):
    with pytest.raises(TypeError):
        records.dump_jsonl([{"task_id": "t"}], tmp_path / "x.jsonl")


# --- first_attempts --------------------------------------------------------------------

def test_first_attempts_keeps_attempt_one_per_task_and_arm_in_input_order():
    rs = [rec("t2", attempt=2), rec("t1"), rec("t2"), rec("t1", arm="B"), rec("t1", attempt=3),
          rec("t3", attempt=2), rec("t1", verdict="failed")]
    got = records.first_attempts(rs)
    assert got == [rec("t1"), rec("t2"), rec("t1", arm="B")]


def test_first_attempts_of_nothing_is_nothing():
    assert records.first_attempts([]) == []


# --- calibration files -----------------------------------------------------------------

CALIB = ("# instructor/calib/Q05.tsv\n"
         "Q05.P1dv\tpredict\tpass\t2026-10-01\t" + "a" * 64 + "\n"
         "Q05.P2d\tpredict\tfail\t2026-10-01\t" + "b" * 64 + "\n"
         "\n"
         "Q05.P3v\tobserved\tpass\t2026-10-02\t" + "c" * 64 + "\n"
         "Q05.X1d\texit\tfail\t2026-10-03\t" + "d" * 64 + "\n"
         "Q05.P2d\tpredict\tpass\t2026-10-04\t" + "e" * 64 + "\n"
         "Q05.T1v\tpredict\tpass\t2026-10-01\t" + "f" * 64 + "\n")


def test_load_calib_reads_firsttry_rows_and_keeps_each_items_first(tmp_path):
    path = tmp_path / "Q05.tsv"
    path.write_text(CALIB, encoding="utf-8")
    rows = records.load_calib(path)
    assert [r.item for r in rows] == ["Q05.P1dv", "Q05.P2d", "Q05.P3v", "Q05.X1d", "Q05.T1v"]
    assert rows[1] == CalibRow("Q05.P2d", "predict", "fail", "2026-10-01", "b" * 64)


@pytest.mark.parametrize("line", [
    "Q05.P1dv\tpredict\tpass\t2026-10-01",
    "Q05.P1dv\tpredict\tpass\t2026-10-01\th\textra",
    "Q5.P1dv\tpredict\tpass\t2026-10-01\th",
    "Q05.P1dv\tguess\tpass\t2026-10-01\th",
    "Q05.P1dv\tpredict\tok\t2026-10-01\th",
])
def test_load_calib_names_the_bad_line(tmp_path, line):
    path = tmp_path / "bad.tsv"
    path.write_text("# header\n" + line + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r":2: "):
        records.load_calib(path)


def test_calib_records_bridges_predict_rows_and_counts_the_rest(tmp_path):
    path = tmp_path / "Q05.tsv"
    path.write_text(CALIB, encoding="utf-8")
    got, excluded = records.calib_records(records.load_calib(path), "first-try")
    assert excluded == 2
    assert got == [
        RunRecord("Q05.P1dv", "first-try", 1, "dv", "verified", 0, 0, 0),
        RunRecord("Q05.P2d", "first-try", 1, "d", "failed", 0, 1, 0),
        RunRecord("Q05.T1v", "first-try", 1, "v", "verified", 0, 0, 0),
    ]
    assert [r.success for r in got] == [True, False, True]


def test_calib_records_of_a_python_item_and_of_nothing():
    rows = [CalibRow("Q07.P2py", "predict", "fail", "2026-10-09", "0" * 64)]
    got, excluded = records.calib_records(rows, "me")
    assert (got[0].lang, got[0].verdict, excluded) == ("py", "failed", 0)
    assert records.calib_records([], "me") == ([], 0)


def test_calib_records_needs_an_arm():
    with pytest.raises(ValueError):
        records.calib_records([], "")
