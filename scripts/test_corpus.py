#!/usr/bin/env python3
"""test_corpus.py — the cheat-corpus runner (phase DV1c, reopened; DELTAS Δ106).

The cheat corpus, tests/corpus/, holds tiny invented programs. Each one uses a
construct that can make a verifier exit 0 without a complete proof (spec §11.4
rows G1–G22 and V1–V25, and the DELTAS additions), or is a healthy control.
Each fixture's manifest.toml records, from real runs on the pinned tools, the
exit code of the plain verifier run, which instruments flag the fixture, and
the sha256 of each instrument's normalized output. tests/corpus/README.md
holds the format, the instrument commands and the hash rules. This runner is
the corpus's only executor, and it runs the instruments only through the
course wrappers (scripts/vcheck, scripts/vaudit, scripts/specfreeze) and the
plain run only through dvl's capped job plumbing.

Usage:
  test_corpus.py --list
      one line per fixture: id, lang, half, kind, X class, directory. An
      empty corpus or an unreadable manifest fails.
  test_corpus.py [--ci] [SEL ...] [--only SEL]... [--jobs N] [--keep]
      the default mode. First the static checks of every manifest (schema,
      file lists, names, includes and path dependencies kept inside the
      fixture, covered_by references resolved), then, per selected fixture,
      the plain run and every [[expect]] instrument, each compared with the
      manifest (plain_exit, outcome, output_sha256, and exit and argv where
      recorded). Prints PASS or FAIL per fixture with locations only (each
      observed output goes to a file in the run's scratch, kept on failure),
      then a summary. With no selection it also runs the corpus-level checks:
      each half (Q, R) covers every X family that the language's corpus
      covers, every catalog row has a fixture, and each language has its
      controls (Δ106).
  test_corpus.py --update [SEL ...] [--only SEL]... [--jobs N] [--keep]
      author-only (CI set to true, or the author's linked worktree off a
      learner branch: the three-condition test of spec §7.4, as
      reference_lint.py applies it). Runs each selected fixture twice and
      re-pins output_sha256 (and fills a missing plain_exit) where both runs
      agree and every observed outcome, exit and plain_exit equals the
      recorded one. It never changes an outcome: an outcome that moved is a
      decision for the author, made by editing the manifest by hand.

  SEL is a fixture id (G01, V-2, C-1), LANG/ID (dafny/C-01) or a fixture
  directory (tests/corpus/verus/V01).
  --jobs N  fixtures in flight at once (default 1, at most 4). Whatever N is,
            every solver job takes the dvl pool slot of its language with
            DVL_DAFNY_JOBS=1 and DVL_VERUS_JOBS=1, so at most one Dafny job
            (8 GB cap) and one Verus job (16 GB cap) run at a time.
  --keep    keep the run's scratch directory after a passing run.

Memory (CLAUDE.md §Resources): every solver job runs under the dvl caps of
scripts/dvl/pins.toml, one per language at a time. Before the first solver
job, MemAvailable must hold the caps that can run at once plus a 15 GB
reserve, else nothing starts (exit 1). A job killed by memory (exit 137 or
143, or a wrapper verdict killed(memory)) is reported as killed(memory),
never as an outcome, and --update never pins it.

Scratch: $DVL_SCRATCH (else /tmp/dvl0-corpus-<uid>) gets one directory per
run, deleted after a passing run unless --keep; the tools see it as their
DVL_SCRATCH, and the hash rules replace it.

Exit: 0 every check passed · 1 a check failed (or the memory preflight) ·
2 usage · 3 refused (--update outside the author's context, a missing pinned
toolchain).
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
CORPUS = ROOT / "tests" / "corpus"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_course_map as ccm  # noqa: E402  (reference names, the one definition)

EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_REFUSED = 0, 1, 2, 3
LANGS = ("dafny", "verus")
HALVES = ("Q", "R")
KINDS = ("construct", "control", "covered-elsewhere")
OUTCOMES = ("flagged", "clean", "unknown")
TOOLS = ("vcheck --gate", "vaudit", "specfreeze --check", "lint", "witness", "swap-to-false",
         "json-completeness", "seed-rerun")
# Spec §5.6: the grader-only classes. A gate must answer UNKNOWN on them, never
# PASS (design §11.2, gate v2); vcheck has no UNKNOWN verdict, so this runner
# reads a gate pass on such a fixture as `unknown`, never as `clean`.
GRADER_ONLY = ("X07", "X08", "X14")
XCLASS = re.compile(r"X(0[1-9]|1[0-8])")
# Fixture ids (the README's grammar): a catalog row of spec §11.4 (G1–G22;
# V1–V24 and Δ19's V25), optionally with a letter for a second fixture of the
# row; a DELTAS addition D-<n> or V-<n>; a control C-<n>.
CATALOG = {"dafny": [f"G{n:02d}" for n in range(1, 23)],
           "verus": [f"V{n:02d}" for n in range(1, 26)]}
ID_CATALOG = {"dafny": re.compile(r"G(0[1-9]|1\d|2[0-2])[a-z]?"),
              "verus": re.compile(r"V(0[1-9]|1\d|2[0-5])[a-z]?")}
ID_DELTA = {"dafny": re.compile(r"D-\d+"), "verus": re.compile(r"V-\d+")}   # D-01 or D-1
ID_CONTROL = re.compile(r"C-\d+")
MIN_CONTROLS = 6           # Δ106: at least 6 healthy decoys per language
SHA = re.compile(r"[0-9a-f]{64}")
TOP_KEYS = {"id", "lang", "half", "xclass", "kind", "title", "files", "plain_exit", "target",
            "expect"}
EXPECT_KEYS = {"tool", "outcome", "kinds", "output_sha256", "summary", "covered_by", "argv",
               "exit"}
# Name stems that mark reference, held-out or sealed material (guard rule 1;
# Δ105): no path component of the corpus may contain one.
BAD_STEMS = tuple(sorted(ccm.REFERENCE_STEMS)) + ("unseal",)
BUILD_DIRS = {"target", ".verus-log", ".verus-solver-log", "__pycache__", "TestResults"}
KILLED = (137, 143)
DAFNY_REFINES = re.compile(r"^\s*(abstract\s+)?module\s+\S+\s+refines\s", re.M)


class Refused(Exception):
    """Exit 3."""


# =====================================================================================
# Fixtures and manifests
# =====================================================================================

@dataclass
class Fixture:
    lang: str
    dir: Path
    data: dict = field(default_factory=dict)
    text: str = ""
    problems: list = field(default_factory=list)   # (line, message)

    @property
    def rel(self):
        return self.dir.relative_to(ROOT).as_posix()

    @property
    def manifest(self):
        return f"{self.rel}/manifest.toml"

    @property
    def id(self):
        v = self.data.get("id")
        return v if isinstance(v, str) else self.dir.name

    @property
    def kind(self):
        return self.data.get("kind")

    @property
    def runs(self):
        return self.kind in ("construct", "control")

    def bad(self, line, msg):
        self.problems.append((line, msg))

    def expects(self):
        e = self.data.get("expect")
        return e if isinstance(e, list) else []

    def expect_line(self, k):
        """The 1-based line of the k-th [[expect]] header (0 when unknown)."""
        n = 0
        for i, line in enumerate(self.text.splitlines(), 1):
            if line.strip() == "[[expect]]":
                if n == k:
                    return i
                n += 1
        return 0

    def key_line(self, key):
        rx = re.compile(rf"^{re.escape(key)}\s*=")
        for i, line in enumerate(self.text.splitlines(), 1):
            if line.lstrip().startswith("[["):
                break
            if rx.match(line):
                return i
        return 0


def sort_key(fx):
    i = fx.id
    m = re.fullmatch(r"([A-Z])(-?)(\d+)([a-z]?)", i)
    if not m:
        return (LANGS.index(fx.lang) if fx.lang in LANGS else 9, 9, 0, i)
    cat = 2 if m[1] == "C" else (1 if m[2] else 0)
    return (LANGS.index(fx.lang) if fx.lang in LANGS else 9, cat, int(m[3]), m[4])


def load_corpus():
    """(fixtures, corpus-level problems). Every directory under
    tests/corpus/<lang>/ is a fixture and needs a manifest."""
    fixtures, problems = [], []
    if not CORPUS.is_dir():
        return [], ["tests/corpus/ does not exist"]
    for p in sorted(CORPUS.iterdir()):
        if p.is_dir():
            if p.name not in LANGS:
                problems.append(f"tests/corpus/{p.name}/: not a corpus language "
                                f"({', '.join(LANGS)})")
        elif p.name != "README.md":
            problems.append(f"tests/corpus/{p.name}: a stray file (only README.md and the "
                            "language directories live here)")
    for lang in LANGS:
        ld = CORPUS / lang
        if not ld.is_dir():
            continue
        for d in sorted(ld.iterdir()):
            if not d.is_dir():
                problems.append(f"{d.relative_to(ROOT).as_posix()}: a stray file (a fixture is "
                                "a directory)")
                continue
            fx = Fixture(lang, d)
            mp = d / "manifest.toml"
            try:
                fx.text = mp.read_text(encoding="utf-8")
                fx.data = tomllib.loads(fx.text)
            except FileNotFoundError:
                fx.bad(0, "no manifest.toml")
            except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
                fx.bad(0, f"unreadable manifest ({type(e).__name__}: {e})")
            fixtures.append(fx)
    fixtures.sort(key=sort_key)
    return fixtures, problems


def target_rel(fx):
    """The repo-relative path the tools run: Dafny <dir>/main.dfy, Verus the
    crate <dir> (or <dir>/<target>)."""
    t = fx.data.get("target")
    if not isinstance(t, str) or not t:
        t = "main.dfy" if fx.lang == "dafny" else "."
    return posixpath.normpath(f"{fx.rel}/{t}")


def tool_files(fx, tool):
    """Files an instrument needs besides the target (relative to the fixture)."""
    if fx.lang == "dafny":
        return {"witness": ["witness.dfy"], "swap-to-false": ["swap.dfy"],
                "specfreeze --check": ["frozen.dfy"]}.get(tool, [])
    return {"witness": ["witness/Cargo.toml"], "swap-to-false": ["swapped/Cargo.toml"],
            "specfreeze --check": ["frozen.rs"]}.get(tool, [])


def command(fx, tool):
    """The wrapper command (repo-relative argv, run from the course root) of
    an instrument, or None for json-completeness (read from the plain run)."""
    d, t = fx.rel, target_rel(fx)
    dafny = fx.lang == "dafny"
    if tool == "vcheck --gate":
        return ["scripts/vcheck", "--gate", t]
    if tool == "vaudit":
        return ["scripts/vaudit", t]
    if tool == "seed-rerun":
        return ["scripts/vcheck", "--brittleness", t]
    if tool == "witness":
        return ["scripts/vcheck", "--gate", f"{d}/witness.dfy" if dafny else f"{d}/witness"]
    if tool == "swap-to-false":
        return ["scripts/vcheck", "--gate", f"{d}/swap.dfy" if dafny else f"{d}/swapped"]
    if tool == "specfreeze --check":
        if dafny:
            return ["scripts/specfreeze", "--against", f"{d}/frozen.dfy", t]
        return ["scripts/specfreeze", "--against", f"{d}/frozen.rs", f"{t}/src/lib.rs"]
    if tool == "json-completeness" and not dafny:
        return None
    raise ValueError(f"no runner command for {tool!r} in {fx.lang}")


def supported(fx, tool):
    if tool == "lint":
        return ("no instrument command: the lint runs inside vaudit and vcheck --gate; record "
                "its findings under those tools")
    if tool == "json-completeness" and fx.lang != "verus":
        return "json-completeness reads Verus's --output-json; Dafny has no such record"
    return None


# =====================================================================================
# Static checks
# =====================================================================================

def check_schema(fx, update=False):
    """The manifest format (tests/corpus/README.md). Under --update a new
    fixture may still lack plain_exit and output_sha256: --update fills them."""
    d = fx.data
    if not d:
        fx.bad(0, "an empty manifest")
        return
    for k in sorted(set(d) - TOP_KEYS):
        fx.bad(fx.key_line(k), f"unknown key {k!r}")
    for k in ("id", "lang", "half", "xclass", "kind", "title"):
        if not isinstance(d.get(k), str):
            fx.bad(fx.key_line(k), f"{k} must be a string")
    if fx.problems:
        return
    if fx.dir.name != d["id"] and not fx.dir.name.startswith(d["id"] + "_"):
        fx.bad(fx.key_line("id"), f"id {d['id']!r} does not name the directory (<ID> or "
                                  "<ID>_<slug>)")
    if d["lang"] != fx.lang:
        fx.bad(fx.key_line("lang"), f"lang {d['lang']!r} differs from the parent directory")
    if d["half"] not in HALVES:
        fx.bad(fx.key_line("half"), f"half must be Q or R, not {d['half']!r}")
    kind = d["kind"]
    if kind not in KINDS:
        fx.bad(fx.key_line("kind"), f"kind must be one of {', '.join(KINDS)}")
        return
    i = d["id"]
    if kind == "control":
        if not ID_CONTROL.fullmatch(i):
            fx.bad(fx.key_line("id"), "a control's id is C-<n>")
        if d["xclass"] != "":
            fx.bad(fx.key_line("xclass"), 'a control has xclass = ""')
    else:
        if not (ID_CATALOG[fx.lang].fullmatch(i) or ID_DELTA[fx.lang].fullmatch(i)):
            fx.bad(fx.key_line("id"), f"id {i!r} is neither a {fx.lang} catalog row nor a "
                                      "DELTAS addition (README: ids)")
        if not XCLASS.fullmatch(d["xclass"]):
            fx.bad(fx.key_line("xclass"), "xclass must be X01..X18 (spec §5.6)")
    if not d["title"].strip() or "\n" in d["title"]:
        fx.bad(fx.key_line("title"), "title must be one non-empty line")
    files = d.get("files")
    if not isinstance(files, list) or not all(isinstance(x, str) for x in files):
        fx.bad(fx.key_line("files"), "files must be a list of strings")
    elif kind == "covered-elsewhere" and files:
        fx.bad(fx.key_line("files"), "a covered-elsewhere row has no program (files = [])")
    elif kind != "covered-elsewhere" and not files:
        fx.bad(fx.key_line("files"), "files is empty")
    if "target" in d and (not isinstance(d["target"], str) or not d["target"]):
        fx.bad(fx.key_line("target"), "target must be a non-empty relative path")
    if kind == "covered-elsewhere":
        if "plain_exit" in d:
            fx.bad(fx.key_line("plain_exit"), "a covered-elsewhere row runs nothing: no "
                                              "plain_exit")
    elif type(d.get("plain_exit")) is not int and not (update and "plain_exit" not in d):
        fx.bad(fx.key_line("plain_exit"), "plain_exit must be an integer (the captured exit "
                                          "of the plain verifier run)")
    ex = d.get("expect")
    if not isinstance(ex, list) or not ex or not all(isinstance(e, dict) for e in ex):
        fx.bad(0, "no [[expect]] table")
        return
    seen = {}
    for k, e in enumerate(ex):
        at = fx.expect_line(k)
        for key in sorted(set(e) - EXPECT_KEYS):
            fx.bad(at, f"[[expect]]: unknown key {key!r}")
        tool, outcome = e.get("tool"), e.get("outcome")
        if tool not in TOOLS:
            fx.bad(at, f"tool must be one of: {', '.join(TOOLS)}")
            continue
        if tool in seen:
            fx.bad(at, f"{tool} has two tables (the first at line {seen[tool]})")
        seen[tool] = at
        if outcome not in OUTCOMES:
            fx.bad(at, f"{tool}: outcome must be one of {', '.join(OUTCOMES)}")
        if not isinstance(e.get("kinds"), list) or \
                not all(isinstance(x, str) for x in e.get("kinds", [])):
            fx.bad(at, f"{tool}: kinds must be a list of strings")
        if not isinstance(e.get("summary"), str) or not e["summary"].strip():
            fx.bad(at, f"{tool}: summary must be a non-empty string")
        if kind == "covered-elsewhere":
            cb = e.get("covered_by")
            if not isinstance(cb, list) or not cb or not all(isinstance(x, str) for x in cb):
                fx.bad(at, f"{tool}: covered_by must name at least one test")
            for key in ("output_sha256", "argv", "exit"):
                if key in e:
                    fx.bad(at, f"{tool}: a covered-elsewhere row runs nothing: no {key}")
            continue
        if "covered_by" in e:
            fx.bad(at, f"{tool}: covered_by belongs to covered-elsewhere rows only")
        why = supported(fx, tool)
        if why:
            fx.bad(at, f"{tool}: {why}")
        if update and "output_sha256" not in e:
            pass                                  # a new table: --update pins it
        elif not isinstance(e.get("output_sha256"), str) or \
                not SHA.fullmatch(e["output_sha256"]):
            fx.bad(at, f"{tool}: output_sha256 must be 64 lower-case hex digits")
        if "argv" in e and (not isinstance(e["argv"], list) or
                            not all(isinstance(x, str) for x in e["argv"])):
            fx.bad(at, f"{tool}: argv must be a list of strings")
        if "exit" in e and type(e["exit"]) is not int:
            fx.bad(at, f"{tool}: exit must be an integer")
        if outcome == "unknown" and not (tool == "vcheck --gate" and
                                         d["xclass"] in GRADER_ONLY):
            fx.bad(at, f"{tool}: outcome unknown is the gate's answer on a grader-only class "
                       f"({', '.join(GRADER_ONLY)}) only")
        if outcome == "clean" and tool == "vcheck --gate" and d["xclass"] in GRADER_ONLY:
            fx.bad(at, f"{tool}: a gate pass on a grader-only class is unknown, never clean")
        if kind == "control" and outcome != "clean":
            fx.bad(at, f"{tool}: a control is clean on every instrument")
        for f in tool_files(fx, tool):
            if not (fx.dir / f).is_file():
                fx.bad(at, f"{tool}: needs {f} in the fixture")
    if kind == "construct" and not any(e.get("outcome") in ("flagged", "unknown") for e in ex):
        fx.bad(0, "a construct needs at least one instrument that flags it (or the grader-only "
                  "gate's unknown)")


def bad_name(name):
    low = name.lower()
    return next((s for s in BAD_STEMS if s in low), None)


def check_tree(fx):
    """File list = disk; names; no build output; the target exists."""
    on_disk = []
    for p in sorted(fx.dir.rglob("*")):
        rel = p.relative_to(fx.dir).as_posix()
        stem = bad_name(p.name)
        if stem or ccm.is_reference(f"{fx.rel}/{rel}") or ccm.reserved(p.name.split(".")[0]):
            fx.bad(0, f"{rel}: a reference, held-out or reserved name (guard rule 1, Δ105)")
        if p.is_dir() and (p.name in BUILD_DIRS or ccm.DAFNY_OUTPUT_DIR.fullmatch(p.name)):
            fx.bad(0, f"{rel}/: a build output inside the corpus (guard rule 1d)")
        if p.is_symlink():
            fx.bad(0, f"{rel}: a symbolic link (fixtures hold plain files only)")
        elif p.is_file() and p.name != "manifest.toml":
            on_disk.append(rel)
    if stem := bad_name(fx.dir.name):
        fx.bad(0, f"the directory name holds {stem!r} (guard rule 1, Δ105)")
    files = fx.data.get("files")
    if isinstance(files, list) and all(isinstance(x, str) for x in files):
        for f in files:
            if f.startswith("/") or ".." in Path(f).parts:
                fx.bad(fx.key_line("files"), f"files: {f!r} leaves the fixture")
        for f in sorted(set(on_disk) - set(files)):
            fx.bad(fx.key_line("files"), f"{f} is on disk but not in files")
        for f in sorted(set(files) - set(on_disk)):
            fx.bad(fx.key_line("files"), f"{f} is listed in files but missing")
    if fx.runs:
        t = ROOT / target_rel(fx)
        inside = t.resolve().is_relative_to(fx.dir.resolve())
        want = t if fx.lang == "dafny" else t / "Cargo.toml"
        if not inside or not want.is_file():
            fx.bad(fx.key_line("target") or fx.key_line("files"),
                   f"the target {target_rel(fx)} is not a "
                   f"{'Dafny file' if fx.lang == 'dafny' else 'crate'} inside the fixture")


INCLUDE_FORMS = (
    re.compile(r'^\s*include\s+"([^"]+)"', re.M),                         # Dafny
    re.compile(r'#\[\s*path\s*=\s*"([^"]+)"\s*\]'),                        # Rust #[path]
    re.compile(r'include(?:_str|_bytes)?!\s*\(\s*"([^"]+)"'),              # Rust include!
)
DEP_TABLES = ("dependencies", "dev-dependencies", "build-dependencies")


def check_reach(fx):
    """Every include, #[path], include! and Cargo path inside the fixture."""
    base = fx.dir.resolve()

    def inside(src, ref, what):
        p = (src.parent / ref).resolve()
        rel = src.relative_to(fx.dir).as_posix()
        if not p.is_relative_to(base):
            fx.bad(0, f"{rel}: {what} {ref!r} reaches outside the fixture")
        elif ccm.is_reference(p.relative_to(ROOT.resolve()).as_posix()):
            fx.bad(0, f"{rel}: {what} {ref!r} names reference material")

    for src in sorted(fx.dir.rglob("*")):
        if not src.is_file():
            continue
        if src.suffix in (".dfy", ".rs"):
            text = src.read_text(encoding="utf-8", errors="replace")
            for rx in INCLUDE_FORMS:
                for m in rx.finditer(text):
                    inside(src, m.group(1), "the include or path form")
        elif src.name == "Cargo.toml":
            try:
                cargo = tomllib.loads(src.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
                fx.bad(0, f"{src.relative_to(fx.dir).as_posix()}: unreadable "
                          f"({type(e).__name__})")
                continue
            tables = [cargo.get(t) for t in DEP_TABLES]
            for tt in (cargo.get("target") or {}).values():
                if isinstance(tt, dict):
                    tables += [tt.get(t) for t in DEP_TABLES]
            for tab in tables:
                for dep in (tab or {}).values() if isinstance(tab, dict) else []:
                    if isinstance(dep, dict) and isinstance(dep.get("path"), str):
                        inside(src, dep["path"], "the path dependency")
            lib = cargo.get("lib")
            if isinstance(lib, dict) and isinstance(lib.get("path"), str):
                inside(src, lib["path"], "the [lib] path")


PYTEST_REF = re.compile(r"(tests/[A-Za-z0-9_/.-]+\.py)::([A-Za-z_]\w*)::([A-Za-z_]\w*)")
HOOK_REF = re.compile(r"(tests/hooks/templates/[A-Za-z0-9_.-]+\.jsonl) \((.+)\)")
_AST_CACHE, _WHY_CACHE = {}, {}


def test_exists(ref):
    """None when the covered_by reference names an existing test, else why
    not. Forms: tests/<file>.py::Class::test, or a guard fixture by its
    `why`: tests/hooks/templates/<file>.jsonl (<why>)."""
    m = PYTEST_REF.fullmatch(ref)
    if m:
        path = ROOT / m[1]
        if path not in _AST_CACHE:
            try:
                _AST_CACHE[path] = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError) as e:
                _AST_CACHE[path] = e
        tree = _AST_CACHE[path]
        if isinstance(tree, Exception):
            return f"{m[1]} is missing or does not parse ({type(tree).__name__})"
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == m[2]:
                if any(isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and f.name == m[3]
                       for f in node.body):
                    return None
                return f"{m[1]}: class {m[2]} has no method {m[3]}"
        return f"{m[1]} has no class {m[2]}"
    m = HOOK_REF.fullmatch(ref)
    if m:
        path = ROOT / m[1]
        if path not in _WHY_CACHE:
            whys = set()
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    s = line.strip()
                    if s and not s.startswith("//"):
                        try:
                            whys.add(json.loads(s).get("why"))
                        except (ValueError, AttributeError):
                            pass
            except OSError:
                whys = None
            _WHY_CACHE[path] = whys
        whys = _WHY_CACHE[path]
        if whys is None:
            return f"{m[1]} is missing"
        return None if m[2] in whys else f"{m[1]} has no fixture whose why is {m[2]!r}"
    return "not a test reference (tests/<file>.py::Class::test, or " \
           "tests/hooks/templates/<file>.jsonl (<why>))"


