"""verus_spec.py: a tokenizer and item parser for Verus sources (DV1b).

Pure text: no verifier, no registry, no file outside the ones it is given.
It never prints file content. `dvl/verus.py` uses it for four jobs:

  * the statement freeze (spec §11.1 row 29): one sha256 per item over its
    signature and its `requires` / `ensures` / `recommends` / `decreases`
    (and every other) clauses, plus the body of a `spec fn` (the body of a
    spec function is part of the statement);
  * the lint (Δ9, design §6.3): constructs that stay green under
    `--no-cheating` and so must be found in the source;
  * the empty-body gate (Δ47): locating one item's body and rewriting it;
  * crate structure: which files `mod x;` declarations reach, which items
    sit outside `verus!`, which `broadcast group`s a crate declares.

How it parses. The tokenizer drops whitespace and comments (line, nested
block and doc comments) and keeps identifiers, literals (strings with
escapes, raw strings `r#"…"#`, byte and C strings, chars), lifetimes and
punctuation, each with its line and column. Brackets `()`, `[]` and `{}`
are matched once; `<…>` is never tracked as a bracket. The item parser
walks Rust items at module level, inside `verus! { … }`, inside inline
`mod m { … }`, `impl … { … }` and `trait … { … }` blocks; it never parses
statements except for the body rewrites of the empty-body gate.

Known limits (documented, not silent):
  * a function's body is the first `{` at bracket depth 0 after its
    parameter list that does not belong to a `match`, `if`/`else`, loop or
    closure expression inside a clause. A block expression or a struct
    literal written bare in a clause (outside parentheses) would be taken
    for the body; Verus itself requires parentheses around struct literals
    there, so course code never does this;
  * generics are skipped by counting `<` and `>` tokens;
  * macro invocations other than `verus!` are opaque token groups;
  * `#[path = …]` on a `mod` is not followed (the lint flags it);
  * the body rewrites strip statements by their leading keyword (`proof`,
    `assert`, `assume`, `let ghost`, `let tracked`, `broadcast use`,
    `reveal…`, `hide`) and loop clauses by keyword; an assignment to a ghost
    variable outside a `proof { }` block is kept.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

# --- tokens --------------------------------------------------------------------------

PUNCT = sorted("""<==> === !== ==> <== &&& ||| ..= ... <<= >>= :: -> => == != <= >= && || .. += -= *= /= %=
^= &= |= << >>""".split(), key=len, reverse=True)
OPEN, CLOSE = "([{", ")]}"
IDENT = re.compile(r"r#[A-Za-z_][A-Za-z0-9_]*|[A-Za-z_][A-Za-z0-9_]*")
NUMBER = re.compile(r"[0-9][0-9A-Za-z_]*")
STRING_START = re.compile(r'(br|rb|cr|r|b|c)?(#*)"')


@dataclass(frozen=True)
class Tok:
    kind: str    # id | punct | lit | life
    text: str
    line: int    # 1-based
    col: int     # 1-based
    start: int   # character offsets into the source
    end: int


class ParseError(ValueError):
    """The source cannot be tokenized or bracket-matched."""

    def __init__(self, msg, line=0):
        super().__init__(msg)
        self.line = line


def tokenize(text):
    """Tokens of Rust/Verus source, comments and whitespace dropped."""
    toks = []
    i, n, line, line_start = 0, len(text), 1, 0

    def add(kind, j):
        toks.append(Tok(kind, text[i:j], line, i - line_start + 1, i, j))

    def advance_lines(a, b):
        nonlocal line, line_start
        k = text.find("\n", a, b)
        while k != -1:
            line += 1
            line_start = k + 1
            k = text.find("\n", k + 1, b)

    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
            line_start = i + 1
            i += 1
            continue
        if c.isspace():
            i += 1
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        if text.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if text.startswith("/*", j):
                    depth, j = depth + 1, j + 2
                elif text.startswith("*/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            if depth:
                raise ParseError("unterminated block comment", line)
            advance_lines(i, j)
            i = j
            continue
        at_word_start = i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")
        m = STRING_START.match(text, i) if (c == '"' or (c in "rbc" and at_word_start)) else None
        if m:
            letters, hashes = m.group(1) or "", m.group(2)
            j = m.end()
            if "r" in letters:
                close = '"' + hashes
                k = text.find(close, j)
                if k == -1:
                    raise ParseError("unterminated raw string", line)
                j = k + len(close)
            else:
                if hashes:
                    raise ParseError("'#' before a non-raw string", line)
                while j < n and text[j] != '"':
                    j += 2 if text[j] == "\\" else 1
                if j >= n:
                    raise ParseError("unterminated string", line)
                j += 1
            add("lit", j)
            advance_lines(i, j)
            i = j
            continue
        q = i + 1 if (c == "b" and at_word_start and text.startswith("b'", i)) else (i if c == "'" else -1)
        if q >= 0 and q + 1 < n and text[q + 1] == "\\":          # '\n', '\'', '\u{..}', b'\x00'
            j = text.find("'", q + 3)
            if j == -1:
                raise ParseError("unterminated char literal", line)
            add("lit", j + 1)
            i = j + 1
            continue
        if q > i and q + 2 < n and text[q + 2] == "'":             # b'x'
            add("lit", q + 3)
            i = q + 3
            continue
        if c == "'":
            if i + 2 < n and text[i + 2] == "'":
                add("lit", i + 3)
                i += 3
                continue
            m = IDENT.match(text, i + 1)
            if m:
                add("life", m.end())
                i = m.end()
                continue
            add("punct", i + 1)
            i += 1
            continue
        m = IDENT.match(text, i)
        if m:
            add("id", m.end())
            i = m.end()
            continue
        if c.isdigit():
            j = NUMBER.match(text, i).end()
            if text.startswith(".", j) and j + 1 < n and text[j + 1].isdigit():
                j = NUMBER.match(text, j + 1).end()          # 1.5 (a tuple index x.0.1 too)
            add("lit", j)
            i = j
            continue
        for p in PUNCT:
            if text.startswith(p, i):
                add("punct", i + len(p))
                i += len(p)
                break
        else:
            add("punct", i + 1)
            i += 1
    return toks


def match_brackets(toks):
    """{open index: close index} and its inverse; raises ParseError when the
    brackets do not balance."""
    pairs, stack = {}, []
    for k, t in enumerate(toks):
        if t.kind != "punct":
            continue
        if t.text in OPEN:
            stack.append(k)
        elif t.text in CLOSE:
            if not stack or OPEN.index(toks[stack[-1]].text) != CLOSE.index(t.text):
                raise ParseError(f"unbalanced '{t.text}'", t.line)
            o = stack.pop()
            pairs[o] = k
            pairs[k] = o
    if stack:
        raise ParseError(f"unclosed '{toks[stack[-1]].text}'", toks[stack[-1]].line)
    return pairs


# --- items ---------------------------------------------------------------------------

FN_QUALS = {"open", "closed", "uninterp", "spec", "proof", "exec", "axiom", "broadcast",
            "const", "unsafe", "async", "default", "extern", "tracked", "ghost"}
CLAUSE_KWS = ("requires", "ensures", "recommends", "decreases", "opens_invariants", "no_unwind",
              "returns", "default_ensures")
BLOCK_OWNERS = {"match", "if", "while", "for", "loop", "unsafe"}


@dataclass
class Item:
    kind: str                 # fn struct enum union type const static trait impl mod use
                              # extern_crate macro broadcast_group broadcast_use
                              # assume_specification global other
    name: str | None
    path: str                 # module path inside the crate ('' = crate root)
    owner: str | None         # impl or trait head, for methods
    start: int                # token index of the first token (first attribute)
    head: int                 # token index of the first token after the attributes
    end: int                  # token index one past the item
    in_verus: bool
    attrs: list = field(default_factory=list)      # [(open '#', close ']')] token indices
    quals: list = field(default_factory=list)
    params: tuple | None = None                    # ('(' index, ')' index)
    ret: tuple | None = None                       # [start, end) token range
    clauses: list = field(default_factory=list)    # [(keyword, start, end)] token ranges
    body: tuple | None = None                      # ('{' index, '}' index)
    children: list = field(default_factory=list)
    mod_decl: bool = False                         # `mod x;`

    @property
    def mode(self):
        if self.kind != "fn":
            return None
        for q in ("spec", "proof", "axiom"):
            if q in self.quals:
                return q
        return "exec"


@dataclass
class Source:
    text: str
    toks: list
    pairs: dict
    items: list               # top-level items (verus! blocks are 'macro' items with children)
    verus_blocks: list        # [(open '{' index, close '}' index)]

    def line_of(self, k):
        return self.toks[k].line if k < len(self.toks) else (self.toks[-1].line if self.toks else 1)

    def text_of(self, a, b):
        """Normalized text of tokens [a, b): one space between tokens."""
        return " ".join(t.text for t in self.toks[a:b])

    def walk(self, items=None):
        """Every item, depth first."""
        for it in (self.items if items is None else items):
            yield it
            yield from self.walk(it.children)

    def fns(self):
        return [it for it in self.walk() if it.kind in ("fn", "assume_specification")]


def parse(text):
    toks = tokenize(text)
    pairs = match_brackets(toks)
    src = Source(text, toks, pairs, [], [])
    src.items = _items(src, 0, len(toks), "", False, None)
    return src


def _attr_end(src, i, end):
    """If an attribute starts at token i, the index of its closing ']'."""
    t = src.toks
    if i < end and t[i].text == "#" and t[i].kind == "punct":
        if i + 1 < end and t[i + 1].text == "[":
            return src.pairs[i + 1]
        if i + 2 < end and t[i + 1].text == "!" and t[i + 2].text == "[":
            return src.pairs[i + 2]
    return None


def _skip_generics(src, i, end):
    t = src.toks
    if i < end and t[i].text == "<":
        depth = 0
        while i < end:
            x = t[i].text
            if x == "<":
                depth += 1
            elif x == ">":
                depth -= 1
            elif x == ">>":
                depth -= 2
            elif x == "<<":
                depth += 2
            elif x in OPEN:
                i = src.pairs[i]
            i += 1
            if depth <= 0:
                break
    return i


def _scan_to(src, i, end, stops=(";", "{")):
    """First index >= i (depth 0, skipping groups) whose token text is in stops."""
    t = src.toks
    while i < end:
        x = t[i].text
        if t[i].kind == "punct" and x in stops:
            return i
        if t[i].kind == "punct" and x in OPEN:
            i = src.pairs[i]
        i += 1
    return end


def _items(src, i, end, path, in_verus, owner):
    t = src.toks
    out = []
    while i < end:
        start = i
        attrs = []
        while (e := _attr_end(src, i, end)) is not None:
            attrs.append((i, e))
            i = e + 1
        if i >= end:
            if attrs:
                out.append(Item("other", None, path, owner, start, start, end, in_verus, attrs))
            break
        head = i
        if t[i].text == ";":
            i += 1
            continue
        if t[i].text == "pub":
            i += 1
            if i < end and t[i].text == "(":
                i = src.pairs[i] + 1
        quals = []
        while i < end and t[i].kind == "id" and t[i].text in FN_QUALS:
            q = t[i].text
            nxt = t[i + 1].text if i + 1 < end else ""
            if q == "const" and nxt != "fn" and nxt not in FN_QUALS:
                break
            if q == "broadcast" and nxt in ("group", "use"):
                break
            if q == "extern" and nxt == "crate":
                break
            if q == "default" and nxt not in FN_QUALS and nxt != "fn":
                break
            quals.append(q)
            i += 1
            if q == "spec" and i < end and t[i].text == "(":     # spec(checked)
                i = src.pairs[i] + 1
            if q == "extern" and i < end and t[i].kind == "lit":  # extern "C"
                i += 1
        if i >= end:
            break
        kw = t[i].text
        it = Item("other", None, path, owner, start, head, end, in_verus, attrs, quals)
        if kw == "fn":
            i = _parse_fn(src, it, i + 1, end)
        elif kw == "assume_specification":
            it.kind = "assume_specification"
            j = _skip_generics(src, i + 1, end)
            if j < end and t[j].text == "[":
                it.name = "assume_specification[" + src.text_of(j + 1, src.pairs[j]).replace(" ", "") + "]"
                j = src.pairs[j] + 1
            i = _parse_sig_tail(src, it, j, end)
        elif kw in ("struct", "enum", "union") and i + 1 < end and t[i + 1].kind == "id":
            it.kind, it.name = kw, t[i + 1].text
            j = _scan_to(src, i + 2, end, (";", "{"))
            it.body = (j, src.pairs[j]) if j < end and t[j].text == "{" else None
            i = (src.pairs[j] if it.body else j) + 1
        elif kw == "trait" and i + 1 < end:
            it.kind, it.name = "trait", t[i + 1].text
            j = _scan_to(src, i + 2, end, ("{", ";"))
            if j < end and t[j].text == "{":
                it.body = (j, src.pairs[j])
                it.children = _items(src, j + 1, src.pairs[j], path, in_verus, it.name)
                i = src.pairs[j] + 1
            else:
                i = j + 1
        elif kw == "impl":
            it.kind = "impl"
            j = _scan_to(src, i + 1, end, ("{", ";"))
            it.name = _impl_owner(src, i + 1, j)
            if j < end and t[j].text == "{":
                it.body = (j, src.pairs[j])
                it.children = _items(src, j + 1, src.pairs[j], path, in_verus, it.name)
                i = src.pairs[j] + 1
            else:
                i = j + 1
        elif kw == "mod" and i + 1 < end and t[i + 1].kind == "id":
            it.kind, it.name = "mod", t[i + 1].text
            j = i + 2
            if j < end and t[j].text == "{":
                it.body = (j, src.pairs[j])
                sub = f"{path}::{it.name}" if path else it.name
                it.children = _items(src, j + 1, src.pairs[j], sub, in_verus, None)
                i = src.pairs[j] + 1
            else:
                it.mod_decl = True
                i = _scan_to(src, j, end, (";",)) + 1
        elif kw == "use":
            it.kind = "use"
            i = _scan_to(src, i + 1, end, (";",)) + 1
        elif kw == "extern" and i + 1 < end and t[i + 1].text == "crate":
            it.kind = "extern_crate"
            it.name = t[i + 2].text if i + 2 < end else None
            i = _scan_to(src, i + 2, end, (";",)) + 1
        elif kw == "broadcast" and i + 1 < end and t[i + 1].text in ("group", "use"):
            if t[i + 1].text == "group":
                it.kind = "broadcast_group"
                it.name = t[i + 2].text if i + 2 < end else None
                j = _scan_to(src, i + 2, end, ("{", ";"))
                if j < end and t[j].text == "{":
                    it.body = (j, src.pairs[j])
                    i = src.pairs[j] + 1
                else:
                    i = j + 1
            else:
                it.kind = "broadcast_use"
                i = _scan_to(src, i + 2, end, (";",)) + 1
        elif kw in ("type", "const", "static") and i + 1 < end:
            it.kind = kw
            k = i + 1
            if t[k].text == "mut":
                k += 1
            it.name = t[k].text
            i = _scan_to(src, k, end, (";",)) + 1
        elif kw == "global":
            it.kind = "global"
            i = _scan_to(src, i + 1, end, (";",)) + 1
        elif t[i].kind == "id" and i + 1 < end and t[i + 1].text == "!":
            it.kind, it.name = "macro", kw
            j = i + 2
            if j < end and t[j].kind == "id":           # macro_rules! name { … }
                j += 1
            if j < end and t[j].text in OPEN:
                close = src.pairs[j]
                if kw == "verus" and t[j].text == "{":
                    it.body = (j, close)
                    src.verus_blocks.append((j, close))
                    it.children = _items(src, j + 1, close, path, True, owner)
                i = close + 1
                if i < end and t[i].text == ";":
                    i += 1
            else:
                i = _scan_to(src, j, end, (";",)) + 1
        else:
            it.kind = "other"
            j = _scan_to(src, i, end, (";", "{"))
            i = (src.pairs[j] if j < end and t[j].text == "{" else j) + 1
        it.end = min(i, end)
        out.append(it)
        i = it.end
    return out


def _impl_owner(src, a, b):
    """'Type' for `impl<…> Type`, '<Type as Trait>' for `impl Trait for Type`."""
    t = src.toks
    a = _skip_generics(src, a, b)
    words = [x for x in t[a:b]]
    for k, x in enumerate(words):
        if x.text == "where":
            words = words[:k]
            break
    for k, x in enumerate(words):
        if x.text == "for" and x.kind == "id":
            trait = "".join(w.text for w in words[:k])
            ty = "".join(w.text for w in words[k + 1:])
            return f"<{ty} as {trait}>"
    return "".join(w.text for w in words)


def _parse_fn(src, it, i, end):
    t = src.toks
    it.kind = "fn"
    if i >= end or t[i].kind != "id":
        it.kind = "other"
        return _scan_to(src, i, end, (";", "{")) + 1
    it.name = t[i].text
    i = _skip_generics(src, i + 1, end)
    if i < end and t[i].text == "(":
        it.params = (i, src.pairs[i])
        i = src.pairs[i] + 1
    return _parse_sig_tail(src, it, i, end)


def _parse_sig_tail(src, it, i, end):
    """From after the parameter list: return type, where, clauses, body or ';'."""
    t = src.toks
    if i < end and t[i].text == "(" and it.params is None:
        it.params = (i, src.pairs[i])
        i = src.pairs[i] + 1
    if i < end and t[i].text == "->":
        a = i + 1
        i = _expr_end(src, a, end, ret=True)
        it.ret = (a, i)
    if i < end and t[i].text == "where":
        i = _expr_end(src, i + 1, end, ret=True)
    while i < end and t[i].kind == "id" and t[i].text in CLAUSE_KWS:
        kw = t[i].text
        a = i + 1
        i = _expr_end(src, a, end)
        it.clauses.append((kw, a, i))
    if i < end and t[i].text == "{":
        it.body = (i, src.pairs[i])
        return src.pairs[i] + 1
    if i < end and t[i].text == ";":
        return i + 1
    return i


def _expr_end(src, i, end, ret=False):
    """End of a return type, where clause or clause expression: the next
    depth-0 clause keyword, body '{' or ';' (see the module docstring)."""
    t = src.toks
    pending = 0
    prev = None
    while i < end:
        x = t[i]
        if x.kind == "id" and x.text in CLAUSE_KWS:
            return i
        if ret and x.kind == "id" and x.text == "where":
            return i
        if x.kind == "punct":
            if x.text == ";":
                return i
            if x.text == "{":
                if not ret and (pending > 0 or (prev is not None and prev.text in ("|", "||", "=>"))):
                    pending = max(0, pending - 1)
                    prev = t[src.pairs[i]]
                    i = src.pairs[i] + 1
                    continue
                return i
            if x.text in "([":
                prev = t[src.pairs[i]]
                i = src.pairs[i] + 1
                continue
            if x.text == ",":
                pending = 0
        elif x.kind == "id" and not ret:
            if x.text in BLOCK_OWNERS:
                pending += 1
            elif x.text == "else" and i + 1 < end and t[i + 1].text == "{":
                pending += 1
        prev = x
        i += 1
    return end


# --- crate structure -----------------------------------------------------------------

def mod_decls(src):
    """[(module path segments, Item)] for every `mod x;` declaration."""
    out = []

    def rec(items, prefix):
        for it in items:
            if it.kind == "mod":
                if it.mod_decl:
                    out.append((prefix + [it.name], it))
                else:
                    rec(it.children, prefix + [it.name])
            elif it.kind == "macro" and it.name == "verus":
                rec(it.children, prefix)
    rec(src.items, [])
    return out


def outside_verus_items(src):
    """Top-level items that are code outside `verus!` (Δ9 V9). Allowed there:
    `use`, `extern crate`, `mod x;`, inner attributes, `#[cfg(test)]` items
    and `#[test]` functions (Δ42: tests sit outside `verus!`), and the
    `verus!` invocation itself."""
    out = []
    for it in src.items:
        if it.kind in ("use", "extern_crate") or (it.kind == "mod" and it.mod_decl):
            continue
        if it.kind == "macro" and it.name == "verus":
            continue
        if it.kind == "other" and it.head >= it.end:      # only attributes (inner ones)
            continue
        if any(_attr_is(src, a, ("cfg(test)", "test")) for a in it.attrs):
            continue
        out.append(it)
    return out


def attr_text(src, a):
    """The attribute's content without `#[`/`#![` and `]`, tokens joined bare."""
    o, c = a
    k = o + 1
    if src.toks[k].text == "!":
        k += 1
    return "".join(x.text for x in src.toks[k + 1:c])


