"""fvh.backends — the model transports and the adapter from a transport to a
Policy (DV4-PLAN §3.4; Δ63, Δ64, Δ65, Δ147, Δ148).

  Completion       one model call's result: the reply text, the structured
                   output (when the CLI returns one), token usage, turns,
                   wall-clock seconds, the call's rate-limit event, the
                   apparatus facts of the call, and the raw event stream
  build(family, app=None, **kw) -> transport
                   a transport built from the apparatus file only (family
                   "claude": fvh.backends.claude; "qwen": the local Qwen
                   through the opencode CLI, fvh.backends.opencode). With
                   FVH_NO_MODEL=1 in the environment, building one (and every
                   call) raises ModelDisabled before anything is executed:
                   the CI tripwire (DV4-PLAN §9)
  ModelPolicy(transport, render, parse=None, *, meter, system, seeds=...)
                   a Policy: render(state, ctx, budget) -> the message, one
                   call per proposal, the reply parsed into actions (by
                   default: the structured output or the reply's one JSON
                   value, validated against protocol.ACTION_SCHEMA; a reply
                   that does not validate raises protocol.Malformed)
  candidate_ask(transport, *, target, meter, system, ...) -> ask(prompt, seed)
                   the `ask` callable Q12's arms take: one model call; the
                   reply must validate against ACTION_SCHEMA and hold exactly
                   one Edit of the target in the whole-file form (an empty
                   `old`), whose `new` is returned as the candidate file's
                   full text; anything else raises protocol.Malformed (the
                   run ends `malformed`; the policy never sees the reply)
  smoke_render(state, ctx, budget)
                   the neutral smoke-test renderer (DV4-PLAN §14 Q7, as DV5
                   confirmed it): the task and the run as one JSON document,
                   for smoke runs only. A lab's renderer is the learner's.

Errors a transport raises (the executor maps each to an outcome, §4.3):
  TransportError(cause, had_output)   cause one of fvh.budget.TRUNCATION_CAUSES;
                   after model output the attempt is `truncated:<cause>`,
                   before any it is `infra-failed`
  apparatus.ApparatusMismatch          an init, overage or result assertion
                   failed: the reply is discarded unread and the batch stops
  Deferred                             the call must not start now (a
                   credential too close to its expiry, a window): the batch
                   defers, the attempt stays re-issuable

Every Qwen request of every mode passes the run's model gate (DV4-PLAN
§5.6.3), so the transports never name the model server's own address: the gate
address is a parameter of the run. Frozen (guard rule 2f), standard library
only. This directory is on scripts/check_single_route.py's allowlist: it is
one of the entry points that start a model CLI.
"""

import importlib
import json
import os
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from fvh import apparatus, budget, protocol
from fvh.apparatus import ApparatusMismatch

__all__ = ["ApparatusMismatch", "Completion", "Deferred", "FAMILY_MODULES", "ModelDisabled",
           "ModelPolicy", "NO_MODEL_ENV", "TransportError", "build", "candidate_ask",
           "default_parse", "one_json_value", "refuse_if_disabled", "smoke_render",
           "strip_think"]

NO_MODEL_ENV = "FVH_NO_MODEL"
FAMILY_MODULES = {budget.CLAUDE: "fvh.backends.claude", budget.QWEN: "fvh.backends.opencode"}


class ModelDisabled(RuntimeError):
    """FVH_NO_MODEL=1: no transport is built and no model call is made (CI)."""


class TransportError(RuntimeError):
    """A call cut by a cause outside the run (module docstring)."""

    def __init__(self, cause: str, message: str, *, had_output: bool = False):
        if cause not in budget.TRUNCATION_CAUSES:
            raise ValueError(f"cause must be one of {', '.join(budget.TRUNCATION_CAUSES)}")
        super().__init__(f"{cause}: {message}")
        self.cause = cause
        self.had_output = had_output


class Deferred(RuntimeError):
    """The call must not start now; the batch defers (never an attempt's outcome)."""


@dataclass(frozen=True)
class Completion:
    text: str
    structured: dict | None = None
    usage: dict = field(default_factory=dict)
    turns: int = 1
    wall_s: float = 0.0
    gpu_s: float = 0.0
    rate_limit: dict | None = None
    window: tuple = ("ok", "")
    apparatus: dict = field(default_factory=dict)
    raw: str = ""

    def __hash__(self):
        return hash((self.text, self.turns, self.wall_s))

    def tokens(self) -> tuple[int, int]:
        u = self.usage or {}

        def n(k):
            v = u.get(k)
            return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else 0
        return n("input_tokens"), n("output_tokens")


def refuse_if_disabled() -> None:
    if os.environ.get(NO_MODEL_ENV) == "1":
        raise ModelDisabled(f"{NO_MODEL_ENV}=1 is set (the CI environment): no transport is "
                            "built and no model is called")


def build(family: str, app=None, **kw):
    """A transport of `family` from the apparatus file (module docstring)."""
    refuse_if_disabled()
    if family not in FAMILY_MODULES:
        raise ValueError(f"family must be one of {', '.join(FAMILY_MODULES)}")
    app = app if app is not None else apparatus.load()
    mod = importlib.import_module(FAMILY_MODULES[family])
    return mod.Transport(app.backend(family), window=app.window(), **kw)


