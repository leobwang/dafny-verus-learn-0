#!/usr/bin/env python3
"""pins.py — the golden harness (phase DV1b; spec §3.8.6, §8.3, §8.5 "golden
pins"; DELTAS Δ29, Δ36–Δ38, Δ59, Δ72).

Dafny and Verus have no in-file output pin, so every answer that is a tool
output lives in a specimen (an IDE-ignored *.dfy.specimen / *.rs.specimen,
copied to scratch with its real extension by the dvl libraries), a given-only
check unit, or a slot file, and this harness checks it:

  obligation   `// FAILS a c`: the set of `// [x]` labels on the lines where the
               verifier reports an error (Dafny: an error or its related
               location; Verus: an error, plus failed proof_note labels) must
               equal the predicted set (Δ38: sets, never order). The run must
               reach verification: a specimen that stops at parse or resolve
               is "could not run", never a pass (so `FAILS none` cannot pass
               on a file that does not resolve)
  error        `// EXPECT @12 "fragment"`: some diagnostic on line 12 contains
               the fragment
  value        an enabled `expect`/`assert_eq!` check passes when the test runs
               (dafny test --target py in a scratch copy; verus --compile
               --test), a Verus `by (compute_only)` assert verifies. A wrong
               compute_only value stops Verus at the VIR stage with an error
               on its own line: that is the slot's FAIL, and the other slots
               of the file are judged on a re-run with it commented out
  verdict      the salted sha256 of the normalized answer in slots/<ID>.slots
               equals the pin in expected/<ID>.pins (`<K><n><lang>
               salted-sha256 <64 hex>`, over "<module id>:<item id>:<answer>";
               a legacy unsalted `sha256` pin is never read: it is reported
               as a problem, DV2b retired its reader)

Author pins (never learner slots): a live `// EXPECT @<line> "<fragment>"` line
outside an error-format item pins a diagnostic of W items, card failures and
demos; a sidecar expected/<repo path>.expect pins a file's whole normalized
output (Δ36/Δ37/Δ59: diagnostics sorted by position, paths reduced to base
names, the Dafny uri and the Verus build-info and timing blocks dropped, the
`aborting due to` line and vstd trigger notes dropped, JSON keys and note
lists sorted; scratch and repo paths redacted). The sidecar of a card demo
that carries `// after: <item id>` lines is SEALED: it shows no output at
all, only one salted hash of the whole normalized output, its diagnostics
included (seal_key, sealed_hash), so it answers no prediction before the
learner records it, and drift in any line still fails.

Chapter pins (DV2b): every tool output a chapter quotes sits in a BARE fence
directly preceded by `<!-- pin: <entry id> -->`; the entry in
expected/<ID>.chapter.toml gives the exact command, its working directory, its
inputs and the normalization, and records the hash of the fence body and of
each input as captured (the section "Chapter fences" below has the schema).

Usage:
  pins.py <ID>                  learner: check the module's ENABLED slots whose
                                first try is recorded (an unrecorded one is not
                                run: its result would answer the prediction).
                                An item whose file was deleted since it shipped
                                (the newest merge base of HEAD with basic /
                                challenge, or main while neither exists) counts as
                                not passing. Prints ✓/✗ and locations only.
  pins.py --ci [--module ID]    CI: every non-planned module's author
                                pins, every sidecar (a sidecar whose source is
                                gone is stale, and a sidecar of a file that
                                carries prediction slots is an answer leak:
                                both errors), the verdict pin files (every pin
                                names a verdict item, every verdict item has a
                                pin, and, in the author's context only (CI=true
                                or the author's worktree) and whenever the
                                reference slot file exists, every pin equals
                                the hash of its reference answer: the static
                                half of --ref; elsewhere that half is skipped
                                and the summary says so, never silently),
                                the count pins expected/<ID>.counts (Δ11:
                                one per unit, no stale unit or symbol; schema
                                2: one shipped-state [[file]] pin per
                                exercise, check, exit and agent file, with its
                                role; vcheck --shipped compares the states),
                                every legacy unsalted verdict pin (a problem in
                                every context), and every chapter pin of the
                                module's chapter (as --chapter). With
                                no armed module (every module planned) and no
                                sidecar or count pin it passes LOUDLY ("no
                                armed module: nothing to check"); with armed
                                modules an empty set fails (one module named with
                                --module that has no verdict item and no reference
                                slot passes LOUDLY). scripts/ci.sh runs
                                --ref too (the reference slot checks run the
                                verifier).
  pins.py --chapter ID [--entry E…]
                                the chapter pins of one module (anywhere): every
                                pinned fence of its chapter is re-run with its
                                entry's command and compared with the fence
                                body (locations only). An entry whose inputs
                                differ from the files it was captured on is
                                stale: a problem in the author's context (spec
                                §3.15 rule 9: re-capture), skipped and counted
                                elsewhere (a learner's own edits); elsewhere
                                too, an entry whose output settles a prediction
                                with no recorded first try is not run (H5),
                                only counted. A recorded quote is checked
                                statically (its body hash), and, in the
                                author's context, verbatim against its source.
  pins.py --update --chapter ID [--entry E…]
                                author: run each entry (every entry quoted in
                                the chapter, or the named ones) and write its
                                output into the chapter's fence below its pin
                                line (a pin line with no fence gets one), then
                                record the hashes in expected/<ID>.chapter.toml
                                (rewritten canonically). A recorded quote's
                                body is the author's; --update checks it
                                verbatim against its source and pins its hash.
                                An entry that cannot be captured is named (exit
                                1) and keeps its fence and pin; the others are
                                written. Nothing is written if the chapter
                                changed while the entries ran.
  pins.py --update [FILE…|--module ID]
                                author: (re)write sidecars from the current
                                output (FILE: create or refresh its sidecar).
                                Refused for a file whose items carry prediction
                                slots (P items, verdict switches, value,
                                obligation and error slots): its output answers
                                them (H5), so those answers are pinned only
                                through the twin (--ref) or as hashes.
  pins.py --ref [--module ID]   author/CI: the reference side: every verdict pin
                                equals the hash of the reference answer, and
                                every reference specimen's enabled slots pass.
                                No armed module: a loud pass, as for --ci.
  pins.py --update --ref --module ID
                                author: write expected/<ID>.pins from the
                                reference answers (salted hashes only).
--update and --ref are author-only (CI=true or the author's worktree); --ci
runs anywhere and reads the reference only in the author's context.
Mismatches print locations only, never content.

Exit: 0 all pass · 1 a mismatch, a stale or missing pin, or nothing to check ·
2 usage · 3 refused.
"""

import argparse
import dataclasses
import importlib.machinery
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
import tomllib
import types
from collections import defaultdict
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
    """The SHARED SLOT RULES section of scripts/firsttry.py, as a module (one
    implementation of the slot grammar and the vacuity rules, spec §3.8.4)."""
    path = SCRIPTS / "firsttry.py"
    text = path.read_text(encoding="utf-8")
    a, b = text.index(BEGIN), text.index(END)
    mod = types.ModuleType("shared_slot_rules")
    mod.__file__ = str(path)
    code = "\n" * text[:a].count("\n") + text[a:b]     # keep firsttry.py's line numbers
    exec(compile(code, str(path), "exec"), mod.__dict__)
    return mod


core = _load_core()
SR = load_shared_rules()
D, V, ci, common, ccm = core.D, core.V, core.ci, core.common, core.ccm
EXPECTED = "expected"
# A verdict pin line. `salted-sha256` (the form every writer writes since the
# DV2a fix round): sha256 over "<module id>:<item id>:<normalized answer>"
# (SR.sr_salted_answer_hash). `sha256` (LEGACY_PIN_KEYWORD) is the unsalted
# form pins written before that round carried. DV2b retired its reader
# (LEGACY_PINS_READABLE stays False, and the shared slot rules no longer hold
# an unsalted hash): a legacy pin still parses, so every reader can name it,
# but it matches no answer (firsttry --check and --exit, the learner mode and
# --ref see "no pin"), and `pins.py --ci` reports it as a problem in every
# context. Re-pin: `scripts/pins.py --update --ref --module <ID>`
# (author-only) rewrites the module's pins, salted, from the reference
# answers.
SALTED_PIN_KEYWORD = "salted-sha256"
LEGACY_PIN_KEYWORD = "sha256"
LEGACY_PINS_READABLE = False
PIN_LINE = re.compile(r"\s*([WCPHXTA][1-9]\d*(?:dv|py|d|v))\s+(salted-sha256|sha256)\s+"
                      r"([0-9a-f]{64})\s*$")
LIVE_EXPECT = re.compile(r'^\s*//\s*EXPECT\s+@(\d+)\s+"((?:[^"\\]|\\.)*)"\s*$')
HOLE_MESSAGE = {"assume": "W-V07", "admit": "W-V07", "assume_termination": "W-V09"}


@dataclasses.dataclass
class Check:
    item: str
    file: str          # repo-relative path of the slot
    line: int
    fmt: str
    state: str
    outcome: str = "error"     # pass | fail | error
    why: str = ""              # a location-only reason


# =====================================================================================
# Verdict pins (expected/<ID>.pins)
# =====================================================================================

def pins_path(root, mid):
    return Path(root) / EXPECTED / f"{mid}.pins"


def read_pins(root, mid):
    """({local id: (line, sha256, keyword)}, [errors]) of expected/<ID>.pins
    (absent = {}). keyword: SALTED_PIN_KEYWORD or LEGACY_PIN_KEYWORD."""
    p = pins_path(root, mid)
    table, errs = {}, []
    if not p.is_file():
        return table, errs
    for ln, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = PIN_LINE.fullmatch(line)
        if not m:
            errs.append(f"{EXPECTED}/{mid}.pins:{ln}: malformed pin (`<K><n><lang>  "
                        f"{SALTED_PIN_KEYWORD} <64 hex>`)")
        elif m.group(1) in table:
            errs.append(f"{EXPECTED}/{mid}.pins:{ln}: {m.group(1)} is pinned twice")
        else:
            table[m.group(1)] = (ln, m.group(3), m.group(2))
    return table, errs


def pin_hash(mid, local, answer):
    """The salted pin a raw slot-file answer hashes to."""
    return SR.sr_salted_answer_hash(mid, local, SR.sr_slot_value(answer))


def pin_matches(mid, local, answer, entry):
    """True when the raw answer hashes to the pin entry (line, digest,
    keyword). A legacy unsalted pin matches nothing (its reader is retired)."""
    _, digest, keyword = entry
    if keyword != SALTED_PIN_KEYWORD:
        return False
    return pin_hash(mid, local, answer) == digest


def verdict_outcome(root, mid, item, raw_value):
    """pass | fail | error for a verdict item's slot-file answer."""
    if raw_value is None:
        return "error"
    table, errs = read_pins(root, mid)
    local = item["id"].split(".", 1)[1]
    if local not in table:
        return "error"
    if table[local][2] != SALTED_PIN_KEYWORD:
        return "error"                  # a legacy pin: never read (pin_hygiene names it)
    return "pass" if pin_matches(mid, local, raw_value, table[local]) else "fail"


def slot_values(root, rel):
    p = Path(root) / rel
    return SR.sr_slot_file_values(p.read_text(encoding="utf-8")) if p.is_file() else {}


def slot_payload_text(root, item, slot):
    """The normalized text of one slot as recorded (a verdict: its answer)."""
    if slot["format"] == "verdict":
        vals = slot_values(root, slot["file"])
        raw = vals.get(item["id"].split(".", 1)[1], (None, ""))[1]
        return SR.sr_normalize_answer(SR.sr_slot_value(raw))
    lines = (Path(root) / slot["file"]).read_text(encoding="utf-8").split("\n")
    return SR.sr_payload(lines[slot["line"] - 1], slot["file"])


slot_bearing = core.slot_bearing


# =====================================================================================
# Running slots
# =====================================================================================

def _enclosing_dafny(text, path, line):
    src = D.parse_source(text, str(path))
    best = None
    for d in src.decls:
        if d.kind in D.METHODLIKE and d.line <= line <= max(d.end_line, d.line) and \
                (best is None or d.line >= best.line):
            best = d
    return best.qual if best else None


