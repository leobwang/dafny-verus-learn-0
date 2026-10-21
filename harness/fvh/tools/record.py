"""fvh.tools.record — the author-only recorder of instrument results (DV4-PLAN §3.7).

Usage (from harness/, e.g. `uv run --directory harness python -m fvh.tools.record ...`):

  python -m fvh.tools.record --half Q [--lang dafny|verus] [--only ID ...]
                             [--instrument NAME ...] [--out DIR] [--dry-run]

For every fixture of the half (fvh.corpus.load_half: the fixtures that hold a
program) it runs instruments through HostRunner on the host, one solver job at
a time under the course tools' caps, and writes each normalized result to
<out>/<lang>/<ID>/<slug(instrument)>.json (fvh.tools.runners: the recorded
files). The default <out> for the Q half is harness/tests/q/fixtures/q09; the
R half needs --out. A relative --out is taken from the course root, and --out
must lie inside it.

Which instruments: every instrument of CORE_INSTRUMENTS (or of --instrument, which may
also name the challenge instruments solver-swap and reach, Δ402) whose
inputs exist for the delivery: the target, and the companion file or crate the
instrument names (tests/corpus/README.md's table). The recorder reads the
deliveries only, never a label: what it records does not depend on a
fixture's class, kind or expected outcomes.

What is recorded: results only (fvh.tools.runners: the recorded files), never
a label. A run whose exit is not 0 or 1 (a usage error, a refusal) or that was
killed is reported and never recorded. When every instrument of a fixture was
recorded and no --instrument narrowed the run, any other recorded file in that
fixture's directory is removed.

Author-only: it refuses (exit 3) unless CI is "true" or the three-condition test
holds (inside git, a linked worktree, HEAD not on the learner branch prefix
that scripts/course_mode.sh names), like `scripts/test_corpus.py --update`
(Δ103). Git discovery stops at the course root's parent.

Memory (CLAUDE.md §Resources): before the first job, MemAvailable must hold the
largest cap of the languages that will run plus 15 GB; HostRunner checks it
again before each job.

Exit: 0 every planned result recorded (or listed, with --dry-run) · 1 a run
failed or the memory preflight did · 2 usage · 3 refused (not the author's
context, or --out outside the course root).

Frozen (guard rule 2f), standard library only.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from fvh import corpus, tools
from fvh.tools import runners as R

EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_REFUSED = 0, 1, 2, 3
DEFAULT_LEARNER_PREFIX = "leobwang-"
_GIT_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
             "GIT_OBJECT_DIRECTORY", "GIT_NAMESPACE")


def learner_prefix(root) -> str:
    """The learner branch prefix, read from scripts/course_mode.sh (one source)."""
    try:
        text = (Path(root) / "scripts" / "course_mode.sh").read_text(encoding="utf-8")
    except OSError:
        return DEFAULT_LEARNER_PREFIX
    m = re.search(r"^LEARNER_PREFIX=['\"]?([A-Za-z0-9_.-]+)", text, re.M)
    return m.group(1) if m else DEFAULT_LEARNER_PREFIX


def author_gate(root) -> str | None:
    """None when the recorder may run on this course root, else why not (Δ103)."""
    if os.environ.get("CI") == "true":
        return None
    root = Path(root).resolve()
    env = {k: v for k, v in os.environ.items() if k not in _GIT_VARS}
    env["GIT_CEILING_DIRECTORIES"] = str(root.parent)

    def git(*args):
        try:
            p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                               timeout=30, env=env, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return p.stdout.strip() if p.returncode == 0 else None

    gd = git("rev-parse", "--path-format=absolute", "--git-dir")
    cd = git("rev-parse", "--path-format=absolute", "--git-common-dir")
    if not gd or not cd:
        return "not inside a git checkout"
    if os.path.realpath(gd) == os.path.realpath(cd):
        return "this is the primary worktree"
    branch = git("symbolic-ref", "--short", "-q", "HEAD")
    if branch and branch.startswith(learner_prefix(root)):
        return "HEAD is on a learner branch"
    return None


def _parser():
    ap = argparse.ArgumentParser(
        prog="python -m fvh.tools.record", allow_abbrev=False,
        description="Author-only: record instrument results for the corpus fixtures of a half.")
    ap.add_argument("--half", required=True, choices=corpus.HALVES)
    ap.add_argument("--lang", choices=corpus.LANGS)
    ap.add_argument("--only", nargs="+", action="extend", default=[], metavar="ID",
                    help="fixture ids (ID or LANG/ID)")
    ap.add_argument("--instrument", action="append", default=[], choices=R.INSTRUMENTS,
                    metavar="NAME", help="record only these instruments (repeatable)")
    ap.add_argument("--out", metavar="DIR",
                    help="where to write (default for --half Q: " + R.FIXTURES + ")")
    ap.add_argument("--dry-run", action="store_true", help="list what would run; run nothing")
    return ap


def _say(*parts):
    print(*parts, flush=True)


def main(argv=None, *, root=None, runner=None) -> int:
    """The recorder. `root` is the course root (default: this checkout); a
    caller that passes `runner` (a HostRunner) does its own memory preflight."""
    try:
        a = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as e:
        return EXIT_USAGE if e.code else EXIT_OK
    root = Path(os.path.realpath(root if root is not None else R.ROOT))
    why = author_gate(root)
    if why:
        print(f"fvh.tools.record: refused: the recorder is author-only and refuses to run here "
              f"({why}); it writes recorded tool results, so it runs only in the course "
              "author's worktree or with CI set to true (Δ103)", file=sys.stderr)
        return EXIT_REFUSED
    if a.out is None and a.half != "Q":
        print("fvh.tools.record: --half R has no default layout: name --out", file=sys.stderr)
        return EXIT_USAGE
    out = Path(a.out) if a.out is not None else Path(R.FIXTURES)
    out = Path(os.path.realpath(out if out.is_absolute() else root / out))
    if not out.is_relative_to(root) or out == root:
        print(f"fvh.tools.record: refused: --out {out} must lie inside the course root {root}",
              file=sys.stderr)
        return EXIT_REFUSED

    langs = [a.lang] if a.lang else list(corpus.LANGS)
    fixtures = []
    try:
        for lang in langs:
            fixtures += corpus.load_half(lang, a.half, root=root)
    except corpus.CorpusError as e:
        print(f"fvh.tools.record: {e}", file=sys.stderr)
        return EXIT_FAIL
    chosen = fixtures
    if a.only:
        chosen, unknown = [], []
        for s in a.only:
            hits = [f for f in fixtures if s in (f.id, f"{f.delivery.lang}/{f.id}")]
            if not hits:
                unknown.append(s)
            chosen += [f for f in hits if f not in chosen]
        if unknown:
            print(f"fvh.tools.record: no fixture of half {a.half} matches "
                  f"{', '.join(map(repr, unknown))}", file=sys.stderr)
            return EXIT_USAGE
    if not chosen:
        print(f"fvh.tools.record: half {a.half} has no fixture to record (an empty set fails)",
              file=sys.stderr)
        return EXIT_FAIL
    wanted = [i for i in R.INSTRUMENTS if i in a.instrument] if a.instrument else \
        list(R.CORE_INSTRUMENTS)

    plan = []
    for fx in chosen:
        d = fx.delivery
        insts = []
        for inst in wanted:
            try:
                paths = R._input_paths(inst, d.target, lang=d.lang)
            except ValueError:
                continue
            if all((root / p).exists() for p in paths):
                insts.append(inst)
        plan.append((fx, insts))
    if a.dry_run:
        for fx, insts in plan:
            _say(f"PLAN   {fx.delivery.lang}/{fx.id}: " + (", ".join(insts) or "(nothing)"))
        _say(f"fvh.tools.record: dry run: {sum(len(i) for _, i in plan)} result(s) for "
             f"{len(plan)} fixture(s); nothing ran")
        return EXIT_OK

    if runner is None:
        runner = R.HostRunner(root)
        need_langs = sorted({fx.delivery.lang for fx, insts in plan if insts})
        try:
            caps = []
            for lang in need_langs:
                R.preflight(root, lang)
                caps.append(R._pin(root, lang, "mem_gb"))
            if caps:
                _say(f"fvh.tools.record: memory preflight: {R.mem_available_gb()} GB available, "
                     f"{max(caps) + R.RESERVE_GB} GB needed")
        except R.PreflightError as e:
            print(f"fvh.tools.record: {e}", file=sys.stderr)
            return EXIT_FAIL

    written = failed = 0
    for fx, insts in plan:
        d = fx.delivery
        fdir = out / d.lang / fx.id
        done, problems = [], []
        for inst in insts:
            try:
                res = tools.run(inst, d.target, root=root, runner=runner)
            except (R.PreflightError, R.ProvenanceError, R.RunnerUnavailable, ValueError) as e:
                problems.append(f"{inst}: not run ({type(e).__name__}: {e})")
                continue
            if res.killed is not None:
                problems.append(f"{inst}: killed ({res.killed}), never recorded")
                continue
            if res.exit_code not in (0, 1):
                problems.append(f"{inst}: exit {res.exit_code} (a usage error or a refusal), "
                                "never recorded")
                continue
            R.write_recording(R.recording_path(out, d.lang, fx.id, inst), res,
                              runner.argv(inst, d.target))
            written += 1
            done.append(f"{inst} exit {res.exit_code}")
        if problems:
            failed += 1
            _say(f"FAIL   {d.lang}/{fx.id}: " + "; ".join(problems))
        else:
            keep = {f"{R.slug(i)}.json" for i in insts}
            stale = sorted(fdir.glob("*.json")) if fdir.is_dir() and not a.instrument else []
            for f in stale:
                if f.name not in keep:
                    f.unlink()
            _say(f"RECORD {d.lang}/{fx.id}: " + (", ".join(done) or "(no instrument applies)"))
    _say(f"fvh.tools.record: {written} result(s) written for {len(plan)} fixture(s), "
         f"{failed} fixture(s) failed; under {out.relative_to(root).as_posix()}")
    return EXIT_FAIL if failed else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
