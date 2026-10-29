"""fvh.backends.opencode — the local Qwen through the opencode CLI, on the host,
tool-less (DV4-PLAN §3.4; Δ64, Δ65, Δ146; an OpenAI-compatible server, Δ505).

Δ64's recipe, pinned:

  - argv `<pinned opencode> run --pure --format json -m <provider>/<model id>
    <message>`, from a fresh mktemp directory under /tmp (outside $HOME); the
    binary path ("~/...") and its sha256 come from the apparatus file.
  - `env -i` with HOME and every XDG_* directory in the call's state
    directory, OPENCODE_CONFIG naming the call's config, LANG=C.UTF-8,
    TERM=dumb, and the eight OPENCODE_DISABLE_* switches.
  - the config {"permission": {"*": "deny"}, "tools": {"*": false}, "mcp": {},
    "autoupdate": false, "share": "disabled"} plus one provider whose base URL
    is this run's model gate (DV4-PLAN §5.6.3), never the model server's own
    address, whose model is the one the host's server serves (Δ505:
    fvh.backends.gate.discover), and whose model entry states the served
    max_model_len (when the server reports one) as its context limit and the
    course's max_tokens as its output limit; and the title agent disabled and automatic compaction off, so that
    one call is one gated request (DV4 step 3c's probe: without them every
    `run` first sends a title request of its own, ~600 prompt tokens).
  - a per-call precheck before the call, without a model call: `debug agent
    build --pure` must show every tool false and no `allow` rule for
    `external_directory` outside the call's state directory (patterns the
    apparatus file lists in `external_ok` excepted), and `debug config --pure`
    must show the gate's address as the only provider URL. The two outputs'
    shapes are DV0's recorded ones (infra/opencode-iso-config-B3).
  - the reply: `<think>` blocks are stripped; what is left must be exactly one
    JSON value (the caller validates it against ACTION_SCHEMA). A server
    that returns the thinking apart (`reasoning` or `reasoning_content`) has
    it read as a reasoning part by the bundled @ai-sdk/openai-compatible
    (checked in the 1.18.25 binary, Δ505), never as text; a server that
    leaves `<think>` in the text has it stripped.

As probed at DV4 step 3c on 1.18.25 through a host gate (the author probe
archive's dv5b/dv4s3/3c-policy/): the `run --format json` stream holds
step_start, text (the reply in `part.text`) and step_finish events (`part.tokens`
with input, output and reasoning counts), which is what this build reads; the
gate's own counts are the budget's either way (DV4-PLAN §4.1). opencode sends
the model entry's seed and max_tokens = min(the output limit, 32000), and no
temperature, top_p or top_k: the gate sets the pins (Δ505: as OpenAI fields). The system
prompt is sent as the message's first paragraph, after opencode's own system
prompt, which every call carries (~3,700 characters).
"""

import json
import os
import shutil
import subprocess
import tempfile
import time
from collections.abc import Mapping
from pathlib import Path

from fvh import apparatus, budget
from fvh.backends import (ApparatusMismatch, Completion, TransportError, refuse_if_disabled,
                          strip_think)

__all__ = ["DISABLE", "NAME", "PROVIDER", "Transport", "argv", "config", "environment",
           "parse_events", "precheck_problems"]

NAME = budget.QWEN
PROVIDER = "fvhgate"
DISABLE = tuple(f"OPENCODE_DISABLE_{s}" for s in (
    "CLAUDE_CODE", "EXTERNAL_SKILLS", "PROJECT_CONFIG", "AUTOUPDATE", "MODELS_FETCH",
    "LSP_DOWNLOAD", "SHARE", "DEFAULT_PLUGINS"))
XDG = {"XDG_CONFIG_HOME": ".config", "XDG_DATA_HOME": ".local/share",
       "XDG_CACHE_HOME": ".cache", "XDG_STATE_HOME": ".local/state"}
DEFAULT_TIMEOUT_S = 900               # [A] one policy call's wall-clock cap


def config(table: Mapping, *, gate_url: str, model: str, context=None, output=4096,
           seed=None) -> dict:
    """The call's opencode config (module docstring): `model` the served model
    id, `context` its served max_model_len (None: not reported, no limit
    stated), `output` the course's max_tokens."""
    tag = model
    if not isinstance(tag, str) or not tag:
        raise apparatus.ApparatusError("a Qwen call needs the served model id (discover())")
    model = {"name": tag}
    if isinstance(context, int) and not isinstance(context, bool) and context > 0:
        model["limit"] = {"context": context, "output": int(output)}
    if seed is not None:
        model["options"] = {"seed": seed}
    return {"$schema": "https://opencode.ai/config.json", "autoupdate": False,
            "share": "disabled", "permission": {"*": "deny"}, "tools": {"*": False}, "mcp": {},
            "agent": {"title": {"disable": True}}, "compaction": {"auto": False},
            "model": f"{PROVIDER}/{tag}",
            "provider": {PROVIDER: {"npm": str(table.get("provider_npm",
                                                         "@ai-sdk/openai-compatible")),
                                    "name": "fvh model gate",
                                    "options": {"baseURL": gate_url},
                                    "models": {tag: model}}}}


def environment(state: Path) -> dict:
    home = state / "home"
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "LANG": "C.UTF-8", "TERM": "dumb",
           "OPENCODE_CONFIG": str(state / "opencode.json")}
    env.update({k: str(home / v) for k, v in XDG.items()})
    env.update({k: "1" for k in DISABLE})
    return env


def argv(binary, model: str, message: str) -> list[str]:
    return [str(binary), "run", "--pure", "--format", "json", "-m",
            f"{PROVIDER}/{model}", message]


