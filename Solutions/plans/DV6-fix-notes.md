# DV6 fix lane: the freeze-bar review's blocker, majors and cheap minors

Author-only notes (reference class). The lane's brief: re-verify and fix every blocker and
major of the three DV6 reviews (decisions, leakage, triage) and the cheap minors; re-run the
affected checks; report each finding's outcome; put what is the user's as DECISION NEEDED.
Memory share 32 GB, one solver job at a time (every job under `systemd-run --user --scope -p
MemoryMax=… -p MemorySwapMax=0`). No model was called. No DELTAS, CLAUDE.md, README or QPLAN
status line written: the README and CLAUDE.md changes are ready as patches (§4). Archive:
`~/.cache/dafny-verus-learn-0/author-probes/dv6/fix/`.

## 1. Outcomes, finding by finding

Legend: **fixed** (re-verified, fixed, checks re-run), **decision** (the user's; §3),
**deferred** (needs a run or a lane this one could not make; §5), **rejected** (did not
reproduce).

### Triage review

| # | sev | finding | outcome |
|---|---|---|---|
| T-B1 | blocker | the guard never sees the Monitor tool | **fixed.** Reproduced (Monitor `cat Solutions/plans/…` exit 0; Bash exit 2). `.claude/settings.json` matcher names `Monitor`; `spoiler-guard.sh` treats it as a shell tool (`Bash\|PowerShell\|Monitor`, its `command`), and a Monitor WebSocket source (`ws.url`, read by both parsers) takes the web tools' rules (rule 2c while a contract runs, rule 1 on a reference path). 10 must-block and 2 must-allow template rows (rules 1, 1b, 1c, 1d, 1e, 2c; ws); `test_hooks.sh`'s `covered` list names Monitor. `guard_doors.py`: door `h_monitor`, `--allowedTools` adds Monitor, and `report` fails when a session tool is neither matched by the clone's matcher nor in `LEFT_ALONE` (`uncovered_tools`). `test_hooks.sh`: 6,925 passed, 0 failed. |
| T-M1 | major | AUTHOR_OPTS lacks `mksandbox-run --attest-rescan` | **fixed.** Added; in the same run as above. |
| T-M2 | major | no full CI run of the tree to freeze | **fixed in part**: this lane's runs are in §2 (they validate this lane's tree; the integration lane's own edits land after them, so the freeze entry re-runs them once more if any of its edits touches a checked file). |
| T-M3 | major | every model-calling line of the freeze bar is missing or stale | **decision** (§3 D-1, the budget); the tools are made ready (window rule, token rule, delivery exemption, Monitor door, plants). |
| T-M4 | major | the three session tools ignore the window rule | **fixed.** `guard_doors.window_verdict/window_gate/window_record` (sandbox/apparatus.toml `[window]` through `fvh.budget.check_event`; worst event of a stream; no event = stop); `guard_doors.run`, `skill_sims.turn` and `calibrate.run` judge every session, keep the verdict in `state.json` (calibrate now saves state on a refusal), and start no session after a defer or stop until `--window-ack`. Unit tests in `test_skill_sims.py` (`WindowRule`: verdicts on synthetic `allowed_warning`, a 0.6 window, overage, no event; record and gate). |
| T-M5 | major | the model budget for the freeze bar | **decision** (§3 D-1). |
| T-M6 | major | no harness case exercises D32's anchors | **decision** (§3 D-2): every /review-code gate must pass first (SKILL gate list), so a case needs a gate-green module state; one built from invented material is a whole module's independent solution. |
| T-M7 | major | the leak-token false positive; no delivery exemption | **fixed.** `guard_doors.code_line`: a line token needs a code mark (`;{}()=<>[]:` or an identifier with `_`, a digit or a camelCase hump); used by `leak_tokens` and `calibrate.reference_tokens`. `skill_sims`: `contract_files` (a case whose prompt starts `/contract`: the named modules' `agentic` lists) and `split_delivery` (Write/Edit content into an allowed file, Read results of one, and the allowed files left in the clone: patterns only; everything else both detectors). Tests: `LeakTokens`, `ContractDelivery` (37 OK). |
| T-M8 | major | rustup self-updated; the image lock no longer matches | **fixed in part / decision.** Re-verified: host `~/.cargo/bin/rustup` is 1.29.1 (`dda72343…`), the lock pins `20a06e64…`. Identified the pinned binary: **rustup 1.28.2**'s `rustup-init` hashes to `20a06e644b0d9bd2fbdbfd52d42540bdde820ea7df86e92e533c073da0cdd43c`; archived at `dv6/fix/rustup/rustup-init-1.28.2`. The README fix (`--no-self-update`, `rustup set auto-self-update disable`) is in the README patch (§4). Replacing the user's `~/.cargo/bin/rustup` is a host change: §3 D-6. |
| T-M9 | major | README Setup gaps; stale README:13 and CLAUDE.md:5 | **fixed as patches** (§4: README Setup step 1 (rustup, Python 3.12), step 2, a step-5 table of uv, Docker and the images, Ollama, age and the key, the public sets, the editor; README:13 states D27; the DV1b/Release-A "arrive" lines dropped; CLAUDE.md:5's attestation and simulation lines). Q06 §0 and Q07 §10 step 4 now point at the table (they read correctly once the patch lands). |
| T-M10 | major | Lab 1's run setup cannot be followed; `get_bench.sh --check` vacuous | **fixed.** Q12 §0 names `scripts/get_bench.sh --all` before `--check`; §4.3 gains a **Run setup** paragraph (install and check; the first forty members in the seed's order are the pilot's candidates, one Qwen sample each, 80 calls; the first twenty the stratum's tasks unless the pilot's rate falls outside 0.1–0.9; the pilot is its own plan in the batch form). `dvl/bench.py --check` with no set installed exits 3 ("nothing was checked"); test `test_check_with_no_set_installed_is_no_pass` (tests/bench/test_get_bench.py, 25 OK). The pilot-candidate reading follows QPLAN §22.6 ("twice the needed public candidates"). |
| T-M11 | major | six practice chapters open Solutions/ before the tier viva | **fixed.** Q10, Q11 (`/viva Q12`), Q13, Q14 (`/viva Q15`), Q16, Q17 (`/viva Q18`): "only after `/viva Q1n`, which examines Q1m too". |
| T-M12 | major | Q15.H2d/H2v not admitted but budgeted | **decision** (§3 D-5). Not applying (a) meanwhile: its edits reach the hollow learner file's CALIBRATION block, its twin and their pins, and (b)/(c) would revert them. |
| T-M13 | major | the toolwright and toolsmith have no reference twin | **fixed.** `Solutions/tools/Q12/holecount.py` (a reference INTERFACE and the tool; documents only) with `Solutions/tools/Q12/test_holecount.py` (7 OK, over `harness/tests/q/fixtures/q09/`), run by `ci.sh --author`'s harness job. `Solutions/tools/Q15/toolsmith.py` (reference INTERFACE; candidates: as shipped, then each call/index/method term of the step mentioning every bound variable, then pairs; ≤ 16 runs; `vcheck --gate --json` only). Recorded run over the battery (16 GB scope, one job at a time, 35 runs, 38 s): **24/24 goal files pass the gate**, and `specfreeze --against` each shipped goal reports 0 findings on all 24; the chosen triggers equal `Solutions/tools/Q15/battery/`'s repairs. Archive `dv6/fix/toolsmith/`. |
| T-M14 | major | Q12's rubric never reviews `policies.py` | **fixed.** Pin `Solutions/harness/q/fvh_q/policies.py`, A2 gates it, new **C7** (one call per `propose`, none after the budget or seeds, prompts only from `render` and protocol state; grade 2 at `file:line`). `update_rubric_pins.sh`: 112 pins current. |
| T-M15 | major | planted rows name harvests the module lacks; the TC table not recorded | **fixed.** Q04 `calc` → Q10 (assertion repair, H3); Q11 `&mut self`/`Result` → Q14.H2v's toy; Q17's class and invariant rows → Q18's statements (§4 steps 1-2), its permission row ends at the core (the challenge branch); Q14's Q18 cell dropped; Q12 and Q15 tool rows → Q18 arm G (§5), with a callback sentence in Q18 §5. The TC1–TC14 table is copied into QPLAN §29 with the pass's note. |
| T-m1 | minor | Q12/Q18 references and a total | **fixed.** §5.5 → §5.3; `python -m fvh report Q12 --reverify all`; spec §11.1 → §11.4; "(90 minutes in all)". |
| T-m2 | minor | overstated harvest cells | **fixed.** Q05/Q11 drop Q14 from the frames rows; Q03 → Q08 §2.1 and Q11.H5d; Q07's `recommends` row says it is taught in full there; Q16's speed-test row → Q18's capstone tests, and Q18 §4 step 2 asks for one row too large for a repeated-addition product; Q09 → Q12.H3v; Q05 drops Q32; the challenge targets say "(the challenge branch)". |
| T-m3 | minor | Done lines disagree (Q01 vaudit, Q11 specfreeze, Q01 Setup) | **deferred** (§5): the header fixes edit shipped learner files, whose shipped-state and chapter pins then need a solver re-capture. |
| T-m4 | minor | Dafny `specfreeze --against` passes on an empty frozen file | **fixed.** `dvl.dafny.freeze_check`: a frozen file with no statement and no abstract module is `freeze-empty` (as Verus). Q18's snapshot now says so in both languages. Test in `test_dafny_static.py`. |
| T-m5 | minor | no chapter, rubric or fixture names the Batch plan field | **deferred** (§5): a rubric line needs the six calibration fixtures, the flawed pre-registration fixture and a paper rebuild with it. |
| T-m6 | minor | small stale lines | **fixed in part**: Q12 §0 and the rubric's CA.a name the assumption audit; Probe R's "once it exists" dropped. Deferred: the HAND block's H4v–H7v rows and Q07's PENDING comment (learner files; pins). |
| T-m7 | minor | intro band's lower bound | **fixed** (0; a `test_course_map` case: 396 passed). |
| T-m8 | minor | Q15/Q17/Q18 lack the dashboard subsection | **deferred** (§5): each needs a pinned live fence. |
| T-m9 | minor | the banks' probe outputs are one-time captures | **deferred** (§5): a solver replay of every bank probe. |
| T-m10 | minor | no include_bytes! fixture | **fixed** (one must-block row; rule 1). |
| T-m11 | minor | CI and README lines from before D26 | **fixed**: `ci.sh`'s header; the README lines are in the patch (§4); the spec and design lines are the integration lane's. |
| T-m12 | minor | records and small learner-facing gaps | **fixed**: the leak table (18 rows, 2026-10-14, 8 OK each), the calibration README's Last run (72 sessions; the old clone is gone; the window rule), Q07's mutant route (in place, then `git restore`), Q04 §9's vstd source path; README's P1 list in the patch; CLAUDE.md:5 in its patch. |

### Decisions review

| # | sev | finding | outcome |
|---|---|---|---|
| D-r1 | major | `ghost var g := M(a);` and a shadowing ghost pass the code check | **fixed.** Re-verified on invented cards. `labcode._d_annotations`: a ghost variable is an annotation only when its right-hand side calls no non-ghost method or constructor and allocates nothing (`_d_runs_code`) and its names collide with no non-ghost parameter, out-parameter or local of the method (`_d_param_names`, `_d_local_names`); otherwise it is code (fail-closed); a ghost update likewise. New `PublicCardGhostCode` tests (both reported deliveries, `new`, a shadowed parameter → `lab-code-changed`; an honest ghost var passes). In memory, the code check on all 30 sealed Lab 2 reference programs (20 local, 10 public): 0 findings. |
| D-r2 | major | Lab 3's references live only in an unversioned cache | **fixed.** `sandbox/seal_hidden.py --stratum` seals a stratum's reference deliveries; `Hidden/labs/Q18/refs.tar.age` (8 files, sha256 `4af14331…8c4e`, manifest `abfe21e8…ee74`) pinned in `bench/local/q/crate/STRATUM.toml` (`refs_archive`, `refs_sha256`, `refs_files`, `refs_manifest_sha256`); `dvl.sandbox._lab3_refs` reads it through `_sealed_tree`; `SEALED_REFERENCE_DIRS` is empty (a plaintext directory still serves a stratum with no refs archive, the tests' decoys). The twins digest is unchanged (`68 twins, sha256 77a7234b1d33a98d`), so `--attest-rescan`: already 88 of 88, `attested.toml` unchanged. Test `test_the_lab3_references_from_their_sealed_archive`. |
| D-r3 | major | D30 misses the cross-language overlap | **decision** (§3 D-3). |
| D-r4 | major | S1 counts annotation-only mutants | **decision, with the option added**: `labcode.code_mutant` built and tested; option (d) written into the lab2 notes' DECISION 1 with its static measure (§3 D-4). |
| D-r5 | major | no /review-code calibration exists to re-run | **decision** (§3 D-2). |
| D-r6 | minor | `card_rule` hangs on the path's spelling | **fixed.** Resolved against the cwd; a copy of a shipped form's bytes takes its rule; a path under a Lab 2 stratum's directory that names no card's form is `lab-code-unchecked`. Tests `CardRulePaths`. |
| D-r7 | minor | `label L:` and qualified lemma calls refused | **fixed** (both, with tests); a qualified call of a non-ghost method stays code. |
| D-r8 | minor | the self-test reads the sealed references | **fixed.** `author_scan(…, sealed=True)`; the self-test passes `sealed=False`. Test `test_an_author_runs_self_test_reads_no_sealed_source`. |
| D-r9 | minor | the lab2pub header's "in no course file" | **fixed** in the header and in `lab2pub.py`'s `STRATUM_HEAD` (`build --check`: 10 current). |

### Leakage review

| # | sev | finding | outcome |
|---|---|---|---|
| L-1 | major | the git history keeps fixed answers | **decision** (§3 D-7). |
| L-2 | major | two simulation plants are answers | **fixed.** `h2d-normalized-prefix` plants `invariant n < |s|`; `q11-h7d-forwards` plants the postcondition unsubstituted. `skill_sims.plant_overlaps` (run by `plant`, author-only): refuses a plant whose added text shares a line of ≥ 12 characters or a conjunct (≥ 9 characters, split at `&&`, `\|\|`, `==>`, braces, semicolons) with any twin's answer region, the declared generic lines aside (`PLANT_GENERIC`). All 11 plants pass; both old plants are caught. |
| L-3 | major | the gold transcripts do not exist | **decision** (§3 D-1); the delivered-code rule is built (T-M7). |
| L-4 | minor | `LOOPDIR_D` is Q10.X1d's answer renamed | **fixed.** A down loop whose statement is `|s| > 0 ==> t >= s[0]`, no fold invariant and no slice lemma; `Total` is `|s|`. `test_forms_static.py` 60 OK. |
| L-5 | minor | the grading notes' DELTAS text names a sealed card | **fixed** (no card id, no token counts). |

## 2. Checks run

| command | result |
|---|---|
| `bash scripts/test_hooks.sh` (4 GB scope) | 6,925 passed, 0 failed |
| `python3 -B -m unittest discover -s tests/instructor/simulations` | 37 OK |
| `… -s tests/instructor/calibration` | 18 OK |
| `… tests/wrappers -p test_lab_code_static.py` | 27 OK |
| `… -p test_forms_static.py`, `test_dafny_static.py`, `test_verus_static.py` | 60, 58, OK |
| `python3 -m unittest tests.sandbox.test_sandbox.AttestSealedReferences` | 12 OK |
| `python3 -m unittest tests.bench.test_get_bench` | 25 OK |
| `python3 scripts/test_course_map.py`; `check_course_map.py` | 396 passed; OK |
| `chapter_lint.py --all` | 18 chapters, 0 problems |
| `update_rubric_pins.sh --check` | 112 current |
| the leak verifier (README's) | 18 modules, 1,634 public files, OK |
| `lab2pub.py build --check` | 10 cards current |
| `mksandbox-run --author --attest-rescan` (8 GB) | already 88 of 88; attested.toml unchanged |
| in-memory code check on the 30 sealed Lab 2 programs | 0 findings |
| `Solutions/tools/Q15/toolsmith.py --battery …` (16 GB), then `specfreeze --against` ×24 | 24/24 gate; 24/24 0 findings |
| `Solutions/tools/Q12/test_holecount.py` | 7 OK |
| CI (§2.1) | see below |

### 2.1 CI on this lane's tree

Three runs, one at a time, each under `systemd-run --user --scope -p MemoryMax=16G -p
MemorySwapMax=0` after `free -g` showed at least 31 GB available, on HEAD 83531a8 plus this
round's 94 uncommitted changes (every DV6 lane's, this lane's included; the notes file excepted):

- `scripts/ci.sh --author` (build/ci/20261014T190448Z-3042080): `ci.sh: PASS — 14 passed, 0
  failed, 0 skipped, 0 absent, in 16404 s (author run; authoring @ 83531a8, 94 uncommitted
  change(s))`. Its pins job is `pins --ci` over every module (823 pins, 0 problems), so it
  covers the grading lane's `pins.py --ci --module Q13 Q15 Q17`; its harness job ran the Q12
  toolwright's reference tests.
- `scripts/ci.sh` (study mode; build/ci/20261014T233813Z-1561428): `ci.sh: PASS — 12 passed,
  0 failed, 2 skipped, 0 absent, in 4210 s (study run; authoring @ 83531a8, 94 uncommitted
  change(s))` (empty-body and rubric skip: author-only).
- `scripts/ci.sh --author --brittleness --job brittleness` (build/ci/20261015T004823Z-2466350),
  the first course-wide brittleness run: `ci.sh: PASS — 1 passed, 0 failed, 0 skipped, 0
  absent, in 1204 s (author run; authoring @ 83531a8, 94 uncommitted change(s))`.

The integration lane's own edits (DELTAS, the README and CLAUDE.md patches, QPLAN's status
line) land after these runs: the freeze entry re-runs the static job at least (the leak
verifier and the course map read those files).

## 3. DECISION NEEDED (the user's)

- **D-1, the freeze bar's model sessions and their budget** (T-M3, T-M5, L-3). About 150
  sessions (calibrate 72, the simulations about 50 turns, guard_doors 11 doors, 3 gold and
  21 known-good `/contract` transcripts) against a seven-day window at 0.58, which the window
  rule now defers at. (a) wait for `allowed`, then run in priority order guard_doors →
  simulations → calibrate → gold transcripts → the other known-good transcripts, each batch
  stopping at a defer (recommended); (b) release a stated number of calls from the study
  reserve; (c) narrow the bar to the user's list (simulations, `calibrate.py all`,
  `guard_doors.py all`, the dry run), and the 21 known-good transcripts become post-freeze
  fixes on basic.
- **D-2, D32's /review-code calibration** (T-M6, D-r5). /review-code refuses unless every
  gate passes, so a case needs a gate-green Q13 and Q15 state. (a) build invented gate-green
  states (a module-sized independent solution each; large); (b) run the cases on a clone
  whose Q13/Q15 learner files are their reference twins, the module's own patterns and tokens
  dropped from the scan (the review reads files equal to the reference by design), with the
  reported first-run verdict in the prompt: `weak` → C5/C4 at 2, `undecided` → no anchor, a
  later run → recorded, no anchor (recommended: it tests the anchors, which is what D32
  asks); (c) record D32's calibration as not runnable and rely on the rubric text.
- **D-3, D30 across languages** (D-r3). Re-verified: `--members humaneval-verus --lab Q12`
  gives 78 members, among them human_eval_048, 052, 062 and 063, whose Dafny versions are
  Lab 2's dp1, dp2, dp5 and dp3. (a) Lab 1's draw also excludes the HumanEval ids of Lab 2's
  public Dafny cards (74 members; STRATUM header, Q12 §4.3, B1, a `Lab1Draw` test)
  (recommended); (b) keep D30 and record the overlap in Q12's disclosure field; (c) as built,
  and Q15's report flags a Lab 2 Dafny card whose HumanEval id was in Lab 1's draw.
- **D-4, S1's mutants on a public card** (D-r4): the lab2 notes' DECISION 1 now has option
  (d) (drop the mutants that change only annotations, `labcode.code_mutant`; 192 of 299
  dropped on the sealed references). Recommended: (d) with (a).
- **D-5, Q15.H2d/H2v's minutes** (T-M12). (a) mark S12 gated at 0 minutes (QPLAN §25.3/§25.7,
  chapter §0, the CALIBRATION block, the units pin; total 613); (b) build F-H2d/F-H2v (the proof
  given) with their four results; (c) admit the pair under the short-format band exception as
  D2 did for H1, adding it to OUT_OF_BAND (recommended).
- **D-6, the host's rustup** (T-M8). (a) put back rustup 1.28.2 (`install -m 755
  ~/.cache/dafny-verus-learn-0/author-probes/dv6/fix/rustup/rustup-init-1.28.2
  ~/.cargo/bin/rustup`, then `rustup set auto-self-update disable`; its sha256 is the lock's)
  (recommended: the images stay valid, `build-images.sh --check` passes); (b) re-lock at the
  next image rebuild, which D33 already defers the judge's verdict-only output to; (c) rebuild
  the images now (then D33's deferred item can land with it).
- **D-7, cutting `basic` without the history** (L-1; the user's, since the cut needs their
  approval). (a) cut `basic` as one squashed commit of the frozen tree on top of `main`
  (`git commit-tree <frozen tree> -p main`), re-create the authoring worktree from
  `origin/basic`, and never merge the old `authoring` history into a shipped branch; add a
  freeze-bar check that `git log basic` holds no pre-cut commit but `main`'s design commit,
  and move Δ120's squash item onto the cut in CLAUDE.md item 3 (recommended); (b) keep the
  history after rewriting the leaky blobs (filter-repo); (c) keep it and widen README's
  history rule to every file.

## 4. Ready patches (for the integration lane; this lane writes neither file)

- `dv6/fix/README.patch` (`git apply --check` clean on this tree): Status (D27's rule; P1's
  nine cards), Done and Predictions first (no "arrives in DV1b"), Setup step 1 (rustup, Python
  3.12), step 2 (`rustup set auto-self-update disable`, `--no-self-update`, `vcheck
  --selftest`), step 5 (the table), the vcheck line, the CI lines (`--quick` about ten minutes;
  the gate before every merge into a shipped branch).
- `dv6/fix/CLAUDE.patch`: line 5's attestation (88 entries; the ten public cards under DV6's
  scan; Lab 3's references sealed), the D27 rule, and the Q01–Q06 simulations "to be re-run".

## 5. Deferred (each needs a run or a lane this one did not make)

1. T-m3: the Q01 crate header's vaudit line and §0 Setup paragraph, Q11's headers'
   specfreeze clause (shipped learner files: shipped-state pins and chapter fences re-captured).
2. T-m5: the Batch plan field in the chapters' field lists, B1 and a DI line, with the six
   fixtures and `paper/fixtures/Q12_flawed_prereg.tex` (a paper rebuild and the calibration).
3. T-m6 rest: the HAND block's H4v–H7v rows; Q07's PENDING comment (learner files, pins).
4. T-m8: the dashboard subsections of Q15, Q17 and Q18 (a pinned live fence each).
5. T-m9: replay every bank probe in a solver lane and re-date the Toolchain lines.
6. D-4's re-measure: killed / killed-without-ensures on the 107 code mutants (one grader
   container run on the sealed references).
7. `mcp__firecrawl__firecrawl_parse` (a user-level MCP tool that reads a local file by path)
   is in neither the guard's matcher nor `LEFT_ALONE`: the next `guard_doors.py report` fails on
   it until the author decides (cover it in the hook by its `filePath`, or leave it alone).

## 6. DELTAS-ready text (for the integration lane to number)

### Δ2xx · The DV6 freeze-bar review's fixes: the Monitor tool guarded, the window rule in the author harnesses, the code check's ghost statements, Lab 3's references sealed, the reference twins of the toolwright and the toolsmith, the plants, the chapters' cross-references — adopted (DV6 fix lane, 2026-10-14)
- **Status:** fixes the triage review's blocker and majors (T-M3, T-M5, T-M6, T-M12 and part of
  T-M8 are the user's: open), the decisions review's two majors that were code (D-r1, D-r2) and
  its minors, and the leakage review's plant and fixture findings. Like Δ195–Δ233, it names no
  answer, no reference statement and no sealed definition. Detail:
  `Solutions/plans/DV6-fix-notes.md`.
- **Change:**
  - **The guard.** Claude Code's Monitor tool runs a shell command or opens a WebSocket; the
    matcher and the hook's tool case had passed it. The matcher names it; the hook reads its
    `command` as a shell line (every shell rule) and its `ws.url` as a web fetch (rules 2c and 1).
    Fixtures for rules 1–2c and the ws forms, and for `include_bytes!`. `guard_doors.py` gains
    a Monitor door and fails its report on any session tool that the matcher misses and
    `LEFT_ALONE` does not name.
  - **The author harnesses.** The window rule (`sandbox/apparatus.toml` `[window]`,
    `fvh.budget.check_event`) judges every session of `guard_doors.py`, `skill_sims.py` and
    `calibrate.py`; a defer or stop ends the run until `--window-ack`. A leak token's line
    token needs a code mark; a `/contract` case's delivery (its allowed files' writes, reads
    and final state) is scanned against the leak patterns only. `plant` refuses a plant that
    shares an answer line or conjunct with any twin; two plants and one wrappers fixture that
    did were replaced.
  - **The code check (D27).** A ghost variable or update whose right-hand side runs a
    non-ghost method or allocates, or whose name a parameter or local holds, is code. `label`
    statements and qualified lemma calls are annotations. The rule no longer hangs on the
    task path's spelling (resolved, or a shipped form's bytes); a stray path under a Lab 2
    stratum is unchecked, never a pass. `labcode.code_mutant` (S1's annotation-only filter,
    for the user's decision).
  - **D31's sources.** Lab 3's reference deliveries are sealed (`Hidden/labs/Q18/refs.tar.age`,
    pinned in the crate stratum's STRATUM.toml; `seal_hidden.py --stratum`), read through the
    same in-memory path as Lab 2's; the twins digest is unchanged, so no entry changed. A
    run's self-test no longer reads the sealed references.
  - **Reference twins.** `Solutions/tools/Q12/holecount.py` with its tests (CI's author
    harness job) and `Solutions/tools/Q15/toolsmith.py`, whose recorded run passes the gate and
    `specfreeze --against` on all 24 battery goal files.
  - **Tools.** `get_bench.sh --check` with nothing installed fails; Dafny's `specfreeze
    --against` on a frozen file that freezes nothing is `freeze-empty`, as Verus's; the intro
    band starts at 0.
  - **Chapters and kits.** The practice chapters open a module's Solutions only after its tier
    viva; Q12 states Lab 1's run setup; the planted tables point at harvests the named modules
    carry, and the threshold-concept table is in QPLAN §29; Q12's rubric reviews `policies.py`
    (C7); references and totals in Q12 and Q18; the lab2pub header on the history.
- **Why:** the reviews' reproductions, re-run before each fix (the notes §1); the checks in
  the notes §2 (`test_hooks.sh` 6,925/0; the leak verifier OK; the rubric pins 112; the course
  map 396; chapter lint 0; 24/24 toolsmith goals; 88/88 attestations already current; the code
  check 0 findings on the 30 sealed Lab 2 programs) and CI (§2.1).
- **Touches:** Δ67, Δ107, Δ120, Δ130, Δ144, Δ148, Δ221, Δ227, Δ228, Δ232 (D27, D31, D32);
  `.claude/settings.json`, `.claude/hooks/spoiler-guard.sh`, `tests/hooks/templates/`,
  `scripts/test_hooks.sh`, `tests/acceptance/guard_doors.py`,
  `tests/instructor/{simulations,calibration}/`, `scripts/dvl/{labcode,sandbox,bench,dafny,lab2pub}.py`,
  `sandbox/seal_hidden.py`, `bench/local/q/{crate,lab2pub}/STRATUM.toml`, `Hidden/labs/Q18/`,
  `scripts/{ci.sh,check_course_map.py,test_course_map.py}`, `Solutions/tools/`, the chapters
  Q03–Q07, Q09–Q18, `paper/rubrics/Q12_rubric.md`, `QPLAN.md` §29, the test suites named.
- **Owner:** DV6's fix lane; the user (the open items).
- **Open:** §3's seven decisions; §5's deferred items; the README and CLAUDE.md patches (§4).
