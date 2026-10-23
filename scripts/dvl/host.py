"""dvl.host — the few answers that differ between the two supported hosts
(DELTAS Δ503: D77, D78).

The course runs on Linux x86-64 and on macOS on Apple silicon (D77). The
learner provides dafny, verus and uv on PATH (D78), and the course applies no
memory management of its own, so this module only answers what the tools must
ask the OS:

  current()            "linux-x86_64", "macos-arm64", or "unsupported-<os>-<arch>"
  pinned(value)        a per-platform pin's value here ({platform id: value})
  is_macos()
  detach_argv()        the prefix that starts a watcher in its own session and
                       returns at once: `setsid -f` on Linux, a Python fork
                       elsewhere (macOS has no setsid(1))
  default_env(home)    the minimal environment of a tool job
  rust_host_triple()   the Rust host triple Verus's toolchain name ends in
  mem_available_gb()   MemAvailable in whole GiB, for reports only (never a gate)

Run as a module (named host, not platform: a file named platform.py beside a
script run from scripts/dvl/ would shadow the standard library's):
  PYTHONPATH=scripts python3 -m dvl.host id|mem-available-gb
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

SUPPORTED = ("linux-x86_64", "macos-arm64")


def current():
    u = os.uname()
    if u.sysname == "Linux" and u.machine == "x86_64":
        return "linux-x86_64"
    if u.sysname == "Darwin" and u.machine == "arm64":
        return "macos-arm64"
    return f"unsupported-{u.sysname.lower()}-{u.machine}"


def pinned(value, platform=None):
    """A per-platform pin's value on `platform` (default: this host): a table
    {platform id: value} gives that platform's entry, None when it has none; a
    plain value is a pin captured on linux-x86_64 before the per-platform
    tables (Δ503) and holds there only."""
    platform = platform or current()
    if isinstance(value, dict):
        return value.get(platform)
    return value if platform == "linux-x86_64" else None


def is_macos():
    return sys.platform == "darwin"


# The detacher where util-linux setsid(1) is absent (macOS): fork, let the
# parent return at once (as `setsid -f` does), start a new session, exec.
_DETACH_PY = ("import os, sys\n"
              "if os.fork():\n    os._exit(0)\n"
              "os.setsid()\n"
              "os.execvp(sys.argv[1], sys.argv[1:])\n")


def detach_argv():
    if sys.platform.startswith("linux"):
        return ["setsid", "-f"]
    return [sys.executable, "-I", "-c", _DETACH_PY]


def default_env(home):
    """Linux: as the course always had it. macOS: the running interpreter's
    directory leads PATH, so `python3` inside a job (dafny test --target py) is
    the course's Python 3.12 and not the system's 3.9, and the locale is one
    macOS has."""
    if is_macos():
        bindir = str(Path(sys.executable).parent)
        return {"PATH": f"{bindir}:/usr/bin:/bin", "LANG": "en_US.UTF-8",
                "LC_ALL": "en_US.UTF-8", "HOME": home}
    return {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "HOME": home}


def rust_host_triple():
    return "aarch64-apple-darwin" if is_macos() else "x86_64-unknown-linux-gnu"


def mem_available_gb():
    """MemAvailable in whole GiB (floored), or None. Reports only."""
    try:
        if sys.platform.startswith("linux"):
            with open("/proc/meminfo", encoding="ascii") as fh:
                for line in fh:
                    if line.startswith("MemAvailable:"):
                        return int(line.split()[1]) // 1048576
            return None
        if is_macos():
            out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
            m = re.search(r"page size of (\d+) bytes", out)
            page = int(m.group(1)) if m else 16384
            n = 0
            for line in out.splitlines():
                k, _, v = line.partition(":")
                if k.strip() in ("Pages free", "Pages inactive", "Pages speculative",
                                 "Pages purgeable"):
                    n += int(v.strip().rstrip("."))
            return n * page // (1 << 30)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return None


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["id"]:
        print(current())
    elif args == ["mem-available-gb"]:
        v = mem_available_gb()
        print("" if v is None else v)
    else:
        print("usage: python3 -m dvl.host id|mem-available-gb", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
