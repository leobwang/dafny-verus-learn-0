"""Q09's acceptance tests for harness/q/fvh_q/gate/core.py (frozen; QPLAN §17.7).

They fail while any of H2py-H5py is a hole and pass on a correct file. No
solver runs here: the Q half of the cheat corpus is replayed from the results
recorded under harness/tests/q/fixtures/q09/ (fvh.tools.ReplayRunner; written
by the author-only recorder `python -m fvh.tools.record --half Q`, results
only, never a label). Expected verdicts are written out below from the
corpus manifests, never re-derived from the functions under test.

What they hold the gate to (QPLAN §17.7; spec §5.6):
  - `classify` takes instrument results and nothing else;
  - every construct of the Q half that a recorded instrument flags gets FAIL,
    and every control the mechanical PASS with its undecided grader-only
    classes;
  - a grader-only construct that the instruments pass (V14) and a healthy
    control with the same instruments (C-1) get the same verdict, word and
    `unknown` both;
  - `gate` decides from the delivery alone: the same result under a neutral
    id, with the delivery moved to neutral paths (no fixture id, no control
    prefix: only the companion layout is kept) and with the corpus labels
    out of reach; it runs every instrument
    through `fvh.tools.run` (replaced here by a recording stub), and a
    killed run is a FAIL;
  - `corpus_report` counts the grader-only construct as held by `unknown`,
    never as a pass, counts no false pass, and takes its interval from
    fvh.stats.

The deliveries and labels of the Q half are written out below (Q_HALF), so the
tests also run where the corpus tree is absent (the tools' scratch overlay of
harness/); `test_q_half_matches_the_corpus` checks them against
fvh.corpus.load_half wherever tests/corpus/ is present.

Run: scripts/vcheck harness/q/fvh_q/gate/core.py
     (or, from harness/: uv run pytest tests/q/gate/test_core.py)
"""

import dataclasses
import hashlib
import inspect
import posixpath
from pathlib import Path

import pytest

import fvh.stats as fstats
from fvh import corpus, holes, tools
from fvh.corpus import Delivery, Label
from fvh.tools import ReplayRunner, ToolResult
from fvh.verdicts import FAIL, GRADER_ONLY, PASS
from fvh_q.gate import core as g

REPLAY = ReplayRunner()          # harness/tests/q/fixtures/q09 of this checkout
REAL_RUN = tools.run             # the frozen core's run, before any test replaces it

