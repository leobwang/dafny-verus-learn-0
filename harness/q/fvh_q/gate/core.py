"""Q09 — Internals III: the gate core (Exercises, Python; solo work)

Commit this module's predictions (P4 and P5 below, and the rest of Q09's)
BEFORE you open the frozen core (harness/fvh/), the acceptance tests
(harness/tests/q/gate/test_core.py), their recorded results
(harness/tests/q/fixtures/q09/) or the cheat corpus (tests/corpus/): they
state what the predictions ask about, and the forensic deliveries of
specimens/Q09/ come first.

This file is solo work (guard rule 2s): you write it yourself. No contract
allowlist may name it, and no assistant edits it; /tutor coaches it as for
any other file.

Imports: the Python standard library and the frozen core `fvh` (harness/fvh/:
fvh.verdicts, fvh.corpus, fvh.tools, fvh.stats), nothing else. The core is
frozen and complete; read it (after your predictions), never edit it. Two
rules carry over from Q06: statistics code lives only in the core (compose
fvh.stats, never re-derive an interval), and an instrument runs only through
`fvh.tools.run` (never a subprocess or a check of your own).

How to work this file:
1. Predictions first: P4 and P5 (the prediction block below; their answers go
   in slots/Q09.slots), with every other prediction of the module (the Dafny
   file's prediction block lists them); record the first tries with
   `scripts/firsttry.sh Q09 --check` before you run anything they are about.
2. Replace each hole, in order: H2, H3, H4, H5. A Python hole is a function
   whose body, after its docstring, is the one statement
   `raise NotImplementedError("<item id>")`; the tools count holes on the
   syntax tree, never by searching the text.
3. Run the acceptance tests (harness/tests/q/gate/test_core.py, frozen):
   `scripts/vcheck harness/q/fvh_q/gate/core.py`. No solver runs in them:
   they replay recorded instrument results.
4. Done = `scripts/vcheck --gate harness/q/fvh_q/gate/core.py` exits 0 (zero
   holes and every acceptance test passing), AND
   `scripts/firsttry.sh Q09 --report --strict` exits 0.
5. Then your own live check, outside the tests: the gate over the Q half of
   the cheat corpus, on the host, one instrument at a time (about five
   minutes): `cd harness && PYTHONPATH=q uv run python -m fvh_q.gate.core
   --half Q`.
6. Stuck for 20 minutes? /tutor Q09.

This file ships with exactly 4 holes: H2, H3, H4 and H5, each counted from the
syntax tree. Commit every prediction BEFORE you run anything it is about, open
later files, or read CI, the registry or the plan: their checks and headers
give some predictions away.

Item kinds and the slot protocol are in the Dafny file's header
(dafny/Q/Q09_InternalsIII/std/Q09_InternalsIII.dfy). A verdict switch here is
a comment: `# SLOT: CHECK P4py` becomes `# CHECK P4py` once the first try is
recorded.

The gate decides from instruments, never from labels: `classify` and `gate`
see instrument results and the delivery's own files, as they will on a real
delivery whose class nobody knows, and only `corpus_report`, the evaluator,
reads the corpus labels.
"""

import argparse
import posixpath
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from fvh import corpus, stats, tools
from fvh.corpus import Delivery, Label
from fvh.tools import ToolResult
from fvh.verdicts import FAIL, GRADER_ONLY, PASS

# =============================================================================
# Given (frozen statements: expected/Q09.freeze pins them). Read them, never
# change them.
# =============================================================================


@dataclass(frozen=True)
class GateVerdict:
    """A gate's verdict on one delivery: `word` is PASS or FAIL; `unknown`
    holds the grader-only classes (fvh.verdicts.GRADER_ONLY, in that order)
    that no supplied instrument decided. A FAIL carries `unknown == ()`."""

    word: str
    unknown: tuple[str, ...]


@dataclass(frozen=True)
class GateResult:
    """One delivery's gate run: its id, the verdict, and every instrument
    result the gate collected, keyed by instrument name."""

    id: str
    verdict: GateVerdict
    results: Mapping[str, ToolResult]


@dataclass(frozen=True)
class Report:
    """The evaluator's account of a set of gate runs against their labels.

    detected         X class -> the number of constructs of that class whose
                     word is FAIL (every class some construct carries is a
                     key, 0 included)
    held_by_unknown  constructs the gate passed whose class is in the
                     verdict's `unknown`
    false_pass       constructs the gate passed whose class is not in the
                     verdict's `unknown` (a correct gate has none)
    fp               controls whose word is FAIL
    controls         the number of controls
    fp_interval      the 95% Wilson interval of fp / controls
    """

    detected: Mapping[str, int]
    held_by_unknown: int
    false_pass: int
    fp: int
    controls: int
    fp_interval: tuple[float, float]


