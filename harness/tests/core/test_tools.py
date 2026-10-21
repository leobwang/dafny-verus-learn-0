"""The frozen core's own tests: fvh.tools, the instrument runners and the
provenance rule (DV4-PLAN §3.7, §9).

No solver runs here. The HostRunner tests run on a throwaway course root whose
scripts/vcheck, scripts/vaudit and scripts/specfreeze are fakes that report
their argv and environment; the registry, corpus and files there are invented
(module id Q98, no course content). The parity tests compare the instrument
commands with scripts/test_corpus.py's on the real corpus.
"""

import ast
import dataclasses
import importlib.machinery
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

import pytest

from fvh import corpus, tools
from fvh.tools import (INSTRUMENTS, ContainerRunner, HostRunner, NoRecording, PreflightError,
                       ProvenanceError, ReplayRunner, Runner, RunnerUnavailable, ToolResult)
from fvh.tools import runners as R

ROOT = Path(__file__).resolve().parents[3]
HARNESS = ROOT / "harness"
SHA = "0" * 64

FAKE_TOOL = r'''
import json, os, pathlib, subprocess, sys, time
here = pathlib.Path(__file__).resolve()
root = here.parents[1]
tool, args = here.name, sys.argv[1:]
ctl_path = root / "fake-control.json"
ctl = json.loads(ctl_path.read_text()) if ctl_path.exists() else {}
beh = ctl.get(tool + " " + " ".join(a for a in args if a != "--json"), ctl.get(tool, {}))
with (root / "calls.jsonl").open("a") as fh:
    fh.write(json.dumps({"tool": tool, "argv": args, "cwd": os.getcwd(),
                         "env": {k: os.environ.get(k) for k in (
                             "CI", "DVL_SCRATCH", "DVL_DAFNY_JOBS", "DVL_VERUS_JOBS",
                             "PYTHONDONTWRITEBYTECODE")}}) + "\n")
scratch = os.environ.get("DVL_SCRATCH", "")
pathlib.Path(scratch, "run-7").mkdir()
if beh.get("child"):
    c = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    (root / "child.pid").write_text(str(c.pid))
if beh.get("sleep"):
    time.sleep(beh["sleep"])
if "--json" in args and not beh.get("text"):
    print(json.dumps({"verdict": beh.get("verdict", "verified"),
                      "exit_code": beh.get("doc_exit", 0), "target": str(root / args[-1]),
                      "raw_dir": scratch + "/run-7/raw", "home": os.environ["HOME"] + "/notes",
                      "elsewhere": "/usr/lib/x86_64/thing.so", "holes": []}))
else:
    print(f"{tool}: {args[-1]}: {beh.get('say', 'ok')}  ")
    print("raw output: " + scratch + "/run-9/raw")
if beh.get("stderr"):
    print(beh["stderr"], file=sys.stderr)
sys.exit(beh.get("exit", 0))
'''

REGISTRY = '''schema = 1

[[module]]
id = "Q98"
exercises = ["dafny/Q/Q98_Toy/core/Q98_Toy.dfy", "dafny/checks/Q98_checks.dfy",
             "verus/q/q98_toy/src/lib.rs", "specimens/Q98/"]
exits = ["dafny/Q/Q98_Toy/exit/Q98_Exit.dfy", "verus/q/q98_toy/src/exit.rs"]
agentic = ["dafny/Q/Q98_Toy/agent/Q98_Agent.dfy"]
harness = ["harness/q/fvh_q/q98_toy.py"]
units = ["dafny/Q/Q98_Toy/core", "verus/q/q98_toy"]
statements = [{ path = "Challenges/Toy/ToyStatement.dfy", sha256 = "PENDING" }]

[module.imports]
"dafny/given/Q/QG_L1_Toy.dfy" = "core"
"verus/given/qg_toy/src/lib.rs" = "prelude"
"dafny/Q/Q98_Toy/core/Q98_Toy.dfy" = "core"
'''

FILES = [
    "tests/corpus/dafny/G01/main.dfy", "tests/corpus/dafny/G01/witness.dfy",
    "tests/corpus/dafny/G01/swap.dfy", "tests/corpus/dafny/G01/frozen.dfy",
    "tests/corpus/verus/V01/Cargo.toml", "tests/corpus/verus/V01/src/lib.rs",
    "tests/corpus/verus/V01/witness/Cargo.toml", "tests/corpus/verus/V01/swapped/Cargo.toml",
    "tests/corpus/verus/V01/frozen.rs", "harness/tests/q/fixtures/extra/x.dfy",
    "dafny/given/Q/QG_L1_Toy.dfy", "verus/given/qg_toy/Cargo.toml",
    "verus/given/qg_toy/src/lib.rs", "dafny/Q/Q98_Toy/core/Q98_Toy.dfy",
    "dafny/Q/Q98_Toy/exit/Q98_Exit.dfy", "dafny/Q/Q98_Toy/agent/Q98_Agent.dfy",
    "dafny/checks/Q98_checks.dfy", "verus/q/q98_toy/Cargo.toml", "verus/q/q98_toy/src/lib.rs",
    "specimens/Q98/P1d.dfy.specimen", "harness/q/fvh_q/q98_toy.py",
    "Challenges/Toy/ToyStatement.dfy", "Challenges/Toy/Toy.dfy",
    "research/runs/Q98/r1/returned/x.dfy", "notes/undeclared.dfy", "dafny/given/Q/QG_L9.dfy",
]


