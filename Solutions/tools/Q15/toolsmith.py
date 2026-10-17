"""CONTRACT
goal: build the automation this file's docstring and INTERFACE block specify for the twelve goals of tools/Q15/battery/ (each in its Dafny and its Verus form): a command-line tool that, for one goal file, finds the quantified step of the goal's last declaration, tries trigger choices for it, and writes a repaired copy that the done gate passes, changing triggers only
allowed-files:
  - tools/Q15/toolsmith.py
acceptance:
  - re-run the tool on a goal you changed and `scripts/vcheck --gate` its output after every edit of the tool; never stack unverified edits
  - for every goal file of tools/Q15/battery/battery.toml, the tool's output file passes `scripts/vcheck --gate` and `scripts/specfreeze --against` the shipped goal file reports no change
  - the tool never writes a statement line (signature, requires, ensures, decreases) and never edits a shipped battery file: it writes new files only, under the output directory it is given
  - the tool adds or changes trigger annotations only (Dafny `{:trigger …}`; Verus `#[trigger]`, `#![trigger …]`), and runs the verifier only through `scripts/vcheck`, one job at a time
  - the standard library only
"""
# Q15 — the toolsmith (rung 12; `/contract Q15`; QPLAN §25.3, §25.4)
#
# This file is the contract's only allowed file. It ships with no code: the
# contractor writes all of it, to the interface you write below.
#
# Before the run (you, about 8 minutes):
#   1. Write the INTERFACE block below: the command line (a goal file in, an
#      output directory; or the battery file and a directory), what the tool
#      prints per goal (the trigger it chose, the runs it made and their
#      verdicts), which trigger candidates it tries and in which order (for
#      example, each subterm of the step's body that mentions every bound
#      variable and holds no arithmetic at its top), how many runs it may
#      spend per goal, what it does with a goal that passes as shipped, and
#      its exit codes.
#   2. Commit it, then run `/contract Q15` on this file in a fresh session.
#
# After the run (you, about 12 minutes): review the tool's source (does it
# touch anything but a trigger? does it ever write over a battery file? does
# it judge a run from vcheck's output only?), then audit every one of the
# twelve goals in both languages: run the tool, `scripts/vcheck --gate` its
# output, and `scripts/specfreeze --against` the shipped goal; fill the AUDIT
# block at the end, one row per goal file.

# INTERFACE (the reference's own; a learner's may differ: DV6 fix round, spec §12.1's twin rule)
#   command line: `python3 tools/Q15/toolsmith.py GOAL OUTDIR` (one goal file, .dfy or .rs),
#     or `python3 tools/Q15/toolsmith.py --battery tools/Q15/battery/battery.toml OUTDIR`
#     (every goal of the battery, both languages); OUTDIR must not be under tools/Q15/battery/
#   output: OUTDIR/<lang>/<goal file name>, the goal with its quantified step's trigger as
#     chosen; one line per run on standard output (`<goal> run <n>: <trigger> -> <verdict>`)
#     and one closing line per goal (`<goal>: chosen <trigger> after <n> run(s)` or
#     `<goal>: no trigger passed in <n> run(s)`)
#   trigger candidates, and their order: the step as shipped first; then each term of the
#     step's range and body (a call, an index or slice, a method call, or a call's argument
#     that is no bare variable) that mentions every bound variable, alone, in the order the
#     terms appear; then each pair of terms that together mention every bound variable;
#     duplicates dropped
#   runs per goal: at most MAX_RUNS (16), one `scripts/vcheck --gate --json` each, one job at
#     a time; a run is passed only when vcheck's own document says "verified" with no hole
#   a goal that passes as shipped: its copy is written unchanged, after one run
#   exit codes: 0 every goal passed; 1 some goal found no trigger; 2 usage or an unreadable
#     goal; the tool never writes under tools/Q15/battery/

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = next((d for d in Path(__file__).resolve().parents
             if (d / "scripts" / "vcheck").is_file() and (d / "MODULES.toml").is_file()),
            Path(__file__).resolve().parents[2])   # the course root, wherever the file sits
VCHECK = ROOT / "scripts" / "vcheck"
MAX_RUNS = 16
TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*!?|\d+|\.\.|::|==>|<==>|&&|\|\||[<>=!]=|\S")
KEYWORDS = {"forall", "exists", "ensures", "requires", "implies", "by", "assert", "if", "then",
            "else", "nat", "int", "seq", "true", "false", "old"}


class Unreadable(Exception):
    pass


