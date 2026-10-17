"""Tests for dvl.common: the memory-capped runner, the toolchain paths and the
pins loader. The runner tests run tiny shell and Python jobs (no solver)
under real `systemd-run --user --scope` caps.

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

    def test_memory_kill_is_137(self):
        rc, _, _ = common.run_capped(
            [sys.executable, "-c", "x = bytearray(400 * 1024 * 1024)"], 0.1, 60)
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

    def _orphan_parent(self, marker, timeout_s, grace_s):
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
                "common.run_capped(['bash', '-c', %r], 0.1, %r, grace_s=%r)\n"
                % (str(ROOT / "scripts"), job, timeout_s, grace_s))
        parent = subprocess.Popen([sys.executable, "-B", "-c", code], env=dict(os.environ),
                                  stderr=subprocess.DEVNULL)   # a killed parent's traceback
        t0 = time.monotonic()
        while not (self._alive(f"^{marker}-main") and self._alive(f"^{marker}-solver")):
            if time.monotonic() - t0 > 30:
                parent.kill()
                self.fail("the capped job never started")
            time.sleep(0.05)
        return parent

    def _units_of(self, pid):
        return subprocess.run(["systemctl", "--user", "list-units", "--all", "--no-legend",
                               f"dvl-bash-{pid}-*"], capture_output=True, text=True).stdout.strip()

    def test_parent_death_stops_the_whole_scope_at_once(self):
        """No orphan: the parent is SIGKILLed while its job (a driver and the
        solver it started) runs with a 600 s limit and a 600 s systemd net;
        the lifeline watcher stops the whole scope within seconds."""
        marker = f"dvl-lifeline-test-{os.getpid()}"
        parent = self._orphan_parent(marker, 600, 600)
        try:
            self.assertTrue(self._units_of(parent.pid), "no scope for the job")
            killed = time.monotonic()
            parent.kill()
            parent.wait()
            while self._alive(f"^{marker}-"):
                self.assertLess(time.monotonic() - killed, 10, "a solver outlived its dead "
                                "parent: the scope was not stopped")
                time.sleep(0.05)
            t0 = time.monotonic()
            while self._units_of(parent.pid):
                self.assertLess(time.monotonic() - t0, 10, "the scope is still loaded")
                time.sleep(0.1)
            t0 = time.monotonic()
            while self._alive(f"dvl-lifeline-dvl-bash-{parent.pid}-"):
                self.assertLess(time.monotonic() - t0, 15, "the watcher never exited")
                time.sleep(0.1)
        finally:
            parent.kill()
            subprocess.run(["pkill", "-f", f"^{marker}-"], capture_output=True)

    def test_ctrl_c_stops_the_scope(self):
        """SIGINT to the parent (Ctrl-C; the job is in its own session, so the
        signal reaches only the parent): the scope is stopped as well."""
        marker = f"dvl-sigint-test-{os.getpid()}"
        parent = self._orphan_parent(marker, 600, 600)
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
        returns, not left to run to the systemd net."""
        marker = f"dvl-straggler-test-{os.getpid()}"
        rc, so, _ = common.run_capped(
            ["bash", "-c", f"(exec -a {marker} sleep 300) & sleep 0.3; echo $!; exit 0"], 1, 600)
        self.assertEqual(rc, 0)
        pid = int(so.read_text().split()[0])
        t0 = time.monotonic()
        while Path(f"/proc/{pid}").exists() and self._alive(f"^{marker}"):
            self.assertLess(time.monotonic() - t0, 10, "the straggler outlived its job")
            time.sleep(0.05)

    def test_systemd_enforces_the_wall_clock_net_when_the_watcher_dies_too(self):
        """Δ58: RuntimeMaxSec = timeout_s + grace_s on the scope, so a job whose
        parent AND lifeline watcher were both SIGKILLed (a kill of the whole
        process tree) is still stopped (here 2 + 2 s)."""
        marker = f"dvl-orphan-test-{os.getpid()}"
        parent = self._orphan_parent(marker, 2, 2)
        try:
            watcher = self._alive(f"dvl-lifeline-dvl-bash-{parent.pid}-")
            self.assertEqual(len(watcher), 1, watcher)
            started = time.monotonic()
            os.kill(int(watcher[0]), 9)
            parent.kill()
            parent.wait()
            time.sleep(0.5)
            self.assertTrue(self._alive(f"^{marker}-main"),
                            "the job died with its parent: the test proves nothing")
            while self._alive(f"^{marker}-"):
                self.assertLess(time.monotonic() - started, 15, "the orphaned job outlived "
                                "timeout_s + grace_s: no systemd net")
                time.sleep(0.2)
        finally:
            parent.kill()
            subprocess.run(["pkill", "-f", f"^{marker}-"], capture_output=True)

    def test_no_lifeline_no_run(self):
        """A watcher that cannot start refuses the job (it could outlive us)."""
        code = ("import sys; sys.path.insert(0, %r)\nfrom dvl import common\n"
                "common._cap_works()\n"
                "import subprocess\nreal = subprocess.run\n"
                "def fake(argv, *a, **k):\n"
                "    if argv[:1] == ['setsid']:\n"
                "        raise FileNotFoundError('setsid')\n"
                "    return real(argv, *a, **k)\n"
                "subprocess.run = fake\n"
                "try:\n    common.run_capped(['true'], 1, 10)\nexcept common.CapError as e:\n"
                "    print('refused')\n" % str(ROOT / "scripts"))
        p = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True,
                           env=dict(os.environ))
        self.assertEqual(p.stdout.strip(), "refused", p.stderr)

    def test_a_systemd_stop_at_the_limit_is_the_wall_clock_net(self):
        """With no grace, systemd's SIGTERM can beat the parent's kill: still 124,
        never killed(memory)."""
        rc, _, _ = common.run_capped(["bash", "-c", "sleep 30"], 1, 2, grace_s=0)
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

    def test_no_cap_no_run(self):
        code = ("import sys; sys.path.insert(0, %r)\nfrom dvl import common\n"
                "try:\n    common.run_capped(['true'], 1, 10)\nexcept common.CapError:\n"
                "    print('refused')\n" % str(ROOT / "scripts"))
        p = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True,
                           env={"PATH": "/nonexistent", "HOME": os.environ.get("HOME", "/tmp"),
                                "DVL_SCRATCH": os.environ["DVL_SCRATCH"]})
        self.assertEqual(p.stdout.strip(), "refused", p.stderr)


