#!/usr/bin/env bash
# update_rubric_pins.sh — fill and check the sha256 pins in paper/rubrics/*_rubric.md
# (phase DV1b; spec §4.6, §8.3, §8.5 "rubric pins fresh"; paper/rubrics/README.md).
#
# A rubric pins the sources it was distilled from, so a rubric that drifts out of
# date with them fails loudly. Rubric authors cannot read the reference, so they
# write PENDING; this script, run by the author or by scripts/ci.sh (CI=true), where
# no permission layer applies, fills in the hash.
#
# Pin line (anywhere in a rubric; the rubric README's layout puts them under the
# "Solution pins (…)" heading line):
#     <repo-relative path>  sha256 <64-hex | PENDING>[ — note]
# The path is repo-relative (no leading /, no ..). Pins may target reference twins
# or learner files.
#
# Usage: scripts/update_rubric_pins.sh [--check] [--root DIR]
#   (no flag)  rewrite every PENDING or stale pin in place; a missing target fails
#   --check    change nothing; exit 1 on any PENDING, stale or missing target
#              (a renamed target must fail loudly)
#   Both modes also fail on a rubric file with no pin line, and on a rubric
#   that the registry (MODULES.toml) names for an armed (non-planned) module
#   but that does not exist: empty sets fail where something is required.
#   With no rubric file at all and no armed module that needs one, there is
#   nothing to check: both modes say so and pass (loudly). --allow-empty is
#   still accepted and changes nothing.
#
# Author-only: it hashes reference files, so it refuses (exit 3) unless CI=true or
# it runs in a linked git worktree whose HEAD is not on a learner branch (spec
# §7.4; the learner branch prefix comes from scripts/course_mode.sh). The guard
# hook also refuses any study-mode command that names this script. It prints paths
# and states only, never file content.
#
# Exit: 0 ok (or nothing to check) · 1 PENDING/stale/missing pins, a rubric with no
# pin, or a missing required rubric · 2 usage · 3 refused (author gate, or an
# unreadable MODULES.toml).

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK=0
ALLOW_EMPTY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --check) CHECK=1 ;;
    --allow-empty) ALLOW_EMPTY=1 ;;
    --root) [ $# -ge 2 ] || { echo "update_rubric_pins: --root needs a directory" >&2; exit 2; }
            ROOT="$(cd "$2" && pwd)"; shift ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    *) echo "update_rubric_pins: unknown argument '$1' (usage: [--check] [--root DIR])" >&2; exit 2 ;;
  esac
  shift
done

# The author self-gate (spec §7.4): CI=true, or a linked worktree off a learner branch.
author_ok() {
  [ "${CI:-}" = true ] && return 0
  local gd cd br prefix
  gd="$(git -C "$ROOT" rev-parse --path-format=absolute --git-dir 2>/dev/null)" || return 1
  cd="$(git -C "$ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || return 1
  [ "$gd" != "$cd" ] || return 1
  prefix="$(sed -n "s/^LEARNER_PREFIX=['\"]\{0,1\}\([A-Za-z0-9_.-]*\).*/\1/p" \
              "$ROOT/scripts/course_mode.sh" 2>/dev/null | head -n 1)"
  prefix="${prefix:-leobwang-}"
  br="$(git -C "$ROOT" symbolic-ref --short -q HEAD 2>/dev/null || true)"
  case "$br" in "$prefix"*) return 1 ;; esac
  return 0
}
if ! author_ok; then
  echo "update_rubric_pins: author-only; refused outside scripts/ci.sh (CI=true) and the course author's worktree (spec §7.4)" >&2
  exit 3
fi

exec python3 - "$ROOT" "$CHECK" "$ALLOW_EMPTY" <<'PY'
import hashlib
import re
import sys
import tomllib
from pathlib import Path, PurePosixPath

root = Path(sys.argv[1])
check = sys.argv[2] == "1"
PIN = re.compile(r"^(?P<pre>\s*[-*]?\s*`?)(?P<path>[\w./\-]+\.[A-Za-z0-9]+)"
                 r"(?P<mid>`?\s+sha256\s+)(?P<val>[0-9a-f]{64}|PENDING)(?P<rest>.*)$")

