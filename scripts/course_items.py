#!/usr/bin/env python3
"""course_items.py — the ONE parser of the course's item markers (spec §3.9,
design §14.3). Every consumer imports it: check_course_map.py (--items, the
coverage group), and later firsttry, pins.py and the reference lint. Nobody
re-implements the grammar.

It is pure text: no registry, no verifier, no file outside the ones it is
given. It never prints file content, only ids, kinds and locations.

Grammar (comment leader `//` in .dfy, .rs, *.dfy.specimen, *.rs.specimen;
`#` in .py; leading whitespace allowed, nothing after the last token):

    // item: <ID>.<K><n><lang> [S<k>] [<format>] [min=<m>]
    // uses: <slug>[, <slug>…]        H, X, T only; directly after the marker
    // need: <target fragment>        X only; directly after the marker
    // pair: <ID>.<K><n><lang>        H, X, T in d or v only; directly after
    <closing automation step>  // did: <what it closed>   (receipt; anywhere)

  <ID>     Q01–Q33, R01–R16 (the registry checks the module)
  <K>      W worked · C card · P predict · H hole · X exit · T test-out ·
           A agent run
  <n>      unpadded positive integer
  <lang>   d (Dafny) | v (Verus) | py (Python) | dv (one item over both
           verifiers: a two-column card, a cross-language predict
           `D:<v> V:<v>`). A d item lives in a Dafny file, a v item in a Verus
           file, a py item in a Python file, a dv item in either verifier file.
  S<k>     the strand, S1–S13: required on Q items, absent on R items (the
           R track has no strands)
  format   P: value | obligation | error | verdict (required);
           C: write:<slug> | recognise:<slug> | diverge:<slug> (required);
           X, T: verdict or nothing; W, H, A: nothing
  min=<m>  X only: the minimum number of filled slots of a multi-slot item
  slug     kebab-case, `/` joining alternatives that fill one slot
           (`assert-by`, `lemma-call/calc`)

Block extent. A block runs from its marker to the line before the next
marker, the next column-0 `/*!` header, the `}` that closes the container
the marker sits in (a Dafny `module`, the `verus!` macro), or end of file;
trailing blank lines are dropped. Python blocks end at the next marker or at
end of file. Text inside block comments and strings is part of the block and
never a marker.

Slots (spec §3.8.3, port formats §3.8.6). Each slot reports
{format, file, line, state}, state ∈ unfilled | filled-disabled | enabled:

  value        `// SLOT: <check>` → unfilled if it holds `???`, else
               filled-disabled; a live check line in the block is enabled:
               Dafny `expect …`, Verus `assert_eq!(…)` / `assert(…)` (with
               `by (compute_only)` for spec values), Python `assert …`
  obligation   `// SLOT: FAILS ???` (unfilled) / `// SLOT: FAILS a c`
               (filled-disabled) / `// FAILS a c` (enabled)
  error        `// SLOT: EXPECT @??? "???"` / `// SLOT: EXPECT @12 "frag"` /
               `// EXPECT @12 "frag"`
  verdict      the answer lives in the module's slot file `slots/<ID>.slots`,
               one line per item: `<K><n><lang> = ???` (unfilled) or
               `<K><n><lang> = "<answer>"` (filled-disabled); it is enabled
               once the item block holds a live `// CHECK <K><n><lang>` line
               (shipped as `// SLOT: CHECK <K><n><lang>`, which is the switch,
               not a second slot). Only the answer's hash is ever pinned.

Usage (files only; module-level parsing with the registry is
`check_course_map.py --items ID [--json]`):
  python3 scripts/course_items.py [--json] [--slots FILE] FILE...
Exit: 0 parsed cleanly, 1 grammar errors (on stderr), 2 usage.
"""

import argparse
import json
import re
import sys
from pathlib import PurePosixPath