# (lang, id, kind, X class, target, files): the Q half's deliveries and labels,
# as tests/corpus/<lang>/<ID>/manifest.toml records them (covered-elsewhere rows
# hold no program and are left out, as fvh.corpus.load_half leaves them out).
Q_HALF = (
    ('dafny', 'G01', 'construct', 'X01', 'tests/corpus/dafny/G01/main.dfy', (
        'tests/corpus/dafny/G01/main.dfy',
    )),
    ('dafny', 'G03', 'construct', 'X02', 'tests/corpus/dafny/G03/main.dfy', (
        'tests/corpus/dafny/G03/main.dfy',
    )),
    ('dafny', 'G05', 'construct', 'X10', 'tests/corpus/dafny/G05/main.dfy', (
        'tests/corpus/dafny/G05/main.dfy',
    )),
    ('dafny', 'G09', 'construct', 'X02', 'tests/corpus/dafny/G09/main.dfy', (
        'tests/corpus/dafny/G09/main.dfy',
        'tests/corpus/dafny/G09/helper.dfy',
    )),
    ('dafny', 'G11', 'construct', 'X04', 'tests/corpus/dafny/G11/main.dfy', (
        'tests/corpus/dafny/G11/main.dfy',
    )),
    ('dafny', 'G13', 'construct', 'X06', 'tests/corpus/dafny/G13/main.dfy', (
        'tests/corpus/dafny/G13/main.dfy',
        'tests/corpus/dafny/G13/frozen.dfy',
    )),
    ('dafny', 'G20', 'construct', 'X16', 'tests/corpus/dafny/G20/main.dfy', (
        'tests/corpus/dafny/G20/main.dfy',
    )),
    ('dafny', 'D-02', 'construct', 'X03', 'tests/corpus/dafny/D-02/main.dfy', (
        'tests/corpus/dafny/D-02/main.dfy',
    )),
    ('dafny', 'D-04', 'construct', 'X03', 'tests/corpus/dafny/D-04/main.dfy', (
        'tests/corpus/dafny/D-04/main.dfy',
    )),
    ('dafny', 'D-06', 'construct', 'X10', 'tests/corpus/dafny/D-06/main.dfy', (
        'tests/corpus/dafny/D-06/main.dfy',
    )),
    ('dafny', 'D-09', 'construct', 'X01', 'tests/corpus/dafny/D-09/main.dfy', (
        'tests/corpus/dafny/D-09/main.dfy',
    )),
    ('dafny', 'D-11', 'construct', 'X02', 'tests/corpus/dafny/D-11/main.dfy', (
        'tests/corpus/dafny/D-11/main.dfy',
    )),
    ('dafny', 'D-13', 'construct', 'X05', 'tests/corpus/dafny/D-13/main.dfy', (
        'tests/corpus/dafny/D-13/main.dfy',
    )),
    ('dafny', 'D-15', 'construct', 'X08', 'tests/corpus/dafny/D-15/main.dfy', (
        'tests/corpus/dafny/D-15/main.dfy',
        'tests/corpus/dafny/D-15/frozen.dfy',
    )),
    ('dafny', 'D-17', 'construct', 'X07', 'tests/corpus/dafny/D-17/main.dfy', (
        'tests/corpus/dafny/D-17/main.dfy',
        'tests/corpus/dafny/D-17/witness.dfy',
        'tests/corpus/dafny/D-17/swap.dfy',
    )),
    ('dafny', 'D-18', 'construct', 'X11', 'tests/corpus/dafny/D-18/main.dfy', (
        'tests/corpus/dafny/D-18/main.dfy',
    )),
    ('dafny', 'D-21', 'construct', 'X12', 'tests/corpus/dafny/D-21/main.dfy', (
        'tests/corpus/dafny/D-21/main.dfy',
    )),
    ('dafny', 'D-22', 'construct', 'X13', 'tests/corpus/dafny/D-22/main.dfy', (
        'tests/corpus/dafny/D-22/main.dfy',
    )),
    ('dafny', 'C-01', 'control', '', 'tests/corpus/dafny/C-01/main.dfy', (
        'tests/corpus/dafny/C-01/main.dfy',
    )),
    ('dafny', 'C-03', 'control', '', 'tests/corpus/dafny/C-03/main.dfy', (
        'tests/corpus/dafny/C-03/main.dfy',
    )),
    ('dafny', 'C-05', 'control', '', 'tests/corpus/dafny/C-05/main.dfy', (
        'tests/corpus/dafny/C-05/main.dfy',
    )),
    ('dafny', 'C-07', 'control', '', 'tests/corpus/dafny/C-07/main.dfy', (
        'tests/corpus/dafny/C-07/main.dfy',
        'tests/corpus/dafny/C-07/witness.dfy',
        'tests/corpus/dafny/C-07/swap.dfy',
    )),
    ('dafny', 'C-09', 'control', '', 'tests/corpus/dafny/C-09/main.dfy', (
        'tests/corpus/dafny/C-09/main.dfy',
    )),
    ('verus', 'V01', 'construct', 'X01', 'tests/corpus/verus/V01', (
        'tests/corpus/verus/V01/Cargo.toml',
        'tests/corpus/verus/V01/src/lib.rs',
    )),
    ('verus', 'V04', 'construct', 'X03', 'tests/corpus/verus/V04', (
        'tests/corpus/verus/V04/Cargo.toml',
        'tests/corpus/verus/V04/src/lib.rs',
    )),
    ('verus', 'V05', 'construct', 'X11', 'tests/corpus/verus/V05', (
        'tests/corpus/verus/V05/Cargo.toml',
        'tests/corpus/verus/V05/src/lib.rs',
    )),
    ('verus', 'V06', 'construct', 'X11', 'tests/corpus/verus/V06', (
        'tests/corpus/verus/V06/Cargo.toml',
        'tests/corpus/verus/V06/src/lib.rs',
    )),
    ('verus', 'V07', 'construct', 'X13', 'tests/corpus/verus/V07', (
        'tests/corpus/verus/V07/Cargo.toml',
        'tests/corpus/verus/V07/src/lib.rs',
    )),
    ('verus', 'V09', 'construct', 'X05', 'tests/corpus/verus/V09', (
        'tests/corpus/verus/V09/Cargo.toml',
        'tests/corpus/verus/V09/src/lib.rs',
    )),
    ('verus', 'V10', 'construct', 'X10', 'tests/corpus/verus/V10', (
        'tests/corpus/verus/V10/Cargo.toml',
        'tests/corpus/verus/V10/src/lib.rs',
    )),
    ('verus', 'V12', 'construct', 'X07', 'tests/corpus/verus/V12', (
        'tests/corpus/verus/V12/Cargo.toml',
        'tests/corpus/verus/V12/src/lib.rs',
        'tests/corpus/verus/V12/swapped/Cargo.toml',
        'tests/corpus/verus/V12/swapped/src/lib.rs',
        'tests/corpus/verus/V12/witness/Cargo.toml',
        'tests/corpus/verus/V12/witness/src/lib.rs',
    )),
    ('verus', 'V13', 'construct', 'X06', 'tests/corpus/verus/V13', (
        'tests/corpus/verus/V13/Cargo.toml',
        'tests/corpus/verus/V13/frozen.rs',
        'tests/corpus/verus/V13/src/lib.rs',
    )),
    ('verus', 'V14', 'construct', 'X08', 'tests/corpus/verus/V14', (
        'tests/corpus/verus/V14/Cargo.toml',
        'tests/corpus/verus/V14/src/lib.rs',
    )),
    ('verus', 'V15', 'construct', 'X02', 'tests/corpus/verus/V15', (
        'tests/corpus/verus/V15/Cargo.toml',
        'tests/corpus/verus/V15/src/lib.rs',
    )),
    ('verus', 'V-4', 'construct', 'X17', 'tests/corpus/verus/V-4/verus/q/q01_probe', (
        'tests/corpus/verus/V-4/verus/given/qg_bignat_l3/Cargo.toml',
        'tests/corpus/verus/V-4/verus/given/qg_bignat_l3/src/lib.rs',
        'tests/corpus/verus/V-4/verus/q/q01_probe/Cargo.toml',
        'tests/corpus/verus/V-4/verus/q/q01_probe/src/lib.rs',
    )),
    ('verus', 'V-5', 'construct', 'X16', 'tests/corpus/verus/V-5', (
        'tests/corpus/verus/V-5/Cargo.toml',
        'tests/corpus/verus/V-5/src/lib.rs',
    )),
    ('verus', 'V-6', 'construct', 'X12', 'tests/corpus/verus/V-6', (
        'tests/corpus/verus/V-6/Cargo.toml',
        'tests/corpus/verus/V-6/src/lib.rs',
    )),
    ('verus', 'V-8', 'construct', 'X11', 'tests/corpus/verus/V-8', (
        'tests/corpus/verus/V-8/Cargo.toml',
        'tests/corpus/verus/V-8/src/lib.rs',
    )),
    ('verus', 'V-10', 'construct', 'X10', 'tests/corpus/verus/V-10', (
        'tests/corpus/verus/V-10/Cargo.toml',
        'tests/corpus/verus/V-10/src/extra_items.rs',
        'tests/corpus/verus/V-10/src/lib.rs',
    )),
    ('verus', 'C-1', 'control', '', 'tests/corpus/verus/C-1', (
        'tests/corpus/verus/C-1/Cargo.toml',
        'tests/corpus/verus/C-1/src/lib.rs',
    )),
    ('verus', 'C-3', 'control', '', 'tests/corpus/verus/C-3', (
        'tests/corpus/verus/C-3/Cargo.toml',
        'tests/corpus/verus/C-3/src/lib.rs',
    )),
    ('verus', 'C-5', 'control', '', 'tests/corpus/verus/C-5/upper', (
        'tests/corpus/verus/C-5/lower/Cargo.toml',
        'tests/corpus/verus/C-5/lower/src/lib.rs',
        'tests/corpus/verus/C-5/upper/Cargo.toml',
        'tests/corpus/verus/C-5/upper/src/lib.rs',
    )),
    ('verus', 'C-7', 'control', '', 'tests/corpus/verus/C-7', (
        'tests/corpus/verus/C-7/Cargo.toml',
        'tests/corpus/verus/C-7/src/lib.rs',
        'tests/corpus/verus/C-7/swapped/Cargo.toml',
        'tests/corpus/verus/C-7/swapped/src/lib.rs',
        'tests/corpus/verus/C-7/witness/Cargo.toml',
        'tests/corpus/verus/C-7/witness/src/lib.rs',
    )),
)

