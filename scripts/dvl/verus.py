"""dvl.verus: the Verus half of the pinned verifier wrapper (phase DV1b).

The tools (scripts/vcheck, scripts/vaudit, specfreeze, firsttry, pins.py, CI)
call this module; nothing else runs Verus. It implements the interface fixed
for both language libraries (types and plumbing in dvl.common):

  verify(target, gate=False, symbol=None, seed=None, isolate=False) -> Result
  holes(target) -> list[Hole]              tool-counted (--no-cheating), never grep
  audit(target) -> list[Finding]           --no-cheating over the crate and its path
                                           dependencies + lint + trust allowlist
  lint(paths, mode) -> list[Finding]       mode: learner | reference | agent
  spec_hash(path, symbols=None) -> {symbol: sha256}
  freeze_check(frozen, candidate) -> list[Finding]
  test(target, names=None) -> Result       verus --compile --test, then the binary
  run_bin(target, args=()) -> (Result, BinRun | None)
                                           a crate's [[bin]] target: the library
                                           verified and compiled, the binary root
                                           compiled against it (verus --compile),
                                           then run with args (D16)
  empty_body(target, item_symbol) -> Result  the item must FAIL in every mode
                                           (modes=['RGN']: a twin's learner regions
                                           blanked, QPLAN §6 Q18)

Also public: check_args (the argument policy), lint_source and lint_manifest
(lint over one text or one Cargo.toml), normalize_output (the canonical form
of a run for pins.py goldens), rlimit_counts (per-function Z3 rlimit from
--time JSON, the Δ59 brittleness metric), proof_notes (the obligation
and failed proof_note label sets, Δ38), eb_variant (one empty-body
rewrite), message_id (VERSIONS.md ids), load_trust and check_trust (the
trust allowlist and its CI check), and the exceptions Refused, TrustError and
HoleCountError (holes() raises it rather than return an uncounted []).

Each also takes keyword-only options documented on the function. A target is
a crate directory (with Cargo.toml), a file of a crate (its crate; or the file
as its own crate root when no `mod` declaration reaches it, as for exit.rs and
agent.rs), a standalone .rs file, or a *.rs.specimen (copied into scratch as
.rs; one under specimens/<ID>/ gets its module's given layer chain).

How a run is made (DELTAS):
  * Verus is called directly, one `verus` process per crate; cargo-verus is
    never used, so its content cache can never answer (Δ19, V25).
  * Environment: built from nothing (dvl.common.run_capped runs `env -i`):
    common.default_env() plus PATH with the rustup bin directory,
    RUSTUP_TOOLCHAIN = the pinned Rust toolchain (Δ42), TMPDIR, and
    RUSTUP_HOME/CARGO_HOME when the caller sets them. VERUS_Z3_PATH,
    VERUS_EXTRA_ARGS, RUSTFLAGS and RUSTC_WRAPPER never reach a job (Δ13, Δ21).
  * Flags: `--rlimit <pin> --num-threads <pin> --output-json
    --error-format=json` (+ `--time` for per-function results), and
    `--no-cheating` on every verify/holes/audit run. The only --smt-option is
    `<seed_smt_option>=<int>` (an unknown option panics, exit 134).
    check_args refuses everything else a caller passes, the pinned
    refused_args (Δ13) by name.
  * Layer chains (Δ22, Δ25): a crate's path dependencies (its Cargo.toml;
    `vstd` is the release's bundled vstd) are verified first, lowest first,
    each with `--import` of every lower crate's .vir, `--extern` of every
    lower crate's rlib, and `--export <PATH> --crate-name <name> --compile`.
    A specimen's chain, and a standalone file's under `layer=`, are the
    given crates under <course root>/verus/given/, the course root being the
    caller's `root=` (vcheck's --root) or else the target's own (its nearest
    ancestor holding MODULES.toml; root_for), never the scripts' checkout
    unless the target lies in no course tree. The default trust allowlist
    is <course root>/expected/verus_trust.toml, its paths relative to it.
  * Memory and time (Δ57, Δ58, CLAUDE.md §Resources): every job goes through
    common.run_capped (systemd-run --user --scope, MemoryMax = the pinned
    mem_gb, at least 16G, MemorySwapMax=0; at most DVL_VERUS_JOBS jobs at
    once across processes, default 1). Exit 137/143 is `killed(memory)`,
    never a verdict; the wall-clock safety kill (exit 124) is `inconclusive`,
    never a success.
  * Output channels (Δ37): --output-json on stdout, one rustc JSON
    diagnostic per line on stderr; JSON key order and note-list order vary
    between runs, so everything read is sorted.
  * Scratch (Δ26, Δ32 practice): a run keeps only its job logs
    (<nn>-<step>/{cmd,stdout,stderr,exit}.txt). Specimen copies, empty-body
    variants, the dependency chain's .vir/.rlib exports and test binaries are
    deleted when the call returns, so no source or statement of a target (a
    reference twin included) stays in the shared scratch root.

Verdicts (spec §6.5, the asymmetric referee): verified; failed (an error at
a location, a front-end error, a failed gate condition); inconclusive (every
error is an rlimit hit, or the wall-clock kill); refused (no tool ran);
killed(memory); error (no verdict: CLI error 255, panic 134, unreadable
output, a dependency that did not build). Stages: cli, parse, resolve (rustc
and VIR front end), verify, compile (code generation after a verification
that found nothing: a --compile run whose errors come from rustc's later
passes), link (the same, when the native linker failed), test, run.

The hole counter (Δ7, Δ8): holes = the --no-cheating diagnostics W-V07
(assume/admit), W-V08 (external_body, assume_specification, axiom fn,
uninterp and bodyless spec fns, external fn/trait specifications) and W-V09
(assume_termination); the final `aborting due to` line (W-V14) never counts.
Real verification errors come in the same run, beside the holes. A hole's
label is its `#[verifier::proof_note("<id>")] assume(false);` note when it
has one (Δ7: the only label the tool reports; proof_note never attaches to
admit(), which the lint flags), else the item id whose block holds it, else
the enclosing fn.

Dependency holes (captured on the pin, 2026-10-04): under --no-cheating a
crate's run reports a dependency's external_body (or assume_specification)
fn once wherever the crate calls it, and never a dependency's assume or
admit; such a run omits `verified`, `errors` and
`is-verifying-entire-crate`. Holes whose file lies outside the target's own
files are therefore dependency holes, never the unit's: each is matched
against the trust allowlist (load_trust); a trusted one becomes an info
diagnostic (trusted-dependency-hole), any other a `dependency-hole` finding.

The done gate (Δ12, Δ11, Δ40, Δ41): one --no-cheating --output-json run; it
passes only with exit 0, `success` present and true,
`is-verifying-entire-crate` true, `encountered-vir-error` present and false,
`verified` >= the unit's minimum (default 1: never exit 0 alone), no hole,
no untrusted dependency hole, and the lint at zero over the crate's files. A
missing key fails; a partial (--verify-*) run never passes (the gate refuses
a symbol). `verified` counts function bodies with obligations, loops and
nonlinear asserts (Δ40). One exception to the single run: when the
--no-cheating run shows no own hole, no error and only trusted dependency
holes, a second run of the same command without --no-cheating supplies the
record (its step is also named `target`, so it is the last target job); the
first run has already shown the target hole-free (Δ7: every cheat site in one
run).
"""

from __future__ import annotations

import concurrent.futures
import functools
import json
import os
import re
import shutil
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import common
from . import verus_spec as vs

_SCRIPTS = Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import course_items as ci  # noqa: E402  the ONE item-marker parser
import gen_units           # noqa: E402  layer names, module -> layer

Diag, Hole, Finding, Result = common.Diag, common.Hole, common.Finding, common.Result

LANG = "verus"
REPO = common.REPO_ROOT
MODES = ("learner", "reference", "agent")


class Refused(ValueError):
    """The wrapper refuses this target or request (no tool runs)."""


def pins():
    """The [verus] section of scripts/dvl/pins.toml (common.load_pins())."""
    p = common.load_pins()["verus"]
    if p["mem_gb"] < 16:
        raise common.DvlError("pins.toml [verus] mem_gb must be at least 16 (Δ57)")
    for k in ("rust_toolchain", "seed_smt_option", "refused_args"):
        if k not in p:
            raise common.DvlError(f"pins.toml [verus] lacks {k}")
    for mode, s in (p.get("eb_mode_timeout_s") or {}).items():
        if mode not in EB_MODES or isinstance(s, bool) or not isinstance(s, int) or \
                not 0 < s <= p["wall_clock_s"]:
            raise common.DvlError(f"pins.toml [verus] eb_mode_timeout_s: {mode} = {s!r} (an "
                                  "empty-body mode, and seconds within the wall-clock net)")
    return p


# --- message ids (VERSIONS.md §2.4 through pins.toml [verus.messages]/[verus.patterns]) -----

# The W-V05 and W-V14 variants captured on the pin by the DV1b Verus lane (any
# rlimit context; the warning count after an abort) live in pins.toml
# [verus.patterns] since DV1c, like every other wording.
HOLE_IDS = ("W-V07", "W-V08", "W-V09")
RLIMIT_ID = "W-V05"
ABORT_ID = "W-V14"
FRONT_END_IDS = {"W-V10", "W-V13", "W-V17", "W-V19", "W-V21", "W-V22"}
LEVELS = {"error": "error", "warning": "warning", "note": "info", "help": "hint"}


@functools.lru_cache(maxsize=1)
def _matchers():
    p = pins()
    exact = {}
    for mid, text in p["messages"].items():
        exact.setdefault(text.split("\n")[0], mid)
    pats = [(mid, re.compile(rx)) for mid, rx in p.get("patterns", {}).items()]
    return exact, pats


def message_id(line):
    """The VERSIONS.md id of a rendered first line (`error: …`, `Error: …`,
    or a plain line), else ""."""
    exact, pats = _matchers()
    line = line.split("\n")[0].rstrip()
    if line in exact:
        return exact[line]
    for mid, rx in pats:
        if rx.match(line):
            return mid
    return ""


def json_message_id(d):
    """message_id for a rustc JSON diagnostic (rendered as `<level>: <message>`)."""
    return message_id(f"{d.get('level', 'error')}: {d.get('message', '')}")


# --- argument policy (Δ13) ---------------------------------------------------------------

VALUED = {"--multiple-errors", "--triggers-mode", "--rlimit", "--smt-option", "--log",
          "--log-dir", "--export", "--import", "--extern", "--num-threads", "--verify-module",
          "--verify-only-module", "--verify-function", "--crate-type", "--crate-name", "-o",
          "--out-dir", "-L", "--cfg", "--edition", "--target", "-V"}
LEARNER_ONLY = {"--expand-errors", "--multiple-errors", "--triggers", "--triggers-mode"}
TRIGGERS_MODES = {"silent", "selective", "all-modules", "verbose", "verbose-all-modules"}
WHY = {
    "--no-verify": "verifies nothing and still exits 0 (V18, Δ11)",
    "--no-lifetime": "skips the ghost-ownership pass (V16)",
    "--no-erasure-check": "skips the erasure check (V16)",
    "-V no-solver-version-check": "lets any Z3 run silently (V24, Δ21)",
    "-V allow-inline-air": "is POTENTIALLY UNSOUND (V17)",
}


def split_args(args):
    """[(flag, value or None)] from a caller's argument list."""
    out, args, i = [], [str(a) for a in args], 0
    while i < len(args):
        a = args[i]
        if a.startswith("-V") and a != "-V":
            out.append(("-V", a[2:].lstrip("=")))
        elif a.startswith("--") and "=" in a:
            flag, _, val = a.partition("=")
            out.append((flag, val))
        elif a in VALUED:
            out.append((a, args[i + 1] if i + 1 < len(args) else None))
            i += 1
        else:
            out.append((a, None))
        i += 1
    return out


def check_args(args, gate=False):
    """Refusal reasons for caller-supplied Verus arguments (empty = allowed).
    Allowed outside the gate: --expand-errors, --multiple-errors N,
    --triggers, --triggers-mode M, --rlimit <the pin> and --smt-option
    <seed option>=<int>; in the gate only the last two. The pinned
    refused_args are refused by name (Δ13); everything else as not allowed."""
    p = pins()
    refused = set(p["refused_args"])
    reasons = []
    for flag, val in split_args(args):
        shown = f"{flag} {val}" if flag == "-V" else flag
        if shown in refused:
            reasons.append(f"{shown}: refused by the pins ({WHY.get(shown, 'Δ13')})")
        elif flag == "-V":
            reasons.append(f"-V {val}: extended options are not part of the pin")
        elif flag.startswith("--verify-"):
            reasons.append(f"{flag}: " + ("a partial run never passes the gate (Δ12, Δ41)" if gate
                                          else "per-symbol runs go through the symbol argument"))
        elif flag == "--rlimit":
            try:
                ok = val is not None and float(val) == float(p["rlimit"])
            except ValueError:
                ok = False
            if not ok:
                reasons.append(f"--rlimit {val}: only the pinned --rlimit {p['rlimit']} "
                               "(V22 rlimit inflation, Δ13)")
        elif flag == "--smt-option":
            if not re.fullmatch(re.escape(p["seed_smt_option"]) + r"=\d+", val or ""):
                reasons.append(f"--smt-option {val}: only {p['seed_smt_option']}=<int> (an "
                               "unknown option panics, exit 134; Δ13)")
        elif flag in LEARNER_ONLY:
            if gate:
                reasons.append(f"{flag}: not part of the gate's pinned command")
            elif flag == "--multiple-errors" and not (val or "").isdigit():
                reasons.append(f"--multiple-errors {val}: an integer")
            elif flag == "--triggers-mode" and val not in TRIGGERS_MODES:
                reasons.append(f"--triggers-mode {val}: one of " +
                               ", ".join(sorted(TRIGGERS_MODES)))
        else:
            reasons.append(f"{flag}: not an allowed Verus option")
    return reasons


def _passthrough(args):
    """The allowed caller arguments verify() forwards (the pinned --rlimit is
    always passed, so a caller's copy is dropped)."""
    out = []
    for flag, val in split_args(args):
        if flag != "--rlimit":
            out += [flag] if val is None else [flag, val]
    return out


# --- runs and jobs --------------------------------------------------------------------------

