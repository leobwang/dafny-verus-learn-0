"""dvl.dafny — the pinned Dafny wrapper library (phase DV1b).

The interface (shared with dvl.verus; types in dvl.common):

  verify(target, gate=False, symbol=None, seed=None, isolate=False, extra_args=(),
         solver=None) -> Result
  holes(target) -> list[Hole]
  audit(target, lint_mode="learner", given_role=False) -> list[Finding]
  lint(paths, mode, context=(), given_role=False) -> list[Finding]
                                                   mode: learner | reference | agent | given
  spec_hash(path, symbols=None) -> dict[symbol, sha256]
  freeze_check(frozen, candidate) -> list[Finding]
  test(target, names=None) -> Result
  empty_body(target, item_symbol, regions=False) -> Result

plus check_args(args, gate) (the refusal list for command-line pass-through),
program(target) (what a target resolves to), count_unit(result) (what a run's
verified_count counts, Δ39), server_argv() (Δ33), and solver_names() /
solver_path(name) (QPLAN §6 Q29: the Z3 binaries bundled with the pinned
Dafny, pinned by name and sha256 in pins.toml [dafny.solvers]; the first is
the pinned solver).

Targets (DELTAS Δ10, Δ27, Δ28). Every Dafny run names its inputs explicitly;
the wrapper never relies on --find-project or on Dafny's own project discovery.
  - a unit's `dfyconfig.toml`, or its directory, or a `.dfy` file directly in a
    directory holding a `dfyconfig.toml`: the unit's project, passed by path.
    Its keys are checked (only `includes` and `[options]` with the allowed unit
    knobs, Δ30, Δ78), every `includes` glob must match a file (Δ27), and inside
    a course tree it must equal scripts/gen_units.py's output: an unknown or
    edited project file is refused.
  - any other `.dfy` file (exit, agent and check files, scratch probes): the file
    plus, inside a course tree, the given layers of its module's chain, with the
    unit options of its module and tier (from dafny/options/<tier>.toml) passed
    on the command line. The tier is the file's `[module.imports]` entry (std-all
    builds as std; QPLAN §6 Q13); an undeclared file is std when it imports Std
    or a std-tier given layer (file_tier). Outside a course tree: the file alone.
  - a `*.dfy.specimen`: copied to scratch with its real extension and verified
    alone (spec §3.8.6; specimens are self-contained).

Pinned flags (from scripts/dvl/pins.toml, the one source): every verifying run
passes --resource-limit <pin> --cores <pin> --solver-path <bundled z3-4.12.1>
--allow-axioms false; the gate adds --allow-warnings false, the learner loop
--allow-warnings. A learner-loop run may name another bundled solver
(verify(solver=<name>), QPLAN §6 Q29: a brittleness measurement): its path
comes from the pins and its sha256 is checked before the run; the gate
refuses it (Δ10). Command-line values beat project [options], `base` chains and
a project solver-path (Δ10), and the project keys that could poison a run are
refused before any run. Every job runs through dvl.common.run_capped (memory
cap, concurrency slots, scrubbed environment, wall-clock safety kill), from a
scratch working directory; every compile runs in a scratch copy (Δ32).

Output channels: `verify`/`measure-complexity` use --json-output (Δ36: JSON
Lines; `{0}` templates filled from `arguments`; the absolute `uri` gives the
file, mapped back from scratch copies) plus a CSV task log for per-symbol
status; `resolve`, `audit` and `test` are parsed as text with snippets off.
Holes are counted from the exact pinned wordings W-D01, W-D02, W-D03 only,
deduplicated by position (Δ1, Δ5); silent hole kinds come from the lint (Δ3).

Static functions (lint, spec_hash, the parser) never run a tool.
"""

from __future__ import annotations

import csv
import glob as globmod
import functools
import hashlib
import json
import os
import re
import shutil
import sys
import tomllib
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from . import common
from .common import Diag, DvlError, Finding, Hole, Result

if str(common.SCRIPTS) not in sys.path:
    sys.path.insert(0, str(common.SCRIPTS))
import course_items as ci  # noqa: E402  (the ONE item parser, Δ71)
import gen_units as gu  # noqa: E402  (unit options and layer chains, Δ78)

LANG = "dafny"
HOLE_CODES = {"W-D01": "bodyless-method", "W-D02": "bodyless-function", "W-D03": "assume"}
MODES = ("learner", "reference", "agent", "given")


class Refused(DvlError):
    """The wrapper refuses this target or option (no tool runs)."""


class HoleCountError(DvlError):
    """holes() could not count: the program does not resolve. `.result` holds
    the run."""

    def __init__(self, message, result):
        super().__init__(message)
        self.result = result


@functools.lru_cache(maxsize=1)
def pins():
    """The [dafny] pins (read once per process; treat as read-only)."""
    return common.load_pins()["dafny"]


# =====================================================================================
# Source analysis: a small Dafny tokenizer and declaration parser (static; no tool)
# =====================================================================================

@dataclass(frozen=True)
class Tok:
    kind: str     # id | num | str | char | op
    text: str
    line: int     # 1-based
    col: int      # 1-based
    start: int    # offsets into the text
    end: int
    glued: bool   # no whitespace or comment before it


OPS = sorted(["<==>", "==>", "<==", "-->", "...", "~>", "!!", "==", "!=", "<=", ">=", "&&",
              "||", "::", ":=", ":-", ":|", "..", "=>", "->", "<-"], key=len, reverse=True)
ID_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_'?]*")
NUM_RE = re.compile(r"0x[0-9A-Fa-f_]+|[0-9][0-9_]*(?:\.[0-9][0-9_]*)?")
STR_RE = re.compile(r'"(?:\\.|[^"\\\n])*"')
VSTR_RE = re.compile(r'@"(?:[^"]|"")*"')
CHAR_RE = re.compile(r"'(?:\\(?:u\{[0-9A-Fa-f]{1,6}\}|U\{[0-9A-Fa-f]{1,6}\}|x[0-9A-Fa-f]{2}|"
                     r"u[0-9A-Fa-f]{4}|.)|[^'\\\n])'")


def tokenize(text):
    """Tokens of Dafny source, comments dropped (nested block comments)."""
    toks = []
    i, n, line, lstart, glued = 0, len(text), 1, 0, False

    def add(kind, j):
        nonlocal i, line, lstart, glued
        s = text[i:j]
        toks.append(Tok(kind, s, line, i - lstart + 1, i, j, glued))
        nl = s.count("\n")
        if nl:
            line += nl
            lstart = i + s.rindex("\n") + 1
        i, glued = j, True

    while i < n:
        c = text[i]
        if c == "\n":
            line, lstart, i, glued = line + 1, i + 1, i + 1, False
            continue
        if c in " \t\r\f\v":
            i, glued = i + 1, False
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            i, glued = (n if j < 0 else j), False
            continue
        if text.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if text.startswith("/*", j):
                    depth, j = depth + 1, j + 2
                elif text.startswith("*/", j):
                    depth, j = depth - 1, j + 2
                else:
                    if text[j] == "\n":
                        line, lstart = line + 1, j + 1
                    j += 1
            i, glued = j, False
            continue
        if m := VSTR_RE.match(text, i):
            add("str", m.end())
        elif m := STR_RE.match(text, i):
            add("str", m.end())
        elif c == "'" and (m := CHAR_RE.match(text, i)):
            add("char", m.end())
        elif m := ID_RE.match(text, i):
            add("id", m.end())
        elif m := NUM_RE.match(text, i):
            add("num", m.end())
        else:
            op = next((o for o in OPS if text.startswith(o, i)), c)
            add("op", i + len(op))
    return toks


@dataclass
class Attr:
    name: str
    style: str          # "{:" or "@"
    args: str           # the argument tokens, space-joined
    line: int
    start: int          # token index of `{` or `@`
    end: int            # token index one past the attribute


@dataclass
class Decl:
    kind: str           # lemma method function predicate constructor iterator const var
                        # datatype codatatype newtype type class trait
    name: str
    qual: str           # Module.[Class.]Name ("Name" in the default module)
    container: str      # qualified name of the enclosing module/class ("" at top level)
    container_kind: str  # top | module | abstract-module | class | trait | datatype | newtype | type
    modifiers: list
    attrs: list         # attributes on the declaration (before or after the keyword)
    header_attrs: list  # attributes inside the header (clauses)
    start: int          # token index of the first modifier or attribute
    kw: int             # token index of the keyword
    header_end: int     # token index one past the header
    body: tuple | None  # (open, close) token indices of the body braces
    by_method: tuple | None
    clauses: list       # [(keyword, token index)]
    line: int
    end_line: int
    has_value: bool = False

    @property
    def ensures(self):
        return sum(1 for k, _ in self.clauses if k == "ensures")


@dataclass
class ModuleDecl:
    name: str
    qual: str
    abstract: bool
    refines: str | None
    line: int
    end_line: int
    open: int
    close: int


@dataclass
class Source:
    path: str
    text: str
    toks: list
    modules: list = field(default_factory=list)
    decls: list = field(default_factory=list)
    includes: list = field(default_factory=list)     # [line]
    imports: list = field(default_factory=list)      # [(line, qualified name)]
    import_decls: list = field(default_factory=list)  # [(line, module qual, statement text)]
    attrs: list = field(default_factory=list)        # every attribute in the file
    export_decls: list = field(default_factory=list)  # (line, module qual, token text)

    def decl(self, symbol):
        """The declaration named `symbol` (qualified, or a unique suffix after a dot)."""
        exact = [d for d in self.decls if d.qual == symbol]
        if exact:
            return exact[0]
        tail = [d for d in self.decls if d.qual.endswith("." + symbol) or d.qual == symbol]
        return tail[0] if len(tail) == 1 else None


MODIFIERS = {"ghost", "static", "opaque", "abstract", "replaceable", "twostate", "least",
             "greatest", "inductive", "protected", "private"}
METHODLIKE = {"lemma", "method", "function", "predicate", "constructor", "iterator",
              "colemma", "copredicate"}
TYPEDECL = {"datatype", "codatatype", "newtype", "type"}
CLASSLIKE = {"class", "trait"}
DECL_KW = METHODLIKE | TYPEDECL | CLASSLIKE | {"const", "var", "module", "import", "export",
                                                "include"}
CLAUSE_KW = {"requires", "ensures", "decreases", "reads", "modifies", "invariant", "yield"}
# A `{` right after one of these opens an expression (a set display), not a body.
EXPR_PREV = {"==", "!=", "<", "<=", ">=", "+", "-", "/", "%", "&&", "||", "==>", "<==", "<==>",
             "!", "!!", "in", "::", ":=", ":|", ":-", "(", "[", ",", "=>", "then", "else", "&",
             "^", "multiset", "set", "iset", "map", "imap", "requires", "ensures", "decreases",
             "reads", "modifies", "invariant", "returns", "=", "<-", "-->", "~>", "->", "#"}
AMBIGUOUS_PREV = {">", "|", "*"}   # decided by what follows the matching `}`


