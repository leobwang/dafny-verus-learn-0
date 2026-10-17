#!/usr/bin/env bash
# test_hooks.sh — replay tests/hooks/*.jsonl through .claude/hooks/spoiler-guard.sh,
# then check that scripts/course_mode.sh moves the two layers as documented,
# that review-due.sh prints its banners, and that the committed settings carry
# the canonical deny rules (spec §7.5).
#
# Fixtures. tests/hooks/must_block.jsonl and must_allow.jsonl are generated
# from tests/hooks/templates/ by scripts/gen_hook_fixtures.py; this suite
# fails if they drift. A line is one PreToolUse hook input plus a "why";
# "@ROOT@" stands for the fake checkout, "@HOME@" for a fake home, "@SID@" and
# "@SLUG@" for the session this harness injects (session_id and
# transcript_path, unless the line says "nosession": true), "@UID@" for id -u,
# "@LANE@" for a throwaway author lane scratch directory this harness creates
# (/tmp/dvl0-dvhooks-*, holding one decoy file, removed on exit: a shell line's
# file operand is checked only when it exists, so the fixture must not depend
# on a real lane's scratch, which the lanes remove; DV5d).
# A line with "raw" feeds that string verbatim. "contract": true puts the
# seeded contract allowlist in place (it also names given, frozen and solo
# paths, to prove rules 2f and 2s ignore them); otherwise the allowlist is
# empty. "no_registry": true moves MODULES.toml away for that line.
#
# Fake roots. The hook runs against throwaway checkouts built by
# gen_hook_fixtures.py --fake-root: decoy reference files only, never real
# material; scratch probes that import references and ones that don't;
# symlinks into the reference tree and onto exercise and given files. Each
# pass gets its own fake home (--fake-home) with decoy session state. Nothing
# here reads this checkout's .claude/state, so an authoring worktree tests
# exactly like the learner checkout.
#
# Passes:
#   fixtures      the generated files equal the templates' expansion
#   study         no mode file: must_block exits 2 from the rule its why
#                 names ("rule 1d: …" → stderr has "(rule 1d)"); must_allow 0
#   study, no jq  the same through the jq-free fallback parser
#   author-only   (study mode) each author-only option of the real tools
#                 (AUTHOR_OPTS below; scripts/<tool>'s own argparse option
#                 list): every spelling argparse accepts (the option and each
#                 unique prefix, with python3 in front too) is refused by the
#                 rule named there, and every other option of the tool
#                 passes; a listed option the tool no longer has fails, and so
#                 does a tool whose option list is empty
#   study root    (D20) a fake checkout under /tmp/dvl0-study-dvhooks-*: a
#                 Read of its CORE.md, a shell in it and a Read under its
#                 DVL_SCRATCH pass, a lane's scratch stays refused; a fake
#                 checkout under the lane dir (@LANE@/clone) is refused by
#                 rule 1 with a message that never says "cd back to" itself
#   stand-down    mode=authoring in a linked worktree: must_block exits 0
#   armed         mode=authoring outside git, in a primary worktree, or on a
#                 leobwang-* branch: the file is ignored, must_block still 2
# course_mode.sh: refusals outside git, in a primary worktree and on a
# learner branch (exit 1, nothing written); canonical-first merge; exact
# removal; the always-on rules untouched both ways; idempotence; status.
# review-due.sh: due items, the stale-allowlist and authoring banners, and it
# never fails. Settings: the committed settings.json carries the canonical and
# always-on rules; the canonical strings agree across course_mode.sh,
# CLAUDE.md and (once it exists) scripts/ci.sh; the hook header, CLAUDE.md's
# access matrix and CORE.md's MAY NOT list name the whole reference set (the
# calibration fixtures included, which have no deny rule); both hooks run
# through bash; the matcher covers every tool the hook checks; no
# disableAllHooks; the IDE pins.
#
# Usage: scripts/test_hooks.sh [-v]    (-v also lists passing cases)
#        SPOILER_GUARD_HOOK=/path/to/copy.sh scripts/test_hooks.sh
#          replays the fixtures against a candidate hook instead of the live
#          one. The live hook guards every session in a checkout, so change a
#          copy and install it only when this suite is green.
# Needs jq (to unpack the fixtures), git and python3.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="${SPOILER_GUARD_HOOK:-$ROOT/.claude/hooks/spoiler-guard.sh}"
BANNER="$ROOT/.claude/hooks/review-due.sh"
GEN="$ROOT/scripts/gen_hook_fixtures.py"
FIX="$ROOT/tests/hooks"
[ -f "$HOOK" ] || { echo "test_hooks: no hook at $HOOK" >&2; exit 2; }
VERBOSE=0
[ "${1:-}" = "-v" ] && VERBOSE=1
command -v jq >/dev/null 2>&1 || { echo "test_hooks: jq is required to unpack the fixtures" >&2; exit 2; }

