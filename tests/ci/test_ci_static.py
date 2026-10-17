"""scripts/ci.sh: options, the author gate, statuses, logs and the study-mode
check; the corpus job and its runner, scripts/test_corpus.py. The static job runs the checker and its suite. Provided-layer regression
fixtures can invoke the pinned verifier on tiny invented programs; no model
or actor session is started. The corpus tests run copies of scripts/ in throwaway checkouts,
with a stub runner or with a tiny invented corpus that the real runner lists
and checks statically but never runs. Every expected outcome was captured
from a real run of ci.sh or the runner on these roots.

Run: python3 -B -m unittest discover -s tests/ci -p 'test_ci_static.py'
"""

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_common as C  # noqa: E402

ALL_JOBS = ["static", "hook-test", "verify-q-dafny", "verify-q-verus", "verify-r-dafny",
            "verify-r-verus", "pins", "empty-body", "corpus", "wrappers", "coexist", "paper",
            "rubric", "harness"]


def listed(out):
    return [m.group(1) for m in re.finditer(r"^  (\S+) ", out, re.M)]


class Options(unittest.TestCase):
    def test_list_names_every_job_in_run_order_and_runs_nothing(self):
        base = C.tmpdir("ci-list-")
        try:
            rc, out, err = C.run_ci("--list", logs=base / "logs")
            self.assertEqual(rc, 0, err)
            self.assertEqual(listed(out), ALL_JOBS)
            self.assertFalse((base / "logs").exists())
        finally:
            C.remove(base)

    def test_quick_is_static_and_hook_test(self):
        rc, out, _ = C.run_ci("--quick", "--list")
        self.assertEqual((rc, listed(out)), (0, ["static", "hook-test"]))

    def test_brittleness_only_on_request(self):
        rc, out, _ = C.run_ci("--brittleness", "--list")
        self.assertEqual((rc, listed(out)), (0, ALL_JOBS + ["brittleness"]))
        rc, out, _ = C.run_ci("--job", "brittleness", "--list")
        self.assertEqual((rc, listed(out)), (0, ["brittleness"]))

    def test_named_jobs_run_in_run_order(self):
        for args in (["--job", "paper", "--job", "static"], ["--job", "paper,static"],
                     ["paper", "static"], ["--job=paper", "static"]):
            rc, out, _ = C.run_ci(*args, "--list")
            self.assertEqual((rc, listed(out)), (0, ["static", "paper"]), args)

    def test_usage_errors_exit_2_and_run_nothing(self):
        base = C.tmpdir("ci-usage-")
        try:
            for args in (["--job", "nope"], ["--quick", "--job", "static"], ["--job"],
                         ["--bogus"], ["--root", str(base / "missing")], ["--job", ","]):
                rc, out, err = C.run_ci(*args, logs=base / "logs")
                self.assertEqual(rc, 2, (args, out, err))
                self.assertIn("ci.sh:", err)
                self.assertFalse((base / "logs").exists(), args)
        finally:
            C.remove(base)

    def test_help(self):
        rc, out, _ = C.run_ci("--help")
        self.assertEqual(rc, 0)
        self.assertIn("scripts/ci.sh --quick", out)
        self.assertIn("--author", out)


class CanonicalRules(unittest.TestCase):
    def test_ci_sh_names_the_canonical_rules_literally(self):
        text = C.CI_SH.read_text(encoding="utf-8")
        canon, always = C.course_lists()
        self.assertEqual(len(canon), 4)
        for rule in canon + always:
            self.assertIn(rule, text)
        for name, want in (("CANONICAL_DENY", canon), ("ALWAYS_ON", always)):
            block = re.search(rf"^{name}=\((.*?)\)\n", text, re.S | re.M).group(1)
            self.assertEqual(re.findall(r'"([^"]+)"', block), want, name)


