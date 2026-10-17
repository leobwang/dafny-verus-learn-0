# DV6 audit lane q13q18: spec §12.1 "Per module" for Q13–Q18 (author-side)

Lane: DV6 AUDIT, Q13–Q18 with layers L6/L7 and Labs 2–3. Memory share 2 GB, so no solver job ran.
Evidence comes from the CI run `build/ci/20261014T004859Z-3125743/` (author run; its summary
says `authoring @ db398e4, 68 uncommitted`, i.e. the tree later committed as 83531a8: no tracked
file is newer than the run's start except `paper/solutions/*.latexmk.log`, build outputs), its
reference logs under `~/.cache/dafny-verus-learn-0/ci/20261014T004859Z-3125743/` (counts only
quoted here), and static re-runs under a 2 GB scope on 2026-10-14. Other DV6 lanes were editing
the worktree during this audit (14 files uncommitted: D26's tools/README/SKILL text, D28/D31's
`benchstrip.py`, `sandbox.py`, `attested.toml`). Every line below is as of HEAD 83531a8 and goes
stale when those edits land (see §3).

Scripts used (archived): `~/.cache/dafny-verus-learn-0/author-probes/dv6/audit-q13q18/`
(`draws.py`: the tier draws against the banks; `ppnames.py`: the parallel problems' names
against the twins and exercises; `leakver.py`: the leak README's verifier, extracted as the
README says).

## 1. Lines verified as holding (for the release checklist)

| §12.1 line | Q13 | Q14 | Q15 | Q16 | Q17 | Q18 | evidence |
|---|---|---|---|---|---|---|---|
| twin complete, hole-free, audit-clean, silent | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `verify-q-{dafny,verus}.log`: every `[reference gate …]` and `[reference audit …]` of the six modules exit 0 (std/crate, exits, agent twins Q15 d+v, Q17, Q18 d+v); the gate fails on warnings, so silent |
| quoted outputs pinned | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `pins.log`: `pins --ci: 823 pin(s) checked over 18 module(s); 0 problem(s)`; `pins.py --ref` exit 0; no `$ `-output fence without a `<!-- pin` marker in the six chapters (scan, 0) |
| exercise = exact hollow; `--lint-hollow` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `static.log`: `Q13 lint-hollow: OK (4 file(s))` … `Q18 … OK (7 file(s))`; `specfreeze --check Q13..Q18` 0 findings each |
| `--empty-body` | ✓ 7/7 | ✓ 7/7 | ✓ 18/18 | ✓ 4/4 | ✓ 3/3 | ✓ 7/7 (+2/2 statement route) | `empty-body.log` exit 0 each; counts from `empty-body.ref.log` |
| hole count = chapter = CI | 3+3 | 3+6 | 5+5 | 2+2 | 4+2 | 1+1 | `verify-q-*.log` `Qnn d/v: N hole(s) counted by the tool …; 0 mismatch(es)`; the chapters' files tables and sums (Q13 l.57–58, 369; Q14 l.62–73 "Nine holes"; Q15 l.95–98; Q16 l.301 "4"; Q17 l.65 "Six"; Q18 l.142 "2") agree |
| every slot unfilled | ✓ 1 | ✓ 1 | ✓ 11 | — | — | ✓ 4 | `slots/Q1n.slots` all `= ???`, equal to chapter_lint's predict-box counts; Q16/Q17 have no P item |
| item markers parse; coverage rows resolve; D4 matrix | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `check_course_map.py` OK (49 modules, 138 import files, 81 coverage rows, 119 pending: all on planned modules); `--only vocab` OK; D4 `concept_items` is `{}` for Q10–Q33 by rule; no WRITE lists from Q10 |
| specimens/exits/demos outside roots, pinned | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `gen_units --check` 37 units match; `Qnn d/v: k file(s) checked against their shipped-state pins; 0 problem(s)` |
| chapter skeleton, 3–5 diagrams, planted table | 3 | 4 | 5 | 4 | 3 | 4 | `chapter_lint --all` 18 chapters, 0 problems; each chapter ends in `## What Qnn planted` with a seed/harvested table |
| written pair compiles; rubric pins filled | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `paper.log` 36 documents; `rubric.log` `update_rubric_pins --check` exit 0; `grep -c PENDING paper/rubrics/Q1[3-8]_rubric.md` 0 each |
| bank size, mix, viva-able, draws | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8 K each, all `viva: yes`, 4 predicts each with a `**Verifier probe**` and a captured output; tier draws A–D of Q15 and Q18 (`draws.py`): pairwise disjoint, 5 distinct strands, every module present, ≥1 predict, every table cell (strand, predict, backward edge) equal to its bank question |
| parallel problems' names disjoint | ✓ 3 | ✓ 3 | ✓ 3 | ✓ 3 | ✓ 3 | ✓ 2 | `ppnames.py`: no PP declaration equal to a twin or exercise declaration (two regex artifacts, `has`/`of`, from prose); `avoid.sh` OK (1,961 Q declarations, 0 hits, 0 stale waivers) |
| leak patterns 3–8, Rule 1 and 2 | 8 | 8 | 8 | 8 | 8 | 8 | the README verifier run 2026-10-14 for Q13–Q18: `48 OK sol=1 prob=0 chap=0 pub=0`, `leak verifier: 6 module(s), 1631 public files scanned, OK`; two `exempt:` lines (L7 above Q13's L6, rule 2); every `# from` file a twin of an H/X/A item |
| calibration fixtures exist (flawed with EXPECTED + clean control, gold) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `tests/instructor/fixtures/Q1n_{flawed,gold}_answers.tex`; 2–4 EXPECTED lines each with a score-4 control. Not run: §2 F2 |
| agentic CONTRACT on line 1 | — | — | ✓ 3 | — | ✓ | ✓ 2 | `/* CONTRACT` / `"""CONTRACT` on line 1 with goal, allowed-files, acceptance in all six agent files; the chapters' CONTRACT blockquotes (lint) |
| practice items admissible or minute-less | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | registry: every H item admitted with minutes, or `admitted=false, minutes=0` (Q15.H2d/H2v); `OUT_OF_BAND`'s twelve exceptions each cite D2/D6/D7/D9/D21 |
| minutes reconcile to the module total | ✓ 200 | ✓ 210 | ✗ §2 F3 | ✓ 225 | ✓ 225 | ✓ 575 | QPLAN §23.4/24.4/26.5/27.5/28.7 sum to their totals; the registry's minutes equal the table lines; the chapter §0 lines repeat them |
| `avoid.sh` clean, no stale waivers | ✓ | | | | | | `static.log`: `0 hit(s), 0 waived, 0 stale waiver(s)`; 1 name waiver idle (N1, no R declarations yet), not stale |
| layers L6, L7 | ✓ | | | ✓ | | | `verify-q-*.log`: `QG_L6_BigNat.dfy` 130 verified, `qg_bignat_l6` 2, `QG_L7` 133, `qg_bignat_l7` 6; gate and audit exit 0 |
| D29 (NOTICE) as built | | | ✓ | | | | `bench/local/q/lab2pub/NOTICE`: both MIT licences, commits, the change statement |

Harness self-tests that `ci.sh` does not run (re-run here, tool-free): `test_skill_sims.py` 31 OK
(plants still apply to the current files), `test_calibrate.py` 18 OK (on the tree with the other
lanes' uncommitted edits).

## 2. Gaps (ranked; file:line, the line it fails, evidence, fix)

**F1 (major). No current skill simulation for Q13–Q18.** §12.1 "A study-clone simulation of
every skill gives zero leak-pattern hits". `tests/instructor/simulations/README.md:105–107`: the
Q16–Q18 set is "not run yet"; `:124–128` DV5d stopped after one blocked turn; the Q13–Q15 set
last ran in DV5b (`:136–138`, `dd24798` + 276 files). Since then (`git diff --stat 5e5d3ee HEAD`):
the hook (70 lines), `banks/Q15.md`, the Q13/Q14/Q15 chapters (55/20/132 lines), the three
rubrics, `Q13_PracticeIIA.dfy`, `Q15_Lab2Specs.dfy`, `q14 lib.rs`, `q15 lab2_specs.rs`; and this
round adds `review-code/SKILL.md` (D26, uncommitted now), which makes every tier's case e stale,
plus D32/D33's rubric and chapter edits. Fix: after this round's edits land, run both sets
(Q13–Q15 a–g, Q16–Q18 a–h) from a terminal, leak scan 0/0, and record a *Last run*.

**F2 (major). The grader calibration has never run.** §12.1 "Calibration fixtures … pass a
headless grader run". `tests/instructor/calibration/README.md:65–67` "**Not run yet.**"; D32 also
requires `/review-code`'s calibration on Q13 and Q15 again. Stale text in the same section: `:72`
"It costs 12 sessions" (the tool's `--budget 72`, `:14`, and CLAUDE.md say 72 over Q01–Q18);
`:74` "The clone is still on disk" (`/tmp/dvl0-dv2b2-calib` is not on the host). Fix:
`calibrate.py all` after D32/D33 land; rewrite *Last run*.

**F3 (major). Q15's minutes do not reconcile.** §12.1 "Minutes reconcile to the module total"
(rule QPLAN.md:2515: a gated item's minutes move to its fallback once the fallback has its four
results, else 0). `MODULES.toml` Q15: `"Q15.H2d" = { admitted = false, minutes = 0, fallback =
"F-H2d: refute and repair only (the proof given)" }`, H2v likewise (Δ199: below the band). But
`QPLAN.md:3058` and `:3105` keep "H2d 8, H2v 7 | 15" inside the 628; `docs/Q15_PracticeIIC.md:31–32`
and the `CALIBRATION` block (`dafny/Q/Q15_PracticeIIC/std/Q15_PracticeIIC.dfy:198`) budget
"refute, repair, prove 15"; §4 (`docs/Q15_PracticeIIC.md:463–471`) asks for refutation, repair
**and proof**, and the shipped `CmpTop` (`Q15_PracticeIIC.dfy:176–180`) is the full item. No
fallback is built and the learner is not told the pair is outside the band. Δ226 records "H items
225 of 240" without resolving it. Q16's gated line shows the convention (QPLAN.md:3208, "0 until
then"). Options: (a) mark S12's line gated, 0 minutes until admitted (QPLAN §25.3/§25.7, the
chapter's §0, the CALIBRATION block; total 613 + 30; chapter units re-pinned) (recommended now);
(b) build F-H2d/F-H2v (proof given) with their four results and move the 15 minutes to them;
(c) DECISION NEEDED: admit the pair under the short-format band exception, as D2 did for S11's
H1d/H1v (`OUT_OF_BAND` and `PRACTICE_BANDS` gain the two). Recommendation: (c) put to the user,
(a) until then.

**F4 (major). The toolsmith agent file has no reference.** §12.1 "a twin reference section
proving it satisfiable". `tools/Q15/toolsmith.py` (Q15's `agentic` list) has no twin:
`Solutions/tools/Q15/` holds only `battery/` (the per-goal trigger repairs), and
`Solutions/plans/Q15-code-notes.md:37` gives its reference column as "—". The repairs show each
goal can be repaired, not that a tool meeting the CONTRACT's acceptance (trigger-only output files,
gate and `specfreeze --against` on all 24 goal files, standard library only) exists. No DELTAS
entry waives it (Δ112 waives delivery specimens only). The same holds for Q12's
`tools/Q12/holecount.py` (outside this lane: Q10–Q12's auditor). Fix: write
`Solutions/tools/Q15/toolsmith.py` and record a run over the battery (a solver lane, Dafny 8 GB /
Verus 16 GB caps, one job at a time), or record in DELTAS that the battery's repairs are the
satisfiability evidence for a Python tool contract.

**F5 (major, in flight this round). Lab 2's public strata are not shippable at HEAD.**
`git show HEAD:sandbox/attested.toml`: 78 entries, 0 under `lab2pub`; `docs/Q15_PracticeIIC.md:83`
"One rule is not fixed yet …" (settled by D27); the forms keep the specification-only definitions
(D28: rebuild, C1/C4/C6/C7 on the same draw, re-seal Q15, re-confirm `HIDDEN_CHECKS_HELD`'s Q15
manifest, then attest the ten); D31 re-scans all entries. Until then a sandbox staging a public
card refuses it, and `sandbox/truth.toml`, `expected/Q15.chapter.toml` and Q15's `pins` move.
Fix: the D27/D28/D31 lanes; then re-run this table's Q15 rows (pins, specfreeze, leak verifier,
`lab2pub.py build --check`, `check_course_map.py`'s hidden-check kind).

**F6 (minor). Three agentic sections lack the dashboard subsection.** §12.1 / spec §2.4.3 item 7
(spec l.399): "a subsection 'What the dashboard can and cannot see', with live evidence". Q01–Q12's
agentic sections each carry `### What the dashboard can and cannot see`; Q15 §11
(`docs/Q15_PracticeIIC.md:840–910`) ends with a paragraph (`:906–908`) and no fence; Q15 §12 has
`### What the tool's checks can and cannot see` (`:939`) with no pinned fence; Q17 §7 (`:448–449`)
and Q18 §9 (`:651–653`) end with a paragraph. `chapter_lint.py` checks only the instruments
heading. Fix: give each a titled subsection with one pinned live fence (the shipped gate or audit
line it reads), re-pin; optionally lint it.

**F7 (minor). Bank probe outputs are not replayed.** No script re-runs a bank's
`**Verifier probe**` (none of `scripts/`, `tests/`, `harness/` reads them); the Q13–Q18 banks'
*Toolchain* lines date every capture 2026-10-11, and `scripts/vcheck` changed since (330 lines
over `5e5d3ee..HEAD`). `banks/Q16.md:40` says every output was captured 2026-10-11, while Δ214
re-captured K7 on 2026-10-12. The chapter fences are re-run by CI; the bank outputs rest on their
capture. Fix: one replay of the 24 Q13–Q18 predict probes before the freeze (a solver lane), with
the dates corrected.

**F8 (minor). The leak README's table is stale.** `tests/instructor/leak_patterns/README.md:37–42`
date Q13–Q18's last verification 2026-10-11/12, though Δ230/Δ231 re-ran the verifier after the
references changed (README l.17 asks for a re-run on every such change) and this lane's run of
2026-10-14 is 48 OK. Fix: update the six rows (and Q01–Q12's, after their own audit).

## 3. What goes stale when this round's edits land

- D26 (`review-code/SKILL.md`, `firsttry.py`, `pins.py`, `course_mode.sh`, README): every
  simulation's case e; `pins --ci` and `firsttry --lint-hollow`/`--empty-body` should be re-run.
- D27/D28/D31 (Q15): Q15's pins, `specfreeze --check`, `HIDDEN_CHECKS_HELD`, `truth.toml`,
  `attested.toml`, the chapter §0/§6.2 text and units pin, leak verifier.
- D30: Q12 chapter and Lab 1's pre-registration (Q10–Q12 lane).
- D32/D33 (Q13 C5, Q15 C4, Q17's reader; the first-run rule in Q13 §2, Q15 §5, Q17 §4): not in
  the HEAD rubrics (`paper/rubrics/Q13_rubric.md:102`, `Q15_rubric.md:107`) or chapters yet; then
  rubric pins, chapter pins, calibration (Q13, Q15) and the simulations re-run.
- The CI evidence above is the author run; the study-mode `scripts/ci.sh` did not run in DV5e.

## 4. DELTAS-ready text (for the integration lane)

> **Δ2xx · The DV6 audit of Q13–Q18 against spec §12.1's per-module lines** — the audit lane
> (2 GB, no solver job) checked every per-module line for Q13–Q18 at HEAD 83531a8 against CI
> `20261014T004859Z-3125743` and static re-runs. Holding: twins, hollows, hole counts (chapter =
> CI), slots, coverage, pins (823), chapters (lint 0, 3–5 diagrams, planted tables), rubric pins,
> banks (8 each, draws A–D of Q15 and Q18 disjoint and consistent), PP names, leak patterns (48
> OK), layers L6/L7, avoid.sh, minutes of Q13, Q14, Q16–Q18. Open: the simulations (Q16–Q18 never
> run, Q13–Q15 stale) and the calibration (never run); Q15's S12 minutes (the gated H2 pair
> budgeted at 15, a decision for the user); the toolsmith's missing reference; Lab 2's public
> strata (D27/D28/D31); the dashboard subsections of Q15 §11–§12, Q17 §7, Q18 §9; a bank-probe
> replay; the leak README's dates. Detail: `Solutions/plans/DV6-audit-q13q18.md`.
