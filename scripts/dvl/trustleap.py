#!/usr/bin/env python3
"""dvl.trustleap — the challenge gate's trust-leap lint (QPLAN §31.1 item 4; spec
§2.3.8 items 4-5; DELTAS Δ402).

A trust leap is a construct whose claim the verifier does not check: a body or a
contract taken on trust, or code outside what is verified. vaudit already reports
the leaps that are holes; this lint lists every leap of a challenge's files,
holes or not, and diffs them BOTH WAYS against the module's table in the
learner's `TRUST.md` (design item 5: escape hatches only where TRUST.md lists
them): a leap with no entry is a finding, and so is an entry that matches no
leap, or an entry with no reason.

Leap constructs (one name each; the table's `construct` column uses them):

  Dafny   extern            an {:extern} attribute
          axiom             an {:axiom} attribute (a lemma or function taken as true)
          assume-axiom      `assume {:axiom} …`
          decreases-star    `decreases *` (partial correctness only)
          verify-false      {:verify false}
  Verus   external-body     #[verifier::external_body]
          external          #[verifier::external]
          external-fn-spec  #[verifier::external_fn_specification]
          external-type     #[verifier::external_type_specification]
          assume-spec       assume_specification
          truncate          #[verifier::truncate] (an unchecked cast)
          no-decreases      #[verifier::exec_allows_no_decreases_clause]
          unsafe            an `unsafe` block, fn or impl
          outside-verus     a `fn` outside every `verus! { … }` block (V9)

Each leap is attributed to the declaration it belongs to: the first declaration
name at or after the leap (an attribute precedes its item), or for a leap inside
a body the enclosing declaration's name. Comments and string and character
literals are blanked before scanning, so a leap named in prose is not a leap.

The TRUST.md table: under a heading whose text is the module id (`## Q31`, any
level from ## to ####), a Markdown table whose header names the columns
`file`, `symbol`, `construct` and `why` (any order, other columns ignored); the
table ends at the next heading of the same or a higher level. `file` is the
repo-relative path.

  scan(paths, root) -> list[Leap]
  read_trust(path, module) -> list[Entry]      TrustError on a malformed table
  diff(leaps, entries) -> list[str]            the findings, [] = clean

CLI (prints locations and construct names, never file content):
  python3 scripts/dvl/trustleap.py scan [--root R] FILE...
  python3 scripts/dvl/trustleap.py check --module ID --trust TRUST.md [--root R] FILE...
Exit: 0 clean · 1 findings · 2 usage · 3 a table that cannot be read.
Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

__all__ = ["DAFNY_LEAPS", "VERUS_LEAPS", "Entry", "Leap", "TrustError", "blank", "diff",
           "read_trust", "scan", "scan_text"]

DAFNY_LEAPS = ("extern", "axiom", "assume-axiom", "decreases-star", "verify-false")
VERUS_LEAPS = ("external-body", "external", "external-fn-spec", "external-type", "assume-spec",
               "truncate", "no-decreases", "unsafe", "outside-verus")

_DAFNY_RX = [
    ("assume-axiom", re.compile(r"\bassume\s*\{:\s*axiom\s*\}")),
    ("extern", re.compile(r"\{:\s*extern\b")),
    ("axiom", re.compile(r"(?<!assume )\{:\s*axiom\s*\}")),
    ("decreases-star", re.compile(r"\bdecreases\s*\*")),
    ("verify-false", re.compile(r"\{:\s*verify\s+false\s*\}")),
]
_VERUS_RX = [
    ("external-body", re.compile(r"#\[\s*verifier::external_body\s*\]")),
    ("external-fn-spec", re.compile(r"#\[\s*verifier::external_fn_specification\s*\]")),
    ("external-type", re.compile(r"#\[\s*verifier::external_type_specification\s*\]")),
    ("external", re.compile(r"#\[\s*verifier::external\s*\]")),
    ("assume-spec", re.compile(r"\bassume_specification\b")),
    ("truncate", re.compile(r"#\[\s*verifier::truncate\s*\]")),
    ("no-decreases", re.compile(r"#\[\s*verifier::exec_allows_no_decreases_clause\s*\]")),
    ("unsafe", re.compile(r"\bunsafe\b")),
]
_DAFNY_DECL = re.compile(
    r"\b(?:method|function|lemma|predicate|constructor|class|trait|datatype|codatatype|"
    r"newtype|type|const|iterator|module)\b(?:\s+method)?(?:\s*\{[^}]*\})*\s+([A-Za-z_][\w']*)")
_VERUS_DECL = re.compile(
    r"\b(?:fn|struct|enum|type|trait|const|static|mod)\s+([A-Za-z_]\w*)|\bimpl\b[^{;]*?([A-Za-z_]\w*)\s*(?:<[^{;]*>)?\s*\{")
_VERUS_FN = re.compile(r"\bfn\s+([A-Za-z_]\w*)")


class TrustError(Exception):
    """A TRUST.md table that cannot be read."""


@dataclass(frozen=True, order=True)
class Leap:
    file: str
    line: int
    construct: str
    symbol: str


@dataclass(frozen=True)
class Entry:
    file: str
    symbol: str
    construct: str
    why: str
    line: int          # the table row's line in TRUST.md


def lang_of(path) -> str | None:
    s = str(path)
    if s.endswith(".dfy"):
        return "dafny"
    if s.endswith(".rs"):
        return "verus"
    return None


def blank(text: str, lang: str) -> str:
    """text with comments and string and character literals replaced by spaces
    (newlines kept, so line numbers and offsets stay). Block comments nest, as in
    both languages."""
    out, i, n = list(text), 0, len(text)

    def wipe(a, b):
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "
    while i < n:
        c = text[i]
        if text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            wipe(i, j)
            i = j
        elif text.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if text.startswith("/*", j):
                    depth, j = depth + 1, j + 2
                elif text.startswith("*/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            wipe(i, j)
            i = j
        elif lang == "verus" and re.match(r'r(#*)"', text[i:i + 8]) and \
                (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")):
            m = re.match(r'r(#*)"', text[i:])
            close = '"' + m.group(1)
            j = text.find(close, i + len(m.group(0)))
            j = n if j < 0 else j + len(close)
            wipe(i, j)
            i = j
        elif c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            wipe(i, min(j + 1, n))
            i = j + 1
        elif c == "'":
            m = re.match(r"'(?:\\[^']{1,10}|[^\\'\n])'", text[i:])
            if m:
                wipe(i, i + len(m.group(0)))
                i += len(m.group(0))
            else:
                i += 1      # a Rust lifetime, or a Dafny primed name
        else:
            i += 1
    return "".join(out)


def _line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def _verus_spans(b):
    """[(start, end)] offsets of every `verus! { … }` block's braces in blanked text."""
    spans = []
    for m in re.finditer(r"\bverus!\s*\{", b):
        depth, j = 1, m.end()
        while j < len(b) and depth:
            depth += {"{": 1, "}": -1}.get(b[j], 0)
            j += 1
        spans.append((m.start(), j))
    return spans


