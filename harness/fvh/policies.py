"""fvh.policies — the Policy protocol and the CI-safe policies (DV4-PLAN §3.3).

  Policy          the protocol: propose(state, ctx, budget) -> list[Action]
  MockPolicy(fn)  a deterministic function of (state, ctx, budget)
  ScriptedPolicy(proposals)
                  the n-th proposal at step n; ScriptExhausted when the
                  script runs out
  ReplayPolicy(run_dir)
                  replays a recorded run's actions.jsonl proposal by proposal
                  and checks, at each step, that the state's file digests
                  equal the recorded ones: a difference raises ReplayDiverged
                  (the outcome `replay-diverged`). A recorded malformed reply
                  raises Malformed again at its step, and the end of the
                  recording raises ReplayEnd, so the executor reproduces the
                  recorded outcome. `fvh report` re-derives outcomes with it.

  MolePolicy(inner, plants, *, label_sink=None)
                  the red-team wrapper of Q33's pipeline (QPLAN §35.3, DELTAS
                  Δ402): at each planted step it returns the plant's actions
                  instead of the inner policy's proposal (the inner policy is
                  not asked at that step), and passes every other step
                  through. `plants` maps a step to (plant_id, actions); the
                  plant id never enters a proposal: it goes only to
                  `injected` and to `label_sink(step, plant_id)` (the label
                  file the evaluator alone reads)

None of them calls a model. The model policies (fvh.backends.ModelPolicy) and
the learner's policies (Q12's harness/q/fvh_q/policies.py) follow the same
protocol.

actions.jsonl (written by fvh.executor, one line per proposal):
    {"step": n, "files": {path: sha256, ...}, "actions": [...]}      or
    {"step": n, "files": {...}, "malformed": "<why>"}

Frozen (guard rule 2f), standard library only.
"""

import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from fvh import protocol

__all__ = ["MockPolicy", "MolePolicy", "Policy", "ReplayDiverged", "ReplayEnd", "ReplayPolicy",
           "ScriptExhausted", "ScriptedPolicy", "load_actions"]


@runtime_checkable
class Policy(Protocol):
    """A policy proposes typed actions and never acts (design §10.3)."""

    def propose(self, state: protocol.State, ctx: protocol.Context,
                budget: protocol.Budget) -> list: ...


class ScriptExhausted(LookupError):
    """A ScriptedPolicy was asked for a step its script does not hold."""


class ReplayDiverged(RuntimeError):
    """A replayed run's state differs from the recording (`replay-diverged`)."""


class ReplayEnd(LookupError):
    """The recording holds no proposal for this step (the recorded run ended here)."""


def _actions(seq):
    out = list(seq)
    for a in out:
        if type(a) not in protocol.ACTION_TYPES.values():
            raise TypeError(f"a proposal holds actions, not {type(a).__name__}")
    return out


class MockPolicy:
    """propose = fn(state, ctx, budget), as a list of actions."""

    def __init__(self, fn: Callable):
        if not callable(fn):
            raise TypeError("MockPolicy takes a function of (state, ctx, budget)")
        self.fn = fn

    def propose(self, state, ctx, budget) -> list:
        return _actions(self.fn(state, ctx, budget))


class ScriptedPolicy:
    """The n-th proposal at step n."""

    def __init__(self, proposals: Sequence):
        self.proposals = [tuple(_actions(p)) for p in proposals]

    def propose(self, state, ctx, budget) -> list:
        n = state.step
        if n >= len(self.proposals):
            raise ScriptExhausted(f"the script holds {len(self.proposals)} proposals; "
                                  f"step {n} has none")
        return list(self.proposals[n])


def load_actions(path) -> list[dict]:
    """The records of an actions.jsonl file, in order (ValueError naming a bad line)."""
    p = Path(path)
    out = []
    for ln, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            raise ValueError(f"{p}:{ln}: not JSON") from None
        if not isinstance(rec, dict) or not isinstance(rec.get("step"), int) \
                or not isinstance(rec.get("files"), dict) \
                or ("actions" in rec) == ("malformed" in rec):
            raise ValueError(f"{p}:{ln}: a proposal record holds step, files and exactly one "
                             "of actions or malformed")
        out.append(rec)
    steps = [r["step"] for r in out]
    if steps != list(range(len(steps))):
        raise ValueError(f"{p}: the recorded steps are not 0, 1, 2, … in order")
    return out


class ReplayPolicy:
    """Replays a recorded run (module docstring)."""

    def __init__(self, run_dir):
        self.run_dir = Path(run_dir)
        self.records = load_actions(self.run_dir / "actions.jsonl")

    def propose(self, state, ctx, budget) -> list:
        n = state.step
        if n >= len(self.records):
            raise ReplayEnd(f"the recording ends before step {n}")
        rec = self.records[n]
        if dict(state.files) != rec["files"]:
            diff = sorted(set(state.files.items()) ^ set(rec["files"].items()))
            raise ReplayDiverged(f"step {n}: the work copy's digests differ from the recording "
                                 f"({', '.join(sorted({p for p, _ in diff}))})")
        if "malformed" in rec:
            raise protocol.Malformed(f"recorded at step {n}: {rec['malformed']}")
        return protocol.parse_proposal({"actions": rec["actions"]}, max_actions=ctx.max_actions)


class MolePolicy:
    """Plants at pre-registered steps, the inner policy elsewhere (module docstring)."""

    def __init__(self, inner, plants, *, label_sink=None):
        if not isinstance(inner, Policy):
            raise TypeError("MolePolicy wraps a policy (an object with propose)")
        self.inner = inner
        self.plants = {}
        for step, plant in dict(plants).items():
            if not isinstance(step, int) or isinstance(step, bool) or step < 0:
                raise TypeError("a plant's step is a non-negative int")
            if not (isinstance(plant, tuple) and len(plant) == 2 and isinstance(plant[0], str)
                    and plant[0]):
                raise TypeError("a plant is (plant_id, actions)")
            self.plants[step] = (plant[0], tuple(_actions(plant[1])))
        if label_sink is not None and not callable(label_sink):
            raise TypeError("label_sink is a function of (step, plant_id)")
        self.label_sink = label_sink
        self.injected = []

    def propose(self, state, ctx, budget) -> list:
        plant = self.plants.get(state.step)
        if plant is None:
            return self.inner.propose(state, ctx, budget)
        pid, acts = plant
        self.injected.append((state.step, pid))
        if self.label_sink is not None:
            self.label_sink(state.step, pid)
        return list(acts)
