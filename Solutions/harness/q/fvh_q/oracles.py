"""Q15 — Lab 2: the specification oracles (Reference Solution)

Hole-free reference for `harness/q/fvh_q/oracles.py` (author-only; never
learner-visible). Same names, signatures, docstrings, item markers and order
as the exercise file. Every hole is filled. Each H item declares, on a
`# triv:` line after its function, the trivial body that the Python TRIV
mode of `scripts/firsttry.sh Q15 --empty-body` lays over this reference: the
acceptance tests must reject each one (QPLAN §19.0, §11.8).

The tools run this file only by overlay: `scripts/dvl/python.py` copies
harness/ to scratch, lays this twin over its learner path and runs the
module's acceptance tests there (harness/tests/q/test_oracles.py, over
synthetic tasks and a stand-in for the instrument runner, so no solver runs).
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
    body = task.body
    sites = []
    i, n = 0, len(body)
    ops = ("<==>", "==>", "<==", "=~=", "<=", ">=", "==", "!=", "<", ">", "+", "-")
    while i < n:
        if body.startswith("//", i):
            j = body.find("\n", i)
            i = n if j < 0 else j
            continue
        if body.startswith("/*", i):
            j = body.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if body[i] == '"':
            j = i + 1
            while j < n and body[j] != '"':
                j += 2 if body[j] == "\\" else 1
            i = j + 1
            continue
        if body[i].isdigit():
            j = i
            while j < n and body[j].isdigit():
                j += 1
            prev = body[i - 1] if i > 0 else ""
            hexy = body[i] == "0" and j < n and body[j] in "xX"
            if not (prev.isalnum() or prev in "_.") and not hexy:
                sites.append(("lit", i, body[i:j]))
            k = j
            while k < n and (body[k].isalnum() or body[k] == "_"):
                k += 1
            i = k
            continue
        if body[i].isalpha() or body[i] == "_":
            j = i
            while j < n and (body[j].isalnum() or body[j] == "_"):
                j += 1
            i = j
            continue
        tok = next((o for o in ops if body.startswith(o, i)), None)
        if tok is not None:
            before = body[i - 1] if i > 0 else ""
            after = body[i + len(tok)] if i + len(tok) < n else ""
            if before.isspace() and after.isspace() and (tok in ROR or tok in AOR):
                sites.append(("op", i, tok))
            i += len(tok)
            continue
        i += 1
    out, seen = [], set()

    def add(op, off, new_body):  # reference-only: a helper of the reference
        if new_body != body and new_body not in seen:
            seen.add(new_body)
            out.append(Mutant(f"M{len(out) + 1:02d}", op, off, new_body))

    for kind, off, tok in sites:
        if kind == "op":
            if tok in ROR:
                add("ror", off, body[:off] + ROR[tok] + body[off + len(tok):])
            if tok in AOR:
                add("aor", off, body[:off] + AOR[tok] + body[off + len(tok):])
        else:
            v = int(tok)
            add("lit+", off, body[:off] + str(v + 1) + body[off + len(tok):])
            if v > 0:
                add("lit-", off, body[:off] + str(v - 1) + body[off + len(tok):])
    return tuple(out)
# triv: return ()


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
    if not mutants:
        raise ValueError("no mutant to run")
    go = run if run is not None else tools.run
    killed = survived = unknown = 0
    survivors = []
    for m in mutants:
        path = write_target(render_program(spec.task, spec, m.body), spec.task.lang, workdir)
        o = outcome(go(GATE, path))
        if o == "failed":
            killed += 1
        elif o == "proved":
            survived += 1
            survivors.append(m.id)
        else:
            unknown += 1
    total = len(mutants)
    return KillReport(total, killed, survived, unknown, tuple(survivors), killed / total)
# triv: return KillReport(len(mutants), len(mutants), 0, 0, (), 1.0)


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
    if spec.task != ref.task:
        raise ValueError("the specification and the reference are of different tasks")
    t = spec.task
    go = run if run is not None else tools.run
    over = tuple(t.params) + tuple(t.results)
    if t.lang == "dafny":
        n1, n2 = f"{t.name}_SpecImpliesRef", f"{t.name}_RefImpliesSpec"
    else:
        n1, n2 = f"{t.name}_spec_implies_ref", f"{t.name}_ref_implies_spec"
    f1 = render_lemma(t, n1, over, tuple(ref.requires) + tuple(spec.requires) + tuple(spec.ensures),
                      tuple(ref.ensures))
    f2 = render_lemma(t, n2, over, tuple(ref.requires) + tuple(ref.ensures),
                      tuple(spec.requires) + tuple(spec.ensures))
    o1 = outcome(go(GATE, write_target(f1, t.lang, workdir)))
    o2 = outcome(go(GATE, write_target(f2, t.lang, workdir)))
    return Implication(o1, o2)
# triv: return Implication("proved", "proved")


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
    for o in (imp.spec_implies_ref, imp.ref_implies_spec, vacuous):
        if o not in OUTCOMES:
            raise ValueError(f"not an outcome: {o!r}")
    if vacuous == "proved":
        return Verdict.VACUOUS
    if vacuous == "unknown":
        return Verdict.UNDECIDED
    a, b = imp.spec_implies_ref, imp.ref_implies_spec
    if a == "proved" and b == "proved":
        return Verdict.FAITHFUL
    if a == "proved" and b == "failed":
        return Verdict.STRONG
    if a == "failed" and b == "proved":
        return Verdict.WEAK
    return Verdict.UNDECIDED
# triv: return Verdict.FAITHFUL
