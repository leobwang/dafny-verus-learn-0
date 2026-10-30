"""fvh.backends.gate — the host-side model gate of a policy run, and the GPU
calendar lock (DV4-PLAN §5.6.3, §10; Δ146, Δ202; the host's OpenAI-compatible
server since Δ505).

Every Qwen request of every mode passes a gate (sandbox/hostside/
model_gate.py). A policy run on the host (fvh.batch, policy mode through the
opencode CLI, D3) gets its own gate on an ephemeral loopback port:

  HostGate(run_dir, config, *, root=None, upstream=None)
      start()          the gate process, its log and running counts in the
                       run directory (gate.log, gate-counts.json), its owner
                       this process (--owner-pid: a killed runner leaves no
                       gate); returns the gate's base URL (clients add /v1)
      counts()         the gate's running totals (calls, tokens, reasoning
                       tokens, GPU-seconds, admitted, capped, overrides,
                       ctx_saturated, the server's version and
                       system_fingerprint as observed, ...)
      stop()           SIGTERM, wait
  discover(app, *, url=None, model=None) -> dict
                       the host's model server and model (Δ505), found by
                       model_gate.discover: the first of the apparatus file's
                       [model_gate] endpoints whose GET /models answers
                       (DVL_MODEL_URL in their place), its only served model
                       (or DVL_MODEL), the served max_model_len (or None) and
                       /version (or None): {"base_url", "model",
                       "max_model_len", "served", "version"}. Observed facts,
                       recorded with every run, never pinned: nothing marks a
                       run UNTRUSTED for the server's identity. GateError when
                       no server answers or the model cannot be chosen (the
                       batch refuses before its first attempt). Read only, no
                       inference
  gate_config(app, found, *, seeds, calls, gpu_s=None) -> dict
      the run's config: the found server and model (the gate checks GET
      /models again before it listens), the served max_model_len (or None:
      the context check then rests on the server's own refusal), the
      apparatus file's request options and margin, the run's per-request
      seeds (the gate sets seed n on the n-th request, so a lab's repeats are
      independent samples) and the caps (calls, and the GPU-seconds when
      given)
  GpuCalendar()        the per-user calendar lock ($XDG_RUNTIME_DIR/
                       dvl-gpu-calendar.lock, the one the sandbox's agent runs
                       take): a non-blocking flock held for a whole Qwen batch;
                       held by another batch -> Deferred (exit 3)

The gate's upstream is the host's server on loopback (Δ146, Δ505): the gate
sends no key; the transports never name the server. With FVH_NO_MODEL=1 no
gate starts (CI). Frozen (guard rule 2f), standard library only. This
directory is on scripts/check_single_route.py's allowlist.
"""

import fcntl
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

from fvh.backends import Deferred, refuse_if_disabled

__all__ = ["CALENDAR_LOCK", "GateError", "GpuCalendar", "HostGate", "discover", "gate_config"]

ROOT = Path(__file__).resolve().parents[3]
GATE_SCRIPT = "sandbox/hostside/model_gate.py"
CALENDAR_LOCK = "dvl-gpu-calendar.lock"     # DV4-PLAN §10, as dvl.sandbox's GPU_LOCK
START_TIMEOUT_S = 20
LOOPBACK_URL = re.compile(r"http://127\.0\.0\.1:\d{1,5}(/[A-Za-z0-9._~/-]*)?")


class GateError(RuntimeError):
    """The gate did not start (or its config cannot be built): no model call is made."""


def _loopback(url, what):
    if not isinstance(url, str) or not LOOPBACK_URL.fullmatch(url):
        raise GateError(f"{what} must be a loopback http address (http://127.0.0.1:PORT[/path]; "
                        f"never `localhost`), not {url!r}")
    return url.rstrip("/")


def _gate_module(root=None):
    """sandbox/hostside/model_gate.py as a module (its discover())."""
    path = Path(root if root is not None else ROOT) / GATE_SCRIPT
    spec = importlib.util.spec_from_file_location("dvl_model_gate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def discover(app, *, url=None, model=None, root=None) -> dict:
    """The host's model server and model (module docstring)."""
    refuse_if_disabled()
    mg = _gate_module(root)
    try:
        return mg.discover(app.model_gate().get("endpoints") or [], url=url, model=model)
    except mg.DiscoveryError as e:
        raise GateError(str(e)) from None


def gate_config(app, found, *, seeds, calls, gpu_s=None) -> dict:
    """The run's gate config (module docstring)."""
    mg = app.model_gate()
    if not isinstance(found, dict) or not isinstance(found.get("model"), str):
        raise GateError("a run's gate takes the discovered server and model (discover())")
    opts = mg.get("options")
    if not isinstance(opts, dict) or not opts:
        raise GateError("the apparatus file's [model_gate] options are missing")
    seeds = [int(s) for s in seeds]
    if not seeds or any(s < 0 for s in seeds):
        raise GateError("a run's gate takes its per-request seeds (one per call)")
    caps = {"calls": int(calls)}
    if gpu_s is not None:
        caps["gpu_s"] = float(gpu_s)
    return {"model": found["model"], "max_model_len": found.get("max_model_len"),
            "check_served": True, "options": dict(opts), "caps": caps,
            "margin": int(mg.get("margin", 512)), "seeds": seeds,
            "upstream": _loopback(found.get("base_url"), "the model server")}


class HostGate:
    """One run's gate on an ephemeral loopback port (module docstring)."""

    def __init__(self, run_dir, config: dict, *, root=None, upstream=None):
        refuse_if_disabled()
        self.run_dir = Path(run_dir)
        self.config = dict(config)
        self.root = Path(root) if root is not None else ROOT
        self.upstream = _loopback(upstream or self.config.get("upstream"), "the gate's upstream")
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
                p.wait(timeout=60)
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
        if not Path(base).is_dir() and sys.platform == "darwin":
            # macOS has no per-user runtime tmpfs: a private directory of its own
            base = Path(os.environ.get("TMPDIR") or "/tmp") / f"dvl-runtime-{os.getuid()}"
            base.mkdir(mode=0o700, exist_ok=True)
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
