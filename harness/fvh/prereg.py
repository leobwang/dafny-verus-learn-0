"""fvh.prereg — the pre-registration gate (DV4-PLAN §4.5; Δ91, Δ192).

For a lab run fvh recomputes the sha256 of the lines from `% PREREG-BEGIN` to
`% PREREG-END` of paper/<ID>_answers.tex, inclusive, exactly as /grade-paper
does (`sed -n '/^% PREREG-BEGIN/,/^% PREREG-END/p' … | sha256sum`: each line
with its newline), and refuses missing or repeated markers. It then reads the
module's `prereg` rows of instructor/gradebook.md,

    | <date> | <ID> | prereg | <min> sha256 <first 16 hex> | <open findings> |

and the run goes ahead only when the NEWEST such row's hash prefix equals the
recomputed hash's first 16 hex digits and its minimum is at least 3.
Otherwise PreregRefused (exit 3), naming the row and the two hashes. The full
hash goes into every record of the batch.

The plan field (DV5d): the block names the batch plan it pre-registers on a
line of its own, `plan-sha256: <64 hex>` (anywhere on the line, as
`\texttt{plan-sha256: …}`, as the template words it, `\texttt{plan-sha256:} …`
(also with a tilde or a backslash-space before the digits), or bare; the
sha256 of the plan file's bytes, what `sha256sum` prints and fvh.batch's
Plan.sha256). A lab batch opens only when
the block names exactly one such hash and it is the plan's (check_plan); the
field is inside the hashed block, so a plan changed after grading needs a
re-graded pre-registration.

Only rows whose track is exactly `prereg` count. A `prereg-fixture` row
(/grade-paper --fixture, Δ192: a course fixture graded for the
grade-the-grader exercise) is never read as an unlock, and never hides an
older `prereg` row either: such rows are skipped as if absent.

  section_hash(path) -> str              the recomputed full sha256
  prereg_rows(gradebook, module) -> [Row]   the module's prereg rows, in file order
  check(root, module) -> str             the full hash, or PreregRefused
  plan_fields(path) -> [str]             the plan-sha256 values the block names
  check_plan(root, module, plan_sha256)  None, or PreregRefused

Frozen (guard rule 2f), standard library only.
"""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

__all__ = ["BEGIN", "END", "MIN_GRADE", "PLAN_FIELD", "PreregRefused", "Row", "check",
           "check_plan", "plan_fields", "prereg_rows", "section_hash"]

BEGIN = "% PREREG-BEGIN"
END = "% PREREG-END"
MIN_GRADE = 3
TRACK = "prereg"
_ROW = re.compile(r"^\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
                  r"\s*([^|]*?)\s*\|\s*$")
_GRADE = re.compile(r"^(\d+)\s+sha256\s+([0-9a-f]{16})$")
PLAN_FIELD = "plan-sha256:"
# between the colon and the digits: blanks and the LaTeX the template's wording invites
# (`\texttt{plan-sha256:} <hex>`, `~`, `\ `, a second `\texttt{`), never a line break
_PLAN = re.compile(r"(?<![A-Za-z0-9_-])plan-sha256:(?:\}|~|\\ |\\texttt\{|[ \t])*"
                   r"([0-9A-Fa-f]{64})(?![0-9A-Za-z])")


class PreregRefused(RuntimeError):
    """No unlocked pre-registration matches the answers file (exit 3)."""


@dataclass(frozen=True)
class Row:
    line: int
    date: str
    module: str
    grade: int | None
    prefix: str | None
    raw: str


def _block(path) -> tuple[Path, str]:
    """The answers file and its PREREG block, markers included (PreregRefused)."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        raise PreregRefused(f"{p}: missing or unreadable: no pre-registration to check") from None
    parts = text.split("\n")                        # sed's lines: split on newline only, and
    lines = [x + "\n" for x in parts[:-1]] + ([parts[-1]] if parts[-1] else [])  # a missing
    # last newline stays missing
    begins = [i for i, x in enumerate(lines) if x.startswith(BEGIN)]
    ends = [i for i, x in enumerate(lines) if x.startswith(END)]
    if len(begins) != 1 or len(ends) != 1:
        raise PreregRefused(f"{p}: the markers {BEGIN} and {END} must each appear exactly once "
                            f"at the start of a line (found {len(begins)} and {len(ends)})")
    b, e = begins[0], ends[0]
    if e < b:
        raise PreregRefused(f"{p}: {END} comes before {BEGIN}")
    return p, "".join(lines[b:e + 1])


def section_hash(path) -> str:
    return hashlib.sha256(_block(path)[1].encode("utf-8")).hexdigest()


def plan_fields(path) -> list[str]:
    """The plan-sha256 values the PREREG block names, lower-cased, in order."""
    return [m.group(1).lower() for m in _PLAN.finditer(_block(path)[1])]


def check_plan(root, module: str, plan_sha256: str) -> None:
    """A lab batch's plan against the pre-registration's plan field (DV5d)."""
    answers = Path(root) / "paper" / f"{module}_answers.tex"
    got = plan_fields(answers)
    where = f"paper/{module}_answers.tex"
    if not got:
        raise PreregRefused(f"{where}: the pre-registration names no batch plan: write "
                            f"`{PLAN_FIELD} <the plan file's sha256>` in its block and have "
                            "it graded (/grade-paper)")
    if len(set(got)) > 1:
        raise PreregRefused(f"{where}: the pre-registration names {len(set(got))} different "
                            f"plans ({', '.join(g[:16] for g in dict.fromkeys(got))}); one "
                            "pre-registration covers one plan")
    if got[0] != plan_sha256.lower():
        raise PreregRefused(f"{where}: the pre-registered plan is {got[0][:16]}…, this plan "
                            f"is {plan_sha256[:16]}… (the plan changed after the "
                            "pre-registration; run the plan it names, or amend and re-grade it)")


def prereg_rows(gradebook, module: str) -> list[Row]:
    p = Path(gradebook)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return []
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        m = _ROW.match(line.strip())
        if not m:
            continue
        date, mod, track, grade, _ = m.groups()
        if mod.upper() != module.upper() or track != TRACK:
            continue
        g = _GRADE.match(grade)
        out.append(Row(n, date, mod, int(g.group(1)) if g else None,
                       g.group(2) if g else None, line.strip()))
    return out


def check(root, module: str) -> str:
    """The full pre-registration hash when the newest prereg row unlocks it."""
    root = Path(root)
    answers = root / "paper" / f"{module}_answers.tex"
    full = section_hash(answers)
    book = root / "instructor" / "gradebook.md"
    rows = prereg_rows(book, module)
    if not rows:
        raise PreregRefused(f"no prereg row for {module} in instructor/gradebook.md: grade the "
                            "pre-registration first (/grade-paper)")
    row = rows[-1]
    where = f"instructor/gradebook.md:{row.line}"
    if row.grade is None or row.prefix is None:
        raise PreregRefused(f"{where}: the newest prereg row has no `<min> sha256 <16 hex>` "
                            f"grade field: {row.raw}")
    if row.prefix != full[:16]:
        raise PreregRefused(f"{where}: the graded hash {row.prefix} differs from the answers "
                            f"file's {full[:16]} (the plan changed after grading; re-grade it)")
    if row.grade < MIN_GRADE:
        raise PreregRefused(f"{where}: held at {row.grade} (every method dimension must be "
                            f">= {MIN_GRADE})")
    return full
