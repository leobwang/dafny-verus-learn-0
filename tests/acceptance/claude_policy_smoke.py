#!/usr/bin/env python3
"""claude_policy_smoke.py: Claude policy mode's by-hand acceptance (DV4-PLAN §9,
§11 steps 4a-4b; Δ63, Δ147, Δ148).

    python3 tests/acceptance/claude_policy_smoke.py [all | SECTION ...]
        [--work DIR] [--archive DIR] [--budget N] [--scripted]

Author-only (the three-condition test of scripts/vcheck) and never under CI:
it calls the subscription CLI. Run it before re-pinning the Claude CLI (the
`pins` and `smoke` sections) and before a merge that changes fvh's Claude
backend, the executor or the verification container (`harness`).

Sections:
  pins     no model call. The pinned version file (sandbox/apparatus.toml's
           [backend.claude]) exists, has its sha256 and prints its version;
           `--help` lists every flag of the policy argv (`--max-turns` is
           accepted though absent from help, VERSIONS.md §2.3); `auth status
           --json` (identifying fields redacted) and whether any read-only
           command reports the overage state.
  smoke    three calls through fvh.backends.claude.Transport, every one with
           the init and overage assertions, a rate_limit_event and the user's
           own credentials file unchanged:
             context    a custom schema: the structured output, and which
                        environment facts the replaced system prompt leaves
             actions    protocol.ACTION_SCHEMA (its oneOf) as the schema: a
                        reply parsed into actions
             max-turns  a reply that wants three turns under the pinned cap
                        of two: is --max-turns enforced, and how it ends
  harness  DV4 step 4b: harness-executed Claude runs, every Verify in a fresh
           verification container (fvh.tools.ContainerRunner), composed the
           way a lab batch is: a plan of 3 arms x 2 synthetic tasks (a Dafny
           and a Verus file under the benchmark slot bench/local/q/smoke4b/,
           invented for this check, never a lab task) against a smoke budget;
           the ledger opened and anchored in a scratch root; the window file
           read (a sentinel call when it does not allow a start); per attempt
           the ledger moves, the executor's run, the run directory (run.json,
           actions, observations, verify.json, inputs, the secret-scanned
           transcript); the window acted on between attempts; the batch
           closed; and `fvh report`'s reproduction half re-deriving every run
           from its logs. The arms: Q12's A1 and A2 (the reference twin's
           IndependentSampler and SequentialRepair through
           fvh.backends.candidate_ask) and M (fvh.backends.ModelPolicy with
           the neutral smoke renderer).

--scripted runs `harness` with a scripted transport instead of the CLI (no
model call; the containers still run): the composition's own check.

Calls: every model call is logged in WORK/calls.jsonl and counted against
--budget (default 20 per work directory). Overage: every call's event must show
isUsingOverage false and an allowed overageStatus, else the transport stops
the run (ApparatusMismatch) and this script stops.
Memory (CLAUDE.md §Resources): one container at a time, Dafny at 8 GB and
Verus at 16 GB, after the free-memory check.
Records: WORK/ holds everything; --archive copies the results, the streams
(only when the secret scan is clean) and the harness root's run records.
No token value is ever printed or stored: the credentials are read for the
derived snapshot (in the transport), their sha256 and mtime, and an exact
scan of each stream.
Exit: 0 every check passed, 1 one failed, 2 usage, 3 refused.
"""

import argparse
import gzip
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "scripts")]

from dvl import sandbox  # noqa: E402
from fvh import apparatus, backends, budget, executor, protocol as P, report, runlog  # noqa: E402
from fvh import tools  # noqa: E402
from fvh.backends import claude as CL  # noqa: E402

SECTIONS = ("pins", "smoke", "harness")
WORK = Path("/tmp/dvl0-dv5b-dv4s4/smoke")
MEM_NEEDED_GIB = 16 + 15
HOST_CRED = Path.home() / ".claude" / ".credentials.json"
ARGV_FLAGS = ("-p", "--safe-mode", "--tools", "--strict-mcp-config", "--no-session-persistence",
              "--output-format", "--verbose", "--json-schema", "--model", "--effort",
              "--system-prompt")
REDACT_KEEP = {"loggedIn", "authMethod", "apiProvider", "subscriptionType"}

RESULTS = []


class Refusal(Exception):
    pass


def say(msg):
    print(f"claude_policy_smoke: {msg}", flush=True)


def note(section, name, ok, evidence):
    RESULTS.append({"section": section, "check": name, "ok": bool(ok), "evidence": evidence})
    print(f"  [{'PASS' if ok else 'FAIL'}] {section}: {name} -- {evidence}", flush=True)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


