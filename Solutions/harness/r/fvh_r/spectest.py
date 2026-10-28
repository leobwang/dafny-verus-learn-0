# Reference Solution.
"""R15 — Lab β: the spectest oracle (Exercises, Python)

Lab β's first oracle reads a specification against the card's reference
input/output pairs. Soundness (H1py): does the specification accept every
reference pair? Completeness (H2py): does it reject outputs mutated away from
them? Each question is one lemma over concrete values: its requires bind the
card's parameters and results to the pair's literals, its ensures is the
specification's postcondition (or its negation), and its body is empty, so
the verifier alone decides it.

Imports: the Python standard library and the frozen core `fvh` (harness/fvh/:
fvh.tools), nothing else. The core is frozen and complete; read it, never
edit it. Every generated file is verified through `fvh.tools.run` (never a
subprocess or a check of your own): a file this module writes lies outside
the course tree, so fvh.tools sends it to the verification container. You
judge a run from its result alone (`outcome_r15`): a killed run is
"unknown"; a container run that is refused (no Docker: RunnerUnavailable) or
deferred (memory short: PreflightError) raises.

How to work this file (Lab β's oracles; PLAN §4.3):
1. Replace each hole, in order: H1py, then H2py. A Python hole is a function
   whose body, after its docstring, is the one statement
   `raise NotImplementedError("<item id>")`; the tools count holes on the
   syntax tree, never by searching the text.
2. Run the acceptance tests (harness/tests/r/r15_cases/test_spectest.py,
   frozen): `scripts/vcheck harness/r/fvh_r/spectest.py`. No solver runs in
   them: they use synthetic cards and a stand-in for the instrument runner.
3. Done = `scripts/vcheck --gate harness/r/fvh_r/spectest.py` exits 0 (zero
   holes and every acceptance test passing), AND
   `scripts/firsttry.sh R15 --report --strict` exits 0.
4. Stuck for 20 minutes? /tutor R15.

This file ships with exactly 2 holes: H1py and H2py, each counted from the
syntax tree. The second oracle, `roundtrip_r15`, is in roundtrip.py beside
this file.

Validity (PLAN §4.3: β's hidden truth stays out of every loop). These
oracles read the card, the specification under test, the card's reference
pairs and verifier results, nothing else: the hidden verdicts
(Hidden/labs/R15/) never enter them. They run after a delivery batch, and the
comparison of their results with the hidden verdicts runs only in the grader
container. A surviving mutant is not a verdict either: an output the
specification rightly allows (an equivalent mutant) is told apart from a
weakness only by the hidden reference, after the batch.
"""

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from fvh import tools

# =============================================================================
# Given (frozen statements). Read them, never change them.
# =============================================================================

LANGS_R15 = ("dafny", "verus")
OUTCOMES_R15 = ("proved", "failed", "unknown")
PAIR_OUTCOMES_R15 = ("holds", "rejects", "unknown")
GATE_R15 = "vcheck --gate"

# The result types that mutate_outputs_r15 treats as integers, and those of
# them that hold no negative value.
INT_TYPES_R15 = ("int", "nat", "i8", "i16", "i32", "i64", "i128", "isize",
                 "u8", "u16", "u32", "u64", "u128", "usize")
NONNEG_TYPES_R15 = ("nat", "u8", "u16", "u32", "u64", "u128", "usize")


@dataclass(frozen=True)
class CardR15:
    """One Lab β card: a declaration's signature and the file around it (no
    implementation: Lab β judges specifications, not code).

    id        the card's id
    lang      "dafny" (a `method`) or "verus" (a `fn`)
    name      the declaration's name
    params    its inputs, (name, type) pairs, in order
    results   its outputs, (name, type) pairs (Verus: exactly one)
    header    the file's text before the declaration (Dafny: up to and inside
              the module, its definitions included; Verus: the imports,
              `verus! {` and the definitions)
    footer    the file's text after it (Dafny: the module's closing brace;
              Verus: the closing `} // verus!`)
    """

    id: str
    lang: str
    name: str
    params: tuple
    results: tuple
    header: str
    footer: str


@dataclass(frozen=True)
class SpecR15:
    """A specification of a card's declaration: its requires and ensures
    clauses, each one boolean expression in the card's language, in order.
    The empty tuple means no clause (true)."""

    card: CardR15
    requires: tuple = ()
    ensures: tuple = ()


