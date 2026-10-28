#!/usr/bin/env python3
"""test_course_map.py — regression cases for scripts/check_course_map.py,
scripts/course_items.py and scripts/gen_units.py.

Each case edits this checkout's MODULES.toml, writes it into a throwaway root,
runs the checker (or the generator) there and checks the exit code and one
line of its output. In the root, docs/, paper/, .claude/, harness/, tools/,
specimens/, slots/ and instructor/ are symlinked from the checkout (when they
exist); dafny/ and verus/ are copied, because the generator writes into them.
A case may overlay files: `files={relpath: content}` makes every directory on
relpath's way a real directory of symlinks and writes the synthetic file there
(content None deletes the entry). The reference-path cases use empty decoys,
never real reference material.

Cases that need a module past `planned` arm a synthetic Q04: ARMED replaces
Q04's table with tests/course_map/armed/Q04.toml (status authoring), declares
the given L1/L2 layer files in Q01/Q02's imports, copies
tests/course_map/armed/tree/ into the root, and runs scripts/gen_units.py
there first. So the suite never depends on the in-flux status of real modules.

A few cases call the parser and the generator in-process (`unit` cases).

Usage: python3 scripts/test_course_map.py [-v]    (-v also lists passing cases)
Exit: 0 every case passed, 1 otherwise.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path, PurePosixPath

sys.dont_write_bytecode = True  # importing the scripts must leave no scripts/__pycache__
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import course_items as ci  # noqa: E402
import gen_units as gu  # noqa: E402

CHECKER = ROOT / "scripts/check_course_map.py"
GEN = ROOT / "scripts/gen_units.py"
FIXTURE = ROOT / "tests/course_map/armed"
BASE = (ROOT / "MODULES.toml").read_text(encoding="utf-8")
LINKED = ("docs", "paper", ".claude", "harness", "tools", "specimens", "slots", "instructor",
          "sandbox", "Hidden")  # sandbox/truth.toml and its archives (ciphertext, hashed
#                                 only): the hidden-check spec kind reads its pins (D21)
COPIED = ("dafny", "verus")
CONCEPTS = ".claude/skills/instructor/concepts.md"
BANKS = ".claude/skills/instructor/banks"
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

# The planned stand-in: a module still `planned` in the committed registry,
# with a paper pair and both verifier trees, used by the cases that need one
# (paper pair, units, pending homes). It was Q10/Q11 until DV5a armed Q10-Q12,
# then Q18 until DV5c armed it; R16 (the R track's capstone, planned until DVR3)
# is the stand-in now, and PLANNED_ROW names a coverage row with an R16 home.
# The admissible case below arms Q13 in its own text, for the same reason.
PLANNED = "R16"
PLANNED_D = "dafny/R/R16_Capstone"
PLANNED_V = "verus/r/r16_capstone"
PLANNED_HOME = "R16"
PLANNED_ROW = "S10.build-tool-poisoning"
if f'id = "{PLANNED}"\n' not in BASE or \
        BASE.split(f'id = "{PLANNED}"\n', 1)[1].split("[[module]]", 1)[0].count('status = "planned"') != 1:
    raise SystemExit(f"test_course_map: the planned stand-in {PLANNED} is no longer planned: "
                     "move the stand-in cases to a module still planned")


def span(kind, key, value, text):
    """(start, end) offsets of the [[kind]] table whose first line is key = "value"."""
    s = text.index(f'[[{kind}]]\n{key} = "{value}"')
    e = text.find("\n[[", s + 1)
    return s, (len(text) if e < 0 else e + 1)


def table(mid, text=BASE):
    return span("module", "id", mid, text)


def replace_in(s, e, what, old, new, text):
    seg = text[s:e]
    if old not in seg:
        raise SystemExit(f"test_course_map: case setup: {old!r} not in {what}")
    return text[:s] + seg.replace(old, new, 1) + text[e:]


def edit(mid, old, new, text=BASE):
    """text with the first `old` inside mid's table replaced by `new`."""
    return replace_in(*table(mid, text), f"{mid}'s table", old, new, text)


SUBTABLE = re.compile(r"(?m)^\[module\.([a-z_]+)\]\n")


def _inline(value):
    """A sub-table's value as an inline TOML table: strings, lists of strings,
    and the nested inline tables of [module.admissible] (booleans, integers and
    strings; Q08's gated items, DV3b)."""
    import json

    def one(x):
        if isinstance(x, bool):
            return "true" if x else "false"
        if isinstance(x, (int, str)):
            return json.dumps(x)
        if isinstance(x, dict):
            return _inline(x)
        return "[" + ", ".join(one(y) for y in x) + "]"
    return "{ " + ", ".join(f"{json.dumps(k)} = {one(v)}" for k, v in value.items()) + " }" \
        if value else "{}"


def setf(mid, key, value, text=BASE):
    """text with mid's `key = …` line set to `key = value` (value is TOML text).
    A non-empty imports, admissible or concept_items table is written as a
    [module.<key>] sub-table (MODULES.toml header). To set one, every
    sub-table of the record is rewritten as an inline line, in its order, so
    the record's fields keep their order (a record armed with both an imports
    and a concept_items sub-table, DV3a); comments inside them are dropped."""
    s, e = table(mid, text)
    seg = text[s:e]
    new, n = re.subn(rf"(?m)^{re.escape(key)} = .*$", lambda _: f"{key} = {value}", seg, count=1)
    if n != 1:
        if f"\n[module.{key}]\n" not in seg:
            raise SystemExit(f"test_course_map: case setup: no '{key}' line in {mid}'s table")
        import tomllib
        rec = next(m for m in tomllib.loads(text)["module"] if m.get("id") == mid)
        first = SUBTABLE.search(seg)
        lines = [f"{k} = {value}" if k == key else f"{k} = {_inline(rec[k])}"
                 for k in (m.group(1) for m in SUBTABLE.finditer(seg))]
        new = seg[:first.start()].rstrip("\n") + "\n" + "".join(x + "\n" for x in lines) + "\n"
    return text[:s] + new + text[e:]


def cov_edit(pid, old, new, text=BASE):
    return replace_in(*span("coverage", "payload_id", pid, text), f"{pid}'s coverage row", old,
                      new, text)


def drop(kind, key, value, text=BASE):
    s, e = span(kind, key, value, text)
    return text[:s] + text[e:]


def sub(text, old, new):
    if old not in text:
        raise SystemExit(f"test_course_map: case setup: {old!r} not in fixture")
    return text.replace(old, new, 1)


# --- the armed module ---------------------------------------------------------------
ARMED_TABLE = (FIXTURE / "Q04.toml").read_text(encoding="utf-8")
_s, _e = table("Q04")
ARMED = BASE[:_s] + ARMED_TABLE + BASE[_e:]


def declare_given(mid, layer, text):
    """text with mid declaring its layer's given files, unless it already does
    (DV2 declares L1 in Q01 and L2 in Q02, beside their own files)."""
    files = (f"dafny/given/Q/QG_{layer}_BigNat.dfy", f"verus/given/qg_bignat_{layer.lower()}/src/lib.rs")
    s, e = table(mid, text)
    if all(f'"{f}"' in text[s:e] for f in files):
        return text
    return setf(mid, "imports", f'{{ "{files[0]}" = "core", "{files[1]}" = "prelude" }}', text)


ARMED = declare_given("Q01", "L1", ARMED)
ARMED = declare_given("Q02", "L2", ARMED)


def _real_later(text=BASE):
    """The real modules past planned that come after Q04 (DV3a arms Q05 and
    Q06): the armed cases plan them and drop their files from the root, so the
    synthetic Q04 is the only moderate-tier module there (its fixture layers
    are not the real L3, and the real Q05-Q06 files would read them)."""
    import tomllib
    return [m["id"] for m in tomllib.loads(text).get("module", []) if isinstance(m, dict)
            and m.get("status") != "planned" and m.get("track") == "Q" and int(m["id"][1:]) > 4]


def plan_real(mid, text):
    """text with the real module mid set back to planned, its imports and
    concept_items emptied."""
    text = setf(mid, "status", '"planned"', text)
    text = setf(mid, "imports", "{}", text)
    return setf(mid, "concept_items", "{}", text)


def module_trees(mid, text=BASE):
    """The on-disk paths of a real module's files: its Dafny and Verus module
    directories (units included), its listed files and specimen directory, its
    slots file and its learner Python files, and the given layer it declares
    (its Dafny file and its Verus crate: DV3b's Q07 declares L4, which an
    armed case's root must not hold once Q07 is planned there)."""
    import tomllib
    rec = next(m for m in tomllib.loads(text)["module"] if m.get("id") == mid)
    out = set()
    for rel in (rec.get("imports") or {}):
        parts = rel.split("/")
        if parts[:2] == ["dafny", "given"]:
            out.add(rel)
        elif parts[:2] == ["verus", "given"]:
            out.add("/".join(parts[:3]))
    for rel in rec["exercises"] + rec["exits"] + rec["agentic"] + rec["harness"] + rec["units"]:
        parts = rel.rstrip("/").split("/")
        if parts[:2] in (["dafny", "Q"], ["dafny", "R"], ["verus", "q"], ["verus", "r"]):
            out.add("/".join(parts[:3]))
        else:
            out.add(rel.rstrip("/"))
    out.add(f"slots/{mid}.slots")
    return sorted(out)


REAL_LATER = _real_later()
for _mid in REAL_LATER:
    ARMED = plan_real(_mid, ARMED)
TREE = {p.relative_to(FIXTURE / "tree").as_posix(): p.read_text(encoding="utf-8")
        for p in sorted((FIXTURE / "tree").rglob("*")) if p.is_file()}


def _baseline(text):
    """What a registry adds to every count the cases pin: the real modules
    past planned (Q04 is the fixture's), their units, and the declared course
    files on disk. Zero while every real module is planned. The armed cases'
    counts come from ARMED (the real modules after Q04 planned); BASE_ON_DISK
    from the committed registry."""
    import tomllib
    mods = [m for m in tomllib.loads(text).get("module", []) if isinstance(m, dict)]
    real = [m for m in mods if m.get("id") != "Q04" and m.get("status") != "planned"]
    declared = {p for m in mods for p in (m.get("imports") or {}) if (ROOT / p).is_file()}
    own = {p for m in real for p in (m.get("imports") or {}) if (ROOT / p).is_file()}
    given = re.compile(r"dafny/given/|verus/given/")
    return ([m["id"] for m in real], sum(m.get("status") == "authoring" for m in real),
            sum(len(m.get("units") or []) for m in real), len(declared),
            len({p for p in own if not given.match(p)}))


REAL_ARMED, REAL_AUTHORING, REAL_UNITS, _, REAL_MODULE_FILES = _baseline(ARMED)
BASE_ON_DISK = _baseline(BASE)[3]
# Package __init__.py files on disk: the import-tier group counts them as
# course files without an owner (DV4 ships harness/q/fvh_q/ and harness/r/fvh_r/).
PKG_ON_DISK = sum(1 for d in ("harness/q/fvh_q", "harness/r/fvh_r") if (ROOT / d).is_dir()
                  for _ in (ROOT / d).rglob("__init__.py"))
# The fixture supplies Q's three layer pairs; R's independently declared
# foundations remain in its copied tree even before their owning module arms.
REAL_R_GIVEN_FILES = len({p for m in tomllib.loads(ARMED)["module"]
                         for p in (m.get("imports") or {})
                         if p.startswith(("dafny/given/R/", "verus/given/rg_"))
                         and (ROOT / p).is_file()})
ARMED_IMPORT_FILES = 13 + REAL_MODULE_FILES + REAL_R_GIVEN_FILES + PKG_ON_DISK
ARMED_IDS = ", ".join(sorted(REAL_ARMED + ["Q04"]))


def _real_banks():
    """The committed banks the vocabulary check counts beside a case's own Q04
    bank: a real module's bank file on disk with a tag vocabulary (DV2b ships
    Q01-Q03's). Zero while no bank is written."""
    import tomllib
    paths = {m.get("bank") for m in tomllib.loads(BASE).get("module", [])
             if isinstance(m, dict) and m.get("id") != "Q04" and m.get("bank")}
    return sum(1 for p in paths if (ROOT / p).is_file()
               and "## Controlled tag vocabulary" in (ROOT / p).read_text(encoding="utf-8"))


REAL_BANKS = _real_banks()
PC = "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"
LIB = "dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy"
EXIT = "dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy"
RS = "verus/q/q04_proof_craft/src/lib.rs"
EXIT_RS = "verus/q/q04_proof_craft/src/exit.rs"
SPEC = "specimens/Q04/P3d.dfy.specimen"
SLOTS = "slots/Q04.slots"


def fx(rel, old, new):
    """{rel: the fixture file with one edit}."""
    return {rel: sub(TREE[rel], old, new)}


CASES = []


def _statement_item_unit():
    """check_course_map.statement_item_problem on an invented module (in-process)."""
    import check_course_map as ccm
    root = Path(tempfile.mkdtemp(prefix="course-map-unit-"))
    try:
        (root / "a.dfy").write_text("// item: Q98.H1d S1\n// prose: Foo\n// contractor: Q98.A1v\n"
                                    "lemma X() {}\n"
                                    "// item: Q98.H2d S1\nlemma Y() {}\n"
                                    "// item: Q98.H3d S1\n// prose: Bar\nlemma Z() {}\n"
                                    "// item: Q98.H4d S1\n// prose: Baz\n// contractor: Q98.H2d\n"
                                    "lemma W() {}\n", encoding="utf-8")
        m = {"agentic": ["b.rs"]}
        h1 = {"id": "Q98.H1d", "kind": "H", "file": "a.dfy", "line_start": 1, "line_end": 4}
        h2 = {"id": "Q98.H2d", "kind": "H", "file": "a.dfy", "line_start": 5, "line_end": 6}
        h3 = {"kind": "H", "file": "b.rs", "line_start": 1, "line_end": 1}
        p1 = {"kind": "P", "file": "b.rs", "line_start": 1, "line_end": 1}
        h5 = {"id": "Q98.H3d", "kind": "H", "file": "a.dfy", "line_start": 7, "line_end": 9}
        h6 = {"id": "Q98.H4d", "kind": "H", "file": "a.dfy", "line_start": 10, "line_end": 13}
        a1 = {"id": "Q98.A1v", "kind": "A", "file": "b.rs", "line_start": 1, "line_end": 1}
        items = [h1, h2, h5, h6, a1]
        if ccm.statement_item_problem(root, m, h1, items) is not None:
            return "a prose block naming its contractor was refused"
        if "names no contractor" not in (ccm.statement_item_problem(root, m, h5, items) or ""):
            return "a prose block with no contractor (Q15's Lab 2 specs) was accepted"
        if "no A item" not in (ccm.statement_item_problem(root, m, h6, items) or ""):
            return "a prose block naming a non-A contractor was accepted"
        if "no A item" not in (ccm.statement_item_problem(root, m, h1, [h1]) or ""):
            return "a contractor that is not the module's item was accepted"
        if ccm.statement_item_problem(root, m, h3) is not None:
            return "an agentic-file item was refused"
        if "no prose item" not in (ccm.statement_item_problem(root, m, h2) or ""):
            return "a plain block was accepted"
        if "is a P item" not in (ccm.statement_item_problem(root, m, p1) or ""):
            return "a P item was accepted"
        if ccm.exception_kind({"exception": "statement-item: x"}) != "statement-item" or \
                ccm.exception_kind({"exception": "no colon"}) is not None or \
                ccm.exception_kind({}) is not None:
            return "exception_kind misreads an entry"
        return None
    finally:
        shutil.rmtree(root)


