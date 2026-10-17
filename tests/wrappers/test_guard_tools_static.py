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


if __name__ == "__main__":
    unittest.main()