@dataclass(frozen=True)
class IOPairR15:
    """One reference behaviour of a card: `inputs`, one source literal (a
    string such as "3", "-2" or "true") per parameter in order, and
    `outputs`, one source literal per result in order.

    `witnesses` (D99): the pair's witness hints, each one boolean expression
    in the card's language about the pair's inputs that names a witness term
    for an existential of the card's specifications (for `exists p ::
    OccursAt(s, w, p)` at s = "ab", w = "b": `OccursAt(s, w, 1)`). Every check
    of the pair asserts them in its body, in order, so the verifier has the
    term an empty body cannot supply. () when the pair has none."""

    inputs: tuple
    outputs: tuple
    witnesses: tuple = ()


@dataclass(frozen=True)
class OutputMutantR15:
    """One output mutant of a reference pair: its id (`O01`, `O02`, … in the
    order mutate_outputs_r15 lists them), the name of the result it changes,
    and the whole mutated outputs tuple."""

    id: str
    result: str
    outputs: tuple


@dataclass(frozen=True)
class SoundReportR15:
    """spec_sound_r15's account: one outcome of PAIR_OUTCOMES_R15 per pair, in
    the pairs' order, and `sound`, True exactly when every pair holds."""

    outcomes: tuple
    sound: bool


@dataclass(frozen=True)
class CompleteReportR15:
    """spec_complete_r15's account: the output mutants run, how many the
    specification killed (it provably rejects them), how many survived (the
    verifier could not show it rejects them), how many gave no verdict, the
    survivors as "<pair index>:<mutant id>" in run order, and the rate
    killed / (killed + survived), 0.0 when no mutant was decided."""

    total: int
    killed: int
    survived: int
    unknown: int
    survivors: tuple
    rate: float


def outcome_r15(result) -> str:
    """The outcome of one `vcheck --gate` result (an fvh.tools.ToolResult),
    judged from its fields and its `document` alone:
      "proved"   exit 0, not killed, and the document says verified, at stage
                 verify, with no hole and a verified count of at least 1;
      "failed"   not killed, and the document says failed at stage verify (a
                 verification error: the claim was checked and did not hold);
      "unknown"  anything else (killed, refused, an error, a front-end stage,
                 no document)."""
    doc = result.document if isinstance(result.document, dict) else {}
    if result.killed is not None:
        return "unknown"
    holes = doc.get("holes")
    n = doc.get("verified_count")
    if (result.exit_code == 0 and doc.get("verdict") == "verified" and doc.get("stage") == "verify"
            and holes == [] and isinstance(n, int) and not isinstance(n, bool) and n >= 1):
        return "proved"
    if doc.get("verdict") == "failed" and doc.get("stage") == "verify":
        return "failed"
    return "unknown"


def _sig_r15(pairs):
    return ", ".join(f"{n}: {t}" for n, t in pairs)


def has_existential_r15(spec: SpecR15) -> bool:
    """True when one of the specification's ensures clauses holds the quantifier
    `exists` (as a whole word, in either language): an empty-body check of
    such a postcondition needs a witness term to be proved (D99)."""
    return any(re.search(r"\bexists\b", c) for c in spec.ensures)


def render_lemma_r15(card: CardR15, name: str, params, requires, ensures, body=()) -> str:
    """The whole file of one lemma over the card's definitions (Dafny: `lemma
    name(params)` with one `requires`/`ensures` line per clause; Verus: `pub
    proof fn name(params)` with `requires` and `ensures` lists), wrapped in
    the card's header and footer. Its body asserts each expression of `body`
    in order (Dafny `assert e;`, Verus `assert(e);`), and is empty when
    `body` is ()."""
    if card.lang == "dafny":
        lines = [f"  lemma {name}({_sig_r15(params)})"]
        lines += [f"    requires {c}" for c in requires]
        lines += [f"    ensures {c}" for c in ensures]
        lines += ["  {"] + [f"    assert {e};" for e in body] + ["  }"]
    else:
        lines = [f"pub proof fn {name}({_sig_r15(params)})"]
        if requires:
            lines += ["    requires"] + [f"        {c}," for c in requires]
        if ensures:
            lines += ["    ensures"] + [f"        {c}," for c in ensures]
        lines += ["{"] + [f"    assert({e});" for e in body] + ["}"]
    return card.header + "\n".join(lines) + "\n" + card.footer