@dataclass
class Run:
    dir: Path
    target: str = ""
    pathmap: list = field(default_factory=list)   # [(scratch path, original path)]
    files: list = field(default_factory=list)     # the plan's [(file as compiled, modpath, test)]
    steps: int = 0

    def orig(self, p):
        """An absolute path as the user knows it (scratch copies mapped back)."""
        if not p:
            return ""
        q = Path(p)
        if not q.is_absolute():
            q = self.dir / q
        s = os.path.normpath(str(q))
        for scratch, orig in sorted(self.pathmap, key=lambda x: -len(x[0])):
            if s == scratch:
                return orig
            if s.startswith(scratch.rstrip("/") + "/"):
                return orig.rstrip("/") + s[len(scratch.rstrip("/")):]
        return s


KEEP_LOGS = {"cmd.txt", "stdout.txt", "stderr.txt", "exit.txt"}
STEP_DIR = re.compile(r"\d{2,}-")


def _rm(p):
    if p.is_dir() and not p.is_symlink():
        shutil.rmtree(p, ignore_errors=True)
    else:
        try:
            p.unlink()
        except FileNotFoundError:
            pass


def _discard(run):
    """Delete everything of a run but its job logs (<nn>-<step>/ with cmd,
    stdout, stderr and exit): specimen and variant copies, deps/ (.vir and
    .rlib exports: a statement leak, Δ26), test binaries and stray temp
    files (Δ32 practice). Only ever inside the scratch root."""
    d = Path(run.dir)
    try:
        inside = d.resolve().is_relative_to(common.scratch_root().resolve())
    except (OSError, common.DvlError):
        inside = False
    if not inside or not d.is_dir():
        return
    for x in d.iterdir():
        if x.is_dir() and not x.is_symlink() and STEP_DIR.match(x.name):
            for y in x.iterdir():
                if y.name not in KEEP_LOGS:
                    _rm(y)
        else:
            _rm(x)
    try:
        d.rmdir()                         # a run that never ran a job leaves nothing
    except OSError:
        pass