def _out_of_band_unit():
    """check_course_map.out_of_band_problems on the committed table and edits."""
    import check_course_map as ccm
    adm = {k: {"admitted": True} for k in ccm.OUT_OF_BAND}
    for mid in sorted({k.split(".")[0] for k in ccm.OUT_OF_BAND}):
        if ccm.out_of_band_problems(mid, adm):
            return f"a committed OUT_OF_BAND entry of {mid} fails: " + \
                str(ccm.out_of_band_problems(mid, adm))
    saved = dict(ccm.OUT_OF_BAND)
    try:
        ccm.OUT_OF_BAND["Q15.H1d"] = (12, "short-format band", "D2")
        if "inside its band 10-30" not in str(ccm.out_of_band_problems("Q15", adm)):
            return "an in-band figure was accepted"
        ccm.OUT_OF_BAND.clear()
        ccm.OUT_OF_BAND["Q15.H6py"] = (0, "short-format band", "D2")
        if "no Dafny or Verus item" not in str(ccm.out_of_band_problems(
                "Q15", {"Q15.H6py": {"admitted": True}})):
            return "a Python item was accepted"
        ccm.OUT_OF_BAND.clear()
        ccm.OUT_OF_BAND["Q05.H1d"] = (0, "short-format band", "D2")
        if "practice module" not in str(ccm.out_of_band_problems(
                "Q05", {"Q05.H1d": {"admitted": True}})):
            return "a concept module's item was accepted"
        # DV6: the intro band starts at 0 (QPLAN §19.0, "at most 10/15"): an intro item
        # with no proof line is inside it, so it needs no OUT_OF_BAND entry
        ccm.OUT_OF_BAND.clear()
        ccm.OUT_OF_BAND["Q10.H6v"] = (0, "short-format band", "D2")
        if "inside its band 0-15" not in str(ccm.out_of_band_problems(
                "Q10", {"Q10.H6v": {"admitted": True}})):
            return "an intro item with 0 proof lines was read as outside its band"
    finally:
        ccm.OUT_OF_BAND.clear()
        ccm.OUT_OF_BAND.update(saved)
    return None


def _hidden_check_unit():
    """check_course_map.hidden_check_problem on an invented module (in-process)."""
    import check_course_map as ccm
    root = Path(tempfile.mkdtemp(prefix="course-map-unit-"))
    held = dict(ccm.HIDDEN_CHECKS_HELD)
    try:
        (root / "a.dfy").write_text("// item: Q98.H1d S1\n// prose: Foo\nmethod X() {}\n"
                                    "// item: Q98.H2d S1\nlemma Y() {}\n"
                                    "// item: Q98.H3d S1\n// prose: Bar\n// contractor: Q98.A1v\n"
                                    "lemma Z() {}\n"
                                    "// item: Q98.H4d S1\n// prose: Baz\nmethod W() {}\n",
                                    encoding="utf-8")
        (root / "c.dfy").write_text("// item: Q98.H5d S1\n// prose: Qux\nmethod V() {}\n",
                                    encoding="utf-8")
        m = {"id": "Q98", "agentic": ["b.rs"], "exercises": ["a.dfy"]}
        h1 = {"id": "Q98.H1d", "kind": "H", "file": "a.dfy", "line_start": 1, "line_end": 3}
        h2 = {"id": "Q98.H2d", "kind": "H", "file": "a.dfy", "line_start": 4, "line_end": 5}
        h3 = {"id": "Q98.H3d", "kind": "H", "file": "a.dfy", "line_start": 6, "line_end": 9}
        h4 = {"id": "Q98.H4d", "kind": "H", "file": "a.dfy", "line_start": 10, "line_end": 12}
        h5 = {"id": "Q98.H5d", "kind": "H", "file": "c.dfy", "line_start": 1, "line_end": 3}
        ag = {"id": "Q98.H6v", "kind": "H", "file": "b.rs", "line_start": 1, "line_end": 1}
        p1 = {"id": "Q98.P1d", "kind": "P", "file": "a.dfy", "line_start": 1, "line_end": 3}
        ccm.HIDDEN_CHECKS_HELD.update({x: "Δ0" for x in ("Q98.H1d", "Q98.H2d", "Q98.H3d",
                                                         "Q98.H5d", "Q98.H6v", "Q98.P1d")})
        sealed = {"Q98"}
        if ccm.hidden_check_problem(root, m, h1, sealed) is not None:
            return "a recorded prose item of an exercise file was refused"
        if "not recorded as holding" not in (ccm.hidden_check_problem(root, m, h4, sealed) or ""):
            return "a prose item whose hidden check is not recorded was accepted"
        if "pins no sealed hidden truth" not in (ccm.hidden_check_problem(root, m, h1, {})
                                                 or ""):
            return "a prose item whose module has no sealed truth was accepted"
        if "names a contractor" not in (ccm.hidden_check_problem(root, m, h3, sealed) or ""):
            return "a prose item naming a contractor (a statement item) was accepted"
        if "agentic files" not in (ccm.hidden_check_problem(root, m, ag, sealed) or ""):
            return "an agentic-file item was accepted"
        if "exercise files" not in (ccm.hidden_check_problem(root, m, h5, sealed) or ""):
            return "an item outside the module's exercise files was accepted"
        if "no prose item" not in (ccm.hidden_check_problem(root, m, h2, sealed) or ""):
            return "a plain block was accepted"
        if "is a P item" not in (ccm.hidden_check_problem(root, m, p1, sealed) or ""):
            return "a P item was accepted"
        (root / "sandbox").mkdir()
        (root / "Hidden/labs/Q98").mkdir(parents=True)
        (root / "Hidden/labs/Q98/verdicts.tar.age").write_bytes(b"decoy ciphertext\n")
        dig = __import__("hashlib").sha256(b"decoy ciphertext\n").hexdigest()
        man = "ab" * 32
        pins = ('[[lab]]\nid = "Q98"\narchive = "Hidden/labs/Q98/verdicts.tar.age"\n'
                f'sha256 = "{dig}"\nmanifest_sha256 = "{man}"\n'
                '[[lab]]\nid = "Q97"\narchive = "Hidden/labs/Q97/verdicts.tar.age"\n'
                f'sha256 = "{dig}"\n')
        (root / "sandbox/truth.toml").write_text(pins, encoding="utf-8")
        if ccm.sealed_labs(root) != {"Q98": man}:
            return f"sealed_labs misreads the pins: {ccm.sealed_labs(root)!r}"
        if ccm.hidden_check_problem(root, m, h1) is not None:
            return "a recorded prose item was refused with the module's truth pinned on disk"
        ccm.HIDDEN_CHECKS_HELD["Q98.H1d"] = ("Δ0", man)
        if ccm.hidden_check_problem(root, m, h1) is not None:
            return "a prose item held at the pinned manifest was refused"
        ccm.HIDDEN_CHECKS_HELD["Q98.H1d"] = ("Δ0", "cd" * 32)
        if "a re-seal" not in (ccm.hidden_check_problem(root, m, h1) or ""):
            return "a prose item held at another manifest (a re-seal) was accepted"
        (root / "Hidden/labs/Q98/verdicts.tar.age").write_bytes(b"other bytes\n")
        if "pins no sealed hidden truth" not in (ccm.hidden_check_problem(root, m, h1) or ""):
            return "an archive whose bytes differ from its pinned sha256 was accepted"
        (root / "Hidden/labs/Q98/verdicts.tar.age").unlink()
        if ccm.sealed_labs(root) != {}:
            return "a pinned archive missing on disk was counted as sealed"
        (root / "sandbox/truth.toml").write_text("[[lab\n", encoding="utf-8")
        if ccm.sealed_labs(root) != {}:
            return "an unreadable truth.toml gave sealed labs"
        for k, v in held.items():
            if not (isinstance(v, tuple) and len(v) == 2
                    and re.fullmatch(r"[0-9a-f]{64}", v[1])):
                return f"the committed HIDDEN_CHECKS_HELD entry {k} names no manifest digest"
        if ccm.exception_kind({"exception": "hidden-check spec: x"}) != "hidden-check spec":
            return "exception_kind misreads a hidden-check spec entry"
        return None
    finally:
        ccm.HIDDEN_CHECKS_HELD.clear()
        ccm.HIDDEN_CHECKS_HELD.update(held)
        shutil.rmtree(root)


def case(name, text, want, line, files=None, args=(), armed=False, ledger=None, decoys=(),
         script="checker", after=None):
    """One subprocess case. `armed` copies the fixture tree and runs the
    generator first; `after` overlays files once the generator has run."""
    CASES.append((name, text, want, line, files or {}, args, armed, ledger, decoys, script,
                  after or {}))


def unit(name, fn):
    """An in-process case: fn() returns None on success or a failure message."""
    CASES.append((name, fn))


# --- the committed registry ------------------------------------------------------------
case("the registry as committed", BASE, 0, "course map OK")
for group, line in (("registry", "course map OK"), ("units", "units:"),
                    ("import-tiers", "import-tiers:"), ("isolation", "isolation:"),
                    ("coverage", "coverage:"), ("vocab", "vocab:")):
    case(f"--only {group} as committed", BASE, 0, line, args=("--only", group))
case("gen_units --check as committed", BASE, 0, "match the registry", script="gen",
     args=("--check",))

# --- schema and ids -----------------------------------------------------------------------
case("missing module", drop("module", "id", "R07"), 1, "R07: missing from the registry")
case("duplicate id", edit("R08", 'id = "R08"', 'id = "R07"'), 1, "R07: id listed more than once")
case("id out of range", edit("R16", 'id = "R16"', 'id = "R17"'), 1, "id must be one of")
_s, _e = table("R01")
_q01 = table("Q01")
case("R before Q", BASE[:_q01[0]] + BASE[_s:_e] + BASE[_q01[0]:_s] + BASE[_e:], 1,
     "modules must be listed in order")
_r01_status = next(m["status"] for m in tomllib.loads(BASE)["module"] if m["id"] == "R01")
case("field order", edit("R01", f'track = "R"\nstatus = "{_r01_status}"',
                         f'status = "{_r01_status}"\ntrack = "R"'),
     1, "fields out of order")
case("missing field", edit("R01", 'card = ["12.11"]\n', ""), 1, "missing field 'card'")
case("unknown field", edit("R01", 'solo = false\n', 'solo = false\nnotes = "x"\n'), 1,
     "unknown field 'notes'")
case("a field that names reference material",
     edit("R01", 'solo = false\n', 'solo = false\nsolution_file = "x"\n'), 1, "is not allowed")
case("bool where an int belongs", setf("R01", "tutor_max_rung", "true"), 1,
     "'tutor_max_rung' must be an integer")
case("enum out of range", setf("R01", "review_bar", '"mathlib-pr"'), 1,
     "'review_bar' = 'mathlib-pr' is not one of")
case("a list of non-strings", setf("R01", "card", "[1]"), 1, "'card' must be a list of non-empty strings")
case("schema version", BASE.replace("schema = 1", "schema = 2", 1), 1, "'schema = 1' is required")
case("not TOML", BASE + "\n[[module\n", 1, "not valid TOML")
case("unknown top-level key", BASE.replace("schema = 1", "schema = 1\nextra = 2", 1), 1,
     "top level: unknown key 'extra'")
# The one WRITE-uses exception (D85): R05's Dafny `assert-by` stands on R05.H2d alone.
WE_HEAD = '[[write_exception]]\nmodule = "R05"\nlang = "d"\nslug = "assert-by"\nitem = "R05.H2d"\n'
if WE_HEAD not in BASE:
    raise SystemExit("test_course_map: the registry no longer declares D85's write exception: "
                     "update the write-exception cases")
WE_BLOCK = BASE[BASE.index(WE_HEAD):]
case("write exception: without the declaration, the 1-item slug fails", sub(BASE, WE_BLOCK, ""), 1,
     "R05: Dafny WRITE 'assert-by' has 1 tagged item (need ≥ 2 `uses:` in Dafny): R05.H2d")
case("write exception: an undecided slug is refused",
     sub(BASE, WE_HEAD, WE_HEAD.replace('slug = "assert-by"', 'slug = "rlimit"')), 1,
     "is no exception the user decided")
case("write exception: the other language is refused",
     sub(BASE, WE_HEAD, WE_HEAD.replace('lang = "d"', 'lang = "v"')), 1,
     "R05 v 'assert-by' is no exception the user decided")
case("write exception: another item is refused",
     sub(BASE, WE_HEAD, WE_HEAD.replace('item = "R05.H2d"', 'item = "R05.H1d"')), 1,
     "the exception covers R05.H2d, not R05.H1d")
case("write exception: the reason names the decision",
     sub(BASE, 'reason = "D85: ', 'reason = "'), 1, "its reason must name the user's decision D85")
case("write exception: a second 1-item slug is not covered",
     sub(BASE, 'write_d = ["assert-by"]', 'write_d = ["assert-by", "lemma-call"]'), 1,
     "R05: Dafny WRITE 'lemma-call' has 0 tagged items")
# D92 (Δ310): `writes = "module"` marks R08's H1/H4 rows, whose learner writes whole
# declarations (reference_lint.py allows the twin's inside their @hole regions).
WR_ROW = '"R08.H4d" = { admitted = true, minutes = 10, fallback = "", writes = "module" }'
if WR_ROW not in BASE:
    raise SystemExit("test_course_map: R08.H4d's admissible row no longer carries D92's "
                     "writes = \"module\": update the writes cases")
case("writes: another value is refused",
     sub(BASE, WR_ROW, WR_ROW.replace('writes = "module"', 'writes = "lines"')), 1,
     "'R08.H4d': writes = \"module\" is the only value")
case("writes: on a T item is refused",
     sub(BASE, '"R11.T1d" = { admitted = true, minutes = 5, fallback = "" }',
         '"R11.T1d" = { admitted = true, minutes = 5, fallback = "", writes = "module" }'), 1,
     "'R11.T1d': writes = \"module\" is the only value, on an H item")
case("writes: after the exception is refused (writes comes first)",
     sub(BASE, WR_ROW, WR_ROW.replace('writes = "module" }',
                                      'exception = "short-format band: x", writes = "module" }')),
     1, "'R08.H4d' must be")
case("legacy id that is a current id", setf("R05", "legacy_id", '"R06"'), 1, "legacy_id 'R06'")
case("legacy id used twice", setf("R06", "legacy_id", '"F06"', setf("R05", "legacy_id", '"F06"')), 1,
     "legacy_id F06 used more than once")

# --- per-track rules ------------------------------------------------------------------------
case("Q tier follows the id", setf("Q05", "tier", '"intro"'), 1, "tier must be 'moderate'")
case("layer follows the id", setf("Q05", "layer", '"L4"'), 1, "layer must be 'L3' for Q05")
case("R layer follows the id", setf("R09", "layer", '"A2"'), 1, "layer must be 'A3' for R09")
# Layer A1b (the band-1 facts, declared by R06; PLAN.md §2.2, adopted DV5a)
case("R06's layer is A1b", setf("R06", "layer", '"A1"'), 1, "layer must be 'A1b' for R06")
case("R05's layer stays A1", setf("R05", "layer", '"A1b"'), 1, "layer must be 'A1' for R05")
case("A1b's given files are declared by R06",
     setf("R05", "imports", '{ "dafny/given/R/RG_A1b_Facts.dfy" = "core" }'), 1,
     "declared by R06, the first module of its layer")


def _a1b_helpers():
    import check_course_map as ccm
    import gen_units as gu
    got = (gu.expected_layer("R06"), gu.layer_chain("A1b"), gu.layer_chain("A2"),
           gu.layer_rank("A1") < gu.layer_rank("A1b") < gu.layer_rank("A2"),
           gu.crate_layer("rg_re_a1b"), gu.crate_layer("rg_re_a2b"), gu.layer_first_module("A1b"),
           gu.dafny_layer_glob("A1b"), gu.verus_layer_crate("A1b"),
           ccm.given_file_layer("dafny/given/R/RG_A1b_Facts.dfy"),
           ccm.given_file_layer("verus/given/rg_re_a1b/src/lib.rs"),
           ccm.given_file_layer("dafny/given/R/RG_A1_Re.dfy"),
           ccm.classify_layer_ref("R", "A1b", "A1", True),
           ccm.classify_layer_ref("R", "A1", "A1b", True) is not None)
    want = ("A1b", ("A1", "A1b"), ("A1", "A1b", "A2"), True, "A1b", None, "R06", "RG_A1b_*.dfy",
            "rg_re_a1b", ("R", "A1b"), ("R", "A1b"), ("R", "A1"), None, True)
    return None if got == want else f"A1b helpers: got {got!r}, want {want!r}"


unit("layer A1b: chain, rank, crate, glob and given-file helpers", _a1b_helpers)
case("Q build target", setf("Q05", "build_target", '"R"'), 1, "build_target must be 'Q'")
case("challenge build target", setf("Q25", "build_target", '"Q"'), 1,
     "build_target must be 'Challenges'")
case("R build target", setf("R03", "build_target", '"Q"'), 1, "build_target must be 'R'")
case("topic follows the id", setf("Q22", "topic", '"numerics"'), 1, "topic must be 'quant'")
case("a tier partitions S1-S13", setf("Q05", "strands", '["S5", "S6", "S7", "S8"]'), 1,
     "strands must partition S1–S13")
