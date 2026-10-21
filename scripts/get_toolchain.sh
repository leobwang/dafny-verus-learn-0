#!/usr/bin/env bash
# get_toolchain.sh — install or verify the pinned Dafny / Verus toolchain, and
# the course's own copy of the pinned Claude Code version file.
#
#   scripts/get_toolchain.sh dafny|verus|claude [--check]
#
# `claude` (Δ277) differs from the two verifiers: nothing is downloaded. The
# pin is sandbox/apparatus.toml's [backend.claude] (version, binary, sha256;
# FVH_APPARATUS names another apparatus file, as for fvh), never a constant
# here. Claude Code's auto-updater deletes old version files from
# ~/.local/share/claude/versions/, so the pin names a copy in the course's own
# store, ~/.local/share/dafny-verus-learn-0/claude/versions/<version> (under
# HOME, as fvh resolves every pinned binary; one copy for every checkout of the
# course), which the updater never touches. `claude` copies the version file
# of the pinned version from the updater's directory into the store, checks
# the copy's sha256 against the pin and its `--version` line, and renames it
# into place read-only (0555). With the copy in place it only verifies; the
# store keeps every copy it installed, so a re-pin can be rolled back after
# the updater has deleted the old file. `--check` verifies the copy alone. The
# user's Claude Code settings and its auto-updater are left as they are.
#
# Contract (spec §8.3, §8.6, §11.1 row 19; design §14.5):
#   * Downloads the pinned release asset into <repo>/.toolchain/ (gitignored),
#     verifies its sha256 against a constant below, refuses a moved tag, and
#     installs atomically (staging dir + rename). On any mismatch it exits
#     non-zero and installs nothing.
#   * Idempotent: if the install already exists and verifies, nothing is
#     downloaded and the binary path is printed.
#   * --check verifies an existing install without any network access.
#   * stdout carries ONLY the binary path (one line, on success). Every
#     diagnostic goes to stderr.
#   * Verus: also ensures the exact Rust toolchain the release requires is
#     installed through rustup, without touching the user's default toolchain.
#
# What "verifies" means (both install and --check):
#   1. the pin record written at install time names exactly the pins below;
#   2. the installed tree hashes to the pinned tree digest (sha256 of the
#      sorted per-file sha256 manifest), so any added, removed or modified
#      file fails; no symlinks or special files are allowed;
#   3. the binaries answer with the pinned version outputs (verifier, bundled
#      Z3s, and for Verus the Rust toolchain via rustup).
# The tag check (tag -> commit, release asset digest) needs the GitHub API and
# therefore runs only when downloading.
#
# Exit codes: 0 ok; 1 refused / verification failed / not installed; 2 usage.
#
# Environment:
#   DVL_TOOLCHAIN_DIR   install root (default <repo>/.toolchain); for tests.
#   GITHUB_TOKEN/GH_TOKEN  optional, raises the GitHub API rate limit.
#   HOME                the Claude store and the updater's directory lie under it.
#   FVH_APPARATUS       the apparatus file `claude` reads (default
#                       <repo>/sandbox/apparatus.toml).

set -euo pipefail

# ---------------------------------------------------------------- pins -----

# Dafny 4.11.0 (tag v4.11.0 is an annotated tag; COMMIT is the tagged commit).
DAFNY_VERSION="4.11.0"
DAFNY_REPO="dafny-lang/dafny"
DAFNY_TAG="v4.11.0"
DAFNY_COMMIT="fcb2042d6d043a2634f0854338c08feeaaaf4ae2"
DAFNY_ASSET="dafny-4.11.0-x64-ubuntu-22.04.zip"
DAFNY_SHA256="a46a9ff7cdd720f7955854c78e95df13f4cfe6b80691b05f8654fe19e8267179"
DAFNY_INSTALL="dafny-4.11.0"
DAFNY_BIN_REL="dafny/dafny"
DAFNY_TREE_FILES="290"
DAFNY_TREE_SHA256="e879bb85aee36a99b7169535ef94ba8785da308996d5fb4b4d4f5e1b34ad701f"
DAFNY_VERSION_OUTPUT="4.11.0+fcb2042d6d043a2634f0854338c08feeaaaf4ae2"
# bundled solvers: "<path relative to install>=<exact first line of --version>"
DAFNY_Z3S=(
  "dafny/z3/bin/z3-4.12.1=Z3 version 4.12.1 - 64 bit"
  "dafny/z3/bin/z3-4.14.1=Z3 version 4.14.1 - 64 bit"
)