def check_covered(fx):
    n = 0
    for k, e in enumerate(fx.expects()):
        for ref in e.get("covered_by") or []:
            if not isinstance(ref, str):
                continue
            why = test_exists(ref)
            n += 1
            if why:
                fx.bad(fx.expect_line(k), f"covered_by {ref}: {why}")
    return n


def static_checks(fx, update=False):
    if fx.problems:              # unreadable manifest
        return 0
    check_schema(fx, update)
    check_tree(fx)
    check_reach(fx)
    return check_covered(fx) if fx.kind == "covered-elsewhere" else 0


def corpus_checks(fixtures):
    """Corpus-level problems and the coverage lines for the summary."""
    probs, lines = [], []
    good = [f for f in fixtures if f.data.get("kind") in KINDS and f.data.get("half") in HALVES
            and isinstance(f.data.get("xclass"), str)]
    for lang in LANGS:
        mine = [f for f in good if f.lang == lang]
        if not mine:
            probs.append(f"tests/corpus/{lang}/: no fixture (an empty set fails)")
            continue
        rows = [f for f in mine if f.kind != "control"]
        fam = {f.data.get("xclass") for f in rows}
        gaps = 0
        for h in HALVES:
            have = {f.data.get("xclass") for f in rows if f.data["half"] == h}
            if missing := sorted(fam - have):
                gaps += 1
                probs.append(f"tests/corpus/{lang}/: half {h} has no fixture of "
                             f"{', '.join(missing)} (design §9.2 item 2: each half covers "
                             "every X family)")
        if not gaps:
            lines.append(f"{lang}: Q and R each cover all {len(fam)} X families of its "
                         f"constructs and covered rows ({' '.join(sorted(fam))})")
        ids = {f.id for f in rows}
        if missing := [r for r in CATALOG[lang]
                       if not any(i == r or (i.startswith(r) and i[len(r):].isalpha())
                                  for i in ids)]:
            probs.append(f"tests/corpus/{lang}/: no fixture for catalog row(s) "
                         f"{', '.join(missing)} (spec §11.4)")
        nc = sum(1 for f in mine if f.kind == "control")
        if nc < MIN_CONTROLS:
            probs.append(f"tests/corpus/{lang}/: {nc} control(s), fewer than {MIN_CONTROLS} "
                         "(Δ106)")
    return probs, lines


