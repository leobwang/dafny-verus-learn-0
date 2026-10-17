"""fvh.budget — caps, the attempt plan, the hash-chained ledger and its anchors,
rolling windows and the overage check, checkpoint and resume (DV4-PLAN §4;
Δ148, Δ149, Δ176).

Units (spec §5.6): calls, tokens (input and output), turns, wall-clock seconds
and GPU-seconds. Three levels of cap, each enforced before the call that would
cross it: per run (Caps, Meter), per module or lab (the registry's `budget`:
claude_calls, claude_runs, qwen_calls, qwen_runs, gpu_hours; check_plan) and
the rolling windows (WindowRule, OverageWatch, batch_may_start).

  Caps(calls, tokens, turns, wall_s, gpu_s)     None: no cap on that unit
  Meter(caps)      counts one run's use; cause() names the first cap reached
                   ("call-cap", "token-cap", "turn-cap", "wall-clock",
                   "gpu-cap"); before_call() raises CapReached on a call,
                   token, GPU or wall-clock cap (the model units are enforced
                   at the call, so a policy that sees an exhausted budget can
                   still stop on its own); the executor checks the turn cap
                   and the wall clock before each proposal;
                   snapshot() is the protocol.Budget a policy sees
  WindowRule, check_event(info, rule) -> (verdict, reason)
                   one rate_limit_event's rate_limit_info: "stop" when
                   isUsingOverage is not false or overageStatus is not in the
                   apparatus file's allowed list (the batch stops as
                   apparatus-mismatch, Δ148); "defer" when the status is not
                   an allowed one or a window's utilization passes its
                   threshold; else "ok"
  OverageWatch     per batch: every call is judged on its own event; a call
                   without one stops the batch (an apparatus anomaly: Δ148
                   and step 4a's probe found one on every call)
  batch_may_start(window_file, rule, now)
                   a batch starts only from a recorded event younger than one
                   five-hour window that checks "ok"; otherwise its first call
                   is a sentinel (Ledger.sentinel), never an attempt

The ledger research/runs/<ID>/ledger.jsonl is append-only and hash-chained:
line n (seq n, from 1) is one JSON object, written canonically (sorted keys,
no spaces), whose "prev" is the sha256 of line n-1's text (GENESIS for the
first). Attempt ids are "<arm>/<task>/<repeat>/<attempt>", fixed by the plan
before the batch; each moves planned -> running -> scored, or to infra-failed
or deferred, and scored is written once (TRANSITIONS). An infra-failed id is
re-issued under the same id at most MAX_REISSUE times (the pre-registration
may set fewer); resume_order() lists what `fvh resume` re-issues, in plan
order, and never a scored id.

The anchors research/ledger-heads.jsonl: at each batch's start and end one
line {module, event ("open"|"close"), seq, head, planned, date,
course_commit}. check_anchors() refuses (AnchorError: exit 3, naming the
line) a module whose ledger is missing, shorter than an anchored seq, or
hashes differently there; open_batch() refuses a new batch while the
module's last anchor is an open one (resume it), and refuses when git
reports the heads file ignored. Only fvh writes the ledgers and the heads
file.

Frozen (guard rule 2f), standard library only.
"""

import dataclasses
import datetime as _dt
import hashlib
import json
import re
import subprocess
import time
import tomllib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from fvh import protocol

__all__ = ["AnchorError", "Arm", "BudgetError", "CAP_CAUSES", "CLAUDE", "Caps", "CapReached",
           "FAMILIES", "GENESIS", "HEADS", "Ledger", "LedgerError", "MAX_REISSUE", "Meter",
           "OverageWatch", "PlannedAttempt", "QWEN", "STATES", "TRANSITIONS",
           "TRUNCATION_CAUSES", "WindowRule", "anchor", "attempt_id", "batch_may_start",
           "check_anchors", "check_event", "check_plan", "close_batch", "enumerate_plan",
           "heads_ignored", "last_anchor", "ledger_path", "open_batch", "plan_totals",
           "read_heads", "read_window", "registry_budget", "resume_order", "write_window"]