def make_root(tmp_path):
    root = tmp_path / "root"
    for f in FILES:
        (root / f).parent.mkdir(parents=True, exist_ok=True)
        (root / f).write_text("// invented\n", encoding="utf-8")
    (root / "MODULES.toml").write_text(REGISTRY, encoding="utf-8")
    (root / "scripts").mkdir()
    for tool in ("vcheck", "vaudit", "specfreeze"):
        (root / "scripts" / tool).write_text(FAKE_TOOL, encoding="utf-8")
    return root


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setenv("DVL_SCRATCH", str(tmp_path / "scratch"))
    monkeypatch.setenv("HOME", "/home/someone-else")
    return make_root(tmp_path)


def control(root, table):
    (root / "fake-control.json").write_text(json.dumps(table), encoding="utf-8")


def calls(root):
    return [json.loads(x) for x in (root / "calls.jsonl").read_text().splitlines()]


def host(root):
    return HostRunner(root, preflight=False)


@pytest.fixture(scope="module")
def runner_mod():
    saved = list(sys.path)
    try:
        path = ROOT / "scripts" / "test_corpus.py"
        loader = importlib.machinery.SourceFileLoader("dvl0_corpus_runner_tools", str(path))
        spec = importlib.util.spec_from_loader("dvl0_corpus_runner_tools", loader)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["dvl0_corpus_runner_tools"] = mod          # its dataclasses look the module up
        loader.exec_module(mod)
    finally:
        sys.path[:] = saved
    return mod


# ----- instruments and commands ----------------------------------------------------------

def test_instruments_are_the_corpus_readme_names(runner_mod):
    assert INSTRUMENTS == ("vcheck --gate", "vaudit", "specfreeze --check", "witness",
                           "swap-to-false", "seed-rerun", "solver-swap", "reach")
    not_runnable = {"lint", "json-completeness"}       # README: read elsewhere, never run
    assert INSTRUMENTS == tuple(t for t in runner_mod.TOOLS if t not in not_runnable)
    readme = (ROOT / "tests" / "corpus" / "README.md").read_text(encoding="utf-8")
    section = readme.split("## Instruments", 1)[1].split("\n## ", 1)[0]
    table = re.findall(r"^\| `([^`]+)` \|", section, re.M)
    assert tuple(t for t in table if t not in not_runnable) == INSTRUMENTS


def test_slugs_are_file_safe_and_distinct():
    slugs = [tools.slug(i) for i in INSTRUMENTS]
    assert slugs == ["vcheck-gate", "vaudit", "specfreeze-check", "witness", "swap-to-false",
                     "seed-rerun", "solver-swap", "reach"]
    with pytest.raises(ValueError):
        tools.slug("lint")


def test_commands_match_the_corpus_runner_on_every_fixture(runner_mod):
    fixtures, problems = runner_mod.load_corpus()
    assert not problems
    by_key = {(fx.lang, fx.id): fx for fx in fixtures}
    n = 0
    for lang in corpus.LANGS:
        for half in corpus.HALVES:
            for f in corpus.load_half(lang, half):
                fx = by_key[(lang, f.id)]
                d = f.delivery
                listed = {e.tool for e in f.label.expects} & set(INSTRUMENTS)
                for inst in INSTRUMENTS:
                    try:
                        paths = R._input_paths(inst, d.target, lang=d.lang)
                    except ValueError:
                        assert inst not in listed
                        continue
                    present = all((ROOT / p).exists() for p in paths)
                    assert present or inst not in listed, (f.id, inst)
                    if present:
                        assert tools.command(inst, d.target, lang=d.lang) == \
                            runner_mod.command(fx, inst), (f.id, inst)
                        n += 1
    assert n > 100


