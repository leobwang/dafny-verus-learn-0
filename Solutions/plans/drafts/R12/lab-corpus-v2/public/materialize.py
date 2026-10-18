"""Lab alpha public slice: materialize one upstream verified answer into an R12 hint-site
form (WALK.md, check C1). Author-side; standard library plus the course's own parsers.

  materialize.py dafnybench|humaneval-verus TASK TASK_ID OUTDIR
      writes OUTDIR/<TASK_ID>.dfy|.rs (the form) and OUTDIR/hints.json (the reference hint
      data, in site order) and OUTDIR/materialize.json (the record: target, sites, kept
      annotations and why, flags); exit 0, or exit 1 with {"c1": reason} on stdout.

Dafny (dafnybench): the removed lines are the answer-vs-task-form diff (only deletions are
allowed); each removed `invariant` / `assert ...;` group inside the target declaration becomes
one site on one line; any other removed line, and any annotation the frozen hint grammar cannot
express, is restored (kept as provided text). Verus (humaneval-verus, answers only): inside the
target exec fn, every `invariant` clause and every plain `assert(..);` becomes a site; the rest
is the answer's. A Verus clause holding `#[trigger]` stays in the skeleton (WALK.md amendment 1).
"""
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path[:0] = [str(ROOT / "tests/wrappers"), str(ROOT / "harness"), str(ROOT / "harness/r")]
import test_tools_common as C  # noqa: E402
from fvh_r import engine as E  # noqa: E402

core = C.load_script("vcheck")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
BAD_CHARS = set('{}#"\'') | {"\n", "\r", "\x00"}


# words never needed in a hint that a scan of signatures picks up
NOISE = {"assert", "proof", "mut", "by", "pub", "open", "closed", "spec", "exec", "ghost", "tracked",
         "modifies", "reads", "returns", "trigger", "auto", "verifier", "self", "Self"}


class Reject(Exception):
    pass


def vocabulary(texts, hints):
    words = set()
    for t in list(texts) + list(hints):
        words |= set(IDENT.findall(t))
    return sorted(w for w in words if w not in E._FORBIDDEN and w not in E._KEYWORDS)


def expressible(hint, vocab):
    if not hint or len(hint) > 8192 or any(ch in BAD_CHARS for ch in hint):
        return False
    if any(x in hint for x in ("//", "/*", "*/", ";")):
        return False
    try:
        E._check_expression(hint, vocab)
        return True
    except ValueError:
        return False


def mask(text):
    """The text with comments and string literals blanked (same length, newlines kept)."""
    out, i, n = list(text), 0, len(text)
    while i < n:
        if text.startswith("//", i):
            j = text.find("\n", i); j = n if j < 0 else j
            for k in range(i, j): out[k] = " "
            i = j; continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2); j = n if j < 0 else j + 2
            for k in range(i, j):
                if out[k] != "\n": out[k] = " "
            i = j; continue
        if text[i] == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            for k in range(i + 1, min(j, n)):
                if out[k] != "\n": out[k] = " "
            i = j + 1; continue
        i += 1
    return "".join(out)


LOCAL = re.compile(r"\b(?:let\s+(?:ghost\s+|tracked\s+)?(?:mut\s+)?|var\s+|for\s+)([A-Za-z_][A-Za-z0-9_]*)")


def scope_words(signature, body):
    """Parameter, type and local-binding names of the target (not every keyword of its body)."""
    sig = set(IDENT.findall(mask(signature)))
    loc = set(LOCAL.findall(mask(body)))
    return " ".join(sorted(sig | loc))


def strip_comment(line):
    # a trailing // comment (no string literals are allowed in hints anyway)
    i = line.find("//")
    return line if i < 0 else line[:i].rstrip()


# --------------------------------------------------------------------------------- Dafny