# -------------------------------------------------------------------------------------
# Preflight
# -------------------------------------------------------------------------------------

def author_gate():
    if "CI" in os.environ:
        raise Refusal("CI is set: this script calls a model, and CI never calls a model")
    if os.environ.get(backends.NO_MODEL_ENV) == "1":
        raise Refusal(f"{backends.NO_MODEL_ENV}=1 is set: no model call is made here")
    loader = importlib.machinery.SourceFileLoader("vcheck", str(ROOT / "scripts" / "vcheck"))
    spec = importlib.util.spec_from_loader("vcheck", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vcheck"] = mod
    loader.exec_module(mod)
    why = mod.author_gate(ROOT)
    if why:
        raise Refusal(f"author-only ({why})")


def load_pins():
    try:
        app = apparatus.load(root=ROOT)
        table = app.backend(budget.CLAUDE)
    except apparatus.ApparatusError as e:
        raise Refusal(str(e)) from None
    drift = apparatus.check(app, ROOT)
    if drift:
        raise Refusal("apparatus drift: " + "; ".join(d.line() for d in drift))
    return app, table


def mem_available_gib():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1048576
    return 0.0


def host_cred_state():
    """(sha256, mtime_ns) of the user's credentials file: never its content."""
    st = HOST_CRED.stat()
    return sha256_bytes(HOST_CRED.read_bytes()), st.st_mtime_ns


def exact_tokens():
    """The current access token, in memory only, for the exact scan of a stream."""
    try:
        oauth = json.loads(HOST_CRED.read_text()).get(CL.OAUTH) or {}
    except (OSError, ValueError):
        return ()
    return tuple(t for t in (oauth.get("accessToken"), oauth.get("refreshToken")) if t)


# -------------------------------------------------------------------------------------
# The call log and the transport
# -------------------------------------------------------------------------------------

class Calls:
    def __init__(self, work, limit):
        self.path = work / "calls.jsonl"
        self.limit = limit

    def used(self):
        return len(self.path.read_text().splitlines()) if self.path.exists() else 0

    def reserve(self, n=1):
        if self.used() + n > self.limit:
            raise Refusal(f"the call budget is spent ({self.used()} of {self.limit} in {self.path})")

    def log(self, rec):
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")


def state_base(work):
    """Where each call's state directory (HOME, CLAUDE_CONFIG_DIR with the derived
    snapshot) lives: RAM-backed and user-only, removed after the call."""
    base = Path(os.environ.get("XDG_RUNTIME_DIR") or work) / "fvh-claude-state"
    base.mkdir(mode=0o700, exist_ok=True)
    return base


class LoggedTransport:
    """The real transport, with each call counted, logged and its stream scanned."""

    family = budget.CLAUDE

    def __init__(self, inner, calls, work, purpose):
        self.inner = inner
        self.calls = calls
        self.work = work
        self.purpose = purpose
        self.streams = []           # every stream of this transport (the run's transcript)

    def complete(self, message, *, system="", seed=None):
        self.calls.reserve()
        before = host_cred_state()
        t0 = time.time()
        err = None
        self.inner.last_raw = None
        try:
            c = self.inner.complete(message, system=system, seed=seed)
            return c
        except Exception as e:
            err = e
            raise
        finally:
            raw = self.inner.last_raw
            after = host_cred_state()
            rec = {"n": self.calls.used() + 1, "purpose": self.purpose, "when": t0,
                   "wall_s": round(time.time() - t0, 2), "made_call": raw is not None,
                   "error": None if err is None else f"{type(err).__name__}: {err}",
                   "host_credentials_unchanged": before == after}
            if raw is not None:
                hits = sandbox.secret_scan(raw.encode("utf-8"), exact=exact_tokens())
                rec["secret_scan"] = sorted({h[0] for h in hits})
                rec["stream_sha256"] = sha256_bytes(raw.encode("utf-8"))
                self.streams.append(raw)
                if not hits:
                    d = self.work / "streams"
                    d.mkdir(exist_ok=True)
                    (d / f"{rec['n']:02d}-{self.purpose}.jsonl").write_text(raw, encoding="utf-8")
                rec["summary"] = summarize(raw)
            if raw is not None or err is None:
                self.calls.log(rec)
            else:
                rec["made_call"] = False
                (self.work / "refused-before-call.jsonl").open("a").write(json.dumps(rec) + "\n")


def summarize(raw):
    s = CL.parse_stream(raw)
    init = s["init"] or {}
    res = s["result"] or {}
    events = []
    for line in raw.splitlines():
        try:
            e = json.loads(line)
            events.append(e.get("type") + (f"/{e.get('subtype')}" if e.get("subtype") else ""))
        except (ValueError, AttributeError, TypeError):
            events.append("?")
    plugins = init.get("plugins") if isinstance(init.get("plugins"), list) else []
    u = res.get("usage") if isinstance(res.get("usage"), dict) else {}
    return {
        "events": events,
        "init": {k: init.get(k) for k in ("tools", "mcp_servers", "model", "apiKeySource",
                                          "claude_code_version", "permissionMode",
                                          "output_style", "agents")},
        "init_plugins": [{"name": p.get("name"), "path_kind": "builtin" if p.get("path") ==
                          "builtin" else "installed", "source": p.get("source")}
                         for p in plugins if isinstance(p, dict)],
        "init_skills": init.get("skills"),
        "init_slash_commands_n": len(init.get("slash_commands") or []),
        "rate_limit": s["rate_limit"],
        "result": {k: res.get(k) for k in ("subtype", "is_error", "num_turns", "terminal_reason",
                                           "stop_reason", "api_error_status", "structured_output",
                                           "permission_denials", "result", "errors")},
        "usage": {k: u.get(k) for k in ("input_tokens", "output_tokens",
                                         "cache_creation_input_tokens", "cache_read_input_tokens")},
        "assistant_events": s["assistant"],
        "synthetic_events": s["synthetic"],
    }


def transport(table, calls, work, purpose, *, schema=P.ACTION_SCHEMA, overrides=None,
              window=None, overage=None):
    t = dict(table)
    t.update(overrides or {})
    inner = CL.Transport(t, schema=schema, window=window, overage=overage,
                         state_base=state_base(work))
    return LoggedTransport(inner, calls, work, purpose)


# -------------------------------------------------------------------------------------
# Section: pins
# -------------------------------------------------------------------------------------

def s_pins(app, table, work, calls):
    binary = apparatus.resolve_binary(table["binary"])
    try:
        apparatus.check_binary(table)
        ok = True
    except apparatus.ApparatusMismatch as e:
        ok = False
    note("pins", "the pinned version file and its sha256", ok,
         f"{table['binary']} sha256 {table['sha256'][:16]}...")
    v = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=60,
                       env={"PATH": "/usr/bin:/bin", "HOME": os.environ["HOME"],
                            **CL.ENV_SWITCHES})
    note("pins", "the version file prints the pinned version",
         v.stdout.strip().startswith(table["version"] + " "), repr(v.stdout.strip()))
    h = subprocess.run([str(binary), "--help"], capture_output=True, text=True, timeout=60,
                       env={"PATH": "/usr/bin:/bin", "HOME": os.environ["HOME"],
                            **CL.ENV_SWITCHES})
    (work / "help.txt").write_text(h.stdout)
    missing = [f for f in ARGV_FLAGS if f not in h.stdout.split()
               and not any(w.startswith(f + ",") or w == f for w in h.stdout.split())]
    note("pins", "help lists every flag of the policy argv", not missing and h.returncode == 0,
         f"{len(h.stdout.splitlines())} lines on stdout; missing {missing or 'none'}; "
         f"--max-turns listed: {'--max-turns' in h.stdout} (accepted unlisted on 2.1.288)")
    note("pins", "help still lists --bare and the commands it never uses as such",
         "--bare" in h.stdout and "setup-token" in h.stdout, "--bare and setup-token present")
    a = subprocess.run([str(binary), "auth", "status", "--json"], capture_output=True, text=True,
                       timeout=60, env={"PATH": "/usr/bin:/bin", "HOME": os.environ["HOME"],
                                        **CL.ENV_SWITCHES})
    try:
        d = json.loads(a.stdout)
    except ValueError:
        d = {}
    red = {k: (v if k in REDACT_KEEP else f"<redacted {type(v).__name__}>") for k, v in d.items()}
    (work / "auth-status-redacted.json").write_text(json.dumps(red, indent=1) + "\n")
    overage_keys = [k for k in d if "overage" in k.lower() or "extra" in k.lower()
                    or "usage" in k.lower()]
    note("pins", "auth status: logged in through the subscription",
         d.get("loggedIn") is True and d.get("authMethod") == "claude.ai",
         json.dumps({k: red.get(k) for k in sorted(REDACT_KEEP)}))
    note("pins", "a read-only source of the overage state (Δ148: step 4a looks for one)", True,
         f"auth status keys naming overage/usage: {overage_keys or 'none'}; help lists no usage "
         "command, so the rate_limit_event of a call (or the batch's sentinel) stays the source")
    link = Path.home() / ".local" / "bin" / "claude"
    note("pins", "the `claude` link (information: the harness never runs it)", True,
         f"{link} -> {os.path.realpath(link)}")


