"""fvh.tools.runners — the instrument runners and the provenance rule (DV4-PLAN §3.7).

The public names are re-exported by `fvh.tools`; import them from there.

Instruments. INSTRUMENTS are the wrapper instruments of tests/corpus/README.md's
table, by the same names. fvh builds every argv itself from that table: a caller
names an instrument and a target, never an argv or an option.

  instrument          command (repo-relative, run from the course root)
  vcheck --gate       scripts/vcheck --gate <t>
  vaudit              scripts/vaudit <t>
  specfreeze --check  Dafny: scripts/specfreeze --against <dir>/frozen.dfy <t>
                      Verus: scripts/specfreeze --against <t>/frozen.rs <t>/src/lib.rs
  witness             Dafny: scripts/vcheck --gate <dir>/witness.dfy
                      Verus: scripts/vcheck --gate <t>/witness
  swap-to-false       Dafny: scripts/vcheck --gate <dir>/swap.dfy
                      Verus: scripts/vcheck --gate <t>/swapped
  seed-rerun          scripts/vcheck --brittleness <t>
  solver-swap         Dafny: scripts/vcheck --brittleness --solvers <t> (every seed under
                      each bundled Z3; Verus has one solver, so it has no solver-swap)
  reach               Dafny: scripts/dvl/reach.py --manifest <dir>/reach.toml <t>
                      Verus: scripts/dvl/reach.py --manifest <t>/reach.toml <t>
                      (the challenge tier's two instruments, QPLAN §31.4 item 5, Δ402)

<t> is the target (a .dfy file, or a Verus crate directory) and <dir> the Dafny
target's directory. `command()` returns these argvs; a runner adds `--json`
where the tool prints a JSON document (every instrument but specfreeze).
`command()` is public, and so is the companion layout it encodes (the README
documents it): a caller may compose it to see which companions an instrument
reads. Nothing here says whether a delivery holds them (`_input_paths`, the
recorder's existence check, stays private) or what a result means.

ToolResult(instrument, target, document, exit_code, killed, runner,
provenance, output_sha256), frozen and validated:
  document       the tool's own --json document (a dict), or, for a tool
                 without one, for output that is not one, and for every
                 killed run, {"exit_code": ..., "lines": [...]} from its
                 normalized text. Paths are redacted as scripts/pins.py
                 redacts them: the run's scratch directory and the rest of
                 the path after it to <scratch>, the course root to <root>,
                 $HOME to ~, any other absolute path to its last component.
  exit_code      the course tool's exit code; None when the runner killed it
  killed         None, "memory" (exit 137/143, or killed(memory) reported) or
                 "wall-clock" (the runner's time-out, exit 124, or the
                 tool's wall-clock safety kill reported, Δ58). A killed
                 result always carries the text form, never a document
                 that reads as a pass (Δ57, Δ58)
  runner         "host" | "container" | "replay"
  provenance     "course" | "learner" | "agent"
  output_sha256  sha256 (UTF-8) of the normalized output: stdout, then a line
                 `--- stderr ---` and stderr when stderr is not blank, paths
                 redacted as above, ANSI codes and trailing blanks removed,
                 the whole stripped and ended with one newline

The provenance rule. provenance_of(target) resolves the target's real path
(symbolic links followed) and gives it
  course   under tests/corpus/ or harness/tests/q/fixtures/, or a given layer
           or challenge statement the registry (MODULES.toml) declares;
  learner  any other path the registry declares: a module's exercises,
           exits, agentic and harness files and units, with the crate
           directory of each declared src/ file;
  agent    everything else: every path under research/, every path outside
           the course root (the sandbox's run directories among them), and
           any path the registry does not declare.
An `agent` target never runs on the host: HostRunner raises ProvenanceError
for one, and `fvh.tools.run` sends it to an isolated runner.

Runners: execute(instrument, target, *, timeout_s=None) -> ToolResult.
  HostRunner(root=None, *, preflight=True)   the course tool as a subprocess
      from the course root, under the tools' own caps, one solver job at a
      time (DVL_DAFNY_JOBS=1, DVL_VERUS_JOBS=1), in a scratch directory of
      its own outside the course tree, with a process-group kill at the
      time-out (default: 3 x the language's pinned wall clock + 600 s). The
      preflight refuses (PreflightError) unless MemAvailable holds the
      language's pinned cap plus 15 GB (CLAUDE.md §Resources). It refuses
      agent targets.
  ContainerRunner(root=None, *, module=None, mem_gb=None, keep=None,
                  lab_task=None, rev=None)   one
      verification container per call through scripts/mksandbox-run (live
      from DV4 step 2b; the class docstring). RunnerUnavailable with
      DVL_NO_DOCKER=1 and when the container cannot run; PreflightError when
      the run is deferred for memory. `lab_task` (a lab batch, Δ182): the
      gate runs as `vcheck --gate --lab-task <the task form> <t>`, the lab
      gate's lever check, with the task form staged read-only; `rev` (`fvh
      report --reverify`): every course file the container stages is read
      at that commit.
  ReplayRunner(fixtures_dir=None, *, root=None)   the recorded results under
      fixtures_dir (default harness/tests/q/fixtures/q09): no solver, no
      container. NoRecording when nothing was recorded for the call.

Recorded files: <fixtures_dir>/<lang>/<ID>/<slug(instrument)>.json, one JSON
object with exactly the keys schema (1), instrument, target, argv, exit_code,
killed (always null: a kill is never recorded), provenance, output_sha256 and
document. They hold instrument results only, never a fixture's label.

Frozen (guard rule 2f), standard library only.
"""