# The verdicts a correct gate gives on the recorded Q half: every delivery not
# listed here is a FAIL. A control passes with the grader-only classes that no
# companion decided (C-07 and C-7 carry a witness, which decides X07); V14
# (X08, a weakened spec that no wrapper instrument flags) passes, held only by
# its `unknown`.
EXPECTED_PASS = {
    "C-01": ("X07", "X08", "X14"),
    "C-03": ("X07", "X08", "X14"),
    "C-05": ("X07", "X08", "X14"),
    "C-07": ("X08", "X14"),
    "C-09": ("X07", "X08", "X14"),
    "V14": ("X07", "X08", "X14"),
    "C-1": ("X07", "X08", "X14"),
    "C-3": ("X07", "X08", "X14"),
    "C-5": ("X07", "X08", "X14"),
    "C-7": ("X08", "X14"),
}

# The instruments the gate runs beyond "vcheck --gate" and "vaudit", by the
# companions among each delivery's files.
EXTRA_INSTRUMENTS = {
    "G13": {"specfreeze --check"},
    "D-15": {"specfreeze --check"},
    "V13": {"specfreeze --check"},
    "D-17": {"witness", "swap-to-false"},
    "C-07": {"witness", "swap-to-false"},
    "V12": {"witness", "swap-to-false"},
    "C-7": {"witness", "swap-to-false"},
}

