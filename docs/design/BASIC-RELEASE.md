# The `basic` release: the Q core's freeze bar

*Latest follow-up: 2026-10-17, §14: the review fixes of the released `basic` (Δ275) and the user's decisions D46–D49; the deferred live checks run now in a separate lane (D47). §11 records the D45 deferral.*

*Status: **written by DV6's integration lane, 2026-10-14**, from the DV6 audit notes (`Solutions/plans/DV6-audit-*.md`), the clean-clone dry run, the fix round's notes (`Solutions/plans/DV6-fix-notes.md`) and the integration lane's own CI runs (DELTAS Δ238, Δ239, Δ241). The Simulate phase adds its lines after these (§5). A line is **HOLDS** with its evidence, **OPEN** with its owner, or **PARTLY** with both halves.*

> **Predictions first.** This file is in `docs/design/`, which is on the README's *Predictions first* list. It records which checks passed and where their logs are; it names no answer, no reference statement, no prediction answer and no key material, and it quotes no tool output a prediction asks about.

## 0. What ships, and when

- **The release plan** (the user, 2026-10-13; DELTAS Δ234): review the Q core to the freeze bar below; then freeze it and ship it as the git branch `basic` (a feature freeze: fixes only); then build the R core and add it to `basic`; then build the challenges on the branch `challenge`, branched from `basic`, where every fix lands on `basic` first and is merged forward at once.
- **The Q core:** Q01–Q18 (status `shipped` on the released branch `basic`), the spine layers L1–L7, the three labs (Lab 1 in Q12, Lab 2 in Q15, Lab 3 in Q18) and the capstone, with the instructor layer, the guard, the tools and the harness they use.
- **The branch step** is conditionally approved by the user (D42): after the freeze checks pass, create a single squashed content commit atop design-only `main`, validate its ancestry, flip the modules' status, and recreate authoring from the released `basic` baseline. Nothing in this file flips a status. A probe in a scratch copy showed the checker accepts Q01–Q18 as `shipped` (DV6's infrastructure audit).
- **The current follow-up tree:** `authoring` at `5d9be4e` plus Δ246. The original DV6 review used `83531a8` plus the round's changes. Each CI line names its run; earlier passes remain historical evidence.

## 1. The freeze bar (the user's list)

**Current exception (D45, Δ247):** the user said “record the blocker and skip. continue to build.” Claude-dependent live checks below are deferred for this build and do not block local development or the initial Basic release. They remain unvalidated work, not passing results. All local CI, toolchain, leak and release-history checks still apply.

