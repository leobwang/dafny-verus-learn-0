"""scripts/ci.sh's DV4 additions (DV4-PLAN §8-§9): the static job's
single-route check (scripts/check_single_route.py) and the harness job's
sterile environment, tripwire shims and socket tripwire.

The planted calls below are regression fixtures: each is the plain operation
the check must catch, in a throwaway root, and none of them reaches anything
(the shims and the socket tripwire refuse before any command or connection
runs)."""

import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_common as C  # noqa: E402

CHECKER = C.ROOT / "scripts" / "check_single_route.py"


def plant(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class SingleRoute(unittest.TestCase):
    def setUp(self):
        self.root = C.tmpdir("ci-route-")
        self.addCleanup(shutil.rmtree, self.root, True)
        C.git("init", "-q", cwd=self.root)
        plant(self.root, "scripts/mksandbox-run", "#!/usr/bin/env python3\n# runs docker run for a sandbox\n")
        plant(self.root, ".claude/hooks/spoiler-guard.sh", "#!/bin/sh\n# refuses docker, sudo, opencode\n")
        plant(self.root, "docs/notes.md", "Prose may say docker and sudo; it is not code.\n")
        plant(self.root, "scripts/vcheck", "#!/usr/bin/env python3\nprint('a course tool')\n")

    def check(self):
        return subprocess.run([sys.executable, "-B", str(CHECKER), "--root", str(self.root)],
                              capture_output=True, text=True)

    def test_the_allowlist_passes(self):
        p = self.check()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("2 allowlisted, 0 outside the allowlist", p.stdout)

    def test_a_planted_container_call_in_a_new_script_fails(self):
        plant(self.root, "scripts/runner.sh", "#!/bin/sh\ndocker run --rm img true\n")
        p = self.check()
        self.assertEqual(p.returncode, 1)
        self.assertIn("scripts/runner.sh:2 names 'docker'", p.stderr)

    def test_a_planted_sudo_fails(self):
        plant(self.root, "scripts/helper.py", "import subprocess\nsubprocess.run(['sudo', 'true'])\n")
        p = self.check()
        self.assertEqual(p.returncode, 1)
        self.assertIn("scripts/helper.py:2 names 'sudo'", p.stderr)

    def test_a_mention_in_a_comment_of_a_file_outside_the_allowlist_fails(self):
        plant(self.root, "harness/q/fvh_q/notes.py", "# this module never calls opencode\nX = 1\n")
        p = self.check()
        self.assertEqual(p.returncode, 1)
        self.assertIn("harness/q/fvh_q/notes.py:1 names 'opencode'", p.stderr)

    def test_an_agent_cli_in_an_argv_list_and_a_container_socket_fail(self):
        plant(self.root, "tools/Q12/run.py", "import subprocess\nsubprocess.run(['claude', '-v'])\n")
        plant(self.root, "tools/Q12/sock.sh", "#!/bin/sh\ncurl --unix-socket /var/run/x.sock http://h/\n")
        p = self.check()
        self.assertEqual(p.returncode, 1)
        self.assertIn("tools/Q12/run.py", p.stderr)
        self.assertIn("tools/Q12/sock.sh", p.stderr)

    def test_the_static_job_runs_the_check(self):
        text = (C.ROOT / "scripts" / "ci.sh").read_text(encoding="utf-8")
        body = text.split("job_static() {", 1)[1].split("\n}\n", 1)[0]
        self.assertIn('check_single_route.py" --root "$ROOT"', body)
        self.assertIn("class_drift", body)
        self.assertIn("research/ledger-heads.jsonl", body)


class HarnessTripwire(unittest.TestCase):
    """The harness job's sterile environment on a throwaway root whose harness
    project plants one call per tripwire."""

    def setUp(self):
        self.base = C.tmpdir("ci-trip-")
        self.addCleanup(C.remove, self.base)
        self.root = C.course_root(self.base)
        h = self.root / "harness"
        (h / "tests" / "core").mkdir(parents=True)
        for f in ("pyproject.toml", "uv.lock"):
            shutil.copyfile(C.ROOT / "harness" / f, h / f)
        shutil.copyfile(C.ROOT / "harness" / "tests" / "conftest.py", h / "tests" / "conftest.py")
        shutil.copytree(C.ROOT / "harness" / "fvh", h / "fvh",
                        ignore=shutil.ignore_patterns("__pycache__"))
        for d in ("q", "r"):
            (h / d).mkdir()
        self.logs = self.base / "logs"

    def run_harness(self):
        return C.run_ci("--job", "harness", root=self.root, logs=self.logs, timeout=1800)

    def test_a_planted_cli_call_leaves_a_marker_and_fails_the_job(self):
        (self.root / "harness" / "tests" / "core" / "test_planted.py").write_text(
            "import subprocess\n\n\n"
            "def test_planted_cli_call():\n"
            "    # a regression fixture: the shim must catch this call\n"
            "    subprocess.run(['claude', '--version'], capture_output=True)\n",
            encoding="utf-8")
        rc, out, err = self.run_harness()
        self.assertEqual((rc, C.status_of(out, "harness")), (1, "FAIL"), (out, err))
        self.assertIn("tripwire", C.job_line(out, "harness"))
        self.assertIn("claude", C.job_line(out, "harness"))

    def test_a_planted_connection_fails_pytest_through_the_socket_tripwire(self):
        (self.root / "harness" / "tests" / "core" / "test_planted.py").write_text(
            "import socket\n\n\n"
            "def test_planted_connection():\n"
            "    # a regression fixture: the tripwire must refuse this connection\n"
            "    try:\n"
            "        socket.create_connection(('127.0.0.1', 11434), timeout=1)\n"
            "    except Exception:\n"
            "        pass\n",
            encoding="utf-8")
        rc, out, err = self.run_harness()
        self.assertEqual((rc, C.status_of(out, "harness")), (1, "FAIL"), (out, err))
        self.assertIn("pytest tests/core", C.job_line(out, "harness"))
        self.assertIn("network tripwire", (self.logs / "harness.log").read_text())

    def test_the_sterile_environment_holds_no_home_and_no_credentials(self):
        (self.root / "harness" / "tests" / "core" / "test_planted.py").write_text(
            "import os\nfrom pathlib import Path\n\n\n"
            "def test_sterile():\n"
            "    home = Path(os.environ['HOME'])\n"
            "    assert not (home / '.claude').exists() and not list(home.iterdir())\n"
            "    assert os.environ['FVH_NO_MODEL'] == '1' and os.environ['DVL_NO_DOCKER'] == '1'\n"
            "    assert os.environ['CLAUDE_CONFIG_DIR'] != str(Path.home() / '.claude')\n"
            "    assert 'CI' not in os.environ\n"
            "    assert not (home / '.local' / 'share' / 'claude').exists()\n",
            encoding="utf-8")
        rc, out, err = self.run_harness()
        self.assertEqual((rc, C.status_of(out, "harness")), (0, "PASS"), (out, err,
                                                                          (self.logs / "harness.log").read_text()[-3000:]))
        # a passing run keeps the scratch its log names (the sterile environment, the
        # project environment) and removes the rest (the tools' scratch root)
        work = self.root.resolve().parent / "ci-work"
        log = (self.logs / "harness.log").read_text()
        named = {m.rstrip(".") for m in re.findall(re.escape(str(work)) + r"/[^\s\"',:;=]+", log)}
        self.assertIn("sterile/home", " ".join(named))
        for n in named:
            self.assertTrue(Path(n).exists(), f"{n}: named by harness.log, removed after a pass")
        (run,) = work.iterdir()
        self.assertFalse((run / "scratch").exists())
        self.assertFalse((run / "tmp").exists())
        self.assertIn("ci.sh: tool scratch the logs name kept:", out)


if __name__ == "__main__":
    unittest.main()
