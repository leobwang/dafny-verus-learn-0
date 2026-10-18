"""dvl.benchstrip: the content transforms scripts/get_bench.sh applies when it
normalizes a benchmark set (QPLAN §30 Q57; DV4-PLAN §7.1).

A `[[set.layout]]` row of bench/manifest.toml may name one `transform`; the
normalizer passes each file it copies through it and CHANGES records which
transform changed how many files. The transforms:

    verus-drop-main          The course gate refuses code outside `verus!`
                             (catalog row V9, Δ9). HumanEval-Verus and the
                             vericoding Verus files end with a `fn main`
                             outside the macro (empty, or runtime tests), so
                             every top-level `fn main` outside `verus!` is
                             dropped. Nothing else changes.
    verus-strip-proofs       A task form from a complete Verus file (the
                             HumanEval-Verus set ships answers only): the
                             proofs are removed, the specification and the
                             code are kept. Removed: proof fns (a proof fn a
                             kept line still names keeps its signature and an
                             empty body), `broadcast group` items, and in exec
                             code the proof statements (`assert(..)`,
                             `assert forall .. by {..}`, `proof {..}`, the
                             proof macros `calc!`, `assert_seqs_equal!` and
                             the like, `let ghost`/`let tracked`, `reveal`,
                             `reveal_with_fuel`, `hide`, `broadcast use`) and
                             the loop clauses (`invariant`,
                             `invariant_except_break`, `invariant_ensures`,
                             a loop's `ensures`). Kept: a loop's `decreases`
                             (Verus refuses a loop without one before it
                             verifies anything, so a task form without it
                             would not resolve), spec
                             fns, every fn's signature with its requires,
                             ensures, recommends and decreases, the exec code,
                             Rust's runtime `assert!` family, comments outside
                             the removed spans. Also drops `fn main` as
                             verus-drop-main does.
    dafny-axiom-assume-to-hole
                             vericoding's Dafny task forms mark the missing
                             code with `assume {:axiom} false;`, which the
                             course gate does not count (vaudit reports it;
                             `vcheck --gate` and the lab gate's lever check,
                             which allows a lever the task form ships, pass
                             the task form unchanged). Each becomes
                             `assume false;`, a hole the gate counts.
    verus-lab2-form          Lab 2's form (QPLAN §25.6; the second transform
    dafny-lab2-form          beside verus-strip-proofs): the one target
                             declaration's requires and ensures removed, the
                             proofs and the definitions only they use
                             removed, the non-recursive definitions only the
                             specification uses removed and returned (the
                             user's decision D28: they are sealed with the
                             reference), the code, the other definitions and
                             the prose kept, an empty witness added (Verus:
                             kept spec fns made `pub open`, so the grader's
                             public lemmas may name them). See "Lab 2's
                             public task forms" below; scripts/dvl/lab2pub.py
                             applies them to the drawn tasks.

`proof_residue(text)` is an independent token check of a stripped Verus file:
the proof constructs still in it (none for a task form). `spec_residue(text,
lang, name)` is the same for a Lab 2 form: the specification or proof still in
it; `definition_residue(text, lang, kept=())` the definitions a Lab 2 form keeps
that D28 would remove (non-recursive, named by no code and reached by no recursive
definition), less the `kept` ones D37 retains (a Lab2Form's `quantified`, recorded
author-side, never in the form). Standard library only (the Dafny form reads the file
with dvl.dafny).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


class StripError(Exception):
    """A file the transform cannot read (unbalanced delimiters, no verus! block)."""


# --- the Rust lexer ------------------------------------------------------------------------------

@dataclass(frozen=True)
class Tok:
    kind: str      # ident, punct, lit, life
    text: str
    start: int
    end: int


_PUNCT = sorted(["<==>", "==>", "<==", "===", "!==", "&&&", "|||", "..=", "...", "::", "->",
                 "=>", "==", "!=", "<=", ">=", "&&", "||", "..", "+=", "-=", "*=", "/=", "%=",
                 "^=", "&=", "|=", "<<", ">>"], key=len, reverse=True)
_IDENT = re.compile(r"r#[A-Za-z_][A-Za-z0-9_]*|[A-Za-z_][A-Za-z0-9_]*")
_NUM = re.compile(r"\d[0-9A-Za-z_]*(\.\d[0-9_]*)?")
_RAW = re.compile(r'b?r(#*)"')
_CHAR = re.compile(r"'(\\u\{[0-9A-Fa-f]+\}|\\x[0-9A-Fa-f]{2}|\\.|[^\\'\n])'")
_LIFE = re.compile(r"'[A-Za-z_][A-Za-z0-9_]*")


def lex(src):
    """(tokens, comment spans) of Rust source; comments and whitespace dropped."""
    toks, comments = [], []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            comments.append((i, j))
            i = j
            continue
        if src.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if src.startswith("/*", j):
                    depth, j = depth + 1, j + 2
                elif src.startswith("*/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            comments.append((i, j))
            i = j
            continue
        m = _RAW.match(src, i)
        if m:
            close = '"' + m.group(1)
            k = src.find(close, m.end())
            j = n if k < 0 else k + len(close)
            toks.append(Tok("lit", src[i:j], i, j))
            i = j
            continue
        if c == '"' or src.startswith('b"', i):
            j = i + (2 if c == "b" else 1)
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            toks.append(Tok("lit", src[i:j], i, j))
            i = j
            continue
        if c == "'" or src.startswith("b'", i):
            off = 1 if c == "b" else 0
            m = _CHAR.match(src, i + off)
            if m:
                toks.append(Tok("lit", src[i:m.end()], i, m.end()))
                i = m.end()
                continue
            m = _LIFE.match(src, i)
            if m and c == "'":
                toks.append(Tok("life", m.group(0), i, m.end()))
                i = m.end()
                continue
        m = _IDENT.match(src, i)
        if m:
            toks.append(Tok("ident", m.group(0), i, m.end()))
            i = m.end()
            continue
        m = _NUM.match(src, i)
        if m:
            toks.append(Tok("lit", m.group(0), i, m.end()))
            i = m.end()
            continue
        for p in _PUNCT:
            if src.startswith(p, i):
                toks.append(Tok("punct", p, i, i + len(p)))
                i += len(p)
                break
        else:
            toks.append(Tok("punct", c, i, i + 1))
            i += 1
    return toks, comments


_OPEN = {"(": ")", "[": "]", "{": "}"}


def matches(toks):
    """{open index: close index} for (), [] and {}; StripError when unbalanced."""
    stack, out = [], {}
    for k, t in enumerate(toks):
        if t.kind != "punct":
            continue
        if t.text in _OPEN:
            stack.append(k)
        elif t.text in (")", "]", "}"):
            if not stack or _OPEN[toks[stack[-1]].text] != t.text:
                raise StripError(f"unbalanced {t.text!r} at offset {t.start}")
            out[stack.pop()] = k
    if stack:
        raise StripError(f"unclosed {toks[stack[-1]].text!r} at offset {toks[stack[-1]].start}")
    return out


def _is(t, kind, text=None):
    return t is not None and t.kind == kind and (text is None or t.text == text)


def verus_blocks(toks, m):
    """[(open, close)] token indices of each `verus! { … }` body's braces."""
    out = []
    for k in range(len(toks) - 2):
        if _is(toks[k], "ident", "verus") and _is(toks[k + 1], "punct", "!") \
                and _is(toks[k + 2], "punct", "{"):
            out.append((k + 2, m[k + 2]))
    return out


# --- the analysis ---------------------------------------------------------------------------------

_MODIFIERS = {"pub", "crate", "super", "in", "self", "open", "closed", "spec", "proof", "exec",
              "broadcast", "tracked", "const", "unsafe", "async", "extern", "default", "uninterp",
              "axiom"}