def _attr_is(src, a, names):
    return attr_text(src, a) in names


def broadcast_groups(src):
    """[(module path, group name)] of `broadcast group` items."""
    return [(it.path, it.name) for it in src.walk() if it.kind == "broadcast_group" and it.name]


# --- statement freeze -----------------------------------------------------------------

HASH_DROPPED_ATTRS = re.compile(
    r"^(doc|verifier::external_body|verifier\(external_body\)|verifier::rlimit\(.*\)|"
    r"verifier::spinoff_prover|allow\(.*\)|warn\(.*\)|deny\(.*\)|expect\(.*\)|inline|inline\(.*\)|"
    r"must_use|rustfmt::skip)$|^doc=")


def item_symbol(it):
    base = f"{it.owner}::{it.name}" if it.owner else (it.name or "")
    return f"{it.path}::{base}" if it.path else base


def _norm(toks):
    """Token texts joined by one space, with every trailing comma dropped (a
    `,` at the end, or before a closing bracket: Rust allows both forms)."""
    out = []
    for k, x in enumerate(toks):
        if x.kind == "punct" and x.text == "," and (
                k + 1 == len(toks) or (toks[k + 1].kind == "punct" and toks[k + 1].text in CLOSE)):
            continue
        out.append(x.text)
    return " ".join(out)


