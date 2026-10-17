"""Q18's acceptance tests for harness/q/fvh_q/gate/gate_v2.py (frozen; QPLAN §28.4).

They fail while any of H3py-H7py is a hole and pass on a correct file. No
solver runs here: the instruments' results on the fixture deliveries of
harness/tests/q/fixtures/q18/ (three planted cheats, K1-K3, and four
controls, C1-C4) are replayed from what the author recorded under
fixtures/q18/rec/ (fvh.tools.ReplayRunner; results only, never a label), and
the option scan reads the fixtures' own files. Expected verdicts are written
out below, never re-derived from the functions under test.

What they hold the gate to (QPLAN §28.4; design §11.2; spec §5.6):
  - the option scan runs before any instrument and names every refused
    option and build-tool file;
  - the gate's document stands for a run of the whole crate only when its
    own fields say so: the command it ran, the wrapper's completeness
    messages, the pinned counts; a record a delivery brings proves nothing;
  - the seed sweep is one run of the pinned seed-rerun instrument, and a
    sweep that moved is a FAIL;
  - every planted cheat gets FAIL; every control the mechanical PASS with its
    undecided grader-only classes; a delivery is judged from its files and
    instrument results alone (a neutral id changes nothing);
  - every instrument runs through `fvh.tools.run` (replaced here by a
    recording stub), once, and a killed run is a FAIL;
  - `fp_report` reads the labels, counts false positives on the controls and
    takes its interval from fvh.stats.

Run: scripts/vcheck harness/q/fvh_q/gate/gate_v2.py
     (or, from harness/: uv run pytest tests/q/gate/test_gate_v2.py)
"""

import copy
import dataclasses
import inspect
from pathlib import Path

import pytest

import fvh.stats as fstats
from fvh import holes, tools
from fvh.tools import ReplayRunner, ToolResult
from fvh.verdicts import FAIL, GRADER_ONLY, PASS
from fvh_q.gate import gate_v2 as g

HERE = Path(__file__).resolve()
FIX = HERE.parents[1] / "fixtures" / "q18"            # harness/tests/q/fixtures/q18
REPLAY = ReplayRunner(FIX / "rec")
REAL_RUN = tools.run
BASE = "harness/tests/q/fixtures/q18"

# (id, lang, target, files, min_verified, symbols, kind, X class): the fixture
# set, as fixtures/q18/set.toml writes it.
SET = (
    ("K1", "verus", f"{BASE}/K1", (f"{BASE}/K1/Cargo.toml", f"{BASE}/K1/src/lib.rs"),
     1, ("lemma_stair_closed",), "construct", "X10"),
    ("K2", "verus", f"{BASE}/K2", (f"{BASE}/K2/Cargo.toml", f"{BASE}/K2/src/lib.rs",
                                   f"{BASE}/K2/verification.json"),
     2, ("add_one", "half_up"), "construct", "X05"),
    ("K3", "verus", f"{BASE}/K3", (f"{BASE}/K3/Cargo.toml", f"{BASE}/K3/src/lib.rs"),
     1, ("mod_word",), "construct", "X16"),
    ("C1", "verus", f"{BASE}/C1", (f"{BASE}/C1/Cargo.toml", f"{BASE}/C1/src/lib.rs"),
     1, ("larger_word",), "control", ""),
    ("C2", "verus", f"{BASE}/C2", (f"{BASE}/C2/Cargo.toml", f"{BASE}/C2/src/lib.rs",
                                   f"{BASE}/C2/frozen.rs"),
     1, ("bound_into",), "control", ""),
    ("C3", "dafny", f"{BASE}/C3/main.dfy", (f"{BASE}/C3/main.dfy",),
     2, ("Gate2C3.OddSumSquare",), "control", ""),
    ("C4", "dafny", f"{BASE}/C4/main.dfy", (f"{BASE}/C4/main.dfy", f"{BASE}/C4/frozen.dfy"),
     1, ("Gate2C4.MinOf",), "control", ""),
)
# The verdicts a correct gate gives (word, unknown); written out, never derived.
EXPECTED = {
    "K1": (FAIL, ()),
    "K2": (FAIL, ()),
    "K3": (FAIL, ()),
    "C1": (PASS, ("X07", "X08", "X14")),
    "C2": (PASS, ("X07", "X14")),
    "C3": (PASS, ("X07", "X08", "X14")),
    "C4": (PASS, ("X07", "X14")),
}
# The instruments a correct gate runs on each delivery.
RUNS = {i: {"vcheck --gate", "vaudit", "seed-rerun"} for i, *_ in SET}
RUNS["C2"] = RUNS["C2"] | {"specfreeze --check"}
RUNS["C4"] = RUNS["C4"] | {"specfreeze --check"}