# Verus weekly release 0.2026.09.27.3cf1832 (never the rolling release).
VERUS_VERSION="0.2026.09.27.3cf1832"
VERUS_REPO="verus-lang/verus"
VERUS_TAG="release/0.2026.09.27.3cf1832"
VERUS_COMMIT="3cf18325f0fd0c3040fbdec8c0f2255c0504c91a"
VERUS_ASSET="verus-0.2026.09.27.3cf1832-x86-linux.zip"
VERUS_SHA256="43814031e10df043221d83c7fa842e3ebd662cb7b0090fc1eb4d7a8673226978"
VERUS_INSTALL="verus-0.2026.09.27.3cf1832"
VERUS_BIN_REL="verus-x86-linux/verus"
VERUS_TREE_FILES="3873"
VERUS_TREE_SHA256="57f0bd81b99b7b10f3cc5be5e72b087d15c096b500a0cd85f7c1693e509bad14"
VERUS_Z3S=(
  "verus-x86-linux/z3=Z3 version 4.16.0 - 64 bit"
)
VERUS_EXTRA_BINS=("verus-x86-linux/cargo-verus" "verus-x86-linux/rust_verify")
# The Rust toolchain the release was built against (its version.json says so).
VERUS_RUST_TOOLCHAIN="1.98.1-x86_64-unknown-linux-gnu"
VERUS_RUSTC_VERSION_OUTPUT="rustc 1.98.1 (48a229cea 2026-09-01)"

# ------------------------------------------------------------- plumbing ----

PIN_RECORD=".get_toolchain.pin"   # written inside the install dir; not in the tree digest

log() { printf 'get_toolchain: %s\n' "$*" >&2; }
die() { printf 'get_toolchain: REFUSED: %s\n' "$*" >&2; exit 1; }
usage() {
  printf 'usage: %s dafny|verus|claude [--check]\n' "${0##*/}" >&2
  exit 2
}

script_dir() { cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P; }

# Selects the pins for $1 into generic variables.
select_tool() {
  case "$1" in
    dafny)
      T_NAME=dafny T_VERSION=$DAFNY_VERSION T_REPO=$DAFNY_REPO T_TAG=$DAFNY_TAG
      T_COMMIT=$DAFNY_COMMIT T_ASSET=$DAFNY_ASSET T_SHA256=$DAFNY_SHA256
      T_INSTALL=$DAFNY_INSTALL T_BIN_REL=$DAFNY_BIN_REL
      T_TREE_FILES=$DAFNY_TREE_FILES T_TREE_SHA256=$DAFNY_TREE_SHA256
      T_Z3S=("${DAFNY_Z3S[@]}") T_EXTRA_BINS=()
      ;;
    verus)
      T_NAME=verus T_VERSION=$VERUS_VERSION T_REPO=$VERUS_REPO T_TAG=$VERUS_TAG
      T_COMMIT=$VERUS_COMMIT T_ASSET=$VERUS_ASSET T_SHA256=$VERUS_SHA256
      T_INSTALL=$VERUS_INSTALL T_BIN_REL=$VERUS_BIN_REL
      T_TREE_FILES=$VERUS_TREE_FILES T_TREE_SHA256=$VERUS_TREE_SHA256
      T_Z3S=("${VERUS_Z3S[@]}") T_EXTRA_BINS=("${VERUS_EXTRA_BINS[@]}")
      ;;
    *) usage ;;
  esac
  T_URL="https://github.com/${T_REPO}/releases/download/${T_TAG}/${T_ASSET}"
}

# A pin still holding its placeholder is not a pin: refuse rather than guess.
assert_pinned() {
  local v
  for v in "$@"; do
    [[ $v == *__PIN_* ]] && die "script has an unfilled pin ($v); fix scripts/get_toolchain.sh"
  done
  return 0
}

need() {
  local c
  for c in "$@"; do command -v "$c" >/dev/null 2>&1 || die "required command not found: $c"; done
}

assert_platform() {
  local os arch
  os=$(uname -s) arch=$(uname -m)
  [[ $os == Linux && $arch == x86_64 ]] || die "pinned assets are linux x86_64 only (host: $os $arch)"
}

sha256_of() { sha256sum -- "$1" | cut -d' ' -f1; }

