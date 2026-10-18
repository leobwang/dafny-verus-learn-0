#!/usr/bin/env python3
"""skill_sims.py: the skill simulations of spec §9.5 step 8 (DV2b-2; Q04–Q06 cases, DV3k;
Q07–Q09 cases, DV3bk; Q10–Q12 cases, DV5ak; Q13–Q15 cases, DV5b; Q16–Q18 cases,
DV5c).

The author plays a confused learner through the instructor and contractor
skills in a throwaway STUDY clone (no mode file, all eight deny rules, the
hooks live), one headless `claude -p` turn at a time. A multi-turn skill
session is resumed with `--resume <session id>`; a one-turn session runs with
`--no-session-persistence`. Each case is judged against the skill's own
SKILL.md and CORE.md (README.md beside this file lists the cases).

AUTHOR-ONLY. `scan` reads the reference set (the leak patterns and the leak
tokens of tests/acceptance/guard_doors.py) and prints only counts. It runs only
in the author's linked worktree and never under CI (CI never calls a model).

Phases (the author drives the learner side, so turns run one at a time):
  setup    clone the worktree's branch into the study root's clone (below),
           copy in every uncommitted file of the worktree, check the
           study-mode invariants (no .claude/state/, the eight deny rules, the
           hook executable and byte-identical to the worktree's), link the
           pinned toolchain, and check that the clone's hook passes a study
           session's first calls in the clone and still refuses WORK (D20).
  plant    write a named learner attempt into the clone (PLANTS below);
           `plant --restore [name]` puts the shipped learner files back (the
           worktree's copies; every planted file when no name is given).
  learner  apply a learner state from a JSON spec kept outside the repo (filled
           prediction slots, test-out attempts): `learner <spec.json>`.
  dropin   `dropin <ID> flawed|gold`: write a calibration fixture into the clone
           as paper/<ID>_answers.tex, as calibrate.py's drop-in does (the shipped
           answers file's header comment, then the fixture from its
           \\documentclass line on, so no EXPECTED line reaches the clone; DV5c).
  turn     one learner turn: `turn <case> new|resume|single "<message>"`,
           from inside the clone, under a systemd scope (MemoryMax 4G for the
           claude process; every solver job runs in the wrapper's own capped
           scope) and a wall-clock net. Budget: WORK/calls.log. The window
           rule (guard_doors.window_verdict, sandbox/apparatus.toml [window])
           judges each turn's rate_limit_events: after a defer or a stop no
           turn starts until the author passes --window-ack.
  scan     leak scan over every captured stream and every file the sessions
           wrote in the clone: the module leak patterns (regexes) and the
           reference-derived leak tokens. Counts only, never a pattern/token.
           A case's patterns are the Q15 tier filter's (Δ130:
           calibrate.patterns_for, one source): those of the modules its
           prompts name and of every module of the same track at a tier as
           high or higher (with several modules named, the union; with none,
           every pattern; a case left with none is refused). The tokens are
           not filtered (Δ130's open question).
  show     the targeted view of one turn, only when that turn scanned clean:
           tool calls (sanitized), refusals, text sizes, question lines and
           structure lines, each truncated.
  check    case-specific counts: `pp <case> <turn> <bank id> <PPn>` (verbatim
           coverage of a bank's parallel problem, and whether its author's
           notes were handed out; `pp1` is Q02's PP1), `hole <case> <item>`
           (the item's reference answer lines in anything the tutor emitted;
           `h2d` is Q02.H2d's method-wide form; `twin <case> <file>` is the
           whole-file form, for an item with no hole markers), `stmt <case>`
           (statement-shaped code lines the tutor wrote that the learner did
           not), `contract <case> <turn> <agent file>` (how much of each
           CONTRACT header line a restatement holds), `viva <case>` (per turn:
           the scoped bank ids named, in order, and the verdict words), `files`
           (what a turn wrote), `grade <case> <turn> <ID> flawed|gold` (a
           /grade-paper turn on a drop-in, judged by calibrate.py's own
           eval_grading, plus the pre-registration's unlock line; DV5c).
  report   write sanitized per-turn summaries, the scan and env to the archive
           (no transcript, no tool result body; short refusal texts verbatim).
  cleanup  delete the clone and the whole study root, every raw output (voided
           calls' included), and the Claude Code state the sessions left
           (transcripts under ~/.claude/projects/<clone slug>/,
           /tmp/claude-<uid>/<clone slug>/, entries named by session id).

Two roots (the user's decision D20, 2026-10-13). WORK (--work) is the lane's
scratch, /tmp/dvl0-<phase>-<lane>/..., which the guard's rule 1 refuses (a
tripwire): state.json, the raw streams, the prompts and calls.log stay there.
The session-facing half, the clone and the wrappers' DVL_SCRATCH, lives under
the study root, WORK with its top directory renamed /tmp/dvl0-study-<phase>-
<lane>/ (/tmp/dvl0-dv5d-simulations/q16-q18 -> /tmp/dvl0-study-dv5d-simulations/
q16-q18/clone and .../dvl), which that pattern does not match (DV5d's attempt 1:
a clone inside WORK had every tool call refused).

Turn options: --max-turns and --timeout (a /grade-paper turn on a drop-in runs
probes: calibrate.py gives it 150 turns and 2700 s); --approve-allowlist runs approve_allowlist_mcp.py as the turn's
permission handler (it approves only a Write/Edit of the contract allowlist: the
learner's click on a prompt a headless run cannot show); --extra-allow adds
--allowedTools rules for one turn; `forget <case>` voids a case the service
refused before any skill work.

Usage: python3 tests/instructor/simulations/skill_sims.py <phase> [...] [--work DIR]
"""

import argparse
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
import uuid
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
HOME = Path.home()
CLAUDE_HOME = Path(os.environ.get("CLAUDE_CONFIG_DIR") or HOME / ".claude")
# DV5d (the Q16–Q18 cases, then the Q13–Q15 re-run, each in its own WORK under
# this directory and its own archive subdirectory, passed with --work/--archive);
# the DV2b-2 run used /tmp/dvl0-dv2b2-sims and author-probes/dv2b2/simulations,
# DV3k /tmp/dvl0-dv3k-sims, DV3bk /tmp/dvl0-dv3bk-sims, DV5ak /tmp/dvl0-dv5ak-sims,
# DV5b /tmp/dvl0-dv5b-simulations and their archives (DV5c started none)
DEFAULT_WORK = Path("/tmp/dvl0-dv5d-simulations")
# WORK is the lane's scratch (state, streams, prompts, calls.log); the clone and the
# wrappers' DVL_SCRATCH live under its study root, /tmp/dvl0-study-<phase>-<lane>/...
# (GD.work_paths; the user's decision D20, 2026-10-13)
DEFAULT_ARCHIVE = HOME / ".cache/dafny-verus-learn-0/author-probes/dv5d/simulations"
SESSION_MEM = "4G"          # the claude process only; solver jobs: the wrapper's own scope
LANE_SHARE_GIB = 16         # this lane's memory share (CLAUDE.md §Resources)
TURN_TIMEOUT_S = 1800
MAX_TURNS = 40
DEFAULT_BUDGET = 30
CLAUDE_FLAGS = [
    "--output-format", "stream-json", "--verbose", "--max-turns", str(MAX_TURNS),
    "--permission-mode", "acceptEdits",
    "--allowedTools", "Read,Bash,Write,Edit,Glob,Grep,Skill",
]

Q02_DFY = "dafny/Q/Q02_FirstSyntaxI/core/Q02_FirstSyntaxI.dfy"
Q05_DFY = "dafny/Q/Q05_Frames/std/Q05_Frames.dfy"
Q06_PY = "harness/q/fvh_q/q06_stats.py"
Q08_AGENT_DFY = "dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy"
Q09_GATE_PY = "harness/q/fvh_q/gate/core.py"
Q10_DFY = "dafny/Q/Q10_PracticeIA/std/Q10_PracticeIA.dfy"
Q11_DFY = "dafny/Q/Q11_PracticeIB/std/Q11_PracticeIB.dfy"
Q13_DFY = "dafny/Q/Q13_PracticeIIA/std/Q13_PracticeIIA.dfy"
Q16_DFY = "dafny/Q/Q16_PracticeIIIA/std/Q16_PracticeIIIA.dfy"
BANK = ".claude/skills/instructor/banks/{}.md"
BANK_Q02 = BANK.format("Q02")

# Learner attempts (plausible and wrong). Each is a list of (file, old, new) edits on
# the clone's shipped learner file. A plant is never a reference answer, and it
# stays as far from one as a plausible attempt allows: tests/ is learner-readable
# (DELTAS Δ144, Open). Beyond the shipped text, only h2d-weak's generic bounds
# invariant also sits in an answer.
_H2D_HOLE = ("    assume false;  // HOLE: delete this line, then write the invariants and the "
             "assertions\n")
_H2D_LOOP = ("    var n := |s|;\n"
             "    while n > 0 && s[n - 1] == 0\n"
             "      decreases n\n")
_POP_HEAD = ("      requires Valid() && |Contents| > 0\n"
             "      ensures x == old(Contents)[|old(Contents)| - 1] && "
             "Contents == old(Contents)[..|old(Contents)| - 1]\n"
             "    {\n"
             "      assume false;  // HOLE: delete this line, then write the frame clauses in the "
             "header above\n")
_POP_CHECK = ("  // method PopCheck(s: LimbStack, t: LimbStack)\n"
              "  //   requires s.Valid() && t.Valid() && s.Repr !! t.Repr && |s.Contents| > 0\n"
              "  //   modifies s.Repr\n"
              "  // {\n"
              "  //   var tc := t.Contents;\n"
              "  //   var x := s.Pop();\n"
              "  //   assert t.Valid() && t.Contents == tc && s.Repr !! t.Repr;\n"
              "  // }\n")