def dafny(task):
    ans = (ROOT / "bench/public/dafnybench/answers" / task).read_text()
    frm = (ROOT / "bench/public/dafnybench/tasks" / task).read_text()
    a, t = ans.split("\n"), frm.split("\n")
    sm = difflib.SequenceMatcher(a=a, b=t, autojunk=False)
    removed = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        if op != "delete":
            raise Reject(f"the task form is not the answer less whole lines ({op} at answer line {i1 + 1})")
        removed.extend(range(i1, i2))
    if not removed:
        raise Reject("the task form removes nothing")
    src = core.D.parse_source(ans, task)
    decls = [d for d in src.decls if d.body]

    def owner(i):  # 0-based line -> innermost declaration containing it
        ln = i + 1
        best = None
        for d in decls:
            s = d.line
            e = ans[:src.toks[d.body[1]].start].count("\n") + 1
            if s <= ln <= e and (best is None or s >= best[1]):
                best = (d, s, e)
        return best
    # group removed lines: an invariant/assert line plus its continuation lines
    groups, cur = [], None
    for i in removed:
        st = a[i].strip()
        if re.match(r"(invariant|assert)\b", st):
            cur = [i]
            groups.append(cur)
        elif cur is not None and i == cur[-1] + 1 and not re.match(r"(decreases|modifies|reads|requires|ensures)\b", st):
            cur.append(i)
        else:
            cur = None
            groups.append([i])  # another removed line: restored
    per_decl = {}
    for g in groups:
        o = owner(g[0])
        if o is None:
            continue
        if re.match(r"(invariant|assert)\b", a[g[0]].strip()):
            per_decl.setdefault(o[0].name, []).append(g)
    if not per_decl:
        raise Reject("no removed invariant or assert inside a declaration")
    target = max(per_decl, key=lambda n: (len(per_decl[n]), -min(g[0] for g in per_decl[n])))
    tdecl = next(d for d in decls if d.name == target)
    ts = tdecl.line
    te = ans[:src.toks[tdecl.body[1]].start].count("\n") + 1
    target_text = "\n".join(a[ts - 1:te])
    funcs = [d.name for d in src.decls if d.kind in ("function", "predicate", "ghost function", "ghost predicate") or "function" in d.kind or "predicate" in d.kind]
    cands = []
    for g in per_decl[target]:
        text = " ".join(strip_comment(a[i]).strip() for i in g)
        m = re.fullmatch(r"invariant\s+(.*)", text)
        kind = "inv"
        if not m:
            m = re.fullmatch(r"assert\s+(.*);", text)
            kind = "assert"
        hint = m.group(1).strip() if m else None
        cands.append((g, kind, hint))
    hints_all = [h for _, _, h in cands if h]
    btok = src.toks[tdecl.body[0]].start
    line_off = sum(len(x) + 1 for x in a[:ts - 1])
    sig_text = ans[line_off:btok]
    body_text = ans[btok:src.toks[tdecl.body[1]].end]
    vocab = [w for w in vocabulary([scope_words(sig_text, body_text)] + funcs, hints_all)
             if w not in NOISE]
    out = list(a)
    sites, hints, kept = [], [], []
    drop = set()
    for g, kind, hint in cands:
        if hint is None or "{:" in hint or " by " in f" {hint} " or not expressible(hint, vocab):
            kept.append({"line": g[0] + 1, "why": "not expressible in the frozen hint grammar",
                         "text": " ".join(a[i].strip() for i in g)})
            continue
        n = len(sites) + 1
        name = ("i" if kind == "inv" else "a") + str(n)
        indent = re.match(r"\s*", a[g[0]]).group(0)
        out[g[0]] = indent + (f"invariant /*R12_HINT:{name}*/ true" if kind == "inv"
                              else f"assert /*R12_HINT:{name}*/ true;")
        drop |= set(g[1:])
        sites.append({"name": name, "identifiers": vocab})
        hints.append(hint)
    restored = [i + 1 for i in removed if owner(i) is None or owner(i)[0].name != target]
    if not sites:
        raise Reject("no removed annotation of the target is expressible in the hint grammar")
    body = [x for k, x in enumerate(out) if k not in drop]
    return finish("dafny", task, ans, body, sites, hints, target, kept,
                  {"restored_outside_target_lines": restored, "target_kind": tdecl.kind,
                   "lemma_shaped": tdecl.kind in ("lemma",) or bool(re.search(r"seq<|string|decreases", target_text))})


# --------------------------------------------------------------------------------- Verus

def scan(text, i, stops):
    """Index of the first stop word or char at depth 0 from i (skipping comments/strings)."""
    depth, n = 0, len(text)
    while i < n:
        if text.startswith("//", i):
            i = text.find("\n", i)
            i = n if i < 0 else i
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        ch = text[i]
        if ch == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            i = j + 1
            continue
        if ch in "([{":
            if depth == 0 and ch in stops:
                return i
            depth += 1
        elif ch in ")]}":
            if depth == 0:
                return i
            depth -= 1
        elif depth == 0:
            if ch in stops:
                return i
            for w in stops:
                if len(w) > 1 and text.startswith(w, i) and not (text[i - 1:i].isalnum() or text[i - 1:i] == "_") \
                        and not (text[i + len(w):i + len(w) + 1].isalnum() or text[i + len(w):i + len(w) + 1] == "_"):
                    return i
        i += 1
    return n


