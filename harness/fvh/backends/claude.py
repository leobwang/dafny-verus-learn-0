"""fvh.backends.claude — Claude in policy mode, on the host, tool-less (DV4-PLAN
§3.4; Δ63, Δ147, Δ148).

The argv (Δ63's, as probed on 2.1.288 [DV0]):

    <pinned version file> -p --safe-mode --tools "" --strict-mcp-config
        --no-session-persistence --output-format stream-json --verbose
        --json-schema <ACTION_SCHEMA> --model <pinned> --effort <pinned>
        --system-prompt <prompt> --max-turns <pinned> <message>

  - The binary is the apparatus file's version file ("~/.local/share/claude/
    versions/<version>"), its sha256 checked before every exec; never the
    `claude` link, so an auto-update cannot change the apparatus under a batch.
  - The environment is built from nothing: PATH /usr/bin:/bin, HOME and
    CLAUDE_CONFIG_DIR in the call's state directory, LANG=C.UTF-8, TERM=dumb,
    DISABLE_AUTOUPDATER=1, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1,
    DISABLE_TELEMETRY=1, DISABLE_ERROR_REPORTING=1. No ANTHROPIC_* variable,
    no CLAUDE_CODE_OAUTH_TOKEN, nothing of the parent's environment.
  - The credentials (Δ147, DV4-PLAN §5.7): for each call a derived snapshot
    of the user's current credentials file (mode 0600 in the call's
    CLAUDE_CONFIG_DIR) that keeps only the OAuth table's access token, its
    expiry, the scopes, the subscription type and the rate-limit tier
    (SNAPSHOT_KEYS): never the refresh token or its expiry, and no other
    top-level entry, so a call can never refresh. A call does not start when
    the access token's remaining life ("expiresAt", in ms) is shorter than
    the call's wall-clock cap plus a margin: Deferred. Probed live at step 4a
    on 2.1.296 (claude_policy_smoke.py): the snapshot works for a policy
    call, and the user's own file is left unchanged.
  - The working directory is a fresh empty directory made by mktemp under
    /tmp (a name that names no task, module or repository), checked empty
    after the call and removed. Records say "system prompt replaced;
    environment context still injected" (Δ63).
  - Init assertions, every call: tools == ["StructuredOutput"], mcp_servers
    == [], model and claude_code_version equal the pins, apiKeySource ==
    "none", cwd equals the call's directory, and plugins and skills hold
    only the CLI's own built-ins that the apparatus pins (builtin_plugins:
    entries whose path is "builtin"; builtin_skills). Step 4a's probe on
    2.1.296: the isolated config drops every installed plugin and user or
    project skill, but the CLI still lists 2 built-in plugins and 17 built-in
    skills; with no Skill tool in `tools` none of them can load. A failure
    discards the reply unread: ApparatusMismatch.
  - Overage, every call (Δ148): the call's rate_limit_event through the
    batch's budget.OverageWatch; "stop" is ApparatusMismatch, "defer" is kept
    in Completion.window for the batch to act on between attempts. A call
    with no event of its own stops too. An ApparatusMismatch raised after the
    CLI ran carries `ran` (the call counts against the budget) and, for an
    overage stop, `overage` and the call's event (`rate_limit`): fvh.batch
    records the event and a sticky ledger note, so no later call runs until
    a human clears it (DV5c fix round).
  - Result checks: is_error false (else TransportError: 429 rate-limit,
    401/403 or the CLI's own "Not logged in" auth, otherwise cli-crash; the
    CLI's own messages, model "<synthetic>", are no model output), num_turns
    at most the pin (else ApparatusMismatch); the structured output is parsed
    by the caller against ACTION_SCHEMA. total_cost_usd is notional and never
    a unit.
  - The turn cap: --max-turns is enforced (step 4a, 2.1.296: a reply that
    wanted three turns under a cap of 2 ended after two model turns with
    result subtype "error_max_turns", is_error true, num_turns 3, errors
    ["Reached maximum number of turns (2)"]). Such a call produced model
    output but no structured output within the cap: it is returned with no
    structured output and an empty text, so the caller's parse makes it
    `malformed` (a scored outcome that counts its call), never a truncation.

Probed live at DV4 step 4a on 2.1.296 (tests/acceptance/claude_policy_smoke.py;
author notes §10): the init and overage assertions, a rate_limit_event on
every call, the turn cap above, the schema (cli_schema), the derived snapshot,
and the environment context the replaced system prompt keeps (the cwd, git
status, platform, shell, OS version, the date and the model's identity).
"""

import json
import os
import shutil
import subprocess
import tempfile
import time
from collections.abc import Mapping
from pathlib import Path

