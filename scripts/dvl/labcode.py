"""dvl.labcode: the lab gate's code check on a Lab 2 card (the user's decision D27, 2026-10-14;
QPLAN §25.5-§25.6), and the code S1's mutant kill renders its mutants from.

A Lab 2 card (bench/local/q/lab2/, the local stratum; bench/local/q/lab2pub/, the public
strata) ships a prose task's executable code with no specification and an empty witness. Arms
S0 and S1 write the specification; they never change the code. What a delivery may add:

  every card    the target's `requires` and `ensures` (and its other signature clauses:
                Dafny `modifies`, `reads`, `decreases`; Verus `recommends`, `decreases`, …),
                one witness call (the witness's body is the delivery's), and declarations
                that are not executable code: definitions (Dafny functions and predicates the
                code does not call; Verus spec fns) and lemmas (Dafny lemmas, ghost methods;
                Verus proof fns), which the specification may use;
  a public card proof annotations too (D27): loop invariants and a loop's `decreases`
                (Dafny also a loop's `modifies`), assertions (with `by` blocks), `calc`,
                `reveal`, ghost variables and their updates, proof `forall` statements and
                lemma calls (Dafny); `assert`, `assert … by`, `proof { … }` blocks, proof
                macros, `let ghost`/`let tracked`, `reveal`, `broadcast use` and the loop
                clauses (Verus). The public tasks' code needs the upstream proof annotations
                before a specification as strong as the prose verifies (DV5e's lab2pub notes
                §7); the local cards' code needs none.

Never executable code: everything else must be the task form's, token for token (comments and
layout aside). `code_findings(task, delivery)` compares the two files' *code skeletons* (the
file's tokens with the allowed additions erased from both) and reports each declaration whose
code differs as a `lab-code-changed` finding; a local card's delivery that adds a proof
annotation gets a finding that says so. `scripts/vcheck --gate --lab-task <form> <delivery>`
applies it to every Lab 2 card after the lever check (`lab_gate`); `--lab-code own` waives it,
for an arm that writes its own code (the vericoding arm V). Which rule a task form takes comes
from its course path (CARD_RULES), which the verification container keeps at the end of the
staged path (`lab-task/<course path>`), read as given and then resolved against the working
directory; a file under another path whose bytes are a Lab 2 form's takes that form's rule, and
a path under a Lab 2 stratum's directory that names no card's form is `lab-code-unchecked`
(DV6 review); any other task form gets no code check.

S1's mutant source (D27): on a public card the mutant kill renders its mutants from the
*delivery's* annotated body (its invariants and assertions kept), since the shipped body does
not verify under any specification as strong as the prose; on a local card from the shipped
body (the delivery's, as the code is unchanged). `mutant_source(task, delivery)` returns the
body, the text before and after the target's declaration, and the rule.

Static and standard library only (Dafny through dvl.dafny's parser, Rust through
dvl.benchstrip's lexer). Messages name the declaration and never quote code."""

from __future__ import annotations

import re
from pathlib import Path

from dvl import benchstrip as B
from dvl import common

# The Lab 2 strata, by course directory: which additions a delivery may make.
CARD_RULES = {"bench/local/q/lab2": "spec", "bench/local/q/lab2pub": "annotations"}
RULES = ("spec", "annotations")
_CARD_PATH = re.compile(r"(?:^|/)(bench/local/q/[a-z0-9_-]+)/([a-z0-9][a-z0-9-]*)/tasks/"
                        r"([a-z0-9][a-z0-9-]*)\.(dfy|rs)$")
KIND = "lab-code-changed"


class CodeError(Exception):
    """A pair the code check cannot compare (a file it cannot read, no target)."""


_REPO = Path(__file__).resolve().parents[2]


def _path_rule(posix):
    m = _CARD_PATH.search(posix)
    if not m or m.group(2) != m.group(3):
        return None
    return CARD_RULES.get(m.group(1))


