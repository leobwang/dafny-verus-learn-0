"""Q18 — Practice III-C: gate v2, the gate at crate scale (Reference Solution)

Hole-free reference for `harness/q/fvh_q/gate/gate_v2.py` (author-only; never
learner-visible). Same names, signatures, docstrings, item markers and order
as the exercise file. Every hole is filled. Each H item declares, on a
`# triv:` line after its function, the trivial body that the Python TRIV mode
of `scripts/firsttry.sh Q18 --empty-body` lays over this reference: the
acceptance tests must reject each one (QPLAN §11.8, §19.0).

The tools run this file only by overlay: `scripts/dvl/python.py` copies
harness/ to scratch, lays this twin over its learner path and runs the
module's acceptance tests there (harness/tests/q/gate/test_gate_v2.py; they
replay the results recorded on the fixture crates of
harness/tests/q/fixtures/q18/, so no solver runs).

Why the reference is shaped as it is (Solutions/plans/Q18-code-notes.md §5):
the option scan runs before any instrument, so a poisoned build file is named
even when the pinned command ignores it; the gate's document is judged by its
own fields (the command it ran, the wrapper's completeness messages, the
pinned counts), never by a record a delivery brings; the seed sweep is one
fresh process of the pinned seed-rerun instrument; only `fp_report` reads
labels.
"""
import argparse
import sys
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from fvh import stats, tools
from fvh.tools import ToolResult
from fvh.verdicts import FAIL, GRADER_ONLY, PASS

# =============================================================================
# Given (frozen statements: expected/Q18.freeze pins them). Read them, never
# change them.
# =============================================================================

COURSE_ROOT = Path(__file__).resolve().parents[4]
"""The course root this file lives in: a target's repo-relative paths are read
from here unless a caller names another root."""

LANGS = ("dafny", "verus")
SEEDS = (1, 2, 3)
"""The pinned seeds of `scripts/vcheck --brittleness` (the seed-rerun instrument)."""

PARTIAL_FLAGS = {
    "dafny": ("--filter-symbol", "--filter-position", "--no-verify"),
    "verus": ("--verify-module", "--verify-function", "--verify-root",
              "--verify-only-module", "--no-verify"),
}
"""Flags that make a verifier run check less than the whole target (catalog
rows G7, G8, V18, V19): a gate document whose command holds one is not a run
of the whole crate."""

# The option allowlist (H5). Catalog rows: spec §11.1's G and V tables.
DAFNY_OPTIONS_ALLOWED = ("standard-libraries", "resource-limit", "manual-lemma-induction")
"""The only keys a delivery's dfyconfig.toml may hold under [options]."""

DAFNY_OPTION_ROWS = {
    "allow-warnings": "G6", "allow-axioms": "G6", "allow-external-contracts": "G6",
    "no-verify": "G7", "filter-symbol": "G8", "filter-position": "G8",
    "library": "G10", "boogie": "G14", "solver-option": "G14", "solver-path": "G15",
    "plugin": "G16",
}
"""The catalog row of a refused [options] key; any other key that is not
allowed is row G21 (project-file poisoning). A top-level `base` key is G21
too."""

CARGO_CONFIG_ROWS = {"build": "V24", "env": "V24", "alias": "V20", "target": "V24"}
"""The catalog row of each table a delivery's .cargo/config.toml (or
.cargo/config) may not hold: [build] and [target.*] can pass flags or a
wrapper to the compiler, [env] can set VERUS_* and RUSTFLAGS, [alias] can put
another command in the verifier's place."""

BUILD_TOOL_RULES = {"build.rs": "build-script", "conftest.py": "conftest"}
"""A file of the delivery with one of these names is a build-tool finding,
whatever it holds: it runs code at build or test time."""

RLIMIT_ATTRIBUTE = "#[verifier::rlimit("
"""A Verus source attribute that raises a function's resource limit (V22)."""


@dataclass(frozen=True)
class Pins:
    """What a complete run of the target must show: at least `min_verified`
    verified, and each symbol in `symbols` (the gate document's per_symbol
    keys) verified."""

    min_verified: int
    symbols: tuple[str, ...]


