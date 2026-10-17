"""Q12 — Practice I-C: the retry client (Reference Solution)

Hole-free reference for `harness/q/fvh_q/retry.py` (author-only; never
learner-visible). Same names, signatures, docstrings, item markers and order
as the exercise file. Every hole is filled. Each H item declares, on a
`# triv:` line after its function, the trivial body that the Python TRIV
mode of `scripts/firsttry.sh Q12 --empty-body` lays over this reference: the
acceptance tests must reject each one (QPLAN §19.0, §11.8).

The tools run this file only by overlay: `scripts/dvl/python.py` copies
harness/ to scratch, lays this twin over its learner path and runs the
module's acceptance tests there (harness/tests/q/test_retry.py; they replay
the results recorded under harness/tests/q/fixtures/q12/rec/ by
Solutions/plans/Q12-record-battery.py, so no solver runs).
"""

import argparse
import sys
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from fvh import tools
from fvh.tools import ToolResult

# =============================================================================
# Given (frozen statements: expected/Q12.freeze pins them). Read them, never
# change them.
# =============================================================================

BATTERY = "harness/tests/q/fixtures/q12/battery.toml"   # repo-relative
LANGS = ("dafny", "verus")


@dataclass(frozen=True)
class Goal:
    """One goal of the battery: its id, its language ("dafny" or "verus")
    and its candidate files (repo-relative paths), in the order to try them."""

    id: str
    lang: str
    candidates: tuple[str, ...]


@dataclass(frozen=True)
class Attempt:
    """What the client did on one goal.

    goal_id  the goal's id
    solved   True when a candidate's run was a complete pass
    tries    the number of candidates run (0 only for a goal with none)
    passed   the candidate that passed, or None
    reasons  one failure reason per failed try, in the order of the tries
             (solve_goal's docstring gives the words); a solved goal's
             passing try adds none
    """

    goal_id: str
    solved: bool
    tries: int
    passed: str | None
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class BatteryReport:
    """The battery's account.

    solved         the number of goals solved
    total          the number of goals
    tries          goal id -> the tries spent on it (every goal is a key)
    first_failure  goal id -> the reason of its first failed try, for every
                   goal that was not solved (and for no other)
    """

    solved: int
    total: int
    tries: Mapping[str, int]
    first_failure: Mapping[str, str]


def course_root() -> Path:
    """The checkout root (this file is harness/q/fvh_q/retry.py)."""
    return Path(__file__).resolve().parents[3]


def load_battery(path=None, *, root=None) -> tuple[Goal, ...]:
    """The goals of a battery file (default BATTERY under the course root),
    in file order. The file holds one `[[goal]]` table per goal, with the
    keys `id`, `lang` and `candidates` (a list of repo-relative paths)."""
    base = Path(root) if root is not None else course_root()
    p = Path(path) if path is not None else base / BATTERY
    with open(p, "rb") as f:
        data = tomllib.load(f)
    goals = []
    for g in data.get("goal", []):
        if g.get("lang") not in LANGS:
            raise ValueError(f"{p}: goal {g.get('id')!r}: lang must be one of {', '.join(LANGS)}")
        goals.append(Goal(str(g["id"]), g["lang"], tuple(str(c) for c in g["candidates"])))
    return tuple(goals)


def main(argv=None) -> int:
    """Your own live check, outside the tests: the client over the battery,
    on the host, one solver job at a time.
        cd harness && PYTHONPATH=q uv run python -m fvh_q.retry --battery
    Prints one line per try (the candidate and the result's exit code and
    verdict), then the solved count and each unsolved goal's first failure.
    Exit 0 once the battery has run (whatever the count)."""
    ap = argparse.ArgumentParser(prog="python -m fvh_q.retry", allow_abbrev=False)
    ap.add_argument("--battery", action="store_true", required=True)
    ap.add_argument("--k", type=int, default=3)
    a = ap.parse_args(argv)

    def shown(instrument, target):
        r = tools.run(instrument, target)
        doc = r.document if isinstance(r.document, dict) else {}
        print(f"  {target}: exit {r.exit_code}, killed {r.killed}, "
              f"verdict {doc.get('verdict')}", flush=True)
        return r

    rep = run_battery(load_battery(), k=a.k, run=shown)
    print(f"solved {rep.solved} of {rep.total}")
    for gid, why in sorted(rep.first_failure.items()):
        print(f"  {gid}: first failure {why}")
    return 0