# -------------------------------------------------------------------------------------
# Section: smoke
# -------------------------------------------------------------------------------------

CTX_SCHEMA = {"type": "object", "additionalProperties": False,
              "required": ["word", "cwd_known", "context_seen"],
              "properties": {"word": {"type": "string"}, "cwd_known": {"type": "string"},
                             "context_seen": {"type": "array", "items": {"type": "string"}}}}
CTX_SYSTEM = ("You are a minimal test responder. Answer only through the structured output. "
              "Set word to the single word the user asks for. Set cwd_known to the absolute "
              "working-directory path if any text in your context states one; otherwise set it "
              "to NONE. In context_seen, list each kind of environment fact your context states "
              "besides this instruction (for example: working directory, platform, OS version, "
              "date, git status, model name, shell), as short phrases; an empty list if none.")
ACT_SYSTEM = ("You are a test responder for a harness smoke check. Answer only through the "
              "structured output, with one JSON object that matches its schema.")
N_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["n"],
            "properties": {"n": {"type": "integer"}}}
N_SYSTEM = ("You are a test responder. This call checks a client's turn cap, so it needs "
            "several tool turns on purpose. Submit through the structured output tool three "
            "times in a row: the first two submissions set n to the string \"draft\" (the tool "
            "rejects them as not matching the schema); the third sets n to 3. Never answer in "
            "plain text.")


