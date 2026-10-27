#!/usr/bin/env python3
"""reference_lint.py — the author's lint of reference twins (phase DV1b).

Spec §3.13 (twins and hollowing), §3.8.4 H6, §8.3; DELTAS Δ71, Δ79, Δ86
(the reference side of the reserved names). Author-only: it reads the
reference tree, so it refuses (exit 3) unless CI=true or it runs in the
course author's linked worktree off a learner branch (spec §7.4); the guard
hook also refuses any study-mode command that names it.

A twin is the hole-free reference for a learner file, at the same path under
the reference tree (<ref>/<learner path>). For every non-planned module
(or --module ID) it checks, through course_items.py (the one item parser) and
the dvl statement tables:

  twin-missing           an exercise, exit or harness (learner Python) file
                         has no twin
  twin-orphan            a twin (dafny/, verus/, harness/q/, harness/r/,
                         specimens/, slots/) has no learner file
  twin-header            the twin's header does not say "Reference Solution"
  marker-*               the item markers differ: missing, extra, changed
                         (kind, strand, format, min, uses, need, pair), or in
                         another order
  declaration-*          the declarations differ: missing, extra (a twin-only
                         declaration is allowed when it is a test, follows the
                         agent reference heading, carries a
                         `reference-only` comment, or lies inside a
                         `@hole-begin`/`@hole-end` region of an item whose
                         admissible row says `writes = "module"`: the
                         learner writes those declarations, D92),
                         statement-differs (the
                         learner's bodyless function holes, and a Dafny
                         function or predicate shipped with a placeholder
                         body the twin replaces, QPLAN §30 Q52, compared by
                         header;
                         a Dafny declaration's opacity is part of its statement,
                         as in specfreeze), declaration-order; a Python twin
                         is compared by its functions' and classes' names and
                         parameter names, in order, and by each shared one's
                         signature (dvl.python.spec_hash, as specfreeze)
  imports-differ         a Dafny module whose import list the learner file
                         freezes (`// specfreeze: frozen-imports`, QPLAN §30
                         Q62) imports something else in the twin
  slot-leftover          SLOT: or ??? in a twin (H6)
  slot-not-enabled       a twin slot is not enabled (twins pin every answer)
  vacuous-slot           a twin slot breaks H1–H3 (the shared slot rules)
  need-missing           an exit block of the twin lacks its own `need:` text
  receipt-missing        a closing automation step in an H/X/T block has no
                         `// did:` receipt
  answer-missing         the reference slot file lacks a verdict answer
  <lint kind>            the reference-mode lint of dvl.dafny/dvl.verus/
                         dvl.python (every hole form, banned constructs,
                         reserved names; Python: the core's hole rules and the
                         import tier); a
                         line a valid `// planted: <item id>` marker covers
                         is exempt (the planted trust leap of an S12
                         delivery specimen's twin; the shared rules'
                         sr_planted; vcheck and vaudit never honour it)
  planted-marker         a `// planted:` marker outside an S12 delivery
                         specimen, or naming no S12 verdict P item of its
                         file, or covering no line
  sidecar-on-slot-file   a whole-output golden expected/<path>.expect of a
                         learner file whose items carry prediction slots (it
                         holds their answers, H5; pins.py --update refuses to
                         write one)
  reserved-name          over the whole reference tree: a directory, file
                         stem, Dafny module/refines/import name, Rust
                         mod/extern crate/path segment, Cargo package, lib,
                         target or dependency name, or Python import or
                         project name is solutions_policy or solutions-first
                         (any case, '-' read as '_')

The SHARED SLOT RULES section of scripts/firsttry.py is loaded by its marker
lines, so the twins meet the same vacuity rules as the learner's slots.

Output: `path:line: <rule>` only, never content, then one summary line.
With no armed module (every module planned) and no reference file to walk
there is nothing to lint: it says so ("no armed module: nothing to check")
and passes; with armed modules, nothing to lint is a failure (an empty set
fails).
Exit: 0 clean (or nothing to check) · 1 findings, or nothing to lint · 2 usage ·
3 refused (the self-gate, an unknown or planned module, a registry with no
module).
"""