# =====================================================================================
# Running: normalization, instruments, the plain run
# =====================================================================================

class Ctx:
    scratch: Path = None
    logs: Path = None


CTX = Ctx()


def normalize(lang, out, err):
    """The text whose sha256 a manifest pins (README: hash rules). Each
    language keeps the rule its fixtures were captured under."""
    scratch = str(CTX.scratch)
    if lang == "dafny":
        text = (out + err).replace(str(ROOT), "<root>").replace(scratch, "<scratch>")
        text = re.sub(r"raw output: \S+", "raw output: <raw>", text)
        text = re.sub(r"widest spread \S+ \d+\.\.\d+ \(CV [0-9.]+%\)", "<spread>", text)
        return " ".join(text.split())
    s = out + (("\n--- stderr ---\n" + err) if err.strip() else "")
    s = s.replace(str(ROOT) + "/", "")
    s = re.sub(re.escape(scratch) + r"\S*", "<SCRATCH>", s)
    return "\n".join(line.rstrip() for line in s.splitlines()).strip() + "\n"


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tool_env():
    env = dict(os.environ)
    env.pop("CI", None)                 # the instruments never take an author path
    env.update(DVL_SCRATCH=str(CTX.scratch), DVL_DAFNY_JOBS="1", DVL_VERUS_JOBS="1",
               PYTHONDONTWRITEBYTECODE="1")
    return env


