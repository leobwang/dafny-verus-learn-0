"""Q15 — Lab 2: the specification oracles (Exercises, Python)

Imports: the Python standard library and the frozen core `fvh` (harness/fvh/:
fvh.tools), nothing else. The core is frozen and complete; read it, never
edit it. Every generated file is verified through `fvh.tools.run` (never a
subprocess or a check of your own): a file this module writes lies outside
the course tree, so fvh.tools sends it to the verification container
(QPLAN §25.6). You judge a run from its result alone (`outcome`): a killed
run is "unknown"; a container run that is refused (no Docker:
RunnerUnavailable) or deferred (memory short: PreflightError) raises.

How to work this file (Lab 2's oracles, after the prose specifications; QPLAN
§25.5-§25.6):
1. Replace each hole, in order: H9, H10, H11, then H12. A Python hole is a
   function whose body, after its docstring, is the one statement
   `raise NotImplementedError("<item id>")`; the tools count holes on the
   syntax tree, never by searching the text.
2. Run the acceptance tests (harness/tests/q/test_oracles.py, frozen):
   `scripts/vcheck harness/q/fvh_q/oracles.py`. No solver runs in them: they
   use synthetic tasks and a stand-in for the instrument runner.
3. Done = `scripts/vcheck --gate harness/q/fvh_q/oracles.py` exits 0 (zero
   holes and every acceptance test passing), AND
   `scripts/firsttry.sh Q15 --report --strict` exits 0.
4. Stuck for 20 minutes? /tutor Q15.

This file ships with exactly 4 holes: H9, H10, H11 and H12, each counted from
the syntax tree. Item kinds and the slot protocol are in the Dafny file's
header (dafny/Q/Q15_PracticeIIC/std/Q15_PracticeIIC.dfy).

Which oracle may run where (QPLAN §25.5): `mutants`, `kill_rate` and
`vacuity` need no hidden input, so their results are the reference-free
feedback arm S1 may see between samples; `implication` and `classify` name
the hidden reference, so they run only after a batch, in the grader
container, where every arm's output is re-judged.
"""

import enum
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from fvh import tools

# =============================================================================
# Given (frozen statements: expected/Q15.freeze pins them). Read them, never
# change them.
# =============================================================================

LANGS = ("dafny", "verus")
OUTCOMES = ("proved", "failed", "unknown")
GATE = "vcheck --gate"


class Verdict(enum.Enum):
    """The oracle's judgement of a specification against the reference.

    The two implication lemmas (implication, H11) read a specification's
    requires and ensures together, inside the reference's requires. So an
    added requires narrows the specification and counts as STRONG (unless
    the reference's requires and ensures give it, the reference's behaviours
    do not meet it), and a dropped requires is not seen (nothing outside the
    reference's requires is judged): WEAK and STRONG speak of what the
    specification claims where the reference's requires hold."""

    FAITHFUL = "faithful"     # it and the reference imply each other
    WEAK = "weak"             # it says less than the reference: wrong behaviours pass it
    STRONG = "strong"         # it claims more (correct behaviours fail it) or adds a requires
    VACUOUS = "vacuous"       # its requires can never hold, so it never applies
    UNDECIDED = "undecided"   # the verifier settled neither way (counts as unfaithful)


