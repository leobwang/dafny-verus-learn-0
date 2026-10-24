#!/usr/bin/env bash
# sandbox/build-images.sh: build the sandbox images and pin them by digest
# (DV4-PLAN §5.2, step 2a). Author-run, after host action H1; never in CI.
#
#   sandbox/build-images.sh [--check] [--snapshot YYYYMMDDTHHMMSSZ]
#
# It builds, from a staged context that holds only these inputs (never the
# checkout as a context):
#   dvl-toolchain  ubuntu:24.04 by digest; python3, libicu74 (Dafny), gcc and
#                  libc6-dev (Verus --compile tests) from the dated Ubuntu
#                  snapshot; the pinned Dafny and Verus trees exactly as
#                  scripts/get_toolchain.sh --check verifies them (checked again
#                  inside the image); the Rust toolchain Verus needs with the
#                  host's rustup; user agent (uid 1000); /opt/dvl/bin/entry
#                  (the relays), /opt/dvl/bin/controls (the containment
#                  controls) and /opt/dvl/bin/truthcheck (the grader
#                  container's truth mode), from sandbox/image/; the pinned
#                  uv (the harness pin, VERSIONS.md §1.4) and age binaries
#                  (sha256 checked below); a uv cache seeded from
#                  harness/uv.lock (the locked wheels, hash-checked by uv)
#                  for the Python acceptance tests.
#   dvl-agent      dvl-toolchain by digest plus the pinned opencode binary
#                  (sha256 checked below).
# and writes sandbox/images.lock (schema 1): each image's digest, its base,
# the packages list's sha256 and the inputs' digests. VERSIONS.md §1.4's
# sandbox row copies the digests (by hand: VERSIONS.md is a prose file).
#
# --check   build nothing: compare the lock with the local images and the
#           current inputs, and exit 1 on any difference.
#
# Calls plain docker only (Δ153: never sudo or sg); refuses (exit 3) without
# Docker access. Memory: an image build runs no solver; the build's own
# get_toolchain.sh --check is a hash pass. Exit: 0 done, 1 failed, 2 usage,
# 3 refused.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
ROOT=$(dirname "$HERE")
LOCK="$HERE/images.lock"

BASE="ubuntu@sha256:008173c23f95b170204355c12626cb5a965d779a7e1283b09e9cffbb1bf33ca3"
SNAPSHOT_DEFAULT="20261010T000000Z"
RUST_TOOLCHAIN="1.98.1-x86_64-unknown-linux-gnu"
OPENCODE_VERSION="1.18.25"
OPENCODE_SHA256="5750524bbdd592157a3e1b4451038c1d05075365336cd74b8ec573f92b2924c0"
OPENCODE_BIN="$HOME/.opencode/bin/opencode"
UV_VERSION="0.12.4"
UV_SHA256="47884be1ceaf3e73c6b6e5abed5cba5eba55109505b796c459503a48b70ba49d"
UV_BIN="$HOME/.local/bin/uv"
AGE_VERSION="v1.3.2"
AGE_SHA256="eb7dd1b518f0a307c99cd97782623c5321da049154b04acd2d98d21aa7bc9b2c"
AGE_BIN="$HOME/.local/bin/age"
RUSTUP_BIN="${CARGO_HOME:-$HOME/.cargo}/bin/rustup"
RUSTUP_TOOLCHAINS="${RUSTUP_HOME:-$HOME/.rustup}/toolchains"

log() { printf 'build-images: %s\n' "$*" >&2; }
die() { printf 'build-images: FAILED: %s\n' "$*" >&2; exit 1; }
refuse() { printf 'build-images: refused: %s\n' "$*" >&2; exit 3; }
usage() { printf 'usage: sandbox/build-images.sh [--check] [--snapshot YYYYMMDDTHHMMSSZ]\n' >&2; exit 2; }

check=0 snapshot=$SNAPSHOT_DEFAULT
while (($#)); do
  case $1 in
    --check) check=1 ;;
    --snapshot) shift; [[ ${1:-} =~ ^[0-9]{8}T[0-9]{6}Z$ ]] || usage; snapshot=$1 ;;
    *) usage ;;
  esac
  shift
