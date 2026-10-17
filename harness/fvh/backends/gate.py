"""fvh.backends.gate — the host-side model gate of a policy run, and the GPU
calendar lock (DV4-PLAN §5.6.3, §10; Δ146, Δ202).

Every Qwen request of every mode passes a gate (sandbox/hostside/
ollama_gate.py). A policy run on the host (fvh.batch, policy mode through the
opencode CLI, D3) gets its own gate on an ephemeral loopback port:

  HostGate(run_dir, config, *, root=None, upstream=None)
      start()          the gate process, its log and running counts in the
                       run directory (gate.log, gate-counts.json), its owner
                       this process (--owner-pid: a killed runner leaves no
                       gate); returns the gate's base URL
      counts()         the gate's running totals (calls, tokens, GPU-seconds,
                       admitted, capped, overrides, ctx_saturated, ...)
      stop()           SIGTERM, wait; the gate unloads the model when its
                       config says so (the batch's last run)
  gate_config(app, *, seeds, calls, gpu_s=None, unload=False) -> dict
      the run's config from the apparatus file's [model_server] and
      [backend.qwen] pins: the pinned tag and its digest (checked against
      /api/tags before the gate listens), the pinned request options, the
      run's per-request seeds (the gate sets seed n on the n-th request, so
      a lab's repeats are independent samples), the caps (calls, and the
      GPU-seconds when given), and keep_alive 0 at stop when `unload`
  server_facts(app, *, upstream=None) -> dict
                       the live model server's facts (DV4-PLAN §3.6, DV5c fix
                       round): reachable, its version (/api/version), the
                       pinned tags' digests (/api/tags) and the unit's
                       environment for the pinned keys (`systemctl show
                       ollama -p Environment`); read only, no inference
  server_drift(app, facts) -> list[apparatus.Drift]
                       the differences from the apparatus file's
                       [model_server] version, models and unit pins (an
                       unreachable server is one); fvh.batch refuses a Qwen
                       batch on any before its first attempt, and
                       `fvh apparatus --check` lists them
  GpuCalendar()        the per-user calendar lock ($XDG_RUNTIME_DIR/
                       dvl-gpu-calendar.lock, the one the sandbox's agent runs
                       take): a non-blocking flock held for a whole Qwen batch;
                       held by another batch -> Deferred (exit 3)

The gate's upstream is the apparatus file's model server on loopback (Δ146);
the transports never name it. With FVH_NO_MODEL=1 no gate starts (CI).
Frozen (guard rule 2f), standard library only. This directory is on
scripts/check_single_route.py's allowlist.
"""

import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from fvh import apparatus, budget
from fvh.backends import Deferred, refuse_if_disabled

__all__ = ["CALENDAR_LOCK", "GateError", "GpuCalendar", "HostGate", "UPSTREAM", "gate_config",
           "server_drift", "server_facts"]

ROOT = Path(__file__).resolve().parents[3]
GATE_SCRIPT = "sandbox/hostside/ollama_gate.py"
UPSTREAM = "http://127.0.0.1:11434"         # Ollama listens on loopback only (Δ146)
CALENDAR_LOCK = "dvl-gpu-calendar.lock"     # DV4-PLAN §10, as dvl.sandbox's GPU_LOCK
START_TIMEOUT_S = 20


class GateError(RuntimeError):
    """The gate did not start (or its config cannot be built): no model call is made."""


def gate_config(app, *, seeds, calls, gpu_s=None, unload=False) -> dict:
    """The run's gate config (module docstring)."""
    table = app.backend(budget.QWEN)
    ms = app.model_server()
    tag = table.get("model")
    models = ms.get("models") if isinstance(ms.get("models"), dict) else {}
    digest = models.get(tag)
    if not isinstance(tag, str) or not isinstance(digest, str) or \
            not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise GateError(f"the model {tag!r} has no digest pin in the apparatus file's "
                        "[model_server] models")
    opts = ms.get("options")
    if not isinstance(opts, dict) or not opts:
        raise GateError("the apparatus file's [model_server] options are missing")
    seeds = [int(s) for s in seeds]
    if not seeds or any(s < 0 for s in seeds):
        raise GateError("a run's gate takes its per-request seeds (one per call)")
    caps = {"calls": int(calls)}
    if gpu_s is not None:
        caps["gpu_s"] = float(gpu_s)
    return {"model": tag, "digest": digest, "options": dict(opts), "caps": caps,
            "margin": int(ms.get("margin", 512)), "seeds": seeds,
            "unload_on_stop": bool(unload)}


