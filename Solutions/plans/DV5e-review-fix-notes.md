# DV5e review fix lane: the three reviews' findings (tools, guard and study root, leakage and claims)

Author-only notes (reference class). The lane's brief: re-verify each finding of the three
DV5e reviews, fix every major and the cheap minors, re-run the affected checks, and give
DELTAS-ready text. Like Δ195–Δ225, nothing here names an answer, a reference statement or
an invariant. Memory share 32 GB (each solver job and each scan inside `systemd-run --user
--scope -p MemoryMax=32G -p MemorySwapMax=0`, under the wrappers' own caps, one job at a
time; `free -g` showed 92–97 GB available before each). Scratch `/tmp/dvl0-dv5e-reviewfix/`
(removed at the end); archive `~/.cache/dafny-verus-learn-0/author-probes/dv5e/reviewfix/`.
No model was called; no lab task was run.

## 1. Outcomes, finding by finding

Review 1 (tools):

| # | sev | finding | reproduced | outcome |
|---|---|---|---|---|
| T1 | major | the band rule is checked by no script; exception kinds are labels | yes (the three edits passed before; now each fails, test cases below) | **fixed** |
| T2 | minor | the exact test counts pool-common shapes (docstring says never) | yes | **fixed, option (b)**: docstrings now say what the code does; option (a) measured and not taken (§2.2); a fixture added. DECISION for the user (§3) |
| T3 | minor | `get_bench --validate` excludes a killed or timed-out audit | yes (code path) | **fixed** |
| T4 | minor | HIDDEN_CHECKS_HELD not tied to the sealed truth judged | yes | **fixed** (manifest-level tie; per-file tie not built, §4) |
| T5 | minor | pcount: attributes before the name; block comments | yes (HEAD counter: `not found` rc 2; 6 proof lines for a 1-line body) | **fixed** |
| T6 | minor | `site_of` picks the first of two sites; strips a module as the crate | yes | **fixed** |
| T7 | minor | Q12 and Q18 describe the lab gate before D24 | yes | **fixed** |

Review 2 (guard and the study root, D20):

| # | sev | finding | reproduced | outcome |
|---|---|---|---|---|
| G1 | minor | calibrate's drop-in outlives a refused or interrupted case; skill_sims' drop-in outlives its case | yes (code order: check_memory before reset; reset outside any finally) | **fixed** |
| G2 | minor | an orphaned study root is not detected by skill_sims setup; CLAUDE.md item 2 gives no removal step | yes (`lane_scratch` by design ignores study roots) | **fixed** in the tool; CLAUDE.md text for the records lane (§5) |
| G3 | minor | one DVL_SCRATCH shared by every case | yes (code) | **fixed** |

Review 3 (leakage and claims):

| # | sev | finding | reproduced | outcome |
|---|---|---|---|---|
| L1 | major | Q13's `strong` gloss gets `requires` backwards; Q15 §5 never says the two checks disagree | yes (truthcheck.py's r1–r4: an added requires gives `weak`, a dropped one `strong`) | **fixed** in Q13 §2 and Q15 §5; `truthcheck.py`'s docstring waits for the next image rebuild (§4) |
| L2 | major | the judge prints six outcome words per row, not one verdict word | yes (`_clean` keeps them) | **claims fixed** (Q13 §2, Q15 §5, Q17's table, both Q15 headers); the run rule is the user's decision (§3) |
| L3 | minor | CLAUDE.md:5 says every lab card was re-attested | yes (`attested.toml` has no `lab2pub` entry) | **text for the records lane** (§5); this lane does not write CLAUDE.md |
| L4 | minor | lab2pub STRATUM says the statements are nowhere learner-visible | accepted on the review's evidence (installed upstream files) | **fixed** (STRATUM.toml and `lab2pub.py`'s STRATUM_HEAD; Q15 §6.2) |
| L5 | minor | the draw "fixed beforehand"; NOTICE omits `pub open`; vp2's kept comment | (1)(2) yes; (3) accepted on the review's evidence | (1)(2) **fixed**; (3) **not fixed** (§4: the form is in the sealed Q15 archive) |
| L6 | minor | rubric D12 quotes the `--judge all` line without `--truth` | yes (`fvh` refuses it) | **fixed** |
| L7 | minor | the test decoy is, renamed, a twin's sealed loop shape | yes (it was the one new hit) | **fixed** (0 new hits; the scan's one remaining hit on the file predates the round) |