def wall_clock(lang):
    from dvl import common
    return int(common.load_pins()[lang]["wall_clock_s"])


@dataclass
class Obs:
    tool: str
    outcome: str          # flagged | clean | unknown | error | killed(memory)
    sha: str = ""
    exit: int | None = None
    argv: list = field(default_factory=list)
    log: str = ""


def outcome_of(fx, tool, rc, text):
    if rc in KILLED or "killed(memory)" in text:
        return "killed(memory)"
    if rc not in (0, 1):
        return "error"
    if tool == "swap-to-false":
        return "flagged" if rc == 0 else "clean"      # a false conclusion that verifies
    if rc == 1:
        return "flagged"
    if tool == "vcheck --gate" and fx.data.get("xclass") in GRADER_ONLY:
        return "unknown"                              # never read a pass there as done
    return "clean"


def log_path(fx, k, tool, rep):
    d = CTX.logs / fx.lang / fx.id
    d.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", tool).strip("-")
    return d / f"{k + 1}-{slug}{'' if rep == 0 else f'.run{rep + 1}'}.txt"


def run_tool(fx, k, tool, rep=0):
    argv = command(fx, tool)
    full = [sys.executable, "-B", str(ROOT / argv[0]), *argv[1:]]
    limit = wall_clock(fx.lang) * 3 + 600
    t0 = time.monotonic()
    try:
        p = subprocess.run(full, cwd=ROOT, env=tool_env(), capture_output=True, text=True,
                           timeout=limit, stdin=subprocess.DEVNULL)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        rc, out, err = 124, "", f"test_corpus: no answer within {limit} s; the tool was stopped\n"
    norm = normalize(fx.lang, out, err)
    lp = log_path(fx, k, tool, rep)
    lp.write_text(f"$ {' '.join(argv)}\n# exit {rc}, {time.monotonic() - t0:.1f}s; sha256 "
                  f"{sha256(norm)} of the normalized output below\n{norm}\n"
                  f"# ---- raw stdout ----\n{out}\n# ---- raw stderr ----\n{err}\n",
                  encoding="utf-8")
    return Obs(tool, outcome_of(fx, tool, rc, out + err), sha256(norm), rc, argv,
               lp.as_posix())