def _enclosing_verus(text, line):
    try:
        src = V.vs.parse(text)
    except V.vs.ParseError:
        return None
    best = None
    for it in src.walk():
        if it.kind == "fn" and src.line_of(it.start) <= line <= src.line_of(max(it.end - 1,
                                                                               it.start)):
            best = it
    return best.name if best else None


def _diags_with_holes(res):
    """A run's diagnostics plus, for Verus, one per hole with its pinned
    wording (the classifier keeps holes apart from the diagnostics)."""
    out = list(res.diagnostics)
    if res.lang == "verus":
        msgs = common.load_pins()["verus"]["messages"]
        for h in res.holes:
            mid = HOLE_MESSAGE.get(h.kind, "W-V08")
            text = re.sub(r"^error: ", "", msgs.get(mid, ""))
            out.append(common.Diag(h.file, h.line, h.col, "error", text, mid))
    return out


def _labels_failing(res, path):
    """The `// [x]` labels on the error lines of `path` (plus, for Verus, the
    failed proof_note labels)."""
    path = str(Path(path).resolve())
    if res.lang == "dafny":
        return set(D.failing_labels(res, path))
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    out = set()
    for d in _diags_with_holes(res):
        if d.severity == "error" and d.file == path and 1 <= d.line <= len(lines):
            m = SR.SR_LABEL.search(lines[d.line - 1])
            if m:
                out.add(m.group(1))
    _, failed = V.proof_notes(core.target_stdout(res))
    return out | set(failed)


def _no_verdict(res):
    return res.verdict in ("refused", "killed(memory)") or (
        res.verdict == "error" and res.stage not in ("parse", "resolve"))


def run_slot_checks(root, rec, items, select, enable_filled=False, tag="pins", copy_as=None):
    """{item id: [Check]} for the slots select(item, slot) picks.
    enable_filled: filled-disabled value slots are enabled in a scratch shadow
    copy first (firsttry --check); every other slot form is a comment the
    harness reads, so its file runs as is. copy_as maps a file (a reference
    twin) to the learner path it runs at, in a shadow tree, so it gets its
    module's context. Nothing is printed; shadow copies are deleted."""
    root = Path(root)
    mid = rec["id"]
    copy_as = copy_as or {}
    out = defaultdict(list)
    by_file = defaultdict(list)
    for it in items:
        for s in it["slots"]:
            if not select(it, s):
                continue
            c = Check(it["id"], s["file"], s["line"], s["format"], s["state"])
            out[it["id"]].append(c)
            if s["format"] == "verdict":
                vals = slot_values(root, s["file"])
                raw = vals.get(it["id"].split(".", 1)[1], (None, None))[1]
                got = verdict_outcome(root, mid, it, raw)
                c.outcome = got
                c.why = "" if got != "error" else f"no pin for {it['id']} in {EXPECTED}/{mid}.pins"
            else:
                by_file[s["file"]].append((it, s, c))
    for rel, entries in by_file.items():
        _run_file(root, rel, entries, enable_filled, tag, copy_as.get(rel))
    return dict(out)


def _run_file(root, rel, entries, enable_filled, tag, run_as):
    lang = core.lang_of(rel)
    src_path = root / rel
    text = src_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    edits = [(it, s) for it, s, _ in entries
             if enable_filled and s["state"] == "filled-disabled" and s["format"] == "value"]
    shadow = None
    target = src_path
    try:
        if run_as:
            # a reference twin runs at its learner path, in its learner unit or crate
            ctx = core.twin_context(core.Target(lang, src_path.resolve(), Path(root)), root)
            if ctx is None:
                raise RuntimeError(f"{rel}: its learner unit does not exist")
            shadow, _ = ctx
            target = shadow / run_as
        elif edits:
            copy_rel = rel
            if lang == "v" and not rel.endswith(".specimen"):
                copy_rel = _crate_rel(root, rel)
                if copy_rel is None:
                    raise RuntimeError(f"{rel}: no crate directory holds it")
            shadow = core.shadow_tree(root, [copy_rel], tag)
            target = shadow / rel
        if edits:
            for it, s in edits:
                lines[s["line"] - 1] = SR.sr_enable_line(lines[s["line"] - 1], rel)
            target.write_text("\n".join(lines), encoding="utf-8")
        _judge(root, rel, lang, target, entries, lines)
    except (RuntimeError, OSError, ValueError) as e:
        for _, _, c in entries:
            c.outcome, c.why = "error", str(e)
    finally:
        core.remove_tree(shadow)


def _crate_rel(root, rel):
    d = (Path(root) / rel).parent
    while d != Path(root) and d != d.parent:
        if (d / "Cargo.toml").is_file():
            return d.relative_to(root).as_posix()
        d = d.parent
    return None


def _judge(root, rel, lang, target, entries, lines):
    tpath = str(Path(target).resolve())
    diag_entries = [e for e in entries if e[1]["format"] in ("obligation", "error")]
    value_entries = [e for e in entries if e[1]["format"] == "value"]
    if diag_entries:
        res = core.lib(lang).verify(str(target))
        if _no_verdict(res):
            for _, _, c in diag_entries:
                c.outcome, c.why = "error", f"no verdict ({res.verdict}); raw output: {res.raw_dir}"
        else:
            failing = _labels_failing(res, target)
            diags = _diags_with_holes(res)
            for it, s, c in diag_entries:
                payload = SR.sr_payload(lines[s["line"] - 1], rel)
                if s["format"] == "obligation":
                    want, problem = SR.sr_obligation(payload)
                    if problem or want is None:
                        c.outcome, c.why = "error", problem or "unfilled"
                        continue
                    if res.stage != "verify":
                        # a run that stopped at parse or resolve proved and
                        # failed nothing: no obligation set can be judged
                        # from it, so `FAILS none` never passes on it
                        c.outcome, c.why = "error", (f"the specimen stops at stage {res.stage} "
                                                     "before verification; raw output: "
                                                     f"{res.raw_dir}")
                        continue
                    c.outcome = "pass" if set(want) == failing else "fail"
                else:
                    line, frag, problem = SR.sr_error(payload)
                    if problem or line is None or frag is None:
                        c.outcome, c.why = "error", problem or "unfilled"
                        continue
                    hit = any(d.file == tpath and d.line == line and frag in d.message
                              for d in diags)
                    c.outcome = "pass" if hit else "fail"
    if value_entries:
        _judge_values(root, lang, target, value_entries, lines, rel)


def _judge_values(root, lang, target, entries, lines, rel):
    text = "\n".join(lines)
    tpath = str(Path(target).resolve())
    spec = [e for e in entries if lang == "v" and
            re.search(r"\bby\s*\(\s*compute", SR.sr_payload(lines[e[1]["line"] - 1], rel))]
    tests = [e for e in entries if e not in spec]
    if lang == "py":
        for _, _, c in entries:
            c.outcome, c.why = "error", "Python value slots are checked by the harness (DV4)"
        return
    if spec:
        _judge_compute(root, target, spec, lines, rel)
    if not tests:
        return
    names = {}
    for it, s, c in tests:
        nm = _enclosing_dafny(text, target, s["line"]) if lang == "d" else \
            _enclosing_verus(text, s["line"])
        if nm is None:
            c.outcome, c.why = "error", "the slot sits in no test method"
            continue
        names[id(c)] = nm
    wanted = sorted(set(names.values()))
    if not wanted:
        return
    res = core.lib(lang).test(str(target), names=wanted)
    per = res.per_symbol
    for it, s, c in tests:
        nm = names.get(id(c))
        if nm is None:
            continue
        hits = [k for k in per if k == nm or k.endswith("." + nm) or k.endswith("::" + nm)]
        if hits:
            c.outcome = "pass" if per[hits[0]] == "passed" else "fail"
        elif res.verdict == "failed" and res.stage in ("parse", "resolve", "compile", "link"):
            c.outcome = "fail"          # the enabled check does not even build
        else:
            c.outcome, c.why = "error", (f"the test did not run ({res.verdict}, stage "
                                         f"{res.stage}); raw output: {res.raw_dir}")


def _judge_compute(root, target, entries, lines, rel):
    """Verus `assert(…) by (compute_only)` value slots. Verus evaluates every
    compute_only assert of a crate at the VIR stage and stops at the first
    that is false (stage resolve: "expression simplifies to … which
    evaluates to false"), on that assert's own line. So an error on a slot's
    own line is that slot's FAIL, whatever the stage; a slot is a PASS once a
    run reached verification with no error on its line. A run that stopped
    before verification on other slots' lines is re-run with those slots
    commented out (in a scratch copy) until every slot is judged; a stop on
    no slot's line (a broken file) leaves the rest "could not run"."""
    todo = list(entries)
    blanked, shadow = set(), None
    run_target = Path(target)
    try:
        for _ in range(len(entries) + 1):
            if not todo:
                return
            if blanked:
                if run_target == Path(target) and not _in_scratch(target):
                    copy_rel = rel if rel.endswith(".specimen") else (_crate_rel(root, rel) or rel)
                    shadow = core.shadow_tree(root, [copy_rel], "compute")
                    run_target = shadow / rel
                text = list(lines)
                for ln in blanked:
                    text[ln - 1] = "// " + text[ln - 1]
                run_target.write_text("\n".join(text), encoding="utf-8")
            res = V.verify(str(run_target))
            if _no_verdict(res):
                for _, _, c in todo:
                    c.outcome, c.why = "error", (f"no verdict ({res.verdict}, stage {res.stage}); "
                                                 f"raw output: {res.raw_dir}")
                return
            rp = str(Path(run_target).resolve())
            err_lines = {d.line for d in res.diagnostics
                         if d.severity == "error" and d.file and str(Path(d.file).resolve()) == rp}
            newly = [e for e in todo if e[1]["line"] in err_lines]
            rest = [e for e in todo if e[1]["line"] not in err_lines]
            for _, _, c in newly:
                c.outcome = "fail"
            if res.stage == "verify":
                for _, _, c in rest:
                    c.outcome = "pass"
                return
            if not newly:
                for _, _, c in rest:
                    c.outcome, c.why = "error", (f"the run stops at stage {res.stage} on no slot's "
                                                 f"line; raw output: {res.raw_dir}")
                return
            blanked |= {e[1]["line"] for e in newly}
            todo = rest
    finally:
        core.remove_tree(shadow)


def _in_scratch(path):
    try:
        return Path(path).resolve().is_relative_to(common.scratch_root().resolve())
    except (OSError, common.DvlError):
        return False


# =====================================================================================
# Goldens (sidecars) and author EXPECT pins
# =====================================================================================

_ABS = re.compile(r"(?<![\w.<>~])/(?:[\w.+@-]+/)+([\w.+@-]+)")


def redact(text, root):
    for p, tag in ((str(Path(root).resolve()), "<root>"),
                   (str(common.scratch_root()), "<scratch>"),
                   (os.environ.get("HOME", "") or "\0", "~")):
        text = text.replace(p, tag)
    return _ABS.sub(lambda m: m.group(1), text)


def sidecar_path(root, rel):
    return Path(root) / EXPECTED / f"{rel}.expect"


def sidecar_source(root, sidecar):
    rel = Path(sidecar).resolve().relative_to((Path(root) / EXPECTED).resolve()).as_posix()
    return rel[:-len(".expect")]


def read_sidecar(path):
    """(command, body lines) of a sidecar."""
    body = [x for x in Path(path).read_text(encoding="utf-8").split("\n")
            if x and not x.startswith("#")]
    if not body or not body[0].startswith("command: "):
        raise ValueError(f"{path}: a sidecar starts with `command: verify|test`")
    return body[0][len("command: "):].strip(), body[1:]


def _job_texts(res, step="-target"):
    if not res.raw_dir:
        return "", ""
    raw = Path(res.raw_dir)
    jobs = sorted(p for p in raw.glob(f"*{step}") if p.is_dir())
    d = jobs[-1] if jobs else raw
    rd = lambda n: (d / n).read_text(encoding="utf-8", errors="replace") if (d / n).is_file() \
        else ""  # noqa: E731
    return rd("stdout.txt"), rd("stderr.txt")