done

"$ROOT/scripts/mksandbox-run" --check-access >&2 || refuse "no Docker access (scripts/mksandbox-run --check-access)"

sha() { sha256sum -- "$1" | cut -d' ' -f1; }
# "<files> <sha256 of the sorted per-file manifest>", as get_toolchain.sh's tree
# digest (its pin record left out)
tree_digest() {
  local m
  m=$(cd "$1" && find . -path ./.get_toolchain.pin -prune -o -type f -print0 | LC_ALL=C sort -z \
       | xargs -0 -r sha256sum --)
  printf '%s %s\n' "$(printf '%s\n' "$m" | grep -c .)" "$(printf '%s\n' "$m" | sha256sum | cut -d' ' -f1)"
}

dafny_bin=$(bash "$ROOT/scripts/get_toolchain.sh" dafny --check) || die "get_toolchain.sh dafny --check"
verus_bin=$(bash "$ROOT/scripts/get_toolchain.sh" verus --check) || die "get_toolchain.sh verus --check"
dafny_dir=$(cd "$(dirname "$dafny_bin")/.." && pwd -P)
verus_dir=$(cd "$(dirname "$verus_bin")/.." && pwd -P)
rust_dir="$RUSTUP_TOOLCHAINS/$RUST_TOOLCHAIN"
[[ -d $rust_dir ]] || die "the Rust toolchain $RUST_TOOLCHAIN is not installed ($rust_dir)"
[[ -x $RUSTUP_BIN ]] || die "rustup not found at $RUSTUP_BIN"
[[ -f $OPENCODE_BIN ]] || die "opencode not found at $OPENCODE_BIN"
[[ $(sha "$OPENCODE_BIN") == "$OPENCODE_SHA256" ]] \
  || die "$OPENCODE_BIN has sha256 $(sha "$OPENCODE_BIN"), pinned $OPENCODE_SHA256 ($OPENCODE_VERSION)"
[[ -f $UV_BIN && $(sha "$UV_BIN") == "$UV_SHA256" ]] \
  || die "$UV_BIN is missing or not the pinned uv $UV_VERSION (sha256 $UV_SHA256)"
[[ -f $AGE_BIN && $(sha "$AGE_BIN") == "$AGE_SHA256" ]] \
  || die "$AGE_BIN is missing or not the pinned age $AGE_VERSION (sha256 $AGE_SHA256; VERSIONS.md §1.4)"
uv_lock_sha=$(sha "$ROOT/harness/uv.lock")
pyproject_sha=$(sha "$ROOT/harness/pyproject.toml")

rust_digest=$(tree_digest "$rust_dir")
rustup_sha=$(sha "$RUSTUP_BIN")
image_src_digest=$(cd "$HERE" && sha256sum image/entry.py image/controls.py image/truthcheck.py \
                   images/toolchain.Dockerfile images/agent.Dockerfile | sha256sum | cut -d' ' -f1)

if ((check)); then
  python3 - "$LOCK" "$rust_digest" "$rustup_sha" "$OPENCODE_SHA256" "$image_src_digest" "$snapshot" \
    "$UV_SHA256" "$AGE_SHA256" "$uv_lock_sha" <<'EOF'
import json, subprocess, sys, tomllib
lock, rust, rustup, oc, src, snap, uvs, ages, uvl = sys.argv[1:]
data = tomllib.load(open(lock, "rb"))
bad = []
imgs = {i["name"]: i for i in data.get("image", [])}
def where():
    """The Docker context the CLI looked in (DOCKER_CONTEXT, DOCKER_HOST or the
    current context), with its endpoint: images live per daemon."""
    c = subprocess.run(["docker", "context", "show"], capture_output=True, text=True)
    name = c.stdout.strip() or "?"
    e = subprocess.run(["docker", "context", "inspect", "--format",
                        "{{.Endpoints.docker.Host}}", name], capture_output=True, text=True)
    return f"Docker context {name!r} ({e.stdout.strip() or 'endpoint unknown'})"