case("families in order", setf("Q11", "strands", '["S1", "S2", "S3", "S4", "S5"]',
                               setf("Q10", "strands", '["S6", "S7", "S8"]')), 1,
     "take the families in order")
case("strands out of order", setf("Q05", "strands", '["S7", "S6", "S8"]'), 1,
     "strands must be listed in order")
case("tier viva off the tier's last module", setf("Q02", "viva_mode", '"tier"'), 1,
     "viva_mode must be 'none'")
case("tier-end module without its viva", setf("Q03", "viva_mode", '"none"'), 1,
     "viva_mode must be 'tier'")
case("the survey has no tier viva", setf("Q01", "viva_mode", '"tier"'), 1,
     "viva_mode must be 'none'")
case("challenge not solo", setf("Q20", "solo", "false"), 1, "challenge modules are solo")
case("challenge graded solutions-first", setf("Q20", "solutions_policy", '"solutions-first"'), 1,
     "never solutions-first")
case("challenge strands", setf("Q20", "strands", '["S1"]'), 1, "draws on every strand")
case("challenge viva", setf("Q21", "viva_mode", '"none"'), 1, "end in a defense viva")
case("solo tutor cap", setf("Q23", "tutor_max_rung", "3"), 1, "cap the tutor at rung 2")
case("core module not solutions-first", setf("Q05", "solutions_policy", '"reference-impl"'), 1,
     "are solutions-first")
case("only challenges are solo", setf("Q05", "solo", "true"), 1, "only challenge modules are solo")
case("R module with strands", setf("R02", "strands", '["S1"]'), 1, "strands are Q-only")
case("R module viva", setf("R02", "viva_mode", '"none"'), 1, "every R module has a module viva")
case("R module with deep_dive", setf("R02", "deep_dive", '["R03"]'), 1, "deep_dive is Q-only")
case("R record names a Q module", setf("R07", "title", '"Libraries, after Q04"'), 1,
     "an R record names a Q module (Q04)")
case("Q record names an R module", setf("Q04", "title", '"Proof craft, see R07"'), 1,
     "names an R module outside deep_dive (R07)")
case("Q deep_dive names an R module", setf("Q04", "deep_dive", '["R07"]'), 0, "course map OK")
case("deep_dive that is no R id", setf("Q04", "deep_dive", '["Q07"]'), 1, "is not an R module id")
case("rung out of range", setf("Q05", "tutor_max_rung", "6"), 1, "tutor_max_rung must be 1–5")
case("paper without a rubric", setf("Q05", "rubric", '""'), 1, "paper = true needs a rubric")
case("a card without paper", setf("Q05", "paper", "false"), 1,
     "card lists paper cards, so paper = true")
case("a lab without paper", setf("Q12", "paper", "false"), 1,
     "engines runs a model (policy or agent), so paper = true")
case("a model engine without paper or card",
     setf("Q31", "engines", '["agent"]',
          setf("Q31", "budget", "{ claude_calls = 0, claude_runs = 0, qwen_calls = 0, qwen_runs = 1, "
               "gpu_hours = 0 }")), 1, "engines runs a model (policy or agent), so paper = true")
case("a challenge with neither card nor engine keeps paper = false", BASE, 0, "course map OK",
     args=("--only", "registry"))

# --- files, langs, units ------------------------------------------------------------------------
case("langs that do not match the files", setf("Q06", "langs", '["d", "v"]'), 1,
     "do not match the module's files")
case("core module without Verus", setf("R03", "langs", '["d"]'), 1, "teach both verifiers")
case("Python before Q06", setf("Q05", "langs", '["d", "v", "py"]'), 1, "Python enters at Q06")
case("Python before R05", setf("R04", "langs", '["d", "v", "py"]'), 1, "Python enters at R05")
case("langs out of order", setf("Q01", "langs", '["v", "d"]'), 1, "listed in the order d, v, py")
case("a path in another module's directory",
     edit("Q04", '"dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"',
          '"dafny/Q/Q05_Frames/core/Q04_ProofCraft.dfy"'), 1, "must sit under dafny/Q/Q04_ProofCraft/")
case("a Verus path outside the module's crate",
     edit("Q04", '"verus/q/q04_proof_craft/src/lib.rs"', '"verus/q/q04_craft/src/lib.rs"'), 1,
     "must sit under verus/q/q04_proof_craft/src/")
case("an exit inside a unit directory",
     edit("Q05", '"dafny/Q/Q05_Frames/exit/Q05_Exit.dfy"', '"dafny/Q/Q05_Frames/std/Q05_Exit.dfy"'), 1,
     "exits: 'dafny/Q/Q05_Frames/std/Q05_Exit.dfy' must sit under")
case("an exit that is the crate root",
     edit("Q05", '"verus/q/q05_frames/src/exit.rs"', '"verus/q/q05_frames/src/lib.rs"'), 1,
     "is the crate root")
case("harness outside the track's package", setf("Q06", "harness", '["harness/r/fvh_r/q06.py"]'),
     1, "must be a .py file under harness/q/fvh_q/")
case("challenge exercise outside its directory",
     setf("Q20", "exercises", '["Challenges/Quant/Q20_HashMap/q20_hash_map/src/lib.rs"]'), 1,
     "must sit under Challenges/Algorithms/Q20_HashMap/")
case("challenge with agentic files", setf("Q20", "agentic", '["tools/Q20/x.py"]'), 1,
     "agentic must be []")
case("malformed chapter", setf("Q05", "chapter", '"docs/Frames.md"'), 1,
     "chapter must be docs/Q05_<Name>.md")
case("units that disagree with exercises", setf("Q05", "units", '["verus/q/q05_frames"]'), 1,
     "units must be")
case("a std unit before Q04",
     setf("Q02", "units", '["dafny/Q/Q02_FirstSyntaxI/std", "verus/q/q02_first_syntax_i"]',
          edit("Q02", "/core/Q02_FirstSyntaxI.dfy", "/std/Q02_FirstSyntaxI.dfy")), 1,
     "no std unit before it")
case("no Verus crate", setf("R03", "units", '["dafny/R/R03_Modules/core"]',
                            edit("R03", '"verus/r/r03_modules/src/lib.rs", ', "")), 1,
     "exactly one Verus crate")
case("empty exercises", setf("Q20", "exercises", "[]"), 1, "exercises must list at least one path")
case("bank path", setf("Q05", "bank", '".claude/skills/instructor/banks/Q5.md"'), 1,
     "bank must be .claude/skills/instructor/banks/Q05.md")
case("defense bank path", setf("Q20", "bank", '".claude/skills/instructor/banks/Q20.md"'), 1,
     "defense_algorithms.md")
case("rubric path", setf("Q05", "rubric", '"paper/rubrics/Q5_rubric.md"'), 1,
     "rubric must be paper/rubrics/Q05_rubric.md")
case("malformed card", setf("Q05", "card", '["3.12"]'), 1, "is not a cheatsheets.md id")
case("missing card", setf("Q05", "card", "[]"), 1, "card must list the module's paper card")
case("shared card", setf("Q05", "card", '["02.2"]'), 1, "card '02.2' is shared by Q04, Q05")
case("a chapter named for another module", setf("Q04", "chapter", '"docs/Q05_ProofCraft.md"'), 1,
     "chapter must be docs/Q04_<Name>.md")
case("a path in another module's specimens", setf("Q06", "exercises",
     '["dafny/Q/Q06_Machine/std/Q06_Machine.dfy", "verus/q/q06_machine/src/lib.rs", "specimens/Q05/x/"]'), 1,
     "must sit under specimens/Q06/")
case("a path listed twice", edit("Q05", '"specimens/Q05/"', '"specimens/Q05/", "specimens/Q05/"'), 1,
     "lists a path twice")
case("dot-dot path", edit("R01", '"specimens/R01/"', '"specimens/R01/../R02/"'), 1,
     "plain repo-relative path")
case("absolute path", setf("Q06", "harness", '["/harness/q/fvh_q/q06_stats.py"]'), 1,
     "plain repo-relative path")
case("reference directory, any case", edit("R01", '"specimens/R01/"', '"specimens/R01/SOLUTIONS/"'),
     1, "points into reference or held-out material")
case("held-out material", setf("Q20", "exercises",
                               '["Challenges/Algorithms/Q20_HashMap/Hidden/q20.rs"]'), 1,
     "points into reference or held-out material")
case("sealed archive", setf("Q20", "exercises", '["Challenges/Algorithms/Q20_HashMap/q20.tar.age"]'),
     1, "points into reference or held-out material")
case("a written-track solution file",
     edit("R02", '"specimens/R02/"', '"specimens/R02/R02_solutions.tex"'), 1,
     "points into reference or held-out material")
case("a reference specimen, by the name up to its first dot",
     edit("R02", '"specimens/R02/"', '"specimens/R02/solutions.dfy.specimen"'), 1,
     "points into reference or held-out material")
case("a registry path named solutions_policy (reserved)",
     setf("Q06", "harness", '["harness/q/fvh_q/solutions_policy.py"]'), 1,
     "is named 'solutions_policy'; solutions_policy and solutions-first are the registry's")
case("a registry directory named solutions-first (reserved)",
     edit("R01", '"specimens/R01/"', '"specimens/R01/solutions-first/"'), 1,
     "is named 'solutions-first'")
case("a reserved name in another spelling",
     edit("R01", '"specimens/R01/"', '"specimens/R01/Solutions_First/"'), 1,
     "is named 'Solutions_First'")
case("a registry path starting with solutions",
     setf("Q06", "harness", '["harness/q/fvh_q/solutions_check.py"]'), 1,
     "'solutions_check.py' starts with 'solutions'")
case("a shipped module needs its files", setf("Q04", "status", '"shipped"', ARMED), 1,
     "Q04: chapter: file 'docs/Q04_ProofCraft.md' does not exist",
     files={"docs/Q04_ProofCraft.md": None})  # the real chapter exists since DV3k
case("paper = false with the pair", BASE, 1, "paper = false but 'paper/Q19_problems.tex' exists",
     files={"paper/Q19_problems.tex": "", "paper/Q19_answers.tex": ""})
def q18_harness(path):
    """BASE with Q18's harness list set to [path] and its gate file's import entry
    moved to path (Q18 is armed since DV5c, so its imports must stay consistent)."""
    imps = next(m for m in tomllib.loads(BASE)["module"] if m["id"] == "Q18")["imports"]
    imps = {(path if k.startswith("harness/") else k): v for k, v in imps.items()}
    inline = "{ " + ", ".join(f'"{k}" = "{v}"' for k, v in imps.items()) + " }"
    # These cases check path classification, not shipped-file existence.
    # Give their synthetic module an explicit state independent of BASE.
    fixture = setf("Q18", "status", '"authoring"')
    return setf("Q18", "imports", inline,
                setf("Q18", "harness", f'["{path}"]', fixture))


case("a Q gate file outside gate/", q18_harness("harness/q/fvh_q/q18_gate.py"), 1,
     "is a gate file; Q's gate sits under harness/q/fvh_q/gate/")
case("a Q gate module file", q18_harness("harness/q/fvh_q/gate.py"), 0, "course map OK",
     args=("--only", "registry"))
case("'gate' inside a word is no gate", q18_harness("harness/q/fvh_q/delegate.py"), 0,
     "course map OK", args=("--only", "registry"))
case("an R harness gate is ordinary learner work (R's gate is Rust)",
     edit("R15", '"harness/r/fvh_r/roundtrip.py" = "py-fvh"',
          '"harness/r/fvh_r/roundtrip.py" = "py-fvh", "harness/r/fvh_r/gate/check.py" = "py-fvh"',
          setf("R15", "harness", '["harness/r/fvh_r/spectest.py", "harness/r/fvh_r/roundtrip.py", '
               '"harness/r/fvh_r/gate/check.py"]')), 0,
     "course map OK", args=("--only", "registry"))
case("a trust-report outside R16",
     setf("R15", "harness", '["harness/r/fvh_r/spectest.py", "harness/r/fvh_r/trust_report.py"]'), 1,
     "matches R16's trust-report pattern")
case("R16 past planned without its trust-report", setf("R16", "status", '"authoring"'), 1,
     "R16 past planned lists its trust-report")
case("R16's trust-report as a contract file",
     edit("R16", '"verus/r/r16_capstone/src/agent.rs"', '"verus/r/r16_capstone/src/trust_report.rs"'), 1,
     "agentic: R16's trust-report is solo work")
case("a Dafny trust-report outside R16 (the tree is dafny/R/)",
     edit("R15", '"dafny/R/R15_VerifierLoop/std/R15_VerifierLoop.dfy"',
          '"dafny/R/R15_VerifierLoop/std/R15_trust_report.dfy"'), 1,
     "'dafny/R/R15_VerifierLoop/std/R15_trust_report.dfy' matches R16's trust-report pattern")
case("R16's Dafny trust-report as a contract file",
     edit("R16", '"dafny/R/R16_Capstone/agent/R16_AgentCapstone.dfy"',
          '"dafny/R/R16_Capstone/agent/R16_trust_report.dfy"'), 1,
     "agentic: R16's trust-report is solo work")
case("half the pair in a planned module", BASE, 1, "only half of the paper pair exists",
     files={f"paper/{PLANNED}_problems.tex": ""})

# --- engines, budget, statements, admissible -----------------------------------------------------
case("engines out of order", setf("Q18", "engines", '["policy", "contract", "agent"]'), 1,
     "engines must be listed in the order")
case("unknown engine", setf("Q18", "engines", '["contract", "rl"]'), 1,
     "engines must be distinct entries of")
case("contract without agentic files", setf("Q10", "engines", '["contract"]'), 1,
     "engines holds contract exactly when agentic lists files")
case("agentic files without contract", setf("Q05", "engines", "[]"), 1,
     "engines holds contract exactly when agentic lists files")
case("budget without a model engine",
     setf("Q05", "budget", "{ claude_calls = 1, claude_runs = 0, qwen_calls = 0, qwen_runs = 0, "
          "gpu_hours = 0 }"), 1, "it spends, but no engine runs a model")
case("model engine without budget",
     setf("Q12", "budget", "{ claude_calls = 0, claude_runs = 0, qwen_calls = 0, qwen_runs = 0, "
          "gpu_hours = 0 }"), 1, "a model engine needs its budget")
case("budget keys", setf("Q05", "budget", "{ claude_calls = 0 }"), 1, "budget must hold exactly")
case("GPU hours over the per-lab cap", setf("Q12", "budget", '{ claude_calls = 180, claude_runs = 0, qwen_calls = 4320, qwen_runs = 0, gpu_hours = 11 }'), 1,
     "budget.gpu_hours = 11 exceeds the per-lab cap of 10")
case("R12's D56 ceiling of 80 GPU-h is its own cap",
     setf("R12", "budget", "{ claude_calls = 110, claude_runs = 10, qwen_calls = 10700, qwen_runs = 1070, "
          "gpu_hours = 81 }"), 1, "budget.gpu_hours = 81 exceeds the per-lab cap of 80 (design §3; the user's D56)")
case("GPU hours over the course cap",
     setf("Q15", "budget", "{ claude_calls = 80, claude_runs = 0, qwen_calls = 1200, qwen_runs = 0, "
          "gpu_hours = 4 }"), 1, "gpu_hours sum to 46 over the registry, above the course cap of 45")
case("negative budget",
     setf("Q12", "budget", "{ claude_calls = -1, claude_runs = 0, qwen_calls = 4320, qwen_runs = 0, "
          "gpu_hours = 10 }"), 1, "budget values are non-negative integers")
case("statements on a core module",
     setf("Q05", "statements", '[{ path = "Challenges/Algorithms/Q05_x/s.dfy", sha256 = "PENDING" }]'),
     1, "statements are the frozen statement files of Q19–Q33")
case("statement with a bad hash",
     setf("Q19", "statements",
          '[{ path = "Challenges/Algorithms/Q19_Sorting/Q19_Statement.dfy", sha256 = "abc" }]'),
     1, "sha256 must be 64 lower-case hex digits")
case("statement outside the challenge",
     setf("Q19", "statements",
          '[{ path = "Challenges/Quant/Q19_Sorting/Q19_Statement.dfy", sha256 = "PENDING" }]'),
     1, "must sit under Challenges/Algorithms/Q19_<Name>/")
