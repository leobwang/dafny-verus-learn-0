# DV6 audit lane: the spec §12.1 "Per module" checklist over Q01–Q06 (author-side)

Lane `audit-q01q06`, 2026-10-14. Read-only except this file. Memory share 2 GB: no solver job ran; the
solver evidence is the author CI run `build/ci/20261014T004859Z-3125743/` (`ci.sh: PASS — 14 passed,
0 failed`, authoring @ db398e4 + 68 uncommitted = 83531a8's tree) and its reference logs under
`~/.cache/dafny-verus-learn-0/ci/20261014T004859Z-3125743/`. Static checks re-run by this lane are marked
**(re-run)**. Scratch `/tmp/dvl0-dv6-auditq0106/` (removed at the end); archive
`~/.cache/dafny-verus-learn-0/author-probes/dv6/audit-q01q06/` (the check scripts and their counts only).

Scope: Q01–Q06, layers L1–L3 (`dafny/given/Q/QG_L{1,2,3}_BigNat.dfy`, `verus/given/qg_bignat_l{1,2,3}`).
No lab ships in Q01–Q06 (Lab 1 is Q12's). Q01–Q06 learner files are unchanged since b93975a (DV3a kits):
`git diff --stat b93975a HEAD` over their chapters, exercise, exit, agent, check and specimen files, banks,
problems, rubrics, fixtures, leak patterns and L1–L3 is empty (only L4–L7 were added under `given/`).

Note: while this lane ran, another lane was editing the worktree for D26 (12 paths modified, among them
`.claude/skills/review-code/SKILL.md`, `README.md`, `CLAUDE.md`, `scripts/{firsttry.py,pins.py,vcheck,
course_mode.sh}`). The facts below are 83531a8's unless a line says otherwise.

## Lines that hold (with evidence) — for the release checklist

### Twin complete, hole-free, audit-clean, silent; outputs and audit rows pinned
- Reference gate and audit exit 0 for every Q01–Q06 twin (core/std units, checks, exits, agents; Verus
  crates, exit.rs, agent.rs): `verify-q-dafny.log`, `verify-q-verus.log`. Every reference gate line is the
  summary line only, `0 holes, 0 errors` (`verify-q-{dafny,verus}.ref.log`; e.g. `Solutions/dafny/Q/Q06_Machine/std
  … verified — 61 verified, 0 holes, 0 errors`); no warning line for any Q01–Q06 path.
- Python twin `Solutions/harness/q/fvh_q/q06_stats.py`: `[reference gate …] exit 0`, `[Python TRIV mode …]
  exit 0` (`harness.log` 145–148).
- `pins.py --ci`: 823 pins over 18 modules, 0 problems; `pins.py --ref` exit 0 (`pins.log`).
- Layers L1–L3: gate and audit exit 0 in both languages (`verify-q-*.log`: QG_L1 9, L2 22, L3 30 verified;
  qg_bignat_l1 3, l2 1, l3 11; 0 findings each); `vaudit --check-trust` 0 findings.

### Exercise file is the exact hollow
- `firsttry --lint-hollow --all`: Q01 OK (41 files), Q02 22, Q03 33, Q04 30, Q05 20, Q06 19 (`static.log`).
- `reference_lint.py` exit 0 (declaration lists, markers, slots; `static.log`, `static.ref.log`).
- `specfreeze --check Q01…Q06`: 0 findings each (`static.log`).
- `--empty-body`: Q01 exit 0 (1190 s), Q02 1292 s, Q03 464 s, Q04 1024 s, Q05 274 s, Q06 1055 s (`empty-body.log` 4–15).
- Hole counts, tool = shipped forms = chapter (`verify-q-*.log` "py holes" lines; chapter file tables):
  Q01 d 3 / v 3 (chapter 3, 3); Q02 6 / 6 (6, 6; "12 holes"); Q03 5 / 5 (5, 5); Q04 d 5 (3 + 2) / v 6 (2 + 4);
  Q05 5 / 4 (5, 4); Q06 5 / 5 plus 3 Python holes (`harness.log` 93; chapter 5, 5, 3). 0 mismatches.
- Dafny one-`ensures` rule: the lint `multi-ensures-hole` (scripts/dvl/dafny.py:667) is part of lint-hollow.

### Item markers, concept matrix, uses:, coverage
- `check_course_map.py` all groups OK (49 modules, 138 import files, 81 coverage rows; `static.log`); its D4
  group covers Q01–Q09 (every P/H/X/T cited), `uses` (≥ 2 per WRITE slug), parity and exit floors.
- `--items Q0n --json` **(re-run)** parses: Q01 49 items, Q02 47, Q03 45, Q04 41, Q05 37, Q06 39.

### Specimens, planted, exit and demo pins
- Every specimen is a `.specimen` file under `specimens/Q0n/` (outside every unit; `gen_units --check` OK);
  their shipped state is in `expected/Q0n.pins` / `.counts`, checked by `pins.py --ci` (0 problems).

### Chapter
- `chapter_lint --all`: Q01 13 strand sections, 11 predict boxes, 3 diagrams, 28 pinned fences; Q02 6/10/5/32;
  Q03 7/14/5/34; Q04 5/9/5/46; Q05 3/8/5/25; Q06 5/9/5/32; 0 problems (`static.log`). Each has
  "What the instruments can and cannot see", "Instructor touchpoints" and "What Q0n planted".
- Q01's three-doors refusal text (`docs/Q01_Hello.md` 700–703, pin `door-b-ref-build`) still equals the hook's
  rule 1b message (`.claude/hooks/spoiler-guard.sh` 2245) **(re-run, by string comparison)**.

### Agentic file
- Line 1 `/* CONTRACT` with exactly `goal:`, `allowed-files:`, `acceptance:` in all nine agentic files
  (Q01 ×2, Q02 ×2, Q04 ×2, Q05 ×2, Q06 Dafny); Q03 is hand-written contract v0 (no agentic file).
- Every `expected/…audit` file an acceptance line names exists; `research/q06_skeleton.dfy` is the learner's
  own copy (chapter `docs/Q06_Machine.md` 1031 says so).
- The "what the dashboard can and cannot see" passage is in each chapter's agentic section
  (`### What the dashboard can and cannot see`: Q01 684, Q02 838, Q03 978, Q04 1056, Q05 1072, Q06 1051),
  the course's convention through Q12.
- Twin reference proves satisfiability: every agent twin's reference gate and audit exit 0 (above).

### Written pair and rubric
- `make -C paper paper`: 36 documents, green (`paper.log`); `make paper-solutions` exit 0.
- `update_rubric_pins.sh --check` exit 0 (`rubric.log`); `PENDING` count 0 in every Q01–Q06 rubric
  **(re-run grep)**. Each has Verifier anchors, Code-review focus and Audit debrief (Q03: "Contract v0
  review", no contract run by design).
- Card pins **(re-run)**: the `sed -n 'a,bp' cheatsheets.md | sha256sum` hash of every Q01–Q06 card range
  appears in its problems file (Q01 642–668 `0cb3f94d…`, Q02 766–791 `04b270b5…`, Q03 944–967 `d323712a…`,
  Q04 614–638 `5a0ff58d…`, Q05 1366–1386 `a821f639…`, Q06 672–699 `00089348…`); each range starts at the
  card's heading (02.3, 02.7, 02.13, 02.2, 03.12, 02.4).

### Bank **(re-run, scripts archived)**
- Sizes and mix lines agree with the headers: Q01 8 (all `viva: no`, survey, tutor-only), Q02 9 (9 viva,
  3 backward edges), Q03 8 (8, 5), Q04 8 (8, 5), Q05 8 (8, 5), Q06 8 (8, 6). Two PPs each, headed "Hand these
  out verbatim", each with **Isolates:**, Done =, Author-verified and Diagnostic, and hole bodies.
- Tier draws: Q03's A, B, C and Q06's A, B, C, D each hold 5 questions on 5 strands, ≥ 1 per tier module,
  ≥ 2 predicts, ≥ 2 backward edges, all `viva: yes`, table strand/predict/edge = the question headers, pairwise
  disjoint; the "no further disjoint draw" statements match the unused sets (Q03: Q02.K1, Q03.K8; Q06: Q04.K4,
  Q05.K1, Q05.K3, Q05.K6).
- PP names vs the module's exercise, specimen and twin declarations: no clash (Q05 PP1's member predicate
  `Valid` is the dynamic-frames idiom inside its own class `Bins`); `avoid.sh` 0 hits, 0 stale waivers.
- Probes: verbatim `vcheck:` outputs, toolchain line dated 2026-10-05/06 on Dafny 4.11.0 / the Verus pin;
  the summary-line format is unchanged since (no change to the `verified — … holes, … errors[, stage …]`
  formatter in `git diff b93975a HEAD -- scripts/vcheck`). Not re-run (no solver share; see minor 4).

### Leak patterns **(re-run)**
- 8 entries each (Q01–Q06), within 3–8. The README verifier over Q01–Q06: `48 OK sol=1 prob=0 chap=0 pub=0`,
  `leak verifier: 6 module(s), 1632 public files scanned, OK` (the given-layer hits are the declared exemptions).
- Extra lane check: lines of ≥ 30 characters in the twins that the learner file lacks, searched verbatim over
  the chapters, banks, rubrics, problems, QPLAN, design docs, expected/, specimens and every learner file: no
  hit outside a later-tier file, a given layer or a statement line (the QPLAN hits are T1d/T1v statements and
  their checks, already printed in the exercise files; Q05.X1d's one sequence identity is taught in the module).

### Calibration fixtures (structure only)
- Flawed fixtures carry per-line `% EXPECTED[B][dim][score]` with score-4 clean lines (Q01: 3 flawed + 5 clean
  fields of B1, the single problem; Q02 4 lines; Q03 5; Q04 4; Q05 5; Q06 6). Gold fixtures are paraphrased:
  0 lines of ≥ 40 characters verbatim from `paper/solutions/Q0n_solutions.tex` (outside the problems file).

### Minutes; practice items; avoid.sh
- Chapter budgets sum to their totals and equal DESIGN-PROPOSAL §7.5 and QPLAN's itemized tables: Q01 227,
  Q02 234, Q03 251 (+30 viva), Q04 251, Q05 253, Q06 281 (+30 viva). `admissible = {}` for Q01–Q06 (concept
  tiers: no practice item carries minutes).
- `avoid.sh`: 0 hits, 0 waived, 0 stale waivers; N1 idle only because R has no declarations (`static.log`).

## Gaps (also in the lane's structured report)

1. **major — calibration never ran for Q01–Q06.** No `calibrate.py` run is archived for any of them (the only
   calibration traces are DV5e's set-up/clean-up tests, `dv5e/studyroot/calibrate.*`). Fix: `calibrate.py all`
   (72 sessions) on the frozen tree; the Q01–Q06 cases are 24 of them.
2. **major — the Q01–Q06 skill simulations are stale and not scheduled.** They ran on 2026-10-05 (Q01–Q03,
   DV2b-2, hook `230e7226…`, CC 2.1.289) and 2026-10-06 (Q04–Q06, DV3k, same hook). Since: the hook is
   `0a1c2b63…` (133 lines changed), `contract/SKILL.md` (allowlist rules, the `tools/` Done exception, the
   closed agent entry points), `viva/SKILL.md` (the Opening paragraph, which Q06's tier viva uses),
   `grade-paper/SKILL.md` (`--fixture`), `CORE.md`'s lists, `skill_sims.py` (+909 lines), and the D26 edit of
   `review-code/SKILL.md` line 27 now in the worktree; the CLI on the host is 2.1.299. DV5e's draft open list
   (`dv5e/integ-attempt1/d233.md` 16) schedules only Q13–Q15 and Q16–Q18 re-runs. Fix: re-run DV2b-2's cases
   a–h and DV3k's a–g after the freeze edits land (D26 included), then archive under `dv6/simulations`.
3. **minor — simulation coverage holes for Q01–Q06.** `/review` ran only on an empty ledger (DV2b-2 case g);
   `/grade-paper` only through calibration (gap 1); Q01's own sessions are `/contract` only (no `/tutor`,
   `/discuss` or `/review-code` on Q01). Fix: add a `/review` case with a seeded Q04–Q06 ledger (e.g. after
   case d's ledger lines) and a `/tutor Q01` or `/discuss Q01` case to the re-run.
4. **minor — bank probes not replayed since authoring.** No CI job re-runs a bank's verbatim probe outputs; the
   wrappers changed (`git diff --stat b93975a HEAD`: `scripts/vcheck` 962 lines, `dvl/dafny.py` 282, `dvl/verus.py` 263) since 2026-10-06. The
   viva's drift rule voids a drifting predict at run time, so nothing blocks the learner. Fix: one probe replay
   per Q01–Q06 bank (needs a solver share), recorded beside the banks' Toolchain lines.
5. **minor — records lag.** `tests/instructor/leak_patterns/README.md` 25–30 still show the 2026-10-05/06/11
   runs; `CLAUDE.md` line 5 still says Q01–Q06 "passed the simulated study sessions" without "to be re-run".
   Fix (integration lane): date the table rows with this lane's run (2026-10-14, 8 OK each, 1,632 public files)
   and add the re-run to CLAUDE.md's line.

## Runs this lane needs (not run: 2 GB share)
- `calibrate.py all` (or `--modules Q01,…,Q06`), the skill simulations' Q01–Q06 cases, a probe replay of the
  six banks, `guard_doors.py all` (Q01's door-a text is CC 2.1.289's; re-check it against the re-run).
- The study-mode `scripts/ci.sh` on the current tree (the last full study run is
  `build/ci/20261013T102615Z-1957673/`, at e43077c + 98).

## DELTAS-ready text (for the integration lane)
- **DV6 audit, Q01–Q06 per-module checklist.** Every §12.1 per-module line holds for Q01–Q06 on 83531a8's tree
  by the author CI run `20261014T004859Z-3125743` and this lane's static re-runs (leak verifier 48/48 OK over
  1,632 public files; bank mix, draws and PPs; card pins; minutes), except calibration (never run for Q01–Q06)
  and the skill simulations (2026-10-05/06, stale after the guard, skill and CLI changes since; not on DV5e's
  re-run list). Both are freeze-bar runs; the Q01–Q06 cases join `calibrate.py all` and the simulation re-run.
