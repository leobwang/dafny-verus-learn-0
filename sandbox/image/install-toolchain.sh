#!/bin/bash
# install-toolchain.sh — the sandbox image's own pinned Linux toolchain, installed
# at image build time (DELTAS Δ504; DV4-PLAN §5.2). Runs only inside the image
# build (sandbox/images/toolchain.Dockerfile's build stage), as root.
#
#   install-toolchain.sh amd64|arm64
#
# Reads /opt/dvl/install/pins.env (written by sandbox/build-images.sh) and
# installs into /opt/dvl/toolchain (Dafny 4.11.0 and Verus 0.2026.09.27.3cf1832)
# and /opt/rust (rustup and Verus's Rust 1.98.1):
#   amd64  the vendor Linux x64 releases, through scripts/get_toolchain.sh (the
#          pinned tag, commit, asset sha256 and tree digest), and rustup-init
#          by sha256;
#   arm64  no vendor release exists for linux-aarch64, so pinned source builds:
#          Verus from its git commit (Rust 1.98.1 with rustc-dev and
#          llvm-tools, Z3 4.16.0's official arm64 build by sha256), Dafny 4.11.0
#          from its NuGet package by sha256 on the image's .NET 8 runtime, Z3
#          4.12.1 from its git tag (no git hash in its version line), Z3 4.14.1
#          from its official arm64 build by sha256.
# Then every solver must match its rlimit fingerprint (z3fp.py against
# tests/fingerprint/z3/expected), or the build fails.
set -euo pipefail

arch=${1:?usage: install-toolchain.sh amd64|arm64}
# shellcheck disable=SC1091
source /opt/dvl/install/pins.env
T=/opt/dvl/toolchain
FP=/opt/dvl/install/fp
export RUSTUP_HOME=/opt/rust/rustup CARGO_HOME=/opt/rust/cargo
export PATH=/opt/rust/cargo/bin:$PATH
JOBS=${DVL_BUILD_JOBS:-4}

log() { printf 'install-toolchain: %s\n' "$*" >&2; }
die() { printf 'install-toolchain: FAILED: %s\n' "$*" >&2; exit 1; }
fetch() {   # URL SHA256 OUT
  curl -fsSL --proto '=https' --retry 3 -o "$3" "$1" || die "download failed: $1"
  [[ $(sha256sum "$3" | cut -d' ' -f1) == "$2" ]] || die "$1 has sha256 $(sha256sum "$3" | cut -d' ' -f1), pinned $2"
}
git_at() {  # REPO REF COMMIT DIR
  mkdir -p "$4"; git -C "$4" init -q; git -C "$4" remote add origin "$1"
  git -C "$4" fetch -q --depth 1 origin "$2" || die "git fetch $1 $2"
  git -C "$4" checkout -q FETCH_HEAD
  [[ $(git -C "$4" rev-parse HEAD) == "$3" ]] || die "$1 $2 is $(git -C "$4" rev-parse HEAD), pinned $3"
}
z3_from_zip() {   # URL SHA256 BINSHA OUT
  local w; w=$(mktemp -d)
  fetch "$1" "$2" "$w/z3.zip"
  unzip -q "$w/z3.zip" -d "$w"
  local bin; bin=$(find "$w" -path '*/bin/z3' -type f | head -n 1)
  [[ -n $bin && $(sha256sum "$bin" | cut -d' ' -f1) == "$3" ]] || die "the z3 of $1 is not the pinned binary"
  install -D -m 0755 "$bin" "$4"; rm -rf "$w"
}

# --- Rust (both arches): rustup-init by sha256, the pinned toolchain as default
case $arch in
  amd64) triple=x86_64-unknown-linux-gnu ;;
  arm64) triple=aarch64-unknown-linux-gnu ;;
  *) die "unknown arch $arch" ;;
esac
fetch "https://static.rust-lang.org/rustup/archive/$RUSTUP_VERSION/$triple/rustup-init" \
  "$RUSTUP_INIT_SHA256" /tmp/rustup-init
chmod 0755 /tmp/rustup-init
/tmp/rustup-init -y --no-modify-path --profile minimal --default-toolchain "$RUST_VERSION-$triple" >&2
rm -f /tmp/rustup-init
rustup set auto-self-update disable >&2

if [[ $arch == amd64 ]]; then
  # the vendor releases, exactly as scripts/get_toolchain.sh pins and checks them
  DVL_TOOLCHAIN_DIR=$T bash /opt/dvl/check/get_toolchain.sh dafny >&2
  DVL_TOOLCHAIN_DIR=$T bash /opt/dvl/check/get_toolchain.sh verus >&2
  rm -rf "$T/.downloads" "$T"/.lock-*
  dafny_dir="$T/dafny-4.11.0/dafny"; verus_dir="$T/verus-0.2026.09.27.3cf1832/verus-x86-linux"
else
  dafny_dir="$T/dafny-4.11.0/dafny"; verus_dir="$T/verus-0.2026.09.27.3cf1832/verus-arm64-linux"
  b=/tmp/dvl-build; mkdir -p "$b" "$dafny_dir/z3/bin"
  # Dafny 4.11.0: the NuGet tool package (tools/net8.0/any) on the image's .NET 8
  dotnet --list-runtimes | grep -qF "Microsoft.NETCore.App 8.0." || die "no .NET 8 runtime"
  fetch "$DAFNY_NUPKG_URL" "$DAFNY_NUPKG_SHA256" "$b/dafny.nupkg"
  unzip -q "$b/dafny.nupkg" 'tools/net8.0/any/*' -d "$b/nupkg"
  cp -R "$b/nupkg/tools/net8.0/any/." "$dafny_dir/"
  dn=$(readlink -f "$(command -v dotnet)")
  cat >"$dafny_dir/dafny" <<EOF