@dataclass(frozen=True)
class CrateTarget:
    """One delivery at crate scale, with no label.

    id       the delivery's id
    lang     "dafny" or "verus"
    target   what the instruments run: a Dafny root file, or a Verus crate
             directory (repo-relative, fvh.tools' form)
    files    every file of the delivery, repo-relative POSIX paths: its
             sources and its companions (project and build files included)
    pins     the counts a complete run must reach
    """

    id: str
    lang: str
    target: str
    files: tuple[str, ...]
    pins: Pins


@dataclass(frozen=True)
class Finding:
    """One static finding of the option scan: `rule` is a catalog row ("G6",
    "V24", …) or a BUILD_TOOL_RULES value, `path` the delivery file it is in
    (repo-relative), `detail` a short note (your wording)."""

    rule: str
    path: str
    detail: str


@dataclass(frozen=True)
class Spread:
    """The seed sweep of one target: `verdicts` the per-seed verdicts in seed
    order, `widest_cv` the largest coefficient of variation of any symbol's
    resource count across the seeds (None when the sweep reported none),
    `stable` True exactly when every seed's verdict is "verified"."""

    verdicts: tuple[str, ...]
    widest_cv: float | None
    stable: bool


@dataclass(frozen=True)
class GateVerdict:
    """A gate's verdict on one delivery: `word` is PASS or FAIL; `unknown`
    holds the grader-only classes (fvh.verdicts.GRADER_ONLY, in that order)
    that no instrument decided, and is () on a FAIL; `reasons` (your wording,
    one per failed check) is non-empty exactly on a FAIL."""

    word: str
    unknown: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class GateResult:
    """One delivery's gate run: its id, the verdict, every instrument result
    keyed by instrument name, the option scan's findings, and the seed sweep
    (None when the gate never reached it)."""

    id: str
    verdict: GateVerdict
    results: Mapping[str, ToolResult]
    findings: tuple[Finding, ...]
    spread: Spread | None


@dataclass(frozen=True)
class Label:
    """What only the evaluator reads of one delivery: its kind ("construct"
    or "control") and, for a construct, its X class (spec §5.6)."""

    kind: str
    xclass: str


@dataclass(frozen=True)
class FPReport:
    """The evaluator's account of a set of gate runs against their labels.

    controls         the number of controls
    fp               controls whose word is FAIL (false positives)
    fp_interval      the 95% Wilson interval of fp / controls
    detected         X class -> the constructs of that class whose word is
                     FAIL (every class some construct carries is a key, 0
                     included)
    held_by_unknown  constructs the gate passed whose class is in the
                     verdict's `unknown`
    false_pass       constructs the gate passed whose class is not in it
    """

    controls: int
    fp: int
    fp_interval: tuple[float, float]
    detected: Mapping[str, int]
    held_by_unknown: int
    false_pass: int


def render(v: GateVerdict) -> str:
    """The printed verdict: `FAIL (<n> reasons)`, or `PASS`, followed by
    ` · UNKNOWN: X07, X08, X14` while `unknown` is not empty (never a bare
    PASS while a grader-only class is undecided, spec §5.6)."""
    if v.word != PASS:
        return f"{v.word} ({len(v.reasons)} reasons)"
    return PASS + (" · UNKNOWN: " + ", ".join(v.unknown) if v.unknown else "")


def load_set(path) -> list[tuple[CrateTarget, Label]]:
    """The targets and labels of a set file (TOML): one [[delivery]] table per
    target with keys id, lang, target, files, min_verified, symbols, kind and
    xclass (tests/q/fixtures/q18/set.toml shows the form)."""
    with open(path, "rb") as f:
        data = tomllib.load(f)
    out = []
    for d in data.get("delivery", []):
        t = CrateTarget(d["id"], d["lang"], d["target"], tuple(d["files"]),
                        Pins(int(d["min_verified"]), tuple(d.get("symbols", []))))
        out.append((t, Label(d["kind"], d.get("xclass", ""))))
    return out