def judged(c):
    return {"window": list(c.window), "rate_limit": c.rate_limit}


SMOKE_CALLS = ("context", "actions", "max-turns")


def s_smoke(app, table, work, calls, only=SMOKE_CALLS):
    window = app.window()
    watch = budget.OverageWatch(window)
    if "context" in only:
        smoke_context(table, work, calls, window, watch)
    if "actions" in only:
        smoke_actions(table, work, calls, window, watch)
    if "max-turns" in only:
        smoke_max_turns(table, work, calls, window, watch)
    mine = [r for r in read_calls(work) if r["purpose"] in SMOKE_CALLS and r.get("made_call")
            and (r.get("summary") or {}).get("events")]
    note("smoke", "every call that reached the model carried its window event and no overage",
         bool(mine) and all((r.get("summary") or {}).get("rate_limit") and all(
             i.get("isUsingOverage") is False and i.get("overageStatus") in window.allowed_overage
             for i in r["summary"]["rate_limit"]) for r in mine),
         f"{len(mine)} call(s) with a stream; overage statuses "
         f"{sorted({i.get('overageStatus') for r in mine for i in r['summary']['rate_limit']})}")


def smoke_context(table, work, calls, window, watch):
    t = transport(table, calls, work, "context", schema=CTX_SCHEMA, window=window, overage=watch)
    try:
        c = t.complete("Reply with the word ok.", system=CTX_SYSTEM)
        so = c.structured or {}
        note("smoke", "context: init assertions, overage and window", c.window[0] == "ok",
             f"window {c.window}; init {c.apparatus.get('init_assertions')}; "
             f"event {json.dumps(c.rate_limit, sort_keys=True)}")
        note("smoke", "context: structured output", so.get("word") == "ok",
             f"turns {c.turns}; cwd_known {'a path' if so.get('cwd_known', 'NONE') != 'NONE' else 'NONE'}"
             f"; context_seen {so.get('context_seen')}")
        (work / "context-reply.json").write_text(json.dumps(so, indent=1) + "\n")
    except (backends.TransportError, apparatus.ApparatusMismatch, backends.Deferred) as e:
        note("smoke", "context: the call", False, f"{type(e).__name__}: {e}")
        raise Refusal("the first call failed: no further call until its record is read "
                      f"({work / 'calls.jsonl'})") from None
    last = read_calls(work)[-1] if read_calls(work) else {}
    note("smoke", "context: the user's credentials file is unchanged by the call",
         last.get("host_credentials_unchanged") is True, "sha256 and mtime equal before and after")
    note("smoke", "context: the stream carries a rate_limit_event",
         bool((last.get("summary") or {}).get("rate_limit")),
         f"events {(last.get('summary') or {}).get('events')}")