## 2. As built

### 2.1 T1: the band, checked (`scripts/check_course_map.py`)

- `PRACTICE_BANDS` (design §7.5's admissibility gate: intro D 1–10 / V 1–15, intermediate
  10–30 / 15–45, hard 30–80 / 45–120) and `OUT_OF_BAND`: item → (proof lines, kind,
  decision) for each admitted item outside its band. The figures are the code notes' pcount
  counts as the registry's exception reasons state them: Q15.H1d 5, H1v 4 (short-format
  band, D2); Q15.H3d, H4d, H5d 0, H3v 7, H5v 0 (hidden-check spec, D21); Q17.H3d 10
  (statement-item, D6); Q18.H1d 12, H1v 19 (short-format band, D7); Q18.H2d, H2v 0 (the
  learner's proof lines: statements only; statement-item, D9).
- `band_problems` (the coverage group, beside the kind checks): an exception only on an
  OUT_OF_BAND item, of its recorded kind, whose reason names its decision; every admitted
  OUT_OF_BAND item carries one. `out_of_band_problems`: every entry is a Dafny or Verus item
  of a practice module, admitted, with a figure outside its band.
- What it does not do: it never counts a reference (the checker never reads reference
  material); an item re-probed outside its band joins the table with its notes' figure.
- `scripts/test_course_map.py`: the review's three edits (Q15.H3d's exception deleted;
  Q15.H4d's retyped to short-format; a short-format exception added to Q14.H1d, in band)
  each refused; a reason with no decision (Q18.H1v); an OUT_OF_BAND item the registry gates
  (Q15.H1v); a unit case on the table (in-band figure, a Python item, a concept module).
  The earlier case that admitted Q14.H3d with a short-format exception now expects refusal
  (it is gated in the registry, and in band by no record). 396 passed, 0 failed.
- `MODULES.toml`'s schema comment names the three kinds and OUT_OF_BAND.

### 2.2 T2: the scan's exact test (`scripts/dvl/sandbox.py`)

Option (a) (pool-common shapes set aside for the exact test too) was built and measured with
the attest lane's `after.py --plants` (production code, Lab 3's 36 files decrypted into
memory only) and an invented-card probe, then reverted:

- planted whole answer regions caught 623 → 608 of 626; single answer lines 2,911 → 2,676 of
  2,934; three-line runs 3,364 → 3,250 of 3,444; short lines inside a run 1,199 → 1,135 of
  1,256; renamed rows unchanged; the 78 attested cards still clean under both.
- The review's textbook Verus max loop passes under (a); the Dafny sum lemma is still caught
  under (a) (its shape is course-visible, not pool-common).

So (a) trades 15 caught whole-region copies for fewer refusals of an author's invented card,
and D25 asks for both "generic structure stops counting" and "a real copied answer run is
still caught". Kept: (b), fail-closed. ScanIndex's docstring, `author_scan`'s and
`sandbox/attested.toml`'s header now say that pool-common shapes are set aside for the
renamed test only, and that an exact copy of a twin's span, names and all, still counts. New
fixture `AttestGenericAndRenamed.test_an_exact_copy_of_a_pool_common_shape_still_counts` (a
renamed copy of a shape two pool files hold passes; the exact copy is refused). The
attestations are unchanged (the rule as attested is the rule as built).

### 2.3 T3, T4, T5, T6

