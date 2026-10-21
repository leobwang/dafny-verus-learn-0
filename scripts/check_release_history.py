#!/usr/bin/env python3
"""D42 and D46: the shipped branch `basic` carries no authoring or archived ancestry.

    python3 scripts/check_release_history.py [CANDIDATE] [--base main] [--root DIR]

The invariant, checked read-only on the candidate (default `basic`) against the design
baseline (default `main`), never rewriting any history:

  1. main..CANDIDATE is a non-empty linear chain of single-parent commits: the first
     one's parent is main, and every later one's parent is the one before it (no merge,
     no second line). The first is the D42 release squash; the later ones are fixes.
  2. Every commit of that chain has a subject that starts with "basic: ".
  3. No archived commit is reachable from the candidate. An archived commit is one
     reachable from a tag `archive/*` that is neither on main nor released: a released
     commit is one reachable from a release tag `basic-*` (`basic-q-initial` marks the
     D42 squash). Archive tags were cut from authoring lines that start on a released
     basic, so they share main and the released commits with basic, and nothing else may
     be shared (the user's D46 rolled basic back from R01-R02, now archived).

    python3 scripts/check_release_history.py --challenge [CHALLENGE] [--basic basic] [--base main]

The `challenge` mode (the user's D26 release plan; QPLAN §38 item 5; DELTAS Δ402) checks
the challenge branch: basic's own invariant holds; and basic..CHALLENGE is one
first-parent line whose commits are either single-parent squashes with a subject that
starts with "challenge: " (one per topic, or a fix) or merges of basic forward, with the
subject "challenge: merge basic …" and a second parent on basic; CHALLENGE contains
basic's tip (every basic fix is merged forward at once); and no commit of
basic..CHALLENGE is reachable from an archive/* tag or from an authoring line
(the local branches dv7, authoring, labalpha and sysb, where they exist): challenge
content arrives as squashes, never as authoring history.

scripts/ci.sh's static job runs it on the course's `basic` (the local branch, else
origin/basic) and passes loudly where the checkout has no `basic` or no `main`, and
on `challenge` the same way once that branch exists.
Exit 0 when the invariant holds, 1 when it does not.
"""
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREFIX = "basic: "
ARCHIVE_TAGS = "refs/tags/archive/"
RELEASE_TAGS = "refs/tags/basic-*"


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          check=True).stdout


def resolve(root, name):
    """The commit `name` names (a branch, tag, remote branch or sha), or None."""
    for ref in (f"refs/heads/{name}", name, f"refs/remotes/origin/{name}"):
        try:
            return _git(root, "rev-parse", "--verify", "-q", ref + "^{commit}").strip() or None
        except subprocess.CalledProcessError:
            continue
    return None


def _tag_commits(root, prefix):
    out = _git(root, "for-each-ref", "--format=%(objectname)", prefix).split()
    return [_git(root, "rev-parse", c + "^{commit}").strip() for c in out]


def problems(root, candidate="basic", base="main"):
    """The invariant's violations, as messages (empty: it holds)."""
    head, baseline = resolve(root, candidate), resolve(root, base)
    if head is None or baseline is None:
        return [f"{candidate if head is None else base} is not a known commit"]
    try:
        chain = [line.split() for line in
                 _git(root, "rev-list", "--reverse", "--parents", head, "^" + baseline).splitlines()]
        subjects = dict(line.split("\x00", 1) for line in
                        _git(root, "log", "--format=%H%x00%s", head, "^" + baseline).splitlines())
    except subprocess.CalledProcessError as e:
        return [f"git could not list {base}..{candidate} ({e.stderr.strip()})"]
    if not chain:
        return [f"{candidate} adds no commit atop {base}: the first basic release is one squash "
                f"whose parent is {base}"]
    out = []
    prev = baseline
    for c, *parents in chain:
        if len(parents) != 1:
            out.append(f"{c[:12]} has {len(parents)} parents: {base}..{candidate} must be a "
                       "linear chain of single-parent commits")
        elif parents[0] != prev:
            out.append(f"{c[:12]}'s parent {parents[0][:12]} is not "
                       + (f"{base}" if prev == baseline else f"the previous commit {prev[:12]}")
                       + f": {base}..{candidate} must be one linear chain starting on {base}")
        prev = c
        if not subjects.get(c, "").startswith(PREFIX):
            out.append(f"{c[:12]}'s subject {subjects.get(c, '')!r} does not start with "
                       f"{PREFIX.strip()!r}")
    archives = _tag_commits(root, ARCHIVE_TAGS)
    if archives:
        not_archived = ["^" + baseline] + ["^" + t for t in _tag_commits(root, RELEASE_TAGS)]
        archived = set(_git(root, "rev-list", *archives, *not_archived).split())
        for c in _git(root, "rev-list", head, *not_archived).split():
            if c in archived:
                out.append(f"{c[:12]} is archived history (reachable from an archive/* tag, "
                           "neither on main nor under a basic-* release tag) and is reachable "
                           f"from {candidate}")
    return out


