#!/usr/bin/env bash
# avoid.sh — the disjointness gate between the Q and R tracks (spec §2.7, design §9,
# PLAN.md §5.5). The implementation is scripts/avoid/avoid.py (its docstring holds the
# whole contract); the inputs are scripts/avoid.curated, scripts/avoid.waivers.tsv and
# scripts/avoid/owners.toml. scripts/ci.sh's static job runs it.
# Usage: scripts/avoid.sh [--track Q|R|both] [--json] [--list-sources] [--extra-r PATH]...
# Exit: 0 clean, 1 an unwaived hit or a stale waiver, 2 a malformed input, 3 usage.
exec python3 -B "$(dirname "${BASH_SOURCE[0]}")/avoid/avoid.py" "$@"