# Throwaway roots live under /tmp itself, never under a Claude Code scratch
# root (/tmp/claude-<uid>/), which rule 1e treats as other sessions' state.
TMP="$(mktemp -d /tmp/dvl0-hooktest.XXXXXX)"
LANE="$(mktemp -d /tmp/dvl0-dvhooks-XXXXXX)"
trap 'rm -rf "$TMP" "$LANE"' EXIT
mkdir -p "$LANE/crate/src"
printf '// decoy lane scratch file (test_hooks.sh); not course material\n' > "$LANE/crate/src/lib.rs"
GIT=(git -c user.name=test-hooks -c user.email=test-hooks@localhost -c init.defaultBranch=main)
SID=11111111-2222-4333-8444-555555555555
UIDN="$(id -u)"

PASS=0
FAIL=0
ok()  { PASS=$((PASS + 1)); [ "$VERBOSE" = 0 ] || echo "  ok    $*"; }
bad() { FAIL=$((FAIL + 1)); echo "  FAIL  $*"; }
expect() {   # LABEL ACTUAL WANTED
  if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 — got $2, want $3"; fi
}
slug_of() { printf '%s' "$1" | sed 's/[^A-Za-z0-9]/-/g'; }

echo "== fixtures"
if python3 "$GEN" --check; then ok "[fixtures] generated files match the templates"
else bad "[fixtures] tests/hooks/*.jsonl drifted from tests/hooks/templates (run scripts/gen_hook_fixtures.py)"; fi
expect "[fixtures] must_block is non-empty" "$([ -s "$FIX/must_block.jsonl" ] && echo yes || echo no)" yes
expect "[fixtures] must_allow is non-empty" "$([ -s "$FIX/must_allow.jsonl" ] && echo yes || echo no)" yes

# fake DIR NAME — populate a fake checkout at DIR and a fake home for it.
fake() {
  mkdir -p "$1"
  python3 "$GEN" --fake-root "$1"
  python3 "$GEN" --fake-home "$TMP/home-$2" --slug="$(slug_of "$1")" --sid="$SID"
}