def main(argv=None) -> int:
    """Your own live check, outside the tests: the gate over a set file's
    targets, one instrument at a time: a course file's instruments on the host,
    an agent-provenance copy's (a plant outside the course tree) in the
    verification container (fvh.tools.run, Δ145). That container is built
    from the course crate whose path the copy's path ends with, so make a
    plant as a copy of a course crate (the capstone crate, a Lab 3 card's
    task) that keeps the crate's path at its end; a copy of a fixture crate
    under tests/q/fixtures/ ends with no course path, and its instruments
    raise RunnerUnavailable.
        cd harness && PYTHONPATH=q uv run python -m fvh_q.gate.gate_v2 \\
            --set tests/q/fixtures/q18/set.toml
    A relative set path is taken from the current directory; the targets'
    paths are repo-relative. Prints one line per delivery, then the report.
    Exit 0 when the report shows no false pass and no false positive, else 1."""
    ap = argparse.ArgumentParser(prog="python -m fvh_q.gate.gate_v2", allow_abbrev=False)
    ap.add_argument("--set", required=True)
    a = ap.parse_args(argv)
    results, labels = [], {}
    for target, label in load_set(a.set):
        r = gate_crate(target)
        results.append(r)
        labels[target.id] = label
        print(f"{target.lang}/{target.id}: {render(r.verdict)}", flush=True)
        for reason in r.verdict.reasons:
            print(f"  {reason}", flush=True)
    rep = fp_report(results, labels)
    lo, hi = rep.fp_interval
    print("detected: " + ", ".join(f"{k} {v}" for k, v in sorted(rep.detected.items())))
    print(f"held by unknown: {rep.held_by_unknown}; false passes: {rep.false_pass}; "
          f"false positives: {rep.fp} of {rep.controls} controls "
          f"(95% Wilson interval {lo:.3f}..{hi:.3f})")
    return 0 if rep.false_pass == 0 and rep.fp == 0 else 1


# =============================================================================
# Holes
# =============================================================================

# item: Q18.H3py S12
def gate_crate(target: CrateTarget, *, run=None) -> GateResult:
    """**H3.** The gate on one crate-scale delivery.

    First, before anything runs, the option scan: `option_findings(target)`.
    Then each instrument once, in a fresh process, as
    `run(instrument, target.target)`, where `run` is the argument when it is
    given, else `fvh.tools.run` looked up at the time of the call (never an
    instrument of your own, never a build or test command):
      "vcheck --gate"        always;
      "vaudit"               always;
      "specfreeze --check"   when the delivery brings its frozen statements
                             (the companion that `fvh.tools.command` names:
                             a file of the delivery);
    and last the seed sweep, `seed_spread(target, run=run)`.

    The verdict is FAIL, with one reason per failed check, when any of these
    holds: the option scan found something (one reason per finding); a run
    was killed or exited with neither 0 nor 1; `complete_and_counted` gives
    a reason on the gate's document (each of its reasons is one of yours);
    "vaudit" or "specfreeze --check" exits 1; the sweep is not stable.
    Otherwise a PASS whose `unknown` is GRADER_ONLY, in that order, minus
    "X08" when "specfreeze --check" ran and passed (a frozen statement
    decides it); nothing here decides X07 or X14.

    Returns GateResult(target.id, verdict, results, findings, spread), the
    results keyed by instrument name, the seed-rerun result among them (as
    seed_spread ran it). Raises ValueError for a language other than
    "dafny" and "verus"; an instrument that cannot run at all raises, and
    the gate never turns that into a PASS.
    """
    if target.lang not in LANGS:
        raise ValueError(f"{target.lang!r} is not a language the gate runs ({', '.join(LANGS)})")
    run = run if run is not None else tools.run
    findings = option_findings(target)
    results = {}
    for name in ("vcheck --gate", "vaudit"):
        results[name] = run(name, target.target)
    frozen = [p for p in tools.command("specfreeze --check", target.target, lang=target.lang)[1:]
              if not p.startswith("--") and p != target.target
              and not p.endswith("/src/lib.rs")]
    if frozen and all(p in target.files for p in frozen):
        results["specfreeze --check"] = run("specfreeze --check", target.target)

    recording = lambda instrument, t: results.setdefault(instrument, run(instrument, t))  # noqa: E731
    reasons = [f"{f.rule}: {f.path}: {f.detail}" for f in findings]
    spread = None
    for name, res in results.items():
        if res.killed is not None or res.exit_code not in (0, 1):
            reasons.append(f"{name}: no verdict (killed {res.killed}, exit {res.exit_code})")
    gate_doc = results["vcheck --gate"].document
    reasons += [f"vcheck --gate: {r}" for r in complete_and_counted(gate_doc, target.pins)]
    if results["vaudit"].exit_code == 1:
        reasons.append("vaudit: a finding")
    sf = results.get("specfreeze --check")
    if sf is not None and sf.exit_code == 1:
        reasons.append("specfreeze --check: a statement changed")
    try:
        spread = seed_spread(target, run=recording)
    except ValueError as e:
        reasons.append(f"seed-rerun: {e}")
    else:
        if not spread.stable:
            reasons.append("seed-rerun: not stable: " + ", ".join(spread.verdicts))
    if reasons:
        return GateResult(target.id, GateVerdict(FAIL, (), tuple(reasons)), results,
                          tuple(findings), spread)
    unknown = tuple(c for c in GRADER_ONLY if not (c == "X08" and sf is not None))
    return GateResult(target.id, GateVerdict(PASS, unknown, ()), results, tuple(findings), spread)