CLAUDE = "claude"
QWEN = "qwen"
# family -> the registry's (calls, runs) budget fields (Δ176)
FAMILY_KEYS = {CLAUDE: ("claude_calls", "claude_runs"), QWEN: ("qwen_calls", "qwen_runs")}
FAMILIES = tuple(FAMILY_KEYS)
UNITS = ("calls", "tokens", "turns", "wall_s", "gpu_s")
CALL_UNITS = ("calls", "tokens", "wall_s", "gpu_s")     # checked before each model call
TURN_UNITS = ("turns", "wall_s")                        # checked before each proposal
CAP_CAUSES = {"calls": "call-cap", "tokens": "token-cap", "turns": "turn-cap",
              "wall_s": "wall-clock", "gpu_s": "gpu-cap"}
# DV4-PLAN §4.3 rule 2's causes; the container runtime's is spelled "container" (the plan's
# word for it is one scripts/check_single_route.py keeps to the entry points); "interrupted"
# is the batch runner's own stop from outside the run (a SIGINT or SIGTERM, or a runner
# killed outright and settled by `fvh resume`, fvh.batch): scored, never re-issued, so that
# an interruption never becomes best-of-n
TRUNCATION_CAUSES = ("rate-limit", "auth", "cli-crash", "gate", "proxy", "container",
                     "host-memory", "interrupted")
STATES = ("planned", "running", "scored", "infra-failed", "deferred")
TRANSITIONS = {"planned": ("running", "deferred"),
               "running": ("scored", "infra-failed", "deferred"),
               "deferred": ("running",),
               "infra-failed": ("running",),
               "scored": ()}
MAX_REISSUE = 3               # [A] re-issues of one infra-failed id (§4.3 rule 3)
GENESIS = "0" * 64
HEADS = "research/ledger-heads.jsonl"
WINDOW_FILE = "research/runs/claude-window.json"
FIVE_HOURS = 5 * 3600
_ID_PART = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]*")
_MODULE = re.compile(r"[QR]\d\d")


class BudgetError(ValueError):
    """A plan or a request the budget refuses (exit 3)."""


class CapReached(RuntimeError):
    """A per-run cap is reached; `cause` is one of CAP_CAUSES' values."""

    def __init__(self, cause: str, detail: str = ""):
        super().__init__(f"{cause}: {detail}" if detail else cause)
        self.cause = cause


class LedgerError(ValueError):
    """A ledger line that breaks the chain or the state rules."""


class AnchorError(RuntimeError):
    """A ledger that disagrees with its anchors, or an open batch (exit 3)."""


# =====================================================================================
# Per-run caps
# =====================================================================================

@dataclass(frozen=True)
class Caps:
    """One run's caps (None: no cap on that unit)."""

    calls: int | None = None
    tokens: int | None = None
    turns: int | None = None
    wall_s: float | None = None
    gpu_s: float | None = None

    def __post_init__(self):
        for f in dataclasses.fields(self):
            v = getattr(self, f.name)
            if v is None:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0:
                raise ValueError(f"Caps.{f.name} must be a number >= 0 or None")

    @classmethod
    def from_mapping(cls, m: Mapping | None) -> "Caps":
        """Caps from a table such as the apparatus file's [defaults]; unknown keys refused."""
        m = dict(m or {})
        unknown = set(m) - set(UNITS)
        if unknown:
            raise ValueError("unknown cap unit(s): " + ", ".join(sorted(unknown)))
        return cls(**m)


