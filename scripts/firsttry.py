#!/usr/bin/env python3
"""firsttry.py — the prediction-slot gate, exit scorer, hollow lint and
empty-body gate (phase DV1b; spec §3.8.3–§3.8.6, §3.10; design §7.3; DELTAS
Δ2, Δ38, Δ45, Δ47, Δ71, Δ72). scripts/firsttry.sh runs it.

A module's items carry slots (scripts/course_items.py, Δ71/Δ72), each
unfilled, filled-disabled or enabled:

  value        `// SLOT: expect F(x) == ???;` (Dafny, in a given-only check unit
               or a specimen), `// SLOT: assert_eq!(f(x), ???);` (Verus, in a
               #[test]), `// SLOT: assert(f(x) == ???) by (compute_only);`
  obligation   `// SLOT: FAILS ???` in a specimen header (labels `// [a]`)
  error        `// SLOT: EXPECT @??? "???"` in a specimen header
  verdict      `<K><n><lang> = ???` in slots/<ID>.slots; enabled by a live
               `// CHECK <K><n><lang>` line; checked against the sha256 pin in
               expected/<ID>.pins (only the hash ever ships)

Usage: scripts/firsttry.sh <ID> [MODE] [--root DIR]
  --check        record the FIRST TRY of every item whose slots are all filled:
                 the filled slots are enabled in a scratch copy, the pinned
                 verifier runs there (scripts/pins.py's harness), and one line
                 `item kind verdict date slot-hash` per item is appended to
                 instructor/calib/<ID>.tsv (append-only; an item's first record
                 wins). kind = predict (filled, not yet enabled: a genuine first
                 try) or observed (a slot was already enabled: shown, never a
                 first-try pass). Prints ✓/✗ per item and nothing the tool
                 said. Never edits your files. Refuses, recording nothing, a
                 slot that breaks a vacuity rule (H1–H3), an item with fewer
                 slots than it shipped with (its file deleted included), an
                 item whose given code is not as shipped, and a check that
                 could not run; any refusal makes it exit 1 (exit 0: recorded,
                 or nothing new to check). It also records the first try of
                 every CODE T item (a test-out written as code, no slot): the
                 first --check run at which its block is complete (code of
                 the learner's beyond what shipped, no hole form left) is the
                 try; its commented checks are enabled in a scratch copy and
                 the verifier runs there; `predict` while every shipped check
                 of the block is still commented, `observed` once one is not
                 (the comment above is_code_t defines it in full). From Q04
                 on (QPLAN §8.0, §6 Q23) a T item's first try (slot or code)
                 is refused while any P item of the module is unrecorded:
                 record the predictions first, then --check again. A code T
                 block's construct forms (`// form:` lines, QPLAN §6 Q43;
                 see "Construct forms" below) are part of its try: a block
                 that verifies but fails a form records as a fail, and an
                 out-of-resource result inside the block is a fail too.
  --report [--strict]
                 (default) per-item slot states and first tries; counts of
                 unfilled (incl. filled but not enabled), missing (against the
                 files as shipped: their version at the newest merge base
                 of HEAD with basic / challenge, or with main while neither
                 exists; an item of a shipped file since deleted is
                 missing, marker and slots), vacuous, commented-check and banned-construct findings,
                 failing enabled slots, unrecorded first tries; missing
                 `// did:` receipts (advisory); the first-try rate. A code T
                 block that is empty (prompt-as-heading, nothing written) or
                 still holds its hole counts as an unattempted test-out, and
                 an unrecorded one as an unrecorded first try. --strict
                 exits 1 on any of them: the module's done gate. Covers the
                 exercise files and specimens, and the exit files once
                 --exit has scored them. --strict also reports a resource
                 attribute outside every item block of a file holding a
                 budget item (`uses: rlimit`; QPLAN §6 Q21; one inside a block
                 is banned there), and runs the compiled checks (`vcheck
                 --test`) of every unit, crate or file holding a
                 property-test item (`uses: property-test`; §6 Q20): a
                 failing test, no test, or no verdict fails it. A finished
                 H, X or T block (code, no hole form) whose construct forms
                 fail is reported as `form` (static forms in every report;
                 `stable`, whose sweep runs the verifier, under --strict
                 only), and --strict fails on it. --strict also runs the
                 lever freeze (Δ199, DV5c): an automation-off lever that the
                 module's freeze pin records for a report file (specfreeze
                 --pin's `frozen_levers`) and the file no longer carries is
                 reported as `lever` (freeze-lever-removed) and fails it.
  --record       append one `calib` row to instructor/gradebook.md.
  --exit         score the closed-book exit (spec §3.10): one verdict per X
                 block; a block passes when it is attempted and has no error,
                 no hole, no unfilled slot, no commented check and every `need:`
                 fragment, and (a budget item, `uses: rlimit`; QPLAN §6 Q21)
                 no resource attribute charged to it (rlimit_charges), and
                 every construct form of the block met (a reason per form).
                 Blocks are judged independently: a parse or resolution
                 error in one block is blanked out and the rest re-run. Nothing is recorded while a block is unattempted; the
                 first complete run is recorded and is the score. Prints
                 `<ID> exit: n/N (threshold t) PASS|FAIL`. Thresholds
                 (EXIT_TIERS, EXIT_MODULES): survey 10/13, intro 5/6,
                 moderate and detailed 3/4 with half in each language
                 (design §7.1); Q10-Q12 at least 1 of their 2 timed items,
                 Q13-Q15 their 1 timed item, R06 and R11 at least 3 of 4 with
                 at least 1 in each language (the orchestrator's Q11
                 decision); Q16-Q18 have no exit file and no numeric
                 threshold (the verifier part plus the reviews).
  --lint-hollow  STATIC (never runs a tool): the exercise, specimen and exit
                 files ship hollow: every slot unfilled, every P and verdict
                 X/T item has its slot, every H item holds a hole form, no
                 commented check outside an `Uncomment as you go:` block, no
                 live enabled slot, the learner-mode lint clean (except on a
                 line a valid `// planted: <item id>` marker covers: the
                 planted trust leap of an S12 delivery specimen, sr_planted;
                 the instruments, vcheck and vaudit, never honour it), and
                 every `// after: <item id>` line of a card demo naming a
                 prediction item, and every `// form:` line parsing into rules
                 of the vocabulary that fit its block's language, inside an H,
                 X or T block with code (the twin-only `cfree:` and `triv:`
                 lines never appear in a learner file). With
                 --all: every non-planned module; with none (every module
                 planned) it passes LOUDLY ("no armed module: nothing to
                 check"); an armed module with no exercise or exit file, or
                 a registry with no module, fails (empty lists fail).
  --empty-body   author-only (CI=true or the author's linked worktree; it
                 refuses elsewhere, exit 3: the Verus modes take up to about
                 15 GB per job, Δ57): every hole item's body is emptied at
                 maximal automation (dvl.dafny.empty_body,
                 dvl.verus.empty_body); each must FAIL (the hole is real). A
                 `function … by method` item keeps its function body and
                 loses its method body. An annotation hole whose reference
                 twin marks the learner's lines (`// @hole-begin <id>` …
                 `// @hole-end <id>`) also gets the region gate (QPLAN §6
                 Q18): the twin, laid over its unit or crate, with those
                 lines blanked must FAIL too (Dafny regions=True, Verus mode
                 RGN; --eb-modes may name RGN).
                 A Dafny run that ends out of resources at the pinned limit
                 (`inconclusive`), the maxauto run included, counts as
                 failing (QPLAN §30 Q66): it is printed as such, never as a
                 lever-needed item. A Verus item whose block's first fn is a
                 method of an `impl Trait for Type` (QPLAN §30 Q65(a);
                 Q14.H2v) gets one gate per hole method of that impl in the
                 block, by its qualified symbol, and passes when each fails;
                 its twin names each method's trivial body as `// triv:
                 <method>: { … }`. A Dafny item whose block holds two or
                 more hole methods (methods, constructors, lemmas; Q17.H1d's
                 class) gets one gate per hole method too, by its qualified
                 symbol (dafny_hole_methods; DV5c).
                 --eb-modes/--eb-seeds narrow the Verus modes and the seeds for
                 a quick look; CI uses the pins. BV runs under its own short
                 wall clock (pins.toml eb_mode_timeout_s). A Verus item whose
                 twin block carries `// triv: { … }` lines gets that body in
                 the TRIV mode (declared_triv_body). A hole item with
                 `// form:` lines, or whose twin block carries `// cfree:
                 { … }` lines, also gets the forms gate (QPLAN §6 Q43): the
                 twin's form lines equal the learner's, the twin meets every
                 form (`stable`: its sweep), and each `cfree:` answer, in
                 place of the item's body in the twin, fails verification or
                 a form; --eb-modes may name FORMS (then the forms gate runs
                 only when FORMS is named).
                 A statement item (the registry's `exception =
                 "statement-item: …"`, the user's decisions D6 and D9) that
                 ships no hole (its statements are written in an agentic
                 file and proved there by a contractor: Q18.H2d/H2v) gets
                 the statement route instead (statement_route): the file's
                 CONTRACT names `scripts/specfreeze --against <statements>
                 <the file>`; the reference statements are that path's twin
                 (Solutions/<statements>) and hold at least one statement
                 the shipped file lacks; the reference delivery (the file's
                 twin) passes the reference gate with zero holes; and
                 `specfreeze --against` the reference statements reports 0
                 findings on it (the lever freeze included). One line per
                 item after the hole summary, `<ID> statement items: n/N
                 pass the statement route`; --eb-modes runs it only when it
                 names STMT. A statement item that holds a hole (a prose
                 item, Q17.H3d) keeps its hole's gates.

Construct forms (QPLAN §6 Q43; scripts/dvl/forms.py holds the vocabulary and
the static checks): `// form: <rule>[, <rule>]` lines inside an H, X or T
block (after its uses/need/pair lines). bv-exec (Verus: no `*`, `/`, `%` or
integer multiplication/division method in the item's exec code outside proof
blocks, assertions, ghost code and spec clauses), no-nl (Verus: no
nonlinear_arith or integer_ring in the block or the helpers it calls),
nl-steps:<k> (Verus: k scoped `assert(…) by (nonlinear_arith) requires …`
steps in the block), trigger (an explicit trigger on a quantifier in the
block; a presence check), stable (no resource attribute in the block, and its
declarations verify in every row of `vcheck --brittleness`, Dafny under each
bundled solver: QPLAN §6 Q29). An item's rules are its block's form lines now
and as shipped (the merge base with basic / challenge, or main), united.

Exit codes: 0 ok · 1 failed (--check: an item refused) · 2 usage · 3 refused
(unknown id, planned module, a missing or unusable registry, missing file, an
author-only mode outside the author's context).

The section between the SHARED SLOT RULES markers below is loaded by
scripts/pins.py and scripts/reference_lint.py from this file, so the learner
gate, the golden harness and the reference lint apply one implementation of
the slot grammar and the vacuity rules (spec §3.8.4).
"""

import argparse
import importlib.machinery
import importlib.util
import math
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

# ===== BEGIN SHARED SLOT RULES =====
# Pure text: the port's slot grammar (spec §3.8.6, Δ72) and the vacuity
# hazards H1–H3 and H6 (spec §3.8.4), plus the `need:`, commented-check and
# receipt scans every consumer shares. Self-contained (stdlib and
# course_items only): scripts/pins.py and scripts/reference_lint.py exec this
# section from firsttry.py by its two marker lines.
import hashlib as _sr_hashlib
import json as _sr_json
import re as _sr_re
import course_items as _sr_ci

SR_MIN_FRAGMENT = 8
SR_SEVERITY = _sr_re.compile(r"\s*(?:error|warning|info|note|help|hint|trace)\s*:", _sr_re.I)
SR_ANSWER_FORM = _sr_re.compile(
    r"Answer form:\s*`?(numeral|constructors|(?:Option|Bool|String|Char)\s+literal)", _sr_re.I)
SR_FAILS = _sr_re.compile(r"FAILS(?:\s+(.*?))?\s*$")
SR_EXPECT = _sr_re.compile(r'EXPECT\s+@(\?\?\?|\d+)\s+"((?:[^"\\]|\\.)*)"\s*$')
SR_LABEL = _sr_re.compile(r"//\s*\[([a-z0-9]+)\]\s*$")
SR_NUM = (r"-?(?:0x[0-9a-fA-F_]+|\d[\d_]*)"
          r"(?:u8|u16|u32|u64|u128|usize|i8|i16|i32|i64|i128|isize)?")
SR_STRING = r'"(?:[^"\\\n]|\\.)*"' + r"|'(?:[^'\\\n]|\\.)*'"
SR_CHAR = r"'(?:[^'\\\n]|\\.[^']*)'"
# Closing automation steps that need a `// did:` receipt (spec §3.7), per language.
SR_AUTOMATION = {
    "v": (r"\bby\s*\(\s*(?:nonlinear_arith|bit_vector|compute|compute_only)\s*\)",
          r"\bbroadcast\s+use\b", r"\breveal(?:_with_fuel)?\s*\("),
    "d": (r"\{:\s*induction\b(?!\s+false)", r"@Induction\b", r"\breveal\s+[A-Za-z_]"),
    "py": (),
}


def sr_leader(rel):
    return "#" if _sr_ci.file_lang(rel) == "py" else "//"


def sr_norm_ws(s):
    return " ".join(s.split())


def sr_sha256(s):
    return _sr_hashlib.sha256(s.encode("utf-8")).hexdigest()


def sr_normalize_answer(s):
    """A verdict answer as hashed (spec §3.8.6): trimmed, internal whitespace
    collapsed to one space."""
    return sr_norm_ws(s)


def sr_salted_answer_hash(mid, local, s):
    """The verdict pin (orchestrator decision, DV2a fix round): sha256 over
    "<module id>:<item id>:<normalized answer>", e.g. "Q04:P1dv:verified 2"
    (the tools suites' synthetic Q04), so equal answers of two items never
    share a pin and no well-known hash of a short string appears in
    expected/. The only verdict hash: the unsalted one is retired (DV2b)."""
    return sr_sha256(f"{mid}:{local}:{sr_normalize_answer(s)}")


# `// planted: <item id>`: a trust leap planted on purpose in an S12 delivery
# specimen (a fake-green "delivery" whose species the learner diagnoses), or in
# an S10 pipeline-forensic delivery (Q15.P2d-P5v: a green-looking delivery
# whose stage and instrument the learner names; DV5b Q15 lane).
# Only the shipping lints honour it (firsttry --lint-hollow, reference_lint):
# they drop their lint findings on the line it covers. vcheck and vaudit
# never read it, so the instruments still report the leap. It covers its own
# line when it trails code, else the next non-blank line. It is valid only in
# a specimen and only when it names a P verdict item of strand S12 (or S10,
# PLANTED_STRANDS) that the same file holds; any other use is itself a problem.
# R04.P5d is the R-owned runtime-check delivery (PLAN §6.4), without Q's
# strand labels. R04.A1d/v instead mark an intentionally false statement:
# they are placement metadata only and NEVER suppress a shipping lint.
SR_PLANTED = _sr_re.compile(r"//\s*planted:\s*(\S+)\s*$")
PLANTED_STRANDS = ("S10", "S12")


def sr_planted(raw_lines, rel, items):
    """({covered line: item id}, [(marker line, problem)]) of a file's
    `// planted:` markers. items: the file's parsed items."""
    covered, problems = {}, []
    mine = {it["id"]: it for it in items if it["file"] == rel}
    for ln, line in enumerate(raw_lines, 1):
        m = SR_PLANTED.search(line)
        if not m:
            continue
        iid = m.group(1)
        it = mine.get(iid)
        # R04's agent plant marks a false mathematical claim, not a trust
        # exemption. Validate its exact home and item scope, then leave the
        # covered map empty: every ordinary shipping lint still applies.
        home = rel.removeprefix("Solutions/")
        r04_agents = {"R04.A1d": "dafny/R/R04_Specs/agent/R04_AgentProver.dfy",
                      "R04.A1v": "verus/r/r04_specs/src/agent.rs"}
        if iid in r04_agents and home == r04_agents[iid] and it is not None \
                and it["kind"] == "A" and it["line_start"] <= ln <= it["line_end"]:
            continue
        if not rel.endswith(".specimen"):
            problems.append((ln, "a `planted:` marker lives only in an S12 delivery specimen"))
            continue
        r04_delivery = iid == "R04.P5d" and home == "specimens/R04/P5d.dfy.specimen"
        # Copies of the runtime-check and assumption deliveries are guarded demos,
        # not new prediction items. Both earlier predictions must be recorded.
        r04_demos = {"specimens/R04/chapter-p1-d.dfy.specimen",
                     "specimens/R04/card-c3d.dfy.specimen",
                     "specimens/R04/card-c5dv-d.dfy.specimen",
                     "specimens/R04/audit-expect-d.dfy.specimen",
                     "specimens/R04/audit-assume-v.rs.specimen",
                     "specimens/R04/card-c5dv-v.rs.specimen"}
        guard_pattern = _sr_re.compile(r"\s*//\s*after:\s*(\S+)\s*")
        afters = {match.group(1) for match in map(guard_pattern.fullmatch, raw_lines) if match}
        r04_demo = iid == "R04.P5d" and home in r04_demos and \
            {"R04.P1d", "R04.P5d"} <= afters
        own_delivery = it is not None and it["kind"] == "P" and it["format"] == "verdict" \
            and (it["strand"] in PLANTED_STRANDS or r04_delivery)
        if not own_delivery and not r04_demo:
            problems.append((ln, f"the `planted:` marker names {iid}, which is no S10 or S12 "
                                 "verdict P item of this file"))
            continue
        code = line[:m.start()].strip()
        target = ln
        if not code:
            target = next((k for k in range(ln + 1, len(raw_lines) + 1)
                           if raw_lines[k - 1].strip()), None)
            if target is None:
                problems.append((ln, "the `planted:` marker covers no line"))
                continue
        covered[target] = iid
    return covered, problems


def sr_slot_value(text):
    """The answer of a slot-file value `"…"` (backslash escapes allowed)."""
    t = text.strip()
    try:
        v = _sr_json.loads(t)
        if isinstance(v, str):
            return v
    except ValueError:
        pass
    return t[1:-1] if len(t) >= 2 and t[0] == t[-1] == '"' else t


def sr_slot_file_values(text):
    """{local id: (line, raw value text)} of a slots/<ID>.slots file."""
    out = {}
    for ln, line in enumerate(text.split("\n"), 1):
        m = _sr_ci.SLOT_FILE_LINE.fullmatch(line)
        if m and not line.strip().startswith("#"):
            out.setdefault(m.group(1), (ln, m.group(2)))
    return out


def sr_payload(raw_line, rel):
    """The text a slot line holds: after `// SLOT: ` (shipped or filled), or
    the live form when enabled (`FAILS …`, `EXPECT @…`, the value check)."""
    lead = _sr_re.escape(sr_leader(rel))
    m = _sr_re.match(rf"\s*{lead} SLOT: ?(.*)$", raw_line)
    if m:
        return m.group(1).strip()
    m = _sr_re.match(rf"\s*{lead}\s*((?:FAILS|EXPECT)\b.*)$", raw_line)
    if m:
        return m.group(1).strip()
    return raw_line.strip()


def sr_enable_line(raw_line, rel):
    """The slot line with its `SLOT: ` prefix removed (the enabled form)."""
    lead = _sr_re.escape(sr_leader(rel))
    m = _sr_re.match(rf"(\s*)({lead}) SLOT: ?(.*)$", raw_line)
    if not m:
        return raw_line
    body = m.group(3)
    if _sr_re.match(r"(?:FAILS|EXPECT|CHECK)\b", body):
        return f"{m.group(1)}{m.group(2)} {body}"      # stays a comment: the harness reads it
    return f"{m.group(1)}{body}"                         # a value check becomes code


def sr_labels(raw_lines):
    """{label: line} of the `// [x]` labels of an obligation specimen."""
    out = {}
    for ln, line in enumerate(raw_lines, 1):
        m = SR_LABEL.search(line)
        if m:
            out.setdefault(m.group(1), ln)
    return out


def sr_obligation(payload):
    """(labels or None while unfilled, problem or None) of `FAILS …`."""
    m = SR_FAILS.fullmatch(payload.strip())
    if not m:
        return None, "an obligation slot reads `FAILS <label> …`"
    body = (m.group(1) or "").strip()
    if "???" in body:
        return None, None
    toks = body.split()
    if toks in ([], ["none"]):
        return frozenset(), None
    if any(not _sr_re.fullmatch(r"[a-z0-9]+", t) for t in toks):
        return None, "obligation labels are lower-case letters or digits, space-separated"
    if len(set(toks)) != len(toks):
        return None, "an obligation label is listed twice"
    return frozenset(toks), None


def sr_error(payload):
    """(line or None, fragment or None, problem or None) of `EXPECT @L "…"`."""
    m = SR_EXPECT.fullmatch(payload.strip())
    if not m:
        return None, None, 'an error slot reads `EXPECT @<line> "<fragment>"`'
    line = None if m.group(1) == "???" else int(m.group(1))
    frag = m.group(2)
    if frag == "???":
        frag = None
    else:
        frag = _sr_re.sub(r"\\(.)", r"\1", frag)
    return line, frag, None