def golden(root, rel, command="verify", res=None):
    """(normalized lines, Result) of one file: the pinned verifier's output."""
    lang = core.lang_of(rel)
    path = Path(root) / rel
    if res is None:
        if command == "verify":
            res = core.lib(lang).verify(str(path))
        elif command == "test":
            res = core.lib(lang).test(str(path))
        else:
            raise ValueError(f"{rel}: unknown sidecar command {command!r}")
    out = [f"exit: {res.exit_code}", f"verdict: {res.verdict}", f"stage: {res.stage}",
           f"verified: {res.verified_count}", f"holes: {len(res.holes)}"]
    out += [f"hole {Path(h.file).name}:{h.line}:{h.col} {h.kind} {h.label}" for h in res.holes]
    if command == "test":
        out += [f"test {k}: {v}" for k, v in sorted(res.per_symbol.items())]
    if lang == "d":
        out += D.normalized(res.diagnostics, path.parent)
    else:
        so, se = _job_texts(res, "-target" if command == "verify" else "-compile-test")
        norm = V.normalize_output(so, se)
        out += json.dumps(norm, sort_keys=True, indent=1, ensure_ascii=False).split("\n")
        if command == "test":
            out += [d.message for d in res.diagnostics if d.code in ("test", "test-not-found")]
    return [redact(x, root) for x in out], res


# Sealed sidecars (DV2a fix round, QPLAN §6 Q10; text-free since DV2b). A
# file with `// after: <item id>` lines is a demo whose output settles that
# prediction, and its sidecar sits in expected/, which a learner can open
# early. For several divergence demos the diagnostics alone settle the
# prediction (Δ120 Open), so a sealed sidecar shows NO output line: the whole
# normalized output (exit code, verdict, stage, counts, holes, every
# diagnostic, the Verus JSON record) is folded into one salted hash,
#   outcome: salted-sha256 <sha256 of "<module id>:<after ids, comma-joined>:
#            <repo path>" + newline + the whole normalized output>,
# so drift in any line still fails pins.py --ci and nothing in the sidecar
# can answer a prediction. A chapter that shows such a demo's output quotes a
# real run in a pinned fence (expected/<ID>.chapter.toml), after the box.

def seal_key(root, rel):
    """(module id, [after ids]) of a file that carries `// after:` lines, or
    None."""
    p = Path(root) / rel
    if not p.is_file():
        return None
    ids = [iid for _, iid in core.after_items(p.read_text(encoding="utf-8"))]
    if not ids:
        return None
    m = re.match(r"(?:.*/)?specimens/([QR]\d\d)/", rel)
    mid = m.group(1) if m else ids[0].split(".", 1)[0]
    return mid, ids


def sealed_hash(mid, ids, rel, lines):
    return SR.sr_sha256(f"{mid}:{','.join(ids)}:{rel}\n" + "\n".join(lines))


def render_sidecar(rel, command, body, seal=None):
    """The sidecar text. seal: (module id, after ids, outcome hash) for a
    sealed sidecar, which shows no output line (body is then unused)."""
    if seal is not None:
        mid, ids, digest = seal
        return (f"# pins.py golden for {rel}: SEALED. This demo waits for {', '.join(ids)},\n"
                "# so its whole normalized output (exit code, verdict, stage, counts, holes and\n"
                "# every diagnostic) is one salted hash, and none of it is shown (spec §3.8.6,\n"
                f"# Δ36, Δ37, Δ59). Regenerate with `scripts/pins.py --update {rel}`; never edit.\n"
                f"command: {command}\nafter: {','.join(ids)}\n"
                f"outcome: {SALTED_PIN_KEYWORD} {digest}\n")
    return (f"# pins.py golden for {rel}: the normalized output of the pinned verifier (spec\n"
            "# §3.8.6, Δ36, Δ37, Δ59). Regenerate with `scripts/pins.py --update "
            f"{rel}`; never edit.\ncommand: {command}\n" + "\n".join(body) + "\n")


def split_sealed(body):
    """(after ids, outcome hash, the lines after the outcome line) of a sealed
    sidecar's body (read_sidecar's second value), or None for an unsealed
    one. A sealed sidecar holds no line after its outcome: any is text that
    the seal should hide (a sidecar sealed before DV2b showed diagnostics)."""
    if len(body) < 2 or not body[0].startswith("after: ") or \
            not body[1].startswith(f"outcome: {SALTED_PIN_KEYWORD} "):
        return None
    ids = [x for x in body[0][len("after: "):].strip().split(",") if x]
    return ids, body[1].split()[-1], body[2:]


def author_expects(rel, text, items):
    """[(pin line, target line, fragment)] of live EXPECT lines that are not an
    error-format item's slots."""
    slot_lines = {s["line"] for it in items if it["file"] == rel and it["format"] == "error"
                  for s in it["slots"]}
    out = []
    for ln, line in enumerate(text.split("\n"), 1):
        m = LIVE_EXPECT.match(line)
        if m and ln not in slot_lines:
            out.append((ln, int(m.group(1)), re.sub(r"\\(.)", r"\1", m.group(2))))
    return out


# =====================================================================================
# Chapter fences (DV2b): expected/<ID>.chapter.toml
# =====================================================================================
#
# Every tool output a chapter quotes is captured on the pins and pinned (spec
# §3.15). In the chapter (the registry's `chapter`), an OUTPUT fence is a bare
# fence (no info string, at column 0) whose nearest preceding non-blank line is
#
#     <!-- pin: <entry id> -->
#
# and every source fence is language-tagged. The entry lives in
# expected/<ID>.chapter.toml (schema 1; pins.py --update rewrites the file
# canonically, so notes go in `note`, never in TOML comments):
#
#   schema = 1
#   [[entry]]
#   id      = "gate-h1d"            lower case, digits, '.', '_', '-'; unique
#   kind    = "command"            (default) or "recorded" (below)
#   cmd     = ["scripts/vcheck", "--gate", "dafny/Q/Q01_Hello/core"]
#             the exact command as the learner types it: one of the course
#             tools scripts/vcheck, scripts/vaudit, scripts/specfreeze,
#             scripts/firsttry.sh (--report or --lint-hollow only), or a
#             pinned toolchain binary `dafny` / `verus` (run on scratch files)
#   cwd     = "root"               (default: the course root) or "scratch": a
#             fresh scratch directory holding the entry's scratch files; a
#             toolchain binary always runs there
#   display = "..."                optional: the command line the fence shows
#             (default: cmd, shell-quoted)
#   inputs  = ["..."]              optional: repo files the output depends on
#             beyond those cmd names (cmd's existing paths, a module id's
#             files and slot and calibration files, and the copied scratch
#             sources are inputs by themselves)
#   answers = ["Q01.P8dv"]          optional: predictions this output settles
#             (chapter_lint: the fence sits after their boxes; the `after:`
#             lines and slots of a specimen input count by themselves)
#   excerpt = [3, 12]              optional: the fence shows output lines 3-12
#             and then a line "..." (spec §3.15 rule 4; say what was cut); an
#             excerpt of the whole output is refused
#   guards  = "open"               (default) run as the learner sees it once
#             the predictions it waits for are recorded (vcheck's H5 guards
#             off); "closed" quotes the run as it is before (a refusal)
#   note    = "..."                optional, free text
#   [entry.normalize]              pins.py's normalization, beyond the fixed
#             one (ANSI codes and trailing blanks dropped; the scratch
#             directory, the course root and $HOME redacted to `.`, `.` and
#             `~`; any other path under the scratch root to `<scratch>/…`)
#   prompt  = true                 first fence line `$ <command>`
#   exit    = false                end with `$ echo $?` and the exit code
#   drop    = ["regex", ...]       drop the output lines that match
#   replace = [["regex", "text"], ...]  re.sub on each line (a volatile token;
#             the chapter states the caveat, spec §3.15 rule 6)
#   [entry.scratch."probe.dfy"]    a scratch file: exactly one of
#             text = "..." · copy = "<repo path>" (a specimen keeps its real
#             extension this way) · fence = "above" (the body of the nearest
#             language-tagged fence above the pin line: the source the
#             chapter shows)
#   [entry.pinned]                 WRITTEN BY pins.py --update, never by hand:
#             body = sha256 of the fence body; [entry.pinned.inputs] maps each
#             input (a repo path, or "scratch:<name>") to its sha256 ("absent"
#             for a missing file) as captured. A guards = "closed" entry also
#             counts the calibration file of each prediction it waits for, so a
#             recorded first try makes the quoted refusal stale, never a
#             mismatch.
#
# A `recorded` entry quotes output no course command can re-run (a guard
# refusal of a Claude Code session, from the author's acceptance archive):
# `source` names the record (an author-only path), the fence body is the
# author's verbatim copy (a trailing "..." line marks an excerpt), and
# `normalize.replace` may redact it. --update checks every body line against
# the record (JSON string values decoded) and pins the body's hash; --ci
# checks the hash everywhere and the record only in the author's context.
#
# Checks (pins.py --chapter, --ci): every pin line names an entry and every
# entry is quoted exactly once; the fence body hashes to `pinned.body`; the
# inputs hash to `pinned.inputs` (else the entry is stale: spec §3.15 rule 9,
# a problem in the author's context, skipped and counted elsewhere, where the
# difference is the learner's own work); the command's output, normalized and
# rendered, equals the fence body. Problems print locations only.

CHAPTER_SCHEMA = 1
PIN_COMMENT = re.compile(r"^<!--\s*pin:\s*(\S*)\s*-->\s*$")
PIN_ID = re.compile(r"[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?")
FENCE_OPEN = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
SCRATCH_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}")
ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
COURSE_TOOLS = {"scripts/vcheck": "vcheck", "scripts/vaudit": "vaudit",
                "scripts/specfreeze": "specfreeze", "scripts/firsttry.sh": "firsttry.py"}
# Forms a chapter never quotes: author-only modes, and modes that write state.
TOOL_REFUSED = {"scripts/vcheck": ("--ref", "--pin-counts"),
                "scripts/vaudit": ("--ref", "--write"),
                "scripts/specfreeze": ("--pin",),
                "scripts/firsttry.sh": ("--check", "--exit", "--record", "--empty-body")}
FIRSTTRY_READ_ONLY = ("--report", "--lint-hollow")
TOOLCHAIN_BINARIES = ("dafny", "verus")
ENTRY_KEYS = ("id", "kind", "cmd", "cwd", "display", "inputs", "answers", "excerpt", "guards",
              "source", "note", "normalize", "scratch", "pinned")
NORMALIZE_KEYS = ("prompt", "exit", "drop", "replace")
SCRATCH_KEYS = ("text", "copy", "fence")
ENTRY_TIMEOUT_S = 3600
INPUT_SKIP = ("target", "__pycache__", ".verus-log", ".verus-solver-log")
ABSENT = "absent"

# Runs a course tool as the learner would, in a fresh interpreter. With
# guards "open" (pins.py's capture: the run a learner sees once the
# predictions it waits for are recorded) the H5 guards are off for this one
# process; nothing else changes. pins.py's own code, never an environment
# switch a shell line could set.
_BOOT = r"""
import importlib.machinery, importlib.util, runpy, sys
from pathlib import Path
sys.dont_write_bytecode = True
script, guards = sys.argv[1], sys.argv[2]
sys.argv = [script] + sys.argv[3:]
scripts = Path(script).resolve().parent
sys.path.insert(0, str(scripts))
loader = importlib.machinery.SourceFileLoader("vcheck", str(scripts / "vcheck"))
core = importlib.util.module_from_spec(importlib.util.spec_from_loader("vcheck", loader))
sys.modules["vcheck"] = core
loader.exec_module(core)
if guards == "open":
    core.h5_guard = lambda root, target: None
    core.slot_guard = lambda root, target: None
if Path(script).name == "vcheck":
    sys.exit(core.main())
runpy.run_path(script, run_name="__main__")
"""


@dataclasses.dataclass
class Fence:
    open: int                  # 0-based index of the opening line
    close: int | None          # index of the closing line (None: never closed)
    indent: int
    marker: str
    info: str
    body: list
    pin: str | None = None     # the entry id of the pin line above it
    pin_line: int | None = None


