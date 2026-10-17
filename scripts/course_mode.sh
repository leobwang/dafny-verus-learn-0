#!/usr/bin/env bash
# course_mode.sh — switch a checkout between AUTHORING and STUDY mode (spec §7.4).
#
# Two enforcement layers guard the reference material (CLAUDE.md §Roles):
#
#   1. .claude/settings.json  permissions.deny  — static; cannot read state.
#   2. .claude/hooks/spoiler-guard.sh           — honours .claude/state/mode,
#      but only where git confirms a linked worktree off the learner branch.
#
# Layer 1 cannot be conditional, so the two layers move together; otherwise
# authors are locked out of the very files they are writing (in the source
# course, rubric sha pins could not be computed).
#
#   authoring : the 4 canonical deny rules removed + state/mode = "authoring"
#   study     : the 4 canonical deny rules merged  + state/mode removed
#
# Both directions touch only CANONICAL_DENY below; every other deny rule
# survives either switch. In particular the always-on rules (ALWAYS_ON: other
# sessions' transcripts, file history and prompt history, and the
# local-assistant skill) stay in both modes: this script never adds or removes
# them. The same four canonical strings appear in CLAUDE.md, scripts/ci.sh's
# study-mode check and scripts/test_hooks.sh; change them together.
#
# Authoring happens in a dedicated linked worktree, never in the learner's
# checkout: `authoring` refuses (exit 1, nothing written, deny list untouched)
# outside git, in the primary worktree (git-dir == git-common-dir) and on a
# leobwang-* branch, and the hook ignores a mode file in any of those places.
#
# STUDY IS THE SHIPPING STATE. Never flip either layer by hand; scripts/ci.sh
# fails on a shipped mode file or a missing canonical rule.
#
# Usage: scripts/course_mode.sh authoring|study|status

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETTINGS="$ROOT/.claude/settings.json"
MODE_FILE="$ROOT/.claude/state/mode"
LEARNER_PREFIX=leobwang-

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

usage() { echo "usage: $(basename "$0") authoring|study|status" >&2; exit 2; }
[ $# -eq 1 ] || usage
case "$1" in authoring|study|status) ;; *) usage ;; esac
[ -f "$SETTINGS" ] || { echo "mode: no $SETTINGS" >&2; exit 1; }

deny() {
  # $1 = "on" (merge the canonical rules in, first) | "off" (take exactly them
  # out) | "show" (print the list and any canonical or always-on rule it lacks)
  python3 - "$SETTINGS" "$1" "${#CANONICAL_DENY[@]}" "${CANONICAL_DENY[@]}" "${ALWAYS_ON[@]}" <<'PY'
import json, sys
path, want, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
canon, always = sys.argv[4:4 + n], sys.argv[4 + n:]
with open(path) as f:
    cfg = json.load(f)
perms = cfg.setdefault("permissions", {})
deny = perms.get("deny", [])
if want == "show":
    print("deny:", json.dumps(deny))
    missing = [r for r in canon if r not in deny]
    if missing:
        print("missing canonical rules:", json.dumps(missing))
    lost = [r for r in always if r not in deny]
    if lost:
        print("WARNING: missing always-on rules (never moved by this script; restore them by hand):", json.dumps(lost))
    sys.exit(0)
others = [r for r in deny if r not in canon]
new = canon + others if want == "on" else others
if new != deny:
    perms["deny"] = new
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
PY
}

# Why this checkout may not author, or nothing when it may.
authoring_refusal() {
  local gd cdir branch
  if ! gd="$(git -C "$ROOT" rev-parse --git-dir 2>/dev/null)" \
     || ! cdir="$(git -C "$ROOT" rev-parse --git-common-dir 2>/dev/null)"; then
    echo "$ROOT is not a git checkout"; return
  fi
  gd="$(cd "$ROOT" && cd "$gd" && pwd -P)"
  cdir="$(cd "$ROOT" && cd "$cdir" && pwd -P)"
  branch="$(git -C "$ROOT" symbolic-ref --short -q HEAD || true)"
  case "$branch" in
    "$LEARNER_PREFIX"*) echo "$ROOT is on the learner branch $branch"; return ;;
  esac
  if [ "$gd" = "$cdir" ]; then echo "$ROOT is the primary worktree"; fi
}

case "$1" in
  authoring)
    why="$(authoring_refusal)"
    if [ -n "$why" ]; then
      echo "mode: refusing AUTHORING — $why. Nothing was changed." >&2
      # The recipe's start point: the shipped branch basic (D26: every fix lands
      # there first), origin/ before local; origin/main while basic does not exist.
      start=origin/main
      for ref in refs/remotes/origin/basic refs/heads/basic; do
        if git -C "$ROOT" rev-parse --verify -q "$ref^{commit}" >/dev/null 2>&1; then
          start="${ref#refs/remotes/}"; start="${start#refs/heads/}"; break
        fi
      done
      echo "Author in a dedicated linked worktree, outside the learner checkout and any session scratchpad:" >&2
      echo "  git -C \"$ROOT\" worktree add ../$(basename "$ROOT")-authoring -b authoring $start" >&2
      echo "  ../$(basename "$ROOT")-authoring/scripts/course_mode.sh authoring" >&2
      exit 1
    fi
    mkdir -p "$(dirname "$MODE_FILE")"
    printf 'authoring\n' > "$MODE_FILE"
    deny off
    echo "mode: AUTHORING — spoiler guard stands down and the ${#CANONICAL_DENY[@]} canonical deny rules are removed in this worktree; the always-on rules stay."
    echo "Remember: scripts/course_mode.sh study  before committing settings or shipping."
    ;;
  study)
    rm -f "$MODE_FILE"
    deny on
    echo "mode: STUDY — spoiler guard active; the ${#CANONICAL_DENY[@]} canonical deny rules are in place."
    ;;
  status)
    if [ -f "$MODE_FILE" ] && grep -q authoring "$MODE_FILE" 2>/dev/null; then
      why="$(authoring_refusal)"
      if [ -n "$why" ]; then
        echo "mode: AUTHORING file present but IGNORED by the hook — $why"
      else
        echo "mode: AUTHORING"
      fi
    else
      echo "mode: STUDY"
    fi
    deny show
    # Layer 2 is off whatever the mode says if any settings layer sets
    # disableAllHooks, or if the hook is not run through bash (then a hook
    # file without its execute bit fails open).
    python3 - "$SETTINGS" "$ROOT/.claude/settings.local.json" \
      "$HOME/.claude/settings.json" "$HOME/.claude/settings.local.json" \
      ${CLAUDE_CONFIG_DIR:+"$CLAUDE_CONFIG_DIR/settings.json" "$CLAUDE_CONFIG_DIR/settings.local.json"} <<'PY'
import json, sys
want = 'bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/spoiler-guard.sh"'
for i, path in enumerate(sys.argv[1:]):
    try:
        with open(path) as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        continue
    if cfg.get("disableAllHooks"):
        print(f"WARNING: {path} sets disableAllHooks: the spoiler guard does not run")
    if i == 0:
        cmds = [h.get("command") for m in cfg.get("hooks", {}).get("PreToolUse", [])
                for h in m.get("hooks", [])]
        if want not in cmds:
            print(f"WARNING: {path} does not run the spoiler guard as: {want}")
PY
    ;;
esac