import dataclasses
import hashlib
import json
import os
import posixpath
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

__all__ = ["FIXTURES", "INSTRUMENTS", "KILLS", "NoRecording", "PROVENANCES", "PreflightError",
           "ProvenanceError", "RUNNERS", "ContainerRunner", "HostRunner", "ReplayRunner",
           "Runner", "RunnerUnavailable", "ToolResult", "command", "provenance_of",
           "read_recording", "recording_path", "slug", "write_recording"]

ROOT = Path(__file__).resolve().parents[3]

CORE_INSTRUMENTS = ("vcheck --gate", "vaudit", "specfreeze --check", "witness", "swap-to-false",
                    "seed-rerun")
CHALLENGE_INSTRUMENTS = ("solver-swap", "reach")     # recorded only when named (Δ402)
INSTRUMENTS = CORE_INSTRUMENTS + CHALLENGE_INSTRUMENTS
PROVENANCES = ("course", "learner", "agent")          # in order of rising distrust
KILLS = ("memory", "wall-clock")
RUNNERS = ("host", "container", "replay")
FIXTURES = "harness/tests/q/fixtures/q09"             # the recorded-fixture layout
LAB_TASK_DIR = "lab-task"                             # where a lab run stages its task form
LANGS = ("dafny", "verus")
SCHEMA = 1

_RANK = {p: i for i, p in enumerate(PROVENANCES)}
_JSON = {"vcheck --gate": True, "vaudit": True, "specfreeze --check": False, "witness": True,
         "swap-to-false": True, "seed-rerun": True, "solver-swap": True, "reach": True}
COURSE_TREES = ("tests/corpus", "harness/tests/q/fixtures", "harness/tests/challenges")  # Δ406
AGENT_TREES = ("research",)
GIVEN_TREES = ("dafny/given", "verus/given")
LEARNER_KEYS = ("exercises", "exits", "agentic", "harness", "units")
RESERVE_GB = 15                       # CLAUDE.md §Resources: the free-memory reserve
KILLED_EXITS = (137, 143)             # SIGKILL / SIGTERM: a memory kill, never a verdict
WALL_CLOCK_EXIT = 124                 # dvl's wall-clock safety kill (Δ58)
_WALL_TEXT = re.compile(r"wall-clock safety (?:kill|net)")
_SHA = re.compile(r"[0-9a-f]{64}")
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_ABS = re.compile(r"(?<![\w.<>~])/(?:[\w.+@-]+/)+([\w.+@-]+)")     # scripts/pins.py's
_PY_DEFAULTS = {"mem_gb": 4, "wall_clock_s": 600}                  # dvl.python's
_REC_KEYS = frozenset({"schema", "instrument", "target", "argv", "exit_code", "killed",
                       "provenance", "output_sha256", "document"})


class ProvenanceError(RuntimeError):
    """An agent target sent to a runner that runs on the host, or a lowered provenance."""


class RunnerUnavailable(RuntimeError):
    """The runner cannot run this call (no Docker here, or the container could not run)."""


class PreflightError(RuntimeError):
    """The host cannot start the job now (memory), or its caps cannot be read."""


class NoRecording(LookupError):
    """No recorded result for this instrument and target (or fixture)."""


# =====================================================================================
# Instruments and their commands
# =====================================================================================

def _check_instrument(instrument):
    if instrument not in INSTRUMENTS:
        raise ValueError(f"{instrument!r} is not an instrument fvh.tools runs "
                         f"({', '.join(INSTRUMENTS)})")


def slug(instrument: str) -> str:
    """The instrument's name in a file-safe spelling (`vcheck --gate` -> `vcheck-gate`)."""
    _check_instrument(instrument)
    return re.sub(r"[^a-z0-9]+", "-", instrument).strip("-")


