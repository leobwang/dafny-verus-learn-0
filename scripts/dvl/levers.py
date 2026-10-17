"""dvl.levers: the lab gate's lever check (QPLAN §30 Q63; PLAN §4.3, Lab α's
validity rule; QPLAN §22.6, Lab 1's).

A lab task enters a stratum only when its task form fails in its shipped
configuration; a delivery must not switch automation back on. This check
compares the verification levers of a delivery with those of the task form it
was made from and refuses any difference: a lever the task form does not ship
(added) and a shipped lever that is gone (removed: dropping a shipped
`{:induction false}` turns automatic induction back on). It is static (no tool
runs) and separate from the learner gate: the learner files may carry
`{:induction}` and the other allowed levers (dvl.dafny.ALLOWED_CURLY), so the
refusal is lab-mode only. `scripts/specfreeze --lab <task> <delivery>`
prints it beside the statement freeze; `scripts/vcheck --gate --lab-task
<task> <delivery>` adds it to the gate; fvh calls lever_findings directly.

Levers:
  Dafny  the attributes in DAFNY_LEVERS (curly `{:name …}`) and DAFNY_AT_LEVERS
         (`@Name(…)`): automatic induction and its triggers, fuel, assertion
         isolation and VC splitting, the nonlinear-arithmetic switch, and the
         resource, time, option and verification switches (the gate's lint
         refuses the last group anyway; here they count as levers too), on a
         declaration, a module or a statement.
  Verus  every `#[verifier::…]` / `#[verifier(…)]` attribute and every crate
         attribute `#![verifier::…]`, except the label `proof_note` and
         triggers (`#[trigger]`, `#[verifier::trigger]`): rlimit,
         spinoff_prover, loop_isolation, nonlinear, integer_ring, bit_vector,
         opaque, external_body and the rest. Proof steps written as code
         (`by (nonlinear_arith)`, `broadcast use`, `reveal`) are proof, not
         levers.
  Both   for a directory pair (a crate, a Dafny project), every project file
         (Cargo.toml, dfyconfig.toml, .cargo/, build.rs, rust-toolchain) must be
         byte-identical: options live there (lab-project-changed).

Removing a shipped trust escape (REMOVABLE: the Verus exec hole's
`external_body`, Dafny's `{:axiom}`, `{:extern}`, `{:verify …}`, `{:only}`)
only strengthens a delivery and is no finding; adding one is.

Each lever is keyed by its scope (the innermost declaration holding it: a
Dafny qualified name, a Verus item symbol; `(file)` outside every
declaration) and its normalized text, and the two multisets are compared.
Findings (dvl.common.Finding, path = the delivery's file):
  lab-lever-added     a lever the task form does not ship at that scope
  lab-lever-removed   a lever the task form ships that the delivery dropped
  lab-file-added      a delivery source file with no task counterpart that
                      carries a lever (a file without levers is no finding)
  lab-project-changed a project file differs or is missing
The message names the scope and the lever, never other code.

Practice mode (`specfreeze --check` and `--against`). A learner or
contractor file may add levers, but the levers that switch automation OFF
(OFF_LEVERS: the nonlinear-arithmetic switch, `{:induction false}`) are part of
the task it ships: deleting `{:disableNonlinearArithmetic}` from a module line
turns a library-step proof into a solver one. off_levers lists them;
specfreeze pins them per file (`frozen_levers`) and reports one that is gone as
`freeze-lever-removed`.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from . import common
from . import dafny as D
from . import verus_spec as vs

Finding = common.Finding

DAFNY_LEVERS = {"induction", "inductionTrigger", "fuel", "isolate_assertions", "isolate",
                "split_here", "focus", "vcs_split_on_every_assert", "vcs_max_cost",
                "vcs_max_keep_going_splits", "vcs_max_splits", "disableNonlinearArithmetic",
                "resource_limit", "rlimit", "timeLimit", "timeLimitMultiplier", "options",
                "verify", "only", "axiom", "extern", "autocontracts", "autoReq"}
DAFNY_AT_LEVERS = {"Induction", "InductionTrigger", "Fuel", "IsolateAssertions",
                   "VcsSplitOnEveryAssert", "DisableNonlinearArithmetic", "ResourceLimit",
                   "TimeLimit", "TimeLimitMultiplier", "Options", "VerifyOnly", "Axiom",
                   "Extern", "AutoContracts"}
VERUS_NON_LEVERS = ("proof_note", "trigger")
# Trust escapes a hole form ships and a delivery removes (the Verus exec hole is
# `#[verifier::external_body]` over `unimplemented!()`, QPLAN §0): removing one
# only strengthens the delivery, so it is no finding. Adding one is.
REMOVABLE = ("{:axiom", "{:extern", "{:verify", "{:only", "@Axiom", "@Extern", "@VerifyOnly",
             "#[verifier::external_body]", "#[verifier(external_body)]")
PROJECT_FILES = ("Cargo.toml", "Cargo.lock", "dfyconfig.toml", "build.rs", "rust-toolchain",
                 "rust-toolchain.toml")
PROJECT_DIRS = (".cargo",)
SOURCE_EXTS = (".dfy", ".rs")


def turns_off(lever):
    """True for a lever that switches automation off (OFF_LEVERS): removing it
    from a shipped file switches the automation back on."""
    lv = " ".join(lever.split())
    return (lv in ("{:disableNonlinearArithmetic}", "@DisableNonlinearArithmetic",
                   "@DisableNonlinearArithmetic()", "{:induction false}", "@Induction(false)"))


def off_levers(path, text=None):
    """Sorted ["<scope> <lever>"] of the automation-off levers of one Dafny or
    Verus source (practice mode's frozen levers; duplicates kept)."""
    return sorted(f"{s} {lv}" for s, lv, _ in levers(path, text) if turns_off(lv))


def off_lever_findings(frozen, candidate):
    """Practice mode: a `freeze-lever-removed` Finding (path = the candidate) for
    each automation-off lever of `frozen` (a list from off_levers, or a source
    path) that `candidate` no longer carries at the same scope."""
    want = Counter(frozen if isinstance(frozen, list) else off_levers(frozen))
    have = Counter(off_levers(candidate))
    return [Finding(str(candidate), 0, "freeze-lever-removed",
                    f"{key}: an automation-off lever the file ships is gone"
                    + (f" (x{n})" if n > 1 else ""))
            for key, n in sorted((want - have).items())]


class LeverError(ValueError):
    """A pair the check cannot compare (a missing path, another language, a
    file beside a directory, a source that does not parse)."""


def lang_of(path):
    p = str(path)
    if p.endswith(".dfy") or p.endswith(".dfy.specimen"):
        return "d"
    if p.endswith(".rs") or p.endswith(".rs.specimen"):
        return "v"
    return None


# --- the lever tables ------------------------------------------------------------------------

def dafny_levers(text, path="<text>"):
    """[(scope, lever text, line)] of a Dafny source."""
    src = D.parse_source(text, str(path))
    spans = []
    for d in src.decls:
        last = d.by_method[1] if d.by_method else d.body[1] if d.body else d.header_end - 1
        spans.append((d.start, max(last, d.start), d.qual))
    out = []
    for a in src.attrs:
        if not ((a.style == "{:" and a.name in DAFNY_LEVERS) or
                (a.style == "@" and a.name in DAFNY_AT_LEVERS)):
            continue
        holders = [s for s in spans if s[0] <= a.start <= s[1]]
        scope = max(holders, key=lambda s: s[0])[2] if holders else _dafny_module_scope(src, a)
        if a.style == "{:":
            lever = "{:" + a.name + (" " + a.args if a.args else "") + "}"
        else:
            lever = "@" + a.name + a.args.replace(" ", "")
        out.append((scope, lever, a.line))
    return out


def _dafny_module_scope(src, a):
    """`module <qual>` for an attribute in a module header or body outside every
    declaration, else `(file)`."""
    inside = [m for m in src.modules if m.line <= a.line and a.start <= m.close]
    if not inside:
        return "(file)"
    return "module " + max(inside, key=lambda m: (m.line, m.open)).qual


def _verus_name(src, o, c):
    """The attribute's path text (`verifier::rlimit(20)`), tokens joined bare."""
    k = o + 1
    if src.toks[k].text == "!":
        k += 1
    return "".join(x.text for x in src.toks[k + 1:c])


def verus_levers(text, path="<text>"):
    """[(scope, lever text, line)] of a Verus source."""
    try:
        src = vs.parse(text)
    except vs.ParseError as e:
        raise LeverError(f"{path}: does not parse ({e})") from None
    t = src.toks
    items = list(src.walk())
    out = []
    for k, x in enumerate(t):
        if not (x.kind == "punct" and x.text == "#"):
            continue
        if k + 1 < len(t) and t[k + 1].text == "[":
            o, close = k, src.pairs.get(k + 1)
        elif k + 2 < len(t) and t[k + 1].text == "!" and t[k + 2].text == "[":
            o, close = k, src.pairs.get(k + 2)
        else:
            continue
        if close is None:
            continue
        name = _verus_name(src, o, close)
        if not (name.startswith("verifier::") or name.startswith("verifier(")):
            continue
        head = name[len("verifier::"):] if name.startswith("verifier::") else \
            name[len("verifier("):].rstrip(")")
        if head.split("(")[0] in VERUS_NON_LEVERS:
            continue
        inner = t[o + 1].text == "!"
        # an outer attribute belongs to the item it starts; an inner one
        # (`#![…]`) to the item whose body holds it, or to the file
        holders = [it for it in items if it.kind != "macro" and (
            (it.body is not None and it.body[0] < o < it.body[1]) if inner
            else it.start <= o < it.end)]
        if holders:
            it = max(holders, key=lambda i: i.start)
            sym = vs.item_symbol(it) if it.name else ""
            scope = f"{it.kind} {sym}".strip()
        else:
            scope = "(file)"
        out.append((scope, ("#![" if t[o + 1].text == "!" else "#[") + name + "]", x.line))
    return out


def levers(path, text=None):
    """[(scope, lever text, line)] of one Dafny or Verus source file."""
    lang = lang_of(path)
    if lang is None:
        raise LeverError(f"{path}: not a Dafny or Verus source")
    text = Path(path).read_text(encoding="utf-8") if text is None else text
    return dafny_levers(text, path) if lang == "d" else verus_levers(text, path)


# --- the comparison ----------------------------------------------------------------------------

def _removable(lever):
    """True for a trust escape whose removal only strengthens a delivery."""
    return any(lever == r or (r.startswith(("{:", "@")) and (
        lever.startswith(r + " ") or lever.startswith(r + "}") or lever.startswith(r + "(")
        or lever == r)) for r in REMOVABLE)


def _file_findings(task, delivery, ttext=None, dtext=None):
    tl, dl = levers(task, ttext), levers(delivery, dtext)
    tc = Counter((s, lv) for s, lv, _ in tl)
    dc = Counter((s, lv) for s, lv, _ in dl)
    dline = {}
    for s, lv, ln in dl:
        dline.setdefault((s, lv), ln)
    out = []
    for key, n in sorted((dc - tc).items()):
        out.append(Finding(str(delivery), dline.get(key, 0), "lab-lever-added",
                           f"{key[1]} on {key[0]}: a lever the task form does not ship"
                           + (f" (x{n})" if n > 1 else "")))
    for key, n in sorted((tc - dc).items()):
        if _removable(key[1]):
            continue
        out.append(Finding(str(delivery), 0, "lab-lever-removed",
                           f"{key[1]} on {key[0]}: a lever the task form ships is gone"
                           + (f" (x{n})" if n > 1 else "")))
    return out


def _tree_files(root):
    root = Path(root)
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if any(part in ("target", ".git") for part in rel.parts):
            continue
        if p.is_file():
            out[rel.as_posix()] = p
    return out


def _is_project(rel):
    parts = rel.split("/")
    return parts[-1] in PROJECT_FILES or any(x in PROJECT_DIRS for x in parts[:-1])


def lever_findings(task, delivery):
    """Findings of a delivery against its task form: two files of one language
    (Dafny or Verus, specimens included) or two directories (a crate or a
    Dafny project, compared file by file under the same relative paths).
    [] = the delivery keeps the task form's levers exactly. Raises LeverError
    when the pair cannot be compared."""
    task, delivery = Path(task), Path(delivery)
    for p in (task, delivery):
        if not p.exists():
            raise LeverError(f"{p}: no such file or directory")
    if task.is_file() and delivery.is_file():
        if lang_of(task) is None or lang_of(task) != lang_of(delivery):
            raise LeverError(f"{task}, {delivery}: two Dafny or two Verus sources")
        return _file_findings(task, delivery)
    if not (task.is_dir() and delivery.is_dir()):
        raise LeverError(f"{task}, {delivery}: two files or two directories")
    tf, df = _tree_files(task), _tree_files(delivery)
    out = []
    for rel in sorted(set(tf) | set(df)):
        a, b = tf.get(rel), df.get(rel)
        if _is_project(rel):
            if a is None or b is None or a.read_bytes() != b.read_bytes():
                out.append(Finding(str(b or delivery / rel), 0, "lab-project-changed",
                                   f"{rel}: a project file differs from the task form's"
                                   if a is not None and b is not None else
                                   f"{rel}: a project file is "
                                   + ("missing" if b is None else "added")))
            continue
        if not rel.endswith(SOURCE_EXTS):
            continue
        if a is not None and b is not None:
            out += _file_findings(a, b)
        elif b is not None:
            for s, lv, ln in levers(b):
                out.append(Finding(str(b), ln, "lab-file-added",
                                   f"{lv} on {s}: a lever in a file the task form does not "
                                   "have"))
        else:
            for s, lv, _ in levers(a):
                if _removable(lv):
                    continue
                out.append(Finding(str(delivery / rel), 0, "lab-lever-removed",
                                   f"{lv} on {s}: a lever the task form ships is gone (its "
                                   "file is missing)"))
    return out
