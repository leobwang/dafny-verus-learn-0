"""Q31 — Gate & bench: the eval harness (the REFERENCE twin; author-only) (Challenge, solo; Python)

Solo work (guard rule 2s). Reads fvh run records only (research/runs/<ID>/, written
by fvh) and writes deterministic tables, composing fvh.stats: never re-derive an
estimator (the import lint's stats-reimplementation rule). Its interface is frozen
(Q31_Statement.toml); the bodies are yours.

The grader's bench-agree mode runs your frozen bench over the held-out run's records
(both arms: your baselines and the course's par agent, D68) and compares its tables
cell by cell with the course's reference tables over the same records.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from fvh import stats

__all__ = ["Curve", "PairedReport", "RunRow", "Table", "cost_curve", "load_runs",
           "paired_report", "pass_at_k_table", "render"]

AXES = ("calls", "tokens", "wall_s", "gpu_s")


@dataclass(frozen=True)
class RunRow:
    """One scored attempt: arm, task, stratum ("course-local" | "public"), language,
    repeat, solved (re-judged by the gate), and its cost on each axis of AXES at the
    first success (or in total when unsolved)."""

    arm: str
    task: str
    stratum: str
    lang: str
    repeat: int
    solved: bool
    cost: Mapping[str, float]


@dataclass(frozen=True)
class Table:
    """rows: (arm, stratum, lang, k) -> (estimate, (lo, hi)); n_tasks per key."""

    rows: Mapping[tuple, tuple]
    n_tasks: Mapping[tuple, int]


@dataclass(frozen=True)
class Curve:
    """solved share after b units of `axis`, with a bootstrap band, per arm."""

    axis: str
    points: Mapping[str, tuple]


@dataclass(frozen=True)
class PairedReport:
    """Two arms on the same tasks: discordant counts b, c, the two-sided McNemar
    p-value, the Holm decision within the declared family, and the MDE at n."""

    a: str
    b: str
    n: int
    discordant: tuple[int, int]
    p_value: float
    rejected: bool
    mde: float


# item: Q31.H9py S13


# triv: return []
def load_runs(root, module: str, *, arms: Sequence[str] = (),
              strata: Mapping[str, str] | None = None) -> list[RunRow]:
    """**H9py.** The scored attempts of research/runs/<module>/ (fvh.runlog: run.json;
    an unscored run, infra-failed or deferred, is not a row), of the named arms (all when
    empty), sorted by (arm, task, repeat). `solved` is the outcome "verified"; `cost` is
    the run's usage on each axis of AXES (a run stops at its first success); `stratum`
    is strata[task] ("course-local" or "public"; "unknown" when strata does not name it)."""
    from fvh import runlog
    strata = strata or {}
    out = []
    for d in runlog.run_dirs(root, module):
        meta = runlog.load_meta(d / "run.json")
        if runlog.to_run_record(meta) is None or (arms and meta.arm not in arms):
            continue
        cost = {ax: float(meta.usage.get(ax, 0) or 0) for ax in AXES}
        out.append(RunRow(meta.arm, meta.task_id, strata.get(meta.task_id, "unknown"), meta.lang,
                          meta.repeat, meta.outcome == "verified", cost))
    return sorted(out, key=lambda r: (r.arm, r.task, r.repeat))


# item: Q31.H10py S13


# triv: return Table({}, {})
def pass_at_k_table(rows: Sequence[RunRow], ks: Sequence[int]) -> Table:
    """**H10py.** Unbiased pass@k per (arm, stratum, lang, k): for each task the
    estimator stats.pass_at_k(n, c, k) over its n samples (rows) with c solved, averaged
    over the tasks of the key. A task with n < 2k samples raises ValueError (pass@k needs
    n >= 2k here; one sample suffices for k == 1). The interval: Wilson (stats.wilson_interval) on solved tasks when k == 1
    and every task of the key has exactly one sample; otherwise stats.bootstrap_ci over the
    per-task estimates with seed 0. n_tasks holds each key's number of tasks."""
    groups = {}
    for r in rows:
        groups.setdefault((r.arm, r.stratum, r.lang), {}).setdefault(r.task, []).append(r.solved)
    out, ntasks = {}, {}
    for key, tasks in groups.items():
        for k in ks:
            ests = []
            for t, s in sorted(tasks.items()):
                if len(s) < 2 * k and not (k == 1 and len(s) == 1):
                    raise ValueError(f"{t}: {len(s)} samples; pass@{k} needs n >= {2 * k}")
                ests.append(stats.pass_at_k(len(s), sum(s), k))
            est = sum(ests) / len(ests)
            if k == 1 and all(len(s) == 1 for s in tasks.values()):
                ci = stats.wilson_interval(sum(s[0] for s in tasks.values()), len(tasks))
            else:
                ci = stats.bootstrap_ci(ests, seed=0)
            out[key + (k,)] = (est, ci)
            ntasks[key + (k,)] = len(tasks)
    return Table(out, ntasks)


