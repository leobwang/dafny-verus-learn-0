#!/usr/bin/env bash
# sandbox/build-images.sh: build the sandbox images for one architecture and pin
# them by digest (DV4-PLAN §5.2; DELTAS Δ504). Author-run; never in CI.
#
#   sandbox/build-images.sh [--arch amd64|arm64] [--check] [--snapshot YYYYMMDDTHHMMSSZ]
#
# --arch defaults to the Docker host's architecture: amd64 on Linux x86-64,
# arm64 on Apple silicon (Docker Desktop's Linux VM). Build each architecture
# natively, on its own host: this script never emulates another one.
#
# It builds, with a memory-capped BuildKit builder (a docker-container builder
# `dvl-build-<arch>`, --driver-opt memory=$DVL_BUILD_MEMORY, default 12g, so
# every build step is bounded) and from a staged context that holds only the
# inputs below (never the checkout as a context), the two targets of
# images/toolchain.Dockerfile:
#   dvl-toolchain  ubuntu:24.04 by the architecture's manifest digest; python3,
#                  libicu74 (Dafny), gcc and libc6-dev (Verus --compile tests),
#                  and on arm64 dotnet-runtime-8.0, from the dated Ubuntu
#                  snapshot; the image's own pinned Linux toolchain, installed
#                  in the build (image/install-toolchain.sh: amd64 the vendor
#                  x64 Dafny and Verus releases through scripts/get_toolchain.sh,
#                  arm64 Verus built from its pinned commit and Dafny 4.11.0
#                  from NuGet with Z3 4.12.1 built from its tag), Rust 1.98.1
#                  through rustup-init (by sha256), every solver checked against
#                  its rlimit fingerprint (image/z3fp.py, tests/fingerprint/z3);
#                  the pinned uv and age Linux releases for the architecture (by
#                  asset and binary sha256); user agent (uid 1000);
#                  /opt/dvl/bin/entry (the relays and the gate container's
#                  forwarder), /opt/dvl/bin/controls and /opt/dvl/bin/truthcheck
#                  from sandbox/image/; a uv cache seeded from harness/uv.lock.
#   dvl-agent      dvl-toolchain plus the pinned opencode Linux release for the
#                  architecture (asset and binary sha256).
# and writes this architecture's entries of sandbox/images.lock (schema 2: one
# [[image]] per name and arch; the other architecture's entries are kept).
# No host binary goes into an image (D80).
#
# --check   build nothing: compare this architecture's lock entries with the
#           local images and the current inputs; exit 1 on any difference.
#
# Calls plain docker only (Δ153: never sudo or sg); refuses (exit 3) without
# Docker access. Exit: 0 done, 1 failed, 2 usage, 3 refused.

if [ -z "${BASH_VERSINFO:-}" ] || [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
  for _b in /opt/homebrew/bin/bash /usr/local/bin/bash; do
    if [ -x "$_b" ]; then exec "$_b" "$0" "$@"; fi
  done
fi
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
ROOT=$(dirname "$HERE")
LOCK="$HERE/images.lock"
SNAPSHOT_DEFAULT="20261010T000000Z"

log() { printf 'build-images: %s\n' "$*" >&2; }
die() { printf 'build-images: FAILED: %s\n' "$*" >&2; exit 1; }
refuse() { printf 'build-images: refused: %s\n' "$*" >&2; exit 3; }
usage() { printf 'usage: sandbox/build-images.sh [--arch amd64|arm64] [--check] [--snapshot YYYYMMDDTHHMMSSZ]\n' >&2; exit 2; }

check=0 snapshot=$SNAPSHOT_DEFAULT arch=""
while (($#)); do
  case $1 in
    --check) check=1 ;;
    --arch) shift; case ${1:-} in amd64|arm64) arch=$1 ;; *) usage ;; esac ;;
    --snapshot) shift; [[ ${1:-} =~ ^[0-9]{8}T[0-9]{6}Z$ ]] || usage; snapshot=$1 ;;
    *) usage ;;
  esac
  shift
done

"$ROOT/scripts/mksandbox-run" --check-access >&2 || refuse "no Docker access (scripts/mksandbox-run --check-access)"
if [[ -z $arch ]]; then
  case $(docker info --format '{{.Architecture}}' 2>/dev/null) in
    x86_64|amd64) arch=amd64 ;;
    aarch64|arm64) arch=arm64 ;;
    *) refuse "the Docker host's architecture is neither amd64 nor arm64" ;;
  esac
fi

if command -v sha256sum >/dev/null 2>&1; then SHA=(sha256sum); else SHA=(shasum -a 256); fi
sha() { "${SHA[@]}" -- "$1" | cut -d' ' -f1; }
sha_stdin() { "${SHA[@]}" | cut -d' ' -f1; }