import argparse
import ast
import importlib.machinery
import importlib.util
import re
import sys
import tomllib
import types
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_core():
    if "vcheck" in sys.modules:
        return sys.modules["vcheck"]
    loader = importlib.machinery.SourceFileLoader("vcheck", str(SCRIPTS / "vcheck"))
    spec = importlib.util.spec_from_loader("vcheck", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vcheck"] = mod
    loader.exec_module(mod)
    return mod


BEGIN, END = "# ===== BEGIN SHARED SLOT RULES =====", "# ===== END SHARED SLOT RULES ====="


def load_shared_rules():
    """The SHARED SLOT RULES section of scripts/firsttry.py (spec §3.8.4)."""
    path = SCRIPTS / "firsttry.py"
    text = path.read_text(encoding="utf-8")
    a, b = text.index(BEGIN), text.index(END)
    mod = types.ModuleType("shared_slot_rules")
    exec(compile("\n" * text[:a].count("\n") + text[a:b], str(path), "exec"), mod.__dict__)
    return mod


core = _load_core()
SR = load_shared_rules()
D, V, ci = core.D, core.V, core.ci
TWIN_TREES = ("dafny/Q", "dafny/R", "dafny/checks", "verus/q", "verus/r", "harness/q", "harness/r",
              "specimens", "slots")
SOURCE_EXTS = (".dfy", ".rs", ".py", ".dfy.specimen", ".rs.specimen")
SKIP_DIRS = {"target", "build", "__pycache__", ".git", ".verus-log", ".verus-solver-log",
             "TestResults", "node_modules", ".venv", "venv"}
AGENT_HEADING = re.compile(r"clearly marked.*answers the agentic file", re.I)
REFERENCE_ONLY = re.compile(r"(?://|#).*\breference-only\b")
DUP_KINDS = {"slot-in-reference", "need-missing"}   # reported by the shared rules instead


class Lint:
    def __init__(self, root):
        self.root = Path(root)
        self.out = set()
        self.twins = 0

    def add(self, path, line, rule):
        rel = core.show(path, self.root)
        self.out.add((rel, int(line or 0), rule))


# =====================================================================================
# Twins of one module
# =====================================================================================

def ref(rel):
    return f"{core.REF_DIR}/{rel}"


def learner_files(root, rec):
    """(required twins, optional twins): exercise, exit and harness (learner
    Python) files need one; specimens may have one (their answers are pinned
    by hash or by the twin), agentic files are answered inside the main twin."""
    req, opt = [], []
    listed = rec["exercises"] + rec["exits"] + (rec.get("harness") or [])
    for rel in core.expand_files(root, listed, SOURCE_EXTS):
        if not (Path(root) / rel).is_file():
            continue
        (opt if rel.startswith("specimens/") else req).append(rel)
    return req, opt


def module_writing_items(rec):
    """The item ids whose learner writes whole declarations: the registry's
    admissible rows with `writes = "module"` (D92, Δ310: R08.H1/H4, a
    refinement module or a trait implementation the learner writes whole)."""
    return {k for k, v in (rec.get("admissible") or {}).items()
            if isinstance(v, dict) and v.get("writes") == "module"}


def in_learner_region(raw, line, writers):
    """True when `line` lies inside a `@hole-begin`/`@hole-end` region of the
    twin that belongs to an item of `writers` (module_writing_items): that
    learner writes the declarations there. An ordinary annotation region
    never excuses a twin-only declaration, and broken markers never do (the
    marker rules report them)."""
    if not writers:
        return False
    try:
        regions = core.common.hole_regions("\n".join(raw))
    except ValueError:
        return False
    return any(iid in writers and b < line < e for iid, b, e in regions)


def twin_only_ok(raw, line, lang, decl_attrs=(), writers=frozenset()):
    """A twin-only declaration is allowed: a test, anything after the agent
    reference heading, a declaration marked `reference-only`, or one inside a
    learner region of a module-writing item (in_learner_region)."""
    if any(AGENT_HEADING.search(x) for x in raw[:max(line - 1, 0)]):
        return True
    for ln in (line, line - 1):
        if 1 <= ln <= len(raw) and REFERENCE_ONLY.search(raw[ln - 1]):
            return True
    if in_learner_region(raw, line, writers):
        return True
    return any(a in ("test", "Test") for a in decl_attrs)


def dafny_opaque(text, path):
    """The opaque declarations of a Dafny source: the `opaque` modifier or a
    `{:opaque}` attribute (specfreeze folds opacity into a statement the same way)."""
    src = D.parse_source(text, str(path))
    return {d.qual for d in src.decls if d.kind in D.HASHED_KINDS and
            ("opaque" in d.modifiers or any((a.style, a.name) == ("{:", "opaque")
                                            for a in d.attrs))}


def dafny_tests(text, path):
    src = D.parse_source(text, str(path))
    return {d.qual for d in src.decls
            if any((a.style, a.name) in (("{:", "test"), ("@", "Test")) for a in d.attrs)}


def compare_declarations(L, rel, lang, ltext, ttext, tpath, writers=frozenset()):
    raw = ttext.split("\n")
    lpath = L.root / rel
    # a frame annotation hole (QPLAN §6 Q22, Δ135): a Dafny twin whose header
    # holds a learner region is compared by its frame core, and the learner's
    # ensures clauses must appear in the twin's in order (as specfreeze does)
    frames = []
    if lang == "d":
        try:
            frames = core.frame_symbols(ttext, tpath)
        except ValueError:
            frames = []         # broken markers: the marker rule reports them
    lh, _, lbodyless = core.statement_table(lpath, lang, text=ltext)
    # a Dafny definition shipped with a placeholder body that the twin replaces
    # (QPLAN §30 Q52) is compared by its header, as a bodyless one is (as
    # specfreeze's open_bodies)
    lbodyless = sorted(set(lbodyless) | set(core.open_body_symbols(
        lpath, lang, ltext=ltext, ttext=ttext, tpath=tpath)))
    # a statement hole completed by added requires/ensures clauses (QPLAN §6
    # Q44): compared by its spec core, the shipped clauses kept in order (as
    # specfreeze's open_specs)
    specs = core.open_spec_symbols(lpath, lang, ltext=ltext, ttext=ttext, tpath=tpath,
                                   exclude=set(lbodyless) | set(frames))
    lh, llines, _ = core.statement_table(lpath, lang, set(lbodyless), text=ltext,
                                         open_frames=frames, open_specs=specs)
    th, tlines, _ = core.statement_table(tpath, lang, set(lbodyless), text=ttext,
                                         open_frames=frames, open_specs=specs)
    # a measure the twin adds is no statement change (vcheck measure_free_text,
    # as specfreeze --check judges a learner's)
    tm, _, _ = core.statement_table(tpath, lang, set(lbodyless),
                                    text=core.measure_free_text(ttext, lang, tpath),
                                    open_frames=frames, open_specs=specs)
    # an added `pub` on an open-visibility fn is no statement change (D94; specfreeze)
    tv = {}
    if lang == "v":
        vis = core.open_visibility_names(ltext, ttext)
        if vis:
            tv, _, _ = core.statement_table(tpath, lang, set(lbodyless),
                                            text=core.pub_free_text(ttext, vis),
                                            open_frames=frames, open_specs=specs)
    tests = dafny_tests(ttext, tpath) if lang == "d" else set()
    lop = dafny_opaque(ltext, lpath) if lang == "d" else set()
    top = dafny_opaque(ttext, tpath) if lang == "d" else set()
    for sym in sorted(set(lh) - set(th), key=lambda s: llines.get(s, 0)):
        L.add(lpath, llines.get(sym, 0), "declaration-missing")
    for sym in sorted(set(th) - set(lh), key=lambda s: tlines.get(s, 0)):
        if not twin_only_ok(raw, tlines.get(sym, 0), lang, ("test",) if sym in tests else (),
                            writers):
            L.add(tpath, tlines.get(sym, 0), "declaration-extra")
    for sym in sorted(set(lh) & set(th)):
        if lh[sym] not in (th[sym], tm.get(sym), tv.get(sym)) or (sym in lop) != (sym in top) or (
                sym in frames and not core.is_subsequence(
                    core.frame_ensures(lpath, ltext, {sym}).get(sym, []),
                    core.frame_ensures(tpath, ttext, {sym}).get(sym, []))):
            L.add(tpath, tlines.get(sym, 0), "statement-differs")
    if lang == "d":
        # a module whose import list is frozen (QPLAN §30 Q62) imports the same
        # in the twin
        lsrc, tsrc = D.parse_source(ltext, str(lpath)), D.parse_source(ttext, str(tpath))
        tlines_m = {m.qual: m.line for m in tsrc.modules}
        for mod in sorted(D.frozen_import_modules(lsrc)):
            if D.subtree_imports(lsrc, mod) != D.subtree_imports(tsrc, mod):
                L.add(tpath, tlines_m.get(mod, 0), "imports-differ")
    common_ = set(lh) & set(th)
    lorder = [s for s in sorted(lh, key=lambda s: (llines.get(s, 0), s)) if s in common_]
    torder = [s for s in sorted(th, key=lambda s: (tlines.get(s, 0), s)) if s in common_]
    if lorder != torder:
        k = next(i for i, (a, b) in enumerate(zip(lorder, torder)) if a != b)
        L.add(tpath, tlines.get(torder[k], 0), "declaration-order")


def python_signatures(text):
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return None, e.lineno or 0
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            sig = node.name
            if not isinstance(node, ast.ClassDef):
                sig += "(" + ",".join(a.arg for a in node.args.args) + ")"
            out.append((node.lineno, sig))
    return sorted(out), 0


def python_lines(text):
    """{qualified name: def/class line} under dvl.python.spec_hash's names
    (classes `C`, methods `C.m`, nested functions `f.<locals>.g`)."""
    out = {}

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}{child.name}"
                out.setdefault(name, child.lineno)
                walk(child, f"{name}." if isinstance(child, ast.ClassDef)
                     else f"{name}.<locals>.")
            else:
                walk(child, prefix)
    walk(ast.parse(text), "")
    return out


