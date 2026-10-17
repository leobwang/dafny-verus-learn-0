"""Q09 — Internals III: the gate core (Reference Solution)

Hole-free reference for `harness/q/fvh_q/gate/core.py` (author-only; never
learner-visible). Same names, signatures, docstrings, item markers and order
as the exercise file. Every hole is filled; the verdict switches are enabled,
and the verdict answers are in `Solutions/slots/Q09.slots`, their hashes in
`expected/Q09.pins`. Each H item declares, on a `# triv:` line after its
function, the trivial body that the Python TRIV mode of
`scripts/firsttry.sh Q09 --empty-body` lays over this reference: the
acceptance tests must reject each one (QPLAN §11.8).

The tools run this file only by overlay: `scripts/dvl/python.py` copies
harness/ to scratch, lays this twin over its learner path and runs the
module's acceptance tests there (harness/tests/q/gate/test_core.py; they
replay the recorded results of harness/tests/q/fixtures/q09/, so no solver
runs).

Why the reference is shaped as it is (QPLAN §17.7; the author notes §4.6):
`classify` and `gate` decide from instrument results and the delivery's own
files only, never from a label, so the gate is the one that later runs on
deliveries whose class nobody knows. A delivery that every instrument passes
is a mechanical PASS that names the grader-only classes no supplied oracle
decided: a passing witness decides X07 (a concrete call meets the
`requires`), a passing frozen-statement check decides X08 (the statement is
the one the client froze), and nothing the course runs decides X14 (it needs
hidden tests). Only `corpus_report`, the evaluator, reads labels.
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
# The prediction block.
# =============================================================================

# item: Q09.P4py S13 verdict
# **P4.** A pre-registered comparison of two arms with 60 tasks in each arm
# (n = 60 tasks per arm, as the function's docstring counts n), two-sided
# alpha = 0.05, power 0.8, baseline success rate 0.5: the value of
# `fvh.stats.mde_two_proportions(60, 0.5)` with its other arguments at their
# defaults. Which is closest:
#   a) 5 pp   b) 15 pp   c) 25 pp   d) 40 pp ?
# Answer form: one letter, `a`, `b`, `c` or `d`.
# CHECK P4py

# item: Q09.P5py S13 verdict
# **P5.** A gate passes all 9 healthy controls of a corpus half (0 false
# positives in 9). Which is closest to the upper end of the 95% Wilson
# interval for its false-positive rate:
#   a) 0%   b) 10%   c) 30%   d) 50% ?
# Answer form: one letter, `a`, `b`, `c` or `d`.
# CHECK P5py

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
    if not isinstance(doc, dict):
        return ["the document is not a JSON object"]
    out = []
    if doc.get("lang") != lang:
        out.append(f"lang is {doc.get('lang')!r}, not {lang!r}")
    if doc.get("stage") != "verify":
        out.append(f"stage is {doc.get('stage')!r}: the run did not reach verification")
    if doc.get("verdict") != "verified":
        out.append(f"verdict is {doc.get('verdict')!r}")
    if doc.get("exit_code") != 0:
        out.append(f"the verifier's exit code is {doc.get('exit_code')!r}")
    holes = doc.get("holes")
    if not isinstance(holes, list) or holes:
        out.append("holes is not an empty list")
    findings = doc.get("findings")
    if not isinstance(findings, list) or findings:
        out.append("findings is not an empty list")
    n = doc.get("verified_count")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        out.append(f"verified_count is {n!r}, not a count of at least 1")
    return out
# triv: return []


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
    gate_result, audit = results.get("vcheck --gate"), results.get("vaudit")
    if gate_result is None or audit is None:
        return GateVerdict(FAIL, ())
    for r in results.values():
        if r.killed is not None or r.exit_code not in (0, 1):
            return GateVerdict(FAIL, ())
    lang = "dafny" if gate_result.target.endswith(".dfy") else "verus"
    if gate_result.exit_code != 0 or json_complete(gate_result.document, lang):
        return GateVerdict(FAIL, ())
    for name in ("vaudit", "specfreeze --check", "witness", "seed-rerun"):
        if name in results and results[name].exit_code == 1:
            return GateVerdict(FAIL, ())
    if "swap-to-false" in results and results["swap-to-false"].exit_code == 0:
        return GateVerdict(FAIL, ())
    decided = set()
    if "witness" in results:
        decided.add("X07")
    if "specfreeze --check" in results:
        decided.add("X08")
    return GateVerdict(PASS, tuple(x for x in GRADER_ONLY if x not in decided))
# triv: return GateVerdict(PASS, ())


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
    if delivery.lang not in ("dafny", "verus"):
        raise ValueError(f"{delivery.id}: no gate for language {delivery.lang!r}")
    call = run if run is not None else tools.run
    files = set(delivery.files)
    t = delivery.target.rstrip("/")
    wanted = ["vcheck --gate", "vaudit"]
    if delivery.lang == "dafny":
        d = posixpath.dirname(t)
        companions = (("specfreeze --check", "frozen.dfy"), ("witness", "witness.dfy"),
                      ("swap-to-false", "swap.dfy"))
        wanted += [inst for inst, name in companions if posixpath.join(d, name) in files]
    else:
        if f"{t}/frozen.rs" in files:
            wanted.append("specfreeze --check")
        for inst, sub in (("witness", "witness"), ("swap-to-false", "swapped")):
            if any(f.startswith(f"{t}/{sub}/") for f in files):
                wanted.append(inst)
    results = {inst: call(inst, delivery.target) for inst in wanted}
    return GateResult(delivery.id, classify(results), results)
# triv: return GateResult(delivery.id, GateVerdict(PASS, ()), {})


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
    detected, held, false_pass, fp, controls = {}, 0, 0, 0, 0
    for r in results:
        if r.id not in labels:
            raise ValueError(f"{r.id}: no label")
        lab = labels[r.id]
        if lab.kind == "construct":
            detected.setdefault(lab.xclass, 0)
            if r.verdict.word == FAIL:
                detected[lab.xclass] += 1
            elif lab.xclass in r.verdict.unknown:
                held += 1
            else:
                false_pass += 1
        elif lab.kind == "control":
            controls += 1
            if r.verdict.word == FAIL:
                fp += 1
    return Report(detected, held, false_pass, fp, controls, stats.wilson_interval(fp, controls))
# triv: return Report({}, 0, 0, 0, 0, (0.0, 1.0))


if __name__ == "__main__":
    sys.exit(main())
