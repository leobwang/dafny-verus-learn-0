"""fvh.labalpha — Lab alpha's policy instrument (R12; DVR4 plan sections 3.3 and 3.8).

The four regimes of Lab alpha are the R12 engine's seeded policies (fvh_r.engine:
R12Independent (10, 1, fifo), R12Repair (1, 10, lifo), R12BestFirst (3, 10, best) on
obligation-localized feedback, R12BestFirstRaw on the raw wrapper document). The lab
runs them through this module's wrappers, which add the analysis plan's two
apparatus rules without touching the engine's search:

  - the equal feedback cap (resource accounting): before a request reaches the
    model, its `feedback` field is measured as its canonical JSON text (sorted keys,
    UTF-8) and capped at FEEDBACK_CAP_TOKENS tokens, counted as
    ceil(bytes / BYTES_PER_TOKEN), the same rule for both formats. A feedback over
    the cap is replaced by its text cut to the cap, head and tail kept with the
    MARKER between them (raw verifier documents are the ones that reach it; the
    truncation rate is reported per arm). fvh.batch's call record logs the
    message's feedback bytes and whether the marker is present.
  - the missing-result rule for policy failures: a reply the hint grammar rejects
    (malformed data) is a failed node that consumes its call and its parent's
    expansion slot (the engine's own accounting, H4py), and the run goes on with
    the next node; the engine still ends the run when its fixed frontier is
    exhausted or the generation budget is spent. The frozen executor would
    otherwise end the run at the first malformed reply.

Everything else (the prompt, the seeds, the verification, the stop rules) is the
engine policy's. The wrappers are imported by name in a plan
(`policy = "fvh.labalpha:BestFirst"`, construct "seeded"); they import fvh_r.engine
by name (ENGINE) when built, so the course's (or, in the learner's run, the
learner's) engine is the one wrapped.

  cap_feedback(feedback, cap_tokens=FEEDBACK_CAP_TOKENS) -> (value, accounting)
  message_accounting(message) -> dict     what fvh.batch logs per call
  Independent, Repair, BestFirst, BestFirstRaw   the wrapped regimes

Frozen (guard rule 2f), standard library only (plus the engine it wraps).
"""

import importlib
import json
import math

__all__ = ["BYTES_PER_TOKEN", "BestFirst", "BestFirstRaw", "FEEDBACK_CAP_TOKENS", "Independent",
           "MARKER", "Repair", "cap_feedback", "message_accounting", "wrap"]

FEEDBACK_CAP_TOKENS = 2048
BYTES_PER_TOKEN = 4
MARKER = "\n...[R12 feedback cap: {elided} bytes elided]...\n"
_MARKER_HEAD = "...[R12 feedback cap: "


def _canonical(feedback) -> str:
    return json.dumps(feedback, ensure_ascii=False, sort_keys=True)


def _cut(data: bytes, n: int, *, tail: bool) -> str:
    """The first (or last) n bytes of UTF-8 data, never splitting a character."""
    part = data[-n:] if tail and n else (data[:n] if not tail else b"")
    return part.decode("utf-8", errors="ignore")


