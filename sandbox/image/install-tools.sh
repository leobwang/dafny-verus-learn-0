#!/bin/bash
# install-tools.sh — the sandbox image's own uv, age and opencode: each tool's
# Linux release for the image's architecture, by the asset's and the binary's
# sha256 from /opt/dvl/install/pins.env (DELTAS Δ504: no host binary is copied
# into an image). Runs only inside the image build, into /opt/dvl/tools.
set -euo pipefail
# shellcheck disable=SC1091
source /opt/dvl/install/pins.env
out=/opt/dvl/tools
mkdir -p "$out"
die() { printf 'install-tools: FAILED: %s\n' "$*" >&2; exit 1; }
one() {   # NAME URL SHA256 BIN_SHA256
  local w bin; w=$(mktemp -d)
  curl -fsSL --proto '=https' --retry 3 -o "$w/a.tgz" "$2" || die "download failed: $2"
  [[ $(sha256sum "$w/a.tgz" | cut -d' ' -f1) == "$3" ]] || die "$2 is not the pinned asset"
  tar -xzf "$w/a.tgz" -C "$w"
  bin=$(find "$w" -type f -name "$1" | head -n 1)
  [[ -n $bin && $(sha256sum "$bin" | cut -d' ' -f1) == "$4" ]] || die "the $1 of $2 is not the pinned binary"
  install -m 0555 "$bin" "$out/$1"; rm -rf "$w"
}
one uv "$UV_URL" "$UV_SHA256" "$UV_BIN_SHA256"
one age "$AGE_URL" "$AGE_SHA256" "$AGE_BIN_SHA256"
one opencode "$OPENCODE_URL" "$OPENCODE_SHA256" "$OPENCODE_BIN_SHA256"
"$out/uv" --version
"$out/age" --version