def lang_of(target) -> str:
    """"dafny" for a .dfy file (or specimen), "python" for a .py file, else "verus"."""
    name = str(target).rstrip("/").lower()
    if name.endswith((".dfy", ".dfy.specimen")):
        return "dafny"
    if name.endswith(".py"):
        return "python"
    return "verus"


def command(instrument: str, target, *, lang: str | None = None) -> list[str]:
    """The instrument's command as tests/corpus/README.md writes it (no --json):
    repo-relative, to run from the course root on `target` as given."""
    _check_instrument(instrument)
    t = str(target).rstrip("/") or "."
    lang = lang or lang_of(t)
    if instrument == "vcheck --gate":
        return ["scripts/vcheck", "--gate", t]
    if instrument == "vaudit":
        return ["scripts/vaudit", t]
    if instrument == "seed-rerun":
        return ["scripts/vcheck", "--brittleness", t]
    if instrument == "solver-swap":
        if lang != "dafny":
            raise ValueError("solver-swap is Dafny's: Verus has one solver (VERSIONS.md §1.2)")
        return ["scripts/vcheck", "--brittleness", "--solvers", t]
    if instrument == "reach":
        if lang == "dafny":
            d = posixpath.dirname(t)
            return ["scripts/dvl/reach.py", "--manifest",
                    posixpath.join(d, "reach.toml") if d else "reach.toml", t]
        if lang == "verus" and not t.endswith(".rs"):
            return ["scripts/dvl/reach.py", "--manifest", f"{t}/reach.toml", t]
    if lang == "dafny":
        d = posixpath.dirname(t)

        def at(name):
            return posixpath.join(d, name) if d else name
        if instrument == "witness":
            return ["scripts/vcheck", "--gate", at("witness.dfy")]
        if instrument == "swap-to-false":
            return ["scripts/vcheck", "--gate", at("swap.dfy")]
        return ["scripts/specfreeze", "--against", at("frozen.dfy"), t]
    if lang == "verus" and not t.endswith(".rs"):
        if instrument == "witness":
            return ["scripts/vcheck", "--gate", f"{t}/witness"]
        if instrument == "swap-to-false":
            return ["scripts/vcheck", "--gate", f"{t}/swapped"]
        return ["scripts/specfreeze", "--against", f"{t}/frozen.rs", f"{t}/src/lib.rs"]
    raise ValueError(f"{instrument} needs a Dafny file or a Verus crate directory, not {t!r}")


def _input_paths(instrument: str, target, *, lang: str | None = None) -> list[str]:
    """Every path the instrument's command names (the target and its companions);
    the recorder's check that an instrument's inputs exist."""
    return [a for a in command(instrument, target, lang=lang)[1:] if not a.startswith("--")]


# =====================================================================================
# The provenance rule
# =====================================================================================

def _root(root):
    return Path(os.path.realpath(root if root is not None else ROOT))


def _real(target, root):
    p = Path(target)
    if not p.is_absolute():
        p = root / p
    return Path(os.path.realpath(p))


def _shown(real, root):
    """The repo-relative POSIX path of a real path inside the root, else the path."""
    try:
        rel = real.relative_to(root).as_posix()
    except ValueError:
        return str(real)
    return rel


def _under(rel, prefixes):
    return any(rel == p or rel.startswith(p + "/") for p in prefixes)


def _clean(p):
    """A registry path as a repo-relative POSIX prefix, or None when it is not one."""
    if not isinstance(p, str):
        return None
    s = posixpath.normpath(p.strip().rstrip("/")) if p.strip() else ""
    if not s or s == "." or s.startswith("/") or ".." in s.split("/"):
        return None
    return s


