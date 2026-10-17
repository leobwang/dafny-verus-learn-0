#!/usr/bin/env bash
# firsttry.sh — the prediction-slot gate, exit scorer, hollow lint and empty-body
# gate (spec §3.8.5). The implementation is scripts/firsttry.py; this is the name
# the course documents use (README, CORE.md, the skills, the rubrics).
# Usage: scripts/firsttry.sh <ID> [--check | --report [--strict] | --record | --exit
#        | --lint-hollow | --empty-body]   (or --lint-hollow --all)
exec python3 "$(dirname "${BASH_SOURCE[0]}")/firsttry.py" "$@"
