"""Shared helpers for the scripts/ci.sh suites (test_ci_static.py, test_ci_tool.py).

ci.sh takes a hidden --root DIR: it checks the course at DIR with this
checkout's scripts. These helpers build throwaway roots and run ci.sh on them
with --log-dir in a temporary directory, so a test reads the job logs and the
console separately. Nothing here is course content; no root holds reference
material.

run_ci() drops CI from the environment unless a test sets it, stops git
discovery at the root's parent (GIT_CEILING_DIRECTORIES), and moves ci.sh's
tool scratch (DVL_CI_WORK) into the test's temporary directory.

This module holds no TestCase: unittest discovery imports it and finds nothing.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CI_SH = ROOT / "scripts" / "ci.sh"
TMP_BASE = os.environ.get("DVL_TEST_TMP") or None
GIT = ["git", "-c", "user.name=ci-tests", "-c", "user.email=ci-tests@example.invalid",
       "-c", "init.defaultBranch=main"]
# A console line of ci.sh: a header or summary line, or one job line
# (status, job, seconds, log location, then an optional reason).
CONSOLE_LINE = re.compile(r"^(ci\.sh: .*|(PASS|FAIL|SKIP|ABSENT) +[a-z-]+ +\d+s  \S+.*)$")


def tmpdir(prefix):
    if TMP_BASE:
        Path(TMP_BASE).mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=TMP_BASE))


def course_lists():
    """(canonical, always-on) deny rules, from scripts/course_mode.sh (one source)."""
    src = (ROOT / "scripts" / "course_mode.sh").read_text(encoding="utf-8")
    out = []
    for name in ("CANONICAL_DENY", "ALWAYS_ON"):
        block = re.search(rf"^{name}=\((.*?)\)\n", src, re.S | re.M).group(1)
        out.append(re.findall(r'"([^"]+)"', block))
    return out[0], out[1]


def write_settings(root, deny):
    (root / ".claude").mkdir(exist_ok=True)
    (root / ".claude" / "settings.json").write_text(
        json.dumps({"permissions": {"deny": deny}}, indent=2) + "\n", encoding="utf-8")


# The module trees of dafny/ and verus/ (exercise files, check units and the units
# gen_units.py writes for armed modules): a planned-only root holds none of them.
MODULE_TREES = ("dafny/Q", "dafny/R", "dafny/checks", "verus/q", "verus/r")


def course_root(base):
    """A planned-only course root that mirrors this checkout's registry: the
    committed MODULES.toml with every module set to planned (DV2 armed Q01-Q03),
    dafny/ and verus/ copied without their module trees and with the units
    regenerated for that registry, the instructor layer's vocabulary and the
    docs linked, a study-mode settings.json (the canonical and always-on deny
    rules, whatever mode this checkout is in), and the paper Makefile with its
    preamble."""
    root = base / "root"
    root.mkdir()
    text = (ROOT / "MODULES.toml").read_text(encoding="utf-8")
    text = re.sub(r'(?m)^status = "(authoring|shipped)"$', 'status = "planned"', text)
    (root / "MODULES.toml").write_text(text, encoding="utf-8")
    for d in ("dafny", "verus"):
        if (ROOT / d).is_dir():
            shutil.copytree(ROOT / d, root / d, symlinks=True,
                            ignore=shutil.ignore_patterns("target"))
    for d in MODULE_TREES:
        shutil.rmtree(root / d, ignore_errors=True)
    subprocess.run(["python3", "-B", str(ROOT / "scripts" / "gen_units.py"), "--root", str(root)],
                   check=True, capture_output=True, text=True)
    canon, always = course_lists()
    write_settings(root, canon + always)
    os.symlink(ROOT / ".claude" / "skills", root / ".claude" / "skills")
    for d in ("docs", "instructor", "specimens", "slots", "tools"):
        if (ROOT / d).exists():
            os.symlink(ROOT / d, root / d)
    (root / "paper").mkdir()
    for f in ("Makefile", "preamble.tex"):
        shutil.copyfile(ROOT / "paper" / f, root / "paper" / f)
    return root


def git(*args, cwd):
    subprocess.run([*GIT, *args], cwd=str(cwd), check=True, capture_output=True, text=True)


def worktrees(base):
    """A primary checkout (base/repo) with two linked worktrees: base/learner on
    a leobwang-* branch and base/authoring on `authoring`."""
    repo = base / "repo"
    repo.mkdir()
    git("init", "-q", cwd=repo)
    git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
    git("worktree", "add", "-q", "-b", "leobwang-test", str(base / "learner"), cwd=repo)
    git("worktree", "add", "-q", "-b", "authoring", str(base / "authoring"), cwd=repo)
    return repo, base / "learner", base / "authoring"


def run_ci(*args, root=None, logs=None, env=None, home=None, script=CI_SH, timeout=1800):
    """Run ci.sh; returns (exit code, stdout, stderr)."""
    argv = ["bash", str(script), *[str(a) for a in args]]
    if root is not None:
        argv += ["--root", str(root)]
    if logs is not None:
        argv += ["--log-dir", str(logs)]
    e = {**os.environ}
    e.pop("CI", None)
    if root is not None:
        e["GIT_CEILING_DIRECTORIES"] = str(Path(root).resolve().parent)
        e["DVL_CI_WORK"] = str(Path(root).resolve().parent / "ci-work")
    if home is not None:
        e["HOME"] = str(home)
    e.update(env or {})
    p = subprocess.run(argv, capture_output=True, text=True, env=e, timeout=timeout,
                       cwd=str(root or ROOT))
    return p.returncode, p.stdout, p.stderr


def job_line(out, job):
    """The console line of one job, or None."""
    for line in out.splitlines():
        m = re.match(r"^(PASS|FAIL|SKIP|ABSENT) +(\S+) ", line)
        if m and m.group(2) == job:
            return line
    return None


def status_of(out, job):
    line = job_line(out, job)
    return line.split()[0] if line else None


def remove(path):
    shutil.rmtree(path, ignore_errors=True)