case("a pending statement",
     setf("Q19", "statements",
          '[{ path = "Challenges/Algorithms/Q19_Sorting/Q19_Statement.dfy", sha256 = "PENDING" }]'),
     0, "course map OK")
case("a Rust statement file, lower-case",
     setf("Q19", "statements", '[{ path = "Challenges/Algorithms/Q19_Sorting/q19_sorting/src/statement.rs", '
          'sha256 = "PENDING" }]'), 0, "course map OK")
case("a statement file not named Statement",
     setf("Q19", "statements", '[{ path = "Challenges/Algorithms/Q19_Sorting/Q19_Spec.dfy", '
          'sha256 = "PENDING" }]'), 1, "a statement file's name holds 'Statement'")
case("challenge past planned without statements", setf("Q19", "status", '"authoring"'), 1,
     "lists its frozen statement files")
# R08's planned F6 interface is provided, immutable input, never a learner file.
R08_STATEMENT = "dafny/given/R/RG_A2_MatcherStatement.dfy"
R08_PIN = __import__("hashlib").sha256((ROOT / R08_STATEMENT).read_bytes()).hexdigest()
R08_DESC = '[{ path = "' + R08_STATEMENT + '", sha256 = "' + R08_PIN + '" }]'
case("R08: exact provided matcher statement", setf("R08", "statements", R08_DESC),
     0, "course map OK")
case("R08: no pending matcher pin", setf("R08", "statements",
     '[{ path = "' + R08_STATEMENT + '", sha256 = "PENDING" }]'),
     1, "needs an actual SHA256 pin")
case("R08: statement cannot be a learner file", setf("R08", "statements",
     '[{ path = "dafny/R/R08_Abstraction/std/R08_Statement.dfy", sha256 = "' + R08_PIN + '" }]'),
     1, "uses the exact provided A2 matcher")
case("R08: only one provided statement", setf("R08", "statements",
     R08_DESC[:-1] + ', ' + R08_DESC[1:]), 1, "one frozen matcher statement")
case("R08: matcher bytes cannot change", BASE, 1, "statement hash mismatch",
     files={R08_STATEMENT: (ROOT / R08_STATEMENT).read_text() + "\n// changed bytes\n"})
case("R08: matcher file cannot disappear", BASE, 1, "provided matcher statement does not exist",
     files={R08_STATEMENT: None})
case("R08: existing matcher cannot lose its pin", setf("R08", "statements", "[]"),
     1, "provided matcher must be declared and pinned")
case("R07: provided statements remain disallowed", setf("R07", "statements", R08_DESC),
     1, "statements are the frozen statement files of Q19–Q33")
# D97: R16's statements are the learner's, PENDING in the registry until the
# learner's post-review commit pins them; inside R16's trees, among its exercises.
R16_ST_D = "dafny/R/R16_Capstone/std/R16_Statements.dfy"
R16_ST_V = "verus/r/r16_capstone/src/statements.rs"
R16_EX = ('["dafny/R/R16_Capstone/std/R16_Capstone.dfy", "' + R16_ST_D + '", '
          '"verus/r/r16_capstone/src/lib.rs", "' + R16_ST_V + '", "specimens/R16/"]')
R16_ST = ('[{ path = "' + R16_ST_D + '", sha256 = "PENDING" }, '
          '{ path = "' + R16_ST_V + '", sha256 = "PENDING" }]')


def r16_statements(statements, exercises=R16_EX):
    return setf("R16", "statements", statements, setf("R16", "exercises", exercises))


case("R16: learner-written statements, pending", r16_statements(R16_ST), 0, "course map OK")
case("R16: a statement pinned in the registry",
     r16_statements(R16_ST.replace('"PENDING" }]', '"' + "a" * 64 + '" }]')),
     1, "pinned by the learner's post-review commit, never in the registry")
case("R16: a statement outside its trees",
     r16_statements('[{ path = "dafny/R/R15_VerifierLoop/std/R16_Statements.dfy", '
                    'sha256 = "PENDING" }]'), 1, "statement files sit in its own trees")
case("R16: a statement that is not an exercise", r16_statements(R16_ST, "[]"),
     1, "is not one of R16's exercises")
case("R16: a statement file not named Statement",
     r16_statements('[{ path = "dafny/R/R16_Capstone/std/R16_Capstone.dfy", '
                    'sha256 = "PENDING" }]'), 1, "a statement file's name holds 'Statement'")
case("R15: learner statements stay R16's", setf("R15", "statements",
     '[{ path = "dafny/R/R15_VerifierLoop/std/R15_Statements.dfy", sha256 = "PENDING" }]'),
     1, "statements are the frozen statement files of Q19–Q33")
case("gated item with minutes",
     setf("Q14", "admissible", '{ "Q14.H4d" = { admitted = false, minutes = 30, fallback = "x" } }'),
     1, "is gated: no minutes (0) and a named fallback")
case("gated item without a fallback",
     setf("Q14", "admissible", '{ "Q14.H4d" = { admitted = false, minutes = 0, fallback = "" } }'),
     1, "is gated")
case("admitted item without minutes",
     setf("Q14", "admissible", '{ "Q14.H4d" = { admitted = true, minutes = 0, fallback = "" } }'),
     1, "is admitted, so it carries its minutes")
# spliced into Q14's own table: Q14 ships authored files, so every item of it keeps its entry
case("a gated item with its fallback",
     re.sub(r'(?m)^"Q14\.H4d" = .*$',
            lambda _: '"Q14.H4d" = { admitted = false, minutes = 0, fallback = "the loop rule on paper" }',
            BASE, count=1),
     0, "course map OK")
# D2 (DV5c): a declared band exception, a fourth key on an admitted item only
case("admitted items with their declared band exceptions, as committed",
     BASE, 0, "module(s) past planned", args=("--only", "coverage"))
# DV5e review fix: the band is checked against OUT_OF_BAND's recorded proof lines
case("a band exception on an admitted item OUT_OF_BAND records in its band (Q14.H1d)",
     re.sub(r'(?m)^"Q14\.H1d" = (.*) \}$',
            lambda mm: f'"Q14.H1d" = {mm.group(1)}, exception = "short-format band: any words" }}',
            BASE, count=1),
     1, "'Q14.H1d' carries an exception, but OUT_OF_BAND records it in its band")
case("a below-band item admitted with its exception deleted (Q15.H3d)",
     re.sub(r'(?m)^"Q15\.H3d" = .*$',
            lambda _: '"Q15.H3d" = { admitted = true, minutes = 18, fallback = "x" }',
            BASE, count=1),
     1, "'Q15.H3d' is admitted outside its band (0 proof lines, OUT_OF_BAND) with no exception")
case("a below-band item's exception retyped to another kind (Q15.H4d as short-format)",
     re.sub(r'(?m)^"Q15\.H4d" = .*$',
            lambda _: '"Q15.H4d" = { admitted = true, minutes = 18, fallback = "x", '
                      'exception = "short-format band: probe; the user\'s decision D21" }',
            BASE, count=1),
     1, "'Q15.H4d' carries a 'short-format band' exception, but OUT_OF_BAND records it under "
        "'hidden-check spec'")
case("a below-band item's exception that names no decision (Q18.H1v)",
     re.sub(r'(?m)^"Q18\.H1v" = .*$',
            lambda _: '"Q18.H1v" = { admitted = true, minutes = 15, fallback = "x", '
                      'exception = "short-format band: short by design" }',
            BASE, count=1),
     1, "'Q18.H1v': its exception's reason names the decision that admits it (D7)")
case("an OUT_OF_BAND item the registry gates (Q15.H1v)",
     re.sub(r'(?m)^"Q15\.H1v" = .*$',
            lambda _: '"Q15.H1v" = { admitted = false, minutes = 0, fallback = "x" }',
            BASE, count=1),
     1, "OUT_OF_BAND: 'Q15.H1v' records an item the registry does not admit")
unit("out_of_band_problems: every committed entry is outside its band; an in-band figure, "
     "a Python item and a non-practice module are refused",
     lambda: _out_of_band_unit())
case("a band exception on a gated item",
     re.sub(r'(?m)^"Q14\.H4d" = .*$',
            lambda _: '"Q14.H4d" = { admitted = false, minutes = 0, fallback = "x", '
                      'exception = "short-format band: why" }',
            BASE, count=1),
     1, "carries an exception but is not admitted")
case("a band exception of an unknown kind",
     re.sub(r'(?m)^"Q14\.H3d" = .*$',
            lambda _: '"Q14.H3d" = { admitted = true, minutes = 12, fallback = "x", '
                      'exception = "too short" }',
            BASE, count=1),
     1, "exception must be \"<kind>: <why>\"")
case("a band exception with no reason",
     re.sub(r'(?m)^"Q14\.H3d" = .*$',
            lambda _: '"Q14.H3d" = { admitted = true, minutes = 12, fallback = "x", '
                      'exception = "short-format band: " }',
            BASE, count=1),
     1, "exception must be")
# D6, D9 (DV5d): the statement-item kind, on a prose item (Q17.H3d) or an item of an
# agentic file (Q18.H2d/H2v: no shipped hole; firsttry's statement route)
case("a statement-item exception on a prose item and on agentic-file items, as committed",
     BASE, 0, "module(s) past planned", args=("--only", "coverage"))
case("a statement-item exception on an item that is neither a prose item nor agentic",
     re.sub(r'(?m)^"Q17\.H1d" = .*$',
            lambda _: '"Q17.H1d" = { admitted = true, minutes = 50, fallback = "x", '
                      'exception = "statement-item: the learner states it" }',
            BASE, count=1),
     1, "'Q17.H1d' carries a statement-item exception, but its block is no prose item")
case("a statement-item exception on a prose item that names no contractor (Q15's Lab 2 spec)",
     re.sub(r'(?m)^"Q15\.H3d" = .*$',
            lambda _: '"Q15.H3d" = { admitted = true, minutes = 18, fallback = "x", '
                      'exception = "statement-item: probe" }',
            BASE, count=1),
     1, "'Q15.H3d' carries a statement-item exception, but its prose block names no contractor")
case("a statement-item exception with no reason",
     re.sub(r'(?m)^"Q17\.H3d" = .*$',
            lambda _: '"Q17.H3d" = { admitted = true, minutes = 35, fallback = "x", '
                      'exception = "statement-item:  " }',
            BASE, count=1),
     1, "exception must be \"<kind>: <why>\" with kind one of 'short-format band', "
        "'statement-item', 'hidden-check spec'")
case("a statement-item exception on a gated item",
     re.sub(r'(?m)^"Q18\.H2v" = .*$',
            lambda _: '"Q18.H2v" = { admitted = false, minutes = 0, fallback = "x", '
                      'exception = "statement-item: why" }',
            BASE, count=1),
     1, "'Q18.H2v' carries an exception but is not admitted")
case("a short-format exception needs no prose block (Q18.H1d, as committed)",
     BASE, 0, "course map OK", args=("--only", "registry"))
unit("statement_item_problem: prose with and without a contractor, agentic and plain blocks",
     lambda: _statement_item_unit())
# D21 (DV5e): the hidden-check spec kind, on an H prose item of an exercise file that
# names no contractor, whose hidden check is recorded as holding (Δ220) and whose module's
# sealed truth is pinned (Q15's five below-band Lab 2 specifications)
case("hidden-check spec exceptions on Q15's prose specifications, as committed",
     BASE, 0, "module(s) past planned", args=("--only", "coverage"))
case("a hidden-check spec exception on an item that is no prose item",
     re.sub(r'(?m)^"Q15\.H1d" = .*$',
            lambda _: '"Q15.H1d" = { admitted = true, minutes = 8, fallback = "x", '
                      'exception = "hidden-check spec: probe" }',
            BASE, count=1),
     1, "'Q15.H1d' carries a hidden-check spec exception, but its block is no prose item")
case("a hidden-check spec exception on a prose item that names its contractor (Q17.H3d)",
     re.sub(r'(?m)^"Q17\.H3d" = .*$',
            lambda _: '"Q17.H3d" = { admitted = true, minutes = 35, fallback = "x", '
                      'exception = "hidden-check spec: probe" }',
            BASE, count=1),
     1, "'Q17.H3d' carries a hidden-check spec exception, but its prose block names a "
        "contractor")
case("a hidden-check spec exception on an agentic-file item (Q18.H2d)",
     re.sub(r'(?m)^"Q18\.H2d" = .*$',
            lambda _: '"Q18.H2d" = { admitted = true, minutes = 12, fallback = "x", '
                      'exception = "hidden-check spec: probe" }',
            BASE, count=1),
     1, "'Q18.H2d' carries a hidden-check spec exception, but it sits in one of the "
        "module's agentic files")
case("a hidden-check spec exception whose module's sealed truth is not pinned",
     BASE, 1, "'Q15.H3d' carries a hidden-check spec exception, but sandbox/truth.toml pins "
              "no sealed hidden truth for Q15",
     files={"sandbox/truth.toml": "schema = 1\n"})
case("a hidden-check spec exception on a gated item",
     re.sub(r'(?m)^"Q15\.H5v" = .*$',
            lambda _: '"Q15.H5v" = { admitted = false, minutes = 0, fallback = "x", '
                      'exception = "hidden-check spec: why" }',
            BASE, count=1),
     1, "'Q15.H5v' carries an exception but is not admitted")
case("a hidden-check spec exception with no reason",
     re.sub(r'(?m)^"Q15\.H5v" = .*$',
            lambda _: '"Q15.H5v" = { admitted = true, minutes = 18, fallback = "x", '
                      'exception = "hidden-check spec:  " }',
            BASE, count=1),
     1, "exception must be \"<kind>: <why>\"")
unit("hidden_check_problem: a recorded prose item passes; unrecorded, unsealed, contractor, "
     "agentic, non-exercise, plain and non-H blocks are refused",
     lambda: _hidden_check_unit())
# D16 (DV5d): the capstone crate's binary target, generated, and its root declared in
# imports though no registry list names it
case("a binary root declared by a module with no binary target",
     BASE.replace('"verus/q/q17_practice_iiib/src/perm.rs" = "all"\n',
                  '"verus/q/q17_practice_iiib/src/perm.rs" = "all"\n'
                  '"verus/q/q17_practice_iiib/src/main.rs" = "arithmetic"\n', 1),
     1, "imports: 'verus/q/q17_practice_iiib/src/main.rs' is not one of Q17's files",
     files={"verus/q/q17_practice_iiib/src/main.rs": "fn main() {}\n"})
case("the capstone's binary root missing",
     BASE, 1, "binary target's root src/main.rs does not exist", script="gen",
     args=("--check",), files={"verus/q/q18_practice_iiic/src/main.rs": None})
unit("gen_units renders a [[bin]] for the capstone crate only",
     lambda: None if ("[[bin]]\nname = \"bignat\"\npath = \"src/main.rs\"\n"
                      in gu.render_crate("Q18", "q18_practice_iiic", "L7")
                      and "[[bin]]" not in gu.render_crate("Q17", "q17_practice_iiib", "L7"))
     else "the rendered crates' [[bin]] tables are wrong")
case("an unknown fifth admissible key",
     re.sub(r'(?m)^"Q14\.H3d" = .*$',
            lambda _: '"Q14.H3d" = { admitted = true, minutes = 12, fallback = "x", note = "y" }',
            BASE, count=1),
     1, "must be { admitted = …, minutes = …, fallback = ")
case("admissible key of another module",
     setf("Q14", "admissible", '{ "Q13.H4d" = { admitted = true, minutes = 30, fallback = "" } }'),
     1, "must be an item id of Q14")

# --- constructs -------------------------------------------------------------------------------------
case("WRITE over the unit cap",
     setf("Q05", "write_v", '["a", "b", "c"]', setf("Q05", "write_d", '["d", "e", "f", "g"]')), 1,
     "at most 6 units and 10 slugs")
case("WRITE over the slug cap",
     setf("Q05", "write_v", '["a", "b", "c", "d", "e", "f"]',
          setf("Q05", "write_d", '["a", "b", "c", "d", "e"]')), 1, "11 slug(s)")
case("integer-ring in Verus", setf("Q07", "write_v", '["bit-vector", "integer-ring"]'), 1,
     "'integer-ring' is not available at the pin")
case("WRITE and RECOGNISE overlap", setf("Q05", "recognise_d", '["by-method"]'), 1,
     "is both WRITE (by-method) and RECOGNISE")
