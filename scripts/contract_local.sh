#!/usr/bin/env bash
# contract_local.sh: replay a module's contract under opencode and a local Qwen
# in a per-run container (DV4-PLAN §6), from the starting state the learner's
# /contract run had, and return a patch the learner reads before deciding
# whether to apply it. The patch is never applied.
#
#   scripts/contract_local.sh <ID> [--file <agentic path>] [--model <tag>] [--from <rev>]
#   scripts/contract_local.sh <ID> --available    can the replay run here? (exit 0, or 3
#                                                  and one line per reason)
#   scripts/contract_local.sh <ID> --dry-run      parse, validate, find the starting
#                                                  state, build and self-test the run;
#                                                  nothing runs
#
# Built at DV4 step 1b (the checks and the dry run) and step 3b (the live
# replay); scripts/dvl/contract_local.py holds the logic.
# Exit codes: 0 done, 1 a step failed, 2 usage, 3 refused (or deferred).
set -euo pipefail
exec python3 -B "$(dirname "${BASH_SOURCE[0]}")/dvl/contract_local.py" "$@"
