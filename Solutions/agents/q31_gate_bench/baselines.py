"""Q31 — Gate & bench: the two baselines (the REFERENCE twin; author-only) (Challenge, solo; Python)

Solo work (guard rule 2s). A scripted policy (for the harness's own tests: it replays
recorded edits, calls no model) and a one-shot renderer for fvh.backends.ModelPolicy on
the Qwen transport, the engine of record for every challenge run (the user's D66).
Interface frozen (Q31_Statement.toml); bodies yours.
"""

from collections.abc import Sequence

from fvh import policies, protocol

__all__ = ["REPLY_RULE", "one_shot_render", "scripted"]

REPLY_RULE = ('Reply with one JSON object and nothing else: {"actions": [{"kind": "edit", '
              '"path": <the target>, "old": "", "new": <the whole new file>}]}.')
"""The reply rule every one-shot prompt ends with (given; frozen)."""


# item: Q31.H14py S9
def scripted(edits: Sequence[protocol.Edit]) -> policies.ScriptedPolicy:
    """**H14py.** A ScriptedPolicy of two proposals: step 0 applies `edits` and runs
    Verify(); step 1 stops with Stop("done"). (The scripted baseline exists for the
    harness's own tests; it calls no model.)"""
    return policies.ScriptedPolicy([list(edits) + [protocol.Verify()],
                                    [protocol.Stop(reason="done")]])


# item: Q31.H15py S9
def one_shot_render(state: protocol.State, ctx: protocol.Context, budget: protocol.Budget) -> str:
    """**H15py.** The one-shot prompt, as text: ctx.material["instructions"], then
    "Statement:" and ctx.statement, then the target's shipped text
    (ctx.material["text"]) in a fenced block, then REPLY_RULE. It uses nothing of the
    run's history (a one-shot run is one call), and the same arguments always give the
    same text."""
    return "\n\n".join([str(ctx.material.get("instructions", "")),
                         "Statement:\n" + str(ctx.statement),
                         "```\n" + str(ctx.material.get("text", "")) + "\n```", REPLY_RULE])
