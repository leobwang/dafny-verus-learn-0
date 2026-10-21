"""Q31 — Gate & bench: gate v3, the gate at task scale (Challenge, solo; Python)

This file is solo work (guard rule 2s): no contract allowlist may name it and no
assistant edits it; /tutor coaches it at rung 2 at most. It extends YOUR Q18 gate v2
(harness/q/fvh_q/gate/gate_v2.py) by composition: it imports gate v2's frozen types
and its gate_crate, and adds what a benchmark gate needs beyond a crate gate. Its
interface below is frozen (Q31_Statement.toml pins each signature's hash); the bodies
are yours.

Imports (the py-agents tier): the standard library, `fvh` (fvh.tools, fvh.stats,
fvh.verdicts, fvh.runlog), `fvh_q` (your Q09 and Q18 gates) and nothing else. Two rules
carry over: an instrument runs only through fvh.tools.run (never a subprocess, a
`cargo build` or `cargo test`: V20), and statistics live only in fvh.stats.

Holes: one per item block (`# item:` markers), each `raise NotImplementedError("<id>")`, counted
from the syntax tree. Done: `scripts/challenge_gate.sh Q31` (its eight checks, the
frozen tests under harness/tests/challenges/q31_gate_bench/, the grader record).

The names fvh.batch's gated arm imports (gate_crate, CrateTarget, Pins, render) stay
here, so Q32's gated arm can use this gate as its acceptance tool.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from fvh import tools, verdicts
from fvh_q.gate.gate_v2 import (CrateTarget, Finding, GateResult, GateVerdict, Label, Pins,
                                Spread, render)
from fvh_q.gate import gate_v2

__all__ = ["AgreementReport", "CrateTarget", "Finding", "GateResult", "Pins", "TaskTarget",
           "agreement_report", "gate_crate", "lever_findings", "reach_findings", "render",
           "run_record_findings", "solver_spread", "statement_identity"]

LABEL = "solver diversity and seed variation: not independent checking"


@dataclass(frozen=True)
class TaskTarget:
    """One benchmark delivery: gate v2's CrateTarget plus what a task adds.

    crate        the CrateTarget gate v2 runs (a Dafny root file or a Verus crate)
    statement    the task's frozen statement file (repo-relative), or "" for none
    task_form    the task form the delivery was made from (the lab gate's lever
                 check compares against it), or "" for none
    editable     the files the task let a policy edit (repo-relative)
    """

    crate: CrateTarget
    statement: str
    task_form: str
    editable: tuple[str, ...]


@dataclass(frozen=True)
class AgreementReport:
    """The evaluator's account of gate v3 against the trusted instruments.

    agree, disagree    X class -> deliveries on which the gate's word matched / did not
                       match the trusted instruments' (decidable classes only)
    unknown_held       grader-only deliveries (X07, X08, X14) the gate held as UNKNOWN
    unknown_passed     grader-only deliveries the gate passed (always a failure)
    false_rejects      honest deliveries the gate failed
    honest             the number of honest deliveries
    fp_interval        the 95 % Wilson interval of false_rejects / honest (fvh.stats)
    """

    agree: Mapping[str, int]
    disagree: Mapping[str, int]
    unknown_held: int
    unknown_passed: int
    false_rejects: int
    honest: int
    fp_interval: tuple[float, float]


# =============================================================================
# Holes (your code)
# =============================================================================

# item: Q31.H1py S12
def gate_crate(target: CrateTarget, *, run=None) -> GateResult:
    """**H1py.** Gate v3 on a crate-scale delivery: gate v2's verdict
    (gate_v2.gate_crate) and then, on a v2 PASS, solver_spread and reach_findings;
    any v3 finding turns the word to FAIL with its reason; UNKNOWN on the grader-only
    classes is kept, never dropped (verdicts.GRADER_ONLY)."""
    raise NotImplementedError("Q31.H1py")


# item: Q31.H2py S12
def gate_task(target: TaskTarget, *, run=None, run_dir=None) -> GateResult:
    """**H2py.** Gate v3 on a benchmark delivery: gate_crate on target.crate, plus
    statement_identity, lever_findings and, when run_dir names the fvh run that made
    the delivery, run_record_findings."""
    raise NotImplementedError("Q31.H2py")


# item: Q31.H3py S12
def statement_identity(target: TaskTarget, *, run=None) -> list[Finding]:
    """**H3py.** The task's frozen statement, unchanged, checked in a fresh process
    by the specfreeze --check instrument; [] when the task has no statement."""
    raise NotImplementedError("Q31.H3py")


# item: Q31.H4py S12
def lever_findings(target: TaskTarget, *, root=None) -> list[Finding]:
    """**H4py.** A verification lever, option or project file the delivery adds
    to (or drops from) its task form."""
    raise NotImplementedError("Q31.H4py")


# item: Q31.H5py S12
def solver_spread(target: CrateTarget, *, run=None) -> Spread:
    """**H5py.** The seed sweep, and for Dafny the bundled solvers too
    (instruments seed-rerun and solver-swap); every row must verify. Never call it
    independent checking (LABEL)."""
    raise NotImplementedError("Q31.H5py")


# item: Q31.H6py S12
def reach_findings(target: CrateTarget, *, run=None) -> list[Finding]:
    """**H6py.** The reach instrument's findings (denied names and modules,
    required roots, reference reach)."""
    raise NotImplementedError("Q31.H6py")


# item: Q31.H7py S12
def run_record_findings(run_dir) -> list[Finding]:
    """**H7py.** The run-level classes from an fvh run's records: X15 (a returned
    file outside the editable set, a changed companion), X17 (a read outside the
    readable set, a canary in a transcript), X18 (an argv or apparatus other than the
    pinned one, a tool call in a transcript)."""
    raise NotImplementedError("Q31.H7py")


# item: Q31.H8py S12
def agreement_report(results: Sequence[GateResult], labels: Mapping[str, Label],
                     trusted: Mapping[str, str]) -> AgreementReport:
    """**H8py.** The evaluator, the one function that reads labels: compares each
    delivery's word with the trusted instruments' (trusted: id -> PASS | FAIL), by
    class, and composes fvh.stats.wilson_interval for the false-reject rate."""
    raise NotImplementedError("Q31.H8py")
