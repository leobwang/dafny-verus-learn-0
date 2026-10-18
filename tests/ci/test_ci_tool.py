"""scripts/ci.sh on an armed course root: the verify, coexist and pins jobs run
the pinned verifiers (one job at a time, under the dvl caps: Dafny 8 GB,
Verus 16 GB). Every expected outcome was captured from a real run on the pins.

The root is the tools suites' throwaway root (tests/wrappers/test_tools_common:
the synthetic armed Q04, its invented given layers, specimens and units). Its
Verus given crates are empty placeholders, which the given-layer gate rightly
fails (a gate needs a positive count, Δ11), so setUpClass gives each one
trivially true proof fn. The verify jobs compare every file with its
shipped-state pin (vcheck --shipped), so setUpClass also writes
expected/Q04.counts the way an author arms a module (vcheck --ref
--pin-counts over the tools suites' invented twins, which a study run never
reads afterwards). Nothing here is course content or an answer.

Run: python3 -B -m unittest discover -s tests/ci -p 'test_ci_tool.py'
"""

import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "wrappers"))
import ci_common as C  # noqa: E402
import test_tools_common as T  # noqa: E402

CORE = "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"
STD = "dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy"
REFERENCE = HERE.parent / "wrappers" / "fixtures" / "tools" / "reference"
SCRIPTS = C.ROOT / "scripts"


def given_crate_fn(root):
    for lib in sorted((root / "verus" / "given").glob("*/src/lib.rs")):
        text = lib.read_text(encoding="utf-8")
        assert "verus! {\n" in text, lib
        name = lib.parent.parent.name
        lib.write_text(text.replace(
            "verus! {\n", "verus! {\n\n// tests/ci: one trivially verified fn, so the given-layer "
            f"gate counts a task.\npub proof fn ci_fixture_{name}()\n    ensures 1 + 1 == 2,\n"
            "{\n}\n", 1), encoding="utf-8")