# Public vocabulary for consumers (firsttry, pins.py, the reference lint).
KINDS = "WCPHXTA"
LANGS = ("d", "v", "py", "dv")
P_FORMATS = ("value", "obligation", "error", "verdict")
CARD_PREFIXES = ("write", "recognise", "diverge")
CHECKED_KINDS = "PHXT"   # machine-checked: cited by the concept matrix, no orphans
CITABLE_KINDS = "PHXTA"  # may be cited by concept_items
USES_KINDS = "HXT"       # may carry uses: (and pair:)
STATES = ("unfilled", "filled-disabled", "enabled")

SLUG_RE = r"[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*"
SLUG = re.compile(SLUG_RE)
ITEM_ID_RE = r"([RQ]\d\d)\.([WCPHXTA])([1-9]\d*)(dv|py|d|v)"
ITEM_ID = re.compile(ITEM_ID_RE)


def marker_re(leader):
    lead = re.escape(leader)
    return re.compile(
        rf"\s*{lead} item: {ITEM_ID_RE}(?: S(1[0-3]|[1-9]))?"
        rf"(?: (value|obligation|error|verdict|(?:write|recognise):{SLUG_RE}"
        rf"|diverge:[a-z0-9]+(?:-[a-z0-9]+)*))?"
        rf"(?: min=([1-9]\d*))?")


def file_lang(rel):
    """'d', 'v' or 'py' for an item-bearing file name, else None."""
    name = PurePosixPath(rel).name
    if name.endswith((".dfy", ".dfy.specimen")):
        return "d"
    if name.endswith((".rs", ".rs.specimen")):
        return "v"
    if name.endswith(".py"):
        return "py"
    return None


def covered_langs(lang):
    """The single languages an item language covers: dv covers d and v."""
    return ("d", "v") if lang == "dv" else (lang,)


# --- source scanning (comments and strings blanked; line numbers kept) -------

CHAR_LIT = re.compile(r"'(?:\\(?:x[0-9a-fA-F]{2}|u\{?[0-9a-fA-F]{1,6}\}?|U[0-9a-fA-F]{8}|.)|[^\\'\n])'")


def scan_c(text):
    """Dafny/Rust source with comments, strings and char literals blanked to
    spaces (newlines kept). Block comments nest, as in both languages.
    Returns (code_lines, starts_in_code): starts_in_code[i] is True when line
    i + 1 begins outside any block comment or string."""
    out, starts = [], [True]
    i, n, depth, state, raw_hashes = 0, len(text), 0, "code", 0
    while i < n:
        c = text[i]
        if c == "\n":
            out.append(c)
            if state == "line":
                state = "code"
            starts.append(state == "code")
            i += 1
        elif state == "code":
            if text.startswith("//", i):
                state = "line"
                out.append("  ")
                i += 2
            elif text.startswith("/*", i):
                state, depth = "block", 1
                out.append("  ")
                i += 2
            elif text.startswith('@"', i):          # Dafny verbatim string
                state = "verbatim"
                out.append("  ")
                i += 2
            elif (m := re.match(r'r(#*)"', text[i:i + 260])) and (
                    i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")):
                state, raw_hashes = "raw", len(m.group(1))   # Rust raw string
                out.append(" " * len(m.group(0)))
                i += len(m.group(0))
            elif c == '"':
                state = "string"
                out.append(" ")
                i += 1
            elif c == "'" and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] in "_'")) \
                    and CHAR_LIT.match(text, i):
                lit = CHAR_LIT.match(text, i).group(0)
                out.append(" " * len(lit))
                i += len(lit)
            else:
                out.append(c)
                i += 1
        elif state == "line":
            out.append(" ")
            i += 1
        elif state == "block":
            if text.startswith("/*", i):
                depth += 1
                out.append("  ")
                i += 2
            elif text.startswith("*/", i):
                depth -= 1
                out.append("  ")
                i += 2
                if depth == 0:
                    state = "code"
            else:
                out.append(" ")
                i += 1
        elif state == "verbatim":
            if text.startswith('""', i):
                out.append("  ")
                i += 2
            else:
                if c == '"':
                    state = "code"
                out.append(" ")
                i += 1
        elif state == "raw":
            close = '"' + "#" * raw_hashes
            if text.startswith(close, i):
                state = "code"
                out.append(" " * len(close))
                i += len(close)
            else:
                out.append(" ")
                i += 1
        else:  # string
            if c == "\\" and i + 1 < n and text[i + 1] != "\n":
                out.append("  ")
                i += 2
                continue
            if c == '"':
                state = "code"
            out.append(" ")
            i += 1
    code = "".join(out).split("\n")
    return code, starts[:len(code)]


