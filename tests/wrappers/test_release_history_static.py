"""D42: the first release carries the frozen tree without authoring ancestry."""
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


class ReleaseHistory(unittest.TestCase):
    def test_squash_passes_and_authoring_ancestry_fails(self):
        with tempfile.TemporaryDirectory(prefix="dvl-release-history-") as temp:
            root = Path(temp)
            env = dict(os.environ, GIT_AUTHOR_NAME="test", GIT_AUTHOR_EMAIL="test@example.invalid",
                       GIT_COMMITTER_NAME="test", GIT_COMMITTER_EMAIL="test@example.invalid")

            def git(*args):
                return subprocess.run(["git", "-C", str(root), *args], env=env, check=True,
                                      text=True, capture_output=True).stdout.strip()

            git("init", "-q", "-b", "main")
            (root / "design.txt").write_text("invented design\n")
            git("add", ".")
            git("commit", "-qm", "design")
            baseline = git("rev-parse", "HEAD")
            git("checkout", "-qb", "authoring")
            for value in ("first draft", "reviewed draft"):
                (root / "course.txt").write_text(value)
                git("add", ".")
                git("commit", "-qm", value)
            self.assertTrue(release.problems(root, "authoring"))
            candidate = git("commit-tree", "HEAD^{tree}", "-p", baseline, "-m", "frozen course")
            self.assertEqual(release.problems(root, candidate), [])
            self.assertTrue(release.problems(root, "missing-release"))
            self.assertTrue(release.problems(root, "main"))


if __name__ == "__main__":
    unittest.main()