# Prints the per-file manifest of tree $1: "<sha256>  ./<path>", sorted by path,
# excluding the pin record. Fails if the tree holds anything but regular files
# and directories.
tree_manifest() {
  local dir=$1 odd
  odd=$(cd "$dir" && find . -path "./$PIN_RECORD" -prune -o ! -type d ! -type f -print | head -n 5)
  [[ -z $odd ]] || die "tree $dir contains non-regular entries (symlinks or special files): ${odd//$'\n'/ }"
  ( cd "$dir" && find . -path "./$PIN_RECORD" -prune -o -type f -print0 \
      | LC_ALL=C sort -z | xargs -0 -r sha256sum -- )
}

# Prints "<file count> <sha256 of manifest>" for tree $1.
tree_digest() {
  local manifest
  manifest=$(tree_manifest "$1")
  printf '%s %s\n' "$(printf '%s\n' "$manifest" | grep -c .)" \
    "$(printf '%s\n' "$manifest" | sha256sum | cut -d' ' -f1)"
}

# GitHub API GET; prints the body.
gh_api() {
  local -a hdr=(-H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28')
  local tok=${GITHUB_TOKEN:-${GH_TOKEN:-}}
  [[ -n $tok ]] && hdr+=(-H "Authorization: Bearer $tok")
  curl -fsSL --proto '=https' --retry 3 "${hdr[@]}" "https://api.github.com/repos/$1"
}

json_get() {  # json_get <python expression over j> ; JSON on stdin
  python3 -c 'import json,sys; j=json.load(sys.stdin); v=eval(sys.argv[1]); print("" if v is None else v)' "$1"
}

# Refuses unless tag $T_TAG still resolves to commit $T_COMMIT and the release
# asset's published digest (when GitHub records one) equals the pinned sha256.
check_tag() {
  local body type sha depth=0 digest
  body=$(gh_api "${T_REPO}/git/ref/tags/${T_TAG}") || die "cannot resolve tag ${T_TAG} via the GitHub API (network or rate limit); refusing to install unverified"
  type=$(json_get 'j["object"]["type"]' <<<"$body")
  sha=$(json_get 'j["object"]["sha"]' <<<"$body")
  while [[ $type == tag ]]; do
    (( ++depth <= 4 )) || die "tag ${T_TAG}: annotated-tag chain too deep"
    body=$(gh_api "${T_REPO}/git/tags/${sha}") || die "cannot dereference tag object ${sha}"
    type=$(json_get 'j["object"]["type"]' <<<"$body")
    sha=$(json_get 'j["object"]["sha"]' <<<"$body")
  done
  [[ $type == commit ]] || die "tag ${T_TAG} points at a ${type}, not a commit"
  [[ $sha == "$T_COMMIT" ]] || die "tag ${T_TAG} MOVED: now ${sha}, pinned ${T_COMMIT}"
  log "tag ${T_TAG} -> ${sha} (matches pin)"
  body=$(gh_api "${T_REPO}/releases/tags/${T_TAG}") || die "cannot read release ${T_TAG} via the GitHub API"
  digest=$(json_get "next((a.get('digest') for a in j['assets'] if a['name']=='${T_ASSET}'), 'MISSING')" <<<"$body")
  case $digest in
    MISSING) die "release ${T_TAG} has no asset named ${T_ASSET}" ;;
    "") log "release asset has no digest field; relying on the pinned sha256 alone" ;;
    "sha256:${T_SHA256}") log "release asset digest matches pin" ;;
    *) die "release asset digest ${digest} != pinned sha256:${T_SHA256}" ;;
  esac
}

# Ensures $DL/$T_ASSET exists and has the pinned sha256 (downloading if absent).
fetch_asset() {
  local dl="$ROOT/.downloads" got
  mkdir -p "$dl"
  local zip="$dl/$T_ASSET" part="$dl/$T_ASSET.part.$$"
  if [[ -f $zip ]]; then
    got=$(sha256_of "$zip")
    [[ $got == "$T_SHA256" ]] || die "cached $zip has sha256 $got, pinned $T_SHA256 (remove it to re-download)"
    log "using cached $zip (sha256 ok)"
    return 0
  fi
  log "downloading $T_URL"
  CLEANUP+=("$part")
  curl -fL --no-progress-meter --proto '=https' --tlsv1.2 --retry 3 -o "$part" "$T_URL" >&2 \
    || die "download failed: $T_URL"
  got=$(sha256_of "$part")
  if [[ $got != "$T_SHA256" ]]; then
    rm -f -- "$part"
    die "downloaded $T_ASSET has sha256 $got, pinned $T_SHA256"
  fi
  mv -f -- "$part" "$zip"
  log "sha256 ok: $T_SHA256"
}