def sr_split_top(s, sep):
    """Index of the first `sep` at bracket depth 0 outside strings, or -1."""
    depth, i, n, q = 0, 0, len(s), ""
    while i < n:
        c = s[i]
        if q:
            if c == "\\":
                i += 2
                continue
            if c == q:
                q = ""
        elif c in "\"":
            q = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif depth == 0 and s.startswith(sep, i) and not (
                sep == "==" and (s.startswith("===", i) or (i > 0 and s[i - 1] in "=!<>"))):
            return i
        i += 1
    return -1


def sr_value(payload, lang):
    """(lhs, rhs) of a value check, or None when the text is none:
    Dafny `expect L == R;`, Verus `assert_eq!(L, R);` and
    `assert(L == R) by (compute_only);`, Python `assert L == R`."""
    s = payload.strip()
    body, sep = None, "=="
    if lang == "d":
        m = _sr_re.fullmatch(r"expect\s+(.*?)\s*;?", s)
        body = m.group(1) if m else None
    elif lang == "v":
        m = _sr_re.fullmatch(r"assert_eq!\s*\((.*)\)\s*;?", s)
        if m:
            body, sep = m.group(1), ","
        else:
            m = _sr_re.fullmatch(r"assert\s*\((.*)\)\s*by\s*\(\s*compute(?:_only)?\s*\)\s*;?", s)
            body = m.group(1) if m else None
    else:
        m = _sr_re.fullmatch(r"assert\s+(.*?)\s*", s)
        body = m.group(1) if m else None
    if body is None:
        return None
    k = sr_split_top(body, sep)
    if k < 0:
        return None
    lhs, rhs = body[:k].strip(), body[k + len(sep):].strip()
    if sep == ",":
        j = sr_split_top(rhs, ",")
        rhs = rhs[:j].strip() if j >= 0 else rhs
    return lhs, rhs


def sr_answer_form(block_lines):
    """The item's declared `Answer form:` (lower case), or None."""
    for line in block_lines:
        m = SR_ANSWER_FORM.search(line)
        if m:
            return sr_norm_ws(m.group(1).lower())
    return None


_SR_SQUASH = _sr_re.compile(r"[\s()\[\]{}]+")


def sr_squash(s):
    """`s` without whitespace and brackets: the echo rule's comparison form."""
    return _SR_SQUASH.sub("", s)


def _sr_term(s):
    """True when `s` is a constructor term: Path [(term, …)] or a literal."""
    s = s.strip()
    if not s:
        return False
    if _sr_re.fullmatch(SR_NUM, s) or _sr_re.fullmatch(SR_STRING, s) or \
            _sr_re.fullmatch(SR_CHAR, s) or s in ("true", "false", "True", "False"):
        return True
    m = _sr_re.fullmatch(r"((?:[A-Za-z_][A-Za-z0-9_]*(?:::|\.))*([A-Za-z_][A-Za-z0-9_]*))"
                         r"\s*(?:\((.*)\))?", s, _sr_re.S)
    if not m or not m.group(2)[0].isupper():
        return False
    args = m.group(3)
    if args is None or not args.strip():
        return True
    parts, rest = [], args
    while True:
        k = sr_split_top(rest, ",")
        if k < 0:
            parts.append(rest)
            break
        parts.append(rest[:k])
        rest = rest[k + 1:]
    return all(_sr_term(p) for p in parts)


def sr_literal_ok(form, rhs):
    s = rhs.strip()
    if form == "numeral":
        return bool(_sr_re.fullmatch(SR_NUM, s))
    if form == "bool literal":
        return s in ("true", "false", "True", "False")
    if form == "string literal":
        return bool(_sr_re.fullmatch(SR_STRING, s))
    if form == "char literal":
        return bool(_sr_re.fullmatch(SR_CHAR, s))
    if form == "option literal":
        return bool(_sr_re.fullmatch(r"(?:Option(?:::|\.))?None", s)) or (
            bool(_sr_re.fullmatch(r"(?:Option(?:::|\.))?Some\s*\(.*\)", s, _sr_re.S)) and _sr_term(s))
    if form == "constructors":
        return _sr_term(s)
    return False