# replay FIXTURE ROOT HOME WANT LABEL [VAR=value...] — every case must exit
# WANT; a block must also come from the rule its "why" names.
replay() {
  local file="$1" root="$2" home="$3" want="$4" label="$5" why contract noreg input got rule slug
  shift 5
  slug="$(slug_of "$root")"
  while IFS=$'\t' read -r why contract noreg input; do
    if [ "$contract" = true ]; then
      cp "$root/tests/hooks/seeded-allowlist" "$root/.claude/state/contract-allowlist"
    else
      : > "$root/.claude/state/contract-allowlist"
    fi
    [ "$noreg" = true ] && mv "$root/MODULES.toml" "$root/MODULES.toml.off"
    set +e
    printf '%s' "$input" | env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CONFIG_DIR -u TMPDIR \
      -u SPOILER_GUARD_NO_JQ "$@" HOME="$home" CLAUDE_PROJECT_DIR="$root" \
      bash "$HOOK" >/dev/null 2>"$TMP/err"
    got=$?
    set -e
    [ "$noreg" = true ] && mv "$root/MODULES.toml.off" "$root/MODULES.toml"
    rule="$(printf '%s' "$why" | sed -n 's/^\(rule [0-9a-z]*\):.*/(\1)/p')"
    if [ "$got" = "$want" ] && [ "$want" = 2 ] && [ -n "$rule" ] && ! grep -qF "$rule" "$TMP/err"; then
      bad "[$label] blocked, but not by $rule — $why"
      sed 's/^/          /' "$TMP/err"
    elif [ "$got" = "$want" ]; then
      ok "[$label] $why"
    else
      bad "[$label] exit $got, want $want — $why"
      sed 's/^/          /' "$TMP/err"
    fi
  done < <(sed "s|@ROOT@|$root|g; s|@HOME@|$home|g; s|@SID@|$SID|g; s|@SLUG@|$slug|g; s|@UID@|$UIDN|g; s|@LANE@|$LANE|g" "$file" \
             | jq -r --arg sid "$SID" --arg tp "$home/.claude/projects/$slug/$SID.jsonl" '
                 (.why // "?") + "\t" + ((.contract // false) | tostring) + "\t"
                 + ((.no_registry // false) | tostring) + "\t"
                 + (if has("raw") then .raw
                    else (.nosession // false) as $ns
                       | del(.why, .contract, .no_registry, .nosession)
                       | (if $ns then . else {session_id: $sid, transcript_path: $tp} + . end)
                       | tojson end)')
}

echo "== spoiler-guard: study mode"
fake "$TMP/study" study
replay "$FIX/must_block.jsonl" "$TMP/study" "$TMP/home-study" 2 "block"
replay "$FIX/must_allow.jsonl" "$TMP/study" "$TMP/home-study" 0 "allow"

echo "== spoiler-guard: study mode, jq-free parser"
replay "$FIX/must_block.jsonl" "$TMP/study" "$TMP/home-study" 2 "block/no-jq" SPOILER_GUARD_NO_JQ=1
replay "$FIX/must_allow.jsonl" "$TMP/study" "$TMP/home-study" 0 "allow/no-jq" SPOILER_GUARD_NO_JQ=1

echo "== spoiler-guard: author-only options in every spelling argparse accepts"
# The final replay fixture may have a live contract. These independent
# option probes assume none; their verdict must not depend on fixture order.
: > "$TMP/study/.claude/state/contract-allowlist"
# TOOL OPTION RULE [VALUE]: the author-only options (spec §7.4, Δ85; the
# hook's RX_AUTHOR) and vaudit's --write, a write target (expected/ is 2f).
# The spellings come from the tool's own parser, so an option the hook does
# not know, a renamed one or a newly unique prefix fails here. A parser with
# allow_abbrev=False (test_corpus.py, mksandbox-run, dvl/bench.py) yields the
# full spelling only; the hook's refusal of their prefixes, and of the
# get_bench.sh front end and the fvh fixture recorder (a module, not an
# option), is in the must_block fixtures.
AUTHOR_OPTS='pins.py --update 1b
pins.py --ref 1b
vcheck --ref 1b
vaudit --ref 1b
specfreeze --pin 1b Q04
firsttry.py --empty-body 1b
test_corpus.py --update 1b
mksandbox-run --author 1b
mksandbox-run --attest 1b bench/local/q/card01/tasks/task.dfy
mksandbox-run --attest-rescan 1b
dvl/bench.py --pin 1b
dvl/bench.py --pin-pool 1b
vaudit --write 2f expected/Q04.audit'
# spellings TOOL OPTION LISTED → "spelling<TAB>kind" lines: kind "author" for
# each accepted spelling of OPTION, "other" for the tool's options that
# AUTHOR_OPTS does not list (LISTED); "gone" when OPTION is not in the
# parser, "empty" when no option was found.
spellings() { python3 - "$ROOT/scripts/$1" "$2" "$3" <<'PY'
import re, sys
try:
    src = open(sys.argv[1], encoding="utf-8").read()
except OSError:
    print("-\tempty"); sys.exit(0)
m = re.search(r"ArgumentParser\(.*?\.parse_args\(", src, re.S)
region = m.group(0) if m else ""
opts = sorted(set(re.findall(r"""["'](--[a-z][a-z0-9-]*)["']""", region)))
want = sys.argv[2]
if not opts:
    print("-\tempty"); sys.exit(0)
if want not in opts:
    print(f"{want}\tgone"); sys.exit(0)
abbrev = "allow_abbrev=False" not in region
for k in range(3, len(want) + 1):
    p = want[:k]
    if p == want or (abbrev and [o for o in opts if o.startswith(p)] == [want]):
        print(f"{p}\tauthor")
listed = set(sys.argv[3].split())
for o in opts:
    if o not in listed:
        print(f"{o}\tother")
PY
}
# probe CMD → "exit<TAB>stderr" from the hook in the study root.
probe() {
  local input got
  input="$(jq -cn --arg c "$1" --arg r "$TMP/study" --arg sid "$SID" \
    --arg tp "$TMP/home-study/.claude/projects/$(slug_of "$TMP/study")/$SID.jsonl" \
    '{tool_name: "Bash", tool_input: {command: $c}, cwd: $r, session_id: $sid, transcript_path: $tp}')"
  set +e
  printf '%s' "$input" | env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CONFIG_DIR -u TMPDIR -u SPOILER_GUARD_NO_JQ \
    HOME="$TMP/home-study" CLAUDE_PROJECT_DIR="$TMP/study" bash "$HOOK" >/dev/null 2>"$TMP/err"
  got=$?
  set -e
  printf '%s\t%s' "$got" "$(tr '\n' ' ' < "$TMP/err")"
}
declare -A OTHER_SEEN=() LISTED=()
while read -r tool opt rule value; do LISTED[$tool]+=" $opt"; done <<< "$AUTHOR_OPTS"
while read -r tool opt rule value; do
  [ -n "$tool" ] || continue
  n=0
  while IFS=$'\t' read -r sp kind; do
    case "$kind" in
      empty) bad "[author-only] scripts/$tool: no argparse option found (a missing or unparsable tool)"; continue ;;
      gone)  bad "[author-only] scripts/$tool no longer has $opt: update RX_AUTHOR, the hook header and AUTHOR_OPTS"; continue ;;
    esac
    arg="${value:-Q04}"
    if [ "$kind" = author ]; then
      n=$((n + 1))
      forms=("scripts/$tool $sp $arg" "python3 scripts/$tool $arg $sp${value:+ $value}")
      [ -n "$value" ] && forms=("scripts/$tool $sp $value Q04" "python3 scripts/$tool $sp=$value Q04")
      [ "$tool" = firsttry.py ] && forms+=("scripts/firsttry.sh Q04 $sp")
      for f in "${forms[@]}"; do
        r="$(probe "$f")"
        if [ "${r%%$'\t'*}" = 2 ] && printf '%s' "$r" | grep -qF "(rule $rule)"; then ok "[author-only] refused (rule $rule): $f"
        else bad "[author-only] '$f' — want exit 2 from rule $rule, got: ${r:0:200}"; fi
      done
    elif [ -z "${OTHER_SEEN[$tool$sp]:-}" ]; then
      OTHER_SEEN[$tool$sp]=1
      f="scripts/$tool $sp Q04"
      r="$(probe "$f")"
      if [ "${r%%$'\t'*}" = 0 ]; then ok "[author-only] learner option passes: $f"
      else bad "[author-only] '$f' is not author-only, yet the hook refuses it: ${r:0:200}"; fi
    fi
  done < <(spellings "$tool" "$opt" "${LISTED[$tool]}")
  case "$(spellings "$tool" "$opt" "${LISTED[$tool]}" | cut -f2 | sort -u | tr '\n' ' ')" in
    *empty*|*gone*) ;;
    *) [ "$n" -gt 0 ] || bad "[author-only] scripts/$tool $opt: no accepted spelling was tested" ;;
  esac
done <<< "$AUTHOR_OPTS"

echo "== spoiler-guard: a study root beside the lane-scratch tripwire, and a checkout inside it (D20)"
# Rule 1 refuses an author lane's scratch, /tmp/dvl0-dv…/ (Δ214, a tripwire). A
# study clone lives under /tmp/dvl0-study-…/ (the user's decision D20), which the
# pattern does not match: a session there reads its skill and runs its shell. A
# checkout inside the tripwire is refused, and the message must not send the
# session back into the directory it refuses. Each case under both parsers.
STUDYR="$(mktemp -d /tmp/dvl0-study-dvhooks-XXXXXX)"
trap 'rm -rf "$TMP" "$LANE" "$STUDYR"' EXIT
fake "$STUDYR/clone" studyroot
fake "$LANE/clone" lanecheckout
for r in "$STUDYR/clone" "$LANE/clone"; do
  mkdir -p "$r/.claude/skills/instructor"
  printf '# decoy skill core (test_hooks.sh); not course material\n' > "$r/.claude/skills/instructor/CORE.md"
done
# at ROOT HOME CWD TOOL INPUT-JSON [VAR=value...] → "exit<TAB>stderr" from the hook
at() {
  local root="$1" home="$2" cwd="$3" tool="$4" tin="$5" input got
  shift 5
  input="$(jq -cn --arg t "$tool" --argjson i "$tin" --arg c "$cwd" --arg sid "$SID" \
    --arg tp "$home/.claude/projects/$(slug_of "$root")/$SID.jsonl" \
    '{tool_name: $t, tool_input: $i, cwd: $c, session_id: $sid, transcript_path: $tp}')"
  set +e
  printf '%s' "$input" | env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CONFIG_DIR -u TMPDIR -u SPOILER_GUARD_NO_JQ \
    "$@" HOME="$home" CLAUDE_PROJECT_DIR="$root" bash "$HOOK" >/dev/null 2>"$TMP/err"
  got=$?
  set -e
  printf '%s\t%s' "$got" "$(tr '\n' ' ' < "$TMP/err")"
}
S="$STUDYR/clone" SH="$TMP/home-studyroot" L="$LANE/clone" LH="$TMP/home-lanecheckout"
for parser in jq no-jq; do
  pv=(); [ "$parser" = no-jq ] && pv=(SPOILER_GUARD_NO_JQ=1)
  r="$(at "$S" "$SH" "$S" Read "{\"file_path\": \"$S/.claude/skills/instructor/CORE.md\"}" "${pv[@]}")"
  expect "[study-root/$parser] a Read of the study clone's CORE.md passes" "${r%%$'\t'*}" 0
  r="$(at "$S" "$SH" "$S" Bash '{"command": "ls .claude/skills/instructor"}' "${pv[@]}")"
  expect "[study-root/$parser] a Bash call whose shell sits in the study clone passes" "${r%%$'\t'*}" 0
  r="$(at "$S" "$SH" "$S" Read "{\"file_path\": \"$STUDYR/dvl/runs/x.log\"}" "${pv[@]}")"
  expect "[study-root/$parser] a Read under the study root's DVL_SCRATCH passes" "${r%%$'\t'*}" 0
  r="$(at "$S" "$SH" "$S" Read "{\"file_path\": \"$LANE/crate/src/lib.rs\"}" "${pv[@]}")"
  if [ "${r%%$'\t'*}" = 2 ] && printf '%s' "$r" | grep -qF "(rule 1)"; then
    ok "[study-root/$parser] a lane's scratch stays refused from a study clone (rule 1)"
  else bad "[study-root/$parser] a Read of $LANE/crate/src/lib.rs — want exit 2 from rule 1, got: ${r:0:200}"; fi
  r="$(at "$S" "$SH" "$S/Solutions" Bash '{"command": "ls"}' "${pv[@]}")"
  if [ "${r%%$'\t'*}" = 2 ] && printf '%s' "$r" | grep -qF "cd back to $S first"; then
    ok "[study-root/$parser] a shell inside the clone's reference tree is sent back to the root (rule 1)"
  else bad "[study-root/$parser] a shell in $S/Solutions — want exit 2 and 'cd back to $S first', got: ${r:0:200}"; fi
  r="$(at "$L" "$LH" "$L" Bash '{"command": "ls"}' "${pv[@]}")"
  if [ "${r%%$'\t'*}" = 2 ] && printf '%s' "$r" | grep -qF "(rule 1)" \
     && ! printf '%s' "$r" | grep -qF "cd back to $L" && printf '%s' "$r" | grep -qF "checkout outside"; then
    ok "[study-root/$parser] a checkout under a lane's scratch is refused without 'cd back to' itself (rule 1)"
  else bad "[study-root/$parser] a shell in the checkout $L — want exit 2 from rule 1 and no 'cd back to $L', got: ${r:0:240}"; fi
  r="$(at "$L" "$LH" "$L" Read "{\"file_path\": \"$L/.claude/skills/instructor/CORE.md\"}" "${pv[@]}")"
  if [ "${r%%$'\t'*}" = 2 ] && printf '%s' "$r" | grep -qF "(rule 1)"; then
    ok "[study-root/$parser] a Read of CORE.md in a checkout under a lane's scratch is refused (rule 1)"
  else bad "[study-root/$parser] a Read of $L/.claude/skills/instructor/CORE.md — want exit 2 from rule 1, got: ${r:0:200}"; fi
done

echo "== spoiler-guard: authoring mode stands down in a linked worktree"
"${GIT[@]}" init -q "$TMP/repo"
"${GIT[@]}" -C "$TMP/repo" commit -q --allow-empty -m init
"${GIT[@]}" -C "$TMP/repo" worktree add -q -b authoring "$TMP/authoring"
fake "$TMP/authoring" authoring
printf 'authoring\n' > "$TMP/authoring/.claude/state/mode"
replay "$FIX/must_block.jsonl" "$TMP/authoring" "$TMP/home-authoring" 0 "stand-down"

echo "== spoiler-guard: authoring mode file ignored outside git"
fake "$TMP/nogit" nogit
printf 'authoring\n' > "$TMP/nogit/.claude/state/mode"
replay "$FIX/must_block.jsonl" "$TMP/nogit" "$TMP/home-nogit" 2 "armed/no-git" GIT_CEILING_DIRECTORIES="$TMP"

echo "== spoiler-guard: authoring mode file ignored in a primary worktree"
"${GIT[@]}" init -q "$TMP/primary"
fake "$TMP/primary" primary
printf 'authoring\n' > "$TMP/primary/.claude/state/mode"
replay "$FIX/must_block.jsonl" "$TMP/primary" "$TMP/home-primary" 2 "armed/primary"

echo "== spoiler-guard: authoring mode file ignored on a leobwang-* branch"
"${GIT[@]}" -C "$TMP/repo" worktree add -q -b leobwang-test "$TMP/learner"
fake "$TMP/learner" learner
printf 'authoring\n' > "$TMP/learner/.claude/state/mode"
replay "$FIX/must_block.jsonl" "$TMP/learner" "$TMP/home-learner" 2 "armed/leobwang"

echo "== course_mode.sh"
CANON='["Read(./Solutions/**)", "Read(./paper/solutions/**)", "Read(./tests/instructor/leak_patterns/**)", "Read(~/.cache/dafny-verus-learn-0/**)"]'
ALWAYS='["Read(~/.claude/projects/*/*.jsonl)", "Read(~/.claude/file-history/**)", "Read(~/.claude/history.jsonl)", "Skill(skill:local-assistant)"]'
# The settings a mode test starts from: one rule of the user's own, three of
# the canonical rules, and the always-on rules.
START="$(python3 -c 'import json,sys; c=json.loads(sys.argv[1]); a=json.loads(sys.argv[2]); print(json.dumps(["Bash(rm -rf /)"] + c[:3] + a))' "$CANON" "$ALWAYS")"
mode_tree() {   # DIR — course_mode.sh plus a settings.json holding START
  mkdir -p "$1/scripts" "$1/.claude"
  install -m 755 "$ROOT/scripts/course_mode.sh" "$1/scripts/course_mode.sh"
  python3 -c 'import json,sys; print(json.dumps({"permissions": {"deny": json.loads(sys.argv[1])}}, indent=2))' "$START" \
    > "$1/.claude/settings.json"
}
deny_of() { python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1]))["permissions"]["deny"]))' "$1/.claude/settings.json"; }
refuses() {   # DIR [VAR=value...] — authoring must exit 1, write no mode file and leave the deny list alone
  local d="$1" got before
  shift
  before="$(deny_of "$d")"
  rm -f "$d/.claude/state/mode"
  if env "$@" "$d/scripts/course_mode.sh" authoring >/dev/null 2>"$TMP/mode-err"; then got=0; else got=$?; fi
  printf '%s|%s|%s' "$got" "$([ -e "$d/.claude/state/mode" ] && echo mode || echo none)" \
    "$([ "$(deny_of "$d")" = "$before" ] && echo same || echo changed)"
}
mode_tree "$TMP/primary"
expect "[course_mode] authoring refused in the primary worktree (exit 1, no mode file, deny list untouched)" "$(refuses "$TMP/primary")" "1|none|same"
expect "[course_mode] the refusal prints the worktree recipe" "$(grep -c 'worktree add .*-b authoring origin/main' "$TMP/mode-err")" 1
# D26: once the shipped branch basic exists, the recipe starts from it (origin/ first)
"${GIT[@]}" init -q "$TMP/primary-basic"
"${GIT[@]}" -C "$TMP/primary-basic" commit -q --allow-empty -m init
"${GIT[@]}" -C "$TMP/primary-basic" branch basic
mode_tree "$TMP/primary-basic"
refuses "$TMP/primary-basic" >/dev/null
expect "[course_mode] the recipe starts from basic once it exists" "$(grep -c 'worktree add .*-b authoring basic$' "$TMP/mode-err")" 1
"${GIT[@]}" -C "$TMP/primary-basic" update-ref refs/remotes/origin/basic HEAD
refuses "$TMP/primary-basic" >/dev/null
expect "[course_mode] the recipe starts from origin/basic when the remote has it" "$(grep -c 'worktree add .*-b authoring origin/basic$' "$TMP/mode-err")" 1
mode_tree "$TMP/learner"
expect "[course_mode] authoring refused on a leobwang-* branch" "$(refuses "$TMP/learner")" "1|none|same"
mode_tree "$TMP/nogit"
expect "[course_mode] authoring refused outside git" "$(refuses "$TMP/nogit" GIT_CEILING_DIRECTORIES="$TMP")" "1|none|same"