def compare_python(L, rel, ltext, ttext, tpath):
    lsig, _ = python_signatures(ltext)
    tsig, tline = python_signatures(ttext)
    if tsig is None:
        L.add(tpath, tline, "parse-error")
        return
    if lsig is None:
        return
    # the frozen statements (specfreeze's): each shared function's and class's
    # signature (annotations, defaults, decorators, bases) as the learner's
    lh, th = core.PY.spec_hash(L.root / rel), core.PY.spec_hash(tpath)
    tlines = python_lines(ttext)
    for sym in sorted(set(lh) & set(th)):
        if lh[sym] != th[sym]:
            L.add(tpath, tlines.get(sym, 0), "statement-differs")
    lnames = [s for _, s in lsig]
    tnames = [s for _, s in tsig]
    tline_of = {s: ln for ln, s in tsig}
    lline_of = {s: ln for ln, s in lsig}
    for s in lnames:
        if s not in tnames:
            L.add(L.root / rel, lline_of[s], "declaration-missing")
    raw = ttext.split("\n")
    for s in tnames:
        if s not in lnames and not twin_only_ok(raw, tline_of[s], "py"):
            L.add(tpath, tline_of[s], "declaration-extra")
    if [s for s in lnames if s in tnames] != [s for s in tnames if s in lnames]:
        L.add(tpath, 0, "declaration-order")


