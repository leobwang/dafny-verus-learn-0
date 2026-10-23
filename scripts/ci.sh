#!/usr/bin/env bash
# ci.sh — the course's local CI (phase DV1c). There is no hosted CI (DELTAS
# Δ67): this script runs the CI jobs of design §14.4 on this host, before
# every merge into a shipped branch (basic first, then merged forward into
# challenge; the user's decision D26), and its pass is recorded in the merge
# commit message.
# The spec §8.5 invariants and design rules hold: pure-Python checks first;
# pipefail everywhere; logs to files, only locations and statuses on the
# console; holes counted by the tools, never by grep; an empty id list or glob
# fails, except that a track or job with nothing armed yet passes LOUDLY; it
# never calls a model.
#
# Usage:
#   scripts/ci.sh                  every job except brittleness (a study run)
#   scripts/ci.sh --quick          static and hook-test only
#   scripts/ci.sh --job NAME ...   the named jobs (repeat --job, give a comma
#                                  list, or name the jobs bare)
#   scripts/ci.sh --list           print the jobs it would run; run nothing
#   scripts/ci.sh --author ...     add the reference-touching steps (below)
#   scripts/ci.sh --brittleness    add the brittleness job (on request only)
#   --log-dir DIR                  write the logs to DIR instead of
#                                  build/ci/<run>/ (gitignored)
#   --root DIR                     (tests) check the course at DIR with this
#                                  checkout's scripts; hook-test, wrappers,
#                                  corpus, the checker's own suite and the
#                                  fixture drift check always test this
#                                  checkout
#
# Jobs, in run order (`--list` prints them; [A] marks steps that run only
# with --author):
#   static          tool-free, seconds: study mode shipped (below);
#                   check_course_map.py (all six groups); test_course_map.py;
#                   gen_units.py --check; gen_hook_fixtures.py --check;
#                   check_single_route.py (only the entry points start
#                   containers, agents or sudo); the sandbox's refused source
#                   classes against the guard's and the checker's reference
#                   paths; .gitignore leaves the ledger anchors, ledgers and
#                   run records tracked (DV4); check_release_history.py on
#                   basic (the local branch, else origin/basic) against main:
#                   a linear chain of single-parent "basic: " commits with no
#                   archived ancestry (D42, D46; loud when either is absent);
#                   firsttry.sh --lint-hollow --all; specfreeze --check per
#                   armed module; chapter_lint.py --all (each armed module's
#                   chapter: the spec §2.4.3 skeleton, the files table's
#                   pinned hole counts, predict boxes before the outputs that
#                   answer them, pinned bare output fences, diagrams, item
#                   ids; pins.py --chapter's static half); avoid.sh (the
#                   disjointness gate between the tracks, spec §2.7: names,
#                   curated Lean names, owner tags, corpus halves, waivers);
#                   [A] reference_lint.py
#   hook-test       scripts/test_hooks.sh
#   verify-q-dafny, verify-q-verus, verify-r-dafny, verify-r-verus
#                   the toolchains on PATH are the pinned versions (vcheck
#                   --versions; DELTAS Δ503, D79: a mismatch fails CI);
#                   every given layer of the track gates and audits clean
#                   (vcheck --gate, vaudit; for Verus also vaudit
#                   --check-trust, once per run); per armed module, every
#                   file of the language is in its shipped state (vcheck
#                   --shipped --json <ID> d|v: each unit, check unit, exit
#                   and agent file in the learner loop gives the verdict,
#                   tool-counted holes and errors pinned in
#                   expected/<ID>.counts, so an exit file's hole count and an
#                   agent file's RED state are compared too), and each unit's
#                   tool-counted holes equal the hole forms its items ship,
#                   item by item (no stray hole, none missing); [A] the
#                   reference gate and audit of every unit twin and of every
#                   exit, check and agent twin (vcheck --ref, vaudit --ref; a
#                   missing twin fails). A track with nothing armed and no
#                   given layer passes LOUDLY.
#   pins            golden pins: pins.py --ci (verdict, count and sidecar
#                   pins, and every armed module's chapter pins: each pinned
#                   output fence re-run and compared); [A] pins.py --ref
#   empty-body      [A] firsttry.sh <ID> --empty-body per armed module
#   corpus          the cheat corpus: test_corpus.py --list (never empty),
#                   then --ci. An absent corpus fails (DELTAS Δ108, Δ109):
#                   a missing scripts/test_corpus.py or tests/corpus/, a
#                   failed --list or an empty one fails the job before any
#                   solver step, and so does a listed fixture outside the
#                   canonical layout tests/corpus/<lang>/<ID>/
#   wrappers        the tool suites: unittest discover -s tests/wrappers,
#                   then -s tests/ci (this script's own tests)
#   coexist         learner files only: every armed Dafny unit of both
#                   tracks resolves as one program (no duplicate declaration);
#                   Verus crate names are unique; the Python half arrives with
#                   the harness (DV4)
#   paper           make -C paper paper, with the empty-set rule (an armed
#                   module with paper = true needs its pair; nothing armed
#                   and no pair passes LOUDLY); [A] make paper-solutions
#   rubric          [A] update_rubric_pins.sh --check
#   harness         the Python harness (QPLAN §11.8): uv lock --check and uv
#                   sync --frozen, offline, the environment in scratch; then,
#                   in the sterile environment (an empty HOME, XDG and
#                   CLAUDE_CONFIG_DIR, the fake apparatus file, FVH_NO_MODEL=1,
#                   DVL_NO_DOCKER=1, tripwire shims for claude, opencode,
#                   ollama, docker and sudo whose markers fail the job, and
#                   the socket tripwire of harness/tests/conftest.py): pytest
#                   tests/core; the adapter suite tests/harness_adapter; the
#                   sandbox suite tests/sandbox and the benchmark suite
#                   tests/bench (no Docker, no network; DV4); the
#                   learner Python files' AST holes and hollow lint; the import
#                   tiers; each armed module's Python files against their
#                   shipped-state pins once expected/<ID>.counts holds them;
#                   [A] each twin's reference gate and the Python TRIV mode.
#                   No harness/ project and no armed harness file passes LOUDLY
#   brittleness     (--brittleness only) vcheck --brittleness on every given
#                   layer and every armed unit; [A] vcheck --ref --brittleness
#                   on every armed unit's twin (Dafny with --solvers)
# The module-level checks (specfreeze, pins.py, firsttry --empty-body) check
# both languages at once, so they run once per run, in static, pins and
# empty-body, rather than in each verify job.
#
# Author mode (--author) adds the steps marked [A]: they read the reference
# (Solutions/, paper/solutions/) or run the memory-heavy empty-body modes.
# ci.sh refuses --author (exit 3) on a leobwang-* branch, always, and
# otherwise unless CI=true or the three-condition test holds (inside git, a
# linked worktree, HEAD not on a learner branch: spec §7.4). It never sets CI
# itself: the author-only tools gate themselves on the same test. Without
# --author, CI is removed from every step's environment and the [A] steps are
# skipped and reported, so no self-gated tool reads the reference: a study
# run is safe in the learner's checkout and in a study-mode session (guard
# rule 1b lets scripts/ci.sh run). The pre-merge gate is a full author run in
# the authoring worktree after scripts/course_mode.sh study.
#
# Study mode shipped (spec §7.4, §8.5; Δ80, Δ87): the static job fails if
# .claude/state/mode exists, or if .claude/settings.json (the working tree,
# and HEAD's copy when it is committed) lacks any of the four canonical deny
# rules
#   Read(./Solutions/**)
#   Read(./paper/solutions/**)
#   Read(./tests/instructor/leak_patterns/**)
#   Read(~/.cache/dafny-verus-learn-0/**)
# or any of the four always-on rules, or if scripts/course_mode.sh's lists
# differ from this script's (CLAUDE.md, course_mode.sh, test_hooks.sh and
# this script must agree).
#
# Memory (DELTAS Δ503, D78): the course applies no memory management; memory
# is the host's and the user's (run ci.sh under your own limit, e.g.
# `systemd-run --user --scope -p MemoryMax=32G -p MemorySwapMax=0 scripts/ci.sh`).
# Jobs run one solver job at a time (DVL_DAFNY_JOBS=1, DVL_VERUS_JOBS=1, set
# here whatever the environment says). A step killed by a signal (exit 137 or
# 143, e.g. the host's OOM killer) is reported as killed(memory), never as a
# verdict.
#
# Logs: one file per job, <log dir>/<job>.log (each step's command line, its
# output and its exit code), and summary.txt; build/ci/latest points at the
# newest default run. Output of the [A] steps goes to
# ~/.cache/dafny-verus-learn-0/ci/<run>/<job>.ref.log (covered by the fourth
# canonical deny rule) and only that location reaches the job log. Tool
# scratch (DVL_SCRATCH) lives in /tmp/dvl0-ci-<uid>/<run>/ (DVL_CI_WORK moves
# the /tmp/dvl0-ci-<uid> part; the [A] steps' scratch lies under the cache
# directory). After a run that passed, only the scratch paths that a retained
# report names are kept (a JSON document's raw_dir, a logged environment
# path; the summary says how many) and the rest is deleted; after a failed
# run all of it is kept. The console shows one
# PASS/FAIL/SKIP/ABSENT line per job and a summary. No job reports ABSENT
# today: the corpus job, its only user, fails instead since Δ109; the status
# and the summary's "absent" count stay for a job a later phase lists before
# it builds it.
#
# Not run here: tests/acceptance/guard_doors.py (it starts model sessions, and
# CI never calls a model: spec §12.1) and anything that needs a model or the
# network.
#
# Exit: 0 every selected job passed (SKIP and ABSENT jobs are reported, not
# failed) · 1 a job failed · 2 usage · 3 refused (--author outside the
# author's context).