case("a construct that is no slug", setf("Q05", "write_d", '["By Method"]'), 1,
     "is not a construct slug")
case("RECOGNISE on a practice module", setf("Q10", "recognise_v", '["calc"]'), 1,
     "recognise_d / recognise_v are for the concept tiers")
case("a concept module without WRITE", setf("Q05", "write_d", "[]"), 1, "write_d is empty")
case("a WRITE list for an absent language", setf("Q20", "write_d", '["calc"]'), 1,
     "'write_d' is non-empty but langs has no d")
case("a construct listed twice", setf("Q05", "write_v", '["result", "result"]'), 1,
     "lists a construct twice")

# --- the imports table ------------------------------------------------------------------------------
case("unknown import tier",
     setf("Q05", "imports", '{ "dafny/Q/Q05_Frames/std/Q05_Frames.dfy" = "mathlib" }'), 1,
     "has tier 'mathlib', not one of: core, std, std-all")
case("a Verus file with a Dafny tier",
     setf("Q05", "imports", '{ "verus/q/q05_frames/src/lib.rs" = "std" }'), 1,
     "not one of: prelude, seq_lib, arithmetic, all")
case("an imports key that is no module file",
     setf("Q05", "imports", '{ "dafny/Q/Q05_Frames/std/Other.dfy" = "std" }'), 1,
     "is not one of Q05's files")
case("a given layer declared by the wrong module",
     setf("Q05", "imports", '{ "dafny/given/Q/QG_L3_BigNat.dfy" = "std" }'), 1,
     "declared by Q04, the first module of its layer")
case("a library tier before Q04",
     setf("Q02", "imports", '{ "verus/q/q02_first_syntax_i/src/lib.rs" = "seq_lib" }'), 1,
     "the library enters at Q04 / R07")
case("a core-unit file with a std tier",
     setf("Q04", "imports", '{ "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy" = "std" }'), 1,
     "sits in a core unit; its tier is core")
case("a std-unit file with the core tier",
     setf("Q04", "imports", '{ "dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy" = "core" }'), 1,
     "sits in a std unit")
case("a module past planned declares every file",
     edit("Q04", '"verus/q/q04_proof_craft/src/agent.rs" = "prelude"\n', "", ARMED), 1,
     "agentic file 'verus/q/q04_proof_craft/src/agent.rs' has no import tier", armed=True)

# --- the D4 matrix (registry-only) ---------------------------------------------------------------------
case("concept_items on a practice module",
     setf("Q10", "concept_items", '{ "S1.x" = ["Q10.H1d"] }'), 1, "Q01–Q09 only")
case("malformed concept key", setf("Q05", "concept_items", '{ "x" = "R" }'), 1,
     "must be S<k>.<concept>[@d|@v|@py]")
case("concept key outside the strands", setf("Q05", "concept_items", '{ "S1.x" = "R" }'), 1,
     "S1 is not one of Q05's strands")
case("prose off S12/S13", setf("Q05", "concept_items", '{ "S6.essay" = "prose" }'), 1,
     "only S12 and S13 keys may rest on a learner-written artifact")
def with_concept(mid, key, value, text=BASE):
    """text with mid's concept_items holding `key = value` (TOML text), its
    other keys kept (an armed record's coverage rests on them)."""
    import tomllib
    rec = next(m for m in tomllib.loads(text)["module"] if m.get("id") == mid)
    body = _inline(rec.get("concept_items") or {})
    body = body[:-2] + f", \"{key}\" = {value} }}" if body != "{}" else f'{{ "{key}" = {value} }}'
    return setf(mid, "concept_items", body, text)


case("prose on S13", with_concept("Q06", "S13.eval-md", '"prose"'), 0, "course map OK")
case("citing another module's item", setf("Q05", "concept_items", '{ "S6.x" = ["Q04.H1dv"] }'), 1,
     "items of another module")
case("citing a worked example", setf("Q05", "concept_items", '{ "S6.x" = ["Q05.W1dv"] }'), 1,
     "only P, H, X, T and A items are checked")
case("an unsuffixed key with one language", setf("Q05", "concept_items", '{ "S6.x" = ["Q05.H1d"] }'),
     1, "cites a Dafny and a Verus item")
case("a @v key citing a Dafny item", setf("Q05", "concept_items", '{ "S6.x@v" = ["Q05.H1d"] }'), 1,
     "is @v but cites Q05.H1d")
case("a @py key without Python", setf("Q05", "concept_items", '{ "S6.x@py" = "R" }'), 1,
     "is @py, but langs has no py")

# --- the ledger -------------------------------------------------------------------------------------------
case("ledger: known tags", BASE, 0, "2 tag(s), all known",
     ledger="- tag: Q04/loop-invariant | error: x\n- tag: R06/loop-invariants | error: y\n")
case("ledger: unknown module", BASE, 1, "names no known module", ledger="- tag: X01/foo | error: x\n")
case("ledger: no vocabulary tag", BASE, 1, "is not <module id>/<vocab-tag>",
     ledger="- tag: Q04 | error: x\n")
case("ledger: the schema comment is not an entry", BASE, 0, "0 tag(s)",
     ledger="<!--\n- tag: <ID>/<vocab-tag> | error: x\n-->\n")
case("ledger: legacy id", setf("R05", "legacy_id", '"F05"'), 1, "uses the legacy id F05",
     ledger="- tag: F05/statistics | error: x\n")

# --- --resolve, --list-nonplanned ----------------------------------------------------------------------------
case("resolve a Q id, any case", BASE, 0, '"id": "Q33"', args=("--resolve", "q33"))
case("resolve shows the new fields", BASE, 0, '"units": ["dafny/Q/Q04_ProofCraft/core"',
     args=("--resolve", "Q04"))
case("resolve a legacy id", setf("R05", "legacy_id", '"F05"'), 0, '"id": "R05"',
     args=("--resolve", "f05"))
case("resolve an unknown id", BASE, 3, "unknown module id", args=("--resolve", "X99"))
case("resolve nothing", BASE, 3, "unknown module id", args=("--resolve", ""))
case("resolve a malformed record", setf("R04", "paper", '"yes"'), 1, "'paper' must be true or false",
     args=("--resolve", "R04"))
case("--list-nonplanned", ARMED, 0, "Q04", armed=True, args=("--list-nonplanned", "Q01-Q18"))
case("--list-nonplanned: none armed", BASE, 0, "",
     args=("--list-nonplanned", f"{PLANNED}-{PLANNED}"))
case("--list-nonplanned: a malformed range", BASE, 2, "wants a range",
     args=("--list-nonplanned", "Q01-R18"))
case("--list-nonplanned: a reversed range", BASE, 2, "wants a range",
     args=("--list-nonplanned", "Q18-Q01"))

# --- the armed module: every group passes ------------------------------------------------------------------
case("armed: every group passes", ARMED, 0, f"{1 + REAL_AUTHORING} authoring", armed=True)
for group, line in (("units", f"units: {3 + REAL_UNITS} unit(s)"),
                    ("import-tiers", f"import-tiers: {ARMED_IMPORT_FILES} files"),
                    ("isolation", "isolation:"),
                    ("coverage", f"coverage: {1 + len(REAL_ARMED)} module(s) past planned ({ARMED_IDS})")):
    case(f"armed: --only {group}", ARMED, 0, line, armed=True, args=("--only", group))
case("armed: gen_units --check", ARMED, 0, f"{3 + REAL_UNITS} unit(s) and verus/Cargo.toml match", armed=True,
     script="gen", args=("--check",))
case("armed: gen_units --list shows the layer chain (Δ22)", ARMED, 0,
     '"dependencies": ["vstd", "qg_bignat_l1", "qg_bignat_l2", "qg_bignat_l3"]', armed=True,
     script="gen", args=("--list", "--json"))
case("armed: a core unit reaches only the core layers (Δ34)", ARMED, 0,
     '"includes": ["*.dfy", "../../../given/Q/QG_L1_*.dfy", "../../../given/Q/QG_L2_*.dfy"]',
     armed=True, script="gen", args=("--list", "--json"))

# --- units ----------------------------------------------------------------------------------------------------
case("units: a generated file edited by hand", ARMED, 1,
     "dafny/Q/Q04_ProofCraft/std/dfyconfig.toml: differs from the generator's output", armed=True,
     after={"dafny/Q/Q04_ProofCraft/std/dfyconfig.toml": 'includes = ["*.dfy"]\n'})
case("units: a generated file never written", ARMED, 1,
     "verus/q/q04_proof_craft/Cargo.toml: missing", armed=True,
     after={"verus/q/q04_proof_craft/Cargo.toml": None})
case("units: the workspace drifts", ARMED, 1, "verus/Cargo.toml: differs", armed=True,
     after={"verus/Cargo.toml": '[workspace]\nresolver = "2"\nmembers = ["q/q04_proof_craft"]\n'})
case("units: a stale project file", BASE, 1, f"{PLANNED_D}/std/dfyconfig.toml: stale project file",
     files={f"{PLANNED_D}/std/dfyconfig.toml": 'includes = ["*.dfy"]\n'})
case("units: an unknown Cargo.toml in a learner tree", BASE, 1,
     f"{PLANNED_V}/Cargo.toml: unknown Cargo.toml",
     files={f"{PLANNED_V}/Cargo.toml": f"[package]\nname = \"{PLANNED_V.rsplit('/', 1)[1]}\"\n"})
case("units: a build script", ARMED, 1, "build scripts never belong in a learner crate", armed=True,
     files={"verus/q/q04_proof_craft/build.rs": "fn main() {}\n"})
case("units: a .cargo directory", ARMED, 1, "a .cargo directory in a learner tree", armed=True,
     files={"verus/q/q04_proof_craft/.cargo/config.toml": "[build]\n"})
case("units: an exit declared as a module", ARMED, 1, "declares `mod exit;`", armed=True,
     files=fx(RS, "use qg_bignat_l3::*;\n", "use qg_bignat_l3::*;\nmod exit;\n"))
case("units: a layer glob that matches nothing (Δ27)", ARMED, 1,
     "'../../../given/Q/QG_L2_*.dfy' matches no file", armed=True,
     after={"dafny/given/Q/QG_L2_BigNat.dfy": None}, args=("--only", "units"))
case("units: a missing layer crate (Δ22)", ARMED, 1,
     "its layer crate verus/given/qg_bignat_l2 does not exist", armed=True,
     after={"verus/given/qg_bignat_l2/Cargo.toml": None, "verus/given/qg_bignat_l2/src/lib.rs": None},
     args=("--only", "units"))
case("units: a layer crate off the chain (Δ22)", ARMED, 1,
     "verus/given/qg_bignat_l3/Cargo.toml: dependencies", armed=True,
     files=fx("verus/given/qg_bignat_l3/Cargo.toml", 'qg_bignat_l1 = { path = "../qg_bignat_l1" }\n', ""))
case("units: a layer crate with a [patch] (Δ20)", ARMED, 1, "no [patch] section", armed=True,
     files=fx("verus/given/qg_bignat_l1/Cargo.toml", "[package.metadata.verus]",
              "[patch.crates-io]\nvstd = { path = \"x\" }\n\n[package.metadata.verus]"))
OPT_CORE = (ROOT / "dafny/options/core.toml").read_text(encoding="utf-8")
OPT_STD = (ROOT / "dafny/options/std.toml").read_text(encoding="utf-8")
case("options: a refused key (Δ10)", BASE, 1, "'allow-warnings' is refused",
     files={"dafny/options/core.toml": sub(OPT_CORE, "resource-limit = 5000000",
                                           "resource-limit = 5000000\nallow-warnings = true")})
case("options: a base chain (Δ10)", BASE, 1, "'base' is refused",
     files={"dafny/options/core.toml": sub(OPT_CORE, "\n[options]\n", '\n[options]\nbase = "../x.toml"\n')})
case("options: an unknown key", BASE, 1, "'cores' is not an allowed unit option",
     files={"dafny/options/std.toml": sub(OPT_STD, "\n[options]\n", "\n[options]\ncores = 2\n")})
case("options: the resource-limit pin (Δ56)", BASE, 1, "must be the course pin 5000000",
     files={"dafny/options/core.toml": sub(OPT_CORE, "resource-limit = 5000000", "resource-limit = 100")})
case("options: the std tier needs the library (Δ34)", BASE, 1,
     "standard-libraries must be true in the std tier",
     files={"dafny/options/std.toml": sub(OPT_STD, "standard-libraries = true\n", "")})
case("options: the core tier has no library", BASE, 1,
     "standard-libraries must be absent or false in the core tier",
     files={"dafny/options/core.toml": sub(OPT_CORE, "resource-limit = 5000000",
                                           "resource-limit = 5000000\nstandard-libraries = true")})
case("options: a cross-track override range", BASE, 1, "must be a range like Q03-Q18",
     files={"dafny/options/core.toml": sub(OPT_CORE, '"Q03-Q18"', '"Q03-R16"')})
case("options: an override changing the pin", BASE, 1, "an override may not change them",
     files={"dafny/options/core.toml": sub(OPT_CORE, "manual-lemma-induction = true",
                                           "resource-limit = 1")})
case("options: a missing tier file", BASE, 1, "dafny/options/std.toml: not found",
     files={"dafny/options/std.toml": None})
case("options: Q03 on gets manual lemma induction (Δ45)", ARMED, 0, "manual-lemma-induction",
     armed=True, script="cat", args=("dafny/Q/Q04_ProofCraft/core/dfyconfig.toml",))

# --- import tiers ---------------------------------------------------------------------------------------------
case("tiers: a core file imports Std", ARMED, 1, f"{PC}:3: reaches Std.Wrappers but its tier is core",
     armed=True, files=fx(PC, "  import opened QG_L1_BigNat\n",
                          "  import Std.Wrappers\n  import opened QG_L1_BigNat\n"))
case("tiers: a core file reaches Std through a std-tier layer", ARMED, 1,
     "reaches Std.Wrappers (via QG_L3_BigNat) but its tier is core", armed=True,
     files=fx(PC, "  import opened QG_L2_BigNat\n", "  import opened QG_L2_BigNat\n  import opened QG_L3_BigNat\n"),
     args=("--only", "import-tiers"))
case("tiers: the std tier excludes LittleEndianNat (Δ35)", ARMED, 1, "the std tier excludes it",
     armed=True, files=fx(LIB, "  import opened Std.Wrappers\n",
                          "  import opened Std.Wrappers\n  import Std.Arithmetic.LittleEndianNat\n"))
case("tiers: a layer whose second module imports its first (L4's QG_L4_Limbs, DV3b)", ARMED, 0,
     "import-tiers:", armed=True,
     files=fx("dafny/given/Q/QG_L3_BigNat.dfy",
              "  function Wrap(): Wrappers.Option<nat> { Wrappers.Some(BASE) }\n}\n",
              "  function Wrap(): Wrappers.Option<nat> { Wrappers.Some(BASE) }\n}\n"
              "module QG_L3_Extra {\n  import QG_L3_BigNat\n}\n"),
     args=("--only", "import-tiers"))
case("tiers: std-all may reach it", edit("Q04", f'"{LIB}" = "std"', f'"{LIB}" = "std-all"', ARMED), 0,
     "import-tiers:", armed=True, args=("--only", "import-tiers"),
     files=fx(LIB, "  import opened Std.Wrappers\n",
              "  import opened Std.Wrappers\n  import Std.Arithmetic.LittleEndianNat\n"))
case("tiers: a prelude file uses vstd::arithmetic", ARMED, 1,
     f"{EXIT_RS}:4: uses vstd::arithmetic but its tier is prelude", armed=True,
     files=fx(EXIT_RS, "use qg_bignat_l1::*;\n", "use qg_bignat_l1::*;\nuse vstd::arithmetic::mul::*;\n"))
case("tiers: a prelude file reaches seq_lib through a layer", ARMED, 1,
     "uses vstd::seq_lib (via qg_bignat_l3) but its tier is prelude", armed=True,
     files=fx(EXIT_RS, "use qg_bignat_l1::*;\n", "use qg_bignat_l3::*;\n"))
case("tiers: a braced vstd import", ARMED, 1, "uses vstd::arithmetic but its tier is prelude",
     armed=True, files=fx(EXIT_RS, "use vstd::prelude::*;\n",
                          "use vstd::{prelude::*, arithmetic::power::*};\n"))