def _content_rule(task, repo=None):
    """The rule of the Lab 2 task form whose bytes the file holds (a copy of a form under
    another path), or None."""
    repo = Path(repo) if repo is not None else _REPO
    try:
        data = Path(task).read_bytes()
    except OSError:
        return None
    for stratum, rule in CARD_RULES.items():
        for q in sorted((repo / stratum).glob("*/tasks/*")):
            if q.suffix in (".dfy", ".rs") and q.is_file() and _path_rule(
                    q.relative_to(repo).as_posix()) == rule:
                try:
                    if q.read_bytes() == data:
                        return rule
                except OSError:
                    continue
    return None


def card_rule(task, repo=None):
    """The rule of a task form: "spec" (a local Lab 2 card), "annotations" (a public one), or
    None (not a Lab 2 card: no code check). Its course path decides, read as given and then
    resolved against the working directory (`tasks/<id>.dfy` from the card's directory); a
    file under another path whose bytes are a Lab 2 form's takes that form's rule (a scratch
    copy; DV6 review)."""
    rule = _path_rule(Path(task).as_posix())
    if rule is None:
        try:
            rule = _path_rule(Path(task).resolve().as_posix())
        except OSError:
            rule = None
    if rule is None:
        rule = _content_rule(task, repo)
    return rule


_LAB2_DIR = re.compile(r"(?:^|/)bench/local/q/lab2(?:pub)?/")


def _lab2_unmatched(task):
    """True when a path names a Lab 2 stratum's directory but no card's task form there."""
    try:
        full = Path(task).resolve().as_posix()
    except OSError:
        full = Path(task).as_posix()
    return bool(_LAB2_DIR.search(Path(task).as_posix()) or _LAB2_DIR.search(full))


def lang_of(path):
    s = str(path)
    return "dafny" if s.endswith(".dfy") else "verus" if s.endswith(".rs") else None


# --- Verus ------------------------------------------------------------------------------------

_V_SIG = B.LAB2_VERUS_SIG
_V_STMT = {"assert", "proof-macro", "proof-block", "ghost-let", "reveal", "broadcast-use"}


def _v_attrs_before(p, s, floor):
    """The first token of the `#[…]` attribute groups right before token s."""
    while s - 2 >= floor and B._is(p.toks[s - 1], "punct", "]"):
        o = next((a for a, b in p.m.items() if b == s - 1), None)
        if o is None or o - 1 < floor or not B._is(p.toks[o - 1], "punct", "#"):
            break
        s = o - 1
    return s


def _verus_parts(text):
    p = B._Plan(text)
    if not p.blocks:
        raise CodeError("no verus! block")
    for o, c in p.blocks:
        p.scan_items(o + 1, c)
    fns = B._verus_fns(p)
    execs = [f for f in fns if f[0] == "exec"]
    return p, fns, execs


def _v_target(execs):
    names = {f[1] for f in execs}
    wit = {f[1] for f in execs if f[1].endswith("_witness") and f[1][:-8] in names}
    targets = [f for f in execs if f[1] not in wit and f[1] + "_witness" in names]
    if len(targets) != 1:
        raise CodeError("no single target with its witness")
    return targets[0][1], targets[0][1] + "_witness"