def smoke_actions(table, work, calls, window, watch):
    t = transport(table, calls, work, "actions", window=window, overage=watch)
    try:
        c = t.complete("Propose exactly one action: a stop action whose reason is \"done\" and "
                       "whose note is \"smoke\".", system=ACT_SYSTEM)
        ctx = P.Context("smoke", "dafny", "s", ("x.dfy",), (), "x.dfy")
        acts = backends.default_parse(c, ctx)
        note("smoke", "actions: ACTION_SCHEMA (oneOf) accepted and parsed",
             acts == [P.Stop("done", "smoke")], f"turns {c.turns}; actions {acts}; window {c.window}")
    except (backends.TransportError, apparatus.ApparatusMismatch, P.Malformed) as e:
        note("smoke", "actions: the call", False, f"{type(e).__name__}: {e}")
    last = read_calls(work)[-1]
    note("smoke", "actions: a rate_limit_event on this call too",
         bool((last.get("summary") or {}).get("rate_limit")), f"events {last['summary']['events']}")


def smoke_max_turns(table, work, calls, window, watch):
    t = transport(table, calls, work, "max-turns", schema=N_SCHEMA, window=window, overage=watch)
    outcome = None
    try:
        c = t.complete("Begin.", system=N_SYSTEM)
        try:
            backends.default_parse(c, P.Context("smoke", "dafny", "s", ("x",), (), "x"))
            outcome = f"returned and parsed (turns {c.turns}): not malformed"
        except P.Malformed as e:
            outcome = (f"returned with no structured output (ended {c.apparatus.get('ended')}, "
                       f"turns {c.turns}); the parse: malformed ({e})")
    except (backends.TransportError, apparatus.ApparatusMismatch) as e:
        outcome = f"{type(e).__name__}: {e}"
    last = read_calls(work)[-1]
    res = (last.get("summary") or {}).get("result") or {}
    model_turns = (last.get("summary") or {}).get("assistant_events")
    note("smoke", "max-turns: the pinned cap of 2 is enforced on a reply that wants 3 turns",
         res.get("subtype") == "error_max_turns" and model_turns == int(table["max_turns"]),
         f"result subtype {res.get('subtype')!r}, is_error {res.get('is_error')}, num_turns "
         f"{res.get('num_turns')}, terminal_reason {res.get('terminal_reason')!r}, errors "
         f"{res.get('errors')}, model turns {model_turns}")
    note("smoke", "max-turns: the transport makes it a malformed reply (scored), not a crash",
         outcome.startswith("returned with no structured output"), outcome)


def read_calls(work):
    p = work / "calls.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


# -------------------------------------------------------------------------------------
# Section: harness (DV4 step 4b)
# -------------------------------------------------------------------------------------

MODULE = "Q12"
SLOT = "bench/local/q/smoke4b/tasks"
TASKS = {
    "S1": ("dafny", f"{SLOT}/S1.dfy",
           "// A synthetic smoke task (DV4 step 4b). Fill in what the method needs to verify.\n"
           "function SmokeTri(n: nat): nat\n{\n  if n == 0 then 0 else n + SmokeTri(n - 1)\n}\n\n"
           "method SmokeSumTo(n: nat) returns (s: nat)\n  ensures s == SmokeTri(n)\n{\n"
           "  s := 0;\n  var i := 0;\n  while i < n\n  {\n    i := i + 1;\n    s := s + i;\n"
           "  }\n}\n"),
    "S2": ("verus", f"{SLOT}/s2.rs",
           "// A synthetic smoke task (DV4 step 4b). Fill in the proof.\n"
           "use vstd::prelude::*;\n\nverus! {\n\nspec fn smoke_tri(n: nat) -> nat\n"
           "    decreases n,\n{\n    if n == 0 { 0 } else { n + smoke_tri((n - 1) as nat) }\n}\n\n"
           "proof fn smoke_tri_monotone(a: nat, b: nat)\n    requires a <= b,\n"
           "    ensures smoke_tri(a) <= smoke_tri(b),\n    decreases b,\n{\n}\n\n} // verus!\n"),
}
STATEMENT = ("Fill in the proof so that the file verifies. Keep every declaration's name, "
             "parameters, return values, requires and ensures clauses as they are; add no "
             "assumption and no axiom.")
SYSTEM = ("You are a verification assistant in a harness smoke run. Answer only through the "
          "structured output, with one JSON object that matches its schema.")
ARMS = (budget.Arm("A1", budget.CLAUDE, 1), budget.Arm("A2", budget.CLAUDE, 2),
        budget.Arm("M", budget.CLAUDE, 2))