class SolverSlice(unittest.TestCase):
    """Every capped job's scope lies in the user slice dvl0.slice, whose own MemoryMax=48G
    bounds all solver jobs together (CLAUDE.md §Resources), while each job keeps its cap."""

    SHIM = r"""#!/bin/sh
printf '%s' "$(basename "$0")" >> "$SHIM_LOG"
for a in "$@"; do printf ' %s' "$a" >> "$SHIM_LOG"; done
printf '\n' >> "$SHIM_LOG"
case "$(basename "$0")" in
  systemctl)
    case " $* " in
      *" set-property "*) exit "${SHIM_SET_EXIT:-0}" ;;
      *" show "*) printf 'MemoryMax=%s\nMemorySwapMax=0\n' "${SHIM_SHOW_MAX:-51539607552}"; exit 0 ;;
      *) exit 0 ;;
    esac ;;
  systemd-run)
    while [ "$#" -gt 0 ] && [ "$1" != "--" ]; do shift; done
    shift
    exec "$@" ;;
esac
"""

    def _shimmed(self, code, **env):
        """Run `code` (after `from dvl import common`) with fake systemctl and systemd-run
        first on PATH; returns (stdout, the shims' argv log lines)."""
        import tempfile
        with tempfile.TemporaryDirectory(prefix="dvl-slice-shim-") as t:
            shim = Path(t) / "bin"
            shim.mkdir()
            for name in ("systemctl", "systemd-run"):
                (shim / name).write_text(self.SHIM)
                (shim / name).chmod(0o755)
            log = Path(t) / "argv.log"
            log.write_text("")
            full = ("import sys; sys.path.insert(0, %r)\nfrom dvl import common\n"
                    % str(ROOT / "scripts")) + code
            e = dict(os.environ, PATH=f"{shim}:{os.environ['PATH']}", SHIM_LOG=str(log),
                     DVL_SCRATCH=os.environ["DVL_SCRATCH"], **env)
            p = subprocess.run([sys.executable, "-B", "-c", full], capture_output=True,
                               text=True, env=e, timeout=120)
            time.sleep(0.3)          # the detached lifeline watcher's last systemctl call
            return p.stdout.strip(), [x for x in log.read_text().splitlines() if x], p.stderr

    def test_the_job_argv_names_the_slice_and_keeps_its_own_cap(self):
        argv = common.cap_argv(8, "dvl-test-unit", {"PATH": "/usr/bin"})
        self.assertIn("--slice=dvl0.slice", argv)
        self.assertEqual(argv[argv.index("MemoryMax=8G") - 1], "-p")
        self.assertIn("MemorySwapMax=0", argv)
        self.assertLess(argv.index("--slice=dvl0.slice"), argv.index("--"))
        self.assertEqual((common.SOLVER_SLICE, common.SOLVER_BUDGET_GB), ("dvl0.slice", 48))

    def test_the_slice_is_bounded_once_before_the_first_job(self):
        out, log, err = self._shimmed(
            "for _ in range(2):\n    print(common.run_capped(['true'], 1, 30)[0])\n")
        self.assertEqual(out.split(), ["0", "0"], err)
        sets = [x for x in log if " set-property " in x]
        self.assertEqual(sets, ["systemctl --user set-property --runtime dvl0.slice "
                                "MemoryMax=48G MemorySwapMax=0"])
        self.assertLess(log.index(sets[0]), min(i for i, x in enumerate(log)
                                                if x.startswith("systemd-run")))
        runs = [x for x in log if x.startswith("systemd-run")]
        self.assertEqual(len(runs), 3, runs)            # the cap probe and the two jobs
        for x in runs:
            self.assertIn(" --slice=dvl0.slice ", x)
        for x in runs[1:]:
            self.assertIn(" -p MemoryMax=1G -p MemorySwapMax=0 ", x)

    def test_a_slice_that_cannot_be_bounded_refuses_the_job(self):
        code = ("try:\n    common.run_capped(['true'], 1, 30)\n"
                "except common.CapError as e:\n    print('refused:', e)\n")
        for env in ({"SHIM_SET_EXIT": "1"}, {"SHIM_SHOW_MAX": "infinity"},
                    {"SHIM_SHOW_MAX": str(64 * 1024 ** 3)}):
            with self.subTest(env=env):
                out, log, err = self._shimmed(code, **env)
                self.assertTrue(out.startswith("refused:"), (out, err))
                self.assertFalse([x for x in log if x.startswith("systemd-run")], log)

    def test_a_real_job_runs_in_the_bounded_slice(self):
        rc, so, _ = common.run_capped(["cat", "/proc/self/cgroup"], 1, 60)
        self.assertEqual(rc, 0)
        self.assertRegex(so.read_text(), r"/dvl0\.slice/dvl-cat-\d+-[0-9a-f]+\.scope$")
        show = subprocess.run(["systemctl", "--user", "show", "dvl0.slice", "-p", "MemoryMax",
                               "-p", "MemorySwapMax"], capture_output=True, text=True).stdout
        self.assertIn(f"MemoryMax={48 * 1024 ** 3}", show)
        self.assertIn("MemorySwapMax=0", show)


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
