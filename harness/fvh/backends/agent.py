"""fvh.backends.agent — the agent-mode route of fvh.batch (DV4-PLAN §3.5; the user's
decision D8 of 2026-10-12, built by DV5d's agent-mode lane).

One agent session of a batch attempt: opencode and the pinned Qwen in a per-run
container, through scripts/mksandbox-run (the one program that starts a container,
whose library is dvl.sandbox), as scripts/contract_local.sh composes its replay,
with a benchmark task in place of a contract:

  1. `mksandbox-run --build-agent` writes the session's manifest
     (dvl.sandbox.build_agent): the brief at TASK.md, the task's editable files (a
     task file, or a crate card's src/**/*.rs; by src, or inline from the work copy
     a continuation starts from), a crate's companions read-only, the module's given
     chain, project files, trusted tools and pins;
  2. `mksandbox-run --agent-session` validates, materializes and self-tests it and
     runs it live (dvl.sandbox.live_run): the gate gets the session's per-request
     seeds and writes its log and counts straight into the session's directory, and
     the batch's open file on the GPU calendar lock is passed in (checked there);
  3. the session's directory then holds TASK.md (the brief), manifest.json,
     selftest.json, sandbox.json (the run's record), returned/ and patch.diff (the
     files the agent changed), the event stream after the secret scan
     (transcript.jsonl.gz), gate.log.gz and gate-counts.json, and session.log
     (mksandbox-run's own lines).

The child runs with the parent-death signal set (SIGKILL), so a runner killed
outright takes it along, and its watcher removes the container, the gate and the
staged run directory; a runner interrupted (SIGINT, SIGTERM) kills it the same way.

The batch (fvh.batch) owns everything around a session: the ledger, the attempt's
seeds and caps, the verification of what the agent returned in a fresh
verification container, a gated arm's acceptance tool and its refused stops, the
run directory's RunMeta and secret scan.

  SegmentSpec          one session's inputs
  Segment              what one session did (the gate's counts, the agent's end,
                       the returned files)
  LiveAgent(root, app, *, mem_gb=None, log=None, mksandbox=None)
      .preflight(spec) -> [problem, ...]   the manifest built and self-tested
                                           (`--selftest-only`); nothing runs,
                                           nothing is kept
      .run_segment(spec) -> Segment        backends.Deferred when the host cannot
                                           start it (memory short, the GPU calendar
                                           lock held elsewhere); a refusal or a
                                           failure of the sandbox is a Segment with
                                           code 1, which carries the gate's counts
                                           when the sandbox wrote no record (ended_by
                                           killed-memory for exit 137/143 or a
                                           signal)

Standard library only. FVH_NO_MODEL=1 and DVL_NO_DOCKER=1 refuse.
"""

import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from fvh import backends

__all__ = ["KILLED_MEMORY", "LiveAgent", "Segment", "SegmentSpec"]

MKSANDBOX_TIMEOUT_S = 300
SESSION_GRACE_S = 900            # beyond the session's wall clock: start, return, removal
PR_SET_PDEATHSIG = 1
KILLED_CODES = (-9, -15, 137, 143)   # SIGKILL/SIGTERM: the memory scope, never a verdict
KILLED_MEMORY = "killed-memory"      # a Segment's ended_by for those exits


def _die_with_parent():
    """preexec_fn: the child gets SIGKILL when the runner dies (Linux prctl)."""
    try:
        import ctypes
        import signal
        ctypes.CDLL(None, use_errno=True).prctl(PR_SET_PDEATHSIG, signal.SIGKILL)
    except Exception:                                 # best effort; the reaper is the net
        pass


@dataclass(frozen=True)
class SegmentSpec:
    attempt_id: str
    run_id: str                 # the session's container run id (file-safe, at most 64)
    module: str
    task: str                   # the task's course path (a task file or a crate directory)
    brief: str
    turns: int                  # opencode's step limit and the gate's call cap
    seeds: tuple                # one per turn at least
    wall_s: float
    gpu_s: float | None
    seg_dir: Path
    texts: dict | None = None   # a continuation's work copy: {course path: text} of every
                                # editable file, staged inline
    calendar_fd: int | None = None  # the batch's open file on the GPU calendar lock


