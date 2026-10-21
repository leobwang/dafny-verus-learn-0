"""Q32 — Proof-search agent (Challenge, solo; Python)

Solo work (guard rule 2s). A policy on the frozen protocol
(propose(state, ctx, budget) -> [Action]; it never acts), run by fvh.batch as a
"seeded" arm: Agent(ask, seeds), where ask(prompt, seed) returns one whole candidate
file for the task's target (fvh.backends.candidate_ask: one model call). Its
acceptance tool is your Q31 gate (the gated arm: gate = "agents/q31_gate_bench/gate.py").
Interface frozen (Q32_Statement.toml); bodies yours. Imports: the standard library,
fvh, fvh_q, q31_gate_bench and this package.

Typed edits: the agent asks for a candidate that differs from its parent by exactly
ONE typed edit (one of EDIT_KINDS, inserted after one anchor line), and keeps a
candidate only when `typed_diff` recognises it as one; so the search moves by typed
edits although the transport returns whole files.

The retrieval index is built only from INDEX_SOURCES and pinned by sha256 at the
freeze (expected/Q32.statements); the grader's attestation scan voids a run whose
index holds a span of a sealed task or of a held-out public task's answer.

Holes: one per item block (`# item:` markers), each `raise NotImplementedError("<id>")`.
"""

import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass

from fvh import protocol

__all__ = ["EDIT_KINDS", "INDEX_SOURCES", "Agent", "Index", "TypedEdit", "build_index",
           "compile_edit", "dedup_key", "typed_diff", "value"]

EDIT_KINDS = ("invariant", "assert", "lemma-call", "decreases", "trigger", "proof-block")
INDEX_SOURCES = ("dafny/given/Q/", "verus/given/", "bench/local/q/agentic/q32-dev/")
KIND_RULES = {
    "invariant": re.compile(r"^\s*invariant\b"),
    "assert": re.compile(r"^\s*assert\b"),
    "lemma-call": re.compile(r"^\s*[A-Za-z_][\w:.]*\s*\(.*\)\s*;\s*$"),
    "decreases": re.compile(r"^\s*decreases\b"),
    "trigger": re.compile(r"trigger"),
    "proof-block": re.compile(r"^\s*(proof\s*\{|calc\b)"),
}
"""What the first line of each kind's text must match (given; frozen)."""


@dataclass(frozen=True)
class TypedEdit:
    """kind (one of EDIT_KINDS), the file, an anchor (a whole line of the work copy,
    quoted exactly, after which the edit goes), and the text it inserts (one or more
    whole lines)."""

    kind: str
    path: str
    anchor: str
    text: str


@dataclass(frozen=True)
class Index:
    """The retrieval index: entries (name, signature, source path), sorted, and the
    sha256 of their canonical JSON."""

    entries: tuple
    sha256: str


# item: Q32.H1py S9
def compile_edit(edit: TypedEdit, file_text: str) -> protocol.Edit:
    """**H1py.** The fvh Edit that applies a typed edit: old = the anchor line with its
    newline, new = the same followed by the edit's text and a newline. ValueError when
    the kind is unknown, the text's first line does not match KIND_RULES[kind], or the
    anchor is not exactly one whole line of file_text."""
    raise NotImplementedError("Q32.H1py")


# item: Q32.H2py S9
def typed_diff(parent: str, child: str) -> TypedEdit | None:
    """**H2py.** The one typed edit that turns parent into child (child = parent with
    one or more consecutive lines inserted after one existing line, the inserted lines'
    first matching a rule of KIND_RULES, the first kind in EDIT_KINDS order that
    matches), or None when child is not such an edit of parent. The path is ""."""
    raise NotImplementedError("Q32.H2py")


# item: Q32.H3py S9
def dedup_key(state: protocol.State) -> str:
    """**H3py.** The search state's identity: the sha256 of the canonical JSON of the
    work copy's file hashes (state.files) and the sorted set of the last verification's
    error messages with every number removed (so the same failures at moved lines are
    the same state)."""
    raise NotImplementedError("Q32.H3py")


# item: Q32.H4py S9
def value(state: protocol.State) -> float:
    """**H4py.** The heuristic value of a state, in [0, 1]: 1.0 for a verified last
    verification (verdict "verified", no hole), else 1 / (2 + e + h) with e the error
    diagnostics and h the holes of the last verification; 0.0 with none."""
    raise NotImplementedError("Q32.H4py")


# item: Q32.H5py S9
def build_index(root, sources: Sequence[str] = INDEX_SOURCES) -> Index:
    """**H5py.** The index over `sources` (each one of INDEX_SOURCES, else ValueError):
    every .dfy lemma, function, predicate and method and every .rs fn under them, as
    (name, the declaration's first line stripped, repo-relative path), sorted; a
    source that does not exist adds nothing."""
    raise NotImplementedError("Q32.H5py")


class Agent:
    """The search: a best-first frontier of scored candidates, keyed by their text's
    sha256 (a text met twice is expanded once) and ranked by value; each step expands
    the best one with one model call for a one-typed-edit child."""

    # item: Q32.H6py S9
    def __init__(self, ask, seeds: Sequence[int], *, index: Index | None = None):
        """**H6py.** Keep ask, the seeds (the n-th call uses seeds[n]) and the index."""
        raise NotImplementedError("Q32.H6py")

    # item: Q32.H7py S9
    def propose(self, state, ctx, budget) -> list:
        """**H7py.** One step:
          1. the last verification verified: [Stop("done")];
          2. record the candidate just verified (its text and value) in the frontier;
          3. the budget exhausted or no seed left: [Stop("give-up")];
          4. pop the best frontier node (at step 0 the shipped text,
             ctx.material["text"]); ask once with the next seed, the prompt holding
             ctx.material["instructions"], the node's text and its error messages, and
             the signatures of up to five index entries whose names occur in them;
          5. a child that typed_diff accepts and that is new: [Edit(ctx.target, old =
             the work copy's current text, new = child), Verify()]; otherwise go back
             to 3 with the next seed (each ask is one call of the budget the batch
             meters; a step makes at most one call if budget.calls_left is 1)."""
        raise NotImplementedError("Q32.H7py")