def _urls(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "baseURL" and isinstance(v, str):
                yield v
            else:
                yield from _urls(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _urls(v)


def precheck_problems(agent_json: str, config_json: str, *, state: Path, gate_url: str,
                      external_ok=()) -> list[str]:
    """The per-call gate's findings on the two debug outputs; empty when it passes."""
    out = []
    try:
        agent = json.loads(agent_json)
        conf = json.loads(config_json)
    except ValueError:
        return ["a debug output is not JSON"]
    tools = agent.get("tools") if isinstance(agent, dict) else None
    if not isinstance(tools, dict) or not tools:
        out.append("debug agent build lists no tools table")
    else:
        on = sorted(k for k, v in tools.items() if v is not False)
        if on:
            out.append("tools not disabled: " + ", ".join(on))
    for rule in (agent.get("permission") or []) if isinstance(agent, dict) else []:
        if not isinstance(rule, dict) or rule.get("permission") != "external_directory":
            continue
        pat = str(rule.get("pattern", ""))
        if rule.get("action") == "allow" and not pat.startswith(str(state) + "/") \
                and pat not in external_ok:
            out.append(f"an external_directory allow rule outside the call's directory: {pat}")
    urls = sorted(set(_urls(conf)))
    if urls != [gate_url]:
        out.append(f"provider URLs {urls}, not only the gate {gate_url}")
    return out


def parse_events(stdout: str) -> tuple[str, dict, int]:
    """(reply text, usage, events) from `run --format json` (module docstring: [probe])."""
    texts, tin, tout, n = [], 0, 0, 0
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        n += 1
        part = e.get("part") if isinstance(e.get("part"), dict) else {}
        if e.get("type") == "text" and isinstance(part.get("text"), str):
            texts.append(part["text"])
        tok = part.get("tokens") if isinstance(part.get("tokens"), dict) else None
        if e.get("type") == "step_finish" and tok:
            tin += int(tok.get("input") or 0)
            tout += int(tok.get("output") or 0)
    return "".join(texts), {"input_tokens": tin, "output_tokens": tout}, n


class Transport:
    """One local Qwen policy call per complete() (module docstring)."""

    family = NAME

    def __init__(self, table: Mapping, *, gate_url: str, model: str | None = None,
                 context: int | None = None, options: Mapping | None = None, window=None,
                 state_base=None, timeout_s: float | None = None, cwd_base: str = "/tmp",
                 clock=time.monotonic):
        refuse_if_disabled()
        if not isinstance(gate_url, str) or not gate_url.startswith(("http://", "https://")):
            raise ValueError("gate_url is the run's model gate (an http URL)")
        self.table = dict(table)
        self.gate_url = gate_url
        self.model = model
        self.context = context
        self.output = int((options or {}).get("max_tokens", 4096))
        self.state_base = Path(state_base) if state_base is not None else None
        self.timeout_s = timeout_s or float(self.table.get("call_timeout_s", DEFAULT_TIMEOUT_S))
        self.cwd_base = cwd_base
        self.clock = clock

    def _run(self, cmd, cwd, env, timeout):
        return subprocess.run(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)

    def complete(self, message: str, *, system: str = "", seed=None) -> Completion:
        refuse_if_disabled()
        binary = apparatus.check_binary(self.table)
        state = Path(tempfile.mkdtemp(dir=self.state_base)) if self.state_base else \
            Path(tempfile.mkdtemp())
        cwd = Path(tempfile.mkdtemp(dir=self.cwd_base))
        try:
            os.chmod(state, 0o700)
            env = environment(state)
            for k in ("HOME", *XDG):
                Path(env[k]).mkdir(parents=True, exist_ok=True)
            conf = config(self.table, gate_url=self.gate_url, model=self.model,
                          context=self.context, output=self.output, seed=seed)
            Path(env["OPENCODE_CONFIG"]).write_text(json.dumps(conf, indent=1), encoding="utf-8")
            try:
                a = self._run([str(binary), "debug", "agent", "build", "--pure"], cwd, env, 120)
                c = self._run([str(binary), "debug", "config", "--pure"], cwd, env, 120)
            except subprocess.TimeoutExpired:
                raise TransportError("cli-crash", "the precheck did not answer") from None
            if a.returncode != 0 or c.returncode != 0:
                raise ApparatusMismatch("the per-call precheck failed to run (exit "
                                        f"{a.returncode}, {c.returncode})")
            problems = precheck_problems(a.stdout, c.stdout, state=state, gate_url=self.gate_url,
                                         external_ok=tuple(self.table.get("external_ok", ())))
            if problems:
                raise ApparatusMismatch("the per-call precheck failed: " + "; ".join(problems))
            text_in = f"{system}\n\n{message}" if system else message
            t0 = self.clock()
            try:
                p = self._run(argv(binary, self.model, text_in), cwd, env, self.timeout_s)
            except subprocess.TimeoutExpired:
                raise TransportError("cli-crash", f"the call passed its {self.timeout_s:g} s cap",
                                     had_output=False) from None
            wall = self.clock() - t0
        finally:
            shutil.rmtree(cwd, ignore_errors=True)
            shutil.rmtree(state, ignore_errors=True)
        text, usage, _ = parse_events(p.stdout)
        if p.returncode != 0:
            raise TransportError("cli-crash", f"the CLI exited {p.returncode}",
                                 had_output=bool(text.strip()))
        return Completion(text=strip_think(text), structured=None, usage=usage, turns=1,
                          wall_s=round(wall, 3),
                          apparatus={"family": NAME, "version": self.table.get("version"),
                                     "binary": self.table.get("binary"),
                                     "sha256": self.table.get("sha256"),
                                     "model": self.model,
                                     "max_model_len": self.context, "seed": seed,
                                     "gate": self.gate_url},
                          raw=p.stdout)
