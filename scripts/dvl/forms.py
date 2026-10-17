"""dvl.forms — per-item construct forms (QPLAN §6 Q43; phase DV3b).

Pure text: no verifier, no registry. It never prints file content.

A checked use of a WRITE construct can sometimes be answered without the
construct at the pin (the Q07-Q09 author notes §0.2 list each such answer).
Such an item's block carries a form line, which states the construct the
answer region must use, in words in its prompt and mechanically here:

    // form: <rule>[, <rule>…]

anywhere inside an H, X or T block (after the marker's `uses:`/`need:`/`pair:`
lines, which must directly follow the marker), as a whole comment line. An
item may carry several form lines; its rules are their union. The closed
vocabulary (FORMS):

  bv-exec      Verus: the item's exec code holds no `*`, `/` or `%` (nor `*=`,
               `/=`, `%=`, nor a call of an integer multiplication, division,
               remainder or power method: ARITH_METHODS) outside `proof { }`
               blocks, `assert …` statements (with or without `by (…)`), ghost
               and tracked lets, loop invariants and spec clauses. The item's
               exec code is every exec fn whose header lies in the block, and
               every exec fn of the same file outside every H, X and T block
               that it calls (transitively, by name).
  no-nl        Verus: no `nonlinear_arith` (nor `integer_ring`, nor a
               `verifier::nonlinear` attribute) in the block's code or in a fn
               of the same file outside every H, X and T block that the
               block's fns call (transitively, by name).
  nl-steps:<k> Verus: at least k (k ≥ 1; the course uses 2) statements
               `assert(…) by (nonlinear_arith) requires …` in the block's
               answer region, each with its own `requires`.
  trigger      Dafny or Verus: an explicit trigger (`{:trigger …}`;
               `#[trigger]` or `#![trigger …]`) and a quantifier (`forall`,
               `exists`) in the block's answer region. A presence check: the
               rubric checks that the quantified fact carries the proof (the
               citation is marked `# nominal:`).
  no-call:<f>  Dafny: the block's answer region calls the function or method
               named f (an identifier f directly before `(`) only inside a
               specification statement or clause: a statement that begins
               with `assert`, `assume`, `calc`, `ghost` or `reveal`, or an
               `invariant`, `decreases`, `requires`, `ensures`, `reads` or
               `modifies` clause, or in the arguments of a bare call statement
               (`L(…);`: a lemma or method call, which assigns nothing). A
               compiled call of a compiled layer function (Q10.H1d's and
               Q13.H5d's `ToNat`) is the construct-free answer it rules out.
               Verus (DV5c, Q16): no fn of the block, and no fn of the same
               file outside every H, X and T block that they call
               (transitively, by name, as no-nl), calls f (an identifier f
               directly before `(`, a method call `x.f(` included); f is an
               exec fn, so every call counts. Q16.H3v's in-place schoolbook:
               a whole-number addition per row (layer L4's `big_add`, or
               `NatLike::plus`) is the answer it rules out.
  formula:<p>  Dafny: the body of the declaration named p, anywhere in the file
               (Q11.H7d's `Pre1` lives in another module than its block), is a
               formula over its parameters: no `var` binding, no `match`, and
               no call (an identifier directly before `(`), so it can hold
               comparisons, sums, products, Boolean connectives and
               `if … then … else` over the parameters, never a restatement of
               a given program. A targeted twin line `// cfree[p]: { … }`
               (cfree_targets) puts its body in p's place.
  loop-dir:[<x>:]up|down
               Dafny or Verus: the direction of the block's loops, read from
               the code. A `while` loop's counters are the identifiers of its
               guard that its body assigns; each assignment is a step up
               (Dafny `x := x + e`; Verus `x = x + e`, `x += e`), a step down
               (`x := x - e`; `x = x - e`, `x -= e`) or another assignment (any
               other right-hand side, a multiple assignment, a `var`/`let`
               that shadows it). A counter whose every assignment is a step
               up steps up, down likewise; a loop counts up when it has a
               counter that steps up and none that steps down (a guard
               identifier assigned another way, such as a found flag, is no
               counter), down likewise; a loop with counters both ways, or
               with none that only steps, has no direction. A Verus `loop`
               with no guard takes as its guard the identifiers of the
               conditions of its body's top-level `if <c> { … break … }`
               exits (DV5c gaps lane); a `loop` with no such exit has no
               direction. A `for`
               loop's direction is its range's: Dafny `to` up and `downto`
               down; Verus up unless its iterator calls `rev`. `loop-dir:up`:
               the answer region holds a loop and every loop there counts up;
               `loop-dir:<x>:up`: the region holds a loop whose guard (a `for`
               loop: whose variable) is x, and every such loop steps x up only
               (the prompt names x). `down` likewise. Each loop so checked
               must also read the sequence the same way: in its body, every
               index (`s[e]`, a slice bound `s[e..]`, `v@[e]`, the index
               arguments of `.subrange`, `.skip`, `.take`, `.update`, `.set`,
               `.index`) uses each identifier the body assigns only as an added
               term (`i`, `i + 1`, `j + i`, a cast of one), never subtracted
               (`|s| - i - 1`), inside a product, a call or a size, and never
               one that steps the other way; an identifier with one definition
               in the body is read through it (`let j = v.len() - i; v[j]`
               subtracts `i`). And at least one such loop must carry the
               computation: it reads an argument of the item at an index that
               adds one of its counters, and it assigns (or changes by a
               mutating call) an identifier the item's result is computed from
               (Dafny: its named results; Verus: its final expression and
               `return`s; both closed under the declarations and assignments
               directly in the body), so a loop beside a construct-free answer
               (a counter that only counts) is no loop of the form. Q13.H5d's
               loop from the low limb and Q14.H3v's from the top limb: the loop
               the other way, written with either counter, is the
               construct-free answer it rules out. A `loop` (Verus) has no
               guard and so no direction.
  no-adder     Verus (DV5c fix round, Q16.H3v): no exec fn of the same file
               outside every H, X and T block that the block's fns reach
               (transitively, by name, as no-nl) states, as one clause of its
               `ensures`, a whole-number sum: `A == B + C` or `B + C == A`, where
               each of A, B and C is one value term, `<e>.to_nat()` or
               `seq_to_nat(<e>)` (a cast of one included). A whole-number adder of
               the learner's own (layer L4's `big_add` copied under another name,
               which `no-call:big_add` cannot see) is the answer it rules out; a
               helper that adds one row of products into a vector in place states
               a product and passes.
  stable       Dafny or Verus: the block carries no resource attribute
               (Dafny `{:rlimit}`, `{:resource_limit}`, `{:timeLimit}`,
               `{:timeLimitMultiplier}`, `@ResourceLimit`, `@TimeLimit`,
               `@TimeLimitMultiplier`; Verus `verifier::rlimit`), and its
               declarations verify in every row of `scripts/vcheck
               --brittleness` (Verus: seeds 1-3; Dafny: seeds 1-3 under each
               bundled solver, `--solvers`; QPLAN §6 Q29, §17.5). The static
               half is here (resource_attr_lines); the caller runs the sweep.

The answer region of a block (the presence rules nl-steps and trigger read only
it) is the block without the header (signature and clauses: the frozen
statement) of the item's own declaration, the first lemma, method, function or
predicate of the block (Verus: the first fn), and without the declarations the
block shipped with besides it (`given`: given code, when the caller knows the
shipped block). The absence rules (bv-exec, no-nl) read the whole block.

Comments and strings never count: every check reads tokens. A twin block
(the reference) may carry `// cfree: { … }` lines (cfree_bodies), each a
construct-free answer the author measured, with `// cfree-decl:` lines
directly above a run of them for a helper the answers add (cfree_answers);
the empty-body gate requires each to fail verification or the item's forms
(firsttry --empty-body).
"""

from __future__ import annotations

import re

from . import verus_spec as vs

