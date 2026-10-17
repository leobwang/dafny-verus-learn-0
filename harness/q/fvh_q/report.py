"""Q12 — Lab 1: the analysis tables (Exercises, Python)

The learner's half of Lab 1's report (DV4-PLAN §14, its sixth question: the frozen `fvh
report` reproduces outcomes from the logs, re-checks the ledger and prints
the apparatus and disclosure block; the analysis tables are yours). Your
report (paper/Q12_answers.tex, B2) prints these tables, and `fvh report Q12`
must reproduce every one of them from research/runs/Q12/.

Lab 1's rows come from the run log, `fvh.runlog` (DV4-PLAN §3.6:
`runlog.split` gives the scored records and the exclusions per arm), and
they exist only after the lab's runs (the live batch runner, `python -m fvh
run`, writes them). The functions here take plain rows (LabRun, below) and
need nothing from the run log, so their acceptance tests run now, on
synthetic rows.

Imports: the Python standard library and the frozen core `fvh`
(harness/fvh/: fvh.records, fvh.stats), nothing else. Statistics code lives
only in the core: compose fvh.stats, never re-derive an interval or a test.

How to work this file:
1. Replace each hole, in order: H12, then H13. A Python hole is a function
   whose body, after its docstring, is the one statement
   `raise NotImplementedError("<item id>")`.
2. Run the acceptance tests (harness/tests/q/test_report.py, frozen;
   synthetic rows only): `scripts/vcheck harness/q/fvh_q/report.py`.
3. Done = `scripts/vcheck --gate harness/q/fvh_q/report.py` exits 0.
4. Stuck for 20 minutes? /tutor Q12.

This file ships with exactly 2 holes: H12 and H13, each counted from the
syntax tree.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from fvh import stats
from fvh.records import RunRecord

# =============================================================================
# Given (frozen statements: expected/Q12.freeze pins them). Read them, never
# change them.
# =============================================================================


@dataclass(frozen=True)
class LabRun:
    """One scored attempt of the lab: its run record (fvh.records.RunRecord:
    task_id, arm, attempt, lang, verdict, holes, errors, verified_count), the
    repeat it belongs to (1, 2, 3, …) and its outcome as the run log gives it
    (RunMeta.outcome, DV4-PLAN §3.6): a verdict word, "malformed", or
    "truncated:<cause>". Exclusions (infra-failed attempts, which have no
    record) are not rows: the report driver counts them per arm."""

    record: RunRecord
    repeat: int
    outcome: str


@dataclass(frozen=True)
class PairedTable:
    """Solved within the budget, per (task, repeat) cell and arm.

    arms       the arms, in the order asked for
    keys       the (task, repeat) cells that every arm has, sorted
    solved     arm -> one bool per key, in key order: some attempt of that
               arm on that cell succeeded (RunRecord.success)
    truncated  arm -> the number of its rows whose outcome is
               "truncated:<cause>" (counted as failures here, the primary
               analysis; the sensitivity line leaves them out)
    unpaired   the cells some arm lacks, sorted (they are left out of keys)
    excluded   arm -> the exclusions the driver reported for it (0 when none)
    """

    arms: tuple[str, ...]
    keys: tuple[tuple[str, int], ...]
    solved: Mapping[str, tuple[bool, ...]]
    truncated: Mapping[str, int]
    unpaired: tuple[tuple[str, int], ...]
    excluded: Mapping[str, int]


@dataclass(frozen=True)
class Comparison:
    """One pre-registered comparison of arm `a` against arm `b`.

    n                  the number of paired cells
    rate_a, rate_b     each arm's solved rate over them
    diff               rate_a - rate_b
    interval           the 95% percentile bootstrap interval of the mean
                       paired difference (fvh.stats.bootstrap_ci)
    p                  the two-sided paired permutation p-value of the
                       difference (fvh.stats.permutation_test)
    holm_reject        whether Holm's procedure over the whole family
                       rejects this comparison (fvh.stats.holm, alpha 0.05)
    mcnemar_by_repeat  repeat -> McNemar's exact p-value over that repeat's
                       cells (fvh.stats.mcnemar): the sensitivity line
    """

    a: str
    b: str
    n: int
    rate_a: float
    rate_b: float
    diff: float
    interval: tuple[float, float]
    p: float
    holm_reject: bool
    mcnemar_by_repeat: Mapping[int, float]


# =============================================================================
# Holes
# =============================================================================

# item: Q12.H12py S13
def paired_table(records: Sequence[LabRun], arms: Sequence[str], *,
                 excluded: Mapping[str, int] | None = None) -> PairedTable:
    """**H12.** The paired table of the arms named in `arms` (the rows of
    any other arm are left out).

    A cell is the pair (task_id, repeat) of a row; an arm has a cell when it
    has at least one row there, and solves it when at least one of those
    rows' records is a success. `keys` are the cells every named arm has,
    sorted; the others go to `unpaired`, sorted. `truncated` counts each
    named arm's rows whose outcome starts with "truncated:", over all its
    rows (paired or not). `excluded` copies the driver's counts for the
    named arms, 0 for an arm it does not name. Raises ValueError for an
    empty `arms` or a repeated arm.
    """
    raise NotImplementedError("Q12.H12py")


# item: Q12.H13py S13
def compare(table: PairedTable, a: str, b: str, *,
            family: Sequence[tuple[str, str]], seed: int) -> Comparison:
    """**H13.** Arm `a` against arm `b` over the table's paired cells, by
    composing fvh.stats only.

    The paired differences are, per key, 1 when only `a` solved, -1 when
    only `b` did, else 0. `interval` is fvh.stats.bootstrap_ci of their
    mean with this `seed`; `p` is fvh.stats.permutation_test of the two
    arms' 0/1 outcomes, paired, with this `seed`. Holm runs over the
    `family` (the pre-registered comparisons, each an (a, b) pair of the
    table's arms; (a, b) must be one of them): every member's p-value is
    computed the same way, and `holm_reject` is this comparison's entry of
    fvh.stats.holm over them, in family order. `mcnemar_by_repeat` gives,
    for each repeat among the keys, fvh.stats.mcnemar of the discordant
    counts over that repeat's cells (b: `a` solved and `b` did not; c: the
    reverse). Raises ValueError for an arm the table does not hold, for
    (a, b) outside the family, and for a table with no paired cell.
    """
    raise NotImplementedError("Q12.H13py")