def job_env(run_dir):
    """The complete environment of every Verus job (Δ13, Δ21, Δ42)."""
    p = pins()
    env = common.default_env()
    home = env.get("HOME") or "/tmp"
    cargo_home = os.environ.get("CARGO_HOME") or os.path.join(home, ".cargo")
    env["PATH"] = f"{cargo_home}/bin:{env.get('PATH', '/usr/bin:/bin')}"
    env["RUSTUP_TOOLCHAIN"] = common.rust_toolchain()   # the pinned Rust, for this host (D77)
    env["TMPDIR"] = str(run_dir)
    for k in ("RUSTUP_HOME", "CARGO_HOME"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    for k in p["scrub_env"]:
        if k in env:
            raise common.DvlError(f"{k} would reach a Verus job")
    return env


@dataclass
class Job:
    step: str
    argv: list
    exit: int
    out: str
    err: str
    raw: Path

    @property
    def killed(self):
        if common.is_killed(self.exit):
            return "memory"
        if self.exit == common.WALL_CLOCK_EXIT:
            return "wallclock"
        return None


def _job(run, step, argv, timeout_s=None):
    """One capped Verus job; its raw files land in <run>/<nn>-<step>/."""
    p = pins()
    limit = p["wall_clock_s"] if timeout_s is None else min(timeout_s, p["wall_clock_s"])
    run.steps += 1
    raw = run.dir / f"{run.steps:02d}-{step}"
    argv = [str(a) for a in argv]
    rc, so, se = common.run_capped(argv, p["mem_gb"], limit, env=job_env(run.dir), cwd=run.dir,
                                   pool="verus", out_dir=raw)
    return Job(step, argv, rc, Path(so).read_text(errors="replace"),
               Path(se).read_text(errors="replace"), raw)


def verus_bin(fresh=False):
    """The pinned verus binary, after get_toolchain.sh verus --check."""
    return common.toolchain("verus", fresh=fresh)["verus"]


# --- crates and targets --------------------------------------------------------------------

@dataclass
class Crate:
    name: str
    root: Path
    dir: Path | None
    deps: list = field(default_factory=list)       # direct path dependencies

    def chain(self):
        """Transitive path dependencies, lowest first, each once."""
        out = []

        def rec(c):
            for d in c.deps:
                rec(d)
                if all(x.name != d.name for x in out):
                    out.append(d)
        rec(self)
        return out


def _crate_name(s):
    n = re.sub(r"\W", "_", s).lower()
    return n if n and not n[0].isdigit() else f"c_{n}"


def load_crate(cdir, _stack=()):
    """A Crate from a directory's Cargo.toml: its library root and its path
    dependencies (vstd is the release's own; anything else is refused)."""
    cdir = Path(cdir).resolve()
    if cdir in _stack:
        raise Refused(f"dependency cycle through {cdir}")
    manifest = cdir / "Cargo.toml"
    try:
        meta = tomllib.loads(manifest.read_text())
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise Refused(f"{manifest}: unreadable ({e})") from None
    if "patch" in meta:
        raise Refused(f"{manifest}: a [patch] section changes what the verifier sees (Δ20)")
    lib = meta.get("lib", {})
    name = _crate_name(lib.get("name") or meta.get("package", {}).get("name") or cdir.name)
    root = cdir / lib.get("path", "src/lib.rs")
    if not root.is_file():
        raise Refused(f"{cdir}: no library root {root}")
    deps = []
    for key, spec in sorted(meta.get("dependencies", {}).items()):
        if key == "vstd":
            continue
        if not isinstance(spec, dict) or "path" not in spec:
            raise Refused(f"{manifest}: dependency {key} is neither vstd nor a path dependency")
        if "package" in spec:
            raise Refused(f"{manifest}: dependency {key} is renamed")
        dep = load_crate(cdir / spec["path"], _stack + (cdir,))
        if dep.name != _crate_name(key):
            raise Refused(f"{manifest}: dependency {key} names crate {dep.name}")
        deps.append(dep)
    return Crate(name, root.resolve(), cdir, deps)


def crate_files(root):
    """[(file, module path, test_only)] reachable from a crate root through
    `mod x;` declarations (a `#[cfg(test)] mod` marks its subtree test-only).
    `#[path]` is not followed; the lint flags it."""
    out, seen = [], set()

    def rec(f, modpath, is_root, test_only):
        f = f.resolve()
        if f in seen or not f.is_file():
            return
        seen.add(f)
        out.append((f, modpath, test_only))
        try:
            src = vs.parse(f.read_text())
        except (vs.ParseError, OSError, UnicodeDecodeError):
            return
        base = f.parent if is_root or f.name == "mod.rs" else f.parent / f.stem
        for segs, it in vs.mod_decls(src):
            t_only = test_only or any(vs.attr_text(src, a) == "cfg(test)" for a in it.attrs)
            d = base.joinpath(*segs[:-1])
            for cand in (d / f"{segs[-1]}.rs", d / segs[-1] / "mod.rs"):
                if cand.is_file():
                    rec(cand, "::".join(filter(None, [modpath] + segs)), False, t_only)
                    break
    rec(Path(root), "", True, False)
    return out


@dataclass
class Plan:
    crate: Crate          # the crate verified (its root may be a scratch copy)
    files: list           # [(file as compiled, module path, test_only)]
    standalone: bool
    layer: str | None = None


SPECIMEN_DIR = re.compile(r"(?:^|/)specimens/([QR]\d\d)/")
WORKSPACE_REL = Path("verus") / "Cargo.toml"     # the generated workspace (never a crate)
GIVEN_REL = Path("verus") / "given"              # the given layer crates, under a course root
# An override of <course root>/verus/given for every target (tests point it at
# a fixture tree); None = the target's own course root decides (given_root).
GIVEN_ROOT = None


def course_root(path):
    """The course tree a path belongs to: its nearest ancestor holding
    MODULES.toml, else None."""
    p = Path(path)
    p = (p if p.is_absolute() else Path.cwd() / p).resolve()
    for d in [p] + list(p.parents):
        if (d / "MODULES.toml").is_file():
            return d
    return None


def root_for(target, root=None):
    """The course root a target's layer chain and trust allowlist come from:
    `root` when the caller names one (vcheck's --root: a probe or a copy that
    lies outside the tree), else the target's own course root, else the
    scripts' checkout (a target in no course tree)."""
    if root is not None:
        return Path(root).resolve()
    return course_root(target) or REPO


def given_root(root):
    """The directory of the given layer crates of a course root."""
    return Path(GIVEN_ROOT) if GIVEN_ROOT is not None else Path(root) / GIVEN_REL


def _find_crate_dir(f, root):
    """The nearest directory at or above f's holding a crate manifest (a
    Cargo.toml with [package]; the course's workspace manifest is skipped),
    looking no higher than the course root."""
    d = f.parent
    workspace = (Path(root) / WORKSPACE_REL).resolve()
    while True:
        m = d / "Cargo.toml"
        if m.is_file() and m.resolve() != workspace:
            try:
                if "package" in tomllib.loads(m.read_text()):
                    return d
            except (OSError, tomllib.TOMLDecodeError):
                return d
        if d == d.parent or d == Path(root):
            return None
        d = d.parent


def _layer_crates(layer, root):
    """The given crates of a layer chain that exist under the course root's
    verus/given/ (given_root)."""
    out = []
    groot = given_root(root)
    for l in gen_units.layer_chain(layer):
        d = groot / gen_units.verus_layer_crate(l)
        if (d / "Cargo.toml").is_file():
            out.append(load_crate(d))
    return out


def resolve(target, run, layer=None, root=None):
    """The Plan for a target (see the module docstring). Raises Refused.
    Layer chains (a specimen's, or a standalone file's with `layer`) come
    from the given crates of root_for(target, root): relative to the
    target's course root, never to the scripts' checkout."""
    t = Path(target)
    t = (t if t.is_absolute() else Path.cwd() / t)
    if not t.exists():
        raise Refused(f"{target}: no such file or directory")
    t = t.resolve()
    croot = root_for(t, root)
    if t.is_dir():
        if not (t / "Cargo.toml").is_file():
            raise Refused(f"{target}: a directory target must be a crate (it has no Cargo.toml)")
        c = load_crate(t)
        return Plan(c, crate_files(c.root), False, layer)
    if t.name.endswith(".rs.specimen"):
        stem = t.name[:-len(".rs.specimen")]
        dst = run.dir / "src" / f"{stem}.rs"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(t, dst)
        run.pathmap.append((str(dst), str(t)))
        m = SPECIMEN_DIR.search(t.as_posix())
        lay = layer or (gen_units.expected_layer(m.group(1)) if m else None)
        crate = Crate(_crate_name(stem), dst, None, _layer_crates(lay, croot) if lay else [])
        return Plan(crate, [(dst, "", False)], True, lay)
    if not t.name.endswith(".rs"):
        raise Refused(f"{target}: not a Verus source (.rs or .rs.specimen)")
    cdir = _find_crate_dir(t, croot)
    if cdir is not None:
        c = load_crate(cdir)
        files = crate_files(c.root)
        if any(f == t for f, _, _ in files):
            return Plan(c, files, False, layer)
        own = Crate(_crate_name(f"{c.name}_{t.stem}"), t, cdir, c.deps)
        return Plan(own, crate_files(t), True, layer)
    deps = _layer_crates(layer, croot) if layer else []
    return Plan(Crate(_crate_name(t.stem), t, None, deps), crate_files(t), True, layer)


def _link_args(crate, outdir):
    args = []
    for d in crate.chain():
        args += ["--import", f"{d.name}={outdir}/{d.name}.vir",
                 "--extern", f"{d.name}={outdir}/lib{d.name}.rlib"]
    return args + (["-L", str(outdir)] if args else [])


def _base_args(p, seed=None, rlimit=None):
    a = ["--rlimit", str(p["rlimit"] if rlimit is None else rlimit),
         "--num-threads", str(p["num_threads"])]
    if seed is not None:
        a += ["--smt-option", f"{p['seed_smt_option']}={int(seed)}"]
    return a


def _build_chain(run, crate, seed=None, timeout_s=None):
    """Verify and export every path dependency, lowest first. None on
    success, else the failing Result (verdict error, or killed(memory))."""
    p = pins()
    outdir = run.dir / "deps"
    outdir.mkdir(exist_ok=True)
    for d in crate.chain():
        argv = [verus_bin(), d.root, "--crate-type=lib", "--crate-name", d.name,
                *_base_args(p, seed), *_link_args(d, outdir), "--export", outdir / f"{d.name}.vir",
                "--compile", "--out-dir", outdir, "--output-json", "--error-format=json"]
        job = _job(run, f"dep-{d.name}", argv, timeout_s)
        if job.exit != 0:
            res = _classify(run, job, d.name, False, None, [], None)
            res.diagnostics.insert(0, Diag(str(d.root), 0, 0, "error",
                                           f"dependency crate {d.name} did not verify and build; "
                                           "nothing of the target was checked", "dependency"))
            if res.verdict != "killed(memory)":
                res.verdict = "error"
            return res
    return None


def _refused(target, message):
    return Result(LANG, str(target), None, "refused", "cli",
                  findings=[Finding(str(target), 0, "refused", message)])


def _toolchain_error(target, e):
    return Result(LANG, str(target), None, "error", "cli",
                  findings=[Finding(str(target), 0, "toolchain", str(e))])


# --- output parsing ---------------------------------------------------------------------------

def parse_json_doc(text):
    """The --output-json document on stdout, or None."""
    s = text.strip()
    if not s:
        return None
    for k in (0, s.find("{")):
        if k < 0:
            continue
        try:
            d = json.loads(s[k:])
            return d if isinstance(d, dict) else None
        except json.JSONDecodeError:
            continue
    return None


def parse_stderr(text):
    """(rustc JSON diagnostics, other non-empty lines) from stderr."""
    diags, raw = [], []
    for line in text.splitlines():
        if line.startswith("{"):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                d = None
            if isinstance(d, dict) and "message" in d:
                diags.append(d)
                continue
        if line.strip():
            raw.append(line)
    return diags, raw


def _primary(d):
    spans = d.get("spans") or []
    for s in spans:
        if s.get("is_primary"):
            return s
    return spans[0] if spans else None


def _highlight(span):
    if not span or not span.get("text"):
        return ""
    t = span["text"][0]
    return t["text"][t["highlight_start"] - 1:t["highlight_end"] - 1]


def _to_diag(run, d):
    sp = _primary(d)
    code = json_message_id(d)
    if not code and isinstance(d.get("code"), dict):
        code = d["code"].get("code") or ""
    sev = LEVELS.get(d.get("level", "error"), "info")
    if sp:
        return Diag(run.orig(sp.get("file_name", "")), sp.get("line_start", 0),
                    sp.get("column_start", 0), sev, d.get("message", ""), code)
    return Diag("", 0, 0, sev, d.get("message", ""), code)


class _Sources:
    """Parsed sources by path (the paths Verus saw), parsed once."""

    def __init__(self):
        self.cache = {}

    def get(self, path):
        if path not in self.cache:
            try:
                self.cache[path] = vs.parse(Path(path).read_text())
            except (OSError, vs.ParseError, UnicodeDecodeError):
                self.cache[path] = None
        return self.cache[path]


def _enclosing(src, line):
    """Items whose extent covers a line, outermost first."""
    out = []
    for it in src.walk():
        if it.kind == "macro":
            continue
        if src.line_of(it.start) <= line <= src.line_of(max(it.end - 1, it.start)):
            out.append(it)
    return out


def _fn_at(src, line):
    if src is None:
        return None
    best = None
    for it in _enclosing(src, line):
        if it.kind in ("fn", "assume_specification"):
            best = it
    return best


def _hole_kind(run, d, srcs):
    mid = json_message_id(d)
    sp = _primary(d)
    hl = _highlight(sp)
    if mid == "W-V07":
        return "admit" if hl.startswith("admit") else "assume"
    if mid == "W-V09":
        return "assume_termination"
    words = set(re.findall(r"[A-Za-z_]+", hl))
    for w in ("assume_specification", "uninterp", "axiom"):
        if w in words:
            return w
    src = None
    if sp and sp.get("file_name"):
        src = srcs.get(_compiled(run, run.orig(sp["file_name"]))[0])
    if src is not None:
        for it in reversed(_enclosing(src, sp["line_start"])):
            attrs = [vs.attr_text(src, a) for a in it.attrs]
            if any("external_fn_specification" in a for a in attrs):
                return "external_fn_specification"
            if any("external_trait_specification" in a for a in attrs):
                return "external_trait_specification"
            if it.kind == "fn" and it.mode == "spec" and not it.body:
                return "bodyless_spec"
    return "external_body"


def _compiled(run, shown):
    """(compiled path, module path) for a file as shown to the user."""
    for f, modpath, _ in run.files:
        if run.orig(str(f)) == shown or str(f) == shown:
            return str(f), modpath
    return shown, ""


def _label(run, srcs, file_shown, line, note):
    """A hole's label: its proof_note, else the item id whose block holds it,
    else the enclosing fn's symbol, else ""."""
    if note:
        return note
    path, _ = _compiled(run, file_shown)
    try:
        items, _ = ci.parse_items(path, Path(path).read_text())
    except (OSError, UnicodeDecodeError):
        items = []
    for it in items:
        if it["line_start"] <= line <= it["line_end"]:
            return it["id"]
    fn = _fn_at(srcs.get(path), line)
    return vs.item_symbol(fn) if fn else ""


def _holes(run, jdiags, srcs):
    out = []
    for d in jdiags:
        if json_message_id(d) not in HOLE_IDS:
            continue
        sp = _primary(d)
        note = ""
        for s in d.get("spans") or []:
            lab = s.get("label") or ""
            if lab.startswith("note: "):
                note = lab[len("note: "):]
        shown = run.orig(sp["file_name"]) if sp else ""
        line = sp["line_start"] if sp else 0
        out.append(Hole(shown, line, sp["column_start"] if sp else 0, _hole_kind(run, d, srcs),
                        _label(run, srcs, shown, line, note)))
    out.sort(key=lambda h: (h.file, h.line, h.col))
    return out


def _smt_breakdown(jd):
    """{function: success} from --time JSON, or None when absent."""
    smt = ((jd or {}).get("times-ms") or {}).get("smt")
    if not isinstance(smt, dict):
        return None
    out = {}
    for m in smt.get("smt-run-module-times") or []:
        for fb in m.get("function-breakdown") or []:
            out[fb["function"]] = bool(fb.get("success"))
    return out


def rlimit_counts(stdout_text):
    """{function: Z3 rlimit count} from a run's --time JSON (Δ59: the
    brittleness metric is the per-function rlimit; compare runs under
    different seeds). Empty when the run printed no SMT breakdown (a
    --no-cheating run that met a hole prints none)."""
    jd = parse_json_doc(stdout_text)
    smt = ((jd or {}).get("times-ms") or {}).get("smt")
    out = {}
    if isinstance(smt, dict):
        for m in smt.get("smt-run-module-times") or []:
            for fb in m.get("function-breakdown") or []:
                out[fb["function"]] = fb.get("rlimit")
    return out


def proof_notes(stdout_text):
    """(obligation labels, failed labels) as sets, from the func-details of
    a run's --output-json (Δ37, Δ38: list order varies, so compare sets;
    --multiple-errors 2, the default, lists every failing label)."""
    jd = parse_json_doc(stdout_text)
    obl, failed = set(), set()
    for v in ((jd or {}).get("func-details") or {}).values():
        obl.update(v.get("obligation_proof_notes") or [])
        failed.update(v.get("failed_proof_notes") or [])
    return obl, failed


def _sym_key(crate_name, verus_name):
    """A Verus function name without its crate prefix (the symbol syntax)."""
    pre = crate_name + "::"
    return verus_name[len(pre):] if verus_name.startswith(pre) else None


def _symbol_of(run, srcs, file_shown, line):
    path, modpath = _compiled(run, file_shown)
    fn = _fn_at(srcs.get(path), line)
    return "::".join(filter(None, [modpath, vs.item_symbol(fn)])) if fn else None


def _a(word):
    """`a <word>` or `an <word>`."""
    return ("an " if word[:1] in "aeiou" else "a ") + word


def _hole_symbol(run, srcs, h):
    """The symbol (within its file) of the fn or assume_specification whose
    extent holds a hole, else ""."""
    path, _ = _compiled(run, h.file)
    fn = _fn_at(srcs.get(path), h.line)
    return vs.item_symbol(fn) if fn else ""


def _match_trust(run, srcs, holes, trust):
    """([(hole, symbol)] trusted, [(hole, symbol)] not) against the trust
    allowlist; every matching entry is marked used (`_used`)."""
    yes, no = [], []
    for h in holes:
        sym = _hole_symbol(run, srcs, h)
        ab = str(Path(h.file).resolve()) if h.file else ""
        hit = [e for e in trust if e["_abs"] == ab and e["kind"] == h.kind and e["symbol"] == sym]
        for e in hit:
            e["_used"] = True
        (yes if hit else no).append((h, sym))
    return yes, no


def _split_dependency_holes(run, srcs, holes, own, trust):
    """(own holes, dependency-hole findings, trusted-dependency info diags):
    a hole whose file is not one of `own` (the target's files as shown) lies
    in a dependency crate, never the unit's (module docstring)."""
    if own is None:
        return holes, [], []
    mine = [h for h in holes if h.file in own]
    yes, no = _match_trust(run, srcs, [h for h in holes if h.file not in own], trust or [])
    found = [Finding(h.file, h.line, "dependency-hole",
                     f"{_a(h.kind)} hole in a dependency crate (in {sym or 'an item'}), not on the "
                     "trust allowlist: not this unit's hole, but nothing that trusts it is done")
             for h, sym in no]
    info = [Diag(h.file, h.line, h.col, "info",
                 f"trusted dependency hole: {h.kind} (in {sym or 'an item'}), on the trust "
                 "allowlist", "trusted-dependency-hole") for h, sym in yes]
    return mine, found, info


def _classify(run, job, crate_name, gate, min_verified, findings, partial, srcs=None, *,
              own=None, trust=None):
    """One target job → Result (verdicts and stages: the module docstring).
    own: the target's own files as shown (None: every hole is the target's);
    holes elsewhere are dependency holes, matched against `trust`."""
    srcs = srcs or _Sources()
    jd = parse_json_doc(job.out)
    jdiags, raw = parse_stderr(job.err)
    all_holes = _holes(run, jdiags, srcs)
    holes, dep_found, dep_info = _split_dependency_holes(run, srcs, all_holes, own, trust)
    findings = list(findings) + dep_found
    diags = list(dep_info)
    for d in jdiags:
        mid = json_message_id(d)
        if mid == ABORT_ID or mid in HOLE_IDS or d.get("level") == "failure-note":
            continue
        if partial and d.get("level") == "note" and d.get("message", "").startswith("verifying "):
            continue
        diags.append(_to_diag(run, d))
    for line in raw:
        mid = message_id(line)
        if mid or line.startswith(("Error", "error")) or "panicked" in line:
            diags.append(Diag("", 0, 0, "error", line.strip(), mid))
    vr = (jd or {}).get("verification-results")
    vr = vr if isinstance(vr, dict) else None
    verified = vr.get("verified") if vr else None
    real = [d for d in diags if d.severity == "error"]
    per = {}

    def res(verdict, stage, extra=()):
        return Result(LANG, run.target, job.exit, verdict, stage, verified, holes,
                      diags + list(extra), list(findings), per, str(run.dir), job.argv)

    if job.killed == "memory":
        return res("killed(memory)", "verify", [Diag(
            "", 0, 0, "error", f"killed by a signal (exit {job.exit}; a memory kill): "
            "not a verdict (Δ57)", "killed(memory)")])
    if job.killed == "wallclock":
        return res("inconclusive", "verify", [Diag(
            "", 0, 0, "error", "killed by the wall-clock safety net: a failure, never a success "
            "(Δ58)", "wall-clock-kill")])
    if job.exit == 255:
        return res("error", "cli")
    if job.exit == 134:
        return res("error", "cli", [] if any(d.code == "W-V25" for d in diags) else [Diag(
            "", 0, 0, "error", "verus panicked (exit 134): not a verdict (Δ13)", "panic")])
    if job.exit not in (0, 1):
        return res("error", "cli", [Diag("", 0, 0, "error", f"unexpected exit code {job.exit}",
                                         "exit")])
    if vr is None:
        return res("error", "parse" if real else "cli", [Diag(
            "", 0, 0, "error", "no --output-json verification-results on stdout", "json")])

    bd = _smt_breakdown(jd)
    if partial:
        per[partial] = _partial_status(run, srcs, partial, holes, real, verified)
    elif bd is not None and not holes:
        for fn, ok in sorted(bd.items()):
            k = _sym_key(crate_name, fn)
            if k:
                per[k] = "verified" if ok else "failed"
    else:
        for fn in sorted(jd.get("func-details") or {}):
            k = _sym_key(crate_name, fn)
            if k:
                per[k] = "no-error"
        for loc in list(holes) + real:
            k = _symbol_of(run, srcs, loc.file, loc.line)
            if k and per.get(k) != "hole":
                per[k] = "hole" if isinstance(loc, Hole) else "failed"

    extra = []
    if real:
        vir = vr.get("encountered-vir-error")
        front = any(d.code in FRONT_END_IDS or re.fullmatch(r"E\d{4}", d.code or "")
                    for d in real)
        if front or (vir and not all_holes and verified is None):
            stage = "resolve"
        elif _after_verification(job, vr, verified, vir):
            # a --compile run whose verification found nothing: rustc's code generation
            # or the native linker stopped it (the R13 P5v shape), never the solver
            stage = "link" if any(_is_link_error(d) for d in real) else "compile"
        elif not vir and verified == 0 and vr.get("errors") == 0:
            stage = "parse"
        else:
            stage = "verify"
        rl = stage == "verify" and all(d.code == RLIMIT_ID for d in real)
        verdict = "inconclusive" if rl else "failed"
    elif job.exit == 1 and not all_holes:
        return res("error", "verify", [Diag("", 0, 0, "error",
                                            "exit 1 without an error diagnostic", "exit")])
    else:
        verdict, stage = "verified", "verify"
    if gate:
        fails = _gate_failures(vr, verified, min_verified, holes, findings, job.exit)
        if fails:
            extra.append(Diag("", 0, 0, "error", "gate: " + "; ".join(fails), "gate"))
            if verdict == "verified":
                verdict = "failed"
    return res(verdict, stage, extra)


LINK_ERROR = re.compile(r"^(linking with `[^`]*` failed|could not find native static library|"
                        r"error: linking)")


def _is_link_error(d):
    """A rustc diagnostic of the native link step (no error code, rustc's own wording)."""
    return not d.code and bool(LINK_ERROR.match(d.message or ""))


def _after_verification(job, vr, verified, vir):
    """True when a failed run compiled after a verification that found nothing: the job
    asked for code generation (`--compile`), verification ran over the crate (`verified`
    positive) with no error and no VIR error, so its errors come from a later stage."""
    return ("--compile" in [str(a) for a in (job.argv or [])] and not vir
            and isinstance(verified, int) and verified > 0 and vr.get("errors") == 0)


def _gate_failures(vr, verified, min_verified, holes, findings, exit_code):
    """The done-gate conditions a run misses (Δ12, Δ11); empty = passed."""
    fails = []
    for key, want in (("success", True), ("is-verifying-entire-crate", True),
                      ("encountered-vir-error", False)):
        if key not in vr:
            fails.append(f"--output-json lacks '{key}'")
        elif vr[key] is not want:
            fails.append(f"'{key}' is {json.dumps(vr[key])}, not {json.dumps(want)}")
    low = 1 if min_verified is None else min_verified
    if verified is None:
        fails.append("--output-json lacks 'verified'")
    elif verified < low:
        fails.append(f"verified {verified} < the unit's minimum {low}"
                     + (" (none pinned: at least 1, Δ11)" if min_verified is None else ""))
    if holes:
        fails.append(f"{len(holes)} hole(s)")
    dep = [f for f in findings if f.kind == "dependency-hole"]
    if dep:
        fails.append(f"{len(dep)} untrusted dependency hole(s)")
    if len(findings) > len(dep):
        fails.append(f"{len(findings) - len(dep)} lint finding(s)")
    if exit_code != 0:
        fails.append(f"exit {exit_code}")
    return fails


def _partial_status(run, srcs, symbol, holes, real, verified):
    """The selected function's status in a fast-channel run. A hole anywhere
    in the crate makes --no-cheating drop the counts (Δ12), so the status
    comes from where the diagnostics fall: hole | failed | inconclusive;
    then from the count when there is one: verified | not-checked; else
    no-error (no diagnostic, count unavailable)."""
    def mine(loc):
        k = _symbol_of(run, srcs, loc.file, loc.line)
        if not k:
            return False
        if "*::" in symbol:
            mod, _, meth = symbol.rpartition("*::")
            return k.endswith("::" + meth) and k.startswith(mod)
        return k == symbol
    if any(mine(h) for h in holes):
        return "hole"
    errs = [d for d in real if mine(d)] or real
    if errs:
        return "inconclusive" if all(d.code == RLIMIT_ID for d in errs) else "failed"
    if verified is not None:
        return "verified" if verified >= 1 else "not-checked"
    return "no-error"


# --- verify and holes ------------------------------------------------------------------------

def _fast_args(symbol):
    """--verify-root/--verify-only-module + --verify-function for a symbol
    `f`, `m::f`, `m::*::method` or `*::method` (Δ41)."""
    parts = symbol.split("::")
    if len(parts) >= 2 and parts[-2] == "*":
        module, fn = parts[:-2], "*::" + parts[-1]
    else:
        module, fn = parts[:-1], parts[-1]
    ident = r"[A-Za-z_][A-Za-z0-9_]*"
    if not re.fullmatch(rf"(\*::)?{ident}", fn) or any(not re.fullmatch(ident, m) for m in module):
        raise Refused(f"symbol {symbol!r}: expected f, module::f or module::*::method")
    return (["--verify-only-module", "::".join(module)] if module else ["--verify-root"]) + \
        ["--verify-function", fn]


def _lint_plan(run, plan, mode):
    tests = [f for f, _, t in plan.files if t]
    found = lint([f for f, _, _ in plan.files], mode, layer=plan.layer, test_files=tests)
    return [Finding(run.orig(x.file), x.line, x.kind, x.message) for x in found]


def verify(target, gate=False, symbol=None, seed=None, isolate=False, *, extra_args=(),
           min_verified=None, lint_mode="learner", layer=None, timeout_s=None, allowlist=None,
           root=None, smt_log_dir=None):
    """Verify a target with the pinned flags in one --no-cheating run (after
    its path dependencies are verified and exported).

    gate=True is the done gate (Δ12): a fresh toolchain check, no symbol, no
    isolate, no extra argument but the pinned rlimit and a seed, the lint
    (lint_mode) over the crate's files, and the conditions of the module
    docstring; min_verified is the unit's pinned minimum `verified`
    (default 1). symbol selects the fast channel (Δ41): `f` (root module),
    `m::f`, `m::*::method`; per_symbol then holds that symbol only. seed adds
    the pinned seed option; isolate adds `-V spinoff-all` (every function in
    its own Z3 instance). extra_args pass check_args or the call is refused.
    layer gives a standalone file the given layer chain up to that layer.
    smt_log_dir (the user's D53, R14): the target's run also passes
    `--log smt --log-dir <run>/smt-log` to Verus, and every file it writes is
    copied into that directory (created if missing) before the run's scratch
    is discarded; the result's `smt_logs` attribute (not a Result field, so the
    JSON document is unchanged) lists the copies. It is refused with the gate:
    a log changes nothing the run verifies, counts or reports, and the gate
    keeps its pinned command. The job is the same capped job (run_capped).
    root names the course root whose given crates and trust allowlist apply
    (default: the target's own course root, root_for).
    timeout_s may shorten, never lengthen, the pinned wall-clock net.

    holes are the target's own; a hole in a dependency crate is matched
    against the trust allowlist (allowlist: a file, default
    <course root>/expected/verus_trust.toml, loaded when the target has a dependency; an
    invalid one refuses the call): trusted, an info diagnostic
    (trusted-dependency-hole); else a `dependency-hole` finding, which fails
    the gate. With only trusted dependency holes, the record comes from a
    second run without --no-cheating (module docstring)."""
    reasons = check_args(extra_args, gate)
    if gate and symbol:
        reasons.append("a partial (--verify-*) run never passes the gate (Δ12, Δ41)")
    if gate and isolate:
        reasons.append("the gate runs the pinned command; -V spinoff-all is not part of it")
    if gate and smt_log_dir is not None:
        reasons.append("the gate runs the pinned command; an SMT log goes with the learner loop "
                       "or the fast channel (D53)")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int) or seed < 0):
        reasons.append(f"seed {seed!r}: a non-negative integer")
    if seed is not None and any(f == "--smt-option" for f, _ in split_args(extra_args)):
        reasons.append("a seed is given twice (seed and --smt-option)")
    if lint_mode not in MODES:
        reasons.append(f"lint mode {lint_mode!r}: one of {', '.join(MODES)}")
    try:
        fast = _fast_args(symbol) if symbol else []
    except Refused as e:
        reasons.append(str(e))
    if reasons:
        return _refused(target, "; ".join(reasons))
    try:
        vb = verus_bin(fresh=gate)
    except common.ToolchainError as e:
        return _toolchain_error(target, e)
    run = Run(common.scratch_dir("verus-verify"), str(target))
    try:
        res = _verify_run(run, target, vb, gate, symbol, seed, isolate, fast, extra_args,
                          min_verified, lint_mode, layer, timeout_s, allowlist, root,
                          smt_log=smt_log_dir is not None)
        if smt_log_dir is not None:
            res.smt_logs = _copy_smt_log(run, Path(smt_log_dir))
        return res
    finally:
        _discard(run)


