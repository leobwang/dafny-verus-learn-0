"""Tool-free tests for the shipped reference (the user's decision D26):
scripts/vcheck's shipped_base, which scripts/firsttry.py and scripts/pins.py
share, takes the newest merge base of HEAD with the shipped branches basic /
challenge (local or origin/) that exist, and falls back to main / origin/main,
exactly as before, while none of them exists.

Each case builds a throwaway git repository: a small one of invented files for
the helper itself, and the synthetic armed course root
(test_tools_common.build_root) for the tools end to end. No verifier runs.

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_shipped_ref_static.py'
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tools_common as C  # noqa: E402

core = C.load_script("vcheck")

# A neutral fixture file the tools read as a specimen with no item in it.
NEUTRAL = "// A neutral fixture file: it holds no item.\n"


class Repo:
    """A throwaway git repository with a fixed identity and a clock that
    advances one minute per commit (so committer times are ordered)."""

    def __init__(self, root):
        self.root = Path(root)
        self.clock = 1_700_000_000

    def git(self, *args):
        self.clock += 60
        stamp = f"{self.clock} +0000"
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
               "GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp,
               "GIT_CEILING_DIRECTORIES": str(self.root.resolve().parent)}
        for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            env.pop(k, None)
        r = subprocess.run(["git", "-C", str(self.root), *args], check=True,
                           capture_output=True, text=True, env=env)
        return r.stdout.strip()

    def write(self, rel, text="x\n"):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def merge(self, ref):
        self.git("merge", "-q", "--no-edit", "--no-ff", ref)
        return self.git("rev-parse", "HEAD")


def shipped(root):
    core._BASE.clear()            # the helper caches per root: each probe is fresh
    return core.shipped_base(root)


def gone(root, rels=("ex/",)):
    core._BASE.clear()
    return core.gone_files(root, list(rels))


# =====================================================================================
# The helper: shipped_base and gone_files on a small invented repository
# =====================================================================================

class Helper(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dvl-shipref-", dir=C.TMP_BASE))
        self.r = Repo(self.tmp)
        self.r.git("init", "-q", "-b", "main")
        self.r.write("DESIGN.md")
        self.design = self.r.commit("design only")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def basic(self, *files):
        """basic from main, adding ex/<f> for each f; HEAD stays on basic."""
        self.r.git("switch", "-q", "-c", "basic", "main")
        for f in files:
            self.r.write(f"ex/{f}")
        return self.r.commit("basic")

    def challenge(self, *files):
        """challenge from basic, adding ex/<f> for each f; HEAD on challenge."""
        self.r.git("switch", "-q", "-c", "challenge", "basic")
        for f in files:
            self.r.write(f"ex/{f}")
        return self.r.commit("challenge")

    def study(self, start):
        self.r.git("switch", "-q", "-c", "leobwang-test", start)

    def rm(self, rel):
        os.remove(self.tmp / rel)

    # --- only main: the behaviour before D26 --------------------------------------
    def test_only_main(self):
        self.r.write("ex/a.dfy")
        m = self.r.commit("course on main")
        self.study("main")
        self.r.write("ex/a.dfy", "mine\n")
        self.r.commit("work")
        self.assertEqual(shipped(self.tmp), m)
        self.assertEqual(gone(self.tmp), [])
        self.rm("ex/a.dfy")
        self.assertEqual(gone(self.tmp), ["ex/a.dfy"])

    def test_only_main_origin_main_newer(self):
        """The fallback keeps its rule: the newer of main and origin/main."""
        self.r.write("ex/a.dfy")
        self.r.commit("course on main")
        self.r.git("switch", "-q", "-c", "upstream")
        self.r.write("ex/b.dfy")
        up = self.r.commit("an update upstream")
        self.r.git("update-ref", "refs/remotes/origin/main", up)
        self.r.git("switch", "-q", "main")
        self.r.git("branch", "-q", "-D", "upstream")
        self.study("main")
        self.r.merge("origin/main")
        self.assertEqual(shipped(self.tmp), up)
        self.rm("ex/b.dfy")
        self.assertEqual(gone(self.tmp), ["ex/b.dfy"])

    def test_no_branch_at_all(self):
        self.r.git("switch", "-q", "-c", "leobwang-test")
        self.r.git("branch", "-q", "-D", "main")
        self.assertIsNone(shipped(self.tmp))
        self.assertEqual(gone(self.tmp), [])

    # --- basic only ----------------------------------------------------------------
    def test_basic_only(self):
        b = self.basic("a.dfy", "b.rs")
        self.study("basic")
        self.r.write("ex/a.dfy", "mine\n")
        self.r.commit("work")
        self.assertEqual(shipped(self.tmp), b)
        self.rm("ex/b.rs")
        self.assertEqual(gone(self.tmp), ["ex/b.rs"])

    def test_basic_wins_over_a_merged_main(self):
        """Once basic exists, main is not consulted, even when HEAD merged a main
        commit that basic lacks (main is retired to the design)."""
        b = self.basic("a.dfy")
        self.r.git("switch", "-q", "main")
        self.r.write("ex/m.dfy")
        self.r.commit("a commit on main only")
        self.study("basic")
        self.r.merge("main")
        self.assertEqual(shipped(self.tmp), b)
        self.rm("ex/a.dfy")
        self.rm("ex/m.dfy")
        self.assertEqual(gone(self.tmp), ["ex/a.dfy"])       # ex/m.dfy never shipped

    def test_origin_basic_only(self):
        """A learner clone may hold only the remote-tracking ref."""
        b = self.basic("a.dfy")
        self.r.git("update-ref", "refs/remotes/origin/basic", b)
        self.r.git("switch", "-q", "--detach", b)
        self.r.git("branch", "-q", "-D", "basic")
        self.study("origin/basic")
        self.assertEqual(shipped(self.tmp), b)
        self.rm("ex/a.dfy")
        self.assertEqual(gone(self.tmp), ["ex/a.dfy"])

    def test_a_tag_named_basic_is_no_shipped_branch(self):
        self.r.write("ex/a.dfy")
        m = self.r.commit("course on main")
        self.r.git("tag", "basic", self.design)
        self.study("main")
        self.assertEqual(shipped(self.tmp), m)

    def test_basic_with_no_shared_history_falls_back(self):
        self.r.write("ex/a.dfy")
        m = self.r.commit("course on main")
        self.r.git("switch", "-q", "--orphan", "basic")
        self.r.write("ex/z.dfy")
        self.r.commit("unrelated")
        self.study("main")
        self.assertEqual(shipped(self.tmp), m)

    # --- basic, then challenge merged into the study branch -------------------------
    def test_challenge_merged(self):
        self.basic("a.dfy")
        self.study("basic")
        self.r.write("ex/a.dfy", "mine\n")
        self.r.commit("work")
        c = self.challenge("c.dfy")
        self.r.git("switch", "-q", "leobwang-test")
        self.r.merge("challenge")
        self.assertEqual(shipped(self.tmp), c)
        self.assertEqual(gone(self.tmp), [])
        self.rm("ex/c.dfy")                                  # challenge's new file
        self.assertEqual(gone(self.tmp), ["ex/c.dfy"])
        self.rm("ex/a.dfy")
        self.assertEqual(gone(self.tmp), ["ex/a.dfy", "ex/c.dfy"])

    def test_challenge_merged_fix_forwarded(self):
        """A fix lands on basic and is merged forward into challenge at once; a
        study branch on challenge that merges challenge again sees the fix."""
        self.basic("a.dfy")
        self.challenge("c.dfy")
        self.study("challenge")
        self.r.git("switch", "-q", "basic")
        self.r.write("ex/f.dfy")
        self.r.commit("a fix on basic")
        self.r.git("switch", "-q", "challenge")
        c2 = self.r.merge("basic")
        self.r.git("switch", "-q", "leobwang-test")
        self.r.merge("challenge")
        self.assertEqual(shipped(self.tmp), c2)
        self.rm("ex/f.dfy")
        self.assertEqual(gone(self.tmp), ["ex/f.dfy"])

    def test_origin_challenge_newer_than_local_basic(self):
        self.basic("a.dfy")
        c = self.challenge("c.dfy")
        self.r.git("update-ref", "refs/remotes/origin/challenge", c)
        self.r.git("switch", "-q", "basic")
        self.r.git("branch", "-q", "-D", "challenge")
        self.study("origin/challenge")
        self.assertEqual(shipped(self.tmp), c)
        self.rm("ex/c.dfy")
        self.assertEqual(gone(self.tmp), ["ex/c.dfy"])

    # --- a study branch that contains basic but not challenge -----------------------
    def test_challenge_not_contained_is_ignored(self):
        b = self.basic("a.dfy", "b.dfy")
        self.challenge("c.dfy")
        self.study("basic")
        self.r.write("ex/a.dfy", "mine\n")
        self.r.commit("work")
        self.assertEqual(shipped(self.tmp), b)
        self.assertEqual(gone(self.tmp), [])                 # ex/c.dfy is not shipped here
        self.rm("ex/b.dfy")
        self.assertEqual(gone(self.tmp), ["ex/b.dfy"])

    def test_challenge_branched_after_a_basic_fix_is_ignored(self):
        """challenge branched from a later basic than the study branch holds:
        the study branch's merge base with challenge is older, so basic's wins."""
        b = self.basic("a.dfy")
        self.study("basic")
        self.r.git("switch", "-q", "basic")
        self.r.write("ex/f.dfy")
        self.r.commit("a fix on basic")
        self.challenge("c.dfy")
        self.r.git("switch", "-q", "leobwang-test")
        self.assertEqual(shipped(self.tmp), b)
        self.rm("ex/a.dfy")
        self.assertEqual(gone(self.tmp), ["ex/a.dfy"])

    # --- bases with no order in history ---------------------------------------------
    def test_unordered_bases_take_the_latest_commit(self):
        """HEAD merged challenge and a basic fix challenge has not taken yet
        (a moment the release plan rules out: fixes are merged forward at
        once): the later commit wins."""
        self.basic("a.dfy")
        self.challenge("c.dfy")
        self.study("challenge")
        self.r.git("switch", "-q", "basic")
        self.r.write("ex/f.dfy")
        fix = self.r.commit("a fix on basic, later than challenge")
        self.r.git("switch", "-q", "leobwang-test")
        self.r.merge("basic")
        self.assertEqual(shipped(self.tmp), fix)


# =====================================================================================
# End to end: firsttry.py --report --strict and pins.py on the armed course root
# =====================================================================================

SPEC = "specimens/Q04/P3d.dfy.specimen"       # a shipped specimen with an item and a slot
NEW = "specimens/Q04/Z9d.dfy.specimen"        # a neutral file the challenges add


class EndToEnd(unittest.TestCase):

    def setUp(self):
        self.root = C.build_root(overlay=True, git=False)
        self.r = Repo(self.root)
        self.r.git("init", "-q", "-b", "main")

    def tearDown(self):
        C.remove_root(self.root)

    def course_on(self, branch_from_design):
        """Commit the course root; with branch_from_design, main holds only a
        design commit and the course is committed on basic."""
        if branch_from_design:
            keep = Path(tempfile.mkdtemp(prefix="dvl-shipref-keep-", dir=C.TMP_BASE))
            names = [n for n in os.listdir(self.root) if n != ".git"]
            for n in names:
                shutil.move(str(self.root / n), keep / n)
            self.r.write("DESIGN.md")
            self.r.commit("design only")
            self.r.git("switch", "-q", "-c", "basic")
            os.remove(self.root / "DESIGN.md")
            for n in names:
                shutil.move(str(keep / n), self.root / n)
            shutil.rmtree(keep)
        return self.r.commit("the course")

    def report(self):
        return C.tool("firsttry.py", "Q04", "--report", "--strict", root=self.root)

    def assert_gone_detected(self, rel, item=None):
        rc, out, err = self.report()
        self.assertEqual(rc, 1, out + err)
        want = (f"{rel}:0: missing: {item}: its file is gone" if item else
                f"{rel}:0: missing: the file is gone (it shipped at the merge base with the "
                "course branch)")
        self.assertIn(want, out)
        self.assertNotIn("no `basic`, `challenge` or `main` branch", out)
        if item:
            rc, out, err = C.tool("pins.py", "Q04", root=self.root)
            self.assertIn(f"· {item}  its file {rel} is gone since it shipped", out)

    def test_only_main(self):
        self.course_on(branch_from_design=False)
        self.r.git("switch", "-q", "-c", "leobwang-test")
        os.remove(self.root / SPEC)
        self.assert_gone_detected(SPEC, "Q04.P3d")

    def test_basic_only(self):
        self.course_on(branch_from_design=True)
        self.r.git("switch", "-q", "-c", "leobwang-test", "basic")
        os.remove(self.root / SPEC)
        self.assert_gone_detected(SPEC, "Q04.P3d")

    def test_challenge_merged(self):
        self.course_on(branch_from_design=True)
        self.r.git("switch", "-q", "-c", "leobwang-test", "basic")
        self.r.git("switch", "-q", "-c", "challenge", "basic")
        self.r.write(NEW, NEUTRAL)
        self.r.commit("challenge")
        self.r.git("switch", "-q", "leobwang-test")
        self.r.merge("challenge")
        rc, out, err = self.report()
        self.assertNotIn("is gone", out)
        os.remove(self.root / NEW)
        self.assert_gone_detected(NEW)                       # challenge's new file counts
        self.r.write(NEW, NEUTRAL)
        os.remove(self.root / SPEC)
        self.assert_gone_detected(SPEC, "Q04.P3d")

    def test_challenge_not_contained_is_ignored(self):
        self.course_on(branch_from_design=True)
        self.r.git("switch", "-q", "-c", "challenge", "basic")
        self.r.write(NEW, NEUTRAL)
        self.r.commit("challenge")
        self.r.git("switch", "-q", "-c", "leobwang-test", "basic")
        self.assertFalse((self.root / NEW).exists())
        rc, out, err = self.report()
        self.assertNotIn("is gone", out)                     # challenge's file is not shipped here
        os.remove(self.root / SPEC)
        self.assert_gone_detected(SPEC, "Q04.P3d")
        self.assertNotIn(NEW, self.report()[1])

    def test_no_branch_note(self):
        self.course_on(branch_from_design=False)
        self.r.git("switch", "-q", "-c", "leobwang-test")
        self.r.git("branch", "-q", "-D", "main")
        rc, out, err = self.report()
        self.assertIn("note: no `basic`, `challenge` or `main` branch to compare with", out)


if __name__ == "__main__":
    unittest.main()