class ArmedRoot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = T.build_root(git=False)
        given_crate_fn(cls.root)
        cls.base = C.tmpdir("ci-tool-")
        shutil.copytree(REFERENCE, cls.root / "Solutions")
        rc, out, err = T.tool("vcheck", "--ref", "--pin-counts", "Q04", root=cls.root,
                              env={"CI": "true"})
        assert rc == 0, (out, err)

    @classmethod
    def tearDownClass(cls):
        T.remove_root(cls.root)
        C.remove(cls.base)
        C.remove(cls.root.parent / "ci-work")

    def run_jobs(self, jobs, tag, env=None):
        logs = self.base / tag
        rc, out, err = C.run_ci("--job", jobs, root=self.root, logs=logs, env=env)
        for line in out.splitlines():
            self.assertRegex(line, C.CONSOLE_LINE)
        return rc, out, err, logs

    def edit(self, rel, old, new):
        """Edit a root file for one test; the cleanup restores it."""
        p = self.root / rel
        saved = p.read_text(encoding="utf-8")
        self.addCleanup(p.write_text, saved, encoding="utf-8")
        assert saved.count(old) == 1, (rel, old)
        p.write_text(saved.replace(old, new), encoding="utf-8")

    def test_armed_track_verifies_with_holes_as_shipped(self):
        rc, out, err, logs = self.run_jobs("verify-q-dafny,verify-q-verus,verify-r-verus,coexist",
                                           "green")
        self.assertEqual(rc, 0, (out, err))
        for job in ("verify-q-dafny", "verify-q-verus", "verify-r-verus", "coexist"):
            self.assertEqual(C.status_of(out, job), "PASS", job)
        d = (logs / "verify-q-dafny.log").read_text()
        self.assertIn("[shipped Q04 d] exit 0", d)
        self.assertIn("Q04 d: 5 file(s) checked against their shipped-state pins; 0 problem(s)", d)
        self.assertIn("Q04 d: 3 hole(s) counted by the tool in 2 unit(s); 3 hole form(s) shipped "
                      "in 2 exercise file(s); 0 mismatch(es)", d)
        for layer in ("QG_L1_BigNat", "QG_L2_BigNat", "QG_L3_BigNat"):
            self.assertIn(f"[gate dafny/given/Q/{layer}.dfy] exit 0", d)
            self.assertIn(f"[audit dafny/given/Q/{layer}.dfy] exit 0", d)
        v = (logs / "verify-q-verus.log").read_text()
        self.assertIn("Q04 v: 4 file(s) checked against their shipped-state pins; 0 problem(s)", v)
        self.assertIn("Q04 v: 2 hole(s) counted by the tool in 1 unit(s); 2 hole form(s) shipped "
                      "in 2 exercise file(s); 0 mismatch(es)", v)
        self.assertIn("[vaudit --check-trust] exit 0", v)
        # vaudit --check-trust runs once per run, in the first Verus job
        self.assertNotIn("--check-trust", (logs / "verify-r-verus.log").read_text())
        self.assertIn("nothing to verify (16 R modules", C.job_line(out, "verify-r-verus"))
        self.assertTrue((logs / "verify-q-dafny" / "Q04.d.json").is_file())
        c = (logs / "coexist.log").read_text()
        self.assertIn("coexist: 2 Dafny unit(s), 5 file(s), resolve as one program", c)
        self.assertIn("coexist: 4 Verus crate(s), 0 duplicate name(s)", c)
        # 2 unit twins and the check, exit and agent twins, each gated and audited
        self.assertIn("10 author-only step(s) skipped", C.job_line(out, "verify-q-dafny"))

    def test_a_stray_hole_fails_the_hole_count(self):
        # Before the first item marker, so no item owns it (an item's block runs to
        # the next marker or the closing brace: a hole appended at the end of the
        # module belongs to the last item, and both counts agree).
        self.edit(CORE, "  import opened QG_L2_BigNat\n",
                  "  import opened QG_L2_BigNat\n\n  lemma CiStray(x: nat)\n    ensures x == x\n")
        rc, out, err, logs = self.run_jobs("verify-q-dafny", "stray")
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("holes Q04 d (exit 1)", C.job_line(out, "verify-q-dafny"))
        self.assertIn("shipped Q04 d (exit 1)", C.job_line(out, "verify-q-dafny"))
        log = (logs / "verify-q-dafny.log").read_text()
        self.assertIn(f"shipped: {CORE}: not in its shipped state: pinned exercise verified, 2 "
                      "hole(s), 0 error(s); the learner loop gives exercise verified, 3 hole(s)",
                      log)
        self.assertRegex(log, rf"{CORE}: \S*CiStray: the tool counts 1 hole\(s\), the file ships "
                              r"0 hole form\(s\)")
        self.assertIn("1 mismatch(es)", log)

    def test_a_duplicate_declaration_across_units_fails_coexist(self):
        self.edit(STD, "  const T1 := 0\n}\n", "  const T1 := 0\n}\n\nmodule Q04_ProofCraft {\n}\n")
        rc, out, err, logs = self.run_jobs("coexist", "dup")
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("dafny: both tracks resolve as one program (exit 1)",
                      C.job_line(out, "coexist"))
        log = (logs / "coexist.log").read_text()
        self.assertIn("do not resolve as one program", log)
        self.assertRegex(log, r"(?m)^dafny/Q/Q04_ProofCraft/\S+\.dfy:\d+:\d+: error$")

    def test_brittleness_on_request(self):
        rc, out, err, logs = self.run_jobs("brittleness", "brittle")
        self.assertEqual((rc, C.status_of(out, "brittleness")), (0, "PASS"), (out, err))
        log = (logs / "brittleness.log").read_text()
        for target in ("dafny/given/Q/QG_L3_BigNat.dfy", "verus/given/qg_bignat_l3", "Q04 d",
                       "Q04 v"):
            self.assertIn(f"[brittleness {target}] exit 0", log)
        self.assertIn("seed 1: verified · seed 2: verified · seed 3: verified — stable", log)

    def test_ci_never_reaches_a_study_run(self):
        """Without --author, CI=true in the caller's environment is dropped, so
        pins.py --ci skips its reference half (this root is not in git)."""
        rc, out, err, logs = self.run_jobs("pins", "ci-env", env={"CI": "true"})
        self.assertIn("ci.sh: study run of", out)
        log = (logs / "pins.log").read_text()
        self.assertIn("the reference half (verdict pins against the reference answers) skipped: "
                      "not the author's context (not inside a git checkout)", log)
        self.assertIn("skipped (author-only, runs with --author): pins.py --ref", log)