def statement_text(src, it):
    """The normalized statement of an item: kept attributes, signature and
    every clause; plus the body of a spec fn, the fields of a struct/enum,
    the whole of a type/const/global/broadcast group/assume_specification."""
    parts = []
    for a in it.attrs:
        if not HASH_DROPPED_ATTRS.search(attr_text(src, a)):
            parts.append("#[" + attr_text(src, a) + "]")
    t = src.toks
    if it.kind in ("fn", "assume_specification"):
        sig_end = it.clauses[0][1] - 1 if it.clauses else (
            it.body[0] if it.body else it.end)
        parts.append(_norm(t[it.head:sig_end]))
        for kw, a, b in it.clauses:
            parts.append(kw + " " + _norm(t[a:b]))
        if it.mode == "spec" and it.body:
            parts.append(_norm(t[it.body[0]:it.body[1] + 1]))
        elif not it.body:
            parts.append(";")
    else:
        parts.append(_norm(t[it.head:it.end]))
    return "\n".join(parts)


FROZEN_KINDS = ("fn", "assume_specification", "struct", "enum", "union", "type", "const",
                "static", "global", "broadcast_group")


def statements(src, file=None):
    """[(symbol, sha256, line, kind)] for every frozen-kind item in `verus!`."""
    out, seen = [], {}
    for it in src.walk():
        if it.kind not in FROZEN_KINDS or not it.in_verus:
            continue
        sym = item_symbol(it) if it.kind != "global" else f"global@{src.line_of(it.head)}"
        if it.kind == "broadcast_group":
            sym = f"{it.path + '::' if it.path else ''}group {it.name}"
        n = seen.get(sym, 0) + 1
        seen[sym] = n
        if n > 1:
            sym = f"{sym}#{n}"
        digest = hashlib.sha256(statement_text(src, it).encode()).hexdigest()
        out.append((sym, digest, src.line_of(it.head), it.kind))
    return out