# rule -> the languages it applies to ('d' Dafny, 'v' Verus)
FORMS = {"bv-exec": "v", "no-nl": "v", "nl-steps": "v", "trigger": "dv", "stable": "dv",
         "no-call": "dv", "formula": "d", "loop-dir": "dv", "no-adder": "v"}
STATIC_RULES = ("bv-exec", "no-nl", "nl-steps", "trigger", "no-call", "formula", "loop-dir",
                "no-adder")
FORM_LINE = re.compile(r"^\s*(?://|#)\s*form\s*:\s*(.*?)\s*$")
CFREE_LINE = re.compile(r"^\s*//\s*cfree:\s?(.*)$")
CFREE_DECL_LINE = re.compile(r"^\s*//\s*cfree-decl:\s?(.*)$")
NL_STEPS = re.compile(r"nl-steps:([1-9]\d?)")
ARG_RULE = re.compile(r"(no-call|formula):([A-Za-z_][A-Za-z0-9_]*)")
CFREE_TARGET_LINE = re.compile(r"^\s*//\s*cfree\[([A-Za-z_][A-Za-z0-9_]*)\]:\s?(.*)$")
LOOP_DIR = re.compile(r"loop-dir:(?:([A-Za-z_][A-Za-z0-9_]*):)?(up|down)")
ARG_FORMS = ("nl-steps", "no-call", "formula", "loop-dir")

# Integer methods that multiply, divide, take a remainder or a power (bv-exec).
ARITH_METHODS = {
    "mul", "div", "rem", "pow", "div_euclid", "rem_euclid", "div_ceil", "div_floor",
    "checked_mul", "checked_div", "checked_rem", "checked_pow", "checked_div_euclid",
    "checked_rem_euclid", "wrapping_mul", "wrapping_div", "wrapping_rem", "wrapping_pow",
    "wrapping_div_euclid", "wrapping_rem_euclid", "saturating_mul", "saturating_div",
    "saturating_pow", "overflowing_mul", "overflowing_div", "overflowing_rem",
    "overflowing_pow", "overflowing_div_euclid", "overflowing_rem_euclid", "strict_mul",
    "strict_div", "strict_rem", "strict_pow", "unchecked_mul", "carrying_mul", "widening_mul",
    "mul_add", "unbounded_mul",
}
# Identifiers after which a `*` is a dereference, never a product.
_PREFIX_KWS = {"return", "let", "mut", "in", "if", "else", "match", "while", "for", "loop",
               "move", "ref", "break", "yield", "box", "await", "as"}
DAFNY_RESOURCE_ATTRS = {("{:", "rlimit"), ("{:", "resource_limit"), ("{:", "timeLimit"),
                        ("{:", "timeLimitMultiplier"), ("@", "ResourceLimit"),
                        ("@", "TimeLimit"), ("@", "TimeLimitMultiplier")}


# --- the marker line ------------------------------------------------------------------------

def rule_name(rule):
    """The vocabulary entry of a rule (`nl-steps:2` -> `nl-steps`), else None."""
    if rule in FORMS and rule not in ARG_FORMS:
        return rule
    if NL_STEPS.fullmatch(rule):
        return "nl-steps"
    m = ARG_RULE.fullmatch(rule)
    if m:
        return m.group(1)
    if LOOP_DIR.fullmatch(rule):
        return "loop-dir"
    return None


def loop_dir_arg(rule):
    """(variable or None, 'up' | 'down') of a `loop-dir:` rule, else None."""
    m = LOOP_DIR.fullmatch(rule)
    return (m.group(1), m.group(2)) if m else None


def rule_arg(rule):
    """The argument of a rule that takes one (`no-call:ToNat` -> `ToNat`)."""
    m = ARG_RULE.fullmatch(rule)
    return m.group(2) if m else None


def parse_rules(text):
    """(rules, problems) of one form line's text after `form:`."""
    rules, probs = [], []
    for tok in (x.strip() for x in text.split(",")):
        if not tok:
            probs.append("an empty rule")
        elif rule_name(tok) is None:
            probs.append(f"`{tok}` is not a form rule (" + ", ".join(
                {"nl-steps": "nl-steps:<k>", "no-call": "no-call:<f>",
                 "formula": "formula:<p>", "loop-dir": "loop-dir:[<x>:]up|down"}.get(r, r)
                for r in FORMS) + ")")
        elif tok not in rules:
            rules.append(tok)
    return rules, probs


def form_lines(raw_lines, lo, hi):
    """[(line, rules, problems)] of the form lines among raw lines lo..hi
    (1-based, inclusive)."""
    out = []
    for ln in range(lo, min(hi, len(raw_lines)) + 1):
        m = FORM_LINE.match(raw_lines[ln - 1])
        if m:
            rules, probs = parse_rules(m.group(1))
            out.append((ln, rules, probs))
    return out


def block_rules(raw_lines, lo, hi):
    """The rules of a block (the union of its form lines), in order."""
    out = []
    for _, rules, _ in form_lines(raw_lines, lo, hi):
        out += [r for r in rules if r not in out]
    return out


def lang_problems(rules, lang):
    """Rules that do not apply to the language ('d' or 'v')."""
    return [r for r in rules if rule_name(r) and lang not in FORMS[rule_name(r)]]


# --- `// cfree:` bodies (twin blocks) -------------------------------------------------------

def cfree_bodies(raw_lines, lo, hi):
    """(bodies, problems): the construct-free answers of a twin block's
    `// cfree:` lines. Consecutive lines are joined with newlines and split into
    their top-level `{ … }` blocks, so one line may hold one answer and an
    answer may run over several lines; text outside a block is a problem."""
    answers, probs = cfree_answers(raw_lines, lo, hi)
    return [b for b, _ in answers], probs


def cfree_answers(raw_lines, lo, hi):
    """(answers, problems): [(body, decls)] of a twin block's construct-free
    answers (cfree_bodies). A run of `// cfree-decl:` lines directly above a
    run of `// cfree:` lines gives declarations the answers of that run add
    to the file (a helper of the learner's own; firsttry puts them directly
    above the block, outside every H, X and T block): decls is their text
    (joined with newlines), or "" for none."""
    groups, cur, decl, pend = [], [], [], None
    probs = []
    for ln in range(lo, min(hi, len(raw_lines)) + 1):
        line = raw_lines[ln - 1]
        m, md = CFREE_LINE.match(line), CFREE_DECL_LINE.match(line)
        if m:
            if decl:
                pend, decl = "\n".join(decl), []
            cur.append(m.group(1))
            continue
        if cur:
            groups.append((cur, pend or ""))
            cur, pend = [], None
        if md:
            decl.append(md.group(1))
        elif decl:
            probs.append("`cfree-decl:` lines with no `cfree:` line directly below them")
            decl = []
    if cur:
        groups.append((cur, pend or ""))
    if decl:
        probs.append("`cfree-decl:` lines with no `cfree:` line directly below them")
    bodies = []
    for g, d in groups:
        text = "\n".join(g)
        depth, start, outside = 0, None, []
        for k, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    start = k
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth < 0:
                    probs.append("a `cfree:` body closes a brace it never opened")
                    depth = 0
                    continue
                if depth == 0:
                    bodies.append((text[start:k + 1].strip(), d))
            elif depth == 0 and not ch.isspace():
                outside.append(ch)
        if depth:
            probs.append("a `cfree:` body leaves a brace open")
        if outside:
            probs.append("a `cfree:` line holds text outside its `{ … }` body")
    return bodies, probs