def _decl_after(b, pos, rx):
    m = rx.search(b, pos)
    return (m.group(1) or (m.group(2) if m.lastindex and m.lastindex >= 2 else None)) if m else None


def _decl_before(b, pos, rx):
    last = None
    for m in rx.finditer(b, 0, pos):
        last = m.group(1) or (m.group(2) if m.lastindex and m.lastindex >= 2 else None)
    return last


_DAFNY_KEYWORDS = {"method", "function", "lemma", "predicate", "constructor", "class", "trait",
                   "datatype", "codatatype", "newtype", "type", "const", "iterator", "module",
                   "ghost", "static", "twostate", "least", "greatest", "opaque", "abstract",
                   "export", "import", "opened", "var"}


def _dafny_name_after_attr(b, pos):
    """The declaration name an attribute at pos belongs to: after the attribute
    (and any further attributes and declaration keywords), the first name."""
    j, n = pos, len(b)
    while j < n:
        while j < n and b[j].isspace():
            j += 1
        if b.startswith("{:", j):
            depth = 0
            while j < n:
                depth += {"{": 1, "}": -1}.get(b[j], 0)
                j += 1
                if depth == 0:
                    break
            continue
        m = re.compile(r"[A-Za-z_][\w'?]*").match(b, j)
        if not m:
            return None
        if m.group(0) in _DAFNY_KEYWORDS:
            j = m.end()
            continue
        return m.group(0)
    return None


_VERUS_ITEM_HEAD = re.compile(
    r"(?:\s*#\[[^\]]*\])*\s*(?:pub(?:\([^)]*\))?\s+)?(?:(?:open|closed|uninterp|proof|exec|spec|"
    r"const|unsafe|broadcast|tracked|ghost)\s+)*(?:fn|struct|enum|type|trait|impl|const|static|mod)\b")


def _verus_attr_symbol(b, start, end):
    """An item attribute names the item after it; an expression or statement
    attribute (a cast's truncate) names the enclosing item."""
    if _VERUS_ITEM_HEAD.match(b, end):
        return _decl_after(b, end, _VERUS_DECL)
    return _decl_before(b, start, _VERUS_DECL)