_CLAUSES = {"invariant", "invariant_except_break", "invariant_ensures", "ensures", "decreases"}
PROOF_MACROS = {"calc", "assert_seqs_equal", "assert_sets_equal", "assert_maps_equal",
                "assert_by_contradiction", "assert_bitvector_by", "assert_nonlinear_by",
                "assert_bit_vector", "assert_multisets_equal"}
_PROOF_CALLS = {"reveal", "reveal_with_fuel", "hide"}
# a `{` right after one of these opens a block expression, never a body
_EXPR_CONT = {"==>", "<==", "<==>", "===", "!==", "&&", "||", "&&&", "|||", "==", "!=", "<=",
              ">=", "+", "-", "*", "/", "%", "!", "=", "=>", "|", "&", "^", "(", "[", "else",
              "return"}


@dataclass
class Item:
    start: int          # token index of the first modifier
    name: str
    body: int | None    # token index of the body's `{`, or None (a `;` declaration)
    end: int            # token index of the last token


class _Plan:
    def __init__(self, src):
        self.src = src
        self.toks, self.comments = lex(src)
        self.m = matches(self.toks)
        self.blocks = verus_blocks(self.toks, self.m)
        self.spans = []           # (first token, last token, kind)
        self.proof_items = []     # Item
        self.mod_uses = []        # (first, last) module-level `broadcast use`

    def tok(self, k):
        return self.toks[k] if 0 <= k < len(self.toks) else None

    def skip_group(self, k):
        return self.m[k] + 1

    def find_body(self, k, limit):
        """The index of the `{` that opens the body after a signature or a loop
        header starting at k (if/match/else blocks inside the clauses are
        skipped), or of the `;` that ends a declaration; None at the limit."""
        pending = 0
        while k < limit:
            t = self.toks[k]
            if t.kind == "punct" and t.text in ("(", "["):
                k = self.skip_group(k)
                continue
            if t.kind == "ident" and t.text in ("if", "match"):
                pending += 1
            elif t.kind == "punct" and t.text == "{":
                prev = self.tok(k - 1)
                if pending == 0 and not (prev is not None and prev.text in _EXPR_CONT):
                    return k
                if pending == 0:
                    # a block expression inside a clause (`P ==> { … }`, a closure body)
                    k = self.skip_group(k)
                    continue
                pending -= 1
                k = self.skip_group(k)
                if _is(self.tok(k), "ident", "else"):
                    if not _is(self.tok(k + 1), "ident", "if"):
                        pending += 1
                    k += 1
                continue
            elif t.kind == "punct" and t.text == ";" and pending == 0:
                return k
            k += 1
        return None

    def modifiers_start(self, k, floor):
        """The first modifier token before index k (k itself when none)."""
        s = k
        while s - 1 >= floor:
            t = self.toks[s - 1]
            if t.kind == "ident" and t.text in _MODIFIERS:
                s -= 1
            elif _is(t, "punct", ")"):
                o = next((a for a, b in self.m.items() if b == s - 1), None)
                if o is not None and _is(self.tok(o - 1), "ident", "pub"):
                    s = o - 1
                else:
                    break
            else:
                break
        return s

    def stmt_end(self, k, limit, brace_ends):
        """The last token of the statement starting at k."""
        j = k
        while j < limit:
            t = self.toks[j]
            if t.kind == "punct" and t.text in ("(", "["):
                j = self.skip_group(j)
                continue
            if t.kind == "punct" and t.text == "{":
                close = self.m[j]
                if brace_ends:
                    return close + 1 if _is(self.tok(close + 1), "punct", ";") else close
                j = close + 1
                continue
            if t.kind == "punct" and t.text == ";":
                return j
            if t.kind == "punct" and t.text == "}":
                return j - 1
            j += 1
        return limit - 1

    def scan_items(self, a, b):
        k = a
        while k < b:
            t = self.toks[k]
            if _is(t, "ident", "fn") and _is(self.tok(k + 1), "ident"):
                s = self.modifiers_start(k, a)
                mods = {x.text for x in self.toks[s:k]}
                body = self.find_body(k + 2, b)
                if body is None:
                    raise StripError(f"fn {self.toks[k + 1].text}: no body or `;` found")
                is_decl = _is(self.toks[body], "punct", ";")
                end = body if is_decl else self.m[body]
                if "proof" in mods:
                    self.proof_items.append(Item(s, self.toks[k + 1].text,
                                                 None if is_decl else body, end))
                elif "spec" not in mods and not is_decl:
                    self.scan_exec(body + 1, self.m[body])
                k = end + 1
                continue
            if _is(t, "ident", "broadcast") and _is(self.tok(k + 1), "ident", "group"):
                s = self.modifiers_start(k, a)
                body = self.find_body(k + 2, b)
                end = self.m[body] if body is not None and _is(self.toks[body], "punct", "{") \
                    else (body if body is not None else k + 1)
                self.spans.append((s, end, "broadcast-group"))
                k = end + 1
                continue
            if _is(t, "ident", "broadcast") and _is(self.tok(k + 1), "ident", "use"):
                end = self.stmt_end(k, b, False)
                self.mod_uses.append((self.modifiers_start(k, a), end))
                k = end + 1
                continue
            k += 1

    def scan_exec(self, a, b):
        """Proof statements and loop clauses inside an exec body [a, b)."""
        k = a
        while k < b:
            t = self.toks[k]
            prev = self.tok(k - 1)
            at_stmt = k == a or (prev is not None and prev.kind == "punct"
                                 and prev.text in ("{", ";", "}"))
            nxt = self.tok(k + 1)
            if at_stmt and t.kind == "ident":
                kind = None
                brace_ends = True
                if t.text == "assert" and not _is(nxt, "punct", "!"):
                    kind = "assert"
                elif t.text in PROOF_MACROS and _is(nxt, "punct", "!"):
                    kind = "proof-macro"
                elif t.text == "proof" and _is(nxt, "punct", "{"):
                    kind = "proof-block"
                elif t.text == "let" and _is(nxt, "ident") and nxt.text in ("ghost", "tracked"):
                    kind, brace_ends = "ghost-let", False
                elif t.text in _PROOF_CALLS and _is(nxt, "punct", "("):
                    kind, brace_ends = "reveal", False
                elif t.text == "broadcast" and _is(nxt, "ident", "use"):
                    kind, brace_ends = "broadcast-use", False
                if kind:
                    end = self.stmt_end(k, b, brace_ends)
                    self.spans.append((k, end, kind))
                    k = end + 1
                    continue
            if t.kind == "ident" and t.text in ("while", "loop", "for"):
                body = self.loop_body(k, b)
                if body is not None:
                    self.loop_clause_spans(k + 1, body)
                    k = body
                    continue
            if t.kind == "ident" and t.text == "fn" and _is(nxt, "ident"):
                # a nested fn inside an exec body: scan it as an item
                body = self.find_body(k + 2, b)
                if body is not None and _is(self.toks[body], "punct", "{"):
                    self.scan_items(k, self.m[body] + 1)
                    k = self.m[body] + 1
                    continue
            k += 1

    def loop_clause_spans(self, k, body):
        """Spans of a loop header's clauses, except `decreases`: Verus refuses
        a loop without a decreases clause before it verifies anything, so the
        task form keeps the measure and loses the invariants and ensures."""
        c = self.first_clause(k, body)
        if c is None:
            return
        marks = []
        j = c
        while j < body:
            t = self.toks[j]
            if t.kind == "punct" and t.text in ("(", "[", "{"):
                j = self.skip_group(j)
                continue
            if t.kind == "ident" and t.text in _CLAUSES:
                marks.append(j)
            j += 1
        for i, a in enumerate(marks):
            e = (marks[i + 1] if i + 1 < len(marks) else body) - 1
            if self.toks[a].text != "decreases":
                self.spans.append((a, e, "loop-clauses"))

    def first_clause(self, k, limit):
        while k < limit:
            t = self.toks[k]
            if t.kind == "punct" and t.text in ("(", "["):
                k = self.skip_group(k)
                continue
            if t.kind == "ident" and t.text in _CLAUSES:
                return k
            k += 1
        return None

    def loop_body(self, k, limit):
        """The `{` of the loop whose keyword is at k: the first brace at depth 0
        after the header (if/match blocks inside clauses skipped)."""
        t = self.toks[k]
        j = k + 1
        if t.text == "for":
            # `for PAT in EXPR`: the `in` at depth 0 must come before any brace
            while j < limit and not _is(self.toks[j], "ident", "in"):
                if _is(self.toks[j], "punct", "{") or _is(self.toks[j], "punct", ";"):
                    return None
                if self.toks[j].kind == "punct" and self.toks[j].text in ("(", "["):
                    j = self.skip_group(j)
                    continue
                j += 1
        c = self.first_clause(j, limit)
        # the header up to the clauses: its first depth-0 brace is the body
        h = j
        stop = c if c is not None else limit
        while h < stop:
            x = self.toks[h]
            if x.kind == "punct" and x.text in ("(", "["):
                h = self.skip_group(h)
                continue
            if _is(x, "punct", "{"):
                if c is not None and h < c:
                    return h
                if c is None:
                    return h
            h += 1
        if c is None:
            return None
        body = self.find_body(c + 1, limit)
        return body if body is not None and _is(self.toks[body], "punct", "{") else None

    def analyse(self):
        if not self.blocks:
            raise StripError("no verus! block")
        for o, c in self.blocks:
            self.scan_items(o + 1, c)
        removed = {it.name for it in self.proof_items}
        keep_sig = set()
        while True:
            spans = self._item_spans(removed - keep_sig, keep_sig)
            named = self._kept_idents(spans)
            more = {n for n in removed - keep_sig if n in named}
            if not more:
                return spans
            keep_sig |= more

    def _item_spans(self, drop, keep_sig):
        spans = list(self.spans)
        for it in self.proof_items:
            if it.name in drop:
                spans.append((it.start, it.end, "proof-fn"))
            elif it.name in keep_sig and it.body is not None and it.end > it.body + 1:
                spans.append((it.body + 1, it.end - 1, "proof-body"))
        for s, e in self.mod_uses:
            names = {t.text for t in self.toks[s:e + 1] if t.kind == "ident"}
            if names & drop:
                spans.append((s, e, "broadcast-use"))
        return spans

    def _kept_idents(self, spans):
        gone = [False] * len(self.toks)
        for s, e, _ in spans:
            for x in range(s, e + 1):
                gone[x] = True
        return {t.text for k, t in enumerate(self.toks) if t.kind == "ident" and not gone[k]}

    def main_items(self):
        """Top-level `fn main` items outside every verus! block."""
        inside = [False] * len(self.toks)
        for o, c in self.blocks:
            for x in range(o, c + 1):
                inside[x] = True
        out = []
        k = 0
        while k < len(self.toks):
            t = self.toks[k]
            if inside[k]:
                k += 1
                continue
            if t.kind == "punct" and t.text in _OPEN:
                k = self.skip_group(k)      # top level only: nothing nested is an item here
                continue
            if _is(t, "ident", "fn") and _is(self.tok(k + 1), "ident", "main"):
                s = self.modifiers_start(k, 0)
                body = self.find_body(k + 2, len(self.toks))
                if body is not None and _is(self.toks[body], "punct", "{"):
                    out.append((s, self.m[body], "main"))
                    k = self.m[body] + 1
                    continue
            k += 1
        return out