PY_STRING = re.compile(r"(?i)(?:[rbuf]|rb|br|fr|rf)?('''|\"\"\"|'|\")")


def scan_py(text):
    """Python source with comments and strings blanked (newlines kept).
    Returns (code_lines, starts_in_code) as scan_c does."""
    out, starts = [], [True]
    i, n, state, quote = 0, len(text), "code", ""
    while i < n:
        c = text[i]
        if c == "\n":
            out.append(c)
            if state == "line":
                state = "code"
            elif state == "string" and len(quote) == 1:
                state = "code"   # an unterminated one-line string ends here
            starts.append(state == "code")
            i += 1
        elif state == "code":
            if c == "#":
                state = "line"
                out.append(" ")
                i += 1
                continue
            m = PY_STRING.match(text, i)
            if m and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")):
                state, quote = "string", m.group(1)
                out.append(" " * len(m.group(0)))
                i += len(m.group(0))
            else:
                out.append(c)
                i += 1
        elif state == "line":
            out.append(" ")
            i += 1
        else:  # string
            if c == "\\" and i + 1 < n:
                out.append(" " if text[i + 1] == "\n" else "  ")
                if text[i + 1] == "\n":
                    i += 1
                    continue
                i += 2
                continue
            if text.startswith(quote, i):
                state = "code"
                out.append(" " * len(quote))
                i += len(quote)
            else:
                out.append(" ")
                i += 1
    code = "".join(out).split("\n")
    return code, starts[:len(code)]


def scan(rel, text):
    return scan_py(text) if file_lang(rel) == "py" else scan_c(text)


# --- slot files ----------------------------------------------------------------

SLOT_FILE_LINE = re.compile(r"\s*([WCPHXTA][1-9]\d*(?:dv|py|d|v))\s*=\s*(.*?)\s*$")


def parse_slot_file(rel, text):
    """{local id: (line, state)} from a module's slots/<ID>.slots, plus errors.
    `X = ???` is unfilled, `X = "<answer>"` filled; `#` starts a comment."""
    out, errs = {}, []
    for ln, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = SLOT_FILE_LINE.fullmatch(line)
        if not m:
            errs.append(f"{rel}:{ln}: malformed slot line (expected `<K><n><lang> = ???` or "
                        "`<K><n><lang> = \"<answer>\"`)")
            continue
        local, value = m.groups()
        if local in out:
            errs.append(f"{rel}:{ln}: slot {local} listed twice (first at line {out[local][0]})")
            continue
        if value == "???":
            out[local] = (ln, "unfilled")
        elif re.fullmatch(r'"(?:[^"\\]|\\.)*"', value) and value != '""':
            out[local] = (ln, "filled")
        else:
            errs.append(f"{rel}:{ln}: slot {local}: the value is `???` or a non-empty "
                        "double-quoted answer")
    return out, errs


# --- items ---------------------------------------------------------------------