def test_the_host_argv_adds_json_where_the_tool_has_it(tmp_path):
    h = HostRunner(tmp_path, preflight=False)
    t = "tests/corpus/dafny/X/main.dfy"
    assert h.argv("vcheck --gate", t) == ["scripts/vcheck", "--json", "--gate", t]
    assert h.argv("vaudit", t) == ["scripts/vaudit", "--json", t]
    assert h.argv("seed-rerun", t) == ["scripts/vcheck", "--json", "--brittleness", t]
    assert h.argv("witness", t) == ["scripts/vcheck", "--json", "--gate",
                                    "tests/corpus/dafny/X/witness.dfy"]
    assert h.argv("swap-to-false", t) == ["scripts/vcheck", "--json", "--gate",
                                          "tests/corpus/dafny/X/swap.dfy"]
    assert h.argv("specfreeze --check", t) == ["scripts/specfreeze", "--against",
                                               "tests/corpus/dafny/X/frozen.dfy", t]
    v = "tests/corpus/verus/Y"
    assert h.argv("witness", v)[-1] == f"{v}/witness"
    assert h.argv("swap-to-false", v)[-1] == f"{v}/swapped"
    assert h.argv("specfreeze --check", v)[2:] == [f"{v}/frozen.rs", f"{v}/src/lib.rs"]
    with pytest.raises(ValueError):
        tools.command("witness", "verus/q/x/src/lib.rs")
    with pytest.raises(ValueError):
        tools.command("json-completeness", t)


# ----- the provenance rule ---------------------------------------------------------------

@pytest.mark.parametrize("path,want", [
    ("tests/corpus/dafny/G01/main.dfy", "course"),
    ("tests/corpus/verus/V01", "course"),
    ("harness/tests/q/fixtures/extra/x.dfy", "course"),
    ("dafny/given/Q/QG_L1_Toy.dfy", "course"),
    ("verus/given/qg_toy", "course"),
    ("verus/given/qg_toy/src/lib.rs", "course"),
    ("Challenges/Toy/ToyStatement.dfy", "course"),
    ("dafny/Q/Q98_Toy/core/Q98_Toy.dfy", "learner"),
    ("dafny/Q/Q98_Toy/core", "learner"),
    ("dafny/Q/Q98_Toy/exit/Q98_Exit.dfy", "learner"),
    ("dafny/Q/Q98_Toy/agent/Q98_Agent.dfy", "learner"),
    ("dafny/checks/Q98_checks.dfy", "learner"),
    ("verus/q/q98_toy", "learner"),
    ("specimens/Q98/P1d.dfy.specimen", "learner"),
    ("harness/q/fvh_q/q98_toy.py", "learner"),
    ("research/runs/Q98/r1/returned/x.dfy", "agent"),
    ("notes/undeclared.dfy", "agent"),
    ("dafny/given/Q/QG_L9.dfy", "agent"),             # a given path no record declares
    ("Challenges/Toy/Toy.dfy", "agent"),
    ("tests/corpus/../research/runs/Q98/r1/returned/x.dfy", "agent"),
    (".", "agent"),
])
def test_the_provenance_rule(root, path, want):
    assert tools.provenance_of(path, root=root) == want
    assert tools.provenance_of(root / path, root=root) == want


def test_paths_outside_the_root_are_agent(root, tmp_path):
    outside = tmp_path / "elsewhere.dfy"
    outside.write_text("// invented\n")
    assert tools.provenance_of(outside, root=root) == "agent"
    assert tools.provenance_of("/tmp", root=root) == "agent"


def test_the_real_path_decides(root):
    (root / "research" / "link-to-corpus.dfy").symlink_to(root / "tests/corpus/dafny/G01/main.dfy")
    (root / "tests" / "corpus" / "dafny" / "G01" / "planted.dfy").symlink_to(
        root / "research/runs/Q98/r1/returned/x.dfy")
    (root / "tests" / "corpus" / "dafny" / "G02").symlink_to(root / "research")
    assert tools.provenance_of("research/link-to-corpus.dfy", root=root) == "course"
    assert tools.provenance_of("tests/corpus/dafny/G01/planted.dfy", root=root) == "agent"
    assert tools.provenance_of("tests/corpus/dafny/G02/runs", root=root) == "agent"


def test_without_a_registry_only_the_course_trees_run_on_the_host(root):
    (root / "MODULES.toml").unlink()
    assert tools.provenance_of("tests/corpus/dafny/G01/main.dfy", root=root) == "course"
    assert tools.provenance_of("dafny/Q/Q98_Toy/core/Q98_Toy.dfy", root=root) == "agent"
    (root / "MODULES.toml").write_text("this is [ not toml", encoding="utf-8")
    assert tools.provenance_of("dafny/given/Q/QG_L1_Toy.dfy", root=root) == "agent"


def test_the_real_course_tree():
    assert tools.provenance_of("tests/corpus/dafny/G01/main.dfy") == "course"
    assert tools.provenance_of("research/anything.dfy") == "agent"
    assert tools.provenance_of("README.md") == "agent"


# ----- run(): the routing ----------------------------------------------------------------

class Isolated(Runner):
    name = "replay"
    isolated = True

    def __init__(self):
        self.seen = []

    def execute(self, instrument, target, *, timeout_s=None):
        self.seen.append((instrument, target, timeout_s))
        return ToolResult(instrument, "t", {"exit_code": 0, "lines": []}, 0, None, "replay",
                          "course", SHA)