def sr_applied(s):
    """Names applied to arguments in `s` (`F(` → F)."""
    return set(_sr_re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", s))


def sr_rule_h1(fragment):
    body = SR_SEVERITY.sub("", fragment, count=1) if SR_SEVERITY.match(fragment) else fragment
    n = len("".join(body.split()))
    if n < SR_MIN_FRAGMENT:
        return (f"H1 (vacuous fragment): {n} non-space character(s), fewer than "
                f"{SR_MIN_FRAGMENT}: it would match almost any message")
    return None


def sr_rule_h3(fragment):
    if SR_SEVERITY.match(fragment):
        return ("H3 (severity prefix): a fragment never starts with error:/warning:/info: "
                "(the prefix is not part of the message text)")
    return None


def sr_rule_h2_echo(fragment, source):
    f = sr_squash(fragment)
    if f and f in sr_squash(source):
        return ("H2 (echo): the fragment occurs in the item's own source; predict the message, "
                "not text copied from the code")
    return None


def sr_rule_h2_value(form, lhs, rhs):
    out = []
    if form is None:
        out.append("H2: the item declares no `Answer form:` line, so no value can be judged "
                   "a literal")
    elif not sr_literal_ok(form, rhs):
        out.append(f"H2 (not a literal): the right-hand side is not a {form} literal")
    if sr_squash(rhs) and sr_squash(lhs) and (sr_squash(rhs) == sr_squash(lhs)
                                              or sr_squash(lhs) in sr_squash(rhs)):
        out.append("H2 (echo): the right-hand side repeats the left-hand side")
    elif sr_applied(rhs) & sr_applied(lhs):
        out.append("H2 (echo): the right-hand side applies a function the left-hand side "
                   "applies; a value is a literal")
    return out


def sr_slot_problems(item, slot, raw_lines, rel, verdict_value=None):
    """Vacuity problems of one filled or enabled slot (an unfilled slot has
    none). raw_lines are the lines of the slot's own file (for a verdict slot
    the item's file, with verdict_value its slot-file answer)."""
    fmt = slot["format"]
    lang = _sr_ci.file_lang(item["file"])
    if fmt == "verdict":
        if verdict_value is None or slot["state"] == "unfilled":
            return []
        return [] if sr_normalize_answer(sr_slot_value(verdict_value)) else \
            ["a verdict answer is non-empty"]
    payload = sr_payload(raw_lines[slot["line"] - 1], rel)
    block = raw_lines[item["line_start"] - 1:item["line_end"]]
    slot_lines = {s["line"] for s in item["slots"] if s["file"] == item["file"]}
    others = [raw_lines[ln - 1] for ln in range(item["line_start"], item["line_end"] + 1)
              if ln not in slot_lines]
    if fmt == "obligation":
        labels, problem = sr_obligation(payload)
        if problem:
            return [problem]
        if labels is None:
            return []
        known = sr_labels(raw_lines)
        unknown = sorted(x for x in labels if x not in known)
        return [f"names label(s) the specimen does not carry: {' '.join(unknown)}"] if unknown \
            else []
    if fmt == "error":
        line, frag, problem = sr_error(payload)
        if problem:
            return [problem]
        if line is None or frag is None:
            return []
        out = []
        if not 1 <= line <= len(raw_lines):
            out.append(f"@{line} is outside the file (1..{len(raw_lines)})")
        out += [p for p in (sr_rule_h1(frag), sr_rule_h3(frag),
                            sr_rule_h2_echo(frag, "\n".join(others))) if p]
        return out
    if fmt == "value":
        lr = sr_value(payload, lang)
        if lr is None:
            return ["a value slot holds one check of the shipped shape (`expect L == R;`, "
                    "`assert_eq!(L, R);`, `assert(L == R) by (compute_only);`)"]
        lhs, rhs = lr
        if "???" in rhs:
            return []
        return sr_rule_h2_value(sr_answer_form(block), lhs, rhs)
    return []


def sr_need_missing(text, rel, item):
    """The `need:` fragments missing from the block's non-comment code
    (whitespace-normalized; spec §3.9)."""
    code, _ = _sr_ci.scan(rel, text)
    block = sr_norm_ws(" ".join(code[item["line_start"]:item["line_end"]]))
    return [f for f in item["need"] if sr_norm_ws(f) not in block]


def sr_uncomment_regions(raw_lines, rel):
    """[(first, last)] line ranges of the comment lines under each
    `Uncomment as you go:` header."""
    lead = _sr_re.escape(sr_leader(rel))
    head = _sr_re.compile(rf"\s*{lead}\s*Uncomment as you go:\s*$")
    is_comment = _sr_re.compile(rf"\s*{lead}")
    out, i, n = [], 0, len(raw_lines)
    while i < n:
        if head.match(raw_lines[i]):
            j = i + 1
            while j < n and is_comment.match(raw_lines[j]) and not head.match(raw_lines[j]):
                j += 1
            if j > i + 1:
                out.append((i + 2, j))
            i = j
        else:
            i += 1
    return out


def sr_commented_checks(raw_lines, rel, lo=1, hi=None):
    """Lines that are commented checks (spec §3.5): every non-prose line under
    an `Uncomment as you go:` header (prose takes a doubled leader), and in
    Rust every #[ignore] test."""
    hi = len(raw_lines) if hi is None else hi
    leader = sr_leader(rel)
    out = []
    for a, b in sr_uncomment_regions(raw_lines, rel):
        for ln in range(a, b + 1):
            body = raw_lines[ln - 1].strip()[len(leader):].strip()
            if body and not body.startswith(leader) and lo <= ln <= hi:
                out.append(ln)
    if rel.endswith((".rs", ".rs.specimen")):
        out += [ln for ln in range(lo, hi + 1)
                if _sr_re.match(r"\s*#\[ignore\b", raw_lines[ln - 1])]
    return sorted(set(out))


SR_CHECKLIKE = {"//": _sr_re.compile(r"\s*//\s*(?:expect\s|assert\s*\(|assert\s+|assert_eq!|"
                                     r"assert_ne!|assert!|#\[test\]|calc\s*\{)"),
                "#": _sr_re.compile(r"\s*#\s*assert\s")}


def sr_stray_commented_checks(raw_lines, rel):
    """Commented check-like lines outside every `Uncomment as you go:` block
    (and not slot lines): a shipped file comments checks only there."""
    leader = sr_leader(rel)
    inside = {ln for a, b in sr_uncomment_regions(raw_lines, rel) for ln in range(a, b + 1)}
    pat = SR_CHECKLIKE[leader]
    return [ln for ln, line in enumerate(raw_lines, 1)
            if ln not in inside and pat.match(line) and "SLOT:" not in line]


def sr_missing_receipts(text, rel, item):
    """Lines of the block holding a closing automation step with no
    `// did:` receipt on that line or the line above (spec §3.7)."""
    lang = _sr_ci.file_lang(rel)
    pats = [_sr_re.compile(p) for p in SR_AUTOMATION.get(lang, ())]
    if not pats:
        return []
    raw = text.split("\n")
    code, _ = _sr_ci.scan(rel, text)
    did = _sr_re.compile(rf"{_sr_re.escape(sr_leader(rel))} did: \S")
    out = []
    for ln in range(item["line_start"], item["line_end"] + 1):
        c = code[ln - 1]
        if any(p.search(c) for p in pats):
            if not (did.search(raw[ln - 1]) or (ln >= 2 and did.search(raw[ln - 2]))):
                out.append(ln)
    return out


def sr_twin_leftovers(raw_lines):
    """Lines of a reference twin that hold a slot form (spec §3.8.4 H6)."""
    return [ln for ln, line in enumerate(raw_lines, 1) if "SLOT:" in line or "???" in line]


def sr_marker_key(item):
    """What a twin's marker must repeat of its learner item (spec §3.13)."""
    return (item["id"], item["kind"], item["strand"], item["format"], item["min"],
            tuple(item["uses"]), tuple(sr_norm_ws(x) for x in item["need"]), item["pair"])
# ===== END SHARED SLOT RULES =====


def _load_core():
    if "vcheck" in sys.modules:
        return sys.modules["vcheck"]
    loader = importlib.machinery.SourceFileLoader("vcheck", str(SCRIPTS / "vcheck"))
    spec = importlib.util.spec_from_loader("vcheck", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vcheck"] = mod
    loader.exec_module(mod)
    return mod


core = _load_core()
import pins as harness  # noqa: E402  (the golden harness: it runs the slot checks)
from dvl import forms as F  # noqa: E402  (QPLAN §6 Q43: per-item construct forms)
from dvl import levers as LEV  # noqa: E402  (Δ199: the lever freeze, --report --strict)

D, V, ci = core.D, core.V, core.ci
PY = core.PY        # dvl.python (DV4): the learner Python files
# Exit thresholds. need (n, d): at least ceil(N * n / d) of the N X items pass.
# per_lang: a floor in each language, ("frac", n, d) of that language's items
# or ("min", k) items. The concept tiers follow design §7.1 (Δ102); the
# practice tiers and R06/R11 follow the orchestrator's Q11 decision (DV2a fix
# round): Q10-Q12 at least 1 of their 2 timed items, Q13-Q15 their 1 timed
# item, Q16-Q18 the verifier part plus the reviews (no numeric threshold, no
# exit file), R06 and R11 at least 3 of 4 with at least 1 in each language.
EXIT_TIERS = {
    "survey": {"need": (10, 13)},
    "intro": {"need": (5, 6)},
    "moderate": {"need": (3, 4), "per_lang": ("frac", 1, 2)},
    "detailed": {"need": (3, 4), "per_lang": ("frac", 1, 2)},
    "practice-intro": {"need": (1, 2)},
    "practice-intermediate": {"need": (1, 1)},
    "practice-hard": {"reviews": True},
}
EXIT_MODULES = {     # R modules have no tier: their thresholds are per module
    "R06": {"need": (3, 4), "per_lang": ("min", 1)},
    "R11": {"need": (3, 4), "per_lang": ("min", 1)},
}
REVIEWS_ONLY = ("its tier gate is the verifier part plus the reviews: no numeric exit "
                "threshold (orchestrator decision Q11)")


def exit_rule(rec):
    """The module's exit rule (EXIT_MODULES, else EXIT_TIERS by tier), or None."""
    return EXIT_MODULES.get(rec["id"]) or EXIT_TIERS.get(rec["tier"] or "")


def die(msg, code=core.EXIT_FAIL):
    print(f"firsttry: {msg}", file=sys.stderr)
    raise SystemExit(code)


# =====================================================================================
# The module context
# =====================================================================================

class Ctx:
    """One module: its record, items, slot file, calibration records and files."""

    def __init__(self, root, mid, lenient=False):
        self.root = Path(root)
        try:
            self.rec = core.record(self.root, mid)
        except core.Refusal as e:
            die(f"refused: {e}", core.EXIT_REFUSED)
        self.mid = self.rec["id"]
        self.items, self.errors = core.module_items(self.root, self.rec)
        if self.errors and not lenient:
            die(f"{self.mid}'s item markers do not parse (check_course_map.py --items):\n  "
                + "\n  ".join(self.errors))
        try:
            self.slots = core.slot_file(self.root, self.mid)
        except RuntimeError as e:
            if not lenient:
                die(f"slots/{self.mid}.slots: {e}")
            self.errors.append(str(e))
            self.slots = None
        self.calib = core.read_calib(self.root, self.mid)
        self.exercises = [r for r in core.expand_files(self.root, self.rec["exercises"])
                          if (self.root / r).is_file()]
        self.exits = [r for r in core.expand_files(self.root, self.rec["exits"])
                      if (self.root / r).is_file()]
        # the learner Python files (DV4): verdict slots, AST holes, acceptance tests
        self.harness = [r for r in self.rec["harness"] if (self.root / r).is_file()]
        # exercise and exit files the module shipped with (the shipped reference:
        # vcheck's shipped_base) that the working tree no longer holds: their
        # items are missing
        self.gone = core.gone_files(self.root, self.rec["exercises"] + self.rec["exits"])
        self._text = {}

    def text(self, rel):
        if rel not in self._text:
            self._text[rel] = (self.root / rel).read_text(encoding="utf-8")
        return self._text[rel]

    def lines(self, rel):
        return self.text(rel).split("\n")

    def items_in(self, rels):
        rels = set(rels)
        return [it for it in self.items if it["file"] in rels]

    def verdict_value(self, item):
        """The raw slot-file value of a verdict item, or None."""
        if not self.slots:
            return None
        vals = sr_slot_file_values(self.text(self.slots[0]))
        local = item["id"].split(".", 1)[1]
        return vals.get(local, (None, None))[1]


# =====================================================================================
# The file as shipped (the newest merge base of HEAD with basic / challenge,
# or with main while neither exists; D26): the shared core's
# shipped_base / shipped_text / gone_files / shipped_slot_items
# =====================================================================================

shipped_base, shipped_text = core.shipped_base, core.shipped_text


SWITCH = re.compile(r"\s*(?://|#)\s*(?:SLOT:\s*)?CHECK\s+[WCPHXTA][1-9]\d*(?:dv|py|d|v)\s*$")


def given_lines(text, item):
    """The item block's given lines (whitespace-normalized, blank lines and
    slot and CHECK-switch lines dropped): what a learner may not change."""
    raw = text.split("\n")
    skip = {s["line"] for s in item["slots"] if s["file"] == item["file"]}
    out = []
    for ln in range(item["line_start"], item["line_end"] + 1):
        if ln in skip or SWITCH.match(raw[ln - 1]):
            continue
        s = sr_norm_ws(raw[ln - 1])
        if s:
            out.append(s)
    return out


def shipped_state(ctx):
    """{item id: (shipped item, shipped text)} over the exercise and exit
    files at the baseline, the ones since deleted included (empty when there
    is no baseline)."""
    return core.shipped_slot_items(ctx.root, ctx.mid, ctx.exercises + ctx.exits + ctx.gone)


def gone_findings(ctx, shipped):
    """[(path, 0, text)]: one per item of a shipped file that is gone (its
    marker and its slots with it), or one for the file when it held none."""
    out = []
    for rel in ctx.gone:
        mine = [(iid, sit) for iid, (sit, _) in shipped.items() if sit["file"] == rel]
        for iid, sit in mine:
            n = len(sit["slots"])
            out.append((rel, 0, f"{iid}: its file is gone (the item shipped at line "
                                f"{sit['line_start']}" + (f" with {n} slot(s)" if n else "")
                        + "): restore the file as shipped"))
        if not mine:
            out.append((rel, 0, "the file is gone (it shipped at the merge base with the "
                                "course branch): restore it"))
    return out


# =====================================================================================
# Static findings per file
# =====================================================================================

def lint_file(root, rel, mode="learner"):
    """The lint findings of one file. A Verus file of a crate is linted with
    its crate, so a file reached through `#[cfg(test)] mod` counts as tests."""
    lang = core.lang_of(rel)
    path = Path(root) / rel
    paths = [path]
    if lang == "v" and not rel.endswith(".specimen"):
        crate = harness._crate_rel(root, rel)
        if crate:
            paths = [Path(root) / crate, path]
    found = core.lib(lang).lint(paths, mode)
    return [f for f in found if Path(f.file).resolve() == path.resolve()]


def item_problems(ctx, it):
    """Vacuity problems of every filled or enabled slot of an item."""
    out = []
    for s in it["slots"]:
        if s["state"] == "unfilled":
            continue
        vv = ctx.verdict_value(it) if s["format"] == "verdict" else None
        lines = ctx.lines(it["file"])
        for p in sr_slot_problems(it, s, lines, it["file"], vv):
            out.append((s["file"], s["line"], p))
    return out


def file_findings(ctx, rel, shipped):
    """Static counts for one learner file: dict of lists of (path, line, text)."""
    f = {"unfilled": [], "disabled": [], "vacuous": [], "commented": [], "did": [],
         "missing": [], "banned": [], "unattempted": [], "budget": [], "holes": []}
    raw = ctx.lines(rel)
    items = ctx.items_in([rel])
    for it in items:
        for s in it["slots"]:
            if s["state"] == "unfilled":
                f["unfilled"].append((s["file"], s["line"], f"{it['id']}: unfilled slot"))
            elif s["state"] == "filled-disabled":
                f["disabled"].append((s["file"], s["line"],
                                      f"{it['id']}: filled but not enabled"))
        for path, line, p in item_problems(ctx, it):
            f["vacuous"].append((path, line, f"{it['id']}: {p}"))
        if not it["slots"] and (it["kind"] == "P" or (it["kind"] in "XT" and it["format"])):
            f["missing"].append((rel, it["line_start"], f"{it['id']}: its slot is missing"))
        if is_code_t(it) and not rel.endswith(".specimen"):
            why = code_t_open(ctx, it, (shipped or {}).get(it["id"]))
            if why:
                f["unattempted"].append((rel, it["line_start"], f"{it['id']}: " + (
                    "the test-out block is empty: write its target" if why == "empty" else
                    "the test-out's hole is still open")))
        if it["kind"] == "X":
            for frag in sr_need_missing(ctx.text(rel), rel, it):
                f["missing"].append((rel, it["line_start"],
                                     f"{it['id']}: a `need:` fragment is not in its code"))
        if it["kind"] in "HXT":
            for ln in sr_missing_receipts(ctx.text(rel), rel, it):
                f["did"].append((rel, ln, f"{it['id']}: closing automation step without a "
                                          "`did:` receipt"))
    for ln in sr_commented_checks(raw, rel):
        f["commented"].append((rel, ln, "commented check"))
    # banned constructs: the learner-mode lint's findings inside H/X/T blocks
    if core.lang_of(rel):
        try:
            found = lint_file(ctx.root, rel)
        except ValueError:
            found = []
        for x in found:
            for it in items:
                if it["kind"] in "HXT" and it["line_start"] <= x.line <= it["line_end"]:
                    f["banned"].append((rel, x.line, f"{it['id']}: {x.kind}"))
                    break
        # budget items (Q21): a resource attribute outside every H/X/T block is
        # charged to each of them (one inside a block is already `banned` there)
        for iid, charges in rlimit_charges(ctx, rel, found).items():
            for line, kind, own in charges:
                if not own:
                    f["budget"].append((rel, line, f"{iid}: {kind} outside every item block "
                                                   "(a budget item proves at the pinned limit)"))
    # a learner Python file (DV4): its open holes (AST, the frozen counter) and
    # its lint's findings inside H/X/T blocks
    if rel.endswith(".py"):
        try:
            for h in PY.holes(ctx.root / rel, root=ctx.root):
                f["holes"].append((rel, h.line, f"{h.label}: the hole is still open"))
        except PY.HoleCountError:
            f["holes"].append((rel, 0, "the file does not parse: its holes cannot be counted"))
        for x in PY.lint([ctx.root / rel], root=ctx.root):
            for it in items:
                if it["kind"] in "HXT" and it["line_start"] <= x.line <= it["line_end"]:
                    f["banned"].append((rel, x.line, f"{it['id']}: {x.kind}"))
                    break
    # against the shipped baseline: items, slots and checks that are gone
    if shipped is not None:
        mine = {it["id"]: it for it in items}
        for iid, (sit, stext) in shipped.items():
            if sit["file"] != rel:
                continue
            cur = mine.get(iid)
            if cur is None:
                f["missing"].append((rel, 0, f"{iid}: its marker is gone (it shipped at "
                                             f"line {sit['line_start']})"))
                continue
            if len(cur["slots"]) < len(sit["slots"]):
                f["missing"].append((rel, cur["line_start"],
                                     f"{iid}: {len(sit['slots']) - len(cur['slots'])} of its "
                                     f"{len(sit['slots'])} shipped slot(s) are gone"))
            if len(set(sit["need"]) - set(cur["need"])):
                f["missing"].append((rel, cur["line_start"],
                                     f"{iid}: a shipped `need:` line is gone"))
            s_checks = len(sr_commented_checks(stext.split("\n"), rel, sit["line_start"],
                                               sit["line_end"]))
            c_checks = len(_check_lines(raw, rel, cur, stext, sit))
            if c_checks < s_checks:
                f["missing"].append((rel, cur["line_start"],
                                     f"{iid}: {s_checks - c_checks} shipped check(s) deleted "
                                     "instead of uncommented"))
    return f


def _check_lines(raw, rel, cur, stext, sit):
    """The current block's check lines that correspond to shipped commented
    checks: each shipped commented check, uncommented or still commented, is
    looked up by its normalized text in the current block."""
    sraw = stext.split("\n")
    leader = sr_leader(rel)
    block = [sr_norm_ws(raw[ln - 1]) for ln in range(cur["line_start"], cur["line_end"] + 1)]
    found = []
    for ln in sr_commented_checks(sraw, rel, sit["line_start"], sit["line_end"]):
        body = sr_norm_ws(sraw[ln - 1].strip()[len(leader):])
        if any(x == body or x == sr_norm_ws(f"{leader} {body}") for x in block):
            found.append(ln)
    return found


# =====================================================================================
# Budget items and property tests (QPLAN §6 Q20, Q21)
# =====================================================================================

# Q21: a budget item (`uses: rlimit`) asks for a proof at the pinned resource
# limit with no resource attribute. vaudit's learner-mode lint reports such an
# attribute (Dafny `resource-attribute`: {:rlimit}, {:resource_limit},
# @ResourceLimit and the time limits; Verus `rlimit-inflation`: a
# #[verifier::rlimit] above the pin). Each finding is charged to the H, X or T
# block it sits in; one in no such block (a helper before the first marker, in a
# worked example's or a card's block) is charged to every budget item of the
# file, since the item may call what it raises. `--exit` fails a budget item on
# a charged finding, and `--report --strict` reports the charges ("budget").
RESOURCE_LINT = ("resource-attribute", "rlimit-inflation")


def rlimit_charges(ctx, rel, found=None):
    """{item id: [(line, kind, in its own block)]} for the budget items of one
    file; {} when the file has none. `found`: the file's lint findings, when
    the caller has them (lint_file)."""
    items = ctx.items_in([rel])
    budget = [it for it in items if "rlimit" in it["uses"]]
    if not budget:
        return {}
    if found is None:
        try:
            found = lint_file(ctx.root, rel)
        except ValueError:
            found = []
    out = {it["id"]: [] for it in budget}
    blocks = [it for it in items if it["kind"] in "HXT"]
    for f in found:
        if f.kind not in RESOURCE_LINT:
            continue
        owner = next((it for it in blocks if it["line_start"] <= f.line <= it["line_end"]), None)
        if owner is None:
            for it in budget:
                out[it["id"]].append((f.line, f.kind, False))
        elif owner["id"] in out:
            out[owner["id"]].append((f.line, f.kind, True))
    return out


# Q20: a property-test item (`uses: property-test`) is done when its checker
# verifies and its suite, outside the verified code (Dafny @Test methods; a
# Verus #[cfg(test)] module), passes. `--report --strict` runs the compiled
# checks (`scripts/vcheck --test`, dvl.dafny.test / dvl.verus.test) of every
# unit, crate or file of the report that holds such an item, behind vcheck's
# H5 guards, and fails on a failing test, on no test at all, or on a run that
# gives no verdict.

def property_test_targets(ctx, files):
    """[(lang, target path, label, [item ids])]: per test target (a Dafny unit
    directory or file; a Verus crate directory, or a file outside its crate's
    module tree) of the report files, the property-test items it holds."""
    out = {}
    for rel in files:
        if rel.endswith(".specimen") or core.lang_of(rel) not in ("d", "v"):
            continue
        ids = [it["id"] for it in ctx.items_in([rel]) if "property-test" in it["uses"]]
        if not ids:
            continue
        lang, path = core.lang_of(rel), ctx.root / rel
        target = path
        if lang == "d" and (path.parent / "dfyconfig.toml").is_file():
            target = path.parent
        elif lang == "v":
            crate = crate_dir_rel(ctx.root, rel)
            if crate:
                try:
                    tree = [Path(f).resolve() for f, _, _ in
                            V.crate_files(V.load_crate(ctx.root / crate).root)]
                except (ValueError, OSError):
                    tree = []
                if path.resolve() in tree:
                    target = ctx.root / crate
        key = (lang, str(target))
        if key not in out:
            out[key] = (lang, target, core.show(target, ctx.root), [])
        out[key][3].extend(ids)
    return list(out.values())


def run_property_tests(ctx, files):
    """[(path, line, text)] for every failing property-test target (Q20)."""
    bad = []
    for lang, target, label, ids in property_test_targets(ctx, files):
        t = core.Target(lang, target, ctx.root)
        try:
            core.h5_guard(ctx.root, t)
            core.slot_guard(ctx.root, t)
        except core.Refusal as e:
            bad.append((label, 0, f"{' '.join(ids)}: the property tests cannot run yet ({e})"))
            continue
        res = core.lib(lang).test(str(target))
        passed = sum(1 for v in res.per_symbol.values() if v == "passed")
        failed = sum(1 for v in res.per_symbol.values() if v == "failed")
        print(f"  property tests ({' '.join(ids)}): {label}: {res.verdict} — {passed} passed, "
              f"{failed} failed")
        if res.verdict != "verified" or not passed:
            why = "no test ran" if not passed and not failed else (
                f"{failed} failed" if failed else f"no verdict ({res.verdict}, stage {res.stage})")
            bad.append((label, 0, f"{' '.join(ids)}: `scripts/vcheck --test {label}`: {why}"))
    return bad


# =====================================================================================
# Construct forms (QPLAN §6 Q43, with §6 Q29's sweep for `stable`)
# =====================================================================================

# An H, X or T block whose construct a correct answer could otherwise avoid at
# the pin carries `// form: <rule>[, <rule>]` lines (dvl.forms: the closed
# vocabulary bv-exec, no-nl, nl-steps:<k>, trigger, stable, and the static
# checks). firsttry checks a block's forms once its hole is closed:
#   --check           a code T item's first try records as a fail when a form
#                     fails (form_failures on the scratch copy it verified);
#   --exit            judge_block adds a reason per failing form;
#   --report          a finished block (code, no hole form) whose forms fail is
#                     reported as `form` (the hole stays unfinished); `stable`
#                     runs only under --strict, which fails on any;
#   --lint-hollow     form lines parse, name rules of the vocabulary that fit
#                     the block's language, and sit in H, X or T blocks that
#                     hold code; `cfree:` and `triv:` lines stay in the twins;
#   --empty-body      (author) the twin's forms equal the learner's, the twin
#                     meets them (`stable`: its sweep), and every `// cfree:`
#                     answer of the twin fails verification or a form.
# An item's rules are the union of its block's form lines now and as shipped
# (the shipped reference): deleting a form line does not lift it. `stable`
# is the sweep of vcheck --brittleness (Verus: seeds 1-3; Dafny: seeds 1-3
# under each bundled solver, --solvers): every declaration of the block, and
# every declaration of the file outside all H, X and T blocks (the helpers it
# may call), verifies in every row (Verus: no error and no hole in it), and the
# block carries no resource attribute.

def item_forms(ctx, it, sit=None):
    """The form rules of an item (its block's form lines, united with the
    shipped block's when the baseline holds it). sit: (shipped item, text)."""
    rules = F.block_rules(ctx.lines(it["file"]), it["line_start"], it["line_end"])
    if sit is not None and sit[0]["file"] == it["file"]:
        s_item, stext = sit
        rules += [r for r in F.block_rules(stext.split("\n"), s_item["line_start"],
                                           s_item["line_end"]) if r not in rules]
    return rules


def hxt_blocks(items):
    return [(i["line_start"], i["line_end"]) for i in items if i["kind"] in "HXT"]


def given_names(text, rel, it):
    """The names of the declarations of an item's block in `text` besides the
    item's own (dvl.forms.block_decl_names): the given code of the block as
    shipped. None when the text does not parse or holds no such block."""
    lang = core.lang_of(rel)
    if lang not in ("d", "v"):
        return None
    try:
        src = F.parse(text, lang, rel)
    except ValueError:
        return None
    items, _ = ci.parse_items(rel, text)
    blk = next((x for x in items if x["id"] == it["id"]), None)
    if blk is None:
        return None
    return F.block_decl_names(src, lang, (blk["line_start"], blk["line_end"]))


def shipped_given(sit):
    """given_names of the shipped block (sit: (shipped item, text) or None)."""
    return None if sit is None else given_names(sit[1], sit[0]["file"], sit[0])


def static_forms(text, rel, it, rules, given=None):
    """{rule: (ok, why)} of the static rules (and stable's static half) on one
    block of `text` (the file as it is, or a scratch variant with the same
    lines); given: the block's shipped declarations besides the item's own,
    left out of the answer region (None: unknown)."""
    lang = core.lang_of(rel)
    if lang not in ("d", "v") or not rules:
        return {}
    items, _ = ci.parse_items(rel, text)
    blk = next((x for x in items if x["id"] == it["id"]), it)
    try:
        src = F.parse(text, lang, rel)
    except ValueError:
        return {r: (False, "the file does not parse") for r in rules}
    return F.check_static(src, lang, rules, (blk["line_start"], blk["line_end"]),
                          hxt_blocks(items), given)


def sweep_solvers(lang):
    """The rows' solvers of the `stable` sweep: Dafny every bundled solver."""
    return D.solver_names() if lang == "d" else [None]


def stable_target(root, rel, lang):
    """What a stable sweep runs for a file under `root`: its Dafny unit or its
    Verus crate (the program the learner loop verifies), else the file."""
    p = Path(root) / rel
    if lang == "d" and (p.parent / "dfyconfig.toml").is_file():
        return p.parent
    if lang == "v":
        got = core.verus_crate_of(p)
        if got is not None:
            return got[0]
    return p


def file_symbols(path, text, rel, lang):
    """[(symbol, line)] of a file's declarations under the libraries'
    per_symbol keys (Dafny `Mod.Name`; Verus `m::f` within its crate)."""
    out = []
    if lang == "d":
        src = D.parse_source(text, str(path))
        return [(d.qual, d.line) for d in src.decls if d.kind in D.METHODLIKE]
    modpath = next((m for f, m in core.verus_file_modpaths(path)
                    if Path(f).resolve() == Path(path).resolve()), "")
    src = V.vs.parse(text)
    for it in src.walk():
        if it.kind == "fn" and it.in_verus:
            out.append(("::".join(filter(None, [modpath, V.vs.item_symbol(it)])),
                        src.line_of(it.head)))
    return out


STABLE_OK = {"d": ("verified",), "v": ("verified", "no-error")}


def stable_judge(rows, path, text, rel, it):
    """(ok, why) of one block over a sweep's rows, or None when a row gave no
    verdict (killed(memory), a refusal, a tool error): never a pass. `path`
    is the verified file (scratch or real), `text` its text."""
    lang = core.lang_of(rel)
    items, _ = ci.parse_items(rel, text)
    blk = next((x for x in items if x["id"] == it["id"]), it)
    lo, hi = blk["line_start"], blk["line_end"]
    blocks = hxt_blocks(items)
    try:
        syms = file_symbols(path, text, rel, lang)
    except ValueError:
        return False, "the file does not parse"
    mine = [s for s, ln in syms if lo <= ln <= hi]
    helpers = [s for s, ln in syms if not any(a <= ln <= b for a, b in blocks)]
    ap = str(Path(path).resolve())
    seen = False
    for r in rows:
        res = r.result
        if res.verdict in ("killed(memory)", "refused") or (
                res.verdict == "error" and res.stage not in ("parse", "resolve")):
            return None
        errs = [d.line for d in res.diagnostics if d.severity == "error" and d.file == ap
                and lo <= d.line <= hi]
        if errs:
            return False, f"an error at line {errs[0]} under {r.label}"
        if res.stage in ("parse", "resolve") and res.verdict != "verified":
            return False, f"the run stopped at stage {res.stage} under {r.label}"
        for s in mine + helpers:
            st = res.per_symbol.get(s)
            if st is None:
                continue
            if s in mine:
                seen = True
            if st not in STABLE_OK[lang]:
                return False, (f"{'its declaration' if s in mine else 'a helper outside every block'}"
                               f" at line {dict(syms)[s]} is {st} under {r.label}")
    if not seen:
        return False, "no verification task ran for the block"
    return True, ""


def form_failures(static, stable=None):
    """[(rule, why)] of the failing rules: the static results, then stable's
    sweep result (None: not run)."""
    out = [(r, why) for r, (ok, why) in static.items() if not ok]
    if stable is not None and not stable[0] and not any(r == "stable" for r, _ in out):
        out.append(("stable", stable[1]))
    return out


def form_text(fails):
    return "; ".join(f"form {r} not met ({why})" if why else f"form {r} not met"
                     for r, why in fails)


def run_stable(target_path, lang, root, seeds=None):
    """The `stable` sweep's rows on a target (a file, unit or crate)."""
    t = core.Target(lang, Path(target_path), Path(root))
    return core.brittleness_rows(t, sweep_solvers(lang), seeds)


# =====================================================================================
# --check
# =====================================================================================

def check_targets(ctx):
    """P items, and T items with slots, in the exercise files (specimens
    included) and the learner Python files."""
    return [it for it in ctx.items_in(ctx.exercises + ctx.harness)
            if it["kind"] == "P" or (it["kind"] == "T" and it["slots"])]


# Predictions before test-outs (QPLAN §8.0, §6 Q23). From the moderate tier on,
# a module's file puts the prediction block before the T block, because a T
# item can settle a prediction of its module (a measure, a trigger). So --check
# records no T item's first try (slot or code) while any P item of the module
# has no recorded first try; that T item is refused (nothing recorded, exit 1)
# until the predictions are recorded by an earlier --check. Q01-Q03 keep their
# order (T items first) and are not affected; the R track has no tiers and
# keeps its own order.

def predictions_first(rec):
    """True for a Q module of the moderate tier or later (Q04 on)."""
    return rec.get("track") == "Q" and int(rec["id"][1:]) >= 4


def waiting_predictions(ctx):
    """The module's P item ids without a recorded first try (all items of the
    module, specimens included), when its T items wait for them; else []."""
    if not predictions_first(ctx.rec):
        return []
    return sorted((it["id"] for it in ctx.items if it["kind"] == "P" and it["id"] not in ctx.calib),
                  key=lambda iid: (int(re.search(r"\.P(\d+)", iid).group(1)), iid))


def waits_note(iid, waiting):
    return (f"  · {iid}  waits for the module's predictions ({len(waiting)} P item(s) "
            f"unrecorded: {' '.join(waiting)}): record them first (fill their slots, run "
            "--check), then --check again (nothing recorded)")


# Code T items (test-outs written as code: a prompt-as-heading block, or a
# statement shipped with a hole; DV2a fix round, QPLAN §6 Q4). Their FIRST TRY
# is defined as follows, and `--check` records it:
#   * the try is the first `--check` run at which the block is COMPLETE: it
#     holds code of the learner's and no hole form (static_holes) is left in
#     it. "Code of the learner's" means non-comment code beyond what the block
#     shipped with (the file at the shipped reference), its own
#     check lines not counted, so uncommenting the checks alone is no
#     attempt; without such a baseline, any non-comment code in the block;
#   * at that run, every check line of the block that is still commented
#     (the lines under its `Uncomment as you go:` header, and Verus #[ignore]
#     lines) is enabled in a scratch copy of its unit or crate, and the
#     pinned verifier runs there in the learner loop;
#   * the verdict is pass when the run reached verification with no error and
#     no hole inside the block (errors elsewhere in the file do not count); a
#     parse or resolution error inside the block is a fail; a stop outside the
#     block (or a run with no verdict) records nothing ("could not run");
#   * the record is `predict` (a genuine first try) when every check the block
#     shipped with is still commented at that run, and `observed` (shown,
#     never a first-try pass) when the learner had uncommented one: they may
#     have seen the verifier's answer. Without a shipped branch to compare
#     with, it is `predict` only when the block still holds a commented check;
#   * a shipped check deleted from the block refuses the item (exit 1): restore
#     it, then --check. The record's hash is that of the normalized block.
# `--report --strict` counts a code T block that is empty or still holds a hole
# as unfilled, and an unrecorded one as an unrecorded first try.

def is_code_t(it):
    return it["kind"] == "T" and not it["slots"] and not it["format"]


def code_t_items(ctx):
    return [it for it in ctx.items_in(ctx.exercises) if is_code_t(it)
            and not it["file"].endswith(".specimen")]


def _code_lines(text, rel, lo, hi):
    """The block's non-comment code lines after its marker, normalized."""
    code, _ = ci.scan(rel, text)
    return [sr_norm_ws(code[ln - 1]) for ln in range(lo + 1, hi + 1) if code[ln - 1].strip()]


def code_t_open(ctx, it, sit=None):
    """None when the code T block is complete (see above), else why not:
    "empty" (no code of the learner's) or "hole" (a hole form is left).
    sit: (shipped item, shipped text) or None."""
    rel = it["file"]
    text = ctx.text(rel)
    now = _code_lines(text, rel, it["line_start"], it["line_end"])
    if sit is not None and sit[0]["file"] == rel:
        s_item, stext = sit
        sraw = stext.split("\n")
        checks = set()
        for ln in sr_commented_checks(sraw, rel, s_item["line_start"], s_item["line_end"]):
            line = _uncomment(sraw[ln - 1], rel)
            checks.update(x for x in _code_lines("\n" + line, rel, 1, 2))
        was = [x for x in _code_lines(stext, rel, s_item["line_start"], s_item["line_end"])
               if x not in checks]
        if [x for x in now if x not in checks] == was:
            return "empty"
    elif not now:
        return "empty"
    if static_holes(text, rel, it, ctx.root):
        return "hole"
    return None


def code_t_kind(ctx, it, sit):
    """(kind predict|observed, problem or None) of a complete code T block
    (see above); sit: (shipped item, shipped text) or None."""
    rel, raw = it["file"], ctx.lines(it["file"])
    lo, hi = it["line_start"], it["line_end"]
    now = len(sr_commented_checks(raw, rel, lo, hi))
    if sit is None or sit[0]["file"] != rel:
        return ("predict" if now else "observed"), None
    s_item, stext = sit
    shipped = len(sr_commented_checks(stext.split("\n"), rel, s_item["line_start"],
                                      s_item["line_end"]))
    present = len(_check_lines(raw, rel, it, stext, s_item))
    if present < shipped:
        return None, (f"{shipped - present} of its {shipped} shipped check(s) are gone: restore "
                      "them, then --check (nothing recorded)")
    return ("predict" if now >= shipped else "observed"), None


def _uncomment(line, rel):
    lead = re.escape(sr_leader(rel))
    return re.sub(rf"^(\s*){lead} ?", r"\1", line, count=1)


def code_t_try(ctx, it, sit=None):
    """(verdict pass|fail, None, form note) or (None, why, None): the block's
    checks enabled in a scratch copy, then the learner loop (see above). A
    verified block whose forms fail (QPLAN §6 Q43; `stable` runs its sweep on
    the same scratch copy) is a fail, and the note names the forms. An
    out-of-resource result inside the block is a fail; one outside it, or a
    run that gave no verdict, records nothing. sit: (shipped item, text)."""
    rel = it["file"]
    lang = core.lang_of(rel)
    raw = ctx.lines(rel)
    lo, hi = it["line_start"], it["line_end"]
    lines = list(raw)
    for ln in sr_commented_checks(raw, rel, lo, hi):
        if re.match(r"\s*#\[ignore\b", lines[ln - 1]):
            lines[ln - 1] = ""
        else:
            lines[ln - 1] = _uncomment(lines[ln - 1], rel)
    if lang == "d":
        unit = (ctx.root / rel).parent
        copy_rel = unit.relative_to(ctx.root).as_posix() if (unit / "dfyconfig.toml").is_file() \
            else rel
    else:
        copy_rel = crate_dir_rel(ctx.root, rel) or rel
    text = "\n".join(lines)
    rules = item_forms(ctx, it, sit)
    shadow = core.shadow_tree(ctx.root, [copy_rel], "ttry")
    try:
        target = shadow / rel
        target.write_text(text, encoding="utf-8")
        res = core.lib(lang).verify(str(target))
        tpath = str(target.resolve())
        verdict, why = _code_t_verdict(res, tpath, lo, hi)
        note = None
        if verdict == "pass" and rules:
            fails = form_failures(static_forms(text, rel, it, rules, shipped_given(sit)))
            if not fails and "stable" in rules:
                judged = stable_judge(run_stable(stable_target(shadow, rel, lang), lang,
                                                 shadow), target, text, rel, it)
                if judged is None:
                    return None, "no verdict from the `stable` sweep (a run was killed or " \
                                 "errored)", None
                fails = form_failures({}, judged)
            if fails:
                verdict, note = "fail", form_text(fails)
    finally:
        core.remove_tree(shadow)
    return verdict, why, note


def _code_t_verdict(res, tpath, lo, hi):
    if res.verdict in ("refused", "killed(memory)") or (
            res.verdict == "error" and res.stage not in ("parse", "resolve")):
        return None, f"no verdict ({res.verdict}); raw output: {res.raw_dir}"
    inside = [d for d in res.diagnostics if d.severity == "error" and d.file == tpath
              and lo <= d.line <= hi]
    holes = [h for h in res.holes if h.file == tpath and lo <= h.line <= hi]
    if inside or holes:
        return "fail", None
    if res.verdict == "inconclusive":
        return None, f"no verdict (inconclusive outside the block); raw output: {res.raw_dir}"
    if res.stage != "verify" and res.verdict != "verified":
        outside = sorted(d.line for d in res.diagnostics if d.severity == "error"
                         and d.file == tpath) or [0]
        return None, (f"an error outside the block (line {outside[0]}) stops verification at "
                      f"stage {res.stage}: fix it, then --check")
    return "pass", None


def check_code_t(ctx, shipped, notes, refused):
    """Record the first try of every complete, unrecorded code T item.
    Returns the calibration rows; notes and refused are filled in place."""
    rows = []
    for it in code_t_items(ctx):
        iid = it["id"]
        if iid in ctx.calib:
            c = ctx.calib[iid]
            notes.append(f"  = {iid}  first try already recorded {c['date']}: {c['verdict']}"
                         + ("" if c["kind"] == "predict" else f" ({c['kind']})"))
            continue
        why = code_t_open(ctx, it, shipped.get(iid))
        if why:
            notes.append(f"  · {iid}  " + ("its block holds no attempt yet: write the target, "
                                          "then --check" if why == "empty" else
                                          "its hole is still open: fill it, then --check")
                         + " (nothing recorded)")
            continue
        kind, problem = code_t_kind(ctx, it, shipped.get(iid))
        if problem:
            notes.append(f"  · {iid}  {problem}")
            refused.add(iid)
            continue
        waiting = waiting_predictions(ctx)
        if waiting:
            notes.append(waits_note(iid, waiting))
            refused.add(iid)
            continue
        verdict, why, note = code_t_try(ctx, it, shipped.get(iid))
        if verdict is None:
            notes.append(f"  · {iid}  the check could not run ({why}); nothing recorded")
            refused.add(iid)
            continue
        block = "\n".join(ctx.lines(it["file"])[it["line_start"] - 1:it["line_end"]])
        rows.append([iid, kind, verdict, core.today(), sr_sha256(sr_norm_ws(block))])
        mark = "✓" if verdict == "pass" else "✗"
        tail = f": {note}" if note else ""
        if kind == "predict":
            print(f"  {mark} {iid}  first try {'passes' if verdict == 'pass' else 'fails'} "
                  f"(test-out: its checks enabled in a scratch copy){tail}")
        else:
            print(f"  · {iid}  observed {mark} (not a first try: a check of the block was "
                  f"already uncommented){tail}")
    return rows


def mode_check(ctx):
    """Record first tries. Exit 1 when any item was refused (a vacuity rule,
    fewer slots than shipped, given code not as shipped, a file gone, a check
    that could not run), so a script that relies on the status sees it; exit
    0 otherwise, "nothing new to check" included."""
    shipped = shipped_state(ctx)
    todo, notes, refused = [], [], set()
    for it in check_targets(ctx):
        iid, slots = it["id"], it["slots"]
        if iid in ctx.calib:
            c = ctx.calib[iid]
            notes.append(f"  = {iid}  first try already recorded {c['date']}: {c['verdict']}"
                         + ("" if c["kind"] == "predict" else f" ({c['kind']})"))
            continue
        if not slots:
            notes.append(f"  · {iid}  its slot is missing: restore it, fill it, then --check "
                         "(nothing recorded)")
            refused.add(iid)
            continue
        sit = shipped.get(iid)
        if sit is not None:
            if len(slots) < len(sit[0]["slots"]):
                notes.append(f"  · {iid}  {len(sit[0]['slots']) - len(slots)} of its "
                             f"{len(sit[0]['slots'])} shipped slots are missing: restore them, "
                             "fill every slot, then --check (nothing recorded)")
                refused.add(iid)
                continue
            if it["file"] == sit[0]["file"] and \
                    given_lines(ctx.text(it["file"]), it) != given_lines(sit[1], sit[0]):
                notes.append(f"  · {iid}  its given code is not as shipped: restore it, then "
                             "--check (nothing recorded)")
                refused.add(iid)
                continue
        states = [s["state"] for s in slots]
        if "unfilled" in states:
            if states.count("unfilled") < len(slots):
                notes.append(f"  · {iid}  {len(slots) - states.count('unfilled')} of "
                             f"{len(slots)} slots filled: fill every slot, then --check")
            continue
        bad = item_problems(ctx, it)
        if bad:
            for path, line, p in bad:
                notes.append(f"  · {iid}  refused ({path}:{line}): {p}; nothing recorded")
            refused.add(iid)
            continue
        if it["kind"] == "T" and waiting_predictions(ctx):
            notes.append(waits_note(iid, waiting_predictions(ctx)))
            refused.add(iid)
            continue
        todo.append(it)
    gone = set(ctx.gone)
    for iid, (sit, _) in sorted(shipped.items()):
        if sit["file"] in gone and iid not in ctx.calib and \
                (sit["kind"] == "P" or (sit["kind"] == "T" and sit["slots"])):
            notes.append(f"  · {iid}  its file {sit['file']} is gone: restore it as shipped, "
                         "fill its slots, then --check (nothing recorded)")
            refused.add(iid)
    print(f"{ctx.mid} --check")
    t_rows = check_code_t(ctx, shipped, notes, refused)
    if not todo and not t_rows:
        for n in notes:
            print(n)
        if refused:
            print(f"  refused: {len(refused)} item(s), nothing recorded for them (exit 1)")
            return core.EXIT_FAIL
        print("  nothing new to check: fill a slot (or complete a test-out block), then run "
              "--check again")
        return core.EXIT_OK
    ids = {it["id"] for it in todo}
    results = harness.run_slot_checks(ctx.root, ctx.rec, ctx.items,
                                      select=lambda it, s: it["id"] in ids,
                                      enable_filled=True, tag="firsttry") if todo else {}
    rows, to_enable = list(t_rows), any(r[1] == "predict" for r in t_rows)
    for it in todo:
        checks = results.get(it["id"], [])
        if len(checks) != len(it["slots"]) or any(c.outcome == "error" for c in checks):
            why = next((c.why for c in checks if c.outcome == "error"), "no result")
            notes.append(f"  · {it['id']}  the check could not run ({why}); nothing recorded")
            refused.add(it["id"])
            continue
        ok = all(c.outcome == "pass" for c in checks)
        kind = "predict" if all(s["state"] == "filled-disabled" for s in it["slots"]) \
            else "observed"
        to_enable = to_enable or kind == "predict"
        payloads = [harness.slot_payload_text(ctx.root, it, s) for s in it["slots"]]
        rows.append([it["id"], kind, "pass" if ok else "fail", core.today(),
                     sr_sha256("\n".join(sr_normalize_answer(p) for p in payloads))])
        mark = "✓" if ok else "✗"
        if kind == "predict":
            print(f"  {mark} {it['id']}  first try {'passes' if ok else 'fails'}")
        else:
            print(f"  · {it['id']}  observed {mark} (not a first try: a slot was already "
                  "enabled, so this record never counts as a first-try pass)")
    for n in notes:
        print(n)
    core.append_calib(ctx.root, ctx.mid, rows)
    if rows:
        print(f"recorded {len(rows)} item(s) in "
              f"{core.show(core.calib_path(ctx.root, ctx.mid), ctx.root)}."
              + (" Now enable those slots (uncomment those checks) in your files and see what "
                 "the tool says." if to_enable else ""))
    if refused:
        print(f"refused: {len(refused)} item(s), nothing recorded for them (exit 1)")
        return core.EXIT_FAIL
    return core.EXIT_OK


# =====================================================================================
# --report
# =====================================================================================

def report_files(ctx):
    """(files, notes): the exercise and learner Python files, plus each exit
    file once scored."""
    files, notes = list(ctx.exercises) + list(ctx.harness), []
    for rel in ctx.exits:
        xs = [i["id"] for i in ctx.items_in([rel]) if i["kind"] == "X"]
        if any(x in ctx.calib for x in xs):
            files.append(rel)
        else:
            notes.append(f"exit {rel}: not scored yet; it joins this report after "
                         f"`scripts/firsttry.sh {ctx.mid} --exit` records its first run")
    return files, notes


def lever_findings(ctx, files):
    """[(file, 0, message)] of the lever freeze on the report files (Δ199, DV5c):
    an automation-off lever (`{:disableNonlinearArithmetic}`, `{:induction
    false}` and their `@` forms) that the module's freeze pin records for a file
    (`frozen_levers`, written by specfreeze --pin) and the file no longer
    carries, as `specfreeze --check` reports it (freeze-lever-removed). Static;
    [] without a pin."""
    import tomllib
    from collections import Counter
    p = ctx.root / "expected" / f"{ctx.mid}.freeze"
    if not p.is_file():
        return []
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError):
        return [(f"expected/{ctx.mid}.freeze", 0, "the freeze pin is malformed (the lever "
                 "freeze could not run)")]
    pinned = {e.get("path"): e for e in data.get("file", []) if isinstance(e, dict)}
    out = []
    for rel in files:
        want = (pinned.get(rel) or {}).get("frozen_levers")
        if not want or core.lang_of(rel) not in ("d", "v"):
            continue
        try:
            have = LEV.off_levers(ctx.root / rel)
        except (LEV.LeverError, OSError, UnicodeDecodeError):
            out.append((rel, 0, "the file does not parse, so the lever freeze cannot run"))
            continue
        for key in sorted(Counter(want) - Counter(have)):
            out.append((rel, 0, f"freeze-lever-removed — {key}: an automation-off lever the "
                        "file shipped with is gone (specfreeze --check reports it too)"))
    return out


def first_try_text(c):
    mark = "✓" if c["verdict"] == "pass" else "✗"
    return f"first try {mark}" if c["kind"] == "predict" else (
        f"exit run {mark}" if c["kind"] == "exit" else f"observed {mark} (not a first try)")


def form_findings(ctx, files, shipped, sweep):
    """[(path, line, text)] for the finished H, X and T blocks of the report
    files whose construct forms fail (QPLAN §6 Q43): a block counts once it
    holds code and no hole form (a code T block: once complete). `sweep`
    (--strict) also runs `stable`'s sweep, once per unit, crate or file."""
    out, groups = [], {}
    for rel in files:
        lang = core.lang_of(rel)
        if lang not in ("d", "v") or rel.endswith(".specimen"):
            continue
        text = ctx.text(rel)
        for it in ctx.items_in([rel]):
            if it["kind"] not in "HXT" or it["format"] == "verdict":
                continue
            sit = shipped.get(it["id"])
            rules = item_forms(ctx, it, sit)
            if not rules:
                continue
            if is_code_t(it):
                if code_t_open(ctx, it, sit):
                    continue
            elif not block_has_code(text, rel, it) or static_holes(text, rel, it, ctx.root):
                continue
            fails = form_failures(static_forms(text, rel, it, rules, shipped_given(sit)))
            if fails:
                out.append((rel, it["line_start"], f"{it['id']}: {form_text(fails)}"))
            elif "stable" in rules and sweep:
                key = (lang, str(stable_target(ctx.root, rel, lang)))
                groups.setdefault(key, []).append((rel, it))
    for (lang, target), blocks in groups.items():
        rows = run_stable(target, lang, ctx.root)
        for rel, it in blocks:
            got = stable_judge(rows, ctx.root / rel, ctx.text(rel), rel, it)
            if got is None:
                out.append((rel, it["line_start"], f"{it['id']}: form stable: no verdict (a "
                            "run of the sweep was killed or errored)"))
            elif not got[0]:
                out.append((rel, it["line_start"], f"{it['id']}: "
                            + form_text([("stable", got[1])])))
    return out


def stable_pending(ctx, files):
    """Item ids of the report files whose forms include `stable` (checked by
    --strict only: its sweep runs the verifier)."""
    return [it["id"] for rel in files for it in ctx.items_in([rel])
            if it["kind"] in "HXT" and "stable" in F.block_rules(ctx.lines(rel),
                                                                 it["line_start"],
                                                                 it["line_end"])]


def mode_report(ctx, strict):
    files, notes = report_files(ctx)
    shipped = shipped_state(ctx)
    keys = ("unfilled", "disabled", "vacuous", "commented", "did", "missing", "banned",
            "unattempted", "budget", "holes")
    tot = {k: [] for k in keys}
    items = ctx.items_in(files)
    # enabled slots of recorded items are checked (an unrecorded one is not run:
    # its ✓/✗ would answer the prediction, H5)
    run_ids = {it["id"] for it in items if it["id"] in ctx.calib and
               any(s["state"] == "enabled" for s in it["slots"])}
    results = harness.run_slot_checks(
        ctx.root, ctx.rec, ctx.items,
        select=lambda it, s: it["id"] in run_ids and s["state"] == "enabled",
        enable_filled=False, tag="report") if run_ids else {}
    failing = []
    nslots = sum(len(it["slots"]) for it in items)
    print(f"{ctx.mid} report — {len(files)} file(s), {nslots} slot(s)")
    for it in items:
        if it["kind"] in "WCA":
            continue
        parts = []
        for s in it["slots"]:
            if s["state"] != "enabled":
                parts.append(s["state"])
                continue
            got = [c for c in results.get(it["id"], []) if c.line == s["line"]
                   and c.file == s["file"]]
            if not got:
                parts.append("enabled" + ("" if it["id"] in ctx.calib else
                                          " (first try unrecorded: run --check)"))
            elif got[0].outcome == "pass":
                parts.append("enabled ✓")
            else:
                parts.append("enabled ✗" if got[0].outcome == "fail" else "enabled (not run)")
                failing.append((s["file"], s["line"], f"{it['id']}: enabled slot "
                                + ("fails" if got[0].outcome == "fail" else
                                   f"could not run ({got[0].why})")))
        if is_code_t(it) and not it["file"].endswith(".specimen"):
            st = code_t_open(ctx, it, shipped.get(it["id"]))
            parts = ["test-out: " + {"empty": "empty", "hole": "hole open"}.get(st, "attempted")]
            line = f"  {it['id']:<9} " + parts[0]
        else:
            line = f"  {it['id']:<9} " + (f"{it['format'] or 'slot'}: " + "; ".join(parts)
                                          if parts else it["kind"] + " item")
        c = ctx.calib.get(it["id"])
        if c:
            line += f" · {first_try_text(c)} ({c['date']})"
        elif it["kind"] == "P" or (it["kind"] == "T" and it["slots"]) or \
                (is_code_t(it) and not it["file"].endswith(".specimen")):
            line += " · unrecorded"
        print(line)
    for rel in files:
        f = file_findings(ctx, rel, shipped)
        for k in keys:
            tot[k] += f[k]
    tot["missing"] += gone_findings(ctx, shipped)
    tot["form"] = form_findings(ctx, files, shipped, sweep=strict)
    labels = (("missing", "missing"), ("holes", "hole"), ("unattempted", "unfilled"),
              ("vacuous", "vacuous"),
              ("commented", "to uncomment"), ("banned", "banned"), ("budget", "budget"),
              ("form", "form"), ("did", "advisory"))
    for k, label in labels:
        for path, line, msg in tot[k]:
            print(f"  {path}:{line}: {label}: {msg}")
    for path, line, msg in failing:
        print(f"  {path}:{line}: failing: {msg}")
    for n in notes:
        print(n)
    pending = stable_pending(ctx, files) if not strict else []
    if pending:
        print(f"note: the `stable` form of {' '.join(pending)} is checked by --report --strict "
              "(its sweep runs the verifier)")
    if shipped_base(ctx.root) is None:
        print("note: no `basic`, `challenge` or `main` branch to compare with: deleted slots "
              "and checks are judged by the minimum rule only")
    not_enabled = len(tot["unfilled"]) + len(tot["disabled"])
    print(f"summary: unfilled {not_enabled} (of {nslots} slot(s); {len(tot['disabled'])} "
          f"filled but not enabled) · test-outs unattempted {len(tot['unattempted'])} · "
          f"missing {len(tot['missing'])} · vacuous "
          f"{len(tot['vacuous'])} · commented checks {len(tot['commented'])} · banned "
          f"{len(tot['banned'])} · forms not met {len(tot['form'])} · failing enabled slots "
          f"{len(failing)} · missing did: {len(tot['did'])} (advisory)")
    p_items = [i["id"] for i in items if i["kind"] == "P"]
    t_items = [i["id"] for i in items if i["kind"] == "T" and i["slots"]]
    ct_items = [i["id"] for i in items if is_code_t(i) and not i["file"].endswith(".specimen")]
    rec_p = [i for i in p_items if i in ctx.calib]
    passed = [i for i in rec_p if ctx.calib[i]["kind"] == "predict" and
              ctx.calib[i]["verdict"] == "pass"]
    observed = [i for i in rec_p if ctx.calib[i]["kind"] != "predict"]
    unrec = [i for i in p_items + t_items + ct_items if i not in ctx.calib]
    pct = f" ({round(100 * len(passed) / len(rec_p))}%)" if rec_p else ""
    print(f"first-try: {len(passed)}/{len(rec_p)} recorded P item(s) passed{pct} "
          f"({len(p_items)} P item(s) in all); observed (never a pass): "
          + (" ".join(observed) if observed else "none")
          + "; unrecorded: " + (" ".join(unrec) if unrec else "none"))
    if ct_items:
        rec_t = [i for i in ct_items if i in ctx.calib]
        t_pass = [i for i in rec_t if ctx.calib[i]["kind"] == "predict" and
                  ctx.calib[i]["verdict"] == "pass"]
        print(f"test-out: {len(t_pass)}/{len(rec_t)} recorded code T item(s) passed on the first "
              f"try ({len(ct_items)} in all); skip a section only if every first try passed")
    if not strict:
        return core.EXIT_OK
    tests = run_property_tests(ctx, files)
    for path, line, msg in tests:
        print(f"  {path}:{line}: property tests: {msg}")
    # a learner Python file is done when the gate passes: zero holes and every
    # acceptance test passing (QPLAN §11.3, §11.8)
    for rel in files:
        if not rel.endswith(".py"):
            continue
        res = PY.check(ctx.root / rel, gate=True, root=ctx.root)
        if res.verdict != "verified":
            tests.append((rel, 0, "acceptance tests: " + PY.summary_line(res, rel, "gate")))
            print(f"  {rel}:0: acceptance tests: {PY.summary_line(res, rel, 'gate')}")
    if tot["holes"]:
        print(f"  Python holes still open: {len(tot['holes'])}")
    levers = lever_findings(ctx, files)
    for path, line, msg in levers:
        print(f"  {path}:{line}: lever: {msg}")
    bad = not_enabled or tot["missing"] or tot["vacuous"] or tot["commented"] or \
        tot["banned"] or failing or unrec or tot["unattempted"] or tot["budget"] or tests or \
        tot["holes"] or tot["form"] or levers
    print(f"strict: {'FAIL' if bad else 'OK'} (unfilled {not_enabled}, test-outs unattempted "
          f"{len(tot['unattempted'])}, missing "
          f"{len(tot['missing'])}, vacuous {len(tot['vacuous'])}, commented checks "
          f"{len(tot['commented'])}, banned {len(tot['banned'])}, budget "
          f"{len(tot['budget'])}, forms not met {len(tot['form'])}, failing enabled slots "
          f"{len(failing)}, failing property-test runs {len(tests)}, levers removed "
          f"{len(levers)}, unrecorded first tries {len(unrec)})")
    if unrec:
        print(f"  unrecorded: {' '.join(unrec)}: run `scripts/firsttry.sh {ctx.mid} --check`")
    return core.EXIT_FAIL if bad else core.EXIT_OK


# =====================================================================================
# --record
# =====================================================================================

def mode_record(ctx):
    files, _ = report_files(ctx)
    shipped = shipped_state(ctx)
    items = ctx.items_in(files)
    p_items = [i["id"] for i in items if i["kind"] == "P"]
    t_unrec = [i["id"] for i in items if (is_code_t(i) and not i["file"].endswith(".specimen")
                                          or (i["kind"] == "T" and i["slots"]))
               and i["id"] not in ctx.calib]
    unfilled = 0
    for rel in files:
        f = file_findings(ctx, rel, shipped)
        unfilled += len(f["unfilled"]) + len(f["disabled"]) + len(f["missing"]) + \
            len(f["unattempted"])
    unfilled += len(gone_findings(ctx, shipped))
    rec_p = [i for i in p_items if i in ctx.calib]
    passed = sum(1 for i in rec_p if ctx.calib[i]["kind"] == "predict" and
                 ctx.calib[i]["verdict"] == "pass")
    ft = f"first-try {passed}/{len(p_items)}" + (
        f" ({round(100 * passed / len(p_items))}%)" if p_items else "")
    x_ids = [i["id"] for i in ctx.items_in(ctx.exits) if i["kind"] == "X"]
    if x_ids and any(i in ctx.calib for i in x_ids):
        ex = (f"exit {sum(1 for i in x_ids if ctx.calib.get(i, {}).get('verdict') == 'pass')}"
              f"/{len(x_ids)}")
    else:
        ex = "exit not run"
    row = (f"| {core.today()} | {ctx.mid} | calib | {ft}; {ex} | unfilled {unfilled}; "
           f"unrecorded {len(p_items) - len(rec_p) + len(t_unrec)} |")
    gb = ctx.root / "instructor" / "gradebook.md"
    if not gb.is_file():
        die(f"{core.show(gb, ctx.root)} does not exist", core.EXIT_REFUSED)
    text = gb.read_text(encoding="utf-8")
    with gb.open("a", encoding="utf-8") as fh:
        fh.write(("" if text.endswith("\n") or not text else "\n") + row + "\n")
    print(f"appended to instructor/gradebook.md:\n{row}")
    return core.EXIT_OK


# =====================================================================================
# --exit
# =====================================================================================

def block_has_code(text, rel, it):
    code, _ = ci.scan(rel, text)
    return any(code[ln - 1].strip() for ln in range(it["line_start"] + 1, it["line_end"] + 1))


def crate_dir_rel(root, rel):
    """The repo-relative crate directory (holding Cargo.toml) of a Verus file."""
    d = (Path(root) / rel).parent
    while d != Path(root) and d != d.parent:
        if (d / "Cargo.toml").is_file():
            return d.relative_to(root).as_posix()
        d = d.parent
    return None


def exit_run(ctx, rel, xs):
    """{item id: (status, reasons)} for the X blocks of one exit file, each
    judged independently; status in pass | fail | unattempted. Returns None
    when the verifier could not produce a verdict (nothing may be recorded).
    A block's construct forms (QPLAN §6 Q43) are judged on the run's text:
    the static ones on every attempted block, `stable`'s sweep on a block that
    passes otherwise."""
    lang = core.lang_of(rel)
    text = ctx.text(rel)
    raw = text.split("\n")
    judged, blanked = {}, set()
    charges = rlimit_charges(ctx, rel)
    shipped = shipped_state(ctx)
    rules = {it["id"]: item_forms(ctx, it, shipped.get(it["id"])) for it in xs}
    for _ in range(len(xs) + 1):
        shadow = None
        try:
            run_text = text
            if blanked:
                copy_rel = rel if lang == "d" else crate_dir_rel(ctx.root, rel) or rel
                shadow = core.shadow_tree(ctx.root, [copy_rel], "exit")
                lines = list(raw)
                for it in xs:
                    if it["id"] in blanked:
                        for ln in range(it["line_start"], it["line_end"] + 1):
                            lines[ln - 1] = ""
                run_text = "\n".join(lines)
                (shadow / rel).write_text(run_text, encoding="utf-8")
                target = shadow / rel
            else:
                target = ctx.root / rel
            res = core.lib(lang).verify(str(target))
            if res.verdict in ("refused", "killed(memory)") or (
                    res.verdict == "error" and res.stage not in ("parse", "resolve")):
                print(f"  the verifier gave no verdict on {rel} ({res.verdict}); raw output: "
                      f"{res.raw_dir}")
                return None
            tpath = str(Path(target).resolve())
            errs = [d for d in res.diagnostics if d.severity == "error" and d.file == tpath]
            holes = [h for h in res.holes if h.file == tpath]
            stage_stop = res.stage in ("parse", "resolve") and res.verdict != "verified"
            newly = []
            for it in xs:
                if it["id"] in judged or it["id"] in blanked:
                    continue
                lo, hi = it["line_start"], it["line_end"]
                e = [d for d in errs if lo <= d.line <= hi]
                if stage_stop:
                    if e:
                        judged[it["id"]] = ("fail", [f"error at line {e[0].line}"])
                        newly.append(it["id"])
                    continue
                fails = None
                if rules[it["id"]] and block_has_code(text, rel, it):
                    fails = form_failures(static_forms(run_text, rel, it, rules[it["id"]],
                                                       shipped_given(shipped.get(it["id"]))))
                judged[it["id"]] = judge_block(ctx, rel, it, e, [h for h in holes
                                                                 if lo <= h.line <= hi],
                                               charges.get(it["id"], []), fails)
            if not stage_stop:
                sweep = None
                for it in xs:
                    st, reasons = judged.get(it["id"], (None, None))
                    if st != "pass" or "stable" not in rules[it["id"]]:
                        continue
                    if sweep is None:
                        root = shadow if shadow is not None else ctx.root
                        sweep = run_stable(stable_target(root, rel, lang), lang, root)
                    got = stable_judge(sweep, target, run_text, rel, it)
                    if got is None:
                        print(f"  the `stable` sweep gave no verdict on {rel} (a run was killed "
                              "or errored)")
                        return None
                    if not got[0]:
                        judged[it["id"]] = ("fail", [form_text([("stable", got[1])])])
                break
        finally:
            core.remove_tree(shadow)
        if not newly:
            outside = [d.line for d in errs] or [0]
            for it in xs:
                if it["id"] not in judged:
                    judged[it["id"]] = ("fail", [f"masked: an error outside every block "
                                                 f"(line {outside[0]}) stops verification"])
            break
        blanked |= set(newly)
    return judged


def judge_block(ctx, rel, it, errs, holes, charges=(), form_fails=None):
    """(status, reasons) of one X block given its errors and holes, and, for a
    budget item, the resource attributes charged to it (rlimit_charges), and
    its failing construct forms (form_failures, QPLAN §6 Q43)."""
    text = ctx.text(rel)
    raw = text.split("\n")
    reasons = []
    has_code = block_has_code(text, rel, it)
    slots = it["slots"]
    if it["format"] == "verdict":
        if not slots or all(s["state"] == "unfilled" for s in slots):
            return "unattempted", ["its verdict slot is unfilled"]
        res = harness.verdict_outcome(ctx.root, ctx.mid, it, ctx.verdict_value(it))
        return ("pass", []) if res == "pass" else ("fail", ["the verdict does not match"])
    if not has_code or holes:
        return "unattempted", ["empty" if not has_code else f"hole at line {holes[0].line}"]
    if errs:
        reasons.append(f"error at line {errs[0].line}")
    cc = sr_commented_checks(raw, rel, it["line_start"], it["line_end"])
    if cc:
        reasons.append(f"commented check at line {cc[0]}")
    left = [s for s in slots if s["state"] != "enabled"]
    if left:
        reasons.append(f"slot {left[0]['state']} at line {left[0]['line']}")
    miss = sr_need_missing(text, rel, it)
    if miss:
        reasons.append(f"{len(miss)} `need:` fragment(s) not in its code")
    if it["min"]:
        good = sum(1 for s in slots if s["state"] == "enabled")
        if good < it["min"]:
            reasons.append(f"{good}/{len(slots)} slots enabled, {it['min']} needed")
    if charges:
        line, kind, own = charges[0]
        reasons.append(f"a resource attribute at line {line} ({kind}"
                       + ("" if own else ", outside every item block") + "): a budget item "
                       "proves at the pinned limit")
    if form_fails:
        reasons.append(form_text(form_fails))
    return ("fail", reasons) if reasons else ("pass", [])


def threshold(rec, results):
    """(needed, out of, per-language floor text or None, per-language ok),
    or None when the module pins no numeric threshold."""
    rule = exit_rule(rec)
    if rule is None or "need" not in rule:
        return None
    num, den = rule["need"]
    total = len(results)
    need = math.ceil(total * num / den)
    lang_ok, ftxt = True, None
    floor = rule.get("per_lang")
    if floor:
        parts = []
        for lang in ("d", "v"):
            mine = [ok for iid, ok in results if iid.endswith(lang) and not iid.endswith("py")]
            if not mine:
                lang_ok = False if floor[0] == "min" else lang_ok
                continue
            n_need = math.ceil(len(mine) * floor[1] / floor[2]) if floor[0] == "frac" \
                else floor[1]
            parts.append(f"{core.LANG_NAMES[lang]} {sum(mine)}/{len(mine)} (≥{n_need})")
            lang_ok = lang_ok and sum(mine) >= n_need
        ftxt = ", ".join(parts)
    return need, total, ftxt, lang_ok


def mode_exit(ctx):
    """Score the exit: judge every X block of every exit file, then record the
    first run on which every unrecorded block holds an attempt (one sitting
    across both languages; spec §3.10)."""
    if not ctx.exits:
        rule = exit_rule(ctx.rec) or {}
        die(f"{ctx.mid} has no exit file in MODULES.toml"
            + (f": {REVIEWS_ONLY}" if rule.get("reviews") else ""), core.EXIT_REFUSED)
    files = []
    empty = []
    for rel in ctx.exits:
        xs = [i for i in ctx.items_in([rel]) if i["kind"] == "X"]
        if not xs:
            # QPLAN §30 Q50: Q13-Q15 have one timed item, so one exit file of the
            # pair ships with no block; it is skipped, not refused (DV5b Q15 lane)
            empty.append(rel)
            continue
        judged = exit_run(ctx, rel, xs)
        if judged is None:
            die("no exit score: the verifier gave no verdict (fix the toolchain or the memory "
                "cap, then run --exit again)")
        files.append((rel, xs, judged))
    if not files:
        die(f"{' and '.join(empty)} {'has' if len(empty) == 1 else 'have'} no X items",
            core.EXIT_REFUSED)
    all_x = [it for _, xs, _ in files for it in xs]
    fresh = [it for it in all_x if it["id"] not in ctx.calib]
    status = {it["id"]: judged[it["id"]] for _, xs, judged in files for it in xs}
    unattempted = [it["id"] for it in fresh if status[it["id"]][0] == "unattempted"]
    record = bool(fresh) and not unattempted
    rows = []
    for rel, xs, judged in files:
        print(f"{ctx.mid} exit — {rel}")
        for it in xs:
            st, reasons = judged[it["id"]]
            now = "✓" if st == "pass" else ("— unattempted: " if st == "unattempted"
                                             else "✗ ") + "; ".join(reasons)
            c = ctx.calib.get(it["id"])
            if c:
                first = f"first run {'✓' if c['verdict'] == 'pass' else '✗'} ({c['date']})"
            elif record:
                block = "\n".join(ctx.lines(rel)[it["line_start"] - 1:it["line_end"]])
                rows.append([it["id"], "exit", "pass" if st == "pass" else "fail",
                             core.today(), sr_sha256(sr_norm_ws(block))])
                first = "first run: recorded now"
            else:
                first = "not recorded"
            print(f"  {it['id']:<8} now {now} · {first}")
    if unattempted:
        print(f"  nothing recorded: {' '.join(unattempted)} hold no attempt yet (empty, a hole, "
              "or an unfilled slot). The exit is scored once, on the first run where every "
              "block of every exit file holds an attempt; a guess counts.")
    core.append_calib(ctx.root, ctx.mid, rows)
    ctx.calib = core.read_calib(ctx.root, ctx.mid)
    results = [(it["id"], ctx.calib.get(it["id"], {}).get("verdict") == "pass") for it in all_x]
    score = sum(ok for _, ok in results)
    unrec = sum(1 for it in all_x if it["id"] not in ctx.calib)
    th = threshold(ctx.rec, results)
    if th is None:
        rule = exit_rule(ctx.rec) or {}
        why = REVIEWS_ONLY if rule.get("reviews") else \
            f"tier {ctx.rec['tier'] or 'none'}: no exit threshold is pinned for it"
        print(f"{ctx.mid} exit: {score}/{len(results)} ({why})"
              + (f"; {unrec} not yet recorded" if unrec else ""))
        return core.EXIT_OK
    need, total, ftxt, lang_ok = th
    verdict = "PASS" if score >= need and lang_ok and not unrec else "FAIL"
    print(f"{ctx.mid} exit: {score}/{total} (threshold {need}"
          + (f"; per language {ftxt}" if ftxt else "") + f") {verdict}"
          + (f"; {unrec} item(s) not yet recorded" if unrec else ""))
    return core.EXIT_OK if verdict == "PASS" else core.EXIT_FAIL


# =====================================================================================
# --lint-hollow (static)
# =====================================================================================

PROOF_NOTE = re.compile(r'#\[verifier::proof_note\("([^"]*)"\)\]\s*assume\s*\(\s*false\s*\)')


def static_holes(text, rel, it, root=None):
    """Lines of the shipped hole forms inside a block (static; the tool counts
    for real): Dafny bodyless lemma/method/function with ensures, `assume`;
    Verus labelled `assume(false)`, `admit()`, external_body, and the
    spec-definition hole `uninterp spec fn` (QPLAN §14.0, Δ8); Python (DV4) a
    function whose body is `raise NotImplementedError("<its item id>")`,
    counted by the frozen core of the course at `root`."""
    lang = core.lang_of(rel)
    lo, hi = it["line_start"], it["line_end"]
    out = []
    if lang == "d":
        src = D.parse_source(text, rel)
        for d in src.decls:
            if d.kind in D.METHODLIKE and d.body is None and d.ensures and lo <= d.line <= hi:
                out.append(d.line)
        for t in src.toks:
            if t.kind == "id" and t.text == "assume" and lo <= t.line <= hi:
                out.append(t.line)
    elif rel.endswith(".py"):
        try:
            found = PY.source_holes(text, root=root)
        except SyntaxError:
            found = []
        out += [line for item, _, line in found if item == it["id"] and lo <= line <= hi]
    elif lang == "v":
        code, _ = ci.scan(rel, text)
        raw = text.split("\n")
        for ln in range(lo, hi + 1):
            c, r = code[ln - 1], raw[ln - 1]
            if re.search(r"\bassume\s*\(|\badmit\s*\(|\buninterp\s+spec\s+fn\b", c) \
                    or "verifier::external_body" in r or "verifier(external_body)" in r:
                out.append(ln)
    return sorted(set(out))


def lint_hollow_module(ctx):
    probs = list(ctx.errors)
    files = ctx.exercises + ctx.exits + ctx.harness
    if not files:
        probs.append(f"{ctx.mid}: no exercise or exit file exists (an empty list fails)")
    for rel in files:
        text, raw = ctx.text(rel), ctx.lines(rel)
        for it in ctx.items_in([rel]):
            at = f"{rel}:{it['line_start']}"
            for s in it["slots"]:
                if s["state"] != "unfilled":
                    probs.append(f"{s['file']}:{s['line']}: {it['id']}: slot ships "
                                 f"{s['state']}, not unfilled")
            if not it["slots"] and (it["kind"] == "P" or (it["kind"] in "XT" and it["format"])):
                probs.append(f"{at}: {it['id']}: no slot (every P item and every verdict X/T "
                             "item ships one)")
            if it["format"] == "value" and core.lang_of(rel) == "d" and \
                    core.gu.DAFNY_UNIT.fullmatch(rel):
                probs.append(f"{at}: {it['id']}: a Dafny value slot lives in a specimen or a "
                             "given-only check unit, never in a hole-bearing unit file (Δ2)")
            if it["format"] == "obligation" and not sr_labels(raw):
                probs.append(f"{at}: {it['id']}: an obligation specimen carries `// [x]` labels")
            if it["kind"] == "H":
                hl = static_holes(text, rel, it, ctx.root)
                if not hl:
                    probs.append(f"{at}: {it['id']}: an H item ships a hole form")
            if it["kind"] == "X" and it["format"] != "verdict" and \
                    block_has_code(text, rel, it) and not static_holes(text, rel, it, ctx.root):
                probs.append(f"{at}: {it['id']}: an X item ships empty or with a hole form "
                             "(this one would score as attempted)")
            if it["kind"] in "HXT" and core.lang_of(rel) == "v":
                for ln in range(it["line_start"], it["line_end"] + 1):
                    m = PROOF_NOTE.search(raw[ln - 1])
                    if m and m.group(1) != it["id"]:
                        probs.append(f"{rel}:{ln}: {it['id']}: its proof_note label is not "
                                     "its own item id")
        probs += form_line_problems(ctx, rel, raw)
        for ln in sr_stray_commented_checks(raw, rel):
            probs.append(f"{rel}:{ln}: a commented check outside an `Uncomment as you go:` "
                         "block")
        for ln, line in enumerate(raw, 1):
            if SWITCH.match(line) and "SLOT:" not in line:
                probs.append(f"{rel}:{ln}: a live CHECK switch ships enabled")
        planted, bad = sr_planted(raw, rel, ctx.items_in([rel]))
        probs += [f"{rel}:{ln}: {msg}" for ln, msg in bad]
        probs += after_problems(ctx, rel, text)
        if core.lang_of(rel):
            try:
                for f in lint_file(ctx.root, rel):
                    if f.line in planted:
                        continue          # a planted trust leap of an S12 delivery (sr_planted)
                    probs.append(f"{rel}:{f.line}: lint: {f.kind}")
            except ValueError as e:
                probs.append(f"{rel}:0: lint: {e}")
        elif rel.endswith(".py"):         # DV4: every H marker sits above one counted hole
            for f in PY.lint_hollow(ctx.root / rel, root=ctx.root):
                probs.append(f"{rel}:{f.line}: python: {f.kind}")
    return probs


TWIN_ONLY_LINE = re.compile(r"^\s*(?://|#)\s*(cfree|cfree-decl|triv):")


def form_line_problems(ctx, rel, raw):
    """Problems of a learner file's construct-form lines (QPLAN §6 Q43): each
    parses into rules of the vocabulary that fit the block's language, and
    sits in an H, X or T block that holds code (not a verdict item); the
    twin-only `cfree:` and `triv:` lines never appear in a learner file."""
    out = []
    lang = core.lang_of(rel)
    items = ctx.items_in([rel])
    for ln, line in enumerate(raw, 1):
        m = TWIN_ONLY_LINE.match(line)
        if m:
            out.append(f"{rel}:{ln}: a `{m.group(1)}:` line belongs in the reference twin only")
    for ln, rules, bad in F.form_lines(raw, 1, len(raw)):
        owner = next((it for it in items if it["line_start"] <= ln <= it["line_end"]), None)
        if owner is None:
            out.append(f"{rel}:{ln}: a `form:` line outside every item block")
            continue
        iid = owner["id"]
        if lang not in ("d", "v"):
            out.append(f"{rel}:{ln}: {iid}: `form:` lines are for Dafny and Verus blocks")
            continue
        if owner["kind"] not in "HXT" or owner["format"] == "verdict":
            out.append(f"{rel}:{ln}: {iid}: a `form:` line on a {owner['kind']} item"
                       + (" with a verdict slot" if owner["format"] == "verdict" else "")
                       + "; only H, X and T blocks that hold code carry forms")
        out += [f"{rel}:{ln}: {iid}: {p}" for p in bad]
        for r in F.lang_problems(rules, lang):
            out.append(f"{rel}:{ln}: {iid}: the form {r} applies to "
                       + ("Verus" if F.FORMS[F.rule_name(r)] == "v" else "Dafny")
                       + " blocks only")
        if not rules and not bad:
            out.append(f"{rel}:{ln}: {iid}: a `form:` line names no rule")
    return out


def after_problems(ctx, rel, text):
    """Problems of a file's `// after: <item id>` lines: only specimens carry
    them (a card demo that waits for a prediction), and each names a P item,
    or a slotted T item, of an armed module."""
    out = []
    for ln, iid in core.after_items(text):
        if not rel.endswith(".specimen"):
            out.append(f"{rel}:{ln}: an `after:` line lives only in a specimen (a card demo)")
            continue
        m = ci.ITEM_ID.fullmatch(iid)
        if not m:
            out.append(f"{rel}:{ln}: `after:` names {iid!r}, which is no item id")
            continue
        if m.group(1) == ctx.mid:
            items = ctx.items
        else:
            try:
                items, _ = core.module_items(ctx.root, core.record(ctx.root, m.group(1)))
            except core.Refusal:
                items = []
        it = next((x for x in items if x["id"] == iid), None)
        if it is None or not (it["kind"] == "P" or (it["kind"] == "T" and it["slots"])):
            out.append(f"{rel}:{ln}: `after:` names {iid}, which is no prediction item (a P "
                       "item, or a T item with a slot)")
    return out


def mode_lint_hollow(root, mids, idle=None):
    if idle:
        print(f"firsttry --lint-hollow --all: {idle}: passing loudly")
        return core.EXIT_OK
    if not mids:
        print("firsttry --lint-hollow: no module to lint (an empty id list fails)")
        return core.EXIT_FAIL
    total = 0
    for mid in mids:
        ctx = Ctx(root, mid, lenient=True)
        probs = lint_hollow_module(ctx)
        for p in probs:
            print(p)
        print(f"{ctx.mid} lint-hollow: {'OK' if not probs else f'{len(probs)} problem(s)'} "
              f"({len(ctx.exercises) + len(ctx.exits) + len(ctx.harness)} file(s))")
        total += len(probs)
    return core.EXIT_OK if not total else core.EXIT_FAIL


# =====================================================================================
# --empty-body
# =====================================================================================

def hole_items(ctx):
    """[(item, rel)] of every H, X and T item whose block holds a hole form."""
    out = []
    for rel in ctx.exercises + ctx.exits + ctx.harness:
        if rel.endswith(".specimen") or (core.lang_of(rel) is None and
                                         not rel.endswith(".py")):
            continue
        text = ctx.text(rel)
        for it in ctx.items_in([rel]):
            if it["kind"] in "HXT" and static_holes(text, rel, it, ctx.root):
                out.append((it, rel))
    return out


# `// triv: <body>` in an item's block of the REFERENCE TWIN (Solutions/<path>):
# the item's own trivial body for the Verus TRIV mode, which has a default
# only for a unit, integer or bool return. One or more consecutive lines,
# joined with newlines; the body is a `{ … }` block, e.g.
#     // triv: { BigNat { limbs: Vec::new() } }
# The twin is the place because the empty-body gate is author-only and a
# trivial body is the author's probe, not learner text.
TRIV_LINE = re.compile(r"^\s*//\s*triv:\s?(.*)$")
# A trait-impl item gates each of its methods (impl_hole_methods); its twin
# names the method a trivial body is for: `// triv: from_big: { None }` (the
# continuation lines of a multi-line body carry no name).
TRIV_NAMED = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


def declared_triv_bodies(ctx, it, rel):
    """({method name or None: body}, problem or None): the `// triv:` lines of
    the item's block in its twin; a line `triv: <name>: { … }` starts the body
    of method <name> (a trait-impl item), a line without a name continues the
    current body (or starts the block's one unnamed body)."""
    twin = ctx.root / core.REF_DIR / rel
    if not twin.is_file():
        return {}, None
    text = twin.read_text(encoding="utf-8")
    items, _ = ci.parse_items(f"{core.REF_DIR}/{rel}", text)
    blk = next((x for x in items if x["id"] == it["id"]), None)
    if blk is None:
        return {}, None
    raw = text.split("\n")
    got = [m.group(1) for ln in range(blk["line_start"], blk["line_end"] + 1)
           if (m := TRIV_LINE.match(raw[ln - 1]))]
    bodies, cur = {}, None
    for line in got:
        m = TRIV_NAMED.match(line.strip())
        if m:
            cur = m.group(1)
            bodies[cur] = [m.group(2)]
        else:
            bodies.setdefault(cur, []).append(line)
    out = {}
    for name, lines in bodies.items():
        body = "\n".join(lines).strip()
        if not (body.startswith("{") and body.endswith("}")):
            return {}, (f"{core.REF_DIR}/{rel}: {it['id']}: a `triv:` body is one `{{ … }}` "
                        "block" + (f" (method {name})" if name else ""))
        out[name] = body
    return out, None


def declared_triv_body(ctx, it, rel):
    """(body or None, problem or None): the item's one unnamed `// triv:` body
    in its twin (declared_triv_bodies)."""
    bodies, problem = declared_triv_bodies(ctx, it, rel)
    if problem:
        return None, problem
    named = [k for k in bodies if k is not None]
    if named:
        return None, (f"{core.REF_DIR}/{rel}: {it['id']}: `triv: <method>:` lines go with an "
                      "impl item gated per method only (impl_hole_methods)")
    return bodies.get(None), None


def impl_hole_methods(text, rel, it):
    """[(symbol, method name)] of a Verus trait-impl item (QPLAN §30 Q65(a);
    Q14.H2v): when the first fn of the block is a method of an `impl Trait
    for Type`, every proof or exec method of that impl in the block that has
    a body and holds a hole form, by its exact symbol (`<Type as
    Trait>::method`, which dvl.verus.empty_body resolves). The same for an
    inherent `impl Type` whose block holds two or more hole methods (Q14.H5v;
    symbols `Type::method`). [] for any other item: its gate stays the first
    fn's."""
    if core.lang_of(rel) != "v":
        return []
    try:
        src, fn = _first_fn(text, it)
    except V.vs.ParseError:
        return []
    if fn is None or not fn.owner:
        return []
    lo, hi = it["line_start"], it["line_end"]
    holes = set(static_holes(text, rel, it))
    out = []
    for x in src.walk():
        if x.kind != "fn" or not x.in_verus or x.owner != fn.owner or not x.body or \
                x.mode not in ("proof", "exec") or not lo <= src.line_of(x.head) <= hi:
            continue
        first, last = src.line_of(x.start), src.line_of(x.end - 1)
        if any(first <= h <= last for h in holes):
            out.append((V.vs.item_symbol(x), x.name))
    if not fn.owner.startswith("<") and len(out) < 2:
        # an inherent-impl item gates per method only when its block holds
        # several hole methods (Q14.H5v); with one, its first fn's gate stands
        return []
    return out


def dafny_hole_methods(text, rel, it):
    """[(symbol, name)] of a Dafny item whose block holds two or more hole
    methods (DV5c, Q17.H1d: a class implementing a trait, whose constructor
    and methods are one item): every method, constructor or lemma of the
    block that has a body holding a hole form, by its qualified symbol
    (`Mod.Class.Method`, `Mod.Class._ctor` for a constructor), which
    dvl.dafny.empty_body resolves. A function or predicate is never one of
    them (a placeholder body is an open body, judged by the methods' gates).
    [] for any other item: its gate stays its first declaration's, so no
    earlier item's gate changes."""
    if core.lang_of(rel) != "d":
        return []
    try:
        src = D.parse_source(text, rel)
    except Exception:  # noqa: BLE001 — an unparsable file keeps the gate's own refusal
        return []
    lo, hi = it["line_start"], it["line_end"]
    holes = set(static_holes(text, rel, it))
    out = [(d.qual, d.name) for d in src.decls
           if d.kind in ("method", "constructor", "lemma") and d.body is not None
           and lo <= d.line <= hi and any(d.line <= h <= d.end_line for h in holes)]
    return out if len(out) >= 2 else []


def dafny_methods_gate(ctx, it, rel, path, methods):
    """(ok, lines) of a Dafny item with several hole methods (dafny_hole_methods):
    the empty body of each, by its symbol (maxauto and the shipped options under
    each pinned seed); the item passes when each fails."""
    ok, out = True, [f"    {it['id']}: one gate per hole method "
                     f"({', '.join(n for _, n in methods)}; DV5c)"]
    for sym, name in methods:
        res = D.empty_body(path, sym)
        outs = [k for k, v in res.per_symbol.items() if v == "inconclusive"]
        if outs:
            out.append(f"    {it['id']}: {name}: {', '.join(outs)} ran out of resources at the "
                       "pinned limit: counted as failing (QPLAN §30 Q66)")
        g_ok, g_lines = gate_line(it, rel, res, f"the empty body of {name}")
        ok = ok and g_ok
        out += g_lines
        out += [f"    {core.show(f.file, ctx.root)}:{f.line}: {f.kind}" for f in res.findings
                if f.kind != "refused"]
    return ok, out


# Verus hole forms the empty-body gate has no body to empty in (DV3b
# integration): a statement hole, whose hole is the labelled assume of a given
# client and whose block opens with a bodyless trait method (QPLAN §14.0,
# §6 Q40: skipped by --empty-body; vcheck, the strict report and --exit count
# its assume), and a spec-definition hole, an `uninterp spec fn` that the
# learner defines (QPLAN §14.0; its definition is judged through its uses and
# the freeze pin's open_bodies). Both are reported as skipped, never silently.
# Reviewed (DV3b kits, tools lane): the trait method that opens a statement
# hole's block may be of any mode (the gate cannot empty a bodyless method of
# any mode), and a block is skipped only when every hole form it holds is of
# the skipped kind; a block that also holds another hole form is not skipped,
# so the gate's refusal of its first fn stays loud.
UNINTERP_HOLE = re.compile(r"\buninterp\s+spec\s+fn\b")


def _first_fn(text, it):
    src = V.vs.parse(text)
    lo, hi = it["line_start"], it["line_end"]
    return src, next((x for x in src.walk() if x.kind == "fn" and x.in_verus
                      and lo <= src.line_of(x.head) <= hi), None)


STATEMENT_SKIP = "a statement hole"
# A prose item (QPLAN §19.0): its block names the declaration the learner writes
# from prose, `// prose: <name>`; its hole is a given client's labelled assume, and
# its use-site check ships commented.
PROSE_LINE = re.compile(r"^\s*//\s*prose:\s*([A-Za-z_][A-Za-z0-9_]*)\s*$")


def prose_name(text, it):
    """The declaration a prose item's block names (`// prose: <name>`), or None."""
    raw = text.split("\n")[it["line_start"] - 1:it["line_end"]]
    return next((m.group(1) for m in map(PROSE_LINE.match, raw) if m), None)


def prose_use_sites(text, rel, it, name):
    """The block's commented use-site check lines (under `Uncomment as you go:`)
    that call the prose declaration `name`; a prose item's client gate needs at
    least one."""
    lines = text.split("\n")
    call = re.compile(r"\b" + re.escape(name) + r"\s*\(")
    return [ln for ln in sr_commented_checks(lines, rel, it["line_start"], it["line_end"])
            if call.search(lines[ln - 1])]


def uncomment_checks(lines, rel, it):
    """`lines` with the block's commented checks uncommented (in place)."""
    leader = sr_leader(rel)
    for ln in sr_commented_checks(lines, rel, it["line_start"], it["line_end"]):
        line = lines[ln - 1]
        k = line.index(leader)
        lines[ln - 1] = line[:k] + line[k + len(leader):].lstrip(" ")
    return lines


FUNCTION_SKIP = "a function hole"


def _dafny_skip_reason(text, rel, it, open_specs):
    """eb_skip_reason for a Dafny hole item (DV5a integration, QPLAN §30 Q66's
    lane reports): a statement hole whose block opens with an open statement
    (its body given, listed under `open_specs` in the freeze pin) and whose
    holes are the labelled assumes of the given client after it (Q10.H2d); or
    a bodyless function or predicate, which has no empty body (Q11.H5d)."""
    try:
        src = D.parse_source(text, rel)
    except Exception:  # noqa: BLE001 — an unparsable file keeps the gate's own refusal
        return None
    lo, hi = it["line_start"], it["line_end"]
    decls = [d for d in src.decls if d.kind in D.METHODLIKE - {"iterator"} and lo <= d.line <= hi]
    if not decls:
        return None
    first, holes = decls[0], static_holes(text, rel, it)
    if not holes:
        return None
    if first.kind in ("function", "predicate") and first.body is None and \
            set(holes) == {first.line}:
        return (f"{FUNCTION_SKIP}: a bodyless function has no empty body; its gate is its "
                "twin's construct-free answers (`cfree:` lines, the forms gate)")
    assumes = {t.line for t in src.toks if t.kind == "id" and t.text == "assume"
               and lo <= t.line <= hi}
    later = decls[1:]
    if first.body is not None and first.qual in (open_specs or ()) and later and \
            set(holes) <= assumes and all(any(d.line <= h <= d.end_line for d in later)
                                          for h in holes):
        return (f"{STATEMENT_SKIP}: its hole is the labelled assume of a given client "
                "(QPLAN §14.0, §6 Q40); its gate is the client's (client_gate)")
    return None


def eb_skip_reason(text, rel, it, open_specs=None):
    """Why the empty-body gate skips a hole item's shipped gate, or None. A
    statement hole (STATEMENT_SKIP) gets the client gate instead; a function
    hole (FUNCTION_SKIP) must carry a `cfree:` line for the forms gate.
    `open_specs` (the file's open statements in expected/<ID>.freeze) admits a
    statement hole whose declaration has a body."""
    name = prose_name(text, it)
    if name is not None:
        return (f"{STATEMENT_SKIP}: a prose item: the statement (`{name}`) is the learner's; "
                "its gate is the given client's, with its commented use-site check "
                "uncommented (client_gate)")
    if core.lang_of(rel) == "d":
        return _dafny_skip_reason(text, rel, it, open_specs)
    if core.lang_of(rel) != "v":
        return None
    try:
        src, fn = _first_fn(text, it)
    except V.vs.ParseError:
        return None
    if fn is None:
        return None
    lo = it["line_start"]
    raw = text.split("\n")[lo - 1:it["line_end"]]
    holes = static_holes(text, rel, it)
    label = re.compile(r'proof_note\(\s*"' + re.escape(it["id"]) + r'"\s*\)\s*\]\s*assume\s*\(')
    labelled = {lo + k for k, ln in enumerate(raw) if label.search(ln)}
    if not fn.body and fn.owner is not None and labelled and set(holes) <= labelled:
        return (f"{STATEMENT_SKIP}: its hole is the labelled assume of a given client "
                "(QPLAN §14.0, §6 Q40); its gate is the client's (client_gate)")
    if fn.body and V.vs.item_symbol(fn) in (open_specs or ()) and labelled and \
            set(holes) <= labelled and all(h > src.line_of(fn.body[1]) for h in labelled):
        return (f"{STATEMENT_SKIP}: its hole is the labelled assume of a given client after "
                "its open statement (QPLAN §14.0, §6 Q40); its gate is the client's "
                "(client_gate)")
    if fn.mode == "spec" and "uninterp" in fn.quals and holes and all(
            UNINTERP_HOLE.search(raw[h - lo]) for h in holes):
        return ("a spec-definition hole: an `uninterp spec fn` has no body to empty; its "
                "definition is judged through its uses and the freeze pin (QPLAN §14.0)")
    return None


def client_gate(ctx, it, rel):
    """(ok, lines) of a statement hole's gate (STATEMENT_SKIP): the learner's
    unit or crate, with the item's hole lines (the labelled assumes of its
    given client) blanked and the shipped statement kept, must fail inside the
    item's block: the client needs the statement the learner writes. Done by
    hand for Q08.T1v/H3v and Q10.H2d/H2v before (Q10-code-notes; DV5a
    integration). A prose item (`// prose: <name>`, QPLAN §19.0) ships no
    statement: its commented use-site check, which must call `<name>`, is
    uncommented too, and the variant must fail at that call (it does not
    resolve) or inside the block; prose_proof_gate checks the proof."""
    lang = core.lang_of(rel)
    text = ctx.text(rel)
    holes = static_holes(text, rel, it)
    prose = prose_name(text, it)
    uses = prose_use_sites(text, rel, it, prose) if prose is not None else []
    if prose is not None and not uses:
        return False, [f"  ? {it['id']}  no client gate: a prose item's block needs a commented "
                       f"use-site check (under `Uncomment as you go:`) that calls `{prose}` "
                       f"({rel})"]
    if lang == "v":
        copy = crate_dir_rel(ctx.root, rel)
    else:
        unit = (ctx.root / rel).parent
        copy = unit.relative_to(ctx.root).as_posix() if (unit / "dfyconfig.toml").is_file() \
            else rel
    if copy is None or not holes:
        return False, [f"  ? {it['id']}  no client gate: no unit or crate holds {rel}"]
    lines = text.split("\n")
    for h in holes:
        lines[h - 1] = ""
    if prose is not None:
        # a prose item: its use-site check is part of the client, commented as
        # shipped; uncommented, it calls the statement the learner has not written
        uncomment_checks(lines, rel, it)
    shadow = core.shadow_tree(ctx.root, [copy], "client")
    try:
        path = shadow / rel
        path.write_text("\n".join(lines), encoding="utf-8")
        res = core.lib(lang).verify(str(path))
        ap = str(path.resolve())
        lo, hi = it["line_start"], it["line_end"]
        errs = sorted({d.line for d in res.diagnostics if d.severity == "error"
                       and d.file == ap and lo <= d.line <= hi})
        if res.verdict in ("refused", "killed(memory)") or (
                res.verdict == "error" and res.stage not in ("parse", "resolve")):
            return False, [f"  ? {it['id']}  no client-gate verdict ({res.verdict}); raw output: "
                           f"{res.raw_dir}"]
        if prose is not None and res.stage == "resolve" and res.verdict != "verified" and \
                set(errs) & set(uses):
            return True, [f"  ✓ {it['id']}  the given client's use-site check does not resolve "
                          f"without `{prose}` (line {', '.join(map(str, errs))}): the statement "
                          f"is required ({rel})"]
        if res.stage in ("parse", "resolve") and res.verdict != "verified":
            return False, [f"  ? {it['id']}  the client gate's variant does not "
                           f"{res.stage} ({rel})"]
        if errs:
            return True, [f"  ✓ {it['id']}  the given client fails without its labelled assume "
                          f"(line {', '.join(map(str, errs))}): the statement is required ({rel})"]
        return False, [f"  ✗ {it['id']}  STATEMENT NOT REQUIRED: the given client verifies "
                       f"without its labelled assume against the shipped statement ({rel})"]
    finally:
        core.remove_tree(shadow)


def prose_decl_line(text, rel, it, name):
    """The line of the declaration `name` inside the item's block (a prose
    item's twin states it there), or None."""
    lang = core.lang_of(rel)
    kw = r"(?:lemma|method|function|predicate)" if lang == "d" else r"fn"
    pat = re.compile(r"\b" + kw + r"\s+" + re.escape(name) + r"\b")
    lines = text.split("\n")
    return next((ln for ln in range(it["line_start"], min(it["line_end"], len(lines)) + 1)
                 if pat.search(lines[ln - 1]) and not lines[ln - 1].lstrip().startswith("//")),
                None)


# Proof text in a Verus exec fn's body: what the light modes of the empty-body
# gate strip. An exec prose item whose twin body holds none has code that needs
# no proof (Q15.H5v's `max_big`), so stripping it changes nothing.
PROOF_TOKENS = {"proof", "assert", "assume", "invariant", "invariant_except_break",
                "decreases", "reveal", "reveal_with_fuel", "broadcast", "ghost", "tracked",
                "Ghost", "Tracked"}


def exec_prose_fn(text, it, name):
    """(fn item, needs proof) of a Verus exec fn `name` inside the item's block
    of a twin, or (None, None) when it is no exec fn there."""
    try:
        src = V.vs.parse(text)
    except V.vs.ParseError:
        return None, None
    fn = next((x for x in src.walk() if x.kind == "fn" and x.in_verus and x.name == name
               and it["line_start"] <= src.line_of(x.head) <= it["line_end"]), None)
    if fn is None or fn.mode != "exec" or not fn.body:
        return None, None
    a, b = fn.body
    needs = any(t.kind == "id" and (t.text in PROOF_TOKENS or t.text.startswith("lemma_"))
                for t in src.toks[a + 1:b])
    return fn, needs


def prose_proof_gate(ctx, it, rel, name, shipped_modes, seeds):
    """(ok, lines) of a prose item's proof gate: in its reference twin, the
    author's statement of `name` (inside the item's block) with an empty body
    must fail, Verus in every light mode and seed, Dafny under maximal
    automation and the shipped options at every seed: the statement the
    learner writes does not prove itself. The client gate checks that the
    statement is needed; this one, that its proof is.

    An exec prose item (Verus; DV5c, Δ197's open item): when the twin's block
    declares a trivial body (`// triv: { … }`), the TRIV variant runs with it
    too, so a statement that trivial code meets fails the gate; and when the
    twin's code holds no proof text at all (exec_prose_fn: the code needs no
    proof, Q15.H5v), the light modes, which strip only proof, would verify
    whatever the statement says, so TRIV alone is the gate (it must fail in
    every seed) and the light modes are not run."""
    twin = ctx.root / core.REF_DIR / rel
    if not twin.is_file():
        return False, [f"  ? {it['id']}  no prose proof gate: no reference twin "
                       f"{core.REF_DIR}/{rel}"]
    ttext = twin.read_text(encoding="utf-8")
    items, _errs = ci.parse_items(rel, ttext)
    titem = next((x for x in items if x["id"] == it["id"]), None)
    if titem is None or prose_decl_line(ttext, rel, titem, name) is None:
        return False, [f"  ? {it['id']}  no prose proof gate: the twin's block of {it['id']} "
                       f"declares no `{name}` ({core.REF_DIR}/{rel})"]
    if core.lang_of(rel) == "v":
        fn, needs = exec_prose_fn(ttext, titem, name)
        tb, problem = declared_triv_body(ctx, it, rel) if fn is not None else (None, None)
        if problem:
            return False, [f"  ? {it['id']}  no prose proof gate: {problem}"]
        if fn is not None and tb is not None and not needs:
            res = V.empty_body(str(twin), name, modes=["TRIV"], seeds=seeds, triv_body=tb)
            g_ok, g_lines = gate_line(it, rel, res, f"the twin's statement of `{name}` with the "
                                      "declared trivial body (TRIV)")
            return g_ok, g_lines + [
                f"    {it['id']}: an exec prose item whose code needs no proof (its twin's "
                f"`{name}` holds no proof text): TRIV, the twin's `triv:` body, is its proof "
                "gate; the light modes, which strip proof only, are not run"] + [
                f"    {core.show(f.file, ctx.root)}:{f.line}: {f.kind}"
                for f in res.findings if f.kind != "refused"]
        res = V.empty_body(str(twin), name, modes=shipped_modes, seeds=seeds, triv_body=tb)
        if fn is not None and tb is None and not needs:
            g_ok, g_lines = gate_line(it, rel, res, f"the twin's `{name}` with an empty body")
            return g_ok, g_lines + [
                f"    {it['id']}: an exec prose item whose code needs no proof: declare its "
                f"trivial body in the twin's block (`// triv: {{ … }}`), which the gate then "
                "runs as TRIV in place of the light modes"]
    else:
        res = D.empty_body(str(twin), name)
    g_ok, g_lines = gate_line(it, rel, res, f"the twin's `{name}` with an empty body")
    return g_ok, g_lines + [f"    {core.show(f.file, ctx.root)}:{f.line}: {f.kind}"
                            for f in res.findings if f.kind != "refused"]


def admitted_false(ctx, iid):
    """True when the registry records the item as not admitted
    ([module.admissible] `admitted = false`): its gate findings are why it
    carries 0 minutes (spec §2.8, QPLAN §19.0), so they are reported but do
    not fail the run."""
    entry = (ctx.rec.get("admissible") or {}).get(iid)
    return isinstance(entry, dict) and entry.get("admitted") is False


def open_spec_symbols_of(ctx, rel):
    """The open statements of a learner file (its `open_specs` in
    expected/<ID>.freeze, QPLAN §6 Q44), [] without a pin."""
    import tomllib
    pin = ctx.root / "expected" / f"{ctx.mid}.freeze"
    try:
        data = tomllib.loads(pin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return next((list(f.get("open_specs") or []) for f in data.get("file", [])
                 if f.get("path") == rel), [])


def open_spec_statement(ltext, ttext, it, open_specs):
    """For a Verus hole item whose declaration (the first fn of its block) is
    an open statement (QPLAN §6 Q44: it ships with no or few clauses, and the
    learner adds them), the learner file with that declaration's clauses taken
    from its twin: the statement the hole is posed against, so the empty-body
    gate does not run an unconstrained body (DV3b integration; Q07.H7v). None
    when the declaration is not open or the twin lacks it."""
    try:
        lsrc, lfn = _first_fn(ltext, it)
        tsrc = V.vs.parse(ttext)
    except V.vs.ParseError:
        return None
    if lfn is None or not lfn.body or V.vs.item_symbol(lfn) not in open_specs:
        return None
    sym = V.vs.item_symbol(lfn)
    tfn = next((x for x in tsrc.walk() if x.kind == "fn" and x.in_verus
                and V.vs.item_symbol(x) == sym and x.body), None)
    if tfn is None:
        return None

    def clause_span(src, fn):
        tk = src.toks
        sig = tk[fn.ret[1] - 1].end if fn.ret else tk[fn.params[1]].end
        return sig, tk[fn.body[0]].start
    la, lb = clause_span(lsrc, lfn)
    ta, tb = clause_span(tsrc, tfn)
    return ltext[:la] + ttext[ta:tb] + ltext[lb:]


def given_body_annotation(ltext, ttext, it):
    """An exec annotation item with its entire implementation already given.

    Every reference region must be in this function's contract, and its raw
    body must equal the shipped body's E0 projection (tokens, ignoring comments).
    Extra reference proof or implementation work therefore keeps the ordinary
    body gates. For a pure annotation, TRIV tests the completed contract's
    usefulness and RGN tests the missing annotation's necessity; stripping
    proof from the already-given implementation is not a learner-work test.
    Call only after open_spec_statement has recognized the frozen open spec.
    """
    try:
        lsrc, lfn = _first_fn(ltext, it)
        tsrc = V.vs.parse(ttext)
        regions = core.common.hole_regions(ttext, it["id"])
        if lfn is None or not lfn.body or lfn.mode in ("proof", "spec") or not regions:
            return False
        tfn = next((x for x in tsrc.walk() if x.kind == "fn" and x.in_verus
                    and V.vs.item_symbol(x) == V.vs.item_symbol(lfn) and x.body), None)
        if tfn is None or tfn.mode != lfn.mode:
            return False
        if not all(tsrc.line_of(tfn.params[1]) < b < e < tsrc.line_of(tfn.body[0])
                   for _, b, e in regions):
            return False
        projected = V.eb_variant(ltext, lsrc, lfn, "E0")
        psrc, pfn = _first_fn(projected, it)
        return ([t.text for t in psrc.toks[pfn.body[0]:pfn.body[1] + 1]] ==
                [t.text for t in tsrc.toks[tfn.body[0]:tfn.body[1] + 1]])
    except (V.vs.ParseError, ValueError):
        return False


def statement_gate(ctx, it, rel, stext, shipped_modes, seeds, triv_body):
    """The shipped gate of an open-statement hole, run on a shadow of its
    learner crate whose file carries the twin's clauses (open_spec_statement).
    Locations map back to the learner file."""
    crate = crate_dir_rel(ctx.root, rel)
    shadow = core.shadow_tree(ctx.root, [crate], "stmt")
    try:
        (shadow / rel).write_text(stext, encoding="utf-8")
        res = V.empty_body(str(shadow / rel), it["id"], modes=shipped_modes, seeds=seeds,
                           triv_body=triv_body)
        return core.remap(res, shadow, ctx.root)
    finally:
        core.remove_tree(shadow)


EB_CFREE_MODES = ("NL", "BV")


def eb_form_killed(text, rel, it, res, rules, given):
    """[(mode, why)] when every variant that verified is a whole-goal NL or BV
    variant (eb_variant: one `assert(<ensures>) by (nonlinear_arith |
    bit_vector)`, a construct-free answer) and each fails a static form of the
    item (QPLAN §6 Q43: a construct-free answer is killed by verification or
    by a form, as the twin's `cfree:` answers are); else None. Only static
    forms are judged here (DV3b integration; Q09.H1v, X1v)."""
    closed = {k.split()[0] for k, v in res.per_symbol.items()
              if v in ("verified", "verifies", "fn-not-checked")}
    if not rules or not closed or not closed <= set(EB_CFREE_MODES):
        return None
    try:
        src, fn = _first_fn(text, it)
    except V.vs.ParseError:
        return None
    if fn is None:
        return None
    out = []
    for mode in sorted(closed):
        variant = V.eb_variant(text, src, fn, mode, (), None, it["id"])
        if variant is None:
            return None
        vitems, _ = ci.parse_items(rel, variant)
        vblk = next((x for x in vitems if x["id"] == it["id"]), None)
        if vblk is None:
            return None
        fails = form_failures(static_forms(variant, rel, vblk, rules, given))
        if not fails:
            return None
        out.append((mode, form_text(fails)))
    return out


def twin_regions(ctx, it, rel):
    """(regions, problem): the item's `@hole-begin`/`@hole-end` regions in its
    reference twin (Solutions/<rel>), [] when the twin is missing or marks
    none; a problem when the twin's markers are broken (QPLAN §6 Q18)."""
    twin = ctx.root / core.REF_DIR / rel
    if not twin.is_file():
        return [], None
    try:
        return core.common.hole_regions(twin.read_text(encoding="utf-8"), it["id"]), None
    except ValueError as e:
        return [], f"{core.REF_DIR}/{rel}: {e}"


def region_gate(ctx, it, rel, lang, seeds):
    """The region mode of the empty-body gate for one annotation hole (QPLAN
    §6 Q18): the item's reference twin, laid over its learner unit or crate,
    with the item's learner regions blanked, must fail (dvl.dafny.empty_body
    regions=True; dvl.verus.empty_body mode RGN). Locations map back into the
    reference tree."""
    t = core.Target(lang, ctx.root / core.REF_DIR / rel, ctx.root)
    got = core.twin_context(t, ctx.root)
    if got is None:
        return core.lib(lang)._refused(str(t.path), f"{core.REF_DIR}/{rel}: the twin mirrors no "
                                                    "learner unit or crate")
    shadow, tt = got
    try:
        if lang == "v":
            res = V.empty_body(str(tt.path), it["id"], modes=["RGN"], seeds=seeds)
        else:
            res = D.empty_body(str(tt.path), it["id"], regions=True)
        return core.twin_remap(res, shadow, ctx.root)
    finally:
        core.remove_tree(shadow)


# The forms gate of --empty-body (QPLAN §6 Q43), per hole item with forms or
# `// cfree:` lines: the twin's form lines equal the learner's; the twin meets
# every form (`stable`: the twin's sweep, laid over its learner unit or crate);
# each `cfree:` answer of the twin (dvl.forms.cfree_bodies), put in place of
# the item's body in the twin, fails verification at the pin (the learner loop)
# or one of the forms. A construct-free answer that verifies and meets every
# form fails the gate: the construct is not required.

class TwinShadows:
    """Twins laid over their learner units or crates (vcheck twin_context), one
    shadow per unit, crate or loose file, kept for the whole gate run, and the
    `stable` sweeps of the unmodified twins. close() removes every shadow."""

    def __init__(self, ctx):
        self.ctx, self.got, self.rows = ctx, {}, {}

    def get(self, lang, rel):
        """(shadow, path of the twin at its learner path), or None when the
        twin mirrors no learner unit or crate."""
        root = self.ctx.root
        if lang == "d":
            unit = (root / rel).parent
            key = ("d", unit.relative_to(root).as_posix()
                   if (unit / "dfyconfig.toml").is_file() else rel)
        else:
            key = ("v", crate_dir_rel(root, rel) or rel)
        if key not in self.got:
            t = core.Target(lang, root / core.REF_DIR / rel, root)
            self.got[key] = core.twin_context(t, root)
        got = self.got[key]
        return None if got is None else (got[0], got[0] / rel)

    def stable_rows(self, lang, rel, seeds=None):
        shadow, _ = self.get(lang, rel)
        target = stable_target(shadow, rel, lang)
        key = (lang, str(target), tuple(seeds or ()))
        if key not in self.rows:
            self.rows[key] = run_stable(target, lang, shadow, seeds)
        return self.rows[key]

    def close(self):
        for got in self.got.values():
            if got is not None:
                core.remove_tree(got[0])
        self.got, self.rows = {}, {}


def body_variant(text, rel, lang, blk, body, target=None, decls=""):
    """`text` (a twin) with the body of the item's declaration (the first
    lemma, method, function or predicate of its block; Verus: the first fn)
    replaced by `body`; None when the block declares none. A Dafny
    `function … by method` loses its method body, as in the empty-body gate.
    target (Dafny): the declaration of that name anywhere in the file instead
    (a `// cfree[<target>]:` answer of a `formula:<target>` form). decls: the
    answer's `// cfree-decl:` text, put on lines of its own where the learner
    writes helpers: directly below the last `// HELPERS` comment line above
    the block (a Verus file's helper area sits above every item block, so the
    forms follow the declaration as a helper), else directly above the block."""
    out = _body_variant(text, rel, lang, blk, body, target)
    if out is None or not decls:
        return out
    lines = out.split("\n")
    at = blk["line_start"] - 1
    helpers = [i for i in range(at) if HELPERS_LINE.match(lines[i])]
    if helpers:
        at = helpers[-1] + 1
    return "\n".join(lines[:at] + [""] + decls.split("\n") + [""] + lines[at:])


HELPERS_LINE = re.compile(r"^\s*//\s*HELPERS\b")


def _body_variant(text, rel, lang, blk, body, target=None):
    lo, hi = blk["line_start"], blk["line_end"]
    if lang == "d":
        src = D.parse_source(text, rel)
        if target is not None:
            d = next((x for x in src.decls if x.kind in D.METHODLIKE - {"iterator"}
                      and x.name == target), None)
        else:
            d = next((x for x in src.decls if x.kind in D.METHODLIKE - {"iterator"}
                      and lo <= x.line <= hi), None)
        if d is None:
            return None
        tk = src.toks
        if d.by_method:
            a, b = tk[d.by_method[0]].start, tk[d.by_method[1]].end
        elif d.body:
            a, b = tk[d.body[0]].start, tk[d.body[1]].end
        else:
            a = b = tk[d.header_end - 1].end
            body = " " + body
        return text[:a] + body + text[b:]
    src = V.vs.parse(text)
    it = next((x for x in src.walk() if x.kind == "fn" and x.in_verus
               and lo <= src.line_of(x.head) <= hi), None)
    if it is None:
        return None
    tk = src.toks
    if it.body:
        a, b = tk[it.body[0]].start, tk[it.body[1]].end
    else:
        a, b = tk[it.end - 1].start, tk[it.end - 1].end
    return text[:a] + body + text[b:]


def item_symbol_in(text, path, rel, lang, blk):
    """The per_symbol key of the item's declaration (see body_variant)."""
    syms = file_symbols(path, text, rel, lang)
    lo, hi = blk["line_start"], blk["line_end"]
    return next((s for s, ln in syms if lo <= ln <= hi), None)


def cfree_verdict(shadows, rel, lang, it, rules, body, seeds, given=None, target=None,
                  decls=""):
    """(status, why) of one construct-free answer: killed (it fails
    verification or a form: the gate holds), passes (it verifies and meets
    every form: the gate fails) or None (no verdict). target: the declaration
    a targeted answer replaces; decls: the declarations it adds (see
    body_variant)."""
    got = shadows.get(lang, rel)
    shadow, path = got
    twin_text = path.read_text(encoding="utf-8")
    items, _ = ci.parse_items(rel, twin_text)
    blk = next(x for x in items if x["id"] == it["id"])
    variant = body_variant(twin_text, rel, lang, blk, body, target, decls)
    if variant is None:
        return None, ("its twin declares no `%s`" % target if target else
                      "its twin block declares nothing to put the body in")
    try:
        path.write_text(variant, encoding="utf-8")
        vitems, _ = ci.parse_items(rel, variant)
        vblk = next((x for x in vitems if x["id"] == it["id"]), blk)
        res = core.lib(lang).verify(str(path))
        if res.verdict in ("refused", "killed(memory)") or (
                res.verdict == "error" and res.stage not in ("parse", "resolve")):
            return None, f"no verdict ({res.verdict}); raw output: {res.raw_dir}"
        ap = str(path.resolve())
        lo, hi = vblk["line_start"], vblk["line_end"]
        errs = [d.line for d in res.diagnostics if d.severity == "error" and d.file == ap
                and lo <= d.line <= hi]
        try:
            sym = item_symbol_in(variant, path, rel, lang, vblk)
        except ValueError:
            sym = None
        st = res.per_symbol.get(sym) if sym else None
        if errs or res.stage in ("parse", "resolve") and res.verdict != "verified" or \
                (st is not None and st not in STABLE_OK[lang]) or \
                (st is None and res.verdict != "verified"):
            return "killed", "fails verification"
        fails = form_failures(static_forms(variant, rel, it, rules, given))
        if not fails and "stable" in rules:
            judged = stable_judge(run_stable(stable_target(shadow, rel, lang), lang, shadow,
                                             seeds), path, variant, rel, it)
            if judged is None:
                return None, "no verdict from the `stable` sweep"
            fails = form_failures({}, judged)
        if fails:
            return "killed", "fails its forms: " + form_text(fails)
        return "passes", "verifies and meets every form"
    finally:
        path.write_text(twin_text, encoding="utf-8")


def forms_gate(ctx, shadows, it, rel, lang, seeds):
    """(ok, lines) of the forms gate for one hole item (see above), or
    (True, []) when neither the learner block nor its twin block carries a
    form or a `cfree:` line."""
    raw = ctx.lines(rel)
    rules = F.block_rules(raw, it["line_start"], it["line_end"])
    twin = ctx.root / core.REF_DIR / rel
    if not twin.is_file():
        return (True, []) if not rules else \
            (False, [f"  ? {it['id']}  no forms gate: no reference twin ({rel})"])
    ttext = twin.read_text(encoding="utf-8")
    tlines = ttext.split("\n")
    titems, _ = ci.parse_items(f"{core.REF_DIR}/{rel}", ttext)
    tblk = next((x for x in titems if x["id"] == it["id"]), None)
    if tblk is None:
        return (True, []) if not rules else \
            (False, [f"  ? {it['id']}  no forms gate: its twin holds no block {it['id']}"])
    trules = F.block_rules(tlines, tblk["line_start"], tblk["line_end"])
    answers, cprobs = F.cfree_answers(tlines, tblk["line_start"], tblk["line_end"])
    bodies = [b for b, _ in answers]
    if not rules and not trules and not bodies and not cprobs:
        return True, []
    ok, out = True, []
    if set(rules) != set(trules):
        ok = False
        out.append(f"  ✗ {it['id']}  the twin's form lines ({', '.join(trules) or 'none'}) "
                   f"differ from the learner's ({', '.join(rules) or 'none'}) ({rel})")
    for p in cprobs:
        ok = False
        out.append(f"  ? {it['id']}  {core.REF_DIR}/{rel}: {p}")
    got = shadows.get(lang, rel)
    if got is None:
        return False, out + [f"  ? {it['id']}  no forms gate: the twin mirrors no learner unit "
                             f"or crate ({rel})"]
    shadow, path = got
    given = given_names(ctx.text(rel), rel, it)
    if rules:
        fails = form_failures(static_forms(ttext, rel, tblk, rules, given))
        if not fails and "stable" in rules:
            judged = stable_judge(shadows.stable_rows(lang, rel, seeds), path, ttext, rel, tblk)
            if judged is None:
                ok = False
                out.append(f"  ? {it['id']}  no verdict from the twin's `stable` sweep ({rel})")
            else:
                fails = form_failures({}, judged)
        if fails:
            ok = False
            out.append(f"  ✗ {it['id']}  the twin fails its forms: {form_text(fails)} ({rel})")
        elif ok:
            out.append(f"  ✓ {it['id']}  the twin meets its forms ({', '.join(rules)}) ({rel})")
    for k, (body, decls) in enumerate(answers, 1):
        st, why = cfree_verdict(shadows, rel, lang, it, rules, body, seeds, given, None, decls)
        if st == "killed":
            out.append(f"  ✓ {it['id']}  construct-free answer {k} {why} ({rel})")
        elif st == "passes":
            ok = False
            out.append(f"  ✗ {it['id']}  CONSTRUCT NOT REQUIRED: construct-free answer {k} "
                       f"{why} ({rel})")
        else:
            ok = False
            out.append(f"  ? {it['id']}  construct-free answer {k}: {why} ({rel})")
    targeted, tprobs = F.cfree_targets(tlines)
    for p in tprobs:
        ok = False
        out.append(f"  ? {it['id']}  {core.REF_DIR}/{rel}: {p}")
    owned = {F.rule_arg(r) for r in rules if F.rule_name(r) == "formula"}
    k = len(bodies)
    for tgt, body in targeted:
        if tgt not in owned:
            continue
        k += 1
        st, why = cfree_verdict(shadows, rel, lang, it, rules, body, seeds, given, tgt)
        if st == "killed":
            out.append(f"  ✓ {it['id']}  construct-free answer {k} (in `{tgt}`) {why} ({rel})")
        elif st == "passes":
            ok = False
            out.append(f"  ✗ {it['id']}  CONSTRUCT NOT REQUIRED: construct-free answer {k} "
                       f"(in `{tgt}`) {why} ({rel})")
        else:
            ok = False
            out.append(f"  ? {it['id']}  construct-free answer {k} (in `{tgt}`): {why} ({rel})")
        bodies = bodies + [body]
    if rules and not bodies and any(F.rule_name(r) != "stable" for r in rules):
        out.append(f"    {it['id']}: its twin carries no `cfree:` answer (advisory: a form other "
                   "than stable is there because a construct-free answer verifies)")
    return ok, out


def gate_line(it, rel, res, what):
    """(ok, lines) for one gate result."""
    out = []
    runs = ", ".join(f"{k}: {v}" for k, v in res.per_symbol.items())
    if res.verdict == "failed":
        out.append(f"  ✓ {it['id']}  {what} fails in every run ({rel})")
    elif res.verdict == "verified":
        closed = [k for k, v in res.per_symbol.items() if v in ("verified", "verifies",
                                                                 "fn-not-checked")]
        out.append(f"  ✗ {it['id']}  FALLS TO AUTOMATION: {what} verifies in "
                   f"{', '.join(closed) or 'a run'} ({rel})")
    else:
        why = "; ".join(f.message for f in res.findings if f.kind == "refused") \
            if res.verdict == "refused" else ""
        out.append(f"  ? {it['id']}  no gate verdict for {what} ({res.verdict}"
                   + (f": {why}" if why else "") + f"); runs: {runs}; raw output: "
                   f"{res.raw_dir}")
    return res.verdict == "failed", out


def impl_methods_gate(ctx, it, rel, path, methods, shipped_modes, seeds):
    """(ok, lines) of a trait-impl item's gates: the empty body of each hole
    method (impl_hole_methods), with its twin's `triv: <method>:` body in the
    TRIV mode (the block's unnamed `triv:` body when the item has one method)."""
    bodies, problem = declared_triv_bodies(ctx, it, rel)
    if problem:
        return False, [f"  ? {it['id']}  no gate run: {problem}"]
    names = {name for _, name in methods}
    stray = sorted(k for k in bodies if k is not None and k not in names)
    if stray:
        return False, [f"  ? {it['id']}  no gate run: {core.REF_DIR}/{rel}: `triv:` names "
                       f"{', '.join(stray)}, no hole method of the item"]
    if None in bodies and len(methods) > 1:
        return False, [f"  ? {it['id']}  no gate run: {core.REF_DIR}/{rel}: an unnamed `triv:` "
                       "body in an impl item with several hole methods (name the method: "
                       "`triv: <method>: { … }`)"]
    ok, out = True, [f"    {it['id']}: an impl item: one gate per hole method "
                     f"({', '.join(n for _, n in methods)}; QPLAN §30 Q65)"]
    for sym, name in methods:
        tb = bodies.get(name, bodies.get(None))
        res = V.empty_body(path, sym, modes=shipped_modes, seeds=seeds, triv_body=tb)
        g_ok, g_lines = gate_line(it, rel, res, f"the empty body of {name}")
        ok = ok and g_ok
        out += g_lines
        if tb is not None:
            out.append(f"    {it['id']}: TRIV runs {name}'s declared trivial body (its twin's "
                       "`triv:` line)")
        out += [f"    {core.show(f.file, ctx.root)}:{f.line}: {f.kind}" for f in res.findings
                if f.kind != "refused"]
    return ok, out


# The statement route (the user's decisions D6 and D9, 2026-10-12; DV5d): an
# admitted statement item with no shipped hole is checked on its reference
# statements and the reference delivery, in its own language.
STATEMENT_ITEM_KIND = "statement-item"
AGAINST_LINE = re.compile(r"`scripts/specfreeze --against (\S+) (\S+)`")


def admission_kind(ctx, iid):
    """The kind of the item's declared exception in [module.admissible], or None."""
    entry = (ctx.rec.get("admissible") or {}).get(iid)
    ex = entry.get("exception") if isinstance(entry, dict) else None
    return ex.split(":", 1)[0].strip() if isinstance(ex, str) and ":" in ex else None


def contract_header(text):
    """The CONTRACT header that opens a file (`/* CONTRACT` … `*/`), or ""."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "/* CONTRACT":
        return ""
    out = []
    for line in lines[1:]:
        if line.strip() == "*/":
            return "\n".join(out)
        out.append(line)
    return ""


def statements_path(text, rel):
    """The committed-statements file a file's CONTRACT checks it against (its
    `scripts/specfreeze --against <statements> <rel>` acceptance line), or None."""
    hits = [a for a, b in AGAINST_LINE.findall(contract_header(text)) if b == rel]
    return hits[0] if len(set(hits)) == 1 else None


def statement_items(ctx, held):
    """[(item, rel)] of the admitted statement items (exception kind
    statement-item) that hold no hole: the items the statement route checks.
    `held`: ids of the module's hole items (they keep their hole's gates)."""
    out = []
    for it in ctx.items:
        if it["kind"] != "H" or it["id"] in held:
            continue
        entry = (ctx.rec.get("admissible") or {}).get(it["id"])
        if isinstance(entry, dict) and entry.get("admitted") is True and \
                admission_kind(ctx, it["id"]) == STATEMENT_ITEM_KIND:
            out.append((it, it["file"]))
    return out


def ungated_items(ctx, gated):
    """Ids of the module's admitted H items that get no gate at all: no hole (not in
    `gated`, the hole items' and statement items' ids) and no statement-item
    exception (DV5d review fix: an admission the empty-body run cannot test is a
    failure, never a silent pass)."""
    adm = ctx.rec.get("admissible") or {}
    return [it["id"] for it in ctx.items
            if it["kind"] == "H" and it["id"] not in gated
            and isinstance(adm.get(it["id"]), dict) and adm[it["id"]].get("admitted") is True]


def _load_specfreeze():
    if "specfreeze" in sys.modules:
        return sys.modules["specfreeze"]
    loader = importlib.machinery.SourceFileLoader("specfreeze", str(SCRIPTS / "specfreeze"))
    spec = importlib.util.spec_from_loader("specfreeze", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["specfreeze"] = mod
    loader.exec_module(mod)
    return mod


def new_statements(ctx, rel, stmts, lang):
    """Symbols the reference statements declare that the file as shipped does
    not: the item's statements (empty: the route has nothing to check)."""
    shipped = shipped_text(ctx.root, rel)
    shipped = ctx.text(rel) if shipped is None else shipped
    have, _, _ = core.statement_table(str(ctx.root / rel), lang, text=shipped)
    ref, _, _ = core.statement_table(str(stmts), lang)
    return sorted(set(ref) - set(have))


