#!/usr/bin/env bash
# challenge_gate.sh — the gate of a solo challenge module, Q19–Q33 (QPLAN §31.1, §31.5;
# spec §2.3.8; DELTAS Δ402). The library is scripts/dvl/challenge.py, whose docstring
# lists the eight checks, the manifest and the exit codes; this file only runs it.
#   scripts/challenge_gate.sh <ID> [--json] [--no-record]
#   scripts/challenge_gate.sh --abandon <ID> [--no-record]
# It writes the gradebook's `challenge` row (CORE.md) and nothing else.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -B "$here/dvl/challenge.py" "$@"
