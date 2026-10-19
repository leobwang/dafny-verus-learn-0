# DVR4 step 5 — R04 at the R module bar (author-only)

Binding inputs: `Solutions/plans/DVR4-repair-plan.md` §2 (R04's row: **keep** + rows), §2.1, §2.2, §4.2, §5 step 5, §7 (D58, D59); PLAN §3 R04 and §6.4's 360-minute record; the exemplar R02 and its notes. Earlier R04 evidence: `Solutions/plans/DVR1-R04-build-notes.md`, `Solutions/plans/R-author-notes.md` §5, `Solutions/plans/R04-agent-refutation-report.md`. Scratch and logs: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step5/p1/r04/` (never `/tmp/dvl0-dv*`).

## 1. Objective-to-exercise map (written before any change, 2026-10-19)

PLAN §3's objectives for R04, where the learner meets each, the item that checks it, and the evidence that keeps it real. Minutes are PLAN §6.4's (test-out 10 = 5 + 5; holes 70 = 10 × 7); none is narrowed. Reference sizes by plan §2.2's counter; "minimal" is the smallest body found by probing on the pins (`probes/`).

| objective (PLAN §3 R04) | chapter section | items that use it | checked item | minutes D/V | reference · minimal lines (D) | reference lines (V) | why not trivial (four results to confirm) |
|---|---|---|---|---|---|---|---|
| an existential introduced by its witness | §2.3 | — | **T1d/T1v** `SomeWordMatches` (closed book) | 5 / 5 | 4 · 2 | 7 | the empty body fails in both languages |
| a positive whole-string witness (every split named) | §2.3 (fresh `Cat`/`Alt` witness, Dafny and Verus pairs) | W2 | **H1d/H1v** `WitnessAbb` | 7 / 7 | 10 · 3 | 20 | empty fails; Dafny needs the `Star` chunk slices; Verus every side's `matches` |
| `forall` introduction and `exists` elimination; a negative claim covers every candidate | §2.1 (W1, C1), §2.2 (W2, C2), §2.4 | W1, W2, C1, C2 | **H2d/H2v** `WitnessNotBa` | 7 / 7 | 17 · **1** | 16 | Verus needs the prefix `forall` and the `choose`; Dafny's solver expands a short literal's splits (one slice fact suffices) |
| anchored (whole-string) against unanchored (substring) specs | §1.1, §1.2 (diagram) | — | **H3d/H3v** `WitnessAnchored` | 7 / 7 | 22 · **2** | 14 (draft) | the first conjunct is settled by `Chr`'s definition; the second is a witness |
| prose to spec with use-site checks; which bounds vary | §1.2 | — | **H4d/H4v** `PrefixMatch` (definition open, Δ160; three given checks; `cfree` forms `false`, `true`) | 7 / 7 | definition (1 line) | definition (1 line) | the forms gate: `false` and `true` bodies fail a check; the three checks discriminate prefix from whole and occurrence |
| spec strength, vacuity and mutant-kill witnesses | §3.1 (lattice diagram, P2), §3.2 (P6), §3.3 (fresh mutant) | — | **H5d/H5v** `MutantKilled` | 7 / 7 | 4 · **2** | 6 · 3 | empty fails; the witness's two values must be proved |
| `expect` outside tests (R-owned surprise); `assume`; the audit | §4.1, §4.2, §6 (audit diagram, drill) | C3d, C4v, C5dv | P1d, P5d; the AUDIT drill | — | — | — | — |
| wp/VC of straight-line code by hand | §5 (pinned pair per language) | — | paper B3 | — | — | — | — |
| rung 6 audited prover; a false statement | §9 | — | A1d/A1v (one planted false statement) | agent 30 | — | — | — |

**Constructs a reference needs, and where each is taught before its hole (criterion 11).** Witness slices (§2.3, a pinned failing and verified pair per language); `forall` statement / `assert forall … implies … by` (§2.1, W1, C1); `:|` / `choose` (§2.2, W2, C2); the empty slice and bounds (§1.1–§1.2); an existential goal introduced by a witness's proved values (§3.3, fresh mutant).

**File order (criterion 9).** The given `Occurs`; T1 (closed book); the prediction block; W1–W2; the cards C1–C3 (C4v in Verus); the holes H1–H5, each after the cards its `uses:` names (H2, H3 after C1–C2); the AUDIT block; C5dv last.

**Hole prompts and hints (criteria 7–8).** Each H item gets `**Hn.** <task>. <guiding question>` and `Hint(1)`, `Hint(2)`, the second naming the construct or fact, never the answer.

**Chapter plan.** Rewritten to R02's standard with exactly PLAN §3's three diagrams (the spec-strength lattice with sample specs; anchored vs unanchored on one string; the audit's view of a delivery); every prediction answered by a pinned capture (P2 had none: a new specimen poses "does the contract force `b`" as one lemma per label, both languages).

**Bank.** Rewritten at the Q06 schema by the bank sub-lane: 12 questions, both draws with live predicts, ≥ 5 backward edges to R01/R02.

## 2. Probes (2026-10-19, `probes/`, `chapter/`)

- **Minimal proofs (the line counter).** Dafny closes R04's concrete-string claims with very little: T1d needs 2 lines (a slice fact and the match), H1d 3 (the three tail slices of "abb"; 2 fail), H2d **1** (one slice fact, `"ba"[..1] == "b"`), H3d **2** (the split at 1 and `"b"[1..] == []`; the first conjunct is settled by `Chr`'s definition), H5d **2** (the slice and the occurrence). A general re-pose of H2d (`requires |s| > 0 && s[0] != 'a'`, any `s`) verifies with an **empty** body: Dafny's split reasoning is strong enough that re-posing does not restore the budget (`probes/a2-*.dfy`). Verus needs the explicit work: H2v's empty body and a two-slice body fail; H5v's minimal is 3 lines.
- **H3's construct claim.** H3's `uses: forall-intro, exists-elim` (PLAN §6.4) is not needed by its minimal proof in either language: the reference's `forall` over prefixes proved a fact the definition already gives. The references were simplified (Dafny 22 → 11 reference lines, Verus to 14), and the prompt now asks which conjunct the definition settles.
- **P2 had no capture.** A new specimen pair (`chapter-p2-{d,v}`) poses "does the contract force `b`" as one lemma per label, each body naming its witness slice; [a] and [d] verify and [b] and [c] fail in both languages (`a d`).
- **Bank overlap found and fixed.** The bank sub-lane's K12 refuted `StarIsOnce` with a two-chunk `Star` witness whose Verus proof shared a 68-token run with R04.H3v's (and H1v's) reference: the counterexample is now the empty string (both bodies empty), re-captured.

## 3. As built (2026-10-19)

**Files.** Both exercise files: the given `Occurs` first, then T1, the prediction block, W1–W2, the cards, a `Holes` banner, H1–H5 with `**Hn.**` prompts, guiding questions and `Hint(1)`/`Hint(2)`, the AUDIT block, C5dv last. H4's three checks are multi-line under `Uncomment as you go:`; H4d keeps its benign `ensures true`. T1d's and H5d's references now carry hole markers. Twins, learner files, agent files (learner and twin) and every specimen are one statement per line with spaced commas; the `// planted: R04.P5d` markers sit on the `expect`/`assume` lines themselves. Specimen twins mirror the learner specimens (13 refreshed; the old twins were byte copies of the packed versions, and `reference_lint` caught the drift). New specimens `chapter-p2-d.dfy.specimen`, `chapter-p2-v.rs.specimen` (`// after: R04.P2dv`), sealed. The P3 lemmas `A`, `B`, `D` and the chapter's `Scale` were renamed for `avoid.sh`.

**Admission evidence (plan §2.1).** References stable on seeds 1–3: core twins (Dafny 17, Verus 10 verified) and both agent twins (`logs/brittle-*.log`). `firsttry.sh R04 --empty-body` 12/12 (`logs/empty-body-1.log`): every lemma's empty body and every region gate fails in every run, maximal automation included; H4d/H4v run the forms gate (both `cfree:` answers, `false` and `true`, fail a given check; the shipped gate is skipped for a definition hole by design). `specfreeze --pin`/`--check R04` 0 (110 statements, 22 files; H4's bodies stay open); `--lint-hollow` OK (20 files); `reference_lint` 0 (20 twins); counts re-pinned (`vcheck --ref --pin-counts R04`); `vcheck --shipped R04` 0; sealed sidecars refreshed (15).