# --- edits --------------------------------------------------------------------------------------

def _line_start(src, i):
    return src.rfind("\n", 0, i) + 1


def _line_end(src, i):
    j = src.find("\n", i)
    return len(src) if j < 0 else j


def _char_span(src, toks, s, e, kind):
    """The character span to delete for tokens s..e: widened to whole lines
    when the tokens own their lines, with attached comment, doc and attribute
    lines above an item or statement."""
    a, b = toks[s].start, toks[e].end
    ls = _line_start(src, a)
    le = _line_end(src, b)
    rest = src[b:le].strip()
    own_start = src[ls:a].strip() == ""
    own_end = rest == "" or rest.startswith("//")
    if kind == "proof-body":
        return a, b, ""
    if own_start and own_end:
        a, b = ls, min(le + 1, len(src))
        # attached lines above: comments (statements, items), doc comments and
        # attributes (items), with no blank line between
        while a > 0:
            pls = _line_start(src, a - 1)
            line = src[pls:a - 1].strip()
            if line.startswith("//") or (kind in ("proof-fn", "broadcast-group", "main")
                                         and line.startswith("#[")):
                a = pls
            else:
                break
        return a, b, ""
    if own_end:
        return a, le, ""
    pad = " " if a > 0 and not src[a - 1].isspace() and b < len(src) and not src[b].isspace() else ""
    return a, b, pad


def _apply(src, toks, spans):
    edits = []
    for s, e, kind in spans:
        if e < s:
            continue
        edits.append(_char_span(src, toks, s, e, kind))
    edits.sort()
    merged = []
    for a, b, pad in edits:
        if merged and a < merged[-1][1]:
            pa, pb, ppad = merged[-1]
            merged[-1] = (pa, max(pb, b), ppad)
        else:
            merged.append((a, b, pad))
    out, last = [], 0
    for a, b, pad in merged:
        out.append(src[last:a])
        out.append(pad)
        last = b
    out.append(src[last:])
    return "".join(out)


def drop_main(text):
    """verus-drop-main. Returns the new text (unchanged when no fn main)."""
    p = _Plan(text)
    spans = p.main_items()
    return _apply(text, p.toks, spans) if spans else text


def strip_proofs(text):
    """verus-strip-proofs (and verus-drop-main). Returns the task form."""
    p = _Plan(text)
    spans = p.analyse() + p.main_items()
    return _apply(text, p.toks, spans)


def strip_report(text):
    """{kind: count} of what strip_proofs removes from `text`."""
    p = _Plan(text)
    out = {}
    for _, _, kind in p.analyse() + p.main_items():
        out[kind] = out.get(kind, 0) + 1
    return out


_DAFNY_AXIOM_ASSUME = re.compile(r"assume\s*\{:axiom\}\s*false\s*;")


def dafny_axiom_assume_to_hole(text):
    return _DAFNY_AXIOM_ASSUME.sub("assume false;", text)


TRANSFORMS = {
    "verus-drop-main": (drop_main, (".rs",)),
    "verus-strip-proofs": (strip_proofs, (".rs",)),
    "dafny-axiom-assume-to-hole": (dafny_axiom_assume_to_hole, (".dfy",)),
}

TRANSFORM_NOTES = {
    "verus-drop-main": "the top-level `fn main` outside `verus!` dropped (the course gate "
                       "refuses code outside verus!, V9)",
    "verus-strip-proofs": "proofs removed (proof fns, proof statements, ghost lets, reveals, "
                          "loop invariants), the specification, the code and each loop's "
                          "decreases kept; the top-level `fn main` outside `verus!` dropped",
    "dafny-axiom-assume-to-hole": "each `assume {:axiom} false;` made `assume false;` (a hole "
                                  "the course gate counts)",
}


