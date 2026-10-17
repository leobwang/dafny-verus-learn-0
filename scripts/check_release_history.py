#!/usr/bin/env python3
"""D42: check that the first basic release has one content commit atop main.

Run with the candidate commit or basic branch after the freeze checks pass,
before distributing the release. Read-only; never rewrites authoring history.
"""
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def problems(root, candidate="basic", base="main"):
    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                              text=True, check=True).stdout.strip()
    try:
        baseline = git("rev-parse", "--verify", base + "^{commit}")
        head = git("rev-parse", "--verify", candidate + "^{commit}")
        parents = git("show", "-s", "--format=%P", head).split()
        added = git("rev-list", head, "^" + baseline).split()
    except subprocess.CalledProcessError:
        return ["candidate or design baseline is not a known commit"]
    if parents != [baseline] or added != [head]:
        return ["the first basic release must be exactly one commit whose sole parent is main"]
    return []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", nargs="?", default="basic")
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()
    errors = problems(args.root, args.candidate)
    print("release history: " + ("OK" if not errors else "; ".join(errors)))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