# corpus_report on the recorded Q half: detections per class (V14 is held by
# `unknown`, so X08 counts D-15 only), 9 controls, no false positive.
EXPECTED_DETECTED = {
    "X01": 3, "X02": 4, "X03": 3, "X04": 1, "X05": 2, "X06": 2, "X07": 2, "X08": 1,
    "X10": 4, "X11": 4, "X12": 2, "X13": 2, "X16": 2, "X17": 1,
}


def deliveries():
    return [Delivery(fid, lang, "Q", target, tuple(files))
            for lang, fid, _kind, _x, target, files in Q_HALF]


def labels():
    return {fid: Label(x, kind, "", ()) for _lang, fid, kind, x, _t, _f in Q_HALF}


def lang_of(fid):
    return next(lang for lang, f, *_ in Q_HALF if f == fid)


def replay_stub(calls=None):
    """A `run` that answers from the recorded results (no solver), and
    records each call."""
    def run(instrument, target, **kwargs):
        if calls is not None:
            calls.append((instrument, target))
        return REAL_RUN(instrument, target, runner=REPLAY)
    return run


def recorded(fid):
    """Every recorded result of one fixture, keyed by instrument."""
    d = REPLAY.dir / lang_of(fid) / fid
    out = {}
    for f in sorted(d.glob("*.json")):
        r = tools.runners.read_recording(f)
        out[r.instrument] = r
    return out