# ---------------------------------------------------------------- pins -----
# ubuntu:24.04, index sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac
# (2026-09-30), by each architecture's manifest digest.
RUSTUP_VERSION="1.28.2"
RUST_VERSION="1.98.1"
UV_VERSION="0.12.4"
AGE_VERSION="v1.3.2"
OPENCODE_VERSION="1.18.25"
pins_for() {   # the pins.env of architecture $1
  cat <<EOF
RUSTUP_VERSION=$RUSTUP_VERSION
RUST_VERSION=$RUST_VERSION
DAFNY_VERSION_OUTPUT=4.11.0+fcb2042d6d043a2634f0854338c08feeaaaf4ae2
VERUS_VERSION=0.2026.09.27.3cf1832
VERUS_COMMIT=3cf18325f0fd0c3040fbdec8c0f2255c0504c91a
EOF
  case $1 in
    amd64) cat <<'EOF'
BASE=ubuntu@sha256:a2d43bffc46670d7108bb3c0468c67c5557c4c92e83e1e34cbff1322ad1b94dc
RUSTUP_INIT_SHA256=20a06e644b0d9bd2fbdbfd52d42540bdde820ea7df86e92e533c073da0cdd43c
UV_URL=https://github.com/astral-sh/uv/releases/download/0.12.4/uv-x86_64-unknown-linux-gnu.tar.gz
UV_SHA256=c8c60f47e6f88d18dbf6f33d7279fb1fbf7ae76631768152cf5578c3d65729b4
UV_BIN_SHA256=47884be1ceaf3e73c6b6e5abed5cba5eba55109505b796c459503a48b70ba49d
AGE_URL=https://github.com/FiloSottile/age/releases/download/v1.3.2/age-v1.3.2-linux-amd64.tar.gz
AGE_SHA256=cbe24006683f8eb669266162894b9a522a1af52f2665fbc63a4bb032ed26ac10
AGE_BIN_SHA256=eb7dd1b518f0a307c99cd97782623c5321da049154b04acd2d98d21aa7bc9b2c
OPENCODE_URL=https://github.com/anomalyco/opencode/releases/download/v1.18.25/opencode-linux-x64.tar.gz
OPENCODE_SHA256=58a3729a6f3432dd6d2917fcc4a949788891a035818646ad480e12c947f56e78
OPENCODE_BIN_SHA256=d91e0d33676d0839f7cde87924cd4127ea88c9d6784eea9f009a7d08bdc60eeb
DVL_TOOLCHAIN_DIR_ENV=/opt/dvl/toolchain
EOF
    ;;
    arm64) cat <<'EOF'
BASE=ubuntu@sha256:18b33ff3829707f31ada654a963b9ee35f2e6f0241b964bd17a22a9b330cb63d
RUSTUP_INIT_SHA256=e3853c5a252fca15252d07cb23a1bdd9377a8c6f3efa01531109281ae47f841c
UV_URL=https://github.com/astral-sh/uv/releases/download/0.12.4/uv-aarch64-unknown-linux-gnu.tar.gz
UV_SHA256=49d881b3403187e1f1789720881e77e4251ad4259d86c4844862657d2a35d13f
UV_BIN_SHA256=6a08833c474b5900a95f6ac22caa9bcdd0b5ad84888b08708a6ed92a795f18ce
AGE_URL=https://github.com/FiloSottile/age/releases/download/v1.3.2/age-v1.3.2-linux-arm64.tar.gz
AGE_SHA256=6b8dc4333c53a5a57c9e5834e3a48f92605d7154014cd07269ff3327db5d37f4
AGE_BIN_SHA256=41b072352f4561018949623c674d16ef704019b9108a9bbdbd21292efebfc94f
OPENCODE_URL=https://github.com/anomalyco/opencode/releases/download/v1.18.25/opencode-linux-arm64.tar.gz
OPENCODE_SHA256=35ef77897425e41b5183a2c21ac4fb1d4d944d82a94e3c920f57b5490af11ac5
OPENCODE_BIN_SHA256=896c9c9b1942d4d74576868af24bbcbfa3f267d7eeb17aa6b8dff70810800084
DVL_TOOLCHAIN_DIR_ENV=
DAFNY_NUPKG_URL=https://api.nuget.org/v3-flatcontainer/dafny/4.11.0/dafny.4.11.0.nupkg
DAFNY_NUPKG_SHA256=42f1000c3a8c894a9b362c2ff69adc2756a2484d599e3a0e5ce2f0eabaffe85f
Z3_SRC_REPO=https://github.com/Z3Prover/z3.git
Z3_SRC_TAG=z3-4.12.1
Z3_SRC_COMMIT=3012293c35eadbfd73e5b94adbe50b0cc44ffb83
Z3_4141_URL=https://github.com/Z3Prover/z3/releases/download/z3-4.14.1/z3-4.14.1-arm64-glibc-2.34.zip
Z3_4141_SHA256=63655c7b81ea54298494bc7c47d65ed5e1b7ea171fd91e78255b0cc3e214e1c2
Z3_4141_BIN_SHA256=94faba3955d8e036a3536efa2a7163ccb2f19241def4ed8414f113497719d797
VERUS_GIT=https://github.com/verus-lang/verus.git
VERUS_Z3_URL=https://github.com/Z3Prover/z3/releases/download/z3-4.16.0/z3-4.16.0-arm64-glibc-2.38.zip
VERUS_Z3_SHA256=87fcd963d3eecb0f12cf1c3ef0ad74e84a3a7bd3caed5d94445645ef94ae6274
VERUS_Z3_BIN_SHA256=06be7345658204eea8ce892a2fbe7741bd5bbde30d25842b8e395430ec88b94a
EOF
    ;;
  esac
}
PINS=$(pins_for "$arch")
BASE=$(sed -n 's/^BASE=//p' <<<"$PINS")
pins_sha=$(printf '%s\n' "$PINS" | sha_stdin)
uv_lock_sha=$(sha "$ROOT/harness/uv.lock")
image_src_digest=$(cd "$HERE" && "${SHA[@]}" image/entry.py image/controls.py image/truthcheck.py \
                   image/install-toolchain.sh image/install-tools.sh image/z3fp.py \
                   images/toolchain.Dockerfile | sha_stdin)