@dataclass
class Segment:
    code: int                   # live_run's: 0 completed, 1 a step failed, 124 wall clock
    ended_by: str = ""          # the sandbox's record's ended_by (done, start-failed, ...)
    agent_end: str = ""         # exit, error, wall-clock ("" when the agent never ran)
    returned: dict = field(default_factory=dict)    # {course path: text} of changed files
    deleted: list = field(default_factory=list)
    rejected: list = field(default_factory=list)
    calls: int = 0
    gpu_s: float = 0.0
    prompt_tokens: int = 0
    output_tokens: int = 0
    ctx_saturated: int = 0
    capped: int = 0
    steps: int = 0
    wall_s: float = 0.0
    agent_wall_s: float = 0.0
    withheld: bool = False      # the sandbox's scan withheld a returned file or the stream
    manifest_sha256: str = ""
    config_sha256: str = ""
    image: str = ""
    selftest_ok: bool = True
    detail: str = ""

    def summary(self) -> dict:
        return {"code": self.code, "ended_by": self.ended_by, "agent_end": self.agent_end,
                "returned": sorted(self.returned), "deleted": sorted(self.deleted),
                "rejected": len(self.rejected), "calls": self.calls,
                "gpu_s": round(self.gpu_s, 3), "steps": self.steps,
                "wall_s": self.wall_s, "manifest_sha256": self.manifest_sha256,
                "config_sha256": self.config_sha256, "selftest_ok": self.selftest_ok,
                **({"detail": self.detail[:300]} if self.detail else {})}


