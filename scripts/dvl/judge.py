"""dvl.judge: the host half of the grader container's judging mode (DV4-PLAN §5.9,
QPLAN §30 Q49, §25.5-§25.6, §19.0's prose item). Standard library only; it
never reads hidden truth and never runs a container.

A *candidate* is one delivered statement to be judged against a sealed
reference in the grader container: a prose item's declaration in a learner
file (Q13.H3v, Q15.H3d-H5v, Q17.H3d), or a Lab 2 arm's returned task file (a
card of bench/local/q/lab2/). This module reads the candidate's own file (the
learner's or the run's text, never a reference tree) and extracts, for the
container:

  - the declaration's name, parameters and results (types as written,
    whitespace-normalized), and its `requires` and `ensures` clauses as written
    (Dafny: one entry per clause; Verus: one entry per clause keyword, the whole
    comma-separated list);
  - a *context*: the file with every executable and proof declaration removed
    (Dafny methods, lemmas, constructors and iterators; Verus exec, proof and
    axiom fns, assume_specification, broadcast use/group items and `mod x;`
    declarations), so that only definitions remain (modules and imports,
    datatypes, types, constants, functions, predicates, spec fns, structs),
    split at the candidate's position into `header` and `footer`. Verus doc
    comments become plain comments, so a removed item leaves no dangling doc
    comment. The grader renders its lemmas between the two;
  - for a card, the card's shipped task form (the course's file) and whether
    the candidate's signature is the task form's (`signature_ok`).

A candidate's given definitions must be the shipped ones: `candidates()` refuses
a prose candidate whose file changes a statement its module's freeze pins
(`specfreeze --check`'s rule for that file) and a card candidate whose context
changes a statement of its task form's context or whose levers differ from the
task form's (the lab gate's lever check).

`build_judge(root, lab, candidates, ...)` returns the raw verify manifest of
one judging run: the module's given chain, project files, tools and pins
read-only, every card's task form editable (the grader writes its lemma files
over it and restores it, as `validate` does), the candidates as one inline
file `judge/candidates.json`, the [truth] table and the one command
`truthcheck judge <LAB>`. A judging run holds one language (a verification
container is sized for its language).

Messages name only candidate ids, items, cards and paths: never statement
text."""

from __future__ import annotations

import json
import os
import re
import secrets
import tomllib
from pathlib import Path

from dvl import dafny as D
from dvl import sandbox as S
from dvl import verus_spec as vs

CANDIDATES = "judge/candidates.json"      # the inline candidates file, under /work
CAND_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,95}")
ITEM_ID = re.compile(r"[QR]\d\d\.[A-Z]\d+[a-z]+")
CARD_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
ITEM_LINE = re.compile(r"^\s*//\s*item:\s*([QR]\d\d\.[A-Z0-9a-z]+)\b")
PROSE_LINE = re.compile(r"^\s*//\s*prose:\s*([A-Za-z_][A-Za-z0-9_]*)\s*$")
MAX_CANDIDATES = 64
D_REMOVE = {"lemma", "method", "constructor", "iterator"}
V_REMOVE_KINDS = {"assume_specification", "broadcast_use", "broadcast_group"}
V_STOP_KWS = {"requires", "ensures"}


class JudgeInputError(ValueError):
    """A candidate cannot be judged as given (a fixed message, no statement text)."""


def _ws(s):
    return " ".join(s.split())


def _strip_commas(s):
    s = s.strip()
    while s.endswith(","):
        s = s[:-1].rstrip()
    return s


def _cut(text, spans, at):
    """`text` with the character spans removed; `at` (the candidate's span start)
    mapped into the result: (header, footer)."""
    out, pos, cut = [], 0, None
    for a, b in sorted(spans):
        if a < pos:
            continue
        if a == at:
            cut = sum(len(x) for x in out) + (a - pos)
        out.append(text[pos:a])
        pos = b
    out.append(text[pos:])
    trimmed = "".join(out)
    if cut is None:
        raise JudgeInputError("the candidate's declaration could not be located")
    header, footer = trimmed[:cut], trimmed[cut:]
    if not header.endswith("\n"):
        header += "\n"
    return header, footer