def compare_markers(L, rel, ltext, trel, ttext, tpath, slot_file):
    litems, _ = ci.parse_items(rel, ltext)
    titems, terrs = ci.parse_items(trel, ttext, slot_file)
    for e in terrs:
        loc = e.split(":", 2)
        L.add(tpath, loc[1] if len(loc) > 2 and loc[1].isdigit() else 0, "marker-grammar")
    lk = {it["id"]: it for it in litems}
    tk = {it["id"]: it for it in titems}
    for iid, it in lk.items():
        if iid not in tk:
            L.add(L.root / rel, it["line_start"], "marker-missing")
        elif SR.sr_marker_key(it) != SR.sr_marker_key(tk[iid]):
            L.add(tpath, tk[iid]["line_start"], "marker-mismatch")
    for iid, it in tk.items():
        if iid not in lk:
            L.add(tpath, it["line_start"], "marker-extra")
    lo = [it["id"] for it in litems if it["id"] in tk]
    to = [it["id"] for it in titems if it["id"] in lk]
    if lo != to:
        k = next(i for i, (a, b) in enumerate(zip(lo, to)) if a != b)
        L.add(tpath, tk[to[k]]["line_start"], "marker-order")
    return titems


def check_twin_slots(L, trel, ttext, tpath, titems, verdict_values):
    raw = ttext.split("\n")
    for ln in SR.sr_twin_leftovers(raw):
        L.add(tpath, ln, "slot-leftover")
    for it in titems:
        for s in it["slots"]:
            if s["format"] == "verdict":
                continue
            if s["state"] != "enabled":
                L.add(tpath, s["line"], "slot-not-enabled")
                continue
            for _ in SR.sr_slot_problems(it, s, raw, trel):
                L.add(tpath, s["line"], "vacuous-slot")
        if it["kind"] == "X":
            for _ in SR.sr_need_missing(ttext, trel, it):
                L.add(tpath, it["line_start"], "need-missing")
        if it["kind"] in "HXT":
            for ln in SR.sr_missing_receipts(ttext, trel, it):
                L.add(tpath, ln, "receipt-missing")
        if it["format"] == "verdict":
            local = it["id"].split(".", 1)[1]
            v = verdict_values.get(local)
            if v is None or not SR.sr_normalize_answer(SR.sr_slot_value(v[1])) or \
                    v[1].strip() == "???":
                L.add(tpath, it["line_start"], "answer-missing")