fp_digest=$(cd "$ROOT/tests/fingerprint/z3" && find . -type f | LC_ALL=C sort | xargs "${SHA[@]}" | sha_stdin)
gt_sha=$(sha "$ROOT/scripts/get_toolchain.sh")

# What each lock entry's inputs must say now.
inputs_json() {
  printf '{"apt_snapshot":"%s","pins_sha256":"%s","image_sources_sha256":"%s","uv_lock_sha256":"%s","fingerprint_sha256":"%s","get_toolchain_sha256":"%s"}' \
    "$snapshot" "$pins_sha" "$image_src_digest" "$uv_lock_sha" "$fp_digest" "$gt_sha"
}

if ((check)); then
  python3 - "$LOCK" "$arch" "$(inputs_json)" <<'EOF'
import json, subprocess, sys, tomllib
lock, arch, want = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
data = tomllib.load(open(lock, "rb"))
bad = []
imgs = {i["name"]: i for i in data.get("image", []) if i.get("arch", "amd64") == arch}
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
        bad.append(f"{name} ({arch}) is not in the lock"); continue
    p = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", i["digest"]],
                       capture_output=True, text=True)
    if p.returncode != 0 or p.stdout.strip() != i["digest"]:
        bad.append(f"{name}@{i['digest']} ({arch}) is not a local image in {where()}; "
                   "set DOCKER_CONTEXT to the context that holds the course images, or build them")
    for k, v in want.items():
        if i.get("inputs", {}).get(k) != v:
            bad.append(f"{name} ({arch}): inputs.{k} is {i.get('inputs', {}).get(k)!r}, now {v!r}")
for b in bad:
    print("build-images: --check: " + b, file=sys.stderr)
print(f"build-images: --check ({arch}): {'OK' if not bad else 'FAILED'}", file=sys.stderr)
sys.exit(1 if bad else 0)
EOF
  exit $?
fi

ctx=$(mktemp -d "${TMPDIR:-/tmp}/dvl-build-images.XXXXXX")
trap 'chmod -R u+w "$ctx" 2>/dev/null; rm -rf "$ctx"' EXIT
log "staging the build context ($arch) in $ctx"
mkdir -p "$ctx/install/fp" "$ctx/check" "$ctx/bin" "$ctx/py"
printf '%s\n' "$PINS" >"$ctx/install/pins.env"
for f in install-toolchain.sh install-tools.sh z3fp.py; do cp "$HERE/image/$f" "$ctx/install/$f"; done
cp -R "$ROOT/tests/fingerprint/z3/queries" "$ROOT/tests/fingerprint/z3/expected" "$ctx/install/fp/"
cp "$ROOT/scripts/get_toolchain.sh" "$ctx/check/get_toolchain.sh"
for f in entry controls truthcheck; do cp "$HERE/image/$f.py" "$ctx/bin/$f"; chmod 0555 "$ctx/bin/$f"; done
cp "$ROOT/harness/pyproject.toml" "$ROOT/harness/uv.lock" "$ctx/py/"
cp "$HERE/images/toolchain.Dockerfile" "$ctx/Dockerfile"