PLANTS = {
    # Q02.H2d, attempt 1: true invariants that say nothing about Normalize
    "h2d-weak": [(Q02_DFY, _H2D_HOLE + _H2D_LOOP,
                  "    var n := |s|;\n"
                  "    while n > 0 && s[n - 1] == 0\n"
                  "      invariant 0 <= n <= |s|\n"
                  "      invariant n < |s| ==> s[n] == 0\n"
                  "      decreases n\n")],
    # Q02.H2d, attempt 2 (on top of 1): "a limb is already dropped" (false on entry,
    # where n is |s|). DV6 fix round: the DV3k wording ("the prefix is already
    # normalized") was a later module's answer invariant word for word; this one is no
    # line and no conjunct of any twin's answer region. The DV2b-2 and DV3k runs planted
    # the earlier wordings (their env.json files record them).
    "h2d-normalized-prefix": [(Q02_DFY,
                               "      invariant n < |s| ==> s[n] == 0\n",
                               "      invariant n < |s| ==> s[n] == 0\n"
                               "      invariant n < |s|\n")],
    # Q05.H2d: the frame copied from Push, the given method above it (`modifies Repr`,
    # `ensures Valid()`), with the hole line deleted and PopCheck uncommented as the
    # file asks. Pop verifies; PopCheck's assertion does not.
    "q05-h2d-copied-frame": [
        (Q05_DFY, _POP_HEAD,
         "      requires Valid() && |Contents| > 0\n"
         "      modifies Repr\n"
         "      ensures Valid()\n"
         "      ensures x == old(Contents)[|old(Contents)| - 1] && "
         "Contents == old(Contents)[..|old(Contents)| - 1]\n"
         "    {\n"),
        (Q05_DFY, _POP_CHECK, "".join(
            line[:2] + line[5:] if line.startswith("  // ") else line
            for line in _POP_CHECK.splitlines(keepends=True)))],
    # Q05.H2d, the tutor's rung-3 bisection (on top of the copied frame): PopCheck's
    # given assertion split into one assertion per conjunct
    "q05-h2d-split-assert": [(Q05_DFY,
                              "    assert t.Valid() && t.Contents == tc && s.Repr !! t.Repr;\n",
                              "    assert t.Valid();\n"
                              "    assert t.Contents == tc;\n"
                              "    assert s.Repr !! t.Repr;\n")],
    # Q06.H6py: every attempt of the arm counted, and a normal-approximation interval
    # re-derived by hand (the file asks for fvh.stats); no guard for an empty arm.
    "q06-h6py-all-attempts": [(Q06_PY, '    raise NotImplementedError("Q06.H6py")\n',
                               "    mine = [rec for rec in records if rec.arm == arm]\n"
                               "    ok = sum(1 for rec in mine if rec.success)\n"
                               "    p = ok / len(mine)\n"
                               "    half = 1.96 * (p * (1 - p) / len(mine)) ** 0.5\n"
                               "    return ok, len(mine), (p - half, p + half)\n")],
    # Q08.A1d (the flagship's statements, learner-owned): two statements that say
    # only "valid, and this long", and a witness that asserts what the learner MEANT.
    # The statements are green (two bodyless methods: two holes); both witness
    # assertions fail, because nothing in either `ensures` pins a value.
    "q08-a1d-length-only": [(Q08_AGENT_DFY,
                             "  // ### WITNESSES (learner-owned: your checks that the statements can be met\n"
                             "  //    and say something).\n",
                             "  method ShiftLeft(a: seq<nat>, k: nat) returns (r: seq<nat>)\n"
                             "    requires Valid(a)\n"
                             "    ensures Valid(r) && |r| == |a| + k\n"
                             "\n"
                             "  method SplitAt(a: seq<nat>, k: nat) returns (lo: seq<nat>, hi: seq<nat>)\n"
                             "    requires Valid(a) && k <= |a|\n"
                             "    ensures Valid(lo) && Valid(hi) && |lo| <= k\n"
                             "\n"
                             "  // ### WITNESSES (learner-owned: your checks that the statements can be met\n"
                             "  //    and say something).\n"
                             "  method Witnesses()\n"
                             "  {\n"
                             "    var r := ShiftLeft([5], 2);\n"
                             "    assert r == [0, 0, 5];\n"
                             "    var lo, hi := SplitAt([1, 2, 3], 1);\n"
                             "    assert lo == [1];\n"
                             "  }\n")],
    # Q10.H4d: the assume deleted and only the loop variables' bounds stated (the
    # invariant any loop over `i` starts with); nothing about the limbs, so
    # NormalizeTrim's preconditions fail after the loop.
    "q10-h4d-bounds-only": [(Q10_DFY,
                             "    assume false;  // HOLE: delete this line, then write the loop invariants\n",
                             ""),
                            (Q10_DFY, "      decreases |s| - i\n",
                             "      invariant i <= |s| && n <= |s|\n      decreases |s| - i\n")],
    # Q11.H7d: the postcondition copied as the precondition, no assignment substituted
    # (DV6 fix round: the earlier forwards substitution held one conjunct of the answer);
    # Pre1Exact fails.
    "q11-h7d-forwards": [(Q11_DFY, "  ghost predicate Pre1(x: int, y: int) { true }\n",
                          "  ghost predicate Pre1(x: int, y: int) { x > 0 && y < 10 }\n")],
    # Q13.H2d: a body that recurs on the FRONT of `b` (the given `decreases |b|` read as
    # "peel b's first limb"), while Normalize strips the top (last) limb; no case
    # split on the top limb, no fact about any sequence. The postcondition fails.
    "q13-h2d-front-recursion": [(Q13_DFY,
                                 "    decreases |b|\n"
                                 "  // HOLE: this lemma has no body; write `{ … }` below the "
                                 "decreases line.\n",
                                 "    decreases |b|\n"
                                 "  {\n"
                                 "    if b != [] {\n"
                                 "      NormalizeConcat(a, b[1..]);\n"
                                 "    }\n"
                                 "  }\n")],
    # Q16.H1d (the DV5c gaps lane): the plain induction the docstring warns about, one
    # recursive call of the plain statement on b's tail, with nothing generalized (no
    # accumulator, no row position); the postcondition fails. No line of it is an
    # answer line: the answer generalizes over what MulAcc's recursion carries.
    "q16-h1d-plain-induction": [(Q16_DFY,
                                 "    ensures Valid(Times(a, b)) && ToNat(Times(a, b)) == "
                                 "ToNat(a) * ToNat(b)\n"
                                 "  // HOLE: this lemma has no body; write `{ … }` below the "
                                 "ensures line.\n",
                                 "    ensures Valid(Times(a, b)) && ToNat(Times(a, b)) == "
                                 "ToNat(a) * ToNat(b)\n"
                                 "  {\n"
                                 "    if |b| > 0 {\n"
                                 "      MulCorrect(a, b[1..]);\n"
                                 "    }\n"
                                 "  }\n")],
    # Q09.H2py: a lazy first body (one combined test, one reason); it ignores the
    # docstring's seven checks and their order, and never looks at `lang`.
    "q09-h2py-one-reason": [(Q09_GATE_PY, '    raise NotImplementedError("Q09.H2py")\n',
                             '    if doc.get("verdict") == "verified" and not doc.get("holes"):\n'
                             '        return []\n'
                             '    return ["not verified"]\n')],
}

STRUCT_RX = re.compile(
    r"refus|fresh session|[Gg]ate \d|verifier goes first|noted|[Nn]ext:|§|Reread|"
    r"Solutions/|yours to open|taint|\brung\b|PP\d|parallel|takeaway|allowlist|contract v0|"
    r"queue|\bdue\b|ledger|record|SOLID|SHAKY|MISSED|PASS|REVIEW|[Dd]raw\b|"
    r"Q\d\d\.K\d|not authored|no viva|has no|closed for|stop", re.I)
RX_BLOCK = re.compile(r"spoiler-guard: blocked \(rule ([0-9a-z]+)\)")


class Refusal(Exception):
    pass


def say(msg):
    print(f"skill_sims: {msg}", flush=True)


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode("utf-8")).hexdigest()


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args, cwd=ROOT, check=True):
    p = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    if check and p.returncode != 0:
        raise Refusal(f"git {' '.join(args)} failed (exit {p.returncode}): {p.stderr.strip()[:200]}")
    return p.stdout


