# DV6 audit lane: the spec §12.1 "Per module" checklist over Q07–Q12 (author-side)

Lane `audit-q07q12`, 2026-10-14. Read-only except this file. Memory share 2 GB: no solver job ran; the
solver evidence is the author CI run `build/ci/20261014T004859Z-3125743/` (`ci.sh: PASS — 14 passed,
0 failed, 0 skipped, 0 absent, in 16918 s`, authoring @ db398e4 + 68 uncommitted = 83531a8's tree) and its
reference logs under `~/.cache/dafny-verus-learn-0/ci/20261014T004859Z-3125743/`. Static checks this lane
re-ran are marked **(re-run)**. The three check scripts (bank counts, tier draws, parallel-problem names
against the twins) are archived in `~/.cache/dafny-verus-learn-0/author-probes/dv6/audit-q07q12/`; they
print counts and names only.

Scope: Q07–Q12; layers L4 (`QG_L4_BigNat.dfy`, `qg_bignat_l4`) and L5 (`QG_L5_BigNat.dfy`, `qg_bignat_l5`);
Lab 1 (`bench/local/q/lab1/`, `paper/Q12_answers.tex`'s pre-registration, `bench/public/POOLS.toml`'s
pools). While this lane ran, other DV6 lanes were editing the worktree (D26/D31: `scripts/{firsttry.py,
pins.py,vcheck,course_mode.sh,mksandbox-run}`, `sandbox/attested.toml`, `.claude/skills/review-code/SKILL.md`,
`README.md`, `CLAUDE.md` and more). No Q07–Q12 module file is among them; the facts below are 83531a8's.

## Lines that hold (with evidence), for the release checklist

### Twin complete, hole-free, audit-clean, silent; outputs pinned
- Every Q07–Q12 twin passes the reference gate with the summary line only and `0 holes, 0 errors`, and
  its audit reports 0 findings (`verify-q-dafny.ref.log`, `verify-q-verus.ref.log`). For example:
  `Solutions/dafny/Q/Q07_InternalsI/std … verified — 134 verified, 0 holes, 0 errors`, `Q08 std 157`,
  `Q09 std 130`, `Q10 std 139`, `Q11 std 150`, `Q12 std 136`, `Q07_checks.dfy 128`, the six Dafny exits
  and the three Dafny agent files. On the Verus side: the crates `q07` 20, `q08` 22, `q09` 10, `q10` 14,
  `q11` 7 and `q12` 5, every `exit.rs`, and the `agent.rs` files of Q07–Q09.
- Python twins (`harness.ref.log`): `gate/core.py` 70 passed, 0 holes, TRIV 4/4 (Q09.H2py–H5py);
  `retry.py` 35 passed, TRIV 2/2 (Q12.H1py, H2py); `policies.py` 26 passed, TRIV 4/4 (Q12.H8py–H11py);
  `report.py` 15 passed, TRIV 2/2 (Q12.H12py, H13py).
- L4 and L5 (`verify-q-dafny.log`, `verify-q-verus.log`): the Dafny layers gate 122 and 127 verified with
  0 holes; the Verus layers `qg_bignat_l4` 15 and `qg_bignat_l5` 1; 0 audit findings each.
  `vaudit --check-trust` reports 0 findings over 7 given crates.
- `pins.py --ci`: 823 pins over 18 modules, 0 problems. `pins.py --ref`: 124 checks, 0 problems
  (`pins.log`, `pins.ref.log`).

### Exercise files are the exact hollow of their twins
- `firsttry.sh --lint-hollow --all` (`static.log`): Q07 OK (16 files), Q08 OK (14), Q09 OK (22),
  Q10 OK (4), Q11 OK (6), Q12 OK (15). `specfreeze --check` reports 0 findings for Q07–Q12.
  The `[holes Qnn d]` steps exit 0 for every module (`verify-q-dafny.log`).
- `--empty-body` (`empty-body.ref.log`): Q07 15/15, Q08 16/16, Q09 12/12, Q10 14/14, Q11 12/12 and
  Q12 20/20 holes pass the gate. Statement holes go through their client gates (Q08.T1v, H3v; Q10.H2d,
  H2v). Q07.H8v's uninterpreted spec fn is skipped with its reason. Q11.H5d is a function hole judged by
  its `cfree:` answers. Out-of-resource maxauto runs count as failing (QPLAN §30 Q66).
- **Chapter, CI and the empty-body count agree on every module (re-run, by hand):**

  | module | per-file counts in the chapter | sum | CI |
  |---|---|---|---|
  | Q07 | 4 + 4 + 3 + (2 + 2) | 15 | 15 |
  | Q08 | 1 + 3 + 3 + 3 + 2 + (2 + 2) | 16 | 16 |
  | Q09 | 1 + 1 + 2 + 4 py + (2 + 2) | 12 | 12 |
  | Q10 | 5 + 7 + (1 + 1) | 14 | 14 |
  | Q11 | 5 + 1 + 3 + 1 + (1 + 1) | 12 | 12 |
  | Q12 | 1 + 4 + 1 + 4 + 2 + 4 + 2 + (1 + 1) | 20 | 20 |

  The agent files' holes are separate. Q09's 4 + 4 bank lemmas are not gate holes.
- Slots: `slots/Q07–Q12.slots` hold 7, 6, 15, 2, 2 and 6 entries, all `???` **(re-run)**. Each count
  equals the module's prediction count.

### Item markers, concept matrix, `uses:`, coverage rows
- `check_course_map.py` (all groups) OK: 49 modules, 138 import files, 81 coverage rows (the 119 pending
  rows are homes in planned modules); `test_course_map` 396 passed (`static.log`).
- `concept_items` is present for Q07–Q09 and `{}` for Q10–Q12, as the checker requires (D4 covers
  Q01–Q09 only). Q10–Q12 declare no `write_*` constructs.

### Specimens, planted, exit and demo pins
- Every file under `specimens/Q07/`, `Q08/`, `Q09/` and `Q12/` is named in its module's
  `expected/<ID>.chapter.toml` **(re-run)**, and `pins.py --ci` checks them: 0 problems.

### Chapters
- `chapter_lint --all` reports 0 problems on every chapter (`static.log`):

  | chapter | strand sections | predict boxes | diagrams | pinned fences |
  |---|---|---|---|---|
  | Q07 | 5 | 7 | 5 | 34 |
  | Q08 | 3 | 6 | 5 | 21 |
  | Q09 | 5 | 15 | 5 | 20 |
  | Q10 | 5 | 2 | 3 | 8 |
  | Q11 | 3 | 2 | 3 | 7 |
  | Q12 | 5 | 6 | 4 | 9 |

- Each chapter ends in a "What Qnn planted" seed/harvested table. Q07, Q08, Q09 and Q12 each have a
  "What the dashboard can and cannot see" subsection under their agentic exercise.

### Agentic files
- Q07–Q09 `agent/*.dfy` and `src/agent.rs` open with the CONTRACT block on line 1, with keys `goal`,
  `allowed-files` and `acceptance`. Their twins pass the gate and the audit (see above).
- `tools/Q12/holecount.py` opens with the three-key CONTRACT docstring on line 1. There is no twin:
  see finding M5.

### Written pairs and rubrics
- `make -C paper paper` built 36 documents; `paper-solutions` exit 0. `update_rubric_pins.sh --check`
  exit 0: no PENDING pin, none stale (`paper.log`, `rubric.log`).
- Paper-card pins **(re-run)**: `sed -n` of each card's range of `cheatsheets.md`, piped to sha256,
  equals the hash its problem prints:

  | module | card range(s) |
  |---|---|
  | Q07 | 795–825 |
  | Q08 | 584–610 |
  | Q09 | 2852–2873 |
  | Q10 | 888–913 |
  | Q11 | 917–940 |
  | Q12 | 2148–2171, 2312–2338, 1681–1706 |

- Each rubric has a Verifier-anchors section, a Gate section and a Code-review focus section.
  Q07, Q08, Q09 and Q12 also have an audit debrief. Q10 and Q11 have no agentic file and no agent run,
  so they have no debrief.

### Banks (re-run: `bank.py`, `draws.py`, `pptwin.py`)
- Each bank has 8 questions, all `viva: yes`, with the spec §6.7 headings.

  | bank | mix line | backward edges | parallel problems |
  |---|---|---|---|
  | Q07 | 1/4/1/1/1 | 7 | 2 |
  | Q08 | 1/4/1/1/1 | 6 | 2 |
  | Q09 | 1/3/2/1/1 | 7 | 2 |
  | Q10 | 1/4/1/1/1 | 5 | 3 |
  | Q11 | 1/4/1/1/1 | 4 | 3 |
  | Q12 | 1/4/1/1/1 | 5 | 2 |

  Every mix line matches the counted kinds.
- Tier draws: Q09's and Q12's A–D tables have every row's strand, predict and backward-edge columns
  matching the question's own header. The draws are pairwise disjoint, with 5 distinct strands each,
  every module present and at least 2 predicts. Each bank's "no further disjoint draw" statement is
  correct: Q09 leaves Q08.K1, K3, K6 and K8 unused; Q12 leaves Q11.K3, K4, K8 and Q12.K8.
- Parallel-problem declarations share no name with the module's twins, apart from the generic `inv`
  type-invariant spec fn in Q10 and a prose word in Q08. `avoid.sh`: 0 hits, 0 stale waivers
  (`static.log`). The idle waiver N1 targets R16 and is not stale.
- Bank probes were captured on 2026-10-07 on the pins, and no pin re-checks them. L1–L5 have not changed
  since then (`git diff 6a2059f HEAD -- dafny/given verus/given` only adds L6/L7). This is not a gap,
  but a re-run of the probes would be the cheap confirmation.

### Leak patterns
- 8 patterns per module, cut from H/X/A items (per the README table). **(re-run)** The README verifier
  `… | python3 - Q07 Q08 Q09 Q10 Q11 Q12`: 48 OK lines `sol=1 prob=0 chap=0 pub=0` over 1,632 public
  files, 1 exempt line (the L7 given layer), exit 0. Pattern text was not copied anywhere.

### Calibration fixtures (content only; never run: M3)
- `tests/instructor/fixtures/Q07–Q12_{flawed,gold}_answers.tex` exist. Each flawed fixture has
  per-line `EXPECTED` and at least one clean problem (score 4):

  | module | flaws | clean |
  |---|---|---|
  | Q07 | 2 | 2 |
  | Q08 | 2 | 2 |
  | Q09 | 3 | 3 |
  | Q10 | 1 | 2 |
  | Q11 | 1 | 1 |
  | Q12 | 2 | 3 |

  `calibrate.py`'s `TUTOR_HOLE` names a hole for each of Q07–Q12.

### Minutes
- **(re-run)** Each chapter's minutes line sums to its stated total, and the total equals QPLAN's tier
  line: Q07 270, Q08 270, Q09 295, Q10 182, Q11 177, Q12 576 (100 practice + 476 Lab 1).
- Each practice line's admitted item minutes sum to the line:
  - **Q10:** 24 = 10 + 14, 15 = 7 + 8, 16, 24, 20 and 20.
  - **Q11:** 20, 20, 12, 12, 20, 15 and 15.
  - **Q12:** hand items 96 = 8 × 12; retry client 20; trigger and fuel 15; policies and report
    110 = 15 + 20 + 30 + 10 + 15 + 20.
- Q12's budget arithmetic matches the registry. Qwen: 4,320 + 80 = 4,400 calls, 540 + 80 = 620 runs.
  Claude: 160 + 20 = 180 calls.

### Lab 1
- All 22 task files under `bench/local/q/lab1/*/tasks/` match their `sandbox/attested.toml` sha256 at
  HEAD, `scan = "DV5e"` **(re-run)**. Lab 1–2's 42 references pass the lab gate with the D24 audit
  (Δ226 Why).

### Simulations (what ran, and on what)
- Q07–Q09: DV3bk, 2026-10-07, 7 cases PASS, 27 turns with 0/0 hits. Archive
  `author-probes/dv3bk/simulations/`: clone head cbb008b plus uncommitted, hook sha256 `5d1ba490…`.
- Q10–Q12: DV5ak, 2026-10-07, 7 cases PASS, 24 turns with 0/0 hits. Archive `dv5ak/simulations/`:
  head 29e725c plus uncommitted, hook `5d1ba490…`.
- HEAD's hook is `0a1c2b63…`. The staleness is in M4.

## Gaps found (ranked; each in the report too)

**Major**
- **M1. D30 is not applied.** Lab 1's draw does not exclude Lab 2's five Verus tasks:
  - None of these says so: `docs/Q12_PracticeIC.md` §4.3 (lines 273–277), the pre-registration
    template's *Tasks and strata* hint (`paper/Q12_answers.tex:29–30`), `bench/local/q/lab1/STRATUM.toml`
    (header lines 26–32), or rubric CT.a/CT.b.
  - The pool is the 83-member HumanEval-Verus pool, and Lab 1 draws 20 from it. Lab 2's tasks are
    `bench/public/POOLS.toml`'s `[[draw]] lab = "Q15"`: `human_eval_100/033/077/035/060`.
  - The learner draws Lab 1's seed, and Lab 1's forms keep the specification.
- **M2. The Q12 rubric does not review `policies.py` (Q12.H8py–H11py: four admitted holes, 75 min).**
  - A2 (line 85) still says "`policies.py` too, once DV4's protocol exists; until then it is not reviewed".
  - There is no `Solutions/harness/q/fvh_q/policies.py` pin and no code-review line. C4 covers H1py and
    H2py; C5 covers H12py and H13py.
- **M3. Calibration has never run.** `tests/instructor/calibration/README.md` *Last run* says "Not run
  yet". The checklist line ("pass a headless grader run") and the freeze bar's `calibrate.py all` are
  unmet for every Q07–Q12 module.
- **M4. Every Q07–Q12 simulation is stale. Δ233's draft lists no re-run for them** (only Q13–Q15's
  re-run and Q16–Q18's first run):
  - All six modules ran under hook `5d1ba490…`; HEAD is `0a1c2b63…` (Δ207, Δ214, Δ222, Δ225, Δ227).
  - **Q12:** the bank's tier-viva *Opening* (e43077c) was never simulated. The contract skill's
    `tools/<ID>/` Done exception was fixed after case f and never re-simulated.
  - **Q07:** the chapter's §10 replay, the agent file and rubric D8/D9 changed after DV3bk (f71dde4..HEAD).
  - **Q09:** two chapter lines changed after DV3bk. Q08, Q10 and Q11 differ from their simulations only
    in the hook.
- **M5. Q12's agentic file has no twin that proves its contract satisfiable** (checklist line 6).
  - There is no `Solutions/tools/Q12/`, and no CI job builds a reference tool against recorded documents.
  - DV5ak case f showed that the contract could not reach Done before the skill's exception. Nothing
    shows that the acceptance lines can be met.
- **M6. D31's one-time re-scan of the 22 Lab 1 entries has not landed.** It must re-scan them with Lab 2
  and Lab 3's references as twins. Another lane was editing `sandbox/attested.toml` while this audit ran.
  Re-check after it lands: every Lab 1 entry rescanned, 0 refused, sha256 unchanged.

**Minor**
- **m1.** `dafny/Q/Q07_InternalsI/std/Q07_InternalsI.dfy:393–394` still says the replay is "PENDING until
  the sandbox arrives, DV4 build step 3b". Δ202 ran it, the chapter's §10 quotes it, and rubric D8/D9 was
  updated.
- **m2.** D24's assumption audit is missing from Q12 §0 (`docs/Q12_PracticeIC.md:63`, "runs through the
  lab gate's lever check") and from rubric CA.a (`paper/rubrics/Q12_rubric.md:52`). §4.3 and the
  instrument row do name it. Δ233's draft lists this item already.
- **m3.** Rubric Probe R (`Q12_rubric.md:25`) still says "then `fvh report Q12` once it exists".
  `fvh report` was built in Δ208.
- **m4.** The pre-registration's *Batch plan* field (`paper/Q12_answers.tex:66–69`, db398e4; `fvh run`
  opens a batch only on the plan it names) is missing from five places:
  - the chapter's field list (`docs/Q12_PracticeIC.md:290–294`);
  - problem B1's list (`paper/Q12_problems.tex:42–48`);
  - every rubric B1 line;
  - both calibration fixtures;
  - `paper/fixtures/Q12_flawed_prereg.tex`.
