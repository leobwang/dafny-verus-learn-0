#!/usr/bin/env python3
"""pcount.py — the proof-line counter of QPLAN §19.0 (Δ53, Δ173), author tool.

A reference's size is its proof text: the non-blank, non-comment lines of
proof blocks, assertions, loop invariants and `decreases` clauses, ghost and
tracked declarations and updates, lemma calls and the bodies of proof
functions and lemmas, plus the statements of every lemma or exec helper the
learner must invent. Exec code is not counted. This file is the counter the
Q10-Q18 author notes (Appendix C.8, `rev/pcount.py`) used for every probed
item, moved into the course with the layout rule of the user's decision D1
(2026-10-12, DELTAS):

  **The layout rule.** A proof block that holds one statement counts as one
  proof line, however it is laid out: Verus `proof { … }` and an
  `assert(…) by { … }` / Dafny `assert … by { … }` block whose braces hold
  exactly one statement count as the one line the opener, the statement and
  the closing brace make when written on one line. (Before D1 the counter
  counted such a block over three lines as two: the opener and the
  statement; Q13.H1v's two blocks were the case.)

One counter fix rides with it: a proof block opened and closed on one line no
longer leaves the counter "inside a proof block", which tagged a later nested
exec line P (`--no-layout-rule` gives the counter as C.8 had it, for the
record).

Four more (DV5d), which the Q14 and Q17 notes had corrected by hand:
  - a Dafny `ghost predicate` or `ghost function` counts its body as proof, as
    a lemma's;
  - a ghost update is proof: in Dafny an assignment to a `ghost var` (a field
    the file declares as `ghost var <name>: <type>`, or a local ghost of the
    counted body), in Verus an assignment whose value is `Ghost(…)` or
    `Tracked(…)` (`self.len = Ghost(…);`), never a `let` destructuring;
  - a Dafny call statement `Name(…);` is a lemma call (proof) unless the file
    declares `Name` as a method or constructor and not as a lemma: an exec
    helper's call is code;
  - an assertion's continuation lines, until its statement ends (a line that
    ends with `;`, `{` or `}`), are proof like its first line.

Two layout fixes (DV5e review): attributes may sit between the keyword and
the name (`lemma {:induction false} F` is found), and block comments
(`/* … */`, nested, across lines) and the contents of string and character
literals are blanked before counting, so a comment line is never a proof line
and a brace inside one never moves the body scan. No Q10-Q18 twin's count of
a declaration the earlier counter found changed (archive dv5e/reviewfix/).

A heuristic tagger, as before: each body line is P (proof) or C (code);
`--show` prints the tags, which the author reads for every exec item. Lemma
and proof-fn bodies count as proof throughout. `--stmt` counts a
declaration's statement lines (signature to the body's brace), the figure an
invented lemma or helper adds. Static: no verifier runs; the file is only
read.

Usage:
  scripts/pcount.py [--show] [--no-layout-rule] <file>:<name>[@<n>] ...
  scripts/pcount.py --stmt <file>:<name>[@<n>] ...
    <name>@<n> takes the n-th declaration of that name in the file; the name
    `constructor` takes a Dafny class's constructor.
Exit: 0, or 2 on a usage error or a name not found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PSTART = re.compile(r"^(assert|assume|invariant|decreases|reveal|reveal_with_fuel|calc|"
                    r"broadcast use|let\s+ghost|let\s+tracked|ghost\s+var|lemma_\w+|forall\b|"
                    r"Ghost\(|Tracked\()")
CLAUSE_CONT = re.compile(r"^(invariant|decreases|ensures|requires)\b")
DECL_START = re.compile(r"^\s*(pub |proof |fn |lemma |method |function |ghost |predicate )")
# A proof block's opener (D1): `proof {`, or an assertion's `by {` (Verus `assert(…) by {`,
# Dafny `assert … by {`; not `by (nonlinear_arith)` and not a `by method` body).
BLOCK_OPENER = re.compile(r"(^proof\s*\{$|\bby\s*\{$)")


def strip_comments(src):
    """The source lines with every block comment (`/* … */`, nested, across
    lines) and the contents of string and character literals blanked, the line
    count kept: a comment line is then blank (never counted) and a brace inside
    a comment or a literal never moves the body scan (DV5e review fix). Line
    comments are left for the callers' own `//.*` strip."""
    text = "\n".join(src)
    out, k, n, depth = [], 0, len(text), 0
    while k < n:
        ch = text[k]
        two = text[k:k + 2]
        if depth:
            if two == "/*":
                depth, k = depth + 1, k + 2
                out.append("  ")
            elif two == "*/":
                depth, k = depth - 1, k + 2
                out.append("  ")
            else:
                out.append("\n" if ch == "\n" else " ")
                k += 1
            continue
        if two == "/*":
            depth, k = 1, k + 2
            out.append("  ")
            continue
        if two == "//":
            e = text.find("\n", k)
            e = n if e < 0 else e
            out.append(text[k:e])
            k = e
            continue
        if ch == '"':
            e = k + 1
            while e < n and text[e] != '"' and text[e] != "\n":
                e += 2 if text[e] == "\\" else 1
            out.append('"' + " " * (min(e, n) - k - 1) + ('"' if e < n and text[e] == '"' else ""))
            k = e + 1 if e < n and text[e] == '"' else e
            continue
        if ch == "'" and (m := re.match(r"'(\\.|[^\\'\n])'", text[k:])):
            out.append("'" + " " * (len(m.group(0)) - 2) + "'")
            k += len(m.group(0))
            continue
        out.append(ch)
        k += 1
    return "".join(out).split("\n")