def _copy_smt_log(run, dest):
    """Copy the files Verus wrote under <run>/smt-log into dest (D53); [copies]."""
    src = Path(run.dir) / "smt-log"
    out = []
    if not src.is_dir():
        return out
    dest.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.rglob("*")):
        if f.is_file() and not f.is_symlink():
            to = dest / f.relative_to(src)
            to.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, to)
            out.append(str(to))
    return out


def _verify_run(run, target, vb, gate, symbol, seed, isolate, fast, extra_args, min_verified,
                lint_mode, layer, timeout_s, allowlist, root, smt_log=False):
    try:
        plan = resolve(target, run, layer, root)
    except Refused as e:
        return _refused(target, str(e))
    run.files = plan.files
    try:
        trust = load_trust(allowlist, root=root_for(target, root)) if plan.crate.chain() else []
    except TrustError as e:
        return _refused(target, f"the trust allowlist is invalid: {e}")
    findings = _lint_plan(run, plan, lint_mode) if gate else []
    bad = _build_chain(run, plan.crate, seed, timeout_s)
    if bad:
        bad.findings = findings + bad.findings
        return bad
    p = pins()
    argv = [vb, plan.crate.root, "--crate-type=lib", "--crate-name", plan.crate.name,
            *_base_args(p, seed), *_link_args(plan.crate, run.dir / "deps"), "--no-cheating",
            "--output-json", "--error-format=json", "--time", *fast]
    if isolate:
        argv += ["-V", "spinoff-all"]
    argv += _passthrough(extra_args)
    if smt_log:
        argv += ["--log", "smt", "--log-dir", str(run.dir / "smt-log")]
    own = {run.orig(str(f)) for f, _, _ in plan.files}
    srcs = _Sources()
    job = _job(run, "target", argv, timeout_s)
    cls = functools.partial(_classify, run, crate_name=plan.crate.name, min_verified=min_verified,
                            findings=findings, partial=symbol or None, srcs=srcs, own=own,
                            trust=trust)
    first = cls(job=job, gate=False)
    trusted = [d for d in first.diagnostics if d.code == "trusted-dependency-hole"]
    if not (trusted and first.verdict == "verified" and not first.holes and
            not any(f.kind == "dependency-hole" for f in first.findings)):
        return cls(job=job, gate=gate) if gate else first
    # Only trusted dependency holes: the --no-cheating run has shown the target
    # hole-free but drops the record; the same command without --no-cheating
    # supplies it (module docstring).
    step = run.steps
    job2 = _job(run, "target", [a for a in argv if a != "--no-cheating"], timeout_s)
    res = cls(job=job2, gate=gate)
    res.diagnostics = trusted + [Diag("", 0, 0, "info", (
        f"the --no-cheating run (step {step:02d}) found no hole of the target and only trusted "
        f"dependency holes; the record comes from step {run.steps:02d}, the same command "
        "without --no-cheating"), "trusted-record")] + res.diagnostics
    return res


class HoleCountError(RuntimeError):
    """holes() could not count: the run did not reach verification."""

    def __init__(self, result):
        super().__init__(f"no hole count for {result.target}: verdict {result.verdict}, stage "
                         f"{result.stage} (raw output in {result.raw_dir})")
        self.result = result


def holes(target, **kw):
    """The tool-counted holes of a target (one --no-cheating run): the
    target's own; a dependency's hole is a finding of verify(), never one of
    these. Raises HoleCountError when the run did not reach verification (a
    refusal, a CLI error, a panic, a front-end error, a memory or wall-clock
    kill), so an empty list always means zero holes."""
    r = verify(target, **kw)
    if r.verdict in ("refused", "error", "killed(memory)") or r.stage != "verify" or \
            any(d.code == "wall-clock-kill" for d in r.diagnostics):
        raise HoleCountError(r)
    return r.holes


# --- lint --------------------------------------------------------------------------------------

RESERVED = {"solutions_policy", "solutions_first"}
GIVEN_CRATE = re.compile(r"qg_bignat_l([1-7])|rg_re_a(1b|[1-5])")
MODULE_DIR = re.compile(r"(?:^|/)verus/[qr]/([qr]\d\d)_[a-z0-9_]+/")
GIVEN_DIR = re.compile(r"(?:^|/)verus/given/(qg_bignat_l[1-7]|rg_re_a(?:1b|[1-5]))/")

LEARNER_RULES = {
    "pervasive-assume": "vstd::pervasive::assume is green under --no-cheating (V15, Δ9)",
    "external-type-specification": "external_type_specification is green under --no-cheating "
                                   "(V6, Δ9)",
    "exec-allows-no-decreases": "exec_allows_no_decreases_clause lets a diverging body prove "
                                "anything (V8, Δ9)",
    "external": "#[verifier::external] hides an item from the verifier (V10, Δ9)",
    "arbitrary": "arbitrary() leaves a spec value unconstrained and passes --no-cheating (Δ8)",
    "outside-verus": "code outside verus! is never verified (V9, Δ9)",
    "cfg-verus-only": "cfg(verus_only) only on `use` items or inside cfg_attr (V11, Δ9)",
    "later-layer": "names a given layer above this file's layer (Δ9, design §10.1)",
    "reference-crate": "names a reference (solutions…) crate",
    "rlimit-inflation": "a per-item rlimit above the pin (V22)",
    "external-body-type": "external_body on a type is green under --no-cheating",
    "proof-note-on-admit": "proof_note never attaches to admit(); label holes with "
                           "assume(false) (Δ7)",
    "include-macro": "include!-family macros pull in source the lint never sees",
    "path-attribute": "#[path] redirects a module to an arbitrary file",
    "reserved-name": "solutions_policy and solutions-first are reserved names (Δ79, Δ86)",
    "parse-error": "the file does not tokenize; nothing else was checked",
}
STRICT_RULES = {
    "agent-rlimit": "a delivery sets no per-item rlimit",
    "assume": "assume(…) is a hole; a finished file has none",
    "admit": "admit() is a hole; a finished file has none",
    "external-body": "external_body is a hole; a finished file has none",
    "assume-specification": "assume_specification is a hole; a finished file has none",
    "axiom": "an axiom fn is a hole; a finished file has none",
    "uninterp": "an uninterp or bodyless spec fn is a hole; a finished file has none",
    "assume-termination": "assume_termination is a hole; a finished file has none",
    "external-specification": "an external fn/trait specification is a hole; a finished file "
                              "has none",
    "proof-note": "a proof_note labels a hole; a finished file has none",
}
REFERENCE_RULES = {
    "slot-in-reference": "a reference twin holds no `SLOT:` and no `???` (spec §3.8.4 H6)",
    "need-missing": "an exit block's `need:` fragment is missing from its code (spec §3.9)",
}
RULES = {**LEARNER_RULES, **STRICT_RULES, **REFERENCE_RULES}
STRICT_ATTRS = {"verifier::external_body": "external-body",
                "verifier(external_body)": "external-body",
                "verifier::assume_termination": "assume-termination",
                "verifier::external_fn_specification": "external-specification",
                "verifier::external_trait_specification": "external-specification"}


def _allowed_crates(path, layer):
    """The given crates a file may name, or None when its layer is unknown."""
    if not layer:
        s = Path(path).as_posix()
        if m := MODULE_DIR.search(s):
            layer = gen_units.expected_layer(m.group(1).upper())
        elif m := GIVEN_DIR.search(s):
            own = gen_units.crate_layer(m.group(1))
            return {gen_units.verus_layer_crate(l) for l in gen_units.layer_chain(own)[:-1]}
        elif m := SPECIMEN_DIR.search(s):
            layer = gen_units.expected_layer(m.group(1))
    if not layer:
        return None
    return {gen_units.verus_layer_crate(l) for l in gen_units.layer_chain(layer)}


def _expand(paths):
    """(source files, test-only files, Cargo manifests) for lint()."""
    files, tests, manifests = [], set(), []
    for p in paths:
        p = Path(p)
        if p.is_dir() and (p / "Cargo.toml").is_file():
            manifests.append((p / "Cargo.toml").resolve())
            try:
                c = load_crate(p)
            except Refused:
                c = None
            if c is not None:
                for f, _, t in crate_files(c.root):
                    files.append(f)
                    if t:
                        tests.add(f)
                continue
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                rel = f.relative_to(p).parts
                if any(x in ("target", ".git") or x.startswith(".") for x in rel[:-1]):
                    continue
                if f.is_file() and (f.name.endswith(".rs") or f.name.endswith(".rs.specimen")):
                    files.append(f.resolve())
                elif f.is_file() and f.name == "Cargo.toml":
                    manifests.append(f.resolve())
        elif p.name == "Cargo.toml":
            manifests.append(p.resolve())
        else:
            files.append(p.resolve())
    return list(dict.fromkeys(files)), tests, list(dict.fromkeys(manifests))