- **T3** (`scripts/dvl/bench.py`): `AUDIT_INCOMPLETE` and `audit_run_verdict`, read as
  `scripts/vcheck`'s lab gate reads them: an `audit-error` or `audit-incomplete` finding whose
  message holds `killed(memory)` gives verdict `killed(memory)`, one with `(inconclusive` or
  `wall-clock` gives `timeout`; the vaudit branch sets that verdict, so `judge_row`'s RETRY
  re-runs the row. A real finding (or an `audit-error` of another cause) still excludes.
  `tests/bench/test_get_bench.py` `AuditRunIncomplete` (3 cases).
- **T4** (`scripts/check_course_map.py`): `sealed_labs` counts a lab only when its archive
  is on disk and hashes to the pinned sha256 (ciphertext only), and returns its pinned
  `manifest_sha256`; `HIDDEN_CHECKS_HELD` entries are (Δ, manifest_sha256), and
  `hidden_check_problem` refuses the kind when the pinned manifest differs ("a re-seal:
  re-judge it, or confirm its references unchanged and record the new manifest"). Q15's
  entries name the DV5e manifest (627dab2b…): the lane compared the archived plaintext
  MANIFEST.sha256 files of DV5d's judged seal (6010a225…) and DV5e's (paths compared; only
  `judge/oracles.py` and `SEALING.md` changed besides the twenty new public-card files), as
  the review did. Q13 (1b5525a8…) and Q17 (f83b64b2…) are unchanged since Δ220.
  `scripts/test_course_map.py` links `Hidden/` into the throwaway root; the unit case covers
  a matching manifest, a re-seal, an archive whose bytes differ, a missing archive and an
  unreadable pin file, and requires every committed entry to name a 64-hex manifest.
- **T5** (`scripts/pcount.py`): `find` allows `{:attr}` between the keyword and the name;
  `strip_comments` blanks block comments (nested, across lines) and string and character
  literal contents, keeping the line count, before `count` and `stmt_lines`. A sweep of
  every declaration in the twins (HEAD counter against the new one, names taken from
  comment-free text; archive `pcount-sweep.txt`): no Q10–Q18 count of a declaration the old
  counter found changed (only declarations it missed, all with an attribute, are now
  counted), so OUT_OF_BAND's figures stand; concept-module counts with block comments in
  their bodies changed (Q08, Q09; no band applies there). `tests/wrappers/test_pcount_static.py`
  `Layout` (3 cases).
- **T6** (`scripts/vcheck`): `site_of(sites, sym, lang, crate=None)`: a run name two sites
  share gives None; the leading segment is stripped as the crate prefix only when it names
  no module or type of the target's sites and, when known, equals the crate's name
  (`verus_crate_name`: a crate whose module tree holds the file, or a standalone file with
  no Cargo.toml above). `--ref --brittleness` passes the crate. `tests/wrappers/test_forms_static.py`
  gains the review's three cases and two more.

### 2.4 G1–G3 (the study root's harnesses)

- `tests/acceptance/guard_doors.py` `case_scratch(base, case_id=None)` (one source for the
  three tools): the case's DVL_SCRATCH is `<study root>/dvl/<case>`; every other entry under
  `dvl/` is removed first; `case_id=None` empties it. guard_doors' `run` (now `run_door` per
  door) and calibrate's `run` (`run_case` per case) empty it in a `finally`.
- `tests/instructor/calibration/calibrate.py`: each case resets the clone and empties the
  scratch before `check_memory`, and the loop's `finally` resets the clone and empties the
  scratch, so a Refusal or an interrupt leaves no drop-in and no wrapper run.
  `test_calibrate.RunLeavesNothing` (a synthetic git clone, the session stubbed, the second
  case refused by memory).