def cfree_targets(raw_lines):
    """(answers, problems): the targeted construct-free answers of a twin file,
    [(target, body)] from its `// cfree[<target>]: { … }` lines, anywhere in the
    file (a `formula:<target>` form of some block owns them); consecutive lines
    with one target join, as for cfree_bodies."""
    groups, cur, tgt = [], [], None
    for line in raw_lines:
        m = CFREE_TARGET_LINE.match(line)
        if m and (not cur or m.group(1) == tgt):
            tgt = m.group(1)
            cur.append(m.group(2))
            continue
        if cur:
            groups.append((tgt, cur))
            cur, tgt = [], None
        if m:
            tgt, cur = m.group(1), [m.group(2)]
    if cur:
        groups.append((tgt, cur))
    out, probs = [], []
    for tgt, g in groups:
        bodies, p = cfree_bodies([f"// cfree: {x}" for x in g], 1, len(g))
        out += [(tgt, b) for b in bodies]
        probs += [f"cfree[{tgt}]: {x}" for x in p]
    return out, probs


# --- Verus ------------------------------------------------------------------------------

def _v_fns(src):
    return [it for it in src.walk() if it.kind == "fn" and it.in_verus]


def _in_any(line, blocks):
    return any(a <= line <= b for a, b in blocks)


def _v_calls(src, it):
    """Names the fn calls (an identifier before `(`, or before `::<…>(`)."""
    names, t = set(), src.toks
    a = it.body[0] if it.body else it.head
    b = it.body[1] if it.body else it.end
    for k in range(a, min(b, len(t) - 1)):
        if t[k].kind != "id":
            continue
        j = k + 1
        if j < len(t) and t[j].text == "::" and j + 1 < len(t) and t[j + 1].text == "<":
            depth, j = 0, j + 1
            while j < len(t):
                depth += 1 if t[j].text == "<" else -1 if t[j].text == ">" else \
                    -2 if t[j].text == ">>" else 0
                j += 1
                if depth <= 0:
                    break
        if j < len(t) and t[j].text == "(":
            names.add(t[k].text)
    return names


def _v_reach(src, block, blocks):
    """The fns of the block (header line in it) plus the helpers they reach:
    fns of the same file outside every H, X and T block, called by name,
    transitively."""
    fns = _v_fns(src)
    mine = [it for it in fns if block[0] <= src.line_of(it.head) <= block[1]]
    helpers = {}
    for it in fns:
        if it.name and not _in_any(src.line_of(it.head), blocks):
            helpers.setdefault(it.name, []).append(it)
    seen = {id(it) for it in mine}
    todo, out = list(mine), list(mine)
    while todo:
        it = todo.pop()
        for name in _v_calls(src, it):
            for h in helpers.get(name, []):
                if id(h) not in seen:
                    seen.add(id(h))
                    out.append(h)
                    todo.append(h)
    return mine, out


def _block_toks(src, block, skip=()):
    return [k for k, x in enumerate(src.toks) if block[0] <= x.line <= block[1]
            and not any(a <= k < b for a, b in skip)]


def v_given_ranges(src, block, given):
    """Token ranges outside a Verus block's answer region (see the module
    docstring): the header of the block's first fn, and every given fn."""
    fns = [it for it in _v_fns(src) if block[0] <= src.line_of(it.head) <= block[1]]
    out = []
    if fns:
        it = fns[0]
        out.append((it.start, it.body[0] if it.body else it.end))
        out += [(x.start, x.end) for x in fns[1:] if given and x.name in given]
    return out


def _span_of(src, it):
    return range(it.start, it.end)


def v_bv_exec(src, block, blocks):
    mine, reach = _v_reach(src, block, blocks)
    execs = [it for it in reach if it.mode == "exec" and it.body]
    if not [it for it in mine if it.mode == "exec"]:
        return False, "the block holds no exec fn"
    t = src.toks
    for it in execs:
        a, b = it.body[0] + 1, it.body[1]
        cut = vs.proof_spans(src, a, b, invariants=True, proof=True)
        for k in range(a, b):
            x = t[k]
            if any(s <= x.start < e for s, e in cut):
                continue
            prev = t[k - 1] if k > 0 else None
            if x.kind == "punct" and x.text in ("/", "%", "*=", "/=", "%="):
                return False, f"`{x.text}` in exec code at line {x.line}"
            if x.kind == "punct" and x.text == "*" and prev is not None and (
                    (prev.kind == "id" and prev.text not in _PREFIX_KWS) or prev.kind == "lit"
                    or (prev.kind == "punct" and prev.text in (")", "]"))):
                return False, f"`*` in exec code at line {x.line}"
            if x.kind == "id" and x.text in ARITH_METHODS and k + 1 < len(t) and \
                    t[k + 1].text == "(" and prev is not None and prev.text in (".", "::"):
                return False, f"a `{x.text}` call in exec code at line {x.line}"
    return True, ""


def _v_nl_at(src, k):
    x = src.toks[k]
    return x.kind == "id" and x.text in ("nonlinear_arith", "integer_ring")


def _v_attr_nonlinear(src, it):
    return any(re.search(r"\bnonlinear\b", vs.attr_text(src, a)) for a in it.attrs)


def v_no_nl(src, block, blocks):
    mine, reach = _v_reach(src, block, blocks)
    for k in _block_toks(src, block):
        if _v_nl_at(src, k):
            x = src.toks[k]
            return False, f"`{x.text}` at line {x.line}"
    for it in reach:
        if _v_attr_nonlinear(src, it):
            return False, f"a nonlinear attribute at line {src.line_of(it.start)}"
        if it in mine:
            continue
        for k in _span_of(src, it):
            if _v_nl_at(src, k):
                x = src.toks[k]
                return False, f"`{x.text}` at line {x.line}, in a helper the block calls"
    return True, ""


def v_no_call(src, block, blocks, name):
    """(ok, why) of `no-call:<name>` on a Verus block: no fn of the block, and
    no helper it reaches (_v_reach), calls name."""
    mine, reach = _v_reach(src, block, blocks)
    t = src.toks
    for it in reach:
        if name not in _v_calls(src, it):
            continue
        a = it.body[0] if it.body else it.head
        b = it.body[1] if it.body else it.end
        line = next((t[k].line for k in range(a, min(b, len(t) - 1))
                     if t[k].kind == "id" and t[k].text == name), src.line_of(it.head))
        return False, (f"a call of `{name}` at line {line}"
                       + ("" if it in mine else ", in a helper the block calls"))
    return True, ""


VALUE_FNS = ("to_nat", "seq_to_nat")


def _v_value_term(src, a, b):
    """Whether toks[a:b] is one value term: a postfix chain `<e>.to_nat()` or a
    call `seq_to_nat(<e>)` (never a product with one)."""
    t = src.toks
    if _base_of(t, src.pairs, b - 1, a) != a:
        return False
    if b - a >= 4 and t[b - 3].text == "to_nat" and t[b - 4].text == "." and \
            t[b - 2].text == "(" and t[b - 1].text == ")":
        return True
    return b - a >= 3 and t[a].text == "seq_to_nat" and t[a + 1].text == "(" and \
        src.pairs.get(a + 1) == b - 1


def _v_sum_clause(src, a, b):
    """Whether the ensures clause toks[a:b] states `A == B + C` (or `B + C == A`)
    over value terms."""
    t, pairs = src.toks, src.pairs
    eqs = [k for k in range(a, b) if t[k].text == "==" and not any(
        o < k < pairs[o] for o in range(a, k) if t[o].text in ("(", "[", "{") and o in pairs)]
    if len(eqs) != 1:
        return False
    k = eqs[0]
    sides = [_terms(t, a, k, pairs, 1, "v"), _terms(t, k + 1, b, pairs, 1, "v")]
    for one, two in (sides, sides[::-1]):
        if len(one) == 1 and len(two) == 2 and all(s > 0 for _, _, s in one + two) and \
                all(_v_value_term(src, x, y) for x, y, _ in one + two):
            return True
    return False


