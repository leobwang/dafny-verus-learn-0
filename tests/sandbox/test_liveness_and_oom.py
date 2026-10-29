"""Δ506's two door fixes, without Docker: the watcher door's "gate stopped" check
uses dvl.host.pid_alive (signal 0, so it also works on macOS, which has no
/proc), and C13's OOMKilled read after an exit 137 is repeated a bounded number
of times (scripts/dvl/sandbox.py _oom_state), so the kill is attributed to the
command that caused it."""

import importlib.machinery
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from dvl import host, sandbox  # noqa: E402

_loader = importlib.machinery.SourceFileLoader(
    "dvl_sandbox_doors", str(ROOT / "tests" / "acceptance" / "sandbox_doors.py"))
_spec = importlib.util.spec_from_loader("dvl_sandbox_doors", _loader)
doors = importlib.util.module_from_spec(_spec)
_loader.exec_module(doors)


class PidAlive(unittest.TestCase):
    def test_a_live_process_then_a_reaped_one(self):
        p = subprocess.Popen(["sleep", "30"])
        try:
            self.assertTrue(host.pid_alive(p.pid))
            self.assertTrue(host.pid_alive(str(p.pid)))
        finally:
            p.kill()
            p.wait()
        self.assertFalse(host.pid_alive(p.pid))

    def test_another_users_process_exists_and_junk_does_not(self):
        self.assertTrue(host.pid_alive(1))          # init/launchd: EPERM or ours, alive
        self.assertFalse(host.pid_alive("not-a-pid"))
        self.assertFalse(host.pid_alive(2 ** 40))


class GateStopped(unittest.TestCase):
    def test_fails_while_the_gate_is_alive(self):
        p = subprocess.Popen(["sleep", "30"])
        try:
            ok, left = doors.gate_stopped([str(p.pid)])
            self.assertFalse(ok, "gate stopped passed while the gate process was alive")
            self.assertEqual(left, [str(p.pid)])
        finally:
            p.kill()
            p.wait()
        ok, left = doors.gate_stopped([str(p.pid)])
        self.assertTrue(ok)
        self.assertEqual(left, [])

    def test_no_gate_found_is_no_pass(self):
        self.assertEqual(doors.gate_stopped([]), (False, []))

    def test_the_check_reads_no_proc(self):
        src = (ROOT / "tests" / "acceptance" / "sandbox_doors.py").read_text(encoding="utf-8")
        self.assertNotIn('Path(f"/proc/', src)


class OomSettle(unittest.TestCase):
    def run_states(self, states, rc, oom_before=False, tries=10):
        calls, sleeps = [], []

        def inspect(name):
            calls.append(name)
            return states[min(len(calls), len(states)) - 1]
        st = sandbox._oom_state("c", rc, oom_before, inspect=inspect, tries=tries, delay=0.01,
                                sleep=sleeps.append)
        return st, len(calls), len(sleeps)

    RUN = {"OOMKilled": False, "Running": True}
    OOM = {"OOMKilled": True, "Running": True}

    def test_a_late_flag_is_waited_for(self):
        st, n, slept = self.run_states([self.RUN, self.RUN, self.RUN, self.OOM], 137)
        self.assertTrue(st["OOMKilled"])
        self.assertEqual((n, slept), (4, 3))

    def test_the_retries_are_bounded(self):
        st, n, slept = self.run_states([self.RUN], 137, tries=5)
        self.assertFalse(st["OOMKilled"])
        self.assertEqual((n, slept), (5, 4))

    def test_no_retry_unless_137_and_not_already_set(self):
        for rc, before in ((0, False), (1, False), (124, False), (137, True)):
            with self.subTest(rc=rc, before=before):
                st, n, slept = self.run_states([self.RUN, self.OOM], rc, oom_before=before)
                self.assertEqual((n, slept), (1, 0))

    def test_a_stopped_container_ends_the_wait(self):
        st, n, slept = self.run_states([{"OOMKilled": False, "Running": False}], 137)
        self.assertEqual((n, slept), (1, 0))


if __name__ == "__main__":
    unittest.main()
