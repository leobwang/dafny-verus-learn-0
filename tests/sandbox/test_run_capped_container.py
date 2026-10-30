"""dvl.common.run_capped's two container modes against fake cgroup files
(DV4-PLAN §5.9, DV4 step 1c). No container, no solver: the jobs are tiny
shell commands, and the cgroup directory is a temporary one holding
memory.max and memory.events as a container's own cgroup would."""

import os
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sandbox_common as sc  # noqa: E402
from dvl import common  # noqa: E402

GIB = 1 << 30


class ContainerModes(unittest.TestCase):
    def setUp(self):
        self.cg = sc.tmpdir("dvl0-sandbox-cgroup-")
        self.scratch = sc.tmpdir("dvl0-sandbox-scratch-")
        self.addCleanup(sc.cleanup, self.cg, self.scratch)
        self.events(0)
        self.patches = [mock.patch.object(common, "CGROUP_DIR", self.cg),
                        mock.patch.dict(os.environ, {"DVL_SCRATCH": str(self.scratch)})]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def events(self, oom):
        (self.cg / "memory.events").write_text(f"low 0\nhigh 0\nmax 3\noom {oom}\noom_kill {oom}\n")

    def memmax(self, value):
        (self.cg / "memory.max").write_text(f"{value}\n")

    def run_job(self, mode, argv, mem_gb=8, timeout_s=30, pool="dafny"):
        # each job's output directory is the test's to remove (DV5d: it was never removed,
        # and every run of this suite left its job directories under /tmp)
        out = sc.tmpdir("dvl0-sandbox-job-")
        self.addCleanup(sc.cleanup, out)
        with mock.patch.dict(os.environ, {"DVL_CAP": mode}):
            return common.run_capped(argv, mem_gb, timeout_s, pool=pool, out_dir=out)

    def test_bounds_come_from_the_pins(self):
        self.assertEqual(common.container_bound_bytes("container-verify", 8), int(11.5 * GIB))
        self.assertEqual(common.container_bound_bytes("container-verify", 16), int(19.5 * GIB))
        self.assertEqual(common.container_bound_bytes("container-agent", 8), int(15.5 * GIB))
        self.assertEqual(common.container_bound_bytes("container-agent", 16), int(23.5 * GIB))
        with mock.patch.dict(os.environ, {"DVL_CONTAINER_MARGIN_GB": "100", "DVL_AGENT_ALLOWANCE_GB": "100"}):
            self.assertEqual(common.container_bound_bytes("container-agent", 8), int(15.5 * GIB))
        pins = common.load_pins()
        pins["container"]["agent_allowance_gb"] = 6
        with mock.patch.object(common, "load_pins", return_value=pins):
            self.assertEqual(common.container_bound_bytes("container-agent", 8), int(17.5 * GIB))
        del pins["container"]
        with mock.patch.object(common, "load_pins", return_value=pins):
            with self.assertRaises(common.CapError):
                common.container_bound_bytes("container-verify", 8)

    def test_a_job_runs_when_memory_max_is_within_the_bound(self):
        self.memmax(int(11.5 * GIB))
        rc, so, _ = self.run_job("container-verify", ["/bin/sh", "-c", "echo capped"])
        self.assertEqual(rc, 0)
        self.assertEqual(Path(so).read_text(), "capped\n")
        self.assertEqual((Path(so).parent / "exit.txt").read_text(), "0\n")

    def test_refused_without_a_cap_or_above_the_bound(self):
        for value in ("max", str(int(11.5 * GIB) + 1), "junk"):
            self.memmax(value)
            with self.assertRaises(common.CapError):
                self.run_job("container-verify", ["/bin/true"])
        (self.cg / "memory.max").unlink()
        with self.assertRaises(common.CapError):
            self.run_job("container-verify", ["/bin/true"])
        self.memmax(int(15.5 * GIB))
        with self.assertRaises(common.CapError):            # an agent container's cap, verify mode
            self.run_job("container-verify", ["/bin/true"])
        self.assertEqual(self.run_job("container-agent", ["/bin/true"])[0], 0)

    def test_memory_events_are_required(self):
        self.memmax(GIB)
        (self.cg / "memory.events").unlink()
        with self.assertRaises(common.CapError):
            self.run_job("container-verify", ["/bin/true"])

    def test_an_oom_kill_during_the_job_is_killed_memory_whatever_its_exit(self):
        self.memmax(GIB)
        bump = f"printf 'oom 1\\noom_kill 1\\n' > {self.cg}/memory.events; exit 1"
        rc, _, _ = self.run_job("container-verify", ["/bin/sh", "-c", bump])
        self.assertEqual(rc, 137)
        self.assertTrue(common.is_killed(rc))
        self.events(1)
        rc, _, _ = self.run_job("container-verify", ["/bin/sh", "-c", "exit 1"])
        self.assertEqual(rc, 1)                              # no new kill: the tool's own exit

    def test_the_wall_clock_net_is_124(self):
        self.memmax(GIB)
        t0 = time.monotonic()
        rc, _, _ = self.run_job("container-agent", ["/bin/sh", "-c", "sleep 30"], timeout_s=1)
        self.assertEqual(rc, common.WALL_CLOCK_EXIT)
        self.assertLess(time.monotonic() - t0, 15)

    def test_container_agent_runs_one_solver_job_at_a_time_across_pools(self):
        self.memmax(GIB)
        spans = []

        def job(pool):
            t0 = time.monotonic()
            self.run_job("container-agent", ["/bin/sh", "-c", "sleep 0.6"], pool=pool)
            spans.append((t0, time.monotonic()))

        ts = [threading.Thread(target=job, args=(p,)) for p in ("dafny", "verus")]
        t0 = time.monotonic()
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        self.assertGreaterEqual(time.monotonic() - t0, 1.15)

    def test_a_bad_mode_is_refused_and_host_mode_is_the_default(self):
        with mock.patch.dict(os.environ, {"DVL_CAP": "uncapped"}):
            with self.assertRaises(common.CapError):
                common.run_capped(["/bin/true"], 8, 5)
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DVL_CAP", None)
            self.assertEqual(common.cap_mode(), "host")


