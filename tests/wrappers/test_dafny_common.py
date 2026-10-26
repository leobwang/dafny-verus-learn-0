"""Tests for dvl.common: the job runner, the toolchain paths and the pins
loader. The runner tests run tiny shell and Python jobs (no solver) as plain
processes (DELTAS Δ503, D78: the course applies no memory management).

Run: python3 -m unittest discover -s tests/wrappers -p 'test_dafny*.py'
"""

import os
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("DVL_SCRATCH", f"/tmp/dvl-test-{os.getuid()}")

from dvl import common  # noqa: E402


class RunCapped(unittest.TestCase):
    def test_exit_code_and_raw_files(self):
        rc, so, se = common.run_capped(["bash", "-c", "echo out; echo err >&2; exit 3"], 1, 60)
        self.assertEqual(rc, 3)
        self.assertEqual(so.read_text(), "out\n")
        self.assertEqual(se.read_text(), "err\n")
        self.assertEqual((so.parent / "exit.txt").read_text(), "3\n")
        self.assertEqual((so.parent / "cmd.txt").read_text(),
                         "bash -c 'echo out; echo err >&2; exit 3'\n")

    def test_a_sigkill_death_is_137_killed_memory(self):
        """The host's OOM killer (or any SIGKILL) is killed(memory), never a verdict."""
        rc, _, _ = common.run_capped(["bash", "-c", "kill -KILL $$"], 1, 60)
        self.assertEqual(rc, 137)
        self.assertTrue(common.is_killed(rc))

    def test_signal_deaths_map_to_killed(self):
        self.assertEqual(common.run_capped(["bash", "-c", "kill -TERM $$"], 1, 60)[0], 143)
        self.assertTrue(common.is_killed(143))
        self.assertFalse(common.is_killed(common.WALL_CLOCK_EXIT))

    def test_wall_clock_kill_is_124_and_kills_the_tree(self):
        marker = f"dvl-clock-test-{os.getpid()}"
        rc, _, _ = common.run_capped(
            ["bash", "-c", f"sleep 300 & exec -a {marker} sleep 300"], 1, 2)
        self.assertEqual(rc, common.WALL_CLOCK_EXIT)
        self.assertEqual(common.TIMEOUT_EXIT, 124)
        left = subprocess.run(["pgrep", "-f", marker], capture_output=True, text=True)
        self.assertEqual(left.stdout.strip(), "")

    @staticmethod
    def _alive(pattern):
        """PIDs whose command line matches `pattern` (pgrep -f)."""
        return subprocess.run(["pgrep", "-f", pattern], capture_output=True,
                              text=True).stdout.split()

    def _orphan_parent(self, marker, timeout_s):
        """A Python parent running one capped job: a driver (`<marker>-main`)
        that started a child of its own (`<marker>-solver`, standing in for a
        solver its driver spawned), both `sleep 300`. Returns the parent once
        both run."""
        job = (f"(exec -a {marker}-solver sleep 300) & exec -a {marker}-main sleep 300")
        # SIGINT at Python's default in the parent, whatever the test runner
        # inherited: a runner started from a background shell has SIGINT
        # ignored, and Python then installs no handler (DV3b integration)
        code = ("import signal; signal.signal(signal.SIGINT, signal.default_int_handler)\n"
                "import sys; sys.path.insert(0, %r)\nfrom dvl import common\n"
                "common.run_capped(['bash', '-c', %r], 0.1, %r)\n"
                % (str(ROOT / "scripts"), job, timeout_s))
        parent = subprocess.Popen([sys.executable, "-B", "-c", code], env=dict(os.environ),
                                  stderr=subprocess.DEVNULL)   # a killed parent's traceback
        t0 = time.monotonic()
        while not (self._alive(f"^{marker}-main") and self._alive(f"^{marker}-solver")):
            if time.monotonic() - t0 > 30:
                parent.kill()
                self.fail("the capped job never started")
            time.sleep(0.05)
        return parent

    def test_parent_death_kills_the_whole_job_at_once(self):
        """No orphan: the parent is SIGKILLed while its job (a driver and the
        solver it started) runs with a 600 s limit; the lifeline watcher kills
        the job's process group within seconds, then exits."""
        marker = f"dvl-lifeline-test-{os.getpid()}"
        parent = self._orphan_parent(marker, 600)
        try:
            killed = time.monotonic()
            parent.kill()
            parent.wait()
            while self._alive(f"^{marker}-"):
                self.assertLess(time.monotonic() - killed, 10, "a solver outlived its dead "
                                "parent")
                time.sleep(0.05)
        finally:
            parent.kill()
            subprocess.run(["pkill", "-f", f"^{marker}-"], capture_output=True)

    def test_ctrl_c_stops_the_scope(self):
        """SIGINT to the parent (Ctrl-C; the job is in its own session, so the
        signal reaches only the parent): the scope is stopped as well."""
        marker = f"dvl-sigint-test-{os.getpid()}"
        parent = self._orphan_parent(marker, 600)
        try:
            sent = time.monotonic()
            parent.send_signal(2)
            parent.wait(timeout=30)
            while self._alive(f"^{marker}-"):
                self.assertLess(time.monotonic() - sent, 10, "the job outlived Ctrl-C")
                time.sleep(0.05)
        finally:
            parent.kill()
            subprocess.run(["pkill", "-f", f"^{marker}-"], capture_output=True)

    def test_stragglers_are_stopped_after_a_normal_return(self):
        """A job that exits leaving a process behind in its scope (a solver
        whose driver returned): the process is stopped once run_capped
        returns, not left running."""
        marker = f"dvl-straggler-test-{os.getpid()}"
        rc, so, _ = common.run_capped(
            ["bash", "-c", f"(exec -a {marker} sleep 300) & sleep 0.3; echo $!; exit 0"], 1, 600)
        self.assertEqual(rc, 0)
        pid = int(so.read_text().split()[0])
        t0 = time.monotonic()
        while Path(f"/proc/{pid}").exists() and self._alive(f"^{marker}"):
            self.assertLess(time.monotonic() - t0, 10, "the straggler outlived its job")
            time.sleep(0.05)

    def test_no_lifeline_no_run(self):
        """A watcher that cannot start refuses the job (it could outlive us)."""
        code = ("import sys; sys.path.insert(0, %r)\nfrom dvl import common\n"
                "import subprocess\nreal = subprocess.run\n"
                "def fake(argv, *a, **k):\n"
                "    if argv[:1] == ['setsid']:\n"
                "        raise FileNotFoundError('setsid')\n"
                "    return real(argv, *a, **k)\n"
                "subprocess.run = fake\n"
                "try:\n    common.run_capped(['true'], 1, 10)\nexcept common.DvlError as e:\n"
                "    print('refused')\n" % str(ROOT / "scripts"))
        p = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True,
                           env=dict(os.environ))
        self.assertEqual(p.stdout.strip(), "refused", p.stderr)

    def test_a_job_killed_at_the_limit_is_the_wall_clock_net(self):
        """A job SIGTERMed at or after its limit is 124, never killed(memory)."""
        rc, _, _ = common.run_capped(["bash", "-c", "trap '' TERM; sleep 30"], 1, 2)
        self.assertEqual(rc, common.WALL_CLOCK_EXIT)

    def test_environment_is_scrubbed(self):
        os.environ["DVL_LEAK_PROBE"] = "1"
        try:
            rc, so, _ = common.run_capped(["bash", "-c", "env"], 1, 60)
            names = {line.split("=", 1)[0] for line in so.read_text().splitlines()}
            self.assertEqual(rc, 0)
            self.assertNotIn("DVL_LEAK_PROBE", names)
            self.assertEqual(names - {"PWD", "SHLVL", "_"}, {"PATH", "LANG", "LC_ALL", "HOME"})
            rc, so, _ = common.run_capped(["bash", "-c", "echo $ONLY"], 1, 60,
                                          env={"PATH": "/usr/bin:/bin", "ONLY": "x"})
            self.assertEqual(so.read_text(), "x\n")
        finally:
            del os.environ["DVL_LEAK_PROBE"]

    def _overlap(self, jobs):
        os.environ["DVL_DVLTEST_JOBS"] = str(jobs)
        stamps = []

        def one():
            rc, so, _ = common.run_capped(
                ["bash", "-c", "date +%s.%N; sleep 1.5; date +%s.%N"], 1, 60, pool="dvltest")
            a, b = so.read_text().split()
            stamps.append((float(a), float(b)))

        try:
            ts = [threading.Thread(target=one) for _ in range(2)]
            for t in ts:
                t.start()
            for t in ts:
                t.join()
        finally:
            del os.environ["DVL_DVLTEST_JOBS"]
        (a0, a1), (b0, b1) = sorted(stamps)
        return b0 < a1

    def test_concurrency_slots(self):
        self.assertFalse(self._overlap(1))
        self.assertTrue(self._overlap(2))

    def test_no_memory_cap_on_the_host(self):
        """D78: a job that allocates past any former cap runs to its own end."""
        rc, _, _ = common.run_capped(
            [sys.executable, "-c", "x = bytearray(300 * 1024 * 1024)"], 0.1, 60)
        self.assertEqual(rc, 0)