for name in ("dvl-toolchain", "dvl-agent"):
    i = imgs.get(name)
    if not i:
        bad.append(f"{name} is not in the lock"); continue
    p = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", f"{name}@{i['digest']}"],
                       capture_output=True, text=True)
    if p.returncode != 0 or p.stdout.strip() != i["digest"]:
        bad.append(f"{name}@{i['digest']} is not a local image in {where()}; "
                   "set DOCKER_CONTEXT to the context that holds the course images, or build them")
    want = {"rust_toolchain_tree": rust, "rustup_sha256": rustup, "image_sources_sha256": src,
            "apt_snapshot": snap, "uv_sha256": uvs, "age_sha256": ages, "uv_lock_sha256": uvl}
    if name == "dvl-agent":
        want["opencode_sha256"] = oc
    for k, v in want.items():
        if i.get("inputs", {}).get(k) != v:
            bad.append(f"{name}: inputs.{k} is {i.get('inputs', {}).get(k)!r}, now {v!r}")
for b in bad:
    print("build-images: --check: " + b, file=sys.stderr)
print(f"build-images: --check: {'OK' if not bad else 'FAILED'} ({len(imgs)} image(s) in the lock)",
      file=sys.stderr)
sys.exit(1 if bad else 0)
EOF
  exit $?
fi

ctx=$(mktemp -d "${TMPDIR:-/tmp}/dvl-build-images.XXXXXX")
trap 'chmod -R u+w "$ctx" 2>/dev/null; rm -rf "$ctx"' EXIT
log "staging the build context in $ctx"
mkdir -p "$ctx/toolchain" "$ctx/rust/rustup/toolchains" "$ctx/rust/cargo/bin" "$ctx/dvl/bin" \
         "$ctx/dvl/check" "$ctx/agent"
cp -a "$dafny_dir" "$ctx/toolchain/"
cp -a "$verus_dir" "$ctx/toolchain/"
cp -a "$rust_dir" "$ctx/rust/rustup/toolchains/"
printf 'version = "12"\ndefault_toolchain = "%s"\nprofile = "minimal"\n\n[overrides]\n' \
  "$RUST_TOOLCHAIN" >"$ctx/rust/rustup/settings.toml"
cp "$RUSTUP_BIN" "$ctx/rust/cargo/bin/rustup"
install -m 0555 "$HERE/image/entry.py" "$ctx/dvl/bin/entry"
install -m 0555 "$HERE/image/controls.py" "$ctx/dvl/bin/controls"
install -m 0555 "$HERE/image/truthcheck.py" "$ctx/dvl/bin/truthcheck"
install -m 0555 "$UV_BIN" "$ctx/dvl/bin/uv"
install -m 0555 "$AGE_BIN" "$ctx/dvl/bin/age"
[[ $(sha "$ctx/dvl/bin/uv") == "$UV_SHA256" && $(sha "$ctx/dvl/bin/age") == "$AGE_SHA256" ]] \
  || die "the staged uv or age differs from its pin"
mkdir -p "$ctx/dvl/py"
install -m 0444 "$ROOT/harness/pyproject.toml" "$ctx/dvl/py/pyproject.toml"
install -m 0444 "$ROOT/harness/uv.lock" "$ctx/dvl/py/uv.lock"
install -m 0444 "$ROOT/scripts/get_toolchain.sh" "$ctx/dvl/check/get_toolchain.sh"
cp "$HERE/images/toolchain.Dockerfile" "$ctx/Dockerfile"
[[ $(tree_digest "$ctx/toolchain/$(basename "$dafny_dir")") == "$(tree_digest "$dafny_dir")" ]] || die "staged Dafny tree differs"
[[ $(tree_digest "$ctx/rust/rustup/toolchains/$RUST_TOOLCHAIN") == "$rust_digest" ]] || die "staged Rust tree differs"

stamp=$(date -u +%Y%m%d)
log "building dvl-toolchain (base $BASE, apt snapshot $snapshot)"
docker build --network default --pull=false --provenance=false --build-arg "BASE=$BASE" \
  --build-arg "APT_SNAPSHOT=$snapshot" -t "dvl-toolchain:$stamp" -f "$ctx/Dockerfile" "$ctx" >&2 \
  || die "docker build dvl-toolchain"