def lint_manifest(path):
    """reserved-name findings for a Cargo.toml (Δ79, Δ86): the package, lib,
    bin/test/example/bench target and dependency names (renames included),
    compared without case and with `-` read as `_`."""
    text = Path(path).read_text()
    try:
        meta = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return [Finding(str(path), 0, "parse-error", RULES["parse-error"])]
    names = [meta.get("package", {}).get("name"), meta.get("lib", {}).get("name")]
    for kind in ("bin", "test", "example", "bench"):
        names += [t.get("name") for t in meta.get(kind, []) if isinstance(t, dict)]
    for table in ("dependencies", "dev-dependencies", "build-dependencies"):
        for key, spec in meta.get(table, {}).items():
            names.append(key)
            if isinstance(spec, dict):
                names.append(spec.get("package"))
    out = []
    lines = text.split("\n")
    for nm in names:
        if isinstance(nm, str) and nm.lower().replace("-", "_") in RESERVED:
            line = next((k for k, l in enumerate(lines, 1) if nm in l), 0)
            out.append(Finding(str(path), line, "reserved-name", RULES["reserved-name"]))
    return out


def lint(paths, mode, *, layer=None, test_files=()):
    """Static findings over Verus sources (never runs a tool, never quotes
    code). mode:
      learner    the constructs that are green under --no-cheating (Δ9, Δ8):
                 vstd::pervasive::assume (V15), external_type_specification
                 (V6), exec_allows_no_decreases_clause (V8),
                 #[verifier::external] (V10), arbitrary() (Δ8), code outside
                 verus! (V9; `use`, `mod x;`, tests and #[cfg(test)] items
                 excepted, Δ42), cfg(verus_only) except on `use` and in
                 cfg_attr (V11), a later layer's or a reference crate,
                 rlimit inflation (V22), external_body on a type,
                 proof_note on admit() (Δ7), include!-family macros, #[path],
                 the reserved names; loud holes are the tool's to count;
      agent      also every hole form and any per-item rlimit: a delivery is
                 hole-free;
      reference  as agent, plus spec §3.8.4 H6 (no SLOT:, no ???) and every
                 X block's `need:` fragments present in its code.
    paths are files or directories (a crate directory expands to its crate's
    files and its Cargo.toml, another directory to every .rs, .rs.specimen
    and Cargo.toml below it; a Cargo.toml gets only the reserved-name
    check, lint_manifest). Files
    reached through a #[cfg(test)] mod, or listed in test_files, are exempt
    from the outside-verus rule. layer sets the spine layer for the
    later-layer rule when the path does not (verus/{q,r}/<id>_*/,
    verus/given/<crate>/, specimens/<ID>/). An empty file list is a
    ValueError (empty lists fail)."""
    if mode not in MODES:
        raise ValueError(f"lint mode must be one of {', '.join(MODES)}, not {mode!r}")
    if isinstance(paths, (str, Path)):
        paths = [paths]
    files, tests, manifests = _expand(paths)
    tests |= {Path(f).resolve() for f in test_files}
    if not files and not manifests:
        raise ValueError("lint: no files (an empty list fails)")
    out = []
    for m in manifests:
        out += lint_manifest(m)
    for f in files:
        try:
            text = Path(f).read_text()
        except (OSError, UnicodeDecodeError):
            out.append(Finding(str(f), 0, "parse-error", RULES["parse-error"]))
            continue
        out += lint_source(text, str(f), mode, layer=layer, test_only=Path(f) in tests)
    return sorted(set(out), key=lambda x: (x.file, x.line, x.kind))


def lint_source(text, path, mode, *, layer=None, test_only=False):
    """lint() over one source text; `path` is reported and decides the layer."""
    out = []

    def add(line, kind):
        out.append(Finding(path, line, kind, RULES[kind]))
    try:
        src = vs.parse(text)
    except vs.ParseError as e:
        return [Finding(path, e.line, "parse-error", RULES["parse-error"])]
    t, n = src.toks, len(src.toks)
    p = pins()
    strict = mode in ("agent", "reference")
    allowed = _allowed_crates(path, layer)
    owner_of = {a[0]: it for it in src.walk() for a in it.attrs}
    for k, x in enumerate(t):
        nx = t[k + 1].text if k + 1 < n else ""
        if x.kind == "id":
            if x.text == "pervasive" and nx == "::" and k + 2 < n and t[k + 2].text == "assume":
                add(x.line, "pervasive-assume")
            elif x.text == "arbitrary" and nx == "(" and k + 2 < n and t[k + 2].text == ")":
                add(x.line, "arbitrary")
            elif x.text in ("include", "include_str", "include_bytes") and nx == "!":
                add(x.line, "include-macro")
            elif x.text == "cfg" and nx == "!" and k + 2 < n and t[k + 2].text == "(":
                if any(y.text == "verus_only" for y in t[k + 3:src.pairs[k + 2]]):
                    add(x.line, "cfg-verus-only")
            elif strict and x.text in ("assume", "admit") and nx == "(":
                add(x.line, x.text)
            if GIVEN_CRATE.fullmatch(x.text) and allowed is not None and x.text not in allowed:
                add(x.line, "later-layer")
            low = x.text.lower()
            if low.startswith("solutions") and low.replace("-", "_") not in RESERVED and \
                    mode != "reference":
                add(x.line, "reference-crate")
            if low in RESERVED and nx == "::":
                add(x.line, "reserved-name")
        elif x.kind == "punct" and x.text == "#":
            e = vs._attr_end(src, k, n)
            if e is None:
                continue
            at = vs.attr_text(src, (k, e))
            owner = owner_of.get(k)
            if at == "verifier::external_type_specification":
                add(x.line, "external-type-specification")
            elif at == "verifier::exec_allows_no_decreases_clause":
                add(x.line, "exec-allows-no-decreases")
            elif at in ("verifier::external", "verifier(external)"):
                add(x.line, "external")
            elif at.startswith("path="):
                add(x.line, "path-attribute")
            elif at.startswith("verifier::rlimit("):
                arg = at[len("verifier::rlimit("):-1]
                try:
                    over = arg == "infinity" or float(arg) > float(p["rlimit"])
                except ValueError:
                    over = True
                if mode == "agent":
                    add(x.line, "agent-rlimit")
                elif over:
                    add(x.line, "rlimit-inflation")
            elif at.startswith("verifier::proof_note("):
                if e + 1 < n and t[e + 1].text == "admit":
                    add(x.line, "proof-note-on-admit")
                if strict:
                    add(x.line, "proof-note")
            elif at in STRICT_ATTRS:
                if STRICT_ATTRS[at] == "external-body" and owner is not None and \
                        owner.kind in ("struct", "enum", "union", "type"):
                    add(x.line, "external-body-type")
                if strict:
                    add(x.line, STRICT_ATTRS[at])
            if at.startswith("cfg(") and "verus_only" in re.findall(r"\w+", at) and \
                    (owner is None or owner.kind != "use"):
                add(x.line, "cfg-verus-only")
    if not test_only:
        for it in vs.outside_verus_items(src):
            add(src.line_of(it.head), "outside-verus")
    for it in src.walk():
        names = []
        if it.kind in ("mod", "extern_crate") and it.name:
            names.append((src.line_of(it.head), it.name))
        elif it.kind == "use":
            names += [(x.line, x.text) for x in t[it.head:it.end] if x.kind == "id"]
        for line, nm in names:
            if nm.lower().replace("-", "_") in RESERVED:
                add(line, "reserved-name")
        if strict and it.kind == "assume_specification":
            add(src.line_of(it.head), "assume-specification")
        elif strict and it.kind == "fn":
            if "axiom" in it.quals:
                add(src.line_of(it.head), "axiom")
            elif "uninterp" in it.quals or (it.mode == "spec" and not it.body and
                                            it.owner is None):
                add(src.line_of(it.head), "uninterp")
    if Path(path).name.split(".")[0].lower().replace("-", "_") in RESERVED:
        add(1, "reserved-name")
    if mode == "reference":
        for ln, line in enumerate(text.split("\n"), 1):
            if "SLOT:" in line or "???" in line:
                add(ln, "slot-in-reference")
        out += need_check_source(text, path)
    return sorted(set(out), key=lambda x: (x.line, x.kind))


def need_check_source(text, path):
    """Findings for X blocks whose `need:` fragments are missing from their
    non-comment code (spec §3.9; whitespace-normalized)."""
    rel = path if path.endswith((".rs", ".rs.specimen")) else path + ".rs"
    items, _ = ci.parse_items(rel, text)
    code, _ = ci.scan(rel, text)
    out = []
    for it in items:
        if not it["need"]:
            continue
        block = " ".join(" ".join(code[it["line_start"]:it["line_end"]]).split())
        for frag in it["need"]:
            if " ".join(frag.split()) not in block:
                out.append(Finding(path, it["line_start"], "need-missing",
                                   f"{it['id']}: " + REFERENCE_RULES["need-missing"]))
    return out


# --- audit ---------------------------------------------------------------------------------------

TRUST_REL = Path("expected") / "verus_trust.toml"    # the default allowlist, per course root
DEFAULT_TRUST = REPO / TRUST_REL                     # the scripts' checkout's
# Where a trust entry's file may lie (repo-relative prefixes): the given layers
# only; a module crate's own hole is never trusted. Tests widen it.
TRUST_ROOTS = ("verus/given/",)
TRUST_KEYS = ("path", "symbol", "kind", "reason")
HOLE_KINDS = ("assume", "admit", "external_body", "assume_specification", "axiom", "uninterp",
              "bodyless_spec", "assume_termination", "external_fn_specification",
              "external_trait_specification")


class TrustError(ValueError):
    """An invalid trust allowlist: problems = [(line, message)] (line 0: the
    file as a whole)."""

    def __init__(self, path, problems):
        self.path, self.problems = str(path), list(problems)
        super().__init__(f"{path}: " + "; ".join(
            (f"line {ln}: {m}" if ln else m) for ln, m in self.problems))


def _trust_symbols(rel, root=REPO):
    """The fn and assume_specification symbols of a file, or None (unparsable)."""
    try:
        src = vs.parse((Path(root) / rel).read_text())
    except (OSError, UnicodeDecodeError, vs.ParseError):
        return None
    return {vs.item_symbol(it) for it in src.walk() if it.kind in ("fn", "assume_specification")}


def load_trust(path=None, *, root=None):
    """[{path, symbol, kind, reason}] from a trust allowlist: `[[trust]]`
    tables, nothing else. `path` is relative to the course root `root`
    (default the scripts' checkout), under a TRUST_ROOTS prefix (verus/given/),
    and names an existing file; `symbol` names a fn (or assume_specification)
    of that file, as dvl.verus_spec.item_symbol spells it within the file;
    `kind` is a Hole kind (HOLE_KINDS); `reason` is non-empty; no other key
    and no duplicate entry. No file at the default path (<root>/expected/
    verus_trust.toml) is an empty allowlist. Each entry also carries `_abs`,
    its file's absolute path (what holes are matched against). Raises
    TrustError listing every problem (a typo or a deleted path never passes
    silently)."""
    root = Path(root).resolve() if root is not None else REPO
    if path is None:
        default = root / TRUST_REL
        if not default.is_file():
            return []
        path = default
    path = Path(path)
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError) as e:
        raise TrustError(path, [(0, f"unreadable ({e.__class__.__name__})")]) from None
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        m = re.search(r"line (\d+)", str(e))
        raise TrustError(path, [(int(m.group(1)) if m else 0, "not valid TOML")]) from None
    heads = [k for k, line in enumerate(text.split("\n"), 1)
             if re.match(r"\s*\[\[\s*trust\s*\]\]", line)]
    problems = [(0, f"unknown top-level key {k!r} (only [[trust]] tables)")
                for k in sorted(set(data) - {"trust"})]
    entries = data.get("trust", [])
    if not isinstance(entries, list):
        problems.append((0, "`trust` must be an array of tables ([[trust]])"))
        entries = []
    out, seen, symbols = [], {}, {}
    for k, e in enumerate(entries, 1):
        ln = heads[k - 1] if k - 1 < len(heads) else 0
        if not isinstance(e, dict):
            problems.append((ln, f"entry {k} is not a table"))
            continue
        miss = [x for x in TRUST_KEYS if not isinstance(e.get(x), str) or not e[x].strip()]
        extra = sorted(set(e) - set(TRUST_KEYS))
        if extra:
            problems.append((ln, f"entry {k}: unknown key(s) {', '.join(extra)}"))
        if miss:
            problems.append((ln, f"entry {k} lacks {', '.join(miss)}"))
            continue
        rel, kind, sym = e["path"], e["kind"], e["symbol"]
        if kind not in HOLE_KINDS:
            problems.append((ln, f"entry {k}: kind {kind!r} is not a hole kind "
                                 f"({', '.join(HOLE_KINDS)})"))
        pp = Path(rel)
        if pp.is_absolute() or ".." in pp.parts or "\\" in rel:
            problems.append((ln, f"entry {k}: path must be repo-relative, without '..'"))
        elif not any(rel.startswith(r) for r in TRUST_ROOTS):
            problems.append((ln, f"entry {k}: path lies outside {', '.join(TRUST_ROOTS)} (the "
                                 "allowlist trusts given layers only)"))
        elif not (root / rel).is_file():
            problems.append((ln, f"entry {k}: path names no file (deleted or misspelt)"))
        else:
            if rel not in symbols:
                symbols[rel] = _trust_symbols(rel, root)
            if symbols[rel] is None:
                problems.append((ln, f"entry {k}: path does not parse as Verus source"))
            elif sym not in symbols[rel]:
                problems.append((ln, f"entry {k}: symbol names no fn or assume_specification "
                                     "of that file"))
        key = (rel, sym, kind)
        if key in seen:
            problems.append((ln, f"entry {k} repeats entry {seen[key]}"))
        seen.setdefault(key, k)
        out.append({**{x: e[x] for x in TRUST_KEYS}, "_abs": str((root / rel).resolve())})
    if problems:
        raise TrustError(path, problems)
    return out


def _trust_findings(err):
    return [Finding(err.path, ln, "bad-trust-entry", msg) for ln, msg in err.problems]


def _dedup(findings):
    """One finding per (file, line, kind): a dependency's hole is seen by its
    own run and again by every run of a crate that calls it."""
    out = {}
    for f in findings:
        out.setdefault((f.file, f.line, f.kind), f)
    return sorted(out.values(), key=lambda x: (x.file, x.line, x.kind))