class Toolchain(unittest.TestCase):
    def test_paths(self):
        tc = common.toolchain("dafny", fresh=True)
        self.assertEqual(sorted(tc), ["dafny", "dafny_root", "dafny_z3"])
        self.assertEqual(tc["dafny_z3"].name, "z3-4.12.1")
        self.assertEqual(tc["dafny_root"].name, "dafny-4.11.0")
        self.assertTrue(all(p.exists() for p in tc.values()))
        both = common.toolchain()
        self.assertEqual({"dafny", "verus", "cargo_verus", "verus_z3"} - set(both), set())
        with self.assertRaises(ValueError):
            common.toolchain("lean")

    def test_dafny_and_verus_come_from_path(self):
        """D78: the tools are the ones on PATH (resolved), not .toolchain lookups."""
        import shutil
        tc = common.toolchain(fresh=True)
        for t in ("dafny", "verus"):
            w = Path(shutil.which(t)).absolute()
            self.assertEqual(tc[t], w.resolve() if w.is_symlink() else w)
        self.assertEqual(tc["verus_z3"], tc["verus"].parent / "z3")

    def test_a_tool_missing_from_path_is_refused(self):
        code = ("import sys; sys.path.insert(0, %r)\nfrom dvl import common\n"
                "try:\n    common.toolchain('dafny')\nexcept common.ToolchainError as e:\n"
                "    print('refused', 'PATH' in str(e))\n" % str(ROOT / "scripts"))
        env = {k: v for k, v in os.environ.items() if k != "DVL_TOOLCHAIN_DIR"}
        env["PATH"] = "/usr/bin:/bin"
        p = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True,
                           env=env)
        self.assertEqual(p.stdout.strip(), "refused True", p.stderr)

    def test_a_missing_install_is_refused(self):
        code = ("import sys; sys.path.insert(0, %r)\nfrom dvl import common\n"
                "try:\n    common.toolchain('dafny')\nexcept common.ToolchainError:\n"
                "    print('refused')\n" % str(ROOT / "scripts"))
        empty = common.scratch_dir("no-toolchain")
        p = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True,
                           env={**os.environ, "DVL_TOOLCHAIN_DIR": str(empty)})
        self.assertEqual(p.stdout.strip(), "refused", p.stderr)


if __name__ == "__main__":
    unittest.main()