class ContainerLifeline(unittest.TestCase):
    """The container lifeline kills the job's process group when the parent's
    pipe closes, under /bin/sh (dash on Ubuntu, the image's shell): it once ran
    `kill -KILL -- "-$pgid"`, which dash rejects (DELTAS Δ504)."""

    def test_a_closed_pipe_kills_the_whole_group_under_dash(self):
        import subprocess
        job = subprocess.Popen(["sh", "-c", "sleep 300 & exec sleep 300"], start_new_session=True)
        try:
            w = common._container_lifeline(job.pid)
            os.close(w)                       # the parent "died": EOF, nothing written
            t0 = time.monotonic()
            while job.poll() is None:
                self.assertLess(time.monotonic() - t0, 10, "the lifeline left the job running")
                time.sleep(0.05)
            r = subprocess.run(["pgrep", "-g", str(job.pid)], capture_output=True)
            self.assertNotEqual(r.returncode, 0, "a process of the group survived")
        finally:
            try:
                os.killpg(job.pid, 9)
            except ProcessLookupError:
                pass


class NoLeftovers(unittest.TestCase):
    """The suite above leaves nothing in its temporary base: every directory a test
    makes (the cgroup and scratch fixtures, each job's output directory) is removed
    when the test ends (DV5d: the job directories were not, and hundreds of
    /tmp/dvl0-sandbox-job-* accumulated)."""

    def test_the_container_mode_suite_removes_every_directory_it_makes(self):
        import io
        import tempfile
        base = Path(tempfile.mkdtemp(prefix="dvl0-sandbox-leftovers-", dir=sc.TMP_BASE))
        self.addCleanup(sc.cleanup, base)
        with mock.patch.object(sc, "TMP_BASE", str(base)):
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(ContainerModes)
            res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
        self.assertTrue(res.wasSuccessful(), res.errors + res.failures)
        self.assertGreater(res.testsRun, 5)
        self.assertEqual(sorted(p.name for p in base.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