def test_an_agent_target_never_runs_on_the_host(root):
    t = "research/runs/Q98/r1/returned/x.dfy"
    with pytest.raises(ProvenanceError):
        tools.run("vcheck --gate", t, root=root, runner=host(root))
    with pytest.raises(ProvenanceError):
        host(root).execute("vcheck --gate", t)
    with pytest.raises(ProvenanceError):
        tools.run("vcheck --gate", t, root=root, runner=Isolated.__base__())
    with pytest.raises(RunnerUnavailable):
        tools.run("vcheck --gate", t, root=root)          # the default: the container
    assert not (root / "calls.jsonl").exists()


def test_an_isolated_runner_takes_an_agent_target(root):
    iso = Isolated()
    res = tools.run("vaudit", "research/runs/Q98/r1/returned/x.dfy", root=root, runner=iso,
                    timeout_s=5)
    assert iso.seen == [("vaudit", str(root / "research/runs/Q98/r1/returned/x.dfy"), 5)]
    assert res.provenance == "agent"


def test_a_provenance_is_raised_never_lowered(root):
    t = "tests/corpus/dafny/G01/main.dfy"
    with pytest.raises(RunnerUnavailable):
        tools.run("vcheck --gate", t, root=root, provenance="agent")
    with pytest.raises(ProvenanceError):
        tools.run("vcheck --gate", t, root=root, runner=host(root), provenance="agent")
    assert tools.run("vcheck --gate", t, root=root, runner=Isolated(),
                     provenance="learner").provenance == "learner"
    with pytest.raises(ProvenanceError):
        tools.run("vcheck --gate", "notes/undeclared.dfy", root=root, runner=Isolated(),
                  provenance="course")
    with pytest.raises(ProvenanceError):
        tools.run("vcheck --gate", "dafny/Q/Q98_Toy/core/Q98_Toy.dfy", root=root,
                  runner=Isolated(), provenance="course")
    with pytest.raises(ValueError):
        tools.run("vcheck --gate", t, root=root, runner=Isolated(), provenance="trusted")


def test_run_checks_its_arguments_and_the_runners_answer(root):
    with pytest.raises(ValueError):
        tools.run("lint", "tests/corpus/dafny/G01/main.dfy", root=root, runner=Isolated())

    class Bad(Isolated):
        def execute(self, instrument, target, *, timeout_s=None):
            return {"exit_code": 0}

    class Wrong(Isolated):
        def execute(self, instrument, target, *, timeout_s=None):
            return ToolResult("vaudit", "t", {}, 0, None, "replay", "course", SHA)

    with pytest.raises(TypeError):
        tools.run("vaudit", "tests/corpus/dafny/G01/main.dfy", root=root, runner=Bad())
    with pytest.raises(ValueError):
        tools.run("witness", "tests/corpus/dafny/G01/main.dfy", root=root, runner=Wrong())


FAKE_MKSANDBOX = r'''
import json, pathlib, sys
here = pathlib.Path(__file__).resolve()
root = here.parents[1]
ctl_path = root / "fake-mk.json"
ctl = json.loads(ctl_path.read_text()) if ctl_path.exists() else {}
args = sys.argv[1:]
with (root / "mk-calls.jsonl").open("a") as fh:
    fh.write(json.dumps(args) + "\n")
if args[0] == "--build-verify":
    argv = json.loads(args[args.index("--argv") + 1])
    print(json.dumps({"target": ctl.get("target", argv[-1]),
                      "manifest": {"schema": 1, "command": [{"argv": argv}]}}))
    sys.exit(ctl.get("build_exit", 0))
recs = pathlib.Path(args[args.index("--records") + 1])
if ctl.get("stderr"):
    print(ctl["stderr"], file=sys.stderr)
if ctl.get("records", True):
    recs.mkdir(parents=True)
    doc = {"verdict": "verified", "exit_code": 0, "holes": [],
           "target": "/work/" + ctl.get("target", "x"),
           "raw_dir": "/tmp/dvl-scratch/runs/dafny-verify-1/raw"}
    cmd = {"argv": [], "exit_code": ctl.get("rc", 0), "killed": ctl.get("killed"),
           "stdout": json.dumps(doc), "stderr": ""}
    (recs / "run.json").write_text(json.dumps(
        {"root": "/work", "scratch": "/tmp/dvl-scratch", "ended_by": ctl.get("ended_by", "done"),
         "commands": [] if ctl.get("no_commands") else [cmd]}))
sys.exit(ctl.get("exit", 0))
'''


def fake_mk(root, ctl=None):
    (root / "scripts" / "mksandbox-run").write_text(FAKE_MKSANDBOX, encoding="utf-8")
    (root / "fake-mk.json").write_text(json.dumps(ctl or {}), encoding="utf-8")


def mk_calls(root):
    p = root / "mk-calls.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