def apply(name, rel, data):
    """Apply transform `name` to file `rel` (bytes). Returns (bytes, changed)."""
    fn, exts = TRANSFORMS[name]
    if not rel.endswith(exts):
        return data, False
    text = data.decode("utf-8")
    new = fn(text)
    return new.encode("utf-8"), new != text


# --- the independent residue check -----------------------------------------------------------------

def proof_residue(text):
    """[(line, what)] proof constructs left inside verus! blocks: an `assert`
    statement (not Rust's `assert!`), a proof macro, `proof {`, a proof fn with
    a non-empty body, `ghost`/`tracked` lets, reveal/hide calls, loop clauses
    (`invariant…`, an `ensures` whose nearest keyword is a loop's; a loop's
    `decreases` is part of the task form)
    and `broadcast use` inside a fn body. Independent of the stripper's plan."""
    toks, _ = lex(text)
    m = matches(toks)
    out = []

    def line(k):
        return text.count("\n", 0, toks[k].start) + 1

    for o, c in verus_blocks(toks, m):
        bodies = []             # (open, close) of every fn body
        for k in range(o + 1, c):
            if _is(toks[k], "ident", "fn") and _is(toks[k + 1], "ident"):
                x = k + 2
                while x < c and not (toks[x].kind == "punct" and toks[x].text in ("{", ";")):
                    x = m[x] + 1 if toks[x].kind == "punct" and toks[x].text in ("(", "[") else x + 1
                if x < c and toks[x].text == "{":
                    bodies.append((x, m[x]))
        last_kw = []            # stack of (depth, keyword) seen
        depth = 0
        for k in range(o + 1, c):
            t = toks[k]
            nxt = toks[k + 1] if k + 1 < len(toks) else None
            if t.kind == "punct" and t.text in ("{", "(", "["):
                depth += 1
            elif t.kind == "punct" and t.text in ("}", ")", "]"):
                depth -= 1
                while last_kw and last_kw[-1][0] > depth:
                    last_kw.pop()
            if t.kind != "ident":
                continue
            if t.text == "assert" and not _is(nxt, "punct", "!"):
                out.append((line(k), "assert"))
            elif t.text in PROOF_MACROS and _is(nxt, "punct", "!"):
                out.append((line(k), f"{t.text}!"))
            elif t.text == "proof" and _is(nxt, "punct", "{"):
                out.append((line(k), "proof block"))
            elif t.text == "let" and _is(nxt, "ident") and nxt.text in ("ghost", "tracked"):
                out.append((line(k), f"let {nxt.text}"))
            elif t.text in _PROOF_CALLS and _is(nxt, "punct", "("):
                out.append((line(k), t.text))
            elif t.text in ("invariant", "invariant_except_break", "invariant_ensures"):
                out.append((line(k), t.text))
            elif t.text in ("while", "loop", "for", "fn"):
                last_kw.append((depth, t.text))
            elif t.text == "ensures":
                kw = next((w for d, w in reversed(last_kw) if d == depth), None)
                if kw in ("while", "loop", "for"):
                    out.append((line(k), "loop ensures"))
            elif t.text == "broadcast" and _is(nxt, "ident", "use") \
                    and any(a < k < b for a, b in bodies):
                out.append((line(k), "broadcast use in a body"))
            if t.text == "fn" and _is(nxt, "ident"):
                j, mods = k - 1, set()
                while j > o and toks[j].kind == "ident" and toks[j].text in _MODIFIERS:
                    mods.add(toks[j].text)
                    j -= 1
                if "proof" in mods:
                    # the body: the first `{` at this depth before a `;`
                    d, x = 0, k + 2
                    while x < c:
                        y = toks[x]
                        if y.kind == "punct" and y.text in ("(", "["):
                            x = m[x] + 1
                            continue
                        if _is(y, "punct", ";"):
                            break
                        if _is(y, "punct", "{"):
                            if m[x] > x + 1:
                                out.append((line(k), f"proof fn {nxt.text} keeps a body"))
                            break
                        x += 1
    return out


# --- Lab 2's public task forms (QPLAN §25.6) ----------------------------------------------------
#
# Lab 2's form of a complete file (the "second transform" beside verus-strip-proofs): the
# specification removed, the prose and the code kept, an empty witness, as Lab 2's local cards
# (bench/local/q/lab2/). One target declaration per file: Verus, the file's only exec fn;
# Dafny, the file's only method. Removed: the target's `requires`, `ensures` (Verus also
# `recommends`, `returns`, `default_ensures`), every proof (Verus: as verus-strip-proofs, but a
# proof fn always goes whole, and a kept line that still names one refuses the file; Dafny:
# lemmas, `assert`, `calc`, `reveal`, ghost variables, proof `forall` statements, lemma calls
# and loop invariants), the definitions only the proofs used (Verus: spec fns no kept line
# and no clause of the target's specification names; Dafny: functions and predicates of
# vericoding's `<vc-helpers>` section no kept line names), and (the user's decision D28,
# 2026-10-14) the definitions only the target's specification reaches that are not recursive:
# Lab2Form.definitions returns their text (Verus made `pub open`) for the sealed reference, so
# the prose, not a shipped predicate, carries the specification (split_definitions: what the
# code reaches stays, and so does a recursive definition the specification reaches, with all
# it names, since the grader's empty lemmas cannot equate two recursive definitions). Kept:
# every other definition, the target's signature with its
# `decreases` (Dafny also `modifies` and `reads`), the executable code, each loop's
# `decreases` (Dafny also a loop's `modifies`), every comment outside the removed spans (the
# HumanEval prompt among them). Changed (Verus): every kept spec fn becomes `pub open` (or
# stays `pub closed`), since the grader's lemmas are `pub proof fn`s and Verus refuses a public
# function whose clauses name a private one. Added: an empty witness (Verus `fn <name>_witness`;
# Dafny `method <Name>Witness`, or `<name>_witness` for a snake-case name) at the end of the
# target's block, and (Dafny, `prose`) the task's prose as a comment above the method. A file
# the transform cannot pose as one task raises StripError (the draw's eligibility rule skips it).

LAB2_VERUS_DROP = {"requires", "ensures", "recommends", "returns", "default_ensures"}
LAB2_VERUS_SIG = LAB2_VERUS_DROP | {"decreases", "opens_invariants", "no_unwind"}


@dataclass
class Lab2Form:
    text: str           # the task form
    lang: str           # "verus" or "dafny"
    name: str           # the target declaration
    witness: str        # the witness's name
    removed: dict       # {kind: count}
    definitions: list = None    # the sealed definitions (D28): the non-recursive definitions
    #                             only the specification used, removed from the form, each its
    #                             declaration's text (Verus: made `pub open`), in file order
    definition_names: list = None   # their names, in the same order
    quantified: list = None     # the definitions D37 keeps in the form although only the
    #                             specification uses them (under a quantifier), sorted; the
    #                             form carries no marker naming them (they would hint the
    #                             hidden specification): lab2pub records them author-side


def _reaches(graph, start):
    """The names reachable from `start` in {name: names it uses} (start excluded unless a
    cycle returns to it)."""
    seen, todo = set(), list(graph.get(start, ()))
    while todo:
        n = todo.pop()
        if n in seen:
            continue
        seen.add(n)
        todo += [m for m in graph.get(n, ()) if m not in seen]
    return seen


def _closure(graph, roots):
    out, todo = set(), list(roots)
    while todo:
        n = todo.pop()
        if n in out:
            continue
        out.add(n)
        todo += [m for m in graph.get(n, ()) if m not in out]
    return out