def delivery_gate(ctx, twin, lang):
    """The reference gate on a twin (vcheck --ref --gate): a Result."""
    t = core.Target(lang, twin, ctx.root)
    shadow, run_t, src, dst = core.run_context(t, ctx.root, True)
    try:
        res = core.verify(run_t, gate=True, lint_mode="reference")
        if shadow is not None:
            core.remap(res, src, dst)
    finally:
        core.remove_tree(shadow)
    return res


def statement_route(ctx, it, rel):
    """(ok, lines) of a statement item's route (D9): the reference
    statements exist, add statements to the shipped file, and the reference
    delivery passes the reference gate with zero holes and `specfreeze
    --against` them with 0 findings."""
    iid, lang = it["id"], core.lang_of(rel)
    if lang not in ("d", "v"):
        return False, [f"  ? {iid}  no statement route: {rel} is no Dafny or Verus file"]
    srel = statements_path(ctx.text(rel), rel)
    if srel is None:
        return False, [f"  ? {iid}  no statement route: {rel}'s CONTRACT names no single "
                       f"`scripts/specfreeze --against <statements> {rel}` line"]
    stmts = ctx.root / core.REF_DIR / srel
    twin = ctx.root / core.REF_DIR / rel
    for p, what in ((stmts, "reference statements"), (twin, "reference delivery")):
        if not p.is_file():
            return False, [f"  ? {iid}  no statement route: no {what} "
                           f"({core.REF_DIR}/{p.relative_to(ctx.root / core.REF_DIR)})"]
    added = new_statements(ctx, rel, stmts, lang)
    if not added:
        return False, [f"  ✗ {iid}  the reference statements ({core.REF_DIR}/{srel}) add no "
                       f"statement to {rel} as shipped: nothing to check"]
    res = delivery_gate(ctx, twin, lang)
    lines, ok = [], True
    if res.verdict != "verified" or res.holes:
        ok = False
        lines.append(f"  ✗ {iid}  the reference delivery ({core.REF_DIR}/{rel}) does not pass "
                     f"the reference gate ({res.verdict}, {len(res.holes)} hole(s)); raw "
                     f"output: {res.raw_dir}")
    sf = _load_specfreeze()
    found = list(sf.against_findings(stmts, twin))
    try:
        found += LEV.off_lever_findings(stmts, twin)
    except LEV.LeverError as e:
        found.append(core.common.Finding(str(twin), 0, "lever-error", str(e)))
    if found:
        ok = False
        lines.append(f"  ✗ {iid}  specfreeze --against {core.REF_DIR}/{srel}: "
                     f"{len(found)} finding(s) on the reference delivery")
        lines += [f"    {core.show(f.file, ctx.root)}:{f.line}: {f.kind}" for f in found]
    if ok:
        lines.append(f"  ✓ {iid}  the statement route: the reference delivery passes the "
                     f"reference gate ({res.verified_count} verified, 0 holes) and specfreeze "
                     f"--against its reference statements ({len(added)} statement(s) the "
                     f"shipped file lacks) reports 0 findings ({rel})")
    return ok, lines


