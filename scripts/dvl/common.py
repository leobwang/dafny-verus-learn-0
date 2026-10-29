"""dvl.common — shared types and plumbing for the pinned verifier wrappers.

Owned by the DV1b Dafny lane; dvl.dafny and dvl.verus both build on it and the
tools (vcheck, vaudit, specfreeze, pins.py, firsttry) consume what it defines.

Types (the fixed interface between the language libraries and the tools):

  Diag(file, line, col, severity, message, code)
      One tool diagnostic. `file` is an absolute path as the tool named it,
      mapped back from any scratch copy to the original file (a file the tool
      synthesised, such as Dafny's bundled standard library, keeps the tool's
      bare name). `line` and `col` are 1-based in both languages (Dafny prints
      0-based columns; dvl.dafny adds one). `severity` is one of
      error | warning | info | hint | related (`related` is a location the
      preceding diagnostic points at, such as "this is the postcondition that
      could not be proved"). `message` is the tool's text with any `{0}`
      template filled in. `code` is the pinned wording id (`W-D01`, `W-V07`, …,
      VERSIONS.md §2.4) when the message matches one exactly, else the tool's
      own id when it has one, else "".
  Hole(file, line, col, kind, label)
      One tool-counted hole. `kind` names the pinned wording that counted it
      (Dafny: bodyless-method W-D01, bodyless-function W-D02, assume W-D03).
      `label` is the item id whose block holds the hole (`Q04.H1d`), else the
      enclosing declaration's name, else "".
  Finding(file, line, kind, message)
      One static or audit finding (lint rule, audit row, freeze violation).
      `file` is an absolute path, or the target as given for a finding about
      the whole target; `line` is 1-based, 0 when the finding has no line.
      `kind` is a kebab-case rule slug; `message` states the rule, never the
      offending code (scripts print locations, never content).
  Result(lang, target, exit_code, verdict, stage, verified_count, holes,
         diagnostics, findings, per_symbol, raw_dir, cmd)
      One wrapper call. `verdict` ∈ VERDICTS; `stage` ∈ STAGES is the stage the
      run reached or stopped at. `exit_code` is the tool's exit code (None when
      no tool ran: a refusal); a memory kill is reported as 137 or 143 with
      verdict killed(memory), never as a verification verdict (CLAUDE.md
      §Resources), and the wall-clock safety kill (DELTAS Δ58) as 124 with
      verdict inconclusive. `verified_count` is the tool's own count (Dafny:
      verification tasks, Δ39; Verus: `verified`, Δ40) or None when the run
      printed none. `per_symbol` maps a symbol to its status; `raw_dir` holds the
      raw outputs (cmd.txt, stdout.txt, stderr.txt, exit.txt, and any logs);
      `cmd` is the argv of the (last) tool command, without the cap wrapper.

Plumbing:

  load_pins()          the parsed scripts/dvl/pins.toml ([dafny] and [verus]):
                       the ONE place pinned flags, limits, caps and message
                       wordings live (spec §3.1 rule 6).
  toolchain(tool)      the tool paths: `dafny` and `verus` from PATH (DELTAS Δ503,
                       D78), each version compared with the pins once per
                       process; a mismatch warns and marks the run untrusted
                       (D79: untrusted(), trust_note()). With DVL_TOOLCHAIN_DIR
                       set (the sandbox images), the pinned install there.
  run_capped(argv, mem_gb, timeout_s, env, cwd)
                       runs one tool job as a plain process (D78: the course
                       applies no memory management; memory is the host's and
                       the user's), with a cross-process concurrency limit per
                       pool (env DVL_<POOL>_JOBS, default from the pins: 1), a
                       scrubbed environment, the Δ58 wall-clock kill (124) and a
                       lifeline watcher that kills the job's process group when
                       the caller dies, so no solver outlives its caller.
                       Returns (exit_code, stdout_path, stderr_path); callers
                       map 137/143 to killed(memory). Inside a sandbox
                       container (DVL_CAP=container-verify or container-agent,
                       set by scripts/mksandbox-run) it runs the job only when
                       the container's own cgroup memory.max is within the
                       bound pins.toml [container] gives (see CAP_MODES below;
                       DV4-PLAN §5.9): container configuration, not course-side
                       management.

  hole_regions(text, item_id=None), strip_regions(text, item_id)
                       the `@hole-begin`/`@hole-end` learner regions of a
                       reference twin and the twin with an item's regions
                       blanked (the empty-body gate's region mode, QPLAN §6
                       Q18; specfreeze's open frames, §6 Q22).

Environment:
  DVL_SCRATCH        scratch root for raw outputs and scratch copies
                     (default /tmp/dvl-<uid>; never inside a course tree).
  DVL_DAFNY_JOBS, DVL_VERUS_JOBS
                     concurrent jobs per pool (default 1 each, from the pins).
  DVL_TOOLCHAIN_DIR  the pinned install to use instead of PATH (the sandbox
                     images, tests), through scripts/get_toolchain.sh --check.
"""