def split_definitions(graph, code_named, spec_named, quantified_named=()):
    """The user's decision D28 on a form's definitions. `graph` is {definition: definitions
    its body names}; `code_named` the definitions a kept line outside every definition names
    (the code, the other declarations); `spec_named` those the target's specification names.
    Returns (keep, sealed): keep, every definition the code reaches, every recursive one the
    specification reaches and every definition those reach; sealed, the definitions only the
    specification reaches that are not kept (non-recursive ones: they leave the form and go
    with the reference). A recursive definition stays (the grader's empty lemmas cannot equate
    two recursive definitions), and so does anything it names. D37 also retains
    definitions used under quantifiers, with their dependencies."""
    recursive = {n for n in graph if n in _reaches(graph, n)}
    spec = _closure(graph, [n for n in spec_named if n in graph])
    keep = _closure(graph, [n for n in code_named if n in graph] +
                    [n for n in spec if n in recursive] +
                    [n for n in quantified_named if n in graph])
    return keep, spec - keep


def quantified_names(toks, spans):
    """Identifiers in a quantified clause's enclosing expression (D37).

    A quantifier inside brackets ends at its enclosing bracket; a top-level
    quantifier extends to the clause's end. Dependencies are closed by
    split_definitions, so a retained helper remains self-contained.
    """
    names = set()
    for a, b in spans:
        stack = []
        pairs = {}
        for i in range(a, b + 1):
            word = toks[i].text
            if word in ("(", "[", "{"):
                stack.append(i)
            elif word in (")", "]", "}") and stack:
                pairs[stack.pop()] = i
        stack = []
        for i in range(a, b + 1):
            word = toks[i].text
            if word in ("(", "[", "{"):
                stack.append(i)
            elif word in (")", "]", "}") and stack:
                stack.pop()
            elif word in ("forall", "exists"):
                end = pairs.get(stack[-1], b) if stack else b
                # Verus puts multiple ensures expressions in one clause span.
                # Stop at the expression's separating comma, not a quantifier's
                # binder comma (forall|i: int, j: int| ...).
                bars, body_start = 0, i + 1
                for j in range(i + 1, end + 1):
                    if toks[j].text == "::":
                        body_start = j + 1
                        break
                    if toks[j].text == "|":
                        bars += 1
                        if bars == 2:
                            body_start = j + 1
                            break
                depth = 0
                for j in range(body_start, end + 1):
                    w = toks[j].text
                    if w in ("(", "[", "{"):
                        depth += 1
                    elif w in (")", "]", "}"):
                        depth -= 1
                    elif w == "," and depth == 0:
                        end = j - 1
                        break
                names.update(t.text for t in toks[i:end + 1])
    return names


def _verus_fns(p):
    """[(mode, name, start, kw, body, end, is_decl)] of every fn inside the verus! blocks."""
    out = []
    for o, c in p.blocks:
        k = o + 1
        while k < c:
            t = p.toks[k]
            if _is(t, "ident", "fn") and _is(p.tok(k + 1), "ident"):
                s = p.modifiers_start(k, o + 1)
                mods = {x.text for x in p.toks[s:k]}
                body = p.find_body(k + 2, c)
                if body is None:
                    raise StripError(f"fn {p.toks[k + 1].text}: no body or `;` found")
                is_decl = _is(p.toks[body], "punct", ";")
                end = body if is_decl else p.m[body]
                mode = "proof" if "proof" in mods or "axiom" in mods else \
                    "spec" if "spec" in mods else "exec"
                out.append((mode, p.toks[k + 1].text, s, k, body, end, is_decl))
                k = end + 1
                continue
            k += 1
    return out


def _sig_clause_spans(p, kw, body, drop):
    """Token spans (first, last) of the signature clauses in `drop` between a fn's keyword
    and its body brace (each up to the next signature clause or the body)."""
    marks = []
    j = kw + 2
    while j < body:
        t = p.toks[j]
        if t.kind == "punct" and t.text in ("(", "[", "{"):
            j = p.skip_group(j)
            continue
        if t.kind == "ident" and t.text in LAB2_VERUS_SIG:
            marks.append(j)
        j += 1
    out = []
    for i, a in enumerate(marks):
        e = (marks[i + 1] if i + 1 < len(marks) else body) - 1
        if p.toks[a].text in drop:
            out.append((a, e))
    return out


def _publish_edits(p, fns):
    """Character edits that make each kept spec fn `pub open` (or `pub closed`): the grader's
    lemmas are `pub proof fn`s (fvh_q.oracles.render_lemma), and Verus refuses a public
    function whose clauses name a private one. A spec fn already `pub` (unrestricted) is left
    as it is; `pub(crate)` and the like become `pub`; `open` is added unless `open` or `closed`
    is there. Within the file's own module nothing else changes."""
    out = []
    for _, _, start, kw, _, _, _ in fns:
        mods = p.toks[start:kw]
        texts = [t.text for t in mods]
        restricted = "pub" in texts and start + texts.index("pub") + 1 < kw and \
            _is(p.toks[start + texts.index("pub") + 1], "punct", "(")
        if "pub" in texts and not restricted and ("open" in texts or "closed" in texts):
            continue
        first = p.toks[start]
        if restricted:
            i = start + texts.index("pub")
            close = p.m[i + 1]
            a, b = p.toks[i].start, p.toks[close].end
            rest = "" if ("open" in texts or "closed" in texts) else " open"
            out.append((a, b, "pub" + rest))
            continue
        spec_tok = next(t for t in mods if t.text == "spec")
        if "pub" not in texts:
            out.append((first.start, first.start, "pub "))
        if "open" not in texts and "closed" not in texts:
            out.append((spec_tok.start, spec_tok.start, "open "))
    return out


def lab2_publish_verus(text, names=None):
    """The Verus file with its spec fns (or the named ones) made `pub open` as the Lab 2 form
    makes its kept ones (the reference program's normalization)."""
    p = _Plan(text)
    fns = [f for f in _verus_fns(p) if f[0] == "spec" and (names is None or f[1] in names)]
    return _apply_char_edits(text, _publish_edits(p, fns))


def _witness_name(name, taken, verus):
    w = f"{name}_witness" if (verus or "_" in name or name[:1].islower()) else f"{name}Witness"
    if w in taken:
        raise StripError(f"the file already declares {w}")
    return w


_BLANK_LINE = re.compile(r"[ \t]*\n")


def _apply_char_edits(src, edits):
    """Apply (a, b, insert) character edits (sorted, overlapping removals merged). A removal
    that leaves two blank lines in a row also takes the blank lines after it (up to the next
    edit), so removed items leave one blank line, not a run of them."""
    edits = sorted(edits, key=lambda e: (e[0], e[1]))
    merged = []
    for a, b, ins in edits:
        if merged and a < merged[-1][1]:
            pa, pb, pins = merged[-1]
            merged[-1] = (pa, max(pb, b), pins + ins)
        else:
            merged.append((a, b, ins))
    out, last = [], 0
    for i, (a, b, ins) in enumerate(merged):
        out.append(src[last:a])
        out.append(ins)
        b = max(last, b)
        if not ins and a < b:
            limit = merged[i + 1][0] if i + 1 < len(merged) else len(src)
            while "".join(out).endswith("\n\n"):
                m = _BLANK_LINE.match(src, b)
                if not m or m.end() > limit:
                    break
                b = m.end()
        last = b
    out.append(src[last:])
    return "".join(out)


_STMT_KINDS = {"assert", "proof-macro", "proof-block", "ghost-let", "reveal", "broadcast-use"}