case("tiers: a prelude file may use the calc! macro (QPLAN §6 Q16)", ARMED, 0,
     f"import-tiers: {ARMED_IMPORT_FILES} files", armed=True,
     files=fx(EXIT_RS, "use vstd::prelude::*;\n",
              "use vstd::prelude::*;\nuse vstd::calc;\nuse vstd::calc_macro::*;\n"),
     args=("--only", "import-tiers"))
case("tiers: calc! in a braced import beside a prelude path", ARMED, 0, "import-tiers:", armed=True,
     files=fx(EXIT_RS, "use vstd::prelude::*;\n", "use vstd::{prelude::*, calc};\n"),
     args=("--only", "import-tiers"))
case("tiers: a wider tier inherits the calc! macro (Δ131)", ARMED, 0, "import-tiers:", armed=True,
     files=fx(RS, "use vstd::prelude::*;\n", "use vstd::prelude::*;\nuse vstd::calc;\n"),
     args=("--only", "import-tiers"))
case("tiers: calc! admits no other root module", ARMED, 1,
     "uses vstd::calculus but its tier is prelude", armed=True,
     files=fx(EXIT_RS, "use vstd::prelude::*;\n", "use vstd::prelude::*;\nuse vstd::calculus;\n"),
     args=("--only", "import-tiers"))
case("tiers: an undeclared course file", ARMED, 1, "undeclared course file escapes the tier check",
     armed=True, files={"dafny/Q/Q04_ProofCraft/core/Q04_Stray.dfy": "module Q04_Stray {\n}\n"})
_q01s, _q01e = table("Q01", ARMED)
case("tiers: a file declared by two records (a duplicated table)",
     ARMED[:_q01e] + ARMED[_q01s:_q01e] + ARMED[_q01e:], 1,
     "'dafny/given/Q/QG_L1_BigNat.dfy' is also declared by Q01", armed=True,
     args=("--only", "import-tiers"))
case("tiers: the glob is empty while a module is armed", ARMED, 1, "a broken glob, not a pass",
     armed=True, after={**{p: None for p in TREE if p.startswith(("dafny/Q/", "verus/q/"))},
                        "dafny/Q": None, "dafny/R": None, "dafny/checks": None,
                        "verus/q": None, "verus/r": None,
                        "harness/q/fvh_q": None, "harness/r/fvh_r": None},
     args=("--only", "import-tiers"))
STATS = "harness/q/fvh_q/q06_stats.py"
INIT = "harness/q/fvh_q/__init__.py"


def with_import(mid, path, tier, text=BASE):
    """text with mid's imports holding `path = tier`, its other entries kept
    (a record armed since keeps every file it declares)."""
    import tomllib
    rec = next(m for m in tomllib.loads(text)["module"] if m.get("id") == mid)
    imports = {**(rec.get("imports") or {}), path: tier}
    return setf(mid, "imports", "{ " + ", ".join(f'"{k}" = "{v}"' for k, v in imports.items())
                + " }", text)


def _counted_on_disk(*rels):
    """How many of rels the base count already holds: a declared file on disk,
    or a package __init__.py on disk (the checker counts those itself)."""
    import tomllib
    declared = {p for m in tomllib.loads(BASE).get("module", []) if isinstance(m, dict)
                for p in (m.get("imports") or {})}
    return sum(1 for r in rels if (ROOT / r).is_file() and
               (r in declared or PurePosixPath(r).name == "__init__.py"))


def _pkgs_after_overlay(rel):
    """PKG_ON_DISK as the checker sees it once rel is overlaid: materialize()
    makes rel's directory real with its entries symlinked, and the `**` glob
    of course_files() does not descend a symlinked subdirectory, so a package
    nested below that directory (Q09's harness/q/fvh_q/gate/) is not counted."""
    here = PurePosixPath(rel).parent
    hidden = sum(1 for p in (ROOT / here).rglob("__init__.py")
                 if p.parent != ROOT / here)
    return PKG_ON_DISK - hidden


case("tiers: py-std imports fvh", with_import("Q06", STATS, "py-std"), 1,
     f"{STATS}:1: imports fvh but its tier is py-std", files={STATS: "import fvh.stats\n"})
case("tiers: py-fvh may import fvh", with_import("Q06", STATS, "py-fvh"), 0,
     f"import-tiers: {BASE_ON_DISK + _pkgs_after_overlay(STATS) + 1 - _counted_on_disk(STATS)} file",
     files={STATS: "import json\nfrom fvh import stats\nfrom . import x\n"},
     args=("--only", "import-tiers"))
case("tiers: a package __init__.py needs no owner", with_import("Q06", STATS, "py-fvh"), 0,
     f"import-tiers: {BASE_ON_DISK + _pkgs_after_overlay(STATS) + 2 - _counted_on_disk(STATS, INIT)} files",
     files={STATS: "import json\n", INIT: "from . import x\n"},
     args=("--only", "import-tiers"))
case("tiers: a package __init__.py is still checked", BASE, 1, "imports numpy but its tier is py-fvh",
     files={INIT: "import numpy\n"})
case("tiers: a check unit is a course file", BASE, 1,
     "dafny/checks/Q09_checks.dfy: undeclared course file",
     files={"dafny/checks/Q09_checks.dfy": "module Q09_Checks {\n}\n"})
case("tiers: a third-party package", with_import("Q06", STATS, "py-fvh"), 1,
     "imports numpy but its tier is py-fvh", files={STATS: "import numpy as np\n"})

# --- isolation -------------------------------------------------------------------------------------------------
case("isolation: a Q file imports an R module", ARMED, 1, "a module of the other track (I2", armed=True,
     files=fx(PC, "  import opened QG_L2_BigNat\n", "  import opened QG_L2_BigNat\n  import R07_Libraries\n"))
case("isolation: a Q file imports another module's file", ARMED, 1, "another module's file", armed=True,
     files=fx(PC, "  import opened QG_L2_BigNat\n", "  import opened QG_L2_BigNat\n  import Q03_FirstSyntaxII\n"))
case("isolation: a layer above the tier", ARMED, 1, "a layer above the module's tier", armed=True,
     files=fx(PC, "  import opened QG_L2_BigNat\n", "  import opened QG_L2_BigNat\n  import QG_L4_BigNat\n"),
     args=("--only", "isolation"))
case("isolation: an R layer from a Q file", ARMED, 1, "a layer of the other track", armed=True,
     files=fx(PC, "  import opened QG_L2_BigNat\n", "  import opened QG_L2_BigNat\n  import RG_A1_Re\n"),
     args=("--only", "isolation"))
case("isolation: a layer imports a higher layer", ARMED, 1, "a layer imports only lower layers",
     armed=True, files=fx("dafny/given/Q/QG_L2_BigNat.dfy", "  import opened QG_L1_BigNat\n",
                          "  import opened QG_L1_BigNat\n  import QG_L3_BigNat\n"),
     args=("--only", "isolation"))
case("isolation: a reference import", ARMED, 1, "reference identifiers start with `solutions`",
     armed=True, files=fx(PC, "  import opened QG_L2_BigNat\n",
                          "  import opened QG_L2_BigNat\n  import SolutionsQ04\n"))
case("isolation: an unknown import", ARMED, 1, "which is neither Std, a given layer", armed=True,
     files=fx(PC, "  import opened QG_L2_BigNat\n", "  import opened QG_L2_BigNat\n  import Helpers\n"))
case("isolation: a nested module may be imported", ARMED, 0, "isolation:", armed=True,
     files=fx(PC, "  const Example := 1\n",
              "  const Example := 1\n  module Inner {\n  }\n  import opened Inner\n"),
     args=("--only", "isolation"))
case("isolation: a module without the prefix (I4a)", ARMED, 1, "module Helpers must be named Q04…",
     armed=True, files={**TREE, PC: TREE[PC] + "\nmodule Helpers {\n}\n"},
     args=("--only", "isolation"))
case("isolation: a declaration outside any module (I4a)", ARMED, 1, "`lemma` outside any module",
     armed=True, files={PC: TREE[PC] + "\nlemma Stray()\n  ensures true\n"}, args=("--only", "isolation"))
case("isolation: an include (I1)", ARMED, 1, "`include` in a course file", armed=True,
     files={PC: 'include "../../../given/Q/QG_L1_BigNat.dfy"\n' + TREE[PC]}, args=("--only", "isolation"))
case("isolation: a given module without its layer prefix", ARMED, 1, "must be named QG_L1_…",
     armed=True, files={"dafny/given/Q/QG_L1_BigNat.dfy": "module BigNatSpec {\n}\n"},
     args=("--only", "isolation"))
case("isolation: a Verus crate above the tier", ARMED, 1, "uses qg_bignat_l4, a layer above", armed=True,
     files=fx(RS, "use qg_bignat_l3::*;\n", "use qg_bignat_l3::*;\nuse qg_bignat_l4::*;\n"),
     args=("--only", "isolation"))
case("isolation: an R crate from a Q crate", ARMED, 1, "uses rg_re_a1, a layer of the other track",
     armed=True, files=fx(RS, "use qg_bignat_l3::*;\n", "use qg_bignat_l3::*;\nuse rg_re_a1::Re;\n"),
     args=("--only", "isolation"))
case("isolation: another module's crate", ARMED, 1, "uses q05_frames, another module's crate",
     armed=True, files=fx(RS, "use qg_bignat_l3::*;\n", "use qg_bignat_l3::*;\nuse q05_frames::x;\n"))
case("isolation: #[path]", ARMED, 1, "#[path = …] reaches files outside", armed=True,
     files=fx(RS, "use qg_bignat_l3::*;\n", 'use qg_bignat_l3::*;\n#[path = "../../x.rs"]\nmod other;\n'),
     args=("--only", "isolation"))
case("isolation: include!", ARMED, 1, "include! reaches files outside", armed=True,
     files=fx(RS, "use qg_bignat_l3::*;\n", 'use qg_bignat_l3::*;\ninclude!("../../x.rs");\n'),
     args=("--only", "isolation"))
case("isolation: a Q harness imports fvh_r", setf("Q06", "imports", f'{{ "{STATS}" = "py-fvh" }}'), 1,
     "imports fvh_r, the other track's package (I2)", files={STATS: "import fvh_r\n"})
case("isolation: sys.path", setf("Q06", "imports", f'{{ "{STATS}" = "py-fvh" }}'), 1,
     "sys.path manipulation", files={STATS: "import sys\nsys.path.insert(0, 'x')\n"})
case("isolation: the other track's bench", ARMED, 1, "names bench/local/r", armed=True,
     files=fx(PC, "  const Example := 1\n", "  const Example := 1 // see bench/local/r/x\n"))
case("isolation: residue — a single-digit Q label", BASE, 1, "'Q4' is a single-digit Q label",
     files={"docs/Q04_ProofCraft.md": "# Q04\n\nSee Q4 first.\n"})
case("isolation: residue — a design-v1 id", BASE, 1, "'F07' is a design-v1 module id",
     files={"docs/Q04_ProofCraft.md": "# Q04\n\nAs in F07.\n"})
case("isolation: residue — an R chapter names Q", BASE, 1, "names Q04, a module of the other track",
     files={"docs/R07_Libraries.md": "# R07\n\nQ04 did this.\n"})
case("isolation: residue — a Recap link is fine", BASE, 0, "isolation:",
     files={"docs/R07_Libraries.md": "# R07\n\nRecap → Q04 (optional).\n"}, args=("--only", "isolation"))
case("isolation: residue — a Q chapter names R", BASE, 1, "names R07, a module of the other track",
     files={"docs/Q04_ProofCraft.md": "# Q04\n\nR07 covers more.\n"})
case("isolation: residue — a Deep dive link is fine", BASE, 0, "isolation:",
     files={"docs/Q04_ProofCraft.md": "# Q04\n\nDeep dive → R07.\n"}, args=("--only", "isolation"))
case("isolation: residue — a mermaid node id", BASE, 1, "mermaid node id 'Q04'",
     files={"docs/Q04_ProofCraft.md": '```mermaid\nflowchart LR\n  Q04 --> b["Q05"]\n```\n'})
case("isolation: residue — quoted mermaid labels", BASE, 0, "isolation:",
     files={"docs/Q04_ProofCraft.md": '```mermaid\nflowchart LR\n  q4["Q04"] -->|"then"| q5["Q05"]\n```\n'},
     args=("--only", "isolation"))
case("isolation: residue — a bank question label", BASE, 1, "bank question label 'P3'",
     files={f"{BANKS}/Q04.md": "# Q04 bank\n\n### P3 — x\n"}, args=("--only", "isolation"))
case("isolation: residue — a rubric line label", BASE, 1, "rubric line label 'E1'",
     files={"paper/rubrics/Q04_rubric.md": "# Q04 rubric\n\n**E1 — x.** y\n"})
# reserved names: guard rule 1 lets solutions_policy / solutions-first through on a
# shell line, so no crate, package or module anywhere in the learner tree carries them
_RES = "solutions_policy and solutions-first are the registry's field and value"
CH20 = "Challenges/Algorithms/Q20_HashMap/q20_hash_map"
case("reserved: a Python module file", BASE, 1,
     f"agents/q31_x/solutions_policy.py: a module file named 'solutions_policy'; {_RES}",
     files={"agents/q31_x/solutions_policy.py": "x = 1\n"}, args=("--only", "isolation"))
case("reserved: a package directory, '-' read as '_'", BASE, 1,
     "tools/Q12/solutions_first: a directory named 'solutions_first'",
     files={"tools/Q12/solutions_first/__init__.py": ""}, args=("--only", "isolation"))
case("reserved: a Python import", BASE, 1, "tools/Q12/run.py:2: Python module 'solutions_policy'",
     files={"tools/Q12/run.py": "import json\nimport solutions_policy.core as p\n"},
     args=("--only", "isolation"))
case("reserved: a from-import", BASE, 1, "tools/Q12/run.py:1: Python module 'solutions_policy'",
     files={"tools/Q12/run.py": "from solutions_policy import x\n"}, args=("--only", "isolation"))
case("reserved: the field read as data is fine", BASE, 0, "no reserved name in",
     files={"tools/Q12/run.py": 'import json\nrec = json.loads(s)\nsolutions_policy = '
            'rec["solutions_policy"]  # solutions-first\n'}, args=("--only", "isolation"))
case("reserved: a doc named for the policy is fine", BASE, 0, "no reserved name in",
     files={"instructor/solutions_policy.md": "# the policy\n"}, args=("--only", "isolation"))
case("reserved: a Dafny module outside the course globs", BASE, 1,
     "Challenges/Algorithms/Q19_Sorting/Q19_Sorting.dfy:2: Dafny module 'solutions_policy'",
     files={"Challenges/Algorithms/Q19_Sorting/Q19_Sorting.dfy":
            "// a challenge file\nmodule solutions_policy {\n}\n"}, args=("--only", "isolation"))
case("reserved: a Dafny import alias", BASE, 1, "Dafny module 'solutions_policy'",
     files={"Challenges/Algorithms/Q19_Sorting/Q19_Sorting.dfy":
            "module Q19_Sorting {\n  import opened solutions_policy = Q19_Spec\n}\n"},
     args=("--only", "isolation"))
case("reserved: a Cargo package name", BASE, 1,
     f"{CH20}/Cargo.toml: package.name names 'solutions-first'",
     files={f"{CH20}/Cargo.toml": '[package]\nname = "solutions-first"\nversion = "0.1.0"\n'},
     args=("--only", "isolation"))
case("reserved: a Cargo dependency", BASE, 1,
     f"{CH20}/Cargo.toml: dependencies names 'solutions_policy'",
     files={f"{CH20}/Cargo.toml": '[package]\nname = "q20_hash_map"\n\n[dependencies]\n'
            'solutions_policy = { path = "../x" }\n'}, args=("--only", "isolation"))
case("reserved: a renamed Cargo dependency", BASE, 1,
     f"{CH20}/Cargo.toml: dependencies.p.package names 'solutions_policy'",
     files={f"{CH20}/Cargo.toml": '[package]\nname = "q20_hash_map"\n\n[dependencies]\n'
            'p = { package = "solutions_policy", path = "../x" }\n'}, args=("--only", "isolation"))
case("reserved: a Rust module and crate path", BASE, 1,
     f"{CH20}/src/lib.rs:2: Rust crate or module 'solutions_first'",
     files={f"{CH20}/src/lib.rs": "use vstd::prelude::*;\nuse solutions_first::x;\n"},
     args=("--only", "isolation"))