def parse_items(rel, text, slot_file=None):
    """The item blocks of one file. `slot_file` is (rel, {local: (line, state)})
    from parse_slot_file, used for verdict slots. Returns (items, errors);
    each item is a dict with the keys of the --items JSON record."""
    lang = file_lang(rel)
    if lang is None:
        return [], []
    leader = "#" if lang == "py" else "//"
    lead = re.escape(leader)
    marker = marker_re(leader)
    marker_like = re.compile(rf"\s*{lead}\s*item\s*:")
    header_like = re.compile(rf"\s*{lead}\s*(uses|need|pair)\s*:")
    header_line = re.compile(rf"\s*{lead} (uses|need|pair): (\S.*?)\s*$")
    slot_line = re.compile(rf"\s*{lead} SLOT: ?(.*)")
    did_line = re.compile(rf"{lead} did: (\S.*?)\s*$")

    raw = text.split("\n")
    code, starts = scan(rel, text)
    items, errs = [], []
    cur, header, depth = None, False, 0

    def close(last):
        while last > cur["line_start"] and not raw[last - 1].strip():
            last -= 1
        cur["line_end"] = last
        items.append(cur)

    for i, line in enumerate(raw):
        ln = i + 1
        line_depth = depth
        if leader == "//":
            depth += code[i].count("{") - code[i].count("}")
        if not starts[i]:
            header = False  # inside a comment or string: part of the block, never a marker
            continue
        if cur and leader == "//":
            # the container the marker sits in closes on this line, or a new header starts
            low, d = line_depth, line_depth
            for ch in code[i]:
                d += 1 if ch == "{" else -1 if ch == "}" else 0
                low = min(low, d)
            if low < cur["_depth"] or line.startswith("/*!"):
                close(ln - 1)
                cur = None
        if marker_like.match(line):
            if cur:
                close(ln - 1)
            cur, header = None, False
            m = marker.fullmatch(line.rstrip())
            if not m:
                errs.append(f"{rel}:{ln}: malformed item marker — expected `{leader} item: "
                            "<ID>.<K><n><lang> [S<k>] [format] [min=<m>]` (K in WCPHXTA, lang "
                            "d|v|py|dv, n and k unpadded)")
                continue
            mod, kind, n, ilang, strand, fmt, low_ = m.groups()
            iid = f"{mod}.{kind}{n}{ilang}"
            cur = {"id": iid, "kind": kind, "n": int(n), "lang": ilang,
                   "strand": f"S{strand}" if strand else None, "format": fmt,
                   "min": int(low_) if low_ else None, "uses": [], "need": [], "pair": None,
                   "did": [], "file": rel, "line_start": ln, "line_end": ln, "slots": [],
                   "_depth": line_depth}
            header = True
            errs += item_grammar_errors(cur, rel, ln, lang)
            continue
        if header_like.match(line):
            what = header_like.match(line).group(1)
            m = header_line.fullmatch(line)
            if cur is None:
                errs.append(f"{rel}:{ln}: `{leader} {what}:` outside an item block")
            elif not header:
                errs.append(f"{rel}:{ln}: `{leader} {what}:` must directly follow its item "
                            f"marker ({cur['id']})")
            elif not m or m.group(1) != what:
                errs.append(f"{rel}:{ln}: malformed `{leader} {what}:` line")
            elif what in ("uses", "pair") and cur["kind"] not in USES_KINDS:
                errs.append(f"{rel}:{ln}: `{leader} {what}:` on a {cur['kind']} item "
                            f"({cur['id']}); only H, X and T items carry {what}:")
            elif what == "need" and cur["kind"] != "X":
                errs.append(f"{rel}:{ln}: `{leader} need:` on a {cur['kind']} item "
                            f"({cur['id']}); only X items carry need:")
            elif what == "uses":
                if cur["lang"] == "py":
                    errs.append(f"{rel}:{ln}: `{leader} uses:` on a Python item ({cur['id']}); "
                                "uses: names verifier constructs")
                for tok in (t.strip() for t in m.group(2).split(",")):
                    if not SLUG.fullmatch(tok):
                        errs.append(f"{rel}:{ln}: `uses:` token {tok!r} is not a construct "
                                    "slug (kebab-case, '/' between alternatives)")
                    elif tok not in cur["uses"]:
                        cur["uses"].append(tok)
            elif what == "pair":
                pm = ITEM_ID.fullmatch(m.group(2))
                if cur["pair"] is not None:
                    errs.append(f"{rel}:{ln}: {cur['id']} has a second `pair:` line")
                elif not pm:
                    errs.append(f"{rel}:{ln}: `pair:` names no item id ({m.group(2)!r})")
                elif cur["lang"] not in ("d", "v") or pm.group(4) not in ("d", "v") \
                        or pm.group(4) == cur["lang"]:
                    errs.append(f"{rel}:{ln}: `pair:` joins a d item and a v item "
                                f"({cur['id']} → {m.group(2)})")
                elif pm.group(2) != cur["kind"] or int(pm.group(3)) != cur["n"] \
                        or pm.group(1) != cur["id"][:3]:
                    errs.append(f"{rel}:{ln}: {cur['id']} pairs with {m.group(2)}; a pair shares "
                                "module, kind and number and differs in language only")
                else:
                    cur["pair"] = m.group(2)
            else:
                cur["need"].append(m.group(2))
            continue
        header = False
        if cur is not None and (dm := did_line.search(line)):
            cur["did"].append(dm.group(1))
        if cur is None and slot_line.match(line):
            errs.append(f"{rel}:{ln}: `{leader} SLOT:` outside an item block")
    if cur:
        close(len(raw))
    for it in items:
        it["slots"] = block_slots(it, raw, code, starts, leader, slot_file)
        del it["_depth"]
        if it["min"] is not None and it["min"] > len(it["slots"]):
            errs.append(f"{rel}:{it['line_start']}: {it['id']} has min={it['min']} but "
                        f"{len(it['slots'])} slot(s)")
    return items, errs