def test_the_container_runner_refuses_without_docker(root, monkeypatch):
    fake_mk(root)
    monkeypatch.setenv("DVL_NO_DOCKER", "1")
    c = ContainerRunner(root)
    assert c.isolated and c.name == "container"
    with pytest.raises(RunnerUnavailable):
        c.execute("vcheck --gate", "tests/corpus/dafny/G01/main.dfy")
    assert mk_calls(root) == []


def test_the_container_runner_reads_the_course_path_of_a_work_copy(root, tmp_path, monkeypatch):
    monkeypatch.delenv("DVL_NO_DOCKER", raising=False)
    rel = "dafny/Q/Q98_Toy/agent/Q98_Agent.dfy"
    fake_mk(root, {"target": rel})
    work = tmp_path / "work-abc"
    (work / rel).parent.mkdir(parents=True)
    (work / rel).write_text("// a work copy\n")
    c = ContainerRunner(root, mem_gb=16)
    assert c.course_rel(work / rel) == rel
    res = tools.run("vcheck --gate", work / rel, root=root, runner=c, provenance="agent")
    assert (res.runner, res.target, res.provenance, res.exit_code, res.killed) == \
        ("container", rel, "agent", 0, None)
    assert res.document["target"] == "<root>/" + rel
    assert res.document["raw_dir"] == "<scratch>"
    build, run = mk_calls(root)
    assert build[:3] == ["--build-verify", "--target", str(work / rel)]
    assert json.loads(build[build.index("--argv") + 1]) == ["scripts/vcheck", "--json", "--gate", rel]
    assert build[build.index("--mem-gb") + 1] == "16"
    assert run[0] == "--records" and run[-1].endswith("manifest.json")
    with pytest.raises(RunnerUnavailable):
        c.course_rel(tmp_path / "elsewhere" / "nothing.dfy")
    assert c.course_rel(root / "research/runs/Q98/r1/returned" / rel) == rel
    # benchmark tasks: a stratum's tasks/ and a lab card's (Lab 1's and Lab 2's layout)
    for bench in ("bench/public/humaneval-dafny/tasks/t1.dfy", "bench/local/q/lab9/tasks/a.dfy",
                  "bench/local/q/lab2/oracle/tasks/tmp1.dfy",
                  "bench/local/r/lab1/c01/tasks/c01.rs"):
        assert c.course_rel(tmp_path / "q15-oracle-x" / bench) == bench
    with pytest.raises(RunnerUnavailable):
        c.course_rel(tmp_path / "x" / "bench/local/q/lab2/a/b/tasks/deep.dfy")


def test_a_plant_copied_from_a_fixture_crate_has_no_container_route(root, tmp_path):
    """gate_v2.main's docstring (DV5d): a plant outside the tree runs in the
    container only when its path ends with a course crate's path; a copy of a
    gate fixture crate (harness/tests/q/fixtures/q18/K1, declared by no
    registry entry) raises RunnerUnavailable before any container is built."""
    c = ContainerRunner(root)
    assert c.course_rel(tmp_path / "plant" / "verus/q/q98_toy") == "verus/q/q98_toy"
    assert c.course_rel(tmp_path / "plant" / "verus/q/q98_toy/src/lib.rs") == \
        "verus/q/q98_toy/src/lib.rs"
    for copy in ("plant/harness/tests/q/fixtures/q18/K1", "plant/tests/q/fixtures/q18/K1",
                 "plant/K1/src/lib.rs"):
        with pytest.raises(RunnerUnavailable, match="no suffix of the path is a course file"):
            c.course_rel(tmp_path / copy)
    assert mk_calls(root) == []


def test_the_container_runner_maps_kills_refusals_and_deferrals(root, monkeypatch):
    monkeypatch.delenv("DVL_NO_DOCKER", raising=False)
    t = "dafny/Q/Q98_Toy/core/Q98_Toy.dfy"
    c = ContainerRunner(root)
    fake_mk(root, {"target": t, "exit": 1, "ended_by": "killed(memory)", "rc": None})
    res = c.execute("vcheck --gate", t)
    assert (res.killed, res.exit_code, res.provenance) == ("memory", 137, "learner")
    assert set(res.document) == {"exit_code", "lines"}
    fake_mk(root, {"target": t, "exit": 124, "ended_by": "wall-clock", "rc": None,
                   "killed": "wall-clock"})
    res = c.execute("vcheck --gate", t)
    assert (res.killed, res.exit_code) == ("wall-clock", None)
    fake_mk(root, {"target": t, "exit": 3, "records": False,
                   "stderr": "mksandbox-run: refused: 3.0 GB available; the run is deferred"})
    with pytest.raises(PreflightError):
        c.execute("vcheck --gate", t)
    fake_mk(root, {"target": t, "exit": 3, "records": False, "stderr": "refused: no access"})
    with pytest.raises(RunnerUnavailable):
        c.execute("vcheck --gate", t)
    fake_mk(root, {"target": t, "exit": 1, "ended_by": "controls-failed", "no_commands": True})
    with pytest.raises(RunnerUnavailable):
        c.execute("vcheck --gate", t)
    fake_mk(root, {"target": "dafny/Q/Q98_Toy/core/Other.dfy"})
    with pytest.raises(RunnerUnavailable):
        c.execute("vcheck --gate", t)          # the two course paths disagree
    fake_mk(root, {"target": t, "build_exit": 3})
    with pytest.raises(RunnerUnavailable):
        c.execute("vaudit", t)