builder="dvl-build-$arch"
mem=${DVL_BUILD_MEMORY:-12g}
if ! docker buildx inspect "$builder" >/dev/null 2>&1; then
  log "creating the builder $builder (docker-container driver, memory $mem)"
  docker buildx create --name "$builder" --driver docker-container \
    --driver-opt "memory=$mem,memory-swap=$mem" >&2 || die "docker buildx create $builder"
fi
stamp=$(date -u +%Y%m%d)
common=(--builder "$builder" --platform "linux/$arch" --provenance=false --load
        --build-arg "BASE=$BASE" --build-arg "APT_SNAPSHOT=$snapshot" --build-arg "DVL_ARCH=$arch"
        --build-arg "DVL_TOOLCHAIN_DIR_ENV=$(sed -n 's/^DVL_TOOLCHAIN_DIR_ENV=//p' <<<"$PINS")"
        -f "$ctx/Dockerfile")
log "building dvl-toolchain ($arch; base $BASE, apt snapshot $snapshot)"
docker buildx build "${common[@]}" --target toolchain -t "dvl-toolchain:$stamp-$arch" "$ctx" >&2 \
  || die "docker buildx build dvl-toolchain"
log "building dvl-agent ($arch)"
docker buildx build "${common[@]}" --target agent -t "dvl-agent:$stamp-$arch" "$ctx" >&2 \
  || die "docker buildx build dvl-agent"
tdigest=$(docker image inspect --format '{{.Id}}' "dvl-toolchain:$stamp-$arch")
adigest=$(docker image inspect --format '{{.Id}}' "dvl-agent:$stamp-$arch")
run_ro() { docker run --rm --network none --memory 512m --memory-swap 512m --user 1000:1000 \
             --cap-drop ALL --read-only "$1" "${@:2}"; }
packages_sha=$(run_ro "$tdigest" cat /opt/dvl/packages.txt | sha_stdin)
pyver=$(run_ro "$tdigest" python3 --version)
dafny_ver=$(run_ro "$tdigest" dafny --version)

python3 - "$LOCK" "$arch" "$tdigest" "$adigest" "$BASE" "$pyver" "$packages_sha" "$dafny_ver" \
  "$(inputs_json)" "$UV_VERSION" "$AGE_VERSION" "$OPENCODE_VERSION" "$RUST_VERSION" <<'EOF'
import json, sys, tomllib, datetime
(lock, arch, td, ad, base, py, pk, dafny, inputs, uv, age, oc, rust) = sys.argv[1:]
try:
    old = tomllib.load(open(lock, "rb")).get("image", [])
except FileNotFoundError:
    old = []
keep = [i for i in old if i.get("arch") and i.get("arch") != arch]
today = datetime.date.today().isoformat()
inp = json.loads(inputs)
inp.update({"uv_version": uv, "age_version": age, "rust_toolchain": rust, "dafny_version": dafny})
new = [{"name": "dvl-toolchain", "arch": arch, "digest": td, "built": today, "base": base,
        "python": py, "packages_sha256": pk, "inputs": dict(inp)},
       {"name": "dvl-agent", "arch": arch, "digest": ad, "built": today,
        "base": f"dvl-toolchain@{td}", "python": py, "packages_sha256": pk,
        "inputs": dict(inp, opencode_version=oc)}]
q = json.dumps
out = ["# sandbox/images.lock: the sandbox images by digest (DV4-PLAN §5.2), schema 2:",
       "# one [[image]] per name and architecture (DELTAS Δ504). Written by",
       "# sandbox/build-images.sh, one architecture per run (the other's entries are",
       "# kept); a manifest names its image as <name>@<digest>, and scripts/mksandbox-run",
       "# offers and accepts only this host's architecture's. `sandbox/build-images.sh",
       "# --check` compares an architecture's entries with the local images and the",
       "# current inputs. The digests are copied into VERSIONS.md §1.4.",
       "schema = 2", ""]
for i in sorted(keep + new, key=lambda x: (x["arch"], x["name"] != "dvl-toolchain")):
    out.append("[[image]]")
    for k in ("name", "arch", "digest", "built", "base", "python", "packages_sha256"):
        out.append(f"{k} = {q(i[k])}")
    out.append("[image.inputs]")
    for k, v in sorted(i["inputs"].items()):
        out.append(f"{k} = {q(v)}")
    out.append("")
open(lock, "w").write("\n".join(out))
EOF
log "dvl-toolchain@$tdigest ($arch)"
log "dvl-agent@$adigest ($arch)"
log "wrote $LOCK"