def target(fid, **over):
    for i, lang, t, files, mv, syms, _, _ in SET:
        if i == fid:
            tg = g.CrateTarget(i, lang, t, files, g.Pins(mv, syms))
            return dataclasses.replace(tg, **over)
    raise KeyError(fid)


def label(fid):
    for i, *_, kind, xc in SET:
        if i == fid:
            return g.Label(kind, xc)
    raise KeyError(fid)


def replay(instrument, t):
    return REPLAY.execute(instrument, t)


def gate_doc(fid):
    return copy.deepcopy(replay("vcheck --gate", target(fid).target).document)


class Recorder:
    """A run stub: records each call, answers from the recordings."""

    def __init__(self, killed=None):
        self.calls, self.killed = [], killed or {}

    def __call__(self, instrument, t):
        self.calls.append((instrument, t))
        if instrument in self.killed:
            return ToolResult(instrument, t, {"exit_code": None, "lines": []}, None,
                              self.killed[instrument], "replay", "course", "0" * 64)
        return replay(instrument, t)


# --- the file and the data ------------------------------------------------------------

def test_no_hole_is_left():
    source = Path(g.__file__).read_text(encoding="utf-8")
    assert holes.count_holes(source) == []


def test_the_set_file_matches():
    got = [(t.id, t.lang, t.target, t.files, t.pins.min_verified, t.pins.symbols, lab.kind,
            lab.xclass) for t, lab in g.load_set(FIX / "set.toml")]
    assert got == list(SET)


def test_every_delivery_has_its_recordings():
    for fid, *_ in SET:
        for instrument in RUNS[fid]:
            assert isinstance(replay(instrument, target(fid).target), ToolResult), (fid, instrument)


# --- H4: complete_and_counted ----------------------------------------------------------

@pytest.mark.parametrize("fid", ["C1", "C2", "C3", "C4", "K3"])
def test_h4_a_complete_document(fid):
    assert g.complete_and_counted(gate_doc(fid), target(fid).pins) == []


@pytest.mark.parametrize("fid", ["K1", "K2"])
def test_h4_a_failed_run_is_not_complete(fid):
    reasons = g.complete_and_counted(gate_doc(fid), target(fid).pins)
    assert reasons and all(isinstance(r, str) and r.strip() for r in reasons)


def test_h4_a_delivered_partial_record():
    # K2 ships its own record: a learner-loop run of one function only.
    import json
    doc = json.loads((FIX / "K2" / "verification.json").read_text(encoding="utf-8"))
    assert doc.get("verdict") == "verified"
    reasons = g.complete_and_counted(doc, target("K2").pins)
    assert len(reasons) >= 2


@pytest.mark.parametrize("over", [
    {"lang": "lean"},
    {"stage": "resolve"},
    {"verdict": "failed"},
    {"exit_code": 1},
    {"holes": [{"file": "f", "line": 3, "col": 1, "kind": "assume", "label": "Q98.H1v"}]},
    {"findings": [{"file": "f", "line": 2, "kind": "outside-verus", "message": "m"}]},
    {"verified_count": 0},
    {"verified_count": True},
    {"per_symbol": {}},
], ids=lambda o: "-".join(f"{k}={v!r}"[:24] for k, v in o.items()))
def test_h4_one_defect_at_least_one_reason(over):
    doc = gate_doc("C1")
    doc.update(over)
    reasons = g.complete_and_counted(doc, target("C1").pins)
    assert reasons and all(isinstance(r, str) and r.strip() for r in reasons)


@pytest.mark.parametrize("flag", g.PARTIAL_FLAGS["verus"])
def test_h4_a_partial_command(flag):
    doc = gate_doc("C1")
    doc["cmd"] = list(doc["cmd"]) + [flag, "larger_word"]
    assert len(g.complete_and_counted(doc, target("C1").pins)) == 1


@pytest.mark.parametrize("flag", g.PARTIAL_FLAGS["dafny"])
def test_h4_a_partial_command_dafny(flag):
    doc = gate_doc("C3")
    doc["cmd"] = list(doc["cmd"]) + [flag, "OddSumSquare"]
    assert len(g.complete_and_counted(doc, target("C3").pins)) == 1