class AuthorGate(unittest.TestCase):
    """--author: never on a learner branch; otherwise CI=true or the
    three-condition test (spec §7.4). A refusal exits 3 and writes nothing."""

    @classmethod
    def setUpClass(cls):
        cls.base = C.tmpdir("ci-author-")
        cls.home = cls.base / "home"
        cls.home.mkdir()
        cls.repo, cls.learner, cls.authoring = C.worktrees(cls.base)
        cls.nogit = cls.base / "nogit"
        cls.nogit.mkdir()

    @classmethod
    def tearDownClass(cls):
        C.remove(cls.base)

    def run_author(self, root, env=None, tag="x"):
        logs = self.base / f"logs-{tag}"
        rc, out, err = C.run_ci("--author", "--job", "harness", root=root, logs=logs,
                                home=self.home, env=env)
        return rc, out, err, logs

    def test_refused_on_a_learner_branch_even_with_ci_true(self):
        for env, tag in ((None, "l1"), ({"CI": "true"}, "l2")):
            rc, out, err, logs = self.run_author(self.learner, env, tag)
            self.assertEqual(rc, 3, (out, err))
            self.assertIn("learner branch (leobwang-test)", err)
            self.assertFalse(logs.exists())

    def test_refused_in_the_primary_worktree_and_outside_git(self):
        for root, why, tag in ((self.repo, "this is the primary worktree", "p"),
                               (self.nogit, "not inside a git checkout", "n")):
            rc, out, err, logs = self.run_author(root, tag=tag)
            self.assertEqual(rc, 3, (out, err))
            self.assertIn(why, err)
            self.assertFalse(logs.exists())

    def test_runs_in_a_linked_worktree_off_the_learner_branch(self):
        rc, out, err, logs = self.run_author(self.authoring, tag="a")
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("ci.sh: author run of", out)
        self.assertEqual(C.status_of(out, "harness"), "PASS")
        self.assertTrue((logs / "summary.txt").is_file())
        # the reference log directory is left only when it holds a log
        self.assertFalse(list((self.home / ".cache" / "dafny-verus-learn-0" / "ci").glob("*/scratch")))

    def test_ci_true_opens_author_mode_outside_git(self):
        rc, out, err, _ = self.run_author(self.nogit, {"CI": "true"}, "c")
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("ci.sh: author run of", out)

    def test_a_study_run_is_allowed_anywhere(self):
        for root, tag in ((self.learner, "s1"), (self.repo, "s2"), (self.nogit, "s3")):
            rc, out, err = C.run_ci("--job", "harness", root=root, logs=self.base / f"logs-{tag}",
                                    home=self.home)
            self.assertEqual(rc, 0, (out, err))
            self.assertIn("ci.sh: study run of", out)