- `tests/instructor/simulations/skill_sims.py`: `stale_study_roots` (setup refuses while
  any other `/tmp/dvl0-study-*` of this user exists, and any entry beside the path down to
  this run's own study root); `live_dropins` and `phase_turn`: a drop-in still in the clone
  belongs to the case whose turn first meets it, and another case's turn is refused until
  `plant --restore`; each case's DVL_SCRATCH is its own, kept over resumed turns. Three new
  tests in `test_skill_sims.py` (31 OK).
- READMEs: calibration, simulations and acceptance say where the scratch goes and that no
  learner study session should run on the host while a drop-in is in a study clone.

### 2.5 L1, L2, T7, L4–L7 (text)

- Q13 §2: the outcome words are named and glossed; `strong` = "claims more, or demands
  less: a `requires` dropped, say"; `weak` = "says less, or demands more: a `requires`
  added, say".
- Q15 §5: the row's outcome words; the two checks read a changed `requires` in opposite
  directions (this check: added → `weak`; the oracles' `classify` and H11's `Verdict`: added
  → `STRONG`, dropped not seen).
- Q17's instrument row, the headers of `Q15_Lab2Specs.dfy` and `lab2_specs.rs`: the outcome
  words behind the verdict word.
- Q12 §4.3 and §6's instrument table, Q18 §5 (arm P): the lab gate also applies the
  assumption audit (D24).
- `bench/local/q/lab2pub/STRATUM.toml` and `lab2pub.py`'s STRATUM_HEAD: the statements are
  in no course file, sealed for the grader, and held by the installed upstream sets. Q15
  §6.2: the same parenthesis; the redraw rule "amended once before any seal". `NOTICE`:
  "(Verus) each kept spec fn made `pub open` (one marked `closed` upstream stays closed,
  made `pub`)".
- `paper/rubrics/Q15_rubric.md` D12: "(the chapter's §6.4 line, which names the archive)".
- `tests/sandbox/test_sandbox.py`: the decoy loop is a shape no twin holds; the pool-shape
  test's decoys follow it.

## 3. Runs (final tree)

- `scripts/check_course_map.py`: course map OK (49 modules, 18 authoring, 138 import files,
  81 coverage rows); `scripts/test_course_map.py` 396 passed, 0 failed.
- `chapter_lint --all` 18 chapters, 0 problems (after `pins.py --update --chapter Q15
  --entry units`, which the two header edits made stale; 14 fence lines, exit 0).
- `pins.py --ci --module` Q15 60, Q12 32, Q13 11, Q17 15, Q18 26 pins, 0 problems each.
- `update_rubric_pins.sh --check`: 111 pins over 18 rubrics current.
- The leak README's verifier: 18 modules over 1,631 public files, OK (after the last edit).
- `lab2pub.py build --check` 10 cards current; `specfreeze --check Q15` 0; `gen_units
  --check` 37 units match.
- `tests/sandbox` 172 OK; `tests/bench` 60 OK; `tests/wrappers` static suites 347 OK (1
  skipped); `tests/instructor/calibration` 18 OK; `tests/instructor/simulations` 31 OK;
  `scripts/test_hooks.sh` 6,806 passed, 0 failed (the hook is unchanged).
- `scripts/ci.sh --author --job static --job rubric`: PASS, 2 passed, in 421 s (log copied
  to the archive, `ci-static-rubric/`).
- The scan (ScanIndex.hits, new since HEAD) over every file this lane touched: no new hit in
  a learner-visible text file; the scripts' new hits are generic Python shapes (a
  `tomllib.loads` try/except, a string-scanning loop, `for x in y: if x in z`) and one prose
  shape in `tests/acceptance/README.md`.
- Not re-run: `tests/wrappers`' tool suites and `tests/ci` (the CI `wrappers` job; this
  lane's wrapper changes are static and their static suites pass), the full CI.

## 4. Decisions for the user, open items

**DECISION NEEDED (L2).** The prose-item judge prints, per row, the verdict word and six
outcome words that show which side and direction differ from the sealed reference; the
learner can run it as often as they like. Options: (a) `truthcheck` prints only `verdict`
and `why` for prose rows (needs an image rebuild and re-pinning); (b) keep the output (the
text now says what it prints) and add a rule to the chapters: run the check once per item,
after the statement is final, and report that first run (A7 records it), as with
`firsttry`; (c) keep both and record it as a known limit. Recommended: (b) now, (a) at the
next image rebuild.

