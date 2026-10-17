"""Q12 — Lab 1: the three Qwen arms and the prompt renderer (Reference Solution)

Hole-free reference for `harness/q/fvh_q/policies.py` (author-only; never
learner-visible). Same names, signatures, docstrings, item markers and order
as the exercise file. Every hole is filled; each H item declares its `# triv:`
body for the Python TRIV mode.

Written on the frozen `fvh.protocol` (DV4 step 1a, built 2026-10-11): Edit(path,
old, new), Verify(mode), Stop(reason, note); State.step, State.last_verify;
Context.target, lang, statement, material; Budget.exhausted, all as
Solutions/plans/Q12-code-notes.md §6 assumed them, so no line of the arms
changed. The acceptance tests now run on the real actions (26 passed, none
skipped), and the arms were also driven through the real fvh.executor with
fvh.backends.candidate_ask as `ask` (Q12-code-notes §11).
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
    if mode not in MODES:
        raise ValueError(f"mode must be one of {', '.join(MODES)}, not {mode!r}")
    if mode != "independent" and (focus is None or not isinstance(focus.verify, dict)):
        raise ValueError(f"mode {mode!r} needs a focus candidate with its gate document")
    parts = [str(ctx.material["instructions"]), "Statement:\n" + str(ctx.statement),
             "Language: " + str(ctx.lang)]
    if mode == "independent":
        parts += ["The file as shipped:", "```\n" + str(ctx.material["text"]) + "\n```"]
    else:
        title = "Your last candidate:" if mode == "repair" else "The candidate to improve:"
        doc = focus.verify
        errors = [d for d in doc.get("diagnostics") or []
                  if isinstance(d, dict) and d.get("severity") == "error"][:20]
        lines = [f"line {d.get('line')}: {d.get('message')}" for d in errors]
        parts += [title, "```\n" + focus.text + "\n```", "The gate's errors:",
                  "\n".join(lines) if lines else "(none)",
                  f"Holes: {len(doc.get('holes') or [])}"]
    return "\n\n".join(parts)
# triv: return str(ctx.material["instructions"])


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
        if state.step == 0:
            if budget.exhausted:
                return stop(None, "budget")
            text = self.ask(render(state, ctx, mode="independent"), self.seed)
            return submit(ctx, ctx.material["text"], text)
        return stop(state.last_verify)
# triv: return stop(state.last_verify)


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
        doc = state.last_verify
        if self.last is not None:
            self.last = Candidate(self.last.text, doc)
        if verified(doc):
            return stop(doc)
        if budget.exhausted or self.calls >= len(self.seeds):
            return stop(doc, "budget")
        seed = self.seeds[self.calls]
        if self.last is None:
            base = ctx.material["text"]
            text = self.ask(render(state, ctx, mode="independent"), seed)
        else:
            base = self.last.text
            text = self.ask(render(state, ctx, mode="repair", focus=self.last), seed)
        self.calls += 1
        self.last = Candidate(text, None)
        return submit(ctx, base, text)
# triv: return stop(state.last_verify)


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
        doc = state.last_verify
        if self.pending is not None:
            self.frontier.append((failing(doc), len(self.frontier),
                                  Candidate(self.pending, doc)))
            self.current, self.pending = self.pending, None
        if verified(doc):
            return stop(doc)
        if budget.exhausted or self.calls >= len(self.seeds):
            return stop(doc, "budget")
        seed = self.seeds[self.calls]
        if self.calls == 0:
            base = ctx.material["text"]
            text = self.ask(render(state, ctx, mode="independent"), seed)
        else:
            _, _, best = min(self.frontier, key=lambda t: (t[0], t[1]))
            base = self.current
            text = self.ask(render(state, ctx, mode="expand", focus=best), seed)
        self.calls += 1
        self.pending = text
        return submit(ctx, base, text)
# triv: return stop(state.last_verify)