def _dedent(line, n):
    k = 0
    while k < n and k < len(line) and line[k] == " ":
        k += 1
    return line[k:]


def parse_chapter(lines):
    """(fences, dangling): every fenced block of a chapter, each with the pin
    line that precedes it (blank lines between allowed), and the pin lines
    [(index, id)] that no fence follows."""
    fences, dangling, pending = [], [], None
    i = 0
    while i < len(lines):
        line = lines[i]
        m = FENCE_OPEN.match(line)
        if m and not (m.group(2)[0] == "`" and "`" in m.group(3)):
            ind, mark, info = len(m.group(1)), m.group(2), m.group(3).strip()
            close = re.compile(r"^ {0,3}" + re.escape(mark[0]) + "{" + str(len(mark)) +
                               r",}\s*$")
            j = i + 1
            while j < len(lines) and not close.match(lines[j]):
                j += 1
            f = Fence(i, j if j < len(lines) else None, ind, mark, info,
                      [_dedent(x, ind) for x in lines[i + 1:j]])
            if pending is not None:
                f.pin_line, f.pin = pending
                pending = None
            fences.append(f)
            i = j + 1
            continue
        pm = PIN_COMMENT.match(line)
        if pm:
            if pending is not None:
                dangling.append(pending)
            pending = (i, pm.group(1))
        elif line.strip() and pending is not None:
            dangling.append(pending)
            pending = None
        i += 1
    if pending is not None:
        dangling.append(pending)
    return fences, dangling


def chapter_toml_path(root, mid):
    return Path(root) / EXPECTED / f"{mid}.chapter.toml"


def _toml_rel(mid):
    return f"{EXPECTED}/{mid}.chapter.toml"


def _is_hex(s):
    return isinstance(s, str) and re.fullmatch(r"[0-9a-f]{64}", s) is not None


def _norm_rel(arg):
    return os.path.normpath(arg).replace(os.sep, "/")


def _cmd_values(cmd):
    """[(option it follows or None, value)] of a command's non-option words
    (an `--opt=value` word gives (--opt, value))."""
    out, prev = [], None
    for a in cmd[1:]:
        if a.startswith("-"):
            if "=" in a and a.startswith("--"):
                k, v = a.split("=", 1)
                out.append((k, v))
                prev = None
            else:
                prev = a
            continue
        out.append((prev, a))
        prev = None
    return out


def _entry_problems(root, mid, e, k):
    """Schema problems of one entry (locations: the pin file and the entry)."""
    name = e.get("id") if isinstance(e.get("id"), str) else f"#{k}"
    w = f"{_toml_rel(mid)}: entry {name}"
    out = []
    if not isinstance(e, dict):
        return [f"{w}: not a table"]
    unknown = sorted(set(e) - set(ENTRY_KEYS))
    if unknown:
        out.append(f"{w}: unknown key(s) {', '.join(unknown)}")
    if not isinstance(e.get("id"), str) or not PIN_ID.fullmatch(e["id"]):
        out.append(f"{w}: `id` is lower-case letters, digits, '.', '_' and '-' (at most 64)")
    kind = e.get("kind", "command")
    if kind not in ("command", "recorded"):
        out.append(f"{w}: `kind` is \"command\" or \"recorded\"")
        return out
    norm = e.get("normalize", {})
    if not isinstance(norm, dict) or set(norm) - set(NORMALIZE_KEYS):
        out.append(f"{w}: [entry.normalize] takes only {', '.join(NORMALIZE_KEYS)}")
        norm = {}
    for key in ("prompt", "exit"):
        if key in norm and not isinstance(norm[key], bool):
            out.append(f"{w}: normalize.{key} is true or false")
    drop = norm.get("drop", [])
    if not isinstance(drop, list) or not all(isinstance(x, str) for x in drop):
        out.append(f"{w}: normalize.drop is a list of regular expressions")
        drop = []
    rep = norm.get("replace", [])
    if not isinstance(rep, list) or not all(isinstance(x, list) and len(x) == 2 and
                                            all(isinstance(y, str) for y in x) for x in rep):
        out.append(f"{w}: normalize.replace is a list of [regex, replacement] pairs")
        rep = []
    for pat in drop + [x[0] for x in rep]:
        try:
            re.compile(pat)
        except re.error as err:
            out.append(f"{w}: the regular expression {pat!r} does not compile ({err})")
    for key in ("display", "note", "source"):
        if key in e and not isinstance(e[key], str):
            out.append(f"{w}: `{key}` is a string")
    ans = e.get("answers", [])
    if not isinstance(ans, list) or not all(isinstance(x, str) and ci.ITEM_ID.fullmatch(x)
                                            for x in ans):
        out.append(f"{w}: `answers` lists item ids (like Q01.P8dv)")
    if "excerpt" in e:
        x = e["excerpt"]
        if not (isinstance(x, list) and len(x) == 2 and all(type(v) is int for v in x) and
                1 <= x[0] <= x[1]):
            out.append(f"{w}: `excerpt` is [first line, last line], 1 <= first <= last")
    pinned = e.get("pinned")
    if pinned is not None:
        ok = isinstance(pinned, dict) and not set(pinned) - {"body", "inputs"} and \
            _is_hex(pinned.get("body")) and isinstance(pinned.get("inputs", {}), dict) and \
            all(isinstance(p, str) and (_is_hex(h) or h == ABSENT)
                for p, h in pinned.get("inputs", {}).items())
        if not ok:
            out.append(f"{w}: [entry.pinned] is pins.py's (body and inputs hashes): re-capture "
                       f"with scripts/pins.py --update --chapter {mid} --entry {name}")
    if kind == "recorded":
        for key in ("cmd", "cwd", "display", "inputs", "excerpt", "guards", "scratch"):
            if key in e:
                out.append(f"{w}: a recorded quote takes no `{key}`")
        if not isinstance(e.get("source"), str) or not e.get("source"):
            out.append(f"{w}: a recorded quote names its `source` (the record it copies)")
        for key in ("prompt", "exit", "drop"):
            if key in norm:
                out.append(f"{w}: a recorded quote's normalize takes only `replace`")
        return out
    if "source" in e:
        out.append(f"{w}: `source` belongs to a recorded quote")
    cmd = e.get("cmd")
    if not (isinstance(cmd, list) and cmd and all(isinstance(x, str) and x for x in cmd)):
        out.append(f"{w}: `cmd` is the command as a non-empty list of words")
        return out
    cwd = e.get("cwd", "root")
    if cwd not in ("root", "scratch"):
        out.append(f"{w}: `cwd` is \"root\" or \"scratch\"")
    if e.get("guards", "open") not in ("open", "closed"):
        out.append(f"{w}: `guards` is \"open\" or \"closed\"")
    scratch = e.get("scratch", {})
    if not isinstance(scratch, dict):
        out.append(f"{w}: [entry.scratch] maps file names to their source")
        scratch = {}
    for sname, spec in scratch.items():
        if not SCRATCH_NAME.fullmatch(sname):
            out.append(f"{w}: scratch file {sname!r}: a plain file name")
        if not isinstance(spec, dict) or len(spec) != 1 or set(spec) - set(SCRATCH_KEYS):
            out.append(f"{w}: scratch file {sname!r}: exactly one of text, copy, fence")
            continue
        (how, val), = spec.items()
        if not isinstance(val, str):
            out.append(f"{w}: scratch file {sname!r}: `{how}` is a string")
        elif how == "fence" and val != "above":
            out.append(f"{w}: scratch file {sname!r}: fence = \"above\" (the nearest "
                       "language-tagged fence above the pin line)")
        elif how == "copy":
            if ccm.is_reference(_norm_rel(val)):
                out.append(f"{w}: scratch file {sname!r} copies reference material")
            elif not (Path(root) / val).is_file():
                out.append(f"{w}: scratch file {sname!r} copies {val}, which does not exist")
    if scratch and cwd != "scratch":
        out.append(f"{w}: scratch files are written to the scratch directory: cwd = \"scratch\"")
    inputs = e.get("inputs", [])
    if not isinstance(inputs, list) or not all(isinstance(x, str) for x in inputs):
        out.append(f"{w}: `inputs` lists repo paths")
        inputs = []
    for x in inputs:
        if ccm.is_reference(_norm_rel(x)):
            out.append(f"{w}: input {x} is reference material")
        elif not (Path(root) / x).exists():
            out.append(f"{w}: input {x} does not exist")
    tool = cmd[0]
    words = [a.split("=", 1)[0] for a in cmd[1:]]
    for a in cmd[1:]:
        v = a.split("=", 1)[1] if a.startswith("--") and "=" in a else a
        if not v.startswith("-") and ccm.is_reference(_norm_rel(v)):
            out.append(f"{w}: `cmd` names reference material: a chapter never quotes it")
    values = _cmd_values(cmd)
    if tool in COURSE_TOOLS:
        bad = [x for x in words if x in TOOL_REFUSED[tool]]
        if bad:
            out.append(f"{w}: {tool} {bad[0]} is author-only or writes state: a chapter quotes "
                       "learner-safe runs only")
        if "--root" in words:
            out.append(f"{w}: --root is pins.py's to add")
        if tool == "scripts/firsttry.sh" and not any(x in FIRSTTRY_READ_ONLY for x in words):
            out.append(f"{w}: scripts/firsttry.sh is quoted with --report or --lint-hollow only "
                       "(its other modes record state)")
        if cwd == "scratch":
            named = [v for o, v in values if v in scratch]
            if tool == "scripts/vcheck" and named and "--module" not in words:
                out.append(f"{w}: a scratch probe runs with its module's pinned flags: "
                           "scripts/vcheck --module <ID> <probe> (spec §3.15 rule 8)")
    elif tool in TOOLCHAIN_BINARIES:
        if cwd != "scratch":
            out.append(f"{w}: a toolchain binary runs on scratch files: cwd = \"scratch\"")
        files = [v for o, v in values if re.search(r"\.(dfy|rs|toml)$", v)]
        stray = [v for v in files if v not in scratch]
        if not files or stray:
            out.append(f"{w}: a toolchain binary runs on the entry's scratch files only "
                       "([entry.scratch])")
    else:
        out.append(f"{w}: `cmd` starts with {tool!r}: a chapter quotes the course tools "
                   f"({', '.join(COURSE_TOOLS)}) or a pinned toolchain binary "
                   f"({', '.join(TOOLCHAIN_BINARIES)})")
    return out


def load_chapter_pins(root, mid):
    """(entries, problems) of expected/<ID>.chapter.toml; ([], []) when the
    file does not exist. Entries keep their TOML shape."""
    p = chapter_toml_path(root, mid)
    if not p.is_file():
        return [], []
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as err:
        return [], [f"{_toml_rel(mid)}: not valid TOML ({err})"]
    problems = []
    if data.get("schema") != CHAPTER_SCHEMA:
        problems.append(f"{_toml_rel(mid)}: schema = {CHAPTER_SCHEMA} is required")
    stray = sorted(set(data) - {"schema", "entry"})
    if stray:
        problems.append(f"{_toml_rel(mid)}: unknown top-level key(s) {', '.join(stray)}")
    entries = data.get("entry", [])
    if not isinstance(entries, list):
        return [], problems + [f"{_toml_rel(mid)}: `entry` is an array of tables ([[entry]])"]
    seen = set()
    for k, e in enumerate(entries, 1):
        problems += _entry_problems(root, mid, e, k)
        if isinstance(e, dict) and isinstance(e.get("id"), str):
            if e["id"] in seen:
                problems.append(f"{_toml_rel(mid)}: entry {e['id']} is defined twice")
            seen.add(e["id"])
    return [e for e in entries if isinstance(e, dict)], problems


def _toml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    raise ValueError(f"cannot write {type(v).__name__} to the chapter pin file")