def _verus_skeleton(text, annotations, target=None, witness=None):
    p, fns, execs = _verus_parts(text)
    if target is None:
        target, witness = _v_target(execs)
    n = len(p.toks)
    gone = [False] * n
    ann = [False] * n                 # a proof annotation inside exec code

    def drop(a, b, mask=gone):
        for x in range(max(a, 0), min(b, n - 1) + 1):
            mask[x] = True
    for f in fns:
        mode, name, start, kw, body, end, is_decl = f
        if mode in ("spec", "proof"):
            drop(_v_attrs_before(p, start, 0), end)
            continue
        for a, e in B._sig_clause_spans(p, kw, body, _V_SIG):
            drop(a, e)
        if name == witness and not is_decl:
            drop(body + 1, end - 1)
    for it in p.proof_items:
        drop(_v_attrs_before(p, it.start, 0), it.end)
    for s, e in p.mod_uses:
        drop(s, e)
    # spec and proof consts
    for k, t in enumerate(p.toks):
        if B._is(t, "ident", "const"):
            s = p.modifiers_start(k, 0)
            if {x.text for x in p.toks[s:k]} & {"spec", "proof"}:
                e = p.stmt_end(k, n, False)
                drop(_v_attrs_before(p, s, 0), e)
    for s, e, kind in p.spans:
        if kind in _V_STMT or kind == "loop-clauses":
            drop(s, e, ann)
        elif kind == "broadcast-group":
            drop(s, e)
    # every clause of a loop header, `decreases` included, is an annotation
    for f in execs:
        _, _, _, kw, body, end, is_decl = f
        if is_decl:
            continue
        k = body + 1
        while k < end:
            t = p.toks[k]
            if t.kind == "ident" and t.text in ("while", "loop", "for"):
                lb = p.loop_body(k, end)
                if lb is not None:
                    c = p.first_clause(k + 1, lb)
                    if c is not None:
                        drop(c, lb - 1, ann)
            k += 1
    scope = ["(file)"] * n
    for f in fns:
        for x in range(f[2], f[5] + 1):
            scope[x] = f[1]
    return _groups(p.toks, gone, ann, scope, annotations)


# --- Dafny ------------------------------------------------------------------------------------

_D_HEADER = {"requires", "ensures", "modifies", "reads", "decreases"}


def _d_last(x):
    return x.by_method[1] if x.by_method else x.body[1] if x.body else x.header_end - 1


def _d_target(src):
    methods = [d for d in src.decls if d.kind == "method" and "ghost" not in d.modifiers]
    names = {d.name for d in methods}

    def wit(nm):
        return nm + "Witness" if (nm + "Witness") in names else nm + "_witness"
    targets = [d for d in methods if wit(d.name) in names]
    if len(targets) != 1:
        raise CodeError("no single target with its witness")
    return targets[0].name, wit(targets[0].name)


def _dafny_skeleton(text, annotations, target=None, witness=None):
    from dvl import dafny as D
    try:
        src = D.parse_source(text)
    except Exception as e:  # noqa: BLE001
        raise CodeError(f"the Dafny parser refused the file: {e}") from None
    if target is None:
        target, witness = _d_target(src)
    toks = src.toks
    n = len(toks)
    gone = [False] * n
    ann = [False] * n

    def drop(a, b, mask=gone):
        for x in range(max(a, 0), min(b, n - 1) + 1):
            mask[x] = True
    lemmas = [x for x in src.decls if x.kind in ("lemma", "colemma") or
              (x.kind == "method" and "ghost" in x.modifiers)]
    lemma_names = {x.name for x in lemmas}
    for x in lemmas:
        drop(x.start, _d_last(x))
    methods = [x for x in src.decls if x.kind in ("method", "constructor") and x not in lemmas]
    for d in methods:
        starts = sorted(k for _, k in d.clauses if d.start <= k < d.header_end)
        for i, k in enumerate(starts):
            e = (starts[i + 1] if i + 1 < len(starts) else d.header_end) - 1
            if toks[k].text in _D_HEADER:
                drop(k, e)
        if d.body and d.name == witness:
            drop(d.body[0] + 1, d.body[1] - 1)
        elif d.body:
            _d_annotations(toks, d.body[0] + 1, d.body[1], lemma_names, ann,
                           code_methods={x.name for x in methods},
                           code_names=_d_param_names(toks, d))
    # functions and predicates the code does not reach are definitions, not code
    defs = {x.name: x for x in src.decls if x.kind in ("function", "predicate")}
    in_def = [False] * n
    for x in defs.values():
        for y in range(x.start, _d_last(x) + 1):
            in_def[y] = True
    code_named = {t.text for j, t in enumerate(toks) if t.kind == "id" and not gone[j]
                  and not ann[j] and not in_def[j]}
    graph = {nm: {toks[y].text for y in range(x.start, _d_last(x) + 1)
                  if toks[y].kind == "id" and toks[y].text != nm} & set(defs)
             for nm, x in defs.items()}
    reached = B._closure(graph, [nm for nm in code_named if nm in defs])
    for nm, x in defs.items():
        if nm not in reached:
            drop(x.start, _d_last(x))
    scope = ["(file)"] * n
    for x in sorted(src.decls, key=lambda d: d.start):
        for y in range(x.start, _d_last(x) + 1):
            scope[y] = x.name
    return _groups(toks, gone, ann, scope, annotations)