class Runs(unittest.TestCase):
    """Statuses, exit codes and what reaches the console, on a planned-only
    root that mirrors this checkout's registry."""

    def setUp(self):
        self.base = C.tmpdir("ci-runs-")
        self.root = C.course_root(self.base)
        self.logs = self.base / "logs"

    def tearDown(self):
        C.remove(self.base)

    def assert_console_is_locations_only(self, out):
        for line in out.splitlines():
            self.assertRegex(line, C.CONSOLE_LINE)

    def test_a_failing_job_fails_the_run_and_the_others_still_run(self):
        (self.root / "paper" / "Q01_problems.tex").write_text("\\documentclass{article}\n",
                                                               encoding="utf-8")
        rc, out, err = C.run_ci("--job", "paper,harness", root=self.root, logs=self.logs)
        self.assertEqual(rc, 1, (out, err))
        self.assertEqual(C.status_of(out, "paper"), "FAIL")
        self.assertIn("make paper (exit 2)", C.job_line(out, "paper"))
        self.assertEqual(C.status_of(out, "harness"), "PASS")
        self.assertIn("ci.sh: FAIL — 1 passed, 1 failed, 0 skipped, 0 absent", out)
        # the tool's own message is in the log, never on the console
        self.assertNotIn("unpaired", out)
        self.assertIn("unpaired written-track files for: Q01", (self.logs / "paper.log").read_text())
        self.assert_console_is_locations_only(out)
        summary = (self.logs / "summary.txt").read_text()
        self.assertIn(C.job_line(out, "paper"), summary)
        self.assertIn("tool scratch kept for inspection", summary)

    def test_harness_passes_loudly_without_a_project_and_fails_on_a_broken_one(self):
        rc, out, _ = C.run_ci("--job", "harness", root=self.root, logs=self.logs)
        self.assertEqual(rc, 0)
        self.assertIn("nothing to test", C.job_line(out, "harness"))
        (self.root / "harness").mkdir()
        (self.root / "harness" / "pyproject.toml").write_text("", encoding="utf-8")
        rc, out, _ = C.run_ci("--job", "harness", root=self.root, logs=self.logs)
        self.assertEqual((rc, C.status_of(out, "harness")), (1, "FAIL"))

    def test_an_unusable_registry_fails_every_job_that_needs_it(self):
        (self.root / "MODULES.toml").write_text("schema = [\n", encoding="utf-8")
        rc, out, err = C.run_ci("--job", "verify-r-dafny,paper,coexist,harness", root=self.root,
                                logs=self.logs)
        self.assertEqual(rc, 1, (out, err))
        for job in ("verify-r-dafny", "paper", "coexist"):
            self.assertEqual(C.status_of(out, job), "FAIL", job)
            self.assertIn("registry", C.job_line(out, job))
        self.assertEqual(C.status_of(out, "harness"), "PASS")
        self.assertIn("unusable", (self.logs / "registry.log").read_text())
        self.assert_console_is_locations_only(out)

    def test_nothing_armed_passes_loudly(self):
        # No armed modules and no R given layer: exercise the true empty case,
        # independently of which provided layers this checkout has acquired.
        shutil.rmtree(self.root / "dafny/given/R", ignore_errors=True)
        rc, out, err = C.run_ci("--job", "verify-r-dafny,pins,coexist,paper", root=self.root,
                                logs=self.logs)
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("nothing to verify (16 R modules", C.job_line(out, "verify-r-dafny"))
        self.assertIn("pins.py passes loudly", C.job_line(out, "pins"))
        self.assertIn("nothing to resolve together", C.job_line(out, "coexist"))
        self.assertIn("nothing to build", C.job_line(out, "paper"))
        self.assertIn("no armed module: nothing to check", (self.logs / "pins.log").read_text())

    def test_an_unproved_given_fails_without_armed_modules(self):
        given = self.root / "dafny/given/R"
        shutil.rmtree(given, ignore_errors=True)
        given.mkdir(parents=True)
        (given / "RG_A1_Re.dfy").write_text(
            "module RG_A1_Re {\n"
            " lemma ProvidedMustHold() ensures false {}\n}\n",
            encoding="utf-8")
        rc, out, err = C.run_ci("--job", "verify-r-dafny", root=self.root,
                                logs=self.logs)
        self.assertEqual(rc, 1, (out, err))
        self.assertEqual(C.status_of(out, "verify-r-dafny"), "FAIL")
        log = (self.logs / "verify-r-dafny.log").read_text()
        self.assertIn("gate dafny/given/R/RG_A1_Re.dfy", log)
        self.assertIn("no armed R module with Dafny units", log)

    def test_author_only_jobs_are_skipped_and_reported_in_a_study_run(self):
        rc, out, err = C.run_ci("--job", "empty-body,rubric", root=self.root, logs=self.logs)
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(C.status_of(out, "empty-body"), "SKIP")
        self.assertEqual(C.status_of(out, "rubric"), "SKIP")
        self.assertIn("0 passed, 0 failed, 2 skipped", out)
        self.assertIn("the pre-merge gate is scripts/ci.sh --author", out)
        self.assertIn("skipped (author-only", (self.logs / "rubric.log").read_text())

    def test_solver_caps_above_the_budget_are_refused(self):
        checkout = self.base / "checkout"
        shutil.copytree(C.ROOT / "scripts", checkout / "scripts",
                        ignore=shutil.ignore_patterns("__pycache__"))
        pins = checkout / "scripts" / "dvl" / "pins.toml"
        text = pins.read_text(encoding="utf-8")
        self.assertEqual(text.count("\nmem_gb = 16\n"), 1)
        pins.write_text(text.replace("\nmem_gb = 16\n", "\nmem_gb = 32\n"), encoding="utf-8")
        rc, out, err = C.run_ci("--job", "harness", root=self.root, logs=self.logs,
                                script=checkout / "scripts" / "ci.sh")
        self.assertEqual(rc, 3, (out, err))
        self.assertIn("[verus] mem_gb = 32", err)
        self.assertFalse(self.logs.exists())