# ----- HostRunner on fake course tools ---------------------------------------------------

def test_the_host_runner_runs_the_course_tool(root, monkeypatch):
    monkeypatch.setenv("CI", "true")
    res = tools.run("vcheck --gate", "tests/corpus/dafny/G01/main.dfy", root=root,
                    runner=host(root))
    (c,) = calls(root)
    assert c["tool"] == "vcheck"
    assert c["argv"] == ["--json", "--gate", "tests/corpus/dafny/G01/main.dfy"]
    assert c["cwd"] == str(root)
    env = c["env"]
    assert env["CI"] is None
    assert (env["DVL_DAFNY_JOBS"], env["DVL_VERUS_JOBS"], env["PYTHONDONTWRITEBYTECODE"]) == \
        ("1", "1", "1")
    scratch = Path(env["DVL_SCRATCH"])
    assert scratch.parent == Path(os.environ["DVL_SCRATCH"]) and not scratch.exists()
    assert (res.instrument, res.target, res.exit_code, res.killed, res.runner,
            res.provenance) == ("vcheck --gate", "tests/corpus/dafny/G01/main.dfy", 0, None,
                                "host", "course")
    assert res.document == {"verdict": "verified", "exit_code": 0,
                            "target": "<root>/tests/corpus/dafny/G01/main.dfy",
                            "raw_dir": "<scratch>", "home": "~/notes",
                            "elsewhere": "thing.so", "holes": []}


def test_a_tool_without_a_json_document_gives_the_text_form(root):
    control(root, {"specfreeze": {"exit": 1, "say": "1 finding(s)", "stderr": "a note"}})
    res = tools.run("specfreeze --check", "tests/corpus/verus/V01", root=root,
                    runner=host(root))
    assert calls(root)[0]["argv"] == ["--against", "tests/corpus/verus/V01/frozen.rs",
                                      "tests/corpus/verus/V01/src/lib.rs"]
    assert res.exit_code == 1 and res.killed is None
    assert res.document == {"exit_code": 1, "lines": [
        "specfreeze: tests/corpus/verus/V01/src/lib.rs: 1 finding(s)",
        "raw output: <scratch>", "", "--- stderr ---", "a note"]}
    text = "\n".join(res.document["lines"]) + "\n"
    import hashlib
    assert res.output_sha256 == hashlib.sha256(text.encode()).hexdigest()


def test_output_that_is_not_a_document_gives_the_text_form(root):
    control(root, {"vaudit": {"text": True, "exit": 3, "say": "refused"}})
    res = tools.run("vaudit", "tests/corpus/dafny/G01/main.dfy", root=root, runner=host(root))
    assert res.exit_code == 3 and res.killed is None
    assert set(res.document) == {"exit_code", "lines"}


def test_the_hash_does_not_depend_on_the_scratch_directory(root):
    a = tools.run("vcheck --gate", "tests/corpus/dafny/G01/main.dfy", root=root,
                  runner=host(root))
    b = tools.run("vcheck --gate", "tests/corpus/dafny/G01/main.dfy", root=root,
                  runner=host(root))
    first, second = calls(root)
    assert first["env"]["DVL_SCRATCH"] != second["env"]["DVL_SCRATCH"]
    assert a.output_sha256 == b.output_sha256 and a.document == b.document


@pytest.mark.parametrize("behaviour,killed,exit_code", [
    ({"exit": 137}, "memory", 137),
    ({"exit": 143}, "memory", 143),
    ({"exit": 1, "verdict": "killed(memory)"}, "memory", 1),
    ({"exit": 1, "doc_exit": 137, "verdict": "error"}, "memory", 1),
    ({"exit": 124}, "wall-clock", 124),
    ({"exit": 1, "doc_exit": 124, "verdict": "inconclusive"}, "wall-clock", 1),
    ({"exit": 1, "text": True, "say": "wall-clock safety kill after 9 s (Δ58)"}, "wall-clock", 1),
    ({"exit": 1, "verdict": "failed"}, None, 1),
])
def test_kills_are_returned_as_kills(root, behaviour, killed, exit_code):
    control(root, {"vcheck": behaviour})
    res = tools.run("vcheck --gate", "tests/corpus/dafny/G01/main.dfy", root=root,
                    runner=host(root))
    assert (res.killed, res.exit_code) == (killed, exit_code)
    if killed:
        assert set(res.document) == {"exit_code", "lines"}
        assert "verdict" not in res.document


