"""Q31 — Gate & bench: the eval harness (Challenge, solo; Python)

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
def load_runs(root, module: str, *, batches: Sequence[str] = ()) -> list[RunRow]:
    """**H9py.** The scored attempts of the module's batches (all when empty),
    from run.json and the re-judging records; an infra-failed attempt is not a row."""
    raise NotImplementedError("Q31.H9py")


# item: Q31.H10py S13
def pass_at_k_table(rows: Sequence[RunRow], ks: Sequence[int]) -> Table:
    """**H10py.** Unbiased pass@k per (arm, stratum, lang, k) with n >= 2k samples
    per task (stats.pass_at_k), its interval (Wilson at k = 1, else the bootstrap with
    seed 0)."""
    raise NotImplementedError("Q31.H10py")


# item: Q31.H11py S13
def cost_curve(rows: Sequence[RunRow], axis: str, budgets: Sequence[float]) -> Curve:
    """**H11py.** Solves versus cost on one axis, with bootstrap bands (seed 0)."""
    raise NotImplementedError("Q31.H11py")


# item: Q31.H12py S13
def paired_report(rows: Sequence[RunRow], a: str, b: str, *, family: Sequence[float] = (),
                  alpha: float = 0.05) -> PairedReport:
    """**H12py.** Arms a and b on their common tasks (repeat 0): McNemar, Holm
    over `family` (the other p-values of the pre-registered family) and the MDE."""
    raise NotImplementedError("Q31.H12py")


# item: Q31.H13py S13
def render(tables: Sequence[object]) -> str:
    """**H13py.** The deterministic text of the tables (sorted keys, fixed number
    formats): byte-identical for the same records."""
    raise NotImplementedError("Q31.H13py")