# --- the corpus job and its runner (Δ108, Δ109) ----------------------------------

COVERING_TEST = "tests/wrappers/test_fake_refusals.py::Refusals::test_flag_is_refused"
NO_HASH = "0" * 64           # a well-formed sha256 that no run is compared with here


def manifest(fid, lang, half, xclass, kind, files, tables, plain_exit=0):
    head = [f'id = "{fid}"', f'lang = "{lang}"', f'half = "{half}"', f'xclass = "{xclass}"',
            f'kind = "{kind}"', 'title = "an invented tests/ci fixture"',
            "files = [" + ", ".join(f'"{f}"' for f in files) + "]"]
    if kind != "covered-elsewhere":
        head.append(f"plain_exit = {plain_exit}")
    out = "# tests/ci: an invented fixture; the runner checks it statically and never runs it\n"
    out += "\n".join(head) + "\n"
    for t in tables:
        out += "\n[[expect]]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in t.items())
    return out


# A tiny invented corpus: a Dafny construct, a Dafny and a Verus control, and a
# covered row per language. Nothing in it is a catalog program.
FAKE_CORPUS = {
    "dafny/G01": ({"main.dfy": "lemma Fake() ensures true {}\n"},
                  ("Q", "X01", "construct", [{
                      "tool": "vaudit", "outcome": "flagged", "kinds": ["audit-axiom"],
                      "output_sha256": NO_HASH, "summary": "vaudit main.dfy: exit 1"}])),
    "dafny/C-01": ({"main.dfy": "lemma Fake() ensures true {}\n"},
                   ("R", "", "control", [{
                       "tool": "vcheck --gate", "outcome": "clean", "kinds": ["verdict:verified"],
                       "output_sha256": NO_HASH, "summary": "vcheck --gate main.dfy: exit 0"}])),
    "dafny/G07": ({}, ("Q", "X03", "covered-elsewhere", [{
        "tool": "vcheck --gate", "outcome": "flagged", "kinds": ["refused"],
        "summary": "the wrapper refuses the flag", "covered_by": [COVERING_TEST]}])),
    "verus/C-1": ({"Cargo.toml": '[package]\nname = "c1"\nversion = "0.1.0"\nedition = "2021"\n',
                   "src/lib.rs": "use vstd::prelude::*;\nverus! {\n}\n"},
                  ("Q", "", "control", [{
                      "tool": "vaudit", "outcome": "clean", "kinds": [],
                      "output_sha256": NO_HASH, "summary": "vaudit .: exit 0"}])),
    "verus/V18": ({}, ("R", "X03", "covered-elsewhere", [{
        "tool": "vcheck --gate", "outcome": "flagged", "kinds": ["refused"],
        "summary": "the wrapper refuses the flag", "covered_by": [COVERING_TEST]}])),
}


def checkout_copy(base, runner=True, corpus=True, name="checkout"):
    """base/<name>: a copy of this checkout's scripts/ (ci.sh's corpus job and
    test_corpus.py both test the checkout their scripts sit in), with the
    fake corpus and the test file its covered rows cite."""
    co = base / name
    shutil.copytree(C.ROOT / "scripts", co / "scripts",
                    ignore=shutil.ignore_patterns("__pycache__"))
    if not runner:
        (co / "scripts" / "test_corpus.py").unlink()
    if corpus:
        write_corpus(co)
    return co


def write_corpus(co):
    for rel, (files, (half, xclass, kind, tables)) in FAKE_CORPUS.items():
        lang, fid = rel.split("/")
        d = co / "tests" / "corpus" / rel
        d.mkdir(parents=True)
        for f, text in files.items():
            (d / f).parent.mkdir(parents=True, exist_ok=True)
            (d / f).write_text(text, encoding="utf-8")
        (d / "manifest.toml").write_text(
            manifest(fid, lang, half, xclass, kind, sorted(files), tables), encoding="utf-8")
    wr = co / "tests" / "wrappers"
    wr.mkdir(parents=True, exist_ok=True)
    (wr / "test_fake_refusals.py").write_text(
        "import unittest\n\n\nclass Refusals(unittest.TestCase):\n"
        "    def test_flag_is_refused(self):\n        pass\n", encoding="utf-8")