def _gone(pid, within=10.0):
    end = time.monotonic() + within
    while time.monotonic() < end:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.1)
    return False


def test_the_time_out_kills_the_process_group(root):
    control(root, {"vcheck": {"sleep": 60, "child": True}})
    t0 = time.monotonic()
    res = tools.run("seed-rerun", "tests/corpus/dafny/G01/main.dfy", root=root,
                    runner=host(root), timeout_s=2)
    assert time.monotonic() - t0 < 30
    assert (res.killed, res.exit_code) == ("wall-clock", None)
    assert set(res.document) == {"exit_code", "lines"} and res.document["exit_code"] is None
    assert _gone(int((root / "child.pid").read_text()))


def test_scratch_never_lies_inside_the_course_tree(root, monkeypatch):
    monkeypatch.setenv("DVL_SCRATCH", str(root / "scratch"))
    with pytest.raises(ValueError):
        tools.run("vaudit", "tests/corpus/dafny/G01/main.dfy", root=root, runner=host(root))


def test_the_memory_preflight(root, monkeypatch):
    with pytest.raises(PreflightError):              # no pins: the cap cannot be read
        tools.run("vaudit", "tests/corpus/dafny/G01/main.dfy", root=root,
                  runner=HostRunner(root))
    (root / "scripts" / "dvl").mkdir()
    (root / "scripts" / "dvl" / "pins.toml").write_text(
        "[dafny]\nmem_gb = 8\nwall_clock_s = 10\n[verus]\nmem_gb = 16\nwall_clock_s = 20\n")
    monkeypatch.setattr(R, "mem_available_gb", lambda: 22)
    with pytest.raises(PreflightError, match="23 GB needed"):
        tools.run("vaudit", "tests/corpus/dafny/G01/main.dfy", root=root,
                  runner=HostRunner(root))
    monkeypatch.setattr(R, "mem_available_gb", lambda: 23)
    assert tools.run("vaudit", "tests/corpus/dafny/G01/main.dfy", root=root,
                     runner=HostRunner(root)).exit_code == 0
    with pytest.raises(PreflightError, match="31 GB needed"):
        tools.run("vaudit", "tests/corpus/verus/V01", root=root, runner=HostRunner(root))
    assert R.default_timeout(root, "verus") == 3 * 20 + 600
    assert len(calls(root)) == 1


# ----- ToolResult ------------------------------------------------------------------------

def result(**kw):
    base = dict(instrument="vaudit", target="t", document={"findings": []}, exit_code=0,
                killed=None, runner="host", provenance="course", output_sha256=SHA)
    base.update(kw)
    return ToolResult(**base)


def test_a_tool_result_is_validated():
    assert result().to_dict()["instrument"] == "vaudit"
    for bad in (dict(instrument="lint"), dict(target=""), dict(document=[]),
                dict(document={"x": object()}), dict(exit_code=True), dict(exit_code="1"),
                dict(killed="cpu"), dict(runner="laptop"), dict(provenance="trusted"),
                dict(output_sha256="ABC"), dict(exit_code=None),
                dict(killed="memory", exit_code=137),                  # a tool document
                dict(killed="memory", exit_code=0, document={"exit_code": 0, "lines": []})):
        with pytest.raises((TypeError, ValueError)):
            result(**bad)
    ok = result(killed="wall-clock", exit_code=None, document={"exit_code": None, "lines": []})
    with pytest.raises(dataclasses.FrozenInstanceError):
        ok.killed = None
    assert hash(result()) == hash(result()) and len({result(), result(), ok}) == 2


# ----- recorded results, replay ----------------------------------------------------------

def test_recordings_round_trip_and_hold_results_only(tmp_path):
    base = tmp_path / "fx"
    res = result(instrument="vcheck --gate", target="tests/corpus/dafny/G01/main.dfy",
                 document={"verdict": "verified"}, exit_code=0)
    path = R.recording_path(base, "dafny", "G01", "vcheck --gate")
    assert path == base / "dafny" / "G01" / "vcheck-gate.json"
    R.write_recording(path, res, ["scripts/vcheck", "--json", "--gate", res.target])
    rec = json.loads(path.read_text())
    assert set(rec) == {"schema", "instrument", "target", "argv", "exit_code", "killed",
                        "provenance", "output_sha256", "document"}
    back = R.read_recording(path)
    assert back == dataclasses.replace(res, runner="replay")
    with pytest.raises(ValueError):                    # a kill is never recorded
        R.write_recording(path, result(killed="memory", exit_code=137,
                                       document={"exit_code": 137, "lines": []}), [])
    with pytest.raises(ValueError):
        R.write_recording(base / "vaudit.json", res, [])
    rec["xclass"] = "X01"                              # a label never rides along
    path.write_text(json.dumps(rec))
    with pytest.raises(ValueError):
        R.read_recording(path)
    del rec["xclass"]
    rec["instrument"] = "vaudit"
    path.write_text(json.dumps(rec))
    with pytest.raises(ValueError):
        R.read_recording(path)
    with pytest.raises(ValueError):
        R.recording_path(base, "dafny", "../G01", "vaudit")