from __future__ import annotations

import copy
import dataclasses
import fcntl
import functools
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import signal
import sys
import subprocess
import tempfile
import time
import tomllib
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from dvl import host as plat

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
PINS_FILE = Path(__file__).resolve().with_name("pins.toml")
GET_TOOLCHAIN = SCRIPTS / "get_toolchain.sh"

VERDICTS = ("verified", "failed", "inconclusive", "refused", "killed(memory)", "error")
STAGES = ("cli", "parse", "resolve", "verify", "compile", "link", "test", "run")
SEVERITIES = ("error", "warning", "info", "hint", "related")
KILLED_EXITS = (137, 143)     # SIGKILL / SIGTERM: a memory kill, never a verdict
WALL_CLOCK_EXIT = 124         # dvl's own wall-clock safety kill (Δ58), as timeout(1) reports
TIMEOUT_EXIT = WALL_CLOCK_EXIT  # the same code under the name dvl.verus reads


class DvlError(Exception):
    """A wrapper could not do its job (bad pins, broken toolchain, no cap)."""


class ToolchainError(DvlError):
    """scripts/get_toolchain.sh --check refused the pinned install."""


class CapError(DvlError):
    """The memory cap could not be applied; no solver job may run uncapped."""


# --- the interface types ------------------------------------------------------------

@dataclass(frozen=True)
class Diag:
    file: str
    line: int
    col: int
    severity: str
    message: str
    code: str = ""


@dataclass(frozen=True)
class Hole:
    file: str
    line: int
    col: int
    kind: str
    label: str = ""


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    kind: str
    message: str


@dataclass
class Result:
    lang: str
    target: str
    exit_code: int | None
    verdict: str
    stage: str
    verified_count: int | None = None
    holes: list[Hole] = field(default_factory=list)
    diagnostics: list[Diag] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    per_symbol: dict[str, str] = field(default_factory=dict)
    raw_dir: str | None = None
    cmd: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.verdict not in VERDICTS:
            raise ValueError(f"unknown verdict {self.verdict!r}")
        if self.stage not in STAGES:
            raise ValueError(f"unknown stage {self.stage!r}")

    def to_dict(self):
        """A JSON-ready dict (lists of dicts for the nested records)."""
        return dataclasses.asdict(self)


def to_json(obj):
    """JSON text for a Result, or for a list of Diag/Hole/Finding records."""
    if dataclasses.is_dataclass(obj):
        obj = dataclasses.asdict(obj)
    elif isinstance(obj, list):
        obj = [dataclasses.asdict(x) if dataclasses.is_dataclass(x) else x for x in obj]
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def display_path(p):
    """`p` relative to the repo root when it lies inside it, else as given."""
    try:
        return Path(p).resolve().relative_to(REPO_ROOT).as_posix()
    except (ValueError, OSError):
        return str(p)


# --- pins -----------------------------------------------------------------------------

# Keys every consumer may rely on; load_pins refuses a pins file without them.
REQUIRED_PINS = {
    "dafny": ("install", "binary", "version_output", "solver", "solver_version",
              "resource_limit", "cores", "mem_gb", "wall_clock_s", "jobs", "seeds",
              "seed_mutations", "messages", "patterns"),
    "verus": ("install", "binary", "version", "solver", "solver_version", "rlimit",
              "num_threads", "mem_gb", "wall_clock_s", "timeout_s", "jobs", "seeds",
              "scrub_env", "smt_options", "high_rlimit_factor", "rust_toolchain", "messages"),
}


@functools.lru_cache(maxsize=1)
def _load_pins_cached(path):
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        raise DvlError(f"pins file not found: {path}") from None
    except tomllib.TOMLDecodeError as e:
        raise DvlError(f"pins file {path} is not valid TOML: {e}") from None
    for section, keys in REQUIRED_PINS.items():
        table = data.get(section)
        if not isinstance(table, dict):
            raise DvlError(f"pins file {path}: no [{section}] table")
        missing = [k for k in keys if k not in table]
        if missing:
            raise DvlError(f"pins file {path}: [{section}] lacks " + ", ".join(missing))
        if not table["seeds"]:
            raise DvlError(f"pins file {path}: [{section}] seeds is empty (empty lists fail)")
    return data


def load_pins():
    """The pinned settings: a fresh deep copy of scripts/dvl/pins.toml."""
    return copy.deepcopy(_load_pins_cached(str(PINS_FILE)))