# An ADDED MEASURE (DV3b kits; Δ160's first Open item, a Q08 Dafny exit): a
# `decreases` clause on a fn that shipped without one is a termination
# argument, part of the proof rather than of what the fn states; a wrong
# measure fails verification, and no measure weakens a statement. The freeze
# and the twin comparison judge a changed statement a second time with the
# candidate's measures blanked, so an added measure passes and a shipped one
# stays frozen (blanked, the candidate no longer matches a statement that
# holds it). A clause that holds `when` or `via` is never blanked: `when`
# narrows a spec fn's definition.
MEASURE_KEEP = ("when", "via")


def measure_free_text(text):
    """`text` with the header `decreases` clause of every fn inside `verus!`
    blanked (layout and line numbers kept), except one that holds `when` or
    `via` (MEASURE_KEEP). Raises ParseError as parse() does."""
    src = parse(text)
    spans = []
    for it in src.walk():
        if it.kind != "fn" or not it.in_verus:
            continue
        for kw, a, b in it.clauses:
            if kw != "decreases" or b <= a or any(
                    x.kind == "id" and x.text in MEASURE_KEEP for x in src.toks[a:b]):
                continue
            spans.append((src.toks[a - 1].start, src.toks[b - 1].end))
    return blank_spans(text, spans)