# --- Dafny ---------------------------------------------------------------------------------------

def _d_group(toks, i):
    """(close index) of the parenthesized group opening at token i."""
    depth = 0
    for j in range(i, len(toks)):
        if toks[j].text in ("(", "[", "{"):
            depth += 1
        elif toks[j].text in (")", "]", "}"):
            depth -= 1
            if depth == 0:
                return j
    raise JudgeInputError("an unbalanced parameter list")


def _d_formals(text, toks, a, b):
    """[(name, type)] of the formals between tokens a ('(') and b (')')."""
    out, start, depth = [], a + 1, 0
    for j in range(a + 1, b + 1):
        x = toks[j].text
        if x in ("(", "[", "{", "<"):
            depth += 1
        elif x in (")", "]", "}", ">") and j < b:
            depth -= 1
        if j == b or (x == "," and depth == 0):
            part = [k for k in range(start, j)]
            start = j + 1
            if not part:
                continue
            words = [k for k in part if toks[k].text not in ("ghost", "nameonly", "older")]
            colon = next((k for k in words if toks[k].text == ":"), None)
            if colon is None or colon == words[0]:
                raise JudgeInputError("a formal parameter without a name and a type")
            name = toks[words[0]].text
            ty = _ws(text[toks[colon + 1].start:toks[part[-1]].end])
            out.append([name, ty])
    return out


def dafny_candidate(text, name, path="<candidate>"):
    try:
        src = D.parse_source(text, path)
    except Exception:  # noqa: BLE001 — a file the parser cannot read is not judged
        raise JudgeInputError("the candidate file does not parse") from None
    toks = src.toks
    found = [d for d in src.decls if d.name == name and d.kind in ("method", "lemma", "function",
                                                                    "predicate")]
    if len(found) != 1:
        raise JudgeInputError(f"the file declares {len(found)} method, lemma, function or "
                              f"predicate named {name}, not one")
    d = found[0]
    i = d.kw + 1
    while i < d.header_end and toks[i].text != "(":
        i += 1
    if i >= d.header_end:
        raise JudgeInputError(f"{name} has no parameter list")
    close = _d_group(toks, i)
    params = _d_formals(text, toks, i, close)
    results = []
    k = close + 1
    if k < d.header_end and toks[k].text == "returns" and toks[k + 1].text == "(":
        rc = _d_group(toks, k + 1)
        results = _d_formals(text, toks, k + 1, rc)
    starts = sorted(k for _, k in d.clauses if d.start <= k < d.header_end)
    req, ens = [], []
    for n, k in enumerate(starts):
        kw = toks[k].text
        end = starts[n + 1] if n + 1 < len(starts) else d.header_end
        a = k + 1
        while a < end and toks[a].text == "{" and a + 1 < end and toks[a + 1].text == ":":
            a = _d_group(toks, a) + 1                  # a clause's leading attribute
        if a >= end:
            continue
        clause = text[toks[a].start:toks[end - 1].end].strip()
        if kw == "requires":
            req.append(clause)
        elif kw == "ensures":
            ens.append(clause)
    spans = []
    for x in src.decls:
        if x.kind in D_REMOVE or x is d:
            last = x.by_method[1] if x.by_method else x.body[1] if x.body else x.header_end - 1
            spans.append((toks[x.start].start, toks[last].end))
    header, footer = _cut(text, spans, toks[d.start].start)
    return {"lang": "dafny", "name": name, "kind": d.kind, "params": params, "results": results,
            "requires": req, "ensures": ens, "header": header, "footer": footer}


# --- Verus ---------------------------------------------------------------------------------------

def _v_formals(src, a, b):
    """[(name, type)] of the formals between tokens a ('(') and b (')')."""
    toks, text = src.toks, src.text
    out, start, depth = [], a + 1, 0
    for j in range(a + 1, b + 1):
        x = toks[j].text
        if x in ("(", "[", "{"):
            depth += 1
        elif x in (")", "]", "}") and j < b:
            depth -= 1
        elif x == "<":
            depth += 1
        elif x in (">", ">>"):
            depth -= len(x)
        if j == b or (x == "," and depth == 0):
            part = list(range(start, j))
            start = j + 1
            if not part:
                continue
            words = [k for k in part if toks[k].text not in ("mut", "tracked", "ghost")]
            colon = next((k for k in words if toks[k].text == ":"), None)
            if colon is None or colon == words[0]:
                raise JudgeInputError("a parameter without a name and a type")
            out.append([toks[words[0]].text, _ws(text[toks[colon + 1].start:toks[part[-1]].end])])
    return out