def write(root, lang, fid, inst, target, exit_code=1):
    res = result(instrument=inst, target=target, exit_code=exit_code,
                 document={"exit_code": exit_code, "lines": []})
    R.write_recording(R.recording_path(root / tools.FIXTURES, lang, fid, inst), res, ["x"])
    return res


def test_replay(root):
    write(root, "dafny", "G01", "vaudit", "tests/corpus/dafny/G01/main.dfy")
    write(root, "verus", "V01", "vaudit", "tests/corpus/verus/V01", exit_code=0)
    r = tools.replay("G01", "vaudit", root=root)
    assert (r.runner, r.exit_code, r.target) == ("replay", 1, "tests/corpus/dafny/G01/main.dfy")
    assert tools.replay("verus/V01", "vaudit", root=root).exit_code == 0
    with pytest.raises(NoRecording):
        tools.replay("G01", "witness", root=root)
    with pytest.raises(NoRecording):
        tools.replay("G99", "vaudit", root=root)
    with pytest.raises(ValueError):
        tools.replay("lean/G01", "vaudit", root=root)
    with pytest.raises(ValueError):
        tools.replay("G01", "lint", root=root)
    write(root, "verus", "G01", "vaudit", "tests/corpus/verus/G01")
    with pytest.raises(ValueError):                    # the id names two languages
        tools.replay("G01", "vaudit", root=root)
    assert tools.replay("dafny/G01", "vaudit", root=root).exit_code == 1


def test_the_replay_runner_behind_run(root):
    write(root, "dafny", "G01", "witness", "tests/corpus/dafny/G01/main.dfy")
    rr = ReplayRunner(root=root)
    assert rr.isolated
    res = tools.run("witness", "tests/corpus/dafny/G01/main.dfy", root=root, runner=rr)
    assert (res.runner, res.provenance, res.exit_code) == ("replay", "course", 1)
    agent = tools.run("witness", "tests/corpus/dafny/G01/main.dfy", root=root, runner=rr,
                      provenance="agent")
    assert agent.provenance == "agent"
    with pytest.raises(NoRecording):
        tools.run("vaudit", "tests/corpus/dafny/G01/main.dfy", root=root, runner=rr)
    write(root, "dafny", "G01b", "witness", "tests/corpus/dafny/G01/main.dfy")
    with pytest.raises(ValueError):                    # two recordings of one call
        ReplayRunner(root=root).execute("witness", "tests/corpus/dafny/G01/main.dfy")
    assert not (root / "calls.jsonl").exists()


def test_the_recorded_layout():
    assert tools.FIXTURES == "harness/tests/q/fixtures/q09"
    assert ReplayRunner().dir == ROOT / "harness" / "tests" / "q" / "fixtures" / "q09"


# ----- the frozen core's rules -----------------------------------------------------------

def test_the_new_modules_use_the_standard_library_only():
    files = [HARNESS / "fvh" / "verdicts.py", HARNESS / "fvh" / "corpus.py",
             *sorted((HARNESS / "fvh" / "tools").glob("*.py"))]
    assert len(files) == 5
    for f in files:
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                heads = {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                heads = {(node.module or "").split(".")[0]}
            else:
                continue
            assert heads <= set(sys.stdlib_module_names) | {"fvh"}, (f.name, heads)


def test_no_gate_logic_ships_in_the_instruments():
    """fvh.tools reports what a tool did; it never reads a result as flagged or clean."""
    for f in (HARNESS / "fvh" / "tools").glob("*.py"):
        text = f.read_text(encoding="utf-8")
        for word in ("flagged", "GRADER_ONLY", "xclass", "classify"):
            assert word not in text, (f.name, word)


def test_the_challenge_instruments(tmp_path):
    """solver-swap and reach (QPLAN §31.4 item 5, Δ402): Dafny-only solver swap; reach
    reads the target's reach.toml companion."""
    assert tools.command("solver-swap", "d/a.dfy") == ["scripts/vcheck", "--brittleness",
                                                       "--solvers", "d/a.dfy"]
    with pytest.raises(ValueError, match="one solver"):
        tools.command("solver-swap", "c/crate", lang="verus")
    assert tools.command("reach", "d/a.dfy") == ["scripts/dvl/reach.py", "--manifest",
                                                 "d/reach.toml", "d/a.dfy"]
    assert tools.command("reach", "c/crate", lang="verus") == [
        "scripts/dvl/reach.py", "--manifest", "c/crate/reach.toml", "c/crate"]
    h = HostRunner(root=tmp_path)
    assert h.argv("reach", "d/a.dfy")[:2] == ["scripts/dvl/reach.py", "--json"]
