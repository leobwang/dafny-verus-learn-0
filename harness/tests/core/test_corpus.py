"""The frozen core's own tests: fvh.corpus, the read-only view of the cheat
corpus (DV4-PLAN §3.7, §9).

The parity tests load scripts/test_corpus.py (the corpus runner, the corpus's
validator) and check fvh.corpus against its loader on every fixture: the same
ids, halves, classes, kinds, titles, targets, files and expectations. The
synthetic corpora below are invented for the test (ids Q98-style, no course
content).
"""

import dataclasses
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

import pytest

from fvh import corpus
from fvh.corpus import CorpusError, Delivery, Expect, Fixture, Label, load_half

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "scripts" / "test_corpus.py"


@pytest.fixture(scope="module")
def runner():
    """scripts/test_corpus.py, loaded under another name, with sys.path restored."""
    assert RUNNER.is_file(), "scripts/test_corpus.py is missing: the parity check cannot run"
    saved = list(sys.path)
    try:
        loader = importlib.machinery.SourceFileLoader("dvl0_corpus_runner", str(RUNNER))
        spec = importlib.util.spec_from_loader("dvl0_corpus_runner", loader)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["dvl0_corpus_runner"] = mod          # its dataclasses look the module up
        loader.exec_module(mod)
    finally:
        sys.path[:] = saved
    return mod


@pytest.fixture(scope="module")
def theirs(runner):
    fixtures, problems = runner.load_corpus()
    assert not problems, problems
    assert fixtures, "the corpus runner lists no fixture"
    return fixtures


def _same(fx, mine, runner):
    d, lab = mine.delivery, mine.label
    data = fx.data
    assert (d.id, d.lang, d.half) == (fx.id, fx.lang, data["half"])
    assert (lab.xclass, lab.kind, lab.title) == (data["xclass"], data["kind"], data["title"])
    want = [(e["tool"], e["outcome"], tuple(e["kinds"])) for e in fx.expects()]
    assert [(e.tool, e.outcome, e.kinds) for e in lab.expects] == want
    if fx.runs:
        assert d.target == runner.target_rel(fx)
        assert d.files == tuple(f"{fx.rel}/{f}" for f in data["files"])
    else:
        assert (d.target, d.files) == ("", ())


@pytest.mark.parametrize("lang", corpus.LANGS)
@pytest.mark.parametrize("half", corpus.HALVES)
def test_parity_with_the_corpus_runner(runner, theirs, lang, half):
    want = [fx for fx in theirs if fx.lang == lang and fx.data["half"] == half and fx.runs]
    mine = load_half(lang, half)
    assert [f.id for f in mine] == [fx.id for fx in want]
    for fx, m in zip(want, mine):
        _same(fx, m, runner)


@pytest.mark.parametrize("lang", corpus.LANGS)
@pytest.mark.parametrize("half", corpus.HALVES)
def test_parity_with_covered_rows(runner, theirs, lang, half):
    want = [fx for fx in theirs if fx.lang == lang and fx.data["half"] == half]
    mine = load_half(lang, half, covered=True)
    assert [f.id for f in mine] == [fx.id for fx in want]
    for fx, m in zip(want, mine):
        _same(fx, m, runner)


def test_every_fixture_is_seen_exactly_once(theirs):
    mine = [(f.delivery.lang, f.id) for lang in corpus.LANGS for half in corpus.HALVES
            for f in load_half(lang, half, covered=True)]
    assert len(mine) == len(set(mine))
    assert sorted(mine) == sorted((fx.lang, fx.id) for fx in theirs)


def test_the_runner_vocabulary_matches(runner):
    assert corpus.LANGS == runner.LANGS
    assert corpus.HALVES == runner.HALVES
    assert corpus.KINDS == runner.KINDS


def test_a_delivery_carries_no_label():
    assert [f.name for f in dataclasses.fields(Delivery)] == ["id", "lang", "half", "target",
                                                             "files"]
    assert [f.name for f in dataclasses.fields(Label)] == ["xclass", "kind", "title", "expects"]
    assert [f.name for f in dataclasses.fields(Expect)] == ["tool", "outcome", "kinds"]
    assert [f.name for f in dataclasses.fields(Fixture)] == ["delivery", "label"]
    for half in corpus.HALVES:
        for fx in load_half("dafny", half):
            words = {fx.label.xclass, fx.label.kind, fx.label.title} - {""}
            flat = dataclasses.astuple(fx.delivery)
            assert not words & set(flat), fx.id