def true_body(ans, mk, fn_at):
    """(start, end) of a verusfmt-formatted fn's body: the first depth-0 `{` after the fn
    keyword that opens its own line at the fn's indentation, or, with no contract clause,
    the first depth-0 `{`; end just past its matching `}`."""
    line0 = ans.rfind("\n", 0, fn_at) + 1
    ind = len(ans[line0:fn_at]) - len(ans[line0:fn_at].lstrip(" \t"))
    depth, i, n, clauses = 0, fn_at, len(mk), False
    while i < n:
        ch = mk[i]
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif depth == 0 and re.match(r"(requires|ensures|recommends|decreases|returns)\b", mk[i:i + 12]) \
                and not (mk[i - 1].isalnum() or mk[i - 1] == "_"):
            clauses = True
        elif ch == "{" and depth == 0:
            ls = mk.rfind("\n", 0, i) + 1
            own_line = mk[ls:i].strip() == "" and (i - ls) == ind
            if own_line or not clauses:
                d, j = 0, i
                while j < n:
                    if mk[j] == "{":
                        d += 1
                    elif mk[j] == "}":
                        d -= 1
                        if d == 0:
                            return i, j + 1
                    j += 1
                return None
            d, j = 0, i  # a block expression of the contract: skip it
            while j < n:
                if mk[j] == "{":
                    d += 1
                elif mk[j] == "}":
                    d -= 1
                    if d == 0:
                        break
                j += 1
            i = j
        i += 1
    return None


def verus(task):
    ans = (ROOT / "bench/public/humaneval-verus/answers" / task).read_text()
    src = core.V.vs.parse(ans)
    fns = [d for d in src.walk() if d.kind == "fn" and d.mode == "exec" and d.owner is None and d.body]
    spans = []
    mk = mask(ans)
    for d in fns:
        tok = next(k for k in range(d.start, d.body[0] + 1) if src.toks[k].text == "fn")
        tb = true_body(ans, mk, src.toks[tok].start)
        if tb is None:
            continue
        b0, b1 = tb
        body = mk[b0:b1]
        k = len(re.findall(r"\binvariant\b", body)) + len(re.findall(r"\bassert\s*\(", body))
        spans.append((k, -b0, d, b0, b1))
    spans = [s for s in spans if s[0] > 0]
    if not spans:
        raise Reject("no invariant or assert in an exec fn")
    _, _, tdecl, b0, b1 = max(spans)
    if (src.toks[tdecl.body[0]].start, src.toks[tdecl.body[1]].end) != (b0, b1):
        raise Reject("the course's Verus parser reads the target's body as another brace block "
                     "(a block expression in its contract); its source span would be wrong")
    tok = next(k for k in range(tdecl.start, tdecl.body[0]) if src.toks[k].text == "fn")
    fstart = src.toks[tok].start
    target_text = ans[fstart:b1]
    funcs = [d.name for d in src.walk() if d.kind == "fn" and d.mode == "spec"]
    edits = []  # (start, end, kind, hint_text, raw)
    # invariant clause lists
    for m in re.finditer(r"\b(invariant_except_break|invariant)\b", mk[b0:b1]):
        p = b0 + m.end()
        end = scan(ans, p, ("decreases", "ensures", "invariant", "invariant_except_break", "{"))
        seg_start = p
        q = p
        while q < end:
            c = scan(ans, q, (",",))
            c = min(c, end)
            raw = ans[q:c]
            if raw.strip():
                edits.append((q, c, "inv", (q, c)))
            q = c + 1
        del seg_start
    # plain asserts
    for m in re.finditer(r"\bassert\s*\(", mk[b0:b1]):
        p = b0 + m.start()
        if any(s <= p < e for s, e, _, _ in edits):
            continue
        open_ = b0 + m.end() - 1
        close = scan(ans, open_ + 1, ())
        after = ans[close + 1:close + 40].lstrip()
        if not after.startswith(";"):
            continue  # assert(..) by {..} stays
        semi = ans.index(";", close + 1)
        edits.append((p, semi + 1, "assert", (open_ + 1, close)))
    edits.sort()
    cands = []
    for s, e, kind, (hs, he) in edits:
        raw = mk[hs:he]  # comments blanked: a trailing comment is not part of the clause
        hint = " ".join(raw.split())
        cands.append((s, e, kind, hint, raw))
    vocab = [w for w in vocabulary([scope_words(ans[fstart:b0], ans[b0:b1])] + funcs,
                                   [c[3] for c in cands if not (set(c[3]) & BAD_CHARS) and "=~=" not in c[3]])
             if w not in NOISE]
    sites, hints, kept, pieces, last, triggers = [], [], [], [], 0, 0
    for s, e, kind, hint, raw in cands:
        if "#" in hint or "=~=" in hint or not expressible(hint, vocab):
            kept.append({"offset": s, "why": "not expressible in the frozen hint grammar", "text": " ".join(raw.split())[:300]})
            continue
        if "#[trigger]" in ans[s:e]:
            triggers += 1
        n = len(sites) + 1
        name = ("i" if kind == "inv" else "a") + str(n)
        line_start = ans.rfind("\n", 0, s) + 1
        indent = re.match(r"[ \t]*", ans[line_start:]).group(0)
        if kind == "inv":
            # the clause, on one line; a second site on a line moves to a line of its own
            lead = mk[s:e]  # comments blanked: a comment before the clause stays in the gap
            stripped = len(lead) - len(lead.lstrip())
            gap = ans[last:s + stripped]
            if sites and "\n" not in gap:
                gap = gap.rstrip(" \t") + "\n" + indent + "    "
            pieces.append(gap)
            pieces.append(f"/*R12_HINT:{name}*/ true")
            last = s + len(raw.rstrip())
        else:
            gap = ans[last:s]
            if sites and "\n" not in gap:
                gap = gap.rstrip(" \t") + "\n" + indent
            pieces.append(gap)
            pieces.append(f"assert(/*R12_HINT:{name}*/ true);")
            last = e
        sites.append({"name": name, "identifiers": vocab})
        hints.append(hint)
    pieces.append(ans[last:])
    if not sites:
        raise Reject("no annotation of the target is expressible in the hint grammar")
    body = "".join(pieces).split("\n")
    return finish("verus", task, ans, body, sites, hints, tdecl.name, kept,
                  {"dropped_triggers": triggers, "lemma_shaped": bool(re.search(r"Seq<|seq|String|str|decreases", target_text))})