# --- toolchain ---------------------------------------------------------------------------
#
# DELTAS Δ503 (D78, D79): the learner provides `dafny` (4.11.0) and `verus`
# (0.2026.09.27.3cf1832) on PATH; the wrappers call them as plain processes.
# At first use each tool's version is compared with the pins; a mismatch is a
# WARNING and the run continues, but everything whose meaning depends on the
# exact toolchain (the done gate's verdict, pins, first tries, brittleness
# figures) says it is UNTRUSTED (untrusted(), trust_note()). The Dafny solver
# is the Z3 4.12.1 its release zip bundles next to it (dafny/z3/bin/), else a
# `z3-4.12.1` or `z3` on PATH (a `dotnet tool` install brings none); its version
# is checked the same way. With DVL_TOOLCHAIN_DIR set (the sandbox images and
# their tests) the pinned install under that directory is used instead, after
# scripts/get_toolchain.sh <tool> --check, as before.
#
# Each Z3 bundled with Dafny (pins.toml [dafny.solvers]) is also compared by
# its sha256, against the release zip's own binary for this platform (one pin
# per supported platform, dvl.host.current(); Δ503). That comparison is part of
# toolchain("dafny") (dafny_solvers()), so `vcheck --versions` and every run
# see the same mismatches.

_TOOLCHAIN_CACHE: dict[str, dict[str, Path]] = {}
_SOLVERS: dict[str, Path] = {}        # bundled solver name -> the binary used
_MISMATCH: dict[str, list] = {}       # tool -> ["<what>: found …, pinned …", …]
_WARNED: set = set()


def pinned_solver_sha256(entry, platform=None):
    """A bundled Dafny solver's pinned sha256 on `platform` (default: this host,
    dvl.host.current()): pins.toml [dafny.solvers] keeps one per supported
    platform, the binary in that platform's pinned release zip. None when the
    pins name none for the platform."""
    return plat.pinned(entry.get("sha256"), platform)


def solver_hash_mismatch(name, path, entry, platform=None):
    """None when the solver `name` at `path` is the pinned binary for `platform`,
    else the mismatch line (D79: a warning and UNTRUSTED, never a refusal)."""
    platform = platform or plat.current()
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    want = pinned_solver_sha256(entry, platform)
    if digest == want:
        return None
    if want is None:
        return f"the solver {name} at {path} has sha256 {digest}; no sha256 is pinned for {platform}"
    return f"the solver {name} at {path} has sha256 {digest}, not the pinned {want} ({platform})"


def _locate_solver(root, entry):
    """A bundled solver's binary: in the release zip's layout under `root`, else
    on PATH by its file name (z3-<version>); None when neither exists."""
    p = Path(root) / entry["path"]
    if p.is_file():
        return p
    found = shutil.which(Path(entry["path"]).name)
    return Path(found).resolve() if found else None


def _bundled_solvers(root, pinned_z3, pins):
    """({name: path} of the bundled solvers found, [mismatch, …]): the pinned
    one is the solver toolchain() resolved; a missing other one is no
    mismatch (dafny.solver_path() refuses it when a run names it)."""
    paths, bad = {}, []
    for name, entry in (pins.get("solvers") or {}).items():
        path = Path(pinned_z3) if entry["path"] == pins["solver"] else _locate_solver(root, entry)
        if path is None:
            continue
        paths[name] = path
        m = solver_hash_mismatch(name, path, entry)
        if m:
            bad.append(m)
    return paths, bad


def dafny_solvers():
    """{name: path} of the Z3 binaries bundled with Dafny that toolchain("dafny")
    found and checked (their hash mismatches are in untrusted())."""
    toolchain("dafny")
    return dict(_SOLVERS)


