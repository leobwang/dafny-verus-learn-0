"""Q12 — Lab 1: the three Qwen arms and the prompt renderer (Exercises, Python)

This file is written on the frozen core's protocol, `fvh.protocol`
(DV4-PLAN §3.2), and its acceptance tests (harness/tests/q/test_policies.py)
run the arms on the real actions. Lab 1's runs go through the live batch
runner (`python -m fvh run Q12 --plan <plan>`; QPLAN §22.6): each arm of the
plan names one class here, and the runner builds it with the harness's `ask`
and the run's pre-registered seeds (`construct = "sampler"` for
IndependentSampler(ask, seed), `"seeded"` for SequentialRepair and BestFirst
(ask, seeds); the plan's form is in harness/fvh/batch.py's docstring).

Imports: the Python standard library and the frozen core `fvh`
(harness/fvh/: fvh.protocol), nothing else. A policy holds no tool and
touches no file: it returns actions (pure data) and the executor applies
them to the run's work copy, verifies them in the verification container and
hands back observations (DV4-PLAN §3.2).

How to work this file (Lab 1's policies block, after the pre-registration
has been graded and unlocked: paper/Q12_answers.tex, B1):
1. Replace each hole, in order: H11 (`render`, which every arm uses), then
   H8, H9 and H10. A Python hole is a function whose body, after its
   docstring, is the one statement `raise NotImplementedError("<item id>")`.
2. Run the acceptance tests (harness/tests/q/test_policies.py, frozen; they
   drive each arm with scripted model replies and scripted observations, no
   model and no container): `scripts/vcheck harness/q/fvh_q/policies.py`.
3. Done = `scripts/vcheck --gate harness/q/fvh_q/policies.py` exits 0. Then
   write each arm's prompt hash into the pre-registration's arms field (the
   source of this file enters the hash, DV4-PLAN §3.6): changing this file
   after the pre-registration is graded changes every arm's prompt hash.
4. Stuck for 20 minutes? /tutor Q12.

This file ships with exactly 4 holes: H8, H9, H10 and H11, each counted from
the syntax tree.

Matched compute (design §11.1, QPLAN §22.5): every arm gets the same budget
B of model calls per task. One call of `ask` is one model call. An arm never
calls `ask` twice in one `propose`, and never once the run's budget is
exhausted.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from fvh import protocol

# =============================================================================
# Given (frozen statements: expected/Q12.freeze pins them). Read them, never
# change them.
# =============================================================================

MODES = ("independent", "repair", "expand")

Ask = Callable[[str, int], str]
"""ask(prompt, seed) -> the model's candidate text for the task's target file.