def render_chapter_toml(mid, entries):
    """expected/<ID>.chapter.toml, canonically (pins.py --update writes it)."""
    out = [f"# {_toml_rel(mid)} — the chapter pins of {mid}'s chapter: one [[entry]] per",
           "# pinned output fence (`<!-- pin: <id> -->` above a bare fence). The schema is in",
           "# scripts/pins.py (\"Chapter fences\") and expected/README.md. Authors write the",
           "# entries; `scripts/pins.py --update --chapter " + mid + " [--entry ID]` captures them",
           "# (it fills [entry.pinned] and rewrites this file canonically: notes go in `note`).",
           f"schema = {CHAPTER_SCHEMA}"]
    order = [k for k in ENTRY_KEYS if k not in ("normalize", "scratch", "pinned")]
    for e in entries:
        out += ["", "[[entry]]"]
        out += [f"{k} = {_toml_value(e[k])}" for k in order if k in e]
        if e.get("normalize"):
            out.append("[entry.normalize]")
            out += [f"{k} = {_toml_value(e['normalize'][k])}" for k in NORMALIZE_KEYS
                    if k in e["normalize"]]
        for sname, spec in (e.get("scratch") or {}).items():
            out.append(f"[entry.scratch.{_toml_value(sname)}]")
            out += [f"{k} = {_toml_value(v)}" for k, v in spec.items()]
        if e.get("pinned"):
            out.append("[entry.pinned]")
            out.append(f"body = {_toml_value(e['pinned']['body'])}")
            if e["pinned"].get("inputs"):
                out.append("[entry.pinned.inputs]")
                out += [f"{_toml_value(k)} = {_toml_value(v)}"
                        for k, v in sorted(e["pinned"]["inputs"].items())]
    return "\n".join(out) + "\n"


def source_fence_above(fences, pin_line):
    """The body of the nearest language-tagged fence that closes above a pin
    line (the source the chapter shows), as file text."""
    best = None
    for f in fences:
        if f.close is not None and f.close < pin_line and f.info:
            best = f
    if best is None:
        raise ValueError("no language-tagged fence above the pin line")
    return "\n".join(best.body) + "\n"


def scratch_texts(root, e, fences, pin_line):
    """{scratch file name: text} of a command entry."""
    out = {}
    for sname, spec in (e.get("scratch") or {}).items():
        (how, val), = spec.items()
        if how == "text":
            out[sname] = val
        elif how == "copy":
            out[sname] = (Path(root) / val).read_text(encoding="utf-8")
        else:
            if pin_line is None:
                raise ValueError(f"scratch file {sname}: the entry has no pin line")
            out[sname] = source_fence_above(fences, pin_line)
    return out


def _file_hash(p):
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _expand_input(root, rel):
    p = Path(root) / rel
    if p.is_dir():
        return sorted(x.relative_to(root).as_posix() for x in p.rglob("*")
                      if x.is_file() and not any(s in INPUT_SKIP or s.endswith("-py")
                                                 for s in x.relative_to(p).parts))
    return [_norm_rel(rel)]


def entry_input_paths(root, e, modules=True):
    """The repo paths a command entry's output depends on: its `inputs`, the
    existing paths its command names (root cwd), every file of a module id it
    names (with the module's slot and calibration files; not the context
    module of `--module ID <probe>`; modules=False leaves these out) and the
    sources of its copied scratch files."""
    root = Path(root)
    rels = list(e.get("inputs", []))
    cmd = e.get("cmd", [])
    if cmd and cmd[0] in COURSE_TOOLS:
        for opt, v in _cmd_values(cmd):
            if opt == "--module" or ccm.is_reference(_norm_rel(v)):
                continue
            if core.ID_RE.fullmatch(v) and not (root / v).exists():
                if not modules:
                    continue
                try:
                    rec = core.record(root, v)
                except core.Refusal:
                    continue
                rels += core.expand_files(root, core.module_files(rec))
                rels += [f"slots/{rec['id']}.slots",
                         core.calib_path(root, rec["id"]).relative_to(root).as_posix()]
            elif e.get("cwd", "root") == "root" and (root / v).exists() and \
                    core.rel_to(root / v, root) is not None:
                rels.append(core.rel_to(root / v, root))
    for spec in (e.get("scratch") or {}).values():
        if "copy" in spec:
            rels.append(spec["copy"])
    out = []
    for r in rels:
        out += _expand_input(root, r)
    if modules and e.get("guards", "open") == "closed":
        # a quoted refusal holds only while the predictions it waits for are
        # unrecorded: their calibration files are inputs (absent as shipped),
        # so a learner's recorded first try makes the entry stale, never a
        # mismatch
        mods = {iid.split(".", 1)[0] for iid in entry_waits(root, e)}
        out += [core.calib_path(root, m).relative_to(root).as_posix() for m in sorted(mods)]
    return list(dict.fromkeys(out))


def entry_input_hashes(root, e, texts):
    out = {}
    for rel in entry_input_paths(root, e):
        p = Path(root) / rel
        out[rel] = _file_hash(p) if p.is_file() else ABSENT
    for sname, text in sorted(texts.items()):
        out[f"scratch:{sname}"] = SR.sr_sha256(text)
    return out


def entry_waits(root, e):
    """Item ids a command entry's output settles: its `answers`, and every
    `after:` item and slot-bearing item of the specimens it names itself (its
    `inputs`, its command's paths, its copied scratch files; a module id's
    files are not run as specimens by any quoted command)."""
    out = list(e.get("answers", []))
    for rel in entry_input_paths(root, e, modules=False):
        if not rel.endswith(".specimen") or not (Path(root) / rel).is_file():
            continue
        text = (Path(root) / rel).read_text(encoding="utf-8")
        out += [iid for _, iid in core.after_items(text)]
        items, _ = ci.parse_items(rel, text)
        out += [it["id"] for it in items if it["kind"] == "P" or it["slots"]]
    return list(dict.fromkeys(out))


def normalize_chapter_output(text, root, cwd, opts):
    """pins.py's normalization of a captured output (see the section header)."""
    text = ANSI.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
    subs = []
    if cwd is not None:
        subs += [str(Path(cwd).resolve()), str(Path(cwd))]
    for base in dict.fromkeys(subs):
        text = text.replace(base + "/", "").replace(base, ".")
    for base in dict.fromkeys([str(Path(root).resolve()), str(Path(root))]):
        text = text.replace(base + "/", "").replace(base, ".")
    sr = common.scratch_root()
    for base in dict.fromkeys([str(sr.resolve()), str(sr)]):
        text = re.sub(re.escape(base) + r"(?:/[^\s:'\"`,;)\]]*)?", "<scratch>/…", text)
    home = os.environ.get("HOME")
    if home and home != "/":
        text = text.replace(home, "~")
    lines = [x.rstrip() for x in text.split("\n")]
    for pat in opts.get("drop", []):
        lines = [x for x in lines if not re.search(pat, x)]
    for pat, repl in opts.get("replace", []):
        lines = [re.sub(pat, repl, x) for x in lines]
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and not lines[0].strip():
        lines.pop(0)
    return lines


def render_entry_body(e, lines, code):
    """The fence body of a command entry: [prompt] + output (or its excerpt and
    a "..." line) + [exit]. ValueError when the excerpt runs past the output."""
    n = e.get("normalize", {})
    shown = list(lines)
    if "excerpt" in e:
        a, b = e["excerpt"]
        if b > len(lines):
            raise ValueError(f"excerpt [{a}, {b}] runs past the {len(lines)}-line output")
        if a == 1 and b == len(lines):
            raise ValueError(f"excerpt [{a}, {b}] is the whole {len(lines)}-line output: drop "
                             "`excerpt` (a \"...\" line marks a cut)")
        shown = lines[a - 1:b] + ["..."]
    body = []
    if n.get("prompt", True):
        body.append("$ " + (e.get("display") or shlex.join(e["cmd"])))
    body += shown
    if n.get("exit", False):
        body += ["$ echo $?", str(code)]
    return body


def run_entry(root, mid, e, texts):
    """(normalized output lines, exit code) of one command entry."""
    root = Path(root)
    cmd = e["cmd"]
    work = raw = None
    try:
        if e.get("cwd", "root") == "scratch" or texts:
            work = common.scratch_dir(f"chapter-{mid}-{e['id']}")
            for sname, text in texts.items():
                (work / sname).write_text(text, encoding="utf-8")
        cwd = work if e.get("cwd", "root") == "scratch" else root
        if cmd[0] in COURSE_TOOLS:
            script = SCRIPTS / COURSE_TOOLS[cmd[0]]
            extra = [] if root.resolve() == core.REPO.resolve() else [f"--root={root}"]
            argv = [sys.executable, "-B", "-c", _BOOT, str(script), e.get("guards", "open"),
                    *extra, *cmd[1:]]
            env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1",
                   "DVL_SCRATCH": str(common.scratch_root())}
            try:
                p = subprocess.run(argv, cwd=str(cwd), env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                   timeout=ENTRY_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"the command ran past {ENTRY_TIMEOUT_S} s") from None
            text, code = p.stdout.decode("utf-8", "replace"), p.returncode
        else:
            tool = cmd[0]
            binary = common.toolchain(tool)[tool]
            pin = common.load_pins()[tool]
            env = V.job_env(work) if tool == "verus" else common.default_env()
            raw = common.scratch_dir(f"chapter-{mid}-{e['id']}-raw")
            code, so, _ = common.run_capped(["sh", "-c", 'exec "$0" "$@" 2>&1', str(binary),
                                             *cmd[1:]], pin["mem_gb"], pin["wall_clock_s"],
                                            env=env, cwd=work, pool=tool, out_dir=raw)
            text = Path(so).read_text(encoding="utf-8", errors="replace")
        if code in common.KILLED_EXITS:
            raise RuntimeError(f"killed(memory) (exit {code}), never a verdict")
        return normalize_chapter_output(text, root, work if cwd == work else None,
                                        e.get("normalize", {})), code
    finally:
        core.remove_tree(work)
        core.remove_tree(raw)


def _record_haystack(e):
    """The text of a recorded quote's source (JSON string values, decoded)."""
    src = Path(os.path.expanduser(e["source"]))
    text = src.read_text(encoding="utf-8")
    try:
        doc = json.loads(text)
    except ValueError:
        hay = text
    else:
        parts = []

        def walk(x):
            if isinstance(x, str):
                parts.append(x)
            elif isinstance(x, list):
                for y in x:
                    walk(y)
            elif isinstance(x, dict):
                for y in x.values():
                    walk(y)
        walk(doc)
        hay = "\n".join(parts)
    for pat, repl in e.get("normalize", {}).get("replace", []):
        hay = re.sub(pat, repl, hay)
    return hay


def recorded_mismatch(e, body):
    """The 1-based fence line of a recorded quote that its source does not
    hold verbatim, 0 when every line is there; OSError when the source cannot
    be read."""
    hay = _record_haystack(e)
    for k, x in enumerate(body, 1):
        s = x.strip()
        if s and s != "..." and s not in hay:
            return k
    return 0


@dataclasses.dataclass
class ChapterState:
    rel: str = ""                       # the chapter's repo path
    exists: bool = False
    lines: list = dataclasses.field(default_factory=list)
    fences: list = dataclasses.field(default_factory=list)
    quoted: list = dataclasses.field(default_factory=list)    # [(entry, fence)]
    stale: dict = dataclasses.field(default_factory=dict)     # id -> [changed inputs]
    problems: list = dataclasses.field(default_factory=list)
    entries: list = dataclasses.field(default_factory=list)