def test_h4_the_wrappers_completeness_message():
    doc = gate_doc("C1")
    doc["diagnostics"] = [{"file": "", "line": 0, "col": 0, "severity": "error",
                           "message": "gate: --output-json lacks 'is-verifying-entire-crate'",
                           "code": "gate"}]
    assert len(g.complete_and_counted(doc, target("C1").pins)) == 1


@pytest.mark.parametrize("key", ["lang", "stage", "verdict", "exit_code", "holes", "findings",
                                 "cmd", "diagnostics", "verified_count"])
def test_h4_a_missing_key_fails(key):
    doc = gate_doc("C1")
    del doc[key]
    assert g.complete_and_counted(doc, target("C1").pins)


def test_h4_the_pins_count():
    doc = gate_doc("C1")
    n = doc["verified_count"]
    assert g.complete_and_counted(doc, g.Pins(n, ())) == []
    assert len(g.complete_and_counted(doc, g.Pins(n + 1, ()))) == 1
    assert len(g.complete_and_counted(doc, g.Pins(1, ("larger_word", "no_such_fn", "another")))) == 2


@pytest.mark.parametrize("doc", [None, [], "verified", 0])
def test_h4_not_a_document(doc):
    assert len(g.complete_and_counted(doc, g.Pins(1, ()))) == 1


# --- H5: option_findings --------------------------------------------------------------

def scan(tmp_path, files):
    rels = []
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        rels.append(rel)
    t = g.CrateTarget("T", "verus", "d", tuple(rels), g.Pins(1, ()))
    return [(f.rule, f.path) for f in g.option_findings(t, root=tmp_path)]


def test_h5_clean_files(tmp_path):
    assert scan(tmp_path, {
        "d/Cargo.toml": '[package]\nname = "x"\nbuild = false\n\n[package.metadata.verus]\nverify = true\n',
        "d/src/lib.rs": "use vstd::prelude::*;\nverus! {\n}\n",
        "u/dfyconfig.toml": '[options]\nstandard-libraries = true\nresource-limit = 5000000\n',
        "u/main.dfy": "module M {}\n",
    }) == []


def test_h5_dafny_options(tmp_path):
    got = scan(tmp_path, {"u/dfyconfig.toml": (
        'base = "../x.toml"\n[options]\nstandard-libraries = true\nallow-warnings = true\n'
        'solver-path = "z3"\nverification-time-limit = 0\nplugin = "p.dll"\n')})
    assert got == [("G21", "u/dfyconfig.toml"), ("G6", "u/dfyconfig.toml"),
                   ("G15", "u/dfyconfig.toml"), ("G21", "u/dfyconfig.toml"),
                   ("G16", "u/dfyconfig.toml")]


def test_h5_cargo_manifest(tmp_path):
    got = scan(tmp_path, {"d/Cargo.toml": (
        '[package]\nname = "x"\nbuild = "gen.rs"\n\n[package.metadata.verus]\nverify = false\n'
        'extra-args = ["--no-lifetime"]\n')})
    assert got == [("build-script", "d/Cargo.toml"), ("V18", "d/Cargo.toml"),
                   ("V16", "d/Cargo.toml")]


def test_h5_cargo_config_and_build_tools(tmp_path):
    got = scan(tmp_path, {
        "d/.cargo/config.toml": '[alias]\nverify = "check"\n\n[env]\nVERUS_EXTRA_ARGS = "x"\n',
        "d/build.rs": "fn main() {}\n",
        "d/conftest.py": "",
        "d/.cargo/config": '[build]\nrustflags = ["--cfg", "x"]\n',
    })
    assert got == [("V20", "d/.cargo/config.toml"), ("V24", "d/.cargo/config.toml"),
                   ("build-script", "d/build.rs"), ("conftest", "d/conftest.py"),
                   ("V24", "d/.cargo/config")]


def test_h5_a_config_toml_elsewhere_is_no_cargo_config(tmp_path):
    assert scan(tmp_path, {"d/config.toml": '[alias]\nverify = "check"\n'}) == []


def test_h5_rlimit_attributes(tmp_path):
    got = scan(tmp_path, {"d/src/lib.rs": (
        "verus! {\n#[verifier::rlimit(infinity)]\nproof fn a() {}\n"
        "#[verifier::rlimit(50)]\nproof fn b() {}\n}\n")})
    assert got == [("V22", "d/src/lib.rs"), ("V22", "d/src/lib.rs")]