def test_fixtures_are_immutable():
    fx = load_half("verus", "Q")[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        fx.delivery.target = "elsewhere"
    with pytest.raises(dataclasses.FrozenInstanceError):
        fx.label.kind = "control"
    assert isinstance(fx.delivery.files, tuple) and isinstance(fx.label.expects, tuple)
    assert fx.id == fx.delivery.id


# ----- synthetic corpora ---------------------------------------------------------------

def manifest(fid, lang="dafny", half="Q", kind="construct", xclass="X01", files=("main.dfy",),
             target=None, expect=(("vaudit", "flagged", ("k",)),), extra=""):
    lines = [f'id = "{fid}"', f'lang = "{lang}"', f'half = "{half}"', f'xclass = "{xclass}"',
             f'kind = "{kind}"', 'title = "an invented line"',
             "files = [" + ", ".join(f'"{f}"' for f in files) + "]"]
    if target is not None:
        lines.append(f'target = "{target}"')
    if kind != "covered-elsewhere":
        lines.append("plain_exit = 0")
    lines.append(extra)
    for tool, outcome, kinds in expect:
        lines += ["", "[[expect]]", f'tool = "{tool}"', f'outcome = "{outcome}"',
                  "kinds = [" + ", ".join(f'"{k}"' for k in kinds) + "]", 'summary = "s"']
    return "\n".join(lines) + "\n"


def put(root, lang, dirname, text, files=()):
    d = root / "tests" / "corpus" / lang / dirname
    d.mkdir(parents=True)
    (d / "manifest.toml").write_text(text, encoding="utf-8")
    for f in files:
        (d / f).parent.mkdir(parents=True, exist_ok=True)
        (d / f).write_text("// invented\n", encoding="utf-8")
    return d


def test_a_synthetic_corpus(tmp_path):
    put(tmp_path, "dafny", "G01", manifest("G01"), ["main.dfy"])
    put(tmp_path, "dafny", "D-2", manifest("D-2", half="R"), ["main.dfy"])
    put(tmp_path, "dafny", "C-01", manifest("C-01", kind="control", xclass="",
                                            files=("main.dfy", "witness.dfy"),
                                            expect=(("witness", "clean", ()),)),
        ["main.dfy", "witness.dfy"])
    put(tmp_path, "dafny", "G07", manifest("G07", kind="covered-elsewhere", files=()))
    put(tmp_path, "verus", "V-1", manifest("V-1", lang="verus", files=("up/Cargo.toml",),
                                           target="up"), ["up/Cargo.toml"])
    put(tmp_path, "verus", "V02", manifest("V02", lang="verus", files=("Cargo.toml",)),
        ["Cargo.toml"])
    q = load_half("dafny", "Q", root=tmp_path)
    assert [f.id for f in q] == ["G01", "C-01"]
    g, c = q
    assert g.delivery == Delivery("G01", "dafny", "Q", "tests/corpus/dafny/G01/main.dfy",
                                  ("tests/corpus/dafny/G01/main.dfy",))
    assert g.label == Label("X01", "construct", "an invented line",
                            (Expect("vaudit", "flagged", ("k",)),))
    assert c.delivery.files == ("tests/corpus/dafny/C-01/main.dfy",
                                "tests/corpus/dafny/C-01/witness.dfy")
    assert [f.id for f in load_half("dafny", "R", root=tmp_path)] == ["D-2"]
    cov = load_half("dafny", "Q", root=tmp_path, covered=True)
    assert [f.id for f in cov] == ["G01", "G07", "C-01"]
    assert cov[1].delivery.target == "" and cov[1].delivery.files == ()
    v = load_half("verus", "Q", root=tmp_path)
    assert [f.id for f in v] == ["V02", "V-1"]
    assert v[0].delivery.target == "tests/corpus/verus/V02"
    assert v[1].delivery.target == "tests/corpus/verus/V-1/up"


def test_bad_arguments_and_an_absent_corpus(tmp_path):
    with pytest.raises(ValueError):
        load_half("lean", "Q", root=tmp_path)
    with pytest.raises(ValueError):
        load_half("dafny", "S", root=tmp_path)
    with pytest.raises(CorpusError):
        load_half("dafny", "Q", root=tmp_path)            # no tests/corpus/
    (tmp_path / "tests" / "corpus").mkdir(parents=True)
    with pytest.raises(CorpusError):
        load_half("dafny", "Q", root=tmp_path)            # no tests/corpus/dafny/


@pytest.mark.parametrize("dirname,text,why", [
    ("G01", None, "missing"),
    ("G01", "id = \n", "unreadable"),
    ("G02", manifest("G01"), "does not name"),
    ("G01", manifest("G01", lang="verus"), "lang"),
    ("G01", manifest("G01", half="S"), "half"),
    ("G01", manifest("G01", kind="decoy"), "kind"),
    ("G01", manifest("G01", target="../G02/main.dfy"), "leaves"),
    ("G01", manifest("G01", expect=()), "no [[expect]]"),
])
def test_a_manifest_that_cannot_be_read_fails_loudly(tmp_path, dirname, text, why):
    d = tmp_path / "tests" / "corpus" / "dafny" / dirname
    d.mkdir(parents=True)
    if text is not None:
        (d / "manifest.toml").write_text(text, encoding="utf-8")
    with pytest.raises(CorpusError, match=None) as e:
        load_half("dafny", "Q", root=tmp_path)
    assert why in str(e.value)
