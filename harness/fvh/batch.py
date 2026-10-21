"""fvh.batch — the live batch runner of `python -m fvh run` and `resume`
(DV4-PLAN §3.5, §3.6, §4; Δ148-Δ150, Δ182, Δ200-Δ203).

A batch is the attempts of one plan, run one at a time in plan order, each a
harness-executed run (DV4-PLAN §3.5): a policy proposes, the executor performs
its actions on a work copy, and every Verify runs in a fresh verification
container (fvh.tools.ContainerRunner). The model is reached only through the
pinned transports (fvh.backends): Claude in policy mode on the host, and the
local Qwen through its pinned agent CLI, tool-less, on the host behind a
per-run model gate (fvh.backends.gate; the user's decision D3 of 2026-10-12
keeps that CLI as the Qwen policy transport, fvh.backends' "qwen" family).

The plan (TOML; `python -m fvh run <ID> --plan PLAN.toml`):

    lab = "<lab>"                 optional: a lab plan (the pre-registration
                                  gate, the lever check); a lab batch opens
                                  only when the graded pre-registration names
                                  this file's sha256 (`plan-sha256: <64 hex>`,
                                  fvh.prereg.check_plan; DV5d)
    seed = <int>                  the base of the per-run seeds (required)
    tasks = ["<task id>", ...]
    repeats = <n>                 default 1
    attempts = <n>                default 1
    max_reissue = <n>             re-issues of an infra-failed id (default and
                                  most 3, DV4-PLAN §4.3 rule 3)
    system = "..." | system_file = "<course path>"
    instructions = "..." | instructions_file = "<course path>"
                                  the task material's instructions
                                  (ctx.material["instructions"])
    statement = "..."             ctx.statement (default: empty)
    lever_check = <bool>          the lab gate's lever check on every Verify
                                  (default: true for a lab plan, false otherwise;
                                  a lab plan cannot turn it off)
    statements = ["<course path>", ...]
                                  the statement files a sealed lab stratum waits
                                  on (fvh.statements, QPLAN §30 Q64): exactly the
                                  paths of expected/<ID>.statements; the batch
                                  opens only when each is committed with content
                                  other than its shipped form, and their committed
                                  sha256 go into the batch note and every run.json.
                                  Required when a task lies in a sealed stratum
    role = "pilot" | "confirmatory" | "descriptive"
                                  required when the tasks lie in a schema-2 local
                                  stratum (one with [[cluster]] roles: Lab alpha's,
                                  DVR4 plan section 3.8): a pilot plan's tasks are
                                  all pilot clusters'; a confirmatory or descriptive
                                  plan runs only under the committed freeze
    freeze = "<course path>"      the freeze file of a confirmatory or descriptive
                                  plan (fvh.prereg.check_roles: complete, on the
                                  current stratum, pilot and confirmatory clusters
                                  disjoint, the plan's tasks inside its role's
                                  clusters; a lab plan's PREREG block names its
                                  sha256 as `freeze-sha256: <64 hex>`); its sha256
                                  goes into the batch note
    gate = "<course path>"        the acceptance tool of a gated arm (Lab 3's gate
    gate_sha256 = "<64 hex>"      v2, harness/q/fvh_q/gate/gate_v2.py) and its
                                  pre-registered sha256: the batch refuses to open,
                                  and an attempt to start, when the file differs
    [task.<task id>]
    path = "<course path>"        the task form: a benchmark task file (its
                                  language from the suffix) or a crate task's
                                  directory (a Verus crate: Cargo.toml and src/;
                                  DV5c gaps lane): its src/**/*.rs are the editable
                                  files, its other files (Cargo.toml, frozen.rs)
                                  read-only companions staged with every
                                  verification, the directory the gate's target
    statement = "..."             optional: this task's ctx.statement (the
                                  plan's statement otherwise)
    min_verified = <n>            a crate task's pins for a gated arm's tool (gate
    symbols = ["<name>", ...]     v2's Pins; defaults 1 and none)
    [[arm]]
    name = "<arm>"                an id part
    family = <a fvh.budget family>  the Claude or the Qwen family
    rounds = <model calls per attempt>
    policy = "<module>:<name>"    the arm's policy class or renderer, imported
                                  from harness/ (fvh, fvh_q, fvh_r); "fvh:smoke"
                                  is fvh.backends.smoke_render
    construct = "sampler" | "seeded" | "model" | "agent"
                                  sampler: cls(ask, seed); seeded: cls(ask,
                                  seeds); model: fvh.backends.ModelPolicy over
                                  the transport with `policy` as the renderer;
                                  agent: an agent-mode arm (below), which names
                                  no policy
    turns, wall_s, gpu_s, tokens  optional per-run caps (defaults: turns =
                                  rounds + 1; wall_s and, for Qwen, gpu_s from
                                  the apparatus file's [defaults]; an agent arm
                                  takes wall_s and gpu_s only: its turns are its
                                  rounds)
    feedback = "none" | "spec"    optional: Lab 2 S1 reference-free feedback (D36);
                                  supplies baseline-filtered mutation scoring, vacuity and
                                  the delivery’s witness/body verdict on Verify.
    lab_code = "preserve" | "own"
                                  preserve (default): keep the task form’s executable code;
                                  own: this arm writes its own code (D38). Recorded and
                                  preserved by report --reverify.
    acceptance = "verify" | "gate"
                                  "gate" (Lab 3's arm G, QPLAN §28.5): every Verify
                                  runs the plan's gate (its gate_crate on the work
                                  copy, each instrument in a fresh verification
                                  container on agent provenance), a Stop is refused
                                  until the gate passes the current work copy, and
                                  the run ends when it does; "verify" (default, arm
                                  P and every other arm) the plain lab gate

Agent mode (construct = "agent"; the user's decision D8, DV5d; DV4-PLAN §3.5): the
Qwen family only (a Claude arm runs harness-executed until DV4 step 4c, D10). An
attempt is an agent session in a per-run container (fvh.backends.agent, which
composes scripts/mksandbox-run's library as scripts/contract_local.sh does): the
agent reads the brief TASK.md (the plan's instructions, the task's statement, the
files it may edit, the gate command it may run on them, and what happens when it
stops), edits the task's files with its own tools, and stops; `rounds` is its turn
cap, which is also the run's gate's call cap, and the n-th gated request carries
the attempt's n-th seed. Then:
  - the task is staged by src (a task file, or a crate card's src/**/*.rs editable
    and its other files read-only), so a lab card must be attested
    (sandbox/attested.toml); `open()` builds and self-tests every agent task's
    manifest first and refuses the batch on any problem;
  - what the agent returned is verified in a fresh verification container, on the
    task's work copy with the lab gate's lever check for a lab plan (the plain
    arm's outcome, "verify");
  - a gated arm ("gate", Lab 3's arm G under D17): the agent's stop is the arm's
    Verify. At every stop the plan's gate runs on the work copy (each instrument in
    a fresh verification container, provenance agent); when it passes the run
    ends "gate-pass"; when it does not, the stop is refused: a new session starts
    from the returned work copy (inline), its brief carrying the gate's verdict
    and reasons, with what is left of the attempt's turns, seeds, GPU-seconds and
    wall clock; when they are spent the run ends by that cap. The agent's own runs
    of the course tools inside its container are its tool calls, not Verifies:
    the harness's gate runs are the only verdicts it records. The outcome is the
    plain lab gate's verdict of the last work copy in both arms (Δ215);
  - each session's records go to seg-<k>/ (manifest.json, selftest.json,
    sandbox.json, the gate's gate.log.gz and gate-counts.json, the scanned
    transcript.jsonl.gz, its own returned/ and patch.diff); the run directory
    holds run.json (RunMeta, mode "agent"), inputs.*, returned/ and patch.diff
    (the changed files against the inputs), verify.json, and acceptance.jsonl (a
    gated arm's gate run at each stop);
  - live_run's ends map onto the ledger so that resume works and an interruption
    never becomes best-of-n: completed (0) is scored; a failed step (1) is
    infra-failed when the gate saw no model request (re-issuable; a self-test or
    manifest refusal also stops the batch) and truncated:container after one
    (scored); the run's wall clock during a command (124) is scored, ended by
    wall-clock, on the work copy as last returned (infra-failed before any
    request); Deferred (3) is deferred, and stops the batch, before any request,
    and truncated:host-memory after one. A session's gate writes its counts into
    seg-<k>/ as it goes, so `fvh resume` settles a runner killed outright from
    them (a gated request means output).

Seeds (DV4-PLAN §4.3 rule 3; the gate config of Δ202's open item): the n-th
model call of attempt <arm>/<task>/<repeat>/<attempt> gets
derive_seed(seed, id, n), a pure function of the plan's base seed and the
attempt id. So repeats are independent samples, and a re-issued id gets the
same seeds. For Qwen the run's gate sets them on the requests (the gate, not
the client, is authoritative); the plan's seeds must be pairwise distinct over
the plan (the runner refuses a plan where two calls would share one).

The run (one attempt), written to research/runs/<ID>/<run id>/:
  ledger      planned -> running -> scored | infra-failed | deferred
              (fvh.budget; scored is write-once)
  run.json    fvh.runlog.RunMeta (mode harness-executed), with the
              apparatus facts, the seeds, the instrument, the prompt hashes,
              the plan's sha256 and the pre-registration hash
  calls.jsonl one line per model call: seed, wall clock, the client's usage,
              the window verdict, an error; for Qwen the gate's own counts
              (calls, tokens, GPU-seconds) beside the client's; the message's
              bytes and, for a JSON request with a `feedback` field, that
              field's bytes and the equal cap's truncation flag
              (fvh.labalpha.message_accounting)
  actions.jsonl, observations.jsonl, verify.json   the executor's
  inputs.tar.gz, inputs.sha256   the task form as staged
  returned/, patch.diff          the final work copy and its diff
  transcript.jsonl.gz            the transport's streams
  gate.log.gz, gate-counts.json  the run's gate (Qwen)
  Every file of the run directory then goes through the secret scan
  (scan_run_dir, DV4-PLAN §5.7): a file with a credential shape is withheld,
  i.e. removed, with its name, size and sha256 in run.json's secret_scan, and
  the runner asks the human to rotate.

Between attempts (DV4-PLAN §4.3 rule 6, §4.4): a Claude window verdict
"defer" (Completion.window), a Deferred transport or a memory deferral stops
the batch cleanly; the ids not run stay planned (or move to deferred) and the
batch stays open for `fvh resume`. An apparatus mismatch stops the batch too:
its attempt is infra-failed (re-issuable once the pins are re-probed); a
transport or model gate that does not start is one. A Claude batch starts
only from a fresh recorded window event, otherwise its first call is a
sentinel (Δ148), recorded in the ledger and counted against the module's
claude_calls. An overage stop (a call whose event shows overage, or that
carries none) is sticky (DV5c fix round): its event goes to the window file,
an `overage-stop` note to the ledger, and no Claude call of any batch of the
module runs until a human checks the account and runs `fvh resume <ID>
--after-overage-check` (an `overage-cleared` note). A live Qwen batch checks
the model server against the apparatus pins (fvh.backends.gate.server_drift:
version, digests, the unit's settings) before its first attempt and refuses
on any difference. A call that ran counts against the run's meter and the
ledger even when its reply was discarded, and Ledger.used counts what
infra-failed or deferred attempts spent.

Interruption: a SIGINT or SIGTERM while an attempt runs ends it as
`truncated:interrupted` when the model had answered (scored, never
re-issued: an interruption must never become best-of-n), else infra-failed;
the batch stays open. A runner killed outright leaves its attempt running;
`fvh resume` first reconciles every running id the same way from what its run
directory holds (a model call recorded in calls.jsonl, actions.jsonl or the
gate's counts means output), then re-issues what fvh.budget.resume_order
lists, in plan order, and closes the batch when every id is settled.

  load_plan(path, root) -> Plan
  derive_seed(base, attempt_id, n) -> int
  Batch(root, module, plan, *, transports=None, runners=None, log=None,
        mem_gb=None)
      .open()                 the checks, the plan in the ledger, the open
                              anchor, the plan's copy and its note
      .run(ids=None) -> int   the attempts (exit code: 0 closed, 1 interrupted
                              or a run failed, 3 deferred or stopped)
  resume(root, module, **kw) -> int   also refuses (BatchError) when the
                              apparatus file is not the one the batch opened on
                              (unless new_apparatus records the change), on
                              drift, and when the re-issues would pass the
                              registry budget with what the ledger spent
  reconcile(root, module, ledger) -> list[(id, state)]

`transports(family, run_dir, seeds, caps)` and `runners(task, lang)` replace
the live transport and ContainerRunner (CI's tests use fakes); live, the
runner takes the GPU calendar lock for a batch with a Qwen arm. Frozen (guard
rule 2f), standard library only.
"""