def find(src, name):
    """The 0-based line of the declaration `name` (`name@n`: the n-th), or None."""
    nth = 1
    if "@" in name:
        name, n = name.split("@")
        nth = int(n)
    if name == "constructor":        # a Dafny class's constructor (anonymous or named)
        pat = re.compile(r"^\s*constructor\b")
    else:
        # attributes may sit between the keyword and the name (`lemma {:induction false} F`)
        pat = re.compile(r"\b(lemma|method|function|predicate|fn)\s+(?:\{:[^}]*\}\s*)*"
                         + re.escape(name) + r"\b")
    for i, line in enumerate(src):
        if pat.search(line):
            nth -= 1
            if nth == 0:
                return i
    return None


def body(src, i):
    """[(depth at line start, code without comment, opens the body)] from line i
    to the line that closes the body brace."""
    depth, started, out = 0, False, []
    for j in range(i, len(src)):
        code = re.sub(r"//.*", "", src[j])
        opened_here = False
        line_depth = depth
        for ch in code:
            if ch == "{":
                depth += 1
                if not started:
                    started = True
                    opened_here = True
            elif ch == "}":
                depth -= 1
        if started:
            out.append((line_depth, code.strip(), opened_here))
            if depth == 0:
                return out
    return out


def body_start(src, i):
    """The line that opens the body of the declaration at line i (a trailing
    comment on a line does not hide its brace)."""
    src = [re.sub(r"//.*", "", x) for x in src]
    ind = len(src[i]) - len(src[i].lstrip())
    start = i
    if not src[i].rstrip().endswith("{"):
        for j in range(i, min(i + 60, len(src))):
            t = src[j]
            if t.strip() == "{" and len(t) - len(t.lstrip()) == ind:
                return j
            if j > i and DECL_START.match(t) and len(t) - len(t.lstrip()) == ind:
                break
        # the signature spans lines and the body brace ends a clause line
        for j in range(i, min(i + 60, len(src))):
            if src[j].rstrip().endswith("{") and \
                    not re.search(r"(if|else|=>|\|)\s*\{$", src[j].rstrip()):
                return j
    return start