# bash >= 4 (associative arrays below). macOS ships 3.2: re-exec under a newer
# bash when one is installed (Homebrew), else refuse (README §Platforms).
if [ -z "${BASH_VERSINFO:-}" ] || [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
  for _b in /opt/homebrew/bin/bash /usr/local/bin/bash; do
    if [ -x "$_b" ]; then exec "$_b" "$0" "$@"; fi
  done
  echo "ci.sh: refused: needs bash >= 4 (macOS: brew install bash)" >&2
  exit 3
fi

set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECKOUT="$(cd "$SCRIPTS/.." && pwd)"
ROOT="$CHECKOUT"

# The four canonical deny rules (spec §7.4; Δ80), literally: the same strings
# appear in scripts/course_mode.sh, CLAUDE.md and scripts/test_hooks.sh.
CANONICAL_DENY=(
  "Read(./Solutions/**)"
  "Read(./paper/solutions/**)"
  "Read(./tests/instructor/leak_patterns/**)"
  "Read(~/.cache/dafny-verus-learn-0/**)"
)
ALWAYS_ON=(
  "Read(~/.claude/projects/*/*.jsonl)"
  "Read(~/.claude/file-history/**)"
  "Read(~/.claude/history.jsonl)"
  "Skill(skill:local-assistant)"
)
REF_TREE=Solutions
COURSE_CACHE="$HOME/.cache/dafny-verus-learn-0"

JOB_ORDER=(static hook-test verify-q-dafny verify-q-verus verify-r-dafny verify-r-verus
           pins empty-body corpus wrappers coexist paper rubric harness brittleness)
QUICK_JOBS=(static hook-test)

describe() {
  case "$1" in
    static)         echo "study mode shipped; checker, its suite, unit generator, fixture drift, single route, sandbox classes, ledger-anchor gitignore, release history, hollow lint, specfreeze --check, chapter lint, avoid.sh; [A] reference_lint" ;;
    hook-test)      echo "scripts/test_hooks.sh (guard fixtures, course_mode.sh, banners, settings wiring)" ;;
    verify-q-dafny) echo "Q track, Dafny: toolchain sha; given layers gate and audit clean; armed files in their shipped state (vcheck --shipped), unit holes = shipped hole forms; [A] unit, exit, check and agent twins gate and audit" ;;
    verify-q-verus) echo "Q track, Verus: the same, plus vaudit --check-trust once per run" ;;
    verify-r-dafny) echo "R track, Dafny: as verify-q-dafny" ;;
    verify-r-verus) echo "R track, Verus: as verify-q-verus" ;;
    pins)           echo "golden pins: pins.py --ci (chapter fences included); [A] pins.py --ref" ;;
    empty-body)     echo "[A] firsttry.sh <ID> --empty-body for every armed module" ;;
    corpus)         echo "the cheat corpus: test_corpus.py --list (never empty) and --ci; an absent corpus fails" ;;
    wrappers)       echo "unittest discover -s tests/wrappers, then -s tests/ci" ;;
    coexist)        echo "both tracks' armed Dafny units resolve as one program; Verus crate names unique" ;;
    paper)          echo "make -C paper paper (empty-set rule); [A] make paper-solutions" ;;
    rubric)         echo "[A] update_rubric_pins.sh --check" ;;
    harness)        echo "uv lock --check, uv sync --frozen (offline); sterile: pytest tests/core, tests/harness_adapter, tests/sandbox, tests/bench, tripwire markers; learner Python holes (AST) and hollow lint; import tiers; [A] twins' reference gate and Python TRIV mode, the Q12 toolwright's reference tests" ;;
    brittleness)    echo "(--brittleness) vcheck --brittleness on given layers and armed units; [A] the units' twins (vcheck --ref --brittleness)" ;;
  esac
}

usage() { sed -n '/^# Usage:/,/^# Jobs, in run order/p' "$SCRIPTS/ci.sh" | sed '$d; s/^# \{0,1\}//'; }
usage_err() { echo "ci.sh: $*" >&2; echo "ci.sh: usage: scripts/ci.sh [--author] [--brittleness] [--quick | --job NAME ...] [--list] [--log-dir DIR]" >&2; exit 2; }
refuse() { echo "ci.sh: refused: $*" >&2; exit 3; }

# --- arguments ---------------------------------------------------------------------

AUTHOR=0
BRITTLE=0
QUICK=0
LIST=0
LOG_DIR=""
WANT=()
while [ $# -gt 0 ]; do
  case "$1" in
    --author) AUTHOR=1 ;;
    --brittleness) BRITTLE=1 ;;
    --quick) QUICK=1 ;;
    --list) LIST=1 ;;
    --job) [ $# -ge 2 ] || usage_err "--job needs a job name"; WANT+=("$2"); shift ;;
    --job=*) WANT+=("${1#--job=}") ;;
    --log-dir) [ $# -ge 2 ] || usage_err "--log-dir needs a directory"; LOG_DIR="$2"; shift ;;
    --log-dir=*) LOG_DIR="${1#--log-dir=}" ;;
    --root) [ $# -ge 2 ] || usage_err "--root needs a directory"
            ROOT="$(cd "$2" 2>/dev/null && pwd)" || usage_err "--root $2: no such directory"; shift ;;
    --root=*) ROOT="$(cd "${1#--root=}" 2>/dev/null && pwd)" || usage_err "$1: no such directory" ;;
    -h|--help) usage; exit 0 ;;
    -*) usage_err "unknown option '$1'" ;;
    *) WANT+=("$1") ;;
  esac
  shift
done