case("reserved: a pyproject name", BASE, 1,
     "harness/pyproject.toml: project.name names 'solutions-policy'",
     files={"harness/pyproject.toml": '[project]\nname = "solutions-policy"\n'},
     args=("--only", "isolation"))
case("reserved: the walk never enters a reference tree", BASE, 0, "no reserved name in",
     files={"Solutions/harness/solutions_policy.py": "", "paper/solutions/solutions_policy.py": ""},
     args=("--only", "isolation"))
case("reserved: the full run reports the walk", BASE, 1,
     "agents/q31_x/solutions_policy.py: a module file named",
     files={"agents/q31_x/solutions_policy.py": ""})

# --- items (--items and the coverage group) ---------------------------------------------------------------
case("--items on the armed module", ARMED, 0, '"id": "Q04.X2d"', armed=True, args=("--items", "Q04", "--json"))
case("--items reports a pair", ARMED, 0, '"pair": "Q04.H1v"', armed=True, args=("--items", "Q04", "--json"))
case("--items reads specimens", ARMED, 0, f'"file": "{SPEC}"', armed=True, args=("--items", "Q04", "--json"))
case("--items: an unfilled verdict", ARMED, 0, '"file": "slots/Q04.slots", "line": 2, "state": "unfilled"',
     armed=True, args=("--items", "Q04", "--json"))
case("--items: a filled verdict", ARMED, 0, '"file": "slots/Q04.slots", "line": 2, "state": "filled-disabled"',
     armed=True, args=("--items", "Q04", "--json"), files=fx(SLOTS, "P1dv = ???", 'P1dv = "D:fail V:ok[a]"'))
case("--items: an enabled verdict", ARMED, 0, '"line": 2, "state": "enabled"', armed=True,
     args=("--items", "Q04", "--json"),
     files={**fx(SLOTS, "P1dv = ???", 'P1dv = "D:ok V:ok"'), **fx(PC, "// SLOT: CHECK P1dv", "// CHECK P1dv")})
case("--items: an enabled obligation", ARMED, 0, "enabled@3", armed=True, args=("--items", "Q04"),
     files=fx(SPEC, "// SLOT: FAILS ???", "// FAILS a"))
case("--items on a planned module", BASE, 0, "[]", args=("--items", "Q05", "--json"))
case("--items on an unknown id", BASE, 3, "unknown module id", args=("--items", "Q99"))
case("--items: a malformed marker", ARMED, 1, "malformed item marker", armed=True,
     args=("--items", "Q04"), files=fx(PC, "// item: Q04.H1d S3", "// item: Q04.H01d S3"))
case("items: no language suffix", ARMED, 1, "malformed item marker", armed=True,
     files=fx(PC, "// item: Q04.H1d S3", "// item: Q04.H1 S3"))
case("items: another module's id", ARMED, 1, "item Q05.A1d in a Q04 file", armed=True,
     files=fx("dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy", "Q04.A1d", "Q05.A1d"))
case("items: a duplicate id", ARMED, 1, "duplicate item id Q04.H2v", armed=True,
     files=fx(RS, "// item: Q04.H1v S3", "// item: Q04.H2v S3"))
case("items: a strand outside the module", ARMED, 1, "is in S9, not one of Q04's strands", armed=True,
     files=fx(LIB, "// item: Q04.T1dv S5", "// item: Q04.T1dv S9"))
case("items: a Q item without a strand", ARMED, 1, "needs its strand", armed=True,
     files=fx(LIB, "// item: Q04.T1dv S5", "// item: Q04.T1dv"))
case("items: a Verus item in a Dafny file", ARMED, 1, "is a v item in a Dafny file", armed=True,
     files=fx(LIB, "// item: Q04.T1dv S5", "// item: Q04.T1v S5"))
case("items: a P item without a format", ARMED, 1, "P item Q04.P2dv needs a format", armed=True,
     files=fx(RS, "// item: Q04.P2dv S2 verdict", "// item: Q04.P2dv S2"))
case("items: an H item with a format", ARMED, 1, "H item Q04.H2v carries no format", armed=True,
     files=fx(RS, "// item: Q04.H2v S4", "// item: Q04.H2v S4 value"))
case("items: a card without a slug", ARMED, 1, "needs write:<slug>, recognise:<slug> or diverge:<slug>",
     armed=True, files=fx(PC, "// item: Q04.C1dv S3 write:calc", "// item: Q04.C1dv S3"))
case("items: an exit with a value format", ARMED, 1, "may carry only the verdict format", armed=True,
     files=fx(EXIT, "// item: Q04.X1d S4", "// item: Q04.X1d S4 value"))
case("items: min= off an exit", ARMED, 1, "min= is for multi-slot X items only", armed=True,
     files=fx(LIB, "// item: Q04.T1dv S5", "// item: Q04.T1dv S5 min=1"))
case("items: min= above the slots", ARMED, 1, "has min=2 but 0 slot(s)", armed=True,
     files=fx(EXIT, "// item: Q04.X1d S4", "// item: Q04.X1d S4 min=2"))
case("items: uses outside a block", ARMED, 1, "`// uses:` outside an item block", armed=True,
     files=fx(PC, "  import opened QG_L1_BigNat\n", "  // uses: calc\n  import opened QG_L1_BigNat\n"))
case("items: uses away from its marker", ARMED, 1, "must directly follow its item marker", armed=True,
     files=fx(PC, "  lemma H1(x: nat)\n", "  lemma H1(x: nat)\n  // uses: calc\n"))
case("items: uses on a P item", ARMED, 1, "`// uses:` on a P item", armed=True,
     files=fx(RS, "// item: Q04.P2dv S2 verdict\n", "// item: Q04.P2dv S2 verdict\n// uses: calc\n"))
case("items: need on an H item", ARMED, 1, "only X items carry need:", armed=True,
     files=fx(LIB, "  // uses: calc\n", "  // uses: calc\n  // need: lemma H2\n"))
case("items: a pair across kinds", ARMED, 1, "a pair shares module, kind and number", armed=True,
     files=fx(PC, "// pair: Q04.H1v", "// pair: Q04.X1v"))
case("items: a pair within one language", ARMED, 1, "`pair:` joins a d item and a v item", armed=True,
     files=fx(PC, "// pair: Q04.H1v", "// pair: Q04.H1d"))
case("items: a pair that does not pair back", ARMED, 1, "but Q04.H1v does not pair back", armed=True,
     files=fx(RS, "// pair: Q04.H1d\n", ""))
case("items: a pair with no partner", ARMED, 1, "pairs with Q04.H1v, which no marker declares",
     armed=True, files={**fx(RS, "// item: Q04.H1v S3\n// uses: calc\n// pair: Q04.H1d\n",
                             "// item: Q04.H3v S3\n// uses: calc\n"),
                        **fx(PC, "  // uses: calc, lemma-call\n", "  // uses: calc, lemma-call\n")})
case("items: a card slug outside the lists", ARMED, 1, "'induction' is not in Q04's write_d", armed=True,
     files=fx(PC, "// item: Q04.C1dv S3 write:calc", "// item: Q04.C1dv S3 write:induction"))
case("items: a recognise card", ARMED, 1, "'forall' is not in Q04's recognise_v", armed=True,
     files=fx(PC, "// item: Q04.C1dv S3 write:calc", "// item: Q04.C1dv S3 recognise:forall"))
case("items: a SLOT outside a block", ARMED, 1, "`// SLOT:` outside an item block", armed=True,
     files=fx(PC, "  import opened QG_L1_BigNat\n", "  // SLOT: ???\n  import opened QG_L1_BigNat\n"))
case("items: a slot line for no verdict", ARMED, 1, "slot P9dv names no verdict item", armed=True,
     files={SLOTS: TREE[SLOTS] + "P9dv = ???\n"})
case("items: a malformed slot line", ARMED, 1, "malformed slot line", armed=True,
     files={SLOTS: TREE[SLOTS] + "P1dv: yes\n"})
case("items: a marker in a block comment is no marker", ARMED, 0, "course map OK", armed=True,
     files=fx(PC, "  const Example := 1\n", "  const Example := 1\n  /* // item: Q04.H9d S1 */\n"))

# --- coverage: D4, uses, parity, admissible (armed) --------------------------------------------------------------
case("D4: a cited item that does not exist",
     edit("Q04", '"S1.limbs" = ["Q04.P1dv"]', '"S1.limbs" = ["Q04.P1dv", "Q04.P9dv"]', ARMED), 1,
     "cites Q04.P9dv, but no item marker", armed=True)
case("D4: an orphan checked item", ARMED, 1, "Q04.H3d is cited by no concept_items key", armed=True,
     files=fx(LIB, "  // item: Q04.T1dv S5\n", "  // item: Q04.H3d S5\n  lemma H3() ensures true\n\n  // item: Q04.T1dv S5\n"))
case("D4: an uncited agent item is fine", ARMED, 0, "course map OK", armed=True,
     files=fx("dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy", "  const Agent := 1\n",
              "  const Agent := 1\n  // item: Q04.A2d S5\n  const Agent2 := 2\n"))
case("D4: a strand with no key", edit("Q04", '"S2.specs" = ["Q04.P2dv"]\n', "", ARMED), 1,
     "strand S2 has no concept_items key", armed=True, args=("--only", "coverage"))
case("uses: a WRITE construct tagged once", ARMED, 1,
     "Q04: Verus WRITE 'calc' has 1 tagged item (need ≥ 2 `uses:` in Verus): Q04.H1v", armed=True,
     files=fx(EXIT_RS, "// item: Q04.X1v S4\n// uses: calc\n", "// item: Q04.X1v S4\n"))
case("uses: an unseen construct", ARMED, 1, "uses 'fuel', which no Q module up to Q04 lists",
     armed=True, files=fx(LIB, "  // uses: calc\n", "  // uses: calc, fuel\n"))
case("uses: a construct WRITE in the other language only", ARMED, 1,
     "uses 'frame', which no Q module up to Q04 lists as Verus", armed=True,
     files=fx(RS, "// item: Q04.H2v S4\n// uses: lemma-call\n", "// item: Q04.H2v S4\n// uses: lemma-call, frame\n"))
case("parity: fewer than two cross-language predicts", ARMED, 1, "1 cross-language (dv) predict(s)",
     armed=True, files=fx(RS, "// item: Q04.P2dv S2 verdict", "// item: Q04.P2v S2 verdict"))
case("parity: an exit floor per language", ARMED, 1, "1 Verus exit item(s); the tier's exit needs ≥ 2",
     armed=True, files=fx(EXIT_RS, "// item: Q04.X2v S5\n// uses: lemma-call\n", "// item: Q04.T2v S5\n// uses: lemma-call\n"))
case("admissible: a key naming no item",
     edit("Q04", "admissible = {}", 'admissible = { "Q04.H7d" = { admitted = true, minutes = 10, fallback = "" } }', ARMED),
     1, "admissible: 'Q04.H7d' names no item marker", armed=True)
# A practice module with exits and no agentic or harness files, armed in the
# case text only (Q10 until DV5a; Q13 is planned until DV5b).
_q13 = setf("Q13", "status", '"authoring"', setf("Q13", "imports",
            '{ "dafny/Q/Q13_PracticeIIA/std/Q13_PracticeIIA.dfy" = "std", "verus/q/q13_practice_iia/src/lib.rs" = "prelude", '
            '"dafny/Q/Q13_PracticeIIA/exit/Q13_Exit.dfy" = "core", "verus/q/q13_practice_iia/src/exit.rs" = "prelude" }'))
case("admissible: a practice hole without an entry", _q13, 1, "Q13.H1d has no admissible entry",
     files={"dafny/Q/Q13_PracticeIIA/std/Q13_PracticeIIA.dfy": "module Q13_PracticeIIA {\n  // item: Q13.H1d S1\n  lemma H1() ensures true\n}\n"},
     args=("--only", "coverage"))

# --- coverage: the rows -------------------------------------------------------------------------------------------
case("rows: a missing field", cov_edit("S5.import-tiers", 'gap = ""', ""), 1,
     "fields must be exactly, in order")
case("rows: an unknown field", cov_edit("S5.import-tiers", 'gap = ""', 'gap = ""\nnote = "x"'), 1,
     "fields must be exactly, in order")
case("rows: a malformed payload id", cov_edit("S5.import-tiers", '"S5.import-tiers"', '"imports"'), 1,
     "is not a payload id")
case("rows: a duplicate payload id", cov_edit("S5.toolchain-mismatch-lab", '"S5.toolchain-mismatch-lab"',
                                              '"S5.import-tiers"'), 1, "S5.import-tiers has more than one row")
case("rows: langs out of order", cov_edit("S5.import-tiers", 'langs = ["d", "v"]', 'langs = ["v", "d"]'), 1,
     "langs must be distinct d, v, py in that order")
case("rows: a challenge home", cov_edit("S5.import-tiers", '"Q04.S5"', '"Q20.S5"'), 1,
     "a challenge is deepening, never a home")
case("rows: a strand the module does not sweep", cov_edit("S5.import-tiers", '"Q04.S5"', '"Q05.S5"'), 1,
     "names S5, which Q05 does not sweep")
case("rows: deepening that is no challenge", cov_edit("S1.datatypes-and-pattern-matching", '"Q19"', '"Q09"'),
     1, "deepening 'Q09' must be a bare Q19–Q33 id")
case("rows: no Q home", cov_edit("S5.import-tiers", 'q_homes = ["Q04.S5"]', "q_homes = []"), 1,
     "no Q home")
case("rows: no R home", cov_edit("S5.import-tiers", 'r_homes = ["R07"]', "r_homes = []"), 1, "no R home")
case("rows: a malformed R home", cov_edit("S5.import-tiers", '"R07"', '"R17"'), 1,
     "is not an R module anchor")
case("rows: a language with no home", cov_edit("S5.import-tiers", 'langs = ["d", "v"]', 'langs = ["d", "v", "py"]'),
     1, "no Q home covers Python")
case("rows: a paper home is language-free", cov_edit("S5.import-tiers", '"Q04.S5"', '"Q04.B1"'), 1,
     "no Q home covers Dafny")
case("rows: a paper home in a planned module is pending",
     cov_edit(PLANNED_ROW, f'"{PLANNED_HOME}"',
              f'"{PLANNED_HOME}", "{PLANNED}.B1"'), 0, "pending)")
# Pin the synthetic subject to planned; actual R07 may already be authored.
case("rows: an item home in a planned module is pending",
     setf("R07", "status", '"planned"',
          cov_edit("S5.import-tiers", '"R07"', '"R07.H1dv"')),
     0, "pending)", args=("--only", "coverage"))
case("rows: an armed strand home resolves", ARMED, 0, f"coverage: {1 + len(REAL_ARMED)} module(s) past planned", armed=True,
     args=("--only", "coverage"))
case("rows: an armed item home that does not resolve", cov_edit("S5.import-tiers", '"Q04.S5"', '"Q04.H9d"', ARMED),
     1, "does not resolve — no item marker Q04.H9d", armed=True)
case("rows: an armed item home of one language", cov_edit("S5.import-tiers", '"Q04.S5"', '"Q04.H1d"', ARMED),
     1, "no Q home covers Verus", armed=True)
case("rows: a gated item home needs a gap",
     cov_edit("S5.import-tiers", '"Q04.S5"', '"Q04.H1d", "Q04.H1v"',
              edit("Q04", "admissible = {}",
                   'admissible = { "Q04.H1d" = { admitted = false, minutes = 0, fallback = "on paper" } }', ARMED)),
     1, "is a gated item (admitted = false)", armed=True)

# --- vocabulary -------------------------------------------------------------------------------------------------------
VOCAB = (ROOT / CONCEPTS).read_text(encoding="utf-8")
ROW = "| `statistics` | | pass@k"
case("vocab: concepts.md is required", BASE, 1, "concepts.md: not found", files={CONCEPTS: None})
case("vocab: a tag that is not kebab-case", BASE, 1, "tag 'NewTag' is not kebab-case",
     files={CONCEPTS: sub(VOCAB, ROW, "| `NewTag` | | x | Q04 |\n" + ROW)})
case("vocab: a tag listed twice", BASE, 1, "tag 'statistics' is listed twice",
     files={CONCEPTS: sub(VOCAB, ROW, "| `statistics` | | x | Q04 |\n" + ROW)})
case("vocab: an alias that is also a tag", BASE, 1, "alias 'variance' is also a tag",
     files={CONCEPTS: sub(VOCAB, "| `statistics` | |", "| `statistics` | `variance` |")})