# --------------------------------------------------------------------------------- common

def finish(lang, task, ans, body, sites, hints, target, kept, flags):
    set_ = "dafnybench" if lang == "dafny" else "humaneval-verus"
    lic = "Apache-2.0 (set licence; per-file upstream licence not recorded)" if lang == "dafny" else "MIT (set and HumanEval prompts)"
    header = [None, None, f"// R12 public task: {set_} {task} ({lic}); proof annotations moved into hint sites."]
    lines = header + body
    # one site per line check and the target span
    text_wo = "\n".join(lines[2:])
    for _ in range(2):
        hs = "// R12_HINT_SITES: " + json.dumps(sites, separators=(",", ":"))
        lines[0] = hs
        lines[1] = "// R12_SOURCE_SPANS: []"
        full = "\n".join(lines)
        if lang == "dafny":
            src = core.D.parse_source(full, task)
            d = src.decl(target)
            s, e = d.line, full[:src.toks[d.body[1]].start].count("\n") + 1
            sym = target
        else:
            src = core.V.vs.parse(full)
            d = next(x for x in src.walk() if x.kind == "fn" and x.name == target and x.owner is None)
            tok = next(k for k in range(d.start, d.body[0]) if src.toks[k].text == "fn")
            s = full[:src.toks[tok].start].count("\n") + 1
            e = full[:src.toks[d.body[1]].start].count("\n") + 1
            sym = target
        lines[1] = "// R12_SOURCE_SPANS: " + json.dumps([{"symbol": sym, "start": s, "end": e}], separators=(",", ":"))
    full = "\n".join(lines)
    task_obj, _ = E.source_task(full)  # validates one site per line etc.
    return full, hints, {"target": target, "sites": len(sites), "kept_annotations": kept, "flags": flags}


def main():
    set_, task, tid, outdir = sys.argv[1:5]
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    try:
        full, hints, rec = (dafny if set_ == "dafnybench" else verus)(task)
        task_obj, _ = E.source_task(full)
    except (Reject, ValueError, StopIteration, AttributeError) as e:
        print(json.dumps({"c1": f"{type(e).__name__}: {e}"}))
        return 1
    ext = ".dfy" if set_ == "dafnybench" else ".rs"
    (out / (tid + ext)).write_text(full)
    (out / "hints.json").write_text(json.dumps({"hints": hints}, indent=1) + "\n")
    (out / "materialize.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({"ok": True, "target": rec["target"], "sites": rec["sites"], "kept": len(rec["kept_annotations"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