class _Parser:
    def __init__(self, path, text):
        self.src = Source(path, text, tokenize(text))
        self.t = self.src.toks
        self.n = len(self.t)
        self.partner = self._pairs()

    def _pairs(self):
        partner, stack = [-1] * self.n, []
        for k, tok in enumerate(self.t):
            if tok.kind != "op":
                continue
            if tok.text == "{":
                stack.append(k)
            elif tok.text == "}" and stack:
                o = stack.pop()
                partner[o], partner[k] = k, o
        return partner

    def text(self, k):
        return self.t[k].text if 0 <= k < self.n else ""

    # --- attributes -----------------------------------------------------------------
    def is_curly_attr(self, k):
        return self.text(k) == "{" and self.text(k + 1) == ":" and self.t[k + 1].glued

    def is_at_attr(self, k):
        if self.text(k) != "@" or k + 1 >= self.n or self.t[k + 1].kind != "id" \
                or not self.t[k + 1].glued:
            return False
        # old@L(x), unchanged@L, fresh@L: a label, glued to the identifier before it
        return not (k > 0 and self.t[k].glued and self.t[k - 1].kind == "id")

    def read_attr(self, k):
        if self.is_curly_attr(k):
            close = self.partner[k]
            if close < 0:
                close = self.n - 1
            name = self.text(k + 2)
            args = " ".join(x.text for x in self.t[k + 3:close])
            a = Attr(name, "{:", args, self.t[k].line, k, close + 1)
        else:
            name, end = self.text(k + 1), k + 2
            if self.text(end) == "(" and self.t[end].glued:
                depth = 0
                for j in range(end, self.n):
                    if self.text(j) == "(":
                        depth += 1
                    elif self.text(j) == ")":
                        depth -= 1
                        if depth == 0:
                            end = j + 1
                            break
            args = " ".join(x.text for x in self.t[k + 2:end])
            a = Attr(name, "@", args, self.t[k].line, k, end)
        self.src.attrs.append(a)
        return a

    def attr_at(self, k):
        return self.is_curly_attr(k) or self.is_at_attr(k)

    # --- member starts ----------------------------------------------------------------
    def member_start(self, k, in_header=False):
        if k >= self.n:
            return True
        x = self.text(k)
        if self.t[k].kind == "id" and (x in MODIFIERS or x in DECL_KW):
            return not (in_header and x == "var")   # `var` in a clause is a let
        if x == "}":
            return True
        if self.is_at_attr(k):
            return True
        if self.is_curly_attr(k) and self.text(k + 2) != "trigger":
            close = self.partner[k]
            return close < 0 or self.member_start(close + 1)
        return False

    def is_expression_brace(self, k, close):
        prev = self.text(k - 1)
        if self.text(k + 1) == "case":
            return True
        if prev == "*" and self.text(k - 2) in ("decreases", "reads", "modifies", ","):
            return False
        if prev in AMBIGUOUS_PREV:
            nxt = close + 1
            return not (close < 0 or nxt >= self.n or self.text(nxt) in ("}", "by")
                        or self.member_start(nxt))
        return prev in EXPR_PREV

    # --- members ---------------------------------------------------------------------------
    def members(self, i, end, prefix, ckind, container):
        while i < end:
            x = self.text(i)
            if x == ";" or x == "}":
                i += 1
                continue
            start, attrs, mods = i, [], []
            while i < end:
                if self.attr_at(i):
                    a = self.read_attr(i)
                    attrs.append(a)
                    i = a.end
                elif self.t[i].kind == "id" and self.text(i) in MODIFIERS:
                    mods.append(self.text(i))
                    i += 1
                else:
                    break
            if i >= end:
                break
            kw = self.text(i)
            if kw == "module":
                i = self.module(start, i, mods, prefix)
            elif kw == "include":
                self.src.includes.append(self.t[i].line)
                i += 2
            elif kw == "import":
                i = self.import_(i, prefix)
            elif kw == "export":
                stop = self.skip_member(i + 1, end)
                self.src.export_decls.append((self.t[i].line, prefix,
                                              " ".join(t.text for t in self.t[i:stop])))
                i = stop
            elif kw in METHODLIKE:
                i = self.methodlike(start, i, attrs, mods, prefix, ckind, container, end)
            elif kw in TYPEDECL or kw in CLASSLIKE:
                i = self.typedecl(start, i, attrs, mods, prefix, ckind, container, end)
            elif kw in ("const", "var"):
                i = self.field_(start, i, attrs, mods, prefix, ckind, container, end)
            else:
                i += 1
        return i

    def qualify(self, prefix, name):
        return f"{prefix}.{name}" if prefix else name

    def module(self, start, i, mods, prefix):
        i += 1
        while self.attr_at(i):
            i = self.read_attr(i).end
        parts = []
        while i < self.n and self.t[i].kind == "id":
            parts.append(self.text(i))
            i += 1
            if self.text(i) == "." and self.t[i].glued:
                i += 1
            else:
                break
        name = ".".join(parts) or "?"
        refines = None
        if self.text(i) == "refines":
            i += 1
            rp = []
            while i < self.n and self.t[i].kind == "id":
                rp.append(self.text(i))
                i += 1
                if self.text(i) == ".":
                    i += 1
                else:
                    break
            refines = ".".join(rp)
        while i < self.n and self.text(i) != "{":
            i += 1
        close = self.partner[i] if i < self.n else -1
        if close < 0:
            close = self.n - 1
        qual = self.qualify(prefix, name)
        m = ModuleDecl(name, qual, "abstract" in mods, refines, self.t[start].line,
                       self.t[close].line, i, close)
        self.src.modules.append(m)
        self.members(i + 1, close, qual, "abstract-module" if m.abstract else "module", qual)
        return close + 1

    def import_(self, i, prefix=""):
        line, kw = self.t[i].line, i
        i += 1
        if self.text(i) == "opened":
            i += 1
        if i + 1 < self.n and self.t[i].kind == "id" and self.text(i + 1) in ("=", ":"):
            i += 2
        parts = []
        while i < self.n and self.t[i].kind == "id":
            parts.append(self.text(i))
            i += 1
            if self.text(i) == "." and self.text(i + 1) != "{":
                i += 1
            else:
                break
        if parts:
            self.src.imports.append((line, ".".join(parts)))
        end = self.skip_member(i, self.n)
        self.src.import_decls.append((line, prefix, " ".join(x.text for x in self.t[kw:end])))
        return end

    def skip_member(self, i, end):
        while i < end and not self.member_start(i):
            if self.text(i) == "{" and self.partner[i] > 0:
                i = self.partner[i] + 1
            else:
                i += 1
        return i

    def header(self, i, end, attrs_out, clauses_out):
        """Scan a declaration header from token i. Returns (header_end, body, by_method)."""
        depth, pending_match = 0, 0
        while i < end:
            x = self.text(i)
            if x in ("(", "["):
                depth += 1
            elif x in (")", "]"):
                depth = max(0, depth - 1)
            elif depth == 0:
                if self.t[i].kind == "id" and x in CLAUSE_KW:
                    clauses_out.append((x, i))
                elif x == "match":
                    pending_match += 1
                elif self.is_curly_attr(i):
                    close = self.partner[i]
                    if close < 0 or self.member_start(close + 1):
                        return i, None, None          # the next member's attribute
                    attrs_out.append(self.read_attr(i))
                    i = close + 1
                    continue
                elif x == "{":
                    close = self.partner[i]
                    if self.text(i + 1) == "case" and pending_match:
                        pending_match -= 1
                        i = close + 1 if close > 0 else i + 1
                        continue
                    if close > 0 and self.is_expression_brace(i, close):
                        i = close + 1
                        continue
                    if close < 0:
                        return i, None, None
                    by = None
                    k = close + 1
                    if self.text(k) == "by" and self.text(k + 1) == "method" and self.text(k + 2) == "{":
                        bc = self.partner[k + 2]
                        if bc > 0:
                            by = (k + 2, bc)
                    return i, (i, close), by
                elif self.member_start(i, in_header=True):
                    return i, None, None
            i += 1
        return i, None, None

    def methodlike(self, start, i, attrs, mods, prefix, ckind, container, end):
        kw, line, kwi = self.text(i), self.t[i].line, i
        kind = {"colemma": "lemma", "copredicate": "predicate"}.get(kw, kw)
        i += 1
        if kind in ("function", "predicate") and self.text(i) == "method":
            i += 1
        while self.attr_at(i):
            a = self.read_attr(i)
            attrs.append(a)
            i = a.end
        name = "_ctor"
        if self.t[i].kind == "id" and self.text(i) not in CLAUSE_KW and self.text(i) != "returns":
            name, i = self.text(i), i + 1
        hattrs, clauses = [], []
        hend, body, by = self.header(i, end, hattrs, clauses)
        last = by[1] if by else body[1] if body else max(hend - 1, start)
        d = Decl(kind, name, self.qualify(prefix, name), container, ckind, mods, attrs, hattrs,
                 start, kwi, hend, body, by, clauses, line, self.t[last].line)
        self.src.decls.append(d)
        return (by[1] + 1) if by else (body[1] + 1) if body else hend

    def typedecl(self, start, i, attrs, mods, prefix, ckind, container, end):
        kw, line, kwi = self.text(i), self.t[i].line, i
        i += 1
        while self.attr_at(i):
            a = self.read_attr(i)
            attrs.append(a)
            i = a.end
        name = self.text(i) if i < self.n and self.t[i].kind == "id" else "?"
        i += 1
        hattrs, clauses = [], []
        if kw in CLASSLIKE:
            while i < end and self.text(i) != "{":
                i += 1
            body = (i, self.partner[i]) if i < end and self.partner[i] > 0 else None
            hend = i
        else:
            hend, body, _ = self.header(i, end, hattrs, clauses)
        last = body[1] if body else max(hend - 1, start)
        qual = self.qualify(prefix, name)
        d = Decl(kw, name, qual, container, ckind, mods, attrs, hattrs, start, kwi, hend, body,
                 None, clauses, line, self.t[last].line)
        self.src.decls.append(d)
        if body:
            self.members(body[0] + 1, body[1], qual, kw if kw in CLASSLIKE else kw, qual)
            return body[1] + 1
        return hend

    def field_(self, start, i, attrs, mods, prefix, ckind, container, end):
        kw, line, kwi = self.text(i), self.t[i].line, i
        i += 1
        while self.attr_at(i):
            a = self.read_attr(i)
            attrs.append(a)
            i = a.end
        name = self.text(i) if i < self.n and self.t[i].kind == "id" else "?"
        i += 1
        has_value, depth = False, 0
        while i < end:
            x = self.text(i)
            if x in ("(", "["):
                depth += 1
            elif x in (")", "]"):
                depth = max(0, depth - 1)
            elif x == "{" and self.partner[i] > 0 and not self.is_curly_attr(i):
                i = self.partner[i] + 1
                continue
            elif depth == 0 and x == ":=":
                has_value = True
            elif depth == 0 and (x == ";" or self.member_start(i)):
                break
            i += 1
        d = Decl(kw, name, self.qualify(prefix, name), container, ckind, mods, attrs, [], start,
                 kwi, i, None, None, [], line, self.t[max(i - 1, start)].line, has_value)
        self.src.decls.append(d)
        return i

    def parse(self):
        self.members(0, self.n, "", "top", "")
        # attributes inside bodies and expressions (`assert {:only}`, triggers):
        seen = {a.start for a in self.src.attrs}
        for k in range(self.n):
            if k not in seen and self.attr_at(k):
                self.read_attr(k)
        self.src.attrs.sort(key=lambda a: a.start)
        return self.src


def parse_source(text, path="<text>"):
    """The modules, declarations, includes, imports and attributes of Dafny source."""
    return _Parser(path, text).parse()


def parse_file(path):
    p = Path(path)
    return parse_source(p.read_text(encoding="utf-8"), str(p))


# =====================================================================================
# Lint (static, tool-free; Δ3, Δ5, design §6.3, spec §3.8.4 H6, §3.9 need:)
# =====================================================================================

# Attributes a learner, agent or reference file may carry. Everything else is a
# finding: the ones below by their own rule, the rest as "attribute-not-allowed"
# (G17: Boogie pass-through attributes; an allowlist, not a blocklist).
ALLOWED_CURLY = {"induction", "inductionTrigger", "trigger", "test", "fuel", "opaque",
                 "isolate_assertions", "isolate", "split_here", "vcs_split_on_every_assert",
                 "disableNonlinearArithmetic", "tailrecursion", "nativeType", "print", "error",
                 "main"}
ALLOWED_AT = {"Test", "IsolateAssertions", "Induction", "InductionTrigger", "Fuel",
              "TailRecursion", "Print", "DisableNonlinearArithmetic", "VcsSplitOnEveryAssert",
              "NativeUInt8", "NativeUInt16", "NativeUInt32", "NativeUInt64", "NativeInt8",
              "NativeInt16", "NativeInt32", "NativeInt64", "NativeInt", "NativeNone"}
ATTR_RULES = {
    ("{:", "axiom"): ("axiom-attribute", "an {:axiom} declaration is an unproved assumption, "
                                         "silent in verify (Δ3, G1)"),
    ("@", "Axiom"): ("axiom-attribute", "an @Axiom declaration is an unproved assumption, silent "
                                        "in verify (Δ3, G1)"),
    ("{:", "verify"): ("verify-false", "{:verify …} switches verification of a declaration off "
                                       "or on by hand (G5)"),
    ("{:", "only"): ("verify-only", "{:only} turns other members or assertions into "
                                    "assumptions (G5, G17)"),
    ("@", "VerifyOnly"): ("verify-only", "@VerifyOnly skips every other member of the file (G5)"),
    ("{:", "extern"): ("extern", "{:extern} trusts code the verifier never sees (Δ3)"),
    ("@", "Extern"): ("extern", "@Extern trusts code the verifier never sees (Δ3)"),
    ("{:", "options"): ("options-attribute", "verifier options live only in the unit's project "
                                             "file, never in a source file (spec §3.1 rule 6)"),
    ("@", "Options"): ("options-attribute", "verifier options live only in the unit's project "
                                            "file, never in a source file (spec §3.1 rule 6)"),
    ("{:", "resource_limit"): ("resource-attribute", "a per-declaration resource limit "
                                                     "overrides the course pin (Δ56)"),
    ("{:", "rlimit"): ("resource-attribute", "a per-declaration resource limit overrides the "
                                             "course pin (Δ56)"),
    ("@", "ResourceLimit"): ("resource-attribute", "a per-declaration resource limit overrides "
                                                   "the course pin (Δ56)"),
    ("{:", "timeLimit"): ("resource-attribute", "a per-declaration time limit (Δ56, G20)"),
    ("{:", "timeLimitMultiplier"): ("resource-attribute", "a per-declaration time limit (G20)"),
    ("@", "TimeLimit"): ("resource-attribute", "a per-declaration time limit (G20)"),
    ("@", "TimeLimitMultiplier"): ("resource-attribute", "a per-declaration time limit (G20)"),
}
LEARNER_RULES = {
    "abstract-module": "an abstract module silences its bodyless members' hole warnings (Δ3, G3)",
    "trait": "a trait's bodyless members do not warn (Δ3, G3); a trait that a class of its "
             "file implements in full is allowed (DV5c)",
    "bodyless-silent": "a bodyless declaration with no `ensures` is silent in verify: an "
                       "uncounted hole (Δ3, G4)",
    "bodyless-abstract": "a bodyless member of an abstract module or trait is silent (Δ3, G3)",
    "multi-ensures-hole": "a hole carries exactly one `ensures` (two warn twice, Δ5)",
    "assume-axiom": "`assume {:axiom}` is silent in verify (Δ3, G1)",
    "decreases-star": "`decreases *` gives up termination, silently (Δ3)",
    "expect-outside-test": "`expect` outside a {:test}/@Test method is assumed by the verifier "
                           "(Δ3, G11)",
    "include": "an included file is not verified by default and audit skips it (Δ3, G9)",
    "uninitialized-const": "a module-level const with no value is an uninterpreted oracle (G4)",
    "attribute-not-allowed": "an attribute outside the course allowlist (G17)",
    "reserved-name": "solutions_policy and solutions-first are reserved names (Δ79, Δ86)",
}
STRICT_RULES = {
    "assume": "`assume` is a hole; a finished file has none",
    "bodyless": "a bodyless declaration is a hole; a finished file has none",
}
REFERENCE_RULES = {
    "slot-in-reference": "a reference twin holds no `SLOT:` and no `???` (spec §3.8.4 H6)",
    "need-missing": "an exit block's `need:` fragment is missing from its code (spec §3.9)",
}
GIVEN_RULES = {
    "abstract-not-refined": "an abstract module in a given layer is allowed only when concrete "
                            "modules of the same program refine it, every bodyless member with "
                            "a body (Δ3, Δ44)",
}
RESERVED = {"solutions_policy", "solutions_first"}


def _reserved(name):
    return name.lower().replace("-", "_") in RESERVED


def _expand(paths):
    out = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            out += sorted(x for x in p.rglob("*") if x.is_file()
                          and (x.name.endswith(".dfy") or x.name.endswith(".dfy.specimen"))
                          and not any(part.endswith("-py") for part in x.relative_to(p).parts[:-1]))
        else:
            out.append(p)
    return out