def item_grammar_errors(it, rel, ln, file_language):
    """Kind/format/language rules that need no registry."""
    errs = []
    at = f"{rel}:{ln}"
    kind, fmt, lang, iid = it["kind"], it["format"] or "", it["lang"], it["id"]
    if file_language == "py" and lang != "py":
        errs.append(f"{at}: {iid} is a {lang} item in a Python file")
    elif file_language != "py" and lang == "py":
        errs.append(f"{at}: {iid} is a py item in a verifier file")
    elif file_language in ("d", "v") and lang not in (file_language, "dv"):
        errs.append(f"{at}: {iid} is a {lang} item in a "
                    f"{'Dafny' if file_language == 'd' else 'Verus'} file")
    if iid[0] == "Q" and it["strand"] is None:
        errs.append(f"{at}: Q item {iid} needs its strand (S1–S13)")
    elif iid[0] == "R" and it["strand"] is not None:
        errs.append(f"{at}: R item {iid} carries a strand; the R track has none")
    if kind == "P" and fmt not in P_FORMATS:
        errs.append(f"{at}: P item {iid} needs a format (" + " | ".join(P_FORMATS) + ")")
    elif kind == "C" and fmt.partition(":")[0] not in CARD_PREFIXES:
        errs.append(f"{at}: card {iid} needs write:<slug>, recognise:<slug> or diverge:<slug>")
    elif kind in "XT" and fmt not in ("", "verdict"):
        errs.append(f"{at}: {kind} item {iid} may carry only the verdict format")
    elif kind in "WHA" and fmt:
        errs.append(f"{at}: {kind} item {iid} carries no format")
    if it["min"] is not None and kind != "X":
        errs.append(f"{at}: min= is for multi-slot X items only ({iid})")
    return errs


VALUE_LIVE = {
    "d": re.compile(r"\s*expect\s"),
    "v": re.compile(r"\s*(?:assert_eq!|assert)\s*\("),
    "py": re.compile(r"\s*assert\s"),
}