def cap_feedback(feedback, cap_tokens: int = FEEDBACK_CAP_TOKENS):
    """The feedback as sent, and its accounting (module docstring).

    Returns (feedback, accounting) unchanged when its canonical text fits the cap,
    else (text cut to the cap: head + MARKER + tail, a string, accounting).
    accounting = {feedback_bytes, feedback_tokens_est, feedback_cap_tokens,
    feedback_truncated, feedback_bytes_sent}."""
    if isinstance(cap_tokens, bool) or not isinstance(cap_tokens, int) or cap_tokens < 64:
        raise ValueError("cap_tokens is an int >= 64")
    text = _canonical(feedback)
    data = text.encode("utf-8")
    tokens = math.ceil(len(data) / BYTES_PER_TOKEN)
    acc = {"feedback_bytes": len(data), "feedback_tokens_est": tokens,
           "feedback_cap_tokens": cap_tokens, "feedback_truncated": False,
           "feedback_bytes_sent": len(data)}
    if tokens <= cap_tokens:
        return feedback, acc
    budget = cap_tokens * BYTES_PER_TOKEN
    marker = MARKER.format(elided=len(data))           # an upper bound on what is elided
    keep = max(0, budget - len(marker.encode("utf-8")))
    head = _cut(data, keep // 2, tail=False)
    tail = _cut(data, keep - keep // 2, tail=True)
    elided = len(data) - len(head.encode("utf-8")) - len(tail.encode("utf-8"))
    out = head + MARKER.format(elided=elided) + tail
    acc.update(feedback_truncated=True, feedback_bytes_sent=len(out.encode("utf-8")))
    return out, acc


def message_accounting(message: str) -> dict:
    """The per-call accounting fvh.batch logs: the message's bytes and, for a JSON
    request with a `feedback` field, that field's canonical bytes and whether it
    carries the cap's marker (a truncated feedback)."""
    out = {"message_bytes": len(message.encode("utf-8"))}
    try:
        obj = json.loads(message)
    except ValueError:
        return out
    if isinstance(obj, dict) and "feedback" in obj:
        fb = obj["feedback"]
        out["feedback_bytes"] = len(_canonical(fb).encode("utf-8"))
        out["feedback_truncated"] = isinstance(fb, str) and _MARKER_HEAD in fb
    return out


def _capped_ask(ask, cap_tokens):
    def capped(prompt, seed):
        try:
            obj = json.loads(prompt)
        except ValueError:
            return ask(prompt, seed)
        if isinstance(obj, dict) and "feedback" in obj:
            obj["feedback"], _ = cap_feedback(obj["feedback"], cap_tokens)
            prompt = json.dumps(obj, ensure_ascii=False)
        return ask(prompt, seed)
    return capped


def _observed(outcome):
    """The observation of a re-entered step was made before its rejected reply."""
    return None


def wrap(base, *, cap_tokens: int = FEEDBACK_CAP_TOKENS):
    """A Lab alpha regime: the engine policy class `base` with the equal cap and the
    malformed-node rule (module docstring)."""
    from fvh import protocol as P

    class LabAlpha(base):
        feedback_cap_tokens = cap_tokens

        def __init__(self, ask, seeds):
            super().__init__(_capped_ask(ask, cap_tokens), seeds)
            self.failed_nodes = 0

        def step_r12(self, state, ctx, budget):
            """The engine policy's step; after a rejected reply, the same step again
            with the observation already made (the next node is staged from the same
            verified state, with the engine's own prompt and the next seed)."""
            again = False
            while True:
                if again:
                    self.engine.observe = _observed    # re-enter without a second observe
                try:
                    return super().step_r12(state, ctx, budget)
                except P.Malformed:
                    eng = self.engine
                    if eng is None or eng.pending is not None or not eng.attempts \
                            or eng.attempts[-1].status != "malformed":
                        raise                              # not a rejected reply: end the run
                    self.failed_nodes += 1
                    again = True
                finally:
                    if self.engine is not None and "observe" in vars(self.engine):
                        del self.engine.observe

    LabAlpha.__name__ = LabAlpha.__qualname__ = "LabAlpha" + base.__name__
    return LabAlpha


ENGINE = "fvh_r.engine"     # imported by name when a regime is built, as fvh.batch imports a
                            # plan's policy: the core never imports a learner package itself


def _regime(name):
    def build(ask, seeds):
        engine = importlib.import_module(ENGINE)
        return wrap(getattr(engine, name))(ask, seeds)
    build.__name__ = name
    return build


Independent = _regime("R12Independent")
Repair = _regime("R12Repair")
BestFirst = _regime("R12BestFirst")
BestFirstRaw = _regime("R12BestFirstRaw")