import dataclasses
import gzip
import hashlib
import importlib
import json
import os
import re
import shutil
import signal
import sys
import time
import tempfile
import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from fvh import (apparatus, backends, budget, executor, labalpha, prereg, protocol, runlog,
                 statements, tools)
from fvh.records import VERDICTS as VERDICT_WORDS

__all__ = ["ArmPlan", "Batch", "BatchError", "CONSTRUCTS", "Interrupted", "Plan", "derive_seed",
           "load_plan", "reconcile", "resume", "scan_run_dir", "secret_hits"]

CONSTRUCTS = ("sampler", "seeded", "model", "agent")
AGENT_ARM_CAPS = ("wall_s", "gpu_s")
AGENT_MAX_TURNS = 200           # dvl.sandbox's [agent] turns bound
AGENT_MIN_WALL_S = 120          # a session needs this much of the wall clock to start
PLAN_KEYS = {"lab", "seed", "tasks", "repeats", "attempts", "max_reissue", "system",
             "system_file", "instructions", "instructions_file", "statement", "lever_check",
             "task", "arm", "statements", "gate", "gate_sha256", "role", "freeze",
             "interleave"}
ARM_KEYS = {"name", "family", "rounds", "policy", "construct", "turns", "wall_s", "gpu_s",
            "tokens", "acceptance", "lab_code", "feedback"}
TASK_KEYS = {"path", "statement", "min_verified", "symbols"}
ACCEPTANCE = ("verify", "gate")
CRATE_MAX_FILES = 64
LANGS = {".dfy": "dafny", ".rs": "verus"}
SENTINEL_MSG = ('Propose exactly one action: a stop action whose reason is "done" and whose '
                'note is "sentinel".')
SENTINEL_SYSTEM = ("You are a test responder for a harness check. Answer only through the "
                   "structured output, with one JSON object that matches its schema.")