tdigest=$(docker image inspect --format '{{.Id}}' "dvl-toolchain:$stamp")
packages_sha=$(docker run --rm --network none --memory 512m --memory-swap 512m --user 1000:1000 \
  --cap-drop ALL --read-only "dvl-toolchain@$tdigest" cat /opt/dvl/packages.txt | sha256sum | cut -d' ' -f1)
pyver=$(docker run --rm --network none --memory 512m --memory-swap 512m --user 1000:1000 \
  --cap-drop ALL --read-only "dvl-toolchain@$tdigest" python3 --version)

actx="$ctx/agent-ctx"
mkdir -p "$actx/agent"
cp "$OPENCODE_BIN" "$actx/agent/opencode"
[[ $(sha "$actx/agent/opencode") == "$OPENCODE_SHA256" ]] || die "staged opencode differs"
cp "$HERE/images/agent.Dockerfile" "$actx/Dockerfile"
# BuildKit resolves a FROM by digest against a registry, so the agent image
# is built FROM the local tag, checked first to name the digest just built.
[[ $(docker image inspect --format '{{.Id}}' "dvl-toolchain:$stamp") == "$tdigest" ]] \
  || die "dvl-toolchain:$stamp no longer names $tdigest"
log "building dvl-agent (from dvl-toolchain:$stamp = dvl-toolchain@$tdigest)"
docker build --network none --pull=false --provenance=false --build-arg "TOOLCHAIN=dvl-toolchain:$stamp" \
  -t "dvl-agent:$stamp" -f "$actx/Dockerfile" "$actx" >&2 || die "docker build dvl-agent"
adigest=$(docker image inspect --format '{{.Id}}' "dvl-agent:$stamp")

today=$(date -u +%Y-%m-%d)
dafny_tree=$(tree_digest "$dafny_dir")
verus_tree=$(tree_digest "$verus_dir")
cat >"$LOCK" <<EOF
# sandbox/images.lock: the sandbox images by digest (DV4-PLAN §5.2), schema 1.
# Written by sandbox/build-images.sh (DV4 step 2a); a manifest names its image
# as <name>@<digest> from here, and scripts/mksandbox-run refuses any other.
# \`sandbox/build-images.sh --check\` compares this file with the local images
# and the current inputs. The digests are copied into VERSIONS.md §1.4.
schema = 1

[[image]]
name = "dvl-toolchain"
digest = "$tdigest"
built = "$today"
base = "$BASE"
python = "$pyver"
packages_sha256 = "$packages_sha"
[image.inputs]
apt_snapshot = "$snapshot"
dafny_tree = "$dafny_tree"
verus_tree = "$verus_tree"
rust_toolchain = "$RUST_TOOLCHAIN"
rust_toolchain_tree = "$rust_digest"
rustup_sha256 = "$rustup_sha"
image_sources_sha256 = "$image_src_digest"
uv_version = "$UV_VERSION"
uv_sha256 = "$UV_SHA256"
uv_lock_sha256 = "$uv_lock_sha"
age_version = "$AGE_VERSION"
age_sha256 = "$AGE_SHA256"

[[image]]
name = "dvl-agent"
digest = "$adigest"
built = "$today"
base = "dvl-toolchain@$tdigest"
python = "$pyver"
packages_sha256 = "$packages_sha"
[image.inputs]
apt_snapshot = "$snapshot"
dafny_tree = "$dafny_tree"
verus_tree = "$verus_tree"
rust_toolchain = "$RUST_TOOLCHAIN"
rust_toolchain_tree = "$rust_digest"
rustup_sha256 = "$rustup_sha"
image_sources_sha256 = "$image_src_digest"
uv_version = "$UV_VERSION"
uv_sha256 = "$UV_SHA256"
uv_lock_sha256 = "$uv_lock_sha"
age_version = "$AGE_VERSION"
age_sha256 = "$AGE_SHA256"
opencode_version = "$OPENCODE_VERSION"
opencode_sha256 = "$OPENCODE_SHA256"
EOF
log "dvl-toolchain@$tdigest"
log "dvl-agent@$adigest"
log "wrote $LOCK"