# The pin record: what was installed, checked field-by-field by --check.
pin_record() {
  printf 'tool=%s\nversion=%s\ntag=%s\ncommit=%s\nasset=%s\nasset_sha256=%s\ntree_files=%s\ntree_sha256=%s\n' \
    "$T_NAME" "$T_VERSION" "$T_TAG" "$T_COMMIT" "$T_ASSET" "$T_SHA256" "$T_TREE_FILES" "$T_TREE_SHA256"
}

# ---------------------------------------------------- rust (verus only) ----

rust_toolchain_present() {
  local list   # captured first: grep -q closing a pipe early would trip pipefail
  list=$(rustup toolchain list 2>/dev/null) || return 1
  cut -d' ' -f1 <<<"$list" | grep -xF "$VERUS_RUST_TOOLCHAIN" >/dev/null
}

ensure_rust_toolchain() {
  need rustup
  if rust_toolchain_present; then
    log "rust toolchain $VERUS_RUST_TOOLCHAIN already installed"
    return 0
  fi
  local before after
  before=$(rustup default 2>/dev/null || true)
  log "installing rust toolchain $VERUS_RUST_TOOLCHAIN (profile minimal; default left as: ${before:-none})"
  rustup toolchain install "$VERUS_RUST_TOOLCHAIN" --profile minimal --no-self-update >&2 \
    || die "rustup failed to install $VERUS_RUST_TOOLCHAIN"
  after=$(rustup default 2>/dev/null || true)
  [[ $before == "$after" ]] || die "rustup changed the default toolchain ($before -> $after); restore it with: rustup default ${before%% *}"
}

check_rust_toolchain() {
  command -v rustup >/dev/null 2>&1 || { log "rustup not found"; return 1; }
  rust_toolchain_present || { log "rust toolchain $VERUS_RUST_TOOLCHAIN not installed"; return 1; }
  local out
  out=$(rustup run "$VERUS_RUST_TOOLCHAIN" rustc --version 2>/dev/null) || { log "rustc ($VERUS_RUST_TOOLCHAIN) does not run"; return 1; }
  [[ $out == "$VERUS_RUSTC_VERSION_OUTPUT" ]] || { log "rustc version '$out' != pinned '$VERUS_RUSTC_VERSION_OUTPUT'"; return 1; }
}

# ------------------------------------------------------------- verify ------

# Verifies the install at $1 (an install dir). Returns 0, or 1 with reasons on stderr.
verify_install() {
  local dir=$1 bin="$1/$T_BIN_REL" ok=0 got entry rel want out
  [[ -d $dir ]] || { log "not installed: $dir"; return 1; }
  if [[ ! -f $dir/$PIN_RECORD ]] || [[ "$(cat -- "$dir/$PIN_RECORD")" != "$(pin_record)" ]]; then
    log "pin record $dir/$PIN_RECORD missing or does not match the pins in this script"
    ok=1
  fi
  got=$(tree_digest "$dir")
  if [[ $got != "$T_TREE_FILES $T_TREE_SHA256" ]]; then
    log "tree digest of $dir is '$got', pinned '$T_TREE_FILES $T_TREE_SHA256' (files added, removed or modified)"
    ok=1
  fi
  for rel in "$T_BIN_REL" "${T_EXTRA_BINS[@]}"; do
    [[ -x $dir/$rel ]] || { log "missing or not executable: $dir/$rel"; ok=1; }
  done
  for entry in "${T_Z3S[@]}"; do
    rel=${entry%%=*} want=${entry#*=}
    out=$("$dir/$rel" --version 2>/dev/null | head -n 1) || true
    [[ $out == "$want" ]] || { log "$rel --version: '$out', pinned '$want'"; ok=1; }
  done
  (( ok == 0 )) || return 1
  case $T_NAME in
    dafny)
      out=$("$bin" --version 2>/dev/null) || { log "$bin --version failed"; return 1; }
      [[ $out == "$DAFNY_VERSION_OUTPUT" ]] || { log "dafny --version: '$out', pinned '$DAFNY_VERSION_OUTPUT'"; return 1; }
      ;;
    verus)
      check_rust_toolchain || return 1
      out=$("$bin" --version --output-json 2>/dev/null) || { log "$bin --version --output-json failed"; return 1; }
      got=$(json_get 'j["verus"]["version"]+" "+j["verus"]["commit"]+" "+j["verus"]["toolchain"].split()[0]' <<<"$out") \
        || { log "cannot parse verus --version --output-json"; return 1; }
      want="$VERUS_VERSION $VERUS_COMMIT $VERUS_RUST_TOOLCHAIN"
      [[ $got == "$want" ]] || { log "verus reports '$got', pinned '$want'"; return 1; }
      ;;
  esac
  return 0
}