EXIT_OK, EXIT_FAIL, EXIT_REFUSED = 0, 1, 3
INTERRUPTED = "truncated:interrupted"
# The credential formats of dvl.sandbox's secret scan (DV4-PLAN §5.7), by id;
# tests/sandbox keeps the two lists in step.
SECRET_PATTERNS = (
    ("anthropic-token", re.compile(rb"sk-ant-[a-z]{2,6}\d{2}-[A-Za-z0-9_-]{20,}")),
    ("oauth-json-key", re.compile(rb'"(accessToken|refreshToken)"\s*:\s*"[^"]{8,}"')),
    ("bearer-header", re.compile(rb"(?i)authorization:\s*bearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    ("private-key", re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github-token", re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
)


class BatchError(RuntimeError):
    """A plan or a batch the runner refuses (exit 3)."""


class Interrupted(BaseException):
    """SIGINT or SIGTERM while a batch runs."""


def secret_hits(data: bytes) -> list[str]:
    """The ids of the credential formats found in `data` (never the content)."""
    return sorted({name for name, rx in SECRET_PATTERNS if rx.search(data)})


def derive_seed(base: int, attempt_id: str, n: int) -> int:
    """The n-th call's seed of an attempt: a pure function of the plan's base seed
    and the attempt id (31 bits, never 0)."""
    h = hashlib.sha256(f"fvh-seed/{int(base)}/{attempt_id}/{int(n)}".encode()).digest()
    return (int.from_bytes(h[:4], "big") & 0x7FFFFFFF) or 1


# =====================================================================================
# The plan
# =====================================================================================

@dataclass(frozen=True)
class ArmPlan:
    name: str
    family: str
    rounds: int
    policy: str
    construct: str
    caps: dict = field(default_factory=dict)
    acceptance: str = "verify"
    lab_code: str = "preserve"
    feedback: str = "none"

    def arm(self) -> budget.Arm:
        return budget.Arm(self.name, self.family, self.rounds)

    @property
    def agent(self) -> bool:
        """An agent-mode arm (construct "agent")."""
        return self.construct == "agent"

    def __hash__(self):
        return hash((self.name, self.family, self.rounds))


@dataclass(frozen=True)
class Plan:
    path: Path
    sha256: str
    text: str
    lab: str
    seed: int
    tasks: dict                 # id -> (course path, lang)
    order: tuple                # the task ids in plan order
    arms: tuple
    repeats: int
    attempts: int
    max_reissue: int
    system: str
    instructions: str
    statement: str
    lever_check: bool
    task_statements: dict = field(default_factory=dict)
    statements: tuple = ()
    gate: str = ""
    gate_sha256: str = ""
    task_pins: dict = field(default_factory=dict)   # id -> (min_verified, symbols)
    role: str = ""              # a schema-2 stratum's plan role (fvh.prereg.check_roles)
    freeze: str = ""            # the freeze file of a confirmatory/descriptive plan
    interleave: tuple = ()      # arm-name groups run adjacent per task and repeat (Δ298)

    def __hash__(self):
        return hash(self.sha256)

    def is_crate(self, root, task) -> bool:
        return (Path(root) / self.tasks[task][0]).is_dir()

    def statement_of(self, task) -> str:
        return self.task_statements.get(task, self.statement)

    def items(self) -> list:
        return budget.enumerate_plan([a.arm() for a in self.arms], list(self.order),
                                     repeats=self.repeats, attempts=self.attempts,
                                     interleave=self.interleave)

    def arm(self, name) -> ArmPlan:
        for a in self.arms:
            if a.name == name:
                return a
        raise KeyError(name)

    def families(self) -> set:
        return {a.family for a in self.arms}

    def seeds(self, attempt_id: str) -> list:
        arm = self.arm(attempt_id.split("/")[0])
        return [derive_seed(self.seed, attempt_id, n) for n in range(arm.rounds)]


def _int(v, what, low=0):
    if isinstance(v, bool) or not isinstance(v, int) or v < low:
        raise BatchError(f"{what} must be an integer >= {low}")
    return v


def _course_text(root, rel, what):
    if not isinstance(rel, str) or not rel or rel.startswith("/") or ".." in rel.split("/"):
        raise BatchError(f"{what} must be a course-relative path")
    p = Path(root) / rel
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise BatchError(f"{what} {rel}: unreadable ({type(e).__name__})") from None


def load_plan(path, root) -> Plan:
    """The plan of a batch, checked (BatchError naming the problem)."""
    path = Path(path)
    try:
        raw = path.read_bytes()
        data = tomllib.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise BatchError(f"{path}: unreadable plan ({type(e).__name__})") from None
    unknown = sorted(set(data) - PLAN_KEYS)
    if unknown:
        raise BatchError(f"{path}: unknown key(s) " + ", ".join(unknown))
    if "seed" not in data:
        raise BatchError(f"{path}: a plan names its base seed (seed = <int>): every run's "
                         "seeds derive from it")
    seed = _int(data["seed"], "seed")
    order = data.get("tasks", [])
    if not isinstance(order, list) or not order or not all(isinstance(t, str) for t in order):
        raise BatchError(f"{path}: tasks is a non-empty list of task ids")
    if len(set(order)) != len(order):
        raise BatchError(f"{path}: a task id is listed twice")
    ttab = data.get("task", {})
    if not isinstance(ttab, dict):
        raise BatchError(f"{path}: [task.<id>] tables give each task's path")
    tasks, task_statements, task_pins = {}, {}, {}
    for t in order:
        entry = ttab.get(t)
        if not isinstance(entry, dict) or set(entry) - TASK_KEYS or "path" not in entry:
            raise BatchError(f"{path}: task {t} needs a [task.{t}] table with a path (and "
                             "optionally a statement)")
        rel = entry["path"]
        if isinstance(rel, str) and rel and not rel.startswith("/") \
                and ".." not in rel.split("/") and (Path(root) / rel).is_dir():
            crate_files(root, rel)                      # refuses a directory that is no crate
            lang = "verus"
        else:
            _course_text(root, rel, f"task {t}'s path")
            lang = LANGS.get(Path(rel).suffix)
            if lang is None:
                raise BatchError(f"{path}: task {t}'s path {rel} is not a .dfy or .rs file or "
                                 "a crate task's directory")
        mv = entry.get("min_verified", 1)
        syms = entry.get("symbols", [])
        if isinstance(mv, bool) or not isinstance(mv, int) or mv < 0 or not isinstance(syms, list) \
                or not all(isinstance(s, str) and s for s in syms):
            raise BatchError(f"{path}: task {t}: min_verified is an integer >= 0 and symbols a "
                             "list of names")
        task_pins[t] = (mv, tuple(syms))
        if not isinstance(entry.get("statement", ""), str):
            raise BatchError(f"{path}: task {t}'s statement is a string")
        tasks[t] = (rel, lang)
        if "statement" in entry:
            task_statements[t] = entry["statement"]
    extra = sorted(set(ttab) - set(order))
    if extra:
        raise BatchError(f"{path}: [task] tables for ids not in tasks: " + ", ".join(extra))
    arms = []
    for i, a in enumerate(data.get("arm", [])):
        if not isinstance(a, dict):
            raise BatchError(f"{path}: [[arm]] #{i + 1} is not a table")
        bad = sorted(set(a) - ARM_KEYS)
        if bad:
            raise BatchError(f"{path}: arm #{i + 1}: unknown key(s) " + ", ".join(bad))
        agent = a.get("construct") == "agent"
        for k in ("name", "family", "rounds", "construct") + (() if agent else ("policy",)):
            if k not in a:
                raise BatchError(f"{path}: arm #{i + 1} has no {k}")
        if agent:
            if a["family"] != budget.QWEN:
                raise BatchError(f"{path}: arm {a['name']}: an agent-mode arm is a Qwen arm (a "
                                 "Claude arm runs harness-executed until DV4 step 4c)")
            if "policy" in a:
                raise BatchError(f"{path}: arm {a['name']}: an agent-mode arm names no policy "
                                 "(the agent works with its own tools)")
            extra = sorted(k for k in ("turns", "tokens") if k in a)
            if extra:
                raise BatchError(f"{path}: arm {a['name']}: an agent-mode arm's caps are wall_s "
                                 f"and gpu_s ({', '.join(extra)} refused: its turns are its rounds)")
            if isinstance(a["rounds"], int) and not isinstance(a["rounds"], bool) \
                    and a["rounds"] > AGENT_MAX_TURNS:
                raise BatchError(f"{path}: arm {a['name']}: an agent-mode arm has at most "
                                 f"{AGENT_MAX_TURNS} turns (rounds)")
            a = dict(a, policy="")
        try:
            budget.Arm(a["name"], a["family"], a["rounds"])
        except (TypeError, ValueError) as e:
            raise BatchError(f"{path}: arm #{i + 1}: {e}") from None
        if a.get("acceptance", "verify") not in ACCEPTANCE:
            raise BatchError(f"{path}: arm {a['name']}: acceptance is one of "
                             + ", ".join(ACCEPTANCE))
        if a.get("feedback", "none") not in ("none", "spec"):
            raise BatchError(f"{path}: arm {a['name']}: feedback is none or spec")
        if a.get("feedback", "none") == "spec" and (agent or a.get("acceptance", "verify") != "verify"):
            raise BatchError(f"{path}: specification feedback requires a policy arm with verify acceptance")
        if a.get("lab_code", "preserve") not in ("preserve", "own"):
            raise BatchError(f"{path}: arm {a['name']}: lab_code is preserve or own")
        if a["construct"] not in CONSTRUCTS:
            raise BatchError(f"{path}: arm {a['name']}: construct is one of "
                             + ", ".join(CONSTRUCTS))
        if a["construct"] == "sampler" and a["rounds"] != 1:
            raise BatchError(f"{path}: arm {a['name']}: a sampler arm makes one call per "
                             "attempt (rounds = 1); its budget is in attempts")
        if not agent and (not isinstance(a["policy"], str) or not re.fullmatch(
                r"[A-Za-z_][\w.]*:[A-Za-z_]\w*", a["policy"])):
            raise BatchError(f"{path}: arm {a['name']}: policy is \"<module>:<name>\"")
        caps = {}
        for k in ("turns", "tokens"):
            if k in a:
                caps[k] = _int(a[k], f"arm {a['name']}'s {k}", 1)
        for k in ("wall_s", "gpu_s"):
            if k in a:
                v = a[k]
                if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
                    raise BatchError(f"arm {a['name']}'s {k} must be a number > 0")
                caps[k] = float(v)
        if agent and caps.get("wall_s", 0) > 4 * 3600:
            raise BatchError(f"{path}: arm {a['name']}: an agent session's wall clock is at most "
                             "4 h (wall_s <= 14400)")
        if agent and "wall_s" in caps and caps["wall_s"] < AGENT_MIN_WALL_S:
            raise BatchError(f"{path}: arm {a['name']}: an agent session needs at least "
                             f"{AGENT_MIN_WALL_S} s of wall clock to start (wall_s >= "
                             f"{AGENT_MIN_WALL_S})")
        arms.append(ArmPlan(a["name"], a["family"], a["rounds"], a["policy"], a["construct"],
                            caps, a.get("acceptance", "verify"), a.get("lab_code", "preserve"),
                            a.get("feedback", "none")))
    if not arms:
        raise BatchError(f"{path}: a plan has at least one [[arm]]")
    if len({a.name for a in arms}) != len(arms):
        raise BatchError(f"{path}: an arm name is used twice")
    max_reissue = _int(data.get("max_reissue", budget.MAX_REISSUE), "max_reissue")
    if max_reissue > budget.MAX_REISSUE:
        raise BatchError(f"{path}: max_reissue is at most {budget.MAX_REISSUE} (DV4-PLAN §4.3)")

    def text_of(key):
        if key in data and f"{key}_file" in data:
            raise BatchError(f"{path}: give {key} or {key}_file, not both")
        if f"{key}_file" in data:
            return _course_text(root, data[f"{key}_file"], f"{key}_file")
        v = data.get(key, "")
        if not isinstance(v, str):
            raise BatchError(f"{path}: {key} is a string")
        return v
    lab = data.get("lab", "")
    if not isinstance(lab, str):
        raise BatchError(f"{path}: lab is a string")
    lever = data.get("lever_check", bool(lab))
    if not isinstance(lever, bool):
        raise BatchError(f"{path}: lever_check is true or false")
    if lab and not lever:
        raise BatchError(f"{path}: a lab plan always runs the lab gate's lever check (Δ182): "
                         "lever_check = false is refused when lab is set")
    statement = data.get("statement", "")
    if not isinstance(statement, str):
        raise BatchError(f"{path}: statement is a string")
    stm = data.get("statements", [])
    if not isinstance(stm, list) or not all(isinstance(s, str) and s for s in stm) \
            or len(set(stm)) != len(stm):
        raise BatchError(f"{path}: statements is a list of distinct course paths")
    sealed = [t for t in order if _in_sealed_stratum(root, tasks[t][0])]
    if sealed and not stm:
        raise BatchError(f"{path}: task(s) {', '.join(sealed)} lie in a sealed stratum: the plan "
                         "names its statement files (statements = [...], QPLAN §30 Q64)")
    gate, gate_sha = data.get("gate", ""), data.get("gate_sha256", "")
    gated = [a.name for a in arms if a.acceptance == "gate"]
    if gated or gate or gate_sha:
        if not gated:
            raise BatchError(f"{path}: gate and gate_sha256 serve a gated arm "
                             "(acceptance = \"gate\"), and no arm is gated")
        if not (isinstance(gate, str) and gate.startswith("harness/") and gate.endswith(".py")):
            raise BatchError(f"{path}: arm(s) {', '.join(gated)} are gated: gate names the "
                             "acceptance tool, a course path harness/….py")
        _course_text(root, gate, "gate")
        if not (isinstance(gate_sha, str) and re.fullmatch(r"[0-9a-f]{64}", gate_sha)):
            raise BatchError(f"{path}: gate_sha256 is the pre-registered sha256 of {gate}")
        bad = [t for t in order if not (Path(root) / tasks[t][0]).is_dir()]
        if bad:
            raise BatchError(f"{path}: a gated arm runs a crate-scale gate: task(s) "
                             f"{', '.join(bad)} are not crate tasks")
    role, frz = data.get("role", ""), data.get("freeze", "")
    if role not in ("",) + prereg.PLAN_ROLES:
        raise BatchError(f"{path}: role is one of " + ", ".join(prereg.PLAN_ROLES))
    if not isinstance(frz, str):
        raise BatchError(f"{path}: freeze is a course path")
    if frz:
        _course_text(root, frz, "freeze")
    inter = data.get("interleave", [])
    if not isinstance(inter, list) or not all(
            isinstance(g, list) and g and all(isinstance(n, str) for n in g) for g in inter):
        raise BatchError(f"{path}: interleave is a list of arm-name groups")
    if role == "confirmatory" and {"best", "best-raw"} <= {a.name for a in arms} \
            and ["best", "best-raw"] not in inter:
        raise BatchError(f"{path}: a confirmatory plan interleaves its two primary arms "
                         "(interleave = [[\"best\", \"best-raw\"]]): a pause at the GPU "
                         "ceiling must leave whole pairs (Δ298)")
    plan = Plan(path=path, sha256=hashlib.sha256(raw).hexdigest(), text=raw.decode("utf-8"),
                lab=lab, seed=seed, tasks=tasks, order=tuple(order), arms=tuple(arms),
                repeats=_int(data.get("repeats", 1), "repeats", 1),
                attempts=_int(data.get("attempts", 1), "attempts", 1), max_reissue=max_reissue,
                system=text_of("system"), instructions=text_of("instructions"),
                statement=statement, lever_check=lever, task_statements=task_statements,
                statements=tuple(stm), gate=gate, gate_sha256=gate_sha, task_pins=task_pins,
                role=role, freeze=frz, interleave=tuple(tuple(g) for g in inter))
    try:
        items = plan.items()
    except (ValueError, budget.BudgetError) as e:
        raise BatchError(f"{path}: {e}") from None
    seen = {}
    for p in items:
        for n, s in enumerate(plan.seeds(p.id)):
            if s in seen:
                raise BatchError(f"{path}: two calls would share the seed {s} ({seen[s]} and "
                                 f"{p.id} call {n}): choose another base seed")
            seen[s] = f"{p.id} call {n}"
    return plan


def crate_files(root, rel) -> tuple:
    """(editable, companions) of a crate task's directory: its src/**/*.rs, and its
    other regular files (Cargo.toml, frozen.rs, …), as course paths; BatchError for a
    directory that is not a crate task (no Cargo.toml or src/lib.rs, a link, a file
    that is not UTF-8, more than CRATE_MAX_FILES files)."""
    d = Path(root) / rel
    if not (d / "Cargo.toml").is_file() or not (d / "src" / "lib.rs").is_file():
        raise BatchError(f"{rel}: a crate task's directory holds Cargo.toml and src/lib.rs")
    ed, co = [], []
    for f in sorted(d.rglob("*")):
        if f.is_symlink():
            raise BatchError(f"{rel}: a crate task holds no link ({f.relative_to(d)})")
        if not f.is_file() or "target" in f.relative_to(d).parts:
            continue
        r = f"{rel}/{f.relative_to(d).as_posix()}"
        try:
            f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            raise BatchError(f"{r}: unreadable or not UTF-8") from None
        (ed if f.relative_to(d).parts[0] == "src" and f.suffix == ".rs" else co).append(r)
    if len(ed) + len(co) > CRATE_MAX_FILES:
        raise BatchError(f"{rel}: more than {CRATE_MAX_FILES} files")
    return tuple(ed), tuple(co)


def _in_sealed_stratum(root, rel) -> bool:
    """A task path inside a local stratum whose STRATUM.toml names a sealed archive."""
    m = re.match(r"^bench/local/([qr])/([^/]+)/", rel)
    if not m:
        return False
    p = Path(root) / "bench" / "local" / m.group(1) / m.group(2) / "STRATUM.toml"
    try:
        return bool(tomllib.loads(p.read_text(encoding="utf-8")).get("archive"))
    except (OSError, ValueError):
        return False


def _import_gate(root, rel):
    """The acceptance tool's module (the plan's gate), imported from harness/ by its
    dotted name (harness/q/fvh_q/gate/gate_v2.py -> fvh_q.gate.gate_v2)."""
    parts = PurePosixPath(rel).with_suffix("").parts
    if len(parts) < 3 or parts[0] != "harness" or parts[1] not in ("q", "r"):
        raise BatchError(f"gate {rel}: a learner gate lives under harness/q/ or harness/r/")
    base = str(Path(root) / "harness" / parts[1])
    if base not in sys.path:
        sys.path.insert(0, base)
    try:
        mod = importlib.import_module(".".join(parts[2:]))
    except Exception as e:                            # the learner's file: any failure refuses
        raise BatchError(f"gate {rel} cannot be imported: {type(e).__name__}: {e}") from None
    for name in ("gate_crate", "CrateTarget", "Pins", "render"):
        if not hasattr(mod, name):
            raise BatchError(f"gate {rel} has no {name}")
    return mod


def _import_policy(root, spec):
    mod_name, attr = spec.split(":", 1)
    if spec == "fvh:smoke":
        return backends.smoke_render, Path(backends.__file__)
    for d in (Path(root) / "harness", Path(root) / "harness" / "q", Path(root) / "harness" / "r"):
        if str(d) not in sys.path:
            sys.path.append(str(d))
    try:
        mod = importlib.import_module(mod_name)
        obj = getattr(mod, attr)
    except (ImportError, AttributeError) as e:
        raise BatchError(f"policy {spec}: {type(e).__name__}: {e}") from None
    return obj, Path(mod.__file__)


# =====================================================================================
# The transport wrapper: call records, streams, the gate's counts
# =====================================================================================

class RecordingTransport:
    """A transport whose every call is recorded in the run directory's calls.jsonl;
    for Qwen the gate's counts after each call give the call's GPU-seconds (the
    budget's count, DV4-PLAN §4.1)."""

    def __init__(self, inner, run_dir, *, gate=None, seeds=()):
        self.inner = inner
        self.family = getattr(inner, "family", "?")
        self.run_dir = Path(run_dir)
        self.gate = gate
        self.seeds = list(seeds)
        self.n = 0
        self.streams = []
        self.last = None
        self.overage = None           # an overage stop: {"event", "reason"} (DV5c)
        self.findings = []
        self._gate_calls = 0
        self._gate_gpu = 0.0

    def _log(self, rec):
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with (self.run_dir / "calls.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")

    def complete(self, message, *, system="", seed=None):
        if self.gate is None and seed is None and self.n < len(self.seeds):
            seed = self.seeds[self.n]
        n, t0 = self.n, time.monotonic()
        self.n += 1
        rec = {"n": n, "seed": seed, "family": self.family, "message_sha256":
               hashlib.sha256(message.encode("utf-8")).hexdigest(),
               **labalpha.message_accounting(message)}   # bytes; a request's feedback size
               # and the equal cap's truncation flag (Lab alpha's resource accounting)
        if hasattr(self.inner, "last_raw"):
            self.inner.last_raw = None
        try:
            c = self.inner.complete(message, system=system, seed=seed)
        except BaseException as e:
            rec.update(error=f"{type(e).__name__}: {e}"[:300],
                       had_output=bool(getattr(e, "had_output", False)),
                       wall_s=round(time.monotonic() - t0, 3))
            if getattr(e, "ran", False):
                rec["ran"] = True
            if getattr(e, "overage", False):
                self.overage = {"event": getattr(e, "rate_limit", None),
                                "reason": f"{e}"[:300]}
                rec["window"] = ["stop", self.overage["reason"]]
            raw = getattr(self.inner, "last_raw", None)
            if raw:
                self.streams.append(raw)
            self._gate_delta(rec)
            self._log(rec)
            raise
        if c.raw:
            self.streams.append(c.raw)
        tin, tout = c.tokens()
        rec.update(wall_s=c.wall_s, client_usage={"input_tokens": tin, "output_tokens": tout},
                   turns=c.turns, window=list(c.window), had_output=True)
        gpu = self._gate_delta(rec)
        if gpu is not None:
            c = dataclasses.replace(c, gpu_s=gpu)
        self._log(rec)
        self.last = c
        return c

    def _gate_delta(self, rec):
        if self.gate is None:
            return None
        cnt = self.gate.counts()
        calls, gpu = int(cnt.get("calls") or 0), float(cnt.get("gpu_s") or 0.0)
        d_calls, d_gpu = calls - self._gate_calls, round(gpu - self._gate_gpu, 3)
        self._gate_calls, self._gate_gpu = calls, gpu
        rec["gate"] = {"calls": d_calls, "gpu_s": d_gpu, "total_calls": calls,
                       "prompt_tokens": cnt.get("prompt_tokens"),
                       "output_tokens": cnt.get("output_tokens"),
                       "capped": cnt.get("capped"), "ctx_saturated": cnt.get("ctx_saturated")}
        if d_calls > 1:
            self.findings.append(f"unattributed-calls:{d_calls - 1}")
        return d_gpu


# =====================================================================================
# The batch
# =====================================================================================

def _utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _scored_state(outcome):
    if runlog.scored(outcome):
        return "scored"
    return "deferred" if outcome == "deferred" else "infra-failed"


class Batch:
    """One batch of a plan (module docstring)."""

    def __init__(self, root, module, plan: Plan, *, transports=None, runners=None, log=None,
                 mem_gb=None, app=None, agent=None):
        self.root = Path(root)
        self.module = module
        self.plan = plan
        self.transports = transports
        self.runners = runners
        self.agent = agent            # the agent-mode route (fvh.backends.agent.LiveAgent's
                                      # interface); None: the live one, built when first used
        # fixed here, not read off self.agent: open()'s preflight builds the live agent
        # route, and the batch is still live (the calendar lock, the server check, the
        # state reap and the unload; DV5d review fix)
        self._live = transports is None and agent is None
        self.say = log or (lambda m: print(f"fvh: {m}", flush=True))
        self.mem_gb = mem_gb
        self.app = app if app is not None else apparatus.load(root=self.root)
        self.ledger = budget.Ledger(budget.ledger_path(self.root, module))
        self.facts = apparatus.git_facts(self.root)
        self.prereg = ""
        self.freeze_sha256 = ""      # the committed freeze of a confirmatory/descriptive plan
        self.watch = budget.OverageWatch(self.app.window())
        self.window_file = self.root / budget.WINDOW_FILE
        self.stop = None              # why the batch stops between attempts
        self.server = None            # the model server's facts (server_check)
        self._sources = {}
        self.statements = {}          # path -> committed sha256 (the statements pin)
        self._gate_mod = None
        self._calendar = None         # the GPU calendar lock while a Qwen batch runs

    # --- the batch's files -------------------------------------------------------

    @property
    def batches_dir(self) -> Path:
        return self.ledger.path.parent / "batches"

    def _registry_budget(self):
        return budget.registry_budget(self.root, self.module)

    @property
    def live(self) -> bool:
        """No test route was injected at construction: the live model server, lock and
        unload (the live agent route built later by open() does not change it)."""
        return self._live

    def open(self) -> int:
        """Check, plan, anchor; keep the plan's copy and its note (returns the ids)."""
        for arm in self.plan.arms:                    # an arm that cannot be built refuses
            if not arm.agent:                         # the batch before anything is written
                _import_policy(self.root, arm.policy)
        self.preflight_agents()
        if self.plan.lab:
            try:
                self.prereg = prereg.check(self.root, self.module)
                prereg.check_plan(self.root, self.module, self.plan.sha256)
            except prereg.PreregRefused as e:
                raise BatchError(str(e)) from None
        try:
            frozen = prereg.check_roles(self.root, self.module, self.plan)
        except prereg.PreregRefused as e:
            raise BatchError(str(e)) from None
        self.freeze_sha256 = frozen["sha256"] if frozen else ""
        self.check_statements()
        self.check_gate()
        if budget.CLAUDE in self.plan.families():
            held = self._overage_held()
            if held:
                raise BatchError(held)
        items = self.plan.items()
        try:
            ledger = budget.open_batch(self.root, self.module, items,
                                       course_commit=self.facts["course_commit"],
                                       require_git=True)
        except (budget.AnchorError, budget.BudgetError, budget.LedgerError) as e:
            raise BatchError(str(e)) from None
        self.ledger = ledger
        seq = ledger.head()[0]
        bid = f"b{seq:05d}-{self.plan.sha256[:12]}"
        self.batches_dir.mkdir(parents=True, exist_ok=True)
        copy = self.batches_dir / f"{bid}.toml"
        copy.write_text(self.plan.text, encoding="utf-8")
        ledger.append({"kind": "note", "note": "batch-plan", "batch": bid,
                       "plan_sha256": self.plan.sha256,
                       "plan_file": copy.relative_to(ledger.path.parent).as_posix(),
                       "prereg_sha256": self.prereg, "lab": self.plan.lab,
                       "seed": self.plan.seed, "max_reissue": self.plan.max_reissue,
                       "apparatus_sha256": self.app.sha256,
                       **({"statements_sha256": dict(sorted(self.statements.items()))}
                          if self.statements else {}),
                       **({"gate": self.plan.gate, "gate_sha256": self.plan.gate_sha256}
                          if self.plan.gate else {}),
                       **({"role": self.plan.role} if self.plan.role else {}),
                       **({"freeze": self.plan.freeze, "freeze_sha256": self.freeze_sha256}
                          if self.freeze_sha256 else {})})
        return len(items)

    def check_statements(self):
        """The statements pin (fvh.statements): every file the plan names is the pin
        file's, committed with content other than its shipped form."""
        if not self.plan.statements:
            return
        try:
            pins = [p for p, _ in statements.read_pins(self.root, self.module)]
            got = statements.check(self.root, self.module)
        except statements.StatementsRefused as e:
            raise BatchError(str(e)) from None
        if sorted(pins) != sorted(self.plan.statements):
            raise BatchError("the plan's statements (" + ", ".join(self.plan.statements)
                             + f") are not the files expected/{self.module}.statements names ("
                             + ", ".join(pins) + ")")
        self.statements = got

    def check_gate(self):
        """A gated arm's tool is the pre-registered file (its sha256), importable."""
        if not self.plan.gate:
            return None
        f = self.root / self.plan.gate
        try:
            have = apparatus.file_sha256(f)
        except OSError:
            raise BatchError(f"gate {self.plan.gate} is missing") from None
        if have != self.plan.gate_sha256:
            raise BatchError(f"gate {self.plan.gate} is not the pre-registered one (sha256 "
                             f"{have[:16]}… here, {self.plan.gate_sha256[:16]}… in the plan)")
        if self._gate_mod is None:
            self._gate_mod = _import_gate(self.root, self.plan.gate)
        return self._gate_mod

    def _acceptance(self, task, target, runner):
        """The gated arm's acceptance callable (fvh.executor): the plan's gate_crate on
        the work copy's crate, each instrument through the attempt's runner (a fresh
        verification container, provenance agent)."""
        mod = self.check_gate()
        mv, syms = self.plan.task_pins.get(task, (1, ()))
        root = self.root

        def accept(work, paths):
            crate = Path(work) / target

            def run(instrument, t):
                return tools.run(instrument, t, root=root, runner=runner, provenance="agent")
            ran = []

            def recording(instrument, t):
                r = run(instrument, t)
                ran.append(r)
                return r
            tgt = mod.CrateTarget(task, "verus", str(crate),
                                  tuple(str(Path(work) / x) for x in paths),
                                  mod.Pins(int(mv), tuple(syms)))
            res = mod.gate_crate(tgt, run=recording)
            v = res.verdict
            return {"passed": v.word == "PASS", "verdict": mod.render(v),
                    "reasons": list(v.reasons), "results": ran}
        return accept

    # --- the window and the sentinel (Δ148) ----------------------------------------

    def _overage_held(self) -> str | None:
        """Why no Claude call may run: an overage stop recorded in the ledger and not
        cleared (DV5c fix round), or None."""
        held = self.ledger.overage_stop()
        if held is None:
            return None
        return (f"an overage stop is recorded (ledger seq {held.get('seq')}: "
                f"{held.get('reason', '')[:200]}); check the account's overage setting, then "
                f"clear it with `fvh resume {self.module} --after-overage-check`")

    def _record_overage(self, where, ov):
        """Persist an overage stop: the event that stopped the call in the window file
        (a later batch_may_start then refuses a start without a sentinel) and a sticky
        `overage-stop` note in the ledger (_overage_held)."""
        if ov.get("event"):
            budget.write_window(self.window_file, ov["event"])
        self.ledger.append({"kind": "note", "note": "overage-stop", "where": where,
                            "reason": (ov.get("reason") or "")[:300]})
        self.say(f"overage stop recorded ({where}): no Claude call runs until "
                 f"`fvh resume {self.module} --after-overage-check`")

    def _window_ok(self, ids) -> bool:
        if not any(self.plan.arm(i.split("/")[0]).family == budget.CLAUDE for i in ids):
            return True
        held = self._overage_held()
        if held:
            self.stop = held
            return False
        rule = self.app.window()
        may, why = budget.batch_may_start(self.window_file, rule)
        if may:
            self.say(f"window: {why}")
            return True
        used = self.ledger.used()[budget.CLAUDE]["calls"]
        have = int(self._registry_budget().get("claude_calls", 0) or 0)
        if used + 1 > have:
            self.stop = (f"the sentinel call would pass the registry's claude_calls = {have} "
                         f"({used} planned or spent)")
            return False
        self.say(f"window: {why}")
        tr = self._transport(budget.CLAUDE, self.batches_dir / "sentinel", [], budget.Caps())
        try:
            c = tr.complete(SENTINEL_MSG, system=SENTINEL_SYSTEM)
            v, r = c.window
            if c.rate_limit:
                budget.write_window(self.window_file, c.rate_limit)
        except (backends.TransportError, apparatus.ApparatusMismatch, backends.Deferred) as e:
            v, r = ("defer" if isinstance(e, backends.Deferred) else "stop",
                    f"{type(e).__name__}: {e}")
        self.ledger.sentinel(family=budget.CLAUDE, calls=1, verdict=v, reason=r[:300])
        if getattr(tr, "overage", None):
            self._record_overage("sentinel", tr.overage)
        self.say(f"sentinel: {v} ({r})")
        if v != "ok":
            self.stop = f"the sentinel's window verdict is {v}: {r}"
            return False
        return True

    # --- one attempt ---------------------------------------------------------------

    def _transport(self, family, run_dir, seeds, caps):
        if self.transports is not None:
            return self.transports(family, Path(run_dir), list(seeds), caps)
        if family == budget.QWEN:
            from fvh.backends import gate as G
            g = G.HostGate(run_dir, G.gate_config(self.app, seeds=seeds or [self.plan.seed],
                                                  calls=max(1, len(seeds)),
                                                  gpu_s=caps.gpu_s), root=self.root)
            url = g.start()
            inner = backends.build(budget.QWEN, self.app, gate_url=url + "/v1",
                                   state_base=_state_base("fvh-qwen-state"))
            t = RecordingTransport(inner, run_dir, gate=g, seeds=seeds)
            t.gate_handle = g
            return t
        from fvh.backends import claude as CL
        inner = CL.Transport(self.app.backend(budget.CLAUDE), window=self.app.window(),
                             overage=self.watch, state_base=_state_base("fvh-claude-state"))
        return RecordingTransport(inner, run_dir, seeds=seeds)

    def _runner(self, task_rel, lang, arm=None):
        if self.runners is not None:
            return self.runners(task_rel, lang)
        mem = self.mem_gb
        return tools.ContainerRunner(self.root, module=self.module, mem_gb=mem,
                                     lab_task=task_rel if self.plan.lever_check else None,
                                     lab_code=arm.lab_code if arm else "preserve")

    def _feedback(self, arm, task, rd, meter):
        if arm.feedback == "none":
            return None
        if self.module != "Q15":
            raise BatchError("spec feedback is a Q15 Lab 2 policy instrument")
        from fvh.labfeedback import SpecFeedback
        for rel in ("harness/fvh/labfeedback.py", "scripts/dvl/spec_feedback.py",
                    "harness/q/fvh_q/oracles.py"):
            source = self.root / rel
            self._sources[str(source)] = apparatus.file_sha256(source)
        def before_probe():
            cause = meter.cause(("wall_s",))
            if cause is not None:
                raise budget.CapReached(cause, "specification feedback reached the run's wall cap")
            return meter.snapshot().wall_s_left
        return SpecFeedback(self.root, task, records=rd / "feedback.jsonl",
                            before_probe=before_probe)

    def _caps(self, arm: ArmPlan) -> budget.Caps:
        d = self.app.defaults()
        return budget.Caps(calls=arm.rounds, tokens=arm.caps.get("tokens"),
                           turns=arm.caps.get("turns", arm.rounds + 1),
                           wall_s=arm.caps.get("wall_s", d.wall_s),
                           gpu_s=arm.caps.get("gpu_s", d.gpu_s if arm.family == budget.QWEN
                                              else None))

    def _policy(self, arm, tr, target, meter, seeds, prompts):
        obj, src = _import_policy(self.root, arm.policy)
        key = str(src)
        if key not in self._sources:
            self._sources[key] = apparatus.file_sha256(src)
        if arm.construct == "model":
            def render(s, c, b, _f=obj):
                m = _f(s, c, b)
                prompts.append(m)
                return m
            return backends.ModelPolicy(tr, render, meter=meter, system=self.plan.system,
                                        seeds=seeds), self._sources[key]
        base = backends.candidate_ask(tr, target=target, meter=meter, system=self.plan.system)

        def ask(prompt, seed, _b=base):
            prompts.append(prompt)
            return _b(prompt, seed)
        if arm.construct == "sampler":
            return obj(ask, seeds[0]), self._sources[key]
        return obj(ask, list(seeds)), self._sources[key]

    def attempt(self, aid: str) -> str:
        """Run one attempt; returns the ledger state it ends in."""
        arm_name, task, repeat, att = aid.split("/")
        arm = self.plan.arm(arm_name)
        if arm.agent:
            return self.agent_attempt(aid)
        target, lang = self.plan.tasks[task]
        crate = self.plan.is_crate(self.root, task)
        if crate:                             # a crate task: its sources editable, its
            ed, co = crate_files(self.root, target)   # companions read-only (DV5c gaps)
            staged = {p: (self.root / p).read_text(encoding="utf-8") for p in ed + co}
            editable, support = ed, {p: staged[p] for p in co}
            ctx_target = f"{target}/src/lib.rs"
        else:
            staged = {target: (self.root / target).read_text(encoding="utf-8")}
            editable, support, ctx_target = (target,), {}, target
        text = staged[ctx_target]
        seeds = self.plan.seeds(aid)
        rid = runlog.new_run_id(aid)
        rd = self.ledger.path.parent / rid
        while rd.exists():
            time.sleep(1.0)
            rid = runlog.new_run_id(aid)
            rd = self.ledger.path.parent / rid
        rd.mkdir(parents=True)
        self.ledger.move(aid, "running", max_reissue=self.plan.max_reissue, run_id=rid)
        runlog.write_inputs(rd, {p: x.encode("utf-8") for p, x in staged.items()})
        caps = self._caps(arm)
        meter = budget.Meter(caps)
        started = _utc()
        prompts, tr, res, detail, interrupted = [], None, None, "", False
        try:
            try:
                tr = self._transport(arm.family, rd, seeds, caps)
            except (backends.Deferred,) as e:
                return self._finish(aid, rd, rid, arm, task, lang, int(repeat), int(att), seeds,
                                    "deferred", "deferred", None, meter, tr, prompts, started,
                                    str(e), "", text=text, target=target, staged=staged)
            except Exception as e:                    # the gate or the transport did not start:
                # an apparatus fault (a digest that differs from its pin, the model server
                # down), so the batch stops, never burns the id's re-issues (DV5c fix round)
                return self._finish(aid, rd, rid, arm, task, lang, int(repeat), int(att), seeds,
                                    "apparatus-mismatch", "apparatus-mismatch", None, meter, tr,
                                    prompts, started,
                                    f"the transport did not start: {type(e).__name__}: {e}", "",
                                    text=text, target=target, staged=staged)
            policy, src_sha = self._policy(arm, tr, ctx_target, meter, seeds, prompts)
            ctx = protocol.Context(task_id=task, lang=lang, statement=self.plan.statement_of(task),
                                   editable=tuple(editable), readable=tuple(support),
                                   target=ctx_target,
                                   material={"instructions": self.plan.instructions,
                                             "text": text})
            runner = self._runner(target, lang, arm)
            accept = self._acceptance(task, target, runner) if arm.acceptance == "gate" else None
            ex = executor.Executor(ctx, {p: staged[p] for p in editable}, runner=runner,
                                   meter=meter, run_dir=rd, root=self.root,
                                   verify_target=target if crate else None,
                                   support_files=support, acceptance=accept,
                                   feedback=self._feedback(arm, target, rd, meter))
            try:
                res = ex.run(policy)
            except Interrupted:
                interrupted = True
            outcome = ended = None
            if interrupted:
                had = meter.outputs > 0 or ex.proposals > 0 or _had_output(rd)
                outcome = ended = INTERRUPTED if had else "infra-failed"
                detail = "the batch was interrupted during this attempt"
            else:
                outcome, ended, detail = res.outcome, res.ended_by, res.detail
            files = res.files if res is not None else dict(ex.files)
            verify = res.verify if res is not None else ex.last_verify
            return self._finish(aid, rd, rid, arm, task, lang, int(repeat), int(att), seeds,
                                outcome, ended, verify, meter, tr, prompts, started, detail,
                                src_sha, files=files, text=text, target=target,
                                interrupted=interrupted, staged=staged)
        finally:
            g = getattr(tr, "gate_handle", None)
            if g is not None and not getattr(tr, "gate_stopped", False):
                g.stop()                      # an attempt that ended before _finish: its
                _compress_gate_log(rd)        # run directory is scanned when resume settles it

    def _finish(self, aid, rd, rid, arm, task, lang, repeat, att, seeds, outcome, ended, verify,
                meter, tr, prompts, started, detail, src_sha, *, files=None, text=None,
                target=None, interrupted=False, staged=None):
        staged = staged if staged is not None else ({target: text} if target and text is not None
                                                    else {})
        findings = list(getattr(tr, "findings", []) or [])
        g = getattr(tr, "gate_handle", None)
        if g is not None:                     # the run's last call is made: its gate log is
            g.stop()                          # complete, and goes through the scan below
            _compress_gate_log(rd)
            tr.gate_stopped = True
        streams = list(getattr(tr, "streams", []) or [])
        if streams:
            blob = "".join(streams).encode("utf-8")
            (rd / "transcript.jsonl.gz").write_bytes(gzip.compress(blob, mtime=0))
        if files is not None and text is not None:
            ret = rd / "returned"
            for p, t in files.items():
                f = ret / p
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(t, encoding="utf-8")
            runlog.write_patch(rd, {p: x for p, x in staged.items() if p in files}, dict(files))
        scan = scan_run_dir(rd, exact=_secret_values(tr))
        hits = scan["hits"]
        if scan["withheld"]:
            findings.append("secret-scan:withheld")
            self.say(f"{aid}: a credential-shaped string ({', '.join(hits)}) in "
                     f"{', '.join(scan['withheld'])}: withheld (name, size and sha256 kept). "
                     "Rotate the credential: log the pinned CLI out, then in again "
                     "(DV4-PLAN §5.7 names the two commands)")
        facts = apparatus.collect(self.app, self.root)
        if self.server is not None:
            facts["model_server_found"] = self.server
        facts.update(seeds=list(seeds), plan_sha256=self.plan.sha256, arm_policy=arm.policy,
                     arm_construct=arm.construct, policy_source_sha256=src_sha,
                     instrument="vcheck --gate", lab_task=(target if self.plan.lever_check
                                                           and target else ""),
                     acceptance=arm.acceptance, lab_code=arm.lab_code, feedback=arm.feedback,
                     prompt_hashes=[apparatus.prompt_hash(system=self.plan.system, message=m,
                                                          schema=protocol.ACTION_SCHEMA,
                                                          policy_source=src_sha or "")
                                    for m in prompts])
        if arm.feedback == "spec":
            facts["feedback_sources_sha256"] = {
                str(Path(p).relative_to(self.root)): digest for p, digest in self._sources.items()
                if Path(p).name in ("labfeedback.py", "spec_feedback.py", "oracles.py")}
        if self.statements:
            facts["statements_sha256"] = dict(sorted(self.statements.items()))
        if arm.acceptance == "gate":
            facts.update(gate=self.plan.gate, gate_sha256=self.plan.gate_sha256)
        if target and (self.root / target).is_dir():
            facts["crate"] = target            # a crate task: fvh.report splits its inputs
        if tr is not None and getattr(tr, "last", None) is not None:
            facts["calls"] = [tr.last.apparatus]
        cnt = {}
        g = getattr(tr, "gate_handle", None)
        if g is not None:
            cnt = g.counts()
        usage = {**meter.usage(), "client_calls": meter.calls}
        if cnt:
            usage.update(gate_calls=cnt.get("calls"), gate_prompt_tokens=cnt.get("prompt_tokens"),
                         gate_output_tokens=cnt.get("output_tokens"), gate_gpu_s=cnt.get("gpu_s"))
            if cnt.get("ctx_saturated"):
                findings.append(f"ctx-saturated:{cnt['ctx_saturated']}")
            if int(cnt.get("calls") or 0) > meter.calls:
                findings.append(f"unattributed-calls:{int(cnt['calls']) - meter.calls}")
        findings = sorted(set(findings))
        cap = runlog.cap_finding(rd)
        if cap:
            findings.append(cap)
        meta = runlog.RunMeta(
            run_id=rid, module=self.module, arm=arm.name, task_id=task, lang=lang, attempt=att,
            repeat=repeat, mode="harness-executed", backend=arm.family, outcome=outcome,
            lab=self.plan.lab, ended_by=ended or "", verify=verify, usage=usage, apparatus=facts,
            course_commit=self.facts["course_commit"], course_dirty=self.facts["course_dirty"],
            inputs_sha256=runlog.inputs_tree_sha256({p: x.encode("utf-8")
                                                     for p, x in staged.items()})
            if staged else "",
            return_summary={"files_sha256": {p: protocol.text_sha256(t)
                                             for p, t in sorted((files or {}).items())}}
            if files is not None else {},
            secret_scan=scan,
            findings=tuple(findings), prereg_sha256=self.prereg, ledger_seq=self.ledger.head()[0],
            started=started, ended=_utc())
        runlog.write_meta(rd, meta)
        st = _scored_state(outcome)
        info = {"run_id": rid, "outcome": outcome, "calls": meter.calls,
                "gpu_s": round(meter.gpu_s, 3)}
        if detail:
            info["detail"] = detail[:300]
        self.ledger.move(aid, st, **info)
        self.say(f"{aid}: {outcome} ({ended or '-'}; {meter.calls} call(s)) -> {st}")
        if getattr(tr, "overage", None):
            self._record_overage(aid, tr.overage)
        if outcome == "apparatus-mismatch":
            self.stop = f"apparatus mismatch in {aid}: {detail}"
        elif outcome == "deferred":
            self.stop = f"deferred in {aid}: {detail}"
        last = getattr(tr, "last", None)
        if last is not None and last.rate_limit:
            budget.write_window(self.window_file, last.rate_limit)
        if last is not None and last.window and last.window[0] == "defer" and self.stop is None:
            self.stop = f"the window defers the batch: {last.window[1]}"
        if interrupted:
            raise Interrupted()
        return st

    # --- agent mode (construct "agent"; module docstring) ----------------------------

    def _agent_route(self):
        if self.agent is None:
            from fvh.backends import agent as AG
            self.agent = AG.LiveAgent(self.root, self.app, mem_gb=self.mem_gb, log=self.say)
        return self.agent

    def _agent_files(self, task):
        """(editable, companions, staged texts) of a task, as the attempt stages it."""
        target, _ = self.plan.tasks[task]
        if self.plan.is_crate(self.root, task):
            ed, co = crate_files(self.root, target)
        else:
            ed, co = (target,), ()
        staged = {p: (self.root / p).read_text(encoding="utf-8") for p in ed + co}
        return ed, co, staged

    def _agent_caps(self, arm: ArmPlan) -> dict:
        """The attempt's turns (its rounds), wall clock and GPU-seconds, the latter
        held to what the module's gpu_hours leave (as contract_local.sh's replay)."""
        d = self.app.defaults()
        gpu = arm.caps.get("gpu_s", d.gpu_s)
        try:
            hours = float(self._registry_budget().get("gpu_hours", 0) or 0)
            spent = sum(float(r.get("gpu_s") or 0) for r in self.ledger.read()
                        if r.get("kind") == "attempt"
                        and r.get("state") in ("scored", "infra-failed"))
            left = hours * 3600 - spent
            gpu = left if gpu is None else min(float(gpu), left)
        except budget.BudgetError:
            pass
        return {"turns": arm.rounds, "wall_s": float(arm.caps.get("wall_s", d.wall_s or 2700)),
                "gpu_s": None if gpu is None else float(gpu)}

    def agent_brief(self, arm: ArmPlan, task: str, *, refusal=None) -> str:
        """The agent's brief (TASK.md): the plan's instructions, the task's statement,
        its files, the gate command, what a stop does in this arm, and, for a refused
        stop of a gated arm, the gate's verdict, up to five reasons and the plain
        gate's verdict."""
        target, _ = self.plan.tasks[task]
        ed, co, _ = self._agent_files(task)
        out = [f"# Task {task}", ""]
        if self.plan.instructions.strip():
            out += [self.plan.instructions.strip(), ""]
        st = self.plan.statement_of(task).strip()
        if st:
            out += ["## The task", "", st, ""]
        out += ["## Files", "", "You may edit only these files (paths from /work):"]
        out += [f"- `{p}`" for p in ed]
        if co:
            out += ["", "These files are read-only; do not change them:"]
            out += [f"- `{p}`" for p in co]
        judge = ("by the lab gate, which also checks that the task's fixed parts are unchanged"
                 if self.plan.lever_check else "by the course's gate")
        if arm.acceptance == "gate":
            judge += ", and each stop by the acceptance gate"
        out += ["", "## Checking your work", "",
                f"From /work, `scripts/vcheck --gate {target}` runs the course's gate on the "
                "task. Run it as often as you need. It is not the judgement: your files are "
                f"judged outside this container, {judge}.", "", "## When you stop", ""]
        if arm.acceptance == "gate":
            out.append("When you stop, the acceptance gate runs on your files, outside this "
                       "container. If it does not pass, your stop is refused: a new session "
                       "starts from your files as they are, with the gate's report, until the "
                       "gate passes or the run's budget ends.")
        else:
            out.append("When you stop, your files are verified once more, outside this "
                       "container; that verification is the run's result.")
        if refusal is not None:
            # as the harness-executed arm G's observation (executor.py) and the Q18
            # chapter say: the gate's word, up to five reasons, the plain gate's verdict
            out += ["", "## Your last stop was refused", "",
                    f"The acceptance gate's verdict on your files: {refusal.get('verdict') or 'FAIL'}"]
            out += [f"- {r}" for r in (refusal.get("reasons") or [])[:5]]
            out += ["", f"The plain gate (`vcheck --gate`) on your files: "
                        f"{refusal.get('vcheck') or '-'}"]
            out += ["", "Continue from your files as they are now."]
        return "\n".join(out) + "\n"

    def _spec(self, aid, rid, k, task, brief, *, turns, seeds, wall_s, gpu_s, seg_dir, texts):
        from fvh.backends import agent as AG
        target, _ = self.plan.tasks[task]
        cid = re.sub(r"[^A-Za-z0-9._-]+", "-", f"{rid}-s{k}")
        cid = (cid[:40] + "-" + hashlib.sha256(cid.encode()).hexdigest()[:12]) if len(cid) > 64 \
            else cid
        fh = getattr(self._calendar, "fh", None)
        return AG.SegmentSpec(attempt_id=aid, run_id=cid, module=self.module, task=target,
                              brief=brief, turns=int(turns), seeds=tuple(seeds),
                              wall_s=float(wall_s), gpu_s=gpu_s, seg_dir=Path(seg_dir),
                              texts=texts, calendar_fd=fh.fileno() if fh is not None else None)

    def preflight_agents(self):
        """Every agent arm's first session, for every task, built and self-tested
        before the batch opens (an unattested card, a refused manifest): BatchError."""
        arms = [a for a in self.plan.arms if a.agent]
        if not arms:
            return
        try:
            route = self._agent_route()
        except backends.ModelDisabled as e:
            raise BatchError(str(e)) from None
        problems = []
        for arm in arms:
            caps = self._agent_caps(arm)
            for task in self.plan.order:
                spec = self._spec(f"{arm.name}/{task}/1/1", f"preflight-{arm.name}-{task}", 1, task,
                                  self.agent_brief(arm, task),
                                  turns=caps["turns"], seeds=[1] * caps["turns"],
                                  wall_s=caps["wall_s"], gpu_s=caps["gpu_s"],
                                  seg_dir=self.root / "unused", texts=None)
                problems += [f"{arm.name}/{task}: {p}" for p in route.preflight(spec)]
        if problems:
            raise BatchError("an agent-mode task's sandbox is refused: " + "; ".join(problems[:8])
                             + (f" (and {len(problems) - 8} more)" if len(problems) > 8 else ""))

    def _agent_verify(self, arm, task, files, support, target, lang, runner):
        """The verification of an agent's work copy: the lab gate (the plain arm), or
        the plan's gate (a gated arm). Returns (doc, acceptance or None)."""
        work = Path(tempfile.mkdtemp(prefix="work-"))
        try:
            for p, t in list(support.items()) + list(files.items()):
                f = work / p
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(t, encoding="utf-8")
            if arm.acceptance == "gate":
                accept = self._acceptance(task, target, runner)
                got = accept(work, tuple(sorted(set(support) | set(files))))
                results = list(got.get("results") or [])
                res = next((r for r in results if r.instrument == "vcheck --gate"), None)
                doc = executor.verdict_doc(res) if res is not None else {
                    "verdict": "error", "lines": [], "holes": [], "diagnostics": [],
                    "verified_count": 0}
                acc = {"passed": bool(got.get("passed")),
                       "verdict": str(got.get("verdict", ""))[:200],
                       "reasons": [str(x)[:300] for x in (got.get("reasons") or [])][:20],
                       "tools": len(results)}
                doc["acceptance"] = acc
            else:
                res = tools.run("vcheck --gate", work / target, root=self.root, runner=runner,
                                provenance="agent")
                doc, acc = executor.verdict_doc(res), None
        finally:
            shutil.rmtree(work, ignore_errors=True)
        doc["files_sha256"] = {p: protocol.text_sha256(t) for p, t in sorted(files.items())}
        return doc, acc

    def agent_attempt(self, aid: str) -> str:
        """Run one agent-mode attempt (module docstring); returns its ledger state."""
        from fvh.backends import agent as AG
        arm_name, task, repeat, att = aid.split("/")
        arm = self.plan.arm(arm_name)
        target, lang = self.plan.tasks[task]
        ed, co, staged = self._agent_files(task)
        support = {p: staged[p] for p in co}
        files = {p: staged[p] for p in ed}
        seeds = self.plan.seeds(aid)
        rid = runlog.new_run_id(aid)
        rd = self.ledger.path.parent / rid
        while rd.exists():
            time.sleep(1.0)
            rid = runlog.new_run_id(aid)
            rd = self.ledger.path.parent / rid
        rd.mkdir(parents=True)
        self.ledger.move(aid, "running", max_reissue=self.plan.max_reissue, run_id=rid)
        runlog.write_inputs(rd, {p: x.encode("utf-8") for p, x in staged.items()})
        caps = self._agent_caps(arm)
        started, t0 = _utc(), time.monotonic()
        st = {"segs": [], "briefs": [], "doc": None, "outcome": None, "ended": None,
              "detail": "", "findings": [], "stop": None, "calls": 0, "gpu_s": 0.0}
        interrupted = False
        try:
            self._agent_loop(aid, arm, task, target, lang, files, support, seeds, caps, rd, t0,
                             st)
        except Interrupted:
            interrupted = True
            had = st["calls"] > 0 or _had_output(rd)
            st["outcome"] = st["ended"] = INTERRUPTED if had else "infra-failed"
            st["detail"] = "the batch was interrupted during this attempt"
        finally:
            for d in rd.glob("seg-*"):
                AG.compress_gate_log(d)
        return self._agent_finish(aid, rd, rid, arm, task, lang, int(repeat), int(att), seeds,
                                  staged, ed, files, st, started, interrupted=interrupted)

    def _agent_loop(self, aid, arm, task, target, lang, files, support, seeds, caps, rd, t0, st):
        from fvh.backends import agent as AG
        route = self._agent_route()
        runner = None
        refusal, k = None, 0
        while True:
            k += 1
            left = caps["turns"] - st["calls"]
            wall_left = caps["wall_s"] - (time.monotonic() - t0)
            gpu_left = None if caps["gpu_s"] is None else caps["gpu_s"] - st["gpu_s"]
            end = ("call-cap" if left <= 0 else "wall-clock" if wall_left < AGENT_MIN_WALL_S
                   else "gpu-cap" if gpu_left is not None and gpu_left < 1 else None)
            if end is not None:
                st["ended"] = end
                if k == 1:                    # no session ran: nothing to score, and the
                    st["outcome"] = "deferred"    # batch stops (DV5d review fix)
                    gl = "-" if gpu_left is None else f"{gpu_left:.1f}"
                    st["detail"] = (f"no agent session could start: {end} (wall clock left "
                                    f"{wall_left:.0f} s, a session needs {AGENT_MIN_WALL_S} s; "
                                    f"GPU-s left {gl})")
                break
            brief = self.agent_brief(arm, task, refusal=refusal)
            st["briefs"].append(brief)
            spec = self._spec(aid, rd.name, k, task, brief, turns=left,
                              seeds=seeds[st["calls"]:st["calls"] + left], wall_s=wall_left,
                              gpu_s=gpu_left, seg_dir=rd / f"seg-{k}",
                              texts=None if k == 1 else dict(files))
            try:
                seg = route.run_segment(spec)
            except backends.Deferred as e:
                if st["calls"] == 0:
                    st["outcome"] = st["ended"] = "deferred"
                else:                         # the host ran short after model output
                    st["outcome"] = st["ended"] = "truncated:host-memory"
                st["detail"] = str(e)[:300]
                return
            st["segs"].append(seg)
            st["calls"] += seg.calls
            st["gpu_s"] += seg.gpu_s
            if seg.ctx_saturated:
                st["findings"].append(f"ctx-saturated:{seg.ctx_saturated}")
            if seg.withheld:
                st["findings"].append("secret-scan:withheld")
            if seg.deleted:                   # the return set restores a deleted file
                st["findings"].append("deleted:" + ",".join(seg.deleted))
            if seg.rejected:
                st["findings"].append(f"return-rejected:{len(seg.rejected)}")
            # a model request any session made (its Segment's counts, or the gate's
            # counts on disk): no re-issue after output (Δ208; DV5d review fix)
            had = st["calls"] > 0 or _had_output(rd)
            if seg.code != 0:
                if seg.ended_by in ("selftest-failed", "manifest-refused"):
                    st["stop"] = f"the agent sandbox of {aid} was refused: {seg.detail[:200]}"
                if not had:
                    st["outcome"] = st["ended"] = "infra-failed"
                    st["detail"] = f"{seg.ended_by}: {seg.detail}"[:300]
                    return
                if seg.code != 124:
                    st["outcome"] = st["ended"] = (
                        "truncated:host-memory" if seg.ended_by == AG.KILLED_MEMORY
                        else "truncated:container")
                    st["detail"] = f"{seg.ended_by}: {seg.detail}"[:300]
                    return
            if not had:                       # the session ended with no model request:
                st["outcome"] = st["ended"] = "infra-failed"     # no output, re-issuable
                st["detail"] = (f"the agent session made no model request ({seg.ended_by}, "
                                f"agent {seg.agent_end or '-'})")[:300]
                return
            for p, t in seg.returned.items():
                if p in files:
                    files[p] = t
            if seg.code == 124:
                end = "wall-clock"
            elif seg.agent_end == "wall-clock":
                end = "wall-clock"
            elif seg.capped and spec.gpu_s is not None and seg.gpu_s >= spec.gpu_s:
                end = "gpu-cap"
            elif seg.calls >= spec.turns or seg.capped:
                end = "call-cap"
            else:
                end = "stop"
            if runner is None:
                runner = self._runner(target, lang, arm)
            try:
                doc, acc = self._agent_verify(arm, task, files, support, target, lang, runner)
            except tools.RunnerUnavailable as e:
                st["outcome"] = st["ended"] = "truncated:container"
                st["detail"] = str(e)[:300]
                return
            except tools.PreflightError as e:
                st["outcome"] = st["ended"] = "truncated:host-memory"
                st["detail"] = str(e)[:300]
                return
            st["doc"] = doc
            if seg.agent_end == "error":      # the agent CLI crashed after output
                st["outcome"] = st["ended"] = "truncated:cli-crash"
                return
            if acc is None:
                st["ended"] = end
                return
            with (rd / "acceptance.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"segment": k, **acc, "files_sha256": doc["files_sha256"],
                                     "vcheck": doc.get("verdict")}, sort_keys=True) + "\n")
            if acc["passed"]:
                st["ended"] = "gate-pass"
                return
            if end != "stop":
                st["ended"] = end
                return
            if seg.calls == 0:                # a continuation that made no request
                st["ended"] = "stop"
                return
            refusal = {**acc, "vcheck": doc.get("verdict")}
            self.say(f"{aid}: stop refused (the gate: {acc['verdict'] or 'FAIL'}); session {k + 1}")

    def _agent_finish(self, aid, rd, rid, arm, task, lang, repeat, att, seeds, staged, ed, files,
                      st, started, *, interrupted=False):
        from fvh.backends import agent as AG
        target, _ = self.plan.tasks[task]
        segs, doc = st["segs"], st["doc"]
        outcome, ended = st["outcome"], st["ended"]
        if outcome is None:
            v = (doc or {}).get("verdict")
            outcome = v if v in VERDICT_WORDS else "error"
        changed = {p: t for p, t in files.items() if t != staged.get(p)}
        for p, t in changed.items():
            f = rd / "returned" / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(t, encoding="utf-8")
        runlog.write_patch(rd, {p: staged[p] for p in ed}, dict(files))
        if doc is not None:
            (rd / "verify.json").write_text(json.dumps(doc, sort_keys=True, indent=1) + "\n",
                                            encoding="utf-8")
        scan = scan_run_dir(rd)
        findings = list(st["findings"])
        if scan["withheld"]:
            findings.append("secret-scan:withheld")
            self.say(f"{aid}: a credential-shaped string ({', '.join(scan['hits'])}) in "
                     f"{', '.join(scan['withheld'])}: withheld (name, size and sha256 kept)")
        # what every session's gate counted, read again after the scan (a killed session
        # has no Segment): the attempt's spend
        tot = {"calls": 0, "gpu_s": 0.0, "prompt_tokens": 0, "output_tokens": 0}
        for d in sorted(rd.glob("seg-*")):
            cnt = AG.read_counts(d)
            for key in tot:
                tot[key] += (float if key == "gpu_s" else int)(cnt.get(key) or 0)
        tot["calls"] = max(tot["calls"], st["calls"])
        tot["gpu_s"] = round(max(tot["gpu_s"], st["gpu_s"]), 3)
        facts = apparatus.collect(self.app, self.root)
        if self.server is not None:
            facts["model_server_found"] = self.server
        facts.update(seeds=list(seeds), plan_sha256=self.plan.sha256, arm_construct="agent",
                     arm_policy="", instrument="vcheck --gate", acceptance=arm.acceptance, lab_code=arm.lab_code, feedback=arm.feedback,
                     lab_task=(target if self.plan.lever_check else ""),
                     agent={"model": str(self.app.backend(budget.QWEN).get("model") or ""),
                            "turns": arm.rounds, "sessions": len(segs),
                            "images": sorted({s.image for s in segs if s.image}),
                            "config_sha256": [s.config_sha256 for s in segs],
                            "manifest_sha256": [s.manifest_sha256 for s in segs]},
                     prompt_hashes=[apparatus.prompt_hash(system="", message=b, schema={},
                                                          policy_source="")
                                    for b in st["briefs"]])
        if arm.feedback == "spec":
            facts["feedback_sources_sha256"] = {
                str(Path(p).relative_to(self.root)): digest for p, digest in self._sources.items()
                if Path(p).name in ("labfeedback.py", "spec_feedback.py", "oracles.py")}
        if self.statements:
            facts["statements_sha256"] = dict(sorted(self.statements.items()))
        if arm.acceptance == "gate":
            facts.update(gate=self.plan.gate, gate_sha256=self.plan.gate_sha256)
        if (self.root / target).is_dir():
            facts["crate"] = target
        usage = {**tot, "tokens": tot["prompt_tokens"] + tot["output_tokens"],
                 "sessions": len(segs), "steps": sum(s.steps for s in segs),
                 "agent_wall_s": round(sum(s.agent_wall_s for s in segs), 2),
                 "wall_s": round(sum(s.wall_s for s in segs), 2)}
        findings = sorted(set(findings))
        cap = runlog.cap_finding(rd)
        if cap:
            findings.append(cap)
        meta = runlog.RunMeta(
            run_id=rid, module=self.module, arm=arm.name, task_id=task, lang=lang, attempt=att,
            repeat=repeat, mode="agent", backend=arm.family, outcome=outcome,
            lab=self.plan.lab, ended_by=ended or "", verify=doc, usage=usage, apparatus=facts,
            course_commit=self.facts["course_commit"], course_dirty=self.facts["course_dirty"],
            inputs_sha256=runlog.inputs_tree_sha256({p: x.encode("utf-8")
                                                     for p, x in staged.items()}),
            manifest_sha256=segs[0].manifest_sha256 if segs else "",
            selftest={"ok": all(s.selftest_ok for s in segs)} if segs else {},
            return_summary={"files_sha256": {p: protocol.text_sha256(t)
                                             for p, t in sorted(files.items())},
                            "changed": sorted(changed),
                            "sessions": [s.summary() for s in segs]},
            secret_scan=scan, findings=tuple(findings), prereg_sha256=self.prereg,
            ledger_seq=self.ledger.head()[0], started=started, ended=_utc())
        runlog.write_meta(rd, meta)
        state = _scored_state(outcome)
        info = {"run_id": rid, "outcome": outcome, "calls": tot["calls"], "gpu_s": tot["gpu_s"]}
        if st["detail"]:
            info["detail"] = st["detail"][:300]
        self.ledger.move(aid, state, **info)
        self.say(f"{aid}: {outcome} ({ended or '-'}; {tot['calls']} call(s), {len(segs)} "
                 f"session(s)) -> {state}")
        if st["stop"]:
            self.stop = st["stop"]
        elif outcome == "deferred":
            self.stop = f"deferred in {aid}: {st['detail']}"
        if interrupted:
            raise Interrupted()
        return state

    # --- the loop ------------------------------------------------------------------

    def server_check(self) -> str | None:
        """Why a live Qwen batch may not start: the model server is unreachable or
        differs from the apparatus file's [model_server] pins (version, the pinned
        tags' digests, the unit's settings), or None (DV5c fix round)."""
        from fvh.backends import gate as G
        try:
            facts = G.server_facts(self.app)
        except (G.GateError, backends.ModelDisabled) as e:
            return f"the model server cannot be checked: {e}"
        self.server = facts
        drift = G.server_drift(self.app, facts)
        if drift:
            return "apparatus drift: " + "; ".join(d.line() for d in drift)
        return None

    def run(self, ids=None) -> int:
        ids = list(budget.resume_order(self.ledger, max_reissue=self.plan.max_reissue)
                   if ids is None else ids)
        if self.live:
            _reap_state(self.app)
        if ids and budget.QWEN in self.plan.families() and self.live:
            why = self.server_check()
            if why:
                self.stop = why
                self.say(f"stopped before the first attempt: {why}; the batch stays open "
                         "(fvh resume)")
                return EXIT_REFUSED
        lock = None
        if budget.QWEN in self.plan.families() and self.live:
            from fvh.backends import gate as G
            lock = G.GpuCalendar()
            try:
                lock.__enter__()
            except backends.Deferred as e:
                self.say(f"deferred: {e}")
                return EXIT_REFUSED
            self._calendar = lock             # an agent session's live run is handed its fd
        old = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}

        def _raise(signum, frame):
            raise Interrupted()
        for s in old:
            signal.signal(s, _raise)
        try:
            if ids and not self._window_ok(ids):
                self.say(f"stopped before the first attempt: {self.stop}; the batch stays open "
                         "(fvh resume)")
                return EXIT_REFUSED
            for aid in ids:
                if self.stop:
                    break
                if self.plan.arm(aid.split("/")[0]).family == budget.QWEN:
                    why = self._gpu_left()
                    if why:
                        self.stop = why
                        break
                self.attempt(aid)
        except Interrupted:
            self.say("interrupted: the batch stays open; `fvh resume` reconciles and continues")
            return EXIT_FAIL
        finally:
            for s, h in old.items():
                signal.signal(s, h)
            try:
                self._unload()
            finally:
                if lock is not None:
                    self._calendar = None
                    lock.__exit__(None, None, None)
        if self.stop:
            left = budget.resume_order(self.ledger, max_reissue=self.plan.max_reissue)
            for aid in left:
                if self.ledger.attempts()[aid].state == "planned":
                    self.ledger.move(aid, "deferred", reason=self.stop[:300])
            self.say(f"stopped between attempts: {self.stop}; {len(left)} id(s) left; the batch "
                     "stays open (fvh resume)")
            return EXIT_REFUSED
        left = budget.resume_order(self.ledger, max_reissue=self.plan.max_reissue)
        if left:
            self.say(f"{len(left)} id(s) are re-issuable (infra-failed): `fvh resume` re-issues "
                     "them; the batch stays open")
            return EXIT_FAIL
        budget.close_batch(self.root, self.module, course_commit=self.facts["course_commit"])
        self.say("every id is settled: the batch is closed (commit research/ledger-heads.jsonl)")
        return EXIT_OK

    def _gpu_left(self):
        """Why the module's GPU hours are spent (the registry's gpu_hours against the
        GPU-seconds the ledger's scored and failed attempts record), or None."""
        try:
            hours = float(self._registry_budget().get("gpu_hours", 0) or 0)
        except budget.BudgetError:
            return None
        spent = sum(float(r.get("gpu_s") or 0) for r in self.ledger.read()
                    if r.get("kind") == "attempt" and r.get("state") in ("scored", "infra-failed"))
        if spent >= hours * 3600:
            return (f"the module's gpu_hours = {hours:g} are spent ({spent:.0f} GPU-s in the "
                    "ledger)")
        return None

    def _unload(self):
        """keep_alive 0 for the model after a Qwen batch (DV4-PLAN §10): one gate with
        unload_on_stop and no call (the calls cap 0, so it forwards nothing)."""
        if budget.QWEN not in self.plan.families() or not self.live:
            return
        from fvh.backends import gate as G
        d = self.batches_dir / "unload"
        try:
            cfg = G.gate_config(self.app, seeds=[self.plan.seed], calls=0, unload=True)
            g = G.HostGate(d, cfg, root=self.root)
            g.start()
            g.stop()
        except Exception as e:                       # the unload is best effort, recorded
            self.say(f"the model unload failed: {type(e).__name__}: {e}")