def _declared(root):
    """(course prefixes, learner prefixes) from the registry; empty when it cannot be read."""
    try:
        data = tomllib.loads((root / "MODULES.toml").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return (), ()
    course, learner = set(), set()
    mods = data.get("module")
    for m in mods if isinstance(mods, list) else []:
        if not isinstance(m, dict):
            continue
        for key in LEARNER_KEYS:
            vals = m.get(key)
            for p in vals if isinstance(vals, list) else []:
                if (c := _clean(p)) is not None:
                    learner.add(c)
        imports = m.get("imports")
        for p in imports if isinstance(imports, dict) else {}:
            if (c := _clean(p)) is not None:
                (course if _under(c, GIVEN_TREES) else learner).add(c)
        stmts = m.get("statements")
        for s in stmts if isinstance(stmts, list) else []:
            if isinstance(s, dict) and (c := _clean(s.get("path"))) is not None:
                course.add(c)
    for group in (course, learner):
        for p in list(group):
            if "/src/" in p:
                group.add(p.split("/src/", 1)[0])
    return tuple(sorted(course)), tuple(sorted(learner))


def provenance_of(target, *, root=None) -> str:
    """"course", "learner" or "agent" for a target (relative paths are taken
    from the course root); see the module docstring."""
    root = _root(root)
    real = _real(target, root)
    rel = _shown(real, root)
    if rel == str(real) or rel == ".":
        return "agent"
    if _under(rel, AGENT_TREES):
        return "agent"
    if _under(rel, COURSE_TREES):
        return "course"
    course, learner = _declared(root)
    if _under(rel, course):
        return "course"
    if _under(rel, learner):
        return "learner"
    return "agent"


def raise_provenance(computed: str, requested: str | None) -> str:
    """The provenance a call runs under: `requested` may raise `computed`
    toward agent, never lower it."""
    if requested is None:
        return computed
    if requested not in PROVENANCES:
        raise ValueError(f"provenance must be one of {', '.join(PROVENANCES)}")
    if _RANK[requested] < _RANK[computed]:
        raise ProvenanceError(f"a provenance is raised, never lowered: the target is "
                              f"{computed!r}, the call asked for {requested!r}")
    return requested


def higher(a: str, b: str) -> str:
    return a if _RANK[a] >= _RANK[b] else b


# =====================================================================================
# ToolResult
# =====================================================================================

@dataclass(frozen=True)
class ToolResult:
    """One instrument run on one target (module docstring). Treat `document` as read-only."""

    instrument: str
    target: str
    document: dict
    exit_code: int | None
    killed: str | None
    runner: str
    provenance: str
    output_sha256: str

    def __post_init__(self):
        _check_instrument(self.instrument)
        if not isinstance(self.target, str) or not self.target:
            raise ValueError("ToolResult.target must be a non-empty string")
        if not isinstance(self.document, dict):
            raise TypeError("ToolResult.document must be a dict")
        try:
            json.dumps(self.document)
        except (TypeError, ValueError) as e:
            raise ValueError(f"ToolResult.document must be JSON data ({e})") from None
        if self.exit_code is not None and (isinstance(self.exit_code, bool) or
                                           not isinstance(self.exit_code, int)):
            raise TypeError("ToolResult.exit_code must be an int or None")
        if self.killed not in (None, *KILLS):
            raise ValueError(f"ToolResult.killed must be None or one of {', '.join(KILLS)}")
        if self.runner not in RUNNERS:
            raise ValueError(f"ToolResult.runner must be one of {', '.join(RUNNERS)}")
        if self.provenance not in PROVENANCES:
            raise ValueError(f"ToolResult.provenance must be one of {', '.join(PROVENANCES)}")
        if not isinstance(self.output_sha256, str) or not _SHA.fullmatch(self.output_sha256):
            raise ValueError("ToolResult.output_sha256 must be 64 lower-case hex digits")
        if self.exit_code is None and self.killed is None:
            raise ValueError("a ToolResult without an exit code is a killed run")
        if self.killed is not None:
            if self.exit_code == 0:
                raise ValueError("a killed run never carries exit 0")
            if set(self.document) != {"exit_code", "lines"}:
                raise ValueError("a killed run carries the text form {exit_code, lines}, "
                                 "never a tool document")

    def __hash__(self):          # the document is a dict: hash the rest (equal results agree)
        return hash((self.instrument, self.target, self.exit_code, self.killed, self.runner,
                     self.provenance, self.output_sha256))

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


# =====================================================================================
# Normalization
# =====================================================================================

def _redactor(root, scratch):
    root_s = str(root)
    home = os.environ.get("HOME", "")
    scr = re.compile(re.escape(str(scratch)) + r"[^\s\"',:;)\]}]*") if scratch else None

    def red(text):
        text = _ANSI.sub("", text)
        if scr is not None:
            text = scr.sub("<scratch>", text)
        text = text.replace(root_s, "<root>")
        if len(home) > 1:
            text = text.replace(home, "~")
        return _ABS.sub(lambda m: m.group(1), text)
    return red


def _redact_json(value, red):
    if isinstance(value, str):
        return red(value)
    if isinstance(value, list):
        return [_redact_json(v, red) for v in value]
    if isinstance(value, dict):
        return {red(k) if isinstance(k, str) else k: _redact_json(v, red)
                for k, v in value.items()}
    return value


def normalize(out: str, err: str, red) -> str:
    """The normalized output text (module docstring: output_sha256)."""
    s = out + (("\n--- stderr ---\n" + err) if err.strip() else "")
    s = red(s)
    return "\n".join(line.rstrip() for line in s.splitlines()).strip() + "\n"


def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _kill_of(rc, raw, doc):
    """'memory', 'wall-clock' or None, from the exit code and what the tool reported."""
    if rc in KILLED_EXITS or "killed(memory)" in raw:
        return "memory"
    if isinstance(doc, dict) and doc.get("exit_code") in KILLED_EXITS:
        return "memory"
    if rc == WALL_CLOCK_EXIT or _WALL_TEXT.search(raw):
        return "wall-clock"
    if isinstance(doc, dict) and doc.get("exit_code") == WALL_CLOCK_EXIT:
        return "wall-clock"
    return None


def make_result(instrument, target, provenance, runner, rc, out, err, timed_out, red,
                want_json) -> ToolResult:
    """A ToolResult from one finished (or killed) tool process."""
    text = normalize(out, err, red)
    lines = text.strip("\n").splitlines() if text.strip() else []
    parsed = None
    if want_json and not timed_out:
        try:
            parsed = json.loads(out)
        except ValueError:
            parsed = None
        if not isinstance(parsed, dict):
            parsed = None
    killed = "wall-clock" if timed_out else _kill_of(rc, out + err, parsed)
    if timed_out:
        rc = None
    if killed is not None or parsed is None:
        doc = {"exit_code": rc, "lines": lines}
    else:
        doc = _redact_json(parsed, red)
    return ToolResult(instrument, target, doc, rc, killed, runner, provenance, _sha256(text))


# =====================================================================================
# Runners
# =====================================================================================

class Runner:
    """The runner interface: execute(instrument, target, *, timeout_s=None) -> ToolResult.
    `isolated` is True only for a runner that runs nothing on the host (a
    container, a replay); only those may take an agent target."""

    name = ""
    isolated = False

    def execute(self, instrument, target, *, timeout_s=None) -> ToolResult:
        raise NotImplementedError


def _pins(root):
    try:
        return tomllib.loads((root / "scripts" / "dvl" / "pins.toml").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None


def _pin(root, lang, key):
    pins = _pins(root)
    if pins is None:
        return None
    table = pins.get(lang) if isinstance(pins.get(lang), dict) else {}
    value = table.get(key, _PY_DEFAULTS.get(key) if lang == "python" else None)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def mem_available_gb():
    if sys.platform == "darwin":            # as scripts/dvl/platform.py: no /proc there
        return _darwin_available_gb()
    try:
        with open("/proc/meminfo", encoding="ascii") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1048576
    except (OSError, ValueError, IndexError):
        pass
    return None


def _darwin_available_gb():
    """free + inactive + speculative + purgeable pages of vm_stat, in whole GiB."""
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
        m = re.search(r"page size of (\d+) bytes", out)
        page = int(m.group(1)) if m else 16384
        n = 0
        for line in out.splitlines():
            k, _, v = line.partition(":")
            if k.strip() in ("Pages free", "Pages inactive", "Pages speculative", "Pages purgeable"):
                n += int(v.strip().rstrip("."))
        return n * page // (1 << 30)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def preflight(root, lang):
    """Refuse (PreflightError) unless MemAvailable holds the language's cap + 15 GB."""
    cap = _pin(_root(root), lang, "mem_gb")
    if cap is None:
        raise PreflightError(f"the {lang} memory cap cannot be read from scripts/dvl/pins.toml; "
                             "no job was started")
    need, have = cap + RESERVE_GB, mem_available_gb()
    if have is None or have < need:
        raise PreflightError(f"{have if have is not None else 'unknown'} GB available, {need} GB "
                             f"needed (the {lang} cap plus the {RESERVE_GB} GB reserve, "
                             "CLAUDE.md §Resources); no job was started")


def default_timeout(root, lang):
    wall = _pin(_root(root), lang, "wall_clock_s") or 1800
    return 3 * wall + 600


def _scratch_base(root):
    base = Path(os.environ.get("DVL_SCRATCH") or f"/tmp/dvl-{os.getuid()}").absolute()
    if Path(os.path.realpath(base)).is_relative_to(root):
        raise ValueError(f"DVL_SCRATCH {base} lies inside the course tree; scratch never does")
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    return base


def _tool_env(scratch):
    env = dict(os.environ)
    env.pop("CI", None)                  # an instrument never takes an author path
    env.update(DVL_SCRATCH=str(scratch), DVL_DAFNY_JOBS="1", DVL_VERUS_JOBS="1",
               PYTHONDONTWRITEBYTECODE="1")
    return env


def _killpg(pid, sig):
    try:
        os.killpg(pid, sig)
    except (ProcessLookupError, PermissionError):
        pass


def _spawn(argv, cwd, env, timeout_s):
    """(exit code, stdout, stderr, timed out). The process leads its own group,
    and the whole group is killed at the time-out."""
    p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         encoding="utf-8", errors="replace", start_new_session=True)
    try:
        out, err = p.communicate(timeout=timeout_s)
        return p.returncode, out, err, False
    except subprocess.TimeoutExpired:
        _killpg(p.pid, signal.SIGTERM)
        try:
            out, err = p.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            _killpg(p.pid, signal.SIGKILL)
            out, err = p.communicate()
        _killpg(p.pid, signal.SIGKILL)
        return None, out or "", err or "", True
    except BaseException:
        _killpg(p.pid, signal.SIGKILL)
        p.wait()
        raise


class HostRunner(Runner):
    """The course tool as a subprocess from the course root (module docstring)."""

    name = "host"
    isolated = False

    def __init__(self, root=None, *, preflight: bool = True):
        self.root = _root(root)
        self.preflight = preflight

    def argv(self, instrument, target) -> list[str]:
        """The repo-relative argv this runner runs (the command plus --json where
        the tool prints a JSON document)."""
        rel = _shown(_real(target, self.root), self.root)
        cmd = command(instrument, rel)
        if _JSON[instrument]:
            cmd.insert(1, "--json")
        return cmd

    def execute(self, instrument, target, *, timeout_s=None) -> ToolResult:
        _check_instrument(instrument)
        real = _real(target, self.root)
        prov = provenance_of(real, root=self.root)
        if prov == "agent":
            raise ProvenanceError(f"{target}: a target of agent provenance never runs on the "
                                  "host; it runs in the verification container")
        shown = _shown(real, self.root)
        lang = lang_of(shown)
        argv = self.argv(instrument, shown)
        if self.preflight:
            preflight(self.root, lang)
        limit = timeout_s if timeout_s is not None else default_timeout(self.root, lang)
        scratch = Path(tempfile.mkdtemp(prefix="fvh-tool-", dir=_scratch_base(self.root)))
        try:
            rc, out, err, timed_out = _spawn(
                [sys.executable, "-B", str(self.root / argv[0]), *argv[1:]], self.root,
                _tool_env(scratch), limit)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        return make_result(instrument, shown, prov, self.name, rc, out, err, timed_out,
                           _redactor(self.root, scratch), _JSON[instrument])


class ContainerRunner(Runner):
    """One verification container per call, through scripts/mksandbox-run (DV4-PLAN
    §5.9; live from DV4 step 2b).

    execute(instrument, target): the target is a course path, or a copy outside
    the course root or under research/ (the executor's work copy, a returned
    file), whose course path is the longest suffix of it that the registry
    declares (or a benchmark task: `bench/public/<set>/tasks/…`,
    `bench/local/<q|r>/<lab>/tasks/…` or a lab card's
    `bench/local/<q|r>/<lab>/<card>/tasks/…`, or a crate card's `…/tasks` directory
    itself; mksandbox-run takes a local
    card's module from its stratum's STRATUM.toml when none is named). `mksandbox-run --build-verify` writes the verify manifest: the
    instrument's command (as HostRunner runs it, with --json where the tool
    prints a document), every regular file under the copy's base inline as an
    editable input over the course's own files of the target's unit, and the
    module's given chain, project files, trusted tools and pins read-only. The
    run (`mksandbox-run --records`) has no network and its own memory cap; its
    run.json holds the command's exit code and output, which become the
    ToolResult as on the host, with the container's root (/work) and scratch
    redacted to <root> and <scratch>.

    Refuses (RunnerUnavailable) with DVL_NO_DOCKER=1 (CI), when no verify
    manifest can be built, and when the container run fails or is refused;
    a deferred run (memory short) is PreflightError. A container killed for
    memory is killed "memory", its wall clock "wall-clock" (Δ57, Δ58).

    With `lab_task` (the task form's course path), the "vcheck --gate"
    instrument runs the lab gate: `scripts/vcheck --gate --json --lab-task
    lab-task/<task> <t>` (QPLAN §30 Q63, Δ182): every lever the delivery adds
    to or drops from its task form is a finding and turns `verified` into
    `failed`; mksandbox-run stages the task form read-only at
    `lab-task/<task>` (LAB_TASK_DIR). The result keeps the instrument's name,
    so a recorded run replays as before. With `rev`, mksandbox-run reads
    every course file it stages (the trusted tools, the given chain, the
    project files, the pins, the task form) at that commit (`git show`), as
    `fvh report --reverify` needs (DV4-PLAN §3.6)."""

    name = "container"
    isolated = True

    def __init__(self, root=None, *, module=None, mem_gb=None, keep=None, mksandbox=None,
                 lab_task=None, lab_code="preserve", rev=None):
        self.root = _root(root)
        self.module = module
        self.mem_gb = mem_gb
        self.keep = Path(keep) if keep is not None else None
        self.mksandbox = Path(mksandbox) if mksandbox else self.root / "scripts" / "mksandbox-run"
        self.last_records = None
        if lab_task is not None and (not isinstance(lab_task, str) or lab_task.startswith("/")
                                     or ".." in lab_task.split("/")):
            raise ValueError("lab_task is the task form's course-relative path")
        if rev is not None and not re.fullmatch(r"[0-9A-Za-z._/~^-]{1,80}", str(rev)):
            raise ValueError(f"rev {rev!r} is not a revision name")
        if lab_code not in ("preserve", "own"):
            raise ValueError("lab_code is preserve or own")
        self.lab_task = lab_task
        self.lab_code = lab_code
        self.rev = rev

    def course_rel(self, target) -> str:
        """The target's course path (see the class docstring)."""
        real = Path(os.path.abspath(target if Path(target).is_absolute() else self.root / target))
        rel = _shown(real, self.root)
        if rel != str(real) and not _under(rel, AGENT_TREES):
            return rel
        course, learner = _declared(self.root)
        parts = real.parts
        for i in range(1, len(parts)):
            cand = "/".join(parts[i:])
            if _under(cand, course) or _under(cand, learner) or \
                    re.match(r"^bench/(public/[^/]+|local/[qr]/[^/]+(/[^/]+)?)/tasks(/|$)", cand):
                return cand
        raise RunnerUnavailable(f"{target}: no suffix of the path is a course file the registry "
                                "declares, so no verification container can be built for it")

    def argv(self, instrument, rel) -> list[str]:
        cmd = command(instrument, rel)
        if _JSON[instrument]:
            cmd.insert(1, "--json")
        if self.lab_task is not None and instrument == "vcheck --gate":
            cmd[-1:-1] = ["--lab-task", f"{LAB_TASK_DIR}/{self.lab_task}"]
            if self.lab_code == "own":
                cmd[-1:-1] = ["--lab-code", "own"]
        return cmd

    def _mk(self, args, timeout):
        return subprocess.run([sys.executable, "-B", str(self.mksandbox), *args], cwd=self.root,
                              stdin=subprocess.DEVNULL, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)

    def execute(self, instrument, target, *, timeout_s=None) -> ToolResult:
        _check_instrument(instrument)
        if os.environ.get("DVL_NO_DOCKER") == "1":
            raise RunnerUnavailable("DVL_NO_DOCKER=1 is set (the CI environment): no "
                                    "verification container runs here")
        rel = self.course_rel(target)
        lang = lang_of(rel)
        argv = self.argv(instrument, rel)
        work = Path(tempfile.mkdtemp(prefix="fvh-container-", dir=_scratch_base(self.root)))
        try:
            build = ["--build-verify", "--target", str(target), "--argv", json.dumps(argv)]
            if self.module:
                build += ["--module", self.module]
            if self.mem_gb is not None:
                build += ["--mem-gb", f"{float(self.mem_gb):g}"]
            if self.lab_task is not None and instrument == "vcheck --gate":
                build += ["--lab-task", self.lab_task]
            if self.rev is not None:
                build += ["--rev", str(self.rev)]
            p = self._mk(build, 300)
            if p.returncode != 0:
                why = [x for x in p.stderr.strip().splitlines() if "build-verify:" in x]
                raise RunnerUnavailable(f"{target}: no verify manifest ("
                                        + "; ".join(why or p.stderr.strip().splitlines()[-1:] or ["?"])
                                        + ")")
            built = json.loads(p.stdout)
            if built.get("target") != rel:
                raise RunnerUnavailable(f"{target}: mksandbox-run reads its course path as "
                                        f"{built.get('target')!r}, fvh as {rel!r}")
            man = work / "manifest.json"
            man.write_text(json.dumps(built["manifest"]), encoding="utf-8")
            recs = work / "records"
            limit = (timeout_s if timeout_s is not None else default_timeout(self.root, lang)) + 300
            try:
                p = self._mk(["--records", str(recs), str(man)], limit)
            except subprocess.TimeoutExpired:
                raise RunnerUnavailable(f"{target}: mksandbox-run did not return within "
                                        f"{limit:g} s") from None
            if p.returncode == 3 and "deferred" in p.stderr:
                raise PreflightError((p.stderr.strip().splitlines() or ["deferred"])[-1])
            run_json = recs / "run.json"
            if p.returncode not in (0, 1, 124) or not run_json.is_file():
                raise RunnerUnavailable(f"{target}: the verification container did not run "
                                        f"(exit {p.returncode}: "
                                        f"{(p.stderr.strip().splitlines() or ['?'])[-1]})")
            rec = json.loads(run_json.read_text(encoding="utf-8"))
            cmds = rec.get("commands") or []
            ended = rec.get("ended_by")
            if not cmds or (p.returncode == 1 and ended != "killed(memory)"):
                raise RunnerUnavailable(f"{target}: the verification container ended with "
                                        f"{ended!r} before its command finished")
            c = cmds[0]
            timed_out = c.get("killed") == "wall-clock" or p.returncode == 124
            rc = c.get("exit_code")
            if ended == "killed(memory)" or c.get("killed") == "memory":
                rc, timed_out = 137, False
            red = _redactor(Path(rec.get("root") or "/work"), rec.get("scratch"))
            prov = provenance_of(target, root=self.root)
            res = make_result(instrument, rel, prov, self.name, rc, c.get("stdout") or "",
                              c.get("stderr") or "", timed_out, red, _JSON[instrument])
            if self.keep is not None:
                dest = self.keep / f"{len(list(self.keep.glob('*')))+1:04d}-{slug(instrument)}"
                shutil.copytree(recs, dest)
                self.last_records = dest
            return res
        finally:
            shutil.rmtree(work, ignore_errors=True)


# =====================================================================================
# Recorded results and the replay runner
# =====================================================================================

def recording_path(fixtures_dir, lang: str, fixture_id: str, instrument: str) -> Path:
    if lang not in LANGS:
        raise ValueError(f"lang must be one of {', '.join(LANGS)}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", fixture_id or ""):
        raise ValueError(f"{fixture_id!r} is not a fixture id")
    return Path(fixtures_dir) / lang / fixture_id / f"{slug(instrument)}.json"


def write_recording(path, result: ToolResult, argv) -> None:
    """Write one recorded result (results only; a kill is never recorded)."""
    if result.killed is not None or result.exit_code is None:
        raise ValueError(f"{result.instrument} on {result.target}: a killed run is never recorded")
    if Path(path).name != f"{slug(result.instrument)}.json":
        raise ValueError(f"{path}: the file name must be {slug(result.instrument)}.json")
    if not isinstance(argv, list) or not all(isinstance(a, str) for a in argv):
        raise TypeError("argv must be a list of strings")
    rec = {"schema": SCHEMA, "instrument": result.instrument, "target": result.target,
           "argv": argv, "exit_code": result.exit_code, "killed": None,
           "provenance": result.provenance, "output_sha256": result.output_sha256,
           "document": result.document}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    os.replace(tmp, p)


def read_recording(path) -> ToolResult:
    """One recorded result, as a ToolResult with runner "replay"."""
    p = Path(path)
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as e:
        raise ValueError(f"{p}: unreadable recording ({type(e).__name__})") from None
    if not isinstance(rec, dict) or set(rec) != _REC_KEYS:
        raise ValueError(f"{p}: a recording holds exactly the keys {', '.join(sorted(_REC_KEYS))}")
    if rec["schema"] != SCHEMA:
        raise ValueError(f"{p}: schema {rec['schema']!r} is not {SCHEMA}")
    if rec["instrument"] not in INSTRUMENTS or p.name != f"{slug(rec['instrument'])}.json":
        raise ValueError(f"{p}: the instrument does not match the file name")
    if rec["killed"] is not None:
        raise ValueError(f"{p}: a killed run is never recorded")
    return ToolResult(rec["instrument"], rec["target"], rec["document"], rec["exit_code"], None,
                      "replay", rec["provenance"], rec["output_sha256"])


class ReplayRunner(Runner):
    """The recorded results under fixtures_dir; no solver and no container."""

    name = "replay"
    isolated = True

    def __init__(self, fixtures_dir=None, *, root=None):
        self.root = _root(root)
        self.dir = Path(fixtures_dir) if fixtures_dir is not None else self.root / FIXTURES
        self._index = None

    def _load(self):
        idx = {}
        for f in sorted(self.dir.glob("*/*/*.json")):
            r = read_recording(f)
            key = (r.instrument, r.target)
            if key in idx:
                raise ValueError(f"{f}: a second recording of {r.instrument} on {r.target}")
            idx[key] = r
        self._index = idx
        return idx

    def execute(self, instrument, target, *, timeout_s=None) -> ToolResult:
        _check_instrument(instrument)
        idx = self._index if self._index is not None else self._load()
        t = str(target)
        if Path(t).is_absolute():
            t = _shown(_real(t, self.root), self.root)
        try:
            return idx[(instrument, t)]
        except KeyError:
            raise NoRecording(f"no recorded result of {instrument} on {t} under "
                              f"{self.dir}") from None
