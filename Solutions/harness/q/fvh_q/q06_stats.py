"""Q06 — The machine and the verifier loop: run records and statistics (Reference Solution)

Hole-free reference for `harness/q/fvh_q/q06_stats.py` (author-only; never
learner-visible). Same names, signatures, docstrings, item markers and order
as the exercise file (one more import from fvh.records). Every hole is filled; the verdict switches are
enabled, and the verdict answers are in `Solutions/slots/Q06.slots`, their
hashes in `expected/Q06.pins`. Each H item declares, on a `# triv:` line after
its function, the trivial body that the Python TRIV mode of
`scripts/firsttry.sh Q06 --empty-body` lays over this reference: the
acceptance tests must reject each one (QPLAN §11.8).

The tools run this file only by overlay: `scripts/dvl/python.py` copies
harness/ to scratch, lays this twin over its learner path and runs
harness/tests/q/test_q06_stats.py there.
"""

from collections.abc import Sequence

from fvh import stats
from fvh.records import RunRecord, first_attempts

# =============================================================================
# The prediction block.
# =============================================================================

# item: Q06.P7py S13 verdict
# **P7.** A prover closes 14 of 20 goals. Which is closest to the half-width
# of the 95% Wilson interval of its success rate:
#   a) 2 pp   b) 10 pp   c) 20 pp   d) 40 pp ?
# Answer form: one letter, `a`, `b`, `c` or `d`.
# CHECK P7py

# item: Q06.P9py S13 verdict
# **P9.** A task sampled 10 times is solved in 3 of the samples. Which is
# closest to the unbiased pass@5 estimate for that task:
#   a) 0.30   b) 0.83   c) 0.92   d) 1.00 ?
# Answer form: one letter, `a`, `b`, `c` or `d`.
# CHECK P9py

# =============================================================================
# Holes
# =============================================================================

# item: Q06.H5py S9
def record_from_vcheck(doc: dict, task_id: str, arm: str, attempt: int) -> RunRecord:
    """**H5.** The run record of one `scripts/vcheck --json` document.

    `doc` is the JSON object vcheck prints for one target. Its keys include
    `lang`, `verdict`, `stage`, `exit_code`, `verified_count` (a number, or
    null when the run printed none), `holes` (a list, one entry per
    tool-counted hole) and `diagnostics` (a list of objects, each with a
    `severity`: error, warning, info, hint or related). The record takes:

      task_id, arm, attempt   as given;
      lang, verdict           copied from the document;
      holes                   the number of entries of `holes`;
      errors                  the number of diagnostics whose severity is `error`;
      verified_count          the document's count, 0 when it is null.
    """
    errors = sum(1 for d in doc["diagnostics"] if d["severity"] == "error")
    count = doc["verified_count"]
    return RunRecord(task_id=task_id, arm=arm, attempt=attempt, lang=doc["lang"],
                     verdict=doc["verdict"], holes=len(doc["holes"]), errors=errors,
                     verified_count=0 if count is None else count)
# triv: return RunRecord(task_id, arm, attempt, "", "verified", 0, 0, 0)


# item: Q06.H6py S13
def pass_rate_ci(records: Sequence[RunRecord], arm: str,
                 confidence: float = 0.95) -> tuple[int, int, tuple[float, float]]:
    """**H6.** First-attempt successes, the number of tasks, and the Wilson interval.

    Only the records of `arm` count, and each of its tasks enters once,
    through its first attempt (its attempt-1 record, wherever it sits in
    `records`); a record is a success as `RunRecord.success` defines it.
    Returns `(successes, tasks, (lo, hi))`, the interval at `confidence`, by
    composing `fvh.stats`. Raises ValueError for an arm with no records: the
    Wilson interval is undefined at n = 0.
    """
    first = first_attempts([r for r in records if r.arm == arm])
    if not first:
        raise ValueError(f"arm {arm!r} has no first-attempt record")
    successes = sum(1 for r in first if r.success)
    return successes, len(first), stats.wilson_interval(successes, len(first), confidence)
# triv: return (0, 0, (0.0, 1.0))


# item: Q06.H7py S13
def pass_at_k_by_task(records: Sequence[RunRecord], arm: str, k: int) -> float:
    """**H7.** The mean over the tasks of `arm` of the unbiased pass@k.

    Every record of `arm` is one sample of its task (all attempts count here,
    unlike a pass rate): a task's n is its number of records and its c the
    number of them that are successes (`RunRecord.success`). Returns the mean,
    over the arm's tasks, of each task's pass@k, by composing `fvh.stats`.
    Raises ValueError for an arm with no records.
    """
    by_task: dict[str, list[RunRecord]] = {}
    for r in records:
        if r.arm == arm:
            by_task.setdefault(r.task_id, []).append(r)
    if not by_task:
        raise ValueError(f"arm {arm!r} has no record")
    values = [stats.pass_at_k(len(rs), sum(1 for r in rs if r.success), k)
              for rs in by_task.values()]
    return sum(values) / len(values)
# triv: return 0.0