def _comment_above(text, a, b, ins):
    """A removed proof statement's character edit widened over the comment lines that sit
    above it with one blank line between (`_char_span` takes only the comment lines right
    above): such a comment describes the removed step (HumanEval-Verus's "Invoke a lemma …"
    above a `proof { … }` block), so the form drops it too."""
    if ins or a != _line_start(text, a) or a < 2:
        return a, b, ins
    blank = _line_start(text, a - 1)
    if text[blank:a].strip():
        return a, b, ins
    top = blank
    while top > 0:
        pls = _line_start(text, top - 1)
        line = text[pls:top - 1].strip()
        if line.startswith("//") and not line.startswith("///"):
            top = pls
        else:
            break
    return (top, b, ins) if top < blank else (a, b, ins)


def lab2_form_verus(text):
    """Lab 2's form of a complete Verus file (see above). Returns a Lab2Form."""
    p = _Plan(text)
    p.analyse()                     # fills p.spans (proof statements, loop clauses), items
    fns = _verus_fns(p)
    execs = [f for f in fns if f[0] == "exec"]
    if len(execs) != 1:
        raise StripError(f"the file has {len(execs)} exec fns, not one")
    _, name, f_start, f_kw, f_body, f_end, is_decl = execs[0]
    if is_decl:
        raise StripError(f"fn {name} has no body")
    spans = [(s, e, k) for s, e, k in p.spans]
    removed = {}

    def note(kind):
        removed[kind] = removed.get(kind, 0) + 1
    for _, _, k in spans:
        note(k)
    for it in p.proof_items:
        spans.append((it.start, it.end, "proof-fn"))
        note("proof-fn")
    for s, e in p.mod_uses:
        spans.append((s, e, "broadcast-use"))
        note("broadcast-use")
    for s, e, k in p.main_items():
        spans.append((s, e, k))
        note(k)
    clause_spans = _sig_clause_spans(p, f_kw, f_body, LAB2_VERUS_DROP)
    if not any(p.toks[a].text == "ensures" for a, _ in clause_spans):
        raise StripError(f"fn {name} states no ensures")
    for a, e in clause_spans:
        spans.append((a, e, "spec-clause"))
        note("spec-clause")
    clause_idents = {p.toks[x].text for a, e in clause_spans for x in range(a, e + 1)
                     if p.toks[x].kind == "ident"}
    # spec fns (the user's decision D28): kept when a kept token outside every spec fn names
    # them, when the target's specification names them and they are recursive, or when a kept
    # spec fn names them; sealed (removed, and sealed with the reference as its `definitions`)
    # when only the specification reaches them and they are not recursive; the rest (only
    # proofs used them) removed
    specs = {f[1]: f for f in fns if f[0] == "spec"}
    gone = [False] * len(p.toks)
    for s, e, _ in spans:
        for x in range(s, e + 1):
            gone[x] = True
    in_spec = [False] * len(p.toks)
    for f in specs.values():
        for x in range(f[2], f[5] + 1):
            in_spec[x] = True
    code_named = {t.text for k, t in enumerate(p.toks) if t.kind == "ident" and not gone[k]
                  and not in_spec[k]}
    graph = {n: {p.toks[x].text for x in range(f[2], f[5] + 1)
                 if p.toks[x].kind == "ident" and not gone[x] and x != f[3] + 1} & set(specs)
             for n, f in specs.items()}
    quantified = quantified_names(p.toks, clause_spans) & set(specs)
    keep, sealed = split_definitions(graph, code_named, clause_idents, quantified)
    baseline_keep, _ = split_definitions(graph, code_named, clause_idents)
    retained_quantified = keep - baseline_keep
    defs, def_names = [], []
    for n, f in specs.items():          # file order
        if n in keep:
            continue
        spans.append((f[2], f[5], "proof-fn"))
        if n in sealed:
            note("spec-definition")
            body = text[p.toks[f[2]].start:p.toks[f[5]].end]
            wrapped = lab2_publish_verus("verus! {\n" + body + "\n}\n")
            defs.append(wrapped[len("verus! {\n"):-len("\n}\n")])
            def_names.append(n)
        else:
            note("spec-fn")
    publish = []
    for n in sorted(keep):
        e = _publish_edits(p, [specs[n]])
        if e:
            publish += e
            note("spec-fn-published")
    # no kept line may name a removed proof fn
    gone = [False] * len(p.toks)
    for s, e, _ in spans:
        for x in range(s, e + 1):
            gone[x] = True
    kept_idents = {t.text for k, t in enumerate(p.toks) if t.kind == "ident" and not gone[k]}
    proof_names = {it.name for it in p.proof_items}
    left = sorted(proof_names & kept_idents)
    if left:
        raise StripError(f"a kept line names the proof fn(s) {left}")
    taken = {f[1] for f in fns}
    witness = _witness_name(name, taken, True)
    edits = [_comment_above(text, *_char_span(text, p.toks, s, e, k)) if k in _STMT_KINDS
             else _char_span(text, p.toks, s, e, k) for s, e, k in spans if e >= s] + publish
    # the witness, before the closing brace of the target's verus! block
    close = next(c for o, c in p.blocks if o < f_kw < c)
    at = _line_start(text, p.toks[close].start)
    if text[at:p.toks[close].start].strip():
        at = p.toks[close].start
    edits.append((at, at, f"/// A non-vacuity witness for `{name}`: one call whose "
                          f"`requires` hold.\nfn {witness}() {{\n}}\n\n"))
    form = _apply_char_edits(text, edits)
    form = re.sub(r"\n\n\n+(/// A non-vacuity witness for `)", r"\n\n\1", form)
    if f"\n\n/// A non-vacuity witness for `{name}`" not in form:
        form = form.replace("/// A non-vacuity witness for `", "\n/// A non-vacuity witness for `", 1)
    return Lab2Form(form, "verus", name, witness, removed, defs, def_names,
                    sorted(retained_quantified))


# --- Dafny -----------------------------------------------------------------------------------------

_D_LOOP_CLAUSES = {"invariant", "decreases", "modifies"}
_D_STMT_PREV = {"{", "}", ";"}