def v_no_adder(src, block, blocks):
    """(ok, why) of `no-adder` on a Verus block (see the module docstring)."""
    mine, reach = _v_reach(src, block, blocks)
    for it in reach:
        if it in mine or it.mode != "exec":
            continue
        for kw, a, b in it.clauses:
            if kw != "ensures":
                continue
            for lo, hi in _split_top(src.toks, a, b, src.pairs, (",",), "v"):
                if hi > lo and _v_sum_clause(src, lo, hi):
                    return False, (f"`{it.name}` (line {src.line_of(it.head)}), a helper the "
                                   "block calls, states a whole-number sum in its `ensures` "
                                   f"(line {src.toks[lo].line})")
    return True, ""


def v_nl_steps(src, block, need, skip=()):
    t, n = src.toks, 0
    for k in _block_toks(src, block, skip):
        if t[k].kind != "id" or t[k].text != "assert" or k + 1 >= len(t) or t[k + 1].text != "(":
            continue
        j = src.pairs.get(k + 1)
        if j is None:
            continue
        seq = [x.text for x in t[j + 1:j + 6]]
        if seq == ["by", "(", "nonlinear_arith", ")", "requires"]:
            n += 1
    if n >= need:
        return True, ""
    return False, (f"{n} scoped `nonlinear_arith` step(s) in the block (`assert(…) by "
                   f"(nonlinear_arith) requires …`), {need} needed")


def v_trigger(src, block, skip=()):
    t = src.toks
    ks = _block_toks(src, block, skip)
    quant = any(t[k].kind == "id" and t[k].text in ("forall", "exists") for k in ks)
    trig = False
    for k in ks:
        if t[k].text != "#":
            continue
        j = k + 1
        if j < len(t) and t[j].text == "!":
            j += 1
        if j + 1 < len(t) and t[j].text == "[" and t[j + 1].text == "trigger":
            trig = True
            break
    if quant and trig:
        return True, ""
    return False, ("no explicit trigger (`#[trigger]` or `#![trigger …]`)" if not trig
                   else "no quantifier") + " in the block"


def v_resource_lines(src, block):
    t, out = src.toks, []
    for k in _block_toks(src, block):
        if t[k].kind == "id" and t[k].text == "verifier" and k + 2 < len(t) and (
                (t[k + 1].text == "::" and t[k + 2].text == "rlimit")
                or (t[k + 1].text == "(" and t[k + 2].text == "rlimit")):
            out.append(t[k].line)
    return sorted(set(out))


# --- Dafny ------------------------------------------------------------------------------

def d_given_ranges(src, block, given):
    """Token ranges outside a Dafny block's answer region (see the module
    docstring): the header of the block's first lemma, method, function or
    predicate (its attributes included), and every given declaration."""
    from . import dafny as D
    lo, hi = block
    decls = [d for d in src.decls if lo <= d.line <= hi]
    target = next((d for d in decls if d.kind in D.METHODLIKE - {"iterator"}), None)
    out = []
    if target is not None:
        out.append((target.start, target.header_end))
    for d in decls:
        if d is target or not given or d.name not in given:
            continue
        end = d.by_method[1] if d.by_method else d.body[1] if d.body else d.header_end - 1
        out.append((d.start, end + 1))
    return out


def d_trigger(src, block, skip=()):
    lo, hi = block

    def free(k):
        return not any(a <= k < b for a, b in skip)
    quant = any(x.kind == "id" and x.text in ("forall", "exists") and lo <= x.line <= hi
                and free(k) for k, x in enumerate(src.toks))
    trig = any(a.style == "{:" and a.name == "trigger" and lo <= a.line <= hi and free(a.start)
               for a in src.attrs)
    if quant and trig:
        return True, ""
    return False, ("no explicit trigger (`{:trigger …}`)" if not trig else "no quantifier") \
        + " in the block"


SPEC_STMT_HEADS = {"assert", "assume", "calc", "ghost", "reveal", "invariant", "decreases",
                   "requires", "ensures", "reads", "modifies"}


def _d_stmt_head(src, k, floor):
    """The first token of the statement or clause that holds token k: walk back
    to the last `;`, `{` or `}` at k's nesting depth (not before floor)."""
    tk = src.toks
    depth = 0
    j = k - 1
    while j >= floor:
        t = tk[j].text
        if t in (")", "]"):
            depth += 1
        elif t in ("(", "["):
            if depth == 0:
                j -= 1
                continue
            depth -= 1
        elif depth == 0 and t in (";", "{", "}"):
            break
        elif depth == 0 and tk[j].kind == "id" and t in SPEC_STMT_HEADS:
            return t
        j -= 1
    nxt = j + 1
    while nxt < k and tk[nxt].kind != "id":
        nxt += 1
    return tk[nxt].text if nxt < k else ""


def _d_bare_call(tk, pairs, k, floor):
    """Whether token k lies in the arguments of a bare call statement
    (`L(…);`, `M.L(…);`): in Dafny that is a lemma or method call, and a call
    statement assigns nothing, so its arguments compute no result."""
    depth, j = 0, k - 1
    while j >= floor:
        t = tk[j].text
        if t in (")", "]"):
            depth += 1
        elif t in ("(", "["):
            depth = max(depth - 1, 0)
        elif depth == 0 and t in (";", "{", "}"):
            break
        j -= 1
    s = j + 1
    if s >= len(tk) or tk[s].kind != "id":
        return False
    i = s + 1
    while i + 1 < len(tk) and tk[i].text == "." and tk[i + 1].kind == "id":
        i += 2
    if i >= len(tk) or tk[i].text != "(" or i not in pairs:
        return False
    close = pairs[i]
    return i < k < close and close + 1 < len(tk) and tk[close + 1].text == ";"


def d_no_call(src, block, name, skip=()):
    lo, hi = block
    tk = src.toks
    pairs = None
    first = next((k for k, x in enumerate(tk) if x.line >= lo), len(tk))
    for k, x in enumerate(tk):
        if not (lo <= x.line <= hi) or x.kind != "id" or x.text != name:
            continue
        if any(a <= k < b for a, b in skip):
            continue
        if k + 1 >= len(tk) or tk[k + 1].text != "(":
            continue
        if _d_stmt_head(src, k, first) in SPEC_STMT_HEADS:
            continue
        if pairs is None:
            pairs = _partners(tk)
        if _d_bare_call(tk, pairs, k, first):
            continue
        return False, f"a compiled call of `{name}` at line {x.line}"
    return True, ""


def d_formula(src, name):
    from . import dafny as D
    d = next((x for x in src.decls if x.name == name and x.kind in D.METHODLIKE), None)
    if d is None:
        return False, f"no declaration `{name}` in the file"
    if not d.body:
        return False, f"`{name}` has no body"
    tk = src.toks
    a, b = d.body
    for k in range(a + 1, b):
        x = tk[k]
        if x.kind == "id" and x.text in ("var", "match"):
            return False, f"`{x.text}` in the body of `{name}` (line {x.line})"
        if x.kind == "id" and k + 1 < b and tk[k + 1].text == "(":
            return False, f"a call of `{x.text}` in the body of `{name}` (line {x.line})"
    return True, ""


# --- loop-dir (Dafny and Verus) -------------------------------------------------------------

_LOOP_CLAUSES = {"d": {"invariant", "decreases", "modifies"},
                 "v": {"invariant", "invariant_except_break", "invariant_ensures", "ensures",
                       "decreases"}}


def _partners(toks):
    """{open index: close index} and its inverse, for (), [] and {} (unbalanced
    brackets are left unpaired)."""
    out, stack = {}, []
    opens, closes = "([{", ")]}"
    for k, x in enumerate(toks):
        if x.kind in ("id", "num", "str", "char", "lit", "life"):
            continue
        if x.text in opens:
            stack.append(k)
        elif x.text in closes:
            while stack and opens.index(toks[stack[-1]].text) != closes.index(x.text):
                stack.pop()
            if stack:
                o = stack.pop()
                out[o], out[k] = k, o
    return out