_THINK = re.compile(r"<think>.*?</think>", re.S)


def strip_think(text: str) -> str:
    """The reply with every <think>…</think> block removed (design §11.1)."""
    out = _THINK.sub("", text)
    if "<think>" in out:                       # an unclosed block: drop to the end
        out = out.split("<think>", 1)[0]
    return out


def one_json_value(text: str):
    """The one JSON value a reply consists of (surrounding blanks and one
    ```json fence allowed); protocol.Malformed otherwise."""
    s = strip_think(text).strip()
    m = re.fullmatch(r"```(?:json)?\s*\n(.*?)\n?```", s, re.S)
    if m:
        s = m.group(1).strip()
    try:
        value, end = json.JSONDecoder().raw_decode(s)
    except ValueError as e:
        raise protocol.Malformed(f"the reply is not one JSON value ({e})") from None
    if s[end:].strip():
        raise protocol.Malformed("the reply holds text after its JSON value")
    return value


def default_parse(completion: Completion, ctx: protocol.Context) -> list:
    obj = completion.structured if completion.structured is not None \
        else one_json_value(completion.text)
    return protocol.parse_proposal(obj, max_actions=ctx.max_actions)


def _charge(meter, completion):
    if meter is None:
        return
    tin, tout = completion.tokens()
    meter.charge(calls=1, tokens_in=tin, tokens_out=tout, gpu_s=completion.gpu_s, output=True)


def _call(transport, meter, message, *, system, seed, on_call):
    if meter is not None:
        meter.before_call()
    try:
        c = transport.complete(message, system=system, seed=seed)
    except TransportError as e:
        if meter is not None:
            meter.charge(calls=1, output=False)
        if on_call is not None:
            on_call(None, e)
        raise
    except ApparatusMismatch as e:
        if getattr(e, "ran", False) and meter is not None:
            meter.charge(calls=1, output=False)   # the CLI ran: the call is spent (DV5c)
        if on_call is not None:
            on_call(None, e)
        raise
    _charge(meter, c)
    if on_call is not None:
        on_call(c, None)
    return c


class ModelPolicy:
    """A transport as a Policy (module docstring)."""

    def __init__(self, transport, render: Callable, parse: Callable | None = None, *,
                 meter: budget.Meter | None = None, system: str = "",
                 seeds: Iterable[int] | None = None, on_call: Callable | None = None):
        self.transport = transport
        self.render = render
        self.parse = parse or default_parse
        self.meter = meter
        self.system = system
        self.seeds = list(seeds) if seeds is not None else None
        self.on_call = on_call
        self.calls = 0

    def propose(self, state, ctx, budget_) -> list:
        message = self.render(state, ctx, budget_)
        if not isinstance(message, str):
            raise TypeError("render returns the message text")
        seed = None
        if self.seeds is not None:
            if self.calls >= len(self.seeds):
                raise budget.CapReached("call-cap", "the pre-registered seeds are used up")
            seed = self.seeds[self.calls]
        c = _call(self.transport, self.meter, message, system=self.system, seed=seed,
                  on_call=self.on_call)
        self.calls += 1
        return list(self.parse(c, ctx))


def candidate_ask(transport, *, target: str, meter: budget.Meter | None = None,
                  system: str = "", on_call: Callable | None = None,
                  max_actions: int = protocol.MAX_ACTIONS) -> Callable[[str, int], str]:
    """The `ask(prompt, seed) -> candidate text` callable (module docstring)."""

    def ask(prompt: str, seed: int) -> str:
        c = _call(transport, meter, prompt, system=system, seed=seed, on_call=on_call)
        obj = c.structured if c.structured is not None else one_json_value(c.text)
        actions = protocol.parse_proposal(obj, max_actions=max_actions)
        edits = [a for a in actions if isinstance(a, protocol.Edit)]
        others = [a for a in actions if not isinstance(a, (protocol.Edit, protocol.Verify))]
        if len(edits) != 1 or others:
            raise protocol.Malformed("a candidate reply holds exactly one edit (and at most a "
                                     "verify), not " + ", ".join(type(a).__name__ for a in actions))
        e = edits[0]
        if e.path != target:
            raise protocol.Malformed(f"the candidate edits {e.path!r}, not the target {target!r}")
        if e.old != "":
            raise protocol.Malformed("a candidate is a whole file: its edit's old is empty")
        return e.new

    return ask


def smoke_render(state: protocol.State, ctx: protocol.Context, budget_: protocol.Budget) -> str:
    """The neutral smoke-test renderer: the task and the run as one JSON document."""
    doc = {"task": ctx.task_id, "lang": ctx.lang, "statement": ctx.statement,
           "editable": list(ctx.editable), "readable": list(ctx.readable),
           "target": ctx.target, "step": state.step, "files": dict(state.files),
           "last_verdict": (state.last_verify or {}).get("verdict"),
           "answer_with": "one JSON object matching the action schema"}
    return json.dumps(doc, sort_keys=True, ensure_ascii=False)