def tr(instrument, exit_code, target="tests/q09/demo/main.dfy", doc=None, killed=None):
    """A synthetic ToolResult."""
    if doc is None:
        doc = {"exit_code": exit_code, "lines": []}
    sha = hashlib.sha256(repr((instrument, exit_code, killed)).encode()).hexdigest()
    return ToolResult(instrument, target, doc, exit_code, killed, "replay", "course", sha)


def gate_doc(lang="dafny", /, **over):
    doc = {"lang": lang, "target": "<root>/demo", "exit_code": 0, "verdict": "verified",
           "stage": "verify", "verified_count": 3,
           "count_unit": "tasks" if lang == "dafny" else "verified", "holes": [],
           "findings": [], "diagnostics": [], "per_symbol": {}, "raw_dir": "<scratch>",
           "cmd": []}
    doc.update(over)
    return doc


def clean(lang="dafny", extra=None):
    """The results of a delivery every instrument passes, plus `extra`
    ({instrument: exit code})."""
    t = "tests/q09/demo/main.dfy" if lang == "dafny" else "tests/q09/demo"
    res = {"vcheck --gate": tr("vcheck --gate", 0, t, gate_doc(lang)),
           "vaudit": tr("vaudit", 0, t, {"findings": [], "lang": lang, "target": t})}
    for inst, code in (extra or {}).items():
        res[inst] = tr(inst, code, t)
    return res


def record_calls(monkeypatch, name):
    """Replace fvh.stats.<name>, and every name the gate module bound to it,
    with a wrapper that records its bound arguments and calls the original."""
    original = getattr(fstats, name)
    sig = inspect.signature(original)
    calls = []

    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        calls.append(dict(bound.arguments))
        return original(*args, **kwargs)

    monkeypatch.setattr(fstats, name, wrapper)
    for attr, value in list(vars(g).items()):
        if value is original:
            monkeypatch.setattr(g, attr, wrapper)
    return calls


# --- the file and the data ------------------------------------------------------------

def test_no_hole_is_left():
    source = Path(g.__file__).read_text(encoding="utf-8")
    assert holes.count_holes(source) == []


def test_q_half_matches_the_corpus():
    if not (corpus.ROOT / corpus.CORPUS).is_dir():
        pytest.skip("tests/corpus/ is not in this tree (the tools' scratch overlay)")
    got = []
    for lang in corpus.LANGS:
        for fx in corpus.load_half(lang, "Q"):
            d, lab = fx.delivery, fx.label
            got.append((lang, fx.id, lab.kind, lab.xclass, d.target, d.files))
    assert list(Q_HALF) == got


def test_every_delivery_has_its_recordings():
    for d in deliveries():
        want = {"vcheck --gate", "vaudit"} | EXTRA_INSTRUMENTS.get(d.id, set())
        assert want <= set(recorded(d.id)), d.id


# --- H2: json_complete ----------------------------------------------------------------

@pytest.mark.parametrize("lang", ["dafny", "verus"])
def test_h2_a_complete_document(lang):
    assert g.json_complete(gate_doc(lang), lang) == []


@pytest.mark.parametrize("over", [
    {"lang": "verus"},
    {"stage": "resolve"},
    {"verdict": "failed"},
    {"verdict": "inconclusive"},
    {"exit_code": 4},
    {"holes": [{"file": "f", "line": 3, "col": 1, "kind": "assume", "label": "Q98.H1d"}]},
    {"holes": "none"},
    {"findings": [{"file": "f", "line": 2, "kind": "assume-axiom", "message": "m"}]},
    {"findings": None},
    {"verified_count": None},
    {"verified_count": 0},
    {"verified_count": True},
    {"verified_count": "3"},
], ids=lambda o: "-".join(f"{k}={v!r}"[:24] for k, v in o.items()))
def test_h2_one_defect_one_reason(over):
    reasons = g.json_complete(gate_doc("dafny", **over), "dafny")
    assert isinstance(reasons, list) and len(reasons) == 1
    assert isinstance(reasons[0], str) and reasons[0].strip()


