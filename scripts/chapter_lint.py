#!/usr/bin/env python3
"""chapter_lint.py — the chapter skeleton lint (phase DV2b; spec §2.4.3, §3.15;
design §14.4). Static: it reads the chapter, the registry, the module's items,
expected/<ID>.counts and expected/<ID>.chapter.toml, and never runs a tool
(pins.py --chapter re-runs the pinned fences; scripts/ci.sh's pins job).

What a chapter (the registry's `chapter`) must hold, checked in order:

  title      line 1 is `# <ID> — <registry title>` (an em dash), the only H1
  opening    a survey module: an "In this module" contents list; any other:
             "Three ideas do all the work" and a numbered list of at least three
  section 0  Q track: the first numbered section is `## 0. …`; outside the
             survey tier its title starts "How this module works"
  files      a "This module's files" table naming every exercise, check, exit,
             agent and harness file that expected/<ID>.counts pins (schema 2),
             each exercise, harness (learner Python), exit and agent row
             stating the file's shipped hole count as the tool counts it
             (`3 holes`, `1 hole`, `no hole`;
             a row of two files `2 + 3 holes` in the files' order, or `1 hole
             each`) and an agent file's planted errors (`4 … errors`); a row
             naming a
             given layer (`…/given/…`) and one naming the reference
             ("Solutions", "… LAST")
  sections   numbered H2s `## <n>. <title>`, numbered consecutively; Q track:
             one `## <n>. S<k> — <title>` per registry strand, in strand order;
             `---` above every H2 but the first
  required   `## <k>. On paper, before the keyboard` exactly when paper = true;
             `## <k>. The exercise file` (with `scripts/firsttry.sh <ID>
             --check` and a Done line); `## <k>. Exercise (agentic): …` when
             the module has agentic files (its CONTRACT blockquote
             `> **CONTRACT (for /contract <ID> — run it in a FRESH
             session):**`) or a hand-written one (a module listed in
             .claude/skills/contract/hand_written.toml: no CONTRACT
             blockquote; the section names the exercise and quotes the
             entry's /contract refusal line, and the module's `agentic` list
             is empty, else the entry is stale); a heading "What the
             instruments can and cannot see"; Q track: `## Exit (closed
             book…` (with `scripts/firsttry.sh <ID> --exit` and the
             threshold n/N); `## Instructor
             touchpoints` (every skill named: /tutor, /discuss, /review,
             /viva, /grade-paper, /review-code, /contract; and Solutions);
             `## What <ID> planted` with a table (a survey module may end with
             "Done when" and "Where this is going" instead). In this order
             after the strand sections.
  predicts   one callout `> **Predict (P<n>) — commit in the file before
             reading on.** <question>` per P item of the module (P<n>, or the
             full local id), no other; a pinned fence whose output settles a
             prediction (pins.entry_waits: its `answers`, and the `after:`
             items and slots of its specimen inputs) sits AFTER that item's
             callout, and never quotes a later module's prediction; an entry's
             `answers` name existing prediction items only (never a hole, exit
             or test-out); a bare label shared by two items (P4 for P4d and
             P4v) is ambiguous
  diagrams   3 to 5 mermaid fences; flowchart node labels quoted, no node id
             that looks like a module id, a sentence before and after each
  fences     every bare fence is an output fence: pinned (`<!-- pin: <id> -->`
             above it); a pinned fence is bare; a tagged fence carries a
             source language (SOURCE_TAGS), never an output tag such as
             `text` or `console`; every fence closes; plus pins.py's static
             half (each pin names an entry, each entry is quoted once, each
             body matches its capture hash, each entry's inputs are as
             captured: stale in the author's context is a problem, elsewhere
             a note)
  item ids   every item id the chapter names (`Q01.H1d`, and a bare local id
             like `H1d` in prose) exists in its armed module

Usage:
  chapter_lint.py <ID> [<ID> ...]   lint these modules' chapters
  chapter_lint.py --all             every non-planned module; none: a loud pass
Output: `path:line: problem` lines, then one summary line per module.
Exit: 0 clean · 1 problems (a missing chapter of an armed module included) ·
2 usage · 3 refused (unknown or planned module, unusable registry, a missing or
malformed hand_written.toml).
"""

