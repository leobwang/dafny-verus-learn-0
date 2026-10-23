"""fvh.lsp, the frozen entry point to the Dafny language server (QPLAN §30 Q56).

No server runs here: the launcher's command line is checked through its
`--argv` mode, and stop_server on fake processes."""

import subprocess
import sys
from pathlib import Path

import pytest

from fvh import lsp

HARNESS = Path(__file__).resolve().parents[2]
ROOT = HARNESS.parent


def test_course_root_holds_the_launcher():
    assert lsp.course_root() == ROOT
    assert (ROOT / lsp.LAUNCHER).is_file()


def test_missing_launcher_is_unavailable(tmp_path):
    with pytest.raises(lsp.ServerUnavailable):
        lsp.start_server(tmp_path)


@pytest.mark.parametrize("bad", [0, -1, 1.5, True, "60"])
def test_runtime_must_be_a_positive_int(bad):
    with pytest.raises(ValueError):
        lsp.start_server(ROOT, runtime_s=bad)


def test_launcher_runs_the_scratch_server_under_the_cap():
    p = subprocess.run([sys.executable, str(ROOT / lsp.LAUNCHER), "--argv", "--runtime", "60"],
                       capture_output=True, text=True, timeout=120, cwd=ROOT)
    if p.returncode == 3 and "refused" in p.stderr:
        pytest.skip(f"no toolchain or no cap here: {p.stderr.strip()}")
    assert p.returncode == 0, p.stderr
    argv = p.stdout.splitlines()
    assert not any("systemd" in a or a.startswith("MemoryMax=") for a in argv)   # D78: no cap
    i = argv.index("server")
    assert "/dafny-server/" in argv[i - 1] and ".toolchain" not in argv[i - 1]
    assert "--resource-limit" in argv[i:] and "--solver-path" in argv[i:] and "--cores" in argv[i:]


def test_launcher_refuses_a_runtime_past_the_wall_clock():
    p = subprocess.run([sys.executable, str(ROOT / lsp.LAUNCHER), "--argv", "--runtime", "999999"],
                       capture_output=True, text=True, timeout=120, cwd=ROOT)
    assert p.returncode == 3


class Fake:
    def __init__(self, hangs):
        self.hangs, self.pid, self.waits = hangs, 2 ** 22 + 11, 0

        class In:
            closed = False

            def close(s):
                s.closed = True
        self.stdin = In()

    def wait(self, timeout=None):
        self.waits += 1
        if self.hangs and self.waits == 1:
            raise subprocess.TimeoutExpired("dafny", timeout)
        return 0


def test_stop_server_closes_stdin_and_reaps():
    f = Fake(hangs=False)
    assert lsp.stop_server(f, grace_s=0.1) == 0
    assert f.stdin.closed and f.waits == 1


def test_stop_server_kills_a_hanging_server():
    f = Fake(hangs=True)
    assert lsp.stop_server(f, grace_s=0.1) == 0
    assert f.waits == 2