def _d_close_paren(toks, j):
    """The index of the bracket closing the one at j (same depth), or len(toks) - 1."""
    pairs = {"(": ")", "[": "]", "{": "}", "<": ">"}
    o, c, d = toks[j].text, pairs[toks[j].text], 0
    for x in range(j, len(toks)):
        if toks[x].text == o:
            d += 1
        elif toks[x].text == c:
            d -= 1
            if d == 0:
                return x
    return len(toks) - 1


def _d_param_names(toks, d):
    """The non-ghost parameter and out-parameter names of a method or constructor header."""
    out = set()
    k = d.kw + 1
    groups = []
    while k < d.header_end:
        t = toks[k]
        if t.text in _D_HEADER:
            break
        if t.text == "(":
            e = _d_close_paren(toks, k)
            groups.append((k, e))
            k = e + 1
            continue
        k += 1
    for a, e in groups:
        depth, ghost = 0, False
        for x in range(a + 1, e):
            t = toks[x]
            if t.text in ("(", "[", "{", "<"):
                depth += 1
            elif t.text in (")", "]", "}", ">"):
                depth -= 1
            elif depth == 0 and t.text == ",":
                ghost = False
            elif depth == 0 and t.text == "ghost":
                ghost = True
            elif (depth == 0 and t.kind == "id" and x + 1 < e and toks[x + 1].text == ":"
                  and not ghost):
                out.add(t.text)
    return out


def _d_local_names(toks, a, c):
    """The names a body [a, c) declares with a non-ghost `var` (and a `for` loop's index)."""
    out = set()
    for k in range(a, c):
        t = toks[k]
        if t.kind == "id" and t.text == "var" and not (k > 0 and toks[k - 1].text == "ghost"):
            j = k + 1
            while j < c and toks[j].text not in (":=", ";", ":|"):
                if toks[j].kind == "id" and toks[j - 1].text in ("var", ","):
                    out.add(toks[j].text)
                j += 1
        elif t.kind == "id" and t.text == "for" and k + 1 < c and toks[k + 1].kind == "id":
            out.add(toks[k + 1].text)
    return out


def _d_runs_code(toks, a, e, code_methods):
    """True when tokens [a, e] call a non-ghost method or constructor or allocate (`new`):
    a ghost variable's right-hand side that does is executable code (DV6 review)."""
    for x in range(a, e + 1):
        t = toks[x]
        if t.kind == "id" and t.text == "new":
            return True
        if (t.kind == "id" and t.text in code_methods and x + 1 <= e
                and toks[x + 1].text in ("(", "<")):
            return True
    return False