def _get_json(url, timeout):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:    # loopback only (Δ146)
            return json.loads(r.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return None


def _unit_environment(unit="ollama", runner=subprocess.run):
    """{KEY: value} of a systemd unit's Environment (the system unit, else the user
    unit), or None when neither can be read."""
    for scope in ([], ["--user"]):
        try:
            p = runner(["systemctl", *scope, "show", unit, "-p", "Environment", "--value"],
                       capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if p.returncode == 0 and p.stdout.strip():
            out = {}
            for tok in p.stdout.split():
                k, eq, v = tok.partition("=")
                if eq:
                    out[k] = v
            return out
    return None


def server_facts(app, *, upstream=None, timeout=5.0, unit_env=None) -> dict:
    """The live model server's facts (module docstring). unit_env: a callable
    returning the unit's environment (tests), else systemctl."""
    refuse_if_disabled()
    base = upstream or UPSTREAM
    if not re.fullmatch(r"http://127\.0\.0\.1:\d{1,5}", base):
        raise GateError(f"the model server must be a loopback http address, not {base!r}")
    ver = _get_json(base + "/api/version", timeout)
    tags = _get_json(base + "/api/tags", timeout)
    digests = {}
    pinned = (app.model_server().get("models") or {})
    for tag in pinned:
        got = None
        for m in (tags or {}).get("models", []) if isinstance(tags, dict) else []:
            if isinstance(m, dict) and m.get("name") == tag:
                got = m.get("digest")
        digests[tag] = got
    env = unit_env() if unit_env is not None else _unit_environment()
    keys = (app.model_server().get("unit") or {})
    return {"reachable": isinstance(ver, dict),
            "version": ver.get("version") if isinstance(ver, dict) else None,
            "models": digests,
            "unit": None if env is None else {k: env.get(k) for k in keys}}


def server_drift(app, facts) -> list:
    """The differences between the live server's facts and the pins (module docstring)."""
    ms = app.model_server()
    out = []
    why = ("the model server changed (an auto-update, a unit edit, a re-pulled model?): "
           "re-run DV4-PLAN §3.6's probes and re-pin, never sample on it silently")
    if not facts.get("reachable"):
        return [apparatus.Drift("model_server.reachable", "yes", "no", "start Ollama (the "
                                "`ollama` unit) or defer the batch")]
    if ms.get("version") is not None and facts.get("version") != ms.get("version"):
        out.append(apparatus.Drift("model_server.version", str(ms.get("version")),
                                   str(facts.get("version")), why))
    for tag, want in (ms.get("models") or {}).items():
        got = (facts.get("models") or {}).get(tag)
        if got != want:
            out.append(apparatus.Drift(f"model_server.models.{tag}", str(want),
                                       str(got or "missing"), why))
    pins = ms.get("unit") or {}
    unit = facts.get("unit")
    for k, want in pins.items():
        got = None if unit is None else unit.get(k)
        if got != str(want):
            out.append(apparatus.Drift(f"model_server.unit.{k}", str(want),
                                       "unreadable" if unit is None else str(got or "unset"),
                                       why))
    return out


class HostGate:
    """One run's gate on an ephemeral loopback port (module docstring)."""

    def __init__(self, run_dir, config: dict, *, root=None, upstream=None):
        refuse_if_disabled()
        self.run_dir = Path(run_dir)
        self.config = dict(config)
        self.root = Path(root) if root is not None else ROOT
        self.upstream = upstream or UPSTREAM
        if not re.fullmatch(r"http://127\.0\.0\.1:\d{1,5}", self.upstream):
            raise GateError(f"the gate's upstream must be a loopback http address, not "
                            f"{self.upstream!r}")
        self.proc = None
        self.url = None

    @property
    def counts_path(self) -> Path:
        return self.run_dir / "gate-counts.json"

    @property
    def log_path(self) -> Path:
        return self.run_dir / "gate.log"

    def start(self) -> str:
        refuse_if_disabled()
        self.run_dir.mkdir(parents=True, exist_ok=True)
        cfg = self.run_dir / ".gate-config.json"
        cfg.write_text(json.dumps(self.config, sort_keys=True), encoding="utf-8")
        ready = self.run_dir / ".gate-ready"
        if ready.exists():
            ready.unlink()
        err = open(self.run_dir / ".gate-stderr", "wb")
        try:
            self.proc = subprocess.Popen(
                [sys.executable, "-B", str(self.root / GATE_SCRIPT), "--port", "0",
                 "--config", str(cfg), "--log", str(self.log_path), "--counts",
                 str(self.counts_path), "--ready", str(ready), "--upstream", self.upstream,
                 "--owner-pid", str(os.getpid())],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err,
                start_new_session=True)
        finally:
            err.close()
        deadline = time.monotonic() + START_TIMEOUT_S
        while time.monotonic() < deadline:
            if ready.is_file() and ready.read_text(encoding="utf-8").strip():
                self.url = ready.read_text(encoding="utf-8").strip()
                return self.url
            if self.proc.poll() is not None:
                break
            time.sleep(0.05)
        why = (self.run_dir / ".gate-stderr").read_text(encoding="utf-8", errors="replace")
        self.stop()
        raise GateError("the model gate did not start" + (f": {why.strip().splitlines()[-1]}"
                                                         if why.strip() else ""))

    def counts(self) -> dict:
        try:
            obj = json.loads(self.counts_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return obj if isinstance(obj, dict) else {}

    def stop(self) -> None:
        p, self.proc = self.proc, None
        if p is not None and p.poll() is None:
            p.send_signal(signal.SIGTERM)
            try:
                p.wait(timeout=180)           # an unload at stop may take a moment
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=30)
        for name in (".gate-config.json", ".gate-ready", ".gate-stderr"):
            try:
                (self.run_dir / name).unlink()
            except OSError:
                pass


class GpuCalendar:
    """The per-user GPU calendar lock, held for a whole Qwen batch (module docstring)."""

    def __init__(self, base=None):
        base = base or os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
        self.path = Path(base) / CALENDAR_LOCK
        self.fh = None

    def __enter__(self):
        self.fh = open(self.path, "a+")
        try:
            fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.fh.close()
            self.fh = None
            raise Deferred(f"another Qwen batch holds the GPU calendar lock ({self.path}): the "
                           "batch is deferred (DV4-PLAN §10)") from None
        return self

    def __exit__(self, *exc):
        if self.fh is not None:
            try:
                fcntl.flock(self.fh, fcntl.LOCK_UN)
            finally:
                self.fh.close()
                self.fh = None
        return False