from fvh import apparatus, budget, protocol
from fvh.backends import (ApparatusMismatch, Completion, Deferred, TransportError,
                          refuse_if_disabled)

__all__ = ["ENV_SWITCHES", "NAME", "OAUTH", "SNAPSHOT_KEYS", "SYNTHETIC", "Transport", "argv",
           "cli_schema", "derive_credentials", "environment", "init_problems", "parse_stream",
           "snapshot_of"]

NAME = budget.CLAUDE
ENV_SWITCHES = {"DISABLE_AUTOUPDATER": "1", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                "DISABLE_TELEMETRY": "1", "DISABLE_ERROR_REPORTING": "1"}
PROMPT_NOTE = "system prompt replaced; environment context still injected"
CREDENTIALS = ".credentials.json"
OAUTH = "claudeAiOauth"               # the credentials file's OAuth table (probed, step 4a)
SNAPSHOT_KEYS = ("accessToken", "expiresAt", "scopes", "subscriptionType", "rateLimitTier")
MARGIN_S = 600                        # [A] the margin above a call's wall-clock cap
DEFAULT_TIMEOUT_S = 600               # [A] one policy call's wall-clock cap



def _ran(exc, *, overage=False, rate_limit=None):
    """An ApparatusMismatch raised after the CLI ran: `ran` (the call counts against
    the budget), `overage` (an overage stop) and the call's own rate_limit_event
    (None when it carried none) ride on it."""
    exc.ran = True
    exc.overage = overage
    exc.rate_limit = dict(rate_limit) if isinstance(rate_limit, Mapping) else None
    return exc

def cli_schema(schema) -> dict:
    """The schema as the CLI takes it: without a top-level "$schema" key. Step 4a's
    probe on 2.1.296: the CLI's validator refuses ACTION_SCHEMA's draft 2020-12
    meta-schema URI ("--json-schema is not a valid JSON Schema: no schema with
    key or ref ...", exit 1, no init event, no model message), and accepts the
    same schema without it (oneOf, const and type lists included). The prompt
    hash keeps the full schema."""
    return {k: v for k, v in schema.items() if k != "$schema"} if isinstance(schema, dict) \
        else schema


def argv(binary, table: Mapping, *, schema, system: str, message: str) -> list[str]:
    """The pinned argv (module docstring)."""
    for k in ("model", "effort", "max_turns"):
        if k not in table:
            raise apparatus.ApparatusError(f"[backend.{NAME}] has no {k} pin")
    return [str(binary), "-p", "--safe-mode", "--tools", "", "--strict-mcp-config",
            "--no-session-persistence", "--output-format", "stream-json", "--verbose",
            "--json-schema", json.dumps(cli_schema(schema), separators=(",", ":"),
                                        sort_keys=True),
            "--model", str(table["model"]), "--effort", str(table["effort"]),
            "--system-prompt", system, "--max-turns", str(int(table["max_turns"])), message]


def environment(state: Path) -> dict:
    """The call's environment, built from nothing."""
    home = state / "home"
    config = state / "config"
    return {"PATH": "/usr/bin:/bin", "HOME": str(home), "CLAUDE_CONFIG_DIR": str(config),
            "LANG": "C.UTF-8", "TERM": "dumb", **ENV_SWITCHES}


def snapshot_of(data) -> dict:
    """The derived snapshot of a parsed credentials file: {OAUTH: the SNAPSHOT_KEYS
    present}; TransportError (auth, before output) when there is no access token."""
    oauth = data.get(OAUTH) if isinstance(data, dict) else None
    if not isinstance(oauth, dict) or not isinstance(oauth.get("accessToken"), str) \
            or not oauth["accessToken"]:
        raise TransportError("auth", f"the credentials file has no {OAUTH} access token")
    return {OAUTH: {k: oauth[k] for k in SNAPSHOT_KEYS if k in oauth}}


def derive_credentials(src, config_dir, *, now: float, min_life_s: float) -> Path:
    """Write the derived snapshot (snapshot_of) into config_dir; Deferred when the
    access token's remaining life is shorter than min_life_s; TransportError
    (auth, before output) when there is no usable credentials file."""
    src = Path(src)
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise TransportError("auth", "no readable credentials file for the call") from None
    snap = snapshot_of(data)
    exp = snap[OAUTH].get("expiresAt")
    if not isinstance(exp, (int, float)) or isinstance(exp, bool):
        raise TransportError("auth", "the credentials file names no access-token expiry")
    left = exp / 1000.0 - now
    if left < min_life_s:
        raise Deferred(f"the access token expires in {int(left)} s, under the call's cap plus "
                       f"the margin ({int(min_life_s)} s): the batch defers")
    config_dir = Path(config_dir)
    config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    dst = config_dir / CREDENTIALS
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(snap, fh)
    return dst