# ------------------------------------------------------------- install -----

install_tool() {
  local final="$ROOT/$T_INSTALL" stage
  check_tag
  fetch_asset
  if [[ $T_NAME == verus ]]; then ensure_rust_toolchain; fi
  stage=$(mktemp -d "$ROOT/.staging-${T_NAME}.XXXXXX")
  CLEANUP+=("$stage")
  log "extracting into $stage"
  unzip -q "$ROOT/.downloads/$T_ASSET" -d "$stage" >&2 || die "unzip failed"
  local got
  got=$(tree_digest "$stage")
  [[ $got == "$T_TREE_FILES $T_TREE_SHA256" ]] \
    || die "extracted tree digest '$got' != pinned '$T_TREE_FILES $T_TREE_SHA256'"
  if [[ $T_NAME == verus ]]; then
    got=$(json_get 'j["verus"]["toolchain"].split()[0]+" "+j["verus"]["commit"]' <"$stage/verus-x86-linux/version.json")
    [[ $got == "$VERUS_RUST_TOOLCHAIN $VERUS_COMMIT" ]] \
      || die "release version.json says '$got', pinned '$VERUS_RUST_TOOLCHAIN $VERUS_COMMIT'"
  fi
  pin_record >"$stage/$PIN_RECORD"
  chmod 0755 "$stage"   # mktemp -d makes it 0700; readers under another uid (sandbox) need r-x
  verify_install "$stage" || die "freshly extracted tree fails verification"
  # The staging dir and the final dir share a parent, so the rename is atomic.
  [[ ! -e $final ]] || die "$final appeared during install"
  mv -T -- "$stage" "$final"
  log "installed $final"
}

# ------------------------------------------------------- claude (Δ277) ----

# The updater's directory and the course's store, both relative to HOME. The
# apparatus file's [backend.claude] binary must be "~/$CLAUDE_STORE_REL/<version>".
CLAUDE_UPSTREAM_REL=".local/share/claude/versions"
CLAUDE_STORE_REL=".local/share/dafny-verus-learn-0/claude/versions"
# The environment `--version` runs in: the switches fvh's transport sets
# (fvh.backends.claude), so the check itself never updates anything.
CLAUDE_ENV=(env -i PATH=/usr/bin:/bin LANG=C.UTF-8 TERM=dumb DISABLE_AUTOUPDATER=1
            CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 DISABLE_TELEMETRY=1
            DISABLE_ERROR_REPORTING=1)

# Reads [backend.claude] into C_VERSION, C_BINARY, C_SHA256 (refuses a malformed pin).
claude_pins() {
  local app=${FVH_APPARATUS:-"$(dirname "$(script_dir)")/sandbox/apparatus.toml"} out
  [[ -f $app ]] || die "no apparatus file at $app"
  out=$(python3 - "$app" <<'PY'
import sys, tomllib
t = tomllib.load(open(sys.argv[1], "rb")).get("backend", {}).get("claude") or {}
print("\n".join(str(t.get(k, "")) for k in ("version", "binary", "sha256")))
PY
  ) || die "$app: unreadable apparatus file"
  { read -r C_VERSION; read -r C_BINARY; read -r C_SHA256; } <<<"$out"
  [[ $C_VERSION =~ ^[0-9]+(\.[0-9]+)+$ ]] || die "$app: [backend.claude] version '${C_VERSION}' is not a version"
  [[ $C_SHA256 =~ ^[0-9a-f]{64}$ ]] || die "$app: [backend.claude] sha256 is not 64 hex digits"
  [[ $C_BINARY == "~/$CLAUDE_STORE_REL/$C_VERSION" ]] \
    || die "$app: [backend.claude] binary is '$C_BINARY'; it must name the course's copy, ~/$CLAUDE_STORE_REL/$C_VERSION (never the updater's ~/$CLAUDE_UPSTREAM_REL/, which an auto-update deletes)"
}

