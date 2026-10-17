"""Q12 — Lab 1: the analysis tables (Reference Solution)

Hole-free reference for `harness/q/fvh_q/report.py` (author-only; never
learner-visible). Same names, signatures, docstrings, item markers and order
as the exercise file. Every hole is filled; each H item declares its `# triv:`
body for the Python TRIV mode. The acceptance tests
(harness/tests/q/test_report.py) run on synthetic rows; Lab 1's rows come
from `fvh.runlog`, which DV4 step 1a builds (Solutions/plans/Q12-code-notes.md
§6 records the row interface it must give).
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
    arms = tuple(arms)
    if not arms:
        raise ValueError("no arm to tabulate")
    if len(set(arms)) != len(arms):
        raise ValueError("an arm is named twice")
    cells = {arm: {} for arm in arms}
    truncated = {arm: 0 for arm in arms}
    for row in records:
        arm = row.record.arm
        if arm not in cells:
            continue
        key = (row.record.task_id, row.repeat)
        cells[arm][key] = cells[arm].get(key, False) or row.record.success
        if row.outcome.startswith("truncated:"):
            truncated[arm] += 1
    every = set().union(*(set(c) for c in cells.values()))
    keys = tuple(sorted(k for k in every if all(k in cells[arm] for arm in arms)))
    unpaired = tuple(sorted(every - set(keys)))
    solved = {arm: tuple(cells[arm][k] for k in keys) for arm in arms}
    got = dict(excluded or {})
    return PairedTable(arms, keys, solved, truncated, unpaired,
                       {arm: int(got.get(arm, 0)) for arm in arms})
# triv: return PairedTable(tuple(arms), (), {arm: () for arm in arms}, {arm: 0 for arm in arms}, (), {arm: 0 for arm in arms})


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
    family = [tuple(pair) for pair in family]
    for arm in {a, b} | {x for pair in family for x in pair}:
        if arm not in table.solved:
            raise ValueError(f"the table holds no arm {arm!r}")
    if (a, b) not in family:
        raise ValueError(f"({a}, {b}) is not a pre-registered comparison")
    if not table.keys:
        raise ValueError("the table has no paired cell")
    vals = {arm: [1.0 if s else 0.0 for s in table.solved[arm]] for arm in table.solved}
    ps = [stats.permutation_test(vals[x], vals[y], paired=True, seed=seed) for x, y in family]
    rejects = stats.holm(ps)
    xa, xb = vals[a], vals[b]
    diffs = [u - v for u, v in zip(xa, xb)]
    n = len(diffs)
    by_repeat = {}
    for r in sorted({rep for _, rep in table.keys}):
        idx = [i for i, (_, rep) in enumerate(table.keys) if rep == r]
        disc_b = sum(1 for i in idx if xa[i] == 1.0 and xb[i] == 0.0)
        disc_c = sum(1 for i in idx if xa[i] == 0.0 and xb[i] == 1.0)
        by_repeat[r] = stats.mcnemar(disc_b, disc_c)
    rate_a, rate_b = sum(xa) / n, sum(xb) / n
    k = family.index((a, b))
    return Comparison(a, b, n, rate_a, rate_b, rate_a - rate_b,
                      stats.bootstrap_ci(diffs, seed=seed), ps[k], rejects[k], by_repeat)
# triv: return Comparison(a, b, 0, 0.0, 0.0, 0.0, (0.0, 0.0), 1.0, False, {})