CHALLENGE_PREFIX = "challenge: "
MERGE_PREFIX = "challenge: merge basic"
AUTHORING_LINES = ("dv7", "authoring", "labalpha", "sysb")


def _is_ancestor(root, a, b):
    return subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", a, b],
                          capture_output=True).returncode == 0


def challenge_problems(root, candidate="challenge", basic="basic", base="main"):
    """The challenge invariant's violations (module doc), basic's included."""
    out = [f"basic: {m}" for m in problems(root, basic, base)]
    head, b = resolve(root, candidate), resolve(root, basic)
    if head is None or b is None:
        return out + [f"{candidate if head is None else basic} is not a known commit"]
    if not _is_ancestor(root, b, head):
        out.append(f"{candidate} does not contain {basic}'s tip {b[:12]}: merge {basic} forward "
                   "at once")
    chain = [line.split() for line in
             _git(root, "rev-list", "--reverse", "--parents", head, "^" + b).splitlines()]
    first = set(_git(root, "rev-list", "--first-parent", head, "^" + b).split())
    subjects = dict(line.split("\x00", 1) for line in
                    _git(root, "log", "--format=%H%x00%s", head, "^" + b).splitlines())
    if not chain:
        out.append(f"{candidate} adds no commit atop {basic}")
    for c, *parents in chain:
        subj = subjects.get(c, "")
        if c not in first:
            out.append(f"{c[:12]} is off {candidate}'s first-parent line: only squashes and "
                       f"merges of {basic} are allowed")
        if len(parents) == 1:
            if not subj.startswith(CHALLENGE_PREFIX) or subj.startswith(MERGE_PREFIX):
                out.append(f"{c[:12]}'s subject {subj!r} does not start with "
                           f"{CHALLENGE_PREFIX.strip()!r} (a single-parent squash)")
        elif len(parents) == 2:
            if not subj.startswith(MERGE_PREFIX):
                out.append(f"{c[:12]} is a merge whose subject {subj!r} does not start with "
                           f"{MERGE_PREFIX!r}")
            if not _is_ancestor(root, parents[1], b):
                out.append(f"{c[:12]} merges {parents[1][:12]}, which is not on {basic}: only "
                           f"{basic} is merged forward")
        else:
            out.append(f"{c[:12]} has {len(parents)} parents")
    own = [c for c, *_ in chain]
    forbidden = _tag_commits(root, ARCHIVE_TAGS) + [x for x in (resolve(root, n) for n in
                                                                AUTHORING_LINES
                                                                if n != candidate) if x]
    if forbidden and own:
        reach = set(_git(root, "rev-list", *forbidden, "^" + b).split())
        for c in own:
            if c in reach:
                out.append(f"{c[:12]} is authoring or archived history (reachable from an "
                           f"archive/* tag or an authoring line) and is on {candidate}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("candidate", nargs="?", default=None)
    ap.add_argument("--base", default="main")
    ap.add_argument("--basic", default="basic")
    ap.add_argument("--challenge", action="store_true")
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()
    if args.challenge:
        cand = args.candidate or "challenge"
        errors = challenge_problems(args.root, cand, args.basic, args.base)
        if errors:
            print("release history (challenge): " + "; ".join(errors))
            return 1
        n = len(_git(args.root, "rev-list", resolve(args.root, cand),
                     "^" + resolve(args.root, args.basic)).split())
        print(f"release history: OK ({cand}: {n} commit(s) atop {args.basic}, squashes and "
              f"merges of {args.basic} only; {args.basic} contained; no authoring or archived "
              "commit reachable)")
        return 0
    args.candidate = args.candidate or "basic"
    errors = problems(args.root, args.candidate, args.base)
    if errors:
        print("release history: " + "; ".join(errors))
        return 1
    n = len(_git(args.root, "rev-list", resolve(args.root, args.candidate),
                 "^" + resolve(args.root, args.base)).split())
    print(f"release history: OK ({args.candidate}: {n} single-parent 'basic: ' commit(s) atop "
          f"{args.base}; no archived commit reachable)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