def read_counts(seg_dir) -> dict:
    """The gate's running totals of a session (its gate-counts.json), or {}."""
    try:
        obj = json.loads((Path(seg_dir) / "gate-counts.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return obj if isinstance(obj, dict) else {}


def _counted(seg, seg_dir):
    """A Segment returned without the sandbox's record, given the gate's counts the
    session wrote before it ended (a session killed after a request made that request:
    DV5d review fix)."""
    cnt = read_counts(seg_dir)
    seg.calls = int(cnt.get("calls") or 0)
    seg.gpu_s = float(cnt.get("gpu_s") or 0.0)
    seg.prompt_tokens = int(cnt.get("prompt_tokens") or 0)
    seg.output_tokens = int(cnt.get("output_tokens") or 0)
    seg.ctx_saturated = int(cnt.get("ctx_saturated") or 0)
    seg.capped = int(cnt.get("capped") or 0)
    return seg


def compress_gate_log(seg_dir):
    p = Path(seg_dir) / "gate.log"
    if p.is_file():
        (Path(seg_dir) / "gate.log.gz").write_bytes(gzip.compress(p.read_bytes(), mtime=0))
        p.unlink()


class LiveAgent:
    """The live route (module docstring)."""

    def __init__(self, root, app, *, mem_gb=None, log=None, mksandbox=None):
        backends.refuse_if_disabled()
        if os.environ.get("DVL_NO_DOCKER") == "1":
            raise backends.ModelDisabled("DVL_NO_DOCKER=1 is set (the CI environment): no agent "
                                         "container runs here")
        self.root = Path(root)
        self.app = app
        self.mem_gb = mem_gb
        self.say = log or (lambda m: None)
        self.mksandbox = Path(mksandbox) if mksandbox else self.root / "scripts" / "mksandbox-run"

    def _mk(self, args, timeout, *, fds=()):
        return subprocess.run([sys.executable, "-B", str(self.mksandbox), *args], cwd=self.root,
                              stdin=subprocess.DEVNULL, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout,
                              pass_fds=tuple(fds), preexec_fn=_die_with_parent)

    def _build(self, spec, where) -> tuple:
        """(manifest path, None) or (None, why)."""
        where = Path(where)
        brief = where / "TASK.md"
        brief.write_text(spec.brief, encoding="utf-8")
        args = ["--build-agent", "--task", spec.task, "--brief", str(brief), "--turns",
                str(int(spec.turns)), "--wall-s", f"{max(1, min(4 * 3600, int(spec.wall_s)))}",
                "--module", spec.module, "--run-id", spec.run_id]
        if spec.gpu_s is not None:
            args += ["--gpu-s", f"{max(1.0, float(spec.gpu_s)):g}"]
        if self.mem_gb is not None:
            args += ["--mem-gb", f"{float(self.mem_gb):g}"]
        if spec.texts is not None:
            t = where / ".texts.json"
            t.write_text(json.dumps(spec.texts), encoding="utf-8")
            args += ["--texts", str(t)]
        try:
            p = self._mk(args, MKSANDBOX_TIMEOUT_S)
        finally:
            (where / ".texts.json").unlink(missing_ok=True)
        if p.returncode != 0:
            why = [x for x in p.stderr.splitlines() if "build-agent:" in x] \
                or p.stderr.strip().splitlines()[-1:] or [f"exit {p.returncode}"]
            return None, "; ".join(why)[:2000]
        m = where / ".manifest.json"
        m.write_text(p.stdout, encoding="utf-8")
        return m, None

    def preflight(self, spec) -> list:
        work = Path(tempfile.mkdtemp(prefix="fvh-agent-preflight-"))
        try:
            man, why = self._build(spec, work)
            if man is None:
                return [why]
            p = self._mk(["--selftest-only", str(man)], MKSANDBOX_TIMEOUT_S)
            try:
                rep = json.loads(p.stdout)
            except ValueError:
                return [(p.stderr.strip().splitlines() or [f"exit {p.returncode}"])[-1]]
            return [f"{name}: {x}" for name, chk in rep.get("checks", {}).items()
                    for x in chk.get("problems", [])]
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def run_segment(self, spec) -> Segment:
        seg_dir = Path(spec.seg_dir)
        seg_dir.mkdir(parents=True, exist_ok=True)
        man, why = self._build(spec, seg_dir)
        if man is None:
            return Segment(1, "manifest-refused", detail=why, selftest_ok=False)
        seeds = seg_dir / ".seeds.json"
        seeds.write_text(json.dumps([int(x) for x in list(spec.seeds)[:int(spec.turns)]]),
                         encoding="utf-8")
        args = ["--agent-session", "--records", str(seg_dir), "--seeds", str(seeds)]
        fds = ()
        if spec.calendar_fd is not None:
            args += ["--calendar-fd", str(int(spec.calendar_fd))]
            fds = (int(spec.calendar_fd),)
        p = None
        try:
            p = self._mk(args + [str(man)], float(spec.wall_s) + SESSION_GRACE_S, fds=fds)
        except subprocess.TimeoutExpired:
            pass
        finally:
            for f in (man, seeds):
                f.unlink(missing_ok=True)
            compress_gate_log(seg_dir)
        if p is not None:
            (seg_dir / "session.log").write_text(p.stdout + p.stderr, encoding="utf-8")
        if p is None:
            return _counted(Segment(1, "session-timeout", detail="mksandbox-run did not return "
                                    "within the session's wall clock and its grace"), seg_dir)
        if p.returncode == 3 and "deferred" in p.stderr:
            raise backends.Deferred((p.stderr.strip().splitlines() or ["deferred"])[-1])
        st = _json(seg_dir / "selftest.json")
        rec = _json(seg_dir / "sandbox.json")
        tail = (p.stderr.strip().splitlines() or [f"exit {p.returncode}"])[-1][:2000]
        if not rec:                   # no record: the gate's counts still say what ran
            if st and not st.get("ok", True):
                return _counted(Segment(1, "selftest-failed", selftest_ok=False, detail=tail),
                                seg_dir)
            if p.returncode in KILLED_CODES:
                return _counted(Segment(1, KILLED_MEMORY, detail=f"mksandbox-run killed (exit "
                                        f"{p.returncode}): {tail}"), seg_dir)
            return _counted(Segment(1, "sandbox-refused" if p.returncode == 3 else
                                    "sandbox-failed", detail=tail), seg_dir)
        ag = rec.get("agent") or {}
        ret = rec.get("return") or {}
        returned, bad = {}, []
        for path in ret.get("returned") or []:
            f = seg_dir / "returned" / path
            try:
                returned[path] = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                bad.append({"name": path, "why": "unreadable or not UTF-8"})
        cnt = read_counts(seg_dir)
        code = p.returncode if p.returncode in (0, 1, 124) else 1
        return Segment(
            code=code, ended_by=str(rec.get("ended_by") or ""),
            agent_end=str(ag.get("ended") or ""), returned=returned,
            deleted=sorted(ret.get("deleted") or []),
            rejected=list(ret.get("rejected") or []) + bad,
            calls=int(cnt.get("calls") or 0), gpu_s=float(cnt.get("gpu_s") or 0.0),
            prompt_tokens=int(cnt.get("prompt_tokens") or 0),
            output_tokens=int(cnt.get("output_tokens") or 0),
            ctx_saturated=int(cnt.get("ctx_saturated") or 0), capped=int(cnt.get("capped") or 0),
            steps=int((ag.get("summary") or {}).get("steps") or 0),
            wall_s=float(rec.get("wall_s") or 0.0), agent_wall_s=float(ag.get("wall_s") or 0.0),
            withheld=bool((rec.get("secret_scan") or {}).get("withheld")
                          or ag.get("transcript_withheld")),
            manifest_sha256=str(rec.get("manifest_sha256") or ""),
            config_sha256=str(ag.get("config_sha256") or ""), image=str(rec.get("image") or ""),
            selftest_ok=bool(rec.get("selftest_ok", True)),
            detail=(str(rec.get("detail") or "") or (tail if code else ""))[:2000])


def _json(p) -> dict:
    try:
        obj = json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return obj if isinstance(obj, dict) else {}