def _d_annotations(toks, a, c, lemma_names, ann, code_methods=frozenset(), code_names=frozenset()):
    """Mark the proof annotations of a Dafny body [a, c) in `ann`. `code_methods` are the
    file's non-ghost methods and constructors, `code_names` the enclosing method's non-ghost
    parameters, out-parameters and locals: a ghost variable that shares a name with one, or
    whose right-hand side calls one (or allocates), is code, never an annotation, so the
    comparison sees it (fail-closed; DV6 review: `ghost var g := M(a);` runs M, and a ghost
    variable that shadows an out-parameter makes a later `r := …` look like a ghost update)."""
    ghosts = set()
    code_names = set(code_names) | _d_local_names(toks, a, c)
    lemma_ok = set(lemma_names) - set(code_methods)
    stmt_at = None                     # the token after a `label L:` starts a statement
    k = a
    while k < c:
        t = toks[k]
        prev = toks[k - 1].text if k > 0 else "{"
        at_stmt = prev in B._D_STMT_PREV or k == stmt_at
        nxt = toks[k + 1] if k + 1 < c else None
        if t.kind == "id" and at_stmt:
            by_block = False
            kind = None
            if (t.text == "label" and nxt is not None and nxt.kind == "id" and k + 2 < c
                    and toks[k + 2].text == ":"):
                for x in range(k, k + 3):
                    ann[x] = True
                stmt_at = k + 3
                k += 3
                continue
            if t.text in ("assert", "reveal"):
                kind = t.text
            elif t.text == "calc":
                kind, by_block = "calc", True
            elif t.text == "ghost" and nxt is not None and nxt.text in ("var", "const"):
                names = set()
                j = k + 2
                while j < c and toks[j].text not in (":=", ";", ":|"):
                    if toks[j].kind == "id" and toks[j - 1].text in ("var", "const", ","):
                        names.add(toks[j].text)
                    j += 1
                e = B._d_stmt_end(toks, k, c, False)
                if not (names & code_names) and not _d_runs_code(toks, j, e, code_methods):
                    kind = "ghost-var"
                    ghosts |= names
            elif t.text == "forall":
                body = B._d_loop_body(toks, k, c)
                if body is not None and any(toks[x].text == "ensures" for x in range(k, body)):
                    kind, by_block = "forall-proof", True
            elif t.kind == "id" and nxt is not None and (t.text in lemma_ok or nxt.text == "."):
                # a lemma call, bare or qualified (`M.L(x);`, `_default.L(x);`): its last
                # name segment is a lemma the file declares and no non-ghost method shares
                j = k
                while (j + 2 < c and toks[j + 1].text == "." and toks[j + 2].kind == "id"):
                    j += 2
                if (toks[j].text in lemma_ok and j + 1 < c
                        and toks[j + 1].text in ("(", "<")):
                    kind = "lemma-call"
            if (kind is None and t.text in ghosts and t.text not in code_names
                    and nxt is not None and nxt.text == ":="):
                e = B._d_stmt_end(toks, k, c, False)
                if not _d_runs_code(toks, k + 2, e, code_methods):
                    kind = "ghost-update"
            if kind:
                e = B._d_stmt_end(toks, k, c, by_block)
                for x in range(k, e + 1):
                    ann[x] = True
                k = e + 1
                continue
        if t.kind == "id" and t.text in ("while", "for"):
            body = B._d_loop_body(toks, k, c)
            if body is not None:
                marks = [x for x in range(k + 1, body) if toks[x].kind == "id"
                         and toks[x].text in B._D_LOOP_CLAUSES and B._depth0(toks, k + 1, x)]
                if marks:
                    for x in range(marks[0], body):
                        ann[x] = True
                k = body + 1
                continue
        k += 1


# --- the comparison ---------------------------------------------------------------------------

def _groups(toks, gone, ann, scope, annotations):
    """[(scope, (token texts))] of the kept tokens, one group per run of one scope; with
    `annotations` the annotation tokens are erased too."""
    out = []
    for k, t in enumerate(toks):
        if gone[k] or (annotations and ann[k]):
            continue
        if out and out[-1][0] == scope[k]:
            out[-1][1].append(t.text)
        else:
            out.append((scope[k], [t.text]))
    return [(s, tuple(x)) for s, x in out]


def skeleton(text, lang, *, annotations, target=None, witness=None):
    """The code skeleton of a Lab 2 file (module docstring): [(declaration, tokens)]."""
    if lang == "verus":
        return _verus_skeleton(text, annotations, target, witness)
    if lang == "dafny":
        return _dafny_skeleton(text, annotations, target, witness)
    raise CodeError(f"a Lab 2 card is Dafny or Verus, not {lang}")


