#!/usr/bin/env bash
# review-due.sh — SessionStart hook (spec §7.3). Banners, each printed only
# when it applies:
#   - the count of due Leitner review items in instructor/ledger.md. Ledger
#     entries carry "due: YYYY-MM-DD"; an item is due when its date is <= today;
#   - a contract allowlist that is non-empty and older than a day: some
#     /contract session never closed out, and its edit unlock (and its block
#     on instructor/ writes, rule 2c) is still live;
#   - an authoring mode file, so a stood-down guard is never silent.
# This hook must never fail or block a session: it always exits 0.

{
  ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
  LEDGER="$ROOT/instructor/ledger.md"
  ALLOWLIST="$ROOT/.claude/state/contract-allowlist"
  MODE_FILE="$ROOT/.claude/state/mode"

  if [ -f "$LEDGER" ]; then
    TODAY="$(date +%Y-%m-%d)"
    N="$(grep -o 'due: [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' "$LEDGER" 2>/dev/null \
        | sed 's/^due: //' \
        | awk -v t="$TODAY" '($0 "") <= t { n++ } END { print n + 0 }')"
    if [ -n "$N" ] && [ "$N" -gt 0 ] 2>/dev/null; then
      echo "Review queue: $N item(s) due — run /review"
    fi
  fi

  if [ -f "$ALLOWLIST" ] && grep -q '[^[:space:]]' "$ALLOWLIST" 2>/dev/null \
     && [ -n "$(find "$ALLOWLIST" -mmin +1440 2>/dev/null)" ]; then
    N="$(grep -c '[^[:space:]]' "$ALLOWLIST" 2>/dev/null)"
    echo "Contract allowlist: $N path(s) unlocked for editing for over a day — a /contract session never closed out, and instructor/ writes stay blocked while it is non-empty. Empty .claude/state/contract-allowlist unless that contract is still in progress."
  fi

  if [ -f "$MODE_FILE" ] && grep -q authoring "$MODE_FILE" 2>/dev/null; then
    echo "AUTHORING mode file present — the spoiler guard stands down only in a linked authoring worktree off the learner branch; elsewhere the file is ignored (scripts/course_mode.sh status)."
  fi
} 2>/dev/null

exit 0