| # | line | state | evidence, or owner |
|---|---|---|---|
| F1 | CI green, author mode (`scripts/ci.sh --author`) | **HOLDS** | Release: full run `build/ci/20261017T003253Z-2536741/`: 14 passed, 0 failed, skipped or absent, in 15,977 s, on the pre-release authoring tree, started clean at `5d9be4e`; the changes through `40a9b5a` are paper, bank, status and test-fixture material, with no formal source, wrapper or native proof payload change, covered by focused author text CI (3/3) and the full study and candidate static runs of F2. The released tree itself had no full author run. Review fixes: the fixed tip `148fa73` passed the full author run `build/ci/20261018T075251Z-2095832/`: 14 passed, 0 failed, 0 skipped, 0 absent, in 17,138 s (§14). |
| F2 | CI green, study mode (`scripts/ci.sh`) | **HOLDS** | Release: full run `build/ci/20261017T045910Z-584851/` on the final Q authoring tree, clean at `40a9b5a`: 12 passed, 0 failed, 2 expected author-only skips, 0 absent, in 4,271 s. Its native and tool payload equals the release candidate's; the release status, README and CLAUDE text differ. The released tree itself had a static run only: candidate static `20261017T032721Z-61186` passed in 417 s after the shipped-fixture fixes. Review fixes: the fixed tip `148fa73` passed the full study run `build/ci/20261018T123901Z-2823479/`: 12 passed, 0 failed, 2 author-only skips (empty-body, rubric), 0 absent, in 4,701 s (§14). |
| F3 | The skill simulations pass (every skill of Q01–Q18, zero leak-pattern hits, legal help delivered) | **PARTLY (live, 2026-10-20)** | The Simulate phase. Every module's set is stale or never ran: Q01–Q12's ran on an earlier hook, skills and CLI (2026-10-05 to 10-07), Q13–Q15's in DV5b, Q16–Q18's never (Δ238). The tools are ready: the window rule, the code-mark token rule, the delivery exemption and the plant check (Δ239). Budget: D43. **DV6 Simulate phase (2026-10-15): deferred** by the window rule after set 1's first turn (§5 S1). D45 defers this live requirement for the current build; see §11. **DV7 live check (2026-10-17):** Set 1 (Q16–Q18) ran live on the release `39ba47b` with Claude Code 2.1.302: cases a–f PASS, h 0/0 over 27 turns (24 patterns per case; controls 144/3,475). Case g was blocked by a fixture marker (§5 S1). Set 2 (Q13–Q15) and the Q01–Q12 re-runs and supplements were not started; the lane stopped at an auto-mode classifier refusal (§5 S2). Archive `author-probes/dv7-live/simulations/q16-q18/`. D45's waiver still covers the remainder. Since then Δ275 fixed the fixture marker (F-3), the detached-HEAD set-up (F-1) and the tutor's rung edge (F-5) on basic; not re-run live. **DV7 live re-run (2026-10-20, `7800b83`, Claude Code 2.1.305; Δ501):** Set 2 (Q13–Q15) ran in full: cases a–f PASS, g 0/0 over 27 turns (48 patterns per case; controls 144 and 3,475). Set 1 case g FAILS. The grader caught all three planted flaws with the expected grades and no unlock, but wrote 6 ledger lines for 7 findings (`check grade` 14/15), and its probe file reproduces a reference capstone helper (2 stream and 2 file token hits). Q01–Q12's re-runs and the freeze supplements were not run. Archive `author-probes/dv7-live2/retry/simulations/`. Since then Δ502 fixed the grader's probe rule and ledger count and the scan's Rule 2 exemption on basic; case g not re-run live. |
| F4 | `tests/instructor/calibration/calibrate.py all` passes (78 sessions over Q01–Q18) | **FAIL (partial run)** | The Simulate phase; never run (the calibration README's *Last run*). D44 adds six `/review-code` cases on Q13/Q15; their clone preparation and strict first-try/unit checks passed, but no model session has run. Budget: D43. **DV6 Simulate phase:** `setup` only, 36 of 36 drop-ins compile; no session (§5 S3). D45 defers this live requirement for the current build; see §11. **DV7 live check (2026-10-17):** Not run. `calibrate.py`'s setup precheck refuses because six lab fixtures (`tests/instructor/fixtures/Q12_flawed_answers.tex:91`, `Q12_gold:95`, `Q15_flawed:123`, `Q15_gold:130`, `Q18_flawed:170`, `Q18_gold:169`) carry Δ246's sentence with the drop-in marker word `fixture`. Reword it, add a drop-in marker test, then run the 78 sessions (§5 S3). D45 waiver unchanged. Since then Δ275 fixed the fixture marker with a 36-drop-in test (F-3) and the detached-HEAD set-up (F-1) on basic; not re-run live. **DV7 live re-run (2026-10-20 to 21; Δ501):** `setup` compiled all 36 drop-ins (F-3 holds). 31 of 78 sessions ran (Q01–Q08 except Q08-tutor) before the window rule deferred at the five-hour window's 0.8 (2026-10-21 00:35). 18 PASS and 13 FAIL: the grader declines a wholly blank file (5 of 8 empty cases); the ledger is short by one line per merged finding (Q04, Q05, Q07); probe code reproduces reference or model-answer lines (Q04, Q05, Q07); one location-matcher miss (Q06). The 47 remaining cases, D44's six reviewer cases among them, were not run. Archive `author-probes/dv7-live2/retry/calibration/`. Since then Δ502 fixed all four on basic (the skill's unanswered-problem, ledger and probe rules; the harness's probe checks, Rule 2 exemption, host-path tokens and Q06's anchors); not re-run live: all 78 sessions are owed. |
| F5 | `tests/acceptance/guard_doors.py all` passes | **HOLDS (live, 2026-10-20)** | The Simulate phase; last run 2026-10-04 on an earlier hook. The Monitor door is built (Δ239). **Tool-coverage prerequisite resolved:** Δ242 covers Firecrawl’s local-file parser, Workflow and ScheduleWakeup in the matcher and hook, with regression tests (§7). A fresh model acceptance run is still required. **DV6 Simulate phase:** `setup` and `dryrun` only, 16 hook runs, 0 unexpected; no session (§5 S4). D45 defers this live requirement for the current build; see §11. **DV7 live check (2026-10-17):** `guard_doors.py all` on `39ba47b`, CLI 2.1.302, hook `7a6b3d91ef02c691…`: dry run 16/0 unexpected; 11 sessions, all 11 rows PASS (doors refused by the deny rules and hook rules 1, 1b, 1e-via-deny, 1f, 2s, Monitor by rule 1; both controls succeed), 0 leak and 0 canary hits over 17,670 tokens. Overall FAIL only on `uncovered_tools`: `ReadMcpResourceDirTool` (new in 2.1.302) is in neither the matcher nor `LEFT_ALONE`, the author's to decide, then re-run (§5 S4). Archive `author-probes/dv7-live/acceptance/`. Since then Δ275 fixed the tool coverage (F-2: `ReadMcpResourceDirTool` left alone), the detached-HEAD set-up (F-1) and the stray-file cleanup (F-4) on basic; not re-run live. **DV7 live re-run (2026-10-20, `7800b83`, CLI 2.1.305, hook `7a6b3d91ef02c691…`; Δ501):** `guard_doors.py all`: **overall PASS**. Dry run 16 hook runs, 0 unexpected; 11 of 11 rows PASS (a and e by the deny rules; b and b2 by rule 1b; c and h by rule 1; d by rule 2s; f and g by rule 1f; both controls succeed). 0 leak and 0 canary hits over 17,671 tokens (control 26). No uncovered tool among 2.1.305's 63. Archive `author-probes/dv7-live2/retry/acceptance/`. |
| F6 | A clean-clone dry run passes | **PARTLY** | HOLDS for every chapter command: a fresh clone in study mode ran every concrete command of the 18 chapters verbatim in three states, with 355 pinned fences matching and 0 problems, and no manual intervention beyond the learner's own steps (Δ238; `author-probes/dv6/dryrun/part1/`). Its findings are fixed (Δ239) including the host's rustup now restored under D41. **OPEN:** the capstone under the final contract and the three gold `/contract` transcripts (Q01, Q09, Q18), deferred by the window rule after 1 of 30 calls (the Simulate phase; Δ240 item 8; the prepared learner state is in `dv6/dryrun/specs/`). **DV7 live check (2026-10-17):** The model part (the capstone under the final contract and the Q01, Q09 and Q18 gold `/contract` transcripts) was not run on 2026-10-17. The window allowed it, but the lane stopped at an auto-mode classifier refusal before step 5 (§5 S5). **DV7 live re-run (2026-10-20 to 21; Δ501):** the capstone under the final contract and the Q01, Q09 and Q18 gold `/contract` transcripts were not run: the window rule deferred during calibration (five-hour 0.8, 2026-10-21 00:35). |
| F7 | A final leak audit is clean | **HOLDS — LOCAL; transcript portion deferred** | Frozen candidate source scan and D42 history check pass at the release step (§13). One squash atop main excludes old authoring ancestry. D45 defers scans of live transcripts that have not been created; no scan result is inferred for them. |
| F8 | No open DECISION NEEDED | **HOLDS** | The user approved all nine recommendations through interactive MCQs (D36–D44, Δ243); they are implemented (§8). D45 deferred the live checks (§11); D46–D49 settle the review round (Δ275, §14). The readings Δ275 took in building its fixes are listed there for the user to confirm; none blocks study. |

