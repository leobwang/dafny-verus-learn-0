#!/usr/bin/env python3
"""avoid.py — the disjointness gate between the Q and R tracks (spec §2.7,
design §9, PLAN.md §5.5; DVR0). scripts/avoid.sh runs it.

A symmetric name-level tripwire for clauses (a) and (b): it finds every place
where one track's learner-facing material reuses a name the other track (or
the Lean course) poses or answers. Shape overlaps that a name scan cannot see
are genre waivers in scripts/avoid.waivers.tsv, never claimed as caught.

What one track T is checked against (the avoid list, regenerated on every
run and never committed):
  1. every hole-bodied declaration in the other track's exercise, check, exit,
     agent and harness files: the item blocks of scripts/course_items.py (H,
     X, T and A items) and, inside each, the shipped hole forms the tools
     count (firsttry.static_holes, the static half of the tools' counters:
     a Dafny bodyless lemma or function with `ensures`, an `assume`; a Verus
     labelled `assume(false)`, `admit()`, `external_body`, `uninterp spec
     fn`; Python `raise NotImplementedError("<item id>")` through the frozen
     counter), mapped to the declaration that holds them; the declarations
     an item poses without a hole form (its `need:` lines and the backticked
     signatures of its instructions: an exit or a test-out written from
     nothing); and every declaration of an agent (A) item's block;
  2. every declaration of the parallel problems in the other track's banks
     (`## Parallel problems` of .claude/skills/instructor/banks/<ID>.md);
  3. every declaration in the other track's written problems
     (paper/<ID>_problems.tex: dafnycode, veruscode, verbatim, lstlisting);
  4. every declaration in the other track's chapter code fences
     (docs/<ID>_*.md: dafny, rust, verus, python fences);
  5. the curated list scripts/avoid.curated (the Lean course's learner-visible
     names: kind `name` = an equal key, `type` = also a hit as a word of a key,
     `never` = a hit as an equal syntax token anywhere in a file);
  6. --extra-r PATH (author only, until the R modules exist): every
     declaration of the .dfy and .rs files under PATH (tools/ and target/
     skipped) is an R declaration, checked like R's own files (the DVR0 regex
     spikes). They are not R sources: which of them R poses as holes is
     DVR1's, so the Q side is not checked against them.

T's own declarations: every declaration (Dafny lemma, function, predicate,
method, datatype and its constructors, newtype, type, class, trait,
iterator; Rust fn, struct, enum and its variants, union, trait, type; Python
def, class) of its module files, its given layers, its specimens, and the
parallel problems, written problems and chapter fences of its modules.

Keys: the last component of a qualified name, with module prefixes Q0n_/R0n_,
layer prefixes QG_L<k>_/RG_A<k>_/RG_A1b_ (and the crate forms), the Verus
lemma_/proof_ prefixes and the Dafny Lemma affix stripped, then camelCase and
snake_case split into words, lower-cased and joined with `_` (NodeCount =
node_count). Keys listed under [conventions] in scripts/avoid/owners.toml
(language conventions such as `wf`, `view`, `new`) are never compared as
equal keys.

Hits (each printed as `<key> <track>:<file>:<line> ↔ <source>`):
  name      (i)   an own key equal to a key of the other side's sources;
  curated   (i, ii) an own key equal to a curated name, or a curated type
                  occurring as a word (run) of an own key; (iii) a `never`
                  name as an equal syntax token in an own file;
  artifact  a word run of the other track's owned artifacts (owners.toml,
            design §9.2 item 3) inside an own key;
  owner     a token tripwire of the other track's owner tags (owners.toml,
            design §9.2 item 1) among the code tokens of an own prediction
            (P item) block; tags without a tripwire are listed, not caught;
  half      an own file that names the other track's half of the cheat
            corpus (design §9.2 item 2): `load_half(…, "<H>")`, `--half <H>`,
            or a tests/corpus/<lang>/<ID>/ path whose manifest says that half;
  self      (no waivers) an own bank parallel problem declaring the key of
            an own hole-bodied declaration (source 1 of the own track): a
            parallel problem never re-poses an exercise (spec §2.7).

Waivers (scripts/avoid.waivers.tsv): `id state key source direction reason
cost`, tab-separated; a `name` row (a key) waives the hits with that key whose
source descriptor matches `source` (fnmatch) in that direction; a name row
that waives no hit is an error (stale, like a stale pin) whenever its target
track has declarations in the run, and is reported idle otherwise (R before
its modules exist). A `genre` row (key `-`) records a shared genre with its
cost (design §9.3); its item homes in armed modules must exist; it is listed,
never claimed as caught. The self-check takes no waivers.

Usage: scripts/avoid.sh [--track Q|R|both] [--json] [--list-sources]
                        [--extra-r PATH]...
  (hidden, for scripts/ci.sh and the tests: --root DIR, the course root, default
  this checkout; --inputs DIR, the directory holding avoid.waivers.tsv,
  avoid.curated and avoid/owners.toml, default this checkout's scripts/)
Exit 0: no unwaived hit and no stale waiver; 1: a hit or a stale waiver;
2: a malformed input (a waiver, curated or owners line, an unreadable
source, an item block of a non-planned module that does not parse); 3: a
usage error.

It reads only learner-visible files of the course plus its own three inputs:
never Solutions/, paper/solutions/, the leak patterns, a held-out tree or
another course's files. --extra-r is the one exception, and only when the
author passes it by hand (scripts/ci.sh never does; guard rule 1 refuses a
reference path on a study session's shell line). It never prints file
content, only names, locations and its own messages.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_course_map as ccm  # noqa: E402  (the registry and the one item parser)
from dvl import dafny as D  # noqa: E402
from dvl import verus_spec as VS  # noqa: E402

EXIT_OK, EXIT_HIT, EXIT_MALFORMED, EXIT_USAGE = 0, 1, 2, 3
TRACKS = ("Q", "R")
WAIVERS = "scripts/avoid.waivers.tsv"   # shown paths; read from the inputs directory
CURATED = "scripts/avoid.curated"
OWNERS = "scripts/avoid/owners.toml"
INPUT_FILES = {WAIVERS: "avoid.waivers.tsv", CURATED: "avoid.curated",
               OWNERS: "avoid/owners.toml"}
WAIVER_COLS = ("id", "state", "key", "source", "direction", "reason", "cost")
DIRECTIONS = ("Q→R", "R→Q", "Lean→Q", "Lean→R")
STATES = ("adopted", "provisional")
CURATED_KINDS = ("name", "type", "never")
# The reference and held-out trees: never read (an --extra-r path excepted).
FORBIDDEN = re.compile(r"(?:^|/)(?:Solutions|paper/solutions|tests/instructor/leak_patterns|"
                       r"tests/instructor/fixtures|Hidden)(?:/|$)")


class Malformed(Exception):
    """An input the gate cannot read as written (exit 2)."""


# --- keys ------------------------------------------------------------------------------------

PREFIX = re.compile(r"^(?:[QR]\d\d_|QG_L\d+_|RG_A\d+b?_|qg_bignat_l\d+_|rg_re_a\d+b?_)")
WORD = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")


def words_of(name):
    """The lower-cased words of an identifier (camelCase and snake_case)."""
    out = []
    for part in name.split("_"):
        out += [w.lower() for w in WORD.findall(part)]
    return out


def key_of(name):
    """The normalized key of a declaration name (module doc, Keys)."""
    n = re.split(r"::|\.", name)[-1].rstrip("?'")
    n = PREFIX.sub("", n)
    w = words_of(n)
    if len(w) > 1 and w[0] == "lemma":
        w = w[1:]
    elif len(w) > 1 and w[0] == "proof" and n.startswith("proof_"):
        w = w[1:]
    if len(w) > 1 and w[-1] == "lemma":
        w = w[:-1]
    return "_".join(w)


def has_run(key_words, run):
    """True when the word list `run` occurs contiguously in key_words."""
    k = len(run)
    return any(key_words[i:i + k] == run for i in range(len(key_words) - k + 1))


# --- declarations ----------------------------------------------------------------------------

@dataclass(frozen=True)
class Decl:
    name: str
    key: str
    track: str
    rel: str        # repo-relative file (or the --extra-r path's file)
    line: int
    origin: str     # file | hole | bank | paper | chapter | spike
    ref: str        # module id, item id or file name: the source descriptor's tail

    @property
    def desc(self):
        return f"{self.origin}:{self.ref}"


D_KW = {"lemma", "function", "predicate", "method", "iterator", "colemma", "copredicate",
        "datatype", "codatatype", "newtype", "type", "class", "trait"}
D_MODS = D.MODIFIERS | {"function", "method"}   # `function method` (Dafny 3) / `ghost method`
V_KW = {"fn", "struct", "enum", "union", "trait", "type"}


def _skip_d_attrs(toks, i):
    """Index past Dafny `{: … }` attributes and `@Attr(…)` attributes at i."""
    n = len(toks)
    while i < n:
        if toks[i].text == "{" and i + 1 < n and toks[i + 1].text == ":":
            depth, i = 1, i + 1
            while i < n and depth:
                i += 1
                if i < n and toks[i].text == "{":
                    depth += 1
                elif i < n and toks[i].text == "}":
                    depth -= 1
            i += 1
        elif toks[i].text == "@" and i + 1 < n and toks[i + 1].kind == "id":
            i += 2
            if i < n and toks[i].text == "(":
                depth = 1
                while i < n and depth:
                    i += 1
                    if i < n and toks[i].text == "(":
                        depth += 1
                    elif i < n and toks[i].text == ")":
                        depth -= 1
                i += 1
        else:
            return i
    return i


def dafny_names(text):
    """[(name, line)] of the declarations in Dafny text (a file or a fence):
    token-based, comments and strings ignored, tolerant of fragments."""
    toks = D.tokenize(text)
    out, n = [], len(toks)
    for i, t in enumerate(toks):
        if t.kind != "id" or t.text not in D_KW:
            continue
        if t.text in ("function", "method") and i + 1 < n and toks[i + 1].text in ("method", "by"):
            continue          # `function method`: the second keyword names it; `function by method`
        if i > 0 and toks[i - 1].text in (".", "::"):
            continue
        j = _skip_d_attrs(toks, i + 1)
        if j < n and toks[j].kind == "id" and toks[j].text not in D_MODS:
            out.append((toks[j].text, toks[j].line))
            if t.text in ("datatype", "codatatype"):
                out += _dafny_ctors(toks, j + 1)
    return out


def _dafny_ctors(toks, i):
    """Constructors of the datatype whose name token sits just before i."""
    n, out = len(toks), []
    depth = 0
    while i < n and toks[i].text != "=":          # type parameters, attributes
        if toks[i].text in ("{", ";") and not (toks[i].text == "{" and i + 1 < n and
                                               toks[i + 1].text == ":"):
            return out
        i += 1
    expect = True
    i += 1
    while i < n:
        x = toks[i]
        if x.text in ("(", "[", "<"):
            depth += 1
        elif x.text in (")", "]", ">"):
            depth = max(0, depth - 1)
        elif depth == 0 and x.text == "|":
            expect = True
        elif depth == 0 and x.kind == "id" and x.text in D_KW | D.MODIFIERS | \
                {"const", "var", "module", "import", "export", "include"}:
            break
        elif depth == 0 and x.text in ("}", ";"):
            break
        elif depth == 0 and x.text == "{":
            if i + 1 < n and toks[i + 1].text == ":":
                i = _skip_d_attrs(toks, i)
                continue
            break                                    # the datatype's member block
        elif depth == 0 and expect and x.kind == "id":
            out.append((x.text, x.line))
            expect = False
        i += 1
    return out


def verus_names(text):
    """[(name, line)] of the declarations in Rust/Verus text, enum variants
    included; token-based, tolerant of fragments."""
    toks = VS.tokenize(text)
    out, n = [], len(toks)
    for i, t in enumerate(toks):
        if t.kind != "id" or t.text not in V_KW:
            continue
        if i + 1 < n and toks[i + 1].kind == "id":
            if t.text == "type" and i > 0 and toks[i - 1].text in ("::", "<", ","):
                continue
            out.append((toks[i + 1].text, toks[i + 1].line))
            if t.text == "enum":
                out += _verus_variants(toks, i + 2)
    return out


def _verus_variants(toks, i):
    n = len(toks)
    while i < n and toks[i].text not in ("{", ";"):
        i += 1
    if i >= n or toks[i].text != "{":
        return []
    out, depth, expect = [], 0, True
    i += 1
    while i < n:
        x = toks[i]
        if x.text in ("(", "[", "{"):
            depth += 1
        elif x.text in (")", "]", "}"):
            if depth == 0:
                break
            depth -= 1
        elif depth == 0 and x.text == ",":
            expect = True
        elif depth == 0 and x.text == "#":
            pass
        elif depth == 0 and expect and x.kind == "id":
            out.append((x.text, x.line))
            expect = False
        i += 1
    return out


def python_names(text):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [(m.group(2), text.count("\n", 0, m.start()) + 1)
                for m in re.finditer(r"(?m)^\s*(def|class)\s+([A-Za-z_]\w*)", text)]
    return [(nd.name, nd.lineno) for nd in ast.walk(tree)
            if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]


def names_in(text, lang):
    if lang == "d":
        return dafny_names(text)
    if lang == "v":
        return verus_names(text)
    if lang == "py":
        return python_names(text)
    return []


def lang_of(rel):
    if rel.endswith((".dfy", ".dfy.specimen")):
        return "d"
    if rel.endswith((".rs", ".rs.specimen")):
        return "v"
    if rel.endswith(".py"):
        return "py"
    return None


# --- text sources: fences, banks, written problems --------------------------------------------

FENCE = re.compile(r"^(\s*)(```+|~~~+)\s*([A-Za-z0-9_+-]*)")
FENCE_LANG = {"dafny": "d", "dfy": "d", "rust": "v", "verus": "v", "rs": "v",
              "python": "py", "py": "py"}
TEX_ENV = re.compile(r"\\begin\{(dafnycode|veruscode|verbatim|lstlisting)\}(.*?)\\end\{\1\}",
                     re.S)
TEX_LANG = {"dafnycode": "d", "veruscode": "v"}


def fences(text, lo=1, hi=None):
    """[(lang, first line of the body, body)] of the labelled code fences of a
    Markdown text whose start lies in [lo, hi]."""
    out, lines = [], text.split("\n")
    i, hi = 0, hi or len(lines)
    while i < len(lines):
        m = FENCE.match(lines[i])
        if not m:
            i += 1
            continue
        mark, lang, start = m.group(2), m.group(3).lower(), i + 1
        j = i + 1
        while j < len(lines) and not lines[j].lstrip().startswith(mark[:3]):
            j += 1
        if lo <= start <= hi and lang in FENCE_LANG:
            out.append((FENCE_LANG[lang], start + 1, "\n".join(lines[i + 1:j])))
        i = j + 1
    return out


def tex_code(text):
    """[(lang, first line, body)] of the code environments of a LaTeX text; a
    verbatim or lstlisting body is read as both verifier languages."""
    out = []
    for m in TEX_ENV.finditer(text):
        line = text.count("\n", 0, m.start(2)) + 1
        env, body = m.group(1), m.group(2)
        for lang in ([TEX_LANG[env]] if env in TEX_LANG else ["d", "v"]):
            out.append((lang, line, body))
    return out


def bank_pp_range(text):
    """(first, last) line of a bank's `## Parallel problems` section, or None."""
    lines = text.split("\n")
    lo = next((k for k, x in enumerate(lines, 1) if re.match(r"^##\s+Parallel problems\b", x)),
              None)
    if lo is None:
        return None
    hi = next((k for k, x in enumerate(lines, 1) if k > lo and re.match(r"^##\s", x)),
              len(lines) + 1)
    return lo, hi - 1