import argparse
import importlib.machinery
import importlib.util
import re
import sys
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load(name, file):
    if name in sys.modules:
        return sys.modules[name]
    loader = importlib.machinery.SourceFileLoader(name, str(SCRIPTS / file))
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    sys.modules[name] = mod
    loader.exec_module(mod)
    return mod


pins = _load("pins", "pins.py")
ft = _load("firsttry", "firsttry.py")
core, ci, ccm = pins.core, pins.ci, pins.ccm

SOURCE_TAGS = ("dafny", "rust", "python", "toml", "json", "bash", "sh", "mermaid", "tex",
               "latex", "lean", "markdown", "md")
SKILLS = ("/tutor", "/discuss", "/review", "/viva", "/grade-paper", "/review-code", "/contract")
# The modules whose agentic exercise the learner writes by hand with no AI session
# while the registry's `agentic` list is empty (Δ114). The ONE list is this data
# file beside the contract skill: /contract reads it at Step 0 item 4, this lint
# reads it here, and neither keeps a copy.
HAND_WRITTEN_FILE = ".claude/skills/contract/hand_written.toml"
HAND_WRITTEN_KEYS = ("exercise", "refusal", "where")
# The count-pin roles whose files-table row states the shipped hole count (a
# check unit ships none; a harness file is a learner Python exercise, DV4).
HOLE_ROLES = ("exercise", "harness", "exit", "agent")
_PLABEL = r"P[1-9]\d*(?:dv|py|d|v)?"
PREDICT = re.compile(rf"^> \*\*Predict \(({_PLABEL}(?:, {_PLABEL})*)\) — commit in the files? "
                     r"before reading on\.\*\*\s*(.*)$")
# the spec's own placeholder, quoted to show the form: not a box
PREDICT_TEMPLATE = re.compile(r"^> \*\*Predict \(P(?:n|<n>)\) — ")
CONTRACT = "> **CONTRACT (for /contract {mid} — run it in a FRESH session):**"
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
NUMBERED = re.compile(r"^(\d+)\.\s+(.*)$")
STRAND = re.compile(r"^S([1-9]\d*) — (\S.*)$")
FULL_ID = re.compile(r"(?<![\w.])([QR]\d\d)\.([WCPHXTA][1-9]\d*(?:dv|py|d|v))\b")
LOCAL_ID = re.compile(r"(?<![\w./-])([WCPHXTA][1-9]\d*(?:dv|py|d|v))(?![\w-])")
MODULE_LIKE = re.compile(r"\b[QRqr]\d\d\b")