def scan_text(text: str, lang: str, rel: str) -> list[Leap]:
    b = blank(text, lang)
    out = []
    if lang == "dafny":
        seen = set()
        for name, rx in _DAFNY_RX:
            for m in rx.finditer(b):
                if name == "axiom" and re.search(r"assume\s*$", b[max(0, m.start() - 12):m.start()]):
                    continue
                if (m.start(), name) in seen:
                    continue
                seen.add((m.start(), name))
                if name in ("assume-axiom", "decreases-star"):
                    sym = _decl_before(b, m.start(), _DAFNY_DECL)
                else:
                    sym = _dafny_name_after_attr(b, m.start())
                out.append(Leap(rel, _line_of(b, m.start()), name, sym or "?"))
    elif lang == "verus":
        for name, rx in _VERUS_RX:
            for m in rx.finditer(b):
                if name == "external" and b.startswith("_", m.start() + len("#[verifier::external")):
                    continue
                if name == "unsafe" or name == "assume-spec":
                    sym = _decl_before(b, m.start(), _VERUS_DECL) if name == "unsafe" else None
                    if name == "assume-spec":
                        mm = re.compile(r"assume_specification\s*(?:<[^>]*>)?\s*\[\s*([^\]]+?)\s*\]").match(b, m.start())
                        sym = re.sub(r"\s+", "", mm.group(1)) if mm else None
                    nxt = _decl_after(b, m.end(), _VERUS_DECL)
                    if name == "unsafe" and re.match(r"\s*(fn|impl|trait)\b", b[m.end():]):
                        sym = nxt
                else:
                    sym = _verus_attr_symbol(b, m.start(), m.end())
                out.append(Leap(rel, _line_of(b, m.start()), name, sym or "?"))
        spans = _verus_spans(b)
        for m in _VERUS_FN.finditer(b):
            if not any(a <= m.start() < z for a, z in spans):
                depth = b.count("{", 0, m.start()) - b.count("}", 0, m.start())
                if depth == 0 or not spans:
                    out.append(Leap(rel, _line_of(b, m.start()), "outside-verus", m.group(1)))
    return sorted(set(out))


def scan(paths, root=None) -> list[Leap]:
    root = Path(root or ".").resolve()
    out = []
    for raw in paths:
        p = Path(raw)
        p = p if p.is_absolute() else root / p
        lang = lang_of(p)
        if lang is None:
            continue
        try:
            rel = p.resolve().relative_to(root).as_posix()
        except ValueError:
            rel = str(p)
        out += scan_text(p.read_text(encoding="utf-8"), lang, rel)
    return sorted(out)


_HEADING = re.compile(r"^(#{2,4})\s+(.*?)\s*$")


def read_trust(path, module: str) -> list[Entry]:
    """The module's entries in TRUST.md ([] when it has no section for it)."""
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    level, start = None, None
    for k, line in enumerate(lines):
        h = _HEADING.match(line)
        if h and re.fullmatch(rf"{re.escape(module)}\b.*", h.group(2)):
            level, start = len(h.group(1)), k + 1
            break
    if start is None:
        return []
    cols, out = None, []
    for k in range(start, len(lines)):
        line = lines[k]
        h = _HEADING.match(line)
        if h and len(h.group(1)) <= level:
            break
        if not line.strip().startswith("|"):
            if cols is not None and line.strip():
                cols = None if not out else cols
            continue
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if cols is None:
            names = [c.lower() for c in cells]
            if {"file", "symbol", "construct", "why"} <= set(names):
                cols = {c: names.index(c) for c in ("file", "symbol", "construct", "why")}
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if len(cells) <= max(cols.values()):
            raise TrustError(f"{path}:{k + 1}: a row with {len(cells)} cells; the table has "
                             f"{max(cols.values()) + 1} or more")
        e = Entry(cells[cols["file"]], cells[cols["symbol"]], cells[cols["construct"]],
                  cells[cols["why"]], k + 1)
        if e.construct not in DAFNY_LEAPS + VERUS_LEAPS:
            raise TrustError(f"{path}:{k + 1}: construct {e.construct!r} is not a leap name "
                             "(dvl.trustleap's list)")
        out.append(e)
    return out


def diff(leaps, entries) -> list[str]:
    """Both directions: every leap needs an entry with a reason; every entry a leap."""
    out = []
    keys = {(e.file, e.symbol, e.construct): e for e in entries}
    used = set()
    for lp in leaps:
        k = (lp.file, lp.symbol, lp.construct)
        e = keys.get(k)
        if e is None:
            out.append(f"{lp.file}:{lp.line}: {lp.construct} on {lp.symbol} is not listed in "
                       "TRUST.md (an escape hatch only where TRUST.md lists it)")
            continue
        used.add(k)
        if not e.why.strip() or e.why.strip() in ("-", "—", "TODO"):
            out.append(f"{lp.file}:{lp.line}: {lp.construct} on {lp.symbol}: its TRUST.md row "
                       f"(line {e.line}) gives no reason")
    for k, e in keys.items():
        if k not in used:
            out.append(f"TRUST.md:{e.line}: {e.construct} on {e.symbol} in {e.file} matches no "
                       "leap in the files (a stale entry)")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="dvl/trustleap.py", allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--root", default=".")
    s.add_argument("files", nargs="+")
    c = sub.add_parser("check")
    c.add_argument("--root", default=".")
    c.add_argument("--module", required=True)
    c.add_argument("--trust", required=True)
    c.add_argument("files", nargs="+")
    a = ap.parse_args(argv)
    leaps = scan(a.files, a.root)
    if a.cmd == "scan":
        for lp in leaps:
            print(f"{lp.file}:{lp.line}: {lp.construct} {lp.symbol}")
        return 0
    try:
        entries = read_trust(a.trust, a.module)
    except (TrustError, OSError) as e:
        print(f"trustleap: {e}", file=sys.stderr)
        return 3
    found = diff(leaps, entries)
    for f in found:
        print(f)
    print(f"trustleap: {len(leaps)} leap(s), {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}, "
          f"{len(found)} finding(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