def lint(paths, mode, context=(), given_role=False):
    """Static findings over Dafny files (directories are walked for *.dfy and
    *.dfy.specimen). mode: learner (silent hole kinds and banned constructs;
    loud holes are the tool's to count), agent (also every hole: a delivery is
    hole-free), reference (as agent, plus spec §3.8.4 H6 and the `need:` lines),
    given (the learner rules for a given layer or a frozen spec, below).

    Abstract modules (Δ3, Δ44). In learner, agent and reference files an
    abstract module and its bodyless members are always findings (they are
    silent in verify and in audit). A given layer may hold a frozen abstract
    spec that the same program refines (L4's statement freeze): there an
    abstract module is allowed when at least one concrete module of the
    program refines it (directly or through abstract refiners) and every such
    concrete module gives every bodyless member a body (a const a value), so
    the program's verification proves each statement; otherwise it is an
    `abstract-not-refined` finding plus a `bodyless-abstract` finding for each
    member left without a body. A file listed in a registry record's
    `statements` (a frozen challenge statement, Δ73) may hold abstract modules
    whatever refines them. A file has that given role when it is a given layer
    of a course tree (dafny/given/<T>/<QG|RG>_<layer>_*.dfy under the root
    holding MODULES.toml) or a declared statement, in every mode; mode `given`
    grants it to every linted file (an out-of-tree copy of a given layer), with
    the learner rules; given_role=True grants it in any mode (the reference
    rules on a reference copy of a given layer). Traits stay findings in every
    mode, except a trait that a class of the same file implements in full
    (implemented_traits; DV5c, Q17.H1d).

    `context` names further files of the same program (not linted) whose
    modules may refine the linted files' abstract modules. Never runs a tool;
    never quotes code."""
    if mode not in MODES:
        raise ValueError(f"lint mode must be one of {', '.join(MODES)}, not {mode!r}")
    files = _expand(paths)
    if not files:
        raise ValueError("lint: no files (an empty list fails)")
    files = list(dict.fromkeys(Path(f).resolve() for f in files))
    texts = {f: f.read_text(encoding="utf-8") for f in files}
    roles = {f: "given" if mode == "given" or given_role else _given_role(f) for f in files}
    program = None
    if any(roles.values()):
        srcs = {f: parse_source(texts[f], str(f)) for f in files}
        for c in context:
            c = Path(c).resolve()
            if c not in srcs and c.is_file() and c.suffix == ".dfy":
                srcs[c] = parse_file(c)
        program = list(srcs.values())
    out = []
    for f in files:
        out += lint_source(texts[f], str(f), mode, role=roles[f], program=program)
    return sorted(set(out), key=lambda x: (x.file, x.line, x.kind))


def _statement_paths(root):
    """Repo-relative paths a registry record declares in `statements` (Δ73)."""
    try:
        key = (str(root), (Path(root) / gu.REGISTRY).stat().st_mtime_ns)
    except OSError:
        return set()
    if key not in _STATEMENTS:
        data, _ = gu.load_registry(Path(root))
        paths = set()
        mods = data.get("module") if isinstance(data, dict) else None
        for m in mods if isinstance(mods, list) else []:
            sts = m.get("statements") if isinstance(m, dict) else None
            for st in sts if isinstance(sts, list) else []:
                if isinstance(st, dict) and isinstance(st.get("path"), str):
                    paths.add(PurePosixPath(st["path"]).as_posix())
        _STATEMENTS[key] = paths
    return _STATEMENTS[key]


_STATEMENTS: dict = {}


def _given_role(path):
    """"given" for a given layer of a course tree, "statement" for a file a
    registry record lists in `statements`, else None (decided by the path under
    the course root, never by a file name alone)."""
    p = Path(path).resolve()
    root = course_root(p)
    if root is None:
        return None
    try:
        rel = p.relative_to(root.resolve()).as_posix()
    except ValueError:
        return None
    if rel in _statement_paths(root.resolve()):
        return "statement"
    if GIVEN_PATH.fullmatch(rel):
        return "given"
    return None


def _needs_refinement(d):
    """A member an abstract module states without a definition."""
    if d.kind in METHODLIKE and d.kind != "iterator":
        return d.body is None and d.by_method is None
    return d.kind == "const" and not d.has_value


def refinement_gaps(sources):
    """{abstract module qual: (refined, gaps)} over the modules of `sources`
    (one program): `refined` is True when at least one concrete module refines
    it (directly or through abstract modules); `gaps` holds the qualified names
    of its bodyless members (and value-less consts) that some concrete refiner
    leaves without a body, or all of them when nothing concrete refines it."""
    mods = [m for s in sources for m in s.modules]
    by_qual = {m.qual: m for m in mods}
    members = {}
    for s in sources:
        for d in s.decls:
            members.setdefault(d.container, []).append(d)

    def resolve(name):
        if name in by_qual:
            return by_qual[name]
        cands = {m.qual: m for m in mods if m.qual.endswith("." + name) or m.name == name}
        return next(iter(cands.values())) if len(cands) == 1 else None

    def chain_to(c, a):
        chain, cur, seen = [], c, set()
        while cur is not None and cur.qual not in seen:
            if cur.qual == a.qual:
                return chain
            seen.add(cur.qual)
            chain.append(cur)
            cur = resolve(cur.refines) if cur.refines else None
        return None

    out = {}
    for a in mods:
        if not a.abstract:
            continue
        need = {d.name: d.qual for d in members.get(a.qual, []) if _needs_refinement(d)}
        chains = [ch for c in mods if not c.abstract and (ch := chain_to(c, a))]
        if not chains:
            out[a.qual] = (False, set(need.values()))
            continue
        gaps = set()
        for ch in chains:
            done = {d.name for m in ch for d in members.get(m.qual, [])
                    if not _needs_refinement(d) and d.kind in (METHODLIKE | {"const"})}
            gaps |= {q for n, q in need.items() if n not in done}
        out[a.qual] = (True, gaps)
    return out


def implemented_traits(src):
    """{trait qual} of the traits of one source that a class of the same source
    implements (DV5c, Q17.H1d's given `PQueue`): a class whose header names the
    trait after `extends`, and which gives every bodyless member of the trait a
    member of the same name with a body. Such a trait is no `trait` finding and
    its bodyless members no `bodyless-abstract` findings: each is a statement
    that the class's member is verified against, not a silent hole (Δ3's G3 is
    a trait nothing implements). A trait no class of its file implements in full
    stays a finding in every mode."""
    traits = {d.qual: d for d in src.decls if d.kind == "trait"}
    if not traits:
        return set()
    members = {}
    for d in src.decls:
        members.setdefault(d.container, []).append(d)
    out = set()
    for c in (d for d in src.decls if d.kind == "class"):
        names = [src.toks[k].text for k in range(c.kw, c.header_end)]
        if "extends" not in names:
            continue
        ext = set(names[names.index("extends") + 1:]) - {","}
        own = {m.name for m in members.get(c.qual, []) if m.body is not None}
        for tq, td in traits.items():
            if td.name not in ext and tq not in ext:
                continue
            need = {m.name for m in members.get(tq, []) if m.kind in METHODLIKE and
                    m.body is None}
            if need <= own:
                out.add(tq)
    return out


def lint_source(text, path, mode, role=None, program=None):
    """lint() for one file's text. `role` is "given" or "statement" for a file
    with the given role (lint() decides it), and `program` the parsed sources of
    its program (default: this file alone)."""
    src = parse_source(text, path)
    out = []

    def add(line, kind, message=None):
        msg = message or LEARNER_RULES.get(kind) or STRICT_RULES.get(kind) or \
            REFERENCE_RULES.get(kind) or GIVEN_RULES.get(kind) or kind
        out.append(Finding(path, line, kind, msg))

    strict = mode in ("reference", "agent")
    implemented = implemented_traits(src)  # traits a class of this file implements (DV5c)
    allowed, unrefined = set(), set()     # given role: allowed abstract modules, open members
    if role:
        gaps = refinement_gaps(program if program is not None else [src])
        for m in src.modules:
            if not m.abstract:
                continue
            refined, open_ = gaps.get(m.qual, (False, set()))
            if role == "statement" or (refined and not open_):
                allowed.add(m.qual)
            else:
                unrefined |= open_
    for line in src.includes:
        add(line, "include")
    for m in src.modules:
        if m.abstract and m.qual in allowed:
            pass
        elif m.abstract and role:
            add(m.line, "abstract-not-refined")
        elif m.abstract:
            add(m.line, "abstract-module")
        for part in [m.name, *(m.refines.split(".") if m.refines else [])]:
            if _reserved(part):
                add(m.line, "reserved-name")
    for line, name in src.imports:
        if any(_reserved(p) for p in name.split(".")):
            add(line, "reserved-name")
    stem = PurePosixPath(path).name.split(".")[0]
    if _reserved(stem):
        add(1, "reserved-name")
    for a in src.attrs:
        if a.name == "axiom" and a.start > 0 and src.toks[a.start - 1].text == "assume":
            continue   # `assume {:axiom}`: the assume-axiom rule below reports it once
        rule = ATTR_RULES.get((a.style, a.name))
        if rule:
            add(a.line, rule[0], rule[1])
        elif (a.style == "{:" and a.name not in ALLOWED_CURLY) or \
                (a.style == "@" and a.name not in ALLOWED_AT):
            add(a.line, "attribute-not-allowed")
    for d in src.decls:
        # a member of an allowed abstract module, or (given role) one every
        # concrete refiner defines: a statement the program proves, not a hole
        stated = d.container_kind == "abstract-module" and \
            (d.container in allowed or (role is not None and d.qual not in unrefined))
        if d.kind == "trait" and d.qual not in implemented:
            add(d.line, "trait")
        if d.kind in ("const",) and d.container_kind in ("module", "abstract-module", "top") \
                and not d.has_value and not stated:
            add(d.line, "uninitialized-const")
        if d.kind not in METHODLIKE:
            continue
        is_test = any((a.style, a.name) in (("{:", "test"), ("@", "Test")) for a in d.attrs)
        if d.body is None and d.kind != "iterator":
            if d.container_kind in ("abstract-module", "trait"):
                if not stated and not (d.container_kind == "trait" and
                                       d.container in implemented):
                    add(d.line, "bodyless-abstract")
            elif d.ensures == 0:
                add(d.line, "bodyless-silent")
            elif strict:
                add(d.line, "bodyless")
            elif d.ensures > 1:
                add(d.line, "multi-ensures-hole")
        for k in range(d.start, d.by_method[1] if d.by_method else d.body[1] if d.body
                       else d.header_end):
            tok = src.toks[k]
            if tok.kind != "id":
                continue
            if tok.text == "decreases" and k + 1 < len(src.toks) and src.toks[k + 1].text == "*":
                add(tok.line, "decreases-star")
            elif tok.text == "assume":
                nxt = [x.text for x in src.toks[k + 1:k + 4]]
                if nxt[:3] == ["{", ":", "axiom"]:
                    add(tok.line, "assume-axiom")
                elif strict:
                    add(tok.line, "assume")
            elif tok.text == "expect" and not is_test:
                add(tok.line, "expect-outside-test")
    if mode == "reference":
        for ln, line in enumerate(text.split("\n"), 1):
            if "SLOT:" in line or "???" in line:
                add(ln, "slot-in-reference")
        out += need_check_source(text, path)
    return out


def _norm_ws(s):
    return " ".join(s.split())


def need_check_source(text, path):
    """Findings for X blocks whose `need:` fragments are missing from their
    non-comment code (spec §3.9; whitespace-normalized)."""
    items, _ = ci.parse_items(path, text)
    code, _ = ci.scan(path, text)
    out = []
    for it in items:
        if not it["need"]:
            continue
        block = _norm_ws(" ".join(code[it["line_start"]:it["line_end"]]))
        for frag in it["need"]:
            if _norm_ws(frag) not in block:
                out.append(Finding(path, it["line_start"], "need-missing",
                                   f"{it['id']}: " + REFERENCE_RULES["need-missing"]))
    return out


# =====================================================================================
# Statement freeze (Δ44): normalized spec-text hashes and the refinement check
# =====================================================================================

HASHED_KINDS = METHODLIKE | TYPEDECL | {"const"}
DEFINITION_KINDS = {"function", "predicate"}   # their bodies are part of the statement


def statement_attr_skip(d):
    """The token indices of a declaration's attributes that its statement drops:
    every attribute but a trigger written in a clause (`ensures forall k
    {:trigger F(k)} :: …`), which is part of what the clause states, as a
    Verus `#[trigger]` is (DV5c; before it, a trigger at a clause's top level
    was dropped and one inside parentheses kept)."""
    skip = set()
    for a in d.attrs + d.header_attrs:
        if a in d.header_attrs and a.style == "{:" and a.name == "trigger":
            continue
        skip.update(range(a.start, a.end))
    return skip


def _spec_tokens(src, d):
    skip = statement_attr_skip(d)
    toks = []
    for k in range(d.start, d.header_end):
        if k in skip or (src.toks[k].text == "opaque" and k < d.kw):
            continue
        toks.append(src.toks[k].text)
    if d.kind in DEFINITION_KINDS and d.body:
        toks += [src.toks[k].text for k in range(d.body[0], d.body[1] + 1)]
    if d.kind == "const" and toks and toks[-1] == ";":
        toks.pop()
    return toks


def spec_hash_source(text, path="<text>", symbols=None):
    src = parse_source(text, path)
    out = {}
    for d in src.decls:
        if d.kind not in HASHED_KINDS:
            continue
        if symbols is not None and d.qual not in symbols:
            continue
        norm = d.kind + "\0" + " ".join(_spec_tokens(src, d))
        out[d.qual] = hashlib.sha256(norm.encode("utf-8")).hexdigest()
    return out


def measure_free_text(text, path="<text>"):
    """`text` with the header `decreases` clauses of every method-like
    declaration blanked (layout and line numbers kept), except `decreases *`,
    which lets a method diverge and so weakens what it states. An ADDED
    MEASURE: a `decreases` on a declaration that shipped without one is part
    of the proof, not of the statement (dvl.verus_spec.measure_free_text says
    how the freeze uses it; Δ160's first Open item, a Q08 exit). Static."""
    src = parse_source(text, path)
    spans = []
    for d in src.decls:
        if d.kind not in METHODLIKE:
            continue
        starts = sorted(k for _, k in d.clauses if d.start <= k < d.header_end)
        for n, k in enumerate(starts):
            if src.toks[k].text != "decreases":
                continue
            end = starts[n + 1] if n + 1 < len(starts) else d.header_end
            words = [src.toks[j].text for j in range(k + 1, end)]
            if not words or words[0] == "*":
                continue
            spans.append((src.toks[k].start, src.toks[end - 1].end))
    out = text
    for s, e in sorted(spans, reverse=True):
        out = out[:s] + "".join(c if c == "\n" else " " for c in out[s:e]) + out[e:]
    return out