SMOKE_BUDGET = {"claude_calls": 12, "claude_runs": 6, "qwen_calls": 0, "qwen_runs": 0,
                "gpu_hours": 0}
SENTINEL_MSG = "Propose exactly one action: a stop action whose reason is \"done\" and whose note is \"sentinel\"."


def instructions(target):
    return (f"You are given one file of a verification task. Reply with one JSON object that "
            f"matches the action schema and holds exactly one edit action: its path is "
            f"\"{target}\", its old is the empty string, and its new is the complete new text "
            f"of the file.")


def m_statement(target, text):
    return (STATEMENT + f"\n\nThe file {target} as shipped:\n```\n{text}```\n\nReply with "
            "actions. To submit, propose an edit of the whole file (path as above, old the empty "
            "string, new the complete text) followed by a verify action with mode \"gate\". The "
            "next message shows the last verification's verdict; once it is \"verified\", "
            "propose a stop action with reason \"done\".")


def load_twin():
    spec = importlib.util.spec_from_file_location(
        "q12_twin_policies", ROOT / "Solutions" / "harness" / "q" / "fvh_q" / "policies.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ScriptedTransport:
    """--scripted: canned replies in the CLI's reply shape (no model)."""

    family = "scripted"

    def __init__(self):
        self.n = 0
        self.streams = []

    def complete(self, message, *, system="", seed=None):
        self.n += 1
        if "sentinel" in message:
            obj = {"actions": [{"type": "stop", "reason": "done", "note": "sentinel"}]}
        elif "smoke_tri" in message or "s2.rs" in message:
            tgt = TASKS["S2"][1]
            obj = {"actions": [{"type": "edit", "path": tgt, "old": "", "new": TASKS["S2"][2]}]}
        else:
            tgt = TASKS["S1"][1]
            if '"last_verdict": "verified"' in message:
                obj = {"actions": [{"type": "stop", "reason": "done", "note": ""}]}
            else:
                obj = {"actions": [{"type": "edit", "path": tgt, "old": "", "new": TASKS["S1"][2]},
                                   {"type": "verify", "mode": "gate"}]}
        info = {"status": "allowed", "overageStatus": "rejected", "isUsingOverage": False,
                "unifiedWindows": {"five_hour": {"utilization": 0.1},
                                   "seven_day": {"utilization": 0.1}}}
        return backends.Completion(text="", structured=obj,
                                   usage={"input_tokens": 1, "output_tokens": 1}, turns=2,
                                   rate_limit=info, window=("ok", "scripted"),
                                   apparatus={"family": "scripted"})


def git_head():
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain",
                                 "--untracked-files=no"], capture_output=True,
                                text=True).stdout.strip())
    return head, dirty


