"""Tool-free regression checks for DV6's newly exposed tool routes.

Only invented files in temporary directories are used. No MCP server, model,
verifier or reference file is opened. The generated hook fixtures additionally
exercise these routes in study, jq-free and authoring modes.
"""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "guard_doors", ROOT / "tests/acceptance/guard_doors.py")
doors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doors)


class NewToolRoutes(unittest.TestCase):
    def test_acceptance_inventory_covers_new_tools(self):
        self.assertEqual(doors.uncovered_tools(
            ["mcp__firecrawl__firecrawl_parse", "Workflow", "ScheduleWakeup"],
            ROOT / ".claude/settings.json"), [])

    def test_unknown_tool_still_fails_inventory(self):
        self.assertEqual(doors.uncovered_tools(
            ["Read", "FutureLocalFileReader", "FutureLocalFileReader"],
            ROOT / ".claude/settings.json"), ["FutureLocalFileReader"])

    def test_parser_resolves_relative_path_from_cwd(self):
        # Same innocent path at the project root and in a subdirectory; only
        # the latter is a symlink to a decoy reference. MCP verifier targets
        # use ROOT, but a local-file parser must use the caller's cwd.
        with tempfile.TemporaryDirectory(prefix="dvl-guard-tool-") as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "Solutions").mkdir()
            (root / "Solutions/decoy.txt").write_text("invented canary\n")
            (root / "notes.txt").write_text("ordinary notes\n")
            (root / "docs/notes.txt").symlink_to("../Solutions/decoy.txt")
            env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root))
            for no_jq in ("", "1"):
                env["SPOILER_GUARD_NO_JQ"] = no_jq
                for cwd, expected in ((root, 0), (root / "docs", 2)):
                    with self.subTest(no_jq=no_jq, cwd=cwd.name):
                        result = subprocess.run(
                            ["bash", str(ROOT / ".claude/hooks/spoiler-guard.sh")],
                            input=json.dumps({
                                "tool_name": "mcp__firecrawl__firecrawl_parse",
                                "tool_input": {"filePath": "notes.txt"},
                                "cwd": str(cwd),
                            }), text=True, capture_output=True, env=env, check=False)
                        self.assertEqual(result.returncode, expected, result.stderr)
                        if expected:
                            self.assertIn("(rule 1)", result.stderr)



class CloneHead(unittest.TestCase):
    """guard_doors.clone_head, which the three author harnesses (guard_doors, skill_sims,
    calibrate) use for their study clone: a worktree on a branch is cloned on that branch;
    one with a detached HEAD (a validation worktree pinned to a commit) is cloned at that
    commit on a new local branch study-<sha12>, where `symbolic-ref --short HEAD` would
    fail (exit 128)."""

    def test_branch_and_detached_heads(self):
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid",
                   GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")

        def git(cwd, *args):
            return subprocess.run(["git", "-C", str(cwd), *args], env=env, check=True,
                                  capture_output=True, text=True).stdout.strip()

        with tempfile.TemporaryDirectory(prefix="dvl-clone-head-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            git(repo, "init", "-q", "-b", "basic")
            for n in ("one", "two"):
                (repo / "f.txt").write_text(n + "\n")
                git(repo, "add", "f.txt")
                git(repo, "commit", "-qm", n)
            first = git(repo, "rev-parse", "HEAD~1")
            rc, branch = doors.clone_head(repo, Path(tmp) / "on-branch")
            self.assertEqual((rc, branch), (0, "basic"))
            git(repo, "switch", "-q", "--detach", first)
            rc, branch = doors.clone_head(repo, Path(tmp) / "detached")
            self.assertEqual((rc, branch), (0, f"study-{first[:12]}"))
            clone = Path(tmp) / "detached"
            self.assertEqual(git(clone, "rev-parse", "HEAD"), first)
            self.assertEqual(git(clone, "symbolic-ref", "--short", "HEAD"), branch)
            self.assertEqual((clone / "f.txt").read_text(), "one\n")



class RemoveStudyRoot(unittest.TestCase):
    """guard_doors.remove_study_root (the three harnesses' cleanup) deletes the study root,
    then a session's stray files in its parents up to the top study directory, each
    recorded as a leftover, and the parents once empty; another run's study root under
    the same top directory stays. Exercised under a temporary base, not /tmp."""

    def test_leftover_files_are_removed_and_recorded(self):
        with tempfile.TemporaryDirectory(prefix="dvl-study-root-") as tmp:
            base = Path(tmp)
            top = base / "dvl0-study-dvtest-lane"
            root = top / "q16-q18"
            (root / "clone").mkdir(parents=True)
            (root / "clone" / "f").write_text("x\n")
            (top / "ccm.out").write_text("a session's stray output\n")
            gone = doors.remove_study_root(root, base=base)
            self.assertFalse(top.exists())
            self.assertIn(f"leftover {top / 'ccm.out'}", gone)
            self.assertEqual(gone[0], str(root))
            self.assertEqual(gone[-1], str(top))
            # another run's study root under the same top directory is kept
            (top / "q13-q15").mkdir(parents=True)
            (top / "q16-q18").mkdir()
            (top / "stray.log").write_text("x\n")
            gone = doors.remove_study_root(top / "q16-q18", base=base)
            self.assertTrue((top / "q13-q15").is_dir())
            self.assertFalse((top / "stray.log").exists())
            self.assertNotIn(str(top), gone)
            for bad in (base / "dvl0-dv5e-x", Path("/home")):
                with self.assertRaises(ValueError):
                    doors.remove_study_root(bad, base=base)


if __name__ == "__main__":
    unittest.main()