# Frozen import lists (QPLAN §30 Q62). A module whose import list is part of
# what it states carries this marker as a comment line directly inside it (Q11's
# `Q11_VcAnswer` imports nothing, so an answer cannot name the given program);
# `specfreeze --pin` records the module's imports, and `--check` refuses an
# added, removed or changed import there. Only the marked modules are frozen.
FROZEN_IMPORTS_MARKER = re.compile(r"^\s*//\s*specfreeze:\s*frozen-imports\b")


def module_imports(src):
    """{module qual ('' = the default module): [import statement text, …]} of a
    parsed source, every module of the file listed (an empty list for a module
    with no import). The text is the statement's tokens joined by one space
    (comments and layout dropped). Static."""
    out = {m.qual: [] for m in src.modules}
    out.setdefault("", [])
    for _, mod, text in src.import_decls:
        out.setdefault(mod, []).append(text)
    return out


def subtree_imports(src, qual):
    """The sorted import statements of module `qual` and of every module nested
    in it, each as "<nested path relative to qual>: <statement text>" (the
    module's own imports with an empty path), or None when the file declares no
    such module. A frozen import list covers the whole subtree, so an import
    added in a new nested module counts as a change too."""
    if not any(m.qual == qual for m in src.modules):
        return None
    out = []
    for _, mod, text in src.import_decls:
        if mod == qual or mod.startswith(qual + "."):
            out.append(f"{mod[len(qual) + 1:]}: {text}")
    return sorted(out)


def frozen_import_modules(src):
    """{module qual: marker line} of the modules whose import list is frozen: a
    FROZEN_IMPORTS_MARKER comment line inside the module and outside every
    module nested in it (the innermost module holding the line)."""
    out = {}
    for ln, line in enumerate(src.text.split("\n"), 1):
        if not FROZEN_IMPORTS_MARKER.match(line):
            continue
        inside = [m for m in src.modules if m.line <= ln <= m.end_line]
        if inside:
            m = max(inside, key=lambda x: (x.line, x.open))
            out.setdefault(m.qual, ln)
    return out


FROZEN_EXPORTS_MARKER = re.compile(r"^\s*//\s*specfreeze:\s*frozen-exports\b")


def frozen_export_modules(src):
    """Modules whose existing export boundary is frozen (R03)."""
    out = {}
    for ln, line in enumerate(src.text.split("\n"), 1):
        if FROZEN_EXPORTS_MARKER.match(line):
            inside = [m for m in src.modules if m.line <= ln <= m.end_line]
            if inside:
                m = max(inside, key=lambda x: (x.line, x.open))
                out.setdefault(m.qual, ln)
    return out


def module_exports(src):
    """{module: [token-normalized export declarations]} (layout/comments free)."""
    out = {m.qual: [] for m in src.modules}
    out.setdefault("", [])
    for _, mod, text in src.export_decls:
        out.setdefault(mod, []).append(text.rstrip(" ;"))
    return out


def export_sets(statements):
    """Parse the export-boundary profile: named/default sets with explicit
    provides/reveals/extends lists. Unsupported syntax fails closed, only in
    modules that opt into the freeze. Entry order is irrelevant."""
    out = {}
    for statement in statements:
        words = [t.text for t in tokenize(statement)]
        if not words or words.pop(0) != "export":
            raise ValueError("an export declaration must start with export")
        modes = ("provides", "reveals", "extends")
        name = words.pop(0) if words and words[0] not in modes else ""
        if name and not ID_RE.fullmatch(name):
            raise ValueError("unsupported export set name")
        if name in out:
            raise ValueError("duplicate export set")
        parts, mode, entry = {k: set() for k in modes}, None, []

        def flush():
            if entry:
                value = "".join(entry)
                if not re.fullmatch(r"(?:[A-Za-z_][A-Za-z0-9_'?]*\.)*"
                                    r"(?:[A-Za-z_][A-Za-z0-9_'?]*|\*)", value):
                    raise ValueError("unsupported export entry")
                parts[mode].add(value)
                entry.clear()

        for word in words:
            if word in modes:
                flush()
                mode = word
            elif word in (",", ";"):
                flush()
            elif mode is None:
                raise ValueError("an export entry needs provides, reveals or extends")
            else:
                entry.append(word)
        flush()
        out[name] = parts
    return out


def exports_preserved(frozen, candidate, additions=()):
    """Keep every shipped set, exposure and inheritance edge. Only explicit
    provides entries for pinned open-body definitions may be added. Reveals,
    wildcards, extra sets and aliases cannot expose the hidden representation.
    Removing the source marker does not remove a recorded boundary."""
    before, after = export_sets(frozen), export_sets(candidate)
    if not before or before.keys() != after.keys():
        return False
    allowed = set(additions)
    for name, old in before.items():
        new = after[name]
        if new["reveals"] != old["reveals"] or new["extends"] != old["extends"]:
            return False
        if not old["provides"] <= new["provides"] or not (
                new["provides"] - old["provides"]) <= allowed:
            return False
    return True


def spec_hash(path, symbols=None):
    """{qualified symbol: sha256 of its normalized statement}: the signature and
    the requires/ensures/decreases/reads/modifies clauses, token by token
    (comments, whitespace and attributes dropped but a clause's triggers,
    statement_attr_skip; `opaque` dropped); a function's
    or predicate's body is part of its statement, a lemma's or method's is not.
    Only the requested symbols when `symbols` is given. Static: no tool runs."""
    p = Path(path)
    return spec_hash_source(p.read_text(encoding="utf-8"), str(p),
                            None if symbols is None else set(symbols))


def _rel_symbol(qual, module):
    return qual[len(module) + 1:] if qual.startswith(module + ".") else qual


def freeze_check(frozen, candidate):
    """Statement-freeze findings for `candidate` against `frozen` (Δ44).

    `frozen` is a Dafny file or a {symbol: sha256} mapping from spec_hash.
      - Hash: every frozen symbol of a concrete module must exist in the
        candidate with the same normalized statement (freeze-missing,
        freeze-changed); a `decreases` added to a declaration that had none is
        no change (measure_free_text).
      - Refinement: for each abstract module of a frozen file, some candidate
        module must refine it (freeze-detached); every bodyless lemma or method
        of it must be refined with a body (freeze-not-concrete); and the
        candidate, verified together with the frozen file at the gate's
        settings, must hold every parent `ensures` with no hole left
        (freeze-refinement, freeze-not-concrete). A refining member that
        restates a `requires` is a tool error (W-D19).
      - The candidate's learner-mode lint findings ride along: an {:axiom}
        child is silent in verify (Δ44)."""
    cand = Path(candidate).resolve()
    csrc = parse_file(cand)
    out = []
    if isinstance(frozen, (str, os.PathLike)):
        fpath = Path(frozen).resolve()
        fsrc = parse_file(fpath)
        abstract = {m.qual: m for m in fsrc.modules if m.abstract}
        in_abstract = lambda d: any(d.qual.startswith(q + ".") for q in abstract)  # noqa: E731
        want = {d.qual: d for d in fsrc.decls if d.kind in HASHED_KINDS and not in_abstract(d)}
        if not want and not abstract:
            # nothing frozen: no pass (the empty-set rule; DV6 fix round, as Verus's
            # freeze-empty: a statements snapshot with no statement in it freezes nothing)
            return [Finding(str(cand), 0, "freeze-empty",
                            f"{fpath.name}: the frozen file holds no statement and no abstract "
                            "module, so nothing is frozen")]
        hashes = spec_hash_source(fsrc.text, str(fpath), set(want))
    else:
        fpath, fsrc, abstract, want = None, None, {}, {}
        hashes = dict(frozen)
        if not hashes:
            raise ValueError("freeze_check: an empty frozen mapping (empty lists fail)")
    have = spec_hash_source(csrc.text, str(cand))
    if any(have.get(s, h) != h for s, h in hashes.items()):
        # an added measure is no change (measure_free_text)
        alt = spec_hash_source(measure_free_text(csrc.text, str(cand)), str(cand))
        have = {s: (hashes[s] if s in hashes and alt.get(s) == hashes[s] else h)
                for s, h in have.items()}
    cdecl = {d.qual: d for d in csrc.decls}
    for sym, h in sorted(hashes.items()):
        if sym not in have:
            out.append(Finding(str(cand), 0, "freeze-missing",
                               f"{sym}: a frozen statement is missing from the candidate"))
        elif have[sym] != h:
            out.append(Finding(str(cand), cdecl[sym].line, "freeze-changed",
                               f"{sym}: the statement differs from the frozen one"))
    for q, m in sorted(abstract.items()):
        refiners = [cm for cm in csrc.modules if cm.refines in (q, m.name)]
        if not refiners:
            out.append(Finding(str(cand), 0, "freeze-detached",
                               f"no module refines the frozen abstract module {q}"))
            continue
        for d in fsrc.decls:
            if not d.qual.startswith(q + ".") or d.kind not in ("lemma", "method") or d.body:
                continue
            rel = _rel_symbol(d.qual, q)
            for rm in refiners:
                cd = cdecl.get(f"{rm.qual}.{rel}")
                if cd is None or cd.body is None:
                    out.append(Finding(str(cand), cd.line if cd else rm.line,
                                       "freeze-not-concrete",
                                       f"{rm.qual}.{rel}: the frozen statement is not refined "
                                       "with a body"))
    if abstract:
        out += _freeze_verify(fpath, cand)
    out += [f for f in lint([cand], "learner")]
    return sorted(set(out), key=lambda x: (x.file, x.line, x.kind, x.message))


def _freeze_verify(fpath, cand):
    """Verify the candidate together with the frozen file (learner-loop flags,
    so unrelated holes do not mask the result) and keep what the refinement is
    responsible for: hole warnings re-emitted at the frozen file (a refined
    statement left without a body), W-D19 (a refining member adds or restates a
    requires), and errors that point into the frozen file (a parent `ensures`
    not established) or sit in a refining module."""
    prog = program(cand)
    extra = [] if any(Path(f).resolve() == fpath.resolve() for f in prog.files) else [fpath]
    try:
        res = _verify_program(prog, gate=False, extra_inputs=extra, target=str(cand))
    finally:
        discard(prog)
    if res.verdict in ("refused", "killed(memory)", "error"):
        return [Finding(str(cand), 0, "freeze-error",
                        f"the refinement check could not run ({res.verdict}); raw output: "
                        f"{res.raw_dir}")]
    frozen = str(fpath.resolve())
    csrc = parse_file(cand)
    ranges = [(m.line, m.end_line) for m in csrc.modules if m.refines]
    out = []
    for h in res.holes:
        if h.file == frozen:
            out.append(Finding(h.file, h.line, "freeze-not-concrete",
                               "a refined statement is left without a body (its hole warning "
                               "is re-emitted, Δ44)"))
    diags = res.diagnostics
    for k, dg in enumerate(diags):
        if dg.severity != "error":
            continue
        related = []
        for r in diags[k + 1:]:
            if r.severity != "related":
                break
            related.append(r)
        in_refiner = dg.file == str(Path(cand).resolve()) and \
            any(a <= dg.line <= b for a, b in ranges)
        if dg.code == "W-D19":
            out.append(Finding(dg.file, dg.line, "freeze-refinement",
                               "a refining member adds or restates a requires (W-D19)"))
        elif dg.file == frozen or any(r.file == frozen for r in related) or in_refiner:
            out.append(Finding(dg.file, dg.line, "freeze-refinement",
                               "the candidate does not establish the frozen statement under "
                               "refinement"))
    if res.stage in ("parse", "resolve") and not out:
        out.append(Finding(str(cand), 0, "freeze-error",
                           f"the program does not {res.stage}; the refinement was not checked"))
    return out


# =====================================================================================
# Targets and projects
# =====================================================================================

@dataclass
class Program:
    target: Path              # the resolved target
    kind: str                 # project | files
    project: Path | None      # the dfyconfig.toml (kind project)
    files: list               # every root .dfy of the program (absolute)
    own: list                 # the target's own files (not given layers)
    options: dict             # the unit options in force
    root: Path | None         # the course root (holds MODULES.toml), if any
    module: str | None        # the module id, if known
    std: bool                 # the standard library is on
    path_map: list = field(default_factory=list)   # [(scratch prefix, original prefix)]
    scratch: Path | None = None   # a scratch copy of sources, deleted after the run

    def inputs(self):
        return [str(self.project)] if self.kind == "project" else [str(f) for f in self.files]

    def cli_options(self):
        """Unit options a `files` program passes on the command line."""
        if self.kind == "project":
            return []
        flags = []
        for k in ("standard-libraries", "manual-lemma-induction", "disable-nonlinear-arithmetic",
                  "isolate-assertions"):
            if self.options.get(k) is True:
                flags.append(f"--{k}")
        return flags


def course_root(path):
    """The nearest ancestor holding MODULES.toml and dafny/options, else None."""
    p = Path(path).resolve()
    for d in [p] + list(p.parents):
        if (d / "MODULES.toml").is_file() and (d / gu.OPTIONS_DIR).is_dir():
            return d
    return None


UNIT_PATH = re.compile(r"dafny/([QR])/([QR]\d\d)_[A-Za-z0-9]+/(?:[^/]+/)*[^/]+")
CHECKS_PATH = re.compile(r"dafny/checks/([QR]\d\d)_[^/]+\.dfy")
GIVEN_PATH = re.compile(r"dafny/given/([QR])/(?:QG|RG)_(A1b|[LA][1-7])_[^/]+\.dfy")