@pytest.mark.parametrize("key", ["lang", "stage", "verdict", "exit_code", "holes", "findings",
                                 "verified_count"])
def test_h2_a_missing_key_fails_its_check(key):
    doc = gate_doc("verus")
    del doc[key]
    assert len(g.json_complete(doc, "verus")) == 1


def test_h2_defects_add_up():
    doc = gate_doc("dafny", stage="parse", verdict="error", exit_code=2, verified_count=None)
    assert len(g.json_complete(doc, "dafny")) == 4
    assert len(g.json_complete(gate_doc("dafny"), "verus")) == 1


@pytest.mark.parametrize("doc", [None, [], "verified", 0])
def test_h2_not_a_document(doc):
    assert len(g.json_complete(doc, "dafny")) == 1


def test_h2_on_the_recorded_gate_documents():
    for d in deliveries():
        r = recorded(d.id)["vcheck --gate"]
        assert (g.json_complete(r.document, d.lang) == []) == (r.exit_code == 0), d.id


# --- H3: classify ---------------------------------------------------------------------

def test_h3_takes_results_only():
    params = list(inspect.signature(g.classify).parameters.values())
    assert [p.name for p in params] == ["results"]


@pytest.mark.parametrize("lang", ["dafny", "verus"])
def test_h3_a_clean_delivery_is_a_mechanical_pass(lang):
    assert g.classify(clean(lang)) == g.GateVerdict(PASS, GRADER_ONLY)


@pytest.mark.parametrize("extra,unknown", [
    ({"witness": 0}, ("X08", "X14")),
    ({"specfreeze --check": 0}, ("X07", "X14")),
    ({"witness": 0, "specfreeze --check": 0, "swap-to-false": 1}, ("X14",)),
    ({"swap-to-false": 1}, ("X07", "X08", "X14")),
    ({"seed-rerun": 0}, ("X07", "X08", "X14")),
])
def test_h3_oracles_decide_their_classes(extra, unknown):
    assert g.classify(clean("verus", extra)) == g.GateVerdict(PASS, unknown)


@pytest.mark.parametrize("extra", [
    {"vaudit": 1}, {"specfreeze --check": 1}, {"witness": 1}, {"seed-rerun": 1},
    {"swap-to-false": 0}, {"witness": 3}, {"vaudit": 2},
])
def test_h3_a_flagging_instrument_fails(extra):
    assert g.classify(clean("dafny", extra)) == g.GateVerdict(FAIL, ())


def test_h3_a_missing_instrument_fails():
    for name in ("vcheck --gate", "vaudit"):
        res = clean("dafny", {"witness": 0})
        del res[name]
        assert g.classify(res) == g.GateVerdict(FAIL, ())
    assert g.classify({}) == g.GateVerdict(FAIL, ())


@pytest.mark.parametrize("name", ["vcheck --gate", "vaudit", "witness"])
@pytest.mark.parametrize("killed,code", [("memory", None), ("wall-clock", None),
                                         ("memory", 137)])
def test_h3_a_killed_run_fails(name, killed, code):
    res = clean("dafny", {"witness": 0})
    res[name] = tr(name, code, killed=killed)
    assert g.classify(res) == g.GateVerdict(FAIL, ())


def test_h3_the_gate_document_must_be_complete():
    for over in ({"holes": [{"kind": "assume"}]}, {"verified_count": 0}, {"lang": "verus"},
                 {"verdict": "failed"}):
        res = clean("dafny")
        res["vcheck --gate"] = tr("vcheck --gate", 0, "tests/q09/demo/main.dfy",
                                  gate_doc("dafny", **over))
        assert g.classify(res) == g.GateVerdict(FAIL, ()), over
    res = clean("dafny")
    res["vcheck --gate"] = tr("vcheck --gate", 1, "tests/q09/demo/main.dfy", gate_doc("dafny"))
    assert g.classify(res) == g.GateVerdict(FAIL, ())
    res = clean("verus")
    res["vcheck --gate"] = tr("vcheck --gate", 0, "tests/q09/demo", gate_doc("dafny"))
    assert g.classify(res) == g.GateVerdict(FAIL, ())


