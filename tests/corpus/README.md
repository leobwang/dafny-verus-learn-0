# The cheat corpus

A verifier that exits 0 has not necessarily proved anything. Some constructs
make verification succeed without a complete proof: an assumption, an axiom,
a trusted or external body, a file the verifier never checked, a weakened
statement, a vacuous precondition. Spec §11.4 catalogs them for Dafny (G1–G22)
and Verus (V1–V24, plus V25 from Δ19), each with the instrument that must
catch it, and DELTAS adds more (the lint rules, `external_body` on a type,
Verus dependency holes, later-layer calls, and others).

This directory holds the **regression fixtures** for that catalog. Each
fixture is a tiny invented program that uses one construct, plus a
`manifest.toml` that records, from real runs on the pinned tools, which course
instruments flag it. Healthy **controls** sit beside them: programs the same
instruments must accept. `scripts/test_corpus.py` replays every fixture and
fails when an instrument stops flagging a construct, starts flagging a
control, or prints different output.

## Scope

The corpus holds **source-level fixtures only**: programs whose source text
uses the construct. Some catalog rows are not source-level. They are verifier
flags on the command line, environment variables, toolchain or IDE settings,
build tooling, and project files that change what is verified (G6–G8, G10,
G14–G16, G19, G21, G22; V16–V20, V22–V25; and the Cargo `[patch]` row). The
wrappers refuse those before any tool runs, or have no code path that reaches
them (they never call `cargo` or `cargo-verus`: V20, V25). The wrapper suites
in `tests/wrappers/` (with the guard fixtures in `tests/hooks/templates/`)
already test that behaviour. Each such row has a manifest of kind
`covered-elsewhere` that names the covering tests, and the runner checks that
they exist. Nothing is built or run for those rows, and nothing in this
directory replaces a binary, sets an environment variable, edits a toolchain
or IDE setting, adds a build script or loads a plugin.

## Layout

```
tests/corpus/
  README.md
  dafny/<ID>/          manifest.toml, main.dfy, and as needed witness.dfy,
                       swap.dfy, frozen.dfy and helper files
  verus/<ID>/          manifest.toml and one crate (Cargo.toml, src/lib.rs),
                       or several crates (`target` names the one the tools
                       run); witness/ and swapped/ are crates of their own;
                       frozen.rs holds a frozen statement
```