mode_tree "$TMP/authoring"
rm -f "$TMP/authoring/.claude/state/mode"
"$TMP/authoring/scripts/course_mode.sh" study >/dev/null
WANT_STUDY="$(python3 -c 'import json,sys; print(json.dumps(json.loads(sys.argv[1]) + ["Bash(rm -rf /)"] + json.loads(sys.argv[2])))' "$CANON" "$ALWAYS")"
WANT_AUTH="$(python3 -c 'import json,sys; print(json.dumps(["Bash(rm -rf /)"] + json.loads(sys.argv[1])))' "$ALWAYS")"
expect "[course_mode] study merges the canonical rules first, ahead of the others" "$(deny_of "$TMP/authoring")" "$WANT_STUDY"
cp "$TMP/authoring/.claude/settings.json" "$TMP/study-settings.json"
"$TMP/authoring/scripts/course_mode.sh" study >/dev/null
expect "[course_mode] study is idempotent (byte-identical settings)" "$(cmp -s "$TMP/study-settings.json" "$TMP/authoring/.claude/settings.json" && echo same || echo differs)" same
"$TMP/authoring/scripts/course_mode.sh" authoring >/dev/null
expect "[course_mode] authoring removes exactly the canonical rules (always-on rules stay)" "$(deny_of "$TMP/authoring")" "$WANT_AUTH"
expect "[course_mode] authoring writes the mode file" "$(cat "$TMP/authoring/.claude/state/mode")" authoring
"$TMP/authoring/scripts/course_mode.sh" authoring >/dev/null
expect "[course_mode] authoring is idempotent" "$(deny_of "$TMP/authoring")" "$WANT_AUTH"
# first_line CMD... — the first line of CMD's output. The whole output is
# captured first: piping into head would close the pipe early, and the
# status command's Python would die of SIGPIPE (BrokenPipeError).
first_line() { local out; out="$("$@")"; printf '%s\n' "$out" | sed -n 1p; }
expect "[course_mode] status reports AUTHORING in a linked worktree" "$(first_line "$TMP/authoring/scripts/course_mode.sh" status)" "mode: AUTHORING"
"$TMP/authoring/scripts/course_mode.sh" study >/dev/null
expect "[course_mode] study removes the mode file" "$([ -e "$TMP/authoring/.claude/state/mode" ] && echo present || echo absent)" absent
expect "[course_mode] study restores the canonical rules and keeps the always-on ones" "$(deny_of "$TMP/authoring")" "$WANT_STUDY"
mkdir -p "$TMP/primary/.claude/state"; printf 'authoring\n' > "$TMP/primary/.claude/state/mode"
expect "[course_mode] status says a mode file in the primary worktree is IGNORED" \
  "$(first_line "$TMP/primary/scripts/course_mode.sh" status | grep -c 'IGNORED by the hook')" 1