Built by the harness from the lab's pinned transport and generation settings
(fvh.backends; the Ollama gate pins the request options, DV4-PLAN §5.6.3):
one call is one model call, the seed is the request's pre-registered seed,
and the reply has been checked against the action schema and reduced to the
full text of one candidate file. A reply that fails the check ends the run as
`malformed` inside the harness; the policy never sees it."""


@dataclass(frozen=True)
class Candidate:
    """One candidate the arm proposed: its text, and the verifier document
    of its gate run (None until the observation arrives)."""

    text: str
    verify: dict | None


def failing(doc: dict | None) -> int:
    """The number of failing obligations of a verifier document: its error
    diagnostics plus its holes; a document that stopped before verification
    (any `stage` but "verify"), and a missing one, count as the worst
    (10**6). A verified document with no hole counts 0."""
    if not isinstance(doc, dict) or doc.get("stage") != "verify":
        return 10**6
    errors = sum(1 for d in doc.get("diagnostics") or []
                 if isinstance(d, dict) and d.get("severity") == "error")
    holes = len(doc.get("holes") or [])
    return errors + holes


def verified(doc: dict | None) -> bool:
    """A gate document that the lab counts as solved: verdict "verified",
    no hole, a positive count."""
    return (isinstance(doc, dict) and doc.get("verdict") == "verified"
            and not doc.get("holes") and isinstance(doc.get("verified_count"), int)
            and not isinstance(doc.get("verified_count"), bool)
            and doc["verified_count"] >= 1)


def submit(ctx: "protocol.Context", current: str, text: str) -> list:
    """The actions that put `text` in place of the target's `current` text
    and run the gate on it."""
    edit = [protocol.Edit(path=ctx.target, old=current, new=text)] if text != current else []
    return edit + [protocol.Verify(mode="gate")]


def stop(doc: dict | None, note: str = "") -> list:
    """The action that ends the run: "done" after a verified gate run, else
    "give-up"."""
    return [protocol.Stop(reason="done" if verified(doc) else "give-up", note=note)]


# =============================================================================
# Holes
# =============================================================================

# item: Q12.H11py S12
def render(state: "protocol.State", ctx: "protocol.Context", *, mode: str,
           focus: Candidate | None = None) -> str:
    """**H11.** The prompt an arm sends for one model call.

    Every prompt starts with `ctx.material["instructions"]`, then the task's
    statement (`ctx.statement`) and language (`ctx.lang`), then one file
    text in a fenced block:
      "independent"  the task form as shipped (`ctx.material["text"]`);
                     nothing from any earlier call or observation;
      "repair"       the arm's last candidate (`focus`), then the
                     diagnostics of its gate document (`focus.verify`):
                     each error's line and message, at most 20, in the
                     document's order, then the hole count;
      "expand"       as "repair", for the frontier state being expanded
                     (`focus`).
    The same arguments always give the same prompt (no time, no randomness,
    no path outside the task). Raises ValueError for another mode, and for
    "repair" or "expand" without a `focus` that carries a document.
    """
    raise NotImplementedError("Q12.H11py")


# item: Q12.H8py S12
class IndependentSampler:
    """**H8.** The arm "B independent samples" (A1): each run is one
    attempt of one round.

    `propose(state, ctx, budget)`: at step 0, while the budget is not
    exhausted, one call `self.ask(render(state, ctx, mode="independent"),
    self.seed)` and `submit` of its candidate over the task form's text;
    at any later step (the gate's observation is in) `stop` on the last
    verifier document, `state.last_verify`. It never reads an earlier
    observation into a prompt. An exhausted budget at step 0 stops with
    "give-up".
    """

    def __init__(self, ask: Ask, seed: int):
        self.ask = ask
        self.seed = seed

    def propose(self, state, ctx, budget) -> list:
        raise NotImplementedError("Q12.H8py")


# item: Q12.H9py S12
class SequentialRepair:
    """**H9.** The arm "one sample + B - 1 repairs" (A2): one attempt of up
    to B rounds.

    `propose(state, ctx, budget)`: once a gate document of the run is
    verified, `stop`; once the budget is exhausted or the seeds are used
    up, `stop`; otherwise the n-th call (n = 0, 1, …) uses `self.seeds[n]`:
    the first renders "independent" and submits over the task form's text,
    every later one renders "repair" with the last candidate and its
    document as `focus` and submits over the last candidate's text. One
    model call per `propose`.
    """

    def __init__(self, ask: Ask, seeds: Sequence[int]):
        self.ask = ask
        self.seeds = tuple(seeds)
        self.calls = 0
        self.last: Candidate | None = None

    def propose(self, state, ctx, budget) -> list:
        raise NotImplementedError("Q12.H9py")


# item: Q12.H10py S12
class BestFirst:
    """**H10.** The arm "best-first over edit states, ranked by failing
    obligations" (A3): one attempt of up to B expansions.

    The frontier holds every candidate whose gate document has arrived,
    ranked by `failing(doc)` (fewest first; equal ranks: the earlier
    candidate first). `propose(state, ctx, budget)`: record the last
    candidate with `state.last_verify` into the frontier; once a document
    is verified, or the budget or the seeds are used up, `stop`; the first
    call renders "independent" and submits over the task form's text; every
    later call renders "expand" with the best frontier candidate as `focus`
    (it stays in the frontier: a state may be expanded again) and submits
    its child over the text the work copy holds now (the last candidate
    submitted). One model call per `propose`; the n-th call uses
    `self.seeds[n]`.
    """

    def __init__(self, ask: Ask, seeds: Sequence[int]):
        self.ask = ask
        self.seeds = tuple(seeds)
        self.calls = 0
        self.frontier: list[tuple[int, int, Candidate]] = []
        self.pending: str | None = None
        self.current: str | None = None

    def propose(self, state, ctx, budget) -> list:
        raise NotImplementedError("Q12.H10py")