# --- inputs -----------------------------------------------------------------------------------

def read_tsv(inputs, rel, cols, what):
    """[(line, {col: value})] of a committed TSV input (# comments, blank lines,
    a header line equal to `cols`). Malformed on any other shape."""
    p = inputs / INPUT_FILES[rel]
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise Malformed(f"{rel}: cannot read the {what} ({e.__class__.__name__})")
    rows, header = [], False
    for ln, line in enumerate(text.split("\n"), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cells = line.split("\t")
        if not header:
            if tuple(c.strip() for c in cells) != cols:
                raise Malformed(f"{rel}:{ln}: the header must be the tab-separated columns "
                                f"{' '.join(cols)}")
            header = True
            continue
        if len(cells) != len(cols):
            raise Malformed(f"{rel}:{ln}: {len(cells)} tab-separated fields, {len(cols)} expected "
                            f"({' '.join(cols)})")
        row = dict(zip(cols, (c.strip() for c in cells)))
        if any(not v for v in row.values()):
            raise Malformed(f"{rel}:{ln}: an empty field (write `-` for none)")
        rows.append((ln, row))
    if not header:
        raise Malformed(f"{rel}: no header line ({' '.join(cols)})")
    return rows


@dataclass
class Waiver:
    line: int
    id: str
    state: str
    key: str
    source: str
    direction: str
    reason: str
    cost: str
    used: int = 0

    @property
    def genre(self):
        return self.key == "-"


ARROW = re.compile(r"\s*(?:→|->)\s*")


def load_waivers(inputs):
    out, seen = [], {}
    for ln, r in read_tsv(inputs, WAIVERS, WAIVER_COLS, "waivers"):
        at = f"{WAIVERS}:{ln}"
        if not re.fullmatch(r"[WXN][1-9]\d*", r["id"]):
            raise Malformed(f"{at}: waiver id {r['id']!r} is not W<n>, X<n> or N<n>")
        if r["key"] == "-" and r["id"][0] == "N":
            raise Malformed(f"{at}: an N<n> id names a name-only waiver; a genre row is W<n> "
                            "or X<n>")
        if r["state"] not in STATES:
            raise Malformed(f"{at}: state must be one of {', '.join(STATES)}")
        direction = ARROW.sub("→", r["direction"])
        if direction not in DIRECTIONS:
            raise Malformed(f"{at}: direction must be one of {', '.join(DIRECTIONS)}")
        if r["key"] != "-" and not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", r["key"]):
            raise Malformed(f"{at}: key {r['key']!r} is not a normalized key (lower-case words "
                            "joined with `_`) or `-` for a genre row")
        if r["key"] == "-":
            if r["id"] in seen:
                raise Malformed(f"{at}: a second genre row for {r['id']} (first at line "
                                f"{seen[r['id']]})")
            seen[r["id"]] = ln
        out.append(Waiver(ln, r["id"], r["state"], r["key"], r["source"], direction,
                          r["reason"], r["cost"]))
    keys = [(w.id, w.key, w.source, w.direction) for w in out if not w.genre]
    dup = {k for k in keys if keys.count(k) > 1}
    if dup:
        raise Malformed(f"{WAIVERS}: duplicate name rows {sorted(dup)}")
    return out


@dataclass(frozen=True)
class Curated:
    line: int
    name: str
    kind: str
    applies: str
    origin: str

    @property
    def key(self):
        return key_of(self.name)


def load_curated(inputs):
    out = []
    for ln, r in read_tsv(inputs, CURATED, ("name", "kind", "applies", "origin"), "curated list"):
        at = f"{CURATED}:{ln}"
        if r["kind"] not in CURATED_KINDS:
            raise Malformed(f"{at}: kind must be one of {', '.join(CURATED_KINDS)}")
        if r["applies"] not in ("Q", "R", "QR"):
            raise Malformed(f"{at}: applies must be Q, R or QR")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", r["name"]):
            raise Malformed(f"{at}: {r['name']!r} is not one identifier")
        out.append(Curated(ln, r["name"], r["kind"], r["applies"], r["origin"]))
    names = [(c.name, c.applies) for c in out]
    if len(set(names)) != len(names):
        raise Malformed(f"{CURATED}: a name is listed twice for the same track")
    return out


def load_owners(inputs):
    p = inputs / INPUT_FILES[OWNERS]
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise Malformed(f"{OWNERS}: cannot read ({e})")
    conv = data.get("conventions", {})
    keys = conv.get("keys", [])
    if not isinstance(keys, list) or not all(isinstance(k, str) and k == key_of(k) for k in keys):
        raise Malformed(f"{OWNERS}: [conventions] keys must be a list of normalized keys")
    arts, tags = [], []
    for a in data.get("artifact", []):
        if a.get("owner") not in TRACKS or not isinstance(a.get("name"), str) or \
                not isinstance(a.get("words"), list) or not a["words"]:
            raise Malformed(f"{OWNERS}: an [[artifact]] needs owner Q|R, name and words")
        arts.append((a["owner"], a["name"], [w.split() for w in a["words"]]))
    for t in data.get("tag", []):
        if t.get("owner") not in TRACKS or not isinstance(t.get("tag"), str) or \
                not isinstance(t.get("homes", []), list) or \
                not isinstance(t.get("tokens", []), list):
            raise Malformed(f"{OWNERS}: a [[tag]] needs owner Q|R, tag, homes and tokens lists")
        tags.append((t["owner"], t["tag"], t.get("homes", []), [key_of(x) for x in
                                                                   t.get("tokens", [])]))
    return set(keys), arts, tags


# --- the course ---------------------------------------------------------------------------------

def read(root, rel):
    if FORBIDDEN.search(rel):
        raise Malformed(f"{rel}: a reference or held-out path is never read")
    try:
        return (root / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise Malformed(f"{rel}: unreadable source ({e.__class__.__name__})")


@dataclass
class Track:
    track: str
    decls: list = field(default_factory=list)       # every own declaration
    sources: list = field(default_factory=list)     # what the other track is checked against
    files: dict = field(default_factory=dict)       # rel -> text (own code and text files)
    pitems: list = field(default_factory=list)      # (item, text) of own P items
    selfcheck: list = field(default_factory=list)   # own bank parallel-problem decls
    holes: int = 0


def given_files(root, track):
    out = []
    d = root / "dafny" / "given" / track
    if d.is_dir():
        out += sorted(p.relative_to(root).as_posix() for p in d.glob("*.dfy"))
    pre = "qg_" if track == "Q" else "rg_"
    v = root / "verus" / "given"
    if v.is_dir():
        for c in sorted(v.glob(pre + "*")):
            if (c / "src").is_dir():
                out += sorted(p.relative_to(root).as_posix() for p in (c / "src").rglob("*.rs"))
    return out


def _static_holes():
    import firsttry  # noqa: E402  (loaded lazily: it pulls in the wrappers' modules)
    return firsttry.static_holes


def enclosing(text, lang, line):
    """The declaration name that holds `line` (the innermost), or None."""
    if lang == "d":
        src = D.parse_source(text)
        best = None
        for d in src.decls:
            if d.kind not in D.METHODLIKE and d.kind not in D.TYPEDECL | D.CLASSLIKE:
                continue
            lo = src.toks[d.start].line if d.start < len(src.toks) else d.line
            if lo <= line <= d.end_line and (best is None or lo >= best[0]):
                best = (lo, d.name)
        return best and best[1]
    src = VS.parse(text)
    best = None
    for it in src.walk():
        if it.kind != "fn" or not it.name:
            continue
        lo, hi = src.line_of(it.start), src.line_of(max(it.end - 1, it.start))
        if lo <= line <= hi and (best is None or lo >= best[0]):
            best = (lo, it.name)
    return best and best[1]


def module_records(root):
    data, err = ccm.load_registry(root)
    if err:
        raise Malformed(f"the module registry is unusable: {err}")
    return [m for m in data.get("module", []) if isinstance(m, dict) and
            isinstance(m.get("id"), str) and m["id"][:1] in TRACKS]


def collect(root, track, records, extra=()):
    """The Track view of one track: its declarations and its sources."""
    T = Track(track)
    static_holes = None
    seen_files = set()

    def add_decls(rel, text, lang, origin, ref, line0=1, into=(T.decls,)):
        got = []
        for name, ln in names_in(text, lang):
            k = key_of(name)
            if not k:
                continue
            d = Decl(name, k, track, rel, ln + line0 - 1, origin, ref)
            got.append(d)
            for lst in into:
                lst.append(d)
        return got

    for rel in given_files(root, track):
        text = read(root, rel)
        T.files[rel] = text
        add_decls(rel, text, lang_of(rel), "file", PurePosixPath(rel).name)
    for m in records:
        if m["id"][0] != track:
            continue
        mid = m["id"]
        files = [f for f in ccm.item_files(root, m) if not FORBIDDEN.search(f)]
        for rel in files:
            if rel in seen_files:
                continue
            seen_files.add(rel)
            text = read(root, rel)
            T.files[rel] = text
            add_decls(rel, text, lang_of(rel), "file", mid)
        if files:
            items, errs = ccm.module_items(root, m)
            # A planned module's files may be partial (mid-authoring); the checker
            # checks items only past planned, and so does this gate's refusal.
            if errs and m.get("status") != "planned":
                raise Malformed(f"{mid}: its item blocks do not parse ({errs[0]}; "
                                "run python3 scripts/check_course_map.py --only coverage)")
            for it in items:
                rel = it["file"]
                text = T.files.get(rel) or read(root, rel)
                if it["kind"] == "P":
                    T.pitems.append((it, text))
                if it["kind"] not in "HXTA":
                    continue
                if static_holes is None:
                    static_holes = _static_holes()
                lang = lang_of(rel)
                for hl in static_holes(text, rel, it, root):
                    if lang == "py":
                        name = next((n for n, ln in python_names(text) if ln == hl), None)
                        name = name or _py_hole_name(text, hl)
                    else:
                        name = enclosing(text, lang, hl)
                    if name and key_of(name):
                        T.holes += 1
                        T.sources.append(Decl(name, key_of(name), track, rel, hl, "hole",
                                              it["id"]))
                # A write-from-nothing item (an exit, a test-out) ships no hole form:
                # the declaration it poses is in its `need:` lines and in the
                # backticked signatures of its instructions.
                if lang in ("d", "v") and it["kind"] == "A":
                    # An agent task (repair, refactor, spec-to-proof) answers every
                    # declaration of its block, holes or not.
                    block = "\n".join(text.split("\n")[it["line_start"] - 1:it["line_end"]])
                    for name, ln in names_in(block, lang):
                        if key_of(name):
                            T.sources.append(Decl(name, key_of(name), track, rel,
                                                  it["line_start"] + ln - 1, "hole", it["id"]))
                if lang in ("d", "v"):
                    for ln, frag in posed_fragments(text, it):
                        for name, _ in names_in(frag, lang):
                            if key_of(name):
                                T.holes += 1
                                T.sources.append(Decl(name, key_of(name), track, rel, ln,
                                                      "hole", it["id"]))
        bank = m.get("bank") or ""
        if bank and (root / bank).is_file():
            text = read(root, bank)
            T.files[bank] = text
            rng = bank_pp_range(text)
            if rng:
                for lang, ln, body in fences(text, *rng):
                    got = add_decls(bank, body, lang, "bank", mid, ln,
                                    into=(T.decls, T.sources))
                    T.selfcheck += got
        paper = f"paper/{mid}_problems.tex"
        if m.get("paper") and (root / paper).is_file():
            text = read(root, paper)
            T.files[paper] = text
            for lang, ln, body in tex_code(text):
                add_decls(paper, body, lang, "paper", mid, ln, into=(T.decls, T.sources))
        chapter = m.get("chapter") or ""
        if chapter and (root / chapter).is_file():
            text = read(root, chapter)
            T.files[chapter] = text
            for lang, ln, body in fences(text):
                add_decls(chapter, body, lang, "chapter", mid, ln, into=(T.decls, T.sources))
    for base in extra:
        for p in sorted(base.rglob("*") if base.is_dir() else [base]):
            if not p.is_file() or not p.name.endswith((".dfy", ".rs")) or \
                    "tools" in p.relative_to(base).parts or "target" in p.relative_to(base).parts:
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                raise Malformed(f"{p}: unreadable --extra-r file ({e.__class__.__name__})")
            rel = str(p.relative_to(root)) if p.is_relative_to(root) else str(p)
            T.files[rel] = text
            add_decls(rel, text, lang_of(p.name), "spike", p.name)
    uniq = {}
    for s in T.sources:
        uniq.setdefault((s.key, s.rel, s.origin, s.ref), s)
    T.sources = list(uniq.values())
    T.holes = sum(1 for s in T.sources if s.origin == "hole")
    return T


NEED_LINE = re.compile(r"^\s*//\s*need:\s*(.*)$")
TICKS = re.compile(r"`([^`\n]+)`")


def posed_fragments(text, it):
    """[(line, fragment)] of an item block's posed declarations: its `need:`
    lines, and the backticked spans of its comment lines (only a span that
    holds a declaration keyword yields a name; commented-out checks are not
    read)."""
    out = []
    lines = text.split("\n")
    for ln in range(it["line_start"], min(it["line_end"], len(lines)) + 1):
        raw = lines[ln - 1]
        m = NEED_LINE.match(raw)
        if m:
            out.append((ln, m.group(1)))
            continue
        s = raw.lstrip()
        if s.startswith("//"):
            out += [(ln, t.group(1)) for t in TICKS.finditer(s)]
    return out


def _py_hole_name(text, line):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    best = None
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                nd.lineno <= line <= (nd.end_lineno or nd.lineno):
            if best is None or nd.lineno >= best.lineno:
                best = nd
    return best and best.name


# --- the checks --------------------------------------------------------------------------------

@dataclass
class Hit:
    kind: str       # name | curated | artifact | owner | half | self
    key: str
    track: str      # the track whose file holds the hit
    rel: str
    line: int
    source: str     # the source descriptor (what a waiver's `source` matches)
    where: str      # the source's location, for the report
    direction: str
    waiver: Waiver | None = None

    def render(self):
        w = f"   [waived: {self.waiver.id}{' (provisional)' if self.waiver.state == 'provisional' else ''}]" \
            if self.waiver else ""
        return f"{self.key} {self.track}:{self.rel}:{self.line} ↔ {self.source}" + \
            (f" ({self.where})" if self.where else "") + f"   [{self.kind}]" + w


HALF_CALL = re.compile(r"""load_half\s*\([^)]*?["']([QR])["']""")
HALF_FLAG = re.compile(r"--half[ =]([QR])\b")
CORPUS_PATH = re.compile(r"tests/corpus/(dafny|verus)/([A-Z]+-\d+)")


def code_ids(text, lang):
    """Identifiers among the code tokens of a text (comments dropped)."""
    try:
        if lang == "d":
            return [(t.text, t.line) for t in D.tokenize(text) if t.kind == "id"]
        if lang == "v":
            return [(t.text, t.line) for t in VS.tokenize(text) if t.kind == "id"]
    except Exception:          # a fragment that does not tokenize: fall back to words
        pass
    return [(m.group(0), text.count("\n", 0, m.start()) + 1)
            for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", text)]


def corpus_halves(root):
    out = {}
    base = root / "tests" / "corpus"
    for lang in ("dafny", "verus"):
        for man in sorted((base / lang).glob("*/manifest.toml")) if (base / lang).is_dir() else []:
            try:
                data = tomllib.loads(man.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
                raise Malformed(f"{man.relative_to(root)}: unreadable corpus manifest")
            out[(lang, man.parent.name)] = data.get("half")
    return out


def check_track(root, T, other, curated, conventions, arts, tags, halves):
    hits = []
    own, oth = T.track, other.track
    src_by_key = {}
    for s in other.sources:
        if s.key not in conventions:
            src_by_key.setdefault(s.key, []).append(s)
    for d in T.decls:
        for s in src_by_key.get(d.key, []):
            hits.append(Hit("name", d.key, own, d.rel, d.line, s.desc, f"{oth}:{s.rel}:{s.line}",
                            f"{oth}→{own}"))
    cur = [c for c in curated if own in c.applies]
    for d in T.decls:
        kw = d.key.split("_")
        for c in cur:
            if c.kind == "never":
                continue
            if d.key == c.key or (c.kind == "type" and has_run(kw, c.key.split("_"))):
                hits.append(Hit("curated", d.key, own, d.rel, d.line, f"curated:{c.name}",
                                f"{CURATED}:{c.line}, {c.origin}", f"Lean→{own}"))
    nevers = {c.name: c for c in cur if c.kind == "never"}
    for rel, text in T.files.items():
        if not nevers:
            break
        for name, ln in code_ids(text, lang_of(rel)) if lang_of(rel) else \
                [(m.group(0), text.count("\n", 0, m.start()) + 1)
                 for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", text)]:
            c = nevers.get(name)
            if c:
                hits.append(Hit("curated", key_of(name), own, rel, ln, f"curated:{c.name}",
                                f"{CURATED}:{c.line}, {c.origin}", f"Lean→{own}"))
    for owner, aname, runs in arts:
        if owner == own:
            continue
        for d in T.decls:
            kw = d.key.split("_")
            for run in runs:
                if has_run(kw, run):
                    hits.append(Hit("artifact", d.key, own, d.rel, d.line,
                                    f"artifact:{owner}:{'_'.join(run)}",
                                    f"{OWNERS}: {owner} owns {aname}", f"{owner}→{own}"))
                    break
    for owner, tag, _homes, toks in tags:
        if owner == own or not toks:
            continue
        for it, text in T.pitems:
            lang = lang_of(it["file"])
            block = "\n".join(text.split("\n")[it["line_start"] - 1:it["line_end"]])
            for name, ln in code_ids(block, lang):
                if key_of(name) in toks:
                    hits.append(Hit("owner", key_of(name), own, it["file"],
                                    it["line_start"] + ln - 1, f"owner:{owner}:{tag}",
                                    f"{it['id']} poses an {owner}-owned surprise", f"{owner}→{own}"))
    for rel, text in T.files.items():
        if rel.startswith(("tests/corpus/",)):
            continue
        for rx in (HALF_CALL, HALF_FLAG):
            for m in rx.finditer(text):
                if m.group(1) != own:
                    ln = text.count("\n", 0, m.start()) + 1
                    hits.append(Hit("half", f"half_{m.group(1).lower()}", own, rel, ln,
                                    f"corpus:{m.group(1)}", "the other track's half of the "
                                    "cheat corpus", f"{m.group(1)}→{own}"))
        for m in CORPUS_PATH.finditer(text):
            h = halves.get((m.group(1), m.group(2)))
            if h and h != own:
                ln = text.count("\n", 0, m.start()) + 1
                hits.append(Hit("half", f"half_{h.lower()}", own, rel, ln, f"corpus:{h}",
                                f"tests/corpus/{m.group(1)}/{m.group(2)} is in the {h} half",
                                f"{h}→{own}"))
    mine = {}
    for d in T.sources:
        if d.origin == "hole":
            mine.setdefault(d.key, d)
    for d in T.selfcheck:
        e = mine.get(d.key)
        if e and d.key not in conventions:
            hits.append(Hit("self", d.key, own, d.rel, d.line, f"self:{d.ref}",
                            f"{own}:{e.rel}:{e.line}", f"{own}→{own}"))
    return hits


def apply_waivers(hits, waivers):
    for h in hits:
        if h.kind == "self":
            continue                        # the self-check takes no waivers (spec §2.7)
        for w in waivers:
            if not w.genre and w.key == h.key and w.direction == h.direction and \
                    fnmatch.fnmatchcase(h.source, w.source):
                h.waiver = w
                w.used += 1
                break


ITEM_TOKEN = re.compile(r"\b([QR]\d\d)\.([A-Z]\d+[a-z]*)\b")


def genre_problems(root, waivers, records):
    """Problems of the genre rows: an item home in an armed module that does not
    exist is stale (the genre's home moved)."""
    status = {m["id"]: m.get("status") for m in records}
    by_mod = {}
    out = []
    for w in waivers:
        if not w.genre:
            continue
        for m in ITEM_TOKEN.finditer(w.source):
            mid, iid = m.group(1), f"{m.group(1)}.{m.group(2)}"
            if status.get(mid) in (None, "planned"):
                continue
            if mid not in by_mod:
                rec = next(r for r in records if r["id"] == mid)
                items, _ = ccm.module_items(root, rec)
                by_mod[mid] = {it["id"] for it in items}
            ids = by_mod[mid]
            if iid not in ids and not any(i.startswith(iid) and i[len(iid):] in ("d", "v", "dv", "py")
                                          for i in ids):
                out.append(f"{WAIVERS}:{w.line}: {w.id}: home {iid} names no item of armed "
                           f"{mid} (stale genre row)")
    return out


def tag_problems(root, tags, records):
    """An owner tag's home that names an item of an armed module must exist."""
    status = {m["id"]: m.get("status") for m in records}
    out, cache = [], {}
    for owner, tag, homes, _ in tags:
        for h in homes:
            m = re.fullmatch(r"([QR]\d\d)\.([A-Z]\d+[a-z]*)", h)
            if not m or m.group(1)[0] != owner:
                out.append(f"{OWNERS}: tag {tag}: home {h!r} is not an item id of the owner "
                           f"track {owner}")
                continue
            mid = m.group(1)
            if status.get(mid) in (None, "planned"):
                continue
            if mid not in cache:
                rec = next(r for r in records if r["id"] == mid)
                cache[mid] = {it["id"] for it in ccm.module_items(root, rec)[0]}
            if h not in cache[mid]:
                out.append(f"{OWNERS}: tag {tag}: home {h} names no item of armed {mid}")
    return out


# --- main --------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(prog="scripts/avoid.sh", add_help=True, allow_abbrev=False)
    ap.add_argument("--track", choices=("Q", "R", "both"), default="both")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list-sources", action="store_true")
    ap.add_argument("--extra-r", action="append", default=[], metavar="PATH")
    ap.add_argument("--root", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--inputs", default=None, help=argparse.SUPPRESS)
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return EXIT_OK if e.code == 0 else EXIT_USAGE
    root = Path(a.root).resolve() if a.root else SCRIPTS.parent
    inputs = Path(a.inputs).resolve() if a.inputs else SCRIPTS
    extra = []
    for x in a.extra_r:
        p = Path(x)
        p = (p if p.is_absolute() else Path.cwd() / p).resolve()
        if not p.exists():
            print(f"avoid.sh: --extra-r {x}: no such file or directory", file=sys.stderr)
            return EXIT_USAGE
        extra.append(p)
    try:
        waivers = load_waivers(inputs)
        curated = load_curated(inputs)
        conventions, arts, tags = load_owners(inputs)
        records = module_records(root)
        halves = corpus_halves(root)
        view = {"Q": collect(root, "Q", records),
                "R": collect(root, "R", records, extra)}
        problems = tag_problems(root, tags, records) + genre_problems(root, waivers, records)
    except Malformed as e:
        print(f"avoid.sh: malformed input: {e}", file=sys.stderr)
        return EXIT_MALFORMED
    if problems:
        for p in problems:
            print(f"avoid.sh: malformed input: {p}", file=sys.stderr)
        return EXIT_MALFORMED
    tracks = TRACKS if a.track == "both" else (a.track,)
    if a.list_sources:
        return list_sources(view, curated, conventions, arts, tags, tracks, a.json)
    hits = []
    for t in tracks:
        hits += check_track(root, view[t], view["R" if t == "Q" else "Q"], curated, conventions,
                            arts, tags, halves)
    hits = dedupe(hits)
    apply_waivers(hits, waivers)
    open_ = [h for h in hits if h.waiver is None]
    # A name row is stale only when its direction's target track was checked and
    # has declarations in this run (R has none until its modules or --extra-r exist).
    live = {t for t in tracks if view[t].decls}
    stale = [w for w in waivers if not w.genre and not w.used and
             w.direction.split("→")[1] in live]
    idle = [w for w in waivers if not w.genre and w.direction.split("→")[1] not in live]
    if a.json:
        print(json.dumps({
            "tracks": list(tracks),
            "hits": [dict(kind=h.kind, key=h.key, track=h.track, file=h.rel, line=h.line,
                          source=h.source, where=h.where, direction=h.direction,
                          waiver=h.waiver.id if h.waiver else None) for h in hits],
            "stale": [dict(id=w.id, line=w.line, key=w.key, source=w.source,
                           direction=w.direction) for w in stale],
            "idle": [w.id for w in idle],
            "genre_waivers": [dict(id=w.id, state=w.state, homes=w.source, direction=w.direction)
                              for w in waivers if w.genre],
            "counts": counts(view, tracks),
        }, indent=1, ensure_ascii=False))
    else:
        for h in sorted(open_, key=lambda h: (h.track, h.kind, h.key, h.rel, h.line)):
            print(h.render())
        for w in stale:
            print(f"{w.key} {WAIVERS}:{w.line} ↔ {w.source}   [stale waiver {w.id}: it waives "
                  "no hit]")
        waived = [h for h in hits if h.waiver]
        c = counts(view, tracks)
        prov = sorted({h.waiver.id for h in waived if h.waiver.state == "provisional"} |
                      {w.id for w in waivers if w.genre and w.state == "provisional"})
        line = (f"avoid.sh: {'FAIL' if open_ or stale else 'OK'}: tracks {'+'.join(tracks)}; "
                + "; ".join(f"{t}: {c[t]['decls']} declarations, {c[t]['sources']} sources "
                            f"({c[t]['holes']} hole-bodied)" for t in TRACKS)
                + f"; {len(curated)} curated names; {len(open_)} hit(s), {len(waived)} waived, "
                f"{len(stale)} stale waiver(s); {sum(1 for w in waivers if w.genre)} genre "
                "waivers listed (shape overlaps, not name-checked)"
                + (f"; {len(idle)} name waiver(s) idle (no declarations on their target "
                   f"track: {', '.join(w.id for w in idle)})" if idle else "")
                + (f"; provisional: {', '.join(prov)}" if prov else "")
                + (f"; --extra-r: {len(extra)} path(s)" if extra else ""))
        print(line)
    return EXIT_HIT if open_ or stale else EXIT_OK


def counts(view, tracks):
    return {t: {"decls": len(view[t].decls), "sources": len(view[t].sources),
                "holes": view[t].holes, "files": len(view[t].files)} for t in TRACKS}


def dedupe(hits):
    seen, out = set(), []
    for h in hits:
        k = (h.kind, h.key, h.track, h.rel, h.line, h.source)
        if k not in seen:
            seen.add(k)
            out.append(h)
    return out


def list_sources(view, curated, conventions, arts, tags, tracks, as_json):
    rows = []
    for t in tracks:
        other = view["R" if t == "Q" else "Q"]
        for s in other.sources:
            rows.append(dict(checked=t, key=s.key, name=s.name, source=s.desc,
                             file=s.rel, line=s.line))
        for c in curated:
            if t in c.applies:
                rows.append(dict(checked=t, key=c.key, name=c.name, source=f"curated:{c.name}",
                                 file=CURATED, line=c.line, kind=c.kind))
    if as_json:
        print(json.dumps({"sources": rows, "conventions": sorted(conventions),
                          "artifacts": [dict(owner=o, name=n, words=[" ".join(r) for r in rs])
                                        for o, n, rs in arts],
                          "tags": [dict(owner=o, tag=t, homes=h, tokens=k)
                                   for o, t, h, k in tags]}, indent=1, ensure_ascii=False))
    else:
        for r in rows:
            print(f"{r['checked']} ← {r['key']}  {r['source']}  {r['file']}:{r['line']}")
        print(f"avoid.sh --list-sources: {len(rows)} source keys "
              f"({', '.join(tracks)} checked against them)")
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:         # a reader such as `head` closed the pipe
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(EXIT_OK)