def _check_tool(tool):
    try:
        p = subprocess.run(["bash", str(GET_TOOLCHAIN), tool, "--check"], capture_output=True,
                           text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ToolchainError(f"get_toolchain.sh {tool} --check did not run: {e}") from None
    lines = p.stdout.strip().splitlines()
    if p.returncode != 0 or len(lines) != 1:
        last = (p.stderr.strip().splitlines() or ["(no message)"])[-1]
        raise ToolchainError(f"get_toolchain.sh {tool} --check refused (exit {p.returncode}): "
                             f"{last}")
    binary = Path(lines[0])
    pins = load_pins()[tool]
    root = binary
    for _ in Path(pins["binary"]).parts:
        root = root.parent
    if root.name != pins["install"]:
        raise ToolchainError(f"get_toolchain.sh {tool} printed {binary}, which is not under the "
                             f"pinned install {pins['install']}")
    out = {tool: binary, f"{tool}_root": root, f"{tool}_z3": root / pins["solver"]}
    if tool == "verus":
        out["cargo_verus"] = root / pins["cargo_verus"]
    for k, v in out.items():
        if not v.exists():
            raise ToolchainError(f"pinned path {k} does not exist: {v}")
    bad = []                              # the pinned install: verified by its own check,
    if tool == "dafny":                   # its bundled solvers compared as on PATH
        found, bad = _bundled_solvers(root, out["dafny_z3"], pins)
        _SOLVERS.clear()
        _SOLVERS.update(found)
    _MISMATCH[tool] = bad
    _warn(tool, bad)
    return out


def _first_line(argv, env=None):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=120, env=env,
                           stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    lines = (p.stdout or "").strip().splitlines()
    return lines[0].strip() if p.returncode == 0 and lines else None


def rust_toolchain():
    """The Rust toolchain Verus's jobs run with: the pinned one, for this host's triple."""
    pinned = load_pins()["verus"]["rust_toolchain"]
    return pinned.split("-", 1)[0] + "-" + plat.rust_host_triple()


def _on_path(tool):
    found = shutil.which(tool)
    if found is None:
        raise ToolchainError(f"`{tool}` is not on PATH; install the pinned {tool} and put it on "
                             "PATH (README, Setup)")
    p = Path(found).absolute()
    # A symlinked command (/usr/local/bin/dafny → the install) is followed to the
    # install, whose layout locates the bundled solvers; a PATH entry naming the
    # install directory itself keeps its spelling, as the paths in outputs do.
    return p.resolve() if p.is_symlink() else p


def _dafny_solver(binary, pins):
    """The Z3 for --solver-path: the release zip's bundled one, else one on PATH."""
    for c in (binary.parent.parent / pins["solver"], binary.parent / "z3" / "bin" /
              Path(pins["solver"]).name):
        if c.is_file():
            return c
    for name in (Path(pins["solver"]).name, "z3"):
        found = shutil.which(name)
        if found:
            return Path(found).resolve()
    raise ToolchainError(f"no Z3 for Dafny: neither {Path(pins['solver']).name} next to "
                         f"{binary} (the release zip's layout) nor `z3-4.12.1` or `z3` on PATH "
                         "(README, Setup)")


def _path_tool(tool):
    pins = load_pins()[tool]
    bad = []
    if tool == "dafny":
        binary = _on_path("dafny")
        root = binary.parent.parent if binary.parent.name == "dafny" else binary.parent
        z3 = _dafny_solver(binary, pins)
        got = _first_line([str(binary), "--version"])
        if got != pins["version_output"]:
            bad.append(f"dafny --version: found {got!r}, pinned {pins['version_output']!r}")
        out = {"dafny": binary, "dafny_root": root, "dafny_z3": z3}
        found, sbad = _bundled_solvers(root, z3, pins)
        _SOLVERS.clear()
        _SOLVERS.update(found)
    else:
        binary = _on_path("verus")
        root = binary.parent
        z3 = root / "z3"
        env = dict(os.environ, RUSTUP_TOOLCHAIN=rust_toolchain())
        raw = None
        try:
            p = subprocess.run([str(binary), "--version", "--output-json"], capture_output=True,
                               text=True, timeout=120, env=env, stdin=subprocess.DEVNULL)
            raw = json.loads(p.stdout)["verus"]
            got = f"{raw.get('version')} {raw.get('commit')}"
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
            got = None
        want = f"{pins['version']} {pins['commit']}"
        if got != want:
            bad.append(f"verus --version: found {got!r}, pinned {want!r}")
        if not z3.is_file():
            raise ToolchainError(f"no z3 next to {binary} (the Verus release layout)")
        out = {"verus": binary, "verus_root": root, "verus_z3": z3,
               "cargo_verus": root / "cargo-verus"}
    zv = _first_line([str(z3), "--version"])
    if zv != pins["solver_version"]:
        bad.append(f"{z3.name} --version: found {zv!r}, pinned {pins['solver_version']!r}")
    if tool == "dafny":
        bad += sbad
    _MISMATCH[tool] = bad
    _warn(tool, bad)
    return out


def _warn(tool, bad):
    if bad and tool not in _WARNED:
        _WARNED.add(tool)
        print(f"dvl: WARNING: {tool} is not the pinned toolchain ({'; '.join(bad)}). The run "
              "continues, but its verdicts, pins, first tries and brittleness figures are "
              "UNTRUSTED (DELTAS Δ503, D79).", file=sys.stderr)


def toolchain(tool=None, fresh=False):
    """The tool paths. tool "dafny" → {dafny, dafny_root, dafny_z3}; "verus" →
    {verus, verus_root, verus_z3, cargo_verus}; None → both. From PATH (D78),
    with the version check of D79 (a mismatch warns once and marks the run
    untrusted); with DVL_TOOLCHAIN_DIR set, the pinned install there after
    get_toolchain.sh --check. Once per process unless `fresh` (the done gate
    re-checks, Δ10). Raises ToolchainError when a tool is missing."""
    tools = ("dafny", "verus") if tool is None else (tool,)
    out = {}
    for t in tools:
        if t not in REQUIRED_PINS:
            raise ValueError(f"unknown tool {t!r}")
        if fresh or t not in _TOOLCHAIN_CACHE:
            _TOOLCHAIN_CACHE[t] = _check_tool(t) if os.environ.get("DVL_TOOLCHAIN_DIR") \
                else _path_tool(t)
        out.update(_TOOLCHAIN_CACHE[t])
    return out


def note_mismatch(tool, what):
    """Record one more way `tool` differs from the pins (a solver's hash, say):
    a warning, never a refusal (D79)."""
    _MISMATCH.setdefault(tool, [])
    if what not in _MISMATCH[tool]:
        _MISMATCH[tool].append(what)
        print(f"dvl: WARNING: {what}; this run's results are UNTRUSTED (DELTAS Δ503, D79).",
              file=sys.stderr)


def untrusted(tool=None):
    """{tool: [mismatch, …]} of the tools checked so far whose version is not the
    pinned one (D79); only `tool`'s when given. Empty: every checked tool is pinned."""
    return {t: list(v) for t, v in _MISMATCH.items() if v and (tool is None or t == tool)}


def trust_note(tool=None):
    """'' when trusted, else the one-line UNTRUSTED note every exact-behaviour
    output carries (D79)."""
    u = untrusted(tool)
    if not u:
        return ""
    return ("UNTRUSTED (toolchain version mismatch: "
            + "; ".join(m for v in u.values() for m in v) + ")")


# --- scratch ------------------------------------------------------------------------------

def scratch_root():
    """The scratch root: $DVL_SCRATCH, else /tmp/dvl-<uid>. Created 0700."""
    root = Path(os.environ.get("DVL_SCRATCH") or f"/tmp/dvl-{os.getuid()}").absolute()
    if plat.is_macos():
        root = root.resolve()       # /tmp is /private/tmp there: one spelling for every tool
    try:
        root.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise DvlError(f"DVL_SCRATCH {root} lies inside the course tree; scratch never does")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return root


def scratch_dir(prefix):
    """A fresh directory under the scratch root's runs/ (kept: it is the raw_dir)."""
    runs = scratch_root() / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return Path(tempfile.mkdtemp(prefix=f"{prefix}-{stamp}-", dir=runs))


# --- the job runner ----------------------------------------------------------------------------

def default_env():
    """A minimal environment for a solver job: nothing that could steer a verifier."""
    env = plat.default_env(os.environ.get("HOME", "/tmp"))
    if os.environ.get("DOTNET_ROOT"):          # a `dotnet tool` Dafny finds its runtime here
        env["DOTNET_ROOT"] = os.environ["DOTNET_ROOT"]
    return env


def pool_of(argv):
    """The concurrency pool of a command: dafny or verus by the binary's name."""
    name = Path(argv[0]).name.lower()
    if "dafny" in name:
        return "dafny"
    if "verus" in name or name.startswith("rust_verify"):
        return "verus"
    return re.sub(r"[^a-z0-9]+", "_", name) or "solver"


def jobs(pool):
    """Concurrent jobs allowed in `pool`: $DVL_<POOL>_JOBS, else the pin, else 1."""
    env = os.environ.get(f"DVL_{pool.upper()}_JOBS")
    if env is not None:
        try:
            n = int(env)
        except ValueError:
            raise DvlError(f"DVL_{pool.upper()}_JOBS={env!r} is not an integer") from None
    else:
        n = int(load_pins().get(pool, {}).get("jobs", 1))
    if n < 1:
        raise DvlError(f"DVL_{pool.upper()}_JOBS must be at least 1")
    return n


class _Slot:
    """One of `n` cross-process slots of a pool, held by an flock (released on
    exit or death, so a crashed job never leaves a stale lock)."""

    def __init__(self, pool, n):
        self.dir = scratch_root() / "slots" / pool
        self.dir.mkdir(parents=True, exist_ok=True)
        self.n, self.fd = n, None

    def __enter__(self):
        while True:
            for k in range(self.n):
                fd = os.open(self.dir / f"slot-{k}.lock", os.O_RDWR | os.O_CREAT, 0o600)
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    os.close(fd)
                    continue
                self.fd = fd
                return self
            time.sleep(0.2)

    def __exit__(self, *exc):
        if self.fd is not None:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            os.close(self.fd)
            self.fd = None


def _killpg(pid):
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


# The host lifeline (POSIX sh; $1 = the job's process group): `done` on stdin
# after a normal return kills the group once (stragglers, such as a solver
# whose driver exited); EOF with nothing read (the parent died: SIGKILL,
# Ctrl-C, a crash) kills it at once. `kill -s KILL -- -<pgid>` is the POSIX
# form, which dash (Ubuntu's /bin/sh) and macOS's sh both accept.
_LIFELINE_SH = r"""
pgid="$1"
IFS= read -r line
kill -s KILL -- "-$pgid" >/dev/null 2>&1
exit 0
"""


def _lifeline(pgid):
    """Start the watcher of process group `pgid` and return the write end of its
    pipe. It runs detached (its own session, re-parented), so neither a signal to
    this process group nor a kill of this process's children reaches it; both
    pipe ends are close-on-exec here, so no other child holds the write end."""
    r, w = os.pipe()
    try:
        subprocess.run(plat.detach_argv() + ["sh", "-c", _LIFELINE_SH, f"dvl-lifeline-{pgid}",
                                             str(pgid)],
                       stdin=r, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       close_fds=True, check=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        os.close(w)
        raise DvlError(f"cannot start the lifeline watcher of a job ({e}); refusing to run a "
                       "solver that could outlive its caller") from None
    finally:
        os.close(r)
    return w


def run_capped(argv, mem_gb, timeout_s, env=None, cwd=None, *, pool=None, out_dir=None):
    """Run one tool job. Returns (exit_code, stdout_path, stderr_path).

    On the host (D78) the job is a plain process: the course applies no memory
    management (memory is the host's and the user's; `mem_gb` is read only by
    the sandbox's container modes, below). What stays:
    - `env` is the job's COMPLETE environment (default: default_env()).
    - At most jobs(pool) jobs of a pool run at once across all processes of this
      user (DVL_<POOL>_JOBS; pool defaults to pool_of(argv)).
    - After `timeout_s` seconds the job's process group is killed and 124 is
      returned (the Δ58 wall-clock net: a failure, never a verdict). A signal
      death is 128 + signal; 137/143 (SIGKILL/SIGTERM, e.g. the host's OOM
      killer) is killed(memory), never a verdict.
    - No orphan: the job runs in its own process group, and a detached lifeline
      watcher kills that group when the job returns (stragglers) or when this
      process dies first.
    - stdout and stderr go to files in `out_dir` (default: a fresh scratch dir),
      next to cmd.txt (the argv) and exit.txt."""
    if not argv:
        raise ValueError("empty argv")
    if not float(timeout_s) > 0:
        raise ValueError(f"timeout_s must be positive, not {timeout_s!r}")
    mode = cap_mode()
    if mode != "host":
        return _run_in_container(argv, mem_gb, timeout_s, env, cwd, pool=pool, out_dir=out_dir,
                                 mode=mode)
    env = default_env() if env is None else dict(env)
    out = Path(out_dir) if out_dir else scratch_dir(f"job-{pool_of(argv)}")
    out.mkdir(parents=True, exist_ok=True)
    cwd = Path(cwd) if cwd else out
    stdout_path, stderr_path = out / "stdout.txt", out / "stderr.txt"
    (out / "cmd.txt").write_text(shlex.join(str(a) for a in argv) + "\n", encoding="utf-8")
    pool = pool or pool_of(argv)
    with _Slot(pool, jobs(pool)):
        with open(stdout_path, "wb") as so, open(stderr_path, "wb") as se:
            started = time.monotonic()
            proc = subprocess.Popen([str(a) for a in argv], stdout=so, stderr=se,
                                    stdin=subprocess.DEVNULL, cwd=cwd, env=env,
                                    start_new_session=True)
            try:
                lifeline = _lifeline(proc.pid)
            except DvlError:
                _killpg(proc.pid)
                proc.wait()
                raise
            finished = False
            try:
                try:
                    rc = proc.wait(timeout=timeout_s)
                    timed_out = False
                except subprocess.TimeoutExpired:
                    timed_out = True
                    _killpg(proc.pid)
                    rc = proc.wait()
                except BaseException:
                    _killpg(proc.pid)
                    proc.wait()
                    raise
                elapsed = time.monotonic() - started
                finished = True
            finally:
                _cut_lifeline(lifeline, finished)
    if rc < 0:
        rc = 128 - rc
    if timed_out or (rc in KILLED_EXITS and elapsed >= float(timeout_s)):
        rc = WALL_CLOCK_EXIT
    (out / "exit.txt").write_text(f"{rc}\n", encoding="utf-8")
    return rc, stdout_path, stderr_path


def run_attached(argv, runtime_s, env):
    """A server on this process's stdin and stdout (scripts/dafny-server): the
    child inherits both, runs in its own process group, and is killed after
    runtime_s (124) or when this process dies (the lifeline). Returns its exit code."""
    proc = subprocess.Popen([str(a) for a in argv], env=dict(env), start_new_session=True)
    try:
        lifeline = _lifeline(proc.pid)
    except DvlError:
        _killpg(proc.pid)
        proc.wait()
        raise
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, lambda *_, s=sig: (_killpg(proc.pid), os._exit(128 + s)))
    try:
        try:
            rc = proc.wait(timeout=runtime_s)
        except subprocess.TimeoutExpired:
            _killpg(proc.pid)
            proc.wait()
            return WALL_CLOCK_EXIT
    finally:
        _cut_lifeline(lifeline, True)
    return 128 - rc if rc < 0 else rc


def _cut_lifeline(w, finished):
    """Release the watcher: `done` after a normal return (it kills the group
    once, for stragglers), plain EOF otherwise (it treats the parent as dead)."""
    try:
        if finished:
            os.write(w, b"done\n")
    except OSError:
        pass                      # the watcher is gone
    finally:
        os.close(w)


def is_killed(exit_code):
    """True for 137/143: record killed(memory), never a verification verdict."""
    return exit_code in KILLED_EXITS


# --- the container modes (DV4-PLAN §5.9; DV4 step 1c) -------------------------------------
#
# Inside a sandbox container the job's bound is the container's own: the container's
# processes live under the Docker daemon's cgroup, and the container's
# --memory (= --memory-swap) is the hard bound. scripts/mksandbox-run sets
# DVL_CAP to one of two modes, and run_capped then runs a job only when the
# container's own cgroup memory.max is set and at most
#   container-verify: the job's pinned cap + margin + the tmpfs caps
#   container-agent:  the same + the agent allowance
# (scripts/dvl/pins.toml [container]; never from the environment). A job
# during which the cgroup's memory.events oom_kill count rose is
# killed(memory) (137), whatever its own exit; the wall-clock net (124) and
# the exit map stay as in host mode (Δ57, Δ58, Δ100). container-agent runs
# one solver job at a time across every pool (one flock), since the agent
# shares the container. Unsetting DVL_CAP inside a container gains nothing:
# the container's --memory still bounds every process in it.

CAP_MODES = ("container-verify", "container-agent")
CGROUP_DIR = Path("/sys/fs/cgroup")   # the container's own cgroup (cgroupns); tests patch it
GIB = 1 << 30


def cap_mode():
    """'host' (DVL_CAP unset or empty), or one of CAP_MODES; CapError otherwise."""
    m = os.environ.get("DVL_CAP", "")
    if m == "":
        return "host"
    if m in CAP_MODES:
        return m
    raise CapError(f"DVL_CAP={m!r} is not a cap mode (host mode is DVL_CAP unset; the container "
                   f"modes are {', '.join(CAP_MODES)})")


def container_bound_bytes(mode, mem_gb):
    """The largest memory.max a container may have for a job of `mem_gb` in `mode`."""
    c = load_pins().get("container")
    keys = ("margin_gb", "work_gb", "tmp_gb", "home_gb", "agent_allowance_gb")
    if not isinstance(c, dict) or any(not isinstance(c.get(k), (int, float)) for k in keys):
        raise CapError("scripts/dvl/pins.toml has no complete [container] table; refusing to run "
                       "a solver in a container whose bound is unknown")
    gb = float(mem_gb) + float(c["margin_gb"]) + float(c["work_gb"]) + float(c["tmp_gb"]) \
        + float(c["home_gb"])
    if mode == "container-agent":
        gb += float(c["agent_allowance_gb"])
    return int(gb * GIB)


def container_memory_max():
    """The container's memory.max in bytes; CapError when unset or unreadable."""
    path = CGROUP_DIR / "memory.max"
    try:
        text = path.read_text().strip()
    except OSError:
        raise CapError(f"{path} is not readable: not inside a memory-capped container, so a "
                       "container cap mode cannot run a solver") from None
    if text == "max":
        raise CapError(f"{path} is 'max': the container has no memory cap; refusing to run a "
                       "solver uncapped")
    try:
        return int(text)
    except ValueError:
        raise CapError(f"{path} holds {text!r}, not a byte count") from None


def oom_kills():
    """The cgroup's memory.events oom_kill count; CapError when unreadable."""
    path = CGROUP_DIR / "memory.events"
    try:
        for line in path.read_text().splitlines():
            k, _, v = line.partition(" ")
            if k == "oom_kill":
                return int(v)
    except (OSError, ValueError):
        pass
    raise CapError(f"{path} has no readable oom_kill count; a memory kill could not be told "
                   "from a crash, so no solver runs")


# The container watcher: the host's lifeline script (above). It was
# `kill -KILL -- "-$pgid"`, which dash (the image's /bin/sh, Ubuntu's) rejects
# as "Illegal number: -", so a container job outlived a killed parent; the
# POSIX `kill -s KILL -- -<pgid>` works in dash and bash alike (DELTAS Δ504).
_CONTAINER_LIFELINE_SH = _LIFELINE_SH


def _container_lifeline(pgid):
    r, w = os.pipe()
    try:
        subprocess.run(plat.detach_argv() + ["sh", "-c", _CONTAINER_LIFELINE_SH,
                                             f"dvl-lifeline-{pgid}", str(pgid)],
                       stdin=r, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       close_fds=True, check=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        os.close(w)
        raise CapError(f"cannot start the lifeline watcher of a capped job ({e})") from None
    finally:
        os.close(r)
    return w


def _run_in_container(argv, mem_gb, timeout_s, env, cwd, *, pool, out_dir, mode):
    """run_capped's container modes (see the comment above CAP_MODES)."""
    limit = container_bound_bytes(mode, mem_gb)
    have = container_memory_max()
    if have > limit:
        raise CapError(f"the container's memory.max is {have / GIB:.2f} GiB, above the "
                       f"{limit / GIB:.2f} GiB that {mode} allows for a {float(mem_gb):g} GB job "
                       "(scripts/dvl/pins.toml [container]); refusing to run")
    before = oom_kills()
    env = default_env() if env is None else dict(env)
    out = Path(out_dir) if out_dir else scratch_dir(f"job-{pool_of(argv)}")
    out.mkdir(parents=True, exist_ok=True)
    cwd = Path(cwd) if cwd else out
    stdout_path, stderr_path = out / "stdout.txt", out / "stderr.txt"
    (out / "cmd.txt").write_text(shlex.join(str(a) for a in argv) + "\n", encoding="utf-8")
    pool = pool or pool_of(argv)
    slot = _Slot("container-agent", 1) if mode == "container-agent" else _Slot(pool, jobs(pool))
    with slot:
        with open(stdout_path, "wb") as so, open(stderr_path, "wb") as se:
            started = time.monotonic()
            proc = subprocess.Popen([str(a) for a in argv], stdout=so, stderr=se,
                                    stdin=subprocess.DEVNULL, cwd=cwd, env=env,
                                    start_new_session=True)
            try:
                lifeline = _container_lifeline(proc.pid)
            except CapError:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
                proc.wait()
                raise
            finished = False
            try:
                try:
                    rc = proc.wait(timeout=timeout_s)
                    timed_out = False
                except subprocess.TimeoutExpired:
                    timed_out = True
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass
                    rc = proc.wait()
                elapsed = time.monotonic() - started
                finished = True
            finally:
                _cut_lifeline(lifeline, finished)
    if rc < 0:
        rc = 128 - rc
    if timed_out or (rc in KILLED_EXITS and elapsed >= float(timeout_s)):
        rc = WALL_CLOCK_EXIT
    elif oom_kills() > before:
        rc = 137                 # the container's OOM killer took a process of this job
    (out / "exit.txt").write_text(f"{rc}\n", encoding="utf-8")
    return rc, stdout_path, stderr_path


# --- learner regions of a reference twin (QPLAN §6 Q18) ----------------------------------------
#
# A reference twin marks the lines the learner writes for an annotation hole
# (invariants, frame clauses, assertions and lemma calls around given code) as
#     // @hole-begin <item id>          (`#` in Python)
#     …the learner's lines…
#     // @hole-end <item id>
# An item may own several regions (a loop's invariants plus a call in its
# body; a header's frame clauses plus a body assertion). Regions never nest
# and every begin has its end. The region mode of the empty-body gate verifies
# the twin with the item's regions blanked: the given code must not verify
# without the learner's lines.

HOLE_BEGIN = re.compile(r"^\s*(?://|#)\s*@hole-begin\s+(\S+)\s*$")
HOLE_END = re.compile(r"^\s*(?://|#)\s*@hole-end\s+(\S+)\s*$")


def hole_regions(text, item_id=None):
    """[(item id, begin line, end line)] of the region markers in `text`
    (1-based marker lines), in file order; only `item_id`'s when given.
    Raises ValueError on an unclosed, unopened, nested or mismatched marker
    anywhere in the text (a broken twin is never half-gated)."""
    out, open_ = [], None
    for ln, line in enumerate(text.split("\n"), 1):
        b, e = HOLE_BEGIN.match(line), HOLE_END.match(line)
        if b:
            if open_ is not None:
                raise ValueError(f"line {ln}: @hole-begin {b.group(1)} inside the open region "
                                 f"of {open_[0]} (line {open_[1]}): regions never nest")
            open_ = (b.group(1), ln)
        elif e:
            if open_ is None:
                raise ValueError(f"line {ln}: @hole-end {e.group(1)} without its @hole-begin")
            if e.group(1) != open_[0]:
                raise ValueError(f"line {ln}: @hole-end {e.group(1)} closes the region of "
                                 f"{open_[0]} (line {open_[1]})")
            out.append((open_[0], open_[1], ln))
            open_ = None
    if open_ is not None:
        raise ValueError(f"line {open_[1]}: @hole-begin {open_[0]} is never closed")
    return [r for r in out if item_id is None or r[0] == item_id]


def strip_regions(text, item_id):
    """`text` with the lines strictly inside each of `item_id`'s regions
    blanked (the marker lines and the line count stay, so locations still
    match the twin). ValueError as hole_regions; also when the item owns no
    region."""
    regions = hole_regions(text, item_id)
    if not regions:
        raise ValueError(f"{item_id}: no @hole-begin/@hole-end region")
    lines = text.split("\n")
    for _, b, e in regions:
        for k in range(b, e - 1):
            lines[k] = ""
    return "\n".join(lines)