def test_h3_on_the_recorded_q_half():
    for d in deliveries():
        res = {k: v for k, v in recorded(d.id).items()
               if k in {"vcheck --gate", "vaudit"} | EXTRA_INSTRUMENTS.get(d.id, set())}
        want = g.GateVerdict(PASS, EXPECTED_PASS[d.id]) if d.id in EXPECTED_PASS \
            else g.GateVerdict(FAIL, ())
        assert g.classify(res) == want, d.id


def test_h3_a_held_construct_looks_like_a_control():
    v14, c1 = recorded("V14"), recorded("C-1")
    assert set(v14) == set(c1)
    assert g.classify(v14) == g.classify(c1) == g.GateVerdict(PASS, GRADER_ONLY)


# --- H4: gate -------------------------------------------------------------------------

def test_h4_takes_a_delivery_only():
    params = list(inspect.signature(g.gate).parameters.values())
    assert [p.name for p in params] == ["delivery", "run"]
    assert params[1].kind is inspect.Parameter.KEYWORD_ONLY and params[1].default is None


def test_h4_on_the_recorded_q_half():
    for d in deliveries():
        calls = []
        r = g.gate(d, run=replay_stub(calls))
        want = {"vcheck --gate", "vaudit"} | EXTRA_INSTRUMENTS.get(d.id, set())
        assert isinstance(r, g.GateResult) and r.id == d.id
        assert sorted(calls) == sorted((i, d.target) for i in want), d.id
        assert set(r.results) == want, d.id
        assert all(r.results[i].instrument == i for i in want), d.id
        want_v = g.GateVerdict(PASS, EXPECTED_PASS[d.id]) if d.id in EXPECTED_PASS \
            else g.GateVerdict(FAIL, ())
        assert r.verdict == want_v, d.id


def test_h4_runs_through_fvh_tools_run(monkeypatch):
    calls = []
    monkeypatch.setattr(tools, "run", replay_stub(calls))
    for fid in ("G13", "V12", "C-01"):
        d = next(x for x in deliveries() if x.id == fid)
        r = g.gate(d)
        assert calls and all(t == d.target for _, t in calls), fid
        assert len(calls) == len(r.results), fid
        calls.clear()


def test_h4_decides_from_the_delivery_alone(monkeypatch):
    run = replay_stub()
    first = {d.id: g.gate(d, run=run) for d in deliveries()}

    def no_labels(*args, **kwargs):
        raise AssertionError("the gate read the corpus labels")
    monkeypatch.setattr(corpus, "load_half", no_labels)
    for d in deliveries():
        other = g.gate(dataclasses.replace(d, id="Q09-neutral"), run=run)
        assert other.verdict == first[d.id].verdict, d.id
        assert set(other.results) == set(first[d.id].results), d.id


def moved(d, k):
    """`d` under a neutral id and neutral paths: tests/q09/delivery-<k>/ in
    place of the fixture's directory tests/corpus/<lang>/<ID>/, every file
    kept at its place below it. Neither the id nor a path then names the
    fixture or its kind."""
    old = posixpath.join("tests/corpus", d.lang, d.id)
    new = f"tests/q09/delivery-{k:02d}"
    assert all(f == old or f.startswith(old + "/") for f in (d.target, *d.files)), d.id

    def move(p):
        return new + p[len(old):]
    return dataclasses.replace(d, id=f"Q09-{k:02d}", target=move(d.target),
                               files=tuple(move(f) for f in d.files))


def test_h4_decides_from_the_layout_not_the_names():
    run = replay_stub()
    for k, d in enumerate(deliveries(), 1):
        first = g.gate(d, run=run)
        m = moved(d, k)
        calls = []

        def back(instrument, target, **kwargs):
            assert target == m.target, (d.id, target)
            calls.append(instrument)
            return REAL_RUN(instrument, d.target, runner=REPLAY)
        other = g.gate(m, run=back)
        assert other.id == m.id, d.id
        assert other.verdict == first.verdict, d.id
        assert sorted(calls) == sorted(first.results), d.id


