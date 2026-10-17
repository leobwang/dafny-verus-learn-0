"""The frozen core's own tests: fvh.contract (DV4-PLAN §6, §9; Δ162's open item):
the CONTRACT parser, the allowlist rules and the acceptance-line forms, each
held to scripts/dvl/contract_local.py's on the same cases (every agentic file of
the registry, and synthetic ones), the refused source classes held to
scripts/dvl/sandbox.py's, and the starting-state rules on a throwaway git
repository."""

import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from fvh import contract as C

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def cl():
    scripts = str(ROOT / "scripts")
    sys.path.insert(0, scripts)
    try:
        return importlib.import_module("dvl.contract_local")
    finally:
        sys.path.remove(scripts)


def outcome(fn, *a):
    try:
        return ("ok", fn(*a))
    except Exception as e:                                   # Refused, from either module
        return (type(e).__name__, str(e))


def agentic_files():
    import tomllib
    data = tomllib.loads((ROOT / "MODULES.toml").read_text(encoding="utf-8"))
    out = []
    for m in data["module"]:
        for p in m.get("agentic", []):
            if not p.endswith("/") and (ROOT / p).is_file():
                out.append((m, p))
    return out


GOOD = """/* CONTRACT
goal: refactor the helper
allowed-files:
  - dafny/Q/Q98/a.dfy
acceptance:
  - `scripts/vcheck --gate dafny/Q/Q98/a.dfy` exits 0 and prints only the summary line
  - `scripts/specfreeze --against research/q98_snapshot.dfy dafny/Q/Q98/a.dfy` reports no change
  - re-verify after every edit,
    one full gate run, last
*/
method M() {}
"""

HEADERS = [
    GOOD,
    GOOD.replace("/* CONTRACT", '"""CONTRACT').replace("*/", '"""'),
    GOOD.replace("goal: refactor the helper\n", ""),
    GOOD.replace("goal:", "scope:"),
    GOOD.replace("allowed-files:\n  - dafny/Q/Q98/a.dfy\n", "allowed-files:\n"),
    GOOD.replace("*/\n", ""),
    "method M() {}\n" + GOOD,
    GOOD.replace("acceptance:\n", "acceptance: inline\n"),
    GOOD.replace("goal: refactor the helper\n", "goal: a\ngoal: b\n"),
    GOOD.replace("method M", "stray: line\nmethod M").replace("*/\nstray: line", "stray: line\n*/"),
]


def test_parse_header_agrees_with_contract_local_on_synthetic_headers(cl):
    for h in HEADERS:
        assert outcome(C.parse_header, h) == outcome(cl.parse_header, h)
    assert C.parse_header(GOOD)["acceptance"][2] == "re-verify after every edit, one full gate run, last"


def test_parse_header_agrees_on_every_registry_agentic_file(cl):
    files = agentic_files()
    assert files, "the registry lists agentic files"
    for _, p in files:
        text = (ROOT / p).read_text(encoding="utf-8")
        a, b = outcome(C.parse_header, text), outcome(cl.parse_header, text)
        assert a == b, p
        if a[0] == "ok":
            for line in a[1]["acceptance"]:
                assert C.classify_line(line) == cl.classify_line(line), (p, line)


REC = {"id": "Q98", "agentic": ["dafny/Q/Q98/a.dfy", "dafny/Q/Q98/dir/", "research/q98.md",
                                "harness/q/fvh_q/gate/core.py", "Solutions/x.dfy",
                                "dafny/given/Q/x.dfy", "research/runs/Q98/run.json",
                                "docs/Q98.md", "bench/public/x/tasks/t.dfy",
                                "verus/r/r98/src/trust_report.rs", "dafny/Q/Q98/Cargo.toml"]}
PATHS = REC["agentic"] + ["dafny/Q/Q98/dir/b.dfy", "dafny/Q/Q98/other.dfy", "/abs.dfy",
                          "./dafny/Q/Q98/a.dfy", "dafny/Q/../Q98/a.dfy", "dafny/Q/Q98/*.dfy",
                          "research/ledger-heads.jsonl", "MODULES.toml", "x.pth"]


def test_path_problem_agrees(cl):
    for p in PATHS:
        assert C.path_problem(p, REC) == cl.path_problem(p, REC), p
    assert C.path_problem("dafny/Q/Q98/a.dfy", REC) is None
    assert C.path_problem("research/runs/Q98/run.json", REC) is not None
    assert C.path_problem("research/q98.md", REC) is None


LINES = [
    "`scripts/vcheck --gate dafny/Q/Q98/a.dfy` exits 0",
    "`scripts/vcheck --gate dafny/Q/Q98/a.dfy` passes",
    "`scripts/specfreeze --against research/s.dfy dafny/Q/Q98/a.dfy` reports no change",
    "`scripts/vaudit dafny/Q/Q98/a.dfy` reports no finding",
    "`scripts/vaudit --compare expected/Q98.audit dafny/Q/Q98/a.dfy` reports no difference",
    "zero holes remain",
    "`git diff` against the committed snapshot changes only the helper",
    "re-verify after every edit",
]


def test_classify_line_agrees(cl):
    for line in LINES:
        assert C.classify_line(line) == cl.classify_line(line), line
    assert [C.classify_line(x)[0] for x in LINES] == [
        "vcheck-gate", "audit", "specfreeze-against", "vaudit", "vaudit-compare", "zero-holes",
        "git-diff", "audit"]


def test_the_refused_classes_equal_the_sandbox_table(cl):
    assert C.REFUSED_CLASSES == cl.sandbox.REFUSED_CLASSES


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@example.invalid", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.run(["git", "-C", str(root), *args], check=True, env=env,
                          capture_output=True, text=True).stdout.strip()


def test_the_starting_state(tmp_path, cl):
    root = tmp_path
    git(root, "init", "-q")
    (root / "dafny/Q/Q98").mkdir(parents=True)
    (root / "research").mkdir()
    (root / "dafny/Q/Q98/a.dfy").write_text("v1\n")
    (root / "research/q98_snapshot.dfy").write_text("snap\n")
    git(root, "add", ".")
    git(root, "commit", "-qm", "snapshot")
    snap_rev = git(root, "rev-parse", "HEAD")
    (root / "dafny/Q/Q98/a.dfy").write_text("v2 (the agent's work)\n")
    git(root, "commit", "-qam", "after")
    c = C.parse_header(GOOD)
    c["acceptance"][1] = c["acceptance"][1].replace("research/s.dfy", "research/q98_snapshot.dfy")
    assert C.starting_state(root, c) == (snap_rev, "research/q98_snapshot.dfy")
    assert outcome(C.starting_state, root, c, None) == outcome(cl.starting_state, root, c, None)
    head = git(root, "rev-parse", "HEAD")
    assert C.starting_state(root, c, "HEAD")[0] == head
    none = {**c, "acceptance": ["re-verify after every edit"]}
    for case in ((none, None), (c, "no-such-rev")):
        a = outcome(C.starting_state, root, *case)
        assert a[0] == "Refused" and a == outcome(cl.starting_state, root, *case)
    (root / "research/q98_snapshot.dfy").write_text("changed\n")
    with pytest.raises(C.Refused, match="differs from its committed"):
        C.starting_state(root, c)


def test_record_reads_the_registry(tmp_path):
    (tmp_path / "MODULES.toml").write_text('[[module]]\nid = "Q98"\nagentic = []\n')
    assert C.record(tmp_path, "q98")["id"] == "Q98"
    with pytest.raises(C.Refused):
        C.record(tmp_path, "Q97")
