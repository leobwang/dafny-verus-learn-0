"""D42 and D46: scripts/check_release_history.py on throwaway git repositories.

main..basic must be a linear chain of single-parent commits whose first parent is main and
whose subjects start with "basic: ", and no archived commit (reachable from an archive/*
tag, neither on main nor under a basic-* release tag) may be reachable from basic."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("release_history", ROOT / "scripts/check_release_history.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

ENV = dict(os.environ, GIT_AUTHOR_NAME="test", GIT_AUTHOR_EMAIL="test@example.invalid",
           GIT_COMMITTER_NAME="test", GIT_COMMITTER_EMAIL="test@example.invalid",
           GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


class ReleaseHistory(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(prefix="dvl-release-history-")
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.git("init", "-q", "-b", "main")
        self.commit("design", "invented design", name="design.txt")
        self.main = self.git("rev-parse", "HEAD")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], env=ENV, check=True,
                              text=True, capture_output=True).stdout.strip()

    def commit(self, subject, content, name="course.txt"):
        (self.root / name).write_text(content + "\n")
        self.git("add", ".")
        self.git("commit", "-qm", subject)
        return self.git("rev-parse", "HEAD")

    def squash_on_main(self, subject="basic: release the frozen course"):
        """The D42 release: the authoring tree as one commit whose sole parent is main."""
        self.git("checkout", "-qb", "authoring", self.main)
        for value in ("first draft", "reviewed draft"):
            self.commit(f"authoring: {value}", value)
        sha = self.git("commit-tree", "HEAD^{tree}", "-p", self.main, "-m", subject)
        self.git("branch", "basic", sha)
        self.git("checkout", "-q", "basic")
        return sha

    def problems(self, candidate="basic"):
        return release.problems(self.root, candidate)

    def test_the_d42_squash_passes_and_authoring_ancestry_fails(self):
        self.squash_on_main()
        self.assertEqual(self.problems(), [])
        got = self.problems("authoring")
        self.assertTrue(any("subject" in p for p in got), got)
        self.assertTrue(self.problems("missing-release"))
        self.assertIn("adds no commit", self.problems("main")[0])

    def test_a_linear_chain_of_basic_fixes_passes(self):
        self.squash_on_main()
        self.commit("basic: fix one", "fix one")
        self.commit("basic: fix two", "fix two")
        self.assertEqual(self.problems(), [])

    def test_a_fix_without_the_prefix_fails(self):
        self.squash_on_main()
        bad = self.commit("fix the rubric", "fix")
        got = self.problems()
        self.assertEqual(len(got), 1, got)
        self.assertIn(bad[:12], got[0])
        self.assertIn("does not start with 'basic:'", got[0])

    def test_a_merge_commit_fails(self):
        self.squash_on_main()
        self.git("checkout", "-qb", "side")
        self.commit("basic: side fix", "side", name="side.txt")
        self.git("checkout", "-q", "basic")
        self.commit("basic: main-line fix", "line")
        self.git("merge", "-q", "--no-ff", "-m", "basic: merge the side fix", "side")
        got = self.problems()
        self.assertTrue(any("2 parents" in p for p in got), got)

    def test_a_chain_that_does_not_start_on_mains_tip_fails(self):
        self.git("checkout", "-qb", "basic")
        self.commit("basic: release", "release")
        self.commit("basic: fix", "fix")
        self.assertEqual(self.problems(), [])
        # main moves on: basic's first commit no longer sits on main
        self.git("checkout", "-q", "main")
        self.commit("a newer design", "newer design", name="design.txt")
        got = self.problems()
        self.assertTrue(any("is not main" in p for p in got), got)

    def test_archived_history_is_refused_and_released_commits_are_not(self):
        first = self.squash_on_main()
        # an authoring line on the released basic, shipped, rolled back and archived (D46)
        self.git("checkout", "-qb", "r-work")
        self.commit("authoring: build R01", "r01")
        shipped = self.commit("basic: ship R01", "r01 shipped")
        self.git("tag", "archive/basic-with-r01", shipped)
        self.git("checkout", "-q", "basic")
        # without a release tag the shared release squash itself counts as archived
        got = self.problems()
        self.assertTrue(any(first[:12] in p and "archived" in p for p in got), got)
        self.git("tag", "basic-q-initial", first)
        self.assertEqual(self.problems(), [])
        self.commit("basic: a fix after the rollback", "fix")
        self.assertEqual(self.problems(), [])
        # a candidate that takes the archived line back is refused on both counts
        got = self.problems("archive/basic-with-r01")
        self.assertTrue(any("archived history" in p and shipped[:12] in p for p in got), got)
        self.assertTrue(any("authoring: build R01" in p for p in got), got)

    def test_an_archived_basic_shaped_commit_is_refused(self):
        first = self.squash_on_main()
        self.git("tag", "basic-q-initial", first)
        rolled_back = self.commit("basic: a fix that was rolled back", "rolled back")
        self.git("tag", "archive/rolled-back", rolled_back)
        got = self.problems()
        self.assertEqual(len(got), 1, got)
        self.assertIn(rolled_back[:12], got[0])
        self.git("reset", "-q", "--hard", first)
        self.assertEqual(self.problems(), [])

    def test_the_command_line(self):
        self.squash_on_main()
        argv = ["python3", "-B", str(ROOT / "scripts/check_release_history.py"),
                "--root", str(self.root)]
        p = subprocess.run(argv, env=ENV, capture_output=True, text=True)
        self.assertEqual((p.returncode, p.stdout.split(" (")[0]), (0, "release history: OK"),
                         (p.stdout, p.stderr))
        self.commit("not prefixed", "x")
        p = subprocess.run(argv + ["basic"], env=ENV, capture_output=True, text=True)
        self.assertEqual(p.returncode, 1, (p.stdout, p.stderr))


if __name__ == "__main__":
    unittest.main()