def chapter_static(root, rec, author_ok=None):
    """The static half of a module's chapter pins: the pin file's schema,
    pin lines against entries (each entry quoted exactly once, at a bare fence
    at column 0), each body hash, and the inputs as captured. A stale entry
    is listed in `stale`; it is a problem only when author_ok (the author's
    context). No command runs."""
    root = Path(root)
    mid = rec["id"]
    st = ChapterState(rel=rec["chapter"])
    entries, st.problems = load_chapter_pins(root, mid)
    st.entries = entries
    cp = root / st.rel
    has_toml = chapter_toml_path(root, mid).is_file()
    if not cp.is_file():
        if has_toml:
            st.problems.append(f"{_toml_rel(mid)}: pins a chapter that does not exist ({st.rel})")
        return st
    st.exists = True
    st.lines = cp.read_text(encoding="utf-8").split("\n")
    st.fences, dangling = parse_chapter(st.lines)
    for i, pid in dangling:
        st.problems.append(f"{st.rel}:{i + 1}: the pin line {pid!r} is not followed by a fence")
    by_id = {e["id"]: e for e in entries if isinstance(e.get("id"), str)}
    seen = {}
    for f in st.fences:
        if f.pin is None:
            continue
        where = f"{st.rel}:{f.pin_line + 1}"
        if not PIN_ID.fullmatch(f.pin):
            st.problems.append(f"{where}: a pin id is lower-case letters, digits, '.', '_' and "
                               "'-'")
            continue
        if f.info:
            st.problems.append(f"{where}: pin {f.pin}: an output fence is bare (drop its "
                               f"{f.info.split()[0]!r} tag; source fences carry the tag)")
        if f.indent:
            st.problems.append(f"{where}: pin {f.pin}: a pinned fence starts at column 0")
        if f.close is None:
            st.problems.append(f"{where}: pin {f.pin}: the fence is never closed")
        if f.pin in seen:
            st.problems.append(f"{where}: pin {f.pin} is quoted twice (also at line "
                               f"{seen[f.pin] + 1}): one fence per entry")
            continue
        seen[f.pin] = f.pin_line
        if f.pin not in by_id:
            st.problems.append(f"{where}: pin {f.pin} names no entry of {_toml_rel(mid)}")
            continue
        st.quoted.append((by_id[f.pin], f))
    dangling_ids = {pid for _, pid in dangling}
    for e in entries:
        eid = e.get("id")
        if isinstance(eid, str) and eid not in seen and eid not in dangling_ids:
            st.problems.append(f"{_toml_rel(mid)}: entry {eid} is quoted nowhere in {st.rel} (a "
                               "pin that matches nothing is an error)")
    for e, f in st.quoted:
        where = f"{st.rel}:{f.open + 1}"
        pinned = e.get("pinned")
        if not isinstance(pinned, dict) or not _is_hex(pinned.get("body")):
            st.problems.append(f"{where}: pin {e['id']}: not captured yet: run scripts/pins.py "
                               f"--update --chapter {mid} --entry {e['id']}")
            continue
        if SR.sr_sha256("\n".join(f.body)) != pinned["body"]:
            st.problems.append(f"{where}: pin {e['id']}: the fence differs from its capture (an "
                               "edit by hand): re-capture with scripts/pins.py --update "
                               f"--chapter {mid} --entry {e['id']}")
        if e.get("kind", "command") != "command" or not isinstance(e.get("cmd"), list):
            continue
        try:
            got = entry_input_hashes(root, e, scratch_texts(root, e, st.fences, f.pin_line))
        except (OSError, ValueError, KeyError) as err:
            st.problems.append(f"{where}: pin {e['id']}: its inputs cannot be read ({err})")
            continue
        want = pinned.get("inputs", {})
        changed = sorted(k for k in set(got) | set(want) if got.get(k) != want.get(k))
        if changed:
            st.stale[e["id"]] = changed
            if author_ok:
                st.problems.append(f"{where}: pin {e['id']}: stale: {len(changed)} input(s) "
                                   f"changed since the capture ({', '.join(changed[:3])}"
                                   f"{', …' if len(changed) > 3 else ''}; spec §3.15 rule 9): "
                                   f"re-capture with scripts/pins.py --update --chapter {mid} "
                                   f"--entry {e['id']}")
    return st


def unrecorded_waits(root, e):
    """The predictions a command entry's output settles whose first try is
    not recorded yet (calibration files)."""
    calib = {}
    out = []
    for iid in entry_waits(root, e):
        m = iid.split(".", 1)[0]
        if m not in calib:
            calib[m] = core.read_calib(root, m)
        if iid not in calib[m]:
            out.append(iid)
    return out


def check_chapter(root, rec, author_ok, only=None):
    """(problems, checks, skipped, held) of a module's chapter pins: the
    static half, then every quoted, captured, fresh command entry re-run and
    compared with its fence (recorded quotes: verbatim against the record in
    the author's context). skipped: stale entries outside the author's
    context. held: outside the author's context, a guards = "open" entry
    whose output settles a prediction with no recorded first try is not run
    (H5: the run would compute the answer, even unseen). only: entry ids to
    restrict the run to."""
    st = chapter_static(root, rec, author_ok)
    problems, checks, skipped, held = list(st.problems), 0, 0, 0
    for e, f in st.quoted:
        if only and e["id"] not in only:
            continue
        where = f"{st.rel}:{f.open + 1}"
        pinned = e.get("pinned")
        if not isinstance(pinned, dict) or not _is_hex(pinned.get("body")):
            continue
        checks += 1
        if e.get("kind", "command") == "recorded":
            if author_ok:
                try:
                    k = recorded_mismatch(e, f.body)
                except OSError as err:
                    problems.append(f"{where}: pin {e['id']}: its record cannot be read "
                                    f"({type(err).__name__})")
                    continue
                if k:
                    problems.append(f"{where}: pin {e['id']}: fence line {k} is not verbatim in "
                                    "its record")
            continue
        if e["id"] in st.stale:
            checks -= 1
            if not author_ok:
                skipped += 1
            continue
        if not author_ok and e.get("guards", "open") == "open":
            try:
                waiting = unrecorded_waits(root, e)
            except (OSError, ValueError):
                waiting = []
            if waiting:
                checks -= 1
                held += 1
                continue
        try:
            texts = scratch_texts(root, e, st.fences, f.pin_line)
            lines, code = run_entry(root, rec["id"], e, texts)
            body = render_entry_body(e, lines, code)
        except (OSError, ValueError, RuntimeError, common.DvlError) as err:
            problems.append(f"{where}: pin {e['id']}: could not run ({err})")
            continue
        if body != f.body:
            k = next((i for i, (x, y) in enumerate(zip(body, f.body)) if x != y),
                     min(len(body), len(f.body)))
            problems.append(f"{where}: pin {e['id']}: the fence differs from the captured output "
                            f"at fence line {k + 1} ({len(f.body)} line(s) in the fence, "
                            f"{len(body)} captured)")
    return problems, checks, skipped, held


def held_note(tool, held):
    return (f"{tool}: {held} pin(s) not run: their output settles predictions whose first try "
            "is not recorded (H5); they run once you record them with scripts/firsttry.sh "
            "<ID> --check, and the author's CI checks them")


def mode_chapter(root, mid, only):
    rec = core.record(root, mid)
    author_ok = core.author_gate(root) is None
    if not (Path(root) / rec["chapter"]).is_file() and not chapter_toml_path(root, mid).is_file():
        print(f"pins --chapter {rec['id']}: {rec['chapter']} does not exist and nothing is pinned "
              "(an empty set fails)")
        return core.EXIT_FAIL
    if only:
        entries, _ = load_chapter_pins(root, rec["id"])
        unknown = [x for x in only if x not in {e.get("id") for e in entries}]
        if unknown:
            raise core.Usage(f"--entry {unknown[0]}: no such entry in {_toml_rel(rec['id'])}")
    problems, checks, skipped, held = check_chapter(root, rec, author_ok, only)
    for p in problems:
        print(p)
    if skipped:
        print(f"pins --chapter {rec['id']}: {skipped} pin(s) skipped: their inputs differ from "
              "the files they were captured on (your own work, not the course as shipped); the "
              "author's CI checks them")
    if held:
        print(held_note(f"pins --chapter {rec['id']}", held))
    if not checks and not problems and not skipped and not held:
        print(f"pins --chapter {rec['id']}: no pinned fence in {rec['chapter']} (an empty set "
              "fails)")
        return core.EXIT_FAIL
    print(f"pins --chapter {rec['id']}: {checks} pin(s) checked; {len(problems)} problem(s)")
    return core.EXIT_OK if not problems else core.EXIT_FAIL


def _fence_lines(body):
    run = max([len(m.group(0)) for x in body for m in [re.match(r"^\s*(`+)", x)] if m] + [2])
    mark = "`" * max(3, run + 1)
    return [mark] + body + [mark]


def mode_chapter_update(root, mid, only):
    core.require_author(root, "pins.py --update --chapter")
    root = Path(root)
    rec = core.record(root, mid)
    mid = rec["id"]
    cp = root / rec["chapter"]
    if not cp.is_file():
        raise core.Refusal(f"{rec['chapter']} does not exist: write the chapter, with a "
                           "`<!-- pin: <id> -->` line above each output fence, first")
    entries, problems = load_chapter_pins(root, mid)
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        raise core.Refusal(f"{_toml_rel(mid)} has {len(problems)} schema problem(s) (above)")
    if not entries:
        raise core.Refusal(f"{_toml_rel(mid)} holds no entry (an empty set fails)")
    lines = cp.read_text(encoding="utf-8").split("\n")
    fences, dangling = parse_chapter(lines)
    where_of = {}
    for f in fences:
        if f.pin is not None and f.pin not in where_of:
            where_of[f.pin] = (f.pin_line, f)
    for i, pid in dangling:
        where_of.setdefault(pid, (i, None))
    ids = [e["id"] for e in entries]
    for x in only:
        if x not in ids:
            raise core.Usage(f"--entry {x}: no such entry in {_toml_rel(mid)}")
    chosen = [e for e in entries if not only or e["id"] in only]
    for e in chosen:
        if e["id"] not in where_of:
            raise core.Refusal(f"entry {e['id']} is quoted nowhere: add `<!-- pin: {e['id']} -->` "
                               f"above its fence in {rec['chapter']}")
    original = "\n".join(lines)
    edits, failed = [], []
    for e in chosen:
        pin_line, f = where_of[e["id"]]
        if f is not None and (f.info or f.indent or f.close is None):
            failed.append(f"{rec['chapter']}:{f.open + 1}: pin {e['id']}: its fence must be bare, "
                          "closed and at column 0")
            continue
        if e.get("kind", "command") == "recorded":
            if f is None or not f.body:
                failed.append(f"{rec['chapter']}:{pin_line + 1}: pin {e['id']}: a recorded "
                              "quote's fence holds the author's verbatim copy: write it first")
                continue
            try:
                k = recorded_mismatch(e, f.body)
            except OSError as err:
                failed.append(f"entry {e['id']}: its record {e['source']} cannot be read "
                              f"({type(err).__name__})")
                continue
            if k:
                failed.append(f"{rec['chapter']}:{f.open + 1 + k}: pin {e['id']}: this line is "
                              "not verbatim in its record")
                continue
            e["pinned"] = {"body": SR.sr_sha256("\n".join(f.body))}
            print(f"pins --update --chapter {mid}: {e['id']}: recorded quote checked against its "
                  f"record ({len(f.body)} line(s))")
            continue
        try:
            texts = scratch_texts(root, e, fences, pin_line)
            out, code = run_entry(root, mid, e, texts)
            body = render_entry_body(e, out, code)
        except common.ToolchainError:
            raise
        except (OSError, ValueError, RuntimeError, common.DvlError) as err:
            failed.append(f"entry {e['id']}: {err}")
            continue
        e["pinned"] = {"body": SR.sr_sha256("\n".join(body)),
                       "inputs": entry_input_hashes(root, e, texts)}
        edits.append((pin_line, f, body))
        print(f"pins --update --chapter {mid}: {e['id']}: captured ({len(body)} fence line(s), "
              f"exit {code})")
    if cp.read_text(encoding="utf-8") != original:
        raise core.Refusal(f"{rec['chapter']} changed while the entries ran: nothing written; "
                           "run the capture again")
    for pin_line, f, body in sorted(edits, key=lambda x: x[0], reverse=True):
        new = _fence_lines(body)
        if f is None:
            lines[pin_line + 1:pin_line + 1] = new
        else:
            lines[f.open:f.close + 1] = new
    if edits:
        cp.write_text("\n".join(lines), encoding="utf-8")
    chapter_toml_path(root, mid).write_text(render_chapter_toml(mid, entries), encoding="utf-8")
    done = len(chosen) - len(failed)
    print(f"pins --update --chapter {mid}: {done} entr{'y' if done == 1 else 'ies'} pinned; wrote "
          f"{rec['chapter']} and {_toml_rel(mid)}")
    for x in failed:
        print(f"pins --update --chapter {mid}: not captured: {x}", file=sys.stderr)
    if failed:
        n = len(failed)
        print(f"pins --update --chapter {mid}: {n} entr{'y' if n == 1 else 'ies'} not captured "
              "(above); their fences and pins are unchanged", file=sys.stderr)
        return core.EXIT_FAIL
    return core.EXIT_OK


