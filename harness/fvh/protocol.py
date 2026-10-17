"""fvh.protocol — the policy protocol: typed actions, the run's state, context and
budget, observations, and the action JSON schema (DV4-PLAN §3.2; design §10.3;
spec §5.6). Frozen from its first build: changing a name here needs a DELTAS
entry (DV4-PLAN §13).

    propose(state, ctx, budget) -> list[Action]

A policy proposes actions and never acts: actions are pure data, a policy holds
no tool and touches no file. The executor (fvh.executor) is the only thing
that validates and performs them, on the run's work copy.

Actions (frozen dataclasses, built by keyword, compared by value):

  Read(path, start=None, end=None)
      `path` must be readable (ctx.readable, or ctx.editable); `start` and
      `end` are 1-based line numbers, inclusive (None: from the first line /
      to the last). The observation holds at most ctx.read_limit bytes.
  Edit(path, old, new)
      `path` must be in ctx.editable. `old` must occur exactly once in the
      work copy's text of `path`, and is replaced by `new`; an empty `old` is
      the whole-file form: `new` becomes the file's whole text. `new` holds
      at most NEW_LIMIT characters. Edits apply to the run's work copy, never
      to the learner's tree.
  Verify(mode="gate")
      runs the task's pinned gate on the work copy in the verification
      container (fvh.tools' ContainerRunner; ReplayRunner in CI). `mode` is
      "loop" or "gate"; at this build both run the pinned gate instrument
      (`vcheck --gate`, the one verifier instrument fvh.tools has). The
      observation's `verdict` is the gate's own JSON document.
  Stop(reason, note="")
      ends the run. `reason` is "done" or "give-up"; `note` at most
      NOTE_LIMIT characters.

State(task_id, step, files, last_verify, history)
    step       0 at the first proposal, then 1, 2, …
    files      path -> sha256 of the work copy's text (UTF-8)
    last_verify  the last verification document of the run, or None
    history    the earlier turns: Turn(step, actions, observations)
Context(task_id, lang, statement, editable, readable, target, max_actions,
        read_limit, material)
    material   the task's prompt material as the pre-registration fixes it
               (a read-only mapping; e.g. "instructions", "text")
Budget(calls_left, tokens_left, wall_s_left, gpu_s_left)
    a snapshot; None means no cap on that unit. `exhausted` is True once any
    capped unit is at or below 0.
Observation(kind, ok, text, verdict=None, cut=0)
    kind       "read", "edit", "verify", "stop" or "refused"
    text       truncated to the read limit, with the cut stated in the text
               and in `cut` (the number of bytes cut)
    verdict    the verification document, for a Verify

ACTION_SCHEMA is the JSON schema (draft 2020-12) of one proposal,
{"actions": [...]}: each action an object whose "type" is "read", "edit",
"verify" or "stop", with the fields above. `parse_proposal` is its validator
(the same rules, in code); a reply that does not validate raises Malformed,
which the executor scores as the attempt's outcome `malformed` (it counts as
a call and ends the run). The harness never repairs a reply.

Frozen (guard rule 2f), standard library only.
"""

import dataclasses
import hashlib
import json
import types
from collections.abc import Mapping
from dataclasses import dataclass

__all__ = ["ACTION_SCHEMA", "ACTION_TYPES", "Action", "Budget", "Context", "Edit",
           "MAX_ACTIONS", "Malformed", "NEW_LIMIT", "NOTE_LIMIT", "OBSERVATION_KINDS",
           "Observation", "READ_LIMIT", "Read", "STOP_REASONS", "State", "Stop", "Turn",
           "VERIFY_MODES", "Verify", "action_from_json", "action_to_json", "clip",
           "observation_from_json", "observation_to_json", "parse_proposal",
           "proposal_to_json", "text_sha256"]

READ_LIMIT = 64 * 1024        # [A] bytes of one Read's observation
NEW_LIMIT = 64 * 1024         # [A] characters of one Edit's `new`
NOTE_LIMIT = 2048             # characters of a Stop's note
MAX_ACTIONS = 8               # [A] actions per proposal
VERIFY_MODES = ("loop", "gate")
STOP_REASONS = ("done", "give-up")
OBSERVATION_KINDS = ("read", "edit", "verify", "stop", "refused")