def lint_twin(L, mid, rel, slot_file, verdict_values, writers=frozenset()):
    lang = ci.file_lang(rel)
    trel = ref(rel)
    tpath = L.root / trel
    ltext = (L.root / rel).read_text(encoding="utf-8")
    ttext = tpath.read_text(encoding="utf-8")
    L.twins += 1
    if not rel.startswith("specimens/") and \
            not any("Reference Solution" in x for x in ttext.split("\n")[:30]):
        L.add(tpath, 1, "twin-header")
    titems = compare_markers(L, rel, ltext, trel, ttext, tpath, slot_file)
    if lang in ("d", "v"):
        try:
            compare_declarations(L, rel, lang, ltext, ttext, tpath, writers)
        except V.vs.ParseError as e:
            L.add(tpath, e.line, "parse-error")
        found = core.lib(lang).lint([tpath], "reference")
        planted, bad = SR.sr_planted(ttext.split("\n"), trel, titems)
        for ln, _ in bad:
            L.add(tpath, ln, "planted-marker")
        for f in found:
            if f.kind in DUP_KINDS:
                continue
            if f.line in planted and Path(f.file).resolve() == tpath.resolve():
                continue          # a planted trust leap of an S12 delivery twin (sr_planted)
            L.add(f.file, f.line, f.kind)
    elif lang == "py":
        compare_python(L, rel, ltext, ttext, tpath)
        for f in core.lib("py").lint([tpath], "reference", root=L.root):
            L.add(f.file, f.line, f.kind)
    check_twin_slots(L, trel, ttext, tpath, titems, verdict_values)


def lint_module(L, mid):
    rec = core.record(L.root, mid)
    req, opt = learner_files(L.root, rec)
    rslots = ref(f"slots/{rec['id']}.slots")
    rslot_path = L.root / rslots
    verdict_values = {}
    slot_file = None
    if rslot_path.is_file():
        text = rslot_path.read_text(encoding="utf-8")
        table, errs = ci.parse_slot_file(rslots, text)
        for e in errs:
            L.add(rslot_path, e.split(":", 2)[1] if e.count(":") >= 2 else 0, "slot-file-grammar")
        verdict_values = SR.sr_slot_file_values(text)
        slot_file = (rslots, table)
    has_verdicts = False
    for rel in req + opt:
        if not (L.root / ref(rel)).is_file():
            if rel in req:
                L.add(L.root / ref(rel), 0, "twin-missing")
            continue
        lint_twin(L, rec["id"], rel, slot_file, verdict_values, module_writing_items(rec))
    items, _ = core.module_items(L.root, rec)
    has_verdicts = any(it["format"] == "verdict" for it in items)
    if has_verdicts and not rslot_path.is_file():
        L.add(rslot_path, 0, "twin-missing")
    lslots = L.root / f"slots/{rec['id']}.slots"
    if rslot_path.is_file() and not lslots.is_file():
        L.add(rslot_path, 0, "twin-orphan")
    slot_sidecars(L, core.expand_files(L.root, core.module_files(rec), SOURCE_EXTS))
    return rec


def slot_sidecars(L, rels=None):
    """Sidecars of learner files that carry prediction slots: every sidecar
    under expected/, or those of `rels`."""
    exp = L.root / "expected"
    if rels is None:
        scs = sorted(exp.rglob("*.expect")) if exp.is_dir() else []
    else:
        scs = [exp / f"{r}.expect" for r in rels if (exp / f"{r}.expect").is_file()]
    for sc in scs:
        rel = sc.relative_to(exp).as_posix()[:-len(".expect")]
        src = L.root / rel
        if src.is_file() and core.slot_bearing(rel, src.read_text(encoding="utf-8")):
            L.add(sc, 0, "sidecar-on-slot-file")