def mode_empty_body(ctx, modes, seeds):
    """Every hole item's gate: the empty body of its shipped form (both
    languages), and, for an annotation hole whose twin marks the learner's
    lines with `@hole-begin`/`@hole-end <id>`, the region gate on the twin
    (QPLAN §6 Q18). An item passes when every gate it gets passes. For
    Verus, --eb-modes may name RGN: then the region gate runs only when RGN
    is named, and the shipped gate only with the other named modes."""
    todo = hole_items(ctx)
    if not todo:
        die(f"{ctx.mid}: no hole item found (an empty list fails)")
    shipped_modes = [m for m in modes if m not in ("RGN", "FORMS", "STMT")] if modes else None
    run_forms = modes is None or "FORMS" in modes
    shadows = TwinShadows(ctx)
    try:
        bad = _empty_body_items(ctx, todo, modes, shipped_modes, run_forms, shadows, seeds)
    finally:
        shadows.close()
    print(f"{ctx.mid} empty-body: {len(todo) - bad}/{len(todo)} hole(s) pass the gate")
    stmt = statement_items(ctx, {it["id"] for it, _ in todo})
    sbad = 0
    if stmt and (modes is None or "STMT" in modes):
        for it, rel in stmt:
            ok, lines = statement_route(ctx, it, rel)
            sbad += not ok
            for line in lines:
                print(line)
        print(f"{ctx.mid} statement items: {len(stmt) - sbad}/{len(stmt)} pass the statement "
              "route")
    elif stmt:
        print(f"{ctx.mid} statement items: {len(stmt)} not run (--eb-modes names no STMT)")
    ungated = ungated_items(ctx, {it["id"] for it, _ in todo} | {it["id"] for it, _ in stmt})
    for iid in ungated:
        print(f"  ? {iid}  admitted with no hole and no statement-item exception: no gate")
    return core.EXIT_OK if not bad and not sbad and not ungated else core.EXIT_FAIL