def s_harness(app, table, work, calls, scripted):
    if mem_available_gib() < MEM_NEEDED_GIB:
        raise Refusal(f"only {mem_available_gib():.0f} GiB available; need {MEM_NEEDED_GIB} "
                      "(the 16 GB share plus 15 GB, CLAUDE.md §Resources)")
    twin = load_twin()
    pol_src = apparatus.source_sha256(ROOT / "Solutions/harness/q/fvh_q/policies.py")
    sroot = work / ("root-scripted" if scripted else "root")
    if sroot.exists():
        raise Refusal(f"{sroot} exists: a harness root is used once (move it away to re-run)")
    (sroot / "research" / "runs").mkdir(parents=True)
    head, dirty = git_head()
    win_path = sroot / budget.WINDOW_FILE
    window = app.window()
    watch = budget.OverageWatch(window)
    if scripted:
        tr = ScriptedTransport()
    else:
        tr = transport(table, calls, work, "harness", window=window, overage=watch)
        calls.reserve(sum(a.rounds for a in ARMS) * len(TASKS) + 1)
    items = budget.enumerate_plan(ARMS, list(TASKS))
    ledger = budget.open_batch(sroot, MODULE, items, course_commit=head, budget=SMOKE_BUDGET,
                               require_git=False)
    note("harness", "the plan fits the smoke budget; the ledger opened and anchored",
         len(ledger.attempts()) == len(items),
         f"{len(items)} attempts, {budget.plan_totals(items)['claude']}; anchor "
         f"{budget.last_anchor(sroot, MODULE)['event']}")
    state = {"last": None, "stop": None}

    def on_call(c, err):
        if c is not None:
            state["last"] = c
            if c.rate_limit:
                budget.write_window(win_path, c.rate_limit)

    may, why = budget.batch_may_start(win_path, window)
    note("harness", "no fresh window event in a new root: the batch's first call is a sentinel",
         not may, why)
    if not may:
        try:
            c = tr.complete(SENTINEL_MSG, system=ACT_SYSTEM)
            on_call(c, None)
            v, r = c.window
        except (backends.TransportError, apparatus.ApparatusMismatch) as e:
            v, r = "stop", f"{type(e).__name__}: {e}"
        ledger.sentinel(family=budget.CLAUDE, calls=1, verdict=v, reason=r)
        may2, why2 = budget.batch_may_start(win_path, window)
        note("harness", "the sentinel's event decides: the batch proceeds", v == "ok" and may2,
             f"sentinel {v} ({r}); window file now: {why2}")
        if v != "ok":
            state["stop"] = f"sentinel {v}: {r}"
    runs = []
    for p in items:
        arm, task = p.id.split("/")[0], p.id.split("/")[1]
        lang, target, text = TASKS[task]
        if state["stop"]:
            ledger.move(p.id, "deferred", reason=state["stop"])
            continue
        rid = runlog.new_run_id(p.id)
        rd = sroot / "research" / "runs" / MODULE / rid
        ledger.move(p.id, "running", run_id=rid)
        meter = budget.Meter(budget.Caps(calls=p.calls, turns=p.calls + 1, wall_s=3600))
        streams_before = len(tr.streams)
        prompts = []
        if arm == "M":
            ctx = P.Context(task, lang, m_statement(target, text), (target,), (), target,
                            material={})
            msgs = []

            def render(s, c, b, _m=msgs):
                m = backends.smoke_render(s, c, b)
                _m.append(m)
                return m
            policy = backends.ModelPolicy(tr, render, meter=meter, system=SYSTEM, seeds=[1, 2],
                                          on_call=on_call)
            prompts = msgs
        else:
            ctx = P.Context(task, lang, STATEMENT, (target,), (), target,
                            material={"instructions": instructions(target), "text": text})
            asked = []

            def oc(c, err, _a=asked):
                on_call(c, err)

            base_ask = backends.candidate_ask(tr, target=target, meter=meter, system=SYSTEM,
                                              on_call=oc)

            def ask(prompt, seed, _b=base_ask, _a=asked):
                _a.append(prompt)
                return _b(prompt, seed)
            policy = (twin.IndependentSampler(ask, seed=1) if arm == "A1"
                      else twin.SequentialRepair(ask, seeds=range(p.calls)))
            prompts = asked
        runner = tools.ContainerRunner(ROOT, module=MODULE, mem_gb=16 if lang == "verus" else 8)
        started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        res = executor.Executor(ctx, {target: text}, runner=runner, meter=meter, run_dir=rd,
                                root=ROOT).run(policy)
        ended = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        inputs_sha = runlog.write_inputs(rd, {target: text.encode("utf-8")})
        new_streams = tr.streams[streams_before:]
        blob = "".join(new_streams).encode("utf-8")
        hits = sandbox.secret_scan(blob, exact=() if scripted else exact_tokens())
        if new_streams and not hits:
            with gzip.open(rd / "transcript.jsonl.gz", "wb") as fh:
                fh.write(blob)
        calls_n = meter.calls
        app_facts = apparatus.collect(app, ROOT)
        app_facts["prompt_hashes"] = [apparatus.prompt_hash(
            system=SYSTEM, message=m, schema=P.ACTION_SCHEMA,
            policy_source=pol_src if arm != "M" else apparatus.source_sha256(backends))
            for m in prompts]
        last = state["last"]
        app_facts["calls"] = [] if last is None else [last.apparatus]
        findings = []
        if hits:
            findings.append("secret-scan-hit")
        meta = runlog.RunMeta(
            run_id=rid, module=MODULE, arm=arm, task_id=task, lang=lang, attempt=1, repeat=1,
            mode="harness-executed", backend=budget.CLAUDE if not scripted else "scripted",
            outcome=res.outcome, ended_by=res.ended_by, verify=res.verify,
            usage={**res.usage, "client_calls": calls_n}, apparatus=app_facts,
            course_commit=head, course_dirty=dirty, inputs_sha256=inputs_sha,
            secret_scan={"hits": sorted({h[0] for h in hits}), "withheld":
                         ["transcript.jsonl.gz"] if hits else []},
            findings=tuple(findings), ledger_seq=ledger.head()[0], started=started, ended=ended)
        runlog.write_meta(rd, meta)
        st = "scored" if runlog.scored(res.outcome) else (
            "deferred" if res.outcome == "deferred" else "infra-failed")
        ledger.move(p.id, st, run_id=rid, outcome=res.outcome, calls=calls_n)
        obs = [json.loads(x) for x in (rd / "observations.jsonl").read_text().splitlines()] \
            if (rd / "observations.jsonl").exists() else []
        runners_ = sorted({t["runner"] for o in obs for t in (o.get("tools") or [])})
        verdicts = [t["document"].get("verdict") for o in obs for t in (o.get("tools") or [])
                    if isinstance(t.get("document"), dict)]
        runs.append({"id": p.id, "run_id": rid, "outcome": res.outcome, "ended_by": res.ended_by,
                     "calls": calls_n, "steps": res.steps, "verdicts": verdicts,
                     "runners": runners_, "state": st, "detail": res.detail})
        note("harness", f"{p.id}: a harness-executed run, every Verify in a container",
             st == "scored" and runners_ == ["container"] and calls_n <= p.calls
             and not hits,
             f"outcome {res.outcome}, ended_by {res.ended_by}, calls {calls_n}/{p.calls}, "
             f"verdicts {verdicts}, runners {runners_}, secret scan {sorted({h[0] for h in hits}) or 'clean'}")
        if last is not None and last.window[0] != "ok":
            state["stop"] = f"window {last.window[0]}: {last.window[1]}"
            note("harness", "the window defers the rest of the batch between attempts", True,
                 state["stop"])
    budget.close_batch(sroot, MODULE, course_commit=head)
    rep = report.build(sroot, MODULE)
    text = report.format_report(rep)
    (work / ("report-scripted.txt" if scripted else "report.txt")).write_text(text)
    print(text)
    note("harness", "fvh report re-derives every run from its logs and the ledger",
         rep.reproduced and len(rep.checks) == len(runs),
         f"{sum(c.ok for c in rep.checks)}/{len(rep.checks)} reproduced; {rep.ledger}")
    used = budget.Ledger(budget.ledger_path(sroot, MODULE)).used()
    note("harness", "the ledger counts the calls (sentinel included)", True, json.dumps(used))
    w = budget.read_window(win_path)
    note("harness", "the window file holds the newest event", w is not None,
         json.dumps((w or {}).get("rate_limit_info"), sort_keys=True))
    (work / ("harness-scripted.json" if scripted else "harness.json")).write_text(
        json.dumps({"runs": runs, "used": used}, indent=1, sort_keys=True) + "\n")


