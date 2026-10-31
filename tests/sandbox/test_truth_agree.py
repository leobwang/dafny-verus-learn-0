"""The grader container's graded modes, gate-agree and bench-agree (QPLAN §31.3, DELTAS
Δ418), and truth.toml's `part` key: no Docker, no key, no solver, and nothing of any real
hidden truth. A throwaway git root with an invented registry record (Q31, solo, its
agents package invented here), invented part pins over random-byte "archives", and, for
truthcheck, stand-in archives, a stand-in learner gate and bench, and a stub vcheck:

  - the pins: a lab's archive and its parts are separate pins (id and part), a part is a
    lower-case word, and no two pins share a key or an archive;
  - the manifest rules: a part archive runs its own mode and the round trip only, a lab
    archive never a graded mode; gate-agree names one language, bench-agree nothing;
  - the graded role: only in a truth run of a graded mode, read at a commit, at its own
    course path, and only the files the mode grades (the module's agents package, the
    learner's own package, bench-agree's run records); no input under grader/;
  - build_truth: the learner's committed work at HEAD (a changed or untracked file
    refuses the run), the frozen core, the tools; gate-agree sized for its language, with
    the grader's writable /work/grader; bench-agree with its records and strata map;
  - mksandbox-run's argument rules for the two modes;
  - truthcheck gate-agree, in-process with its child a real subprocess: the gate sees
    renumbered deliveries and no label, sealed id or trusted word; every instrument call
    runs through the in-container runner; the counts follow the course's evaluator;
    nothing the gate prints and no canary of the deliveries reaches stdout or stderr;
  - truthcheck bench-agree: the learner's tables against the sealed reference's, cell
    for cell, counts only;
  - a study session's tools cannot start either run (guard rule 1c)."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from dvl import sandbox  # noqa: E402

CANARY = "DVLCANARY-agree-test-7b1e"     # an invented token: no real canary's hash
SEALED_ID = "sealedidzq"                 # an invented sealed delivery id marker
GIT = ["git", "-c", "user.name=sandbox-tests", "-c", "user.email=sandbox-tests@example.invalid",
       "-c", "init.defaultBranch=main"]

REGISTRY = """schema = 1

[[module]]
id = "Q31"
track = "Q"
status = "authoring"
title = "Invented challenge module"
layer = ""
units = []
exercises = []
exits = []
agentic = []
harness = ["agents/q31_gate_bench/gate.py", "agents/q31_gate_bench/bench.py"]
engines = ["policy"]
solo = true
budget = { claude_calls = 0, claude_runs = 0, qwen_calls = 0, qwen_runs = 0, gpu_hours = 0 }