# triv: return GateResult(target.id, GateVerdict(PASS, GRADER_ONLY, ()), {}, (), None)


# item: Q18.H4py S12
def complete_and_counted(doc: dict, pins: Pins) -> list[str]:
    """**H4.** The reasons a `scripts/vcheck --gate --json` document cannot
    stand for a complete run of the whole target; `[]` for one that can.

    One reason (a short string, your wording) per check that fails, in this
    order:
      1. `lang` is "dafny" or "verus";
      2. `stage` is "verify";
      3. `verdict` is "verified";
      4. `exit_code` (the verifier's own) is 0;
      5. `holes` is an empty list;
      6. `findings` is an empty list;
      7. `cmd` is a list of strings holding none of PARTIAL_FLAGS[lang]
         (with an unknown `lang`, this check fails too);
      8. no entry of `diagnostics` has a `message` that starts with
         "gate:" (the wrapper's own completeness checks: for Verus, the
         `--output-json` keys `success`, `is-verifying-entire-crate` and
         `encountered-vir-error`);
      9. `verified_count` is an int (a bool is not one) of at least
         `pins.min_verified`;
     10. every symbol of `pins.symbols` is a key of `per_symbol` whose value
         is "verified": one reason per symbol that is not.
    A missing key fails its check. A `doc` that is not a dict gives exactly
    one reason.
    """
    if not isinstance(doc, dict):
        return ["the document is not a JSON object"]
    out = []
    lang = doc.get("lang")
    if lang not in LANGS:
        out.append(f"lang is {lang!r}, not one of {', '.join(LANGS)}")
    if doc.get("stage") != "verify":
        out.append(f"stage is {doc.get('stage')!r}, not 'verify'")
    if doc.get("verdict") != "verified":
        out.append(f"verdict is {doc.get('verdict')!r}, not 'verified'")
    if doc.get("exit_code") != 0:
        out.append(f"the verifier's exit code is {doc.get('exit_code')!r}")
    holes = doc.get("holes")
    if not isinstance(holes, list) or holes:
        out.append("holes is not an empty list")
    findings = doc.get("findings")
    if not isinstance(findings, list) or findings:
        out.append("findings is not an empty list")
    cmd = doc.get("cmd")
    if not isinstance(cmd, list) or not all(isinstance(a, str) for a in cmd):
        out.append("cmd is not a list of strings")
    elif lang not in LANGS:
        out.append("cmd cannot be checked for a partial run: unknown language")
    else:
        partial = [a for a in cmd if a in PARTIAL_FLAGS[lang]]
        if partial:
            out.append("a partial run: " + ", ".join(partial))
    diags = doc.get("diagnostics")
    if not isinstance(diags, list):
        out.append("diagnostics is not a list")
    else:
        gate = [d.get("message", "") for d in diags
                if isinstance(d, dict) and str(d.get("message", "")).startswith("gate:")]
        if gate:
            out.append("the wrapper's completeness check failed: " + "; ".join(gate))
    n = doc.get("verified_count")
    if isinstance(n, bool) or not isinstance(n, int) or n < pins.min_verified:
        out.append(f"verified_count is {n!r}, below the pinned {pins.min_verified}")
    per = doc.get("per_symbol")
    per = per if isinstance(per, dict) else {}
    for s in pins.symbols:
        if per.get(s) != "verified":
            out.append(f"{s} is {per.get(s)!r}, not verified")
    return out
