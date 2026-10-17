"""Q18 — Practice III-C: gate v2, the gate at crate scale (Exercises, Python; solo work)

Commit this module's predictions (the four build-tool deliveries of
specimens/Q18/) BEFORE you open the acceptance tests
(harness/tests/q/gate/test_gate_v2.py) or their recorded fixtures
(harness/tests/q/fixtures/q18/): the fixtures' companions state what the
predictions ask about.

This file is solo work (guard rule 2s), as Q09's gate core was: you write it
yourself. No contract allowlist may name it, and no assistant edits it;
/tutor coaches it as for any other file. It extends your Q09 gate
(harness/q/fvh_q/gate/core.py) from one file to a crate, and it does not
import it: the gate you ship in Lab 3 is this file alone.

Imports: the Python standard library and the frozen core `fvh` (harness/fvh/:
fvh.tools, fvh.stats, fvh.verdicts), nothing else. The core is frozen and
complete; read it, never edit it. Two rules carry over from Q06 and Q09:
statistics code lives only in the core (compose fvh.stats, never re-derive an
interval), and an instrument runs only through `fvh.tools.run` (never a
subprocess, a `cargo build`, a `cargo test` or a check of your own: V20).

How to work this file:
1. Predictions first: the specimens' slots (slots/Q18.slots); record the
   first tries with `scripts/firsttry.sh Q18 --check` before you run
   anything they are about.
2. Replace each hole, in order: H3, H4, H5, H6, H7. A Python hole is a
   function whose body, after its docstring, is the one statement
   `raise NotImplementedError("<item id>")`; the tools count holes on the
   syntax tree, never by searching the text.
3. Run the acceptance tests (harness/tests/q/gate/test_gate_v2.py, frozen):
   `scripts/vcheck harness/q/fvh_q/gate/gate_v2.py`. No solver runs in them:
   they replay instrument results recorded on the fixture crates.
4. Done = `scripts/vcheck --gate harness/q/fvh_q/gate/gate_v2.py` exits 0
   (zero holes and every acceptance test passing), AND
   `scripts/firsttry.sh Q18 --report --strict` exits 0.
5. Then your own live check, outside the tests: the gate over the
   adversarial set (the fixtures' planted cheats and controls, then your own
   capstone plant added to a copy of the set file), one instrument at a
   time (about ten minutes): the fixtures' instruments run on the host (course
   files); a plant copied outside the course tree is of agent provenance, so
   its instruments run in the verification container (fvh.tools.run, Δ145;
   Docker needed):
   `cd harness && PYTHONPATH=q uv run python -m fvh_q.gate.gate_v2 --set
   tests/q/fixtures/q18/set.toml`.
6. Stuck for 20 minutes? /tutor Q18.

This file ships with exactly 5 holes: H3, H4, H5, H6 and H7, each counted
from the syntax tree.

The gate decides from instruments and the delivery's own files, never from
labels: only `fp_report`, the evaluator, reads them.
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
    raise NotImplementedError("Q18.H3py")
# Hint(1): compute everything, then decide: reasons are a list you append to.
# Hint(2): `seed_spread` calls `run` itself; pass yours on, and keep the
#    result it ran by asking it, or by running the sweep through a wrapper
#    that records what it returns.


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
    raise NotImplementedError("Q18.H4py")
# Hint: as Q09's json_complete, with three more checks; a missing `cmd` or
#    `diagnostics` reads as a failed check, not as an error.


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
    raise NotImplementedError("Q18.H5py")
# Hint: `tomllib.loads` on the text; `PurePosixPath(p).name` and `.parent.name`
#    tell the file kinds apart.


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
    raise NotImplementedError("Q18.H6py")
# Hint: the document's verdict keys are strings ("1"), its seeds ints.


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
    raise NotImplementedError("Q18.H7py")
# Hint: one pass over the results; fvh.stats.wilson_interval needs n >= 1.


if __name__ == "__main__":
    sys.exit(main())