@dataclass
class Plain:
    exit: int | None
    vr: dict | None = None        # Verus: the verification-results object
    argv: list = field(default_factory=list)
    note: str = ""


def plain_dafny(fx):
    """dafny verify with only the resource pins (no audit, no wrapper policy):
    the target alone, or frozen.dfy first when main.dfy refines a module."""
    from dvl import common
    tc, p = common.toolchain("dafny"), common.load_pins()["dafny"]
    t = ROOT / target_rel(fx)
    files = [t]
    frozen = fx.dir / "frozen.dfy"
    if frozen.is_file() and DAFNY_REFINES.search(t.read_text(encoding="utf-8")):
        files = [frozen, t]
    argv = [str(tc["dafny"]), "verify", *[str(f) for f in files],
            "--resource-limit", str(p["resource_limit"]), "--cores", str(p["cores"]),
            "--solver-path", str(tc["dafny_z3"])]
    rc, _, _ = common.run_capped(argv, p["mem_gb"], p["wall_clock_s"], pool="dafny",
                                 out_dir=common.scratch_dir("corpus-plain-dafny"))
    shown = ["dafny", "verify", *[f.relative_to(ROOT).as_posix() for f in files],
             "--resource-limit", str(p["resource_limit"]), "--cores", str(p["cores"]),
             "--solver-path", "<z3>"]
    return Plain(rc, None, shown)


