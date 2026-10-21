"""Q32 — Proof-search agent (the REFERENCE twin; author-only) (Challenge, solo; Python)

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


def _verified(doc):
    return isinstance(doc, dict) and doc.get("verdict") == "verified" and not doc.get("holes")


def _score(doc):
    if not isinstance(doc, dict):
        return 0.0
    if _verified(doc):
        return 1.0
    e = sum(1 for d in doc.get("diagnostics") or [] if isinstance(d, dict) and d.get("severity") == "error")
    return 1.0 / (2 + e + len(doc.get("holes") or []))


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
    if edit.kind not in KIND_RULES:
        raise ValueError(f"unknown edit kind {edit.kind!r}")
    first = edit.text.split("\n", 1)[0]
    if not KIND_RULES[edit.kind].search(first):
        raise ValueError(f"a {edit.kind} edit's text starts with {first!r}")
    lines = file_text.split("\n")
    if lines.count(edit.anchor) != 1:
        raise ValueError("the anchor is not exactly one whole line of the file")
    old = edit.anchor + "\n"
    if file_text.count(old) != 1:
        raise ValueError("the anchor line does not end in a newline exactly once")
    return protocol.Edit(path=edit.path, old=old, new=old + edit.text.rstrip("\n") + "\n")


# item: Q32.H2py S9
def typed_diff(parent: str, child: str) -> TypedEdit | None:
    """**H2py.** The one typed edit that turns parent into child (child = parent with
    one or more consecutive lines inserted after one existing line, the inserted lines'
    first matching a rule of KIND_RULES, the first kind in EDIT_KINDS order that
    matches), or None when child is not such an edit of parent. The path is ""."""
    p, c = parent.split("\n"), child.split("\n")
    n = len(c) - len(p)
    if n < 1:
        return None
    i = 0
    while i < len(p) and p[i] == c[i]:
        i += 1
    if i == 0 or c[:i] + c[i + n:] != p:
        return None
    inserted = c[i:i + n]
    for kind in EDIT_KINDS:
        if KIND_RULES[kind].search(inserted[0]):
            return TypedEdit(kind, "", p[i - 1], "\n".join(inserted))
    return None


# item: Q32.H3py S9
def dedup_key(state: protocol.State) -> str:
    """**H3py.** The search state's identity: the sha256 of the canonical JSON of the
    work copy's file hashes (state.files) and the sorted set of the last verification's
    error messages with every number removed (so the same failures at moved lines are
    the same state)."""
    doc = state.last_verify if isinstance(state.last_verify, dict) else {}
    msgs = sorted({re.sub(r"\d+", "", str(d.get("message", "")))
                   for d in doc.get("diagnostics") or []
                   if isinstance(d, dict) and d.get("severity") == "error"})
    blob = json.dumps({"files": dict(sorted(state.files.items())), "errors": msgs},
                      sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# item: Q32.H4py S9
def value(state: protocol.State) -> float:
    """**H4py.** The heuristic value of a state, in [0, 1]: 1.0 for a verified last
    verification (verdict "verified", no hole), else 1 / (2 + e + h) with e the error
    diagnostics and h the holes of the last verification; 0.0 with none."""
    return _score(state.last_verify)


# item: Q32.H5py S9
def build_index(root, sources: Sequence[str] = INDEX_SOURCES) -> Index:
    """**H5py.** The index over `sources` (each one of INDEX_SOURCES, else ValueError):
    every .dfy lemma, function, predicate and method and every .rs fn under them, as
    (name, the declaration's first line stripped, repo-relative path), sorted; a
    source that does not exist adds nothing."""
    from pathlib import Path
    base = Path(root)
    rx_d = re.compile(r"^\s*(?:ghost\s+|static\s+|opaque\s+)*(?:lemma|function|predicate|method)"
                      r"\s+(?:\{[^}]*\}\s*)*([A-Za-z_][\w']*)")
    rx_v = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:(?:open|closed|proof|spec|exec|broadcast)"
                      r"\s+)*fn\s+([A-Za-z_]\w*)")
    entries = []
    for src in sources:
        if src not in INDEX_SOURCES:
            raise ValueError(f"{src!r} is not an index source ({', '.join(INDEX_SOURCES)})")
        d = base / src
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*")):
            if f.suffix not in (".dfy", ".rs") or not f.is_file():
                continue
            rx = rx_d if f.suffix == ".dfy" else rx_v
            rel = f.relative_to(base).as_posix()
            for line in f.read_text(encoding="utf-8").split("\n"):
                m = rx.match(line)
                if m:
                    entries.append((m.group(1), line.strip(), rel))
    entries = tuple(sorted(set(entries)))
    sha = hashlib.sha256(json.dumps(entries, separators=(",", ":")).encode("utf-8")).hexdigest()
    return Index(entries, sha)


class Agent:
    """The search: a best-first frontier of scored candidates, keyed by their text's
    sha256 (a text met twice is expanded once) and ranked by value; each step expands
    the best one with one model call for a one-typed-edit child."""

    # item: Q32.H6py S9
    def __init__(self, ask, seeds: Sequence[int], *, index: Index | None = None):
        """**H6py.** Keep ask, the seeds (the n-th call uses seeds[n]) and the index."""
        self.ask, self.seeds, self.index = ask, list(seeds), index
        self.calls = 0
        self.frontier = []            # (value, order, text, errors)
        self.seen = set()
        self.current = None           # the work copy's text as last submitted
        self.order = 0

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
        doc = state.last_verify
        if _verified(doc):
            return [protocol.Stop(reason="done")]
        if self.current is None:
            self.current = str(ctx.material["text"])
            self._push(self.current, None)
        elif state.history:
            self._push(self.current, doc)
        asked = 0
        limit = budget.calls_left
        while self.frontier:
            if budget.exhausted or self.calls >= len(self.seeds) or \
                    (limit is not None and asked >= limit):
                return [protocol.Stop(reason="give-up")]
            _, _, text, errors = self._best()
            child = self.ask(self._prompt(ctx, text, errors), self.seeds[self.calls])
            self.calls += 1
            asked += 1
            key = hashlib.sha256(child.encode("utf-8")).hexdigest()
            if key in self.seen or typed_diff(text, child) is None:
                self._push_back(text, errors)
                continue
            old, self.current = self.current, child
            return [protocol.Edit(path=ctx.target, old=old, new=child), protocol.Verify()]
        return [protocol.Stop(reason="give-up")]

    def _push(self, text, doc):
        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if key in self.seen:
            return
        self.seen.add(key)
        errors = [str(d.get("message", "")) for d in (doc or {}).get("diagnostics") or []
                  if isinstance(d, dict) and d.get("severity") == "error"]
        self.order += 1
        self.frontier.append((_score(doc) if doc is not None else 0.5, -self.order, text, errors))

    def _push_back(self, text, errors):
        self.order += 1
        self.frontier.append((-1.0, -self.order, text, errors))   # tried: last in line

    def _best(self):
        self.frontier.sort(key=lambda n: (n[0], n[1]))
        return self.frontier.pop()

    def _prompt(self, ctx, text, errors):
        hints = []
        if self.index is not None:
            blob = " ".join(errors)
            hints = [sig for name, sig, _ in self.index.entries if name in blob][:5]
        return "\n\n".join([str(ctx.material.get("instructions", "")),
                             "Insert exactly one typed edit (" + ", ".join(EDIT_KINDS) + ").",
                             "```\n" + text + "\n```", "Errors:\n" + ("\n".join(errors) or "(none)"),
                             "Lemmas you may call:\n" + ("\n".join(hints) or "(none)")])