def test_h5_a_file_that_does_not_parse(tmp_path):
    assert scan(tmp_path, {"d/Cargo.toml": "[package\nname = \n"}) == [("G21", "d/Cargo.toml")]


def test_h5_a_missing_file_raises(tmp_path):
    t = g.CrateTarget("T", "verus", "d", ("d/Cargo.toml",), g.Pins(1, ()))
    with pytest.raises(FileNotFoundError):
        g.option_findings(t, root=tmp_path)


def test_h5_on_the_fixtures():
    assert [(f.rule, f.path) for f in g.option_findings(target("K1"))] == \
        [("V18", f"{BASE}/K1/Cargo.toml")]
    for fid in ("K2", "K3", "C1", "C2", "C3", "C4"):
        assert g.option_findings(target(fid)) == [], fid


# --- H6: seed_spread ------------------------------------------------------------------

@pytest.mark.parametrize("fid", ["C1", "C3"])
def test_h6_a_stable_sweep(fid):
    rec = Recorder()
    sp = g.seed_spread(target(fid), run=rec)
    assert rec.calls == [("seed-rerun", target(fid).target)]
    assert sp.verdicts == ("verified",) * 3 and sp.stable is True
    doc = replay("seed-rerun", target(fid).target).document
    cvs = [e["cv"] for e in doc["spread"]]
    assert sp.widest_cv == (max(cvs) if cvs else None)


def test_h6_a_sweep_that_moved():
    sp = g.seed_spread(target("K3"), run=Recorder())
    doc = replay("seed-rerun", target("K3").target).document
    assert sp.verdicts == tuple(doc["verdicts"][str(s)] for s in (1, 2, 3))
    assert sp.stable is False


def test_h6_other_seeds_are_refused():
    with pytest.raises(ValueError):
        g.seed_spread(target("C1"), seeds=(1, 2), run=Recorder())


def test_h6_a_killed_sweep_raises():
    with pytest.raises(ValueError):
        g.seed_spread(target("C1"), run=Recorder({"seed-rerun": "wall-clock"}))


def test_h6_runs_through_fvh_tools_run(monkeypatch):
    rec = Recorder()
    monkeypatch.setattr(tools, "run", rec)
    g.seed_spread(target("C1"))
    assert rec.calls == [("seed-rerun", target("C1").target)]


# --- H3: gate_crate -------------------------------------------------------------------

def test_h3_takes_a_target_only():
    assert list(inspect.signature(g.gate_crate).parameters) == ["target", "run"]


@pytest.mark.parametrize("fid", [i for i, *_ in SET])
def test_h3_on_the_fixture_set(fid):
    rec = Recorder()
    r = g.gate_crate(target(fid), run=rec)
    word, unknown = EXPECTED[fid]
    assert (r.id, r.verdict.word, r.verdict.unknown) == (fid, word, unknown)
    assert bool(r.verdict.reasons) == (word == FAIL)
    assert sorted(i for i, _ in rec.calls) == sorted(RUNS[fid])
    assert set(r.results) == RUNS[fid]
    assert all(t == target(fid).target for _, t in rec.calls)


def test_h3_the_scan_comes_first(monkeypatch):
    order = []
    real = g.option_findings

    def scan_first(t, **kw):
        order.append("scan")
        return real(t, **kw)

    def run(instrument, t):
        order.append(instrument)
        return replay(instrument, t)

    monkeypatch.setattr(g, "option_findings", scan_first)
    g.gate_crate(target("K1"), run=run)
    assert order[0] == "scan" and order[-1] == "seed-rerun"


def test_h3_a_poisoned_file_alone_fails(tmp_path, monkeypatch):
    # C1's instruments all pass; a refused option in its files must fail it.
    (tmp_path / "x").mkdir()
    (tmp_path / "x" / "dfyconfig.toml").write_text("[options]\nallow-warnings = true\n")
    monkeypatch.setattr(g, "COURSE_ROOT", tmp_path)
    r = g.gate_crate(target("C1", files=("x/dfyconfig.toml",)), run=Recorder())
    assert r.verdict.word == FAIL and [f.rule for f in r.findings] == ["G6"]