def _statement_ends(text):
    """How many statements `text` (a block's inner code on one line) holds, and
    whether anything follows the last one: top-level `;` end statements, and
    a top-level `}` that is not followed by `else` or `;` ends one."""
    depth, ends, k, n, tail = 0, 0, 0, len(text), False
    while k < n:
        ch = text[k]
        if ch == '"':
            k = text.find('"', k + 1)
            k = n if k < 0 else k + 1
            tail = True
            continue
        if ch in "([{":
            depth += 1
            tail = True
        elif ch in ")]}":
            depth -= 1
            if ch == "}" and depth == 0:
                rest = text[k + 1:].lstrip()
                if not (rest.startswith("else") or rest.startswith(";")):
                    ends += 1
                    tail = False
                    k += 1
                    continue
            tail = True
        elif ch == ";" and depth == 0:
            ends += 1
            tail = False
        elif not ch.isspace():
            tail = True
        k += 1
    return ends, tail


def collapse_blocks(lines):
    """The layout rule (D1): each proof block (BLOCK_OPENER) whose inner code
    is exactly one statement, laid over several lines, joined into the one
    line it would be: (depth, "opener statement }", opens-the-body)."""
    out, k = [], 0
    while k < len(lines):
        d, s, oh = lines[k]
        if not oh and BLOCK_OPENER.search(s):
            m = k + 1
            while m < len(lines) and not (lines[m][0] == d + 1 and lines[m][1].startswith("}")):
                m += 1
            if m < len(lines) and lines[m][1] in ("}", "};", "},"):
                inner = " ".join(x[1] for x in lines[k + 1:m] if x[1])
                ends, tail = _statement_ends(inner)
                if inner and ends == 1 and not tail:
                    out.append((d, f"{s} {inner} {lines[m][1]}", False))
                    k = m + 1
                    continue
        out.append(lines[k])
        k += 1
    return out


GHOST_FIELD = re.compile(r"^\s*ghost\s+var\s+(\w+)\s*:[^=]*$")
GHOST_LOCAL = re.compile(r"\bghost\s+var\s+(\w+)")
VERUS_GHOST_UPDATE = re.compile(r"^[\w.]+(\[[^\]]*\])?\s*=\s*(Ghost|Tracked)\(")
DAFNY_CALL = re.compile(r"^([A-Z]\w*)\(.*\);$")


def ghost_names(src, lines):
    """The Dafny ghost variables an update of which is proof: the fields the
    file declares (`ghost var <name>: <type>`, no initializer) and the
    counted body's own `ghost var` locals."""
    names = {m.group(1) for x in src if (m := GHOST_FIELD.match(re.sub(r"//.*", "", x)))}
    names |= {m.group(1) for _, s, _ in lines for m in GHOST_LOCAL.finditer(s)}
    return names


def exec_methods(src):
    """The names the file declares as a Dafny method or constructor and never
    as a lemma (a call statement to one is code)."""
    meth, lem = set(), set()
    for x in src:
        x = re.sub(r"//.*", "", x)
        for m in re.finditer(r"\b(lemma|method|constructor)\s+(\w+)", x):
            if m.group(1) == "lemma" or re.search(r"\b(ghost|twostate)\s+method\s+"
                                                  + re.escape(m.group(2)) + r"\b", x):
                lem.add(m.group(2))
            else:
                meth.add(m.group(2))
    return meth - lem


def _ghost_update(s, ghosts):
    m = re.match(r"^(this\.)?(\w+)\s*:=", s)
    if m and m.group(2) in ghosts:
        return True
    return bool(VERUS_GHOST_UPDATE.match(s))