def _module_of(root, path):
    """The module whose units a course file belongs to: dafny/{Q,R}/<ID>_<Name>/…,
    dafny/checks/<ID>_*.dfy, or a given layer's first module (its options)."""
    try:
        rel = Path(path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None
    if m := UNIT_PATH.fullmatch(rel):
        return m.group(2)
    if m := CHECKS_PATH.fullmatch(rel):
        return m.group(1)
    if (m := GIVEN_PATH.fullmatch(rel)) and m.group(2) in gu.LAYER_DAFNY_TIER and \
            gu.layer_track(m.group(2)) == m.group(1):
        return gu.layer_first_module(m.group(2))
    return None


def _uses_std(paths):
    for p in paths:
        try:
            src = parse_file(p)
        except (OSError, UnicodeDecodeError):
            continue
        if any(name == "Std" or name.startswith("Std.") for _, name in src.imports):
            return True
    return False


GIVEN_MODULE = re.compile(r"(?:QG|RG)_(A1b|[LA][1-7])_[A-Za-z0-9_]+")


def _reaches_std_layer(paths):
    """True when a file imports a given layer module (`QG_L3_BigNat`) whose
    Dafny files are std tier (gen_units.LAYER_DAFNY_TIER): such a file can
    only build with the standard library on."""
    for p in paths:
        try:
            src = parse_file(p)
        except (OSError, UnicodeDecodeError):
            continue
        for _, name in src.imports:
            m = GIVEN_MODULE.fullmatch(name.split(".")[0])
            if m and gu.LAYER_DAFNY_TIER.get(m.group(1)) == "std":
                return True
    return False


def registry_tier(root, rel):
    """The import tier the registry declares for a course file (`[module.imports]`
    of the module that owns it: core | std | std-all), or None when no record
    declares it or the registry cannot be read (the tools that check the
    registry report that; here it only means "infer the tier")."""
    data, err = gu.load_registry(Path(root))
    if err or not isinstance(data, dict):
        return None
    for m in data.get("module") or []:
        imports = m.get("imports") if isinstance(m, dict) else None
        if isinstance(imports, dict) and isinstance(imports.get(rel), str):
            return imports[rel]
    return None


def file_tier(root, path, rel):
    """The Dafny tier a course file outside a unit builds in: its
    `[module.imports]` entry when the registry declares one (std-all builds
    as std; QPLAN §6 Q13), else std when the file imports Std or a std-tier
    given layer, else core."""
    declared = registry_tier(root, rel) if root is not None else None
    if declared in ("core", "std", "std-all"):
        return "core" if declared == "core" else "std"
    return "std" if _uses_std([path]) or _reaches_std_layer([path]) else "core"


def validate_project(project, root):
    """Refusal reasons for a project file (empty when acceptable)."""
    reasons = []
    try:
        with open(project, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        return [f"{common.display_path(project)}: unreadable project file ({e})"]
    for key in data:
        if key not in ("includes", "options"):
            reasons.append(f"{common.display_path(project)}: project key '{key}' is refused "
                           "(only includes and [options]; Δ10, G21)")
    inc = data.get("includes")
    if not isinstance(inc, list) or not inc or not all(isinstance(x, str) for x in inc):
        reasons.append(f"{common.display_path(project)}: includes must be a non-empty list of "
                       "globs")
    opts = data.get("options", {})
    if not isinstance(opts, dict):
        reasons.append(f"{common.display_path(project)}: [options] must be a table")
    else:
        reasons += [f"{common.display_path(project)}: [options] {e}"
                    for e in gu.option_errors(opts)]
    if root is not None:
        try:
            rel = project.resolve().relative_to(root).as_posix()
        except ValueError:
            rel = None
        if rel is not None and rel.startswith("dafny/"):
            data_reg, err = gu.load_registry(root)
            if err:
                reasons.append(f"cannot check {rel} against the generator: {err}")
            else:
                files, _, _ = gu.plan(root, data_reg)
                if rel not in files:
                    reasons.append(f"{rel}: unknown dfyconfig.toml — no non-planned unit "
                                   "produces it (scripts/gen_units.py)")
                elif project.read_text(encoding="utf-8") != files[rel]:
                    reasons.append(f"{rel}: edited dfyconfig.toml — it differs from "
                                   "scripts/gen_units.py's output")
    return reasons


def expand_includes(project):
    """The absolute files a project's includes name; a glob matching nothing is
    an error (Δ27)."""
    with open(project, "rb") as f:
        data = tomllib.load(f)
    base = project.parent
    files, empty = [], []
    for pat in data.get("includes", []):
        got = sorted(Path(os.path.normpath(x)) for x in globmod.glob(str(base / pat))
                     if x.endswith(".dfy"))
        if not got:
            empty.append(pat)
        files += [g for g in got if g not in files]
    return files, empty, data.get("options", {})


def program(target):
    """What `target` verifies as (a Program). Raises Refused. A specimen's
    Program holds a scratch copy (Program.scratch): pass it to discard() when
    done (verify, holes, audit, test and empty_body do)."""
    p = Path(target)
    if not p.exists():
        raise Refused(f"{target}: no such file or directory")
    p = p.resolve()
    if p.is_dir():
        if not (p / "dfyconfig.toml").is_file():
            raise Refused(f"{common.display_path(p)}: not a unit (no dfyconfig.toml)")
        p = p / "dfyconfig.toml"
    if p.name.endswith(".dfy.specimen"):
        return _specimen_program(p)
    root = course_root(p)
    if p.suffix == ".toml":
        if p.name != "dfyconfig.toml":
            raise Refused(f"{common.display_path(p)}: only project files named dfyconfig.toml "
                          "are used (W-D30)")
        return _project_program(p, p, root)
    if p.suffix != ".dfy":
        raise Refused(f"{common.display_path(p)}: not a Dafny file, unit or project")
    if (p.parent / "dfyconfig.toml").is_file():
        return _project_program(p, p.parent / "dfyconfig.toml", root)
    return _files_program(p, root)


def _project_program(target, project, root):
    reasons = validate_project(project, root)
    if reasons:
        raise Refused("; ".join(reasons))
    files, empty, opts = expand_includes(project)
    if empty:
        raise Refused(f"{common.display_path(project)}: includes glob(s) match no file: "
                      + ", ".join(empty) + " (Δ27)")
    if target.suffix == ".dfy" and target not in files:
        raise Refused(f"{common.display_path(target)}: not among its unit's includes")
    unit = project.parent
    own = [f for f in files if f.parent == unit]
    mid = _module_of(root, project) if root else None
    return Program(target, "project", project, files, own, dict(opts), root, mid,
                   opts.get("standard-libraries") is True)


def _files_program(path, root):
    mid = _module_of(root, path) if root else None
    files = [path]
    if mid:
        try:
            options, errs = gu.load_options(root)
        except Exception as e:  # noqa: BLE001 — a broken options file is a refusal
            raise Refused(f"cannot load {gu.OPTIONS_DIR}: {e}") from None
        if errs:
            raise Refused("; ".join(errs))
        rel = path.relative_to(root.resolve()).as_posix()
        given = GIVEN_PATH.fullmatch(rel)
        layer = given.group(2) if given else gu.expected_layer(mid)
        if given is not None:
            std = _uses_std([path]) or gu.LAYER_DAFNY_TIER[layer] == "std"
            tier = "std" if std else "core"
        else:
            tier = file_tier(root, path, rel)
        chain = gu.layer_chain(layer)
        for l in chain:
            if tier != "std" and gu.LAYER_DAFNY_TIER[l] != "core":
                continue
            d = root / gu.dafny_given_dir(mid[0])
            got = sorted(d.glob(gu.dafny_layer_glob(l))) if d.is_dir() else []
            files += [g.resolve() for g in got if g.resolve() not in files]
        opts = gu.unit_options(options, tier, mid)
    else:
        std = _uses_std([path])
        opts = {"resource-limit": pins()["resource_limit"]}
        if std:
            opts["standard-libraries"] = True
    return Program(path, "files", None, files, [path], opts, root, mid,
                   opts.get("standard-libraries") is True)


def _specimen_program(p):
    tmp = common.scratch_dir("dafny-specimen")
    copy = tmp / p.name[: -len(".specimen")]
    shutil.copyfile(p, copy)
    std = _uses_std([copy])
    opts = {"resource-limit": pins()["resource_limit"]}
    if std:
        opts["standard-libraries"] = True
    return Program(p, "files", None, [copy], [copy], opts, course_root(p), None, std,
                   [(str(copy), str(p))], tmp)


def _scratch_copy(prog, tag):
    """A copy of every input of `prog` under a fresh scratch dir, layout kept
    (Δ32: compiles never run beside the sources). Returns (copy Program, dir)."""
    tmp = common.scratch_dir(f"dafny-{tag}")
    srcs = list(prog.files) + ([prog.project] if prog.project else [])
    base = Path(os.path.commonpath([str(Path(s).parent) for s in srcs]))
    tree = tmp / "src"
    mapping = {}
    for s in srcs:
        dst = tree / Path(s).relative_to(base)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(s, dst)
        mapping[Path(s)] = dst
    orig_map = prog.path_map or []
    back = lambda s: next((o for c, o in orig_map if c == s), s)  # noqa: E731
    path_map = [(str(dst), back(str(src))) for src, dst in mapping.items()]
    cp = Program(prog.target, prog.kind, mapping.get(prog.project) if prog.project else None,
                 [mapping[Path(f)] for f in prog.files], [mapping[Path(f)] for f in prog.own],
                 dict(prog.options), prog.root, prog.module, prog.std, path_map, tree)
    return cp, tmp


def discard(prog):
    """Delete a program's scratch copy of sources. Runs keep only their logs
    (cmd, stdout, stderr, exit, task CSV): a scratch copy of a reference twin
    would otherwise leave answer text outside every guarded path."""
    if prog is not None and prog.scratch is not None:
        shutil.rmtree(prog.scratch, ignore_errors=True)


# =====================================================================================
# The refusal list (Δ10, Δ17, Δ18; spec §11.4 G6–G8, G10, G14–G16, G19–G22)
# =====================================================================================

REFUSED_FLAGS = {
    "--no-verify": "skips verification (G7)",
    "--allow-warnings": "makes holes non-fatal; the wrapper sets it (G6)",
    "--allow-axioms": "silences hole warnings (Δ6, G6)",
    "--allow-external-contracts": "silences {:extern} warnings (G6)",
    "--allow-deprecation": "an --allow-* option (G6)",
    "--boogie": "Boogie pass-through (Δ17, G14)",
    "--solver-option": "solver pass-through, internal-only (Δ17, G14)",
    "--solver-plugin": "replaces the solver (G15)",
    "--solver-path": "the wrapper pins the bundled z3-4.12.1 (Δ10, G15, G22)",
    "--solver-log": "internal-only dump (Δ17)",
    "--plugin": "loads arbitrary code (G16)",
    "--prelude": "replaces the verifier's prelude (unsound)",
    "--library": "library inputs are not verified (Δ15, G10)",
    "--resource-limit": "the wrapper pins the course limit (Δ56)",
    "--verification-time-limit": "time limits are not verdicts; 0 is unbounded (Δ10, G20)",
    "--cores": "the wrapper pins --cores (Δ59, CLAUDE.md §Resources)",
    "--find-project": "the wrapper names the project explicitly (Δ10)",
    "--stdin": "the wrapper names its inputs explicitly",
    "--dont-verify-dependencies": "skips verifying dependencies",
    "--relax-definite-assignment": "weakens the checks",
    "--default-function-opacity": "a unit option, set only by the unit",
    "--manual-lemma-induction": "a unit option, set only by the unit (Δ30, Δ45)",
    "--disable-nonlinear-arithmetic": "a unit option, set only by the unit (Δ30)",
    "--standard-libraries": "a unit option, set only by the unit (Δ34)",
    "--json-output": "the wrapper chooses the output channel",
    "--log-format": "the wrapper chooses the output channel",
    "--use-basename-for-filename": "the wrapper chooses the output channel",
    "--error-limit": "changes what is reported",
    "--test-assumptions": "experimental",
    "--bprint": "internal-only dump (Δ17)",
    "--print": "internal-only dump (Δ17)",
    "--rprint": "internal-only dump (Δ17)",
    "--pprint": "internal-only dump (Δ17)",
    "--sprint": "internal-only dump (Δ17)",
    "--warn-contradictory-assumptions": "internal-only (Δ16)",
}
LOOP_ONLY_FLAGS = {"--filter-symbol": True, "--filter-position": True,
                   "--isolate-assertions": False, "--analyze-proofs": False,
                   "--extract-counterexample": False}


def check_args(args, gate):
    """Refusal reasons for Dafny command-line arguments a caller wants to pass
    through (empty when every argument is acceptable). The gate accepts none:
    it runs only the pinned flags. The learner loop accepts the filters,
    --isolate-assertions, --analyze-proofs and --extract-counterexample."""
    reasons, k, args = [], 0, list(args)
    while k < len(args):
        a = args[k]
        flag, _, inline = a.partition("=")
        if re.fullmatch(r"/[A-Za-z][A-Za-z0-9]*(?::.*)?", a):   # /compile:0, not /home/x.dfy
            reasons.append(f"{a}: the legacy CLI is refused (Δ18, G19)")
        elif flag in REFUSED_FLAGS:
            reasons.append(f"{flag}: refused — {REFUSED_FLAGS[flag]}")
        elif flag in LOOP_ONLY_FLAGS:
            if gate:
                reasons.append(f"{flag}: refused in the gate (filters and per-assertion "
                               "splitting change what is verified; Δ10, Δ11, G8)")
            if LOOP_ONLY_FLAGS[flag] and not inline:
                k += 1
        elif a.startswith("-"):
            reasons.append(f"{a}: not a wrapper option (only the pinned flags run)")
        k += 1
    return reasons


# =====================================================================================
# Output parsing
# =====================================================================================

@functools.lru_cache(maxsize=1)
def _messages():
    return {v: k for k, v in pins()["messages"].items()}


@functools.lru_cache(maxsize=1)
def _patterns():
    return {k: re.compile(v) for k, v in pins()["patterns"].items()}


def _map_path(path, path_map, cwd):
    if path.startswith("file://"):
        path = urllib.parse.unquote(urllib.parse.urlparse(path).path)
    p = Path(path)
    if not p.is_absolute():
        cand = Path(cwd) / p
        if cand.exists():
            p = cand
        else:
            return path   # a tool-internal file (the bundled standard library)
    s = os.path.normpath(str(p))
    for scratch, orig in sorted(path_map, key=lambda x: -len(x[0])):
        if s == scratch:
            return orig
        if s.startswith(scratch.rstrip("/") + "/"):
            return orig.rstrip("/") + s[len(scratch.rstrip("/")):]
    return s


TEMPLATE_CODES = ("W-D06", "W-D11", "W-D12", "W-D20", "W-D25", "W-D26")


def _code_for(message, errid=""):
    """The pinned wording id of a message (exact text, then a template), else
    the tool's own id, else ""."""
    code = _messages().get(message)
    if code:
        return code
    pats = _patterns()
    for k in TEMPLATE_CODES:
        if pats[k].match(message):
            return k
    return errid or ""


def _fill(template, args):
    return re.sub(r"\{(\d+)\}", lambda m: str(args[int(m.group(1))])
                  if int(m.group(1)) < len(args) else m.group(0), template)


SEVERITY = {1: "error", 2: "warning", 3: "info", 4: "hint"}


def parse_json_lines(text, path_map=(), cwd="."):
    """(diagnostics, status lines, error lines) from `--json-output`."""
    diags, status, errors = [], [], []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            status.append(raw)
            continue
        kind, val = obj.get("type"), obj.get("value")
        if kind == "diagnostic" and isinstance(val, dict):
            diags += _json_diag(val, path_map, cwd)
        elif kind == "status":
            # "Results File: <csv>" echoes the wrapper's own --log-format target
            status += [x for x in str(val).splitlines()
                       if x.strip() and not x.startswith("Results File: ")]
        elif kind == "error":
            errors += [x for x in str(val).splitlines() if x.strip()]
    return diags, status, errors


def _json_diag(v, path_map, cwd):
    loc = v.get("location") or {}
    rng = (loc.get("range") or {}).get("start") or {}
    f = _map_path(loc.get("uri") or loc.get("filePath") or loc.get("filename") or "", path_map, cwd)
    msg = _fill(v.get("defaultFormatMessage") or "", v.get("arguments") or [])
    code = _code_for(msg, v.get("errorId") or "")
    out = [Diag(f, int(rng.get("line", 0)), int(rng.get("character", -1)) + 1,
                SEVERITY.get(v.get("severity"), "info"), msg, code)]
    for rel in v.get("relatedInformation") or []:
        rl = rel.get("location") or {}
        rs = (rl.get("range") or {}).get("start") or {}
        rf = _map_path(rl.get("uri") or rl.get("filePath") or rl.get("filename") or "",
                       path_map, cwd)
        rmsg = _fill(rel.get("defaultFormatMessage") or "", rel.get("arguments") or [])
        out.append(Diag(rf, int(rs.get("line", 0)), int(rs.get("character", -1)) + 1,
                        "related", rmsg, code))
    return out


TEXT_SEVERITY = {"Error": "error", "Warning": "warning", "Info": "info",
                 "Related location": "related"}


def parse_text(text, path_map=(), cwd="."):
    """(diagnostics, other lines) from text output with --show-snippets false."""
    pat = _patterns()["text-diagnostic"]
    diags, other, last_code = [], [], ""
    for line in text.splitlines():
        m = pat.match(line)
        if m:
            sev = TEXT_SEVERITY[m.group("severity")]
            msg = m.group("message")
            code = _code_for(msg) if sev != "related" else last_code
            if sev != "related":
                last_code = code
            diags.append(Diag(_map_path(m.group("file"), path_map, cwd), int(m.group("line")),
                              int(m.group("col")) + 1, sev, msg, code))
        elif line.strip():
            other.append(line)
    return diags, other


def parse_csv_log(path):
    """[(display name, outcome, resource count)] from a --log-format csv file."""
    if not Path(path).is_file():
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                rc = int(r.get("TestResult.ResourceCount") or 0)
            except ValueError:
                rc = 0
            rows.append((r.get("TestResult.DisplayName", ""), r.get("TestResult.Outcome", ""), rc))
    return rows


def _symbol_of(display):
    return display.split(" (", 1)[0].strip()


def per_symbol_status(rows, diags):
    """{symbol: verified | failed | inconclusive} from CSV tasks and the
    out-of-resource / time-out diagnostics (Δ39: tasks per symbol and kind)."""
    pats = _patterns()
    inconclusive = set()
    for d in diags:
        for key in ("W-D11", "W-D12"):
            m = pats[key].match(d.message)
            if m:
                inconclusive.add(m.group("name"))
    out = {}
    for display, outcome, _ in rows:
        sym = _symbol_of(display)
        ok = outcome == "Passed"
        prev = out.get(sym, "verified")
        out[sym] = "verified" if ok and prev == "verified" else "failed"
    for sym, st in out.items():
        if st == "failed" and sym in inconclusive:
            out[sym] = "inconclusive"
    return out


def holes_from(diags, label_files=True):
    """Tool-counted holes: the exact pinned wordings W-D01..W-D03, deduplicated
    by position (Δ1, Δ5)."""
    seen, out = set(), []
    for d in diags:
        if d.severity != "warning" or d.code not in HOLE_CODES:
            continue
        key = (d.file, d.line, d.col)
        if key in seen:
            continue
        seen.add(key)
        out.append(Hole(d.file, d.line, d.col, HOLE_CODES[d.code],
                        _label(d.file, d.line) if label_files else ""))
    return out


_LABEL_CACHE: dict = {}


def _label(file, line):
    """The item id whose block holds `line`, else the enclosing declaration."""
    p = Path(file)
    if not p.is_file():
        return ""
    try:
        key = (str(p), p.stat().st_mtime_ns)
        if key not in _LABEL_CACHE:
            text = p.read_text(encoding="utf-8")
            items, _ = ci.parse_items(str(p), text)
            _LABEL_CACHE[key] = (items, parse_source(text, str(p)))
        items, src = _LABEL_CACHE[key]
    except (OSError, UnicodeDecodeError):
        return ""
    for it in items:
        if it["line_start"] <= line <= it["line_end"]:
            return it["id"]
    best = None
    for d in src.decls:
        if d.kind in METHODLIKE and d.line <= line <= max(d.end_line, d.line) and \
                (best is None or d.line >= best.line):
            best = d
    return best.qual if best else ""


# =====================================================================================
# Running Dafny
# =====================================================================================

def solver_names():
    """The bundled solvers' names (pins.toml [dafny.solvers]), the pinned one
    first (QPLAN §6 Q29)."""
    names = list((pins().get("solvers") or {}).keys())
    pinned = PurePosixPath(pins()["solver"]).name.removeprefix("z3-")
    if pinned in names:
        names.remove(pinned)
    return [pinned] + names


_SOLVER_CHECKED: dict = {}


def solver_path(name=None):
    """The path of a bundled solver by name (None: the pinned one). Raises
    Refused for a name the pins do not list, and common.ToolchainError when
    the binary is missing or its sha256 is not the pinned one (checked once
    per process)."""
    tc = common.toolchain("dafny")
    if name is None:
        return tc["dafny_z3"]
    table = pins().get("solvers") or {}
    if name not in table:
        raise Refused(f"solver {name!r}: not a solver bundled with the pinned Dafny; one of "
                      + ", ".join(solver_names()) + " (QPLAN §6 Q29)")
    entry = table[name]
    path = Path(tc["dafny_root"]) / entry["path"]
    if name not in _SOLVER_CHECKED:
        if not path.is_file():
            raise common.ToolchainError(f"the bundled solver {name} is missing: {path}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            raise common.ToolchainError(f"the bundled solver {name} at {path} has sha256 "
                                        f"{digest}, not the pinned {entry['sha256']}")
        _SOLVER_CHECKED[name] = path
    return _SOLVER_CHECKED[name]


def _base_flags(gate, cores=True, solver=None):
    p = pins()
    tc = common.toolchain("dafny")
    flags = ["--resource-limit", str(p["resource_limit"])]
    if cores:
        flags += ["--cores", str(p["cores"])]
    if solver is not None and gate:
        raise Refused("the gate keeps the pinned solver (Δ10): another solver is refused")
    z3 = tc["dafny_z3"] if solver is None else solver_path(solver)
    flags += ["--solver-path", str(z3)] + list(p["always"])
    flags += list(p["gate"] if gate else p["loop"])
    return flags


def _run(argv, tag, cwd=None, raw=None):
    p = pins()
    raw = Path(raw) if raw else common.scratch_dir(f"dafny-{tag}")
    work = Path(cwd) if cwd else raw
    rc, so, se = common.run_capped(argv, p["mem_gb"], p["wall_clock_s"], env=common.default_env(),
                                   cwd=work, pool="dafny", out_dir=raw)
    return rc, so.read_text(encoding="utf-8", errors="replace"), \
        se.read_text(encoding="utf-8", errors="replace"), raw


def _refused(target, message, lang=LANG):
    return Result(lang, str(target), None, "refused", "cli",
                  findings=[Finding(str(target), 0, "refused", message)])


def _toolchain_error(target, e):
    return Result(LANG, str(target), None, "error", "cli",
                  findings=[Finding(str(target), 0, "toolchain", str(e))])


def _killed_or_clock(rc):
    if common.is_killed(rc):
        return "killed(memory)"
    if rc == common.WALL_CLOCK_EXIT:
        return "inconclusive"
    return None


def verify(target, gate=False, symbol=None, seed=None, isolate=False, extra_args=(),
           solver=None):
    """Verify a unit, a file or a specimen with the pinned flags.

    gate=True is the done gate: a fresh toolchain check (Δ10), --allow-warnings
    false (holes and every warning fail), no filters (a symbol is refused), no
    per-assertion isolation, and a positive verified count (Δ11). seed=S runs
    `measure-complexity --random-seed S --mutations 1` (Δ17, Δ59; its count is
    the CSV's passed tasks). symbol="Mod.Name" verifies that symbol only
    (--filter-symbol 'Mod.Name.', Δ11) and fails if it did not run.
    extra_args are pass-through Dafny arguments; check_args judges them (the
    gate takes none; the loop takes the filters, --isolate-assertions,
    --analyze-proofs, --extract-counterexample). Under --filter-position the
    count is of assertions (W-D08), never comparable with task counts (Δ39;
    count_unit()). solver names another bundled Z3 (solver_names(); QPLAN §6
    Q29: a measurement, never a gate): refused with gate=True (Δ10).

    verdicts: verified (exit 0, count > 0, symbol present); failed (verification
    errors, parse or resolution errors, warnings in the gate, nothing verified
    in the gate or in any filtered run); inconclusive (only out-of-resource or
    time-out results, or the wall-clock kill); killed(memory) (137/143);
    refused (no tool ran); error (CLI errors, a missing solver, unparseable
    output)."""
    if gate and (symbol or isolate):
        return _refused(target, "the gate verifies the whole unit: filters and per-assertion "
                                "isolation are refused (Δ10, Δ11, G8)")
    if gate and solver is not None:
        return _refused(target, "the gate keeps the pinned solver (Δ10): another bundled "
                                "solver is a measurement, never a gate (QPLAN §6 Q29)")
    reasons = check_args(extra_args, gate)
    if reasons:
        return _refused(target, "; ".join(reasons))
    try:
        common.toolchain("dafny", fresh=gate)
        if solver is not None:
            solver_path(solver)
        prog = program(target)
    except Refused as e:
        return _refused(target, str(e))
    except common.ToolchainError as e:
        return _toolchain_error(target, e)
    try:
        return _verify_program(prog, gate=gate, symbol=symbol, seed=seed, isolate=isolate,
                               extra_flags=[str(a) for a in extra_args], target=str(target),
                               solver=solver)
    finally:
        discard(prog)


def _verify_program(prog, gate=False, symbol=None, seed=None, isolate=False, extra_inputs=(),
                    extra_flags=(), target=None, raw=None, solver=None):
    p = pins()
    tc = common.toolchain("dafny")
    raw = Path(raw) if raw else common.scratch_dir("dafny-verify")
    log = raw / "tasks.csv"
    if seed is None:
        argv = [str(tc["dafny"]), "verify"]
    else:
        argv = [str(tc["dafny"]), "measure-complexity", "--random-seed", str(int(seed)),
                "--mutations", str(p["seed_mutations"])]
    argv += prog.inputs() + [str(x) for x in extra_inputs]
    argv += ["--json-output"] + _base_flags(gate, solver=solver) + prog.cli_options() \
        + list(extra_flags)
    argv += ["--log-format", f"csv;LogFileName={log}"]
    if isolate:
        argv.append("--isolate-assertions")
    if symbol:
        argv += ["--filter-symbol", symbol.rstrip(".") + "."]
    rc, out, err, raw = _run(argv, "verify", raw=raw)
    diags, status, errors = parse_json_lines(out, prog.path_map, raw)
    rows = parse_csv_log(log)
    res = Result(LANG, target or str(prog.target), rc, "error", "verify", None,
                 holes_from(diags), _sorted(diags), [], per_symbol_status(rows, diags), str(raw),
                 argv)
    _classify_verify(res, status + errors, rows, gate, symbol, seed is not None)
    return res


def _sorted(diags):
    """Diagnostics in position order (Dafny's own order is stable but not source
    order, Δ36); a related location stays right after its diagnostic, and a
    diagnostic printed twice at one position (@VerifyOnly, {:only}: W-D16,
    Δ5) is kept once."""
    groups, cur = [], None
    for d in diags:
        if d.severity == "related" and cur is not None:
            cur.append(d)
        else:
            cur = [d]
            groups.append(cur)
    unique = list(dict.fromkeys(tuple(g) for g in groups))
    unique.sort(key=lambda g: (g[0].file, g[0].line, g[0].col, g[0].severity, g[0].message))
    return [d for g in unique for d in g]


def resource_counts(result):
    """{symbol: the largest resource count of its tasks} from a verify run's CSV
    task log. Quote a count only from a seeded run (Δ59: plain runs are not
    fully reproducible)."""
    if not result.raw_dir:
        return {}
    out = {}
    for display, _, rc in parse_csv_log(Path(result.raw_dir) / "tasks.csv"):
        sym = _symbol_of(display)
        out[sym] = max(out.get(sym, 0), rc)
    return out


def normalized(diags, base):
    """Golden-ready lines `<path>:<line>:<col>: <severity>: <message>`: paths
    relative to `base` (a tool-internal file keeps its bare name; the absolute
    uri never appears, Δ36), in position order, duplicates dropped."""
    out = []
    for d in diags:
        try:
            f = Path(d.file).resolve().relative_to(Path(base).resolve()).as_posix() \
                if Path(d.file).is_absolute() else d.file
        except ValueError:
            f = Path(d.file).name
        out.append(f"{f}:{d.line}:{d.col}: {d.severity}: {d.message}")
    return list(dict.fromkeys(out))


LABEL = re.compile(r"//\s*\[([a-z0-9]+)\]\s*$")


def failing_labels(result, path):
    """The `// [x]` labels (spec §3.8.6 `obligation` specimens) on the lines of
    `path` where the run reported an error or its related location. Dafny
    assumes a failed assertion afterwards (Δ38), so a specimen keeps each
    labelled obligation independent of the earlier ones."""
    path = str(Path(path).resolve())
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    out, last_error = set(), False
    for d in result.diagnostics:
        if d.severity == "error":
            last_error = True
        elif d.severity != "related":
            last_error = False
        if d.file != path or not (d.severity == "error" or (d.severity == "related" and
                                                            last_error)):
            continue
        if 1 <= d.line <= len(lines) and (m := LABEL.search(lines[d.line - 1])):
            out.add(m.group(1))
    return out


FILTER_FLAGS = ("--filter-symbol", "--filter-position")


def _flag_in(argv, flag):
    return any(a == flag or a.startswith(flag + "=") for a in argv)


def count_unit(result):
    """What `result.verified_count` counts (Δ39): "assertions" under
    --filter-position (W-D08), "passed-tasks" for a seeded measure-complexity
    run (its CSV's passed rows), else "tasks" (W-D07). Counts of different
    units are never compared."""
    if _flag_in(result.cmd, "--filter-position"):
        return "assertions"
    if "measure-complexity" in result.cmd[1:2]:
        return "passed-tasks"
    return "tasks"


def _classify_verify(res, lines, rows, gate, symbol, seeded):
    pats, msgs = _patterns(), pins()["messages"]
    kc = _killed_or_clock(res.exit_code)
    summary = None
    for line in lines:
        # W-D07 counts tasks; W-D08 (--filter-position) counts assertions (Δ39)
        if m := pats["W-D07"].match(line.strip()) or pats["W-D08"].match(line.strip()):
            summary = m
    filtered = bool(symbol) or any(_flag_in(res.cmd, f) for f in FILTER_FLAGS)
    if seeded:
        res.verified_count = sum(1 for _, o, _ in rows if o == "Passed")
    elif summary:
        res.verified_count = int(summary.group("verified"))
    errs = [d for d in res.diagnostics if d.severity == "error"]
    if kc:
        res.verdict = kc
        if kc == "inconclusive":
            res.diagnostics.append(Diag(res.target, 0, 0, "error",
                                        f"wall-clock safety kill after {pins()['wall_clock_s']} s "
                                        "(Δ58): counted as a failure, never a verdict", "Δ58"))
        return
    rc = res.exit_code
    if rc == 0:
        if not summary and not seeded:
            res.verdict = "error"
            res.findings.append(Finding(res.target, 0, "no-summary",
                                        "the verifier printed no summary line"))
            return
        res.verdict = "verified"
        if symbol and not any(s == symbol.rstrip(".") or s.endswith("." + symbol.rstrip("."))
                              for s in res.per_symbol):
            res.verdict = "failed"
            res.findings.append(Finding(res.target, 0, "symbol-not-verified",
                                        f"{symbol}: no verification task ran for it (Δ11)"))
        elif not res.verified_count and filtered:
            res.verdict = "failed"
            res.findings.append(Finding(res.target, 0, "filter-matched-nothing",
                                        "the filter matched nothing: 0 verified, and exit 0 "
                                        "alone is not a pass (Δ11, G8)"))
        elif not res.verified_count:
            res.findings.append(Finding(res.target, 0, "nothing-verified",
                                        "0 verification tasks ran: exit 0 alone is not a pass "
                                        "(Δ11)"))
            if gate:
                res.verdict = "failed"
        return
    if rc == 1:
        res.verdict, res.stage = "error", "cli"
        return
    if rc == 2:
        parse = [d for d in errs if d.code.startswith("p_") or "parse error" in d.message]
        if any(pats["W-D13-parse"].match(x) for x in lines) or parse:
            res.verdict, res.stage = "failed", "parse"
        elif any(pats["W-D13-resolution"].match(x) for x in lines) or errs:
            res.verdict, res.stage = "failed", "resolve"
        elif any(x.strip() == msgs["W-D04"] for x in lines):
            res.verdict, res.stage = "failed", "verify"
            res.findings.append(Finding(res.target, 0, "warnings-fail-gate",
                                        "warnings fail the gate (W-D04): holes and every other "
                                        "warning must be gone"))
        else:
            res.verdict, res.stage = "error", "cli"
        return
    if rc == 4:
        if any(d.message == msgs["W-D24"] for d in res.diagnostics) or \
                any(x.strip() == msgs["W-D24"] for x in lines):
            res.verdict, res.stage = "error", "cli"
            return
        hard = [d for d in errs if not (pats["W-D11"].match(d.message) or
                                        pats["W-D12"].match(d.message))]
        res.verdict = "failed" if hard or not errs else "inconclusive"
        if summary and not errs and (summary.groupdict().get("oor") or
                                     summary.groupdict().get("timeouts")):
            res.verdict = "inconclusive"
        return
    res.verdict = "error"


# --- holes ---------------------------------------------------------------------------------

def holes(target):
    """The tool-counted holes of a unit or file: `dafny resolve` (no solver) with
    the learner-loop flags, warnings matched against the exact pinned wordings
    W-D01, W-D02, W-D03 and deduplicated by position (Δ1, Δ5). Silent hole kinds
    are the lint's (Δ3). Raises Refused, or HoleCountError when the program does
    not resolve (a count from a broken program is not a count)."""
    prog = program(target)
    tc = common.toolchain("dafny")
    p = pins()
    argv = [str(tc["dafny"]), "resolve"] + prog.inputs() + ["--show-snippets", "false"]
    argv += list(p["always"]) + list(p["loop"])
    if prog.kind == "files" and prog.std:
        argv.append("--standard-libraries")
    try:
        rc, out, err, raw = _run(argv, "resolve")
    finally:
        discard(prog)
    diags, other = parse_text(out, prog.path_map, raw)
    res = Result(LANG, str(target), rc, "verified" if rc == 0 else "failed", "resolve", None,
                 holes_from(diags), _sorted(diags), [], {}, str(raw), argv)
    kc = _killed_or_clock(rc)
    if kc:
        res.verdict = kc
        raise HoleCountError(f"{target}: the resolver run was {kc}", res)
    if rc != 0 or any(d.severity == "error" for d in diags):
        res.verdict = "failed" if rc == 2 else "error"
        raise HoleCountError(f"{target}: the program does not resolve (exit {rc}); "
                             f"holes cannot be counted", res)
    return res.holes


# --- audit ---------------------------------------------------------------------------------

def audit(target, lint_mode="learner", given_role=False):
    """The assumption audit (Δ4): `dafny audit` over the whole program with every
    file a root (a unit's project; a file plus its given chain), every W-D14 row
    a finding, plus the lint over the target's own files in `lint_mode`
    (default learner: the silent kinds audit misses, abstract-module members,
    `expect` outside tests, `include`). The lint sees the whole program, so a
    given layer's frozen abstract spec that the program refines in full is not
    a finding (lint's given role: automatic for a course tree's given layers
    and declared statements; lint_mode="given" grants it to every own file, for
    an out-of-tree copy, and given_role=True does so in any lint mode). Rows
    inside the bundled standard library are the
    pinned toolchain's trusted base and are not findings, but their count is
    pinned (a different count is). A bodyless member of a trait that a class of
    its file implements in full is a statement, not a finding (DV5c,
    implemented_traits). An audit that could not run is a finding."""
    if lint_mode not in MODES:
        raise ValueError(f"lint mode must be one of {', '.join(MODES)}, not {lint_mode!r}")
    try:
        prog = program(target)
    except Refused as e:
        return [Finding(str(target), 0, "refused", str(e))]
    tc = common.toolchain("dafny")
    p = pins()
    argv = [str(tc["dafny"]), "audit"] + prog.inputs() + list(p["always"])
    if prog.kind == "files" and prog.std:
        argv.append("--standard-libraries")
    try:
        rc, out, err, raw = _run(argv, "audit")
    except BaseException:
        discard(prog)
        raise
    findings = audit_findings(out, prog, raw)
    statements = _implemented_trait_lines(prog, raw)
    findings = [f for f in findings if not (f.kind.startswith("audit-bodyless") and
                                            (str(Path(f.file).resolve()), f.line) in statements)]
    kc = _killed_or_clock(rc)
    if kc or rc != 0:
        findings.append(Finding(str(target), 0, "audit-error",
                                f"the audit did not run to completion ({kc or f'exit {rc}'}); "
                                f"raw output: {raw}"))
    try:
        back = lambda fs: [Path(_map_path(str(f), prog.path_map, raw)) for f in fs]  # noqa: E731
        findings += lint(back(prog.own), lint_mode, context=back(prog.files),
                         given_role=given_role)
    finally:
        discard(prog)
    return sorted(set(findings), key=lambda x: (x.file, x.line, x.kind, x.message))


def _implemented_trait_lines(prog, cwd):
    """{(resolved file, line)} of the bodyless members of the traits that a class
    of the same own file implements in full (implemented_traits; DV5c). `dafny
    audit` reports each such member as a bodyless declaration, but the class's
    member is verified against it: a statement, not an assumption. Every other
    bodyless row stays a finding."""
    out = set()
    for f in prog.own:
        path = Path(_map_path(str(f), prog.path_map, cwd))
        try:
            src = parse_source(Path(f).read_text(encoding="utf-8"), str(path))
        except Exception:  # noqa: BLE001 — an unparsable file keeps every audit row
            continue
        impl = implemented_traits(src)
        out |= {(str(path.resolve()), d.line) for d in src.decls
                if d.container in impl and d.kind in METHODLIKE and d.body is None}
    return out


def audit_findings(text, prog, cwd):
    pats = _patterns()
    issues = {v: k for k, v in pins()["audit_issues"].items()}
    stdlib = set(pins()["stdlib_files"])
    out, rows, std_rows, summary = [], 0, 0, None
    for line in text.splitlines():
        if m := pats["W-D14-summary"].match(line.strip()):
            summary = int(m.group("n"))
            continue
        m = pats["W-D14-row"].match(line)
        if not m:
            continue
        rows += 1
        if m.group("file") in stdlib:
            std_rows += 1
            continue
        kind = issues.get(m.group("issue"), "other")
        out.append(Finding(_map_path(m.group("file"), prog.path_map, cwd), int(m.group("line")),
                           f"audit-{kind}", f"{m.group('name')}: {m.group('issue')}"))
    target = str(prog.target)
    if summary is None:
        out.append(Finding(target, 0, "audit-error", "no auditor summary line (W-D14)"))
    elif summary != rows:
        out.append(Finding(target, 0, "audit-error",
                           f"the auditor reported {summary} findings but {rows} rows parsed"))
    want = pins()["stdlib_audit_rows"] if prog.std else 0
    if summary is not None and std_rows != want:
        out.append(Finding(target, 0, "audit-stdlib-drift",
                           f"{std_rows} audit rows inside the standard library, pinned {want}"))
    return out


# --- test ------------------------------------------------------------------------------------

def test(target, names=None):
    """Compiled checks: `dafny test --target py` in a scratch copy (Δ32), with the
    learner-loop flags (tests may run beside open proof holes, Δ2). names: test
    methods (qualified, or bare names matched as `*.Name`) → an anchored
    --methods-to-test regex; each must report PASSED. With no names, at least one
    test must run (Δ11, Δ43: a misspelled {:tset} never runs).
    per_symbol: {qualified test name: passed | failed}."""
    try:
        tc = common.toolchain("dafny")
        prog = program(target)
    except Refused as e:
        return _refused(target, str(e))
    except common.ToolchainError as e:
        return _toolchain_error(target, e)
    p = pins()
    cp, tmp = _scratch_copy(prog, "test")
    argv = [str(tc["dafny"]), "test", "--target", p["test_target"]] + cp.inputs()
    argv += ["--show-snippets", "false"] + _base_flags(False) + cp.cli_options()
    names = list(names or [])
    if names:
        alts = [re.escape(n) if "." in n else r"(?:.*\.)?" + re.escape(n) for n in names]
        argv += ["--methods-to-test", "^(?:" + "|".join(alts) + ")$"]
    try:
        rc, out, err, raw = _run(argv, "test", cwd=tmp / "src", raw=tmp)
        return _parse_test(out, rc, cp, raw, str(target), argv, names)
    finally:
        discard(cp)     # the sources and the compiled <stem>-py/ output (Δ32)
        discard(prog)


# W-D21 status words. The runner prints "<Qualified.Name>: " before a test and the
# status after it, so a test that prints puts its own output in between (captured
# from the pin, fixtures/dafny/captured/test_print_*.txt):
#   Name: <output>\nPASSED        Name: <output>PASSED  (output without a newline)
#   Name: <output>\nFAILED\n\t<file>(l,c): <message>
TEST_STATUS = {"PASSED": "passed", "FAILED": "failed"}
_TEST_START = re.compile(r"^(?P<name>[^\s:()]+): (?P<rest>.*)$")
_TEST_STATUS_END = re.compile(r"(?P<status>" + "|".join(TEST_STATUS) + r")$")


def _test_statuses(out):
    """{qualified test name: passed | failed} from `dafny test` stdout (W-D21, Δ43).

    Results come only after the verifier's first summary line (W-D07; the lines
    before it are diagnostics). A test opens at "<Name>: " and closes at the first
    line that ends in PASSED or FAILED, its own output included (a printing test,
    above); the pinned one-line form `<Name>: PASSED|FAILED` is the case with no
    output. A FAILED read after a test closed and before the next one opens still
    marks it failed, so a test whose output ends a line with PASSED cannot hide its
    own failure. A test that opened and never reported (the run died) is failed.
    Per-test attribution trusts a test's output not to forge "<Other>: PASSED"; the
    verdict never rests on it alone (it also needs exit 0, and `dafny test` exits 3
    when any test fails)."""
    pats = _patterns()
    lines = out.splitlines()
    begin = next((i + 1 for i, x in enumerate(lines) if pats["W-D07"].match(x.strip())), 0)
    per, cur, closed = {}, None, None

    def status_at_end(text):
        m = _TEST_STATUS_END.search(text.rstrip())
        return TEST_STATUS[m.group("status")] if m else None

    for line in lines[begin:]:
        s = line.strip()
        if pats["W-D21-detail"].match(line):
            continue
        if pats["W-D21-halted"].match(s):
            if cur is not None:
                per[cur], cur = "failed", None
            continue
        if cur is not None:
            st = status_at_end(line)
            if st:
                per[cur], closed, cur = st, cur, None
            continue
        if m := pats["W-D21-result"].match(s):
            closed = m.group("name")
            per[closed] = TEST_STATUS[m.group("status")]
            continue
        m = _TEST_START.match(line)
        if m and not pats["text-diagnostic"].match(s):
            cur = m.group("name")
            st = status_at_end(m.group("rest"))
            if st:
                per[cur], closed, cur = st, cur, None
            continue
        if closed is not None and status_at_end(line) == "failed":
            per[closed] = "failed"
    if cur is not None:
        per[cur] = "failed"
    return per


def _parse_test(out, rc, prog, raw, target, argv, names):
    pats, msgs = _patterns(), pins()["messages"]
    diags, other = parse_text(out, prog.path_map, Path(raw) / "src")
    per, findings = _test_statuses(out), []
    summary = None
    for line in out.splitlines():
        s = line.strip()
        if m := pats["W-D07"].match(s):
            summary = m
        elif m := pats["W-D21-detail"].match(line):
            diags.append(Diag(_map_path(m.group("file"), prog.path_map, Path(raw) / "src"),
                              int(m.group("line")), int(m.group("col")) + 1, "error",
                              m.group("message"), "W-D21"))
        elif m := pats["W-D21-halted"].match(s):
            diags.append(Diag(_map_path(m.group("file"), prog.path_map, Path(raw) / "src"),
                              int(m.group("line")), int(m.group("col")) + 1, "error",
                              m.group("message"), "W-D21"))
    res = Result(LANG, target, rc, "error", "test", int(summary.group("verified")) if summary
                 else None, holes_from(diags), _sorted(diags), findings, per, str(raw), argv)
    kc = _killed_or_clock(rc)
    if kc:
        res.verdict = kc
        return res
    lines = [x.strip() for x in out.splitlines()]
    if rc == 3 and not per:
        res.stage = "compile"
        res.verdict = "failed"
        return res
    if rc == 4:
        res.stage, res.verdict = "verify", "failed"
        return res
    if rc == 2:
        res.stage, res.verdict = "resolve", "failed"
        return res
    if rc not in (0, 3):
        res.stage, res.verdict = "cli", "error"
        return res
    missing = []
    for n in names:
        hits = [k for k in per if k == n or k.endswith("." + n)]
        if not hits:
            missing.append(n)
    for n in missing:
        res.findings.append(Finding(target, 0, "test-not-run",
                                    f"{n}: the test did not run (no PASSED/FAILED line; Δ43)"))
    if not per:
        res.findings.append(Finding(target, 0, "no-tests",
                                    "no test ran: exit 0 alone is not a pass (Δ11, Δ43)"))
    failed = [k for k, v in per.items() if v == "failed"]
    res.verdict = "failed" if (failed or missing or not per or rc != 0) else "verified"
    if msgs["W-D05"] in lines:
        res.stage = "compile"
    return res


# --- empty-body gate ---------------------------------------------------------------------------

LEVER_ATTRS = {("{:", "induction"), ("@", "Induction"), ("{:", "fuel"), ("@", "Fuel"),
               ("{:", "disableNonlinearArithmetic"), ("@", "DisableNonlinearArithmetic"),
               ("{:", "opaque")}


def _find_item_decl(prog, item_symbol):
    """(file, Source, Decl) for an item id (`Q04.H1d`: the first lemma, method,
    function or predicate in its block) or a symbol (`Mod.Name`)."""
    is_item = re.fullmatch(r"[QR]\d\d\.[WCPHXTA][1-9]\d*(?:dv|py|d|v)", item_symbol)
    for f in prog.own:
        text = Path(f).read_text(encoding="utf-8")
        src = parse_source(text, str(f))
        if is_item:
            items, _ = ci.parse_items(str(f), text)
            for it in items:
                if it["id"] != item_symbol:
                    continue
                for d in src.decls:
                    if d.kind in METHODLIKE - {"iterator"} and \
                            it["line_start"] <= d.line <= it["line_end"]:
                        return Path(f), src, d
                raise Refused(f"{item_symbol}: its block holds no lemma, method or function")
        else:
            d = src.decl(item_symbol)
            if d is not None and d.kind in METHODLIKE:
                return Path(f), src, d
    raise Refused(f"{item_symbol}: no such item or symbol in {common.display_path(prog.target)}'s "
                  "own files")


def _edit(text, edits):
    """Apply [(start offset, end offset, replacement)] edits."""
    for s, e, rep in sorted(edits, key=lambda x: -x[0]):
        text = text[:s] + rep + text[e:]
    return text


def _empty_body_text(src, d, maxauto, regions=None):
    """The variant source: the item's body emptied (a `function … by method`
    keeps its function body, which is its statement, and loses its method
    body: QPLAN §6 Q18), or, with `regions` (an item id), the item's learner
    regions blanked (common.strip_regions) and the rest of the file kept;
    maxauto also strips the baked levers."""
    toks, edits = src.toks, []
    if regions is None:
        if d.by_method:
            edits.append((toks[d.by_method[0]].start, toks[d.by_method[1]].end, "{}"))
        elif d.body:
            edits.append((toks[d.body[0]].start, toks[d.body[1]].end, "{}"))
        else:
            end = toks[d.header_end - 1].end
            edits.append((end, end, " {}"))
    if maxauto:
        edits += _lever_edits(src, only=d)
    text = _edit(src.text, edits)
    return common.strip_regions(text, regions) if regions is not None else text


def _lever_edits(src, only=None):
    """Edits that strip the baked automation levers (Δ45, Δ46): induction and
    fuel attributes on the hole, nonlinear-arithmetic module attributes and
    function opacity everywhere in the file."""
    toks, edits = src.toks, []
    hole_attrs = set()
    if only is not None:
        for a in only.attrs + only.header_attrs:
            hole_attrs.add(a.start)
    for a in src.attrs:
        key = (a.style, a.name)
        if key not in LEVER_ATTRS:
            continue
        if key in {("{:", "induction"), ("@", "Induction"), ("{:", "fuel"), ("@", "Fuel")} \
                and a.start not in hole_attrs:
            continue
        edits.append((toks[a.start].start, toks[a.end - 1].end, ""))
    for d in src.decls:
        if d.kind in ("function", "predicate"):
            for k in range(d.start, d.kw):
                if toks[k].text == "opaque":
                    edits.append((toks[k].start, toks[k].end, ""))
    return edits


def empty_body(target, item_symbol, regions=False):
    """The empty-body gate for one hole (Δ45, Δ46, spec §2.8): the item's body
    becomes `{}` (a bodyless hole gets one; a `function … by method` keeps its
    function body and its method body becomes `{}`) in a scratch copy, and the
    variant is verified for that symbol only.

    regions=True is the region mode for an annotation hole (QPLAN §6 Q18):
    `target` is the item's reference twin, laid over its learner unit, and
    item_symbol its item id; the variant blanks the lines inside the item's
    `@hole-begin`/`@hole-end` regions (common.strip_regions), keeps the given
    code, and must fail the same way. Its runs are named `region-maxauto` and
    `region-shipped:seed=S`. Runs:
      maxauto           every baked lever stripped (the hole's induction and
                        fuel attributes, nonlinear-arithmetic module attributes
                        and function opacity in every file of the program), the
                        unit's manual-lemma-induction and
                        disable-nonlinear-arithmetic overridden off on the
                        command line: auto-induction on;
      shipped:seed=S    the shipped levers and unit options, under each pinned
                        seed (measure-complexity, Δ17).
    per_symbol maps each run to verified | failed | inconclusive |
    killed(memory) | error. verdict: failed when no shipped run verified and
    none was killed or errored (the hole is real: it passes the gate);
    verified when any shipped run verified (the gate rejects the item);
    otherwise the worst run's verdict. maxauto is reported, not gating: a hole
    that verifies there but fails as shipped is a "hole + lever" item
    (finding lever-needed).

    Out of resources (QPLAN §30 Q66, decided): a run that ends `inconclusive`
    (only an out-of-resource or time-out result: the empty body was not
    proved within the pinned resource limit) counts as FAILING at the pin, in
    every run: a shipped run toward the verdict above, and the maxauto run for
    the four results' "fails under maximal automation" (spec §2.8), so an
    inconclusive maxauto run is never a lever-needed finding. It is reported
    as an empty-body-inconclusive finding, so the record says which runs
    failed by running out. This is the Dafny reading of Δ58's rule (a Verus
    wall-clock kill counts as the variant failing) and of Verus's
    fails(rlimit); a proof that needs more than the pinned limit is not a
    proof at the pin (Δ56)."""
    try:
        common.toolchain("dafny")
        prog = program(target)
    except Refused as e:
        return _refused(target, str(e))
    except common.ToolchainError as e:
        return _toolchain_error(target, e)
    try:
        f, src, d = _find_item_decl(prog, item_symbol)
        rid = None
        if regions:
            if not re.fullmatch(r"[QR]\d\d\.[WCPHXTA][1-9]\d*(?:dv|py|d|v)", item_symbol):
                raise Refused(f"{item_symbol}: the region mode takes an item id")
            try:
                if not common.hole_regions(src.text, item_symbol):
                    raise Refused(f"{item_symbol}: no @hole-begin/@hole-end region in "
                                  f"{common.display_path(f)}")
            except ValueError as e:
                raise Refused(f"{common.display_path(f)}: {e}") from None
            rid = item_symbol
    except Refused as e:
        discard(prog)
        return _refused(target, str(e))
    p = pins()
    root = common.scratch_dir("dafny-emptybody")
    pre = "region-" if rid else ""
    runs = [(f"{pre}maxauto", None, True)] + [(f"{pre}shipped:seed={s}", s, False)
                                             for s in p["seeds"]]

    def one(run):
        name, seed, maxauto = run
        cp, tmp = _scratch_copy(prog, "eb")
        idx = [Path(x) for x in prog.files].index(Path(f))
        cf = cp.files[idx]
        Path(cf).write_text(_empty_body_text(src, d, maxauto, rid), encoding="utf-8")
        if maxauto:
            for other in cp.files:
                if other == cf:
                    continue
                osrc = parse_file(other)
                edits = _lever_edits(osrc)
                if edits:
                    Path(other).write_text(_edit(osrc.text, edits), encoding="utf-8")
        extra = ["--manual-lemma-induction", "false", "--disable-nonlinear-arithmetic", "false"] \
            if maxauto else []
        if maxauto and cp.kind == "files":
            cp.options = {k: v for k, v in cp.options.items()
                          if k not in ("manual-lemma-induction", "disable-nonlinear-arithmetic")}
        rd = root / name.replace(":", "-").replace("=", "")
        rd.mkdir(parents=True, exist_ok=True)
        try:
            res = _verify_program(cp, gate=False, symbol=d.qual, seed=seed, extra_flags=extra,
                                  target=str(target), raw=rd)
        finally:
            discard(cp)
            shutil.rmtree(tmp, ignore_errors=True)
        st = res.per_symbol.get(d.qual)
        if res.verdict in ("killed(memory)", "error", "refused"):
            st = res.verdict
        elif st is None:
            st = "error"
        return name, st, res

    try:
        with ThreadPoolExecutor(max_workers=common.jobs("dafny")) as ex:
            results = list(ex.map(one, runs))
    finally:
        discard(prog)
    per = {name: st for name, st, _ in results}
    shipped = [st for name, st, _ in results if name.startswith(f"{pre}shipped")]
    if "verified" in shipped:
        verdict = "verified"
    elif all(st in ("failed", "inconclusive") for st in shipped):
        verdict = "failed"
    elif "killed(memory)" in shipped:
        verdict = "killed(memory)"
    else:
        verdict = "error"
    last = results[-1][2]
    findings = []
    if per.get(f"{pre}maxauto") == "verified" and verdict == "failed":
        findings.append(Finding(str(f), d.line, "lever-needed",
                                f"{d.qual}: the " + ("region-blanked twin" if rid else
                                                     "empty body")
                                + " verifies at maximal automation and fails only with the "
                                "shipped levers (a hole + lever item, Δ45)"))
    for name, st in per.items():
        if st == "inconclusive":
            findings.append(Finding(str(f), d.line, "empty-body-inconclusive",
                                    f"{d.qual}: {name} ran out of resource or time: not "
                                    "verified at the pin, counted as failing (QPLAN §30 Q66)"))
    decisive = next((r for n, s, r in results if n.startswith(f"{pre}shipped")
                     and s == "verified"), last)
    diags = list(dict.fromkeys(dg for _, _, r in results for dg in r.diagnostics
                               if dg.severity == "error"))
    return Result(LANG, str(target), decisive.exit_code, verdict, "verify", None, [], diags,
                  findings, per, str(root), decisive.cmd)


# --- the language server (Δ33) ----------------------------------------------------------------

def server_install():
    """A scratch copy of the pinned install for `dafny server`, which writes a
    log file into its install directory on every start (Δ33): the pinned tree
    under .toolchain/ is never the server's. Refreshed when its file list or
    sizes drift from the pinned tree."""
    tc = common.toolchain("dafny")
    src = Path(tc["dafny_root"]).resolve()
    dst = common.scratch_root() / "dafny-server" / src.name

    def listing(root, skip_logs):
        out = {}
        for x in sorted(root.rglob("*")):
            if x.is_file() and not (skip_logs and x.name.startswith("DafnyLanguageServerLog")):
                out[x.relative_to(root).as_posix()] = x.stat().st_size
        return out

    if not dst.is_dir() or listing(dst, True) != listing(src, False):
        if dst.exists():
            shutil.rmtree(dst)
        tmp = dst.with_name(dst.name + f".tmp{os.getpid()}")
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(src, tmp, symlinks=False)
        tmp.rename(dst)
    return dst


def server_argv(extra=()):
    """argv for `dafny server` from the scratch copy (Δ33), with the pinned
    solver of that copy and the course resource limit. Run it under
    dvl.common.run_capped like any solver job."""
    inst = server_install()
    p = pins()
    return [str(inst / p["binary"]), "server", "--resource-limit", str(p["resource_limit"]),
            "--cores", str(p["cores"]), "--solver-path", str(inst / p["solver"])] + list(extra)