## 2. Spec §12.1, Infrastructure (Phase 0)

| line | state | evidence, or owner |
|---|---|---|
| The toolchain is pinned, `VERSIONS.md` rows dated; CI asserts the versions and the binary sha256 | **HOLDS** | `VERSIONS.md` §1.1–§1.2 (Dafny 4.11.0 with its zip, tree and binary sha256 and bundled Z3; Verus 0.2026.09.27.3cf1832, Rust 1.98.1, Z3 4.16.0, `vstd =0.0.0-2026-09-20-0158` in all 25 `Cargo.toml`); `get_toolchain.sh --check` in `verify-q-{dafny,verus}.log` of each CI run below. D41 restored the archived rustup 1.28.2 after checking its sha256 against the lock; `sandbox/build-images.sh --check` passes for both images (2026-10-16). |
| A clean clone builds the default target green in minutes; `make -C paper paper` compiles and fails on an empty set | **HOLDS** | The dry run's clone: setup, `vcheck --selftest` PASS, `make -C paper paper` 36 documents (Δ238); `paper/Makefile` refuses an empty set or an unpaired file. |
| The default target is learner exercises only; the reference is built by name only; the checker enforces it | **HOLDS** | `static.log`: `gen_units` 37 units match the registry; the checker's `files` group; reference builds only through `vcheck --ref` in the author steps. |
| `MODULES.toml` + `check_course_map.py` (all groups) + regression tests run first in CI; no reference path in the registry | **HOLDS** | `static` is CI's first job: "course map OK: 49 modules (33 Q, 16 R; 0 shipped, 18 authoring, 31 planned)" and `test_course_map` 396 passed (this lane's step 1). |
| Every skill's Step 0 resolves through the registry | **HOLDS** | Each of the seven `SKILL.md` files has one `check_course_map.py --resolve` Step 0 (DV6's infrastructure audit). |
| `vcheck`, `vaudit`, `specfreeze`, `pins.py`, `firsttry.sh` exist and print locations, not content | **HOLDS** | `scripts/`; `tests/wrappers/test_tools_{static,tool}.py`, `test_dafny_common.py` in the `wrappers` job. |
| The guard's four layers | **HOLDS** | The 4 canonical and 4 always-on deny rules (`.claude/settings.json`; `course_mode.sh status`); the hook's rules, now over the Monitor tool too (Δ239); CORE.md's MAY / MAY NOT; leak patterns with the verifier (F7). |
| `test_hooks.sh` replays must-block and must-allow fixtures with rule attribution and every §7.2 side channel, in the study, jq-free, stand-down and still-armed passes (`hook-test`) | **HOLDS** | `test_hooks.sh` 6,925 passed, 0 failed (this lane's step 1) and the `hook-test` job of F1 and F2; the `include_bytes!` fixture added (Δ239). |
| `course_mode.sh` refuses authoring outside a linked, non-learner worktree and moves both layers; CI fails on a shipped mode file or a missing canonical rule | **HOLDS** | `static.log`: "study mode shipped: yes (… 4 canonical and 4 always-on rules)"; the hook test's `course_mode.sh` section; the recipe from `basic` (Δ235). |
| A fresh study session is demonstrably denied a reference read, a reference build, an include or import of the reference, and a heredoc into a solo tree; refusal texts captured for module 1 | **HOLDS for the doors; the report gate is open** | DV7 live run (F5): every door refused in a fresh study session, refusal texts verbatim in `dv7-live/acceptance/verdict.md`; the report fails only on the new `ReadMcpResourceDirTool`. Since then Δ275 left `ReadMcpResourceDirTool` alone (F-2); the report has not been re-run. Before it (DV6): `guard_doors.py all` (F5). The Q01 chapter's quoted rule-1b text still equals the hook's message (DV6's audits, by string comparison). |
| The SessionStart banner reports due reviews, a stale allowlist and authoring mode | **HOLDS** | `.claude/hooks/review-due.sh`; the hook test's `review-due.sh (SessionStart)` section. |

## 3. Spec §12.1, Per module (Q01–Q18)

Evidence: the three per-module audits (`Solutions/plans/DV6-audit-{q01q06,q07q12,q13q18}.md`, at `83531a8` with CI run `20261014T004859Z-3125743`), re-checked on the final tree by this lane's CI runs (F1, F2) and step 1 (Δ241).

| line | state | evidence, or owner |
|---|---|---|
| The twin is complete, tool-counted hole-free, audit-clean and silent; every quoted output and audit row pinned | **HOLDS** | `verify-q-{dafny,verus}.log` and their reference logs: every reference gate and audit of Q01–Q18 and L1–L7 exits 0 with the summary line only; `pins --ci` 823 pins over 18 modules, 0 problems (the `pins` job and this lane's step 1). |
| The exercise file is the exact hollow; declaration lists equal; hole count = chapter = CI; every slot unfilled; `--lint-hollow` and `--empty-body` pass; one `ensures` per Dafny hole | **HOLDS** | `static.log` (`--lint-hollow --all`, `reference_lint`, `specfreeze --check` 0 for every module); `empty-body.log` every module exit 0 (the author run); the audits' hole and slot tables (chapter = tool = CI for all 18). |
| Item markers parse; the concept matrix cites every P/H/X/T item (depth track); each WRITE construct has ≥ 2 `uses:`; coverage rows resolve | **HOLDS** | `check_course_map.py` all groups OK (138 import files, 81 coverage rows, the 119 pending on planned modules); D4 covers Q01–Q09, `{}` from Q10 by rule. |
| Specimens, planted, exit and demo files outside every root, their shipped state pinned | **HOLDS** | `gen_units --check`; each module's shipped-state pins checked by `pins.py --ci`. |
| The chapter follows the skeleton, quotes only captured output, shows predict answers after the box, has 3–5 diagrams and the planted/harvested table | **HOLDS** | `chapter_lint --all` 18 chapters, 0 problems (step 1 and the `static` job); the continuity pass's harvest-cell fixes (Δ239). The Q15, Q17 and Q18 dashboard gap is closed with four live pinned fences (Δ245). |
| The agentic file has the three-key CONTRACT on line 1, one of the four shapes, a dashboard passage, and a twin reference proving it satisfiable | **HOLDS** | All 22 agentic files open with the CONTRACT block; the agent twins pass the reference gate and audit; the toolwright's and toolsmith's twins built and checked (Δ239: `Solutions/tools/Q12/test_holecount.py` in the author harness job; the toolsmith 24/24). |
| The written pair compiles; the rubric has sha pins filled (no `PENDING`), verifier anchors, code-review focus and an audit debrief | **HOLDS** | `paper.log` 36 documents; `update_rubric_pins.sh --check` 112 pins over 18 rubrics current (step 1); Q12's rubric reviews `policies.py` (C7, Δ239). |
| The bank meets size, mix, viva-able count, backward edges, verified probes, disjoint draws and parallel problems | **HOLDS** | Size, mix, edges, draws and names: the audits' bank scripts. Fresh replay across all 18 banks: 362 formal command cases, 14 Python examples and 24 audit/freeze examples, all expected results matched (Δ246). This checks verdict/count and numerical/audit/freeze summaries, not byte-for-byte diagnostic recapture; the viva drift rule still applies. |
| Leak patterns: 3–8 entries, Rule 1 and Rule 2 verified, cut only from H/X/T/A answers | **HOLDS** | 8 per module; the verifier 18 modules over 1,635 public files, OK, re-run after this file was written; the leak README's table re-dated (Δ239). |
| Calibration fixtures pass a headless grader run | **OPEN** | F4. The fixtures' structure holds (per-line `EXPECTED`, a clean control, paraphrased gold). |
| A study-clone simulation of every skill gives zero leak-pattern hits, with legal help delivered | **OPEN** | F3. |
| Minutes reconcile to the module total; practice items admissible or minute-less | **HOLDS** | The audits' sums against design §7.5 and QPLAN; D40 admits Q15.H2d/H2v at 8/7 minutes under the short-format band exception (7/13 proof lines). `check_course_map.py` passes. |
| (Two tracks) `avoid.sh` clean, no stale waivers | **HOLDS** | `avoid.sh`: 1,961 Q declarations, 0 hits, 0 waived, 0 stale waivers (step 1); the idle name waiver N1 waits for R declarations |

## 4. Spec §12.1, Course level

| line | state | evidence, or owner |
|---|---|---|
| The role ladder runs end to end; each agentic exercise has artifact-based acceptance and one recorded known-good transcript | **PARTLY** | HOLDS: artifact-based acceptance on all 22 agentic files; the ladder's rungs in the registry. **OPEN:** known-good transcripts exist for Q07.A2d only (the Qwen replay); the 3 gold `/contract` transcripts (F6) and the other 21 files' transcripts (the Simulate phase; Δ240 item 8, option (c) would move the 21 after the freeze). |
| Contract v0/v1/v2 slots in `CLAUDE.md` below the learner marker, fallback rules above | **HOLDS** | `CLAUDE.md`'s §Contractor contract (DV6's infrastructure audit). |
| Continuity pass: every whisper or threshold-concept step pays off | **HOLDS** | DV6's continuity pass (`Solutions/plans/DV6-audit-continuity.md`): 0 blockers; its 4 majors and 7 minors fixed (Δ239); every whisper and TC step pays off; the TC1–TC14 table in QPLAN §29. The harvests that name challenge modules say "(the challenge branch)". |
| Clean-clone dry run: every chapter command runs verbatim | **PARTLY** | F6. |
| Brittleness: the reference re-verifies under N seeds within the pinned resource limit (the CV gate) | **HOLDS** | The first course-wide run: `scripts/ci.sh --author --brittleness --job brittleness` PASS in 1,204 s (`build/ci/20261015T004823Z-2466350/`, Δ239), on the tree before this lane's edits, which changed no reference. |
| CI never calls a model, never runs on the learner branch, never prints reference content | **HOLDS** | `ci.sh` excludes the model harnesses and runs the harness job in a sterile environment with tripwire shims; `--author` refuses on `leobwang-*`; every author step's output goes to `~/.cache/dafny-verus-learn-0/ci/`; `check_single_route.py` 34 of 34 allowlisted (step 1). |

## 5. Lines the Simulate phase adds

*Written by DV6's Simulate lane, 2026-10-15. The lane ran its four steps in order and started a model session only through the harnesses' pinned headless path, whose window rule it did not override (no `--window-ack`). Archives are under `~/.cache/dafny-verus-learn-0/author-probes/dv6/{simulations,calibration,acceptance}/`. Every scratch and study root was removed.*

| # | line | state | evidence, or owner |
|---|---|---|---|
| S0 | **The window-rule record** | **OPEN** (deferred) | Set 1's first turn (case a's intake) returned `rate_limit_event` status `allowed_warning`, with the five-hour window at 0.17 and the seven-day window at **0.84**. The study reserve is `allowed` only and a seven-day window below 0.6 (`sandbox/apparatus.toml` `[window]`). `skill_sims.py` recorded `defer` and stopped. The window belongs to the account, so the lane started no further session in any tool. It used 1 model call, notional 0.41 USD. Resuming waits for the window to fall back under the reserve, or for the user's call on Δ240 item 8. |
| S1 | Skill simulations, set 1 (Q16–Q18, cases a–h) | **OPEN** | a: intake only. The session resolved Q16 and ran `vcheck --module Q16` (3 calls, 0 refused). It asked for the attempt and the exact error, gave no hint and stopped, as the intake requires. b–g: not run. h: the one turn scans 0 pattern and 0 token hits (24 patterns, Q16 tier filter; controls 144 and 3,475). Checked without a model: the learner state's 5 anchors each occur once on the current tree; the plant passes `plant_overlaps`; with the plant, `vcheck` reports both of H1d's postcondition conjuncts failing and the H3d hole; `test_skill_sims.py` 37 OK. Archive `dv6/simulations/q16-q18/`. |
| S2 | Skill simulations, set 2 (the Q13–Q15 re-run of DV5b's cases a–g) | **OPEN** | Not started (S0). The learner state's 13 anchors each occur once on the current tree. |
| S3 | `calibrate.py all` (F4) | **OPEN** | `run` not started (S0). `setup`: the clone, the hook probes and the precheck all as expected, and 36 of 36 drop-ins compile (flawed and gold for Q01–Q18); `test_calibrate.py` 18 OK. D32's Q13/Q15 `/review-code` calibration has no harness case (Δ240 item 9). Archive `dv6/calibration/`. |
| S4 | `guard_doors.py all` (F5) and spec §12.1's "a fresh study session is denied …" | **OPEN** | `run` not started (S0). `dryrun`: 16 hook runs on the current hook (`04a18567288da90c…`), 0 unexpected, every door refused by its expected rule (1, 1b, 1e, 1f, 2s; door h's Monitor `command` by rule 1) and both controls pass. This is the hook layer only; the session rows need `run`. **Before `report` can pass:** Claude Code 2.1.299's session tool list has three tools in neither the matcher nor `LEFT_ALONE`: `mcp__firecrawl__firecrawl_parse`, `Workflow` and `ScheduleWakeup` (the author or the orchestrator). Archive `dv6/acceptance/`. |
| S5 | The capstone under the final contract and the three gold `/contract` transcripts (F6) | **OPEN** | Not in this lane's steps; still deferred by the same window (S0). |


**DV7 live check (2026-10-17, the release `39ba47b`, Claude Code 2.1.302; Δ276).** The live-check lane's rows, beside the DV6 rows above. Its findings F-1 to F-5 are fixed on basic (Δ275); nothing was re-run live after those fixes.

| # | line | state | evidence, or owner |
|---|---|---|---|
| S0 | **The window-rule record** | **HOLDS** | 38 model calls, every one judged `ok`: status `allowed`, no overage, five-hour window 0.17 → 0.33, seven-day 0.04 → 0.08 (`state.json` `window_log` in both archives). No `--window-ack`, no reserve release. |
| S1 | Skill simulations, set 1 (Q16–Q18, cases a–h) | **PARTLY** | a–f PASS (a: rungs 1–5 one per turn, PP1 verbatim 18/18 with its notes withheld, H1d 0/3, twin 0/74, stmt 0; b: policy answer, 0/56; c: four classifications and their moves, record, 1 ledger line; d: opening, draw A as tabled, REVIEW 0/3/2, 5 ledger lines, 1 gradebook row, then draw B opening with Q16.K2; e: gate-3 refusal with the motto; f: stopped on empty statements and placeholder snapshots, no allowlist). g blocked: `dropin Q18 flawed` refused on the marker word in `tests/instructor/fixtures/Q18_flawed_answers.tex:170`. h: 27/27 turns 0/0. Archive `dv7-live/simulations/q16-q18/`. |
| S2 | Skill simulations, set 2 (the Q13–Q15 re-run of DV5b's cases a–g) | **OPEN** | Not started: the auto-mode classifier refused the lane's `setup`. Anchors 13/13 still occur once. |
| S3 | `calibrate.py all` (F4) | **BLOCKED** | The setup precheck would refuse on the six lab fixtures' `fixture` word (F4). No session. |
| S4 | `guard_doors.py all` (F5) and spec §12.1's "a fresh study session is denied …" | **PARTLY** | 11/11 rows PASS, 0 leak, 0 canary; overall FAIL on `ReadMcpResourceDirTool` (`guard_doors.py:202–210`). |
| S5 | The capstone under the final contract and the three gold `/contract` transcripts (F6) | **OPEN** | Not run (lane stopped at the classifier refusal). |

**DV7 live re-run (2026-10-18 to 2026-10-21, `7800b83`, Claude Code 2.1.303 then 2.1.305; Δ501).** The live-check lane's rows for its first attempt (2026-10-18) and its retry (2026-10-20 to 21), beside the rows above. Its findings D-1 to D-5 and O-3 are fixed on basic (Δ502); nothing was re-run live after those fixes.

| # | line | state | evidence, or owner |
|---|---|---|---|
| S0 | **The window-rule record** | **OPEN (deferred twice)** | Attempt 1: 1 model call, status `allowed_warning`, five-hour 0.05, seven-day 0.66: `defer` after guard door a. Retry: every call `allowed` until calibration's Q08-empty met the five-hour window at 0.8 (2026-10-21 00:35:33): `defer`. No `--window-ack`, no override, overage `rejected`. 72 model calls in all, 62.60 USD at list price plus one call whose stream a host reboot lost (`dv7-live2/{acceptance,retry/*}/state.json`). |
| S1 | Set 1 case g | **FAIL** | `check grade` 14/15: 6 ledger lines for 7 findings; 2 stream and 2 file token hits from the grader's probe (Δ501 D-1, D-2). Fixed on basic by Δ502; not re-run. |
| S2 | Set 2 (Q13–Q15) | **HOLDS** | Cases a–f PASS; g 27/27 turns 0/0. Archive `dv7-live2/retry/simulations/q13-q15/`. |
| S3 | `calibrate.py all` (F4) | **FAIL (partial run)** | 31 of 78 sessions: 18 PASS, 13 FAIL (blank files declined, short ledgers, probe-code token hits, one exempt-layer false positive, one matcher miss); 47 not run. Fixed on basic by Δ502; all 78 owed. |
| S4 | `guard_doors.py all` (F5) | **HOLDS** | Retry: overall PASS, 11/11 rows, 0 leak, 0 canary; 63 tools, none uncovered. Attempt 1's door a also PASS (108 tools, none uncovered). |
| S5 | The capstone and the three gold `/contract` transcripts (F6) | **OPEN** | Not run (S0). |

## 6. Other items before the branch step

- **The host's rustup:** resolved under D41 (Δ244); checksum-verified archive restored and both image checks pass.
- **Deferred minors:** resolved by Δ245–Δ246: header/record notes and affected pins, dashboard passages, Batch plan consistency, and all bank checks. Live acceptance remains required independently.
- **The orchestrator:** commit the round; at the branch step, re-run both CI modes on the tree to freeze if anything changed after F1–F2.

## 7. DV6 follow-up: guard tool coverage (2026-10-16)

Work continues in the existing linked `authoring` worktree at `3dab787`; `main` still holds the design only. No module status or release branch changed. DELTAS Δ242 records this increment.

- **Closed:** F5's tool-coverage prerequisite from Δ241 and S4. Firecrawl's local `filePath` now receives the ordinary file-read checks, including cwd-relative paths and symlinks. Workflow and ScheduleWakeup are refused in study mode under rule 1f, enforcing the existing ban on workflows and background jobs. Authoring mode still stands down.
- **Regression coverage:** 18 new fixture templates expand to 36 cases (26 must-block, 10 must-allow), across both tracks and all three languages where relevant. Three tool-free tests cover acceptance-tool inventory, rejection of an unknown tool, and a relative symlink with an innocuous same-named file at the project root; the latter runs with and without jq.
- **Test-harness correction:** the last replay fixture can leave an active contract in the fake checkout. The author-option probes now clear that allowlist before starting. The first run exposed 50 wrong-rule/false-refusal failures from this leftover state; the rerun passes with the contract-active fixture still last.
- **Validation:** `build/ci/20261016T161107Z-2682424/static.log` passed (396 registry tests, generators, hollow/specfreeze checks, all 18 chapters, isolation); that quick CI invocation failed its hook job before the fixture-state correction. The corrected job, `scripts/ci.sh --job hook-test`, passed in 196 s at `build/ci/20261016T162127Z-3498227/`, with **7,101 checks passed, 0 failed**. `python3 -B -m unittest discover -s tests/wrappers -p test_guard_tools_static.py` passed **3 tests**. No model or solver was called for this increment.
- **Still open:** F3–F6's live sessions and transcripts; validation of D36–D44; the remaining dry-run and leak-audit work. The earlier full author/study CI passes are historical evidence, not full runs over this changed guard: F1/F2 need re-running before the freeze. No study reserve was released and no window override was used.

## 8. Approved decisions and implementation (2026-10-16)

D36–D44 (DELTAS Δ243) settle all nine decisions of Δ240. The model reserve remains protected, and the approved basic squash is conditional on the freeze checks passing.

| decision | implementation and evidence | remaining work |
|---|---|---|
| D36 | Opt-in `feedback = "spec"` reaches policy Verify observations and recorded replay. Annotation-only mutants are excluded; only proved precondition-only baselines enter the denominator. Unknown full checks never count as kills. Independent live container smoke: 3 eligible, 3 killed; vacuity and implementation outcomes recorded. | Reference calibration is complete under the original capped author verifier route: 24 eligible code mutants, 16 kills; two cards have undefined rates. Full adapter/container/policy/replay smoke also passes with completed oracles (Δ245). Actual learner lab runs still require their completed oracles and pre-registration. |
| D37 | Rebuilt ten public forms; one changed. C1/C4/C6/C7 passed for that form, including the hidden judge. Resealed 72 files; 51 protected files unchanged. Re-attested 88 current cards; retained one historical hash. | Final frozen-tree checks. |
| D38 | `lab_code` defaults to `preserve`; explicit `own` is recorded and honored by policy/agent verification and report re-verification. Fake batch/replay tests and live preserve/own checks passed. | Actual lab runs after pre-registration. |
| D39 | Lab 1 excludes Lab 2 HumanEval ids across languages; eligible Verus pool 74. Draw tests pass; chapter, written worksheet and stratum updated. | Actual lab draws after pre-registration. |
| D40 | Registry and checker admit Q15.H2d/H2v under the short-format band exception, 8/7 minutes. Course map passes. | None specific to this admission. |
| D41 | Restored checksum-verified rustup 1.28.2; self-update disabled; both image lock checks pass. | None specific to this restoration. |
| D42 | Shipping procedure records one squash atop main. Read-only release-history checker rejects authoring ancestry and accepts the intended squash in a synthetic-repository test. | Freeze checks, then branch creation and ancestry verification. |
| D43 | One pinned, logged sentinel on 2026-10-16 returned `rejected`, five-hour utilization 0 and seven-day utilization 1.0; canonical window verdict `defer`. No further model call; no reserve release or override. Reported reset: 2026-10-19 12:00 UTC (07:00 America/Chicago). | After the account window permits: guard acceptance, simulations, calibration, then transcripts. |
| D44 | Six isolated `/review-code` cases built (weak, undecided, later-run for Q13/Q15); only supplied answers exempted from their scan. 19 calibration tests pass; real clone preparation passes strict first-try and unit verification for both modules. | Six model sessions and reports, subject to D43. |

Evidence from this follow-up is archived under `author-probes/dv6-decisions/`; solver work used one verification container at a time under a 16 GiB scope. Full author/study CI remains required before freezing. Tests are run in their separate CI suites because the core suite's network tripwire deliberately conflicts with sandbox tests' fake local sockets when collected together.

The current quota check used one sentinel, not a study or grading session. Its stream was evaluated by the existing `guard_doors.window_verdict`; live F3–F6 validation remains deferred. A reset timestamp alone is not authorization to skip a fresh window check.

Final focused CI: `scripts/ci.sh --author --job static --job hook-test --job harness --job paper --job rubric` passed all five jobs in 701 s, log `build/ci/20261016T181512Z-975363/` (authoring at `3dab787` plus this follow-up). Static: 396 course-map regressions; hook: 7,101 cases; harness: 565 core, 50 adapter, 185 sandbox and 79 benchmark tests, with its author reference checks. Separately, 398 static wrapper tests passed with one skip; Q12/Q15 checked 92 live pins with zero problems; 112 rubric pins are current. Q09's runner input hash was recaptured with unchanged displayed output. All 18 chapters lint clean, the ten public forms regenerate exactly, and the staged-tree leak verifier reports 18 modules, 1,647 public files, OK. These selected jobs do not close F1/F2's full CI requirement.


## 9. Basic freeze continuation (2026-10-16 America/Chicago)

D36's reference-score remeasurement and the complete Verus feedback smoke are complete (Δ245). Q15 measurement metadata is resealed; reference programs and prose checks are unchanged. The manifest check passes and all 88 current task cards remain attested. A witness-removal parser bug is fixed with regression coverage. The missing agent dashboard examples and several deferred header/record notes are corrected and their affected pins recaptured. Full author/study CI is next; bank sources are being replayed separately.

The fresh quota sentinel still reports `rejected` at seven-day utilization 1.0. No model acceptance or calibration result is inferred from the scripted verifier smoke. F3–F6 remain required, and the release branch is not created while those checks are deferred.


## 10. Bank replay and Batch plan consistency (2026-10-17 UTC)

Every bank's quoted check was replayed with its documented setup or follow-up edit: 362 formal command cases, 14 Python examples and 24 audit/freeze examples, all 400 matched their expected summaries. Initial mismatches were replay-setup mistakes, corrected to match the written instructions; no bank program or quoted result changed. Source hashes, explicit variant recipes, actual commands, exit statuses and stdout/stderr are private evidence under `author-probes/dv7-freeze/`. The dated Toolchain notes record the scope: verdict/count and numerical/audit/freeze checks, without claiming byte-for-byte diagnostic recapture.

Q12/Q15/Q18 problem lists, answer templates, rubrics and all six lab calibration fixtures now agree on the Batch plan binding; Q12's standalone flawed fixture does too. Method-only fixtures describe a prospective plan and cannot open a batch. An actual run still needs the exact final digest inside the hashed pre-registration and a fresh unlocked gradebook row; a separate pilot or subset batch gets its own binding while preserving the registered method. No digest was invented and no batch was opened. Rubric source pins were refreshed. All 36 learner paper documents and the seven changed fixtures compile; 19 calibration-harness tests and 37 simulation-harness tests pass. All 18 chapters lint clean, the 49-module course map passes and 112 rubric pins are current. The staged-tree leak verifier scans 18 modules over 1,648 public files, OK. The live calibration sessions remain pending.

The simulation runbook now explicitly covers Q01 tutor intake, Q01 discussion and a seeded non-empty review queue with date/box/graduation assertions. These are prepared cases, not model results. The weekly-window deferral and F3–F6 remain unchanged. D43 also retains the course-level requirement for the other known-good contractor transcripts; they follow the capstone and three gold transcripts.

Full author CI started at `5d9be4e`, log `build/ci/20261017T003253Z-2536741/`; static, hooks, Q Dafny, Q Verus, planned R tracks and pins passed. Empty-body and the remaining jobs are running; full study CI is queued after author success. Focused author CI over the subsequent text/fixture changes passed `static`, `paper` and `rubric`, 3/3 in 418 s, log `build/ci/20261017T012909Z-3617441/`. Neither complete CI mode is claimed passed yet.

## 11. Claude quota blocker deferred by the user (D45; 2026-10-17 UTC)

**Authority:** after the five Claude-dependent work categories were explained, the user instructed: “record the blocker and skip. continue to build.” This supersedes D43's requirement that those live results gate the current build/release; it does not spend the study reserve, override the provider window, or remove any guard.

**Blocker:** the most recent pinned sentinel returned `rejected`, seven-day utilization 1.0. The expected reset is 2026-10-19 12:00 UTC (07:00 America/Chicago). No further model call is made for this build. A fresh allowed-window check is required before any later live validation.

**Deferred, not passed:** guard acceptance in real Claude sessions (F5); skill simulations across Q01–Q18 including the supplementary cases (F3); 78 grader calibration sessions (F4); the final-contract capstone and three gold contract transcripts (the model portion of F6); remaining known-good agentic contractor transcripts (the course-level line); scans of those not-yet-created transcripts (the corresponding portion of F7). These are follow-up validation debt on Basic. The local dry-run, automated guard regressions, scripted feedback smoke and reference checks retain their exact scopes and do not stand in for these live results.

**Continue building:** complete model-free author/study CI and frozen-tree leak/history checks, prepare the D42 squash release with this exception recorded, then continue the R core on the Basic baseline. A local-check failure still requires a fix; the user did not waive it. Preserve old authoring history outside shipped ancestry and leave design-only main unchanged.


## 12. Initial Basic candidate prepared (2026-10-17 UTC; Δ248)

The candidate contains the Q-only course snapshot with all eighteen Q-core registry records set to `shipped`, with the guards in study mode. R and challenge records remain planned. It is prepared as one content commit whose sole parent is design-only main, without any old authoring ancestry. The README and CLAUDE status expose D45's live-validation deferral.

**Not promoted yet:** the full local author run `build/ci/20261017T003253Z-2536741/` continues in the Q authoring worktree, with full study CI queued after its success. The candidate's structural/static checks and final tree leak audit are checked separately after the release metadata changes. Native failures still require fixes; a partial run is not reported as a complete pass. The final release records both complete CI summaries and the history check.

## 13. Initial Q core released locally on Basic (2026-10-17 UTC; Δ250)

The full author run passed 14/14 in 15,977 s; the full study run passed 12 jobs
with two expected author-only skips in 4,271 s. The author run began at `5d9be4e`;
its formal sources, wrappers and native proof payload are unchanged through
the final Q author tree `40a9b5a`. The intervening paper, bank, status and
synthetic-fixture changes have focused author text CI, full final study CI
and candidate static coverage. The candidate differs from `40a9b5a` only in
README/CLAUDE/release status documentation and the eighteen Q status fields.

Candidate static `build/ci/20261017T032721Z-61186/` passed in 417 s. Final
course-map, study settings, protected source-leak and D42 ancestry checks
are recorded with the release evidence under `author-probes/dv7-freeze/`.
Release-only documentation is then folded into the single content squash;
its sole parent remains design-only main. Preserve the old Q authoring
history on an archive branch and recreate authoring from this Basic baseline.
The primary main checkout stays unchanged. No external push is performed.

Q01–Q18 are shipped in this initial Q-only snapshot. R and challenge records
remain planned; build and validate R on Basic next, then branch challenges
from the completed Basic course. D45's live guard/simulation/calibration and
contractor/capstone transcript debt remains explicit and unpassed. Neither
the provider reserve nor any course guard was overridden.

Sections 1–12 retain dated checkpoint history. Their earlier running/queued
or not-promoted text describes that checkpoint; this release entry and the
current freeze table give the final local state. The read-only history
checker now checks basic's whole chain as an invariant, and CI's static job
runs it (§14).

## 14. Review fixes on Basic (2026-10-17; Δ275)

Independent reviewers audited Codex's round (Δ242–Δ250) and the released
branch: the Q release implemented D36–D45 correctly and was squashed
cleanly; it shipped past the freeze bar under D45, which the user has now
resolved by D47 (the usage window has reset; the deferred live checks run
in a separate validation lane, and the learner may start studying). The
user also decided D46 (basic holds the Q core only; it was rolled back
from a state that also had R01–R02, now archived), D48 (R03's classes as
`u32` code-point pairs; the shared A2 layer provisional until R03 and R06
pass) and D49 (Lab α redesigned around one pre-registered primary contrast,
at least 60 regex-lemma clusters plus a public slice sized by a power
simulation, and a 5-cluster pilot outside the confirmatory runs).

The fixes, each a `basic: ` commit on basic (Δ275 lists the evidence; F-1 to F-5 were found by the live-check lane running under D47):

| # | fix | where |
|---|---|---|
| 1 | the release history is an invariant (a linear chain of single-parent `basic: ` commits on main, no archived ancestry), run by CI's static job | `scripts/check_release_history.py`, `scripts/ci.sh` |
| 2 | the README and CLAUDE CI claims name the trees the full runs used | README, CLAUDE.md, F1, F2 |
| 3 | stale text: §0, F8, QPLAN §22.6 (D39, 74 members) and §25 (Q15.H2d/H2v at 8/7 minutes, D40) | this file, QPLAN |
| 4 | D39 in Q12's B1 tasks-and-strata field and rubric line CT.b, the fixtures kept consistent, the rubric re-pinned | `paper/Q12_problems.tex`, `paper/rubrics/Q12_rubric.md` |
| 5 | the learner branches from the local `basic` until it is pushed | README Setup 3 |
| 6 | vp3-he077's kept-definition marker moved author-side; the card rebuilt and re-attested | `scripts/dvl/{benchstrip,lab2pub}.py`, `bench/local/q/lab2pub/`, `sandbox/attested.toml` |
| 7 | the hook test's lane fixtures no longer depend on the host | `scripts/test_hooks.sh`, `tests/hooks/` |
| 8 | words glued to numbers spaced | this file, Δ250 |
| 9 | the DELTAS index complete; Δ275 records the review, D46–D49 and the fixes | DELTAS |
| 10 | every capped solver job runs in the user slice `dvl0.slice` (MemoryMax=48G, MemorySwapMax=0), each with its own cap; Δ245 corrected | `scripts/dvl/common.py` |
| 11 | a passing CI run keeps the scratch its reports name | `scripts/ci.sh` |
| 12 | a Verus build that fails after verification reports stage `link` or `compile`, never `verify` | `scripts/dvl/verus.py`, Q12 §2 |
| 13 | the armed-units test fixture no longer depends on the real records' shipping state (found by this lane's full CI) | `tests/wrappers/test_dafny_tool.py` |
| F-1 | the three study-clone harnesses run from a detached HEAD (`clone_head`) | `tests/acceptance/guard_doors.py`, `skill_sims.py`, `calibrate.py` |
| F-2 | `ReadMcpResourceDirTool` (Claude Code 2.1.302) is left alone, as its sibling is | `guard_doors.LEFT_ALONE` |
| F-3 | the six lab calibration fixtures no longer hold the drop-in marker word; all 36 make a drop-in | `tests/instructor/fixtures/` |
| F-4 | a study root's cleanup removes and records a session's stray files | `guard_doors.remove_study_root` |
| F-5 | a tutor turn asks no question of a higher rung | `.claude/skills/tutor/SKILL.md` |

Checks on the fixed tree before its full CI: `check_course_map.py` (49
modules, 18 shipped), `chapter_lint --all` (18 chapters, 0 problems),
`update_rubric_pins --check` (112 current), the leak verifier (18 modules,
1,644 public files, OK), `avoid.sh` (0 hits), `test_hooks.sh` (7,107
passed, 0 failed), `lab2pub.py build --check --author` (10 cards current).

**Full CI on the fixed tip `148fa73` (clean tree; each run under
`systemd-run --user --scope -p MemoryMax=24G -p MemorySwapMax=0`):**

- `scripts/ci.sh --author`: `ci.sh: PASS — 14 passed, 0 failed, 0 skipped, 0 absent, in 17138 s (author run; basic @ 148fa73, clean tree)`, logs `build/ci/20261018T075251Z-2095832/`.
- `scripts/ci.sh`: `ci.sh: PASS — 12 passed, 0 failed, 2 skipped, 0 absent, in 4701 s (study run; basic @ 148fa73, clean tree)`, logs `build/ci/20261018T123901Z-2823479/`; the two skips are the author-only empty-body and rubric jobs.

Earlier attempts on this lane's intermediate tips are not passes: an author
run at `a712802` failed static (the single-route check, fixed), a focused
run at `c99b5e9` failed wrappers (the armed-units fixture and the kept
reference scratch, fixed), a full author run at `3f083c2` passed 14/14 in
16,454 s before the live-check lane's five fixes were added, and the runs
at `3f083c2` (study) and `7ce6e87` (author) were stopped before they
finished, to run both modes on the final tree. The live checks
themselves (F3–F6) are recorded in §1 and §5 (Δ276); nothing was re-run
live after this lane's fixes.