def _d_close(toks, k):
    """The index of the token that closes the group opening at k."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    want, depth = [], 0
    for j in range(k, len(toks)):
        x = toks[j].text
        if toks[j].kind == "op" and x in pairs:
            want.append(pairs[x])
        elif toks[j].kind == "op" and want and x == want[-1]:
            want.pop()
            if not want:
                return j
    raise StripError(f"an unbalanced {toks[k].text!r} at line {toks[k].line}")


def _d_stmt_end(toks, k, limit, by_block=False):
    """The last token of the statement starting at k: its `;` at depth 0, or (an assertion's
    `by`, a calc's or a forall statement's body) the brace closing its block."""
    j = k
    while j < limit:
        t = toks[j]
        if t.kind == "op" and t.text in ("(", "["):
            j = _d_close(toks, j) + 1
            continue
        if t.kind == "op" and t.text == "{":
            c = _d_close(toks, j)
            prev = toks[j - 1].text if j > 0 else ""
            if by_block or prev == "by":
                return c + 1 if c + 1 < limit and toks[c + 1].text == ";" else c
            j = c + 1
            continue
        if t.kind == "op" and t.text == ";":
            return j
        if t.kind == "op" and t.text == "}":
            return j - 1
        j += 1
    return limit - 1


def _d_loop_body(toks, k, limit):
    """The `{` of the loop whose keyword is at k (the first depth-0 brace not opened by an
    expression), or None."""
    from dvl import dafny as D
    j = k + 1
    while j < limit:
        t = toks[j]
        if t.kind == "op" and t.text in ("(", "["):
            j = _d_close(toks, j) + 1
            continue
        if t.kind == "op" and t.text == "{":
            prev = toks[j - 1].text
            if prev in D.EXPR_PREV and prev not in _D_LOOP_CLAUSES:
                j = _d_close(toks, j) + 1
                continue
            return j
        if t.kind == "op" and t.text == ";":
            return None
        j += 1
    return None


def _d_char_span(text, toks, s, e):
    """A Dafny token span as a character edit: whole lines when the tokens own them (with the
    comment and attribute lines right above), else the tokens alone."""
    a, b = toks[s].start, toks[e].end
    ls, le = _line_start(text, a), _line_end(text, b)
    rest = text[b:le].strip()
    if text[ls:a].strip() == "" and (rest == "" or rest.startswith("//")):
        a, b = ls, min(le + 1, len(text))
        while a > 0:
            pls = _line_start(text, a - 1)
            line = text[pls:a - 1].strip()
            if line.startswith("//") and not line.startswith("// <"):
                a = pls
            else:
                break
        return a, b, ""
    if rest == "" or rest.startswith("//"):
        return a, le, ""
    return a, b, ""


def lab2_form_dafny(text, prose=None):
    """Lab 2's form of a complete Dafny file (see above). `prose`, when given, goes in a block
    comment right above the target method. Returns a Lab2Form."""
    from dvl import dafny as D
    try:
        src = D.parse_source(text)
    except Exception as e:  # noqa: BLE001
        raise StripError(f"the Dafny parser refused the file: {e}") from None
    toks = src.toks
    methods = [d for d in src.decls if d.kind in ("method", "constructor", "iterator")]
    if len(methods) != 1:
        raise StripError(f"the file has {len(methods)} methods, not one")
    d = methods[0]
    if not d.body:
        raise StripError(f"method {d.name} has no body")
    if any(a.name in ("axiom", "extern") or a.name in ("Axiom", "Extern") for a in src.attrs):
        raise StripError("the file carries an {:axiom} or {:extern} attribute")
    removed = {}

    def note(kind):
        removed[kind] = removed.get(kind, 0) + 1
    spans = []                      # (first token, last token)
    lemmas = [x for x in src.decls if x.kind in ("lemma", "colemma") or
              (x.kind in ("lemma", "method") and "ghost" in x.modifiers and x is not d)]
    lemma_names = {x.name for x in lemmas}
    for x in lemmas:
        last = x.body[1] if x.body else x.header_end - 1
        spans.append((x.start, last))
        note("lemma")
    # the target's requires and ensures
    starts = sorted(k for _, k in d.clauses if d.start <= k < d.header_end)
    if not any(toks[k].text == "ensures" for k in starts):
        raise StripError(f"method {d.name} states no ensures")
    spec_spans = []
    for n, k in enumerate(starts):
        end = (starts[n + 1] if n + 1 < len(starts) else d.header_end) - 1
        if toks[k].text in ("requires", "ensures"):
            spans.append((k, end))
            spec_spans.append((k, end))
            note("spec-clause")
    # the proofs in the body
    o, c = d.body
    k = o + 1
    while k < c:
        t = toks[k]
        prev = toks[k - 1].text
        at_stmt = prev in _D_STMT_PREV
        nxt = toks[k + 1] if k + 1 < c else None
        if t.kind == "id" and at_stmt:
            kind = None
            by_block = False
            if t.text == "assert":
                kind = "assert"
            elif t.text == "assume":
                raise StripError("the body holds an assume")
            elif t.text == "calc":
                kind, by_block = "calc", True
            elif t.text == "reveal":
                kind = "reveal"
            elif t.text == "ghost" and nxt is not None and nxt.text in ("var", "const"):
                kind = "ghost-var"
            elif t.text == "forall":
                body = _d_loop_body(toks, k, c)
                if body is None or not any(toks[x].text == "ensures" for x in range(k, body)):
                    raise StripError("a forall statement that is not a proof")
                kind, by_block = "forall-proof", True
            elif t.text in lemma_names and nxt is not None and nxt.text in ("(", "<"):
                kind = "lemma-call"
            if kind:
                e = _d_stmt_end(toks, k, c, by_block)
                spans.append((k, e))
                note(kind)
                k = e + 1
                continue
        if t.kind == "id" and t.text in ("while", "for"):
            body = _d_loop_body(toks, k, c)
            if body is not None:
                marks = [x for x in range(k + 1, body) if toks[x].kind == "id"
                         and toks[x].text in _D_LOOP_CLAUSES and _depth0(toks, k + 1, x)]
                for i, a in enumerate(marks):
                    e = (marks[i + 1] if i + 1 < len(marks) else body) - 1
                    if toks[a].text == "invariant":
                        spans.append((a, e))
                        note("loop-invariant")
                k = body + 1
                continue
        k += 1
    # vc-helpers definitions no kept token names
    hs, he = text.find("// <vc-helpers>"), text.find("// </vc-helpers>")
    helpers = [x for x in src.decls if x.kind in ("function", "predicate") and hs >= 0
               and hs < toks[x.start].start < he] if he > hs >= 0 else []
    gone = [False] * len(toks)
    for s, e in spans:
        for x in range(s, e + 1):
            gone[x] = True
    in_help = [False] * len(toks)
    hspan = {}
    for x in helpers:
        last = x.by_method[1] if x.by_method else x.body[1] if x.body else x.header_end - 1
        hspan[x.name] = (x.start, last)
        for y in range(x.start, last + 1):
            in_help[y] = True
    named = {t.text for j, t in enumerate(toks) if t.kind == "id" and not gone[j]
             and not in_help[j]}
    keep, todo = set(), [n for n in hspan if n in named]
    while todo:
        n = todo.pop()
        if n in keep:
            continue
        keep.add(n)
        a, b = hspan[n]
        inner = {toks[y].text for y in range(a, b + 1) if toks[y].kind == "id"}
        todo += [m for m in hspan if m in inner and m not in keep]
    for n, (a, b) in hspan.items():
        if n not in keep:
            spans.append((a, b))
            note("helper-definition")
    # the user's decision D28: a function or predicate only the target's specification
    # reaches, and not recursive, leaves the form and is sealed with the reference as its
    # `definitions`; recursive ones and those the code reaches stay
    gone = [False] * len(toks)
    for s_, e_ in spans:
        for x in range(s_, e_ + 1):
            gone[x] = True
    dspan = {}
    for x in src.decls:
        if x.kind not in ("function", "predicate") or gone[x.start]:
            continue
        last = x.by_method[1] if x.by_method else x.body[1] if x.body else x.header_end - 1
        name_at = next((j for j in range(x.kw + 1, x.header_end) if toks[j].kind == "id"
                        and toks[j].text == x.name), None)
        dspan[x.name] = (x.start, last, name_at)
    in_def = [False] * len(toks)
    for a, b, _ in dspan.values():
        for y in range(a, b + 1):
            in_def[y] = True
    code_named = {t.text for j, t in enumerate(toks) if t.kind == "id" and not gone[j]
                  and not in_def[j]}
    spec_named = {toks[y].text for a, b in spec_spans for y in range(a, b + 1)
                  if toks[y].kind == "id"}
    graph = {n: {toks[y].text for y in range(a, b + 1) if toks[y].kind == "id" and y != at}
             & set(dspan) for n, (a, b, at) in dspan.items()}
    quantified = quantified_names(toks, spec_spans) & set(dspan)
    _keep, sealed = split_definitions(graph, code_named, spec_named, quantified)
    baseline_keep, _ = split_definitions(graph, code_named, spec_named)
    retained_quantified = _keep - baseline_keep
    defs, def_names = [], []
    for n, (a, b, _) in sorted(dspan.items(), key=lambda kv: kv[1][0]):
        if n in sealed:
            spans.append((a, b))
            note("spec-definition")
            defs.append(text[toks[a].start:toks[b].end])
            def_names.append(n)
    gone = [False] * len(toks)
    for s, e in spans:
        for x in range(s, e + 1):
            gone[x] = True
    left = sorted({t.text for j, t in enumerate(toks) if t.kind == "id" and not gone[j]}
                  & lemma_names)
    if left:
        raise StripError(f"a kept line names the lemma(s) {left}")
    taken = {x.name for x in src.decls}
    witness = _witness_name(d.name, taken, False)
    edits = [_d_char_span(text, toks, s, e) for s, e in spans if e >= s]
    if prose is not None:
        body = prose.replace("*/", "* /").rstrip("\n")
        at = _line_start(text, toks[d.start].start)
        edits.append((at, at, "/* The task's prose:\n" + body + "\n*/\n"))
    # the witness: after the target's module's last member, else at the end of the file
    mod = next((m for m in src.modules if m.open < d.kw < m.close), None)
    wtext = (f"\n/** A non-vacuity witness for `{d.name}`: one call whose `requires` hold. */\n"
             f"method {witness}()\n{{\n}}\n")
    if mod is not None:
        at = _line_start(text, toks[mod.close].start)
        edits.append((at, at, wtext))
        form = _apply_char_edits(text, edits)
    else:
        form = _apply_char_edits(text, edits).rstrip("\n") + "\n" + wtext
    return Lab2Form(form, "dafny", d.name, witness, removed, defs, def_names,
                    sorted(retained_quantified))


def _depth0(toks, a, x):
    """True when token x sits at bracket depth 0 counted from token a."""
    depth = 0
    for j in range(a, x):
        if toks[j].kind == "op" and toks[j].text in ("(", "[", "{"):
            depth += 1
        elif toks[j].kind == "op" and toks[j].text in (")", "]", "}"):
            depth -= 1
    return depth == 0


def lab2_form(text, lang, prose=None):
    if lang == "verus":
        if prose is not None:
            raise StripError("a Verus form keeps its own prose (the file's prompt comment)")
        return lab2_form_verus(text)
    if lang == "dafny":
        return lab2_form_dafny(text, prose)
    raise StripError(f"a Lab 2 form is Dafny or Verus, not {lang}")


def _lab2_verus(text):
    return lab2_form_verus(text).text


def _lab2_dafny(text):
    return lab2_form_dafny(text).text


TRANSFORMS["verus-lab2-form"] = (_lab2_verus, (".rs",))
TRANSFORMS["dafny-lab2-form"] = (_lab2_dafny, (".dfy",))
TRANSFORM_NOTES["verus-lab2-form"] = (
    "Lab 2's form: the only exec fn's requires and ensures removed, the proofs and the "
    "definitions only they use removed, the non-recursive definitions only the specification "
    "uses removed (D28), except quantified definitions retained under D37, the code and the prompt kept, an empty witness added")
TRANSFORM_NOTES["dafny-lab2-form"] = (
    "Lab 2's form: the only method's requires and ensures removed, the lemmas, proof statements "
    "and loop invariants removed, the non-recursive definitions only the specification uses "
    "removed (D28), except quantified definitions retained under D37, the code kept, an empty witness added")


# --- the independent specification check -------------------------------------------------------

def spec_residue(text, lang, name):
    """[(line, what)] specification or proof left in a Lab 2 form: a `requires`/`ensures`
    (Verus also `recommends`, `returns`) on `name`, and the proof residue (Verus:
    proof_residue, plus any proof fn; Dafny: a lemma, an assert, calc, reveal, ghost
    variable, loop invariant, assume). Independent of the transform's plan."""
    out = []
    if lang == "verus":
        out += proof_residue(text)
        toks, _ = lex(text)
        m = matches(toks)
        for k in range(len(toks) - 1):
            t = toks[k]
            if _is(t, "ident", "fn") and _is(toks[k + 1], "ident"):
                j, mods = k - 1, set()
                while j >= 0 and toks[j].kind == "ident" and toks[j].text in _MODIFIERS:
                    mods.add(toks[j].text)
                    j -= 1
                if "proof" in mods:
                    out.append((text.count("\n", 0, t.start) + 1, f"proof fn {toks[k + 1].text}"))
                if toks[k + 1].text == name:
                    x = k + 2
                    while x < len(toks) and not (toks[x].kind == "punct" and
                                                 toks[x].text in ("{", ";")):
                        if toks[x].kind == "punct" and toks[x].text in ("(", "["):
                            x = m[x] + 1
                            continue
                        if toks[x].kind == "ident" and toks[x].text in LAB2_VERUS_DROP:
                            out.append((text.count("\n", 0, toks[x].start) + 1,
                                        f"{toks[x].text} on {name}"))
                        x += 1
        return out
    from dvl import dafny as D
    src = D.parse_source(text)
    toks = src.toks
    hs, he = text.find("// <vc-helpers>"), text.find("// </vc-helpers>")
    for x in src.decls:
        if x.kind in ("lemma", "colemma"):
            out.append((x.line, f"lemma {x.name}"))
        if he > hs >= 0 and hs < toks[x.start].start < he and \
                any(kw in ("requires", "ensures") for kw, _ in x.clauses):
            out.append((x.line, f"a helper's contract ({x.name})"))
        if x.name == name and x.kind == "method":
            for kw, k in x.clauses:
                if kw in ("requires", "ensures") and x.start <= k < x.header_end:
                    out.append((toks[k].line, f"{kw} on {name}"))
    for t in toks:
        if t.kind == "id" and t.text in ("assert", "calc", "reveal", "invariant", "assume"):
            out.append((t.line, t.text))
    for a, b in zip(toks, toks[1:]):
        if a.text == "ghost" and b.text == "var":
            out.append((a.line, "ghost var"))
    return out