def close_of(text, i):
    """The index of the bracket closing the one at text[i]."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    o, c, d = text[i], pairs[text[i]], 0
    for j in range(i, len(text)):
        if text[j] == o:
            d += 1
        elif text[j] == c:
            d -= 1
            if d == 0:
                return j
    raise Unreadable("an unbalanced bracket")


def depth0_find(text, start, words):
    """The first index >= start at bracket depth 0 where one of `words` starts (as a word)."""
    d = 0
    i = start
    while i < len(text):
        ch = text[i]
        if d == 0:
            for w in words:
                if text.startswith(w, i) and (not w[0].isalpha() or (
                        (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_"))
                        and (i + len(w) >= len(text) or not (text[i + len(w)].isalnum()
                                                             or text[i + len(w)] == "_")))):
                    return i, w
        if ch in "([{":
            d += 1
        elif ch in ")]}":
            d -= 1
        i += 1
    return -1, None


# --- the quantified step ----------------------------------------------------------------------

class Step:
    """The quantified step of a goal's last declaration: its bound variables, the span of
    its trigger annotations and the span of its range and body (character offsets)."""

    def __init__(self, lang, text):
        self.lang, self.text = lang, text
        if lang == "dafny":
            last = max(m.start() for m in re.finditer(r"(?m)^\s*lemma\s", text))
            sig = re.compile(r"\blemma\b").search(text, last).end()
            body_at, _ = depth0_find(text, sig, ["{\n", "{ ", "{\r"])    # the body's brace
            if body_at < 0:
                raise Unreadable("the last lemma has no body")
            m = re.compile(r"\bforall\b").search(text, body_at)
            if m is None:
                raise Unreadable("no forall statement in the last lemma")
            self.q = m.start()
            i = m.end()
            j, w = depth0_find(text, i, ["{:", "|", "ensures"])
            if j < 0:
                raise Unreadable("a forall statement without ensures")
            self.vars_text = text[i:j]
            at = j
            while at > i and text[at - 1] == " ":
                at -= 1
            self.attr_at = at
            k = j
            while text.startswith("{:", k):            # existing attributes
                k = close_of(text, k) + 1
                while text[k] == " ":
                    k += 1
            self.attr_end = k
            b, _ = depth0_find(text, k, ["{\n", "{ ", "{\r"])     # the step's block
            if b < 0:
                raise Unreadable("a forall statement without its block")
            self.body = (k, b)
        else:
            last = max(m.start() for m in re.finditer(r"(?m)^\s*(pub\s+)?proof\s+fn\s", text))
            m = re.compile(r"\bassert\s+forall\s*\|").search(text, last)
            if m is None:
                raise Unreadable("no `assert forall` in the last proof fn")
            self.q = m.start()
            bar2 = text.index("|", m.end())
            self.vars_text = text[m.end():bar2]
            k = bar2 + 1
            while text[k] == " ":
                k += 1
            self.attr_at = k
            if text.startswith("#![", k):
                k = close_of(text, k + 2) + 1
                while text[k] == " ":
                    k += 1
            self.attr_end = k
            b, _ = depth0_find(text, k, ["by"])
            if b < 0:
                raise Unreadable("an `assert forall` without `by`")
            self.body = (k, b)
        self.vars = [v.split(":")[0].strip() for v in split0(self.vars_text) if v.strip()]
        if not self.vars:
            raise Unreadable("no bound variable")

    def body_text(self):
        a, b = self.body
        return self.text[a:b]


def split0(s):
    out, d, cur = [], 0, ""
    for ch in s:
        if ch in "([{<":
            d += 1
        elif ch in ")]}>":
            d -= 1
        if ch == "," and d == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


def words(s):
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", s))


def terms(body, bound):
    """The candidate terms of a step's body, in order: calls, indexings and slices, method
    calls, and call arguments that are no bare variable; each mentions a bound variable."""
    body = body.replace("#[trigger] ", "")
    out = []

    def add(t):
        t = t.strip()
        if t and t not in out and words(t) & set(bound) and t not in bound:
            out.append(t)
    i = 0
    n = len(body)
    while i < n:
        m = re.compile(r"[A-Za-z_][A-Za-z0-9_]*!?|\(|\[").match(body, i)
        if not m:
            i += 1
            continue
        if m.group(0) in KEYWORDS or (i > 0 and (body[i - 1].isalnum() or body[i - 1] in "_.")):
            i = m.end()
            continue
        start, j = i, m.end()
        if m.group(0) in ("(", "["):
            j = close_of(body, i) + 1
        chain_end = None
        while j < n and body[j] in "([." :
            if body[j] in "([":
                e = close_of(body, j)
                # an argument or an index is a term only when it holds a call, an
                # index or a sequence display (arithmetic over a variable is no trigger)
                for arg in (split0(body[j + 1:e]) if body[j] == "(" else [body[j + 1:e]]):
                    if re.search(r"[(\[]", arg):
                        add(arg)
                j = e + 1
                chain_end = j
                add(body[start:j])
            elif body[j] == "." and j + 1 < n and body[j + 1] != ".":
                mm = re.compile(r"\.[A-Za-z_][A-Za-z0-9_]*").match(body, j)
                if not mm:
                    break
                j = mm.end()
                if j < n and body[j] == "(":
                    continue
                chain_end = j
                add(body[start:j])
            else:
                break
        if body[start] in "([" and chain_end is None:
            inner = body[start + 1:close_of(body, start)]
            if body[start] == "(":
                add(body[start:close_of(body, start) + 1])
            i = start + 1
            continue
        i = (start + len(m.group(0))) if chain_end is None else start + len(m.group(0))
    return out


def candidates(step):
    ts = terms(step.body_text(), step.vars)
    allv = set(step.vars)
    singles = [(t,) for t in ts if allv <= words(t)]
    pairs = [(a, b) for x, a in enumerate(ts) for b in ts[x + 1:]
             if allv <= (words(a) | words(b)) and not (allv <= words(a) or allv <= words(b))]
    return [None] + singles + pairs


def with_trigger(step, trig):
    """The goal's text with the step's trigger annotations replaced by `trig` (a tuple of
    terms; None: as shipped)."""
    if trig is None:
        return step.text
    t, (a, b) = step.text, step.body
    if step.lang == "dafny":
        return (t[:step.attr_at] + " {:trigger " + ", ".join(trig) + "} "
                + t[step.attr_end:])
    body = t[a:b].replace("#[trigger] ", "")
    for term in trig:
        k = body.find(term)
        if k < 0:
            raise Unreadable("a candidate term is not in the body")
        mark = "#[trigger] " + (term if re.fullmatch(r"[\w!]+(\(.*\)|\[.*\])+|\(.*\)|[\w.]+\(.*\)",
                                                     term) else f"({term})")
        body = body[:k] + mark + body[k + len(term):]
    return t[:step.attr_at] + body + t[b:]


def show(trig):
    return "as shipped" if trig is None else " + ".join(trig)


def gate(path):
    """True when scripts/vcheck --gate --json says verified with no hole (its document only)."""
    p = subprocess.run([str(VCHECK), "--gate", "--json", str(path)], capture_output=True,
                       text=True, cwd=str(ROOT))
    try:
        doc = json.loads(p.stdout)
    except ValueError:
        return False, f"no document (exit {p.returncode})"
    ok = doc.get("verdict") == "verified" and doc.get("holes") == [] and p.returncode == 0
    return ok, str(doc.get("verdict"))


def run_goal(goal, outdir, say=print):
    goal = Path(goal)
    lang = "dafny" if goal.suffix == ".dfy" else "verus" if goal.suffix == ".rs" else None
    if lang is None:
        raise Unreadable(f"{goal}: not a .dfy or .rs goal")
    step = Step(lang, goal.read_text(encoding="utf-8"))
    out = Path(outdir) / lang / goal.name
    out.parent.mkdir(parents=True, exist_ok=True)
    runs = 0
    for trig in candidates(step)[:MAX_RUNS]:
        try:
            text = with_trigger(step, trig)
        except Unreadable:
            continue
        out.write_text(text, encoding="utf-8")
        runs += 1
        ok, verdict = gate(out)
        say(f"{goal} run {runs}: {show(trig)} -> {verdict}")
        if ok:
            say(f"{goal}: chosen {show(trig)} after {runs} run(s)")
            return True
    out.write_text(step.text, encoding="utf-8")
    say(f"{goal}: no trigger passed in {runs} run(s)")
    return False


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 3 and argv[0] == "--battery":
        bat = Path(argv[1])
        try:
            data = tomllib.loads(bat.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            print(f"toolsmith: {bat} cannot be read", file=sys.stderr)
            return 2
        goals = [ROOT / g[k] for g in data.get("goal", []) for k in ("dafny", "verus") if g.get(k)]
        outdir = Path(argv[2])
    elif len(argv) == 2 and not argv[0].startswith("-"):
        goals, outdir = [Path(argv[0])], Path(argv[1])
    else:
        print("usage: toolsmith.py GOAL OUTDIR | --battery BATTERY.toml OUTDIR", file=sys.stderr)
        return 2
    shipped = (ROOT / "tools" / "Q15" / "battery").resolve()
    if outdir.resolve() == shipped or shipped in outdir.resolve().parents:
        print("toolsmith: the output directory may not be under tools/Q15/battery/", file=sys.stderr)
        return 2
    ok = True
    for g in goals:
        try:
            ok = run_goal(g, outdir) and ok
        except (Unreadable, OSError) as e:
            print(f"toolsmith: {g}: {e}", file=sys.stderr)
            return 2
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