def load_guard_doors():
    """The DV1c harness: its deny list, environment scrub, stream helpers and leak tokens."""
    path = ROOT / "tests" / "acceptance" / "guard_doors.py"
    spec = importlib.util.spec_from_file_location("guard_doors", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GD = load_guard_doors()


def load_calibrate():
    """The calibration harness (tests/instructor/calibration/calibrate.py): its Q15
    tier filter `patterns_for` is the one source of the leak-pattern selection (Δ130)."""
    path = ROOT / "tests" / "instructor" / "calibration" / "calibrate.py"
    spec = importlib.util.spec_from_file_location("calibrate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CAL = load_calibrate()


def mem_available_gib():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1048576
    return 0.0


# -------------------------------------------------------------------------------------
# setup / plant
# -------------------------------------------------------------------------------------

LANE_SCRATCH = re.compile(r"^dvl0-dv[0-9a-z]+-.+$")


def lane_scratch(base="/tmp", exclude=()):
    """The author lanes' scratch directories on this host (CLAUDE.md:
    /tmp/dvl0-<phase>-<lane>/), owned by this user, other than `exclude` (this
    run's own work directory and its parents): they can hold reference twins and
    sealed truth that a study session could read, so a simulation starts only
    when there are none (DV5c fix round)."""
    keep = {Path(x).resolve() for x in exclude}
    out = []
    try:
        entries = sorted(Path(base).iterdir())
    except OSError:
        return out
    for d in entries:
        try:
            if LANE_SCRATCH.match(d.name) and d.is_dir() and not d.is_symlink() \
                    and d.stat().st_uid == os.getuid() and d.resolve() not in keep \
                    and not any(k.is_relative_to(d.resolve()) for k in keep):
                out.append(str(d))
        except OSError:
            continue
    return out


def stale_study_roots(own, base="/tmp"):
    """The study roots on this host (/tmp/dvl0-study-*, owned by this user) other
    than this run's own study root `own` (DV5e review): a study root lies outside the
    guard's lane-scratch tripwire (D20), and one left behind (a WORK removed without
    its tool's `cleanup`) holds a full clone of the authoring branch, perhaps a
    drop-in and wrapper runs, which a study session could read. Under own's top
    directory, any entry off the path down to `own` counts (another run of the lane)."""
    own = Path(os.path.normpath(os.path.abspath(str(own))))
    out = []
    try:
        entries = sorted(Path(base).iterdir())
    except OSError:
        return out
    for d in entries:
        try:
            if not (d.name.startswith(GD.STUDY_PREFIX) and d.is_dir() and not d.is_symlink()
                    and d.stat().st_uid == os.getuid()):
                continue
            top = Path(os.path.normpath(os.path.abspath(str(d))))
            if not own.is_relative_to(top):
                out.append(str(d))
                continue
            chain, cur = own.relative_to(top).parts, top
            for part in chain:
                out += [str(x) for x in sorted(cur.iterdir()) if x.name != part]
                cur = cur / part
                if not cur.is_dir():
                    break
        except OSError:
            continue
    return out


def paths_of(work, state=None):
    """GD.work_paths as a refusal: the study root (the clone, DVL_SCRATCH) and WORK
    (D20); a state written before D20 names its own clone."""
    try:
        paths = GD.work_paths(work)
    except ValueError as e:
        raise Refusal(str(e))
    if state and state.get("clone") and not state.get("study_root"):
        paths["clone"] = Path(state["clone"])
    return paths


def phase_setup(work, state):
    paths = paths_of(work)
    clone = paths["clone"]
    if clone.exists():
        raise Refusal(f"{clone} exists: run `cleanup` first")
    try:
        GD.check_study_root_free(paths["study_root"])
    except ValueError as e:
        raise Refusal(str(e))
    # the study root (/tmp/dvl0-study-…) is no lane's scratch: LANE_SCRATCH does not match it
    stale = lane_scratch(exclude=[work])
    if stale:
        raise Refusal("author lane scratch is on this host and may hold reference twins or "
                      "sealed truth that a study session can read: archive what matters under "
                      "~/.cache/dafny-verus-learn-0/author-probes/ and remove it first ("
                      + ", ".join(stale) + ")")
    orphans = stale_study_roots(paths["study_root"])
    if orphans:
        raise Refusal("a study root is on this host (an earlier run's clone, possibly a "
                      "drop-in), outside the guard's lane-scratch tripwire: run that tool's "
                      "`cleanup` or remove it first (" + ", ".join(orphans) + ")")
    work.mkdir(parents=True, exist_ok=True)
    paths["study_root"].mkdir(parents=True, exist_ok=True)
    rc, branch = GD.clone_head(ROOT, clone)
    if rc != 0:
        raise Refusal(f"git clone failed (exit {rc})")
    head = git("rev-parse", "HEAD", cwd=clone).strip()
    copied, removed = {}, []
    for rel in [x for x in git("ls-files", "-m", "-o", "--exclude-standard", "-z").split("\0") if x]:
        parts = rel.split("/")
        if "__pycache__" in parts or rel.endswith(".pyc") or rel.startswith(".claude/state/"):
            continue
        src = ROOT / rel
        if not src.is_file():
            continue
        dst = clone / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied[rel] = sha(src.read_bytes())
    for rel in [x for x in git("ls-files", "-d", "-z").split("\0") if x]:
        (clone / rel).unlink(missing_ok=True)
        removed.append(rel)
    shutil.rmtree(clone / ".claude" / "state", ignore_errors=True)
    (clone / ".claude" / "settings.local.json").unlink(missing_ok=True)
    hook = clone / ".claude" / "hooks" / "spoiler-guard.sh"
    hook.chmod(0o755)
    deny = read_json(clone / ".claude" / "settings.json").get("permissions", {}).get("deny", [])
    missing = [r for r in GD.DENY_RULES if r not in deny]
    if missing:
        raise Refusal("the clone lacks deny rules: " + ", ".join(missing))
    hook_sha = sha(hook.read_bytes())
    if hook_sha != sha((ROOT / ".claude/hooks/spoiler-guard.sh").read_bytes()):
        raise Refusal("the clone's hook differs from the worktree's")
    if (clone / ".claude" / "state" / "mode").exists():
        raise Refusal("the clone has a mode file")
    tc = ROOT / ".toolchain"
    if tc.exists():
        os.symlink(str(tc.resolve()), str(clone / ".toolchain"))
    # The clone must be usable from inside (D20): the guard passes a study session's
    # first calls there and still refuses WORK.
    hook_rows, problems = GD.probe_study_clone(paths)
    if problems:
        raise Refusal("the study clone fails the hook probe: " + "; ".join(problems))
    slug = GD.clone_slug(clone)
    write_json(work / "baseline.files.json", changed_files(clone))
    state.update(
        clone=str(clone), study_root=str(paths["study_root"]), dvl_scratch=str(paths["dvl"]),
        study_probe=hook_rows, branch=branch, head=head, copied=copied, removed=removed,
        hook_sha256=hook_sha, deny=deny, slug=slug, cases={}, plants=[], prompts=[],
        preexisting={"projects_slug": (CLAUDE_HOME / "projects" / slug).exists(),
                     "tmp_slug": Path(f"/tmp/claude-{os.getuid()}/{slug}").exists()},
        setup_at=datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
    say(f"setup: clone {clone} at {head[:12]} (+{len(copied)} uncommitted files, "
        f"-{len(removed)}); hook {hook_sha[:16]}; deny rules {len(deny)}; study root "
        f"{paths['study_root']} ({len(hook_rows)} hook probes as expected)")


_PIECE = re.compile(r"&&|\|\||==>|<==>|[{};]")
# Declared overlaps (README.md, the plant paragraph): generic lines any attempt at the item
# needs, which a plant may share with an answer region. Each entry: (plant, line).
PLANT_GENERIC = {
    ("h2d-weak", "invariant 0 <= n <= |s|"),       # the loop variable's bounds
    ("q08-a1d-length-only", "requires Valid(a)"),  # the precondition any limb statement takes
    ("q08-a1d-length-only", "method Witnesses()"),  # the witness section's own header
    ("q16-h1d-plain-induction", "if |b| > 0 {"),   # the case split any induction on b opens
    # the validity conjuncts any statement over limb sequences states first
    ("q08-a1d-length-only", "ensures Valid(r)"),
    ("q08-a1d-length-only", "ensures Valid(lo)"),
    ("q08-a1d-length-only", "Valid(hi)"),
}


def _pieces(line):
    return {p.strip() for p in _PIECE.split(line) if len(p.strip()) >= 9}


def answer_regions():
    """(answer lines, answer conjuncts) of every reference twin: the lines of a
    Solutions/{dafny,verus,harness}/ file that its learner file does not hold, and their
    pieces split at &&, ||, ==>, braces and semicolons (author-only; it opens the
    reference set and returns no text to any output)."""
    lines, pieces = set(), set()
    for rel in [x for x in git("ls-files", "-z", "--", "Solutions/dafny", "Solutions/verus",
                               "Solutions/harness").split("\0") if x]:
        learner = ROOT / rel[len("Solutions/"):]
        try:
            twin = (ROOT / rel).read_text(encoding="utf-8")
            shipped = learner.read_text(encoding="utf-8") if learner.is_file() else ""
        except (OSError, UnicodeDecodeError):
            continue
        have = {x.strip() for x in shipped.splitlines()}
        for x in twin.splitlines():
            x = x.strip()
            if x and x not in have:
                if len(x) >= 12:
                    lines.add(x)
                pieces |= {q for q in _pieces(x) if q not in shipped}
    return lines, pieces


def plant_overlaps(name, regions=None):
    """[(file, what)] where a plant's new text shares a line of 12 or more characters, or a
    conjunct, with a twin's answer region, its declared generic lines aside (DV6 fix round:
    a plant sits in a learner-readable file, so it must be no answer, its own item's or a
    later module's)."""
    lines, pieces = regions or answer_regions()
    out = []
    for rel, old, new in PLANTS[name]:
        shipped = (ROOT / rel).read_text(encoding="utf-8")
        added = [x.strip() for x in new.splitlines() if x.strip() and x.strip() not in shipped
                 and (name, x.strip()) not in PLANT_GENERIC]
        if any(x in lines for x in added):
            out.append((rel, "an answer line"))
        if any(q in pieces and q not in shipped and (name, q) not in PLANT_GENERIC
               for x in added for q in _pieces(x)):
            out.append((rel, "a conjunct of an answer line"))
    return out


def phase_plant(work, state, name, restore):
    clone = Path(state["clone"])
    if restore:
        if name and name not in PLANTS:
            raise Refusal(f"unknown plant {name!r} ({', '.join(PLANTS)})")
        rels = sorted({r for r, _, _ in PLANTS[name]} if name else
                      {p["file"] for p in state["plants"] if p.get("name") != "restore"})
        for rel in rels:
            # the shipped form is the worktree's copy (setup copied it in)
            shutil.copy2(ROOT / rel, clone / rel)
            state["plants"].append(dict(name="restore", file=rel,
                                        sha256=sha((clone / rel).read_bytes())))
        say(f"plant: restored {', '.join(rels) or 'nothing'} to the shipped form")
        return
    if name not in PLANTS:
        raise Refusal(f"unknown plant {name!r} ({', '.join(PLANTS)})")
    bad = plant_overlaps(name)
    if bad:
        raise Refusal(f"plant {name} shares " + "; ".join(f"{w} ({r})" for r, w in bad)
                      + ": a plant is never an answer (DV6)")
    for rel, old, new in PLANTS[name]:
        f = clone / rel
        text = f.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise Refusal(f"plant {name}: the anchor occurs {text.count(old)} times in {rel}")
        f.write_text(text.replace(old, new), encoding="utf-8")
        state["plants"].append(dict(name=name, file=rel, new=new,
                                    sha256=sha(f.read_bytes())))
    say(f"plant: {name} written into {', '.join(r for r, _, _ in PLANTS[name])}")


def phase_learner(work, state, spec_path):
    """Apply a learner state from a JSON spec kept OUTSIDE the repo (the author's
    archive, read-denied in study mode): {"name": ..., "edits": [[file, old, new],
    ...]}. It stands for work a learner does before a skill runs, such as filled
    prediction slots and test-out attempts ahead of a tier viva, which must not sit
    in tests/ (learner-readable). Each edit's anchor must occur exactly once; each
    is recorded as a plant (its text joins the prompts in the token detector's
    exemptions: the learner's own writing, not the session's)."""
    spec_path = Path(spec_path).resolve()
    if ROOT in spec_path.parents:
        raise Refusal("learner: the spec must live outside the repo (tests/ is learner-readable)")
    spec = read_json(spec_path)
    clone = Path(state["clone"])
    name = spec.get("name") or spec_path.stem
    for rel, old, new in spec["edits"]:
        f = clone / rel
        text = f.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise Refusal(f"learner {name}: the anchor occurs {text.count(old)} times in {rel}")
        f.write_text(text.replace(old, new), encoding="utf-8")
        state["plants"].append(dict(name=f"learner:{name}", file=rel, new=new,
                                    sha256=sha(f.read_bytes()), spec_sha256=sha(spec_path.read_bytes())))
    say(f"learner: {name}: {len(spec['edits'])} edit(s) in "
        f"{len({r for r, _, _ in spec['edits']})} file(s)")


DROPIN_KINDS = ("flawed", "gold")
DROPIN_MARKERS = ("EXPECTED", "CALIBRATION", "tests/instructor", "fixture")


def dropin_text(mid, kind, root=ROOT):
    """calibrate.py's drop-in, from the worktree's files: the shipped answers file's
    header comment (paper/<ID>_answers.tex up to its \\documentclass line), then the
    calibration fixture from its \\documentclass line on, so the fixture's EXPECTED
    header never reaches the clone. calibrate.dropin_text reads the skeleton at a git
    revision, which a module still uncommitted lacks (Q16–Q18 at DV5c); the splice
    and the marker check are the same."""
    if not re.fullmatch(r"[QR]\d\d", mid) or kind not in DROPIN_KINDS:
        raise Refusal(f"dropin: want a module id and one of {', '.join(DROPIN_KINDS)}")
    skel_f = Path(root) / "paper" / f"{mid}_answers.tex"
    fx_f = Path(root) / "tests" / "instructor" / "fixtures" / f"{mid}_{kind}_answers.tex"
    if not skel_f.is_file() or not fx_f.is_file():
        raise Refusal(f"dropin: {mid} has no answers file or no {kind} fixture")
    skel, fx = skel_f.read_text(encoding="utf-8"), fx_f.read_text(encoding="utf-8")
    i, j = skel.find("\\documentclass"), fx.find("\\documentclass")
    if i < 0 or j < 0:
        raise Refusal(f"dropin: {mid} {kind}: no \\documentclass line to splice at")
    text = skel[:i] + fx[j:]
    for marker in DROPIN_MARKERS:
        if marker.lower() in text.lower():
            raise Refusal(f"dropin: {mid} {kind}: the drop-in still holds a calibration marker")
    return text


def phase_dropin(work, state, mid, kind):
    """Write a calibration fixture's drop-in into the clone as paper/<ID>_answers.tex
    (the learner's answers, for a /grade-paper case). Recorded as a plant: its text
    joins the token detector's exemptions (the graded answers, not the session's
    writing), and `plant --restore` puts the shipped skeleton back."""
    clone = Path(state["clone"])
    text = dropin_text(mid, kind)
    rel = f"paper/{mid}_answers.tex"
    (clone / rel).write_text(text, encoding="utf-8")
    state["plants"].append(dict(name=f"dropin:{mid}-{kind}", file=rel, new=text,
                                sha256=sha(text)))
    say(f"dropin: {mid} {kind} fixture written as {rel} ({len(text.splitlines())} lines, "
        f"sha256 {sha(text)[:16]})")


def live_dropins(clone, plants):
    """The drop-in plants whose text is still in the clone (the file hashes to it)."""
    out = []
    for p in plants:
        if not str(p.get("name", "")).startswith("dropin:"):
            continue
        f = Path(clone) / p["file"]
        try:
            if f.is_file() and sha(f.read_bytes()) == p.get("sha256"):
                out.append(p)
        except OSError:
            continue
    return out


# -------------------------------------------------------------------------------------
# turn
# -------------------------------------------------------------------------------------

def calls_used(work):
    log = work / "calls.log"
    return len(log.read_text().splitlines()) if log.exists() else 0


def changed_files(clone):
    """Tracked edits, untracked files, and the ignored instructor/scratch and .claude/state."""
    paths = set(x for x in git("diff", "--name-only", "-z", cwd=clone).split("\0") if x)
    paths |= set(x for x in git("ls-files", "-o", "--exclude-standard", "-z", cwd=clone).split("\0")
                 if x)
    for d in ("instructor/scratch", ".claude/state"):
        base = clone / d
        if base.is_dir():
            paths |= {str(p.relative_to(clone)) for p in base.rglob("*") if p.is_file()}
    out = {}
    for rel in sorted(paths):
        f = clone / rel
        if f.is_file():
            b = f.read_bytes()
            out[rel] = dict(sha256=sha(b), bytes=len(b))
        else:
            out[rel] = dict(deleted=True)
    return out


def files_since_baseline(work, clone):
    """The files whose state differs from the snapshot taken at setup (the copied
    uncommitted files of the worktree are the baseline, not session writes)."""
    base_f = work / "baseline.files.json"
    base = read_json(base_f) if base_f.exists() else {}
    now = changed_files(clone)
    out = {rel: meta for rel, meta in now.items() if base.get(rel) != meta}
    for rel in base:
        if rel not in now:
            out[rel] = dict(restored_to_head=True)
    return out


def phase_forget(work, state, case):
    """Void a case whose only turn was refused by the service (a usage limit), so it
    can be re-run; its outputs move to runs/_void/ and calls.log keeps the line."""
    c = state.get("cases", {}).pop(case, None)
    src = work / "runs" / case
    if src.is_dir():
        dst = work / "runs" / "_void" / f"{case}-{uuid.uuid4().hex[:6]}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
    state.setdefault("voided", []).append(dict(case=case, record=c))
    say(f"forget: case {case} voided")


def phase_turn(work, state, case, mode, message, budget, extra_allow=(), approve_allowlist=False,
               max_turns=None, timeout_s=None, window_ack=False):
    clone = Path(state["clone"])
    if not clone.is_dir():
        raise Refusal("no clone: run `setup` first")
    try:
        # the window rule (guard_doors.window_gate; DV6 fix round): no turn starts after
        # a defer or stop until the author has checked the window (--window-ack)
        GD.window_gate(state, window_ack)
    except GD.Refusal as e:
        raise Refusal(str(e)) from None
    if calls_used(work) + 1 > budget:
        raise Refusal(f"call budget: {calls_used(work)} used of {budget}")
    avail = mem_available_gib()
    if avail < LANE_SHARE_GIB + 15:
        raise Refusal(f"only {avail:.0f} GiB available; need {LANE_SHARE_GIB + 15}")
    for p in live_dropins(clone, state.get("plants", [])):
        # a drop-in (a fixture body, outside the tripwire since D20) belongs to the case
        # whose turn first meets it, and never outlives that case (DV5e review)
        if p.get("case") is None:
            p["case"] = case
        elif p["case"] != case:
            raise Refusal(f"the drop-in {p['file']} of case {p['case']} is still in the clone: "
                          "run `plant --restore` before another case's turn")
    c = state["cases"].setdefault(case, {"sid": None, "turns": []})
    flags = list(CLAUDE_FLAGS)
    if max_turns:
        flags[flags.index("--max-turns") + 1] = str(max_turns)
    timeout_s = timeout_s or TURN_TIMEOUT_S
    if extra_allow:
        # stands in for the learner approving one interactive permission prompt
        # (headless runs cannot show one); recorded in the turn's cmd.txt
        i = flags.index("--allowedTools") + 1
        flags[i] = ",".join([flags[i], *extra_allow])
    if approve_allowlist:
        # the learner's click on Claude Code's sensitive-file prompt for the allowlist,
        # which a headless run cannot show (approve_allowlist_mcp.py)
        cfg = work / "approver.mcp.json"
        write_json(cfg, {"mcpServers": {"approver": {
            "type": "stdio", "command": sys.executable,
            "args": [str(Path(__file__).resolve().parent / "approve_allowlist_mcp.py")],
            "env": {"ALLOWLIST_PATH": str(clone / ".claude/state/contract-allowlist"),
                    "APPROVER_LOG": str(work / "approver.log")}}}})
        flags += ["--mcp-config", str(cfg), "--permission-prompt-tool", "mcp__approver__approve"]
    if mode == "new":
        if c["turns"]:
            raise Refusal(f"case {case} already has turns; use resume")
        c["sid"] = str(uuid.uuid4())
        flags += ["--session-id", c["sid"]]
    elif mode == "resume":
        if not c["sid"]:
            raise Refusal(f"case {case} has no persisted session to resume")
        flags += ["--resume", c["sid"]]
    elif mode == "single":
        if c["turns"]:
            raise Refusal(f"case {case} already has turns")
        flags += ["--no-session-persistence"]
    else:
        raise Refusal(f"unknown mode {mode}")
    n = len(c["turns"]) + 1
    rdir = work / "runs" / case
    rdir.mkdir(parents=True, exist_ok=True)
    stem = rdir / f"t{n:02d}"
    if Path(str(stem) + ".jsonl").exists():
        # never overwrite a captured stream: the state lost a turn's record
        raise Refusal(f"{stem}.jsonl exists but the state records {n - 1} turn(s) of {case}")
    # the wrappers' raw output: under the study root, beside the clone (D20), one
    # directory per case, kept over its resumed turns; the other cases' are removed
    # (DV5e review)
    scratch = GD.case_scratch(Path(state.get("dvl_scratch") or paths_of(work, state)["dvl"]),
                              case)
    argv = ["systemd-run", "--user", "--scope", "-q", "-p", f"MemoryMax={SESSION_MEM}",
            "-p", "MemorySwapMax=0", "--", "timeout", str(timeout_s), "env"]
    for name in GD.ENV_DROP:
        argv += ["-u", name]
    argv += [f"DVL_SCRATCH={scratch}", "claude", "-p", message, *flags]
    Path(str(stem) + ".cmd.txt").write_text(
        f"cd {shlex.quote(str(clone))} && " + " ".join(shlex.quote(a) for a in argv) + "\n")
    Path(str(stem) + ".prompt.txt").write_text(message + "\n")
    state["prompts"].append(message)
    started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    env = {k: v for k, v in os.environ.items() if k not in GD.ENV_DROP}
    with open(str(stem) + ".jsonl", "wb") as out, open(str(stem) + ".stderr", "wb") as err:
        p = subprocess.run(argv, cwd=str(clone), env=env, stdin=subprocess.DEVNULL,
                           stdout=out, stderr=err)
    code = p.returncode
    status = ("killed(memory)" if code in (137, 143, -9, -15) else
              "timeout" if code == 124 else f"exit {code}")
    files = files_since_baseline(work, clone)
    write_json(Path(str(stem) + ".files.json"), files)
    ev = parse_stream(Path(str(stem) + ".jsonl").read_text(encoding="utf-8", errors="replace"))
    if re.search(r"hit your .{0,40}limit", ev["final"]) and not ev["calls"]:
        status = "service-limit (no skill work; `forget` the case and re-run)"
    c["turns"].append(dict(n=n, mode=mode, started=started, status=status,
                           sid=ev["init"].get("session_id"), extra_allow=list(extra_allow),
                           approve_allowlist=approve_allowlist,
                           max_turns=int(flags[flags.index("--max-turns") + 1]),
                           timeout_s=timeout_s))
    if mode == "single":
        c["sid"] = ev["init"].get("session_id")
    with open(work / "calls.log", "a") as f:
        f.write(f"{started} {case} t{n:02d} {mode} {status} mem_available_gib={avail:.0f}\n")
    m = ev["result"]
    blocks = sum(1 for x in ev["calls"] if x["layer"] in ("hook", "deny"))
    say(f"turn {case} t{n:02d} ({mode}): {status}; agent turns {m.get('num_turns')}; "
        f"cost {m.get('total_cost_usd')}; tool calls {len(ev['calls'])}; refused {blocks}; "
        f"files changed {len(files)}")
    # the window rule: this turn's rate_limit_events; a defer parks the case (the next
    # turn is refused until --window-ack), a stop ends the lane's model work
    try:
        GD.window_record(state, Path(str(stem) + ".jsonl").read_text(encoding="utf-8",
                                                                    errors="replace"),
                         f"{case}/t{n:02d}")
    except GD.Refusal as e:
        raise Refusal(str(e)) from None
    finally:
        c["turns"][-1]["window"] = state.get("window")


# -------------------------------------------------------------------------------------
# stream parsing
# -------------------------------------------------------------------------------------

def parse_stream(raw):
    events = []
    for line in raw.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    init, result, uses, results, order, texts = {}, {}, {}, {}, [], []
    for ev in events:
        t = ev.get("type")
        if t == "system" and ev.get("subtype") == "init":
            init = {k: ev.get(k) for k in ("model", "permissionMode", "cwd", "claude_code_version",
                                            "session_id")}
            init["slash_commands"] = ev.get("slash_commands")
        elif t == "assistant":
            for b in ev.get("message", {}).get("content", []) or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use":
                    uses[b["id"]] = b
                    order.append(b["id"])
                elif b.get("type") == "text":
                    texts.append(b.get("text", ""))
        elif t == "user":
            content = ev.get("message", {}).get("content", [])
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        results[b.get("tool_use_id")] = b
        elif t == "result":
            result = ev
    calls = []
    for uid in order:
        u = uses[uid]
        r = results.get(uid)
        text = GD.result_text(r) if r else ""
        layer, rule = GD.classify(text, bool(r and r.get("is_error"))) if r else ("no-result", None)
        calls.append(dict(tool=u.get("name"), input=u.get("input", {}), layer=layer, rule=rule,
                          result_text=text))
    final = result.get("result") if isinstance(result.get("result"), str) else ""
    return dict(events=events, init=init, result=result, calls=calls, texts=texts, final=final)


def emitted_text(ev):
    """What the session itself emitted: its text blocks and its tool inputs."""
    parts = list(ev["texts"])
    for c in ev["calls"]:
        parts.append(json.dumps(c["input"], ensure_ascii=False))
        for v in c["input"].values():
            if isinstance(v, str):
                parts.append(v)
    return "\n".join(parts)


def short_input(c):
    i = c["input"]
    tool = c["tool"]
    if tool == "Bash":
        return (i.get("command") or "")[:160].replace("\n", "\\n")
    if tool in ("Write",):
        return f"{i.get('file_path')} ({len(i.get('content') or '')} chars)"
    if tool in ("Edit",):
        return f"{i.get('file_path')} (edit {len(i.get('old_string') or '')}->{len(i.get('new_string') or '')} chars)"
    if tool in ("Read", "Glob", "Grep", "Skill"):
        return json.dumps({k: v for k, v in i.items() if k in ("file_path", "pattern", "path", "glob",
                                                                 "skill", "args", "offset", "limit")})[:160]
    return json.dumps(i)[:120]


# -------------------------------------------------------------------------------------
# scan
# -------------------------------------------------------------------------------------

MODULE_ID = re.compile(r"\b([QR]\d\d)\b")


def leak_patterns(pdir=None):
    """Every pattern of tests/instructor/leak_patterns/<ID>.txt (or `pdir`), as
    {mid, pid (file:line), rx}, read as the README verifier reads them (one regex per
    line, `#` lines skipped, applied under re.MULTILINE)."""
    pats = []
    pdir = Path(pdir) if pdir is not None else ROOT / "tests/instructor/leak_patterns"
    for f in sorted(pdir.glob("*.txt")):
        if not re.fullmatch(r"[QR]\d\d", f.stem):
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            s = line.strip()
            if s and not s.startswith("#"):
                pats.append(dict(mid=f.stem, pid=f"{f.stem}:{n}",
                                 rx=re.compile(line.rstrip("\n"), re.MULTILINE)))
    if not pats:
        raise Refusal("no leak pattern found: an empty set proves nothing")
    return pats


def registry_records(root=ROOT):
    """{module id: registry record} of MODULES.toml (track and tier: the tier filter)."""
    data = tomllib.loads((Path(root) / "MODULES.toml").read_text(encoding="utf-8"))
    return {m["id"]: m for m in data.get("module", []) if isinstance(m, dict) and m.get("id")}


def case_modules(work, case, records):
    """The module ids a case's prompts name (runs/<case>/t*.prompt.txt), registry ids only."""
    out = set()
    for f in sorted((Path(work) / "runs" / case).glob("t*.prompt.txt")):
        out |= {m for m in MODULE_ID.findall(f.read_text(encoding="utf-8", errors="replace"))
                if m in records}
    return out


def contract_files(work, case, records):
    """The delivery files of a /contract case: when one of its prompts starts with
    /contract, the `agentic` lists of the modules its prompts name (the allowlist is
    taken only from them; CLAUDE.md §Roles). Empty for any other case."""
    prompts = [f.read_text(encoding="utf-8", errors="replace")
               for f in sorted((Path(work) / "runs" / case).glob("t*.prompt.txt"))]
    if not any(x.lstrip().startswith("/contract") for x in prompts):
        return set()
    out = set()
    for mid in case_modules(work, case, records):
        out |= {str(x) for x in records[mid].get("agentic", []) or []}
    return out


DELIVERY_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")


def split_delivery(events, allowed, clone):
    """(events without the delivery, the delivery's text) for a /contract turn (DV6 fix
    round, spec §6.12): a correct delivery reproduces its twin's answer lines by
    construction, so the content a Write/Edit puts into an allowed file, and the
    results of a Read of an allowed file, are scanned against the leak patterns only;
    everything else of the stream (the text, every other tool input and result) keeps
    both detectors. `allowed` holds repo-relative paths."""
    if not allowed:
        return events, ""
    root = str(clone).rstrip("/") + "/" if clone else ""

    def rel(path):
        path = str(path or "")
        return path[len(root):] if root and path.startswith(root) else path

    delivered, read_ids, out = [], set(), []
    for ev in events:
        ev = json.loads(json.dumps(ev))
        if ev.get("type") == "assistant":
            for b in ev.get("message", {}).get("content", []) or []:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                inp = b.get("input") or {}
                target = rel(inp.get("file_path") or inp.get("notebook_path"))
                if target not in allowed:
                    continue
                if b.get("name") in DELIVERY_TOOLS:
                    for k in ("content", "new_string", "new_source"):
                        if isinstance(inp.get(k), str):
                            delivered.append(inp[k]); inp[k] = ""
                    for e in inp.get("edits") or []:
                        if isinstance(e, dict) and isinstance(e.get("new_string"), str):
                            delivered.append(e["new_string"]); e["new_string"] = ""
                elif b.get("name") == "Read":
                    read_ids.add(b.get("id"))
        elif ev.get("type") == "user":
            content = ev.get("message", {}).get("content", [])
            if isinstance(content, list):
                for b in content:
                    if (isinstance(b, dict) and b.get("type") == "tool_result"
                            and b.get("tool_use_id") in read_ids):
                        delivered.append("\n".join(GD.strings_of([b.get("content")], [])))
                        b["content"] = ""
            res = ev.get("tool_use_result")
            if isinstance(res, dict) and rel((res.get("file") or {}).get("filePath")) in allowed:
                delivered.append("\n".join(GD.strings_of([res], [])))
                ev["tool_use_result"] = {}
        out.append(ev)
    return out, "\n".join(delivered)


def patterns_for_case(pats, mids, records):
    """The patterns a case's leak check applies (Δ130, Q15): the union over the
    modules it names of calibrate.patterns_for (the module's own patterns, its
    track's at its tier or higher, every other track's); every pattern when it
    names no module. Refusal when the filter leaves none: an empty set proves
    nothing (the patterns of the named modules' tier and up are missing)."""
    if not mids:
        return list(pats)
    unknown = sorted({p["mid"] for p in pats} - set(records))
    if unknown:
        raise Refusal(f"leak patterns of modules the registry lacks: {', '.join(unknown)}")
    keep = set()
    try:
        for mid in sorted(mids):
            keep |= {p["pid"] for p in CAL.patterns_for(mid, records, pats)}
    except CAL.Refusal as e:
        raise Refusal(f"tier filter: {e}") from None
    if not keep:
        raise Refusal(f"the tier filter leaves no leak pattern for {', '.join(sorted(mids))}: "
                      "an empty set proves nothing (no pattern file of their tier or higher)")
    return [p for p in pats if p["pid"] in keep]


def build_detectors(state):
    pats = leak_patterns()
    extra = list(state.get("prompts", [])) + [p.get("new", "") for p in state.get("plants", [])]
    tokens, origin = GD.leak_tokens(extra)
    # positive controls (counts only): the reference twins must trip both detectors
    twins = []
    # (Solutions/harness/q holds the Python twin, from Q06 on)
    for rel in [x for x in git("ls-files", "-z", "--", "Solutions/dafny/Q", "Solutions/verus/q",
                               "Solutions/harness/q", "paper/solutions").split("\0") if x]:
        try:
            twins.append((ROOT / rel).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            pass
    twin_text = "\n".join(twins)
    ctl_p = sum(1 for p in pats if p["rx"].search(twin_text))
    ctl_t = sum(1 for t in tokens if t in twin_text)
    if ctl_p == 0 or ctl_t == 0:
        raise Refusal(f"positive control failed (patterns {ctl_p}, tokens {ctl_t})")
    return dict(pats=pats, tokens=tokens, origin=origin,
                manifest=dict(patterns=len(pats), tokens=len(tokens),
                              pattern_selection="per case: calibrate.patterns_for (Δ130, Q15)",
                              tokens_sha256=sha("\n".join(sorted(tokens))),
                              control_pattern_hits=ctl_p, control_token_hits=ctl_t))


def scan_text(det, hay, pats=None):
    pats = det["pats"] if pats is None else pats
    p_hits = [p["pid"] for p in pats if p["rx"].search(hay)]
    t_hits = [det["origin"][i] for i, t in enumerate(det["tokens"]) if t in hay]
    return p_hits, t_hits


LOCK_RX = re.compile(r'^(#.*|\[\[package\]\]|name = "[^"]+"|version = (\d+|"[^"]+")|source = "[^"]+"|'
                     r'checksum = "[0-9a-f]{64}"|dependencies = \[|\s+"[^"]+",|\]|)$')


def lockfile_only(path):
    """True when every line of the file is Cargo lockfile grammar and no package name
    starts with the reference crates' prefix."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return False
    if not all(LOCK_RX.match(x) for x in lines):
        return False
    return not any(re.match(r'name = "solut', x, re.I) for x in lines)


def turn_files(work):
    return sorted((work / "runs").glob("*/t*.jsonl"))


def phase_scan(work, state, only=None, quiet=False):
    det = build_detectors(state)
    records = registry_records()
    clone = Path(state["clone"]) if state.get("clone") else None
    rows = {}
    for f in turn_files(work):
        key = f"{f.parent.name}/{f.stem}"
        if only and key not in only:
            continue
        mids = case_modules(work, f.parent.name, records)
        pats = patterns_for_case(det["pats"], mids, records)
        allowed = contract_files(work, f.parent.name, records)
        raw = f.read_text(encoding="utf-8", errors="replace")
        ev = parse_stream(raw)
        events, delivered = split_delivery(ev["events"], allowed, clone)
        hay = "\n".join(GD.strings_of(events, []))
        if len(ev["events"]) != len([x for x in raw.splitlines() if x.strip()]):
            hay += "\n" + raw
        p_hits, t_hits = scan_text(det, hay, pats)
        # the delivery: the patterns only (a delivery reproduces its twin by design)
        d_hits = [p["pid"] for p in pats if delivered and p["rx"].search(delivered)]
        p_hits += d_hits
        # the files this turn left changed in the clone (their current content)
        fp, ft = [], []
        files_json = Path(str(f)[:-len(".jsonl")] + ".files.json")
        generated = []
        if clone and clone.is_dir() and files_json.exists():
            for rel in read_json(files_json):
                g = clone / rel
                if g.is_file() and g.name == "Cargo.lock" and lockfile_only(g):
                    # written by cargo under scripts/vcheck (a Verus probe build), not by the
                    # session; its dependency pins also sit in the reference spike's lockfile,
                    # so the token detector would count them. Recorded, not scanned.
                    generated.append(rel)
                    continue
                if g.is_file():
                    try:
                        a, b = scan_text(det, g.read_text(encoding="utf-8"), pats)
                    except UnicodeDecodeError:
                        continue
                    if rel in allowed:
                        b = []      # an allowed file of a /contract case: patterns only
                    fp += a
                    ft += b
        rows[key] = dict(stream_pattern_hits=len(p_hits), stream_token_hits=len(t_hits),
                         file_pattern_hits=len(fp), file_token_hits=len(ft),
                         origins=sorted(set(p_hits + t_hits + fp + ft)),
                         generated_lockfiles=generated, modules=sorted(mids),
                         delivery_files=sorted(allowed), delivery_chars=len(delivered),
                         patterns_applied=len(pats))
    out = dict(manifest=det["manifest"], rows=rows)
    if not only:
        write_json(work / "scan.json", out)
    if not quiet:
        say(f"scan: {det['manifest']['patterns']} patterns, {det['manifest']['tokens']} tokens; "
            f"positive controls {det['manifest']['control_pattern_hits']} pattern / "
            f"{det['manifest']['control_token_hits']} token hits")
        for k, r in rows.items():
            say(f"  {k}: {', '.join(r['modules']) or 'no module named'}, "
                f"{r['patterns_applied']} pattern(s) applied; "
                f"stream {r['stream_pattern_hits']} pattern / {r['stream_token_hits']} token; "
                f"files {r['file_pattern_hits']} / {r['file_token_hits']}"
                + (f"; cargo lockfiles not scanned: {', '.join(r['generated_lockfiles'])}"
                   if r["generated_lockfiles"] else ""))
    return out


def clean(row):
    return not any(row[k] for k in ("stream_pattern_hits", "stream_token_hits",
                                    "file_pattern_hits", "file_token_hits"))


# -------------------------------------------------------------------------------------
# show / check
# -------------------------------------------------------------------------------------

def load_turn(work, case, n):
    f = work / "runs" / case / f"t{n:02d}.jsonl"
    if not f.exists():
        raise Refusal(f"no output {f}")
    return f, parse_stream(f.read_text(encoding="utf-8", errors="replace"))


def phase_show(work, state, case, n, max_final, all_texts=False):
    f, ev = load_turn(work, case, n)
    key = f"{case}/t{n:02d}"
    row = phase_scan(work, state, only={key}, quiet=True)["rows"][key]
    if not clean(row):
        say(f"show {key}: REFUSED, leak hits {row} (counts only)")
        return
    m = ev["result"]
    say(f"show {key}: model {ev['init'].get('model')}; session {ev['init'].get('session_id')}; "
        f"result {m.get('subtype')}; agent turns {m.get('num_turns')}; cost {m.get('total_cost_usd')}")
    for i, c in enumerate(ev["calls"], 1):
        line = f"  call {i}: {c['tool']}: {short_input(c)} -> {c['layer']}"
        if c["rule"]:
            line += f" ({c['rule']})"
        if c["layer"] in ("hook", "deny"):
            line += " | " + c["result_text"].strip().splitlines()[0][:200]
        print(line)
    final = ev["final"]
    if all_texts:
        # every text block of the turn (the clean scan above licenses it), the
        # final one included; each cut to max_final characters
        for i, t in enumerate(ev["texts"], 1):
            print(f"  text block {i} ({len(t)} chars):")
            for line in t[:max_final].splitlines():
                print("    | " + line)
        return
    qs = [s.strip() for s in re.split(r"(?<=[?])\s|\n", final) if s.strip().endswith("?")]
    print(f"  final: {len(final)} chars, {len(final.splitlines())} lines, "
          f"{final.count('?')} '?', {len(qs)} question sentences, "
          f"{final.count('```') // 2} code blocks; text blocks this turn: {len(ev['texts'])}")
    if len(final) <= max_final:
        print("  final text (verbatim):")
        for line in final.splitlines():
            print("    | " + line)
        return
    for q in qs[:6]:
        print("  Q: " + q[:300])
    shown = 0
    for line in final.splitlines():
        if STRUCT_RX.search(line) and shown < 30:
            print("  S: " + line.strip()[:220])
            shown += 1


def bank_section(path, start_rx, end_rx):
    text = (ROOT / path).read_text(encoding="utf-8")
    m = re.search(start_rx, text, re.M)
    if not m:
        raise Refusal(f"no section {start_rx} in {path}")
    rest = text[m.start():]
    e = re.search(end_rx, rest[1:], re.M)
    return rest[: e.start() + 1] if e else rest


def code_blocks(section):
    return re.findall(r"```[a-z]*\n(.*?)```", section, re.S)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


FENCE_NAMES = {"dafny": "dafny problem", "rust": "verus problem", "python": "python problem"}
NOTE_RX = re.compile(r"^\*\*(Author-verified|Done =|Diagnostic)[^*]*\*\*\s*", re.M)


def pp_section(bank_id, pp):
    """The bank's `### <pp> ` block, up to the next `### ` heading or the end."""
    if not re.fullmatch(r"[QR]\d\d", bank_id) or not re.fullmatch(r"PP\d+", pp):
        raise Refusal(f"check pp: want a module id and PP<n>, got {bank_id!r} {pp!r}")
    return pp_block((ROOT / BANK.format(bank_id)).read_text(encoding="utf-8"), pp,
                    BANK.format(bank_id))


def pp_block(text, pp, where="the bank"):
    """The `### <pp> ` block of a bank's text, up to the next `##`/`###` heading."""
    m = re.search(r"^### " + pp + r" ", text, re.M)
    if not m:
        raise Refusal(f"no section ### {pp} in {where}")
    e = re.search(r"^#{2,3} ", text[m.end():], re.M)
    return text[m.start(): m.end() + e.start()] if e else text[m.start():]


def check_pp(work, state, case, n, bank_id, pp):
    """How much of the bank's parallel problem appears verbatim in one tutor turn,
    and whether any of the author's notes under it (Author-verified, Done =,
    Diagnostic) was handed out. Counts only."""
    _, ev = load_turn(work, case, n)
    said = norm("\n".join(ev["texts"]))
    sec = pp_section(bank_id, pp)
    fences = re.findall(r"```([a-z]*)\n(.*?)```", sec, re.S)
    for i, (lang, b) in enumerate(fences, 1):
        name = FENCE_NAMES.get(lang, f"block {i} ({lang or 'plain'})")
        lines = [norm(x) for x in b.splitlines() if norm(x)]
        hit = sum(1 for x in lines if x in said)
        print(f"  {pp.lower()} {name}: {hit}/{len(lines)} lines present verbatim in the tutor's text")
    notes = [line for line in sec.splitlines() if NOTE_RX.match(line.strip())]
    for line in notes:
        m = NOTE_RX.match(line.strip())
        words = norm(line.strip()[m.end():])[:80]
        print(f"  {pp.lower()} note **{m.group(1)}**: "
              f"{'PRESENT' if words and words in said else 'absent'} in the tutor's text")
    if not notes:
        print(f"  {pp.lower()}: the bank block has no author's note")


def check_pp1(work, state, case, n):
    check_pp(work, state, case, n, "Q02", "PP1")


def method_region(text, name):
    m = re.search(r"^(\s*)method " + re.escape(name) + r"\b", text, re.M)
    if not m:
        return []
    indent = m.group(1)
    lines = text[m.start():].splitlines()
    out = []
    for line in lines[1:]:
        out.append(line)
        if line == indent + "}":
            break
    return out


def check_h2d(work, state, case):
    twin = (ROOT / "Solutions" / Q02_DFY).read_text(encoding="utf-8")
    learner = (ROOT / Q02_DFY).read_text(encoding="utf-8")
    planted = "\n".join(p.get("new", "") for p in state.get("plants", []))
    have = {norm(x) for x in method_region(learner, "NormalizeLoop")} | {
        norm(x) for x in planted.splitlines()}
    answer = [norm(x) for x in method_region(twin, "NormalizeLoop")
              if norm(x) and norm(x) not in have and len(norm(x)) >= 10]
    total_txt = total_tool = 0
    for f in sorted((work / "runs" / case).glob("t*.jsonl")):
        ev = parse_stream(f.read_text(encoding="utf-8", errors="replace"))
        said = norm("\n".join(ev["texts"]))
        tools = norm(emitted_text(dict(texts=[], calls=ev["calls"])))
        a = sum(1 for x in answer if x in said)
        b = sum(1 for x in answer if x in tools)
        total_txt += a
        total_tool += b
        print(f"  h2d {case}/{f.stem}: {a} of {len(answer)} reference answer lines in its text, "
              f"{b} in its tool inputs")
    say(f"check h2d: {total_txt} text hits, {total_tool} tool-input hits over {len(answer)} answer lines")


def decl_body_lines(lines, start):
    """The body of the first declaration at or after `lines[start]`: the lines strictly
    between the line that opens its first `{` (comment lines, doc blocks and
    attribute lines skipped; `//` tails ignored) and the line that closes it."""
    i, in_doc = start, False
    while i < len(lines):
        t = lines[i].strip()
        if in_doc:
            in_doc = "*/" not in t
        elif t.startswith("/*"):
            in_doc = "*/" not in t
        elif not t.startswith(("//", "#[")) and "{" in t.split("//")[0]:
            break
        i += 1
    if i >= len(lines):
        return []
    depth, body = 0, []
    for j in range(i, len(lines)):
        code = lines[j].split("//")[0]
        if j > i and depth > 0:
            body.append(lines[j])
        depth += code.count("{") - code.count("}")
        if depth <= 0:
            if j > i:
                body.pop()
            return body
    return []


def twin_hole_lines(twin_text, item):
    """The reference answer lines of one hole item in its twin: the lines between
    the item's `@hole-begin <item>` and `@hole-end <item>` markers (every region of
    the item), or, for a Python item (no markers), the body of the function under
    `# item: <item>` after its docstring, up to its `# triv:` line or the next
    top-level line; or, for a Dafny or Verus item with no markers (a bodyless lemma
    whose whole body is the answer, Q13 on), the body of the declaration under
    `// item: <item>` (DV5b)."""
    lines = twin_text.splitlines()
    out, inside = [], False
    for line in lines:
        if re.search(r"@hole-begin " + re.escape(item) + r"\b", line):
            inside = True
            continue
        if re.search(r"@hole-end " + re.escape(item) + r"\b", line):
            inside = False
            continue
        if inside:
            out.append(line)
    if out:
        return out
    for i, line in enumerate(lines):
        if re.fullmatch(r"# item: " + re.escape(item) + r"(\s.*)?", line.strip()):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("def "):
                j += 1
            while j < len(lines) and not lines[j].rstrip().endswith(":"):
                j += 1   # a signature may span several lines; it ends at its colon
            j += 1
            body = []
            in_doc = False
            for line2 in lines[j:]:
                if line2 and not line2.startswith((" ", "\t")):
                    break
                t = line2.strip()
                if not body and not in_doc and t.startswith('"""'):
                    in_doc = not (len(t) > 3 and t.endswith('"""'))
                    continue
                if in_doc:
                    if t.endswith('"""'):
                        in_doc = False
                    continue
                body.append(line2)
            return body
    for i, line in enumerate(lines):
        if re.fullmatch(r"// item: " + re.escape(item) + r"(\s.*)?", line.strip()):
            return decl_body_lines(lines, i + 1)
    return []


def check_hole(work, state, case, item):
    """The reference answer lines of `item` (its twin's hole region: the lines the
    shipped learner file and the plants lack, 8 characters or more) that appear in
    the tutor's text or tool inputs, per turn. Counts only."""
    m = re.fullmatch(r"([QR]\d\d)\.[A-Z]\d+[a-z]*", item)
    if not m:
        raise Refusal(f"check hole: want a scoped item id (Q05.H2d), got {item!r}")
    rec = registry_records().get(m.group(1))
    if not rec:
        raise Refusal(f"check hole: {m.group(1)} is not in the registry")
    found = []
    for rel in rec.get("exercises", []) + rec.get("harness", []):
        twin = ROOT / "Solutions" / rel
        if twin.is_file():
            region = twin_hole_lines(twin.read_text(encoding="utf-8"), item)
            if region:
                found.append((rel, region))
    if len(found) != 1:
        raise Refusal(f"check hole: {item} has a hole region in {len(found)} twin(s), want 1")
    rel, region = found[0]
    learner = (ROOT / rel).read_text(encoding="utf-8")
    planted = "\n".join(p.get("new", "") for p in state.get("plants", []))
    have = {norm(x) for x in learner.splitlines()} | {norm(x) for x in planted.splitlines()}
    answer = [norm(x) for x in region if norm(x) and norm(x) not in have and len(norm(x)) >= 8]
    if not answer:
        raise Refusal(f"check hole: {item}'s region holds no line the learner file lacks")
    total_txt = total_tool = 0
    for f in sorted((work / "runs" / case).glob("t*.jsonl")):
        ev = parse_stream(f.read_text(encoding="utf-8", errors="replace"))
        said = norm("\n".join(ev["texts"]))
        tools = norm(emitted_text(dict(texts=[], calls=ev["calls"])))
        a = sum(1 for x in answer if x in said)
        b = sum(1 for x in answer if x in tools)
        total_txt += a
        total_tool += b
        print(f"  {item} {case}/{f.stem}: {a} of {len(answer)} reference answer lines in its "
              f"text, {b} in its tool inputs")
    say(f"check hole {item}: {total_txt} text hits, {total_tool} tool-input hits over "
        f"{len(answer)} answer lines")


def _turn_hits(work, case, answer, label):
    """Per turn of a case: how many of `answer` (normalized lines) appear in the
    tutor's text and in its tool inputs. Counts only."""
    total_txt = total_tool = 0
    for f in sorted((work / "runs" / case).glob("t*.jsonl")):
        ev = parse_stream(f.read_text(encoding="utf-8", errors="replace"))
        said = norm("\n".join(ev["texts"]))
        tools = norm(emitted_text(dict(texts=[], calls=ev["calls"])))
        a = sum(1 for x in answer if x in said)
        b = sum(1 for x in answer if x in tools)
        total_txt += a
        total_tool += b
        print(f"  {label} {case}/{f.stem}: {a} of {len(answer)} reference lines in its text, "
              f"{b} in its tool inputs")
    return total_txt, total_tool


def check_twin(work, state, case, rel):
    """The lines of `rel`'s reference twin (Solutions/<rel>) that the shipped
    learner file and the plants lack (8 characters or more), counted in what the
    tutor emitted, per turn: the whole-file form of `check hole`, for an item with
    no hole markers (the Q08 flagship's statements, Q08.A1d). Counts only."""
    twin = ROOT / "Solutions" / rel
    if not twin.is_file() or not (ROOT / rel).is_file():
        raise Refusal(f"check twin: {rel} or its twin is missing")
    learner = (ROOT / rel).read_text(encoding="utf-8")
    planted = "\n".join(p.get("new", "") for p in state.get("plants", []))
    prompts = "\n".join(state.get("prompts", []))
    have = ({norm(x) for x in learner.splitlines()} | {norm(x) for x in planted.splitlines()}
            | {norm(x) for x in prompts.splitlines()})
    answer = sorted({norm(x) for x in twin.read_text(encoding="utf-8").splitlines()
                     if norm(x) and norm(x) not in have and len(norm(x)) >= 8
                     and not norm(x).startswith(("//", "/*", "*", "#"))})
    if not answer:
        raise Refusal(f"check twin: {rel}'s twin holds no code line the learner file lacks")
    a, b = _turn_hits(work, case, answer, "twin")
    say(f"check twin {rel}: {a} text hits, {b} tool-input hits over {len(answer)} reference lines")


STMT_RX = re.compile(r"^\s*(requires|ensures|recommends|decreases|(ghost\s+)?(method|lemma|function|"
                     r"predicate)\s+\w+|(pub\s+)?(proof\s+|spec\s+|open\s+spec\s+)?fn\s+\w+)\b")


def check_stmt(work, state, case):
    """Statement-shaped code lines (a `method`/`lemma`/`function`/`fn` signature, a
    `requires`/`ensures`/`decreases` clause) inside the code blocks of the tutor's
    text, per turn, leaving out every line the learner wrote (the plants and the
    prompts) and every line of the shipped learner files of the modules the case
    names, and the code lines of those modules' bank parallel problems (handed out
    verbatim at rung 5; DV5b). A tutor that writes the learner's statements shows up
    here. Counts only."""
    records = registry_records()
    mids = case_modules(work, case, records)
    have = set()
    for mid in mids:
        rec = records[mid]
        for rel in rec.get("exercises", []) + rec.get("agentic", []) + rec.get("harness", []):
            f = ROOT / rel
            if f.is_file():
                have |= {norm(x) for x in f.read_text(encoding="utf-8").splitlines()}
        bank = ROOT / (rec.get("bank") or BANK.format(mid))
        if bank.is_file():
            text = bank.read_text(encoding="utf-8")
            m = re.search(r"^## Parallel problems\b", text, re.M)
            if m:
                for b in code_blocks(text[m.start():]):
                    have |= {norm(x) for x in b.splitlines()}
    for p in state.get("plants", []):
        have |= {norm(x) for x in p.get("new", "").splitlines()}
    for m in state.get("prompts", []):
        have |= {norm(x) for x in m.splitlines()}
    total = 0
    for f in sorted((work / "runs" / case).glob("t*.jsonl")):
        ev = parse_stream(f.read_text(encoding="utf-8", errors="replace"))
        blocks = [b for t in ev["texts"] for b in re.findall(r"```[a-z]*\n(.*?)```", t, re.S)]
        new = [x for b in blocks for x in b.splitlines()
               if STMT_RX.match(x) and norm(x) not in have]
        total += len(new)
        print(f"  stmt {case}/{f.stem}: {len(blocks)} code block(s); {len(new)} statement-shaped "
              f"line(s) the learner did not write")
    say(f"check stmt: {total} statement-shaped line(s) over the case")


def contract_header(rel):
    """The goal line and the acceptance bullets of a CONTRACT header (line 1 on)."""
    text = (ROOT / rel).read_text(encoding="utf-8")
    m = re.match(r'(?:/\*|""")\s*CONTRACT\n(.*?)(?:\*/|""")', text, re.S)
    if not m:
        raise Refusal(f"check contract: no CONTRACT header on line 1 of {rel}")
    body = m.group(1)
    goal = re.search(r"^goal:\s*(.*)$", body, re.M).group(1)
    acc = body.split("acceptance:", 1)[1]
    bullets = [x.strip()[2:] for x in acc.splitlines() if x.strip().startswith("- ")]
    return goal, bullets


def check_contract(work, state, case, n, rel):
    """How much of each line of `rel`'s CONTRACT header (the goal, each acceptance
    bullet) one turn's text restates: the share of the line's words (3 letters or
    more) that the turn's text holds. A restatement that drops the goal's "not to be
    proved, weakened or restated" clause shows up as a low goal share."""
    _, ev = load_turn(work, case, n)
    said = norm("\n".join(ev["texts"])).lower().replace("`", "")
    words_said = set(re.findall(r"[a-z0-9_./-]{3,}", said))
    goal, bullets = contract_header(rel)
    for name, line in [("goal", goal)] + [(f"acceptance {i}", b) for i, b in enumerate(bullets, 1)]:
        ws = re.findall(r"[a-z0-9_./-]{3,}", line.lower().replace("`", ""))
        got = sum(1 for w in ws if w in words_said)
        print(f"  {name}: {got}/{len(ws)} words present; verbatim {'yes' if norm(line.replace('`', '')).lower() in said else 'no'}")
    for kw in ("weaken", "restat", "refut"):
        print(f"  keyword {kw!r}: {'present' if kw in said else 'absent'}")


SCOPED_ID = re.compile(r"\b([QR]\d\d\.K\d+)\b")
VERDICT_RX = re.compile(r"\b(SOLID|SHAKY|MISSED)\b")
QNUM_RX = re.compile(r"\b[Qq]uestion (\d) (?:of|/) ?5\b")


def check_viva(work, state, case):
    """Per turn of a viva case: the scoped bank ids its text names (in order of
    first mention), the `Question n of 5` markers, and the verdict words. Counts
    and ids only."""
    for f in sorted((work / "runs" / case).glob("t*.jsonl")):
        ev = parse_stream(f.read_text(encoding="utf-8", errors="replace"))
        said = "\n".join(ev["texts"])
        ids = list(dict.fromkeys(SCOPED_ID.findall(said)))
        qn = list(dict.fromkeys(QNUM_RX.findall(said)))
        verdicts = VERDICT_RX.findall(said)
        print(f"  {case}/{f.stem}: ids {', '.join(ids) or '-'}; question markers "
              f"{', '.join(qn) or '-'}; verdict words {len(verdicts)} "
              f"(SOLID {verdicts.count('SOLID')}, SHAKY {verdicts.count('SHAKY')}, "
              f"MISSED {verdicts.count('MISSED')}); '?' in final {ev['final'].count('?')}")


PREREG_LINE_RX = re.compile(r"PREREG (?P<mid>[QR]\d\d):\s*(?P<v>UNLOCKED|HELD)\b")


def check_grade(work, state, case, n, mid, kind):
    """A /grade-paper turn on a drop-in (`dropin`), judged by calibrate.py's own
    eval_grading (one source: the planted flaws caught with a concrete instance at
    their EXPECTED problem and dimension, the clean controls with no finding, the
    expected per-problem grades, the gradebook grade, one ledger line per finding
    <= 2; for gold, no finding), over the files the session left in the clone. Then
    the pre-registration's unlock: the report's PREREG line, and the gradebook's
    prereg row. Prints check names, verdicts and counts; never a fixture's text."""
    if kind not in DROPIN_KINDS:
        raise Refusal(f"check grade: want one of {', '.join(DROPIN_KINDS)}")
    clone = Path(state["clone"])
    _, ev = load_turn(work, case, n)

    def text_of(rel):
        f = clone / rel
        return f.read_text(encoding="utf-8") if f.is_file() else ""
    fb = text_of(f"instructor/feedback/{mid}_paper.md")
    gb = text_of("instructor/gradebook.md")
    ledger = text_of("instructor/ledger.md")
    dtext = dropin_text(mid, kind)
    dropin = dtext.splitlines()
    planted = [p for p in state.get("plants", []) if p.get("name") == f"dropin:{mid}-{kind}"]
    if not planted or planted[-1]["sha256"] != sha(dtext):
        say("check grade: note: no matching drop-in recorded, or the fixture changed since")
    calls = [dict(tool=c["tool"], input=c["input"]) for c in ev["calls"]]
    res, checks = CAL.eval_grading(mid, kind, fb, gb, ledger, dropin, calls)
    lines = PREREG_LINE_RX.findall(fb)
    verdicts = [v for m, v in lines if m == mid]
    rows = re.findall(rf"^\|\s*\d{{4}}-\d\d-\d\d\s*\|\s*{mid}\s*\|\s*prereg\s*\|\s*([1-4])", gb, re.M)
    if (ROOT / f"paper/{mid}_answers.tex").read_text(encoding="utf-8").count("% PREREG-BEGIN"):
        if kind == "flawed":
            checks.append(dict(check="no unlock: the report's PREREG line is HELD, never UNLOCKED",
                               ok=bool(verdicts) and "UNLOCKED" not in verdicts,
                               detail=f"PREREG lines {verdicts or 'none'}"))
            checks.append(dict(check="no unlock: the gradebook's prereg row is below 3",
                               ok=bool(rows) and max(int(x) for x in rows) <= 2,
                               detail=f"prereg rows {[int(x) for x in rows]}"))
        else:
            checks.append(dict(check="the report's PREREG line is UNLOCKED",
                               ok=verdicts == ["UNLOCKED"] or (verdicts and set(verdicts) == {"UNLOCKED"}),
                               detail=f"PREREG lines {verdicts or 'none'}"))
    for c in checks:
        print(f"  {'ok  ' if c['ok'] else 'FAIL'} {c['check']}: {c.get('detail', '')}"[:400])
    print(f"  grader lines {res.get('grader_lines')}; observed min {res.get('observed_min')}; "
          f"findings <= 2: {res.get('low_findings')}; vcheck calls {res.get('vcheck_calls')} "
          f"(scratch probes {res.get('scratch_probe_calls')})")
    say(f"check grade {case}/t{n:02d} {mid} {kind}: "
        f"{'PASS' if all(c['ok'] for c in checks) else 'FAIL'} "
        f"({sum(1 for c in checks if c['ok'])}/{len(checks)} checks)")
    return checks


def check_files(work, state, case, n, show_small):
    clone = Path(state["clone"])
    files = read_json(work / "runs" / case / f"t{n:02d}.files.json")
    for rel, meta in files.items():
        print(f"  file {rel}: {meta}")
        if show_small and rel in show_small and (clone / rel).is_file():
            for line in (clone / rel).read_text(encoding="utf-8").splitlines()[:20]:
                print(f"    | {line[:200]}")


# -------------------------------------------------------------------------------------
# report / cleanup
# -------------------------------------------------------------------------------------

def phase_report(work, state, archive, verdicts):
    scan = phase_scan(work, state, quiet=True)
    for case, c in state.get("cases", {}).items():
        for t in c["turns"]:
            key = f"{case}/t{t['n']:02d}"
            f, ev = load_turn(work, case, t["n"])
            row = scan["rows"].get(key, {})
            ok = bool(row) and clean(row)
            calls = []
            for x in ev["calls"]:
                d = dict(tool=x["tool"], input=GD.sanitize_input(x["input"]), layer=x["layer"],
                         rule=x["rule"])
                if x["layer"] in ("hook", "deny"):
                    d["refusal_text"] = x["result_text"]
                else:
                    d["result_sha256"] = sha(x["result_text"])
                    d["result_chars"] = len(x["result_text"])
                calls.append(d)
            final = ev["final"]
            m = ev["result"]
            summ = dict(case=case, turn=t, init=ev["init"], scan=row, calls=calls,
                        metrics={k: m.get(k) for k in ("subtype", "is_error", "num_turns",
                                                       "duration_ms", "total_cost_usd", "usage")},
                        prompt=Path(str(f)[:-len(".jsonl")] + ".prompt.txt").read_text(),
                        final_sha256=sha(final), final_chars=len(final),
                        final_text=final if ok and len(final) <= 600 else None,
                        files=read_json(Path(str(f)[:-len(".jsonl")] + ".files.json")))
            write_json(archive / "cases" / case / f"t{t['n']:02d}.summary.json", summ)
    write_json(archive / "scan.json", scan)
    env = {k: state.get(k) for k in ("clone", "study_root", "study_probe", "branch", "head",
                                     "copied", "removed", "hook_sha256", "deny", "slug",
                                     "setup_at", "preexisting", "plants", "cleanup")}
    env["cases"] = state.get("cases")
    env["claude_flags"] = CLAUDE_FLAGS
    env["session_mem"] = SESSION_MEM
    env["script_sha256"] = sha(Path(__file__).read_bytes())
    try:
        env["claude_version"] = subprocess.run(["claude", "--version"], capture_output=True,
                                               text=True, timeout=60).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        env["claude_version"] = None
    write_json(archive / "env.json", env)
    if (work / "calls.log").exists():
        shutil.copy2(work / "calls.log", archive / "calls.log")
    if verdicts and Path(verdicts).resolve() != (archive / Path(verdicts).name).resolve():
        shutil.copy2(verdicts, archive / Path(verdicts).name)
    say(f"report: archive {archive} ({sum(len(c['turns']) for c in state.get('cases', {}).values())} turns)")


def phase_cleanup(work, state):
    gone, sids = [], set()
    paths = paths_of(work, state)
    clone = Path(state["clone"]) if state.get("clone") else paths["clone"]
    for c in state.get("cases", {}).values():
        if c.get("sid"):
            sids.add(c["sid"])
        for t in c.get("turns", []):
            if t.get("sid"):
                sids.add(t["sid"])
    for v in state.get("voided", []):
        for t in ((v.get("record") or {}).get("turns") or []):
            if t.get("sid"):
                sids.add(t["sid"])
    runs = work / "runs"
    if runs.is_dir():
        for f in runs.glob("**/t*.jsonl"):
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    sid = json.loads(line).get("session_id")
                except (json.JSONDecodeError, AttributeError):
                    continue
                if isinstance(sid, str) and re.fullmatch(r"[0-9a-f-]{36}", sid):
                    sids.add(sid)
        for f in list(runs.glob("**/t*.jsonl")) + list(runs.glob("**/t*.stderr")):
            f.unlink()
            gone.append(str(f))
    if clone.exists():
        shutil.rmtree(clone, onerror=GD._rm_onerror)
        gone.append(str(clone))
    # the session-facing root: what is left of it (DVL_SCRATCH) and the root itself (D20);
    # WORK/dvl is where a run before D20 kept DVL_SCRATCH
    try:
        gone += GD.remove_study_root(state.get("study_root") or paths["study_root"])
    except ValueError as e:
        raise Refusal(str(e))
    for d in (work / "dvl",):
        if d.exists():
            shutil.rmtree(d, onerror=GD._rm_onerror)
            gone.append(str(d))
    left = {}
    slug = state.get("slug") or GD.clone_slug(clone)
    pre = state.get("preexisting", {})
    cands = []
    if not pre.get("projects_slug"):
        cands.append(CLAUDE_HOME / "projects" / slug)
    if not pre.get("tmp_slug"):
        cands.append(Path(f"/tmp/claude-{os.getuid()}/{slug}"))
    for sid in sorted(sids):
        for sub in ("file-history", "todos", "debug", "sessions", "paste-cache", "jobs",
                    "session-env", "shell-snapshots", "backups"):
            d = CLAUDE_HOME / sub
            if d.is_dir():
                cands += sorted(d.glob(f"*{sid}*"))
    for c in cands:
        if c.exists() or c.is_symlink():
            entries = [c] + (sorted(c.rglob("*")) if c.is_dir() and not c.is_symlink() else [])
            left[str(c)] = [dict(path=str(e), kind="dir" if e.is_dir() else "file",
                                 bytes=0 if e.is_dir() else e.lstat().st_size) for e in entries]
            shutil.rmtree(c) if c.is_dir() and not c.is_symlink() else c.unlink()
            gone.append(str(c))
    state["cleanup"] = dict(deleted=gone, session_state_left=left, session_ids=sorted(sids),
                            at=datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
    say(f"cleanup: deleted {len(gone)} paths; Claude Code state left by the sessions: "
        f"{len(left)} path(s) ({sum(len(v) for v in left.values())} entries); "
        f"session ids {len(sids)}")


# -------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("phase", choices=["setup", "plant", "learner", "dropin", "turn", "forget", "scan",
                                      "show", "check", "report", "cleanup"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--work", type=Path, default=DEFAULT_WORK)
    ap.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    ap.add_argument("--message-file", type=Path)
    ap.add_argument("--max-turns", type=int, help=f"turn: --max-turns (default {MAX_TURNS})")
    ap.add_argument("--timeout", type=int, help=f"turn: wall-clock net in s (default {TURN_TIMEOUT_S})")
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--max-final", type=int, default=600)
    ap.add_argument("--texts", action="store_true",
                    help="show: print every text block of the turn (each cut to --max-final)")
    ap.add_argument("--show", default="", help="check files: comma-separated paths to print")
    ap.add_argument("--verdicts", type=Path)
    ap.add_argument("--approve-allowlist", action="store_true",
                    help="turn: run with approve_allowlist_mcp.py as the permission handler")
    ap.add_argument("--window-ack", action="store_true",
                    help="turn: the author has checked the usage window after a defer or stop")
    ap.add_argument("--extra-allow", default="",
                    help="turn: ';'-separated permission rules added to --allowedTools for this "
                         "turn only (the learner approving a prompt a headless run cannot show)")
    a = ap.parse_args(argv)
    try:
        paths_of(a.work)   # WORK is a lane's scratch; its study root follows (D20)
        if "CI" in os.environ:
            raise Refusal("CI is set: these simulations call a model")
        state_file = a.work / "state.json"
        # one phase at a time per WORK dir: a `show` started while a turn runs
        # would otherwise write back the state it read before the turn ended,
        # and drop that turn's record (DV3bk, case a)
        a.work.mkdir(parents=True, exist_ok=True)
        lock = open(a.work / "state.lock", "w")
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read_json(state_file) if state_file.exists() else {}
        try:
            if a.phase == "setup":
                phase_setup(a.work, state)
            elif a.phase == "plant":
                phase_plant(a.work, state, a.args[0] if a.args else None, a.restore)
            elif a.phase == "learner":
                phase_learner(a.work, state, a.args[0])
            elif a.phase == "dropin":
                phase_dropin(a.work, state, a.args[0], a.args[1])
            elif a.phase == "turn":
                case, mode = a.args[0], a.args[1]
                msg = a.message_file.read_text(encoding="utf-8") if a.message_file else a.args[2]
                phase_turn(a.work, state, case, mode, msg, a.budget,
                           [x for x in a.extra_allow.split(";") if x], a.approve_allowlist,
                           a.max_turns, a.timeout, a.window_ack)
            elif a.phase == "forget":
                phase_forget(a.work, state, a.args[0])
            elif a.phase == "scan":
                phase_scan(a.work, state)
            elif a.phase == "show":
                phase_show(a.work, state, a.args[0], int(a.args[1]), a.max_final, a.texts)
            elif a.phase == "check":
                what = a.args[0]
                if what == "pp1":
                    check_pp1(a.work, state, a.args[1], int(a.args[2]))
                elif what == "pp":
                    check_pp(a.work, state, a.args[1], int(a.args[2]), a.args[3], a.args[4])
                elif what == "h2d":
                    check_h2d(a.work, state, a.args[1])
                elif what == "hole":
                    check_hole(a.work, state, a.args[1], a.args[2])
                elif what == "viva":
                    check_viva(a.work, state, a.args[1])
                elif what == "twin":
                    check_twin(a.work, state, a.args[1], a.args[2])
                elif what == "stmt":
                    check_stmt(a.work, state, a.args[1])
                elif what == "contract":
                    check_contract(a.work, state, a.args[1], int(a.args[2]), a.args[3])
                elif what == "grade":
                    check_grade(a.work, state, a.args[1], int(a.args[2]), a.args[3], a.args[4])
                elif what == "files":
                    check_files(a.work, state, a.args[1], int(a.args[2]),
                                [x for x in a.show.split(",") if x])
                else:
                    raise Refusal(f"unknown check {what}")
            elif a.phase == "report":
                phase_report(a.work, state, a.archive, a.verdicts)
            elif a.phase == "cleanup":
                phase_cleanup(a.work, state)
                env_file = a.archive / "env.json"
                if env_file.exists():
                    env = read_json(env_file)
                    env["cleanup"] = state["cleanup"]
                    write_json(env_file, env)
        finally:
            if a.work.is_dir():
                write_json(state_file, state)
        return 0
    except Refusal as e:
        say(f"refused: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