expect "[course_mode] status names a missing canonical rule" "$("$TMP/primary/scripts/course_mode.sh" status | grep -c 'missing canonical rules')" 1
python3 - "$TMP/primary/.claude/settings.json" <<'PY'
import json, sys
p = sys.argv[1]; d = json.load(open(p))
d["permissions"]["deny"] = [r for r in d["permissions"]["deny"] if "history.jsonl" not in r]
json.dump(d, open(p, "w"), indent=2)
PY
expect "[course_mode] status warns when an always-on rule is missing" "$("$TMP/primary/scripts/course_mode.sh" status | grep -c 'missing always-on rules')" 1
if "$TMP/primary/scripts/course_mode.sh" bogus >/dev/null 2>&1; then got=0; else got=$?; fi
expect "[course_mode] an unknown mode is a usage error" "$got" 2

echo "== review-due.sh (SessionStart)"
banner() { CLAUDE_PROJECT_DIR="$1" bash "$BANNER" | grep -c "$2" || true; }
mkdir -p "$TMP/session/.claude/state" "$TMP/session/instructor"
printf -- '- Q04 carry due: 2000-01-01\n- Q05 frame due: 2999-01-01\n' > "$TMP/session/instructor/ledger.md"
expect "[banner] a past-due ledger item is counted" "$(CLAUDE_PROJECT_DIR="$TMP/session" bash "$BANNER" | grep -c 'Review queue: 1 item(s) due')" 1
printf -- '- Q05 frame due: 2999-01-01\n' > "$TMP/session/instructor/ledger.md"
expect "[banner] future items are not due" "$(banner "$TMP/session" 'Review queue')" 0
printf 'dafny/Q/Q04_Proofs/core/Q04_AgentRepair.dfy\n' > "$TMP/session/.claude/state/contract-allowlist"
expect "[banner] a fresh allowlist is not flagged" "$(banner "$TMP/session" 'Contract allowlist')" 0
touch -d '2 days ago' "$TMP/session/.claude/state/contract-allowlist"
expect "[banner] a day-old non-empty allowlist is flagged" "$(banner "$TMP/session" 'Contract allowlist')" 1
: > "$TMP/session/.claude/state/contract-allowlist"
touch -d '2 days ago' "$TMP/session/.claude/state/contract-allowlist"
expect "[banner] an emptied allowlist is not flagged" "$(banner "$TMP/session" 'Contract allowlist')" 0
expect "[banner] no mode file, no authoring banner" "$(banner "$TMP/session" 'AUTHORING')" 0
printf 'authoring\n' > "$TMP/session/.claude/state/mode"
expect "[banner] an authoring mode file is bannered" "$(banner "$TMP/session" 'AUTHORING')" 1
if CLAUDE_PROJECT_DIR="$TMP/does-not-exist" bash "$BANNER" >/dev/null 2>&1; then got=0; else got=$?; fi
expect "[banner] never fails, even on a missing project dir" "$got" 0
mkdir -p "$TMP/garbled/instructor"; printf '\377\376 due: 20x-01-01\n' > "$TMP/garbled/instructor/ledger.md"
if CLAUDE_PROJECT_DIR="$TMP/garbled" bash "$BANNER" >/dev/null 2>&1; then got=0; else got=$?; fi
expect "[banner] never fails on a garbled ledger" "$got" 0