def count(src, name, layout_rule=True):
    """(proof lines, code lines, [(tag, line)]) of the declaration `name` in
    the source lines `src`, or None when it is not found."""
    src = strip_comments(src)
    i = find(src, name)
    if i is None:
        return None
    lines = body(src, body_start(src, i))
    if layout_rule:
        lines = collapse_blocks(lines)
    p = c = 0
    in_proof, in_clause, in_assert, rows = 0, False, False, []
    proofmode = bool(re.search(r"\b(proof\s+fn|lemma)\b|\bghost\s+(predicate|function)\b",
                               src[i]))
    ghosts, methods = ghost_names(src, lines), exec_methods(src)
    for d, s, oh in lines:
        if oh:  # the line that opens the body
            s2 = s[s.index("{") + 1:].strip() if "{" in s else ""
            if not s2 or s2 == "}":
                continue
            s = s2
        if not s or s in ("{", "}", "};", "},"):
            if s == "{":
                in_clause = False
            if in_proof and s.startswith("}") and d <= in_proof:
                in_proof = 0
                in_clause = False     # a clause never outlives its proof block
            continue
        tag = "C"
        continues = in_assert            # an assertion's continuation line (DV5d)
        if continues:
            in_assert = not re.search(r"[;{}]$", s)
        if in_proof and d >= in_proof:
            tag = "P"
        elif continues:
            tag = "P"
        elif s.startswith("proof {") or s == "proof{":
            tag = "P"
            # a block closed on its own line leaves the counter outside it
            if not layout_rule or s.count("{") > s.count("}"):
                in_proof = d + 1
        elif PSTART.match(s):
            tag = "P"
        elif (m := DAFNY_CALL.match(s)) and ":=" not in s and m.group(1) not in methods:
            tag = "P"  # a Dafny lemma call statement (an exec method's call is code)
        elif _ghost_update(s, ghosts):
            tag = "P"  # a ghost or tracked update (DV5d)
        if not continues and re.match(r"^(assert|assume)\b", s) and \
                not re.search(r"[;{}]$", s):
            in_assert = True             # the statement goes on below
        if CLAUSE_CONT.match(s):
            in_clause = True
            tag = "P"
        elif in_clause:
            if s.startswith("{"):
                in_clause = False
            elif not re.match(r"^(while|if|let|for|loop|return|match)\b", s):
                tag = "P"
            else:
                in_clause = False
        if s.endswith("{") and in_clause and not CLAUSE_CONT.match(s):
            in_clause = False
        # a statement that ends here ends its clause too (`assert(…) by (…)
        # requires …;` with no brace body): the next line is no continuation
        if in_clause and s.endswith(";") and not s.endswith(",;"):
            in_clause = False
        if in_proof and s.startswith("}") and d < in_proof:
            in_proof = 0
        if proofmode:
            tag = "P"
        rows.append((tag, s))
        if tag == "P":
            p += 1
        else:
            c += 1
    return p, c, rows


def stmt_lines(src, name):
    """The statement lines of the declaration `name` (signature to the body's
    brace), or None when it is not found."""
    src = strip_comments(src)
    i = find(src, name)
    if i is None:
        return None
    n = 0
    for j in range(i, len(src)):
        t = re.sub(r"//.*", "", src[j]).strip()
        if t == "{":
            break
        if t:
            n += 1
        if t.endswith("{") and not re.search(r"(if|else)\b.*\{$", t):
            break
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("specs", nargs="+", metavar="FILE:NAME")
    ap.add_argument("--show", action="store_true", help="print each counted line's tag")
    ap.add_argument("--stmt", action="store_true", help="count statement lines instead")
    ap.add_argument("--no-layout-rule", action="store_true",
                    help="the counter as the author notes' C.8 had it (for the record)")
    a = ap.parse_args(argv)
    bad = 0
    for spec in a.specs:
        if ":" not in spec:
            print(f"pcount: {spec}: expected FILE:NAME", file=sys.stderr)
            return 2
        path, name = spec.rsplit(":", 1)
        try:
            src = Path(path).read_text(encoding="utf-8").split("\n")
        except OSError as e:
            print(f"pcount: {path}: {e}", file=sys.stderr)
            return 2
        if a.stmt:
            n = stmt_lines(src, name)
            if n is None:
                print(f"{name}: not found")
                bad = 1
            else:
                print(f"{name}: statement {n}")
            continue
        got = count(src, name, layout_rule=not a.no_layout_rule)
        if got is None:
            print(f"{name}: not found")
            bad = 1
            continue
        p, c, rows = got
        print(f"{name}: proof {p}, code {c}, total {p + c}")
        if a.show:
            for t, s in rows:
                print(f"   {t} {s}")
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