def _d_expr_brace(toks, k):
    """A Dafny `{` that opens an expression (a set display, an attribute)."""
    from . import dafny as D
    nxt = toks[k + 1].text if k + 1 < len(toks) else ""
    return nxt == ":" or (k > 0 and toks[k - 1].text in D.EXPR_PREV)


def _loop_parts(toks, pairs, k, lang):
    """(guard token range, body (open, close)) of the `while` at token k, or
    None when no body brace follows."""
    stop = _LOOP_CLAUSES[lang]
    j, guard_end = k + 1, None
    while j < len(toks):
        x = toks[j]
        if x.text in ("(", "[") and j in pairs:
            j = pairs[j] + 1
            continue
        if x.kind == "id" and x.text in stop:
            guard_end = guard_end or j
        elif x.text == "{":
            if lang == "d" and _d_expr_brace(toks, j) and j in pairs:
                j = pairs[j] + 1
                continue
            if j not in pairs:
                return None
            return (k + 1, guard_end or j), (j, pairs[j])
        elif x.text in (";", "}"):
            return None
        j += 1
    return None


def _stmt_start(toks, j, floor):
    """The index of the first token of the statement holding token j."""
    i = j - 1
    while i > floor and toks[i].text not in (";", "{", "}"):
        i -= 1
    return i + 1


def _stmt_end(toks, pairs, j, ceil):
    i = j
    while i < ceil and toks[i].text != ";":
        if toks[i].text in ("(", "[", "{") and i in pairs:
            i = pairs[i]
        i += 1
    return i


def _steps(toks, pairs, body, names, lang):
    """{name: [step]} of the assignments to `names` in a loop body: 'up',
    'down' or 'other' (see the module docstring)."""
    a, b = body
    out = {n: [] for n in names}
    assign = (":=",) if lang == "d" else ("=", "+=", "-=", "*=", "/=", "%=", "<<=", ">>=",
                                          "&=", "|=", "^=")
    decl_kw = "var" if lang == "d" else "let"
    j = a
    while j + 1 < b:
        j += 1
        x = toks[j]
        if x.text in ("(", "[") and j in pairs:   # an assignment is a statement
            j = pairs[j]
            continue
        if lang == "d" and x.text == ":|":
            pass
        elif x.text not in assign:
            continue
        s = _stmt_start(toks, j, a)
        lhs = toks[s:j]
        if lhs and lhs[0].kind == "id" and lhs[0].text in (decl_kw, "ghost"):
            for y in lhs:
                if y.kind == "id" and y.text in out:
                    out[y.text].append("other")
            continue
        hit = [y.text for y in lhs if y.kind == "id" and y.text in out]
        if not hit:
            continue
        single = len(lhs) == 1 and lhs[0].kind == "id"
        if not single or x.text == ":|":
            for n in hit:
                out[n].append("other")
            continue
        n = lhs[0].text
        if x.text == "+=":
            out[n].append("up")
            continue
        if x.text == "-=":
            out[n].append("down")
            continue
        if x.text not in (":=", "="):
            out[n].append("other")
            continue
        e = _stmt_end(toks, pairs, j + 1, b)
        rhs = toks[j + 1:e]
        if len(rhs) >= 3 and rhs[0].kind == "id" and rhs[0].text == n and \
                rhs[1].text in ("+", "-"):
            out[n].append("up" if rhs[1].text == "+" else "down")
        else:
            out[n].append("other")
    return out


def _break_guard(toks, pairs, body):
    """The identifiers of a Verus `loop`'s exit conditions (DV5c gaps lane): the
    condition of every `if <cond> { … break … }` at the top level of the loop's body
    stands for the guard a `while` would have (its negation), so a guardless `loop`
    that exits on a counter has that counter as its guard. [] when the body has no
    such exit."""
    a, b = body
    names, j = [], a + 1
    while j < b:
        x = toks[j]
        if x.text == "if" and x.kind == "id":
            c = j + 1
            while c < b and toks[c].text != "{":
                if toks[c].text in ("(", "[") and c in pairs:
                    c = pairs[c] + 1
                    continue
                c += 1
            if c < b and c in pairs:
                inner = range(c + 1, pairs[c])
                if any(toks[i].kind == "id" and toks[i].text == "break" for i in inner):
                    names += [toks[i].text for i in range(j + 1, c) if toks[i].kind == "id"
                              and not (i > 0 and toks[i - 1].text in (".", "::"))
                              and toks[i].text not in names]
                j = pairs[c] + 1
                continue
        if x.text in ("{", "(", "[") and j in pairs:
            j = pairs[j] + 1                     # only the body's top level
            continue
        j += 1
    return names


def loops_of(src, lang, block, skip=()):
    """[{line, kind, guard, dirs, dir, why}] of the loops in a block's answer
    region (see `loop-dir` in the module docstring): guard the identifiers of
    a `while` guard (a `for` loop: its variable), dirs {counter: 'up' | 'down'
    | None}, dir 'up', 'down', 'mixed' or None (no counter, or a counter
    assigned another way), and why when dir is None."""
    toks = src.toks
    pairs = src.pairs if lang == "v" else _partners(toks)
    lo, hi = block
    out = []

    def add(line, kind, guard, dirs, d, why="", body=None):
        out.append({"line": line, "kind": kind, "guard": set(guard), "dirs": dirs, "dir": d,
                    "why": why, "body": body})

    def brace_after(j):
        while j < len(toks) and toks[j].text not in ("{", ";"):
            if toks[j].text in ("(", "[") and j in pairs:
                j = pairs[j] + 1
                continue
            j += 1
        return (j, pairs[j]) if j < len(toks) and toks[j].text == "{" and j in pairs else None
    for k, x in enumerate(toks):
        if not (lo <= x.line <= hi) or x.kind != "id" or any(s <= k < e for s, e in skip):
            continue
        if x.text == "for":
            if lang == "d" and k + 2 < len(toks) and toks[k + 1].kind == "id" and \
                    toks[k + 2].text == ":=":
                j, d = k + 3, None
                while j < len(toks) and toks[j].text not in ("{", ";"):
                    if toks[j].kind == "id" and toks[j].text in ("to", "downto"):
                        d = "up" if toks[j].text == "to" else "down"
                        break
                    j += 1
                v = toks[k + 1].text
                add(x.line, "for", [v], {v: d}, d, "" if d else "a `for` loop with no range",
                    brace_after(k + 3))
            elif lang == "v" and k + 2 < len(toks) and toks[k + 1].kind == "id" and \
                    toks[k + 2].text == "in":
                j, d = k + 3, "up"
                while j < len(toks) and toks[j].text != "{":
                    if toks[j].text in ("(", "[") and j in pairs:
                        j = pairs[j] + 1
                        continue
                    if toks[j].kind == "id" and toks[j].text == "rev":
                        d = "down"
                    j += 1
                v = toks[k + 1].text
                add(x.line, "for", [v], {v: d}, d, body=brace_after(k + 3))
            continue
        if x.text == "loop" and lang == "v" and k + 1 < len(toks) and (
                toks[k + 1].text == "{" or toks[k + 1].text in _LOOP_CLAUSES["v"]):
            body = brace_after(k + 1)
            names = _break_guard(toks, pairs, body) if body else []
            if not names:
                add(x.line, "loop", [], {}, None, "a `loop` has no guard (no top-level "
                    "`if … { break }` exit)", body)
                continue
            steps = _steps(toks, pairs, body, dict.fromkeys(names), lang)
            dirs = {n: (st[0] if len(set(st)) == 1 and st[0] != "other" else None)
                    for n, st in steps.items() if st}
            ds = {d for d in dirs.values() if d is not None}
            if not dirs:
                add(x.line, "loop", names, dirs, None,
                    "no identifier of its exit condition is assigned in its body", body)
            elif not ds:
                add(x.line, "loop", names, dirs, None, "no identifier of its exit condition "
                    "only steps up or only steps down", body)
            else:
                add(x.line, "loop", names, dirs, ds.pop() if len(ds) == 1 else "mixed",
                    body=body)
            continue
        if x.text != "while":
            continue
        parts = _loop_parts(toks, pairs, k, lang)
        if parts is None:
            add(x.line, "while", [], {}, None, "no loop body found")
            continue
        (ga, gb), body = parts
        names = [toks[j].text for j in range(ga, gb) if toks[j].kind == "id"
                 and not (j > 0 and toks[j - 1].text in (".", "::"))]
        steps = _steps(toks, pairs, body, dict.fromkeys(names), lang)
        dirs = {n: (st[0] if len(set(st)) == 1 and st[0] != "other" else None)
                for n, st in steps.items() if st}
        ds = {d for d in dirs.values() if d is not None}
        if not dirs:
            add(x.line, "while", names, dirs, None,
                "no identifier of its guard is assigned in its body", body)
        elif not ds:
            add(x.line, "while", names, dirs, None, "no identifier of its guard only steps up "
                "or only steps down", body)
        else:
            add(x.line, "while", names, dirs, ds.pop() if len(ds) == 1 else "mixed", body=body)
    return out