STATE_BASES = ("fvh-claude-state", "fvh-qwen-state")
# what an agent session hands mksandbox-run, removed when it returns (fvh.backends.agent)
SESSION_TRANSIENTS = (".manifest.json", ".seeds.json", ".texts.json")


def _state_base(name):
    base = Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp") / name
    base.mkdir(mode=0o700, exist_ok=True)
    return base


def _reap_state(app, *, now=None):
    """Remove the per-call state directories a killed runner left (a derived
    credentials snapshot among them): every subdirectory of the transports'
    state bases older than the longest call cap plus a margin, so no call that
    may still run loses its own (DV5c fix round)."""
    caps = []
    for fam in app.families():
        try:
            v = app.backend(fam).get("call_timeout_s", app.backend(fam).get("timeout_s"))
        except apparatus.ApparatusError:
            v = None
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            caps.append(float(v))
    age = max(caps + [3600.0]) + 600.0
    now = time.time() if now is None else now
    gone = 0
    for name in STATE_BASES:
        base = Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp") / name
        if not base.is_dir():
            continue
        for d in base.iterdir():
            try:
                if d.is_dir() and not d.is_symlink() and now - d.stat().st_mtime > age:
                    shutil.rmtree(d, ignore_errors=True)
                    gone += 1
            except OSError:
                continue
    return gone


