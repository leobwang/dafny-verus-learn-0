"""The frozen core's own tests: fvh.runlog (DV4-PLAN §3.6, §9; Δ149, Δ150):
RunMeta's validation and round trip, the outcome-to-RunRecord mapping of §3.6,
split's records, exclusions and rows, the deterministic inputs archive, the
patch, and the 5 MB cap finding."""

import gzip
import io
import json
import tarfile

import pytest

from fvh import runlog as L
from fvh.records import VERDICTS, RunRecord

DOC = {"verdict": "failed", "holes": [{"line": 1}, {"line": 2}], "verified_count": 3,
       "diagnostics": [{"severity": "error"}, {"severity": "related"}, {"severity": "error"}]}


def meta(**kw):
    base = dict(run_id="20261011T000000Z-A1-t1-1-1", module="Q98", arm="A1", task_id="t1",
                lang="dafny", attempt=1, repeat=1, mode="harness-executed", backend="mock",
                outcome="failed", verify=DOC)
    base.update(kw)
    return L.RunMeta(**base)


def test_round_trip(tmp_path):
    m = meta(findings=["ctx-saturated"], usage={"calls": 3})
    L.write_meta(tmp_path, m)
    assert L.load_meta(tmp_path) == m and L.load_meta(tmp_path / "run.json") == m
    obj = json.loads((tmp_path / "run.json").read_text())
    obj["extra"] = 1
    (tmp_path / "run.json").write_text(json.dumps(obj))
    with pytest.raises(ValueError, match="RunMeta's fields"):
        L.load_meta(tmp_path)


@pytest.mark.parametrize("change", [
    {"outcome": "lost"}, {"outcome": "truncated:sunspots"}, {"mode": "batch"},
    {"attempt": 0}, {"repeat": True}, {"run_id": "a/b"}, {"ended_by": "boredom"},
    {"inputs_sha256": "abc"}, {"verify": "doc"}, {"findings": [1]}, {"arm": ""},
])
def test_validation(change):
    with pytest.raises((TypeError, ValueError)):
        meta(**change)


@pytest.mark.parametrize("v", VERDICTS)
def test_a_verdict_maps_to_itself_with_the_counts(v):
    r = L.to_run_record(meta(outcome=v))
    assert r == RunRecord("t1", "A1", 1, "dafny", v, 2, 2, 3)


def test_malformed_and_truncated():
    assert L.to_run_record(meta(outcome="malformed")) == RunRecord("t1", "A1", 1, "dafny",
                                                                   "error", 0, 1, 0)
    r = L.to_run_record(meta(outcome="truncated:rate-limit"))
    assert (r.verdict, r.holes, r.errors) == ("inconclusive", 2, 2)
    r = L.to_run_record(meta(outcome="truncated:cli-crash", verify=None))
    assert (r.verdict, r.holes, r.errors, r.verified_count) == ("inconclusive", 0, 0, 0)


@pytest.mark.parametrize("o", ["infra-failed", "apparatus-mismatch", "replay-diverged",
                               "planned", "deferred"])
def test_unscored_outcomes_have_no_record(o):
    assert L.to_run_record(meta(outcome=o)) is None and not L.scored(o)


def test_split():
    ms = [meta(outcome="verified", repeat=1), meta(outcome="infra-failed"),
          meta(outcome="truncated:auth", arm="A2", repeat=2),
          meta(outcome="apparatus-mismatch", arm="A2"), meta(outcome="infra-failed"),
          meta(outcome="deferred"), meta(outcome="planned")]
    s = L.split(ms)
    records, excluded, rows = s
    assert [r.verdict for r in records] == ["verified", "inconclusive"]
    assert excluded == {"A1": {"infra-failed": 2}, "A2": {"apparatus-mismatch": 1}}
    assert s.excluded_counts() == {"A1": 2, "A2": 1}
    assert [(x.repeat, x.outcome) for x in rows] == [(1, "verified"), (2, "truncated:auth")]
    assert rows[0].record is records[0]


def test_inputs_are_deterministic_and_checked(tmp_path):
    files = {"b/x.dfy": b"two\n", "a.dfy": b"one\n"}
    t1 = L.write_inputs(tmp_path / "r1", files)
    t2 = L.write_inputs(tmp_path / "r2", dict(reversed(list(files.items()))))
    assert t1 == t2 == L.inputs_tree_sha256(files)
    assert (tmp_path / "r1" / "inputs.tar.gz").read_bytes() == \
        (tmp_path / "r2" / "inputs.tar.gz").read_bytes()
    assert L.read_inputs(tmp_path / "r1") == files
    (tmp_path / "r1" / "inputs.sha256").write_text("0" * 64 + "  a.dfy\n")
    with pytest.raises(ValueError, match="does not match"):
        L.read_inputs(tmp_path / "r1")


def test_inputs_refuse_links(tmp_path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo("evil")
        info.type, info.linkname = tarfile.SYMTYPE, "/etc/passwd"
        tar.addfile(info)
    (tmp_path / "inputs.tar.gz").write_bytes(gzip.compress(buf.getvalue()))
    (tmp_path / "inputs.sha256").write_text("")
    with pytest.raises(ValueError, match="refused member"):
        L.read_inputs(tmp_path)


def test_patch_and_cap(tmp_path):
    n = L.write_patch(tmp_path, {"a.dfy": "x\ny\n", "gone.dfy": "z\n"},
                      {"a.dfy": "x\nY\n", "new.dfy": "n"})
    text = (tmp_path / "patch.diff").read_text()
    assert "--- a/a.dfy" in text and "+Y" in text and "+++ /dev/null" in text
    assert "\\ No newline at end of file" in text and n == text.count("\n")
    assert L.cap_finding(tmp_path) is None
    (tmp_path / "transcript.jsonl.gz").write_bytes(b"\0" * (L.CAP_BYTES + 1))
    assert L.cap_finding(tmp_path).startswith("over-cap:")


def test_run_ids_and_dirs(tmp_path):
    rid = L.new_run_id("A1/t1/1/1", now=0)
    assert rid == "19700101T000000Z-A1-t1-1-1"
    base = tmp_path / "research" / "runs" / "Q98"
    L.write_meta(base / rid, meta(run_id=rid))
    (base / "stray").mkdir()
    assert L.run_dirs(tmp_path, "Q98") == [base / rid]
    assert set(L.RUN_FILES) >= {"run.json", "actions.jsonl", "verify.json", "inputs.tar.gz"}