| item | minutes | reference · minimal lines | (1) seeds 1–3 | (2) empty body, shipped | (3) maximal automation | (4) TRIV | row |
|---|---|---|---|---|---|---|---|
| T1d | 5 | 4 · 2 | stable | fails; region gate fails | fails | n/a (proof) | admitted |
| T1v | 5 | 7 | stable | fails; region gate fails | fails | n/a | admitted |
| H1d | 7 | 10 · 3 | stable | fails; region gate fails | fails | n/a | admitted |
| H1v | 7 | 20 | stable | fails; region gate fails | fails | n/a | admitted |
| H2d | 7 | 17 · **1** | stable | fails; region gate fails | fails | n/a | admitted at 7 pending DECISION 1 |
| H2v | 7 | 16 | stable | fails; region gate fails | fails | n/a | admitted |
| H3d | 7 | 11 · **2** | stable | fails; region gate fails | fails | n/a | admitted at 7 pending DECISION 1 |
| H3v | 7 | 14 | stable | fails; region gate fails | fails | n/a | admitted |
| H4d | 7 | definition (1 line) | stable | forms gate: `false`, `true` fail | n/a (definition) | the two `cfree` bodies | admitted |
| H4v | 7 | definition (1 line) | stable | forms gate: `false`, `true` fail | n/a | as H4d | admitted |
| H5d | 7 | 4 · **2** | stable | fails; region gate fails | fails | n/a | admitted at 7 pending DECISION 1 |
| H5v | 7 | 6 · 3 | stable | fails; region gate fails | fails | n/a | admitted |

