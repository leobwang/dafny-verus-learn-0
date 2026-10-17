# DV5c gaps lane: notes (author-only)

> **Author-only.** The gaps lane's record of the Release B completeness review's gaps: each
> gap re-verified, what was built, the runs, what is left (owner, decision), and the
> DELTAS-ready text for the records lane. Never quote it from a learner-visible file.

Working tree: `authoring` @ 5e5d3ee plus the DV5c lanes' uncommitted work (study mode, as
found; nothing committed). Solver and container jobs one at a time through the wrappers,
inside a 32 GB `systemd-run --user --scope -p MemoryMax=32G -p MemorySwapMax=0` (lane runner
`/tmp/dvl0-dv5c-gaps/run.sh`, which waits for 47 GB available). Scratch `/tmp/dvl0-dv5c-gaps/`
(mode 0700; a scratch git copy of the course, `root/`, for the unseal, the Lab 3 smoke and the
task validation); archive `~/.cache/dafny-verus-learn-0/author-probes/dv5c/gaps/`.

## 1. Gaps and outcomes

See §7 (the critic's gaps, in its order, each re-verified first).

## 2. What was built

**Lab 3's harness pieces (frozen core, `harness/fvh`; tests `harness/tests/core/test_crate_lab.py`).**
- `fvh.statements` (new): the `statements` pin of QPLAN §30 Q64. `expected/<ID>.statements`
  (frozen; new file `expected/Q18.statements`) lists each statement file with the sha256 of
  its shipped form. `check` passes only when every file is tracked, its working copy is the
  committed one, and the committed content differs from the shipped form. `unseal` runs the
  check, then for each sealed stratum of the module (a STRATUM.toml with `module` and
  `archive`) checks the archive's sha256, decrypts it with the pinned age (`~/.local/bin/age`,
  sha256 from the sandbox/truth.toml [[lab]] of the same recipient) and the key that row
  names, parses the tar in memory (regular files under labs/<LAB>/ only), checks the
  plaintext manifest and the stratum's pins (manifest sha256, file count, card ids), and only
  then writes the cards' task files (never over a differing file; a second run is a no-op)
  and `UNSEALED.toml` (date, statements' hashes, archive and manifest sha256).
- `python -m fvh unseal <ID> [--dry-run]` (new command).
- `fvh.batch`: plan keys `statements` (required when a task lies in a sealed stratum; must
  be the pin file's paths; checked at open and at resume, the hashes in the batch note and
  every run.json), `gate` and `gate_sha256` (the gated arm's tool, pre-registered by sha256;
  checked at open and before each gated attempt), arm key `acceptance = "verify" | "gate"`,
  task keys `min_verified`, `symbols` (gate v2's Pins). A task path may be a **crate task's
  directory** (Cargo.toml and src/lib.rs): its src/**/*.rs are editable, its other files
  read-only companions staged with every verification; the gate's target is the crate.
  The gated arm's acceptance callable runs the plan's `gate_crate` on the work copy with every
  instrument through the attempt's ContainerRunner (agent provenance).
- `fvh.executor`: `support_files` (companions written into the work copy at each
  verification, never editable) and `acceptance` (Lab 3's arm G: every Verify runs the
  acceptance tool; a Stop is refused until it passes the current work copy; the run ends
  `gate-pass` when it does; the outcome stays the plain instrument's verdict). `ReplayAcceptance`
  and `LogRunner(skip_acceptance=)` let `fvh report` re-derive a gated run.
- `fvh.runlog`: end cause `gate-pass`. `fvh.report`: a crate run's inputs split into sources
  and companions (rederive) and its target is the crate (reverify).
- The exact-value secret scan (DV4-PLAN §5.7): `fvh.backends.claude.Transport` remembers the
  access tokens its derived snapshots held (in memory only, `secret_values()`);
  `batch.scan_run_dir(rd, exact=…)` withholds a file holding one (finding `exact-token`).
- `scripts/dvl/sandbox.py`: `bench_task` also names a crate card's `…/tasks` directory;
  `build_verify --lab-task <dir>` stages a crate task form file by file under
  `lab-task/<dir>/` (also at a revision, for `--reverify`). `fvh.tools.runners.ContainerRunner`
  reads such a directory as a course path. Test: `tests/sandbox/test_build_verify_dv4r.py`
  `CrateLabTask`.

**Canaries** (DV4-PLAN §14 Q5): a `DVLCANARY` file (first line `DVLCANARY-<random>`) at the top
of `Solutions/`, `paper/solutions/`, `tests/instructor/leak_patterns/`,
`tests/instructor/fixtures/`, `Hidden/` and `~/.cache/dafny-verus-learn-0/`; each public set's
`answers/DVLCANARY` written by `scripts/get_bench.sh` (`dvl.bench.plant_canary`, a token
derived from the set's name and pinned commit, outside the set's digest: `NOT_DIGESTED`);
`sandbox/canaries.sha256` lists 11 trees; the two new sealed archives hold the Hidden/ token.
Tests: `tests/bench/test_get_bench.py` (planting, digest unchanged, re-plant),
`tests/sandbox/test_sandbox.py` (the shipped list names each tree), and
`tests/acceptance/sandbox_doors.py canary` (one fixture per tree: the file hashes to its line
and a staged copy is refused and attributed).

**Hidden truth**: Q13.H3v's and Q17.H3d's reference statements, as Spec fields
(`prose/<item>.toml`, Q15's form) with the canary, sealed by `sandbox/seal_hidden.py` into
`Hidden/labs/Q13/verdicts.tar.age` and `Hidden/labs/Q17/verdicts.tar.age`; two [[lab]] rows
in `sandbox/truth.toml`. Plaintext archived under `dv5c/gaps/hidden-src/`.

**Calibration**: `calibrate.py` covers Q01–Q18 (72 sessions; tutor holes Q16.H1d, Q17.H1d,
Q18.H1d: each the first exercise file's H item of its language, each covered by a leak
pattern cut from its answer; the critic's Q18.H3py is not a Dafny or Verus hole, which
`eval_tutor` and the defaults test require). README and tests updated (16 OK, author-only
cases included).

**Simulations**: the Q16–Q18 case table (README, designed, not run) and the plant
`q16-h1d-plain-induction` (`PLANTS`, the plant-order test).

**Tools**: `loop-dir` reads a guardless Verus `loop` through its top-level
`if <c> { … break … }` exits (test added; forms suite 59 OK); `pins.py --ref --module <ID>`
passes loudly for a module with no verdict item and no reference slot (a whole run with
nothing to check still fails).

## 3. Runs (one job at a time, 32 GB scope; archive `dv5c/gaps/`)

- **Unseal, live** (scratch git copy of the course, stand-in statements committed):
  refused before the commit (`still the shipped form`, then `not committed`), then 36 task
  files written, a second run 0 written / 36 kept (`unseal/`).
- **Lab 3 task validation** (`lab3/check.log`): every possible card's reference passes
  `vcheck --gate` and `--brittleness` (seeds 1–3: verified · verified · verified — stable);
  each stub with only its `external_body` line deleted fails the gate (`precondition not
  satisfied` from `unimplemented!()`, 0 verified). Impossible cards: i01 and i02, a call at
  a = b = 0 (i02: a = 0) lets `assert(false)` verify (the postcondition is unmeetable there),
  and the same probe without the call fails (control); i03 and i04, an honest body fails
  the postcondition, and the postcondition assumed verifies in the learner loop and fails the
  gate (holes counted, `encountered-vir-error`); every task form verifies with its holes.
- **Gate v2 (the twin) live, agent provenance, in the verification container**
  (`lab3/gatev2_refs.log`): each possible card's reference, copied outside the tree at its
  card path, `PASS · UNKNOWN: X07, X14` with all four instruments run (vcheck --gate,
  vaudit, specfreeze --check, seed-rerun stable; widest CV 3.6%).
- **Gate v2 live on the fixture set, host** (`lab3/gatev2_set_host.log`): K1 FAIL (V18 and
  6 reasons), K2 FAIL (count below the pin, `half_up` failed), K3 FAIL (`verified, verified,
  inconclusive`: the recorded seed-3 flip reproduced), C1–C4 PASS; 0 false passes, 0 of 4
  false positives (Wilson 0.000..0.490): the recordings the 80 frozen tests replay hold live.
  The same set through the container is refused: `mksandbox-run --build-verify` has no
  course path for a copy of `harness/tests/q/fixtures/q18/<K>` (§5).
- **Lab 3 composition smoke** (`smoke/`): plan with `statements`, `gate` + `gate_sha256`,
  task `bench/local/q/crate/c01-eq-word/tasks`, arms G (gate) and P (verify), scripted
  replies (no model), every verification in a fresh verification container: G `verified`,
  ended `gate-pass` (its early Stop refused; acceptance `PASS · UNKNOWN: X07, X14`, 4 tools),
  P `failed`, ended `stop`; batch closed; `fvh report Q18` reproduced 2/2; `fvh report Q18
  --reverify all` 2/2 from the run's commit.
- **Truth round trip** (`truth/manifest-checks.txt`): `mksandbox-run --truth … --truth-check
  manifest` Q13 (3 files), Q17 (3), Q15 (50): unsealed, manifest ok.
- **`sandbox_doors.py all`** (`doors-all/`): 90 passed, 0 failed (after the fix round's
  sandbox edits and this lane's: the canary section's 13 controls among them).
- **The Q16 plant** (`q16-plant-check.txt`): both conjuncts of `MulCorrect` fail; H3d's hole stays.
- **Suites**: `harness/tests/core` 519 passed (11 new); `tests/sandbox` 128 OK; `tests/bench`
  11 OK; `test_calibrate` 16 OK (author-only cases run); `test_skill_sims` 16 OK; static
  wrapper suites (`test_tools_static`, `test_forms_static`, `test_practice_tools_static`,
  `test_pcount_static`) OK; `check_course_map` OK; `check_single_route` 0 outside the
  allowlist; `pins.py --chapter Q09` 20 pins 0 problems after re-capturing `py-shipped`
  (stale from this lane's `runners.py` edit).
- **CI**: a first author run (before most of this lane's edits) passed static, hook-test,
  the four verify jobs and `pins --ref` (124 checks), and failed `pins --ci` on that one stale
  pin; it was stopped in the empty-body job so the lane's solver jobs could run and the final
  run would cover the final tree (`ci-author1-partial/`). The final run: §7.

## 4. Findings of this lane

- **Gate v2's container route refuses fixture copies.** `gate_v2.main`'s docstring says an
  agent-provenance copy runs its instruments in the verification container; a copy of a
  `harness/tests/q/fixtures/q18/` crate has no course path for `build_verify` (only units,
  learner files and benchmark tasks do), so `fvh.tools.run` raises `RunnerUnavailable`. A
  plant made from the capstone crate (a unit) and Lab 3's card copies do run there (above).
  Low; owner DV4 (a fixture-tree route) or the Q18 lane (word the docstring for plants of
  course crates).
- **`--lab-task` took only a staged file**: fixed (a staged `lab-task/…` directory is accepted).
- **Tier-internal disjointness sweep** (`sweep/`): 1,879 twin answer lines (≥ 16 characters,
  not in the twin's own learner file) of Q16–Q18's twins, the gate v2 twin, Q18's specimen and
  slot twins and the three solution files, searched in 97 hard-tier learner-visible files
  (chapters, banks, rubrics, problems, answers, learner files, specimens, slots, STRATUM,
  research forms, expected pins, given L7, Q18's frozen tests and fixtures, QPLAN, MODULES,
  DELTAS): 97 hits, every one generic (case arms, signatures, loop headers, `let n =
  a.limbs.len();`, extensionality assertions, separators, `\author`) or a statement the
  learner file states. One structural overlap, no answer line: Q18.H1v's shipped `cast_out`
  is a complete top-down loop with a suffix-value invariant (`r == seq_to_nat(a@.subrange(i,
  n)) % M`), the invariant's domain Q16.H2v asks the learner to find (Q16's chapter removed
  that hint). Low; owner the Q18 lane (DECISION-free: reword or accept as a later-tier file).
  L7 has no twin (a given layer).

## 5. Open (owner, severity)

- **Not this lane's**: the records (DELTAS entries for this round, D1–D4, Δ204 items 1, 2, 5,
  the shortfall notes, W19, the status lines of CLAUDE.md, README and QPLAN): the records lane.
- **The orchestrator (high, before any simulation)**: remove the other lanes' scratch
  (`/tmp/dvl0-dv5b-*`, `/tmp/dvl0-dv5c-*` except a running lane's) or reboot; then the
  simulations owner runs the Q16–Q18 set and re-runs Q13–Q15 (they call the model).
- **The author (high)**: `python3 tests/acceptance/guard_doors.py all` (the guard changed in
  the fix round; it calls a model); `calibrate.py all` (72 sessions, model calls).
- **DV4 (high: Lab 2's judging)**: a truthcheck judging mode (the two-way implication and
  the classification of a delivered statement against a sealed reference, verdict-only
  output), which needs an image rebuild (`sandbox/build-images.sh`: new digests in
  `images.lock`, VERSIONS.md §1.4, the apparatus) and its tests; then the [[lab]] rows' prose
  references are judged in the container.
- **DV4 (high: before Lab 3's Qwen arm)**: agent-mode batch composition (opencode in a
  per-run container through `dvl.sandbox.live_run`, per-run seeds) is not built; Lab 3's
  Claude arm (harness-executed) is composable now.
- **DV5 (high: Lab 1, Lab 2)**: the public pools' validation (`get_bench.sh --validate`:
  dafnybench 785 answers, humaneval-verus 167, vericoding 2,683, minif2f 12; hours of solver
  time, one job at a time), the HumanEval-Verus stripping step (the set ships answers only,
  no task forms: 0 files under tasks/), the shingle scan's recalibration and the cards'
  attestation (`sandbox/attested.toml`: 0 cards).
- **The author (medium)**: one pre-registered reference run per lab (model calls).
- **The guard owner (low)**: refuse `fvh unseal` while a contract is active (rule 2c's list
  names `fvh run`, `resume` and `contract-local`).
- **Tools (low)**: a test for `pins.py --ref --module` on a module with nothing to check;
  pcount's remaining hand corrections; Verus brittleness symbol attribution; the plan's sha256
  as a PREREG field (a template change in Q12/Q15/Q18's answers files: the lab owners).

## 6. DELTAS-ready text (for the records lane to number)

**Δ2xx · Lab 3's harness pieces: the statements pin and `fvh unseal`, crate tasks, the gated
arm, the exact-value secret scan; canaries planted; Q13's and Q17's prose references sealed;
calibration over Q01–Q18; two tool fixes — adopted (DV5c gaps lane, 2026-10-12)**
- **Status:** built and tested by the gaps lane of the Release B completeness review; like
  Δ195–Δ205 it names no answer. Detail: `Solutions/plans/DV5c-gaps-notes.md`; archive
  `dv5c/gaps/`.
- **Change:**
  - **QPLAN §30 Q64 built.** `expected/<ID>.statements` (frozen) pins each statement file's
    shipped form by sha256 (`expected/Q18.statements`: `research/q18_statements.{dfy,rs}`).
    `fvh.statements.check` passes only for committed files whose content differs from the
    shipped form; `python -m fvh unseal <ID>` then checks, decrypts (pinned age, the key the
    truth file names for the stratum's recipient), verifies and writes a sealed stratum's
    cards, never over a differing file, with an `UNSEALED.toml` record. A lab plan whose task
    lies in a sealed stratum must name `statements`; the batch note and every run.json carry
    their committed hashes, and `fvh resume` refuses when they changed.
  - **Crate tasks.** A plan task's path may be a crate card's `tasks` directory: its
    `src/**/*.rs` editable, its other files read-only companions staged at every
    verification (`Executor(support_files=)`); the lab gate's lever check compares the
    two directories (`build_verify --lab-task <dir>` stages the form file by file); `fvh
    report` re-derives and re-verifies crate runs.
  - **The gated arm** (QPLAN §28.5's arm G): `acceptance = "gate"` with the plan's `gate`
    and pre-registered `gate_sha256`: every Verify runs the gate's `gate_crate` on the work
    copy (each instrument in a fresh verification container, provenance agent), a Stop is
    refused until the gate passes the current copy, and the run ends `gate-pass` when it
    does; arm P (`acceptance = "verify"`, the default) is unchanged. The outcome is the
    plain lab gate's verdict in both arms.
  - **The exact-value secret scan** (DV4-PLAN §5.7): the Claude transport keeps its
    snapshots' access tokens in memory and the run-directory scan withholds any file that
    holds one (`exact-token`).
  - **Canaries** (DV4-PLAN §14 Q5): `DVLCANARY` files in the reference trees, the hidden
    truth, the author cache and each public set's `answers/` (by `get_bench.sh`, outside the
    digest); `sandbox/canaries.sha256` lists 11 trees; `sandbox_doors.py canary` checks each.
  - **Hidden truth**: Q13.H3v and Q17.H3d's reference statements sealed
    (`Hidden/labs/Q13/`, `Hidden/labs/Q17/`, two [[lab]] rows). The judging step (a
    truthcheck mode for the two-way implication) is still not built.
  - `calibrate.py` defaults Q01–Q18 (72 sessions); simulations README designs the Q16–Q18
    cases and adds a Q16 plant; `loop-dir` reads a guardless Verus `loop` by its
    `if … { break }` exits; `pins.py --ref --module` passes loudly on a module with nothing
    to check.
- **Touches:** Δ146–Δ150, Δ182, Δ197, Δ200–Δ203; `harness/fvh/{statements,batch,executor,
  report,runlog,__main__}.py`, `harness/fvh/backends/claude.py`, `harness/fvh/tools/runners.py`,
  `scripts/dvl/{sandbox,bench,forms}.py`, `scripts/pins.py`, `expected/Q18.statements`,
  `sandbox/{canaries.sha256,truth.toml,README.md}`, `Hidden/labs/{Q13,Q17}/`, the tests.
- **Owner:** the gaps lane; the open items' owners (§7).

## 7. The completeness review's gaps (in its order): re-verified, outcome

| # | gap | re-verified | outcome |
|---|---|---|---|
| 1 | records (DELTAS, D1–D4, status lines) | yes (DELTAS ends at Δ205) | not this lane's (records lane); this lane's text in §6 |
| 2 | full CI on the final tree; empty-body re-gates | yes (newest log was a static FAIL) | **run**: final author run (§8); the empty-body job covers every armed module (Q10–Q12, Q15, Q17 included) |
| 3 | skill simulations Q16–Q18; Q13–Q15 out of date | yes | **designed** (case table, plant, plant checked); not run: lane scratch of other lanes present, model calls (orchestrator, simulations owner) |
| 4 | guard and sandbox acceptance | yes | **sandbox_doors all: 90/90**; guard_doors not run (model calls: the author) |
| 5 | calibration Q16–Q18 | yes | **built** (Q01–Q18, 72); the run is the author's |
| 6 | registry admissions resting on open decisions | yes | DECISION NEEDED (the lane's report) |
| 7 | hard-tier minutes at 0 | yes | DECISION NEEDED |
| 8 | the capstone CLI | yes (no [[bin]]) | DECISION NEEDED |
| 9 | Lab 3's statements pin and unseal | yes | **built** (`fvh.statements`, `fvh unseal`, plan key), tested, run live on the real archive in a scratch copy |
| 10 | crate tasks, arm G, agent-mode composition | yes | **built** crate tasks and the gated arm (tested; container smoke passed); agent-mode composition open (DV4) |
| 11 | gate v2 never live | yes | **run** live: the set on the host (matches the recordings), the Lab 3 references through the container with agent provenance (8/8 PASS); fixture copies cannot enter the container (§4) |
| 12 | canaries | yes (list empty) | **planted** (11 trees) and checked per tree |
| 13 | hidden truth | yes (only Q15 sealed; truthcheck manifest/validate only) | **sealed** Q13 and Q17 (round trip in the container); the judging mode open (DV4, needs an image rebuild) |
| 14 | public pools | yes (no validation.jsonl; humaneval-verus has no tasks/) | open (DV5: hours of solver time; the stripping step is a design item) |
| 15 | Lab 3 task validation thin | yes | **run**: seeds 1–3 and gate v2 on every possible card, stubs not trivially solvable, refutation and control probes for i01/i02, honest-fails and assume-gate-refused for i03/i04; attestation waits on gap 14's scan |
| 16 | reference runs | yes | open (model calls: the author); the no-model Lab 3 smoke ran |
| 17 | tier disjointness sweep | yes | **run**: no answer line leaks; one structural overlap noted (§4) |
| 18 | D2's reading | yes | DECISION NEEDED |
| 19 | `big_sub` vs `sub` | yes | DECISION NEEDED |
| 20 | the key's custody | yes | DECISION NEEDED |
| 21 | D6 probe (step 4c) | yes | the user's (open) |
| 22 | small tool gaps | yes | **fixed**: loop-dir on a guardless `loop`, `pins --ref --module` on an empty module, the exact-value secret scan; open: pcount's hand corrections, Verus brittleness symbols, the plan sha256 as a PREREG field |

## 8. CI on the final tree

- `scripts/ci.sh --author` (32 GB scope; `ci-author2/`, 15,925 s): static, hook-test, the four
  verify jobs, pins (`--ci` and `--ref`), **empty-body** (every armed module: Q01 8/8, Q02
  16/16, Q03 15/15, Q04 15/15, Q05 13/13, Q06 17/17, Q07 15/15, Q08 16/16, Q09 12/12, Q10 14/14,
  Q11 12/12, Q12 20/20, Q13 7/7, Q14 7/7, Q15 18/18, Q16 4/4, Q17 3/3, Q18 7/7 holes pass the
  gate), wrappers, coexist, paper, rubric and harness PASS; **corpus FAIL** on one pin:
  `D-03`'s vaudit output sha256 (the `trait` finding's message gained the Q17 lane's
  "a trait that a class of its file implements in full is allowed (DV5c)"; kinds and
  outcome unchanged). Re-captured with `test_corpus.py --update D-03`; the corpus job then
  PASS (`ci-author3/`). The pin follows the Q17 trait-lint relaxation, which awaits the
  user's decision: if the relaxation is reverted, re-capture D-03 again.
- `scripts/ci.sh` (the study run, `ci-study/`, 4,265 s): PASS, 12 passed, 2 skipped (author-only), after the D-03 re-capture.