def render(v: GateVerdict) -> str:
    """The printed verdict: `FAIL`, or `PASS`, followed by
    ` · UNKNOWN: X07, X08, X14` while `unknown` is not empty. Never a bare
    PASS while a grader-only class is undecided (spec §5.6)."""
    if v.word != PASS:
        return v.word
    return PASS + (" · UNKNOWN: " + ", ".join(v.unknown) if v.unknown else "")


def main(argv=None) -> int:
    """Your own live check, outside the tests: the gate over one half of the
    cheat corpus, on the host, one instrument at a time.
        cd harness && PYTHONPATH=q uv run python -m fvh_q.gate.core --half Q
    Prints one line per delivery, then the report. Exit 0 when the report
    shows no false pass and no false positive, else 1."""
    ap = argparse.ArgumentParser(prog="python -m fvh_q.gate.core", allow_abbrev=False)
    ap.add_argument("--half", required=True, choices=corpus.HALVES)
    ap.add_argument("--lang", choices=corpus.LANGS)
    a = ap.parse_args(argv)
    results, labels = [], {}
    for lang in [a.lang] if a.lang else list(corpus.LANGS):
        for fx in corpus.load_half(lang, a.half):
            r = gate(fx.delivery)
            results.append(r)
            labels[fx.id] = fx.label
            print(f"{lang}/{fx.id}: {render(r.verdict)}", flush=True)
    rep = corpus_report(results, labels)
    lo, hi = rep.fp_interval
    print("detected: " + ", ".join(f"{k} {v}" for k, v in sorted(rep.detected.items())))
    print(f"held by unknown: {rep.held_by_unknown}; false passes: {rep.false_pass}; "
          f"false positives: {rep.fp} of {rep.controls} controls "
          f"(95% Wilson interval {lo:.3f}..{hi:.3f})")
    return 0 if rep.false_pass == 0 and rep.fp == 0 else 1


# =============================================================================
# The prediction block. Commit every prediction of this module before you read
# past this block, and record the first tries:
#     scripts/firsttry.sh Q09 --check
# Verdict answers go in slots/Q09.slots (`P4py = ???` → `P4py = "<answer>"`).
# =============================================================================

# item: Q09.P4py S13 verdict
# **P4.** A pre-registered comparison of two arms with 60 tasks in each arm
# (n = 60 tasks per arm, as the function's docstring counts n), two-sided
# alpha = 0.05, power 0.8, baseline success rate 0.5: the value of
# `fvh.stats.mde_two_proportions(60, 0.5)` with its other arguments at their
# defaults. Which is closest:
#   a) 5 pp   b) 15 pp   c) 25 pp   d) 40 pp ?
# Answer form: one letter, `a`, `b`, `c` or `d`.
# SLOT: CHECK P4py

# item: Q09.P5py S13 verdict
# **P5.** A gate passes all 9 healthy controls of a corpus half (0 false
# positives in 9). Which is closest to the upper end of the 95% Wilson
# interval for its false-positive rate:
#   a) 0%   b) 10%   c) 30%   d) 50% ?
# Answer form: one letter, `a`, `b`, `c` or `d`.
# SLOT: CHECK P5py

# =============================================================================
# Holes
# =============================================================================

# item: Q09.H2py S9
def json_complete(doc: dict, lang: str) -> list[str]:
    """**H2.** The reasons a `scripts/vcheck --json` document cannot be
    trusted as a pass, from the document's own fields; `[]` for a complete
    one.

    `lang` is the delivery's language, "dafny" or "verus". One reason (a
    short string, your wording) per check that fails, in this order:

      1. `lang` is the given language;
      2. `stage` is "verify" (the run reached verification);
      3. `verdict` is "verified";
      4. `exit_code` (the verifier's own exit code, not vcheck's) is 0;
      5. `holes` is a list, and it is empty;
      6. `findings` is a list, and it is empty;
      7. `verified_count` is an int (a bool is not one) of at least 1.

    A missing key fails its check. A `doc` that is not a dict gives exactly
    one reason.
    """
    raise NotImplementedError("Q09.H2py")
# Hint: `dict.get` reads a missing key as None, which fails every check above;
#    test each field on its own and append one reason per failure.