NUMBER_WORDS = {"no": 0, "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_NUM = r"(?:\d+|" + "|".join(NUMBER_WORDS) + r")"


def hand_written(root):
    """{module id: {exercise, refusal, where}} from HAND_WRITTEN_FILE under root.
    A missing or malformed file raises core.Refusal: it never reads as an empty
    list, which would silently drop the hand-written rules."""
    path = Path(root) / HAND_WRITTEN_FILE
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise core.Refusal(f"{HAND_WRITTEN_FILE} is missing (the list of hand-written agentic "
                           "exercises, Δ114)") from None
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise core.Refusal(f"{HAND_WRITTEN_FILE}: unreadable ({e})") from None
    for mid, ent in data.items():
        where = f"{HAND_WRITTEN_FILE}: [{mid}]"
        if not re.fullmatch(r"[QR]\d\d", mid) or not isinstance(ent, dict):
            raise core.Refusal(f"{where}: every entry is a table named by a module id")
        if tuple(sorted(ent)) != HAND_WRITTEN_KEYS or \
                not all(isinstance(v, str) and v.strip() for v in ent.values()):
            raise core.Refusal(f"{where}: needs exactly the keys {', '.join(HAND_WRITTEN_KEYS)}, "
                               "each a non-empty string")
        if mid not in ent["refusal"] or ent["exercise"] not in ent["refusal"]:
            raise core.Refusal(f"{where}: its refusal line names the module and the exercise")
    return data


def hand_written_problems(entry, text):
    """What the agentic section's prose `text` lacks for a hand-written exercise:
    the exercise's name, and the entry's /contract refusal line quoted verbatim
    (blockquote markers and line breaks aside)."""
    out = []
    if entry["exercise"].lower() not in text.lower():
        out.append(f"the agentic section gives the {entry['exercise']} instructions (the "
                   "learner writes it by hand, CLAUDE.md)")
    flat = " ".join(" ".join(re.sub(r"^\s*>\s?", "", x) for x in text.split("\n")).split())
    if " ".join(entry["refusal"].split()) not in flat:
        out.append(f"the agentic section quotes the /contract refusal line of "
                   f"{HAND_WRITTEN_FILE} verbatim: \"{entry['refusal']}\"")
    return out


def stated_counts(text, noun):
    """[n, ...] of every count of <noun> a table cell states, in order: `3
    holes`, `**5 holes**`, `2 + 3 holes` (two counts), `1 hole each`, `no
    hole`, `0 holes`, `hole-free` (up to two words between a count and its
    noun)."""
    t = re.sub(r"[*_`]", "", text)
    out = []
    pat = (rf"(?i)(?<![\w.])({_NUM}(?:\s*(?:\+|,|and|/)\s*{_NUM})*)"
           rf"(?:\s+[\w-]+){{0,2}}?\s+{noun}s?\b")
    for m in re.finditer(pat, t):
        for w in re.findall(rf"(?i){_NUM}", m.group(1)):
            out.append(int(w) if w.isdigit() else NUMBER_WORDS[w.lower()])
    if re.search(rf"(?i)\b{noun}-free\b", t):
        out.append(0)
    return out


def count_said(row, paths, path, n, noun):
    """True when a files-table row states `n` <noun>s for `path`: a row naming
    k of the pinned files and stating k counts gives them in the files'
    order (`a.dfy`, `b.rs` … `2 + 3 holes`); one count covers every file of
    the row (`1 hole each`); otherwise any stated count may be the file's."""
    said = stated_counts(row, noun)
    named = sorted((row.index(p), p) for p in paths if p in row)
    if len(said) == len(named) > 1:
        return said[[p for _, p in named].index(path)] == n
    return n in said


class Chapter:
    """A chapter's lines with its fences masked out (headings and prose are
    read outside fences only)."""

    def __init__(self, lines):
        self.lines = lines
        self.fences, self.dangling = pins.parse_chapter(lines)
        self.in_fence = set()
        for f in self.fences:
            end = f.close if f.close is not None else len(lines) - 1
            self.in_fence.update(range(f.open, end + 1))
        self.headings = []                     # (index, level, title)
        for i, x in enumerate(lines):
            if i in self.in_fence:
                continue
            m = HEADING.match(x)
            if m:
                self.headings.append((i, len(m.group(1)), m.group(2)))
        self.h2 = [(i, t) for i, lv, t in self.headings if lv == 2]

    def section(self, i):
        """Line indices of the H2 section that starts at i (to the next H2)."""
        nxt = [j for j, _ in self.h2 if j > i]
        return range(i, nxt[0] if nxt else len(self.lines))

    def text_of(self, rng, prose_only=True):
        return "\n".join(self.lines[k] for k in rng if not (prose_only and k in self.in_fence))


def lint(root, rec, author_ok, hand=None):
    """(problems, summary) of one module's chapter. hand: hand_written(root),
    read here when not given."""
    root = Path(root)
    mid, rel = rec["id"], rec["chapter"]
    entry = (hand_written(root) if hand is None else hand).get(mid)
    path = root / rel
    if not path.is_file():
        return ([f"{rel}:0: {mid} is armed and its chapter does not exist"] +
                pins.chapter_static(root, rec, author_ok).problems), f"{rel}: missing"
    lines = path.read_text(encoding="utf-8").split("\n")
    ch = Chapter(lines)
    out = []

    def at(i, msg):
        out.append(f"{rel}:{i + 1}: {msg}")

    q = rec["track"] == "Q"
    survey = rec["tier"] == "survey"
    first_h2 = ch.h2[0][0] if ch.h2 else len(lines)

    # ---- title and opening ------------------------------------------------------------
    want = f"# {mid} — {rec['title']}"
    if not lines or lines[0] != want:
        at(0, f"line 1 is the title `{want}` (the registry title, an em dash)")
    for i, lv, _ in ch.headings:
        if lv == 1 and i != 0:
            at(i, "a second H1: the title is the only one")
    head = ch.text_of(range(0, first_h2))
    if survey:
        if "In this module" not in head:
            at(0, "a survey chapter opens with an \"In this module\" contents list (before its "
                  "first section)")
    else:
        k = next((i for i in range(first_h2) if i not in ch.in_fence and
                  "Three ideas do all the work" in lines[i]), None)
        if k is None:
            at(0, "the opening states \"Three ideas do all the work\" and a numbered list (spec "
                  "§2.4.3 item 1)")
        else:
            items = [i for i in range(k + 1, first_h2) if re.match(r"^\d+\.\s+\S", lines[i])]
            if len(items) < 3:
                at(k, "\"Three ideas do all the work\" is followed by a numbered list of three")

    # ---- numbered sections, strands, separators -----------------------------------------
    numbered = []
    for i, t in ch.h2:
        m = NUMBERED.match(t)
        if m:
            numbered.append((i, int(m.group(1)), m.group(2)))
        elif re.match(r"^\d+\s", t) or re.match(r"^\d+\)", t):
            at(i, "a numbered section is `## <n>. <title>`")
    nums = [n for _, n, _ in numbered]
    if nums and (nums != list(range(nums[0], nums[0] + len(nums))) or nums[0] > 1):
        at(numbered[0][0], f"sections are numbered consecutively from 0 or 1 (found "
                           f"{', '.join(map(str, nums))})")
    if q:
        if not numbered or numbered[0][1] != 0:
            at(first_h2 if first_h2 < len(lines) else 0,
               "a Q chapter's first numbered section is `## 0. …`")
        elif not survey and not numbered[0][2].startswith("How this module works"):
            at(numbered[0][0], "`## 0. How this module works, pretest, test-out` opens a depth "
                               "chapter (spec §2.4.3 item 1)")
    strands = []
    for i, n, t in numbered:
        m = STRAND.match(t)
        if m:
            strands.append((i, f"S{m.group(1)}"))
        elif re.match(r"^S\d+\s*[-–—:]", t):
            at(i, "a strand section is `## <n>. S<k> — <title>` (an em dash between spaces)")
    if q:
        got = [s for _, s in strands]
        if got != list(rec["strands"]):
            at(strands[0][0] if strands else first_h2 if first_h2 < len(lines) else 0,
               f"one strand section per strand of {mid}, in strand order: "
               f"{' '.join(rec['strands'])} (found {' '.join(got) or 'none'})")
    for i, _ in ch.h2[1:]:
        j = i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        if j < 0 or lines[j].strip() != "---":
            at(i, "`---` separates top sections (above every H2 but the first)")

    # ---- required sections and their order ------------------------------------------------
    def h2_like(pred):
        return [(i, t) for i, t in ch.h2 if pred(NUMBERED.match(t).group(2)
                                                 if NUMBERED.match(t) else t)]

    paper = h2_like(lambda t: t.startswith("On paper, before the keyboard"))
    exfile = h2_like(lambda t: t.startswith("The exercise file"))
    agentic = h2_like(lambda t: t.startswith("Exercise (agentic)"))
    exit_ = h2_like(lambda t: t.startswith("Exit (closed book"))
    touch = h2_like(lambda t: t == "Instructor touchpoints")
    planted = h2_like(lambda t: t == f"What {mid} planted")
    done = h2_like(lambda t: t.startswith("Done when"))
    going = h2_like(lambda t: t.startswith("Where this is going"))
    if rec["paper"] and not paper:
        at(first_h2 if ch.h2 else 0, f"paper = true: `## <k>. On paper, before the keyboard` is "
                                     "required")
    if not rec["paper"] and paper:
        at(paper[0][0], "paper = false: this module has no On-paper section")
    for name, got in (("On paper, before the keyboard", paper), ("The exercise file", exfile),
                      ("Exercise (agentic)", agentic)):
        for i, t in got:
            if not NUMBERED.match(t):
                at(i, f"`{name}` is a numbered section (`## <k>. {name}…`)")
    if not exfile:
        at(0, "`## <k>. The exercise file` is required")
    else:
        sec = ch.text_of(ch.section(exfile[0][0]), prose_only=False)
        if f"firsttry.sh {mid} --check" not in sec:
            at(exfile[0][0], f"The exercise file states the slot protocol (`scripts/firsttry.sh "
                             f"{mid} --check`)")
        if not re.search(r"\bDone\b", sec):
            at(exfile[0][0], "The exercise file states its Done line")
    if entry is not None and rec["agentic"]:
        at(0, f"{HAND_WRITTEN_FILE} lists {mid}, whose registry `agentic` is not empty: "
              f"/contract {mid} runs, so the entry is stale (Δ114)")
    needs_agentic = bool(rec["agentic"]) or entry is not None
    if needs_agentic and not agentic:
        at(0, "`## <k>. Exercise (agentic): <title>` is required")
    for i, _ in agentic:
        sec = ch.section(i)
        has = any(lines[k].startswith(CONTRACT.format(mid=mid)) for k in sec)
        if rec["agentic"] and not has:
            at(i, f"the agentic section holds the CONTRACT blockquote `"
                  f"{CONTRACT.format(mid=mid)}`")
        if not rec["agentic"]:
            if has:
                at(i, f"{mid} has no agentic file: /contract {mid} refuses, so no CONTRACT "
                      "blockquote")
            if entry is not None:
                for msg in hand_written_problems(entry, ch.text_of(sec)):
                    at(i, msg)
    if not any(re.match(r"^(?:\d+\.\s+)?What the instruments can and cannot see", t)
               for _, lv, t in ch.headings if 2 <= lv <= 4):
        at(0, "a heading \"What the instruments can and cannot see\" is required (spec §2.4.3)")
    if q and rec["exits"]:
        if not exit_:
            at(0, "`## Exit (closed book)` is required")
        else:
            sec = ch.text_of(ch.section(exit_[0][0]), prose_only=False)
            if f"firsttry.sh {mid} --exit" not in sec:
                at(exit_[0][0], f"the Exit section names its scoring command (`scripts/"
                                f"firsttry.sh {mid} --exit`)")
            rule = ft.exit_rule(rec) or {}
            if "need" in rule:
                a, b = rule["need"]
                if not re.search(rf"(?<!\d){a}\s*(?:/|of|out of)\s*{b}(?!\d)", sec):
                    at(exit_[0][0], f"the Exit section states the threshold ({a}/{b})")
    if not touch:
        at(0, "`## Instructor touchpoints` is required")
    else:
        sec = ch.text_of(ch.section(touch[0][0]), prose_only=False)
        missing = [s for s in SKILLS if not re.search(re.escape(s) + r"(?![\w-])", sec)]
        if missing:
            at(touch[0][0], f"Instructor touchpoints names every skill, as a touchpoint or as "
                            f"\"not this module\" (missing: {', '.join(missing)})")
        if "Solutions" not in sec:
            at(touch[0][0], "Instructor touchpoints says Solutions last")
    if planted:
        sec = ch.section(planted[0][0])
        if not any(lines[k].startswith("|") for k in sec if k not in ch.in_fence):
            at(planted[0][0], f"What {mid} planted is a seed → harvest table")
    elif survey and done and going:
        pass
    else:
        at(0, f"`## What {mid} planted` (a seed → harvest table) is required" +
           (" (a survey chapter may end with \"Done when\" and \"Where this is going\" instead)"
            if survey else ""))
    order = [("the strand sections", [strands[-1][0]] if strands else []),
             ("On paper", [i for i, _ in paper]), ("The exercise file", [i for i, _ in exfile]),
             ("Exercise (agentic)", [i for i, _ in agentic]), ("Exit", [i for i, _ in exit_]),
             ("Instructor touchpoints", [i for i, _ in touch]),
             ("the closing section", [i for i, _ in planted or going])]
    seq = [(name, idx[0]) for name, idx in order if idx]
    for (n1, i1), (n2, i2) in zip(seq, seq[1:]):
        if i2 < i1:
            at(i2, f"{n2} comes after {n1} (spec §2.4.3 order)")

    # ---- files table ------------------------------------------------------------------
    out += files_table(root, rec, ch, rel)

    # ---- predicts -----------------------------------------------------------------------
    items, errs = core.module_items(root, rec)
    out += [f"{rel}:0: {e}" for e in errs]
    p_items = {}
    for it in items:
        if it["kind"] == "P":
            n = re.match(r"P(\d+)", it["id"].split(".", 1)[1]).group(1)
            p_items.setdefault(n, []).append(it["id"])
    boxes = {}
    for i, x in enumerate(lines):
        if i in ch.in_fence or not re.match(r"^\s*(?:>\s*)?\*\*Predict\s*\(", x) or \
                PREDICT_TEMPLATE.match(x):
            continue
        m = PREDICT.match(x)
        if not m:
            at(i, "a predict callout is `> **Predict (P<n>) — commit in the file before reading "
                  "on.** <question>` (a pair: `(P<n>, P<m>) — commit in the files …`)")
            continue
        question = m.group(2).strip()
        k = i + 1
        while not question and k < len(lines) and lines[k].startswith(">"):
            question = lines[k].lstrip(">").strip()
            k += 1
        if not question:
            at(i, f"Predict ({m.group(1)}) states its question")
        for label in m.group(1).split(", "):
            n = re.match(r"P(\d+)", label).group(1)
            ids = p_items.get(n, [])
            if label != f"P{n}":
                ids = [y for y in ids if y.endswith("." + label)]
            if len(ids) > 1:
                at(i, f"Predict ({label}) is ambiguous: {mid} has "
                      f"{', '.join(y.split('.', 1)[1] for y in ids)}; name the item")
                continue
            if not ids:
                at(i, f"Predict ({label}) names no prediction item of {mid}")
                continue
            if ids[0] in boxes:
                at(i, f"Predict ({label}) appears twice (also line {boxes[ids[0]] + 1})")
                continue
            boxes[ids[0]] = i
    for n, ids in sorted(p_items.items(), key=lambda kv: int(kv[0])):
        for iid in ids:
            if iid not in boxes:
                at(0, f"no predict callout for {iid} (`> **Predict (P{n}) — commit in the file "
                      "before reading on.**`)")

    # ---- fences, pins, and answers after their boxes --------------------------------------
    for f in ch.fences:
        if f.close is None:
            at(f.open, "this fence is never closed")
        tag = f.info.split()[0].lower() if f.info else ""
        if f.pin is None and not tag:
            at(f.open, "a bare fence is output: pin it (`<!-- pin: <id> -->` on the line above, "
                       "an entry in expected/" + f"{mid}.chapter.toml)")
        elif tag and tag not in SOURCE_TAGS:
            at(f.open, f"fence tag {tag!r}: a source fence carries its language "
                       f"({', '.join(SOURCE_TAGS)}); output fences are bare and pinned")
    for i, x in enumerate(lines):
        if i not in ch.in_fence and re.match(r"^\s*>\s*(```|~~~)\s*$", x):
            at(i, "a bare fence inside a blockquote cannot be pinned: move the output out of it")
    st = pins.chapter_static(root, rec, author_ok)
    out += st.problems
    notes = []
    if st.stale and not author_ok:
        notes.append(f"{len(st.stale)} pin(s) stale against the files as captured (your own "
                     "work; the author's CI re-captures)")
    later = {m["id"] for m in core.registry(root).get("module", []) if isinstance(m, dict)
             and isinstance(m.get("id"), str) and m["id"][0] == mid[0] and m["id"] > mid}
    kinds = {it["id"]: it["kind"] for it in items}
    status = {m["id"]: m.get("status") for m in core.registry(root).get("module", [])
              if isinstance(m, dict) and isinstance(m.get("id"), str)}
    for e, f in st.quoted:
        for iid in e.get("answers", []) if isinstance(e.get("answers"), list) else []:
            if not isinstance(iid, str):
                continue
            owner = iid.split(".", 1)[0]
            if owner != mid and status.get(owner) not in (None, "planned") and \
                    not any(k.startswith(owner + ".") for k in kinds):
                its, _ = core.module_items(root, core.record(root, owner))
                kinds.update({it["id"]: it["kind"] for it in its})
            if status.get(owner) in (None, "planned"):
                at(f.pin_line, f"pin {e['id']}: its `answers` names {iid}, whose module is "
                               "unknown or planned")
            elif iid not in kinds:
                at(f.pin_line, f"pin {e['id']}: its `answers` names {iid}, no item of {owner}")
            elif kinds[iid] != "P":
                at(f.pin_line, f"pin {e['id']}: its `answers` names {iid}, which is no "
                               "prediction: a chapter never quotes a hole, exit or test-out "
                               "answer")
        if e.get("kind", "command") != "command" or not isinstance(e.get("cmd"), list):
            waits = list(e.get("answers", []))
        else:
            try:
                waits = pins.entry_waits(root, e)
            except (OSError, ValueError):
                waits = list(e.get("answers", []))
        for iid in waits:
            owner = iid.split(".", 1)[0]
            if owner == mid:
                if iid in boxes and boxes[iid] > f.pin_line:
                    at(f.pin_line, f"pin {e['id']} settles {iid}, whose predict box comes later "
                                   f"(line {boxes[iid] + 1}): the answer appears only after the "
                                   "box")
            elif owner in later:
                at(f.pin_line, f"pin {e['id']} settles {iid}, a later module's prediction")

    # ---- diagrams ---------------------------------------------------------------------------
    mer = [f for f in ch.fences if f.info.split()[:1] == ["mermaid"]]
    if not 3 <= len(mer) <= 5:
        at(mer[0].open if mer else 0, f"{len(mer)} mermaid diagram(s): a chapter has 3 to 5 "
                                      "(spec §3.15 rule 10)")
    for f in mer:
        out += [f"{rel}:{f.open + 2 + k}: {msg}" for k, msg in mermaid_problems(f.body)]
        before = f.open - 1
        while before >= 0 and not lines[before].strip():
            before -= 1
        after = (f.close if f.close is not None else len(lines)) + 1
        while after < len(lines) and not lines[after].strip():
            after += 1
        if before < 0 or re.match(r"^(#|```|~~~|---|\||<!--)", lines[before]):
            at(f.open, "frame each diagram with a sentence before it")
        if after >= len(lines) or re.match(r"^(#|```|~~~|---|<!--)", lines[after]):
            at(f.open, "frame each diagram with a takeaway after it")

    # ---- item ids ----------------------------------------------------------------------------
    out += item_id_problems(root, rec, ch, rel, items)

    words = len(re.findall(r"\S+", ch.text_of(range(len(lines)))))
    summary = (f"{rel}: {len(strands)} strand section(s), {len(boxes)} predict box(es), "
               f"{len(mer)} diagram(s), {len(st.quoted)} pinned fence(s), {words} words"
               + "".join(f"; {n}" for n in notes))
    return out, summary


def files_table(root, rec, ch, rel):
    """Problems of the "This module's files" table (hole counts from
    expected/<ID>.counts)."""
    lines, mid = ch.lines, rec["id"]
    k = next((i for i, x in enumerate(lines) if i not in ch.in_fence and
              "This module's files" in x), None)
    if k is None:
        return [f"{rel}:0: a \"This module's files\" table is required (spec §2.4.3 item 2)"]
    start = next((i for i in range(k + 1, min(k + 6, len(lines))) if lines[i].startswith("|")),
                 None)
    if start is None:
        return [f"{rel}:{k + 1}: \"This module's files\" is followed by its table"]
    end = start
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    rows = [lines[i] for i in range(start, end) if not re.match(r"^\|[\s:|-]+\|?\s*$", lines[i])]
    out = []

    def bad(msg):
        out.append(f"{rel}:{start + 1}: {msg}")

    table, problems = core.read_file_pins(root, mid)
    if problems or table is None:
        bad(f"expected/{mid}.counts pins no file's shipped state (schema 2): the table's hole "
            f"counts cannot be checked; re-pin with vcheck --ref --pin-counts {mid}")
        table = {}
    for path, e in sorted(table.items()):
        mine = [r for r in rows if path in r]
        if not mine:
            bad(f"the files table names {path} (its {e['role']} file)")
            continue
        if e["role"] in HOLE_ROLES and \
                not any(count_said(r, table, path, e["holes"], "hole") for r in mine):
            bad(f"{path}: its row states the shipped hole count, {e['holes']} (tool-counted, "
                f"expected/{mid}.counts; a row of two files states `a + b holes`)")
        if e["role"] == "agent" and e.get("errors") and \
                not any(count_said(r, table, path, e["errors"], "error") for r in mine):
            bad(f"{path}: its row states the agent file's shipped errors, {e['errors']}")
    if not any("/given/" in r for r in rows):
        bad("the files table names the given layer(s) (a `…/given/…` path)")
    if not any("Solutions" in r and re.search(r"(?i)\blast\b", r) for r in rows):
        bad("the files table names the reference, \"yours to open LAST\"")
    return out


def mermaid_problems(body):
    """[(body line index, problem)] of one mermaid diagram (spec §3.15 rule 10)."""
    out = []
    kind = next((x.split()[0] for x in body if x.strip() and not x.strip().startswith("%%")), "")
    flow = kind in ("flowchart", "graph")
    for k, raw in enumerate(body):
        x = raw.strip()
        if not x or x.startswith("%%"):
            continue
        bare = re.sub(r'"[^"]*"', '""', x)
        # arrows and their pieces (-->, ---, -. "…" .->, ==>, <-->, --x, ~~~) are not shapes
        bare = re.sub(r"<?[-=.~]{2,}[>xo]?|<?[-=.~]+>", " ", bare)
        if flow and re.match(r"^(classDef|class|style|linkStyle|click|direction|end)\b", bare):
            continue
        if MODULE_LIKE.search(bare):
            out.append((k, "a mermaid node id looks like a module id (Q01, R07): rename it"))
        if flow and k > 0:
            for m in re.finditer(r"[\[({>]+([^\])}\"]*)", bare):
                if m.group(1).strip(" /\\"):
                    out.append((k, "flowchart node labels are quoted (`a[\"…\"]`)"))
                    break
            for m in re.finditer(r"\|([^|]*)\|", bare):
                if m.group(1).replace('""', "").strip():
                    out.append((k, "edge labels are quoted (`-->|\"…\"|`)"))
                    break
    return out


def item_id_problems(root, rec, ch, rel, items):
    """Item ids the chapter names that do not exist."""
    mid = rec["id"]
    data = core.registry(root)
    status = {m["id"]: m.get("status") for m in data.get("module", [])
              if isinstance(m, dict) and isinstance(m.get("id"), str)}
    known = {mid: {it["id"] for it in items}}
    out, seen = [], set()
    for i, x in enumerate(ch.lines):
        for m in FULL_ID.finditer(x):
            owner, iid = m.group(1), f"{m.group(1)}.{m.group(2)}"
            if (iid, i) in seen:
                continue
            seen.add((iid, i))
            if owner not in status:
                out.append(f"{rel}:{i + 1}: {iid}: no module {owner}")
                continue
            if status[owner] == "planned":
                out.append(f"{rel}:{i + 1}: {iid} names an item of {owner}, which is planned (its "
                           "items do not exist yet)")
                continue
            if owner not in known:
                its, _ = core.module_items(root, core.record(root, owner))
                known[owner] = {it["id"] for it in its}
            if iid not in known[owner]:
                out.append(f"{rel}:{i + 1}: {iid} is no item of {owner}")
        if i in ch.in_fence:
            continue
        for m in LOCAL_ID.finditer(x):
            iid = f"{mid}.{m.group(1)}"
            start = m.start()
            if start >= 4 and re.match(r"[QR]\d\d\.", x[start - 4:start]):
                continue                    # part of a full id, judged above
            if iid not in known[mid] and (iid, i) not in seen:
                seen.add((iid, i))
                out.append(f"{rel}:{i + 1}: {m.group(1)} is no item of {mid}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="chapter_lint.py", description="The chapter skeleton lint.")
    ap.add_argument("ids", nargs="*", metavar="ID")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--root", type=Path, default=core.REPO, help=argparse.SUPPRESS)
    try:
        a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as e:
        return core.EXIT_USAGE if e.code else 0
    root = a.root.resolve()
    if a.all == bool(a.ids):
        print("chapter_lint: usage: chapter_lint.py <ID> [<ID> ...] | --all", file=sys.stderr)
        return core.EXIT_USAGE
    try:
        if a.all:
            mids, idle = core.armed_or_none(root)
            if idle:
                print(f"chapter_lint: {idle}: passing loudly")
                return core.EXIT_OK
        else:
            mids = a.ids
        recs = [core.record(root, m) for m in mids]
        hand = hand_written(root)
    except core.Refusal as e:
        print(f"chapter_lint: refused: {e}", file=sys.stderr)
        return core.EXIT_REFUSED
    author_ok = core.author_gate(root) is None
    total = 0
    for rec in recs:
        problems, summary = lint(root, rec, author_ok, hand)
        for p in problems:
            print(p)
        total += len(problems)
        print(f"chapter_lint {rec['id']}: {summary}; {len(problems)} problem(s)")
    if len(recs) > 1:
        print(f"chapter_lint: {len(recs)} chapter(s), {total} problem(s)")
    return core.EXIT_OK if not total else core.EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
