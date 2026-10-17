"""Q12 — Practice I-C: the retry client (Exercises, Python)

Imports: the Python standard library and the frozen core `fvh` (harness/fvh/:
fvh.tools), nothing else. The core is frozen and complete; read it, never
edit it. An instrument runs only through `fvh.tools.run` (never a subprocess
or a check of your own), and you judge a run from its result alone.

How to work this file (the S9 block of Q12, after the module's predictions:
the stage specimens under specimens/Q12/; record their first tries with
`scripts/firsttry.sh Q12 --check` first):
1. Replace each hole, in order: H1, then H2. A Python hole is a function
   whose body, after its docstring, is the one statement
   `raise NotImplementedError("<item id>")`; the tools count holes on the
   syntax tree, never by searching the text.
2. Run the acceptance tests (harness/tests/q/test_retry.py, frozen):
   `scripts/vcheck harness/q/fvh_q/retry.py`. No solver runs in them: they
   replay the battery's recorded results (harness/tests/q/fixtures/q12/rec/)
   and require its pinned solve count (expected/Q12.battery).
3. Done = `scripts/vcheck --gate harness/q/fvh_q/retry.py` exits 0 (zero
   holes and every acceptance test passing), AND
   `scripts/firsttry.sh Q12 --report --strict` exits 0.
4. Then your own live check, outside the tests: the client over the battery,
   on the host, one solver job at a time (a few minutes):
   `cd harness && PYTHONPATH=q uv run python -m fvh_q.retry --battery`.
5. Stuck for 20 minutes? /tutor Q12.

This file ships with exactly 2 holes: H1 and H2, each counted from the syntax
tree. Item kinds and the slot protocol are in the Dafny file's header
(dafny/Q/Q12_PracticeIC/std/Q12_PracticeIC.dfy).

The battery (harness/tests/q/fixtures/q12/battery.toml, frozen): twelve
goals, six per language, each with three candidate files written in advance,
some of them wrong in different ways. A candidate is a whole file that
stands alone: the client never edits one, it only runs the done gate on it.
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
    raise NotImplementedError("Q12.H1py")
# Hint: a `dict.get` on a key that may be missing, and `isinstance(x, bool)`
#    before `isinstance(x, int)`: True is an int in Python.


# item: Q12.H2py S9
def run_battery(goals: Sequence[Goal], *, k: int = 3, run=None) -> BatteryReport:
    """**H2.** Every goal through `solve_goal` (this module's, looked up at
    the time of the call), with the same `k` and `run`. Returns the
    BatteryReport (above): the solved count, the number of goals, the tries
    per goal, and, for each goal not solved, the reason of its first failed
    try (a goal with no candidates has no try, and no entry there). Goal ids
    are unique; raises ValueError on a repeated one.
    """
    raise NotImplementedError("Q12.H2py")
# Hint: `solve_goal` read through the module's globals at call time is what a
#    test can replace; one pass over the goals builds every field.


if __name__ == "__main__":
    sys.exit(main())
