#!/usr/bin/env python3
"""named_call_gate.py — the static half of the named-call gate (the user's D90).

A library-call hole is judged by the named-call gate instead of the three-fact
bar of D64: its proof is a short sequence of named library calls, and

  1. the empty body fails (the empty-body gate, scripts/firsttry.sh --empty-body);
  2. removing any one call fails;
  3. every call keeps its found-by note (`// found-by: ide|grep|docs|source|llm|memory`).

An item opts in with a `// gate: named-calls` line in its block, in the learner
file and in its reference twin. This script checks, from the twin alone, that the
gate is recorded mechanically: every call statement of the item's hole regions
carries a found-by note, and the twin block holds one `// cfree: { … }` answer per
call, equal to the hole body with exactly that call removed. The empty-body gate
then runs every `cfree:` answer in place of the body and requires it to fail
(firsttry's forms gate), which is check 2; check 1 is the empty-body gate itself.

It never runs a verifier and never prints reference text: problems name the item
and the file only. Usage: scripts/named_call_gate.py [--root DIR] [MODULE ...]
(default: every module whose twins carry a `gate: named-calls` item). Exit 0
when every gated item is recorded, 1 otherwise. Author-only (it reads twins).
"""

import argparse
import re
import sys
from pathlib import Path

GATE_LINE = re.compile(r"^\s*//\s*gate:\s*named-calls\s*$")
ITEM_LINE = re.compile(r"^\s*//\s*item:\s*([QR]\d\d\.[A-Z]\d+[a-z]*)\b")
HOLE_BEGIN = re.compile(r"^\s*//\s*@hole-begin\s+(\S+)\s*$")
HOLE_END = re.compile(r"^\s*//\s*@hole-end\s+(\S+)\s*$")
CFREE = re.compile(r"^\s*//\s*cfree:\s?(.*)$")
FOUND_BY = re.compile(r"//\s*found-by:\s*(ide|grep|docs|source|llm|memory)\b")
# A call statement: a qualified or method call, or a `broadcast use`, ending in `;`.
CALL = re.compile(r"^\s*(broadcast\s+use\s+[\w:]+\s*;|[\w.@]+\s*\(.*\)\s*;)\s*(//.*)?$")
TWIN_GLOBS = ("Solutions/dafny/**/*.dfy", "Solutions/verus/**/*.rs")


def norm(s):
    """Whitespace-insensitive form of a body, comments dropped."""
    s = re.sub(r"//[^\n]*", "", s)
    return re.sub(r"\s+", "", s)


def items(lines):
    """[(item id, first line, last line)] of the blocks of a file (1-based)."""
    starts = [(i + 1, m.group(1)) for i, l in enumerate(lines) if (m := ITEM_LINE.match(l))]
    out = []
    for k, (ln, iid) in enumerate(starts):
        end = starts[k + 1][0] - 1 if k + 1 < len(starts) else len(lines)
        out.append((iid, ln, end))
    return out


def check_item(lines, iid, lo, hi):
    """Problems of one gated item's block (lines lo..hi, 1-based)."""
    probs = []
    block = lines[lo - 1:hi]
    regions, cur = [], None
    for l in block:
        if (m := HOLE_BEGIN.match(l)) and m.group(1) == iid:
            cur = []
            continue
        if (m := HOLE_END.match(l)) and m.group(1) == iid:
            regions.append(cur or [])
            cur = None
            continue
        if cur is not None:
            cur.append(l)
    if not regions:
        return [f"{iid}: gated, but its twin block holds no `@hole-begin {iid}` region"]
    body = [l for r in regions for l in r]
    calls = [k for k, l in enumerate(body) if CALL.match(l)]
    if not calls:
        probs.append(f"{iid}: gated, but its hole regions hold no named call")
    for k in calls:
        if not FOUND_BY.search(body[k]):
            probs.append(f"{iid}: a named call of its hole has no `// found-by:` note")
    answers = {norm(m.group(1)) for l in block if (m := CFREE.match(l))}
    for k in calls:
        want = "{" + norm("\n".join(l for j, l in enumerate(body) if j != k)) + "}"
        if want not in answers:
            probs.append(f"{iid}: no `cfree:` answer removes exactly its call number "
                         f"{calls.index(k) + 1} of {len(calls)}")
    return probs


def check_file(path, rel, only=None):
    """(gated item ids, problems) of one twin file."""
    lines = path.read_text(encoding="utf-8").split("\n")
    gated, probs = [], []
    for iid, lo, hi in items(lines):
        if only and iid.split(".")[0] not in only:
            continue
        if any(GATE_LINE.match(l) for l in lines[lo - 1:hi]):
            gated.append(iid)
            probs += [f"{rel}: {p}" for p in check_item(lines, iid, lo, hi)]
    return gated, probs


def check(root, only=None):
    gated, probs = [], []
    for g in TWIN_GLOBS:
        for p in sorted(root.glob(g)):
            if not p.is_file():
                continue
            gi, pr = check_file(p, p.relative_to(root).as_posix(), only)
            gated += gi
            probs += pr
    return gated, probs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("modules", nargs="*")
    a = ap.parse_args()
    gated, probs = check(Path(a.root), set(a.modules) or None)
    for p in probs:
        print(p)
    print(f"named_call_gate: {len(gated)} gated item(s); {len(probs)} problem(s)")
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