class Meter:
    """One run's use against its caps."""

    def __init__(self, caps: Caps | None = None, *, clock=time.monotonic):
        self.caps = caps or Caps()
        self.clock = clock
        self.started = clock()
        self.calls = 0
        self.tokens_in = 0
        self.tokens_out = 0
        self.gpu_s = 0.0
        self.outputs = 0          # calls that returned model output
        self.turns = 0

    def elapsed(self) -> float:
        return self.clock() - self.started

    def used(self) -> dict:
        return {"calls": self.calls, "tokens": self.tokens_in + self.tokens_out,
                "turns": self.turns, "wall_s": self.elapsed(), "gpu_s": self.gpu_s}

    def cause(self, units=UNITS) -> str | None:
        """The first cap among `units` that is reached (use >= cap), in UNITS order, or None."""
        used = self.used()
        for unit in (u for u in UNITS if u in units):
            cap = getattr(self.caps, unit)
            if cap is not None and used[unit] >= cap:
                return CAP_CAUSES[unit]
        return None

    def before_call(self) -> None:
        """Raise CapReached when the next model call would cross a cap (calls, tokens,
        GPU-seconds or the wall clock; turns are the executor's)."""
        c = self.cause(CALL_UNITS)
        if c is not None:
            raise CapReached(c, "the next model call would cross the run's cap")

    def charge(self, *, calls: int = 1, tokens_in: int = 0, tokens_out: int = 0,
               gpu_s: float = 0.0, output: bool = True) -> None:
        for name, v in (("calls", calls), ("tokens_in", tokens_in), ("tokens_out", tokens_out),
                        ("gpu_s", gpu_s)):
            if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0:
                raise ValueError(f"Meter.charge: {name} must be a number >= 0")
        self.calls += calls
        self.tokens_in += int(tokens_in)
        self.tokens_out += int(tokens_out)
        self.gpu_s += float(gpu_s)
        if output:
            self.outputs += 1

    def snapshot(self) -> protocol.Budget:
        used = self.used()

        def left(unit):
            cap = getattr(self.caps, unit)
            return None if cap is None else cap - used[unit]
        return protocol.Budget(calls_left=left("calls"), tokens_left=left("tokens"),
                               wall_s_left=left("wall_s"), gpu_s_left=left("gpu_s"))

    def usage(self) -> dict:
        """The run's usage as RunMeta.usage records it (the client's counts)."""
        return {"calls": self.calls, "input_tokens": self.tokens_in,
                "output_tokens": self.tokens_out, "turns": self.turns,
                "wall_s": round(self.elapsed(), 3), "gpu_s": round(self.gpu_s, 3),
                "outputs": self.outputs}


# =====================================================================================
# Rolling windows and overage (Δ148)
# =====================================================================================

@dataclass(frozen=True)
class WindowRule:
    """The apparatus file's window and overage pins."""

    allowed_overage: tuple = ("rejected",)
    allowed_status: tuple = ("allowed",)
    five_hour_max: float = 0.8            # [A]
    seven_day_max: float = 0.6            # [A]
    max_age_s: float = FIVE_HOURS

    def __post_init__(self):
        object.__setattr__(self, "allowed_overage", tuple(self.allowed_overage))
        object.__setattr__(self, "allowed_status", tuple(self.allowed_status))

    @classmethod
    def from_mapping(cls, m: Mapping | None) -> "WindowRule":
        m = dict(m or {})
        known = {f.name for f in dataclasses.fields(cls)}
        unknown = set(m) - known
        if unknown:
            raise ValueError("unknown window key(s): " + ", ".join(sorted(unknown)))
        return cls(**m)


def check_event(info, rule: WindowRule) -> tuple[str, str]:
    """("ok"|"defer"|"stop", reason) for one rate_limit_event's rate_limit_info."""
    if not isinstance(info, Mapping):
        return "stop", "no rate_limit_info: the overage state is unknown"
    if info.get("isUsingOverage") is not False:
        return "stop", f"isUsingOverage is {info.get('isUsingOverage')!r}, not false"
    if info.get("overageStatus") not in rule.allowed_overage:
        return "stop", (f"overageStatus {info.get('overageStatus')!r} is not in the allowed "
                        f"list {list(rule.allowed_overage)}")
    if info.get("status") not in rule.allowed_status:
        return "defer", f"status {info.get('status')!r}: a window or limit is reached"
    windows = info.get("unifiedWindows")
    windows = windows if isinstance(windows, Mapping) else {}
    for name, limit in (("five_hour", rule.five_hour_max), ("seven_day", rule.seven_day_max)):
        w = windows.get(name)
        u = w.get("utilization") if isinstance(w, Mapping) else None
        if isinstance(u, (int, float)) and not isinstance(u, bool) and u >= limit:
            return "defer", f"the {name} window's utilization {u} is at or above {limit}"
    return "ok", "allowed, no overage, under the thresholds"