# triv: return []


# item: Q18.H5py S10
def option_findings(target: CrateTarget, *, root=None) -> list[Finding]:
    """**H5.** The option allowlist and the build-tool checks: what the
    delivery's own files would change about how it is built or checked, read
    statically (nothing here runs). `root` is the course root the files are
    read from (default COURSE_ROOT). One Finding per offence, in the order of
    `target.files`, then within a file in reading order:
      - a file named as a key of BUILD_TOOL_RULES (its basename): one
        finding with that value as the rule;
      - a file named dfyconfig.toml: one finding (row G21) for a top-level
        `base` key; one per key of its [options] table that is not in
        DAFNY_OPTIONS_ALLOWED, with the row DAFNY_OPTION_ROWS gives it, else
        G21;
      - a file named Cargo.toml: one finding (rule "build-script") when its
        [package] table's `build` key is present and not `false`; and in its
        [package.metadata.verus] table, one finding (row V18) when `verify`
        is present and not `true`, and one (row V16) per other key;
      - a file named config.toml or config whose parent directory is named
        .cargo: one finding per top-level table of CARGO_CONFIG_ROWS present
        in it, with that row;
      - a .rs file: one finding (row V22) per line holding RLIMIT_ATTRIBUTE.
    A TOML file that does not parse is one finding (row G21) and nothing
    more about that file. A file of `target.files` that is missing raises
    FileNotFoundError: the scan never passes a delivery it could not read.
    """
    base = Path(root) if root is not None else COURSE_ROOT
    out = []
    for rel in target.files:
        p = PurePosixPath(rel)
        path = Path(rel) if Path(rel).is_absolute() else base / rel
        text = path.read_text(encoding="utf-8")
        if p.name in BUILD_TOOL_RULES:
            out.append(Finding(BUILD_TOOL_RULES[p.name], rel, "a build-tool file"))
            continue
        is_cargo_config = p.name in ("config.toml", "config") and p.parent.name == ".cargo"
        if p.name in ("dfyconfig.toml", "Cargo.toml") or is_cargo_config:
            try:
                data = tomllib.loads(text)
            except tomllib.TOMLDecodeError:
                out.append(Finding("G21", rel, "the file does not parse"))
                continue
            if p.name == "dfyconfig.toml":
                if "base" in data:
                    out.append(Finding("G21", rel, "a base chain"))
                for key in data.get("options", {}):
                    if key not in DAFNY_OPTIONS_ALLOWED:
                        out.append(Finding(DAFNY_OPTION_ROWS.get(key, "G21"), rel,
                                           f"option {key}"))
            elif p.name == "Cargo.toml":
                pkg = data.get("package", {})
                if "build" in pkg and pkg["build"] is not False:
                    out.append(Finding("build-script", rel, f"package.build = {pkg['build']!r}"))
                meta = pkg.get("metadata", {}).get("verus", {})
                for key, value in meta.items():
                    if key == "verify":
                        if value is not True:
                            out.append(Finding("V18", rel, f"metadata.verus.verify = {value!r}"))
                    else:
                        out.append(Finding("V16", rel, f"metadata.verus.{key}"))
            else:
                for table in data:
                    if table in CARGO_CONFIG_ROWS:
                        out.append(Finding(CARGO_CONFIG_ROWS[table], rel, f"[{table}]"))
            continue
        if p.suffix == ".rs":
            for n, line in enumerate(text.splitlines(), 1):
                if RLIMIT_ATTRIBUTE in line:
                    out.append(Finding("V22", rel, f"line {n}: a raised rlimit"))
    return out