# --- loop-dir: what the loop reads and what it computes (DV5c fix round) ---------------------

_MUT_METHODS = {"push", "set", "pop", "insert", "remove", "clear", "truncate", "append",
                "extend", "swap", "resize"}
_IDX_METHODS = {"subrange": None, "skip": None, "take": None, "update": 1, "set": 1,
                "index": 1, "spec_index": 1, "insert": 1, "remove": 1}
_DECL_KWS = {"var", "let", "ghost", "mut", "tracked"}
_NOT_BASE_KWS = {"in", "return", "if", "else", "while", "match", "let", "var", "mut", "as",
                 "assert", "assume", "invariant", "decreases", "requires", "ensures", "ghost",
                 "calc", "forall", "exists", "seq", "set", "map", "multiset", "iset", "imap"}


def _is_op(x, *texts):
    return x.kind not in ("id", "num", "str", "char", "lit", "life") and x.text in texts


def _split_top(toks, lo, hi, pairs, seps, lang):
    """[(a, b)] sub-ranges of toks[lo:hi] split at top-level separators seps
    (brackets through pairs; a Dafny `|…|` counts as a bracket)."""
    out, start, k, card = [], lo, lo, False
    while k < hi:
        x = toks[k]
        if _is_op(x, "(", "[", "{") and k in pairs and pairs[k] < hi:
            k = pairs[k] + 1
            continue
        if lang == "d" and _is_op(x, "|"):
            card = not card
        elif not card and _is_op(x, *seps):
            out.append((start, k))
            start = k + 1
        k += 1
    out.append((start, hi))
    return out


def _base_of(toks, pairs, j, floor):
    """The token index of the leading identifier of the postfix chain ending
    at token j (`a.limbs`, `v@`, `s[k..]`), or None."""
    i = j
    while i >= floor:
        x = toks[i]
        if _is_op(x, ")", "]"):
            o = pairs.get(i)
            if o is None:
                return None
            i = o - 1
            continue
        if _is_op(x, "@"):
            i -= 1
            continue
        if x.kind == "id":
            if i - 1 >= floor and _is_op(toks[i - 1], ".", "::"):
                i -= 2
                continue
            return i
        return None
    return None


def _index_ranges(toks, pairs, a, b, lang):
    """[(lo, hi, base)] of the index positions among toks a..b: the inside of
    `x[…]` (a Dafny slice split at `..`, an update `x[i := v]` cut at `:=`,
    several indices split at `,`) and the index arguments of `.subrange(…)`,
    `.skip(…)`, `.take(…)`, `.update(…)`, `.set(…)`, `.index(…)`, `.insert(…)`
    and `.remove(…)`; base: the token index of the indexed expression's leading
    identifier (_base_of), or None."""
    out = []
    for j in range(a + 1, b):
        x = toks[j]
        if _is_op(x, "[") and j in pairs:
            p = toks[j - 1]
            if not ((p.kind == "id" and p.text not in _NOT_BASE_KWS) or _is_op(p, ")", "]", "@")):
                continue
            hi = pairs[j]
            base = _base_of(toks, pairs, j - 1, a)
            for lo2, hi2 in _split_top(toks, j + 1, hi, pairs, (",",), lang):
                cut = next((k for lo3, hi3 in [(lo2, hi2)] for k in range(lo3, hi3)
                            if _is_op(toks[k], ":=")), hi2)
                for lo3, hi3 in _split_top(toks, lo2, cut, pairs, ("..",), lang):
                    if hi3 > lo3:
                        out.append((lo3, hi3, base))
        elif x.kind == "id" and x.text in _IDX_METHODS and _is_op(toks[j - 1], ".") and \
                j + 1 < b and _is_op(toks[j + 1], "(") and j + 1 in pairs:
            args = _split_top(toks, j + 2, pairs[j + 1], pairs, (",",), lang)
            n = _IDX_METHODS[x.text]
            base = _base_of(toks, pairs, j - 2, a)
            out += [(lo2, hi2, base) for lo2, hi2 in (args if n is None else args[:n])
                    if hi2 > lo2]
    return out


def _strip_cast(toks, lo, hi):
    """hi without a trailing cast `as <type>` (a type of identifiers, `::` and
    generic arguments)."""
    k, depth = hi - 1, 0
    while k > lo:
        x = toks[k]
        if _is_op(x, ">"):
            depth += 1
        elif _is_op(x, "<"):
            depth -= 1
        elif depth == 0 and x.kind == "id" and x.text == "as":
            return k
        elif depth == 0 and not (x.kind == "id" or _is_op(x, "::", ",")):
            return hi
        k -= 1
    return hi


def _terms(toks, lo, hi, pairs, sign, lang):
    """[(lo, hi, sign)] of the additive terms of toks[lo:hi]: split at the
    top-level binary `+` and `-`; a unary minus flips a term's sign, a cast is
    dropped, and a whole parenthesized term is opened with its sign."""
    raw, k, start, cur, card, operand = [], lo, lo, sign, False, False
    while k < hi:
        x = toks[k]
        if _is_op(x, "(", "[", "{") and k in pairs and pairs[k] < hi:
            k = pairs[k] + 1
            operand = True
            continue
        if lang == "d" and _is_op(x, "|"):
            card = not card
            operand = not card
            k += 1
            continue
        if not card and _is_op(x, "+", "-"):
            if operand:
                raw.append((start, k, cur))
                cur = sign if x.text == "+" else -sign
            elif x.text == "-":
                cur = -cur
            start = k + 1
            operand = False
            k += 1
            continue
        operand = (x.kind != "op" and x.kind != "punct" and x.text != "as") or _is_op(x, ")", "]")
        k += 1
    raw.append((start, hi, cur))
    out = []
    for a, b, s in raw:
        b = _strip_cast(toks, a, b)
        if b <= a:
            continue
        if _is_op(toks[a], "(") and pairs.get(a) == b - 1:
            out += _terms(toks, a + 1, b - 1, pairs, s, lang)
        else:
            out.append((a, b, s))
    return out


def _index_uses(toks, pairs, lo, hi, lang, defs, sign=1, depth=0):
    """{name: {'pos', 'neg', 'opaque'}} of the identifiers of the index
    expression toks[lo:hi]: a term that is one identifier is read with its
    sign ('pos' or 'neg'); an identifier anywhere else (in a product, a call, a
    field access or a size `|…|`) is 'opaque'. An identifier with one
    definition in the loop body (defs: {name: (lo, hi)}) is read through it,
    up to 4 levels."""
    out = {}

    def put(n, how):
        out.setdefault(n, set()).add(how)

    def through(n, s, how):
        if n in defs and depth < 4:
            a, b = defs[n]
            for m, hows in _index_uses(toks, pairs, a, b, lang, defs, s, depth + 1).items():
                for h in hows:
                    put(m, h if how is None else how)
    for a, b, s in _terms(toks, lo, hi, pairs, sign, lang):
        if b - a == 1 and toks[a].kind == "id":
            n = toks[a].text
            put(n, "pos" if s > 0 else "neg")
            through(n, s, None)
            continue
        for k in range(a, b):
            if toks[k].kind == "id" and not (k > a and _is_op(toks[k - 1], ".", "::")):
                put(toks[k].text, "opaque")
                through(toks[k].text, 1, "opaque")
    return out


