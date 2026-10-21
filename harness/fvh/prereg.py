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

The freeze (DVR4 plan sections 3.3, 3.6, 3.8; the user's decisions D49-D52): a
lab whose primary contrast the course fixes commits its analysis plan, after its
pilot, as a freeze file (TOML; Lab alpha's is bench/local/r/labalpha/FREEZE.toml)
with every field of FREEZE_FIELDS. A plan over a schema-2 local stratum (one with
[[cluster]] rows, each with a role) names its `role`: a `pilot` plan's tasks are
all pilot clusters' tasks and need no freeze; a `confirmatory` or `descriptive`
plan names the freeze (`freeze = "<course path>"`), which must be complete,
match the stratum it was frozen on (stratum_sha256), keep the pilot and
confirmatory clusters disjoint, list the descriptive subset inside the
confirmatory clusters, and agree with the stratum's roles; the plan's tasks are
then exactly inside its role's clusters. A lab plan's PREREG block also names the
freeze it registers, `freeze-sha256: <64 hex>` (the learner registers the fixed
primary and their own descriptive analyses, D51). Anything else is
PreregRefused (FreezeRefused).

  section_hash(path) -> str              the recomputed full sha256
  prereg_rows(gradebook, module) -> [Row]   the module's prereg rows, in file order
  check(root, module) -> str             the full hash, or PreregRefused
  plan_fields(path) -> [str]             the plan-sha256 values the block names
  check_plan(root, module, plan_sha256)  None, or PreregRefused
  load_freeze(root, rel) -> dict         a complete, consistent freeze, or FreezeRefused
  freeze_fields(path) -> [str]           the freeze-sha256 values the block names
  check_roles(root, module, plan)        a plan's role against its stratum and freeze:
                                         the freeze (or None), or FreezeRefused; a
                                         cluster with a sealed task (`sealed = true`)
                                         never enters a plan (the user's D61)

Frozen (guard rule 2f), standard library only.
"""

import hashlib
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

__all__ = ["BEGIN", "END", "FREEZE_FIELD", "FREEZE_FIELDS", "FreezeRefused", "MIN_GRADE",
           "PLAN_FIELD", "PLAN_ROLES", "PreregRefused", "Row", "check", "check_plan",
           "check_roles", "freeze_fields", "load_freeze", "plan_fields", "prereg_rows",
           "section_hash", "stratum_clusters"]

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


FREEZE_FIELD = "freeze-sha256:"
_FREEZE = re.compile(r"(?<![A-Za-z0-9_-])freeze-sha256:(?:\}|~|\\ |\\texttt\{|[ \t])*"
                     r"([0-9A-Fa-f]{64})(?![0-9A-Za-z])")
# The fields a freeze must hold, each non-empty (DVR4 plan section 3.8)
FREEZE_FIELDS = ("estimand", "primary_contrast", "test", "budget_axis", "aggregation",
                 "missing_rule", "resource_accounting", "cluster_rule", "confirmatory_clusters",
                 "pilot_clusters", "power_sim_sha256")
_FREEZE_TEXT = ("estimand", "primary_contrast", "test", "budget_axis", "aggregation",
                "missing_rule", "resource_accounting", "cluster_rule")
PLAN_ROLES = ("pilot", "confirmatory", "descriptive")
CLUSTER_ROLES = ("pilot", "confirmatory", "unassigned")


class PreregRefused(RuntimeError):
    """No unlocked pre-registration matches the answers file (exit 3)."""


class FreezeRefused(PreregRefused):
    """A freeze that is incomplete or inconsistent, or a plan outside its role (exit 3)."""


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



# --- the freeze ---------------------------------------------------------------------------

def _hex64(v):
    return isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v) is not None


def _ids(v, what, where):
    if not isinstance(v, list) or not v or any(not isinstance(x, str) or not x for x in v):
        raise FreezeRefused(f"{where}: {what} is a non-empty list of cluster ids")
    if len(set(v)) != len(v):
        raise FreezeRefused(f"{where}: {what} names a cluster twice")
    return v


def _rel(root, rel, what):
    if not isinstance(rel, str) or not rel or rel.startswith("/") or ".." in rel.split("/"):
        raise FreezeRefused(f"{what} must be a course-relative path, not {rel!r}")
    return Path(root) / rel


def stratum_clusters(path) -> dict:
    """{cluster id: {"role", "descriptive", "tasks"}} of a schema-2 stratum file."""
    p = Path(path)
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise FreezeRefused(f"{p}: unreadable stratum ({type(e).__name__})") from None
    if data.get("schema") != 2:
        raise FreezeRefused(f"{p}: not a schema-2 stratum")
    sealed_tasks = {t.get("id") for t in data.get("task", []) if t.get("sealed") is True}
    out = {}
    for c in data.get("cluster", []):
        cid, role, tasks = c.get("id"), c.get("role"), c.get("tasks")
        if not isinstance(cid, str) or not cid or cid in out:
            raise FreezeRefused(f"{p}: a cluster needs one unique id")
        if role not in CLUSTER_ROLES:
            raise FreezeRefused(f"{p}: cluster {cid}: role is one of {', '.join(CLUSTER_ROLES)}")
        if not isinstance(tasks, list) or not tasks or any(not isinstance(t, str) for t in tasks):
            raise FreezeRefused(f"{p}: cluster {cid}: tasks is a non-empty list of task ids")
        desc = c.get("descriptive", False)
        if not isinstance(desc, bool) or (desc and role != "confirmatory"):
            raise FreezeRefused(f"{p}: cluster {cid}: only a confirmatory cluster is in the "
                                "descriptive subset")
        out[cid] = {"role": role, "descriptive": desc, "tasks": list(tasks),
                    "sealed": any(t in sealed_tasks for t in tasks)}
    seen = {}
    for cid, c in out.items():
        for t in c["tasks"]:
            if t in seen:
                raise FreezeRefused(f"{p}: task {t} lies in clusters {seen[t]} and {cid}")
            seen[t] = cid
    return out


def load_freeze(root, rel) -> dict:
    """The freeze file at course path `rel`, checked complete and consistent (module
    docstring); FreezeRefused names the first problem."""
    p = _rel(root, rel, "freeze")
    where = rel
    try:
        raw = p.read_bytes()
        data = tomllib.loads(raw.decode("utf-8"))
    except OSError:
        raise FreezeRefused(f"{where}: no freeze is committed: the confirmatory analysis plan "
                            "is frozen after the pilot (DVR4 plan section 3.6)") from None
    except (UnicodeDecodeError, ValueError) as e:
        raise FreezeRefused(f"{where}: unreadable freeze ({type(e).__name__})") from None
    missing = [k for k in FREEZE_FIELDS if k not in data]
    if missing:
        raise FreezeRefused(f"{where}: the freeze is incomplete: missing " + ", ".join(missing))
    for k in _FREEZE_TEXT:
        if not isinstance(data[k], str) or not data[k].strip():
            raise FreezeRefused(f"{where}: the freeze is incomplete: {k} is empty")
    conf = _ids(data["confirmatory_clusters"], "confirmatory_clusters", where)
    pilot = _ids(data["pilot_clusters"], "pilot_clusters", where)
    both = sorted(set(conf) & set(pilot))
    if both:
        raise FreezeRefused(f"{where}: pilot and confirmatory clusters overlap ("
                            + ", ".join(both) + "): the pilot is excluded from the "
                            "confirmatory sample")
    desc = data.get("descriptive_clusters", [])
    if desc:
        desc = _ids(desc, "descriptive_clusters", where)
        outside = sorted(set(desc) - set(conf))
        if outside:
            raise FreezeRefused(f"{where}: descriptive clusters outside the confirmatory "
                                "sample: " + ", ".join(outside))
    if not _hex64(data["power_sim_sha256"]):
        raise FreezeRefused(f"{where}: power_sim_sha256 is the simulation file's sha256 "
                            "(64 lower-case hex)")
    if "K" in data and data["K"] != len(conf):
        raise FreezeRefused(f"{where}: K = {data['K']!r} but {len(conf)} confirmatory clusters "
                            "are listed")
    st_rel, st_sha = data.get("stratum"), data.get("stratum_sha256")
    if not _hex64(st_sha):
        raise FreezeRefused(f"{where}: the freeze is incomplete: stratum and stratum_sha256 "
                            "name the stratum it was frozen on")
    sp = _rel(root, st_rel, "the freeze's stratum")
    try:
        got = hashlib.sha256(sp.read_bytes()).hexdigest()
    except OSError:
        raise FreezeRefused(f"{where}: its stratum {st_rel} is missing") from None
    if got != st_sha:
        raise FreezeRefused(f"{where}: the stratum changed after the freeze ({st_rel} is "
                            f"{got[:16]}, frozen {st_sha[:16]})")
    clusters = stratum_clusters(sp)
    for cid in conf + pilot:
        if cid not in clusters:
            raise FreezeRefused(f"{where}: cluster {cid} is not in {st_rel}")
    for cid in conf:
        if clusters[cid]["role"] != "confirmatory":
            raise FreezeRefused(f"{where}: {cid} is frozen confirmatory but the stratum says "
                                f"{clusters[cid]['role']}")
    for cid in pilot:
        if clusters[cid]["role"] != "pilot":
            raise FreezeRefused(f"{where}: {cid} is frozen pilot but the stratum says "
                                f"{clusters[cid]['role']}")
    flagged = sorted(c for c, v in clusters.items() if v["descriptive"])
    if sorted(desc) != flagged:
        raise FreezeRefused(f"{where}: the descriptive subset differs from the stratum's "
                            "descriptive flags")
    return dict(data, sha256=hashlib.sha256(raw).hexdigest(), clusters=clusters)


def freeze_fields(path) -> list[str]:
    """The freeze-sha256 values the PREREG block names, lower-cased, in order."""
    return [m.group(1).lower() for m in _FREEZE.finditer(_block(path)[1])]


def _task_stratum(root, rel):
    m = re.match(r"^bench/local/([qr])/([^/]+)/", rel)
    if not m:
        return None
    p = Path(root) / "bench" / "local" / m.group(1) / m.group(2) / "STRATUM.toml"
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return p if data.get("schema") == 2 and data.get("cluster") else None


def check_roles(root, module: str, plan):
    """A plan's role against its schema-2 stratum and the freeze (module docstring).

    `plan` needs .tasks ({id: (course path, lang)}), .role, .freeze, .lab and .path.
    Returns the loaded freeze for a confirmatory or descriptive plan, None for a
    pilot plan or a plan over no schema-2 stratum; FreezeRefused otherwise."""
    root = Path(root)
    strata = {_task_stratum(root, rel) for rel, _ in plan.tasks.values()}
    governed = {s for s in strata if s is not None}
    role, frz = getattr(plan, "role", ""), getattr(plan, "freeze", "")
    where = str(getattr(plan, "path", "the plan"))
    if not governed:
        if role or frz:
            raise FreezeRefused(f"{where}: role and freeze serve a plan over a schema-2 stratum")
        return None
    if len(governed) > 1 or None in strata:
        raise FreezeRefused(f"{where}: one plan draws from one schema-2 stratum only")
    sp = governed.pop()
    if role not in PLAN_ROLES:
        raise FreezeRefused(f"{where}: a plan over {sp.relative_to(root)} names its role ("
                            + ", ".join(PLAN_ROLES) + ")")
    clusters = stratum_clusters(sp)
    task_cluster = {t: cid for cid, c in clusters.items() for t in c["tasks"]}
    freeze = None
    if role == "pilot":
        if frz:
            raise FreezeRefused(f"{where}: a pilot plan runs before and outside the freeze")
        allowed = {cid for cid, c in clusters.items() if c["role"] == "pilot"}
    else:
        if not frz:
            raise FreezeRefused(f"{where}: a {role} plan runs only under the committed freeze "
                                "(freeze = \"<course path>\")")
        freeze = load_freeze(root, frz)
        if _rel(root, freeze.get("stratum"), "stratum").resolve() != sp.resolve():
            raise FreezeRefused(f"{where}: the freeze was made on another stratum")
        allowed = set(freeze["confirmatory_clusters"]) if role == "confirmatory" \
            else set(freeze.get("descriptive_clusters", []))
        if plan.lab:
            named = freeze_fields(root / "paper" / f"{module}_answers.tex")
            if set(named) != {freeze["sha256"]}:
                raise FreezeRefused(f"paper/{module}_answers.tex: the pre-registration must name "
                                    f"the freeze it registers, `{FREEZE_FIELD} "
                                    f"{freeze['sha256']}` (and no other)")
    for cid, c in clusters.items():
        if c["sealed"]:
            allowed.discard(cid)           # a sealed cluster never enters a plan (D61)
    stray = []
    for t, (rel, _) in plan.tasks.items():
        cid = next((task_cluster[x] for x in task_cluster
                    if rel.startswith(f"{sp.parent.relative_to(root).as_posix()}/{x}/")), None)
        if cid is None or cid not in allowed:
            stray.append(f"{t} ({cid or 'no cluster'})")
    if stray:
        raise FreezeRefused(f"{where}: task(s) outside the {role} clusters: " + ", ".join(stray))
    return freeze
