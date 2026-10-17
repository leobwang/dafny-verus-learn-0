# DV6 audit, continuity lane (spec §9.2 phase 5) — Q01–Q18 and layers L1–L7

Author-side notes (reference set). Read-only audit of the authoring worktree at HEAD 83531a8
(branch `authoring`; the working tree also carried other DV6 lanes' uncommitted edits to tools,
README and CLAUDE.md, none of them to `docs/Q*.md` or the given layers). Memory share 2 GB:
no solver job ran; every verifier fact below is cited from the chapters' pinned fences or from
the CI author run `build/ci/20261014T004859Z-3125743/` (14/14 PASS, the tree that became 83531a8).
No scratch was used.

Rules audited (spec §2.4.3 item 10, §9.2 phase 5, §12.1 "Continuity pass" and the chapter
checklist line "the planted/harvested table"; design §2.3.7 / spec §11.2.3 threshold concepts;
the lane brief): every whisper, cliffhanger or TC step pays off in a later chapter; no forward
reference to material not met (a later module, an unshipped R module, a challenge module); the
planted/harvested tables close; cross-module references (item ids, section numbers, file paths,
command names) resolve.

Ranking: blocker = stops the learner or leaks an answer; major = breaks a stated rule or a
checklist line (here: a harvest cell that names a payoff the named module does not contain, so
the seed's row does not close); minor = a cell or reference that is wrong but whose seed is paid
off elsewhere, or a reference that resolves to the wrong place.

**Result: 0 blockers, 4 majors, 7 minors.** Every TC step and every body-text whisper holds; the
gaps are harvest cells written to an earlier plan of Q07, Q14 and Q18 than the one built, plus
two section references.

---

## 1. Findings

### M1 (major) — Q04's `calc` row names Q07, which has no `calc`
- **Where:** `docs/Q04_ProofCraft.md:1091` — `| calc chains and where their errors land (P3dv, P4d) | Q07: proof engineering and porting |`.
- **Evidence:** `grep -c calc docs/Q07_InternalsI.md` → 0; no `calc` in `dafny/Q/Q07_InternalsI/` or `verus/q/q07_internals_i/`. The seed is paid off in `docs/Q10_PracticeIA.md:198` ("Q04's `calc` chains and Q02's `assert … by` are the tools"), which the row does not name.
- **Fix:** make the cell `Q10: assertion repair (H3), where a missing step is a calc line`, or add a calc step to Q07's port (§6) and say so there.

### M2 (major) — Q11's `&mut self`/`Result` row names two modules with neither
- **Where:** `docs/Q11_PracticeIB.md:397` — `&mut self with Result, nothing changed on Err (H3v, H4v) | Q13 (sub with a borrow), Q18 (the capstone's API)`.
- **Evidence:** Q13's H1v is `pub fn sub(a: &BigNat, b: &BigNat) -> (r: BigNat)` (`verus/q/q13_practice_iia/src/lib.rs:50`): no `&mut`, no `Result`. Q18's API is `BigNatCore` with `fn minus(&self, other: &Self) -> (r: Self)` and `fn to_word(&self) -> (r: Option<u64>)` (`verus/given/qg_bignat_l7/src/api.rs:19,29`). `grep -n 'Result\|Err\b' docs/Q1[2-8]*.md` → no hit. The seed has no payoff after Q11.
- **Fix:** re-point the cell to what was built (e.g. `Q14 (H2v's toy: &mut self against old and final)`, `docs/Q14_PracticeIIB.md:119–123`), or give Q18's extension trait one `&mut self` operation with a `Result` and say so in Q18 §1.

### M3 (major) — Q17's frame and permission rows (and one Q14 cell) promise a Q18 mirror that was not built
- **Where:** `docs/Q17_PracticeIIIB.md:478` (`a class that implements a given trait over a frame that grows (H1d) | Q18 (the capstone's Dafny mirror and its interfaces)`), `:480` (`one tracked permission per slot … (H2v) | Q18 (the capstone's crate: a representation invariant kept across every &mut operation)`), `:479` (`… (H1d) | Q18 (the capstone's representation)`); and the Q18 cell of `docs/Q14_PracticeIIB.md:524` (`Q18 (the capstone's Dafny mirror)` for a refinement).
- **Evidence:** `docs/Q18_PracticeIIIC.md:128–131`: "In Dafny the same operations are compiled methods of the agent file's module". `grep -n -i 'class \|refine\|&mut\|Repr' docs/Q18_PracticeIIIC.md` → only the cheat-"class" lines (X classes); the Verus operations are `&self` trait methods (api.rs above). So rows 478 and 480 have no payoff at all (Q18 is their only harvest), 479 only a generic one ("the invariants the loops need", Q18:355), and Q14:524's Q18 cell is false (its Q17 cell holds: `docs/Q17_PracticeIIIB.md:72` "as Q14's refinement did").
- **Fix:** re-point the four cells to what Q18 has: `Q18 (the capstone's statements: what each operation's contract needs, §4 step 1–2)` for 478/479; for 480 either `the challenge modules` (see m6) or drop the Q18 claim and say the permission thread ends at Q17; for Q14:524 keep Q17 only.

### M4 (major) — the toolwright and toolsmith rows name "gate v2's tools", which uses neither
- **Where:** `docs/Q12_PracticeIC.md:511` (`the toolwright (/contract Q12) | Q18 (gate v2's tools)`) and `docs/Q15_PracticeIIC.md:1005` (`a tool built to your interface and audited goal by goal (rung 12) | Q18 (gate v2's tools)`).
- **Evidence:** `harness/q/fvh_q/gate/gate_v2.py:9–17`: solo work, "Imports: the Python standard library and the frozen core `fvh` … nothing else". `grep -n -i 'holecount\|toolsmith\|tools/Q1\|toolwright' docs/Q18_PracticeIIIC.md` → no hit. The closest payoff is Q18 §5's arm G, "the agent's acceptance tool is your gate v2" (`docs/Q18_PracticeIIIC.md:463`), which neither row names and which does not call back to the interface-first discipline.
- **Fix:** make both cells `Q18 (arm G: a tool you specified, handed to an agent as its acceptance tool, §5)` and add one sentence in Q18 §5 calling back to Q12 §9 / Q15 §12 (the interface and the audit come before the agent uses the tool).

### m1 (minor) — Q05 and Q11 name Q14 as a frames harvest; Q14 has no frame
- **Where:** `docs/Q05_Frames.md:1152` (`Q14 (an abstract BigNat refined)` for `dynamic frames: Repr, Valid(), fresh`), `docs/Q11_PracticeIB.md:396` (`Q14 (a refinement with frames)`).
- **Evidence:** `grep -n -i 'Repr\|frame\|modifies\|fresh' docs/Q14_PracticeIIB.md` → only line 524 (its own table). Q14.H1d refines `QG_L4_Spec` with a record that caches its length (`docs/Q14_PracticeIIB.md:93–103`). Both rows still close through Q11 (`docs/Q11_PracticeIB.md:145`) and Q17 (`docs/Q17_PracticeIIIB.md:72,122,158`).
- **Fix:** drop the Q14 cell from both rows (or reword: `Q14 (a refinement, no heap)`).

### m2 (minor) — Q03's subset-type row names Q15 instead of Q08 and Q11
- **Where:** `docs/Q03_FirstSyntaxII.md:1041` — `subset types and their witnesses | Q15 (specifications that come with witnesses)`.
- **Evidence:** Q15's witnesses are non-vacuity witnesses for a `requires` (`docs/Q15_PracticeIIC.md:483,489`); `subset type` does not occur in Q15. Subset types return in `docs/Q08_InternalsII.md:544` (§2.1) and Q11.H5d (`docs/Q11_PracticeIB.md:57`), neither named.
- **Fix:** `Q08 (§2.1: subset types and newtypes), Q11 (H5d)`; keep Q15 only for the witness half if wanted.

### m3 (minor) — Q07's `recommends` row: neither harvest takes `recommends` or spec-fn totality up
- **Where:** `docs/Q07_InternalsI.md:940` — `total spec fns and recommends (P6v, H8v) | Q08: trait specifications; Q14: a trait with a ghost view`.
- **Evidence:** `grep -n recommends docs/Q*.md` → Q07 only. Q08's trait section has uninterpreted trait spec fns (`docs/Q08_InternalsII.md:209`) but never connects them to totality. The concept is fully taught in Q07 §2 (not a whisper), so nothing is left unexplained.
- **Fix:** one clause in Q08 §1 ("a trait's spec fn, like Q07's `top`, is total: a generic client knows only its contracts"), or re-point the cell.

### m4 (minor) — Q16's speed-test row: Q18's tests are not speed tests
- **Where:** `docs/Q16_PracticeIIIA.md:355` — `a speed test where the verifier cannot tell two methods apart (H3v) | Q18 (the capstone's tests)`.
- **Evidence:** Q18's TESTS are "the differential check's sample rows, the same rows in both languages" (`docs/Q18_PracticeIIIC.md:365–366, 383–385`); `grep -n -i 'speed\|slow\|performance' docs/Q18_PracticeIIIC.md` → no hit, though the learner's own multiplication enters the crate (`:381`).
- **Fix:** one sentence in Q18 §4 step 2: include a sample row large enough that a repeated-addition multiplication cannot finish (Q16's speed test, `docs/Q16_PracticeIIIA.md:99–106`).

### m5 (minor) — two section references resolve to the wrong place
- `docs/Q12_PracticeIC.md:47`: "the lab's acceptance (§5.5) checks the lab"; Q12 has no §5.5: Lab 1's acceptance is `### 5.3 Lab 1's acceptance` (`:319`). **Fix:** §5.3.
- `docs/Q18_PracticeIIIC.md:281–282`: "each with its catalog row (spec §11.1's G and V rows)"; spec §11.1 (`docs/design/spec4dafny-verus.md:2330`) is the mechanism table and holds no G/V row; the G1–G22 and V1–V24 rows are §11.4's fake-green catalogs (`:2463–2536`). **Fix:** spec §11.4.

### m6 (minor) — harvests that name challenge modules, which basic will not ship
- **Where:** `docs/Q05_Frames.md:1160` (`Q32 (a proof-search agent you build)`), `docs/Q16_PracticeIIIA.md:352` (`the challenge modules`), `docs/Q18_PracticeIIIC.md:691–694` (`the challenges`, `the agentic challenges Q31–Q33`, `the challenges' gates`, `Q31 (the gate and bench topic extends gate v2)`).
- **Evidence:** Q31 and Q32 resolve in the registry as `status = "planned"` (`MODULES.toml`, `title = "Gate & bench"`, `"Proof-search agent"`); the release plan freezes basic without them. Q05's and Q16's rows close in-core anyway (Q06; Q17, Q18). Q18's four rows close only outside the core, which is right for the last core module, but on basic they point at modules that are not there.
- **Fix:** keep the cells but mark them as beyond this release, e.g. `(the challenge branch)`; Q05:1160 can drop Q32. Wording only, no decision needed.

### m7 (minor) — Q09's sweep row names Q12's stage attribution
- **Where:** `docs/Q09_InternalsIII.md:913` — `the sweep, the solver swap, proof splits and trigger rewrites | Q12 (stage attribution), …`.
- **Evidence:** Q12 §2 (stage attribution, `docs/Q12_PracticeIC.md:155`) runs no sweep and no swap; the nearer payoff is Q12 §3's H3v triggers (`:220–222`, "Q09 taught triggers"). The row closes through Q15 §3 and Q18 §3.
- **Fix:** `Q12 (H3v: trigger choice)`.

### Watch item (not a finding of this lane; for integration)
The user's 2026-10-14 decisions touch chapter text that still states the pre-decision state:
`docs/Q15_PracticeIIC.md:82–87` ("One rule is not fixed yet, and the runs on the public strata
wait on it": D27 settles it); Q12 does not yet say that Lab 1's draw excludes Lab 2's five
Verus tasks (D30; `grep -n 'Lab 2' docs/Q12_PracticeIC.md` → only the planted table); Q13 §2,
Q15 §5 and Q17 §4 do not yet carry D33's "run the hidden check once per item, after the
statement is final, and report that first run" rule. The decisions lanes own these edits;
re-run this lane's §2.1–§2.3 checks on those three chapters after they land.

---

## 2. Lines verified as holding (evidence for the release checklist)

### 2.1 Mechanical cross-references
- **Item ids.** `chapter_lint.py --all`: "18 chapter(s), 0 problem(s)"
  (`build/ci/20261014T004859Z-3125743/static.log:126–146`); its item-id check
  (`scripts/chapter_lint.py:624–660`) resolves every full id `Qnn.Xx` against the registry and
  refuses planned owners, and every bare id against the chapter's own module.
- **Cross-module section references** (all six resolve): Q06:86 "Q03 §3" → Q03 §3 S9 (`:461`);
  Q06:244 "Q03 §4" → Q03 §4 S10 (`:518`); Q09:199 "Q06 §2" → Q06 §2 S10 (`:242`); Q09:372
  "Q06 §3.1" → Q06 §3.1 Triggers (`:332`, the matching loop at `:429`); Q15:520 and Q17:321
  "Q13's §2" → Q13 §2 (`:94`), which glosses all seven verdict words (`:252–255` for
  `undecided`, `mismatch`, `context`). Strand references Q02:560/877 "Q04's S5" → Q04 §5
  (`:542`), Q02:873 "Q03 S8" → Q03 §2 (`:367`), Q02:879 "Q03 S13" → Q03 §7 (`:777`).
- **Intra-chapter § references:** a script over every `§n(.m)` outside fences, design-doc
  prefixes excluded, found only the two of m5.
- **File paths.** Every backticked path in `docs/Q*.md` exists, or is a file the chapter tells
  the learner to create (`research/q06_skeleton.dfy`, `q07_frozen.*`, `q08_statements.*`,
  `q09_bank.*`, `q17_statements.dfy`, `tools/Q12/test_holecount.py`, the run logs under
  `research/runs/`), or is relative to a named directory (`tools/Q15/battery/dafny/G01.dfy`,
  `verus/q/q18_practice_iiic/src/main.rs`, `harness/fvh`'s default `bench/local/q/lab2/oracle/tasks/`
  layout, Q15:598, described as a default the tool creates).
- **Commands.** Every `scripts/<name>` named in a chapter exists. `fvh` subcommands named
  (`run`, `resume`, `report` with `--reverify`/`--judge`/`--truth`, `unseal`) are parsers in
  `harness/fvh/__main__.py:368–391`; "fvh import" hits are `from fvh import stats` in
  `python3 -c` lines (Q06:795/820/838, Q09:616/643). Skills named exist under `.claude/skills/`
  (contract, discuss, grade-paper, review, review-code, tutor, viva); `/grade-paper`'s
  `--post`, `--report` and `--fixture` are its documented modes (`.claude/skills/grade-paper/SKILL.md:9–16`).
- **Paper cards.** All 23 card ids the chapters and registry name resolve to headings of the
  learner's `cheatsheets.md` with the titles the chapters give (01.13 … 12.12); every module's
  registry `card` list is cited in its chapter (Q17's 12.12 once).
- **No unshipped trees or R modules.** `grep -nE '\bR(0[1-9]|1[0-6])\b'` over `docs/Q*.md` →
  none; no `Challenges/`, `agents/`, `dafny/R/`, `verus/r/`, `harness/r/` path. Learner files
  of Q01–Q18 (exercises, specimens, slots, paper, tools, research forms) name only the next
  module or the tier viva ahead of them (7 hits, all `/viva` or contract-version pointers, or
  QPLAN question numbers).

### 2.2 Layers L1–L7
- Each layer is introduced in its first module and its header's "Imported by" and "Do not open
  before" match: L1 Q01 (`docs/Q01_Hello.md:79,89`); L2 Q02 (`docs/Q02_FirstSyntaxI.md:3,83`);
  L3 Q04 (`docs/Q04_ProofCraft.md:38,73`; header "Do not open … before you start Q04");
  L4 Q07 (`docs/Q07_InternalsI.md:37,70`); L5 Q10 (`docs/Q10_PracticeIA.md:29,59`);
  L6 Q13 (`docs/Q13_PracticeIIA.md:31–33,62`); L7 Q16 (`docs/Q16_PracticeIIIA.md:37–41,64`).
  Q17 and Q18 add none and say so (`docs/Q17_PracticeIIIB.md:34`, `docs/Q18_PracticeIIIC.md:43`).
- The Verus `sub`→`big_sub` rename (Δ209) is continuous for the learner: Q13 poses the
  learner's `sub` (H1v); Q16 introduces L7's `big_sub` by name (`:40`); Q18 says
  "subtraction is L7's" (`:381`) and builds `BigNatCore.minus` on it (`:126`).
- Q13's L6 `normalize` (Verus) is used, not posed, in Q13 (`:88`) and Q16 (`:96,225`).

### 2.3 Body-text whispers and forward pointers (each pays off)
| planted | paid off |
|---|---|
| Q01:270 Verus literal unfolding fails; "a skill of Q02 and Q03" | Q02 §3 (`:211`), Q07 §4.1 P1dv (`:398`, `:457`) |
| Q01:300 loop = induction; Q02 writes invariants | Q02 §4 (`:309`) |
| Q01:319 "a recursive proof without a valid measure proves nothing" | Q04:446 (well-founded circle), Q05 §2.1 (`:464`), Q15 P5v (`:291`) |
| Q01:354 frames; "Q02's frame card and Q05 go further" | Q02 C5d (`:603`), Q05 §1 (`:92–116`) |
| Q01:362 modes; "Q03 is the module of modes" | Q03 §1 S7 (`:90`) |
| Q01:465 the dashed box; "Q03 takes it up" | Q03 §4 S10 (`:518`) |
| Q01:500 nonlinear search; Q04's `nonlinear_arith` | Q04 §5.3 (`:773`) |
| Q02:207 witnesses recognised; Q03 writes them | Q03 §7 (`:777`) |
| Q02:541 automatic induction on | Q03:629 (off in every unit, callback), Q04 §4 (`:442`) |
| Q03:593 "the calculator you verify in Q08" | Q08 §3 (`:743`, `:887`) |
| Q03:643 triggers "in Q06" | Q06 §3.1 (`:332`) |
| Q03:765 "Q09 makes this a full forensic exercise" | Q09 §4.1 (`:497`, `:500` callback) |
| Q03:981–983 v0 tested by Q04's run; v1 in Q09 | Q04:1035, Q09 §10 (`:770`) |
| Q04:223 triggers given; "you choose triggers in Q06" | Q06 §3.1 |
| Q04:294 opaque `weight`; "Q06 is the module of opacity" | Q06 §3.2 (`:431`), Q07:525 callback |
| Q06:910/917 EVAL v1 in Q09; final TRUST in Q18 | Q09 §7 (`:674`); Q18:547, `research/TRUST.md` "Q-v1 — Q18, final" |
| Q06:429 matching loop warned | Q09 §3.4 (`:370–374`, callback) |
| Q07:390 splits; "Q09 measures what splits do to stability" | Q09 §3 (`:211`) |
| Q08:995 the loop rule on paper; Q14 | Q14 §3 W2d/H4d (`:352–358`) |
| Q09:205 "Q15 writes an [LSP client]" | Q15 §1 (`:122`) |
| Q09:649 paired McNemar for Q12's Lab 1 | Q12 §5 (`:299`) |
| Q15's hard-tier pointer (`:1002`) "shipped known to fail" | Q16:4,10,156; Q17:167 |

### 2.4 Planted/harvested rows that close (beyond the findings)
Checked row by row against the harvest chapter; every row not listed in §1 has at least one
named payoff. Representative evidence per table:
- **Q01** (`:744–754`): Q03 §1.4 runtime checks (`:303`), Q04 §1 carries (`:79`); Q05 §2.1
  lexicographic; Q05 §3 wp to VC (`:723` callback); Q06 §7 TRUST v0; Q04 §5.3; Q03 §7
  witnesses; Q15 arm V (`:632`) vericoding; Q03 §11 v0 from the Q01 tally (`:954,967`).
- **Q02** (`:871–879`): Q03:629; Q04 §3 `calc`, Q06 §3.2 scoped reveal; Q03:378 the three
  obligations; Q05 §2.1; Q03 §7; Q05 §1; Q04 §5.1–5.2; Q03:968 LATENCY LOG; Q03 §7, Q15 §6.
- **Q03** (`:1039–1049`): Q05:705, Q08 §3 tracked; Q05 H5d `ParseDecimal` (`:987`);
  Q05 §3; Q06 §1, Q12 §9 holecount (`:423`), Q18 §4; Q12 §2, Q15 §2; Q04 §4, Q09 §3; Q06 §3.1,
  Q15 §3; Q09 §4.1; Q15 §5–6 oracles; Q04:1035, Q09, Q18:548.
- **Q04** (`:1090–1100`): Q06 §4.2 limb adders (`:663`); Q06 §3.1; Q05 §2.1, Q06 §10;
  Q05 H3d `CmpFast` (`:984`); Q06 H3d/H3v budget items (`:588`); Q07 §1 `bit_vector` (`:192`
  callback to Q04.P6v); Q07 §5 (`:643` callback); Q09 §3; Q06 §1; Q05 §7, Q12 §4.
- **Q05** (`:1152–1160`): Q11 §1, Q17 §1; Q08 §1 (`:212–232` `&mut self`, old, final),
  Q14 H2v toy (`:119–123`); Q11 H3v/H4v; Q14 §2; Q13 H5d; Q08 §2; Q08 §3, Q11 §3, Q17 §3;
  Q06 §10, Q09 §4, Q15 §11 ATTRIBUTIONS (`:105`); Q06 §10.
- **Q06** (`:1107–1118`): Q09 §4.2, Q12 §9, Q18 §4; Q09 §3, Q12 §1; Q12 §5, Q15 §6; Q18:547;
  Q09 §3.4, Q15 §3; Q07:525; Q07 §4.1, Q09 §3; Q15 §4 (concrete refutation before proof);
  Q09:365, Q18:281/319; Q07 §10, Q08 §7, Q09 §10; Q09 §5, Q12 §5; Q09 §7.
- **Q07** (`:937–945`): Q08 §1, Q09 §3, Q12 §3 (`:215–217` callback); Q08 §7, Q09, Q13 §5;
  Q08, Q10 §1, Q13 §1; Q09 §3, Q15 §3; Q08 §7, Q15 §5; Q08 §7, Q09 §10, Q18 §4; Q12 §4;
  Q08, Q09.
- **Q08** (`:1249–1260`): Q14 §1, Q17 §1; Q14 §1; Q14:15, Q17:83; Q09 §4, Q18 §4; Q11 H5d;
  Q14 §2; Q14 §1; Q11 H10v, Q14 H5v, Q17 H2v; Q11 H9d, Q17 H3d; Q14 §3; Q09 §10, Q18 §4;
  Q09 viva.
- **Q09** (`:911–919`): Q12 §1, Q15 §2; Q15 §1; Q15 §3, Q18 §3; Q15 §2, Q18 §4; Q18 §4;
  Q18 H7py; Q12 §4, Q15 §6; lab reports; Q18:548.
- **Q10** (`:465–469`): Q11 H3v/H4v, Q17 H2v (`:243` callback); Q13 §2, Q15 §5; Q12 §4,
  Q15 §4; Q11 H2d `CopyFrom` (`dafny/Q/Q11_PracticeIB/std/Q11_PracticeIB.dfy:167`), Q13 H5d;
  Q13 §5, Q16 §5.
- **Q11** (`:396–401`, other than M2/m1): Q17 §1 (`:158` callback); Q14 §2; Q15 §5, Q17 §3;
  Q14 §3, Q17 §3; Q14 H5v, Q17 H2v.
- **Q12** (`:506–510`, other than M4): Q15 §1; Q15 §2; Q15 §6, Q18 H7py; Q15 §6, Q18 §5;
  Q15 B1, Q18 B2 (`:520` callback).
- **Q13** (`:430–434`): Q16 H3v, Q18:381; Q15 §5; Q15 §5; Q16 §4 H1d; Q16 §5.
- **Q14** (`:524–529`, other than M3's cell): Q17:72; Q17 §1, Q18:126 extension trait;
  Q16 §4; Q16 H3d; Q17 §3 W2d; Q17 H2v.
- **Q15** (`:999–1005`, other than M4): Q18 §4; Q18 §2 (`:188` callback); Q18 §3; Q16–Q17;
  Q18 §5; Q18 §5.
- **Q16** (`:351–354`, other than m4/m6): Q17 §1, Q18 §4; Q17:328, Q18:33; Q18:381;
  Q18:129 (`Times`).
- **Q17** (`:481–482`): Q18 §4 steps 2–3 (statements yours, the statement-only review),
  Q18:548 contract v2.
- **Q18** (`:691–696`): rows close beyond the core by design (the last core module); see m6.

### 2.5 Threshold concepts (design §2.3.7 schedule: glimpsed Q01–Q03, operated Q02–Q06, mechanism Q07–Q09; TC9, TC13, TC14 resolve in Q18)
| TC | glimpsed | operated | mechanism / resolution |
|---|---|---|---|
| TC1 spec is a formula | Q01 §2 | Q02 §2 | Q08 §3 verified wp |
| TC2 the verifier's knowledge at a point | Q01 §3 | Q02 §3 scoped facts | Q07 §3 batches, Q08 §3 |
| TC3 green with an assumption is not done | Q01 §12 | Q03 §6 fake greens | Q09 §4 forensics |
| TC4 proved is not computed | Q01:270 literals | Q06 §3.2 opacity | Q07 §4 fuel |
| TC5 recursion ⇔ induction | Q01:300 | Q02 §4, Q04 §4 | Q08 §3 loop rule on paper, Q14 §3 |
| TC6 termination makes recursion sound | Q01:319 | Q02 §4.2, Q05 §2.1 | Q04:446 (earlier than the schedule), Q08:443, Q14:358 partial correctness, Q15 P5v |
| TC7 ghost vs compiled | Q01 §7 | Q03 §1, Q05 §2 erasure | Q08 §2 ghost state |
| TC8 everything becomes a VC | Q01 §8 | Q03 §2, Q05 §3 | Q08 §3 |
| TC9 no small kernel | Q01 §10 | Q03 §4, Q06 §2 TRUST v0 | Q09 §4, Q18 final TRUST (`:547`) |
| TC10 triggers; incomplete | Q03 §5 | Q06 §3.1 | Q09 §3.4 |
| TC11 several doors | Q01 §18 | Q06 §1 | Q09 §2 editor's door |
| TC12 frames / ownership | Q01 §6 | Q02 §6, Q05 §1 | Q08 §3 permissions |
| TC13 statements are the human job | Q01 §13 | Q03 §7, Q08 §7 flagship | Q18 §4 capstone round |
| TC14 brittleness | Q01 §11 | Q04 §5.2 lemma-group cost | Q09 §3, Q18 §3 |
TC6's mechanism sits in Q04 §4 and Q14/Q15 rather than Q07–Q09; it is paid off, so it is no
gap (the chapters never promise it for Q07–Q09).

---

## 3. DELTAS-ready text (for the integration lane)

> **Δ2xx · The continuity pass over Q01–Q18 and L1–L7 (spec §9.2 phase 5) — adopted (DV6, 2026-10-14).**
> Status: the audit lane's read-only pass at 83531a8; detail `Solutions/plans/DV6-audit-continuity.md`.
> Item ids, cross-module section references, file paths, commands, skills and paper cards
> resolve; every layer is introduced in its first module; every body-text whisper and every
> TC step pays off. Four harvest rows do not close as written (Q04:1091, Q11:397,
> Q17:478/480 with Q14:524's Q18 cell, Q12:511/Q15:1005): each names a payoff the named
> module does not contain (Q07 has no `calc`; no `Result` after Q11; Q18's Dafny mirror is a
> module of compiled methods, with no class, refinement or `&mut`; gate v2 imports no
> learner tool), and the fix re-points the cell to the built payoff or adds a one-line
> callback. Seven minor cells and references are corrected with them (Q05:1152, Q11:396,
> Q03:1041, Q07:940, Q16:355, Q09:913; Q12:47 §5.5→§5.3, Q18:282 spec §11.1→§11.4), and the
> harvests that name challenge modules are marked as beyond basic. Names no answer.