def definition_residue(text, lang, kept=()):
    """[(line, name)] definitions a Lab 2 form keeps that the user's decision D28 would remove,
    found from the form alone (independent of the transform and of any specification): a
    definition (Verus spec fn; Dafny function or predicate) that is not recursive, that no
    line outside the definitions names, that no recursive definition reaches, and that is
    not one of `kept` (the definitions D37 retains because the reference specification uses
    them under a quantifier, with what they reach; recorded author-side, never in the form).
    Such a definition can only be specification vocabulary (or unused), which the form must
    not ship unless it is recursive or kept."""
    if lang == "verus":
        p = _Plan(text)
        fns = [f for f in _verus_fns(p) if f[0] == "spec"]
        toks = p.toks
        spans = {f[1]: (f[2], f[5], f[3] + 1) for f in fns}
        kind = "ident"
    else:
        from dvl import dafny as D
        src = D.parse_source(text)
        toks = src.toks
        spans = {}
        for x in src.decls:
            if x.kind in ("function", "predicate"):
                last = x.by_method[1] if x.by_method else x.body[1] if x.body else x.header_end - 1
                at = next((j for j in range(x.kw + 1, x.header_end) if toks[j].kind == "id"
                           and toks[j].text == x.name), None)
                spans[x.name] = (x.start, last, at)
        kind = "id"
    inside = [False] * len(toks)
    for a, b, _ in spans.values():
        for y in range(a, b + 1):
            inside[y] = True
    code_named = {t.text for j, t in enumerate(toks) if t.kind == kind and not inside[j]}
    graph = {n: {toks[y].text for y in range(a, b + 1) if toks[y].kind == kind and y != at}
             & set(spans) for n, (a, b, at) in spans.items()}
    recursive = {n for n in graph if n in _reaches(graph, n)}
    reached = _closure(graph, [n for n in code_named if n in graph] + sorted(recursive)
                       + [n for n in kept if n in graph])
    out = []
    for n, (a, _, _) in spans.items():
        if n not in reached:
            line = toks[a].line if lang == "dafny" else text.count("\n", 0, toks[a].start) + 1
            out.append((line, n))
    return sorted(out)