def _targets(text, lang):
    if lang == "verus":
        return _v_target(_verus_parts(text)[2])
    from dvl import dafny as D
    try:
        return _d_target(D.parse_source(text))
    except CodeError:
        raise
    except Exception as e:  # noqa: BLE001
        raise CodeError(f"the Dafny parser refused the file: {e}") from None


def _diff_scopes(a, b):
    """The declarations whose code differs between two skeletons, in order."""
    da, db = {}, {}
    for s, t in a:
        da.setdefault(s, []).append(t)
    for s, t in b:
        db.setdefault(s, []).append(t)
    order = [s for s, _ in a] + [s for s, _ in b]
    seen, out = set(), []
    for s in order:
        if s in seen:
            continue
        seen.add(s)
        if da.get(s) != db.get(s):
            out.append(s)
    if not out and a != b:
        out = ["(file)"]                       # the same groups in another order
    return out


def code_findings(task, delivery, rule=None, *, ttext=None, dtext=None):
    """[Finding] of a delivery against its Lab 2 task form (module docstring). `rule`
    defaults to the task form's (card_rule); no rule, no finding. A pair the check cannot
    compare is one `lab-code-unchecked` finding, never a pass."""
    rule = card_rule(task) if rule is None else rule
    dl = str(delivery)
    if rule is None:
        if _lab2_unmatched(task):
            # under a Lab 2 stratum's directory but no card's form: fail-closed (DV6 review)
            return [common.Finding(dl, 0, "lab-code-unchecked",
                                   "the task form is under a Lab 2 stratum's directory but is "
                                   "no card's task form (bench/local/q/lab2*/<card>/tasks/"
                                   "<card>.dfy|rs), so the code check cannot pick its rule")]
        return []
    if rule not in RULES:
        raise ValueError(f"rule {rule!r} is not one of {', '.join(RULES)}")
    try:
        lang = lang_of(task)
        if lang is None or lang_of(delivery) != lang:
            raise CodeError("the delivery is not one file of the task form's language")
        ttext = Path(task).read_text(encoding="utf-8") if ttext is None else ttext
        dtext = Path(delivery).read_text(encoding="utf-8") if dtext is None else dtext
        target, witness = _targets(ttext, lang)
        want = skeleton(ttext, lang, annotations=rule == "annotations", target=target,
                        witness=witness)
        have = skeleton(dtext, lang, annotations=rule == "annotations", target=target,
                        witness=witness)
    except (CodeError, B.StripError, OSError, UnicodeDecodeError) as e:
        return [common.Finding(dl, 0, "lab-code-unchecked",
                               f"the code check could not compare the delivery with its task "
                               f"form: {e}")]
    bad = _diff_scopes(want, have)
    if not bad:
        return []
    if rule == "spec":
        loose_want = skeleton(ttext, lang, annotations=True, target=target, witness=witness)
        loose_have = skeleton(dtext, lang, annotations=True, target=target, witness=witness)
        if not _diff_scopes(loose_want, loose_have):
            return [common.Finding(dl, 0, KIND,
                                   f"the delivery adds proof annotations to {', '.join(bad)}: a "
                                   f"local Lab 2 card's delivery adds only its specification and "
                                   f"one witness call (proof annotations are a public card's, "
                                   f"the user's decision D27)")]
    what = ("its specification, one witness call, proof annotations and definitions"
            if rule == "annotations" else "its specification, one witness call and definitions")
    return [common.Finding(dl, 0, KIND,
                           f"the delivery changes the task form's executable code in "
                           f"{', '.join(bad)}: a Lab 2 delivery adds only {what}, never "
                           f"executable code (the user's decision D27)")]