#!/bin/sh
# dafny: Dafny 4.11.0 (NuGet, tools/net8.0/any) on the image's .NET 8 (DELTAS Δ504);
# called through the /opt/dvl/path/dafny symlink too, so \$0 is resolved (Δ506).
DOTNET_ROOT='$(dirname "$dn")'; export DOTNET_ROOT
DOTNET_CLI_TELEMETRY_OPTOUT=1; export DOTNET_CLI_TELEMETRY_OPTOUT
exec '$dn' "\$(dirname "\$(readlink -f "\$0")")/Dafny.dll" "\$@"
EOF
  chmod 0755 "$dafny_dir/dafny"
  # Z3 4.12.1 from its tag; Z3 4.14.1 the official arm64 build
  git_at "$Z3_SRC_REPO" "refs/tags/$Z3_SRC_TAG" "$Z3_SRC_COMMIT" "$b/z3"
  cmake -S "$b/z3" -B "$b/z3/build" -DCMAKE_BUILD_TYPE=Release -DZ3_BUILD_LIBZ3_SHARED=OFF \
    -DZ3_BUILD_PYTHON_BINDINGS=OFF -DZ3_BUILD_TEST_EXECUTABLES=OFF -DZ3_ENABLE_EXAMPLE_TARGETS=OFF \
    -DZ3_BUILD_DOCUMENTATION=OFF -DZ3_INCLUDE_GIT_HASH=OFF -DZ3_INCLUDE_GIT_DESCRIBE=OFF >&2
  cmake --build "$b/z3/build" --target shell -j "$JOBS" >&2
  install -m 0755 "$b/z3/build/z3" "$dafny_dir/z3/bin/z3-4.12.1"
  z3_from_zip "$Z3_4141_URL" "$Z3_4141_SHA256" "$Z3_4141_BIN_SHA256" "$dafny_dir/z3/bin/z3-4.14.1"
  # Verus from its commit, the upstream release workflow's steps
  rustup component add --toolchain "$RUST_VERSION-$triple" rustc-dev llvm-tools rust-src >&2
  git_at "$VERUS_GIT" "$VERUS_COMMIT" "$VERUS_COMMIT" "$b/verus"
  z3_from_zip "$VERUS_Z3_URL" "$VERUS_Z3_SHA256" "$VERUS_Z3_BIN_SHA256" "$b/verus/source/z3"
  ( cd "$b/verus/source" && export RUSTUP_TOOLCHAIN="$RUST_VERSION-$triple" CARGO_BUILD_JOBS="$JOBS" \
    && cargo run -q -p cargo-verus-toolchains --bin create-manifest -- --write-to-dir cargo-verus/toolchain-manifests \
    && cargo build --release \
    && cargo run --release -p cargo-verus -- build --release --manifest-path vstd/Cargo.toml ) >&2
  rel="$b/verus/source/target-verus/release"
  cp "$b/verus/source/z3" "$rel/z3"
  ( cd "$b/verus/source" && RUSTUP_TOOLCHAIN="$RUST_VERSION-$triple" ./target-verus/release/verus \
      --version --output-json ) >"$rel/version.json"
  mkdir -p "$(dirname "$verus_dir")"
  cp -RL "$rel" "$verus_dir"
  rm -rf "$b" "$CARGO_HOME/registry" "$CARGO_HOME/git"
fi

# --- the version lines and the rlimit fingerprint of every solver
"$dafny_dir/dafny" --version | grep -qx "$DAFNY_VERSION_OUTPUT" || die "dafny --version is not $DAFNY_VERSION_OUTPUT"
RUSTUP_TOOLCHAIN="$RUST_VERSION-$triple" "$verus_dir/verus" --version --output-json \
  | python3 -c 'import json,sys; v=json.load(sys.stdin)["verus"]; sys.exit(v["version"]+" "+v["commit"] != sys.argv[1])' \
    "$VERUS_VERSION $VERUS_COMMIT" || die "verus --version is not $VERUS_VERSION $VERUS_COMMIT"
for z in "$dafny_dir/z3/bin/z3-4.12.1=4.12.1" "$dafny_dir/z3/bin/z3-4.14.1=4.14.1" "$verus_dir/z3=4.16.0"; do
  bin=${z%%=*} ver=${z#*=}
  "$bin" --version | head -n 1 | grep -qx "Z3 version $ver - 64 bit" || die "$bin --version is not Z3 $ver"
  python3 /opt/dvl/install/z3fp.py "$bin" "$ver" "$FP" || die "$bin fails the Z3 $ver rlimit fingerprint"
done
mkdir -p /opt/dvl/path
ln -sf "$dafny_dir/dafny" /opt/dvl/path/dafny     # dvl.common's PATH lookup (arm64, D78)
ln -sf "$verus_dir/verus" /opt/dvl/path/verus
log "installed ($arch): $dafny_dir, $verus_dir, Rust $RUST_VERSION-$triple"