class OverageWatch:
    """The per-batch overage check of every call (Δ148)."""

    def __init__(self, rule: WindowRule):
        self.rule = rule
        self.last = None
        self.calls = 0

    def observe(self, info) -> tuple[str, str, Mapping | None]:
        """(verdict, reason, the event that was judged) for one call's event or None.
        Every call carries its own event (Δ148, step 4a's probe): a call without one
        is an apparatus anomaly and stops the batch, never judged on an earlier
        call's event (DV5c fix round)."""
        self.calls += 1
        if info is None:
            return "stop", ("the call carried no rate_limit_event: its overage state is "
                            "unknown"), None
        self.last = info
        verdict, reason = check_event(info, self.rule)
        return verdict, reason, info


def read_window(path) -> dict | None:
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return obj if isinstance(obj, dict) else None


def write_window(path, info: Mapping, *, now: float | None = None) -> None:
    """Keep the newest event of any batch (research/runs/claude-window.json)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = {"recorded_at": time.time() if now is None else now, "rate_limit_info": dict(info)}
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(rec, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    tmp.replace(p)


def batch_may_start(path, rule: WindowRule, *, now: float | None = None) -> tuple[bool, str]:
    """(True, why) when the recorded event lets a batch start without a sentinel."""
    now = time.time() if now is None else now
    rec = read_window(path)
    if rec is None:
        return False, "no recorded window event: the first call is a sentinel"
    at = rec.get("recorded_at")
    if not isinstance(at, (int, float)) or isinstance(at, bool) or now - at >= rule.max_age_s:
        return False, "the recorded window event is older than one five-hour window: a sentinel"
    verdict, reason = check_event(rec.get("rate_limit_info"), rule)
    if verdict != "ok":
        return False, f"the recorded window event does not allow a start ({reason}): a sentinel"
    return True, "a fresh recorded window event allows the start"


# =====================================================================================
# The attempt plan and the registry budget
# =====================================================================================

@dataclass(frozen=True)
class Arm:
    """One arm of a batch: its name, model family and calls per attempt (rounds)."""

    name: str
    family: str
    rounds: int

    def __post_init__(self):
        if not isinstance(self.name, str) or not _ID_PART.fullmatch(self.name):
            raise ValueError(f"arm name {self.name!r} is not an id part")
        if self.family not in FAMILY_KEYS:
            raise ValueError(f"arm family must be one of {', '.join(FAMILIES)}")
        if isinstance(self.rounds, bool) or not isinstance(self.rounds, int) or self.rounds < 1:
            raise ValueError("Arm.rounds must be an int >= 1")


@dataclass(frozen=True)
class PlannedAttempt:
    id: str
    family: str
    calls: int


def attempt_id(arm: str, task: str, repeat: int, attempt: int) -> str:
    for name, part in (("arm", arm), ("task", task)):
        if not isinstance(part, str) or not _ID_PART.fullmatch(part):
            raise ValueError(f"{name} {part!r} is not an id part")
    for name, n in (("repeat", repeat), ("attempt", attempt)):
        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            raise ValueError(f"{name} must be an int >= 1")
    return f"{arm}/{task}/{repeat}/{attempt}"


def enumerate_plan(arms: Iterable[Arm], tasks: Iterable[str], *, repeats: int = 1,
                   attempts: int = 1) -> list[PlannedAttempt]:
    """Every attempt id of a batch, in plan order (arm, task, repeat, attempt):
    calls = tasks x attempts x rounds x arms x repeats (design §11.1)."""
    arms, tasks = list(arms), list(tasks)
    out = [PlannedAttempt(attempt_id(a.name, t, r, k), a.family, a.rounds)
           for a in arms for t in tasks for r in range(1, repeats + 1)
           for k in range(1, attempts + 1)]
    if len({p.id for p in out}) != len(out):
        raise BudgetError("the plan repeats an attempt id")
    return out


def plan_totals(items: Iterable[PlannedAttempt]) -> dict:
    tot = {f: {"calls": 0, "runs": 0} for f in FAMILIES}
    for p in items:
        tot[p.family]["calls"] += p.calls
        tot[p.family]["runs"] += 1
    return tot


def registry_budget(root, module: str) -> dict:
    """The module's `budget` table from MODULES.toml (BudgetError when absent)."""
    try:
        data = tomllib.loads((Path(root) / "MODULES.toml").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise BudgetError(f"MODULES.toml cannot be read ({type(e).__name__})") from None
    for m in data.get("module", []):
        if isinstance(m, dict) and str(m.get("id", "")).upper() == module.upper():
            b = m.get("budget")
            if not isinstance(b, dict):
                raise BudgetError(f"{module}'s registry record has no budget table")
            return dict(b)
    raise BudgetError(f"module {module!r} is not in MODULES.toml")


def check_plan(items: Iterable[PlannedAttempt], budget: Mapping, *,
               used: Mapping | None = None) -> list[str]:
    """Problems with a plan against the registry budget, counting what the
    ledger already holds (`used`: family -> {"calls", "runs"}); empty when it fits."""
    tot = plan_totals(items)
    used = used or {}
    out = []
    for fam, (ck, rk) in FAMILY_KEYS.items():
        for unit, key in (("calls", ck), ("runs", rk)):
            want = tot[fam][unit] + int((used.get(fam) or {}).get(unit, 0))
            have = budget.get(key, 0)
            if not isinstance(have, int) or isinstance(have, bool):
                have = 0
            if want > have:
                out.append(f"the plan needs {want} {fam} {unit} with the ledger's, the "
                           f"registry allows {key} = {have}")
    return out


# =====================================================================================
# The ledger
# =====================================================================================

def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ledger_path(root, module: str) -> Path:
    if not _MODULE.fullmatch(module):
        raise ValueError(f"{module!r} is not a module id")
    return Path(root) / "research" / "runs" / module / "ledger.jsonl"


@dataclass
class AttemptState:
    state: str
    family: str
    calls: int
    order: int
    reissues: int = 0
    outcome: str | None = None


class Ledger:
    """research/runs/<ID>/ledger.jsonl (module docstring)."""

    def __init__(self, path, *, clock=_utc_now):
        self.path = Path(path)
        self.clock = clock

    # --- reading -------------------------------------------------------------------

    def texts(self) -> list[str]:
        if not self.path.exists():
            return []
        raw = self.path.read_text(encoding="utf-8")
        if raw and not raw.endswith("\n"):
            raise LedgerError(f"{self.path}: the last line is incomplete")
        return raw.splitlines()

    def read(self) -> list[dict]:
        """Every line, the chain and the state rules checked (LedgerError naming the line)."""
        out, prev = [], GENESIS
        states: dict[str, str] = {}
        for n, text in enumerate(self.texts(), 1):
            try:
                rec = json.loads(text)
            except ValueError:
                raise LedgerError(f"{self.path}:{n}: not JSON") from None
            if not isinstance(rec, dict) or _canon(rec) != text:
                raise LedgerError(f"{self.path}:{n}: not a canonical ledger line")
            if rec.get("seq") != n:
                raise LedgerError(f"{self.path}:{n}: seq {rec.get('seq')!r}, expected {n}")
            if rec.get("prev") != prev:
                raise LedgerError(f"{self.path}:{n}: the chain breaks here (prev does not hash "
                                  "the line before)")
            kind = rec.get("kind")
            if kind == "attempt":
                aid, st = rec.get("id"), rec.get("state")
                if st not in STATES:
                    raise LedgerError(f"{self.path}:{n}: state {st!r}")
                before = states.get(aid)
                if before is None and st != "planned":
                    raise LedgerError(f"{self.path}:{n}: {aid} moves to {st} without a plan")
                if before is not None and st not in TRANSITIONS[before]:
                    raise LedgerError(f"{self.path}:{n}: {aid} cannot move {before} -> {st}")
                states[aid] = st
            elif kind not in ("sentinel", "note"):
                raise LedgerError(f"{self.path}:{n}: kind {kind!r}")
            out.append(rec)
            prev = _sha(text)
        return out

    def head(self) -> tuple[int, str]:
        texts = self.texts()
        return (len(texts), _sha(texts[-1])) if texts else (0, GENESIS)

    def line_hash(self, seq: int) -> str | None:
        texts = self.texts()
        return _sha(texts[seq - 1]) if 1 <= seq <= len(texts) else None

    def attempts(self) -> dict[str, AttemptState]:
        out: dict[str, AttemptState] = {}
        for rec in self.read():
            if rec["kind"] != "attempt":
                continue
            aid, st = rec["id"], rec["state"]
            if st == "planned":
                out[aid] = AttemptState("planned", rec["family"], rec["calls"], len(out))
                continue
            a = out[aid]
            if st == "running" and a.state == "infra-failed":
                a.reissues += 1
            a.state = st
            if st == "scored":
                a.outcome = rec.get("outcome")
        return out

    def used(self) -> dict:
        """family -> {"calls": planned calls, sentinel calls and the calls spent by
        attempts that ended infra-failed or deferred (their id runs again, so what
        they spent is spent on top of the plan), "runs": planned ids}."""
        tot = {f: {"calls": 0, "runs": 0} for f in FAMILIES}
        family = {}
        for rec in self.read():
            if rec["kind"] == "attempt" and rec["state"] == "planned":
                family[rec["id"]] = rec["family"]
                tot[rec["family"]]["calls"] += rec["calls"]
                tot[rec["family"]]["runs"] += 1
            elif rec["kind"] == "attempt" and rec["state"] in ("infra-failed", "deferred"):
                n = rec.get("calls")
                if isinstance(n, int) and not isinstance(n, bool) and n > 0 and \
                        rec["id"] in family:
                    tot[family[rec["id"]]]["calls"] += n
            elif rec["kind"] == "sentinel":
                tot[rec["family"]]["calls"] += rec["calls"]
        return tot

    def notes(self, name: str) -> list[dict]:
        """The ledger's `note` lines of one name, in order."""
        return [r for r in self.read() if r.get("kind") == "note" and r.get("note") == name]

    def overage_stop(self) -> dict | None:
        """The overage stop that still holds (DV5c fix round): the newest
        `overage-stop` note with no `overage-cleared` note after it, or None."""
        held = None
        for r in self.read():
            if r.get("kind") != "note":
                continue
            if r.get("note") == "overage-stop":
                held = r
            elif r.get("note") == "overage-cleared":
                held = None
        return held

    # --- writing ---------------------------------------------------------------------

    def append(self, rec: Mapping) -> dict:
        seq, head = self.head()
        self.read()                                   # never extend a broken chain
        line = dict(rec)
        line.update(seq=seq + 1, prev=head, date=self.clock())
        text = _canon(line)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(text + "\n")
        return line

    def plan(self, items: Iterable[PlannedAttempt]) -> int:
        have = self.attempts()
        items = list(items)
        for p in items:
            if p.id in have:
                raise BudgetError(f"attempt {p.id} is already in the ledger: no id is added "
                                  "twice")
        for p in items:
            self.append({"kind": "attempt", "id": p.id, "state": "planned",
                         "family": p.family, "calls": p.calls})
        return len(items)

    def move(self, aid: str, state: str, *, max_reissue: int = MAX_REISSUE, **info) -> dict:
        a = self.attempts().get(aid)
        if a is None:
            raise LedgerError(f"{aid} is not in the plan")
        if state not in TRANSITIONS[a.state]:
            raise LedgerError(f"{aid} cannot move {a.state} -> {state}")
        if a.state == "infra-failed" and a.reissues >= max_reissue:
            raise LedgerError(f"{aid} was re-issued {a.reissues} times, the most allowed")
        rec = {"kind": "attempt", "id": aid, "state": state}
        rec.update(info)
        return self.append(rec)

    def sentinel(self, *, family: str = CLAUDE, calls: int = 1, **info) -> dict:
        """A sentinel call (Δ148): counted against the module's calls, never an attempt."""
        rec = {"kind": "sentinel", "family": family, "calls": calls}
        rec.update(info)
        return self.append(rec)


def resume_order(ledger: Ledger, *, max_reissue: int = MAX_REISSUE) -> list[str]:
    """The ids `fvh resume` re-issues, in plan order: planned, deferred, and
    infra-failed ones with re-issues left; never a scored or running one."""
    out = []
    for aid, a in sorted(ledger.attempts().items(), key=lambda kv: kv[1].order):
        if a.state in ("planned", "deferred") or (a.state == "infra-failed"
                                                  and a.reissues < max_reissue):
            out.append(aid)
    return out


# =====================================================================================
# The anchors (Δ149)
# =====================================================================================

def read_heads(root) -> list[tuple[int, dict]]:
    p = Path(root) / HEADS
    if not p.exists():
        return []
    out = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            raise AnchorError(f"{HEADS}:{n}: not JSON") from None
        if not isinstance(rec, dict) or rec.get("event") not in ("open", "close") \
                or not isinstance(rec.get("seq"), int) or not isinstance(rec.get("head"), str):
            raise AnchorError(f"{HEADS}:{n}: not an anchor line")
        out.append((n, rec))
    return out


def last_anchor(root, module: str) -> dict | None:
    mine = [rec for _, rec in read_heads(root) if rec.get("module") == module]
    return mine[-1] if mine else None


def check_anchors(root, module: str) -> int:
    """The number of the module's anchors, each checked against its ledger
    (AnchorError naming the heads line otherwise)."""
    ledger = Ledger(ledger_path(root, module))
    mine = [(n, rec) for n, rec in read_heads(root) if rec.get("module") == module]
    if not mine:
        if ledger.path.exists():
            try:
                ledger.read()
            except LedgerError as e:
                raise AnchorError(str(e)) from None
        return 0
    if not ledger.path.exists():
        raise AnchorError(f"{HEADS}:{mine[-1][0]}: anchors {module}'s ledger, but "
                          f"{ledger.path.name} is missing: a reset budget is a visible edit of "
                          "the heads file, never a fresh start")
    try:
        ledger.read()
    except LedgerError as e:
        raise AnchorError(f"{e} ({HEADS} anchors this ledger)") from None
    count = len(ledger.texts())
    for n, rec in mine:
        seq = rec["seq"]
        if seq > count:
            raise AnchorError(f"{HEADS}:{n}: anchors seq {seq}, but the ledger holds {count} "
                              "lines (truncated)")
        if seq and ledger.line_hash(seq) != rec["head"]:
            raise AnchorError(f"{HEADS}:{n}: the ledger's line {seq} hashes differently "
                              "(edited or replaced)")
    return len(mine)


def heads_ignored(root) -> bool | None:
    """True when git reports the heads file ignored; None outside a git checkout."""
    try:
        p = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "--", HEADS],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode == 0:
        return True
    if p.returncode == 1:
        return False
    return None