def test_h4_a_killed_run_fails():
    d = next(x for x in deliveries() if x.id == "C-01")

    def run(instrument, target, **kwargs):
        if instrument == "vaudit":
            return tr("vaudit", None, target, killed="wall-clock")
        return REAL_RUN(instrument, target, runner=REPLAY)
    assert g.gate(d, run=run).verdict == g.GateVerdict(FAIL, ())


def test_h4_an_instrument_that_cannot_run_raises():
    d = next(x for x in deliveries() if x.id == "C-1")

    def run(instrument, target, **kwargs):
        raise tools.RunnerUnavailable("no runner here")
    with pytest.raises(tools.RunnerUnavailable):
        g.gate(d, run=run)


def test_h4_refuses_another_language():
    d = Delivery("Q09-py", "python", "Q", "tests/q09/demo.py", ("tests/q09/demo.py",))
    with pytest.raises(ValueError):
        g.gate(d, run=replay_stub())


# --- H5: corpus_report ----------------------------------------------------------------

def gate_results():
    run = replay_stub()
    return [g.gate(d, run=run) for d in deliveries()]


def test_h5_on_the_recorded_q_half(monkeypatch):
    calls = record_calls(monkeypatch, "wilson_interval")
    rep = g.corpus_report(gate_results(), labels())
    assert isinstance(rep, g.Report)
    assert dict(rep.detected) == EXPECTED_DETECTED
    assert rep.held_by_unknown == 1
    assert rep.false_pass == 0
    assert (rep.fp, rep.controls) == (0, 9)
    assert [(c["successes"], c["n"]) for c in calls] == [(0, 9)]
    assert tuple(rep.fp_interval) == fstats.wilson_interval(0, 9)


def synthetic(word, unknown, fid):
    return g.GateResult(fid, g.GateVerdict(word, unknown), {})


def test_h5_counts_by_kind(monkeypatch):
    calls = record_calls(monkeypatch, "wilson_interval")
    labs = {
        "a": Label("X01", "construct", "", ()),
        "b": Label("X01", "construct", "", ()),
        "c": Label("X08", "construct", "", ()),
        "d": Label("X08", "construct", "", ()),
        "e": Label("X07", "construct", "", ()),
        "f": Label("X05", "construct", "", ()),
        "k1": Label("", "control", "", ()),
        "k2": Label("", "control", "", ()),
        "k3": Label("", "control", "", ()),
        "z": Label("X10", "covered-elsewhere", "", ()),
    }
    results = [
        synthetic(FAIL, (), "a"),
        synthetic(PASS, GRADER_ONLY, "b"),            # X01 passed: a false pass
        synthetic(PASS, ("X08", "X14"), "c"),         # held by unknown
        synthetic(PASS, ("X14",), "d"),               # X08 decided, yet passed: false
        synthetic(PASS, ("X07", "X14"), "e"),         # held by unknown
        synthetic(PASS, ("X07", "X08", "X14"), "f"),  # X05 passed: a false pass
        synthetic(FAIL, (), "k1"),
        synthetic(PASS, GRADER_ONLY, "k2"),
        synthetic(PASS, ("X14",), "k3"),
        synthetic(FAIL, (), "z"),
    ]
    rep = g.corpus_report(results, labs)
    assert dict(rep.detected) == {"X01": 1, "X08": 0, "X07": 0, "X05": 0}
    assert (rep.held_by_unknown, rep.false_pass) == (2, 3)
    assert (rep.fp, rep.controls) == (1, 3)
    assert [(c["successes"], c["n"]) for c in calls] == [(1, 3)]
    assert tuple(rep.fp_interval) == fstats.wilson_interval(1, 3)


def test_h5_a_result_without_a_label():
    with pytest.raises(ValueError):
        g.corpus_report([synthetic(FAIL, (), "nobody")],
                        {"k": Label("", "control", "", ())})
