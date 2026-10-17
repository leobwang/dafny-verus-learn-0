#!/usr/bin/env bash
# get_bench.sh: fetch and check the course's benchmark sets (DV4-PLAN §7).
# A thin front end: the implementation and its usage are scripts/dvl/bench.py.
#
#   scripts/get_bench.sh SET...            fetch the pinned commit, normalize, verify, install
#   scripts/get_bench.sh --all             every set in bench/manifest.toml
#   scripts/get_bench.sh --check [SET...]  offline: installed digests, licence and notice files
#   scripts/get_bench.sh --list            sets, licences, modes, install state
#   scripts/get_bench.sh --validate SET [--only NAME...] [--sample N --seed S]
#                        [--workers N --mem-gb SHARE] [--restart]
#                                          re-validate on the course pins (one solver job at a
#                                          time by default; resumable, stoppable)
#   scripts/get_bench.sh --members SET --lab LAB [--seed S]
#                                          the members LAB may draw from SET's pinned pool: the
#                                          pool less the tasks another lab's [[draw]] took (D30),
#                                          sorted or in the seeded order (Lab 1: --lab Q12)
#   scripts/get_bench.sh --pin-pool SET... author-only: record a finished validation's pool in
#                                          bench/public/POOLS.toml
#   scripts/get_bench.sh --pin SET...      author-only (Δ103; guard rule 1b)
#
# Exit codes: 0 done, 1 a step failed, 2 usage, 3 refused.
set -euo pipefail
exec python3 -B "$(dirname "${BASH_SOURCE[0]}")/dvl/bench.py" "$@"