SYNTHETIC = "<synthetic>"              # the model of a message the CLI writes itself (step 4a)


def parse_stream(text: str) -> dict:
    """{init, rate_limit (list of rate_limit_info), result, assistant (count of model
    messages), synthetic (count of the CLI's own messages, such as "Not logged
    in"), bad (count)}."""
    out = {"init": None, "rate_limit": [], "result": None, "assistant": 0, "synthetic": 0,
           "bad": 0}
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except ValueError:
            out["bad"] += 1
            continue
        if not isinstance(e, dict):
            out["bad"] += 1
            continue
        t = e.get("type")
        if t == "system" and e.get("subtype") == "init" and out["init"] is None:
            out["init"] = e
        elif t == "rate_limit_event" and isinstance(e.get("rate_limit_info"), dict):
            out["rate_limit"].append(e["rate_limit_info"])
        elif t == "assistant":
            m = e.get("message") if isinstance(e.get("message"), dict) else {}
            out["synthetic" if m.get("model") == SYNTHETIC else "assistant"] += 1
        elif t == "result":
            out["result"] = e
    return out


def init_problems(init, table: Mapping, cwd) -> list[str]:
    """The init assertions (module docstring); empty when every one holds."""
    if not isinstance(init, dict):
        return ["no init event"]
    want = {"tools": ["StructuredOutput"], "mcp_servers": [], "model": table.get("model"),
            "apiKeySource": "none", "claude_code_version": table.get("version"),
            "cwd": str(cwd)}
    out = []
    for k, v in want.items():
        if init.get(k) != v:
            out.append(f"init {k} is {init.get(k)!r}, not {v!r}")
    plugins, skills = init.get("plugins"), init.get("skills")
    ok_plugins = set(table.get("builtin_plugins") or ())
    ok_skills = set(table.get("builtin_skills") or ())
    if not isinstance(plugins, list):
        out.append(f"init plugins is {plugins!r}, not a list")
    else:
        extra = [p.get("name") if isinstance(p, dict) else p for p in plugins
                 if not (isinstance(p, dict) and p.get("path") == "builtin"
                         and p.get("name") in ok_plugins)]
        if extra:
            out.append(f"init plugins lists {len(extra)} entries beyond the pinned built-ins: "
                       f"{extra!r}")
    if not isinstance(skills, list):
        out.append(f"init skills is {skills!r}, not a list")
    else:
        extra = [x for x in skills if x not in ok_skills]
        if extra:
            out.append(f"init skills lists {len(extra)} entries beyond the pinned built-ins: "
                       f"{extra!r}")
    return out


