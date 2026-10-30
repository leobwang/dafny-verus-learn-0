"""dvl.host — the few answers that differ between the two supported hosts
(DELTAS Δ503: D77, D78).

The course runs on Linux x86-64 and on macOS on Apple silicon (D77). The
learner provides dafny, verus and uv on PATH (D78), and the course applies no
memory management of its own, so this module only answers what the tools must
ask the OS:

  current()            "linux-x86_64", "macos-arm64", "linux-aarch64" (the arm64
                       sandbox image only), or "unsupported-<os>-<arch>"
  pinned(value)        a per-platform pin's value here ({platform id: value})
  is_macos()
  detach_argv()        the prefix that starts a watcher in its own session and
                       returns at once: `setsid -f` on Linux, a Python fork
                       elsewhere (macOS has no setsid(1))
  default_env(home)    the minimal environment of a tool job
  rust_host_triple()   the Rust host triple Verus's toolchain name ends in
  mem_available_gb()   MemAvailable in whole GiB, for reports only (never a gate)
  pid_alive(pid)       whether a process exists, portably (signal 0; no /proc)
  runtime_dir(), proc_start(pid), listening_tcp_ports(), host_addresses()
                       the sandbox's host facts (DELTAS Δ504; T3 on both hosts)

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
# Not a learner host (D77): linux-aarch64 is the platform of the arm64 sandbox
# image (D80), whose own solver builds pins.toml pins under this id (Δ506).
IMAGE_ONLY = ("linux-aarch64",)


def current():
    u = os.uname()
    if u.sysname == "Linux" and u.machine == "x86_64":
        return "linux-x86_64"
    if u.sysname == "Darwin" and u.machine == "arm64":
        return "macos-arm64"
    if u.sysname == "Linux" and u.machine == "aarch64":
        return "linux-aarch64"
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
    if is_macos():
        return "aarch64-apple-darwin"
    if os.uname().machine == "aarch64":            # the arm64 sandbox image (Δ506)
        return "aarch64-unknown-linux-gnu"
    return "x86_64-unknown-linux-gnu"


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


def docker_arch():
    """The architecture of this host's Docker images: amd64 on Linux x86-64, arm64 on
    Apple silicon (Docker Desktop's Linux VM is arm64 there)."""
    m = os.uname().machine
    return "arm64" if m in ("arm64", "aarch64") else "amd64"


def runtime_dir():
    """The per-user runtime directory: $XDG_RUNTIME_DIR, else /run/user/<uid> (Linux,
    as the sandbox always had it); on macOS, which has neither, a private
    $TMPDIR/dvl-runtime-<uid> (under /var/folders, which Docker Desktop shares)."""
    base = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    if is_macos() and not os.path.isdir(base):
        base = os.path.join(os.environ.get("TMPDIR") or "/tmp", f"dvl-runtime-{os.getuid()}")
        os.makedirs(base, mode=0o700, exist_ok=True)
    return base


def pid_alive(pid):
    """Whether process `pid` exists, on Linux and macOS alike (macOS has no /proc):
    signal 0 checks existence and permission without delivering anything; a
    process of another user (EPERM) exists. A zombie counts as alive until its
    parent reaps it."""
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (OSError, ValueError, OverflowError):
        return False
    return True


def proc_start(pid):
    """A process's start time as a token ('0' when unknown): Linux /proc/<pid>/stat
    field 22 (clock ticks since boot), macOS `ps -o lstart=`."""
    if sys.platform.startswith("linux"):
        try:
            with open(f"/proc/{pid}/stat", encoding="ascii") as fh:
                return fh.read().rsplit(")", 1)[1].split()[19]
        except (OSError, IndexError):
            return "0"
    try:
        out = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True,
                             text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "0"
    return out.replace(" ", "_") if out else "0"


def listening_tcp_ports():
    """Every TCP port the host listens on (Linux `ss -ltnH`; macOS `lsof`)."""
    ports = set()
    if is_macos():
        argv, col = ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN", "-Fn"], None
    else:
        argv, col = ["ss", "-ltnH"], 3
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return ports
    for line in out.splitlines():
        if col is None:
            if line.startswith("n") and ":" in line:
                port = line.rsplit(":", 1)[-1]
                if port.isdigit():
                    ports.add(int(port))
            continue
        cols = line.split()
        if len(cols) > col:
            port = cols[col].rsplit(":", 1)[-1]
            if port.isdigit():
                ports.add(int(port))
    return ports


def host_addresses():
    """The host's addresses but loopback and link-local (Linux `ip -o addr show`;
    macOS `ifconfig`)."""
    out = []
    try:
        if is_macos():
            text = subprocess.run(["ifconfig"], capture_output=True, text=True,
                                  timeout=30).stdout
            for line in text.splitlines():
                cols = line.split()
                if len(cols) >= 2 and cols[0] in ("inet", "inet6"):
                    out.append(cols[1].split("%")[0])
        else:
            text = subprocess.run(["ip", "-o", "addr", "show"], capture_output=True, text=True,
                                  timeout=30).stdout
            for line in text.splitlines():
                cols = line.split()
                if len(cols) >= 4 and cols[2] in ("inet", "inet6"):
                    out.append(cols[3].split("/")[0])
    except (OSError, subprocess.SubprocessError):
        return []
    return [a for a in out if a not in ("127.0.0.1", "::1") and not a.startswith("fe80:")]


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