# Verifies the version file $1: a regular file (no symlink), executable, the
# pinned sha256, and `--version` printing "<version> (Claude Code)".
verify_claude_file() {
  local f=$1 got out
  [[ -f $f && ! -L $f ]] || { log "not installed (or not a regular file): $f"; return 1; }
  [[ -x $f ]] || { log "not executable: $f"; return 1; }
  got=$(sha256_of "$f")
  [[ $got == "$C_SHA256" ]] || { log "$f has sha256 $got, pinned $C_SHA256"; return 1; }
  out=$("${CLAUDE_ENV[@]}" HOME="$HOME" "$f" --version 2>/dev/null | head -n 1) || true
  [[ $out == "$C_VERSION (Claude Code)" ]] || { log "$f --version: '$out', pinned '$C_VERSION (Claude Code)'"; return 1; }
}

claude_main() {
  local check=$1 store final src stage
  [[ -n ${HOME:-} && $HOME == /* ]] || die "HOME is unset or not absolute"
  need sha256sum python3
  claude_pins
  store="$HOME/$CLAUDE_STORE_REL" final="$HOME/$CLAUDE_STORE_REL/$C_VERSION"
  if (( check )); then
    verify_claude_file "$final" || die "--check failed for $final (install it with: scripts/get_toolchain.sh claude)"
    log "verified $final"
    printf '%s\n' "$final"
    return 0
  fi
  need flock
  mkdir -p -m 0755 "$store"
  trap cleanup EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  exec 9>"$store/.lock"
  flock 9 || die "cannot lock $store/.lock"
  if [[ -e $final || -L $final ]]; then
    verify_claude_file "$final" \
      || die "existing copy $final fails verification; remove it and rerun (nothing was changed)"
    log "already installed and verified: $final"
    printf '%s\n' "$final"
    return 0
  fi
  src="$HOME/$CLAUDE_UPSTREAM_REL/$C_VERSION"
  [[ -f $src ]] || die "Claude Code $C_VERSION is not in ~/$CLAUDE_UPSTREAM_REL/ (the updater may have deleted it) and the store has no copy: re-pin to a version that is there (VERSIONS.md §1.4), or put $C_VERSION back with \`claude install $C_VERSION\` (which also moves the \`claude\` link) and rerun"
  stage=$(mktemp "$store/.staging-$C_VERSION.XXXXXX")
  CLEANUP+=("$stage")
  log "copying $src"
  cp -- "$src" "$stage" || die "cannot copy $src"
  chmod 0555 "$stage"
  verify_claude_file "$stage" || die "the copy of $src fails verification (nothing was installed)"
  [[ ! -e $final ]] || die "$final appeared during install"
  mv -T -- "$stage" "$final"
  log "installed $final"
  printf '%s\n' "$final"
}

# ---------------------------------------------------------------- main -----

CLEANUP=()
cleanup() { local p; for p in "${CLEANUP[@]}"; do [[ -e $p ]] && rm -rf -- "$p"; done; return 0; }

main() {
  local tool="" check=0 a
  for a in "$@"; do
    case $a in
      dafny|verus|claude) [[ -z $tool ]] || usage; tool=$a ;;
      --check) check=1 ;;
      -h|--help) usage ;;
      *) usage ;;
    esac
  done
  [[ -n $tool ]] || usage
  if [[ $tool == claude ]]; then
    claude_main "$check"
    return 0
  fi

  select_tool "$tool"
  assert_platform
  need sha256sum find sort xargs python3
  assert_pinned "$T_TREE_FILES" "$T_TREE_SHA256" "${T_Z3S[@]}" "$DAFNY_VERSION_OUTPUT" "$VERUS_RUSTC_VERSION_OUTPUT"

  ROOT=${DVL_TOOLCHAIN_DIR:-"$(dirname "$(script_dir)")/.toolchain"}
  local final="$ROOT/$T_INSTALL"

  if (( check )); then
    verify_install "$final" || die "--check failed for $final"
    log "verified $final"
    printf '%s\n' "$final/$T_BIN_REL"
    return 0
  fi

  need curl unzip flock
  mkdir -p "$ROOT"
  trap cleanup EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM   # route signals through exit so the EXIT cleanup runs
  exec 9>"$ROOT/.lock-$T_NAME"
  flock 9 || die "cannot lock $ROOT/.lock-$T_NAME"

  if [[ -e $final ]]; then
    verify_install "$final" \
      || die "existing install $final fails verification; remove it and rerun (nothing was changed)"
    log "already installed and verified: $final"
  else
    install_tool
  fi
  printf '%s\n' "$final/$T_BIN_REL"
}

# Sourcing the script (for tests) defines the functions without running main.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
