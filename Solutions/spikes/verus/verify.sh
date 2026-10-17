#!/usr/bin/env bash
# Verify the BigNat L1-L4 spike (+ qg_bignat_x extras) on the pinned Verus (DV0 reference material).
#
# Usage: verify.sh [--seed N] [--rlimit R] [--out DIR] [--json] [--no-cheating] [--cargo]
#   default        direct chain: one `verus` call per crate, each importing the exported
#                  metadata (.vir) of EVERY crate below it (transitive imports are required)
#                  and the rlib of the crate directly below it
#   --cargo        `cargo verus verify --workspace` on this directory's own workspace
#                  (fetches vstd from crates.io on first use; also verifies vstd itself)
#   --seed N       adds --smt-option smt.random_seed=N
#   --rlimit R     Verus --rlimit (default 2 = Z3 rlimit 6,000,000 per query)
#   --out DIR      where .vir/.rlib (and JSON with --json) go (default target/vir)
#   --json         adds --output-json --time and writes DIR/<crate>.json
#   --no-cheating  adds --no-cheating (rejects assume, admit, external_body, assume_specification)
# Exit status: 0 iff every crate verified.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
VD="$REPO/.toolchain/verus-0.2026.09.27.3cf1832/verus-x86-linux"
VERUS="$VD/verus"
RUST_TC="1.98.1-x86_64-unknown-linux-gnu"
CRATES=(qg_bignat_l1 qg_bignat_l2 qg_bignat_l3 qg_bignat_l4 qg_bignat_x)
RLIMIT=2
SEED=""
OUT="$HERE/target/vir"
JSON=0
CARGO=0
NOCHEAT=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --seed) SEED="$2"; shift 2 ;;
    --rlimit) RLIMIT="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --json) JSON=1; shift ;;
    --cargo) CARGO=1; shift ;;
    --no-cheating) NOCHEAT=1; shift ;;
    *) echo "usage: verify.sh [--seed N] [--rlimit R] [--out DIR] [--json] [--no-cheating] [--cargo]" >&2; exit 2 ;;
  esac
done
[ -x "$VERUS" ] || { echo "pinned verus missing: $VERUS (run scripts/get_toolchain.sh verus)" >&2; exit 1; }
EXTRA=(--rlimit "$RLIMIT" --num-threads 1)
[ -n "$SEED" ] && EXTRA+=(--smt-option "smt.random_seed=$SEED")
[ "$NOCHEAT" = 1 ] && EXTRA+=(--no-cheating)

if [ "$CARGO" = 1 ]; then
  cd "$HERE"
  PATH="$VD:$PATH" RUSTUP_TOOLCHAIN="$RUST_TC" "$VD/cargo-verus" verus verify \
    --manifest-path "$HERE/Cargo.toml" --workspace -- "${EXTRA[@]}"
  exit $?
fi

mkdir -p "$OUT"
cd "$HERE"
status=0
for ((k = 0; k < ${#CRATES[@]}; k++)); do
  crate="${CRATES[$k]}"
  args=("$crate/src/lib.rs" --crate-type=lib --crate-name "$crate" "${EXTRA[@]}")
  for ((j = 0; j < k; j++)); do
    args+=(--import "${CRATES[$j]}=$OUT/${CRATES[$j]}.vir")
  done
  if [ "$k" -gt 0 ]; then
    below="${CRATES[$((k - 1))]}"
    args+=(--extern "$below=$OUT/lib$below.rlib" -L "$OUT")
  fi
  args+=(--export "$OUT/$crate.vir" --compile --out-dir "$OUT")
  if [ "$JSON" = 1 ]; then
    if RUSTUP_TOOLCHAIN="$RUST_TC" "$VERUS" "${args[@]}" --output-json --time \
        > "$OUT/$crate.json" 2> "$OUT/$crate.stderr"; then
      echo "$crate: ok"
    else
      echo "$crate: FAILED (see $OUT/$crate.stderr)"; status=1; break
    fi
  else
    printf '%s: ' "$crate"
    if ! RUSTUP_TOOLCHAIN="$RUST_TC" "$VERUS" "${args[@]}"; then status=1; break; fi
  fi
done
exit $status