class Malformed(ValueError):
    """A proposal that does not validate against ACTION_SCHEMA: the attempt's
    outcome is `malformed`; it is never repaired."""


def _str(owner, name, value, *, empty=True, limit=None):
    if not isinstance(value, str):
        raise TypeError(f"{owner}.{name} must be a str, not {type(value).__name__}")
    if not empty and not value:
        raise ValueError(f"{owner}.{name} must not be empty")
    if limit is not None and len(value) > limit:
        raise ValueError(f"{owner}.{name} holds {len(value)} characters, more than {limit}")


def _line(owner, name, value):
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{owner}.{name} must be an int or None")
    if value < 1:
        raise ValueError(f"{owner}.{name} is a 1-based line number, not {value}")


@dataclass(frozen=True)
class Read:
    """Read `path` (lines `start` to `end`, 1-based, inclusive)."""

    path: str
    start: int | None = None
    end: int | None = None

    def __post_init__(self):
        _str("Read", "path", self.path, empty=False)
        _line("Read", "start", self.start)
        _line("Read", "end", self.end)
        if self.start is not None and self.end is not None and self.end < self.start:
            raise ValueError("Read.end comes before Read.start")


@dataclass(frozen=True)
class Edit:
    """Replace the one occurrence of `old` in `path` by `new` (`old` empty: the whole file)."""

    path: str
    old: str
    new: str

    def __post_init__(self):
        _str("Edit", "path", self.path, empty=False)
        _str("Edit", "old", self.old)
        _str("Edit", "new", self.new, limit=NEW_LIMIT)


@dataclass(frozen=True)
class Verify:
    """Run the task's pinned gate on the work copy."""

    mode: str = "gate"

    def __post_init__(self):
        if self.mode not in VERIFY_MODES:
            raise ValueError(f"Verify.mode must be one of {', '.join(VERIFY_MODES)}, "
                             f"not {self.mode!r}")


@dataclass(frozen=True)
class Stop:
    """End the run."""

    reason: str
    note: str = ""

    def __post_init__(self):
        if self.reason not in STOP_REASONS:
            raise ValueError(f"Stop.reason must be one of {', '.join(STOP_REASONS)}, "
                             f"not {self.reason!r}")
        _str("Stop", "note", self.note, limit=NOTE_LIMIT)


Action = Read | Edit | Verify | Stop
ACTION_TYPES = {"read": Read, "edit": Edit, "verify": Verify, "stop": Stop}
_TYPE_OF = {cls: name for name, cls in ACTION_TYPES.items()}