def _audit_runs(run, plan, trust, timeout_s, srcs):
    """--no-cheating over each crate of the chain and the target (after
    _build_chain): (findings, audited files as shown). Every hole is a
    finding unless the allowlist names it (entries marked `_used`)."""
    p = pins()
    vb = verus_bin()
    outdir = run.dir / "deps"
    findings, audited = [], set()
    for c in plan.crate.chain() + [plan.crate]:
        argv = [vb, c.root, "--crate-type=lib", "--crate-name", c.name, *_base_args(p),
                *_link_args(c, outdir), "--no-cheating", "--output-json", "--error-format=json"]
        job = _job(run, f"audit-{c.name}", argv, timeout_s)
        r = _classify(run, job, c.name, False, None, [], None, srcs)
        files = plan.files if c is plan.crate else crate_files(c.root)
        audited |= {run.orig(str(f)) for f, _, _ in files}
        if r.verdict in ("error", "killed(memory)", "refused") or r.stage != "verify" or \
                any(d.code == "wall-clock-kill" for d in r.diagnostics):
            findings.append(Finding(str(c.root if c is not plan.crate else run.target), 0,
                                    "audit-incomplete", f"the --no-cheating run of {c.name} did "
                                    f"not complete ({r.verdict}, stage {r.stage}); raw output "
                                    f"in {r.raw_dir}"))
            continue
        _, untrusted = _match_trust(run, srcs, r.holes, trust)
        for h, sym in untrusted:
            findings.append(Finding(h.file, h.line, f"hole-{h.kind.replace('_', '-')}",
                                    f"{_a(h.kind)} hole (in {sym or 'an item'}) not on the "
                                    "trust allowlist"))
    return findings, audited


def audit(target, *, mode="learner", allowlist=None, layer=None, timeout_s=None, root=None):
    """The Verus assumption audit (spec §11.1 row 3; design §11.1): every
    --no-cheating hole of the target crate and of each of its path
    dependencies (the given layers its proofs trust), minus the trust
    allowlist (load_trust; default <course root>/expected/verus_trust.toml,
    the course root being root_for(target, root); an invalid one
    gives only its bad-trust-entry findings and runs nothing); the lint
    (mode) over the target's files; and every allowlist entry under the
    audited files that matched no hole (stale-trust-entry: a waiver that
    matches nothing is an error; check_trust checks every entry). One finding
    per (file, line, kind). A run that did not complete is itself a finding
    (audit-incomplete), so an empty list always means a clean audit."""
    if mode not in MODES:
        raise ValueError(f"lint mode must be one of {', '.join(MODES)}, not {mode!r}")
    try:
        croot = root_for(target, root)
        trust = load_trust(allowlist, root=croot)
    except TrustError as e:
        return _trust_findings(e)
    try:
        verus_bin()
    except common.ToolchainError as e:
        return [Finding(str(target), 0, "audit-incomplete", str(e))]
    run = Run(common.scratch_dir("verus-audit"), str(target))
    try:
        try:
            plan = resolve(target, run, layer, croot)
        except Refused as e:
            return [Finding(str(target), 0, "audit-incomplete", str(e))]
        run.files = plan.files
        findings = _lint_plan(run, plan, mode)
        bad = _build_chain(run, plan.crate, None, timeout_s)
        if bad:
            return _dedup(findings + [Finding(str(target), 0, "audit-incomplete",
                                              f"a dependency did not build ({bad.verdict}); raw "
                                              f"output in {bad.raw_dir}")])
        found, audited = _audit_runs(run, plan, trust, timeout_s, _Sources())
        findings += found
        for e in trust:
            f = e["_abs"]
            if f in {str(Path(x).resolve()) for x in audited} and not e.get("_used"):
                findings.append(Finding(f, 0, "stale-trust-entry",
                                        f"trust entry {e['symbol']} ({e['kind']}) matches no "
                                        "hole"))
        return _dedup(findings)
    finally:
        _discard(run)


def given_crates(root=None):
    """The given layer crate directories of a course root (given_root(root)/
    <crate>/Cargo.toml; root defaults to the scripts' checkout), sorted."""
    groot = given_root(Path(root).resolve() if root is not None else REPO)
    return sorted(d for d in groot.iterdir() if (d / "Cargo.toml").is_file()) \
        if groot.is_dir() else []


def check_trust(allowlist=None, *, timeout_s=None, root=None):
    """The CI check of the trust allowlist (a waiver that matches nothing is
    an error): load_trust's validation (bad-trust-entry), then a full
    --no-cheating audit of every given layer crate of the course root `root`
    (default the scripts' checkout; given_crates(root): verus/given/*/
    Cargo.toml; each chain audited once, from its top crates): every
    given-layer hole the allowlist does not name (hole-<kind>), every entry
    that matched no hole (stale-trust-entry, wherever its file lies) and
    every run that did not complete (audit-incomplete). No lint. [] = every
    entry matched a hole and no given layer has an untrusted hole (an empty
    allowlist over no given crate is [] too: nothing is trusted). The
    allowlist defaults to <root>/expected/verus_trust.toml."""
    croot = Path(root).resolve() if root is not None else REPO
    try:
        trust = load_trust(allowlist, root=croot)
    except TrustError as e:
        return _trust_findings(e)
    crates = given_crates(croot)
    findings = []
    if crates:
        try:
            verus_bin()
        except common.ToolchainError as e:
            return [Finding(str(given_root(croot)), 0, "audit-incomplete", str(e))]
    loaded = {}
    for d in crates:
        try:
            loaded[d.resolve()] = load_crate(d)
        except Refused as e:
            findings.append(Finding(str(d / "Cargo.toml"), 0, "audit-incomplete", str(e)))
    below = {x.dir for c in loaded.values() for x in c.chain()}
    srcs = _Sources()
    for d, c in loaded.items():
        if d in below:
            continue                      # audited from a crate above it
        run = Run(common.scratch_dir("verus-trust"), str(d))
        try:
            plan = Plan(c, crate_files(c.root), False)
            run.files = plan.files
            bad = _build_chain(run, c, None, timeout_s)
            if bad:
                findings.append(Finding(str(d), 0, "audit-incomplete",
                                        f"a dependency did not build ({bad.verdict}); raw "
                                        f"output in {bad.raw_dir}"))
                continue
            findings += _audit_runs(run, plan, trust, timeout_s, srcs)[0]
        finally:
            _discard(run)
    for e in trust:
        if not e.get("_used"):
            findings.append(Finding(e["_abs"], 0, "stale-trust-entry",
                                    f"trust entry {e['symbol']} ({e['kind']}) matches no hole of "
                                    "a given layer"))
    return _dedup(findings)


# --- statement freeze -------------------------------------------------------------------------

def _spec_records(path, measure_free=False):
    """[(symbol, sha256, file, line, kind)] for a Verus file, specimen or crate
    directory (items of a submodule file carry its module path). measure_free:
    each file's header `decreases` clauses blanked first
    (verus_spec.measure_free_text)."""
    p = Path(path)
    files = crate_files(load_crate(p).root) if p.is_dir() else [(p.resolve(), "", False)]
    out = []
    for f, modpath, _ in files:
        text = Path(f).read_text()
        src = vs.parse(vs.measure_free_text(text) if measure_free else text)
        for sym, digest, line, kind in vs.statements(src):
            out.append(("::".join(filter(None, [modpath, sym])), digest, str(f), line, kind))
    return out


def spec_hash(path, symbols=None):
    """{symbol: sha256} of the statements in a Verus file or crate: for every
    item inside verus!, its kept attributes, its signature and every clause
    (requires, ensures, recommends, decreases, …), normalized to tokens; plus
    the body of a spec fn and the whole of a struct, enum, type, const,
    global, broadcast group or assume_specification. Proof and exec bodies,
    comments, whitespace, trailing commas, doc comments and the attributes
    external_body, rlimit, spinoff_prover, allow/warn/deny, inline and
    must_use are not part of a statement. symbols restricts the result
    (absent symbols are simply absent). Parser limits: dvl/verus_spec.py."""
    d = {}
    for sym, digest, _, _, _ in _spec_records(path):
        d[sym] = digest
    if symbols is not None:
        d = {s: d[s] for s in symbols if s in d}
    return d


def _hash_map(x):
    """({symbol: sha256}, {symbol: (file, line)}) from a dict, a .json/.toml
    mapping file (a TOML file may nest it under [statements]) or Verus
    sources."""
    if isinstance(x, dict):
        return dict(x), {}
    p = Path(x)
    if p.suffix == ".json":
        return dict(json.loads(p.read_text())), {}
    if p.suffix == ".toml":
        data = tomllib.loads(p.read_text())
        return dict(data.get("statements", data)), {}
    recs = _spec_records(p)
    return {r[0]: r[1] for r in recs}, {r[0]: (r[2], r[3]) for r in recs}


def freeze_check(frozen, candidate):
    """Findings for every frozen statement missing from (freeze-missing) or
    changed in (freeze-changed) the candidate. Either side is a spec_hash
    dict, a .json/.toml mapping file, or Verus sources. New candidate items
    are allowed. An empty frozen list is a finding (freeze-empty). An added
    measure is no change: a statement that differs is compared again on the
    candidate's sources with their measures blanked (verus_spec
    measure_free_text), so a `decreases` added to a fn that had none passes."""
    fz, _ = _hash_map(frozen)
    cd, locs = _hash_map(candidate)
    if not isinstance(candidate, dict) and Path(candidate).suffix not in (".json", ".toml") \
            and any(cd.get(s, h) != h for s, h in fz.items()):
        alt = {r[0]: r[1] for r in _spec_records(candidate, measure_free=True)}
        cd = {s: (fz[s] if s in fz and alt.get(s) == fz[s] else h) for s, h in cd.items()}
    where = "" if isinstance(candidate, dict) else str(Path(candidate).resolve())
    if not fz:
        return [Finding(where, 0, "freeze-empty",
                        "the frozen statement list is empty: nothing would be checked")]
    out = []
    for sym in sorted(fz):
        if sym not in cd:
            out.append(Finding(where, 0, "freeze-missing", f"frozen item {sym} is missing"))
        elif cd[sym] != fz[sym]:
            f, line = locs.get(sym, (where, 0))
            out.append(Finding(f, line, "freeze-changed",
                               f"the statement of {sym} changed (signature or clauses)"))
    return out


# --- tests (Δ42) ------------------------------------------------------------------------------

TEST_LINE = re.compile(r"^test (\S+) \.\.\. (ok|FAILED|ignored)\b")
TEST_STATUS = {"ok": "passed", "FAILED": "failed", "ignored": "ignored"}


def test(target, names=None, *, layer=None, timeout_s=None, root=None):
    """Compiled checks (Δ42): verify the crate in the normal mode (proof holes
    do not block tests), build its libtest binary with `verus --compile
    --test`, run every test once (--test-threads 1) as a plain job (no course memory cap, Δ503), and
    judge the requested names: each must match exactly one test (its full
    path, or its trailing `::`-segments) and pass. A name that matches
    nothing, or no test at all, fails (Δ11: never exit 0 alone). per_symbol:
    {test path: passed | failed | ignored}; verified_count is the
    verification's own `verified`. root: as for verify()."""
    try:
        vb = verus_bin()
    except common.ToolchainError as e:
        return _toolchain_error(target, e)
    run = Run(common.scratch_dir("verus-test"), str(target))
    try:
        return _test_run(run, target, vb, names, layer, timeout_s, root)
    finally:
        _discard(run)


def _test_run(run, target, vb, names, layer, timeout_s, root=None):
    try:
        plan = resolve(target, run, layer, root)
    except Refused as e:
        return _refused(target, str(e))
    run.files = plan.files
    bad = _build_chain(run, plan.crate, None, timeout_s)
    if bad:
        return bad
    p = pins()
    tbin = run.dir / "testbin"
    argv = [vb, plan.crate.root, "--crate-type=lib", "--crate-name", plan.crate.name,
            *_base_args(p), *_link_args(plan.crate, run.dir / "deps"), "--compile", "--test",
            "-o", tbin, "--output-json", "--error-format=json"]
    job = _job(run, "compile-test", argv, timeout_s)
    r = _classify(run, job, plan.crate.name, False, None, [], None)
    if r.verdict != "verified" or job.exit != 0 or not tbin.is_file():
        if r.verdict == "verified":
            r.verdict, r.stage = "error", "compile"
        return r
    tjob = _job(run, "run-tests", [tbin, "--test-threads", "1"], timeout_s)
    per = {}
    for line in tjob.out.splitlines():
        if m := TEST_LINE.match(line):
            per[m.group(1)] = TEST_STATUS[m.group(2)]
    diags = []
    if names is None:
        judged = sorted(k for k, v in per.items() if v != "ignored")
    else:
        judged = []
        for nm in names:
            hits = [k for k in per if k == nm or k.endswith("::" + nm)]
            if len(hits) == 1:
                judged.append(hits[0])
            else:
                diags.append(Diag("", 0, 0, "error", f"test {nm} " + (
                    "did not run" if not hits else f"is ambiguous ({len(hits)} tests)"),
                    "test-not-found"))
    if not judged and not diags:
        diags.append(Diag("", 0, 0, "error", "no test ran (an empty test set never passes)",
                          "test-not-found"))
    for k in judged:
        if per.get(k) != "passed":
            diags.append(Diag("", 0, 0, "error", f"test {k} {per.get(k, 'did not run')}",
                              "test"))
    res = Result(LANG, str(target), tjob.exit, "verified", "test", r.verified_count, [],
                 diags, [], per, str(run.dir), tjob.argv)
    if tjob.killed == "memory":
        res.verdict = "killed(memory)"
    elif tjob.killed == "wallclock":
        res.verdict = "inconclusive"
        res.diagnostics.append(Diag("", 0, 0, "error", "test binary killed by the wall-clock "
                                    "safety net (Δ58)", "wall-clock-kill"))
    elif diags:
        res.verdict = "failed"
    return res


# --- a crate's binary target (the user's decision D16, 2026-10-12; QPLAN §30 Q59) ----------------

@dataclass
class BinRun:
    """One run of a built binary: its name, the arguments it got, its exit
    code and its two output streams (as the program wrote them)."""
    name: str
    args: list
    exit: int
    stdout: str
    stderr: str


def bin_targets(cdir):
    """[(name, root file)] of a crate directory's `[[bin]]` tables. Refused
    when the manifest is unreadable."""
    manifest = Path(cdir) / "Cargo.toml"
    try:
        meta = tomllib.loads(manifest.read_text())
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise Refused(f"{manifest}: unreadable ({e})") from None
    out = []
    for t in meta.get("bin", []):
        if not isinstance(t, dict) or not isinstance(t.get("name"), str) or \
                not isinstance(t.get("path"), str):
            raise Refused(f"{manifest}: a [[bin]] table needs a name and a path")
        out.append((t["name"], (Path(cdir) / t["path"]).resolve()))
    return out