# =====================================================================================
# Modes
# =====================================================================================

def module_scope(root, rec):
    """Every existing Dafny/Verus file of a module (exercises with specimens,
    exits, agentic files)."""
    rels = core.expand_files(root, core.module_files(rec),
                             (".dfy", ".rs", ".dfy.specimen", ".rs.specimen"))
    return [r for r in rels if (Path(root) / r).is_file()]


def mode_learner(root, mid):
    rec = core.record(root, mid)
    items, errs = core.module_items(root, rec)
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        return core.EXIT_FAIL
    calib = core.read_calib(root, rec["id"])
    blocked = sorted({it["id"] for it in items for s in it["slots"]
                      if s["state"] == "enabled" and it["id"] not in calib})
    results = run_slot_checks(root, rec, items,
                              select=lambda it, s: s["state"] == "enabled" and it["id"] in calib,
                              tag="pins")
    n_ok = n_bad = 0
    print(f"pins {rec['id']}: enabled slots")
    for iid in sorted(results):
        checks = results[iid]
        ok = all(c.outcome == "pass" for c in checks)
        n_ok += ok
        n_bad += not ok
        where = ", ".join(f"{c.file}:{c.line}" for c in checks if c.outcome != "pass")
        print(f"  {'✓' if ok else '✗'} {iid}" + (f"  {where}" if where else "")
              + "".join(f" (could not run: {c.why})" for c in checks if c.outcome == "error"))
    for iid in blocked:
        n_bad += 1
        print(f"  · {iid}  enabled, but its first try is not recorded: run "
              f"scripts/firsttry.sh {rec['id']} --check first (not run, H5)")
    # files the module shipped with (vcheck's shipped_base) that are gone
    gone = core.gone_files(root, rec["exercises"] + rec["exits"])
    shipped = core.shipped_slot_items(root, rec["id"], gone) if gone else {}
    for iid, (sit, _) in sorted(shipped.items()):
        if sit["slots"] or sit["kind"] == "P":
            n_bad += 1
            print(f"  · {iid}  its file {sit['file']} is gone since it shipped: restore it "
                  "(its slots are missing)")
    print(f"pins {rec['id']}: {n_ok} pass, {n_bad} not" + ("" if n_ok + n_bad else
                                                          " (no enabled slot yet)"))
    return core.EXIT_OK if not n_bad else core.EXIT_FAIL


def pin_hygiene(root, rec, items):
    """Problems of expected/<ID>.pins: malformed, stale, missing or legacy
    (unsalted) pins."""
    table, errs = read_pins(root, rec["id"])
    verdicts = {it["id"].split(".", 1)[1] for it in items if it["format"] == "verdict"}
    for local, (ln, _, keyword) in sorted(table.items()):
        if local not in verdicts:
            errs.append(f"{EXPECTED}/{rec['id']}.pins:{ln}: {local} names no verdict item of "
                        f"{rec['id']} (a pin that matches nothing is an error)")
        if keyword == LEGACY_PIN_KEYWORD:
            errs.append(f"{EXPECTED}/{rec['id']}.pins:{ln}: {local} is a legacy unsalted pin, "
                        "which no tool reads any more: re-pin with scripts/pins.py --update "
                        f"--ref --module {rec['id']}")
    for local in sorted(verdicts - set(table)):
        errs.append(f"{EXPECTED}/{rec['id']}.pins:0: verdict item {rec['id']}.{local} has no pin")
    return errs, len(table)


def verdict_ref_problems(root, mid, verdicts, table, missing_pin=True):
    """(problems, checks): every verdict pin against the hash of the reference
    answer in <ref>/slots/<ID>.slots (static; locations only). missing_pin:
    report a verdict item with no pin (pin_hygiene already does in --ci)."""
    rslots = ref_rel(f"slots/{mid}.slots")
    rvals = slot_values(root, rslots)
    problems, checks = [], 0
    for it in verdicts:
        local = it["id"].split(".", 1)[1]
        checks += 1
        if local not in rvals:
            problems.append(f"{rslots}:0: {it['id']}: no reference answer")
        elif local not in table:
            if missing_pin:
                problems.append(f"{EXPECTED}/{mid}.pins:0: {it['id']}: no pin")
        elif not pin_matches(mid, local, rvals[local][1], table[local]):
            problems.append(f"{rslots}:{rvals[local][0]}: {it['id']}: the reference answer "
                            "does not match its pin")
    return problems, checks


def count_hygiene(root, rec):
    """(problems, checks) of expected/<ID>.counts (Δ11): one pin per unit of
    the module, no pin for anything else, and every pinned symbol still a
    learner-declared declaration with a contract (static; vcheck --ref
    compares the counts with the twins)."""
    mid, units = rec["id"], rec["units"]
    rel = f"{EXPECTED}/{mid}.counts"
    table, problems = core.read_counts(root, mid)
    if table is None:
        if units:
            return [f"{rel}:0: {mid} has {len(units)} verification unit(s) and no count pin "
                    f"(Δ11; the author writes it with vcheck --ref --pin-counts {mid})"], 0
        return [], 0
    checks = 0
    for unit in units:
        if unit not in table:
            problems.append(f"{rel}:0: unit {unit} has no count pin")
    for unit, e in sorted(table.items()):
        checks += 1
        if unit not in units:
            problems.append(f"{rel}:0: {unit} is not a unit of {mid} (a pin that matches nothing "
                            "is an error)")
            continue
        lang = core.gu.unit_kind(unit)[0]
        if e["lang"] != core.POOL[lang]:
            problems.append(f"{rel}:0: {unit} is a {core.POOL[lang]} unit, pinned as {e['lang']}")
            continue
        if e["min_verified"] < len(e["symbols"]):
            problems.append(f"{rel}:0: {unit}: min_verified is below its {len(e['symbols'])} "
                            "pinned symbol(s)")
        if not (Path(root) / unit).is_dir():
            continue                     # reported as a missing unit elsewhere
        try:
            contract = core.contract_symbols(root, unit, lang)
        except (ValueError, OSError) as err:
            problems.append(f"{rel}:0: {unit}: its files do not parse ({err})")
            continue
        stale = [s for s in e["symbols"] if s not in contract]
        if stale:
            problems.append(f"{rel}:0: {unit}: {len(stale)} pinned symbol(s) no longer declared "
                            f"with a contract in its learner files ({', '.join(stale)}): a stale "
                            f"pin; re-pin with vcheck --ref --pin-counts {mid}")
    fp, fn = file_pin_hygiene(root, rec)
    return problems + fp, checks + fn


def file_pin_hygiene(root, rec):
    """(problems, checks) of the [[file]] tables of expected/<ID>.counts
    (schema 2, the Q8 decision): one shipped-state pin per exercise, check,
    exit and agent file of the module, each with the file's role, and no pin
    for anything else (static; vcheck --shipped compares the states)."""
    mid = rec["id"]
    rel = f"{EXPECTED}/{mid}.counts"
    if core.read_counts(root, mid)[0] is None:
        return [], 0                     # no count pin at all: count_hygiene says so
    table, problems = core.read_file_pins(root, mid)
    if problems:
        return problems, 0
    if table is None:
        return [f"{rel}:0: {mid} pins no file's shipped state (a schema-1 pin: no [[file]] "
                f"table, Q8); re-pin with vcheck --ref --pin-counts {mid}"], 0
    listed = {r: role for r, role, _ in core.module_pin_files(root, rec)}
    checks = 0
    for f, e in sorted(table.items()):
        checks += 1
        if f not in listed:
            problems.append(f"{rel}:0: {f} is no exercise, check, exit or agent file of {mid} (a "
                            "pin that matches nothing is an error)")
        elif listed[f] != e["role"]:
            problems.append(f"{rel}:0: {f} is pinned as {e['role']}, but it is {mid}'s "
                            f"{listed[f]} file")
    for f in sorted(set(listed) - set(table)):
        problems.append(f"{rel}:0: {f} has no shipped-state pin; re-pin with vcheck --ref "
                        f"--pin-counts {mid}")
    return problems, checks


def compare_golden(root, rel, sidecar, cache):
    """Problems (locations only) of one sidecar."""
    try:
        command, want = read_sidecar(sidecar)
    except ValueError as e:
        return [str(e)]
    if not (Path(root) / rel).is_file():
        return [f"{core.show(sidecar, root)}: stale sidecar: its source {rel} is gone"]
    seal = seal_key(root, rel)
    sealed = split_sealed(want)
    where = core.show(sidecar, root)
    if seal is not None and sealed is None:
        return [f"{where}: an unsealed sidecar of a demo that waits for {', '.join(seal[1])}: "
                f"it shows the outcome before the prediction; re-pin with scripts/pins.py "
                f"--update {rel}"]
    if seal is None and sealed is not None:
        return [f"{where}: a sealed sidecar of {rel}, which has no `after:` line: re-pin with "
                f"scripts/pins.py --update {rel}"]
    out = []
    if sealed is not None:
        ids, digest, shown = sealed
        if ids != seal[1]:
            return [f"{where}: sealed for {', '.join(ids)}, but {rel} waits for "
                    f"{', '.join(seal[1])}: re-pin with scripts/pins.py --update {rel}"]
        if shown:
            out.append(f"{where}: a sealed sidecar that still shows {len(shown)} output line(s) "
                       f"(the pre-DV2b form): re-pin with scripts/pins.py --update {rel}")
    key = (rel, command)
    if key not in cache:
        cache[key] = golden(root, rel, command)
    got, res = cache[key]
    raw = f"; raw output: {res.raw_dir}" if res.raw_dir else ""
    if sealed is not None:
        if sealed_hash(seal[0], sealed[0], rel, got) != sealed[1]:
            out.append(f"{rel}: golden mismatch: the sealed output differs; pinned in {where}"
                       + raw)
        return out
    if got == want:
        return []
    k = next((i for i, (x, y) in enumerate(zip(got, want)) if x != y), min(len(got), len(want)))
    return [f"{rel}: golden mismatch at normalized line {k + 1} (pinned {len(want)} lines, got "
            f"{len(got)}); pinned in {where}" + raw]