**DECISION NEEDED (T2).** D25 asks both that generic structure stop counting and that a
real copied answer run still be caught; the exact test meets the second at the cost of the
first for pool-common shapes. Options: (a) set pool-common shapes aside for the exact test
too (measured: 15 of 626 whole-region copies and 235 of 2,934 single lines no longer
caught); (b) keep the exact test fail-closed, as built and now documented; (c) (a) but only
for spans of structure-and-keyword tokens. Recommended: (b).

Open (owner, severity):

- **The image owner (medium; next image rebuild).** `sandbox/image/truthcheck.py`'s
  docstring (line 51): "strong: only the first (it claims more, or demands less); weak: only
  the second (it says less, or demands more)"; then re-capture the Q13 and Q15 chapter pins
  and re-run the leak verifier. Not edited here: the file is an image input.
- **The kits lane (low; at the next Q15 re-seal).** vp2's form keeps the comment of a
  proof block the transform removed: `benchstrip`'s `verus-lab2-form` should drop the
  comment lines directly above a removed proof statement or block; then rebuild vp2's form,
  update its `form_sha256`, re-run C1, C4 and `build --check`, re-seal Q15 and re-confirm
  HIDDEN_CHECKS_HELD's Q15 manifest. Not done here: the form is in the sealed archive. The
  upstream answer file the learner installs holds the same comment and the proof.
- **The tools owner (low).** T4's tie is per manifest; a per-item tie (the sha256 of each
  item's sealed reference files) needs the plaintext manifest, which a study checkout does
  not have; a manifest digest the seal records for each file would allow it. T1's figures
  are recorded, not counted: an author-mode cross-check that maps items to their twins'
  declarations and runs pcount would close it.
- **The records lane (low).** §5's CLAUDE.md text.
- **The author (as Δ225).** `calibrate.py all`, the simulations and `guard_doors.py all`
  meet these harness changes at their next live run.

## 5. Text for the records lane (CLAUDE.md; this lane does not write it)

- CLAUDE.md:5, the **Armed** line, Lab 3's clause: "its 36 task files are attested,
  re-attested with every Lab 1 card and Lab 2's twenty local cards under the recalibrated
  scan (78 entries; Lab 2's ten public cards are not attested yet)".
- CLAUDE.md §Authoring item 2, after the study-root sentence: "Before removing a lane's
  scratch, run its harness's `cleanup`, or remove `/tmp/dvl0-study-<phase>-<lane>/` too:
  a study root lies outside the tripwire, and `skill_sims.py setup` refuses while one is on
  the host."

## 6. DELTAS-ready text (for the integration lane to number)

### Δ2xx · The DV5e review fix round: the band checked against a record, the hidden-check record tied to its seal, the scan's exact test documented, the audit retry, pcount's layout, `site_of`'s ambiguity, the study root's leftovers, the hidden check's outcome words and `requires` direction, the lab gate's text — adopted (DV5e, 2026-10-13)

- **Status:** three reviews of the DV5e round (tools; the guard and the study root; leakage
  and claims) raised 17 findings (3 major, 14 minor). The fix lane reproduced all 17 (two on
  the review's evidence), fixed the 3 majors (one in the text, its run rule the user's
  decision) and 12 minors, and carries 2 (an image docstring, a sealed form). Like
  Δ195–Δ225, it names no answer. Detail: `Solutions/plans/DV5e-review-fix-notes.md`.
- **Change:**
  - **The band is checked** (`scripts/check_course_map.py`): `PRACTICE_BANDS` and
    `OUT_OF_BAND`, each admitted item outside its tier's band with its proof lines (the code
    notes' pcount figures), its exception kind and the user's decision; the coverage group
    refuses an exception on any other item, one of another kind, one whose reason names no
    decision, and an admitted OUT_OF_BAND item with none. The checker records the figures;
    it never counts a reference.
  - **The hidden-check record is tied to its seal:** `sealed_labs` counts a lab only when
    its archive is on disk with the pinned sha256; `HIDDEN_CHECKS_HELD` names the
    `manifest_sha256` each hold applies to (Q15's re-seal confirmed against the judged one:
    only `judge/oracles.py` and `SEALING.md` changed besides the new public cards).
  - **The scan's exact test** stays fail-closed (an exact copy of a twin's span counts even
    when its shape is pool-common); the docstrings and `sandbox/attested.toml`'s header say
    so, a fixture shows it, and the alternative was measured (15 of 626 planted whole-region
    copies lost) and not taken, pending the user.
  - **`get_bench --validate`** retries a row whose assumption audit was killed by memory or
    stopped by the wall clock, as the lab gate does (CLAUDE.md §Resources).
  - **`pcount.py`** finds a declaration with attributes before its name and blanks block
    comments and literals before counting; no Q10–Q18 figure changed.
  - **`vcheck --ref --brittleness`**: a run name two sites share, or a module taken for the
    crate prefix, is reported as unattributed, never as a wrong site.
  - **The study root's leftovers** (D20's harnesses): calibrate resets its clone and empties
    the scratch before each case and in a `finally`; each case's DVL_SCRATCH is its own
    (`guard_doors.case_scratch`); `skill_sims` refuses a set-up while another study root is
    on the host, and another case's turn while a drop-in is in the clone.
  - **Learner-visible text:** Q13 §2 names the hidden check's outcome words and glosses
    `strong` and `weak` with the direction of `requires` (an added `requires` is `weak`, a
    dropped one `strong`); Q15 §5 says its rows carry those words and that Lab 2's oracles
    read a changed `requires` the other way (D22); Q17's table and the two Q15 headers name
    the outcome words; Q12 and Q18 say the lab gate applies the assumption audit (D24);
    lab2pub's STRATUM.toml and Q15 §6.2 say the installed upstream sets hold the public
    statements and that the redraw rule was amended once before any seal; `NOTICE` names
    the `pub open` change; rubric D12 points at the chapter's line.