echo "== settings.json and the IDE pins"
# The committed blob (HEAD) when settings.json is tracked; an authoring
# worktree's own working copy lacks the canonical rules by design
# (course_mode.sh moved them), and scripts/ci.sh checks the checked-out tree.
has_rules() { python3 -c 'import json,sys; d=json.load(sys.stdin)["permissions"]["deny"]; print(all(r in d for r in json.loads(sys.argv[1])))' "$1"; }
if git -C "$ROOT" cat-file -e HEAD:.claude/settings.json 2>/dev/null; then
  COMMITTED="$(git -C "$ROOT" show HEAD:.claude/settings.json)"; WHERE="committed (HEAD)"
else
  COMMITTED="$(cat "$ROOT/.claude/settings.json")"; WHERE="working-tree (not yet committed)"
fi
expect "[settings] $WHERE settings.json carries the canonical rules" "$(printf '%s' "$COMMITTED" | has_rules "$CANON")" True
expect "[settings] $WHERE settings.json carries the always-on rules" "$(printf '%s' "$COMMITTED" | has_rules "$ALWAYS")" True
if grep -qs authoring "$ROOT/.claude/state/mode"; then
  echo "  skip  working-tree settings.json canonical rules (this checkout is mid-authoring)"
else
  expect "[settings] working-tree settings.json carries the canonical rules" "$(has_rules "$CANON" < "$ROOT/.claude/settings.json")" True