# =============================================================================
# Holes
# =============================================================================

# item: Q12.H1py S9
def solve_goal(goal: Goal, *, k: int = 3, run=None) -> Attempt:
    """**H1.** Try a goal's candidates in order, at most `k` of them, and stop
    at the first complete pass.

    Each try is one call `run("vcheck --gate", candidate)`, where `run` is
    the argument when it is given, else `fvh.tools.run` looked up at the time
    of the call. The call returns a ToolResult (fvh.tools); judge it from its
    fields and its `document` (the `scripts/vcheck --gate --json` document)
    only. A try's failure reason is the FIRST of these that applies:

      "killed:<cause>"   the run was killed (`killed` is "memory" or
                         "wall-clock"): never a pass, whatever else it says;
      "exit:<n>"         its exit code is neither 0 nor 1 (a usage error or
                         a refusal; <n> the code);
      "no-document"      `document` is not a dict, or lacks one of the keys
                         `stage`, `verdict`, `holes`, `verified_count`;
      "stage:<s>"        the document's `stage` is not "verify" (the run
                         stopped before verification; <s> the stage);
      "holes:<n>"        `holes` is not an empty list (<n> its length; 0 when
                         it is not a list);
      "verdict:<v>"      `verdict` is not "verified" (<v> the verdict);
      "count"            `verified_count` is not an int of at least 1 (a
                         bool is not an int here);
      "exit:<n>"         the exit code is not 0.

    A try with no reason is a complete pass. Returns the Attempt (above):
    for a solved goal `passed` is the passing candidate and `reasons` holds
    the earlier tries' reasons; for an unsolved one `passed` is None and
    `reasons` holds one reason per try. Raises ValueError when `k` is below 1.
    """
    if k < 1:
        raise ValueError(f"k must be at least 1, not {k}")
    runner = run if run is not None else tools.run
    reasons = []
    tries = 0
    for cand in goal.candidates[:k]:
        tries += 1
        r = runner("vcheck --gate", cand)
        doc = r.document
        n = doc.get("verified_count") if isinstance(doc, dict) else None
        holes = doc.get("holes") if isinstance(doc, dict) else None
        if r.killed is not None:
            why = f"killed:{r.killed}"
        elif r.exit_code not in (0, 1):
            why = f"exit:{r.exit_code}"
        elif not isinstance(doc, dict) or any(key not in doc for key in
                                              ("stage", "verdict", "holes", "verified_count")):
            why = "no-document"
        elif doc["stage"] != "verify":
            why = f"stage:{doc['stage']}"
        elif not isinstance(holes, list) or holes:
            why = f"holes:{len(holes) if isinstance(holes, list) else 0}"
        elif doc["verdict"] != "verified":
            why = f"verdict:{doc['verdict']}"
        elif isinstance(n, bool) or not isinstance(n, int) or n < 1:
            why = "count"
        elif r.exit_code != 0:
            why = f"exit:{r.exit_code}"
        else:
            return Attempt(goal.id, True, tries, cand, tuple(reasons))
        reasons.append(why)
    return Attempt(goal.id, False, tries, None, tuple(reasons))
# triv: return Attempt(goal.id, True, 1, goal.candidates[0] if goal.candidates else None, ())



# item: Q12.H2py S9
def run_battery(goals: Sequence[Goal], *, k: int = 3, run=None) -> BatteryReport:
    """**H2.** Every goal through `solve_goal` (this module's, looked up at
    the time of the call), with the same `k` and `run`. Returns the
    BatteryReport (above): the solved count, the number of goals, the tries
    per goal, and, for each goal not solved, the reason of its first failed
    try (a goal with no candidates has no try, and no entry there). Goal ids
    are unique; raises ValueError on a repeated one.
    """
    seen = set()
    tries, first = {}, {}
    solved = 0
    for g in goals:
        if g.id in seen:
            raise ValueError(f"goal id {g.id!r} is repeated")
        seen.add(g.id)
        att = solve_goal(g, k=k, run=run)
        tries[g.id] = att.tries
        if att.solved:
            solved += 1
        elif att.reasons:
            first[g.id] = att.reasons[0]
    return BatteryReport(solved, len(goals), tries, first)
# triv: return BatteryReport(len(goals), len(goals), {g.id: 1 for g in goals}, {})


if __name__ == "__main__":
    sys.exit(main())