def blank_spans(text, spans):
    """`text` with each character span [start, end) replaced by spaces, its
    newlines kept."""
    out = text
    for s, e in sorted(spans, reverse=True):
        out = out[:s] + "".join(c if c == "\n" else " " for c in out[s:e]) + out[e:]
    return out


# --- body rewrites (empty-body gate, Δ47) --------------------------------------------

LOOP_CLAUSES = ("invariant", "invariant_except_break", "invariant_ensures", "ensures", "decreases")


def find_fn(src, symbol):
    """The fn item for a symbol: exact symbol, else a unique name match."""
    fns = [it for it in src.walk() if it.kind == "fn" and it.in_verus]
    exact = [it for it in fns if item_symbol(it) == symbol]
    if exact:
        return exact[0]
    by_name = [it for it in fns if it.name == symbol or item_symbol(it).endswith("::" + symbol)]
    return by_name[0] if len(by_name) == 1 else None


# Statements that are block-like expressions: in statement position (Rust's
# ExpressionWithBlock) they end at the brace that closes them, with no `;`,
# unless an `else` continues an `if`. The empty-body gate's proof-span walk
# relies on this to see a `proof { }` block that directly follows one as a
# statement of its own (QPLAN §6 Q9: E0/E0H/E1 kept such a block after
# stripping the ghost lets it uses).
BLOCK_LIKE = ("if", "match", "while", "loop", "for", "unsafe")