def _undoc(text):
    """Doc comments as plain comments (same length), so that a removed item leaves
    no doc comment that documents nothing."""
    text = re.sub(r"(?m)^(\s*)//[/!]", lambda m: m.group(1) + "// ", text)
    return re.sub(r"/\*[*!](?!/)", "/* ", text)


def verus_candidate(text, name, path="<candidate>"):
    try:
        src = vs.parse(text)
    except Exception:  # noqa: BLE001
        raise JudgeInputError("the candidate file does not parse") from None
    toks = src.toks
    found = [it for it in src.walk() if it.kind == "fn" and it.name == name]
    if len(found) != 1:
        raise JudgeInputError(f"the file declares {len(found)} fn named {name}, not one")
    it = found[0]
    if it.params is None:
        raise JudgeInputError(f"{name} has no parameter list")
    params = _v_formals(src, *it.params)
    results = []
    if it.ret is not None:
        a, b = it.ret
        if b - a >= 2 and toks[a].text == "(" and src.pairs.get(a) == b - 1 and \
                any(toks[k].text == ":" for k in range(a + 1, b - 1)):
            results = _v_formals(src, a, b - 1)
            if len(results) != 1:
                raise JudgeInputError(f"{name}'s named result is not one name and type")
    req, ens = [], []
    for kw, a, b in it.clauses:
        if kw not in V_STOP_KWS or a >= b:
            continue
        clause = _strip_commas(text[toks[a].start:toks[b - 1].end])
        if clause:
            (req if kw == "requires" else ens).append(clause)
    spans = []
    for x in src.walk():
        drop = (x.kind == "fn" and x.mode in ("exec", "proof", "axiom")) or x is it \
            or x.kind in V_REMOVE_KINDS or (x.kind == "mod" and x.mod_decl)
        if drop:
            spans.append((toks[x.start].start, toks[x.end - 1].end))
    header, footer = _cut(text, spans, toks[it.start].start)
    return {"lang": "verus", "name": name, "kind": it.mode or "fn", "params": params,
            "results": results, "requires": req, "ensures": ens,
            "header": _undoc(header), "footer": _undoc(footer)}


def candidate(text, lang, name, path="<candidate>"):
    if lang == "dafny":
        return dafny_candidate(text, name, path)
    if lang == "verus":
        return verus_candidate(text, name, path)
    raise JudgeInputError(f"a candidate is Dafny or Verus, not {lang}")


# --- locating prose items and cards ---------------------------------------------------------------

def prose_item(root, item):
    """(course path of the learner file, declaration name) of a prose item: the file of
    its module's `exercises` that holds `// item: <item>` with a `// prose: <name>`
    marker before the next item marker."""
    if not ITEM_ID.fullmatch(item):
        raise JudgeInputError(f"{item!r} is not an item id")
    rec = S.registry_record(root, item.split(".")[0])
    for rel in rec.get("exercises", []):
        p = Path(root) / rel
        if not p.is_file() or p.suffix not in (".dfy", ".rs"):
            continue
        inside = False
        for line in p.read_text(encoding="utf-8").splitlines():
            m = ITEM_LINE.match(line)
            if m:
                inside = m.group(1) == item
                continue
            m = PROSE_LINE.match(line)
            if inside and m:
                return rel, m.group(1)
    raise JudgeInputError(f"{item} is not a prose item of {rec['id']}'s exercise files")