def text_sha256(text: str) -> str:
    """sha256 of a text's UTF-8 bytes (the digests State.files holds)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clip(text: str, limit: int) -> tuple[str, int]:
    """(text, cut): at most `limit` UTF-8 bytes of `text` (cut on a character
    boundary), with a last line stating the bytes cut; cut is 0 when nothing was."""
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text, 0
    kept = data[:limit].decode("utf-8", errors="ignore")
    cut = len(data) - len(kept.encode("utf-8"))
    return kept + f"\n[... {cut} bytes cut: the observation holds at most {limit} bytes]", cut


@dataclass(frozen=True)
class Observation:
    """What the executor observed for one action."""

    kind: str
    ok: bool
    text: str
    verdict: dict | None = None
    cut: int = 0

    def __post_init__(self):
        if self.kind not in OBSERVATION_KINDS:
            raise ValueError(f"Observation.kind must be one of {', '.join(OBSERVATION_KINDS)}")
        if not isinstance(self.ok, bool):
            raise TypeError("Observation.ok must be a bool")
        _str("Observation", "text", self.text)
        if self.verdict is not None and not isinstance(self.verdict, dict):
            raise TypeError("Observation.verdict must be a dict or None")
        if isinstance(self.cut, bool) or not isinstance(self.cut, int) or self.cut < 0:
            raise ValueError("Observation.cut must be an int >= 0")

    def __hash__(self):
        return hash((self.kind, self.ok, self.text, self.cut))


@dataclass(frozen=True)
class Turn:
    """One earlier proposal of the run and its observations."""

    step: int
    actions: tuple
    observations: tuple

    def __hash__(self):
        return hash((self.step, self.actions, self.observations))


def _frozen_map(value, owner, name):
    if not isinstance(value, Mapping):
        raise TypeError(f"{owner}.{name} must be a mapping")
    return types.MappingProxyType(dict(value))


def _paths(value, owner, name):
    if isinstance(value, str) or not all(isinstance(p, str) and p for p in value):
        raise TypeError(f"{owner}.{name} must be a sequence of non-empty path strings")
    return tuple(value)


def _count(owner, name, value, *, low=0):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{owner}.{name} must be an int")
    if value < low:
        raise ValueError(f"{owner}.{name} must be >= {low}, not {value}")


@dataclass(frozen=True)
class Context:
    """The task as the policy sees it (fixed for the whole run)."""

    task_id: str
    lang: str
    statement: str
    editable: tuple
    readable: tuple
    target: str
    max_actions: int = MAX_ACTIONS
    read_limit: int = READ_LIMIT
    material: Mapping = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        _str("Context", "task_id", self.task_id, empty=False)
        _str("Context", "lang", self.lang, empty=False)
        _str("Context", "statement", self.statement)
        object.__setattr__(self, "editable", _paths(self.editable, "Context", "editable"))
        object.__setattr__(self, "readable", _paths(self.readable, "Context", "readable"))
        _str("Context", "target", self.target, empty=False)
        if self.target not in self.editable:
            raise ValueError(f"Context.target {self.target!r} must be one of the editable paths")
        _count("Context", "max_actions", self.max_actions, low=1)
        _count("Context", "read_limit", self.read_limit, low=1)
        object.__setattr__(self, "material", _frozen_map(self.material, "Context", "material"))

    def __hash__(self):
        return hash((self.task_id, self.lang, self.target, self.editable, self.readable))

    def may_read(self, path: str) -> bool:
        return path in self.readable or path in self.editable


@dataclass(frozen=True)
class State:
    """The run so far, as the policy sees it before a proposal."""

    task_id: str
    step: int
    files: Mapping
    last_verify: dict | None = None
    history: tuple = ()

    def __post_init__(self):
        _str("State", "task_id", self.task_id, empty=False)
        _count("State", "step", self.step)
        object.__setattr__(self, "files", _frozen_map(self.files, "State", "files"))
        if self.last_verify is not None and not isinstance(self.last_verify, dict):
            raise TypeError("State.last_verify must be a dict or None")
        object.__setattr__(self, "history", tuple(self.history))

    def __hash__(self):
        return hash((self.task_id, self.step, tuple(sorted(self.files.items()))))


@dataclass(frozen=True)
class Budget:
    """A snapshot of what is left of the run's caps (None: that unit has no cap)."""

    calls_left: int | None = None
    tokens_left: int | None = None
    wall_s_left: float | None = None
    gpu_s_left: float | None = None

    def __post_init__(self):
        for f in dataclasses.fields(self):
            v = getattr(self, f.name)
            if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float))):
                raise TypeError(f"Budget.{f.name} must be a number or None")

    @property
    def exhausted(self) -> bool:
        """True once any capped unit is at or below 0."""
        return any(v is not None and v <= 0 for v in (self.calls_left, self.tokens_left,
                                                       self.wall_s_left, self.gpu_s_left))


# =====================================================================================
# JSON: the schema, the validator and the round trip
# =====================================================================================