def render_pair_check_r15(card: CardR15, spec: SpecR15, name: str, inputs, outputs,
                          negate: bool, witnesses=()) -> str:
    """The whole file of the lemma that checks the specification at one
    pair of values: over the card's parameters followed by its results; its
    requires bind each of them to its literal, in order (`x == 3`), then add
    the specification's requires clauses; its one ensures is the
    specification's postcondition, the conjunction of its ensures clauses
    (one clause as it is, several each parenthesized and joined by ` && `,
    none `true`), or with `negate` its negation (`!(…)`, none `false`); its
    body asserts the pair's witness hints `witnesses`, in order (D99), and
    is empty when there are none.

    Proved without `negate`: the specification accepts these outputs for
    these inputs. Proved with `negate`: it rejects them. Raises ValueError
    when the spec is of another card or the literals do not match the
    card's parameters and results in number, and TypeError when a literal
    is not a string."""
    if spec.card != card:
        raise ValueError("the specification is of another card")
    if len(inputs) != len(card.params) or len(outputs) != len(card.results):
        raise ValueError("the literals do not match the card's parameters and results")
    values = tuple(inputs) + tuple(outputs)
    if not all(isinstance(v, str) for v in values):
        raise TypeError("a pair's inputs and outputs are source literals (strings)")
    over = tuple(card.params) + tuple(card.results)
    requires = tuple(f"{n} == {v}" for (n, _), v in zip(over, values)) + tuple(spec.requires)
    ens = tuple(spec.ensures)
    if not ens:
        post = "false" if negate else "true"
    else:
        conj = ens[0] if len(ens) == 1 else " && ".join(f"({c})" for c in ens)
        post = f"!({conj})" if negate else conj
    return render_lemma_r15(card, name, over, requires, (post,), tuple(witnesses))


# Where write_target_r15 puts a file by default, under a fresh directory
# outside the course tree: a Lab β task's layout, so the verification
# container reads it as a benchmark task of R15's stratum (bench/local/r/labbeta/).
TARGET_LAYOUT_R15 = "bench/local/r/labbeta/oracle/tasks"


def write_target_r15(text: str, lang: str, workdir=None) -> str:
    """Write one generated file into `workdir` (default: TARGET_LAYOUT_R15
    under a fresh directory outside the course tree, so fvh.tools runs it as
    an agent target, in the verification container) and return its path."""
    d = Path(workdir) if workdir is not None else \
        Path(tempfile.mkdtemp(prefix="r15-oracle-")) / TARGET_LAYOUT_R15
    d.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(suffix=".dfy" if lang == "dafny" else ".rs", dir=d)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def mutate_outputs_r15(card: CardR15, pair: IOPairR15) -> tuple:
    """The output mutants of one reference pair, each changing one result's
    literal and keeping the others. For each result in order:
      an integer type (INT_TYPES_R15) whose literal is a decimal integer
      (optionally negative): the value plus 1, the value minus 1, then 0
      when the value is not 0; a negative value is dropped for a type of
      NONNEG_TYPES_R15;
      bool, with literal `true` or `false`: its negation;
      anything else (another type or literal): no mutant.
    A mutant whose outputs equal the reference outputs, or an earlier
    mutant's, is dropped. Ids are `O01`, `O02`, … in the order listed.
    Returns a tuple of OutputMutantR15 (above)."""
    out, seen = [], {tuple(pair.outputs)}
    for k, (rname, rtype) in enumerate(card.results):
        lit = pair.outputs[k].strip()
        values = []
        if rtype in INT_TYPES_R15 and re.fullmatch(r"-?\d+", lit):
            v = int(lit)
            values = [v + 1, v - 1] + ([0] if v != 0 else [])
            if rtype in NONNEG_TYPES_R15:
                values = [w for w in values if w >= 0]
            values = [str(w) for w in values]
        elif rtype == "bool" and lit in ("true", "false"):
            values = ["false" if lit == "true" else "true"]
        for w in values:
            outs = tuple(pair.outputs[:k]) + (w,) + tuple(pair.outputs[k + 1:])
            if outs in seen:
                continue
            seen.add(outs)
            out.append(OutputMutantR15(f"O{len(out) + 1:02d}", rname, outs))
    return tuple(out)

# =============================================================================
# Holes
# =============================================================================

