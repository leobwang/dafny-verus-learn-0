"""Q06 — The machine and the verifier loop: run records and statistics (Exercises, Python)

Commit this module's predictions (P7 and P9 below, and the rest of Q06's)
BEFORE you open the frozen core (harness/fvh/) or the acceptance tests
(harness/tests/): they state the estimators that P7 and P9 ask about.

Imports: the Python standard library and the frozen core `fvh` (harness/fvh/:
fvh.stats, fvh.records, fvh.holes), nothing else. The core is frozen and
complete; read it (after your predictions), never edit it. Statistics code
lives only in the core: here you compose fvh.stats, and never re-derive an
interval or an estimator.

How to work this file:
1. Predictions first: P7 and P9 (the prediction block below; their answers go
   in slots/Q06.slots), with every other prediction of the module (the Dafny
   file's prediction block lists them); record the first tries with
   `scripts/firsttry.sh Q06 --check` before you run anything they are about.
2. Replace each hole. A Python hole is a function whose body, after its
   docstring, is the one statement `raise NotImplementedError("<item id>")`;
   the tools count holes on the syntax tree, never by searching the text.
3. Run the acceptance tests (harness/tests/q/test_q06_stats.py, frozen):
   `scripts/vcheck harness/q/fvh_q/q06_stats.py`, or, from the checkout root,
   `uv run --directory harness pytest tests/q/test_q06_stats.py`.
4. Done = `scripts/vcheck --gate harness/q/fvh_q/q06_stats.py` exits 0 (zero
   holes and every acceptance test passing), AND
   `scripts/firsttry.sh Q06 --report --strict` exits 0.
5. Stuck for 20 minutes? /tutor Q06.

This file ships with exactly 3 holes: H5, H6 and H7, each counted from the
syntax tree. Commit every prediction BEFORE you run anything it is about, open
later files, or read CI, the registry or the plan: their checks and headers
give some predictions away.

Item kinds and the slot protocol are in the Dafny file's header
(dafny/Q/Q06_Machine/std/Q06_Machine.dfy). A verdict switch here is a comment:
`# SLOT: CHECK P7py` becomes `# CHECK P7py` once the first try is recorded.
"""

from collections.abc import Sequence

from fvh import stats
from fvh.records import RunRecord

# =============================================================================
# The prediction block. Commit every prediction of this module before you read
# past this block, and record the first tries:
#     scripts/firsttry.sh Q06 --check
# Verdict answers go in slots/Q06.slots (`P7py = ???` → `P7py = "<answer>"`).
# =============================================================================

# item: Q06.P7py S13 verdict
# **P7.** A prover closes 14 of 20 goals. Which is closest to the half-width
# of the 95% Wilson interval of its success rate:
#   a) 2 pp   b) 10 pp   c) 20 pp   d) 40 pp ?
# Answer form: one letter, `a`, `b`, `c` or `d`.
# SLOT: CHECK P7py

# item: Q06.P9py S13 verdict
# **P9.** A task sampled 10 times is solved in 3 of the samples. Which is
# closest to the unbiased pass@5 estimate for that task:
#   a) 0.30   b) 0.83   c) 0.92   d) 1.00 ?
# Answer form: one letter, `a`, `b`, `c` or `d`.
# SLOT: CHECK P9py

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
    raise NotImplementedError("Q06.H5py")
# Hint: every field of the record comes from one key of the document or one argument;
#    only two of them need a count.


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
    raise NotImplementedError("Q06.H6py")
# Hint(1): fvh.records has a helper that keeps the attempt-1 records.
# Hint(2): fvh.stats.wilson_interval takes the successes, the number of tasks and the
#    confidence.


# item: Q06.H7py S13
def pass_at_k_by_task(records: Sequence[RunRecord], arm: str, k: int) -> float:
    """**H7.** The mean over the tasks of `arm` of the unbiased pass@k.

    Every record of `arm` is one sample of its task (all attempts count here,
    unlike a pass rate): a task's n is its number of records and its c the
    number of them that are successes (`RunRecord.success`). Returns the mean,
    over the arm's tasks, of each task's pass@k, by composing `fvh.stats`.
    Raises ValueError for an arm with no records.
    """
    raise NotImplementedError("Q06.H7py")
# Hint(1): group the arm's records by task first.
# Hint(2): fvh.stats.pass_at_k(n, c, k) for each task, then the plain mean.
