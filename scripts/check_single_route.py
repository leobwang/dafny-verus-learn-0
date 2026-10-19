#!/usr/bin/env python3
"""check_single_route.py: only the entry points start containers, agents or sudo.

Guard rule 1f says container and agent runs go only through
scripts/mksandbox-run, scripts/contract_local.sh and the fvh harness (Δ83),
and no course script calls sudo (DV4-PLAN §5.1, P8). The hook cannot enforce
this on the entry points' callers without refusing ci.sh and its own fixtures
(DV4-PLAN §8, the 1f row), so this build-time check does: it lists every
course code file that names a container tool, an agent or model CLI, a
privilege change or a container socket, and fails on any file outside the
allowlist below. A mention counts, comments included: the check reads words,
not intent, so a new script that only talks about `docker` in a comment must
be allowlisted with its reason or reworded.

Scanned: the checkout's tracked and untracked-but-not-ignored files that hold
code (.py .sh .bash .rs .dfy .js .ts, and any file whose first line is a
shebang), outside the reference trees (never read in a study run). Prose and
data (.md .tex .txt .json .jsonl .toml) are not code and are not scanned.

Usage: scripts/check_single_route.py [--root DIR] [--list]
  --list   print every file that names one of the words, allowlisted or not
Exit: 0 clean, 1 a file outside the allowlist names one, 2 usage.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Every file allowed to name the words, with its reason. A trailing "/" is a
# directory prefix.
ALLOWLIST = {
    "bench/local/r/labalpha/pub-hev-075/tasks/pub-hev-075.rs": "a Lab alpha public task form "
        "(HumanEval-Verus human_eval_064, byte-faithful): its counter variable is named ctr; "
        "benchmark code, never a command",
    "scripts/mksandbox-run": "the one program that starts a container (DV4-PLAN §5)",
    "scripts/dvl/sandbox.py": "mksandbox-run's library: the docker argv and the access check",
    "scripts/contract_local.sh": "the local contract replay's front end (DV4-PLAN §6)",
    "scripts/dvl/contract_local.py": "contract_local.sh's library: the replay's checks and manifest",
    "sandbox/": "the images, entry points, relays and host-side gate (DV4 steps 2a-2c)",
    "harness/fvh/backends/": "the fvh model transports (DV4-PLAN §3.4)",
    "harness/fvh/executor.py": "the fvh executor: verification through mksandbox-run",
    "harness/fvh/tools/": "the fvh instrument runners: ContainerRunner calls mksandbox-run",
    ".claude/hooks/spoiler-guard.sh": "the guard: rule 1f names every word it refuses",
    "scripts/test_hooks.sh": "the hook-test harness",
    "scripts/gen_hook_fixtures.py": "the hook fixtures' generator and decoy trees",
    "tests/hooks/": "the hook's fixtures",
    "tests/acceptance/": "the by-hand acceptance scripts (guard doors, sandbox doors, smoke runs)",
    "tests/instructor/calibration/": "the by-hand grader calibration (spec §6.12); calls the subscription CLI, never from CI",
    "tests/instructor/simulations/": "the by-hand skill simulations (spec §9.5 step 8); call the subscription CLI, never from CI",
    "scripts/ci.sh": "the CI runner: the harness job's tripwire shims refuse these commands",
    "harness/tests/conftest.py": "the harness tests' network tripwire",
    "harness/tests/core/test_nettrip.py": "the tripwire's own tests refuse a container socket",
    "harness/tests/core/fakes/": "the fake claude and opencode executables of the backend tests",
    "tests/sandbox/": "the sandbox suites: a fake docker that refuses",
    "tests/ci/test_ci_dv4.py": "this check's own cases plant the words",
    "scripts/check_single_route.py": "this check names the words",
}

CODE_EXT = (".py", ".sh", ".bash", ".rs", ".dfy", ".js", ".ts", ".mjs")
SKIP_EXT = (".md", ".tex", ".txt", ".json", ".jsonl", ".toml", ".lock", ".csv", ".pdf", ".png",
            ".svg", ".pins", ".counts", ".freeze", ".audit", ".slots", ".bib", ".cls", ".sty")
REFERENCE = ("Solutions/", "paper/solutions/", "tests/instructor/leak_patterns/",
             "tests/instructor/fixtures/", "Hidden/")

_B = r"(?<![A-Za-z0-9_.-])"
_E = r"(?![A-Za-z0-9_-])"
WORDS = re.compile(
    _B + r"(docker|docker-compose|dockerd[A-Za-z-]*|podman|nerdctl|buildah|crictl|incus|lxd|"
    r"opencode|codex|ollama|sudo|pkexec|doas|runuser|newgrp)" + _E
    + r"|(?:^|[;&|(`]|\$\(|\s)(su|sg|ctr|lxc|runc)\s+-"
    + r"|[\"'](su|sg|ctr|lxc|runc)[\"']\s*[,\]]"
    + r"|DOCKER_HOST=|docker\.sock|podman\.sock|containerd\.sock|--unix-socket|http\+unix:"
    + r"|" + _B + r"claude\s+(-p|--print|-c|--continue|-r|--resume|auth|setup-token|update|mcp|--tools)" + _E
    + r"|[\"']claude[\"']\s*[,\])]",
    re.M)


def course_files(root):
    p = subprocess.run(["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
                       capture_output=True)
    if p.returncode != 0:
        names = [x.relative_to(root).as_posix() for x in root.rglob("*") if x.is_file()
                 and ".git" not in x.relative_to(root).parts]
    else:
        names = [n for n in p.stdout.decode("utf-8", "replace").split("\0") if n]
    for rel in sorted(names):
        if rel.startswith(REFERENCE) or rel.endswith(SKIP_EXT):
            continue
        path = root / rel
        if not path.is_file() or path.is_symlink():
            continue
        if rel.endswith(CODE_EXT):
            yield rel, path
            continue
        try:
            with open(path, "rb") as f:
                head = f.read(2)
        except OSError:
            continue
        if head == b"#!":
            yield rel, path


def allowed(rel):
    return any(rel == k or (k.endswith("/") and rel.startswith(k)) for k in ALLOWLIST)


def scan(root):
    """[(rel, line, word)] for every hit; the first hit of each file."""
    hits = []
    for rel, path in course_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = WORDS.search(text)
        if m:
            line = text.count("\n", 0, m.start()) + 1
            hits.append((rel, line, m.group(0).strip()))
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser(description="Only the entry points start containers, agents or sudo.")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    hits = scan(root)
    bad = [h for h in hits if not allowed(h[0])]
    if a.list:
        for rel, line, word in hits:
            print(f"{'ok ' if allowed(rel) else 'BAD'} {rel}:{line}: {word}")
    for rel, line, word in bad:
        print(f"check_single_route: {rel}:{line} names {word!r}: only the entry points start "
              "containers, agents or sudo (guard rule 1f, DV4-PLAN §8). Route the run through "
              "scripts/mksandbox-run, scripts/contract_local.sh or fvh, or allowlist the file in "
              "scripts/check_single_route.py with its reason.", file=sys.stderr)
    print(f"check_single_route: {len(hits)} file(s) name a container tool, an agent CLI or sudo; "
          f"{len(hits) - len(bad)} allowlisted, {len(bad)} outside the allowlist")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