# triv: return []


# item: Q18.H6py S11
def seed_spread(target: CrateTarget, *, seeds=SEEDS, run=None) -> Spread:
    """**H6.** The seed sweep of one target: `run("seed-rerun",
    target.target)`, once (one fresh process; `run` as in gate_crate), whose
    instrument is `scripts/vcheck --brittleness` (every pinned seed, each in
    a fresh verifier process). Its JSON document holds `seeds` (the seeds it
    ran, in order), `verdicts` (seed, as a string -> verdict) and `spread`
    (a list of {symbol, solver, min, max, cv} entries).

    Returns Spread(verdicts in the order of `seeds`, the largest `cv` of the
    spread entries or None when there is none, stable). Raises ValueError
    when the document's seeds are not `seeds` (in that order) or a seed has
    no verdict, and when the run was killed or exited with neither 0 nor 1:
    a sweep that did not finish never reads as stable.
    """
    run = run if run is not None else tools.run
    res = run("seed-rerun", target.target)
    if res.killed is not None or res.exit_code not in (0, 1):
        raise ValueError(f"the sweep gave no verdict (killed {res.killed}, exit {res.exit_code})")
    doc = res.document
    got = tuple(doc.get("seeds") or ())
    if got != tuple(seeds):
        raise ValueError(f"the sweep ran seeds {got}, not {tuple(seeds)}")
    vmap = doc.get("verdicts") or {}
    verdicts = []
    for s in seeds:
        if str(s) not in vmap:
            raise ValueError(f"seed {s} has no verdict")
        verdicts.append(vmap[str(s)])
    cvs = [e["cv"] for e in doc.get("spread") or [] if isinstance(e, dict)
           and isinstance(e.get("cv"), (int, float))]
    return Spread(tuple(verdicts), max(cvs) if cvs else None,
                  all(v == "verified" for v in verdicts))
# triv: return Spread(tuple("verified" for _ in seeds), None, True)


# item: Q18.H7py S13
def fp_report(results: Sequence[GateResult], labels: Mapping[str, Label]) -> FPReport:
    """**H7.** The evaluator: the one function here that reads labels.

    For each result, by its label's kind:
      construct  FAIL: counts under `detected[label.xclass]`; PASS with
                 `label.xclass` in the verdict's `unknown`: held by unknown;
                 any other PASS: a false pass;
      control    FAIL: a false positive; every control counts in `controls`.
    `detected` has a key for every class some construct carries, 0
    included. `fp_interval` is the 95% Wilson interval of the false positives
    among the controls, by composing `fvh.stats`; with no control at all it
    is (0.0, 1.0), the interval that says nothing. Raises ValueError for a
    result whose id has no label, or a label of another kind.
    """
    detected, held, false_pass, fp, controls = {}, 0, 0, 0, 0
    for r in results:
        if r.id not in labels:
            raise ValueError(f"{r.id}: no label")
        lab = labels[r.id]
        if lab.kind == "construct":
            detected.setdefault(lab.xclass, 0)
            if r.verdict.word == FAIL:
                detected[lab.xclass] += 1
            elif lab.xclass in r.verdict.unknown:
                held += 1
            else:
                false_pass += 1
        elif lab.kind == "control":
            controls += 1
            if r.verdict.word == FAIL:
                fp += 1
        else:
            raise ValueError(f"{r.id}: a label of kind {lab.kind!r}")
    interval = stats.wilson_interval(fp, controls) if controls else (0.0, 1.0)
    return FPReport(controls, fp, interval, detected, held, false_pass)
# triv: return FPReport(0, 0, (0.0, 1.0), {}, 0, 0)


if __name__ == "__main__":
    sys.exit(main())