- **m5.** The `HAND` block (`dafny/Q/Q12_PracticeIC/std/Q12_Lab1Hand.dfy:75–82`) lists only H4d–H7d.
  The Verus hand file (`lab1_hand.rs:12–15`) sends H4v–H7v there, and bank Q12's viva *Opening* reads
  the H4v–H7v rows too.
- **m6.** The intro band in `PRACTICE_BANDS` has lower bound 1 (`scripts/check_course_map.py:261`), and
  its comment says an item outside the band needs a declared exception. Four admitted items have 0
  recorded proof lines, are absent from `OUT_OF_BAND`, and carry no exception:
  - Q10.H6v (Q10 notes, line 65);
  - Q11.H3v and Q11.H10v (Q11 notes, lines 61–64 and 133–136);
  - Q12.H6v (Q12 notes, line 43).

  QPLAN §19.0 says "at most 10/15", so the band's lower bound is wrong, or the record is incomplete.
- **m7.** The leak README's *Modules* table still shows 2026-10-07 as Q07–Q12's last run. Later full
  runs (Δ225, Δ230, Δ231) and this lane's re-run passed.

## DELTAS-ready text (for the integration lane)

- **Δ2xx · DV6 audit, Q07–Q12 (spec §12.1 Per module).**
  - Every Per-module line holds on 83531a8 (evidence in `Solutions/plans/DV6-audit-q07q12.md`) except
    these: calibration never run (M3); the simulations stale under the current hook and three changed
    kits (M4); the toolwright without a twin (M5); Q12's rubric not reviewing `policies.py` (M2).
  - Two of the user's decisions are still to apply here: D30 (M1) and D31's re-scan of Lab 1 (M6).
  - Seven minor text and record fixes (m1–m7).
  - No solver job ran; the solver evidence is CI log `build/ci/20261014T004859Z-3125743/`.