def _lhs_names(toks, s, j):
    """(names, mutated) of the left-hand side toks[s:j] of an assignment: the
    declared or assigned identifiers, and the base of an element or field
    assignment (`x[i] = …`, `x.f = …`)."""
    lhs = toks[s:j]
    if not lhs:
        return [], []
    if lhs[0].kind == "id" and lhs[0].text in _DECL_KWS:
        names = [y.text for k, y in enumerate(lhs) if y.kind == "id" and y.text not in _DECL_KWS
                 and k > 0 and (lhs[k - 1].kind == "id" and lhs[k - 1].text in _DECL_KWS
                                or _is_op(lhs[k - 1], ","))]
        return names, []
    parts = [(a, b) for a, b in _split_top(toks, s, j, {}, (",",), "v")]
    names, mutated = [], []
    for a, b in parts:
        if b - a == 1 and toks[a].kind == "id":
            names.append(toks[a].text)
        elif b > a and toks[a].kind == "id":
            mutated.append(toks[a].text)
    return names, mutated


def _body_assigns(toks, pairs, body, lang):
    """(steps, defs, changed) of a loop body: steps {name: [step]} of every
    identifier assigned or declared in it ('up', 'down' or 'other', as
    _steps); defs {name: (lo, hi)}: the right-hand side of an identifier with
    exactly one plain assignment or declaration in the body; changed: every
    identifier the body assigns, declares, writes an element or field of, or
    changes by a mutating method call (`x.push(…)`, `x.set(…)`, …) or a
    `&mut x` argument."""
    a, b = body
    assign = (":=",) if lang == "d" else ("=", "+=", "-=", "*=", "/=", "%=", "<<=", ">>=",
                                          "&=", "|=", "^=")
    names, rhs, count, changed = [], {}, {}, set()
    j = a
    while j + 1 < b:
        j += 1
        x = toks[j]
        if x.kind == "id" and x.text in _MUT_METHODS and j >= 2 and _is_op(toks[j - 1], ".") \
                and j + 1 < b and _is_op(toks[j + 1], "("):
            bi = _base_of(toks, pairs, j - 2, a)
            if bi is not None:
                changed.add(toks[bi].text)
            continue
        if _is_op(x, "&") and j + 2 < b and toks[j + 1].text == "mut" and toks[j + 2].kind == "id":
            changed.add(toks[j + 2].text)
            continue
        if not (_is_op(x, *assign) or (lang == "d" and _is_op(x, ":|"))):
            continue
        s = _stmt_start(toks, j, a)
        got, mut = _lhs_names(toks, s, j)
        changed.update(got)
        changed.update(mut)
        if not got:
            continue
        e = _stmt_end(toks, pairs, j + 1, b)
        for n in got:
            names.append(n)
            count[n] = count.get(n, 0) + 1
            if len(got) == 1 and x.text in ("=", ":="):
                rhs[n] = (j + 1, e)
    steps = _steps(toks, pairs, body, dict.fromkeys(names), lang) if names else {}
    defs = {n: r for n, r in rhs.items() if count.get(n) == 1}
    return steps, defs, changed


def _decl_parts(src, lang, block):
    """(params, results, body) of the item's declaration (the first lemma,
    method, function or predicate of the block; Verus: the first fn): its
    parameter names, its named results (Dafny `returns`; Verus: none) and its
    body (open, close), or None when the block declares none."""
    lo, hi = block
    toks = src.toks
    if lang == "d":
        from . import dafny as D
        d = next((x for x in src.decls if lo <= x.line <= hi
                  and x.kind in D.METHODLIKE - {"iterator"}), None)
        if d is None or not d.body:
            return None
        pairs = _partners(toks)
        groups, k = [], d.kw
        while k < d.header_end:
            if _is_op(toks[k], "(") and k in pairs:
                kind = "results" if k > 0 and toks[k - 1].text == "returns" else "params"
                if kind == "results" or not groups:
                    groups.append((kind, k, pairs[k]))
                k = pairs[k] + 1
                continue
            k += 1
        params, results = set(), set()
        for kind, a, b in groups:
            names = {toks[i].text for i in range(a + 1, b) if toks[i].kind == "id"
                     and i + 1 < b and _is_op(toks[i + 1], ":")}
            (results if kind == "results" else params).update(names)
        return params, results, d.body
    it = next((x for x in _v_fns(src) if lo <= src.line_of(x.head) <= hi), None)
    if it is None or not it.body or not it.params:
        return None
    a, b = it.params
    params = set()
    for i in range(a + 1, b):
        if toks[i].kind != "id":
            continue
        nxt = toks[i + 1] if i + 1 < b else None
        if nxt is not None and nxt.text == ":":
            params.add(toks[i].text)
        elif nxt is not None and nxt.text == ")" and i + 2 < b and toks[i + 2].text == ":":
            params.add(toks[i].text)                  # Ghost(x): …, Tracked(x): …
    return params, set(), it.body


def _block_stmts(toks, pairs, body, lang):
    """[(kind, lo, hi)] of the statements directly in a body (open, close):
    kind 'block' for a `while`, `for`, `loop`, `if` (with its `else`
    chain), `match`, `proof`, `forall` or bare `{ … }` statement, 'stmt' for one
    that ends in `;`, and 'tail' for a final expression without one."""
    a, b = body
    out, k = [], a + 1
    heads = {"while", "for", "loop", "if", "match", "proof", "unsafe", "forall"}
    while k < b:
        x = toks[k]
        if (x.kind == "id" and x.text in heads) or _is_op(x, "{"):
            j = k
            while j < b and not _is_op(toks[j], "{"):
                if _is_op(toks[j], "(", "[") and j in pairs:
                    j = pairs[j] + 1
                    continue
                if _is_op(toks[j], ";"):
                    break
                j += 1
            if j < b and _is_op(toks[j], "{") and j in pairs:
                end = pairs[j] + 1
                while end < b and toks[end].kind == "id" and toks[end].text == "else":
                    j = end
                    while j < b and not _is_op(toks[j], "{"):
                        if _is_op(toks[j], "(", "[") and j in pairs:
                            j = pairs[j] + 1
                            continue
                        j += 1
                    end = pairs[j] + 1 if j < b and j in pairs else b
                out.append(("block", k, end))
                k = end
                continue
        j = k
        while j < b and not _is_op(toks[j], ";"):
            if _is_op(toks[j], "(", "[", "{") and j in pairs:
                j = pairs[j] + 1
                continue
            j += 1
        out.append(("stmt" if j < b else "tail", k, j))
        k = j + 1
    return out


def _result_flow(toks, pairs, body, results, lang):
    """The identifiers the item's result is computed from, outside its loops:
    Dafny its named results; Verus the identifiers of its final expression and
    of each `return`; then, to a fixpoint, the identifiers of the right-hand
    side of every statement directly in the body that assigns or declares one
    of them (`let q2 = BigNat { limbs: q };` adds q)."""
    flow = set(results)
    stmts = _block_stmts(toks, pairs, body, lang)
    ids = lambda lo, hi: {toks[i].text for i in range(lo, hi) if toks[i].kind == "id"
                          and not (i > lo and _is_op(toks[i - 1], ".", "::"))}
    if lang == "v":
        for kind, lo, hi in stmts:
            if kind == "tail":
                flow |= ids(lo, hi)
        a, b = body
        for k in range(a + 1, b):
            if toks[k].kind == "id" and toks[k].text == "return":
                flow |= ids(k + 1, _stmt_end(toks, pairs, k + 1, b))
    assign = (":=",) if lang == "d" else ("=",)
    changed = True
    while changed:
        changed = False
        for kind, lo, hi in stmts:
            if kind != "stmt":
                continue
            eq = next((k for k in range(lo, hi) if _is_op(toks[k], *assign)
                       and not any(o < k < pairs[o] for o in range(lo, k)
                                   if _is_op(toks[o], "(", "[", "{") and o in pairs)), None)
            if eq is None:
                continue
            got, mut = _lhs_names(toks, lo, eq)
            if set(got + mut) & flow:
                new = ids(eq + 1, hi) - flow
                if new:
                    flow |= new
                    changed = True
    return flow