A fixture directory is named by its id alone: `tests/corpus/<lang>/<ID>/` is
the canonical layout (Δ109, which supersedes Δ106's `<id>_<slug>/`). The
runner still accepts an `<ID>_<slug>` directory, but that form lets two
directories carry the same id, which the runner does not detect, so no fixture
uses it and `scripts/ci.sh`'s `corpus` job fails any listed fixture whose
directory is not `<lang>/<ID>`.

A fixture directory holds only plain files, every one listed in `files`. It holds no build
output (no `target/`, `.verus-log/` or Dafny `*-py/`), and no symbolic links.
No path component may contain one of the reference-material stems listed in
`REFERENCE_STEMS` of `scripts/check_course_map.py`, the sealed-material prefix
that guard rule 1 reserves (Δ105), or a reserved registry name. Every Dafny
`include`, Rust `#[path]` or `include!`, and Cargo `path` dependency must
resolve inside the fixture's own directory. The guard content-scans this tree
(Δ105), and the runner checks all of these rules.

**Ids.** Use a catalog row (`G01`–`G22`, `V01`–`V25`, with a letter added for
a second fixture of the same row, such as `V07b`), a DELTAS addition (`D-<n>`
for Dafny, `V-<n>` for Verus), or a control (`C-<n>`).

## The manifest

```toml
id = "G01"             # the directory's id
lang = "dafny"         # "dafny" | "verus" (= the parent directory)
half = "Q"             # "Q" | "R": the Q09 half or the R13 half (design §9.2 item 2)
xclass = "X01"         # spec §5.6 taxonomy, X01..X18; "" for a control
kind = "construct"     # "construct" | "control" | "covered-elsewhere"
title = "..."          # one neutral line
files = ["main.dfy"]   # every file of the fixture except manifest.toml; [] when covered elsewhere
target = "upper"       # optional: what the tools run, relative to the fixture
                       # (default main.dfy for Dafny, the fixture directory for Verus)
plain_exit = 0         # the plain verifier run's exit code, captured (not for covered-elsewhere)

[[expect]]             # one table per instrument
tool = "vaudit"        # see Instruments
outcome = "flagged"    # "flagged" | "clean" | "unknown"
kinds = ["..."]        # what the tool reported (finding kinds, hole kinds, W-codes)
output_sha256 = "..."  # sha256 of the tool's normalized output (see Hash rules)
summary = "..."        # a short non-content summary: counts and locations, never messages
argv = ["..."]         # optional: the exact command, run from the course root
exit = 1               # optional: the captured exit code
covered_by = ["tests/wrappers/test_x.py::Class::test_y"]   # covered-elsewhere only
```

A **construct** lists every instrument that flags it, and may also list ones
that pass it. It needs at least one table whose outcome is `flagged` (or
`unknown`, below). A **control** lists every instrument it was run through,
and each one's outcome is `clean`. A **covered-elsewhere** row has
`files = []`, no `plain_exit`, `output_sha256`, `argv` or `exit`, and a
`covered_by` list in every table. A reference is either
`tests/<file>.py::Class::test_method` or a guard fixture named by its `why`:
`tests/hooks/templates/<file>.jsonl (<why text>)`.

Comment lines in a manifest carry its provenance: the capture date and pins,
the plain run's counts, and the hash rule. The runner ignores them, and
`--update` keeps them.

## Instruments

Every command runs from the course root on the fixture's repo-relative paths,
and only through the course wrappers. `<dir>` is the fixture directory and
`<target>` is its target.

| tool | Dafny | Verus | flagged when |
|---|---|---|---|
| `vcheck --gate` | `scripts/vcheck --gate <target>` | the same | exit 1 |
| `vaudit` | `scripts/vaudit <target>` | the same | exit 1 |
| `specfreeze --check` | `scripts/specfreeze --against <dir>/frozen.dfy <target>` | `scripts/specfreeze --against <dir>/frozen.rs <target>/src/lib.rs` | exit 1 |
| `witness` | `scripts/vcheck --gate <dir>/witness.dfy` | `scripts/vcheck --gate <dir>/witness` | exit 1: no concrete call meets the requires |
| `swap-to-false` | `scripts/vcheck --gate <dir>/swap.dfy` | `scripts/vcheck --gate <dir>/swapped` | **exit 0**: the conclusion replaced by `false` still verifies, so the context is vacuous |
| `seed-rerun` | `scripts/vcheck --brittleness <target>` | the same | exit 1 |
| `solver-swap` | `scripts/vcheck --brittleness --solvers <target>` | (none: one solver) | exit 1: a seed or a bundled solver does not verify (solver diversity, not independent checking) |
| `reach` | `scripts/dvl/reach.py --manifest <dir>/reach.toml <target>` | `scripts/dvl/reach.py --manifest <target>/reach.toml <target>` | exit 1: a denied name or module, a missing required root, or reach into a reference tree (the challenge tier, Δ402) |
| `json-completeness` | (none) | the plain run's `--output-json` `verification-results` | `success` is not true, `is-verifying-entire-crate` is not true, or `verified` < 1 |
| `lint` | (none) | (none) | not runnable on its own: the lint runs inside `vaudit` and `vcheck --gate`, so record its rule ids under those tools |

`specfreeze --check <ID>` compares a registry module with its pin. A corpus
fixture is not a registry module, so the corpus spells the instrument
`specfreeze --check` and runs `--against` on the fixture's frozen file. A
Dafny refinement (a `main.dfy` with `module X refines Y`) is checked against
`frozen.dfy` in refinement mode, and every other fixture in hash mode.

Any exit code other than 0 or 1 is never an outcome: 2 is usage, 3 a refusal,
124 the wall-clock kill, and 137 or 143 (or a `killed(memory)` verdict) a
memory kill. The fixture fails.

**The plain run** is the verifier with no audit and no course policy, the run
whose exit code a naive grader would trust. For Dafny it is
`dafny verify <target> --resource-limit <pin> --cores <pin> --solver-path <pinned z3>`,
with `frozen.dfy` placed first for a refinement. For Verus it is
`verus <crate root> --crate-type=lib --crate-name <name> --rlimit <pin> --num-threads <pin> [--import/--extern/-L of the path dependencies] --output-json --error-format=json --time`.
It runs without `--no-cheating`, and its path dependencies are verified and
exported first, as the wrappers build them. Both run through dvl's capped job
plumbing, under the 8 GB and 16 GB caps. In a recorded `argv`, `<deps>` stands
for the run's dependency output directory.

**Grader-only classes (UNKNOWN).** X07 (vacuous hypotheses), X08 (weakened
spec) and X14 (lookup-table overfitting) need an oracle the learner never
sees. On them a gate must answer UNKNOWN and never PASS (spec §5.6; design
§11.2, gate v2). `vcheck` has no UNKNOWN verdict, so the runner reads a
`vcheck --gate` pass (exit 0) on a fixture of those classes as `unknown`,
never as `clean`, and a construct held only by that rule counts as caught. Two Verus fixtures, V13c and V14, are
held only this way, because no wrapper instrument flags them. The other
grader-only fixtures are caught by `witness`, `swap-to-false` or
`specfreeze --check`, and the summary line names the ones held only by
`unknown`.

## Hash rules

`output_sha256` is the sha256 (UTF-8) of the tool's output after
normalization. Each language keeps the rule its fixtures were captured under:

- **Dafny.** Concatenate stdout and stderr. Replace the course root path with
  `<root>` and the run's scratch root with `<scratch>`. Replace
  `raw output: <path>` with `raw output: <raw>`, and the brittleness spread
  clause (`widest spread <symbol> <a>..<b> (CV <x>%)`) with `<spread>`.
  Collapse every whitespace run to one space and trim the ends.
- **Verus.** Take stdout, then, when stderr is not blank, a line
  `--- stderr ---` followed by stderr. Remove `<root>/`. Replace the run's
  scratch root, and the rest of the path that follows it, with `<SCRATCH>`.
  Strip trailing blanks from each line, strip the whole text, and end it with
  one newline. The brittleness spread numbers stay in the hash. They are
  stable on this host and toolchain, so re-pin them after a toolchain change.
- **json-completeness.** Hash the `verification-results` object as
  `json.dumps(obj, sort_keys=True)` plus a newline.

The scratch root is the per-run directory the runner creates under
`$DVL_SCRATCH` (by default `/tmp/dvl0-corpus-<uid>`) and passes to the tools
as their `DVL_SCRATCH`.

## The runner

```
python3 scripts/test_corpus.py --list                  # id, lang, half, kind, X class, directory
python3 scripts/test_corpus.py --ci                    # the whole corpus (the default mode)
python3 scripts/test_corpus.py --ci --only V-2 G01     # a selection: ids, lang/id or directories
python3 scripts/test_corpus.py --update --only V-2     # author-only: re-pin hashes
```

`--ci` checks the items below. `scripts/ci.sh`'s `corpus` job runs `--list`,
then `--ci`. An absent corpus fails that job (Δ108, Δ109): a missing runner or
`tests/corpus/`, a failed or empty listing, or a listed fixture outside
`tests/corpus/<lang>/<ID>/` fails it before any solver job starts.

1. **Statically, for every fixture:** the manifest format; the id against the
   directory, language and kind; `files` against the disk; names, build
   outputs and links; includes and path dependencies kept inside the fixture;
   every `covered_by` reference resolved (pytest ids through the test file's
   AST, guard fixtures through their `why`).
2. **For each selected construct and control:** the plain run's exit equals
   `plain_exit`, and for each `[[expect]]` table the observed outcome equals
   the recorded one and the normalized output's sha256 equals
   `output_sha256` (and `exit` and `argv` too, where they are recorded). A
   run that leaves a new file in the fixture fails.
3. **For the whole corpus (when there is no selection):** in each language,
   each half (Q, R) covers every X family that the language's constructs and
   covered rows cover; every catalog row (G01–G22, V01–V25) has a fixture;
   and there are at least six controls per language (Δ106).

It prints `PASS` or `FAIL` per fixture, with locations (`manifest.toml:<line>`)
and never tool messages. Each instrument's observed output, raw and
normalized, goes to a file in the run's scratch directory, and a failing line
names that file. The scratch directory is deleted after a passing run unless
you pass `--keep`. Exit codes: 0 means everything passed, 1 means a check
failed or the memory preflight did, 2 is usage, and 3 is a refusal (`--update`
outside the author's context, or a missing pinned toolchain).

**Memory (CLAUDE.md §Resources).** Fixtures run one at a time by default.
`--jobs N` (at most 4) keeps N fixtures in flight, but every solver job still
takes its language's dvl pool slot with `DVL_DAFNY_JOBS=1` and
`DVL_VERUS_JOBS=1`, so at most one Dafny job (8 GB cap) and one Verus job
(16 GB cap) run at once. Before the first solver job, MemAvailable must cover
the caps that can run at once plus a 15 GB reserve, or nothing starts.

**`--update`** is author-only. Like `reference_lint.py`, it refuses unless CI
is set to true or the three-condition test holds (inside git, a linked
worktree, and HEAD not on a learner branch; spec §7.4). In study mode the
guard refuses it as well (rule 1b; also its `--u…` prefixes, which the parser
rejects anyway, and `python3 -m test_corpus --update`; Δ109). `--list`,
`--ci` and `--only` stay open to the learner. It runs each selected
fixture twice. Where both runs agree and every observed outcome, `exit` and
`plain_exit` equal the recorded ones, it rewrites `output_sha256` in place,
filling a missing one and a missing `plain_exit`, and leaves every comment
and every other value as it was. It never changes an outcome, an exit or a
recorded `plain_exit`. A moved outcome is a decision for the author, made by
editing the manifest by hand.

## Adding or changing a fixture

1. Work in authoring mode, in the authoring worktree. `tests/corpus/` is guard
   class 2g for writes.
2. Write a tiny **invented** program in a new directory
   `tests/corpus/<lang>/<ID>/`, named by the id alone. Never copy or
   paraphrase course reference material, and keep includes and dependencies
   inside the fixture.
3. Write `manifest.toml` by hand: the metadata, `files`, and one `[[expect]]`
   table per instrument with the outcome you expect, a `kinds` list and a
   non-content `summary`. Leave out `output_sha256` and `plain_exit`.
4. Run `python3 scripts/test_corpus.py --update --only <ID>`. It refuses if an
   observed outcome differs from the one you wrote. If it does, look at the
   observed output it names and decide whether the program or the
   expectation is wrong.
5. Run `python3 scripts/test_corpus.py --ci` for the whole corpus. The halves
   rule may need the fixture's `half` changed.

Recorded outputs always come from real runs on the pinned tools and are
never invented. After a toolchain or wrapper change that alters tool wording,
re-run `--update` and review the diff: only `output_sha256` lines should
move. A change to `scripts/dvl/pins.toml` that names a wording the tools
reported as unlisted can also rename a reported kind. When Δ109 added the
`{:extern}` requires-clause text, D-18's `vaudit` kind `audit-other` became
`audit-extern-requires`. Fix such a `kinds` list (and its `summary`) by hand,
then re-pin the hash with `--update`.
