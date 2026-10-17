"""fvh.lsp — the frozen entry point to the Dafny language server (QPLAN §30 Q56).

Learner code (Q15's client, harness/q/fvh_q/lsp_client.py) never starts a
server process of its own: it calls start_server(), which runs the course's
launcher `scripts/dafny-server` from the course root. The launcher runs the
pinned `dafny server` from the scratch copy of the install (Δ33) under the
Dafny memory cap of CLAUDE.md §Resources (a systemd scope with MemoryMax and
a lifetime), with the pinned solver, resource limit and cores. Standard
library only, like every module of the core.

  start_server(root=None, *, runtime_s=900) -> subprocess.Popen
      the server, talking LSP on the returned process's stdin and stdout
      (binary pipes; stderr is discarded). It is the leader of a process group
      of its own. runtime_s is the scope's lifetime (the launcher refuses more
      than the pinned wall clock). Raises ServerUnavailable when the launcher
      is missing; a launcher that refuses (no cap, no toolchain) exits 3 at
      once, which the caller sees as an end of file on stdout.
  stop_server(proc, *, grace_s=5.0) -> int | None
      ends the server: closes its stdin, waits up to grace_s, then kills its
      process group; returns its exit code (None if it could not be reaped).
  course_root() -> Path
      the checkout root (this file is harness/fvh/lsp.py).

The protocol itself (framing, requests, the server's notifications) is the
learner's to write; nothing here parses a message.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

__all__ = ["ServerUnavailable", "course_root", "start_server", "stop_server", "LAUNCHER"]

LAUNCHER = "scripts/dafny-server"   # repo-relative


class ServerUnavailable(RuntimeError):
    """The course's launcher is not there to run."""


def course_root() -> Path:
    """The checkout root (this file is harness/fvh/lsp.py)."""
    return Path(__file__).resolve().parents[2]


def start_server(root=None, *, runtime_s: int = 900) -> subprocess.Popen:
    """The pinned Dafny language server under the course's cap (module doc)."""
    base = Path(root) if root is not None else course_root()
    launcher = base / LAUNCHER
    if not launcher.is_file():
        raise ServerUnavailable(f"{launcher}: no such launcher")
    if isinstance(runtime_s, bool) or not isinstance(runtime_s, int) or runtime_s < 1:
        raise ValueError(f"runtime_s must be a positive int, not {runtime_s!r}")
    return subprocess.Popen([sys.executable, str(launcher), "--runtime", str(runtime_s)],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, cwd=str(base), start_new_session=True)


def stop_server(proc, *, grace_s: float = 5.0):
    """Close the server's stdin, wait, then kill its process group (module doc)."""
    try:
        if proc.stdin is not None and not proc.stdin.closed:
            proc.stdin.close()
    except OSError:
        pass
    try:
        return proc.wait(timeout=grace_s)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        return proc.wait(timeout=grace_s)
    except subprocess.TimeoutExpired:
        return None