# The rubrics the registry requires: the `rubric` field of every armed module.
required = {}
reg = root / "MODULES.toml"
if reg.is_file():
    try:
        mods = tomllib.loads(reg.read_text(encoding="utf-8")).get("module", [])
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        print(f"update_rubric_pins: refused: MODULES.toml is unreadable ({e.__class__.__name__}); "
              "run python3 scripts/check_course_map.py", file=sys.stderr)
        sys.exit(3)
    for m in mods if isinstance(mods, list) else []:
        if isinstance(m, dict) and m.get("status") != "planned" and \
                isinstance(m.get("rubric"), str) and m["rubric"]:
            required[m["rubric"]] = m.get("id", "?")

pending, stale, missing, bad, updated, unpinned = [], [], [], [], [], []
checked = 0
rubrics = sorted((root / "paper" / "rubrics").glob("*_rubric.md"))
absent = [f"{rel} (the rubric of armed module {mid})" for rel, mid in sorted(required.items())
          if not (root / rel).is_file()]
if not rubrics and not required:
    print("update_rubric_pins" + (" --check" if check else "") + ": no rubric file under "
          "paper/rubrics/ yet and no armed module needs one: nothing to check (passing loudly)")
    sys.exit(0)
for rubric in rubrics:
    rrel = rubric.relative_to(root).as_posix()
    lines = rubric.read_text(encoding="utf-8").splitlines(keepends=True)
    out, changed, here = [], False, 0
    for ln, line in enumerate(lines, 1):
        m = PIN.match(line.rstrip("\n"))
        if not m:
            out.append(line)
            continue
        checked += 1
        here += 1
        rel = m.group("path")
        parts = PurePosixPath(rel).parts
        if rel.startswith("/") or ".." in parts:
            bad.append(f"{rrel}:{ln}: {rel}")
            out.append(line)
            continue
        target = root / rel
        if not target.is_file():
            # a pin whose target is gone can never go stale: it fails loudly instead
            missing.append(f"{rrel}:{ln}: {rel}")
            out.append(line)
            continue
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if m.group("val") == digest:
            out.append(line)
            continue
        if check:
            (pending if m.group("val") == "PENDING" else stale).append(f"{rrel}:{ln}: {rel}")
            out.append(line)
            continue
        nl = "\n" if line.endswith("\n") else ""
        out.append(f"{m.group('pre')}{rel}{m.group('mid')}{digest}{m.group('rest')}{nl}")
        changed = True
        updated.append(f"{rrel}:{ln}: {rel}")
    if changed:
        rubric.write_text("".join(out), encoding="utf-8")
    if not here:
        unpinned.append(rrel)

for x in absent:
    print(f"MISSING RUBRIC: {x}")
for x in unpinned:
    print(f"NO PIN: {x} (a rubric pins the sources it was distilled from; an empty set fails)")
for x in missing:
    print(f"MISSING: {x}")
for x in bad:
    print(f"BAD PATH: {x} (repo-relative, no leading /, no ..)")
structural = len(absent) + len(unpinned) + len(missing) + len(bad)
if check:
    for label, items in (("PENDING", pending), ("STALE", stale)):
        for x in items:
            print(f"{label}: {x}")
    if pending or stale or structural:
        print(f"update_rubric_pins --check: {len(pending)} pending, {len(stale)} stale, "
              f"{len(missing)} missing, {len(bad)} bad (of {checked} pins in {len(rubrics)} "
              f"rubric(s)); {len(unpinned)} rubric(s) with no pin, {len(absent)} required "
              "rubric(s) absent; run scripts/update_rubric_pins.sh, and fix missing paths by hand")
        sys.exit(1)
    print(f"update_rubric_pins --check: all {checked} rubric pins current ({len(rubrics)} "
          "rubric(s))")
    sys.exit(0)
for x in updated:
    print(f"UPDATED: {x}")
print(f"update_rubric_pins: {len(updated)} pin(s) written of {checked}"
      + (f"; {len(missing)} missing, {len(bad)} bad, {len(unpinned)} rubric(s) with no pin, "
         f"{len(absent)} required rubric(s) absent: fix by hand" if structural else ""))
sys.exit(1 if structural else 0)
PY