class AuthorRun(unittest.TestCase):
    """--author on an armed linked worktree (off the learner branch) whose
    Solutions/ holds the tools suites' invented twins
    (tests/wrappers/fixtures/tools/reference/), armed the way an author arms a
    module: vcheck --ref --pin-counts, pins.py --update --ref, specfreeze --pin.
    The reference steps' output goes to ~/.cache/dafny-verus-learn-0/ci/<run>/,
    which each test removes afterwards."""

    @classmethod
    def setUpClass(cls):
        cls.base = C.tmpdir("ci-author-tool-")
        primary = T.build_root(git=True)
        cls.primary = primary
        cls.root = cls.base / "wt"
        C.git("worktree", "add", "-q", "-b", "authoring", str(cls.root), cwd=primary)
        shutil.copytree(REFERENCE, cls.root / "Solutions")
        given_crate_fn(cls.root)
        env = {**os.environ, "GIT_CEILING_DIRECTORIES": str(cls.base),
               "DVL_SCRATCH": str(cls.base / "arm-scratch"), "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("CI", None)
        for argv in (["vcheck", "--ref", "--pin-counts", "Q04"],
                     ["pins.py", "--update", "--ref", "--module", "Q04"],
                     ["specfreeze", "--pin", "Q04"]):
            p = subprocess.run([sys.executable, "-B", str(SCRIPTS / argv[0]), *argv[1:],
                                f"--root={cls.root}"], capture_output=True, text=True, env=env,
                               timeout=1800)
            assert p.returncode == 0, (argv, p.stdout, p.stderr)

    @classmethod
    def tearDownClass(cls):
        T.remove_root(cls.primary)
        C.remove(cls.base)

    def run_author(self, jobs, tag):
        logs = self.base / tag
        rc, out, err = C.run_ci("--author", "--job", jobs, root=self.root, logs=logs,
                                env={"GIT_CEILING_DIRECTORIES": str(self.base),
                                     "DVL_CI_WORK": str(self.base / "ci-work")})
        m = re.search(r"^ci\.sh: reference logs: ~/(\S+)/$", out, re.M)
        self.assertTrue(m, (out, err))
        refdir = Path.home() / m.group(1)
        self.assertTrue(str(refdir).startswith(str(Path.home() / ".cache" / "dafny-verus-learn-0"
                                                   / "ci")), refdir)
        self.addCleanup(shutil.rmtree, refdir, True)
        for line in out.splitlines():
            self.assertRegex(line, C.CONSOLE_LINE)
        return rc, out, err, logs, refdir

    def test_reference_steps_run_with_locations_only_in_the_job_log(self):
        rc, out, err, logs, ref = self.run_author("verify-q-dafny,verify-q-verus,pins,coexist",
                                                  "green")
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("ci.sh: author run of", out)
        for job in ("verify-q-dafny", "verify-q-verus", "pins", "coexist"):
            self.assertEqual(C.status_of(out, job), "PASS", job)
        d = (ref / "verify-q-dafny.ref.log").read_text()
        for unit, n in (("core", 7), ("std", 3)):
            self.assertIn(f"vcheck: Solutions/dafny/Q/Q04_ProofCraft/{unit} [dafny, reference "
                          f"gate]: verified — {n} verified, 0 holes, 0 errors", d)
            self.assertIn(f"vaudit: Solutions/dafny/Q/Q04_ProofCraft/{unit} [dafny, reference]: "
                          "0 finding(s)", d)
        vl = (logs / "verify-q-verus.log").read_text()
        self.assertIn("[reference gate verus/q/q04_proof_craft] exit 0", vl)
        for f in ("verus/q/q04_proof_craft/src/exit.rs", "verus/q/q04_proof_craft/src/agent.rs"):
            self.assertIn(f"[reference gate {f}] exit 0", vl)
            self.assertIn(f"[reference audit {f}] exit 0", vl)
        dl = (logs / "verify-q-dafny.log").read_text()
        for f in ("dafny/checks/Q04_checks.dfy", "dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy",
                  "dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy"):
            self.assertIn(f"[reference gate {f}] exit 0", dl)
            self.assertIn(f"[reference audit {f}] exit 0", dl)
        self.assertIn("pins --ref: 7 check(s); 0 problem(s)", (ref / "pins.ref.log").read_text())
        # the job log holds the reference step's command and exit code, never its output
        jl = (logs / "verify-q-dafny.log").read_text()
        self.assertIn("(output: ~/.cache/dafny-verus-learn-0/ci/", jl)
        self.assertNotIn("reference gate]:", jl)
        # a passing run keeps only the reference scratch that a log names (each raw_dir)
        scratch = ref / "scratch"
        if scratch.exists():
            self.assertIn("ci.sh: reference scratch the logs name kept:", out)
            named = "".join(f.read_text(errors="replace") for f in
                            [*ref.glob("*.ref.log"), *logs.rglob("*")] if f.is_file())
            for top in scratch.rglob("*"):
                if top.is_dir() and top.parent.parent == scratch:
                    self.assertIn(str(top), named, "kept, but no log names it")
        else:
            self.assertNotIn("reference scratch the logs name kept", out)

    def test_a_stale_or_missing_twin_fails_verify(self):
        twin = self.root / "Solutions" / STD
        saved = twin.read_text(encoding="utf-8")
        self.addCleanup(twin.write_text, saved, encoding="utf-8")
        twin.write_text(saved.replace("  // item: Q04.T1dv", "  // reference-only: a helper\n"
                                      "  lemma Extra(x: nat)\n    ensures x + 1 > x\n  {\n  }\n\n"
                                      "  // item: Q04.T1dv", 1), encoding="utf-8")
        core = self.root / "Solutions" / "dafny" / "Q" / "Q04_ProofCraft" / "core"
        moved = self.base / "core-twin"
        core.rename(moved)
        self.addCleanup(moved.rename, core)
        agent = self.root / "Solutions" / "dafny" / "Q" / "Q04_ProofCraft" / "agent"
        moved_agent = self.base / "agent-twin"
        agent.rename(moved_agent)
        self.addCleanup(moved_agent.rename, agent)
        rc, out, err, logs, ref = self.run_author("verify-q-dafny", "broken")
        self.assertEqual(rc, 1, (out, err))
        line = C.job_line(out, "verify-q-dafny")
        self.assertIn("twin of dafny/Q/Q04_ProofCraft/core", line)
        self.assertIn("twin of dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy", line)
        self.assertIn("reference gate dafny/Q/Q04_ProofCraft/std (exit 1)", line)
        self.assertNotIn("count-pin-stale", out)
        self.assertIn("Solutions/dafny/Q/Q04_ProofCraft/std: count-pin-stale",
                      (ref / "verify-q-dafny.ref.log").read_text())


if __name__ == "__main__":
    unittest.main()