def block_slots(item, raw, code, starts, leader, slot_file):
    """Slots of one block, each {format, file, line, state}."""
    fmt, lead = item["format"], re.escape(leader)
    local = item["id"].split(".", 1)[1]
    slot_re = re.compile(rf"\s*{lead} SLOT: ?(.*)")
    live = {"obligation": re.compile(rf"\s*{lead}\s*FAILS\b"),
            "error": re.compile(rf"\s*{lead}\s*EXPECT\s+@")}
    check_live = re.compile(rf"\s*{lead}\s*CHECK\s+{re.escape(local)}\s*$")
    check_slot = re.compile(rf"\s*{lead} SLOT: ?CHECK\b")
    slots, enabled_check = [], False
    value_live = VALUE_LIVE[file_lang(item["file"])]
    for ln in range(item["line_start"] + 1, item["line_end"] + 1):
        r, c, s = raw[ln - 1], code[ln - 1], starts[ln - 1]
        if not s:
            continue
        if fmt == "verdict" and check_slot.match(r):
            continue  # the enable switch, not a slot
        if fmt == "verdict" and check_live.match(r):
            enabled_check = True
            continue
        if m := slot_re.match(r):
            state = "unfilled" if "???" in m.group(1) else "filled-disabled"
            slots.append({"format": fmt, "file": item["file"], "line": ln, "state": state})
        elif fmt == "value" and c.strip() and value_live.match(c):
            slots.append({"format": fmt, "file": item["file"], "line": ln, "state": "enabled"})
        elif fmt in live and live[fmt].match(r):
            slots.append({"format": fmt, "file": item["file"], "line": ln, "state": "enabled"})
    if fmt == "verdict" and slot_file is not None:
        srel, table = slot_file
        if local in table:
            line, st = table[local]
            state = "unfilled" if st == "unfilled" else (
                "enabled" if enabled_check else "filled-disabled")
            slots.append({"format": fmt, "file": srel, "line": line, "state": state})
    return slots


def public(items):
    """Items as the JSON records consumers read (a stable key order)."""
    keys = ("id", "kind", "n", "lang", "strand", "format", "min", "uses", "need", "pair",
            "did", "file", "line_start", "line_end", "slots")
    return [{k: it[k] for k in keys} for it in items]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Parse item markers in course files.")
    ap.add_argument("files", nargs="+", metavar="FILE")
    ap.add_argument("--json", action="store_true", help="print one JSON array")
    ap.add_argument("--slots", metavar="FILE", help="the module's slots/<ID>.slots file")
    args = ap.parse_args(argv)
    errs, items = [], []
    slot_file = None
    if args.slots:
        try:
            with open(args.slots, encoding="utf-8") as f:
                table, e = parse_slot_file(args.slots, f.read())
        except OSError as e:
            print(f"course_items: cannot read {args.slots}: {e.strerror}", file=sys.stderr)
            return 2
        errs += e
        slot_file = (args.slots, table)
    for path in args.files:
        if file_lang(path) is None:
            print(f"course_items: {path}: not an item-bearing file (.dfy, .rs, .py, "
                  "*.specimen)", file=sys.stderr)
            return 2
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            print(f"course_items: cannot read {path}: {e.strerror}", file=sys.stderr)
            return 2
        got, e = parse_items(path, text, slot_file)
        items += got
        errs += e
    for e in errs:
        print(e, file=sys.stderr)
    if args.json:
        print(json.dumps(public(items), ensure_ascii=False))
    else:
        for it in items:
            slots = " ".join(f"{s['state']}@{s['line']}" for s in it["slots"])
            print(f"{it['id']}\t{it['strand'] or '-'}\t{it['format'] or '-'}\t"
                  f"{it['file']}:{it['line_start']}-{it['line_end']}"
                  + (f"\tuses: {', '.join(it['uses'])}" if it["uses"] else "")
                  + (f"\tpair: {it['pair']}" if it["pair"] else "")
                  + (f"\tslots: {slots}" if slots else ""))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