def stub_runner(co, listing):
    """Replace the runner by a stub that records its arguments, prints
    LISTING for --list and exits 0: it tests ci.sh's own handling."""
    (co / "scripts" / "test_corpus.py").write_text(
        "import json, sys\nfrom pathlib import Path\n"
        "with open(Path(__file__).with_name('calls.jsonl'), 'a') as fh:\n"
        "    fh.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        f"if sys.argv[1:] == ['--list']:\n    print({listing!r}, end='')\n", encoding="utf-8")
    return co / "scripts" / "calls.jsonl"


def manifests(co):
    return {p: p.read_bytes() for p in sorted((co / "tests" / "corpus").rglob("manifest.toml"))}


def run_runner(co, *args, env=None):
    """Run a checkout copy's test_corpus.py from that checkout: (exit, stdout, stderr)."""
    e = {k: v for k, v in os.environ.items() if k != "CI"}
    e.update(GIT_CEILING_DIRECTORIES=str(co.resolve().parent),
             DVL_SCRATCH=str(co.resolve().parent / "corpus-scratch"))
    e.update(env or {})
    p = subprocess.run([sys.executable, "-B", str(co / "scripts" / "test_corpus.py"), *args],
                       cwd=str(co), env=e, capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout, p.stderr


def mem_available_gb():
    try:
        with open("/proc/meminfo", encoding="ascii") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1048576
    except (OSError, ValueError, IndexError):
        pass
    return 0


class Corpus(unittest.TestCase):
    """The corpus job fails on an absent corpus (Δ108, Δ109): a missing runner,
    a missing tests/corpus/, a failed listing or an empty one, each before any
    solver step. The runner lists a tiny invented corpus, checks every manifest
    statically, and refuses --update outside the author's context."""

    def setUp(self):
        self.base = C.tmpdir("ci-corpus-")
        self.root = C.course_root(self.base)

    def tearDown(self):
        C.remove(self.base)

    def corpus_job(self, co, tag):
        logs = self.base / f"logs-{tag}"
        rc, out, err = C.run_ci("--job", "corpus", root=self.root, logs=logs,
                                script=co / "scripts" / "ci.sh")
        log = (logs / "corpus.log").read_text(encoding="utf-8") if logs.exists() else ""
        return rc, out, err, log

    def assert_fails(self, rc, out, err, why):
        self.assertEqual((rc, C.status_of(out, "corpus")), (1, "FAIL"), (out, err))
        self.assertIn(why, C.job_line(out, "corpus"))
        self.assertIn("ci.sh: FAIL — 0 passed, 1 failed, 0 skipped, 0 absent", out)
        for line in out.splitlines():
            self.assertRegex(line, C.CONSOLE_LINE)

    def test_a_missing_runner_fails(self):
        co = checkout_copy(self.base, runner=False)
        rc, out, err, _ = self.corpus_job(co, "corpus-without-runner")
        self.assert_fails(rc, out, err, "scripts/test_corpus.py does not exist")
        shutil.rmtree(co / "tests")          # nothing at all: the case Δ104 reported ABSENT
        rc, out, err, _ = self.corpus_job(co, "nothing")
        self.assert_fails(rc, out, err, "scripts/test_corpus.py does not exist")

    def test_a_missing_or_empty_corpus_fails_before_any_solver(self):
        co = checkout_copy(self.base, corpus=False)
        rc, out, err, log = self.corpus_job(co, "no-dir")
        self.assert_fails(rc, out, err, "tests/corpus/ does not exist")
        self.assertNotIn("[test_corpus --list]", log)       # no step ran
        for lang in ("dafny", "verus"):
            (co / "tests" / "corpus" / lang).mkdir(parents=True)
        rc, out, err, log = self.corpus_job(co, "empty")
        self.assert_fails(rc, out, err, "test_corpus --list (exit 1)")
        self.assertIn("the corpus lists no fixture (an empty set fails)", log)
        self.assertIn("[test_corpus --list] exit 1", log)
        self.assertNotIn("[test_corpus --ci]", log)          # the --ci step never started

    def test_an_empty_listing_fails(self):
        co = checkout_copy(self.base)
        calls = stub_runner(co, "")
        rc, out, err, _ = self.corpus_job(co, "empty-listing")
        self.assert_fails(rc, out, err, "test_corpus --list lists no fixture")
        self.assertEqual(calls.read_text(encoding="utf-8").splitlines(), ['["--list"]'])

    def test_a_listing_is_followed_by_the_ci_run(self):
        if mem_available_gb() < 31:
            self.skipTest("ci.sh's memory preflight before --ci needs 31 GB available")
        co = checkout_copy(self.base)
        calls = stub_runner(co, "C-01   dafny  R  control           -    tests/corpus/dafny/C-01\n")
        rc, out, err, log = self.corpus_job(co, "listed")
        self.assertEqual((rc, C.status_of(out, "corpus")), (0, "PASS"), (out, err, log))
        self.assertEqual(calls.read_text(encoding="utf-8").splitlines(),
                         ['["--list"]', '["--ci"]'])
        self.assertIn("test_corpus --list: 1 fixture(s) listed", log)

    def test_a_fixture_outside_the_canonical_layout_fails(self):
        # The runner lists a second G01 under Δ106's <ID>_<slug>/ name; the
        # job refuses it before any solver step (Δ109: tests/corpus/<lang>/<ID>/).
        co = checkout_copy(self.base)
        shutil.copytree(co / "tests" / "corpus" / "dafny" / "G01",
                        co / "tests" / "corpus" / "dafny" / "G01_axiom")
        rc, out, err = run_runner(co, "--list")
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual([line.split()[0] for line in out.splitlines()].count("G01"), 2)
        rc, out, err, log = self.corpus_job(co, "slug")
        self.assert_fails(rc, out, err, "corpus layout")
        self.assertIn("a fixture directory is not tests/corpus/<lang>/<ID>/: "
                      "tests/corpus/dafny/G01_axiom (id G01)", log)
        self.assertNotIn("[test_corpus --ci]", log)

    def test_the_runner_lists_and_checks_a_tiny_fake_corpus(self):
        co = checkout_copy(self.base)
        rc, out, err = run_runner(co, "--list")
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual([line.split()[0] for line in out.splitlines()],
                         ["G01", "G07", "C-01", "V18", "C-1"])
        # --ci on a covered row: the static checks of every manifest, no solver
        rc, out, err = run_runner(co, "--ci", "--only", "G07")
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("1 passed, 0 failed; 0 run (0 plain run(s), 0 instrument run(s))", out)
        self.assertIn("2 test reference(s) resolved in the whole corpus", out)
        self.assertIn("test_corpus: ci: PASS", out)
        # a broken manifest outside the selection fails it, statically, by location
        mp = co / "tests" / "corpus" / "dafny" / "C-01" / "manifest.toml"
        mp.write_text(mp.read_text(encoding="utf-8").replace('outcome = "clean"',
                                                             'outcome = "flagged"'),
                      encoding="utf-8")
        rc, out, err = run_runner(co, "--ci", "--only", "G07")
        self.assertEqual(rc, 1, (out, err))
        self.assertRegex(out, r"tests/corpus/dafny/C-01/manifest\.toml:\d+: vcheck --gate: a "
                              r"control is clean on every instrument")
        self.assertIn("0 run (0 plain run(s)", out)

    def test_update_refuses_outside_the_authors_context(self):
        repo, learner, authoring = C.worktrees(self.base)
        nogit = self.base / "nogit"
        refused = {"not inside a git checkout": nogit, "this is the primary worktree": repo,
                   "HEAD is on a learner branch": learner}
        for why, co in refused.items():
            checkout_copy(co.parent, name=co.name)
            before = manifests(co)
            rc, out, err = run_runner(co, "--update", "--only", "G07")
            self.assertEqual(rc, 3, (why, out, err))
            self.assertIn(f"test_corpus: refused: --update is author-only and refuses to run "
                          f"here ({why})", err)
            self.assertEqual(manifests(co), before, why)
        # the author's linked worktree off the learner branch: the gate opens; a
        # covered row runs nothing and re-pins nothing
        checkout_copy(authoring.parent, name=authoring.name)
        before = manifests(authoring)
        rc, out, err = run_runner(authoring, "--update", "--only", "G07")
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("test_corpus: --update re-pinned 0 value(s)", out)
        self.assertEqual(manifests(authoring), before)
        # a mistyped prefix is a usage error: the parser takes no abbreviation
        rc, out, err = run_runner(authoring, "--up", "--only", "G07")
        self.assertEqual(rc, 2, (out, err))

    def test_update_rewrites_only_the_pinned_values(self):
        # --update's rewrite step, in process on a copy of the runner, with
        # invented results (the step that runs the fixtures twice is not used)
        co = checkout_copy(self.base)
        new = co / "tests" / "corpus" / "dafny" / "G02"
        new.mkdir()
        (new / "main.dfy").write_text("lemma Fake() ensures true {}\n", encoding="utf-8")
        text = manifest("G02", "dafny", "R", "X01", "construct", ["main.dfy"], [{
            "tool": "vaudit", "outcome": "flagged", "kinds": ["audit-axiom"],
            "summary": "vaudit main.dfy: exit 1"}]).replace("plain_exit = 0\n", "")
        (new / "manifest.toml").write_text(text, encoding="utf-8")
        name = f"corpus_runner_copy_{id(self)}"
        spec = importlib.util.spec_from_file_location(name, co / "scripts" / "test_corpus.py")
        R = importlib.util.module_from_spec(spec)
        saved_path, saved_modules = list(sys.path), set(sys.modules)
        sys.modules[name] = R
        try:
            spec.loader.exec_module(R)
            fixtures, probs = R.load_corpus()
            self.assertEqual(probs, [])
            by_id = {f.id: f for f in fixtures}
            # a recorded hash re-pinned in place: one line changes, comments stay
            g01 = by_id["G01"]
            old = g01.text
            self.assertEqual(R.rewrite(g01, R.Result(g01, updated=[(0, "a" * 64)])), 1)
            now = (g01.dir / "manifest.toml").read_text(encoding="utf-8")
            self.assertEqual(now, old.replace(NO_HASH, "a" * 64))
            # a new fixture: the missing hash and plain_exit are filled in
            g02 = by_id["G02"]
            self.assertEqual(R.rewrite(g02, R.Result(g02, updated=[(0, "b" * 64)],
                                                     fill_plain=1)), 2)
            now = (g02.dir / "manifest.toml").read_text(encoding="utf-8")
            self.assertTrue(now.startswith("# tests/ci: an invented fixture"))
            want = tomllib.loads(text)
            want["plain_exit"] = 1
            want["expect"][0]["output_sha256"] = "b" * 64
            self.assertEqual(tomllib.loads(now), want)
        finally:      # the copy's scripts/ leaves sys.path and sys.modules again
            sys.path[:] = saved_path
            for m in set(sys.modules) - saved_modules:
                sys.modules.pop(m, None)


class StudyModeShipped(unittest.TestCase):
    """The static job's study-mode check (spec §7.4, §8.5; Δ80, Δ87)."""

    @classmethod
    def setUpClass(cls):
        cls.base = C.tmpdir("ci-static-")
        cls.root = C.course_root(cls.base)

    @classmethod
    def tearDownClass(cls):
        C.remove(cls.base)

    def test_shipped_then_mid_authoring(self):
        logs = self.base / "clean"
        rc, out, err = C.run_ci("--job", "static", root=self.root, logs=logs)
        self.assertEqual(rc, 0, (out, err, (logs / "static.log").read_text()))
        self.assertIn("study mode shipped: yes", (logs / "static.log").read_text())
        self.assertIn("specfreeze: no armed module", C.job_line(out, "static"))
        self.assertIn("chapter_lint: no armed module, no chapter to lint", C.job_line(out, "static"))

        canon, always = C.course_lists()
        C.write_settings(self.root, [r for r in canon + always if r != canon[1]])
        (self.root / ".claude" / "state").mkdir()
        (self.root / ".claude" / "state" / "mode").write_text("authoring\n", encoding="utf-8")
        logs = self.base / "dirty"
        rc, out, err = C.run_ci("--job", "static", root=self.root, logs=logs)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("study mode shipped (exit 1)", C.job_line(out, "static"))
        log = (logs / "static.log").read_text()
        self.assertIn(".claude/state/mode exists (it says authoring)", log)
        self.assertIn(f"the canonical deny rule {canon[1]} is missing", log)
        self.assertNotIn(canon[1], out)
        for line in out.splitlines():
            self.assertRegex(line, C.CONSOLE_LINE)


def ci_helper_source():
    """The Python helper ci.sh runs as `py <subcommand>` (its HELPER here-document)."""
    text = C.CI_SH.read_text(encoding="utf-8")
    m = re.search(r"^HELPER=\"\$\(cat <<'PY'\n(.*?)\nPY\n\)\"$", text, re.S | re.M)
    assert m, "ci.sh holds no HELPER here-document"
    return m.group(1)


class HolesStep(unittest.TestCase):
    """The verify jobs' `holes <ID> <lang>` step (ci.sh's helper, run directly):
    an armed module whose unit files are absent fails cleanly, file by file,
    in either language, with no traceback (DV3a follow-up)."""

    def setUp(self):
        self.base = C.tmpdir("ci-holes-")
        self.addCleanup(C.remove, self.base)
        self.root = self.base / "root"
        self.root.mkdir()
        shutil.copyfile(C.ROOT / "MODULES.toml", self.root / "MODULES.toml")
        with open(self.root / "MODULES.toml", "rb") as f:
            q04 = next(m for m in tomllib.load(f)["module"] if m["id"] == "Q04")
        self.assertNotEqual(q04["status"], "planned")
        self.q04 = q04

    def holes(self, lang, results):
        j = self.base / f"Q04.{lang}.json"
        j.write_text(json.dumps({"results": results, "problems": [], "checked": 0}))
        env = {**os.environ, "DVLCI_ROOT": str(self.root),
               "DVLCI_SCRIPTS": str(C.ROOT / "scripts")}
        p = subprocess.run([sys.executable, "-B", "-c", ci_helper_source(), "holes", "Q04", lang,
                            str(j)], capture_output=True, text=True, env=env, timeout=300)
        return p.returncode, p.stdout, p.stderr

    def test_missing_unit_files_fail_cleanly(self):
        for lang, ext in (("d", ".dfy"), ("v", ".rs")):
            unit = next(u for u in self.q04["units"] if u.startswith("dafny/" if lang == "d"
                                                                     else "verus/"))
            files = [p for p in self.q04["exercises"] if p.endswith(ext)
                     and p.startswith(unit.rstrip("/") + "/")]
            self.assertTrue(files)
            rc, out, err = self.holes(lang, [{"unit": unit, "holes": []}])
            self.assertEqual(rc, 1, (lang, out, err))
            self.assertNotIn("Traceback", out + err)
            for f in files:
                self.assertIn(f"{f}: the registry lists this unit file of Q04 and it does not "
                              "exist", out)
            self.assertRegex(out, rf"Q04 {lang}: 0 hole\(s\) counted by the tool in 1 unit\(s\); "
                                  rf"0 hole form\(s\) shipped in \d+ exercise file\(s\); "
                                  rf"0 mismatch\(es\); \d+ unit file\(s\) missing or unreadable")

    def test_an_unreadable_unit_file_fails_cleanly(self):
        f = next(p for p in self.q04["exercises"] if p.endswith(".dfy"))
        (self.root / f).parent.mkdir(parents=True)
        (self.root / f).write_bytes(b"\xff\xfe\x00 not utf-8")
        unit = next(u for u in self.q04["units"] if f.startswith(u.rstrip("/") + "/"))
        rc, out, err = self.holes("d", [{"unit": unit, "holes": []}])
        self.assertEqual(rc, 1, (out, err))
        self.assertNotIn("Traceback", out + err)
        self.assertIn("Q04: its items cannot be parsed: a module file is unreadable "
                      "(UnicodeDecodeError); no hole form counted", out)


if __name__ == "__main__":
    unittest.main()
