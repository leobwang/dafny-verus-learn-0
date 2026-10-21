#!/usr/bin/env python3
"""dvl.reach — the challenge gate's reach scan (QPLAN §31.1 item 6; spec §2.3.8 item 7
and its last row; DELTAS Δ402).

A challenge's frozen manifest (`<ID>_Statement.toml`) names what a delivery may not
reach and what it must define:

    [reach]
    deny_names   = ["LemmaMulComm", "vstd::arithmetic::mul::lemma_mul_is_commutative"]
    deny_modules = ["Std.Arithmetic.LittleEndianNat", "vstd::arithmetic::mul"]
    require      = ["SortedPermutation", "heapsort"]

  deny_names    a declaration (an upstream result, a later-layer lemma, "named in case
                the library adds it") the delivery may not name: matched as a whole
                identifier on its last segment, and on its full qualified spelling
                (Dafny `A.B.c`, Verus `a::b::c`)
  deny_modules  a module the delivery may not import or qualify through: Dafny
                `import [opened] M…` / `M.x`, Verus `use m::…` / `m::x`, M itself or
                any submodule of it
  require       a declaration the delivery must define (its statement's roots)

Every delivery is also scanned for reach into a reference or held-out tree: a Dafny
`include`, a Rust `#[path = …]`, `include!`/`include_str!`/`include_bytes!` or a
Cargo path dependency whose string names `Solutions`, `Hidden`, `leak_patterns` or
the author archive. Comments and literals are blanked first (dvl.trustleap.blank),
except the path strings of those include forms, which are read.

This is a TEXT scan of the delivery's own files: it does not resolve names through
the given layers or follow a call graph. A name reached only through an alias the
scan cannot see (a Verus `use … as`, a Dafny import alias of a denied module is
caught; a re-export through an allowed crate is not) is a known residual, recorded in
Δ402; the resolved-program form (Dafny's symbol table, Verus `--log vir` call edges)
is QPLAN §40 Q69.

  scan(files, policy, root) -> list[str]        findings, [] = clean
  load_policy(manifest_path) -> dict            the [reach] table (empty lists if absent)

CLI: python3 scripts/dvl/reach.py --manifest M.toml [--root R] FILE...
Exit 0 clean · 1 findings · 2 usage · 3 an unreadable manifest. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))
from dvl.trustleap import blank, lang_of  # noqa: E402

__all__ = ["REFERENCE_WORDS", "load_policy", "scan", "scan_text"]

KEYS = ("deny_names", "deny_modules", "require")
REFERENCE_WORDS = ("Solutions", "Hidden", "leak_patterns", "dafny-verus-learn-0/author")

_INCLUDE_FORMS = [
    re.compile(r'\binclude\s+"([^"]*)"'),                                   # Dafny
    re.compile(r'#\[\s*path\s*=\s*"([^"]*)"\s*\]'),                          # Rust
    re.compile(r'\binclude(?:_str|_bytes)?!\s*\(\s*"([^"]*)"'),
    re.compile(r'\bpath\s*=\s*"([^"]*)"'),                                  # Cargo.toml
]
_DAFNY_DEFN = re.compile(
    r"\b(?:method|function|lemma|predicate|constructor|class|trait|datatype|codatatype|"
    r"newtype|type|const|iterator|module)\b(?:\s+method)?(?:\s*\{:[^}]*\})*\s+([A-Za-z_][\w'?]*)")
_VERUS_DEFN = re.compile(r"\b(?:fn|struct|enum|type|trait|const|static|mod)\s+([A-Za-z_]\w*)")


class PolicyError(Exception):
    pass


def load_policy(path) -> dict:
    try:
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise PolicyError(f"{path}: {e}") from None
    t = data.get("reach", {})
    if not isinstance(t, dict) or set(t) - set(KEYS):
        raise PolicyError(f"{path}: [reach] holds only {', '.join(KEYS)}")
    out = {}
    for k in KEYS:
        v = t.get(k, [])
        if not isinstance(v, list) or not all(isinstance(x, str) and x for x in v):
            raise PolicyError(f"{path}: reach.{k} must be a list of non-empty strings")
        out[k] = v
    return out


def _sep(lang):
    return "." if lang == "dafny" else "::"


def _norm(name, lang):
    """A policy name in the file language's separator."""
    return name.replace("::", ".") if lang == "dafny" else name.replace(".", "::")


def _qual_rx(qual, lang):
    parts = [re.escape(p) for p in re.split(r"\.|::", qual)]
    sep = r"\s*\.\s*" if lang == "dafny" else r"\s*::\s*"
    return re.compile(r"(?<![\w.:])" + sep.join(parts) + r"(?![\w'?])")


def _line(text, pos):
    return text.count("\n", 0, pos) + 1


def scan_text(text, lang, rel, policy):
    """(findings, defined names) of one file."""
    out, lines = [], set()
    for rx in _INCLUDE_FORMS:
        for m in rx.finditer(text):
            if any(w in m.group(1) for w in REFERENCE_WORDS):
                lines.add(_line(text, m.start()))
    out += [f"{rel}:{n}: reaches a reference or held-out path through an include form"
            for n in sorted(lines)]
    if lang not in ("dafny", "verus"):
        return out, set()
    b = blank(text, lang)
    for name in policy.get("deny_names", []):
        q = _norm(name, lang)
        last = re.split(r"\.|::", q)[-1]
        rxs = [re.compile(r"(?<![\w'?])" + re.escape(last) + r"(?![\w'?])")]
        if last != q:
            rxs.append(_qual_rx(q, lang))
        hit = None
        for rx in rxs:
            m = rx.search(b)
            if m and (hit is None or m.start() < hit):
                hit = m.start()
        if hit is not None:
            out.append(f"{rel}:{_line(b, hit)}: names the denied declaration {name}")
    for mod in policy.get("deny_modules", []):
        q = _norm(mod, lang)
        if lang == "dafny":
            imp = re.compile(r"\bimport\s+(?:opened\s+)?(?:[A-Za-z_]\w*\s*=\s*)?"
                             + r"\s*\.\s*".join(map(re.escape, q.split(".")))
                             + r"(?![\w'?])")
        else:
            imp = re.compile(r"\buse\s+(?:::)?" + r"\s*::\s*".join(map(re.escape, q.split("::")))
                             + r"(?!\w)")
        m = imp.search(b) or _qual_rx(q, lang).search(b)
        if m:
            out.append(f"{rel}:{_line(b, m.start())}: reaches the denied module {mod}")
    defs = set((_DAFNY_DEFN if lang == "dafny" else _VERUS_DEFN).findall(b))
    return out, defs


def scan(files, policy, root=None):
    root = Path(root or ".").resolve()
    out, defs = [], set()
    for raw in files:
        p = Path(raw)
        p = p if p.is_absolute() else root / p
        try:
            rel = p.resolve().relative_to(root).as_posix()
        except ValueError:
            rel = str(p)
        lang = lang_of(p) or ("cargo" if p.name == "Cargo.toml" else None)
        if lang is None:
            continue
        f, d = scan_text(p.read_text(encoding="utf-8"), lang, rel, policy)
        out += f
        defs |= d
    for name in policy.get("require", []):
        last = re.split(r"\.|::", name)[-1]
        if last not in defs:
            out.append(f"the required declaration {name} is not defined in the delivery")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="dvl/reach.py", allow_abbrev=False)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args(argv)
    try:
        policy = load_policy(a.manifest)
    except PolicyError as e:
        print(f"reach: {e}", file=sys.stderr)
        return 3
    found = scan(a.files, policy, a.root)
    for f in found:
        print(f)
    print(f"reach: {len(found)} finding(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