def plain_verus(fx):
    """The pinned verus command WITHOUT --no-cheating, path dependencies built
    first as the wrappers build them (dvl.verus's capped job plumbing)."""
    from dvl import common
    from dvl import verus as V
    t = ROOT / target_rel(fx)
    run = V.Run(common.scratch_dir("corpus-plain-verus"), str(t))
    try:
        plan = V.resolve(str(t), run)
        run.files = plan.files
        bad = V._build_chain(run, plan.crate)
        if bad is not None:
            return Plain(bad.exit_code, {}, [], f"a path dependency did not build ({bad.verdict})")
        outdir = run.dir / "deps"
        argv = [V.verus_bin(), plan.crate.root, "--crate-type=lib", "--crate-name",
                plan.crate.name, *V._base_args(V.pins()), *V._link_args(plan.crate, outdir),
                "--output-json", "--error-format=json", "--time"]
        job = V._job(run, "plain", argv)
        jd = V.parse_json_doc(job.out) or {}
        vr = jd.get("verification-results") or {}
        shown = ["verus", Path(plan.crate.root).resolve().relative_to(ROOT).as_posix(),
                 *[str(a).replace(str(outdir), "<deps>") for a in job.argv[2:]]]
        return Plain(job.exit, vr if isinstance(vr, dict) else {}, shown)
    finally:
        V._discard(run)


def run_plain(fx):
    try:
        return plain_dafny(fx) if fx.lang == "dafny" else plain_verus(fx)
    except Exception as e:      # a wrapper refusal or a dvl error: a failure, never a verdict
        return Plain(None, None, [], f"the plain run did not run ({type(e).__name__}: {e})")


def json_completeness(fx, k, plain, rep=0):
    vr = plain.vr or {}
    bad = []
    if vr.get("success") is not True:
        bad.append("success-not-true")
    if vr.get("is-verifying-entire-crate") is not True:
        bad.append("not-entire-crate")
    if type(vr.get("verified")) is not int or vr["verified"] < 1:
        bad.append("verified-0")
    canon = json.dumps(vr, sort_keys=True) + "\n"
    lp = log_path(fx, k, "json-completeness", rep)
    lp.write_text(f"$ {' '.join(plain.argv)}\n# exit {plain.exit}; sha256 {sha256(canon)} of the "
                  f"verification-results object below; problems: {bad or 'none'}\n{canon}",
                  encoding="utf-8")
    if plain.exit in KILLED:
        outcome = "killed(memory)"
    elif plain.exit is None:
        outcome = "error"
    else:
        outcome = "flagged" if bad else "clean"
    return Obs("json-completeness", outcome, sha256(canon), plain.exit, plain.argv, lp.as_posix())


def snapshot(fx):
    return {p.relative_to(fx.dir).as_posix() for p in fx.dir.rglob("*")}


# =====================================================================================
# One fixture: --ci and --update
# =====================================================================================

@dataclass
class Result:
    fx: Fixture
    ok: bool = True
    lines: list = field(default_factory=list)
    obs: list = field(default_factory=list)     # per run: [Obs per expect]
    plains: list = field(default_factory=list)
    updated: list = field(default_factory=list)  # (k, new sha)
    fill_plain: int | None = None
    n_tools: int = 0
    n_plain: int = 0
    seconds: float = 0.0


def loc(fx, line):
    return f"{fx.manifest}:{line}" if line else fx.manifest


def compare(fx, res, plain, obs, update=False):
    """Fill res.lines with every difference between the manifest and one run."""
    d = fx.data
    pl = fx.key_line("plain_exit")
    if plain.exit is None or plain.exit in KILLED:
        res.lines.append(f"{loc(fx, pl)}: plain run: "
                         f"{plain.note or 'killed(memory), never a verdict'}")
    elif "plain_exit" not in d:
        if not update:
            res.lines.append(f"{loc(fx, pl)}: plain_exit is missing")
    elif plain.exit != d["plain_exit"]:
        res.lines.append(f"{loc(fx, pl)}: plain_exit: recorded {d['plain_exit']}, observed "
                         f"{plain.exit}")
    for k, (e, o) in enumerate(zip(fx.expects(), obs)):
        at = loc(fx, fx.expect_line(k))
        t = e["tool"]
        if o.outcome in ("error", "killed(memory)"):
            res.lines.append(f"{at}: {t}: {o.outcome} (exit {o.exit}), never an outcome; "
                             f"observed output: {o.log}")
            continue
        if o.outcome != e["outcome"]:
            res.lines.append(f"{at}: {t}: outcome: recorded {e['outcome']}, observed "
                             f"{o.outcome} (exit {o.exit}); observed output: {o.log}")
        if "exit" in e and e["exit"] != o.exit:
            res.lines.append(f"{at}: {t}: exit: recorded {e['exit']}, observed {o.exit}")
        if "argv" in e and e["argv"] != o.argv:
            res.lines.append(f"{at}: {t}: argv differs from the runner's command "
                             f"({' '.join(o.argv)})")
        if not update and e.get("output_sha256") != o.sha:
            was = str(e.get("output_sha256"))[:12]
            res.lines.append(f"{at}: {t}: output_sha256: recorded {was}…, observed "
                             f"{o.sha[:12]}…; observed output: {o.log}")


def run_fixture(fx, update=False):
    res = Result(fx)
    t0 = time.monotonic()
    before = snapshot(fx)
    reps = 2 if update else 1
    for rep in range(reps):
        plain = run_plain(fx)
        res.n_plain += 1
        obs = []
        for k, e in enumerate(fx.expects()):
            if e["tool"] == "json-completeness":
                obs.append(json_completeness(fx, k, plain, rep))
            else:
                obs.append(run_tool(fx, k, e["tool"], rep))
                res.n_tools += 1
        res.plains.append(plain)
        res.obs.append(obs)
    compare(fx, res, res.plains[0], res.obs[0], update)
    if update:
        a, b = res.obs
        for k, (x, y) in enumerate(zip(a, b)):
            if x.sha != y.sha or x.exit != y.exit:
                res.lines.append(f"{loc(fx, fx.expect_line(k))}: {x.tool}: two runs disagree "
                                 f"(exit {x.exit} vs {y.exit}; sha {x.sha[:12]}… vs "
                                 f"{y.sha[:12]}…): not pinned")
        if res.plains[0].exit != res.plains[1].exit:
            res.lines.append(f"{loc(fx, fx.key_line('plain_exit'))}: plain run: two runs "
                             "disagree: not pinned")
        if not res.lines:
            res.updated = [(k, x.sha) for k, (e, x) in enumerate(zip(fx.expects(), a))
                           if e.get("output_sha256") != x.sha]
            if "plain_exit" not in fx.data:
                res.fill_plain = res.plains[0].exit
    after = snapshot(fx)
    if new := sorted(after - before):
        res.lines.append(f"{fx.rel}/: the run left {len(new)} new path(s) in the fixture "
                         f"(first: {new[0]})")
    res.ok = not res.lines
    res.seconds = time.monotonic() - t0
    return res