def _empty_body_items(ctx, todo, modes, shipped_modes, run_forms, shadows, seeds):
    bad = 0
    for it, rel in todo:
        if rel.endswith(".py"):
            # the Python TRIV mode (QPLAN §11.8): the twin's `# triv:` body, on top
            # of the reference, must make the acceptance tests fail
            twin = ctx.root / core.REF_DIR / rel
            res = PY.empty_body(twin, it["id"], root=ctx.root) if twin.is_file() else \
                PY._refused(twin, f"{core.REF_DIR}/{rel}: no reference twin")
            g_ok, g_lines = gate_line(it, rel, res, "the declared trivial body (TRIV)")
            bad += not g_ok
            for line in g_lines:
                print(line)
            continue
        lang = core.lang_of(rel)
        path = str(ctx.root / rel)
        regions, rproblem = twin_regions(ctx, it, rel)
        ok, lines, ran = True, [], 0
        if rproblem:
            ok = False
            lines.append(f"  ? {it['id']}  no region gate: {rproblem}")
        run_shipped = lang == "d" or modes is None or bool(shipped_modes)
        run_region = bool(regions) and (lang == "d" or modes is None or "RGN" in modes)
        skip, stext = eb_skip_reason(ctx.text(rel), rel, it, open_spec_symbols_of(ctx, rel)), \
            None
        if skip:
            run_shipped = False
            lines.append(f"  - {it['id']}  shipped gate skipped: {skip} ({rel})")
        if skip and skip.startswith(STATEMENT_SKIP):
            ran += 1
            c_ok, c_lines = client_gate(ctx, it, rel)
            ok, lines = ok and c_ok, lines + c_lines
            prose = prose_name(ctx.text(rel), it)
            if prose is not None:
                p_ok, p_lines = prose_proof_gate(ctx, it, rel, prose, shipped_modes, seeds)
                ok, lines = ok and p_ok, lines + p_lines
        methods = impl_hole_methods(ctx.text(rel), rel, it) if lang == "v" and run_shipped \
            else []
        dmethods = dafny_hole_methods(ctx.text(rel), rel, it) if lang == "d" and run_shipped \
            else []
        if dmethods:
            # a Dafny item with several hole methods (DV5c, Q17.H1d): one gate per
            # method, by its qualified symbol; the item passes when each fails
            ran += 1
            m_ok, m_lines = dafny_methods_gate(ctx, it, rel, path, dmethods)
            ok, lines = ok and m_ok, lines + m_lines
            run_shipped = False
        if methods:
            # a trait-impl item: one gate per hole method, by its qualified
            # symbol (QPLAN §30 Q65(a)); the item passes when each fails
            ran += 1
            m_ok, m_lines = impl_methods_gate(ctx, it, rel, path, methods, shipped_modes, seeds)
            ok, lines = ok and m_ok, lines + m_lines
            run_shipped = False
        if lang == "v" and run_shipped:
            tb, problem = declared_triv_body(ctx, it, rel)
            if problem:
                bad += 1
                print(f"  ? {it['id']}  no gate run: {problem}")
                continue
            twin = ctx.root / core.REF_DIR / rel
            stext = open_spec_statement(ctx.text(rel), twin.read_text(encoding="utf-8"), it,
                                        open_spec_symbols_of(ctx, rel)) \
                if twin.is_file() else None
            if stext is not None:
                body_modes = shipped_modes
                if modes is None and given_body_annotation(
                        ctx.text(rel), twin.read_text(encoding="utf-8"), it):
                    body_modes = ["TRIV"]
                    lines.append(f"    {it['id']}: a contract annotation with its exec body "
                                 "already given: TRIV tests the completed contract; RGN "
                                 "tests the missing annotation")
                res = statement_gate(ctx, it, rel, stext, body_modes, seeds, tb)
                lines.append(f"    {it['id']}: an open statement (QPLAN §6 Q44): the gate runs "
                             "with its twin's clauses laid over the shipped declaration")
            else:
                res = V.empty_body(path, it["id"], modes=shipped_modes, seeds=seeds,
                                   triv_body=tb)
            if tb is not None:
                lines.append(f"    {it['id']}: TRIV runs the item's declared trivial body (its "
                             "twin's `triv:` line)")
        elif run_shipped:
            res = D.empty_body(path, it["id"])
            outs = [k for k, v in res.per_symbol.items() if v == "inconclusive"]
            if outs:
                lines.append(f"    {it['id']}: {', '.join(outs)} ran out of resources at the "
                             "pinned limit: counted as failing (QPLAN §30 Q66)")
        if run_shipped:
            ran += 1
            killed = None
            if lang == "v" and res.verdict == "verified":
                rules = F.block_rules(ctx.lines(rel), it["line_start"], it["line_end"])
                # an open statement's variants were built on the twin's clauses
                killed = eb_form_killed(stext or ctx.text(rel), rel, it, res, rules,
                                        given_names(ctx.text(rel), rel, it))
            if killed:
                g_ok, g_lines = True, [
                    f"  ✓ {it['id']}  the empty body fails in every run but its whole-goal "
                    f"{mode} variant, a construct-free answer that fails its forms: {why} ({rel})"
                    for mode, why in killed]
            else:
                g_ok, g_lines = gate_line(it, rel, res, "the empty body")
            ok, lines = ok and g_ok, lines + g_lines
            lines += [f"    {core.show(f.file, ctx.root)}:{f.line}: {f.kind}" for f in res.findings
                      if f.kind != "refused"]
        if run_region:
            ran += 1
            res = region_gate(ctx, it, rel, lang, seeds)
            g_ok, g_lines = gate_line(it, rel, res, f"the twin without its {len(regions)} "
                                      f"learner region(s)")
            ok, lines = ok and g_ok, lines + g_lines
            lines += [f"    {core.show(f.file, ctx.root)}:{f.line}: {f.kind}" for f in res.findings
                      if f.kind != "refused"]
        elif regions:
            lines.append(f"    {it['id']}: region gate skipped (--eb-modes names no RGN)")
        if run_forms:
            f_ok, f_lines = forms_gate(ctx, shadows, it, rel, lang, seeds if lang == "v"
                                       else None)
            if f_lines:
                ran += 1
                ok, lines = ok and f_ok, lines + f_lines
        elif F.block_rules(ctx.lines(rel), it["line_start"], it["line_end"]):
            lines.append(f"    {it['id']}: forms gate skipped (--eb-modes names no FORMS)")
        if skip and skip.startswith(FUNCTION_SKIP) and not any(
                "construct-free answer" in ln for ln in lines):
            ok = False
            lines.append(f"  ? {it['id']}  no gate run: a function hole needs a `cfree:` line "
                         f"in its twin's block ({core.REF_DIR}/{rel})")
        if not ok and admitted_false(ctx, it["id"]):
            ok = True
            lines.append(f"    {it['id']}: not admitted (MODULES.toml: admitted = false, 0 "
                         "minutes): the findings above are why; they do not fail the run")
        if not ran and skip:
            pass
        elif not ran:
            ok = False
            lines.append(f"  ? {it['id']}  no gate run: --eb-modes names only RGN and its twin "
                         "marks no learner region" if not modes or "FORMS" not in modes else
                         f"  ? {it['id']}  no gate run: --eb-modes names only RGN or FORMS and "
                         "the item has no such gate")
        bad += not ok
        for line in lines:
            print(line)
    return bad