[[module]]
id = "Q12"
track = "Q"
status = "authoring"
title = "Invented core module"
layer = ""
units = []
exercises = []
exits = []
agentic = []
harness = []
engines = []
solo = false
budget = { claude_calls = 0, claude_runs = 0, qwen_calls = 0, qwen_runs = 0, gpu_hours = 0 }
"""


def git(root, *args):
    return subprocess.run(GIT + ["-C", str(root), *args], check=True, capture_output=True,
                          text=True).stdout


def make_root(tmp):
    """A git root holding the course tools, an invented Q31 record and its committed
    agents package, the learner's package, two run records, a stratum and two part pins
    over random-byte archives."""
    root = tmp / "course"
    for rel in ("scripts", "dafny/options", "sandbox/images.lock", "harness/fvh"):
        src, dst = ROOT / rel, root / rel
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    (root / "MODULES.toml").write_text(REGISTRY)
    files = {
        "agents/q31_gate_bench/__init__.py": "",
        "agents/q31_gate_bench/gate.py": "def gate_task(t, *, run=None, run_dir=None):\n    pass\n",
        "agents/q31_gate_bench/bench.py": "def load_runs(root, module, **kw):\n    return []\n",
        "agents/q29_other/policy.py": "X = 1\n",            # another topic's package
        "harness/q/fvh_q/__init__.py": "",
        "harness/q/fvh_q/gate/__init__.py": "",
        "harness/q/fvh_q/gate/gate_v2.py": "COURSE_ROOT = None\n",
        "research/runs/Q31/r1/run.json": '{"arm": "a"}\n',
        "research/runs/Q31/r2/run.json": '{"arm": "b"}\n',
        "research/runs/Q31/r2/transcript.jsonl": "{}\n",     # not a record bench-agree reads
        "research/runs/Q12/r9/run.json": "{}\n",             # another module's record
        "bench/local/q/agentic/q31-dev/STRATUM.toml":
            'schema = 1\nmodule = "Q31"\n[[card]]\nid = "cl-a"\nsource = "course-local"\n'
            '[[card]]\nid = "pd-b"\nsource = "dafnybench"\n',
    }
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    pins = []
    for part in ("cheats", "bench"):
        arc = root / "Hidden" / "Agentic" / "Q31" / f"{part}.tar.age"
        arc.parent.mkdir(parents=True, exist_ok=True)
        data = b"age-encryption.org/v1\n" + os.urandom(128)
        arc.write_bytes(data)
        pins.append(f'[[lab]]\nid = "Q31"\npart = "{part}"\n'
                    f'archive = "Hidden/Agentic/Q31/{part}.tar.age"\n'
                    'recipient = "age1invented"\nidentity = "~/.keys/invented.agekey"\n'
                    f'sha256 = "{hashlib.sha256(data).hexdigest()}"\nfiles = 1\n')
    (root / "sandbox" / "truth.toml").write_text("schema = 1\n" + "\n".join(pins))
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "fixture")
    return root


class Pins(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dvl0-agree-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = make_root(self.tmp)

    def write(self, text):
        (self.root / "sandbox" / "truth.toml").write_text(text)

    def test_parts_are_their_own_pins(self):
        pins = sandbox.truth_pins(self.root)
        self.assertEqual(sorted(pins), ["Q31:bench", "Q31:cheats"])
        self.assertEqual(pins[sandbox.truth_key("Q31", "cheats")]["part"], "cheats")
        self.assertNotIn("Q31", pins)

    def test_a_bad_or_repeated_part_is_refused(self):
        base = 'schema = 1\n[[lab]]\nid = "Q31"\npart = "%s"\narchive = "%s"\nsha256 = "x"\n'
        self.write(base % ("Cheats", "a.age"))
        with self.assertRaises(sandbox.ManifestError):
            sandbox.truth_pins(self.root)
        self.write(base % ("cheats", "a.age") + base.split("\n", 1)[1] % ("cheats", "b.age"))
        with self.assertRaises(sandbox.ManifestError):
            sandbox.truth_pins(self.root)
        self.write(base % ("cheats", "a.age") + base.split("\n", 1)[1] % ("bench", "a.age"))
        with self.assertRaises(sandbox.ManifestError):
            sandbox.truth_pins(self.root)


class GradedManifest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dvl0-agree-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = make_root(self.tmp)

    def problems(self, raw):
        try:
            sandbox.validate(raw, self.root)
        except sandbox.ManifestError as e:
            return e.problems
        return []

    def test_gate_agree_stages_the_committed_work_and_sizes_for_its_language(self):
        raw = sandbox.build_truth(self.root, "Q31", "gate-agree", part="cheats", lang="verus")
        m = sandbox.validate(raw, self.root)
        head = git(self.root, "rev-parse", "HEAD").strip()
        graded = {e.src: e for e in m.files if e.role == "graded"}
        self.assertEqual(sorted(graded), ["agents/q31_gate_bench/__init__.py",
                                          "agents/q31_gate_bench/bench.py",
                                          "agents/q31_gate_bench/gate.py",
                                          "harness/q/fvh_q/__init__.py",
                                          "harness/q/fvh_q/gate/__init__.py",
                                          "harness/q/fvh_q/gate/gate_v2.py"])
        self.assertTrue(all(e.rev == head and e.dst == e.src for e in graded.values()))
        self.assertIn("harness/fvh/tools/runners.py",
                      {e.src for e in m.files if e.role == "given"})
        self.assertFalse(any(e.dst.startswith(("research/", "Hidden/", "Solutions/"))
                             for e in m.files))
        self.assertEqual(m.commands, ((sandbox.TRUTHCHECK, "gate-agree", "Q31", "verus"),))
        self.assertEqual(m.truth["part"], "cheats")
        self.assertEqual(m.pools(), ["verus"])
        self.assertEqual(m.limits["mem_gb"], sandbox.memory_bound_gb("verify", ["verus"]))
        mounts = dict(sandbox.work_mounts(m))
        self.assertIn(f"{sandbox.WORK}/grader", mounts)
        self.assertIn("tmpfs-mode=1777", mounts[f"{sandbox.WORK}/grader"])
        lines = sandbox.docker_argv(m, "/RUN")
        self.assertIn(f"type=bind,source=/RUN/in/agents/q31_gate_bench/gate.py,destination="
                      f"{sandbox.WORK}/agents/q31_gate_bench/gate.py,readonly", lines[0])

    def test_bench_agree_stages_the_records_and_the_strata(self):
        raw = sandbox.build_truth(self.root, "Q31", "bench-agree", part="bench")
        m = sandbox.validate(raw, self.root)
        graded = {e.src for e in m.files if e.role == "graded"}
        self.assertLessEqual({"research/runs/Q31/r1/run.json", "research/runs/Q31/r2/run.json"},
                             graded)
        self.assertFalse(any(s.startswith("research/runs/Q12/") or s.endswith(".jsonl")
                             for s in graded))
        strata = next(e for e in m.files if e.dst == f"{sandbox.GRADER_IN}/strata.json")
        self.assertEqual(strata.role, "task")
        self.assertEqual(json.loads(strata.text)["strata"],
                         {"cl-a": "course-local", "pd-b": "public"})
        self.assertNotIn(f"{sandbox.WORK}/grader", dict(sandbox.work_mounts(m)))
        self.assertEqual(m.commands, ((sandbox.TRUTHCHECK, "bench-agree", "Q31"),))

    def test_uncommitted_or_untracked_work_refuses_the_run(self):
        (self.root / "agents/q31_gate_bench/gate.py").write_text("# changed\n")
        with self.assertRaises(sandbox.ManifestError) as e:
            sandbox.build_truth(self.root, "Q31", "gate-agree", part="cheats", lang="dafny")
        self.assertIn("commit it first", str(e.exception))
        git(self.root, "checkout", "--", "agents")
        (self.root / "research/runs/Q31/r3").mkdir()
        (self.root / "research/runs/Q31/r3/run.json").write_text("{}\n")
        with self.assertRaises(sandbox.ManifestError):
            sandbox.build_truth(self.root, "Q31", "bench-agree", part="bench")
        sandbox.build_truth(self.root, "Q31", "gate-agree", part="cheats", lang="dafny")

    def test_the_mode_fits_the_part(self):
        for mode, part, lang in (("gate-agree", "bench", "dafny"), ("bench-agree", "cheats", None),
                                 ("validate", "cheats", None), ("gate-agree", "cheats", None),
                                 ("bench-agree", "bench", "dafny")):
            with self.assertRaises(sandbox.ManifestError, msg=(mode, part, lang)):
                sandbox.build_truth(self.root, "Q31", mode, part=part, lang=lang)
        raw = sandbox.build_truth(self.root, "Q31", "manifest", part="cheats")
        self.assertEqual(sandbox.validate(raw, self.root).truth["part"], "cheats")
        with self.assertRaises(sandbox.ManifestError):
            sandbox.build_truth(self.root, "Q12", "gate-agree", part="cheats", lang="dafny")

    def test_the_grader_argv_and_the_part_agree(self):
        raw = sandbox.build_truth(self.root, "Q31", "gate-agree", part="cheats", lang="dafny")
        for argv in (["gate-agree", "Q31"], ["gate-agree", "Q31", "python"],
                     ["bench-agree", "Q31"], ["validate", "Q31"], ["judge", "Q31"]):
            bad = dict(raw, command=[{"argv": [sandbox.TRUTHCHECK, *argv]}])
            self.assertTrue(self.problems(bad), argv)
        bad = dict(raw, truth={k: v for k, v in raw["truth"].items() if k != "part"})
        self.assertTrue(any("pinned" in p for p in self.problems(bad)))
        bad = dict(raw, truth=dict(raw["truth"], extra=1))
        self.assertTrue(any("[truth]" in p for p in self.problems(bad)))

    def test_the_graded_role_is_narrow(self):
        raw = sandbox.build_truth(self.root, "Q31", "gate-agree", part="cheats", lang="dafny")
        head = git(self.root, "rev-parse", "HEAD").strip()
        g = next(f for f in raw["file"] if f.get("role") == "graded")

        def with_file(**f):
            return dict(raw, file=raw["file"] + [f])
        other = "agents/q29_other/policy.py"
        sha = hashlib.sha256((self.root / other).read_bytes()).hexdigest()
        cases = {
            "another topic's package": with_file(src=other, dst=other, role="graded", rev=head,
                                                 sha256=sha),
            "no commit": dict(raw, file=[dict(g, rev=None) if f is g else f for f in raw["file"]]),
            "a branch name": dict(raw, file=[dict(g, rev="HEAD") if f is g else f
                                             for f in raw["file"]]),
            "another path": dict(raw, file=[dict(g, dst="x/" + g["dst"]) if f is g else f
                                            for f in raw["file"]]),
            "a record in gate-agree": with_file(
                src="research/runs/Q31/r1/run.json", dst="research/runs/Q31/r1/run.json",
                role="graded", rev=head,
                sha256=hashlib.sha256(b'{"arm": "a"}\n').hexdigest()),
            "an input under grader/": with_file(dst="grader/x.dfy", role="editable", text="x",
                                                sha256=hashlib.sha256(b"x").hexdigest()),
        }
        for why, bad in cases.items():
            self.assertTrue(self.problems(bad), why)
        not_graded = dict(raw, command=[{"argv": [sandbox.TRUTHCHECK, "manifest", "Q31"]}])
        self.assertTrue(any("graded mode" in p for p in self.problems(not_graded)))
        self.assertEqual(self.problems(raw), [])

    def test_the_command_line_rules(self):
        base = [sys.executable, "-B", str(ROOT / "scripts" / "mksandbox-run"), "--truth",
                "Hidden/Agentic/Q31/cheats.tar.age"]
        for extra in (["--truth-check", "gate-agree"],
                      ["--truth-check", "gate-agree", "--truth-lang", "dafny", "--cards", "a"],
                      ["--truth-check", "bench-agree", "--truth-lang", "dafny"],
                      ["--truth-check", "bench-agree", "--cards", "a"]):
            p = subprocess.run(base + extra, capture_output=True, text=True, timeout=60)
            self.assertEqual(p.returncode, 2, (extra, p.stderr))


# --- truthcheck, in-process (its child a real subprocess) -------------------------------------

STUB_VCHECK = '''import json, sys
print(json.dumps({"verdict": "verified", "stub": sys.argv[1:]}))
'''

LEARNER_GATE = '''"""A stand-in learner gate: FAIL when a delivery holds `assume false`, an error on
`boom`, else PASS with X07 unknown. It runs one instrument through fvh.tools (no runner
named), prints every delivery file, and records what it could see."""
import json, os
from dataclasses import dataclass
from fvh import tools

@dataclass(frozen=True)
class Pins:
    min_verified: int
    symbols: tuple

@dataclass(frozen=True)
class CrateTarget:
    id: str
    lang: str
    target: str
    files: tuple
    pins: Pins

@dataclass(frozen=True)
class TaskTarget:
    crate: CrateTarget
    statement: str
    task_form: str
    editable: tuple

@dataclass(frozen=True)
class V:
    word: str
    unknown: tuple

@dataclass(frozen=True)
class R:
    verdict: V

def gate_task(target, *, run=None, run_dir=None):
    res = tools.run("vcheck --gate", target.crate.target)
    seen = {"id": target.crate.id, "runner": res.runner, "doc": res.document,
            "files": list(target.crate.files), "run_dir": run_dir}
    texts = ""
    for f in target.crate.files:
        texts += open(f).read()
        print(open(f).read())
    for d, _, fs in os.walk(os.environ["DVL_AGREE_PEEK"]):
        for f in fs:
            texts += open(os.path.join(d, f), errors="replace").read()
    seen["peek"] = texts
    with open(os.environ["DVL_AGREE_LOG"], "a") as fh:
        fh.write(json.dumps(seen) + "\\n")
    body = "".join(open(f).read() for f in target.crate.files)
    if "boom" in body:
        raise RuntimeError("stand-in failure " + body)
    if "assume false" in body:
        return R(V("FAIL", ()))
    return R(V("PASS", ("X07",)))
'''

BENCH = '''"""A stand-in bench: rows from the run records, one table per call, tab-separated lines."""
import json, os
from dataclasses import dataclass

@dataclass(frozen=True)
class Row:
    arm: str
    task: str
    solved: bool

def load_runs(root, module, *, arms=(), strata=None):
    base = os.path.join(root, "research", "runs", module)
    out = []
    for d in sorted(os.listdir(base)):
        m = json.load(open(os.path.join(base, d, "run.json")))
        out.append(Row(m["arm"], m["task"], m["solved"]))
    return out

def pass_at_k_table(rows, ks):
    return ("pass", [(r.arm, k, SHIFT + sum(x.solved for x in rows if x.arm == r.arm))
                     for r in rows for k in ks])

def cost_curve(rows, axis, budgets):
    if axis == "bad":
        raise ValueError(axis)
    return ("curve", [(axis, r.arm, b, 0.5) for r in rows for b in budgets])

def paired_report(rows, a, b):
    return ("paired", [(a, b, len(rows))])

def render(tables):
    lines = set()
    for kind, rows in tables:
        for r in rows:
            lines.add("\\t".join([kind, *map(str, r)]))
    return "\\n".join(sorted(lines)) + "\\n"
'''


def load_truthcheck():
    spec = importlib.util.spec_from_file_location("truthcheck_under_test",
                                                  ROOT / "sandbox" / "image" / "truthcheck.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TruthcheckAgree(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dvl0-agree-tc-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.work = self.tmp / "work"
        for rel in ("harness/fvh",):
            shutil.copytree(ROOT / rel, self.work / rel, ignore=shutil.ignore_patterns("__pycache__"))
        (self.work / "MODULES.toml").write_text(REGISTRY)
        (self.work / "scripts").mkdir()
        (self.work / "scripts" / "vcheck").write_text(STUB_VCHECK)
        (self.work / "grader").mkdir()
        (self.work / "agents" / "q31_gate_bench").mkdir(parents=True)
        (self.work / "agents" / "q31_gate_bench" / "__init__.py").write_text("")
        (self.work / "agents" / "q31_gate_bench" / "gate.py").write_text(LEARNER_GATE)
        self.log = self.tmp / "seen.jsonl"
        self.tc = load_truthcheck()
        self.tc.WORK = str(self.work)
        self.tc.CHILD_TMP = str(self.tmp / "child")
        self.tc.PYTHON = sys.executable
        self.env = mock.patch.dict(os.environ, {
            "DVL_AGREE_LOG": str(self.log), "DVL_AGREE_PEEK": str(self.tmp / "child"),
            "DVL_SCRATCH": str(self.tmp / "scratch")})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.mods = dict(sys.modules)

    def tearDown(self):
        for k in [k for k in sys.modules if k not in self.mods]:
            del sys.modules[k]

    def archive(self, deliveries, bodies):
        files = {"labs/Q31/MANIFEST.sha256": b""}
        lines = ['schema = 1', 'entry = "q31_gate_bench.gate:gate_task"']
        for d in deliveries:
            lines.append("[[delivery]]")
            for k, v in d.items():
                lines.append(f"{k} = {json.dumps(v)}")
        files["labs/Q31/gate/DELIVERIES.toml"] = "\n".join(lines).encode()
        for did, body in bodies.items():
            for rel, text in body.items():
                files[f"labs/Q31/gate/{did}/{rel}"] = text.encode()
        return files

    def run_tc(self, argv, files):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(self.tc, "unseal", lambda lab: (dict(files), None)), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.tc.entry(argv)
        return code, out.getvalue(), err.getvalue()

    def delivery(self, did, xclass, trusted, lang="dafny"):
        d = {"id": f"{SEALED_ID}{did}", "lang": lang, "class": xclass, "target": "main.dfy",
             "statement": "", "task_form": "", "editable": ["main.dfy"], "run_dir": "",
             "min_verified": 1, "symbols": ["M.L"]}
        if trusted is not None:
            d["trusted"] = trusted
        return d

    def test_gate_agree_counts_by_class_and_shows_the_gate_nothing_sealed(self):
        dels = [self.delivery("1", "control", "PASS"), self.delivery("2", "X02", "FAIL"),
                self.delivery("3", "X02", "FAIL"), self.delivery("4", "X07", None),
                self.delivery("5", "X10", "FAIL"), self.delivery("6", "X02", "FAIL", lang="verus")]
        bodies = {f"{SEALED_ID}1": {"main.dfy": f"// {CANARY} honest\n"},
                  f"{SEALED_ID}2": {"main.dfy": f"assume false; // {CANARY}\n"},
                  f"{SEALED_ID}3": {"main.dfy": f"// {CANARY} a cheat the gate passes\n"},
                  f"{SEALED_ID}4": {"main.dfy": f"// {CANARY} grader-only\n"},
                  f"{SEALED_ID}5": {"main.dfy": f"// boom {CANARY}\n"},
                  f"{SEALED_ID}6": {"main.dfy": "assume false;\n"}}
        code, out, err = self.run_tc(["gate-agree", "Q31", "dafny"], self.archive(dels, bodies))
        self.assertEqual(code, 1, out)
        doc = json.loads(out)
        self.assertEqual(doc["classes"], {"X02": {"agree": 1, "disagree": 1},
                                          "X10": {"agree": 0, "disagree": 1}})
        self.assertEqual(doc["controls"], {"honest": 1, "false_rejects": 0})
        self.assertEqual(doc["grader_only"], {"held": 1, "passed": 0})
        self.assertEqual((doc["deliveries"], doc["other_language"], doc["not_run"]), (5, 1, 1))
        self.assertFalse(doc["agreed"])
        for text in (out, err):
            self.assertNotIn(CANARY, text)
            self.assertNotIn(SEALED_ID, text)
        seen = [json.loads(x) for x in self.log.read_text().splitlines()]
        self.assertEqual([s["id"] for s in seen], ["d01", "d02", "d03", "d04", "d05"])
        for s in seen:
            self.assertEqual(s["runner"], "container")      # the in-container runner
            self.assertEqual(s["doc"]["verdict"], "verified")
            self.assertTrue(all(f.startswith(f"grader/{s['id']}/") for f in s["files"]))
            for word in (SEALED_ID, "X02", "X07", "X10", "control", "trusted"):
                self.assertNotIn(word, s["peek"])           # the child's spec holds no label
        self.assertEqual(list((self.work / "grader").iterdir()), [])   # cleaned after

    def test_gate_agree_passes_when_every_delivery_agrees(self):
        dels = [self.delivery("1", "control", "PASS"), self.delivery("2", "X02", "FAIL"),
                self.delivery("3", "X14", None)]
        bodies = {f"{SEALED_ID}1": {"main.dfy": "honest\n"},
                  f"{SEALED_ID}2": {"main.dfy": "assume false;\n"},
                  f"{SEALED_ID}3": {"main.dfy": "assume false;\n"}}
        code, out, _ = self.run_tc(["gate-agree", "Q31", "dafny"], self.archive(dels, bodies))
        self.assertEqual(code, 0, out)
        doc = json.loads(out)
        self.assertTrue(doc["agreed"])
        self.assertEqual(doc["classes"], {"X02": {"agree": 1, "disagree": 0},
                                          "X14": {"agree": 1, "disagree": 0}})

    def test_malformed_deliveries_and_other_parts_are_refused(self):
        bad = [dict(self.delivery("1", "X02", None)),                   # no trusted word
               dict(self.delivery("1", "control", "FAIL")),             # a failing control
               dict(self.delivery("1", "X99", "FAIL")),                 # no such class
               dict(self.delivery("1", "X02", "FAIL"), target="../x")]  # a path out
        for d in bad:
            code, out, err = self.run_tc(["gate-agree", "Q31", "dafny"],
                                         self.archive([d], {d["id"]: {"main.dfy": CANARY}}))
            self.assertEqual(code, 3, (d, out))
            self.assertNotIn(CANARY, out + err)
        code, out, _ = self.run_tc(["gate-agree", "Q31", "dafny"], {"labs/Q31/MANIFEST.sha256": b""})
        self.assertEqual(code, 3)
        self.assertIn("not a cheats part", json.loads(out)["error"])
        code, out, _ = self.run_tc(["gate-agree", "Q31"], {})
        self.assertEqual(code, 2)

    def records(self, rows):
        for i, (arm, task, solved) in enumerate(rows):
            d = self.work / "research" / "runs" / "Q31" / f"r{i}"
            d.mkdir(parents=True)
            (d / "run.json").write_text(json.dumps({"arm": arm, "task": task, "solved": solved}))
        (self.work / "grader-in").mkdir(exist_ok=True)
        (self.work / "grader-in" / "strata.json").write_text(
            json.dumps({"schema": 1, "module": "Q31", "strata": {"t1": "course-local"}}))

    def bench_archive(self, curves=("calls",)):
        spec = ['schema = 1', 'module = "q31_gate_bench.bench"', 'reference = "bench/bench.py"',
                'ks = [1, 2]', '[keys]', 'pass = 3', 'curve = 4', 'paired = 3']
        for c in curves:
            spec += ["[[curve]]", f'axis = "{c}"', "budgets = [1, 2]"]
        ref = BENCH.replace("SHIFT +", "0 +") + f"\n# {CANARY}\n"
        return {"labs/Q31/MANIFEST.sha256": b"", "labs/Q31/bench/TABLES.toml":
                "\n".join(spec).encode(), "labs/Q31/bench/bench.py": ref.encode()}

    def test_bench_agree_matches_cell_for_cell(self):
        self.records([("a", "t1", True), ("b", "t1", False), ("a", "t2", True)])
        (self.work / "agents" / "q31_gate_bench" / "bench.py").write_text(
            BENCH.replace("SHIFT +", "0 +"))
        code, out, err = self.run_tc(["bench-agree", "Q31"], self.bench_archive())
        self.assertEqual(code, 0, out)
        doc = json.loads(out)
        self.assertTrue(doc["agreed"])
        self.assertEqual(doc["tables"], 3)            # pass, curve:calls, paired:a|b
        self.assertEqual(doc["kinds"]["pass"]["mismatched"], 0)
        self.assertGreater(doc["kinds"]["pass"]["matched"], 0)
        self.assertNotIn(CANARY, out + err)

    def test_bench_agree_counts_the_cells_that_differ(self):
        self.records([("a", "t1", True), ("b", "t1", False)])
        (self.work / "agents" / "q31_gate_bench" / "bench.py").write_text(
            BENCH.replace("SHIFT +", "1 +").replace('if axis == "bad"', 'if axis == "calls"'))
        code, out, err = self.run_tc(["bench-agree", "Q31"], self.bench_archive(("calls", "bad")))
        self.assertEqual(code, 1, out)
        doc = json.loads(out)
        self.assertFalse(doc["agreed"])
        self.assertEqual(doc["skipped"], 1)           # the reference has no "bad" curve either
        self.assertEqual(doc["learner_errors"], 1)    # the learner's calls curve raised
        self.assertEqual(doc["kinds"]["pass"]["mismatched"], 4)    # every estimate off by one
        self.assertEqual(doc["kinds"]["curve"]["missing_rows"], 4)
        self.assertEqual(doc["kinds"]["paired"]["mismatched"], 0)
        self.assertNotIn(CANARY, out + err)
        self.assertNotIn("\tpass\t", out)


class StudySessionGuard(unittest.TestCase):
    """Both command lines name the sealed archive: rule 1c refuses them in a study session."""

    def test_the_graded_command_lines_are_refused(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl0-agreeguard-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        root, home = tmp / "study", tmp / "home"
        root.mkdir()
        gen = ROOT / "scripts" / "gen_hook_fixtures.py"
        sid = "11111111-2222-4333-8444-555555555557"
        slug = "".join(c if c.isascii() and c.isalnum() else "-" for c in str(root))
        subprocess.run([sys.executable, str(gen), "--fake-root", str(root)], check=True,
                       capture_output=True)
        subprocess.run([sys.executable, str(gen), "--fake-home", str(home), f"--slug={slug}",
                        f"--sid={sid}"], check=True, capture_output=True)
        for cmd in ("scripts/mksandbox-run --truth Hidden/Agentic/Q31/cheats.tar.age "
                    "--truth-check gate-agree --truth-lang dafny",
                    "scripts/mksandbox-run --truth Hidden/Agentic/Q31/bench.tar.age "
                    "--truth-check bench-agree --mem-gb 8"):
            inp = {"session_id": sid,
                   "transcript_path": f"{home}/.claude/projects/{slug}/{sid}.jsonl",
                   "tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(root)}
            env = {k: v for k, v in os.environ.items()
                   if k not in ("CLAUDE_CODE_SESSION_ID", "CLAUDE_CONFIG_DIR", "TMPDIR",
                                "SPOILER_GUARD_NO_JQ")}
            env.update(HOME=str(home), CLAUDE_PROJECT_DIR=str(root))
            p = subprocess.run(["bash", str(ROOT / ".claude" / "hooks" / "spoiler-guard.sh")],
                               input=json.dumps(inp), capture_output=True, text=True, env=env,
                               timeout=60)
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertIn("rule 1c", p.stderr)


if __name__ == "__main__":
    unittest.main()