def orphans(L, mids):
    """Twin files under the twin trees with no learner file."""
    for tree in TWIN_TREES:
        d = L.root / ref(tree)
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*")):
            if not p.is_file() or set(p.relative_to(d).parts) & SKIP_DIRS:
                continue
            if not p.name.endswith(SOURCE_EXTS + (".slots",)):
                continue
            learner = p.relative_to(L.root / core.REF_DIR).as_posix()
            if not (L.root / learner).is_file():
                L.add(p, 0, "twin-orphan")


# =====================================================================================
# Reserved names over the whole reference tree (Δ79, Δ86)
# =====================================================================================

def reserved(name):
    return core.ccm.reserved(name)


def python_reserved(text):
    """Lines of Python imports whose head is a reserved name."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            heads = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            heads = [node.module.split(".")[0]]
        else:
            continue
        if any(reserved(h) for h in heads):
            out.append(node.lineno)
    return out


def pyproject_reserved(text):
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return [0]
    names = [data.get("project", {}).get("name")]
    st = data.get("tool", {}).get("setuptools", {})
    for key in ("packages", "py-modules"):
        v = st.get(key)
        if isinstance(v, list):
            names += v
    return [0] if any(isinstance(n, str) and reserved(n) for n in names) else []


def reserved_walk(L):
    base = L.root / core.REF_DIR
    if not base.is_dir():
        return 0
    n = 0
    for p in sorted(base.rglob("*")):
        rel_parts = p.relative_to(base).parts
        if set(rel_parts[:-1]) & SKIP_DIRS or any(x.endswith("-py") for x in rel_parts[:-1]):
            continue
        if p.is_symlink():
            continue
        stem = p.name.split(".")[0]
        if reserved(stem) or reserved(p.stem):
            L.add(p, 0, "reserved-name")
        if not p.is_file():
            continue
        n += 1
        name = p.name
        try:
            if name.endswith((".dfy", ".dfy.specimen")):
                for f in D.lint_source(p.read_text(encoding="utf-8"), str(p), "learner"):
                    if f.kind == "reserved-name":
                        L.add(p, f.line, "reserved-name")
            elif name.endswith((".rs", ".rs.specimen")):
                for f in V.lint_source(p.read_text(encoding="utf-8"), str(p), "learner"):
                    if f.kind == "reserved-name":
                        L.add(p, f.line, "reserved-name")
            elif name == "Cargo.toml":
                for f in V.lint_manifest(p):
                    L.add(p, f.line, f.kind)
            elif name.endswith(".py"):
                for ln in python_reserved(p.read_text(encoding="utf-8")):
                    L.add(p, ln, "reserved-name")
            elif name == "pyproject.toml":
                for ln in pyproject_reserved(p.read_text(encoding="utf-8")):
                    L.add(p, ln, "reserved-name")
        except (UnicodeDecodeError, OSError):
            continue
    return n


# =====================================================================================
# CLI
# =====================================================================================

def main(argv=None):
    ap = argparse.ArgumentParser(prog="reference_lint.py", description="Lint reference twins.")
    ap.add_argument("--module", metavar="ID", help="one module (default: every non-planned one)")
    # Kept so a caller written before DV1c still parses; it no longer changes
    # anything (no armed module passes loudly by itself).
    ap.add_argument("--allow-empty", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--root", type=Path, default=core.REPO, help=argparse.SUPPRESS)
    try:
        a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as e:
        return core.EXIT_USAGE if e.code else 0
    root = a.root.resolve()
    try:
        core.require_author(root, "reference_lint.py")
        if a.module:
            mids, idle = [core.record(root, a.module)["id"]], None
        else:
            mids, idle = core.armed_or_none(root)
        L = Lint(root)
        for mid in mids:
            lint_module(L, mid)
        if not a.module:
            orphans(L, mids)
            slot_sidecars(L)
        walked = reserved_walk(L)
    except core.Refusal as e:
        print(f"reference_lint: refused: {e}", file=sys.stderr)
        return core.EXIT_REFUSED
    for rel, line, rule in sorted(L.out):
        print(f"{rel}:{line}: {rule}")
    if not L.twins and not walked:
        if idle and not L.out:
            print(f"reference_lint: {idle}; no reference file: passing loudly")
            return core.EXIT_OK
        print(f"reference_lint: nothing to lint ({len(mids)} non-planned module(s), no reference "
              "file); an empty set fails")
        return core.EXIT_FAIL
    print(f"reference_lint: {len(L.out)} finding(s); {L.twins} twin(s) in {len(mids)} module(s); "
          f"{walked} reference file(s) checked for reserved names")
    return core.EXIT_OK if not L.out else core.EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