def _stmt_end(src, i, end):
    """End (exclusive) of the statement starting at i inside a block. A
    block-like statement (if/else, match, a loop, `unsafe`, a plain block)
    ends at the brace that closes it, so what follows (a `proof { }` block, a
    call) is the next statement."""
    t = src.toks
    saw_by = False
    first = t[i] if i < end else None
    block_like = first is not None and (
        (first.kind == "id" and first.text in BLOCK_LIKE)
        or (first.kind == "punct" and first.text == "{"))
    while i < end:
        x = t[i]
        if x.kind == "id" and x.text == "by":
            saw_by = True
        if x.kind == "punct":
            if x.text == ";":
                return i + 1
            if x.text == "{":
                close = src.pairs[i]
                j = close + 1
                if saw_by or (i > 0 and t[i - 1].text in ("proof",)):
                    return j + 1 if j < end and t[j].text == ";" else j
                if block_like and not (j < end and t[j].kind == "id" and t[j].text == "else"):
                    return j + 1 if j < end and t[j].text == ";" else j
                i = j
                continue
            if x.text in "([":
                i = src.pairs[i] + 1
                continue
        i += 1
    return end


def proof_spans(src, a, b, invariants=True, proof=True, keep_tracked=False):
    """Character spans to delete inside the block tokens [a, b) (exclusive of
    the braces): proof text (statements) and/or loop invariant clauses,
    recursively through nested blocks. keep_tracked keeps the `let tracked`
    statements (exec code consumes their values, `Tracked(perm)`; QPLAN §30
    Q65(b)); one inside a stripped `proof { }` block goes with the block."""
    t = src.toks
    spans = []
    i = a
    while i < b:
        stmt_start = i
        while (e := _attr_end(src, i, b)) is not None:
            i = e + 1
        if i >= b:
            break
        x = t[i]
        nxt = t[i + 1].text if i + 1 < b else ""
        is_proof = proof and x.kind == "id" and (
            (x.text == "proof" and nxt == "{")
            or x.text in ("assert", "assume", "admit", "reveal", "reveal_with_fuel", "hide")
            or (x.text == "let" and nxt in ("ghost", "tracked")
                and not (keep_tracked and nxt == "tracked"))
            or (x.text == "broadcast" and nxt == "use"))
        if is_proof:
            e = _stmt_end(src, i, b)
            spans.append((t[stmt_start].start, t[e - 1].end))
            i = e
            continue
        if x.kind == "id" and x.text in ("while", "loop", "for"):
            j = i + 1
            # loop head up to its clauses / body
            while j < b and not (t[j].kind == "id" and t[j].text in LOOP_CLAUSES) and t[j].text != "{":
                if t[j].text in "([":
                    j = src.pairs[j]
                j += 1
            while j < b and t[j].kind == "id" and t[j].text in LOOP_CLAUSES:
                kw = t[j].text
                k = _expr_end_loop(src, j + 1, b)
                if invariants and kw in ("invariant", "invariant_except_break", "invariant_ensures"):
                    spans.append((t[j].start, t[k - 1].end if k > j + 1 else t[j].end))
                j = k
            if j < b and t[j].text == "{":
                spans += proof_spans(src, j + 1, src.pairs[j], invariants, proof, keep_tracked)
                i = src.pairs[j] + 1
                continue
            i = j
            continue
        # walk into nested blocks of an ordinary statement (if/else/match/blocks)
        e = _stmt_end(src, i, b)
        k = i
        while k < e:
            if t[k].text == "{" and t[k].kind == "punct":
                spans += proof_spans(src, k + 1, src.pairs[k], invariants, proof, keep_tracked)
                k = src.pairs[k] + 1
                continue
            if t[k].text in "([" and t[k].kind == "punct":
                k = src.pairs[k] + 1
                continue
            k += 1
        i = e
    return spans


