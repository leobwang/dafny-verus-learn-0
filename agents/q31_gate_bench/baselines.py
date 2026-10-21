"""Q31 — Gate & bench: the two baselines (Challenge, solo; Python)

Solo work (guard rule 2s). A scripted policy (for the harness's own tests: it replays
recorded edits, calls no model) and a one-shot renderer for fvh.backends.ModelPolicy on
the Qwen transport, the engine of record for every challenge run (the user's D66).
Interface frozen (Q31_Statement.toml); bodies yours.
"""

from collections.abc import Sequence

from fvh import policies, protocol

__all__ = ["one_shot_render", "scripted"]


# item: Q31.H14py S9
def scripted(edits: Sequence[protocol.Edit]) -> policies.ScriptedPolicy:
    """**H14py.** A ScriptedPolicy that applies `edits` at step 0, verifies at step 1
    and stops at step 2 ("done" when the last verification passed, else "give-up")."""
    raise NotImplementedError("Q31.H14py")


# item: Q31.H15py S9
def one_shot_render(state: protocol.State, ctx: protocol.Context, budget: protocol.Budget) -> str:
    """**H15py.** The one-shot prompt: the task statement, the editable file's text
    and the reply rule (one JSON object holding the whole-file Edit); no feedback, so a
    run is one call."""
    raise NotImplementedError("Q31.H15py")