fi
# Spec §7.2: the four canonical strings appear in four places that must agree
# (course_mode.sh, the CI study-mode check, CLAUDE.md, this suite).
canon_in() {   # FILE — 1 when FILE carries every canonical string literally, else the missing ones
  python3 - "$1" "$CANON" <<'PY'
import json, sys
text = open(sys.argv[1], encoding="utf-8").read()
missing = [r for r in json.loads(sys.argv[2]) if r not in text]
print(missing or 1)
PY
}
expect "[settings] CLAUDE.md names every canonical rule literally" "$(canon_in "$ROOT/CLAUDE.md")" 1
if [ -f "$ROOT/scripts/ci.sh" ]; then
  expect "[settings] scripts/ci.sh's study-mode check names every canonical rule" "$(canon_in "$ROOT/scripts/ci.sh")" 1
else
  echo "  skip  scripts/ci.sh canonical rules (no ci.sh yet; DV1c builds it, Δ67)"
fi
# The reference set, as rule 1 of the hook defines it, named alike in the
# hook header, CLAUDE.md's access matrix and CORE.md's MAY NOT list. The
# calibration fixtures have no deny rule, so these lists are where a reader
# learns they are reference-class.
REFSET='Solutions/ paper/solutions/ tests/instructor/leak_patterns/ tests/instructor/fixtures/ ~/.cache/dafny-verus-learn-0/'
for f in "$HOOK" "$ROOT/CLAUDE.md" "$ROOT/.claude/skills/instructor/CORE.md"; do
  missing=""
  for r in $REFSET; do grep -qF -- "$r" "$f" || missing+=" $r"; done
  expect "[settings] ${f#"$ROOT"/} names the whole reference set" "${missing:-none}" none
