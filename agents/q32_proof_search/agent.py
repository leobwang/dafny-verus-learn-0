"""Q32 — Proof-search agent (Challenge, solo; Python)

Solo work (guard rule 2s). A policy on the frozen protocol
(propose(state, ctx, budget) -> [Action]; it never acts). Its acceptance tool is your
Q31 gate (fvh.batch's gated arm: gate = "agents/q31_gate_bench/gate.py"). Interface
frozen (Q32_Statement.toml); bodies yours. Imports: the standard library, fvh, fvh_q,
q31_gate_bench and this package.

The retrieval index is built only from INDEX_SOURCES and pinned by sha256 at the
freeze (expected/Q32.statements); the grader's attestation scan voids a run whose
index holds a span of a sealed task or of a held-out public task's answer.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from fvh import protocol

__all__ = ["EDIT_KINDS", "INDEX_SOURCES", "Agent", "Index", "TypedEdit", "build_index",
           "compile_edit", "dedup_key", "value"]

EDIT_KINDS = ("invariant", "assert", "lemma-call", "decreases", "trigger", "proof-block")
INDEX_SOURCES = ("dafny/given/Q/", "verus/given/", "bench/local/q/agentic/q32-dev/")


@dataclass(frozen=True)
class TypedEdit:
    """kind (one of EDIT_KINDS), the file, an anchor (a line of the work copy the edit
    attaches after, quoted exactly), and the text it inserts."""

    kind: str
    path: str
    anchor: str
    text: str


@dataclass(frozen=True)
class Index:
    """The retrieval index: entries (name, signature, source path) and its sha256."""

    entries: tuple
    sha256: str


# item: Q32.H1py S9
def compile_edit(edit: TypedEdit, file_text: str) -> protocol.Edit:
    """**H1py.** The fvh Edit that applies a typed edit (the anchor must occur
    exactly once; a malformed edit raises ValueError)."""
    raise NotImplementedError("Q32.H1py")


# item: Q32.H2py S9
def dedup_key(state: protocol.State) -> str:
    """**H2py.** The search state's identity: the work copy's file hashes and the
    normalized set of failing obligations of its last verification."""
    raise NotImplementedError("Q32.H2py")


# item: Q32.H3py S9
def value(state: protocol.State) -> float:
    """**H3py.** The heuristic value of a state (higher is closer to verified)."""
    raise NotImplementedError("Q32.H3py")


# item: Q32.H4py S9
def build_index(root, sources: Sequence[str] = INDEX_SOURCES) -> Index:
    """**H4py.** The index over `sources` only (a path outside them is refused)."""
    raise NotImplementedError("Q32.H4py")


class Agent:
    """The search (holes H5py and H6py). The search: a frontier over states keyed by
    dedup_key, ranked by value, expanded by model-proposed typed edits, scheduled
    within the per-task budget B; every candidate goes through the gate."""

    # item: Q32.H5py S9
    def __init__(self, ask, seed: int, *, index: Index | None = None):
        raise NotImplementedError("Q32.H5py")

    # item: Q32.H6py S9
    def propose(self, state, ctx, budget) -> list:
        raise NotImplementedError("Q32.H6py")