def rewrite(fx, res):
    """Re-pin output_sha256 lines (and fill plain_exit) in place, keeping
    every comment and layout; the result must parse to the old data with
    only those values changed."""
    lines = fx.text.splitlines(keepends=True)
    heads = [i for i, s in enumerate(lines) if s.strip() == "[[expect]]"]
    new = dict(res.updated)
    for k in sorted(new, reverse=True):
        lo = heads[k]
        hi = next((i for i in range(lo + 1, len(lines)) if lines[i].lstrip().startswith("[")),
                  len(lines))
        idx = next((i for i in range(lo + 1, hi)
                    if re.match(r"^output_sha256\s*=", lines[i])), None)
        line = f'output_sha256 = "{new[k]}"\n'
        if idx is not None:
            lines[idx] = line
        else:                      # the format's order: tool, outcome, kinds, output_sha256
            at = next((i for i in range(lo + 1, hi) if re.match(r"^summary\s*=", lines[i])),
                      None)
            if at is None:
                at = 1 + next((i for i in range(lo + 1, hi)
                               if re.match(r"^outcome\s*=", lines[i])), lo)
            lines.insert(at, line)
    if res.fill_plain is not None:
        first = heads[0] if heads else len(lines)
        while first > 0 and not lines[first - 1].strip():
            first -= 1
        lines.insert(first, f"plain_exit = {res.fill_plain}\n")
    text = "".join(lines)
    want = json.loads(json.dumps(fx.data))
    for k, s in new.items():
        want["expect"][k]["output_sha256"] = s
    if res.fill_plain is not None:
        want["plain_exit"] = res.fill_plain
    if tomllib.loads(text) != want:
        raise RuntimeError(f"{fx.manifest}: the rewrite would change more than the pinned values")
    (fx.dir / "manifest.toml").write_text(text, encoding="utf-8")
    return len(new) + (res.fill_plain is not None)


# =====================================================================================
# CLI
# =====================================================================================

def select(fixtures, sels):
    if not sels:
        return fixtures, []
    out, unknown = [], []
    for s in sels:
        s2 = s.rstrip("/")
        hits = [f for f in fixtures
                if s2 in (f.id, f"{f.lang}/{f.id}", f.rel) or
                (Path(s2).is_absolute() and Path(s2).resolve() == f.dir.resolve()) or
                (not Path(s2).is_absolute() and (Path.cwd() / s2).resolve() == f.dir.resolve())]
        if not hits:
            unknown.append(s)
        out += [f for f in hits if f not in out]
    return sorted(out, key=sort_key), unknown


def preflight(langs, jobs):
    """(ok, message): the toolchains of the langs are on PATH. No memory check:
    memory is the host's and the user's (DELTAS Δ503, D78)."""
    from dvl import common
    for lang in langs:
        try:
            common.toolchain(lang)
        except common.DvlError as e:
            raise Refused(f"no usable {lang} ({e}); install the pinned {lang} and put it on "
                          "PATH (README, Setup)") from None
    note = common.trust_note()
    return True, "toolchains on PATH" + (f"; {note}" if note else "")


def author_gate():
    loader = importlib.machinery.SourceFileLoader("vcheck", str(SCRIPTS / "vcheck"))
    spec = importlib.util.spec_from_loader("vcheck", loader)
    core = importlib.util.module_from_spec(spec)
    sys.modules["vcheck"] = core
    loader.exec_module(core)
    why = core.author_gate(ROOT)
    if why:
        raise Refused(f"--update is author-only and refuses to run here ({why}); it writes the "
                      "corpus's expected outcomes, so it runs only in the course author's "
                      "worktree or with CI set to true (spec §7.4, Δ106)")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="test_corpus.py", description="The cheat-corpus runner.",
                                 allow_abbrev=False)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--list", action="store_true", help="list every fixture; run nothing")
    mode.add_argument("--ci", action="store_true", help="run and compare (the default)")
    mode.add_argument("--update", action="store_true", help="author-only: re-pin the hashes")
    ap.add_argument("--only", action="append", default=[], metavar="SEL",
                    help="a fixture id, LANG/ID or fixture directory (repeatable)")
    ap.add_argument("--jobs", type=int, default=1, metavar="N",
                    help="fixtures in flight at once (default 1, at most 4)")
    ap.add_argument("--keep", action="store_true", help="keep the scratch of a passing run")
    ap.add_argument("sel", nargs="*", metavar="SEL", help="as --only")
    try:
        a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as e:
        return EXIT_USAGE if e.code else EXIT_OK
    if not 1 <= a.jobs <= 4:
        print("test_corpus: --jobs must be 1 to 4", file=sys.stderr)
        return EXIT_USAGE
    try:
        return run(a)
    except Refused as e:
        print(f"test_corpus: refused: {e}", file=sys.stderr)
        return EXIT_REFUSED