# item: Q09.H3py S12
def classify(results: Mapping[str, ToolResult]) -> GateVerdict:
    """**H3.** One delivery's verdict from its instrument results alone.

    `results` maps instrument names (fvh.tools.INSTRUMENTS) to the
    ToolResult of that instrument on the delivery. A result's language is
    its target's: a target ending in `.dfy` is Dafny ("dafny"), any other
    is Verus ("verus").

    FAIL (with `unknown == ()`) when any of these holds:
      - "vcheck --gate" or "vaudit" is missing from `results`;
      - a result was killed (`killed` is not None) or its `exit_code` is
        neither 0 nor 1 (no exit code, a usage error or a refusal);
      - "vcheck --gate" exits 1, or `json_complete` gives a reason on its
        document;
      - "vaudit", "specfreeze --check", "witness" or "seed-rerun" exits 1
        (a finding, a changed statement, no concrete call that meets the
        `requires`, a verdict that moved);
      - "swap-to-false" exits 0 (the conclusion replaced by `false` still
        verifies: the hypotheses are vacuous).

    Otherwise a mechanical PASS whose `unknown` is GRADER_ONLY, in that
    order, minus the classes a supplied oracle decided: a "witness" result
    (here it passed) decides X07, a "specfreeze --check" result decides
    X08; nothing decides X14.
    """
    raise NotImplementedError("Q09.H3py")
# Hint(1): settle every FAIL condition first; what is left is a PASS.
# Hint(2): build `unknown` from GRADER_ONLY in its own order, leaving out what
#    the supplied oracles decided.


# item: Q09.H4py S12
def gate(delivery: Delivery, *, run=None) -> GateResult:
    """**H4.** Run the instruments a delivery calls for, then classify.

    Always "vcheck --gate" and "vaudit" on `delivery.target`. Then, by the
    companions among `delivery.files` (repo-relative paths; tests/corpus/
    README.md's layout), with <dir> the directory of a Dafny target and
    <t> a Verus target (a crate directory):
      "specfreeze --check"  Dafny: <dir>/frozen.dfy is a file of the
                            delivery; Verus: <t>/frozen.rs is;
      "witness"             Dafny: <dir>/witness.dfy; Verus: a file under
                            <t>/witness/;
      "swap-to-false"       Dafny: <dir>/swap.dfy; Verus: a file under
                            <t>/swapped/.
    The layout is public, and `fvh.tools.command(instrument, target)`
    encodes it (the paths its argv names): you may compose it rather than
    write the paths above out. The rest is the gate's own work: whether the
    delivery brings an instrument's companions (a companion directory counts
    when a file of the delivery lies under it), and a verdict from the
    results alone.
    Each instrument runs once, in a fresh process, as
    `run(instrument, delivery.target)`, where `run` is the argument when it
    is given, else `fvh.tools.run` looked up at the time of the call (never
    an instrument of your own). Returns GateResult(delivery.id,
    classify(results), results), the results keyed by instrument name. A
    killed or timed-out run is a FAIL, never a PASS (classify sees to it);
    an instrument that cannot run at all raises, and the gate never turns
    that into a PASS. Raises ValueError for a language other than "dafny"
    and "verus".
    """
    raise NotImplementedError("Q09.H4py")
# Hint(1): `posixpath` joins and splits repo-relative paths the way the corpus
#    writes them.
# Hint(2): `tools.run`, read through the module when the gate runs, is what a
#    test can replace; a name bound at import time is not.


# item: Q09.H5py S13
def corpus_report(results: Sequence[GateResult], labels: Mapping[str, Label]) -> Report:
    """**H5.** The evaluator: the one function here that reads labels.

    `labels` maps a delivery id to its Label (fvh.corpus). For each result,
    by its label's kind:
      construct          FAIL: counts under `detected[label.xclass]`;
                         PASS with `label.xclass` in the verdict's
                         `unknown`: held by unknown; any other PASS: a
                         false pass;
      control            FAIL: a false positive; every control counts in
                         `controls`;
      covered-elsewhere  not counted.
    `detected` has a key for every class some construct carries, 0
    included. `fp_interval` is the 95% Wilson interval of the false
    positives among the controls, by composing `fvh.stats`. Raises
    ValueError for a result whose id has no label.
    """
    raise NotImplementedError("Q09.H5py")
# Hint: one pass over the results; fvh.stats.wilson_interval takes the false
#    positives and the number of controls.


if __name__ == "__main__":
    sys.exit(main())