# item: Q31.H11py S13


# triv: return Curve(axis, {})
def cost_curve(rows: Sequence[RunRow], axis: str, budgets: Sequence[float]) -> Curve:
    """**H11py.** Solves versus cost on one axis (one of AXES; another raises
    ValueError): for each arm and each budget b (in the given order), the share of the
    arm's rows that are solved with cost[axis] <= b, and stats.bootstrap_ci of that share
    over the rows (seed 0). points: arm -> tuple of (b, share, (lo, hi))."""
    if axis not in AXES:
        raise ValueError(f"axis {axis!r} is not one of {', '.join(AXES)}")
    by = {}
    for r in rows:
        by.setdefault(r.arm, []).append(r)
    pts = {}
    for arm, rs in sorted(by.items()):
        line = []
        for b in budgets:
            ind = [1.0 if (r.solved and r.cost.get(axis, 0) <= b) else 0.0 for r in rs]
            line.append((b, sum(ind) / len(ind), stats.bootstrap_ci(ind, seed=0)))
        pts[arm] = tuple(line)
    return Curve(axis, pts)


# item: Q31.H12py S13


# triv: return PairedReport(a, b, 0, (0, 0), 1.0, False, 1.0)
def paired_report(rows: Sequence[RunRow], a: str, b: str, *, family: Sequence[float] = (),
                  alpha: float = 0.05) -> PairedReport:
    """**H12py.** Arms a and b on their common tasks, each task's lowest repeat:
    the discordant counts (b solved only by a, c only by b), the two-sided stats.mcnemar
    p-value (1.0 when b + c == 0), `rejected` = the first decision of stats.holm over
    [p] + family at alpha, and the MDE stats.mde_two_proportions(n, p0, alpha=alpha,
    paired=True) with p0 the share of arm b solved, held to [0.01, 0.99]. No common task
    raises ValueError."""
    def first(arm):
        best = {}
        for r in rows:
            if r.arm == arm and (r.task not in best or r.repeat < best[r.task].repeat):
                best[r.task] = r
        return best
    ra, rb = first(a), first(b)
    common = sorted(set(ra) & set(rb))
    if not common:
        raise ValueError(f"arms {a} and {b} share no task")
    nb = sum(1 for t in common if ra[t].solved and not rb[t].solved)
    nc = sum(1 for t in common if rb[t].solved and not ra[t].solved)
    p = stats.mcnemar(nb, nc) if nb + nc else 1.0
    rejected = stats.holm([p, *family], alpha)[0]
    p0 = min(0.99, max(0.01, sum(rb[t].solved for t in common) / len(common)))
    mde = stats.mde_two_proportions(len(common), p0, alpha=alpha, paired=True)
    return PairedReport(a, b, len(common), (nb, nc), p, rejected, mde)


# item: Q31.H13py S13


# triv: return ""
def render(tables: Sequence[object]) -> str:
    """**H13py.** The deterministic text: one line per Table key ("pass", arm,
    stratum, lang, k, estimate, lo, hi), per Curve point ("curve", axis, arm, b, share, lo,
    hi) and per PairedReport ("paired", a, b, n, b, c, p, rejected, mde), tab-separated,
    floats as %.4f, lines sorted; the same records always give the same bytes."""
    lines = []
    f = "%.4f"
    for t in tables:
        if isinstance(t, Table):
            for key, (est, (lo, hi)) in t.rows.items():
                lines.append("\t".join(["pass", *map(str, key), f % est, f % lo, f % hi]))
        elif isinstance(t, Curve):
            for arm, pts in t.points.items():
                for b, share, (lo, hi) in pts:
                    lines.append("\t".join(["curve", t.axis, arm, f % b, f % share, f % lo, f % hi]))
        elif isinstance(t, PairedReport):
            lines.append("\t".join(["paired", t.a, t.b, str(t.n), str(t.discordant[0]),
                                    str(t.discordant[1]), f % t.p_value, str(t.rejected),
                                    f % t.mde if t.mde != float("inf") else "inf"]))
        else:
            raise TypeError(f"render takes Tables, Curves and PairedReports, not {type(t).__name__}")
    return "\n".join(sorted(lines)) + ("\n" if lines else "")
