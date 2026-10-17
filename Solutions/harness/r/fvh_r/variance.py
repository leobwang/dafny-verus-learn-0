"""R05 — No goal state (Reference Solution, Python).

Commit all four R05 predictions before reading these tests or running the
measurement specimens. Two syntax-tree-counted holes compose the frozen
statistics core; do not implement a bootstrap estimator here.

One UTF-8 JSON object per line is one `scripts/vcheck --json --measures`
document from a single target. Keep tasks/languages in separate logs when
summarising; never silently combine different experiments. Extra wrapper
fields are allowed. Every row must contain `wall_s`, `resource_count` and
`verdict`: wall_s is a finite nonnegative number, resource_count is a finite
nonnegative number or null (unavailable), and verdict is one of the wrapper's
six verdicts below. Booleans are not measurements. Blank lines, missing keys,
non-objects, invalid JSON and invalid values are malformed; raise ValueError
with the one-based line number. Preserve row order; an empty file gives [].
OSError from opening the path propagates. Counts may be absent at a tool pin;
null means unavailable and never zero.

Run the frozen tests through scripts/vcheck --gate harness/r/fvh_r/variance.py.
The source's two holes intentionally fail acceptance. Done includes a clean
audit, unchanged signatures and the module's written measurement discussion.
"""
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
import json
import math
import statistics
from fvh import stats

VERDICTS = frozenset(("verified", "failed", "inconclusive", "refused", "killed(memory)", "error"))

@dataclass(frozen=True)
class TimingRun:
    wall_s: float
    resource_count: float | None
    verdict: str

@dataclass(frozen=True)
class Summary:
    n: int
    mean: float
    cv: float
    interval: tuple[float, float]

# item: R05.H1py
def runs_from_log(path: Path) -> list[TimingRun]:
    """Read the exact row schema above, preserving every verdict and order.

    Use json.loads for each line. Error messages identify the one-based line;
    parsing failure must never drop a failed run or return a partial prefix.
    """
    rows = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            doc = json.loads(line)
            if not isinstance(doc, dict):
                raise ValueError("expected object")
            wall, count, verdict = doc["wall_s"], doc["resource_count"], doc["verdict"]
            for value in (wall,) + (() if count is None else (count,)):
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError("measurement is not numeric")
                if not math.isfinite(value) or value < 0:
                    raise ValueError("measurement is not finite/nonnegative")
            if not isinstance(verdict, str) or verdict not in VERDICTS:
                raise ValueError("unknown verdict")
            rows.append(TimingRun(float(wall), None if count is None else float(count), verdict))
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            raise ValueError(f"line {lineno}: malformed measurement") from exc
    return rows
# triv: return []

# item: R05.H2py
def variance_summary(runs: Sequence[TimingRun], field: str, *, seed: int) -> Summary:
    """Summarise wall_s or resource_count for at least two comparable runs.

    ValueError for fewer than two runs, another field, an unavailable value,
    or a nonnumeric/bool/nonfinite/negative value. Use statistics.fmean and
    statistics.stdev (sample standard deviation); CV is stdev/mean. All-zero
    measurements have CV 0. Compose fvh.stats.bootstrap_ci(values,
    statistics.fmean, seed=seed), whose default interval is 95 percent.
    A summary includes every supplied run, including a failed verdict. Filter
    or stratify intentionally before calling; a bootstrap interval estimates
    this sample's mean under its sampling assumptions, not a bound on the next
    verifier invocation. It does not establish proof correctness.
    """
    if field not in ("wall_s", "resource_count") or len(runs) < 2:
        raise ValueError("need a supported field and at least two runs")
    values = []
    for run in runs:
        value = getattr(run, field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("unavailable/non-numeric measurement")
        if not math.isfinite(value) or value < 0:
            raise ValueError("measurement is not finite/nonnegative")
        values.append(float(value))
    mean = statistics.fmean(values)
    cv = statistics.stdev(values) / mean if mean else 0.0
    interval = stats.bootstrap_ci(values, statistics.fmean, seed=seed)
    return Summary(len(values), mean, cv, interval)
# triv: return Summary(0, 0.0, 0.0, (0.0, 0.0))