def run_bin(target, args=(), *, timeout_s=None, root=None):
    """A crate's command-line tool through the pinned compiler (D16): the
    crate's path dependencies verified and exported (as for verify), the
    library verified in the normal mode (proof holes do not block it, as for
    test(); the done gate is verify(gate=True)) and compiled to an rlib, its
    one `[[bin]]` root compiled against it with `verus --crate-type=bin
    --compile`, then the binary run once with `args` as a plain job (no course memory cap, Δ503) and
    the wall clock. Cargo is never used. Returns (Result, BinRun or None):
    the Result's stage is `run` and its verdict `verified` when the binary
    was built and exited 0 (`failed` for another exit; killed(memory) and
    inconclusive as the caps say); a build that did not pass returns its own
    Result (stage verify or compile) and no BinRun. per_symbol: {bin name:
    "exit <n>"}. The scratch copy, the rlibs and the binary are deleted on
    return; the job logs stay (raw_dir). root: as for verify()."""
    try:
        vb = verus_bin()
    except common.ToolchainError as e:
        return _toolchain_error(target, e), None
    run = Run(common.scratch_dir("verus-bin"), str(target))
    try:
        return _bin_run(run, target, vb, list(args), timeout_s, root)
    finally:
        _discard(run)


def _bin_run(run, target, vb, args, timeout_s, root=None):
    t = Path(target)
    t = (t if t.is_absolute() else Path.cwd() / t)
    shown = common.display_path(t)
    if not (t.is_dir() and (t / "Cargo.toml").is_file()):
        return _refused(target, f"{shown}: --bin takes a crate directory (one with a "
                                "Cargo.toml)"), None
    try:
        bins = bin_targets(t)
        if len(bins) != 1:
            raise Refused(f"{shown}: the crate has "
                          + ("no [[bin]] target" if not bins else f"{len(bins)} [[bin]] targets")
                          + "; --bin builds a crate with exactly one")
        name, main = bins[0]
        if not main.is_file():
            raise Refused(f"{shown}: the [[bin]] root {common.display_path(main)} does not exist")
        plan = resolve(t, run, None, root)
        if any(f == main for f, _, _ in plan.files):
            raise Refused(f"{shown}: the [[bin]] root is a module of the library")
    except Refused as e:
        return _refused(target, str(e)), None
    run.files = plan.files + [(main, "", False)]
    bad = _build_chain(run, plan.crate, None, timeout_s)
    if bad:
        return bad, None
    p = pins()
    deps = run.dir / "deps"
    lib = plan.crate
    argv = [vb, lib.root, "--crate-type=lib", "--crate-name", lib.name, *_base_args(p),
            *_link_args(lib, deps), "--export", deps / f"{lib.name}.vir", "--compile",
            "--out-dir", deps, "--output-json", "--error-format=json"]
    job = _job(run, "lib", argv, timeout_s)
    r = _classify(run, job, lib.name, False, None, [], None)
    if r.verdict != "verified" or job.exit != 0 or not (deps / f"lib{lib.name}.rlib").is_file():
        if r.verdict == "verified":
            r.verdict, r.stage = "error", "compile"
        return r, None
    lib_verified = r.verified_count
    binc = Crate(_crate_name(name), main, t.resolve(), [lib])
    out = run.dir / "bin" / name
    out.parent.mkdir(exist_ok=True)
    argv = [vb, main, "--crate-type=bin", "--crate-name", binc.name, *_base_args(p),
            *_link_args(binc, deps), "--compile", "-o", out, "--output-json",
            "--error-format=json"]
    job = _job(run, "bin", argv, timeout_s)
    r = _classify(run, job, binc.name, False, None, [], None)
    if r.verdict != "verified" or job.exit != 0 or not out.is_file():
        if r.verdict == "verified":
            r.verdict, r.stage = "error", "compile"
        return r, None
    rjob = _job(run, "run-bin", [out, *args], timeout_s)
    res = Result(LANG, str(target), rjob.exit, "verified" if rjob.exit == 0 else "failed", "run",
                 lib_verified, [], [], [], {name: f"exit {rjob.exit}"}, str(run.dir), rjob.argv)
    if rjob.killed == "memory":
        res.verdict = "killed(memory)"
        res.diagnostics.append(Diag("", 0, 0, "error", f"killed by a signal (exit "
                                    f"{rjob.exit}; a memory kill): not a verdict (Δ57)", "killed(memory)"))
    elif rjob.killed == "wallclock":
        res.verdict = "inconclusive"
        res.diagnostics.append(Diag("", 0, 0, "error", "the binary was killed by the "
                                    "wall-clock safety net (Δ58)", "wall-clock-kill"))
    return res, BinRun(name, [str(a) for a in args], rjob.exit, rjob.out, rjob.err)


# --- the empty-body gate (Δ45, Δ47) ------------------------------------------------------------

# Mode definitions (Δ47; the DV0 spike's gate tool). E0H runs E0 at
# EB_HIGH_FACTOR x the pinned rlimit ("E0 at 10x the rlimit").
SEQ_GROUPS = ("vstd::seq_lib::group_seq_properties", "vstd::seq::group_seq_lemmas_expensive")
ARITH_LITE = ("vstd::arithmetic::mul::group_mul_basics",
              "vstd::arithmetic::div_mod::group_mod_properties",
              "vstd::arithmetic::div_mod::group_div_basics",
              "vstd::arithmetic::div_mod::group_mod_basics",
              "vstd::arithmetic::div_mod::group_fundamental_div_mod_converse",
              "vstd::arithmetic::power::group_pow_properties")
MUL_HEAVY = ("vstd::arithmetic::mul::group_mul_properties",)
EB_HIGH_FACTOR = 10
EB_MODES = ("E0", "E0H", "E1", "E2", "EC", "EM", "NL", "BV", "INV", "TRIV", "RGN")
EB_PROOF = ("E0", "E0H", "E1", "E2", "EC", "EM", "NL", "BV")
EB_EXEC = ("E0", "E0H", "E1", "E2", "EC", "EM", "INV", "TRIV")
# RGN (the region mode, QPLAN §6 Q18) runs only when asked for: on a reference
# twin, never by default on a learner file.
EB_ON_REQUEST = ("RGN",)
INT_TYPES = {"u8", "u16", "u32", "u64", "u128", "usize", "i8", "i16", "i32", "i64", "i128",
             "isize"}
LEVER_ATTRS = re.compile(r"verifier(::|\()(external_body|rlimit|spinoff_prover)")


def eb_timeout(mode, timeout_s, p=None):
    """The wall clock of one empty-body variant job: the caller's timeout_s,
    shortened to the mode's own pin (pins.toml eb_mode_timeout_s: BV's short
    clock), or None for the course net. A kill counts as the variant failing
    (Δ58)."""
    p = pins() if p is None else p
    own = (p.get("eb_mode_timeout_s") or {}).get(mode)
    if own is None:
        return timeout_s
    return own if timeout_s is None else min(own, timeout_s)


def _trivial_body(src, it):
    if it.ret is None:
        return "{\n}"
    ret = [x.text for x in src.toks[it.ret[0]:it.ret[1]]]
    if ret[:1] == ["("] and ":" in ret and ret[-1:] == [")"]:
        ret = ret[ret.index(":") + 1:-1]
    ty = "".join(ret)
    if ty in ("", "()"):
        return "{\n}"
    if ty in INT_TYPES:
        return "{\n    0\n}"
    if ty == "bool":
        return "{\n    false\n}"
    return None


def _empty_proof_body(src, it):
    """The empty body of a proof fn: `{}`, or `{ arbitrary() }` for a proof fn
    that returns a value (`-> (r: T)` or `-> T`, not unit): `{}` does not
    type-check there, so every variant would end no-verify and the gate
    `error` (QPLAN §30 Q65, PLAN §8 R15(b); the DVR0 spike's gate_ret.py).
    vstd's `arbitrary()` is an unconstrained value: the empty proof plus a
    witness nothing is known about. A tracked return keeps `{}` (a spec value
    cannot be returned in tracked mode; no variant applies)."""
    if it.ret is None:
        return "{\n}"
    ret = [x.text for x in src.toks[it.ret[0]:it.ret[1]]]
    if "tracked" in ret:
        return "{\n}"
    if ret[:1] == ["("] and ":" in ret and ret[-1:] == [")"]:
        ret = ret[ret.index(":") + 1:-1]
    if "".join(ret) in ("", "()"):
        return "{\n}"
    return "{\n    arbitrary()\n}"


def eb_variant(text, src, it, mode, groups=(), triv_body=None, item_id=None):
    """The source text of one empty-body variant of fn `it`, or None when the
    mode does not apply (Δ47):
      E0, E0H  proof fn: body `{}` (`{ arbitrary() }` when it returns a
               value, _empty_proof_body); exec fn: every proof statement
               (proof blocks, assert/assume/admit, ghost lets, broadcast use,
               reveal/hide) and loop invariant stripped, exec code, decreases
               and `let tracked` statements kept (exec code consumes tracked
               values, `Tracked(perm)`: QPLAN §30 Q65(b), PLAN §8 R15(a));
      E1 E2 EC EM  E0 plus a module-level `broadcast use` of `groups`;
      NL, BV   proof fn: one whole-goal `assert(<ensures>) by
               (nonlinear_arith | bit_vector) requires <requires>;`;
      INV      exec fn with a loop invariant: the invariants dropped only;
      TRIV     exec fn: a trivial body (triv_body, or one for a unit,
               integer or bool return): the spec must not accept it;
      RGN      proof or exec fn of a reference twin: the lines inside the
               `@hole-begin`/`@hole-end` regions of item `item_id` blanked
               (common.strip_regions), the given code kept (QPLAN §6 Q18);
               a clause keyword whose whole list the regions blanked
               (`invariant`, `requires`, `ensures`, `decreases`, …, followed
               by another clause or the body) is dropped too
               (rgn_drop_dangling); None without an item id or a region.
    The item's own levers (external_body, rlimit, spinoff_prover) go first."""
    t = src.toks
    if not it.body:
        return None
    b0, b1 = t[it.body[0]].start, t[it.body[1]].end
    proof = it.mode == "proof"
    if proof and mode in ("E0", "E0H", "E1", "E2", "EC", "EM", "NL", "BV"):
        body = _empty_proof_body(src, it)
        if mode in ("NL", "BV"):
            ens, req = vs.clause_exprs(src, it, "ensures"), vs.clause_exprs(src, it, "requires")
            if not ens or it.ret is not None:
                return None
            prover = "nonlinear_arith" if mode == "NL" else "bit_vector"
            body = ("{\n    assert(" + " && ".join(f"({e})" for e in ens) + f") by ({prover})"
                    + ("\n        requires\n            " + ",\n            ".join(req) + ","
                       if req else "") + ";\n}")
        new = text[:b0] + body + text[b1:]
    elif not proof and mode in ("E0", "E0H", "E1", "E2", "EC", "EM", "INV"):
        spans = vs.proof_spans(src, it.body[0] + 1, it.body[1], invariants=True,
                               proof=(mode != "INV"), keep_tracked=True)
        if mode == "INV" and not spans:
            return None
        new = text[:b0] + vs.apply_spans(text[b0:b1], [(a - b0, b - b0) for a, b in spans]) \
            + text[b1:]
    elif not proof and mode == "TRIV":
        body = triv_body or _trivial_body(src, it)
        if body is None:
            return None
        new = text[:b0] + body + text[b1:]
    elif mode == "RGN":
        if item_id is None or not common.hole_regions(text, item_id):
            return None
        new = text
    else:
        return None
    levers = [(t[a].start, t[c].end) for a, c in it.attrs
              if LEVER_ATTRS.match(vs.attr_text(src, (a, c)))]
    new = vs.apply_spans(new, levers)
    if groups:
        ins = vs.module_insert_point(src, it)
        ins -= sum(b - a for a, b in levers if b <= ins)
        new = new[:ins] + "broadcast use " + ", ".join(groups) + ";\n\n" + new[ins:]
    if mode == "RGN":
        new = rgn_drop_dangling(common.strip_regions(new, item_id), item_id)
    return new


# The clause keywords of a Verus fn header and of a loop (verus_spec's lists):
# each heads a list, which the grammar does not allow to be empty (`no_unwind`
# stands alone, so it is never dangling).
RGN_CLAUSE_KWS = (frozenset(vs.CLAUSE_KWS) | frozenset(vs.LOOP_CLAUSES)) - {"no_unwind"}


def rgn_drop_dangling(text, item_id):
    """`text` (a region variant: item_id's regions already blanked) without
    the clause keywords those regions left dangling (DV3a follow-up, Δ137
    Open): a keyword of RGN_CLAUSE_KWS that is the last token before one of
    the item's regions, when the first token after the region (other blank
    regions and comments skipped) is another clause keyword, the body's `{`
    or a `;`. Blanking a whole `invariant` list then means "no invariant",
    and the variant still parses. Only the keyword's characters go: the line
    count and every other location stay as in the twin."""
    regions = common.hole_regions(text, item_id)
    if not regions:
        return text
    toks = vs.tokenize(text)
    spans = set()
    for _, b, e in regions:
        before = [t for t in toks if t.line < b]
        after = [t for t in toks if t.line > e]
        if not before or not after:
            continue
        kw, nxt = before[-1], after[0]
        if kw.kind == "id" and kw.text in RGN_CLAUSE_KWS and (
                (nxt.kind == "id" and nxt.text in RGN_CLAUSE_KWS)
                or (nxt.kind == "punct" and nxt.text in ("{", ";"))):
            spans.add((kw.start, kw.end))
    return vs.apply_spans(text, sorted(spans))


def owner_type(owner):
    """The type an impl method belongs to, from vs's owner text: `T` for
    `<T as Trait>` and for an inherent `T` (generic arguments dropped: `T<U>`
    gives `T`), None for no owner."""
    if not owner:
        return None
    m = re.fullmatch(r"<(.+) as .+>", owner)
    ty = m.group(1) if m else owner
    return ty.split("<", 1)[0]