def mode_ci(root, only):
    # Learner-visible pins run anywhere; the reference half (verdict pins
    # against the reference answers) only where the author self-gate passes.
    no_ref = core.author_gate(root)
    if only:
        mids, idle = [core.record(root, only)["id"]], None
    else:
        mids, idle = core.armed_or_none(root)
    problems, checks = [], 0
    cache, verify_cache = {}, {}
    scope_files = set()
    chapter_skipped = chapter_held = 0
    for mid in mids:
        rec = core.record(root, mid)
        items, errs = core.module_items(root, rec)
        problems += errs
        perrs, npins = pin_hygiene(root, rec, items)
        problems += perrs
        checks += npins
        if no_ref is None and (Path(root) / ref_rel(f"slots/{mid}.slots")).is_file():
            table, _ = read_pins(root, mid)
            vp, vn = verdict_ref_problems(root, mid, [it for it in items
                                                      if it["format"] == "verdict"], table,
                                          missing_pin=False)
            problems += vp
            checks += vn
        cp, cn = count_hygiene(root, rec)
        problems += cp
        checks += cn
        if (Path(root) / rec["chapter"]).is_file() or chapter_toml_path(root, mid).is_file():
            cp, cn, cs, ch = check_chapter(root, rec, no_ref is None)
            problems += cp
            checks += cn
            chapter_skipped += cs
            chapter_held += ch
        for rel in module_scope(root, rec):
            scope_files.add(rel)
            text = (Path(root) / rel).read_text(encoding="utf-8")
            pins_here = author_expects(rel, text, items)
            if not pins_here:
                continue
            if rel not in verify_cache:
                verify_cache[rel] = core.lib(core.lang_of(rel)).verify(str(Path(root) / rel))
            res = verify_cache[rel]
            tpath = str((Path(root) / rel).resolve())
            diags = _diags_with_holes(res)
            for pin_ln, line, frag in pins_here:
                checks += 1
                if _no_verdict(res):
                    problems.append(f"{rel}:{pin_ln}: no verdict ({res.verdict}); raw output: "
                                    f"{res.raw_dir}")
                elif not any(d.file == tpath and d.line == line and frag in d.message
                             for d in diags):
                    problems.append(f"{rel}:{pin_ln}: EXPECT pin not matched")
    exp = Path(root) / EXPECTED
    sidecars = sorted(exp.rglob("*.expect")) if exp.is_dir() else []
    for sc in sidecars:
        rel = sidecar_source(root, sc)
        if only and rel not in scope_files and (Path(root) / rel).exists():
            continue
        checks += 1
        src = Path(root) / rel
        if src.is_file() and slot_bearing(rel, src.read_text(encoding="utf-8")):
            problems.append(f"{core.show(sc, root)}: a sidecar of {rel}, whose items carry "
                            "prediction slots: it holds their answers (H5); delete it and pin "
                            "them through the twin (pins.py --ref) or as hashes")
            continue
        problems += compare_golden(root, rel, sc, cache)
    if not only:
        live = set(mids)
        for f in sorted(exp.glob("*.counts")) if exp.is_dir() else []:
            if f.stem not in live:
                checks += 1
                problems.append(f"{core.show(f, root)}: {f.stem} is not a non-planned module (a "
                                "pin that matches nothing is an error)")
        for f in sorted(exp.glob("*.chapter.toml")) if exp.is_dir() else []:
            if f.name.split(".", 1)[0] not in live:
                checks += 1
                problems.append(f"{core.show(f, root)}: {f.name.split('.', 1)[0]} is not a "
                                "non-planned module (a pin that matches nothing is an error)")
    for p in problems:
        print(p)
    if not checks and not problems:
        if idle:
            print(f"pins --ci: {idle}; 0 sidecars, 0 count pins: passing loudly")
            return core.EXIT_OK
        print(f"pins --ci: nothing pinned ({len(mids)} non-planned module(s), 0 sidecars); an "
              "empty set fails")
        return core.EXIT_FAIL
    if chapter_skipped:
        print(f"pins --ci: {chapter_skipped} chapter pin(s) skipped: their inputs differ from the "
              "files they were captured on (your own work, not the course as shipped); the "
              "author's CI checks them")
    if chapter_held:
        print(held_note("pins --ci", chapter_held))
    if no_ref is not None and mids:
        print(f"pins --ci: the reference half (verdict pins against the reference answers) "
              f"skipped: not the author's context ({no_ref}); pins.py --ref runs it there")
    print(f"pins --ci: {checks} pin(s) checked over {len(mids)} module(s); {len(problems)} "
          "problem(s)")
    return core.EXIT_OK if not problems else core.EXIT_FAIL


def mode_update(root, files, only):
    core.require_author(root, "pins.py --update")
    exp = Path(root) / EXPECTED
    targets = []
    if files:
        for f in files:
            p = Path(f) if Path(f).is_absolute() else Path.cwd() / f
            rel = core.rel_to(p, root)
            if rel is None or not p.is_file() or core.lang_of(p) is None:
                raise core.Refusal(f"{f}: not a Dafny or Verus file of this checkout")
            if core.is_reference_path(p, root):
                raise core.Refusal(f"{f}: reference material is never pinned in expected/")
            held = slot_bearing(rel, p.read_text(encoding="utf-8"))
            if held:
                raise core.Refusal(f"{rel} carries prediction slots ({', '.join(held)}): a "
                                   "sidecar of it would hold their answers (H5); pin them through "
                                   "the twin (pins.py --ref) or as hashes")
            sc = sidecar_path(root, rel)
            command = read_sidecar(sc)[0] if sc.is_file() else "verify"
            targets.append((rel, sc, command))
    else:
        scope = None
        if only:
            scope = set(module_scope(root, core.record(root, only)))
        for sc in (sorted(exp.rglob("*.expect")) if exp.is_dir() else []):
            rel = sidecar_source(root, sc)
            if scope is not None and rel not in scope:
                continue
            if not (Path(root) / rel).is_file():
                print(f"{core.show(sc, root)}: stale (its source is gone); delete it by hand")
                continue
            if slot_bearing(rel, (Path(root) / rel).read_text(encoding="utf-8")):
                raise core.Refusal(f"{core.show(sc, root)}: its source {rel} carries prediction "
                                   "slots; delete the sidecar (H5) and pin them through the twin")
            targets.append((rel, sc, read_sidecar(sc)[0]))
    if not targets:
        print("pins --update: nothing to update (name a file, or create sidecars first; an "
              "empty set fails)")
        return core.EXIT_FAIL
    for rel, sc, command in targets:
        body, res = golden(root, rel, command)
        seal = seal_key(root, rel)
        sc.parent.mkdir(parents=True, exist_ok=True)
        if seal is not None:
            mid, ids = seal
            sc.write_text(render_sidecar(rel, command, body,
                                         (mid, ids, sealed_hash(mid, ids, rel, body))),
                          encoding="utf-8")
            print(f"pins --update: wrote {core.show(sc, root)} (sealed for {', '.join(ids)}: one "
                  "hash, no output line)")
            continue
        sc.write_text(render_sidecar(rel, command, body), encoding="utf-8")
        print(f"pins --update: wrote {core.show(sc, root)} ({res.verdict}, {len(body)} lines)")
    return core.EXIT_OK


def ref_rel(rel):
    return f"{core.REF_DIR}/{rel}"


def mode_ref(root, only, update):
    core.require_author(root, "pins.py --ref")
    if update and not only:
        raise core.Usage("--update --ref writes one module's pins: add --module ID")
    if only:
        mids, idle = [core.record(root, only)["id"]], None
    else:
        mids, idle = core.armed_or_none(root)
    if idle:
        print(f"pins --ref: {idle}: passing loudly")
        return core.EXIT_OK
    problems, checks = [], 0
    for mid in mids:
        rec = core.record(root, mid)
        items, errs = core.module_items(root, rec)
        problems += errs
        verdicts = [it for it in items if it["format"] == "verdict"]
        rslots = ref_rel(f"slots/{mid}.slots")
        rvals = slot_values(root, rslots)
        if update:
            if not rvals:
                raise core.Refusal(f"{rslots}: no reference answers to pin")
            lines = [f"# {EXPECTED}/{mid}.pins — one salted sha256 per verdict answer: "
                     f"sha256 of \"{mid}:<item id>:<answer>\",",
                     "# the answer normalized (trimmed, whitespace collapsed). Written by",
                     f"# `scripts/pins.py --update --ref --module {mid}` from the reference "
                     "answers. Never the answer itself."]
            missing = []
            for it in verdicts:
                local = it["id"].split(".", 1)[1]
                if local not in rvals or rvals[local][1].strip() == "???":
                    missing.append(it["id"])
                    continue
                lines.append(f"{local}  {SALTED_PIN_KEYWORD} "
                             f"{pin_hash(mid, local, rvals[local][1])}")
            if missing:
                raise core.Refusal(f"{rslots}: no reference answer for {' '.join(missing)}")
            if not verdicts:
                raise core.Refusal(f"{mid} has no verdict item (an empty pin file fails)")
            p = pins_path(root, mid)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"pins --update --ref: wrote {core.show(p, root)} ({len(verdicts)} pin(s))")
            continue
        table, perrs = read_pins(root, mid)
        problems += perrs
        vp, vn = verdict_ref_problems(root, mid, verdicts, table)
        problems += vp
        checks += vn
        for lrel in module_scope(root, rec):
            trel = ref_rel(lrel)
            tw = Path(root) / trel
            if not tw.is_file():
                continue
            titems, terrs = ci.parse_items(trel, tw.read_text(encoding="utf-8"))
            problems += [f"{e.split(':', 2)[0]}:{e.split(':', 2)[1]}: item grammar" for e in terrs]
            if not any(s["format"] != "verdict" for it in titems for s in it["slots"]):
                continue
            for it in titems:
                for s in it["slots"]:
                    if s["state"] != "enabled":
                        problems.append(f"{trel}:{s['line']}: {it['id']}: a reference slot is "
                                        "not enabled")
            copy_as = {} if lrel.startswith("specimens/") else {trel: lrel}
            res = run_slot_checks(root, rec, titems,
                                  select=lambda it, s: s["state"] == "enabled" and
                                  s["format"] != "verdict", tag="ref", copy_as=copy_as)
            for iid, cs in res.items():
                for c in cs:
                    checks += 1
                    if c.outcome != "pass":
                        problems.append(f"{c.file}:{c.line}: {iid}: reference slot "
                                        f"{'fails' if c.outcome == 'fail' else 'did not run'}")
    if update:
        return core.EXIT_OK
    for p in problems:
        print(p)
    if not checks and not problems and only:
        # one module named (--module): a module with no verdict item and no reference
        # slot has nothing for --ref to check; the whole run's empty set still fails
        # (DV5c gaps lane: Q16 has no slot)
        print(f"pins --ref: {mids[0]} has no verdict item and no reference slot: nothing to "
              "check for it (passing loudly; a run over every armed module with nothing to "
              "check fails)")
        return core.EXIT_OK
    if not checks and not problems:
        print(f"pins --ref: nothing to check ({len(mids)} module(s)); an empty set fails")
        return core.EXIT_FAIL
    print(f"pins --ref: {checks} check(s); {len(problems)} problem(s)")
    return core.EXIT_OK if not problems else core.EXIT_FAIL


def main(argv=None):
    rc = _main(argv)
    if common.trust_note():
        print(f"pins: {common.trust_note()}: every result above ran on a toolchain other "
              "than the pinned one, so none of it is the course's pinned result (DELTAS Δ503, D79)")
    return rc


def _main(argv=None):
    ap = argparse.ArgumentParser(prog="pins.py", description="The golden harness.")
    ap.add_argument("args", nargs="*", metavar="ID|FILE")
    ap.add_argument("--ci", action="store_true")
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--ref", action="store_true")
    ap.add_argument("--module", metavar="ID")
    ap.add_argument("--chapter", metavar="ID")
    ap.add_argument("--entry", action="append", default=[], metavar="E")
    # Kept so a caller written before DV1c still parses; it no longer changes
    # anything: no armed module passes loudly by itself, and with armed
    # modules an empty set fails (empty lists fail).
    ap.add_argument("--allow-empty", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--root", type=Path, default=core.REPO, help=argparse.SUPPRESS)
    try:
        a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as e:
        return core.EXIT_USAGE if e.code else 0
    root = a.root.resolve()
    try:
        if a.ci and (a.update or a.ref or a.chapter):
            raise core.Usage("--ci runs alone")
        if a.entry and not a.chapter:
            raise core.Usage("--entry goes with --chapter ID")
        if a.chapter:
            if a.ref or a.module or a.args:
                raise core.Usage("usage: pins.py [--update] --chapter ID [--entry E ...]")
            if a.update:
                return mode_chapter_update(root, a.chapter, a.entry)
            return mode_chapter(root, a.chapter, a.entry)
        if a.ci:
            if a.args:
                raise core.Usage("--ci takes no positional argument (use --module ID)")
            return mode_ci(root, a.module)
        if a.ref:
            if a.args:
                raise core.Usage("--ref takes no positional argument (use --module ID)")
            return mode_ref(root, a.module, a.update)
        if a.update:
            if a.args and a.module:
                raise core.Usage("--update takes files or --module, not both")
            return mode_update(root, a.args, a.module)
        if a.module or len(a.args) != 1:
            raise core.Usage("usage: pins.py <ID> | --ci | --chapter ID | --update [FILE…] | "
                             "--update --chapter ID | --ref")
        return mode_learner(root, a.args[0])
    except core.Usage as e:
        print(f"pins: {e}", file=sys.stderr)
        return core.EXIT_USAGE
    except core.Refusal as e:
        print(f"pins: refused: {e}", file=sys.stderr)
        return core.EXIT_REFUSED
    except common.ToolchainError as e:
        print(f"pins: {e}", file=sys.stderr)
        return core.EXIT_REFUSED
    except common.CapError as e:
        print(f"pins: {e}", file=sys.stderr)
        return core.EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