def run(a):
    if a.update:
        author_gate()
    fixtures, corpus_probs = load_corpus()
    sels = a.only + a.sel
    if a.list:
        if a.jobs != 1 or a.keep:
            print("test_corpus: --list runs nothing (--jobs and --keep do not apply)",
                  file=sys.stderr)
            return EXIT_USAGE
        chosen, unknown = select(fixtures, sels)
        for s in unknown:
            print(f"test_corpus: no fixture matches {s!r}", file=sys.stderr)
        if unknown:
            return EXIT_USAGE
        bad = 0
        for fx in chosen:
            if fx.problems or not all(isinstance(fx.data.get(k), str)
                                      for k in ("id", "half", "kind", "xclass")):
                bad += 1
                for line, msg in fx.problems or [(0, "id, half, kind or xclass missing")]:
                    print(f"{loc(fx, line)}: {msg}", file=sys.stderr)
                continue
            d = fx.data
            print(f"{fx.id:<6} {fx.lang:<6} {d['half']}  {d['kind']:<17} "
                  f"{d['xclass'] or '-':<4} {fx.rel}")
        for p in corpus_probs:
            print(f"test_corpus: {p}", file=sys.stderr)
        if not chosen:
            print("test_corpus: the corpus lists no fixture (an empty set fails)",
                  file=sys.stderr)
            return EXIT_FAIL
        return EXIT_FAIL if bad or corpus_probs else EXIT_OK

    chosen, unknown = select(fixtures, sels)
    for s in unknown:
        print(f"test_corpus: no fixture matches {s!r}", file=sys.stderr)
    if unknown:
        return EXIT_USAGE
    if not chosen:
        print("test_corpus: the corpus lists no fixture (an empty set fails)", file=sys.stderr)
        return EXIT_FAIL
    whole = not sels
    word = "update" if a.update else "ci"
    t0 = time.monotonic()

    # Static checks of every fixture (selected or not: a broken manifest
    # anywhere is a corpus failure), before any solver job.
    n_refs = sum(static_checks(fx, a.update) for fx in fixtures)
    if whole:
        probs, cover = corpus_checks(fixtures)
        corpus_probs += probs
    else:
        cover = []
    runnable = [fx for fx in chosen if fx.runs and not fx.problems]

    base = Path(os.environ.get("DVL_SCRATCH") or f"/tmp/dvl0-corpus-{os.getuid()}").absolute()
    if base.resolve().is_relative_to(ROOT.resolve()):
        raise Refused(f"DVL_SCRATCH {base} lies inside the course tree; scratch never does")
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    CTX.scratch = Path(tempfile.mkdtemp(prefix=f"corpus-{time.strftime('%Y%m%d-%H%M%S')}-",
                                        dir=base))
    CTX.logs = CTX.scratch / "observed"
    os.environ["DVL_SCRATCH"] = str(CTX.scratch)      # the in-process plain runs (dvl)
    os.environ["DVL_DAFNY_JOBS"] = "1"
    os.environ["DVL_VERUS_JOBS"] = "1"

    started = False
    if runnable:
        langs = sorted({fx.lang for fx in runnable}, key=LANGS.index)
        ok, msg = preflight(langs, a.jobs)
        print(f"test_corpus: {msg}")
        if not ok:
            shutil.rmtree(CTX.scratch, ignore_errors=True)
            return EXIT_FAIL
        started = True

    def work(fx):
        return run_fixture(fx, update=a.update)

    failed, passed, written = [], [], 0
    n_tools = n_plain = 0

    def report(fx, res):
        nonlocal written, n_tools, n_plain
        d = fx.data
        head = f"{fx.id:<6} {fx.lang:<6} {d.get('half', '?')}  {str(d.get('kind')):<17}"
        probs = [f"{loc(fx, line)}: {msg}" for line, msg in fx.problems]
        if res is not None:
            probs += res.lines
            n_tools += res.n_tools
            n_plain += res.n_plain
        if not probs and res is not None and a.update and (res.updated or
                                                           res.fill_plain is not None):
            try:
                written += rewrite(fx, res)
            except (OSError, RuntimeError) as e:
                probs.append(f"{fx.manifest}: not re-pinned ({e})")
        if probs:
            failed.append(fx)
            print(f"FAIL  {head}")
            for p in probs:
                print(f"      {p}")
            return
        passed.append(fx)
        if res is None:
            refs = sum(len(e.get("covered_by") or []) for e in fx.expects())
            what = (f"{refs} covering test(s) found" if fx.kind == "covered-elsewhere"
                    else "static checks")
            print(f"PASS  {head} {what}")
            return
        tools = ", ".join(f"{o.tool} {o.outcome}" for o in res.obs[0])
        if a.update:
            n = len(res.updated) + (res.fill_plain is not None)
            print(f"{'UPDATED' if n else 'SAME   '} {head} {n} value(s) re-pinned; plain "
                  f"{res.plains[0].exit}; {tools} ({res.seconds:.0f}s)")
        else:
            print(f"PASS  {head} plain {res.plains[0].exit}; {tools} ({res.seconds:.0f}s)")

    if a.jobs == 1:
        for fx in chosen:
            res = work(fx) if fx in runnable else None
            report(fx, res)
            sys.stdout.flush()
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:
            futs = {fx.id + fx.lang: pool.submit(work, fx) for fx in runnable}
            for fx in chosen:
                res = futs[fx.id + fx.lang].result() if fx in runnable else None
                report(fx, res)
                sys.stdout.flush()

    # Selected fixtures are reported above; a broken manifest outside the
    # selection still fails the run.
    others = [fx for fx in fixtures if fx not in chosen and fx.problems]
    for fx in others:
        failed.append(fx)
        print(f"FAIL  {fx.id:<6} {fx.lang:<6} (not selected; its manifest is broken)")
        for line, msg in fx.problems:
            print(f"      {loc(fx, line)}: {msg}")
    for p in corpus_probs:
        print(f"FAIL  corpus: {p}")

    by_lang = {lang: sum(1 for f in chosen if f.lang == lang) for lang in LANGS}
    kinds = {k: [f for f in chosen if f.kind == k] for k in KINDS}
    held = [f.id for f in kinds["construct"]
            if not any(e.get("outcome") == "flagged" for e in f.expects())]
    good = {k: sum(1 for f in v if f in passed) for k, v in kinds.items()}
    print(f"test_corpus: {len(chosen)} fixture(s) (" +
          ", ".join(f"{lang} {n}" for lang, n in by_lang.items() if n) +
          f"): {len(passed)} passed, {len(failed)} failed; {len(runnable)} run ({n_plain} plain "
          f"run(s), {n_tools} instrument run(s)), {len(kinds['covered-elsewhere'])} covered "
          f"elsewhere ({n_refs} test reference(s) resolved in the whole corpus)")
    print(f"test_corpus: {good['construct']}/{len(kinds['construct'])} construct(s) flagged by "
          f"at least one instrument as recorded" +
          (f" ({len(held)} held only by the gate's grader-only UNKNOWN: {', '.join(held)})"
           if held else "") +
          f"; {good['control']}/{len(kinds['control'])} control(s) clean on every instrument")
    for c in cover:
        print(f"test_corpus: halves: {c}")
    if not whole:
        print("test_corpus: a selection: the corpus-level checks (halves, catalog rows, "
              "controls) run only on the whole corpus")
    if a.update:
        print(f"test_corpus: --update re-pinned {written} value(s)")
    ok = not failed and not corpus_probs
    if started:
        if ok and not a.keep:
            shutil.rmtree(CTX.scratch, ignore_errors=True)
        else:
            print(f"test_corpus: scratch kept: {CTX.scratch}")
    elif CTX.scratch:
        shutil.rmtree(CTX.scratch, ignore_errors=True)
    print(f"test_corpus: {word}: {'PASS' if ok else 'FAIL'} ({time.monotonic() - t0:.0f}s)")
    return EXIT_OK if ok else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