class Transport:
    """One Claude policy call per complete() (module docstring)."""

    family = NAME

    def __init__(self, table: Mapping, *, window: budget.WindowRule | None = None,
                 schema=protocol.ACTION_SCHEMA, state_base=None, credentials=None,
                 overage: budget.OverageWatch | None = None, timeout_s: float | None = None,
                 cwd_base: str = "/tmp", now=time.time, clock=time.monotonic):
        refuse_if_disabled()
        self.table = dict(table)
        self.schema = schema
        self.window = window or budget.WindowRule()
        self.overage = overage or budget.OverageWatch(self.window)
        self.state_base = Path(state_base) if state_base is not None else None
        self.credentials = credentials
        self.timeout_s = timeout_s or float(self.table.get("call_timeout_s", DEFAULT_TIMEOUT_S))
        self.cwd_base = cwd_base
        self.now = now
        self.clock = clock
        self.last_raw = None          # the last call's stream (kept for the record, even
                                      # when its assertions fail and the reply is discarded)
        self._tokens = set()          # the access tokens this transport's snapshots held:
        #                               in memory only, for the exact-value secret scan

    def _remember_token(self, dst):
        try:
            tok = json.loads(Path(dst).read_text(encoding="utf-8"))[OAUTH]["accessToken"]
        except (OSError, ValueError, KeyError, TypeError):
            return
        if isinstance(tok, str) and len(tok) >= 16:
            self._tokens.add(tok)

    def secret_values(self) -> tuple:
        """The exact credential values this transport handed a call (DV4-PLAN §5.7's
        exact-value scan; DV5c gaps lane): never written anywhere, only matched."""
        return tuple(sorted(self._tokens))

    def _credentials_src(self):
        if self.credentials is not None:
            return Path(self.credentials)
        home = os.environ.get("HOME", "")
        if not home:
            raise TransportError("auth", "HOME is unset: no credentials file")
        return Path(home) / ".claude" / CREDENTIALS

    def complete(self, message: str, *, system: str = "", seed=None) -> Completion:
        refuse_if_disabled()
        binary = apparatus.check_binary(self.table)
        state = Path(tempfile.mkdtemp(dir=self.state_base)) if self.state_base else \
            Path(tempfile.mkdtemp())
        cwd = Path(tempfile.mkdtemp(dir=self.cwd_base))
        try:
            os.chmod(state, 0o700)
            env = environment(state)
            Path(env["HOME"]).mkdir(mode=0o700)
            dst = derive_credentials(self._credentials_src(), env["CLAUDE_CONFIG_DIR"],
                                     now=self.now(), min_life_s=self.timeout_s + MARGIN_S)
            self._remember_token(dst)
            cmd = argv(binary, self.table, schema=self.schema, system=system, message=message)
            t0 = self.clock()
            try:
                p = subprocess.run(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=self.timeout_s)
            except subprocess.TimeoutExpired as e:
                out = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) \
                    else (e.stdout or "")
                raise TransportError("cli-crash", f"the call passed its {self.timeout_s:g} s cap",
                                     had_output=parse_stream(out)["assistant"] > 0) from None
            wall = self.clock() - t0
            self.last_raw = p.stdout
            left = sorted(os.listdir(cwd))
        finally:
            shutil.rmtree(cwd, ignore_errors=True)
            shutil.rmtree(state, ignore_errors=True)
        s = parse_stream(p.stdout)
        problems = init_problems(s["init"], self.table, cwd)
        if left:
            problems.append(f"the call left {len(left)} entries in its working directory")
        if problems:
            if s["init"] is None:
                tail = (p.stderr or "").strip().splitlines()[-1:]
                problems.append(f"exit {p.returncode}" + (f": {tail[0][:300]}" if tail else ""))
            raise _ran(ApparatusMismatch("the call's init assertions failed (the reply was "
                                         "discarded unread): " + "; ".join(problems)))
        info = s["rate_limit"][-1] if s["rate_limit"] else None
        verdict, reason, judged = self.overage.observe(info)
        if verdict == "stop":
            # the call ran (and may have been billed): the event that stopped it goes
            # with the exception, so the batch records it and the stop holds (DV5c)
            raise _ran(ApparatusMismatch(f"overage check: {reason}"), overage=True,
                       rate_limit=info)
        res = s["result"]
        had_output = s["assistant"] > 0
        if not isinstance(res, dict):
            raise TransportError("cli-crash", f"no result event (exit {p.returncode})",
                                 had_output=had_output)
        turns = res.get("num_turns")
        cap = int(self.table["max_turns"])
        max_turns = res.get("subtype") == "error_max_turns"
        if res.get("is_error") is not False and not max_turns:
            status = res.get("api_error_status")
            text = res.get("result") if isinstance(res.get("result"), str) else ""
            cause = "rate-limit" if status == 429 else "auth" if status in (401, 403) \
                or text.startswith("Not logged in") else "cli-crash"
            raise TransportError(cause, f"the call ended with an error (status {status!r}"
                                 + (f", {text[:120]!r}" if text and s["synthetic"] else "") + ")",
                                 had_output=had_output)
        if max_turns and not had_output:
            raise TransportError("cli-crash", "the turn cap ended a call without model output",
                                 had_output=False)
        if not isinstance(turns, int) or isinstance(turns, bool) or \
                (turns > cap and not max_turns):
            raise _ran(ApparatusMismatch(f"num_turns {turns!r} is above the pinned cap {cap}"))
        u = res.get("usage") if isinstance(res.get("usage"), dict) else {}
        usage = {"input_tokens": int(u.get("input_tokens") or 0)
                 + int(u.get("cache_creation_input_tokens") or 0)
                 + int(u.get("cache_read_input_tokens") or 0),
                 "output_tokens": int(u.get("output_tokens") or 0),
                 "modelUsage": res.get("modelUsage"),
                 "permission_denials": res.get("permission_denials"),
                 "total_cost_usd_notional": res.get("total_cost_usd")}
        structured = res.get("structured_output") if not max_turns else None
        return Completion(
            text=res.get("result") if isinstance(res.get("result"), str) and not max_turns
            else "",
            structured=structured if isinstance(structured, dict) else None,
            usage=usage, turns=turns, wall_s=round(wall, 3), rate_limit=judged,
            window=(verdict, reason),
            apparatus={"family": NAME, "version": self.table.get("version"),
                       "binary": self.table.get("binary"), "sha256": self.table.get("sha256"),
                       "model": self.table.get("model"), "effort": self.table.get("effort"),
                       "init_assertions": "passed", "prompt": PROMPT_NOTE, "seed": seed,
                       "allowed_overage": list(self.window.allowed_overage),
                       "ended": "max-turns" if max_turns else "completed"},
            raw=p.stdout)