def anchor(root, module: str, event: str, *, course_commit: str, planned: int,
           date: str | None = None) -> dict:
    if event not in ("open", "close"):
        raise ValueError("an anchor's event is open or close")
    seq, head = Ledger(ledger_path(root, module)).head()
    rec = {"module": module, "event": event, "seq": seq, "head": head, "planned": planned,
           "date": date or _utc_now(), "course_commit": course_commit}
    p = Path(root) / HEADS
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def open_batch(root, module: str, items: Iterable[PlannedAttempt], *, course_commit: str,
               budget: Mapping | None = None, require_git: bool = True) -> Ledger:
    """Check the anchors and the budget, write the plan, anchor the batch's start."""
    ign = heads_ignored(root)
    if ign is True:
        raise AnchorError(f"git reports {HEADS} ignored: the anchors must be tracked")
    if ign is None and require_git:
        raise AnchorError(f"{root} is not a git checkout: the anchors must be tracked")
    check_anchors(root, module)
    last = last_anchor(root, module)
    if last is not None and last["event"] == "open":
        raise AnchorError(f"{module}'s last batch is still open (seq {last['seq']}): resume it "
                          "(fvh resume), never start a fresh one")
    items = list(items)
    if not items:
        raise BudgetError("a batch plans at least one attempt")
    ledger = Ledger(ledger_path(root, module))
    budget = registry_budget(root, module) if budget is None else budget
    problems = check_plan(items, budget, used=ledger.used())
    if problems:
        raise BudgetError("; ".join(problems))
    ledger.plan(items)
    anchor(root, module, "open", course_commit=course_commit, planned=len(items))
    return ledger


def close_batch(root, module: str, *, course_commit: str) -> dict:
    last = last_anchor(root, module)
    if last is None or last["event"] != "open":
        raise AnchorError(f"{module} has no open batch to close")
    check_anchors(root, module)
    planned = len(Ledger(ledger_path(root, module)).attempts())
    return anchor(root, module, "close", course_commit=course_commit, planned=planned)