def _loop_reads(src, lang, lp, want, counters, params, flow):
    """(ok, why, anchored) of one loop the form checks: every index the loop
    body reads is computed from the identifiers the body assigns only as
    `+ x` (no `- x`, no product, call or size of one), and each of them that
    steps, steps the wanted way; anchored when the loop reads an argument of
    the item at an index that holds one of its counters and assigns an
    identifier the result is computed from (_result_flow)."""
    toks = src.toks
    pairs = src.pairs if lang == "v" else _partners(toks)
    steps, defs, changed = _body_assigns(toks, pairs, lp["body"], lang)
    dirs = {n: (st[0] if len(set(st)) == 1 and st[0] != "other" else None)
            for n, st in steps.items() if st}
    reads_arg = False
    for lo, hi, base in _index_ranges(toks, pairs, lp["body"][0], lp["body"][1], lang):
        uses = _index_uses(toks, pairs, lo, hi, lang, defs)
        expr = " ".join(toks[k].text for k in range(lo, hi))
        line = toks[lo].line
        for n, hows in sorted(uses.items()):
            if n not in steps:
                continue
            if "neg" in hows:
                return False, (f"the {lp['kind']} loop at line {lp['line']} reads index "
                               f"`{expr}` at line {line}, which subtracts `{n}`: it reads from "
                               f"the other end"), False
            if "opaque" in hows:
                return False, (f"the {lp['kind']} loop at line {lp['line']} reads index "
                               f"`{expr}` at line {line}, computed from `{n}` other than by "
                               "adding it"), False
            if dirs.get(n) in ("up", "down") and dirs[n] != want:
                return False, (f"the {lp['kind']} loop at line {lp['line']} reads index "
                               f"`{expr}` at line {line}, and `{n}` steps {dirs[n]}"), False
        if base is not None and toks[base].text in params and \
                any("pos" in uses.get(c, ()) for c in counters):
            reads_arg = True
    return True, "", reads_arg and bool(changed & flow)


def loop_dir(src, lang, block, rule, skip=()):
    """(ok, why) of a `loop-dir:[<x>:]up|down` rule on a block (see the module
    docstring)."""
    var, want = loop_dir_arg(rule)
    loops = loops_of(src, lang, block, skip)
    if var is None:
        if not loops:
            return False, "no loop in the block's answer region"
        for lp in loops:
            d = lp["dir"]
            if d != want:
                return False, (f"the {lp['kind']} loop at line {lp['line']} " + (
                    f"counts {d}" if d in ("up", "down") else
                    "steps its counters both ways" if d == "mixed" else
                    f"has no direction ({lp['why']})") + f", not {want}")
        mine = loops
    else:
        mine = [lp for lp in loops if var in lp["guard"]]
        if not mine:
            return False, f"no loop on `{var}` in the block's answer region"
        for lp in mine:
            got = lp["dirs"].get(var)
            if got != want:
                return False, (f"the {lp['kind']} loop at line {lp['line']} " + (
                    f"steps `{var}` {got}" if got in ("up", "down") else
                    f"never steps `{var}`" if var not in lp["dirs"] else
                    f"assigns `{var}` other than by a step") + f", not {want}")
    parts = _decl_parts(src, lang, block)
    if parts is None:
        return True, ""
    params, results, body = parts
    toks = src.toks
    pairs = src.pairs if lang == "v" else _partners(toks)
    flow = _result_flow(toks, pairs, body, results, lang)
    anchored = False
    for lp in mine:
        if lp.get("body") is None:
            continue
        counters = {var} if var else {g for g, d in lp["dirs"].items() if d == want}
        ok, why, anc = _loop_reads(src, lang, lp, want, counters, params, flow)
        if not ok:
            return False, why
        anchored = anchored or anc
    if not anchored:
        return False, ("no loop " + (f"on `{var}` " if var else "") + "both reads an argument "
                       "of the item at its counter and assigns what the result is computed "
                       "from")
    return True, ""


def d_resource_lines(src, block):
    lo, hi = block
    return sorted({a.line for a in src.attrs
                   if (a.style, a.name) in DAFNY_RESOURCE_ATTRS and lo <= a.line <= hi})


# --- the static check -----------------------------------------------------------------------

def block_decl_names(src, lang, block):
    """The names of a block's declarations after the item's own (the first
    lemma, method, function or predicate; Verus: the first fn): what the
    caller passes as `given` for the shipped block."""
    lo, hi = block
    if lang == "d":
        from . import dafny as D
        decls = [d for d in src.decls if lo <= d.line <= hi]
        target = next((d for d in decls if d.kind in D.METHODLIKE - {"iterator"}), None)
        return {d.name for d in decls if d is not target}
    fns = [it for it in _v_fns(src) if lo <= src.line_of(it.head) <= hi]
    return {it.name for it in fns[1:] if it.name}


def parse(text, lang, path="<text>"):
    """The parsed source the checks take (dvl.dafny.Source or verus_spec.Source).
    Raises ValueError (verus_spec.ParseError) when it does not tokenize."""
    if lang == "d":
        from . import dafny as D
        return D.parse_source(text, path)
    return vs.parse(text)


def check_static(src, lang, rules, block, blocks, given=None):
    """{rule: (ok, why)} for the static rules among `rules` (and the static
    half of `stable`: no resource attribute in the block), on a parsed source;
    block (lo, hi) is the item's block, blocks every H, X and T block of the
    file (helpers outside them are followed); given: the names of the
    declarations the block shipped with besides the item's own (None:
    unknown), left out of the answer region."""
    out = {}
    skip = (d_given_ranges(src, block, given) if lang == "d"
            else v_given_ranges(src, block, given))
    for r in rules:
        name = rule_name(r)
        if name is None:
            out[r] = (False, "not a form rule")
            continue
        if lang not in FORMS[name]:
            out[r] = (False, f"a {'Verus' if lang == 'd' else 'Dafny'} form on a "
                             f"{'Dafny' if lang == 'd' else 'Verus'} block")
            continue
        if name == "bv-exec":
            out[r] = v_bv_exec(src, block, blocks)
        elif name == "no-nl":
            out[r] = v_no_nl(src, block, blocks)
        elif name == "nl-steps":
            out[r] = v_nl_steps(src, block, int(NL_STEPS.fullmatch(r).group(1)), skip)
        elif name == "trigger":
            out[r] = d_trigger(src, block, skip) if lang == "d" else \
                v_trigger(src, block, skip)
        elif name == "no-call":
            out[r] = d_no_call(src, block, rule_arg(r), skip) if lang == "d" else \
                v_no_call(src, block, blocks, rule_arg(r))
        elif name == "formula":
            out[r] = d_formula(src, rule_arg(r))
        elif name == "loop-dir":
            out[r] = loop_dir(src, lang, block, r, skip)
        elif name == "no-adder":
            out[r] = v_no_adder(src, block, blocks)
        elif name == "stable":
            lines = d_resource_lines(src, block) if lang == "d" else v_resource_lines(src, block)
            out[r] = (not lines, f"a resource attribute at line {lines[0]}" if lines else "")
    return out