case("vocab: an alias listed twice", BASE, 1, "alias 'frame' is listed twice",
     files={CONCEPTS: sub(VOCAB, "| `statistics` | |", "| `statistics` | `frame` |")})
case("vocab: a malformed row", BASE, 1, "a row's first cell is one `tag`",
     files={CONCEPTS: sub(VOCAB, ROW, "| statistics-x | | x | Q04 |\n" + ROW)})
BANK = ("# Q04 bank\n\n## Controlled tag vocabulary\n\n| tag | covers |\n|---|---|\n| `{tag}` | x |\n\n"
        "## Questions\n\n### K1 [why] — x\n**viva:** no · **strand:** {strand} · **tags:** `{tag}`\n")
case("vocab: a bank tag missing from concepts.md", BASE, 1, "tag 'horner' is not in",
     files={f"{BANKS}/Q04.md": BANK.format(tag="horner", strand="S4")}, args=("--only", "vocab"))
case("vocab: a bank tag through an alias", setf("Q04", "status", '"authoring"'), 0, f"{1 + REAL_BANKS} bank vocabularies",
     files={f"{BANKS}/Q04.md": BANK.format(tag="loop-invariants", strand="S4")}, args=("--only", "vocab"))
case("vocab: a Q bank strand outside its module", BASE, 1, "strand S9 is not one of Q04's strands",
     files={f"{BANKS}/Q04.md": BANK.format(tag="loop-invariant", strand="S9")}, args=("--only", "vocab"))
case("vocab: a bank without a vocabulary", BASE, 1, "no `## Controlled tag vocabulary` section",
     files={f"{BANKS}/Q04.md": "# Q04 bank\n"}, args=("--only", "vocab"))
case("vocab: an unknown ledger tag", BASE, 1, "'not-a-tag' is not in", ledger="- tag: Q04/not-a-tag | error: x\n")
case("vocab: a ledger tag outside its bank", BASE, 1, "is not in Q04's bank vocabulary",
     files={f"{BANKS}/Q04.md": BANK.format(tag="loop-invariant", strand="S4")},
     ledger="- tag: Q04/statistics | error: x\n")
case("vocab: a ledger alias inside its bank", setf("Q04", "status", '"authoring"'), 0, "1 tag(s), all known",
     files={f"{BANKS}/Q04.md": BANK.format(tag="loop-invariant", strand="S4")},
     ledger="- tag: Q04/loop-invariants | error: x\n")
_shipped = setf("Q04", "status", '"shipped"', ARMED)
SHIP_FILES = {"docs/Q04_ProofCraft.md": "# Q04\n", "paper/rubrics/Q04_rubric.md": "# Q04 rubric\n",
              "paper/Q04_problems.tex": "", "paper/Q04_answers.tex": "",
              f"{BANKS}/Q04.md": BANK.format(tag="loop-invariant", strand="S4")}
case("vocab: a shipped module's bank holds its questions", _shipped, 1,
     "1 bank question(s) (K<n>); a shipped Q04 needs ≥ 8", armed=True, files=SHIP_FILES)
case("vocab: a shipped tier viva needs its tier's banks", setf("Q06", "status", '"shipped"'), 1,
     "the tier viva draws from Q04–Q06, but Q04's bank", args=("--only", "vocab"),
     files={f"{BANKS}/Q04.md": None})  # the real Q04 bank exists since DV3k


# --- in-process cases: the parser and the generator ---------------------------------------------------------------
def _parse(rel, text, slots=None):
    return ci.parse_items(rel, text, slots)


def t_r_item_strand():
    items, errs = _parse("x.rs", "verus! {\n// item: R04.H1v S2\n}\n")
    return None if any("carries a strand" in e for e in errs) else f"errors: {errs}"


def t_r_item_ok():
    items, errs = _parse("x.dfy", "module R04 {\n  // item: R04.H1d\n  lemma L() ensures true\n}\n")
    return None if not errs and items and items[0]["strand"] is None else f"{items} {errs}"


def t_python_items():
    text = ("# item: Q06.H1py S13\ndef f():\n    pass\n\n# item: Q06.P1py S13 value\n"
            "def test_p1():\n    # SLOT: assert f() == ???\n    assert f() is None\n")
    items, errs = _parse("x.py", text)
    states = [s["state"] for it in items for s in it["slots"]]
    return None if not errs and [i["id"] for i in items] == ["Q06.H1py", "Q06.P1py"] \
        and states == ["unfilled", "enabled"] else f"{items} {errs}"


def t_block_extent():
    text = ("module Q04_X {\n  // item: Q04.H1d S1\n  lemma A()\n    ensures true\n  {\n  }\n}\n"
            "// trailing comment\n")
    items, errs = _parse("x.dfy", text)
    return None if not errs and items[0]["line_end"] == 6 else f"{items} {errs}"


def t_verus_block_extent():
    text = ("verus! {\n// item: Q04.H1v S1\nproof fn a()\n{\n}\n\n// after\n} // verus!\nfn tail() {}\n")
    items, errs = _parse("x.rs", text)
    return None if not errs and items[0]["line_end"] == 7 else f"{items} {errs}"


def t_strings_and_chars():
    text = ('verus! {\n// item: Q04.H1v S1\nfn a() { let s = "}}"; let c = \'}\'; let r = r#"}"#; }\n'
            "// did: nothing to close\n}\n")
    items, errs = _parse("x.rs", text)
    return None if not errs and items[0]["line_end"] == 4 and items[0]["did"] == ["nothing to close"] \
        else f"{items} {errs}"


def t_prose_not_markers():
    text = "module Q04_X {\n  // item 3 of the list is long\n  // need to show this\n}\n"
    items, errs = _parse("x.dfy", text)
    return None if not errs and not items else f"{items} {errs}"


def t_value_slots():
    text = ("module Q04_C {\n  // item: Q04.P2d S1 value\n  method {:test} P2() {\n"
            "    // SLOT: expect F(1) == ???;\n    // SLOT: expect F(2) == 3;\n    expect F(3) == 4;\n  }\n}\n")
    items, errs = _parse("x.dfy", text)
    states = [s["state"] for s in items[0]["slots"]]
    return None if not errs and states == ["unfilled", "filled-disabled", "enabled"] else f"{items} {errs}"


def t_options_override():
    opts, errs = gu.load_options(ROOT)
    if errs:
        return f"options errors: {errs}"
    q02, q03 = gu.unit_options(opts, "core", "Q02"), gu.unit_options(opts, "core", "Q03")
    r05 = gu.unit_options(opts, "std", "R05")
    ok = ("manual-lemma-induction" not in q02 and q03.get("manual-lemma-induction") is True
          and r05.get("standard-libraries") is True and r05.get("resource-limit") == 5000000)
    return None if ok else f"Q02 {q02} Q03 {q03} R05 {r05}"


def t_workspace_render():
    ws = gu.render_workspace(["given/qg_bignat_l1", "q/q01_hello", "given/rg_re_a1", "r/r02_datatypes"],
                             ["given/qg_bignat_l1", "q/q01_hello"])
    return None if 'default-members = ["given/qg_bignat_l1", "q/q01_hello"]' in ws and "[patch" not in ws \
        else ws


def t_crate_render():
    c = gu.render_crate("R10", "r10_type_invariants", "A4")
    want = ['rg_re_a1 = { path = "../../given/rg_re_a1" }', 'rg_re_a4 = { path = "../../given/rg_re_a4" }',
            "build = false", 'vstd = "=0.0.0-2026-09-20-0158"']
    return None if all(w in c for w in want) and "rg_re_a5" not in c else c


def t_r16_trust_report_listed():
    import tomllib
    import check_course_map as ccm
    base = next(x for x in tomllib.loads(BASE)["module"] if x["id"] == "R16")
    for extra in ("verus/r/r16_capstone/src/trust_report.rs", "harness/r/fvh_r/trust-report.py",
                  "dafny/R/R16_Capstone/std/R16_trust_report.dfy"):
        key = "harness" if extra.startswith("harness/") else "exercises"
        m = {**base, "status": "authoring", key: base[key] + [extra]}
        if key == "harness":
            m["langs"] = ["d", "v", "py"]
        bad = [e for e in ccm.check_langs_and_paths(m) if "trust-report" in e or "langs" in e]
        if bad:
            return f"{extra}: {bad}"
    return None


def t_trust_report_pattern():
    """TRUST_REPORT names the R trees as spelled (dafny/R/, verus/r/, harness/r/),
    as the guard's rule-2s pattern must."""
    import check_course_map as ccm
    hit = ["dafny/R/R16_Capstone/std/R16_trust_report.dfy", "verus/r/r16_capstone/src/trust_report.rs",
           "harness/r/fvh_r/trust-report.py", "verus/r/r16_capstone/src/report/trust_report/mod.rs"]
    miss = ["dafny/Q/Q18_Capstone/std/Q18_trust_report.dfy", "verus/q/q18_x/src/trust_report.rs",
            "harness/q/fvh_q/trust_report.py", "dafny/R/R16_Capstone/std/R16_Trust.dfy",
            "docs/R16_trust_report.md"]
    bad = [p for p in hit if not ccm.TRUST_REPORT.match(p)] + [p for p in miss if ccm.TRUST_REPORT.match(p)]
    return f"misclassified: {bad}" if bad else None


def t_q_gate_pattern():
    """Q_GATE is the guard's rule-2s gate pattern: Q's harness only (R's gate is Rust)."""
    import check_course_map as ccm
    hit = ["harness/q/fvh_q/gate/check.py", "harness/q/fvh_q/gate.py", "harness/q/fvh_q/gate"]
    miss = ["harness/r/fvh_r/gate/check.py", "harness/r/fvh_r/gate.py", "harness/q/fvh_q/delegate.py",
            "harness/q/fvh_q/gates.py", "harness/q/fvh_q/q18_gate.py"]
    bad = [p for p in hit if not ccm.Q_GATE.match(p)] + [p for p in miss if ccm.Q_GATE.match(p)]
    return f"misclassified: {bad}" if bad else None


def t_reserved_walk_symlinks():
    """The reserved-name walk lists names but never reads or enters a reference
    tree, nor follows a symlink out of the learner tree."""
    import check_course_map as ccm
    root = Path(tempfile.mkdtemp(prefix="course-map-walk-"))
    try:
        for rel, text in (("Solutions/harness/solutions_policy.py", "import solutions_policy\n"),
                          ("paper/solutions/x.py", "import solutions_policy\n"),
                          ("tools/Q12/own.py", "import solutions_policy\n")):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8")
        os.symlink(root / "Solutions/harness/solutions_policy.py", root / "tools/Q12/link.py")
        os.symlink(root / "Solutions", root / "tools/ref")
        errs, _ = ccm.check_reserved_names(root)
        want = ["tools/Q12/own.py:1: Python module 'solutions_policy'"]
        got = [e.split(";")[0] for e in errs]
        return None if got == want else f"got {got}"
    finally:
        shutil.rmtree(root)


def t_derive_units():
    got = gu.derive_units(["verus/q/q04_proof_craft/src/lib.rs", "dafny/Q/Q04_ProofCraft/std/A.dfy",
                           "specimens/Q04/", "dafny/Q/Q04_ProofCraft/core/B.dfy",
                           "dafny/Q/Q04_ProofCraft/std/C.dfy"])
    want = ["dafny/Q/Q04_ProofCraft/core", "dafny/Q/Q04_ProofCraft/std", "verus/q/q04_proof_craft"]
    return None if got == want else f"{got}"


for _name, _fn in (("parser: an R item carries no strand", t_r_item_strand),
                   ("parser: an R item without a strand", t_r_item_ok),
                   ("parser: Python items and slots", t_python_items),
                   ("parser: a block ends where its module closes", t_block_extent),
                   ("parser: a Verus block ends at the verus! brace", t_verus_block_extent),
                   ("parser: braces in strings and chars; did: receipts", t_strings_and_chars),
                   ("parser: prose comments are not markers", t_prose_not_markers),
                   ("parser: value slot states", t_value_slots),
                   ("generator: tier options and the Q03 override (Δ45)", t_options_override),
                   ("generator: default-members are the Q crates (Δ23)", t_workspace_render),
                   ("generator: an R crate depends on its chain (Δ22)", t_crate_render),
                   ("generator: units derive from exercises", t_derive_units),
                   ("registry: R16 past planned with its trust-report listed", t_r16_trust_report_listed),
                   ("registry: the trust-report pattern spells the R trees", t_trust_report_pattern),
                   ("registry: the gate pattern is Q's only", t_q_gate_pattern),
                   ("isolation: the reserved-name walk skips reference trees and symlinks",
                    t_reserved_walk_symlinks)):
    unit(_name, _fn)


# --- the runner ---------------------------------------------------------------------------------------------------
def materialize(root, rel):
    """Make every directory on rel's way a real directory in the case root (its
    entries symlinked to the checkout's), so one file there can be replaced
    without ever writing through a symlink into the checkout."""
    parts = PurePosixPath(rel).parts
    here, real = root, ROOT
    for part in parts[:-1]:
        here, real = here / part, real / part
        if here.is_symlink():
            here.unlink()
            here.mkdir()
            if real.is_dir():
                for child in real.iterdir():
                    os.symlink(child, here / child.name)
        elif not here.exists():
            here.mkdir()
    return here / parts[-1]


def overlay(root, files):
    for rel, content in files.items():
        target = materialize(root, rel)
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)
        if content is not None:
            target.write_text(content, encoding="utf-8")


# The real Q04's own files: an armed case's synthetic Q04 replaces the real
# record, so they must not sit in its root (DV3a armed the real Q04).
REAL_Q04 = ("dafny/Q/Q04_ProofCraft", "dafny/checks/Q04_checks.dfy", "verus/q/q04_proof_craft",
            "specimens/Q04", "slots/Q04.slots", ".claude/skills/instructor/banks/Q04.md")
REAL_LATER_FILES = tuple(p for mid in REAL_LATER for p in module_trees(mid))


def run_case(text, files, args, armed, ledger, decoys, script, after):
    root = Path(tempfile.mkdtemp(prefix="course-map-"))
    try:
        for name in LINKED:
            if (ROOT / name).exists():
                os.symlink(ROOT / name, root / name)
        for name in COPIED:
            if (ROOT / name).is_dir():
                shutil.copytree(ROOT / name, root / name, symlinks=True)
        (root / "MODULES.toml").write_text(text, encoding="utf-8")
        if ledger is not None:
            overlay(root, {"instructor/ledger.md": ledger})
        for d in decoys:
            overlay(root, {d: ""})
        if armed:
            overlay(root, {rel: None for rel in REAL_Q04 + REAL_LATER_FILES
                           if (ROOT / rel).exists()})
            overlay(root, TREE)
        overlay(root, files)
        if armed:
            # a case may plant a file the generator objects to; the checker reports it
            subprocess.run([sys.executable, str(GEN), "--root", str(root)],
                           capture_output=True, text=True, env=ENV)
        overlay(root, after)
        if script == "cat":
            path = root / args[0]
            return (0, path.read_text(encoding="utf-8")) if path.is_file() else (1, "no such file")
        cmd = [sys.executable, str(GEN if script == "gen" else CHECKER), "--root", str(root), *args]
        p = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
        return p.returncode, p.stdout + p.stderr
    finally:
        shutil.rmtree(root)


def main():
    verbose = sys.argv[1:] == ["-v"]
    if sys.argv[1:] not in ([], ["-v"]):
        print("usage: test_course_map.py [-v]", file=sys.stderr)
        return 2
    failed = 0
    for c in CASES:
        if len(c) == 2:
            name, fn = c
            try:
                msg = fn()
            except Exception as e:  # a crash is a failure, reported
                msg = f"raised {type(e).__name__}: {e}"
            if msg is None:
                if verbose:
                    print(f"  ok    {name}")
                continue
            failed += 1
            print(f"  FAIL  {name}: {msg}")
            continue
        name, text, want, line, files, args, armed, ledger, decoys, script, after = c
        got, out = run_case(text, files, args, armed, ledger, decoys, script, after)
        if got == want and line in out:
            if verbose:
                print(f"  ok    {name}")
            continue
        failed += 1
        print(f"  FAIL  {name}: exit {got}, want {want} with {line!r}")
        print("".join(f"          {l}\n" for l in out.splitlines()[:40]), end="")
    print(f"\ntest_course_map: {len(CASES) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
