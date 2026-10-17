"""The frozen core's own tests: the author-only recorder `python -m fvh.tools.record`
(DV4-PLAN §3.7, §9): its three-condition self-gate and what it writes, on
throwaway roots.

No solver runs here: the throwaway roots hold fake course tools (the ones of
test_tools.py) and an invented corpus (no course content). No test records
into the real course tree.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from fvh import tools
from fvh.tools import HostRunner, record
from fvh.tools import runners as R

from test_tools import FAKE_TOOL

HARNESS = Path(__file__).resolve().parents[2]
GIT_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")


def git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if k not in GIT_VARS}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_AUTHOR_NAME="t",
               GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@example.invalid")
    subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True,
                   stdin=subprocess.DEVNULL)


def repo(tmp_path, branch="authoring"):
    """(primary checkout, linked worktree on `branch`)."""
    main = tmp_path / "main"
    main.mkdir()
    git(main, "init", "-q", "-b", "main")
    git(main, "commit", "-q", "--allow-empty", "-m", "invented")
    wt = tmp_path / "wt"
    git(main, "worktree", "add", "-q", str(wt), "-b", branch)
    return main, wt


@pytest.fixture
def no_ci(monkeypatch, tmp_path):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("DVL_SCRATCH", str(tmp_path / "scratch"))


# ----- the self-gate ----------------------------------------------------------------------

def test_ci_true_passes_the_gate(monkeypatch, tmp_path):
    monkeypatch.setenv("CI", "true")
    assert record.author_gate(tmp_path) is None


def test_the_three_conditions(no_ci, tmp_path):
    assert record.author_gate(tmp_path) == "not inside a git checkout"
    main, wt = repo(tmp_path)
    assert record.author_gate(main) == "this is the primary worktree"
    assert record.author_gate(wt) is None
    sub = wt / "nested"
    sub.mkdir()
    assert record.author_gate(sub) == "not inside a git checkout"   # discovery stops at root


def test_a_learner_branch_is_refused(no_ci, tmp_path):
    _, wt = repo(tmp_path, branch="leobwang-study")
    assert record.author_gate(wt) == "HEAD is on a learner branch"


def test_the_learner_prefix_comes_from_course_mode(no_ci, tmp_path):
    _, wt = repo(tmp_path, branch="pupil-1")
    assert record.author_gate(wt) is None
    (wt / "scripts").mkdir()
    (wt / "scripts" / "course_mode.sh").write_text('#!/bin/sh\nLEARNER_PREFIX="pupil-"\n')
    assert record.learner_prefix(wt) == "pupil-"
    assert record.author_gate(wt) == "HEAD is on a learner branch"


def test_outside_the_authors_context_nothing_runs(no_ci, tmp_path, capsys):
    root = tmp_path / "plain"
    build(root)
    assert record.main(["--half", "Q"], root=root, runner=HostRunner(root, preflight=False)) == 3
    assert "author-only" in capsys.readouterr().err
    assert not (root / "calls.jsonl").exists()
    assert not (root / tools.FIXTURES).exists()


def test_the_command_line_refuses_outside_the_authors_context(tmp_path):
    copy = tmp_path / "harness"
    shutil.copytree(HARNESS / "fvh", copy / "fvh",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    env = {k: v for k, v in os.environ.items() if k not in ("CI", "PYTHONPATH", *GIT_VARS)}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(copy))
    p = subprocess.run([sys.executable, "-B", "-m", "fvh.tools.record", "--half", "Q"],
                       cwd=copy, env=env, capture_output=True, text=True, timeout=120,
                       stdin=subprocess.DEVNULL)
    assert p.returncode == 3, p.stderr
    assert "refused" in p.stderr and "author-only" in p.stderr
    assert not (tmp_path / tools.FIXTURES).exists()


# ----- recording on a throwaway author root -----------------------------------------------

def manifest(fid, lang, half, kind, xclass, files, tools_listed, title):
    lines = [f'id = "{fid}"', f'lang = "{lang}"', f'half = "{half}"', f'xclass = "{xclass}"',
             f'kind = "{kind}"', f'title = "{title}"',
             "files = [" + ", ".join(f'"{f}"' for f in files) + "]"]
    if kind != "covered-elsewhere":
        lines.append("plain_exit = 0")
    for t in tools_listed:
        lines += ["", "[[expect]]", f'tool = "{t}"',
                  f'outcome = "{"clean" if kind == "control" else "flagged"}"',
                  'kinds = ["invented-kind"]', 'summary = "invented"']
    return "\n".join(lines) + "\n"


CORPUS = [
    # (lang, id, half, kind, xclass, files, listed tools, title)
    ("dafny", "G01", "Q", "construct", "X01", ["main.dfy", "witness.dfy", "swap.dfy"],
     ["vaudit"], "an invented construct"),
    ("dafny", "C-01", "Q", "control", "", ["main.dfy"], ["vcheck --gate", "witness"],
     "an invented control"),
    ("dafny", "G07", "Q", "covered-elsewhere", "X10", [], ["vcheck --gate"],
     "an invented covered row"),
    ("dafny", "D-2", "R", "construct", "X03", ["main.dfy"], ["vaudit"], "an invented R row"),
    ("verus", "V01", "Q", "construct", "X02",
     ["Cargo.toml", "src/lib.rs", "frozen.rs", "witness/Cargo.toml"], ["vcheck --gate"],
     "an invented crate"),
]


def build(root):
    for lang, fid, half, kind, xclass, files, listed, title in CORPUS:
        d = root / "tests" / "corpus" / lang / fid
        d.mkdir(parents=True)
        (d / "manifest.toml").write_text(manifest(fid, lang, half, kind, xclass, files, listed,
                                                  title))
        for f in files:
            (d / f).parent.mkdir(parents=True, exist_ok=True)
            (d / f).write_text("// invented\n")
    (root / "scripts").mkdir(exist_ok=True)
    for tool in ("vcheck", "vaudit", "specfreeze"):
        (root / "scripts" / tool).write_text(FAKE_TOOL)
    return root


def author_root(tmp_path):
    _, wt = repo(tmp_path)
    return build(wt)


def recorded(root):
    base = root / tools.FIXTURES
    return sorted(p.relative_to(base).as_posix() for p in base.rglob("*.json"))


def go(root, *args):
    return record.main(["--half", "Q", *args], root=root, runner=HostRunner(root, preflight=False))


def test_the_recorder_writes_results_only(no_ci, tmp_path):
    root = author_root(tmp_path)
    assert go(root) == 0
    assert recorded(root) == [
        "dafny/C-01/seed-rerun.json", "dafny/C-01/vaudit.json", "dafny/C-01/vcheck-gate.json",
        "dafny/G01/seed-rerun.json", "dafny/G01/swap-to-false.json", "dafny/G01/vaudit.json",
        "dafny/G01/vcheck-gate.json", "dafny/G01/witness.json",
        "verus/V01/seed-rerun.json", "verus/V01/specfreeze-check.json",
        "verus/V01/vaudit.json", "verus/V01/vcheck-gate.json", "verus/V01/witness.json"]
    for rel in recorded(root):
        text = (root / tools.FIXTURES / rel).read_text()
        for word in ("X01", "X02", "construct", "control", "invented-kind", "flagged",
                     "clean", "an invented", "xclass", "outcome"):
            assert word not in text, (rel, word)
    r = tools.replay("G01", "witness", root=root)
    assert (r.runner, r.exit_code, r.provenance, r.target) == \
        ("replay", 0, "course", "tests/corpus/dafny/G01/main.dfy")
    rec = json.loads((root / tools.FIXTURES / "dafny/G01/witness.json").read_text())
    assert rec["argv"] == ["scripts/vcheck", "--json", "--gate",
                           "tests/corpus/dafny/G01/witness.dfy"]
    assert rec["document"]["target"] == "<root>/tests/corpus/dafny/G01/witness.dfy"
    via_run = tools.run("seed-rerun", "tests/corpus/verus/V01", root=root,
                        runner=tools.ReplayRunner(root=root))
    assert via_run.document == tools.replay("V01", "seed-rerun", root=root).document


def test_selection_and_narrowing(no_ci, tmp_path):
    root = author_root(tmp_path)
    assert go(root, "--only", "C-01", "--instrument", "vaudit") == 0
    assert recorded(root) == ["dafny/C-01/vaudit.json"]
    assert go(root, "--only", "dafny/C-01", "--instrument", "vcheck --gate") == 0
    assert recorded(root) == ["dafny/C-01/vaudit.json", "dafny/C-01/vcheck-gate.json"]
    assert go(root, "--lang", "verus", "--instrument", "witness") == 0
    assert "verus/V01/witness.json" in recorded(root)
    assert not any(r.startswith("dafny/G01") for r in recorded(root))
    assert go(root, "--only", "D-2") == 2                 # an R row: not in half Q
    assert go(root, "--only", "G99") == 2
    assert go(root, "--instrument", "lint") == 2


def test_a_dry_run_runs_nothing(no_ci, tmp_path, capsys):
    root = author_root(tmp_path)
    assert go(root, "--dry-run") == 0
    out = capsys.readouterr().out
    assert "PLAN   dafny/G01: vcheck --gate, vaudit, witness, swap-to-false, seed-rerun" in out
    assert not (root / "calls.jsonl").exists() and not (root / tools.FIXTURES).exists()


def test_kills_and_refusals_are_never_recorded(no_ci, tmp_path, capsys):
    root = author_root(tmp_path)
    (root / "fake-control.json").write_text(json.dumps({
        "vaudit tests/corpus/dafny/G01/main.dfy": {"exit": 137},
        "vcheck --brittleness tests/corpus/dafny/C-01/main.dfy": {"exit": 3, "text": True}}))
    assert go(root, "--lang", "dafny") == 1
    out = capsys.readouterr().out
    assert "FAIL   dafny/G01: vaudit: killed (memory)" in out
    assert "FAIL   dafny/C-01: seed-rerun: exit 3" in out
    got = recorded(root)
    assert "dafny/G01/vaudit.json" not in got and "dafny/C-01/seed-rerun.json" not in got
    assert "dafny/G01/witness.json" in got


def test_stale_results_are_removed_after_a_full_recording(no_ci, tmp_path):
    root = author_root(tmp_path)
    stale = root / tools.FIXTURES / "dafny" / "C-01" / "witness.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}")
    assert go(root, "--only", "C-01", "--instrument", "vaudit") == 0
    assert stale.exists()                                 # a narrowed run removes nothing
    assert go(root, "--only", "C-01") == 0
    assert not stale.exists()


def test_where_it_writes(no_ci, tmp_path):
    root = author_root(tmp_path)
    assert go(root, "--out", str(tmp_path / "elsewhere")) == 3
    assert record.main(["--half", "R"], root=root,
                       runner=HostRunner(root, preflight=False)) == 2
    assert record.main(["--half", "R", "--out", "build/r13"], root=root,
                       runner=HostRunner(root, preflight=False)) == 0
    assert sorted(p.name for p in (root / "build" / "r13" / "dafny" / "D-2").iterdir()) == \
        ["seed-rerun.json", "vaudit.json", "vcheck-gate.json"]


def test_the_memory_preflight_runs_first(no_ci, tmp_path, monkeypatch, capsys):
    root = author_root(tmp_path)
    (root / "scripts" / "dvl").mkdir()
    (root / "scripts" / "dvl" / "pins.toml").write_text("[dafny]\nmem_gb = 8\n[verus]\n"
                                                        "mem_gb = 16\n")
    monkeypatch.setattr(R, "mem_available_gb", lambda: 20)
    assert record.main(["--half", "Q", "--lang", "dafny"], root=root) == 1
    assert "23 GB needed" in capsys.readouterr().err
    assert not (root / "calls.jsonl").exists()