- **Why:** the lane's runs on the authoring worktree (`authoring` @ db398e4 plus the round's
  working tree): `test_course_map` 396 passed; `chapter_lint` 18 chapters 0 problems;
  `pins.py --ci` Q12, Q13, Q15, Q17, Q18 0 problems; rubric pins current; the leak verifier
  OK over 1,631 public files; `tests/sandbox` 172, `tests/bench` 60, the wrappers' static
  suites 347, calibration 18, simulations 31 OK; `test_hooks.sh` 6,806 passed;
  `ci.sh --author --job static --job rubric` PASS. Archive `dv5e/reviewfix/`.
- **Touches:** Δ218 (D2, D6, D7, D9 kinds), Δ220, Δ221; the round's D20–D25 entries;
  `MODULES.toml` (schema comment); `scripts/check_course_map.py`, `test_course_map.py`,
  `pcount.py`, `vcheck`, `dvl/bench.py`, `dvl/sandbox.py`, `dvl/lab2pub.py`;
  `sandbox/attested.toml` (header); `tests/acceptance/guard_doors.py`,
  `tests/instructor/calibration/calibrate.py`, `tests/instructor/simulations/skill_sims.py`
  and their tests and READMEs; `tests/sandbox/test_sandbox.py`, `tests/bench/test_get_bench.py`,
  `tests/wrappers/test_pcount_static.py`, `test_forms_static.py`; `docs/Q12`, `Q13`, `Q15`,
  `Q17`, `Q18`; `expected/Q15.chapter.toml` (units); the two Q15 Lab 2 headers;
  `bench/local/q/lab2pub/STRATUM.toml`, `NOTICE`; `paper/rubrics/Q15_rubric.md`.
- **Owner:** this round's review fix lane; the open items' owners (notes §4).
- **Open:** the user: L2's run rule and T2's exact-test reading (each with options); the
  image owner: `truthcheck.py`'s docstring; the kits lane: vp2's kept comment at the next
  Q15 re-seal; the records lane: CLAUDE.md lines 5 and §Authoring item 2 (notes §5); the
  tools owner: a per-item seal tie and a counted band cross-check.