# item: R15.H1py
def spec_sound_r15(spec: SpecR15, pairs, *, run=None, workdir=None) -> SoundReportR15:
    """**H1.** Is the specification sound on the card's reference pairs?

    For each pair, in order, write the check `render_pair_check_r15(card,
    spec, <name>, pair.inputs, pair.outputs, False)`, where card is
    spec.card and <name> is `<card name>_PairHolds` (Dafny) or
    `<card name>_pair_holds` (Verus), with `write_target_r15` (into
    `workdir` when given), with the pair's witness hints
    (`witnesses=pair.witnesses`), and run `run("vcheck --gate", <its path>)`,
    where `run` is the argument when it is given, else `fvh.tools.run` looked
    up at the time of the call: one run per pair. The pair holds when the
    run's `outcome_r15` is "proved", rejects when it is "failed", and is
    unknown otherwise, with one exception (D99): a "failed" run is unknown,
    never rejects, when the specification has an existential
    (`has_existential_r15`) and the pair has no witness hint, because an
    empty body cannot name the witness. Returns the SoundReportR15 (above):
    sound only when every pair holds (an unknown pair is never counted as
    holding). Raises ValueError when there is no pair.
    """
    if not pairs:
        raise ValueError("no pair to check")
    card = spec.card
    go = run if run is not None else tools.run
    name = f"{card.name}_PairHolds" if card.lang == "dafny" else f"{card.name}_pair_holds"
    exist = has_existential_r15(spec)
    got = []
    for p in pairs:
        text = render_pair_check_r15(card, spec, name, p.inputs, p.outputs, False,
                                     witnesses=p.witnesses)
        o = outcome_r15(go(GATE_R15, write_target_r15(text, card.lang, workdir)))
        if o == "failed" and exist and not p.witnesses:
            o = "unknown"
        got.append("holds" if o == "proved" else "rejects" if o == "failed" else "unknown")
    return SoundReportR15(tuple(got), all(g == "holds" for g in got))
# triv: return SoundReportR15(tuple("holds" for _ in pairs), True)


# item: R15.H2py
def spec_complete_r15(spec: SpecR15, pairs, *, run=None, workdir=None) -> CompleteReportR15:
    """**H2.** How many output mutants does the specification reject?

    For each pair (index i, from 0, in order) and each of its output mutants
    `mutate_outputs_r15(card, pair)`, in order, write the negated check
    `render_pair_check_r15(card, spec, <name>, pair.inputs, mutant.outputs,
    True)`, where <name> is `<card name>_MutantRejected` (Dafny) or
    `<card name>_mutant_rejected` (Verus), with the pair's witness hints, and
    run it like spec_sound_r15's checks (`run`, `workdir`): one run per
    mutant. The mutant is killed when the run's `outcome_r15` is "proved"
    (the specification provably rejects that output), survives when it is
    "failed", and is unknown otherwise, with spec_sound_r15's exception: a
    "failed" run is unknown when the specification has an existential and the
    pair has no witness hint (D99). A survivor is listed as "<i>:<mutant
    id>". Returns the CompleteReportR15
    (above): rate = killed / (killed + survived), 0.0 when no mutant was
    decided (a pair with no mutant adds nothing and runs nothing). Raises
    ValueError when there is no pair.
    """
    if not pairs:
        raise ValueError("no pair to check")
    card = spec.card
    go = run if run is not None else tools.run
    name = f"{card.name}_MutantRejected" if card.lang == "dafny" else \
        f"{card.name}_mutant_rejected"
    exist = has_existential_r15(spec)
    killed = survived = unknown = 0
    survivors = []
    for i, p in enumerate(pairs):
        for m in mutate_outputs_r15(card, p):
            text = render_pair_check_r15(card, spec, name, p.inputs, m.outputs, True,
                                         witnesses=p.witnesses)
            o = outcome_r15(go(GATE_R15, write_target_r15(text, card.lang, workdir)))
            if o == "failed" and exist and not p.witnesses:
                o = "unknown"
            if o == "proved":
                killed += 1
            elif o == "failed":
                survived += 1
                survivors.append(f"{i}:{m.id}")
            else:
                unknown += 1
    decided = killed + survived
    return CompleteReportR15(killed + survived + unknown, killed, survived, unknown,
                             tuple(survivors), killed / decided if decided else 0.0)
# triv: return CompleteReportR15(0, 0, 0, 0, (), 1.0)