declare -A KNOWN=() SEL=()
for j in "${JOB_ORDER[@]}"; do KNOWN[$j]=1; done
if [ ${#WANT[@]} -gt 0 ]; then
  [ "$QUICK" = 0 ] || usage_err "--quick and named jobs are alternatives"
  for w in "${WANT[@]}"; do
    IFS=, read -r -a parts <<< "$w"
    for j in "${parts[@]}"; do
      [ -n "$j" ] || continue
      [ -n "${KNOWN[$j]:-}" ] || usage_err "unknown job '$j' (scripts/ci.sh --list names them)"
      SEL[$j]=1
    done
  done
  [ ${#SEL[@]} -gt 0 ] || usage_err "no job named"
elif [ "$QUICK" = 1 ]; then
  for j in "${QUICK_JOBS[@]}"; do SEL[$j]=1; done
else
  for j in "${JOB_ORDER[@]}"; do
    if [ "$j" != brittleness ]; then SEL[$j]=1; fi
  done
fi
if [ "$BRITTLE" = 1 ]; then SEL[brittleness]=1; fi
SELECTED=()
for j in "${JOB_ORDER[@]}"; do
  if [ -n "${SEL[$j]:-}" ]; then SELECTED+=("$j"); fi
done

if [ "$LIST" = 1 ]; then
  echo "ci.sh: jobs in run order ([A] = runs only with --author):"
  for j in "${SELECTED[@]}"; do printf '  %-15s %s\n' "$j" "$(describe "$j")"; done
  exit 0
fi

# --- the author gate (spec §7.4) ------------------------------------------------------

learner_prefix() {
  local f p=""
  for f in "$ROOT/scripts/course_mode.sh" "$SCRIPTS/course_mode.sh"; do
    if [ -f "$f" ]; then
      p="$(sed -n "s/^LEARNER_PREFIX=['\"]\{0,1\}\([A-Za-z0-9_.-]*\).*/\1/p" "$f")"
      [ -z "$p" ] || break
    fi
  done
  printf '%s' "${p:-leobwang-}"
}
PREFIX="$(learner_prefix)"
git_of() { git -C "$ROOT" "$@" 2>/dev/null; }
release_ref() {   # NAME — the local branch NAME, else origin/NAME; fails when neither exists
  local r
  for r in "refs/heads/$1" "refs/remotes/origin/$1"; do
    if git_of rev-parse --verify -q "$r^{commit}" > /dev/null; then printf '%s' "$r"; return 0; fi
  done
  return 1
}
BRANCH="$(git_of symbolic-ref --short -q HEAD || true)"
author_why() {   # empty when the three-condition test holds, else the reason
  local gd cd
  gd="$(git_of rev-parse --path-format=absolute --git-dir)" || { echo "not inside a git checkout"; return 0; }
  cd="$(git_of rev-parse --path-format=absolute --git-common-dir)" || { echo "not inside a git checkout"; return 0; }
  if [ "$gd" = "$cd" ]; then echo "this is the primary worktree"; return 0; fi
  case "$BRANCH" in "$PREFIX"*) echo "HEAD is on a learner branch ($BRANCH)" ;; esac
  return 0
}
if [ "$AUTHOR" = 1 ]; then
  case "$BRANCH" in
    "$PREFIX"*) refuse "--author never runs on a learner branch ($BRANCH): the reference steps belong to the course author's worktree (spec §7.4, §12.1)" ;;
  esac
  if [ "${CI:-}" != true ]; then
    WHY="$(author_why)"
    [ -z "$WHY" ] || refuse "--author runs only in the course author's linked worktree off a learner branch, or with CI=true ($WHY); a study run is scripts/ci.sh without --author"
  fi
else
  unset CI
fi

# --- the helper -------------------------------------------------

# The helper: the registry listing, the hole comparison, the study-mode check
# and the coexistence checks. It imports the course's own
# parsers (check_course_map, gen_units, firsttry, dvl), never a second one.
HELPER="$(cat <<'PY'
import json, os, re, subprocess, sys, tomllib
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(os.environ["DVLCI_ROOT"]).resolve()
SCRIPTS = Path(os.environ["DVLCI_SCRIPTS"]).resolve()
sys.path.insert(0, str(SCRIPTS))


def load(name, path):
    import importlib.machinery
    import importlib.util
    if name in sys.modules:
        return sys.modules[name]
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    loader.exec_module(mod)
    return mod


def rel(p):
    try:
        return Path(p).resolve().relative_to(ROOT).as_posix()
    except (ValueError, OSError, TypeError):
        return str(p)


def modules():
    """One TSV line per module: id, track, status, paper (1/0), Dafny units,
    Verus units (comma lists, '-' for none)."""
    import check_course_map as ccm
    import gen_units as gu
    data, err = ccm.load_registry(ROOT)
    if err:
        print(f"ci.sh: the module registry is unusable: {err}", file=sys.stderr)
        return 1
    mods = data.get("module")
    if not isinstance(mods, list) or not mods:
        print("ci.sh: MODULES.toml lists no [[module]] table (an empty set fails)", file=sys.stderr)
        return 1
    bad = 0
    for m in mods:
        errs = ccm.check_fields(m) if isinstance(m, dict) else ["a module entry is not a table"]
        if errs:
            bad += 1
            for e in errs:
                print(f"MODULES.toml: {e}", file=sys.stderr)
            continue
        units = {"d": [], "v": []}
        for u in m["units"]:
            units[gu.unit_kind(u.rstrip("/"))[0]].append(u.rstrip("/"))
        print("\t".join([m["id"], m["track"], m["status"], "1" if m["paper"] else "0",
                         ",".join(units["d"]) or "-", ",".join(units["v"]) or "-"]))
    return 1 if bad else 0


def files(mid, lang):
    """One line `role<TAB>path` per exit, check and agent file of the
    module in one language (vcheck's module_pin_files; the unit files are
    gated through their units)."""
    core = load("vcheck", SCRIPTS / "vcheck")
    try:
        rec = core.record(ROOT, mid)
    except core.Refusal as e:
        print(f"ci.sh: {e}", file=sys.stderr)
        return 1
    for rel, role, _ in core.module_pin_files(ROOT, rec, [lang]):
        if role != "exercise":
            print(f"{role}\t{rel}")
    return 0


def holes(mid, lang, jpath):
    """Tool-counted holes (the unit results of vcheck --shipped --json) = the
    hole forms the module's items ship (firsttry.static_holes), per (file,
    item); locations only. Also prints the shipped-state comparison's
    problems from the same JSON (learner files: locations and counts). A
    unit file the registry lists that is missing or unreadable fails the
    step by its path, in either language (no traceback)."""
    import check_course_map as ccm
    import gen_units as gu
    ft = load("firsttry", SCRIPTS / "firsttry.py")
    rec, code = ccm.find_record(ROOT, mid)
    if rec is None:
        return 1
    try:
        items, errs = ccm.module_items(ROOT, rec)
    except (OSError, UnicodeDecodeError) as e:
        print(f"{mid}: its items cannot be parsed: a module file is unreadable "
              f"({type(e).__name__}); no hole form counted")
        return 1
    for e in errs:
        print(e)
    if errs:
        return 1
    units = [u.rstrip("/") for u in rec["units"] if gu.unit_kind(u.rstrip("/"))[0] == lang]
    ext = ".dfy" if lang == "d" else ".rs"
    files = [p for p in rec["exercises"]
             if p.endswith(ext) and any(p.startswith(u + "/") for u in units)]
    want = Counter()
    unread = 0
    for f in files:
        try:
            text = (ROOT / f).read_text(encoding="utf-8")
        except FileNotFoundError:
            unread += 1
            print(f"{f}: the registry lists this unit file of {mid} and it does not exist "
                  "(an armed module ships every file; no hole form counted)")
            continue
        except (OSError, UnicodeDecodeError) as e:
            unread += 1
            print(f"{f}: unreadable ({type(e).__name__}; no hole form counted)")
            continue
        for it in items:
            if it["file"] == f and it["kind"] in "HXT":
                n = len(ft.static_holes(text, f, it))
                if n:
                    want[(f, it["id"])] += n
    try:
        data = json.loads(Path(jpath).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"{jpath}: no vcheck --json result ({type(e).__name__})")
        return 1
    if isinstance(data, dict) and "results" in data:      # vcheck --shipped --json
        for x in data.get("problems") or []:
            print(f"shipped: {x}")
        print(f"{mid} {lang}: {data.get('checked', 0)} file(s) checked against their "
              f"shipped-state pins; {len(data.get('problems') or [])} problem(s)")
        results = [r for r in data["results"] if r.get("unit")]
    else:
        results = data if isinstance(data, list) else [data]
    if not results:
        print(f"{mid}: vcheck returned no unit (an empty set fails)")
        return 1
    got = Counter()
    for r in results:
        for h in r.get("holes") or []:
            got[(rel(h.get("file")), h.get("label") or h.get("kind") or "?")] += 1
    bad = 0
    for key in sorted(set(want) | set(got)):
        if want[key] != got[key]:
            bad += 1
            print(f"{key[0]}: {key[1]}: the tool counts {got[key]} hole(s), the file ships "
                  f"{want[key]} hole form(s)")
    print(f"{mid} {lang}: {sum(got.values())} hole(s) counted by the tool in {len(results)} "
          f"unit(s); {sum(want.values())} hole form(s) shipped in {len(files)} exercise "
          f"file(s); {bad} mismatch(es)" + (f"; {unread} unit file(s) missing or unreadable"
                                             if unread else ""))
    return 1 if bad or unread else 0


def deny_problems(text, where, canon, always):
    try:
        deny = json.loads(text)["permissions"]["deny"]
        if not isinstance(deny, list):
            raise TypeError("deny is not a list")
    except (ValueError, KeyError, TypeError) as e:
        return [f"{where}: no readable permissions.deny ({type(e).__name__})"]
    out = [f"{where}: the canonical deny rule {r} is missing" for r in canon if r not in deny]
    out += [f"{where}: the always-on deny rule {r} is missing" for r in always if r not in deny]
    return out


def shipped():
    """Study mode is the shipping state (spec §7.4, §8.5)."""
    canon = os.environ["DVLCI_CANON"].split("\n")
    always = os.environ["DVLCI_ALWAYS"].split("\n")
    errs = []
    mode = ROOT / ".claude" / "state" / "mode"
    if mode.exists() or mode.is_symlink():
        try:
            says = mode.read_text(encoding="utf-8").strip()
        except OSError:
            says = ""
        errs.append(".claude/state/mode exists" + (" (it says authoring)" if says == "authoring"
                                                     else "") +
                    ": the repo ships in study mode; run scripts/course_mode.sh study")
    sp = ROOT / ".claude" / "settings.json"
    try:
        errs += deny_problems(sp.read_text(encoding="utf-8"), ".claude/settings.json", canon,
                              always)
    except OSError:
        errs.append(".claude/settings.json: missing")
    git = ["git", "-C", str(ROOT)]
    if subprocess.run(git + ["cat-file", "-e", "HEAD:.claude/settings.json"],
                      capture_output=True).returncode == 0:
        blob = subprocess.run(git + ["show", "HEAD:.claude/settings.json"], capture_output=True,
                              text=True)
        errs += deny_problems(blob.stdout, "HEAD:.claude/settings.json", canon, always)
        where = "the working tree and HEAD"
    else:
        where = "the working tree (.claude/settings.json is not committed at HEAD)"
    cm = ROOT / "scripts" / "course_mode.sh"
    if not cm.is_file():
        cm = SCRIPTS / "course_mode.sh"
    try:
        src = cm.read_text(encoding="utf-8")
    except OSError:
        src = ""
    for name, want in (("CANONICAL_DENY", canon), ("ALWAYS_ON", always)):
        m = re.search(rf"^{name}=\((.*?)\)\n", src, re.S | re.M)
        got = re.findall(r'"([^"]+)"', m.group(1)) if m else None
        if got != want:
            errs.append(f"{rel(cm)}: {name} differs from scripts/ci.sh's list (the four places "
                        "that name the canonical rules must agree, Δ80)")
    for e in errs:
        print(e)
    print(f"study mode shipped: {'no' if errs else 'yes'} ({len(errs)} problem(s); checked "
          f"{where}, {len(canon)} canonical and {len(always)} always-on rules)")
    return 1 if errs else 0


def coexist_dafny(units):
    """Every given unit's files (learner and given, never reference) as one
    program, resolved once through the pinned wrapper (dvl.dafny.holes runs
    `dafny resolve`, no solver)."""
    from dvl import common
    from dvl import dafny as D
    files, std = [], False
    for u in units:
        try:
            prog = D.program(str(ROOT / u))
        except D.Refused as e:
            print(f"{u}: refused by the wrapper ({e})")
            return 1
        for f in prog.files:
            if f not in files:
                files.append(f)
        std = std or prog.std
    work = common.scratch_dir("ci-coexist")
    lines = ["# scripts/ci.sh coexist: every armed Dafny unit of both tracks as one program",
             "includes = [" + ", ".join(json.dumps(str(f)) for f in files) + "]"]
    if std:
        lines += ["", "[options]", "standard-libraries = true"]
    (work / "dfyconfig.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        found = D.holes(str(work))
    except D.HoleCountError as e:
        for d in e.result.diagnostics:
            if d.severity == "error":
                print(f"{rel(d.file)}:{d.line}:{d.col}: error")
        print(f"coexist: the {len(units)} unit(s) ({len(files)} file(s)) do not resolve as one "
              f"program ({e.result.verdict}); raw output: {e.result.raw_dir}")
        return 1
    except D.Refused as e:
        print(f"coexist: refused by the wrapper ({e})")
        return 1
    print(f"coexist: {len(units)} Dafny unit(s), {len(files)} file(s), resolve as one program "
          f"({'with' if std else 'without'} the standard library; {len(found)} hole(s))")
    return 0


def coexist_verus(units):
    names = {}
    crates = [ROOT / u for u in units] + sorted(p.parent for p in
                                                (ROOT / "verus" / "given").glob("*/Cargo.toml"))
    for c in crates:
        try:
            with open(c / "Cargo.toml", "rb") as f:
                name = tomllib.load(f)["package"]["name"]
        except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError) as e:
            print(f"{rel(c / 'Cargo.toml')}: no readable [package] name ({type(e).__name__})")
            return 1
        names.setdefault(name.replace("-", "_"), []).append(rel(c))
    dups = {n: cs for n, cs in names.items() if len(cs) > 1}
    for n, cs in sorted(dups.items()):
        print(f"crate name {n} is used by {', '.join(cs)}")
    print(f"coexist: {len(crates)} Verus crate(s), {len(dups)} duplicate name(s)")
    return 1 if dups else 0


def prune(scratch, *reports):
    """After a passing run: remove the run's tool scratch except every existing path that
    a retained report (a log, a JSON document, the summary) names, with what lies under it
    (a named path the run never created keeps nothing). Prints each kept path, relative to
    the scratch root; a report that names the root itself keeps it whole."""
    import shutil
    base = Path(scratch)
    if not base.is_dir():
        return 0
    pat = re.compile(re.escape(str(base)) + r"(/[^\s\"'`,;:=()\[\]{}<>|\\]*)?")
    keep = set()
    for r in reports:
        for f in ([Path(r)] if Path(r).is_file() else sorted(Path(r).rglob("*"))):
            if not f.is_file() or f.is_relative_to(base):   # the scratch never names itself
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in pat.finditer(text):
                q = base / (m.group(1) or "").strip("/").rstrip(".")
                if q.exists() or q.is_symlink():
                    keep.add(q)
    if base in keep:
        print(".")
        return 0

    def sweep(d):
        for e in sorted(d.iterdir()):
            if e in keep:
                continue
            if e.is_dir() and not e.is_symlink() and any(k.is_relative_to(e) for k in keep):
                sweep(e)
            elif e.is_dir() and not e.is_symlink():
                shutil.rmtree(e, ignore_errors=True)
            else:
                e.unlink(missing_ok=True)
    sweep(base)
    for k in sorted(keep):
        print(k.relative_to(base))
    return 0


cmd, args = sys.argv[1], sys.argv[2:]
sys.exit({"modules": lambda: modules(),
          "prune": lambda: prune(*args),
          "files": lambda: files(*args),
          "holes": lambda: holes(*args),
          "shipped": lambda: shipped(),
          "coexist-dafny": lambda: coexist_dafny(args),
          "coexist-verus": lambda: coexist_verus(args)}[cmd]())
PY
)"
DVLCI_CANON="$(printf '%s\n' "${CANONICAL_DENY[@]}")"
DVLCI_ALWAYS="$(printf '%s\n' "${ALWAYS_ON[@]}")"
export DVLCI_CANON DVLCI_ALWAYS
py() {
  DVLCI_ROOT="$ROOT" DVLCI_SCRIPTS="$SCRIPTS" python3 -B -c "$HELPER" "$@"
}


# --- run directories and the registry ------------------------------------------------

export DVL_DAFNY_JOBS=1 DVL_VERUS_JOBS=1 PYTHONDONTWRITEBYTECODE=1
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
if [ -n "$LOG_DIR" ]; then
  mkdir -p "$LOG_DIR"
  RUNDIR="$(cd "$LOG_DIR" && pwd)"
else
  RUNDIR="$ROOT/build/ci/$RUN_ID"
  mkdir -p "$RUNDIR"
  ln -sfn "$RUN_ID" "$ROOT/build/ci/latest"
fi
WORK_BASE="${DVL_CI_WORK:-/tmp/dvl0-ci-$(id -u)}"
WORK="$WORK_BASE/$RUN_ID"
mkdir -p -m 700 "$WORK_BASE"
mkdir -p -m 700 "$WORK" "$WORK/scratch" "$WORK/tmp"
REFDIR="$COURSE_CACHE/ci/$RUN_ID"
if [ "$AUTHOR" = 1 ]; then mkdir -p -m 700 "$REFDIR" "$REFDIR/scratch"; fi
export DVL_SCRATCH="$WORK/scratch" DVL_TEST_TMP="$WORK/tmp"

show() {   # a path as the console shows it: relative to the root, ~/…, or absolute
  case "$1" in
    "$ROOT"/*) printf '%s' "${1#"$ROOT"/}" ;;
    "$HOME"/*) printf '~/%s' "${1#"$HOME"/}" ;;
    *) printf '%s' "$1" ;;
  esac
}

if MODLIST="$(py modules 2> "$RUNDIR/registry.log")"; then MODLIST_RC=0; else MODLIST_RC=$?; fi
declare -A M_TRACK=() M_STATUS=() M_PAPER=() M_DUNITS=() M_VUNITS=()
M_IDS=()
if [ "$MODLIST_RC" = 0 ]; then
  while IFS=$'\t' read -r id tr st pa du vu; do
    [ -n "$id" ] || continue
    M_IDS+=("$id"); M_TRACK[$id]="$tr"; M_STATUS[$id]="$st"; M_PAPER[$id]="$pa"
    M_DUNITS[$id]="$du"; M_VUNITS[$id]="$vu"
  done <<< "$MODLIST"
fi

# --- the step machinery (runs inside a job's subshell) -------------------------------

log() { printf '%s\n' "$*" >> "$JOBLOG"; }
loud() { J_NOTES+=("$*"); log "LOUD: $*"; }
fail_note() { J_FAILED+=("$1"); log "FAIL: $1${2:+ — $2}"; }
absent() { J_ABSENT="$*"; log "ABSENT: $*"; }
qcmd() { local a out=""; for a in "$@"; do out+="$(printf '%q' "$a") "; done; printf '%s' "${out% }"; }
in_dir() { local d="$1"; shift; cd "$d" && "$@"; }

_run() {   # OUT ERR LABEL CMD... — run CMD; STEP_RC holds its exit code
  local out="$1" err="$2" label="$3" t0=$SECONDS
  shift 3
  if ( "$@" ) >> "$out" 2>> "$err" < /dev/null; then STEP_RC=0; else STEP_RC=$?; fi
  J_RUN=$((J_RUN + 1))
  case "$STEP_RC" in
    0) ;;
    137|143) J_FAILED+=("$label: killed(memory), exit $STEP_RC, never a verdict") ;;
    *) J_FAILED+=("$label (exit $STEP_RC)") ;;
  esac
  printf '[%s] exit %s (%ss)%s\n' "$label" "$STEP_RC" $((SECONDS - t0)) \
    "$(case "$STEP_RC" in 137|143) echo ' killed(memory): never a verdict' ;; esac)" >> "$JOBLOG"
  return 0
}
step() {      # LABEL CMD... — output into the job log
  local label="$1"; shift
  printf '\n$ %s\n' "$(qcmd "$@")" >> "$JOBLOG"
  _run "$JOBLOG" "$JOBLOG" "$label" "$@"
}
step_to() {   # LABEL FILE CMD... — stdout into FILE, stderr into the job log
  local label="$1" file="$2"; shift 2
  printf '\n$ %s > %s\n' "$(qcmd "$@")" "$file" >> "$JOBLOG"
  : > "$file"
  _run "$file" "$JOBLOG" "$label" "$@"
}
astep() {     # LABEL CMD... — an author-only step: output into the reference log
  local label="$1"; shift
  if [ "$AUTHOR" != 1 ]; then
    J_SKIP=$((J_SKIP + 1)); STEP_RC=0
    log "skipped (author-only, runs with --author): $label"
    return 0
  fi
  printf '\n$ %s\n' "$(qcmd "$@")" >> "$REFLOG"
  log "\$ $(qcmd "$@")   (output: $(show "$REFLOG"))"
  _run "$REFLOG" "$REFLOG" "$label" env DVL_SCRATCH="$REFDIR/scratch" "$@"
}
registry_ok() {
  if [ "$MODLIST_RC" != 0 ]; then
    fail_note "registry" "the module listing failed (exit $MODLIST_RC); see $(show "$RUNDIR/registry.log")"
    return 1
  fi
}
armed() {     # [TRACK] — the non-planned module ids, in registry order
  local id
  for id in "${M_IDS[@]}"; do
    if [ "${M_STATUS[$id]}" != planned ] && { [ -z "${1:-}" ] || [ "${M_TRACK[$id]}" = "$1" ]; }; then
      echo "$id"
    fi
  done
}
track_total() {
  local id n=0
  for id in "${M_IDS[@]}"; do
    if [ "${M_TRACK[$id]}" = "$1" ]; then n=$((n + 1)); fi
  done
  echo "$n"
}
units_of() {  # ID d|v — the module's units of one language, one per line
  local u="${M_DUNITS[$1]}"
  [ "$2" = d ] || u="${M_VUNITS[$1]}"
  [ "$u" = - ] || tr ',' '\n' <<< "$u"
}
given_targets() {   # TRACK d|v — the given layers that exist, root-relative
  local f pre=qg
  [ "$1" = Q ] || pre=rg
  if [ "$2" = d ]; then
    for f in "$ROOT/dafny/given/$1"/*.dfy; do
      if [ -f "$f" ]; then echo "${f#"$ROOT"/}"; fi
    done
  else
    for f in "$ROOT/verus/given/${pre}"_*/Cargo.toml; do
      if [ -f "$f" ]; then f="${f%/Cargo.toml}"; echo "${f#"$ROOT"/}"; fi
    done
  fi
}
lines() { [ -z "$1" ] && echo 0 || grep -c '' <<< "$1"; }
twin_missing() {    # PATH — a twin that does not exist, or a twin unit or crate directory
  local t="$1"      # with no source file of its own (only a project mirror, Δ110)
  if [ -d "$t" ]; then
    ! compgen -G "$t/*.dfy" > /dev/null && [ -z "$(find "$t/src" -name '*.rs' -print -quit 2>/dev/null)" ]
  else
    [ ! -e "$t" ]
  fi
}

VCHECK=(python3 -B "$SCRIPTS/vcheck" --root "$ROOT")
VAUDIT=(python3 -B "$SCRIPTS/vaudit" --root "$ROOT")

# --- the jobs ---------------------------------------------------------------------

job_static() {
  local ids id
  step "study mode shipped" py shipped
  step "check_course_map (all groups)" python3 -B "$SCRIPTS/check_course_map.py" --root "$ROOT"
  step "test_course_map" python3 -B "$SCRIPTS/test_course_map.py"
  step "gen_units --check" python3 -B "$SCRIPTS/gen_units.py" --check --root "$ROOT"
  step "gen_hook_fixtures --check" python3 -B "$SCRIPTS/gen_hook_fixtures.py" --check
  # DV4-PLAN §8-§9: only the entry points start containers, agents or sudo; the
  # sandbox's refused source classes cover every reference path of the guard
  # (this checkout's hook) and the checker; the ledger anchors, ledgers and
  # run records stay tracked (§4.2, §14 Q12).
  step "single route (check_single_route.py)" python3 -B "$SCRIPTS/check_single_route.py" --root "$ROOT"
  step "sandbox source classes agree with the guard and the checker" python3 -B -c \
    'import sys; sys.path.insert(0, sys.argv[1]); from dvl import sandbox; p = sandbox.class_drift(sys.argv[2]); print("\n".join(p) or "the sandbox refuses every reference path of the guard and the checker"); sys.exit(1 if p else 0)' \
    "$SCRIPTS" "$CHECKOUT"
  if git_of rev-parse --is-inside-work-tree >/dev/null; then
    for f in research/ledger-heads.jsonl research/runs/Q07/ledger.jsonl research/runs/Q07/r1/run.json; do
      if git -C "$ROOT" check-ignore -q --no-index "$f" 2>/dev/null; then
        fail_note ".gitignore matches $f" "the ledger anchors, ledgers and run records stay tracked (DV4-PLAN §4.2)"
      fi
    done
    log "ledger anchors: .gitignore leaves research/ledger-heads.jsonl, ledgers and run.json tracked"
    # D42 and D46: the shipped branch is a linear chain of single-parent "basic: "
    # commits atop design-only main, with no archived (archive/*) ancestry.
    local rel_base rel_cand
    if rel_base="$(release_ref main)" && rel_cand="$(release_ref basic)"; then
      step "release history (check_release_history.py)" python3 -B "$SCRIPTS/check_release_history.py" \
        --root "$ROOT" --base "$rel_base" "$rel_cand"
    else
      loud "no basic or no main branch in this checkout: the release-history check did not run"
    fi
  else
    loud "not a git checkout: the ledger-anchor .gitignore and release-history checks did not run"
  fi
  step "firsttry --lint-hollow --all" bash "$SCRIPTS/firsttry.sh" --lint-hollow --all --root "$ROOT"
  if registry_ok; then
    ids="$(armed)"
    if [ -z "$ids" ]; then
      loud "specfreeze: no armed module, nothing to compare ($(lines "$MODLIST") modules, all planned)"
    else
      for id in $ids; do
        step "specfreeze --check $id" python3 -B "$SCRIPTS/specfreeze" --check "$id" --root "$ROOT"
      done
    fi
    if [ -z "$ids" ]; then
      loud "chapter_lint: no armed module, no chapter to lint ($(lines "$MODLIST") modules, all planned)"
    else
      step "chapter_lint --all" python3 -B "$SCRIPTS/chapter_lint.py" --all --root "$ROOT"
    fi
  fi
  # The disjointness gate between the tracks (spec §2.7, design §9, PLAN.md §5.5;
  # DVR0): learner-visible files only, its inputs from this checkout's scripts/.
  step "avoid.sh" bash "$SCRIPTS/avoid.sh" --root "$ROOT"
  astep "reference_lint" python3 -B "$SCRIPTS/reference_lint.py" --root "$ROOT"
}

job_hook_test() {
  step "test_hooks.sh" bash "$SCRIPTS/test_hooks.sh"
}

TRUST_DONE="$RUNDIR/.check-trust.done"
job_verify() {   # TRACK d|v
  local track="$1" lang="$2" tool=dafny name=Dafny total ids id given t u twin json gv
  if [ "$lang" = v ]; then tool=verus; name=Verus; fi
  step "toolchain versions (dafny, verus on PATH)" "${VCHECK[@]}" --versions
  registry_ok || return 0
  total="$(track_total "$track")"
  if [ "$total" -eq 0 ]; then
    fail_note "registry" "MODULES.toml lists no $track module (an empty set fails)"
    return 0
  fi
  ids=""
  for id in $(armed "$track"); do
    if [ -n "$(units_of "$id" "$lang")" ]; then ids+="$id "; fi
  done
  given="$(given_targets "$track" "$lang")"
  if [ "$lang" = v ] && [ ! -e "$TRUST_DONE" ]; then
    : > "$TRUST_DONE"
    step "vaudit --check-trust" "${VAUDIT[@]}" --check-trust
  fi
  if [ -z "$ids" ] && [ -z "$given" ]; then
    loud "no armed $track module with $name units and no $track given layer: nothing to verify ($total $track modules, all planned or without $name units)"
    return 0
  fi
  for t in $given; do
    step "gate $t" "${VCHECK[@]}" --gate "$ROOT/$t"
    step "audit $t" "${VAUDIT[@]}" "$ROOT/$t"
  done
  [ -n "$given" ] || loud "no $track $name given layer yet"
  if [ -z "$ids" ]; then
    loud "no armed $track module with $name units ($total $track modules)"
    return 0
  fi
  mkdir -p "$RUNDIR/$JOB"
  for id in $ids; do
    json="$RUNDIR/$JOB/$id.$lang.json"
    # every file of the language in the learner loop against its shipped-state
    # pin (exit 1 on a difference); its JSON feeds the per-item hole comparison
    step_to "shipped $id $lang" "$json" "${VCHECK[@]}" --shipped --json "$id" "$lang"
    if grep -q '"results"' "$json" 2>/dev/null; then
      step "holes $id $lang" py holes "$id" "$lang" "$json"
    else
      log "holes $id $lang: not compared (vcheck --shipped printed no result)"
    fi
    for u in $(units_of "$id" "$lang"); do
      twin="$ROOT/$REF_TREE/$u"
      if [ "$AUTHOR" = 1 ] && twin_missing "$twin"; then
        fail_note "twin of $u" "$REF_TREE/$u does not exist or holds no source file (every unit has a reference twin)"
        continue
      fi
      astep "reference gate $u" "${VCHECK[@]}" --ref "$twin"
      astep "reference audit $u" "${VAUDIT[@]}" --ref "$twin"
    done
    if ! others="$(py files "$id" "$lang" 2>> "$JOBLOG")"; then
      fail_note "files $id $lang" "the module's exit, check and agent files could not be listed"
      continue
    fi
    while IFS=$'\t' read -r role f; do
      [ -n "${f:-}" ] || continue
      twin="$ROOT/$REF_TREE/$f"
      if [ "$AUTHOR" = 1 ] && twin_missing "$twin"; then
        fail_note "twin of $f" "$REF_TREE/$f does not exist (every $role file has a reference twin)"
        continue
      fi
      astep "reference gate $f" "${VCHECK[@]}" --ref "$twin"
      astep "reference audit $f" "${VAUDIT[@]}" --ref "$twin"
    done <<< "$others"
  done
}
job_verify_q_dafny() { job_verify Q d; }
job_verify_q_verus() { job_verify Q v; }
job_verify_r_dafny() { job_verify R d; }
job_verify_r_verus() { job_verify R v; }

job_pins() {
  registry_ok || return 0
  if [ -z "$(armed)" ]; then
    loud "no armed module: pins.py passes loudly ($(lines "$MODLIST") modules, all planned)"
  fi
  step "pins.py --ci" python3 -B "$SCRIPTS/pins.py" --ci --root "$ROOT"
  astep "pins.py --ref" python3 -B "$SCRIPTS/pins.py" --ref --root "$ROOT"
}

job_empty_body() {
  local ids id
  if [ "$AUTHOR" != 1 ]; then
    astep "firsttry --empty-body (every armed module)" true
    return 0
  fi
  registry_ok || return 0
  ids="$(armed)"
  if [ -z "$ids" ]; then
    loud "no armed module: no hole to empty ($(lines "$MODLIST") modules, all planned)"
    return 0
  fi
  for id in $ids; do
    astep "empty-body $id" bash "$SCRIPTS/firsttry.sh" "$id" --empty-body --root "$ROOT"
  done
}

job_corpus() {   # an absent corpus fails (Δ108, Δ109); nothing here before --ci starts a solver
  local list="$RUNDIR/corpus.list"
  if [ ! -f "$SCRIPTS/test_corpus.py" ]; then
    fail_note "scripts/test_corpus.py does not exist" "an absent corpus fails (Δ108, Δ109)"
    return 0
  fi
  if [ ! -d "$CHECKOUT/tests/corpus" ]; then
    fail_note "tests/corpus/ does not exist" "an absent corpus fails (Δ108, Δ109)"
    return 0
  fi
  step_to "test_corpus --list" "$list" in_dir "$CHECKOUT" python3 -B "$SCRIPTS/test_corpus.py" --list
  [ "$STEP_RC" = 0 ] || return 0      # the runner failed the listing: a missing, empty or broken corpus
  if ! grep -q '[^[:space:]]' "$list"; then
    fail_note "test_corpus --list lists no fixture" "the listing is empty, and an empty set fails"
    return 0
  fi
  log "test_corpus --list: $(grep -c '[^[:space:]]' "$list") fixture(s) listed in $(show "$list")"
  # The canonical layout is tests/corpus/<lang>/<ID>/ (Δ109). The runner still
  # accepts Δ106's <ID>_<slug>/, which lets two directories carry one id; the
  # listing's last column is the directory, its first two the id and the lang.
  local bad
  bad="$(awk '{ n = split($NF, p, "/")
                if (n != 4 || p[1] != "tests" || p[2] != "corpus" || p[3] != $2 || p[4] != $1)
                  printf "%s%s (id %s)", (k++ ? "; " : ""), $NF, $1 }' "$list")"
  if [ -n "$bad" ]; then
    fail_note "corpus layout" "a fixture directory is not tests/corpus/<lang>/<ID>/: $bad"
    return 0
  fi
  step "test_corpus --ci" in_dir "$CHECKOUT" python3 -B "$SCRIPTS/test_corpus.py" --ci
}

job_wrappers() {
  step "unittest tests/wrappers" in_dir "$CHECKOUT" python3 -B -m unittest discover -s tests/wrappers
  if [ -d "$CHECKOUT/tests/ci" ]; then
    step "unittest tests/ci" in_dir "$CHECKOUT" python3 -B -m unittest discover -s tests/ci
  else
    fail_note "unittest tests/ci" "tests/ci/ (this script's own tests) does not exist"
  fi
}

job_coexist() {
  local id u dunits=() vunits=()
  registry_ok || return 0
  for id in $(armed); do
    for u in $(units_of "$id" d); do dunits+=("$u"); done
    for u in $(units_of "$id" v); do vunits+=("$u"); done
  done
  if [ ${#dunits[@]} -eq 0 ]; then
    loud "no armed Dafny unit: nothing to resolve together"
  else
    step "dafny: both tracks resolve as one program" py coexist-dafny "${dunits[@]}"
  fi
  if [ ${#vunits[@]} -eq 0 ] && [ -z "$(given_targets Q v; given_targets R v)" ]; then
    loud "no Verus crate: no name to compare"
  else
    step "verus: crate names unique" py coexist-verus "${vunits[@]}"
  fi
  log "the Python half (fvh, fvh_q and fvh_r imported in one process) is the harness job's (harness/tests/core/test_layout.py)"
}

job_paper() {
  local id f ids="" have=0 sol=0
  registry_ok || return 0
  for id in $(armed); do
    if [ "${M_PAPER[$id]}" = 1 ]; then ids+="$id "; fi
  done
  for id in $ids; do
    for f in problems answers; do
      if [ ! -f "$ROOT/paper/${id}_$f.tex" ]; then
        fail_note "paper/${id}_$f.tex missing" "$id is armed with paper = true (MODULES.toml), so its pair must exist"
      fi
    done
  done
  for f in "$ROOT"/paper/[RQ][0-9][0-9]_problems.tex "$ROOT"/paper/[RQ][0-9][0-9]_answers.tex; do
    if [ -f "$f" ]; then have=1; fi
  done
  if [ -z "$ids" ] && [ "$have" = 0 ]; then
    loud "no written-track pair and no armed module with paper = true: nothing to build"
  else
    step "make paper" make -C "$ROOT/paper" paper
  fi
  if [ "$AUTHOR" = 1 ]; then
    for f in "$ROOT/paper/solutions"/*.tex; do
      if [ -f "$f" ]; then sol=1; fi
    done
    if [ "$sol" = 0 ] && [ -z "$ids" ]; then
      loud "no reference solution file and no armed module with paper = true: nothing to build for paper-solutions"
      return 0
    fi
  fi
  astep "make paper-solutions" make -C "$ROOT/paper" paper-solutions
}

job_rubric() {
  if [ "$AUTHOR" = 1 ] && registry_ok && [ -z "$(armed)" ]; then
    loud "no armed module: update_rubric_pins.sh checks only the rubric files present"
  fi
  astep "update_rubric_pins --check" bash "$SCRIPTS/update_rubric_pins.sh" --check --root "$ROOT"
}

job_harness() {   # QPLAN §11.8: the fvh core, the learner Python files, the Python adapter
  # uv runs offline on the pinned lock, with its project environment in this run's
  # scratch (never harness/.venv) and no user uv configuration; PYTHONDONTWRITEBYTECODE=1
  # (exported above) and -p no:cacheprovider keep harness/ free of bytecode and caches.
  # No solver runs here. Model backends, ruff and the sandbox self-test join this job
  # with the rest of the core (Q07-Q12).
  local h="$ROOT/harness" adapter="$SCRIPTS/dvl/python.py" armed="" files="" ids="" id f uvb
  local -a uvenv=() abs=()
  if [ "$MODLIST_RC" = 0 ]; then
    if ! armed="$(python3 -B "$adapter" files --armed --root "$ROOT" 2>> "$JOBLOG")"; then
      fail_note "harness files" "the armed modules' harness files could not be listed (see the log)"
      return 0
    fi
  fi
  if [ ! -f "$h/pyproject.toml" ]; then
    if [ -n "$armed" ]; then
      fail_note "harness/pyproject.toml missing" "armed modules list harness files: $(tr '\n' ' ' <<< "$armed")"
    else
      loud "no harness/ project and no armed module lists a harness file: nothing to test"
    fi
    return 0
  fi
  for f in $armed; do
    if [ ! -f "$ROOT/$f" ]; then fail_note "$f missing" "an armed module lists it in harness"; fi
  done
  uvb="$(command -v uv || true)"
  if [ -z "$uvb" ] && [ -x "$HOME/.local/bin/uv" ]; then uvb="$HOME/.local/bin/uv"; fi
  if [ -z "$uvb" ]; then
    fail_note "uv" "uv is not installed (the pinned host tool, VERSIONS.md §1.4)"
    return 0
  fi
  uvenv=(env UV_PROJECT_ENVIRONMENT="$WORK/py-env" XDG_CONFIG_HOME="$WORK/py-config"
         UV_NO_PROGRESS=1 NO_COLOR=1)
  step "uv lock --check" "${uvenv[@]}" "$uvb" lock --check --offline --directory "$h"
  step "uv sync --frozen" "${uvenv[@]}" "$uvb" sync --frozen --offline --directory "$h"
  if [ "$STEP_RC" != 0 ]; then
    log "uv sync failed: nothing that needs the environment ran (fill uv's cache once, online: uv sync --directory harness)"
    return 0
  fi
  # The sterile environment (DV4-PLAN §9): CI never calls a model, never starts a
  # container and never connects outside its own fakes. uv's cache path is
  # resolved with the real HOME first; then every harness test runs with HOME,
  # the XDG directories and CLAUDE_CONFIG_DIR in empty scratch directories (so the
  # pinned binaries, which fvh resolves relative to HOME, and every credentials
  # file are absent), FVH_APPARATUS at the backend tests' fake apparatus file,
  # FVH_NO_MODEL=1 and DVL_NO_DOCKER=1, and tripwire shims for claude, opencode,
  # ollama, docker and sudo first on PATH: a shim leaves a marker and fails, and
  # any marker fails the job. The socket tripwire is harness/tests/conftest.py.
  local uvcache sterile marks shim apparatus
  local -a sterile_env=()
  uvcache="$("$uvb" cache dir 2>/dev/null || true)"
  sterile="$WORK/sterile"
  marks="$WORK/tripwire-marks"
  mkdir -p "$sterile"/{home,config,cache,data,state,claude,bin} "$marks"
  mkdir -p -m 700 "$sterile/runtime"
  for shim in claude opencode ollama docker sudo; do
    printf '#!/bin/sh\n: > "%s/%s.$$"\necho "ci.sh tripwire: %s is not available to a harness test (CI never calls a model, starts a container or escalates)" >&2\nexit 97\n' \
      "$marks" "$shim" "$shim" > "$sterile/bin/$shim"
    chmod 755 "$sterile/bin/$shim"
  done
  apparatus="$ROOT/harness/tests/core/fakes/apparatus.toml"
  if [ ! -f "$apparatus" ]; then
    apparatus="$sterile/no-apparatus.toml"
    log "no harness/tests/core/fakes/apparatus.toml yet: FVH_APPARATUS names a missing file, so a backend fails closed"
  fi
  sterile_env=(env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT -u CLAUDE_CODE_SESSION_ID
               -u CLAUDE_CODE_OAUTH_TOKEN -u ANTHROPIC_API_KEY -u ANTHROPIC_BASE_URL
               -u OLLAMA_HOST -u DOCKER_HOST
               HOME="$sterile/home" XDG_CONFIG_HOME="$sterile/config" XDG_CACHE_HOME="$sterile/cache"
               XDG_DATA_HOME="$sterile/data" XDG_STATE_HOME="$sterile/state"
               XDG_RUNTIME_DIR="$sterile/runtime" CLAUDE_CONFIG_DIR="$sterile/claude"
               FVH_APPARATUS="$apparatus" FVH_NO_MODEL=1 DVL_NO_DOCKER=1
               PATH="$sterile/bin:$PATH" ${uvcache:+UV_CACHE_DIR="$uvcache"})
  log "sterile environment: HOME=$sterile/home, shims in $sterile/bin, FVH_APPARATUS=$apparatus, UV_CACHE_DIR=${uvcache:-unset}"
  step "pytest tests/core (sterile, network tripwire)" "${sterile_env[@]}" "${uvenv[@]}" "$uvb" run \
    --frozen --offline --directory "$h" pytest tests/core -q -p no:cacheprovider
  step "adapter suite (tests/harness_adapter)" in_dir "$CHECKOUT" "${sterile_env[@]}" python3 -B -m unittest discover -s tests/harness_adapter
  step "sandbox suite (tests/sandbox, no Docker)" in_dir "$CHECKOUT" "${sterile_env[@]}" python3 -B -m unittest discover -s tests/sandbox
  step "benchmark suite (tests/bench, a local upstream)" in_dir "$CHECKOUT" "${sterile_env[@]}" python3 -B -m unittest discover -s tests/bench
  if [ -n "$(ls -A "$marks" 2>/dev/null)" ]; then
    fail_note "tripwire: a harness test ran $(ls "$marks" | sed 's/\..*//' | sort -u | paste -sd, -)" \
      "a shim left a marker in $marks: CI never calls a model, starts a container or escalates"
  fi
  if ! files="$(python3 -B "$adapter" files --root "$ROOT" 2>> "$JOBLOG")"; then
    fail_note "learner Python files" "could not be listed (see the log)"
    return 0
  fi
  for f in $files; do abs+=("$ROOT/$f"); done
  if [ ${#abs[@]} -eq 0 ]; then
    loud "no learner Python file yet: no hole to count"
  else
    step "learner Python holes (AST)" python3 -B "$adapter" holes --root "$ROOT" "${abs[@]}"
    step "hollow learner Python" python3 -B "$adapter" hollow --root "$ROOT" "${abs[@]}"
  fi
  step "import tiers" python3 -B "$SCRIPTS/check_course_map.py" --root "$ROOT" --only import-tiers
  # the shipped state of each armed module's Python files (vcheck --shipped <ID> py),
  # once expected/<ID>.counts pins them (role harness; vcheck --ref --pin-counts <ID>)
  if [ -n "$armed" ]; then
    if ! ids="$(python3 -B "$adapter" files --armed --ids --root "$ROOT" 2>> "$JOBLOG")"; then
      fail_note "harness modules" "the armed modules with harness files could not be listed"
      ids=""
    fi
    for id in $ids; do
      if grep -q '^role = "harness"$' "$ROOT/expected/$id.counts" 2>/dev/null; then
        step "shipped $id py" "${VCHECK[@]}" --shipped "$id" py
      else
        loud "expected/$id.counts pins no Python file yet: $id's harness files were not compared with a shipped state"
      fi
    done
  fi
  for f in $files; do
    if [ "$AUTHOR" = 1 ] && [ ! -f "$ROOT/$REF_TREE/$f" ]; then
      fail_note "twin of $f" "$REF_TREE/$f does not exist (every learner Python file has a reference twin)"
      continue
    fi
    astep "reference gate $f" python3 -B "$adapter" ref --root "$ROOT" "$ROOT/$REF_TREE/$f"
    astep "Python TRIV mode $f" python3 -B "$adapter" triv --root "$ROOT" "$ROOT/$REF_TREE/$f"
  done
  # [A] the agentic tools' reference twins that need no solver (DV6 fix round: the Q12
  # toolwright's twin proves its contract satisfiable over the recorded documents)
  if [ "$AUTHOR" = 1 ] && [ -f "$ROOT/$REF_TREE/tools/Q12/test_holecount.py" ]; then
    astep "reference toolwright (tools/Q12)" python3 -B "$ROOT/$REF_TREE/tools/Q12/test_holecount.py"
  fi
}

job_brittleness() {
  local t track lang id targets=() mods=()
  registry_ok || return 0
  for track in Q R; do
    for lang in d v; do
      for t in $(given_targets "$track" "$lang"); do targets+=("$t"); done
    done
  done
  for id in $(armed); do
    for lang in d v; do
      if [ -n "$(units_of "$id" "$lang")" ]; then mods+=("$id $lang"); fi
    done
  done
  if [ ${#targets[@]} -eq 0 ] && [ ${#mods[@]} -eq 0 ]; then
    loud "no given layer and no armed unit: nothing to re-verify under the seeds"
    return 0
  fi
  for t in "${targets[@]}"; do
    step "brittleness $t" "${VCHECK[@]}" --brittleness "$ROOT/$t"
  done
  for t in "${mods[@]}"; do
    # shellcheck disable=SC2086  # "<ID> <lang>" splits into two words on purpose
    step "brittleness $t" "${VCHECK[@]}" --brittleness $t
  done
  # [A] each armed unit's reference twin under the same seeds (vcheck --ref
  # --brittleness, QPLAN §6 Q29; Dafny over both bundled solvers)
  local u lg sv
  for t in "${mods[@]}"; do
    id="${t% *}"; lg="${t#* }"; sv=()
    [ "$lg" = d ] && sv=(--solvers)
    for u in $(units_of "$id" "$lg"); do
      astep "reference brittleness $u" "${VCHECK[@]}" --ref --brittleness "${sv[@]}" "$ROOT/$REF_TREE/$u"
    done
  done
}

# --- the runner -------------------------------------------------------------------

job_body() {   # runs in the job's subshell; writes the job's status file
  set -o errtrace
  trap 'printf "ci.sh: internal error in job %s (line %s)\n" "$JOB" "$LINENO" >> "$JOBLOG"' ERR
  J_RUN=0; J_SKIP=0; J_FAILED=(); J_NOTES=(); J_ABSENT=""; J_MEM_OK=""
  "job_${JOB//-/_}"
  local st why="" x
  if [ ${#J_FAILED[@]} -gt 0 ]; then
    st=FAIL
    for x in "${J_FAILED[@]}"; do why+="${why:+; }$x"; done
  elif [ -n "$J_ABSENT" ]; then
    st=ABSENT; why="$J_ABSENT"
  elif [ "$J_RUN" -eq 0 ] && [ ${#J_NOTES[@]} -eq 0 ] && [ "$J_SKIP" -gt 0 ]; then
    st=SKIP; why="author-only: runs with scripts/ci.sh --author in the authoring worktree"
  else
    st=PASS
    for x in "${J_NOTES[@]}"; do why+="${why:+; }$x"; done
    if [ "$J_SKIP" -gt 0 ]; then why+="${why:+; }$J_SKIP author-only step(s) skipped"; fi
  fi
  printf '%s\t%s\n' "$st" "$why" > "$STATUSF"
}

trap 'echo "ci.sh: interrupted" >&2; exit 130' INT TERM

HEAD_DESC="not a git checkout"
if SHA="$(git_of rev-parse --short HEAD)"; then
  if DIRTY="$(git_of --no-optional-locks status --porcelain)"; then
    HEAD_DESC="${BRANCH:-detached HEAD} @ $SHA, $( [ -z "$DIRTY" ] && echo "clean tree" || echo "$(lines "$DIRTY") uncommitted change(s)")"
  else
    HEAD_DESC="${BRANCH:-detached HEAD} @ $SHA"
  fi
fi
KIND="study run"
[ "$AUTHOR" = 0 ] || KIND="author run"
{
  echo "ci.sh: $KIND of $ROOT ($HEAD_DESC)"
  [ "$ROOT" = "$CHECKOUT" ] || echo "ci.sh: course root $ROOT, scripts of $CHECKOUT (hook-test, wrappers, corpus and the suites test this checkout)"
  echo "ci.sh: jobs: ${SELECTED[*]}"
  echo "ci.sh: solver jobs one at a time (no course memory cap: the host's, Δ503 D78); logs: $(show "$RUNDIR")/"
  [ "$AUTHOR" = 0 ] || echo "ci.sh: reference logs: $(show "$REFDIR")/"
} | tee "$RUNDIR/summary.txt"

T0=$SECONDS
NPASS=0; NFAIL=0; NSKIP=0; NABSENT=0
for JOB in "${SELECTED[@]}"; do
  JOBLOG="$RUNDIR/$JOB.log"
  REFLOG="$REFDIR/$JOB.ref.log"
  STATUSF="$RUNDIR/.$JOB.status"
  : > "$JOBLOG"
  rm -f "$STATUSF"
  printf '# ci.sh job %s — %s\n# %s\n' "$JOB" "$(describe "$JOB")" "$(date -u +%FT%TZ)" >> "$JOBLOG"
  t0=$SECONDS
  ( job_body ) &
  if wait "$!"; then rc=0; else rc=$?; fi
  dt=$((SECONDS - t0))
  if [ -s "$STATUSF" ]; then
    IFS=$'\t' read -r st why < "$STATUSF"
  else
    st=FAIL; why="ci.sh internal error (exit $rc); see the log"
  fi
  [ "$rc" = 0 ] || [ "$st" = FAIL ] || { st=FAIL; why="ci.sh internal error (exit $rc); see the log"; }
  case "$st" in
    PASS) NPASS=$((NPASS + 1)) ;;
    FAIL) NFAIL=$((NFAIL + 1)) ;;
    SKIP) NSKIP=$((NSKIP + 1)) ;;
    ABSENT) NABSENT=$((NABSENT + 1)) ;;
  esac
  printf '%s\t%s\n' "$st" "$why" >> "$JOBLOG"
  extra=""
  if [ "$AUTHOR" = 1 ] && [ -f "$REFLOG" ]; then extra="; reference log $(show "$REFLOG")"; fi
  printf '%-6s %-15s %5ss  %s%s%s\n' "$st" "$JOB" "$dt" "$(show "$JOBLOG")" "$extra" "${why:+ — $why}" \
    | tee -a "$RUNDIR/summary.txt"
done

TOTAL=$((SECONDS - T0))
VERDICT=PASS
[ "$NFAIL" = 0 ] || VERDICT=FAIL
{
  echo "ci.sh: $VERDICT — $NPASS passed, $NFAIL failed, $NSKIP skipped, $NABSENT absent, in ${TOTAL} s ($KIND; $HEAD_DESC)"
  [ "$AUTHOR" = 1 ] || [ "$NSKIP" = 0 ] || echo "ci.sh: the skipped jobs are author-only; the pre-merge gate is scripts/ci.sh --author in the authoring worktree"
  [ "$NABSENT" = 0 ] || echo "ci.sh: ABSENT jobs are not built yet: they neither pass nor fail"
  echo "ci.sh: summary $(show "$RUNDIR/summary.txt")"
} | tee -a "$RUNDIR/summary.txt"

if [ "$VERDICT" = PASS ]; then
  # A passing run keeps exactly the scratch its retained reports name (vcheck's raw_dir
  # of each JSON document, the harness's environment paths) and removes the rest.
  REPORTS=("$RUNDIR")
  [ "$AUTHOR" = 0 ] || REPORTS+=("$REFDIR")
  if KEPT="$(py prune "$WORK" "${REPORTS[@]}")" && [ -n "$KEPT" ]; then
    echo "ci.sh: tool scratch the logs name kept: $(lines "$KEPT") path(s) under $WORK (the rest removed)" \
      | tee -a "$RUNDIR/summary.txt"
  else
    rm -rf "$WORK"
  fi
  if [ "$AUTHOR" = 1 ]; then
    if KEPT="$(py prune "$REFDIR/scratch" "${REPORTS[@]}")" && [ -n "$KEPT" ]; then
      echo "ci.sh: reference scratch the logs name kept: $(lines "$KEPT") path(s) under $(show "$REFDIR/scratch")" \
        | tee -a "$RUNDIR/summary.txt"
    else
      rm -rf "$REFDIR/scratch"; rmdir "$REFDIR" 2>/dev/null || true
    fi
  fi
  exit 0
fi
echo "ci.sh: tool scratch kept for inspection: $WORK" >> "$RUNDIR/summary.txt"
exit 1