def test_h3_decides_from_the_delivery_alone():
    for fid, *_ in SET:
        r = g.gate_crate(target(fid, id="neutral"), run=Recorder())
        assert (r.id, r.verdict.word, r.verdict.unknown) == ("neutral", *EXPECTED[fid])


def test_h3_runs_through_fvh_tools_run(monkeypatch):
    rec = Recorder()
    monkeypatch.setattr(tools, "run", rec)
    r = g.gate_crate(target("C1"))
    assert r.verdict.word == PASS and len(rec.calls) == 3


@pytest.mark.parametrize("name", ["vcheck --gate", "vaudit", "seed-rerun"])
def test_h3_a_killed_run_fails(name):
    r = g.gate_crate(target("C1"), run=Recorder({name: "memory"}))
    assert r.verdict.word == FAIL and r.verdict.unknown == ()


def test_h3_an_instrument_that_cannot_run_raises():
    def broken(instrument, t):
        raise tools.RunnerUnavailable("no verifier here")
    with pytest.raises(tools.RunnerUnavailable):
        g.gate_crate(target("C1"), run=broken)


def test_h3_refuses_another_language():
    with pytest.raises(ValueError):
        g.gate_crate(target("C1", lang="lean"), run=Recorder())


def test_h3_a_seed_flip_is_caught_by_the_sweep_alone():
    # K3's own gate run is complete and its audit clean: only the sweep moves.
    assert g.complete_and_counted(gate_doc("K3"), target("K3").pins) == []
    assert replay("vaudit", target("K3").target).exit_code == 0
    r = g.gate_crate(target("K3"), run=Recorder())
    assert r.verdict.word == FAIL and r.spread is not None and r.spread.stable is False


# --- H7: fp_report --------------------------------------------------------------------

def results_of(ids):
    return [g.gate_crate(target(i), run=Recorder()) for i in ids]


def test_h7_on_the_fixture_set(monkeypatch):
    calls = []
    real = fstats.wilson_interval

    def wilson(*a, **kw):
        calls.append(a)
        return real(*a, **kw)

    monkeypatch.setattr(fstats, "wilson_interval", wilson)
    monkeypatch.setattr(g.stats, "wilson_interval", wilson)
    ids = [i for i, *_ in SET]
    rep = g.fp_report(results_of(ids), {i: label(i) for i in ids})
    assert (rep.controls, rep.fp, rep.held_by_unknown, rep.false_pass) == (4, 0, 0, 0)
    assert dict(rep.detected) == {"X10": 1, "X05": 1, "X16": 1}
    assert rep.fp_interval == real(0, 4)
    assert calls and calls[-1][:2] == (0, 4)


def test_h7_counts_by_kind():
    ok = g.GateResult("a", g.GateVerdict(PASS, GRADER_ONLY, ()), {}, (), None)
    bad = g.GateResult("b", g.GateVerdict(FAIL, (), ("x",)), {}, (), None)
    held = g.GateResult("c", g.GateVerdict(PASS, GRADER_ONLY, ()), {}, (), None)
    leak = g.GateResult("d", g.GateVerdict(PASS, (), ()), {}, (), None)
    fpos = g.GateResult("e", g.GateVerdict(FAIL, (), ("y",)), {}, (), None)
    labels = {"a": g.Label("control", ""), "b": g.Label("construct", "X03"),
              "c": g.Label("construct", "X07"), "d": g.Label("construct", "X01"),
              "e": g.Label("control", "")}
    rep = g.fp_report([ok, bad, held, leak, fpos], labels)
    assert (rep.controls, rep.fp, rep.held_by_unknown, rep.false_pass) == (2, 1, 1, 1)
    assert dict(rep.detected) == {"X03": 1, "X07": 0, "X01": 0}
    assert rep.fp_interval == fstats.wilson_interval(1, 2)


def test_h7_no_control():
    bad = g.GateResult("b", g.GateVerdict(FAIL, (), ("x",)), {}, (), None)
    rep = g.fp_report([bad], {"b": g.Label("construct", "X03")})
    assert rep.controls == 0 and rep.fp_interval == (0.0, 1.0)


def test_h7_a_result_without_a_label():
    ok = g.GateResult("a", g.GateVerdict(PASS, GRADER_ONLY, ()), {}, (), None)
    with pytest.raises(ValueError):
        g.fp_report([ok], {})
    with pytest.raises(ValueError):
        g.fp_report([ok], {"a": g.Label("covered-elsewhere", "")})