def _secret_values(tr) -> tuple:
    """The exact credential values a run's transport (or the one it wraps) handed its
    calls, for scan_run_dir; () when it names none."""
    for t in (tr, getattr(tr, "inner", None)):
        fn = getattr(t, "secret_values", None)
        if callable(fn):
            try:
                return tuple(fn())
            except Exception:                         # the format scan still runs
                return ()
    return ()


def scan_run_dir(rd, exact=()) -> dict:
    """The secret scan of a run directory before it is kept (DV4-PLAN §5.7; DV5c fix
    round): every file in it (a .gz one decompressed) against SECRET_PATTERNS and,
    when `exact` names them, the exact credential values the run's transport handed
    its calls (finding `exact-token`; DV5c gaps lane); a file with a hit is withheld,
    i.e. removed, and its name, size, sha256 and the formats found are recorded,
    never its content. Returns {"hits": [formats], "withheld": [names],
    "withheld_files": [records]}."""
    rd = Path(rd)
    values = [v.encode("utf-8") for v in exact if isinstance(v, str) and len(v) >= 16]
    hits, names, recs = set(), [], []
    for f in sorted(x for x in rd.rglob("*") if x.is_file() and not x.is_symlink()):
        if f.name == "run.json":
            continue
        try:
            raw = f.read_bytes()
        except OSError:
            continue
        data = raw
        if f.suffix == ".gz":
            try:
                data = gzip.decompress(raw)
            except (OSError, EOFError):
                data = raw
        got = secret_hits(data)
        if any(v in data for v in values):
            got = sorted(set(got) | {"exact-token"})
        if not got:
            continue
        rel = f.relative_to(rd).as_posix()
        hits.update(got)
        names.append(rel)
        recs.append({"name": rel, "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                     "findings": got})
        f.unlink()
    return {"hits": sorted(hits), "withheld": names, "withheld_files": recs}


def _compress_gate_log(rd):
    p = rd / "gate.log"
    if p.is_file():
        (rd / "gate.log.gz").write_bytes(gzip.compress(p.read_bytes(), mtime=0))
        p.unlink()


def _had_output(rd) -> bool:
    """Whether a run directory shows a model answer: a recorded call with output, a
    recorded proposal, or a gated call."""
    rd = Path(rd)
    calls = rd / "calls.jsonl"
    if calls.is_file():
        for line in calls.read_text(encoding="utf-8").splitlines():
            try:
                if json.loads(line).get("had_output"):
                    return True
            except ValueError:
                continue
    acts = rd / "actions.jsonl"
    if acts.is_file() and acts.read_text(encoding="utf-8").strip():
        return True
    for p in [rd / "gate-counts.json"] + sorted(rd.glob("seg-*/gate-counts.json")):
        try:                                  # an agent-mode attempt's sessions (seg-<k>/)
            if int(json.loads(p.read_text(encoding="utf-8")).get("calls") or 0) > 0:
                return True
        except (OSError, ValueError, AttributeError, TypeError):
            continue
    return False


# =====================================================================================
# Resume
# =====================================================================================

def batch_note(ledger) -> dict | None:
    """The newest batch-plan note of the ledger."""
    out = None
    for rec in ledger.read():
        if rec.get("kind") == "note" and rec.get("note") == "batch-plan":
            out = rec
    return out


def reconcile(root, module, ledger, plan=None, *, log=None) -> list:
    """Settle every `running` id a killed runner left (module docstring)."""
    say = log or (lambda m: None)
    out = []
    lines = ledger.read()
    for aid, a in ledger.attempts().items():
        if a.state != "running":
            continue
        rid = None
        for rec in lines:
            if rec.get("kind") == "attempt" and rec.get("id") == aid and rec.get("state") == "running":
                rid = rec.get("run_id")
        rd = ledger.path.parent / rid if rid else None
        if rd is not None and (rd / "run.json").is_file():
            try:
                meta = runlog.load_meta(rd)
                st = _scored_state(meta.outcome)
                ledger.move(aid, st, run_id=rid, outcome=meta.outcome,
                            calls=int(meta.usage.get("calls", 0) or 0),
                            detail="settled on resume from its run.json")
                out.append((aid, st))
                continue
            except ValueError:
                pass
        had = rd is not None and _had_output(rd)
        outcome = INTERRUPTED if had else "infra-failed"
        if rd is not None and rd.is_dir() and plan is not None:
            arm_name, task, repeat, att = aid.split("/")
            target, lang = plan.tasks[task]
            verify = None
            if (rd / "verify.json").is_file():
                try:
                    verify = json.loads((rd / "verify.json").read_text(encoding="utf-8"))
                except ValueError:
                    verify = None
            try:
                facts = apparatus.collect(apparatus.load(root=root), root)
            except apparatus.ApparatusError:
                facts = {}
            agent = plan.arm(arm_name).agent
            facts.update(seeds=plan.seeds(aid), plan_sha256=plan.sha256,
                         lab_code=plan.arm(arm_name).lab_code,
                         settled="on resume: the runner was killed during this attempt",
                         lab_task=target if plan.lever_check else "",
                         **({"arm_construct": "agent"} if agent else {}))
            _compress_gate_log(rd)
            for d in rd.glob("seg-*"):
                _compress_gate_log(d)
                for f in SESSION_TRANSIENTS:  # a killed session's hand-over files
                    (d / f).unlink(missing_ok=True)
            scan = scan_run_dir(rd)
            meta = runlog.RunMeta(
                run_id=rid, module=module, arm=arm_name, task_id=task, lang=lang,
                attempt=int(att), repeat=int(repeat),
                mode="agent" if agent else "harness-executed",
                backend=plan.arm(arm_name).family, outcome=outcome, lab=plan.lab,
                ended_by=outcome, verify=verify, usage=_spent(rd),
                apparatus=facts, secret_scan=scan,
                inputs_sha256=_inputs_sha(rd),
                findings=("runner-killed",) + (("secret-scan:withheld",) if scan["withheld"]
                                               else ()),
                ledger_seq=ledger.head()[0], ended=_utc())
            runlog.write_meta(rd, meta)
        st = _scored_state(outcome)
        spent = _spent(rd) if rd is not None else {}
        ledger.move(aid, st, run_id=rid or "", outcome=outcome, **spent,
                    detail="settled on resume: the runner was killed during this attempt")
        say(f"{aid}: running when the runner stopped -> {outcome} ({st})")
        out.append((aid, st))
    return out


def _spent(rd) -> dict:
    """What a killed attempt spent, from its run directory: the model calls (the
    recorded calls, or the gate's count when higher) and the gate's GPU-seconds,
    so the ledger's budget counts them (DV5c fix round)."""
    out = {"calls": _count_calls(rd)}
    calls, gpu, seen = 0, 0.0, False
    for p in [Path(rd) / "gate-counts.json"] + sorted(Path(rd).glob("seg-*/gate-counts.json")):
        try:                                  # the run's gate, or an agent attempt's sessions'
            cnt = json.loads(p.read_text(encoding="utf-8"))
            calls += int(cnt.get("calls") or 0)
            gpu += float(cnt.get("gpu_s") or 0.0)
            seen = True
        except (OSError, ValueError, AttributeError, TypeError):
            continue
    if seen:
        out["calls"] = max(out["calls"], calls)
        out["gpu_s"] = round(gpu, 3)
    return out


def _count_calls(rd):
    p = Path(rd) / "calls.jsonl"
    return len(p.read_text(encoding="utf-8").splitlines()) if p.is_file() else 0


def _inputs_sha(rd):
    p = Path(rd) / "inputs.sha256"
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ""


def _apparatus_of(ledger, note) -> str:
    """The apparatus file's sha256 the open batch runs on: the batch-plan note's, or
    the newest `apparatus-changed` note after it."""
    want = note.get("apparatus_sha256") or ""
    seen = False
    for rec in ledger.read():
        if rec is note or rec.get("seq") == note.get("seq"):
            seen = True
        elif seen and rec.get("kind") == "note" and rec.get("note") == "apparatus-changed":
            want = rec.get("to") or want
    return want


def resume(root, module, *, transports=None, runners=None, log=None, mem_gb=None, app=None,
           dry_run=False, after_overage_check=False, new_apparatus=False,
           check_apparatus=None, agent=None) -> int:
    """Resume the open batch (module docstring). Before any call (DV5c fix round):
    the apparatus file is the one the batch opened on (or one recorded since with
    new_apparatus, which notes the change in the ledger), the host matches its pins
    (check_apparatus, default: live, i.e. no test transports), a Qwen batch's model
    server matches them, a held overage stop is cleared only by
    after_overage_check, and the calls the re-issues would spend fit the registry
    budget with what the ledger has spent."""
    root = Path(root)
    say = log or (lambda m: print(f"fvh: {m}", flush=True))
    try:
        budget.check_anchors(root, module)
    except (budget.AnchorError, budget.LedgerError) as e:
        raise BatchError(str(e)) from None
    last = budget.last_anchor(root, module)
    if last is None or last["event"] != "open":
        raise BatchError(f"{module} has no open batch to resume")
    ledger = budget.Ledger(budget.ledger_path(root, module))
    note = batch_note(ledger)
    if note is None:
        raise BatchError(f"{module}'s open batch has no plan note: it was not opened by "
                         "`fvh run` (a contract replay resumes through scripts/contract_local.sh)")
    copy = ledger.path.parent / note["plan_file"]
    try:
        data = copy.read_bytes()
    except OSError:
        raise BatchError(f"the batch's plan copy {copy} is missing") from None
    if hashlib.sha256(data).hexdigest() != note["plan_sha256"]:
        raise BatchError(f"the batch's plan copy {copy} differs from the sha256 the ledger "
                         "recorded: a plan is never changed after its batch opens")
    plan = load_plan(copy, root)
    b = Batch(root, module, plan, transports=transports, runners=runners, log=say, mem_gb=mem_gb,
              app=app, agent=agent)
    b.ledger = ledger
    b.prereg = note.get("prereg_sha256") or ""
    want = _apparatus_of(ledger, note)
    if want and b.app.sha256 != want:
        if not new_apparatus or dry_run:
            raise BatchError(f"the apparatus file {b.app.path} changed since the batch opened "
                             f"(sha256 {want[:16]}… then, {b.app.sha256[:16]}… now): restore it, "
                             f"or record the change with `fvh resume {module} --new-apparatus` "
                             "(the ledger notes it and the report discloses it)")
        ledger.append({"kind": "note", "note": "apparatus-changed", "from": want,
                       "to": b.app.sha256})
        say(f"apparatus change recorded: {want[:16]}… -> {b.app.sha256[:16]}…")
    if check_apparatus is None:
        check_apparatus = transports is None and agent is None
    if check_apparatus:
        drift = apparatus.check(b.app, root)
        if drift:
            raise BatchError("apparatus drift: " + "; ".join(d.line() for d in drift))
    if plan.lab:
        try:
            full = prereg.check(root, module)
        except prereg.PreregRefused as e:
            raise BatchError(str(e)) from None
        if full != b.prereg:
            raise BatchError("the pre-registration changed since the batch opened "
                             f"({b.prereg[:16]} -> {full[:16]})")
    b.check_statements()
    if (note.get("statements_sha256") or {}) != b.statements:
        raise BatchError("the committed statements changed since the batch opened: a batch "
                         "runs against the statements it opened on")
    b.check_gate()
    held = ledger.overage_stop()
    if held is not None and after_overage_check and not dry_run:
        ledger.append({"kind": "note", "note": "overage-cleared",
                       "cleared": held.get("seq"), "by": "fvh resume --after-overage-check"})
        say("the overage stop is cleared (the human checked the account): Claude calls may run")
    elif held is not None and budget.CLAUDE in plan.families():
        say(f"held: {b._overage_held()}")
    if dry_run:
        ids = budget.resume_order(ledger, max_reissue=plan.max_reissue)
        running = [a for a, s in ledger.attempts().items() if s.state == "running"]
        say(f"{module}: {len(running)} running id(s) to settle, {len(ids)} to re-issue, in plan "
            f"order (max_reissue {plan.max_reissue}, the plan's)")
        for i in running:
            print(f"  settle {i}")
        for i in ids:
            print(f"  run    {i}")
        return EXIT_OK
    reconcile(root, module, ledger, plan, log=say)
    over = _reissue_over_budget(b, ledger, plan)
    if over:
        raise BatchError(over)
    return b.run()


def _reissue_over_budget(b, ledger, plan) -> str:
    """Why the re-issues would pass the registry budget: the ledger's spent calls
    (Ledger.used: planned, sentinels, and what infra-failed or deferred attempts
    spent) plus the calls of the infra-failed ids to re-run, per family; "" when
    they fit."""
    try:
        reg = b._registry_budget()
    except budget.BudgetError:
        return ""
    used = ledger.used()
    att = ledger.attempts()
    extra = {}
    for aid in budget.resume_order(ledger, max_reissue=plan.max_reissue):
        a = att[aid]
        if a.state == "infra-failed":
            extra[a.family] = extra.get(a.family, 0) + a.calls
    for fam, (ck, _rk) in budget.FAMILY_KEYS.items():
        have = reg.get(ck, 0)
        if not isinstance(have, int) or isinstance(have, bool):
            continue
        need = int(used.get(fam, {}).get("calls", 0)) + extra.get(fam, 0)
        if extra.get(fam) and need > have:
            return (f"re-issuing would need {need} {fam} calls with what the ledger has spent "
                    f"({used[fam]['calls']}), the registry allows {ck} = {have}")
    return ""