def lab_cards(root, lab):
    """{card: (lang, name, task form course path)} of the lab's local strata."""
    out = {}
    for st in sorted((Path(root) / "bench" / "local").glob("*/*/STRATUM.toml")):
        try:
            data = tomllib.loads(st.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("lab") != lab:
            continue
        for c in data.get("card", []):
            cid, lang, name = c.get("id"), c.get("lang"), c.get("name")
            ext = {"dafny": ".dfy", "verus": ".rs"}.get(lang)
            if isinstance(cid, str) and ext and isinstance(name, str):
                rel = (st.parent / cid / "tasks" / f"{cid}{ext}").relative_to(root).as_posix()
                out[cid] = (lang, name, rel)
    return out


def _specfreeze(root):
    """The specfreeze script as a module (its statement tables and the lab check)."""
    import importlib.machinery
    import importlib.util
    import sys
    if "specfreeze" not in sys.modules:
        loader = importlib.machinery.SourceFileLoader(
            "specfreeze", str(Path(root) / "scripts" / "specfreeze"))
        spec = importlib.util.spec_from_loader("specfreeze", loader)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["specfreeze"] = mod
        loader.exec_module(mod)
    return sys.modules["specfreeze"]


def freeze_ok(root, item, rel, text):
    """True when the candidate text keeps every statement its module's freeze pins for
    `rel` (checked on a copy laid over a scratch root's file list: the pin's rule)."""
    import shutil
    import tempfile
    sf = _specfreeze(root)
    mid = item.split(".")[0]
    pin = sf.load_freeze(sf.freeze_path(root, mid))
    entry = next((e for e in pin.get("file", []) if e.get("path") == rel), None)
    if entry is None:
        return True                   # an unfrozen file: nothing pinned
    tmp = Path(tempfile.mkdtemp(prefix="dvl-judge-freeze-"))
    try:
        f = tmp / Path(rel).name
        f.write_text(text, encoding="utf-8")
        lang = entry.get("lang") or sf.lang_of(rel)
        frames = set(entry.get("open_frames", [])) if lang == "d" else set()
        specs = set(entry.get("open_specs", [])) if lang in ("d", "v") else set()
        ob = set(entry.get("open_bodies", []))
        try:
            have, _, _ = sf.statements(f, lang, ob, frames, specs)
        except Exception:  # noqa: BLE001
            return False
        frozen = dict(entry.get("statements", {}))
        if any(have.get(s) != h for s, h in frozen.items()):
            alt, _, _ = sf.statements(f, lang, ob, frames, specs,
                                      text=sf.core.measure_free_text(text, lang, f))
            if any(have.get(s) != h and alt.get(s) != h for s, h in frozen.items()):
                # an open spec's clauses are the learner's: compare its kept clauses
                if not specs:
                    return False
                parts = sf.core.spec_parts(f, lang, symbols=specs, open_bodies=ob)
                for s, h in frozen.items():
                    if have.get(s) == h or alt.get(s) == h:
                        continue
                    if s not in specs or not sf.core.spec_clauses_kept(
                            entry.get("spec_clauses", {}).get(s, []),
                            parts.get(s, (None, {}))[1]):
                        return False
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def lab_ok(root, form_rel, text, lang, name):
    """True when a card candidate keeps its task form's definitions and levers: every
    statement of the task form's context (candidate(): the form with its methods,
    lemmas and executable fns removed) has the same statement hash in the
    candidate's context (which may add definitions of its own), and the lab gate's
    lever check (dvl.levers) finds no lever added or removed. The task's own
    declaration is the candidate's to specify, so the lab gate's statement freeze
    (`specfreeze --lab`) does not apply to it."""
    import shutil
    import tempfile
    from dvl import levers as LEV
    sf = _specfreeze(root)
    form = Path(root) / form_rel
    tmp = Path(tempfile.mkdtemp(prefix="dvl-judge-lab-"))
    try:
        mine = candidate(text, lang, name)
        theirs = candidate(form.read_text(encoding="utf-8"), lang, name)
        ext = ".dfy" if lang == "dafny" else ".rs"
        a, b, d = tmp / f"form{ext}", tmp / f"cand{ext}", tmp / f"delivery{ext}"
        a.write_text(theirs["header"] + theirs["footer"], encoding="utf-8")
        b.write_text(mine["header"] + mine["footer"], encoding="utf-8")
        d.write_text(text, encoding="utf-8")
        code = "d" if lang == "dafny" else "v"
        try:
            want, _, _ = sf.statements(a, code)
            have, _, _ = sf.statements(b, code)
            if any(have.get(sym) != h for sym, h in want.items()):
                return False
            return not list(LEV.lever_findings(form, d))
        except Exception:  # noqa: BLE001
            return False
    except JudgeInputError:
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- the judging run's inputs ------------------------------------------------------------------

def load_spec(path):
    """The candidates a judging run takes, from a TOML file ([[candidate]] tables) or
    a JSON file ({"candidates": [...]}): each an `id`, and an `item` (a prose item;
    `file` optional, default the learner file in the checkout) or a `card` with its
    `file` (a run's returned task file)."""
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    data = tomllib.loads(raw) if p.suffix == ".toml" else json.loads(raw)
    cands = data.get("candidate") if p.suffix == ".toml" else data.get("candidates")
    if not isinstance(cands, list) or not cands:
        raise JudgeInputError("the judging spec lists no candidate")
    if len(cands) > MAX_CANDIDATES:
        raise JudgeInputError(f"at most {MAX_CANDIDATES} candidates per judging run")
    base = p.parent
    out = []
    for c in cands:
        if not isinstance(c, dict) or set(c) - {"id", "item", "card", "file"}:
            raise JudgeInputError("a candidate has the keys id, item or card, and file")
        f = c.get("file")
        if f is not None:
            f = Path(f)
            f = f if f.is_absolute() else (base / f)
        out.append({"id": c.get("id"), "item": c.get("item"), "card": c.get("card"),
                    "file": f})
    return out


# A candidate the host does not send to the solver: its reason code (the grader maps it
# to the verdict `mismatch` with a fixed reason).
REFUSED = ("parse", "freeze", "task-form")


def _stub(cid, item, card, lang, name, code):
    return {"id": cid, "item": item, "card": card, "lang": lang, "name": name, "refused": code,
            "params": [], "results": [], "requires": [], "ensures": [], "header": "",
            "footer": "", "target": None, "signature_ok": None}


def candidates(root, lab, specs, *, check_freeze=True):
    """The candidates of `specs` (load_spec) as the container reads them, and their one
    language. A malformed spec raises JudgeInputError (or ManifestError for an unusable
    registry); a candidate whose file cannot be read as its declaration (`parse`), changes
    a statement its module's freeze pins (`freeze`) or changes its task form's definitions
    or levers (`task-form`) is sent as a stub with that `refused` code, never refused as a
    whole run (one bad delivery of a batch is one row)."""
    root = Path(root).resolve()
    if not re.fullmatch(r"[QR]\d\d", str(lab)):
        raise JudgeInputError(f"{lab!r} is not a lab id")
    cards = lab_cards(root, lab)
    out, seen = [], set()
    for c in specs:
        cid = c.get("id")
        if not isinstance(cid, str) or not CAND_ID.fullmatch(cid) or cid in seen:
            raise JudgeInputError(f"candidate id {cid!r}: a unique plain word")
        seen.add(cid)
        item, card, f = c.get("item"), c.get("card"), c.get("file")
        if (item is None) == (card is None):
            raise JudgeInputError(f"{cid}: names an item or a card, not both")
        if f is not None:
            f = Path(f).resolve()
            if _reference_path(f, root):
                raise JudgeInputError(f"{cid}: {f} is reference material, never a candidate")
            if not f.is_file():
                raise JudgeInputError(f"{cid}: {f} is not a file")
        if item is not None:
            if not isinstance(item, str) or not ITEM_ID.fullmatch(item) or \
                    item.split(".")[0] != lab:
                raise JudgeInputError(f"{cid}: {item!r} is not a prose item of {lab}")
            rel, name = prose_item(root, item)
            path = f or (root / rel)
            lang = S.lang_pool(rel)
            if S.lang_pool(Path(path).name) != lang:
                raise JudgeInputError(f"{cid}: the file is not a {lang} file")
            text = Path(path).read_text(encoding="utf-8")
            if check_freeze and not freeze_ok(root, item, rel, text):
                out.append(_stub(cid, item, None, lang, name, "freeze"))
                continue
            try:
                got = candidate(text, lang, name, str(path))
            except JudgeInputError:
                out.append(_stub(cid, item, None, lang, name, "parse"))
                continue
            got.update(id=cid, item=item, card=None, target=None, signature_ok=None)
        else:
            if not isinstance(card, str) or card not in cards:
                raise JudgeInputError(f"{cid}: {card!r} is not a card of {lab}'s local strata")
            if f is None:
                raise JudgeInputError(f"{cid}: a card candidate names its file")
            lang, name, form = cards[card]
            if S.lang_pool(Path(f).name) != lang:
                raise JudgeInputError(f"{cid}: the file is not a {lang} file")
            text = Path(f).read_text(encoding="utf-8")
            try:
                got = candidate(text, lang, name, str(f))
            except JudgeInputError:
                out.append(_stub(cid, None, card, lang, name, "parse"))
                continue
            if check_freeze and not lab_ok(root, form, text, lang, name):
                out.append(_stub(cid, None, card, lang, name, "task-form"))
                continue
            shipped = candidate((root / form).read_text(encoding="utf-8"), lang, name, form)
            got.update(id=cid, item=None, card=card, target=form,
                       signature_ok=(got["params"], got["results"]) ==
                       (shipped["params"], shipped["results"]))
        out.append(got)
    langs = {c["lang"] for c in out}
    if len(langs) != 1:
        raise JudgeInputError("a judging run judges one language's candidates (a verification "
                              "container is sized for its language): split the spec")
    return out, langs.pop()


def _reference_path(p, root):
    try:
        rel = Path(p).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return False
    return S.source_class(rel) is not None and rel.split("/")[0] in (
        "Solutions", "Hidden", "paper", "tests")


def build_judge(root, lab, cands, lang, *, mem_gb=None, run_id=None):
    """The raw manifest of one judging run of `lab` over `cands` (candidates())."""
    root = Path(root).resolve()
    pin = S.truth_pins(root).get(lab)
    if pin is None:
        raise S.ManifestError(f"no lab {lab!r} is pinned in {S.TRUTH_FILE}")
    rec = S.registry_record(root, lab)
    files, seen = [], set()
    forms = sorted({c["target"] for c in cands if c.get("target")})
    for f in forms:
        text = (root / f).read_text(encoding="utf-8")
        seen.add(f)
        files.append({"dst": f, "role": "editable", "text": text,
                      "sha256": S.sha256_bytes(text.encode("utf-8"))})
    blob = json.dumps({"schema": 1, "lab": lab, "lang": lang, "candidates": cands},
                      sort_keys=True)
    files.append({"dst": CANDIDATES, "role": "task", "text": blob,
                  "sha256": S.sha256_bytes(blob.encode("utf-8"))})
    seen.add(CANDIDATES)
    for src, role in S.readonly_inputs(root, rec, {lang}):
        if src == "verus/Cargo.toml" or src in seen:
            continue
        seen.add(src)
        data = S.read_source(root, S.Entry(src, src, role, "0" * 64))
        files.append({"src": src, "dst": src, "role": role, "sha256": S.sha256_bytes(data)})
    if lang == "verus":
        text = S.verus_workspace(root, rec)
        files.append({"dst": "verus/Cargo.toml", "role": "project", "text": text,
                      "sha256": S.sha256_bytes(text.encode("utf-8"))})
    lock = S.read_images_lock(root)
    image = next((k for k in lock if k.startswith("dvl-toolchain@")),
                 "dvl-toolchain@sha256:" + "0" * 64)
    raw = {"schema": S.SCHEMA, "run_id": run_id or f"j{os.getpid()}-{secrets.token_hex(4)}",
           "module": rec["id"], "kind": "verify", "image": image, "network": "none",
           "limits": {"wall_clock_s": 4 * 3600}, "file": files, "return": [],
           "command": [{"argv": [S.TRUTHCHECK, "judge", lab]}],
           "truth": {"lab": lab, "archive": pin["archive"], "sha256": pin["sha256"]}}
    if mem_gb is not None:
        bound = S.memory_bound_gb("verify", [lang])
        raw["limits"]["mem_gb"] = min(float(mem_gb), bound)
    return raw