done
expect "[settings] course_mode.sh's CANONICAL_DENY is the canonical list" \
  "$(python3 - "$ROOT/scripts/course_mode.sh" "$CANON" <<'PY'
import json, re, sys
src = open(sys.argv[1]).read()
block = re.search(r"CANONICAL_DENY=\((.*?)\)\n", src, re.S).group(1)
print(re.findall(r'"([^"]+)"', block) == json.loads(sys.argv[2]))
PY
)" True
wiring() { python3 - "$ROOT/.claude/settings.json" "$1" <<'PY'
import json, re, sys
cfg = json.load(open(sys.argv[1]))
hooks = cfg.get("hooks", {})
want = {"PreToolUse": 'bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/spoiler-guard.sh"',
        "SessionStart": 'bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/review-due.sh"'}
cmds = {ev: [h.get("command", "") for m in hooks.get(ev, []) for h in m.get("hooks", [])] for ev in want}
ms = [m.get("matcher", "") for m in hooks.get("PreToolUse", [])
      if any(h.get("command") == want["PreToolUse"] for h in m.get("hooks", []))]
# Claude Code tests a regex matcher with JavaScript's RegExp.test (a search);
# the course's matcher is anchored, so re.search is the same test.
hit = lambda t: any(re.search(m, t) for m in ms)
covered = ["Read", "Grep", "Glob", "Bash", "PowerShell", "Monitor", "Workflow", "ScheduleWakeup",
           "mcp__firecrawl__firecrawl_parse", "Edit", "Write", "MultiEdit", "NotebookEdit",
           "LSP", "Skill", "WebFetch", "WebSearch", "mcp__vcheck__check", "mcp__dafny__verify",
           "mcp__dafny-lsp__verify_symbol", "mcp__verus__verify", "mcp__plugin_dafny-tools_dafny__verify",
           "mcp__plugin_course_vcheck__check", "mcp__plugin_x_verus-lsp__hover"]
left_alone = ["Agent", "TodoWrite", "mcp__claude_ai_Claude_Docs__read", "mcp__firecrawl__firecrawl_search"]
arg = sys.argv[2]
if arg == "commands":
    print(all(want[ev] in cmds[ev] for ev in want))
elif arg == "covered":
    print([t for t in covered if not hit(t)] or True)
elif arg == "left-alone":
    print([t for t in left_alone if hit(t)] or True)
elif arg == "timeout":
    print(all(h.get("timeout") == 15 for ev in want for m in hooks.get(ev, []) for h in m.get("hooks", [])))
elif arg == "session":
    print([m.get("matcher") for m in hooks.get("SessionStart", [])] == ["startup|resume|clear"])
else:
    print(cfg.get("disableAllHooks", False))
PY
}
expect "[settings] spoiler-guard.sh and review-due.sh run through bash (the mode bit cannot disarm them)" "$(wiring commands)" True
expect "[settings] the PreToolUse matcher covers every tool the hook checks" "$(wiring covered)" True
expect "[settings] the PreToolUse matcher leaves unrelated tools alone" "$(wiring left-alone)" True
expect "[settings] every hook has the 15 s timeout" "$(wiring timeout)" True
expect "[settings] the SessionStart matcher is startup|resume|clear" "$(wiring session)" True
expect "[settings] settings.json does not set disableAllHooks" "$(wiring disable)" False
expect "[settings] the hook header carries the honesty clause" "$(grep -c 'This is a tripwire, not a sandbox' "$HOOK")" 1
expect "[ide] .vscode/settings.json pins Dafny 4.11.0 and the pinned verus binary" "$(python3 - "$ROOT/.vscode/settings.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(d.get("dafny.version") == "4.11.0"
      and d.get("verus-analyzer.verus.verusBinary", "").endswith(".toolchain/verus-0.2026.09.27.3cf1832/verus-x86-linux/verus"))
PY
)" True

echo
echo "test_hooks: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