def _find_item(run, plan, item_symbol):
    """(compiled file, module path, Source, fn Item) for an item id (the
    first fn of its block) or a fn symbol, else None. A symbol is matched, in
    this order, as: the exact symbol (`f`, `m::f`, `Owner::f`, `<T as
    Trait>::f`, with or without the module path of its file); a qualified
    method `T::f` or `m::T::f` naming the TYPE of an impl method, inherent or
    trait (QPLAN §30 Q65(a): a trait-impl method shares its name with the
    trait's declaration and with other impls, so `f` alone is ambiguous);
    the bare name `f`. Each rule must give one fn; the first rule that gives
    any decides (the crate-level exact symbol: its first match, as it always
    was)."""
    is_id = bool(ci.ITEM_ID.fullmatch(item_symbol))
    full, exact, typed, by_name = [], [], [], []
    for f, modpath, _ in plan.files:
        text = Path(f).read_text()
        src = vs.parse(text)
        if is_id:
            items, _ = ci.parse_items(str(f), text)
            for blk in items:
                if blk["id"] == item_symbol:
                    cands = [it for it in src.walk() if it.kind == "fn" and it.in_verus and
                             blk["line_start"] <= src.line_of(it.head) <= blk["line_end"]]
                    if cands:
                        return f, modpath, src, cands[0]
            continue
        for it in src.walk():
            if it.kind != "fn" or not it.in_verus:
                continue
            sym = vs.item_symbol(it)
            if "::".join(filter(None, [modpath, sym])) == item_symbol:
                full.append((f, modpath, src, it))
            elif sym == item_symbol:
                exact.append((f, modpath, src, it))
            ty = owner_type(it.owner) if it.owner and it.owner.startswith("<") or \
                (it.owner and _is_impl_owner(src, it)) else None
            if ty is not None:
                short = "::".join(filter(None, [it.path, ty, it.name]))
                if item_symbol in ("::".join(filter(None, [modpath, short])), short):
                    typed.append((f, modpath, src, it))
            if it.name == item_symbol:
                by_name.append((f, modpath, src, it))
    if full:
        return full[0]          # the crate-level symbol, as before Q65
    for found in (exact, typed, by_name):
        if found:
            return found[0] if len(found) == 1 else None
    return None


def _is_impl_owner(src, it):
    """True when fn `it` is a method of an impl block (not of a trait)."""
    for parent in src.walk():
        if it in parent.children:
            return parent.kind == "impl"
    return False


def _verify_function_arg(plan, it):
    """The --verify-function pattern of an empty-body variant: `f` for a free
    fn, `*::f` for a method whose name no other fn of the target's files
    carries, and `T::f` (the method's type, owner_type) when another fn
    shares the name: a trait's declaration, another impl of the same trait,
    an inherent method (QPLAN §30 Q65(a)). Verus lists an impl method, trait
    impls included, as `T::f` relative to the verified module and matches
    that name exactly (probed at the pin: `*::f` verified both impls of a
    trait, `T::f` only T's, `*::T::f` none)."""
    if it.owner is None:
        return it.name
    same = 0
    for f, _, _ in plan.files:
        same += sum(1 for x in vs.parse(Path(f).read_text()).walk()
                    if x.kind == "fn" and x.in_verus and x.name == it.name)
    ty = owner_type(it.owner)
    return f"*::{it.name}" if same <= 1 or ty is None else f"{ty}::{it.name}"


def _course_groups(plan):
    """Every broadcast group the target crate and its path dependencies
    declare, as a path usable from the target (EC's course group)."""
    out = []
    for c in plan.crate.chain():
        for f, modpath, _ in crate_files(c.root):
            for path, name in vs.broadcast_groups(vs.parse(Path(f).read_text())):
                out.append("::".join(filter(None, [c.name, modpath, path, name])))
    for f, modpath, _ in plan.files:
        for path, name in vs.broadcast_groups(vs.parse(Path(f).read_text())):
            out.append("::".join(filter(None, ["crate", modpath, path, name])))
    return out


def _eb_status(job):
    if job.killed == "memory":
        return "killed(memory)"
    if job.killed == "wallclock":
        return "killed(harness)"
    jd = parse_json_doc(job.out)
    jdiags, raw = parse_stderr(job.err)
    vr = (jd or {}).get("verification-results")
    vr = vr if isinstance(vr, dict) else None
    errs = [d for d in jdiags if d.get("level") == "error" and json_message_id(d) != ABORT_ID]
    if job.exit == 0 and vr is not None:
        return "verifies" if (vr.get("verified") or 0) >= 1 else "fn-not-checked"
    if job.exit == 1 and vr is not None and not vr.get("encountered-vir-error") and \
            vr.get("verified") is not None and errs and \
            not any(isinstance(d.get("code"), dict) for d in errs):
        return "fails(rlimit)" if all(json_message_id(d) == RLIMIT_ID for d in errs) \
            else "fails(error)"
    first = errs[0]["message"] if errs else (raw[0] if raw else f"exit {job.exit}")
    return "no-verify(" + first.splitlines()[0][:120] + ")"


def empty_body(target, item_symbol, *, modes=None, seeds=None, triv_body=None, layer=None,
               timeout_s=None, root=None):
    """The empty-body gate for one item (Δ45, Δ47; design §7.3). Each
    applicable mode of eb_variant is verified on a scratch copy of the crate
    through the fast channel (--verify-root/--verify-only-module +
    --verify-function, Δ41), at the pinned rlimit (E0H: EB_HIGH_FACTOR x
    it), under every pinned seed (EM, memory-heavy, under the first seed
    only), jobs running DVL_VERUS_JOBS at a time (default 1). item_symbol is
    an item id (`Q04.H1v`: the first fn of its block) or a fn symbol; an impl
    method may be named by its type, `Type::method`, or exactly, `<Type as
    Trait>::method` (_find_item; QPLAN §30 Q65(a)), and its variant is
    verified under `--verify-function Type::method` when another fn shares
    its name (_verify_function_arg). modes
    restricts the modes; by default every applicable one: proof fns E0 E0H
    E1 E2 EC EM NL BV, exec fns E0 E0H E1 E2 EC EM INV TRIV (EC only when a
    broadcast group is declared in the crate or below; NL/BV only with an
    ensures and no named return; INV only with a loop invariant; TRIV only
    for a unit, integer or bool return unless triv_body is given). RGN, the
    region mode of an annotation hole (QPLAN §6 Q18), runs only when modes
    names it: `target` is the item's reference twin laid over its learner
    crate, item_symbol its item id, and the variant blanks the item's
    `@hole-begin`/`@hole-end` regions; a twin whose markers are broken is
    refused.

    The item must FAIL. verdict: failed = no variant verified (the hole is
    real: it passes the gate); verified = some variant verified or raised no
    obligation (the item falls to automation: the gate rejects it);
    killed(memory) = a variant was killed by the memory cap and none
    verified; error = the plain empty body (E0) did not reach verification,
    or no variant did, so nothing was tested; refused = a bad request. A
    variant of another mode that does not reach verification (Verus rejects
    the prover on the goal, e.g. bit_vector over a recursive spec fn) did not
    close the item: it is reported (no-verify, a warning) and counts as
    failing. A wall-clock kill counts as the variant failing (Δ58).
    per_symbol: {'<mode> seed=<s>': verifies | fn-not-checked | fails(error)
    | fails(rlimit) | no-verify(<first error>) | killed(memory) |
    killed(harness)}; verified_count = variants that verified. The variant
    copies are deleted when the call returns (module docstring, Scratch).
    Each variant job runs under eb_timeout(mode, timeout_s): BV under its
    own short clock (pins.toml eb_mode_timeout_s), the others under
    timeout_s or the course net. root: as for verify()."""
    p = pins()
    seeds = list(p["seeds"] if seeds is None else seeds)
    if not seeds or any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in seeds):
        return _refused(target, "seeds: a non-empty list of non-negative integers (empty lists "
                                "fail)")
    if modes is not None and (not modes or any(m not in EB_MODES for m in modes)):
        return _refused(target, f"modes: one or more of {' '.join(EB_MODES)} (integer_ring is "
                                "not a mode at the pin, Δ47)")
    try:
        vb = verus_bin()
    except common.ToolchainError as e:
        return _toolchain_error(target, e)
    run = Run(common.scratch_dir("verus-emptybody"), str(target))
    try:
        return _empty_body_run(run, target, vb, item_symbol, p, seeds, modes, triv_body,
                               layer, timeout_s, root)
    finally:
        _discard(run)


def _empty_body_run(run, target, vb, item_symbol, p, seeds, modes, triv_body, layer,
                    timeout_s, root=None):
    try:
        plan = resolve(target, run, layer, root)
        run.files = plan.files
        found = _find_item(run, plan, item_symbol)
    except (Refused, vs.ParseError) as e:
        return _refused(target, str(e))
    if found is None:
        return _refused(target, f"{item_symbol}: no unique fn item found in the target (name "
                                "an impl method by its type, `Type::method` or `<Type as "
                                "Trait>::method`)")
    f, modpath, src, it = found
    if it.mode not in ("proof", "exec") or not it.body:
        return _refused(target, f"{item_symbol}: a {it.mode} fn without a body is not a hole the "
                                "empty-body gate can test")
    applicable = (EB_PROOF if it.mode == "proof" else EB_EXEC) + \
        tuple(m for m in EB_ON_REQUEST if modes and m in modes)
    cgroups = _course_groups(plan)
    groups = {"E1": SEQ_GROUPS, "E2": ARITH_LITE, "EM": MUL_HEAVY, "EC": tuple(cgroups)}
    text = Path(f).read_text()
    item_id = item_symbol if ci.ITEM_ID.fullmatch(item_symbol) else None
    if modes and "RGN" in modes:
        try:
            common.hole_regions(text, item_id)
        except ValueError as e:
            return _refused(target, f"{run.orig(str(f))}: {e}")
    variants = {}
    for mode in (m for m in (modes or applicable) if m in applicable):
        if mode == "EC" and not cgroups:
            continue
        v = eb_variant(text, src, it, mode, groups.get(mode, ()), triv_body, item_id)
        if v is not None:
            variants[mode] = v
    if not variants:
        return _refused(target, f"{item_symbol}: none of the requested modes applies")
    bad = _build_chain(run, plan.crate, None, timeout_s)
    if bad:
        return bad
    base = plan.crate.root.parent
    module = "::".join(filter(None, [modpath, it.path]))
    vf = (["--verify-only-module", module] if module else ["--verify-root"]) + \
        ["--verify-function", _verify_function_arg(plan, it)]
    jobs = []
    for mode, vtext in variants.items():
        vdir = run.dir / f"variant-{mode}"
        for g, _, _ in plan.files:
            g = Path(g)
            dst = vdir / (g.relative_to(base) if g.is_relative_to(base) else g.name)
            dst.parent.mkdir(parents=True, exist_ok=True)
            if g == Path(f):
                dst.write_text(vtext)
            else:
                shutil.copyfile(g, dst)
        run.pathmap.append((str(vdir), str(base)))
        rl = p["rlimit"] * EB_HIGH_FACTOR if mode == "E0H" else p["rlimit"]
        root = vdir / (plan.crate.root.relative_to(base))
        for sd in (seeds[:1] if mode == "EM" else seeds):
            argv = [vb, root, "--crate-type=lib", "--crate-name", plan.crate.name,
                    *_base_args(p, sd, rl), *_link_args(plan.crate, run.dir / "deps"),
                    "--output-json", "--error-format=json", "--time", *vf]
            jobs.append((mode, sd, argv))

    def go(j):
        mode, sd, argv = j
        return mode, sd, _job(run, f"eb-{mode}-seed{sd}", argv, eb_timeout(mode, timeout_s, p))
    with concurrent.futures.ThreadPoolExecutor(max_workers=common.jobs("verus")) as ex:
        done = list(ex.map(go, jobs))
    per, diags = {}, []
    where, line = run.orig(str(f)), src.line_of(it.head)
    for mode, sd, job in done:
        st = _eb_status(job)
        per[f"{mode} seed={sd}"] = st
        if st in ("verifies", "fn-not-checked"):
            diags.append(Diag(where, line, 0, "error", f"{item_symbol}: the empty body {st} in "
                              f"mode {mode} (seed {sd}): the item falls to automation",
                              "empty-body"))
        elif st.startswith("no-verify"):
            diags.append(Diag(where, line, 0, "warning", f"{item_symbol}: variant {mode} "
                              f"(seed {sd}) did not reach verification", "no-verify"))
    sts = list(per.values())
    e0_broken = any(k.startswith("E0 ") and v.startswith("no-verify") for k, v in per.items())
    if any(x in ("verifies", "fn-not-checked") for x in sts):
        verdict = "verified"
    elif "killed(memory)" in sts:
        verdict = "killed(memory)"
    elif e0_broken or all(x.startswith("no-verify") for x in sts):
        verdict = "error"
    else:
        verdict = "failed"
    return Result(LANG, str(target), None, verdict, "verify", sum(x == "verifies" for x in sts),
                  [], diags, [], per, str(run.dir), done[0][2].argv if done else [])


# --- normalization for goldens (Δ37) -----------------------------------------------------------

def normalize_output(stdout_text, stderr_text):
    """A canonical form of one Verus run for golden comparison (pins.py):
    the --output-json document with sorted keys and sorted note lists, its
    `times-ms` and `verus` (build-info) blocks dropped; the diagnostics with
    the `aborting due to` line dropped, --triggers notes whose span is in a
    vstd file dropped, file names reduced to basenames, sorted by position;
    and the other stderr lines, in order."""
    jd = parse_json_doc(stdout_text)
    if jd is not None:
        jd = {k: v for k, v in jd.items() if k not in ("times-ms", "verus")}
        for v in (jd.get("func-details") or {}).values():
            for k in ("obligation_proof_notes", "failed_proof_notes"):
                if isinstance(v.get(k), list):
                    v[k] = sorted(v[k])
        jd = json.loads(json.dumps(jd, sort_keys=True))
    jdiags, raw = parse_stderr(stderr_text)
    out = []
    for d in jdiags:
        if json_message_id(d) == ABORT_ID:
            continue
        sp = _primary(d) or {}
        fname = sp.get("file_name", "")
        if d.get("level") == "note" and "triggers" in d.get("message", "") and \
                "vstd" in Path(fname).parts:
            continue
        out.append({"level": d.get("level"), "message": d.get("message"),
                    "file": os.path.basename(fname), "line": sp.get("line_start", 0),
                    "col": sp.get("column_start", 0),
                    "labels": sorted(s.get("label") or "" for s in d.get("spans") or [])})
    out.sort(key=lambda x: (x["file"], x["line"], x["col"], x["message"]))
    return {"json": jd, "diagnostics": out, "other": raw}