def _expr_end_loop(src, i, end):
    t = src.toks
    while i < end:
        x = t[i]
        if x.kind == "id" and x.text in LOOP_CLAUSES:
            return i
        if x.kind == "punct" and x.text == "{":
            return i
        if x.kind == "punct" and x.text in "([":
            i = src.pairs[i] + 1
            continue
        i += 1
    return end


def apply_spans(text, spans):
    """Delete character spans (sorted, non-overlapping after merge)."""
    out, pos = [], 0
    for a, b in sorted(spans):
        if a < pos:
            a = pos
        if b <= a:
            continue
        out.append(text[pos:a])
        pos = b
    out.append(text[pos:])
    return "".join(out)


def clause_exprs(src, it, kw):
    """The comma-separated expressions of every `kw` clause of a fn, each as
    its original source text (comments inside it included)."""
    exprs = []
    t = src.toks
    for k, a, b in it.clauses:
        if k != kw:
            continue
        first, i = None, a
        while i <= b:
            if i == b or (t[i].kind == "punct" and t[i].text == ","):
                if first is not None:
                    exprs.append(src.text[t[first].start:t[i - 1].end])
                first = None
                i += 1
                continue
            if first is None:
                first = i
            if t[i].kind == "punct" and t[i].text in OPEN:
                i = src.pairs[i]
            i += 1
    return exprs


def module_insert_point(src, it):
    """Character offset at which a module-level item can be inserted just
    before `it` (before its enclosing impl/trait when it is a method)."""
    if it.owner is not None:
        for p in src.walk():
            if p.kind in ("impl", "trait") and p.body and p.body[0] < it.start < p.body[1]:
                return src.toks[p.start].start
    return src.toks[it.start].start