# =====================================================================================
# CLI
# =====================================================================================

def main(argv=None):
    ap = argparse.ArgumentParser(prog="firsttry", description="The prediction-slot gate.")
    ap.add_argument("id", nargs="?", help="module id (Q04, R06); --lint-hollow also takes --all")
    m = ap.add_mutually_exclusive_group()
    for flag in ("--check", "--report", "--record", "--exit", "--lint-hollow", "--empty-body"):
        m.add_argument(flag, action="store_const", const=flag, dest="mode")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--all", action="store_true", help="--lint-hollow: every non-planned module")
    # Kept so a caller written before DV1c still parses; it no longer changes
    # anything (no armed module passes loudly by itself).
    ap.add_argument("--allow-empty", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--eb-modes", help="--empty-body: Verus modes, comma-separated")
    ap.add_argument("--eb-seeds", help="--empty-body: Verus seeds, comma-separated")
    ap.add_argument("--root", type=Path, default=core.REPO, help=argparse.SUPPRESS)
    try:
        a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as e:
        return core.EXIT_USAGE if e.code else 0
    mode = a.mode or "--report"
    root = a.root.resolve()
    if a.strict and mode != "--report":
        print("firsttry: --strict goes with --report", file=sys.stderr)
        return core.EXIT_USAGE
    if a.all and mode != "--lint-hollow":
        print("firsttry: --all goes with --lint-hollow", file=sys.stderr)
        return core.EXIT_USAGE
    if (a.eb_modes or a.eb_seeds) and mode != "--empty-body":
        print("firsttry: --eb-modes/--eb-seeds go with --empty-body", file=sys.stderr)
        return core.EXIT_USAGE
    if bool(a.id) == bool(a.all):
        print("firsttry: usage: firsttry.sh <ID> [--check | --report [--strict] | --record | "
              "--exit | --lint-hollow | --empty-body]  (or --lint-hollow --all)",
              file=sys.stderr)
        return core.EXIT_USAGE
    try:
        if mode == "--lint-hollow":
            if a.all:
                mids, idle = core.armed_or_none(root)
            else:
                mids, idle = [core.record(root, a.id)["id"]], None
            return mode_lint_hollow(root, mids, idle)
        ctx = Ctx(root, a.id)
        if mode == "--check":
            return mode_check(ctx)
        if mode == "--report":
            return mode_report(ctx, a.strict)
        if mode == "--record":
            return mode_record(ctx)
        if mode == "--exit":
            return mode_exit(ctx)
        core.require_author(root, "firsttry --empty-body")
        modes = [x for x in a.eb_modes.split(",") if x] if a.eb_modes else None
        try:
            seeds = [int(x) for x in a.eb_seeds.split(",") if x] if a.eb_seeds else None
        except ValueError:
            print("firsttry: --eb-seeds takes integers", file=sys.stderr)
            return core.EXIT_USAGE
        return mode_empty_body(ctx, modes, seeds)
    except core.Refusal as e:
        print(f"firsttry: refused: {e}", file=sys.stderr)
        return core.EXIT_REFUSED
    except SystemExit as e:
        return e.code
    except core.common.ToolchainError as e:
        print(f"firsttry: {e}; run scripts/get_toolchain.sh dafny|verus", file=sys.stderr)
        return core.EXIT_REFUSED
    except core.common.CapError as e:
        print(f"firsttry: {e}", file=sys.stderr)
        return core.EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