def mutant_source(task, delivery_text, rule=None, *, task_text=None):
    """S1's mutant source on a Lab 2 card (D27): {"rule", "name", "body", "header",
    "footer"}: the target's body is the delivery's on a public card (its proof annotations
    kept) and the task form's on a local one; the header and footer (the text before and
    after the target's declaration) are the delivery's, whose definitions and lemmas its
    specification may use. Raises CodeError when the target cannot be found."""
    rule = card_rule(task) if rule is None else rule
    if rule not in RULES:
        raise CodeError(f"{task} is not a Lab 2 card")
    lang = lang_of(task)
    ttext = Path(task).read_text(encoding="utf-8") if task_text is None else task_text
    target, _ = _targets(ttext, lang)
    d_body, d_head, d_foot = _split(delivery_text, lang, target)
    body = d_body if rule == "annotations" else _split(ttext, lang, target)[0]
    return {"rule": rule, "name": target, "body": body, "header": d_head, "footer": d_foot}


def code_mutant(task, delivery_text, mutant_body, rule=None, *, task_text=None):
    """True when a mutant of S1's mutant source changes executable code: the delivery with
    the target's body replaced by `mutant_body` has another code skeleton (proof annotations
    erased) than the delivery itself. A mutant that changes only an invariant, an assertion
    or another proof annotation tests no specification (it fails on its own annotation,
    whatever the ensures says), so S1's kill rate can leave it out before any run (the
    DV6 review's option (d) of the lab2 lane's decision 1; reference-free: it reads the
    delivery and its task form only). Raises CodeError when the target cannot be found."""
    src = mutant_source(task, delivery_text, rule, task_text=task_text)
    lang = lang_of(task)
    ttext = Path(task).read_text(encoding="utf-8") if task_text is None else task_text
    target, witness = _targets(ttext, lang)
    base = src["header"] + delivery_text[len(src["header"]):]
    i = base.find(src["body"], len(src["header"])) if src["rule"] == "annotations" else -1
    if src["rule"] == "annotations":
        if i < 0:
            raise CodeError("the target's body is not found in the delivery")
        unmutated = base
        mutated = base[:i] + mutant_body + base[i + len(src["body"]):]
    else:
        # a local card: the body is the task form's; compare within the task form
        tb, th, _ = _split(ttext, lang, target)
        j = ttext.find(tb, len(th))
        unmutated, mutated = ttext, ttext[:j] + mutant_body + ttext[j + len(tb):]
    a = skeleton(unmutated, lang, annotations=True, target=target, witness=witness)
    b = skeleton(mutated, lang, annotations=True, target=target, witness=witness)
    return a != b


def _split(text, lang, name):
    """(body, header, footer) of the target declaration: the text between its braces, the text
    before the declaration and the text after it."""
    if lang == "verus":
        p, fns, _ = _verus_parts(text)
        f = next((f for f in fns if f[1] == name and f[0] == "exec" and not f[6]), None)
        if f is None:
            raise CodeError(f"no exec fn {name} with a body")
        start = _v_attrs_before(p, f[2], 0)
        return (text[p.toks[f[4]].end:p.toks[f[5]].start], text[:p.toks[start].start],
                text[p.toks[f[5]].end:])
    from dvl import dafny as D
    src = D.parse_source(text)
    d = next((x for x in src.decls if x.name == name and x.kind == "method" and x.body), None)
    if d is None:
        raise CodeError(f"no method {name} with a body")
    t = src.toks
    return (text[t[d.body[0]].end:t[d.body[1]].start], text[:t[d.start].start],
            text[t[d.body[1]].end:])


def without_declaration(text, lang, name):
    """Remove an exec declaration and its attached Rust documentation.

    Rust doc comments are attributes requiring an item. Keeping a removed
    witness's documentation at the end of verus! makes every probe fail to
    parse. Ordinary surrounding comments and all other declarations remain.
    """
    _, head, foot = _split(text, lang, name)
    if lang == "verus":
        doc = re.compile(r"(?:^|\n)[ \t]*(?:///[^\n]*|/\*\*(?:(?!\*/).)*\*/)[ \t\n]*$", re.S)
        while True:
            clean = doc.sub("\n", head)
            if clean == head:
                break
            head = clean
    return head + "\n" + foot