_LINE_SCHEMA = {"type": ["integer", "null"], "minimum": 1}
ACTION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "proposal",
    "type": "object",
    "additionalProperties": False,
    "required": ["actions"],
    "properties": {
        "actions": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_ACTIONS,
            "items": {"oneOf": [
                {"type": "object", "additionalProperties": False, "required": ["type", "path"],
                 "properties": {"type": {"const": "read"},
                                "path": {"type": "string", "minLength": 1},
                                "start": _LINE_SCHEMA, "end": _LINE_SCHEMA}},
                {"type": "object", "additionalProperties": False,
                 "required": ["type", "path", "old", "new"],
                 "properties": {"type": {"const": "edit"},
                                "path": {"type": "string", "minLength": 1},
                                "old": {"type": "string"},
                                "new": {"type": "string", "maxLength": NEW_LIMIT}}},
                {"type": "object", "additionalProperties": False, "required": ["type", "mode"],
                 "properties": {"type": {"const": "verify"},
                                "mode": {"enum": list(VERIFY_MODES)}}},
                {"type": "object", "additionalProperties": False, "required": ["type", "reason"],
                 "properties": {"type": {"const": "stop"},
                                "reason": {"enum": list(STOP_REASONS)},
                                "note": {"type": "string", "maxLength": NOTE_LIMIT}}},
            ]},
        },
    },
}

_REQUIRED = {"read": {"type", "path"}, "edit": {"type", "path", "old", "new"},
             "verify": {"type", "mode"}, "stop": {"type", "reason"}}
_ALLOWED = {"read": {"type", "path", "start", "end"}, "edit": {"type", "path", "old", "new"},
            "verify": {"type", "mode"}, "stop": {"type", "reason", "note"}}


def action_to_json(action) -> dict:
    """The JSON object of one action (ACTION_SCHEMA's item form)."""
    kind = _TYPE_OF.get(type(action))
    if kind is None:
        raise TypeError(f"{type(action).__name__} is not an action")
    obj = {"type": kind}
    for f in dataclasses.fields(action):
        v = getattr(action, f.name)
        if kind == "read" and f.name in ("start", "end") and v is None:
            continue
        obj[f.name] = v
    return obj


def action_from_json(obj) -> Action:
    """One action from its JSON object; Malformed when it does not validate."""
    if not isinstance(obj, dict):
        raise Malformed(f"an action is a JSON object, not {type(obj).__name__}")
    kind = obj.get("type")
    if kind not in ACTION_TYPES:
        raise Malformed(f"an action's type must be one of {', '.join(ACTION_TYPES)}, "
                        f"not {kind!r}")
    keys = set(obj)
    if not _REQUIRED[kind] <= keys:
        raise Malformed(f"a {kind} action needs " + ", ".join(sorted(_REQUIRED[kind] - keys)))
    if not keys <= _ALLOWED[kind]:
        raise Malformed(f"a {kind} action has no field " + ", ".join(sorted(keys - _ALLOWED[kind])))
    fields = {k: v for k, v in obj.items() if k != "type"}
    try:
        return ACTION_TYPES[kind](**fields)
    except (TypeError, ValueError) as e:
        raise Malformed(f"a {kind} action does not validate: {e}") from None


def proposal_to_json(actions) -> dict:
    """{"actions": [...]}: one proposal as ACTION_SCHEMA describes it."""
    return {"actions": [action_to_json(a) for a in actions]}


def parse_proposal(obj, *, max_actions: int = MAX_ACTIONS) -> list:
    """The actions of one proposal (a dict, or its JSON text); Malformed when it
    does not validate against ACTION_SCHEMA (or holds more than max_actions)."""
    if isinstance(obj, (str, bytes)):
        try:
            obj = json.loads(obj)
        except ValueError as e:
            raise Malformed(f"the reply is not JSON ({e})") from None
    if not isinstance(obj, dict):
        raise Malformed(f"a proposal is a JSON object, not {type(obj).__name__}")
    if set(obj) != {"actions"}:
        raise Malformed("a proposal is an object with exactly one field, actions")
    acts = obj["actions"]
    if not isinstance(acts, list):
        raise Malformed("a proposal's actions are a JSON array")
    if not acts:
        raise Malformed("a proposal holds at least one action")
    limit = min(max_actions, MAX_ACTIONS)
    if len(acts) > limit:
        raise Malformed(f"a proposal holds at most {limit} actions, not {len(acts)}")
    return [action_from_json(a) for a in acts]


def observation_to_json(obs: Observation) -> dict:
    return dataclasses.asdict(obs)


def observation_from_json(obj) -> Observation:
    if not isinstance(obj, dict):
        raise ValueError("an observation is a JSON object")
    return Observation(**obj)