@dataclass(frozen=True)
class Task:
    """One prose task: a declaration's signature, its shipped implementation
    and the file around it.

    id        the task's id (a card name: `d01-…`, `v03-…`)
    lang      "dafny" (a `method`) or "verus" (a `pub fn`)
    name      the declaration's name
    params    its inputs, (name, type) pairs, in order
    results   its outputs, (name, type) pairs (Verus: exactly one)
    body      the implementation: the text between the declaration's braces
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
    body: str
    header: str
    footer: str


@dataclass(frozen=True)
class Spec:
    """A specification of a task's declaration: its requires and ensures
    clauses, each one boolean expression in the task's language, in order.
    The empty tuple means no clause (requires: true)."""

    task: Task
    requires: tuple = ()
    ensures: tuple = ()


@dataclass(frozen=True)
class Mutant:
    """One mutant of a task's implementation: its id (`M01`, `M02`, … in the
    order mutants() lists them), the operator that made it (MUTATION_OPERATORS'
    names), the character offset of the mutated token in the body, and the
    mutated body."""

    id: str
    operator: str
    offset: int
    body: str


@dataclass(frozen=True)
class KillReport:
    """kill_rate's account: the mutants run, how many the specification
    killed (their run failed), how many survived (they verified against it),
    how many gave no verdict (unknown), the survivors' ids in mutant order,
    and the rate killed / total."""

    total: int
    killed: int
    survived: int
    unknown: int
    survivors: tuple
    rate: float


@dataclass(frozen=True)
class Implication:
    """implication's account: the outcome (OUTCOMES) of each of its two
    lemmas, both inside the reference's requires. spec_implies_ref: the
    specification's behaviours meet the reference (if it failed, the
    specification is too weak); ref_implies_spec: the reference's behaviours
    meet the specification, its requires included (if it failed, the
    specification is too strong, or it adds a requires the reference's do not
    give). A requires the specification drops is in neither lemma's
    conclusion, so neither failure shows it (Verdict)."""

    spec_implies_ref: str
    ref_implies_spec: str


def outcome(result) -> str:
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


def _sig(pairs):
    return ", ".join(f"{n}: {t}" for n, t in pairs)


def render_program(task: Task, spec: Spec, body: str) -> str:
    """The whole file of the task's declaration under `spec`, with `body` as
    its implementation (Dafny: `method name(params) returns (results)`, one
    `requires`/`ensures` line per clause; Verus: `pub fn name(params) ->
    (result)`, with `requires` and `ensures` lists)."""
    if task.lang == "dafny":
        lines = [f"  method {task.name}({_sig(task.params)}) returns ({_sig(task.results)})"]
        lines += [f"    requires {c}" for c in spec.requires]
        lines += [f"    ensures {c}" for c in spec.ensures]
        lines += ["  {", body.rstrip("\n"), "  }"]
    else:
        (rn, rt), = task.results
        lines = [f"pub fn {task.name}({_sig(task.params)}) -> ({rn}: {rt})"]
        if spec.requires:
            lines += ["    requires"] + [f"        {c}," for c in spec.requires]
        if spec.ensures:
            lines += ["    ensures"] + [f"        {c}," for c in spec.ensures]
        lines += ["{", body.rstrip("\n"), "}"]
    return task.header + "\n".join(lines) + "\n" + task.footer


def render_lemma(task: Task, name: str, params, requires, ensures) -> str:
    """The whole file of one lemma over the task's definitions (Dafny: `lemma
    name(params)` with one `requires`/`ensures` line per clause and an empty
    body; Verus: `pub proof fn name(params)` with `requires` and `ensures`
    lists and an empty body)."""
    if task.lang == "dafny":
        lines = [f"  lemma {name}({_sig(params)})"]
        lines += [f"    requires {c}" for c in requires]
        lines += [f"    ensures {c}" for c in ensures]
        lines += ["  {", "  }"]
    else:
        lines = [f"pub proof fn {name}({_sig(params)})"]
        if requires:
            lines += ["    requires"] + [f"        {c}," for c in requires]
        if ensures:
            lines += ["    ensures"] + [f"        {c}," for c in ensures]
        lines += ["{", "}"]
    return task.header + "\n".join(lines) + "\n" + task.footer


# Where write_target puts a file by default, under a fresh directory outside the
# course tree: a Lab 2 task's layout, so the verification container reads it as
# a benchmark task of Q15 (bench/local/q/lab2/STRATUM.toml names the module).
TARGET_LAYOUT = "bench/local/q/lab2/oracle/tasks"


def write_target(text: str, lang: str, workdir=None) -> str:
    """Write one generated file into `workdir` (default: TARGET_LAYOUT under a
    fresh directory outside the course tree, so fvh.tools runs it as an agent
    target, in Q15's verification container) and return its path."""
    d = Path(workdir) if workdir is not None else \
        Path(tempfile.mkdtemp(prefix="q15-oracle-")) / TARGET_LAYOUT
    d.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(suffix=".dfy" if lang == "dafny" else ".rs", dir=d)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def vacuity(spec: Spec, *, run=None, workdir=None) -> str:
    """Whether the specification's requires can never hold: the outcome of a
    lemma `<name>_vacuity(params)` that assumes every requires clause and
    proves `false`. "proved" means vacuous; "failed" means a witness may
    exist; a spec with no requires clause is "failed" without a run. `run`
    as in kill_rate."""
    if not spec.requires:
        return "failed"
    t = spec.task
    nm = f"{t.name}_Vacuity" if t.lang == "dafny" else f"{t.name}_vacuity"
    text = render_lemma(t, nm, t.params, spec.requires, ("false",))
    r = (run if run is not None else tools.run)(GATE, write_target(text, t.lang, workdir))
    return outcome(r)


# The mutation operators, in the order mutants() tries them at one site:
#   ror    a relational operator swapped: < <=, <= <, > >=, >= >, == !=, != ==
#   aor    an additive operator swapped: + -, - +
#   lit+   a decimal integer literal n made n + 1
#   lit-   a decimal integer literal n > 0 made n - 1
MUTATION_OPERATORS = ("ror", "aor", "lit+", "lit-")
ROR = {"<": "<=", "<=": "<", ">": ">=", ">=": ">", "==": "!=", "!=": "=="}
AOR = {"+": "-", "-": "+"}

# =============================================================================
# Holes
# =============================================================================

# item: Q15.H9py S13
def mutants(task: Task) -> tuple:
    """**H9.** The mutants of the task's implementation (task.body), each
    made by one operator of MUTATION_OPERATORS at one site.

    Read the body left to right, skipping `//` comments (to the end of the
    line), `/* … */` comments and `"…"` strings. The sites:
      - an operator token among `<==>`, `==>`, `<==`, `=~=`, `<=`, `>=`,
        `==`, `!=`, `<`, `>`, `+`, `-` (take the longest at each position;
        only those in ROR or AOR are sites) is a site only when the
        character just before it and the one just after it are both
        whitespace (so generics such as `Vec<u64>`, a unary minus such as
        `-1`, `->` and `::` are never sites);
      - a decimal integer literal (a maximal run of digits, not preceded by
        a letter, a digit, `_` or `.`, and not part of a `0x` literal; a type
        suffix such as `u64` or `nat` may follow it) is a site for lit+ and,
        when it is above 0, lit- (only the digits change).
    At each site (in order of their offsets) try the operators in the order
    of MUTATION_OPERATORS. Skip a mutant whose body equals an earlier one's.
    Ids are `M01`, `M02`, … in the order listed. Returns the tuple of Mutant
    (above); () when the body has no site.
    """
    raise NotImplementedError("Q15.H9py")
# Hint: one pass that records the sites first (kind, offset, token), then
#    one loop over the sites that builds the bodies.


# item: Q15.H10py S13
def kill_rate(spec: Spec, mutants: tuple, *, run=None, workdir=None) -> KillReport:
    """**H10.** Run every mutant against the specification and count.

    For each mutant, in order, write the program `render_program(spec.task,
    spec, mutant.body)` with `write_target` (into `workdir` when given) and
    run `run("vcheck --gate", <its path>)`, where `run` is the argument when
    it is given, else `fvh.tools.run` looked up at the time of the call. A
    mutant is killed when the run's `outcome` is "failed", survives when it
    is "proved", and is unknown otherwise. Returns the KillReport (above),
    rate = killed / total. Raises ValueError when there is no mutant.
    """
    raise NotImplementedError("Q15.H10py")
# Hint: `outcome` already says which runs count; a killed run is unknown,
#    never a kill.


# item: Q15.H11py S13
def implication(spec: Spec, ref: Spec, *, run=None, workdir=None) -> Implication:
    """**H11.** The two implication lemmas between a specification and the
    reference specification of the same task, each generated with
    `render_lemma` and run like kill_rate's mutants (`run`, `workdir`). Over
    the task's parameters followed by its results:

      spec_implies_ref   named `<name>_SpecImpliesRef` (Dafny) or
                         `<name>_spec_implies_ref` (Verus); requires: the
                         reference's requires clauses, then the
                         specification's requires clauses, then its ensures
                         clauses; ensures: the reference's ensures clauses;
      ref_implies_spec   named `<name>_RefImpliesSpec` or
                         `<name>_ref_implies_spec`; requires: the reference's
                         requires clauses, then its ensures clauses; ensures:
                         the specification's requires clauses, then its
                         ensures clauses.

    Each lemma's outcome is `outcome` of its run. Returns the Implication
    (above): both lemmas assume the reference's requires, so an added
    requires the reference does not give fails ref_implies_spec, and a
    dropped one fails neither (the Verdict's gloss). Raises ValueError when the two specs are of different
    tasks.
    The lemmas name the hidden reference: run this only after a batch, in
    the grader container, never inside an agent's loop (QPLAN §25.5).
    """
    raise NotImplementedError("Q15.H11py")
# Hint: `render_lemma` takes the parameters, the requires and the ensures;
#    the two lemmas differ only in which side assumes what.


# item: Q15.H12py S13
def classify(imp: Implication, vacuous: str) -> Verdict:
    """**H12.** The verdict on a specification, from its Implication and the
    outcome of its vacuity check (`vacuity`): VACUOUS when the vacuity check
    proved its requires unsatisfiable; else FAITHFUL when both lemmas were
    proved; STRONG when spec_implies_ref was proved and ref_implies_spec
    failed; WEAK when ref_implies_spec was proved and spec_implies_ref
    failed; UNDECIDED in every other case (both failed, or any outcome
    unknown, the vacuity check's included). Raises ValueError when an outcome
    is not one of OUTCOMES.
    """
    raise NotImplementedError("Q15.H12py")
# Hint: check the vacuity outcome before the two implications.