Minutes reconcile: test-out 10 and holes 70 (10 × 7) = PLAN §6.4's lines; `[module.admissible]` holds the 12 rows (80 minutes).

**Overlap.** `bin/overlap.py R04` at 24-token windows: after the K12 fix, no answer region shares more than 7 windows with an R04 specimen, chapter block or bank probe (the shared runs are statement text and A1 boilerplate). Finding (not this lane's files): the Lab α forms `bench/local/r/labalpha/r09-rep-range-correct-v` and `r09-copies-split-v` share 64 windows with R04.H2v's reference, the `if matches(Cat(a, b), s) { let i = choose|i: int| … }` skeleton, which is W2v's given elimination idiom (taught in the chapter, §2.2); recorded, no pattern matches it. Public-answer calibration: 0 over 22 shipped files. Leak patterns re-cut: 8 OK over 2,691 public files (7 of the old 8 no longer matched their re-laid-out twins; H2v tightened past the Lab α form `r06-star-unfold-refuted-v`, which the old pattern matched).

**Chapter.** Rewritten: 5,859 lint words (from 6,306, now with source inline instead of abstract prose), 17 Dafny and 17 Rust source blocks (from 1 and 1), 42 pinned fences (from 20), exactly PLAN §3's three diagrams (the spec-strength lattice; anchored against unanchored on one string; the audit's view of a delivery; the old prediction-flow, bounds and dashboard diagrams were not the record's), each run source directly above its pinned output, every prediction answered after its box (P2 newly captured). `chapter_lint` 0; `pins.py --chapter R04` 42/42; `pins.py --ci --module R04` 71 pins 0 problems; `--ref` 6 checks 0.

**Bank.** Rewritten by the bank sub-lane at the Q06 schema: 12 questions (2 reconstruct, 4 predict, 2 why, 2 connect, 2 transfer), 1,364 lines, 12 `**Reread**` sections (all resolve in the chapter), 8 backward edges to R01/R02, two disjoint draws with two live predicts each (A: K3, K7; B: K2, K4), two parallel problems (`XStarThenY` for H1–H3; `SuffixMatch` from prose for H4/H5) with author-verified runs; tags mapped onto the controlled vocabulary (`check_course_map.py` refused seven new tags); no generic branch lines; numeral scan clean.

**Written pair.** Unchanged problems; rubric pins refreshed (4); `make -C paper paper` builds.

**Study workflow** (`bin/wf.py R04`, disposable clone): firsttry `--check` records 8 first tries (6 predictions, 2 test-outs), strict OK, freeze 0 on the shipped agent statements, both units' gates and audits, both agent references' gates and audits: 11/11. (The first run's three failures were the harness's: it re-commented specimen `expect` lines that are not slots, and it froze against the agent twins, whose third statement is by design a refutation; `workflow-run1/`.)

## 4. DECISION NEEDED

**1 · R04's Dafny holes on concrete strings are under plan §2.2's floor (non-blocking).** H2d's minimal proof is 1 line, H3d's and H5d's 2 (T1d's 2, a test-out), because Dafny's solver expands short literal strings' splits; the Verus twins carry the explicit witness and quantifier work (16, 14, 6 lines). A general re-pose does not help (H2d over any `s` verifies empty). H3's `uses:` names `forall-intro` and `exists-elim`, which neither language's minimal H3 proof needs, so PLAN §6.4's "checked uses ≥ 2" for `forall-intro` rests on H2 alone. Options: (a) record H2d, H3d, H5d as R04 exceptions under D59's reading, with the chapter's §2.4 stating the asymmetry, and correct H3's `uses:` to the constructs it needs; (b) re-pose the Dafny holes on statements Dafny's automation does not close (for example over strings of unknown length with nested `Star`; not yet found); (c) move 2 minutes from each of H2d, H3d, H5d to their Verus twins. **Recommend (a).**