# -------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sections", nargs="*", default=["all"])
    ap.add_argument("--work", type=Path, default=WORK)
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--budget", type=int, default=20)
    ap.add_argument("--scripted", action="store_true")
    ap.add_argument("--only", default=",".join(SMOKE_CALLS),
                    help="the smoke calls to make (comma-separated: " + ",".join(SMOKE_CALLS) + ")")
    a = ap.parse_args(argv)
    secs = SECTIONS if a.sections == ["all"] else tuple(a.sections)
    bad = [s for s in secs if s not in SECTIONS]
    if bad:
        print(f"unknown section(s): {bad}; choose from {SECTIONS}", file=sys.stderr)
        return 2
    try:
        author_gate()
        app, table = load_pins()
        a.work.mkdir(parents=True, exist_ok=True)
        calls = Calls(a.work, a.budget)
        say(f"work {a.work}; {calls.used()} of {a.budget} call(s) used; pins {table['version']} "
            f"{table['model']} effort {table['effort']} max_turns {table['max_turns']}")
        for s in secs:
            say(f"section {s}")
            if s == "pins":
                s_pins(app, table, a.work, calls)
            elif s == "smoke":
                s_smoke(app, table, a.work, calls,
                        only=tuple(x for x in a.only.split(",") if x in SMOKE_CALLS))
            elif s == "harness":
                s_harness(app, table, a.work, calls, a.scripted)
    except Refusal as e:
        say(f"refused: {e}")
        code = 3
    else:
        code = 0 if all(r["ok"] for r in RESULTS) else 1
    out = a.work / f"results-{int(time.time())}.json"
    out.write_text(json.dumps({"sections": list(secs), "results": RESULTS, "exit": code,
                               "calls_used": Calls(a.work, a.budget).used()}, indent=1) + "\n")
    if a.archive:
        a.archive.mkdir(parents=True, exist_ok=True)
        for f in a.work.iterdir():
            dst = a.archive / f.name
            if f.is_dir():
                shutil.copytree(f, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(f, dst)
    say(f"{sum(r['ok'] for r in RESULTS)} passed, {sum(not r['ok'] for r in RESULTS)} failed; "
        f"{Calls(a.work, a.budget).used()} model call(s) logged; exit {code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
